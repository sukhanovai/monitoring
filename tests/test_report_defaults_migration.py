"""
Одноразовая миграция состава отчёта со старых дефолтов на дефолт 9.0.0
(`core/config_manager.py:_migrate_report_extensions`).

При обновлении с 8.x сохранённый прежний дефолт (без ids_cert_monitor)
должен смениться на текущий — у системы и в личных настройках, — а
ручной выбор пользователя не трогается, в том числе при повторных запусках.
"""

from __future__ import annotations

import importlib
import json
import sqlite3

from lib.report_settings import (
    DEFAULT_REPORT_EXTENSIONS,
    LEGACY_DEFAULT_REPORT_EXTENSIONS,
    is_previous_default_report_extensions,
)

_config_module = importlib.import_module("core.config_manager")

_OLD_8X_DEFAULT = [ext for ext in DEFAULT_REPORT_EXTENSIONS if ext != "ids_cert_monitor"]


def _seed(db_path, system_value, personal_values):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT, category TEXT, "
        "description TEXT, data_type TEXT, updated_at TIMESTAMP)"
    )
    conn.execute(
        "INSERT INTO settings (key, value, category, data_type) "
        "VALUES ('REPORT_EXTENSIONS', ?, 'report', 'list')",
        (json.dumps(system_value),),
    )
    conn.execute(
        "CREATE TABLE user_preferences (user_id INTEGER, key TEXT, value TEXT, "
        "updated_at TIMESTAMP, PRIMARY KEY (user_id, key))"
    )
    for user_id, value in personal_values.items():
        conn.execute(
            "INSERT INTO user_preferences (user_id, key, value) VALUES (?, 'REPORT_EXTENSIONS', ?)",
            (user_id, json.dumps(value)),
        )
    conn.commit()
    conn.close()


def _read(db_path):
    conn = sqlite3.connect(str(db_path))
    system = json.loads(
        conn.execute("SELECT value FROM settings WHERE key = 'REPORT_EXTENSIONS'").fetchone()[0]
    )
    personal = {
        uid: json.loads(value)
        for uid, value in conn.execute(
            "SELECT user_id, value FROM user_preferences WHERE key = 'REPORT_EXTENSIONS'"
        )
    }
    conn.close()
    return system, personal


def test_previous_defaults_are_recognised():
    assert is_previous_default_report_extensions(LEGACY_DEFAULT_REPORT_EXTENSIONS)
    assert is_previous_default_report_extensions(_OLD_8X_DEFAULT)
    # 8.66.0: mail_cert_monitor вместо ids_cert_monitor.
    assert is_previous_default_report_extensions(_OLD_8X_DEFAULT + ["mail_cert_monitor"])
    assert not is_previous_default_report_extensions(DEFAULT_REPORT_EXTENSIONS)
    assert not is_previous_default_report_extensions(["backup_monitor"])
    assert not is_previous_default_report_extensions(None)


def test_old_defaults_migrate_once_and_custom_sets_stay(tmp_path):
    db_path = tmp_path / "settings.db"
    custom = ["backup_monitor", "zfs_monitor"]
    _seed(db_path, _OLD_8X_DEFAULT, {1: _OLD_8X_DEFAULT, 2: custom})

    _config_module.ConfigManager(db_path=str(db_path))
    system, personal = _read(db_path)
    assert system == DEFAULT_REPORT_EXTENSIONS
    assert personal[1] == DEFAULT_REPORT_EXTENSIONS
    assert personal[2] == custom

    # Пользователь сознательно убрал IDS (получился прежний дефолт) —
    # повторный запуск не возвращает его.
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "UPDATE user_preferences SET value = ? WHERE user_id = 1",
        (json.dumps(_OLD_8X_DEFAULT),),
    )
    conn.commit()
    conn.close()
    _config_module.ConfigManager(db_path=str(db_path))
    _system, personal = _read(db_path)
    assert personal[1] == _OLD_8X_DEFAULT
