param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [switch]$SkipBuild,
    [switch]$AllowDirty,
    [switch]$AutoStashDirty,
    [switch]$UpdateDocsLinks,
    [switch]$NoWorkingTreeSideEffects
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
        $dirtyPreview = ($dirty | Select-Object -First 15) -join "`n"
        throw @"
Working tree is not clean. Commit or stash changes before running script.

Quick fix:
  ./scripts/publish_android_prerelease.ps1 -AutoStashDirty

Manual stash:
  git stash push -u -m prerelease-temp
  ./scripts/publish_android_prerelease.ps1

Advanced mode (unsafe, use only if you really know what you are doing):
  ./scripts/publish_android_prerelease.ps1 -AllowDirty

Dirty files preview (first 15):
$dirtyPreview
"@
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

function Get-GhCommand {
    $ghCommand = Get-Command gh -ErrorAction SilentlyContinue
    if ($ghCommand) {
        return $ghCommand.Source
    }

    $windowsHome = $null
    if ($env:HOMEDRIVE -and $env:HOMEPATH) {
        $windowsHome = Join-Path $env:HOMEDRIVE $env:HOMEPATH
    }

    $commonCandidates = @(
        "C:/Program Files/GitHub CLI/gh.exe",
        "C:/Program Files/GitHub CLI/bin/gh.exe",
        "C:/Program Files (x86)/GitHub CLI/gh.exe",
        "C:/Program Files (x86)/GitHub CLI/bin/gh.exe"
    )

    $homeCandidates = @($env:LOCALAPPDATA, $env:USERPROFILE, $HOME, $windowsHome) |
        Where-Object { $_ } |
        Select-Object -Unique

    foreach ($homeDir in $homeCandidates) {
        $commonCandidates += (Join-Path $homeDir "scoop/shims/gh.exe")
        $commonCandidates += (Join-Path $homeDir "scoop/apps/gh/current/bin/gh.exe")
        $commonCandidates += (Join-Path $homeDir "AppData/Local/Microsoft/WinGet/Links/gh.exe")
        $commonCandidates += (Join-Path $homeDir "AppData/Local/Programs/GitHub CLI/gh.exe")
        $commonCandidates += (Join-Path $homeDir "AppData/Local/Programs/GitHub CLI/bin/gh.exe")
    }

    if ($env:LOCALAPPDATA) {
        $commonCandidates += (Join-Path $env:LOCALAPPDATA "Programs/GitHub CLI/gh.exe")
    }

    $whereGh = $null
    try {
        $whereGh = & where.exe gh 2>$null | Select-Object -First 1
    }
    catch {
        $whereGh = $null
    }

    if ($whereGh -and (Test-Path $whereGh)) {
        return $whereGh
    }

    foreach ($candidate in ($commonCandidates | Select-Object -Unique)) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Invoke-Gh {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    if (-not $script:GhCommandPath) {
        throw "gh command path is not initialized."
    }

    & $script:GhCommandPath @Args
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


function Get-DefaultSecureTokenFilePath {
    $windowsHome = $null
    if ($env:HOMEDRIVE -and $env:HOMEPATH) {
        $windowsHome = Join-Path $env:HOMEDRIVE $env:HOMEPATH
    }

    $homeDir = $HOME
    if (-not $homeDir) { $homeDir = $env:USERPROFILE }
    if (-not $homeDir) { $homeDir = $windowsHome }
    if (-not $homeDir) {
        throw "Cannot resolve home directory for secure token file path."
    }

    return Join-Path $homeDir ".monitoring/github_token"
}

function Get-GitHubToken {
    $script:GitHubTokenSearchPaths = @()
    $script:GitHubTokenEnvSearchPaths = @()
    $script:GitHubTokenGhConfigSearchPaths = @()

    if ($env:GH_TOKEN) { return $env:GH_TOKEN.Trim() }
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN.Trim() }
    if ($env:GITHUB_PAT) { return $env:GITHUB_PAT.Trim() }

    $persistedUserGhToken = [Environment]::GetEnvironmentVariable("GH_TOKEN", "User")
    if ($persistedUserGhToken) { return $persistedUserGhToken.Trim() }

    $persistedUserGithubToken = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")
    if ($persistedUserGithubToken) { return $persistedUserGithubToken.Trim() }

    $persistedUserGithubPat = [Environment]::GetEnvironmentVariable("GITHUB_PAT", "User")
    if ($persistedUserGithubPat) { return $persistedUserGithubPat.Trim() }

    $persistedMachineGhToken = [Environment]::GetEnvironmentVariable("GH_TOKEN", "Machine")
    if ($persistedMachineGhToken) { return $persistedMachineGhToken.Trim() }

    $persistedMachineGithubToken = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "Machine")
    if ($persistedMachineGithubToken) { return $persistedMachineGithubToken.Trim() }

    $persistedMachineGithubPat = [Environment]::GetEnvironmentVariable("GITHUB_PAT", "Machine")
    if ($persistedMachineGithubPat) { return $persistedMachineGithubPat.Trim() }

    $windowsHome = $null
    if ($env:HOMEDRIVE -and $env:HOMEPATH) {
    $windowsHome = Join-Path $env:HOMEDRIVE $env:HOMEPATH
    }

    $homeCandidates = @($HOME, $env:USERPROFILE, $windowsHome) |
        Where-Object { $_ } |
        Select-Object -Unique

    $secureTokenFile = Get-DefaultSecureTokenFilePath

    $tokenFiles = @(
        $secureTokenFile,
        (Join-Path $RepoRoot ".github_token"),
        (Join-Path $RepoRoot ".github-token")
    )

    $envFiles = @(
        (Join-Path $RepoRoot ".env")
    )

    $ghConfigFiles = @()

    foreach ($homeDir in $homeCandidates) {
        $tokenFiles += (Join-Path $homeDir ".github_token")
        $tokenFiles += (Join-Path $homeDir ".github-token")
        $envFiles += (Join-Path $homeDir ".env")
        $ghConfigFiles += (Join-Path $homeDir ".config/gh/hosts.yml")
        $ghConfigFiles += (Join-Path $homeDir "AppData/Roaming/GitHub CLI/hosts.yml")
    }

    $tokenFiles = $tokenFiles | Select-Object -Unique
    $envFiles = $envFiles | Select-Object -Unique
    $ghConfigFiles = $ghConfigFiles | Select-Object -Unique
    $script:GitHubTokenSearchPaths = $tokenFiles
    $script:GitHubTokenEnvSearchPaths = $envFiles
    $script:GitHubTokenGhConfigSearchPaths = $ghConfigFiles

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
            if ($line -match '^\s*(?:export\s+|setx?\s+|\$env:)?(?<name>GH_TOKEN|GITHUB_TOKEN|GITHUB_PAT)\s*(?<separator>=|:|\s)\s*(?<value>.+?)\s*$') {
                $value = $Matches.value.Trim()
                $value = ($value -replace '\s+#.*$', '').Trim()
                $value = ($value -replace '\s+;.*$', '').Trim()
                $value = ($value -replace '\s+//.*$', '').Trim()
                if ($Matches.separator -match '^\s$') {
                    $value = ($value -replace '^\S+\s+(?<token>gh[pousr]_[A-Za-z0-9_]+).*$','$1').Trim()
                }
                $value = $value.Trim('"').Trim("'")
                if ($value) {
                    return $value
                }
            }
        }
    }

    foreach ($ghConfigPath in $ghConfigFiles) {
        if (-not (Test-Path $ghConfigPath)) {
            continue
        }

        $hostsContent = Get-Content -Path $ghConfigPath
        $insideGithub = $false
        foreach ($line in $hostsContent) {
            if ($line -match '^\s*github\.com\s*:\s*$') {
                $insideGithub = $true
                continue
            }

            if ($insideGithub -and $line -match '^\S') {
                $insideGithub = $false
            }

            if ($insideGithub -and $line -match '^\s*oauth_token\s*:\s*(?<value>.+?)\s*$') {
                $value = $Matches.value.Trim().Trim('"').Trim("'")
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
        $ghConfigPathsHint = ($script:GitHubTokenGhConfigSearchPaths | ForEach-Object { "- $_" }) -join "`n"
        throw @"
GitHub token was not found.
Set GH_TOKEN, GITHUB_TOKEN, or GITHUB_PAT environment variable,
or save token into one of files:
$pathsHint
or add one of GH_TOKEN/GITHUB_TOKEN/GITHUB_PAT into .env file:
$envPathsHint
or login via gh (`gh auth login`) so token can be read from hosts.yml:
$ghConfigPathsHint

PowerShell examples:
`$env:GH_TOKEN = "ghp_xxx"                        # current session
setx GH_TOKEN "ghp_xxx"                          # persist for next sessions
"ghp_xxx" | Set-Content -NoNewline $HOME/.monitoring/github_token # secure user-local token file
./scripts/publish_android_prerelease.ps1

How to create PAT quickly:
1) Open https://github.com/settings/tokens (classic) or https://github.com/settings/personal-access-tokens/new
2) Create token with required repo/release scopes
3) Save it into `$HOME/.monitoring/github_token` (or one of paths above)

Android Studio terminal tip:
after `setx`, restart Android Studio terminal/IDE so process env is refreshed,
or run script with `$env:GH_TOKEN in current terminal session.
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
        $ghConfigPathsHint = ($script:GitHubTokenGhConfigSearchPaths | ForEach-Object { "- $_" }) -join "`n"
        throw @"
GitHub token was not found.
gh CLI is not available, so GitHub API fallback requires a token before build/publish starts.

Set GH_TOKEN, GITHUB_TOKEN, or GITHUB_PAT environment variable,
or save token into one of files:
$pathsHint
or add one of GH_TOKEN/GITHUB_TOKEN/GITHUB_PAT into .env file:
$envPathsHint
or login via gh (`gh auth login`) so token can be read from hosts.yml:
$ghConfigPathsHint

PowerShell examples:
`$env:GH_TOKEN = "ghp_xxx"                        # current session
setx GH_TOKEN "ghp_xxx"                          # persist for next sessions
"ghp_xxx" | Set-Content -NoNewline $HOME/.monitoring/github_token # secure user-local token file
./scripts/publish_android_prerelease.ps1

How to create PAT quickly:
1) Open https://github.com/settings/tokens (classic) or https://github.com/settings/personal-access-tokens/new
2) Create token with required repo/release scopes
3) Save it into `$HOME/.monitoring/github_token` (or one of paths above)

Android Studio terminal tip:
after `setx`, restart Android Studio terminal/IDE so process env is refreshed,
or run script with `$env:GH_TOKEN in current terminal session.
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
        (Join-Path $releaseDir "app-universal-release.apk")
    )

    foreach ($candidate in $preferred) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $releaseApks = Get-ChildItem -Path $releaseDir -Filter "*.apk" -File

    $signedCandidates = $releaseApks |
        Where-Object { $_.Name -notmatch "unsigned" -and $_.Name -notmatch "-x86|-x86_64|-arm64-v8a|-armeabi-v7a|-universal-debug" } |
        Sort-Object LastWriteTime -Descending

    if ($signedCandidates) {
        return $signedCandidates[0].FullName
    }

    $unsigned = $releaseApks | Where-Object { $_.Name -match "unsigned" }
    if ($unsigned) {
        throw @"
Only unsigned APK was found in release outputs. Such file is not installable for prerelease distribution.
Configure release signing (or use debug signing for prerelease) and rebuild.
Found files:
$($releaseApks.Name -join "`n")
"@
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
    Invoke-Gh release view $ReleaseTag | Out-Null 2>$null
    if ($LASTEXITCODE -ne 0) {
        $releaseExists = $false
    }

    if (-not $releaseExists) {
        Write-Host "[6/7] Creating prerelease $ReleaseTag via gh..."
        Invoke-Gh release create $ReleaseTag $ApkTarget --title $ReleaseTitle --target develop --prerelease --notes $Notes
    }
    else {
        Write-Host "[6/7] Updating prerelease $ReleaseTag via gh..."
        Invoke-Gh release edit $ReleaseTag --title $ReleaseTitle --target develop --prerelease --notes $Notes
        Invoke-Gh release upload $ReleaseTag $ApkTarget --clobber
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

function Update-PrereleaseApkLinkInFile {
    param(
        [string]$FilePath,
        [string]$DownloadUrl
    )

    if (-not (Test-Path $FilePath)) {
        return
    }

    $content = Get-Content -Path $FilePath -Raw
    $updated = [regex]::Replace(
        $content,
        '(<!-- ANDROID_PRERELEASE_APK_LINK_START -->)(.*?)(<!-- ANDROID_PRERELEASE_APK_LINK_END -->)',
        "`$1$DownloadUrl`$3"
    )

    if ($updated -ne $content) {
        Set-Content -Path $FilePath -Value $updated -Encoding UTF8
    }
}

function Update-PrereleaseApkLinks {
    param(
        [string]$RepoRoot,
        [string]$ReleaseTag,
        [string]$ApkName
    )

    $defaultOwner = "sukhanovai"
    $defaultRepo = "monitoring"

    try {
        $repo = Get-GitHubRepo
    }
    catch {
        Write-Host "[4/7] Warning: failed to resolve origin repo. Fallback to $defaultOwner/$defaultRepo"
        $repo = @{ Owner = $defaultOwner; Repo = $defaultRepo }
    }

    if (-not $repo.Owner -or -not $repo.Repo) {
        Write-Host "[4/7] Warning: empty owner/repo from git remote. Fallback to $defaultOwner/$defaultRepo"
        $repo = @{ Owner = $defaultOwner; Repo = $defaultRepo }
    }

    $downloadUrl = "https://github.com/$($repo.Owner)/$($repo.Repo)/releases/download/$ReleaseTag/$ApkName"

    $filesToUpdate = @(
        (Join-Path $RepoRoot "README.md"),
        (Join-Path $RepoRoot "docs/android_mobile_app.md")
    )

    foreach ($path in $filesToUpdate) {
        Update-PrereleaseApkLinkInFile -FilePath $path -DownloadUrl $downloadUrl
    }

    return $downloadUrl
}



try {
    Write-Host "[1/7] Checking required commands..."
    Require-Command git
    $script:GhCommandPath = Get-GhCommand
    $ghAvailable = [bool]$script:GhCommandPath
    if ($ghAvailable) {
        Write-Host "[1/7] Found gh CLI at: $script:GhCommandPath"
    }
    else {
        Write-Host "[1/7] gh CLI not found in PATH/common Windows locations. Will use GitHub API fallback (requires GH_TOKEN, GITHUB_TOKEN, or GITHUB_PAT)."
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

    if (-not $ghAvailable) {
        Write-Host "[2/7] Verifying GitHub token before build (API fallback)..."
        Ensure-GitHubAuthReady -GhAvailable $false
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

    $repoOwner = "sukhanovai"
    $repoName = "monitoring"
    try {
        $repo = Get-GitHubRepo
        if ($repo.Owner -and $repo.Repo) {
            $repoOwner = $repo.Owner
            $repoName = $repo.Repo
        }
    }
    catch {
        Write-Host "[4/7] Warning: failed to resolve origin repo. Fallback to $repoOwner/$repoName"
    }

    $downloadUrl = "https://github.com/$repoOwner/$repoName/releases/download/$releaseTag/$apkName"

    if ($UpdateDocsLinks) {
        Write-Host "[4/7] Warning: -UpdateDocsLinks is deprecated and ignored to avoid local README/docs edits and pull conflicts."
        Write-Host "[4/7] Docs were NOT modified. Copy URL manually if needed: $downloadUrl"
    }
    else {
        Write-Host "[4/7] Docs link update skipped (default). README/docs are not edited by this script."
    }

    $notes = @"
EN: Android prerelease for develop branch.
EN: Built from branch develop, version $projectVersion.
EN: Stable release in main remains unchanged.

RU: Пререлиз Android для ветки develop.
RU: Собрано из ветки develop, версия $projectVersion.
RU: Стабильный релиз в main не изменяется.
"@

    if ($ghAvailable) {
        Write-Host "[5/7] Checking GitHub release $releaseTag via gh..."
        Publish-WithGh -ReleaseTag $releaseTag -ReleaseTitle $releaseTitle -ApkTarget $apkTarget -Notes $notes
    }
    else {
        Publish-WithApi -ReleaseTag $releaseTag -ReleaseTitle $releaseTitle -ApkTarget $apkTarget -ApkName $apkName -Notes $notes
    }

    if ($NoWorkingTreeSideEffects) {
        $postDirty = (git status --porcelain)
        if ($postDirty) {
            throw @"
Script finished publish, but local working tree has modifications.
To avoid future pull conflicts, run recovery script:
  ./scripts/android_studio_pull_recover.ps1

Dirty files:
$($postDirty -join "`n")
"@
        }
    }

    Write-Host "[7/7] Done. Prerelease published: $releaseTag"
    Write-Host "APK: $apkTarget"
    Write-Host "APK download URL: $downloadUrl"
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
