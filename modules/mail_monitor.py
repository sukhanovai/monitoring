"""
/modules/mail_monitor.py
Server Monitoring System v8.3.23
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mailbox monitoring
Система мониторинга серверов
Версия: 8.3.23
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг почтового ящика
"""

from __future__ import annotations

import ast
import email.policy
import json
import fnmatch
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
    MAILDIR_CUR,
    MAILDIR_NEW,
    MAIL_MONITOR_LOG_FILE,
    ZFS_SERVERS,
)
from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from extensions.supplier_stock_files import (
    cleanup_supplier_stock_archives,
    get_supplier_stock_config,
    process_supplier_stock_file,
    unpack_archive_file,
)
from lib.logging import setup_logging

LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logging("mail_monitor", log_file=MAIL_MONITOR_LOG_FILE)


def get_database_patterns_from_config() -> dict[str, list[str]]:
    """Правильно извлекает паттерны из конфигурации."""
    try:
        all_patterns = BACKUP_PATTERNS

        if isinstance(all_patterns, str):
            try:
                import json

                all_patterns = json.loads(all_patterns)
            except Exception:
                logger.error("❌ Не удалось распарсить BACKUP_PATTERNS как JSON")
                return {"company": [], "barnaul": [], "client": [], "yandex": []}

        if not isinstance(all_patterns, dict):
            logger.error(f"❌ BACKUP_PATTERNS не словарь: {type(all_patterns)}")
            return {"company": [], "barnaul": [], "client": [], "yandex": []}

        db_patterns = all_patterns.get("database", {})

        if isinstance(db_patterns, list):
            result: dict[str, list[str]] = {}
            for item in db_patterns:
                if isinstance(item, dict):
                    for key, value in item.items():
                        result[key] = value
                else:
                    logger.warning(
                        "⚠️ Неверный формат элемента в database паттернах: %s",
                        item,
                    )
        elif isinstance(db_patterns, dict):
            result = db_patterns
        else:
            result = {}

        return {
            "company": result.get("company", []),
            "barnaul": result.get("barnaul", []),
            "client": result.get("client", []),
            "yandex": result.get("yandex", []),
        }

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов: {exc}")
        return {"company": [], "barnaul": [], "client": [], "yandex": []}


DATABASE_BACKUP_PATTERNS = get_database_patterns_from_config()

logger.info(
    "🔍 Итоговые паттерны company: %s",
    DATABASE_BACKUP_PATTERNS.get("company", []),
)
logger.info(
    "🔍 Итоговые паттерны barnaul: %s",
    DATABASE_BACKUP_PATTERNS.get("barnaul", []),
)
logger.info(
    "🔍 Итоговые паттерны client: %s",
    DATABASE_BACKUP_PATTERNS.get("client", []),
)
logger.info(
    "🔍 Итоговые паттерны yandex: %s",
    DATABASE_BACKUP_PATTERNS.get("yandex", []),
)


def get_zfs_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем ZFS из таблицы паттернов."""
    try:
        patterns = config_manager.get_backup_patterns()
        zfs_patterns = patterns.get("zfs", {})
        subject_patterns: list[str] = []

        if isinstance(zfs_patterns, dict):
            subject_patterns = zfs_patterns.get("subject", [])
        elif isinstance(zfs_patterns, list):
            subject_patterns = zfs_patterns

        if not subject_patterns:
            fallback = BACKUP_PATTERNS.get("zfs", {})
            if isinstance(fallback, dict):
                subject_patterns = fallback.get("subject", [])
            elif isinstance(fallback, list):
                subject_patterns = fallback

        return [pattern for pattern in subject_patterns if isinstance(pattern, str)]

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения ZFS паттернов: {exc}")
        return []


def get_mail_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем о бэкапах почты из таблицы паттернов."""
    try:
        patterns = config_manager.get_backup_patterns()
        mail_patterns = patterns.get("mail", {})
        subject_patterns: list[str] = []

        if isinstance(mail_patterns, dict):
            subject_patterns = mail_patterns.get("subject", [])
        elif isinstance(mail_patterns, list):
            subject_patterns = mail_patterns

        if not subject_patterns:
            fallback = BACKUP_PATTERNS.get("mail", {})
            if isinstance(fallback, dict):
                subject_patterns = fallback.get("subject", [])
            elif isinstance(fallback, list):
                subject_patterns = fallback

        return [pattern for pattern in subject_patterns if isinstance(pattern, str)]

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов почты: {exc}")
        return []


def get_stock_load_patterns_from_config() -> dict[str, list[str]]:
    """Извлекает паттерны для логов загрузки остатков из настроек."""
    try:
        patterns = config_manager.get_backup_patterns()
        if isinstance(patterns, str):
            try:
                import json

                patterns = json.loads(patterns)
            except Exception:
                patterns = {}
        if not isinstance(patterns, dict):
            patterns = {}
        if not patterns:
            fallback_raw = config_manager.get_setting("BACKUP_PATTERNS", BACKUP_PATTERNS)
            if isinstance(fallback_raw, str):
                try:
                    import json

                    fallback_raw = json.loads(fallback_raw)
                except Exception:
                    fallback_raw = {}
            if isinstance(fallback_raw, dict):
                patterns = fallback_raw
        stock_patterns = patterns.get("stock_load", {})

        def _normalize_list(value: object) -> list[str]:
            if isinstance(value, list):
                return [item for item in value if isinstance(item, str)]
            if isinstance(value, str):
                return [value]
            return []

        def _strip_named_groups(patterns: list[str]) -> list[str]:
            sanitized: list[str] = []
            for pattern in patterns:
                sanitized.append(re.sub(r"\(\?P<[^>]+>", "(?:", pattern))
            return sanitized

        normalized: dict[str, list[str]] = {
            "subject": [],
            "attachment": [],
            "file_entry": [],
            "success": [],
            "ignore": [],
            "failure": [],
        }
        sources: list[dict] = []

        if isinstance(stock_patterns, dict):
            for key in normalized:
                normalized[key] = _normalize_list(stock_patterns.get(key))
            raw_sources = stock_patterns.get("sources", [])
            if isinstance(raw_sources, list):
                sources = [item for item in raw_sources if isinstance(item, dict)]
        elif isinstance(stock_patterns, list):
            normalized["subject"] = _normalize_list(stock_patterns)

        source_from_db = []
        if isinstance(stock_patterns, dict):
            for key, patterns_list in stock_patterns.items():
                if not isinstance(key, str) or not key.startswith("source:"):
                    continue
                name = key.split("source:", 1)[1].strip()
                if not name:
                    continue
                source_from_db.append(
                    {
                        "name": name,
                        "subject": _normalize_list(patterns_list),
                    }
                )
        if source_from_db:
            sources = source_from_db

        if normalized["subject"]:
            normalized["subject"] = _strip_named_groups(normalized["subject"])

        if not any(normalized.values()):
            from config import settings as defaults

            fallback = defaults.BACKUP_PATTERNS.get("stock_load", {})
            if isinstance(fallback, dict):
                for key in normalized:
                    normalized[key] = _normalize_list(fallback.get(key))
                fallback_sources = fallback.get("sources", [])
                if isinstance(fallback_sources, list):
                    sources = [item for item in fallback_sources if isinstance(item, dict)]
        else:
            from config import settings as defaults

            fallback = defaults.BACKUP_PATTERNS.get("stock_load", {})
            if isinstance(fallback, dict):
                for key in normalized:
                    if not normalized[key]:
                        normalized[key] = _normalize_list(fallback.get(key))
        if normalized["subject"]:
            normalized["subject"] = _strip_named_groups(normalized["subject"])

        from config import settings as defaults

        default_sources = defaults.BACKUP_PATTERNS.get("stock_load", {}).get("sources", [])
        if not isinstance(default_sources, list):
            default_sources = []

        if sources:
            for source in sources:
                if not isinstance(source, dict):
                    continue
                subject_patterns = _normalize_list(source.get("subject"))
                source["subject"] = _strip_named_groups(subject_patterns)
        else:
            sources = []

        default_by_name = {
            str(item.get("name") or "").strip(): item
            for item in default_sources
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        }
        existing_names = {str(item.get("name") or "").strip() for item in sources if isinstance(item, dict)}
        for name, source in default_by_name.items():
            if name not in existing_names:
                subject_patterns = _normalize_list(source.get("subject"))
                sources.append(
                    {
                        "name": name,
                        "subject": _strip_named_groups(subject_patterns),
                    }
                )

        if not sources:
            sources = [
                {
                    "name": "Основное предприятие",
                    "subject": normalized.get("subject", []),
                }
            ]
        normalized["sources"] = sources

        return normalized
    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов остатков: {exc}")
        return {
            "subject": [],
            "attachment": [],
            "file_entry": [],
            "success": [],
            "ignore": [],
            "failure": [],
            "sources": [],
        }


class BackupProcessor:
    """Обработчик бэкапов."""

    def __init__(self) -> None:
        self.db_path = BACKUP_DATABASE_CONFIG["backups_db"]
        self.processed_files: set[str] = set()
        self.init_database()

    def init_database(self) -> None:
        """Инициализация базы данных."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
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
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_backups_host_date
                ON proxmox_backups(host_name, received_at)
            """
            )

            cursor.execute(
                """
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
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_zfs_server_date
                ON zfs_pool_status(server_name, received_at)
            """
            )

            cursor.execute(
                """
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
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_mail_backup_date
                ON mail_server_backups(host_name, received_at)
            """
            )

            cursor.execute(
                """
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
            )

            cursor.execute("PRAGMA table_info(stock_load_results)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if "source_name" not in existing_columns:
                cursor.execute("ALTER TABLE stock_load_results ADD COLUMN source_name TEXT")

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_load_date
                ON stock_load_results(received_at)
            """
            )

            conn.commit()
            conn.close()
            logger.info("База данных бэкапов инициализирована")

        except Exception as exc:
            logger.error(f"Ошибка инициализации БД: {exc}")
            raise

    def process_new_emails(self) -> int:
        """Обрабатывает новые письма из директории new."""
        maildir_new = MAILDIR_NEW
        maildir_cur = MAILDIR_CUR

        if not maildir_new.exists():
            logger.error(f"Директория не существует: {maildir_new}")
            return 0

        processed_count = 0
        for file_path in maildir_new.iterdir():
            if not file_path.is_file():
                continue

            logger.info(f"🔍 Обнаружено новое письмо: {file_path.name}")

            result = self.parse_email_file(file_path)

            if result:
                try:
                    new_path = maildir_cur / file_path.name
                    shutil.move(str(file_path), str(new_path))
                    logger.info(f"✅ Письмо перемещено в cur: {file_path.name}")
                    self.processed_files.add(str(new_path))
                except Exception as exc:
                    logger.error(f"❌ Ошибка перемещения письма: {exc}")
                    self.processed_files.add(str(file_path))

                processed_count += 1
            else:
                logger.warning(f"⚠️ Не удалось обработать письмо: {file_path.name}")
                try:
                    new_path = maildir_cur / file_path.name
                    shutil.move(str(file_path), str(new_path))
                    self.processed_files.add(str(new_path))
                except Exception as exc:
                    logger.error(f"❌ Ошибка перемещения непрочитанного письма: {exc}")

        return processed_count

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
                    error_value = match.group(2) if match.groups() and len(match.groups()) > 1 else None
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

    def save_database_backup(self, backup_info: dict, subject: str, email_date: datetime | None = None) -> None:
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

    def _match_subject_patterns(self, subject: str, patterns: list[str]) -> bool:
        """Проверяет тему письма по списку паттернов."""
        normalized_subject = re.sub(r"\s+", " ", subject).strip()
        for pattern in patterns:
            try:
                if re.search(pattern, subject, re.IGNORECASE):
                    return True
                if normalized_subject != subject and re.search(pattern, normalized_subject, re.IGNORECASE):
                    return True
            except re.error as exc:
                logger.warning("⚠️ Некорректный паттерн '%s': %s", pattern, exc)
        return False

    def _decode_attachment_payload(self, payload: bytes | None) -> str:
        """Пытается декодировать содержимое вложения."""
        if not payload:
            return ""

        for encoding in ("utf-8", "cp1251", "windows-1251", "latin-1"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue

        return payload.decode("utf-8", errors="ignore")

    def _match_regex(self, pattern: str, value: str) -> bool:
        try:
            return bool(re.search(pattern, value, re.IGNORECASE))
        except re.error as exc:
            logger.warning("⚠️ Некорректный паттерн '%s': %s", pattern, exc)
        return False

    def _normalize_rule_pattern(self, value: str) -> str:
        cleaned = str(value or "").strip()
        if not cleaned:
            return ""
        if cleaned[0] in ("'", '"') and cleaned[-1:] == cleaned[0]:
            cleaned = cleaned[1:-1].strip()
        return cleaned

    def _normalize_match_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip()).lower()

    def _decode_header_value(self, value: str | None) -> str:
        if not value:
            return ""
        try:
            parts = decode_header(value)
        except Exception:
            return str(value)
        decoded = []
        for payload, encoding in parts:
            if isinstance(payload, bytes):
                decoded.append(payload.decode(encoding or "utf-8", errors="ignore"))
            else:
                decoded.append(str(payload))
        return "".join(decoded).strip()

    def _get_attachment_filename(self, part) -> str:
        filename = part.get_filename() or part.get_param("name", header="content-type")
        return self._decode_header_value(filename)

    def _match_rule_pattern(self, pattern: str, value: str) -> bool:
        cleaned = self._normalize_rule_pattern(pattern)
        if not cleaned:
            return True
        if cleaned.lower().startswith("re:"):
            return self._match_regex(cleaned[3:].strip(), value)
        fragments = [part.strip() for part in cleaned.split("|") if part.strip()]
        if not fragments:
            return True
        haystack = self._normalize_match_text(value)
        for fragment in fragments:
            needle = self._normalize_match_text(fragment)
            if not needle:
                continue
            if any(char in needle for char in ("*", "?")):
                if fnmatch.fnmatch(haystack, needle):
                    return True
                continue
            if needle in haystack:
                return True
        return False

    def _get_sender_candidates(self, msg) -> list[str]:
        from_header = msg.get("from", "") or ""
        addresses = [addr for _, addr in getaddresses([from_header]) if addr]
        candidates = [from_header, *addresses]
        return [candidate.strip() for candidate in candidates if candidate.strip()]

    def _append_date_suffix(self, filename: str, timestamp: datetime) -> str:
        path = Path(filename)
        stamp = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{path.stem}_{stamp}{path.suffix}"

    def _resolve_attachment_name(self, source: dict, filename: str) -> str:
        base_name = Path(filename).stem if filename else "attachment"
        aliases = source.get("filename_aliases") or {}
        if isinstance(aliases, dict):
            for pattern, alias in aliases.items():
                if not pattern:
                    continue
                if self._match_rule_pattern(str(pattern), filename) or self._match_rule_pattern(
                    str(pattern),
                    base_name,
                ):
                    return str(alias)
        return base_name

    def _resolve_filename_aliases(self, source: dict, filename_pattern: str) -> tuple[dict | None, str]:
        aliases = source.get("filename_aliases")
        if isinstance(aliases, dict):
            return aliases, filename_pattern
        if isinstance(filename_pattern, dict):
            return filename_pattern, ""
        if isinstance(filename_pattern, str):
            trimmed = filename_pattern.strip()
            if trimmed.startswith("{") and trimmed.endswith("}"):
                try:
                    parsed = json.loads(trimmed)
                except json.JSONDecodeError:
                    parsed = None
                if not isinstance(parsed, dict):
                    try:
                        parsed = ast.literal_eval(trimmed)
                    except (ValueError, SyntaxError):
                        parsed = None
                if isinstance(parsed, dict):
                    return parsed, ""
        return None, filename_pattern

    def _build_attachment_output_name(
        self,
        template: str,
        filename: str,
        index: int,
        name_override: str | None = None,
    ) -> str:
        base_name = Path(filename).stem if filename else "attachment"
        name_value = name_override or base_name
        try:
            return template.format(index=index, name=name_value, filename=filename, stem=base_name)
        except Exception:
            return template or filename or f"attachment_{index}"

    def _extract_matching_attachments(
        self,
        msg,
        filename_patterns: list[str],
    ) -> list[dict]:
        """Возвращает список вложений, подходящих под паттерны имени файла."""
        matched: list[dict] = []
        if not msg.is_multipart():
            return matched

        for part in msg.walk():
            filename = self._get_attachment_filename(part)
            if not filename:
                continue
            if filename_patterns and not self._match_subject_patterns(
                filename,
                filename_patterns,
            ):
                continue

            payload = part.get_payload(decode=True)
            content = self._decode_attachment_payload(payload)
            matched.append(
                {
                    "filename": filename,
                    "content": content,
                }
            )

        return matched

    def parse_supplier_stock_email(
        self,
        subject: str,
        msg,
        email_date: datetime | None,
    ) -> dict | None:
        """Парсит письма с файлами остатков поставщиков."""
        if not extension_manager.is_extension_enabled("supplier_stock_files"):
            return None

        config = get_supplier_stock_config()
        mail_config = config.get("mail", {})
        if not mail_config.get("enabled"):
            return None

        sources = mail_config.get("sources", [])
        if not isinstance(sources, list) or not sources:
            return None

        now = email_date or datetime.now()
        temp_dir = Path(mail_config.get("temp_dir") or "")
        temp_dir.mkdir(parents=True, exist_ok=True)

        sender_candidates = self._get_sender_candidates(msg)
        matched_files: list[str] = []

        for source in sources:
            if not isinstance(source, dict):
                continue
            if not source.get("enabled", True):
                continue

            sender_pattern = source.get("sender_pattern") or ""
            if sender_pattern:
                if not any(
                    self._match_rule_pattern(sender_pattern, candidate)
                    for candidate in sender_candidates
                ):
                    continue

            subject_pattern = source.get("subject_pattern") or ""
            if subject_pattern and not self._match_rule_pattern(subject_pattern, subject):
                continue

            expected = int(source.get("expected_attachments") or 1)
            mime_pattern = source.get("mime_pattern") or "application/"
            raw_filename_pattern = source.get("filename_pattern") or ""
            filename_aliases, filename_pattern = self._resolve_filename_aliases(
                source,
                str(raw_filename_pattern),
            )
            output_template = str(source.get("output_template") or "").strip()
            source_context = dict(source)
            if filename_aliases:
                source_context["filename_aliases"] = filename_aliases

            collected = 0
            if not msg.is_multipart():
                continue

            for part in msg.walk():
                filename = self._get_attachment_filename(part)
                if not filename:
                    continue

                content_type = part.get_content_type() or ""
                if mime_pattern and not self._match_rule_pattern(mime_pattern, content_type):
                    continue

                if filename_pattern and not self._match_rule_pattern(filename_pattern, filename):
                    continue

                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                output_name = filename
                if output_template:
                    name_override = self._resolve_attachment_name(source_context, filename)
                    output_name = self._build_attachment_output_name(
                        output_template,
                        filename,
                        collected + 1,
                        name_override,
                    )
                output_path = temp_dir / output_name
                output_path.write_bytes(payload)
                original_path = output_path

                if source.get("unpack_archive"):
                    unpacked_path = unpack_archive_file(output_path)
                    if unpacked_path:
                        output_path = unpacked_path
                        logger.info(
                            "📦 Вложение поставщика распаковано: %s -> %s",
                            filename,
                            output_path,
                        )
                processing_result = process_supplier_stock_file(
                    output_path,
                    source.get("id") or source.get("name"),
                    "mail",
                    collected + 1,
                    original_path,
                )
                if processing_result:
                    logger.info(
                        "🧩 Обработка остатков выполнена: %s",
                        processing_result.get("rules"),
                    )

                matched_files.append(str(output_path))
                collected += 1

                logger.info(
                    "📦 Сохранено вложение поставщика: %s -> %s",
                    filename,
                    output_path,
                )

                if collected >= expected:
                    break

            if collected < expected:
                logger.warning(
                    "⚠️ Для правила '%s' найдено %s/%s вложений",
                    source.get("name") or source.get("id") or "без имени",
                    collected,
                    expected,
                )

        if not matched_files:
            logger.info(
                "📭 Письмо не соответствует правилам остатков поставщиков: %s",
                subject[:80],
            )
            return None

        cleanup_supplier_stock_archives(config, now)
        return {"supplier_stock_files": matched_files}

    def _match_stock_load_source(self, subject: str, patterns: dict[str, list[str]]) -> str:
        """Определяет источник отчёта по теме письма."""
        sources = patterns.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                name = str(source.get("name") or "").strip()
                if not name:
                    continue
                subject_patterns = source.get("subject", [])
                if not isinstance(subject_patterns, list):
                    continue
                if self._match_subject_patterns(subject, subject_patterns):
                    return name
        return "Основное предприятие"

    def parse_stock_load_log(
        self,
        content: str,
        patterns: dict[str, list[str]],
    ) -> list[dict]:
        """Парсит содержимое лога загрузки остатков."""
        file_entry_patterns = patterns.get("file_entry", [])
        success_patterns = patterns.get("success", [])
        failure_patterns = patterns.get("failure", [])
        ignore_patterns = patterns.get("ignore", [])

        default_file_entry = (
            r"^\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}:\s+"
            r"(?P<supplier>.+?)\s{2,}(?P<path>(?:[A-Za-z]:\\|\\\\[^\\]+\\).+)$"
        )
        if default_file_entry not in file_entry_patterns:
            file_entry_patterns = [*file_entry_patterns, default_file_entry]

        file_entry_regexes = [re.compile(pat, re.IGNORECASE) for pat in file_entry_patterns]
        success_regexes = [re.compile(pat, re.IGNORECASE) for pat in success_patterns]
        failure_regexes = [re.compile(pat, re.IGNORECASE) for pat in failure_patterns]
        ignore_regexes = [re.compile(pat, re.IGNORECASE) for pat in ignore_patterns]

        entries: list[dict] = []
        current: dict | None = None
        fallback_entry = {
            "supplier_name": "неизвестно",
            "file_path": None,
            "rows_count": None,
            "errors": [],
            "has_success": False,
            "has_failure": False,
            "log_timestamp": None,
        }

        def finalize_current() -> None:
            nonlocal current
            if not current:
                return

            has_success = current.get("has_success", False)
            has_failure = current.get("has_failure", False)
            if has_success and has_failure:
                status = "warning"
            elif has_success:
                status = "success"
            elif has_failure:
                status = "failed"
            else:
                status = "unknown"

            current["status"] = status
            current["error_count"] = len(current.get("errors", []))
            if current.get("errors"):
                current["error_sample"] = current["errors"][0][:500]
            else:
                current["error_sample"] = None

            entries.append(current)
            current = None

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            file_match = None
            for regex in file_entry_regexes:
                file_match = regex.search(line)
                if file_match:
                    break

            if file_match:
                finalize_current()

                supplier = None
                path = None
                match_groups = file_match.groupdict()
                if match_groups:
                    supplier = match_groups.get("supplier")
                    path = match_groups.get("path")
                if supplier is None and file_match.lastindex:
                    supplier = file_match.group(1)
                if path is None and file_match.lastindex and file_match.lastindex >= 2:
                    path = file_match.group(2)

                supplier = " ".join((supplier or "").split()) or "неизвестно"
                path = path.strip() if isinstance(path, str) else None

                timestamp_match = re.match(
                    r"^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
                    line,
                )
                log_timestamp = timestamp_match.group(1) if timestamp_match else None

                current = {
                    "supplier_name": supplier,
                    "file_path": path,
                    "rows_count": None,
                    "errors": [],
                    "has_success": False,
                    "has_failure": False,
                    "log_timestamp": log_timestamp,
                }
                continue

            if not current:
                ignored = False
                for regex in ignore_regexes:
                    if regex.search(line):
                        ignored = True
                        break
                if ignored:
                    continue

                success_match = None
                for regex in success_regexes:
                    success_match = regex.search(line)
                    if success_match:
                        break

                if success_match:
                    fallback_entry["has_success"] = True
                    if fallback_entry["log_timestamp"] is None:
                        timestamp_match = re.match(
                            r"^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
                            line,
                        )
                        fallback_entry["log_timestamp"] = (
                            timestamp_match.group(1) if timestamp_match else None
                        )
                    rows_value = None
                    match_groups = success_match.groupdict()
                    if match_groups:
                        rows_value = match_groups.get("rows")
                    if rows_value is None and success_match.lastindex:
                        rows_value = success_match.group(1)
                    try:
                        fallback_entry["rows_count"] = (
                            int(str(rows_value)) if rows_value else None
                        )
                    except ValueError:
                        fallback_entry["rows_count"] = None
                    continue

                failure_match = None
                for regex in failure_regexes:
                    failure_match = regex.search(line)
                    if failure_match:
                        break

                if failure_match:
                    fallback_entry["has_failure"] = True
                    if fallback_entry["log_timestamp"] is None:
                        timestamp_match = re.match(
                            r"^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
                            line,
                        )
                        fallback_entry["log_timestamp"] = (
                            timestamp_match.group(1) if timestamp_match else None
                        )
                    fallback_entry["errors"].append(line)
                continue

            ignored = False
            for regex in ignore_regexes:
                if regex.search(line):
                    ignored = True
                    break
            if ignored:
                continue

            success_match = None
            for regex in success_regexes:
                success_match = regex.search(line)
                if success_match:
                    break

            if success_match:
                current["has_success"] = True
                rows_value = None
                match_groups = success_match.groupdict()
                if match_groups:
                    rows_value = match_groups.get("rows")
                if rows_value is None and success_match.lastindex:
                    rows_value = success_match.group(1)
                try:
                    current["rows_count"] = int(str(rows_value)) if rows_value else None
                except ValueError:
                    current["rows_count"] = None
                continue

            failure_match = None
            for regex in failure_regexes:
                failure_match = regex.search(line)
                if failure_match:
                    break

            if failure_match:
                current["has_failure"] = True
                current["errors"].append(line)
                continue

        finalize_current()

        if not entries and (fallback_entry["has_success"] or fallback_entry["has_failure"]):
            has_success = fallback_entry.get("has_success", False)
            has_failure = fallback_entry.get("has_failure", False)
            if has_success and has_failure:
                status = "warning"
            elif has_success:
                status = "success"
            elif has_failure:
                status = "failed"
            else:
                status = "unknown"

            fallback_entry["status"] = status
            fallback_entry["error_count"] = len(fallback_entry.get("errors", []))
            if fallback_entry.get("errors"):
                fallback_entry["error_sample"] = fallback_entry["errors"][0][:500]
            else:
                fallback_entry["error_sample"] = None

            entries.append(fallback_entry)

        return entries

    def save_stock_load_entries(
        self,
        entries: list[dict],
        subject: str,
        attachment_name: str | None,
        source_name: str | None,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет результаты загрузки остатков в БД."""
        if not entries:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            received_at = (
                email_date.strftime("%Y-%m-%d %H:%M:%S")
                if email_date
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            for entry in entries:
                supplier_name = entry.get("supplier_name")
                if not supplier_name or supplier_name == "неизвестно":
                    supplier_name = source_name or "неизвестно"
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO stock_load_results
                    (supplier_name, source_name, file_path, status, rows_count, error_count, error_sample,
                    attachment_name, log_timestamp, email_subject, received_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        supplier_name,
                        source_name,
                        entry.get("file_path"),
                        entry.get("status", "unknown"),
                        entry.get("rows_count"),
                        entry.get("error_count", 0),
                        entry.get("error_sample"),
                        attachment_name,
                        entry.get("log_timestamp"),
                        subject[:500],
                        received_at,
                    ),
                )

            conn.commit()
            logger.info("✅ Сохранены результаты загрузки остатков: %s", len(entries))

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения остатков в БД: {exc}")
        finally:
            if "conn" in locals():
                conn.close()

    def parse_stock_load_email(
        self,
        subject: str,
        msg,
        email_date: datetime | None,
    ) -> dict | None:
        """Парсит письмо с логами загрузки остатков."""
        if not extension_manager.is_extension_enabled("stock_load_monitor"):
            return None

        patterns = get_stock_load_patterns_from_config()
        subject_patterns = patterns.get("subject", [])
        sources = patterns.get("sources", [])
        matches_subject = (
            self._match_subject_patterns(subject, subject_patterns)
            if subject_patterns
            else True
        )
        matches_source = False
        if isinstance(sources, list) and sources:
            for source in sources:
                if not isinstance(source, dict):
                    continue
                source_subject = source.get("subject", [])
                if not isinstance(source_subject, list):
                    continue
                if self._match_subject_patterns(subject, source_subject):
                    matches_source = True
                    break

        if not matches_subject and not matches_source:
            return None

        source_name = self._match_stock_load_source(subject, patterns)

        attachment_patterns = patterns.get("attachment", [])
        attachments = self._extract_matching_attachments(msg, attachment_patterns)
        if not attachments:
            logger.warning("⚠️ Лог остатков не найден во вложениях письма: %s", subject)
            return None

        all_entries: list[dict] = []
        for attachment in attachments:
            content = attachment.get("content", "")
            entries = self.parse_stock_load_log(content, patterns)
            self.save_stock_load_entries(
                entries,
                subject,
                attachment.get("filename"),
                source_name,
                email_date,
            )
            all_entries.extend(entries)

        if not all_entries:
            logger.warning("⚠️ Не удалось извлечь результаты остатков из письма: %s", subject)
            return None

        return {"stock_load_entries": all_entries}

    def parse_email_file(self, file_path: Path) -> dict | None:
        """Парсит email файл."""
        try:
            logger.info(f"Обработка файла: {file_path}")

            msg = message_from_bytes(
                Path(file_path).read_bytes(),
                policy=email.policy.default,
            )

            subject = msg.get("subject", "")
            email_date_str = msg.get("date", "")
            logger.info(f"Тема письма: {subject}")
            logger.info(f"Дата письма: {email_date_str}")

            email_date = None
            if email_date_str:
                try:
                    email_date = parsedate_to_datetime(email_date_str)
                    logger.info(f"✅ Дата письма распарсена: {email_date}")
                except Exception as exc:
                    logger.warning(
                        "Не удалось распарсить дату письма '%s': %s",
                        email_date_str,
                        exc,
                    )
                    try:
                        email_date = datetime.strptime(
                            email_date_str,
                            "%a, %d %b %Y %H:%M:%S %z",
                        )
                        logger.info(
                            "✅ Дата письма распарсена альтернативным методом: %s",
                            email_date,
                        )
                    except Exception:
                        logger.warning(
                            "❌ Не удалось распарсить дату альтернативным методом, используем текущее время"
                        )
                        email_date = datetime.now()
            else:
                logger.warning("❌ Дата письма отсутствует, используем текущее время")
                email_date = datetime.now()

            db_backup_info = self.parse_database_backup(subject, self.get_email_body(msg))
            if db_backup_info:
                logger.info(
                    "📊 Обнаружен бэкап базы данных: %s",
                    db_backup_info["database_display_name"],
                )
                self.save_database_backup(db_backup_info, subject, email_date)
                return db_backup_info

            zfs_entries = self.parse_zfs_status(subject)
            if zfs_entries:
                self.save_zfs_status(zfs_entries, subject, email_date)
                return {"zfs_entries": zfs_entries}

            mail_backup_info = self.parse_mail_backup(subject)
            if mail_backup_info:
                self.save_mail_backup(mail_backup_info, subject, email_date)
                return mail_backup_info

            supplier_stock_info = self.parse_supplier_stock_email(subject, msg, email_date)
            if supplier_stock_info:
                return supplier_stock_info

            stock_load_info = self.parse_stock_load_email(subject, msg, email_date)
            if stock_load_info:
                return stock_load_info

            if not self.is_proxmox_backup_email(subject):
                logger.info(
                    "Пропускаем не-Proxmox/БД/ZFS/почта/остатки письмо: %s...",
                    subject[:50],
                )
                return None

            backup_info = self.parse_subject(subject)
            if not backup_info:
                logger.warning("Не удалось извлечь информацию из темы")
                return None

            body = self.get_email_body(msg)
            backup_info.update(self.parse_body(body))

            self.save_backup_report(backup_info, subject, email_date)

            return backup_info

        except Exception as exc:
            logger.error(f"Ошибка парсинга файла {file_path}: {exc}")
            return None

    def is_proxmox_backup_email(self, subject: str) -> bool:
        """Проверяет, является ли письмо отчетом о бэкапе Proxmox."""
        subject_lower = subject.lower()
        return any(
            keyword in subject_lower
            for keyword in [
                "vzdump backup status",
                "proxmox backup",
                "backup successful",
                "backup failed",
            ]
        )

    def parse_subject(self, subject: str) -> dict | None:
        """Парсит тему письма."""
        if "pve2-rubicon" in subject.lower():
            host_name = "pve2-rubicon"
            status_match = re.search(r":\s*([^:]+)$", subject)
            if status_match:
                raw_status = status_match.group(1).strip().lower()
                normalized_status = self.normalize_status(raw_status)
                return {
                    "host_name": host_name,
                    "backup_status": normalized_status,
                    "raw_status": raw_status,
                    "task_type": "vzdump",
                }

        if "pve-rubicon" in subject.lower() and "pve2-rubicon" not in subject.lower():
            host_name = "pve-rubicon"
            status_match = re.search(r":\s*([^:]+)$", subject)
            if status_match:
                raw_status = status_match.group(1).strip().lower()
                normalized_status = self.normalize_status(raw_status)
                return {
                    "host_name": host_name,
                    "backup_status": normalized_status,
                    "raw_status": raw_status,
                    "task_type": "vzdump",
                }

        host_match = re.search(r"\(([^)]+)\)", subject)
        if not host_match:
            logger.warning(f"Не удалось извлечь имя хоста: {subject}")
            return None

        host_name = host_match.group(1).split(".")[0]

        status_match = re.search(r":\s*([^:]+)$", subject)
        if not status_match:
            logger.warning(f"Не удалось извлечь статус: {subject}")
            return None

        raw_status = status_match.group(1).strip().lower()
        normalized_status = self.normalize_status(raw_status)

        return {
            "host_name": host_name,
            "backup_status": normalized_status,
            "raw_status": raw_status,
            "task_type": "vzdump",
        }

    def normalize_status(self, raw_status: str) -> str:
        """Нормализует статус бэкапа."""
        status_map = {
            "backup successful": "success",
            "successful": "success",
            "ok": "success",
            "backup failed": "failed",
            "failed": "failed",
            "error": "failed",
        }
        return status_map.get(raw_status, raw_status)

    def get_email_body(self, msg) -> str:
        """Извлекает тело письма."""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        return part.get_content()
            else:
                return msg.get_content()
        except Exception as exc:
            logger.error(f"Ошибка извлечения тела письма: {exc}")

        return ""

    def parse_body(self, body: str) -> dict:
        """Парсит тело письма для извлечения корректной информации."""
        info = {
            "duration": None,
            "total_size": None,
            "error_message": None,
            "vm_count": 0,
            "successful_vms": 0,
            "failed_vms": 0,
        }

        try:
            lines = body.split("\n")
            in_details_section = False

            for line in lines:
                line = line.strip()
                line_lower = line.lower()

                if any(
                    keyword in line_lower
                    for keyword in [
                        "total size",
                        "backup size",
                        "size:",
                        "data size",
                        "total backup",
                    ]
                ):
                    size_patterns = [
                        r"(\d+\.?\d*)\s*([TGMK]i?B)",
                        r"(\d[\d,]*\.?\d*)\s*([TGMK]i?B)",
                        r"size[:\s]+(\d+\.?\d*)\s*([TGMK]i?B)",
                    ]

                    for pattern in size_patterns:
                        size_match = re.search(pattern, line, re.IGNORECASE)
                        if size_match:
                            size_value = size_match.group(1).replace(",", "")
                            size_unit = size_match.group(2).upper()
                            info["total_size"] = f"{size_value} {size_unit}"
                            break

                if "total running time" in line_lower:
                    time_match = re.search(r"(\d+[hm]\s*\d*[sm]*)", line, re.IGNORECASE)
                    if time_match:
                        raw_time = time_match.group(1)
                        info["duration"] = self.parse_duration(raw_time)

                elif "vmid" in line_lower and "name" in line_lower and "status" in line_lower:
                    in_details_section = True
                    continue

                elif in_details_section and re.match(r"^\d+\s+", line):
                    parts = line.split()
                    if len(parts) >= 4:
                        info["vm_count"] += 1
                        status = parts[2].lower()
                        if status == "ok":
                            info["successful_vms"] += 1
                        else:
                            info["failed_vms"] += 1

                elif in_details_section and not line:
                    in_details_section = False

                elif "error" in line_lower or "failed" in line_lower:
                    if not info["error_message"] and len(line) > 10:
                        info["error_message"] = line[:200]

            if not info["duration"] and info["vm_count"] > 0:
                total_seconds = 0
                for line in lines:
                    time_match = re.search(r"(\d+m\s*\d*s)", line)
                    if time_match:
                        vm_time = time_match.group(1)
                        total_seconds += self.duration_to_seconds(vm_time)

                if total_seconds > 0:
                    info["duration"] = self.seconds_to_duration(total_seconds)

        except Exception as exc:
            logger.error(f"Ошибка парсинга тела письма: {exc}")

        return info

    def parse_duration(self, duration_str: str) -> str:
        """Парсит строку длительности в читаемый формат."""
        try:
            duration_str = duration_str.lower().replace(" ", "")

            hours = 0
            minutes = 0
            seconds = 0

            h_match = re.search(r"(\d+)h", duration_str)
            if h_match:
                hours = int(h_match.group(1))

            m_match = re.search(r"(\d+)m", duration_str)
            if m_match:
                minutes = int(m_match.group(1))

            s_match = re.search(r"(\d+)s", duration_str)
            if s_match:
                seconds = int(s_match.group(1))

            if hours > 0:
                return f"{hours}h {minutes:02d}m {seconds:02d}s"
            if minutes > 0:
                return f"{minutes}m {seconds:02d}s"
            return f"{seconds}s"

        except Exception as exc:
            logger.error(f"Ошибка парсинга длительности '{duration_str}': {exc}")
            return duration_str

    def duration_to_seconds(self, duration_str: str) -> int:
        """Конвертирует строку длительности в секунды."""
        try:
            total_seconds = 0
            duration_str = duration_str.lower().replace(" ", "")

            m_match = re.search(r"(\d+)m", duration_str)
            if m_match:
                total_seconds += int(m_match.group(1)) * 60

            s_match = re.search(r"(\d+)s", duration_str)
            if s_match:
                total_seconds += int(s_match.group(1))

            return total_seconds
        except Exception:
            return 0

    def seconds_to_duration(self, total_seconds: int) -> str:
        """Конвертирует секунды в читаемую длительность."""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        if minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        return f"{seconds}s"

    def save_backup_report(self, backup_info: dict, subject: str, email_date: datetime | None = None) -> None:
        """Сохраняет отчет в базу с корректным временем, игнорируя дубликаты."""
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
                INSERT OR IGNORE INTO proxmox_backups
                (host_name, backup_status, task_type, duration, total_size, error_message,
                email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    backup_info["host_name"],
                    backup_info["backup_status"],
                    backup_info["task_type"],
                    backup_info.get("duration"),
                    backup_info.get("total_size"),
                    backup_info.get("error_message"),
                    subject[:500],
                    received_at,
                ),
            )

            conn.commit()
            logger.info(
                "✅ Сохранен бэкап: %s - %s",
                backup_info["host_name"],
                backup_info["backup_status"],
            )

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения в БД: {exc}")
        finally:
            if "conn" in locals():
                conn.close()


def run_mail_monitor() -> int:
    """
    Запускает обработку новых писем с отчётами о бэкапах.

    Returns:
        Количество обработанных писем.
    """
    processor = BackupProcessor()
    return processor.process_new_emails()


def main() -> None:
    """Основная функция."""
    logger.info("🔄 Запуск исправленного мониторинга почты Proxmox бэкапов...")

    try:
        processor = BackupProcessor()

        logger.info("📧 Мониторинг директорий: /root/Maildir/new и /root/Maildir/cur")

        while True:
            try:
                processed = processor.process_new_emails()
                if processed > 0:
                    logger.info(f"✅ Обработано новых писем: {processed}")

                time.sleep(30)

            except Exception as exc:
                logger.error(f"❌ Ошибка в основном цикле: {exc}")
                time.sleep(60)

    except Exception as exc:
        logger.error(f"💥 Критическая ошибка: {exc}")
        raise


__all__ = ["BackupProcessor", "run_mail_monitor", "main"]


if __name__ == "__main__":
    main()
