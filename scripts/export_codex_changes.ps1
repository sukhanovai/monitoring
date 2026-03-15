param(
    [string]$OutputDir = "artifacts",
    [int]$LastCommits = 1,
    [string]$FromRef,
    [string]$ToRef = "HEAD"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

Require-Command git

if ($LastCommits -lt 1) {
    throw "LastCommits must be >= 1"
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not $FromRef) {
    $FromRef = "HEAD~$LastCommits"
}

$patchFile = Join-Path $OutputDir ("codex-changes-$timestamp.patch")

Write-Host "[1/3] Creating patch from $FromRef..$ToRef"
git format-patch "$FromRef..$ToRef" --stdout > $patchFile
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create patch from range $FromRef..$ToRef"
}

$absPatch = (Resolve-Path $patchFile).Path

Write-Host "[2/3] Patch saved: $absPatch"
Write-Host "[3/3] Apply locally with:"
Write-Host "  git am < \"$absPatch\""

