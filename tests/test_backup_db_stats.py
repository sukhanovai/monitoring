"""
Тесты сводок бэкапов БД (extensions/backup_monitor/backup_utils.py).

Регрессия: утренний отчёт показывал «Нет бэкапов за 16ч — Клиенты: Buh2025»,
хотя бэкапы приходили каждый день. Парсер писем сохраняет имя БД в нижнем
регистре ('buh2025', из subject_lower), а в конфиге ключ — 'Buh2025';
get_database_backup_stats / get_backup_summary сравнивали имена точным
регистрозависимым сравнением. Детали БД (get_database_details) при этом
уже сравнивали нормализованно (8.63.30) — отчёт и детали противоречили
друг другу. Теперь обе сводки используют ту же нормализацию.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pytest


@pytest.fixture()
def backups_db(monkeypatch, tmp_path):
    """Подменяет DATA_DIR/DATABASE_BACKUP_CONFIG и наполняет backups.db.

    В конфиге клиентская база записана как 'Buh2025', в БД бэкапов — как
    'buh2025' (так её сохраняет parse_database_backup из subject_lower).
    """
    import config.db_settings as db_settings

    monkeypatch.setattr(db_settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        db_settings,
        "DATABASE_BACKUP_CONFIG",
        {
            "client_databases": {
                "Buh2025": "Бухгалтерия 2025",
                "shop": "Магазин",
            },
        },
    )

    conn = sqlite3.connect(str(tmp_path / "backups.db"))
    conn.execute(
        """
        CREATE TABLE database_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_name TEXT NOT NULL,
            database_name TEXT NOT NULL,
            database_display_name TEXT,
            backup_status TEXT NOT NULL,
            backup_type TEXT,
            task_type TEXT,
            error_count INTEGER DEFAULT 0,
            email_subject TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    recent = (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    for db_name in ("buh2025", "shop"):
        conn.execute(
            """
            INSERT INTO database_backups
            (host_name, database_name, backup_status, backup_type, task_type, received_at)
            VALUES ('rubicon-1c', ?, 'success', 'client', 'client_database_dump', ?)
            """,
            (db_name, recent),
        )
    conn.commit()
    conn.close()
    return tmp_path


def test_database_backup_stats_matches_db_names_case_insensitively(backups_db) -> None:
    from extensions.backup_monitor.backup_utils import get_database_backup_stats

    stats = get_database_backup_stats(period_hours=16)
    assert stats["error"] is None
    client = next(c for c in stats["categories"] if c["key"] == "client")
    assert client["total"] == 2
    assert client["ok"] == 2
    assert client["missing"] == []
    assert client["stale"] == []


def test_backup_summary_matches_db_names_case_insensitively(backups_db) -> None:
    from extensions.backup_monitor.backup_utils import get_backup_summary

    message, has_issues = get_backup_summary(
        period_hours=16, include_proxmox=False, include_databases=True
    )
    assert "Клиенты: 2/2" in message
    assert "Нет бэкапов за последние" not in message
    assert has_issues is False
