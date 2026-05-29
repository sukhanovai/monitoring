"""
/modules/mail_parts/patterns.py
Server Monitoring System v8.62.66
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Pattern helpers extracted from modules/mail_monitor.py (PR6 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.66
Автор: Александр Суханов (c)
Лицензия: MIT
Сборщики regex/glob-паттернов из конфигурации БД для разных типов писем
с бэкапами: БД, ZFS, snapshot-передача, почтовый бэкап, supplier stock.
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
from modules.mail_parts import logger  # noqa: F401  — общий логгер пакета


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


def _normalize_snapshot_pattern(pattern: str) -> str:
    """Нормализует шаблон передачи снэпшотов для пользовательского ввода."""
    normalized = str(pattern or "").strip()
    if not normalized:
        return ""

    normalized = normalized.replace(".*", "__WILDCARD__")
    normalized = normalized.replace(".\*", "__WILDCARD__")
    normalized = re.sub(r"\s+", r"\\s+", normalized)
    normalized = normalized.replace("__WILDCARD__", r".*")
    return normalized


def get_snapshot_transfer_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем о передаче снэпшотов."""
    try:
        patterns = config_manager.get_backup_patterns()
        if isinstance(patterns, str):
            try:
                patterns = json.loads(patterns)
            except Exception:
                patterns = {}
        if not isinstance(patterns, dict):
            patterns = {}

        transfer_patterns = patterns.get("snapshot_transfer", {})
        subject_patterns: list[str] = []

        if isinstance(transfer_patterns, dict):
            subject_patterns = transfer_patterns.get("subject", [])
        elif isinstance(transfer_patterns, list):
            subject_patterns = transfer_patterns

        fallback_source = BACKUP_PATTERNS
        if isinstance(fallback_source, str):
            try:
                fallback_source = json.loads(fallback_source)
            except Exception:
                fallback_source = {}
        if not isinstance(fallback_source, dict):
            fallback_source = {}

        fallback = fallback_source.get("snapshot_transfer", {})
        fallback_patterns: list[str] = []
        if isinstance(fallback, dict):
            fallback_patterns = fallback.get("subject", [])
        elif isinstance(fallback, list):
            fallback_patterns = fallback

        normalized = [
            _normalize_snapshot_pattern(pattern)
            for pattern in subject_patterns
            if isinstance(pattern, str)
        ]
        normalized_fallback = [
            _normalize_snapshot_pattern(pattern)
            for pattern in fallback_patterns
            if isinstance(pattern, str)
        ]

        if not normalized:
            return normalized_fallback

        for fallback_pattern in normalized_fallback:
            if fallback_pattern not in normalized:
                normalized.append(fallback_pattern)

        return normalized
    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов передачи снэпшотов: {exc}")
        return []


def get_nas_transfer_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем о передаче бэкапов на NAS."""
    try:
        patterns = config_manager.get_backup_patterns()
        nas_patterns = patterns.get("nas_transfer", {})
        subject_patterns: list[str] = []

        if isinstance(nas_patterns, dict):
            subject_patterns = nas_patterns.get("subject", [])
        elif isinstance(nas_patterns, list):
            subject_patterns = nas_patterns

        if not subject_patterns:
            fallback = BACKUP_PATTERNS.get("nas_transfer", {})
            if isinstance(fallback, dict):
                subject_patterns = fallback.get("subject", [])
            elif isinstance(fallback, list):
                subject_patterns = fallback

        return [pattern for pattern in subject_patterns if isinstance(pattern, str)]

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов передачи на NAS: {exc}")
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
        existing_names = {
            str(item.get("name") or "").strip() for item in sources if isinstance(item, dict)
        }
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
