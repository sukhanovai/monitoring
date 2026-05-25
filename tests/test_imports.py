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
# Heavy-импорты (core.monitor_core, bot.handlers, modules.mail_monitor, main)
# добавятся позже, когда CI научится ставить runtime deps.
LIGHT_MODULES = [
    "config.settings",
    "lib.utils",
    "lib.logging",
]


@pytest.mark.parametrize("module_name", LIGHT_MODULES)
def test_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)


def test_app_version_consistent() -> None:
    """APP_VERSION в config.settings должен быть единственным источником истины."""
    from config import settings

    assert settings.APP_VERSION
    assert settings.ANDROID_LATEST_VERSION
    assert settings.ANDROID_MIN_SUPPORTED_VERSION
