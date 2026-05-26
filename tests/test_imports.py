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
