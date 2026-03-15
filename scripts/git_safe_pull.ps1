param(
    [string]$Remote = "origin",
    [string]$Branch = "develop",
    [switch]$NoRebase,
    [switch]$KeepStash,
    [switch]$OnlyAndroidClientConfig,
    [switch]$ResetAndroidClientConfigToRemote,
    [switch]$AutoDetectAndroidClientConfigOnly,
    [switch]$HardResetToRemote
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

function Get-DirtyPaths {
    $trackedChanges = git diff --name-only HEAD
    $untrackedChanges = git ls-files --others --exclude-standard

    $allChanges = @()
    if ($trackedChanges) {
        $allChanges += $trackedChanges
    }
    if ($untrackedChanges) {
        $allChanges += $untrackedChanges
    }

    if (-not $allChanges) {
        return @()
    }

    return $allChanges |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ } |
        Sort-Object -Unique
}

Require-Command git

$stashCreated = $false
$stashName = "auto-stash-before-pull-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

$targetBackupDir = $null
$targetBackupCreated = $false
$targetDirtyPaths = @()

$androidConfigPaths = @(
    "android-client/build.gradle.kts",
    "android-client/gradle.properties",
    "android-client/gradle/wrapper/gradle-wrapper.properties"
)

try {
    if ($HardResetToRemote -and ($OnlyAndroidClientConfig -or $ResetAndroidClientConfigToRemote -or $AutoDetectAndroidClientConfigOnly -or $KeepStash)) {
        throw "-HardResetToRemote cannot be combined with safe-pull stash/Android-config options."
    }

    if ($HardResetToRemote) {
        Write-Host "[1/4] Hard reset mode enabled. All local changes will be discarded..."
        git fetch $Remote $Branch
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to fetch $Remote/$Branch"
        }

        git reset --hard "$Remote/$Branch"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to hard reset to $Remote/$Branch"
        }

        git clean -fd
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to clean untracked files"
        }

        Write-Host "[2/4] Repository reset to $Remote/$Branch."
        Write-Host "[3/4] No stash/backup restore required in hard reset mode."
        Write-Host "[4/4] Done."
        return
    }

    if ($ResetAndroidClientConfigToRemote -and -not $OnlyAndroidClientConfig) {
        throw "-ResetAndroidClientConfigToRemote can be used only with -OnlyAndroidClientConfig."
    }

    if ($AutoDetectAndroidClientConfigOnly -and $OnlyAndroidClientConfig) {
        throw "Use either -AutoDetectAndroidClientConfigOnly or -OnlyAndroidClientConfig, not both."
    }

    if ($AutoDetectAndroidClientConfigOnly) {
        $dirtyPaths = Get-DirtyPaths
        if ($dirtyPaths.Count -gt 0) {
            $onlyAndroidConfigDirty = $true
            foreach ($path in $dirtyPaths) {
                if ($androidConfigPaths -notcontains $path) {
                    $onlyAndroidConfigDirty = $false
                    break
                }
            }

            if ($onlyAndroidConfigDirty) {
                Write-Host "[1/4] Auto-detected changes only in Android config files. Switching to -OnlyAndroidClientConfig mode."
                $OnlyAndroidClientConfig = $true
            }
            else {
                Write-Host "[1/4] Auto-detect found changes outside Android config files. Using regular stash mode."
            }
        }
        else {
            Write-Host "[1/4] Working tree is clean."
        }
    }

    if ($OnlyAndroidClientConfig) {
        $otherDirty = git status --porcelain -- . ":(exclude)android-client/build.gradle.kts" ":(exclude)android-client/gradle.properties" ":(exclude)android-client/gradle/wrapper/gradle-wrapper.properties"
        if ($otherDirty) {
            throw "OnlyAndroidClientConfig mode supports changes only in target Android config files. Commit/stash other files first."
        }

        if ($ResetAndroidClientConfigToRemote) {
            $unmerged = git diff --name-only --diff-filter=U
            if ($unmerged) {
                foreach ($path in $unmerged) {
                    if ($androidConfigPaths -notcontains $path) {
                        throw "Found unresolved conflicts outside Android config files: $path"
                    }
                }

                Write-Host "[1/4] Unmerged Android config files detected. Resetting merge state before pull..."
                git reset --merge
            }

            Write-Host "[1/4] Discarding local changes in target Android config files before pull..."
            git restore --staged --worktree -- $androidConfigPaths
        }

        foreach ($path in $androidConfigPaths) {
            $pathDirty = git status --porcelain -- $path
            if ($pathDirty) {
                $targetDirtyPaths += $path
            }
        }

        if ($targetDirtyPaths.Count -gt 0 -and -not $ResetAndroidClientConfigToRemote) {
            Write-Host "[1/4] Target Android config files are dirty. Backing them up and cleaning working tree for pull..."
            $targetBackupDir = Join-Path ([System.IO.Path]::GetTempPath()) ("git-safe-pull-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
            New-Item -Path $targetBackupDir -ItemType Directory | Out-Null

            foreach ($path in $targetDirtyPaths) {
                $sourcePath = Join-Path (Get-Location) $path
                if (Test-Path $sourcePath) {
                    $backupPath = Join-Path $targetBackupDir $path
                    $backupParent = Split-Path -Path $backupPath -Parent
                    New-Item -Path $backupParent -ItemType Directory -Force | Out-Null
                    Copy-Item -Path $sourcePath -Destination $backupPath -Force
                }
            }

            git restore --staged --worktree -- $targetDirtyPaths
            $targetBackupCreated = $true
        }
        elseif ($ResetAndroidClientConfigToRemote) {
            Write-Host "[1/4] Target Android config files were reset to local HEAD (remote version will be applied by pull)."
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

    if ($OnlyAndroidClientConfig -and $targetBackupCreated) {
        Write-Host "[3/4] Restoring local Android config files from backup (without stash pop merge)..."
        foreach ($path in $targetDirtyPaths) {
            $backupPath = Join-Path $targetBackupDir $path
            $destPath = Join-Path (Get-Location) $path
            if (Test-Path $backupPath) {
                $destParent = Split-Path -Path $destPath -Parent
                New-Item -Path $destParent -ItemType Directory -Force | Out-Null
                Copy-Item -Path $backupPath -Destination $destPath -Force
            }
        }
    }
    elseif ($stashCreated -and -not $KeepStash) {
        Write-Host "[3/4] Restoring stashed changes..."
        git stash pop
    }
    elseif ($stashCreated -and $KeepStash) {
        Write-Host "[3/4] Stash kept as requested (-KeepStash): $stashName"
    }
    else {
        Write-Host "[3/4] No stash/backup to restore."
    }

    Write-Host "[4/4] Done."
}
catch {
    Write-Host "Error: $($_.Exception.Message)"
    if ($stashCreated) {
        Write-Host "A temporary stash may still exist. Check with: git stash list"
    }
    if ($targetBackupCreated) {
        Write-Host "Temporary backup folder: $targetBackupDir"
    }
    throw
}
finally {
    if ($targetBackupCreated -and $targetBackupDir -and (Test-Path $targetBackupDir)) {
        Remove-Item -Path $targetBackupDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
