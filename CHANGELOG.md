## [8.11.2] - 2026-02-28

- EN: Fixed broken Cyrillic encoding in Android UI labels, messages, and status texts.
- RU: Исправлена сломанная кириллическая кодировка в Android UI (подписи, сообщения и статусы).
- EN: Unified bot and Android release version to 8.11.2 for GitHub release consistency.
- RU: Синхронизированы версии бота и Android-приложения до 8.11.2 для единообразной фиксации релизов на GitHub.

The project follows Semantic Versioning (SemVer).  
ÐŸÑ€Ð¾ÐµÐºÑ‚ Ð¸ÑÐ¿Ð¾Ð»ÑŒÐ·ÑƒÐµÑ‚ Semantic Versioning (SemVer).

## [8.11.1] - 2026-02-28

### Fixed / Ð˜ÑÐ¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¾
- EN: Restored export of ANDROID_APP_VERSION and APP_VERSION from config package to prevent startup ImportError in core.monitor.
- RU: Ð’Ð¾ÑÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½ ÑÐºÑÐ¿Ð¾Ñ€Ñ‚ ANDROID_APP_VERSION Ð¸ APP_VERSION Ð¸Ð· Ð¿Ð°ÐºÐµÑ‚Ð° config, Ñ‡Ñ‚Ð¾Ð±Ñ‹ ÑƒÐ±Ñ€Ð°Ñ‚ÑŒ ImportError Ð¿Ñ€Ð¸ ÑÑ‚Ð°Ñ€Ñ‚Ðµ Ð² core.monitor.
- EN: Enabled Android BuildConfig generation explicitly in app Gradle config to fix Unresolved reference: BuildConfig in MainViewModel.
- RU: Ð¯Ð²Ð½Ð¾ Ð²ÐºÐ»ÑŽÑ‡ÐµÐ½Ð° Ð³ÐµÐ½ÐµÑ€Ð°Ñ†Ð¸Ñ Android BuildConfig Ð² Gradle-ÐºÐ¾Ð½Ñ„Ð¸Ð³Ðµ Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ñ Ð´Ð»Ñ ÑƒÑÑ‚Ñ€Ð°Ð½ÐµÐ½Ð¸Ñ Unresolved reference: BuildConfig Ð² MainViewModel.

### Changed / Ð˜Ð·Ð¼ÐµÐ½ÐµÐ½Ð¾
- EN: Unified bot and Android release version to 8.11.1 for GitHub release consistency.
- RU: Ð¡Ð¸Ð½Ñ…Ñ€Ð¾Ð½Ð¸Ð·Ð¸Ñ€Ð¾Ð²Ð°Ð½Ñ‹ Ð²ÐµÑ€ÑÐ¸Ð¸ Ð±Ð¾Ñ‚Ð° Ð¸ Android-Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ñ Ð´Ð¾ 8.11.1 Ð´Ð»Ñ ÐµÐ´Ð¸Ð½Ð¾Ð¾Ð±Ñ€Ð°Ð·Ð½Ð¾Ð¹ Ñ„Ð¸ÐºÑÐ°Ñ†Ð¸Ð¸ Ñ€ÐµÐ»Ð¸Ð·Ð¾Ð² Ð½Ð° GitHub.
- EN: Android `versionCode` bumped to 4.
- RU: Ð”Ð»Ñ Android ÑƒÐ²ÐµÐ»Ð¸Ñ‡ÐµÐ½ `versionCode` Ð´Ð¾ 4.

## [8.11.0] - 2026-02-27

### Added / Äîáàâëåíî
- EN: Android server availability now opens as a button-driven server list (similar to Telegram bot) and shows selected server status in the top status card.
- RU: Â Android ïðîâåðêà äîñòóïíîñòè ñåðâåðà òåïåðü îòêðûâàåòñÿ êàê ñïèñîê êíîïîê ñåðâåðîâ (êàê â Telegram-áîòå), à ñòàòóñ âûáðàííîãî ñåðâåðà ïîêàçûâàåòñÿ â âåðõíåì áëîêå ñòàòóñà.
- EN: Android status card now shows bot version and Android app version.
- RU: Â áëîêå ñòàòóñà Android òåïåðü îòîáðàæàþòñÿ âåðñèÿ áîòà è âåðñèÿ Android-ïðèëîæåíèÿ.
- EN: Telegram bot now displays Android app version in status/about responses.
- RU: Â Telegram-áîòå äîáàâëåíî îòîáðàæåíèå âåðñèè Android-ïðèëîæåíèÿ â ñòàòóñå/èíôîðìàöèè.

### Changed / Èçìåíåíî
- EN: Theme switch was removed from the main Android screen and left in Settings (Appearance section).
- RU: Ïåðåêëþ÷åíèå òåìû óáðàíî ñ ãëàâíîãî ýêðàíà Android è îñòàâëåíî â íàñòðîéêàõ (ðàçäåë "Îôîðìëåíèå").
- EN: Removed the helper text "Tap Refresh..." from Android status block.
- RU: Èç áëîêà ñòàòóñà Android óáðàíà ïîäñêàçêà "Íàæìè Îáíîâèòü...".
- EN: Removed the bottom "Server list" section from Android main screen.
- RU: Óáðàí íèæíèé áëîê "Ñïèñîê ñåðâåðîâ" ñ ãëàâíîãî ýêðàíà Android.

## [8.10.0] - 2026-02-27

### Added / Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð¾
- EN: Android now stores morning report text locally and shows it in-app after push delivery.
- RU: Ð’ Android ÑƒÑ‚Ñ€ÐµÐ½Ð½Ð¸Ð¹ Ð¾Ñ‚Ñ‡ÐµÑ‚ Ñ‚ÐµÐ¿ÐµÑ€ÑŒ ÑÐ¾Ñ…Ñ€Ð°Ð½ÑÐµÑ‚ÑÑ Ð»Ð¾ÐºÐ°Ð»ÑŒÐ½Ð¾ Ð¸ Ð¾Ñ‚Ð¾Ð±Ñ€Ð°Ð¶Ð°ÐµÑ‚ÑÑ Ð² Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ð¸ Ð¿Ð¾ÑÐ»Ðµ push-ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ñ.
- EN: Added morning report actions in Android UI: `Read` and `Close`.
- RU: Ð’ Android Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ‹ Ð´ÐµÐ¹ÑÑ‚Ð²Ð¸Ñ Ð´Ð»Ñ ÑƒÑ‚Ñ€ÐµÐ½Ð½ÐµÐ³Ð¾ Ð¾Ñ‚Ñ‡ÐµÑ‚Ð°: `ÐŸÑ€Ð¾Ñ‡Ð¸Ñ‚Ð°Ð½Ð¾` Ð¸ `Ð—Ð°ÐºÑ€Ñ‹Ñ‚ÑŒ`.
- EN: Added server availability lookup in Android by server ID/name.
- RU: Ð’ Android Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð° Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð¾ÑÑ‚Ð¸ ÐºÐ¾Ð½ÐºÑ€ÐµÑ‚Ð½Ð¾Ð³Ð¾ ÑÐµÑ€Ð²ÐµÑ€Ð° Ð¿Ð¾ ID/Ð¸Ð¼ÐµÐ½Ð¸.

### Changed / Ð˜Ð·Ð¼ÐµÐ½ÐµÐ½Ð¾
- EN: Tapping a morning report push notification now opens Android app and the saved report.
- RU: ÐÐ°Ð¶Ð°Ñ‚Ð¸Ðµ Ð½Ð° push Ñ ÑƒÑ‚Ñ€ÐµÐ½Ð½Ð¸Ð¼ Ð¾Ñ‚Ñ‡ÐµÑ‚Ð¾Ð¼ Ñ‚ÐµÐ¿ÐµÑ€ÑŒ Ð¾Ñ‚ÐºÑ€Ñ‹Ð²Ð°ÐµÑ‚ Android-Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ Ð¸ ÑÐ¾Ñ…Ñ€Ð°Ð½ÐµÐ½Ð½Ñ‹Ð¹ Ð¾Ñ‚Ñ‡ÐµÑ‚.
- EN: Theme switching in Android is now visible as a quick toggle on the main screen.
- RU: ÐŸÐµÑ€ÐµÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ðµ Ñ‚ÐµÐ¼Ñ‹ Ð² Android ÑÑ‚Ð°Ð»Ð¾ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ð¾ Ñ‡ÐµÑ€ÐµÐ· Ð±Ñ‹ÑÑ‚Ñ€Ñ‹Ð¹ Ð¿ÐµÑ€ÐµÐºÐ»ÑŽÑ‡Ð°Ñ‚ÐµÐ»ÑŒ Ð½Ð° Ð³Ð»Ð°Ð²Ð½Ð¾Ð¼ ÑÐºÑ€Ð°Ð½Ðµ.

## [8.9.0] - 2026-02-27

### Changed / Ð˜Ð·Ð¼ÐµÐ½ÐµÐ½Ð¾
- EN: Removed TamTam bot integration from runtime, alert routing, and bot settings flows.
- RU: Ð£Ð´Ð°Ð»ÐµÐ½Ð° Ð¸Ð½Ñ‚ÐµÐ³Ñ€Ð°Ñ†Ð¸Ñ TamTam-Ð±Ð¾Ñ‚Ð° Ð¸Ð· Ñ€Ð°Ð½Ñ‚Ð°Ð¹Ð¼Ð°, Ð¼Ð°Ñ€ÑˆÑ€ÑƒÑ‚Ð¸Ð·Ð°Ñ†Ð¸Ð¸ Ð°Ð»ÐµÑ€Ñ‚Ð¾Ð² Ð¸ ÑÑ†ÐµÐ½Ð°Ñ€Ð¸ÐµÐ² Ð½Ð°ÑÑ‚Ñ€Ð¾ÐµÐº Ð±Ð¾Ñ‚Ð°.

## [8.8.0] - 2026-02-26

### Added / Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð¾
- EN: Android scheduled morning report delivery via background worker with push notification and sound.
- RU: Ð’ Android Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð° Ð´Ð¾ÑÑ‚Ð°Ð²ÐºÐ° ÑƒÑ‚Ñ€ÐµÐ½Ð½ÐµÐ³Ð¾ Ð¾Ñ‚Ñ‡ÐµÑ‚Ð° Ð¿Ð¾ Ñ€Ð°ÑÐ¿Ð¸ÑÐ°Ð½Ð¸ÑŽ Ñ‡ÐµÑ€ÐµÐ· Ñ„Ð¾Ð½Ð¾Ð²Ñ‹Ð¹ worker Ñ push-ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸ÐµÐ¼ Ð¸ Ð·Ð²ÑƒÐºÐ¾Ð¼.
- EN: Android runtime request for notification permission (`POST_NOTIFICATIONS`, Android 13+).
- RU: Ð’ Android Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½ runtime-Ð·Ð°Ð¿Ñ€Ð¾Ñ Ñ€Ð°Ð·Ñ€ÐµÑˆÐµÐ½Ð¸Ñ Ð½Ð° ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ñ (`POST_NOTIFICATIONS`, Android 13+).
- EN: App setting to enable/disable scheduled morning report notifications.
- RU: Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð° Ð½Ð°ÑÑ‚Ñ€Ð¾Ð¹ÐºÐ° Ð²ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ñ/Ð²Ñ‹ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ñ Ð¿Ð»Ð°Ð½Ð¾Ð²Ñ‹Ñ… ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ð¹ ÑƒÑ‚Ñ€ÐµÐ½Ð½ÐµÐ³Ð¾ Ð¾Ñ‚Ñ‡ÐµÑ‚Ð°.
- EN: App setting to switch between dark and light themes.
- RU: Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð° Ð½Ð°ÑÑ‚Ñ€Ð¾Ð¹ÐºÐ° Ð¿ÐµÑ€ÐµÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ñ Ð¼ÐµÐ¶Ð´Ñƒ Ñ‚ÐµÐ¼Ð½Ð¾Ð¹ Ð¸ ÑÐ²ÐµÑ‚Ð»Ð¾Ð¹ Ñ‚ÐµÐ¼Ð°Ð¼Ð¸.

### Changed / Ð˜Ð·Ð¼ÐµÐ½ÐµÐ½Ð¾
- EN: Dark theme is now default in Android app.
- RU: Ð¢ÐµÐ¼Ð½Ð°Ñ Ñ‚ÐµÐ¼Ð° ÑƒÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð° Ð¿Ð¾ ÑƒÐ¼Ð¾Ð»Ñ‡Ð°Ð½Ð¸ÑŽ Ð² Android-Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ð¸.
- EN: Morning report notifications are now scheduled using configured report time.
- RU: ÐŸÐ»Ð°Ð½Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ðµ ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ð¹ ÑƒÑ‚Ñ€ÐµÐ½Ð½ÐµÐ³Ð¾ Ð¾Ñ‚Ñ‡ÐµÑ‚Ð° Ñ‚ÐµÐ¿ÐµÑ€ÑŒ Ð¸ÑÐ¿Ð¾Ð»ÑŒÐ·ÑƒÐµÑ‚ Ð½Ð°ÑÑ‚Ñ€Ð¾ÐµÐ½Ð½Ð¾Ðµ Ð²Ñ€ÐµÐ¼Ñ Ð¾Ñ‚Ñ‡ÐµÑ‚Ð°.

## [8.7.0] - 2026-02-26

### Added / Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð¾
- EN: New BFF API for server settings management:
  - `GET /v1/settings/servers`
  - `POST /v1/settings/servers`
  - `PATCH /v1/settings/servers/{ip}`
  - `PATCH /v1/settings/servers/{ip}/enabled`
  - `DELETE /v1/settings/servers/{ip}`
- RU: Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½ Ð½Ð¾Ð²Ñ‹Ð¹ BFF API Ð´Ð»Ñ ÑƒÐ¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¸Ñ ÑÐµÑ€Ð²ÐµÑ€Ð°Ð¼Ð¸ Ð² Ð½Ð°ÑÑ‚Ñ€Ð¾Ð¹ÐºÐ°Ñ… (Ð¿Ð¾Ð»ÑƒÑ‡ÐµÐ½Ð¸Ðµ, Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð¸Ðµ, Ñ€ÐµÐ´Ð°ÐºÑ‚Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ðµ, Ð²ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ðµ/Ð²Ñ‹ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ðµ Ð¼Ð¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³Ð°, ÑƒÐ´Ð°Ð»ÐµÐ½Ð¸Ðµ).
- EN: Android settings include a dedicated `Ð¡ÐµÑ€Ð²ÐµÑ€Ñ‹` section with CRUD and monitoring enable/disable actions.
- RU: Ð’ Android-Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½ Ñ€Ð°Ð·Ð´ÐµÐ» `Ð¡ÐµÑ€Ð²ÐµÑ€Ñ‹` Ñ CRUD-Ð¾Ð¿ÐµÑ€Ð°Ñ†Ð¸ÑÐ¼Ð¸ Ð¸ Ð²ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸ÐµÐ¼/Ð²Ñ‹ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸ÐµÐ¼ Ð¼Ð¾Ð½Ð¸Ñ‚Ð¾Ñ€Ð¸Ð½Ð³Ð°.

### Changed / Ð˜Ð·Ð¼ÐµÐ½ÐµÐ½Ð¾
- EN: `config.db_settings_app.SettingsManager` extended for server management: `enabled` on create, include disabled servers, partial updates.
- RU: `config.db_settings_app.SettingsManager` Ñ€Ð°ÑÑˆÐ¸Ñ€ÐµÐ½ Ð´Ð»Ñ ÑƒÐ¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¸Ñ ÑÐµÑ€Ð²ÐµÑ€Ð°Ð¼Ð¸: `enabled` Ð¿Ñ€Ð¸ ÑÐ¾Ð·Ð´Ð°Ð½Ð¸Ð¸, Ð²Ñ‹Ð±Ð¾Ñ€ÐºÐ° Ð¾Ñ‚ÐºÐ»ÑŽÑ‡ÐµÐ½Ð½Ñ‹Ñ… ÑÐµÑ€Ð²ÐµÑ€Ð¾Ð², Ñ‡Ð°ÑÑ‚Ð¸Ñ‡Ð½Ñ‹Ðµ Ð¾Ð±Ð½Ð¾Ð²Ð»ÐµÐ½Ð¸Ñ.

## [8.6.0] - 2026-02-26

### Added / Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ð¾
- EN: Android/BFF: expanded Windows server types management in mobile settings (create, rename, merge, delete).
- RU: Ð’ Android/BFF Ñ€Ð°ÑÑˆÐ¸Ñ€ÐµÐ½Ð¾ ÑƒÐ¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¸Ðµ Ñ‚Ð¸Ð¿Ð°Ð¼Ð¸ Windows-ÑÐµÑ€Ð²ÐµÑ€Ð¾Ð² (ÑÐ¾Ð·Ð´Ð°Ð½Ð¸Ðµ, Ð¿ÐµÑ€ÐµÐ¸Ð¼ÐµÐ½Ð¾Ð²Ð°Ð½Ð¸Ðµ, Ð¾Ð±ÑŠÐµÐ´Ð¸Ð½ÐµÐ½Ð¸Ðµ, ÑƒÐ´Ð°Ð»ÐµÐ½Ð¸Ðµ).
- EN: BFF API endpoints for Windows credentials and Windows server type operations.
- RU: Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ‹ BFF API endpoints Ð´Ð»Ñ Windows-ÑƒÑ‡ÐµÑ‚Ð½Ñ‹Ñ… Ð·Ð°Ð¿Ð¸ÑÐµÐ¹ Ð¸ Ð¾Ð¿ÐµÑ€Ð°Ñ†Ð¸Ð¹ Ñ Ñ‚Ð¸Ð¿Ð°Ð¼Ð¸ ÑÐµÑ€Ð²ÐµÑ€Ð¾Ð² Windows.
- EN: `CHANGELOG.md` introduced.
- RU: Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½ Ñ„Ð°Ð¹Ð» `CHANGELOG.md`.

### Changed / Ð˜Ð·Ð¼ÐµÐ½ÐµÐ½Ð¾
- EN: Android settings section label changed from `Auth` to `ÐÑƒÑ‚ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ`.
- RU: Ð’ Android Ñ€Ð°Ð·Ð´ÐµÐ» Ð½Ð°ÑÑ‚Ñ€Ð¾ÐµÐº Ð¿ÐµÑ€ÐµÐ¸Ð¼ÐµÐ½Ð¾Ð²Ð°Ð½ Ñ `Auth` Ð½Ð° `ÐÑƒÑ‚ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ`.
- EN: Removed extra nested `ÐÑƒÑ‚ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ` button in Android auth screen.
- RU: Ð£Ð´Ð°Ð»ÐµÐ½Ð° Ð»Ð¸ÑˆÐ½ÑÑ Ð²Ð»Ð¾Ð¶ÐµÐ½Ð½Ð°Ñ ÐºÐ½Ð¾Ð¿ÐºÐ° `ÐÑƒÑ‚ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ` Ð² ÑÐºÑ€Ð°Ð½Ðµ auth-Ð½Ð°ÑÑ‚Ñ€Ð¾ÐµÐº Android.
- EN: Android settings sync now loads Windows credentials from `/v1/settings/auth/windows-credentials`.
- RU: Ð¡Ð¸Ð½Ñ…Ñ€Ð¾Ð½Ð¸Ð·Ð°Ñ†Ð¸Ñ Ð½Ð°ÑÑ‚Ñ€Ð¾ÐµÐº Android Ñ‚ÐµÐ¿ÐµÑ€ÑŒ Ð¿Ð¾Ð´Ñ‚ÑÐ³Ð¸Ð²Ð°ÐµÑ‚ Windows-ÑƒÑ‡ÐµÑ‚ÐºÐ¸ Ð¸Ð· `/v1/settings/auth/windows-credentials`.

### Fixed / Ð˜ÑÐ¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¾
- EN: Android `ÐŸÑ€Ð¾ÑÐ¼Ð¾Ñ‚Ñ€ Ð²ÑÐµÑ… ÑƒÑ‡ÐµÑ‚Ð½Ñ‹Ñ… Ð·Ð°Ð¿Ð¸ÑÐµÐ¹` no longer depends only on aggregate auth payload.
- RU: Ð’ Android `ÐŸÑ€Ð¾ÑÐ¼Ð¾Ñ‚Ñ€ Ð²ÑÐµÑ… ÑƒÑ‡ÐµÑ‚Ð½Ñ‹Ñ… Ð·Ð°Ð¿Ð¸ÑÐµÐ¹` Ð±Ð¾Ð»ÑŒÑˆÐµ Ð½Ðµ Ð·Ð°Ð²Ð¸ÑÐ¸Ñ‚ Ñ‚Ð¾Ð»ÑŒÐºÐ¾ Ð¾Ñ‚ Ð°Ð³Ñ€ÐµÐ³Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð½Ð¾Ð³Ð¾ auth-Ð¾Ñ‚Ð²ÐµÑ‚Ð°.