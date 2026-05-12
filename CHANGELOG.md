# Changelog / История изменений

## [8.0.3] - 2026-04-12

### RU
- В разделе настроек бэкапов для ZFS добавлена отдельная кнопка **«🧊 Паттерны ZFS»** для прямого перехода к управлению паттернами без промежуточного шага через меню ZFS.

### EN
- Added a dedicated **“🧊 ZFS Patterns”** button in backup settings for direct access to ZFS pattern management without going through the intermediate ZFS menu.

## [8.0.2] - 2026-04-12

### RU
- Исправлена нормализация имён ZFS-хостов (регистронезависимое сопоставление): проблемы на хостах теперь корректно попадают в сводку и больше не маскируются статусом «OK» из-за различий в регистре имени.
- Вывод статусов ZFS в сводках теперь приводит имена хостов к конфигурационным, поэтому плашка и детальная страница показывают фактическое состояние по включённым серверам.

### EN
- Fixed ZFS host name normalization (case-insensitive matching): host issues are now correctly included in summaries and are no longer masked by an “OK” status due to case differences.
- ZFS status rendering in summaries now maps host names to configured names, so the tile and detailed status page reflect the real state for enabled servers.

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
