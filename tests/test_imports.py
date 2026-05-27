"""
Smoke-тест на импорты ключевых модулей.

Главная задача — ловить обрыв импортов на крупных декомпозициях
(PR5: core.monitor_core, PR6: modules.mail_monitor, PR7:
bot.handlers.settings_handlers). Если рефакторинг ломает граф
импортов, тест краснеет до запуска приложения.
"""

from __future__ import annotations

import importlib

import pytest

# Лёгкие модули без runtime-зависимостей (paramiko/telegram/matrix-nio).
# Heavy-импорты (bot.handlers, modules.mail_monitor, main) добавятся
# позже, когда CI научится ставить runtime deps.
LIGHT_MODULES = [
    "config.settings",
    "lib.utils",
    "lib.logging",
    "core.monitor_state",
]


def test_monitor_decomposed_modules_importable() -> None:
    """PR5: пакет `core/monitor_parts/` — extract'ы из monitor_core.py —
    должен импортироваться без падений при наличии заглушек runtime
    зависимостей. Имя пакета — `monitor_parts`, чтобы не перекрыть
    существующий модуль `core/monitor.py` (фикс к hotfix-у 8.62.50)."""
    import importlib

    for name in (
        "core.monitor",  # singleton-модуль `monitor` должен оставаться доступным
        "core.monitor_parts",
        "core.monitor_parts.alerts",
        "core.monitor_parts.availability",
        "core.monitor_parts.lifecycle",
        "core.monitor_parts.report",
        "core.monitor_parts.resource_checks",
        "core.monitor_parts.telegram_handlers",
        # PR6/PR6b/PR6c — пакет декомпозиции mail_monitor
        "modules.mail_parts",
        "modules.mail_parts.patterns",
        "modules.mail_parts.processor",
        "modules.mail_parts.db",
        "modules.mail_parts.db.schema",
        "modules.mail_parts.parsers",
        "modules.mail_parts.parsers.database",
        "modules.mail_parts.parsers.mail",
        "modules.mail_parts.parsers.proxmox",
        "modules.mail_parts.parsers.stock_load",
        "modules.mail_parts.parsers.zfs",
    ):
        importlib.import_module(name)


def test_core_monitor_singleton_not_shadowed() -> None:
    """Регрессия hotfix-а 8.62.50: пакет рядом с `core/monitor.py` не
    должен перекрывать `from core.monitor import monitor`."""
    from core.monitor import monitor

    assert monitor is not None


def test_mail_monitor_facade_and_parts() -> None:
    """PR6: BackupProcessor вынесен в `modules.mail_parts.processor`,
    pattern-хелперы — в `modules.mail_parts.patterns`. Фасад
    `modules.mail_monitor` должен по-прежнему отдавать `BackupProcessor`,
    `run_mail_monitor`, `main` — на них завязаны `core.task_router` и
    `modules.improved_mail_monitor`. Имя пакета — `mail_parts`, чтобы не
    столкнуться с существующим `modules/mail_monitor.py` (урок PR5 hotfix)."""
    from modules.mail_monitor import BackupProcessor, main, run_mail_monitor
    from modules.mail_parts.patterns import (
        get_database_patterns_from_config,
        get_mail_patterns_from_config,
        get_snapshot_transfer_patterns_from_config,
        get_stock_load_patterns_from_config,
        get_zfs_patterns_from_config,
    )
    from modules.mail_parts.processor import BackupProcessor as BackupProcessorPkg

    assert BackupProcessorPkg is BackupProcessor
    assert callable(run_mail_monitor)
    assert callable(main)
    assert callable(get_database_patterns_from_config)
    assert callable(get_zfs_patterns_from_config)
    assert callable(get_mail_patterns_from_config)
    assert callable(get_snapshot_transfer_patterns_from_config)
    assert callable(get_stock_load_patterns_from_config)


def test_settings_handlers_facade() -> None:
    """PR7: bot/handlers/settings_handlers.py превращён в одноимённый
    пакет с подмодулем _legacy.py. Внешние импортёры
    (`bot.handlers.callbacks`, `bot.menu.handlers`,
    `extensions.backup_monitor.bot_handler`) опираются на конкретные имена
    из этого пакета — тест явно их перепроверяет, чтобы PR7b/PR7c не
    обронили имя при разнесении на UI-семьи."""
    from bot.handlers.settings_handlers import (
        BACKUP_SETTINGS_CALLBACKS,
        handle_setting_value,
        settings_callback_handler,
        show_mail_patterns_menu,
        show_snapshot_transfer_settings,
        show_zfs_main_menu,
    )

    assert isinstance(BACKUP_SETTINGS_CALLBACKS, (set, frozenset))
    assert BACKUP_SETTINGS_CALLBACKS  # non-empty (24 callback id's)
    assert callable(settings_callback_handler)
    assert callable(handle_setting_value)
    assert callable(show_mail_patterns_menu)
    assert callable(show_zfs_main_menu)
    assert callable(show_snapshot_transfer_settings)

    # _legacy остаётся приватным подмодулем пакета, но должен быть
    # импортируем — иначе ломается обратный путь, если кому-то нужен
    # full-module reload.
    from bot.handlers.settings_handlers import _legacy
    from bot.handlers.settings_handlers._legacy import (
        settings_callback_handler as direct_handler,
    )

    assert direct_handler is settings_callback_handler  # identity preserved
    assert _legacy.__name__ == "bot.handlers.settings_handlers._legacy"


def test_settings_handlers_supplier_stock_split() -> None:
    """PR7b: блок supplier_stock (~84 функции) вынесен из _legacy.py в
    одноимённый модуль `settings_handlers.supplier_stock`. Тест ловит,
    чтобы:
    1. функции были доступны через прямой импорт нового модуля;
    2. они оставались доступны через фасад пакета (`import *` в __init__);
    3. `_legacy.py` через обратный re-export `from .supplier_stock import *`
       продолжал отдавать те же объекты — нужно для внутренних ссылок
       `settings_callback_handler` в _legacy.py."""
    from bot.handlers.settings_handlers import (
        show_stock_load_settings,
        show_supplier_stock_settings,
        supplier_stock_handle_input,
    )
    from bot.handlers.settings_handlers._legacy import (
        show_supplier_stock_settings as via_legacy,
    )
    from bot.handlers.settings_handlers.supplier_stock import (
        show_supplier_stock_settings as via_module,
    )

    assert callable(show_supplier_stock_settings)
    assert callable(supplier_stock_handle_input)
    assert callable(show_stock_load_settings)
    # Все три пути ведут к одному и тому же объекту функции
    assert via_module is show_supplier_stock_settings
    assert via_legacy is show_supplier_stock_settings
    assert show_supplier_stock_settings.__module__ == (
        "bot.handlers.settings_handlers.supplier_stock"
    )


def test_settings_handlers_zfs_split() -> None:
    """PR7c: блок ZFS (~29 функций) вынесен из _legacy.py в одноимённый
    модуль `settings_handlers.zfs`. Тест ловит, чтобы три пути импорта
    (`...settings_handlers.X`, `...settings_handlers._legacy.X`,
    `...settings_handlers.zfs.X`) возвращали один и тот же объект и
    `__module__` указывал в новый модуль."""
    from bot.handlers.settings_handlers import (
        add_zfs_pattern_handler,
        show_zfs_main_menu,
        show_zfs_patterns_menu,
        zfs_pattern_confirm_handler,
    )
    from bot.handlers.settings_handlers._legacy import (
        show_zfs_main_menu as via_legacy,
    )
    from bot.handlers.settings_handlers.zfs import (
        show_zfs_main_menu as via_module,
    )

    assert callable(show_zfs_main_menu)
    assert callable(show_zfs_patterns_menu)
    assert callable(add_zfs_pattern_handler)
    assert callable(zfs_pattern_confirm_handler)
    assert via_module is show_zfs_main_menu
    assert via_legacy is show_zfs_main_menu
    assert show_zfs_main_menu.__module__ == "bot.handlers.settings_handlers.zfs"


def test_settings_handlers_backups_split() -> None:
    """PR7d: Proxmox vzdump (15 функций) и ZFS snapshot transfer
    (10 функций) выделены в `settings_handlers.backups.proxmox` и
    `settings_handlers.backups.snapshot`. Тест ловит identity на трёх
    путях для представителя каждой подсемьи."""
    from bot.handlers.settings_handlers import (
        add_proxmox_pattern_handler,
        add_snapshot_pattern_handler,
        show_proxmox_backup_settings,
        show_proxmox_patterns_menu,
        show_snapshot_hosts_menu,
        show_snapshot_transfer_settings,
    )
    from bot.handlers.settings_handlers._legacy import (
        show_proxmox_backup_settings as proxmox_via_legacy,
        show_snapshot_transfer_settings as snapshot_via_legacy,
    )
    from bot.handlers.settings_handlers.backups.proxmox import (
        show_proxmox_backup_settings as proxmox_via_module,
    )
    from bot.handlers.settings_handlers.backups.snapshot import (
        show_snapshot_transfer_settings as snapshot_via_module,
    )

    assert callable(show_proxmox_backup_settings)
    assert callable(show_proxmox_patterns_menu)
    assert callable(add_proxmox_pattern_handler)
    assert callable(show_snapshot_hosts_menu)
    assert callable(show_snapshot_transfer_settings)
    assert callable(add_snapshot_pattern_handler)

    assert proxmox_via_module is show_proxmox_backup_settings
    assert proxmox_via_legacy is show_proxmox_backup_settings
    assert show_proxmox_backup_settings.__module__ == (
        "bot.handlers.settings_handlers.backups.proxmox"
    )

    assert snapshot_via_module is show_snapshot_transfer_settings
    assert snapshot_via_legacy is show_snapshot_transfer_settings
    assert show_snapshot_transfer_settings.__module__ == (
        "bot.handlers.settings_handlers.backups.snapshot"
    )


def test_settings_handlers_backups_db_split() -> None:
    """PR7e: DB-backup семья (53 функции) выделена в
    `settings_handlers.backups.db`. Тест ловит identity на трёх путях
    для пары представителей: `show_database_backup_settings` (главное
    меню) и `settings_toggle_database_monitoring` (callback)."""
    from bot.handlers.settings_handlers import (
        add_database_category_handler,
        delete_database_entry_execute,
        edit_default_db_pattern_handler,
        handle_db_category_input,
        settings_toggle_database_monitoring,
        show_database_backup_settings,
        show_db_patterns_menu,
    )
    from bot.handlers.settings_handlers._legacy import (
        settings_toggle_database_monitoring as toggle_via_legacy,
        show_database_backup_settings as menu_via_legacy,
    )
    from bot.handlers.settings_handlers.backups.db import (
        settings_toggle_database_monitoring as toggle_via_module,
        show_database_backup_settings as menu_via_module,
    )

    assert callable(show_database_backup_settings)
    assert callable(show_db_patterns_menu)
    assert callable(add_database_category_handler)
    assert callable(delete_database_entry_execute)
    assert callable(edit_default_db_pattern_handler)
    assert callable(handle_db_category_input)
    assert callable(settings_toggle_database_monitoring)

    assert menu_via_module is show_database_backup_settings
    assert menu_via_legacy is show_database_backup_settings
    assert toggle_via_module is settings_toggle_database_monitoring
    assert toggle_via_legacy is settings_toggle_database_monitoring

    assert show_database_backup_settings.__module__ == ("bot.handlers.settings_handlers.backups.db")
    assert settings_toggle_database_monitoring.__module__ == (
        "bot.handlers.settings_handlers.backups.db"
    )


def test_settings_handlers_pr7f_split() -> None:
    """PR7f: финальная партия семей вынесена из _legacy.py:
    - `settings_handlers.auth` (~7 функций: SSH/Windows auth UI);
    - `settings_handlers.backups.mail` (~9 функций: mail backup UI);
    - `settings_handlers.windows_creds` (~2 функции: handler ввода учётки).
    Тест ловит identity на трёх путях для представителей каждой подсемьи."""
    from bot.handlers.settings_handlers import (
        handle_windows_credential_input,
        show_auth_settings,
        show_mail_backup_settings,
        show_mail_patterns_menu,
        show_ssh_auth_settings,
        show_windows_auth_settings,
    )
    from bot.handlers.settings_handlers._legacy import (
        handle_windows_credential_input as w_via_legacy,
        show_auth_settings as auth_via_legacy,
        show_mail_backup_settings as mail_via_legacy,
    )
    from bot.handlers.settings_handlers.auth import (
        show_auth_settings as auth_via_module,
    )
    from bot.handlers.settings_handlers.backups.mail import (
        show_mail_backup_settings as mail_via_module,
    )
    from bot.handlers.settings_handlers.windows_creds import (
        handle_windows_credential_input as w_via_module,
    )

    assert callable(show_auth_settings)
    assert callable(show_ssh_auth_settings)
    assert callable(show_windows_auth_settings)
    assert callable(show_mail_backup_settings)
    assert callable(show_mail_patterns_menu)
    assert callable(handle_windows_credential_input)

    assert auth_via_module is show_auth_settings
    assert auth_via_legacy is show_auth_settings
    assert show_auth_settings.__module__ == "bot.handlers.settings_handlers.auth"

    assert mail_via_module is show_mail_backup_settings
    assert mail_via_legacy is show_mail_backup_settings
    assert show_mail_backup_settings.__module__ == ("bot.handlers.settings_handlers.backups.mail")

    assert w_via_module is handle_windows_credential_input
    assert w_via_legacy is handle_windows_credential_input
    assert handle_windows_credential_input.__module__ == (
        "bot.handlers.settings_handlers.windows_creds"
    )


def test_mail_backup_processor_mixins_composition() -> None:
    """PR6c: BackupProcessor собран из 5 parser-mixin'ов через множественное
    наследование. Тест закрепляет состав MRO — поломка инфраструктуры
    разбиения (одного mixin'а забыли, или порядок наследования съехал)
    покраснит CI до запуска."""
    from modules.mail_monitor import BackupProcessor
    from modules.mail_parts.parsers import (
        DatabaseBackupParserMixin,
        MailBackupParserMixin,
        ProxmoxBackupParserMixin,
        StockLoadParserMixin,
        ZfsBackupParserMixin,
    )

    mro = BackupProcessor.__mro__
    for mixin in (
        DatabaseBackupParserMixin,
        MailBackupParserMixin,
        ProxmoxBackupParserMixin,
        StockLoadParserMixin,
        ZfsBackupParserMixin,
    ):
        assert mixin in mro, mixin.__name__

    # Хотя бы по одному «представительному» методу из каждого mixin'а
    # должен быть доступен на инстансе.
    for method_name in (
        "parse_database_backup",  # DatabaseBackupParserMixin
        "parse_mail_backup",  # MailBackupParserMixin
        "parse_subject",  # ProxmoxBackupParserMixin
        "parse_stock_load_log",  # StockLoadParserMixin
        "parse_zfs_status",  # ZfsBackupParserMixin
    ):
        assert hasattr(BackupProcessor, method_name), method_name


def test_resource_check_specs_unified() -> None:
    """PR5: ResourceCheckSpec заменяет три копии perform_*_check. Тест
    закрепляет, что CPU/RAM/DISK имеют ожидаемые ключи и пороги."""
    from core.monitor_parts.resource_checks import CPU_SPEC, DISK_SPEC, RAM_SPEC

    assert CPU_SPEC.metric == "cpu" and CPU_SPEC.critical_threshold == 80
    assert RAM_SPEC.metric == "ram" and RAM_SPEC.critical_threshold == 85
    assert DISK_SPEC.metric == "disk" and DISK_SPEC.critical_threshold == 90
    assert CPU_SPEC.callback_id == "check_cpu"
    assert RAM_SPEC.callback_id == "check_ram"
    assert DISK_SPEC.callback_id == "check_disk"


def test_monitor_state_singleton() -> None:
    """MonitoringState из PR4 — единственный источник runtime-состояния
    ядра. Тест ловит ломающие изменения структуры в PR5+."""
    from core.monitor_state import STATE_FIELDS, MonitoringState, state

    assert isinstance(state, MonitoringState)
    expected = {
        "bot",
        "server_status",
        "morning_data",
        "monitoring_active",
        "last_check_time",
        "servers",
        "resource_history",
        "last_resource_check",
        "resource_alerts_sent",
        "last_report_date",
        "last_collection_schedule_time",
        "sent_collection_slots",
    }
    assert set(STATE_FIELDS) == expected
    for name in expected:
        assert hasattr(state, name), name


@pytest.mark.parametrize("module_name", LIGHT_MODULES)
def test_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)


def test_app_version_consistent() -> None:
    """APP_VERSION в config.settings должен быть единственным источником истины."""
    from config import settings

    assert settings.APP_VERSION
    assert settings.ANDROID_LATEST_VERSION
    assert settings.ANDROID_MIN_SUPPORTED_VERSION
