param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [string]$AppId = "ru.monitoring.mobile",
    [string]$MainActivity = ".MainActivity",
    [switch]$SkipInstall,
    [switch]$SkipRun
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

$androidDir = Join-Path $RepoRoot "android-client"
$gradlew = Join-Path $androidDir "gradlew.bat"

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

Write-Host "[1/5] Sync project with Gradle files (CLI equivalent)..."
Invoke-GradleStep -Description "Gradle sync-equivalent" -Tasks @("help")

Write-Host "[2/5] Clean project..."
Invoke-GradleStep -Description "Clean project" -Tasks @("clean")

Write-Host "[3/5] Assemble project..."
Invoke-GradleStep -Description "Assemble debug" -Tasks @("assembleDebug")

if (-not $SkipInstall) {
    Write-Host "[4/5] Install app on connected device/emulator..."
    Invoke-GradleStep -Description "Install debug APK" -Tasks @(":app:installDebug")
}
else {
    Write-Host "[4/5] Install skipped (-SkipInstall)."
}

if ($SkipRun) {
    Write-Host "[5/5] App launch skipped (-SkipRun)."
    Write-Host "✅ Done: sync + clean + assemble"
    exit 0
}

if (-not $SkipInstall) {
    Require-Command adb

    $adbState = & adb get-state 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $adbState) {
        Write-Warning "No active adb device/emulator. APK installation finished, but app launch skipped."
        Write-Host "Start an emulator or connect a device, then run: adb shell am start -n $AppId/$MainActivity"
        exit 0
    }

    Write-Host "[5/5] Launch app (equivalent to 'app' [U] Shift+F10)..."
    & adb shell am start -n "$AppId/$MainActivity"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to launch app via adb."
    }

    Write-Host "✅ Done: sync + clean + assemble + install + run"
}
else {
    Write-Host "[5/5] Launch skipped because install was skipped."
    Write-Host "✅ Done: sync + clean + assemble"
}
