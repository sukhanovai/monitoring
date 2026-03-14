param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

Write-Host "[1/7] Checking required commands..."
Require-Command git
Require-Command gh

Push-Location $RepoRoot
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($branch -ne "develop") {
        throw "This script must be run from 'develop'. Current branch: '$branch'."
    }

    Write-Host "[2/7] Reading project version from config/settings.py..."
    $settingsPath = Join-Path $RepoRoot "config/settings.py"
    if (-not (Test-Path $settingsPath)) {
        throw "File not found: $settingsPath"
    }

    $settingsContent = Get-Content -Path $settingsPath -Raw
    $versionMatch = [regex]::Match($settingsContent, 'APP_VERSION\s*=\s*"(?<version>\d+\.\d+\.\d+)"')
    if (-not $versionMatch.Success) {
        throw "APP_VERSION was not found in config/settings.py"
    }

    $projectVersion = $versionMatch.Groups["version"].Value
    $releaseTag = "v$projectVersion-develop"
    $releaseTitle = "Android develop prerelease $projectVersion"

    $androidDir = Join-Path $RepoRoot "android-client"
    if (-not (Test-Path $androidDir)) {
        throw "Directory not found: $androidDir"
    }

    if (-not $SkipBuild) {
        Write-Host "[3/7] Building release APK..."
        Push-Location $androidDir
        try {
            if (Test-Path (Join-Path $androidDir "gradlew.bat")) {
                & .\gradlew.bat :app:assembleRelease
            }
            elseif (Test-Path (Join-Path $androidDir "gradlew")) {
                & ./gradlew :app:assembleRelease
            }
            else {
                throw "gradlew/gradlew.bat was not found in android-client"
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "[3/7] Build skipped by -SkipBuild flag"
    }

    Write-Host "[4/7] Checking APK output..."
    $apkSource = Join-Path $androidDir "app/build/outputs/apk/release/app-release.apk"
    if (-not (Test-Path $apkSource)) {
        throw "APK not found: $apkSource"
    }

    $artifactDir = Join-Path $RepoRoot "artifacts"
    New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null

    $apkName = "monitoring-android-$projectVersion-develop.apk"
    $apkTarget = Join-Path $artifactDir $apkName
    Copy-Item -Path $apkSource -Destination $apkTarget -Force

    Write-Host "[5/7] Checking GitHub release $releaseTag..."
    $releaseExists = $true
    gh release view $releaseTag | Out-Null 2>$null
    if ($LASTEXITCODE -ne 0) {
        $releaseExists = $false
    }

    $notes = @"
EN: Android prerelease for develop branch.
EN: Built from branch develop, version $projectVersion.
EN: Stable release in main remains unchanged.

RU: Android prerelease for develop branch.
RU: Built from branch develop, version $projectVersion.
RU: Stable release in main remains unchanged.
"@

    if (-not $releaseExists) {
        Write-Host "[6/7] Creating prerelease $releaseTag..."
        gh release create $releaseTag $apkTarget --title $releaseTitle --target develop --prerelease --notes $notes
    }
    else {
        Write-Host "[6/7] Updating prerelease $releaseTag..."
        gh release edit $releaseTag --title $releaseTitle --target develop --prerelease --notes $notes
        gh release upload $releaseTag $apkTarget --clobber
    }

    Write-Host "[7/7] Done. Prerelease published: $releaseTag"
    Write-Host "APK: $apkTarget"
}
finally {
    Pop-Location
}
