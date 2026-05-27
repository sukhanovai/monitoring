# Project memory

## Версия проекта — проверять перед каждым PR

Перед созданием любого PR сверять номер версии проекта во всех файлах, где
он упоминается, и приводить к актуальному значению.

Канонический источник версии — `config/settings.py`:

- `APP_VERSION` — версия серверного бэкенда.
- `ANDROID_LATEST_VERSION` — какую новейшую APK сервер анонсирует
  мобильному клиенту через `/v1/mobile/version`.
- `ANDROID_MIN_SUPPORTED_VERSION` — нижний порог поддержки, **не** равен
  текущей версии, менять только осознанно.

Места, которые должны совпадать с текущей версией:

- `config/settings.py` (`APP_VERSION`, `ANDROID_LATEST_VERSION`)
- заголовки `main.py`, файлов `modules/*`, `extensions/*`, `docs/*`
  (`Server Monitoring System v<версия>` / `Версия: <версия>`)
- `android-client/gradle.properties` (`ANDROID_VERSION_NAME`)
- ссылки на prerelease APK в `README.md` и `docs/android_mobile_app.md`
- верхняя запись в `CHANGELOG.md`

Быстрая проверка через `scripts/bump_version.py`:

```sh
python scripts/bump_version.py --check       # сверка (выход 1 при рассинхроне)
python scripts/bump_version.py --print       # вывести текущую APP_VERSION
python scripts/bump_version.py 8.62.62       # обновить везде до новой версии
```

`--check` запускается pre-commit hook'ом автоматически на каждый коммит,
который трогает версионные файлы. Скрипт **не инкрементирует** ни
`ANDROID_VERSION_CODE`, ни запись в `CHANGELOG.md` — это надо делать
вручную (`ANDROID_VERSION_CODE` имеет независимую семантику, `CHANGELOG`
содержит описание изменений автора).

Старая ручная сверка через grep (на случай если скрипт сломан):

```sh
grep -rnoE "8\.6[0-9]\.[0-9]+" \
  --include="*.py" --include="*.kt" --include="*.kts" --include="*.properties" \
  --include="*.md" --include="*.json" --include="*.gradle" --include="*.txt" \
  . --exclude-dir=.git \
  | grep -vE "CHANGELOG.md" \
  | grep -vE ":<текущая_версия>$|:<ANDROID_MIN_SUPPORTED_VERSION>$"
```
