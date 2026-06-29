"""
/bot/handlers/settings_handlers/__init__.py
Server Monitoring System v8.63.32
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings handlers package — точка входа пакета декомпозиции
bot/handlers/settings_handlers (PR7 серии оптимизации).
Система мониторинга серверов
Версия: 8.63.32
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

# --- Восстановление общего пространства приватных хелперов ---
# При декомпозиции монолита приватные (`_`-префиксные) функции разъехались
# по модулям пакета, а `from ... import *` подтягивает только публичные имена.
# Из-за этого код одного модуля, ссылающийся на приватный хелпер из другого
# (например `supplier_stock` → `_format_archive_cleanup_days` из `_legacy`
# или `_build_mail_pattern_from_fragments` из `backups.mail`), падал с
# `NameError`. Ниже собираем все приватные хелперы модульного уровня со всех
# подмодулей пакета и доинъецируем недостающие в globals каждого модуля.
# `setdefault` не перетирает собственные определения модуля, поэтому
# восстанавливается видимость имён ровно как в исходном monolith-файле.
from bot.handlers.settings_handlers import (  # noqa: E402,F401
    _legacy,
    auth,
    callback_dispatcher,
    report,
    settings_value,
    supplier_stock,
    windows_creds,
    zfs,
)
from bot.handlers.settings_handlers.backups import (  # noqa: E402,F401
    db as _backups_db,
    mail as _backups_mail,
    proxmox as _backups_proxmox,
    snapshot as _backups_snapshot,
)

_PACKAGE_HELPER_MODULES = (
    _legacy,
    auth,
    callback_dispatcher,
    report,
    settings_value,
    supplier_stock,
    windows_creds,
    zfs,
    _backups_db,
    _backups_mail,
    _backups_proxmox,
    _backups_snapshot,
)


def _share_private_helpers() -> None:
    """Сделать приватные хелперы пакета видимыми во всех его модулях."""
    registry: dict = {}
    for module in _PACKAGE_HELPER_MODULES:
        for name, value in vars(module).items():
            if name.startswith("_") and not name.startswith("__") and callable(value):
                registry.setdefault(name, value)
    for module in _PACKAGE_HELPER_MODULES:
        module_globals = vars(module)
        for name, value in registry.items():
            module_globals.setdefault(name, value)


_share_private_helpers()
