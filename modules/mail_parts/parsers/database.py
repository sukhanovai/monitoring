"""
/modules/mail_parts/parsers/database.py
Server Monitoring System v8.62.67
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
DatabaseBackupParserMixin — часть BackupProcessor (PR6c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.67
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin DatabaseBackupParserMixin; объединяется с другими mixin'ами в BackupProcessor.
"""

from __future__ import annotations

import ast
import email.policy
import fnmatch
import json
import re
import shutil
import sqlite3
import time
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

from config.db_settings import (
    BACKUP_DATABASE_CONFIG,
    BACKUP_PATTERNS,
    DATABASE_BACKUP_CONFIG,
    LOG_DIR,
    MAIL_MONITOR_LOG_FILE,
    MAILDIR_CUR,
    MAILDIR_NEW,
    ZFS_SERVERS,
)
from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from extensions.supplier_stock_files import (
    append_supplier_stock_report,
    cleanup_supplier_stock_archives,
    get_supplier_stock_config,
    process_supplier_stock_file,
    unpack_archive_file,
)
from lib.logging import setup_logging
from modules.mail_parts import logger
from modules.mail_parts.db.schema import create_schema
from modules.mail_parts.patterns import (
    get_database_patterns_from_config,
    get_mail_patterns_from_config,
    get_snapshot_transfer_patterns_from_config,
    get_stock_load_patterns_from_config,
    get_zfs_patterns_from_config,
)


class DatabaseBackupParserMixin:
    """Mixin DatabaseBackupParserMixin — методы для одного типа писем-отчётов."""

    def parse_database_backup(self, subject: str, body: str) -> dict | None:
        """Парсит бэкапы баз данных из темы письма."""
        try:
            logger.info(f"🎯 Парсим бэкап БД: '{subject}'")
            backup_info: dict = {}

            subject_lower = subject.lower()

            patterns = get_database_patterns_from_config()
            fallback_patterns = {
                "barnaul": [
                    r"cobian\s+brn\s+backup\s+([\w.-]+),\s*errors[:=]\s*([\w\d]+)?",
                ],
                "client": [
                    r"rubicon-1c\s+([\w.-]+)\s+dump\s+complete",
                    r"backup\s+1c7\.7\s+([\w.-]+)\s+ok",
                ],
            }

            def parse_error_count(raw_value: str | None) -> int:
                if not raw_value:
                    return 0
                digits = re.findall(r"\d+", raw_value)
                return int(digits[0]) if digits else 0

            for pattern in patterns.get("company", []):
                match = re.search(pattern, subject_lower, re.IGNORECASE)
                if match:
                    db_name = match.group(1).strip() if match.groups() else "unknown"
                    logger.info(
                        "✅ Найден бэкап company_database: '%s' по паттерну: %s",
                        db_name,
                        pattern,
                    )

                    company_dbs = DATABASE_BACKUP_CONFIG.get("company_databases", {})
                    display_name = company_dbs.get(db_name, db_name)

                    backup_info = {
                        "host_name": "sr-bup",
                        "backup_status": "success",
                        "task_type": "database_dump",
                        "database_name": db_name,
                        "database_display_name": display_name,
                        "backup_type": "company_database",
                    }
                    return backup_info

            client_patterns = patterns.get("client", []) + fallback_patterns["client"]
            for pattern in client_patterns:
                match = re.search(pattern, subject_lower, re.IGNORECASE)
                if match:
                    db_name = match.group(1).strip() if match.groups() else "unknown"
                    logger.info(
                        "✅ Найден бэкап client: '%s' по паттерну: %s",
                        db_name,
                        pattern,
                    )

                    company_dbs = DATABASE_BACKUP_CONFIG.get("company_databases", {})
                    if db_name in company_dbs:
                        display_name = company_dbs.get(db_name, db_name)
                        backup_info = {
                            "host_name": "sr-bup",
                            "backup_status": "success",
                            "task_type": "database_dump",
                            "database_name": db_name,
                            "database_display_name": display_name,
                            "backup_type": "company_database",
                        }
                        return backup_info

                    client_dbs = DATABASE_BACKUP_CONFIG.get("client_databases", {})
                    display_name = client_dbs.get(db_name, db_name)

                    backup_info = {
                        "host_name": "kc-1c" if "kc-1c" in subject_lower else "rubicon-1c",
                        "backup_status": "success",
                        "task_type": "client_database_dump",
                        "database_name": db_name,
                        "database_display_name": display_name,
                        "backup_type": "client",
                    }
                    return backup_info

            barnaul_patterns = patterns.get("barnaul", []) + fallback_patterns["barnaul"]
            for pattern in barnaul_patterns:
                match = re.search(pattern, subject_lower, re.IGNORECASE)
                if match:
                    db_name = match.group(1).strip() if match.groups() else "unknown"
                    error_value = (
                        match.group(2) if match.groups() and len(match.groups()) > 1 else None
                    )
                    error_count = parse_error_count(error_value)
                    logger.info(
                        "✅ Найден бэкап barnaul: '%s' по паттерну: %s",
                        db_name,
                        pattern,
                    )

                    barnaul_dbs = DATABASE_BACKUP_CONFIG.get("barnaul_backups", {})
                    display_name = barnaul_dbs.get(db_name, db_name)

                    backup_info = {
                        "host_name": "brn-backup",
                        "backup_status": "success" if error_count == 0 else "failed",
                        "task_type": "cobian_backup",
                        "database_name": db_name,
                        "database_display_name": display_name,
                        "error_count": error_count,
                        "backup_type": "barnaul",
                    }
                    return backup_info

            for pattern in patterns.get("yandex", []):
                match = re.search(pattern, subject_lower, re.IGNORECASE)
                if match:
                    db_name = match.group(1).strip().upper() if match.groups() else "UNKNOWN"
                    logger.info(
                        "✅ Найден бэкап yandex: '%s' по паттерну: %s",
                        db_name,
                        pattern,
                    )

                    yandex_dbs = DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
                    display_name = yandex_dbs.get(db_name, db_name)

                    backup_info = {
                        "host_name": "yandex-backup",
                        "backup_status": "success",
                        "task_type": "yandex_backup",
                        "database_name": db_name,
                        "database_display_name": display_name,
                        "backup_type": "yandex",
                    }
                    return backup_info

            logger.info(f"❌ Ни один паттерн не подошел для темы: '{subject}'")
            return None

        except Exception as exc:
            logger.error(f"💥 Ошибка в parse_database_backup: {exc}")
            import traceback

            logger.error(traceback.format_exc())
            return None

    def save_database_backup(
        self, backup_info: dict, subject: str, email_date: datetime | None = None
    ) -> None:
        """Сохраняет информацию о бэкапе базы данных, игнорируя дубликаты."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS database_backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_name TEXT NOT NULL,
                    database_name TEXT NOT NULL,
                    database_display_name TEXT,
                    backup_status TEXT NOT NULL,
                    backup_type TEXT,
                    task_type TEXT,
                    error_count INTEGER DEFAULT 0,
                    email_subject TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(host_name, database_name, received_at)
                )
            """
            )

            received_at = (
                email_date.strftime("%Y-%m-%d %H:%M:%S")
                if email_date
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            cursor.execute(
                """
                INSERT OR IGNORE INTO database_backups
                (host_name, database_name, database_display_name, backup_status, backup_type,
                task_type, error_count, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    backup_info["host_name"],
                    backup_info["database_name"],
                    backup_info.get("database_display_name"),
                    backup_info["backup_status"],
                    backup_info.get("backup_type"),
                    backup_info.get("task_type"),
                    backup_info.get("error_count", 0),
                    subject[:500],
                    received_at,
                ),
            )

            conn.commit()
            logger.info(
                "✅ Сохранен бэкап БД: %s - %s",
                backup_info["database_display_name"],
                backup_info["backup_status"],
            )

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения бэкапа БД в БД: {exc}")
        finally:
            if "conn" in locals():
                conn.close()
