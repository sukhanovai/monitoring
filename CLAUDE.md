# Project memory

## Версия проекта — проверять перед каждым PR

Перед созданием любого PR сверять номер версии проекта во всех файлах, где
он упоминается, и приводить к актуальному значению.

Канонический источник версии — `config/settings.py`:

- `APP_VERSION` — версия серверного бэкенда.
- `ANDROID_LATEST_VERSION` — запасная версия APK, которую сервер анонсирует
  через `/v1/mobile/version`, если GitHub Releases недоступен (обычно версии
  каналов берутся из релизов — `core/android_release_channels.py`).
- `ANDROID_MIN_SUPPORTED_VERSION` — нижний порог поддержки, **не** равен
  текущей версии, менять только осознанно.

Места, которые должны совпадать с текущей версией:

- `config/settings.py` (`APP_VERSION`, `ANDROID_LATEST_VERSION`)
- заголовки `main.py`, файлов `modules/*`, `extensions/*`, `docs/*`
  (`Server Monitoring System v<версия>` / `Версия: <версия>`)
- `android-client/gradle.properties` (`ANDROID_VERSION_NAME`)
- ссылка на бета-APK в `docs/development.md`
- верхняя запись в `CHANGELOG.md`

Быстрая проверка через `scripts/bump_version.py`:

```sh
python scripts/bump_version.py --check       # сверка (выход 1 при рассинхроне)
python scripts/bump_version.py --print       # вывести текущую APP_VERSION
python scripts/bump_version.py 9.0.1         # обновить везде до новой версии
```

`--check` запускается pre-commit hook'ом автоматически на каждый коммит,
который трогает версионные файлы. Скрипт **не инкрементирует** ни
`ANDROID_VERSION_CODE`, ни запись в `CHANGELOG.md` — это надо делать
вручную (`ANDROID_VERSION_CODE` имеет независимую семантику, `CHANGELOG`
содержит описание изменений автора).

Старая ручная сверка через grep (на случай если скрипт сломан):

```sh
grep -rnoE "9\.[0-9]+\.[0-9]+" \
  --include="*.py" --include="*.kt" --include="*.kts" --include="*.properties" \
  --include="*.md" --include="*.json" --include="*.gradle" --include="*.txt" \
  . --exclude-dir=.git \
  | grep -vE "CHANGELOG.md" \
  | grep -vE ":<текущая_версия>$|:<ANDROID_MIN_SUPPORTED_VERSION>$"
```

## Ветки и каналы

- Разработка — только в `develop`. `main` = стабильная версия для
  пользователей, обновляется PR `develop → main` при выпуске.
- Android: канал «Бета» = prerelease `v<версия>-beta`
  (`ComDone-<версия>-beta.apk`), «Стабильная» = релиз `v<версия>`
  (`ComDone-<версия>.apk` + `ComDone.apk`). Публикация —
  `scripts/publish_android.ps1 [-Channel stable]`, подробности —
  `docs/development.md`.
- `applicationId` `ru.monitoring.mobile.compactops` и ключ подписи не
  менять: иначе у пользователей не будет обновления поверх.
- Идентификаторы каналов `develop`/`main` в `ANDROID_UPDATE_BRANCHES` не
  переименовывать — они сохранены в установленных приложениях.

## Совместимость API — бета-клиент обязан работать со стабильным сервером

- API меняется только аддитивно: эндпоинты и поля JSON не удаляются, не
  переименовываются, не меняют смысл.
- Новый эндпоинт после baseline 9.0.0 → метка в
  `core/api_capabilities.py` (`API_CAPABILITIES`) и запись в
  `android-client/.../api/ServerCapabilities.kt`
  (`ENDPOINT_CAPABILITIES`); UI проверяет `ServerCapabilities.supports(...)`.
- Проверяется `tests/test_api_compatibility_contract.py`; правило —
  `docs/contracts/api_compatibility.md`.

## Документация

- `docs/deployment.md` — единственная пользовательская инструкция по
  установке/обновлению; при изменении установки, env-переменных,
  зависимостей или systemd — обновлять её.
- `docs/dev/` — рабочие заметки и планы разработки (не для пользователей).
