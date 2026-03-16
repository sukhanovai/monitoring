param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [switch]$SkipBuild,
    [switch]$AllowDirty,
    [switch]$AutoStashDirty,
    [string]$GitHubToken
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

function Push-TempStash {
    param([string]$Message)

    $stashOutput = git stash push -u -m $Message
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create temporary stash before prerelease publish."
    }

    if ($stashOutput -match "No local changes to save") {
        return $null
    }

    return "stash@{0}"
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
    $script:GitHubTokenSearchPaths = @()
    $script:GitHubTokenEnvSearchPaths = @()

    if ($GitHubToken) { return $GitHubToken.Trim() }
    if ($env:GH_TOKEN) { return $env:GH_TOKEN.Trim() }
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN.Trim() }
    if ($env:GITHUB_PAT) { return $env:GITHUB_PAT.Trim() }

    $windowsHome = $null
    if ($env:HOMEDRIVE -and $env:HOMEPATH) {
    $windowsHome = Join-Path $env:HOMEDRIVE $env:HOMEPATH
    }

    $homeCandidates = @($HOME, $env:USERPROFILE, $windowsHome) |
        Where-Object { $_ } |
        Select-Object -Unique

    $tokenFiles = @(
        (Join-Path $RepoRoot ".github_token"),
        (Join-Path $RepoRoot ".github-token")
    )

    $envFiles = @(
        (Join-Path $RepoRoot ".env")
    )

    foreach ($homeDir in $homeCandidates) {
        $tokenFiles += (Join-Path $homeDir ".github_token")
        $tokenFiles += (Join-Path $homeDir ".github-token")
        $envFiles += (Join-Path $homeDir ".env")
    }

    $tokenFiles = $tokenFiles | Select-Object -Unique
    $envFiles = $envFiles | Select-Object -Unique
    $script:GitHubTokenSearchPaths = $tokenFiles
    $script:GitHubTokenEnvSearchPaths = $envFiles

    foreach ($tokenFile in $tokenFiles) {
        if (Test-Path $tokenFile) {
            $token = (Get-Content -Path $tokenFile -Raw).Trim()
            if ($token) {
                return $token
            }
        }
    }

    foreach ($envFile in $envFiles) {
        if (-not (Test-Path $envFile)) {
            continue
        }

        $envContent = Get-Content -Path $envFile
        foreach ($line in $envContent) {
            if ($line -match '^\s*(?:export\s+|setx?\s+|\$env:)?(GH_TOKEN|GITHUB_TOKEN|GITHUB_PAT)\s*(?:=|:)\s*(?<value>.+?)\s*$') {
                $value = $Matches.value.Trim()
                $value = ($value -replace '\s+#.*$', '').Trim()
                $value = ($value -replace '\s+;.*$', '').Trim()
                $value = ($value -replace '\s+//.*$', '').Trim()
                $value = $value.Trim('"').Trim("'")
                if ($value) {
                    return $value
                }
            }
        }
    }

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
        $pathsHint = ($script:GitHubTokenSearchPaths | ForEach-Object { "- $_" }) -join "`n"
        $envPathsHint = ($script:GitHubTokenEnvSearchPaths | ForEach-Object { "- $_" }) -join "`n"
        throw @"
GitHub token was not found.
Set GH_TOKEN, GITHUB_TOKEN, or GITHUB_PAT environment variable,
or pass -GitHubToken parameter,
or save token into one of files:
$pathsHint
or add one of GH_TOKEN/GITHUB_TOKEN/GITHUB_PAT into .env file:
$envPathsHint

PowerShell examples:
`$env:GH_TOKEN = "ghp_xxx"                        # current session
setx GH_TOKEN "ghp_xxx"                          # persist for next sessions
./scripts/publish_android_prerelease.ps1 -GitHubToken "ghp_xxx"
"@ 
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

function Ensure-GitHubAuthReady {
    param([bool]$GhAvailable)

    if ($GhAvailable) {
        return
    }

    $token = Get-GitHubToken
    if (-not $token) {
        $pathsHint = ($script:GitHubTokenSearchPaths | ForEach-Object { "- $_" }) -join "`n"
        $envPathsHint = ($script:GitHubTokenEnvSearchPaths | ForEach-Object { "- $_" }) -join "`n"
        throw @"
GitHub token was not found.
gh CLI is not available, so GitHub API fallback requires a token before build/publish starts.

Set GH_TOKEN, GITHUB_TOKEN, or GITHUB_PAT environment variable,
or pass -GitHubToken parameter,
or save token into one of files:
$pathsHint
or add one of GH_TOKEN/GITHUB_TOKEN/GITHUB_PAT into .env file:
$envPathsHint

PowerShell examples:
`$env:GH_TOKEN = "ghp_xxx"                        # current session
setx GH_TOKEN "ghp_xxx"                          # persist for next sessions
./scripts/publish_android_prerelease.ps1 -GitHubToken "ghp_xxx"
"@
    }
}


function Resolve-ApkSource {
    param([string]$AndroidDir)

    $releaseDir = Join-Path $AndroidDir "app/build/outputs/apk/release"
    if (-not (Test-Path $releaseDir)) {
        throw "APK release directory not found: $releaseDir"
    }

    $preferred = @(
        (Join-Path $releaseDir "app-release.apk")
        (Join-Path $releaseDir "app-release-unsigned.apk")
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

try {
    Write-Host "[1/7] Checking required commands..."
    Require-Command git
    $ghAvailable = Get-CommandExists gh
    if ($ghAvailable) {
        Write-Host "[1/7] Found gh CLI."
    }
    else {
        Write-Host "[1/7] gh CLI not found. Will use GitHub API fallback (requires GH_TOKEN or GITHUB_TOKEN)."
    }

    Ensure-GitHubAuthReady -GhAvailable $ghAvailable

    Push-Location $RepoRoot
    $tempStashRef = $null
    try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($branch -ne "develop") {
        throw "This script must be run from 'develop'. Current branch: '$branch'."
    }

    if ($AllowDirty -and $AutoStashDirty) {
        throw "-AllowDirty and -AutoStashDirty cannot be used together. Choose one mode."
    }

    if ($AutoStashDirty) {
        $dirty = (git status --porcelain)
        if ($dirty) {
            Write-Host "[2/7] Dirty working tree detected. Creating temporary stash..."
            $tempStashRef = Push-TempStash -Message "prerelease-temp"
        }
        else {
            Write-Host "[2/7] Working tree already clean. Temporary stash is not required."
        }
    }
    elseif (-not $AllowDirty) {
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
        if ($tempStashRef) {
            Write-Host "[7/7] Restoring temporary stash $tempStashRef..."
            git stash pop $tempStashRef | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[7/7] Warning: failed to auto-restore temporary stash $tempStashRef. Restore it manually with: git stash list"
            }
        }

        Pop-Location
    }
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
