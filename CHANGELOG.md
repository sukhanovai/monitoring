## [8.55.36] - 2026-04-19

### Fixed / Исправлено
- EN: Restored the settings gear for the Android `zfs место` tile in Ops chips: tapping the gear now opens ZFS-pool host settings via `zfsp_hosts_list`, while regular tile tap keeps opening free-space data.
- RU: Возвращена шестерёнка настроек для Android-плашки `zfs место` в Ops-чипах: тап по шестерёнке снова открывает настройки хостов ZFS-пулов через `zfsp_hosts_list`, а обычный тап по плашке по-прежнему открывает данные по свободному месту.
- EN: SemVer patch bump to `8.55.36`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.36` and `ANDROID_VERSION_CODE=562`; prerelease links aligned to `v8.55.36-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.36`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.36` и `ANDROID_VERSION_CODE=562`; prerelease-ссылки выровнены на `v8.55.36-develop`.

## [8.55.35] - 2026-04-19

### Changed / Изменено
- EN: Android `zfs место` card flow was simplified: removed the gear button from the `💽 Free space of ZFS pools` dialog header; regular tap on the tile opens pool free-space data, long tap opens host settings (`zfsp_hosts_list`).
- RU: Упрощён сценарий карточки Android `zfs место`: убрана шестерёнка из заголовка диалога `💽 Свободное место ZFS пулов`; обычный тап по плашке открывает данные по свободному месту, долгий тап открывает настройки хостов (`zfsp_hosts_list`).
- EN: ZFS-pool host settings UI now uses host cards; long tap on a host card opens an actions window (edit, enable/disable, delete).
- RU: UI настроек хостов ZFS-пулов переведён на карточки хостов; долгий тап по карточке открывает окно действий (редактирование, вкл/выкл, удаление).
- EN: SemVer patch bump to `8.55.35`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.35` and `ANDROID_VERSION_CODE=561`; prerelease links aligned to `v8.55.35-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.35`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.35` и `ANDROID_VERSION_CODE=561`; prerelease-ссылки выровнены на `v8.55.35-develop`.

## [8.55.34] - 2026-04-18

### Fixed / Исправлено
- EN: Fixed Android `zfs место` tile behavior: tapping the gear on the tile now opens ZFS-pool free-space host settings by running `zfsp_hosts_list` (Telegram-bot parity: `Free space of ZFS pools` → `Host settings`).
- RU: Исправлено поведение Android-плашки `zfs место`: тап по шестерёнке на плашке теперь открывает настройки хостов свободного места ZFS-пулов через `zfsp_hosts_list` (паритет с Telegram-ботом: `Свободное место ZFS пулов` → `Настройка хостов`).
- EN: SemVer patch bump to `8.55.34`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.34` and `ANDROID_VERSION_CODE=560`; prerelease links aligned to `v8.55.34-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.34`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.34` и `ANDROID_VERSION_CODE=560`; prerelease-ссылки выровнены на `v8.55.34-develop`.

## [8.55.28] - 2026-04-18

### Changed / Изменено
- EN: In Android app `zfs место` (`💽 Free space of ZFS pools`), free-space percentages now use stronger proximity-based critical coloring: color transitions are smooth from critical to normal and each `% free` value is rendered as a highlighted badge to improve readability near thresholds.
- RU: В Android-приложении в `zfs место` (`💽 Свободное место ZFS пулов`) усилено выделение процентов свободного места по мере приближения к критическим порогам: цвет теперь плавно меняется от критичного к нормальному, а каждое значение `% free` показывается в выделенном бейдже для лучшей читаемости у порогов.
- EN: SemVer patch bump to `8.55.28`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.28` and `ANDROID_VERSION_CODE=554`; prerelease links aligned to `v8.55.28-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.28`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.28` и `ANDROID_VERSION_CODE=554`; prerelease-ссылки выровнены на `v8.55.28-develop`.

## [8.55.27] - 2026-04-18

### Changed / Изменено
- EN: Fixed Android Compose compile error in `MainActivity`: helper `zfsPoolCardBackgroundColor` is now marked `@Composable`, so `MaterialTheme.colorScheme` is used from a valid composable context.
- RU: Исправлена ошибка компиляции Android Compose в `MainActivity`: хелпер `zfsPoolCardBackgroundColor` помечен `@Composable`, поэтому `MaterialTheme.colorScheme` вызывается из корректного composable-контекста.
- EN: Android app UI updated: in `zfs место`, pool results are now rendered as a compact table (host / pool / free %) with threshold-aware coloring and tap support on table rows.
- RU: Обновлён UI Android-приложения: в `zfs место` результаты по пулам теперь отображаются компактной таблицей (хост / пул / свободно %) с пороговой цветовой индикацией и поддержкой тапа по строкам.
- EN: SemVer patch bump to `8.55.27`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.27` and `ANDROID_VERSION_CODE=553`; prerelease links aligned to `v8.55.27-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.27`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.27` и `ANDROID_VERSION_CODE=553`; prerelease-ссылки выровнены на `v8.55.27-develop`.

## [8.55.24] - 2026-04-18

### Changed / Изменено
- EN: SemVer patch bump to `8.55.24`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.24` and `ANDROID_VERSION_CODE=550`; prerelease links aligned to `v8.55.24-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.24`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.24` и `ANDROID_VERSION_CODE=550`; prerelease-ссылки выровнены на `v8.55.24-develop`.

## [8.55.23] - 2026-04-18

### Changed / Изменено
- EN: SemVer patch bump to `8.55.23`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.23` and `ANDROID_VERSION_CODE=549`; prerelease links aligned to `v8.55.23-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.23`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.23` и `ANDROID_VERSION_CODE=549`; prerelease-ссылки выровнены на `v8.55.23-develop`.

## [8.55.22] - 2026-04-18

### Fixed / Исправлено
- EN: Fixed Android `zfs место` gear action in `💽 Free space of ZFS pools`: settings now run via extension-settings flow (`onExtensionsSettingsAction`) for `zfsp_hosts_list`, so the dialog opens `⚙️ Hosts monitoring free space of ZFS` instead of jumping to `🧊 ZFS statuses`.
- RU: Исправлено действие шестерёнки в Android-плашке `zfs место` (`💽 Свободное место ZFS пулов`): настройки теперь запускаются через поток настроек расширений (`onExtensionsSettingsAction`) для `zfsp_hosts_list`, поэтому открывается `⚙️ Хосты мониторинга свободного места ZFS`, а не `🧊 Статусы ZFS`.
- EN: SemVer patch bump to `8.55.22`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.22` and `ANDROID_VERSION_CODE=548`; prerelease links aligned to `v8.55.22-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.22`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.22` и `ANDROID_VERSION_CODE=548`; prerelease-ссылки выровнены на `v8.55.22-develop`.

## [8.55.21] - 2026-04-18

### Fixed / Исправлено
- EN: Fixed Android `zfs место` tile settings behavior: the gear button now opens ZFS pool host settings (`zfsp_hosts_list`) when the action is available, with automatic fallback to refresh (`zfs_pool_free_space_menu`) if settings are not yet loaded.
- RU: Исправлено поведение шестерёнки в Android-плашке `zfs место`: кнопка настроек теперь открывает настройки хостов ZFS-пулов (`zfsp_hosts_list`), а если действие ещё не загружено — автоматически делает обновление (`zfs_pool_free_space_menu`).
- EN: SemVer patch bump to `8.55.21`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.21` and `ANDROID_VERSION_CODE=547`; prerelease links aligned to `v8.55.21-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.21`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.21` и `ANDROID_VERSION_CODE=547`; prerelease-ссылки выровнены на `v8.55.21-develop`.

## [8.55.18] - 2026-04-18

### Changed / Изменено
- EN: Fixed Android ZFS card separation to match Telegram behavior: tiles are now explicitly split into `zfs` and `Свободное место ZFS пулов`, and pool dialog actions no longer jump into generic ZFS host settings.
- RU: Исправлено разделение Android-плашек ZFS до поведения как в Telegram: карточки теперь явно разведены на `zfs` и `Свободное место ZFS пулов`, а действия в диалоге пулов больше не уводят в общие настройки ZFS-хостов.
- EN: SemVer patch bump to `8.55.18`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.18` and `ANDROID_VERSION_CODE=544`; prerelease links aligned to `v8.55.18-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.18`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.18` и `ANDROID_VERSION_CODE=544`; prerelease-ссылки выровнены на `v8.55.18-develop`.

## [8.55.16] - 2026-04-18

### Changed / Изменено
- EN: Fixed Android `ZFS pools` gear action: tapping settings now routes through extension-settings API (`settings_zfs_list`) and opens the host settings dialog, instead of sending `zfsp_hosts_list` to `/v1/control/actions` (which caused `400`).
- RU: Исправлено действие шестерёнки в Android `ZFS-пулах`: тап по настройкам теперь идёт через API настроек расширений (`settings_zfs_list`) и открывает диалог настроек хостов, вместо отправки `zfsp_hosts_list` в `/v1/control/actions` (из-за этого прилетал `400`).
- EN: SemVer patch bump to `8.55.16`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.16` and `ANDROID_VERSION_CODE=542`; prerelease links aligned to `v8.55.16-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.16`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.16` и `ANDROID_VERSION_CODE=542`; prerelease-ссылки выровнены на `v8.55.16-develop`.

## [8.55.14] - 2026-04-18

### Changed / Изменено
- EN: Fixed Android build failure in `MainViewModel`: added a dedicated menu-options resolver overload for `ExtensionsActionResponse`, so `settings_zfs_list` extension responses are handled with the correct type and `compileCompactOpsDebugKotlin` no longer fails on type mismatch.
- RU: Исправлен падёж Android-сборки в `MainViewModel`: добавлен отдельный overload резолвера menu-options для `ExtensionsActionResponse`, поэтому ответы extension-действия `settings_zfs_list` обрабатываются корректным типом и `compileCompactOpsDebugKotlin` больше не падает из-за type mismatch.
- EN: SemVer patch bump to `8.55.14`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.14` and `ANDROID_VERSION_CODE=540`; prerelease links aligned to `v8.55.14-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.14`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.14` и `ANDROID_VERSION_CODE=540`; prerelease-ссылки выровнены на `v8.55.14-develop`.

## [8.55.13] - 2026-04-18

### Changed / Изменено
- EN: Fixed Android `ZFS pools` gear action: it now opens host settings from the same flow as Telegram (`Main menu` → `ZFS pool free space` → `host settings`) via `settings_zfs_list`.
- RU: Исправлено действие шестерёнки в Android `ZFS-пулах`: теперь открываются настройки хостов из того же контура, что и в Telegram (`Главное меню` → `Свободное место ZFS пулов` → `настройки хостов`) через `settings_zfs_list`.
- EN: Updated Android `ZFS pools` dialog data source to keep rendering extension options for both `zfs_pool_free_space_menu` and nested `zfsp_*` actions, so host-settings screens are shown in-app correctly.
- RU: Обновлён источник данных в Android-диалоге `ZFS-пулы`: теперь экран продолжает рендерить опции расширения и для `zfs_pool_free_space_menu`, и для вложенных `zfsp_*` действий, поэтому настройки хостов корректно отображаются в приложении.
- EN: SemVer patch bump to `8.55.13`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.13` and `ANDROID_VERSION_CODE=539`; prerelease links aligned to `v8.55.13-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.13`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.13` и `ANDROID_VERSION_CODE=539`; prerelease-ссылки выровнены на `v8.55.13-develop`.

## [8.55.10] - 2026-04-18

### Changed / Изменено
- EN: Android `ZFS pools` free-space percentage highlight was intensified: `% free` values now use stronger contrast (bold + tinted background) and adaptive color by remaining free space level to make threshold approach obvious at a glance.
- RU: В Android `ZFS-пулах` усилено выделение процента свободного места: значения `% free` теперь показываются с более контрастным акцентом (жирный + подложка) и адаптивным цветом по уровню оставшегося свободного места, чтобы приближение к порогам читалось сразу.
- EN: Fixed Android compilation error in `zfsFreePercentBackgroundColor`: interpolation fraction is now explicitly converted to `Float`, restoring valid `Color` `lerp(...).copy(...)` resolution for Kotlin compiler.
- RU: Исправлена ошибка компиляции Android в `zfsFreePercentBackgroundColor`: доля интерполяции теперь явно приводится к `Float`, из-за чего Kotlin снова корректно резолвит `Color`-ветку `lerp(...).copy(...)`.
- EN: SemVer patch bump to `8.55.10`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.10` and `ANDROID_VERSION_CODE=536`; prerelease links aligned to `v8.55.10-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.10`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.10` и `ANDROID_VERSION_CODE=536`; prerelease-ссылки выровнены на `v8.55.10-develop`.

## [8.55.8] - 2026-04-18

### Changed / Изменено
- EN: Android `ZFS pools` dialog UI updated: removed inline `Refresh` and `Close` action buttons from the dialog content/actions and added a dedicated settings gear in the dialog header.
- RU: Обновлён UI Android-диалога `ZFS-пулы`: убраны встроенные кнопки `Обновить` и `Закрыть` из действий/контента диалога и добавлена отдельная шестерёнка настроек в заголовок.
- EN: Fixed ZFS pools summary calculation for pool responses that include explicit `Пулов: N` lines, so the summary no longer falls back to auxiliary menu-action counts (e.g., `0/2`) when there are more actual pools.
- RU: Исправлен расчёт сводки ZFS-пулов для ответов с явной строкой `Пулов: N`, поэтому сводка больше не скатывается к подсчёту служебных пунктов меню (например, `0/2`) при большем числе реальных пулов.
- EN: Enhanced visibility of `% free` values in ZFS pool entries: percent values are now highlighted with stronger emphasis and color-coded by free-space level (critical/warning/normal).
- RU: Улучшена видимость значений `% free` в строках ZFS-пулов: проценты теперь выделяются более ярко и окрашиваются по уровню свободного места (критично/предупреждение/норма).
- EN: In `Compact Ops`, added a circular sync arrow button to the left of the settings gear for quick manual synchronization.
- RU: В `Оперативном центре` добавлена кнопка круговой стрелки синхронизации слева от шестерёнки настроек для быстрого ручного обновления.
- EN: SemVer patch bump to `8.55.8`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.8` and `ANDROID_VERSION_CODE=534`; prerelease links aligned to `v8.55.8-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.8`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.8` и `ANDROID_VERSION_CODE=534`; prerelease-ссылки выровнены на `v8.55.8-develop`.

## [8.55.6] - 2026-04-18

### Changed / Изменено
- EN: Fixed Android `Compact Ops` ZFS status loader: `zfs` now follows only dedicated ZFS actions (`zfs_menu`, `settings_zfs*` for hosts/patterns) and explicitly ignores `settings_zfs_pool*`, so the `zfs` tile is no longer linked to ZFS pools actions.
- RU: Исправлен загрузчик статусов ZFS в Android `Оперативном центре`: `zfs` теперь следует только профильным действиям ZFS (`zfs_menu`, `settings_zfs*` для хостов/паттернов) и явно игнорирует `settings_zfs_pool*`, поэтому плашка `zfs` больше не связана с действиями ZFS-пулов.
- EN: SemVer patch bump to `8.55.6`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.6` and `ANDROID_VERSION_CODE=532`; prerelease links aligned to `v8.55.6-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.6`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.6` и `ANDROID_VERSION_CODE=532`; prerelease-ссылки выровнены на `v8.55.6-develop`.

## [8.55.6] - 2026-04-18

### Changed / Изменено
- EN: In Android `Compact Ops`, separated `zfs` and `zfs pools` actions: the ZFS status loader now ignores `zfs_pool_free_space` actions, so the `zfs` tile no longer opens or shows pool data by mistake.
- RU: В Android `Оперативный центр` разделены действия `zfs` и `zfs пулы`: загрузчик статусов ZFS теперь игнорирует `zfs_pool_free_space`-действия, поэтому плашка `zfs` больше не открывает и не показывает данные пулов по ошибке.
- EN: Normalized Android tile ids for `zfs`/`zfs pools` in `Compact Ops` and tightened click routing for `zfs pools` to id-based matching, so `zfs_pool_free_space_menu` opens from the dedicated tile consistently.
- RU: В `Оперативном центре` нормализованы id плашек `zfs`/`zfs пулы` и ужесточена маршрутизация клика `zfs пулы` по id, поэтому `zfs_pool_free_space_menu` стабильно открывается из своей отдельной плашки.
- EN: SemVer patch bump to `8.55.6`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.6` and `ANDROID_VERSION_CODE=531`; prerelease links aligned to `v8.55.6-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.6`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.6` и `ANDROID_VERSION_CODE=531`; prerelease-ссылки выровнены на `v8.55.6-develop`.
## [8.55.0] - 2026-04-18

### Changed / Изменено
- EN: Android `Compact Ops` now shows a dedicated extension tile for `💽 Free space of ZFS pools` even when backend returns `zfs_pool_free_space_monitor`, and the tile opens `zfs_pool_free_space_menu`.
- RU: В Android `Оперативный центр` добавлена отдельная плашка расширения `💽 Свободное место ZFS пулов`: теперь учитывается backend-id `zfs_pool_free_space_monitor`, а тап открывает `zfs_pool_free_space_menu`.
- EN: Added summary and problem-state calculation for `zfs_pool_free_space_menu` so the tile value/alert coloring reflects pool data, and extended status parsing to treat `🟢` as a healthy marker.
- RU: Добавлен расчёт сводки и аварийности для `zfs_pool_free_space_menu`, чтобы значение/подсветка плашки отражали состояние пулов; парсинг статусов расширен — `🟢` считается нормальным состоянием.
- EN: SemVer minor bump to `8.55.0`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.0` and `ANDROID_VERSION_CODE=526`; prerelease links aligned to `v8.55.0-develop`.
- RU: Выполнен SemVer minor-бамп до `8.55.0`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.0` и `ANDROID_VERSION_CODE=526`; prerelease-ссылки выровнены на `v8.55.0-develop`.

## [8.53.20] - 2026-04-17

### Changed / Изменено
- EN: In Android app settings → extensions, removed quick-action buttons for extension sections from the UI; left only the extension enable/disable controls and explanatory text.
- RU: В Android-приложении в настройках → расширения убраны кнопки быстрых переходов по разделам; оставлены только переключатели включения/выключения расширений и поясняющий текст.
- EN: SemVer patch bump to `8.53.20`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.20` and `ANDROID_VERSION_CODE=524`; prerelease links aligned to `v8.53.20-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.20`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.20` и `ANDROID_VERSION_CODE=524`; prerelease-ссылки выровнены на `v8.53.20-develop`.

## [8.53.17] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android `compileCompactOpsDebugKotlin` failure in `MainActivity`: added the missing closing brace for the main composable scope so `ExtensionsSection` is resolved correctly and Kotlin parser errors are eliminated.
- RU: Исправлен сбой Android `compileCompactOpsDebugKotlin` в `MainActivity`: добавлена недостающая закрывающая фигурная скобка основного composable-скоупа, из-за чего `ExtensionsSection` снова корректно резолвится и parser-ошибки Kotlin исчезают.
- EN: SemVer patch bump to `8.53.17`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.17` and `ANDROID_VERSION_CODE=521`; prerelease links aligned to `v8.53.17-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.17`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.17` и `ANDROID_VERSION_CODE=521`; prerelease-ссылки выровнены на `v8.53.17-develop`.

## [8.53.14] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android `compileCompactOpsDebugKotlin` failure in `MainActivity`: removed two extra closing braces that broke Compose scope and caused `ExtensionsSection` to be parsed as a local function (`private` modifier error) with follow-up syntax errors.
- RU: Исправлен сбой Android `compileCompactOpsDebugKotlin` в `MainActivity`: удалены две лишние закрывающие фигурные скобки, которые ломали Compose-скоуп и приводили к тому, что `ExtensionsSection` парсился как локальная функция (ошибка с `private`) с последующими синтаксическими ошибками.
- EN: SemVer patch bump to `8.53.14`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.14` and `ANDROID_VERSION_CODE=518`; prerelease links aligned to `v8.53.14-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.14`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.14` и `ANDROID_VERSION_CODE=518`; prerelease-ссылки выровнены на `v8.53.14-develop`.

## [8.53.13] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android `compileCompactOpsDebugKotlin` parse failure in `MainActivity`: added the missing `)` to close the settings `AlertDialog` call and restored closing braces for class scope so `ExtensionsSection` resolves correctly and is no longer treated as a local function.
- RU: Исправлен parse-сбой Android `compileCompactOpsDebugKotlin` в `MainActivity`: добавлена отсутствующая `)` для закрытия вызова `AlertDialog` в настройках и восстановлены закрывающие фигурные скобки класса, из-за чего `ExtensionsSection` снова корректно резолвится и больше не считается локальной функцией.
- EN: SemVer patch bump to `8.53.13`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.13` and `ANDROID_VERSION_CODE=517`; prerelease links aligned to `v8.53.13-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.13`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.13` и `ANDROID_VERSION_CODE=517`; prerelease-ссылки выровнены на `v8.53.13-develop`.

## [8.53.11] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android `compileCompactOpsDebugKotlin` failure in `MainActivity`: removed one extra closing brace in the settings layout block so `PullRefreshIndicator` remains inside the composable scope and parser errors no longer cascade into unresolved references/local-function diagnostics.
- RU: Исправлен сбой Android `compileCompactOpsDebugKotlin` в `MainActivity`: удалена одна лишняя закрывающая скобка в блоке layout настроек, из-за чего `PullRefreshIndicator` снова находится внутри composable-скоупа и больше не возникает каскад parser/unresolved-reference/local-function ошибок.
- EN: SemVer patch bump to `8.53.11`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.11` and `ANDROID_VERSION_CODE=515`; prerelease links aligned to `v8.53.11-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.11`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.11` и `ANDROID_VERSION_CODE=515`; prerelease-ссылки выровнены на `v8.53.11-develop`.

## [8.53.10] - 2026-04-17

### Changed / Изменено
- EN: Fixed `compileCompactOpsDebugKotlin` syntax failure in `MainActivity`: removed a stray `}, confirmButton = {}` fragment after the settings section, restoring valid Compose block structure and eliminating parser/unresolved-reference cascade errors.
- RU: Исправлен синтаксический сбой `compileCompactOpsDebugKotlin` в `MainActivity`: удалён лишний фрагмент `}, confirmButton = {}` после секции настроек, восстановлена корректная структура Compose-блоков и устранён каскад parser/unresolved-reference ошибок.
- EN: SemVer patch bump to `8.53.10`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.10` and `ANDROID_VERSION_CODE=514`; prerelease links aligned to `v8.53.10-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.10`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.10` и `ANDROID_VERSION_CODE=514`; prerelease-ссылки выровнены на `v8.53.10-develop`.

## [8.53.9] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android Compose build failure in `MainActivity`: removed an extra closing brace in the settings dialog block so `PullRefreshIndicator` stays inside the composable layout scope and Kotlin parser errors no longer cascade into unresolved references.
- RU: Исправлен сбой Android Compose-сборки в `MainActivity`: удалена лишняя закрывающая скобка в блоке диалога настроек, из-за чего `PullRefreshIndicator` снова находится в корректном composable-скоупе, а каскад синтаксических ошибок и `Unresolved reference` больше не возникает.
- EN: SemVer patch bump to `8.53.9`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.9` and `ANDROID_VERSION_CODE=513`; prerelease links aligned to `v8.53.9-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.9`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.9` и `ANDROID_VERSION_CODE=513`; prerelease-ссылки выровнены на `v8.53.9-develop`.

## [8.53.8] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android Compose build failure in `MainActivity`: added mandatory `confirmButton` for the settings `AlertDialog`, which resolves overload selection and removes `@Composable invocations can only happen from the context of a @Composable function` errors in `compileCompactOpsDebugKotlin`.
- RU: Исправлен сбой Android Compose-сборки в `MainActivity`: для `AlertDialog` окна настроек добавлен обязательный `confirmButton`, что корректно выбирает перегрузку и убирает ошибки `@Composable invocations can only happen from the context of a @Composable function` при `compileCompactOpsDebugKotlin`.
- EN: SemVer patch bump to `8.53.8`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.8` and `ANDROID_VERSION_CODE=512`; prerelease links aligned to `v8.53.8-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.8`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.8` и `ANDROID_VERSION_CODE=512`; prerelease-ссылки выровнены на `v8.53.8-develop`.

## [8.53.7] - 2026-04-17

### Changed / Изменено
- EN: Fixed Android Compose build failure in `MainActivity`: corrected `AlertDialog` block structure in settings UI so composable scopes close in the right order, eliminating syntax/composable-context cascade errors during `compileCompactOpsDebugKotlin`.
- RU: Исправлен падёж Android Compose-сборки в `MainActivity`: восстановлена корректная структура блока `AlertDialog` в UI настроек, чтобы composable-скоупы закрывались в правильном порядке и не вызывали каскад синтаксических/контекстных ошибок при `compileCompactOpsDebugKotlin`.
- EN: SemVer patch bump to `8.53.7`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.7` and `ANDROID_VERSION_CODE=511`; prerelease links aligned to `v8.53.7-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.7`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.7` и `ANDROID_VERSION_CODE=511`; prerelease-ссылки выровнены на `v8.53.7-develop`.

## [8.53.6] - 2026-04-17

### Changed / Изменено
- EN: Telegram `Main menu -> ZFS` status list now uses color markers per pool state: `🟢` for healthy pools (`ONLINE`) and `🔴` for problem states.
- RU: В Telegram `Главное меню -> ZFS` список статусов теперь помечается цветовыми маркерами по состоянию пула: `🟢` для штатного состояния (`ONLINE`) и `🔴` для проблемных состояний.
- EN: SemVer patch bump to `8.53.6`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.6` and `ANDROID_VERSION_CODE=510`; prerelease links aligned to `v8.53.6-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.6`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.6` и `ANDROID_VERSION_CODE=510`; prerelease-ссылки выровнены на `v8.53.6-develop`.

## [8.53.5] - 2026-04-17

### Changed / Изменено
- EN: Updated Telegram `Main menu -> ZFS` screen: it now shows the current ZFS pool status list (latest parsed states from mail monitoring data) directly in the ZFS root screen, while keeping navigation buttons for hosts and patterns.
- RU: Обновлён экран Telegram `Главное меню -> ZFS`: теперь в корневом экране ZFS показывается текущий список состояний ZFS-пулов (последние статусы из почтового мониторинга), при этом сохранены кнопки перехода к хостам и паттернам.
- EN: Adjusted `ZFS -> Hosts` presentation and onboarding for mail-based monitoring: host cards no longer display IP/threshold details, and host creation now requires only a host name because matching is done by parsed email patterns.
- RU: Скорректированы экран `ZFS -> Хосты` и добавление хостов для почтового мониторинга: карточки хостов больше не показывают IP/порог, а при добавлении требуется только имя хоста, так как сопоставление идёт по распарсенным паттернам писем.
- EN: SemVer patch bump to `8.53.5`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.5` and `ANDROID_VERSION_CODE=508`; prerelease links aligned to `v8.53.5-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.5`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.5` и `ANDROID_VERSION_CODE=508`; prerelease-ссылки выровнены на `v8.53.5-develop`.

## [8.53.3] - 2026-04-17

### Changed / Изменено
- EN: Reverted Telegram `🧊 ZFS` main-menu routing to the original ZFS monitor flow: `zfs_menu` now opens the ZFS monitoring menu (hosts/patterns for mail-based ZFS status parsing) instead of the SSH free-space screen.
- RU: Возвращена исходная маршрутизация `🧊 ZFS` в главном меню Telegram: `zfs_menu` снова открывает меню мониторинга ZFS (хосты/паттерны для парсинга почтовых статусов ZFS), а не экран SSH-свободного места.
- EN: Kept backward compatibility for internal ZFS entrypoints by redirecting legacy `show_zfs_status_summary` calls to the ZFS main menu.
- RU: Сохранена обратная совместимость внутренних точек входа ZFS: устаревший вызов `show_zfs_status_summary` теперь перенаправляется в главное меню ZFS.
- EN: SemVer patch bump to `8.53.3`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.3` and `ANDROID_VERSION_CODE=507`; prerelease links aligned to `v8.53.3-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.3`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.3` и `ANDROID_VERSION_CODE=507`; prerelease-ссылки выровнены на `v8.53.3-develop`.

## [8.53.2] - 2026-04-17

### Changed / Изменено
- EN: Telegram `🧊 ZFS` button behavior fixed: `zfs_menu` now opens live ZFS pool free-space summary for configured hosts instead of opening ZFS settings first.
- RU: Исправлено поведение кнопки Telegram `🧊 ZFS`: `zfs_menu` теперь открывает сводку по свободному месту ZFS-пулов хостов, а не меню настроек ZFS.
- EN: ZFS free-space collection switched from `zpool list` to `zfs list` in Telegram ZFS pool reporting modules; pool metrics are now calculated from root dataset (`USED + AVAIL`) to better match practical available space.
- RU: Сбор данных свободного места ZFS в Telegram-проверках переведён с `zpool list` на `zfs list`; метрики пула теперь считаются по корневому dataset (`USED + AVAIL`), что лучше отражает доступное место.
- EN: Removed `🔄 Refresh` button from ZFS status/free-space Telegram screens to simplify navigation and avoid redundant controls.
- RU: Убрана кнопка `🔄 Обновить` из экранов ZFS-статуса/свободного места в Telegram для упрощения навигации и удаления дублирующего действия.
- EN: SemVer patch bump to `8.53.2`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.53.2` and `ANDROID_VERSION_CODE=506`; prerelease links aligned to `v8.53.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.53.2`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.2` и `ANDROID_VERSION_CODE=506`; prerelease-ссылки выровнены на `v8.53.2-develop`.

## [8.53.1] - 2026-04-17

### Changed / Изменено
- EN: Completed SemVer patch bump to `8.53.1` by synchronizing remaining explicit version mentions across runtime/config/docs, including files that still had `8.52.0`/`8.53.0` after the previous release pass.
- RU: Завершён SemVer patch-бамп до `8.53.1`: синхронизированы оставшиеся явные упоминания версии в runtime/config/docs, включая файлы, где после прошлого релизного прохода ещё оставались `8.52.0`/`8.53.0`.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.53.1` and `ANDROID_VERSION_CODE=505`; prerelease links aligned to `v8.53.1-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.53.1` и `ANDROID_VERSION_CODE=505`; prerelease-ссылки выровнены на `v8.53.1-develop`.

## [8.53.0] - 2026-04-17

### Changed / Изменено
- EN: Restored `🧊 ZFS` behavior in Telegram main menu: `zfs_menu` now opens the original ZFS extension menu (hosts/patterns for mail-based ZFS status monitoring) instead of SSH free-space output.
- RU: Восстановлено поведение `🧊 ZFS` в главном меню Telegram: `zfs_menu` снова открывает исходное меню расширения ZFS (хосты/паттерны для почтового мониторинга статуса ZFS), а не SSH-вывод свободного места.
- EN: Added a separate Telegram extension `💽 Free space on ZFS pools` with independent enable/disable toggle in extension management and a dedicated main-menu button.
- RU: Добавлено отдельное Telegram-расширение `💽 Свободное место ZFS пулов` с независимым включением/выключением в управлении расширениями и отдельной кнопкой в главном меню.
- EN: Implemented dedicated host management for the new free-space extension (add/edit/delete/activate/deactivate), with required fields `host name`, `IP`, and `alert threshold`; SSH authorization is reused from common SSH settings.
- RU: Реализовано отдельное управление хостами для нового расширения свободного места (добавить/редактировать/удалить/активировать/деактивировать) с полями `имя хоста`, `IP` и `порог алерта`; SSH-авторизация используется из общих SSH-настроек.
- EN: Added scheduled polling of ZFS pool free space into the common monitoring loop for the new extension, with threshold alerts and recovery notifications.
- RU: Добавлен плановый опрос свободного места ZFS-пулов в общий цикл мониторинга для нового расширения, с пороговыми алертами и уведомлениями о восстановлении.
- EN: SemVer **minor** bump to `8.53.0`; synchronized explicit version mentions in runtime/config/docs and Android metadata to `ANDROID_VERSION_NAME=8.53.0`, `ANDROID_VERSION_CODE=504`.
- RU: Выполнен SemVer **minor**-бамп до `8.53.0`; синхронизированы явные упоминания версии в runtime/config/docs и Android-метаданных до `ANDROID_VERSION_NAME=8.53.0`, `ANDROID_VERSION_CODE=504`.

## [8.52.0] - 2026-04-17

### Changed / Изменено
- EN: Telegram ZFS extension upgraded to monitor free space on ZFS pools of backup hosts via SSH in the common monitoring loop schedule; alerts now trigger when free space drops below a per-host threshold.
- RU: Расширение ZFS в Telegram доработано: добавлен мониторинг свободного места на ZFS-пулах backup-хостов по SSH в общем расписании цикла проверок; алерты срабатывают при падении свободного места ниже порога конкретного хоста.
- EN: Added/updated Telegram UX for ZFS extension: ZFS button in start menu, `zfs_menu` now returns live pool free-space details, and host management now supports add/edit/delete/activate/deactivate with fields `name`, `ip`, and `alert threshold`.
- RU: Обновлён Telegram UX расширения ZFS: добавлена кнопка ZFS в стартовое меню, по `zfs_menu` теперь выводятся актуальные данные по свободному месту пулов, а управление хостами поддерживает добавление/редактирование/удаление/активацию/деактивацию с полями `имя`, `ip` и `порог алерта`.
- EN: Android `Settings → Time`: merged `Notifications ON`/`Notifications OFF` into a single toggle-style button that flips state on tap.
- RU: Android `Настройки → Время`: кнопки `Уведомления ВКЛ` и `Уведомления ВЫКЛ` объединены в одну кнопку-переключатель с инверсией состояния по нажатию.
- EN: Android `Settings → Extensions`: removed the `Open extension settings` button; extension settings menu now auto-loads when the section is opened.
- RU: Android `Настройки → Расширения`: удалена кнопка `Открыть настройки расширений`; меню настроек расширений теперь автоматически подгружается при входе в раздел.
- EN: Restyled extension management actions (`Enable all`/`Disable all` and per-extension toggle) to fit the app’s Material 3 settings style.
- RU: Кнопки управления расширениями (`Включить все`/`Отключить все` и индивидуальный toggle расширения) визуально приведены к стилю приложения на Material 3.
- EN: SemVer **minor** bump to `8.52.0`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.52.0` and `ANDROID_VERSION_CODE=503`; prerelease links aligned to `v8.52.0-develop`.
- RU: Выполнен SemVer **minor**-бамп до `8.52.0`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.52.0` и `ANDROID_VERSION_CODE=503`; prerelease-ссылки выровнены на `v8.52.0-develop`.

## [8.51.4] - 2026-04-17

### Changed / Изменено
- EN: In Android settings dialog, replaced the text close button with a header `X` icon to close the window.
- RU: В Android-диалоге настроек текстовая кнопка закрытия заменена на крестик `X` в заголовке окна.
- EN: Removed `Servers` and `Theme` section chips from settings sections list and removed dual theme chips from the dialog body.
- RU: Из списка разделов настроек убраны плашки `Серверы` и `Тема`, а также удалён блок из двух отдельных переключателей темы внутри тела диалога.
- EN: Added a single icon-only theme toggle button in the settings header and placed it to the left of the close icon; icon now reflects the target mode (`DarkMode`/`LightMode`).
- RU: Добавлена единая кнопка переключения темы только с иконкой в заголовке настроек; кнопка размещена слева от крестика, а иконка отражает целевой режим (`DarkMode`/`LightMode`).
- EN: SemVer patch bump to `8.51.4`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.51.4` and `ANDROID_VERSION_CODE=499`; prerelease links aligned to `v8.51.4-develop`.
- RU: Выполнен SemVer patch-бамп до `8.51.4`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.51.4` и `ANDROID_VERSION_CODE=499`; prerelease-ссылки выровнены на `v8.51.4-develop`.

## [8.51.3] - 2026-04-17

### Changed / Изменено
- EN: Fixed broken `AlertDialog` composition structure in Android `MainActivity.kt` settings overlay: restored missing block closure so `confirmButton` stays inside the dialog call and settings sections compile correctly (`:app:compileCompactOpsDebugKotlin`).
- RU: Исправлена сломанная структура композиции `AlertDialog` в Android `MainActivity.kt` (окно настроек): восстановлено пропущенное закрытие блока, из-за чего `confirmButton` снова находится внутри вызова диалога, а секции настроек корректно компилируются (`:app:compileCompactOpsDebugKotlin`).
- EN: SemVer patch bump to `8.51.3`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.51.3` and `ANDROID_VERSION_CODE=498`; prerelease links aligned to `v8.51.3-develop`.
- RU: Выполнен SemVer patch-бамп до `8.51.3`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.51.3` и `ANDROID_VERSION_CODE=498`; prerelease-ссылки выровнены на `v8.51.3-develop`.

## [8.51.2] - 2026-04-17

### Changed / Изменено
- EN: Renamed Android dashboard action from `⚙️ General settings` to `⚙️ Settings` and changed opening behavior: settings now open as an overlay dialog instead of inline block expansion.
- RU: Переименован пункт в Android-дашборде с `⚙️ Общие настройки` на `⚙️ Настройки`, а открытие переработано в формат окна с наложением (overlay) вместо разворота инлайнового блока.
- EN: Inside the settings overlay, section selectors and theme controls were migrated from buttons to `FilterChip` toggle tiles for faster section switching.
- RU: Внутри окна настроек кнопки выбора разделов и темы заменены на плашки-переключатели (`FilterChip`) для более быстрого переключения.
- EN: SemVer patch bump to `8.51.2`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.51.2` and `ANDROID_VERSION_CODE=497`; prerelease links aligned to `v8.51.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.51.2`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.51.2` и `ANDROID_VERSION_CODE=497`; prerelease-ссылки выровнены на `v8.51.2-develop`.

## [8.51.0] - 2026-04-16

### Changed / Изменено
- EN: Added mobile/Telegram extension action `zfs_free_space` and expanded `zfs_menu`: the response now includes live polling of free space on Proxmox Backup Server ZFS pools `rpool`/`zfs` over SSH for enabled backup hosts (`PROXMOX_HOSTS`), with per-host capacity, used percent, and pool health.
- RU: Добавлено действие расширения `zfs_free_space` для mobile/Telegram и расширен `zfs_menu`: ответ теперь включает живой опрос свободного места на ZFS-пулах `rpool`/`zfs` Proxmox Backup Server по SSH для включённых backup-хостов (`PROXMOX_HOSTS`), с выводом ёмкости, процента занятости и здоровья пула по каждому хосту.
- EN: SemVer **minor** bump to `8.51.0`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.51.0` and `ANDROID_VERSION_CODE=495`; prerelease links aligned to `v8.51.0-develop`.
- RU: Выполнен SemVer **minor**-бамп до `8.51.0`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.51.0` и `ANDROID_VERSION_CODE=495`; prerelease-ссылки выровнены на `v8.51.0-develop`.
## [8.50.142] - 2026-04-16

### Changed / Изменено
- EN: Fixed Android compile error in `MainActivity.kt`: `buildPatternOptionGroups` now uses the fully qualified `ru.monitoring.mobile.api.MenuOption` type, removing unresolved reference errors (`MenuOption`/`label`) during `:app:compileCompactOpsDebugKotlin`.
- RU: Исправлена ошибка компиляции Android в `MainActivity.kt`: функция `buildPatternOptionGroups` теперь использует полностью квалифицированный тип `ru.monitoring.mobile.api.MenuOption`, что убирает `Unresolved reference` (`MenuOption`/`label`) на шаге `:app:compileCompactOpsDebugKotlin`.
- EN: SemVer patch bump to `8.50.142`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.142` and `ANDROID_VERSION_CODE=488`; prerelease links aligned to `v8.50.142-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.142`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.142` и `ANDROID_VERSION_CODE=488`; prerelease-ссылки выровнены на `v8.50.142-develop`.

## [8.50.140] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → Proxmox backups` (dialog opened by tapping the Proxmox tile), host tile background color now reflects incidents only for hosts with monitoring enabled; disabled hosts no longer turn problem-red.
- RU: В Android-приложении в `Оперативный центр → Бэкапы Proxmox` (диалог после тапа по плашке Proxmox) цвет плашки хоста теперь показывает инцидент только для хостов с включённым мониторингом; отключённые хосты больше не подсвечиваются как проблемные.
- EN: SemVer patch bump to `8.50.140`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.140` and `ANDROID_VERSION_CODE=486`; prerelease links aligned to `v8.50.140-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.140`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.140` и `ANDROID_VERSION_CODE=486`; prerelease-ссылки выровнены на `v8.50.140-develop`.

## [8.50.139] - 2026-04-15

### Changed / Изменено
- EN: Android Proxmox backup host tiles now separate semantics: the circle marker on tile text shows only monitoring state (`🟢` enabled / `⚪` disabled), while backup incident state is conveyed by tile background color (`errorContainer` when a problem is detected).
- RU: В Android-плашках хостов Proxmox разделена семантика индикации: цветной кружок в тексте плашки теперь показывает только состояние мониторинга (`🟢` включён / `⚪` выключен), а наличие проблем бэкапа отображается цветом самой плашки (`errorContainer` при проблеме).
- EN: For Proxmox host labels, leading status emojis from backup result lines are sanitized in card text to avoid mixing backup incident markers with monitoring-state markers.
- RU: Для подписей хостов Proxmox в тексте карточек убраны лидирующие статус-эмодзи из строк результатов бэкапа, чтобы не смешивать маркеры инцидентов с маркерами состояния мониторинга.
- EN: SemVer patch bump to `8.50.139`; Android metadata updated to `ANDROID_VERSION_NAME=8.50.139` and `ANDROID_VERSION_CODE=485`; prerelease links aligned to `v8.50.139-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.139`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.139` и `ANDROID_VERSION_CODE=485`; prerelease-ссылки выровнены на `v8.50.139-develop`.

## [8.50.137] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Resources → gear → Resource check parameters`, added a Telegram-bot-like current-threshold summary with numeric values for CPU/RAM/Disk warning and critical levels (`80/90`, `85/95`, `80/90` defaults) directly in the dialog.
- RU: В Android-приложении в `Ресурсы → шестерёнка → Параметры проверки ресурсов` добавлено отображение текущих порогов в формате как в Telegram-боте: числовая сводка по CPU/RAM/Disk (предупреждение и критический, с дефолтами `80/90`, `85/95`, `80/90`).
- EN: Resource threshold values are now reflected immediately after change in the same session (optimistic UI update), so the current-parameters block shows the entered value without extra navigation.
- RU: Значения порогов ресурсов теперь сразу отражаются после изменения в рамках текущей сессии (optimistic UI), поэтому блок текущих параметров показывает введённое значение без дополнительной навигации.
- EN: SemVer patch bump to `8.50.137`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.137` and `ANDROID_VERSION_CODE=483`; prerelease links aligned to `v8.50.137-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.137`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.137` и `ANDROID_VERSION_CODE=483`; prerelease-ссылки выровнены на `v8.50.137-develop`.

## [8.50.136] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Resources → gear → Resource check parameters`, the dialog now displays current values for each threshold (warning/critical for CPU, RAM, Disk), so edits start from visible live settings.
- RU: В Android-приложении в `Ресурсы → шестерёнка → Параметры проверки ресурсов` диалог теперь показывает текущие значения порогов (предупреждение/критический для CPU, RAM, Disk), чтобы менять параметры от видимого актуального состояния.
- EN: Added an explicit close icon (`X`) in the `Resource check parameters` dialog header and removed the text button `Close`.
- RU: В диалог `Параметры проверки ресурсов` добавлен явный крестик (`X`) в заголовке и убрана текстовая кнопка `Закрыть`.
- EN: In the threshold edit dialog, added a line with the current value before entering a new percentage.
- RU: В диалоге изменения порога добавлена строка с отображением текущего значения перед вводом нового процента.
- EN: SemVer patch bump to `8.50.136`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.136` and `ANDROID_VERSION_CODE=482`; prerelease links aligned to `v8.50.136-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.136`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.136` и `ANDROID_VERSION_CODE=482`; prerelease-ссылки выровнены на `v8.50.136-develop`.

## [8.50.133] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → resources`, fixed the tile gear action: tapping `⚙️` on the resources tile now opens the resources settings dialog (same behavior as long press).
- RU: В Android-приложении в `Оперативный центр → ресурсы` исправлено действие шестерёнки на плашке: тап по `⚙️` теперь открывает диалог настроек ресурсов (как и долгий тап).
- EN: SemVer patch bump to `8.50.133`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.133` and `ANDROID_VERSION_CODE=479`; prerelease links aligned to `v8.50.133-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.133`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.133` и `ANDROID_VERSION_CODE=479`; prerelease-ссылки выровнены на `v8.50.133-develop`.

## [8.50.129] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → Servers` (dialog opened by tapping the `Servers` tile), swapped visual status markers: the circle now reflects monitoring activity (enabled/disabled host), while unavailable hosts are highlighted by card background color.
- RU: В Android-приложении в `Оперативный центр → Серверы` (диалог после тапа по плашке `Серверы`) поменяли местами визуальные маркеры: кружок теперь показывает активность мониторинга хоста (вкл/выкл), а недоступный хост подсвечивается цветом самой плашки.
- EN: SemVer patch bump to `8.50.129`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.129` and `ANDROID_VERSION_CODE=475`; prerelease links aligned to `v8.50.129-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.129`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.129` и `ANDROID_VERSION_CODE=475`; prerelease-ссылки выровнены на `v8.50.129-develop`.

## [8.50.128] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → Proxmox backups`, in the host actions dialog (opened by long tap on a host tile), pressing `Delete` now opens a confirmation dialog before deleting the host.
- RU: В Android-приложении в `Оперативный центр → Бэкапы Proxmox` в диалоге действий хоста (открывается долгим тапом по плашке хоста) нажатие `Удал.` теперь сначала открывает диалог подтверждения перед удалением хоста.
- EN: SemVer patch bump to `8.50.128`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.128` and `ANDROID_VERSION_CODE=474`; prerelease links aligned to `v8.50.128-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.128`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.128` и `ANDROID_VERSION_CODE=474`; prerelease-ссылки выровнены на `v8.50.128-develop`.

## [8.50.127] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → Servers`, pressing `Edit` in the host actions dialog (opened by long tap on a host tile) now opens direct host editing instead of navigating to the settings section.
- RU: В Android-приложении в `Оперативный центр → Серверы` кнопка `Изм.` в диалоге действий хоста (открывается долгим тапом по плашке хоста) теперь открывает прямое редактирование хоста вместо перехода в раздел настроек.
- EN: In the same dialog flow, add/edit server modal now adapts title and confirm text for edit mode and locks IP field while editing an existing host.
- RU: В этом же сценарии диалог добавления/редактирования сервера теперь подстраивает заголовок и текст подтверждения для режима редактирования, а поле IP блокируется при правке существующего хоста.
- EN: SemVer patch bump to `8.50.127`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.127` and `ANDROID_VERSION_CODE=473`; prerelease links aligned to `v8.50.127-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.127`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.127` и `ANDROID_VERSION_CODE=473`; prerelease-ссылки выровнены на `v8.50.127-develop`.

## [8.50.126] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → Databases`, swapped header action buttons in the dialog opened from the DB tile: `+` (add database) is now shown before `⚙️` (backup patterns/settings).
- RU: В Android-приложении в `Оперативный центр → БД` в заголовке диалога после тапа по плашке БД поменяны местами кнопки действий: теперь `+` (добавить БД) отображается раньше `⚙️` (паттерны/настройки бэкапов).
- EN: In Android app `Operational center → ZFS`, swapped header action buttons in the status dialog opened from the ZFS tile: `+` (add host) is now shown before `⚙️` (ZFS patterns/settings).
- RU: В Android-приложении в `Оперативный центр → ZFS` в заголовке диалога статусов после тапа по плашке ZFS поменяны местами кнопки действий: теперь `+` (добавить хост) отображается раньше `⚙️` (паттерны/настройки ZFS).
- EN: SemVer patch bump to `8.50.126`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.126` and `ANDROID_VERSION_CODE=472`; prerelease links aligned to `v8.50.126-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.126`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.126` и `ANDROID_VERSION_CODE=472`; prerelease-ссылки выровнены на `v8.50.126-develop`.

## [8.50.125] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → Proxmox backups`, swapped the header action buttons so `+` (add server) is now shown before `⚙️` (patterns/settings) after tapping the Proxmox tile.
- RU: В Android-приложении в `Оперативный центр → Бэкапы Proxmox` в заголовке после тапа по плашке Proxmox поменяны местами кнопки действий: теперь `+` (добавить сервер) отображается раньше `⚙️` (паттерны/настройки).
- EN: In Android app `Operational center → Databases` and `Operational center → ZFS`, short tap on tiles/cards now opens host/database actions (edit / enable-disable / delete) directly, matching the requested quick-access flow.
- RU: В Android-приложении в `Оперативный центр → БД` и `Оперативный центр → ZFS` короткий тап по плашкам теперь сразу открывает действия по объекту (редактировать / вкл-выкл / удалить) по запросу на быстрый доступ.
- EN: In Android app `Operational center → Resources (point checks)`, swapped the `⚙️` and `✖` buttons in the dialog header opened from the `resources` tile.
- RU: В Android-приложении в `Оперативный центр → Ресурсы (точечные проверки)` в заголовке диалога, который открывается с плашки `ресурсы`, поменяны местами кнопки `⚙️` и `✖`.
- EN: SemVer patch bump to `8.50.125`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.125` and `ANDROID_VERSION_CODE=471`; prerelease links aligned to `v8.50.125-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.125`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.125` и `ANDROID_VERSION_CODE=471`; prerelease-ссылки выровнены на `v8.50.125-develop`.

## [8.50.121] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center → ZFS`, removed the bottom status text `enable/disable …` from the host actions dialog opened by long tap on a host tile.
- RU: В Android-приложении в `Оперативный центр → ZFS` из диалога действий хоста (открывается долгим тапом по плашке хоста) убран нижний статусный текст `включить/отключить …`.
- EN: In Android app `Operational center → ZFS`, removed the `Close` text button from the same host actions dialog; closing is now done via the top-right icon or outside tap.
- RU: В Android-приложении в `Оперативный центр → ZFS` в этом же диалоге убрана текстовая кнопка `Закрыть`; закрытие выполняется иконкой в правом верхнем углу или тапом вне окна.
- EN: SemVer patch bump to `8.50.121`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.121` and `ANDROID_VERSION_CODE=468`; prerelease links aligned to `v8.50.121-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.121`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.121` и `ANDROID_VERSION_CODE=468`; prerelease-ссылки выровнены на `v8.50.121-develop`.

## [8.50.117] - 2026-04-15

### Changed / Изменено
- EN: In Android app `Operational center`, short taps on tiles `Servers`, `proxmox`, and `resources` now additionally show a hint that long-press actions are available on each tile.
- RU: В Android-приложении в `Оперативный центр` короткий тап по плашкам `Серверы`, `proxmox` и `ресурсы` теперь дополнительно показывает подсказку о доступности действий по долгому тапу для каждой плашки.
- EN: SemVer patch bump to `8.50.117`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.117` and `ANDROID_VERSION_CODE=464`; prerelease links aligned to `v8.50.117-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.117`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.117` и `ANDROID_VERSION_CODE=464`; prerelease-ссылки выровнены на `v8.50.117-develop`.

## [8.50.115] - 2026-04-15

### Changed / Изменено
- EN: In Android app dashboard, the `Servers` tile now runs single-server checks on short tap (same behavior that previously required a long tap), reducing interaction steps.
- RU: В дашборде Android-приложения плашка `Серверы` теперь запускает точечные проверки по короткому тапу (то же поведение, которое раньше было только по долгому тапу), что сокращает количество действий.
- EN: SemVer patch bump to `8.50.115`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.115` and `ANDROID_VERSION_CODE=462`; prerelease links aligned to `v8.50.115-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.115`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.115` и `ANDROID_VERSION_CODE=462`; prerelease-ссылки выровнены на `v8.50.115-develop`.

## [8.50.114] - 2026-04-15

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, fixed host activity markers flickering from green to yellow right after opening the host list by preserving known monitoring state when settings payload arrives later.
- RU: В Android-приложении в `Оперативный центр → ZFS` исправлено мигание маркеров активности хостов из зелёного в жёлтый сразу после открытия списка: теперь сохраняется уже известное состояние мониторинга, даже если payload настроек приходит позже.
- EN: In Android app `Operational center → ZFS`, fixed stale marker state after long-press host actions (`enable/disable monitoring`): disabled hosts no longer end up incorrectly highlighted as active (green).
- RU: В Android-приложении в `Оперативный центр → ZFS` исправлено зависание состояния маркеров после действий по долгому тапу (`вкл/выкл мониторинга`): выключенные хосты больше не подсвечиваются ошибочно как активные (зелёным).

### Changed / Изменено
- EN: SemVer patch bump to `8.50.114`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.114` and `ANDROID_VERSION_CODE=461`.
- RU: Выполнен SemVer patch-бамп до `8.50.114`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.114` и `ANDROID_VERSION_CODE=461`.

## [8.50.110] - 2026-04-15

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, a long press on a host tile now opens host settings actions (edit name, enable/disable monitoring, delete), with explicit hints in the status and hosts dialogs.
- RU: В Android-приложении в `Оперативный центр → ZFS` долгий тап по плашке хоста теперь открывает действия настройки хоста (редактирование имени, вкл/выкл мониторинга, удаление), добавлены явные подсказки в диалогах статусов и списка хостов.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.110`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.110` and `ANDROID_VERSION_CODE=457`.
- RU: Выполнен SemVer patch-бамп до `8.50.110`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.110` и `ANDROID_VERSION_CODE=457`.

## [8.50.105] - 2026-04-14

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, the host counter now also uses host names from `settings_zfs_list` actions, so configured hosts are counted even when one host is powered off and has no fresh pool status rows.
- RU: В Android-приложении в `Оперативный центр → ZFS` счётчик хостов теперь дополнительно учитывает имена из действий `settings_zfs_list`, поэтому сконфигурированные хосты считаются даже если один выключен и по нему нет свежих строк статуса пулов.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.105`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.105` and `ANDROID_VERSION_CODE=453`; prerelease links aligned to `v8.50.105-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.105`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.105` и `ANDROID_VERSION_CODE=453`; prerelease-ссылки выровнены на `v8.50.105-develop`.

## [8.50.104] - 2026-04-14

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, the host counter in the status dialog now respects `Всего хостов` from backend payload and no longer drops powered-off hosts from the total number.
- RU: В Android-приложении в `Оперативный центр → ZFS` счётчик хостов в диалоге статусов теперь учитывает `Всего хостов` из backend-payload и больше не теряет выключенные хосты в общем количестве.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.104`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.104` and `ANDROID_VERSION_CODE=452`; prerelease links aligned to `v8.50.104-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.104`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.104` и `ANDROID_VERSION_CODE=452`; prerelease-ссылки выровнены на `v8.50.104-develop`.

## [8.50.103] - 2026-04-14

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, the status dialog now builds host tiles from the union of status payload and `settings_zfs_list`, so disabled hosts remain visible in the list and are no longer dropped when monitoring is inactive.
- RU: В Android-приложении в `Оперативный центр → ZFS` диалог статусов теперь строит список хостов как объединение payload статусов и `settings_zfs_list`, поэтому отключённые хосты остаются видимыми и больше не пропадают при деактивированном мониторинге.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.103`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.103` and `ANDROID_VERSION_CODE=451`; prerelease links aligned to `v8.50.103-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.103`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.103` и `ANDROID_VERSION_CODE=451`; prerelease-ссылки выровнены на `v8.50.103-develop`.

## [8.50.97] - 2026-04-14

### Added / Добавлено
- EN: In Android app `Operational center`, added back the `ZFS` extension tile with Telegram-bot parity behavior: tile is shown when `zfs_monitor` is enabled, opens `zfs` action on tap, and uses ZFS summary/problem state for compact status display.
- RU: В Android-приложении в `Оперативном центре` возвращена плашка расширения `ZFS` с паритетом поведения с Telegram-ботом: плашка показывается при включённом `zfs_monitor`, по нажатию открывает действие `zfs`, а для компактного статуса использует сводку/проблемность ZFS.

### Fixed / Исправлено
- EN: Restored ZFS extension action-to-id mapping and fallback settings option (`settings_zfs`) in Android local menu filtering so extension settings stay available when `zfs_monitor` is enabled.
- RU: Восстановлен маппинг ZFS action→extension-id и fallback-пункт настроек (`settings_zfs`) в Android-логике локальной фильтрации меню, чтобы настройки расширения были доступны при включённом `zfs_monitor`.
- EN: In Android `Operational center → ZFS`, when card parsing returns empty but backend already sent a textual ZFS payload, the dialog now shows formatted raw statuses instead of the misleading `ZFS statuses have not been received yet`.
- RU: В Android `Оперативный центр → ZFS`, если карточки не распарсились, но бэкенд уже прислал текстовый payload со статусами, диалог теперь показывает форматированный исходный текст статусов вместо вводящего в заблуждение `Статусы ZFS пока не получены`.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.97`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.97` and `ANDROID_VERSION_CODE=445`; prerelease links aligned to `v8.50.97-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.97`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.97` и `ANDROID_VERSION_CODE=445`; prerelease-ссылки выровнены на `v8.50.97-develop`.

## [8.50.88] - 2026-04-14

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, opening ZFS statuses now additionally refreshes `settings_zfs_list`; when a host is disabled in Telegram (`Main menu → ZFS host settings`), its tile stays visible in the host pool status list and only monitoring activity state changes.
- RU: В Android-приложении в `Оперативный центр → ZFS` при открытии статусов теперь дополнительно обновляется `settings_zfs_list`; если хост отключён в Telegram (`Главное меню → Настройка хостов ZFS`), его плашка остаётся в списке статусов пулов, а меняется только статус активности мониторинга.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.88`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.88` and `ANDROID_VERSION_CODE=436`; prerelease links aligned to `v8.50.88-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.88`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.88` и `ANDROID_VERSION_CODE=436`; prerelease-ссылки выровнены на `v8.50.88-develop`.

## [8.50.86] - 2026-04-13

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, merged ZFS cards now preserve per-host summary status (`⚪/🟢/🔴`) while combining pool details, so tiles correctly show disabled hosts as neutral, healthy hosts as green, and problematic hosts as red instead of falling back to unknown/yellow.
- RU: В Android-приложении в `Оперативный центр → ZFS` при объединении карточек теперь сохраняется суммарный статус хоста (`⚪/🟢/🔴`) вместе с деталями пулов, поэтому плашки корректно показывают отключённые хосты как нейтральные, здоровые как зелёные, а проблемные как красные без отката в unknown/жёлтый.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.86`; synchronized version mentions across project runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.86` and `ANDROID_VERSION_CODE=434`; prerelease links aligned to `v8.50.86-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.86`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.86` и `ANDROID_VERSION_CODE=434`; prerelease-ссылки выровнены на `v8.50.86-develop`.

## [8.50.84] - 2026-04-13

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, host monitoring state on tiles is now derived from `settings_zfs_list` toggle semantics (`Enable` means currently disabled, `Disable` means currently enabled), so tiles no longer invert host enabled/disabled state.
- RU: В Android-приложении в `Оперативный центр → ZFS` состояние мониторинга хоста на плашках теперь определяется по семантике кнопки из `settings_zfs_list` (`Включить` означает «сейчас выключен», `Отключить` — «сейчас включен»), поэтому инверсия статуса включён/выключен устранена.
- EN: Tap on ZFS tile now refreshes `settings_zfs_list` together with `zfs_menu`, matching Telegram flow `Main menu → ZFS → ZFS host settings` and keeping host status badges up to date.
- RU: Тап по ZFS-плашке теперь обновляет `settings_zfs_list` вместе с `zfs_menu`, как в Telegram-сценарии `Главное меню → ZFS → Настройки хостов ZFS`, поэтому бейджи статусов хостов всегда актуальны.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.84`; synchronized version mentions across project runtime/config/docs and Android client artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.50.84` and `ANDROID_VERSION_CODE=432`; prerelease links aligned to `v8.50.84-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.84`; синхронизированы упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.84` и `ANDROID_VERSION_CODE=432`; prerelease-ссылки выровнены на `v8.50.84-develop`.

## [8.50.81] - 2026-04-13

### Fixed / Исправлено
- EN: In Telegram bot ZFS host settings, monitoring state changes are now persisted in backup DB table `zfs_monitoring_state` on add/toggle/rename/delete, so Android `Operational center → ZFS` can stay synchronized with bot state between refreshes.
- RU: В настройках ZFS-хостов Telegram-бота изменения состояния мониторинга теперь сохраняются в таблицу бэкап-БД `zfs_monitoring_state` при добавлении/переключении/переименовании/удалении, поэтому Android `Оперативный центр → ZFS` держит синхронизацию с ботом между обновлениями.
- EN: ZFS status summary now merges persisted monitoring state from DB with `ZFS_SERVERS` config, reducing cases where host monitoring was shown as `unknown`.
- RU: Сводка статусов ZFS теперь объединяет сохранённое в БД состояние мониторинга с конфигом `ZFS_SERVERS`, что снижает случаи, когда мониторинг хоста показывался как `неизвестно`.
- EN: In Android `Operational center`, tap on ZFS tile now only opens `zfs_menu` statuses and no longer forces `settings_zfs_list`, preventing long-tap host action flow from bouncing to common all-host statuses.
- RU: В Android `Оперативный центр` тап по плашке ZFS теперь открывает только статусы `zfs_menu` и больше не форсит `settings_zfs_list`, из-за чего long tap по хосту перестал отбрасывать в общие статусы всех хостов.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.81`; synchronized version mentions across project files; Android metadata updated to `ANDROID_VERSION_NAME=8.50.81` and `ANDROID_VERSION_CODE=429`; prerelease link updated to `v8.50.81-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.81`; синхронизированы упоминания версии по файлам проекта; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.81` и `ANDROID_VERSION_CODE=429`; prerelease-ссылка обновлена на `v8.50.81-develop`.

## [8.50.80] - 2026-04-13

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS`, parsing now supports current Telegram ZFS summary lines (`🟢/🔴/⚪ host · ok/total · timestamp`), so host cards are built correctly and monitoring state no longer falls back to `unknown`.
- RU: В Android-приложении в `Оперативный центр → ZFS` разбор теперь поддерживает актуальные summary-строки Telegram (`🟢/🔴/⚪ host · ok/total · timestamp`), поэтому карточки хостов строятся корректно, а статус мониторинга больше не уходит в `неизвестно`.
- EN: Long tap on a ZFS host tile now opens that host's actions directly from cached `settings_zfs_list` data; fallback request is used only when host actions are missing, so long tap no longer bounces back to common ZFS statuses.
- RU: Долгий тап по ZFS-плашке хоста теперь сразу открывает действия этого хоста из кэша `settings_zfs_list`; запасной запрос выполняется только если действий нет, поэтому long tap больше не отбрасывает в общие статусы ZFS.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.80`; synchronized version mentions across project files; Android metadata updated to `ANDROID_VERSION_NAME=8.50.80` and `ANDROID_VERSION_CODE=428`.
- RU: Выполнен SemVer patch-бамп до `8.50.80`; синхронизированы упоминания версии по файлам проекта; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.80` и `ANDROID_VERSION_CODE=428`.

## [8.50.79] - 2026-04-13

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS tile`, tap now refreshes both `zfs_menu` statuses and `settings_zfs_list`, so host monitoring enabled/disabled markers stay synchronized with Telegram `Main menu → ZFS`.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS` тап теперь обновляет и статусы `zfs_menu`, и настройки `settings_zfs_list`, поэтому маркеры включён/выключен для мониторинга хостов остаются синхронизированы с Telegram `Главное меню → ZFS`.
- EN: ZFS status dialog now uses a dedicated cached `zfsStatusMessage` from `zfs_menu`; opening host settings no longer overwrites status cards/details with generic fallback text.
- RU: Диалог статусов ZFS теперь использует отдельный кэш `zfsStatusMessage` из `zfs_menu`; при открытии настроек хостов статусы/детали больше не перетираются в общий фолбэк-текст.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.79`; synchronized project version mentions across runtime/config/docs/Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.79` and `ANDROID_VERSION_CODE=427`; aligned prerelease links to `v8.50.79-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.79`; синхронизированы упоминания версии в runtime/config/docs/Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.79` и `ANDROID_VERSION_CODE=427`; prerelease-ссылки выровнены на `v8.50.79-develop`.

## [8.50.77] - 2026-04-13

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile`, host monitoring enabled/disabled state is now taken from a dedicated cached `settings_zfs_list` snapshot, so state stays synchronized with Telegram `Main menu → ZFS` even after switching between ZFS submenus.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS` состояние включён/выключен для мониторинга хостов теперь берётся из отдельного кэша снимка `settings_zfs_list`, поэтому синхронизация с Telegram `Главное меню → ZFS` сохраняется даже после переключения между подменю ZFS.
- EN: Added persistent `zfsHostMenuOptions` state in `MainViewModel`; ZFS status dialog now resolves host monitoring markers from this cached list instead of depending on the currently opened extension settings submenu.
- RU: В `MainViewModel` добавлено постоянное состояние `zfsHostMenuOptions`; диалог статусов ZFS теперь определяет маркеры мониторинга хостов из этого кэша, а не зависит от того, какое подменю настроек расширений открыто в текущий момент.
- EN: SemVer patch bump to `8.50.77`; synchronized project version mentions across runtime/config/docs/Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.77` and `ANDROID_VERSION_CODE=425`; aligned prerelease links to `v8.50.77-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.77`; синхронизированы упоминания версии в runtime/config/docs/Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.77` и `ANDROID_VERSION_CODE=425`; prerelease-ссылки выровнены на `v8.50.77-develop`.

## [8.50.75] - 2026-04-13

### Changed / Изменено
- EN: In Android app `Operational center → ZFS → host status tile`, parsing of ZFS host settings is now based on callback actions (`settings_zfs_edit_name_*`, `settings_zfs_delete_*`, `settings_zfs_toggle_*`) instead of strict button order, so monitoring status is resolved reliably in details and tiles.
- RU: В Android-приложении в `Оперативный центр → ZFS → плашка статуса хоста` разбор настроек хостов ZFS переведён на callback-действия (`settings_zfs_edit_name_*`, `settings_zfs_delete_*`, `settings_zfs_toggle_*`) вместо жёсткой зависимости от порядка кнопок, поэтому статус мониторинга теперь корректно определяется и в деталях, и на плашке.
- EN: Disabled ZFS host monitoring in Telegram bot settings no longer removes host tiles from Android `Operational center → ZFS`; tiles remain visible and only the monitoring indicator color/state changes.
- RU: При отключении мониторинга ZFS-хоста в Telegram-боте хост больше не пропадает из Android `Оперативный центр → ZFS`; плашка остаётся, меняется только цвет/состояние индикатора мониторинга.
- EN: SemVer patch bump to `8.50.75`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.75` and `ANDROID_VERSION_CODE=423`; aligned prerelease links to `v8.50.75-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.75`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.75` и `ANDROID_VERSION_CODE=423`; prerelease-ссылки выровнены на `v8.50.75-develop`.
## [8.50.73] - 2026-04-13

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile → statuses`, each host tile now shows only host name (with monitoring-enabled indicator at the left) and the raw data receive time text without any extra labels.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS → статусы` на каждой плашке хоста оставлены только имя хоста (с индикатором включённости мониторинга слева) и время получения данных без дополнительных подписей.
- EN: Removed the separate `Monitoring: ...` row and other redundant text from compact ZFS status tiles; tile color remains aggregated by all host pools (`default` only when all pools are `ONLINE`, alert otherwise).
- RU: Убрана отдельная строка `Мониторинг: ...` и прочий лишний текст с компактных ZFS-плашек; цвет плашки по-прежнему агрегируется по всем пулам хоста (`стандартный` только когда все пулы `ONLINE`, иначе тревожный).
- EN: SemVer patch bump to `8.50.73`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.73` and `ANDROID_VERSION_CODE=421`; aligned prerelease links to `v8.50.73-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.73`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.73` и `ANDROID_VERSION_CODE=421`; prerelease-ссылки выровнены на `v8.50.73-develop`.
## [8.50.68] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile → statuses`, status tiles are now grouped by host and each tile shows a traffic-light indicator, host name, pool list, and data timestamp for every pool.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS → статусы` плашки теперь сгруппированы по хостам: каждая содержит светофор статуса, имя хоста, список пулов и время получения данных по каждому пулу.
- EN: For hosts with multiple pools, all pools are rendered on a single host tile (with compact truncation after the third pool), and the non-interactive fallback options list was removed from the dialog.
- RU: Для хостов с несколькими пулами все пулы отображаются на одной плашке хоста (с компактным сворачиванием после третьего пула), а неинтерактивный список дополнительных опций убран из диалога.
- EN: SemVer patch bump to `8.50.68`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.68` and `ANDROID_VERSION_CODE=417`; aligned prerelease links to `v8.50.68-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.68`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.68` и `ANDROID_VERSION_CODE=417`; prerelease-ссылки выровнены на `v8.50.68-develop`.

## [8.50.66] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile → statuses`, all parsed ZFS status items are rendered as interactive tiles even when backend action is absent.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS → статусы` все распознанные статусы ZFS теперь отображаются интерактивными плашками даже если для пункта не пришёл backend-action.
- EN: In Android app `Operational center → ZFS tile → statuses`, short tap opens received data details, and long tap opens ZFS host settings.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS → статусы` короткий тап открывает сведения о полученных данных, долгий тап открывает настройки хостов ZFS.
- EN: SemVer patch bump to `8.50.66`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.66` and `ANDROID_VERSION_CODE=415`; aligned prerelease links to `v8.50.66-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.66`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.66` и `ANDROID_VERSION_CODE=415`; prerelease-ссылки выровнены на `v8.50.66-develop`.

## [8.50.60] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile`, added a long tap on the main ZFS tile to open `ZFS host settings` directly.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS` добавлен долгий тап по основной плашке ZFS для прямого открытия `настроек хостов ZFS`.
- EN: In Android app `Operational center → ZFS tile → statuses`, short tap on a host status tile keeps opening host data details, while long tap opens host settings for the selected host.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS → статусы` короткий тап по плашке статуса открывает сведения по данным хоста, а долгий тап открывает настройки выбранного хоста.
- EN: SemVer patch bump to `8.50.60`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.60` and `ANDROID_VERSION_CODE=409`; aligned prerelease links to `v8.50.60-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.60`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.60` и `ANDROID_VERSION_CODE=409`; prerelease-ссылки выровнены на `v8.50.60-develop`.

## [8.50.59] - 2026-04-12

### Changed / Изменено
- EN: In Telegram bot `Settings → Extensions`, removed the `💻 Resources` item so resource thresholds are configured only from the server-resources flow.
- RU: В Telegram-боте в `Настройки → Расширения` удалён пункт `💻 Ресурсы`, чтобы пороги ресурсов настраивались только из сценария ресурсов сервера.
- EN: In Telegram bot `Main menu → Server resources → Resource settings → any threshold input`, changed the `❌ Cancel` action to return to `Resource settings` instead of the global settings root.
- RU: В Telegram-боте в `Главное меню → Ресурсы сервера → Настройки ресурсов → ввод любого порога` кнопка `❌ Отмена` теперь возвращает в `Настройки ресурсов`, а не в общий корень настроек.
- EN: SemVer patch bump to `8.50.59`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.59` and `ANDROID_VERSION_CODE=408`; aligned prerelease links to `v8.50.59-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.59`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.59` и `ANDROID_VERSION_CODE=408`; prerelease-ссылки выровнены на `v8.50.59-develop`.
## [8.50.57] - 2026-04-12

### Changed / Изменено
- EN: In Telegram bot `Main menu`, removed the `⚙️ Resource settings` button to keep resource tuning inside the dedicated resources flow.
- RU: В Telegram-боте в `Главном меню` удалена кнопка `⚙️ Настройки ресурсов`, чтобы настройки порогов открывались только из сценария проверки ресурсов.
- EN: In Telegram bot `Server resources → Resource settings`, added a dedicated `🏠 Home` button.
- RU: В Telegram-боте в `Ресурсы сервера → Настройки ресурсов` добавлена отдельная кнопка `🏠 На главную`.
- EN: In Telegram bot `Server resources → Resource settings`, changed the `↩️ Back` action to return to `Server resources` instead of the global settings root.
- RU: В Telegram-боте в `Ресурсы сервера → Настройки ресурсов` кнопка `↩️ Назад` теперь возвращает в `Ресурсы сервера`, а не в корень общих настроек.
- EN: SemVer patch bump to `8.50.57`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.57` and `ANDROID_VERSION_CODE=406`; aligned prerelease links to `v8.50.57-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.57`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.57` и `ANDROID_VERSION_CODE=406`; prerelease-ссылки выровнены на `v8.50.57-develop`.
## [8.50.54] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile → gear`, replaced duplicate gear actions with a unified `ZFS settings` entry point that opens a chooser with two sections: `Hosts` and `Patterns`, matching the Proxmox backup settings navigation style.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS → шестерёнка` заменены дублирующиеся действия шестерёнки на единую точку входа `Настройки ZFS` с выбором двух разделов: `Хосты` и `Паттерны`, по стилю навигации как в настройках бэкапов Proxmox.
- EN: SemVer patch bump to `8.50.54`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.54` and `ANDROID_VERSION_CODE=403`; aligned prerelease links to `v8.50.54-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.54`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.54` и `ANDROID_VERSION_CODE=403`; prerelease-ссылки выровнены на `v8.50.54-develop`.

## [8.50.50] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile`, compacted tapped ZFS status rows further: each host status is forced into a single line, host names are abbreviated when too long, and row paddings are tightened to use dialog space more efficiently.
- RU: В Android-приложении `Оперативный центр → плашка ZFS` ещё сильнее ужат вывод после тапа: статус каждого хоста принудительно держится в одной строке, длинные имена хостов сокращаются, отступы строк уменьшены для более плотного использования окна.
- EN: SemVer patch bump to `8.50.50`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.50` and `ANDROID_VERSION_CODE=399`; aligned prerelease links to `v8.50.50-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.50`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.50` и `ANDROID_VERSION_CODE=399`; prerelease-ссылки выровнены на `v8.50.50-develop`.

## [8.50.49] - 2026-04-12

### Added / Добавлено
- EN: In Telegram bot `Main menu → Server resources`, added a dedicated `⚙️ Configure check parameters` button that opens resource-threshold settings in one tap.
- RU: В Telegram-боте в `Главное меню → Ресурсы сервера` добавлена отдельная кнопка `⚙️ Настроить параметры проверки` для быстрого перехода к настройкам порогов ресурсов.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.49`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.49` and `ANDROID_VERSION_CODE=398`; aligned prerelease links to `v8.50.49-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.49`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.49` и `ANDROID_VERSION_CODE=398`; prerelease-ссылки выровнены на `v8.50.49-develop`.

## [8.50.47] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile`, compacted the tapped ZFS status rows even further into a single-line format: status icon first, then host name, then remaining status details.
- RU: В Android-приложении `Оперативный центр → плашка ZFS` вывод после тапа по ZFS сделан ещё компактнее в одну строку: сначала иконка статуса, затем имя хоста, дальше остальные детали статуса.
- EN: SemVer patch bump to `8.50.47`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.47` and `ANDROID_VERSION_CODE=396`; aligned prerelease links to `v8.50.47-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.47`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.47` и `ANDROID_VERSION_CODE=396`; prerelease-ссылки выровнены на `v8.50.47-develop`.

## [8.50.46] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile`, made the ZFS status output even more compact after tapping the tile: state labels are shortened (`OK/DEG/ERR/OFF/...`), timestamps are condensed (`MM-DD HH:MM` when recognizable), and redundant header/decorative lines are removed to reduce scrolling.
- RU: В Android-приложении `Оперативный центр → плашка ZFS` вывод статусов после тапа сделан ещё компактнее: сокращены метки состояний (`OK/DEG/ERR/OFF/...`), время ужато (`MM-DD HH:MM`, если формат распознан), лишние заголовки/декоративные строки убраны для уменьшения скролла.
- EN: In Telegram bot path `Settings → Extensions`, removed the `🧊 ZFS` button from the extensions menu.
- RU: В Telegram-боте в сценарии `Настройки → Расширения` удалена кнопка `🧊 ZFS` из списка расширений.
- EN: SemVer patch bump to `8.50.46`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.46` and `ANDROID_VERSION_CODE=395`; aligned prerelease links to `v8.50.46-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.46`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.46` и `ANDROID_VERSION_CODE=395`; prerelease-ссылки выровнены на `v8.50.46-develop`.

## [8.50.44] - 2026-04-12

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS tile`, fixed false `OK` state when backend returns raw per-pool statuses (`• pool: STATE (timestamp)`): the tile summary now parses such lines and correctly marks non-`ONLINE` pools as problems.
- RU: В Android-приложении в `Оперативный центр → плашка ZFS` исправлен ложный статус `ОК`, когда backend возвращает «сырые» статусы по пулам (`• pool: STATE (timestamp)`): сводка плашки теперь парсит такие строки и корректно помечает не-`ONLINE` пулы как проблему.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.44`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.44` and `ANDROID_VERSION_CODE=393`; aligned prerelease links to `v8.50.44-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.44`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.44` и `ANDROID_VERSION_CODE=393`; prerelease-ссылки выровнены на `v8.50.44-develop`.

## [8.50.43] - 2026-04-12

### Changed / Изменено
- EN: In Android app `Operational center → ZFS tile`, the ZFS statuses dialog is now denser: reduced inter-item spacing/padding and tighter line-height in status text to minimize scrolling.
- RU: В Android-приложении `Оперативный центр → плашка ZFS` диалог статусов сделан более плотным: уменьшены интервалы/отступы и межстрочное расстояние в тексте статусов, чтобы меньше скроллить.
- EN: Added an explicit `Close` (X) icon button in the ZFS statuses dialog header for faster one-tap dismiss.
- RU: В заголовок диалога статусов ZFS добавлена явная кнопка закрытия `✕` для быстрого закрытия в один тап.
- EN: In Telegram bot `Main menu → ZFS`, added a dedicated `⚙️ ZFS pattern settings` button on the ZFS status screen for one-tap access to ZFS patterns management.
- RU: В Telegram-боте в `Главное меню → ZFS` на экране статусов добавлена отдельная кнопка `⚙️ Настройка паттернов ZFS` для быстрого перехода к управлению паттернами ZFS.
- EN: In Telegram bot `Main menu → ZFS → ZFS pattern settings`, removed the `↩️ Back` button from the patterns screen; only `Home` and `Close` controls are kept.
- RU: В Telegram-боте в `Главное меню → ZFS → Настройка паттернов ZFS` убрана кнопка `↩️ Назад` на экране паттернов; оставлены только `На главную` и `Закрыть`.
- EN: SemVer patch bump to `8.50.43`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.43` and `ANDROID_VERSION_CODE=392`; aligned prerelease links to `v8.50.43-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.43`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.43` и `ANDROID_VERSION_CODE=392`; prerelease-ссылки выровнены на `v8.50.43-develop`.

## [8.50.37] - 2026-04-12

### Fixed / Исправлено
- EN: In Android app `Operational center → ZFS tile`, tapping the tile no longer falls back to `ZFS statuses have not been received yet` when backend returns message-only response; the dialog now keeps `zfs_menu` context and shows the latest ZFS status message correctly.
- RU: В Android-приложении `Оперативный центр → плашка ZFS` исправлен ложный фолбэк `Статусы ZFS пока не получены.` при ответе backend только сообщением; диалог теперь сохраняет контекст `zfs_menu` и корректно показывает актуальный текст статусов ZFS.

### Added / Добавлено
- EN: In Android app `Operational center`, tapping the `ZFS` tile now opens an overlay dialog that displays current ZFS statuses and allows quick refresh from the same window.
- RU: В Android-приложении в `Оперативном центре` тап по плашке `ZFS` теперь открывает окно-наложение с текущими статусами ZFS и возможностью быстрого обновления прямо из этого окна.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.37`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.37` and `ANDROID_VERSION_CODE=386`; aligned prerelease links to `v8.50.37-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.37`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.37` и `ANDROID_VERSION_CODE=386`; prerelease-ссылки выровнены на `v8.50.37-develop`.

## [8.50.35] - 2026-04-12

### Fixed / Исправлено
- EN: Reworked Telegram ZFS status summary rendering for quick scanning: output is now compact and highlights health at a glance with aggregated counters (`servers`, `pools`) and explicit server-level problem markers.
- RU: Переработано отображение сводки статусов ZFS в Telegram для быстрого просмотра: вывод стал компактнее и сразу подсвечивает здоровье через агрегированные счётчики (`серверы`, `пулы`) и явные маркеры проблем по серверам.

### Added / Добавлено
- EN: Added per-server compact lines in Telegram ZFS summary (`ok/total` + latest timestamp) and concise problem details for non-ONLINE pools to reduce noise while preserving diagnostics.
- RU: Добавлены компактные строки по каждому серверу в Telegram-сводке ZFS (`ok/total` + время последнего статуса) и короткая детализация проблемных пулов (не `ONLINE`) без лишнего шума.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.35`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.35` and `ANDROID_VERSION_CODE=384`; aligned prerelease links to `v8.50.35-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.35`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.35` и `ANDROID_VERSION_CODE=384`; prerelease-ссылки выровнены на `v8.50.35-develop`.
## [8.50.28] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Mail tile → Mail backup patterns`, mail pattern cards now render full pattern content from backend settings message (`N. <type>: <regex>`), and a `mail` section header is shown above the list to match expected Telegram-style structure.
- RU: В Android-приложении `Оперативный центр → плитка Почта → Паттерны бэкапов почты` карточки паттернов теперь показывают полный текст паттерна из backend-сообщения настроек (`N. <type>: <regex>`), а над списком добавлен заголовок секции `mail` для соответствия ожидаемой структуре в стиле Telegram.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.28`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.28` and `ANDROID_VERSION_CODE=377`; aligned prerelease links to `v8.50.28-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.28`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.28` и `ANDROID_VERSION_CODE=377`; prerelease-ссылки выровнены на `v8.50.28-develop`.

## [8.50.25] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Mail backups`, removed the redundant bottom `Close` button, kept header controls only, and suppressed duplicated raw backup list text so the backups are shown once.
- RU: В Android-приложении в `Оперативный центр → Бэкапы почты` убрана лишняя нижняя кнопка `Закрыть`, оставлены только контролы в заголовке, а также убрано дублирование «сырого» списка — бэкапы теперь отображаются один раз.

### Added / Добавлено
- EN: In Android app `Operational center → Mail backups`, updated the gear button in the dialog header to open mail backup pattern settings via extension settings (`settings_patterns_mail`) instead of backup history action.
- RU: В Android-приложении в `Оперативный центр → Бэкапы почты` в заголовок диалога обновлена кнопка-шестерёнка в заголовке диалога: теперь она открывает настройки паттернов бэкапов почты через меню настроек (`settings_patterns_mail`) вместо вызова действия истории бэкапов.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.25`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.25` and `ANDROID_VERSION_CODE=374`; aligned prerelease links to `v8.50.25-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.25`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.25` и `ANDROID_VERSION_CODE=374`; prerelease-ссылки выровнены на `v8.50.25-develop`.

## [8.50.23] - 2026-04-09

### Added / Добавлено
- EN: In Android app `Operational center`, tapping the `Mail` tile now opens a modal overlay window with the latest mail server backup history (status, size, path, and relative time).
- RU: В Android-приложении в `Оперативном центре` по тапу на плитку `Почта` теперь открывается модальное окно с историей бэкапов почтового сервера (статус, размер, путь и относительное время).

### Changed / Изменено
- EN: SemVer patch bump to `8.50.23`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.23` and `ANDROID_VERSION_CODE=372`; aligned prerelease links to `v8.50.23-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.23`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.23` и `ANDROID_VERSION_CODE=372`; prerelease-ссылки выровнены на `v8.50.23-develop`.

## [8.50.21] - 2026-04-09

### Added / Добавлено
- EN: In Android app `Operational center → DB tile → DB backups → DB backup patterns`, added an inline hint in the `Add pattern` dialog describing the recommended fill format: `category=database`, `type=subject`, and a meaningful DB backup subject fragment in the pattern field.
- RU: В Android-приложении в `Оперативный центр → плитка БД → Бэкапы БД → Паттерны бэкапов БД` добавлена подсказка в диалог `Добавить паттерн` с рекомендуемым форматом заполнения: `category=database`, `type=subject` и осмысленный фрагмент темы письма с бэкапом в поле паттерна.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.21`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.21` and `ANDROID_VERSION_CODE=370`; aligned prerelease links to `v8.50.21-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.21`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.21` и `ANDROID_VERSION_CODE=370`; prerelease-ссылки выровнены на `v8.50.21-develop`.

## [8.50.20] - 2026-04-09

### Added / Добавлено
- EN: In Android app `Operational center → DB backups`, added a gear button in the DB backups tile dialog to open a dedicated DB backup patterns modal overlay.
- RU: В Android-приложении в `Оперативный центр → Бэкапы БД` добавлена кнопка-шестерёнка в диалоге плитки БД для открытия отдельного модального окна с паттернами бэкапов БД.
- EN: In DB backup patterns modal overlay, added explicit controls in the header: `+` for adding a new pattern and `×` for closing the modal.
- RU: В модальном окне паттернов бэкапов БД в заголовок добавлены явные контролы: `+` для добавления нового паттерна и `×` для закрытия окна.
- EN: Added pattern action modal flow for DB backup patterns: tapping a pattern now opens an overlay with `Edit`/`Delete` choices.
- RU: Добавлен сценарий выбора действия для паттерна бэкапа БД: по тапу на паттерн открывается отдельное окно с выбором `Редактировать`/`Удалить`.

### Changed / Изменено
- EN: Reused Android pattern add/edit forms for DB category (`database`) and wired refresh routing to return back to DB patterns list after save/delete actions from DB backup tile flow.
- RU: Переиспользованы Android-формы добавления/редактирования паттернов для категории БД (`database`) и настроен корректный возврат в список паттернов БД после сохранения/удаления из потока плитки БД.
- EN: SemVer patch bump to `8.50.20`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.20` and `ANDROID_VERSION_CODE=369`; aligned prerelease links to `v8.50.20-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.20`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.20` и `ANDROID_VERSION_CODE=369`; prerelease-ссылки выровнены на `v8.50.20-develop`.

## [8.50.19] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Proxmox`, editing a Proxmox backup pattern now supports changing both fields in one dialog: pattern type and pattern value.
- RU: В Android-приложении в `Оперативный центр → Proxmox` редактирование паттерна бэкапа теперь позволяет менять сразу оба поля в одном окне: тип паттерна и значение паттерна.

### Changed / Изменено
- EN: Proxmox/DB/ZFS pattern edit menu labels now include both type and current pattern (`type — pattern`) to prefill Android edit dialog consistently.
- RU: В меню редактирования паттернов Proxmox/БД/ZFS в label теперь передаются и тип, и текущий паттерн (`тип — паттерн`) для корректного префилла Android-формы.
- EN: Backend action `settings_proxmox_pattern_edit_<id>` now accepts extended payload `|<new_type>|<new_pattern>` (legacy `|<new_pattern>` remains supported for compatibility).
- RU: Backend-действие `settings_proxmox_pattern_edit_<id>` теперь принимает расширенный payload `|<новый_тип>|<новый_паттерн>` (старый формат `|<новый_паттерн>` сохранён для совместимости).
- EN: SemVer patch bump to `8.50.19`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.19` and `ANDROID_VERSION_CODE=368`; aligned prerelease links to `v8.50.19-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.19`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.19` и `ANDROID_VERSION_CODE=368`; prerelease-ссылки выровнены на `v8.50.19-develop`.

## [8.50.18] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Proxmox`, fixed loading of Proxmox patterns from the backup tile gear button: `settings_patterns_proxmox` is no longer sent via control API and now correctly goes through extensions-settings API, so the patterns list is returned and rendered instead of staying on the loading state.
- RU: В Android-приложении в `Оперативный центр → Proxmox` исправлена загрузка паттернов по кнопке-шестерёнке в плитке бэкапов: `settings_patterns_proxmox` больше не отправляется через control API и теперь уходит в extensions-settings API, поэтому список паттернов приходит и отображается, а не зависает в состоянии загрузки.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.18`; synchronized project version mentions across runtime modules, config, docs, and Android artifacts; updated Android metadata to `ANDROID_VERSION_NAME=8.50.18` and `ANDROID_VERSION_CODE=367`; aligned prerelease links to `v8.50.18-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.18`; синхронизированы упоминания версии в runtime-модулях, конфиге, документации и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.18` и `ANDROID_VERSION_CODE=367`; prerelease-ссылки выровнены на `v8.50.18-develop`.

## [8.50.15] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Proxmox`, fixed Proxmox patterns loading in the tile dialog: action aliases are now normalized before request dispatch, and the UI accepts both `settings_patterns_proxmox` and `settings_backup_patterns` menu states.
- RU: В Android-приложении в `Оперативный центр → Proxmox` исправлена загрузка паттернов в диалоге плитки: перед отправкой запроса теперь нормализуются алиасы действий, а UI принимает оба состояния меню — `settings_patterns_proxmox` и `settings_backup_patterns`.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.15`; synchronized all current repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.15` and `ANDROID_VERSION_CODE=364`, and aligned prerelease links to `v8.50.15-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.15`; синхронизированы все актуальные упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.15` и `ANDROID_VERSION_CODE=364`, prerelease-ссылки выровнены на `v8.50.15-develop`.

## [8.50.13] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Proxmox`, fixed loading of the Proxmox patterns list: action `settings_patterns_proxmox` is now routed as a control menu action, so pattern options are returned and rendered in the dialog.
- RU: В Android-приложении в `Оперативный центр → Proxmox` исправлена загрузка списка паттернов: действие `settings_patterns_proxmox` теперь маршрутизируется как control-меню, поэтому список паттернов корректно приходит и отображается в диалоге.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.13`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.13` and `ANDROID_VERSION_CODE=362`, and aligned prerelease links to `v8.50.13-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.13`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.13` и `ANDROID_VERSION_CODE=362`, prerelease-ссылки выровнены на `v8.50.13-develop`.

## [8.50.12] - 2026-04-09

### Changed / Изменено
- EN: SemVer patch bump to `8.50.12`; synchronized all repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.12` and `ANDROID_VERSION_CODE=361`, and aligned prerelease links to `v8.50.12-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.12`; синхронизированы все упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.12` и `ANDROID_VERSION_CODE=361`, prerelease-ссылки выровнены на `v8.50.12-develop`.

## [8.50.11] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Proxmox`, the backups dialog now has a gear button that opens an overlay with Proxmox backup patterns; the patterns overlay includes close `×` and add `+` actions, and tapping a pattern opens an overlay with `edit`/`delete` choices.
- RU: В Android-приложении `Оперативный центр → Proxmox` в диалоге бэкапов добавлена шестерёнка для открытия наложенного окна со списком паттернов; в окне паттернов добавлены `×` для закрытия и `+` для добавления, а тап по паттерну открывает наложенное окно с выбором `редактировать`/`удалить`.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.11`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.11` and `ANDROID_VERSION_CODE=360`, and aligned prerelease links to `v8.50.11-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.11`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.11` и `ANDROID_VERSION_CODE=360`, prerelease-ссылки выровнены на `v8.50.11-develop`.

## [8.50.10] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center`, replaced the gear icon with a plus icon for add actions in: `Servers → targeted server availability checks`, `Proxmox → backups list`, `DB → backups list`, and `Resources → targeted server resource checks`.
- RU: В Android-приложении в `Оперативном центре` иконка-шестерёнка заменена на плюс для действий добавления в разделах: `Серверы → точечная проверка доступности`, `Proxmox → список бэкапов`, `БД → список бэкапов`, `Ресурсы → точечная проверка ресурсов серверов`.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.10`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.10` and `ANDROID_VERSION_CODE=359`, and aligned prerelease links to `v8.50.10-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.10`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.10` и `ANDROID_VERSION_CODE=359`, prerelease-ссылки выровнены на `v8.50.10-develop`.

## [8.50.9] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → DB`, in the DB backup list cards the category label `company database` is shortened to `company`.
- RU: В Android-приложении `Оперативный центр → БД` в карточках списка бэкапов БД отображение категории `company database` сокращено до `company`.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.9`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.9` and `ANDROID_VERSION_CODE=358`, and aligned prerelease links to `v8.50.9-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.9`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.9` и `ANDROID_VERSION_CODE=358`, prerelease-ссылки выровнены на `v8.50.9-develop`.

## [8.50.8] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Resources`, the per-server resources details dialog now has a close `×` icon in the header and no longer shows the bottom `Close` text button.
- RU: В Android-приложении `Оперативный центр → Ресурсы` в окне деталей ресурсов по серверу добавлен крестик `×` в заголовке, а нижняя текстовая кнопка `Закрыть` убрана.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.8`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.8` and `ANDROID_VERSION_CODE=357`, and aligned prerelease links to `v8.50.8-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.8`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.8` и `ANDROID_VERSION_CODE=357`, prerelease-ссылки выровнены на `v8.50.8-develop`.

## [8.50.7] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → Resources`, tapping a server card in the server list now opens an overlay dialog with per-server resource check details (loading state + result text) instead of keeping details only inside the list card.
- RU: В Android-приложении `Оперативный центр → Ресурсы` тап по карточке сервера в списке теперь открывает наложенное окно с деталями точечной проверки ресурсов (состояние загрузки + текст результата), а не оставляет детали только внутри карточки списка.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.7`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.7` and `ANDROID_VERSION_CODE=356`, and aligned prerelease links to `v8.50.7-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.7`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.7` и `ANDROID_VERSION_CODE=356`, prerelease-ссылки выровнены на `v8.50.7-develop`.

## [8.50.6] - 2026-04-09

### Fixed / Исправлено
- EN: Fixed a Kotlin compile error in Android `MainActivity` by explicitly grouping the `if` expression in the `messageSource` comparison condition for server dialog cards.
- RU: Исправлена ошибка компиляции Kotlin в Android `MainActivity`: в условии сравнения `messageSource` для карточек серверного диалога явно добавлена группировка `if`-выражения.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.6`; synchronized repository version mentions in code/docs, updated Android metadata to `ANDROID_VERSION_NAME=8.50.6` and `ANDROID_VERSION_CODE=355`, and aligned prerelease links to `v8.50.6-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.6`; синхронизированы упоминания версии в коде/документации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.6` и `ANDROID_VERSION_CODE=355`, prerelease-ссылки выровнены на `v8.50.6-develop`.

## [8.50.5] - 2026-04-09

- EN: SemVer patch bump to `8.50.5`; synchronized all runtime/config/docs/android version mentions after follow-up review, updated Android metadata to `ANDROID_VERSION_NAME=8.50.5` and `ANDROID_VERSION_CODE=354`, and aligned prerelease links to `v8.50.5-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.5`; после дополнительной проверки синхронизированы все упоминания версии в runtime/config/docs/android, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.5` и `ANDROID_VERSION_CODE=354`, prerelease-ссылки выровнены на `v8.50.5-develop`.

# Changelog / История изменений

All notable changes to this project are documented in this file.  
Все значимые изменения проекта фиксируются в этом файле.

The project follows Semantic Versioning (SemVer).  
Проект использует Semantic Versioning (SemVer).

## [8.50.4] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center`, tapping the `resources` tile now opens the same server list dialog as long-press on the `servers` tile.
- RU: В Android-приложении в `Оперативном центре` тап по плашке `ресурсы` теперь открывает тот же диалог со списком серверов, что и долгий тап по плашке `серверы`.
- EN: In Android app server selection dialog, `resources` mode now performs per-server resource checks instead of availability checks.
- RU: В Android-приложении в диалоге выбора серверов режим `ресурсы` теперь выполняет точечную проверку ресурсов сервера вместо проверки доступности.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.4`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.50.4` and `ANDROID_VERSION_CODE=353`, prerelease links aligned to `v8.50.4-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.4`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.4` и `ANDROID_VERSION_CODE=353`, prerelease-ссылки выровнены на `v8.50.4-develop`.

## [8.50.3] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center`, extension tiles are now shown only for enabled extensions.
- RU: В Android-приложении `Оперативный центр` плашки расширений теперь отображаются только для включённых расширений.
- EN: In Android app `Operational center → Tile settings`, extension tiles list now includes only enabled extensions.
- RU: В Android-приложении `Оперативный центр → Настройка плашек` список плашек расширений теперь включает только включённые расширения.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.3`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.50.3` and `ANDROID_VERSION_CODE=352`, prerelease links aligned to `v8.50.3-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.3`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.3` и `ANDROID_VERSION_CODE=352`, prerelease-ссылки выровнены на `v8.50.3-develop`.

## [8.50.2] - 2026-04-09

### Fixed / Исправлено
- EN: In Telegram bot `Main menu → DB backups`, removed the `↩️ Back` button from the databases backup screen.
- RU: В Telegram-боте в `Главное меню → Бэкапы БД` удалена кнопка `↩️ Назад` с экрана бэкапов баз данных.
- EN: In Telegram bot `Main menu → Proxmox backups`, removed the `↩️ Back` button from the host list screen.
- RU: В Telegram-боте в `Главное меню → Бэкапы Proxmox` удалена кнопка `↩️ Назад` с экрана списка хостов.
- EN: In Telegram bot `Main menu → Mail backups`, removed the `🔄 Refresh` button from the mail backups screen (including empty-state screen).
- RU: В Telegram-боте в `Главное меню → Бэкапы почты` удалена кнопка `🔄 Обновить` с экрана почтовых бэкапов (включая экран без данных).
- EN: In Telegram bot `Main menu → ZFS`, removed the `↩️ Back` button from the ZFS hosts list screen.
- RU: В Telegram-боте в `Главное меню → ZFS` удалена кнопка `↩️ Назад` с экрана списка ZFS-хостов.
- EN: In Telegram bot `Main menu → Server availability` and `Main menu → Server resources`, removed `🔄 Refresh list` and `🔍 Search server` buttons from server selection menus.
- RU: В Telegram-боте в `Главное меню → Доступность сервера` и `Главное меню → Ресурсы сервера` удалены кнопки `🔄 Обновить список` и `🔍 Поиск сервера` из меню выбора серверов.

### Changed / Изменено
- EN: SemVer patch bump to `8.50.2`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.50.2` and `ANDROID_VERSION_CODE=351`, prerelease links aligned to `v8.50.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.50.2`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.50.2` и `ANDROID_VERSION_CODE=351`, prerelease-ссылки выровнены на `v8.50.2-develop`.
## [8.49.0] - 2026-04-09

### Added / Добавлено
- EN: In Telegram bot `Main menu → Mail backups`, added a dedicated `⚙️ Mail patterns settings` button that opens a full patterns management menu with actions to edit existing patterns, delete existing patterns, and add a new pattern.
- RU: В Telegram-боте в `Главное меню → Бэкапы почты` добавлена отдельная кнопка `⚙️ Настройка паттернов почты`, открывающая полноценное меню управления паттернами с действиями редактирования существующих паттернов, удаления существующих паттернов и добавления нового паттерна.

### Changed / Изменено
- EN: SemVer minor bump to `8.49.0`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.49.0` and `ANDROID_VERSION_CODE=348`, prerelease links aligned to `v8.49.0-develop`.
- RU: Выполнен SemVer minor-бамп до `8.49.0`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.49.0` и `ANDROID_VERSION_CODE=348`, prerelease-ссылки выровнены на `v8.49.0-develop`.

## [8.48.31] - 2026-04-09

### Added / Добавлено
- EN: In Android app `Operational center → Servers` (list opened by long tap), availability markers were added to server cards: `🟢` for `UP`, `🔴` for unavailable statuses (`DOWN/UNREACHABLE/OFFLINE/ERROR/CRITICAL`), and `⚪` for unknown status.
- RU: В Android-приложении `Оперативный центр → Серверы` (список по долгому тапу) добавлены маркеры доступности на карточки серверов: `🟢` для `UP`, `🔴` для недоступных статусов (`DOWN/UNREACHABLE/OFFLINE/ERROR/CRITICAL`) и `⚪` для неизвестного статуса.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.31`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.31` and `ANDROID_VERSION_CODE=347`, prerelease links aligned to `v8.48.31-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.31`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.31` и `ANDROID_VERSION_CODE=347`, prerelease-ссылки выровнены на `v8.48.31-develop`.

## [8.48.30] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center`, DB and Proxmox tiles now switch value text color to error only when there are actual issues among entities enabled for monitoring; opening tile details no longer turns tile text red by itself.
- RU: В Android-приложении `Оперативный центр` плашки БД и Proxmox теперь окрашивают текст значения в цвет ошибки только при реальных проблемах среди сущностей, включённых в мониторинг; простое открытие деталей по тапу больше не краснит текст само по себе.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.30`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.30` and `ANDROID_VERSION_CODE=346`, prerelease links aligned to `v8.48.30-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.30`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.30` и `ANDROID_VERSION_CODE=346`, prerelease-ссылки выровнены на `v8.48.30-develop`.

## [8.48.29] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → DB tile`, removed the `Category:` prefix on DB backup cards and left only the category name in card text.
- RU: В Android-приложении `Оперативный центр → плашка БД` в карточках списка бэкапов убран префикс `Категория:`, теперь отображается только название категории.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.29`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.29` and `ANDROID_VERSION_CODE=345`, prerelease links aligned to `v8.48.29-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.29`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.29` и `ANDROID_VERSION_CODE=345`, prerelease-ссылки выровнены на `v8.48.29-develop`.

## [8.48.28] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → DB tile`, the long-press DB actions dialog now keeps a visible close (`✕`) button even for long DB names by constraining the title text and preserving header layout.
- RU: В Android-приложении `Оперативный центр → плашка БД` в диалоге действий по долгому тапу теперь стабильно виден крестик закрытия (`✕`) даже при длинных именах БД за счёт ограничения заголовка и фиксации layout шапки.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.28`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.28` and `ANDROID_VERSION_CODE=344`, prerelease links aligned to `v8.48.28-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.28`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.28` и `ANDROID_VERSION_CODE=344`, prerelease-ссылки выровнены на `v8.48.28-develop`.

## [8.48.26] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → DB tile`, fixed DB backup cards that could show only monitor marker (`🟢/⚪`) without DB name; when label content is empty after sanitization, UI now restores DB name from `db_detail_*` action payload.
- RU: В Android-приложении `Оперативный центр → плашка БД` исправлены карточки бэкапов, где мог отображаться только маркер мониторинга (`🟢/⚪`) без имени БД; если после очистки label пустой, UI теперь восстанавливает имя базы из payload action `db_detail_*`.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.26`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.26` and `ANDROID_VERSION_CODE=342`, prerelease links aligned to `v8.48.26-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.26`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.26` и `ANDROID_VERSION_CODE=342`, prerelease-ссылки выровнены на `v8.48.26-develop`.

## [8.48.25] - 2026-04-09

### Fixed / Исправлено
- EN: In Android app `Operational center → DB tile`, restored DB names on cards in the DB backups list: when backend menu options come without `label`, UI now falls back to the DB key extracted from `db_detail_*` action.
- RU: В Android-приложении `Оперативный центр → плашка БД` возвращены имена баз на карточках в списке бэкапов БД: если backend присылает пункт меню без `label`, UI теперь подставляет имя из ключа БД, извлечённого из action `db_detail_*`.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.25`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.25` and `ANDROID_VERSION_CODE=341`, prerelease links aligned to `v8.48.25-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.25`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.25` и `ANDROID_VERSION_CODE=341`, prerelease-ссылки выровнены на `v8.48.25-develop`.

## [8.48.24] - 2026-04-09

### Fixed / Исправлено
- EN: In `Main menu → Proxmox backups → Pattern settings`, the `Back` button now returns to the Proxmox backups hosts list instead of an empty intermediate menu.
- RU: В `Главное меню → Бэкапы Proxmox → Настройки паттернов` кнопка `Назад` теперь возвращает к списку хостов/бэкапов Proxmox, а не в пустое промежуточное меню.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.24`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.24` and `ANDROID_VERSION_CODE=340`, prerelease links aligned to `v8.48.24-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.24`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.24` и `ANDROID_VERSION_CODE=340`, prerelease-ссылки выровнены на `v8.48.24-develop`.

## [8.48.22] - 2026-04-08

### Changed / Изменено
- EN: In `Main menu → DB backups → Manage categories`, replaced the action-only submenu with a direct category list where each row has edit (`✏️`) and delete (`🗑️`) actions, and kept a separate `Add category` button.
- RU: В `Главное меню → Бэкапы БД → Управление категориями` подменю действий заменено на прямой список категорий, где у каждой строки есть действия редактирования (`✏️`) и удаления (`🗑️`), при этом отдельная кнопка `Добавить категорию` сохранена.
- EN: In category management opened from `DB backups`, `Back` now returns to `DB backups` instead of intermediate settings screens.
- RU: В управлении категориями, открытом из `Бэкапы БД`, кнопка `Назад` теперь возвращает в `Бэкапы БД`, а не в промежуточные экраны настроек.
- EN: SemVer patch bump to `8.48.22`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.22` and `ANDROID_VERSION_CODE=338`, prerelease links aligned to `v8.48.22-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.22`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.22` и `ANDROID_VERSION_CODE=338`, prerelease-ссылки выровнены на `v8.48.22-develop`.

## [8.48.21] - 2026-04-08

### Fixed / Исправлено
- EN: In `Main menu → DB backups`, restored the `Manage categories` button in the operational DB backups screen.
- RU: В `Главное меню → Бэкапы БД` возвращена кнопка `Управление категориями` в операционный экран бэкапов БД.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.21`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.21` and `ANDROID_VERSION_CODE=337`, prerelease links aligned to `v8.48.21-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.21`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.21` и `ANDROID_VERSION_CODE=337`, prerelease-ссылки выровнены на `v8.48.21-develop`.

## [8.48.19] - 2026-04-08

### Fixed / Исправлено
- EN: In `Main menu → DB backups → Manage databases → Manage categories`, fixed the `Back` button flow to consistently return to `Manage databases`.
- RU: В `Главное меню → Бэкапы БД → Управление базами → Управление категориями` исправлен сценарий кнопки `Назад`: теперь она стабильно возвращает в меню `Управление базами`.

### Changed / Изменено
- EN: In `Main menu → DB backups`, compacted the database list layout: DB buttons are now rendered in two columns inside each type block.
- RU: В `Главное меню → Бэкапы БД` список баз сделан компактнее: кнопки БД теперь выводятся в две колонки внутри каждого блока типа.
- EN: SemVer patch bump to `8.48.19`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.19` and `ANDROID_VERSION_CODE=335`, prerelease links aligned to `v8.48.19-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.19`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.19` и `ANDROID_VERSION_CODE=335`, prerelease-ссылки выровнены на `v8.48.19-develop`.

## [8.48.18] - 2026-04-08

### Fixed / Исправлено
- EN: In `Main menu → DB backups → Manage databases`, fixed a `NameError` when opening a category (`_build_db_toggle_monitor_callback` was undefined) by using the correct callback builder for DB monitoring toggles.
- RU: В `Главное меню → Бэкапы БД → Управление базами` исправлен `NameError` при открытии категории (`_build_db_toggle_monitor_callback` не был определён): использован корректный builder callback для переключателей мониторинга БД.
- EN: In `Main menu → DB backups → Manage databases → Manage categories`, adjusted `Back` navigation in category-management flow to return to `Manage databases`.
- RU: В `Главное меню → Бэкапы БД → Управление базами → Управление категориями` скорректирована навигация `Назад` в потоке управления категориями: возврат ведёт в `Управление базами`.

### Changed / Изменено
- EN: In `Main menu → DB backups`, made category quick-access list more compact by rendering category buttons in two columns.
- RU: В `Главное меню → Бэкапы БД` список категорий сделан компактнее: кнопки категорий выводятся в две колонки.
- EN: In `Main menu → DB backups → Manage databases`, restored per-database monitoring toggle buttons (`✅ Вкл` / `⛔ Выкл`) after selecting a category.
- RU: В `Главное меню → Бэкапы БД → Управление базами` после выбора категории возвращены кнопки включения/выключения мониторинга БД (`✅ Вкл` / `⛔ Выкл`).
- EN: SemVer patch bump to `8.48.18`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.18` and `ANDROID_VERSION_CODE=334`, prerelease links aligned to `v8.48.18-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.18`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.18` и `ANDROID_VERSION_CODE=334`, prerelease-ссылки выровнены на `v8.48.18-develop`.

## [8.48.17] - 2026-04-08

### Changed / Изменено
- EN: In `Main menu → DB backups`, removed per-DB monitoring toggle buttons (`enable/disable`) from the operational DB list and DB details screen.
- RU: В `Главное меню → Бэкапы БД` убраны кнопки включения/выключения мониторинга конкретных БД в операционном списке и в экране деталей БД.
- EN: In `Main menu → DB backups → Manage databases`, returned per-DB monitoring toggle controls (`✅ Вкл` / `⛔ Выкл`) in category details alongside edit/delete actions.
- RU: В `Главное меню → Бэкапы БД → Управление базами` возвращены кнопки включения/выключения мониторинга (`✅ Вкл` / `⛔ Выкл`) в деталях категории рядом с действиями редактирования/удаления.
- EN: In `Main menu → DB backups → Manage databases → Manage categories`, fixed the `Back` button so it now returns to `Manage databases`.
- RU: В `Главное меню → Бэкапы БД → Управление базами → Управление категориями` исправлена кнопка `Назад`: теперь она возвращает в меню `Управление базами`.
- EN: SemVer patch bump to `8.48.17`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.17` and `ANDROID_VERSION_CODE=333`, prerelease links aligned to `v8.48.17-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.17`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.17` и `ANDROID_VERSION_CODE=333`, prerelease-ссылки выровнены на `v8.48.17-develop`.

## [8.48.14] - 2026-04-08

### Fixed / Исправлено
- EN: In `Main menu → DB backups → Manage databases`, fixed `Back` navigation to return to `DB backups`.
- RU: В `Главное меню → Бэкапы БД → Управление базами` исправлена кнопка `Назад`: теперь она возвращает в меню `Бэкапы БД`.

### Added / Добавлено
- EN: In `Main menu → DB backups`, added a dedicated `Manage DB categories` entry that opens category management tools (add/edit/delete/view).
- RU: В `Главное меню → Бэкапы БД` добавлен отдельный пункт `Управление категориями баз`, который открывает инструменты управления категориями (добавление/редактирование/удаление/просмотр).

### Changed / Изменено
- EN: In `Settings → Extensions`, removed the `DB backups` button from the extensions list.
- RU: В `Настройки → Расширения` удалена кнопка `Бэкапы БД` из списка расширений.
- EN: SemVer patch bump to `8.48.14`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.14` and `ANDROID_VERSION_CODE=331`, prerelease links aligned to `v8.48.14-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.14`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.14` и `ANDROID_VERSION_CODE=331`, prerelease-ссылки выровнены на `v8.48.14-develop`.

## [8.48.13] - 2026-04-08

### Fixed / Исправлено
- EN: In `Main menu → DB backups → Manage databases`, fixed `Back` navigation to return to `DB backups` instead of looping in DB management screens.
- RU: В `Главное меню → Бэкапы БД → Управление базами` исправлена навигация кнопки `Назад`: теперь она возвращает в меню `Бэкапы БД`, а не зацикливает экран управления.
- EN: In DB category view opened from `Manage databases`, fixed `Back` to return to `Manage databases` category list.
- RU: В экране категории БД, открытом из `Управление базами`, кнопка `Назад` теперь корректно возвращает к списку категорий в `Управление базами`.
- EN: After enabling/disabling DB monitoring inside a category, replaced `To DB list` with `Back` that returns directly to the same category menu.
- RU: После включения/выключения мониторинга БД внутри категории убрана кнопка `К списку баз`; вместо неё добавлена `Назад`, возвращающая прямо в меню текущей категории.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.13`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.13` and `ANDROID_VERSION_CODE=330`, prerelease links aligned to `v8.48.13-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.13`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.13` и `ANDROID_VERSION_CODE=330`, prerelease-ссылки выровнены на `v8.48.13-develop`.

## [8.48.12] - 2026-04-08

### Fixed / Исправлено
- EN: Fixed `Button_data_invalid` in `Main menu → DB backups → Manage databases` for non-Latin category names (e.g. `филиалы`): DB category, DB-entry and monitoring-toggle callbacks now use short tokenized callback IDs with safe reverse mapping.
- RU: Исправлен `Button_data_invalid` в `Главное меню → Бэкапы БД → Управление базами` для не-латинских категорий (например, `филиалы`): callback для категорий, действий по БД и переключателя мониторинга переведены на короткие токенизированные идентификаторы с безопасным обратным маппингом.
- EN: In `Main menu → Proxmox backups`, removed the `Show problematic` button from the hosts list as requested.
- RU: В `Главное меню → Бэкапы Proxmox` убрана кнопка `Показать проблемные` из списка хостов по запросу.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.12`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.12` and `ANDROID_VERSION_CODE=329`, prerelease links aligned to `v8.48.12-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.12`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.12` и `ANDROID_VERSION_CODE=329`, prerelease-ссылки выровнены на `v8.48.12-develop`.

## [8.48.9] - 2026-04-08

### Fixed / Исправлено
- EN: In Telegram path `Main menu → DB backups → Manage databases`, reduced inline keyboard payload: the screen now shows compact category actions instead of rendering per-DB CRUD/toggle buttons in one response, preventing Telegram `BadRequest: Reply markup is too long` on large DB configs.
- RU: В Telegram-сценарии `Главное меню → Бэкапы БД → Управление базами` уменьшен объём inline-клавиатуры: экран теперь показывает компактные действия по категориям вместо отрисовки всех CRUD/переключателей по каждой БД в одном ответе, что устраняет Telegram `BadRequest: Reply markup is too long` при большом конфиге БД.
- EN: Added category list capping (`20` items) with explicit fallback hint to use `View all DBs`, so the menu remains stable even with very large configuration trees.
- RU: Добавлено ограничение списка категорий (`20` элементов) с явной подсказкой использовать `Просмотр всех БД`, чтобы меню оставалось стабильным даже при очень большом дереве конфигурации.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.9`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.9` and `ANDROID_VERSION_CODE=326`, prerelease links aligned to `v8.48.9-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.9`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.9` и `ANDROID_VERSION_CODE=326`, prerelease-ссылки выровнены на `v8.48.9-develop`.
## [8.48.3] - 2026-04-08

### Fixed / Исправлено
- EN: In Telegram path `Main menu → DB backups`, long inline keyboards are now split into pages (`20` databases per page) and include page navigation, preventing Telegram `BadRequest: Reply markup is too long` on large DB lists.
- RU: В Telegram-сценарии `Главное меню → Бэкапы БД` длинная inline-клавиатура теперь разбивается на страницы (`20` баз на страницу) с навигацией, что устраняет ошибку Telegram `BadRequest: Reply markup is too long` при большом списке БД.
- EN: In Telegram path `Main menu → Proxmox backups`, the button now opens the Proxmox hosts list again (`backup_hosts`), restoring direct visibility of monitored hosts and their statuses.
- RU: В Telegram-сценарии `Главное меню → Бэкапы Proxmox` кнопка снова открывает список хостов Proxmox (`backup_hosts`), возвращая прямой просмотр хостов и их статусов.
- EN: In Telegram path `Main menu → DB backups`, navigation actions were clarified: the screen now explicitly keeps `Add new DB`, `Back`, and `Close` controls in the backups menu layout.
- RU: В Telegram-сценарии `Главное меню → Бэкапы БД` уточнена навигация: в раскладке меню явно сохранены кнопки `Добавить новую БД`, `Назад` и `Закрыть`.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.3`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.3` and `ANDROID_VERSION_CODE=320`, prerelease links aligned to `v8.48.3-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.3`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.3` и `ANDROID_VERSION_CODE=320`, prerelease-ссылки выровнены на `v8.48.3-develop`.

## [8.48.1] - 2026-04-08

### Fixed / Исправлено
- EN: Android `Operations Center → DB` tile now builds the database list from the same settings-DB configuration source as Telegram `DB Backups`, with identical enabled/disabled flags and status calculation, so the visible DB set and health state stay synchronized.
- RU: Android `Оперативный центр → плашка БД` теперь строит список баз из того же источника конфигурации settings DB, что и Telegram `Бэкапы БД`, с одинаковыми флагами включения/выключения и расчётом статусов, поэтому видимый набор БД и их состояние синхронизированы.
- EN: `backup_databases` API action for mobile now uses the unified DB snapshot used by Telegram handlers; menu labels and summary counters are aligned with the bot.
- RU: API-действие `backup_databases` для мобильного клиента теперь использует единый snapshot БД из Telegram-обработчиков; подписи списка и сводные счётчики выровнены с ботом.

### Changed / Изменено
- EN: SemVer patch bump to `8.48.1`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.1` and `ANDROID_VERSION_CODE=318`, prerelease links aligned to `v8.48.1-develop`.
- RU: Выполнен SemVer patch-бамп до `8.48.1`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.1` и `ANDROID_VERSION_CODE=318`, prerelease-ссылки выровнены на `v8.48.1-develop`.

## [8.48.0] - 2026-04-08

### Added / Добавлено
- EN: In Telegram path `Main menu → DB backups`, added a direct `Add new DB` button in the DB backups list screen to quickly jump into DB configuration/edit flow.
- RU: В Telegram-сценарии `Главное меню → Бэкапы БД` на экране списка бэкапов добавлена отдельная кнопка `Добавить новую БД` для быстрого перехода в сценарий добавления/редактирования БД.
- EN: In the same DB backups list, each configured DB now has dedicated `Edit` and `Delete` action buttons, so management can be done directly from the operational list.
- RU: В том же списке бэкапов БД для каждой настроенной базы добавлены отдельные кнопки `Изменить` и `Удалить`, чтобы управлять БД прямо из операционного списка.

### Fixed / Исправлено
- EN: In Telegram path `Main menu → Proxmox backups → Pattern settings → Edit patterns`, the `Back` button now returns to the `Proxmox backups` menu screen instead of switching to the hosts list.
- RU: В Telegram-сценарии `Главное меню → Бэкапы Proxmox → Настройка паттернов → Редактировать паттерны` кнопка `Назад` теперь возвращает в меню `Бэкапы Proxmox`, а не переводит в список хостов.

### Changed / Изменено
- EN: SemVer minor bump to `8.48.0`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.48.0` and `ANDROID_VERSION_CODE=317`, prerelease links aligned to `v8.48.0-develop`.
- RU: Выполнен SemVer minor-бамп до `8.48.0`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.48.0` и `ANDROID_VERSION_CODE=317`, prerelease-ссылки выровнены на `v8.48.0-develop`.

## [8.46.2] - 2026-04-08

### Fixed / Исправлено
- EN: In Telegram path `Main menu → Proxmox backups`, the `Pattern settings` button now opens Proxmox pattern editing immediately (`settings_patterns_proxmox`) without the intermediate submenu.
- RU: В Telegram-сценарии `Главное меню → Бэкапы Proxmox` кнопка `Настройка паттернов` теперь сразу открывает редактирование паттернов (`settings_patterns_proxmox`) без промежуточного подменю.
- EN: In Proxmox patterns editing opened from backups flow, the `Back` button now returns to `Proxmox backups` (`backup_proxmox`) instead of the settings extensions screen.
- RU: В редактировании паттернов Proxmox, открытом из сценария бэкапов, кнопка `Назад` теперь возвращает в `Бэкапы Proxmox` (`backup_proxmox`), а не в экран расширений настроек.
- EN: In Telegram path `Settings → Extensions`, the `Proxmox backups` section button was removed from the extensions list.
- RU: В Telegram-сценарии `Настройки → Расширения` кнопка раздела `Бэкапы Proxmox` удалена из списка расширений.

### Changed / Изменено
- EN: SemVer patch bump to `8.46.2`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.46.2` and `ANDROID_VERSION_CODE=316`, prerelease links aligned to `v8.46.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.46.2`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.46.2` и `ANDROID_VERSION_CODE=316`, prerelease-ссылки выровнены на `v8.46.2-develop`.

## [8.46.1] - 2026-04-08

### Fixed / Исправлено
- EN: In Android `Operations center → DB tile`, the DB list now uses the same enabled/disabled monitoring source as the Telegram bot, so statuses are shown consistently between Telegram and Android.
- RU: В Android `Оперативный центр → плашка БД` список баз теперь использует тот же источник статусов включения/выключения мониторинга, что и Telegram-бот, поэтому статусы синхронизированы между Telegram и Android.
- EN: `settings_db_toggle_monitor_*` now updates DB-monitoring state through the same backup-monitor toggle path used by Telegram handlers; the updated state is persisted in the settings database and read from there for next renders.
- RU: `settings_db_toggle_monitor_*` теперь обновляет состояние мониторинга через тот же toggle-путь backup-монитора, что и Telegram-обработчики; обновлённое состояние сохраняется в базе настроек и затем читается оттуда при следующих отрисовках.

### Changed / Изменено
- EN: SemVer patch bump to `8.46.1`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.46.1` and `ANDROID_VERSION_CODE=315`, prerelease links aligned to `v8.46.1-develop`.
- RU: Выполнен SemVer patch-бамп до `8.46.1`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.46.1` и `ANDROID_VERSION_CODE=315`, prerelease-ссылки выровнены на `v8.46.1-develop`.

## [8.45.3] - 2026-04-08

### Fixed / Исправлено
- EN: In Telegram path `Main menu → Proxmox backups`, the main button now opens the dedicated Proxmox backups submenu (`backup_proxmox`) instead of jumping directly to hosts, so the `Pattern settings` screen with actions to edit/delete existing patterns and add a new pattern is always reachable from this flow.
- RU: В Telegram-сценарии `Главное меню → Бэкапы Proxmox` главная кнопка теперь открывает отдельное подменю Proxmox-бэкапов (`backup_proxmox`), а не сразу список хостов; из этого потока стабильно доступен экран `Настройка паттернов` с действиями редактирования/удаления существующих паттернов и добавления нового паттерна.

### Changed / Изменено
- EN: SemVer patch bump to `8.45.3`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.45.3` and `ANDROID_VERSION_CODE=313`, prerelease links aligned to `v8.45.3-develop`.
- RU: Выполнен SemVer patch-бамп до `8.45.3`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.45.3` и `ANDROID_VERSION_CODE=313`, prerelease-ссылки выровнены на `v8.45.3-develop`.

## [8.45.2] - 2026-04-08

### Added / Добавлено
- EN: In Android `Operations Center → DB` tile, each database item in the DB backups list now explicitly shows Telegram-bot monitoring state (`🟢 Monitoring on` / `⚪ Monitoring off`) so enabled/disabled status is visible immediately.
- RU: В Android `Оперативный центр → плашка БД` в списке бэкапов БД для каждой базы теперь явно отображается состояние мониторинга из Telegram-бота (`🟢 Мониторинг вкл` / `⚪ Мониторинг выкл`), чтобы статус включения/выключения был виден сразу.

### Changed / Изменено
- EN: SemVer patch bump to `8.45.2`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.45.2` and `ANDROID_VERSION_CODE=312`, prerelease links aligned to `v8.45.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.45.2`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.45.2` и `ANDROID_VERSION_CODE=312`, prerelease-ссылки выровнены на `v8.45.2-develop`.

## [8.45.0] - 2026-04-08

### Added / Добавлено
- EN: In Telegram path `Main menu → Proxmox backups`, added a dedicated `Pattern settings` button that opens a single menu with actions to edit, delete, and add a new Proxmox backup pattern.
- RU: В Telegram-сценарии `Главное меню → Бэкапы Proxmox` добавлена отдельная кнопка `Настройка паттернов`, открывающая единое меню с действиями редактирования, удаления и добавления нового паттерна бэкапов Proxmox.

### Changed / Изменено
- EN: SemVer minor bump to `8.45.0`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.45.0` and `ANDROID_VERSION_CODE=310`, prerelease links aligned to `v8.45.0-develop`.
- RU: Выполнен SemVer minor-бамп до `8.45.0`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.45.0` и `ANDROID_VERSION_CODE=310`, prerelease-ссылки выровнены на `v8.45.0-develop`.

## [8.44.1] - 2026-04-08

### Added / Добавлено
- EN: In Telegram path `Backup Proxmox → Hosts`, added host management mode with actions to add a new host, rename an existing host, activate/deactivate monitoring, and delete a host directly from the backup menu.
- RU: В Telegram-сценарии `Бэкапы Proxmox → По хостам` добавлен режим управления хостами: можно добавить новый хост, переименовать существующий, активировать/деактивировать мониторинг и удалить хост прямо из меню бэкапов.
- EN: In Telegram path `Settings → Extensions → Proxmox Backups`, the main Proxmox menu now has direct pattern actions: open edit/delete list and start adding a new Proxmox backup pattern.
- RU: В Telegram-сценарии `Настройки → Расширения → Бэкапы Proxmox` в основном меню добавлены прямые действия с паттернами: переход к списку редактирования/удаления и запуск добавления нового паттерна Proxmox.

### Fixed / Исправлено
- EN: In Telegram path `Settings → Extensions → DB Backups → Databases`, added consistent navigation buttons `Back`, `Home`, and `Close` in the “Databases” sub-screens where only back navigation was available before.
- RU: В Telegram-сценарии `Настройки → Расширения → Бэкапы БД → Базы` добавлены единообразные кнопки навигации `Назад`, `На главную` и `Закрыть` в подпунктах, где раньше был только возврат назад.
- EN: Proxmox backup host listing no longer hides hosts present in backup history when enabled hosts are configured; DB-discovered hosts are now merged into the visible list.
- RU: Список хостов Proxmox больше не скрывает хосты из истории бэкапов при наличии включённых хостов в конфиге; хосты из БД теперь объединяются с конфигурационным списком.
- EN: Proxmox mail parser now resolves host aliases against `PROXMOX_HOSTS` (including `sr-` prefixed hosts like `sr-pve*` / `sr-bup*`), which fixes missing host association for subjects like `vzdump backup status (pve3.geltd.local)` and future `bup2` (`sr-bup2`) notifications.
- RU: Парсер Proxmox-писем теперь сопоставляет алиасы хостов с `PROXMOX_HOSTS` (включая префикс `sr-` для `sr-pve*` / `sr-bup*`), что исправляет пропуски привязки хоста для тем вида `vzdump backup status (pve3.geltd.local)` и учитывает будущие уведомления `bup2` (`sr-bup2`).

### Changed / Изменено
- EN: SemVer patch bump to `8.44.1`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.44.1` and `ANDROID_VERSION_CODE=308`, prerelease links aligned to `v8.44.1-develop`.
- RU: Выполнен SemVer patch-бамп до `8.44.1`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.44.1` и `ANDROID_VERSION_CODE=308`, prerelease-ссылки выровнены на `v8.44.1-develop`.

## [8.42.4] - 2026-04-08

### Fixed / Исправлено
- EN: In Telegram path `Settings → Extensions → DB Backups → Databases`, added explicit per-database monitoring toggle buttons in the full DB list (`📋 Просмотр всех БД`) so each base can be enabled/disabled directly from this screen.
- RU: В Telegram-сценарии `Настройки → Расширения → Бэкапы БД → Базы` добавлены явные кнопки включения/выключения мониторинга для каждой базы в полном списке (`📋 Просмотр всех БД`), чтобы переключать мониторинг сразу на этом экране.
- EN: In DB backup settings screens, navigation now consistently includes `Back`, `Home`, and `Close` actions (including the main DB settings list and full DB view).
- RU: В экранах настроек бэкапов БД навигация теперь везде содержит `Назад`, `На главную` и `Закрыть` (включая основной список БД и полный просмотр баз).

### Changed / Изменено
- EN: SemVer patch bump to `8.42.4`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.42.4` and `ANDROID_VERSION_CODE=305`, prerelease links aligned to `v8.42.4-develop`.
- RU: Выполнен SemVer patch-бамп до `8.42.4`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.42.4` и `ANDROID_VERSION_CODE=305`, prerelease-ссылки выровнены на `v8.42.4-develop`.

## [8.42.2] - 2026-04-07

### Fixed / Исправлено
- EN: In Telegram path `Settings → Extensions → DB Backups → Databases`, DB monitoring toggle callbacks were shortened to stay within Telegram callback-data limits and prevent `Button_data_invalid` errors.
- RU: В Telegram-сценарии `Настройки → Расширения → Бэкапы БД → Базы` callback-данные переключателей мониторинга БД укорочены под лимиты Telegram, из-за чего устранена ошибка `Button_data_invalid`.

### Changed / Изменено
- EN: SemVer patch bump to `8.42.2`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.42.2` and `ANDROID_VERSION_CODE=303`, prerelease links aligned to `v8.42.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.42.2`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.42.2` и `ANDROID_VERSION_CODE=303`, prerelease-ссылки выровнены на `v8.42.2-develop`.

## [8.42.0] - 2026-04-07

### Added / Добавлено
- EN: In Telegram path `Settings → Extensions → DB Backups → Databases`, added per-database monitoring toggle: from DB details you can now disable/enable a specific DB directly, with state persisted in `DATABASE_MONITORING_DISABLED`.
- RU: В Telegram-сценарии `Настройки → Расширения → Бэкапы БД → Базы` добавлено переключение мониторинга по каждой базе: в деталях БД теперь можно сразу отключить/включить конкретную базу, состояние сохраняется в `DATABASE_MONITORING_DISABLED`.

### Changed / Изменено
- EN: DB backups list in Telegram now marks disabled DBs with `⚪`, and excluded DBs are skipped in “problem databases” and DB summary calculations.
- RU: В списке бэкапов БД Telegram отключённые базы теперь помечаются `⚪`, а исключённые базы не участвуют в расчётах «проблемных баз» и сводки БД.
- EN: SemVer minor bump to `8.42.0`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.42.0` and `ANDROID_VERSION_CODE=301`, with prerelease links aligned to `v8.42.0-develop`.
- RU: Выполнен SemVer minor-бамп до `8.42.0`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.42.0` и `ANDROID_VERSION_CODE=301`, prerelease-ссылки выровнены на `v8.42.0-develop`.

## [8.41.58] - 2026-04-07

### Fixed / Исправлено
- EN: Android Ops Center `proxmox` tile now calculates backup summary only for hosts that are enabled in monitoring; disabled hosts are excluded from ratio and problem state.
- RU: Плашка `proxmox` в Android «Оперативном центре» теперь считает сводку бэкапов только по хостам, включённым в мониторинге; отключённые хосты исключаются из соотношения и статуса проблем.

### Changed / Изменено
- EN: SemVer patch bump to `8.41.58`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.41.58` and `ANDROID_VERSION_CODE=300`, with prerelease links aligned to `v8.41.58-develop`.
- RU: Выполнен SemVer patch-бамп до `8.41.58`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.41.58` и `ANDROID_VERSION_CODE=300`, prerelease-ссылки выровнены на `v8.41.58-develop`.

## [8.41.56] - 2026-04-07

### Fixed / Исправлено
- EN: Android Ops Center DB backup list now correctly sends DB action payloads (`edit/toggle/delete`) with URL-encoded category/key, so enabling/disabling DB monitoring works for names with special characters.
- RU: В списке бэкапов БД Android Ops Center теперь корректно отправляются payload действий (`edit/toggle/delete`) с URL-encoding категории/ключа, поэтому включение/выключение мониторинга БД работает и для имен со спецсимволами.
- EN: In the DB backups dialog, tapping the gear now opens a dedicated “Add DB” dialog directly in Ops Center (same interaction style as Proxmox list), without requiring a jump to extension settings.
- RU: В диалоге бэкапов БД тап по шестерёнке теперь открывает отдельный диалог «Добавить БД» прямо в Ops Center (в том же стиле взаимодействия, как в списке Proxmox), без перехода в настройки расширений.

### Changed / Изменено
- EN: SemVer patch bump to `8.41.56`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.41.56` and `ANDROID_VERSION_CODE=298`, with prerelease links aligned to `v8.41.56-develop`.
- RU: Выполнен SemVer patch-бамп до `8.41.56`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.41.56` и `ANDROID_VERSION_CODE=298`, prerelease-ссылки выровнены на `v8.41.56-develop`.

## [8.41.54] - 2026-04-07

### Fixed / Исправлено
- EN: Android Ops Center DB backup flow now routes `db_detail_*` actions through the same control-action pipeline as Proxmox host actions, so tapping DB backup cards opens details without API routing errors.
- RU: В Android «Оперативном центре» поток бэкапов БД теперь отправляет `db_detail_*` через тот же control-action пайплайн, что и действия по хостам Proxmox, поэтому тап по карточкам БД открывает детали без ошибок маршрутизации API.

### Changed / Изменено
- EN: SemVer patch bump to `8.41.54`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.41.54` and `ANDROID_VERSION_CODE=296`, with prerelease links aligned to `v8.41.54-develop`.
- RU: Выполнен SemVer patch-бамп до `8.41.54`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.41.54` и `ANDROID_VERSION_CODE=296`, prerelease-ссылки выровнены на `v8.41.54-develop`.

## [8.41.51] - 2026-04-07

### Changed / Изменено
- EN: Android Ops Center: the `БД` tile now opens in the same interaction flow as `proxmox` (reset selected backup labels, close stale stats dialog state, then open DB backups dialog for fresh data).
- RU: Android «Оперативный центр»: плашка `БД` теперь открывается по тому же сценарию, что и `proxmox` (сброс выбранных меток бэкапа, очистка состояния старого диалога статистики и открытие диалога бэкапов БД с актуальными данными).
- EN: Android DB backups dialog now mirrors Proxmox loading behavior: until `backup_databases` menu data is received, the dialog stays in explicit loading mode.
- RU: Диалог бэкапов БД в Android теперь зеркалит поведение загрузки Proxmox: пока не получены menu-данные `backup_databases`, показывается явное состояние загрузки.
- EN: SemVer patch bump to `8.41.51`; repository version references synchronized; Android metadata updated to `ANDROID_VERSION_NAME=8.41.51` and `ANDROID_VERSION_CODE=293`, with prerelease links aligned to `v8.41.51-develop`.
- RU: Выполнен SemVer patch-бамп до `8.41.51`; ссылки на версию в репозитории синхронизированы; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.41.51` и `ANDROID_VERSION_CODE=293`, prerelease-ссылки выровнены на `v8.41.51-develop`.

## [8.41.48] - 2026-04-07

### Fixed
- EN: Fixed Android Ops Hub sync badge behavior: after manual synchronization, status now switches to synchronized when refresh cycle completes even if some server checks return errors.
- RU: Исправлено поведение статуса синхронизации в Android «Оперативном центре»: после ручной синхронизации статус теперь переключается в «синхронизировано» по завершении цикла обновления, даже если часть проверок серверов завершилась ошибками.

### Changed
- EN: SemVer patch bump to `8.41.48`; Android metadata updated to `ANDROID_VERSION_NAME=8.41.48` and `ANDROID_VERSION_CODE=291`; prerelease APK link synchronized.
- RU: Выполнен SemVer patch-бамп до `8.41.48`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.41.48` и `ANDROID_VERSION_CODE=291`; ссылка на prerelease APK синхронизирована.

## [8.41.47] - 2026-04-07

### Changed / Изменено
- EN: In Android Ops Center, the `БД` tile now consistently renders DB backup-specific data in the same compact pattern as the `proxmox` tile (summary from `backup_databases`, list context and backup-oriented labels).
- RU: В Android «Оперативном центре» плашка `БД` теперь стабильно показывает именно данные бэкапов БД в том же компактном паттерне, что и плашка `proxmox` (сводка из `backup_databases`, контекст списка и backup-ориентированные подписи).
- EN: Tapping the `БД` tile now follows the same interaction model as `proxmox`: opens the dedicated backups dialog and routes further actions using DB-backup data only.
- RU: Тап по плашке `БД` теперь работает по той же модели, что и `proxmox`: открывается отдельный диалог бэкапов и дальнейшие действия идут только по данным бэкапов БД.
- EN: Updated Android DB-backups dialog copy (`title/loading/empty/close`) to clearly reflect backup semantics instead of a generic database list wording.
- RU: Обновлены тексты диалога бэкапов БД в Android (`title/loading/empty/close`), чтобы явно отражать сценарий бэкапов вместо общего «списка баз».
- EN: Completed repository-wide SemVer patch bump to `8.41.47`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.47` and `ANDROID_VERSION_CODE=290`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.47`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.47` и `ANDROID_VERSION_CODE=290`, а также выровнены prerelease-ссылки на APK.

## [8.41.45] - 2026-04-07

### Fixed / Исправлено
- EN: Fixed Android Ops Center DB backup tile parsing: summary markers are now matched with normalized `е/ё`, and total fallback now also reads `В мониторинге`, so the tile no longer falls back to a dash when DB backups exist.
- RU: Исправлен разбор сводки плашки бэкапов БД в Android «Оперативном центре»: маркеры теперь сопоставляются с нормализацией `е/ё`, а fallback по общему числу также читает строку `В мониторинге`, поэтому плашка больше не уходит в прочерк при наличии бэкапов.
- EN: Completed repository-wide SemVer patch bump to `8.41.45`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.45` and `ANDROID_VERSION_CODE=288`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.45`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.45` и `ANDROID_VERSION_CODE=288`, а также выровнены prerelease-ссылки на APK.

## [8.41.42] - 2026-04-07

### Fixed / Исправлено
- EN: Fixed Android Ops Center DB list loading state: for `backup_databases` we now keep the menu context even when `menu_options` is empty, so the dialog no longer hangs on "loading" and correctly shows an empty-state message.
- RU: Исправлено состояние загрузки списка БД в Android «Оперативном центре»: для `backup_databases` теперь сохраняется контекст меню даже при пустом `menu_options`, поэтому диалог больше не зависает на «загрузке» и корректно показывает состояние пустого списка.
- EN: Added DB summary fallback parsing in Android (`0/0`) when backend reports that database data is not available yet, so the DB tile no longer shows a dash in this scenario.
- RU: Добавлен fallback-разбор сводки БД в Android (`0/0`), когда backend сообщает, что данных по базам пока нет, поэтому в этом сценарии плашка БД больше не показывает прочерк.
- EN: Completed repository-wide SemVer patch bump to `8.41.42`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.42` and `ANDROID_VERSION_CODE=285`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.42`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.42` и `ANDROID_VERSION_CODE=285`, а также выровнены prerelease-ссылки на APK.

## [8.41.41] - 2026-04-07

### Fixed / Исправлено
- EN: Fixed `backup_databases` mobile/backend response so disabled DBs are no longer dropped from the list: they are now shown with a disabled marker (`⚪ … — мониторинг отключён`), which restores DB list rendering in Android Ops Center and keeps access to per-DB actions.
- RU: Исправлен mobile/backend-ответ для `backup_databases`: отключённые БД больше не выкидываются из списка, а отображаются с маркером отключения (`⚪ … — мониторинг отключён`), из-за чего в Android «Оперативном центре» снова загружается список баз и остаётся доступ к действиям по каждой базе.
- EN: Updated DB backup summary text to include monitored DB count (`🔎 В мониторинге`), so Android tile parsing consistently receives numeric totals instead of fallback dash output.
- RU: Обновлён текст сводки по бэкапам БД с добавлением счётчика `🔎 В мониторинге`, чтобы Android-плашка стабильно получала числовые итоги вместо fallback-прочерка.
- EN: Completed repository-wide SemVer patch bump to `8.41.41`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.41` and `ANDROID_VERSION_CODE=284`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.41`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.41` и `ANDROID_VERSION_CODE=284`, а также выровнены prerelease-ссылки на APK.

## [8.41.40] - 2026-04-07

### Changed / Изменено
- EN: In Android Ops Center DB tiles, long-tap actions now include monitor toggle (on/off) in addition to edit/delete.
- RU: В Android «Оперативном центре» в плашках БД по долгому тапу добавлено переключение мониторинга (вкл/выкл) вместе с редактированием/удалением.
- EN: Added backend support for DB monitor toggling via mobile actions and excluded disabled DB tiles from the `backup_databases` list until they are enabled again.
- RU: Добавлена backend-поддержка переключения мониторинга БД через mobile-действия, а отключённые базы теперь исключаются из списка `backup_databases` до повторного включения.
- EN: Completed repository-wide SemVer patch bump to `8.41.40`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.40` and `ANDROID_VERSION_CODE=283`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.40`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.40` и `ANDROID_VERSION_CODE=283`, а также выровнены prerelease-ссылки на APK.

## [8.41.39] - 2026-04-06

### Changed / Изменено
- EN: In Android Ops Center, database tiles in the "Database backups" overlay now support long-tap actions in the same pattern as Proxmox tiles (quick manage actions from a dedicated dialog).
- RU: В Android «Оперативном центре» плашки баз в оверлее «Бэкапы БД» теперь поддерживают долгий тап по аналогии с Proxmox-плашками (быстрые действия управления в отдельном диалоге).
- EN: Added a gear action to the "Database backups" overlay header for direct DB-entry creation from Ops Center, without leaving the current context.
- RU: В заголовок оверлея «Бэкапы БД» добавлена шестерёнка для прямого добавления записи БД из оперативного центра без выхода из текущего контекста.
- EN: Completed repository-wide SemVer patch bump to `8.41.39`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.39` and `ANDROID_VERSION_CODE=282`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.39`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.39` и `ANDROID_VERSION_CODE=282`, а также выровнены prerelease-ссылки на APK.

## [8.41.36] - 2026-04-06

### Changed / Изменено
- EN: Updated Android Ops Center Proxmox host cards with long-tap management actions (edit, toggle, delete), mirroring the long-tap control pattern used in point server checks.
- RU: В Android оперативном центре на карточках Proxmox-хостов добавлено управление по долгому тапу (редактировать, включить/выключить, удалить) по аналогии со сценарием долгого тапа в точечной проверке серверов.
- EN: Proxmox add-host flow from the gear button now submits only the backup host name (`settings_proxmox_add|<host>`), and backend mobile settings API now applies this payload directly by adding the host into `PROXMOX_HOSTS`.
- RU: В сценарии добавления Proxmox-хоста по шестерёнке теперь отправляется только имя хоста бэкапа (`settings_proxmox_add|<host>`), а backend mobile settings API сразу применяет этот payload, добавляя хост в `PROXMOX_HOSTS`.
- EN: Completed repository-wide SemVer patch bump to `8.41.36`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.36` and `ANDROID_VERSION_CODE=279`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.36`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.36` и `ANDROID_VERSION_CODE=279`, а также выровнены prerelease-ссылки на APK.

## [8.41.35] - 2026-04-06

### Changed / Изменено
- EN: Fixed Proxmox host counting mismatch: backup reports now use the full enabled host list from settings instead of only hosts already present in DB history.
- RU: Исправлено расхождение подсчёта Proxmox-хостов: отчёты по бэкапам теперь используют полный список включённых хостов из настроек, а не только хосты, которые уже есть в истории БД.
- EN: Normalized stale-host calculations to the same configured host scope to keep summary/problem counters consistent across Telegram bot and Android app.
- RU: Нормализован расчёт «устаревших» хостов в той же области настроенных хостов, чтобы счётчики в сводке/проблемах были консистентны в Telegram-боте и Android-приложении.
- EN: Completed repository-wide SemVer patch bump to `8.41.35`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.35` and `ANDROID_VERSION_CODE=278`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.35`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.35` и `ANDROID_VERSION_CODE=278`, а также выровнены prerelease-ссылки на APK.
## [8.41.32] - 2026-04-05

### Changed / Изменено
- EN: Completed repository-wide SemVer patch bump to `8.41.32`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.32` and `ANDROID_VERSION_CODE=275`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.32`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.32` и `ANDROID_VERSION_CODE=275`, а также выровнены prerelease-ссылки на APK.

## [8.41.31] - 2026-04-05

### Changed / Изменено
- EN: In Android Ops Center, tapping the gear in the Proxmox backups overlay no longer closes the backups window first; the add-server action is triggered directly from the same overlay context.
- RU: В Android оперативном центре нажатие на шестерёнку в оверлее бэкапов Proxmox больше не закрывает окно бэкапов перед действием; запуск добавления сервера выполняется прямо из текущего оверлея.
- EN: Morning report display in Android was moved to a top overlay dialog (AlertDialog) opened from the Ops Center quick action, with scrollable content and mark-as-read support.
- RU: Показ утреннего отчёта в Android перенесён в верхний оверлейный диалог (AlertDialog), который открывается из быстрого действия оперативного центра, со скроллом контента и поддержкой отметки «Прочитано».
- EN: Completed repository-wide SemVer patch bump to `8.41.31`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.31` and `ANDROID_VERSION_CODE=274`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.31`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.31` и `ANDROID_VERSION_CODE=274`, а также выровнены prerelease-ссылки на APK.
## [8.41.28] - 2026-04-05

### Changed / Изменено
- EN: Android Proxmox UX in Ops Center was refined: removed the duplicate inline "Proxmox backups" list under the Settings button and kept only the overlay list dialog.
- RU: Доработан UX Proxmox в оперативном центре Android: убран дублирующийся встроенный список «бэкапы Proxmox» под кнопкой «Настройки», оставлен только оверлейный список.
- EN: Added a gear action in the "Proxmox backups" dialog for opening backup-server addition flow, and removed the gear action from the backup statistics dialog.
- RU: Добавлена шестерёнка в диалоге «бэкапы Proxmox» для запуска добавления сервера в бэкап, а из диалога статистики бэкапа шестерёнка удалена.
- EN: Completed repository-wide SemVer patch bump to `8.41.28`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.28` and `ANDROID_VERSION_CODE=271`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.28`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.28` и `ANDROID_VERSION_CODE=271`, а также выровнены prerelease-ссылки на APK.

## [8.41.27] - 2026-04-05

### Changed / Изменено
- EN: Redesigned Android launcher foreground icon: now it emphasizes an antenna/satellite communication motif above open palms (hands) for clearer monitoring-and-protection symbolism.
- RU: Переработана foreground-иконка launcher в Android: теперь акцент на антенне/спутниковой связи над раскрытыми ладонями для более явной символики мониторинга и защиты.
- EN: Completed repository-wide SemVer patch bump to `8.41.27`; synchronized explicit project-version references, updated Android metadata to `ANDROID_VERSION_NAME=8.41.27` and `ANDROID_VERSION_CODE=270`, and aligned prerelease APK links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.27`; синхронизированы явные упоминания версии проекта, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.27` и `ANDROID_VERSION_CODE=270`, а также выровнены prerelease-ссылки на APK.

## [8.41.26] - 2026-04-05

### Changed / Изменено
- EN: Updated Android launcher icon scaling by removing extra foreground inset (`0dp` on all sides) so the icon art is used at full adaptive-icon area without adding new binary assets.
- RU: Обновлён масштаб иконки Android launcher: убран дополнительный отступ foreground (`0dp` со всех сторон), чтобы изображение использовалось на полной adaptive-icon области без добавления новых бинарных ассетов.
- EN: Completed repository-wide SemVer patch bump to `8.41.26`; synchronized explicit project-version references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.26` and `ANDROID_VERSION_CODE=269`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.26`; синхронизированы явные упоминания версии проекта и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.26` и `ANDROID_VERSION_CODE=269`.
## [8.41.21] - 2026-04-05

- EN: Updated Android operational center UX: added top-right quick app minimize button, removed explicit close buttons, and removed the extensions block from the operational center surface.
- RU: Обновлён UX оперативного центра Android: добавлен быстрый крестик сворачивания приложения в правом верхнем углу, убраны явные кнопки закрытия и удалён блок «Расширения» с поверхности оперативного центра.
- EN: Sync trigger is now guarded from duplicate starts while an active synchronization is already running.
- RU: Запуск синхронизации теперь защищён от повторного старта, пока предыдущая синхронизация ещё выполняется.
- EN: Performed repository patch bump to `8.41.21`; updated Android metadata to `ANDROID_VERSION_NAME=8.41.21` and `ANDROID_VERSION_CODE=264`, plus aligned prerelease README link.
- RU: Выполнен patch-бамп репозитория до `8.41.21`; обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.21` и `ANDROID_VERSION_CODE=264`, а также выровнена prerelease-ссылка в README.

## [8.41.20] - 2026-04-05

### Changed / Изменено
- EN: Follow-up release after review: completed repository-wide SemVer patch bump to `8.41.20` and synchronized all in-code/doc references where project version is explicitly declared.
- RU: Довыпуск после ревью: выполнен репозиторный SemVer patch-бамп до `8.41.20` и синхронизированы все in-code/doc ссылки, где версия проекта указана явно.
- EN: Android metadata was incremented to `ANDROID_VERSION_NAME=8.41.20` and `ANDROID_VERSION_CODE=263`; prerelease links were aligned to `v8.41.20-develop`.
- RU: Android-метаданные увеличены до `ANDROID_VERSION_NAME=8.41.20` и `ANDROID_VERSION_CODE=263`; prerelease-ссылки выровнены на `v8.41.20-develop`.

## [8.41.19] - 2026-04-05

### Changed / Изменено
- EN: In Android Compact Operations Center, tapping the `proxmox` tile now behaves like a long tap on `Servers`: it opens a dedicated Proxmox backup selection dialog and lets you launch backup stats directly from that dialog.
- RU: В Android Compact оперативном центре тап по плашке `proxmox` теперь работает как долгий тап по `Серверы`: открывается отдельный диалог выбора Proxmox-бэкапа с быстрым запуском статистики.
- EN: In Proxmox backup statistics, tapping the settings gear (`⚙`) now opens a dedicated Proxmox backup add dialog instead of routing to common settings.
- RU: В статистике Proxmox-бэкапа нажатие на шестерёнку (`⚙`) теперь открывает отдельный диалог добавления Proxmox-бэкапа вместо перехода в общие настройки.
- EN: Completed repository-wide SemVer patch bump to `8.41.19`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.19` and `ANDROID_VERSION_CODE=262`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.19`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.19` и `ANDROID_VERSION_CODE=262`.

## [8.41.16] - 2026-04-03

### Changed / Изменено
- EN: Updated Android launcher icon concept: the foreground now shows a satellite above cupped hands to reflect monitoring and protection.
- RU: Обновлена концепция иконки Android-приложения: на переднем плане теперь спутник над раскрытыми ладонями как символ мониторинга и защиты.
- EN: In Android Operations Center, tapping the `proxmox` tile now opens a chips list of Proxmox backup names (same compact tile style as server quick actions).
- RU: В Android оперативном центре тап по плашке `proxmox` теперь открывает список имён Proxmox-бэкапов в виде компактных плашек (в том же стиле, что и быстрые действия по серверам).
- EN: Proxmox backup statistics now open as an overlay dialog above the Operations Center; added close (`✕`) and settings (`⚙`) controls in the header.
- RU: Статистика Proxmox-бэкапа теперь открывается поверх оперативного центра во всплывающем диалоге; в заголовок добавлены крестик закрытия (`✕`) и шестерёнка (`⚙`).
- EN: Added a quick settings route from backup statistics (`settings_backup_hosts`) to start adding/configuring new backup entries.
- RU: Добавлен быстрый переход из статистики бэкапа в настройки (`settings_backup_hosts`) для добавления/настройки новых backup-элементов.
- EN: Completed repository-wide SemVer patch bump to `8.41.16`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.16` and `ANDROID_VERSION_CODE=260`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.16`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.16` и `ANDROID_VERSION_CODE=260`.

## [8.41.11] - 2026-04-03

### Changed / Изменено
- EN: In Android Compact Operations Center, removed the `Раздел системы` block from the Ops Hub screen; system controls remain available in non-compact layout and via existing settings entry points.
- RU: В Android Compact оперативном центре убран блок `Раздел системы` с экрана Ops Hub; системные действия остаются доступны в некомпактной раскладке и через существующие точки входа в настройки.
- EN: In the Proxmox tile flow, tapping the `proxmox` tile now opens a chips list of Proxmox backup names directly in the Operations Center.
- RU: В сценарии плашки Proxmox тап по плашке `proxmox` теперь открывает список имён Proxmox-бэкапов в виде плашек прямо в оперативном центре.
- EN: Added in-place Proxmox backup statistics card: tapping a backup-name chip runs the backup action and renders returned stats under the Proxmox block.
- RU: Добавлена inline-карточка статистики Proxmox-бэкапа: нажатие на плашку имени бэкапа запускает действие и показывает возвращённую статистику под блоком Proxmox.
- EN: Completed repository-wide SemVer patch bump to `8.41.11`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.11` and `ANDROID_VERSION_CODE=255`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.11`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.11` и `ANDROID_VERSION_CODE=255`.

## [8.41.10] - 2026-04-03

### Changed / Изменено
- EN: In the Android Operations Center targeted server check dialog, kept the close icon (`✕`) on the right side of the title and placed the settings icon directly under it to open the add-server flow.
- RU: В Android-диалоге точечной проверки серверов оперативного центра крестик закрытия (`✕`) оставлен справа в заголовке, а шестерёнка размещена прямо под ним с действием открытия добавления сервера.
- EN: Moved targeted-check sorting controls higher, directly under the dialog header, so sorting is available earlier in the flow.
- RU: Методы сортировки в точечной проверке передвинуты выше — сразу под заголовок диалога, чтобы переключение было доступно раньше по сценарию.
- EN: Completed repository-wide SemVer patch bump to `8.41.10`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.10` and `ANDROID_VERSION_CODE=254`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.10`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.10` и `ANDROID_VERSION_CODE=254`.

## [8.41.6] - 2026-04-03

### Changed / Изменено
- EN: In Android Operations Center targeted server check dialog, removed the `Только включённые` filter label/checkbox and always show the full server list.
- RU: В Android-диалоге точечной проверки серверов оперативного центра убраны надпись и галка `Только включённые`; теперь всегда показывается полный список серверов.
- EN: In targeted server check tiles, removed inline `Вкл/Выкл` status text and made disabled server tiles visually distinct with `errorContainer` background color.
- RU: В плашках точечной проверки убран текстовый статус `Вкл/Выкл`, а отключённые серверы теперь выделяются отдельным цветом фона (`errorContainer`).
- EN: Replaced the bottom `Закрыть` action in the targeted server check dialog with a close icon (`✕`) in the top-right corner of the dialog header.
- RU: Нижняя кнопка `Закрыть` в диалоге точечной проверки заменена на крестик (`✕`) в правом верхнем углу заголовка.
- EN: Completed repository-wide SemVer patch bump to `8.41.6`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.6` and `ANDROID_VERSION_CODE=250`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.6`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.6` и `ANDROID_VERSION_CODE=250`.

## [8.41.5] - 2026-04-03

### Changed / Изменено
- EN: In Android Operations Center, removed the `🛰 Проверить доступность` action button from the main action block.
- RU: В Android оперативном центре удалена кнопка `🛰 Проверить доступность` из основного блока действий.
- EN: In Android targeted server check dialog, replaced list-like server buttons with denser compact tiles and kept tap/long-press behavior for quick checks and actions.
- RU: В Android-диалоге точечной проверки серверов кнопки-строки заменены на компактные плашки; сохранены короткий тап для проверки и длинный тап для действий.
- EN: In Android server action dialog, replaced bottom close action with a close icon (`✕`) on the right side of the title.
- RU: В Android-диалоге действий по серверу закрытие через нижнюю кнопку заменено на крестик (`✕`) справа в заголовке.
- EN: Completed repository-wide SemVer patch bump to `8.41.5`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.5` and `ANDROID_VERSION_CODE=249`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.5`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.5` и `ANDROID_VERSION_CODE=249`.

## [8.41.4] - 2026-04-03

### Changed / Изменено
- EN: In Android targeted server checks, made the server-management list denser: reduced card spacing and replaced large row action buttons with compact text controls.
- RU: В Android точечной проверке серверов список управления сделан плотнее: уменьшены отступы карточек и крупные кнопки действий заменены компактными текстовыми контролами.
- EN: In Android server edit flow, replaced explicit close action with a close icon (`✕`) on the right side of the section header.
- RU: В Android-флоу редактирования сервера явное закрытие заменено на иконку крестика (`✕`) справа от заголовка секции.
- EN: In Android Operations Center and tile settings copy, changed the label `Развернуть сведения` to shorter `Развернуть` (and matching collapse text to `Свернуть`).
- RU: В Android оперативном центре и настройке плашек надпись `Развернуть сведения` заменена на короткую `Развернуть` (а парная — на `Свернуть`).
- EN: In Android tile-settings dialog, replaced `Готово` UX with close icon (`✕`) in the title and kept close action as `Закрыть`; also made the list text denser.
- RU: В Android-диалоге настройки плашек UX `Готово` заменён на крестик (`✕`) в заголовке, действие оставлено как `Закрыть`; список сделан более компактным по тексту.
- EN: Completed repository-wide SemVer patch bump to `8.41.4`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.4` and `ANDROID_VERSION_CODE=248`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.4`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.4` и `ANDROID_VERSION_CODE=248`.

## [8.41.3] - 2026-04-03

### Fixed / Исправлено
- EN: Added `ExperimentalFoundationApi` opt-in to the Android `MonitoringApp` composable so `combinedClickable` in Compact Ops compiles without experimental API errors.
- RU: Добавлен opt-in `ExperimentalFoundationApi` для Android-компонуемого `MonitoringApp`, чтобы `combinedClickable` в Compact Ops компилировался без ошибок experimental API.

### Changed / Изменено
- EN: Completed repository-wide SemVer patch bump to `8.41.3`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.3` and `ANDROID_VERSION_CODE=247`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.3`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.3` и `ANDROID_VERSION_CODE=247`.

## [8.41.2] - 2026-04-03

### Changed / Изменено
- EN: In Android targeted server check dialog, moved the gear button from the floating list overlay into the dialog header next to the title for more predictable access.
- RU: В Android-диалоге точечной проверки серверов шестерёнка перенесена из плавающего оверлея списка в заголовок диалога рядом с названием для более предсказуемого доступа.
- EN: Rewired the gear action to open a dedicated server-add dialog (IP/name/type/timeout), so adding a server is now available directly from targeted checks.
- RU: Действие шестерёнки перенастроено на открытие отдельного диалога добавления сервера (IP/имя/тип/timeout), поэтому добавление сервера теперь доступно прямо из точечной проверки.
- EN: Replaced server list buttons with compact tappable cards; short tap runs targeted availability check, long tap opens compact icon-based actions (edit, enable/disable, delete).
- RU: Кнопки списка серверов заменены на компактные плашки; короткий тап запускает точечную проверку доступности, долгий тап открывает компактные иконки действий (редактирование, включение/выключение, удаление).
- EN: Completed repository-wide SemVer patch bump to `8.41.2`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.2` and `ANDROID_VERSION_CODE=246`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.2`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.2` и `ANDROID_VERSION_CODE=246`.

## [8.41.1] - 2026-04-03

### Changed / Изменено
- EN: In Android targeted server check overlay, moved the server-list settings gear to a floating top-right position (overlay method) directly over the list area for faster access.
- RU: В оверлее точечной проверки серверов Android шестерёнка настроек списка перенесена в плавающее положение справа сверху (методом наложения) прямо над областью списка для более быстрого доступа.
- EN: Made server buttons in the targeted check list even more compact by reducing list spacing and button/text paddings, which decreases scrolling while searching for a specific server.
- RU: Кнопки серверов в списке точечной проверки сделаны ещё компактнее: уменьшены интервалы списка и внутренние отступы кнопок/текста, что снижает объём скроллинга при поиске нужного сервера.
- EN: Completed repository-wide SemVer patch bump to `8.41.1`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.1` and `ANDROID_VERSION_CODE=245`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.41.1`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.1` и `ANDROID_VERSION_CODE=245`.

## [8.41.0] - 2026-04-03

### Added / Добавлено
- EN: In Android Compact Ops, long-press on the `Servers` tile now opens a modal overlay with per-server targeted availability check buttons.
- RU: В Android Compact Ops долгое нажатие на плашку `Серверы` теперь открывает модальное наложение с кнопками точечной проверки доступности по каждому серверу.
- EN: Added a gear button in the top-right corner of the server list overlay that opens a second overlay with server list settings.
- RU: Добавлена шестерёнка в правом верхнем углу списка серверов: она открывает отдельное наложение с настройками списка серверов.

### Changed / Изменено
- EN: Made server action buttons in the targeted-check overlay more compact (reduced paddings and smaller text) to reduce scrolling while searching for a specific server.
- RU: Кнопки серверов в оверлее точечной проверки сделаны более компактными (уменьшены отступы и размер текста), чтобы снизить скроллинг при поиске нужного сервера.
- EN: Removed the separate `Checks` section that was rendered below the Ops Center in Android Compact Ops.
- RU: Удалён отдельный раздел `Проверки`, который отображался ниже оперативного центра в Android Compact Ops.
- EN: Completed repository-wide SemVer minor bump to `8.41.0`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.41.0` and `ANDROID_VERSION_CODE=244`.
- RU: Выполнен репозиторный SemVer minor-бамп до `8.41.0`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.41.0` и `ANDROID_VERSION_CODE=244`.

## [8.40.9] - 2026-04-03

### Added / Добавлено
- EN: Android Compact Ops server tile now supports two interaction modes: short tap starts sequential availability check for all configured servers, while long tap opens per-server quick check buttons.
- RU: В Android Compact Ops плашка серверов теперь поддерживает два режима: короткое нажатие запускает последовательную проверку доступности всех настроенных серверов, долгое нажатие открывает кнопки точечной проверки по одному серверу.

### Changed / Изменено
- EN: Added visual progress for bulk server checks in Android UI, including current server label and linear progress bar during the run.
- RU: Добавлен визуальный прогресс пакетной проверки серверов в Android UI: отображается текущий сервер и линейный прогресс-бар во время выполнения.
- EN: Completed repository-wide SemVer patch bump to `8.40.9`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.40.9` and `ANDROID_VERSION_CODE=243`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.40.9`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.40.9` и `ANDROID_VERSION_CODE=243`.

## [8.40.8] - 2026-04-02

### Fixed / Исправлено
- EN: Fixed Android sync indicator behavior in Compact Ops: sync progress now tracks both settings and availability stages, remains visible until both complete, and shows deterministic percentage instead of disappearing early.
- RU: Исправлено поведение индикатора синхронизации Android в Compact Ops: прогресс теперь учитывает этапы загрузки настроек и доступности, остаётся видимым до завершения обоих этапов и показывает детерминированный процент вместо преждевременного скрытия.

### Changed / Изменено
- EN: Completed repository-wide SemVer patch bump to `8.40.8`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.40.8` and `ANDROID_VERSION_CODE=242`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.40.8`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.40.8` и `ANDROID_VERSION_CODE=242`.

## [8.40.7] - 2026-04-02

### Fixed / Исправлено
- EN: Fixed Android `compactOps` debug Kotlin compilation failure in `MainActivity.kt`: added explicit opt-in for Compose Material experimental API (`@OptIn(ExperimentalMaterialApi::class)`) required by pull-refresh components.
- RU: Исправлена ошибка компиляции Kotlin для Android `compactOps` debug в `MainActivity.kt`: добавлен явный opt-in для экспериментального API Compose Material (`@OptIn(ExperimentalMaterialApi::class)`), необходимого pull-refresh компонентам.

### Changed / Изменено
- EN: Completed repository-wide SemVer patch bump to `8.40.7`; synchronized runtime/config/docs/mobile references and updated Android metadata to `ANDROID_VERSION_NAME=8.40.7` and `ANDROID_VERSION_CODE=241`.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.40.7`; синхронизированы ссылки на версию в runtime/config/docs/mobile и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.40.7` и `ANDROID_VERSION_CODE=241`.

## [8.40.2] - 2026-04-02

### Fixed / Исправлено
- EN: Fixed Android `compactOps` build failure in `MainActivity`: moved `extractMailBackupVolumeFromMorningReport` to top-level private scope so the mail tile summary logic resolves correctly during Kotlin compilation.
- RU: Исправлено падение Android-сборки `compactOps` в `MainActivity`: `extractMailBackupVolumeFromMorningReport` вынесена в private-функцию верхнего уровня, чтобы логика сводки плашки почты корректно резолвилась при компиляции Kotlin.

### Changed / Изменено
- EN: Completed repository-wide SemVer patch bump to `8.40.2`; synchronized runtime/config/docs/mobile references, updated Android metadata to `ANDROID_VERSION_NAME=8.40.2` and `ANDROID_VERSION_CODE=236`, and refreshed prerelease links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.40.2`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.40.2` и `ANDROID_VERSION_CODE=236`, а также обновлены prerelease-ссылки.

## [8.39.13] - 2026-04-02

### Fixed / Исправлено
- EN: Fixed Compact Ops sync indicator in the operations center: the status line now displays the exact sync time (HH:mm:ss) after a successful sync.
- RU: Исправлен индикатор синхронизации в оперативном центре Compact Ops: после успешной синхронизации строка статуса теперь показывает точное время синка (HH:mm:ss).

### Changed / Изменено
- EN: Removed the `New visual mode` subtitle from the Compact Ops top bar to keep the header cleaner.
- RU: Убрана подпись `Новый визуальный режим` из верхней панели Compact Ops, чтобы шапка была чище.
- EN: Completed repository-wide patch bump to `8.39.13`; synchronized version references across runtime/config/docs/mobile, updated Android metadata to `ANDROID_VERSION_NAME=8.39.13` and `ANDROID_VERSION_CODE=232`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.39.13`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.39.13` и `ANDROID_VERSION_CODE=232`, а также обновлены prerelease-ссылки.

## [8.39.9] - 2026-04-01

### Fixed / Исправлено
- EN: Fixed Compact Ops `ZFS` tile summary in the operations center: it now uses monitoring ratio data (for example, combined `servers + pools` like `48/48`) instead of static `вкл/выкл`.
- RU: Исправлена сводка плашки `ZFS` в оперативном центре Compact Ops: теперь используется мониторинговое соотношение (например суммарно `серверы + пулы`, как `48/48`), а не статичное `вкл/выкл`.
- EN: Fixed false red state for Compact Ops `Расширения`/`поставщики` tile when supplier stock reports are fully successful (e.g. `9/9`): health now prioritizes explicit success ratios from the report response.
- RU: Исправлена ложная красная подсветка плашки `Расширения`/`поставщики` в Compact Ops при полностью успешных отчётах поставщиков (например `9/9`): оценка состояния теперь приоритетно берёт явные ratio успеха из ответа отчёта.

### Changed / Изменено
- EN: Completed repository-wide patch bump to `8.39.9`; synchronized version references across runtime/config/docs/mobile, updated Android metadata to `ANDROID_VERSION_NAME=8.39.9` and `ANDROID_VERSION_CODE=228`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.39.9`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.39.9` и `ANDROID_VERSION_CODE=228`, а также обновлены prerelease-ссылки.

## [8.39.7] - 2026-04-01

### Fixed / Исправлено
- EN: Fixed Compact Ops `Расширения` alert state: extension summary now evaluates mail backup health by the latest mail backup entry only, so historical older failures no longer paint the tile red when current backup is healthy.
- RU: Исправлено аварийное состояние `Расширения` в Compact Ops: здоровье почтовых бэкапов теперь считается только по последней записи, поэтому старые ошибки из истории больше не красят плашку в красный при актуально успешном бэкапе.
- EN: Fixed Compact Ops `ZFS` tile fallback value: when ZFS extension is enabled/disabled and ratio summary is unavailable, the tile now shows `вкл`/`выкл` instead of a dash.
- RU: Исправлен fallback для плашки `ZFS` в Compact Ops: когда у расширения нет ratio-сводки, теперь отображается `вкл`/`выкл` вместо прочерка.

### Changed / Изменено
- EN: Completed repository patch bump to `8.39.7`; updated Android metadata to `ANDROID_VERSION_NAME=8.39.7` and `ANDROID_VERSION_CODE=226`, synchronized Android runtime version string and prerelease README link.
- RU: Выполнен patch-бамп репозитория до `8.39.7`; обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.39.7` и `ANDROID_VERSION_CODE=226`, синхронизированы runtime-версия Android и prerelease-ссылка в README.

## [8.39.6] - 2026-03-31

### Fixed / Исправлено
- EN: Improved GitHub API fallback in `publish_android_prerelease.ps1` for existing prereleases: when `PATCH /releases/{id}` returns `400/422`, the script now retries without `target_commitish`, then with a minimal payload, so release updates are more resilient to GitHub validation differences.
- RU: Улучшен GitHub API fallback в `publish_android_prerelease.ps1` для уже существующих prerelease: если `PATCH /releases/{id}` возвращает `400/422`, скрипт теперь повторяет запрос без `target_commitish`, а затем с минимальным payload, чтобы обновление релиза было устойчивее к различиям в валидации GitHub.

### Changed / Изменено
- EN: Completed repository-wide patch bump to `8.39.6`; synchronized runtime/config/docs/mobile references, updated Android metadata to `ANDROID_VERSION_NAME=8.39.6` and `ANDROID_VERSION_CODE=225`, and refreshed prerelease links.
- RU: Выполнен patch-бамп по репозиторию до `8.39.6`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.39.6` и `ANDROID_VERSION_CODE=225`, а также обновлены prerelease-ссылки.

## [8.39.5] - 2026-03-31

### Changed / Изменено
- EN: Completed follow-up repository-wide patch bump to `8.39.5` after review feedback; synchronized Android runtime/doc references and updated Android metadata to `ANDROID_VERSION_NAME=8.39.5` and `ANDROID_VERSION_CODE=224`.
- RU: По результатам ревью выполнен дополнительный patch-бамп по репозиторию до `8.39.5`; синхронизированы ссылки на версию в Android/runtime/docs и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.39.5` и `ANDROID_VERSION_CODE=224`.

## [8.39.4] - 2026-03-31

### Changed / Изменено
- EN: Added one automatic retry for `getAvailability()` when synchronization fails due to transient network failures (`timeout`, `connect`, `DNS`) to reduce false `not synchronized` states in Compact Ops.
- RU: Для `getAvailability()` добавлена одна автоматическая повторная попытка при временных сетевых сбоях (`timeout`, `connect`, `DNS`), чтобы снизить число ложных состояний `не синхронизировано` в Compact Ops.
- EN: Completed repository-wide patch bump to `8.39.4`; Android metadata updated to `ANDROID_VERSION_NAME=8.39.4` and `ANDROID_VERSION_CODE=223`, and prerelease links were updated.
- RU: Выполнен patch-бамп по репозиторию до `8.39.4`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.39.4` и `ANDROID_VERSION_CODE=223`, prerelease-ссылки обновлены.

## [8.39.3] - 2026-03-30

### Changed / Изменено
- EN: Added a dedicated `ZFS` tile to Compact Ops Ops Center metrics, so ZFS extension status is visible in the same compact chip grid as other operational monitors.
- RU: В оперативном центре Compact Ops добавлена отдельная плашка `ZFS`, чтобы статус ZFS-расширения отображался в общем наборе компактных метрик.
- EN: Reworked the `почта` tile logic: it now shows only `OK` or `!` based on the status of the most recent mail backup entry, with fallback to existing backup health flag when history is unavailable.
- RU: Переделана логика плашки `почта`: теперь она показывает только `ОК` или `!` по статусу последнего почтового бэкапа, с fallback на существующий флаг проблем бэкапа, если история недоступна.
- EN: Moved Compact Ops synchronization action from the separate `⟳ Synchronize` button to tap on the `⚡ Ops Center` header area, and removed the standalone sync button from the action row.
- RU: Функция синхронизации в Compact Ops перенесена с отдельной кнопки `⟳ Синхронизировать` на тап по области заголовка `⚡ Оперативный центр`; отдельная кнопка синхронизации удалена.
- EN: Completed repository-wide patch bump to `8.39.3`; Android metadata updated to `ANDROID_VERSION_NAME=8.39.3` and `ANDROID_VERSION_CODE=222`.
- RU: Выполнен patch-бамп по репозиторию до `8.39.3`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.39.3` и `ANDROID_VERSION_CODE=222`.

## [8.39.1] - 2026-03-30

### Changed / Изменено
- EN: In Compact Ops, extension tiles in the Ops Center now show collected operational values (ratios/statuses like on the `Servers` tile) instead of empty placeholders.
- RU: В Compact Ops плашки расширений в оперативном центре теперь показывают собранные значения (соотношения/статусы по аналогии с плашкой «Серверы») вместо пустых заглушек.
- EN: Moved extension tiles into the shared `Details` tile flow next to `Servers`: they now participate in the same expand/collapse behavior (`Expand details` / `Collapse details`) and can be configured in tile settings.
- RU: Плашки расширений перенесены в общий поток «Сведения» рядом с «Серверами»: теперь они участвуют в том же механизме сворачивания/разворачивания («Развернуть сведения» / «Свернуть сведения») и настраиваются в настройках плашек.
- EN: Reworked extension visualization from elongated cards to compact metric chips consistent with `Servers`, reducing visual noise in the Ops Center.
- RU: Визуал расширений переделан с вытянутых карточек на компактные metric-chip плашки в стиле «Серверов», чтобы уменьшить визуальный шум в оперативном центре.
- EN: Removed the separate status card from Compact Ops dashboard and moved core state indicators into the Ops Center header: project version is now shown to the right of the title, and sync state is shown below the title.
- RU: Убрано отдельное окно «Статус» из дашборда Compact Ops; ключевые индикаторы перенесены в заголовок оперативного центра: версия проекта отображается справа от названия, а статус синхронизации — под названием.
- EN: Added compact sync indicator styling: `synchronized` is shown in green, `not synchronized` in red.
- RU: Добавлена компактная индикация синхронизации: `синхронизировано` отображается зелёным, `не синхронизировано` — красным.
- EN: Completed patch bump to `8.39.1`; Android metadata updated to `ANDROID_VERSION_NAME=8.39.1` and `ANDROID_VERSION_CODE=220`.
- RU: Выполнен patch-бамп до `8.39.1`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.39.1` и `ANDROID_VERSION_CODE=220`.

## [8.38.8] - 2026-03-30

### Changed / Изменено
- EN: Compact Ops extension cards in the Ops Center now use short labels (`proxmox`, `БД`, `почта`, `остатки`, `поставщики`, `ресурсы`, `web`, `mail`) instead of verbose monitoring names.
- RU: Плашки расширений в оперативном центре Compact Ops теперь используют короткие названия (`proxmox`, `БД`, `почта`, `остатки`, `поставщики`, `ресурсы`, `web`, `mail`) вместо длинных мониторинговых формулировок.
- EN: Added ratio summaries for `stock_load_monitor` and `supplier_stock_files` based on extension control-action responses (`без проблем/всего`) with problem highlighting behavior aligned to Proxmox/DB cards.
- RU: Для `stock_load_monitor` и `supplier_stock_files` добавлены сводки в формате `без проблем/всего` из ответов control-action, с той же логикой подсветки проблем, что у карточек Proxmox/БД.
- EN: Resource tile now shows aggregated status (`ОК` or `!`) based on extension-reported problem markers; `web_interface` and `email_processor` tiles now show trigger state as `вкл/выкл`.
- RU: Плашка ресурсов теперь показывает агрегированное состояние (`ОК` или `!`) по маркерам проблем в данных расширения; для `web_interface` и `email_processor` добавлено отображение состояния триггера `вкл/выкл`.
- EN: Completed repository-wide patch bump to `8.38.8`; synchronized runtime/config/docs/mobile version references, updated Android metadata to `ANDROID_VERSION_NAME=8.38.8` and `ANDROID_VERSION_CODE=218`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.38.8`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.8` и `ANDROID_VERSION_CODE=218`, а также обновлены prerelease-ссылки.

## [8.38.7] - 2026-03-30

### Changed / Изменено
- EN: Compact Ops extension cards now fetch live extension summaries during refresh and display extension-produced ratios for backup monitors (for example, `14/14` for Proxmox and `34/35` for DB backups) instead of static extension naming on the value line.
- RU: Плашки расширений в Compact Ops теперь при обновлении подтягивают live-сводки от расширений и показывают соотношения, полученные от мониторинга бэкапов (например, `14/14` для Proxmox и `34/35` для БД), а не статичное имя расширения в строке значения.
- EN: Added shared parsing of backup monitor responses (`Без проблем`, `Проблемных`, totals) to keep ratio text and error-color behavior aligned with the Servers tile logic.
- RU: Добавлен общий парсинг ответов мониторинга бэкапов (`Без проблем`, `Проблемных`, итоги), чтобы соотношение и цветовая маркировка ошибок работали по логике, согласованной с плашкой «Серверы».
- EN: Completed repository-wide patch bump to `8.38.7`; synchronized runtime/config/docs/mobile version references, updated Android metadata to `ANDROID_VERSION_NAME=8.38.7` and `ANDROID_VERSION_CODE=217`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.38.7`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.7` и `ANDROID_VERSION_CODE=217`, а также обновлены prerelease-ссылки.

## [8.38.6] - 2026-03-30

### Changed / Изменено
- EN: Updated Compact Ops extension cards in the Ops Center: cards now prioritize extension-produced data values (for example, `14/14` for Proxmox backups) instead of only showing extension identity/description.
- RU: Обновлены плашки расширений в оперативном центре Compact Ops: теперь в приоритете отображаются данные, полученные расширениями (например, `14/14` для бэкапов Proxmox), а не только само название/описание расширения.
- EN: Added ratio-aware visual marking for extension values: if the parsed `done/total` ratio is degraded, value text uses error color behavior aligned with the Servers tile.
- RU: Добавлена цветовая маркировка значений по соотношению `выполнено/всего`: при деградации значение подсвечивается ошибочным цветом по той же логике, что и у плашки «Серверы».
- EN: Completed repository-wide patch bump to `8.38.6`; synchronized runtime/config/docs/mobile version references, updated Android metadata to `ANDROID_VERSION_NAME=8.38.6` and `ANDROID_VERSION_CODE=216`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.38.6`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.6` и `ANDROID_VERSION_CODE=216`, а также обновлены prerelease-ссылки.

## [8.38.5] - 2026-03-28

### Fixed / Исправлено
- EN: In Compact Ops, wired the "⟳ Sync" button to the same refresh flow as Quick Actions "🔄 Update" and additionally collapse per-server menus after sync to avoid stale per-item state.
- RU: В Compact Ops кнопка «⟳ Синхронизировать» привязана к тому же refresh-сценарию, что и «🔄 Обновить» в «Быстрых действиях»; после синхронизации дополнительно закрываются меню проверок по отдельным серверам, чтобы не оставалось устаревшего состояния.
- EN: Changed Servers tile click behavior: now it immediately requests fresh server settings list and opens single-server check menu (without intermediate choice dialog).
- RU: Изменено поведение плашки «Серверы»: теперь при нажатии сразу запрашивается актуальный список серверов и открывается меню проверки одного сервера (без промежуточного диалога выбора).

### Changed / Изменено
- EN: Renamed Compact Ops extension subsection title from "Extension tiles" to "Extensions".
- RU: Переименован заголовок секции расширений в Compact Ops: вместо «Плашки расширений» теперь «Расширения».
- EN: Reworked Compact Ops extensions block: replaced metric chips with result cards that show extension name and extension execution/result details.
- RU: Переработан блок расширений в Compact Ops: вместо плашек-метрик выводятся карточки результатов с названием расширения и деталями результата работы.
- EN: Completed repository-wide patch bump to `8.38.5`; synchronized runtime/config/docs/mobile version references, updated Android metadata to `ANDROID_VERSION_NAME=8.38.5` and `ANDROID_VERSION_CODE=215`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.38.5`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.5` и `ANDROID_VERSION_CODE=215`, а также обновлены prerelease-ссылки.
## [8.38.2] - 2026-03-28

### Changed / Изменено
- EN: Updated Compact Ops UX: tile settings are now opened via a gear icon in the top-right corner of the Ops frame.
- RU: Обновлён UX Compact Ops: настройка плашек теперь открывается через иконку-шестерёнку в правом верхнем углу Ops-фрейма.
- EN: Added extension info tiles under the main Ops tiles to show enabled extension cards with extension-provided details.
- RU: Добавлены плашки расширений под основными Ops-плашками: показываются карточки активных расширений со сведениями из самих расширений.
- EN: Changed the "Servers" tile click behavior to open a choice dialog with two options: "All servers" and "One server".
- RU: Изменено поведение нажатия плашки «Серверы»: теперь открывается диалог выбора проверки с вариантами «Все серверы» и «Один сервер».
- EN: Changed the "Mode" tile click behavior to cycle silent mode in a loop: `force_quiet -> force_loud -> auto_mode -> force_quiet`.
- RU: Изменено поведение плашки «Режим»: теперь при нажатии режим переключается по циклу `force_quiet -> force_loud -> auto_mode -> force_quiet`.
- EN: Completed repository-wide patch bump to `8.38.2`; synchronized runtime/config/docs/mobile version references, updated Android metadata to `ANDROID_VERSION_NAME=8.38.2` and `ANDROID_VERSION_CODE=212`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.38.2`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.2` и `ANDROID_VERSION_CODE=212`, а также обновлены prerelease-ссылки.

## [8.38.1] - 2026-03-28

### Fixed / Исправлено
- EN: Fixed Android `compactOps` build failure in `MainActivity` by restoring derived Windows auth counters (`windowsTotal`, `windowsTypes`) used in the auth settings block.
- RU: Исправлено падение Android-сборки `compactOps` в `MainActivity`: восстановлены вычисляемые счётчики Windows-аутентификации (`windowsTotal`, `windowsTypes`), используемые в блоке настроек auth.

### Changed / Изменено
- EN: Completed repository-wide patch bump to `8.38.1`; synchronized runtime/config/docs/mobile version references, updated Android metadata to `ANDROID_VERSION_NAME=8.38.1` and `ANDROID_VERSION_CODE=211`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.38.1`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.1` и `ANDROID_VERSION_CODE=211`, а также обновлены prerelease-ссылки.

## [8.38.0] - 2026-03-28

### Added / Добавлено
- EN: Added a Compact Ops tile settings dialog: users can choose which tiles stay visible by default, while the rest move under the “Expand/Collapse details” button.
- RU: Добавлена настройка плашек в Compact Ops: можно выбрать, какие плашки показываются сразу, а какие скрываются под кнопкой «Развернуть/свернуть сведения».
- EN: Added a new “Modes” tile in Compact Ops that opens the corresponding settings section and shows the current silent-mode status.
- RU: Добавлена новая плашка «Режимы» в Compact Ops, которая открывает соответствующий раздел настроек и показывает текущий статус тихого режима.

### Changed / Изменено
- EN: Updated Compact Ops tile composition: removed `DOWN`, `UNKNOWN`, `Disabled extensions`, `Extension issues`, `Win credentials`, and `Win types`; kept focused tiles for `Servers`, `Extensions`, and `Modes`.
- RU: Обновлён состав плашек Compact Ops: убраны `DOWN`, `UNKNOWN`, `Выкл. расширения`, `Проблемы расширений`, `Win-учётки` и `Типы Win`; оставлены ключевые плашки `Серверы`, `Расширения` и `Режимы`.
- EN: Updated server and extension tile counters to `active/total` format and renamed the toggle button text to “Expand/Collapse details”.
- RU: Обновлён формат счётчиков плашек серверов и расширений на `активные/всего`, а текст кнопки переключения переименован в «Развернуть/свернуть сведения».
- EN: Removed the Compact Ops subtitle text (“Focus on state …”) from the hero block.
- RU: Удалена подпись в hero-блоке Compact Ops («Фокус на состоянии …»).
- EN: Completed repository-wide SemVer minor bump to `8.38.0`; synchronized runtime/config/docs/version headers, updated Android metadata to `ANDROID_VERSION_NAME=8.38.0` and `ANDROID_VERSION_CODE=210`, and refreshed prerelease links.
- RU: Выполнен SemVer minor-бамп версии по репозиторию до `8.38.0`; синхронизированы runtime/config/docs/version-заголовки, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.38.0` и `ANDROID_VERSION_CODE=210`, а также обновлены prerelease-ссылки.

## [8.36.0] - 2026-03-28

### Changed / Изменено
- EN: Reworked Android visual style for the Compact Ops flavor into a command-center layout: new centered top bar with mode subtitle, gradient hero block, metric chips, and dashboard action buttons for sync/availability/report/settings.
- RU: Полностью переработан визуальный стиль Android для flavor Compact Ops в формат command-center: новая центрированная верхняя панель с подписью режима, градиентный hero-блок, метрики-чипы и dashboard-кнопки для синхронизации/доступности/отчёта/настроек.
- EN: Introduced a custom Material 3 color system for both dark and light themes to make the interface visually distinct from the previous default look.
- RU: Добавлена кастомная цветовая система Material 3 для тёмной и светлой тем, чтобы интерфейс выглядел принципиально иначе по сравнению с прежним дефолтным видом.
- EN: Completed repository-wide SemVer minor bump to `8.36.0`; synchronized runtime/config/docs/version headers, updated Android metadata to `ANDROID_VERSION_NAME=8.36.0` and `ANDROID_VERSION_CODE=208`, and refreshed prerelease links.
- RU: Выполнен SemVer minor-бамп версии по репозиторию до `8.36.0`; синхронизированы runtime/config/docs/version-заголовки, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.36.0` и `ANDROID_VERSION_CODE=208`, а также обновлены prerelease-ссылки.

## [8.35.1] - 2026-03-28

### Fixed / Исправлено
- EN: Fixed `scripts/android_post_pull_build_run.ps1` for flavor-based Android builds: script now builds/installs an explicit flavor (`compactOps` by default), avoids ambiguous `installDebug`, and uses the corresponding package ID for launch.
- RU: Исправлен `scripts/android_post_pull_build_run.ps1` для flavor-сборок Android: скрипт теперь собирает/ставит конкретный flavor (`compactOps` по умолчанию), убирает неоднозначный `installDebug` и использует соответствующий package ID для запуска.
- EN: Updated `scripts/publish_android_prerelease.ps1` to support explicit flavor selection for Gradle assemble tasks and APK lookup, preventing incorrect artifact resolution in multi-flavor outputs.
- RU: Обновлён `scripts/publish_android_prerelease.ps1`: добавлен явный выбор flavor для Gradle assemble-задач и поиска APK, что убирает ошибки выбора артефакта при нескольких flavor.

### Changed / Изменено
- EN: Completed repository-wide patch bump to `8.35.1`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.35.1` and `ANDROID_VERSION_CODE=207`, and refreshed prerelease links.
- RU: Выполнен полный patch-бамп версии по репозиторию до `8.35.1`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.35.1` и `ANDROID_VERSION_CODE=207`, а также обновлены prerelease-ссылки.

## [8.35.0] - 2026-03-28

### Added / Добавлено
- EN: Added Android product flavor split for parallel UI development in one branch: `legacy` (current app) and `compactOps` (new Variant A — Compact Ops Hub), including separate install IDs and app labels.
- RU: Добавлено разделение Android-приложения на product flavor для параллельной разработки UI в одной ветке: `legacy` (текущий вариант) и `compactOps` (новый Вариант A — Compact Ops Hub), включая раздельные install ID и названия приложения.
- EN: Added implementation and rollout guide `docs/android_compact_ops_hub_plan.md` with step-by-step Android Studio switching instructions for Build Variants.
- RU: Добавлен гайд по реализации и раскатке `docs/android_compact_ops_hub_plan.md` с пошаговой инструкцией переключения Build Variants в Android Studio.

### Changed / Изменено
- EN: Implemented initial Compact Ops Hub visual layer in Android app: dense top layout, Ops Snapshot block, compact quick actions, and adaptive spacing controlled by `BuildConfig.IS_COMPACT_OPS_HUB` while preserving full legacy behavior.
- RU: Реализован стартовый визуальный слой Compact Ops Hub в Android-приложении: плотная верхняя компоновка, блок Ops Snapshot, компактные быстрые действия и адаптивные отступы через `BuildConfig.IS_COMPACT_OPS_HUB` при полном сохранении legacy-поведения.
- EN: Completed repository-wide SemVer minor bump to `8.35.0`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.35.0` and `ANDROID_VERSION_CODE=206`, and aligned prerelease links.
- RU: Выполнен SemVer minor-бамп версии по репозиторию до `8.35.0`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.35.0` и `ANDROID_VERSION_CODE=206`, а также выровнены prerelease-ссылки.
## [8.33.87] - 2026-03-28

### Added / Добавлено
- EN: Added `docs/android_ui_concepts.md` with three Android interface concepts and accompanying SVG mockups: Dashboard Cards, Server List + Filters, and Incident Timeline.
- RU: Добавлен `docs/android_ui_concepts.md` с тремя концептами Android-интерфейса и SVG-макетами: Dashboard Cards, Server List + Filters и Incident Timeline.

### Fixed / Исправлено
- EN: Implemented Android resource-threshold editing in extension settings (`Settings → Extensions → Open extension settings → Resources`): taps on `CPU warning/critical`, `RAM warning/critical`, `Disk warning/critical` now open input dialogs and submit value payloads.
- RU: Реализовано редактирование порогов ресурсов в Android-настройках расширений (`Настройки → Расширения → Открыть настройки расширений → Ресурсы`): нажатия `CPU предупреждение/критический`, `RAM предупреждение/критический`, `Disk предупреждение/критический` теперь открывают диалог ввода и отправляют значение порога.
- EN: Added backend handling for `set_cpu_*|value`, `set_ram_*|value`, `set_disk_*|value` in mobile Control API, with validation (0-100), settings persistence, and refreshed threshold summary/menu in response.
- RU: Добавлена серверная обработка `set_cpu_*|value`, `set_ram_*|value`, `set_disk_*|value` в mobile Control API с валидацией (0-100), сохранением настроек и возвратом обновлённой сводки/меню порогов.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.87`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.87` and `ANDROID_VERSION_CODE=204`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.87`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.87` и `ANDROID_VERSION_CODE=204`, а также выровнены prerelease-ссылки.

## [8.33.84] - 2026-03-27

### Fixed / Исправлено
- EN: Added local Android extension settings submenu for Resources (`Settings → Extensions → Open extension settings → Resources`) with the same threshold actions as in Telegram bot: `CPU warning`, `CPU critical`, `RAM warning`, `RAM critical`, `Disk warning`, `Disk critical`.
- RU: Добавлено локальное подменю Android-настроек расширений для «Ресурсов» (`Настройки → Расширения → Открыть настройки расширений → Ресурсы`) с теми же пороговыми действиями, что и в Telegram-боте: `CPU предупреждение`, `CPU критический`, `RAM предупреждение`, `RAM критический`, `Disk предупреждение`, `Disk критический`.
- EN: Updated Android routing for resource-threshold actions so `set_cpu_*`, `set_ram_*`, `set_disk_*` commands are sent through Control API and behave consistently with bot callbacks.
- RU: Обновлена маршрутизация Android для действий порогов ресурсов: команды `set_cpu_*`, `set_ram_*`, `set_disk_*` отправляются через Control API и работают консистентно с callback’ами бота.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.84`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.84` and `ANDROID_VERSION_CODE=201`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.84`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.84` и `ANDROID_VERSION_CODE=201`, а также выровнены prerelease-ссылки.

## [8.33.82] - 2026-03-27

### Added / Добавлено
- EN: Added full ZFS host management in Android/Web extension settings (`Settings → Extensions → Open extension settings → ZFS → Hosts`): host list now includes edit/delete/enable-toggle actions, and add/rename flows are available from Android dialogs via action payloads.
- RU: Добавлено полноценное управление ZFS-хостами в Android/Web (`Настройки → Расширения → Открыть настройки расширений → ZFS → Хосты`): в списке появились действия редактирования/удаления/переключения, а добавление и переименование работают через Android-диалоги с payload-действиями.
- EN: Added ZFS patterns management in Android/Web extension settings (`Settings → Extensions → Open extension settings → ZFS → Patterns`): list with statuses, enable/disable, delete, and add/edit actions now work similarly to Telegram-bot behavior.
- RU: Добавлено управление ZFS-паттернами в Android/Web (`Настройки → Расширения → Открыть настройки расширений → ZFS → Паттерны`): теперь работают список со статусами, включение/выключение, удаление и действия добавления/редактирования по аналогии с поведением Telegram-бота.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.82`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.82` and `ANDROID_VERSION_CODE=199`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.82`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.82` и `ANDROID_VERSION_CODE=199`, а также выровнены prerelease-ссылки.

## [8.33.78] - 2026-03-26

### Fixed / Исправлено
- EN: Implemented working DB backup settings actions in Android/Web extension settings, synchronized with Telegram-bot data sources: `📋 View all DBs` now returns actual `DATABASE_CONFIG`, and `🔍 DB patterns` now shows real records from `backup_patterns` with enable/disable, edit, and disable-as-delete actions.
- RU: Реализованы рабочие действия настроек бэкапов БД в Android/Web с синхронизацией по тем же источникам, что и в Telegram-боте: `📋 Просмотр всех БД` теперь отдаёт реальный `DATABASE_CONFIG`, а `🔍 Паттерны БД` показывает записи из `backup_patterns` с включением/выключением, редактированием и «удалением» через отключение.
- EN: Improved Android pattern-add dialog trigger for extension settings: action `settings_proxmox_pattern_add|...` now correctly opens the input form with prefilled category/type, enabling DB-pattern creation flow from `🔍 DB patterns`.
- RU: Улучшен триггер Android-диалога добавления паттерна: действие `settings_proxmox_pattern_add|...` теперь корректно открывает форму с предзаполненной категорией/типом, что включает сценарий добавления DB-паттерна из `🔍 Паттерны БД`.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.78`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.78` and `ANDROID_VERSION_CODE=195`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.78`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.78` и `ANDROID_VERSION_CODE=195`, а также выровнены prerelease-ссылки.

## [8.33.77] - 2026-03-26

### Fixed / Исправлено
- EN: Fixed Android extension settings routing for DB backups (`Settings → Extensions → Open extension settings → DB backups`): `settings_*` actions are now handled by Extensions Settings API, so submenu items `📋 Databases` and `🔍 Patterns` open correctly (aligned with Telegram bot behavior).
- RU: Исправлена маршрутизация настроек расширений Android для бэкапов БД (`Настройки → Расширения → Открыть настройки расширений → Бэкапы БД`): действия `settings_*` теперь обрабатываются через Extensions Settings API, поэтому подпункты `📋 Базы` и `🔍 Паттерны` открываются корректно (вровень с поведением Telegram-бота).

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.77`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.77` and `ANDROID_VERSION_CODE=194`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.77`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.77` и `ANDROID_VERSION_CODE=194`, а также выровнены prerelease-ссылки.

## [8.33.76] - 2026-03-26

### Fixed / Исправлено
- EN: Fixed Android extension-settings routing for database backup section (`Settings → Extensions → Open extension settings → DB backups`): all `settings_*` actions are now sent through Control API, so submenu buttons `📋 Databases` and `🔍 Patterns` open and work the same way as in Telegram bot.
- RU: Исправлена маршрутизация Android-настроек расширений для раздела бэкапов БД (`Настройки → Расширения → Открыть настройки расширений → Бэкапы БД`): все действия `settings_*` теперь отправляются через Control API, поэтому подпункты `📋 Базы` и `🔍 Паттерны` открываются и работают так же, как в Telegram-боте.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.76`; synchronized project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.76` and `ANDROID_VERSION_CODE=193`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.76`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.76` и `ANDROID_VERSION_CODE=193`, а также выровнены prerelease-ссылки.

## [8.33.72] - 2026-03-26

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.72`; synchronized all project/runtime/docs references, updated Android metadata to `ANDROID_VERSION_NAME=8.33.72` and `ANDROID_VERSION_CODE=189`, and aligned prerelease links.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.72`; синхронизированы ссылки на версию в проекте/runtime/docs, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.72` и `ANDROID_VERSION_CODE=189`, а также выровнены prerelease-ссылки.

## [8.33.71] - 2026-03-26

### Fixed / Исправлено
- EN: Added full Proxmox pattern list support for Android/Web extension settings path (`Settings → Extensions → Open extension settings → Proxmox backups → Patterns`): the menu now shows actual patterns from `backup_patterns` instead of an empty placeholder and provides persisted actions for enable/disable and delete.
- RU: Добавлена полноценная работа списка Proxmox-паттернов для Android/Web в цепочке (`Настройки → Расширения → Открыть настройки расширений → Бэкапы Proxmox → Паттерны`): вместо пустой заглушки теперь показываются реальные паттерны из `backup_patterns`, а также доступны сохраняемые действия включения/выключения и удаления.

### Changed / Изменено
- EN: Completed patch version bump to `8.33.71`; updated Android metadata to `ANDROID_VERSION_NAME=8.33.71` and `ANDROID_VERSION_CODE=188`, and synchronized Android prerelease link in README.
- RU: Выполнен патч-бамп версии до `8.33.71`; обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.71` и `ANDROID_VERSION_CODE=188`, а также синхронизирована ссылка на Android prerelease в README.

## [8.33.70] - 2026-03-26

### Fixed / Исправлено
- EN: Fixed stale Proxmox host visibility in backup menus after disabling a host in settings (`Settings → Extensions → Proxmox backups → Hosts` in Telegram and Android extension settings): host list resolution now reads `PROXMOX_HOSTS` from runtime settings via `core.config_manager` with `use_cache=False`, so disabled hosts no longer remain in the “Proxmox backups” menu.
- RU: Исправлено «залипание» отключённых Proxmox-хостов в меню бэкапов после выключения хоста в настройках (`Настройки → Расширения → Бэкапы Proxmox → Хосты` в Telegram и Android): получение списка хостов теперь берёт `PROXMOX_HOSTS` из runtime-настроек через `core.config_manager` с `use_cache=False`, поэтому отключённые хосты больше не остаются в меню «Бэкапы Proxmox».

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.70`; synchronized runtime/config/docs/Android references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.70` and `ANDROID_VERSION_CODE=187`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.70`; синхронизированы ссылки в runtime/config/docs/Android и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.70` и `ANDROID_VERSION_CODE=187`.

## [8.33.65] - 2026-03-26

### Fixed / Исправлено
- EN: Fixed Proxmox hosts counter in Android path `Settings → Extensions → Open extension settings → Proxmox backups`: host source resolution now supports JSON/Python string payloads (including legacy dict literals) and additionally falls back to runtime `config.db_settings.PROXMOX_HOSTS`, so valid configured hosts are no longer shown as `0`.
- RU: Исправлен счётчик Proxmox-хостов в Android-цепочке `Настройки → Расширения → Открыть настройки расширений → Бэкапы Proxmox`: источник хостов теперь корректно обрабатывает JSON/Python-строку (включая legacy-формат) и дополнительно использует runtime `config.db_settings.PROXMOX_HOSTS`, поэтому при реальной конфигурации больше не показывается `0`.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.65`; synchronized runtime/config/docs/Android references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.65` and `ANDROID_VERSION_CODE=182`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.65`; синхронизированы ссылки в runtime/config/docs/Android и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.65` и `ANDROID_VERSION_CODE=182`.

## [8.33.60] - 2026-03-23

### Fixed / Исправлено
- EN: Improved DB backup status response clarity: when there are failures, the summary now includes explicit names of problematic databases (`db_name (backup_type)`), so operators can immediately see which backup failed without opening each item.
- RU: Улучшена понятность статуса бэкапов БД: при наличии сбоев в сводке теперь выводятся явные имена проблемных баз (`db_name (backup_type)`), чтобы сразу было видно, какой бэкап не прошёл, без перебора всех пунктов.
- EN: DB backup menu options are now status-marked by name (`✅` for healthy and `🚨` for problematic), making failed database buttons instantly visible in Android.
- RU: Пункты меню бэкапов БД теперь помечаются статусом прямо в названии (`✅` для нормальных и `🚨` для проблемных), поэтому нужная «падающая» база сразу видна в Android.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.60`; synchronized runtime/config/docs/Android references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.60` and `ANDROID_VERSION_CODE=177`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.60`; синхронизированы ссылки в runtime/config/docs/Android и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.60` и `ANDROID_VERSION_CODE=177`.

## [8.33.55] - 2026-03-22

### Fixed / Исправлено
- EN: Expanded Android problematic-backup button highlighting in “💾 Proxmox Backups” and “🗃️ DB Backups”: menu items are now marked with error colors when labels contain `❌`, `⚠️`, `🚨`, `🆘`, `⛔`, `🔴`, `🟠`, or `⚪` anywhere in text; problematic items also receive a `🚨` prefix for extra contrast.
- RU: Расширено выделение кнопок проблемных бэкапов в Android-разделах «💾 Бэкапы Proxmox» и «🗃️ Бэкапы БД»: пункты меню теперь подсвечиваются error-цветами, если в тексте есть `❌`, `⚠️`, `🚨`, `🆘`, `⛔`, `🔴`, `🟠` или `⚪`; для дополнительного акцента проблемным пунктам добавляется префикс `🚨`.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.55`; synchronized runtime/config/docs/Android references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.55` and `ANDROID_VERSION_CODE=173`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.55`; синхронизированы ссылки в runtime/config/docs/Android и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.55` и `ANDROID_VERSION_CODE=173`.

## [8.33.53] - 2026-03-22

### Fixed / Исправлено
- EN: In the Android app, problematic backup buttons are now visually highlighted in the “💾 Proxmox Backups” and “🗃️ DB Backups” menus (for items starting with `❌`, `⚠️`, or `🚨`) using error-container colors.
- RU: В Android-приложении визуально выделены кнопки проблемных бэкапов в меню «💾 Бэкапы Proxmox» и «🗃️ Бэкапы БД» (для пунктов, начинающихся с `❌`, `⚠️` или `🚨`) через error-цвета.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.53`; synchronized runtime/config/docs/Android references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.53` and `ANDROID_VERSION_CODE=171`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.53`; синхронизированы ссылки в runtime/config/docs/Android и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.53` и `ANDROID_VERSION_CODE=171`.

## [8.33.52] - 2026-03-22

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.52`; synchronized all runtime/config/docs/Android version references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.52` and `ANDROID_VERSION_CODE=170`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.52`; синхронизированы ссылки на версию в runtime/config/docs/Android, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.52` и `ANDROID_VERSION_CODE=170`.

## [8.33.51] - 2026-03-22

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.51`; synchronized all current Android/app/docs version references and updated Android metadata to `ANDROID_VERSION_NAME=8.33.51` and `ANDROID_VERSION_CODE=169`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.51`; синхронизированы все актуальные ссылки на версию в Android/app/docs, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.51` и `ANDROID_VERSION_CODE=169`.

## [8.33.50] - 2026-03-22

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.50`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.50` and `ANDROID_VERSION_CODE=168`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.50`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.50` и `ANDROID_VERSION_CODE=168`.

## [8.33.49] - 2026-03-22

### Fixed / Исправлено
- EN: Fixed Android action routing for the “🗃️ DB Backups” button: `backup_databases` now uses the control-action endpoint (`/v1/control/action`) instead of extension actions (`/v1/settings/extensions/actions`), which prevents HTTP 400 responses when opening the DB backups menu.
- RU: Исправлена маршрутизация действий Android для кнопки «🗃️ Бэкапы БД»: `backup_databases` теперь отправляется в control-action endpoint (`/v1/control/action`), а не в extension actions (`/v1/settings/extensions/actions`), из-за чего убраны HTTP 400 при открытии меню бэкапов БД.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.49`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.49` and `ANDROID_VERSION_CODE=167`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.49`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.49` и `ANDROID_VERSION_CODE=167`.

## [8.33.48] - 2026-03-21

### Changed / Изменено
- EN: Updated Android main menu layout in the “System section”: “Management” and “Settings” buttons are now rendered in one horizontal row (two-column flow), consistent with the “Quick actions” block style.
- RU: Обновлён layout главного меню Android в «Разделе системы»: кнопки «Управление» и «Настройки» теперь отображаются в один горизонтальный ряд (двухколоночный flow), в стиле блока «Быстрые действия».
- EN: Completed repository-wide patch version bump to `8.33.48`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.48` and `ANDROID_VERSION_CODE=166`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.48`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.48` и `ANDROID_VERSION_CODE=166`.

## [8.33.47] - 2026-03-21

### Fixed / Исправлено
- EN: Fixed Android debug build compilation in `MainActivity.kt`: corrected `PaddingValues` import to `androidx.compose.foundation.layout.PaddingValues`, eliminating unresolved reference errors in `:app:compileDebugKotlin`.
- RU: Исправлена компиляция Android debug-сборки в `MainActivity.kt`: импорт `PaddingValues` заменён на `androidx.compose.foundation.layout.PaddingValues`, из-за чего исчезли ошибки unresolved reference в `:app:compileDebugKotlin`.

### Changed / Изменено
- EN: Refined Android main menu layout: moved “Management” and “Settings” buttons into a dedicated “System section” card to visually separate core controls from checks/extensions.
- RU: Доработан layout главного меню Android: кнопки «Управление» и «Настройки» вынесены в отдельную карточку «Раздел системы», чтобы визуально отделить базовое управление от проверок/расширений.
- EN: Made extension buttons more compact on Android by switching them to a two-column flow with reduced internal paddings and single-line labels.
- RU: Сделаны более компактные кнопки расширений в Android: переведены в двухколоночный flow с уменьшенными внутренними отступами и однострочными подписями.
- EN: Completed repository-wide patch version bump to `8.33.47`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.47` and `ANDROID_VERSION_CODE=165`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.47`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.47` и `ANDROID_VERSION_CODE=165`.

## [8.33.45] - 2026-03-21

### Fixed / Исправлено
- EN: Fixed Android debug build failure in `MainActivity.kt`: removed direct import of `foundation.layout.weight`, which started resolving to an internal API in newer Compose; existing `Modifier.weight(...)` usage now resolves correctly from layout scopes and `:app:compileDebugKotlin` succeeds.
- RU: Исправлен падёж Android debug-сборки в `MainActivity.kt`: убран прямой импорт `foundation.layout.weight`, который в новых версиях Compose начал резолвиться во внутренний API; существующие вызовы `Modifier.weight(...)` теперь корректно берутся из layout-скоупов, и `:app:compileDebugKotlin` проходит.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.45`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.45` and `ANDROID_VERSION_CODE=163`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.45`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.45` и `ANDROID_VERSION_CODE=163`.

## [8.33.44] - 2026-03-21

### Changed / Изменено
- EN: Improved Android main-screen action layout for better ergonomics: quick actions and server checks are now grouped into compact two-column button rows with clear section headers, reducing vertical clutter and making frequent taps easier.
- RU: Улучшена компоновка действий на главном экране Android: быстрые действия и проверки серверов сгруппированы в компактные двухколоночные ряды кнопок с явными заголовками секций, что уменьшает «простыню» по высоте и упрощает частые нажатия.
- EN: Completed repository-wide patch version bump to `8.33.44`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.44` and `ANDROID_VERSION_CODE=162`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.44`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.44` и `ANDROID_VERSION_CODE=162`.

## [8.33.43] - 2026-03-21

### Fixed / Исправлено
- EN: Reworked morning/manual monitoring report layout to be compact and readable: removed bloated `Metric | Value` headers, server availability now renders as a short key/value table, and backup/1C/ZFS blocks are normalized into concise fixed-width sections.
- RU: Переработан утренний/ручной отчёт мониторинга в компактный и читаемый вид: убраны раздутые заголовки `Показатель | Значение`, доступность серверов теперь выводится короткой key/value-таблицей, а блоки бэкапов/1С/ZFS нормализованы в лаконичные секции фиксированной ширины.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.43`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.43` and `ANDROID_VERSION_CODE=161`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.43`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.43` и `ANDROID_VERSION_CODE=161`.

## [8.33.40] - 2026-03-21

### Fixed / Исправлено
- EN: Fixed morning manual report generation for backup sections: summary builder now gracefully handles missing backup tables (`proxmox_backups`, `database_backups`) and returns partial status instead of aborting the whole backup block with “report generation error”.
- RU: Исправлено формирование утреннего ручного отчёта в секции бэкапов: сборщик сводки теперь корректно обрабатывает отсутствие таблиц бэкапов (`proxmox_backups`, `database_backups`) и возвращает частичный статус вместо падения всего блока с ошибкой «Ошибка формирования отчета о бэкапах».

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.40`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.40` and `ANDROID_VERSION_CODE=158`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.40`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.40` и `ANDROID_VERSION_CODE=158`.

## [8.33.39] - 2026-03-20

### Fixed / Исправлено
- EN: Fixed Proxmox host actions in mobile extension settings (`/v1/settings/extensions/actions`): host names are now extracted from the original callback value (without forced lowercasing), so edit/delete/toggle actions correctly target the same host keys as in Telegram bot flows.
- RU: Исправлены действия с Proxmox-хостами в mobile-настройках расширений (`/v1/settings/extensions/actions`): имя хоста теперь берётся из исходного callback без принудительного lower-case, поэтому edit/delete/toggle корректно работают с теми же ключами хостов, что и в Telegram-боте.
- EN: Improved Proxmox host list source fallback for Android/web settings: when app-specific settings storage returns an empty value, backend additionally checks the shared config manager store before falling back to static defaults, preventing false “Hosts not configured” screens.
- RU: Улучшен fallback-источник списка Proxmox-хостов для Android/web-настроек: если app-хранилище настроек вернуло пусто, backend дополнительно проверяет общее хранилище config manager до fallback на статические defaults, что убирает ложный экран «Хосты не настроены».

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.39`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.39` and `ANDROID_VERSION_CODE=157`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.39`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.39` и `ANDROID_VERSION_CODE=157`.

## [8.33.36] - 2026-03-20

### Fixed / Исправлено
- EN: Fixed Android extension-settings action routing for Proxmox backups: in Settings → Extensions → Open extension settings, buttons now prioritize backend callback data over legacy action aliases, so “Hosts → Host list” opens the real Proxmox host list (Telegram-parity flow) instead of looping to a generic screen with “Hosts not configured.”
- RU: Исправлена маршрутизация действий в Android-настройках расширений для бэкапов Proxmox: в Настройки → Расширения → Открыть настройки расширений кнопки теперь в приоритете используют backend callback data вместо legacy action-алиасов, поэтому «Хосты → Список хостов» открывает реальный список Proxmox-хостов (как в Telegram), а не уводит на общий экран с «Хосты не настроены».

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.36`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.36` and `ANDROID_VERSION_CODE=155`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.36`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.36` и `ANDROID_VERSION_CODE=155`.
## [8.33.32] - 2026-03-19

### Fixed / Исправлено
- EN: Fixed Android extension settings for Proxmox backups: the “Hosts” screen no longer renders the monitoring-servers management list and now relies on backend Proxmox-host actions/menu responses.
- RU: Исправлены настройки расширения бэкапов Proxmox в Android: экран «Хосты» больше не показывает список управления серверами мониторинга и теперь использует backend-меню/действия именно для Proxmox-хостов.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.32`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.32` and `ANDROID_VERSION_CODE=151`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.32`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.32` и `ANDROID_VERSION_CODE=151`.

## [8.33.31] - 2026-03-19

### Added / Добавлено
- EN: Added a host-management list in Android Settings → Extensions → Open extension settings → Proxmox backups → Hosts with Telegram-like actions: disable/enable monitoring, edit host, and delete host.
- RU: Добавлен список управления хостами в Android Настройки → Расширения → Открыть настройки расширений → Бэкапы Proxmox → Хосты с действиями как в Telegram: отключить/включить наблюдение, редактировать хост и удалить хост.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.31`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.31` and `ANDROID_VERSION_CODE=150`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.31`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.31` и `ANDROID_VERSION_CODE=150`.

## [8.33.30] - 2026-03-19

### Changed / Изменено
- EN: Synchronized project version references across Python modules, docs, and Android client to `8.33.30` to remove version drift.
- RU: Синхронизированы ссылки на версию проекта в Python-модулях, документации и Android-клиенте до `8.33.30`, чтобы устранить рассинхрон версий.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.33.30` and `ANDROID_VERSION_CODE=149`.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.33.30` и `ANDROID_VERSION_CODE=149`.

## [8.33.29] - 2026-03-19
- EN: Fixed Android extension-settings callback flow to match Telegram behavior: removed local placeholder submenu actions and normalized legacy local action aliases to real backend callbacks (`settings_backup_proxmox`, `settings_db_main`, etc.), so nested buttons now trigger server-side actions instead of HTTP 400.
- RU: Исправлен callback-флоу настроек расширений в Android под поведение Telegram: убраны локальные заглушки подменю и добавлена нормализация устаревших локальных action-алиасов в реальные backend-callback’и (`settings_backup_proxmox`, `settings_db_main` и т.д.), поэтому вложенные кнопки теперь запускают серверные действия без HTTP 400.
- EN: Extended `/v1/settings/extensions/actions` to handle nested extension settings callbacks (`settings_zfs_toggle_*`, `settings_zfs_edit_name_*`, `settings_zfs_delete_*`, `settings_db_*`, `supplier_stock_*`) with actionable responses instead of `INVALID_ACTION`.
- RU: Расширен `/v1/settings/extensions/actions` поддержкой вложенных callback’ов настроек расширений (`settings_zfs_toggle_*`, `settings_zfs_edit_name_*`, `settings_zfs_delete_*`, `settings_db_*`, `supplier_stock_*`) с рабочими ответами вместо `INVALID_ACTION`.
- EN: Completed repository-wide patch version bump to `8.33.29`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.29`, `ANDROID_VERSION_CODE=148`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.29`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.29`, `ANDROID_VERSION_CODE=148`.

## [8.33.28] - 2026-03-19

### Fixed / Исправлено
- EN: Fixed Android Settings → Extensions → “Open extension settings”: nested buttons now return actionable server-driven menus (including Proxmox Hosts flow and child actions), matching Telegram bot behavior instead of static status-only responses.
- RU: Исправлен экран Android Настройки → Расширения → «Открыть настройки расширений»: вложенные кнопки теперь получают рабочие серверные меню (включая сценарий Proxmox → Хосты и дочерние действия) по аналогии с Telegram-ботом, а не статичные ответы-статусы.
- EN: Extended Android API model for `/v1/settings/extensions/actions` to consume `menu_options`, so nested extension settings menus can update dynamically after each callback action.
- RU: Расширена Android API-модель для `/v1/settings/extensions/actions` с поддержкой `menu_options`, чтобы вложенные меню настроек расширений динамически обновлялись после каждого callback-действия.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.28`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.28`, `ANDROID_VERSION_CODE=147`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.28`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.28`, `ANDROID_VERSION_CODE=147`.

## [8.33.24] - 2026-03-19

### Fixed / Исправлено
- EN: Fixed Android Settings → Extensions → “Open extension settings”: this screen now always builds buttons from active extensions settings actions (`settings_*`) and no longer shows extension actions from the main menu.
- RU: Исправлен сценарий Android Настройки → Расширения → «Открыть настройки расширений»: экран теперь всегда строит кнопки из действий настроек активных расширений (`settings_*`) и больше не подтягивает действия расширений из главного меню.
- EN: Fixed `/v1/settings/extensions/actions` behavior for extension settings root callbacks (`settings_ext_*`, `settings_zfs`): backend now returns extension-settings responses instead of forwarding these callbacks to main extension menu actions.
- RU: Исправлено поведение `/v1/settings/extensions/actions` для корневых callback’ов настроек расширений (`settings_ext_*`, `settings_zfs`): backend теперь возвращает ответы настроек расширений вместо прокидывания в действия главного меню расширений.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.24`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.24`, `ANDROID_VERSION_CODE=143`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.24`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.24`, `ANDROID_VERSION_CODE=143`.

## [8.33.20] - 2026-03-19

### Fixed / Исправлено
- EN: Fixed HTTP 400 in Android Settings → Extensions → “Open extensions settings”: backend endpoint `/v1/settings/extensions/actions` now supports extension-settings callbacks (`settings_ext_*`, `settings_zfs`, `settings_resources`) and returns proper action results.
- RU: Исправлен HTTP 400 в Android Настройки → Расширения → «Открыть настройки расширений»: backend endpoint `/v1/settings/extensions/actions` теперь поддерживает callback’и настроек расширений (`settings_ext_*`, `settings_zfs`, `settings_resources`) и возвращает корректные результаты действий.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.20`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.20`, `ANDROID_VERSION_CODE=140`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.20`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.20`, `ANDROID_VERSION_CODE=140`.
- EN: Synchronized leftover `8.33.18` references across runtime banners, config constants, scripts, and docs to eliminate partial version drift.
- RU: Синхронизированы оставшиеся ссылки `8.33.18` в runtime-баннерах, константах конфигурации, скриптах и документации, чтобы убрать частичный рассинхрон версии.

## [8.33.18] - 2026-03-18

### Fixed / Исправлено
- EN: Fixed Android Settings → Extensions → “Open extensions settings”: fallback buttons now open extension **settings** callbacks (`settings_*`) instead of duplicating extension actions from the main menu.
- RU: Исправлен сценарий Android Настройки → Расширения → «Открыть настройки расширений»: fallback-кнопки теперь открывают именно callback-настройки расширений (`settings_*`), а не дублируют действия расширений из главного меню.
- EN: In extension-settings flow, filtered out main-menu extension actions (`backup_hosts`, `backup_databases`, `backup_mail`, `backup_stock_loads`, `supplier_stock_reports`, `zfs_menu`, etc.) so this section contains only settings-related actions.
- RU: В сценарии настроек расширений отфильтрованы действия расширений из главного меню (`backup_hosts`, `backup_databases`, `backup_mail`, `backup_stock_loads`, `supplier_stock_reports`, `zfs_menu` и др.), чтобы в этом блоке оставались только действия, относящиеся к настройкам.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.18`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.18`, `ANDROID_VERSION_CODE=138`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.18`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.18`, `ANDROID_VERSION_CODE=138`.

## [8.33.13] - 2026-03-18

### Fixed / Исправлено
- EN: Updated Android Settings → "Extensions": extension enable/disable list is now always visible in this section, independent of the extension-settings menu state.
- RU: Обновлён раздел Android Настройки → «Расширения»: список включения/выключения расширений теперь всегда виден в этом разделе и не зависит от состояния меню настроек расширений.
- EN: Fixed "⚙️ Open extensions settings" flow to load and show settings buttons for active extensions only.
- RU: Исправлен сценарий «⚙️ Открыть настройки расширений»: теперь загружается и показывается список кнопок настроек только для активных расширений.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.13`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.13`, `ANDROID_VERSION_CODE=133`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.13`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.13`, `ANDROID_VERSION_CODE=133`.

## [8.33.12] - 2026-03-18

### Fixed / Исправлено
- EN: Fixed Android Extensions settings behavior: after tapping "⚙️ Open extensions settings", the section now actually expands and displays extension controls (enable/disable and bulk actions).
- RU: Исправлено поведение настроек расширений в Android: после нажатия «⚙️ Открыть настройки расширений» раздел теперь действительно раскрывается и показывает управление расширениями (вкл/выкл и массовые действия).

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.12`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.12`, `ANDROID_VERSION_CODE=132`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.12`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.12`, `ANDROID_VERSION_CODE=132`.

## [8.33.10] - 2026-03-18

### Fixed / Исправлено
- EN: Restored extension toggles list in Android Settings → "Extensions": enable/disable controls are shown immediately after opening this section again.
- RU: Возвращён список управления расширениями в Android (Настройки → «Расширения»): переключатели вкл/выкл снова отображаются сразу при входе в раздел.
- EN: Fixed "⚙️ Open extensions settings" behavior: the button now opens only extension settings actions/menu and no longer hides extension toggle controls.
- RU: Исправлено поведение «⚙️ Открыть настройки расширений»: кнопка теперь открывает именно меню настроек расширений и больше не скрывает блок управления включением/выключением расширений.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.10`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.10`, `ANDROID_VERSION_CODE=130`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.10`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.10`, `ANDROID_VERSION_CODE=130`.

## [8.33.9] - 2026-03-18

### Fixed / Исправлено
- EN: Improved Android Extensions settings UX: the "⚙️ Open extensions settings" button now works as a real open/close toggle for the extensions settings block (Telegram-like behavior) instead of only showing a status text.
- RU: Улучшен UX настроек расширений в Android: кнопка «⚙️ Открыть настройки расширений» теперь работает как реальный тумблер открытия/скрытия блока настроек расширений (поведение как в Telegram), а не только выводит статусный текст.
- EN: Removed duplicate top-level "🛠️ Extensions" button from Android main menu to avoid duplicated navigation.
- RU: Удалена дублирующая верхнеуровневая кнопка «🛠️ Расширения» из главного меню Android, чтобы убрать дубли навигации.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.9`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.9`, `ANDROID_VERSION_CODE=129`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.9`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.9`, `ANDROID_VERSION_CODE=129`.

## [8.33.7] - 2026-03-18

### Fixed / Исправлено
- EN: Fixed Android extensions settings flow: in Settings, the app now has a dedicated "Extensions settings" entry that opens extension configuration callbacks (Telegram-bot style) instead of duplicating the main-menu extension actions.
- RU: Исправлен сценарий настроек расширений в Android: в «Настройках» добавлен отдельный вход в «Настройки расширений», который открывает callback-настройки расширений (как в Telegram-боте), а не дублирует действия из главного меню.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.7`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.7`, `ANDROID_VERSION_CODE=127`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.7`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.7`, `ANDROID_VERSION_CODE=127`.

## [8.33.5] - 2026-03-18

### Fixed / Исправлено
- EN: Fixed Android settings navigation layout: section buttons now wrap to a new line on narrow screens, so the "Extensions" button is always visible and accessible.
- RU: Исправлена вёрстка навигации разделов в настройках Android: кнопки теперь переносятся на новую строку на узких экранах, поэтому кнопка «Расширения» всегда видна и доступна.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.5`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.5`, `ANDROID_VERSION_CODE=125`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.5`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.5`, `ANDROID_VERSION_CODE=125`.

## [8.33.4] - 2026-03-18

### Fixed / Исправлено
- EN: Added an "Extensions" section inside Android app settings to match Telegram-bot workflow: users can now manage extension toggles and run extension actions directly from settings.
- RU: В настройки Android-приложения добавлен раздел «Расширения» для паритета с Telegram-ботом: теперь из настроек можно включать/выключать расширения и запускать их действия.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.4`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.4`, `ANDROID_VERSION_CODE=124`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.4`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.4`, `ANDROID_VERSION_CODE=124`.

## [8.33.3] - 2026-03-18

### Fixed / Исправлено
- EN: Fixed IEK JSON processing to build the `orig` output using warehouse keys from saved source settings (`iek_json.stores`) instead of hardcoded legacy warehouse columns.
- RU: Исправлена обработка IEK JSON: `orig`-файл теперь строится по ключам складов из сохранённых настроек источника (`iek_json.stores`), а не по зашитому legacy-набору колонок.
- EN: Fixed supplier stock totals behavior for custom IEK warehouse sets by reusing configured warehouse keys in row generation, so newly added warehouses are included in processing results.
- RU: Исправлено поведение суммарных остатков для кастомных наборов складов IEK: при формировании строк используются настроенные ключи складов, поэтому новые склады попадают в результаты обработки.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.3`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.3`, `ANDROID_VERSION_CODE=123`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.3`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.3`, `ANDROID_VERSION_CODE=123`.

## [8.33.2] - 2026-03-17

### Fixed / Исправлено
- EN: Fixed Android forced-update action: when API returns a broken GitHub URL or legacy missing asset path, the app now falls back to `https://github.com/sukhanovai/monitoring/releases/latest` instead of opening GitHub 404.
- RU: Исправлено действие принудительного обновления в Android: если API возвращает битую GitHub-ссылку или legacy-путь к отсутствующему asset, приложение теперь использует fallback `https://github.com/sukhanovai/monitoring/releases/latest` вместо перехода на GitHub 404.
- EN: Updated backend default `ANDROID_APK_DOWNLOAD_URL` to GitHub latest releases page, so default server configuration points users to a valid update location.
- RU: Обновлён backend-default `ANDROID_APK_DOWNLOAD_URL` на страницу последних релизов GitHub, чтобы стандартная конфигурация сервера вела пользователя в валидное место обновления.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.2`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.2`, `ANDROID_VERSION_CODE=122`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.2`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.2`, `ANDROID_VERSION_CODE=122`.
## [8.33.0] - 2026-03-17

### Fixed / Исправлено
- EN: Implemented Android parity for the "📦 Результаты остатков поставщиков" button: actions now route through `/v1/control/actions` and open supplier stock reports with Telegram-like daily summary (download/mail groups, per-source statuses, quick source navigation).
- RU: Реализован паритет Android для кнопки «📦 Результаты остатков поставщиков»: действия теперь идут через `/v1/control/actions` и открывают отчёты остатков поставщиков в логике Telegram (группы скачивание/почта, статусы по источникам, быстрый переход в историю источника).
- EN: Added mobile control handlers for `supplier_stock_reports`, `supplier_stock_reports_download`, `supplier_stock_reports_mail`, and `supplier_stock_report_source_day|...` with detailed 24h source history.
- RU: Добавлены mobile-control-обработчики `supplier_stock_reports`, `supplier_stock_reports_download`, `supplier_stock_reports_mail` и `supplier_stock_report_source_day|...` с детальной 24-часовой историей по источнику.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.33.0`; Android metadata updated to `ANDROID_VERSION_NAME=8.33.0`, `ANDROID_VERSION_CODE=120`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.33.0`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.33.0`, `ANDROID_VERSION_CODE=120`.

## [8.32.73] - 2026-03-17

### Fixed / Исправлено
- EN: Improved forced-update card in Android client: now shows installed app version (`current_version` from API with fallback to local build version), so users can clearly compare it with min/latest requirements.
- RU: Улучшена карточка принудительного обновления в Android-клиенте: теперь отображается установленная версия приложения (`current_version` из API с fallback на локальную версию сборки), чтобы пользователь явно видел расхождение с min/latest версиями.
- EN: Fixed broken "Update app" navigation in Android client: invalid/empty/non-download GitHub links are now normalized to stable fallback URL `https://github.com/sukhanovai/monitoring/releases/latest/download/monitoring-android.apk`.
- RU: Исправлен сломанный переход кнопки «Обновить приложение» в Android-клиенте: невалидные/пустые/страничные GitHub-ссылки теперь нормализуются в стабильный fallback URL `https://github.com/sukhanovai/monitoring/releases/latest/download/monitoring-android.apk`.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.32.73`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.73`, `ANDROID_VERSION_CODE=118`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.32.73`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.73`, `ANDROID_VERSION_CODE=118`.

## [8.32.72] - 2026-03-17

### Fixed / Исправлено
- EN: Strengthened final app launch in `scripts/android_post_pull_build_run.ps1`: before launch the script force-stops the package, starts launcher activity with `am start -W`, verifies that the app actually becomes foreground via `dumpsys`, and falls back to `monkey` with the same foreground validation if needed.
- RU: Усилен финальный запуск приложения в `scripts/android_post_pull_build_run.ps1`: перед запуском скрипт делает `force-stop` пакета, стартует launcher-activity через `am start -W`, проверяет фактический выход приложения на передний план через `dumpsys` и при необходимости использует fallback через `monkey` с той же проверкой foreground.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.32.72`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.72`, `ANDROID_VERSION_CODE=117`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.32.72`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.72`, `ANDROID_VERSION_CODE=117`.

## [8.32.69] - 2026-03-17

### Fixed / Исправлено
- EN: Hardened GitHub API prerelease creation in `scripts/publish_android_prerelease.ps1`: release creation retries now handle both HTTP 400 and 422, include a third fallback attempt with a minimal payload (without `target_commitish` and `body`), and keep detailed diagnostics for all attempts.
- RU: Усилена надёжность создания prerelease через GitHub API в `scripts/publish_android_prerelease.ps1`: повторы теперь обрабатывают HTTP 400 и 422, добавлена третья попытка с минимальным payload (без `target_commitish` и `body`), а также сохраняется подробная диагностика по всем попыткам.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.32.69`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.69`, `ANDROID_VERSION_CODE=114`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.32.69`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.69`, `ANDROID_VERSION_CODE=114`.

## [8.32.68] - 2026-03-17

### Fixed / Исправлено
- EN: Improved GitHub API prerelease publish diagnostics in `scripts/publish_android_prerelease.ps1`: when release creation fails with HTTP 400 (including retry without `target_commitish`), the script now preserves and prints GitHub API response details from both attempts, making root-cause analysis actionable.
- RU: Улучшена диагностика публикации prerelease через GitHub API в `scripts/publish_android_prerelease.ps1`: при падении создания релиза с HTTP 400 (включая повтор без `target_commitish`) скрипт теперь сохраняет и выводит детали ответа GitHub API по обеим попыткам, чтобы было проще разобрать первопричину.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.32.68`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.68`, `ANDROID_VERSION_CODE=113`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.32.68`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.68`, `ANDROID_VERSION_CODE=113`.

## [8.32.67] - 2026-03-17

### Fixed / Исправлено
- EN: Improved GitHub API prerelease publish resilience in `scripts/publish_android_prerelease.ps1`: if release creation still returns HTTP 400 after retry without `target_commitish`, the script now performs an additional tag-based release lookup and switches to update flow when a release already exists.
- RU: Повышена устойчивость публикации prerelease через GitHub API в `scripts/publish_android_prerelease.ps1`: если создание релиза всё ещё возвращает HTTP 400 после повтора без `target_commitish`, скрипт теперь дополнительно ищет релиз по тегу и переходит в режим обновления, если релиз уже существует.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.32.67`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.67`, `ANDROID_VERSION_CODE=112`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.32.67`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.67`, `ANDROID_VERSION_CODE=112`.

## [8.32.65] - 2026-03-17

### Fixed / Исправлено
- EN: Fixed GitHub API prerelease publishing in `scripts/publish_android_prerelease.ps1` for cases when `/releases/tags/{tag}` returns 404 but a draft release with the same tag already exists; the script now additionally scans release pages (including drafts) and updates the existing release instead of failing with HTTP 400 on create.
- RU: Исправлена публикация prerelease через GitHub API в `scripts/publish_android_prerelease.ps1` для случая, когда `/releases/tags/{tag}` возвращает 404, но draft-релиз с тем же тегом уже существует; скрипт теперь дополнительно сканирует страницы релизов (включая draft) и обновляет существующий релиз вместо падения с HTTP 400 при создании.

### Changed / Изменено
- EN: Completed repository-wide patch version bump to `8.32.65`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.65`, `ANDROID_VERSION_CODE=110`.
- RU: Выполнен полный патч-бамп версии по репозиторию до `8.32.65`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.65`, `ANDROID_VERSION_CODE=110`.

## [8.32.60] - 2026-03-16

### Fixed / Исправлено
- EN: Added a third safe recovery path for `git pull` conflicts in docs (`git stash push -u` → `git pull --rebase` → `git stash pop`) for local edits in `README.md` and `docs/android_mobile_app.md`.
- RU: Добавлен третий безопасный сценарий при конфликте `git pull` в документации (`git stash push -u` → `git pull --rebase` → `git stash pop`) для локальных правок `README.md` и `docs/android_mobile_app.md`.

### Changed / Изменено
- EN: Completed repository-wide version bump to `8.32.60`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.60`, `ANDROID_VERSION_CODE=105`.
- RU: Выполнен полный бамп версии по репозиторию до `8.32.60`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.60`, `ANDROID_VERSION_CODE=105`.

## [8.32.58] - 2026-03-16

### Fixed / Исправлено
- EN: Fixed Android prerelease build/publish flow in `scripts/publish_android_prerelease.ps1`: the script now selects only installable signed APK artifacts and stops with explicit guidance when only unsigned APK is present.
- RU: Исправлен flow сборки/публикации Android prerelease в `scripts/publish_android_prerelease.ps1`: скрипт теперь выбирает только устанавливаемые подписанные APK и завершает работу с явной подсказкой, если найден только unsigned APK.
- EN: Fixed recurring `git pull` conflicts after prerelease publish by making README/docs link rewrite opt-in (`-UpdateDocsLinks`) instead of default behavior.
- RU: Исправлены регулярные конфликты при `git pull` после публикации prerelease: переписывание ссылки в README/docs теперь выполняется только по флагу `-UpdateDocsLinks`, а не по умолчанию.
- EN: Fixed release APK installability in Android builds by enabling debug-keystore signing for `release` type in `android-client/app/build.gradle.kts` for prerelease distribution.
- RU: Исправлена устанавливаемость release APK в Android-сборке: для `release`-типа включено подписание debug-keystore в `android-client/app/build.gradle.kts` для prerelease-дистрибуции.

### Changed / Изменено
- EN: Completed repository-wide version bump to `8.32.58`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.58`, `ANDROID_VERSION_CODE=103`.
- RU: Выполнен полный бамп версии по репозиторию до `8.32.58`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.58`, `ANDROID_VERSION_CODE=103`.

## [8.32.57] - 2026-03-16

### Fixed / Исправлено
- EN: Fixed Android prerelease APK links in `README.md` and `docs/android_mobile_app.md`: replaced placeholder repository path with the actual `sukhanovai/monitoring` URL.
- RU: Исправлены ссылки на Android prerelease APK в `README.md` и `docs/android_mobile_app.md`: вместо шаблонного пути репозитория теперь используется фактический `sukhanovai/monitoring`.
- EN: Fixed prerelease release notes template in `scripts/publish_android_prerelease.ps1`: Russian section is now written in Russian.
- RU: Исправлен шаблон описания prerelease в `scripts/publish_android_prerelease.ps1`: русский блок теперь действительно на русском языке.

### Changed / Изменено
- EN: Completed full repository-wide version bump to `8.32.57`; synchronized runtime/config/docs/script/android UI references and bumped Android metadata to `ANDROID_VERSION_NAME=8.32.57`, `ANDROID_VERSION_CODE=102`.
- RU: Выполнен полный бамп версии по всему репозиторию до `8.32.57`; синхронизированы ссылки в runtime/config/docs/скриптах/Android UI, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.57`, `ANDROID_VERSION_CODE=102`.

## [8.32.56] - 2026-03-16

### Changed / Изменено
- EN: Updated Android prerelease workflow docs with an auto-managed APK download link marker; `scripts/publish_android_prerelease.ps1` now rewrites this link in `README.md` and `docs/android_mobile_app.md` on each publish run.
- RU: Обновлена документация по Android prerelease: добавлен автообновляемый маркер ссылки на APK; `scripts/publish_android_prerelease.ps1` теперь переписывает эту ссылку в `README.md` и `docs/android_mobile_app.md` при каждом запуске публикации.
- EN: Removed explicit `-GitHubToken` usage from script guidance and switched to secure token-file flow (`$HOME/.monitoring/github_token`) with env fallback.
- RU: Убрано явное использование `-GitHubToken` в сценарии запуска; переход на безопасный файл токена (`$HOME/.monitoring/github_token`) с fallback через переменные окружения.
- EN: Completed repository-wide version bump to `8.32.56`; Android metadata updated to `ANDROID_VERSION_NAME=8.32.56` and `ANDROID_VERSION_CODE=101`.
- RU: Выполнен полный бамп версии по репозиторию до `8.32.56`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.32.56` и `ANDROID_VERSION_CODE=101`.

## [8.32.55] - 2026-03-16

### Changed / Изменено
- EN: Completed repository-wide version bump after follow-up review: synchronized all current `8.32.54` references to `8.32.55` in config banners, runtime settings, scripts, docs, and Android UI metadata.
- RU: Завершён полный бамп версии по репозиторию после повторной проверки: все актуальные ссылки `8.32.54` синхронизированы на `8.32.55` в баннерах конфигов, runtime-настройках, скриптах, документации и метаданных Android UI.
- EN: Android app version metadata updated to `ANDROID_VERSION_NAME=8.32.55` and `ANDROID_VERSION_CODE=100`.
- RU: Метаданные версии Android-приложения обновлены до `ANDROID_VERSION_NAME=8.32.55` и `ANDROID_VERSION_CODE=100`.

## [8.32.54] - 2026-03-16

### Fixed / Исправлено
- EN: Updated `scripts/publish_android_prerelease.ps1` fallback log message to explicitly list all supported token environment variables: `GH_TOKEN`, `GITHUB_TOKEN`, and `GITHUB_PAT`.
- RU: Обновлено fallback-сообщение в `scripts/publish_android_prerelease.ps1`: теперь явно перечислены все поддерживаемые переменные токена — `GH_TOKEN`, `GITHUB_TOKEN` и `GITHUB_PAT`.
- EN: Added an explicit token re-check right before version read/build stage when `gh` is unavailable, so API fallback prerequisites are validated as part of step `[2/7]` before expensive Android build work.
- RU: Добавлена явная повторная проверка токена перед чтением версии/сборкой, когда `gh` недоступен, чтобы требования API fallback валидировались на шаге `[2/7]` до затратной Android-сборки.

### Changed / Изменено
- EN: Project version bumped to `8.32.54`; Android `versionCode` bumped to `99`.
- RU: Версия проекта повышена до `8.32.54`; Android `versionCode` увеличен до `99`.

## [8.32.53] - 2026-03-16

### Fixed / Исправлено
- EN: Improved dirty working tree failure output in `scripts/publish_android_prerelease.ps1`: the script now prints explicit command examples for `-AutoStashDirty`, manual stash flow, `-AllowDirty`, and a short preview of dirty files.
- RU: Улучшен вывод ошибки при грязном рабочем дереве в `scripts/publish_android_prerelease.ps1`: скрипт теперь показывает явные примеры команд для `-AutoStashDirty`, ручного stash-сценария, `-AllowDirty` и короткий превью-список изменённых файлов.

### Changed / Изменено
- EN: Project version bumped to `8.32.53`; Android `versionCode` bumped to `98`.
- RU: Версия проекта повышена до `8.32.53`; Android `versionCode` увеличен до `98`.

## [8.32.52] - 2026-03-16

### Fixed / Исправлено
- EN: Updated dirty working tree guidance in `scripts/publish_android_prerelease.ps1` with a clearer quick action: rerun with `-AutoStashDirty`, plus explicit manual stash and `-AllowDirty` alternatives.
- RU: Обновлена подсказка для грязного рабочего дерева в `scripts/publish_android_prerelease.ps1` с более понятным быстрым действием: перезапуск с `-AutoStashDirty`, а также явные альтернативы через ручной stash и `-AllowDirty`.

### Changed / Изменено
- EN: Project version bumped to `8.32.52`; Android `versionCode` bumped to `97`.
- RU: Версия проекта повышена до `8.32.52`; Android `versionCode` увеличен до `97`.

## [8.32.51] - 2026-03-16

### Fixed / Исправлено
- EN: Improved dirty working tree error hint in `scripts/publish_android_prerelease.ps1`: message now explicitly suggests `-AutoStashDirty` for temporary auto-stash, plus `-AllowDirty` for advanced workflows.
- RU: Улучшена подсказка при грязном рабочем дереве в `scripts/publish_android_prerelease.ps1`: сообщение теперь явно предлагает `-AutoStashDirty` для временного авто-stash, а также `-AllowDirty` для продвинутых сценариев.

### Changed / Изменено
- EN: Project version bumped to `8.32.51`; Android `versionCode` bumped to `96`.
- RU: Версия проекта повышена до `8.32.51`; Android `versionCode` увеличен до `96`.

## [8.32.50] - 2026-03-16

### Changed / Изменено
- EN: Completed full version alignment across the repository after prerelease script updates: synchronized hardcoded project version banners/usages in source modules, docs, and Android app metadata to avoid partial version drift.
- RU: Завершено полное выравнивание версии по репозиторию после обновлений prerelease-скрипта: синхронизированы захардкоженные баннеры/упоминания версии в модулях, документации и метаданных Android-приложения, чтобы исключить частичный дрейф версии.
- EN: Project version bumped to `8.32.50`; Android `versionCode` bumped to `95`.
- RU: Версия проекта повышена до `8.32.50`; Android `versionCode` увеличен до `95`.

## [8.32.49] - 2026-03-16

### Changed / Изменено
- EN: Improved missing-token guidance in `scripts/publish_android_prerelease.ps1`: added explicit PAT creation links and a one-liner to save token into `.github_token`, so Android Studio users can configure GitHub API fallback faster when `gh` is unavailable.
- RU: Улучшены подсказки при отсутствии токена в `scripts/publish_android_prerelease.ps1`: добавлены прямые ссылки на создание PAT и однострочник для сохранения токена в `.github_token`, чтобы в Android Studio быстрее настраивать fallback через GitHub API при отсутствии `gh`.
- EN: Project version bumped to `8.32.49`; Android `versionCode` bumped to `94`.
- RU: Версия проекта повышена до `8.32.49`; Android `versionCode` увеличен до `94`.

## [8.32.48] - 2026-03-16

### Fixed / Исправлено
- EN: Improved `scripts/publish_android_prerelease.ps1` gh CLI detection for Android Studio/Windows terminals: added extra common install locations including `.../GitHub CLI/bin/gh.exe` and Scoop app path `scoop/apps/gh/current/bin/gh.exe`.
- RU: Улучшено определение gh CLI в `scripts/publish_android_prerelease.ps1` для Android Studio/Windows-терминалов: добавлены дополнительные типовые пути установки, включая `.../GitHub CLI/bin/gh.exe` и путь Scoop `scoop/apps/gh/current/bin/gh.exe`.
- EN: Added `where.exe gh` probe before fallback path scan to detect gh in PATH aliases/links that are visible to shell but not covered by static path list.
- RU: Добавлена проверка `where.exe gh` перед сканированием fallback-путей, чтобы находить gh через PATH-алиасы/линки, которые видны оболочке, но не покрыты статическим списком путей.

### Changed / Изменено
- EN: Project version bumped to `8.32.48`; Android `versionCode` bumped to `93`.
- RU: Версия проекта повышена до `8.32.48`; Android `versionCode` увеличен до `93`.

## [8.32.45] - 2026-03-16

### Fixed / Исправлено
- EN: Improved parsing of token variables in `.env` for `scripts/publish_android_prerelease.ps1`: now supports PowerShell-style lines with whitespace separator (for example, `setx GH_TOKEN ghp_xxx`) so Android Studio terminals can pick up token hints more reliably.
- RU: Улучшен парсинг переменных токена в `.env` для `scripts/publish_android_prerelease.ps1`: теперь поддерживаются строки PowerShell с пробелом-разделителем (например, `setx GH_TOKEN ghp_xxx`), чтобы в терминалах Android Studio надёжнее подхватывались подсказки с токеном.
- EN: Completed version alignment across the repository after prerelease script updates: all hardcoded project version banners/usages are now synchronized to the current release value to prevent partial version drift in diagnostics, docs, and UI metadata.
- RU: Завершена синхронизация версий по всему репозиторию после обновлений prerelease-скрипта: все захардкоженные баннеры/упоминания версии проекта приведены к текущему релизному значению, чтобы исключить частичный дрейф версий в диагностике, документации и метаданных UI.

### Changed / Изменено
- EN: Project version bumped to `8.32.45`; Android `versionCode` bumped to `91`.
- RU: Версия проекта повышена до `8.32.45`; Android `versionCode` увеличен до `91`.

## [8.32.43] - 2026-03-16

### Fixed / Исправлено
- EN: Enhanced GitHub token discovery in `scripts/publish_android_prerelease.ps1` for Android Studio PowerShell flow when `gh` CLI is unavailable: script now also reads token from GitHub CLI auth config (`hosts.yml`) in standard Linux/macOS and Windows locations.
- RU: Улучшен поиск GitHub-токена в `scripts/publish_android_prerelease.ps1` для сценария Android Studio PowerShell при отсутствии `gh` CLI: скрипт теперь дополнительно читает токен из конфигурации авторизации GitHub CLI (`hosts.yml`) в стандартных путях Linux/macOS и Windows.
- EN: Improved missing-token diagnostics by listing checked `hosts.yml` locations, alongside env and token-file paths.
- RU: Улучшена диагностика отсутствия токена: в сообщении теперь выводятся проверенные пути `hosts.yml` вместе с путями env и token-файлов.

### Changed / Изменено
- EN: Project version bumped to `8.32.43`; Android `versionCode` bumped to `89`.
- RU: Версия проекта повышена до `8.32.43`; Android `versionCode` увеличен до `89`.

## [8.32.42] - 2026-03-16

### Fixed / Исправлено
- EN: Improved `scripts/publish_android_prerelease.ps1` gh CLI detection for Android Studio PowerShell terminals on Windows: the script now searches common installation paths (`Program Files`, Scoop shims, WinGet links) when `gh` is missing from `PATH`.
- RU: Улучшено определение gh CLI в `scripts/publish_android_prerelease.ps1` для PowerShell-терминала Android Studio на Windows: скрипт теперь ищет `gh` в типовых путях установки (`Program Files`, shims Scoop, ссылки WinGet), если команда отсутствует в `PATH`.
- EN: Added a dedicated `Invoke-Gh` wrapper to run release commands through the detected executable path, preventing false "gh not found" failures in IDE terminals.
- RU: Добавлен отдельный враппер `Invoke-Gh` для запуска release-команд через найденный путь к исполняемому файлу, что устраняет ложные падения "gh not found" в терминалах IDE.

### Changed / Изменено
- EN: Project version bumped to `8.32.42`; Android `versionCode` bumped to `88`.
- RU: Версия проекта повышена до `8.32.42`; Android `versionCode` увеличен до `88`.

## [8.32.40] - 2026-03-16

### Fixed / Исправлено
- EN: Improved GitHub token parsing in `scripts/publish_android_prerelease.ps1`: `.env` lines now also support `set`/`setx` prefixes and trim inline trailing comments, which reduces false negatives in Android Studio PowerShell workflows.
- RU: Улучшен парсинг GitHub-токена в `scripts/publish_android_prerelease.ps1`: строки `.env` теперь дополнительно поддерживают префиксы `set`/`setx` и обрезают хвостовые inline-комментарии, что снижает ложные срабатывания в PowerShell-потоке Android Studio.

### Changed / Изменено
- EN: Project version bumped to `8.32.40`; Android `versionCode` bumped to `86`.
- RU: Версия проекта повышена до `8.32.40`; Android `versionCode` увеличен до `86`.

## [8.32.39] - 2026-03-16

### Changed / Изменено
- EN: Aligned project version references across source files and Android client metadata to prevent partial version bumps after script updates.
- RU: Синхронизированы упоминания версии проекта во всех исходных файлах и метаданных Android-клиента, чтобы исключить частичный бамп версии после изменений скриптов.
- EN: Project version bumped to `8.32.39`; Android `versionCode` bumped to `85`.
- RU: Версия проекта повышена до `8.32.39`; Android `versionCode` увеличен до `85`.

## [8.32.37] - 2026-03-16

### Changed / Изменено
- EN: Extended `scripts/publish_android_prerelease.ps1` GitHub token lookup with `.env` support (repository and home directory): script now recognizes `GH_TOKEN`, `GITHUB_TOKEN`, and `GITHUB_PAT` from `.env`, which helps in Android Studio terminals where token is stored in env files but not exported into current process environment.
- RU: Расширен поиск GitHub-токена в `scripts/publish_android_prerelease.ps1` поддержкой `.env` (в репозитории и домашней директории): скрипт теперь распознаёт `GH_TOKEN`, `GITHUB_TOKEN` и `GITHUB_PAT` из `.env`, что помогает в терминале Android Studio, когда токен хранится в env-файле, но не экспортирован в текущее окружение процесса.
- EN: Improved missing-token diagnostics to also show `.env` lookup locations checked by the script.
- RU: Улучшена диагностика отсутствия токена: теперь дополнительно выводятся пути поиска `.env`, которые проверил скрипт.
- EN: Project version bumped to `8.32.37`; Android `versionCode` bumped to `84`.
- RU: Версия проекта повышена до `8.32.37`; Android `versionCode` увеличен до `84`.

## [8.32.36] - 2026-03-16

### Fixed / Исправлено
- EN: Improved `scripts/android_post_pull_build_run.ps1` ADB launch step: script now auto-detects `adb` not only from `PATH`, but also from common Android SDK locations (`ANDROID_SDK_ROOT`, `ANDROID_HOME`, `%LOCALAPPDATA%\Android\Sdk`, `%USERPROFILE%\AppData\Local\Android\Sdk`), which fixes launch failures in Android Studio terminal when Platform-Tools are installed but not exported to `PATH`.
- RU: Улучшен шаг запуска через ADB в `scripts/android_post_pull_build_run.ps1`: скрипт теперь ищет `adb` не только в `PATH`, но и в типичных путях Android SDK (`ANDROID_SDK_ROOT`, `ANDROID_HOME`, `%LOCALAPPDATA%\Android\Sdk`, `%USERPROFILE%\AppData\Local\Android\Sdk`), что устраняет падение запуска в терминале Android Studio, когда Platform-Tools установлены, но не добавлены в `PATH`.

### Changed / Изменено
- EN: Project version bumped to `8.32.36`; Android `versionCode` bumped to `83`.
- RU: Версия проекта повышена до `8.32.36`; Android `versionCode` увеличен до `83`.

## [8.32.35] - 2026-03-16

### Added / Добавлено
- EN: Added `scripts/android_post_pull_build_run.ps1` for Android Studio terminal on Windows: runs Gradle sync-equivalent configuration, clean build, assemble, installs debug APK, and launches the app on a connected device/emulator (CLI equivalent of `'app' [U] Shift+F10`).
- RU: Добавлен `scripts/android_post_pull_build_run.ps1` для терминала Android Studio на Windows: выполняет эквивалент sync Gradle, очистку проекта, сборку, установку debug APK и запуск приложения на подключённом устройстве/эмуляторе (CLI-эквивалент `'app' [U] Shift+F10`).

### Changed / Изменено
- EN: Project version bumped to `8.32.35`; Android `versionCode` bumped to `82`.
- RU: Версия проекта повышена до `8.32.35`; Android `versionCode` увеличен до `82`.

## [8.32.34] - 2026-03-16

### Added / Добавлено
- EN: Added `scripts/android_post_pull_build_run.sh` for Android Studio terminal: runs Gradle sync-equivalent configuration, clean build, assemble, installs debug APK, and launches the app on a connected device/emulator.
- RU: Добавлен `scripts/android_post_pull_build_run.sh` для терминала Android Studio: выполняет эквивалент sync Gradle, очистку проекта, сборку, установку debug APK и запуск приложения на подключённом устройстве/эмуляторе.

### Changed / Изменено
- EN: Project version bumped to `8.32.34`; Android `versionCode` bumped to `81`.
- RU: Версия проекта повышена до `8.32.34`; Android `versionCode` увеличен до `81`.

## [8.32.33] - 2026-03-16

### Fixed / Исправлено
- EN: Improved error handling in `scripts/publish_android_prerelease.ps1`: failures are now printed as a concise message without PowerShell stack trace noise, while preserving non-zero exit code.
- RU: Улучшена обработка ошибок в `scripts/publish_android_prerelease.ps1`: при сбоях теперь выводится краткое сообщение без лишнего PowerShell stack trace, при этом сохраняется ненулевой код завершения.

### Changed / Изменено
- EN: Project version bumped to `8.32.33`; Android `versionCode` bumped to `80`.
- RU: Версия проекта повышена до `8.32.33`; Android `versionCode` увеличен до `80`.

## [8.32.32] - 2026-03-16

### Changed / Изменено
- EN: Extended `scripts/publish_android_prerelease.ps1` token lookup: added `-GitHubToken` parameter, support for `GITHUB_PAT`, and additional Windows home directory probing (`USERPROFILE`, `HOMEDRIVE`/`HOMEPATH`) for `.github_token` / `.github-token` files.
- RU: Расширен поиск токена в `scripts/publish_android_prerelease.ps1`: добавлен параметр `-GitHubToken`, поддержка `GITHUB_PAT`, а также дополнительная проверка Windows-домашних директорий (`USERPROFILE`, `HOMEDRIVE`/`HOMEPATH`) для файлов `.github_token` / `.github-token`.
- EN: Improved missing-token diagnostics with explicit usage example for `-GitHubToken`.
- RU: Улучшена диагностика отсутствия токена: добавлен явный пример запуска с `-GitHubToken`.
- EN: Missing-token diagnostics in `scripts/publish_android_prerelease.ps1` now print real, deduplicated token lookup paths detected for the current Windows environment instead of static placeholders.
- RU: Диагностика отсутствия токена в `scripts/publish_android_prerelease.ps1` теперь выводит реальные уникальные пути поиска токена для текущего Windows-окружения вместо статичных шаблонов.
- EN: Project version bumped to `8.32.32`; Android `versionCode` bumped to `79`.
- RU: Версия проекта повышена до `8.32.32`; Android `versionCode` увеличен до `79`.

## [8.32.28] - 2026-03-15

### Changed / Изменено
- EN: Improved `scripts/publish_android_prerelease.ps1` GitHub API fallback: script now also reads token from `.github_token`/`.github-token` files in repository or home directory, and error message contains explicit PowerShell setup examples for `GH_TOKEN`.
- RU: Улучшен fallback через GitHub API в `scripts/publish_android_prerelease.ps1`: скрипт теперь читает токен не только из переменных окружения, но и из файлов `.github_token`/`.github-token` в репозитории или домашней директории, а текст ошибки дополнен явными PowerShell-примерами настройки `GH_TOKEN`.
- EN: Project version bumped to `8.32.28`; Android `versionCode` bumped to `75`.
- RU: Версия проекта повышена до `8.32.28`; Android `versionCode` увеличен до `75`.

## [8.32.27] - 2026-03-15

### Changed / Изменено
- EN: Improved `scripts/git_safe_pull.ps1` diagnostics for Android Studio `git pull` conflicts caused by local Android Gradle config changes, including explicit hint commands for safe restore or forced reset-to-remote flow.
- RU: Улучшена диагностика в `scripts/git_safe_pull.ps1` для конфликтов `git pull` в Android Studio из-за локальных изменений Android Gradle-конфигов: добавлены явные команды-подсказки для безопасного восстановления или принудительного reset к remote-версии.
- EN: Project version bumped to `8.32.27`; Android `versionCode` bumped to `74`.
- RU: Версия проекта повышена до `8.32.27`; Android `versionCode` увеличен до `74`.

## [8.32.26] - 2026-03-15

### Added / Добавлено
- EN: Added a dedicated README troubleshooting snippet for Android Studio `git pull` failures caused by local changes in `android-client/gradle/wrapper/gradle-wrapper.properties`, with a direct `git_safe_pull.ps1` command example.
- RU: Добавлен отдельный troubleshooting-фрагмент в README для ошибок `git pull` в Android Studio из-за локальных изменений в `android-client/gradle/wrapper/gradle-wrapper.properties`, с прямым примером команды `git_safe_pull.ps1`.

### Changed / Изменено
- EN: Project version bumped to `8.32.26`; Android `versionCode` bumped to `73`.
- RU: Версия проекта повышена до `8.32.26`; Android `versionCode` увеличен до `73`.

## [8.32.25] - 2026-03-16

### Fixed / Исправлено
- EN: Fixed Android Studio sync/build failure `Cannot add extension with name 'kotlin'` by downgrading Gradle wrapper from `9.1.0` to `8.7`, which is compatible with the configured Android Gradle Plugin `8.5.2` and Kotlin plugins.
- RU: Исправлен сбой синхронизации/сборки в Android Studio `Cannot add extension with name 'kotlin'`: Gradle wrapper понижен с `9.1.0` до `8.7`, совместимого с используемыми Android Gradle Plugin `8.5.2` и Kotlin-плагинами.

### Changed / Изменено
- EN: Project version bumped to `8.32.25`; Android `versionCode` bumped to `72`.
- RU: Версия проекта повышена до `8.32.25`; Android `versionCode` увеличен до `72`.

## [8.32.24] - 2026-03-15

### Added / Добавлено
- EN: Added optional `-AutoStashDirty` mode to `scripts/publish_android_prerelease.ps1`: when the working tree is dirty, the script automatically creates a temporary stash before publish and restores it in `finally`.
- RU: Добавлен опциональный режим `-AutoStashDirty` в `scripts/publish_android_prerelease.ps1`: при грязном рабочем дереве скрипт автоматически создаёт временный stash перед публикацией и восстанавливает его в блоке `finally`.

### Fixed / Исправлено
- EN: Added explicit validation that `-AllowDirty` and `-AutoStashDirty` cannot be used together.
- RU: Добавлена явная проверка, что `-AllowDirty` и `-AutoStashDirty` нельзя использовать одновременно.

### Changed / Изменено
- EN: Project version bumped to `8.32.24`; Android `versionCode` bumped to `71`.
- RU: Версия проекта повышена до `8.32.24`; Android `versionCode` увеличен до `71`.

## [8.32.22] - 2026-03-15

### Fixed / Исправлено
- EN: Fixed `scripts/publish_android_prerelease.ps1` APK path selection for PowerShell: wrapped `Join-Path` calls in parentheses inside array initialization to prevent passing `System.Object[]` as `ChildPath` and failing on step `[4/7] Checking APK output...`.
- RU: Исправлен выбор пути к APK в `scripts/publish_android_prerelease.ps1` для PowerShell: вызовы `Join-Path` обёрнуты в скобки при инициализации массива, чтобы не передавался `System.Object[]` в `ChildPath` и не падал шаг `[4/7] Checking APK output...`.

### Changed / Изменено
- EN: Project version bumped to `8.32.22`; Android `versionCode` bumped to `69`.
- RU: Версия проекта повышена до `8.32.22`; Android `versionCode` увеличен до `69`.

## [8.32.21] - 2026-03-15

### Fixed / Исправлено
- EN: Fixed `scripts/git_safe_pull.ps1` reset behavior that could leave local changes in index/worktree before `git pull --rebase` (`cannot pull with rebase: Your index contains uncommitted changes`). Reset mode now discards target Android config changes to `HEAD` first and only then runs pull.
- RU: Исправлено поведение reset-режима в `scripts/git_safe_pull.ps1`, из-за которого перед `git pull --rebase` могли оставаться локальные изменения в index/worktree (`cannot pull with rebase: Your index contains uncommitted changes`). Теперь режим сначала сбрасывает целевые Android-конфиги к `HEAD`, и только потом выполняет pull.
- EN: Kept explicit `unmerged` recovery for target Android config files before pull, so failed `stash pop` states are still auto-unblocked in reset mode.
- RU: Сохранена явная обработка `unmerged` для целевых Android-конфигов перед pull, поэтому конфликтные состояния после неудачного `stash pop` по-прежнему автоматически разблокируются в reset-режиме.

### Changed / Изменено
- EN: Updated README reset instructions to use `git restore --staged --worktree` before pull (instead of checkouting files from `origin/develop` pre-pull).
- RU: Обновлены reset-инструкции в README: теперь используется `git restore --staged --worktree` перед pull (вместо предварительного `checkout` файлов из `origin/develop`).
- EN: Project version bumped to `8.32.21`; Android `versionCode` bumped to `68`.
- RU: Версия проекта повышена до `8.32.21`; Android `versionCode` увеличен до `68`.

## [8.32.20] - 2026-03-15

### Fixed / Исправлено
- EN: Improved `scripts/git_safe_pull.ps1` reset flow for Android config files: `-OnlyAndroidClientConfig -ResetAndroidClientConfigToRemote` now detects unresolved conflicts (`unmerged`) in target files, safely clears merge-conflict index state, and then replaces files from `$Remote/$Branch` before pull.
- RU: Улучшен reset-сценарий `scripts/git_safe_pull.ps1` для Android-конфигов: `-OnlyAndroidClientConfig -ResetAndroidClientConfigToRemote` теперь обнаруживает неразрешённые конфликты (`unmerged`) в целевых файлах, безопасно очищает конфликтное состояние индекса и затем заменяет файлы версиями из `$Remote/$Branch` перед pull.
- EN: Added explicit guard for unresolved conflicts outside target Android config files — script now stops with a clear message instead of trying partial recovery.
- RU: Добавлена явная защита для неразрешённых конфликтов вне целевых Android-конфигов — скрипт останавливается с понятным сообщением и не пытается делать частичное восстановление.

### Changed / Изменено
- EN: README updated to clarify that reset mode can unblock `git pull` after a failed `stash pop` conflict scenario in Android Studio.
- RU: README обновлён: уточнено, что reset-режим помогает разблокировать `git pull` после конфликтного `stash pop` в Android Studio.
- EN: Project version bumped to `8.32.20`; Android `versionCode` bumped to `67`.
- RU: Версия проекта повышена до `8.32.20`; Android `versionCode` увеличен до `67`.

## [8.32.19] - 2026-03-15

### Added / Добавлено
- EN: Added a straightforward overwrite mode to `scripts/git_safe_pull.ps1`: `-OnlyAndroidClientConfig -ResetAndroidClientConfigToRemote` fetches `$Remote/$Branch`, replaces local Android config files with remote versions, and then runs pull — intended for cases when local Android Gradle config can be safely discarded.
- RU: Добавлен простой режим принудительной замены в `scripts/git_safe_pull.ps1`: `-OnlyAndroidClientConfig -ResetAndroidClientConfigToRemote` подтягивает `$Remote/$Branch`, заменяет локальные Android-конфиги версиями из удалённой ветки и выполняет pull — для кейсов, когда локальные правки в Android Gradle-конфигах можно безопасно отбросить.

### Changed / Изменено
- EN: Updated README with a one-command "discard local Android config and take GitHub version" flow and matching manual commands.
- RU: Обновлён README: добавлен сценарий "одной командой отбросить локальный Android-конфиг и взять версию из GitHub" и соответствующие ручные команды.
- EN: Project version bumped to `8.32.19`; Android `versionCode` bumped to `66`.
- RU: Версия проекта повышена до `8.32.19`; Android `versionCode` увеличен до `66`.

## [8.32.18] - 2026-03-15

### Fixed / Исправлено
- EN: Reworked `scripts/git_safe_pull.ps1` for `-OnlyAndroidClientConfig`: replaced `stash pop` flow with temporary backup/restore of target Android config files (`build.gradle.kts`, `gradle.properties`, `gradle-wrapper.properties`) to avoid post-pull merge conflicts in common Android Studio workflows.
- RU: Переработан `scripts/git_safe_pull.ps1` для `-OnlyAndroidClientConfig`: вместо схемы `stash pop` используется временный backup/restore целевых Android-конфигов (`build.gradle.kts`, `gradle.properties`, `gradle-wrapper.properties`), чтобы избежать merge-конфликтов после pull в типовом потоке Android Studio.
- EN: Added guardrail for `-OnlyAndroidClientConfig` mode: if there are local changes outside target Android config files, script now stops early with explicit action hint.
- RU: Добавлен guardrail для режима `-OnlyAndroidClientConfig`: если есть локальные изменения вне целевых Android-конфигов, скрипт останавливается заранее и даёт явную подсказку по дальнейшим действиям.

### Changed / Изменено
- EN: Updated README with conflict-resistant manual backup/restore commands as alternative to stash-based recovery in Android Studio terminal.
- RU: Обновлён README: добавлены более устойчивые к конфликтам ручные команды backup/restore как альтернатива stash-сценарию в терминале Android Studio.
- EN: Project version bumped to `8.32.18`; Android `versionCode` bumped to `65`.
- RU: Версия проекта повышена до `8.32.18`; Android `versionCode` увеличен до `65`.

## [8.32.17] - 2026-03-15

### Fixed / Исправлено
- EN: Expanded Android Studio safe-pull guidance and targeted stash scope to also include `android-client/gradle/wrapper/gradle-wrapper.properties`, because this file can be locally modified together with Android Gradle config and still block or complicate post-pull restoration.
- RU: Расширены рекомендации и целевой stash для safe-pull в Android Studio: теперь дополнительно учитывается `android-client/gradle/wrapper/gradle-wrapper.properties`, так как этот файл часто меняется вместе с Android Gradle-конфигом и мешает корректному восстановлению после pull.

### Changed / Изменено
- EN: Project version bumped to `8.32.17`; Android `versionCode` bumped to `64`.
- RU: Версия проекта повышена до `8.32.17`; Android `versionCode` увеличен до `64`.

## [8.32.16] - 2026-03-15

### Added / Добавлено
- EN: Added explicit manual Android Studio recovery commands for the common `git pull` block (`Please commit your changes or stash them before you merge`) when local edits are in `android-client/build.gradle.kts` and `android-client/gradle.properties`.
- RU: Добавлены явные ручные команды восстановления для Android Studio при типовой блокировке `git pull` (`Please commit your changes or stash them before you merge`), когда локальные правки находятся в `android-client/build.gradle.kts` и `android-client/gradle.properties`.

### Changed / Изменено
- EN: Project version bumped to `8.32.16`; Android `versionCode` bumped to `63`.
- RU: Версия проекта повышена до `8.32.16`; Android `versionCode` увеличен до `63`.

## [8.32.15] - 2026-03-15

### Fixed / Исправлено
- EN: Extended `scripts/git_safe_pull.ps1` with `-OnlyAndroidClientConfig` mode to stash only `android-client/build.gradle.kts` and `android-client/gradle.properties`, then pull and restore — directly addressing recurring Android Studio terminal pull blocks on those files.
- RU: Расширен `scripts/git_safe_pull.ps1` режимом `-OnlyAndroidClientConfig`: stash только `android-client/build.gradle.kts` и `android-client/gradle.properties`, затем pull и восстановление — это напрямую закрывает повторяющийся блок `git pull` в терминале Android Studio по этим файлам.
- EN: Added explicit README command for manual recovery in Android Studio terminal.
- RU: Добавлена явная команда в README для ручного восстановления в терминале Android Studio.

### Changed / Изменено
- EN: Project version bumped to `8.32.15`; Android `versionCode` bumped to `62`.
- RU: Версия проекта повышена до `8.32.15`; Android `versionCode` увеличен до `62`.

## [8.32.14] - 2026-03-15

### Changed / Изменено
- EN: Moved Android app version source to `android-client/gradle.properties` (`ANDROID_VERSION_CODE`, `ANDROID_VERSION_NAME`) and switched `app/build.gradle.kts` to read these values, reducing routine merge conflicts in `app/build.gradle.kts` during `git pull`.
- RU: Источник Android-версий перенесён в `android-client/gradle.properties` (`ANDROID_VERSION_CODE`, `ANDROID_VERSION_NAME`), а `app/build.gradle.kts` теперь читает эти значения, что снижает количество типовых merge-конфликтов в `app/build.gradle.kts` при `git pull`.
- EN: Project version bumped to `8.32.14`; Android `versionCode` bumped to `61`.
- RU: Версия проекта повышена до `8.32.14`; Android `versionCode` увеличен до `61`.

## [8.32.13] - 2026-03-15

### Fixed / Исправлено
- EN: Fixed Android Studio build failure for Compose on Kotlin 2.x (`Starting in Kotlin 2.0, the Compose Compiler Gradle plugin is required`) by enabling `org.jetbrains.kotlin.plugin.compose` in the app module and declaring it in the root Gradle plugins block.
- RU: Исправлен сбой сборки Android Studio для Compose на Kotlin 2.x (`Starting in Kotlin 2.0, the Compose Compiler Gradle plugin is required`): подключён `org.jetbrains.kotlin.plugin.compose` в app-модуле и объявлен в корневом блоке Gradle-плагинов.
- EN: Upgraded Kotlin Android/plugin versions to `2.0.21` and removed obsolete `composeOptions.kotlinCompilerExtensionVersion` config for Kotlin 2 compose plugin flow.
- RU: Обновлены версии Kotlin Android/plugin до `2.0.21` и убрана устаревшая конфигурация `composeOptions.kotlinCompilerExtensionVersion` для потока compose-плагина в Kotlin 2.

### Changed / Изменено
- EN: Project version bumped to `8.32.13`; Android `versionCode` bumped to `60`.
- RU: Версия проекта повышена до `8.32.13`; Android `versionCode` увеличен до `60`.

## [8.32.12] - 2026-03-14

### Added / Добавлено
- EN: Added helper script `scripts/git_safe_pull.ps1` for safe pulls with local changes: auto-stash, pull (`--rebase` by default), and optional stash restore.
- RU: Добавлен helper-скрипт `scripts/git_safe_pull.ps1` для безопасного pull при локальных изменениях: авто-stash, pull (`--rebase` по умолчанию) и опциональное восстановление stash.

### Changed / Изменено
- EN: Updated README with practical instructions for resolving `git pull` blocking errors caused by local modifications.
- RU: Обновлён README с практической инструкцией по обходу блокирующей ошибки `git pull` из-за локальных изменений.
- EN: Project version bumped to `8.32.12`; Android `versionCode` bumped to `59`.
- RU: Версия проекта повышена до `8.32.12`; Android `versionCode` увеличен до `59`.

## [8.32.11] - 2026-03-14

### Fixed / Исправлено
- EN: Added preflight Git working-tree check to `scripts/publish_android_prerelease.ps1` so users get explicit guidance before running into `git pull` merge protection errors (`Please commit your changes or stash them before you merge`).
- RU: Добавлена preflight-проверка чистоты Git working tree в `scripts/publish_android_prerelease.ps1`, чтобы заранее получать понятную подсказку и не упираться в ошибки `git pull` вида `Please commit your changes or stash them before you merge`.
- EN: Added `-AllowDirty` escape hatch for advanced cases when user intentionally wants to run publish flow with local modifications.
- RU: Добавлен флаг `-AllowDirty` для продвинутого сценария, когда публикацию нужно запустить осознанно с локальными изменениями.

### Changed / Изменено
- EN: Project version bumped to `8.32.11`; Android `versionCode` bumped to `58`.
- RU: Версия проекта повышена до `8.32.11`; Android `versionCode` увеличен до `58`.

## [8.32.10] - 2026-03-14

### Fixed / Исправлено
- EN: Fixed APK discovery in `scripts/publish_android_prerelease.ps1`: script no longer hardcodes `app-release.apk` and now supports `app-release.apk`, `app-release-unsigned.apk`, or latest `*.apk` from release output directory.
- RU: Исправлен поиск APK в `scripts/publish_android_prerelease.ps1`: убран жёсткий хардкод `app-release.apk`, теперь поддерживаются `app-release.apk`, `app-release-unsigned.apk` или последний `*.apk` в каталоге release-вывода.
- EN: Added explicit log line with selected APK path to simplify troubleshooting in Android Studio terminal.
- RU: Добавлен явный лог с выбранным путём APK для упрощения диагностики в терминале Android Studio.

### Changed / Изменено
- EN: Project version bumped to `8.32.10`; Android `versionCode` bumped to `57`.
- RU: Версия проекта повышена до `8.32.10`; Android `versionCode` увеличен до `57`.

## [8.32.9] - 2026-03-14

### Fixed / Исправлено
- EN: Updated `scripts/publish_android_prerelease.ps1` to work without `gh`: if `gh` is unavailable, script now falls back to GitHub REST API using `GH_TOKEN`/`GITHUB_TOKEN` (create/edit prerelease and upload APK asset).
- RU: Обновлён `scripts/publish_android_prerelease.ps1`: теперь при отсутствии `gh` скрипт использует fallback через GitHub REST API с `GH_TOKEN`/`GITHUB_TOKEN` (создание/обновление prerelease и загрузка APK-артефакта).
- EN: Improved preflight messaging so missing `gh` no longer hard-fails immediately; script reports the API fallback path.
- RU: Улучшены preflight-сообщения: отсутствие `gh` больше не валит скрипт сразу, теперь явно показывается сценарий fallback через API.

### Changed / Изменено
- EN: Project version bumped to `8.32.9`; Android `versionCode` bumped to `56`.
- RU: Версия проекта повышена до `8.32.9`; Android `versionCode` увеличен до `56`.

## [8.32.8] - 2026-03-14

### Fixed / Исправлено
- EN: Fixed Windows PowerShell parsing errors in `scripts/publish_android_prerelease.ps1` caused by non-ASCII/encoding-sensitive text; script messages were rewritten in ASCII-safe form to avoid mojibake/parser failures.
- RU: Исправлены ошибки парсинга в Windows PowerShell в `scripts/publish_android_prerelease.ps1`, вызванные не-ASCII/кодировочными строками; сообщения переписаны в ASCII-безопасном виде для исключения кракозябр и сбоев парсера.

### Changed / Изменено
- EN: Project version bumped to `8.32.8`; Android `versionCode` bumped to `55`.
- RU: Версия проекта повышена до `8.32.8`; Android `versionCode` увеличен до `55`.

## [8.32.7] - 2026-03-14

### Fixed / Исправлено
- EN: Fixed Android Studio build error `Undefined Toolchain Download Repositories` / `Could not create task ':app:compileDebugAndroidTestJavaWithJavac'` by removing explicit Kotlin toolchain provisioning (`kotlin { jvmToolchain(17) }`) that forced missing local toolchain resolution.
- RU: Исправлена ошибка сборки Android Studio `Undefined Toolchain Download Repositories` / `Could not create task ':app:compileDebugAndroidTestJavaWithJavac'`: убран явный Kotlin toolchain (`kotlin { jvmToolchain(17) }`), который принудительно требовал недоступный локальный toolchain.
- EN: Kept `kotlinOptions { jvmTarget = "17" }` to preserve Java/Kotlin bytecode compatibility with project Java 17 settings.
- RU: Сохранён `kotlinOptions { jvmTarget = "17" }` для совместимости Java/Kotlin bytecode с настройками Java 17 в проекте.

### Changed / Изменено
- EN: Project version bumped to `8.32.7`; Android `versionCode` bumped to `54`.
- RU: Версия проекта повышена до `8.32.7`; Android `versionCode` увеличен до `54`.

## [8.32.6] - 2026-03-14

### Fixed / Исправлено
- EN: Fixed Android build failure `:app:compileDebugKotlin` caused by JVM target mismatch (`javac=17`, `kotlin=21`): pinned Kotlin/JVM to 17 via `kotlinOptions { jvmTarget = "17" }` and `kotlin { jvmToolchain(17) }`.
- RU: Исправлен сбой Android-сборки `:app:compileDebugKotlin` из-за несовпадения JVM target (`javac=17`, `kotlin=21`): Kotlin/JVM зафиксирован на 17 через `kotlinOptions { jvmTarget = "17" }` и `kotlin { jvmToolchain(17) }`.

### Changed / Изменено
- EN: Project version bumped to `8.32.6`; Android `versionCode` bumped to `53`.
- RU: Версия проекта повышена до `8.32.6`; Android `versionCode` увеличен до `53`.

## [8.32.5] - 2026-03-14

### Fixed / Исправлено
- EN: Reduced PR conflict surface by reverting non-essential repository-wide version-header changes and keeping only target files for Android prerelease workflow and Gradle plugin compatibility fix.
- RU: Снижен объём конфликтов в PR: отменены несущественные массовые правки version-header по репозиторию, оставлены только целевые файлы для Android prerelease workflow и фикса совместимости Gradle-плагинов.

### Changed / Изменено
- EN: Project version bumped to `8.32.5`; Android `versionCode` bumped to `52`.
- RU: Версия проекта повышена до `8.32.5`; Android `versionCode` увеличен до `52`.

## [8.32.4] - 2026-03-14

### Fixed / Исправлено
- EN: Removed the overreaching conflict-resolution helper script and its README section to avoid misleading workflow expectations; kept focus on the `develop` Android prerelease publishing flow.
- RU: Удалён избыточный helper-скрипт разруливания конфликтов и соответствующий раздел в README, чтобы не вводить в заблуждение по workflow; фокус оставлен на публикации Android prerelease из `develop`.

### Changed / Изменено
- EN: Project version bumped to `8.32.4`; Android `versionCode` bumped to `51`.
- RU: Версия проекта повышена до `8.32.4`; Android `versionCode` увеличен до `51`.

## [8.32.3] - 2026-03-14

### Added / Добавлено
- EN: Added helper script `scripts/resolve_merge_conflicts.ps1` to reproduce GitHub CLI conflict-resolution flow for PR branches: fetch base branch, merge, auto-resolve known version-conflict files by keeping branch changes, and stop on unresolved files.
- RU: Добавлен вспомогательный скрипт `scripts/resolve_merge_conflicts.ps1` для CLI-разруливания конфликтов PR-ветки по сценарию GitHub: fetch базовой ветки, merge, авторазрешение известных конфликтных версионных файлов с сохранением изменений ветки и остановка при остаточных конфликтах.

### Changed / Изменено
- EN: Project version bumped to `8.32.3`; Android `versionCode` bumped to `50`.
- RU: Версия проекта повышена до `8.32.3`; Android `versionCode` увеличен до `50`.

## [8.32.2] - 2026-03-14

### Fixed / Исправлено
- EN: Reconciled branch state with the latest code line for conflict-prone versioned files (core/config/bot/android module descriptors) while keeping the Android Gradle plugin fix (`org.jetbrains.kotlin.android`) intact.
- RU: Согласовано состояние ветки с актуальной линией кода для конфликтных файлов с версиями (core/config/bot/android-дескрипторы) с сохранением фикса Android Gradle-плагина (`org.jetbrains.kotlin.android`).

### Changed / Изменено
- EN: Project version bumped to `8.32.2`; Android `versionCode` bumped to `49`.
- RU: Версия проекта повышена до `8.32.2`; Android `versionCode` увеличен до `49`.

## [8.32.1] - 2026-03-14

### Fixed / Исправлено
- EN: Fixed Android Gradle plugin configuration: removed unresolved `org.jetbrains.kotlin.plugin.compose` (not available for Kotlin `1.9.24`) and switched module plugins to standard `org.jetbrains.kotlin.android`, restoring project sync/build in Android Studio.
- RU: Исправлена конфигурация Android Gradle-плагинов: удалён недоступный `org.jetbrains.kotlin.plugin.compose` (для Kotlin `1.9.24`) и модуль переведён на стандартный `org.jetbrains.kotlin.android`, из-за чего снова работает sync/build в Android Studio.

### Changed / Изменено
- EN: Project version bumped to `8.32.1`; Android `versionCode` bumped to `48`.
- RU: Версия проекта повышена до `8.32.1`; Android `versionCode` увеличен до `48`.

## [8.32.0] - 2026-03-14

### Added / Добавлено
- EN: Added PowerShell script `scripts/publish_android_prerelease.ps1` to build Android release APK and publish it as a GitHub prerelease from `develop` (`v<version>-develop`) without changing stable release flow in `main`.
- RU: Добавлен PowerShell-скрипт `scripts/publish_android_prerelease.ps1`, который собирает Android release APK и публикует его как GitHub prerelease из `develop` (`v<версия>-develop`) без изменения стабильного релизного потока в `main`.
- EN: Documented one-command prerelease publishing flow from Android Studio terminal in `README.md`.
- RU: Задокументирован запуск публикации prerelease одной командой из терминала Android Studio в `README.md`.

### Changed / Изменено
- EN: Project version bumped to `8.32.0`; Android `versionCode` bumped to `47`.
- RU: Версия проекта повышена до `8.32.0`; Android `versionCode` увеличен до `47`.

## [8.31.0] - 2026-03-13

### Fixed / Исправлено
- EN: Expanded Android `🧊 ZFS` response to match Telegram detail level: now it returns per-server/per-pool latest states with timestamps from `zfs_pool_status` instead of showing only configured server names.
- RU: Расширен ответ Android по кнопке `🧊 ZFS` до уровня Telegram: теперь возвращаются последние статусы по каждому серверу и пулу с временем из `zfs_pool_status`, а не только список настроенных серверов.
- EN: Added explicit mobile-side handling for missing ZFS data sources (`backups_db` not configured, missing `zfs_pool_status` table, empty dataset) with clear user-facing messages.
- RU: Добавлена явная обработка отсутствующих источников ZFS-данных на mobile API (`backups_db` не настроена, нет таблицы `zfs_pool_status`, пустой набор данных) с понятными сообщениями пользователю.
- EN: Added startup Android version gate: app calls `GET /v1/mobile/version?current_version=...`, blocks main functionality on mismatch, and shows a forced update CTA with APK link.
- RU: Добавлен version-gate для Android при старте: приложение вызывает `GET /v1/mobile/version?current_version=...`, блокирует основной функционал при расхождении версий и показывает обязательное обновление с ссылкой на APK.
- EN: Added BFF endpoint `GET /v1/mobile/version` (and `/api/v1/mobile/version`) with token auth and SemVer-aware update requirement calculation.
- RU: Добавлен BFF endpoint `GET /v1/mobile/version` (и `/api/v1/mobile/version`) с token-auth и расчётом необходимости обновления по SemVer.

### Changed / Изменено
- EN: Project version bumped to `8.31.0`; Android `versionCode` bumped to `46`.
- RU: Версия проекта повышена до `8.31.0`; Android `versionCode` увеличен до `46`.

## [8.30.7] - 2026-03-13

### Fixed / Исправлено
- EN: Extended supplier stock download diagnostics for HTTP sources: added response metadata logging (`status`, `Content-Length`, `chunk_size`, `url`) and detailed `IncompleteRead` context (`bytes_read`, `partial`, `expected_more`, `chunk_count`) to speed up root-cause analysis of intermittent truncation.
- RU: Расширена диагностика загрузки остатков поставщиков по HTTP: добавлено логирование метаданных ответа (`status`, `Content-Length`, `chunk_size`, `url`) и подробного контекста `IncompleteRead` (`bytes_read`, `partial`, `expected_more`, `chunk_count`) для ускорения поиска причины периодических обрывов.

### Changed / Изменено
- EN: Project version bumped to `8.30.7`; Android `versionCode` bumped to `43`.
- RU: Версия проекта повышена до `8.30.7`; Android `versionCode` увеличен до `43`.

## [8.30.6] - 2026-03-13

### Fixed / Исправлено
- EN: Fixed supplier stock HTTP download stability for large files: response body is now read in chunks instead of a single large read, reducing `IncompleteRead(...)` failures on unstable/proxied connections.
- RU: Исправлена стабильность HTTP-загрузки остатков поставщиков для больших файлов: тело ответа теперь читается чанками вместо одного большого чтения, что снижает количество сбоев `IncompleteRead(...)` на нестабильных/проксированных соединениях.

### Changed / Изменено
- EN: Project version bumped to `8.30.6`; Android `versionCode` bumped to `42`.
- RU: Версия проекта повышена до `8.30.6`; Android `versionCode` увеличен до `42`.

## [8.30.5] - 2026-03-13

### Fixed / Исправлено
- EN: Added a global Telegram dispatcher error handler so polling network failures (e.g. `ConnectTimeoutError`/`NetworkError`) are logged as warnings and do not crash with "No error handlers are registered".
- RU: Добавлен глобальный обработчик ошибок Telegram dispatcher: сетевые сбои polling (например, `ConnectTimeoutError`/`NetworkError`) теперь логируются как предупреждения и не валят процесс с "No error handlers are registered".
- EN: Updated polling startup parameters to be more tolerant to unstable networks (`timeout=20`, `read_latency=2.0`).
- RU: Обновлены параметры запуска polling для нестабильной сети (`timeout=20`, `read_latency=2.0`).

### Changed / Изменено
- EN: Project version bumped to `8.30.5`; Android `versionCode` bumped to `41`.
- RU: Версия проекта повышена до `8.30.5`; Android `versionCode` увеличен до `41`.

## [8.30.3] - 2026-03-13

### Fixed / Исправлено
- EN: Fixed Android `🧊 ZFS` action so it responds in Telegram-like style with a configured ZFS servers summary and enabled/disabled markers.
- RU: Исправлена кнопка `🧊 ZFS` в Android: теперь она отвечает в стиле Telegram и показывает сводку настроенных ZFS-серверов с маркерами включено/выключено.

### Changed / Изменено
- EN: Project version bumped to `8.30.3`; Android `versionCode` bumped to `39`.
- RU: Версия проекта повышена до `8.30.3`; Android `versionCode` увеличен до `39`.

## [8.29.0] - 2026-03-12

### Changed / Изменено
- EN: Reworked Android mail backup history block to look closer to Telegram style: compact rows with status icon, backup path, and muted relative time in parentheses.
- RU: Переработан блок истории бэкапов почты в Android под стиль Telegram: компактные строки со статус-иконкой, путём бэкапа и приглушённым временем в скобках.
- EN: Simplified Android launcher icon to a minimal memorable monogram-style mark for better recognition on the home screen.
- RU: Упрощена иконка Android-приложения до лаконичного запоминающегося знака в стиле монограммы для лучшей узнаваемости на домашнем экране.
- EN: Project version bumped to `8.29.0`; Android `versionCode` bumped to `36`.
- RU: Версия проекта повышена до `8.29.0`; Android `versionCode` увеличен до `36`.

## [8.28.0] - 2026-03-12

### Added / Добавлено
- EN: Added Telegram-like mail backup history rendering in Android: mailbox actions now parse and display recent entries with status icons (✅/⚠️/❌), size, path and relative time.
- RU: В Android добавлен вывод истории бэкапов почты как в Telegram: действия выбора ящика теперь парсят и показывают последние записи со статусами (✅/⚠️/❌), размером, путём и относительным временем.

### Changed / Изменено
- EN: Updated Android launcher icon (`ic_launcher_foreground`) to a server/shield/sync visual closer to the provided backup reference style.
- RU: Обновлена иконка Android (`ic_launcher_foreground`) на вариант с сервером/щитом/синхронизацией, ближе к предоставленному референсу бэкапов.
- EN: Project version bumped to `8.28.0`; Android `versionCode` bumped to `35`.
- RU: Версия проекта повышена до `8.28.0`; Android `versionCode` увеличен до `35`.

## [8.25.0] - 2026-03-12

### Fixed / Исправлено
- EN: Added Android submenu toggle behavior for "📬 Mail backups" by analogy with Proxmox and databases: tap now expands/collapses dynamic options and keeps the backup context for selected mailbox actions.
- RU: Добавлено Android-поведение переключения подменю для «📬 Бэкапы почты» по аналогии с Proxmox и БД: нажатие теперь раскрывает/скрывает динамические пункты и сохраняет контекст бэкапов почты для действий выбора ящика.
- EN: Unified Android dynamic backup menus: Proxmox, database, and mail backup sections now work through the same expandable flow from the main menu buttons.
- RU: Унифицированы динамические меню бэкапов в Android: разделы Proxmox, БД и почты теперь работают через единый раскрывающийся сценарий от кнопок главного меню.

### Changed / Изменено
- EN: Project version bumped to `8.25.0`; Android `versionCode` bumped to `32`.
- RU: Версия проекта повышена до `8.25.0`; Android `versionCode` увеличен до `32`.

## [8.24.4] - 2026-03-12

### Fixed / Исправлено
- EN: Fixed Proxmox host selection in mobile control API: `backup_host_*` actions are now processed as valid backup menu actions, so Android server-choice buttons return host backup details instead of `400 INVALID_ACTION`.
- RU: Исправлен выбор Proxmox-хоста в mobile control API: действия `backup_host_*` теперь обрабатываются как валидные backup-команды меню, поэтому кнопки выбора сервера в Android возвращают детали бэкапов хоста вместо `400 INVALID_ACTION`.

### Changed / Изменено
- EN: Project version bumped to `8.24.4`; Android `versionCode` bumped to `30`.
- RU: Версия проекта повышена до `8.24.4`; Android `versionCode` увеличен до `30`.

## [8.24.1] - 2026-03-12

### Fixed / Исправлено
- EN: Improved Telegram alert fan-out for availability incidents: messages are now sent to all configured chats in parallel with retries, reducing inter-chat skew and preventing late delivery to part of chats.
- RU: Улучшена рассылка Telegram-алертов при инцидентах доступности: сообщения теперь отправляются во все настроенные чаты параллельно с повторными попытками, что снижает рассинхрон и убирает позднюю доставку в часть чатов.
- EN: Improved Android DOWN-alert polling cadence: background check moved from 15-minute periodic schedule to chained one-time checks (~1 minute) so unavailability/recovery signals arrive much closer to real time.
- RU: Улучшена частота проверки DOWN-алертов в Android: фоновая проверка переведена с периодических 15 минут на цепочку одноразовых запусков (~1 минута), чтобы события недоступности/восстановления приходили заметно ближе к реальному времени.

### Changed / Изменено
- EN: Project version bumped to `8.24.1`; Android `versionCode` bumped to `27`.
- RU: Версия проекта повышена до `8.24.1`; Android `versionCode` увеличен до `27`.

## [8.23.4] - 2026-03-12

### Fixed / Исправлено
- EN: Fixed Android menu layout for "Proxmox backups": server choice buttons are now rendered inline in the main action list right below "💾 Бэкапы Proxmox" and push following menu items down instead of appearing in the top status card.
- RU: Исправлен layout меню Android для «Бэкапы Proxmox»: кнопки выбора сервера теперь рендерятся прямо в основном списке действий сразу под «💾 Бэкапы Proxmox» и раздвигают пункты ниже, а не появляются в верхней карточке статуса.
- EN: Fixed Android Proxmox server selection flow: tapping a server choice button now triggers the corresponding `backup_host_*` action and shows host backup details like in the Telegram bot flow.
- RU: Исправлен сценарий выбора сервера Proxmox в Android: нажатие кнопки сервера теперь запускает соответствующее действие `backup_host_*` и показывает детали бэкапов хоста как в Telegram-боте.

### Changed / Изменено
- EN: Added accent styling for expandable submenu buttons (server availability/resources and dynamic Proxmox host list) to visually distinguish buttons that appear when a menu section expands.
- RU: Добавлена акцентная стилизация для кнопок раскрывающихся подменю (доступность/ресурсы серверов и динамический список хостов Proxmox), чтобы визуально выделить кнопки, которые появляются при расширении меню.
- EN: Project version bumped to `8.23.4`; Android `versionCode` bumped to `26`.
- RU: Версия проекта повышена до `8.23.4`; Android `versionCode` увеличен до `26`.
## [8.23.1] - 2026-03-11

### Fixed / Исправлено
- EN: Fixed Android compilation error in `MainViewModel`: the mixed API call branch for extension actions now normalizes successful responses to a message string, removing `Unresolved reference: message`.
- RU: Исправлена ошибка компиляции Android в `MainViewModel`: смешанная ветка API-вызовов для действий расширений теперь нормализует успешные ответы в строку сообщения, что убирает `Unresolved reference: message`.

### Changed / Изменено
- EN: Project version bumped to `8.23.1`; Android `versionCode` bumped to `24`.
- RU: Версия проекта повышена до `8.23.1`; Android `versionCode` увеличен до `24`.

## [8.23.0] - 2026-03-11

### Fixed / Исправлено
- EN: Fixed Android action "Proxmox backups": now it returns Telegram-like Proxmox summary plus a server selection menu and supports opening host details from that menu.
- RU: Исправлена Android-кнопка «Бэкапы Proxmox»: теперь возвращается сводка как в Telegram и меню выбора сервера с переходом к деталям по хосту.

### Changed / Изменено
- EN: Added mobile API payload field `menu_options` for control actions to transfer server menu options to Android UI.
- RU: В мобильный API ответов control actions добавлено поле `menu_options` для передачи пунктов меню серверов в Android UI.
- EN: Project version bumped to `8.23.0`; Android `versionCode` bumped to `23`.
- RU: Версия проекта повышена до `8.23.0`; Android `versionCode` увеличен до `23`.

## [8.22.4] - 2026-03-11

### Fixed / Исправлено
- EN: Fixed Android "ZFS" main-menu action: it now uses extensions actions API (`/v1/settings/extensions/actions`) like Telegram bot flow, instead of control actions API.
- RU: Исправлена кнопка «ZFS» в главном меню Android: теперь она использует API действий расширений (`/v1/settings/extensions/actions`) как в Telegram-боте, а не API команд управления.

### Changed / Изменено
- EN: Project version bumped to `8.22.4`; Android `versionCode` bumped to `21`.
- RU: Версия проекта повышена до `8.22.4`; Android `versionCode` увеличен до `21`.

## [8.22.3] - 2026-03-11

### Fixed / Исправлено
- EN: Fixed Android parity for main-menu buttons "Proxmox backups", "DB backups", "Mail backups", and "ZFS": mobile actions now check extension availability like Telegram, and ZFS reads actual `zfs_pool_status` data.
- RU: Исправлен паритет Android-кнопок «Бэкапы Proxmox», «Бэкапы БД», «Бэкапы почты» и «ZFS»: мобильные действия теперь проверяют включённость расширений как в Telegram, а ZFS читает реальные данные из `zfs_pool_status`.

### Changed / Изменено
- EN: Project version bumped to `8.22.3`; Android `versionCode` bumped to `20`.
- RU: Версия проекта повышена до `8.22.3`; Android `versionCode` увеличен до `20`.

## [8.22.1] - 2026-03-11

### Fixed / Исправлено
- EN: Android main menu now expands the server list right after the "Server resources" button, inserting the list between it and the next menu action.
- RU: В Android-главном меню список серверов теперь раскрывается сразу после кнопки «Ресурсы сервера» и вставляется между ней и следующей кнопкой.
- EN: Fixed HTTP 400 for Android main-menu actions "Proxmox backups", "DB backups", "Mail backups", and "ZFS" by routing these actions through extensions API instead of control API.
- RU: Исправлены HTTP 400 для Android-кнопок «Бэкапы Proxmox», «Бэкапы БД», «Бэкапы почты» и «ZFS»: теперь они отправляются через API расширений, а не через API управления.

### Changed / Изменено
- EN: Project version bumped to `8.22.1`; Android `versionCode` bumped to `18`.
- RU: Версия проекта повышена до `8.22.1`; Android `versionCode` увеличен до `18`.

## [8.21.1] - 2026-03-11

### Fixed / Исправлено
- EN: Fixed recovery alert handling in monitoring: restored servers no longer trigger `NameError` (`downtime_start`), so recovery notifications are sent correctly.
- RU: Исправлена обработка алерта при восстановлении в мониторинге: при возврате сервера больше не возникает `NameError` (`downtime_start`), уведомления о восстановлении отправляются корректно.

### Changed / Изменено
- EN: Project version bumped to `8.21.1`; Android `versionCode` bumped to `16`.
- RU: Версия проекта повышена до `8.21.1`; Android `versionCode` увеличен до `16`.

## [8.21.0] - 2026-03-03

### Added / Добавлено
- EN: Added dynamic extension action buttons to the Android main menu for enabled extensions (Telegram bot parity): Proxmox backups, DB backups, mail backups, 1C stock, supplier stock reports, and ZFS.
- RU: В главное меню Android добавлены динамические кнопки действий включённых расширений (паритет с Telegram-ботом): бэкапы Proxmox, бэкапы БД, бэкапы почты, остатки 1С, отчёты остатков поставщиков и ZFS.

### Changed / Изменено
- EN: Android now hides extension-specific main-menu buttons when the corresponding extension is disabled; the server resources section is shown only when `resource_monitor` is enabled.
- RU: Android теперь скрывает кнопки расширений в главном меню, если соответствующее расширение выключено; раздел ресурсов сервера показывается только при включённом `resource_monitor`.
- EN: Project version bumped to `8.21.0`; Android `versionCode` bumped to `15`.
- RU: Версия проекта повышена до `8.21.0`; Android `versionCode` увеличен до `15`.

## [8.17.0] - 2026-03-01

### Fixed / Исправлено
- EN: Fixed Android outage notifications so server names are resolved correctly (including fallback payloads) and not shown as generic IDs.
- RU: Исправлены Android-уведомления о недоступности: имена серверов теперь корректно резолвятся (включая fallback-формат ответа) и не показываются как абстрактные ID.
- EN: Fixed Android notification deep-link handling: after tapping outage notification, down server names are now shown in app status.
- RU: Исправлена обработка deep-link из Android-уведомления: после тапа по уведомлению имена недоступных серверов теперь отображаются в статусе приложения.

### Added / Добавлено
- EN: Added a "Close" button to Android main menu; it moves app task to background and returns user to home screen.
- RU: Добавлена кнопка «Закрыть» в главное меню Android; она сворачивает приложение в фон и возвращает пользователя на рабочий стол.

### Changed / Изменено
- EN: Moved Android main menu action "Refresh data" to the first position for faster access.
- RU: Кнопка «Обновить данные» в главном меню Android перенесена на первое место для быстрого доступа.
- EN: Project version bumped to `8.17.0`; Android `versionCode` bumped to `11`.
- RU: Версия проекта повышена до `8.17.0`; Android `versionCode` увеличен до `11`.

## [8.15.0] - 2026-03-01

### Fixed / Исправлено
- EN: Fixed Android outage push logic: alerts now trigger for extended outage statuses (`DOWN`, `UNREACHABLE`, `OFFLINE`, `ERROR`, `CRITICAL`) so notifications arrive when a server is actually unavailable.
- RU: Исправлена логика push-оповещений об авариях в Android: алерты теперь срабатывают и для расширенных статусов недоступности (`DOWN`, `UNREACHABLE`, `OFFLINE`, `ERROR`, `CRITICAL`), поэтому уведомления приходят при реальной недоступности сервера.
- EN: Fixed availability summary counting in Android so non-UP outage states are counted as DOWN in the UI.
- RU: Исправлен подсчёт сводки доступности в Android: все нерабочие статусы теперь считаются как DOWN в интерфейсе.

### Added / Добавлено
- EN: Added a dedicated "Refresh data" action in the Android main menu to quickly sync settings and server availability in one tap.
- RU: Добавлена отдельная кнопка «Обновить данные» в главном меню Android для быстрого обновления настроек и доступности серверов одним нажатием.
- EN: Added explicit light/dark theme buttons in Android settings for quick direct switching.
- RU: Добавлены явные кнопки светлой/тёмной темы в настройках Android для быстрого прямого переключения.

### Changed / Изменено
- EN: Project version bumped to `8.15.0`; Android `versionCode` bumped to `10`.
- RU: Версия проекта повышена до `8.15.0`; Android `versionCode` увеличен до `10`.

## [8.13.0] - 2026-02-27

### Fixed / Исправлено
- EN: Fixed targeted server availability in Android by switching the button action to a dedicated single-server API request (`GET /v1/monitoring/availability/{server_id}`), aligned with Telegram bot behavior.
- RU: Исправлена точечная проверка доступности сервера в Android: по кнопке теперь идёт отдельный запрос для одного сервера (`GET /v1/monitoring/availability/{server_id}`), как в Telegram-боте.
- EN: Fixed Android server availability feedback placement: the current request result is now shown inside the server button group, directly above the server button that initiated it.
- RU: Исправлено размещение результата проверки в Android: сообщение текущего запроса теперь выводится внутри группы серверов, прямо над кнопкой запрошенного сервера.

### Added / Добавлено
- EN: Added BFF endpoint `GET /v1/monitoring/availability/{server_id}` (and `/api/v1/...`) with token auth, server lookup, and direct status check.
- RU: Добавлен BFF endpoint `GET /v1/monitoring/availability/{server_id}` (и `/api/v1/...`) с token-auth, поиском сервера и прямой проверкой статуса.

### Changed / Изменено
- EN: Project version bumped to `8.13.0`; Android `versionCode` bumped to `8`.
- RU: Версия проекта повышена до `8.13.0`; Android `versionCode` увеличен до `8`.

## [8.12.3] - 2026-02-27

### Fixed / Исправлено
- EN: Removed duplicate Android-version output from bot and Android app screens; now project version is shown once.
- RU: Убрано дублирующее отображение Android-версии в боте и Android-приложении; теперь показывается одна версия проекта.
- EN: Fixed targeted server availability in Android submenu by improving server matching (IP/name with bracketed and quoted formats).
- RU: Исправлена проверка доступности выбранного сервера в Android-подменю: улучшено сопоставление серверов (IP/имя, варианты со скобками и кавычками).

### Changed / Изменено
- EN: Project version bumped to `8.12.3`; Android `versionCode` bumped to `6`.
- RU: Версия проекта повышена до `8.12.3`; Android `versionCode` увеличен до `6`.

## [8.11.2] - 2026-02-28

### Fixed / Исправлено
- EN: Fixed broken Cyrillic encoding in Android UI labels, messages, and status texts.
- RU: Исправлена сломанная кириллическая кодировка в Android UI (подписи, сообщения и статусы).

### Changed / Изменено
- EN: Unified bot and Android release version to 8.11.2 for GitHub release consistency.
- RU: Синхронизированы версии бота и Android-приложения до 8.11.2 для единообразной фиксации релизов на GitHub.

## [8.11.1] - 2026-02-28

### Fixed / Исправлено
- EN: Restored export of ANDROID_APP_VERSION and APP_VERSION from config package to prevent startup ImportError in core.monitor.
- RU: Восстановлен экспорт ANDROID_APP_VERSION и APP_VERSION из пакета config, чтобы убрать ImportError при старте в core.monitor.
- EN: Enabled Android BuildConfig generation explicitly in app Gradle config to fix Unresolved reference: BuildConfig in MainViewModel.
- RU: Явно включена генерация Android BuildConfig в Gradle-конфиге приложения для устранения Unresolved reference: BuildConfig в MainViewModel.

### Changed / Изменено
- EN: Unified bot and Android release version to 8.11.1 for GitHub release consistency.
- RU: Синхронизированы версии бота и Android-приложения до 8.11.1 для единообразной фиксации релизов на GitHub.
- EN: Android `versionCode` bumped to 4.
- RU: Для Android увеличен `versionCode` до 4.

## [8.11.0] - 2026-02-27

### Added / Добавлено
- EN: Android server availability now opens as a button-driven server list (similar to Telegram bot) and shows selected server status in the top status card.
- RU: В Android проверка доступности сервера теперь открывается как список кнопок серверов (как в Telegram-боте), а статус выбранного сервера показывается в верхнем блоке статуса.
- EN: Android status card now shows bot version and Android app version.
- RU: В блоке статуса Android теперь отображаются версия бота и версия Android-приложения.
- EN: Telegram bot now displays Android app version in status/about responses.
- RU: В Telegram-боте добавлено отображение версии Android-приложения в статусе/информации.

### Changed / Изменено
- EN: Theme switch was removed from the main Android screen and left in Settings (Appearance section).
- RU: Переключение темы убрано с главного экрана Android и оставлено в настройках (раздел "Оформление").
- EN: Removed the helper text "Tap Refresh..." from Android status block.
- RU: Из блока статуса Android убрана подсказка "Нажми Обновить...".
- EN: Removed the bottom "Server list" section from Android main screen.
- RU: Убран нижний блок "Список серверов" с главного экрана Android.

## [8.10.0] - 2026-02-27

### Added / Добавлено
- EN: Android now stores morning report text locally and shows it in-app after push delivery.
- RU: В Android утренний отчет теперь сохраняется локально и отображается в приложении после push-уведомления.
- EN: Added morning report actions in Android UI: `Read` and `Close`.
- RU: В Android добавлены действия для утреннего отчета: `Прочитано` и `Закрыть`.
- EN: Added server availability lookup in Android by server ID/name.
- RU: В Android добавлена проверка доступности конкретного сервера по ID/имени.

### Changed / Изменено
- EN: Tapping a morning report push notification now opens Android app and the saved report.
- RU: Нажатие на push с утренним отчетом теперь открывает Android-приложение и сохраненный отчет.
- EN: Theme switching in Android is now visible as a quick toggle on the main screen.
- RU: Переключение темы в Android стало доступно через быстрый переключатель на главном экране.

## [8.9.0] - 2026-02-27

### Changed / Изменено
- EN: Removed TamTam bot integration from runtime, alert routing, and bot settings flows.
- RU: Удалена интеграция TamTam-бота из рантайма, маршрутизации алертов и сценариев настроек бота.

## [8.8.0] - 2026-02-26

### Added / Добавлено
- EN: Android scheduled morning report delivery via background worker with push notification and sound.
- RU: В Android добавлена доставка утреннего отчета по расписанию через фоновый worker с push-уведомлением и звуком.
- EN: Android runtime request for notification permission (`POST_NOTIFICATIONS`, Android 13+).
- RU: В Android добавлен runtime-запрос разрешения на уведомления (`POST_NOTIFICATIONS`, Android 13+).
- EN: App setting to enable/disable scheduled morning report notifications.
- RU: Добавлена настройка включения/выключения плановых уведомлений утреннего отчета.
- EN: App setting to switch between dark and light themes.
- RU: Добавлена настройка переключения между темной и светлой темами.

### Changed / Изменено
- EN: Dark theme is now default in Android app.
- RU: Темная тема установлена по умолчанию в Android-приложении.
- EN: Morning report notifications are now scheduled using configured report time.
- RU: Планирование уведомлений утреннего отчета теперь использует настроенное время отчета.

## [8.7.0] - 2026-02-26

### Added / Добавлено
- EN: New BFF API for server settings management:
  - `GET /v1/settings/servers`
  - `POST /v1/settings/servers`
  - `PATCH /v1/settings/servers/{ip}`
  - `PATCH /v1/settings/servers/{ip}/enabled`
  - `DELETE /v1/settings/servers/{ip}`
- RU: Добавлен новый BFF API для управления серверами в настройках (получение, добавление, редактирование, включение/выключение мониторинга, удаление).
- EN: Android settings include a dedicated `Серверы` section with CRUD and monitoring enable/disable actions.
- RU: В Android-приложение добавлен раздел `Серверы` с CRUD-операциями и включением/выключением мониторинга.

### Changed / Изменено
- EN: `config.db_settings_app.SettingsManager` extended for server management: `enabled` on create, include disabled servers, partial updates.
- RU: `config.db_settings_app.SettingsManager` расширен для управления серверами: `enabled` при создании, выборка отключенных серверов, частичные обновления.

## [8.6.0] - 2026-02-26

### Added / Добавлено
- EN: Android/BFF: expanded Windows server types management in mobile settings (create, rename, merge, delete).
- RU: В Android/BFF расширено управление типами Windows-серверов (создание, переименование, объединение, удаление).
- EN: BFF API endpoints for Windows credentials and Windows server type operations.
- RU: Добавлены BFF API endpoints для Windows-учетных записей и операций с типами серверов Windows.
- EN: `CHANGELOG.md` introduced.
- RU: Добавлен файл `CHANGELOG.md`.

### Changed / Изменено
- EN: Android settings section label changed from `Auth` to `Аутентификация`.
- RU: В Android раздел настроек переименован с `Auth` на `Аутентификация`.
- EN: Removed extra nested `Аутентификация` button in Android auth screen.
- RU: Удалена лишняя вложенная кнопка `Аутентификация` в экране auth-настроек Android.
- EN: Android settings sync now loads Windows credentials from `/v1/settings/auth/windows-credentials`.
- RU: Синхронизация настроек Android теперь подтягивает Windows-учетки из `/v1/settings/auth/windows-credentials`.

### Fixed / Исправлено
- EN: Android `Просмотр всех учетных записей` no longer depends only on aggregate auth payload.
- RU: В Android `Просмотр всех учетных записей` больше не зависит только от агрегированного auth-ответа.
