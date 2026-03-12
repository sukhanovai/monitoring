# Changelog / История изменений

All notable changes to this project are documented in this file.  
Все значимые изменения проекта фиксируются в этом файле.

The project follows Semantic Versioning (SemVer).  
Проект использует Semantic Versioning (SemVer).

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
