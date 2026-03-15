param(
    [string]$Remote = "origin",
    [string]$BaseBranch = "develop",
    [switch]$NoCommit
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Command '$Name' was not found. Install it and retry."
    }
}

Require-Command git

$volatilePaths = @(
    "CHANGELOG.md",
    "android-client/app/src/main/java/ru/monitoring/mobile/ui/MainViewModel.kt",
    "android-client/gradle.properties",
    "bot/__init__.py",
    "bot/handlers/__init__.py",
    "bot/handlers/base.py",
    "bot/handlers/callbacks.py",
    "bot/handlers/commands.py",
    "bot/handlers/extensions.py",
    "bot/handlers/settings_handlers.py",
    "bot/menu/__init__.py",
    "bot/menu/builder.py",
    "bot/menu/handlers.py",
    "config/__init__.py",
    "config/db_settings.py",
    "config/db_settings_app.py",
    "config/debug.py",
    "config/debug_app.py",
    "config/settings.py",
    "config/settings_app.py",
    "core/__init__.py",
    "core/checker.py",
    "core/config_manager.py",
    "core/monitor.py",
    "core/monitor_core.py",
    "core/task_router.py",
    "docs/api_202020_project.md",
    "extensions/__init__.py",
    "extensions/backup_monitor/backup_handlers.py",
    "extensions/backup_monitor/backup_utils.py",
    "extensions/backup_monitor/bot_handler.py",
    "extensions/backup_monitor/db_settings_backup_monitor.py",
    "extensions/backup_monitor/settings_backup_monitor.py",
    "extensions/base.py",
    "extensions/extension_manager.py",
    "extensions/server_checks.py",
    "extensions/server_checks/__init__.py",
    "extensions/supplier_stock_files.py",
    "extensions/utils.py",
    "extensions/web_interface.py",
    "extensions/web_interface/__init__.py",
    "lib/__init__.py",
    "lib/alerts.py",
    "lib/common.py",
    "lib/helpers.py",
    "lib/logging.py",
    "lib/monitoring_utils.py",
    "lib/network.py",
    "lib/utils.py",
    "main.py",
    "modules/__init__.py",
    "modules/availability.py",
    "modules/debug.py",
    "modules/improved_mail_monitor.py",
    "modules/mail_monitor.py",
    "modules/morning_report.py",
    "modules/resources.py",
    "modules/targeted_checks.py",
    "modules/targeted_resources.py",
    "scripts/generate_mobile_default_token.py"
)

Write-Host "[1/5] Fetching $Remote/$BaseBranch..."
git fetch $Remote $BaseBranch
if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch $Remote/$BaseBranch"
}

Write-Host "[2/5] Merging $Remote/$BaseBranch into current branch..."
$mergeFailed = $false
git merge "$Remote/$BaseBranch"
if ($LASTEXITCODE -ne 0) {
    $mergeFailed = $true
}

if ($mergeFailed) {
    Write-Host "[3/5] Merge has conflicts. Resolving volatile version files by taking base branch version..."

    foreach ($path in $volatilePaths) {
        git checkout --theirs -- $path 2>$null
        if ($LASTEXITCODE -eq 0) {
            git add -- $path
        }
    }

    $unmerged = git diff --name-only --diff-filter=U
    if ($unmerged) {
        Write-Host "[4/5] Unmerged files still present:"
        $unmerged | ForEach-Object { Write-Host " - $_" }
        throw "Not all conflicts were resolved automatically. Resolve remaining files manually and continue merge."
    }
}
else {
    Write-Host "[3/5] Merge completed without conflicts."
}

if (-not $NoCommit) {
    Write-Host "[5/5] Creating merge commit..."
    git commit --no-edit
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create merge commit"
    }
}
else {
    Write-Host "[5/5] -NoCommit set: merge resolved and staged, commit skipped."
}

Write-Host "Done."
