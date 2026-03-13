Param(
    [string]$TargetBranch = "devel",
    [string]$GitHubRepo = "",
    [string]$ApkAssetName = "monitoring-android.apk",
    [string]$ReleaseNotes = "",
    [switch]$SkipBranchCheck,
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Assert-Command([string]$name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Команда '$name' не найдена в PATH"
    }
}

function Get-ProjectRoot {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    return (Resolve-Path (Join-Path $scriptDir "..")).Path
}

function Get-AppVersion([string]$settingsPath) {
    $line = Get-Content $settingsPath | Where-Object { $_ -match '^APP_VERSION\s*=\s*"([^"]+)"' } | Select-Object -First 1
    if (-not $line) { throw "Не удалось прочитать APP_VERSION из $settingsPath" }
    $m = [regex]::Match($line, '^APP_VERSION\s*=\s*"([^"]+)"')
    return $m.Groups[1].Value
}

function Resolve-Repo([string]$root, [string]$explicitRepo) {
    if ($explicitRepo) { return $explicitRepo }

    $envRepo = $env:ANDROID_GITHUB_REPOSITORY
    if ($envRepo) { return $envRepo }

    $origin = (git -C $root remote get-url origin).Trim()
    if (-not $origin) { return "" }

    if ($origin -match 'github\.com[:/](.+?)(\.git)?$') {
        return $matches[1]
    }

    return ""
}

$projectRoot = Get-ProjectRoot
$androidDir = Join-Path $projectRoot "android-client"
$settingsPath = Join-Path $projectRoot "config/settings.py"
$apkOutput = Join-Path $androidDir "app/build/outputs/apk/release/app-release.apk"

Write-Step "Проверка окружения"
Assert-Command git
Assert-Command gh

if (-not $env:JAVA_HOME) {
    throw "JAVA_HOME не задан. Пример: `$env:JAVA_HOME = 'C:\Program Files\Android\Android Studio\jbr'"
}

if (-not (Test-Path (Join-Path $env:JAVA_HOME "bin/java.exe"))) {
    throw "JAVA_HOME задан, но java.exe не найден: $env:JAVA_HOME"
}

$currentBranch = (git -C $projectRoot rev-parse --abbrev-ref HEAD).Trim()
if (-not $SkipBranchCheck -and $currentBranch -ne $TargetBranch) {
    throw "Текущая ветка '$currentBranch'. Для публикации нужен '$TargetBranch' (или используй -SkipBranchCheck)."
}

Write-Step "Чтение версии проекта"
$version = Get-AppVersion -settingsPath $settingsPath
if (-not $version) { throw "Пустая версия проекта" }
$tag = "android-v$version"
$title = "Android develop $version"
if (-not $ReleaseNotes) {
    $ReleaseNotes = "Android prerelease from $TargetBranch ($version)"
}

$repo = Resolve-Repo -root $projectRoot -explicitRepo $GitHubRepo
if (-not $repo) {
    throw "Не удалось определить GitHub repo. Передай -GitHubRepo owner/repo или задай ANDROID_GITHUB_REPOSITORY."
}

Write-Step "Проверка аутентификации GitHub"
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "gh не авторизован. Выполни: gh auth login"
}

if (-not $SkipBuild) {
    Write-Step "Сборка release APK"
    Push-Location $androidDir
    try {
        ./gradlew assembleRelease
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path $apkOutput)) {
    throw "APK не найден: $apkOutput"
}

$tempApk = Join-Path ([System.IO.Path]::GetTempPath()) $ApkAssetName
Copy-Item $apkOutput $tempApk -Force

$shaPath = "$tempApk.sha256"
Write-Step "Расчет SHA256"
if (Get-Command sha256sum -ErrorAction SilentlyContinue) {
    $hashLine = (sha256sum $tempApk).Trim()
    Set-Content -Path $shaPath -Value $hashLine
}
else {
    $h = Get-FileHash -Algorithm SHA256 $tempApk
    Set-Content -Path $shaPath -Value ("{0}  {1}" -f $h.Hash.ToLower(), [System.IO.Path]::GetFileName($tempApk))
}

Write-Step "Публикация prerelease в GitHub"
$existing = gh release view $tag --repo $repo 2>$null
if ($LASTEXITCODE -eq 0) {
    gh release upload $tag $tempApk $shaPath --repo $repo --clobber
    gh release edit $tag --repo $repo --prerelease --title $title --notes $ReleaseNotes
}
else {
    gh release create $tag $tempApk $shaPath --repo $repo --title $title --notes $ReleaseNotes --prerelease
}

Write-Step "Готово"
Write-Host "Опубликовано: tag=$tag repo=$repo asset=$ApkAssetName" -ForegroundColor Green
