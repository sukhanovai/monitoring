param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [switch]$SkipBuild,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}


function Ensure-CleanWorkingTree {
    $dirty = (git status --porcelain)
    if ($dirty) {
        throw "Working tree is not clean. Commit or stash changes before running script. Tip: git stash push -u -m prerelease-temp"
    }
}

function Get-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-GitHubRepo {
    $origin = (git remote get-url origin).Trim()
    if (-not $origin) {
        throw "Git remote 'origin' was not found or has empty URL."
    }

    if ($origin -match '^https://github\.com/(?<owner>[^/]+)/(?<repo>[^/]+?)(\.git)?$') {
        return @{ Owner = $Matches.owner; Repo = $Matches.repo }
    }

    if ($origin -match '^git@github\.com:(?<owner>[^/]+)/(?<repo>[^/]+?)(\.git)?$') {
        return @{ Owner = $Matches.owner; Repo = $Matches.repo }
    }

    throw "Unsupported origin URL format: $origin"
}

function Get-GitHubToken {
    if ($env:GH_TOKEN) { return $env:GH_TOKEN }
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN }
    return $null
}

function Invoke-GitHubApi {
    param(
        [string]$Method,
        [string]$Url,
        $Body,
        [byte[]]$Binary,
        [string]$ContentType = "application/json"
    )

    $token = Get-GitHubToken
    if (-not $token) {
        throw "GitHub token was not found. Set GH_TOKEN or GITHUB_TOKEN environment variable."
    }

    $headers = @{
        Authorization = "Bearer $token"
        Accept        = "application/vnd.github+json"
        "User-Agent"  = "monitoring-prerelease-script"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    if ($Binary) {
        $uploadHeaders = @{
            Authorization = "Bearer $token"
            Accept        = "application/vnd.github+json"
            "User-Agent"  = "monitoring-prerelease-script"
            "X-GitHub-Api-Version" = "2022-11-28"
            "Content-Type" = $ContentType
        }

        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $uploadHeaders -Body $Binary
    }

    if ($Body -ne $null) {
        $json = $Body | ConvertTo-Json -Depth 10
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -Body $json -ContentType "application/json"
    }

    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
}


function Resolve-ApkSource {
    param([string]$AndroidDir)

    $releaseDir = Join-Path $AndroidDir "app/build/outputs/apk/release"
    if (-not (Test-Path $releaseDir)) {
        throw "APK release directory not found: $releaseDir"
    }

    $preferred = @(
        Join-Path $releaseDir "app-release.apk",
        Join-Path $releaseDir "app-release-unsigned.apk"
    )

    foreach ($candidate in $preferred) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $latestApk = Get-ChildItem -Path $releaseDir -Filter "*.apk" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($latestApk) {
        return $latestApk.FullName
    }

    throw "APK file was not found in: $releaseDir"
}

function Publish-WithGh {
    param(
        [string]$ReleaseTag,
        [string]$ReleaseTitle,
        [string]$ApkTarget,
        [string]$Notes
    )

    $releaseExists = $true
    gh release view $ReleaseTag | Out-Null 2>$null
    if ($LASTEXITCODE -ne 0) {
        $releaseExists = $false
    }

    if (-not $releaseExists) {
        Write-Host "[6/7] Creating prerelease $ReleaseTag via gh..."
        gh release create $ReleaseTag $ApkTarget --title $ReleaseTitle --target develop --prerelease --notes $Notes
    }
    else {
        Write-Host "[6/7] Updating prerelease $ReleaseTag via gh..."
        gh release edit $ReleaseTag --title $ReleaseTitle --target develop --prerelease --notes $Notes
        gh release upload $ReleaseTag $ApkTarget --clobber
    }
}

function Publish-WithApi {
    param(
        [string]$ReleaseTag,
        [string]$ReleaseTitle,
        [string]$ApkTarget,
        [string]$ApkName,
        [string]$Notes
    )

    $repo = Get-GitHubRepo
    $owner = $repo.Owner
    $name = $repo.Repo

    Write-Host "[5/7] Checking GitHub release $ReleaseTag via API..."
    $release = $null
    try {
        $release = Invoke-GitHubApi -Method GET -Url "https://api.github.com/repos/$owner/$name/releases/tags/$ReleaseTag"
    }
    catch {
        $release = $null
    }

    if (-not $release) {
        Write-Host "[6/7] Creating prerelease $ReleaseTag via API..."
        $body = @{
            tag_name         = $ReleaseTag
            target_commitish = "develop"
            name             = $ReleaseTitle
            body             = $Notes
            draft            = $false
            prerelease       = $true
        }
        $release = Invoke-GitHubApi -Method POST -Url "https://api.github.com/repos/$owner/$name/releases" -Body $body
    }
    else {
        Write-Host "[6/7] Updating prerelease $ReleaseTag via API..."
        $editBody = @{
            target_commitish = "develop"
            name             = $ReleaseTitle
            body             = $Notes
            draft            = $false
            prerelease       = $true
        }
        $release = Invoke-GitHubApi -Method PATCH -Url "https://api.github.com/repos/$owner/$name/releases/$($release.id)" -Body $editBody
    }

    $assets = Invoke-GitHubApi -Method GET -Url "https://api.github.com/repos/$owner/$name/releases/$($release.id)/assets"
    foreach ($asset in $assets) {
        if ($asset.name -eq $ApkName) {
            Write-Host "[6/7] Removing existing asset $ApkName via API..."
            Invoke-GitHubApi -Method DELETE -Url "https://api.github.com/repos/$owner/$name/releases/assets/$($asset.id)" | Out-Null
        }
    }

    $bytes = [System.IO.File]::ReadAllBytes($ApkTarget)
    $uploadUrl = "https://uploads.github.com/repos/$owner/$name/releases/$($release.id)/assets?name=$ApkName"
    Write-Host "[6/7] Uploading APK asset via API..."
    Invoke-GitHubApi -Method POST -Url $uploadUrl -Binary $bytes -ContentType "application/vnd.android.package-archive" | Out-Null
}

Write-Host "[1/7] Checking required commands..."
Require-Command git
$ghAvailable = Get-CommandExists gh
if ($ghAvailable) {
    Write-Host "[1/7] Found gh CLI."
}
else {
    Write-Host "[1/7] gh CLI not found. Will use GitHub API fallback (requires GH_TOKEN or GITHUB_TOKEN)."
}

Push-Location $RepoRoot
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($branch -ne "develop") {
        throw "This script must be run from 'develop'. Current branch: '$branch'."
    }

    if (-not $AllowDirty) {
        Ensure-CleanWorkingTree
    }
    else {
        Write-Host "[2/7] Dirty working tree allowed by -AllowDirty"
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
    $apkSource = Resolve-ApkSource -AndroidDir $androidDir
    Write-Host "[4/7] Using APK: $apkSource"

    $artifactDir = Join-Path $RepoRoot "artifacts"
    New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null

    $apkName = "monitoring-android-$projectVersion-develop.apk"
    $apkTarget = Join-Path $artifactDir $apkName
    Copy-Item -Path $apkSource -Destination $apkTarget -Force

    $notes = @"
EN: Android prerelease for develop branch.
EN: Built from branch develop, version $projectVersion.
EN: Stable release in main remains unchanged.

RU: Android prerelease for develop branch.
RU: Built from branch develop, version $projectVersion.
RU: Stable release in main remains unchanged.
"@

    if ($ghAvailable) {
        Write-Host "[5/7] Checking GitHub release $releaseTag via gh..."
        Publish-WithGh -ReleaseTag $releaseTag -ReleaseTitle $releaseTitle -ApkTarget $apkTarget -Notes $notes
    }
    else {
        Publish-WithApi -ReleaseTag $releaseTag -ReleaseTitle $releaseTitle -ApkTarget $apkTarget -ApkName $apkName -Notes $notes
    }

    Write-Host "[7/7] Done. Prerelease published: $releaseTag"
    Write-Host "APK: $apkTarget"
}
finally {
    Pop-Location
}
