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
