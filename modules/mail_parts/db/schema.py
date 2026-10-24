"""
/modules/mail_parts/db/schema.py
Server Monitoring System v8.67.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
SQL DDL for backups.db extracted from BackupProcessor.init_database
(PR6b серии оптимизации).
Система мониторинга серверов
Версия: 8.67.0
Автор: Александр Суханов (c)
Лицензия: MIT
DDL таблиц backups.db (`proxmox_backups`, `zfs_pool_status`,
`snapshot_transfers`, `mail_server_backups`, `stock_load_results`,
`nas_transfers`, `ids_*` расширения ids_cert_monitor), их индексов и однократной миграции колонки
`source_name` для старых инсталляций. Отделено от логики `BackupProcessor`, чтобы:
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

NAS_TRANSFERS_DDL = """
CREATE TABLE IF NOT EXISTS nas_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    status TEXT NOT NULL,
    nas_mounted INTEGER DEFAULT 0,
    started_at_text TEXT,
    completed_at_text TEXT,
    bases_processed INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    problem_bases TEXT,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host_name, started_at_text, completed_at_text, received_at)
)
"""

CONFIG_CONSOLE_BACKUPS_DDL = """
CREATE TABLE IF NOT EXISTS config_console_backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_name TEXT NOT NULL,
    status TEXT NOT NULL,
    delivery_method TEXT,
    receiver TEXT,
    started_at_text TEXT,
    completed_at_text TEXT,
    vm_config_count INTEGER DEFAULT 0,
    lxc_config_count INTEGER DEFAULT 0,
    history_container_count INTEGER DEFAULT 0,
    history_file_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    problem_items TEXT,
    email_subject TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host_name, started_at_text, completed_at_text, received_at)
)
"""

# IDS/CERT (расширение ids_cert_monitor): журнал писем, текущее состояние
# проблем, сигналы жизни IDS, сроки сертификатов и очередь оповещений.
# Письма разбирает mail-monitor, а рассылает основной цикл — очередь
# `ids_outbox` связывает два процесса и переживает перезапуск.
IDS_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS ids_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL UNIQUE,
    source TEXT,
    level TEXT,
    node TEXT,
    ct TEXT,
    event TEXT,
    family TEXT,
    problem_key TEXT,
    fields TEXT,
    details TEXT,
    subject TEXT,
    event_time TIMESTAMP,
    received_at TIMESTAMP,
    outcome TEXT
)
"""

IDS_STATE_DDL = """
CREATE TABLE IF NOT EXISTS ids_state (
    problem_key TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    node TEXT NOT NULL,
    ct TEXT NOT NULL,
    family TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'OK',
    since TIMESTAMP,
    last_event_at TIMESTAMP,
    last_event TEXT,
    last_subject TEXT,
    last_fields TEXT,
    last_details TEXT,
    last_notified_at TIMESTAMP,
    acknowledged INTEGER DEFAULT 0,
    ack_by TEXT,
    ack_at TIMESTAMP
)
"""

IDS_HEARTBEAT_DDL = """
CREATE TABLE IF NOT EXISTS ids_heartbeat (
    source_key TEXT PRIMARY KEY,
    node TEXT NOT NULL,
    ct TEXT NOT NULL,
    last_at TIMESTAMP NOT NULL,
    level TEXT,
    fields TEXT
)
"""

IDS_CERT_UNTIL_DDL = """
CREATE TABLE IF NOT EXISTS ids_cert_until (
    source_key TEXT PRIMARY KEY,
    node TEXT NOT NULL,
    ct TEXT NOT NULL,
    until_date TEXT NOT NULL,
    updated_at TIMESTAMP
)
"""

IDS_OUTBOX_DDL = """
CREATE TABLE IF NOT EXISTS ids_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL,
    level TEXT NOT NULL,
    kind TEXT,
    problem_key TEXT,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP
)
"""

INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS idx_backups_host_date ON proxmox_backups(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_zfs_server_date ON zfs_pool_status(server_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_snapshot_transfers_host_date "
    "ON snapshot_transfers(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_mail_backup_date ON mail_server_backups(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_stock_load_date ON stock_load_results(received_at)",
    "CREATE INDEX IF NOT EXISTS idx_nas_transfers_host_date "
    "ON nas_transfers(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_config_console_host_date "
    "ON config_console_backups(host_name, received_at)",
    "CREATE INDEX IF NOT EXISTS idx_ids_events_time ON ids_events(event_time)",
    "CREATE INDEX IF NOT EXISTS idx_ids_events_key ON ids_events(problem_key, event_time)",
    "CREATE INDEX IF NOT EXISTS idx_ids_outbox_status ON ids_outbox(status, id)",
)

TABLE_DDLS = (
    PROXMOX_BACKUPS_DDL,
    ZFS_POOL_STATUS_DDL,
    SNAPSHOT_TRANSFERS_DDL,
    MAIL_SERVER_BACKUPS_DDL,
    STOCK_LOAD_RESULTS_DDL,
    NAS_TRANSFERS_DDL,
    CONFIG_CONSOLE_BACKUPS_DDL,
    IDS_EVENTS_DDL,
    IDS_STATE_DDL,
    IDS_HEARTBEAT_DDL,
    IDS_CERT_UNTIL_DDL,
    IDS_OUTBOX_DDL,
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
    "CONFIG_CONSOLE_BACKUPS_DDL",
    "INDEX_STATEMENTS",
    "IDS_CERT_UNTIL_DDL",
    "IDS_EVENTS_DDL",
    "IDS_HEARTBEAT_DDL",
    "IDS_OUTBOX_DDL",
    "IDS_STATE_DDL",
    "MAIL_SERVER_BACKUPS_DDL",
    "NAS_TRANSFERS_DDL",
    "PROXMOX_BACKUPS_DDL",
    "SNAPSHOT_TRANSFERS_DDL",
    "STOCK_LOAD_RESULTS_DDL",
    "TABLE_DDLS",
    "ZFS_POOL_STATUS_DDL",
    "create_schema",
]
