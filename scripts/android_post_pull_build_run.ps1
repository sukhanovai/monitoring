param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [ValidateSet("legacy", "compactOps")]
    [string]$Flavor = "compactOps",
    [string]$AppId = "",
    [string]$MainActivity = ".MainActivity",
    [switch]$SkipInstall,
    [switch]$SkipRun
)

$ErrorActionPreference = "Stop"


function Get-FlavorConfig {
    param(
        [ValidateSet("legacy", "compactOps")]
        [string]$Flavor
    )

    switch ($Flavor) {
        "legacy" {
            return @{
                Variant = "Legacy"
                AppId = "ru.monitoring.mobile.legacy"
            }
        }
        "compactOps" {
            return @{
                Variant = "CompactOps"
                AppId = "ru.monitoring.mobile.compactops"
            }
        }
        default {
            throw "Unsupported flavor: $Flavor"
        }
    }
}

function Resolve-AdbPath {
    $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
    if ($adbCommand) {
        return $adbCommand.Source
    }

    $candidates = @()
    foreach ($sdkRoot in @($env:ANDROID_SDK_ROOT, $env:ANDROID_HOME)) {
        if ($sdkRoot) {
            $candidates += (Join-Path $sdkRoot "platform-tools\adb.exe")
            $candidates += (Join-Path $sdkRoot "platform-tools\adb")
        }
    }

    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe")
        $candidates += (Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb")
    }

    if ($env:USERPROFILE) {
        $candidates += (Join-Path $env:USERPROFILE "AppData\Local\Android\Sdk\platform-tools\adb.exe")
        $candidates += (Join-Path $env:USERPROFILE "AppData\Local\Android\Sdk\platform-tools\adb")
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    throw "Command 'adb' was not found in PATH or common Android SDK locations. Install Android SDK Platform-Tools or set ANDROID_SDK_ROOT/ANDROID_HOME."
}

function Resolve-TargetDevice {
    param(
        [string]$AdbPath
    )

    $devicesOutput = & $AdbPath devices
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $deviceLine = $devicesOutput |
        Select-Object -Skip 1 |
        Where-Object { $_ -match "\tdevice$" } |
        Select-Object -First 1

    if (-not $deviceLine) {
        return $null
    }

    return ($deviceLine -split "\t")[0]
}

function Test-AnyDeviceConnected {
    param(
        [string]$AdbPath
    )

    return [bool](Resolve-TargetDevice -AdbPath $AdbPath)
}

function Ensure-DeviceReadyForLaunch {
    param(
        [string]$AdbPath,
        [string]$DeviceId
    )

    Write-Host "Preparing device screen for visible app launch..."

    & $AdbPath -s $DeviceId wait-for-device

    $bootCompleted = & $AdbPath -s $DeviceId shell getprop sys.boot_completed
    if ($bootCompleted -notmatch "1") {
        Write-Host "Device is still booting; waiting up to 30 seconds..."
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 1
            $bootCompleted = & $AdbPath -s $DeviceId shell getprop sys.boot_completed
            if ($bootCompleted -match "1") {
                break
            }
        }
    }

    & $AdbPath -s $DeviceId shell input keyevent KEYCODE_WAKEUP | Out-Null
    & $AdbPath -s $DeviceId shell wm dismiss-keyguard | Out-Null
    & $AdbPath -s $DeviceId shell input keyevent KEYCODE_MENU | Out-Null
}

function Test-AppIsForeground {
    param(
        [string]$AdbPath,
        [string]$DeviceId,
        [string]$AppId,
        [int]$TimeoutSeconds = 12
    )

    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        $windowDump = & $AdbPath -s $DeviceId shell dumpsys window windows
        $activityDump = & $AdbPath -s $DeviceId shell dumpsys activity activities

        if (($windowDump -match $AppId) -or ($activityDump -match $AppId)) {
            return $true
        }

        Start-Sleep -Seconds 1
    }

    return $false
}

$androidDir = Join-Path $RepoRoot "android-client"
$gradlew = Join-Path $androidDir "gradlew.bat"
$flavorConfig = Get-FlavorConfig -Flavor $Flavor
$variantName = $flavorConfig.Variant

if (-not $AppId) {
    $AppId = $flavorConfig.AppId
}

if (-not (Test-Path $gradlew)) {
    throw "gradlew.bat was not found at: $gradlew"
}

function Invoke-GradleStep {
    param(
        [string]$Description,
        [string[]]$Tasks
    )

    Write-Host "==> $Description"
    & $gradlew "-p" $androidDir @Tasks
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle step failed: $Description"
    }
}

function Restart-AdbServer {
    param(
        [string]$AdbPath
    )

    Write-Host "Restarting adb server to recover the transport (Broken pipe workaround)..."
    & $AdbPath kill-server 2>$null | Out-Null
    Start-Sleep -Seconds 1
    & $AdbPath start-server 2>$null | Out-Null
    & $AdbPath wait-for-device
}

function Invoke-RobustInstall {
    param(
        [string]$AdbPath,
        [string]$Description,
        [string]$InstallTask,
        [string]$ApkPath,
        [int]$MaxAttempts = 3
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Write-Host "==> $Description (attempt $attempt/$MaxAttempts)"

        if ($attempt -gt 1) {
            Restart-AdbServer -AdbPath $AdbPath
            Start-Sleep -Seconds ([int][Math]::Min(8, [Math]::Pow(2, $attempt)))
        }

        $deviceId = Resolve-TargetDevice -AdbPath $AdbPath

        # Prefer a direct 'adb install': platform-tools is far more resilient to
        # the ddmlib "Failure calling service package: Broken pipe" that the
        # Gradle :app:install*Debug task hits on flaky emulator transports.
        if ((Test-Path $ApkPath) -and $deviceId) {
            Write-Host "Installing via 'adb -s $deviceId install -r -t' ..."
            & $AdbPath -s $deviceId install -r -t "$ApkPath"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "APK installed via adb install."
                return
            }
            Write-Warning "adb install failed (exit $LASTEXITCODE); trying Gradle install task..."
        }
        elseif (-not (Test-Path $ApkPath)) {
            Write-Warning "APK not found at $ApkPath; using Gradle install task..."
        }

        & $gradlew "-p" $androidDir $InstallTask
        if ($LASTEXITCODE -eq 0) {
            Write-Host "APK installed via Gradle install task."
            return
        }

        Write-Warning "Install attempt $attempt/$MaxAttempts failed."
    }

    throw "Gradle step failed: $Description (after $MaxAttempts attempts; last error is likely 'Broken pipe' - cold-boot/wipe the AVD or reconnect the device, then rerun)"
}

Write-Host "[1/5] Sync project with Gradle files (CLI equivalent)..."
Invoke-GradleStep -Description "Gradle sync-equivalent" -Tasks @("help")

Write-Host "[2/5] Clean project..."
Invoke-GradleStep -Description "Clean project" -Tasks @("clean")

Write-Host "[3/5] Assemble project..."
$assembleTask = ":app:assemble{0}Debug" -f $variantName
Invoke-GradleStep -Description "Assemble $Flavor debug" -Tasks @($assembleTask)

if (-not $SkipInstall) {
    $adbPath = Resolve-AdbPath
    if (-not (Test-AnyDeviceConnected -AdbPath $adbPath)) {
        Write-Warning "No connected adb devices/emulators. Install and run steps will be skipped."
        Write-Host "Tip: connect a device or start an emulator, then rerun script without -SkipInstall."
        $SkipInstall = $true
        $SkipRun = $true
    }
}

if (-not $SkipInstall) {
    Write-Host "[4/5] Install app on connected device/emulator..."
    $installTask = ":app:install{0}Debug" -f $variantName
    $apkPath = Join-Path $androidDir ("app\build\outputs\apk\{0}\debug\app-{0}-debug.apk" -f $Flavor)
    Invoke-RobustInstall -AdbPath $adbPath -Description "Install $Flavor debug APK" -InstallTask $installTask -ApkPath $apkPath
}
else {
    Write-Host "[4/5] Install skipped (-SkipInstall)."
}

if ($SkipRun) {
    Write-Host "[5/5] App launch skipped (-SkipRun)."
    Write-Host "[OK] Done: sync + clean + assemble ($Flavor)"
    exit 0
}

if (-not $SkipInstall) {
    $targetDevice = Resolve-TargetDevice -AdbPath $adbPath
    if (-not $targetDevice) {
        Write-Warning "No active adb device/emulator. APK installation finished, but app launch skipped."
        Write-Host "Start an emulator or connect a device, then run: `"$adbPath`" shell am start -n $AppId/$MainActivity"
        exit 0
    }

    Write-Host "Using adb target: $targetDevice"
    Ensure-DeviceReadyForLaunch -AdbPath $adbPath -DeviceId $targetDevice

    $resolvedComponent = & $adbPath -s $targetDevice shell cmd package resolve-activity --brief $AppId 2>$null
    $resolvedComponent = ($resolvedComponent | Where-Object { $_ -and $_ -match "/" } | Select-Object -Last 1)
    if (-not $resolvedComponent) {
        $resolvedComponent = "$AppId/$MainActivity"
    }

    Write-Host "[5/5] Launch app (equivalent to 'app' [U] Shift+F10)..."

    $launched = $false

    & $adbPath -s $targetDevice shell am force-stop $AppId | Out-Null
    & $adbPath -s $targetDevice shell am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n $resolvedComponent
    if ($LASTEXITCODE -eq 0) {
        $launched = Test-AppIsForeground -AdbPath $adbPath -DeviceId $targetDevice -AppId $AppId
    }

    if (-not $launched) {
        Write-Warning "Direct am start did not bring app to foreground; trying monkey fallback..."
        & $adbPath -s $targetDevice shell monkey -p $AppId -c android.intent.category.LAUNCHER 1
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to launch app via adb."
        }

        $launched = Test-AppIsForeground -AdbPath $adbPath -DeviceId $targetDevice -AppId $AppId
        if (-not $launched) {
            throw "App launch command completed, but package '$AppId' did not become foreground on device '$targetDevice'."
        }
    }

    Write-Host "[OK] Done: sync + clean + assemble + install + run ($Flavor)"
}
else {
    Write-Host "[5/5] Launch skipped because install was skipped."
    Write-Host "[OK] Done: sync + clean + assemble ($Flavor)"
}
