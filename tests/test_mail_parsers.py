"""
Unit-тесты для pure-функций modules/mail_parts/processor.py и
modules/mail_parts/db/schema.py.

Это первые полезные тесты в проекте — раньше там были только
smoke-тесты на импорт. Они закрепляют поведение pure-методов
`BackupProcessor` (`normalize_status`, `parse_subject`, `parse_duration`,
`duration_to_seconds`, `seconds_to_duration`, `is_proxmox_backup_email`,
`parse_zfs_status`, `parse_mail_backup`, `parse_database_backup`) и
DDL-функции `create_schema`. Любая регрессия в PR6c (разбиение
BackupProcessor на mixins/parsers) покраснит CI до запуска.
"""

from __future__ import annotations

import sqlite3

import pytest


@pytest.fixture(scope="module")
def processor():
    """Поднимает BackupProcessor с in-memory схемой backups.db.

    `BackupProcessor.__init__` создаёт схему в `self.db_path` (берётся из
    `BACKUP_DATABASE_CONFIG["backups_db"]`, который через conftest указывает
    в tmp). Для pure-парсеров БД не нужна, но создать её мы должны, чтобы
    конструктор не упал.
    """
    from modules.mail_parts.processor import BackupProcessor

    return BackupProcessor()


# ---- normalize_status -------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("backup successful", "success"),
        ("successful", "success"),
        ("OK", "success"),
        ("ok.", "success"),
        ("backup failed", "failed"),
        ("failed", "failed"),
        ("ERROR", "failed"),
        # неизвестные статусы возвращаются как есть (lower-cased, trimmed)
        ("partial", "partial"),
        ("   warning   ", "warning"),
    ],
)
def test_normalize_status(processor, raw: str, expected: str) -> None:
    assert processor.normalize_status(raw) == expected


# ---- is_proxmox_backup_email -------------------------------------------------


@pytest.mark.parametrize(
    "subject,expected",
    [
        ("vzdump backup status (pve1) : backup successful", True),
        ("Proxmox Backup Status (host) : backup failed", True),
        ("Re: vzdump backup status (pve1) : backup successful", True),
        ("Случайное письмо о бэкапе", False),
        ("ZFS pool status report", False),
    ],
)
def test_is_proxmox_backup_email(processor, subject: str, expected: bool) -> None:
    assert processor.is_proxmox_backup_email(subject) is expected


# ---- parse_subject ----------------------------------------------------------


def test_parse_subject_extracts_host_and_status(processor) -> None:
    result = processor.parse_subject(
        "vzdump backup status (sr-pve1.example.local) : backup successful"
    )
    assert result is not None
    assert result["host_name"] == "sr-pve1"  # имя нормализуется через _resolve_proxmox_host_name
    assert result["backup_status"] == "success"
    assert result["raw_status"] == "backup successful"
    assert result["task_type"] == "vzdump"


def test_parse_subject_failed_status(processor) -> None:
    result = processor.parse_subject("vzdump backup status (pve2) : backup failed")
    assert result is not None
    assert result["backup_status"] == "failed"


def test_parse_subject_without_host_returns_none(processor) -> None:
    # Нет скобок с именем хоста и нет специальных подстрок pve-rubicon / pve2-rubicon
    assert processor.parse_subject("vzdump backup status : backup successful") is None


# ---- parse_duration / duration_to_seconds / seconds_to_duration -------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1h 23m 45s", "1h 23m 45s"),
        ("45m 12s", "45m 12s"),
        ("30s", "30s"),
        ("2h", "2h 00m 00s"),
        ("5m", "5m 00s"),
        ("", "0s"),
    ],
)
def test_parse_duration(processor, raw: str, expected: str) -> None:
    assert processor.parse_duration(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("45m 12s", 45 * 60 + 12),
        ("5m", 5 * 60),
        ("30s", 30),
        ("0s", 0),
        ("", 0),
    ],
)
def test_duration_to_seconds(processor, raw: str, expected: int) -> None:
    # ВАЖНО: оригинальная duration_to_seconds НЕ учитывает часы — это
    # подмеченное в монолите ограничение, тест фиксирует существующее
    # поведение, чтобы любая «нечаянная» правка вылезла наружу.
    assert processor.duration_to_seconds(raw) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        (0, "0s"),
        (45, "45s"),
        (60, "1m 00s"),
        (605, "10m 05s"),
        (3600, "1h 00m 00s"),
        (3725, "1h 02m 05s"),
    ],
)
def test_seconds_to_duration(processor, raw: int, expected: str) -> None:
    assert processor.seconds_to_duration(raw) == expected


# ---- create_schema ----------------------------------------------------------


def test_create_schema_creates_all_tables() -> None:
    """DDL должен создать ровно те таблицы, на которые рассчитывает
    остаток BackupProcessor.save_* методов."""
    from modules.mail_parts.db.schema import create_schema

    conn = sqlite3.connect(":memory:")
    try:
        create_schema(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        # sqlite_sequence создаётся автоматически из-за AUTOINCREMENT —
        # отфильтровываем системные имена с префиксом sqlite_.
        tables = {row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")}
        assert tables == {
            "proxmox_backups",
            "zfs_pool_status",
            "snapshot_transfers",
            "mail_server_backups",
            "stock_load_results",
            "nas_transfers",
            "config_console_backups",
        }

        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        for expected_idx in (
            "idx_backups_host_date",
            "idx_zfs_server_date",
            "idx_snapshot_transfers_host_date",
            "idx_mail_backup_date",
            "idx_stock_load_date",
            "idx_nas_transfers_host_date",
            "idx_config_console_host_date",
        ):
            assert expected_idx in indexes, expected_idx
    finally:
        conn.close()


def test_create_schema_is_idempotent() -> None:
    """Повторный вызов create_schema не должен падать — в backups.db
    он будет вызываться при каждом старте mail-monitor.service."""
    from modules.mail_parts.db.schema import create_schema

    conn = sqlite3.connect(":memory:")
    try:
        create_schema(conn)
        create_schema(conn)
        create_schema(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master " "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        # количество таблиц остаётся стабильным (плюс sqlite_sequence фильтруем)
        assert cursor.fetchone()[0] == 7
    finally:
        conn.close()


def test_create_schema_migrates_source_name_column() -> None:
    """Старая инсталляция могла создать stock_load_results без source_name —
    create_schema должна добавить колонку через ALTER TABLE."""
    from modules.mail_parts.db.schema import create_schema

    conn = sqlite3.connect(":memory:")
    try:
        cursor = conn.cursor()
        # эмулируем «старую» версию таблицы без source_name
        cursor.execute(
            """
            CREATE TABLE stock_load_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_name TEXT NOT NULL,
                file_path TEXT,
                status TEXT NOT NULL,
                rows_count INTEGER,
                error_count INTEGER DEFAULT 0,
                error_sample TEXT,
                attachment_name TEXT,
                log_timestamp TEXT,
                email_subject TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

        create_schema(conn)

        cursor.execute("PRAGMA table_info(stock_load_results)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "source_name" in columns
    finally:
        conn.close()


# ---- config_console backup --------------------------------------------------


_CONFIG_CONSOLE_BODY = """Хост: sr-pve5
Способ доставки: ssh-rsync
Приёмник: root@sr-bup:/bup/backup/sr-pve5
Начало: 2026-05-30 03:00:01
Завершено: 2026-05-30 03:02:17
VM конфигов: 4
LXC конфигов: 9
Контейнеров с историей: 9
Файлов истории: 17
Ошибок: 1
Проблемные элементы: lxc-164/postgres
"""


def test_parse_config_console_backup_extracts_fields(processor, monkeypatch) -> None:
    """Парсер достаёт хост/статус из темы и счётчики из тела письма."""
    from extensions.extension_manager import extension_manager

    monkeypatch.setattr(extension_manager, "is_extension_enabled", lambda _id: True)

    info = processor.parse_config_console_backup(
        "Config backup sr-pve5 PARTIAL", _CONFIG_CONSOLE_BODY
    )
    assert info is not None
    assert info["host_name"] == "sr-pve5"
    assert info["status"] == "PARTIAL"
    assert info["delivery_method"] == "ssh-rsync"
    assert info["receiver"] == "root@sr-bup:/bup/backup/sr-pve5"
    assert info["vm_config_count"] == 4
    assert info["lxc_config_count"] == 9
    assert info["history_container_count"] == 9
    assert info["history_file_count"] == 17
    assert info["error_count"] == 1
    assert info["problem_items"] == "lxc-164/postgres"


def test_parse_config_console_backup_disabled_returns_none(processor, monkeypatch) -> None:
    """При выключенном расширении парсер ничего не возвращает."""
    from extensions.extension_manager import extension_manager

    monkeypatch.setattr(extension_manager, "is_extension_enabled", lambda _id: False)
    assert (
        processor.parse_config_console_backup(
            "Config backup sr-pve5 OK", _CONFIG_CONSOLE_BODY
        )
        is None
    )


def test_parse_email_file_dispatches_config_console(processor, monkeypatch, tmp_path) -> None:
    """Полный путь: письмо проходит через parse_email_file и пишется в БД."""
    import sqlite3 as _sqlite3
    from pathlib import Path

    from extensions.extension_manager import extension_manager

    monkeypatch.setattr(extension_manager, "is_extension_enabled", lambda _id: True)

    eml = (
        "From: root@sr-pve5\nTo: katok@202020.ru\n"
        "Subject: Config backup sr-pve5 PARTIAL\n"
        "Date: Fri, 30 May 2026 03:02:17 +0700\n"
        "Content-Type: text/plain; charset=utf-8\n\n" + _CONFIG_CONSOLE_BODY
    )
    eml_path = Path(tmp_path) / "msg.eml"
    eml_path.write_text(eml, encoding="utf-8")

    result = processor.parse_email_file(eml_path)
    assert result and "config_console_backup" in result

    conn = _sqlite3.connect(str(processor.db_path))
    try:
        row = conn.execute(
            "SELECT host_name, status, lxc_config_count, error_count "
            "FROM config_console_backups WHERE host_name = ?",
            ("sr-pve5",),
        ).fetchone()
        assert row == ("sr-pve5", "PARTIAL", 9, 1)
    finally:
        conn.close()


def test_save_config_console_backup_is_idempotent(monkeypatch) -> None:
    """INSERT OR IGNORE не плодит дублей при повторной обработке письма."""
    import sqlite3 as _sqlite3
    from datetime import datetime

    from extensions.extension_manager import extension_manager
    from modules.mail_parts.processor import BackupProcessor

    monkeypatch.setattr(extension_manager, "is_extension_enabled", lambda _id: True)

    proc = BackupProcessor()
    info = proc.parse_config_console_backup(
        "Config backup sr-pve5 PARTIAL", _CONFIG_CONSOLE_BODY
    )
    email_date = datetime(2026, 5, 30, 3, 2, 17)
    proc.save_config_console_backup(info, "Config backup sr-pve5 PARTIAL", email_date)
    proc.save_config_console_backup(info, "Config backup sr-pve5 PARTIAL", email_date)

    conn = _sqlite3.connect(str(proc.db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM config_console_backups WHERE host_name = ?",
            ("sr-pve5",),
        )
        assert cursor.fetchone()[0] == 1
    finally:
        conn.close()
