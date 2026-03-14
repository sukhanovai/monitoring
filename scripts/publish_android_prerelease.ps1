param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")),
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Не найдена команда '$Name'. Установи её и попробуй снова."
    }
}

Write-Host "[1/7] Проверка зависимостей..."
Require-Command git
Require-Command gh

Push-Location $RepoRoot
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($branch -ne "develop") {
        throw "Скрипт должен запускаться только из ветки 'develop'. Сейчас: '$branch'."
    }

    Write-Host "[2/7] Получение версии проекта из config/settings.py..."
    $settingsPath = Join-Path $RepoRoot "config/settings.py"
    if (-not (Test-Path $settingsPath)) {
        throw "Не найден файл $settingsPath"
    }

    $settingsContent = Get-Content -Path $settingsPath -Raw
    $versionMatch = [regex]::Match($settingsContent, 'APP_VERSION\s*=\s*"(?<version>\d+\.\d+\.\d+)"')
    if (-not $versionMatch.Success) {
        throw "Не удалось определить APP_VERSION в config/settings.py"
    }

    $projectVersion = $versionMatch.Groups["version"].Value
    $releaseTag = "v$projectVersion-develop"
    $releaseTitle = "Android develop prerelease $projectVersion"

    $androidDir = Join-Path $RepoRoot "android-client"
    if (-not (Test-Path $androidDir)) {
        throw "Не найден каталог android-client"
    }

    if (-not $SkipBuild) {
        Write-Host "[3/7] Сборка release APK..."
        Push-Location $androidDir
        try {
            if (Test-Path (Join-Path $androidDir "gradlew.bat")) {
                & .\gradlew.bat :app:assembleRelease
            }
            elseif (Test-Path (Join-Path $androidDir "gradlew")) {
                & ./gradlew :app:assembleRelease
            }
            else {
                throw "Не найден gradlew/gradlew.bat в android-client"
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host "[3/7] Сборка пропущена флагом -SkipBuild"
    }

    Write-Host "[4/7] Поиск готового APK..."
    $apkSource = Join-Path $androidDir "app/build/outputs/apk/release/app-release.apk"
    if (-not (Test-Path $apkSource)) {
        throw "APK не найден: $apkSource"
    }

    $artifactDir = Join-Path $RepoRoot "artifacts"
    New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null

    $apkName = "monitoring-android-$projectVersion-develop.apk"
    $apkTarget = Join-Path $artifactDir $apkName
    Copy-Item -Path $apkSource -Destination $apkTarget -Force

    Write-Host "[5/7] Проверка релиза $releaseTag в GitHub..."
    $releaseExists = $true
    gh release view $releaseTag | Out-Null 2>$null
    if ($LASTEXITCODE -ne 0) {
        $releaseExists = $false
    }

    $notes = @"
EN: Android prerelease for develop branch.
EN: Built from branch develop, version $projectVersion.
EN: Stable release in main remains unchanged.

RU: Android пререлиз для ветки develop.
RU: Собрано из ветки develop, версия $projectVersion.
RU: Стабильный релиз в main не изменяется.
"@

    if (-not $releaseExists) {
        Write-Host "[6/7] Создание нового prerelease $releaseTag..."
        gh release create $releaseTag $apkTarget --title $releaseTitle --target develop --prerelease --notes $notes
    }
    else {
        Write-Host "[6/7] Обновление существующего prerelease $releaseTag..."
        gh release edit $releaseTag --title $releaseTitle --target develop --prerelease --notes $notes
        gh release upload $releaseTag $apkTarget --clobber
    }

    Write-Host "[7/7] Готово. Пререлиз опубликован: $releaseTag"
    Write-Host "APK: $apkTarget"
}
finally {
    Pop-Location
}
