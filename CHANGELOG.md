# Changelog / История изменений

All notable changes to this project are documented in this file.  
Все значимые изменения проекта фиксируются в этом файле.

The project follows Semantic Versioning (SemVer).  
Проект использует Semantic Versioning (SemVer).

## [8.40.4] - 2026-04-02

### Fixed / Исправлено
- EN: Fixed Compact Ops mail tile data source in the Android Ops Center: latest mail backup volume is now parsed directly from `backup_mail` control response/history and shown in the `почта` tile instead of false `нет данных`.
- RU: Исправлен источник данных для плашки `почта` в Android оперативном центре: объём последнего почтового бэкапа теперь парсится напрямую из ответа/истории `backup_mail` и отображается вместо ложного `нет данных`.

### Changed / Изменено
- EN: Added pull-to-refresh gesture for the Android app main screen (`pull down to sync`), wired to full data refresh (settings + availability), similar to browser page refresh.
- RU: Для главного экрана Android-приложения добавлен жест pull-to-refresh (`потянуть вниз для синхронизации`), который запускает полное обновление данных (настройки + доступность) по аналогии с обновлением страницы в браузере.
- EN: Completed repository-wide SemVer patch bump to `8.40.4`; synchronized runtime/config/docs/mobile references, updated Android metadata to `ANDROID_VERSION_NAME=8.40.4` and `ANDROID_VERSION_CODE=238`, and refreshed prerelease links.
- RU: Выполнен репозиторный SemVer patch-бамп до `8.40.4`; синхронизированы ссылки на версию в runtime/config/docs/mobile, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.40.4` и `ANDROID_VERSION_CODE=238`, а также обновлены prerelease-ссылки.

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
