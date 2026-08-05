"""
Тесты сборщиков паттернов писем (modules/mail_parts/patterns.py).

Регрессия: если у настройки BACKUP_PATTERNS в таблице `settings`
проставлен data_type='string', она приходит сырой JSON-строкой. Тогда
fallback `BACKUP_PATTERNS.get(...)` падал с
«'str' object has no attribute 'get'» — в логе mail_monitor это видно как
«❌ Ошибка извлечения паттернов передачи на NAS» и «❌ Ошибка извлечения
паттернов конфигов/историй», а сами письма переставали разбираться.
"""

from __future__ import annotations

import json

import pytest

_RAW_PATTERNS = {
    "nas_transfer": {"subject": [r"^Передача бэкапов на NAS"]},
    "config_console": {"subject": [r"^Config backup (\S+)"]},
    "mail": {"subject": [r"^Бэкап почты"]},
    "zfs": {"subject": [r"^ZFS status"]},
}


@pytest.fixture
def patterns_module(monkeypatch):
    """patterns.py с пустой таблицей backup_patterns — работает только fallback."""
    import modules.mail_parts.patterns as patterns
    from core.config_manager import config_manager

    monkeypatch.setattr(config_manager, "get_backup_patterns", lambda: {})
    return patterns


@pytest.mark.parametrize(
    "getter,category",
    [
        ("get_nas_transfer_patterns_from_config", "nas_transfer"),
        ("get_config_console_patterns_from_config", "config_console"),
        ("get_mail_patterns_from_config", "mail"),
        ("get_zfs_patterns_from_config", "zfs"),
    ],
)
def test_patterns_from_json_string_setting(patterns_module, monkeypatch, getter, category) -> None:
    """BACKUP_PATTERNS строкой разбирается, а не теряется с ошибкой."""
    monkeypatch.setattr(
        patterns_module,
        "BACKUP_PATTERNS",
        json.dumps(_RAW_PATTERNS, ensure_ascii=False),
    )

    assert getattr(patterns_module, getter)() == _RAW_PATTERNS[category]["subject"]


@pytest.mark.parametrize(
    "getter,category",
    [
        ("get_nas_transfer_patterns_from_config", "nas_transfer"),
        ("get_config_console_patterns_from_config", "config_console"),
        ("get_mail_patterns_from_config", "mail"),
        ("get_zfs_patterns_from_config", "zfs"),
    ],
)
def test_patterns_from_dict_setting(patterns_module, monkeypatch, getter, category) -> None:
    """Обычный словарь продолжает работать как раньше."""
    monkeypatch.setattr(patterns_module, "BACKUP_PATTERNS", _RAW_PATTERNS)

    assert getattr(patterns_module, getter)() == _RAW_PATTERNS[category]["subject"]


def test_table_patterns_win_over_setting(patterns_module, monkeypatch) -> None:
    """Паттерны из таблицы backup_patterns приоритетнее настройки."""
    from core.config_manager import config_manager

    monkeypatch.setattr(patterns_module, "BACKUP_PATTERNS", _RAW_PATTERNS)
    monkeypatch.setattr(
        config_manager,
        "get_backup_patterns",
        lambda: {"nas_transfer": {"subject": ["из таблицы"]}},
    )

    assert patterns_module.get_nas_transfer_patterns_from_config() == ["из таблицы"]


def test_table_patterns_as_string(patterns_module, monkeypatch) -> None:
    """Строковый ответ таблицы паттернов тоже разбирается."""
    from core.config_manager import config_manager

    monkeypatch.setattr(patterns_module, "BACKUP_PATTERNS", {})
    monkeypatch.setattr(
        config_manager,
        "get_backup_patterns",
        lambda: json.dumps({"config_console": {"subject": ["из строки"]}}, ensure_ascii=False),
    )

    assert patterns_module.get_config_console_patterns_from_config() == ["из строки"]


def test_snapshot_patterns_from_json_string_setting(patterns_module, monkeypatch) -> None:
    """Паттерны передачи снэпшотов из строковой настройки нормализуются."""
    monkeypatch.setattr(
        patterns_module,
        "BACKUP_PATTERNS",
        json.dumps({"snapshot_transfer": {"subject": ["Передача снэпшотов .*"]}}),
    )

    assert patterns_module.get_snapshot_transfer_patterns_from_config() == [
        r"Передача\s+снэпшотов\s+.*"
    ]


def test_coerce_json_setting_parses_string() -> None:
    """get_json_setting возвращает словарь, даже если в БД лежит строка."""
    from config.db_settings import _coerce_json_setting

    value = _coerce_json_setting("BACKUP_PATTERNS", json.dumps(_RAW_PATTERNS), {})
    assert value == _RAW_PATTERNS


def test_coerce_json_setting_falls_back_on_garbage() -> None:
    """Неразбираемая строка не подменяет собой словарь."""
    from config.db_settings import _coerce_json_setting

    default = {"nas_transfer": {}}
    assert _coerce_json_setting("BACKUP_PATTERNS", "не json", default) is default


def test_coerce_json_setting_keeps_plain_string_settings() -> None:
    """Строковые настройки со строковым default не трогаем."""
    from config.db_settings import _coerce_json_setting

    assert _coerce_json_setting("SSH_USERNAME", "root", "monitor") == "root"
