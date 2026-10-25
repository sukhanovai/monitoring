# ComDone — разработка и выпуск релизов

Server Monitoring System v9.0.0

Документ для разработчика. Пользовательская установка описана в
[deployment.md](deployment.md).

## Ветки и каналы

| Ветка | Назначение | Сервер | Android-канал | Релиз GitHub |
|---|---|---|---|---|
| `develop` | ежедневная разработка | сервер разработчика | **Бета** | prerelease `v<версия>-beta`, `ComDone-<версия>-beta.apk` |
| `main` | стабильная версия для пользователей | серверы пользователей | **Стабильная** | релиз `v<версия>`, `ComDone-<версия>.apk` + `ComDone.apk` |

- Вся работа ведётся в `develop`. В `main` код попадает только через PR
  `develop → main` при выпуске стабильной версии.
- Сервер разработчика работает на `develop`. В Android-приложении канал
  выбирается в **Настройки → Обновление**. Канал влияет только на то,
  какой APK предлагать, а не на то, с каким сервером работать.
- Внутренние идентификаторы каналов остались `develop` и `main`: они
  сохранены в установленных приложениях. Пользователь видит названия
  «Бета» и «Стабильная».

Текущая бета-сборка:
<!-- ANDROID_PRERELEASE_APK_LINK_START -->https://github.com/sukhanovai/monitoring/releases/download/v9.0.0-beta/ComDone-9.0.0-beta.apk<!-- ANDROID_PRERELEASE_APK_LINK_END -->

## Совместимость: бета-приложение ↔ стабильный сервер

Любая сборка приложения из `develop` обязана работать с сервером из `main`.
Правило и механизм описаны в
[contracts/api_compatibility.md](contracts/api_compatibility.md). Коротко:

- API меняется только аддитивно: поля и эндпоинты не удаляются и не
  переименовываются;
- новый эндпоинт получает метку в `core/api_capabilities.py`
  (`API_CAPABILITIES`), а в приложении — запись в
  `ServerCapabilities.ENDPOINT_CAPABILITIES`. UI проверяет
  `ServerCapabilities.supports(state.serverCapabilities, "<метка>")` и
  скрывает функцию, если сервер её не объявил;
- тест `tests/test_api_compatibility_contract.py` (запускается в CI)
  ловит эндпоинт без метки и удалённый эндпоинт из baseline.

## Версия

Канонический источник — `config/settings.py` (`APP_VERSION`). Сверка и
обновление во всех файлах:

```sh
python scripts/bump_version.py --check
python scripts/bump_version.py 9.0.1
```

Вручную: `ANDROID_VERSION_CODE` в `android-client/gradle.properties`
(+1 на каждую публикуемую сборку) и верхняя запись `CHANGELOG.md`.

Номер версии APK (`versionName`) — строго `X.Y.Z`: приложение сравнивает
версии по трём числам. Пометка `-beta` есть только в имени файла и теге.

## Ключ подписи Android — критично

Обновление поверх установленного приложения возможно, только если новый APK
подписан **тем же ключом**. Все выпущенные сборки подписаны debug-ключом ПК
разработчика:

- Windows: `%USERPROFILE%\.android\debug.keystore`
- пароль хранилища `android`, alias `androiddebugkey`, пароль ключа `android`

**Сделайте резервную копию этого файла** (менеджер паролей и/или личное
облако, не в репозиторий). Если ключ потеряется, ни одно приложение у
пользователей не обновится поверх, понадобится переустановка.

Чтобы сборка не зависела от содержимого `.android`, укажите ключ явно в
`~/.gradle/gradle.properties` или `android-client/local.properties` (оба вне
git):

```properties
COMDONE_KEYSTORE_FILE=C:/keys/comdone.keystore
COMDONE_KEYSTORE_PASSWORD=android
COMDONE_KEY_ALIAS=androiddebugkey
COMDONE_KEY_PASSWORD=android
```

Без этих свойств release подписывается стандартным `debug.keystore`.

Идентификатор пакета `ru.monitoring.mobile.compactops` (бывший flavor
`compactOps`) менять нельзя по той же причине.

## Сборка и публикация APK

Из терминала Android Studio (PowerShell). Нужен `gh` (`gh auth login`)
или токен в `GH_TOKEN` / `GITHUB_TOKEN` / `$HOME/.monitoring/github_token`.

```powershell
# Бета — из develop
git checkout develop; git pull
./scripts/publish_android.ps1                    # = -Channel beta

# Стабильная — из main, после слияния develop → main
git checkout main; git pull
./scripts/publish_android.ps1 -Channel stable
```

Скрипт собирает `assembleRelease`, проверяет, что версия файла совпадает с
`APP_VERSION`, создаёт или обновляет релиз и загружает APK. Полезные флаги:
`-BuildType debug`, `-SkipBuild`, `-AutoStashDirty`.

Локальная сборка и запуск на устройстве после `git pull`:

```powershell
./scripts/android_post_pull_build_run.ps1        # sync + clean + assembleDebug + install + run
```

Помощники git для Windows при конфликтах после `git pull`:
`scripts/git_safe_pull.ps1` и `scripts/android_studio_pull_recover.ps1`
(подробно — [dev/android_development.md](dev/android_development.md)).

## Выпуск стабильной версии

1. В `develop`:
   - `python scripts/bump_version.py X.Y.Z`;
   - `ANDROID_VERSION_CODE` +1;
   - запись в `CHANGELOG.md`;
   - коммит и пуш, CI зелёный.
2. Опубликовать бету: `./scripts/publish_android.ps1`. Обновить на своём
   телефоне поверх предыдущей версии и проверить, что токен и настройки
   на месте.
3. Проверить бету против стабильного сервера: запустить код `main` локально
   (`git worktree add ../comdone-main main`, затем
   `python main.py` с отдельным `MONITORING_BASE_DIR`) и подключить
   приложение.
4. PR `develop → main`, слияние.
5. Из `main`: `./scripts/publish_android.ps1 -Channel stable`. Скрипт
   создаст тег `vX.Y.Z` и релиз с `ComDone-X.Y.Z.apk` и `ComDone.apk`.

## CI

`.github/workflows/ci.yml` запускается на push в `main` и `develop` и на
каждый PR:

- ruff, compileall, mypy (строгий набор), pytest (включая контракт API);
- `android-build`: `assembleRelease` с временным ключом CI. APK доступен как
  артефакт сборки на 7 дней. Для установки у пользователей он **не
  подходит**: подпись другая.

## Рабочие заметки

Исторические планы, исследования и черновики лежат в [dev/](dev/), в том
числе подробная инструкция по Android Studio
([dev/android_development.md](dev/android_development.md)).
