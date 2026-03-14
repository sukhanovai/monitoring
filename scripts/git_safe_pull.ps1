param(
    [string]$Remote = "origin",
    [string]$Branch = "develop",
    [switch]$NoRebase,
    [switch]$KeepStash
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

Require-Command git

$stashCreated = $false
$stashName = "auto-stash-before-pull-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

try {
    $dirty = git status --porcelain
    if ($dirty) {
        Write-Host "[1/4] Working tree is dirty. Creating temporary stash..."
        git stash push -u -m $stashName | Out-Null
        $stashCreated = $true
    }
    else {
        Write-Host "[1/4] Working tree is clean."
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
