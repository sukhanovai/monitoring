"""
/modules/mail_parts/db/schema.py
Server Monitoring System v8.62.62
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
SQL DDL for backups.db extracted from BackupProcessor.init_database
(PR6b серии оптимизации).
Система мониторинга серверов
Версия: 8.62.62
Автор: Александр Суханов (c)
Лицензия: MIT
DDL шести таблиц backups.db (`proxmox_backups`, `zfs_pool_status`,
`snapshot_transfers`, `mail_server_backups`, `stock_load_results`),
их индексов и однократной миграции колонки `source_name` для старых
инсталляций. Отделено от логики `BackupProcessor`, чтобы:
1. SQL можно было читать целиком в одном месте;
2. unit-тесты могли поднимать схему в in-memory sqlite без побочек.
"""

from __future__ import annotations

import sqlite3

PROXMOX_BACKUPS_DDL = """
CREATE TABLE IF NOT EXISTS proxmox_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    backup_status TEXT NOT NULL,
    task_type TEXT,
    duration TEXT,
    total_size TEXT,
    error_message TEXT,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

ZFS_POOL_STATUS_DDL = """
CREATE TABLE IF NOT EXISTS zfs_pool_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_name TEXT NOT NULL,
    pool_name TEXT NOT NULL,
    pool_index INTEGER,
    pool_state TEXT NOT NULL,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(server_name, pool_name, received_at)
)
"""

SNAPSHOT_TRANSFERS_DDL = """
CREATE TABLE IF NOT EXISTS snapshot_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    status TEXT NOT NULL,
    snapshot_name TEXT,
    method TEXT,
    start_snapshot TEXT,
    size_text TEXT,
    started_at_text TEXT,
    completed_at_text TEXT,
    duration_text TEXT,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

MAIL_SERVER_BACKUPS_DDL = """
CREATE TABLE IF NOT EXISTS mail_server_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    backup_status TEXT NOT NULL,
    total_size TEXT,
    backup_path TEXT,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host_name, backup_path, received_at)
)
"""

STOCK_LOAD_RESULTS_DDL = """
CREATE TABLE IF NOT EXISTS stock_load_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    source_name TEXT,
    file_path TEXT,
    status TEXT NOT NULL,
    rows_count INTEGER,
    error_count INTEGER DEFAULT 0,
    error_sample TEXT,
    attachment_name TEXT,
    log_timestamp TEXT,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_name, file_path, log_timestamp, received_at)
)
"""

INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_backups_host_date ON proxmox_backups(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_zfs_server_date ON zfs_pool_status(server_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_snapshot_transfers_host_date "
    "ON snapshot_transfers(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_mail_backup_date ON mail_server_backups(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_stock_load_date ON stock_load_results(received_at)",
)

TABLE_DDLS = (
    PROXMOX_BACKUPS_DDL,
    ZFS_POOL_STATUS_DDL,
    SNAPSHOT_TRANSFERS_DDL,
    MAIL_SERVER_BACKUPS_DDL,
    STOCK_LOAD_RESULTS_DDL,
)


def create_schema(conn: sqlite3.Connection) -> None:
    """Создаёт таблицы и индексы backups.db, если их ещё нет.

    Также мигрирует старые инсталляции `stock_load_results` без колонки
    `source_name` — добавляет её через `ALTER TABLE`. Безопасно вызывать
    повторно: всё через `IF NOT EXISTS` и проверку `PRAGMA table_info`.
    """
    cursor = conn.cursor()

    for ddl in TABLE_DDLS:
        cursor.execute(ddl)

    cursor.execute("PRAGMA table_info(stock_load_results)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if "source_name" not in existing_columns:
        cursor.execute("ALTER TABLE stock_load_results ADD COLUMN source_name TEXT")

    for index_sql in INDEX_STATEMENTS:
        cursor.execute(index_sql)

    conn.commit()


__all__ = [
    "INDEX_STATEMENTS",
    "MAIL_SERVER_BACKUPS_DDL",
    "PROXMOX_BACKUPS_DDL",
    "SNAPSHOT_TRANSFERS_DDL",
    "STOCK_LOAD_RESULTS_DDL",
    "TABLE_DDLS",
    "ZFS_POOL_STATUS_DDL",
    "create_schema",
]
