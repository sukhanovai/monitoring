"""
/modules/mail_parts/patterns.py
Server Monitoring System v8.65.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Pattern helpers extracted from modules/mail_monitor.py (PR6 серии оптимизации).
Система мониторинга серверов
Версия: 8.65.2
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

# Категории таблицы backup_patterns, которые принадлежат другим расширениям
# (а не бэкапам БД) и не должны попадать в паттерны баз данных.
_NON_DATABASE_PATTERN_CATEGORIES = {
    "mail",
    "zfs",
    "proxmox",
    "snapshot_transfer",
    "nas_transfer",
    "config_console",
    "stock_load",
}

# Алиасы «полных» ключей DATABASE_CONFIG к коротким именам категорий,
# которые ожидает parse_database_backup (см. get_database_patterns_from_config).
_DB_CATEGORY_ALIASES = {
    "company_databases": "company",
    "barnaul_backups": "barnaul",
    "client_databases": "client",
    "yandex_backups": "yandex",
}


def _as_pattern_mapping(value: object) -> dict:
    """Приводит источник паттернов к словарю.

    ``BACKUP_PATTERNS`` и ответ ``config_manager.get_backup_patterns()``
    могут прийти строкой (JSON или Python-repr), если у настройки в БД
    проставлен ``data_type='string'``. Тогда ``.get()`` падал с
    ``'str' object has no attribute 'get'``, и письма о передаче на NAS
    и о бэкапах конфигов/историй молча переставали разбираться.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text:
            for loader in (json.loads, ast.literal_eval):
                try:
                    parsed = loader(text)
                except Exception:
                    continue
                if isinstance(parsed, dict):
                    return parsed
    return {}


def _extract_subject_patterns(value: object) -> list[str]:
    """Достаёт список subject-паттернов из раздела конфигурации."""
    if isinstance(value, dict):
        subject = value.get("subject", [])
    else:
        subject = value

    if isinstance(subject, str):
        return [subject]
    if isinstance(subject, list):
        return [pattern for pattern in subject if isinstance(pattern, str)]
    return []


def _get_subject_patterns(category: str) -> list[str]:
    """Возвращает subject-паттерны категории: таблица БД, затем настройка."""
    table_patterns = _as_pattern_mapping(config_manager.get_backup_patterns())
    subject_patterns = _extract_subject_patterns(table_patterns.get(category))
    if subject_patterns:
        return subject_patterns

    fallback_patterns = _as_pattern_mapping(BACKUP_PATTERNS)
    return _extract_subject_patterns(fallback_patterns.get(category))


def _merge_db_patterns_from_table(result: dict[str, list[str]]) -> dict[str, list[str]]:
    """Дополняет паттерны БД записями из таблицы ``backup_patterns``.

    Паттерны, добавленные через мастер Telegram-бота
    («Бэкапы БД» → «Настройка паттернов» → «Добавить паттерн»), сохраняются в
    таблицу ``backup_patterns``, а не в настройку ``BACKUP_PATTERNS``. Без
    этого слияния парсер писем их не видит — бэкап только что добавленной базы
    не отслеживается, и пользователю кажется, что паттерн «не сохранился».
    """
    try:
        table_patterns = _as_pattern_mapping(config_manager.get_backup_patterns())
    except Exception as exc:
        logger.error(f"❌ Не удалось прочитать backup_patterns: {exc}")
        return result

    for category, type_map in table_patterns.items():
        if not isinstance(category, str) or category in _NON_DATABASE_PATTERN_CATEGORIES:
            continue
        if not isinstance(type_map, dict):
            continue

        collected: list[str] = []
        for pattern_type, patterns_list in type_map.items():
            # Паттерны Proxmox исторически хранятся под категорией "database".
            if isinstance(pattern_type, str) and pattern_type.startswith("proxmox"):
                continue
            if isinstance(patterns_list, list):
                collected.extend(p for p in patterns_list if isinstance(p, str))
            elif isinstance(patterns_list, str):
                collected.append(patterns_list)

        if not collected:
            continue

        existing = result.get(category)
        if not isinstance(existing, list):
            existing = [existing] if isinstance(existing, str) else []
            result[category] = existing
        for pattern in collected:
            if pattern not in existing:
                existing.append(pattern)

    return result


def get_database_patterns_from_config() -> dict[str, list[str]]:
    """Правильно извлекает паттерны из конфигурации."""
    try:
        all_patterns = _as_pattern_mapping(BACKUP_PATTERNS)
        if not all_patterns and BACKUP_PATTERNS:
            logger.error(f"❌ BACKUP_PATTERNS не словарь: {type(BACKUP_PATTERNS)}")

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
            result = dict(db_patterns)
        else:
            result = {}

        # Гарантируем наличие базовых категорий, на которые опирается парсер.
        for base_category in ("company", "barnaul", "client", "yandex"):
            result.setdefault(base_category, [])

        # Подмешиваем паттерны, добавленные через мастер бота (таблица
        # backup_patterns), иначе они не влияют на разбор писем.
        result = _merge_db_patterns_from_table(result)

        # Мастер «Настройка паттернов» предлагает категории прямо из
        # DATABASE_CONFIG (см. _get_database_categories в
        # bot/handlers/settings_handlers/backups/db.py) — там ключи
        # «полные» (barnaul_backups, client_databases, ...), а не короткие
        # (barnaul, client, ...), которые парсер ищет в barnaul_patterns/
        # client_patterns ниже. Схлопываем такие алиасы в канонические
        # категории, иначе паттерн, добавленный под "barnaul_backups",
        # никогда не попадёт в barnaul_patterns: письмо распознаётся через
        # запасную ветку «пользовательских категорий» с backup_type =
        # "barnaul_backups", и такой бэкап не совпадает ни с одной
        # категорией сводки БД, хотя он успешен и найден вовремя.
        for alias, canonical in _DB_CATEGORY_ALIASES.items():
            alias_patterns = result.pop(alias, None)
            if not isinstance(alias_patterns, list):
                continue
            canonical_patterns = result.setdefault(canonical, [])
            if not isinstance(canonical_patterns, list):
                canonical_patterns = []
                result[canonical] = canonical_patterns
            for pattern in alias_patterns:
                if pattern not in canonical_patterns:
                    canonical_patterns.append(pattern)

        return result

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов: {exc}")
        return {"company": [], "barnaul": [], "client": [], "yandex": []}


def get_zfs_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем ZFS из таблицы паттернов."""
    try:
        return _get_subject_patterns("zfs")

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
        patterns = _as_pattern_mapping(config_manager.get_backup_patterns())
        subject_patterns = _extract_subject_patterns(patterns.get("snapshot_transfer"))

        fallback_source = _as_pattern_mapping(BACKUP_PATTERNS)
        fallback_patterns = _extract_subject_patterns(fallback_source.get("snapshot_transfer"))

        normalized = [_normalize_snapshot_pattern(pattern) for pattern in subject_patterns]
        normalized_fallback = [
            _normalize_snapshot_pattern(pattern) for pattern in fallback_patterns
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
        return _get_subject_patterns("nas_transfer")

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов передачи на NAS: {exc}")
        return []


def get_config_console_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем о бэкапе конфигов и историй консолей."""
    try:
        return _get_subject_patterns("config_console")

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов конфигов/историй: {exc}")
        return []


def get_mail_patterns_from_config() -> list[str]:
    """Извлекает паттерны для писем о бэкапах почты из таблицы паттернов."""
    try:
        return _get_subject_patterns("mail")

    except Exception as exc:
        logger.error(f"❌ Ошибка извлечения паттернов почты: {exc}")
        return []


def get_stock_load_patterns_from_config() -> dict[str, list[str]]:
    """Извлекает паттерны для логов загрузки остатков из настроек."""
    try:
        patterns = _as_pattern_mapping(config_manager.get_backup_patterns())
        if not patterns:
            patterns = _as_pattern_mapping(
                config_manager.get_setting("BACKUP_PATTERNS", BACKUP_PATTERNS)
            )
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
