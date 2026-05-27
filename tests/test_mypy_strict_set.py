"""
Структурные тесты для mypy-strict набора (PR10).

mypy сам по себе запускается в CI отдельным шагом — тест здесь
закрепляет ЧТО мы хотим иметь под strict, чтобы:
1. список «эталонных» модулей не уменьшился незаметно;
2. указанные модули продолжали импортироваться (если кто-то их удалит,
   тест покраснит сразу).
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]

# Модули в strict-наборе (mypy `strict = true`).
STRICT_MODULES = [
    "core.monitor_state",
    "scripts.bump_version",
    "modules.mail_parts.db.schema",
    "modules.mail_parts.db",
]

# Модули с почти-strict — без disallow_untyped_calls, потому что
# вызывают untyped legacy-API.
NEAR_STRICT_MODULES = [
    "core.monitor_parts.alerts",
    "core.monitor_parts.availability",
    "core.monitor_parts.resource_checks",
]


def _load_pyproject_mypy_overrides() -> list[dict]:
    text = (REPO_ROOT / "pyproject.toml").read_bytes()
    data = tomllib.loads(text.decode("utf-8"))
    return data.get("tool", {}).get("mypy", {}).get("overrides", [])


@pytest.fixture(scope="module")
def overrides() -> list[dict]:
    return _load_pyproject_mypy_overrides()


def test_strict_set_present_in_pyproject(overrides) -> None:
    """PR10: strict-набор PURE-модулей должен явно лежать в pyproject.toml.
    Защита от случайного удаления override-секции при будущих правках."""
    strict_sections = [o for o in overrides if o.get("strict") is True]
    assert strict_sections, "Не найдено ни одной mypy override с strict=true"

    captured_modules: set[str] = set()
    for section in strict_sections:
        module_value = section.get("module")
        if isinstance(module_value, str):
            captured_modules.add(module_value)
        elif isinstance(module_value, list):
            captured_modules.update(module_value)

    for required in STRICT_MODULES:
        assert required in captured_modules, f"{required!r} должен быть в strict-наборе mypy"


def test_near_strict_set_present_in_pyproject(overrides) -> None:
    """PR10: near-strict набор (`disallow_untyped_defs` без
    `disallow_untyped_calls`) обязан быть в pyproject — это документация
    плана, какие модули ВКЛЮЧИТЬ в полный strict следующим шагом."""
    near_strict_sections = [
        o
        for o in overrides
        if o.get("disallow_untyped_defs") is True and o.get("strict") is not True
    ]
    captured: set[str] = set()
    for section in near_strict_sections:
        module_value = section.get("module")
        if isinstance(module_value, str):
            captured.add(module_value)
        elif isinstance(module_value, list):
            captured.update(module_value)
    for required in NEAR_STRICT_MODULES:
        assert required in captured, f"{required!r} должен быть в near-strict наборе mypy"


@pytest.mark.parametrize("module_name", STRICT_MODULES + NEAR_STRICT_MODULES)
def test_strict_targets_importable(module_name: str) -> None:
    """Подстраховка: модули из mypy-набора должны импортироваться без
    стороннего runtime окружения (стабы в conftest). Если кто-то
    удалит/переименует модуль из списка — увидим тут."""
    importlib.import_module(module_name)
