# Changelog / История изменений

## [8.0.2] - 2026-04-02

### RU
- Добавлена поддержка переменной окружения `TELEGRAM_PROXY_URL`: теперь прокси можно применять только к Telegram-трафику без запуска всего процесса через `proxychains`.
- Инициализация Telegram-бота обновлена: при наличии `TELEGRAM_PROXY_URL` используется `request_kwargs.proxy_url`.
- Обновлён production-пример в `README.md` с рекомендацией использовать `TELEGRAM_PROXY_URL` вместо глобального `proxychains`.
- В веб-интерфейсе обновлён нижний служебный текст: убрана пометка о визуальном режиме, отображается актуальная версия.

### EN
- Added support for the `TELEGRAM_PROXY_URL` environment variable so proxying can be limited to Telegram traffic instead of wrapping the whole process with `proxychains`.
- Updated Telegram bot initialization: when `TELEGRAM_PROXY_URL` is set, `request_kwargs.proxy_url` is used.
- Updated the production example in `README.md` to recommend `TELEGRAM_PROXY_URL` over global `proxychains`.
- Updated the web interface footer service text: removed visual-mode wording and now shows the current version.

## [8.0.1] - 2026-03-18

### RU
- Исправлено поведение кнопки **«Открыть настройки расширений»** в разделе настроек: при открытии теперь действительно отображается список расширений со статусами и кнопками управления.
- Кнопка теперь корректно переключается между состояниями **«Открыть настройки расширений»** и **«Скрыть настройки расширений»** и управляет видимостью списка.

### EN
- Fixed the **"Open extension settings"** button behavior in the settings section: opening it now actually shows the extensions list with statuses and control buttons.
- The button now correctly toggles between **"Open extension settings"** and **"Hide extension settings"** and controls the list visibility.

## [8.0.0] - 2026-03-17

### RU
- Базовый релиз модульной системы мониторинга с Telegram-ботом, расширениями и CLI-проверками.

### EN
- Initial release of the modular monitoring system with Telegram bot, extensions, and CLI checks.
