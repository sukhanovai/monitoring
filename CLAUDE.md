# Project memory

## Версия проекта — проверять перед каждым PR

Перед созданием любого PR сверять номер версии проекта во всех файлах, где
он упоминается, и приводить к актуальному значению.

Канонический источник версии — `config/settings.py`:

- `APP_VERSION`
- `ANDROID_APP_VERSION`
- `ANDROID_LATEST_VERSION`
- `ANDROID_MIN_SUPPORTED_VERSION` — нижний порог поддержки, **не** равен
  текущей версии, менять только осознанно.

Места, которые должны совпадать с текущей версией:

- `config/settings.py` (`APP_VERSION`, `ANDROID_APP_VERSION`,
  `ANDROID_LATEST_VERSION`)
- заголовки `main.py`, файлов `modules/*`, `extensions/*`, `docs/*`
  (`Server Monitoring System v<версия>` / `Версия: <версия>`)
- `android-client/gradle.properties` (`ANDROID_VERSION_NAME`)
- ссылки на prerelease APK в `README.md` и `docs/android_mobile_app.md`
- верхняя запись в `CHANGELOG.md`

Быстрая проверка отсутствия рассинхрона (должно быть пусто):

```sh
grep -rnoE "8\.6[0-9]\.[0-9]+" \
  --include="*.py" --include="*.kts" --include="*.properties" \
  --include="*.md" --include="*.json" --include="*.gradle" --include="*.txt" \
  . --exclude-dir=.git \
  | grep -vE "CHANGELOG.md" \
  | grep -vE ":<текущая_версия>$|:<ANDROID_MIN_SUPPORTED_VERSION>$"
```
