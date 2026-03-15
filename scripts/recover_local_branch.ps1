param(
    [string]$Remote = "origin",
    [string]$BaseBranch = "develop",
    [switch]$CreateBackupPatch = $true,
    [switch]$NoClean,
    [switch]$NoHardReset
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

Require-Command git

$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
if (-not $currentBranch) {
    throw "Failed to detect current git branch."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = "artifacts"
$backupPatch = Join-Path $backupDir ("backup-before-recover-$currentBranch-$timestamp.patch")

Write-Host "[1/5] Current branch: $currentBranch"

if ($CreateBackupPatch) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "[2/5] Creating backup patch of current branch delta vs $Remote/$BaseBranch..."
    git fetch $Remote $BaseBranch
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to fetch $Remote/$BaseBranch"
    }

    git format-patch "$Remote/$BaseBranch..HEAD" --stdout > $backupPatch
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create backup patch"
    }

    Write-Host "[2/5] Backup patch saved: $(Resolve-Path $backupPatch)"
}
else {
    Write-Host "[2/5] Backup patch skipped by flag."
}

Write-Host "[3/5] Fetching latest $Remote/$BaseBranch..."
git fetch $Remote $BaseBranch
if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch $Remote/$BaseBranch"
}

if (-not $NoHardReset) {
    Write-Host "[4/5] Hard resetting current branch to $Remote/$BaseBranch..."
    git reset --hard "$Remote/$BaseBranch"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to hard reset branch to $Remote/$BaseBranch"
    }
}
else {
    Write-Host "[4/5] Hard reset skipped by flag."
}

if (-not $NoClean) {
    Write-Host "[5/5] Cleaning untracked files (git clean -fd)..."
    git clean -fd
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to clean untracked files"
    }
}
else {
    Write-Host "[5/5] git clean skipped by flag."
}

Write-Host "Done. Branch '$currentBranch' is aligned with $Remote/$BaseBranch."
if ($CreateBackupPatch) {
    Write-Host "If needed, re-apply selected changes from patch with: git am < \"$(Resolve-Path $backupPatch)\""
}
