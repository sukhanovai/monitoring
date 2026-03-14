param(
    [string]$BaseBranch = "develop",
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Не найдена команда '$Name'. Установи её и повтори запуск."
    }
}

$conflictTargets = @(
    "CHANGELOG.md",
    "android-client/app/build.gradle.kts",
    "android-client/app/src/main/java/ru/monitoring/mobile/ui/MainViewModel.kt",
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
    "core/monitor_core.py"
)

Require-Command git

$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host "Текущая ветка: $currentBranch"
Write-Host "Подтягиваю $Remote/$BaseBranch..."
git fetch $Remote $BaseBranch

Write-Host "Вливаю $Remote/$BaseBranch в $currentBranch..."
$mergeSucceeded = $true
git merge "$Remote/$BaseBranch"
if ($LASTEXITCODE -ne 0) {
    $mergeSucceeded = $false
}

if ($mergeSucceeded) {
    Write-Host "Конфликтов нет, merge завершен."
    exit 0
}

Write-Host "Обнаружены конфликты, пробую авторазрешение (оставляю текущую ветку для целевых файлов)..."
foreach ($path in $conflictTargets) {
    git checkout --ours -- "$path" 2>$null
    if ($LASTEXITCODE -eq 0) {
        git add "$path"
    }
}

$remaining = git diff --name-only --diff-filter=U
if ($remaining) {
    Write-Host "Остались неразрешенные конфликты:"
    $remaining | ForEach-Object { Write-Host " - $_" }
    throw "Авторазрешение не завершено. Дорешай оставшиеся файлы вручную."
}

Write-Host "Все конфликты закрыты. Проверь diff и выполни commit вручную."
