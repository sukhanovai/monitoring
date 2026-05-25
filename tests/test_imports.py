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

CRITICAL_MODULES = [
    "config",
    "config.settings",
    "lib.logging",
    "lib.utils",
    "core",
    "core.monitor_core",
    "modules.mail_monitor",
    "bot.handlers",
    "main",
]


@pytest.mark.parametrize("module_name", CRITICAL_MODULES)
def test_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)


def test_app_version_consistent() -> None:
    """APP_VERSION в config.settings должен быть единственным источником истины."""
    from config import settings

    assert settings.APP_VERSION
    assert settings.ANDROID_LATEST_VERSION
    assert settings.ANDROID_MIN_SUPPORTED_VERSION
