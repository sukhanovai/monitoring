## [8.62.42] - 2026-05-21

### Added
- RU: Matrix command-bot и Android-приложение теперь поддерживают расширение «📸 Передачи ZFS-снэпшотов» — паритет с Telegram-ботом. Раньше расширение `snapshot_transfer_monitor` парсило письма о STARTED/SUCCESS/SKIPPED/ERROR/BUSY и складывало результаты в таблицу `snapshot_transfers`, но просмотреть их можно было только через Telegram-меню «📸 Передачи снэпшотов» — Matrix-бот в `!extensions` его не показывал («им нечего показать командой»), а в Android-приложении плашки и диалога не было вовсе. Бэкенд расширил эндпоинт `/v1/control/actions`: новые действия `snapshot_transfer_menu` (сводка по хостам + последние 8 распарсенных писем + кнопки на хосты) и `snapshot_transfer_host_<host>` (последние 15 записей по конкретному хосту) собирают данные из `SNAPSHOT_TRANSFER_HOSTS` и таблицы `snapshot_transfers`, проверяя включённость расширения. Matrix-бот получил команду `!snapshots` и кнопку-реакцию `📸` в подменю `!extensions`, выводящие тот же отчёт через `_handle_ext_snapshot_transfer`. Android-клиент рендерит плашку «📸 снэпшоты» с соотношением `ok/total` (зелёный при `🔴 0`, красный иначе) рядом с остальными `OpsMetricTile`-ами расширений; тап открывает `AlertDialog` с заголовком, кнопкой «🔄 Обновить» и текстом ответа сервера, под которым кнопки-хосты ведут на `snapshot_transfer_host_<host>` — детализацию по 15 записям.
- EN: Matrix command-bot and the Android app now support the "📸 ZFS snapshot transfers" extension — parity with the Telegram bot. Previously the `snapshot_transfer_monitor` extension parsed STARTED/SUCCESS/SKIPPED/ERROR/BUSY emails and stored them in the `snapshot_transfers` table, but the data was only viewable through the Telegram menu "📸 Передачи снэпшотов" — the Matrix bot skipped it in `!extensions` ("nothing to show via command") and the Android app had neither a tile nor a dialog. The backend extends `/v1/control/actions` with two new actions: `snapshot_transfer_menu` (per-host summary + the latest 8 parsed emails + per-host buttons) and `snapshot_transfer_host_<host>` (latest 15 entries for a single host), reading from `SNAPSHOT_TRANSFER_HOSTS` and the `snapshot_transfers` table and gated by the extension's enabled flag. The Matrix bot gains a `!snapshots` command and a `📸` reaction button in the `!extensions` submenu, both producing the same report through `_handle_ext_snapshot_transfer`. The Android client renders a "📸 снэпшоты" tile with an `ok/total` ratio (green when `🔴 0`, red otherwise) alongside the other extension `OpsMetricTile`s; tapping opens an `AlertDialog` with a title, a "🔄 Обновить" button and the server's response text, with host buttons below that route to `snapshot_transfer_host_<host>` for the 15-row detail view.

### Changed
- RU: SemVer patch-бамп до `8.62.42`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.42`, `ANDROID_VERSION_CODE=804`).
- EN: SemVer patch bump to `8.62.42`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.42`, `ANDROID_VERSION_CODE=804`).

## [8.62.41] - 2026-05-21

### Changed
- RU: Android-приложение: плашка «🧩 Расширения» в настройках — счётчики «Всего · N / Включено · N / Выключено · N» в сводной карточке теперь сами являются кнопками-фильтрами (`Surface(onClick=…)`), а отдельная строка из трёх `FilterChip` под полем поиска убрана. Раньше плашки в `Surface(primaryContainer)` показывали статистику пассивно, а тапать для смены фильтра приходилось по чипам ниже формы поиска — это удваивало визуальные элементы (одна и та же тройка «Все/Включено/Выключено» сверху и снизу) и заставляло глаз скакать вверх-вниз. Теперь активный фильтр подсвечивается `secondaryContainer` с рамкой `BorderStroke(2.dp, secondary)` и приподнятой `tonalElevation = 3.dp` прямо на счётчике, который ты и так читаешь, а раздел между поиском и списком стал короче на одну строку.
- EN: Android app: the "🧩 Extensions" tile in settings — the "Всего · N / Включено · N / Выключено · N" counters in the summary card are now themselves filter buttons (`Surface(onClick=…)`), and the separate row of three `FilterChip`s below the search field is removed. Previously the chips in `Surface(primaryContainer)` showed stats passively while filter switching lived in a second row of chips under the search box, duplicating the same "All / Enabled / Disabled" trio top and bottom and forcing the eye to jump up and down. Now the active filter is highlighted with `secondaryContainer`, a `BorderStroke(2.dp, secondary)` outline and raised `tonalElevation = 3.dp` directly on the counter you already read, and the gap between search and list is one row shorter.
- RU: SemVer patch-бамп до `8.62.41`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.41`, `ANDROID_VERSION_CODE=803`).
- EN: SemVer patch bump to `8.62.41`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.41`, `ANDROID_VERSION_CODE=803`).

## [8.62.40] - 2026-05-21

### Changed
- RU: Android-приложение: плашка «🧩 Расширения» в настройках полностью переработана для удобства управления. Раньше раздел состоял из вводного текста «Включай/выключай расширения…», текста с подсказкой, пары кнопок «Включить все»/«Отключить все» отдельной строкой и плоского списка `ElevatedCard`-ов, в каждом из которых лежал полноширинный `Button` («Выключить»/«Включить») плюс строка «Статус: Включено/Отключено» — на 10+ расширениях экран растягивался и листать его, чтобы найти нужное, было неудобно. Теперь раздел начинается со сводной карточки `Surface(primaryContainer)` с тремя `StatChip`-ами «Всего · N», «Включено · N» (`tertiaryContainer`) и «Выключено · N» (`surfaceVariant`), под ними — две кнопки `Включить все` / `Отключить все` (disabled, когда массовая операция бессмысленна, например «Включить все» при `disabled == 0`). Дальше идёт поле `OutlinedTextField` с иконкой поиска для фильтрации по имени/описанию (с кнопкой-крестиком для очистки) и три `FilterChip` «Все · N / Включено · N / Выключено · N», которые сохраняются через `rememberSaveable` и переживают повороты экрана. Каждое расширение теперь рендерится компактной строкой `ElevatedCard`: заголовок + описание + статус-лейбл «включено»/«выключено» слева в одну колонку, а справа — `Switch`, который переключает расширение одним тапом (вместо полноширинной кнопки). Цвет карточки кодирует состояние (`tertiaryContainer` для включённых, `surfaceVariant` для выключенных), чтобы по списку взглядом было видно, что активно. Если поиск/фильтр ничего не вернул, показывается пояснительный `Surface(surfaceVariant)` «Ничего не найдено по текущему фильтру» вместо пустоты.
- EN: Android app: the "🧩 Extensions" tile in settings is fully redesigned for easier management. Previously the section consisted of an intro line "Включай/выключай расширения…", a hint paragraph, a separate row of "Включить все"/"Отключить все" buttons, and a flat list of `ElevatedCard`s where each card hosted a full-width `Button` ("Выключить"/"Включить") plus a "Статус: Включено/Отключено" line — with 10+ extensions the screen stretched and scrolling to find one was awkward. The section now opens with a summary card `Surface(primaryContainer)` carrying three `StatChip`s "Всего · N", "Включено · N" (`tertiaryContainer`) and "Выключено · N" (`surfaceVariant`); right below sit two buttons "Включить все" / "Отключить все" that auto-disable when the bulk action would be a no-op (e.g. "Включить все" while `disabled == 0`). Below that, an `OutlinedTextField` with a search icon filters by name/description (with a clear-X trailing icon) and three `FilterChip`s "Все · N / Включено · N / Выключено · N" persist via `rememberSaveable` across rotations. Each extension is now a compact `ElevatedCard` row: title + description + a "включено"/"выключено" status label stacked on the left, and a `Switch` on the right that toggles the extension in a single tap (replacing the full-width button). Card color encodes state (`tertiaryContainer` for enabled, `surfaceVariant` for disabled) so the list scans at a glance. When search/filter returns nothing, an explanatory `Surface(surfaceVariant)` "Ничего не найдено по текущему фильтру" replaces the empty space.
- RU: SemVer patch-бамп до `8.62.40`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.40`, `ANDROID_VERSION_CODE=802`).
- EN: SemVer patch bump to `8.62.40`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.40`, `ANDROID_VERSION_CODE=802`).

## [8.62.39] - 2026-05-21

### Changed
- RU: Android-приложение: плашка «🔐 Аутентификация» в настройках полностью переработана для удобства управления учётками. Раньше под одной кнопкой «🖥 Windows аутентификация» жили три отдельных тоггла («👥 Просмотр всех учетных записей», «📊 Учетные данные по типам», «⚙️ Управление типами серверов»), показывавших фактически одни и те же данные в разных форматах, а форма добавления учётки и плоский список форм «создать тип / переименовать / объединить / удалить» с четырьмя `OutlinedTextField`-ами без подсказок были навалены в одну колонку без визуальных границ. Теперь раздел состоит из summary-карточки (`Surface(primaryContainer)`) с чипами «SSH», «Windows-записей», «Типов»; раскрывающейся `ElevatedCard` SSH-доступа (логин + путь к ключу + «Сохранить SSH»); и раскрывающейся `ElevatedCard` Windows с двумя вкладками `FilterChip` — «👥 Записи» и «📂 Типы». На вкладке «Записи» фильтр-чипы по типам (включая «все»), компактные `Surface(surfaceVariant)`-карточки `username · тип · приоритет` с иконкой удаления (через подтверждающий `AlertDialog`, чтобы исключить случайные нажатия), и отдельная раскрывашка «➕ Добавить учётку» с быстрым выбором существующего типа через чипы. На вкладке «Типы» — карточки с `total/active` и инлайновыми действиями «Переименовать» (с предзаполнением старого имени) и «Удалить» (открывает диалог с выбором целевого типа из существующих чипами), плюс раскрывашки «Создать тип» и «🔀 Объединить типы» с выбором source/target через чипы. Кнопки сохранения теперь disabled до заполнения обязательных полей, чтобы убрать бессмысленные клики.
- EN: Android app: the "🔐 Authentication" tile in settings is completely redesigned for easier account management. Previously a single "🖥 Windows authentication" button hid three overlapping toggles ("👥 Просмотр всех учетных записей", "📊 Учетные данные по типам", "⚙️ Управление типами серверов") that showed essentially the same data in different formats, while the "add account" form and a flat stack of "create / rename / merge / delete type" forms with four unnamed `OutlinedTextField`s were piled into one column with no visual separation. The section now has a summary card (`Surface(primaryContainer)`) with chips "SSH", "Windows-записей", "Типов"; a collapsible `ElevatedCard` for SSH (username + key path + "Сохранить SSH"); and a collapsible `ElevatedCard` for Windows with two `FilterChip` tabs — "👥 Records" and "📂 Types". The Records tab has type filter chips (including "все"), compact `Surface(surfaceVariant)` cards "username · type · priority" with a delete icon (gated by a confirmation `AlertDialog` so accidental taps cannot wipe accounts) and a separate "➕ Add account" expander with quick selection of existing types via chips. The Types tab shows per-type cards with `total/active` and inline actions "Rename" (pre-fills the old name) and "Delete" (opens a dialog with chip-based target type selection), plus collapsible "Create type" and "🔀 Merge types" sections with source/target chip selection. Save buttons are now disabled until required fields are filled, eliminating meaningless taps.
- RU: SemVer patch-бамп до `8.62.39`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.39`, `ANDROID_VERSION_CODE=801`).
- EN: SemVer patch bump to `8.62.39`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.39`, `ANDROID_VERSION_CODE=801`).

## [8.62.38] - 2026-05-21

### Added
- RU: Android-приложение: в экране настроек, на плашке «🔌 BFF» появилась кнопка «Проверить связь с BFF». Раньше единственный способ убедиться, что сохранённые `Base URL API` и `Bearer токен` рабочие — это закрыть диалог настроек и нажать «Обновить» на главном экране; при ошибке причина (неверный URL, протухший токен, проблема с TLS) терялась в общем `summaryText`. Теперь кнопка отдельной строкой во всю ширину диалога дёргает `GET /v1/control/status` через текущий `currentApi()` и показывает результат в `ElevatedCard` под собой: зелёный `tertiaryContainer` с текстом «Связь с BFF установлена (monitoring=active)» при успехе, красный `errorContainer` с причиной ошибки (`HTTP 401: Unauthorized`, `timeout`, `Ошибка сети` и т.п.) при неудаче. Пока запрос в работе — кнопка disabled, со спиннером и подписью «Проверяю связь…», чтобы исключить повторные тапы.
- EN: Android app: in the settings screen, the "🔌 BFF" tile now has a "Проверить связь с BFF" button. Previously the only way to make sure the saved `Base URL API` and `Bearer токен` actually work was to close the settings dialog and tap "Refresh" on the main screen; on failure the reason (wrong URL, expired token, TLS issue) was lost in the general `summaryText`. The button now sits on its own full-width row inside the dialog, calls `GET /v1/control/status` through the current `currentApi()` and renders the result in an `ElevatedCard` below it: a green `tertiaryContainer` saying "Связь с BFF установлена (monitoring=active)" on success, a red `errorContainer` carrying the failure reason (`HTTP 401: Unauthorized`, `timeout`, `Ошибка сети`, etc.) on failure. While the request is in flight the button is disabled and shows an inline spinner with "Проверяю связь…" to prevent double-taps.

### Changed
- RU: SemVer patch-бамп до `8.62.38`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.38`, `ANDROID_VERSION_CODE=800`).
- EN: SemVer patch bump to `8.62.38`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.38`, `ANDROID_VERSION_CODE=800`).

## [8.62.37] - 2026-05-21

### Fixed
- RU: Android-приложение: кнопка «Проверить связь с сервером бота» в плашках «🤖 Бот Telegram» и «🤖 Бот Matrix» больше не выглядит «нерабочей». Раньше кнопка стояла в одной `Row` с кнопкой «Сохранить» внутри узкого AlertDialog с настройками — длинная подпись прижимала её к краю и попасть пальцем было трудно, а ответ сервера выводился крошечным безымянным `Text(state.message)` под кнопками, который легко не заметить. Теперь кнопка занимает отдельную строку во всю ширину диалога, во время запроса показывает спиннер и подпись «Проверяю связь…» (плюс кнопка disabled, чтобы исключить повторные тапы), а результат рендерится в `ElevatedCard` под кнопкой: зелёный фон (`tertiaryContainer`) и текст от сервера в случае успеха («Связь с Telegram установлена (бот @username)» / «Связь с Matrix установлена (user_id=…)») и красный фон (`errorContainer`) с причиной ошибки (`telegram_bot_token не задан в настройках`, `HTTP 401: Unauthorized`, `timeout: Telegram API не ответил за 10 c` и т.п.).
- EN: Android app: the "Проверить связь с сервером бота" button in the "🤖 Бот Telegram" and "🤖 Бот Matrix" tiles no longer looks broken. Previously the button lived in the same `Row` as the "Save" button inside a narrow settings `AlertDialog` — the long label squeezed it against the edge and made it hard to tap, and the server's reply was shown as a tiny unstyled `Text(state.message)` below the buttons that was easy to miss. The test button now occupies its own full-width row, displays an inline spinner with "Проверяю связь…" while the request is in flight (and stays disabled to prevent double-taps), and the result is rendered in an `ElevatedCard` below the button: a green `tertiaryContainer` card carrying the server's success text ("Связь с Telegram установлена (бот @username)" / "Связь с Matrix установлена (user_id=…)") on success, and a red `errorContainer` card carrying the failure reason on error (`telegram_bot_token не задан в настройках`, `HTTP 401: Unauthorized`, `timeout: Telegram API не ответил за 10 c`, etc.).

### Changed
- RU: SemVer patch-бамп до `8.62.37`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.37`, `ANDROID_VERSION_CODE=799`).
- EN: SemVer patch bump to `8.62.37`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.37`, `ANDROID_VERSION_CODE=799`).

## [8.62.36] - 2026-05-21

### Fixed
- RU: Android-приложение: кнопка «Проверить связь с сервером бота» в плашках «🤖 Бот Telegram» и «🤖 Бот Matrix» теперь действительно проверяет связь с самим botом, а не с мониторинговым backend'ом. Раньше нажатие отправляло `GET /v1/control/status`, который возвращал статус мониторинга — пользователь видел «Связь с сервером бота есть (active)» даже если токен Telegram-бота был протух, а Matrix homeserver/access_token были невалидны. Добавлены новые backend-эндпоинты `POST /v1/settings/bot/test` (под капотом дёргают Telegram API `getMe`) и `POST /v1/settings/bot/matrix/test` (дёргают `/_matrix/client/v3/account/whoami` с access_token). Android-клиент (`testBotServerConnection`, `testMatrixBotServerConnection`) теперь вызывает их и показывает реальный результат: успешный username бота / `user_id`, либо текст ошибки от Telegram/Matrix (`Unauthorized`, `Forbidden`, timeout и т.п.).
- EN: Android app: the "Проверить связь с сервером бота" button in both "🤖 Бот Telegram" and "🤖 Бот Matrix" tiles now actually verifies the bot itself, not the monitoring backend. Previously it sent `GET /v1/control/status`, which returned the monitoring status — so the user saw "Связь с сервером бота есть (active)" even when the Telegram token was expired or the Matrix homeserver/access_token were invalid. Two new backend endpoints have been added: `POST /v1/settings/bot/test` (calls Telegram API `getMe` under the hood) and `POST /v1/settings/bot/matrix/test` (calls `/_matrix/client/v3/account/whoami` with the saved access_token). The Android client (`testBotServerConnection`, `testMatrixBotServerConnection`) now invokes them and surfaces the real outcome: bot username / `user_id` on success, or the upstream Telegram/Matrix error text (`Unauthorized`, `Forbidden`, timeout, etc.).
- RU: Android-приложение: поле `matrix_homeserver` в плашке «🤖 Бот Matrix» больше не пустует при первом открытии настроек. Backend (`GET /v1/settings/bot/matrix` и ответ `PATCH /v1/settings/bot/matrix`) теперь подставляет значение по умолчанию из `config.settings.MATRIX_HOMESERVER` (`https://matrix.202020.ru`), когда `MATRIX_HOMESERVER` ещё не сохранён в БД через `settings_manager`. Раньше отдавалась пустая строка `""`, которая попадала в `state.matrixHomeserverInput` (т.к. `null`-fallback не срабатывал) и поле оставалось пустым.
- EN: Android app: the `matrix_homeserver` field on the "🤖 Бот Matrix" tile is no longer empty on first open. The backend (`GET /v1/settings/bot/matrix` and the response of `PATCH /v1/settings/bot/matrix`) now falls back to `config.settings.MATRIX_HOMESERVER` (`https://matrix.202020.ru`) when `MATRIX_HOMESERVER` has not yet been persisted in the DB via `settings_manager`. Previously an empty string `""` was returned, which then landed in `state.matrixHomeserverInput` (the `null`-fallback didn't trigger) leaving the field blank.

### Changed
- RU: SemVer patch-бамп до `8.62.36`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.36`, `ANDROID_VERSION_CODE=798`).
- EN: SemVer patch bump to `8.62.36`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.36`, `ANDROID_VERSION_CODE=798`).

## [8.62.35] - 2026-05-21

### Added
- RU: Android-приложение: на экране «Настройки» появилась плашка «🤖 Бот Matrix» с полями `matrix_homeserver`, `matrix_access_token` (маскированный, с переключателем видимости), `matrix_room_id`, кнопками «Сохранить matrix» и «Проверить связь с сервером бота» — параллельно плашке Telegram-бота. Сервер расширил API на эндпоинты `GET/PATCH /v1/settings/bot/matrix`, которые работают с настройками `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, `MATRIX_ROOM_ID` через тот же `settings_manager`, что и Telegram-бот.
- EN: Android app: the "Settings" screen now includes a "🤖 Бот Matrix" tile with `matrix_homeserver`, `matrix_access_token` (masked, with a visibility toggle), `matrix_room_id` fields plus "Сохранить matrix" and "Проверить связь с сервером бота" buttons — parallel to the Telegram bot tile. The backend gained `GET/PATCH /v1/settings/bot/matrix` endpoints that read/write `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, `MATRIX_ROOM_ID` via the same `settings_manager` used by the Telegram bot.

### Changed
- RU: Плашка настроек Telegram-бота переименована из «🤖 Бот» в «🤖 Бот Telegram», чтобы не путаться с новой плашкой «🤖 Бот Matrix». Заголовок диалога раздела обновлён аналогично.
- EN: The Telegram bot settings tile is renamed from "🤖 Бот" to "🤖 Бот Telegram" so it doesn't collide with the new "🤖 Бот Matrix" tile. The dialog header for the section was updated the same way.
- RU: SemVer patch-бамп до `8.62.35`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.35`, `ANDROID_VERSION_CODE=797`).
- EN: SemVer patch bump to `8.62.35`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.35`, `ANDROID_VERSION_CODE=797`).

### Fixed
- RU: Android-приложение: кнопка «Проверить связь с сервером бота» в плашке настроек Telegram-бота визуально «не работала» — запрос `GET /v1/control/status` уходил и возвращал `200`, но AlertDialog с настройками бота не показывал поле `state.message`, поэтому пользователь не видел ни «Связь с сервером бота есть (active)», ни ошибку. Сообщение `state.message` теперь выводится непосредственно в диалогах разделов «🤖 Бот Telegram» и «🤖 Бот Matrix».
- EN: Android app: the "Проверить связь с сервером бота" button in the Telegram bot settings tile appeared "not working" — the `GET /v1/control/status` request was firing and returning `200`, but the bot settings AlertDialog never rendered `state.message`, so the user saw neither the "Связь с сервером бота есть (active)" success nor any error. `state.message` is now rendered directly inside the "🤖 Бот Telegram" and "🤖 Бот Matrix" section dialogs.

## [8.62.34] - 2026-05-21

### Added
- RU: Android-приложение: на экране «Настройки → Мониторинг» теперь доступны все таймауты, которые редактируются из Telegram-бота по пути «Настройки → Мониторинг → ⏰ Таймауты серверов» — Windows 2025, доменные серверы, Admin серверы, стандартные Windows, Linux и Ping. Поля интервала проверки, таймаута API и максимального времени простоя получили человекочитаемые подписи. Сервер расширил `GET/PATCH /v1/settings/monitoring` ключами `windows_2025_timeout_sec`, `domain_servers_timeout_sec`, `admin_servers_timeout_sec`, `standard_windows_timeout_sec`, `linux_timeout_sec`, `ping_timeout_sec` поверх настроек `WINDOWS_2025_TIMEOUT`, `DOMAIN_SERVERS_TIMEOUT`, `ADMIN_SERVERS_TIMEOUT`, `STANDARD_WINDOWS_TIMEOUT`, `LINUX_TIMEOUT`, `PING_TIMEOUT` — те же ключи, что использует Telegram-бот, поэтому Android-клиент и бот теперь правят общие значения.
- EN: Android app: the "Настройки → Мониторинг" screen now exposes every timeout editable from the Telegram bot under "Settings → Monitoring → ⏰ Server timeouts" — Windows 2025, domain servers, Admin servers, standard Windows, Linux and Ping. The check interval, API timeout and max downtime fields now use human-readable labels. The backend extends `GET/PATCH /v1/settings/monitoring` with `windows_2025_timeout_sec`, `domain_servers_timeout_sec`, `admin_servers_timeout_sec`, `standard_windows_timeout_sec`, `linux_timeout_sec`, `ping_timeout_sec` on top of the `WINDOWS_2025_TIMEOUT`, `DOMAIN_SERVERS_TIMEOUT`, `ADMIN_SERVERS_TIMEOUT`, `STANDARD_WINDOWS_TIMEOUT`, `LINUX_TIMEOUT`, `PING_TIMEOUT` settings — the same keys the Telegram bot edits, so the Android client and the bot now mutate shared values.

### Changed
- RU: SemVer patch-бамп до `8.62.34`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.34`, `ANDROID_VERSION_CODE=796`).
- EN: SemVer patch bump to `8.62.34`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.34`, `ANDROID_VERSION_CODE=796`).

## [8.62.33] - 2026-05-20

### Fixed
- RU: Telegram-бот: восстановлен переход в подменю «Настройки → Мониторинг → ⏰ Таймауты серверов». Callback `server_timeouts` не подпадал ни под один из префиксов в `bot/handlers/callbacks.py:callback_router` (`settings_`, `set_`, `manage_`, `ssh_`, `windows_`, `server_type_`) и не входил в литеральный набор делегирования в `settings_callback_handler`, поэтому нажатие на кнопку только логировало `📥 CALLBACK DATA: server_timeouts` и ничего не происходило. Добавлен `server_timeouts` в литеральный список делегирования — меню снова открывается и показывает текущие таймауты с кнопками выбора параметра. Заодно убрана пустая `try/except`-обёртка, из-за которой `📥 CALLBACK DATA: …` логировалось дважды на один callback.
- EN: Telegram bot: restored navigation into «Настройки → Мониторинг → ⏰ Таймауты серверов». The `server_timeouts` callback didn't match any prefix in `bot/handlers/callbacks.py:callback_router` (`settings_`, `set_`, `manage_`, `ssh_`, `windows_`, `server_type_`) and wasn't listed in the literal delegation set for `settings_callback_handler`, so tapping the button only logged `📥 CALLBACK DATA: server_timeouts` and the submenu never opened. Added `server_timeouts` to the literal delegation set — the menu opens again and renders the current timeouts together with parameter-selection buttons. The empty `try/except` scaffold that caused `📥 CALLBACK DATA: …` to be logged twice per callback was also removed.

### Changed
- RU: SemVer patch-бамп до `8.62.33`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.33`, `ANDROID_VERSION_CODE=795`).
- EN: SemVer patch bump to `8.62.33`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.33`, `ANDROID_VERSION_CODE=795`).

## [8.62.32] - 2026-05-20

### Fixed
- RU: Telegram-бот: меню «Настройки → Мониторинг → ⏰ Таймауты серверов» снова открывается корректно и показывает реально применяемые значения (ключи `WINDOWS_2025_TIMEOUT`, `DOMAIN_SERVERS_TIMEOUT`, `ADMIN_SERVERS_TIMEOUT`, `STANDARD_WINDOWS_TIMEOUT`, `LINUX_TIMEOUT`, `PING_TIMEOUT`) вместо устаревшего словаря `SERVER_TIMEOUTS`, который по умолчанию пуст и приводил к экрану «не настроены». Удалена дублирующая декларация `handle_setting_input`, перетиравшая актуальный обработчик с подсказками для таймаутов.
- EN: Telegram bot: the «Настройки → Мониторинг → ⏰ Таймауты серверов» menu opens reliably again and shows the timeouts actually in effect (`WINDOWS_2025_TIMEOUT`, `DOMAIN_SERVERS_TIMEOUT`, `ADMIN_SERVERS_TIMEOUT`, `STANDARD_WINDOWS_TIMEOUT`, `LINUX_TIMEOUT`, `PING_TIMEOUT`) instead of the stale `SERVER_TIMEOUTS` dict that defaulted to empty and rendered a "not configured" screen. The duplicate `handle_setting_input` definition that shadowed the timeout-aware one was removed.

### Added
- RU: Telegram-бот: при открытии полей ввода «Интервал проверки», «Макс. время простоя» и других известных параметров (тихий режим, ресурсы, таймауты, веб) подсказка теперь начинается строкой «📍 Текущее значение: …», чтобы было видно, от какого значения отталкиваться при правке.
- EN: Telegram bot: when opening input prompts for «Интервал проверки», «Макс. время простоя», and other known parameters (silent mode, resources, timeouts, web), the hint now starts with a "📍 Текущее значение: …" line so the user can see the value they are editing.
- RU: Matrix-бот: после запуска бот шлёт в основную комнату стартовое сообщение и навешивает под ним кнопку-эмодзи `📋`. Эту же кнопку бот вешает под утренним/сводным отчётом (через `lib.alerts._send_matrix_alert`, флаг `attach_menu_button=True`); тап по `📋` вызывает `!menu`, минуя ввод текста.
- EN: Matrix bot: on startup the bot posts a greeting into the default room and attaches a `📋` button-reaction. The same `📋` reaction is added under the morning/summary report (via `lib.alerts._send_matrix_alert`, flag `attach_menu_button=True`); tapping `📋` triggers `!menu` without typing.

### Changed
- RU: SemVer patch-бамп до `8.62.32`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.32`, `ANDROID_VERSION_CODE=794`).
- EN: SemVer patch bump to `8.62.32`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.32`, `ANDROID_VERSION_CODE=794`).

## [8.62.31] - 2026-05-20

### Added
- RU: Matrix-бот: в основное меню (`!menu`) добавлена точечная проверка доступности сервера через команду `!check <имя|ip>` — отрабатывает тот же бэкенд, что и Telegram-бот (`run_targeted_task` в режиме `availability`).
- EN: Matrix bot: the main menu (`!menu`) now lists a targeted availability check via `!check <name|ip>` — reusing the same backend (`run_targeted_task` in `availability` mode) as the Telegram bot.
- RU: Matrix-бот: в подменю расширений (`!extensions`) подключена точечная проверка ресурсов одного сервера через команду `!res <имя|ip>` — доступна только при включённом расширении `resource_monitor` и использует `run_targeted_task` в режиме `resources`.
- EN: Matrix bot: the extensions submenu (`!extensions`) wires up a targeted single-server resource check via `!res <name|ip>` — only available when the `resource_monitor` extension is enabled and calls `run_targeted_task` in `resources` mode.

### Changed
- RU: SemVer patch-бамп до `8.62.31`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.31`, `ANDROID_VERSION_CODE=793`).
- EN: SemVer patch bump to `8.62.31`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.31`, `ANDROID_VERSION_CODE=793`).

## [8.62.30] - 2026-05-20

### Changed
- RU: Android: в диалоге «🗃️ Бэкапы БД» поведение тапа по плашке базы данных разделено — короткий тап вызывает API `db_detail_<тип>__<имя>` и показывает список последних бэкапов БД (как в Telegram-боте) во вспомогательном диалоге, а длинный тап оставлен за карточкой действий (редактировать / вкл-выкл / удалить). Подсказка в шапке диалога переписана под новое поведение.
- EN: Android: in the "🗃️ Бэкапы БД" dialog the database-tile tap was split — a short tap calls `db_detail_<type>__<name>` and shows the database's latest backups list (mirroring the Telegram-bot view) in a sub-dialog; a long press keeps opening the actions card (edit / toggle / delete). The dialog's hint text was updated to match.
- RU: Android: плашка «остатки» (расширение `stock_load_monitor`) в оперативном центре больше не ведёт в настройки — короткий тап теперь открывает диалог «📦 Загрузка остатков 1С», который вызывает API `backup_stock_loads` и показывает текущую сводку по загрузке остатков (как в Telegram-боте).
- EN: Android: the "остатки" tile (the `stock_load_monitor` extension) in the operational center no longer jumps into settings — a short tap now opens the "📦 Загрузка остатков 1С" dialog that invokes the `backup_stock_loads` API and renders the current 1C stock-load summary (mirroring the Telegram-bot view).
- RU: SemVer patch-бамп до `8.62.30`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.30`, `ANDROID_VERSION_CODE=792`).
- EN: SemVer patch bump to `8.62.30`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.30`, `ANDROID_VERSION_CODE=792`).

## [8.62.29] - 2026-05-20

### Added
- RU: Android: в оперативном центре между заголовком и плашками появилась компактная сводка инцидентов — отдельные мини-плашки в красной палитре с меткой проблемного раздела и его текущим значением; секция показывается только когда есть актуальные инциденты (хотя бы одна загруженная плашка с `hasProblem=true`). Тап по мини-плашке открывает тот же экран деталей, что и основная плашка.
- EN: Android: the operational center now shows a compact incident summary between the header and the tile grid — small error-tinted chips listing each problematic section together with its current value; the strip is shown only when there are live incidents (at least one loaded tile with `hasProblem=true`). Tapping a chip opens the same details screen as the corresponding main tile.

### Changed
- RU: SemVer patch-бамп до `8.62.29`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.29`, `ANDROID_VERSION_CODE=791`).
- EN: SemVer patch bump to `8.62.29`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.29`, `ANDROID_VERSION_CODE=791`).

## [8.62.28] - 2026-05-20

### Changed
- RU: Android: на экране «🌅 Последний отчёт» убрана кнопка «Обновить» в правом верхнем углу — обновление отчёта запрашивается только pull-to-refresh (потянуть список вниз); подсказка пустого состояния обновлена. Сам action `send_morning_report` остаётся доступен через жест и из утреннего диалога.
- EN: Android: on the "🌅 Последний отчёт" screen the top-right "Обновить" button was removed — refreshing the report is now driven only by pull-to-refresh; the empty-state hint was reworded. The `send_morning_report` action stays available via the gesture and from the morning-report dialog.
- RU: Android: в диалоге «💾 Бэкапы Proxmox» поведение тапа по плашке хоста разделено — короткий тап вызывает API `backup_host_<host>` и показывает список последних бэкапов хоста (как в Telegram-боте) во вспомогательном диалоге без потери списка хостов в фоне; длинный тап оставлен за карточкой действий (редактировать / вкл-выкл / удалить). Подсказка в шапке диалога переписана под новое поведение.
- EN: Android: in the "💾 Бэкапы Proxmox" dialog the host-tile tap was split — a short tap calls `backup_host_<host>` and shows the host's latest backups list (mirroring the Telegram-bot view) in a sub-dialog without resetting the underlying host list; a long press keeps opening the actions card (edit / toggle / delete). The dialog's hint text was updated to match.
- RU: Android: плашка «Режим» в оперативном центре теперь показывает не только режим (авто/принуд.), но и текущее состояние — `🔇 тихо`, `🔊 громко`, `🔇 авто`, `🔊 авто`. Строка `Сейчас: …` из шапки оперативного центра убрана, чтобы не дублировать ту же информацию.
- EN: Android: the "Режим" tile in the operational center now displays not only the mode (auto/forced) but also the current effective state — `🔇 тихо`, `🔊 громко`, `🔇 авто`, `🔊 авто`. The `Сейчас: …` line in the operational-center header was removed to avoid duplicating the same information.
- RU: SemVer patch-бамп до `8.62.28`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.28`, `ANDROID_VERSION_CODE=790`).
- EN: SemVer patch bump to `8.62.28`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.28`, `ANDROID_VERSION_CODE=790`).

## [8.62.27] - 2026-05-20

### Fixed
- RU: Android: разделение расширений в API `zfs_menu` — экшен теперь возвращает только статусы исправности пулов ZFS из таблицы `zfs_pool_status` (расширение `zfs_monitor`), без блока «💽 Свободное место ZFS» (расширение `zfs_pool_free_space_monitor`). До фикса четыре ветки ответа `zfs_menu` (нет БД / нет таблицы / нет данных / есть данные) подклеивали к ответу `_build_zfs_free_space_section()`, и плашка «zfs статусы» в андроид-клиенте парсила строки свободного места (например, `• rpool: 50G из 100G (занято 50%, ONLINE)`) как пулы — сведения по исправности отображались неверно. Свободное место остаётся доступным через отдельный экшен `zfs_pool_free_space_menu` и свою плашку «zfs место». Передачи снэпшотов (расширение `snapshot_transfer_monitor`) в `zfs_menu` не участвовали и не путаются.
- EN: Android: API `zfs_menu` extension separation — the action now returns only ZFS pool health statuses from the `zfs_pool_status` table (the `zfs_monitor` extension), without the "💽 Свободное место ZFS" block (the `zfs_pool_free_space_monitor` extension). Before the fix, four `zfs_menu` branches (no DB / no table / no rows / has data) appended `_build_zfs_free_space_section()` to the response, and the "zfs статусы" tile in the Android client parsed free-space lines (e.g. `• rpool: 50G из 100G (занято 50%, ONLINE)`) as pools — health data was rendered incorrectly. Free space remains accessible through the dedicated `zfs_pool_free_space_menu` action and its "zfs место" tile. Snapshot transfers (the `snapshot_transfer_monitor` extension) never participated in `zfs_menu` and are unaffected.

### Changed
- RU: SemVer patch-бамп до `8.62.27`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.27`, `ANDROID_VERSION_CODE=789`).
- EN: SemVer patch bump to `8.62.27`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.27`, `ANDROID_VERSION_CODE=789`).

## [8.62.26] - 2026-05-20

### Fixed
- RU: Android: плашка «zfs статусы» в оперативном центре корректно подтягивает сведения о здоровье пулов ZFS. Парсинг в `buildBackupTileSummary` (`MainViewModel.kt`) теперь ограничен секцией «📊 ZFS статусы» — строки из блока «💽 Свободное место ZFS» (например, `• rpool: 50G из 100G (занято 50%, ONLINE)`) больше не учитываются как пулы, и регулярка состояния ужесточена до `[A-Z_]+`, чтобы не цеплять размеры с цифрами/единицами. Если у сервера ещё нет данных по пулам, плашка показывает `0/0` без флага проблемы вместо пустой.
- EN: Android: the "zfs статусы" tile in the operational center now correctly picks up ZFS pool health info. The parsing in `buildBackupTileSummary` (`MainViewModel.kt`) is scoped to the "📊 ZFS статусы" section — lines from the "💽 Свободное место ZFS" block (e.g. `• rpool: 50G из 100G (занято 50%, ONLINE)`) are no longer counted as pools, and the state regex was tightened to `[A-Z_]+` so size strings with digits/units stop matching. When the server has no pool data yet, the tile shows `0/0` with no problem flag instead of staying blank.
- RU: Android: при запросе утреннего отчёта (кнопка «Обновить» на экране отчёта или действие `send_morning_report`) текст ответа больше не дублируется на главном экране оперативного центра — он отображается только на экране «🌅 Последний отчёт» и в диалоге утреннего отчёта. В `MainActivity.kt` удалён блок `if (state.messageSource == "morning_report") { Text(state.message) }` из колонки секций главного экрана.
- EN: Android: requesting the morning report (the "Обновить" button on the report screen or the `send_morning_report` action) no longer duplicates the response text on the operational-center main screen — the report is shown only on the "🌅 Последний отчёт" screen and inside the morning-report dialog. The `if (state.messageSource == "morning_report") { Text(state.message) }` block was removed from the main-screen sections column in `MainActivity.kt`.

### Changed
- RU: SemVer patch-бамп до `8.62.26`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.26`, `ANDROID_VERSION_CODE=788`).
- EN: SemVer patch bump to `8.62.26`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.26`, `ANDROID_VERSION_CODE=788`).

## [8.62.25] - 2026-05-20

### Changed
- RU: Android: текстовые подсказки о свайпах удалены со всех экранов; направление свайпа теперь обозначается визуальным индикатором страниц (три «пилюли» внизу экрана, активная подсвечена и вытянута), по тапу на индикатор выполняется переход на выбранный экран. Подсказки в оперцентре, отчёте и настройках больше не дублируются текстом.
- EN: Android: textual swipe hints were removed from every screen; the swipe direction is now conveyed by a visual page indicator (three pill-shaped marks at the bottom, the active one highlighted and elongated), tapping a mark jumps to the selected screen. The duplicate text hints in the operational center, report and settings screens are gone.
- RU: Android: вместо отдельной строки «Сертификат: …» в заголовке оперцентра и кнопки «🔐 Проверить только сертификат (врем.)» теперь отдельная плашка «🔐 Сертификат BFF» в оперативном центре: показывает текст статуса, при ошибке окрашивается в errorContainer и показывает текст предупреждения; тап по плашке запускает ту же диагностику TLS, что и раньше. Дублирующая «🔐 Сертификат BFF» в красной плашке (item внутри LazyColumn) удалена. Аналогичная плашка заменила состояние/кнопку и в не-компактной (классической) разметке оперцентра.
- EN: Android: the standalone "Сертификат: …" line in the operational-center header and the "🔐 Проверить только сертификат (врем.)" button were replaced by a single "🔐 Сертификат BFF" tile in the operational center: it shows the status text, switches to `errorContainer` and shows the warning text when a problem is detected, and tapping the tile runs the same TLS diagnostics as before. The duplicate red "🔐 Сертификат BFF" item-card in the LazyColumn was removed. The same tile replaces the cert status line and button in the non-compact (classic) operational-center layout as well.
- RU: SemVer patch-бамп до `8.62.25`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.25`, `ANDROID_VERSION_CODE=787`).
- EN: SemVer patch bump to `8.62.25`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.25`, `ANDROID_VERSION_CODE=787`).

## [8.62.24] - 2026-05-19

### Changed
- RU: Android: в горизонтальном пейджере поменяны местами экраны «Отчёт» и «Настройки» — теперь из оперативного центра свайп вправо открывает 🌅 отчёт, свайп влево — ⚙️ настройки (раньше было наоборот). Из оперативного центра убраны кнопки «🌅 Отчёт» и «⚙️ Настройки» (переход между экранами только свайпом), вместо них добавлена визуальная подсказка о направлении свайпов.
- EN: Android: the "Report" and "Settings" pages were swapped in the horizontal pager — from the operational center a swipe right now opens the 🌅 report and a swipe left opens ⚙️ settings (previously the opposite). The "🌅 Report" and "⚙️ Settings" buttons were removed from the operational center (screen navigation is swipe-only) and replaced with a visual hint describing the swipe directions.
- RU: SemVer patch-бамп до `8.62.24`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.24`, `ANDROID_VERSION_CODE=786`).
- EN: SemVer patch bump to `8.62.24`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.24`, `ANDROID_VERSION_CODE=786`).

### Fixed
- RU: Android: подсказки о свайпах на экранах отчёта и настроек приведены в соответствие фактическому направлению жеста (свайп влево/вправо для возврата в оперативный центр), добавлены стрелки-эмодзи.
- EN: Android: the swipe hints on the report and settings screens now match the actual gesture direction (swipe left/right to return to the operational center), with emoji arrows added.

## [8.62.23] - 2026-05-19

### Fixed
- RU: `scripts/android_post_pull_build_run.ps1` падал на 3-й попытке установки с `NativeCommandError`: `adb start-server` пишет `* daemon not running; starting now` в stderr, а при `$ErrorActionPreference = "Stop"` Windows PowerShell 5.1 превращает stderr нативной команды в терминирующую ошибку (`2>$null` это не подавляет). Добавлена обёртка `Invoke-Adb` (локальный `ErrorActionPreference=Continue`, stderr через `2>&1` в текст, явная проверка кода возврата); все adb-вызовы в логике установки переведены на неё.
- RU: Истинная причина провала установки — не флак транспорта, а `Failure calling service package: Broken pipe` → `Can't find service: package`: на эмуляторе не поднят/упал package manager (`system_server`). Перезапуск adb это не лечит. Добавлена `Wait-ForPackageService`: перед каждой попыткой установки скрипт ждёт `sys.boot_completed=1` и доступности сервиса `package` (poll `cmd package list packages`, таймаут 180с). Если сервис так и не поднялся — внятная ошибка с инструкцией восстановить устройство (Cold Boot / Wipe Data / увеличить Internal Storage AVD).
- EN: `scripts/android_post_pull_build_run.ps1` died on the 3rd install attempt with `NativeCommandError`: `adb start-server` prints `* daemon not running; starting now` to stderr, and under `$ErrorActionPreference = "Stop"` Windows PowerShell 5.1 turns native-command stderr into a terminating error (`2>$null` does not suppress it). Added an `Invoke-Adb` wrapper (local `ErrorActionPreference=Continue`, stderr folded via `2>&1`, explicit exit-code check); all adb calls in the install path now go through it.
- EN: The real install failure is a device-side fault, not a transport flake: `Failure calling service package: Broken pipe` → `Can't find service: package` means the emulator's package manager (`system_server`) is not up/crashed; restarting adb cannot fix it. Added `Wait-ForPackageService`: before each install attempt the script waits for `sys.boot_completed=1` and a responsive `package` service (polls `cmd package list packages`, 180s timeout). If it never comes up, the script fails with a clear device-recovery message (Cold Boot / Wipe Data / enlarge AVD Internal Storage).

### Changed
- RU: SemVer patch-бамп до `8.62.23`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.23`, `ANDROID_VERSION_CODE=785`).
- EN: SemVer patch bump to `8.62.23`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.23`, `ANDROID_VERSION_CODE=785`).

## [8.62.22] - 2026-05-19

### Fixed
- RU: `scripts/android_post_pull_build_run.ps1` не парсился в Windows PowerShell 5.1 (`ParserError: UnexpectedToken`, «Отсутствует закрывающий знак "}"»): файл содержал не-ASCII символы (em-dash `—` в сообщении throw и `✅` в `Write-Host`), а PS 5.1 под русской локалью читает `.ps1` без BOM как Windows-1251 → мохибейк ломал разбор строк. Скрипт приведён к чистому ASCII (`—` → `-`, `✅` → `[OK]`), теперь парсится независимо от локали/кодировки. Логика установки/сборки/запуска не изменена.
- EN: `scripts/android_post_pull_build_run.ps1` failed to parse under Windows PowerShell 5.1 (`ParserError: UnexpectedToken`, missing closing `}`): the file contained non-ASCII characters (an em-dash `—` in a throw message and `✅` in `Write-Host`), and PS 5.1 under a Russian locale reads a BOM-less `.ps1` as Windows-1251, so the mojibake broke string parsing. The script is now pure ASCII (`—` → `-`, `✅` → `[OK]`) and parses regardless of locale/encoding. Install/build/run logic is unchanged.

### Changed
- RU: SemVer patch-бамп до `8.62.22`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.22`, `ANDROID_VERSION_CODE=784`).
- EN: SemVer patch bump to `8.62.22`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.22`, `ANDROID_VERSION_CODE=784`).

## [8.62.21] - 2026-05-19

### Fixed
- RU: Скрипт `scripts/android_post_pull_build_run.ps1` падал на шаге `[4/5] Install` с `com.android.ddmlib.InstallException: Failure calling service package: Broken pipe (32)` — флакающий обрыв ADB-транспорта при установке через Gradle-задачу `:app:install*Debug` (ddmlib). Сборка APK при этом проходит успешно. Шаг установки переделан: новая функция `Invoke-RobustInstall` сначала ставит APK напрямую через `adb -s <device> install -r -t` (platform-tools устойчивее ddmlib), при неуспехе откатывается на Gradle-задачу, и повторяет до 3 попыток с перезапуском adb-сервера (`Restart-AdbServer`: `kill-server`/`start-server`/`wait-for-device`) и экспоненциальной паузой между попытками. Логика сборки/запуска не изменена.
- EN: The `scripts/android_post_pull_build_run.ps1` script failed at the `[4/5] Install` step with `com.android.ddmlib.InstallException: Failure calling service package: Broken pipe (32)` — a flaky ADB transport drop while installing through the Gradle `:app:install*Debug` (ddmlib) task. The APK itself assembles fine. The install step was reworked: a new `Invoke-RobustInstall` function first installs the APK directly via `adb -s <device> install -r -t` (platform-tools is far more resilient than ddmlib), falls back to the Gradle task on failure, and retries up to 3 times with an adb-server restart (`Restart-AdbServer`: `kill-server`/`start-server`/`wait-for-device`) and exponential backoff between attempts. Build/run logic is unchanged.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.21`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.21`, `ANDROID_VERSION_CODE=783`).
- EN: Performed a SemVer patch bump to `8.62.21`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.21`, `ANDROID_VERSION_CODE=783`).

## [8.62.20] - 2026-05-19

### Fixed
- RU: Исправлена ошибка компиляции Android-клиента (`compileCompactOpsDebugKotlin`), возникшая после перехода на `HorizontalPager` (8.62.19). `screensPagerState`/`screensScope` использовались в обработчике плашки расширения (строка ~2309) раньше, чем объявлялись (~2384) — `val` объявления перенесены в начало `MonitoringApp`. Также `rememberPullRefreshState` для экрана отчёта вызывался с trailing-lambda, которая попадала в параметр `refreshingOffset: Dp` вместо `onRefresh` — колбэк передан позиционным аргументом.
- EN: Fixed an Android client compile error (`compileCompactOpsDebugKotlin`) introduced by the `HorizontalPager` rework (8.62.19). `screensPagerState`/`screensScope` were referenced in the extension-tile click handler (line ~2309) before their declaration (~2384) — the `val` declarations were moved to the top of `MonitoringApp`. Also `rememberPullRefreshState` for the report screen was called with a trailing lambda that bound to the `refreshingOffset: Dp` parameter instead of `onRefresh` — the callback is now passed as a positional argument.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.20`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.20`, `ANDROID_VERSION_CODE=782`).
- EN: Performed a SemVer patch bump to `8.62.20`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.20`, `ANDROID_VERSION_CODE=782`).

## [8.62.19] - 2026-05-19

### Changed
- RU: В Android-клиенте навигация между экранами переделана со «всплывающих окон» на горизонтальный пейджер (`HorizontalPager`): «⚡ Оперативный центр» — центральный экран, свайп влево перелистывает на экран последнего отчёта, свайп вправо — на экран настроек с плашками. Оперативный центр при перелистывании уходит в противоположную сторону (нативный эффект пейджера). Кнопки «🌅 Отчёт» и «⚙️ Настройки» теперь перелистывают на соответствующий экран, а не открывают модальное окно. По тапу на плашку настроек по-прежнему открывается окно-наложение с настройками раздела.
- RU: Экран отчёта показывает последний полученный отчёт без автоматического запроса нового; добавлены кнопка «Обновить» и pull-to-refresh (потянуть вниз) — оба запрашивают свежий отчёт (`send_morning_report`).
- EN: In the Android client screen navigation was reworked from pop-up dialogs to a horizontal pager (`HorizontalPager`): the "⚡ Operations Center" is the central screen, swiping left pages to the latest-report screen, swiping right to the tiled settings screen. The ops center slides off to the opposite side while paging (native pager effect). The "🌅 Отчёт" and "⚙️ Настройки" buttons now page to the matching screen instead of opening a modal. Tapping a settings tile still opens an overlay window with that section's settings.
- EN: The report screen shows the last received report without auto-requesting a new one; an "Обновить" button and pull-to-refresh were added — both request a fresh report (`send_morning_report`).
- RU: Выполнен SemVer patch-бамп до `8.62.19`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.19`, `ANDROID_VERSION_CODE=781`).
- EN: Performed a SemVer patch bump to `8.62.19`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.19`, `ANDROID_VERSION_CODE=781`).

## [8.62.18] - 2026-05-19

### Added
- RU: В Android-клиенте из «⚡ Оперативного центра» добавлена навигация свайпами: свайп влево открывает просмотр текущего последнего (утреннего) отчёта — то же, что кнопка «🌅 Отчёт»; свайп вправо открывает экран настроек. Экран настроек теперь показывает разделы в виде плашек (BFF, Мониторинг, Бот, Время, Аутентификация, Расширения); по тапу на плашку открывается окно-наложение с настройками соответствующего раздела. Прежний переключатель разделов через `FilterChip` заменён на плашки.
- EN: In the Android client the "⚡ Operations Center" gained swipe navigation: swiping left opens the current latest (morning) report — the same as the "🌅 Отчёт" button; swiping right opens the settings screen. The settings screen now lays out sections as tiles (BFF, Monitoring, Bot, Time, Auth, Extensions); tapping a tile opens an overlay window with that section's settings. The previous `FilterChip` section switcher was replaced by tiles.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.18`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.18`, `ANDROID_VERSION_CODE=780`).
- EN: Performed a SemVer patch bump to `8.62.18`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.18`, `ANDROID_VERSION_CODE=780`).

## [8.62.17] - 2026-05-19

### Fixed
- RU: При перезапуске сервиса в Telegram и Matrix приходило два отдельных уведомления «🟢 Мониторинг серверов запущен» — одно из `main.py` (этап стартового уведомления) и одно из потока мониторинга `core/monitor.py`. Теперь стартовое уведомление формируется и отправляется один раз методом `Monitor._send_startup_notification()`: версия сервера, версия Android-клиента, хост, версия Python и время запуска объединены с параметрами мониторинга (число серверов, интервалы проверок, время утреннего отчёта, состояние веб-интерфейса) в одно сообщение. Дублирующая отправка из `main.py` и неиспользуемая `build_startup_message()` удалены; уведомление по-прежнему подавляется при `--silent-start`.
- EN: On service restart Telegram and Matrix received two separate "🟢 Monitoring started" notifications — one from `main.py` (startup notification stage) and one from the `core/monitor.py` monitoring thread. The startup notification is now built and sent once by `Monitor._send_startup_notification()`: server version, Android client version, host, Python version and start time are merged with the monitoring parameters (server count, check intervals, morning report time, web interface state) into a single message. The duplicate send from `main.py` and the unused `build_startup_message()` were removed; the notification is still suppressed under `--silent-start`.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.17`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.17`, `ANDROID_VERSION_CODE=779`).
- EN: Performed a SemVer patch bump to `8.62.17`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.17`, `ANDROID_VERSION_CODE=779`).

## [8.62.16] - 2026-05-19

### Added
- RU: Диагностика ошибки «⚪ TLS: ошибка проверки (Ошибка сети)» в Android-клиенте. Добавлен временный серверный эндпоинт `POST /v1/mobile/diagnostics/tls` (+ `/api/...`), который принимает результат проверки TLS-сертификата Base URL от приложения и подробно логирует его в консоль сервера через `app.logger`: исход (`success`/`error`/`no_certificate`/`config_error`), host/port/base_url, согласованные protocol и cipher suite, subject/issuer/SAN/срок действия сертификата при успехе, а при ошибке — полную цепочку исключений (`класс: сообщение <- класс: сообщение …`) и обрезанный стектрейс, плюс версию приложения, модель устройства и subject токена. Это позволяет понять реальную причину сбоя удалённо, без доступа к logcat устройства.
- RU: В оперативный центр (под строкой «Сертификат: …») и в legacy-карточку «Статус» добавлена временная кнопка «🔐 Проверить только сертификат (врем.)». Она запускает только TLS-проверку Base URL (без полной синхронизации ~16 запросов), обновляет статус сертификата на экране и отправляет подробный диагностический отчёт в консоль сервера. Периодическая синхронизация настроек по-прежнему делает ту же проверку, но в консоль сервера не пишет (чтобы не засорять лог) — отчёт уходит только по нажатию кнопки.
- EN: Diagnostics for the Android client "⚪ TLS: ошибка проверки (Ошибка сети)" error. Added a temporary server endpoint `POST /v1/mobile/diagnostics/tls` (+ `/api/...`) that receives the Base URL TLS certificate check result from the app and logs it in detail to the server console via `app.logger`: outcome (`success`/`error`/`no_certificate`/`config_error`), host/port/base_url, negotiated protocol and cipher suite, certificate subject/issuer/SAN/validity on success, and on failure the full exception chain (`class: message <- class: message …`) plus a truncated stack trace, along with the app version, device model and token subject. This makes the real failure cause diagnosable remotely without access to the device logcat.
- EN: Added a temporary "🔐 Проверить только сертификат (врем.)" button to the operations center (below the "Сертификат: …" line) and to the legacy "Status" card. It runs only the Base URL TLS check (without the full ~16-request sync), refreshes the on-screen certificate status and sends a detailed diagnostic report to the server console. The periodic settings sync still performs the same check but no longer writes to the server console (to avoid log noise) — the report is only sent on button press.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.16`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.16`, `ANDROID_VERSION_CODE=778`).
- EN: Performed a SemVer patch bump to `8.62.16`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.16`, `ANDROID_VERSION_CODE=778`).

## [8.62.15] - 2026-05-19

### Fixed
- RU: В Android-клиенте проверка TLS-сертификата Base URL API («Сертификат: …» в оперативном центре / карточке «Статус») ложно показывала «⚪ TLS: ошибка проверки (Ошибка сети)», хотя боевой трафик приложения через этот же `https://api.202020.ru:8443/` работал. Причина — `fetchBffCertificateStatus()` создавал `SSLSocket` через `createSocket()` без аргументов и подключался вручную, из-за чего в TLS-хендшейке не отправлялось расширение SNI (`server_name`). Обратный прокси, который и выдаёт сертификат для `api.202020.ru:8443`, без SNI не понимал, какой виртуальный хост запрашивается, и рвал соединение — ошибка приходила без сообщения и сворачивалась в обобщённое «Ошибка сети». Боевой трафик не страдал, потому что OkHttp/Retrofit отправляют SNI автоматически. Теперь перед `startHandshake()` на сокете явно выставляется `SNIHostName(host)` через `sslParameters`, и проверка корректно получает сертификат прокси и его срок действия.
- EN: In the Android client the Base URL API TLS certificate check ("Сертификат: …" in the operations center / "Статус" card) falsely reported "⚪ TLS: ошибка проверки (Ошибка сети)", even though the app's production traffic over the same `https://api.202020.ru:8443/` worked. Cause — `fetchBffCertificateStatus()` created the `SSLSocket` via the no-arg `createSocket()` and connected it manually, so the TLS handshake sent no SNI (`server_name`) extension. The reverse proxy that issues the certificate for `api.202020.ru:8443` could not tell which virtual host was requested without SNI and reset the connection; the resulting error had no message and collapsed into the generic "Ошибка сети". Production traffic was unaffected because OkHttp/Retrofit set SNI automatically. The socket now explicitly sets `SNIHostName(host)` via `sslParameters` before `startHandshake()`, so the check correctly retrieves the proxy certificate and its expiry.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.15`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.15`, `ANDROID_VERSION_CODE=777`).
- EN: Performed a SemVer patch bump to `8.62.15`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.15`, `ANDROID_VERSION_CODE=777`).

## [8.62.14] - 2026-05-18

### Added
- RU: В Android-клиенте срок действия TLS-сертификата Base URL API BFF теперь виден в «⚡ Оперативном центре», а не только в legacy-карточке «Статус». В шапку оперативного центра добавлена строка «Сертификат: …» с текущим статусом (`🟢 OK, N дн.` / `🟠 истекает через N дн.` / `🔴 истёк` / `⚪ не проверен`); при приближении к истечению строка подсвечивается цветом ошибки. Когда до истечения остаётся ≤14 дней (`certificateExpiryWarningDays`) или сертификат уже просрочен, под плитками показывается заметная карточка-предупреждение «🔐 Сертификат BFF» с текстом предупреждения и датой истечения. Сама проверка (`fetchBffCertificateStatus()` — TLS-хендшейк к хосту/порту из Base URL, разбор `notAfter` X.509) уже выполнялась при синхронизации настроек, но её результат в компактном оперативном центре нигде не отображался.
- EN: In the Android client the TLS certificate expiry of the BFF API Base URL is now surfaced in the "⚡ Operations Center", not only in the legacy "Status" card. A "Сертификат: …" line was added to the ops-center header with the current status (`🟢 OK, N days` / `🟠 expires in N days` / `🔴 expired` / `⚪ not checked`); as expiry approaches the line turns the error colour. When ≤14 days remain (`certificateExpiryWarningDays`) or the certificate is already expired, a prominent "🔐 Сертификат BFF" warning card with the warning text and expiry date is shown below the tiles. The check itself (`fetchBffCertificateStatus()` — TLS handshake to the Base URL host/port, parsing the X.509 `notAfter`) already ran during settings sync, but its result was never displayed in the compact ops center.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.14`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.14`, `ANDROID_VERSION_CODE=776`).
- EN: Performed a SemVer patch bump to `8.62.14`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.14`, `ANDROID_VERSION_CODE=776`).

## [8.62.13] - 2026-05-18

### Changed
- RU: Ускорен запуск Android-клиента. При старте теперь запрашиваются только два минимальных параметра — список включённых расширений (определяет, какие плитки показывать) и текущий режим работы (плитка «Режим»). Раньше `loadInitialState()` вызывал монолитный `refreshSettingsFromServer()` с ~16 сетевыми вызовами (настройки + статусы всех бэкапов/zfs/доступности), из-за чего дашборд долго входил в рабочее состояние. Добавлен `loadStartupEssentials()` (только `getExtensionsSettings` + `getControlStatus`). Остальные данные плиток грузятся лениво по тапу через новый `loadTileData(tileId)` — каждой плитке сопоставлен свой минимальный набор запросов (proxmox/БД/почта/zfs/zfs место/остатки/поставщики/серверы). Настройки (интервалы/бот/время/доступы) подтягиваются один раз лениво при первом открытии экрана «Настройки» (`ensureSettingsLoaded()`), полная синхронизация по кнопке «Синхронизировать» снимает все оверлеи (`allDataLoaded`).
- EN: Sped up Android client startup. On launch only two minimal parameters are now requested — the list of enabled extensions (decides which tiles to render) and the current operating mode (the "Режим"/Mode tile). Previously `loadInitialState()` called the monolithic `refreshSettingsFromServer()` with ~16 network calls (settings + all backup/zfs/availability statuses), so the dashboard took long to become usable. Added `loadStartupEssentials()` (only `getExtensionsSettings` + `getControlStatus`). The remaining per-tile data is loaded lazily on tap via the new `loadTileData(tileId)` — each tile mapped to its own minimal request set (proxmox/DB/mail/zfs/zfs-space/stock/suppliers/servers). Settings (intervals/bot/time/auth) are fetched lazily once on first opening the Settings screen (`ensureSettingsLoaded()`); a full "Sync" clears all overlays (`allDataLoaded`).
- RU: На всех плитках данных при запуске (кроме «Режим») вместо значения отображается «?» с полупрозрачным символом обновления поверх всей плитки; тап по такой плитке запускает запрос именно её данных (без открытия диалога), пока идёт загрузка — крутится индикатор. После загрузки плитка работает как обычно.
- EN: On every data tile at startup (except "Режим"/Mode) a "?" is shown instead of the value, with a semi-transparent refresh symbol over the whole tile; tapping such a tile triggers a request for exactly its data (without opening the dialog), with a spinner while loading. After loading the tile behaves normally.
- RU: Выполнен SemVer patch-бамп до `8.62.13`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.13`, `ANDROID_VERSION_CODE=775`).
- EN: Performed a SemVer patch bump to `8.62.13`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.13`, `ANDROID_VERSION_CODE=775`).

## [8.62.12] - 2026-05-18

### Fixed
- RU: Синхронизация в Android-клиенте полностью не работала: сервер логировал `GET /v1/monitoring/availability unauthorized … reason=invalid` и отдавал `401`. Причина — приложение хранило только выданный сервером session-токен (`preferences.apiToken`), а исходный bootstrap-токен после обмена в `saveToken()` выбрасывался. Когда session-токен переставал быть валидным на сервере (передеплой/пересоздание таблицы `mobile_api_tokens`, ротация `MOBILE_AUTH_SECRET`, отзыв токена), клиент бесконечно слал мёртвый токен без какого-либо восстановления — лечилось только ручным повторным вводом токена. Теперь bootstrap-токен персистится отдельно (`AppPreferences.bootstrapToken`), а в OkHttp добавлен `Authenticator` (общий помощник `MobileTokenRefresher`): на `401` он автоматически переобменивает bootstrap-токен через `/v1/auth/token/reissue` на свежий session-токен, персистит его и повторяет исходный запрос. Покрыты и foreground-синхронизация (`currentApi()` с синком Compose-state), и фоновые воркеры (`ServerDownAlertWorker`, `MorningReportWorker`, теперь читают токен из prefs динамически). Гарды от зацикливания: один повтор на запрос (заголовок `X-Token-Retry` + счётчик `priorResponse`) и общий 10-секундный дедуп параллельных переобменов. Это же чинит и `reason=expired`. ВАЖНО для уже установленных копий: после обновления один раз пере-сохраните токен в Настройках, чтобы bootstrap-токен попал в новое хранилище и авто-восстановление включилось.
- EN: Android client sync was completely broken: the server logged `GET /v1/monitoring/availability unauthorized … reason=invalid` and returned `401`. Cause — the app stored only the server-issued session token (`preferences.apiToken`) and discarded the original bootstrap token after the exchange in `saveToken()`. Once the session token stopped validating server-side (redeploy / recreated `mobile_api_tokens` table, `MOBILE_AUTH_SECRET` rotation, token revocation), the client forever sent the dead token with no recovery — only a manual token re-entry fixed it. The bootstrap token is now persisted separately (`AppPreferences.bootstrapToken`), and an OkHttp `Authenticator` (shared `MobileTokenRefresher` helper) was added: on `401` it automatically re-exchanges the bootstrap token via `/v1/auth/token/reissue` for a fresh session token, persists it and retries the original request. Both foreground sync (`currentApi()`, syncing Compose state) and background workers (`ServerDownAlertWorker`, `MorningReportWorker`, now reading the token from prefs dynamically) are covered. Loop guards: one retry per request (`X-Token-Retry` header + `priorResponse` count) and a shared 10-second dedup of concurrent refreshes. This also fixes `reason=expired`. NOTE for existing installs: after updating, re-save the token once in Settings so the bootstrap token lands in the new storage and auto-recovery kicks in.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.12`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.12`, `ANDROID_VERSION_CODE=774`).
- EN: Performed a SemVer patch bump to `8.62.12`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.12`, `ANDROID_VERSION_CODE=774`).

## [8.62.11] - 2026-05-18

### Fixed
- RU: Android-клиент показывал «Версия проекта: 8.62.0» (и «Установленная версия» при пустом ответе сервера), хотя реальная сборка давно ушла вперёд. Причина — в `MainViewModel.kt` версия была зашита строкой `projectVersion = "8.62.0"` и не бампилась: быстрый grep-чек рассинхрона версий из `CLAUDE.md` сканировал `*.kts`, но не `*.kt`, поэтому константа оставалась незамеченной. Теперь `projectVersion` берётся из `BuildConfig.VERSION_NAME` (т.е. из `gradle.properties` → `ANDROID_VERSION_NAME`) с отрезанием flavor-суффикса (`-legacy`/`-compactops`) до чистого `X.Y.Z`, поэтому отображаемая версия больше не может отстать от канонической. В grep-чек `CLAUDE.md` добавлен `--include="*.kt"`, чтобы рассинхрон в Kotlin-исходниках ловился впредь.
- EN: The Android client showed "Project version: 8.62.0" (and "Installed version" when the server response was empty) while the actual build had moved on long ago. Cause — `MainViewModel.kt` hardcoded `projectVersion = "8.62.0"` and it was never bumped: the `CLAUDE.md` version-drift grep scanned `*.kts` but not `*.kt`, so the constant rotted unnoticed. `projectVersion` now derives from `BuildConfig.VERSION_NAME` (i.e. `gradle.properties` → `ANDROID_VERSION_NAME`), stripping the flavor suffix (`-legacy`/`-compactops`) down to a clean `X.Y.Z`, so the displayed version can no longer fall behind the canonical one. Added `--include="*.kt"` to the `CLAUDE.md` grep so Kotlin-source drift is caught going forward.
- RU: При нажатии «Синхронизировать» без сохранённого токена `refreshSettingsFromServer` корректно пропускался, но `refreshAvailability` всё равно отправлял `GET /v1/monitoring/availability` (и точечный `…/availability/<server>`) без заголовка `Authorization` — сервер логировал `GET /v1/monitoring/availability unauthorized … reason=missing` и отдавал `401`, а пользователь видел лишь невнятную сетевую ошибку. Добавлены ранние проверки пустого токена в `refreshData`, `refreshAvailability` и `refreshServerAvailability` (как уже было в `refreshSettingsFromServer`): неаутентифицированные запросы доступности больше не уходят на сервер, вместо этого показывается понятное сообщение «Не задан токен доступа. Укажите токен в Настройках и сохраните его.».
- EN: Tapping "Sync" without a saved token correctly skipped `refreshSettingsFromServer`, but `refreshAvailability` still sent `GET /v1/monitoring/availability` (and the per-server `…/availability/<server>`) with no `Authorization` header — the server logged `GET /v1/monitoring/availability unauthorized … reason=missing` and returned `401`, while the user only saw a vague network error. Added early blank-token guards to `refreshData`, `refreshAvailability` and `refreshServerAvailability` (mirroring `refreshSettingsFromServer`): unauthenticated availability requests no longer reach the server; instead a clear "No access token set. Enter the token in Settings and save it." message is shown.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.11`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.11`, `ANDROID_VERSION_CODE=773`).
- EN: Performed a SemVer patch bump to `8.62.11`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.11`, `ANDROID_VERSION_CODE=773`).

## [8.62.10] - 2026-05-18

### Fixed
- RU: Matrix command-bot, `!settings`: разделы паттернов появлялись только для «📊 бэкапы Proxmox» и «🗃️ бэкапы БД», а у «🧊 ZFS», «📸 передачи снэпшотов», «📬 бэкапы почтового сервера» и «📦 загрузка остатков 1С» паттернов не было видно вовсе. Причина — `!settings` показывал только legacy-JSON `settings.BACKUP_PATTERNS`, тогда как паттерны `zfs`/`snapshot_transfer`/… живут в таблице `backup_patterns` (ею управляют меню паттернов Telegram-бота, из неё же читает рантайм `modules.mail_monitor`). Теперь `lib/matrix_commands.py` строит ЭФФЕКТИВНЫЙ словарь паттернов: дефолты `config.settings.BACKUP_PATTERNS` ← legacy-JSON ← таблица `backup_patterns` (таблица авторитетна, как в рантайме), и раздувает его по расширениям. Для каждого расширения-владельца паттернов (`backup_monitor`, `database_backup_monitor`, `mail_backup_monitor`, `zfs_monitor`, `snapshot_transfer_monitor`, `stock_load_monitor`) гарантируется хотя бы один раздел: если паттернов ещё нет — показывается пустой раздел-плейсхолдер `BACKUP_PATTERNS.<раздел> = {}` с пометкой «(паттерны не заданы)», чтобы раздел был виден так же, как Proxmox/БД. `!settings get BACKUP_PATTERNS.<раздел>` тоже резолвится по эффективному словарю (раздел из таблицы/дефолтов виден, даже если его нет в legacy-JSON). «💽 свободное место ZFS» паттернов не имеет по архитектуре (SSH-проверка `df`, без разбора писем) — для него раздел осознанно не синтезируется.
- EN: Matrix command-bot, `!settings`: pattern sections only showed up for "📊 Proxmox backups" and "🗃️ DB backups"; "🧊 ZFS", "📸 snapshot transfers", "📬 mail server backups" and "📦 1C stock load" had no patterns visible at all. Cause — `!settings` rendered only the legacy `settings.BACKUP_PATTERNS` JSON, while `zfs`/`snapshot_transfer`/… patterns live in the `backup_patterns` table (managed by the Telegram bot's pattern menus and read by the `modules.mail_monitor` runtime). Now `lib/matrix_commands.py` builds an EFFECTIVE pattern dict: `config.settings.BACKUP_PATTERNS` defaults ← legacy JSON ← `backup_patterns` table (table authoritative, as at runtime) and expands it across extensions. Every pattern-owning extension (`backup_monitor`, `database_backup_monitor`, `mail_backup_monitor`, `zfs_monitor`, `snapshot_transfer_monitor`, `stock_load_monitor`) is guaranteed at least one section: when no patterns exist yet an empty placeholder `BACKUP_PATTERNS.<section> = {}` is shown ("(patterns not set)") so the section is visible just like Proxmox/DB. `!settings get BACKUP_PATTERNS.<section>` resolves against the effective dict too (a table/defaults section is visible even if absent from the legacy JSON). "💽 ZFS free space" has no patterns by design (SSH `df` check, no email parsing) — no section is synthesized for it.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.10`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.10`, `ANDROID_VERSION_CODE=772`).
- EN: Performed a SemVer patch bump to `8.62.10`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.10`, `ANDROID_VERSION_CODE=772`).

## [8.62.9] - 2026-05-18

### Fixed
- RU: Matrix command-bot, `!settings`: единый параметр `BACKUP_PATTERNS` целиком сваливался под одно расширение «📊 бэкапы Proxmox» как один большой `string`-блок, хотя его разделы верхнего уровня принадлежат РАЗНЫМ расширениям (как в Telegram-боте, где паттерны разнесены по меню каждого расширения). Теперь в `lib/matrix_commands.py` `BACKUP_PATTERNS` раздувается в виртуальные строки `BACKUP_PATTERNS.<раздел>` и каждая привязывается к своему расширению по карте разделов: `mail`→«📬 бэкапы почтового сервера», `database`→«🗃️ бэкапы БД», `zfs`→«🧊 ZFS», `snapshot_transfer`→«📸 передачи снэпшотов», `stock_load`→«📦 загрузка остатков 1С», `proxmox`/`proxmox_subject`/`hostname_extraction` и неизвестные разделы→«📊 бэкапы Proxmox». Добавлены секции расширений `mail_backup_monitor` и `stock_load_monitor` в `_EXTENSION_SETTINGS`. `!settings get BACKUP_PATTERNS.<раздел>` отдаёт конкретный раздел с владельцем и описанием (регистронезависимо); `!settings set BACKUP_PATTERNS.<раздел>` отклоняется с подсказкой (правится через меню паттернов расширений Telegram-бота). Невалидный/непустой-несловарный `BACKUP_PATTERNS` показывается как раньше одной строкой.
- EN: Matrix command-bot, `!settings`: the single `BACKUP_PATTERNS` setting was dumped wholesale under one extension "📊 Proxmox backups" as a big `string` blob, even though its top-level sections belong to DIFFERENT extensions (like in the Telegram bot, where patterns are split across each extension's menu). Now in `lib/matrix_commands.py` `BACKUP_PATTERNS` is expanded into virtual `BACKUP_PATTERNS.<section>` rows, each attached to its owning extension by a section map: `mail`→"📬 mail server backups", `database`→"🗃️ DB backups", `zfs`→"🧊 ZFS", `snapshot_transfer`→"📸 snapshot transfers", `stock_load`→"📦 1C stock load", `proxmox`/`proxmox_subject`/`hostname_extraction` and unknown sections→"📊 Proxmox backups". Added `mail_backup_monitor` and `stock_load_monitor` sections to `_EXTENSION_SETTINGS`. `!settings get BACKUP_PATTERNS.<section>` returns that section with its owner and description (case-insensitive); `!settings set BACKUP_PATTERNS.<section>` is rejected with a hint (edited via the Telegram bot's extension pattern menus). An invalid / non-dict `BACKUP_PATTERNS` is still shown as a single row as before.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.9`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.9`, `ANDROID_VERSION_CODE=771`).
- EN: Performed a SemVer patch bump to `8.62.9`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.9`, `ANDROID_VERSION_CODE=771`).

## [8.62.8] - 2026-05-18

### Added
- RU: Тихий перезапуск сервиса: CLI-ключ `--silent-start` и эквивалентная переменная окружения `MONITOR_SILENT_START` (truthy — `1/true/yes/on`). При их наличии стартовое уведомление «🟢 Мониторинг серверов запущен» не отправляется ни в Telegram, ни в Matrix (оба идут через `send_alert`), а лишь пишется в лог. Удобно для `systemctl restart server-monitor` без шума о перезапуске в чаты: добавьте `Environment=MONITOR_SILENT_START=1` (или флаг в `ExecStart`) в unit. Хелпер `lib.alerts.is_startup_muted()`; CLI-ключ пробрасывается в окружение, чтобы фоновые потоки `core.monitor`/`monitor_core` тоже его видели.
- EN: Quiet service restart: CLI flag `--silent-start` and the equivalent `MONITOR_SILENT_START` env var (truthy — `1/true/yes/on`). When set, the "🟢 Monitoring started" startup notification is sent neither to Telegram nor Matrix (both go through `send_alert`) and is only logged. Handy for `systemctl restart server-monitor` without restart noise in chats: add `Environment=MONITOR_SILENT_START=1` (or the flag in `ExecStart`) to the unit. Added `lib.alerts.is_startup_muted()`; the CLI flag is propagated into the environment so the `core.monitor`/`monitor_core` background threads see it too.

### Fixed
- RU: Стартовое сообщение мониторинга показывало жёстко зашитое `• Утренний отчет: 08:30` (статическая `config.settings.DATA_COLLECTION_TIME`), игнорируя реальное время из настроек. Теперь время берётся из `morning_report._get_collection_times()` (БД `DATA_COLLECTION_TIMES`/`DATA_COLLECTION_TIME` с фолбэком на дефолт), несколько слотов выводятся через запятую; при сбое — прежний фолбэк. Поправлено в `core/monitor.py` и `core/monitor_core.py`.
- EN: The monitoring startup message showed a hardcoded `• Morning report: 08:30` (static `config.settings.DATA_COLLECTION_TIME`), ignoring the actual configured time. The time now comes from `morning_report._get_collection_times()` (DB `DATA_COLLECTION_TIMES`/`DATA_COLLECTION_TIME`, falling back to the default); multiple slots are comma-joined; on failure the previous fallback is used. Fixed in `core/monitor.py` and `core/monitor_core.py`.
- RU: В `!settings` (Matrix command-bot) параметр `BACKUP_PATTERNS` сваливался в «🧩 прочее» как `BACKUP_PATTERNS [string] = {…}` без описания, хотя в Telegram-боте паттерны корректно разнесены по расширениям. Причина — у ключа в БД были категория `general` и пустое `description` (сохранялся из бота без них). `BACKUP_PATTERNS` добавлен в канонические категории (`backup`) — теперь привязывается к расширению «📊 бэкапы Proxmox»; добавлен идемпотентный бэкфилл `description` (новый `_CANONICAL_SETTING_DESCRIPTION`, перезаписывается только пустое/NULL-описание) — `_migrate_setting_categories` чинит уже существующие БД.
- EN: In `!settings` (Matrix command-bot) the `BACKUP_PATTERNS` setting fell into "🧩 other" as `BACKUP_PATTERNS [string] = {…}` with no description, even though the Telegram bot splits patterns across extensions correctly. Root cause — the DB row had category `general` and an empty `description` (saved from the bot without them). `BACKUP_PATTERNS` was added to the canonical categories (`backup`) so it now attaches to the "📊 Proxmox backups" extension; an idempotent `description` backfill was added (new `_CANONICAL_SETTING_DESCRIPTION`, overwrites only empty/NULL description) — `_migrate_setting_categories` repairs existing databases.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.8`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.8`, `ANDROID_VERSION_CODE=770`).
- EN: Performed a SemVer patch bump to `8.62.8`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.8`, `ANDROID_VERSION_CODE=770`).

## [8.62.7] - 2026-05-18

### Fixed
- RU: Параметры независимых расширений путались между собой в Matrix command-bot (`!settings`) и в Telegram-боте (меню паттернов): «бэкапы Proxmox», «бэкапы БД», «ZFS» (исправность массивов), «свободное место ZFS-пулов» и «передачи снэпшотов» сваливались в кучу. Корневая причина — `ConfigManager.set_setting()` с дефолтом `category='general'`: при сохранении из Telegram-бота (вызовы без явной категории) `INSERT OR REPLACE` затирал категорию параметра в `general`, поэтому привязка параметра к расширению по категории становилась недетерминированной (зависела от того, какой UI сохранил параметр последним). `set_setting()` теперь не затирает `category`/`description`, если они не переданы (берёт уже сохранённые значения; `general`/'' — только для нового ключа). Категории сидов приведены к независимым (`ZFS_SERVERS`→`zfs`, `ZFS_POOL_FREE_SPACE_HOSTS`→`zfs_pool_free_space`, `SNAPSHOT_TRANSFER_HOSTS`→`snapshot_transfer`), добавлена идемпотентная миграция категорий для уже существующих БД. В `lib/matrix_commands.py` каждое расширение получило свою категорию и явные ключи-владельцы, добавлена секция `database_backup_monitor` («🗃️ бэкапы БД»). В меню «Паттерны бэкапов БД» Telegram-бота фильтр `db` больше не захватывает категории `snapshot_transfer`/`stock_load` (и `mail`/`zfs`/`proxmox`) — паттерны независимых расширений больше не смешиваются.
- EN: Settings of independent extensions were getting mixed up in the Matrix command-bot (`!settings`) and in the Telegram bot (patterns menu): "Proxmox backups", "DB backups", "ZFS" (array health), "ZFS pool free space" and "snapshot transfers" were lumped together. Root cause — `ConfigManager.set_setting()` defaulted `category='general'`: when saved from the Telegram bot (calls without an explicit category), the `INSERT OR REPLACE` clobbered the setting's category to `general`, so category-based attribution of a setting to an extension became non-deterministic (it depended on which UI saved the setting last). `set_setting()` now no longer clobbers `category`/`description` when they are not passed (it keeps the already-stored values; `general`/'' only for a brand-new key). Seed categories were made independent (`ZFS_SERVERS`→`zfs`, `ZFS_POOL_FREE_SPACE_HOSTS`→`zfs_pool_free_space`, `SNAPSHOT_TRANSFER_HOSTS`→`snapshot_transfer`), and an idempotent category migration was added for existing databases. In `lib/matrix_commands.py` each extension now has its own category and explicit owner keys, and a `database_backup_monitor` section ("🗃️ DB backups") was added. In the Telegram bot's "DB backup patterns" menu the `db` filter no longer captures the `snapshot_transfer`/`stock_load` categories (nor `mail`/`zfs`/`proxmox`) — patterns of independent extensions are no longer mixed.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.7`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.7`, `ANDROID_VERSION_CODE=769`).
- EN: Performed a SemVer patch bump to `8.62.7`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.7`, `ANDROID_VERSION_CODE=769`).

## [8.62.6] - 2026-05-18

### Fixed
- RU: Matrix command-bot, `!settings`: команда падала с `'MatrixCommandBot' object has no attribute '_handle_settings'` (в `sync_forever`), потому что диспетчер `_handle_settings` и обработчик `_settings_set` были удалены при рефакторинге, а `_route_command` всё ещё вызывал `await self._handle_settings(...)`. Восстановлены `_handle_settings` (разбор `help/list/get/set`) и `_settings_set` (конвертация значения по `data_type`, проверка доступа `_check_setting_access`, сохранение через `config_manager.set_setting` + аудит). Теперь работают `!settings`, `!settings list [группа]`, `!settings get <KEY>`, `!settings set <KEY> <значение>`.
- EN: Matrix command-bot, `!settings`: the command crashed with `'MatrixCommandBot' object has no attribute '_handle_settings'` (in `sync_forever`) because the `_handle_settings` dispatcher and `_settings_set` handler were dropped during a refactor while `_route_command` still called `await self._handle_settings(...)`. Restored `_handle_settings` (parses `help/list/get/set`) and `_settings_set` (value conversion by `data_type`, `_check_setting_access` gate, persisted via `config_manager.set_setting` + audit). `!settings`, `!settings list [group]`, `!settings get <KEY>` and `!settings set <KEY> <value>` work again.
- RU: Matrix command-bot, главное `!menu`: в описаниях команд пропали emoji — строки шли как `• !status — …`, хотя под сообщением висят кнопки-реакции с emoji. `_control_menu_text` теперь строится из `MENU_BUTTONS` и нового словаря `_MENU_DESCRIPTIONS`, поэтому emoji в строке всегда совпадает с emoji соответствующей кнопки-реакции (`📡 !status — доступность всех серверов` и т.д.).
- EN: Matrix command-bot, main `!menu`: emojis were missing from command descriptions — lines rendered as `• !status — …` even though the message has emoji reaction buttons. `_control_menu_text` is now built from `MENU_BUTTONS` and the new `_MENU_DESCRIPTIONS` map, so the emoji in each line always matches the emoji of its reaction button (`📡 !status — доступность всех серверов`, etc.).
- RU: Matrix command-bot: `!start`, `!menu` и `!help` открывали одно и то же меню, хотя в тексте было два разных описания. Теперь `!start`/`!menu` отдают главное меню с кнопками-реакциями, а `!help` — отдельную краткую справку по командам (без кнопок-реакций).
- EN: Matrix command-bot: `!start`, `!menu` and `!help` all opened the same menu despite two distinct descriptions in the text. Now `!start`/`!menu` return the main menu with reaction buttons, while `!help` returns a separate brief command reference (no reaction buttons).

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.6`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.6`, `ANDROID_VERSION_CODE=768`).
- EN: Performed a SemVer patch bump to `8.62.6`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.6`, `ANDROID_VERSION_CODE=768`).

## [8.62.5] - 2026-05-17

### Added
- RU: В Matrix command-bot `!dbbackup` без аргумента теперь шлёт сводку бэкапов БД и навешивает кнопки-реакции с именами баз; нажатие кнопки (или команда `!dbbackup <имя_базы>`) отдаёт статистику бэкапов по конкретной базе: статус, число успешных/неудачных/всего и последние бэкапы за 168ч (время, статус, тип задачи, число ошибок). Список баз берётся из `get_database_monitor_snapshot` (конфиг + `backups.db`), как в Telegram-боте; лейблы кнопок делаются уникальными (Matrix агрегирует одинаковые реакции — при совпадении display_name добавляется тип/счётчик), кнопок не больше 40, посторонние emoji-реакции под сводкой игнорируются. `!dbbackup <имя_базы>` работает и без открытого меню (резолв по свежему снимку). В подменю `!extensions` добавлена подсказка про аргумент `!dbbackup <имя_базы>`.
- EN: In the Matrix command-bot, `!dbbackup` with no argument now sends the database backup summary and attaches reaction buttons labeled with database names; pressing a button (or the `!dbbackup <db>` command) returns per-database backup stats: status, success/failed/total counts and the last 168h backups (time, status, task type, error count). The database list comes from `get_database_monitor_snapshot` (config + `backups.db`), like the Telegram bot; button labels are made unique (Matrix aggregates identical reactions — on display_name collision a type/counter suffix is added), capped at 40 buttons, and stray emoji reactions under the summary are ignored. `!dbbackup <db>` also works without an open menu (resolved against a fresh snapshot). The `!extensions` submenu now hints at the `!dbbackup <db>` argument.
- RU: В главное `!menu` Matrix command-bot добавлено описание команды вызова меню расширений — `!extensions` (алиас `!ext`): кнопка `🧩` присутствовала, но строки-описания в тексте `!menu` не было.
- EN: Added the extensions-menu command description to the Matrix command-bot main `!menu` — `!extensions` (alias `!ext`): the `🧩` button existed, but the `!menu` text had no description line for it.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.5`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.5`, `ANDROID_VERSION_CODE=767`).
- EN: Performed a SemVer patch bump to `8.62.5`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.5`, `ANDROID_VERSION_CODE=767`).

## [8.62.4] - 2026-05-17

### Fixed
- RU: Matrix command-bot: `!stock` (расширение `stock_load_monitor`) теперь отдаёт детальную загрузку остатков 1С по источникам/поставщикам (как в Telegram-боте): `📦 Загрузка остатков 1С (за 24ч)` → `Всего поставщиков: N` → `<источник> (N)` → `✅/⚠️/❌ <поставщик> (<строки>)[ — <ошибка>] (<Xд Yч назад>)`, вместо краткой сводки `• Файлов: …, ✅ … успешно, ❔ … без статуса`. Причина: команда `!stock` зарегистрирована как расширение и маршрутизировалась в `_handle_ext_stock_load` (краткая сводка `get_stock_load_summary`), из-за чего детальный обработчик `_handle_stock` был недостижим. Теперь `_handle_ext_stock_load` делегирует в `_handle_stock` (формат и относительное время совпадают с Telegram); убрана мёртвая ветка `!stock` в `_route_command`.
- EN: Matrix command-bot: `!stock` (the `stock_load_monitor` extension) now returns the detailed 1C stock load grouped by source/supplier (like the Telegram bot): `📦 Загрузка остатков 1С (за 24ч)` → `Всего поставщиков: N` → `<source> (N)` → `✅/⚠️/❌ <supplier> (<rows>)[ — <error>] (<Xd Yh ago>)`, instead of the brief `• Файлов: …, ✅ … успешно, ❔ … без статуса` summary. Root cause: `!stock` is registered as an extension and was routed to `_handle_ext_stock_load` (brief `get_stock_load_summary`), leaving the detailed `_handle_stock` handler unreachable. `_handle_ext_stock_load` now delegates to `_handle_stock` (format and relative time match Telegram); the dead `!stock` branch in `_route_command` was removed.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.4`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.4`, `ANDROID_VERSION_CODE=766`).
- EN: Performed a SemVer patch bump to `8.62.4`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.4`, `ANDROID_VERSION_CODE=766`).

## [8.62.3] - 2026-05-17

### Fixed
- RU: Matrix command-bot: `!zfs` (расширение `zfs_monitor`) теперь отдаёт детальный список пулов по серверам (как в Telegram-боте): `🧊 Мониторинг ZFS` → `📊 Текущее состояние пулов` → `🖥 <сервер>` → `🟢/🔴 <пул>: <state> (<время>)`, вместо агрегированной сводки `Статусы ZFS (последние)`. Причина: команда `!zfs` зарегистрирована как расширение и маршрутизировалась в `_handle_ext_zfs` (сводка из `morning_report.get_zfs_summary_for_report()`), из-за чего детальный обработчик `_handle_zfs` был недостижим. Теперь `_handle_ext_zfs` делегирует в `_handle_zfs`; убрана мёртвая ветка `!zfs` в `_route_command`.
- EN: Matrix command-bot: `!zfs` (the `zfs_monitor` extension) now returns the detailed per-server pool list (like the Telegram bot): `🧊 Мониторинг ZFS` → `📊 Текущее состояние пулов` → `🖥 <server>` → `🟢/🔴 <pool>: <state> (<time>)`, instead of the aggregated `Статусы ZFS (последние)` summary. Root cause: `!zfs` is registered as an extension and was routed to `_handle_ext_zfs` (summary from `morning_report.get_zfs_summary_for_report()`), leaving the detailed `_handle_zfs` handler unreachable. `_handle_ext_zfs` now delegates to `_handle_zfs`; the dead `!zfs` branch in `_route_command` was removed.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.3`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.3`, `ANDROID_VERSION_CODE=765`).
- EN: Performed a SemVer patch bump to `8.62.3`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.3`, `ANDROID_VERSION_CODE=765`).

## [8.62.2] - 2026-05-17

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.2`; синхронизированы упоминания версии в заголовках исходников/доков, ссылках на prerelease APK и Android-метаданные (`ANDROID_VERSION_NAME=8.62.2`, `ANDROID_VERSION_CODE=764`).
- EN: Performed a SemVer patch bump to `8.62.2`; synchronized version mentions in source/doc headers, prerelease APK links and Android metadata (`ANDROID_VERSION_NAME=8.62.2`, `ANDROID_VERSION_CODE=764`).

## [8.62.1] - 2026-05-17

### Added
- RU: В Matrix command-bot `!backup` без аргумента теперь шлёт сводку Proxmox и навешивает кнопки-реакции с именами серверов; нажатие кнопки (или команда `!backup <имя_сервера>`) отдаёт детализацию последних бэкапов по конкретному хосту (статус, время, размер, ошибка). Список хостов берётся из `BackupMonitorBot.get_all_hosts()` (только включённые), кнопок не больше 40, посторонние emoji-реакции под сводкой игнорируются. В подменю `!extensions` добавлена подсказка про аргумент `!backup <имя_сервера>`.
- EN: In the Matrix command-bot, `!backup` with no argument now sends the Proxmox summary and attaches reaction buttons labeled with server names; pressing a button (or the `!backup <server>` command) returns the last backups detail for that host (status, time, size, error). The host list comes from `BackupMonitorBot.get_all_hosts()` (enabled only), capped at 40 buttons, and stray emoji reactions under the summary are ignored. The `!extensions` submenu now hints at the `!backup <server>` argument.

### Fixed
- RU: `!zfs` (расширение `zfs_monitor`) больше не выдаёт «не указан IP» для каждого сервера. Это почтовый монитор: статусы пулов берутся из таблицы `zfs_pool_status`, как в `!report` (`morning_report.get_zfs_summary_for_report()`), а `ZFS_SERVERS` хранит только имена без IP. Ранее команда ошибочно шла в SSH-сборщик `zfs_free_space_monitor.collect_zfs_free_space()`. SSH-сбор свободного места остаётся за `!zfsfree` (`ZFS_POOL_FREE_SPACE_HOSTS`).
- EN: `!zfs` (the `zfs_monitor` extension) no longer reports "IP not set" for every server. It is a mail-based monitor: pool statuses come from the `zfs_pool_status` table, like `!report` (`morning_report.get_zfs_summary_for_report()`), while `ZFS_SERVERS` only stores names without IPs. The command previously and incorrectly went through the SSH collector `zfs_free_space_monitor.collect_zfs_free_space()`. SSH-based free-space polling stays with `!zfsfree` (`ZFS_POOL_FREE_SPACE_HOSTS`).

### Changed
- RU: Выполнен SemVer patch-бамп до `8.62.1`; синхронизированы упоминания версии в заголовках исходников/доков и Android-метаданные (`ANDROID_VERSION_NAME=8.62.1`, `ANDROID_VERSION_CODE=763`).
- EN: Performed a SemVer patch bump to `8.62.1`; synchronized version mentions in source/doc headers and Android metadata (`ANDROID_VERSION_NAME=8.62.1`, `ANDROID_VERSION_CODE=763`).

## [8.62.0] - 2026-05-17

### Added
- RU: В Matrix command-bot добавлено подменю расширений: в главное `!menu` добавлена кнопка `🧩` и команда `!extensions` (алиас `!ext`). Подменю показывает команды и кнопки-реакции только для включённых расширений (`extension_manager.is_extension_enabled`): `!resources` (resource_monitor), `!backup` (backup_monitor), `!dbbackup` (database_backup_monitor), `!mailbackup` (mail_backup_monitor), `!stock` (stock_load_monitor), `!zfs` (zfs_monitor), `!zfsfree` (zfs_pool_free_space_monitor), `!supplier` (supplier_stock_files), `!web` (web_interface). Каждая команда переиспользует существующий headless-backend без Telegram-объектов; выключенное расширение возвращает понятное сообщение, реакция на стороннее меню игнорируется.
- EN: Added an extensions submenu to the Matrix command-bot: a `🧩` button and `!extensions` command (alias `!ext`) were added to the main `!menu`. The submenu shows commands and reaction buttons only for enabled extensions (`extension_manager.is_extension_enabled`): `!resources` (resource_monitor), `!backup` (backup_monitor), `!dbbackup` (database_backup_monitor), `!mailbackup` (mail_backup_monitor), `!stock` (stock_load_monitor), `!zfs` (zfs_monitor), `!zfsfree` (zfs_pool_free_space_monitor), `!supplier` (supplier_stock_files), `!web` (web_interface). Each command reuses the existing headless backend without Telegram objects; a disabled extension returns a clear message and stale reactions are ignored.

### Changed
- RU: `!resources` и `!res` теперь относятся к расширению `resource_monitor` и учитывают его включённость: при выключенном расширении команды недоступны. Кнопка `📊 !resources` убрана из главного `!menu` и перенесена в подменю `!extensions`. Выполнен SemVer minor-бамп до `8.62.0`; синхронизированы упоминания версии в заголовках исходников/доков и Android-метаданные (`ANDROID_VERSION_NAME=8.62.0`, `ANDROID_VERSION_CODE=762`).
- EN: `!resources` and `!res` now belong to the `resource_monitor` extension and respect its enabled state: the commands are unavailable when the extension is off. The `📊 !resources` button was removed from the main `!menu` and moved into the `!extensions` submenu. Performed a SemVer minor bump to `8.62.0`; synchronized version mentions in source/doc headers and Android metadata (`ANDROID_VERSION_NAME=8.62.0`, `ANDROID_VERSION_CODE=762`).

## [8.61.29] - 2026-05-15

### Added
- RU: Matrix command-bot доведён до паритета с Telegram по основным операциям: добавлены команды `!resources` (ресурсы всех серверов), `!servers`/`!list` (список серверов), `!check <имя|ip>` и `!res <имя|ip>` (точечные проверки доступности/ресурсов), `!pause`/`!resume` (управление мониторингом), `!silent`/`!loud`/`!auto` (управление тихим режимом), `!mode` (состояние управления) и `!about` (версия/сведения). Команды переиспользуют существующий backend (`core.task_router`, `lib.alerts`, `modules.morning_report`) без Telegram-объектов.
- EN: Brought the Matrix command-bot to parity with Telegram for core operations: added `!resources` (all-server resources), `!servers`/`!list` (server list), `!check <name|ip>` and `!res <name|ip>` (targeted availability/resource checks), `!pause`/`!resume` (monitoring control), `!silent`/`!loud`/`!auto` (silent-mode control), `!mode` (control state) and `!about` (version/info). Commands reuse the existing backend (`core.task_router`, `lib.alerts`, `modules.morning_report`) without Telegram objects.
- RU: Добавлены кнопки в чате через emoji-реакции: на сообщение `!menu` бот навешивает реакции, нажатие которых в Element / Element X / web-клиенте запускает соответствующую команду с теми же ACL и аудитом. Для старых сборок `matrix-nio` без `ReactionEvent` предусмотрен fallback через `UnknownEvent`.
- EN: Added in-chat buttons via emoji reactions: the bot attaches reactions to the `!menu` message, and pressing one in Element / Element X / the web client runs the mapped command with the same ACL and audit. A fallback via `UnknownEvent` covers older `matrix-nio` builds without `ReactionEvent`.
- RU: Добавлена поддержка E2EE в command-bot: логин по паролю со стабильным `device_id`, persistent crypto-store, авто-выгрузка/запрос ключей, обработка `MegolmEvent` с `request_room_key`, отправка зашифрованных ответов/реакций (`ignore_unverified_devices`), `sync_forever`. Без пары user/password бот работает в legacy-режиме (только токен, незашифрованные комнаты). Новые ключи: `MATRIX_BOT_USER_ID`, `MATRIX_BOT_PASSWORD`, `MATRIX_STORE_PATH`, `MATRIX_DEVICE_NAME` (с DB-override по образцу остальных `MATRIX_*`); crypto-store исключён из git.
- EN: Added E2EE support to the command-bot: password login with a stable `device_id`, a persistent crypto-store, automatic key upload/query, `MegolmEvent` handling with `request_room_key`, encrypted replies/reactions (`ignore_unverified_devices`), and `sync_forever`. Without a user/password pair the bot stays in legacy mode (token only, non-encrypted rooms). New keys: `MATRIX_BOT_USER_ID`, `MATRIX_BOT_PASSWORD`, `MATRIX_STORE_PATH`, `MATRIX_DEVICE_NAME` (with DB override like the other `MATRIX_*`); the crypto-store is git-ignored.

### Changed
- RU: Документация `docs/matrix_bot_management.md` обновлена: roadmap заменён на описание реализованных команд и кнопок-реакций. Выполнен SemVer patch-бамп до `8.61.29`; синхронизированы упоминания версии и Android-метаданные (`ANDROID_VERSION_NAME=8.61.29`, `ANDROID_VERSION_CODE=761`).
- EN: Updated `docs/matrix_bot_management.md`: the roadmap was replaced with the implemented commands and reaction-button reference. Performed a SemVer patch bump to `8.61.29`; synchronized version mentions and Android metadata (`ANDROID_VERSION_NAME=8.61.29`, `ANDROID_VERSION_CODE=761`).

## [8.61.28] - 2026-05-14

- RU: Исправлено зацикливание Matrix self-command на сообщениях меню: echo-сообщения бота с несколькими `!`-командами в одной строке (например «!start или !menu — ...») теперь отбрасываются и не запускают повторную обработку.
- EN: Fixed Matrix self-command looping on menu messages: bot echo messages that contain multiple `!` commands on one line (for example "!start or !menu — ...") are now discarded and no longer trigger recursive processing.
- RU: Выполнен SemVer patch-бамп до `8.61.28`; синхронизированы все актуальные упоминания версии проекта в исходниках и конфигурации, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.61.28` и `ANDROID_VERSION_CODE=760`.
- EN: Performed a SemVer patch bump to `8.61.28`; synchronized all active project version mentions across source/config files, and updated Android metadata to `ANDROID_VERSION_NAME=8.61.28` and `ANDROID_VERSION_CODE=760`.

## [8.61.24] - 2026-05-14

- RU: Выполнен SemVer patch-бамп до `8.61.24`; синхронизированы актуальные упоминания версии проекта и Android-метаданные (`ANDROID_VERSION_NAME=8.61.24`, `ANDROID_VERSION_CODE=756`).
- EN: Performed a SemVer patch bump to `8.61.24`; synchronized active project version mentions and Android metadata (`ANDROID_VERSION_NAME=8.61.24`, `ANDROID_VERSION_CODE=756`).

## [8.61.23] - 2026-05-14

### Fixed
- RU: Для Matrix command-bot добавлен диагностический callback на все `m.room.message`-события: теперь в логах видно события, которые не являются `RoomMessageText/RoomMessageNotice`, что помогает разбирать кейс «команды отправляются, но бот молчит».
- EN: Added a diagnostic callback for all Matrix `m.room.message` events in the command bot: logs now show non-`RoomMessageText/RoomMessageNotice` events to troubleshoot cases where commands are sent but the bot stays silent.

### Changed
- RU: Выполнен SemVer patch-бамп до `8.61.23`; синхронизированы актуальные упоминания версии проекта и Android-метаданные (`ANDROID_VERSION_NAME=8.61.23`, `ANDROID_VERSION_CODE=755`).
- EN: Performed a SemVer patch bump to `8.61.23`; synchronized active project version mentions and Android metadata (`ANDROID_VERSION_NAME=8.61.23`, `ANDROID_VERSION_CODE=755`).

## [8.61.22] - 2026-05-14
- RU: Исправлен зацикленный echo в Matrix command-bot: исходящие сообщения бота теперь не повторно маршрутизируются как self-command, если текст не начинается с явной команды `!`.
- EN: Fixed looped echo in Matrix command-bot: bot outbound messages are no longer re-routed as self-commands unless the text explicitly starts with a `!` command.
- RU: Выполнен SemVer patch-бамп до `8.61.22`; синхронизированы актуальные упоминания версии проекта и Android-метаданные (`ANDROID_VERSION_NAME=8.61.22`, `ANDROID_VERSION_CODE=754`).
- EN: Performed a SemVer patch bump to `8.61.22`; synchronized active project version mentions and Android metadata (`ANDROID_VERSION_NAME=8.61.22`, `ANDROID_VERSION_CODE=754`).

## [8.61.21] - 2026-05-14

- RU: Исправлен разбор Matrix-команд в сообщениях с префиксом/упоминанием: регулярное выражение для inline-команд (`!help`, `!status` и т.д.) теперь использует корректные escape-последовательности и реально находит команду в тексте, а не пропускает её.
- EN: Fixed Matrix command parsing for prefixed/mention messages: the inline command regex (`!help`, `!status`, etc.) now uses correct escape sequences and actually matches commands in message text instead of skipping them.
- RU: Добавлена нормализация символа `！` → `!` при извлечении команды из Matrix-сообщения, чтобы команды с «широким» восклицательным знаком тоже отрабатывали.
- EN: Added normalization `！` → `!` during Matrix command extraction so commands sent with the fullwidth exclamation mark are processed as expected.
- RU: Выполнен SemVer patch-бамп до `8.61.21`; синхронизированы все актуальные упоминания версии проекта и Android-метаданные (`ANDROID_VERSION_NAME=8.61.21`, `ANDROID_VERSION_CODE=753`).
- EN: Performed a SemVer patch bump to `8.61.21`; synchronized all active project version mentions and Android metadata (`ANDROID_VERSION_NAME=8.61.21`, `ANDROID_VERSION_CODE=753`).

## [8.61.19] - 2026-05-15

- RU: Исправлен краш Matrix command bot при старте: в диагностическом логе ACL использовалось несуществующее поле `whitelist_user_ids`; заменено на актуальное `allowed_users`, из-за чего `AttributeError` больше не возникает.
- EN: Fixed a startup crash in Matrix command bot: ACL diagnostics referenced non-existent `whitelist_user_ids`; switched to current `allowed_users`, preventing the `AttributeError`.
- RU: Выполнен SemVer patch-бамп до `8.61.19`; синхронизированы упоминания версии проекта и Android-метаданные (`ANDROID_VERSION_NAME=8.61.19`, `ANDROID_VERSION_CODE=751`), обновлена ссылка prerelease APK в README.
- EN: Performed a SemVer patch bump to `8.61.19`; synchronized project version mentions and Android metadata (`ANDROID_VERSION_NAME=8.61.19`, `ANDROID_VERSION_CODE=751`), and updated the prerelease APK link in README.

## [8.61.18] - 2026-05-14

- RU: Выполнен SemVer patch-бамп до `8.61.18`; синхронизированы упоминания версии проекта во всех актуальных файлах, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.61.18` и `ANDROID_VERSION_CODE=750`, а также ссылки на prerelease APK в документации.
- EN: Performed a SemVer patch bump to `8.61.18`; synchronized project version mentions across all active files, updated Android metadata to `ANDROID_VERSION_NAME=8.61.18` and `ANDROID_VERSION_CODE=750`, and refreshed prerelease APK links in docs.

## [8.61.17] - 2026-05-14

- RU: Выполнен SemVer patch-бамп до `8.61.17`; синхронизированы все актуальные упоминания версии проекта в runtime/config/Android/README, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.61.17` и `ANDROID_VERSION_CODE=749`.
- EN: Performed a SemVer patch bump to `8.61.17`; synchronized all active project version mentions across runtime/config/Android/README, and updated Android metadata to `ANDROID_VERSION_NAME=8.61.17` and `ANDROID_VERSION_CODE=749`.

## [8.61.16] - 2026-05-14

- RU: Добавлено явное логирование запуска Matrix command sync с параметрами ACL и входящих команд (`room`, `sender`, `command`) для быстрой диагностики, когда в логах не видно реакции на сообщения комнаты.
- EN: Added explicit Matrix command sync startup logging with ACL parameters and incoming command logs (`room`, `sender`, `command`) for fast diagnostics when room message reactions are not visible in logs.
- RU: Выполнен SemVer patch-бамп до `8.61.16`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.61.16` и `ANDROID_VERSION_CODE=748`, ссылка prerelease APK в README синхронизирована.
- EN: Performed a SemVer patch bump to `8.61.16`; Android metadata updated to `ANDROID_VERSION_NAME=8.61.16` and `ANDROID_VERSION_CODE=748`, and the README prerelease APK link was synchronized.

## [8.61.15] - 2026-05-14

- RU: Синхронизированы актуальные упоминания версии проекта во всех рабочих файлах; значения приведены к `8.61.15`.
- EN: Synchronized current project version mentions across all active files; values were aligned to `8.61.15`.
- RU: Добавлены диагностические Matrix-команды `!diag` и `!ping`, а также расширена справка `!help/!menu` для оперативной проверки маршрутизации команд и ACL.
- EN: Added diagnostic Matrix commands `!diag` and `!ping`, and expanded `!help/!menu` guidance for quick command-routing and ACL checks.
- RU: Исправлен парсинг Matrix-команд в bridged/префиксных сообщениях: `!diag` и другие `!`-команды теперь извлекаются даже если команда не в начале строки, что устраняет ложное игнорирование как echo от бота.
- EN: Fixed Matrix command parsing for bridged/prefixed messages: `!diag` and other `!` commands are now extracted even when not at the start of a line, preventing false self-echo ignores.
- RU: Тестовое Matrix-сообщение из Telegram-бота обновлено: теперь показывает корректные Matrix-команды с префиксом `!` вместо Telegram-style `/...`.
- EN: Updated Matrix test message from the Telegram bot: it now shows correct Matrix commands with `!` prefix instead of Telegram-style `/...`.
- RU: Выполнен SemVer patch-бамп до `8.61.15`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.61.15` и `ANDROID_VERSION_CODE=747`.
- EN: Performed a SemVer patch bump to `8.61.15`; Android metadata updated to `ANDROID_VERSION_NAME=8.61.15` and `ANDROID_VERSION_CODE=747`.

## [8.61.12] - 2026-05-13

- RU: Исправлена обработка Matrix-команд из чата с ботом при использовании того же user_id: self-команды (например, `!help`) теперь обрабатываются, а обычные echo-сообщения по-прежнему игнорируются.
- EN: Fixed Matrix command handling in bot chat when using the same user_id: self-commands (for example, `!help`) are now processed, while regular echo messages are still ignored.
- RU: Выполнен SemVer patch-бамп до `8.61.12`; синхронизированы упоминания версии в runtime/config/Android, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.61.12` и `ANDROID_VERSION_CODE=744`.
- EN: Performed a SemVer patch bump to `8.61.12`; synchronized version mentions across runtime/config/Android, and updated Android metadata to `ANDROID_VERSION_NAME=8.61.12` and `ANDROID_VERSION_CODE=744`.

## [8.61.11] - 2026-05-13

- RU: Исправлена инициализация Matrix command-bot: на старте добавлен `whoami`, чтобы корректно определить `user_id` бота и перестать обрабатывать собственные служебные сообщения как внешние команды.
- EN: Fixed Matrix command-bot initialization: added `whoami` during startup to correctly resolve bot `user_id` and stop treating self-sent service messages as external commands.
- RU: Снижен шум логов для входящих Matrix-событий без команд: такие сообщения теперь игнорируются тихо, с редким диагностическим логом вместо спама на каждое событие.
- EN: Reduced log noise for inbound Matrix events without commands: such messages are now ignored quietly with occasional diagnostic logs instead of per-event spam.
- RU: Выполнен SemVer patch-бамп до `8.61.11`; синхронизированы упоминания версии в runtime/config/docs/Android.
- EN: Performed a SemVer patch bump to `8.61.11`; synchronized version mentions across runtime/config/docs/Android.
## [8.61.8] - 2026-05-13

- RU: Улучшена диагностика пропуска Matrix command sync при отсутствии `matrix-nio`: в лог добавлен путь активного Python-интерпретатора и точная команда установки зависимости в этот интерпретатор.
- EN: Improved diagnostics for skipped Matrix command sync when `matrix-nio` is missing: logs now include the active Python interpreter path and an exact install command for that interpreter.
- RU: Выполнен SemVer patch-бамп до `8.61.8`; синхронизированы актуальные упоминания версии в проекте и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.61.8` и `ANDROID_VERSION_CODE=742`.
- EN: Performed a SemVer patch bump to `8.61.8`; synchronized active version mentions across the project and updated Android metadata to `ANDROID_VERSION_NAME=8.61.8` and `ANDROID_VERSION_CODE=742`.

## [8.60.4] - 2026-05-13

- EN: Fixed Matrix alert initialization in the main startup flow: `lib/alerts.py` now performs a safe fallback to `config.settings` when Matrix globals are empty, reducing false "channel not configured" skips caused by late initialization order.
- RU: Исправлена инициализация Matrix-алертов в основном потоке запуска: `lib/alerts.py` теперь делает безопасный fallback к `config.settings`, если Matrix-глобали пустые, что снижает ложные пропуски "канал не настроен" из-за порядка инициализации.
- EN: SemVer patch bump to `8.60.4`; synchronized active version mentions across runtime/config/docs/Android and bumped Android metadata to `ANDROID_VERSION_NAME=8.60.4` and `ANDROID_VERSION_CODE=737`.
- RU: Патч-бамп SemVer до `8.60.4`; синхронизированы актуальные упоминания версии в runtime/config/docs/Android и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.60.4` и `ANDROID_VERSION_CODE=737`.

## [8.60.0] - 2026-05-13
- RU: Добавлен входящий Matrix command-bot на базе `matrix-nio`: long-poll `/sync`, обработчик `m.room.message`, роутинг команд `!status`, `!report`, `!settings` и ответы в комнату.
- EN: Added inbound Matrix command bot based on `matrix-nio`: long-poll `/sync`, `m.room.message` handler, command routing for `!status`, `!report`, `!settings`, and room replies.
- RU: Команда `!status` переиспользует backend-проверку доступности через `core.task_router.run_availability_task`, а `!report` использует существующий генератор отчёта `morning_report.force_report()`.
- EN: `!status` now reuses backend availability checks via `core.task_router.run_availability_task`, while `!report` reuses existing report generation via `morning_report.force_report()`.
- RU: Добавлен ACL для Matrix-команд: whitelist по `MATRIX_ALLOWED_USER_IDS` и ограничение комнат через `MATRIX_ALLOWED_ROOM_IDS` (с fallback на `MATRIX_ROOM_ID`).
- EN: Added ACL for Matrix commands: user whitelist via `MATRIX_ALLOWED_USER_IDS` and room restriction via `MATRIX_ALLOWED_ROOM_IDS` (fallback to `MATRIX_ROOM_ID`).
- RU: Добавлен аудит команд в логах (`[MATRIX_AUDIT]`): кто, когда, какая команда и результат ACL.
- EN: Added command audit logging (`[MATRIX_AUDIT]`): who, when, which command, and ACL result.
- RU: Выполнен SemVer minor-бамп до `8.60.0`; обновлены актуальные упоминания версии в runtime-файлах.
- EN: Performed SemVer minor bump to `8.60.0`; synchronized active runtime version mentions.

## [8.59.17] - 2026-05-13
- RU: Добавлена отдельная эксплуатационная документация по управлению ботом в Matrix (`docs/matrix_bot_management.md`): быстрый запуск, первичная настройка, ротация токена, диагностика и roadmap входящих команд.
- EN: Added a dedicated operational guide for Matrix bot management (`docs/matrix_bot_management.md`): quick start, initial setup, token rotation, troubleshooting, and incoming-commands roadmap.
- RU: В README добавлена прямая ссылка на новую инструкцию по Matrix, чтобы сократить время онбординга и убрать дубли в основном документе.
- EN: Added a direct link in README to the new Matrix guide to reduce onboarding time and avoid duplicated operational details in the main document.
- RU: Выполнен SemVer patch-бамп до `8.59.17`; синхронизированы актуальные упоминания версии в проекте, Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.59.17` и `ANDROID_VERSION_CODE=733`.
- EN: Performed a SemVer patch bump to `8.59.17`; synchronized active version mentions across the project, and updated Android metadata to `ANDROID_VERSION_NAME=8.59.17` and `ANDROID_VERSION_CODE=733`.
## [8.59.15] - 2026-05-13
- RU: Приведены к единому актуальному значению все рабочие упоминания версии проекта в исходниках и конфигурации; текущая версия синхронизирована как `8.59.15`.
- EN: Aligned all active project version mentions across source files and configuration; current version is synchronized to `8.59.15`.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.15` и `ANDROID_VERSION_CODE=731`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.15` and `ANDROID_VERSION_CODE=731`.

## [8.59.14] - 2026-05-13
- RU: Уточнена рекомендация по Matrix-стеку под этот репозиторий: основным вариантом выбран `matrix-nio` (Python) с аргументацией по внедрению в текущий backend, эксплуатации и контролю доступа.
- EN: Refined Matrix stack recommendation for this repository: `matrix-nio` (Python) is now the primary option, with rationale focused on backend integration, operations, and access control.
- RU: Добавлены критерии, когда вместо `matrix-nio` уместнее использовать `maubot` или `matrix-bot-sdk`.
- EN: Added decision criteria for when `maubot` or `matrix-bot-sdk` is a better fit than `matrix-nio`.
- RU: SemVer patch-бамп до `8.59.14`; синхронизированы актуальные упоминания версии в runtime/config/docs/Android.
- EN: SemVer patch bump to `8.59.14`; synchronized current version mentions across runtime/config/docs/Android.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.14` и `ANDROID_VERSION_CODE=730`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.14` and `ANDROID_VERSION_CODE=730`.

## [8.59.13] - 2026-05-13
- RU: В `README.md` добавлен практический гайд по управлению мониторингом через Matrix (как в Telegram-боте): варианты стека (`matrix-nio`, `matrix-bot-sdk`, `maubot`), безопасный MVP команд и рекомендации по ACL.
- EN: Added a practical guide to `README.md` for Matrix-based monitoring control (Telegram-bot style): stack options (`matrix-nio`, `matrix-bot-sdk`, `maubot`), safe MVP commands, and ACL recommendations.
- RU: SemVer patch-бамп до `8.59.13`; синхронизированы актуальные упоминания версии в runtime/config/docs/Android.
- EN: SemVer patch bump to `8.59.13`; synchronized current version mentions across runtime/config/docs/Android.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.13` и `ANDROID_VERSION_CODE=729`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.13` and `ANDROID_VERSION_CODE=729`.

## [8.59.12] - 2026-05-13
- RU: Уточнена документация по bootstrap Matrix-бота: явно разделены `--admin-token` (админский токен Synapse) и обычный `MATRIX_ACCESS_TOKEN` бота/пользователя из настроек.
- EN: Clarified Matrix bot bootstrap docs: explicitly distinguished `--admin-token` (Synapse admin token) from the regular bot/user `MATRIX_ACCESS_TOKEN` used in settings.
- RU: Добавлены пояснения по `--password`: это новый пароль создаваемого bot-user, нужен для login и получения `MATRIX_ACCESS_TOKEN`.
- EN: Added `--password` explanation: it is a new password for the created bot user and is required for login/access-token retrieval.
- RU: SemVer patch-бамп до `8.59.12`; синхронизированы текущие упоминания версии в runtime/config/docs/Android.
- EN: SemVer patch bump to `8.59.12`; synchronized current version mentions across runtime/config/docs/Android.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.12` и `ANDROID_VERSION_CODE=728`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.12` and `ANDROID_VERSION_CODE=728`.

## [8.59.11] - 2026-05-13
- RU: Добавлен скрипт `scripts/setup_matrix_bot.py` для первичной установки Matrix-бота на Synapse: создание пользователя через Admin API, логин, получение `access_token` и join в указанную комнату.
- EN: Added `scripts/setup_matrix_bot.py` bootstrap script for initial Matrix bot setup on Synapse: user creation via Admin API, login, `access_token` retrieval, and joining a target room.
- RU: SemVer patch-бамп до `8.59.11`; синхронизированы текущие упоминания версии в runtime/config/docs/Android.
- EN: SemVer patch bump to `8.59.11`; synchronized current version mentions across runtime/config/docs/Android.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.12` и `ANDROID_VERSION_CODE=727`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.12` and `ANDROID_VERSION_CODE=727`.

## [8.59.10] - 2026-05-13
- RU: Выполнен SemVer patch-бамп до `8.59.10`; выровнены разъехавшиеся упоминания версии во всех рабочих файлах проекта (runtime/config/docs/Android).
- EN: Performed a SemVer patch bump to `8.59.10`; aligned drifted version mentions across all working project files (runtime/config/docs/Android).
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.12` и `ANDROID_VERSION_CODE=726`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.12` and `ANDROID_VERSION_CODE=726`.

## [8.59.9] - 2026-05-13
- RU: Исправлена синтаксическая ошибка в Matrix payload builder: формирование `formatted_body` вынесено в отдельную переменную, чтобы устранить падение сервиса с `SyntaxError: f-string: expecting '\}'` при старте.
- EN: Fixed a syntax error in the Matrix payload builder: `formatted_body` assembly now uses a separate variable, preventing service startup crash with `SyntaxError: f-string: expecting '\}'`.
- RU: SemVer patch-бамп до `8.59.9`; синхронизированы текущие упоминания версии в runtime/конфигурации/Android.
- EN: SemVer patch bump to `8.59.9`; synchronized current version mentions across runtime/configuration/Android.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.9` и `ANDROID_VERSION_CODE=725`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.9` and `ANDROID_VERSION_CODE=725`.

## [8.59.8] - 2026-05-13
- RU: SemVer patch-бамп до `8.59.8`; синхронизированы все текущие упоминания версии проекта в runtime/конфигурации/Android/документации.
- EN: SemVer patch bump to `8.59.8`; synchronized all current project version mentions across runtime/configuration/Android/documentation.
- RU: Обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.59.8` и `ANDROID_VERSION_CODE=724`.
- EN: Updated Android metadata to `ANDROID_VERSION_NAME=8.59.8` and `ANDROID_VERSION_CODE=724`.
- RU: Для Matrix тестового сообщения добавлены action-кнопки в стиле Telegram (рендер через `formatted_body` и HTML-ссылки + текстовый fallback для клиентов без rich-format).
- EN: Added Telegram-style action buttons for Matrix test messages (rendered via `formatted_body` HTML links with plain-text fallback for clients without rich formatting).

## [8.59.6] - 2026-05-13
- RU: Исправлена отправка тестового сообщения в Matrix: запрос на endpoint `/_matrix/client/v3/rooms/{roomId}/send/m.room.message/{txnId}` переведён на корректный HTTP-метод `PUT`, чтобы устранить `405 Method Not Allowed`.
- EN: Fixed Matrix test-message delivery: request to `/_matrix/client/v3/rooms/{roomId}/send/m.room.message/{txnId}` now uses the correct HTTP `PUT` method to eliminate `405 Method Not Allowed`.
- RU: SemVer patch-бамп до `8.59.6`; синхронизированы явные упоминания версии в runtime/config/docs/Android, обновлены `ANDROID_VERSION_NAME=8.59.6` и `ANDROID_VERSION_CODE=722`.
- EN: SemVer patch bump to `8.59.6`; synchronized explicit version mentions across runtime/config/docs/Android, updated `ANDROID_VERSION_NAME=8.59.6` and `ANDROID_VERSION_CODE=722`.

## 8.59.5 - 2026-05-13

- RU: Исправлен тест Matrix из меню настроек: перед отправкой тестового сообщения callback теперь читает `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, `MATRIX_ROOM_ID` из БД и вызывает `init_matrix_bot`, поэтому тест больше не пропускается с `homeserver=empty, token=empty, room_id=empty`.
- EN: Fixed Matrix test from settings menu: before sending the test message, the callback now reads `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, and `MATRIX_ROOM_ID` from DB and calls `init_matrix_bot`, so the test is no longer skipped with `homeserver=empty, token=empty, room_id=empty`.
- RU: SemVer patch bump до `8.59.5`; синхронизированы явные упоминания версии проекта в runtime/config/docs/Android, обновлены `ANDROID_VERSION_NAME=8.59.5` и `ANDROID_VERSION_CODE=721`.
- EN: SemVer patch bump to `8.59.5`; synchronized explicit project version mentions across runtime/config/docs/Android, updated `ANDROID_VERSION_NAME=8.59.5` and `ANDROID_VERSION_CODE=721`.

## 8.59.3 - 2026-05-13

- RU: Исправлена дубликация Telegram-алертов в Matrix: `txn_id` для Matrix Client API теперь генерируется через `uuid4`, поэтому при нескольких отправках в одну миллисекунду события не конфликтуют и не теряются.
- EN: Fixed Telegram-to-Matrix alert duplication: Matrix Client API `txn_id` is now generated with `uuid4`, so concurrent sends within the same millisecond no longer collide or drop events.
- RU: SemVer patch bump до `8.58.51`; синхронизированы все явные упоминания версии проекта в runtime/config/docs/Android, обновлены `ANDROID_VERSION_NAME=8.58.51` и `ANDROID_VERSION_CODE=719`.
- EN: SemVer patch bump to `8.58.51`; synchronized all explicit project version mentions across runtime/config/docs/Android, updated `ANDROID_VERSION_NAME=8.58.51` and `ANDROID_VERSION_CODE=719`.

## 8.58.46 - 2026-05-12

- RU: SemVer patch bump до `8.58.46`; синхронизированы все явные упоминания версии проекта в runtime/config/docs/Android, обновлены `ANDROID_VERSION_NAME=8.58.46` и `ANDROID_VERSION_CODE=714`.
- EN: SemVer patch bump to `8.58.46`; synchronized all explicit project version mentions across runtime/config/docs/Android, updated `ANDROID_VERSION_NAME=8.58.46` and `ANDROID_VERSION_CODE=714`.

## 8.58.44 - 2026-05-12
- RU: Исправлена отправка в Matrix для алертов недоступности: endpoint Matrix Client API теперь вызывается в корректном формате `.../send/m.room.message/{txnId}` c `Authorization: Bearer`, поэтому уведомления дублируются в Matrix даже при падении целевого сервера.
- EN: Fixed Matrix delivery for availability alerts: Matrix Client API is now called using the correct `.../send/m.room.message/{txnId}` endpoint with `Authorization: Bearer`, so notifications are duplicated to Matrix even when the target server is down.
- RU: SemVer patch bump до `8.58.44`; синхронизированы явные упоминания версии в runtime/config/docs/Android, обновлены `ANDROID_VERSION_NAME=8.58.44` и `ANDROID_VERSION_CODE=712`.
- EN: SemVer patch bump to `8.58.44`; synchronized explicit version mentions across runtime/config/docs/Android, updated `ANDROID_VERSION_NAME=8.58.44` and `ANDROID_VERSION_CODE=712`.

## 8.58.43 - 2026-05-12
- RU: SemVer patch bump до `8.58.43`; синхронизированы все явные упоминания версии проекта во всех рабочих файлах (runtime/config/docs/Android), обновлены `ANDROID_VERSION_NAME=8.58.43`, повышен `ANDROID_VERSION_CODE=711` и синхронизирована in-app версия Android-клиента.
- EN: SemVer patch bump to `8.58.43`; synchronized all explicit project version mentions across working files (runtime/config/docs/Android), updated `ANDROID_VERSION_NAME=8.58.43`, bumped `ANDROID_VERSION_CODE=711`, and synced Android in-app client version.

## 8.58.42 - 2026-05-12
- RU: Matrix-отправка исправлена: `room_id` теперь URL-encoded перед вызовом Matrix Client API, поэтому идентификаторы комнат вида `!room:server` корректно доходят до endpoint и алерты не теряются из-за некорректного URL.
- EN: Fixed Matrix delivery: `room_id` is now URL-encoded before Matrix Client API call, so room IDs like `!room:server` reach the endpoint correctly and alerts are no longer dropped due to malformed URL paths.
- RU: SemVer patch bump до `8.58.42`; синхронизированы все явные упоминания версии проекта в runtime/config/docs/Android, обновлены `ANDROID_VERSION_NAME=8.58.42`, `ANDROID_VERSION_CODE=710` и in-app версия Android-клиента.
- EN: SemVer patch bump to `8.58.42`; synchronized all explicit project version mentions across runtime/config/docs/Android, updated `ANDROID_VERSION_NAME=8.58.42`, `ANDROID_VERSION_CODE=710`, and Android in-app version.

## 8.58.41 - 2026-05-12
- RU: SemVer patch bump до `8.58.41`; синхронизированы все явные упоминания версии проекта во всех затронутых файлах (runtime/config/docs/Android), обновлены `ANDROID_VERSION_NAME=8.58.41`, повышен `ANDROID_VERSION_CODE=709` и синхронизирована in-app версия Android-клиента.
- EN: SemVer patch bump to `8.58.41`; synchronized all explicit project version mentions across touched files (runtime/config/docs/Android), updated `ANDROID_VERSION_NAME=8.58.41`, bumped `ANDROID_VERSION_CODE=709`, and synced Android client in-app version.

## 8.58.40 - 2026-05-12

- RU: SemVer patch bump до `8.58.40`; синхронизированы все явные упоминания версии проекта в runtime/config/Android-файлах, Android metadata обновлены до `ANDROID_VERSION_NAME=8.58.40` и `ANDROID_VERSION_CODE=708`.
- EN: SemVer patch bump to `8.58.40`; synchronized all explicit project version mentions across runtime/config/Android files, Android metadata updated to `ANDROID_VERSION_NAME=8.58.40` and `ANDROID_VERSION_CODE=708`.

## 8.58.39 - 2026-05-12

- RU: README по Matrix дополнен пояснениями про Bash history expansion (`!` в `room_id`) и рабочими примерами экспорта `MATRIX_ROOM_ID` для shell.
- EN: Matrix README section now explains Bash history expansion (`!` in `room_id`) with working `MATRIX_ROOM_ID` export examples.
- RU: README уточнён по `MATRIX_ACCESS_TOKEN`: нужен токен того Matrix-аккаунта, который отправляет алерты (рекомендован отдельный бот-пользователь).
- EN: README clarified `MATRIX_ACCESS_TOKEN`: use the token of the Matrix account that sends alerts (dedicated bot account is recommended).
- RU: SemVer patch bump до `8.58.39`; Android metadata обновлены до `ANDROID_VERSION_NAME=8.58.39` и `ANDROID_VERSION_CODE=707`.
- EN: SemVer patch bump to `8.58.39`; Android metadata updated to `ANDROID_VERSION_NAME=8.58.39` and `ANDROID_VERSION_CODE=707`.

## 8.58.38 - 2026-05-11

- RU: Android: удалена кнопка «Проверить связь с BFF» из экрана настроек, так как ручная проверка не давала стабильного результата.
- EN: Android: removed the “Check BFF connection” button from settings because the manual check was unreliable.
- RU: Добавлен Matrix-канал уведомлений (homeserver `matrix.202020.ru`) как дополнительная доставка алертов параллельно Telegram при заполненных `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, `MATRIX_ROOM_ID`.
- EN: Added Matrix notifications (homeserver `matrix.202020.ru`) as an additional alert delivery channel alongside Telegram when `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN`, and `MATRIX_ROOM_ID` are configured.
- RU: В README добавлена пошаговая инструкция по созданию Matrix-бота/пользователя и подключению комнаты для алертов.
- EN: Added a step-by-step README guide for creating a Matrix bot/user and wiring a room for alert delivery.
- RU: SemVer patch bump до `8.58.38`; Android metadata обновлены до `ANDROID_VERSION_NAME=8.58.38` и `ANDROID_VERSION_CODE=706`.
- EN: SemVer patch bump to `8.58.38`; Android metadata updated to `ANDROID_VERSION_NAME=8.58.38` and `ANDROID_VERSION_CODE=706`.

## 8.58.36 - 2026-05-10
- RU: Android: исправлена ошибка компиляции `Unresolved reference colors` в `MainActivity` — для Material 3 заменён вызов `MaterialTheme.colors.error` на `MaterialTheme.colorScheme.error`.
- EN: Android: fixed `Unresolved reference colors` compilation error in `MainActivity` by switching Material 3 usage from `MaterialTheme.colors.error` to `MaterialTheme.colorScheme.error`.
- RU: SemVer patch bump до `8.58.36`; обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.58.36` и `ANDROID_VERSION_CODE=704`, синхронизированы явные упоминания версии в runtime/конфигах/документации.
- EN: SemVer patch bump to `8.58.36`; updated Android metadata to `ANDROID_VERSION_NAME=8.58.36` and `ANDROID_VERSION_CODE=704`, and synchronized explicit version mentions across runtime/config/docs.

## 8.58.35 - 2026-05-10
- RU: Android: добавлена проверка TLS-сертификата Base URL BFF при синхронизации настроек; в оперативном центре теперь показывается текущий статус сертификата (OK / скоро истекает / истёк / ошибка проверки) и предупреждение при риске истечения в ближайшие 14 дней.
- EN: Android: added TLS certificate expiry check for the BFF Base URL during settings sync; Ops Center now shows current certificate status (OK / expiring soon / expired / check error) and displays a warning when expiry is within the next 14 days.
- RU: SemVer patch bump до `8.58.35`; обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.58.35` и `ANDROID_VERSION_CODE=703`, синхронизированы явные упоминания версии в runtime/документации.
- EN: SemVer patch bump to `8.58.35`; updated Android metadata to `ANDROID_VERSION_NAME=8.58.35` and `ANDROID_VERSION_CODE=703`, synchronized explicit version mentions in runtime/documentation.

## 8.58.34 - 2026-05-10
- RU: Добавлен операционный TLS-блок для `api.202020.ru:8443` с готовым cron-скриптом (exit code 1 при истечении сертификата) и пошаговым сценарием ручного продления через certbot/acme.sh; выполнен SemVer patch bump до `8.58.34` и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.58.34` и `ANDROID_VERSION_CODE=702`.
- EN: Added an operational TLS section for `api.202020.ru:8443` with a ready-to-use cron check script (exit code 1 when certificate is expired) and step-by-step manual renewal flow for certbot/acme.sh; performed SemVer patch bump to `8.58.34` and updated Android metadata to `ANDROID_VERSION_NAME=8.58.34` and `ANDROID_VERSION_CODE=702`.

## 8.58.32 - 2026-05-10
- RU: SemVer patch bump до `8.58.32`; синхронизированы явные упоминания версии проекта во всех файлах с runtime/config/doc-константами, обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.58.32` и `ANDROID_VERSION_CODE=700`.
- EN: SemVer patch bump to `8.58.32`; synchronized explicit project-version mentions across runtime/config/doc constants, and updated Android metadata to `ANDROID_VERSION_NAME=8.58.32` and `ANDROID_VERSION_CODE=700`.

## 8.58.30 - 2026-05-10
- RU: Android: улучшена диагностика TLS-ошибок в UI — для `SSLException` добавлены более точные подсказки про просроченный/ещё не действительный сертификат и про mismatch имени хоста в сертификате.
- EN: Android: improved TLS error diagnostics in UI — `SSLException` now provides more specific hints for expired/not-yet-valid certificates and hostname mismatch in certificate.
- RU: SemVer patch bump до `8.58.30`; обновлены `ANDROID_VERSION_NAME=8.58.30` и `ANDROID_VERSION_CODE=698`, синхронизированы явные упоминания версии.
- EN: SemVer patch bump to `8.58.30`; updated `ANDROID_VERSION_NAME=8.58.30` and `ANDROID_VERSION_CODE=698`, synchronized explicit version mentions.

## 8.58.28 - 2026-05-10
- RU: Досинхронизированы явные упоминания версии проекта во всех backend/runtime/doc-файлах, где оставался рассинхрон после прошлого релизного шага.
- EN: Finalized synchronization of explicit project version mentions across backend/runtime/doc files where drift remained after the previous release step.
- RU: SemVer patch bump до `8.58.28`; обновлены `ANDROID_VERSION_NAME=8.58.28` и `ANDROID_VERSION_CODE=696`.
- EN: SemVer patch bump to `8.58.28`; updated `ANDROID_VERSION_NAME=8.58.28` and `ANDROID_VERSION_CODE=696`.

## 8.58.27 - 2026-05-10
- RU: Починена синхронизация с BFF, когда токен хранится в сохранённых настройках (а поле токена в UI временно пустое); синхронизация больше не скипается ошибочно.
- EN: Fixed BFF synchronization when token is stored in persisted settings (while token input in UI is temporarily empty); sync is no longer skipped incorrectly.
- RU: Исправлена проверка связи с BFF в настройках: результат проверки теперь явно формируется в сообщении приложения и дублируется в логах с тем же статусом.
- EN: Fixed BFF connection check in settings: check result is now explicitly shown in app message and mirrored in logs with matching status.
- RU: SemVer patch bump до `8.58.27`; обновлены `ANDROID_VERSION_NAME=8.58.27` и `ANDROID_VERSION_CODE=695`, синхронизированы явные упоминания версии.
- EN: SemVer patch bump to `8.58.27`; updated `ANDROID_VERSION_NAME=8.58.27` and `ANDROID_VERSION_CODE=695`, synchronized explicit version mentions.

## 8.58.25 - 2026-05-10
- RU: Android: исправлена сборка уведомлений о недоступности серверов — в `ServerDownAlertWorker` объединён `companion object`, из-за чего снова доступны константы (`CHANNEL_ID`, `EXTRA_DOWN_SERVER_NAMES`, `NOTIFICATION_ID`) и методы планирования (`schedule`, `scheduleNext`).
- EN: Android: fixed build for server-down notifications — merged duplicated `companion object` in `ServerDownAlertWorker`, restoring access to constants (`CHANNEL_ID`, `EXTRA_DOWN_SERVER_NAMES`, `NOTIFICATION_ID`) and scheduling methods (`schedule`, `scheduleNext`).
- RU: SemVer patch bump до `8.58.26`; обновлены `ANDROID_VERSION_NAME=8.58.26` и `ANDROID_VERSION_CODE=694`, синхронизированы явные упоминания версии.
- EN: SemVer patch bump to `8.58.26`; updated `ANDROID_VERSION_NAME=8.58.26` and `ANDROID_VERSION_CODE=694`, synchronized explicit version mentions.

## 8.58.26 - 2026-05-10
- RU: Android: починена проверка связи с BFF в настройках — запрос теперь выполняется с нормализованными token/Base URL, а результат проверки дублируется в сообщение приложения и в системный лог.
- EN: Android: fixed BFF connectivity check in settings — requests now run with normalized token/base URL, and check results are mirrored to both in-app message and system log.
- RU: Android: стабилизирована доставка данных и оповещений из фоновых воркеров — для API-вызовов используется нормализованный Base URL, добавлены явные логи успеха/ошибок, чтобы легче разбирать отвал синхронизации.
- EN: Android: stabilized data delivery and alerts from background workers — API calls now use normalized base URL, with explicit success/failure logs to simplify sync-failure diagnostics.
- RU: SemVer patch bump до `8.58.25`; обновлены `ANDROID_VERSION_NAME=8.58.25` и `ANDROID_VERSION_CODE=693`, синхронизированы явные упоминания версии.
- EN: SemVer patch bump to `8.58.25`; updated `ANDROID_VERSION_NAME=8.58.25` and `ANDROID_VERSION_CODE=693`, and synchronized explicit version mentions.

## 8.58.21 - 2026-05-10
- RU: Android: усилил логирование синхронизации (старт/этапы/финиш по `sessionId`), чтобы в логах явно было видно ход sync-процесса.
- EN: Android: improved synchronization logging (start/steps/finish with `sessionId`) so sync flow is clearly visible in logs.
- RU: В секцию BFF в настройках добавлена отдельная кнопка «Проверить связь с BFF»; проверка связи с сервером бота оставлена в секции Bot.
- EN: Added a dedicated “Check BFF connectivity” button to the BFF settings section; bot-server connectivity check remains in the Bot section.
- RU: SemVer patch bump до `8.58.21`; обновлены `ANDROID_VERSION_NAME=8.58.21`, `ANDROID_VERSION_CODE=689`, runtime-версия Android UI и ссылка prerelease APK в README.
- EN: SemVer patch bump to `8.58.21`; updated `ANDROID_VERSION_NAME=8.58.21`, `ANDROID_VERSION_CODE=689`, Android UI runtime version, and prerelease APK link in README.

## 8.58.20 - 2026-05-10
- RU: Android: добавлены расширенные логи синхронизации (старт с базовым URL/флагом токена и результаты проверки связи) для диагностики проблем, когда синхронизация не стартует и в логах пусто.
- EN: Android: added extended synchronization logs (start with base URL/token flag and connectivity-check results) to diagnose cases where sync does not start and logs are empty.
- RU: В разделе «Настройки бота» добавлена кнопка «Проверить связь с сервером бота», выполняющая API-проверку и показывающая результат пользователю.
- EN: Added a “Check bot server connection” button in “Bot settings”; it runs an API connectivity check and shows the result to the user.
- RU: Исправлена ошибка компиляции Android (`Suspension functions can only be called within coroutine body`) в `MainViewModel`: helper `fetchOrLog` переведён в `suspend`-контекст с явной обработкой исключений через `try/catch`.
- EN: Fixed Android compilation error (`Suspension functions can only be called within coroutine body`) in `MainViewModel`: the `fetchOrLog` helper is now suspend-aware with explicit `try/catch` exception handling.
- RU: Исправлена ошибка компиляции Android в `MainViewModel`: в логе старта синхронизации заменено несуществующее поле `state.tokenInput` на `state.token`.
- EN: Fixed Android compilation error in `MainViewModel`: replaced nonexistent `state.tokenInput` with `state.token` in the sync-start log line.
- RU: SemVer patch bump до `8.58.20`; синхронизированы явные упоминания текущей версии в runtime-заголовках, конфигурации, документации и Android metadata (`ANDROID_VERSION_NAME=8.58.20`, `ANDROID_VERSION_CODE=688`).
- EN: SemVer patch bump to `8.58.20`; synchronized explicit current-version mentions across runtime headers, configuration, documentation, and Android metadata (`ANDROID_VERSION_NAME=8.58.20`, `ANDROID_VERSION_CODE=688`).
## 8.58.16 - 2026-05-07
- RU: Исправлена ложноположительная «успешная» отправка утреннего отчета: `modules/morning_report.py` теперь отправляет отчет через `lib.alerts.send_alert`, проверяет `sent_ok` и пишет ошибку доставки при `sent=False`.
- EN: Fixed false-positive "successful" morning report delivery: `modules/morning_report.py` now sends via `lib.alerts.send_alert`, validates `sent_ok`, and logs delivery failure when `sent=False`.
- RU: SemVer patch bump до `8.58.16`; синхронизированы явные упоминания текущей версии в runtime-заголовках, конфигурации и Android metadata.
- EN: SemVer patch bump to `8.58.16`; synchronized explicit current-version mentions across runtime headers, configuration, and Android metadata.

## 8.58.14 - 2026-05-07
- RU: Исправлен двойной запуск сбора перед отправкой утреннего отчета: в плановом автозапуске `core/monitor.py` теперь используется `send_report(..., collect_before_send=False)`, чтобы не стартовал повторный `collect_morning_data` и отчет уходил сразу по уже собранному слепку.
- EN: Fixed duplicate data-collection start before morning-report delivery: scheduled auto-run in `core/monitor.py` now calls `send_report(..., collect_before_send=False)` to avoid a second `collect_morning_data` pass and send immediately using the collected snapshot.
- RU: Исправлен `NameError` в `core/monitor.py` при старте мониторинга через proxychains/systemd: переменная `DATA_COLLECTION_TIME` теперь корректно импортируется из конфигурации и используется в стартовом сообщении.
- EN: Fixed `NameError` in `core/monitor.py` during monitor startup via proxychains/systemd: `DATA_COLLECTION_TIME` is now properly imported from configuration and used in the startup message.
- RU: SemVer patch bump до `8.58.14`; синхронизированы явные упоминания текущей версии проекта в runtime-заголовках Python-модулей, backend-конфигах, документации и Android metadata (`ANDROID_VERSION_NAME=8.58.16`, `ANDROID_VERSION_CODE=684`).
- EN: SemVer patch bump to `8.58.14`; synchronized explicit current-version mentions across Python runtime headers, backend config constants, documentation, and Android metadata (`ANDROID_VERSION_NAME=8.58.16`, `ANDROID_VERSION_CODE=684`).

## 8.58.10 - 2026-05-07
- RU: Добавлено server-visible логирование старта запуска сбора данных для утреннего отчёта в `core/monitor_core.py`: теперь перед сбором пишется `[MORNING_REPORT_COLLECTION] start` с текущим временем, временем триггера и расчётным временем запуска.
- EN: Added server-visible logging for morning-report data collection start in `core/monitor_core.py`: before collecting data, the app now writes `[MORNING_REPORT_COLLECTION] start` with current time, trigger time, and resolved scheduled datetime.
- RU: SemVer patch bump до `8.58.10`; синхронизированы явные упоминания версии в backend-конфигах и Android metadata (`ANDROID_VERSION_NAME=8.58.10`, `ANDROID_VERSION_CODE=681`).
- EN: SemVer patch bump to `8.58.10`; synchronized explicit version mentions in backend configs and Android metadata (`ANDROID_VERSION_NAME=8.58.10`, `ANDROID_VERSION_CODE=681`).

## 8.58.9 - 2026-05-07
- RU: Исправлен источник времени автозапуска утреннего отчёта: запуск сбора данных в цикле мониторинга теперь явно привязан к настройкам из Telegram-меню «Настройки → Временные настройки → Время сбора данных» (ключи `DATA_COLLECTION_TIMES`/`DATA_COLLECTION_TIME` из БД настроек).
- EN: Fixed morning report auto-run time source: data collection start in monitoring loop is now explicitly tied to Telegram menu settings “Settings → Time settings → Data collection time” (settings DB keys `DATA_COLLECTION_TIMES`/`DATA_COLLECTION_TIME`).
- RU: Добавлено server-visible логирование старта сбора данных для утреннего отчёта (`[MORNING_REPORT_COLLECTION] start`) с временем триггера, итоговым расписанием и источником значения, чтобы это было видно через `journalctl -u server-monitor.service -f`.
- EN: Added server-visible logging for morning report collection start (`[MORNING_REPORT_COLLECTION] start`) with trigger time, resolved schedule, and value source, so it is visible via `journalctl -u server-monitor.service -f`.
- RU: SemVer patch bump до `8.58.9`; синхронизированы явные упоминания версии в backend-конфигах и Android metadata (`ANDROID_VERSION_NAME=8.58.9`, `ANDROID_VERSION_CODE=680`).
- EN: SemVer patch bump to `8.58.9`; synchronized explicit version mentions in backend configs and Android metadata (`ANDROID_VERSION_NAME=8.58.9`, `ANDROID_VERSION_CODE=680`).
- RU: Досинхронизированы оставшиеся упоминания `8.58.7` в runtime-заголовках Python-модулей, Android `MainViewModel` и документации (`README.md`, `docs/android_mobile_app.md`, `docs/api_202020_project.md`) до текущей версии `8.58.9`.
- EN: Synchronized remaining `8.58.7` mentions in Python module runtime headers, Android `MainViewModel`, and documentation files (`README.md`, `docs/android_mobile_app.md`, `docs/api_202020_project.md`) to the current version `8.58.9`.

## [8.58.7] - 2026-05-06
- EN: Updated Android application icons and synchronized related Android assets.
- RU: Обновлены иконки Android-приложения и синхронизированы связанные Android-ресурсы.
- EN: SemVer patch bump to `8.58.7`; synchronized explicit project version mentions across source/config/docs and updated Android metadata to `ANDROID_VERSION_NAME=8.58.7` and `ANDROID_VERSION_CODE=678`.
- RU: Выполнен SemVer patch-бамп до `8.58.7`; синхронизированы явные упоминания версии проекта в исходниках/конфигах/доках и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.58.7` и `ANDROID_VERSION_CODE=678`.
## [8.58.4] - 2026-05-05
- EN: SemVer patch bump to `8.58.4`; synchronized current project-version mentions across runtime headers, backend config constants, and Android client metadata files.
- RU: Выполнен SemVer patch-бамп до `8.58.4`; синхронизированы актуальные упоминания версии проекта в runtime-заголовках, backend-константах конфигурации и Android-метаданных.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.58.4` and `ANDROID_VERSION_CODE=676`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.58.4` и `ANDROID_VERSION_CODE=676`.

## [8.58.3] - 2026-05-05
- EN: Follow-up patch to fully synchronize current version mentions after review feedback; bumped runtime headers and app version constants to `8.58.3`.
- RU: Дополнительный patch-фикс по замечанию ревью: полностью синхронизированы актуальные упоминания версии, runtime-заголовки и константы версии приложения обновлены до `8.58.3`.
- EN: SemVer patch bump to `8.58.3`.
- RU: Выполнен SemVer patch-бамп до `8.58.3`.

## [8.58.2] - 2026-05-05
- EN: Fixed morning-report scheduler window: trigger now uses a dynamic interval from settings (`CHECK_INTERVAL`) so the report is not skipped when loop timing drifts past the exact minute.
- RU: Исправлено окно запуска планировщика утреннего отчёта: триггер теперь учитывает динамический интервал из настроек (`CHECK_INTERVAL`), поэтому отчёт не пропускается при сдвиге цикла мимо точной минуты.
- EN: Monitor loop sleep now also uses live `CHECK_INTERVAL` from DB settings, so runtime changes apply without restart and stay consistent with scheduler checks.
- RU: Пауза основного цикла мониторинга теперь тоже берётся из актуального `CHECK_INTERVAL` в БД, поэтому изменения применяются без рестарта и синхронизируются с проверкой расписания.
- EN: SemVer patch bump to `8.58.2`; synchronized explicit version mentions in updated runtime/config files.
- RU: Выполнен SemVer patch-бамп до `8.58.2`; синхронизированы явные упоминания версии в обновлённых runtime/config-файлах.

## [8.58.1] - 2026-05-05
- EN: SemVer patch bump to `8.58.1`; synchronized explicit version mentions across backend, Android config, and documentation files.
- RU: Выполнен SemVer patch-бамп до `8.58.1`; синхронизированы явные упоминания версии в backend, Android-конфигурации и документации.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.58.1` and `ANDROID_VERSION_CODE=675`; prerelease APK links aligned to `v8.58.1-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.58.1` и `ANDROID_VERSION_CODE=675`; ссылки на prerelease APK выровнены на `v8.58.1-develop`.

## [8.58.0] - 2026-05-05

- EN: Added support for multiple morning-report schedule points via settings (`DATA_COLLECTION_TIMES`), allowing comma-separated `HH:MM` values instead of a single daily time.
- RU: Добавлена поддержка нескольких точек расписания утреннего отчёта через настройки (`DATA_COLLECTION_TIMES`): теперь можно указывать список `HH:MM` через запятую вместо одного времени в сутки.
- EN: Updated scheduler logic to trigger once per configured slot per day and keep backward compatibility with legacy `DATA_COLLECTION_TIME`.
- RU: Обновлена логика планировщика: запуск выполняется один раз на каждый настроенный слот в день с сохранением обратной совместимости с `DATA_COLLECTION_TIME`.
- EN: SemVer minor bump to `8.58.0`; synchronized explicit version mentions in updated backend files.
- RU: Выполнен SemVer minor-бамп до `8.58.0`; синхронизированы явные упоминания версии в обновлённых backend-файлах.

## [8.57.3] - 2026-05-04

- EN: SemVer patch bump to `8.57.3`; synchronized explicit current-version mentions across project files where version is documented.
- RU: Выполнен SemVer patch-бамп до `8.57.3`; синхронизированы явные упоминания текущей версии во всех файлах, где она зафиксирована.
- EN: Updated prerelease Android APK links in documentation to `v8.57.3-develop` and `monitoring-android-8.57.3-develop-debug.apk`.
- RU: Обновлены ссылки на Android prerelease APK в документации до `v8.57.3-develop` и `monitoring-android-8.57.3-develop-debug.apk`.

## [8.57.2] - 2026-05-04

- EN: Fixed morning report scheduler to trigger strictly inside the configured `HH:MM` minute window and to reuse unified send pipeline with success/failure handling.
- RU: Исправлен планировщик утреннего отчёта: запуск теперь происходит строго в минутном окне `HH:MM` из настроек и использует единый пайплайн отправки с контролем успешности.
- EN: Added explicit schedule diagnostics for missed windows after restarts (`[MORNING_REPORT_SCHEDULE] waiting_next_day`) and delivery failures (`send_failed`) to simplify `journalctl -u server-monitor.service -f` debugging.
- RU: Добавлена явная диагностика расписания при пропуске окна после рестартов (`[MORNING_REPORT_SCHEDULE] waiting_next_day`) и при неуспешной отправке (`send_failed`) для удобной отладки в `journalctl -u server-monitor.service -f`.
- EN: SemVer patch bump to `8.57.2`; synchronized current version mentions across project files and docs.
- RU: Выполнен SemVer patch-бамп до `8.57.2`; синхронизированы актуальные упоминания версии в файлах проекта и документации.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.57.2` and `ANDROID_VERSION_CODE=674`; prerelease APK links aligned to `v8.57.2-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.57.2` и `ANDROID_VERSION_CODE=674`; ссылки на prerelease APK выровнены на `v8.57.2-develop`.

## [8.56.99] - 2026-05-01

- EN: SemVer patch bump to `8.56.99`; synchronized current project-version mentions across source, config, docs, and scripts.
- RU: Выполнен SemVer patch-бамп до `8.56.99`; синхронизированы актуальные упоминания версии проекта в исходниках, конфиге, документации и скриптах.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.99` and `ANDROID_VERSION_CODE=671`; prerelease APK links aligned to `v8.56.99-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.99` и `ANDROID_VERSION_CODE=671`; ссылки на prerelease APK выровнены на `v8.56.99-develop`.

## [8.56.98] - 2026-05-01

- EN: SemVer patch bump to `8.56.98`; synchronized explicit current-version mentions across project files.
- RU: Выполнен SemVer patch-бамп до `8.56.98`; синхронизированы явные упоминания текущей версии во всех файлах проекта.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.98` and `ANDROID_VERSION_CODE=670`; prerelease APK links aligned to `v8.56.98-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.98` и `ANDROID_VERSION_CODE=670`; ссылки на prerelease APK выровнены на `v8.56.98-develop`.

## [8.56.97] - 2026-05-01

- EN: SemVer patch bump to `8.56.97`; synchronized explicit current-version mentions across project files.
- RU: Выполнен SemVer patch-бамп до `8.56.97`; синхронизированы явные упоминания текущей версии во всех файлах проекта.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.97` and `ANDROID_VERSION_CODE=669`; prerelease APK links aligned to `v8.56.97-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.97` и `ANDROID_VERSION_CODE=669`; ссылки на prerelease APK выровнены на `v8.56.97-develop`.

## [8.56.96] - 2026-05-01

- EN: Fixed scheduled morning report delivery by not marking a day as sent when Telegram delivery fails; report now retries automatically on next monitoring loop tick.
- RU: Исправлена отправка утреннего отчёта по расписанию: день больше не помечается как отправленный при неуспешной доставке в Telegram; добавлен автоповтор на следующем тике цикла мониторинга.
- EN: Expanded diagnostics for schedule and delivery pipeline (`send_morning_report` / `send_alert`), including planned time, report length, recipient count, and per-channel result.
- RU: Расширена диагностика цепочки расписания и доставки (`send_morning_report` / `send_alert`): добавлены логи планового времени, длины отчёта, числа получателей и результата канала доставки.

## [8.56.95] - 2026-05-01

### Changed
- EN: Fixed parsing of `DATA_COLLECTION_TIME` when value is stored as `HH:MM:SS` (or contains extra time parts): scheduler now correctly takes hours/minutes instead of silently falling back to defaults.
- RU: Исправлен парсинг `DATA_COLLECTION_TIME`, когда значение хранится как `HH:MM:SS` (или содержит лишние части времени): планировщик теперь корректно берёт часы/минуты и не откатывается молча к дефолту.
- EN: Added safer normalization for runtime collection-time parsing in morning report module and database-backed settings loader.
- RU: Добавлена более безопасная нормализация парсинга времени сбора в модуле утреннего отчёта и в загрузчике настроек из БД.
- EN: Added explicit schedule-run log line for morning report with Telegram menu path (`Main menu → Settings → Time settings → Data collection time`) to verify launches in `journalctl -u server-monitor.service -f`.
- RU: Добавлен явный лог запуска утреннего отчёта по расписанию с указанием пути меню Telegram (`Главное меню → Настройки → Временные настройки → Время сбора данных`) для проверки в `journalctl -u server-monitor.service -f`.
- EN: SemVer patch bump to `8.56.95`; synchronized explicit current-version mentions across project files.
- RU: Выполнен SemVer patch-бамп до `8.56.95`; синхронизированы явные упоминания текущей версии во всех файлах проекта.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.95` and `ANDROID_VERSION_CODE=668`; prerelease APK links aligned to `v8.56.95-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.95` и `ANDROID_VERSION_CODE=668`; ссылки на prerelease APK выровнены на `v8.56.95-develop`.

## [8.56.88] - 2026-05-01
- EN: Fixed morning report scheduling after changing `DATA_COLLECTION_TIME` in Telegram settings: the monitor now reads runtime-configured collection time on each check instead of relying on stale startup constants.
- RU: Исправлено расписание утреннего отчёта после изменения `DATA_COLLECTION_TIME` в настройках Telegram: монитор теперь на каждой проверке читает актуальное время из runtime-настроек, а не использует устаревшую константу со старта.
- EN: Added explicit startup-trigger logs for automatic morning report run (current time + planned time) so launch can be verified via `journalctl -u server-monitor.service -f`.
- RU: Добавлен явный лог-триггер автозапуска утреннего отчёта (текущее время + плановое время), чтобы запуск можно было проверить через `journalctl -u server-monitor.service -f`.
- EN: SemVer patch bump to `8.56.88`; Android metadata updated to `ANDROID_VERSION_NAME=8.56.88` and `ANDROID_VERSION_CODE=662`.
- RU: Выполнен SemVer patch-бамп до `8.56.88`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.88` и `ANDROID_VERSION_CODE=662`.

## [8.56.87] - 2026-05-01

- EN: Fixed Telegram time input validation for `DATA_COLLECTION_TIME`: the bot now enforces valid `HH:MM` ranges and normalizes saved values, preventing fallback to default schedule when invalid times were entered.
- RU: Исправлена валидация ввода времени `DATA_COLLECTION_TIME` в Telegram: бот теперь проверяет диапазон `HH:MM` и сохраняет нормализованное значение, чтобы отчёт не откатывался к дефолтному расписанию при некорректном времени.
- EN: SemVer patch bump to `8.56.87`; synchronized explicit current-version mentions across project files and updated Android metadata to `ANDROID_VERSION_NAME=8.56.87` and `ANDROID_VERSION_CODE=661`.
- RU: Выполнен SemVer patch-бамп до `8.56.87`; синхронизированы явные упоминания текущей версии во всех файлах проекта и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.87` и `ANDROID_VERSION_CODE=661`.

## [8.56.85] - 2026-05-01

- EN: Fixed Telegram time-setting input flow: `SILENT_START` and `SILENT_END` now accept both hour-only (`21`) and `HH:MM` format (`21:00`) without `invalid literal for int()` errors.
- RU: Исправлен ввод временных настроек в Telegram: `SILENT_START` и `SILENT_END` теперь принимают как только час (`21`), так и формат `HH:MM` (`21:00`) без ошибки `invalid literal for int()`.
- EN: Fixed persistence key mapping for data collection time: `data_collection` updates now save into `DATA_COLLECTION_TIME`, so runtime schedule actually changes after successful update.
- RU: Исправлено сопоставление ключа сохранения времени сбора данных: `data_collection` теперь сохраняется в `DATA_COLLECTION_TIME`, поэтому расписание реально меняется после успешного обновления.
- EN: Morning and manual monitoring reports now include ZFS pool free-space summary and snapshot-transfer summary for the last 24 hours.
- RU: В утренний и ручной отчёты мониторинга добавлены сводки по свободному месту ZFS-пулов и передачам снэпшотов за последние 24 часа.
- EN: Snapshot-transfer Telegram screen now includes a dedicated "Latest parsed emails" section with recent records from `snapshot_transfers` (host, status, timestamp), making successful parsing visible immediately after mail processing.
- RU: Экран Telegram «Передачи снэпшотов» теперь содержит отдельный блок «Последние распарсенные письма» с недавними записями из `snapshot_transfers` (хост, статус, время), чтобы результат разбора писем был виден сразу после обработки почты.
- EN: Hardened snapshot-transfer parsing in `mail_monitor`: subject whitespace is normalized before regex matching, and successful matches now log whether a custom pattern or fallback pattern was used.
- RU: Усилен парсинг snapshot-transfer в `mail_monitor`: перед regex-сопоставлением нормализуются пробелы в теме письма, а при успехе теперь логируется, сработал пользовательский паттерн или fallback.
- EN: Snapshot transfer menu in Telegram now shows parsed results per host (latest status from `snapshot_transfers`) alongside configured start time.
- RU: В Telegram-меню передач снэпшотов теперь показываются распарсенные результаты по каждому хосту (последний статус из `snapshot_transfers`) вместе с настроенным временем старта.
- EN: Fixed Telegram runtime error in snapshot-transfer settings: replaced undefined `_escape_markdown` with valid `escape_markdown`, so the menu renders subject patterns and hosts without crashing.
- RU: Исправлена runtime-ошибка Telegram в настройках передач снэпшотов: неопределённый `_escape_markdown` заменён на корректный `escape_markdown`, поэтому меню снова отображает subject-паттерны и хосты без падения.
- EN: SemVer patch bump to `8.56.85`; synchronized explicit current-version mentions across project files and updated Android metadata to `ANDROID_VERSION_NAME=8.56.85` and `ANDROID_VERSION_CODE=658`.
- RU: Выполнен SemVer patch-бамп до `8.56.85`; синхронизированы явные упоминания текущей версии во всех файлах проекта и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.85` и `ANDROID_VERSION_CODE=658`.
- EN: Fixed Telegram snapshot-transfer settings crash by importing `BACKUP_DB_FILE` and replacing undefined `logger` usage with `debug_logger` in error handling.
- RU: Исправлено падение Telegram в настройках передач снэпшотов: добавлен импорт `BACKUP_DB_FILE`, а в обработке ошибок неопределённый `logger` заменён на `debug_logger`.
- EN: Snapshot transfer subject patterns now normalize escaped wildcard fragments (for example, `snapshots.\*transfer.\*STARTED`) and whitespace, so emails like `snapshots transfer pve-rubicon STARTED/SUCCESS` are matched reliably.
- RU: Паттерны темы для передач снэпшотов теперь нормализуют экранированные wildcard-фрагменты (например, `snapshots.\*transfer.\*STARTED`) и пробелы, поэтому письма вида `snapshots transfer pve-rubicon STARTED/SUCCESS` стабильно распознаются.

## [8.56.68] - 2026-04-30
- EN: Fixed snapshot-transfer parsing fallback in mail monitor: if user-defined patterns miss a valid subject, parser now retries with built-in generic pattern `snapshots transfer <host> <status>` and no longer drops valid `STARTED` notifications.
- RU: Исправлен fallback парсинга snapshot-transfer в mail monitor: если пользовательские паттерны не совпали с валидной темой, парсер повторяет проверку встроенным универсальным паттерном `snapshots transfer <host> <status>` и больше не теряет валидные уведомления `STARTED`.
- EN: SemVer patch bump to `8.56.68`; synchronized project version mentions and Android metadata updated to `ANDROID_VERSION_NAME=8.56.68` and `ANDROID_VERSION_CODE=643`.
- RU: Выполнен SemVer patch-бамп до `8.56.68`; синхронизированы упоминания версии в проекте и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.68` и `ANDROID_VERSION_CODE=643`.

## [8.56.67] - 2026-04-30
- EN: Clarified mail monitor skip log text to explicitly include snapshot transfers (`передачи снэпшотов`) in the checked categories, reducing confusion when unrelated emails are skipped after snapshot-transfer parsing attempts.
- RU: Уточнён текст skip-лога mail monitor: в список проверяемых категорий явно добавлены передачи снэпшотов (`передачи снэпшотов`), чтобы убрать путаницу при пропуске нерелевантных писем после попытки snapshot-transfer парсинга.
- EN: SemVer patch bump to `8.56.67`; synchronized project version mentions and Android metadata updated to `ANDROID_VERSION_NAME=8.56.67` and `ANDROID_VERSION_CODE=642`.
- RU: Выполнен SemVer patch-бамп до `8.56.67`; синхронизированы упоминания версии в проекте и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.67` и `ANDROID_VERSION_CODE=642`.

## [8.56.66] - 2026-04-30

- EN: SemVer patch bump to `8.56.66`; synchronized explicit current-version mentions across project files to remove version drift.
- RU: Выполнен SemVer patch-бамп до `8.56.66`; синхронизированы явные упоминания текущей версии во всех файлах проекта для устранения рассинхрона.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.66` and `ANDROID_VERSION_CODE=640`; prerelease APK links aligned to `v8.56.66-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.66` и `ANDROID_VERSION_CODE=640`; ссылки на prerelease APK выровнены на `v8.56.66-develop`.

## [8.56.64] - 2026-04-30

- EN: Fixed snapshot-transfer pattern loading in mail monitor when backup patterns are stored as a JSON string; config and fallback patterns are now safely normalized before reading `snapshot_transfer.subject`.
- RU: Исправлена загрузка паттернов snapshot-transfer в mail monitor, когда backup patterns хранятся JSON-строкой; конфигурация и fallback-паттерны теперь безопасно нормализуются перед чтением `snapshot_transfer.subject`.
- EN: This prevents runtime error `'str' object has no attribute 'get'` during processing of subjects like `snapshots transfer <host> STARTED`.
- RU: Это устраняет runtime-ошибку `'str' object has no attribute 'get'` при обработке тем вида `snapshots transfer <host> STARTED`.
- EN: SemVer patch bump to `8.56.64`; synchronized project version mentions and Android metadata updated to `ANDROID_VERSION_NAME=8.56.64` and `ANDROID_VERSION_CODE=639`.
- RU: Выполнен SemVer patch-бамп до `8.56.64`; синхронизированы упоминания версии в проекте и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.64` и `ANDROID_VERSION_CODE=639`.

## [8.56.63] - 2026-04-30

- EN: Mail monitor now parses and stores `snapshots transfer <host> <status>` emails even when the Snapshot Transfer extension is disabled, preventing false "Не удалось обработать письмо" warnings for valid transfer notifications.
- RU: Монитор почты теперь парсит и сохраняет письма вида `snapshots transfer <host> <status>` даже при выключенном расширении Snapshot Transfer, что убирает ложные предупреждения "Не удалось обработать письмо" для валидных уведомлений о передаче.
- EN: Snapshot-transfer parsing now always appends built-in default subject regex patterns to custom `snapshot_transfer.subject` rules from settings, preventing misses when custom rules are too narrow (for example, `SUCCESS`-only).
- RU: Парсинг snapshot-transfer теперь всегда добавляет встроенные дефолтные subject-regex паттерны к кастомным правилам `snapshot_transfer.subject` из настроек, что предотвращает пропуски при слишком узких шаблонах (например, только `SUCCESS`).
- EN: SemVer patch bump to `8.56.63`; synchronized explicit current-version mentions across project files and updated Android metadata to `ANDROID_VERSION_NAME=8.56.63` and `ANDROID_VERSION_CODE=638`.
- RU: Выполнен SemVer patch-бамп до `8.56.63`; синхронизированы явные упоминания текущей версии во всех файлах проекта и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.63` и `ANDROID_VERSION_CODE=638`.

## [8.56.59] - 2026-04-30
- EN: Fixed snapshot-transfer Telegram settings flow: host start-time input no longer leaks into host rename and pattern-add flows; conflicting snapshot host input states are reset before entering each action.
- RU: Исправлен поток Telegram-настроек передач снэпшотов: ввод времени старта больше не перехватывает переименование хоста и добавление паттерна; конфликтующие состояния ввода сбрасываются перед запуском каждого действия.
- EN: SemVer patch bump to `8.56.59`; synchronized current version mentions and Android metadata updated to `ANDROID_VERSION_NAME=8.56.59` and `ANDROID_VERSION_CODE=634`.
- RU: Выполнен SemVer patch-бамп до `8.56.59`; синхронизированы упоминания текущей версии и обновлены Android-метаданные до `ANDROID_VERSION_NAME=8.56.59` и `ANDROID_VERSION_CODE=634`.

## [8.56.58] - 2026-04-30

- EN: Snapshot Transfer settings menu updated: removed global start-time item and removed back button from the Snapshot Transfer patterns screen.
- RU: Обновлено меню «Передачи снэпшотов»: убран общий пункт времени старта и удалена кнопка «Назад» на экране паттернов передачи.
- EN: Snapshot Transfer hosts screen now shows host list and management buttons (edit, enable/disable, delete, per-host start time).
- RU: Экран хостов передач снэпшотов теперь показывает список хостов и кнопки управления (редактирование, вкл/выкл, удаление, индивидуальное время старта).
- EN: Fixed non-working “Add pattern” button for Snapshot Transfer patterns by adding callback routing.
- RU: Исправлена неработающая кнопка «Добавить паттерн» в паттернах передач снэпшотов за счёт корректной маршрутизации callback.
- EN: Removed “📸 Snapshot Transfers” entry from Settings → Extensions section.
- RU: Удалена кнопка «📸 Передачи снэпшотов» из раздела «Настройки → Расширения».

- EN: SemVer patch bump to `8.56.58`; synchronized explicit current-version mentions across project files; Android metadata updated to `ANDROID_VERSION_NAME=8.56.58` and `ANDROID_VERSION_CODE=633`.
- RU: Выполнен SemVer patch-бамп до `8.56.58`; синхронизированы явные упоминания текущей версии во всех файлах проекта; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.58` и `ANDROID_VERSION_CODE=633`.

## [8.56.54] - 2026-04-30

- EN: Added full Telegram settings flow for `📸 Snapshot Transfers`: from main menu it now opens dedicated snapshot-transfer settings with direct actions for hosts, patterns, and start time.
- RU: Добавлен полноценный сценарий настроек Telegram для `📸 Передачи снэпшотов`: из главного меню теперь открывается отдельный экран настроек передачи снэпшотов с прямыми действиями для хостов, паттернов и времени старта.
- EN: Added snapshot-transfer section to Settings → Extensions for faster access to related configuration.
- RU: Добавлен раздел передачи снэпшотов в Настройки → Расширения для быстрого доступа к связанным параметрам.
- EN: SemVer patch bump to `8.56.54`; synchronized explicit version mentions and Android metadata (`ANDROID_VERSION_NAME=8.56.54`, `ANDROID_VERSION_CODE=629`), prerelease links aligned to `v8.56.54-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.54`; синхронизированы явные упоминания версии и Android-метаданные (`ANDROID_VERSION_NAME=8.56.54`, `ANDROID_VERSION_CODE=629`), prerelease-ссылки выровнены на `v8.56.54-develop`.

## [8.56.53] - 2026-04-30

### Improved / Улучшено
- EN: SemVer patch bump to `8.56.54`; synchronized all explicit current-version mentions across project files (backend, modules, extensions, scripts, docs, and bot handlers).
- RU: Выполнен SemVer patch-бамп до `8.56.54`; синхронизированы все явные упоминания текущей версии во всех файлах проекта (backend, модули, расширения, скрипты, документация и обработчики бота).
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.54` and `ANDROID_VERSION_CODE=629`; prerelease links aligned to `v8.56.54-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.54` и `ANDROID_VERSION_CODE=629`; prerelease-ссылки выровнены на `v8.56.54-develop`.
- EN: In Telegram bot menu `📸 Snapshot Transfers`, opened direct settings menu with required actions: `Hosts`, `Patterns`, and `Start time`.
- RU: В меню Telegram-бота `📸 Передачи снэпшотов` открыто прямое меню настроек с нужными действиями: `Хосты`, `Паттерны` и `Время старта`.
- EN: Removed redundant redirect to Extensions from `📸 Snapshot Transfers`; now users manage snapshot-transfer flow immediately from the snapshot menu.
- RU: Убрана лишняя переадресация в «Расширения» из `📸 Передачи снэпшотов`; теперь управление идёт сразу из меню снэпшотов.

## [8.56.48] - 2026-04-30
- EN: Added snapshot-transfer monitoring for emails with statuses `STARTED`, `SUCCESS`, `SKIPPED`, `ERROR`, `BUSY`; parser now stores transfer details (host, snapshot, method, size, timing, duration) in new DB table `snapshot_transfers`.
- RU: Добавлен мониторинг передачи снэпшотов по письмам со статусами `STARTED`, `SUCCESS`, `SKIPPED`, `ERROR`, `BUSY`; парсер теперь сохраняет детали передачи (хост, снэпшот, метод, размер, время старта/завершения, длительность) в новую таблицу `snapshot_transfers`.
- EN: Added extension toggle `snapshot_transfer_monitor`, default regex patterns `snapshot_transfer.subject`, and default setting `SNAPSHOT_TRANSFER_HOSTS` for host/pool/schedule configuration.
- RU: Добавлен переключатель расширения `snapshot_transfer_monitor`, дефолтные regex-паттерны `snapshot_transfer.subject` и настройка `SNAPSHOT_TRANSFER_HOSTS` для конфигурации хостов/пулов/расписания.

## [8.56.47] - 2026-04-23

### Improved / Улучшено
- EN: In Android Ops Center, the current mode state is now shown directly under the `⚡ Ops Center` title (for example, `Now: quiet mode`).
- RU: В Android Оперативном центре текущее состояние режима теперь показывается сразу под заголовком `⚡ Оперативный центр` (например, `Сейчас: тихий режим`).
- EN: The mode-switch tile now displays only a short status (`auto` / `quiet` / `loud` / `...`) instead of full verbose text.
- RU: Плашка-переключатель режима теперь показывает только короткий статус (`авто` / `тихо` / `громко` / `...`) вместо длинного текста.
- EN: SemVer patch bump to `8.56.47`; synchronized explicit current-version mentions across project files and Android metadata (`ANDROID_VERSION_CODE=625`).
- RU: Выполнен SemVer patch-бамп до `8.56.47`; синхронизированы явные упоминания текущей версии в файлах проекта и Android-метаданные (`ANDROID_VERSION_CODE=625`).

## [8.56.45] - 2026-04-23

### Fixed / Исправлено
- EN: In Android extension tile dialogs, replaced help control rendering with the same textual `?` style used in server/resource tile dialogs for a consistent tap UX.
- RU: В Android-диалогах плашек расширений отображение кнопки справки заменено на такой же текстовый `?`, как в диалогах плашек серверов/ресурсов, чтобы выровнять UX при тапах.
- EN: SemVer patch bump to `8.56.45`; synchronized explicit current-version mentions across project files and Android metadata (`ANDROID_VERSION_CODE=623`).
- RU: Выполнен SemVer patch-бамп до `8.56.45`; синхронизированы явные упоминания текущей версии в файлах проекта и Android-метаданные (`ANDROID_VERSION_CODE=623`).

## [8.56.43] - 2026-04-23

### Improved / Улучшено
- EN: Unified header actions for Android dialogs (`✖`, `?`, `⚙️`, `+`) to a single compact style: all controls now use consistent icon buttons with aligned visuals and spacing.
- RU: Кнопки заголовков Android-диалогов (`✖`, `?`, `⚙️`, `+`) приведены к единому компактному стилю: теперь используется единый тип иконок с выровненной визуалкой и отступами.
- EN: Applied the unified compact actions in tiles/dialogs where these controls are used (`📬`, `🧊`, `💽`, `💾`, `🗃️`), including replacement of textual `?` with a consistent help icon.
- RU: Единый компактный стиль применён в плашках/диалогах, где используются эти действия (`📬`, `🧊`, `💽`, `💾`, `🗃️`), включая замену текстового `?` на стандартную иконку справки.
- EN: SemVer patch bump to `8.56.43`; synchronized explicit current-version mentions across project files and Android metadata (`ANDROID_VERSION_CODE=621`).
- RU: Выполнен SemVer patch-бамп до `8.56.43`; синхронизированы явные упоминания текущей версии в файлах проекта и Android-метаданные (`ANDROID_VERSION_CODE=621`).

## [8.56.42] - 2026-04-23

### Fixed / Исправлено
- EN: Fixed Android Ops Center tile `🧊 Статусы ZFS`: host-card tap now requests host details using the host action from menu options, so dialog data is fetched from DB/backend instead of showing only local fallback text.
- RU: Исправлена плашка `🧊 Статусы ZFS` в Android Оперативном центре: тап по карточке хоста теперь отправляет action хоста из menu options и подтягивает данные из БД/backend, а не показывает только локальный fallback-текст.
- EN: SemVer patch bump to `8.56.42`; synchronized explicit current-version mentions across project files and Android metadata (`ANDROID_VERSION_CODE=620`).
- RU: Выполнен SemVer patch-бамп до `8.56.42`; синхронизированы явные упоминания текущей версии в файлах проекта и Android-метаданные (`ANDROID_VERSION_CODE=620`).

## [8.56.41] - 2026-04-23

### Fixed / Исправлено
- EN: Fixed parsing of ZFS status data in Android dialog/cards for the updated backend format (`🖥 *host*` + emoji pool lines). ZFS status cards now correctly render host and pool states instead of showing placeholders.
- RU: Исправлен парсинг данных ZFS в Android-диалоге/плашках под обновлённый формат backend (`🖥 *host*` + строки пулов с emoji). Теперь карточки ZFS корректно показывают хосты и статусы пулов вместо прочерков.
- EN: SemVer patch bump to `8.56.41`; synchronized explicit current-version mentions across project files and Android metadata (`ANDROID_VERSION_CODE=619`).
- RU: Выполнен SemVer patch-бамп до `8.56.41`; синхронизированы явные упоминания текущей версии в файлах проекта и Android-метаданные (`ANDROID_VERSION_CODE=619`).

## [8.56.35] - 2026-04-23

### Fixed / Исправлено
- EN: In Android dialogs for `💾 Бэкапы Proxmox` and `🗃️ Бэкапы БД`, swapped header actions `✖` and `+` (add action is now first, close action moved to the last position in the row).
- RU: В Android-диалогах `💾 Бэкапы Proxmox` и `🗃️ Бэкапы БД` кнопки `✖` и `+` в заголовке поменяны местами (`+` теперь первая, `✖` перенесена в конец ряда).
- EN: SemVer patch bump to `8.56.35`; synchronized explicit current-version mentions across backend modules/config/docs/scripts and Android metadata (`ANDROID_VERSION_CODE=613`).
- RU: Выполнен SemVer patch-бамп до `8.56.35`; синхронизированы явные упоминания текущей версии в backend-модулях/конфигурации/документации/скриптах и Android-метаданные (`ANDROID_VERSION_CODE=613`).

## [8.56.34] - 2026-04-23

### Improved / Улучшено
- EN: In Android dialogs for `💾 Бэкапы Proxmox` and `🗃️ Бэкапы БД`, tap behavior on backup tiles was aligned toward quick actions: Proxmox host cards now open the host action sheet directly on tap.
- RU: В Android-диалогах `💾 Бэкапы Proxmox` и `🗃️ Бэкапы БД` выровнено поведение тапа по плашкам: карточки Proxmox-хостов теперь открывают карточку действий сразу по тапу.
- EN: Removed the background substrate under header controls (`✖`, `⚙️`, `?`, `+`) in both dialogs to make icon actions visually cleaner.
- RU: Убрана подложка под кнопками заголовка (`✖`, `⚙️`, `?`, `+`) в обоих диалогах, чтобы иконки выглядели чище.
- EN: SemVer patch bump to `8.56.34`; synchronized explicit current-version mentions across backend modules/config/docs/scripts and Android metadata (`ANDROID_VERSION_CODE=612`).
- RU: Выполнен SemVer patch-бамп до `8.56.34`; синхронизированы явные упоминания текущей версии в backend-модулях/конфигурации/документации/скриптах и Android-метаданные (`ANDROID_VERSION_CODE=612`).

## [8.56.31] - 2026-04-22

### Fixed / Исправлено
- EN: SemVer patch bump to `8.56.31`; synchronized explicit current-version mentions across backend modules, config, docs, scripts, and Android client artifacts to eliminate version drift.
- RU: Выполнен SemVer patch-бамп до `8.56.31`; синхронизированы явные упоминания текущей версии в backend-модулях, конфигурации, документации, скриптах и Android-артефактах для устранения рассинхрона версии.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.31` and `ANDROID_VERSION_CODE=609`; prerelease links aligned to `v8.56.31-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.31` и `ANDROID_VERSION_CODE=609`; prerelease-ссылки выровнены на `v8.56.31-develop`.

## [8.56.30] - 2026-04-22

### Improved / Улучшено
- EN: In Android dialogs for `💾 Бэкапы Proxmox` and `🗃️ Бэкапы БД`, header controls (`✖`, `⚙️`, `?`, `+`) were regrouped into a compact horizontal action cluster with subtle background and tighter spacing, making the layout visually cleaner and more consistent with Material UI.
- RU: В Android-диалогах `💾 Бэкапы Proxmox` и `🗃️ Бэкапы БД` кнопки заголовка (`✖`, `⚙️`, `?`, `+`) перегруппированы в компактный горизонтальный блок с мягкой подложкой и аккуратными отступами — интерфейс стал визуально чище и гармоничнее в стиле Material UI.
- EN: SemVer patch bump to `8.56.30`; Android metadata updated to `ANDROID_VERSION_NAME=8.56.30` and `ANDROID_VERSION_CODE=608`.
- RU: Выполнен SemVer patch-бамп до `8.56.30`; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.30` и `ANDROID_VERSION_CODE=608`.

## [8.56.29] - 2026-04-21

### Fixed / Исправлено
- EN: In Android dialogs opened from tiles `💾 Бэкапы Proxmox`, `🗃️ Бэкапы БД`, `📬 Почта`, and `🧊 zfs статусы`, header action buttons are now arranged vertically in the exact order: close (`✖`), help (`?`), settings (`⚙️`), add (`+`).
- RU: В Android-диалогах, открываемых из плашек `💾 Бэкапы Proxmox`, `🗃️ Бэкапы БД`, `📬 Почта` и `🧊 zfs статусы`, кнопки в заголовке теперь расположены вертикально и в точном порядке: закрыть (`✖`), справка (`?`), настройки (`⚙️`), добавить (`+`).
- EN: For the `📬 Почта` tile dialog, added a dedicated `+` action in the header to open mail-pattern creation directly.
- RU: Для диалога плашки `📬 Почта` добавлено отдельное действие `+` в заголовке для прямого открытия создания нового паттерна почты.
- EN: SemVer patch bump to `8.56.29`; synchronized explicit current-version mentions across backend modules, config, docs, scripts, and Android artifacts. Android metadata updated to `ANDROID_VERSION_NAME=8.56.29` and `ANDROID_VERSION_CODE=607`.
- RU: Выполнен SemVer patch-бамп до `8.56.29`; синхронизированы явные упоминания текущей версии в backend-модулях, конфигурации, документации, скриптах и Android-артефактах. Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.29` и `ANDROID_VERSION_CODE=607`.

## [8.56.28] - 2026-04-21

### Fixed / Исправлено
- EN: Added a contextual `?` help button near the close icon in each key Android Ops tile dialog (servers/resources, mail backups, ZFS statuses, ZFS free space, Proxmox backups, DB backups) with in-app explanations of purpose, behavior, and setup flow.
- RU: Добавлена контекстная кнопка `?` рядом с крестиком закрытия в ключевых Android-диалогах плашек оперативного центра (серверы/ресурсы, бэкапы почты, статусы ZFS, свободное место ZFS, бэкапы Proxmox, бэкапы БД) с пояснениями: за что отвечает плашка, что в ней происходит и как её настраивать.
- EN: SemVer patch bump to `8.56.28`; synchronized all explicit current-version mentions across backend modules, config, docs, scripts, and Android client artifacts to remove version drift.
- RU: Выполнен SemVer patch-бамп до `8.56.28`; синхронизированы все явные упоминания текущей версии в backend-модулях, конфигурации, документации, скриптах и Android-артефактах, чтобы убрать рассинхрон версии.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.28` and `ANDROID_VERSION_CODE=606`; prerelease links aligned to `v8.56.28-develop`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.28` и `ANDROID_VERSION_CODE=606`; prerelease-ссылки выровнены на `v8.56.28-develop`.

## [8.56.25] - 2026-04-21

### Fixed / Исправлено
- EN: Fixed Kotlin syntax in Android `MainActivity`: replaced a stray closing brace with the missing `)` to correctly close the settings `AlertDialog(...)` call, restoring valid Compose scope and removing the cascade of `@Composable invocations can only happen...` errors during `:app:compileCompactOpsDebugKotlin`.
- RU: Исправлен синтаксис Kotlin в Android `MainActivity`: лишняя закрывающая фигурная скобка заменена на недостающую `)` для корректного закрытия вызова `AlertDialog(...)` в настройках, что восстановило корректный Compose-scope и убрало каскад ошибок `@Composable invocations can only happen...` на `:app:compileCompactOpsDebugKotlin`.
- EN: SemVer patch bump to `8.56.25`; synchronized explicit version mentions across project files and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.25` and `ANDROID_VERSION_CODE=603`; prerelease links aligned to `v8.56.25-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.25`; синхронизированы явные упоминания версии в файлах проекта и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.25` и `ANDROID_VERSION_CODE=603`; prerelease-ссылки выровнены на `v8.56.25-develop`.

## [8.56.22] - 2026-04-21

### Fixed / Исправлено
- EN: Fixed Kotlin syntax in Android `MainActivity`: removed an extra closing parenthesis in the ZFS host settings dialog block, restoring valid Compose scope and removing the cascade of `@Composable invocations can only happen...` build errors.
- RU: Исправлена синтаксическая ошибка Kotlin в Android `MainActivity`: удалена лишняя закрывающая скобка в блоке диалога настроек ZFS-хостов, что восстановило корректный Compose-scope и убрало каскад ошибок сборки `@Composable invocations can only happen...`.
- EN: SemVer patch bump to `8.56.22`; synchronized explicit version mentions across project files and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.22` and `ANDROID_VERSION_CODE=600`; prerelease links aligned to `v8.56.22-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.22`; синхронизированы явные упоминания версии в файлах проекта и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.22` и `ANDROID_VERSION_CODE=600`; prerelease-ссылки выровнены на `v8.56.22-develop`.

## [8.56.20] - 2026-04-20

### Fixed / Исправлено
- EN: In Android flow `💽 zfs место` → gear (`⚙️ Хосты свободного места ZFS`), added a color status marker on each host card: green for enabled host monitoring, red for disabled.
- RU: В Android-сценарии `💽 zfs место` → шестерёнка (`⚙️ Хосты свободного места ZFS`) на каждую карточку хоста добавлен цветовой маркер состояния: зелёный для включенного мониторинга хоста, красный для выключенного.
- EN: SemVer patch bump to `8.56.20`; synchronized explicit version mentions across project files and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.20` and `ANDROID_VERSION_CODE=598`; prerelease links aligned to `v8.56.20-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.20`; синхронизированы явные упоминания версии в файлах проекта и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.20` и `ANDROID_VERSION_CODE=598`; prerelease-ссылки выровнены на `v8.56.20-develop`.

## [8.56.17] - 2026-04-20

### Fixed / Исправлено
- EN: In Android `zfs место` (`💽 Free space of ZFS pools`), removed the `+` button from the main free-space dialog header; host creation is now available only in host settings opened via the gear icon.
- RU: В Android `zfs место` (`💽 Свободное место ZFS пулов`) убрана кнопка `+` из заголовка основного окна свободного места; добавление хоста теперь доступно только в настройках, открываемых по шестерёнке.
- EN: In Android host settings for ZFS pool free-space (`⚙️ Хосты свободного места ZFS`), arranged close (`✖`) and add (`+`) actions vertically in the dialog header.
- RU: В Android-настройках хостов свободного места ZFS (`⚙️ Хосты свободного места ZFS`) действия закрытия (`✖`) и добавления (`+`) расположены вертикально в заголовке диалога.
- EN: In the same host settings dialog, removed body buttons labeled `Добавить хост` and `Назад`; host add remains in the header `+`, while navigation back is handled by closing the dialog.
- RU: В том же диалоге настроек хостов удалены кнопки в теле с надписями `Добавить хост` и `Назад`; добавление хоста остаётся в `+` заголовка, возврат выполняется через закрытие диалога.
- EN: SemVer patch bump to `8.56.17`; synchronized explicit version mentions across project files and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.17` and `ANDROID_VERSION_CODE=595`; prerelease links aligned to `v8.56.17-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.17`; синхронизированы явные упоминания версии в файлах проекта и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.17` и `ANDROID_VERSION_CODE=595`; prerelease-ссылки выровнены на `v8.56.17-develop`.

## [8.56.16] - 2026-04-20

### Fixed / Исправлено
- EN: Fixed Android flow `zfs место` → gear (`⚙️ Хосты свободного места ZFS`): host add dialog now closes the free-space screen first, so no extra underlying window appears during host creation.
- RU: Исправлен Android-сценарий `zfs место` → шестерёнка (`⚙️ Хосты свободного места ZFS`): диалог добавления хоста теперь сначала закрывает экран свободного места, поэтому при создании хоста не появляется лишнее окно под формой добавления.
- EN: SemVer patch bump to `8.56.16`; synchronized explicit version mentions across project files and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.16` and `ANDROID_VERSION_CODE=594`; prerelease links aligned to `v8.56.16-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.16`; синхронизированы явные упоминания версии в файлах проекта и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.16` и `ANDROID_VERSION_CODE=594`; prerelease-ссылки выровнены на `v8.56.16-develop`.

## [8.56.11] - 2026-04-20

### Changed / Изменено
- EN: SemVer patch bump to `8.56.11`; synchronized project version mentions across backend headers/config, Android client constants, and docs prerelease links.
- RU: Выполнен SemVer patch-бамп до `8.56.11`; синхронизированы упоминания версии проекта в заголовках/конфигах backend, константах Android-клиента и prerelease-ссылках в документации.
- EN: Android metadata updated to `ANDROID_VERSION_NAME=8.56.11` and `ANDROID_VERSION_CODE=589`.
- RU: Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.11` и `ANDROID_VERSION_CODE=589`.

## [8.56.10] - 2026-04-20

### Fixed / Исправлено
- EN: Fixed compact-ops tile `zfs статусы`: added dedicated tile gear action that opens the ZFS settings chooser (hosts/patterns) directly from the tile.
- RU: Исправлена compact-ops плашка `zfs статусы`: добавлено отдельное действие по шестерёнке плашки для прямого открытия выбора настроек ZFS (хосты/паттерны).
- EN: In Android flow `zfs место` → gear (`⚙️ Хосты свободного места ZFS`), added explicit `+` icon in the dialog header to open host creation immediately using current backend `zfsp_add*` action.
- RU: В Android-сценарии `zfs место` → шестерёнка (`⚙️ Хосты свободного места ZFS`) добавлена явная иконка `+` в заголовок диалога для мгновенного открытия добавления хоста через актуальное backend-действие `zfsp_add*`.
- EN: SemVer patch bump to `8.56.10`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.10` and `ANDROID_VERSION_CODE=588`; prerelease links aligned to `v8.56.10-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.10`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.10` и `ANDROID_VERSION_CODE=588`; prerelease-ссылки выровнены на `v8.56.10-develop`.

## [8.56.9] - 2026-04-20

### Fixed / Исправлено
- EN: Fixed Android compact-ops tiles so `zfs статусы`, `поставщики`, and `zfs место` again show calculated summaries instead of fallback dashes when backend IDs use legacy aliases.
- RU: Исправлены Android-плашки compact-ops: `zfs статусы`, `поставщики` и `zfs место` снова показывают расчётные сводки вместо прочерков при legacy-алиасах ID на backend.
- EN: Fixed tap routing for tile `поставщики`: tap now opens supplier reports action (`supplier_stock_reports`) and no longer routes into ZFS free-space host settings flow.
- RU: Исправлена маршрутизация тапа по плашке `поставщики`: тап теперь открывает отчёты поставщиков (`supplier_stock_reports`) и больше не уводит в поток настроек хостов ZFS-свободного места.
- EN: SemVer patch bump to `8.56.9`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.9` and `ANDROID_VERSION_CODE=587`; prerelease links aligned to `v8.56.9-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.9`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.9` и `ANDROID_VERSION_CODE=587`; prerelease-ссылки выровнены на `v8.56.9-develop`.

## [8.56.5] - 2026-04-20

- EN: Fixed Android ZFS pool free-space host management: add/edit actions now send plain values from dialog payloads, and backend `zfsp_*` handlers decode URL-encoded payload parts for compatibility before validation/saving.
- RU: Исправлено управление хостами свободного места ZFS-пулов в Android: действия добавления/редактирования теперь отправляют из диалога обычные значения, а backend-обработчики `zfsp_*` декодируют URL-кодированные части payload перед валидацией и сохранением.
- EN: SemVer patch bump to `8.56.5`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.5` and `ANDROID_VERSION_CODE=583`; prerelease links aligned to `v8.56.5-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.5`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.5` и `ANDROID_VERSION_CODE=583`; prerelease-ссылки выровнены на `v8.56.5-develop`.

## [8.56.4] - 2026-04-20

### Fixed / Исправлено
- EN: In Android flow `zfs место` → `💽 Free space of ZFS pools` → gear, tapping `+` now always opens new-host creation with payload based on the current backend add action (`zfsp_add*`), then submits host name, IP, and threshold.
- RU: В Android-сценарии `zfs место` → `💽 Свободное место ZFS пулов` → шестерёнка, тап по `+` теперь всегда открывает добавление нового хоста с payload на основе актуального backend-действия добавления (`zfsp_add*`), а затем отправляет имя хоста, IP и порог.
- EN: SemVer patch bump to `8.56.4`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.4` and `ANDROID_VERSION_CODE=582`; prerelease links aligned to `v8.56.4-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.4`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.4` и `ANDROID_VERSION_CODE=582`; prerelease-ссылки выровнены на `v8.56.4-develop`.

## [8.56.2] - 2026-04-19

### Fixed / Исправлено
- EN: In Android `💽 Free space of ZFS pools` host settings (tile `zfs место` → gear), removed text buttons labeled `Add host` from the dialog body; host creation is now done via the `+` icon in the dialog header.
- RU: В Android `💽 Свободное место ZFS пулов` в настройках хостов (плашка `zfs место` → шестерёнка) убраны текстовые кнопки с надписью `Добавить хост` из тела диалога; добавление хоста теперь выполняется через кнопку `+` в заголовке диалога.
- EN: In Android `💽 Free space of ZFS pools` host settings (`zfs место` → gear), the `+` button now always opens the add-host form (name, IP, threshold) and no longer stays inactive due to backend menu-state mismatch.
- RU: В Android `💽 Свободное место ZFS пулов` в настройках хостов (`zfs место` → шестерёнка) кнопка `+` теперь всегда открывает форму добавления хоста (имя, IP, порог) и больше не зависает неактивной из-за рассинхрона состояния меню backend.
- EN: SemVer patch bump to `8.56.2`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.2` and `ANDROID_VERSION_CODE=580`; prerelease links aligned to `v8.56.2-develop`.
- RU: Выполнен SemVer patch-бамп до `8.56.2`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.2` и `ANDROID_VERSION_CODE=580`; prerelease-ссылки выровнены на `v8.56.2-develop`.

## [8.56.0] - 2026-04-19

### Changed / Изменено
- EN: In Android `💽 Free space of ZFS pools` (`zfs место`) host settings (tap tile → tap gear), removed the hint text `Tap on a host card...` from the dialog body.
- RU: В Android `💽 Свободное место ZFS пулов` (`zfs место`) в настройках хостов (тап по плашке → тап по шестерёнке) убрана подсказка `Тап по плашке...` из тела диалога.
- EN: Added an explicit `➕ Add host` action inside the host-settings content area (in addition to toolbar actions), matching Telegram bot flow `Main menu → Free space of ZFS pools → Host settings → Add host`.
- RU: Добавлено явное действие `➕ Добавить хост` прямо в области настроек хостов (дополнительно к действиям в тулбаре), что выравнивает поведение с Telegram-ботом по пути `Главное меню → Свободное место ZFS пулов → Настройка хостов → Добавить хост`.
- EN: SemVer minor bump to `8.56.0`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.56.0` and `ANDROID_VERSION_CODE=578`; prerelease links aligned to `v8.56.0-develop`.
- RU: Выполнен SemVer minor-бамп до `8.56.0`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.56.0` и `ANDROID_VERSION_CODE=578`; prerelease-ссылки выровнены на `v8.56.0-develop`.

## [8.55.52] - 2026-04-19

### Fixed / Исправлено
- EN: In Android `💽 Free space of ZFS pools` host cards in the settings list now run quick actions on regular tap as well (same behavior as long tap: edit / enable-disable / delete).
- RU: В Android `💽 Свободное место ZFS пулов` плашки хостов в списке настроек теперь по обычному тапу запускают быстрые действия (как и долгий тап: редактировать / вкл-выкл / удалить).
- EN: In Android `💽 Free space of ZFS pools`, after opening host settings by tapping the gear, the `+` action is now always available and opens the add-host parameters form (host name, IP, threshold).
- RU: В Android `💽 Свободное место ZFS пулов` после открытия настроек хостов через шестерёнку действие `+` теперь всегда доступно и открывает форму параметров добавляемого хоста (имя, IP, порог).
- EN: SemVer patch bump to `8.55.52`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.52` and `ANDROID_VERSION_CODE=577`; prerelease links aligned to `v8.55.52-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.52`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.52` и `ANDROID_VERSION_CODE=577`; prerelease-ссылки выровнены на `v8.55.52-develop`.

## [8.55.50] - 2026-04-19

### Fixed / Исправлено
- EN: Android `zfs место` flow in `💽 Free space of ZFS pools` now matches the expected sequence: tap tile → tap gear opens host settings list, and tap `+` opens the add-host form with parameters (host name, IP, threshold).
- RU: В Android-сценарии `zfs место` для `💽 Свободное место ZFS пулов` восстановлена ожидаемая последовательность: тап по плашке → тап по шестерёнке открывает список настроек хостов, а тап по `+` открывает форму добавления с параметрами (имя хоста, IP, порог).
- EN: SemVer patch bump to `8.55.50`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.50` and `ANDROID_VERSION_CODE=575`; prerelease links aligned to `v8.55.50-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.50`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.50` и `ANDROID_VERSION_CODE=575`; prerelease-ссылки выровнены на `v8.55.50-develop`.

## [8.55.49] - 2026-04-19

### Fixed / Исправлено
- EN: Fixed Android `zfs место` host-settings flow in `💽 Free space of ZFS pools`: tapping the `+` action now opens the add-host dialog instead of sending a no-op `zfsp_add` action without payload.
- RU: Исправлен сценарий настроек хостов Android-плашки `zfs место` в `💽 Свободное место ZFS пулов`: тап по действию `+` теперь открывает форму добавления хоста, а не отправляет пустой `zfsp_add` без параметров.
- EN: SemVer patch bump to `8.55.49`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.49` and `ANDROID_VERSION_CODE=574`; prerelease links aligned to `v8.55.49-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.49`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.49` и `ANDROID_VERSION_CODE=574`; prerelease-ссылки выровнены на `v8.55.49-develop`.

## [8.55.48] - 2026-04-19

### Fixed / Исправлено
- EN: In Telegram bot path `Main menu → Free space of ZFS pools → Host settings`, added a `✖️ Close` button in the hosts list screen.
- RU: В Telegram-боте по пути `Главное меню → Свободное место ZFS пулов → Настройка хостов` добавлена кнопка `✖️ Закрыть` на экране списка хостов.
- EN: Android tile `zfs место` tap now opens `💽 Free space of ZFS pools` without auto-opening the host-add form.
- RU: Тап по Android-плашке `zfs место` теперь открывает `💽 Свободное место ZFS пулов` без автоматического открытия формы добавления хоста.
- EN: In `💽 Free space of ZFS pools`, tapping the gear now immediately opens the add-host dialog with host parameters (name, IP, threshold 1–95), while still requesting host settings via `zfsp_hosts_list` in background.
- RU: В `💽 Свободное место ZFS пулов` тап по шестерёнке теперь сразу открывает окно добавления хоста с параметрами (имя, IP, порог 1–95), параллельно запрашивая настройки хостов через `zfsp_hosts_list`.
- EN: Tap on a host card in ZFS pool host settings now opens a dedicated edit form and submits `zfsp_edit_name_*|...`, `zfsp_edit_ip_*|...`, `zfsp_edit_threshold_*|...`; long tap keeps opening quick actions (edit / enable-disable / delete).
- RU: Тап по плашке хоста в настройках ZFS-пулов теперь открывает отдельную форму редактирования и отправляет `zfsp_edit_name_*|...`, `zfsp_edit_ip_*|...`, `zfsp_edit_threshold_*|...`; долгий тап сохраняет быстрые действия (редактирование / вкл-выкл / удаление).
- EN: SemVer patch bump to `8.55.48`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.48` and `ANDROID_VERSION_CODE=573`; prerelease links aligned to `v8.55.48-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.48`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.48` и `ANDROID_VERSION_CODE=573`; prerelease-ссылки выровнены на `v8.55.48-develop`.

## [8.55.37] - 2026-04-19

### Fixed / Исправлено
- EN: Android `zfs место` tile now opens the free-space dialog without a tile-level gear; host settings were moved into the opened `💽 Free space of ZFS pools` dialog header and still run `zfsp_hosts_list`.
- RU: Для Android-плашки `zfs место` убрана шестерёнка на самой плашке; настройки хостов перенесены в заголовок открываемого окна `💽 Свободное место ZFS пулов` и по-прежнему запускают `zfsp_hosts_list`.
- EN: SemVer patch bump to `8.55.37`; synchronized explicit version mentions across runtime/config/docs and Android artifacts; Android metadata updated to `ANDROID_VERSION_NAME=8.55.37` and `ANDROID_VERSION_CODE=563`; prerelease links aligned to `v8.55.37-develop`.
- RU: Выполнен SemVer patch-бамп до `8.55.37`; синхронизированы явные упоминания версии в runtime/config/docs и Android-артефактах; Android-метаданные обновлены до `ANDROID_VERSION_NAME=8.55.37` и `ANDROID_VERSION_CODE=563`; prerelease-ссылки выровнены на `v8.55.37-develop`.

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
