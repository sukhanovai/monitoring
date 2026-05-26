"""
/bot/handlers/settings_handlers/__init__.py
Server Monitoring System v8.62.58
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings handlers package — точка входа пакета декомпозиции
bot/handlers/settings_handlers (PR7 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.58
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет settings_handlers — на этом этапе содержит единый legacy-модуль
`_legacy.py` со всем оригинальным содержимым прежнего monolith-файла
bot/handlers/settings_handlers.py (~14 800 строк, 291 функция). Внешние
импортёры (`bot.handlers.__init__`, `bot.handlers.callbacks`,
`bot.menu.handlers`, `extensions.backup_monitor.bot_handler`) видят
точно те же имена, что и раньше — за счёт явного реэкспорта ниже.
Дальнейшее разнесение по UI-семьям (menu, auth_servers, windows_creds,
backups/{proxmox,db,zfs,mail,snapshot}, supplier_stock) — в PR7b+.
"""

from __future__ import annotations

# Реэкспорт всех публичных имён прежнего monolith-файла. `_legacy.py` не
# объявляет `__all__`, поэтому `import *` подтягивает всё без `_`-префикса —
# ровно то поведение, которое было у одиночного settings_handlers.py.
from bot.handlers.settings_handlers._legacy import *  # noqa: F401, F403

# Явный pin имён, на которые опираются внешние модули — страховка на случай,
# если PR7b/PR7c перепишет какое-то из них и забудет вернуть в публичный
# namespace пакета.
from bot.handlers.settings_handlers._legacy import (  # noqa: F401
    BACKUP_SETTINGS_CALLBACKS,
    handle_setting_value,
    settings_callback_handler,
    show_mail_patterns_menu,
    show_snapshot_transfer_settings,
    show_zfs_main_menu,
)
