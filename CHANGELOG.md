# Changelog / История изменений

All notable changes to this project are documented in this file.  
Все значимые изменения проекта фиксируются в этом файле.

The project follows Semantic Versioning (SemVer).  
Проект использует Semantic Versioning (SemVer).

## [8.20.0] - 2026-03-03

### Added / Добавлено
- EN: Added Android extensions section with Telegram-bot parity: list all extensions with status and allow per-extension enable/disable.
- RU: Добавлен раздел «Расширения» в Android по паритету с Telegram-ботом: отображается список всех расширений со статусом и доступно включение/выключение каждого.
- EN: Added Android bulk actions for extensions: “Enable all” and “Disable all”.
- RU: Добавлены массовые действия для расширений в Android: «Включить все» и «Отключить все».
- EN: Added BFF API endpoints for mobile extensions management: `GET /v1/settings/extensions`, `PATCH /v1/settings/extensions/{extension_id}`, `POST /v1/settings/extensions/actions`.
- RU: Добавлены BFF API endpoint’ы для управления расширениями с мобильного клиента: `GET /v1/settings/extensions`, `PATCH /v1/settings/extensions/{extension_id}`, `POST /v1/settings/extensions/actions`.

### Changed / Изменено
- EN: Project version bumped to `8.20.0`; Android `versionCode` bumped to `14`.
- RU: Версия проекта повышена до `8.20.0`; Android `versionCode` увеличен до `14`.
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
