$ErrorActionPreference = "Stop"

Write-Host "[1/2] Reset local tracked changes to HEAD..."
git restore --source=HEAD --staged --worktree -- .
if ($LASTEXITCODE -ne 0) {
    throw "git restore failed"
}

Write-Host "[2/2] Pull latest develop with rebase..."
git pull --rebase origin develop
if ($LASTEXITCODE -ne 0) {
    throw "git pull --rebase failed"
}

Write-Host "Done. Working tree synchronized with origin/develop."
