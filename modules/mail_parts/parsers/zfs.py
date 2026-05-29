"""
/modules/mail_parts/parsers/zfs.py
Server Monitoring System v8.62.72
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ZfsBackupParserMixin — часть BackupProcessor (PR6c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.72
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin ZfsBackupParserMixin; объединяется с другими mixin'ами в BackupProcessor.
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


class ZfsBackupParserMixin:
    """Mixin ZfsBackupParserMixin — методы для одного типа писем-отчётов."""

    def parse_zfs_status(self, subject: str) -> list[dict] | None:
        """Парсит статусы ZFS массивов из темы письма."""
        if not extension_manager.is_extension_enabled("zfs_monitor"):
            return None

        patterns = get_zfs_patterns_from_config()
        if not patterns:
            logger.info("⚠️ Паттерны ZFS не настроены")
            return None

        matched_server = None
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if not match:
                continue

            if match.groupdict().get("server"):
                matched_server = match.group("server")
            elif match.groups():
                matched_server = match.group(1)
            break

        if not matched_server:
            return None

        matched_server = matched_server.strip()
        if matched_server not in ZFS_SERVERS and matched_server.lower() in ZFS_SERVERS:
            matched_server = matched_server.lower()

        states = re.findall(r"state:\s*([A-Za-z0-9_-]+)", subject, re.IGNORECASE)
        if not states:
            logger.warning(f"⚠️ Не удалось найти статусы ZFS в теме: {subject}")
            return None

        server_config = ZFS_SERVERS.get(matched_server, {})
        if not server_config:
            logger.warning(
                "⚠️ ZFS сервер не найден в настройках: %s",
                matched_server,
            )
        if isinstance(server_config, dict) and not server_config.get("enabled", True):
            logger.info("ℹ️ ZFS сервер отключен в настройках: %s", matched_server)
            return None

        entries = []
        for index, state in enumerate(states, start=1):
            pool_name = f"pool_{index}"
            entries.append(
                {
                    "server_name": matched_server,
                    "pool_name": pool_name,
                    "pool_index": index,
                    "pool_state": state.upper(),
                }
            )

        return entries

    def save_zfs_status(
        self,
        entries: list[dict],
        subject: str,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет статусы ZFS массивов в БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            received_at = (
                email_date.strftime("%Y-%m-%d %H:%M:%S")
                if email_date
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            for entry in entries:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO zfs_pool_status
                    (server_name, pool_name, pool_index, pool_state, email_subject, received_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry["server_name"],
                        entry["pool_name"],
                        entry.get("pool_index"),
                        entry["pool_state"],
                        subject[:500],
                        received_at,
                    ),
                )

            conn.commit()
            logger.info(
                "✅ Сохранены статусы ZFS: %s (%s шт.)",
                entries[0]["server_name"] if entries else "unknown",
                len(entries),
            )

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения ZFS статуса в БД: {exc}")
        finally:
            if "conn" in locals():
                conn.close()

    def parse_snapshot_transfer(self, subject: str, body: str) -> dict | None:
        """Парсит статус передачи ZFS-снэпшотов из темы и тела письма."""
        patterns = get_snapshot_transfer_patterns_from_config()
        if not patterns:
            patterns = [
                r"^snapshots transfer (?P<host>[\w.-]+) (?P<status>STARTED|SUCCESS|SKIPPED|ERROR|BUSY)$",
            ]

        normalized_subject = " ".join((subject or "").split())

        match = None
        for pattern in patterns:
            match = re.search(pattern, normalized_subject, re.IGNORECASE)
            if match:
                logger.info(
                    "✅ Snapshot transfer: совпадение по пользовательскому паттерну: %s", pattern
                )
                break

        if not match:
            fallback_pattern = r"^snapshots transfer (?P<host>[\w.-]+) (?P<status>STARTED|SUCCESS|SKIPPED|ERROR|BUSY)$"
            match = re.search(fallback_pattern, normalized_subject, re.IGNORECASE)
            if match:
                logger.info("✅ Snapshot transfer: совпадение по fallback-паттерну")

        host_name = ""
        status = ""

        if match:
            host_name = (
                match.groupdict().get("host") or match.group(1) if match.lastindex else ""
            ).strip()
            status = (match.groupdict().get("status") or "").upper().strip()

        if not host_name or not status:
            token_match = re.search(
                r"\bsnapshots\s+transfer\s+(?P<host>[\w.-]+)\s+(?P<status>STARTED|SUCCESS|SKIPPED|ERROR|BUSY)\b",
                normalized_subject,
                re.IGNORECASE,
            )
            if token_match:
                host_name = (token_match.groupdict().get("host") or "").strip()
                status = (token_match.groupdict().get("status") or "").upper().strip()

        if not host_name or not status:
            return None

        def _extract(pattern: str) -> str | None:
            local = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if not local:
                return None
            value = local.group(1).strip()
            return value or None

        return {
            "host_name": host_name,
            "status": status,
            "snapshot_name": _extract(r"Снапшот:\s*(.+)"),
            "method": _extract(r"Метод:\s*(.+)"),
            "start_snapshot": _extract(r"Старт:\s*(.+)"),
            "size_text": _extract(r"Размер:\s*(.+)"),
            "started_at_text": _extract(r"Начало:\s*(.+)"),
            "completed_at_text": _extract(r"Завершено:\s*(.+)"),
            "duration_text": _extract(r"Длительность:\s*(.+)"),
        }

    def save_snapshot_transfer(
        self,
        transfer_info: dict,
        subject: str,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет статус передачи снэпшотов в БД."""
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
                INSERT INTO snapshot_transfers
                (host_name, status, snapshot_name, method, start_snapshot, size_text,
                 started_at_text, completed_at_text, duration_text, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transfer_info["host_name"],
                    transfer_info["status"],
                    transfer_info.get("snapshot_name"),
                    transfer_info.get("method"),
                    transfer_info.get("start_snapshot"),
                    transfer_info.get("size_text"),
                    transfer_info.get("started_at_text"),
                    transfer_info.get("completed_at_text"),
                    transfer_info.get("duration_text"),
                    subject[:500],
                    received_at,
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения статуса передачи снэпшотов: {exc}")
        finally:
            if "conn" in locals():
                conn.close()
