param(
    [string]$Remote = "origin",
    [string]$Branch = "develop",
    [switch]$NoRebase,
    [switch]$KeepStash,
    [switch]$OnlyAndroidClientConfig
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

Require-Command git

function Has-ChangesInPath {
    param([string[]]$Paths)

    $status = git status --porcelain -- $Paths
    return [bool]$status
}

$stashCreated = $false
$stashName = "auto-stash-before-pull-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

try {
    if ($OnlyAndroidClientConfig) {
        $paths = @("android-client/build.gradle.kts", "android-client/gradle.properties", "android-client/gradle/wrapper/gradle-wrapper.properties")
        $targetDirty = Has-ChangesInPath -Paths $paths
        if ($targetDirty) {
            Write-Host "[1/4] Android config files (including Gradle wrapper properties) are dirty. Creating targeted stash..."
            git stash push -m $stashName -- $paths | Out-Null
            $stashCreated = $true
        }
        else {
            Write-Host "[1/4] Target Android config files are clean."
        }
    }
    else {
        $dirty = git status --porcelain
        if ($dirty) {
            Write-Host "[1/4] Working tree is dirty. Creating temporary stash..."
            git stash push -u -m $stashName | Out-Null
            $stashCreated = $true
        }
        else {
            Write-Host "[1/4] Working tree is clean."
        }
    }

    Write-Host "[2/4] Pulling $Remote/$Branch..."
    if ($NoRebase) {
        git pull $Remote $Branch
    }
    else {
        git pull --rebase $Remote $Branch
    }

    if ($stashCreated -and -not $KeepStash) {
        Write-Host "[3/4] Restoring stashed changes..."
        git stash pop
    }
    elseif ($stashCreated -and $KeepStash) {
        Write-Host "[3/4] Stash kept as requested (-KeepStash): $stashName"
    }
    else {
        Write-Host "[3/4] No stash to restore."
    }

    Write-Host "[4/4] Done."
}
catch {
    Write-Host "Error: $($_.Exception.Message)"
    if ($stashCreated) {
        Write-Host "A temporary stash may still exist. Check with: git stash list"
    }
    throw
}
