"""
/modules/mail_parts/parsers/mail.py
Server Monitoring System v8.62.59
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
MailBackupParserMixin — часть BackupProcessor (PR6c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.59
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin MailBackupParserMixin; объединяется с другими mixin'ами в BackupProcessor.
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


class MailBackupParserMixin:
    """Mixin MailBackupParserMixin — методы для одного типа писем-отчётов."""

    def parse_mail_backup(self, subject: str) -> dict | None:
        """Парсит результат бэкапа почтового сервера из темы письма."""
        if not extension_manager.is_extension_enabled("mail_backup_monitor"):
            return None

        default_pattern = (
            r"^\s*бэкап\s+zimbra\s*-\s*"
            r"(?P<size>\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?)\s+"
            r"(?P<path>/\S+)\s*$"
        )
        patterns = get_mail_patterns_from_config()
        if not patterns:
            patterns = [default_pattern]

        match = None
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                break

        if not match:
            return None

        match_groups = match.groupdict()
        size = match_groups.get("size")
        path = match_groups.get("path")
        if size is None and match.lastindex and match.lastindex >= 1:
            size = match.group(1)
        if path is None and match.lastindex and match.lastindex >= 2:
            path = match.group(2)

        size = size.strip() if isinstance(size, str) else None
        path = path.strip() if isinstance(path, str) else None

        logger.info("✅ Найден бэкап Zimbra: размер=%s, путь=%s", size, path)
        return {
            "host_name": "zimbra",
            "backup_status": "success",
            "task_type": "mail_backup",
            "total_size": size,
            "backup_path": path,
        }

    def save_mail_backup(
        self,
        backup_info: dict,
        subject: str,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет результат бэкапа почтового сервера."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            received_at = (
                email_date.strftime("%Y-%m-%d %H:%M:%S")
                if email_date
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            cursor.execute(
                """
                INSERT OR IGNORE INTO mail_server_backups
                (host_name, backup_status, total_size, backup_path, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    backup_info["host_name"],
                    backup_info["backup_status"],
                    backup_info.get("total_size"),
                    backup_info.get("backup_path"),
                    subject[:500],
                    received_at,
                ),
            )

            conn.commit()
            logger.info(
                "✅ Сохранен бэкап почтового сервера: %s (%s)",
                backup_info.get("total_size") or "неизвестно",
                backup_info.get("backup_path") or "без пути",
            )

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения бэкапа почтового сервера: {exc}")
        finally:
            if "conn" in locals():
                conn.close()
