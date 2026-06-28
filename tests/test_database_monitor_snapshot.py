"""
Тесты для get_database_monitor_snapshot.

Проверяют, что бэкапы авто-обнаруживаемых категорий (yandex), попавшие в
backups.db, показываются в меню «Бэкапы БД» даже если их нет в статической
конфигурации, тогда как незнакомые базы обычных категорий по-прежнему
отфильтровываются.
"""

from __future__ import annotations

import extensions.backup_monitor.backup_handlers as bh


class _FakeBackupBot:
    """Минимальная заглушка backup_bot для get_database_monitor_snapshot."""

    def __init__(self, distinct_rows):
        self._distinct_rows = distinct_rows

    def execute_query(self, query, params=()):
        # Запрос со SELECT DISTINCT ... FROM database_backups (без WHERE)
        # отдаёт перечень (backup_type, database_name, display_name).
        if "SELECT DISTINCT" in query:
            return list(self._distinct_rows)
        # _get_latest_backup_type делает SELECT backup_type ... WHERE ...
        db_name = params[0] if params else ""
        for backup_type, name, _display in self._distinct_rows:
            if str(name).lower() == str(db_name).lower():
                return [(backup_type,)]
        return []

    def get_database_display_status(self, backup_type, db_name):
        return "success"


def _patch_config(monkeypatch, config):
    monkeypatch.setattr(
        "extensions.backup_monitor.db_settings_backup_monitor.DATABASE_BACKUP_CONFIG",
        config,
        raising=False,
    )
    monkeypatch.setattr(bh, "_get_disabled_db_monitors", lambda: set())


def test_yandex_backup_autodiscovered_when_absent_from_config(monkeypatch):
    """Бэкап yandex/MDM из backups.db виден, хотя в конфиге его нет."""
    _patch_config(monkeypatch, {"yandex_backups": {}})

    bot = _FakeBackupBot([("yandex", "MDM", "")])
    snapshot = bh.get_database_monitor_snapshot(bot)

    names = {(row["backup_type"], row["db_name"]) for row in snapshot}
    assert ("yandex", "MDM") in names


def test_unconfigured_non_autodiscover_db_is_filtered(monkeypatch):
    """Незнакомая база обычной категории (company) не показывается."""
    _patch_config(monkeypatch, {"company_databases": {}})

    bot = _FakeBackupBot([("company_database", "SOME_DB", "")])
    snapshot = bh.get_database_monitor_snapshot(bot)

    names = {(row["backup_type"], row["db_name"]) for row in snapshot}
    assert ("company_database", "SOME_DB") not in names


def test_configured_yandex_db_keeps_display_name(monkeypatch):
    """Настроенная yandex-база использует человекочитаемое имя из конфига."""
    _patch_config(monkeypatch, {"yandex_backups": {"MDM": "Yandex MDM"}})

    bot = _FakeBackupBot([("yandex", "MDM", "")])
    snapshot = bh.get_database_monitor_snapshot(bot)

    rows = {row["db_name"]: row for row in snapshot}
    assert rows["MDM"]["display_name"] == "Yandex MDM"
