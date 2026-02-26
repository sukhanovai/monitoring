"""
/bot/handlers/settings_handlers.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for managing settings via a bot
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РЅР°СЃС‚СЂРѕР№РєР°РјРё С‡РµСЂРµР· Р±РѕС‚Р°
"""

import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError
from telegram.utils.helpers import escape_markdown
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from core.config_manager import config_manager as settings_manager
from config.db_settings import BACKUP_DATABASE_CONFIG
from config.settings import BACKUP_PATTERNS as DEFAULT_BACKUP_PATTERNS
from extensions.extension_manager import extension_manager
from extensions.supplier_stock_files import (
    SUPPLIER_STOCK_EXTENSION_ID,
    build_supplier_stock_source_stats,
    get_supplier_stock_config,
    get_supplier_stock_reports,
    parse_supplier_stock_schedule_times,
    save_supplier_stock_config,
    summarize_supplier_stock_reports,
)
from lib.logging import debug_log
import json
import re

BACKUP_SETTINGS_CALLBACKS = {
    'backup_times',
    'settings_backup_databases',
    'backup_db_add_category',
    'view_patterns',
    'add_pattern',
    'add_zfs_pattern',
    'add_proxmox_pattern',
    'add_mail_pattern',
    'add_stock_pattern',
    'edit_mail_default_pattern',
    'mail_pattern_confirm',
    'mail_pattern_retry',
    'stock_pattern_confirm',
    'stock_pattern_retry',
    'zfs_pattern_confirm',
    'zfs_pattern_retry',
    'db_pattern_confirm',
    'db_pattern_retry',
    'proxmox_pattern_confirm',
    'proxmox_pattern_retry',
}

debug_logger = debug_log

def _safe_query_answer(query, text: str | None = None, **kwargs) -> None:
    try:
        if text is None:
            query.answer(**kwargs)
        else:
            query.answer(text, **kwargs)
    except (BadRequest, TelegramError):
        pass

def _get_mail_fallback_patterns() -> list:
    """РџРѕР»СѓС‡РёС‚СЊ Р·Р°РїР°СЃРЅС‹Рµ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹."""
    default_pattern = (
        r"^\s*Р±СЌРєР°Рї\s+zimbra\s*-\s*"
        r"(?P<size>\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?)\s+"
        r"(?P<path>/\S+)\s*$"
    )
    config_patterns = settings_manager.get_backup_patterns()
    if isinstance(config_patterns, str):
        try:
            config_patterns = json.loads(config_patterns)
        except json.JSONDecodeError:
            config_patterns = {}
    config_mail = config_patterns.get("mail", {})
    if isinstance(config_mail, dict):
        patterns = config_mail.get("subject", [])
    elif isinstance(config_mail, list):
        patterns = config_mail
    else:
        patterns = []

    if patterns:
        return patterns

    fallback_raw = settings_manager.get_setting('BACKUP_PATTERNS', DEFAULT_BACKUP_PATTERNS)
    if isinstance(fallback_raw, str):
        try:
            fallback_raw = json.loads(fallback_raw)
        except json.JSONDecodeError:
            fallback_raw = {}
    if not fallback_raw:
        fallback_raw = DEFAULT_BACKUP_PATTERNS
    fallback_mail = fallback_raw.get("mail", {})
    if isinstance(fallback_mail, dict):
        return fallback_mail.get("subject", []) or [default_pattern]
    if isinstance(fallback_mail, list):
        return fallback_mail or [default_pattern]
    return [default_pattern]

def _escape_pattern_text(text: str) -> str:
    """Р­РєСЂР°РЅРёСЂСѓРµС‚ С‚РµРєСЃС‚ РґР»СЏ Markdown."""
    return escape_markdown(str(text or ""), version=1)

def _format_current_hint(value, default: str = "РЅРµ Р·Р°РґР°РЅРѕ") -> str:
    """РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ РїРѕРґСЃРєР°Р·РєСѓ РґР»СЏ С‚РµРєСѓС‰РµРіРѕ Р·РЅР°С‡РµРЅРёСЏ."""
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    return str(value)

def _format_archive_cleanup_days(value) -> str:
    """РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ РѕС‚РѕР±СЂР°Р¶РµРЅРёРµ РїРµСЂРёРѕРґР° РѕС‡РёСЃС‚РєРё Р°СЂС…РёРІР°."""
    try:
        days = int(str(value).strip())
    except (TypeError, ValueError):
        days = 0
    if days <= 0:
        return "РІС‹РєР»СЋС‡РµРЅРѕ"
    return f"{days} РґРЅ."

def _build_mail_pattern_from_subject(subject: str) -> str:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ РїРѕ С‚РµРјРµ РїРёСЃСЊРјР°."""
    if not subject:
        return ""

    normalized = subject.strip()
    if not normalized:
        return ""

    size_regex = r"\b\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?\b"
    path_regex = r"/\S+"
    date_iso_regex = r"\b\d{4}[-/.]\d{2}[-/.]\d{2}\b"
    date_ru_regex = r"\b\d{2}[-/.]\d{2}[-/.]\d{4}\b"
    time_regex = r"\b\d{2}:\d{2}(?::\d{2})?\b"

    draft = re.sub(size_regex, "__SIZE__", normalized, flags=re.IGNORECASE)
    draft = re.sub(path_regex, "__PATH__", draft)
    draft = re.sub(date_iso_regex, "__DATE__", draft)
    draft = re.sub(date_ru_regex, "__DATE__", draft)
    draft = re.sub(time_regex, "__TIME__", draft)

    escaped = re.escape(draft)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)

    replacements = {
        "__SIZE__": r"(?P<size>\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?)",
        "__PATH__": r"(?P<path>/\S+)",
        "__DATE__": r"\d{2,4}[-/.]\d{2}[-/.]\d{2,4}",
        "__TIME__": r"\d{2}:\d{2}(?::\d{2})?",
    }

    for placeholder, pattern in replacements.items():
        escaped = escaped.replace(re.escape(placeholder), pattern)

    return escaped

def _build_mail_pattern_from_fragments(fragments: list[str]) -> str:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ РёР· РѕР±СЏР·Р°С‚РµР»СЊРЅС‹С… С„СЂР°РіРјРµРЅС‚РѕРІ."""
    cleaned = [fragment.strip() for fragment in fragments if fragment.strip()]
    if not cleaned:
        return ""
    escaped_parts = [re.escape(fragment) for fragment in cleaned]
    return r".*".join(escaped_parts)

def _build_stock_subject_pattern(subject: str) -> str:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ РґР»СЏ С‚РµРјС‹ РїРёСЃСЊРјР° Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ."""
    if not subject:
        return ""

    normalized = subject.strip()
    if not normalized:
        return ""

    time_regex = r"\b\d{2}:\d{2}:\d{2}\b"
    date_regex = r"\b\d{2}[./-]\d{2}[./-]\d{2,4}\b"

    draft = re.sub(time_regex, "__TIME__", normalized)
    draft = re.sub(date_regex, "__DATE__", draft)

    escaped = re.escape(draft)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)

    escaped = escaped.replace(re.escape("__TIME__"), r"\d{2}:\d{2}:\d{2}")
    escaped = escaped.replace(re.escape("__DATE__"), r"\d{2}[./-]\d{2}[./-]\d{2,4}")
    return escaped

def _build_stock_pattern_from_fragments(fragments: list[str]) -> str:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ РґР»СЏ РѕСЃС‚Р°С‚РєРѕРІ РёР· РѕР±СЏР·Р°С‚РµР»СЊРЅС‹С… С„СЂР°РіРјРµРЅС‚РѕРІ."""
    return _build_mail_pattern_from_fragments(fragments)

def _build_stock_success_pattern(sample: str) -> str:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ СѓСЃРїРµС…Р° РїРѕ РїСЂРёРјРµСЂСѓ СЃС‚СЂРѕРєРё."""
    normalized = sample.strip()
    if not normalized:
        return ""

    date_regex = r"\b\d{2}\.\d{2}\.\d{2}\b"
    time_regex = r"\b\d{2}:\d{2}:\d{2}\b"

    draft = re.sub(date_regex, "__DATE__", normalized)
    draft = re.sub(time_regex, "__TIME__", draft)
    draft = re.sub(r"(СЃС‚СЂРѕРє\s+)\d+", r"\1__ROWS__", draft, flags=re.IGNORECASE)

    escaped = re.escape(draft)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)

    escaped = escaped.replace(re.escape("__DATE__"), r"\d{2}\.\d{2}\.\d{2}")
    escaped = escaped.replace(re.escape("__TIME__"), r"\d{2}:\d{2}:\d{2}")
    escaped = escaped.replace(re.escape("__ROWS__"), r"(?P<rows>\d+)")
    return escaped

def _get_stock_load_fallback_patterns() -> dict[str, list[str]]:
    """РџРѕР»СѓС‡РёС‚СЊ Р·Р°РїР°СЃРЅС‹Рµ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ."""
    fallback_raw = settings_manager.get_setting('BACKUP_PATTERNS', DEFAULT_BACKUP_PATTERNS)
    if isinstance(fallback_raw, str):
        try:
            fallback_raw = json.loads(fallback_raw)
        except json.JSONDecodeError:
            fallback_raw = {}
    if not fallback_raw:
        fallback_raw = DEFAULT_BACKUP_PATTERNS

    stock_patterns = fallback_raw.get("stock_load", {})
    if not isinstance(stock_patterns, dict):
        return {}

    return {
        key: [p for p in value if isinstance(p, str)]
        for key, value in stock_patterns.items()
        if isinstance(value, list)
    }

def _get_database_fallback_patterns() -> dict[str, list[str]]:
    """РџРѕР»СѓС‡РёС‚СЊ Р·Р°РїР°СЃРЅС‹Рµ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Р±СЌРєР°РїРѕРІ Р‘Р”."""
    fallback_raw = settings_manager.get_setting('BACKUP_PATTERNS', DEFAULT_BACKUP_PATTERNS)
    if isinstance(fallback_raw, str):
        try:
            fallback_raw = json.loads(fallback_raw)
        except json.JSONDecodeError:
            fallback_raw = {}
    if not fallback_raw:
        fallback_raw = DEFAULT_BACKUP_PATTERNS

    db_patterns = fallback_raw.get("database", {})
    if isinstance(db_patterns, list):
        result: dict[str, list[str]] = {}
        for item in db_patterns:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, list):
                        result[key] = [p for p in value if isinstance(p, str)]
        return result
    if isinstance(db_patterns, dict):
        return {
            key: [p for p in value if isinstance(p, str)]
            for key, value in db_patterns.items()
            if isinstance(value, list)
        }
    return {}

def _get_backup_patterns_setting() -> dict:
    """РџРѕР»СѓС‡РёС‚СЊ РїРѕР»РЅС‹Рµ РїР°С‚С‚РµСЂРЅС‹ РёР· РЅР°СЃС‚СЂРѕРµРє."""
    raw_patterns = settings_manager.get_setting('BACKUP_PATTERNS', DEFAULT_BACKUP_PATTERNS)
    if isinstance(raw_patterns, str):
        try:
            raw_patterns = json.loads(raw_patterns)
        except json.JSONDecodeError:
            raw_patterns = {}
    if not isinstance(raw_patterns, dict):
        return {}
    return raw_patterns

def _get_database_patterns_setting() -> dict[str, list[str]]:
    """РџРѕР»СѓС‡РёС‚СЊ РїР°С‚С‚РµСЂРЅС‹ Р‘Р” РёР· РЅР°СЃС‚СЂРѕРµРє РІ РЅРѕСЂРјР°Р»РёР·РѕРІР°РЅРЅРѕРј РІРёРґРµ."""
    raw_patterns = _get_backup_patterns_setting()
    db_patterns = raw_patterns.get("database", {})
    if isinstance(db_patterns, list):
        normalized: dict[str, list[str]] = {}
        for item in db_patterns:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, list):
                        normalized[key] = [p for p in value if isinstance(p, str)]
        return normalized
    if isinstance(db_patterns, dict):
        return {
            key: [p for p in value if isinstance(p, str)]
            for key, value in db_patterns.items()
            if isinstance(value, list)
        }
    return {}

def _save_database_patterns_setting(db_patterns: dict[str, list[str]]) -> None:
    """РЎРѕС…СЂР°РЅРёС‚СЊ РїР°С‚С‚РµСЂРЅС‹ Р‘Р” РІ РЅР°СЃС‚СЂРѕР№РєР°С…."""
    raw_patterns = _get_backup_patterns_setting()
    raw_patterns["database"] = db_patterns
    settings_manager.set_setting('BACKUP_PATTERNS', raw_patterns)

def _get_database_names() -> list[str]:
    """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РёРјС‘РЅ Р‘Р” РёР· РЅР°СЃС‚СЂРѕРµРє."""
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if not isinstance(db_config, dict):
        return []

    names: list[str] = []
    for databases in db_config.values():
        if isinstance(databases, dict):
            names.extend([name for name in databases.keys() if isinstance(name, str)])
    return names

def _inject_db_placeholder(text: str, db_names: list[str]) -> tuple[str, str | None]:
    """РџРѕРґРјРµРЅРёС‚СЊ РёРјСЏ Р‘Р” РЅР° РїР»РµР№СЃС…РѕР»РґРµСЂ, РµСЃР»Рё РЅР°Р№РґРµРЅРѕ."""
    if not text or not db_names:
        return text, None

    matched = None
    for db_name in sorted(db_names, key=len, reverse=True):
        if re.search(re.escape(db_name), text, re.IGNORECASE):
            matched = db_name
            break

    if not matched:
        return text, None

    replaced = re.sub(
        re.escape(matched),
        "__DB__",
        text,
        flags=re.IGNORECASE
    )
    return replaced, matched

def _build_db_pattern_from_subject(subject: str, db_names: list[str]) -> tuple[str, str | None]:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ Р‘Р” РїРѕ С‚РµРјРµ РїРёСЃСЊРјР°."""
    if not subject:
        return "", None

    normalized = subject.strip()
    if not normalized:
        return "", None

    normalized, db_name = _inject_db_placeholder(normalized, db_names)
    if not db_name:
        return "", None

    escaped = re.escape(normalized)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)
    escaped = escaped.replace(re.escape("__DB__"), r"([\w.-]+)")
    return escaped, db_name

def _build_db_pattern_from_fragments(
    fragments: list[str],
    db_names: list[str],
) -> tuple[str, str | None]:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ Р‘Р” РёР· РѕР±СЏР·Р°С‚РµР»СЊРЅС‹С… С„СЂР°РіРјРµРЅС‚РѕРІ."""
    cleaned = [fragment.strip() for fragment in fragments if fragment.strip()]
    if not cleaned:
        return "", None

    processed = []
    matched_db: str | None = None
    for fragment in cleaned:
        replaced, db_name = _inject_db_placeholder(fragment, db_names)
        if db_name:
            if matched_db and matched_db != db_name:
                return "", None
            matched_db = db_name
        processed.append(replaced)

    if not matched_db:
        return "", None

    escaped_parts = [re.escape(fragment) for fragment in processed]
    pattern = r".*".join(escaped_parts)
    pattern = pattern.replace(re.escape("__DB__"), r"([\w.-]+)")
    return pattern, matched_db

def _get_zfs_server_names() -> list[str]:
    """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РёРјС‘РЅ ZFS СЃРµСЂРІРµСЂРѕРІ РёР· РЅР°СЃС‚СЂРѕРµРє."""
    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if isinstance(zfs_servers, dict):
        return [name for name in zfs_servers.keys() if isinstance(name, str)]
    return []

def _inject_server_placeholder(text: str, server_names: list[str]) -> tuple[str, bool]:
    """РџРѕРґРјРµРЅРёС‚СЊ РёРјСЏ СЃРµСЂРІРµСЂР° РЅР° РїР»РµР№СЃС…РѕР»РґРµСЂ, РµСЃР»Рё РЅР°Р№РґРµРЅРѕ."""
    if not text or not server_names:
        return text, False

    matched = None
    for server_name in sorted(server_names, key=len, reverse=True):
        if re.search(re.escape(server_name), text, re.IGNORECASE):
            matched = server_name
            break

    if not matched:
        return text, False

    replaced = re.sub(
        re.escape(matched),
        "__SERVER__",
        text,
        flags=re.IGNORECASE
    )
    return replaced, True

def _build_zfs_pattern_from_subject(subject: str, server_names: list[str]) -> tuple[str, bool]:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ ZFS РїРѕ С‚РµРјРµ РїРёСЃСЊРјР°."""
    if not subject:
        return "", False

    normalized = subject.strip()
    if not normalized:
        return "", False

    normalized, has_server = _inject_server_placeholder(normalized, server_names)
    escaped = re.escape(normalized)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)
    escaped = escaped.replace(re.escape("__SERVER__"), r"(?P<server>[\w.-]+)")
    return escaped, has_server

def _build_zfs_pattern_from_fragments(
    fragments: list[str],
    server_names: list[str],
) -> tuple[str, bool]:
    """РЎРѕР±СЂР°С‚СЊ regex РїР°С‚С‚РµСЂРЅ ZFS РёР· РѕР±СЏР·Р°С‚РµР»СЊРЅС‹С… С„СЂР°РіРјРµРЅС‚РѕРІ."""
    cleaned = [fragment.strip() for fragment in fragments if fragment.strip()]
    if not cleaned:
        return "", False

    processed = []
    has_server = False
    for fragment in cleaned:
        replaced, fragment_has_server = _inject_server_placeholder(fragment, server_names)
        if fragment_has_server:
            has_server = True
        processed.append(replaced)

    escaped_parts = [re.escape(fragment) for fragment in processed]
    pattern = r".*".join(escaped_parts)
    pattern = pattern.replace(re.escape("__SERVER__"), r"(?P<server>[\w.-]+)")
    return pattern, has_server

def settings_command(update, context):
    """РљРѕРјР°РЅРґР° СѓРїСЂР°РІР»РµРЅРёСЏ РЅР°СЃС‚СЂРѕР№РєР°РјРё"""
    keyboard = [
        [InlineKeyboardButton("рџ¤– РќР°СЃС‚СЂРѕР№РєРё Р±РѕС‚Р°", callback_data='settings_telegram')],
        [InlineKeyboardButton("вЏ° Р’СЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё", callback_data='settings_time')],
        [InlineKeyboardButton("рџ”§ РњРѕРЅРёС‚РѕСЂРёРЅРі", callback_data='settings_monitoring')],
    ]

    keyboard.extend([
        [InlineKeyboardButton("рџ”ђ РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ", callback_data='settings_auth')],
        [InlineKeyboardButton("рџ–ҐпёЏ РЎРµСЂРІРµСЂС‹", callback_data='settings_servers')],
    ])

    keyboard.append([InlineKeyboardButton("рџ§© Р Р°СЃС€РёСЂРµРЅРёСЏ", callback_data='settings_extensions')])

    if extension_manager.is_extension_enabled('web_interface'):
        keyboard.append([InlineKeyboardButton("рџЊђ Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ", callback_data='settings_web')])

    keyboard.extend([
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])
    
    if update.message:
        update.message.reply_text(
            "вљ™пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєР°РјРё*\n\nР’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ РЅР°СЃС‚СЂРѕР№РєРё:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.callback_query.edit_message_text(
            "вљ™пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєР°РјРё*\n\nР’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ РЅР°СЃС‚СЂРѕР№РєРё:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def show_telegram_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Telegram - РћР‘РќРћР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()
    
    token = settings_manager.get_setting('TELEGRAM_TOKEN', '')
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    token_display = "рџџў РЈСЃС‚Р°РЅРѕРІР»РµРЅ" if token else "рџ”ґ РќРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ"
    chats_display = f"{len(chat_ids)} С‡Р°С‚РѕРІ" if chat_ids else "рџ”ґ РќРµ РЅР°СЃС‚СЂРѕРµРЅС‹"

    tamtam_token = settings_manager.get_setting('TAMTAM_TOKEN', '')
    tamtam_chat_ids = settings_manager.get_setting('TAMTAM_CHAT_IDS', [])
    tamtam_token_display = "рџџў РЈСЃС‚Р°РЅРѕРІР»РµРЅ" if tamtam_token else "рџ”ґ РќРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ"
    tamtam_chats_display = f"{len(tamtam_chat_ids)} С‡Р°С‚РѕРІ" if tamtam_chat_ids else "рџ”ґ РќРµ РЅР°СЃС‚СЂРѕРµРЅС‹"
    
    message = (
        "рџ¤– *РќР°СЃС‚СЂРѕР№РєРё Telegram*\n\n"
        f"вЂў РўРѕРєРµРЅ Р±РѕС‚Р°: {token_display}\n"
        f"вЂў ID С‡Р°С‚РѕРІ: {chats_display}\n\n"
        "рџџ  *РќР°СЃС‚СЂРѕР№РєРё TamTam*\n"
        f"вЂў РўРѕРєРµРЅ Р±РѕС‚Р°: {tamtam_token_display}\n"
        f"вЂў ID С‡Р°С‚РѕРІ: {tamtam_chats_display}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ”‘ РЈСЃС‚Р°РЅРѕРІРёС‚СЊ С‚РѕРєРµРЅ", callback_data='set_telegram_token')],
        [InlineKeyboardButton("рџ’¬ РЈРїСЂР°РІР»РµРЅРёРµ С‡Р°С‚Р°РјРё", callback_data='manage_chats')],
        [InlineKeyboardButton("рџџ  РЈСЃС‚Р°РЅРѕРІРёС‚СЊ TamTam С‚РѕРєРµРЅ", callback_data='set_tamtam_token')],
        [InlineKeyboardButton("рџџ  РЈРїСЂР°РІР»РµРЅРёРµ TamTam С‡Р°С‚Р°РјРё", callback_data='manage_tamtam_chats')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_monitoring_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РјРѕРЅРёС‚РѕСЂРёРЅРіР° - РћР‘РќРћР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()
    
    check_interval = settings_manager.get_setting('CHECK_INTERVAL', 60)
    max_fail_time = settings_manager.get_setting('MAX_FAIL_TIME', 900)
    
    # РќРѕРІС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё С‚Р°Р№РјР°СѓС‚РѕРІ
    windows_2025_timeout = settings_manager.get_setting('WINDOWS_2025_TIMEOUT', 35)
    domain_timeout = settings_manager.get_setting('DOMAIN_SERVERS_TIMEOUT', 20)
    admin_timeout = settings_manager.get_setting('ADMIN_SERVERS_TIMEOUT', 25)
    standard_timeout = settings_manager.get_setting('STANDARD_WINDOWS_TIMEOUT', 30)
    linux_timeout = settings_manager.get_setting('LINUX_TIMEOUT', 15)
    
    message = (
        "рџ”§ *РќР°СЃС‚СЂРѕР№РєРё РјРѕРЅРёС‚РѕСЂРёРЅРіР°*\n\n"
        f"вЂў РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё: {check_interval} СЃРµРє\n"
        f"вЂў РњР°РєСЃ. РІСЂРµРјСЏ РїСЂРѕСЃС‚РѕСЏ: {max_fail_time} СЃРµРє\n\n"
        "*РўР°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ:*\n"
        f"вЂў Windows 2025: {windows_2025_timeout} СЃРµРє\n"
        f"вЂў Р”РѕРјРµРЅРЅС‹Рµ СЃРµСЂРІРµСЂС‹: {domain_timeout} СЃРµРє\n"
        f"вЂў Admin СЃРµСЂРІРµСЂС‹: {admin_timeout} СЃРµРє\n"
        f"вЂў РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ Windows: {standard_timeout} СЃРµРє\n"
        f"вЂў Linux СЃРµСЂРІРµСЂС‹: {linux_timeout} СЃРµРє\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("вЏ±пёЏ РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё", callback_data='set_check_interval')],
        [InlineKeyboardButton("рџљЁ РњР°РєСЃ. РІСЂРµРјСЏ РїСЂРѕСЃС‚РѕСЏ", callback_data='set_max_fail_time')],
        [InlineKeyboardButton("вЏ° РўР°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ", callback_data='server_timeouts')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_time_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РІСЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё"""
    query = update.callback_query
    query.answer()
    
    silent_start = settings_manager.get_setting('SILENT_START', 20)
    silent_end = settings_manager.get_setting('SILENT_END', 9)
    data_collection = settings_manager.get_setting('DATA_COLLECTION_TIME', '08:30')
    
    message = (
        "вЏ° *Р’СЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё*\n\n"
        f"вЂў РўРёС…РёР№ СЂРµР¶РёРј: {silent_start}:00 - {silent_end}:00\n"
        f"вЂў РЎР±РѕСЂ РґР°РЅРЅС‹С…: {data_collection}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ”‡ РќР°С‡Р°Р»Рѕ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°", callback_data='set_silent_start')],
        [InlineKeyboardButton("рџ”Љ РљРѕРЅРµС† С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°", callback_data='set_silent_end')],
        [InlineKeyboardButton("рџ“Љ Р’СЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С…", callback_data='set_data_collection')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_resource_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё СЂРµСЃСѓСЂСЃРѕРІ"""
    query = update.callback_query
    query.answer()
    
    cpu_warning = settings_manager.get_setting('CPU_WARNING', 80)
    cpu_critical = settings_manager.get_setting('CPU_CRITICAL', 90)
    ram_warning = settings_manager.get_setting('RAM_WARNING', 85)
    ram_critical = settings_manager.get_setting('RAM_CRITICAL', 95)
    disk_warning = settings_manager.get_setting('DISK_WARNING', 80)
    disk_critical = settings_manager.get_setting('DISK_CRITICAL', 90)
    
    message = (
        "рџ’» *РќР°СЃС‚СЂРѕР№РєРё СЂРµСЃСѓСЂСЃРѕРІ*\n\n"
        f"вЂў CPU РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ: {cpu_warning}%\n"
        f"вЂў CPU РєСЂРёС‚РёС‡РµСЃРєРёР№: {cpu_critical}%\n"
        f"вЂў RAM РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ: {ram_warning}%\n"
        f"вЂў RAM РєСЂРёС‚РёС‡РµСЃРєРёР№: {ram_critical}%\n"
        f"вЂў Disk РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ: {disk_warning}%\n"
        f"вЂў Disk РєСЂРёС‚РёС‡РµСЃРєРёР№: {disk_critical}%\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ’» CPU РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ", callback_data='set_cpu_warning')],
        [InlineKeyboardButton("рџ’» CPU РєСЂРёС‚РёС‡РµСЃРєРёР№", callback_data='set_cpu_critical')],
        [InlineKeyboardButton("рџ§  RAM РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ", callback_data='set_ram_warning')],
        [InlineKeyboardButton("рџ§  RAM РєСЂРёС‚РёС‡РµСЃРєРёР№", callback_data='set_ram_critical')],
        [InlineKeyboardButton("рџ’ѕ Disk РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ", callback_data='set_disk_warning')],
        [InlineKeyboardButton("рџ’ѕ Disk РєСЂРёС‚РёС‡РµСЃРєРёР№", callback_data='set_disk_critical')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±СЌРєР°РїРѕРІ - РЎ РР—РњР•РќР•РќРќР«Рњ CALLBACK"""
    query = update.callback_query
    query.answer()
    
    backup_alert_hours = settings_manager.get_setting('BACKUP_ALERT_HOURS', 24)
    backup_stale_hours = settings_manager.get_setting('BACKUP_STALE_HOURS', 36)
    
    database_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    db_categories = list(database_config.keys()) if database_config else []
    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    proxmox_count = len(proxmox_hosts) if isinstance(proxmox_hosts, dict) else 0
    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    zfs_count = len(zfs_servers) if isinstance(zfs_servers, dict) else 0
    
    message = (
        "рџ’ѕ *РќР°СЃС‚СЂРѕР№РєРё Р±СЌРєР°РїРѕРІ*\n\n"
        f"вЂў РђР»РµСЂС‚С‹ С‡РµСЂРµР·: {backup_alert_hours}С‡\n"
        f"вЂў РЈСЃС‚Р°СЂРµРІР°РЅРёРµ С‡РµСЂРµР·: {backup_stale_hours}С‡\n"
        f"вЂў РљР°С‚РµРіРѕСЂРёРё Р‘Р”: {len(db_categories)}\n\n"
        f"вЂў Proxmox С…РѕСЃС‚С‹: {proxmox_count}\n\n"
        f"вЂў ZFS СЃРµСЂРІРµСЂС‹: {zfs_count}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР» РґР»СЏ РЅР°СЃС‚СЂРѕР№РєРё:"
    )
    
    keyboard = [
        [InlineKeyboardButton("вЏ° Р’СЂРµРјРµРЅРЅС‹Рµ РёРЅС‚РµСЂРІР°Р»С‹", callback_data='backup_times')],
    ]

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ–ҐпёЏ Proxmox Р±СЌРєР°РїС‹", callback_data='settings_backup_proxmox')])
        keyboard.append([InlineKeyboardButton("рџ–ҐпёЏ РџР°С‚С‚РµСЂРЅС‹ Proxmox", callback_data='settings_patterns_proxmox')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ—ѓпёЏ Р‘Р°Р·С‹ РґР°РЅРЅС‹С…", callback_data='settings_db_main')])
        keyboard.append([InlineKeyboardButton("рџ—ѓпёЏ РџР°С‚С‚РµСЂРЅС‹ Р‘Р”", callback_data='settings_patterns_db')])

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append([InlineKeyboardButton("рџ§Љ ZFS", callback_data='settings_zfs')])

    keyboard.extend([
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_proxmox_backup_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±СЌРєР°РїРѕРІ Proxmox РІ СЂР°Р·РґРµР»Рµ СЂР°СЃС€РёСЂРµРЅРёР№"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    proxmox_count = len(proxmox_hosts) if isinstance(proxmox_hosts, dict) else 0

    message = (
        "рџ–ҐпёЏ *Р‘СЌРєР°РїС‹ Proxmox*\n\n"
        f"РҐРѕСЃС‚РѕРІ РІ СЃРїРёСЃРєРµ: {proxmox_count}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ“‹ РҐРѕСЃС‚С‹", callback_data='settings_backup_proxmox')],
        [InlineKeyboardButton("рџ”Ќ РџР°С‚С‚РµСЂРЅС‹", callback_data='settings_patterns_proxmox')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_database_backup_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±СЌРєР°РїРѕРІ Р‘Р” РІ СЂР°Р·РґРµР»Рµ СЂР°СЃС€РёСЂРµРЅРёР№"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    db_categories = list(db_config.keys()) if isinstance(db_config, dict) else []

    message = (
        "рџ—ѓпёЏ *Р‘СЌРєР°РїС‹ Р‘Р”*\n\n"
        f"РљР°С‚РµРіРѕСЂРёР№: {len(db_categories)}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ“‹ Р‘Р°Р·С‹", callback_data='settings_db_main')],
        [InlineKeyboardButton("рџ”Ќ РџР°С‚С‚РµСЂРЅС‹", callback_data='settings_patterns_db')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ Р±СЌРєР°РїРѕРІ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "рџ—ѓпёЏ *РќР°СЃС‚СЂРѕР№РєРё Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ Р±СЌРєР°РїРѕРІ*\n\n"
    
    if not db_config:
        message += "вќЊ *Р‘Р°Р·С‹ РґР°РЅРЅС‹С… РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n\n"
        message += "Р—РґРµСЃСЊ РІС‹ РјРѕР¶РµС‚Рµ РЅР°СЃС‚СЂРѕРёС‚СЊ РєР°С‚РµРіРѕСЂРёРё Рё Р±Р°Р·С‹ РґР°РЅРЅС‹С… РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ."
    else:
        message += "*РўРµРєСѓС‰РёРµ РЅР°СЃС‚СЂРѕР№РєРё:*\n\n"
        for category, databases in db_config.items():
            message += f"рџ“Ѓ *{category.upper()}*\n"
            message += f"   РљРѕР»РёС‡РµСЃС‚РІРѕ Р‘Р”: {len(databases)}\n"
            # РџРѕРєР°Р·С‹РІР°РµРј РЅРµСЃРєРѕР»СЊРєРѕ РїСЂРёРјРµСЂРѕРІ
            sample_dbs = list(databases.values())[:2]
            for db_name in sample_dbs:
                message += f"   вЂў {db_name}\n"
            if len(databases) > 2:
                message += f"   вЂў ... Рё РµС‰Рµ {len(databases) - 2} Р‘Р”\n"
            message += "\n"
    
    message += "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    
    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='settings_db_add_category')],
        [InlineKeyboardButton("вњЏпёЏ Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='settings_db_edit_category')],
        [InlineKeyboardButton("рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='settings_db_delete_category')],
        [InlineKeyboardButton("рџ“‹ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… Р‘Р”", callback_data='settings_db_view_all')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_all_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РІСЃРµ РЅР°СЃС‚СЂРѕР№РєРё"""
    query = update.callback_query
    query.answer()
    
    all_settings = settings_manager.get_all_settings()
    
    message = "рџ“Љ *Р’СЃРµ РЅР°СЃС‚СЂРѕР№РєРё СЃРёСЃС‚РµРјС‹*\n\n"
    
    for category in settings_manager.get_categories():
        message += f"*{category.upper()}:*\n"
        category_settings = {k: v for k, v in all_settings.items() if k.lower().startswith(category.lower()) or settings_manager.get_setting(k, category='') == category}
        
        for key, value in category_settings.items():
            if key == 'TELEGRAM_TOKEN' and value:
                value = '***' + value[-4:]  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕР»СЊРєРѕ РїРѕСЃР»РµРґРЅРёРµ 4 СЃРёРјРІРѕР»Р°
            elif key == 'TAMTAM_TOKEN' and value:
                value = '***' + value[-4:]
            elif key == 'CHAT_IDS':
                value = f"{len(value)} С‡Р°С‚РѕРІ"
            elif key == 'TAMTAM_CHAT_IDS':
                value = f"{len(value)} С‡Р°С‚РѕРІ"
            elif isinstance(value, (list, dict)):
                value = f"{len(value)} СЌР»РµРјРµРЅС‚РѕРІ"
            
            message += f"вЂў {key}: {value}\n"
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєР°РјРё", callback_data='settings_main')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def settings_callback_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє callback'РѕРІ РЅР°СЃС‚СЂРѕРµРє"""
    query = update.callback_query
    data = query.data
    
    # РµСЃР»Рё СЌС‚Рѕ callback РѕС‚ Р±СЌРєР°РїРѕРІ, РќР• РѕР±СЂР°Р±Р°С‚С‹РІР°РµРј Р·РґРµСЃСЊ
    if (
        data.startswith('db_')
        and data not in BACKUP_SETTINGS_CALLBACKS
        and not data.startswith('db_default_')
    ):
        _safe_query_answer(query, "вљ™пёЏ РџРµСЂРµРЅР°РїСЂР°РІР»РµРЅРёРµ Рє РјРѕРґСѓР»СЋ Р±СЌРєР°РїРѕРІ...")
        # РџРµСЂРµРґР°РµРј РѕР±СЂР°Р±РѕС‚РєСѓ РґР°Р»СЊС€Рµ РїРѕ С†РµРїРѕС‡РєРµ
        return
    if data.startswith('backup_') and data not in BACKUP_SETTINGS_CALLBACKS:
        _safe_query_answer(query, "вљ™пёЏ РџРµСЂРµРЅР°РїСЂР°РІР»РµРЅРёРµ Рє РјРѕРґСѓР»СЋ Р±СЌРєР°РїРѕРІ...")
        # РџРµСЂРµРґР°РµРј РѕР±СЂР°Р±РѕС‚РєСѓ РґР°Р»СЊС€Рµ РїРѕ С†РµРїРѕС‡РєРµ
        return

    try:
        # РћСЃРЅРѕРІРЅС‹Рµ РєР°С‚РµРіРѕСЂРёРё РЅР°СЃС‚СЂРѕРµРє
        if data == 'settings_main':
            settings_command(update, context)
        elif data == 'settings_telegram':
            show_telegram_settings(update, context)
        elif data == 'settings_monitoring':
            show_monitoring_settings(update, context)
        elif data == 'settings_time':
            show_time_settings(update, context)
        elif data == 'settings_resources':
            show_resource_settings(update, context)
        elif data == 'settings_auth':
            show_auth_settings(update, context)  # РўРµРїРµСЂСЊ СѓРїСЂРѕС‰РµРЅРЅР°СЏ РІРµСЂСЃРёСЏ
        elif data == 'settings_servers':
            show_servers_settings(update, context)
        elif data == 'settings_backup':
            show_backup_settings(update, context)
        elif data == 'settings_extensions':
            show_settings_extensions_menu(update, context)
        elif data == 'settings_extensions_manage':
            show_extensions_settings_menu(update, context)
        elif data == 'settings_ext_backup_proxmox':
            show_proxmox_backup_settings(update, context)
        elif data == 'settings_ext_backup_db':
            show_database_backup_settings(update, context)
        elif data == 'settings_ext_backup_mail':
            show_mail_backup_settings(update, context)
        elif data == 'settings_ext_stock_load':
            show_stock_load_settings(update, context)
        elif data == 'settings_ext_supplier_stock':
            show_supplier_stock_settings(update, context)
        elif data == 'settings_patterns_db':
            show_db_patterns_menu(update, context)
        elif data == 'settings_patterns_proxmox':
            show_proxmox_patterns_menu(update, context)
        elif data == 'settings_patterns_zfs':
            show_zfs_patterns_menu(update, context)
        elif data == 'settings_patterns_mail':
            show_mail_patterns_menu(update, context)
        elif data == 'settings_patterns_stock':
            show_stock_load_patterns_menu(update, context)
        elif data == 'settings_web':
            show_web_settings(update, context)
        elif data == 'settings_view_all':
            view_all_settings_handler(update, context)

        elif data == 'supplier_stock_download':
            show_supplier_stock_download_settings(update, context)
        elif data == 'supplier_stock_mail':
            show_supplier_stock_mail_settings(update, context)
        elif data == 'supplier_stock_reports':
            show_supplier_stock_reports(update, context, source_kind='download')
        elif data == 'supplier_stock_reports_download':
            show_supplier_stock_reports(update, context, source_kind='download')
        elif data == 'supplier_stock_reports_mail':
            show_supplier_stock_reports(update, context, source_kind='mail')
        elif data == 'supplier_stock_reports_sources_download':
            show_supplier_stock_report_sources(update, context, source_kind='download')
        elif data == 'supplier_stock_reports_sources_mail':
            show_supplier_stock_report_sources(update, context, source_kind='mail')
        elif data.startswith('supplier_stock_report_source_day|'):
            _, source_kind, source_id = data.split('|', 2)
            show_supplier_stock_report_source_stats(update, context, source_id, source_kind, period_days=1)
        elif data.startswith('supplier_stock_report_source|'):
            _, source_kind, source_id = data.split('|', 2)
            show_supplier_stock_report_source_stats(update, context, source_id, source_kind)
        elif data.startswith('supplier_stock_report_entry|'):
            _, entry_key = data.split('|', 1)
            show_supplier_stock_report_entry_details(update, context, entry_key)
        elif data == 'supplier_stock_processing':
            show_supplier_stock_processing_menu(update, context, action_prefix="supplier_stock_processing")
        elif data.startswith('supplier_stock_processing|'):
            parts = data.split('|')
            action = parts[1] if len(parts) > 1 else ''
            rule_id = parts[2] if len(parts) > 2 else ''
            if action == 'add':
                supplier_stock_start_processing_rule_menu(update, context)
            elif action == 'edit' and rule_id:
                supplier_stock_start_processing_rule_menu(update, context, rule_id=rule_id)
            elif action in ('toggle', 'delete', 'activate') and rule_id:
                config = get_supplier_stock_config()
                rules = config.get("processing", {}).get("rules", [])
                if action == 'toggle':
                    for rule in rules:
                        if str(rule.get("id")) == rule_id:
                            rule["enabled"] = not rule.get("enabled", True)
                            if not rule.get("enabled", True):
                                rule["active"] = False
                            break
                elif action == 'activate':
                    _set_supplier_stock_processing_active_rule(rules, rule_id)
                elif action == 'delete':
                    rules = [item for item in rules if str(item.get("id")) != rule_id]
                config.setdefault("processing", {})["rules"] = rules
                save_supplier_stock_config(config)
                show_supplier_stock_processing_menu(update, context, action_prefix="supplier_stock_processing")
        elif data.startswith('supplier_stock_processing_rule|'):
            parts = data.split('|')
            action = parts[1] if len(parts) > 1 else ''
            if action == 'menu':
                show_supplier_stock_processing_rule_menu(update, context)
            elif action == 'save':
                supplier_stock_save_processing_rule(update, context)
            elif action == 'save_back':
                if _save_processing_rule_data(update, context):
                    back_callback = context.user_data.get('supplier_stock_processing_back', 'supplier_stock_processing')
                    _show_processing_rule_back_menu(update, context, back_callback)
            elif action == 'back':
                if context.user_data.get('supplier_stock_processing_rule_dirty'):
                    _persist_processing_rule_data(context)
                    context.user_data['supplier_stock_processing_rule_dirty'] = False
                back_callback = context.user_data.get('supplier_stock_processing_back', 'supplier_stock_processing')
                _show_processing_rule_back_menu(update, context, back_callback)
            elif action == 'toggle_processing':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                data['requires_processing'] = not data.get('requires_processing', True)
                if data.get('requires_processing') and not data.get('variants'):
                    _sync_processing_variants_count(data, 1)
                    data['variants_count'] = 1
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_rule_menu(update, context)
            elif action in ('add_variant', 'remove_variant'):
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variants = data.get('variants', [])
                current_count = len(variants)
                if action == 'add_variant':
                    new_count = current_count + 1
                else:
                    new_count = max(current_count - 1, 0)
                _sync_processing_variants_count(data, new_count)
                data['variants_count'] = new_count
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_rule_menu(update, context)
            elif action == 'variant' and len(parts) > 2:
                variant_index = int(parts[2])
                context.user_data['supplier_stock_processing_variant_index'] = variant_index
                show_supplier_stock_processing_variant_menu(update, context, variant_index)
            elif action == 'field' and len(parts) > 2:
                field = parts[2]
                supplier_stock_start_processing_field_edit(update, context, field)
        elif data.startswith('supplier_stock_processing_variant|'):
            parts = data.split('|')
            action = parts[1] if len(parts) > 1 else ''
            variant_index = int(parts[2]) if len(parts) > 2 else 0
            if action == 'menu':
                show_supplier_stock_processing_variant_menu(update, context, variant_index)
            elif action == 'add_column':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                columns_count = variant.get("data_columns_count") or len(variant.get("data_columns", []))
                _sync_variant_columns(variant, columns_count + 1)
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_variant_menu(update, context, variant_index)
            elif action == 'toggle_orc':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get('orc', {})
                orc['enabled'] = not orc.get('enabled', False)
                variant['orc'] = orc
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_rule_menu(update, context)
            elif action == 'field' and len(parts) > 3:
                field = parts[3]
                item_index = int(parts[4]) if len(parts) > 4 else None
                supplier_stock_start_processing_field_edit(
                    update,
                    context,
                    field,
                    variant_index=variant_index,
                    item_index=item_index,
                )
        elif data.startswith('supplier_stock_processing_columns|'):
            parts = data.split('|')
            action = parts[1] if len(parts) > 1 else ''
            variant_index = int(parts[2]) if len(parts) > 2 else 0
            if action == 'menu':
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action == 'toggle_article_filter':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                current_value = variant.get("use_article_filter")
                if current_value is None:
                    current_value = bool(variant.get("article_filter"))
                variant["use_article_filter"] = not current_value
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action in ('tac', 'toggle_article_filter_column') and len(parts) > 3:
                column_index = int(parts[3])
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                columns_count = variant.get("data_columns_count") or len(variant.get("data_columns", []))
                _sync_variant_columns(variant, columns_count)
                filters = list(variant.get("use_article_filter_columns", []))
                if 0 <= column_index < len(filters):
                    filters[column_index] = not filters[column_index]
                    variant["use_article_filter_columns"] = filters
                    data['variants'][variant_index] = variant
                    context.user_data['supplier_stock_processing_rule_data'] = data
                    context.user_data['supplier_stock_processing_rule_dirty'] = True
                    _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action == 'add_column':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                columns_count = variant.get("data_columns_count") or len(variant.get("data_columns", []))
                _sync_variant_columns(variant, columns_count + 1)
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action == 'remove_column' and len(parts) > 3:
                column_index = int(parts[3])
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                if _remove_variant_column(variant, column_index):
                    data['variants'][variant_index] = variant
                    context.user_data['supplier_stock_processing_rule_data'] = data
                    context.user_data['supplier_stock_processing_rule_dirty'] = True
                    _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
        elif data.startswith('supplier_stock_processing_orc|'):
            parts = data.split('|')
            action = parts[1] if len(parts) > 1 else ''
            variant_index = int(parts[2]) if len(parts) > 2 else 0
            if action == 'menu':
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == 'set_input' and len(parts) > 3:
                input_index = int(parts[3])
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get('orc', {})
                orc['input_index'] = input_index
                variant['orc'] = orc
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == 'clear_input':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get('orc', {})
                orc.pop('input_index', None)
                variant['orc'] = orc
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == 'set_output' and len(parts) > 3:
                output_index = int(parts[3])
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get('orc', {})
                orc['output_index'] = output_index
                variant['orc'] = orc
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == 'clear_output':
                data = context.user_data.get('supplier_stock_processing_rule_data', {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get('orc', {})
                orc.pop('output_index', None)
                variant['orc'] = orc
                data['variants'][variant_index] = variant
                context.user_data['supplier_stock_processing_rule_data'] = data
                context.user_data['supplier_stock_processing_rule_dirty'] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
        elif data.startswith('supplier_stock_processing_source|'):
            parts = data.split('|')
            source_id = parts[1] if len(parts) > 1 else ''
            action = parts[2] if len(parts) > 2 else ''
            rule_id = parts[3] if len(parts) > 3 else ''
            back_callback = f'supplier_stock_source_settings|{source_id}'
            action_prefix = f'supplier_stock_processing_source|{source_id}'
            if action == 'menu':
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="рџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ (РёСЃС‚РѕС‡РЅРёРє)*",
                )
            elif action == 'add':
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                )
            elif action == 'edit' and rule_id:
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    rule_id,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                )
            elif action in ('toggle', 'delete', 'activate') and rule_id:
                config = get_supplier_stock_config()
                rules = config.get("processing", {}).get("rules", [])
                if action == 'toggle':
                    for rule in rules:
                        if str(rule.get("id")) == rule_id:
                            rule["enabled"] = not rule.get("enabled", True)
                            if not rule.get("enabled", True):
                                rule["active"] = False
                            break
                elif action == 'activate':
                    _set_supplier_stock_processing_active_rule(
                        rules,
                        rule_id,
                        source_id=source_id,
                        source_kind="download",
                    )
                elif action == 'delete':
                    rules = [item for item in rules if str(item.get("id")) != rule_id]
                config.setdefault("processing", {})["rules"] = rules
                save_supplier_stock_config(config)
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="рџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ (РёСЃС‚РѕС‡РЅРёРє)*",
                )
        elif data.startswith('supplier_stock_processing_mail|'):
            parts = data.split('|')
            source_id = parts[1] if len(parts) > 1 else ''
            action = parts[2] if len(parts) > 2 else ''
            rule_id = parts[3] if len(parts) > 3 else ''
            back_callback = f'supplier_stock_mail_source_settings|{source_id}'
            action_prefix = f'supplier_stock_processing_mail|{source_id}'
            if action == 'menu':
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="рџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ (РїРѕС‡С‚Р°)*",
                )
            elif action == 'add':
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                )
            elif action == 'edit' and rule_id:
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    rule_id,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                )
            elif action in ('toggle', 'delete', 'activate') and rule_id:
                config = get_supplier_stock_config()
                rules = config.get("processing", {}).get("rules", [])
                if action == 'toggle':
                    for rule in rules:
                        if str(rule.get("id")) == rule_id:
                            rule["enabled"] = not rule.get("enabled", True)
                            if not rule.get("enabled", True):
                                rule["active"] = False
                            break
                elif action == 'activate':
                    _set_supplier_stock_processing_active_rule(
                        rules,
                        rule_id,
                        source_id=source_id,
                        source_kind="mail",
                    )
                elif action == 'delete':
                    rules = [item for item in rules if str(item.get("id")) != rule_id]
                config.setdefault("processing", {})["rules"] = rules
                save_supplier_stock_config(config)
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="рџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ (РїРѕС‡С‚Р°)*",
                )
        elif data == 'supplier_stock_noop':
            query.answer(" ", show_alert=False)
        elif data == 'supplier_stock_mail_toggle':
            config = get_supplier_stock_config()
            mail_settings = config.get("mail", {})
            mail_settings["enabled"] = not mail_settings.get("enabled", False)
            config["mail"] = mail_settings
            save_supplier_stock_config(config)
            show_supplier_stock_mail_settings(update, context)
        elif data == 'supplier_stock_mail_temp_dir':
            context.user_data['supplier_stock_mail_edit'] = 'temp_dir'
            config = get_supplier_stock_config()
            current_temp_dir = _format_current_hint(config.get("mail", {}).get("temp_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїСѓС‚СЊ Рє РІСЂРµРјРµРЅРЅРѕРјСѓ РєР°С‚Р°Р»РѕРіСѓ РґР»СЏ РїРѕС‡С‚РѕРІС‹С… С„Р°Р№Р»РѕРІ:\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_temp_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_mail')]
                ])
            )
        elif data == 'supplier_stock_mail_archive_dir':
            context.user_data['supplier_stock_mail_edit'] = 'archive_dir'
            config = get_supplier_stock_config()
            current_archive_dir = _format_current_hint(config.get("mail", {}).get("archive_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїСѓС‚СЊ Рє РєР°С‚Р°Р»РѕРіСѓ Р°СЂС…РёРІР° РґР»СЏ РїРѕС‡С‚РѕРІС‹С… С„Р°Р№Р»РѕРІ:\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_archive_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_mail')]
                ])
            )
        elif data == 'supplier_stock_archive_cleanup_mail':
            context.user_data['supplier_stock_edit'] = 'archive_cleanup_days'
            context.user_data['supplier_stock_archive_cleanup_back'] = 'supplier_stock_mail'
            config = get_supplier_stock_config()
            current_value = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїРµСЂРёРѕРґ РѕС‡РёСЃС‚РєРё Р°СЂС…РёРІР° РІ РґРЅСЏС… (0 вЂ” РѕС‚РєР»СЋС‡РёС‚СЊ):\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_value}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_mail')]
                ])
            )
        elif data == 'supplier_stock_report_period':
            context.user_data['supplier_stock_edit'] = 'report_period_days'
            config = get_supplier_stock_config()
            current_value = config.get("reporting", {}).get("period_days", 7)
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїРµСЂРёРѕРґ РѕС‚С‡С‘С‚РѕРІ РІ РґРЅСЏС… (РјРёРЅРёРјСѓРј 1):\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_value}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_ext_supplier_stock')]
                ])
            )
        elif data == 'supplier_stock_mail_unpack_toggle':
            query.answer("в„№пёЏ Р Р°СЃРїР°РєРѕРІРєР° С‚РµРїРµСЂСЊ РЅР° СѓСЂРѕРІРЅРµ РїСЂР°РІРёР»", show_alert=False)
            show_supplier_stock_mail_settings(update, context)
        elif data == 'supplier_stock_mail_sources':
            show_supplier_stock_mail_sources_menu(update, context)
        elif data == 'supplier_stock_resources':
            show_supplier_stock_resources_menu(update, context)
        elif data == 'supplier_stock_ftp':
            show_supplier_stock_ftp_settings(update, context)
        elif data == 'supplier_stock_mail_source_add':
            supplier_stock_start_mail_source_wizard(update, context)
        elif data.startswith('supplier_stock_mail_source_settings|'):
            source_id = data.split('|', 1)[1]
            show_supplier_stock_mail_source_settings(update, context, source_id)
        elif data.startswith('supplier_stock_mail_source_individual|'):
            source_id = data.split('|', 1)[1]
            show_supplier_stock_mail_source_individual_settings(update, context, source_id)
        elif data.startswith('supplier_stock_mail_field|'):
            _, source_id, field = data.split('|', 2)
            supplier_stock_start_mail_source_field_edit(update, context, source_id, field)
        elif data.startswith('supplier_stock_mail_source_individual_toggle_'):
            source_id = data.replace('supplier_stock_mail_source_individual_toggle_', '')
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    individual_dir = source.setdefault("individual_directory", {})
                    individual_dir["enabled"] = not individual_dir.get("enabled", False)
                    break
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_mail_source_individual_settings(update, context, source_id)
        elif data.startswith('supplier_stock_mail_source_unpack_toggle_'):
            source_id = data.replace('supplier_stock_mail_source_unpack_toggle_', '')
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            updated = False
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["unpack_archive"] = not source.get("unpack_archive", False)
                    updated = True
                    break
            if not updated:
                query.answer("вљ пёЏ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ", show_alert=False)
                return
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get('supplier_stock_mail_source_settings_id') == source_id:
                show_supplier_stock_mail_source_settings(update, context, source_id)
            else:
                show_supplier_stock_mail_sources_menu(update, context)
        elif data.startswith('supplier_stock_mail_source_toggle_'):
            source_id = data.replace('supplier_stock_mail_source_toggle_', '')
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["enabled"] = not source.get("enabled", True)
                    break
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get('supplier_stock_mail_source_settings_id') == source_id:
                show_supplier_stock_mail_source_settings(update, context, source_id)
            else:
                show_supplier_stock_mail_sources_menu(update, context)
        elif data.startswith('supplier_stock_mail_source_delete_'):
            source_id = data.replace('supplier_stock_mail_source_delete_', '')
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            sources = [item for item in sources if str(item.get("id")) != source_id]
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_mail_sources_menu(update, context)
        elif data.startswith('supplier_stock_resource_settings|'):
            resource_id = data.split('|', 1)[1]
            show_supplier_stock_resource_settings(update, context, resource_id)
        elif data.startswith('supplier_stock_resource_field|'):
            _, resource_id, field = data.split('|', 2)
            supplier_stock_start_resource_field_edit(update, context, resource_id, field)
        elif data == 'supplier_stock_resource_add':
            supplier_stock_start_resource_wizard(update, context)
        elif data.startswith('supplier_stock_resource_toggle_'):
            resource_id = data.replace('supplier_stock_resource_toggle_', '')
            config = get_supplier_stock_config()
            resources = config.get("resources", [])
            for resource in resources:
                if str(resource.get("id")) == resource_id:
                    resource["enabled"] = not resource.get("enabled", True)
                    break
            config["resources"] = resources
            save_supplier_stock_config(config)
            show_supplier_stock_resources_menu(update, context)
        elif data.startswith('supplier_stock_resource_delete_'):
            resource_id = data.replace('supplier_stock_resource_delete_', '')
            config = get_supplier_stock_config()
            resources = [item for item in config.get("resources", []) if str(item.get("id")) != resource_id]
            config["resources"] = resources
            save_supplier_stock_config(config)
            show_supplier_stock_resources_menu(update, context)
        elif data.startswith('supplier_stock_ftp_field|'):
            _, field = data.split('|', 1)
            supplier_stock_start_ftp_field_edit(update, context, field)
        elif data == 'supplier_stock_temp_dir':
            context.user_data['supplier_stock_edit'] = 'temp_dir'
            config = get_supplier_stock_config()
            current_temp_dir = _format_current_hint(config.get("download", {}).get("temp_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїСѓС‚СЊ Рє РІСЂРµРјРµРЅРЅРѕРјСѓ РєР°С‚Р°Р»РѕРіСѓ:\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_temp_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_download')]
                ])
            )
        elif data == 'supplier_stock_schedule':
            show_supplier_stock_schedule_menu(update, context)
        elif data == 'supplier_stock_unpack_toggle':
            query.answer("в„№пёЏ Р Р°СЃРїР°РєРѕРІРєР° С‚РµРїРµСЂСЊ РЅР° СѓСЂРѕРІРЅРµ РёСЃС‚РѕС‡РЅРёРєРѕРІ", show_alert=False)
            show_supplier_stock_download_settings(update, context)
        elif data == 'supplier_stock_archive_dir':
            context.user_data['supplier_stock_edit'] = 'archive_dir'
            config = get_supplier_stock_config()
            current_archive_dir = _format_current_hint(config.get("download", {}).get("archive_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїСѓС‚СЊ Рє РєР°С‚Р°Р»РѕРіСѓ Р°СЂС…РёРІР°:\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_archive_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_download')]
                ])
            )
        elif data == 'supplier_stock_archive_cleanup_download':
            context.user_data['supplier_stock_edit'] = 'archive_cleanup_days'
            context.user_data['supplier_stock_archive_cleanup_back'] = 'supplier_stock_download'
            config = get_supplier_stock_config()
            current_value = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РїРµСЂРёРѕРґ РѕС‡РёСЃС‚РєРё Р°СЂС…РёРІР° РІ РґРЅСЏС… (0 вЂ” РѕС‚РєР»СЋС‡РёС‚СЊ):\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_value}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_download')]
                ])
            )
        elif data == 'supplier_stock_unpack_toggle':
            config = get_supplier_stock_config()
            download_settings = config.get("download", {})
            download_settings["unpack_archive"] = not download_settings.get("unpack_archive", False)
            config["download"] = download_settings
            save_supplier_stock_config(config)
            show_supplier_stock_download_settings(update, context)
        elif data == 'supplier_stock_schedule_toggle':
            config = get_supplier_stock_config()
            schedule = config.get("download", {}).get("schedule", {})
            schedule["enabled"] = not schedule.get("enabled", False)
            config["download"]["schedule"] = schedule
            save_supplier_stock_config(config)
            show_supplier_stock_schedule_menu(update, context)
        elif data == 'supplier_stock_schedule_time':
            context.user_data['supplier_stock_edit'] = 'schedule_time'
            config = get_supplier_stock_config()
            current_time = _format_current_hint(
                config.get("download", {}).get("schedule", {}).get("time")
            )
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Р’РІРµРґРёС‚Рµ РѕРґРЅРѕ РёР»Рё РЅРµСЃРєРѕР»СЊРєРѕ РІСЂРµРјРµРЅ Р·Р°РїСѓСЃРєР° (HH:MM).\n"
                "Р Р°Р·РґРµР»РёС‚РµР»Рё: РїСЂРѕР±РµР», Р·Р°РїСЏС‚Р°СЏ РёР»Рё С‚РѕС‡РєР° СЃ Р·Р°РїСЏС‚РѕР№.\n"
                f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_time}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_schedule')]
                ])
            )
        elif data == 'supplier_stock_sources':
            show_supplier_stock_sources_menu(update, context)
        elif data == 'supplier_stock_source_add':
            supplier_stock_start_source_wizard(update, context)
        elif data.startswith('supplier_stock_source_settings|'):
            source_id = data.split('|', 1)[1]
            show_supplier_stock_source_settings(update, context, source_id)
        elif data.startswith('supplier_stock_source_individual|'):
            source_id = data.split('|', 1)[1]
            show_supplier_stock_source_individual_settings(update, context, source_id)
        elif data.startswith('supplier_stock_source_field|'):
            _, source_id, field = data.split('|', 2)
            supplier_stock_start_source_field_edit(update, context, source_id, field)
        elif data.startswith('supplier_stock_source_iek_settings|'):
            source_id = data.split('|', 1)[1]
            show_supplier_stock_source_iek_settings(update, context, source_id)
        elif data.startswith('supplier_stock_source_iek_field|'):
            _, source_id, field = data.split('|', 2)
            supplier_stock_start_source_iek_field_edit(update, context, source_id, field)
        elif data.startswith('supplier_stock_source_individual_toggle_'):
            source_id = data.replace('supplier_stock_source_individual_toggle_', '')
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    individual_dir = source.setdefault("individual_directory", {})
                    individual_dir["enabled"] = not individual_dir.get("enabled", False)
                    break
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_source_individual_settings(update, context, source_id)
        elif data.startswith('supplier_stock_source_unpack_toggle_'):
            source_id = data.replace('supplier_stock_source_unpack_toggle_', '')
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            updated = False
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["unpack_archive"] = not source.get("unpack_archive", False)
                    updated = True
                    break
            if not updated:
                query.answer("вљ пёЏ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ", show_alert=False)
                return
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get('supplier_stock_source_settings_id') == source_id:
                show_supplier_stock_source_settings(update, context, source_id)
            else:
                show_supplier_stock_sources_menu(update, context)
        elif data.startswith('supplier_stock_source_toggle_'):
            source_id = data.replace('supplier_stock_source_toggle_', '')
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["enabled"] = not source.get("enabled", True)
                    break
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get('supplier_stock_source_settings_id') == source_id:
                show_supplier_stock_source_settings(update, context, source_id)
            else:
                show_supplier_stock_sources_menu(update, context)
        elif data.startswith('supplier_stock_source_delete_'):
            source_id = data.replace('supplier_stock_source_delete_', '')
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            sources = [item for item in sources if str(item.get("id")) != source_id]
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_sources_menu(update, context)
        
        # РџРѕРґРїСѓРЅРєС‚С‹
        elif data == 'backup_times':
            show_backup_times(update, context)
        elif data == 'settings_backup_proxmox':
            show_backup_proxmox_settings(update, context)
        elif data == 'settings_proxmox_add':
            add_proxmox_host_handler(update, context)
        elif data == 'settings_proxmox_list':
            show_proxmox_hosts_list(update, context)
        elif data.startswith('settings_proxmox_delete_'):
            host_name = data.replace('settings_proxmox_delete_', '')
            delete_proxmox_host(update, context, host_name)
        elif data.startswith('settings_proxmox_edit_'):
            host_name = data.replace('settings_proxmox_edit_', '')
            edit_proxmox_host_handler(update, context, host_name)
        elif data.startswith('settings_proxmox_toggle_'):
            host_name = data.replace('settings_proxmox_toggle_', '')
            toggle_proxmox_host(update, context, host_name)
        elif data == 'settings_zfs':
            show_zfs_settings(update, context)
        elif data == 'settings_zfs_list':
            show_zfs_servers_list(update, context)
        elif data == 'settings_zfs_add':
            add_zfs_server_handler(update, context)
        elif data.startswith('settings_zfs_edit_name_'):
            server_name = data.replace('settings_zfs_edit_name_', '')
            edit_zfs_server_name_handler(update, context, server_name)
        elif data.startswith('settings_zfs_delete_'):
            server_name = data.replace('settings_zfs_delete_', '')
            delete_zfs_server(update, context, server_name)
        elif data.startswith('settings_zfs_toggle_'):
            server_name = data.replace('settings_zfs_toggle_', '')
            toggle_zfs_server(update, context, server_name)
        
        # РќРѕРІС‹Рµ РѕР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РЅР°СЃС‚СЂРѕРµРє Р‘Р”
        elif data == 'settings_db_main':
            show_backup_databases_settings(update, context)
        elif data == 'settings_db_add_category':
            add_database_category_handler(update, context)
        elif data == 'settings_db_edit_category':
            edit_databases_handler(update, context)
        elif data == 'settings_db_delete_category':
            delete_database_category_handler(update, context)
        elif data == 'settings_db_view_all':
            view_all_databases_handler(update, context)
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РЅРѕРІС‹С… РїСѓРЅРєС‚РѕРІ РјРµРЅСЋ
        elif data == 'manage_chats':
            manage_chats_handler(update, context)
        elif data == 'manage_tamtam_chats':
            manage_tamtam_chats_handler(update, context)
        elif data == 'server_timeouts':
            show_server_timeouts(update, context)  # РўРµРїРµСЂСЊ СѓРїСЂРѕС‰РµРЅРЅР°СЏ РІРµСЂСЃРёСЏ
        elif data == 'settings_add_server':
            add_server_handler(update, context)
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СѓСЃС‚Р°РЅРѕРІРєРё Р·РЅР°С‡РµРЅРёР№
        elif data.startswith('set_'):
            handle_setting_input(update, context, data.replace('set_', ''))
        
        # РЈРїСЂР°РІР»РµРЅРёРµ С‡Р°С‚Р°РјРё
        elif data == 'add_chat':
            add_chat_handler(update, context)
        elif data == 'remove_chat':
            remove_chat_handler(update, context)
        elif data == 'add_tamtam_chat':
            add_tamtam_chat_handler(update, context)
        elif data == 'remove_tamtam_chat':
            remove_tamtam_chat_handler(update, context)
        
        # РџР°С‚С‚РµСЂРЅС‹ Р±СЌРєР°РїРѕРІ
        elif data == 'view_patterns':
            view_patterns_handler(update, context)
        elif data == 'add_pattern':
            add_pattern_handler(update, context)
        elif data == 'add_zfs_pattern':
            add_zfs_pattern_handler(update, context)
        elif data == 'add_proxmox_pattern':
            add_proxmox_pattern_handler(update, context)
        elif data == 'add_mail_pattern':
            add_mail_pattern_handler(update, context)
        elif data == 'add_stock_pattern':
            show_stock_pattern_type_menu(update, context)
        elif data == 'edit_mail_default_pattern':
            edit_mail_default_pattern_handler(update, context)
        elif data == 'db_pattern_confirm':
            db_pattern_confirm_handler(update, context)
        elif data == 'db_pattern_retry':
            db_pattern_retry_handler(update, context)
        elif data.startswith('db_pattern_set_category_'):
            category = data.replace('db_pattern_set_category_', '')
            db_pattern_set_category_handler(update, context, category)
        elif data == 'zfs_pattern_confirm':
            zfs_pattern_confirm_handler(update, context)
        elif data == 'zfs_pattern_retry':
            zfs_pattern_retry_handler(update, context)
        elif data == 'proxmox_pattern_confirm':
            proxmox_pattern_confirm_handler(update, context)
        elif data == 'proxmox_pattern_retry':
            proxmox_pattern_retry_handler(update, context)
        elif data == 'stock_pattern_confirm':
            stock_pattern_confirm_handler(update, context)
        elif data == 'stock_pattern_retry':
            stock_pattern_retry_handler(update, context)
        elif data.startswith('stock_pattern_select_'):
            pattern_type = data.replace('stock_pattern_select_', '')
            stock_pattern_select_handler(update, context, pattern_type)
        elif data.startswith('db_default_edit_'):
            raw_value = data.replace('db_default_edit_', '')
            if '__' in raw_value:
                category, index_value = raw_value.split('__', 1)
                edit_default_db_pattern_handler(update, context, category, index_value)
        elif data.startswith('db_default_delete_'):
            raw_value = data.replace('db_default_delete_', '')
            if '__' in raw_value:
                category, index_value = raw_value.split('__', 1)
                delete_default_db_pattern_handler(update, context, category, index_value)
        elif data == 'mail_pattern_confirm':
            mail_pattern_confirm_handler(update, context)
        elif data == 'mail_pattern_retry':
            mail_pattern_retry_handler(update, context)
        elif data == 'settings_ext_enable_all':
            _enable_all_extensions_settings(query)
            show_extensions_settings_menu(update, context)
        elif data == 'settings_ext_disable_all':
            _disable_all_extensions_settings(query)
            show_extensions_settings_menu(update, context)
        elif data.startswith('settings_ext_toggle_'):
            extension_id = data.replace('settings_ext_toggle_', '')
            success, message = extension_manager.toggle_extension(extension_id)
            if success:
                _safe_query_answer(query, message)
                show_extensions_settings_menu(update, context)
            else:
                _safe_query_answer(query, message, show_alert=True)
        elif data.startswith('delete_pattern_'):
            pattern_id = data.replace('delete_pattern_', '')
            delete_pattern_handler(update, context, pattern_id)
        elif data.startswith('edit_pattern_'):
            pattern_id = data.replace('edit_pattern_', '')
            edit_pattern_handler(update, context, pattern_id)
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Рё СѓРґР°Р»РµРЅРёСЏ РєР°С‚РµРіРѕСЂРёР№ Р‘Р”
        elif data.startswith('settings_db_add_db_'):
            category = data.replace('settings_db_add_db_', '')
            add_database_entry_handler(update, context, category)
        elif data.startswith('settings_db_edit_db_'):
            raw_value = data.replace('settings_db_edit_db_', '')
            if '__' in raw_value:
                category, db_key = raw_value.split('__', 1)
                edit_database_entry_handler(update, context, category, db_key)
        elif data.startswith('settings_db_delete_db_confirm_'):
            raw_value = data.replace('settings_db_delete_db_confirm_', '')
            if '__' in raw_value:
                category, db_key = raw_value.split('__', 1)
                delete_database_entry_execute(update, context, category, db_key)
        elif data.startswith('settings_db_delete_db_'):
            raw_value = data.replace('settings_db_delete_db_', '')
            if '__' in raw_value:
                category, db_key = raw_value.split('__', 1)
                delete_database_entry_confirmation(update, context, category, db_key)
        elif data.startswith('settings_db_delete_confirm_'):
            category = data.replace('settings_db_delete_confirm_', '')
            delete_database_category_execute(update, context, category)
        elif data.startswith('settings_db_delete_'):
            category = data.replace('settings_db_delete_', '')
            delete_database_category_confirmation(update, context, category)
        elif data.startswith('settings_db_edit_'):
            category = data.replace('settings_db_edit_', '')
            edit_database_category_details(update, context, category)
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЃРµСЂРІРµСЂРѕРІ
        elif data == 'settings_servers_list':
            show_servers_list(update, context)
        elif data.startswith('settings_delete_server_'):
            ip = data.replace('settings_delete_server_', '')
            delete_server_confirmation(update, context, ip)
        elif data.startswith('settings_confirm_delete_server_'):
            ip = data.replace('settings_confirm_delete_server_', '')
            delete_server_execute(update, context, ip)
        elif data.startswith('settings_edit_server_type_select_'):
            handle_server_type_selection(update, context)
        elif data.startswith('settings_edit_server_name_'):
            ip = data.replace('settings_edit_server_name_', '')
            start_server_name_edit(update, context, ip)
        elif data.startswith('settings_edit_server_type_'):
            ip = data.replace('settings_edit_server_type_', '')
            start_server_type_edit(update, context, ip)
        elif data.startswith('settings_edit_server_'):
            ip = data.replace('settings_edit_server_', '')
            show_server_edit_menu(update, context, ip)
        elif data.startswith('settings_toggle_server_'):
            ip = data.replace('settings_toggle_server_', '')
            toggle_server_monitoring(update, context, ip)
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ С‚Р°Р№РјР°СѓС‚РѕРІ СЃРµСЂРІРµСЂРѕРІ
        elif data == 'set_windows_2025_timeout':
            handle_setting_input(update, context, 'windows_2025_timeout')
        elif data == 'set_domain_servers_timeout':
            handle_setting_input(update, context, 'domain_servers_timeout')
        elif data == 'set_admin_servers_timeout':
            handle_setting_input(update, context, 'admin_servers_timeout')
        elif data == 'set_standard_windows_timeout':
            handle_setting_input(update, context, 'standard_windows_timeout')
        elif data == 'set_linux_timeout':
            handle_setting_input(update, context, 'linux_timeout')
        elif data == 'set_ping_timeout':
            handle_setting_input(update, context, 'ping_timeout')
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё С‚РёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ
        elif data.startswith('server_type_'):
            handle_server_type(update, context)
        
        # РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ
        elif data == 'settings_auth':
            show_auth_settings(update, context)
        elif data == 'ssh_auth_settings':
            show_ssh_auth_settings(update, context)
        
        # Windows Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ
        elif data == 'windows_auth_main':
            show_windows_auth_settings(update, context)
        elif data == 'windows_auth_list':
            show_windows_auth_list(update, context)
        elif data == 'windows_auth_add':
            show_windows_auth_add(update, context)
        elif data == 'windows_auth_by_type':
            show_windows_auth_by_type(update, context)
        elif data == 'windows_auth_manage_types':
            show_windows_auth_manage_types(update, context)
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё С‚РёРїРѕРІ РґР»СЏ Windows СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…
        elif data.startswith('cred_type_'):
            handle_credential_type_selection(update, context)

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё СѓРїСЂР°РІР»РµРЅРёСЏ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ Windows
        elif data.startswith('manage_type_'):
            handle_server_type_management(update, context)

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ (РїРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ РѕРїРµСЂР°С†РёР№)
        elif data.startswith('merge_confirm_'):
            parts = data.replace('merge_confirm_', '').split('_')
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = '_'.join(parts[1:])
                merge_server_types_confirmation(update, context, source_type, target_type)

        elif data.startswith('delete_type_confirm_'):
            server_type = data.replace('delete_type_confirm_', '')
            delete_server_type_confirmation(update, context, server_type)

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РѕРїРµСЂР°С†РёР№ СЃ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ
        elif data.startswith('merge_execute_'):
            parts = data.replace('merge_execute_', '').split('_')
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = '_'.join(parts[1:])
                execute_server_type_merge(update, context, source_type, target_type)

        elif data.startswith('delete_type_execute_'):
            server_type = data.replace('delete_type_execute_', '')
            execute_server_type_delete(update, context, server_type)

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ Р·Р°РєСЂС‹С‚РёСЏ РјРµРЅСЋ
        elif data == 'close':
            try:
                query.delete_message()
            except:
                query.edit_message_text("вњ… РњРµРЅСЋ Р·Р°РєСЂС‹С‚Рѕ")
        
        else:
            _safe_query_answer(query, "вљ™пёЏ Р­С‚РѕС‚ СЂР°Р·РґРµР» РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ")
    
    except Exception as e:
        print(f"вќЊ РћС€РёР±РєР° РІ settings_callback_handler: {e}")
        debug_logger(f"РћС€РёР±РєР° РІ settings_callback_handler: {e}")
        _safe_query_answer(query, "вќЊ РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР° РїСЂРё РѕР±СЂР°Р±РѕС‚РєРµ Р·Р°РїСЂРѕСЃР°")
    
    _safe_query_answer(query)

def handle_setting_input(update, context, setting_key):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° Р·РЅР°С‡РµРЅРёР№ РЅР°СЃС‚СЂРѕРµРє - РћР‘РќРћР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()
    
    # РЎРѕС…СЂР°РЅСЏРµРј РєР°РєРѕРµ РЅР°СЃС‚СЂРѕР№РєСѓ РјРµРЅСЏРµРј
    context.user_data['editing_setting'] = setting_key
    context.user_data['editing_setting_message_id'] = query.message.message_id
    context.user_data['editing_setting_chat_id'] = query.message.chat_id
    
    setting_descriptions = {
        # РЎСѓС‰РµСЃС‚РІСѓСЋС‰РёРµ РЅР°СЃС‚СЂРѕР№РєРё...
        'telegram_token': 'Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ С‚РѕРєРµРЅ Telegram Р±РѕС‚Р°:',
        'tamtam_token': 'Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ С‚РѕРєРµРЅ TamTam Р±РѕС‚Р°:',
        'check_interval': 'Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ РёРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё (РІ СЃРµРєСѓРЅРґР°С…):',
        'max_fail_time': 'Р’РІРµРґРёС‚Рµ РјР°РєСЃРёРјР°Р»СЊРЅРѕРµ РІСЂРµРјСЏ РїСЂРѕСЃС‚РѕСЏ (РІ СЃРµРєСѓРЅРґР°С…):',
        'silent_start': 'Р’РІРµРґРёС‚Рµ С‡Р°СЃ РЅР°С‡Р°Р»Р° С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (0-23):',
        'silent_end': 'Р’РІРµРґРёС‚Рµ С‡Р°СЃ РѕРєРѕРЅС‡Р°РЅРёСЏ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (0-23):',
        'data_collection': 'Р’РІРµРґРёС‚Рµ РІСЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С… (С„РѕСЂРјР°С‚ HH:MM):',
        'cpu_warning': 'Р’РІРµРґРёС‚Рµ РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РґР»СЏ CPU (%):',
        'cpu_critical': 'Р’РІРµРґРёС‚Рµ РєСЂРёС‚РёС‡РµСЃРєРёР№ РїРѕСЂРѕРі РґР»СЏ CPU (%):',
        'ram_warning': 'Р’РІРµРґРёС‚Рµ РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РґР»СЏ RAM (%):',
        'ram_critical': 'Р’РІРµРґРёС‚Рµ РєСЂРёС‚РёС‡РµСЃРєРёР№ РїРѕСЂРѕРі РґР»СЏ RAM (%):',
        'disk_warning': 'Р’РІРµРґРёС‚Рµ РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РґР»СЏ Disk (%):',
        'disk_critical': 'Р’РІРµРґРёС‚Рµ РєСЂРёС‚РёС‡РµСЃРєРёР№ РїРѕСЂРѕРі РґР»СЏ Disk (%):',
        'ssh_username': 'Р’РІРµРґРёС‚Рµ РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ SSH:',
        'ssh_key_path': 'Р’РІРµРґРёС‚Рµ РїСѓС‚СЊ Рє SSH РєР»СЋС‡Сѓ:',
        'web_port': 'Р’РІРµРґРёС‚Рµ РїРѕСЂС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°:',
        'web_host': 'Р’РІРµРґРёС‚Рµ С…РѕСЃС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°:',
        'backup_alert_hours': 'Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°СЃРѕРІ РґР»СЏ Р°Р»РµСЂС‚РѕРІ Рѕ Р±СЌРєР°РїР°С…:',
        'backup_stale_hours': 'Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°СЃРѕРІ РґР»СЏ СѓСЃС‚Р°СЂРµРІС€РёС… Р±СЌРєР°РїРѕРІ:',
        
        # РќРѕРІС‹Рµ С‚Р°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ
        'windows_2025_timeout': 'Р’РІРµРґРёС‚Рµ С‚Р°Р№РјР°СѓС‚ РґР»СЏ Windows 2025 СЃРµСЂРІРµСЂРѕРІ (РІ СЃРµРєСѓРЅРґР°С…):',
        'domain_servers_timeout': 'Р’РІРµРґРёС‚Рµ С‚Р°Р№РјР°СѓС‚ РґР»СЏ РґРѕРјРµРЅРЅС‹С… СЃРµСЂРІРµСЂРѕРІ (РІ СЃРµРєСѓРЅРґР°С…):',
        'admin_servers_timeout': 'Р’РІРµРґРёС‚Рµ С‚Р°Р№РјР°СѓС‚ РґР»СЏ Admin СЃРµСЂРІРµСЂРѕРІ (РІ СЃРµРєСѓРЅРґР°С…):',
        'standard_windows_timeout': 'Р’РІРµРґРёС‚Рµ С‚Р°Р№РјР°СѓС‚ РґР»СЏ СЃС‚Р°РЅРґР°СЂС‚РЅС‹С… Windows СЃРµСЂРІРµСЂРѕРІ (РІ СЃРµРєСѓРЅРґР°С…):',
        'linux_timeout': 'Р’РІРµРґРёС‚Рµ С‚Р°Р№РјР°СѓС‚ РґР»СЏ Linux СЃРµСЂРІРµСЂРѕРІ (РІ СЃРµРєСѓРЅРґР°С…):',
        'ping_timeout': 'Р’РІРµРґРёС‚Рµ С‚Р°Р№РјР°СѓС‚ РґР»СЏ Ping СЃРµСЂРІРµСЂРѕРІ (РІ СЃРµРєСѓРЅРґР°С…):',
    }
    
    message = setting_descriptions.get(setting_key, f'Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ Р·РЅР°С‡РµРЅРёРµ РґР»СЏ {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_main')]
        ])
    )

def handle_setting_value(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїРѕР»СѓС‡РµРЅРёСЏ Р·РЅР°С‡РµРЅРёСЏ РЅР°СЃС‚СЂРѕР№РєРё - РћР‘РќРћР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    # РЎРЅР°С‡Р°Р»Р° РїСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё Windows СѓС‡РµС‚РЅР°СЏ Р·Р°РїРёСЃСЊ
    if context.user_data.get('adding_windows_cred'):
        return handle_windows_credential_input(update, context)

    if (
        context.user_data.get('supplier_stock_edit')
        or context.user_data.get('supplier_stock_add_source')
        or context.user_data.get('supplier_stock_edit_source')
        or context.user_data.get('supplier_stock_source_field')
        or context.user_data.get('supplier_stock_source_iek_field')
        or context.user_data.get('supplier_stock_resource_add')
        or context.user_data.get('supplier_stock_resource_field')
        or context.user_data.get('supplier_stock_ftp_field')
        or context.user_data.get('supplier_stock_processing_add')
        or context.user_data.get('supplier_stock_processing_edit')
        or context.user_data.get('supplier_stock_processing_field')
        or context.user_data.get('supplier_stock_mail_edit')
        or context.user_data.get('supplier_stock_mail_add_source')
        or context.user_data.get('supplier_stock_mail_edit_source')
        or context.user_data.get('supplier_stock_mail_source_field')
    ):
        return supplier_stock_handle_input(update, context)
    
    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЃРѕР·РґР°РµС‚СЃСЏ Р»Рё С‚РёРї СЃРµСЂРІРµСЂРѕРІ
    if context.user_data.get('creating_server_type'):
        return handle_server_type_creation(update, context)
    
    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё С‚РёРї СЃРµСЂРІРµСЂРѕРІ
    if context.user_data.get('editing_server_type'):
        return handle_server_type_editing(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё СЃРµСЂРІРµСЂ
    if context.user_data.get('editing_server'):
        return handle_server_edit_input(update, context)
    
    # Р—Р°С‚РµРј РїСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё СЃРµСЂРІРµСЂ
    if context.user_data.get('adding_server'):
        return handle_server_input(update, context)
    
    # Р—Р°С‚РµРј РїСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё РєР°С‚РµРіРѕСЂРёСЏ Р‘Р”
    if context.user_data.get('adding_db_category'):
        return handle_db_category_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё С…РѕСЃС‚ Proxmox
    if context.user_data.get('adding_proxmox_host'):
        return handle_proxmox_host_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё С…РѕСЃС‚ Proxmox
    if context.user_data.get('editing_proxmox_host'):
        return handle_proxmox_host_edit_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё ZFS СЃРµСЂРІРµСЂ
    if context.user_data.get('adding_zfs_server'):
        return handle_zfs_server_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё РёРјСЏ ZFS СЃРµСЂРІРµСЂР°
    if context.user_data.get('editing_zfs_server_name'):
        return handle_zfs_server_name_edit_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё Р±Р°Р·Р° РґР°РЅРЅС‹С…
    if context.user_data.get('adding_db_entry'):
        return handle_db_entry_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё Р±Р°Р·Р° РґР°РЅРЅС‹С…
    if context.user_data.get('editing_db_entry'):
        return handle_db_entry_edit_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р»Рё РїР°С‚С‚РµСЂРЅ Р±СЌРєР°РїРѕРІ
    if context.user_data.get('adding_backup_pattern'):
        return handle_backup_pattern_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё РїР°С‚С‚РµСЂРЅ Р±СЌРєР°РїРѕРІ
    if context.user_data.get('editing_backup_pattern'):
        return handle_backup_pattern_edit_input(update, context)

    # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р»Рё РґРµС„РѕР»С‚РЅС‹Р№ РїР°С‚С‚РµСЂРЅ Р‘Р”
    if context.user_data.get('editing_default_db_pattern'):
        return handle_default_db_pattern_edit_input(update, context)

    if context.user_data.get('adding_tamtam_chat'):
        return handle_tamtam_chat_add_input(update, context)

    if context.user_data.get('removing_tamtam_chat'):
        return handle_tamtam_chat_remove_input(update, context)
    
    # Р•СЃР»Рё СЌС‚Рѕ РѕР±С‹С‡РЅР°СЏ РЅР°СЃС‚СЂРѕР№РєР°
    if 'editing_setting' not in context.user_data:
        return
        
    setting_key = context.user_data['editing_setting']
    new_value = update.message.text
    
    try:
        # РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РґР°РЅРЅС‹С… Рё РїСЂРµРѕР±СЂР°Р·СѓРµРј
        setting_types = {
            'check_interval': 'int', 'max_fail_time': 'int', 'silent_start': 'int', 'silent_end': 'int',
            'cpu_warning': 'int', 'cpu_critical': 'int', 'ram_warning': 'int', 'ram_critical': 'int',
            'disk_warning': 'int', 'disk_critical': 'int', 'web_port': 'int',
            'backup_alert_hours': 'int', 'backup_stale_hours': 'int'
        }
        
        if setting_key in setting_types and setting_types[setting_key] == 'int':
            new_value = int(new_value)
        elif setting_key == 'data_collection':
            # РџСЂРѕРІРµСЂСЏРµРј С„РѕСЂРјР°С‚ РІСЂРµРјРµРЅРё
            import re
            if not re.match(r'^\d{1,2}:\d{2}$', new_value):
                raise ValueError("РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РІСЂРµРјРµРЅРё. РСЃРїРѕР»СЊР·СѓР№С‚Рµ HH:MM")
        
        # РЎРѕС…СЂР°РЅСЏРµРј РЅР°СЃС‚СЂРѕР№РєСѓ
        category_map = {
            'telegram_token': 'telegram',
            'tamtam_token': 'tamtam',
            'check_interval': 'monitoring', 'max_fail_time': 'monitoring',
            'silent_start': 'time', 'silent_end': 'time', 'data_collection': 'time',
            'cpu_warning': 'resources', 'cpu_critical': 'resources',
            'ram_warning': 'resources', 'ram_critical': 'resources',
            'disk_warning': 'resources', 'disk_critical': 'resources',
            'ssh_username': 'auth', 'ssh_key_path': 'auth',
            'web_port': 'web', 'web_host': 'web',
            'backup_alert_hours': 'backup', 'backup_stale_hours': 'backup'
        }
        
        special_db_keys = {
            'telegram_token': 'TELEGRAM_TOKEN',
            'tamtam_token': 'TAMTAM_TOKEN',
        }
        db_key = special_db_keys.get(setting_key, setting_key.upper())
        category = category_map.get(setting_key, 'general')
        
        settings_manager.set_setting(db_key, new_value, category)
        
        # РћС‡РёС‰Р°РµРј РєРѕРЅС‚РµРєСЃС‚
        del context.user_data['editing_setting']
        prompt_message_id = context.user_data.pop('editing_setting_message_id', None)
        prompt_chat_id = context.user_data.pop('editing_setting_chat_id', None)
        if prompt_message_id and prompt_chat_id:
            try:
                context.bot.delete_message(chat_id=prompt_chat_id, message_id=prompt_message_id)
            except Exception:
                pass
        
        update.message.reply_text(
            f"вњ… РќР°СЃС‚СЂРѕР№РєР° {db_key} СѓСЃРїРµС€РЅРѕ РѕР±РЅРѕРІР»РµРЅР°!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вљ™пёЏ Р’РµСЂРЅСѓС‚СЊСЃСЏ Рє РЅР°СЃС‚СЂРѕР№РєР°Рј", callback_data='settings_main')]
            ])
        )
        
    except ValueError as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР°: {e}\nРџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·:")
    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
        
def show_web_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР° - РЎ РљРќРћРџРљРћР™ Р—РђРљР Р«РўР¬"""
    query = update.callback_query
    query.answer()
    
    web_port = settings_manager.get_setting('WEB_PORT', 5000)
    web_host = settings_manager.get_setting('WEB_HOST', '0.0.0.0')
    
    message = (
        "рџЊђ *РќР°СЃС‚СЂРѕР№РєРё РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°*\n\n"
        f"вЂў РџРѕСЂС‚: {web_port}\n"
        f"вЂў РҐРѕСЃС‚: {web_host}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ”Њ РџРѕСЂС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°", callback_data='set_web_port')],
        [InlineKeyboardButton("рџЊђ РҐРѕСЃС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°", callback_data='set_web_host')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_settings_handlers():
    """РџРѕР»СѓС‡РёС‚СЊ РѕР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РЅР°СЃС‚СЂРѕРµРє"""
    return [
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^manage_'),
        MessageHandler(Filters.text & ~Filters.command, handle_setting_value)
    ]

def show_auth_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё - РћР‘РќРћР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    # РџРѕР»СѓС‡Р°РµРј СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ Windows СѓС‡РµС‚РЅС‹Рј РґР°РЅРЅС‹Рј
    windows_creds = settings_manager.get_windows_credentials()
    
    message = (
        "рџ”ђ *РќР°СЃС‚СЂРѕР№РєРё Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё*\n\n"
        "*SSH Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ:*\n"
        f"вЂў РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ: `{ssh_username}`\n"
        f"вЂў РџСѓС‚СЊ Рє РєР»СЋС‡Сѓ: `{ssh_key_path}`\n\n"
        "*Windows Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ:*\n"
        f"вЂў РЈС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(windows_creds)}\n"
        f"вЂў РўРёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ: {len(settings_manager.get_windows_server_types())}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР» РґР»СЏ РЅР°СЃС‚СЂРѕР№РєРё:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ‘¤ SSH Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ", callback_data='ssh_auth_settings')],
        [InlineKeyboardButton("рџ–ҐпёЏ Windows Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ", callback_data='windows_auth_main')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_ssh_auth_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё SSH Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    message = (
        "рџ‘¤ *SSH Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ*\n\n"
        f"вЂў SSH РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ: `{ssh_username}`\n"
        f"вЂў РџСѓС‚СЊ Рє SSH РєР»СЋС‡Сѓ: `{ssh_key_path}`\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ‘¤ SSH РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ", callback_data='set_ssh_username')],
        [InlineKeyboardButton("рџ”‘ РџСѓС‚СЊ Рє SSH РєР»СЋС‡Сѓ", callback_data='set_ssh_key_path')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_auth'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_servers_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё СЃРµСЂРІРµСЂРѕРІ - РЎ РљРќРћРџРљРћР™ Р—РђРљР Р«РўР¬"""
    query = update.callback_query
    query.answer()
    
    servers = settings_manager.get_all_servers(include_disabled=True)
    enabled_servers = [s for s in servers if s.get('enabled', True)]
    paused_servers = [s for s in servers if not s.get('enabled', True)]
    windows_servers = [s for s in servers if s['type'] == 'rdp']
    linux_servers = [s for s in servers if s['type'] == 'ssh']
    ping_servers = [s for s in servers if s['type'] == 'ping']
    
    # РЎР±СЂР°СЃС‹РІР°РµРј СЃРѕСЃС‚РѕСЏРЅРёСЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ, РµСЃР»Рё РІРµСЂРЅСѓР»РёСЃСЊ РІ РјРµРЅСЋ
    context.user_data.pop('adding_server', None)
    context.user_data.pop('editing_server', None)
    context.user_data.pop('server_stage', None)
    context.user_data.pop('edit_server_stage', None)
    context.user_data.pop('edit_server_ip', None)
    context.user_data.pop('edit_server_data', None)

    message = (
        "рџ–ҐпёЏ *РќР°СЃС‚СЂРѕР№РєРё СЃРµСЂРІРµСЂРѕРІ*\n\n"
        f"вЂў Windows СЃРµСЂРІРµСЂРѕРІ: {len(windows_servers)}\n"
        f"вЂў Linux СЃРµСЂРІРµСЂРѕРІ: {len(linux_servers)}\n"
        f"вЂў Ping СЃРµСЂРІРµСЂРѕРІ: {len(ping_servers)}\n"
        f"вЂў Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ: {len(servers)}\n"
        f"вЂў РђРєС‚РёРІРЅС‹С…: {len(enabled_servers)}\n"
        f"вЂў РџСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅРѕ: {len(paused_servers)}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ“‹ РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ", callback_data='settings_servers_list')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ", callback_data='settings_add_server')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _get_server_by_ip(servers, ip):
    """РќР°Р№С‚Рё СЃРµСЂРІРµСЂ РїРѕ IP РёР· СЃРїРёСЃРєР°"""
    for server in servers:
        if server.get('ip') == ip:
            return server
    return None

def show_servers_list(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ СЃ РґРµР№СЃС‚РІРёСЏРјРё"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)

    # РЎР±СЂР°СЃС‹РІР°РµРј СЃРѕСЃС‚РѕСЏРЅРёСЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂРё РїРѕРєР°Р·Рµ СЃРїРёСЃРєР°
    context.user_data.pop('editing_server', None)
    context.user_data.pop('edit_server_stage', None)
    context.user_data.pop('edit_server_ip', None)
    context.user_data.pop('edit_server_data', None)

    if not servers:
        message = "рџ“‹ *РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ*\n\nвќЊ РЎРµСЂРІРµСЂС‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
        keyboard = [
            [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ", callback_data='settings_add_server')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ]
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    message_lines = ["рџ“‹ *РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ*\n"]
    for server in servers:
        status_icon = "рџџў" if server.get('enabled', True) else "вЏёпёЏ"
        status_text = "РјРѕРЅРёС‚РѕСЂРёРЅРі" if server.get('enabled', True) else "РїР°СѓР·Р°"
        message_lines.append(
            f"вЂў {status_icon} {server['name']} (`{server['ip']}`) вЂ” {server['type'].upper()} вЂ” {status_text}"
        )

    keyboard = [
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ]
    ]
    for server in servers:
        toggle_text = "вЏёпёЏ РџР°СѓР·Р°" if server.get('enabled', True) else "в–¶пёЏ Р’РѕР·РѕР±РЅРѕРІРёС‚СЊ"
        keyboard.append([
            InlineKeyboardButton(
                f"вњЏпёЏ {server['name']}",
                callback_data=f"settings_edit_server_{server['ip']}"
            ),
            InlineKeyboardButton(
                toggle_text,
                callback_data=f"settings_toggle_server_{server['ip']}"
            ),
            InlineKeyboardButton(
                "рџ—‘пёЏ",
                callback_data=f"settings_delete_server_{server['ip']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ", callback_data='settings_add_server')
    ])
    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_confirmation(update, context, ip):
    """РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    message = (
        "рџ—‘пёЏ *РЈРґР°Р»РµРЅРёРµ СЃРµСЂРІРµСЂР°*\n\n"
        f"РЎРµСЂРІРµСЂ: *{server['name']}* (`{server['ip']}`)\n"
        "РџРѕРґС‚РІРµСЂРґРёС‚Рµ СѓРґР°Р»РµРЅРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("вњ… РЈРґР°Р»РёС‚СЊ", callback_data=f"settings_confirm_delete_server_{ip}")],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_execute(update, context, ip):
    """РЈРґР°Р»РёС‚СЊ СЃРµСЂРІРµСЂ"""
    query = update.callback_query
    query.answer()

    success = settings_manager.delete_server(ip)
    if success:
        message = f"вњ… РЎРµСЂРІРµСЂ `{ip}` СѓРґР°Р»РµРЅ."
    else:
        message = f"вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СѓРґР°Р»РёС‚СЊ СЃРµСЂРІРµСЂ `{ip}`."

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ Рє СЃРїРёСЃРєСѓ", callback_data='settings_servers_list')]
        ])
    )

def show_server_edit_menu(update, context, ip):
    """РњРµРЅСЋ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    status_text = "рџџў Р’РєР»СЋС‡РµРЅ" if server.get('enabled', True) else "вЏёпёЏ РџСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"
    message = (
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ СЃРµСЂРІРµСЂР°*\n\n"
        f"вЂў РРјСЏ: *{server['name']}*\n"
        f"вЂў IP: `{server['ip']}`\n"
        f"вЂў РўРёРї: *{server['type'].upper()}*\n\n"
        f"вЂў РЎС‚Р°С‚СѓСЃ: *{status_text}*\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    toggle_text = "вЏёпёЏ РџСЂРёРѕСЃС‚Р°РЅРѕРІРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі" if server.get('enabled', True) else "в–¶пёЏ Р’РѕР·РѕР±РЅРѕРІРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі"
    keyboard = [
        [InlineKeyboardButton("рџ“ќ РР·РјРµРЅРёС‚СЊ РёРјСЏ", callback_data=f"settings_edit_server_name_{ip}")],
        [InlineKeyboardButton("рџ”§ РР·РјРµРЅРёС‚СЊ С‚РёРї", callback_data=f"settings_edit_server_type_{ip}")],
        [InlineKeyboardButton(toggle_text, callback_data=f"settings_toggle_server_{ip}")],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def toggle_server_monitoring(update, context, ip):
    """РџРµСЂРµРєР»СЋС‡РёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    new_status = not server.get('enabled', True)
    success = settings_manager.set_server_enabled(ip, new_status)

    if success:
        status_text = "рџџў РњРѕРЅРёС‚РѕСЂРёРЅРі РІРєР»СЋС‡РµРЅ" if new_status else "вЏёпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"
        message = (
            "вњ… РЎС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РѕР±РЅРѕРІР»РµРЅ.\n\n"
            f"вЂў РЎРµСЂРІРµСЂ: *{server.get('name', ip)}*\n"
            f"вЂў РЎС‚Р°С‚СѓСЃ: *{status_text}*"
        )
    else:
        message = "вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ СЃС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°."

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ Рє СЃРїРёСЃРєСѓ", callback_data='settings_servers_list')]
        ])
    )

def start_server_name_edit(update, context, ip):
    """Р—Р°РїСѓСЃРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РёРјРµРЅРё СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    context.user_data['editing_server'] = True
    context.user_data['edit_server_stage'] = 'name'
    context.user_data['edit_server_ip'] = ip
    context.user_data['edit_server_data'] = server

    query.edit_message_text(
        "рџ“ќ Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ СЃРµСЂРІРµСЂР°:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_servers_list')]
        ])
    )

def start_server_type_edit(update, context, ip):
    """Р—Р°РїСѓСЃРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ С‚РёРїР° СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    context.user_data['editing_server'] = True
    context.user_data['edit_server_stage'] = 'type'
    context.user_data['edit_server_ip'] = ip
    context.user_data['edit_server_data'] = server

    keyboard = [
        [InlineKeyboardButton("рџ–ҐпёЏ Windows (RDP)", callback_data=f"settings_edit_server_type_select_rdp_{ip}")],
        [InlineKeyboardButton("рџђ§ Linux (SSH)", callback_data=f"settings_edit_server_type_select_ssh_{ip}")],
        [InlineKeyboardButton("рџ“Ў Ping Only", callback_data=f"settings_edit_server_type_select_ping_{ip}")],
        [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_servers_list')]
    ]

    query.edit_message_text(
        "рџ”§ Р’С‹Р±РµСЂРёС‚Рµ РЅРѕРІС‹Р№ С‚РёРї СЃРµСЂРІРµСЂР°:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_server_type_selection(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІС‹Р±РѕСЂР° РЅРѕРІРѕРіРѕ С‚РёРїР° СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    if not context.user_data.get('editing_server'):
        return

    data = query.data.replace('settings_edit_server_type_select_', '')
    parts = data.split('_')
    if len(parts) < 2:
        query.edit_message_text(
            "вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РІС‹Р±РѕСЂР° С‚РёРїР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    server_type = parts[0]
    ip = "_".join(parts[1:])
    server = context.user_data.get('edit_server_data') or {}
    if server.get('ip') != ip:
        servers = settings_manager.get_all_servers(include_disabled=True)
        server = _get_server_by_ip(servers, ip)

    if not server:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers_list')]
            ])
        )
        return

    success = settings_manager.add_server(
        ip,
        server.get('name', ip),
        server_type,
        server.get('credentials'),
        server.get('timeout', 30),
        server.get('enabled', True)
    )

    context.user_data.pop('editing_server', None)
    context.user_data.pop('edit_server_stage', None)
    context.user_data.pop('edit_server_ip', None)
    context.user_data.pop('edit_server_data', None)

    if success:
        message = (
            "вњ… РўРёРї СЃРµСЂРІРµСЂР° РѕР±РЅРѕРІР»РµРЅ.\n\n"
            f"вЂў РЎРµСЂРІРµСЂ: *{server.get('name', ip)}*\n"
            f"вЂў РќРѕРІС‹Р№ С‚РёРї: *{server_type.upper()}*"
        )
    else:
        message = "вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ С‚РёРї СЃРµСЂРІРµСЂР°."

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ Рє СЃРїРёСЃРєСѓ", callback_data='settings_servers_list')]
        ])
    )

def handle_server_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ СЃРµСЂРІРµСЂР°"""
    if not context.user_data.get('editing_server'):
        return

    stage = context.user_data.get('edit_server_stage')
    if stage != 'name':
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("вќЊ РРјСЏ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    server = context.user_data.get('edit_server_data') or {}
    ip = context.user_data.get('edit_server_ip')
    if not ip:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ СЃРµСЂРІРµСЂ.")
        return

    success = settings_manager.add_server(
        ip,
        new_name,
        server.get('type', 'ping'),
        server.get('credentials'),
        server.get('timeout', 30),
        server.get('enabled', True)
    )

    context.user_data.pop('editing_server', None)
    context.user_data.pop('edit_server_stage', None)
    context.user_data.pop('edit_server_ip', None)
    context.user_data.pop('edit_server_data', None)

    if success:
        message = (
            "вњ… РРјСЏ СЃРµСЂРІРµСЂР° РѕР±РЅРѕРІР»РµРЅРѕ.\n\n"
            f"вЂў IP: `{ip}`\n"
            f"вЂў РќРѕРІРѕРµ РёРјСЏ: *{new_name}*"
        )
    else:
        message = "вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ РёРјСЏ СЃРµСЂРІРµСЂР°."

    update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ Рє СЃРїРёСЃРєСѓ", callback_data='settings_servers_list')]
        ])
    )

def show_backup_times(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РІСЂРµРјРµРЅРЅС‹С… РёРЅС‚РµСЂРІР°Р»РѕРІ Р±СЌРєР°РїРѕРІ - РЎ РљРќРћРџРљРћР™ Р—РђРљР Р«РўР¬"""
    query = update.callback_query
    query.answer()
    
    alert_hours = settings_manager.get_setting('BACKUP_ALERT_HOURS', 24)
    stale_hours = settings_manager.get_setting('BACKUP_STALE_HOURS', 36)
    
    message = (
        "вЏ° *Р’СЂРµРјРµРЅРЅС‹Рµ РёРЅС‚РµСЂРІР°Р»С‹ Р±СЌРєР°РїРѕРІ*\n\n"
        f"вЂў РђР»РµСЂС‚С‹ С‡РµСЂРµР·: {alert_hours} С‡Р°СЃРѕРІ\n"
        f"вЂў РЈСЃС‚Р°СЂРµРІР°РЅРёРµ С‡РµСЂРµР·: {stale_hours} С‡Р°СЃРѕРІ\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџљЁ Р§Р°СЃС‹ РґР»СЏ Р°Р»РµСЂС‚РѕРІ", callback_data='set_backup_alert_hours')],
        [InlineKeyboardButton("рџ“… Р§Р°СЃС‹ РґР»СЏ СѓСЃС‚Р°СЂРµРІР°РЅРёСЏ", callback_data='set_backup_stale_hours')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ Р±СЌРєР°РїРѕРІ - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()

    # РЎР±СЂР°СЃС‹РІР°РµРј СЃРѕСЃС‚РѕСЏРЅРёСЏ РґРѕР±Р°РІР»РµРЅРёСЏ/СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Р‘Р” РїСЂРё РІС‹С…РѕРґРµ РІ РјРµРЅСЋ
    context.user_data.pop('adding_db_entry', None)
    context.user_data.pop('editing_db_entry', None)
    context.user_data.pop('db_entry_category', None)
    context.user_data.pop('db_entry_key', None)
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "рџ—ѓпёЏ *РќР°СЃС‚СЂРѕР№РєРё Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ Р±СЌРєР°РїРѕРІ*\n\n"
    
    if not db_config:
        message += "вќЊ *Р‘Р°Р·С‹ РґР°РЅРЅС‹С… РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n\n"
    else:
        for category, databases in db_config.items():
            if not isinstance(databases, dict):
                databases = {}
            message += f"*{category.upper()}* ({len(databases)} Р‘Р”):\n"
            for db_key in databases.keys():
                message += f"вЂў `{db_key}`\n"
            message += "\n"
    
    message += "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    
    keyboard = []

    for category, databases in db_config.items():
        if not isinstance(databases, dict):
            databases = {}
        keyboard.append([InlineKeyboardButton(
            f"вћ• Р”РѕР±Р°РІРёС‚СЊ Р‘Р” РІ {category}",
            callback_data=f"settings_db_add_db_{category}"
        )])
        row = []
        for db_key in databases.keys():
            row.append(InlineKeyboardButton(
                f"вњЏпёЏ {db_key}",
                callback_data=f"settings_db_edit_db_{category}__{db_key}"
            ))
            row.append(InlineKeyboardButton(
                f"рџ—‘пёЏ {db_key}",
                callback_data=f"settings_db_delete_db_{category}__{db_key}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    keyboard.extend([
        [InlineKeyboardButton("рџ“‹ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… Р‘Р”", callback_data='settings_db_view_all')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ Р‘Р”", callback_data='settings_db_add_category')],
        [InlineKeyboardButton("рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='settings_db_delete_category')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_backup_db'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ Р±СЌРєР°РїРѕРІ - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "рџ—ѓпёЏ *РќР°СЃС‚СЂРѕР№РєРё Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ Р±СЌРєР°РїРѕРІ*\n\n"
    
    for category, databases in db_config.items():
        message += f"*{category.upper()}* ({len(databases)} Р‘Р”):\n"
        for db_key, db_name in list(databases.items())[:3]:
            message += f"вЂў {db_name}\n"
        if len(databases) > 3:
            message += f"вЂў ... Рё РµС‰Рµ {len(databases) - 3} Р‘Р”\n"
        message += "\n"
    
    message += "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    
    keyboard = [
        [InlineKeyboardButton("рџ“‹ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… Р‘Р”", callback_data='view_all_databases')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ Р‘Р”", callback_data='add_database'),
         InlineKeyboardButton("вњЏпёЏ Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ Р‘Р”", callback_data='edit_databases')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_backup_db'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_settings_extensions_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РјРµРЅСЋ СЂР°СЃС€РёСЂРµРЅРёР№ РІ РЅР°СЃС‚СЂРѕР№РєР°С…"""
    query = update.callback_query
    query.answer()

    message = "рџ§© *Р Р°СЃС€РёСЂРµРЅРёСЏ*\n\nР’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:"

    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ’ѕ Р‘СЌРєР°РїС‹ Proxmox", callback_data='settings_ext_backup_proxmox')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ—ѓпёЏ Р‘СЌРєР°РїС‹ Р‘Р”", callback_data='settings_ext_backup_db')])

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“¬ Р‘СЌРєР°РїС‹ РїРѕС‡С‚С‹", callback_data='settings_ext_backup_mail')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“¦ Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ 1РЎ", callback_data='settings_ext_stock_load')])

    if extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        keyboard.append([InlineKeyboardButton("рџ“¦ РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ", callback_data='settings_ext_supplier_stock')])

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append([InlineKeyboardButton("рџ§Љ ZFS", callback_data='settings_zfs')])

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("рџ’» Р РµСЃСѓСЂСЃС‹", callback_data='settings_resources')])

    keyboard.extend([
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_extensions_settings_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СѓРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё СЃ РІРѕР·РІСЂР°С‚РѕРј РІ РЅР°СЃС‚СЂРѕР№РєРё"""
    query = update.callback_query
    query.answer()

    extensions_status = extension_manager.get_extensions_status()

    message = "рџ› пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё*\n\n"
    message += "рџ“Љ *РЎС‚Р°С‚СѓСЃ СЂР°СЃС€РёСЂРµРЅРёР№:*\n\n"

    keyboard = []

    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']

        status_icon = "рџџў" if enabled else "рџ”ґ"
        toggle_text = "рџ”ґ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "рџџў Р’РєР»СЋС‡РёС‚СЊ"

        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   РЎС‚Р°С‚СѓСЃ: {'Р’РєР»СЋС‡РµРЅРѕ' if enabled else 'РћС‚РєР»СЋС‡РµРЅРѕ'}\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}",
                callback_data=f'settings_ext_toggle_{ext_id}'
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("рџ“Љ Р’РєР»СЋС‡РёС‚СЊ РІСЃРµ", callback_data='settings_ext_enable_all')],
        [InlineKeyboardButton("рџ“‹ РћС‚РєР»СЋС‡РёС‚СЊ РІСЃРµ", callback_data='settings_ext_disable_all')],
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ]
    ])

    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_mail_backup_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹ РІ СЂР°Р·РґРµР»Рµ СЂР°СЃС€РёСЂРµРЅРёР№"""
    query = update.callback_query
    query.answer()

    pattern_count = 0
    source_label = "Р±Р°Р·Р°"
    patterns = settings_manager.get_backup_patterns()
    if isinstance(patterns, str):
        try:
            patterns = json.loads(patterns)
        except json.JSONDecodeError:
            patterns = {}
    mail_patterns = patterns.get("mail", {})
    if isinstance(mail_patterns, dict):
        pattern_count = len(mail_patterns.get("subject", []))
    elif isinstance(mail_patterns, list):
        pattern_count = len(mail_patterns)

    if pattern_count == 0:
        fallback_patterns = _get_mail_fallback_patterns()
        pattern_count = len(fallback_patterns)
        if pattern_count:
            source_label = "РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ"
        else:
            source_label = "РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹"

    message = (
        "рџ“¬ *Р‘СЌРєР°РїС‹ РїРѕС‡С‚С‹*\n\n"
        f"РџР°С‚С‚РµСЂРЅРѕРІ: {pattern_count} ({source_label})\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”Ќ РџР°С‚С‚РµСЂРЅС‹", callback_data='settings_patterns_mail')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_stock_load_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ 1РЎ РІ СЂР°Р·РґРµР»Рµ СЂР°СЃС€РёСЂРµРЅРёР№."""
    query = update.callback_query
    query.answer()

    pattern_count = 0
    source_label = "Р±Р°Р·Р°"
    patterns = settings_manager.get_backup_patterns()
    if isinstance(patterns, str):
        try:
            patterns = json.loads(patterns)
        except json.JSONDecodeError:
            patterns = {}

    stock_patterns = patterns.get("stock_load", {})
    if isinstance(stock_patterns, dict):
        pattern_count = sum(
            len(value) for value in stock_patterns.values() if isinstance(value, list)
        )

    if pattern_count == 0:
        fallback_patterns = _get_stock_load_fallback_patterns()
        pattern_count = sum(len(value) for value in fallback_patterns.values())
        if pattern_count:
            source_label = "РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ"
        else:
            source_label = "РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹"

    message = (
        "рџ“¦ *Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ 1РЎ*\n\n"
        f"РџР°С‚С‚РµСЂРЅРѕРІ: {pattern_count} ({source_label})\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”Ќ РџР°С‚С‚РµСЂРЅС‹", callback_data='settings_patterns_stock')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РїРѕР»СѓС‡РµРЅРёСЏ С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)
    context.user_data.pop('supplier_stock_archive_cleanup_back', None)
    context.user_data.pop('supplier_stock_archive_cleanup_back', None)
    context.user_data.pop('supplier_stock_add_source', None)
    context.user_data.pop('supplier_stock_mail_edit', None)
    context.user_data.pop('supplier_stock_mail_add_source', None)
    context.user_data.pop('supplier_stock_processing_add', None)
    context.user_data.pop('supplier_stock_processing_stage', None)
    context.user_data.pop('supplier_stock_processing_data', None)
    context.user_data.pop('supplier_stock_processing_edit', None)
    context.user_data.pop('supplier_stock_processing_edit_id', None)
    context.user_data.pop('supplier_stock_source_settings_id', None)
    context.user_data.pop('supplier_stock_mail_source_settings_id', None)
    context.user_data.pop('supplier_stock_source_field', None)
    context.user_data.pop('supplier_stock_source_field_id', None)
    context.user_data.pop('supplier_stock_mail_source_field', None)
    context.user_data.pop('supplier_stock_mail_source_field_id', None)
    context.user_data.pop('supplier_stock_resource_settings_id', None)
    context.user_data.pop('supplier_stock_resource_field', None)
    context.user_data.pop('supplier_stock_resource_field_id', None)
    context.user_data.pop('supplier_stock_resource_add', None)
    context.user_data.pop('supplier_stock_resource_stage', None)
    context.user_data.pop('supplier_stock_resource_data', None)
    context.user_data.pop('supplier_stock_ftp_field', None)

    config = get_supplier_stock_config()
    download = config.get("download", {})
    sources = download.get("sources", [])
    schedule = download.get("schedule", {})
    mail_settings = config.get("mail", {})
    mail_status = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if mail_settings.get("enabled") else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    mail_rules = len(mail_settings.get("sources", []))

    schedule_state = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if schedule.get("enabled") else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    schedule_time = schedule.get("time", "РЅРµ Р·Р°РґР°РЅРѕ")

    reporting_days = config.get("reporting", {}).get("period_days", 7)
    message = (
        "рџ“¦ *РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ*\n\n"
        f"РСЃС‚РѕС‡РЅРёРєРѕРІ: {len(sources)}\n"
        f"Р Р°СЃРїРёСЃР°РЅРёРµ: {schedule_state} ({schedule_time})\n\n"
        "рџ“§ *РџРѕС‡С‚РѕРІС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ (РѕСЃС‚Р°С‚РєРё)*\n\n"
        f"РЎС‚Р°С‚СѓСЃ: {mail_status}\n"
        f"РџСЂР°РІРёР»: {mail_rules}\n\n"
        "рџ—“ *РћС‚С‡С‘С‚С‹*\n"
        f"РџРµСЂРёРѕРґ: {reporting_days} РґРЅ.\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:"
    )

    keyboard = [
        [InlineKeyboardButton("рџЊђ РЎРєР°С‡РёРІР°РЅРёРµ С„Р°Р№Р»РѕРІ", callback_data='supplier_stock_download')],
        [InlineKeyboardButton("рџ“§ РџРѕС‡С‚РѕРІС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ", callback_data='supplier_stock_mail')],
        [InlineKeyboardButton("рџ—“ РџРµСЂРёРѕРґ РѕС‚С‡С‘С‚РѕРІ", callback_data='supplier_stock_report_period')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_extensions'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _format_supplier_stock_timestamp(value: str | None) -> str:
    """РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ С‡РёС‚Р°РµРјРѕРµ РІСЂРµРјСЏ Р·Р°РїСѓСЃРєР°."""
    if not value:
        return "РЅРµРёР·РІРµСЃС‚РЅРѕ"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(value)

def _supplier_stock_status_label(status: str | None, fallback: str = "РЅРµРёР·РІРµСЃС‚РЅРѕ") -> str:
    """РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ РєРѕСЂРѕС‚РєСѓСЋ РјРµС‚РєСѓ СЃС‚Р°С‚СѓСЃР°."""
    if status == "success":
        return "рџџў СѓСЃРїРµС€РЅРѕ"
    if status == "error":
        return "рџ”ґ РѕС€РёР±РєР°"
    if status == "skipped":
        return "вљЄпёЏ РїСЂРѕРїСѓС‰РµРЅРѕ"
    return f"рџџЎ {fallback}"

def _supplier_stock_processing_status(processing: dict | None) -> str:
    """РћРїСЂРµРґРµР»РёС‚СЊ СЃС‚Р°С‚СѓСЃ РѕР±СЂР°Р±РѕС‚РєРё."""
    if not processing:
        return "вЏ­пёЏ РЅРµ Р·Р°РїСѓСЃРєР°Р»Р°СЃСЊ"
    if processing.get("status") == "skipped":
        return "вљЄпёЏ РїСЂРѕРїСѓС‰РµРЅРѕ"
    results = processing.get("results") or []
    if not results:
        return "рџџЎ РЅРµС‚ СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ"
    statuses = [item.get("status") for item in results if isinstance(item, dict)]
    if not statuses:
        return "рџџЎ РЅРµС‚ СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ"
    if all(status == "success" for status in statuses):
        return "рџџў СѓСЃРїРµС€РЅРѕ"
    if any(status == "error" for status in statuses):
        return "рџ”ґ РѕС€РёР±РєР°"
    if all(status == "skipped" for status in statuses):
        return "вљЄпёЏ РїСЂРѕРїСѓС‰РµРЅРѕ"
    return "рџџЎ С‡Р°СЃС‚РёС‡РЅРѕ"

def _supplier_stock_transfer_status(transfer: dict | None) -> str:
    """РћРїСЂРµРґРµР»РёС‚СЊ СЃС‚Р°С‚СѓСЃ РІС‹РіСЂСѓР·РєРё."""
    if not transfer:
        return "вЏ­пёЏ РЅРµ Р·Р°РїСѓСЃРєР°Р»Р°СЃСЊ"
    status = transfer.get("status")
    if status == "skipped":
        return "вљЄпёЏ РїСЂРѕРїСѓС‰РµРЅРѕ"
    if status and status != "success":
        return "рџ”ґ РѕС€РёР±РєР°"
    items = transfer.get("items") or []
    ftp_items = transfer.get("ftp_ork", {}).get("items") or []
    statuses = [
        item.get("status")
        for item in list(items) + list(ftp_items)
        if isinstance(item, dict)
    ]
    if not statuses:
        return "рџџЎ РЅРµС‚ С„Р°Р№Р»РѕРІ"
    if all(status == "success" for status in statuses):
        return "рџџў СѓСЃРїРµС€РЅРѕ"
    if any(status == "error" for status in statuses):
        return "рџ”ґ РѕС€РёР±РєР°"
    return "рџџЎ С‡Р°СЃС‚РёС‡РЅРѕ"

def _supplier_stock_stage_label(is_ok: bool) -> str:
    return "РћРљ" if is_ok else "РЅРµ РћРљ"

def _supplier_stock_processing_ok(processing: dict | None) -> bool:
    if not processing:
        return False
    if processing.get("status") == "skipped":
        return False
    results = processing.get("results") or []
    statuses = [item.get("status") for item in results if isinstance(item, dict)]
    if not statuses:
        return False
    return all(status == "success" for status in statuses)

def _supplier_stock_transfer_ok(transfer: dict | None) -> bool:
    if not transfer:
        return False
    status = transfer.get("status")
    if status == "skipped":
        return False
    items = transfer.get("items") or []
    ftp_items = transfer.get("ftp_ork", {}).get("items") or []
    statuses = [
        item.get("status")
        for item in list(items) + list(ftp_items)
        if isinstance(item, dict)
    ]
    if not statuses:
        return False
    return status == "success" and all(item_status == "success" for item_status in statuses)

def _build_supplier_stock_daily_summary(
    reports: list[dict],
    source_kind: str,
) -> list[dict]:
    summary: list[dict] = []
    seen_sources: set[str] = set()
    for entry in reports:
        source_id = str(entry.get("source_id") or entry.get("source_name") or "unknown")
        if source_id in seen_sources:
            continue
        seen_sources.add(source_id)
        processing_info = entry.get("processing") if entry.get("status") == "success" else None
        receive_ok = entry.get("status") == "success"
        processing_ok = _supplier_stock_processing_ok(processing_info)
        transfer_ok = _supplier_stock_transfer_ok(
            processing_info.get("transfer") if processing_info else None
        )
        summary.append({
            "entry": entry,
            "source_id": source_id,
            "source_name": entry.get("source_name") or source_id,
            "source_kind": source_kind,
            "receive_ok": receive_ok,
            "processing_ok": processing_ok,
            "transfer_ok": transfer_ok,
        })
    return summary

def _supplier_stock_processing_mode_label(value: str | None) -> str:
    """РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ С‡РёС‚Р°РµРјСѓСЋ РјРµС‚РєСѓ СЂРµР¶РёРјР° РѕР±СЂР°Р±РѕС‚РєРё."""
    mode = (value or "table").strip().lower()
    if mode == "iek_json":
        return "IEK JSON"
    return "РўР°Р±Р»РёС‡РЅС‹Р№"

def show_supplier_stock_reports(update, context, source_kind: str = "download") -> None:
    """РџРѕРєР°Р·Р°С‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚С‹ Р·Р°РіСЂСѓР·РєРё, РѕР±СЂР°Р±РѕС‚РєРё Рё РІС‹РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    query = update.callback_query
    query.answer()

    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        query.edit_message_text(
            "рџ“¦ РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ РѕС‚РєР»СЋС‡РµРЅС‹ РІ РЅР°СЃС‚СЂРѕР№РєР°С….",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')]]
            ),
        )
        return

    reporting_days = 1
    reports = get_supplier_stock_reports(limit=None, period_days=reporting_days, source_kind=source_kind)
    title = "РїРѕР»СѓС‡РµРЅРЅС‹Рµ СЃРєР°С‡РёРІР°РЅРёРµРј" if source_kind == "download" else "РїРѕР»СѓС‡РµРЅРЅС‹Рµ РїРѕ РїРѕС‡С‚Рµ"
    message_lines = [
        "рџ“¦ *РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ вЂ” СЂРµР·СѓР»СЊС‚Р°С‚С‹*",
        "",
        f"Р“СЂСѓРїРїР°: {title}",
        "РџРµСЂРёРѕРґ: РїРѕСЃР»РµРґРЅРёРµ 24 С‡Р°СЃР°",
        "",
    ]
    summary = _build_supplier_stock_daily_summary(reports, source_kind)
    if not summary:
        message_lines.append("вљЄпёЏ Р—Р° СЃСѓС‚РєРё РґР°РЅРЅС‹С… РЅРµС‚.")
    else:
        message_lines.append("РљР»РёРєРЅРё РёСЃС‚РѕС‡РЅРёРє, С‡С‚РѕР±С‹ РѕС‚РєСЂС‹С‚СЊ РёСЃС‚РѕСЂРёСЋ Р·Р° СЃСѓС‚РєРё.")
        for entry in summary:
            source_name = _escape_pattern_text(entry.get("source_name") or "РЅРµРёР·РІРµСЃС‚РЅС‹Р№ РёСЃС‚РѕС‡РЅРёРє")
            receive_label = _supplier_stock_stage_label(entry["receive_ok"])
            processing_label = _supplier_stock_stage_label(entry["processing_ok"])
            transfer_label = _supplier_stock_stage_label(entry["transfer_ok"])
            message_lines.extend([
                "",
                f"вЂў *{source_name}*",
                f"  рџ“Ґ Р—Р°РіСЂСѓР·РєР°: {receive_label}",
                f"  рџ§© РћР±СЂР°Р±РѕС‚РєР°: {processing_label}",
                f"  рџ“¤ Р’С‹РіСЂСѓР·РєР°: {transfer_label}",
            ])

    def _split_message(lines: list[str], max_length: int = 3500) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for line in lines:
            candidate_len = current_len + len(line) + (1 if current else 0)
            if current and candidate_len > max_length:
                chunks.append("\n".join(current))
                current = [line]
                current_len = len(line)
            else:
                current.append(line)
                current_len = candidate_len
        if current:
            chunks.append("\n".join(current))
        return chunks

    message_chunks = _split_message(message_lines)
    keyboard = [
        [
            InlineKeyboardButton("в¬‡пёЏ РЎРєР°С‡РёРІР°РЅРёРµ", callback_data='supplier_stock_reports_download'),
            InlineKeyboardButton("рџ“§ РџРѕС‡С‚Р°", callback_data='supplier_stock_reports_mail'),
        ],
    ]
    entry_map: dict[str, dict] = {}
    if summary:
        for index, item in enumerate(summary, start=1):
            entry_key = str(index)
            entry_map[entry_key] = item
            source_id = str(item.get("source_id") or "")
            source_name = str(item.get("source_name") or source_id)
            source_label = source_name[:24]
            row = [
                InlineKeyboardButton(
                    f"рџ“Љ {source_label}",
                    callback_data=f'supplier_stock_report_source_day|{source_kind}|{source_id}',
                )
            ]
            if not (item.get("receive_ok") and item.get("processing_ok") and item.get("transfer_ok")):
                row.append(
                    InlineKeyboardButton(
                        "вќ— Р”РµС‚Р°Р»Рё",
                        callback_data=f'supplier_stock_report_entry|{entry_key}',
                    )
                )
            keyboard.append(row)
        context.user_data["supplier_stock_report_entries"] = entry_map
        context.user_data["supplier_stock_report_entries_kind"] = source_kind
    keyboard.extend([
        [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data=f'supplier_stock_reports_{source_kind}')],
        [InlineKeyboardButton("рџ› пёЏ РќР°СЃС‚СЂРѕР№РєРё", callback_data='settings_ext_supplier_stock')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
    ])

    query.edit_message_text(
        message_chunks[0] if message_chunks else "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    for chunk in message_chunks[1:]:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=chunk,
            parse_mode='Markdown',
        )


def show_supplier_stock_report_sources(update, context, source_kind: str = "download") -> None:
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє РёСЃС‚РѕС‡РЅРёРєРѕРІ РѕСЃС‚Р°С‚РєРѕРІ СЃ С‚РµРєСѓС‰РёРјРё СЃС‚Р°С‚СѓСЃР°РјРё."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    reporting_days = config.get("reporting", {}).get("period_days", 7)
    grouped = summarize_supplier_stock_reports(period_days=reporting_days)
    sources = grouped.get(source_kind, [])
    group_label = "РїРѕР»СѓС‡РµРЅРЅС‹Рµ СЃРєР°С‡РёРІР°РЅРёРµРј" if source_kind == "download" else "РїРѕР»СѓС‡РµРЅРЅС‹Рµ РїРѕ РїРѕС‡С‚Рµ"

    message_lines = [
        "рџ“¦ *РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ вЂ” РёСЃС‚РѕС‡РЅРёРєРё*",
        "",
        f"Р“СЂСѓРїРїР°: {group_label}",
        f"РџРµСЂРёРѕРґ: {reporting_days} РґРЅ.",
        "",
    ]

    if not sources:
        message_lines.append("вљЄпёЏ РСЃС‚РѕС‡РЅРёРєРѕРІ Р·Р° РїРµСЂРёРѕРґ РЅРµС‚.")
    else:
        for entry in sources:
            source_name = entry.get("source_name") or entry.get("source_id") or "РЅРµРёР·РІРµСЃС‚РЅС‹Р№ РёСЃС‚РѕС‡РЅРёРє"
            time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
            message_lines.extend([
                "",
                f"вЂў *{_escape_pattern_text(source_name)}* ({_escape_pattern_text(time_label)})",
                f"  рџ“Ґ Р—Р°РіСЂСѓР·РєР°: {entry.get('receive', {}).get('icon', 'вљЄпёЏ')}",
                f"  рџ§© РћР±СЂР°Р±РѕС‚РєР°: {entry.get('processing', {}).get('icon', 'вљЄпёЏ')}",
                f"  рџ“¤ Р’С‹РіСЂСѓР·РєР°: {entry.get('transfer', {}).get('icon', 'вљЄпёЏ')}",
            ])

    keyboard = [
        [
            InlineKeyboardButton("в¬‡пёЏ РЎРєР°С‡РёРІР°РЅРёРµ", callback_data='supplier_stock_reports_sources_download'),
            InlineKeyboardButton("рџ“§ РџРѕС‡С‚Р°", callback_data='supplier_stock_reports_sources_mail'),
        ],
    ]
    if sources:
        row: list[InlineKeyboardButton] = []
        for entry in sources:
            source_id = str(entry.get("source_id") or entry.get("source_name") or "")
            if not source_id:
                continue
            row.append(
                InlineKeyboardButton(
                    f"рџ“Љ {source_id}",
                    callback_data=f'supplier_stock_report_source|{source_kind}|{source_id}',
                )
            )
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
    keyboard.extend([
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_reports_{source_kind}')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
    ])

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def show_supplier_stock_report_source_stats(
    update,
    context,
    source_id: str,
    source_kind: str = "download",
    period_days: int | None = None,
) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РїРѕРґСЂРѕР±РЅСѓСЋ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ РёСЃС‚РѕС‡РЅРёРєСѓ РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    if not source_id:
        query.edit_message_text(
            "вљЄпёЏ РСЃС‚РѕС‡РЅРёРє РЅРµ РІС‹Р±СЂР°РЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_reports_sources_{source_kind}')],
            ]),
        )
        return

    if period_days is None:
        config = get_supplier_stock_config()
        reporting_days = config.get("reporting", {}).get("period_days", 7)
    else:
        reporting_days = period_days
    stats = build_supplier_stock_source_stats(source_id, source_kind, reporting_days)
    summary = stats.get("summary", {})
    entries = stats.get("entries", [])

    message_lines = [
        "рџ“¦ *РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ вЂ” СЃС‚Р°С‚РёСЃС‚РёРєР° РёСЃС‚РѕС‡РЅРёРєР°*",
        "",
        f"РСЃС‚РѕС‡РЅРёРє: {_escape_pattern_text(source_id)}",
        f"Р“СЂСѓРїРїР°: {'РїРѕР»СѓС‡РµРЅРЅС‹Рµ СЃРєР°С‡РёРІР°РЅРёРµРј' if source_kind == 'download' else 'РїРѕР»СѓС‡РµРЅРЅС‹Рµ РїРѕ РїРѕС‡С‚Рµ'}",
        f"РџРµСЂРёРѕРґ: {reporting_days} РґРЅ.",
        "",
        f"Р’СЃРµРіРѕ Р·Р°РїСѓСЃРєРѕРІ: {summary.get('total', 0)}",
        f"рџ“Ґ РЈСЃРїРµС€РЅРѕ: {summary.get('receive_success', 0)} | РћС€РёР±РѕРє: {summary.get('receive_error', 0)}",
        f"рџ§© РЈСЃРїРµС€РЅРѕ: {summary.get('processing_success', 0)} | РћС€РёР±РѕРє: {summary.get('processing_error', 0)}",
        f"рџ“¤ РЈСЃРїРµС€РЅРѕ: {summary.get('transfer_success', 0)} | РћС€РёР±РѕРє: {summary.get('transfer_error', 0)}",
        "",
        "*РџРѕСЃР»РµРґРЅРёРµ СЃРѕР±С‹С‚РёСЏ:*",
    ]

    if not entries:
        message_lines.append("вљЄпёЏ Р—Р°РїРёСЃРµР№ РїРѕРєР° РЅРµС‚.")
    else:
        for entry in entries[:10]:
            time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
            message_lines.extend([
                "",
                f"вЂў {_escape_pattern_text(time_label)}",
                f"  рџ“Ґ {entry.get('receive', {}).get('icon', 'вљЄпёЏ')}",
                f"  рџ§© {entry.get('processing', {}).get('icon', 'вљЄпёЏ')}",
                f"  рџ“¤ {entry.get('transfer', {}).get('icon', 'вљЄпёЏ')}",
            ])
            if entry.get("error"):
                message_lines.append(f"  вќ— РћС€РёР±РєР°: {_escape_pattern_text(entry.get('error'))}")

    keyboard = [
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_reports_sources_{source_kind}')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
    ]

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def show_supplier_stock_report_entry_details(update, context, entry_key: str) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РґРµС‚Р°Р»Рё РїРѕСЃР»РµРґРЅРµРіРѕ Р·Р°РїСѓСЃРєР° РїРѕ РёСЃС‚РѕС‡РЅРёРєСѓ."""
    query = update.callback_query
    query.answer()

    entry_map = context.user_data.get("supplier_stock_report_entries", {})
    source_kind = context.user_data.get("supplier_stock_report_entries_kind", "download")
    summary = entry_map.get(entry_key)
    if not summary:
        query.edit_message_text(
            "вљЄпёЏ Р”РµС‚Р°Р»Рё РЅРµРґРѕСЃС‚СѓРїРЅС‹, РѕР±РЅРѕРІРёС‚Рµ СЂРµР·СѓР»СЊС‚Р°С‚С‹.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_reports_{source_kind}')],
            ]),
        )
        return

    entry = summary.get("entry", {})
    source_id = summary.get("source_id") or entry.get("source_id") or "РЅРµРёР·РІРµСЃС‚РЅРѕ"
    source_name = entry.get("source_name") or source_id
    time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
    download_status = _supplier_stock_status_label(entry.get("status"))
    processing_info = entry.get("processing") if entry.get("status") == "success" else None
    processing_status = _supplier_stock_processing_status(processing_info)
    transfer_status = _supplier_stock_transfer_status(
        processing_info.get("transfer") if processing_info else None
    )
    if entry.get("status") != "success":
        processing_status = "вЏ­пёЏ РЅРµ Р·Р°РїСѓСЃРєР°Р»Р°СЃСЊ"
        transfer_status = "вЏ­пёЏ РЅРµ Р·Р°РїСѓСЃРєР°Р»Р°СЃСЊ"

    message_lines = [
        "рџ“¦ *РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ вЂ” РїРѕРґСЂРѕР±РЅРѕСЃС‚Рё*",
        "",
        f"РСЃС‚РѕС‡РЅРёРє: {_escape_pattern_text(source_name)}",
        f"Р“СЂСѓРїРїР°: {'РїРѕР»СѓС‡РµРЅРЅС‹Рµ СЃРєР°С‡РёРІР°РЅРёРµРј' if source_kind == 'download' else 'РїРѕР»СѓС‡РµРЅРЅС‹Рµ РїРѕ РїРѕС‡С‚Рµ'}",
        f"Р—Р°РїСѓСЃРє: {_escape_pattern_text(time_label)}",
        "",
        f"рџ“Ґ Р—Р°РіСЂСѓР·РєР°: {download_status}",
        f"рџ§© РћР±СЂР°Р±РѕС‚РєР°: {processing_status}",
        f"рџ“¤ Р’С‹РіСЂСѓР·РєР°: {transfer_status}",
    ]
    if entry.get("error"):
        message_lines.append(f"\nвќ— РћС€РёР±РєР°: {_escape_pattern_text(entry.get('error'))}")

    keyboard = [
        [InlineKeyboardButton(
            "рџ“Љ РСЃС‚РѕСЂРёСЏ РёСЃС‚РѕС‡РЅРёРєР°",
            callback_data=f'supplier_stock_report_source_day|{source_kind}|{source_id}',
        )],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_reports_{source_kind}')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
    ]

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

def show_supplier_stock_download_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё СЃРєР°С‡РёРІР°РЅРёСЏ С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)

    config = get_supplier_stock_config()
    download = config.get("download", {})
    temp_dir = download.get("temp_dir", "")
    sources = download.get("sources", [])
    schedule = download.get("schedule", {})
    unpack_enabled = sum(1 for source in sources if source.get("unpack_archive"))
    unpack_state = f"{unpack_enabled}/{len(sources)}" if sources else "РЅРµС‚"
    schedule_state = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if schedule.get("enabled") else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    schedule_time = schedule.get("time", "РЅРµ Р·Р°РґР°РЅРѕ")
    archive_cleanup = _format_archive_cleanup_days(config.get("archive_cleanup_days"))

    message = (
        "рџ“¦ *РЎРєР°С‡РёРІР°РЅРёРµ С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ*\n\n"
        f"Р’СЂРµРјРµРЅРЅС‹Р№ РєР°С‚Р°Р»РѕРі: `{temp_dir}`\n"
        f"РђСЂС…РёРІ: `{download.get('archive_dir', '')}`\n"
        f"РћС‡РёСЃС‚РєР° Р°СЂС…РёРІР°: {archive_cleanup}\n"
        f"Р Р°СЃРїР°РєРѕРІРєР° РІ РёСЃС‚РѕС‡РЅРёРєР°С…: {unpack_state}\n"
        f"РСЃС‚РѕС‡РЅРёРєРѕРІ: {len(sources)}\n"
        f"Р Р°СЃРїРёСЃР°РЅРёРµ: {schedule_state} ({schedule_time})\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ“Ѓ Р’СЂРµРјРµРЅРЅС‹Р№ РєР°С‚Р°Р»РѕРі", callback_data='supplier_stock_temp_dir')],
        [InlineKeyboardButton("рџ—„пёЏ РљР°С‚Р°Р»РѕРі Р°СЂС…РёРІР°", callback_data='supplier_stock_archive_dir')],
        [InlineKeyboardButton("рџ§№ РџРµСЂРёРѕРґ РѕС‡РёСЃС‚РєРё Р°СЂС…РёРІР°", callback_data='supplier_stock_archive_cleanup_download')],
        [InlineKeyboardButton("вЏ° Р Р°СЃРїРёСЃР°РЅРёРµ", callback_data='supplier_stock_schedule')],
        [InlineKeyboardButton("рџ“¦ РСЃС‚РѕС‡РЅРёРєРё", callback_data='supplier_stock_sources')],
        [InlineKeyboardButton("рџ“¤ Р РµСЃСѓСЂСЃС‹ РІС‹РіСЂСѓР·РєРё", callback_data='supplier_stock_resources')],
        [InlineKeyboardButton("рџ“Ў FTP РћР Рљ", callback_data='supplier_stock_ftp')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_supplier_stock'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_mail_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РїРѕР»СѓС‡РµРЅРёСЏ РѕСЃС‚Р°С‚РєРѕРІ С‡РµСЂРµР· РїРѕС‡С‚Сѓ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_mail_edit', None)
    context.user_data.pop('supplier_stock_archive_cleanup_back', None)
    context.user_data.pop('supplier_stock_mail_add_source', None)
    context.user_data.pop('supplier_stock_mail_source_stage', None)
    context.user_data.pop('supplier_stock_mail_source_data', None)
    context.user_data.pop('supplier_stock_mail_edit_source', None)
    context.user_data.pop('supplier_stock_mail_edit_source_stage', None)
    context.user_data.pop('supplier_stock_mail_edit_source_id', None)

    config = get_supplier_stock_config()
    mail_settings = config.get("mail", {})
    sources = mail_settings.get("sources", [])
    status_text = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if mail_settings.get("enabled") else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    temp_dir = mail_settings.get("temp_dir") or ""
    archive_dir = mail_settings.get("archive_dir") or ""
    unpack_enabled = sum(1 for source in sources if source.get("unpack_archive"))
    unpack_state = f"{unpack_enabled}/{len(sources)}" if sources else "РЅРµС‚"
    archive_cleanup = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
    message = (
        "рџ“§ *РџРѕС‡С‚РѕРІС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ (РѕСЃС‚Р°С‚РєРё)*\n\n"
        f"РЎС‚Р°С‚СѓСЃ: {status_text}\n"
        f"Р’СЂРµРјРµРЅРЅС‹Р№ РєР°С‚Р°Р»РѕРі: `{_escape_pattern_text(temp_dir)}`\n"
        f"РђСЂС…РёРІ: `{_escape_pattern_text(archive_dir)}`\n"
        f"РћС‡РёСЃС‚РєР° Р°СЂС…РёРІР°: {archive_cleanup}\n"
        f"Р Р°СЃРїР°РєРѕРІРєР° РІ РїСЂР°РІРёР»Р°С…: {unpack_state}\n"
        f"РџСЂР°РІРёР»: {len(sources)}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data='supplier_stock_mail_toggle')],
        [InlineKeyboardButton("рџ“Ѓ Р’СЂРµРјРµРЅРЅС‹Р№ РєР°С‚Р°Р»РѕРі", callback_data='supplier_stock_mail_temp_dir')],
        [InlineKeyboardButton("рџ—„пёЏ РљР°С‚Р°Р»РѕРі Р°СЂС…РёРІР°", callback_data='supplier_stock_mail_archive_dir')],
        [InlineKeyboardButton("рџ§№ РџРµСЂРёРѕРґ РѕС‡РёСЃС‚РєРё Р°СЂС…РёРІР°", callback_data='supplier_stock_archive_cleanup_mail')],
        [InlineKeyboardButton("рџ“Ћ РџСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№", callback_data='supplier_stock_mail_sources')],
        [InlineKeyboardButton("рџ“¤ Р РµСЃСѓСЂСЃС‹ РІС‹РіСЂСѓР·РєРё", callback_data='supplier_stock_resources')],
        [InlineKeyboardButton("рџ“Ў FTP РћР Рљ", callback_data='supplier_stock_ftp')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_supplier_stock'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_resources_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє СЂРµСЃСѓСЂСЃРѕРІ РІС‹РіСЂСѓР·РєРё РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_resource_settings_id', None)
    context.user_data.pop('supplier_stock_resource_field', None)
    context.user_data.pop('supplier_stock_resource_field_id', None)
    context.user_data.pop('supplier_stock_resource_add', None)
    context.user_data.pop('supplier_stock_resource_stage', None)
    context.user_data.pop('supplier_stock_resource_data', None)

    config = get_supplier_stock_config()
    resources = config.get("resources", [])

    if not resources:
        message = "рџ“¤ *Р РµСЃСѓСЂСЃС‹ РІС‹РіСЂСѓР·РєРё*\n\nвќЊ Р РµСЃСѓСЂСЃС‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        message_lines = ["рџ“¤ *Р РµСЃСѓСЂСЃС‹ РІС‹РіСЂСѓР·РєРё*\n"]
        for index, resource in enumerate(resources, start=1):
            name = _escape_pattern_text(resource.get("name") or resource.get("id") or f"Р РµСЃСѓСЂСЃ {index}")
            unc_path = _escape_pattern_text(resource.get("unc_path") or "РЅРµ Р·Р°РґР°РЅРѕ")
            login = _escape_pattern_text(resource.get("login") or "РЅРµ Р·Р°РґР°РЅРѕ")
            enabled = resource.get("enabled", True)
            status_icon = "рџџў" if enabled else "рџ”ґ"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   вЂў UNC: `{unc_path}`\n"
                    f"   вЂў Р›РѕРіРёРЅ: `{login}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СЂРµСЃСѓСЂСЃ", callback_data='supplier_stock_resource_add')],
    ]

    for resource in resources:
        resource_id = resource.get("id") or ""
        if not resource_id:
            continue
        enabled = resource.get("enabled", True)
        toggle_text = "в›”пёЏ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "вњ… Р’РєР»СЋС‡РёС‚СЊ"
        keyboard.append([
            InlineKeyboardButton(
                f"вљ™пёЏ {resource.get('name', resource_id)}",
                callback_data=f'supplier_stock_resource_settings|{resource_id}'
            ),
            InlineKeyboardButton(
                toggle_text,
                callback_data=f'supplier_stock_resource_toggle_{resource_id}'
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                "рџ—‘пёЏ",
                callback_data=f'supplier_stock_resource_delete_{resource_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_supplier_stock'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_resource_settings(update, context, resource_id: str) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ СЂРµСЃСѓСЂСЃР° РІС‹РіСЂСѓР·РєРё."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_resource_settings_id'] = resource_id
    context.user_data.pop('supplier_stock_resource_field', None)
    context.user_data.pop('supplier_stock_resource_field_id', None)

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        query.edit_message_text(
            "вќЊ Р РµСЃСѓСЂСЃ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_resources')]
            ])
        )
        return

    name = _escape_pattern_text(resource.get("name") or resource_id)
    unc_path = _escape_pattern_text(resource.get("unc_path") or "РЅРµ Р·Р°РґР°РЅРѕ")
    login = _escape_pattern_text(resource.get("login") or "РЅРµ Р·Р°РґР°РЅРѕ")
    password = "Р·Р°РґР°РЅРѕ" if resource.get("password") else "РЅРµ Р·Р°РґР°РЅРѕ"
    status_icon = "рџџў" if resource.get("enabled", True) else "рџ”ґ"

    message = (
        "вљ™пёЏ *Р РµСЃСѓСЂСЃ РІС‹РіСЂСѓР·РєРё*\n\n"
        f"{status_icon} *{name}*\n"
        f"вЂў UNC РїСѓС‚СЊ: `{unc_path}`\n"
        f"вЂў Р›РѕРіРёРЅ: `{login}`\n"
        f"вЂў РџР°СЂРѕР»СЊ: `{password}`\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РЅР°СЃС‚СЂРѕР№РєСѓ:"
    )

    keyboard = [
        [
            InlineKeyboardButton("вњЏпёЏ РќР°Р·РІР°РЅРёРµ", callback_data=f'supplier_stock_resource_field|{resource_id}|name'),
            InlineKeyboardButton("рџ“‚ UNC РїСѓС‚СЊ", callback_data=f'supplier_stock_resource_field|{resource_id}|unc_path'),
        ],
        [
            InlineKeyboardButton("рџ‘¤ Р›РѕРіРёРЅ", callback_data=f'supplier_stock_resource_field|{resource_id}|login'),
            InlineKeyboardButton("рџ”ђ РџР°СЂРѕР»СЊ", callback_data=f'supplier_stock_resource_field|{resource_id}|password'),
        ],
        [InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data=f'supplier_stock_resource_toggle_{resource_id}')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_resources'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_ftp_settings(update, context) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё FTP РћР Рљ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_ftp_field', None)

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})
    host = _escape_pattern_text(ftp_settings.get("host") or "РЅРµ Р·Р°РґР°РЅРѕ")
    login = _escape_pattern_text(ftp_settings.get("login") or "РЅРµ Р·Р°РґР°РЅРѕ")
    password = "Р·Р°РґР°РЅРѕ" if ftp_settings.get("password") else "РЅРµ Р·Р°РґР°РЅРѕ"

    message = (
        "рџ“Ў *FTP РћР Рљ*\n\n"
        f"HOST FTP: `{host}`\n"
        f"Р›РѕРіРёРЅ FTP: `{login}`\n"
        f"РџР°СЂРѕР»СЊ FTP: `{password}`\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ:"
    )

    keyboard = [
        [
            InlineKeyboardButton("рџЊђ HOST FTP", callback_data='supplier_stock_ftp_field|host'),
            InlineKeyboardButton("рџ‘¤ Р›РѕРіРёРЅ FTP", callback_data='supplier_stock_ftp_field|login'),
        ],
        [InlineKeyboardButton("рџ”ђ РџР°СЂРѕР»СЊ FTP", callback_data='supplier_stock_ftp_field|password')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_supplier_stock'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_processing_menu(
    update,
    context,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
    action_prefix: str = "supplier_stock_processing",
    title: str = "рџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ*",
):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РѕР±СЂР°Р±РѕС‚РєРё РїРѕР»СѓС‡РµРЅРЅС‹С… С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_processing_add', None)
    context.user_data.pop('supplier_stock_processing_stage', None)
    context.user_data.pop('supplier_stock_processing_data', None)
    context.user_data.pop('supplier_stock_processing_edit', None)
    context.user_data.pop('supplier_stock_processing_edit_id', None)
    context.user_data.pop('supplier_stock_processing_variant_index', None)
    context.user_data.pop('supplier_stock_processing_data_columns_expected', None)
    context.user_data.pop('supplier_stock_processing_data_columns', None)
    context.user_data.pop('supplier_stock_processing_output_names_expected', None)
    context.user_data.pop('supplier_stock_processing_output_names', None)
    context.user_data.pop('supplier_stock_processing_rule_dirty', None)
    context.user_data['supplier_stock_processing_source_id'] = source_id
    context.user_data['supplier_stock_processing_source_kind'] = source_kind
    context.user_data['supplier_stock_processing_back'] = back_callback
    context.user_data['supplier_stock_processing_action_prefix'] = action_prefix
    context.user_data['supplier_stock_processing_title'] = title

    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    if source_id is not None:
        rules = [
            rule for rule in rules
            if _processing_rule_matches_source(rule, source_id, source_kind, config)
        ]

    if not rules:
        message = f"{title}\n\nвќЊ РџСЂР°РІРёР»Р° РѕР±СЂР°Р±РѕС‚РєРё РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        message_lines = [f"{title}\n"]
        for index, rule in enumerate(rules, start=1):
            name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"РџСЂР°РІРёР»Рѕ {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "РЅРµ Р·Р°РґР°РЅРѕ")
            enabled = rule.get("enabled", True)
            active = rule.get("active", False)
            status_icon = "рџџў" if enabled else "рџ”ґ"
            processing_text = "РѕР±СЂР°Р±РѕС‚РєР°" if rule.get("requires_processing", True) else "Р±РµР· РѕР±СЂР°Р±РѕС‚РєРё"
            active_text = "РґР°" if active else "РЅРµС‚"
            message_lines.append(
                (
                    f"{index}. {status_icon}{'в­ђ' if active else ''} *{name}*\n"
                    f"   вЂў Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР°: `{source_file}`\n"
                    f"   вЂў Р РµР¶РёРј: `{processing_text}`\n"
                    f"   вЂў РђРєС‚РёРІРЅРѕ: `{active_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РїСЂР°РІРёР»Рѕ", callback_data=f'{action_prefix}|add')],
    ]

    for rule in rules:
        rule_id = rule.get("id") or ""
        if not rule_id:
            continue
        enabled = rule.get("enabled", True)
        active = rule.get("active", False)
        toggle_text = "в›”пёЏ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "вњ… Р’РєР»СЋС‡РёС‚СЊ"
        active_text = "в›”пёЏ РћС‚РєР»СЋС‡РёС‚СЊ Р°РєС‚РёРІРЅРѕСЃС‚СЊ" if active else "в­ђ Р’РєР»СЋС‡РёС‚СЊ Р°РєС‚РёРІРЅРѕСЃС‚СЊ"
        keyboard.append([
            InlineKeyboardButton(
                f"вњЏпёЏ {rule.get('name', rule_id)}",
                callback_data=f'{action_prefix}|edit|{rule_id}'
            ),
            InlineKeyboardButton(
                f"{toggle_text}",
                callback_data=f'{action_prefix}|toggle|{rule_id}'
            ),
            InlineKeyboardButton(
                "рџ—‘пёЏ",
                callback_data=f'{action_prefix}|delete|{rule_id}'
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                active_text,
                callback_data=f'{action_prefix}|activate|{rule_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _default_processing_variant() -> dict:
    return {
        "article_col": None,
        "article_filter": None,
        "extra_filter_col": None,
        "extra_filter": None,
        "use_article_filter": None,
        "use_article_filter_columns": [],
        "article_prefix": "",
        "article_postfix": "",
        "article_transform": {
            "pattern": "",
            "replacement": "",
        },
        "data_columns": [],
        "data_columns_count": 0,
        "output_names": [],
        "output_format": None,
        "orc": {
            "enabled": False,
            "prefix": "",
            "stor": "",
            "column": None,
            "input_index": None,
            "output_index": None,
            "output_format": None,
        },
    }

def _ensure_processing_variant(data: dict, index: int) -> dict:
    variants = data.setdefault("variants", [])
    while len(variants) <= index:
        variants.append(_default_processing_variant())
    return variants[index]

def _set_supplier_stock_processing_active_rule(
    rules: list[dict],
    rule_id: str,
    source_id: str | None = None,
    source_kind: str | None = None,
) -> None:
    config = get_supplier_stock_config()
    for rule in rules:
        if source_id is not None and str(rule.get("source_id")) != str(source_id):
            continue
        if source_kind and not _processing_rule_matches_source(rule, source_id, source_kind, config):
            continue
        if str(rule.get("id")) == str(rule_id):
            rule["active"] = not rule.get("active", False)
            if rule["active"]:
                rule["enabled"] = True

def _sync_processing_variants_count(data: dict, count: int) -> None:
    variants = data.setdefault("variants", [])
    if count < len(variants):
        data["variants"] = variants[:count]
    while len(data["variants"]) < count:
        data["variants"].append(_default_processing_variant())

def _sync_variant_columns(variant: dict, count: int) -> None:
    variant["data_columns_count"] = count
    columns = list(variant.get("data_columns", []))
    while len(columns) < count:
        columns.append(None)
    variant["data_columns"] = columns[:count]
    names = list(variant.get("output_names", []))
    while len(names) < count:
        names.append("")
    variant["output_names"] = names[:count]
    filters = list(variant.get("use_article_filter_columns", []))
    while len(filters) < count:
        filters.append(True)
    variant["use_article_filter_columns"] = filters[:count]

def _remove_variant_column(variant: dict, index: int) -> bool:
    columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if index < 0 or index >= columns_count:
        return False
    columns = list(variant.get("data_columns", []))
    names = list(variant.get("output_names", []))
    filters = list(variant.get("use_article_filter_columns", []))
    if index < len(columns):
        columns.pop(index)
    if index < len(names):
        names.pop(index)
    if index < len(filters):
        filters.pop(index)
    variant["data_columns"] = columns
    variant["output_names"] = names
    variant["use_article_filter_columns"] = filters
    _sync_variant_columns(variant, max(columns_count - 1, 0))
    return True

def _fill_processing_rule_from_source(data: dict) -> None:
    source_id = data.get("source_id")
    if not source_id:
        return
    config = get_supplier_stock_config()
    source_kind, source = _resolve_processing_rule_source(data, config)
    source_name = None
    source_output = None
    if source_kind == "download" and source:
        source_name = source.get("name") or source_id
        source_output = source.get("output_name")
    elif source_kind == "mail" and source:
        source_name = source.get("name") or source_id
        source_output = source.get("output_template")
    if source_name:
        data["name"] = source_name
    if source_output:
        data["source_file"] = source_output
    if source_output and not data.get("output_name"):
        data["output_name"] = source_output
    if source_kind and not data.get("source_kind"):
        data["source_kind"] = source_kind

def _find_supplier_source(sources: list[dict], source_id: str) -> dict | None:
    return next((item for item in sources if str(item.get("id")) == str(source_id)), None)

def _resolve_processing_rule_source(data: dict, config: dict) -> tuple[str | None, dict | None]:
    source_id = data.get("source_id")
    if not source_id:
        return None, None
    download_sources = config.get("download", {}).get("sources", [])
    mail_sources = config.get("mail", {}).get("sources", [])
    download_source = _find_supplier_source(download_sources, source_id)
    mail_source = _find_supplier_source(mail_sources, source_id)
    rule_kind = data.get("source_kind")
    if rule_kind == "download" and download_source:
        return "download", download_source
    if rule_kind == "mail" and mail_source:
        return "mail", mail_source
    if download_source and not mail_source:
        return "download", download_source
    if mail_source and not download_source:
        return "mail", mail_source
    if download_source and mail_source:
        source_file = str(data.get("source_file") or "")
        if source_file and source_file == str(download_source.get("output_name") or ""):
            return "download", download_source
        if source_file and source_file == str(mail_source.get("output_template") or ""):
            return "mail", mail_source
        rule_name = str(data.get("name") or "")
        if rule_name and rule_name == str(download_source.get("name") or ""):
            return "download", download_source
        if rule_name and rule_name == str(mail_source.get("name") or ""):
            return "mail", mail_source
    return None, None

def _processing_rule_matches_source(
    rule: dict,
    source_id: str | None,
    source_kind: str | None,
    config: dict,
) -> bool:
    if source_id is not None and str(rule.get("source_id")) != str(source_id):
        return False
    if not source_kind:
        return True
    resolved_kind, _ = _resolve_processing_rule_source(rule, config)
    return resolved_kind == source_kind

def _processing_rule_summary(data: dict) -> str:
    requires_processing = data.get("requires_processing", True)
    processing_text = "РґР°" if requires_processing else "РЅРµС‚"
    name = _escape_pattern_text(data.get("name") or "РЅРµ Р·Р°РґР°РЅРѕ")
    source_file = _escape_pattern_text(data.get("source_file") or "РЅРµ Р·Р°РґР°РЅРѕ")
    output_name = _escape_pattern_text(data.get("output_name") or "РЅРµ Р·Р°РґР°РЅРѕ")
    lines = [
        "рџ§© *РќР°СЃС‚СЂРѕР№РєР° РѕР±СЂР°Р±РѕС‚РєРё*\n",
        f"вЂў РќР°Р·РІР°РЅРёРµ: `{name}`",
        f"вЂў Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР°: `{source_file}`",
        f"вЂў РўСЂРµР±СѓРµС‚СЃСЏ РѕР±СЂР°Р±РѕС‚РєР°: `{processing_text}`",
    ]
    if requires_processing:
        data_row = data.get("data_row")
        lines.append(f"вЂў РџРµСЂРІР°СЏ СЃС‚СЂРѕРєР° СЃ РґР°РЅРЅС‹РјРё: `{data_row or 'РЅРµ Р·Р°РґР°РЅРѕ'}`")
    else:
        lines.append(f"вЂў РРјСЏ С„Р°Р№Р»Р° РЅР° РІС‹С…РѕРґРµ: `{output_name}`")
    return "\n".join(lines)

def show_supplier_stock_processing_rule_menu(update, context) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    _fill_processing_rule_from_source(data)
    context.user_data["supplier_stock_processing_rule_data"] = data
    requires_processing = data.get("requires_processing", True)
    variants = data.get("variants", [])
    variants_count = len(variants)
    if requires_processing and not variants_count:
        _sync_processing_variants_count(data, 1)
        data["variants_count"] = 1
        variants = data.get("variants", [])
        variants_count = len(variants)
    variant_index = 0 if variants_count else None
    message = _processing_rule_summary(data)

    toggle_text = "вњ… РўСЂРµР±СѓРµС‚СЃСЏ РѕР±СЂР°Р±РѕС‚РєР°" if requires_processing else "в›”пёЏ РћР±СЂР°Р±РѕС‚РєР° РЅРµ С‚СЂРµР±СѓРµС‚СЃСЏ"

    keyboard = [[InlineKeyboardButton("вЂ” РќР°СЃС‚СЂРѕР№РєРё РїСЂР°РІРёР»Р° вЂ”", callback_data='supplier_stock_noop')]]
    if not data.get("source_id"):
        keyboard.extend([
            [InlineKeyboardButton("вњЏпёЏ РќР°Р·РІР°РЅРёРµ", callback_data='supplier_stock_processing_rule|field|name')],
            [InlineKeyboardButton("рџ“„ Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР°", callback_data='supplier_stock_processing_rule|field|source_file')],
        ])
    keyboard.append([InlineKeyboardButton(toggle_text, callback_data='supplier_stock_processing_rule|toggle_processing')])

    if requires_processing:
        variant = _ensure_processing_variant(data, variant_index or 0)
        orc = variant.get("orc", {})
        orc_enabled = orc.get("enabled", False)
        orc_text = "РґР°" if orc_enabled else "РЅРµС‚"
        keyboard.extend([
            [InlineKeyboardButton("рџ“Ќ РџРµСЂРІР°СЏ СЃС‚СЂРѕРєР° СЃ РґР°РЅРЅС‹РјРё", callback_data='supplier_stock_processing_rule|field|data_row')],
            [
                InlineKeyboardButton(
                    "рџ”Ћ РќРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ Р°СЂС‚РёРєСѓР»РѕРј",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_col'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџ§Є РЈСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_filter'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџ§Є РЈСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° РїРѕ РµС‰Рµ РѕРґРЅРѕР№ РєРѕР»РѕРЅРєРµ",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|extra_filter'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџЏ·пёЏ РџСЂРµС„РёРєСЃ РІ Р°СЂС‚РёРєСѓР»Рµ",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_prefix'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџЏ·пёЏ РџРѕСЃС‚С„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_postfix'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџ§№ РР·РјРµРЅРµРЅРёРµ РІС…РѕРґСЏС‰РµРіРѕ Р°СЂС‚РёРєСѓР»Р°",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_transform'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџ“Љ РљРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё",
                    callback_data=f'supplier_stock_processing_columns|menu|{variant_index}'
                )
            ],
            [
                InlineKeyboardButton(
                    "рџ§ѕ Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РЅР° РІС‹С…РѕРґРµ",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_format'
                )
            ],
            [
                InlineKeyboardButton(
                    f"рџ“¦ Р¤Р°Р№Р» РґР»СЏ РћР Рљ: {orc_text}",
                    callback_data=f'supplier_stock_processing_variant|toggle_orc|{variant_index}'
                )
            ],
        ])
        if orc_enabled:
            keyboard.append([
                InlineKeyboardButton(
                    "вљ™пёЏ РќР°СЃС‚СЂРѕР№РєРё С„Р°Р№Р»Р° РћР Рљ",
                    callback_data=f'supplier_stock_processing_orc|menu|{variant_index}'
                )
            ])
    else:
        keyboard.append([
            InlineKeyboardButton("рџ“„ РРјСЏ С„Р°Р№Р»Р° РЅР° РІС‹С…РѕРґРµ", callback_data='supplier_stock_processing_rule|field|output_name')
        ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_processing_rule|back'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_processing_variant_menu(update, context, variant_index: int) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    variant = _ensure_processing_variant(data, variant_index)
    context.user_data['supplier_stock_processing_rule_data'] = data

    article_col = variant.get("article_col") or "РЅРµ Р·Р°РґР°РЅРѕ"
    article_filter = _escape_pattern_text(variant.get("article_filter") or "РЅРµ Р·Р°РґР°РЅРѕ")
    extra_filter_col = variant.get("extra_filter_col")
    extra_filter = variant.get("extra_filter")
    if extra_filter_col and extra_filter:
        extra_filter_text = f"в„–{extra_filter_col}: {_escape_pattern_text(extra_filter)}"
    else:
        extra_filter_text = "РЅРµ Р·Р°РґР°РЅРѕ"
    article_prefix = _escape_pattern_text(variant.get("article_prefix") or "РЅРµ Р·Р°РґР°РЅРѕ")
    article_postfix = _escape_pattern_text(variant.get("article_postfix") or "РЅРµ Р·Р°РґР°РЅРѕ")
    article_transform = variant.get("article_transform") or {}
    transform_pattern = article_transform.get("pattern") or ""
    transform_replacement = article_transform.get("replacement") or ""
    if transform_pattern:
        transform_text = f"{_escape_pattern_text(transform_pattern)} => {_escape_pattern_text(transform_replacement)}"
    else:
        transform_text = "РЅРµ Р·Р°РґР°РЅРѕ"
    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    output_format = variant.get("output_format") or "РЅРµ Р·Р°РґР°РЅРѕ"
    orc = variant.get("orc", {})
    orc_enabled = orc.get("enabled", False)
    orc_text = "РґР°" if orc_enabled else "РЅРµС‚"
    orc_column = orc.get("column") or "РЅРµ Р·Р°РґР°РЅРѕ"
    orc_input_index = orc.get("input_index")
    orc_output_index = orc.get("output_index")
    orc_output_format = orc.get("output_format")
    orc_output_name = _escape_pattern_text(orc.get("output_name") or "")
    if orc_output_format:
        orc_output_text = orc_output_format
    elif output_format != "РЅРµ Р·Р°РґР°РЅРѕ":
        orc_output_text = f"РєР°Рє РѕСЃРЅРѕРІРЅРѕР№ ({output_format})"
    else:
        orc_output_text = "РЅРµ Р·Р°РґР°РЅРѕ"

    message = (
        "рџ“¦ *РќР°СЃС‚СЂРѕР№РєР° С„Р°Р№Р»Р° РѕР±СЂР°Р±РѕС‚РєРё*\n\n"
        f"вЂў РќРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ Р°СЂС‚РёРєСѓР»РѕРј: `{article_col}`\n"
        f"вЂў РЈСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ: `{article_filter}`\n"
        f"вЂў РЈСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° РїРѕ РґРѕРї. РєРѕР»РѕРЅРєРµ: `{extra_filter_text}`\n"
        f"вЂў РџСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°: `{article_prefix}`\n"
        f"вЂў РџРѕСЃС‚С„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°: `{article_postfix}`\n"
        f"вЂў РР·РјРµРЅРµРЅРёРµ РІС…РѕРґСЏС‰РµРіРѕ Р°СЂС‚РёРєСѓР»Р°: `{transform_text}`\n"
        f"вЂў РљРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё: `{data_columns_count or 'РЅРµ Р·Р°РґР°РЅРѕ'}`\n"
        f"вЂў Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РЅР° РІС‹С…РѕРґРµ: `{output_format}`\n"
        f"вЂў Р¤Р°Р№Р» РґР»СЏ РћР Рљ: `{orc_text}`"
    )
    if orc_enabled:
        message += (
            f"\nвЂў РљРѕР»РѕРЅРєР° РґР°РЅРЅС‹С… РґР»СЏ РћР Рљ: `{orc_column}`"
            f"\nвЂў Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РћР Рљ РЅР° РІС‹С…РѕРґРµ: `{_escape_pattern_text(orc_output_text)}`"
            f"\nвЂў РРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РћР Рљ: `{orc_output_name or 'РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ (_orc)'}`"
        )
        if orc_input_index:
            message += f"\nвЂў Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РІС…РѕРґ): `в„–{orc_input_index}`"
        if orc_output_index:
            output_label = f"в„–{orc_output_index}"
            if data_columns_count and orc_output_index <= data_columns_count:
                names = variant.get("output_names", [])
                name_value = names[orc_output_index - 1] if orc_output_index - 1 < len(names) else ""
                if name_value:
                    output_label = f"{orc_output_index}. {_escape_pattern_text(name_value)}"
            message += f"\nвЂў Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РІС‹С…РѕРґ): `{output_label}`"

    keyboard = [
        [InlineKeyboardButton("вЂ” РќР°СЃС‚СЂРѕР№РєРё С„Р°Р№Р»Р° вЂ”", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("рџ”Ћ РќРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ Р°СЂС‚РёРєСѓР»РѕРј", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_col')],
        [InlineKeyboardButton("рџ§Є РЈСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_filter')],
        [
            InlineKeyboardButton(
                "рџ§Є РЈСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° РїРѕ РµС‰Рµ РѕРґРЅРѕР№ РєРѕР»РѕРЅРєРµ",
                callback_data=f'supplier_stock_processing_variant|field|{variant_index}|extra_filter'
            )
        ],
        [InlineKeyboardButton("рџЏ·пёЏ РџСЂРµС„РёРєСЃ РІ Р°СЂС‚РёРєСѓР»Рµ", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_prefix')],
        [InlineKeyboardButton("рџЏ·пёЏ РџРѕСЃС‚С„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_postfix')],
        [InlineKeyboardButton("рџ§№ РР·РјРµРЅРµРЅРёРµ РІС…РѕРґСЏС‰РµРіРѕ Р°СЂС‚РёРєСѓР»Р°", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_transform')],
    ]

    keyboard.append([InlineKeyboardButton("вЂ” РљРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё вЂ”", callback_data='supplier_stock_noop')])
    keyboard.append([
        InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєРѕР»РѕРЅРєСѓ", callback_data=f'supplier_stock_processing_variant|add_column|{variant_index}')
    ])

    if data_columns_count:
        for idx in range(data_columns_count):
            label = variant.get("data_columns", [])
            value = label[idx] if idx < len(label) else "РЅРµ Р·Р°РґР°РЅРѕ"
            keyboard.append([
                InlineKeyboardButton(
                    f"рџ“€ РљРѕР»РѕРЅРєР° {idx + 1}: {value or 'РЅРµ Р·Р°РґР°РЅРѕ'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|data_column|{idx}'
                )
            ])
        keyboard.append([InlineKeyboardButton("вЂ” РРјРµРЅР° С„Р°Р№Р»РѕРІ вЂ”", callback_data='supplier_stock_noop')])
        for idx in range(data_columns_count):
            names = variant.get("output_names", [])
            name_value = names[idx] if idx < len(names) else "РЅРµ Р·Р°РґР°РЅРѕ"
            keyboard.append([
                InlineKeyboardButton(
                    f"рџ“„ РРјСЏ С„Р°Р№Р»Р° {idx + 1}: {name_value or 'РЅРµ Р·Р°РґР°РЅРѕ'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_name|{idx}'
                )
            ])

    keyboard.extend([
        [InlineKeyboardButton("рџ§ѕ Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РЅР° РІС‹С…РѕРґРµ", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_format')],
        [InlineKeyboardButton(f"рџ“¦ Р¤Р°Р№Р» РґР»СЏ РћР Рљ: {orc_text}", callback_data=f'supplier_stock_processing_variant|toggle_orc|{variant_index}')],
    ])

    if orc_enabled:
        keyboard.extend([
            [InlineKeyboardButton("вЂ” Р¤Р°Р№Р» РґР»СЏ РћР Рљ вЂ”", callback_data='supplier_stock_noop')],
            [InlineKeyboardButton("рџЏ·пёЏ РџСЂРµС„РёРєСЃ РІ Р°СЂС‚РёРєСѓР»Рµ", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_prefix')],
            [InlineKeyboardButton("рџ“¦ Stor", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_stor')],
            [InlineKeyboardButton("рџ“€ РљРѕР»РѕРЅРєР° СЃ РґР°РЅРЅС‹РјРё", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_column')],
            [
                InlineKeyboardButton(
                    "рџ§ѕ Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РћР Рљ РЅР° РІС‹С…РѕРґРµ",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_output_format'
                )
            ],
        ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_processing_rule|menu'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_processing_columns_menu(update, context, variant_index: int) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    variant = _ensure_processing_variant(data, variant_index)
    context.user_data['supplier_stock_processing_rule_data'] = data

    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    columns = variant.get("data_columns", [])
    names = variant.get("output_names", [])
    column_filters = variant.get("use_article_filter_columns", [])

    use_article_filter = variant.get("use_article_filter")
    if use_article_filter is None:
        use_article_filter = bool(variant.get("article_filter"))
    filter_text = "РґР°" if use_article_filter else "РЅРµС‚"
    message_lines = [
        "рџ“Љ *РљРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё*\n",
        f"РљРѕР»РёС‡РµСЃС‚РІРѕ РєРѕР»РѕРЅРѕРє: `{data_columns_count or 0}`",
        f"РСЃРїРѕР»СЊР·РѕРІР°С‚СЊ СѓСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ: `{filter_text}`",
    ]
    for idx in range(data_columns_count or 0):
        col_value = columns[idx] if idx < len(columns) else "РЅРµ Р·Р°РґР°РЅРѕ"
        name_value = names[idx] if idx < len(names) else "РЅРµ Р·Р°РґР°РЅРѕ"
        filter_enabled = column_filters[idx] if idx < len(column_filters) else True
        filter_text_line = "РґР°" if filter_enabled else "РЅРµС‚"
        message_lines.append(
            f"{idx + 1}. РљРѕР»РѕРЅРєР°: `{col_value or 'РЅРµ Р·Р°РґР°РЅРѕ'}` в†’ С„Р°Р№Р»: `{_escape_pattern_text(name_value)}`"
            f" (С„РёР»СЊС‚СЂ: `{filter_text_line}`)"
        )
    message = "\n".join(message_lines)

    toggle_text = (
        "вњ… РСЃРїРѕР»СЊР·РѕРІР°С‚СЊ СѓСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ"
        if use_article_filter
        else "в›”пёЏ РќРµ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ СѓСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ"
    )
    keyboard = [
        [InlineKeyboardButton("вЂ” РљРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё вЂ”", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton(toggle_text, callback_data=f'supplier_stock_processing_columns|toggle_article_filter|{variant_index}')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєРѕР»РѕРЅРєСѓ", callback_data=f'supplier_stock_processing_columns|add_column|{variant_index}')],
    ]

    if data_columns_count:
        for idx in range(data_columns_count):
            value = columns[idx] if idx < len(columns) else "РЅРµ Р·Р°РґР°РЅРѕ"
            keyboard.append([
                InlineKeyboardButton(
                    f"рџ“€ РљРѕР»РѕРЅРєР° {idx + 1}: {value or 'РЅРµ Р·Р°РґР°РЅРѕ'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|data_column|{idx}'
                ),
                InlineKeyboardButton(
                    "рџ—‘пёЏ",
                    callback_data=f'supplier_stock_processing_columns|remove_column|{variant_index}|{idx}'
                ),
            ])
            filter_enabled = column_filters[idx] if idx < len(column_filters) else True
            filter_toggle_text = (
                f"вњ… Р¤РёР»СЊС‚СЂ Р°СЂС‚РёРєСѓР»РѕРІ {idx + 1}"
                if filter_enabled
                else f"в›”пёЏ Р¤РёР»СЊС‚СЂ Р°СЂС‚РёРєСѓР»РѕРІ {idx + 1}"
            )
            keyboard.append([
                InlineKeyboardButton(
                    filter_toggle_text,
                    callback_data=f'supplier_stock_processing_columns|tac|{variant_index}|{idx}'
                )
            ])
        keyboard.append([InlineKeyboardButton("вЂ” РРјРµРЅР° С„Р°Р№Р»РѕРІ вЂ”", callback_data='supplier_stock_noop')])
        for idx in range(data_columns_count):
            name_value = names[idx] if idx < len(names) else "РЅРµ Р·Р°РґР°РЅРѕ"
            keyboard.append([
                InlineKeyboardButton(
                    f"рџ“„ РРјСЏ С„Р°Р№Р»Р° {idx + 1}: {name_value or 'РЅРµ Р·Р°РґР°РЅРѕ'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_name|{idx}'
                )
            ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_processing_rule|menu'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_processing_orc_menu(update, context, variant_index: int) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    variant = _ensure_processing_variant(data, variant_index)
    context.user_data['supplier_stock_processing_rule_data'] = data

    orc = variant.get("orc", {})
    orc_prefix = _escape_pattern_text(orc.get("prefix") or "РЅРµ Р·Р°РґР°РЅРѕ")
    orc_stor = _escape_pattern_text(orc.get("stor") or "РЅРµ Р·Р°РґР°РЅРѕ")
    orc_column = orc.get("column") or "РЅРµ Р·Р°РґР°РЅРѕ"
    orc_input_index = orc.get("input_index")
    orc_output_index = orc.get("output_index")
    base_output_format = variant.get("output_format")
    orc_output_format = orc.get("output_format")
    orc_output_name = _escape_pattern_text(orc.get("output_name") or "")
    if orc_output_format:
        orc_output_text = orc_output_format
    elif base_output_format:
        orc_output_text = f"РєР°Рє РѕСЃРЅРѕРІРЅРѕР№ ({base_output_format})"
    else:
        orc_output_text = "РЅРµ Р·Р°РґР°РЅРѕ"

    config = get_supplier_stock_config()
    source_kind, source = _resolve_processing_rule_source(data, config)
    input_count = 0
    if source_kind == "mail" and source:
        input_count = int(source.get("expected_attachments") or 1)

    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    output_names = variant.get("output_names", [])

    message_lines = [
        "рџ“¦ *Р¤Р°Р№Р» РґР»СЏ РћР Рљ*\n",
        f"вЂў РџСЂРµС„РёРєСЃ РІ Р°СЂС‚РёРєСѓР»Рµ: `{orc_prefix}`",
        f"вЂў Stor: `{orc_stor}`",
        f"вЂў РљРѕР»РѕРЅРєР° СЃ РґР°РЅРЅС‹РјРё: `{orc_column}`",
        f"вЂў Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РћР Рљ РЅР° РІС‹С…РѕРґРµ: `{_escape_pattern_text(orc_output_text)}`",
        f"вЂў РРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РћР Рљ: `{orc_output_name or 'РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ (_orc)'}`",
    ]
    if input_count > 1:
        input_label = f"в„–{orc_input_index}" if orc_input_index else "РЅРµ Р·Р°РґР°РЅРѕ"
        message_lines.append(f"вЂў Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РІС…РѕРґ): `{input_label}`")
    if data_columns_count > 1:
        output_label = "РЅРµ Р·Р°РґР°РЅРѕ"
        if orc_output_index:
            output_label = f"в„–{orc_output_index}"
            if orc_output_index <= data_columns_count:
                name_value = output_names[orc_output_index - 1] if orc_output_index - 1 < len(output_names) else ""
                if name_value:
                    output_label = f"{orc_output_index}. {_escape_pattern_text(name_value)}"
        message_lines.append(f"вЂў Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РІС‹С…РѕРґ): `{output_label}`")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вЂ” Р¤Р°Р№Р» РґР»СЏ РћР Рљ вЂ”", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("рџЏ·пёЏ РџСЂРµС„РёРєСЃ РІ Р°СЂС‚РёРєСѓР»Рµ", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_prefix')],
        [InlineKeyboardButton("рџ“¦ Stor", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_stor')],
        [InlineKeyboardButton("рџ“€ РљРѕР»РѕРЅРєР° СЃ РґР°РЅРЅС‹РјРё", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_column')],
        [
            InlineKeyboardButton(
                "рџ“„ РРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РћР Рљ",
                callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_output_name'
            )
        ],
        [
            InlineKeyboardButton(
                "рџ§ѕ Р¤РѕСЂРјР°С‚ С„Р°Р№Р»Р° РћР Рљ РЅР° РІС‹С…РѕРґРµ",
                callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_output_format'
            )
        ],
    ]

    if input_count > 1:
        keyboard.append([InlineKeyboardButton("вЂ” Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РІС…РѕРґ) вЂ”", callback_data='supplier_stock_noop')])
        for idx in range(1, input_count + 1):
            selected = "вњ…" if orc_input_index == idx else "рџ“Ґ"
            keyboard.append([
                InlineKeyboardButton(
                    f"{selected} Р’С…РѕРґ {idx}",
                    callback_data=f'supplier_stock_processing_orc|set_input|{variant_index}|{idx}'
                )
            ])
        if orc_input_index:
            keyboard.append([
                InlineKeyboardButton(
                    "рџљ« РЎР±СЂРѕСЃРёС‚СЊ РІС‹Р±РѕСЂ РІС…РѕРґР°",
                    callback_data=f'supplier_stock_processing_orc|clear_input|{variant_index}'
                )
            ])

    if data_columns_count > 1:
        keyboard.append([InlineKeyboardButton("вЂ” Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РІС‹С…РѕРґ) вЂ”", callback_data='supplier_stock_noop')])
        for idx in range(1, data_columns_count + 1):
            name_value = output_names[idx - 1] if idx - 1 < len(output_names) else ""
            label = f"Р’С‹С…РѕРґ {idx}"
            if name_value:
                label = f"{idx}. {name_value}"
            selected = "вњ…" if orc_output_index == idx else "рџ“¤"
            keyboard.append([
                InlineKeyboardButton(
                    f"{selected} {label}",
                    callback_data=f'supplier_stock_processing_orc|set_output|{variant_index}|{idx}'
                )
            ])
        if orc_output_index:
            keyboard.append([
                InlineKeyboardButton(
                    "рџљ« РЎР±СЂРѕСЃРёС‚СЊ РІС‹Р±РѕСЂ РІС‹С…РѕРґР°",
                    callback_data=f'supplier_stock_processing_orc|clear_output|{variant_index}'
                )
            ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_processing_rule|menu'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def supplier_stock_start_processing_rule_menu(
    update,
    context,
    rule_id: str | None = None,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_processing_stage', None)
    context.user_data.pop('supplier_stock_processing_data', None)
    context.user_data.pop('supplier_stock_processing_add', None)
    context.user_data.pop('supplier_stock_processing_edit', None)

    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    rule = None
    if rule_id:
        rule = next((item for item in rules if str(item.get("id")) == rule_id), None)
        if not rule:
            query.edit_message_text(
                "вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
                ])
            )
            return
        context.user_data['supplier_stock_processing_rule_edit_id'] = rule_id
        context.user_data['supplier_stock_processing_rule_add'] = False
        data = dict(rule)
    else:
        context.user_data['supplier_stock_processing_rule_edit_id'] = None
        context.user_data['supplier_stock_processing_rule_add'] = True
        data = {
            "name": "",
            "source_file": "",
            "output_name": "",
            "enabled": True,
            "requires_processing": True,
            "variants_count": 0,
            "variants": [],
        }
    if source_id:
        data['source_id'] = source_id
        context.user_data['supplier_stock_processing_source_id'] = source_id
    if source_kind:
        data['source_kind'] = source_kind
        context.user_data['supplier_stock_processing_source_kind'] = source_kind
    _fill_processing_rule_from_source(data)
    context.user_data['supplier_stock_processing_rule_data'] = data
    context.user_data['supplier_stock_processing_back'] = back_callback
    context.user_data['supplier_stock_processing_rule_dirty'] = False
    show_supplier_stock_processing_rule_menu(update, context)

def supplier_stock_start_processing_field_edit(
    update,
    context,
    field: str,
    variant_index: int | None = None,
    item_index: int | None = None,
) -> None:
    query = update.callback_query
    query.answer()

    rule_data = context.user_data.get("supplier_stock_processing_rule_data", {})
    if rule_data.get("source_id") and field in ("name", "source_file"):
        query.edit_message_text(
            "в„№пёЏ РќР°Р·РІР°РЅРёРµ Рё С„Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° Р±РµСЂСѓС‚СЃСЏ РёР· РЅР°СЃС‚СЂРѕРµРє РёСЃС‚РѕС‡РЅРёРєР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_processing_rule|menu')]
            ])
        )
        return

    context.user_data['supplier_stock_processing_field'] = field
    context.user_data['supplier_stock_processing_variant_index'] = variant_index
    context.user_data['supplier_stock_processing_item_index'] = item_index

    prompts = {
        "name": "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РїСЂР°РІРёР»Р°:",
        "source_file": "Р’РІРµРґРёС‚Рµ РёРјСЏ С„Р°Р№Р»Р° РёСЃС‚РѕС‡РЅРёРєР°:",
        "data_row": "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РїРµСЂРІРѕР№ СЃС‚СЂРѕРєРё СЃ РґР°РЅРЅС‹РјРё:",
        "output_name": "Р’РІРµРґРёС‚Рµ РёРјСЏ С„Р°Р№Р»Р° РЅР° РІС‹С…РѕРґРµ (РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ {index}, {name}, {filename}):",
        "article_col": "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ Р°СЂС‚РёРєСѓР»РѕРј:",
        "article_filter": (
            "Р’РІРµРґРёС‚Рµ СѓСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ (regex) РёР»Рё '-' РґР»СЏ РІСЃРµС….\n\n"
            "РџСЂРёРјРµСЂС‹:\n"
            "вЂў $1 ~ /^[0-9]/ && $col+0 > 0\n"
            "вЂў $1 ~ /^[A-Z].*/ && $4 ~ /^[0-9]+$/\n"
            "вЂў grep -E '^DKS [0-9A-Z]{6,},'\n"
            "вЂў gsub(/^\\./, \"\", art); gsub(/[A-Za-z]+$/, \"\", art);\n"
            "вЂў ($3+0 > 0) && ($4 == \"РњРѕСЃРєРІР°\")"
        ),
        "extra_filter": (
            "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё Рё СѓСЃР»РѕРІРёРµ РѕС‚Р±РѕСЂР° (regex) С‡РµСЂРµР· ';'.\n"
            "РџСЂРёРјРµСЂ: 4;^РњРѕСЃРєРІР°$\n"
            "РР»Рё '-' С‡С‚РѕР±С‹ РѕС‚РєР»СЋС‡РёС‚СЊ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№ С„РёР»СЊС‚СЂ."
        ),
        "article_prefix": (
            "Р’РІРµРґРёС‚Рµ РїСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° (РёР»Рё '-' РµСЃР»Рё РЅРµ РЅСѓР¶РµРЅ). "
            "Р•СЃР»Рё РЅСѓР¶РµРЅ РїСЂРѕР±РµР» РІ РєРѕРЅС†Рµ, РјРѕР¶РЅРѕ СѓРєР°Р·Р°С‚СЊ \\s:"
        ),
        "article_postfix": "Р’РІРµРґРёС‚Рµ РїРѕСЃС‚С„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° (РёР»Рё '-' РµСЃР»Рё РЅРµ РЅСѓР¶РµРЅ). РџСЂРѕР±РµР»С‹ РІ РєРѕРЅС†Рµ СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ:",
        "article_transform": (
            "Р’РІРµРґРёС‚Рµ РїСЂР°РІРёР»Рѕ РёР·РјРµРЅРµРЅРёСЏ Р°СЂС‚РёРєСѓР»Р° (regex) РёР»Рё '-' С‡С‚РѕР±С‹ РѕС‚РєР»СЋС‡РёС‚СЊ.\n\n"
            "Р¤РѕСЂРјР°С‚: РїР°С‚С‚РµСЂРЅ => Р·Р°РјРµРЅР° (Р·Р°РјРµРЅР° РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚РѕР№).\n"
            "РџСЂРёРјРµСЂС‹:\n"
            "вЂў ^0+ =>\n"
            "вЂў [^0-9A-Za-z]+ =>\n"
            "вЂў \\s+ => -"
        ),
        "data_column": "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё:",
        "output_format": "Р’РІРµРґРёС‚Рµ С„РѕСЂРјР°С‚ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° (xls, xlsx, csv):",
        "orc_prefix": "Р’РІРµРґРёС‚Рµ РїСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° РґР»СЏ С„Р°Р№Р»Р° РћР Рљ (РёР»Рё '-' РµСЃР»Рё РЅРµ РЅСѓР¶РµРЅ):",
        "orc_stor": "Р’РІРµРґРёС‚Рµ РїР°СЂР°РјРµС‚СЂ Stor РґР»СЏ С„Р°Р№Р»Р° РћР Рљ:",
        "orc_column": "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё РґР»СЏ С„Р°Р№Р»Р° РћР Рљ:",
        "orc_output_name": (
            "Р’РІРµРґРёС‚Рµ РёРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РћР Рљ "
            "(РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ {index}, {name}, {filename}) "
            "РёР»Рё '-' С‡С‚РѕР±С‹ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РґРѕР±Р°РІР»РµРЅРёРµ _orc:"
        ),
        "orc_output_format": (
            "Р’РІРµРґРёС‚Рµ С„РѕСЂРјР°С‚ С„Р°Р№Р»Р° РћР Рљ РЅР° РІС‹С…РѕРґРµ (xls, xlsx, csv) "
            "РёР»Рё '-' С‡С‚РѕР±С‹ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ С„РѕСЂРјР°С‚ РѕСЃРЅРѕРІРЅРѕРіРѕ С„Р°Р№Р»Р°:"
        ),
    }
    prompt = prompts.get(field, "Р’РІРµРґРёС‚Рµ Р·РЅР°С‡РµРЅРёРµ:")
    if field == "output_name" and variant_index is not None:
        prompt = "Р’РІРµРґРёС‚Рµ РёРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° (РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ {index}, {name}, {filename}):"

    current_value = None
    if variant_index is not None:
        variant = _ensure_processing_variant(rule_data, variant_index)
        if field == "article_col":
            current_value = variant.get("article_col")
        elif field == "article_filter":
            current_value = variant.get("article_filter")
        elif field == "extra_filter":
            extra_filter_col = variant.get("extra_filter_col")
            extra_filter = variant.get("extra_filter")
            if extra_filter_col and extra_filter:
                current_value = f"{extra_filter_col}; {extra_filter}"
            else:
                current_value = None
        elif field == "article_prefix":
            current_value = variant.get("article_prefix")
        elif field == "article_postfix":
            current_value = variant.get("article_postfix")
        elif field == "article_transform":
            article_transform = variant.get("article_transform") or {}
            pattern = article_transform.get("pattern") or ""
            replacement = article_transform.get("replacement") or ""
            if pattern:
                current_value = f"{pattern} => {replacement}"
            else:
                current_value = None
        elif field == "data_column":
            columns = variant.get("data_columns", [])
            if item_index is not None and item_index < len(columns):
                current_value = columns[item_index]
        elif field == "output_name":
            names = variant.get("output_names", [])
            if item_index is not None and item_index < len(names):
                current_value = names[item_index]
        elif field == "output_format":
            current_value = variant.get("output_format")
        elif field in ("orc_prefix", "orc_stor", "orc_column", "orc_output_name", "orc_output_format"):
            orc = variant.get("orc", {})
            if field == "orc_prefix":
                current_value = orc.get("prefix")
            elif field == "orc_stor":
                current_value = orc.get("stor")
            elif field == "orc_column":
                current_value = orc.get("column")
            elif field == "orc_output_name":
                current_value = orc.get("output_name")
            elif field == "orc_output_format":
                if orc.get("output_format"):
                    current_value = orc.get("output_format")
                elif variant.get("output_format"):
                    current_value = f"РєР°Рє РѕСЃРЅРѕРІРЅРѕР№ ({variant.get('output_format')})"
    else:
        if field == "name":
            current_value = rule_data.get("name")
        elif field == "source_file":
            current_value = rule_data.get("source_file")
        elif field == "data_row":
            current_value = rule_data.get("data_row")
        elif field == "output_name":
            current_value = rule_data.get("output_name")

    current_hint = _format_current_hint(current_value)
    back_callback = 'supplier_stock_processing_rule|menu'
    if variant_index is not None:
        back_callback = f'supplier_stock_processing_variant|menu|{variant_index}'
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nРўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_hint}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
        ])
    )

def _validate_processing_rule(data: dict) -> list[str]:
    missing = []
    if data.get("requires_processing", True):
        variants = data.get("variants", [])
        variants_count = len(variants)
        if not variants_count:
            missing.append("С„Р°Р№Р»С‹ РѕР±СЂР°Р±РѕС‚РєРё")
        if not data.get("data_row"):
            missing.append("РїРµСЂРІР°СЏ СЃС‚СЂРѕРєР° СЃ РґР°РЅРЅС‹РјРё")
        for idx in range(variants_count):
            variant = _ensure_processing_variant(data, idx)
            if not variant.get("article_col"):
                missing.append(f"РєРѕР»РѕРЅРєР° Р°СЂС‚РёРєСѓР»Р° (С„Р°Р№Р» {idx + 1})")
            columns_count = variant.get("data_columns_count") or max(
                len(variant.get("data_columns", [])),
                len(variant.get("output_names", [])),
            )
            if not columns_count:
                missing.append(f"РєРѕР»-РІРѕ РєРѕР»РѕРЅРѕРє (С„Р°Р№Р» {idx + 1})")
            columns = variant.get("data_columns", [])
            if any(col is None for col in columns) or len(columns) < columns_count:
                missing.append(f"РєРѕР»РѕРЅРєРё РґР°РЅРЅС‹С… (С„Р°Р№Р» {idx + 1})")
            names = variant.get("output_names", [])
            if len(names) < columns_count or any(not name for name in names):
                missing.append(f"РёРјРµРЅР° С„Р°Р№Р»РѕРІ (С„Р°Р№Р» {idx + 1})")
            if not variant.get("output_format"):
                missing.append(f"С„РѕСЂРјР°С‚ С„Р°Р№Р»Р° (С„Р°Р№Р» {idx + 1})")
            orc = variant.get("orc", {})
            if orc.get("enabled"):
                if not orc.get("stor"):
                    missing.append(f"Stor РћР Рљ (С„Р°Р№Р» {idx + 1})")
    return missing

def _save_processing_rule_data(update, context) -> bool:
    query = update.callback_query
    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    source_id = context.user_data.get("supplier_stock_processing_source_id")
    if source_id:
        data["source_id"] = source_id
    _fill_processing_rule_from_source(data)
    context.user_data["supplier_stock_processing_rule_data"] = data
    missing = _validate_processing_rule(data)
    if missing:
        query.answer("Р—Р°РїРѕР»РЅРёС‚Рµ: " + ", ".join(missing), show_alert=True)
        return False
    edit_id = context.user_data.get('supplier_stock_processing_rule_edit_id') or data.get("id")
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
    return True

def _persist_processing_rule_data(context) -> None:
    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    source_id = context.user_data.get("supplier_stock_processing_source_id")
    if source_id:
        data["source_id"] = source_id
    _fill_processing_rule_from_source(data)
    edit_id = context.user_data.get('supplier_stock_processing_rule_edit_id') or data.get("id")
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id, keep_context=True)
    if not edit_id:
        context.user_data['supplier_stock_processing_rule_edit_id'] = data.get('id')
        context.user_data['supplier_stock_processing_rule_add'] = False
    elif data.get("id"):
        context.user_data['supplier_stock_processing_rule_edit_id'] = data.get("id")
    context.user_data['supplier_stock_processing_rule_data'] = data

def _show_processing_rule_back_menu(update, context, back_callback: str) -> None:
    if back_callback == 'settings_ext_supplier_stock':
        show_supplier_stock_settings(update, context)
        return
    if back_callback == 'supplier_stock_processing':
        show_supplier_stock_processing_menu(update, context, action_prefix="supplier_stock_processing")
        return
    if back_callback.startswith('supplier_stock_source_settings|'):
        source_id = back_callback.split('|', 1)[1]
        show_supplier_stock_source_settings(update, context, source_id)
        return
    if back_callback.startswith('supplier_stock_mail_source_settings|'):
        source_id = back_callback.split('|', 1)[1]
        show_supplier_stock_mail_source_settings(update, context, source_id)
        return

    update.callback_query.edit_message_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєРё СЃРѕС…СЂР°РЅРµРЅС‹.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
        ])
    )

def supplier_stock_save_processing_rule(update, context) -> None:
    query = update.callback_query
    query.answer()

    if not _save_processing_rule_data(update, context):
        return
    context.user_data['supplier_stock_processing_rule_dirty'] = False
    back_callback = context.user_data.get('supplier_stock_processing_back', 'supplier_stock_processing')
    query.edit_message_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєРё СЃРѕС…СЂР°РЅРµРЅС‹.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
        ])
    )

def show_supplier_stock_mail_sources_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє РїСЂР°РІРёР» РІР»РѕР¶РµРЅРёР№ РґР»СЏ РїРѕС‡С‚С‹."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_mail_source_settings_id', None)
    context.user_data.pop('supplier_stock_mail_add_source', None)
    context.user_data.pop('supplier_stock_mail_source_stage', None)
    context.user_data.pop('supplier_stock_mail_source_data', None)
    context.user_data.pop('supplier_stock_mail_edit_source', None)
    context.user_data.pop('supplier_stock_mail_edit_source_stage', None)
    context.user_data.pop('supplier_stock_mail_edit_source_id', None)

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])

    if not sources:
        message = "рџ“Ћ *РџСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№*\n\nвќЊ РџСЂР°РІРёР»Р° РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        message_lines = ["рџ“Ћ *РџСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№*\n"]
        for index, source in enumerate(sources, start=1):
            name = _escape_pattern_text(source.get("name") or source.get("id") or f"РџСЂР°РІРёР»Рѕ {index}")
            sender = _escape_pattern_text(source.get("sender_pattern") or "Р»СЋР±РѕР№")
            subject = _escape_pattern_text(source.get("subject_pattern") or "Р»СЋР±РѕР№")
            mime_pattern = _escape_pattern_text(source.get("mime_pattern") or "application/.*")
            filename_pattern = _escape_pattern_text(source.get("filename_pattern") or "Р»СЋР±РѕР№")
            expected = source.get("expected_attachments", 1)
            output_template = _escape_pattern_text(source.get("output_template") or "РЅРµ Р·Р°РґР°РЅРѕ")
            enabled = source.get("enabled", True)
            unpack_enabled = source.get("unpack_archive", False)
            status_icon = "рџџў" if enabled else "рџ”ґ"
            unpack_text = "РґР°" if unpack_enabled else "РЅРµС‚"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   вЂў РћС‚РїСЂР°РІРёС‚РµР»СЊ: `{sender}`\n"
                    f"   вЂў РўРµРјР°: `{subject}`\n"
                    f"   вЂў MIME: `{mime_pattern}`\n"
                    f"   вЂў РРјСЏ С„Р°Р№Р»Р°: `{filename_pattern}`\n"
                    f"   вЂў РћР¶РёРґР°РµС‚СЃСЏ: `{expected}`\n"
                    f"   вЂў РЁР°Р±Р»РѕРЅ: `{output_template}`\n"
                    f"   вЂў Р Р°СЃРїР°РєРѕРІРєР°: `{unpack_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РїСЂР°РІРёР»Рѕ", callback_data='supplier_stock_mail_source_add')],
    ]

    for source in sources:
        source_id = source.get("id") or ""
        if not source_id:
            continue
        enabled = source.get("enabled", True)
        unpack_enabled = source.get("unpack_archive", False)
        toggle_text = "в›”пёЏ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "вњ… Р’РєР»СЋС‡РёС‚СЊ"
        unpack_text = "рџ“¦ Р Р°СЃРїР°РєРѕРІРєР°: РІРєР»" if unpack_enabled else "рџ“¦ Р Р°СЃРїР°РєРѕРІРєР°: РІС‹РєР»"
        keyboard.append([
            InlineKeyboardButton(
                f"вљ™пёЏ {source.get('name', source_id)}",
                callback_data=f'supplier_stock_mail_source_settings|{source_id}'
            ),
            InlineKeyboardButton(
                f"{toggle_text}",
                callback_data=f'supplier_stock_mail_source_toggle_{source_id}'
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                unpack_text,
                callback_data=f'supplier_stock_mail_source_unpack_toggle_{source_id}'
            ),
            InlineKeyboardButton(
                "рџ—‘пёЏ",
                callback_data=f'supplier_stock_mail_source_delete_{source_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_schedule_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РјРµРЅСЋ СЂР°СЃРїРёСЃР°РЅРёСЏ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)

    config = get_supplier_stock_config()
    schedule = config.get("download", {}).get("schedule", {})
    schedule_state = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if schedule.get("enabled") else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    schedule_time = schedule.get("time", "РЅРµ Р·Р°РґР°РЅРѕ")

    message = (
        "вЏ° *Р Р°СЃРїРёСЃР°РЅРёРµ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ*\n\n"
        f"РЎС‚Р°С‚СѓСЃ: {schedule_state}\n"
        f"Р’СЂРµРјСЏ: {schedule_time}\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data='supplier_stock_schedule_toggle')],
        [InlineKeyboardButton("рџ•’ РР·РјРµРЅРёС‚СЊ РІСЂРµРјСЏ", callback_data='supplier_stock_schedule_time')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_download'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_sources_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє РёСЃС‚РѕС‡РЅРёРєРѕРІ С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_source_settings_id', None)
    context.user_data.pop('supplier_stock_add_source', None)
    context.user_data.pop('supplier_stock_source_stage', None)
    context.user_data.pop('supplier_stock_source_data', None)
    context.user_data.pop('supplier_stock_edit_source', None)
    context.user_data.pop('supplier_stock_edit_source_stage', None)
    context.user_data.pop('supplier_stock_edit_source_id', None)

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])

    if not sources:
        message = "рџ“¦ *РСЃС‚РѕС‡РЅРёРєРё С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ*\n\nвќЊ РСЃС‚РѕС‡РЅРёРєРё РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        message_lines = ["рџ“¦ *РСЃС‚РѕС‡РЅРёРєРё С„Р°Р№Р»РѕРІ РѕСЃС‚Р°С‚РєРѕРІ*\n"]
        for index, source in enumerate(sources, start=1):
            name = _escape_pattern_text(source.get("name") or source.get("id") or f"РСЃС‚РѕС‡РЅРёРє {index}")
            url = _escape_pattern_text(source.get("url") or "URL РЅРµ Р·Р°РґР°РЅ")
            output_name = _escape_pattern_text(source.get("output_name") or "РЅРµ Р·Р°РґР°РЅРѕ")
            method = _escape_pattern_text(source.get("method") or "http")
            processing_mode = _escape_pattern_text(_supplier_stock_processing_mode_label(source.get("processing_mode")))
            enabled = source.get("enabled", True)
            unpack_enabled = source.get("unpack_archive", False)
            status_icon = "рџџў" if enabled else "рџ”ґ"
            unpack_text = "РґР°" if unpack_enabled else "РЅРµС‚"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   вЂў URL: `{url}`\n"
                    f"   вЂў Р¤Р°Р№Р»: `{output_name}`\n"
                    f"   вЂў РњРµС‚РѕРґ: `{method}`\n"
                    f"   вЂў РћР±СЂР°Р±РѕС‚РєР°: `{processing_mode}`\n"
                    f"   вЂў Р Р°СЃРїР°РєРѕРІРєР°: `{unpack_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РёСЃС‚РѕС‡РЅРёРє", callback_data='supplier_stock_source_add')],
    ]

    for source in sources:
        source_id = source.get("id") or ""
        if not source_id:
            continue
        enabled = source.get("enabled", True)
        unpack_enabled = source.get("unpack_archive", False)
        toggle_text = "в›”пёЏ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "вњ… Р’РєР»СЋС‡РёС‚СЊ"
        unpack_text = "рџ“¦ Р Р°СЃРїР°РєРѕРІРєР°: РІРєР»" if unpack_enabled else "рџ“¦ Р Р°СЃРїР°РєРѕРІРєР°: РІС‹РєР»"
        keyboard.append([
            InlineKeyboardButton(
                f"вљ™пёЏ {source.get('name', source_id)}",
                callback_data=f'supplier_stock_source_settings|{source_id}'
            ),
            InlineKeyboardButton(
                f"{toggle_text}",
                callback_data=f'supplier_stock_source_toggle_{source_id}'
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                unpack_text,
                callback_data=f'supplier_stock_source_unpack_toggle_{source_id}'
            ),
            InlineKeyboardButton(
                "рџ—‘пёЏ",
                callback_data=f'supplier_stock_source_delete_{source_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_download'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_source_settings(update, context, source_id: str):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ РёСЃС‚РѕС‡РЅРёРєР° РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_source_settings_id'] = source_id
    context.user_data.pop('supplier_stock_source_field', None)
    context.user_data.pop('supplier_stock_source_field_id', None)
    context.user_data.pop('supplier_stock_source_iek_field', None)
    context.user_data.pop('supplier_stock_source_iek_field_id', None)

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return

    name = _escape_pattern_text(source.get("name") or source_id)
    url = _escape_pattern_text(source.get("url") or "РЅРµ Р·Р°РґР°РЅ")
    output_name = _escape_pattern_text(source.get("output_name") or "РЅРµ Р·Р°РґР°РЅРѕ")
    method = _escape_pattern_text(source.get("method") or "http")
    processing_mode = source.get("processing_mode") or "table"
    processing_label = _escape_pattern_text(_supplier_stock_processing_mode_label(processing_mode))
    discover = source.get("discover")
    discover_text = "РЅРµ Р·Р°РґР°РЅРѕ"
    if isinstance(discover, dict):
        discover_text = _escape_pattern_text(
            f"{discover.get('url', '')} | {discover.get('pattern', '')} | {discover.get('prefix', '')}"
        )
    vars_map = source.get("vars") or {}
    vars_text = ", ".join([f"{key}={value}" for key, value in vars_map.items()]) if vars_map else "РЅРµ Р·Р°РґР°РЅРѕ"
    auth_state = "Р·Р°РґР°РЅРѕ" if source.get("auth") else "РЅРµ Р·Р°РґР°РЅРѕ"
    pre_request = source.get("pre_request") or {}
    pre_request_text = "РЅРµ Р·Р°РґР°РЅРѕ"
    if pre_request:
        pre_request_text = _escape_pattern_text(f"{pre_request.get('url', '')} | {pre_request.get('data', '')}")
    options = []
    if source.get("include_headers"):
        options.append("headers")
    if source.get("append"):
        options.append("append")
    options_text = ", ".join(options) if options else "РЅРµ Р·Р°РґР°РЅРѕ"
    upload_subdir = _escape_pattern_text(source.get("upload_subdir") or "РЅРµ Р·Р°РґР°РЅРѕ")
    individual_dir = source.get("individual_directory") or {}
    individual_enabled = individual_dir.get("enabled", False)
    individual_status = "РІРєР»" if individual_enabled else "РІС‹РєР»"
    individual_path = _escape_pattern_text(individual_dir.get("unc_path") or "РЅРµ Р·Р°РґР°РЅРѕ")
    status_icon = "рџџў" if source.get("enabled", True) else "рџ”ґ"
    unpack_text = "РІРєР»" if source.get("unpack_archive", False) else "РІС‹РєР»"

    rules = config.get("processing", {}).get("rules", [])
    matched_rules = [
        rule for rule in rules
        if _processing_rule_matches_source(rule, source_id, "download", config)
    ]
    iek_section: list[str] = []
    if processing_mode == "iek_json":
        iek_settings = source.get("iek_json") or {}
        stores = iek_settings.get("stores", {})
        orc_stores = iek_settings.get("orc_stores", [])
        outputs = iek_settings.get("outputs", {})
        stores_text = _escape_pattern_text(
            ", ".join([f"{key}={value}" for key, value in stores.items()]) or "РЅРµ Р·Р°РґР°РЅРѕ"
        )
        orc_text = _escape_pattern_text(
            ", ".join([f"{item.get('key')}={item.get('stor')}" for item in orc_stores if isinstance(item, dict)])
            or "РЅРµ Р·Р°РґР°РЅРѕ"
        )
        outputs_text = _escape_pattern_text(
            ", ".join([f"{key}={value}" for key, value in outputs.items()]) or "РЅРµ Р·Р°РґР°РЅРѕ"
        )
        prefix_text = _escape_pattern_text(iek_settings.get("prefix") or "РЅРµ Р·Р°РґР°РЅРѕ")
        msk_stores = iek_settings.get("msk_stores", [])
        msk_text = _escape_pattern_text(", ".join(msk_stores) or "РЅРµ Р·Р°РґР°РЅРѕ")
        nsk_text = _escape_pattern_text(iek_settings.get("nsk_store") or "РЅРµ Р·Р°РґР°РЅРѕ")
        iek_section = [
            "вљ™пёЏ *IEK JSON*",
            f"вЂў РЎРєР»Р°РґС‹: `{stores_text}`",
            f"вЂў РњРЎРљ СЃРєР»Р°РґС‹: `{msk_text}`",
            f"вЂў РќРЎРљ СЃРєР»Р°Рґ: `{nsk_text}`",
            f"вЂў ORK stor: `{orc_text}`",
            f"вЂў РџСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°: `{prefix_text}`",
            f"вЂў Р¤Р°Р№Р»С‹: `{outputs_text}`",
        ]

    message_lines = [
        f"вљ™пёЏ *РСЃС‚РѕС‡РЅРёРє РѕСЃС‚Р°С‚РєРѕРІ*\n",
        f"{status_icon} *{name}*",
        f"вЂў URL: `{url}`",
        f"вЂў Р¤Р°Р№Р»: `{output_name}`",
        f"вЂў РњРµС‚РѕРґ: `{method}`",
        f"вЂў РћР±СЂР°Р±РѕС‚РєР°: `{processing_label}`",
        f"вЂў РџРѕРёСЃРє СЃСЃС‹Р»РєРё: `{discover_text}`",
        f"вЂў РџРµСЂРµРјРµРЅРЅС‹Рµ: `{_escape_pattern_text(vars_text)}`",
        f"вЂў РђРІС‚РѕСЂРёР·Р°С†РёСЏ: `{auth_state}`",
        f"вЂў РџСЂРµРґР·Р°РїСЂРѕСЃ: `{pre_request_text}`",
        f"вЂў РћРїС†РёРё: `{_escape_pattern_text(options_text)}`",
        f"вЂў РџРѕРґРєР°С‚Р°Р»РѕРі РІС‹РіСЂСѓР·РєРё: `{upload_subdir}`",
        f"вЂў РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Р№ РєР°С‚Р°Р»РѕРі: `{individual_status}`",
        f"вЂў UNC РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР°: `{individual_path}`",
        f"вЂў Р Р°СЃРїР°РєРѕРІРєР°: `{unpack_text}`",
    ]
    if iek_section:
        message_lines.extend(["", *iek_section])
    message_lines.extend([
        "\nрџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ*",
        f"РџСЂР°РІРёР»: {len(matched_rules)}",
    ])
    if matched_rules:
        for index, rule in enumerate(matched_rules, start=1):
            rule_name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"РџСЂР°РІРёР»Рѕ {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "РЅРµ Р·Р°РґР°РЅРѕ")
            enabled = rule.get("enabled", True)
            status = "рџџў" if enabled else "рџ”ґ"
            message_lines.append(f"{index}. {status} *{rule_name}* (`{source_file}`)")

    message_lines.append("\nР’С‹Р±РµСЂРёС‚Рµ РЅР°СЃС‚СЂРѕР№РєСѓ:")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вЂ” РќР°СЃС‚СЂРѕР№РєРё РёСЃС‚РѕС‡РЅРёРєР° вЂ”", callback_data='supplier_stock_noop')],
        [
            InlineKeyboardButton("вњЏпёЏ РќР°Р·РІР°РЅРёРµ", callback_data=f'supplier_stock_source_field|{source_id}|name'),
            InlineKeyboardButton("рџ”— URL", callback_data=f'supplier_stock_source_field|{source_id}|url'),
        ],
        [
            InlineKeyboardButton("рџ”Ћ РџРѕРёСЃРє СЃСЃС‹Р»РєРё", callback_data=f'supplier_stock_source_field|{source_id}|discover'),
            InlineKeyboardButton("рџ§© РџРµСЂРµРјРµРЅРЅС‹Рµ", callback_data=f'supplier_stock_source_field|{source_id}|vars'),
        ],
        [
            InlineKeyboardButton("рџ“„ РРјСЏ С„Р°Р№Р»Р°", callback_data=f'supplier_stock_source_field|{source_id}|output_name'),
            InlineKeyboardButton("рџ”ђ РђРІС‚РѕСЂРёР·Р°С†РёСЏ", callback_data=f'supplier_stock_source_field|{source_id}|auth'),
        ],
        [
            InlineKeyboardButton("рџ“¬ РџСЂРµРґР·Р°РїСЂРѕСЃ", callback_data=f'supplier_stock_source_field|{source_id}|pre_request'),
            InlineKeyboardButton("вљ™пёЏ РћРїС†РёРё", callback_data=f'supplier_stock_source_field|{source_id}|options'),
        ],
        [
            InlineKeyboardButton("рџ§© РўРёРї РѕР±СЂР°Р±РѕС‚РєРё", callback_data=f'supplier_stock_source_field|{source_id}|processing_mode'),
            InlineKeyboardButton("рџ“‚ РџРѕРґРєР°С‚Р°Р»РѕРі РІС‹РіСЂСѓР·РєРё", callback_data=f'supplier_stock_source_field|{source_id}|upload_subdir'),
        ],
    ]
    if processing_mode == "iek_json":
        keyboard.append([
            InlineKeyboardButton("вљ™пёЏ IEK JSON", callback_data=f'supplier_stock_source_iek_settings|{source_id}')
        ])
    keyboard.extend([
        [
            InlineKeyboardButton("рџ“Ѓ РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Р№ РєР°С‚Р°Р»РѕРі", callback_data=f'supplier_stock_source_individual|{source_id}'),
        ],
        [
            InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data=f'supplier_stock_source_toggle_{source_id}'),
            InlineKeyboardButton(f"рџ“¦ Р Р°СЃРїР°РєРѕРІРєР°: {unpack_text}", callback_data=f'supplier_stock_source_unpack_toggle_{source_id}')
        ],
        [InlineKeyboardButton("вЂ” РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ вЂ”", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("рџ“‹ РџСЂР°РІРёР»Р° РѕР±СЂР°Р±РѕС‚РєРё", callback_data=f'supplier_stock_processing_source|{source_id}|menu')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РїСЂР°РІРёР»Рѕ", callback_data=f'supplier_stock_processing_source|{source_id}|add')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ],
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_individual_settings(update, context, source_id: str) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° РёСЃС‚РѕС‡РЅРёРєР°."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return

    individual_dir = source.get("individual_directory") or {}
    enabled = individual_dir.get("enabled", False)
    status_text = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if enabled else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    unc_path = _escape_pattern_text(individual_dir.get("unc_path") or "РЅРµ Р·Р°РґР°РЅРѕ")
    login = _escape_pattern_text(individual_dir.get("login") or "РЅРµ Р·Р°РґР°РЅРѕ")
    password = "Р·Р°РґР°РЅРѕ" if individual_dir.get("password") else "РЅРµ Р·Р°РґР°РЅРѕ"

    message = (
        "рџ“Ѓ *РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Р№ РєР°С‚Р°Р»РѕРі*\n\n"
        f"РЎС‚Р°С‚СѓСЃ: {status_text}\n"
        f"UNC РїСѓС‚СЊ: `{unc_path}`\n"
        f"Р›РѕРіРёРЅ: `{login}`\n"
        f"РџР°СЂРѕР»СЊ: `{password}`\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data=f'supplier_stock_source_individual_toggle_{source_id}')],
        [
            InlineKeyboardButton("рџ“‚ UNC РїСѓС‚СЊ", callback_data=f'supplier_stock_source_field|{source_id}|individual_path'),
            InlineKeyboardButton("рџ‘¤ Р›РѕРіРёРЅ", callback_data=f'supplier_stock_source_field|{source_id}|individual_login'),
        ],
        [InlineKeyboardButton("рџ”ђ РџР°СЂРѕР»СЊ", callback_data=f'supplier_stock_source_field|{source_id}|individual_password')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_source_settings|{source_id}')],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_iek_settings(update, context, source_id: str) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РѕР±СЂР°Р±РѕС‚РєРё IEK JSON."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return

    iek_settings = source.get("iek_json") or {}
    stores = iek_settings.get("stores", {})
    orc_stores = iek_settings.get("orc_stores", [])
    outputs = iek_settings.get("outputs", {})

    stores_text = _escape_pattern_text(", ".join([f"{key}={value}" for key, value in stores.items()]) or "РЅРµ Р·Р°РґР°РЅРѕ")
    orc_text = _escape_pattern_text(
        ", ".join([f"{item.get('key')}={item.get('stor')}" for item in orc_stores if isinstance(item, dict)])
        or "РЅРµ Р·Р°РґР°РЅРѕ"
    )
    outputs_text = _escape_pattern_text(
        ", ".join([f"{key}={value}" for key, value in outputs.items()]) or "РЅРµ Р·Р°РґР°РЅРѕ"
    )
    prefix_text = _escape_pattern_text(iek_settings.get("prefix") or "РЅРµ Р·Р°РґР°РЅРѕ")
    msk_stores = iek_settings.get("msk_stores", [])
    msk_text = _escape_pattern_text(", ".join(msk_stores) or "РЅРµ Р·Р°РґР°РЅРѕ")
    nsk_text = _escape_pattern_text(iek_settings.get("nsk_store") or "РЅРµ Р·Р°РґР°РЅРѕ")

    message = (
        "вљ™пёЏ *IEK JSON*\n\n"
        f"РЎРєР»Р°РґС‹: `{stores_text}`\n"
        f"РњРЎРљ СЃРєР»Р°РґС‹: `{msk_text}`\n"
        f"РќРЎРљ СЃРєР»Р°Рґ: `{nsk_text}`\n"
        f"РћР Рљ stor: `{orc_text}`\n"
        f"РџСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°: `{prefix_text}`\n"
        f"Р¤Р°Р№Р»С‹: `{outputs_text}`\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ—єпёЏ РЎРєР»Р°РґС‹", callback_data=f'supplier_stock_source_iek_field|{source_id}|stores')],
        [InlineKeyboardButton("рџ“Ќ РњРЎРљ СЃРєР»Р°РґС‹", callback_data=f'supplier_stock_source_iek_field|{source_id}|msk_stores')],
        [InlineKeyboardButton("рџ“Ќ РќРЎРљ СЃРєР»Р°Рґ", callback_data=f'supplier_stock_source_iek_field|{source_id}|nsk_store')],
        [InlineKeyboardButton("рџ§ѕ ORK stor", callback_data=f'supplier_stock_source_iek_field|{source_id}|orc_stores')],
        [InlineKeyboardButton("рџЏ·пёЏ РџСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р°", callback_data=f'supplier_stock_source_iek_field|{source_id}|prefix')],
        [InlineKeyboardButton("рџ“„ Р¤Р°Р№Р»С‹", callback_data=f'supplier_stock_source_iek_field|{source_id}|outputs')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_source_settings|{source_id}'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_mail_source_settings(update, context, source_id: str):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_mail_source_settings_id'] = source_id
    context.user_data.pop('supplier_stock_mail_source_field', None)
    context.user_data.pop('supplier_stock_mail_source_field_id', None)

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    name = _escape_pattern_text(source.get("name") or source_id)
    sender = _escape_pattern_text(source.get("sender_pattern") or "Р»СЋР±РѕР№")
    subject = _escape_pattern_text(source.get("subject_pattern") or "Р»СЋР±РѕР№")
    mime_pattern = _escape_pattern_text(source.get("mime_pattern") or "application/.*")
    filename_pattern = _escape_pattern_text(source.get("filename_pattern") or "Р»СЋР±РѕР№")
    expected = source.get("expected_attachments", 1)
    output_template = _escape_pattern_text(source.get("output_template") or "РЅРµ Р·Р°РґР°РЅРѕ")
    enabled = source.get("enabled", True)
    unpack_enabled = source.get("unpack_archive", False)
    status_icon = "рџџў" if enabled else "рџ”ґ"
    unpack_text = "РІРєР»" if unpack_enabled else "РІС‹РєР»"
    upload_subdir = _escape_pattern_text(source.get("upload_subdir") or "РЅРµ Р·Р°РґР°РЅРѕ")
    individual_dir = source.get("individual_directory") or {}
    individual_enabled = individual_dir.get("enabled", False)
    individual_status = "РІРєР»" if individual_enabled else "РІС‹РєР»"
    individual_path = _escape_pattern_text(individual_dir.get("unc_path") or "РЅРµ Р·Р°РґР°РЅРѕ")

    rules = config.get("processing", {}).get("rules", [])
    matched_rules = [
        rule for rule in rules
        if _processing_rule_matches_source(rule, source_id, "mail", config)
    ]

    message_lines = [
        "рџ“Ћ *РџСЂР°РІРёР»Рѕ РІР»РѕР¶РµРЅРёР№*\n",
        f"{status_icon} *{name}*",
        f"вЂў РћС‚РїСЂР°РІРёС‚РµР»СЊ: `{sender}`",
        f"вЂў РўРµРјР°: `{subject}`",
        f"вЂў MIME: `{mime_pattern}`",
        f"вЂў РРјСЏ С„Р°Р№Р»Р°: `{filename_pattern}`",
        f"вЂў РћР¶РёРґР°РµС‚СЃСЏ: `{expected}`",
        f"вЂў РЁР°Р±Р»РѕРЅ: `{output_template}`",
        f"вЂў РџРѕРґРєР°С‚Р°Р»РѕРі РІС‹РіСЂСѓР·РєРё: `{upload_subdir}`",
        f"вЂў РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Р№ РєР°С‚Р°Р»РѕРі: `{individual_status}`",
        f"вЂў UNC РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР°: `{individual_path}`",
        f"вЂў Р Р°СЃРїР°РєРѕРІРєР°: `{unpack_text}`\n",
        "рџ§© *РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ*",
        f"РџСЂР°РІРёР»: {len(matched_rules)}",
    ]
    if matched_rules:
        for index, rule in enumerate(matched_rules, start=1):
            rule_name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"РџСЂР°РІРёР»Рѕ {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "РЅРµ Р·Р°РґР°РЅРѕ")
            enabled_rule = rule.get("enabled", True)
            status = "рџџў" if enabled_rule else "рџ”ґ"
            message_lines.append(f"{index}. {status} *{rule_name}* (`{source_file}`)")

    message_lines.append("\nР’С‹Р±РµСЂРёС‚Рµ РЅР°СЃС‚СЂРѕР№РєСѓ:")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("вЂ” РќР°СЃС‚СЂРѕР№РєРё РїСЂР°РІРёР»Р° вЂ”", callback_data='supplier_stock_noop')],
        [
            InlineKeyboardButton("вњЏпёЏ РќР°Р·РІР°РЅРёРµ", callback_data=f'supplier_stock_mail_field|{source_id}|name'),
            InlineKeyboardButton("рџ‘¤ РћС‚РїСЂР°РІРёС‚РµР»СЊ", callback_data=f'supplier_stock_mail_field|{source_id}|sender'),
        ],
        [
            InlineKeyboardButton("рџ“ќ РўРµРјР°", callback_data=f'supplier_stock_mail_field|{source_id}|subject'),
            InlineKeyboardButton("рџ§ѕ MIME", callback_data=f'supplier_stock_mail_field|{source_id}|mime'),
        ],
        [
            InlineKeyboardButton("рџ“„ РРјСЏ С„Р°Р№Р»Р°", callback_data=f'supplier_stock_mail_field|{source_id}|filename'),
            InlineKeyboardButton("рџ”ў РљРѕР»-РІРѕ РІР»РѕР¶РµРЅРёР№", callback_data=f'supplier_stock_mail_field|{source_id}|expected'),
        ],
        [
            InlineKeyboardButton("рџ“¦ РЁР°Р±Р»РѕРЅ С„Р°Р№Р»Р°", callback_data=f'supplier_stock_mail_field|{source_id}|output'),
        ],
        [
            InlineKeyboardButton("рџ“‚ РџРѕРґРєР°С‚Р°Р»РѕРі РІС‹РіСЂСѓР·РєРё", callback_data=f'supplier_stock_mail_field|{source_id}|upload_subdir'),
            InlineKeyboardButton("рџ“Ѓ РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Р№ РєР°С‚Р°Р»РѕРі", callback_data=f'supplier_stock_mail_source_individual|{source_id}'),
        ],
        [
            InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data=f'supplier_stock_mail_source_toggle_{source_id}'),
            InlineKeyboardButton(f"рџ“¦ Р Р°СЃРїР°РєРѕРІРєР°: {unpack_text}", callback_data=f'supplier_stock_mail_source_unpack_toggle_{source_id}')
        ],
        [InlineKeyboardButton("вЂ” РћР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»РѕРІ вЂ”", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("рџ“‹ РџСЂР°РІРёР»Р° РѕР±СЂР°Р±РѕС‚РєРё", callback_data=f'supplier_stock_processing_mail|{source_id}|menu')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РїСЂР°РІРёР»Рѕ", callback_data=f'supplier_stock_processing_mail|{source_id}|add')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [
            InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_mail_source_individual_settings(update, context, source_id: str) -> None:
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    individual_dir = source.get("individual_directory") or {}
    enabled = individual_dir.get("enabled", False)
    status_text = "рџџў Р’РєР»СЋС‡РµРЅРѕ" if enabled else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ"
    unc_path = _escape_pattern_text(individual_dir.get("unc_path") or "РЅРµ Р·Р°РґР°РЅРѕ")
    login = _escape_pattern_text(individual_dir.get("login") or "РЅРµ Р·Р°РґР°РЅРѕ")
    password = "Р·Р°РґР°РЅРѕ" if individual_dir.get("password") else "РЅРµ Р·Р°РґР°РЅРѕ"

    message = (
        "рџ“Ѓ *РРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Р№ РєР°С‚Р°Р»РѕРі*\n\n"
        f"РЎС‚Р°С‚СѓСЃ: {status_text}\n"
        f"UNC РїСѓС‚СЊ: `{unc_path}`\n"
        f"Р›РѕРіРёРЅ: `{login}`\n"
        f"РџР°СЂРѕР»СЊ: `{password}`\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”Ѓ Р’РєР»СЋС‡РёС‚СЊ/РІС‹РєР»СЋС‡РёС‚СЊ", callback_data=f'supplier_stock_mail_source_individual_toggle_{source_id}')],
        [
            InlineKeyboardButton("рџ“‚ UNC РїСѓС‚СЊ", callback_data=f'supplier_stock_mail_field|{source_id}|individual_path'),
            InlineKeyboardButton("рџ‘¤ Р›РѕРіРёРЅ", callback_data=f'supplier_stock_mail_field|{source_id}|individual_login'),
        ],
        [InlineKeyboardButton("рџ”ђ РџР°СЂРѕР»СЊ", callback_data=f'supplier_stock_mail_field|{source_id}|individual_password')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_mail_source_settings|{source_id}')],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def supplier_stock_start_source_field_edit(update, context, source_id: str, field: str) -> None:
    """Р—Р°РїСЂРѕСЃРёС‚СЊ РёР·РјРµРЅРµРЅРёРµ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ РїРѕР»СЏ РёСЃС‚РѕС‡РЅРёРєР°."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_source_field'] = field
    context.user_data['supplier_stock_source_field_id'] = source_id

    prompts = {
        "name": "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РёСЃС‚РѕС‡РЅРёРєР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "url": "Р’РІРµРґРёС‚Рµ URL РґР»СЏ СЃРєР°С‡РёРІР°РЅРёСЏ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "discover": "Р’РІРµРґРёС‚Рµ РїР°СЂР°РјРµС‚СЂС‹ РїРѕРёСЃРєР° URL (URL | regex | prefix), '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "vars": "Р’РІРµРґРёС‚Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ РїРѕРґСЃС‚Р°РЅРѕРІРєРё key=value С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "output_name": "Р’РІРµРґРёС‚Рµ РёРјСЏ С„Р°Р№Р»Р° РЅР°Р·РЅР°С‡РµРЅРёСЏ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "auth": "Р’РІРµРґРёС‚Рµ login:password, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "pre_request": "Р’РІРµРґРёС‚Рµ URL | РґР°РЅРЅС‹Рµ РґР»СЏ РїСЂРµРґР·Р°РїСЂРѕСЃР°, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "options": "Р’РІРµРґРёС‚Рµ РѕРїС†РёРё (headers, append) С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "processing_mode": "Р’РІРµРґРёС‚Рµ С‚РёРї РѕР±СЂР°Р±РѕС‚РєРё (`table` РёР»Рё `iek\\_json`), '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ:",
        "upload_subdir": "Р’РІРµРґРёС‚Рµ РїРѕРґРєР°С‚Р°Р»РѕРі РґР»СЏ РІС‹РіСЂСѓР·РєРё (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "individual_path": "Р’РІРµРґРёС‚Рµ UNC РїСѓС‚СЊ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "individual_login": "Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "individual_password": "Р’РІРµРґРёС‚Рµ РїР°СЂРѕР»СЊ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
    }

    current_values = {
        "name": source.get("name") or source_id,
        "url": source.get("url") or "-",
        "discover": source.get("discover") or "-",
        "vars": source.get("vars") or "-",
        "output_name": source.get("output_name") or "-",
        "auth": "Р·Р°РґР°РЅРѕ" if source.get("auth") else "-",
        "pre_request": source.get("pre_request") or "-",
        "options": "headers/append" if (source.get("include_headers") or source.get("append")) else "-",
        "processing_mode": source.get("processing_mode") or "table",
        "upload_subdir": source.get("upload_subdir") or "-",
        "individual_path": (source.get("individual_directory") or {}).get("unc_path") or "-",
        "individual_login": (source.get("individual_directory") or {}).get("login") or "-",
        "individual_password": "Р·Р°РґР°РЅРѕ" if (source.get("individual_directory") or {}).get("password") else "-",
    }

    prompt = prompts.get(field, "Р’РІРµРґРёС‚Рµ Р·РЅР°С‡РµРЅРёРµ:")
    current_value = current_values.get(field, "-")
    if isinstance(current_value, dict):
        current_value = json.dumps(current_value, ensure_ascii=False)
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nРўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=f'supplier_stock_source_settings|{source_id}')]
        ])
    )

def supplier_stock_start_source_iek_field_edit(update, context, source_id: str, field: str) -> None:
    """Р—Р°РїСЂРѕСЃРёС‚СЊ РёР·РјРµРЅРµРЅРёРµ РїР°СЂР°РјРµС‚СЂРѕРІ IEK JSON."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_source_iek_field'] = field
    context.user_data['supplier_stock_source_iek_field_id'] = source_id

    prompts = {
        "stores": "Р’РІРµРґРёС‚Рµ СЃРєР»Р°РґС‹ РІ С„РѕСЂРјР°С‚Рµ key=uuid С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ:",
        "msk_stores": "Р’РІРµРґРёС‚Рµ СЃРїРёСЃРѕРє СЃРєР»Р°РґРѕРІ РњРЎРљ С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ (РЅР°РїСЂРёРјРµСЂ: sherbinka, chehov):",
        "nsk_store": "Р’РІРµРґРёС‚Рµ РєР»СЋС‡ СЃРєР»Р°РґР° РќРЎРљ (РЅР°РїСЂРёРјРµСЂ: novosibirsk):",
        "orc_stores": "Р’РІРµРґРёС‚Рµ ORK stor РІ С„РѕСЂРјР°С‚Рµ key=stor С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ:",
        "prefix": "Р’РІРµРґРёС‚Рµ РїСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° РґР»СЏ ORK (РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "outputs": "Р’РІРµРґРёС‚Рµ РёРјРµРЅР° С„Р°Р№Р»РѕРІ РІ С„РѕСЂРјР°С‚Рµ orig=..., msk=..., nsk=..., orc=... С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ:",
    }

    iek_settings = source.get("iek_json") or {}
    current_values = {
        "stores": iek_settings.get("stores") or "-",
        "msk_stores": iek_settings.get("msk_stores") or "-",
        "nsk_store": iek_settings.get("nsk_store") or "-",
        "orc_stores": iek_settings.get("orc_stores") or "-",
        "prefix": iek_settings.get("prefix") or "-",
        "outputs": iek_settings.get("outputs") or "-",
    }

    prompt = prompts.get(field, "Р’РІРµРґРёС‚Рµ Р·РЅР°С‡РµРЅРёРµ:")
    current_value = current_values.get(field, "-")
    if isinstance(current_value, (dict, list)):
        current_value = json.dumps(current_value, ensure_ascii=False)

    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nРўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=f'supplier_stock_source_iek_settings|{source_id}')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
        ])
    )

def supplier_stock_start_mail_source_field_edit(update, context, source_id: str, field: str) -> None:
    """Р—Р°РїСЂРѕСЃРёС‚СЊ РёР·РјРµРЅРµРЅРёРµ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ РїРѕР»СЏ РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_mail_source_field'] = field
    context.user_data['supplier_stock_mail_source_field_id'] = source_id

    prompts = {
        "name": "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РїСЂР°РІРёР»Р° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "sender": "Р’РІРµРґРёС‚Рµ regex/Р°РґСЂРµСЃ РѕС‚РїСЂР°РІРёС‚РµР»СЏ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "subject": "Р’РІРµРґРёС‚Рµ regex С‚РµРјС‹ РїРёСЃСЊРјР°, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "mime": "Р’РІРµРґРёС‚Рµ MIME-С„РёР»СЊС‚СЂ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "filename": "Р’РІРµРґРёС‚Рµ regex РёРјРµРЅРё РІР»РѕР¶РµРЅРёСЏ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:",
        "expected": "Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ РѕР¶РёРґР°РµРјС‹С… РІР»РѕР¶РµРЅРёР№ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "output": "Р’РІРµРґРёС‚Рµ С€Р°Р±Р»РѕРЅ РёРјРµРЅРё РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "upload_subdir": "Р’РІРµРґРёС‚Рµ РїРѕРґРєР°С‚Р°Р»РѕРі РґР»СЏ РІС‹РіСЂСѓР·РєРё (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "individual_path": "Р’РІРµРґРёС‚Рµ UNC РїСѓС‚СЊ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "individual_login": "Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "individual_password": "Р’РІРµРґРёС‚Рµ РїР°СЂРѕР»СЊ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
    }

    current_values = {
        "name": source.get("name") or source_id,
        "sender": source.get("sender_pattern") or "-",
        "subject": source.get("subject_pattern") or "-",
        "mime": source.get("mime_pattern") or "application/.*",
        "filename": source.get("filename_pattern") or "-",
        "expected": source.get("expected_attachments", 1),
        "output": source.get("output_template") or "-",
        "upload_subdir": source.get("upload_subdir") or "-",
        "individual_path": (source.get("individual_directory") or {}).get("unc_path") or "-",
        "individual_login": (source.get("individual_directory") or {}).get("login") or "-",
        "individual_password": "Р·Р°РґР°РЅРѕ" if (source.get("individual_directory") or {}).get("password") else "-",
    }

    prompt = prompts.get(field, "Р’РІРµРґРёС‚Рµ Р·РЅР°С‡РµРЅРёРµ:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nРўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=f'supplier_stock_mail_source_settings|{source_id}')]
        ])
    )


def supplier_stock_start_resource_wizard(update, context) -> None:
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° РґРѕР±Р°РІР»РµРЅРёСЏ СЂРµСЃСѓСЂСЃР° РІС‹РіСЂСѓР·РєРё."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_resource_stage'] = 'name'
    context.user_data['supplier_stock_resource_data'] = {}
    context.user_data['supplier_stock_resource_add'] = True

    query.edit_message_text(
        "вћ• *РќРѕРІС‹Р№ СЂРµСЃСѓСЂСЃ РІС‹РіСЂСѓР·РєРё*\n\nР’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ СЂРµСЃСѓСЂСЃР°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_resources')]
        ])
    )


def supplier_stock_start_resource_field_edit(update, context, resource_id: str, field: str) -> None:
    """Р—Р°РїСЂРѕСЃРёС‚СЊ РёР·РјРµРЅРµРЅРёРµ РїРѕР»СЏ СЂРµСЃСѓСЂСЃР° РІС‹РіСЂСѓР·РєРё."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        query.edit_message_text(
            "вќЊ Р РµСЃСѓСЂСЃ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_resources')]
            ])
        )
        return

    context.user_data['supplier_stock_resource_field'] = field
    context.user_data['supplier_stock_resource_field_id'] = resource_id

    prompts = {
        "name": "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ СЂРµСЃСѓСЂСЃР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "unc_path": "Р’РІРµРґРёС‚Рµ UNC РїСѓС‚СЊ РєРѕСЂРЅРµРІРѕРіРѕ РєР°С‚Р°Р»РѕРіР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "login": "Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ СЂРµСЃСѓСЂСЃР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "password": "Р’РІРµРґРёС‚Рµ РїР°СЂРѕР»СЊ СЂРµСЃСѓСЂСЃР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
    }

    current_values = {
        "name": resource.get("name") or resource_id,
        "unc_path": resource.get("unc_path") or "-",
        "login": resource.get("login") or "-",
        "password": "Р·Р°РґР°РЅРѕ" if resource.get("password") else "-",
    }

    prompt = prompts.get(field, "Р’РІРµРґРёС‚Рµ Р·РЅР°С‡РµРЅРёРµ:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nРўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=f'supplier_stock_resource_settings|{resource_id}')]
        ])
    )


def supplier_stock_start_ftp_field_edit(update, context, field: str) -> None:
    """Р—Р°РїСЂРѕСЃРёС‚СЊ РёР·РјРµРЅРµРЅРёРµ РїР°СЂР°РјРµС‚СЂР° FTP."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_ftp_field'] = field
    prompts = {
        "host": "Р’РІРµРґРёС‚Рµ HOST FTP (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ):",
        "login": "Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ FTP (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
        "password": "Р’РІРµРґРёС‚Рµ РїР°СЂРѕР»СЊ FTP (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ, 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ):",
    }

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})
    current_values = {
        "host": ftp_settings.get("host") or "-",
        "login": ftp_settings.get("login") or "-",
        "password": "Р·Р°РґР°РЅРѕ" if ftp_settings.get("password") else "-",
    }
    prompt = prompts.get(field, "Р’РІРµРґРёС‚Рµ Р·РЅР°С‡РµРЅРёРµ:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nРўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_ftp')]
        ])
    )

def supplier_stock_start_processing_wizard(
    update,
    context,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° РґРѕР±Р°РІР»РµРЅРёСЏ РїСЂР°РІРёР»Р° РѕР±СЂР°Р±РѕС‚РєРё."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)
    context.user_data.pop('supplier_stock_add_source', None)
    context.user_data.pop('supplier_stock_edit_source', None)
    context.user_data.pop('supplier_stock_mail_edit', None)
    context.user_data.pop('supplier_stock_mail_add_source', None)
    context.user_data.pop('supplier_stock_mail_edit_source', None)
    context.user_data['supplier_stock_processing_stage'] = 'name'
    context.user_data['supplier_stock_processing_data'] = {}
    context.user_data['supplier_stock_processing_add'] = True
    context.user_data['supplier_stock_processing_source_id'] = source_id
    context.user_data['supplier_stock_processing_source_kind'] = source_kind
    context.user_data['supplier_stock_processing_back'] = back_callback

    if source_id:
        context.user_data['supplier_stock_processing_data']['source_id'] = source_id
    if source_kind:
        context.user_data['supplier_stock_processing_data']['source_kind'] = source_kind

    query.edit_message_text(
        "вћ• *РќРѕРІРѕРµ РїСЂР°РІРёР»Рѕ РѕР±СЂР°Р±РѕС‚РєРё*\n\nР’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РїСЂР°РІРёР»Р°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=back_callback)]
        ])
    )

def supplier_stock_start_processing_edit_wizard(
    update,
    context,
    rule_id: str,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂР°РІРёР»Р° РѕР±СЂР°Р±РѕС‚РєРё."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)
    context.user_data.pop('supplier_stock_add_source', None)
    context.user_data.pop('supplier_stock_edit_source', None)
    context.user_data.pop('supplier_stock_mail_edit', None)
    context.user_data.pop('supplier_stock_mail_add_source', None)
    context.user_data.pop('supplier_stock_mail_edit_source', None)
    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    rule = next((item for item in rules if str(item.get("id")) == rule_id), None)

    if not rule:
        query.edit_message_text(
            "вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
            ])
        )
        return

    context.user_data['supplier_stock_processing_edit'] = True
    context.user_data['supplier_stock_processing_edit_id'] = rule_id
    context.user_data['supplier_stock_processing_data'] = dict(rule)
    context.user_data['supplier_stock_processing_stage'] = 'edit_name'
    context.user_data['supplier_stock_processing_source_id'] = source_id
    context.user_data['supplier_stock_processing_source_kind'] = source_kind
    context.user_data['supplier_stock_processing_back'] = back_callback

    if source_id:
        context.user_data['supplier_stock_processing_data']['source_id'] = source_id
    if source_kind:
        context.user_data['supplier_stock_processing_data']['source_kind'] = source_kind

    query.edit_message_text(
        f"вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РїСЂР°РІРёР»Р° РѕР±СЂР°Р±РѕС‚РєРё*\n\n"
        f"РўРµРєСѓС‰РµРµ РёРјСЏ: `{_escape_pattern_text(rule.get('name'))}`\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=back_callback)]
        ])
    )

def supplier_stock_handle_processing_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РјР°СЃС‚РµСЂР° РЅР°СЃС‚СЂРѕР№РєРё РѕР±СЂР°Р±РѕС‚РєРё."""
    stage = context.user_data.get('supplier_stock_processing_stage')
    data = context.user_data.get('supplier_stock_processing_data', {})
    raw_input = update.message.text or ""
    user_input = raw_input.rstrip("\n")
    user_input_stripped = user_input.strip()
    source_id = context.user_data.get('supplier_stock_processing_source_id')
    source_kind = context.user_data.get('supplier_stock_processing_source_kind')
    if source_id:
        data['source_id'] = source_id
    if source_kind:
        data['source_kind'] = source_kind
    back_callback = context.user_data.get('supplier_stock_processing_back', 'supplier_stock_processing')

    if context.user_data.get('supplier_stock_processing_field'):
        field = context.user_data.pop('supplier_stock_processing_field')
        variant_index = context.user_data.pop('supplier_stock_processing_variant_index', None)
        item_index = context.user_data.pop('supplier_stock_processing_item_index', None)
        rule_data = context.user_data.get('supplier_stock_processing_rule_data', {})
        if source_id:
            rule_data['source_id'] = source_id
        if source_kind:
            rule_data['source_kind'] = source_kind
        variant_fields = {
            'article_col',
            'article_filter',
            'extra_filter',
            'article_prefix',
            'article_postfix',
            'article_transform',
            'data_columns_count',
            'data_column',
            'output_name',
            'output_format',
            'orc_prefix',
            'orc_stor',
            'orc_column',
            'orc_output_name',
            'orc_output_format',
        }
        if variant_index is not None and field in variant_fields:
            variant = _ensure_processing_variant(rule_data, variant_index)
            if field == 'article_col':
                article_col = _parse_positive_int(user_input_stripped)
                if article_col is None:
                    update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
                    return None
                variant['article_col'] = article_col
            elif field == 'article_filter':
                if user_input_stripped not in ('-', ''):
                    variant['article_filter'] = user_input_stripped
                    if variant.get("use_article_filter") is None:
                        variant["use_article_filter"] = True
                else:
                    variant.pop('article_filter', None)
            elif field == 'extra_filter':
                if user_input_stripped in ('-', ''):
                    variant.pop('extra_filter', None)
                    variant.pop('extra_filter_col', None)
                else:
                    if ';' not in user_input_stripped:
                        update.message.reply_text("вќЊ РЈРєР°Р¶РёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё Рё СѓСЃР»РѕРІРёРµ С‡РµСЂРµР· ';'.")
                        return None
                    col_part, filter_part = user_input_stripped.split(';', 1)
                    extra_filter_col = _parse_positive_int(col_part.strip())
                    extra_filter_value = filter_part.strip()
                    if extra_filter_col is None:
                        update.message.reply_text("вќЊ РќРѕРјРµСЂ РєРѕР»РѕРЅРєРё РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ С†РµР»С‹Рј С‡РёСЃР»РѕРј Р±РѕР»СЊС€Рµ 0.")
                        return None
                    if not extra_filter_value:
                        update.message.reply_text("вќЊ РЈРєР°Р¶РёС‚Рµ СѓСЃР»РѕРІРёРµ РѕС‚Р±РѕСЂР° РїРѕСЃР»Рµ ';'.")
                        return None
                    variant['extra_filter_col'] = extra_filter_col
                    variant['extra_filter'] = extra_filter_value
            elif field == 'article_prefix':
                if user_input_stripped in ('-', ''):
                    variant['article_prefix'] = ""
                else:
                    variant['article_prefix'] = user_input
            elif field == 'article_postfix':
                raw_value = user_input
                if raw_value == "":
                    variant['article_postfix'] = ""
                elif raw_value.strip() == "-":
                    variant['article_postfix'] = ""
                else:
                    variant['article_postfix'] = raw_value
            elif field == 'article_transform':
                raw_value = user_input
                if raw_value.strip() in ('', '-'):
                    variant['article_transform'] = {
                        "pattern": "",
                        "replacement": "",
                    }
                else:
                    if "=>" in raw_value:
                        pattern_part, replacement_part = raw_value.split("=>", 1)
                        pattern_value = pattern_part.strip()
                        replacement_value = replacement_part
                    else:
                        pattern_value = raw_value.strip()
                        replacement_value = ""
                    if not pattern_value:
                        update.message.reply_text("вќЊ РЈРєР°Р¶РёС‚Рµ regex-РїР°С‚С‚РµСЂРЅ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ Р°СЂС‚РёРєСѓР»Р°.")
                        return None
                    variant['article_transform'] = {
                        "pattern": pattern_value,
                        "replacement": replacement_value,
                    }
            elif field == 'data_columns_count':
                columns_count = _parse_positive_int(user_input_stripped)
                if columns_count is None:
                    update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
                    return None
                _sync_variant_columns(variant, columns_count)
            elif field == 'data_column':
                col_value = _parse_positive_int(user_input_stripped)
                if col_value is None:
                    update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
                    return None
                columns = list(variant.get("data_columns", []))
                if item_index is None or item_index >= len(columns):
                    update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ РёРЅРґРµРєСЃ РєРѕР»РѕРЅРєРё.")
                    return None
                columns[item_index] = col_value
                variant['data_columns'] = columns
            elif field == 'output_name':
                if not user_input_stripped:
                    update.message.reply_text("вќЊ РРјСЏ С„Р°Р№Р»Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                    return None
                names = list(variant.get("output_names", []))
                if item_index is None or item_index >= len(names):
                    update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ РёРЅРґРµРєСЃ С„Р°Р№Р»Р°.")
                    return None
                names[item_index] = user_input_stripped
                variant['output_names'] = names
            elif field == 'output_format':
                format_value = user_input_stripped.lower()
                if format_value not in ('xls', 'xlsx', 'csv'):
                    update.message.reply_text("вќЊ Р”РѕРїСѓСЃС‚РёРјС‹Рµ С„РѕСЂРјР°С‚С‹: xls, xlsx, csv.")
                    return None
                variant['output_format'] = format_value
            elif field == 'orc_prefix':
                orc = variant.get("orc", {})
                if user_input_stripped in ('-', ''):
                    orc['prefix'] = ""
                else:
                    orc['prefix'] = user_input
                variant['orc'] = orc
            elif field == 'orc_stor':
                if not user_input_stripped:
                    update.message.reply_text("вќЊ Stor РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                    return None
                orc = variant.get("orc", {})
                orc['stor'] = user_input_stripped
                variant['orc'] = orc
            elif field == 'orc_column':
                col_value = _parse_positive_int(user_input_stripped)
                if col_value is None:
                    update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
                    return None
                orc = variant.get("orc", {})
                orc['column'] = col_value
                variant['orc'] = orc
            elif field == 'orc_output_name':
                orc = variant.get("orc", {})
                if user_input_stripped in ('-', ''):
                    orc.pop('output_name', None)
                else:
                    orc['output_name'] = user_input_stripped
                variant['orc'] = orc
            elif field == 'orc_output_format':
                if user_input_stripped in ('-', ''):
                    orc = variant.get("orc", {})
                    orc.pop('output_format', None)
                    variant['orc'] = orc
                else:
                    format_value = user_input_stripped.lower()
                    if format_value not in ('xls', 'xlsx', 'csv'):
                        update.message.reply_text("вќЊ Р”РѕРїСѓСЃС‚РёРјС‹Рµ С„РѕСЂРјР°С‚С‹: xls, xlsx, csv.")
                        return None
                    orc = variant.get("orc", {})
                    orc['output_format'] = format_value
                    variant['orc'] = orc
            rule_data['variants'][variant_index] = variant
        else:
            if field == 'name':
                if not user_input_stripped:
                    update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                    return None
                rule_data['name'] = user_input_stripped
            elif field == 'source_file':
                if not user_input_stripped:
                    update.message.reply_text("вќЊ РРјСЏ С„Р°Р№Р»Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                    return None
                rule_data['source_file'] = user_input_stripped
            elif field == 'data_row':
                data_row = _parse_positive_int(user_input_stripped)
                if data_row is None:
                    update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
                    return None
                rule_data['data_row'] = data_row
            elif field == 'output_name':
                if not user_input_stripped:
                    update.message.reply_text("вќЊ РРјСЏ С„Р°Р№Р»Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                    return None
                rule_data['output_name'] = user_input_stripped
            else:
                update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РІР°СЂРёР°РЅС‚ РЅР°СЃС‚СЂРѕР№РєРё.")
                return None
        context.user_data['supplier_stock_processing_rule_data'] = rule_data
        context.user_data['supplier_stock_processing_rule_dirty'] = True
        _supplier_stock_close_prompt_message(context)
        if variant_index is None:
            update.message.reply_text(
                "вњ… Р“РѕС‚РѕРІРѕ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_processing_rule|menu')]
                ])
            )
        else:
            update.message.reply_text(
                "вњ… Р“РѕС‚РѕРІРѕ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_processing_variant|menu|{variant_index}')]
                ])
            )
        _persist_processing_rule_data(context)
        return None

    if stage == 'name':
        if not user_input_stripped:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        data['name'] = user_input_stripped
        data['id'] = _slugify_supplier_source_id(user_input_stripped)
        context.user_data['supplier_stock_processing_stage'] = 'source_file'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Р’РІРµРґРёС‚Рµ С„Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РЅР°РїСЂРёРјРµСЂ: supplier_1_orig.xls):")
        return None

    if stage == 'edit_name':
        if user_input_stripped and user_input_stripped not in ('-',):
            data['name'] = user_input_stripped
        context.user_data['supplier_stock_processing_stage'] = 'edit_source_file'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text(
            f"РўРµРєСѓС‰РёР№ С„Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР°: {data.get('source_file', '-')}\n"
            "Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ С„Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ):"
        )
        return None

    if stage == 'edit_source_file':
        if user_input_stripped and user_input_stripped not in ('-',):
            data['source_file'] = user_input_stripped
        context.user_data['supplier_stock_processing_stage'] = 'edit_reconfigure'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text(
            "РџРµСЂРµРЅР°СЃС‚СЂРѕРёС‚СЊ РѕР±СЂР°Р±РѕС‚РєСѓ? (РґР°/РЅРµС‚):"
        )
        return None

    if stage == 'edit_reconfigure':
        reconfigure = _parse_yes_no(user_input_stripped)
        if reconfigure is None:
            update.message.reply_text("вќЊ РћС‚РІРµС‚СЊС‚Рµ 'РґР°' РёР»Рё 'РЅРµС‚'.")
            return None
        if not reconfigure:
            _save_supplier_stock_processing_rule(context, data, edit_id=data.get("id"))
            update.message.reply_text(
                "вњ… РџСЂР°РІРёР»Рѕ РѕР±РЅРѕРІР»РµРЅРѕ.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
                ])
            )
            return None
        data.pop('variants', None)
        data.pop('variants_count', None)
        data.pop('data_row', None)
        data.pop('requires_processing', None)
        context.user_data['supplier_stock_processing_stage'] = 'needs_processing'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("РўСЂРµР±СѓРµС‚СЃСЏ РѕР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»Р°? (РґР°/РЅРµС‚):")
        return None

    if stage == 'source_file':
        if not user_input_stripped:
            update.message.reply_text("вќЊ Р¤Р°Р№Р» РёСЃС‚РѕС‡РЅРёРєР° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        data['source_file'] = user_input_stripped
        context.user_data['supplier_stock_processing_stage'] = 'needs_processing'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("РўСЂРµР±СѓРµС‚СЃСЏ РѕР±СЂР°Р±РѕС‚РєР° С„Р°Р№Р»Р°? (РґР°/РЅРµС‚):")
        return None

    if stage == 'needs_processing':
        needs_processing = _parse_yes_no(user_input_stripped)
        if needs_processing is None:
            update.message.reply_text("вќЊ РћС‚РІРµС‚СЊС‚Рµ 'РґР°' РёР»Рё 'РЅРµС‚'.")
            return None
        data['requires_processing'] = needs_processing
        if not needs_processing:
            edit_id = data.get("id") if context.user_data.get('supplier_stock_processing_edit') else None
            _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
            done_text = "вњ… РџСЂР°РІРёР»Рѕ РѕР±РЅРѕРІР»РµРЅРѕ." if context.user_data.get('supplier_stock_processing_edit') else "вњ… РџСЂР°РІРёР»Рѕ РґРѕР±Р°РІР»РµРЅРѕ."
            update.message.reply_text(
                done_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
                ])
            )
            return None
        context.user_data['supplier_stock_processing_stage'] = 'variants_count'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("РЎРєРѕР»СЊРєРѕ РІР°СЂРёР°РЅС‚РѕРІ РєРѕРЅРµС‡РЅС‹С… С„Р°Р№Р»РѕРІ С‚СЂРµР±СѓРµС‚СЃСЏ? (С‡РёСЃР»Рѕ):")
        return None

    if stage == 'variants_count':
        variants_count = _parse_positive_int(user_input_stripped)
        if variants_count is None:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
            return None
        data['variants_count'] = variants_count
        data['variants'] = []
        context.user_data['supplier_stock_processing_variant_index'] = 0
        context.user_data['supplier_stock_processing_stage'] = 'data_row'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РїРµСЂРІРѕР№ СЃС‚СЂРѕРєРё СЃ РґР°РЅРЅС‹РјРё (РЅР°РїСЂРёРјРµСЂ: 2):")
        return None

    if stage == 'data_row':
        data_row = _parse_positive_int(user_input_stripped)
        if data_row is None:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
            return None
        data['data_row'] = data_row
        context.user_data['supplier_stock_processing_stage'] = 'variant_article_col'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ Р°СЂС‚РёРєСѓР»РѕРј:")
        return None

    if stage == 'variant_article_col':
        article_col = _parse_positive_int(user_input_stripped)
        if article_col is None:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
            return None
        context.user_data['supplier_stock_processing_current_variant'] = {
            "article_col": article_col,
        }
        context.user_data['supplier_stock_processing_stage'] = 'variant_article_filter'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ СѓСЃР»РѕРІРёСЏ РѕС‚Р±РѕСЂР° Р°СЂС‚РёРєСѓР»РѕРІ (regex) РёР»Рё '-' РґР»СЏ РІСЃРµС….\n\n"
            "РџСЂРёРјРµСЂС‹ СѓСЃР»РѕРІРёР№:\n"
            "вЂў $1 ~ /^[0-9]/ && $col+0 > 0\n"
            "вЂў $1 ~ /^[A-Z].*/ && $4 ~ /^[0-9]+$/\n"
            "вЂў grep -E '^DKS [0-9A-Z]{6,},'\n"
            "вЂў gsub(/^\./, \"\", art); gsub(/[A-Za-z]+$/, \"\", art);\n"
            "вЂў ($3+0 > 0) && ($4 == \"РњРѕСЃРєРІР°\")"
        )
        return None

    if stage == 'variant_article_filter':
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        if user_input_stripped not in ('-', ''):
            variant['article_filter'] = user_input_stripped
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'variant_prefix'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РїСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° (РёР»Рё '-' РµСЃР»Рё РЅРµ РЅСѓР¶РµРЅ). "
            "РџСЂРѕР±РµР»С‹ РІ РєРѕРЅС†Рµ СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ, Р»РёР±Рѕ РёСЃРїРѕР»СЊР·СѓР№С‚Рµ \\s."
        )
        return None

    if stage == 'variant_prefix':
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        if user_input_stripped in ('-', ''):
            variant['article_prefix'] = ""
        else:
            variant['article_prefix'] = user_input
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'variant_postfix'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РїРѕСЃС‚С„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° (РёР»Рё '-' РµСЃР»Рё РЅРµ РЅСѓР¶РµРЅ). "
            "РџСЂРѕР±РµР»С‹ РІ РєРѕРЅС†Рµ СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ."
        )
        return None

    if stage == 'variant_postfix':
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        raw_value = user_input
        if raw_value == "":
            variant['article_postfix'] = ""
        elif raw_value.strip() == "-":
            variant['article_postfix'] = ""
        else:
            variant['article_postfix'] = raw_value
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'data_columns_count'
        update.message.reply_text("РЎРєРѕР»СЊРєРѕ РєРѕР»РѕРЅРѕРє СЃ РґР°РЅРЅС‹РјРё РЅСѓР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ? (С‡РёСЃР»Рѕ):")
        return None

    if stage == 'data_columns_count':
        columns_count = _parse_positive_int(user_input_stripped)
        if columns_count is None:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
            return None
        context.user_data['supplier_stock_processing_data_columns_expected'] = columns_count
        context.user_data['supplier_stock_processing_data_columns'] = []
        context.user_data['supplier_stock_processing_stage'] = 'data_column'
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё 1 РёР· %d:" % columns_count)
        return None

    if stage == 'data_column':
        col_value = _parse_positive_int(user_input_stripped)
        if col_value is None:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
            return None
        columns = context.user_data.get('supplier_stock_processing_data_columns', [])
        columns.append(col_value)
        context.user_data['supplier_stock_processing_data_columns'] = columns
        expected = context.user_data.get('supplier_stock_processing_data_columns_expected', 0)
        if len(columns) < expected:
            update.message.reply_text(
                "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ РґР°РЅРЅС‹РјРё %d РёР· %d:" % (len(columns) + 1, expected)
            )
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['data_columns'] = columns
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_output_names_expected'] = expected
        context.user_data['supplier_stock_processing_output_names'] = []
        context.user_data['supplier_stock_processing_stage'] = 'output_name'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РёРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РґР»СЏ РєРѕР»РѕРЅРєРё 1 РёР· %d "
            "(РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ {index}, {name}, {filename}):" % expected
        )
        return None

    if stage == 'output_name':
        if not user_input_stripped:
            update.message.reply_text("вќЊ РРјСЏ С„Р°Р№Р»Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        names = context.user_data.get('supplier_stock_processing_output_names', [])
        names.append(user_input_stripped)
        context.user_data['supplier_stock_processing_output_names'] = names
        expected = context.user_data.get('supplier_stock_processing_output_names_expected', 0)
        if len(names) < expected:
            update.message.reply_text(
                "Р’РІРµРґРёС‚Рµ РёРјСЏ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° РґР»СЏ РєРѕР»РѕРЅРєРё %d РёР· %d "
                "(РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ {index}, {name}, {filename}):" % (len(names) + 1, expected)
            )
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['output_names'] = names
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'output_format'
        update.message.reply_text("Р’РІРµРґРёС‚Рµ С„РѕСЂРјР°С‚ РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° (xls, xlsx, csv):")
        return None

    if stage == 'output_format':
        format_value = user_input_stripped.lower()
        if format_value not in ('xls', 'xlsx', 'csv'):
            update.message.reply_text("вќЊ Р”РѕРїСѓСЃС‚РёРјС‹Рµ С„РѕСЂРјР°С‚С‹: xls, xlsx, csv.")
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['output_format'] = format_value
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'orc_required'
        update.message.reply_text("РќСѓР¶РЅРѕ С„РѕСЂРјРёСЂРѕРІР°С‚СЊ РѕС‚РґРµР»СЊРЅС‹Р№ С„Р°Р№Р» РґР»СЏ РћР Рљ? (РґР°/РЅРµС‚):")
        return None

    if stage == 'orc_required':
        orc_required = _parse_yes_no(user_input_stripped)
        if orc_required is None:
            update.message.reply_text("вќЊ РћС‚РІРµС‚СЊС‚Рµ 'РґР°' РёР»Рё 'РЅРµС‚'.")
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['orc'] = {"enabled": orc_required}
        context.user_data['supplier_stock_processing_current_variant'] = variant
        if not orc_required:
            return _supplier_stock_finish_variant(update, context, data)
        context.user_data['supplier_stock_processing_stage'] = 'orc_prefix'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РїСЂРµС„РёРєСЃ Р°СЂС‚РёРєСѓР»Р° РґР»СЏ С„Р°Р№Р»Р° РћР Рљ (РёР»Рё '-' РµСЃР»Рё РЅРµ РЅСѓР¶РµРЅ). "
            "РџСЂРѕР±РµР»С‹ РІ РєРѕРЅС†Рµ СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ."
        )
        return None

    if stage == 'orc_prefix':
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        if user_input_stripped in ('-', ''):
            variant['orc']['prefix'] = ""
        else:
            variant['orc']['prefix'] = user_input
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'orc_stor'
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РїР°СЂР°РјРµС‚СЂ Stor РґР»СЏ С„Р°Р№Р»Р° РћР Рљ:")
        return None

    if stage == 'orc_stor':
        if not user_input_stripped:
            update.message.reply_text("вќЊ Stor РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['orc']['stor'] = user_input_stripped
        context.user_data['supplier_stock_processing_current_variant'] = variant
        return _supplier_stock_finish_variant(update, context, data)

    update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
    return None

def supplier_stock_start_source_wizard(update, context):
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° РґРѕР±Р°РІР»РµРЅРёСЏ РёСЃС‚РѕС‡РЅРёРєР° РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_source_stage'] = 'name'
    context.user_data['supplier_stock_source_data'] = {}
    context.user_data['supplier_stock_add_source'] = True

    query.edit_message_text(
        "вћ• *РќРѕРІС‹Р№ РёСЃС‚РѕС‡РЅРёРє РѕСЃС‚Р°С‚РєРѕРІ*\n\nР’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РёСЃС‚РѕС‡РЅРёРєР°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_sources')]
        ])
    )

def supplier_stock_start_edit_wizard(update, context, source_id: str):
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РёСЃС‚РѕС‡РЅРёРєР° РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_edit_source'] = True
    context.user_data['supplier_stock_edit_source_stage'] = 'name'
    context.user_data['supplier_stock_edit_source_id'] = source_id

    query.edit_message_text(
        f"вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РёСЃС‚РѕС‡РЅРёРєР°*\n\nРўРµРєСѓС‰РµРµ РёРјСЏ: `{_escape_pattern_text(source.get('name'))}`\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_sources')]
        ])
    )

def supplier_stock_handle_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РґР»СЏ РЅР°СЃС‚СЂРѕРµРє РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    if context.user_data.get('supplier_stock_source_iek_field'):
        return supplier_stock_handle_source_iek_field_input(update, context)
    if context.user_data.get('supplier_stock_resource_field'):
        return supplier_stock_handle_resource_field_input(update, context)
    if context.user_data.get('supplier_stock_resource_add'):
        return supplier_stock_handle_resource_input(update, context)
    if context.user_data.get('supplier_stock_ftp_field'):
        return supplier_stock_handle_ftp_input(update, context)
    if context.user_data.get('supplier_stock_source_field'):
        return supplier_stock_handle_source_field_input(update, context)
    if context.user_data.get('supplier_stock_mail_source_field'):
        return supplier_stock_handle_mail_source_field_input(update, context)
    if context.user_data.get('supplier_stock_processing_field'):
        return supplier_stock_handle_processing_input(update, context)
    if context.user_data.get('supplier_stock_edit'):
        return supplier_stock_handle_edit_input(update, context)
    if context.user_data.get('supplier_stock_processing_add') or context.user_data.get('supplier_stock_processing_edit'):
        return supplier_stock_handle_processing_input(update, context)
    if context.user_data.get('supplier_stock_mail_edit'):
        return supplier_stock_handle_mail_edit_input(update, context)
    if context.user_data.get('supplier_stock_mail_edit_source'):
        return supplier_stock_handle_mail_source_edit_input(update, context)
    if context.user_data.get('supplier_stock_mail_add_source'):
        return supplier_stock_handle_mail_source_input(update, context)
    if context.user_data.get('supplier_stock_edit_source'):
        return supplier_stock_handle_source_edit_input(update, context)
    if context.user_data.get('supplier_stock_add_source'):
        return supplier_stock_handle_source_input(update, context)
    return None

def _supplier_stock_remember_prompt_message(context, query):
    """Р—Р°РїРѕРјРЅРёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ СЃ Р·Р°РїСЂРѕСЃРѕРј РІРІРѕРґР° РїР°СЂР°РјРµС‚СЂР°."""
    if not query or not query.message:
        return
    context.user_data['supplier_stock_prompt_message_id'] = query.message.message_id
    context.user_data['supplier_stock_prompt_chat_id'] = query.message.chat_id

def _supplier_stock_close_prompt_message(context):
    """РЈРґР°Р»РёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ СЃ Р·Р°РїСЂРѕСЃРѕРј РІРІРѕРґР° РїР°СЂР°РјРµС‚СЂР°."""
    message_id = context.user_data.pop('supplier_stock_prompt_message_id', None)
    chat_id = context.user_data.pop('supplier_stock_prompt_chat_id', None)
    if not message_id or not chat_id:
        return
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

def supplier_stock_handle_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ РЅР°СЃС‚СЂРѕРµРє РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    field = context.user_data.get('supplier_stock_edit')
    if not field:
        return None

    message = update.message
    if not message or not message.text:
        debug_logger("вљ пёЏ supplier_stock_handle_edit_input: РїРѕР»СѓС‡РµРЅРѕ РїСѓСЃС‚РѕРµ СЃРѕРѕР±С‰РµРЅРёРµ.")
        return None

    user_input = message.text.strip()
    config = get_supplier_stock_config()

    if field == 'temp_dir':
        if not user_input:
            update.message.reply_text("вќЊ РџСѓС‚СЊ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        config['download']['temp_dir'] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… Р’СЂРµРјРµРЅРЅС‹Р№ РєР°С‚Р°Р»РѕРі РѕР±РЅРѕРІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_download')]
            ])
        )
        return None

    if field == 'schedule_time':
        schedule_times = parse_supplier_stock_schedule_times(user_input)
        if not schedule_times:
            update.message.reply_text(
                "вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РІСЂРµРјРµРЅРё. РСЃРїРѕР»СЊР·СѓР№С‚Рµ HH:MM Рё СЂР°Р·РґРµР»РёС‚РµР»Рё: РїСЂРѕР±РµР», Р·Р°РїСЏС‚Р°СЏ РёР»Рё ;"
            )
            return None
        config['download']['schedule']['time'] = ', '.join(schedule_times)
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… Р’СЂРµРјСЏ СЂР°СЃРїРёСЃР°РЅРёСЏ РѕР±РЅРѕРІР»РµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_schedule')]
            ])
        )
        return None

    if field == 'archive_cleanup_days':
        try:
            cleanup_days = int(user_input)
        except ValueError:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ РґРЅРµР№ (0 вЂ” РѕС‚РєР»СЋС‡РёС‚СЊ).")
            return None
        if cleanup_days < 0:
            update.message.reply_text("вќЊ РџРµСЂРёРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РѕС‚СЂРёС†Р°С‚РµР»СЊРЅС‹Рј.")
            return None
        config["archive_cleanup_days"] = cleanup_days
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        back_callback = context.user_data.pop('supplier_stock_archive_cleanup_back', 'supplier_stock_download')
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… РџРµСЂРёРѕРґ РѕС‡РёСЃС‚РєРё Р°СЂС…РёРІР° РѕР±РЅРѕРІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
            ])
        )
        return None

    if field == 'report_period_days':
        try:
            period_days = int(user_input)
        except ValueError:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ РґРЅРµР№ (РјРёРЅРёРјСѓРј 1).")
            return None
        if period_days < 1:
            update.message.reply_text("вќЊ РџРµСЂРёРѕРґ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ РјРёРЅРёРјСѓРј 1 РґРµРЅСЊ.")
            return None
        config.setdefault("reporting", {})["period_days"] = period_days
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… РџРµСЂРёРѕРґ РѕС‚С‡С‘С‚РѕРІ РѕР±РЅРѕРІР»С‘РЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_supplier_stock')]
            ])
        )
        return None

    if field == 'archive_dir':
        if not user_input:
            update.message.reply_text("вќЊ РџСѓС‚СЊ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        config['download']['archive_dir'] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… РљР°С‚Р°Р»РѕРі Р°СЂС…РёРІР° РѕР±РЅРѕРІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_download')]
            ])
        )
        return None

    return None

def supplier_stock_handle_mail_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РґР»СЏ РѕР±С‰РёС… РЅР°СЃС‚СЂРѕРµРє РїРѕС‡С‚С‹ РѕСЃС‚Р°С‚РєРѕРІ."""
    field = context.user_data.get('supplier_stock_mail_edit')
    if not field:
        return None

    user_input = update.message.text.strip()
    config = get_supplier_stock_config()

    if field == 'temp_dir':
        if not user_input:
            update.message.reply_text("вќЊ РџСѓС‚СЊ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        config["mail"]["temp_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_mail_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… Р’СЂРµРјРµРЅРЅС‹Р№ РєР°С‚Р°Р»РѕРі РѕР±РЅРѕРІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail')]
            ])
        )
        return None

    if field == 'archive_dir':
        if not user_input:
            update.message.reply_text("вќЊ РџСѓС‚СЊ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        config["mail"]["archive_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_mail_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… РљР°С‚Р°Р»РѕРі Р°СЂС…РёРІР° РѕР±РЅРѕРІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail')]
            ])
        )
        return None

    return None

def supplier_stock_start_mail_source_wizard(update, context):
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° РґРѕР±Р°РІР»РµРЅРёСЏ РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№ РїРѕС‡С‚С‹."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_mail_source_stage'] = 'name'
    context.user_data['supplier_stock_mail_source_data'] = {}
    context.user_data['supplier_stock_mail_add_source'] = True

    query.edit_message_text(
        "вћ• *РќРѕРІРѕРµ РїСЂР°РІРёР»Рѕ РІР»РѕР¶РµРЅРёР№*\n\nР’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РїСЂР°РІРёР»Р°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_mail_sources')]
        ])
    )

def supplier_stock_start_mail_edit_wizard(update, context, source_id: str):
    """Р—Р°РїСѓСЃРє РјР°СЃС‚РµСЂР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№ РїРѕС‡С‚С‹."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_mail_edit_source'] = True
    context.user_data['supplier_stock_mail_edit_source_stage'] = 'name'
    context.user_data['supplier_stock_mail_edit_source_id'] = source_id

    query.edit_message_text(
        f"вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РїСЂР°РІРёР»Р°*\n\n"
        f"РўРµРєСѓС‰РµРµ РёРјСЏ: `{_escape_pattern_text(source.get('name'))}`\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='supplier_stock_mail_sources')]
        ])
    )

def supplier_stock_handle_mail_source_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РІ РјР°СЃС‚РµСЂРµ РґРѕР±Р°РІР»РµРЅРёСЏ РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№."""
    stage = context.user_data.get('supplier_stock_mail_source_stage')
    source_data = context.user_data.get('supplier_stock_mail_source_data', {})
    user_input = update.message.text.strip()

    if stage == 'name':
        if not user_input:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        source_data['name'] = user_input
        source_data['id'] = _slugify_supplier_source_id(user_input)
        context.user_data['supplier_stock_mail_source_stage'] = 'sender'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ regex РёР»Рё Р°РґСЂРµСЃ РѕС‚РїСЂР°РІРёС‚РµР»СЏ (РЅР°РїСЂРёРјРµСЂ: sender@example.com) "
            "РёР»Рё '-' С‡С‚РѕР±С‹ РїСЂРёРЅРёРјР°С‚СЊ Р»СЋР±С‹Рµ РїРёСЃСЊРјР°:"
        )
        return None

    if stage == 'sender':
        if user_input not in ('-', ''):
            source_data['sender_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'subject'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ regex РґР»СЏ С‚РµРјС‹ РїРёСЃСЊРјР° РёР»Рё '-' С‡С‚РѕР±С‹ РїСЂРёРЅРёРјР°С‚СЊ Р»СЋР±СѓСЋ С‚РµРјСѓ:"
        )
        return None

    if stage == 'subject':
        if user_input not in ('-', ''):
            source_data['subject_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'mime'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ MIME-С„РёР»СЊС‚СЂ (РЅР°РїСЂРёРјРµСЂ: application/vnd.ms-excel) "
            "РёР»Рё '-' С‡С‚РѕР±С‹ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ application/.*:"
        )
        return None

    if stage == 'mime':
        if user_input not in ('-', ''):
            source_data['mime_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'filename'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ regex РґР»СЏ РёРјРµРЅРё РІР»РѕР¶РµРЅРёСЏ РёР»Рё '-' С‡С‚РѕР±С‹ РїСЂРёРЅРёРјР°С‚СЊ Р»СЋР±С‹Рµ С„Р°Р№Р»С‹:"
        )
        return None

    if stage == 'filename':
        if user_input not in ('-', ''):
            source_data['filename_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'expected'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ РѕР¶РёРґР°РµРјС‹С… РІР»РѕР¶РµРЅРёР№ (РЅР°РїСЂРёРјРµСЂ: 1 РёР»Рё 2):"
        )
        return None

    if stage == 'expected':
        expected = _parse_expected_attachments(user_input)
        if expected is None:
            update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
            return None
        source_data['expected_attachments'] = expected
        context.user_data['supplier_stock_mail_source_stage'] = 'output'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ С€Р°Р±Р»РѕРЅ РёРјРµРЅРё РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р° "
            "(РЅР°РїСЂРёРјРµСЂ: supplier_{index}_orig.xls, РґРѕСЃС‚СѓРїРЅС‹ {index}, {name}):"
        )
        return None

    if stage == 'output':
        if not user_input:
            update.message.reply_text("вќЊ РЁР°Р±Р»РѕРЅ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        source_data['output_template'] = user_input
        source_data.setdefault('enabled', True)
        source_data.setdefault('unpack_archive', False)

        config = get_supplier_stock_config()
        sources = config['mail'].get('sources', [])
        source_data['id'] = _unique_supplier_source_id(source_data.get('id', 'source'), sources)
        sources.append(source_data)
        config['mail']['sources'] = sources
        save_supplier_stock_config(config)

        context.user_data.pop('supplier_stock_mail_add_source', None)
        context.user_data.pop('supplier_stock_mail_source_stage', None)
        context.user_data.pop('supplier_stock_mail_source_data', None)

        update.message.reply_text(
            "вњ… РџСЂР°РІРёР»Рѕ РґРѕР±Р°РІР»РµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return None

    update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
    return None

def supplier_stock_handle_mail_source_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РїСЂРё СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРё РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№."""
    stage = context.user_data.get('supplier_stock_mail_edit_source_stage')
    source_id = context.user_data.get('supplier_stock_mail_edit_source_id')
    user_input = update.message.text.strip()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
        ]))
        return None

    if stage == 'name':
        if user_input and user_input not in ('-',):
            source['name'] = user_input
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'sender'
        current_sender = source.get("sender_pattern") or "-"
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ regex/Р°РґСЂРµСЃ РѕС‚РїСЂР°РІРёС‚РµР»СЏ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_sender}"
        )
        return None

    if stage == 'sender':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('sender_pattern', None)
        elif user_input not in ('-',):
            source['sender_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'subject'
        current_subject = source.get("subject_pattern") or "-"
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ regex РґР»СЏ С‚РµРјС‹ РїРёСЃСЊРјР°, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_subject}"
        )
        return None

    if stage == 'subject':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('subject_pattern', None)
        elif user_input not in ('-',):
            source['subject_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'mime'
        current_mime = source.get("mime_pattern") or "-"
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ MIME-С„РёР»СЊС‚СЂ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_mime}"
        )
        return None

    if stage == 'mime':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('mime_pattern', None)
        elif user_input not in ('-',):
            source['mime_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'filename'
        current_filename = source.get("filename_pattern") or "-"
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ regex РґР»СЏ РёРјРµРЅРё РІР»РѕР¶РµРЅРёСЏ, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_filename}"
        )
        return None

    if stage == 'filename':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('filename_pattern', None)
        elif user_input not in ('-',):
            source['filename_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'expected'
        current_expected = source.get("expected_attachments", 1)
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ РѕР¶РёРґР°РµРјС‹С… РІР»РѕР¶РµРЅРёР№, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_expected}"
        )
        return None

    if stage == 'expected':
        if user_input not in ('-',):
            expected = _parse_expected_attachments(user_input)
            if expected is None:
                update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0 РёР»Рё '-'.")
                return None
            source['expected_attachments'] = expected
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'output'
        current_output = source.get("output_template") or "-"
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ С€Р°Р±Р»РѕРЅ РёРјРµРЅРё РІС‹С…РѕРґРЅРѕРіРѕ С„Р°Р№Р»Р°, '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_output}"
        )
        return None

    if stage == 'output':
        if user_input and user_input not in ('-',):
            source['output_template'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop('supplier_stock_mail_edit_source', None)
        context.user_data.pop('supplier_stock_mail_edit_source_stage', None)
        context.user_data.pop('supplier_stock_mail_edit_source_id', None)

        update.message.reply_text(
            "вњ… РџСЂР°РІРёР»Рѕ РѕР±РЅРѕРІР»РµРЅРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return None

    update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ С€Р°Рі СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
    return None

def supplier_stock_handle_source_field_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РїСЂРё СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРё РѕС‚РґРµР»СЊРЅРѕРіРѕ РїРѕР»СЏ РёСЃС‚РѕС‡РЅРёРєР°."""
    field = context.user_data.get('supplier_stock_source_field')
    source_id = context.user_data.get('supplier_stock_source_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
        ]))
        return None

    if field == 'name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            source['name'] = user_input
    elif field == 'url':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ URL РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            source['url'] = user_input
    elif field == 'discover':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('discover', None)
        else:
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ URL | regex | prefix, '-' РёР»Рё 'none'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
                )
                return None
            source['discover'] = discover
    elif field == 'vars':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('vars', None)
        else:
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ key=value, СЂР°Р·РґРµР»РёС‚РµР»Рё Р·Р°РїСЏС‚Р°СЏ/РЅРѕРІР°СЏ СЃС‚СЂРѕРєР°.")
                return None
            source['vars'] = vars_map
    elif field == 'output_name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ РРјСЏ С„Р°Р№Р»Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            source['output_name'] = user_input
    elif field == 'auth':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('auth', None)
        else:
            if ':' not in user_input:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ login:password РёР»Рё 'none'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                return None
            username, password = user_input.split(':', 1)
            source['auth'] = {'username': username, 'password': password}
    elif field == 'pre_request':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('pre_request', None)
        else:
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ URL | РґР°РЅРЅС‹Рµ, '-' РёР»Рё 'none'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
                )
                return None
            source['pre_request'] = pre_request
    elif field == 'options':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('include_headers', None)
            source.pop('append', None)
        else:
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ СЃРїРёСЃРєРѕРј С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ (headers, append), '-' РёР»Рё 'none'."
                )
                return None
            source.update(options)
    elif field == 'processing_mode':
        if user_input in ('-', ''):
            pass
        else:
            mode = _normalize_supplier_processing_mode(user_input)
            if not mode:
                update.message.reply_text("вќЊ Р”РѕРїСѓСЃС‚РёРјС‹Рµ Р·РЅР°С‡РµРЅРёСЏ: table, iek_json.")
                return None
            source['processing_mode'] = mode
            if mode == "iek_json":
                source.setdefault("iek_json", {})
    elif field == 'upload_subdir':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('upload_subdir', None)
        else:
            source['upload_subdir'] = user_input
    elif field == 'individual_path':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            individual_dir.pop('unc_path', None)
        else:
            individual_dir['unc_path'] = user_input
    elif field == 'individual_login':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            individual_dir.pop('login', None)
        else:
            individual_dir['login'] = user_input
    elif field == 'individual_password':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            individual_dir.pop('password', None)
        else:
            individual_dir['password'] = user_input
    else:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РїРѕР»Рµ РЅР°СЃС‚СЂРѕР№РєРё.")
        return None

    config["download"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_source_field', None)
    context.user_data.pop('supplier_stock_source_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_source_settings|{source_id}')]
        ])
    )
    return None

def supplier_stock_handle_source_iek_field_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РїСЂРё СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРё РїР°СЂР°РјРµС‚СЂРѕРІ IEK JSON."""
    field = context.user_data.get('supplier_stock_source_iek_field')
    source_id = context.user_data.get('supplier_stock_source_iek_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
        ]))
        return None

    iek_settings = source.setdefault("iek_json", {})

    if user_input in ("-", ""):
        config["download"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_source_iek_field', None)
        context.user_data.pop('supplier_stock_source_iek_field_id', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "вњ… РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_source_iek_settings|{source_id}')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
            ])
        )
        return None
    if field == "stores":
        if user_input.lower() in ("none", "РЅРµС‚"):
            iek_settings["stores"] = {}
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ key=uuid С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ/РЅРѕРІСѓСЋ СЃС‚СЂРѕРєСѓ.")
                return None
            iek_settings["stores"] = parsed
    elif field == "msk_stores":
        if user_input.lower() in ("none", "РЅРµС‚"):
            iek_settings["msk_stores"] = []
        else:
            if not user_input:
                update.message.reply_text("вќЊ РЎРїРёСЃРѕРє РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј.")
                return None
            iek_settings["msk_stores"] = [item.strip() for item in re.split(r"[,\n]+", user_input) if item.strip()]
    elif field == "nsk_store":
        if user_input.lower() in ("none", "РЅРµС‚"):
            iek_settings["nsk_store"] = ""
        else:
            if not user_input:
                update.message.reply_text("вќЊ Р—РЅР°С‡РµРЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј.")
                return None
            iek_settings["nsk_store"] = user_input
    elif field == "orc_stores":
        if user_input.lower() in ("none", "РЅРµС‚"):
            iek_settings["orc_stores"] = []
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ key=stor С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ/РЅРѕРІСѓСЋ СЃС‚СЂРѕРєСѓ.")
                return None
            iek_settings["orc_stores"] = [{"key": key, "stor": value} for key, value in parsed.items()]
    elif field == "prefix":
        iek_settings["prefix"] = "" if user_input.lower() in ("none", "РЅРµС‚") else user_input
    elif field == "outputs":
        if user_input.lower() in ("none", "РЅРµС‚"):
            iek_settings["outputs"] = {}
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ orig=..., msk=..., nsk=..., orc=... С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ.")
                return None
            iek_settings["outputs"] = parsed
    else:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РїРѕР»Рµ РЅР°СЃС‚СЂРѕР№РєРё.")
        return None

    source["iek_json"] = iek_settings
    config["download"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_source_iek_field', None)
    context.user_data.pop('supplier_stock_source_iek_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_source_iek_settings|{source_id}')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
        ])
    )
    return None

def supplier_stock_handle_mail_source_field_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РїСЂРё СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРё РѕС‚РґРµР»СЊРЅРѕРіРѕ РїРѕР»СЏ РїСЂР°РІРёР»Р° РІР»РѕР¶РµРЅРёР№."""
    field = context.user_data.get('supplier_stock_mail_source_field')
    source_id = context.user_data.get('supplier_stock_mail_source_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("вќЊ РџСЂР°РІРёР»Рѕ РЅРµ РЅР°Р№РґРµРЅРѕ.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_mail_sources')]
        ]))
        return None

    if field == 'name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            source['name'] = user_input
    elif field == 'sender':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('sender_pattern', None)
        else:
            source['sender_pattern'] = user_input
    elif field == 'subject':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('subject_pattern', None)
        else:
            source['subject_pattern'] = user_input
    elif field == 'mime':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('mime_pattern', None)
        else:
            source['mime_pattern'] = user_input
    elif field == 'filename':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('filename_pattern', None)
        else:
            source['filename_pattern'] = user_input
    elif field == 'expected':
        if user_input in ('-', ''):
            pass
        else:
            expected = _parse_expected_attachments(user_input)
            if expected is None:
                update.message.reply_text("вќЊ Р’РІРµРґРёС‚Рµ С†РµР»РѕРµ С‡РёСЃР»Рѕ Р±РѕР»СЊС€Рµ 0.")
                return None
            source['expected_attachments'] = expected
    elif field == 'output':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ РЁР°Р±Р»РѕРЅ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            source['output_template'] = user_input
    elif field == 'upload_subdir':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('upload_subdir', None)
        else:
            source['upload_subdir'] = user_input
    elif field == 'individual_path':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            individual_dir.pop('unc_path', None)
        else:
            individual_dir['unc_path'] = user_input
    elif field == 'individual_login':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            individual_dir.pop('login', None)
        else:
            individual_dir['login'] = user_input
    elif field == 'individual_password':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            individual_dir.pop('password', None)
        else:
            individual_dir['password'] = user_input
    else:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РїРѕР»Рµ РЅР°СЃС‚СЂРѕР№РєРё.")
        return None

    config["mail"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_mail_source_field', None)
    context.user_data.pop('supplier_stock_mail_source_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_mail_source_settings|{source_id}')]
        ])
    )
    return None


def supplier_stock_handle_resource_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РІ РјР°СЃС‚РµСЂРµ РґРѕР±Р°РІР»РµРЅРёСЏ СЂРµСЃСѓСЂСЃР° РІС‹РіСЂСѓР·РєРё."""
    stage = context.user_data.get('supplier_stock_resource_stage')
    resource_data = context.user_data.get('supplier_stock_resource_data', {})
    user_input = (update.message.text or "").strip()

    if stage == 'name':
        if not user_input:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        resource_data['name'] = user_input
        resource_data['id'] = _slugify_supplier_source_id(user_input)
        context.user_data['supplier_stock_resource_stage'] = 'unc_path'
        context.user_data['supplier_stock_resource_data'] = resource_data
        update.message.reply_text("Р’РІРµРґРёС‚Рµ UNC РїСѓС‚СЊ РєРѕСЂРЅРµРІРѕРіРѕ РєР°С‚Р°Р»РѕРіР°:")
        return None

    if stage == 'unc_path':
        if not user_input:
            update.message.reply_text("вќЊ UNC РїСѓС‚СЊ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        resource_data['unc_path'] = user_input
        context.user_data['supplier_stock_resource_stage'] = 'login'
        context.user_data['supplier_stock_resource_data'] = resource_data
        update.message.reply_text("Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ СЂРµСЃСѓСЂСЃР° (РёР»Рё '-' С‡С‚РѕР±С‹ РїСЂРѕРїСѓСЃС‚РёС‚СЊ):")
        return None

    if stage == 'login':
        if user_input not in ('-', ''):
            resource_data['login'] = user_input
        context.user_data['supplier_stock_resource_stage'] = 'password'
        context.user_data['supplier_stock_resource_data'] = resource_data
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РїР°СЂРѕР»СЊ СЂРµСЃСѓСЂСЃР° (РёР»Рё '-' С‡С‚РѕР±С‹ РїСЂРѕРїСѓСЃС‚РёС‚СЊ):")
        return None

    if stage == 'password':
        if user_input not in ('-', ''):
            resource_data['password'] = user_input
        resource_data.setdefault('enabled', True)
        config = get_supplier_stock_config()
        resources = config.get("resources", [])
        resource_data['id'] = _unique_supplier_source_id(resource_data.get('id', 'resource'), resources)
        resources.append(resource_data)
        config["resources"] = resources
        save_supplier_stock_config(config)

        context.user_data.pop('supplier_stock_resource_add', None)
        context.user_data.pop('supplier_stock_resource_stage', None)
        context.user_data.pop('supplier_stock_resource_data', None)

        update.message.reply_text(
            "вњ… Р РµСЃСѓСЂСЃ РґРѕР±Р°РІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_resources')]
            ])
        )
        return None

    update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
    return None


def supplier_stock_handle_resource_field_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РїСЂРё СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРё СЂРµСЃСѓСЂСЃР° РІС‹РіСЂСѓР·РєРё."""
    field = context.user_data.get('supplier_stock_resource_field')
    resource_id = context.user_data.get('supplier_stock_resource_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not resource_id:
        return None

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        update.message.reply_text("вќЊ Р РµСЃСѓСЂСЃ РЅРµ РЅР°Р№РґРµРЅ.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_resources')]
        ]))
        return None

    if field == 'name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            resource['name'] = user_input
    elif field == 'unc_path':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ UNC РїСѓС‚СЊ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            resource['unc_path'] = user_input
    elif field == 'login':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            resource.pop('login', None)
        else:
            resource['login'] = user_input
    elif field == 'password':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            resource.pop('password', None)
        else:
            resource['password'] = user_input
    else:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РїРѕР»Рµ РЅР°СЃС‚СЂРѕР№РєРё.")
        return None

    config["resources"] = resources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_resource_field', None)
    context.user_data.pop('supplier_stock_resource_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=f'supplier_stock_resource_settings|{resource_id}')]
        ])
    )
    return None


def supplier_stock_handle_ftp_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РґР»СЏ РЅР°СЃС‚СЂРѕРµРє FTP РћР Рљ."""
    field = context.user_data.get('supplier_stock_ftp_field')
    user_input = (update.message.text or "").strip()

    if not field:
        return None

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})

    if field == 'host':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("вќЊ HOST FTP РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        else:
            ftp_settings['host'] = user_input
    elif field == 'login':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            ftp_settings.pop('login', None)
        else:
            ftp_settings['login'] = user_input
    elif field == 'password':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'РЅРµС‚'):
            ftp_settings.pop('password', None)
        else:
            ftp_settings['password'] = user_input
    else:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РїРѕР»Рµ РЅР°СЃС‚СЂРѕР№РєРё.")
        return None

    config["ftp_ork"] = ftp_settings
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_ftp_field', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "вњ… РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_ftp')]
        ])
    )
    return None

def supplier_stock_handle_source_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РІ РјР°СЃС‚РµСЂРµ РґРѕР±Р°РІР»РµРЅРёСЏ РёСЃС‚РѕС‡РЅРёРєР°."""
    stage = context.user_data.get('supplier_stock_source_stage')
    source_data = context.user_data.get('supplier_stock_source_data', {})
    user_input = update.message.text.strip()

    if stage == 'name':
        if not user_input:
            update.message.reply_text("вќЊ РќР°Р·РІР°РЅРёРµ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        source_data['name'] = user_input
        source_data['id'] = _slugify_supplier_source_id(user_input)
        context.user_data['supplier_stock_source_stage'] = 'url'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ URL РґР»СЏ СЃРєР°С‡РёРІР°РЅРёСЏ. "
            "РњРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РїРµСЂРµРјРµРЅРЅС‹Рµ С„РѕСЂРјР°С‚Р° РїРѕРґСЃС‚Р°РЅРѕРІРєРё РІРёРґР° {abc} "
            "РґР»СЏ РґР°Р»СЊРЅРµР№С€РµР№ РїРѕРґРјРµРЅС‹ Р·РЅР°С‡РµРЅРёР№."
        )
        return None

    if stage == 'url':
        if not user_input:
            update.message.reply_text("вќЊ URL РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        source_data['url'] = user_input
        context.user_data['supplier_stock_source_stage'] = 'discover'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р•СЃР»Рё РЅСѓР¶РЅРѕ РёСЃРєР°С‚СЊ СЃСЃС‹Р»РєСѓ РЅР° СЃС‚СЂР°РЅРёС†Рµ, РІРІРµРґРёС‚Рµ URL, regex Рё РїСЂРµС„РёРєСЃ С‡РµСЂРµР· '|'.\n"
            "РџСЂРёРјРµСЂ: http://site/page | ostatki_msk_ot_[^\"']*\\.xls | http://site/f/\n"
            "Р’РІРµРґРёС‚Рµ '-' РµСЃР»Рё РЅРµ РЅСѓР¶РЅРѕ:"
        )
        return None

    if stage == 'discover':
        if user_input not in ('-', ''):
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ URL | regex | prefix (РїСЂРµС„РёРєСЃ РјРѕР¶РЅРѕ РѕСЃС‚Р°РІРёС‚СЊ РїСѓСЃС‚С‹Рј)."
                )
                return None
            source_data['discover'] = discover

        context.user_data['supplier_stock_source_stage'] = 'vars'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ СЂР°РЅРµРµ СѓРєР°Р·Р°РЅРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ РїРѕРґСЃС‚Р°РЅРѕРІРєРё РІ С„РѕСЂРјР°С‚Рµ key=value С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ "
            "(РїСЂРёРјРµСЂ: abc=DKC_Maga_Del_1200_$(date '%d.%m.%Y').zip). "
            "Р’РІРµРґРёС‚Рµ '-' РµСЃР»Рё РЅРµ РЅСѓР¶РЅРѕ:"
        )
        return None

    if stage == 'vars':
        if user_input not in ('-', ''):
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ key=value, СЂР°Р·РґРµР»РёС‚РµР»Рё Р·Р°РїСЏС‚Р°СЏ/РЅРѕРІР°СЏ СЃС‚СЂРѕРєР°.")
                return None
            source_data['vars'] = vars_map

        context.user_data['supplier_stock_source_stage'] = 'output_name'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РёРјСЏ С„Р°Р№Р»Р° РЅР°Р·РЅР°С‡РµРЅРёСЏ (РЅР°РїСЂРёРјРµСЂ: dkc_orig.zip):"
        )
        return None

    if stage == 'output_name':
        if not user_input:
            update.message.reply_text("вќЊ РРјСЏ С„Р°Р№Р»Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return None
        source_data['output_name'] = user_input
        context.user_data['supplier_stock_source_stage'] = 'auth'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ Рё РїР°СЂРѕР»СЊ С‡РµСЂРµР· РґРІРѕРµС‚РѕС‡РёРµ (login:password) "
            "РёР»Рё '-' С‡С‚РѕР±С‹ РїСЂРѕРїСѓСЃС‚РёС‚СЊ Рё СЃРѕС…СЂР°РЅРёС‚СЊ:"
        )
        return None

    if stage == 'auth':
        if user_input not in ('-', 'РЅРµС‚', 'РќРµС‚', 'none', 'None'):
            if ':' not in user_input:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ login:password РёР»Рё '-'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                return None
            username, password = user_input.split(':', 1)
            source_data['auth'] = {'username': username, 'password': password}

        context.user_data['supplier_stock_source_stage'] = 'pre_request'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р•СЃР»Рё РЅСѓР¶РµРЅ РїСЂРµРґРІР°СЂРёС‚РµР»СЊРЅС‹Р№ POST-Р·Р°РїСЂРѕСЃ РґР»СЏ Р°РІС‚РѕСЂРёР·Р°С†РёРё, "
            "РІРІРµРґРёС‚Рµ URL Рё РґР°РЅРЅС‹Рµ С‡РµСЂРµР· '|'.\n"
            "РџСЂРёРјРµСЂ: http://www.owen.ru/dealers | login=...&password=...&iTask=login\n"
            "Р’РІРµРґРёС‚Рµ '-' РµСЃР»Рё РЅРµ РЅСѓР¶РЅРѕ:"
        )
        return None

    if stage == 'pre_request':
        if user_input not in ('-', ''):
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ URL | РґР°РЅРЅС‹Рµ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР° РёР»Рё РІРІРµРґРёС‚Рµ '-'."
                )
                return None
            source_data['pre_request'] = pre_request

        context.user_data['supplier_stock_source_stage'] = 'options'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РїР°СЂР°РјРµС‚СЂС‹ СЃРѕС…СЂР°РЅРµРЅРёСЏ: headers (СЃ Р·Р°РіРѕР»РѕРІРєР°РјРё), append (РґРѕРїРёСЃС‹РІР°С‚СЊ).\n"
            "РџСЂРёРјРµСЂ: headers, append\n"
            "Р’РІРµРґРёС‚Рµ '-' РµСЃР»Рё РЅРµ РЅСѓР¶РЅРѕ:"
        )
        return None

    if stage == 'options':
        if user_input not in ('-', ''):
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ СЃРїРёСЃРєРѕРј С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ (headers, append)."
                )
                return None
            source_data.update(options)

        source_data.setdefault('method', 'http')
        source_data.setdefault('enabled', True)
        source_data.setdefault('unpack_archive', False)

        config = get_supplier_stock_config()
        sources = config['download'].get('sources', [])
        source_data['id'] = _unique_supplier_source_id(source_data.get('id', 'source'), sources)
        sources.append(source_data)
        config['download']['sources'] = sources
        save_supplier_stock_config(config)

        context.user_data.pop('supplier_stock_add_source', None)
        context.user_data.pop('supplier_stock_source_stage', None)
        context.user_data.pop('supplier_stock_source_data', None)

        update.message.reply_text(
            "вњ… РСЃС‚РѕС‡РЅРёРє РґРѕР±Р°РІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return None

    update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
    return None

def supplier_stock_handle_source_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚РєР° РІРІРѕРґР° РїСЂРё СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРё РёСЃС‚РѕС‡РЅРёРєР° РѕСЃС‚Р°С‚РєРѕРІ."""
    stage = context.user_data.get('supplier_stock_edit_source_stage')
    source_id = context.user_data.get('supplier_stock_edit_source_id')
    user_input = update.message.text.strip()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("вќЊ РСЃС‚РѕС‡РЅРёРє РЅРµ РЅР°Р№РґРµРЅ.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
        ]))
        return None

    if stage == 'name':
        if user_input and user_input not in ('-',):
            source['name'] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data['supplier_stock_edit_source_stage'] = 'url'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ URL (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ). "
            "РњРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РїРµСЂРµРјРµРЅРЅС‹Рµ С„РѕСЂРјР°С‚Р° РїРѕРґСЃС‚Р°РЅРѕРІРєРё РІРёРґР° {abc} "
            "РґР»СЏ РґР°Р»СЊРЅРµР№С€РµР№ РїРѕРґРјРµРЅС‹ Р·РЅР°С‡РµРЅРёР№:\n"
            f"{source.get('url')}"
        )
        return None

    if stage == 'url':
        if user_input and user_input not in ('-',):
            source['url'] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data['supplier_stock_edit_source_stage'] = 'discover'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РїР°СЂР°РјРµС‚СЂС‹ РїРѕРёСЃРєР° СЃСЃС‹Р»РєРё РЅР° СЃС‚СЂР°РЅРёС†Рµ РІ С„РѕСЂРјР°С‚Рµ URL | regex | prefix, "
            "'-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            "РџСЂРёРјРµСЂ: http://site/page | ostatki_msk_ot_[^\"']*\\.xls | http://site/f/"
        )
        return None

    if stage == 'discover':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('discover', None)
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        elif user_input not in ('-',):
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ URL | regex | prefix, '-' РёР»Рё 'none'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
                )
                return None
            source['discover'] = discover
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)

        context.user_data['supplier_stock_edit_source_stage'] = 'vars'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ СЂР°РЅРµРµ СѓРєР°Р·Р°РЅРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ РїРѕРґСЃС‚Р°РЅРѕРІРєРё РІ С„РѕСЂРјР°С‚Рµ key=value С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ "
            "(РїСЂРёРјРµСЂ: abc=DKC_Maga_Del_1200_$(date '%d.%m.%Y').zip). "
            "'-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:"
        )
        return None

    if stage == 'vars':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('vars', None)
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        elif user_input not in ('-',):
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ key=value, СЂР°Р·РґРµР»РёС‚РµР»Рё Р·Р°РїСЏС‚Р°СЏ/РЅРѕРІР°СЏ СЃС‚СЂРѕРєР°.")
                return None
            source['vars'] = vars_map
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)

        context.user_data['supplier_stock_edit_source_stage'] = 'output_name'
        update.message.reply_text(
            f"РўРµРєСѓС‰РёР№ С„Р°Р№Р» РЅР°Р·РЅР°С‡РµРЅРёСЏ: {source.get('output_name')}\n"
            "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ С„Р°Р№Р»Р° РЅР°Р·РЅР°С‡РµРЅРёСЏ (РёР»Рё '-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ):"
        )
        return None

    if stage == 'output_name':
        if user_input and user_input not in ('-',):
            source['output_name'] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data['supplier_stock_edit_source_stage'] = 'auth'
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ Р»РѕРіРёРЅ Рё РїР°СЂРѕР»СЊ С‡РµСЂРµР· РґРІРѕРµС‚РѕС‡РёРµ (login:password), "
            "'-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ:"
        )
        return None

    if stage == 'auth':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('auth', None)
        elif user_input not in ('-',):
            if ':' not in user_input:
                update.message.reply_text("вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ login:password, '-' РёР»Рё 'none'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                return None
            username, password = user_input.split(':', 1)
            source['auth'] = {'username': username, 'password': password}

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_edit_source_stage'] = 'pre_request'
        current_pre = source.get("pre_request") or {}
        current_pre_url = current_pre.get("url", "-")
        current_pre_data = current_pre.get("data", "-")
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РїСЂРµРґРІР°СЂРёС‚РµР»СЊРЅС‹Р№ POST-Р·Р°РїСЂРѕСЃ РґР»СЏ Р°РІС‚РѕСЂРёР·Р°С†РёРё РІ С„РѕСЂРјР°С‚Рµ URL | РґР°РЅРЅС‹Рµ, "
            "'-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_pre_url} | {current_pre_data}"
        )
        return None

    if stage == 'pre_request':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('pre_request', None)
        elif user_input not in ('-',):
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ URL | РґР°РЅРЅС‹Рµ, '-' РёР»Рё 'none'. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
                )
                return None
            source['pre_request'] = pre_request

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data['supplier_stock_edit_source_stage'] = 'options'
        current_options = []
        if source.get("include_headers"):
            current_options.append("headers")
        if source.get("append"):
            current_options.append("append")
        current_label = ", ".join(current_options) if current_options else "-"
        update.message.reply_text(
            "Р’РІРµРґРёС‚Рµ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РїР°СЂР°РјРµС‚СЂС‹ СЃРѕС…СЂР°РЅРµРЅРёСЏ: headers (СЃ Р·Р°РіРѕР»РѕРІРєР°РјРё), append (РґРѕРїРёСЃС‹РІР°С‚СЊ). "
            "'-' С‡С‚РѕР±С‹ РѕСЃС‚Р°РІРёС‚СЊ С‚РµРєСѓС‰РµРµ РёР»Рё 'none' С‡С‚РѕР±С‹ РѕС‡РёСЃС‚РёС‚СЊ.\n"
            f"РўРµРєСѓС‰РµРµ Р·РЅР°С‡РµРЅРёРµ: {current_label}"
        )
        return None

    if stage == 'options':
        if user_input.lower() in ('none', 'РЅРµС‚'):
            source.pop('include_headers', None)
            source.pop('append', None)
        elif user_input not in ('-',):
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "вќЊ Р¤РѕСЂРјР°С‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ СЃРїРёСЃРєРѕРј С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ (headers, append), '-' РёР»Рё 'none'."
                )
                return None
            source.update(options)

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop('supplier_stock_edit_source', None)
        context.user_data.pop('supplier_stock_edit_source_stage', None)
        context.user_data.pop('supplier_stock_edit_source_id', None)

        update.message.reply_text(
            "вњ… РСЃС‚РѕС‡РЅРёРє РѕР±РЅРѕРІР»РµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='supplier_stock_sources')]
            ])
        )
        return None

    update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ С€Р°Рі СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
    return None

def _slugify_supplier_source_id(value: str) -> str:
    raw = re.sub(r'[^a-zA-Z0-9]+', '_', value.strip().lower())
    return raw.strip('_') or 'source'

def _unique_supplier_source_id(source_id: str, sources: list[dict]) -> str:
    existing = {str(item.get('id')) for item in sources if item.get('id')}
    if source_id not in existing:
        return source_id
    index = 2
    while f"{source_id}_{index}" in existing:
        index += 1
    return f"{source_id}_{index}"

def _parse_yes_no(value: str) -> bool | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in ('РґР°', 'yes', 'y', 'true', '1'):
        return True
    if lowered in ('РЅРµС‚', 'no', 'n', 'false', '0'):
        return False
    return None

def _normalize_supplier_processing_mode(value: str) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in ("table", "С‚Р°Р±Р»РёС‡РЅС‹Р№", "С‚Р°Р±Р»РёС†Р°"):
        return "table"
    if lowered in ("iek_json", "iek", "json"):
        return "iek_json"
    return None

def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None

def _save_supplier_stock_processing_rule(
    context,
    data: dict,
    edit_id: str | None = None,
    keep_context: bool = False,
) -> None:
    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    if edit_id:
        updated = False
        for index, rule in enumerate(rules):
            if str(rule.get("id")) == str(edit_id):
                data['id'] = edit_id
                data.setdefault('enabled', rule.get('enabled', True))
                data.setdefault('active', rule.get('active', False))
                rules[index] = data
                updated = True
                break
        if not updated:
            data['id'] = edit_id
            data.setdefault('enabled', True)
            data.setdefault('active', False)
            rules.append(data)
    else:
        data.setdefault('enabled', True)
        data.setdefault('active', False)
        data['id'] = _unique_supplier_source_id(data.get('id', 'rule'), rules)
        rules.append(data)
    config.setdefault("processing", {})["rules"] = rules
    save_supplier_stock_config(config)
    if not keep_context:
        context.user_data.pop('supplier_stock_processing_add', None)
        context.user_data.pop('supplier_stock_processing_edit', None)
        context.user_data.pop('supplier_stock_processing_stage', None)
        context.user_data.pop('supplier_stock_processing_data', None)
        context.user_data.pop('supplier_stock_processing_edit_id', None)
        context.user_data.pop('supplier_stock_processing_variant_index', None)
        context.user_data.pop('supplier_stock_processing_data_columns_expected', None)
        context.user_data.pop('supplier_stock_processing_data_columns', None)
        context.user_data.pop('supplier_stock_processing_output_names_expected', None)
        context.user_data.pop('supplier_stock_processing_output_names', None)
        context.user_data.pop('supplier_stock_processing_current_variant', None)

def _supplier_stock_finish_variant(update, context, data: dict):
    variant = context.user_data.get('supplier_stock_processing_current_variant', {})
    data.setdefault('variants', []).append(variant)
    total = data.get('variants_count', 1)
    current_index = context.user_data.get('supplier_stock_processing_variant_index', 0) + 1
    if current_index < total:
        context.user_data['supplier_stock_processing_variant_index'] = current_index
        context.user_data['supplier_stock_processing_stage'] = 'variant_article_col'
        context.user_data.pop('supplier_stock_processing_data_columns_expected', None)
        context.user_data.pop('supplier_stock_processing_data_columns', None)
        context.user_data.pop('supplier_stock_processing_output_names_expected', None)
        context.user_data.pop('supplier_stock_processing_output_names', None)
        context.user_data.pop('supplier_stock_processing_current_variant', None)
        update.message.reply_text(
            f"РќР°СЃС‚СЂРѕР№РєР° РІР°СЂРёР°РЅС‚Р° {current_index + 1} РёР· {total}.\n"
            "Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ РєРѕР»РѕРЅРєРё СЃ Р°СЂС‚РёРєСѓР»РѕРј:"
        )
        return None

    edit_id = data.get("id") if context.user_data.get('supplier_stock_processing_edit') else None
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
    back_callback = context.user_data.get('supplier_stock_processing_back', 'supplier_stock_processing')
    update.message.reply_text(
        "вњ… РџСЂР°РІРёР»Рѕ РѕР±СЂР°Р±РѕС‚РєРё СЃРѕС…СЂР°РЅРµРЅРѕ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)]
        ])
    )
    return None

def _parse_supplier_vars(raw_value: str) -> dict | None:
    if not raw_value:
        return {}
    parts = re.split(r'[,\n]+', raw_value)
    result = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '=' not in part:
            return None
        key, value = part.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key:
            return None
        result[key] = value
    return result

def _parse_supplier_pre_request(raw_value: str) -> dict | None:
    if not raw_value:
        return None
    if '|' in raw_value:
        url, data = raw_value.split('|', 1)
    elif '\n' in raw_value:
        url, data = raw_value.split('\n', 1)
    else:
        return None
    url = url.strip()
    data = data.strip()
    if not url:
        return None
    if data in ('-', ''):
        data = ''
    return {"url": url, "data": data}

def _parse_supplier_discover(raw_value: str) -> dict | None:
    if not raw_value:
        return None
    parts = [part.strip() for part in raw_value.split('|')]
    if len(parts) < 2:
        return None
    url = parts[0]
    pattern = parts[1]
    prefix = parts[2] if len(parts) > 2 else ''
    if not url or not pattern:
        return None
    return {"url": url, "pattern": pattern, "prefix": prefix}

def _parse_supplier_options(raw_value: str) -> dict | None:
    if not raw_value:
        return None
    parts = [part.strip().lower() for part in re.split(r"[,\n]+", raw_value) if part.strip()]
    if not parts:
        return None
    options = {}
    for part in parts:
        if part in ("headers", "header"):
            options["include_headers"] = True
        elif part in ("append", "РґРѕРїРёСЃР°С‚СЊ"):
            options["append"] = True
        else:
            return None
    return options

def _parse_expected_attachments(raw_value: str) -> int | None:
    if not raw_value:
        return None
    try:
        value = int(raw_value)
    except ValueError:
        return None
    return value if value > 0 else None

def _enable_all_extensions_settings(query):
    enabled = 0
    for ext_id in extension_manager.get_extensions_status():
        success, _ = extension_manager.enable_extension(ext_id)
        if success:
            enabled += 1
    query.answer(f"вњ… Р’РєР»СЋС‡РµРЅРѕ {enabled} СЂР°СЃС€РёСЂРµРЅРёР№")

def _disable_all_extensions_settings(query):
    disabled = 0
    for ext_id in extension_manager.get_extensions_status():
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled += 1
    query.answer(f"вњ… РћС‚РєР»СЋС‡РµРЅРѕ {disabled} СЂР°СЃС€РёСЂРµРЅРёР№")

def show_db_patterns_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Р‘Р”"""
    context.user_data['patterns_filter'] = 'db'
    context.user_data['patterns_back'] = 'settings_ext_backup_db'
    context.user_data['patterns_add'] = 'add_pattern'
    context.user_data['patterns_title'] = "рџ—ѓпёЏ *РџР°С‚С‚РµСЂРЅС‹ Р±СЌРєР°РїРѕРІ Р‘Р”*"
    view_patterns_handler(update, context)

def show_proxmox_patterns_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Proxmox"""
    context.user_data['patterns_filter'] = 'proxmox'
    context.user_data['patterns_back'] = 'settings_ext_backup_proxmox'
    context.user_data['patterns_add'] = 'add_proxmox_pattern'
    context.user_data['patterns_title'] = "рџ–ҐпёЏ *РџР°С‚С‚РµСЂРЅС‹ Р±СЌРєР°РїРѕРІ Proxmox*"
    view_patterns_handler(update, context)

def show_zfs_patterns_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ ZFS"""
    context.user_data['patterns_filter'] = 'zfs'
    context.user_data['patterns_back'] = 'settings_zfs'
    context.user_data['patterns_add'] = 'add_zfs_pattern'
    context.user_data['patterns_title'] = "рџ§Љ *РџР°С‚С‚РµСЂРЅС‹ ZFS*"
    view_patterns_handler(update, context)

def show_mail_patterns_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹"""
    context.user_data['patterns_filter'] = 'mail'
    context.user_data['patterns_back'] = 'settings_ext_backup_mail'
    context.user_data['patterns_add'] = 'add_mail_pattern'
    context.user_data['patterns_title'] = "рџ“¬ *РџР°С‚С‚РµСЂРЅС‹ Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹*"
    view_patterns_handler(update, context)

def show_stock_load_patterns_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РїР°С‚С‚РµСЂРЅС‹ РґР»СЏ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ."""
    context.user_data['patterns_filter'] = 'stock_load'
    context.user_data['patterns_back'] = 'settings_ext_stock_load'
    context.user_data['patterns_add'] = 'add_stock_pattern'
    context.user_data['patterns_title'] = "рџ“¦ *РџР°С‚С‚РµСЂРЅС‹ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ*"
    view_patterns_handler(update, context)

def show_backup_proxmox_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р±СЌРєР°РїРѕРІ Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    message = "рџ–ҐпёЏ *Р‘СЌРєР°РїС‹ Proxmox*\n\n"
    if not proxmox_hosts:
        message += "вќЊ РҐРѕСЃС‚С‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹.\n\n"
    else:
        message += f"РҐРѕСЃС‚РѕРІ РІ СЃРїРёСЃРєРµ: {len(proxmox_hosts)}\n\n"

    message += "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"

    keyboard = [
        [InlineKeyboardButton("рџ“‹ РЎРїРёСЃРѕРє С…РѕСЃС‚РѕРІ", callback_data='settings_proxmox_list')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ С…РѕСЃС‚", callback_data='settings_proxmox_add')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_ext_backup_proxmox'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_proxmox_hosts_list(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє С…РѕСЃС‚РѕРІ Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    message = "рџ“‹ *РҐРѕСЃС‚С‹ Proxmox*\n\n"
    if not proxmox_hosts:
        message += "вќЊ РҐРѕСЃС‚С‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        for host_name in sorted(proxmox_hosts.keys()):
            host_value = proxmox_hosts.get(host_name)
            enabled = True
            if isinstance(host_value, dict):
                enabled = host_value.get('enabled', True)
            status_icon = "рџџў" if enabled else "рџ”ґ"
            message += f"{status_icon} `{host_name}`\n"

    keyboard = []
    for host_name in sorted(proxmox_hosts.keys()):
        host_value = proxmox_hosts.get(host_name)
        enabled = True
        if isinstance(host_value, dict):
            enabled = host_value.get('enabled', True)
        toggle_text = "в›”пёЏ РћС‚РєР»СЋС‡РёС‚СЊ" if enabled else "вњ… Р’РєР»СЋС‡РёС‚СЊ"
        keyboard.append([
            InlineKeyboardButton(
                f"вњЏпёЏ {host_name}",
                callback_data=f"settings_proxmox_edit_{host_name}"
            ),
            InlineKeyboardButton(
                f"рџ—‘пёЏ {host_name}",
                callback_data=f"settings_proxmox_delete_{host_name}"
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {host_name}",
                callback_data=f"settings_proxmox_toggle_{host_name}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_proxmox_host_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ С…РѕСЃС‚ Proxmox"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_proxmox_host'] = True

    query.edit_message_text(
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ Proxmox С…РѕСЃС‚Р°*\n\n"
        "Р’РІРµРґРёС‚Рµ РёРјСЏ С…РѕСЃС‚Р° (РєР°Рє РІ РїРёСЃСЊРјР°С… Р±СЌРєР°РїРѕРІ):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def delete_proxmox_host(update, context, host_name):
    """РЈРґР°Р»РёС‚СЊ С…РѕСЃС‚ Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "вќЊ РҐРѕСЃС‚ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    proxmox_hosts.pop(host_name, None)
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    query.edit_message_text(
        f"вњ… РҐРѕСЃС‚ `{host_name}` СѓРґР°Р»С‘РЅ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def handle_proxmox_host_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґРѕР±Р°РІР»РµРЅРёСЏ С…РѕСЃС‚Р° Proxmox"""
    if 'adding_proxmox_host' not in context.user_data:
        return

    host_name = update.message.text.strip()
    if not host_name:
        update.message.reply_text("вќЊ РРјСЏ С…РѕСЃС‚Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name in proxmox_hosts:
        update.message.reply_text("вќЊ РўР°РєРѕР№ С…РѕСЃС‚ СѓР¶Рµ РµСЃС‚СЊ. Р’РІРµРґРёС‚Рµ РґСЂСѓРіРѕР№:")
        return

    proxmox_hosts[host_name] = {'enabled': True}
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    update.message.reply_text(
        f"вњ… РҐРѕСЃС‚ `{host_name}` РґРѕР±Р°РІР»РµРЅ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

    context.user_data.pop('adding_proxmox_host', None)

def edit_proxmox_host_handler(update, context, host_name):
    """РќР°С‡Р°С‚СЊ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ С…РѕСЃС‚Р° Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "вќЊ РҐРѕСЃС‚ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    context.user_data['editing_proxmox_host'] = True
    context.user_data['editing_proxmox_host_name'] = host_name

    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ С…РѕСЃС‚Р° Proxmox*\n\n"
        f"РўРµРєСѓС‰РёР№ С…РѕСЃС‚: `{host_name}`\n\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ С…РѕСЃС‚Р°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def handle_proxmox_host_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ С…РѕСЃС‚Р° Proxmox"""
    if 'editing_proxmox_host' not in context.user_data:
        return

    new_host_name = update.message.text.strip()
    if not new_host_name:
        update.message.reply_text("вќЊ РРјСЏ С…РѕСЃС‚Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    old_host_name = context.user_data.get('editing_proxmox_host_name')
    if not old_host_name or old_host_name not in proxmox_hosts:
        update.message.reply_text("вќЊ РҐРѕСЃС‚ РЅРµ РЅР°Р№РґРµРЅ.")
        context.user_data.pop('editing_proxmox_host', None)
        context.user_data.pop('editing_proxmox_host_name', None)
        return

    if new_host_name in proxmox_hosts and new_host_name != old_host_name:
        update.message.reply_text("вќЊ РўР°РєРѕР№ С…РѕСЃС‚ СѓР¶Рµ РµСЃС‚СЊ. Р’РІРµРґРёС‚Рµ РґСЂСѓРіРѕР№:")
        return

    host_value = proxmox_hosts.pop(old_host_name, None)
    if not isinstance(host_value, dict):
        host_value = {'enabled': True}
    proxmox_hosts[new_host_name] = host_value
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    update.message.reply_text(
        f"вњ… РҐРѕСЃС‚ РѕР±РЅРѕРІР»С‘РЅ: `{new_host_name}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_proxmox_host', None)
    context.user_data.pop('editing_proxmox_host_name', None)

def toggle_proxmox_host(update, context, host_name):
    """Р’РєР»СЋС‡РёС‚СЊ/РѕС‚РєР»СЋС‡РёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі С…РѕСЃС‚Р° Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "вќЊ РҐРѕСЃС‚ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    host_value = proxmox_hosts.get(host_name)
    if isinstance(host_value, dict):
        enabled = host_value.get('enabled', True)
    else:
        enabled = True
        host_value = {'enabled': True}

    host_value['enabled'] = not enabled
    proxmox_hosts[host_name] = host_value
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    status_text = "РІРєР»СЋС‡РµРЅ" if host_value['enabled'] else "РѕС‚РєР»СЋС‡РµРЅ"
    query.edit_message_text(
        f"вњ… РњРѕРЅРёС‚РѕСЂРёРЅРі С…РѕСЃС‚Р° `{host_name}` {status_text}.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def show_zfs_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё ZFS"""
    query = update.callback_query
    query.answer()

    show_zfs_main_menu(update, context)

def show_zfs_main_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РјРµРЅСЋ ZFS РёР· РіР»Р°РІРЅРѕРіРѕ РјРµРЅСЋ"""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("рџ“‹ РҐРѕСЃС‚С‹", callback_data='settings_zfs_list')],
        [InlineKeyboardButton("рџ”Ќ РџР°С‚С‚РµСЂРЅС‹", callback_data='settings_patterns_zfs')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        "рџ§Љ *РњРѕРЅРёС‚РѕСЂРёРЅРі ZFS*\n\nР’С‹Р±РµСЂРёС‚Рµ СЂР°Р·РґРµР»:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_zfs_status_summary(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РїРѕСЃР»РµРґРЅРёРµ СЃС‚Р°С‚СѓСЃС‹ ZFS РјР°СЃСЃРёРІРѕРІ"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    allowed_servers = {
        name
        for name, server_value in zfs_servers.items()
        if not isinstance(server_value, dict) or server_value.get('enabled', True)
    }

    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path:
        query.edit_message_text(
            "рџ§Љ *ZFS СЃС‚Р°С‚СѓСЃС‹*\n\nвќЊ Р‘Р°Р·Р° Р±СЌРєР°РїРѕРІ РЅРµ РЅР°СЃС‚СЂРѕРµРЅР°.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT s.server_name, s.pool_name, s.pool_state, s.received_at
            FROM zfs_pool_status s
            JOIN (
                SELECT server_name, pool_name, MAX(received_at) AS last_seen
                FROM zfs_pool_status
                GROUP BY server_name, pool_name
            ) latest
            ON s.server_name = latest.server_name
            AND s.pool_name = latest.pool_name
            AND s.received_at = latest.last_seen
            ORDER BY s.server_name, s.pool_name
            """
        )
        rows = cursor.fetchall()
    except Exception as exc:
        if "no such table: zfs_pool_status" in str(exc):
            query.edit_message_text(
                "рџ§Љ *ZFS СЃС‚Р°С‚СѓСЃС‹*\n\nвќЊ РўР°Р±Р»РёС†Р° ZFS РµС‰С‘ РЅРµ СЃРѕР·РґР°РЅР°.\n"
                "Р”РѕР¶РґРёС‚РµСЃСЊ РїРµСЂРІРѕРіРѕ РїРёСЃСЊРјР° РёР»Рё РїРµСЂРµР·Р°РїСѓСЃС‚РёС‚Рµ РјРѕРЅРёС‚РѕСЂРёРЅРі.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                    [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
                ])
            )
            conn.close()
            return
        raise
    finally:
        conn.close()

    if allowed_servers:
        rows = [row for row in rows if row[0] in allowed_servers]
    else:
        rows = []

    if not rows:
        message = "рџ“Љ *ZFS СЃС‚Р°С‚СѓСЃС‹*\n\nвќЊ Р”Р°РЅРЅС‹С… РЅРµС‚."
    else:
        def _md(value: object) -> str:
            return escape_markdown(str(value or ""), version=1)

        message = "рџ“Љ *ZFS СЃС‚Р°С‚СѓСЃС‹ (РїРѕСЃР»РµРґРЅРёРµ)*\n\n"
        current_server = None
        for server_name, pool_name, pool_state, received_at in rows:
            if server_name != current_server:
                if current_server is not None:
                    message += "\n"
                message += f"*{_md(server_name)}*\n"
                current_server = server_name
            message += (
                f"вЂў {_md(pool_name)}: `{_md(pool_state)}` ({_md(received_at)})\n"
            )

    keyboard = [
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_zfs_servers_list(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє ZFS СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    message = "рџ“‹ *ZFS СЃРµСЂРІРµСЂС‹*\n\n"
    if not zfs_servers:
        message += "вќЊ РЎРµСЂРІРµСЂС‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        for server_name in sorted(zfs_servers.keys()):
            server_value = zfs_servers.get(server_name, {})
            enabled = True
            if isinstance(server_value, dict):
                enabled = server_value.get('enabled', True)
            status_icon = "рџџў" if enabled else "рџ”ґ"
            message += f"{status_icon} `{server_name}`\n"

    keyboard = []
    for server_name in sorted(zfs_servers.keys()):
        server_value = zfs_servers.get(server_name, {})
        enabled = True
        if isinstance(server_value, dict):
            enabled = server_value.get('enabled', True)
        toggle_text = "в›”пёЏ РћС‚РєР»СЋС‡РёС‚СЊ" if enabled else "вњ… Р’РєР»СЋС‡РёС‚СЊ"
        keyboard.append([
            InlineKeyboardButton(
                f"вњЏпёЏ {server_name}",
                callback_data=f"settings_zfs_edit_name_{server_name}"
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"рџ—‘пёЏ {server_name}",
                callback_data=f"settings_zfs_delete_{server_name}"
            ),
            InlineKeyboardButton(
                f"{toggle_text} {server_name}",
                callback_data=f"settings_zfs_toggle_{server_name}"
            ),
        ])

    keyboard.append([
        InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ", callback_data='settings_zfs_add')
    ])

    keyboard.append([
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_zfs_server_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ ZFS СЃРµСЂРІРµСЂ"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_zfs_server'] = True
    context.user_data['zfs_server_stage'] = 'name'

    query.edit_message_text(
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ ZFS СЃРµСЂРІРµСЂР°*\n\n"
        "Р’РІРµРґРёС‚Рµ РёРјСЏ СЃРµСЂРІРµСЂР° (РєР°Рє РїСЂРёС…РѕРґРёС‚ РІ С‚РµРјРµ РїРёСЃСЊРјР°):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_zfs'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def delete_zfs_server(update, context, server_name):
    """РЈРґР°Р»РёС‚СЊ ZFS СЃРµСЂРІРµСЂ"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    if server_name not in zfs_servers:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    zfs_servers.pop(server_name, None)
    settings_manager.set_setting('ZFS_SERVERS', zfs_servers)
    _delete_zfs_server_statuses(server_name)

    query.edit_message_text(
        f"вњ… РЎРµСЂРІРµСЂ `{server_name}` СѓРґР°Р»С‘РЅ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def handle_zfs_server_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґРѕР±Р°РІР»РµРЅРёСЏ ZFS СЃРµСЂРІРµСЂР°"""
    if 'adding_zfs_server' not in context.user_data:
        return

    user_input = update.message.text.strip()
    stage = context.user_data.get('zfs_server_stage', 'name')

    if stage == 'name':
        if not user_input:
            update.message.reply_text("вќЊ РРјСЏ СЃРµСЂРІРµСЂР° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        if user_input in zfs_servers:
            update.message.reply_text("вќЊ РўР°РєРѕР№ СЃРµСЂРІРµСЂ СѓР¶Рµ РµСЃС‚СЊ. Р’РІРµРґРёС‚Рµ РґСЂСѓРіРѕР№:")
            return

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        zfs_servers[user_input] = {
            'enabled': True,
        }
        settings_manager.set_setting('ZFS_SERVERS', zfs_servers)

        update.message.reply_text(
            "вњ… РЎРµСЂРІРµСЂ РґРѕР±Р°РІР»РµРЅ.\n"
            f"РРјСЏ: `{user_input}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

        context.user_data.pop('adding_zfs_server', None)
        context.user_data.pop('zfs_server_stage', None)

def edit_zfs_server_name_handler(update, context, server_name):
    """РќР°С‡Р°С‚СЊ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РёРјРµРЅРё ZFS СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    if server_name not in zfs_servers:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    context.user_data['editing_zfs_server_name'] = True
    context.user_data['editing_zfs_server_old_name'] = server_name

    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ ZFS СЃРµСЂРІРµСЂР°*\n\n"
        f"РўРµРєСѓС‰РµРµ РёРјСЏ: `{server_name}`\n\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РёРјСЏ СЃРµСЂРІРµСЂР°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_zfs'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def handle_zfs_server_name_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РёРјРµРЅРё ZFS СЃРµСЂРІРµСЂР°"""
    if 'editing_zfs_server_name' not in context.user_data:
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("вќЊ РРјСЏ СЃРµСЂРІРµСЂР° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    old_name = context.user_data.get('editing_zfs_server_old_name')
    if not old_name or old_name not in zfs_servers:
        update.message.reply_text("вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.")
        context.user_data.pop('editing_zfs_server_name', None)
        context.user_data.pop('editing_zfs_server_old_name', None)
        return

    if new_name in zfs_servers and new_name != old_name:
        update.message.reply_text("вќЊ РўР°РєРѕР№ СЃРµСЂРІРµСЂ СѓР¶Рµ РµСЃС‚СЊ. Р’РІРµРґРёС‚Рµ РґСЂСѓРіРѕР№:")
        return

    server_value = zfs_servers.pop(old_name, None)
    if not isinstance(server_value, dict):
        server_value = {'enabled': True}
    zfs_servers[new_name] = server_value
    settings_manager.set_setting('ZFS_SERVERS', zfs_servers)
    _rename_zfs_server_statuses(old_name, new_name)

    update.message.reply_text(
        f"вњ… РЎРµСЂРІРµСЂ РѕР±РЅРѕРІР»С‘РЅ: `{new_name}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_zfs_server_name', None)
    context.user_data.pop('editing_zfs_server_old_name', None)

def toggle_zfs_server(update, context, server_name):
    """Р’РєР»СЋС‡РёС‚СЊ/РѕС‚РєР»СЋС‡РёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі ZFS СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    if server_name not in zfs_servers:
        query.edit_message_text(
            "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    server_value = zfs_servers.get(server_name)
    if isinstance(server_value, dict):
        enabled = server_value.get('enabled', True)
    else:
        enabled = True
        server_value = {'enabled': True}

    server_value['enabled'] = not enabled
    zfs_servers[server_name] = server_value
    settings_manager.set_setting('ZFS_SERVERS', zfs_servers)

    status_text = "РІРєР»СЋС‡РµРЅ" if server_value['enabled'] else "РѕС‚РєР»СЋС‡РµРЅ"
    query.edit_message_text(
        f"вњ… РњРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂР° `{server_name}` {status_text}.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_zfs'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def _delete_zfs_server_statuses(server_name: str) -> None:
    """РЈРґР°Р»РёС‚СЊ СЃС‚Р°С‚СѓСЃС‹ ZFS СЃРµСЂРІРµСЂР° РёР· Р‘Р” Р±СЌРєР°РїРѕРІ."""
    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path:
        return

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM zfs_pool_status WHERE server_name = ?",
            (server_name,)
        )
        conn.commit()
    except Exception as exc:
        if "no such table: zfs_pool_status" not in str(exc):
            debug_logger(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ СѓРґР°Р»РёС‚СЊ СЃС‚Р°С‚СѓСЃС‹ ZFS СЃРµСЂРІРµСЂР°: {exc}")
    finally:
        conn.close()

def _rename_zfs_server_statuses(old_name: str, new_name: str) -> None:
    """РџРµСЂРµРёРјРµРЅРѕРІР°С‚СЊ СЃС‚Р°С‚СѓСЃС‹ ZFS СЃРµСЂРІРµСЂР° РІ Р‘Р” Р±СЌРєР°РїРѕРІ."""
    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path:
        return

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE zfs_pool_status SET server_name = ? WHERE server_name = ?",
            (new_name, old_name)
        )
        conn.commit()
    except Exception as exc:
        if "no such table: zfs_pool_status" not in str(exc):
            debug_logger(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РїРµСЂРµРёРјРµРЅРѕРІР°С‚СЊ СЃС‚Р°С‚СѓСЃС‹ ZFS СЃРµСЂРІРµСЂР°: {exc}")
    finally:
        conn.close()

def handle_setting_input(update, context, setting_key):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° Р·РЅР°С‡РµРЅРёР№ РЅР°СЃС‚СЂРѕРµРє"""
    query = update.callback_query
    query.answer()
    
    # РЎРѕС…СЂР°РЅСЏРµРј РєР°РєРѕРµ РЅР°СЃС‚СЂРѕР№РєСѓ РјРµРЅСЏРµРј
    context.user_data['editing_setting'] = setting_key
    context.user_data['editing_setting_message_id'] = query.message.message_id
    context.user_data['editing_setting_chat_id'] = query.message.chat_id
    
    setting_descriptions = {
        'telegram_token': 'Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ С‚РѕРєРµРЅ Telegram Р±РѕС‚Р°:',
        'check_interval': 'Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ РёРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё (РІ СЃРµРєСѓРЅРґР°С…):',
        'max_fail_time': 'Р’РІРµРґРёС‚Рµ РјР°РєСЃРёРјР°Р»СЊРЅРѕРµ РІСЂРµРјСЏ РїСЂРѕСЃС‚РѕСЏ (РІ СЃРµРєСѓРЅРґР°С…):',
        'silent_start': 'Р’РІРµРґРёС‚Рµ С‡Р°СЃ РЅР°С‡Р°Р»Р° С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (0-23):',
        'silent_end': 'Р’РІРµРґРёС‚Рµ С‡Р°СЃ РѕРєРѕРЅС‡Р°РЅРёСЏ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (0-23):',
        'data_collection': 'Р’РІРµРґРёС‚Рµ РІСЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С… (С„РѕСЂРјР°С‚ HH:MM):',
        'cpu_warning': 'Р’РІРµРґРёС‚Рµ РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РґР»СЏ CPU (%):',
        'cpu_critical': 'Р’РІРµРґРёС‚Рµ РєСЂРёС‚РёС‡РµСЃРєРёР№ РїРѕСЂРѕРі РґР»СЏ CPU (%):',
        'ram_warning': 'Р’РІРµРґРёС‚Рµ РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РґР»СЏ RAM (%):',
        'ram_critical': 'Р’РІРµРґРёС‚Рµ РєСЂРёС‚РёС‡РµСЃРєРёР№ РїРѕСЂРѕРі РґР»СЏ RAM (%):',
        'disk_warning': 'Р’РІРµРґРёС‚Рµ РїРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ РґР»СЏ Disk (%):',
        'disk_critical': 'Р’РІРµРґРёС‚Рµ РєСЂРёС‚РёС‡РµСЃРєРёР№ РїРѕСЂРѕРі РґР»СЏ Disk (%):',
        'ssh_username': 'Р’РІРµРґРёС‚Рµ РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ SSH:',
        'ssh_key_path': 'Р’РІРµРґРёС‚Рµ РїСѓС‚СЊ Рє SSH РєР»СЋС‡Сѓ:',
        'web_port': 'Р’РІРµРґРёС‚Рµ РїРѕСЂС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°:',
        'web_host': 'Р’РІРµРґРёС‚Рµ С…РѕСЃС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°:',
        'backup_alert_hours': 'Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°СЃРѕРІ РґР»СЏ Р°Р»РµСЂС‚РѕРІ Рѕ Р±СЌРєР°РїР°С…:',
        'backup_stale_hours': 'Р’РІРµРґРёС‚Рµ РєРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°СЃРѕРІ РґР»СЏ СѓСЃС‚Р°СЂРµРІС€РёС… Р±СЌРєР°РїРѕРІ:',
    }
    
    message = setting_descriptions.get(setting_key, f'Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ Р·РЅР°С‡РµРЅРёРµ РґР»СЏ {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_main')]
        ])
    )

def add_database_category_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґРѕР±Р°РІР»РµРЅРёСЏ РєР°С‚РµРіРѕСЂРёРё Р‘Р”"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ РєР°С‚РµРіРѕСЂРёРё Р±Р°Р· РґР°РЅРЅС‹С…*\n\n"
        "Р­С‚Р° С„СѓРЅРєС†РёСЏ РЅР°С…РѕРґРёС‚СЃСЏ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ.\n"
        "РЎРєРѕСЂРѕ Р·РґРµСЃСЊ РјРѕР¶РЅРѕ Р±СѓРґРµС‚ РґРѕР±Р°РІР»СЏС‚СЊ РЅРѕРІС‹Рµ РєР°С‚РµРіРѕСЂРёРё Р‘Р” РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_databases')]
        ])
    )

def edit_database_category_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РєР°С‚РµРіРѕСЂРёРё Р‘Р”"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='backup_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"вњЏпёЏ {category}", callback_data=f'edit_category_{category}')])
    
    keyboard.append([InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_databases')])
    
    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РєР°С‚РµРіРѕСЂРёР№ Р±Р°Р· РґР°РЅРЅС‹С…*\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_database_category_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СѓРґР°Р»РµРЅРёСЏ РєР°С‚РµРіРѕСЂРёРё Р‘Р”"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='backup_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"рџ—‘пёЏ {category}", callback_data=f'delete_category_{category}')])
    
    keyboard.append([InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_databases')])
    
    query.edit_message_text(
        "рџ—‘пёЏ *РЈРґР°Р»РµРЅРёРµ РєР°С‚РµРіРѕСЂРёРё Р±Р°Р· РґР°РЅРЅС‹С…*\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ СѓРґР°Р»РµРЅРёСЏ:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def view_all_databases_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕСЃРјРѕС‚СЂР° РІСЃРµС… Р‘Р”"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "рџ“‹ *Р’СЃРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°*\n\n"
    
    if not db_config:
        message += "вќЊ *РќРµС‚ РЅР°СЃС‚СЂРѕРµРЅРЅС‹С… Р±Р°Р· РґР°РЅРЅС‹С…*\n\n"
        message += "Р”РѕР±Р°РІСЊС‚Рµ РєР°С‚РµРіРѕСЂРёРё Рё Р±Р°Р·С‹ РґР°РЅРЅС‹С… РІ РЅР°СЃС‚СЂРѕР№РєР°С…."
    else:
        total_dbs = 0
        for category, databases in db_config.items():
            message += f"рџ“Ѓ *{category.upper()}* ({len(databases)} Р‘Р”):\n"
            for db_key, db_name in databases.items():
                message += f"   вЂў {db_name}\n"
                total_dbs += 1
            message += "\n"
        
        message += f"*РС‚РѕРіРѕ:* {total_dbs} Р±Р°Р· РґР°РЅРЅС‹С… РІ {len(db_config)} РєР°С‚РµРіРѕСЂРёСЏС…"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_backup_databases')]
        ])
    )

def manage_chats_handler(update, context):
    """РЈРїСЂР°РІР»РµРЅРёРµ С‡Р°С‚Р°РјРё - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ Р‘Р•Р— РљРќРћРџРљР РЎРџРРЎРљРђ Р’РЎР•РҐ Р§РђРўРћР’"""
    query = update.callback_query
    query.answer()
    
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    message = "рџ’¬ *РЈРїСЂР°РІР»РµРЅРёРµ С‡Р°С‚Р°РјРё*\n\n"
    message += f"РўРµРєСѓС‰РµРµ РєРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°С‚РѕРІ: {len(chat_ids)}\n\n"
    
    if chat_ids:
        message += "*РўРµРєСѓС‰РёРµ С‡Р°С‚С‹:*\n"
        for i, chat_id in enumerate(chat_ids[:5], 1):
            message += f"{i}. `{chat_id}`\n"
        if len(chat_ids) > 5:
            message += f"... Рё РµС‰Рµ {len(chat_ids) - 5} С‡Р°С‚РѕРІ\n"
    else:
        message += "вќЊ *Р§Р°С‚С‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n"
    
    message += "\nР’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    
    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ С‡Р°С‚", callback_data='add_chat')],
        [InlineKeyboardButton("рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ С‡Р°С‚", callback_data='remove_chat')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_telegram'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def manage_tamtam_chats_handler(update, context):
    """РЈРїСЂР°РІР»РµРЅРёРµ С‡Р°С‚Р°РјРё TamTam."""
    query = update.callback_query
    query.answer()

    tamtam_chat_ids = settings_manager.get_setting('TAMTAM_CHAT_IDS', [])

    message = "рџџ  *РЈРїСЂР°РІР»РµРЅРёРµ TamTam С‡Р°С‚Р°РјРё*\n\n"
    message += f"РўРµРєСѓС‰РµРµ РєРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°С‚РѕРІ: {len(tamtam_chat_ids)}\n\n"

    if tamtam_chat_ids:
        message += "*РўРµРєСѓС‰РёРµ С‡Р°С‚С‹:*\n"
        for i, chat_id in enumerate(tamtam_chat_ids[:5], 1):
            message += f"{i}. `{chat_id}`\n"
        if len(tamtam_chat_ids) > 5:
            message += f"... Рё РµС‰Рµ {len(tamtam_chat_ids) - 5} С‡Р°С‚РѕРІ\n"
    else:
        message += "вќЊ *Р§Р°С‚С‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n"

    message += "\nР’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"

    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ С‡Р°С‚", callback_data='add_tamtam_chat')],
        [InlineKeyboardButton("рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ С‡Р°С‚", callback_data='remove_tamtam_chat')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_telegram'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_server_timeouts(update, context):
    """РўР°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ - РЈРџР РћР©Р•РќРќРђРЇ Р‘Р•Р— MARKDOWN Р’Р•Р РЎРРЇ"""
    query = update.callback_query
    query.answer()
    
    timeouts = settings_manager.get_setting('SERVER_TIMEOUTS', {})
    
    # РџСЂРѕСЃС‚РѕР№ С‚РµРєСЃС‚ Р±РµР· Markdown
    message = "вЏ° РўР°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ\n\n"
    
    if timeouts:
        for server_type, timeout in timeouts.items():
            message += f"вЂў {server_type}: {timeout} СЃРµРє\n"
    else:
        message += "вќЊ РўР°Р№РјР°СѓС‚С‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹\n"
        message += "РСЃРїРѕР»СЊР·СѓСЋС‚СЃСЏ Р·РЅР°С‡РµРЅРёСЏ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ.\n\n"
        message += "РўР°Р№РјР°СѓС‚С‹ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ:\n"
        message += "вЂў Windows 2025: 35 СЃРµРє\n"
        message += "вЂў Р”РѕРјРµРЅРЅС‹Рµ СЃРµСЂРІРµСЂС‹: 20 СЃРµРє\n"
        message += "вЂў Admin СЃРµСЂРІРµСЂС‹: 25 СЃРµРє\n"
        message += "вЂў РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ Windows: 30 СЃРµРє\n"
        message += "вЂў Linux СЃРµСЂРІРµСЂС‹: 15 СЃРµРє\n"
        message += "вЂў Ping СЃРµСЂРІРµСЂС‹: 10 СЃРµРє\n"
    
    message += "\nР’С‹Р±РµСЂРёС‚Рµ РїР°СЂР°РјРµС‚СЂ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ:"
    
    keyboard = [
        [InlineKeyboardButton("рџ–ҐпёЏ Windows 2025", callback_data='set_windows_2025_timeout')],
        [InlineKeyboardButton("рџЊђ Р”РѕРјРµРЅРЅС‹Рµ СЃРµСЂРІРµСЂС‹", callback_data='set_domain_servers_timeout')],
        [InlineKeyboardButton("рџ”§ Admin СЃРµСЂРІРµСЂС‹", callback_data='set_admin_servers_timeout')],
        [InlineKeyboardButton("рџ’» РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ Windows", callback_data='set_standard_windows_timeout')],
        [InlineKeyboardButton("рџђ§ Linux СЃРµСЂРІРµСЂС‹", callback_data='set_linux_timeout')],
        [InlineKeyboardButton("рџ“Ў Ping СЃРµСЂРІРµСЂС‹", callback_data='set_ping_timeout')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_monitoring'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,  # Р‘РµР· parse_mode
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_server_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ - РћРЎРќРћР’РќРђРЇ Р Р•РђР›РР—РђР¦РРЇ"""
    query = update.callback_query
    query.answer()
    
    # РЎРѕС…СЂР°РЅСЏРµРј СЃРѕСЃС‚РѕСЏРЅРёРµ РґРѕР±Р°РІР»РµРЅРёСЏ СЃРµСЂРІРµСЂР°
    context.user_data['adding_server'] = True
    context.user_data['server_stage'] = 'ip'
    
    message = (
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ СЃРµСЂРІРµСЂР°*\n\n"
        "Р’РІРµРґРёС‚Рµ IP-Р°РґСЂРµСЃ СЃРµСЂРІРµСЂР°:\n\n"
        "_РџСЂРёРјРµСЂ: 192.168.6.000_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_servers')]
        ])
    )

def handle_server_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РґР°РЅРЅС‹С… СЃРµСЂРІРµСЂР°"""
    if 'adding_server' not in context.user_data or not context.user_data['adding_server']:
        return
    
    user_input = update.message.text
    stage = context.user_data.get('server_stage', 'ip')
    
    try:
        if stage == 'ip':
            # РџСЂРѕРІРµСЂРєР° IP-Р°РґСЂРµСЃР°
            import re
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            if not re.match(ip_pattern, user_input):
                update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ IP-Р°РґСЂРµСЃР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                return
            
            context.user_data['server_ip'] = user_input
            context.user_data['server_stage'] = 'name'
            
            update.message.reply_text(
                "рџ“ќ Р’РІРµРґРёС‚Рµ РёРјСЏ СЃРµСЂРІРµСЂР°:\n\n"
                "_РџСЂРёРјРµСЂ: web-server-01_",
                parse_mode='Markdown'
            )
            
        elif stage == 'name':
            context.user_data['server_name'] = user_input
            context.user_data['server_stage'] = 'type'
            
            keyboard = [
                [InlineKeyboardButton("рџ–ҐпёЏ Windows (RDP)", callback_data='server_type_rdp')],
                [InlineKeyboardButton("рџђ§ Linux (SSH)", callback_data='server_type_ssh')],
                [InlineKeyboardButton("рџ“Ў Ping Only", callback_data='server_type_ping')],
                [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_servers')]
            ]
            
            update.message.reply_text(
                "рџ”§ Р’С‹Р±РµСЂРёС‚Рµ С‚РёРї СЃРµСЂРІРµСЂР°:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР°: {e}")
        # РЎР±СЂР°СЃС‹РІР°РµРј СЃРѕСЃС‚РѕСЏРЅРёРµ РїСЂРё РѕС€РёР±РєРµ
        context.user_data['adding_server'] = False

def handle_server_type(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІС‹Р±РѕСЂР° С‚РёРїР° СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    query.answer()
    
    if 'adding_server' not in context.user_data:
        return
    
    server_type = query.data.replace('server_type_', '')
    server_ip = context.user_data.get('server_ip')
    server_name = context.user_data.get('server_name')
    
    try:
        # Р”РѕР±Р°РІР»СЏРµРј СЃРµСЂРІРµСЂ РІ Р±Р°Р·Сѓ
        success = settings_manager.add_server(server_ip, server_name, server_type)
        
        if success:
            message = f"вњ… *РЎРµСЂРІРµСЂ РґРѕР±Р°РІР»РµРЅ!*\n\nвЂў IP: `{server_ip}`\nвЂў РРјСЏ: `{server_name}`\nвЂў РўРёРї: `{server_type}`"
            
            # РћС‡РёС‰Р°РµРј СЃРѕСЃС‚РѕСЏРЅРёРµ
            context.user_data['adding_server'] = False
            context.user_data.pop('server_ip', None)
            context.user_data.pop('server_name', None)
            context.user_data.pop('server_stage', None)
        else:
            message = "вќЊ РћС€РёР±РєР° РїСЂРё РґРѕР±Р°РІР»РµРЅРёРё СЃРµСЂРІРµСЂР°"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ Рє СЃРµСЂРІРµСЂР°Рј", callback_data='settings_servers'),
                 InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РµС‰Рµ", callback_data='settings_add_server')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР°: {e}")

def view_all_databases_handler(update, context):
    """РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… Р‘Р” - РћРЎРќРћР’РќРђРЇ Р Р•РђР›РР—РђР¦РРЇ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        message = "рџ“‹ *Р’СЃРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…*\n\nвќЊ *РќРµС‚ РЅР°СЃС‚СЂРѕРµРЅРЅС‹С… Р±Р°Р· РґР°РЅРЅС‹С…*"
    else:
        message = "рџ“‹ *Р’СЃРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…*\n\n"
        total_dbs = 0
        
        for category, databases in db_config.items():
            message += f"рџ“Ѓ *{category.upper()}* ({len(databases)} Р‘Р”):\n"
            for db_key, db_name in databases.items():
                message += f"   вЂў {db_name}\n"
                total_dbs += 1
            message += "\n"
        
        message += f"*РС‚РѕРіРѕ:* {total_dbs} Р±Р°Р· РґР°РЅРЅС‹С… РІ {len(db_config)} РєР°С‚РµРіРѕСЂРёСЏС…"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def add_database_category_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ Р‘Р” - РћРЎРќРћР’РќРђРЇ Р Р•РђР›РР—РђР¦РРЇ"""
    query = update.callback_query
    query.answer()
    
    context.user_data['adding_db_category'] = True
    
    message = (
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ РєР°С‚РµРіРѕСЂРёРё Р‘Р”*\n\n"
        "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РЅРѕРІРѕР№ РєР°С‚РµРіРѕСЂРёРё:\n\n"
        "_РџСЂРёРјРµСЂ: company, client, backup_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_db_main')]
        ])
    )

def edit_databases_handler(update, context):
    """Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ Р‘Р” - РћРЎРќРћР’РќРђРЇ Р Р•РђР›РР—РђР¦РРЇ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='settings_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"вњЏпёЏ {category}", callback_data=f'settings_db_edit_{category}')])
    
    keyboard.append([InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')])
    
    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ Р±Р°Р· РґР°РЅРЅС‹С…*\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_database_category_handler(update, context):
    """РЈРґР°Р»РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ Р‘Р” - РћРЎРќРћР’РќРђРЇ Р Р•РђР›РР—РђР¦РРЇ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ", callback_data='settings_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"рџ—‘пёЏ {category}", callback_data=f'settings_db_delete_{category}')])
    
    keyboard.append([InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')])
    
    query.edit_message_text(
        "рџ—‘пёЏ *РЈРґР°Р»РµРЅРёРµ РєР°С‚РµРіРѕСЂРёРё Р‘Р”*\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ СѓРґР°Р»РµРЅРёСЏ:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def edit_database_category_details(update, context, category):
    """РџРѕРєР°Р·Р°С‚СЊ РґРµС‚Р°Р»Рё РєР°С‚РµРіРѕСЂРёРё Р‘Р”"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category)
    if databases is not None and not isinstance(databases, dict):
        databases = {}

    if databases is None:
        query.edit_message_text(
            "вќЊ РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    message = f"вњЏпёЏ *РљР°С‚РµРіРѕСЂРёСЏ {category}*\n\n"
    if not databases:
        message += "вќЊ Р’ СЌС‚РѕР№ РєР°С‚РµРіРѕСЂРёРё РЅРµС‚ Р±Р°Р· РґР°РЅРЅС‹С….\n"
    else:
        message += "РЎРїРёСЃРѕРє Р±Р°Р· РґР°РЅРЅС‹С…:\n"
        for db_key, db_name in databases.items():
            message += f"вЂў {db_name} (`{db_key}`)\n"

    message += "\nР’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"

    keyboard = [[InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ Р‘Р”", callback_data=f"settings_db_add_db_{category}")]]
    for db_key, db_name in databases.items():
        button_text = f"вњЏпёЏ {db_name}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"settings_db_edit_db_{category}__{db_key}"),
            InlineKeyboardButton(f"рџ—‘пёЏ {db_name}", callback_data=f"settings_db_delete_db_{category}__{db_key}")
        ])

    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_database_entry_handler(update, context, category):
    """Р—Р°РїСѓСЃРє РґРѕР±Р°РІР»РµРЅРёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РІ РєР°С‚РµРіРѕСЂРёСЋ"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if category not in db_config:
        query.edit_message_text(
            "вќЊ РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    # РРЅРёС†РёР°Р»РёР·РёСЂСѓРµРј СЃРѕСЃС‚РѕСЏРЅРёРµ РґРѕР±Р°РІР»РµРЅРёСЏ Р‘Р”
    context.user_data['adding_db_entry'] = True
    context.user_data['db_entry_category'] = category
    context.user_data.pop('db_entry_key', None)

    query.edit_message_text(
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n\n"
        "Р’РІРµРґРёС‚Рµ РєР»СЋС‡ Р±Р°Р·С‹ РґР°РЅРЅС‹С… (Р»Р°С‚РёРЅРёС†Р°/С†РёС„СЂС‹/СЃРёРјРІРѕР»С‹ `_`, `-`, `.`):\n\n"
        "_РџСЂРёРјРµСЂ: trade, client_db_01_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_db_main')]
        ])
    )

def edit_database_entry_handler(update, context, category, db_key):
    """Р—Р°РїСѓСЃРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    if not isinstance(databases, dict):
        databases = {}
    if db_key not in databases:
        query.edit_message_text(
            "вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    context.user_data['editing_db_entry'] = True
    context.user_data['db_entry_category'] = category
    context.user_data['db_entry_key'] = db_key

    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РљР»СЋС‡: `{db_key}`\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ РєР»СЋС‡:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='settings_db_main')]
        ])
    )

def delete_database_entry_confirmation(update, context, category, db_key):
    """РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    db_name = databases.get(db_key)

    if db_name is None:
        query.edit_message_text(
            "вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    query.edit_message_text(
        "рџ—‘пёЏ *РЈРґР°Р»РµРЅРёРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"Р‘Р°Р·Р°: `{db_name}`\n\n"
        "РЈРґР°Р»РёС‚СЊ?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вњ… РЈРґР°Р»РёС‚СЊ", callback_data=f"settings_db_delete_db_confirm_{category}__{db_key}")],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def delete_database_entry_execute(update, context, category, db_key):
    """РЈРґР°Р»РµРЅРёРµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    db_name = databases.pop(db_key, None)

    if db_name is None:
        query.edit_message_text(
            "вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    db_config[category] = databases
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    query.edit_message_text(
        "вњ… *Р‘Р°Р·Р° РґР°РЅРЅС‹С… СѓРґР°Р»РµРЅР°!*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"Р‘Р°Р·Р°: `{db_name}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def delete_database_category_confirmation(update, context, category):
    """РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ РєР°С‚РµРіРѕСЂРёРё Р‘Р”"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if category not in db_config:
        query.edit_message_text(
            "вќЊ РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    message = (
        "рџ—‘пёЏ *РЈРґР°Р»РµРЅРёРµ РєР°С‚РµРіРѕСЂРёРё Р‘Р”*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        "РџРѕРґС‚РІРµСЂРґРёС‚Рµ СѓРґР°Р»РµРЅРёРµ:"
    )

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вњ… РЈРґР°Р»РёС‚СЊ", callback_data=f"settings_db_delete_confirm_{category}")],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
        ])
    )

def delete_database_category_execute(update, context, category):
    """РЈРґР°Р»РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ Р‘Р”"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if category not in db_config:
        query.edit_message_text(
            "вќЊ РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
            ])
        )
        return

    db_config.pop(category, None)
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    query.edit_message_text(
        f"вњ… РљР°С‚РµРіРѕСЂРёСЏ *{category}* СѓРґР°Р»РµРЅР°.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )
    
def not_implemented_handler(update, context, feature_name=""):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґР»СЏ С„СѓРЅРєС†РёР№ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ"""
    query = update.callback_query
    query.answer()
    
    message = f"рџ› пёЏ *Р¤СѓРЅРєС†РёСЏ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ*\n\n"
    if feature_name:
        message += f"Р¤СѓРЅРєС†РёСЏ '{feature_name}' РЅР°С…РѕРґРёС‚СЃСЏ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ.\n"
    message += "РЎРєРѕСЂРѕ Р·РґРµСЃСЊ Р±СѓРґРµС‚ РґРѕСЃС‚СѓРїРЅР° РЅРѕРІР°СЏ С„СѓРЅРєС†РёРѕРЅР°Р»СЊРЅРѕСЃС‚СЊ."
    
    # РћРїСЂРµРґРµР»СЏРµРј РѕС‚РєСѓРґР° РїСЂРёС€РµР» Р·Р°РїСЂРѕСЃ РґР»СЏ РєРЅРѕРїРєРё "РќР°Р·Р°Рґ"
    back_button = 'settings_main'
    if hasattr(query, 'data'):
        if 'telegram' in query.data:
            back_button = 'settings_telegram'
        elif 'backup' in query.data:
            back_button = 'settings_backup'
        elif 'servers' in query.data:
            back_button = 'settings_servers'
        elif 'monitoring' in query.data:
            back_button = 'settings_monitoring'
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_button),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def handle_db_category_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РєР°С‚РµРіРѕСЂРёРё Р‘Р”"""
    if 'adding_db_category' not in context.user_data:
        return
    
    category_name = update.message.text.strip()
    
    try:
        # РџРѕР»СѓС‡Р°РµРј С‚РµРєСѓС‰СѓСЋ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ Р‘Р”
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        
        # Р”РѕР±Р°РІР»СЏРµРј РЅРѕРІСѓСЋ РєР°С‚РµРіРѕСЂРёСЋ
        if category_name not in db_config:
            db_config[category_name] = {}
            settings_manager.set_setting('DATABASE_CONFIG', db_config)
            
            update.message.reply_text(
                f"вњ… *РљР°С‚РµРіРѕСЂРёСЏ '{category_name}' РґРѕР±Р°РІР»РµРЅР°!*\n\n"
                "РўРµРїРµСЂСЊ РІС‹ РјРѕР¶РµС‚Рµ РґРѕР±Р°РІРёС‚СЊ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РІ СЌС‚Сѓ РєР°С‚РµРіРѕСЂРёСЋ.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вњЏпёЏ Р”РѕР±Р°РІРёС‚СЊ Р‘Р”", callback_data=f'settings_db_edit_{category_name}'),
                     InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
                ])
            )
        else:
            update.message.reply_text(
                f"вќЊ РљР°С‚РµРіРѕСЂРёСЏ '{category_name}' СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main')]
                ])
            )
    
    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР°: {e}")
    
    # РћС‡РёС‰Р°РµРј СЃРѕСЃС‚РѕСЏРЅРёРµ
    context.user_data['adding_db_category'] = False

def handle_db_entry_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґРѕР±Р°РІР»РµРЅРёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    if 'adding_db_entry' not in context.user_data:
        return

    user_input = update.message.text.strip()
    category = context.user_data.get('db_entry_category')

    if not category:
        update.message.reply_text("вќЊ РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
        context.user_data['adding_db_entry'] = False
        return

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    if not isinstance(databases, dict):
        databases = {}

    if not user_input:
        update.message.reply_text("вќЊ РљР»СЋС‡ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    if ' ' in user_input:
        update.message.reply_text("вќЊ РљР»СЋС‡ РЅРµ РґРѕР»Р¶РµРЅ СЃРѕРґРµСЂР¶Р°С‚СЊ РїСЂРѕР±РµР»С‹. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    if user_input in databases:
        update.message.reply_text("вќЊ РўР°РєРѕР№ РєР»СЋС‡ СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚. Р’РІРµРґРёС‚Рµ РґСЂСѓРіРѕР№:")
        return

    databases[user_input] = user_input
    db_config[category] = databases
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    update.message.reply_text(
        "вњ… *Р‘Р°Р·Р° РґР°РЅРЅС‹С… РґРѕР±Р°РІР»РµРЅР°!*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РљР»СЋС‡: `{user_input}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
             InlineKeyboardButton("вњЏпёЏ Р”РѕР±Р°РІРёС‚СЊ РµС‰Рµ", callback_data=f'settings_db_add_db_{category}')]
        ])
    )

    context.user_data.pop('adding_db_entry', None)
    context.user_data.pop('db_entry_category', None)
    context.user_data.pop('db_entry_key', None)

def handle_db_entry_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    if 'editing_db_entry' not in context.user_data:
        return

    user_input = update.message.text.strip()
    category = context.user_data.get('db_entry_category')
    db_key = context.user_data.get('db_entry_key')

    if not category or not db_key:
        update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ Р±Р°Р·Сѓ РґР°РЅРЅС‹С…. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
        context.user_data['editing_db_entry'] = False
        return

    if not user_input:
        update.message.reply_text("вќЊ РљР»СЋС‡ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})

    if db_key not in databases:
        update.message.reply_text("вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅРµ РЅР°Р№РґРµРЅР°.")
        context.user_data['editing_db_entry'] = False
        return

    if user_input in databases and user_input != db_key:
        update.message.reply_text("вќЊ РўР°РєРѕР№ РєР»СЋС‡ СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚. Р’РІРµРґРёС‚Рµ РґСЂСѓРіРѕР№:")
        return

    databases.pop(db_key, None)
    databases[user_input] = user_input
    db_config[category] = databases
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    update.message.reply_text(
        "вњ… *Р‘Р°Р·Р° РґР°РЅРЅС‹С… РѕР±РЅРѕРІР»РµРЅР°!*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РќРѕРІС‹Р№ РєР»СЋС‡: `{user_input}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_db_main'),
             InlineKeyboardButton("вњЏпёЏ Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ РµС‰Рµ", callback_data=f'settings_db_edit_{category}')]
        ])
    )

    context.user_data.pop('editing_db_entry', None)
    context.user_data.pop('db_entry_category', None)
    context.user_data.pop('db_entry_key', None)
    
def show_windows_auth_settings(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё Windows - РћРЎРќРћР’РќРћР• РњР•РќР®"""
    query = update.callback_query
    query.answer()
    
    # РџРѕР»СѓС‡Р°РµРј СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ СѓС‡РµС‚РЅС‹Рј РґР°РЅРЅС‹Рј
    credentials = settings_manager.get_windows_credentials()
    server_types = settings_manager.get_windows_server_types()
    
    # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
    stats = {}
    for cred in credentials:
        server_type = cred['server_type']
        if server_type not in stats:
            stats[server_type] = 0
        stats[server_type] += 1
    
    message = "рџ–ҐпёЏ *РЈРїСЂР°РІР»РµРЅРёРµ Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРµР№ Windows*\n\n"
    message += f"вЂў Р’СЃРµРіРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(credentials)}\n"
    message += f"вЂў РўРёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ: {len(server_types)}\n\n"
    
    if stats:
        message += "*РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРѕ С‚РёРїР°Рј:*\n"
        for server_type, count in stats.items():
            message += f"вЂў {server_type}: {count} СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№\n"
    else:
        message += "вќЊ *РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n"
    
    message += "\nР’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ:"
    
    keyboard = [
        [InlineKeyboardButton("рџ‘Ґ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№", callback_data='windows_auth_list')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ", callback_data='windows_auth_add')],
        [InlineKeyboardButton("рџ“Љ РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРѕ С‚РёРїР°Рј", callback_data='windows_auth_by_type')],
        [InlineKeyboardButton("вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ", callback_data='windows_auth_manage_types')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_auth'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_windows_auth_list(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃРїРёСЃРѕРє РІСЃРµС… СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№ Windows"""
    query = update.callback_query
    query.answer()
    
    credentials = settings_manager.get_windows_credentials()
    
    message = "рџ‘Ґ *Р’СЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё Windows*\n\n"
    
    if not credentials:
        message += "вќЊ *РЈС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё РЅРµ РЅР°Р№РґРµРЅС‹*\n"
    else:
        for i, cred in enumerate(credentials, 1):
            status = "рџџў" if cred['enabled'] else "рџ”ґ"
            message += f"{status} *{cred['server_type']}* (РїСЂРёРѕСЂРёС‚РµС‚: {cred['priority']})\n"
            message += f"   РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ: `{cred['username']}`\n"
            message += f"   РџР°СЂРѕР»СЊ: `{'*' * 8}`\n"
            message += f"   ID: {cred['id']}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ", callback_data='windows_auth_add')],
        [InlineKeyboardButton("вњЏпёЏ Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ", callback_data='windows_auth_edit')],
        [InlineKeyboardButton("рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ", callback_data='windows_auth_delete')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_windows_auth_add(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ С„РѕСЂРјСѓ РґРѕР±Р°РІР»РµРЅРёСЏ СѓС‡РµС‚РЅРѕР№ Р·Р°РїРёСЃРё Windows"""
    query = update.callback_query
    query.answer()
    
    # РќР°С‡РёРЅР°РµРј РїСЂРѕС†РµСЃСЃ РґРѕР±Р°РІР»РµРЅРёСЏ
    context.user_data['adding_windows_cred'] = True
    context.user_data['cred_stage'] = 'username'
    
    message = (
        "вћ• *Р”РѕР±Р°РІР»РµРЅРёРµ СѓС‡РµС‚РЅРѕР№ Р·Р°РїРёСЃРё Windows*\n\n"
        "Р’РІРµРґРёС‚Рµ РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ:\n\n"
        "_РџСЂРёРјРµСЂ: Administrator_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_main')]
        ])
    )

def show_windows_auth_by_type(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "рџ“Љ *РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ*\n\n"
    
    if not server_types:
        message += "вќЊ *РўРёРїС‹ СЃРµСЂРІРµСЂРѕРІ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n"
    else:
        for server_type in server_types:
            credentials = settings_manager.get_windows_credentials(server_type)
            message += f"*{server_type}* ({len(credentials)} СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№):\n"
            
            for cred in credentials[:3]:  # РџРѕРєР°Р·С‹РІР°РµРј РїРµСЂРІС‹Рµ 3
                status = "рџџў" if cred['enabled'] else "рџ”ґ"
                message += f"  {status} {cred['username']} (РїСЂРёРѕСЂРёС‚РµС‚: {cred['priority']})\n"
            
            if len(credentials) > 3:
                message += f"  ... Рё РµС‰Рµ {len(credentials) - 3} СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№\n"
            message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("рџ‘Ґ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС…", callback_data='windows_auth_list')],
        [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ", callback_data='windows_auth_add')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_windows_credential_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РґР°РЅРЅС‹С… СѓС‡РµС‚РЅРѕР№ Р·Р°РїРёСЃРё Windows"""
    if 'adding_windows_cred' not in context.user_data:
        return
    
    user_input = update.message.text
    stage = context.user_data.get('cred_stage')
    
    try:
        if stage == 'username':
            context.user_data['cred_username'] = user_input
            context.user_data['cred_stage'] = 'password'
            
            update.message.reply_text(
                "рџ”’ Р’РІРµРґРёС‚Рµ РїР°СЂРѕР»СЊ:\n\n"
                "_РџР°СЂРѕР»СЊ Р±СѓРґРµС‚ СЃРѕС…СЂР°РЅРµРЅ РІ Р·Р°С€РёС„СЂРѕРІР°РЅРЅРѕРј РІРёРґРµ_",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_main')]
                ])
            )
            
        elif stage == 'password':
            context.user_data['cred_password'] = user_input
            context.user_data['cred_stage'] = 'server_type'
            
            # РџСЂРµРґР»Р°РіР°РµРј СЃС‚Р°РЅРґР°СЂС‚РЅС‹Рµ С‚РёРїС‹ СЃРµСЂРІРµСЂРѕРІ
            keyboard = [
                [InlineKeyboardButton("рџ–ҐпёЏ Windows 2025", callback_data='cred_type_windows_2025')],
                [InlineKeyboardButton("рџЊђ Р”РѕРјРµРЅРЅС‹Рµ СЃРµСЂРІРµСЂС‹", callback_data='cred_type_domain_servers')],
                [InlineKeyboardButton("рџ”§ Admin СЃРµСЂРІРµСЂС‹", callback_data='cred_type_admin_servers')],
                [InlineKeyboardButton("рџ’» РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ Windows", callback_data='cred_type_standard_windows')],
                [InlineKeyboardButton("вљ™пёЏ Р”СЂСѓРіРѕР№ С‚РёРї", callback_data='cred_type_custom')],
                [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_main')]
            ]
            
            update.message.reply_text(
                "рџ–ҐпёЏ Р’С‹Р±РµСЂРёС‚Рµ С‚РёРї СЃРµСЂРІРµСЂРѕРІ РґР»СЏ СЌС‚РёС… СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif stage == 'server_type_custom':
            context.user_data['cred_server_type'] = user_input
            context.user_data['cred_stage'] = 'priority'
            
            update.message.reply_text(
                "рџ“Љ Р’РІРµРґРёС‚Рµ РїСЂРёРѕСЂРёС‚РµС‚ (С‡РёСЃР»Рѕ):\n\n"
                "_РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ СЃ Р±РѕР»РµРµ РІС‹СЃРѕРєРёРј РїСЂРёРѕСЂРёС‚РµС‚РѕРј Р±СѓРґСѓС‚ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊСЃСЏ РїРµСЂРІС‹РјРё_",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_main')]
                ])
            )
            
        elif stage == 'priority':
            try:
                priority = int(user_input)
                context.user_data['cred_priority'] = priority
                
                # РЎРѕС…СЂР°РЅСЏРµРј СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ
                username = context.user_data['cred_username']
                password = context.user_data['cred_password']
                server_type = context.user_data['cred_server_type']
                
                success = settings_manager.add_windows_credential(
                    username, password, server_type, priority
                )
                
                if success:
                    # РћС‡РёС‰Р°РµРј РєРѕРЅС‚РµРєСЃС‚
                    for key in ['adding_windows_cred', 'cred_stage', 'cred_username', 
                               'cred_password', 'cred_server_type', 'cred_priority']:
                        context.user_data.pop(key, None)
                    
                    update.message.reply_text(
                        f"вњ… *РЈС‡РµС‚РЅР°СЏ Р·Р°РїРёСЃСЊ РґРѕР±Р°РІР»РµРЅР°!*\n\n"
                        f"вЂў РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ: `{username}`\n"
                        f"вЂў РўРёРї СЃРµСЂРІРµСЂРѕРІ: `{server_type}`\n"
                        f"вЂў РџСЂРёРѕСЂРёС‚РµС‚: `{priority}`",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РµС‰Рµ", callback_data='windows_auth_add'),
                             InlineKeyboardButton("рџ‘Ґ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС…", callback_data='windows_auth_list')],
                            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_main')]
                        ])
                    )
                else:
                    update.message.reply_text("вќЊ РћС€РёР±РєР° РїСЂРё СЃРѕС…СЂР°РЅРµРЅРёРё СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…")
                    
            except ValueError:
                update.message.reply_text("вќЊ РџСЂРёРѕСЂРёС‚РµС‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ С‡РёСЃР»РѕРј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
                
    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР°: {e}")
        # РЎР±СЂР°СЃС‹РІР°РµРј СЃРѕСЃС‚РѕСЏРЅРёРµ РїСЂРё РѕС€РёР±РєРµ
        context.user_data['adding_windows_cred'] = False

def handle_credential_type_selection(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РІС‹Р±РѕСЂР° С‚РёРїР° СЃРµСЂРІРµСЂР° РґР»СЏ СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…"""
    query = update.callback_query
    query.answer()
    
    if 'adding_windows_cred' not in context.user_data:
        return
    
    cred_type = query.data.replace('cred_type_', '')
    
    type_mapping = {
        'windows_2025': 'windows_2025',
        'domain_servers': 'domain_servers', 
        'admin_servers': 'admin_servers',
        'standard_windows': 'standard_windows'
    }
    
    if cred_type == 'custom':
        context.user_data['cred_stage'] = 'server_type_custom'
        query.edit_message_text(
            "вњЏпёЏ Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ:\n\n"
            "_РџСЂРёРјРµСЂ: backup_servers, web_servers_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_main')]
            ])
        )
    else:
        context.user_data['cred_server_type'] = type_mapping.get(cred_type, cred_type)
        context.user_data['cred_stage'] = 'priority'
        
        query.edit_message_text(
            "рџ“Љ Р’РІРµРґРёС‚Рµ РїСЂРёРѕСЂРёС‚РµС‚ (С‡РёСЃР»Рѕ):\n\n"
            "_РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ СЃ Р±РѕР»РµРµ РІС‹СЃРѕРєРёРј РїСЂРёРѕСЂРёС‚РµС‚РѕРј Р±СѓРґСѓС‚ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊСЃСЏ РїРµСЂРІС‹РјРё_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_main')]
            ])
        )

def show_windows_auth_manage_types(update, context):
    """РЈРїСЂР°РІР»РµРЅРёРµ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ - РћР‘РќРћР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ РЎ РќРђРЎРўР РћР™РљРђРњР"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "вљ™пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ*\n\n"
    
    if not server_types:
        message += "вќЊ *РўРёРїС‹ СЃРµСЂРІРµСЂРѕРІ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹*\n"
    else:
        message += "*РЎСѓС‰РµСЃС‚РІСѓСЋС‰РёРµ С‚РёРїС‹:*\n"
        for server_type in server_types:
            credentials = settings_manager.get_windows_credentials(server_type)
            enabled_count = sum(1 for cred in credentials if cred['enabled'])
            message += f"вЂў *{server_type}*: {enabled_count}/{len(credentials)} Р°РєС‚РёРІРЅС‹С… СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№\n"
    
    message += "\n*Р”РѕСЃС‚СѓРїРЅС‹Рµ РґРµР№СЃС‚РІРёСЏ:*\n"
    message += "вЂў *РџРµСЂРµРёРјРµРЅРѕРІР°С‚СЊ С‚РёРї* - РёР·РјРµРЅРёС‚СЊ РЅР°Р·РІР°РЅРёРµ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ\n"
    message += "вЂў *РћР±СЉРµРґРёРЅРёС‚СЊ С‚РёРїС‹* - РѕР±СЉРµРґРёРЅРёС‚СЊ РґРІР° С‚РёРїР° РІ РѕРґРёРЅ\n"
    message += "вЂў *РЈРґР°Р»РёС‚СЊ С‚РёРї* - СѓРґР°Р»РёС‚СЊ С‚РёРї (СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё СЃРѕС…СЂР°РЅСЏС‚СЃСЏ)\n"
    
    keyboard = []
    
    # РљРЅРѕРїРєРё РґР»СЏ РєР°Р¶РґРѕРіРѕ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ
    for server_type in server_types:
        keyboard.append([
            InlineKeyboardButton(f"вњЏпёЏ {server_type}", callback_data=f'manage_type_edit_{server_type}'),
            InlineKeyboardButton(f"рџ”„ {server_type}", callback_data=f'manage_type_merge_{server_type}')
        ])
    
    # РћР±С‰РёРµ РґРµР№СЃС‚РІРёСЏ
    keyboard.extend([
        [InlineKeyboardButton("вћ• РЎРѕР·РґР°С‚СЊ РЅРѕРІС‹Р№ С‚РёРї", callback_data='manage_type_create')],
        [InlineKeyboardButton("рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ С‚РёРї", callback_data='manage_type_delete')],
        [InlineKeyboardButton("рџ“Љ РЎС‚Р°С‚РёСЃС‚РёРєР° РїРѕ С‚РёРїР°Рј", callback_data='manage_type_stats')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_main'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_server_type_management(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СѓРїСЂР°РІР»РµРЅРёСЏ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    data = query.data
    
    if data == 'manage_type_create':
        create_server_type_handler(update, context)
    elif data == 'manage_type_delete':
        delete_server_type_handler(update, context)
    elif data == 'manage_type_stats':
        show_server_type_stats(update, context)
    elif data.startswith('manage_type_edit_'):
        server_type = data.replace('manage_type_edit_', '')
        edit_server_type_handler(update, context, server_type)
    elif data.startswith('manage_type_merge_'):
        server_type = data.replace('manage_type_merge_', '')
        merge_server_type_handler(update, context, server_type)
       

def create_server_type_handler(update, context):
    """РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕРіРѕ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    context.user_data['creating_server_type'] = True
    
    query.edit_message_text(
        "вћ• *РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕРіРѕ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ*\n\n"
        "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РґР»СЏ РЅРѕРІРѕРіРѕ С‚РёРїР°:\n\n"
        "_РџСЂРёРјРµСЂ: web_servers, database_servers, backup_servers_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_manage_types')]
        ])
    )

def edit_server_type_handler(update, context, old_type):
    """Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    context.user_data['editing_server_type'] = True
    context.user_data['old_server_type'] = old_type
    
    credentials = settings_manager.get_windows_credentials(old_type)
    
    query.edit_message_text(
        f"вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ*\n\n"
        f"РўРµРєСѓС‰РµРµ РЅР°Р·РІР°РЅРёРµ: *{old_type}*\n"
        f"РљРѕР»РёС‡РµСЃС‚РІРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(credentials)}\n\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІРѕРµ РЅР°Р·РІР°РЅРёРµ РґР»СЏ СЌС‚РѕРіРѕ С‚РёРїР°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_manage_types')]
        ])
    )

def merge_server_type_handler(update, context, source_type):
    """РћР±СЉРµРґРёРЅРµРЅРёРµ С‚РёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    # РСЃРєР»СЋС‡Р°РµРј С‚РµРєСѓС‰РёР№ С‚РёРї РёР· СЃРїРёСЃРєР° РґР»СЏ РѕР±СЉРµРґРёРЅРµРЅРёСЏ
    target_types = [t for t in server_types if t != source_type]
    
    if not target_types:
        query.answer("вќЊ РќРµС‚ РґСЂСѓРіРёС… С‚РёРїРѕРІ РґР»СЏ РѕР±СЉРµРґРёРЅРµРЅРёСЏ")
        return
    
    message = f"рџ”„ *РћР±СЉРµРґРёРЅРµРЅРёРµ С‚РёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ*\n\n"
    message += f"РСЃС‚РѕС‡РЅРёРє: *{source_type}*\n"
    message += f"РЈС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(settings_manager.get_windows_credentials(source_type))}\n\n"
    message += "Р’С‹Р±РµСЂРёС‚Рµ С†РµР»РµРІРѕР№ С‚РёРї РґР»СЏ РѕР±СЉРµРґРёРЅРµРЅРёСЏ:"
    
    keyboard = []
    for target_type in target_types:
        cred_count = len(settings_manager.get_windows_credentials(target_type))
        keyboard.append([
            InlineKeyboardButton(
                f"рџ”„ {target_type} ({cred_count})", 
                callback_data=f'merge_confirm_{source_type}_{target_type}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_manage_types')])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_type_handler(update, context):
    """РЈРґР°Р»РµРЅРёРµ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "рџ—‘пёЏ *РЈРґР°Р»РµРЅРёРµ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ*\n\n"
    message += "Р’С‹Р±РµСЂРёС‚Рµ С‚РёРї РґР»СЏ СѓРґР°Р»РµРЅРёСЏ:\n\n"
    message += "*Р’РЅРёРјР°РЅРёРµ:* РџСЂРё СѓРґР°Р»РµРЅРёРё С‚РёРїР° РІСЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё СЌС‚РѕРіРѕ С‚РёРїР° Р±СѓРґСѓС‚ РїРµСЂРµРјРµС‰РµРЅС‹ РІ С‚РёРї 'default'"
    
    keyboard = []
    for server_type in server_types:
        if server_type != 'default':  # РќРµ РїРѕР·РІРѕР»СЏРµРј СѓРґР°Р»РёС‚СЊ С‚РёРї 'default'
            cred_count = len(settings_manager.get_windows_credentials(server_type))
            keyboard.append([
                InlineKeyboardButton(
                    f"рџ—‘пёЏ {server_type} ({cred_count})", 
                    callback_data=f'delete_type_confirm_{server_type}'
                )
            ])
    
    keyboard.append([InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_manage_types')])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_server_type_stats(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "рџ“Љ *РЎС‚Р°С‚РёСЃС‚РёРєР° РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ*\n\n"
    
    total_credentials = 0
    for server_type in server_types:
        credentials = settings_manager.get_windows_credentials(server_type)
        enabled_count = sum(1 for cred in credentials if cred['enabled'])
        total_credentials += len(credentials)
        
        message += f"*{server_type}*\n"
        message += f"вЂў Р’СЃРµРіРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(credentials)}\n"
        message += f"вЂў РђРєС‚РёРІРЅС‹С…: {enabled_count}\n"
        message += f"вЂў РќРµР°РєС‚РёРІРЅС‹С…: {len(credentials) - enabled_count}\n\n"
    
    message += f"*РћР±С‰Р°СЏ СЃС‚Р°С‚РёСЃС‚РёРєР°:*\n"
    message += f"вЂў РўРёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ: {len(server_types)}\n"
    message += f"вЂў Р’СЃРµРіРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {total_credentials}\n"
    message += f"вЂў РЎСЂРµРґРЅРµРµ РЅР° С‚РёРї: {total_credentials / len(server_types):.1f} СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='manage_type_stats')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_manage_types'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def merge_server_types_confirmation(update, context, source_type, target_type):
    """РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ РѕР±СЉРµРґРёРЅРµРЅРёСЏ С‚РёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    source_creds = settings_manager.get_windows_credentials(source_type)
    target_creds = settings_manager.get_windows_credentials(target_type)
    
    message = f"рџ”„ *РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ РѕР±СЉРµРґРёРЅРµРЅРёСЏ*\n\n"
    message += f"*РСЃС‚РѕС‡РЅРёРє:* {source_type}\n"
    message += f"вЂў РЈС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(source_creds)}\n\n"
    message += f"*Р¦РµР»СЊ:* {target_type}\n"
    message += f"вЂў РЈС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(target_creds)}\n\n"
    message += f"*РџРѕСЃР»Рµ РѕР±СЉРµРґРёРЅРµРЅРёСЏ:*\n"
    message += f"вЂў РўРёРї {source_type} Р±СѓРґРµС‚ СѓРґР°Р»РµРЅ\n"
    message += f"вЂў Р’СЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё Р±СѓРґСѓС‚ РїРµСЂРµРјРµС‰РµРЅС‹ РІ {target_type}\n"
    message += f"вЂў РС‚РѕРіРѕРІРѕРµ РєРѕР»РёС‡РµСЃС‚РІРѕ: {len(source_creds) + len(target_creds)} СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№\n\n"
    message += "Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ РІС‹РїРѕР»РЅРёС‚СЊ РѕР±СЉРµРґРёРЅРµРЅРёРµ?"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("вњ… Р”Р°, РѕР±СЉРµРґРёРЅРёС‚СЊ", callback_data=f'merge_execute_{source_type}_{target_type}'),
                InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_manage_types')
            ]
        ])
    )

def delete_server_type_confirmation(update, context, server_type):
    """РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    credentials = settings_manager.get_windows_credentials(server_type)
    
    message = f"рџ—‘пёЏ *РџРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ*\n\n"
    message += f"РўРёРї: *{server_type}*\n"
    message += f"РЈС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(credentials)}\n\n"
    message += "*Р’РЅРёРјР°РЅРёРµ:* Р’СЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё СЌС‚РѕРіРѕ С‚РёРїР° Р±СѓРґСѓС‚ РїРµСЂРµРјРµС‰РµРЅС‹ РІ С‚РёРї 'default'\n\n"
    message += "Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ СѓРґР°Р»РёС‚СЊ СЌС‚РѕС‚ С‚РёРї?"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("вњ… Р”Р°, СѓРґР°Р»РёС‚СЊ", callback_data=f'delete_type_execute_{server_type}'),
                InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data='windows_auth_manage_types')
            ]
        ])
    )

def execute_server_type_merge(update, context, source_type, target_type):
    """Р’С‹РїРѕР»РЅРµРЅРёРµ РѕР±СЉРµРґРёРЅРµРЅРёСЏ С‚РёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    try:
        # РџРѕР»СѓС‡Р°РµРј СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РёСЃС…РѕРґРЅРѕРіРѕ С‚РёРїР°
        source_credentials = settings_manager.get_windows_credentials(source_type)
        
        # РћР±РЅРѕРІР»СЏРµРј С‚РёРї РґР»СЏ РєР°Р¶РґРѕР№ СѓС‡РµС‚РЅРѕР№ Р·Р°РїРёСЃРё
        for cred in source_credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type=target_type
            )
        
        message = f"вњ… *РўРёРїС‹ СЃРµСЂРІРµСЂРѕРІ РѕР±СЉРµРґРёРЅРµРЅС‹!*\n\n"
        message += f"вЂў РўРёРї *{source_type}* СѓРґР°Р»РµРЅ\n"
        message += f"вЂў Р’СЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё РїРµСЂРµРјРµС‰РµРЅС‹ РІ *{target_type}*\n"
        message += f"вЂў РџРµСЂРµРјРµС‰РµРЅРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(source_credentials)}"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ Рљ СѓРїСЂР°РІР»РµРЅРёСЋ С‚РёРїР°РјРё", callback_data='windows_auth_manage_types')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РїСЂРё РѕР±СЉРµРґРёРЅРµРЅРёРё С‚РёРїРѕРІ: {str(e)}")

def execute_server_type_delete(update, context, server_type):
    """Р’С‹РїРѕР»РЅРµРЅРёРµ СѓРґР°Р»РµРЅРёСЏ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    query.answer()
    
    try:
        # РџРѕР»СѓС‡Р°РµРј СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ СѓРґР°Р»СЏРµРјРѕРіРѕ С‚РёРїР°
        credentials = settings_manager.get_windows_credentials(server_type)
        
        # РџРµСЂРµРјРµС‰Р°РµРј РІСЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё РІ С‚РёРї 'default'
        for cred in credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type='default'
            )
        
        message = f"вњ… *РўРёРї СЃРµСЂРІРµСЂРѕРІ СѓРґР°Р»РµРЅ!*\n\n"
        message += f"вЂў РўРёРї *{server_type}* СѓРґР°Р»РµРЅ\n"
        message += f"вЂў Р’СЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё РїРµСЂРµРјРµС‰РµРЅС‹ РІ С‚РёРї 'default'\n"
        message += f"вЂў РџРµСЂРµРјРµС‰РµРЅРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(credentials)}"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ Рљ СѓРїСЂР°РІР»РµРЅРёСЋ С‚РёРїР°РјРё", callback_data='windows_auth_manage_types')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РїСЂРё СѓРґР°Р»РµРЅРёРё С‚РёРїР°: {str(e)}")

def handle_server_type_creation(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЃРѕР·РґР°РЅРёСЏ РЅРѕРІРѕРіРѕ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    new_type = update.message.text.strip()
    
    try:
        # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚ Р»Рё СѓР¶Рµ С‚Р°РєРѕР№ С‚РёРї
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types:
            update.message.reply_text(
                f"вќЊ РўРёРї '{new_type}' СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_manage_types')]
                ])
            )
            return
        
        # РЎРѕР·РґР°РµРј РЅРѕРІСѓСЋ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ СЃ СЌС‚РёРј С‚РёРїРѕРј (РјРѕР¶РЅРѕ РїСѓСЃС‚СѓСЋ)
        success = settings_manager.add_windows_credential(
            username=f"user_{new_type}",
            password="temp_password",
            server_type=new_type,
            priority=0
        )
        
        if success:
            # РЎСЂР°Р·Сѓ СѓРґР°Р»СЏРµРј РІСЂРµРјРµРЅРЅСѓСЋ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ, РµСЃР»Рё РЅСѓР¶РЅРѕ
            # РёР»Рё РѕСЃС‚Р°РІР»СЏРµРј РєР°Рє С€Р°Р±Р»РѕРЅ
            
            update.message.reply_text(
                f"вњ… *РўРёРї СЃРµСЂРІРµСЂРѕРІ '{new_type}' СЃРѕР·РґР°РЅ!*\n\n"
                "РўРµРїРµСЂСЊ РІС‹ РјРѕР¶РµС‚Рµ РґРѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё РґР»СЏ СЌС‚РѕРіРѕ С‚РёРїР°.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ", callback_data='windows_auth_add'),
                     InlineKeyboardButton("в†©пёЏ Рљ СѓРїСЂР°РІР»РµРЅРёСЋ С‚РёРїР°РјРё", callback_data='windows_auth_manage_types')]
                ])
            )
        else:
            update.message.reply_text("вќЊ РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё С‚РёРїР°")
    
    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР°: {e}")
    
    # РћС‡РёС‰Р°РµРј РєРѕРЅС‚РµРєСЃС‚
    context.user_data['creating_server_type'] = False

def handle_server_type_editing(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ С‚РёРїР° СЃРµСЂРІРµСЂРѕРІ"""
    new_type = update.message.text.strip()
    old_type = context.user_data.get('old_server_type')
    
    try:
        # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚ Р»Рё СѓР¶Рµ С‚Р°РєРѕР№ С‚РёРї
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types and new_type != old_type:
            update.message.reply_text(
                f"вќЊ РўРёРї '{new_type}' СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='windows_auth_manage_types')]
                ])
            )
            return
        
        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё СЃС‚Р°СЂРѕРіРѕ С‚РёРїР°
        credentials = settings_manager.get_windows_credentials(old_type)
        
        # РћР±РЅРѕРІР»СЏРµРј С‚РёРї РґР»СЏ РєР°Р¶РґРѕР№ СѓС‡РµС‚РЅРѕР№ Р·Р°РїРёСЃРё
        for cred in credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type=new_type
            )
        
        update.message.reply_text(
            f"вњ… *РўРёРї СЃРµСЂРІРµСЂРѕРІ РїРµСЂРµРёРјРµРЅРѕРІР°РЅ!*\n\n"
            f"вЂў РЎС‚Р°СЂРѕРµ РЅР°Р·РІР°РЅРёРµ: {old_type}\n"
            f"вЂў РќРѕРІРѕРµ РЅР°Р·РІР°РЅРёРµ: {new_type}\n"
            f"вЂў РћР±РЅРѕРІР»РµРЅРѕ СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: {len(credentials)}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ Рљ СѓРїСЂР°РІР»РµРЅРёСЋ С‚РёРїР°РјРё", callback_data='windows_auth_manage_types')]
            ])
        )
    
    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР°: {e}")
    
    # РћС‡РёС‰Р°РµРј РєРѕРЅС‚РµРєСЃС‚
    context.user_data['editing_server_type'] = False
    context.user_data.pop('old_server_type', None)

# РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РЅРµСЂР°Р±РѕС‚Р°СЋС‰РёС… РєРЅРѕРїРѕРє
def add_chat_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ С‡Р°С‚ - Р·Р°РіР»СѓС€РєР°"""
    not_implemented_handler(update, context, "Р”РѕР±Р°РІР»РµРЅРёРµ С‡Р°С‚Р°")

def remove_chat_handler(update, context):
    """РЈРґР°Р»РёС‚СЊ С‡Р°С‚ - Р·Р°РіР»СѓС€РєР°"""
    not_implemented_handler(update, context, "РЈРґР°Р»РµРЅРёРµ С‡Р°С‚Р°")

def add_tamtam_chat_handler(update, context):
    """РќР°С‡Р°С‚СЊ РґРѕР±Р°РІР»РµРЅРёРµ TamTam С‡Р°С‚Р°."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_tamtam_chat'] = True
    context.user_data.pop('removing_tamtam_chat', None)

    query.edit_message_text(
        "рџџ  *Р”РѕР±Р°РІР»РµРЅРёРµ TamTam С‡Р°С‚Р°*\n\n"
        "РћС‚РїСЂР°РІСЊС‚Рµ ID С‡Р°С‚Р° TamTam РѕРґРЅРёРј СЃРѕРѕР±С‰РµРЅРёРµРј.\n"
        "РќР°РїСЂРёРјРµСЂ: `1234567890`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='manage_tamtam_chats')],
            [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def remove_tamtam_chat_handler(update, context):
    """РќР°С‡Р°С‚СЊ СѓРґР°Р»РµРЅРёРµ TamTam С‡Р°С‚Р°."""
    query = update.callback_query
    query.answer()

    tamtam_chat_ids = settings_manager.get_setting('TAMTAM_CHAT_IDS', [])
    if not tamtam_chat_ids:
        query.edit_message_text(
            "вќЊ РЎРїРёСЃРѕРє TamTam С‡Р°С‚РѕРІ РїСѓСЃС‚.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='manage_tamtam_chats')],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    context.user_data['removing_tamtam_chat'] = True
    context.user_data.pop('adding_tamtam_chat', None)

    preview = "\n".join(f"вЂў `{chat_id}`" for chat_id in tamtam_chat_ids[:10])
    if len(tamtam_chat_ids) > 10:
        preview += f"\n... Рё РµС‰Рµ {len(tamtam_chat_ids) - 10}"

    query.edit_message_text(
        "рџџ  *РЈРґР°Р»РµРЅРёРµ TamTam С‡Р°С‚Р°*\n\n"
        "РўРµРєСѓС‰РёРµ ID:\n"
        f"{preview}\n\n"
        "РћС‚РїСЂР°РІСЊС‚Рµ ID, РєРѕС‚РѕСЂС‹Р№ РЅСѓР¶РЅРѕ СѓРґР°Р»РёС‚СЊ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='manage_tamtam_chats')],
            [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )


def handle_tamtam_chat_add_input(update, context):
    """Р”РѕР±Р°РІР»СЏРµС‚ TamTam chat ID РёР· С‚РµРєСЃС‚РѕРІРѕРіРѕ РІРІРѕРґР°."""
    chat_id = update.message.text.strip()
    if not chat_id:
        update.message.reply_text("вќЊ ID С‡Р°С‚Р° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
        return

    tamtam_chat_ids = settings_manager.get_setting('TAMTAM_CHAT_IDS', [])
    if chat_id in tamtam_chat_ids:
        context.user_data.pop('adding_tamtam_chat', None)
        update.message.reply_text(
            "в„№пёЏ Р­С‚РѕС‚ ID СѓР¶Рµ РµСЃС‚СЊ РІ СЃРїРёСЃРєРµ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџџ  Рљ TamTam С‡Р°С‚Р°Рј", callback_data='manage_tamtam_chats')]
            ])
        )
        return

    tamtam_chat_ids.append(chat_id)
    settings_manager.set_setting('TAMTAM_CHAT_IDS', tamtam_chat_ids, 'tamtam')
    context.user_data.pop('adding_tamtam_chat', None)

    update.message.reply_text(
        f"вњ… TamTam С‡Р°С‚ `{chat_id}` РґРѕР±Р°РІР»РµРЅ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџџ  Рљ TamTam С‡Р°С‚Р°Рј", callback_data='manage_tamtam_chats')]
        ])
    )


def handle_tamtam_chat_remove_input(update, context):
    """РЈРґР°Р»СЏРµС‚ TamTam chat ID РёР· СЃРїРёСЃРєР°."""
    chat_id = update.message.text.strip()
    tamtam_chat_ids = settings_manager.get_setting('TAMTAM_CHAT_IDS', [])

    if chat_id not in tamtam_chat_ids:
        update.message.reply_text(
            "вќЊ РўР°РєРѕР№ ID РЅРµ РЅР°Р№РґРµРЅ РІ СЃРїРёСЃРєРµ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџџ  Рљ TamTam С‡Р°С‚Р°Рј", callback_data='manage_tamtam_chats')]
            ])
        )
        return

    tamtam_chat_ids = [item for item in tamtam_chat_ids if item != chat_id]
    settings_manager.set_setting('TAMTAM_CHAT_IDS', tamtam_chat_ids, 'tamtam')
    context.user_data.pop('removing_tamtam_chat', None)

    update.message.reply_text(
        f"вњ… TamTam С‡Р°С‚ `{chat_id}` СѓРґР°Р»С‘РЅ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџџ  Рљ TamTam С‡Р°С‚Р°Рј", callback_data='manage_tamtam_chats')]
        ])
    )

def view_all_settings_handler(update, context):
    """РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… РЅР°СЃС‚СЂРѕРµРє - Р·Р°РіР»СѓС€РєР°"""
    not_implemented_handler(update, context, "РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… РЅР°СЃС‚СЂРѕРµРє")

def add_pattern_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ РїР°С‚С‚РµСЂРЅ - Р·Р°РіР»СѓС€РєР°"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'db_input'
    context.user_data['backup_pattern_mode'] = 'db_wizard'

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° Р‘Р”*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р’Рѕ С„СЂР°РіРјРµРЅС‚Р°С… РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ СѓРєР°Р¶РёС‚Рµ РёРјСЏ Р‘Р” РёР· РЅР°СЃС‚СЂРѕРµРє.\n\n"
        "РџСЂРёРјРµСЂ С‚РµРјС‹:\n"
        "`Backup db company_main completed`\n\n"
        "РџСЂРёРјРµСЂ С„СЂР°РіРјРµРЅС‚РѕРІ:\n"
        "`Backup db; company_main; completed`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def add_zfs_pattern_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ РїР°С‚С‚РµСЂРЅ РґР»СЏ ZFS"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'zfs_input'
    context.user_data['backup_pattern_mode'] = 'zfs_wizard'

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° ZFS*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р’Рѕ С„СЂР°РіРјРµРЅС‚Р°С… РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ СѓРєР°Р¶РёС‚Рµ РёРјСЏ ZFS СЃРµСЂРІРµСЂР° РёР· РЅР°СЃС‚СЂРѕРµРє.\n\n"
        "РџСЂРёРјРµСЂ С‚РµРјС‹:\n"
        "`ZFS alert zfs01: state: ONLINE, state: ONLINE`\n\n"
        "РџСЂРёРјРµСЂ С„СЂР°РіРјРµРЅС‚РѕРІ:\n"
        "`ZFS alert; zfs01; state:`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def add_proxmox_pattern_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ РїР°С‚С‚РµСЂРЅ РґР»СЏ Proxmox"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'proxmox_input'
    context.user_data['backup_pattern_mode'] = 'proxmox_wizard'

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° Proxmox*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р¤СЂР°РіРјРµРЅС‚С‹ СѓС‡РёС‚С‹РІР°СЋС‚СЃСЏ РІ СѓРєР°Р·Р°РЅРЅРѕРј РїРѕСЂСЏРґРєРµ.\n\n"
        "РџСЂРёРјРµСЂ С‚РµРјС‹:\n"
        "`vzdump backup status`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def add_mail_pattern_handler(update, context):
    """Р”РѕР±Р°РІРёС‚СЊ РїР°С‚С‚РµСЂРЅ РґР»СЏ Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'mail_input'
    context.user_data['backup_pattern_mode'] = 'mail_wizard'

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° РїРѕС‡С‚С‹*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р¤СЂР°РіРјРµРЅС‚С‹ СѓС‡РёС‚С‹РІР°СЋС‚СЃСЏ РІ СѓРєР°Р·Р°РЅРЅРѕРј РїРѕСЂСЏРґРєРµ.\n\n"
        "РџСЂРёРјРµСЂ С‚РµРјС‹:\n"
        "`Р‘СЌРєР°Рї Zimbra - 52G /backups/zimbra/2025-03-01`\n\n"
        "РџСЂРёРјРµСЂ С„СЂР°РіРјРµРЅС‚РѕРІ:\n"
        "`Р‘СЌРєР°Рї Zimbra; /backups/zimbra`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def show_stock_pattern_type_menu(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ РІС‹Р±РѕСЂ С‚РёРїР° РїР°С‚С‚РµСЂРЅР° РґР»СЏ РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    message = (
        "рџ“¦ *Р”РѕР±Р°РІР»РµРЅРёРµ РїР°С‚С‚РµСЂРЅР° РґР»СЏ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ*\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ, С‡С‚Рѕ РЅСѓР¶РЅРѕ РЅР°СЃС‚СЂРѕРёС‚СЊ:"
    )

    keyboard = [
        [InlineKeyboardButton("рџ§ѕ РўРµРјР° РїРёСЃСЊРјР°", callback_data='stock_pattern_select_subject')],
        [InlineKeyboardButton("рџ—‚пёЏ РСЃС‚РѕС‡РЅРёРє РѕС‚С‡РµС‚Р°", callback_data='stock_pattern_select_source')],
        [InlineKeyboardButton("рџ“Ћ РРјСЏ РІР»РѕР¶РµРЅРёСЏ", callback_data='stock_pattern_select_attachment')],
        [InlineKeyboardButton("рџ“„ РЎС‚СЂРѕРєР° С„Р°Р№Р»Р°", callback_data='stock_pattern_select_file_entry')],
        [InlineKeyboardButton("вњ… РЈСЃРїРµС€РЅР°СЏ Р·Р°РіСЂСѓР·РєР°", callback_data='stock_pattern_select_success')],
        [InlineKeyboardButton("рџ™€ РРіРЅРѕСЂРёСЂРѕРІР°С‚СЊ СЃС‚СЂРѕРєРё", callback_data='stock_pattern_select_ignore')],
        [InlineKeyboardButton("вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё", callback_data='stock_pattern_select_failure')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_patterns_stock'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def stock_pattern_select_handler(update, context, pattern_type: str):
    """Р—Р°РїСѓСЃС‚РёС‚СЊ РјР°СЃС‚РµСЂ РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‚РёРїР° РїР°С‚С‚РµСЂРЅР° РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'stock_input'
    if pattern_type == 'subject':
        context.user_data['backup_pattern_mode'] = 'stock_subject_wizard'
    elif pattern_type == 'source':
        context.user_data['backup_pattern_mode'] = 'stock_source_wizard'
    else:
        context.user_data['backup_pattern_mode'] = 'stock_log_wizard'
    context.user_data['backup_pattern_stock_type'] = pattern_type
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)
    context.user_data.pop('backup_pattern_stock_label', None)

    if pattern_type == 'subject':
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ С‚РµРјС‹*\n\n"
            "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
            "Р¤СЂР°РіРјРµРЅС‚С‹ СѓС‡РёС‚С‹РІР°СЋС‚СЃСЏ РІ СѓРєР°Р·Р°РЅРЅРѕРј РїРѕСЂСЏРґРєРµ.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`Р›РѕРіРё Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ РІ СЂР°Р±РѕС‡СѓСЋ Р±Р°Р·Сѓ 07:38:14`"
        )
    elif pattern_type == 'source':
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РёСЃС‚РѕС‡РЅРёРєР° РѕС‚С‡РµС‚Р°*\n\n"
            "Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РёСЃС‚РѕС‡РЅРёРєР° Рё С‚РµРјСѓ РїРёСЃСЊРјР° С‡РµСЂРµР· `|`.\n"
            "Р’ С‚РµРјРµ РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`Р¤РёР»РёР°Р» РњРѕСЃРєРІР° | Р›РѕРіРё Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ РІ СЂР°Р±РѕС‡СѓСЋ Р±Р°Р·Сѓ 07:38:14`"
        )
    elif pattern_type == 'attachment':
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РёРјРµРЅРё РІР»РѕР¶РµРЅРёСЏ*\n\n"
            "Р’РІРµРґРёС‚Рµ РёРјСЏ С„Р°Р№Р»Р° РёР»Рё С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`LogiLogistam.txt`"
        )
    elif pattern_type == 'file_entry':
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ СЃС‚СЂРѕРєРё С„Р°Р№Р»Р°*\n\n"
            "Р’РІРµРґРёС‚Рµ СЃС‚СЂРѕРєСѓ СЃ РЅР°Р·РІР°РЅРёРµРј РїРѕСЃС‚Р°РІС‰РёРєР° Рё РїСѓС‚РµРј Рє С„Р°Р№Р»Сѓ.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`19.01.26 07:35:36: Р—Р­РўРђ  РќРЎРљ  D:\\Obmen\\OCTATKu\\Р—Р­РўРђ\\РћСЃС‚Р°С‚РєРё Р—Р­РўРђ РќРЎРљ.csv`"
        )
    elif pattern_type == 'success':
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ СЃС‚СЂРѕРєРё СѓСЃРїРµС…Р°*\n\n"
            "Р’РІРµРґРёС‚Рµ СЃС‚СЂРѕРєСѓ СЃ СЂРµР·СѓР»СЊС‚Р°С‚РѕРј СѓСЃРїРµС€РЅРѕР№ Р·Р°РіСЂСѓР·РєРё.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`19.01.26 07:35:39: ***РћСЃС‚Р°С‚РєРё Р·Р°РіСЂСѓР¶РµРЅС‹!***   СЃС‚СЂРѕРє 348   07:35:39`"
        )
    elif pattern_type == 'ignore':
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РёРіРЅРѕСЂРёСЂСѓРµРјРѕР№ СЃС‚СЂРѕРєРё*\n\n"
            "Р’РІРµРґРёС‚Рµ СЃС‚СЂРѕРєСѓ РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
            "Р­С‚Рё СЃС‚СЂРѕРєРё Р±СѓРґСѓС‚ РїСЂРѕРїСѓСЃРєР°С‚СЊСЃСЏ РїСЂРё СЂР°Р·Р±РѕСЂРµ.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`Р’РЅРёРјР°РЅРёРµ! РћС€РёР±РєР° РІ РЅРѕРјРµРЅРєР»Р°С‚СѓСЂРµ РђСЂС‚РёРєСѓР»=`"
        )
    else:
        prompt = (
            "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ СЃС‚СЂРѕРєРё РѕС€РёР±РєРё*\n\n"
            "Р’РІРµРґРёС‚Рµ СЃС‚СЂРѕРєСѓ СЃ РѕС€РёР±РєРѕР№ РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n\n"
            "РџСЂРёРјРµСЂ:\n"
            "`--- РЅРµСѓРґР°С‡Р°!!! РїСѓСЃС‚Р°СЏ Р·Р°РіСЂСѓР·РєР°`"
        )

    query.edit_message_text(
        prompt,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def stock_pattern_retry_handler(update, context):
    """РџРѕРІС‚РѕСЂРёС‚СЊ РІРІРѕРґ РґР»СЏ РїР°С‚С‚РµСЂРЅРѕРІ РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    pattern_type = context.user_data.get('backup_pattern_stock_type', 'subject')
    stock_pattern_select_handler(update, context, pattern_type)

def stock_pattern_confirm_handler(update, context):
    """РџРѕРґС‚РІРµСЂРґРёС‚СЊ СЃРѕС…СЂР°РЅРµРЅРёРµ РїР°С‚С‚РµСЂРЅР° РѕСЃС‚Р°С‚РєРѕРІ."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    pattern_type = context.user_data.get('backup_pattern_stock_type')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    label = context.user_data.get('backup_pattern_stock_label')

    if not pattern or not pattern_type:
        query.edit_message_text(
            "вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ Р·Р°РЅРѕРІРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    try:
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
            VALUES (?, ?, ?, 1)
            """,
            (pattern_type, pattern, "stock_load")
        )
        conn.commit()

        source_label = context.user_data.get('backup_pattern_source', 'РјР°СЃС‚РµСЂ')
        label_text = f"РњРµС‚РєР°: *{label}*\n" if label else ""
        query.edit_message_text(
            "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
            "РљР°С‚РµРіРѕСЂРёСЏ: *stock_load*\n"
            f"РўРёРї: *{pattern_type}*\n"
            f"{label_text}"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
    finally:
        context.user_data.pop('adding_backup_pattern', None)
        context.user_data.pop('backup_pattern_stage', None)
        context.user_data.pop('backup_pattern_category', None)
        context.user_data.pop('backup_pattern_type', None)
        context.user_data.pop('backup_pattern_subject', None)
        context.user_data.pop('backup_pattern_mode', None)
        context.user_data.pop('backup_pattern_generated', None)
        context.user_data.pop('backup_pattern_source', None)
        context.user_data.pop('backup_pattern_stock_type', None)
        context.user_data.pop('backup_pattern_stock_label', None)

def edit_mail_default_pattern_handler(update, context):
    """РР·РјРµРЅРёС‚СЊ РґРµС„РѕР»С‚РЅС‹Р№ РїР°С‚С‚РµСЂРЅ РґР»СЏ Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹"""
    query = update.callback_query
    query.answer()

    fallback_patterns = _get_mail_fallback_patterns()
    current_pattern = fallback_patterns[0] if fallback_patterns else ""

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'pattern_only'
    context.user_data['backup_pattern_mode'] = 'mail'

    query.edit_message_text(
        "вњЏпёЏ *РР·РјРµРЅРµРЅРёРµ РїР°С‚С‚РµСЂРЅР° РїРѕС‡С‚С‹*\n\n"
        f"РўРµРєСѓС‰РёР№ РїР°С‚С‚РµСЂРЅ:\n`{current_pattern}`\n\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ regex РїР°С‚С‚РµСЂРЅ С‚РµРјС‹ РїРёСЃСЊРјР°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def mail_pattern_retry_handler(update, context):
    """РџРѕРІС‚РѕСЂРёС‚СЊ РІРІРѕРґ С‚РµРјС‹/С„СЂР°РіРјРµРЅС‚РѕРІ РґР»СЏ РїР°С‚С‚РµСЂРЅР° РїРѕС‡С‚С‹."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'mail_input'
    context.user_data['backup_pattern_mode'] = 'mail_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° РїРѕС‡С‚С‹*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р¤СЂР°РіРјРµРЅС‚С‹ СѓС‡РёС‚С‹РІР°СЋС‚СЃСЏ РІ СѓРєР°Р·Р°РЅРЅРѕРј РїРѕСЂСЏРґРєРµ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def mail_pattern_confirm_handler(update, context):
    """РџРѕРґС‚РІРµСЂРґРёС‚СЊ СЃРѕС…СЂР°РЅРµРЅРёРµ РїР°С‚С‚РµСЂРЅР° РїРѕС‡С‚С‹."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        query.edit_message_text(
            "вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ Р·Р°РЅРѕРІРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    try:
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
            VALUES (?, ?, ?, 1)
            """,
            ("subject", pattern, "mail")
        )
        conn.commit()

        source_label = context.user_data.get('backup_pattern_source', 'РјР°СЃС‚РµСЂ')
        query.edit_message_text(
            "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
            "РљР°С‚РµРіРѕСЂРёСЏ: *mail*\n"
            "РўРёРї: *subject*\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
    finally:
        context.user_data.pop('adding_backup_pattern', None)
        context.user_data.pop('backup_pattern_stage', None)
        context.user_data.pop('backup_pattern_category', None)
        context.user_data.pop('backup_pattern_type', None)
        context.user_data.pop('backup_pattern_subject', None)
        context.user_data.pop('backup_pattern_mode', None)
        context.user_data.pop('backup_pattern_generated', None)
        context.user_data.pop('backup_pattern_source', None)

def db_pattern_retry_handler(update, context):
    """РџРѕРІС‚РѕСЂРёС‚СЊ РІРІРѕРґ С‚РµРјС‹/С„СЂР°РіРјРµРЅС‚РѕРІ РґР»СЏ РїР°С‚С‚РµСЂРЅР° Р‘Р”."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'db_input'
    context.user_data['backup_pattern_mode'] = 'db_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)
    context.user_data.pop('backup_pattern_category', None)
    context.user_data.pop('backup_pattern_db_name', None)

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° Р‘Р”*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р’Рѕ С„СЂР°РіРјРµРЅС‚Р°С… РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ СѓРєР°Р¶РёС‚Рµ РёРјСЏ Р‘Р” РёР· РЅР°СЃС‚СЂРѕРµРє.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def _get_database_categories() -> list[str]:
    """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РєР°С‚РµРіРѕСЂРёР№ Р‘Р” РёР· РЅР°СЃС‚СЂРѕРµРє."""
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if not isinstance(db_config, dict):
        return []
    return sorted([key for key in db_config.keys() if isinstance(key, str)])

def _show_db_pattern_confirm(update, context):
    """РџРѕРєР°Р·Р°С‚СЊ СЌРєСЂР°РЅ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° Р‘Р” СЃ РІС‹Р±РѕСЂРѕРј РєР°С‚РµРіРѕСЂРёРё."""
    pattern = context.user_data.get('backup_pattern_generated')
    db_name = context.user_data.get('backup_pattern_db_name', '')
    category = context.user_data.get('backup_pattern_category', '')
    source_label = context.user_data.get('backup_pattern_source', 'РјР°СЃС‚РµСЂ')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        return

    categories = _get_database_categories()
    keyboard: list[list[InlineKeyboardButton]] = []
    if categories:
        row: list[InlineKeyboardButton] = []
        for category_name in categories:
            label = f"вњ… {category_name}" if category_name == category else category_name
            row.append(
                InlineKeyboardButton(
                    label,
                    callback_data=f"db_pattern_set_category_{category_name}"
                )
            )
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    keyboard.extend([
        [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='db_pattern_confirm')],
        [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='db_pattern_retry')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])

    message = (
        "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
        f"Р‘Р”: *{db_name}*\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
        f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n"
    )
    if categories:
        message += "\nР’С‹Р±РµСЂРёС‚Рµ РєР°С‚РµРіРѕСЂРёСЋ РїРµСЂРµРґ СЃРѕС…СЂР°РЅРµРЅРёРµРј:"
    else:
        message += "\nвљ пёЏ РќРµС‚ РґРѕСЃС‚СѓРїРЅС‹С… РєР°С‚РµРіРѕСЂРёР№ Р‘Р”."

    query = update.callback_query
    if query:
        query.answer()
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def db_pattern_set_category_handler(update, context, category: str):
    """Р’С‹Р±СЂР°С‚СЊ РєР°С‚РµРіРѕСЂРёСЋ РґР»СЏ РїР°С‚С‚РµСЂРЅР° Р‘Р”."""
    context.user_data['backup_pattern_category'] = category
    _show_db_pattern_confirm(update, context)

def db_pattern_confirm_handler(update, context):
    """РџРѕРґС‚РІРµСЂРґРёС‚СЊ СЃРѕС…СЂР°РЅРµРЅРёРµ РїР°С‚С‚РµСЂРЅР° Р‘Р”."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    category = context.user_data.get('backup_pattern_category')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern or not category:
        query.edit_message_text(
            "вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ Р·Р°РЅРѕРІРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    try:
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
            VALUES (?, ?, ?, 1)
            """,
            ("subject", pattern, category)
        )
        conn.commit()

        source_label = context.user_data.get('backup_pattern_source', 'РјР°СЃС‚РµСЂ')
        db_name = context.user_data.get('backup_pattern_db_name', '')
        db_info = f"Р‘Р”: *{db_name}*\n" if db_name else ""
        query.edit_message_text(
            "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
            f"{db_info}"
            f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
            "РўРёРї: *subject*\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
    finally:
        context.user_data.pop('adding_backup_pattern', None)
        context.user_data.pop('backup_pattern_stage', None)
        context.user_data.pop('backup_pattern_category', None)
        context.user_data.pop('backup_pattern_type', None)
        context.user_data.pop('backup_pattern_subject', None)
        context.user_data.pop('backup_pattern_mode', None)
        context.user_data.pop('backup_pattern_generated', None)
        context.user_data.pop('backup_pattern_source', None)
        context.user_data.pop('backup_pattern_db_name', None)

def edit_default_db_pattern_handler(update, context, category: str, index_value: str):
    """Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ РґРµС„РѕР»С‚РЅС‹Р№ РїР°С‚С‚РµСЂРЅ Р‘Р”."""
    query = update.callback_query
    query.answer()

    try:
        index = int(index_value)
    except ValueError:
        query.edit_message_text("вќЊ РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РёРЅРґРµРєСЃ РїР°С‚С‚РµСЂРЅР°.")
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        query.edit_message_text("вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ.")
        return

    current_pattern = patterns[index - 1]
    context.user_data['editing_default_db_pattern'] = True
    context.user_data['editing_default_db_category'] = category
    context.user_data['editing_default_db_index'] = index

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РґРµС„РѕР»С‚РЅРѕРіРѕ РїР°С‚С‚РµСЂРЅР° Р‘Р”*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РўРµРєСѓС‰РёР№ РїР°С‚С‚РµСЂРЅ: `{current_pattern}`\n\n"
        "Р’РІРµРґРёС‚Рµ РЅРѕРІС‹Р№ regex РїР°С‚С‚РµСЂРЅ С‚РµРјС‹ РїРёСЃСЊРјР°:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=back_callback),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def delete_default_db_pattern_handler(update, context, category: str, index_value: str):
    """РЈРґР°Р»РёС‚СЊ РґРµС„РѕР»С‚РЅС‹Р№ РїР°С‚С‚РµСЂРЅ Р‘Р”."""
    query = update.callback_query
    query.answer()

    try:
        index = int(index_value)
    except ValueError:
        query.edit_message_text("вќЊ РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РёРЅРґРµРєСЃ РїР°С‚С‚РµСЂРЅР°.")
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        query.edit_message_text("вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ.")
        return

    patterns.pop(index - 1)
    if patterns:
        db_patterns[category] = patterns
    else:
        db_patterns.pop(category, None)

    _save_database_patterns_setting(db_patterns)

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    query.edit_message_text(
        "вњ… Р”РµС„РѕР»С‚РЅС‹Р№ РїР°С‚С‚РµСЂРЅ СѓРґР°Р»С‘РЅ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def zfs_pattern_retry_handler(update, context):
    """РџРѕРІС‚РѕСЂРёС‚СЊ РІРІРѕРґ С‚РµРјС‹/С„СЂР°РіРјРµРЅС‚РѕРІ РґР»СЏ РїР°С‚С‚РµСЂРЅР° ZFS."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'zfs_input'
    context.user_data['backup_pattern_mode'] = 'zfs_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° ZFS*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р’Рѕ С„СЂР°РіРјРµРЅС‚Р°С… РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ СѓРєР°Р¶РёС‚Рµ РёРјСЏ ZFS СЃРµСЂРІРµСЂР° РёР· РЅР°СЃС‚СЂРѕРµРє.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def zfs_pattern_confirm_handler(update, context):
    """РџРѕРґС‚РІРµСЂРґРёС‚СЊ СЃРѕС…СЂР°РЅРµРЅРёРµ РїР°С‚С‚РµСЂРЅР° ZFS."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        query.edit_message_text(
            "вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ Р·Р°РЅРѕРІРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    try:
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
            VALUES (?, ?, ?, 1)
            """,
            ("subject", pattern, "zfs")
        )
        conn.commit()

        source_label = context.user_data.get('backup_pattern_source', 'РјР°СЃС‚РµСЂ')
        query.edit_message_text(
            "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
            "РљР°С‚РµРіРѕСЂРёСЏ: *zfs*\n"
            "РўРёРї: *subject*\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
    finally:
        context.user_data.pop('adding_backup_pattern', None)
        context.user_data.pop('backup_pattern_stage', None)
        context.user_data.pop('backup_pattern_category', None)
        context.user_data.pop('backup_pattern_type', None)
        context.user_data.pop('backup_pattern_subject', None)
        context.user_data.pop('backup_pattern_mode', None)
        context.user_data.pop('backup_pattern_generated', None)
        context.user_data.pop('backup_pattern_source', None)

def proxmox_pattern_retry_handler(update, context):
    """РџРѕРІС‚РѕСЂРёС‚СЊ РІРІРѕРґ С‚РµРјС‹/С„СЂР°РіРјРµРЅС‚РѕРІ РґР»СЏ РїР°С‚С‚РµСЂРЅР° Proxmox."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'proxmox_input'
    context.user_data['backup_pattern_mode'] = 'proxmox_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)

    query.edit_message_text(
        "рџ§™ *РњР°СЃС‚РµСЂ РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР° Proxmox*\n\n"
        "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° С†РµР»РёРєРѕРј РёР»Рё РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ С„СЂР°РіРјРµРЅС‚С‹ С‡РµСЂРµР· `;`/`,`.\n"
        "Р¤СЂР°РіРјРµРЅС‚С‹ СѓС‡РёС‚С‹РІР°СЋС‚СЃСЏ РІ СѓРєР°Р·Р°РЅРЅРѕРј РїРѕСЂСЏРґРєРµ.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def proxmox_pattern_confirm_handler(update, context):
    """РџРѕРґС‚РІРµСЂРґРёС‚СЊ СЃРѕС…СЂР°РЅРµРЅРёРµ РїР°С‚С‚РµСЂРЅР° Proxmox."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        query.edit_message_text(
            "вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ. РќР°С‡РЅРёС‚Рµ РґРѕР±Р°РІР»РµРЅРёРµ Р·Р°РЅРѕРІРѕ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback)],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    try:
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
            VALUES (?, ?, ?, 1)
            """,
            ("subject", pattern, "proxmox")
        )
        conn.commit()

        source_label = context.user_data.get('backup_pattern_source', 'РјР°СЃС‚РµСЂ')
        query.edit_message_text(
            "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
            "РљР°С‚РµРіРѕСЂРёСЏ: *proxmox*\n"
            "РўРёРї: *subject*\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
    finally:
        context.user_data.pop('adding_backup_pattern', None)
        context.user_data.pop('backup_pattern_stage', None)
        context.user_data.pop('backup_pattern_category', None)
        context.user_data.pop('backup_pattern_type', None)
        context.user_data.pop('backup_pattern_subject', None)
        context.user_data.pop('backup_pattern_mode', None)
        context.user_data.pop('backup_pattern_generated', None)
        context.user_data.pop('backup_pattern_source', None)

def view_patterns_handler(update, context):
    """РџСЂРѕСЃРјРѕС‚СЂ РїР°С‚С‚РµСЂРЅРѕРІ"""
    query = update.callback_query
    query.answer()

    conn = settings_manager.get_connection()
    cursor = conn.cursor()
    filter_mode = context.user_data.get('patterns_filter', 'all')
    if filter_mode == 'zfs':
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'zfs'
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == 'db':
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1
            AND category NOT IN ('mail', 'zfs', 'proxmox')
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == 'proxmox':
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1
            AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == 'mail':
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'mail'
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == 'stock_load':
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'stock_load'
            ORDER BY category, pattern_type, id
            """
        )
    else:
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1
            ORDER BY category, pattern_type, id
            """
        )
    rows = cursor.fetchall()

    title = context.user_data.get('patterns_title', "рџ“‹ *РџР°С‚С‚РµСЂРЅС‹*")
    display_rows = rows
    if filter_mode == 'db':
        display_rows = []
        for pattern_id, pattern_type, pattern, category in rows:
            if category == "database" and pattern_type.startswith("proxmox"):
                continue
            display_category = category
            display_type = pattern_type
            if category == "database" and pattern_type.startswith("database"):
                normalized = pattern_type
                while normalized.startswith("database"):
                    normalized = normalized[len("database"):]
                display_category = normalized or category
                display_type = "subject"
            display_rows.append((pattern_id, display_type, pattern, display_category))
    if filter_mode == 'proxmox':
        display_rows = []
        for pattern_id, pattern_type, pattern, category in rows:
            display_category = category
            display_type = pattern_type
            if category == "database" and pattern_type.startswith("proxmox"):
                normalized = pattern_type[len("proxmox"):]
                display_category = "proxmox"
                display_type = normalized or "subject"
            display_rows.append((pattern_id, display_type, pattern, display_category))
    if filter_mode == 'stock_load':
        display_rows = []
        for pattern_id, pattern_type, pattern, category in rows:
            display_category = category
            display_type = pattern_type
            if isinstance(pattern_type, str) and pattern_type.startswith("source:"):
                label = pattern_type.split("source:", 1)[1].strip()
                display_type = "source"
                if label:
                    display_type = f"source ({label})"
            display_rows.append((pattern_id, display_type, pattern, display_category))

    fallback_patterns = []
    fallback_db_patterns = {}
    fallback_stock_patterns: dict[str, list[str]] = {}
    if not display_rows and filter_mode == 'mail':
        fallback_patterns = _get_mail_fallback_patterns()
    if not display_rows and filter_mode == 'db':
        fallback_db_patterns = _get_database_fallback_patterns()
    if not display_rows and filter_mode == 'stock_load':
        fallback_stock_patterns = _get_stock_load_fallback_patterns()

    if not display_rows and not fallback_patterns and not fallback_db_patterns and not fallback_stock_patterns:
        message = f"{title}\n\nвќЊ РџР°С‚С‚РµСЂРЅС‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹."
    else:
        message = f"{title}\n\n"
        current_category = None
        for index, (pattern_id, pattern_type, pattern, category) in enumerate(display_rows, start=1):
            if category != current_category:
                if current_category is not None:
                    message += "\n"
            message += f"*{_escape_pattern_text(category)}*\n"
            current_category = category
            message += (
                f"{index}. {_escape_pattern_text(pattern_type)}: "
                f"`{_escape_pattern_text(pattern)}`\n"
            )
        if fallback_patterns:
            if rows:
                message += "\n"
            message += "*mail (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ)*\n"
            for index, pattern in enumerate(fallback_patterns, start=1):
                message += f"{index}. subject: `{_escape_pattern_text(pattern)}`\n"
        if fallback_db_patterns:
            if rows or fallback_patterns:
                message += "\n"
            message += "*database (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ)*\n"
            for category, patterns in fallback_db_patterns.items():
                message += f"*{_escape_pattern_text(category)}*\n"
                for index, pattern in enumerate(patterns, start=1):
                    message += f"{index}. subject: `{_escape_pattern_text(pattern)}`\n"
        if fallback_stock_patterns:
            if rows or fallback_patterns or fallback_db_patterns:
                message += "\n"
            message += "*stock_load (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ)*\n"
            for pattern_type, patterns in fallback_stock_patterns.items():
                message += f"*{_escape_pattern_text(pattern_type)}*\n"
                for index, pattern in enumerate(patterns, start=1):
                    message += (
                        f"{index}. {_escape_pattern_text(pattern_type)}: "
                        f"`{_escape_pattern_text(pattern)}`\n"
                    )

    keyboard = []
    for index, (pattern_id, pattern_type, pattern, category) in enumerate(display_rows, start=1):
        keyboard.append([
            InlineKeyboardButton(
                f"вњЏпёЏ {index}. {category}:{pattern_type}",
                callback_data=f"edit_pattern_{pattern_id}"
            ),
            InlineKeyboardButton(
                f"рџ—‘пёЏ {index}. {category}:{pattern_type}",
                callback_data=f"delete_pattern_{pattern_id}"
            )
        ])

    if fallback_patterns and filter_mode == 'mail':
        keyboard.append([
            InlineKeyboardButton("вњЏпёЏ РР·РјРµРЅРёС‚СЊ РґРµС„РѕР»С‚РЅС‹Р№ РїР°С‚С‚РµСЂРЅ", callback_data='edit_mail_default_pattern')
        ])
    if fallback_db_patterns and filter_mode == 'db':
        for category, patterns in fallback_db_patterns.items():
            for index, _ in enumerate(patterns, start=1):
                keyboard.append([
                    InlineKeyboardButton(
                        f"вњЏпёЏ {category} #{index}",
                        callback_data=f"db_default_edit_{category}__{index}"
                    ),
                    InlineKeyboardButton(
                        f"рџ—‘пёЏ {category} #{index}",
                        callback_data=f"db_default_delete_{category}__{index}"
                    )
                ])

    add_callback = context.user_data.get('patterns_add')
    if add_callback:
        keyboard.append([InlineKeyboardButton("вћ• Р”РѕР±Р°РІРёС‚СЊ РїР°С‚С‚РµСЂРЅ", callback_data=add_callback)])

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    keyboard.append([
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _get_database_category(db_name):
    """РџРѕР»СѓС‡РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РїРѕ РєР»СЋС‡Сѓ"""
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if not isinstance(db_config, dict):
        return "unknown"
    for category, databases in db_config.items():
        if isinstance(databases, dict) and db_name in databases:
            return category
    return "unknown"

def delete_pattern_handler(update, context, pattern_id):
    """РЈРґР°Р»РёС‚СЊ РїР°С‚С‚РµСЂРЅ"""
    query = update.callback_query
    query.answer()

    try:
        pattern_id_int = int(pattern_id)
    except ValueError:
        query.edit_message_text("вќЊ РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ РїР°С‚С‚РµСЂРЅР°.")
        return

    conn = settings_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE backup_patterns SET enabled = 0 WHERE id = ?",
        (pattern_id_int,)
    )
    conn.commit()

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    query.edit_message_text(
        "вњ… РџР°С‚С‚РµСЂРЅ СѓРґР°Р»С‘РЅ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def edit_pattern_handler(update, context, pattern_id):
    """Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ РїР°С‚С‚РµСЂРЅ"""
    query = update.callback_query
    query.answer()

    try:
        pattern_id_int = int(pattern_id)
    except ValueError:
        query.edit_message_text("вќЊ РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ РїР°С‚С‚РµСЂРЅР°.")
        return

    conn = settings_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, pattern_type, pattern, category
        FROM backup_patterns
        WHERE id = ? AND enabled = 1
        """,
        (pattern_id_int,)
    )
    row = cursor.fetchone()

    if not row:
        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        query.edit_message_text(
            "вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    _, pattern_type, pattern, category = row
    context.user_data['editing_backup_pattern'] = True
    context.user_data['editing_backup_pattern_id'] = pattern_id_int
    context.user_data['backup_pattern_category'] = category
    context.user_data['backup_pattern_type'] = pattern_type
    if category == 'zfs':
        context.user_data['backup_pattern_mode'] = 'zfs'
        context.user_data['backup_pattern_stage'] = 'pattern_only'
    elif category == 'proxmox':
        context.user_data['backup_pattern_mode'] = 'proxmox'
        context.user_data['backup_pattern_stage'] = 'pattern_only'
    elif category == 'mail':
        context.user_data['backup_pattern_mode'] = 'mail'
        context.user_data['backup_pattern_stage'] = 'pattern_only'
    elif category == 'stock_load':
        context.user_data['backup_pattern_mode'] = 'stock'
        context.user_data['backup_pattern_stage'] = 'pattern_only'
    else:
        context.user_data['backup_pattern_mode'] = 'db'
        context.user_data['backup_pattern_stage'] = 'subject'

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    if category in ('zfs', 'proxmox', 'mail'):
        prompt = "Р’РІРµРґРёС‚Рµ РїР°С‚С‚РµСЂРЅ С‚РµРјС‹ РїРёСЃСЊРјР°:"
    elif category == 'stock_load':
        prompt = "Р’РІРµРґРёС‚Рµ regex РїР°С‚С‚РµСЂРЅ РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‚РёРїР°:"
    else:
        prompt = "Р’РІРµРґРёС‚Рµ С‚РµРјСѓ РїРёСЃСЊРјР° (РєР°Рє РїСЂРёС…РѕРґРёС‚ РІ РїРѕС‡С‚Рµ):"

    query.edit_message_text(
        "вњЏпёЏ *Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РїР°С‚С‚РµСЂРЅР°*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РўРёРї: *{pattern_type}*\n"
        f"РўРµРєСѓС‰РёР№ РїР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
        f"{prompt}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("вќЊ РћС‚РјРµРЅР°", callback_data=back_callback),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

def handle_backup_pattern_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґРѕР±Р°РІР»РµРЅРёСЏ РїР°С‚С‚РµСЂРЅР°"""
    if 'adding_backup_pattern' not in context.user_data:
        return

    user_input = update.message.text.strip()
    stage = context.user_data.get('backup_pattern_stage', 'category')
    mode = context.user_data.get('backup_pattern_mode', 'db')

    if mode == 'db_wizard':
        if stage != 'db_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        db_names = _get_database_names()
        if not db_names:
            update.message.reply_text(
                "вќЊ Р‘Р°Р·С‹ РґР°РЅРЅС‹С… РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹. РЎРЅР°С‡Р°Р»Р° РґРѕР±Р°РІСЊС‚Рµ Р‘Р” РІ РЅР°СЃС‚СЂРѕР№РєР°С…."
            )
            context.user_data.pop('adding_backup_pattern', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_mode', None)
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern, db_name = _build_db_pattern_from_fragments(
                fragments,
                db_names,
            )
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            pattern, db_name = _build_db_pattern_from_subject(
                user_input,
                db_names,
            )
            source_label = "С‚РµРјР° РїРёСЃСЊРјР°"

        if not pattern or not db_name:
            update.message.reply_text(
                "вќЊ РќРµ РЅР°Р№РґРµРЅРѕ РёРјСЏ Р‘Р” РёР· РЅР°СЃС‚СЂРѕРµРє.\n"
                "Р”РѕР±Р°РІСЊС‚Рµ РІ С‚РµРјСѓ РёР»Рё С„СЂР°РіРјРµРЅС‚С‹ РёРјСЏ Р‘Р” Рё РїРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
            )
            return

        category = _get_database_category(db_name)
        if category == "unknown":
            update.message.reply_text(
                "вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ Р‘Р”.\n"
                "РџСЂРѕРІРµСЂСЊС‚Рµ, С‡С‚Рѕ Р‘Р” РµСЃС‚СЊ РІ РЅР°СЃС‚СЂРѕР№РєР°С…."
            )
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'db_confirm'
        context.user_data['backup_pattern_category'] = category
        context.user_data['backup_pattern_db_name'] = db_name

        _show_db_pattern_confirm(update, context)
        return

    if mode == 'zfs_wizard':
        if stage != 'zfs_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        server_names = _get_zfs_server_names()
        if not server_names:
            update.message.reply_text(
                "вќЊ ZFS СЃРµСЂРІРµСЂС‹ РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹. РЎРЅР°С‡Р°Р»Р° РґРѕР±Р°РІСЊС‚Рµ СЃРµСЂРІРµСЂС‹ РІ РЅР°СЃС‚СЂРѕР№РєР°С… ZFS."
            )
            context.user_data.pop('adding_backup_pattern', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_mode', None)
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern, has_server = _build_zfs_pattern_from_fragments(
                fragments,
                server_names,
            )
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            pattern, has_server = _build_zfs_pattern_from_subject(
                user_input,
                server_names,
            )
            source_label = "С‚РµРјР° РїРёСЃСЊРјР°"

        if not pattern:
            update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР±СЂР°С‚СЊ РїР°С‚С‚РµСЂРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        if not has_server:
            update.message.reply_text(
                "вќЊ РќРµ РЅР°Р№РґРµРЅРѕ РёРјСЏ ZFS СЃРµСЂРІРµСЂР° РёР· РЅР°СЃС‚СЂРѕРµРє.\n"
                "Р”РѕР±Р°РІСЊС‚Рµ РІ С‚РµРјСѓ РёР»Рё С„СЂР°РіРјРµРЅС‚С‹ РёРјСЏ СЃРµСЂРІРµСЂР° Рё РїРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
            )
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'zfs_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
            "РЎРѕС…СЂР°РЅРёС‚СЊ?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='zfs_pattern_confirm')],
                [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='zfs_pattern_retry')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    if mode == 'mail_wizard':
        if stage != 'mail_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_mail_pattern_from_fragments(fragments)
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            pattern = _build_mail_pattern_from_subject(user_input)
            source_label = "С‚РµРјР° РїРёСЃСЊРјР°"

        if not pattern:
            update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР±СЂР°С‚СЊ РїР°С‚С‚РµСЂРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'mail_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
            "РЎРѕС…СЂР°РЅРёС‚СЊ?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='mail_pattern_confirm')],
                [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='mail_pattern_retry')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    if mode == 'stock_subject_wizard':
        if stage != 'stock_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            pattern = _build_stock_subject_pattern(user_input)
            source_label = "С‚РµРјР° РїРёСЃСЊРјР°"

        if not pattern:
            update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР±СЂР°С‚СЊ РїР°С‚С‚РµСЂРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'stock_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
            "РЎРѕС…СЂР°РЅРёС‚СЊ?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='stock_pattern_confirm')],
                [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='stock_pattern_retry')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    if mode == 'stock_source_wizard':
        if stage != 'stock_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        if "|" not in user_input:
            update.message.reply_text(
                "вќЊ РќСѓР¶РµРЅ С„РѕСЂРјР°С‚ `РќР°Р·РІР°РЅРёРµ | РўРµРјР° РїРёСЃСЊРјР°`. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
            )
            return

        label_raw, subject_raw = [part.strip() for part in user_input.split("|", 1)]
        if not label_raw or not subject_raw:
            update.message.reply_text(
                "вќЊ РќР°Р·РІР°РЅРёРµ Рё С‚РµРјР° РЅРµ РјРѕРіСѓС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹РјРё. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
            )
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", subject_raw)]
        fragments = [fragment for fragment in fragments if fragment]
        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            pattern = _build_stock_subject_pattern(subject_raw)
            source_label = "С‚РµРјР° РїРёСЃСЊРјР°"

        if not pattern:
            update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР±СЂР°С‚СЊ РїР°С‚С‚РµСЂРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'stock_confirm'
        context.user_data['backup_pattern_stock_type'] = f"source:{label_raw}"
        context.user_data['backup_pattern_stock_label'] = label_raw

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РњРµС‚РєР°: *{label_raw}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
            "РЎРѕС…СЂР°РЅРёС‚СЊ?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='stock_pattern_confirm')],
                [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='stock_pattern_retry')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    if mode == 'stock_log_wizard':
        if stage != 'stock_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        pattern_type = context.user_data.get('backup_pattern_stock_type', 'file_entry')
        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            if pattern_type == 'success':
                pattern = _build_stock_success_pattern(user_input)
                source_label = "СЃС‚СЂРѕРєР° Р»РѕРіР°"
            elif pattern_type == 'attachment':
                pattern = re.escape(user_input.strip()) + r"$"
                source_label = "РёРјСЏ С„Р°Р№Р»Р°"
            elif pattern_type == 'ignore':
                pattern = _build_stock_pattern_from_fragments([user_input])
                source_label = "СЃС‚СЂРѕРєР° Р»РѕРіР°"
            elif pattern_type == 'failure':
                pattern = _build_stock_pattern_from_fragments([user_input])
                source_label = "СЃС‚СЂРѕРєР° Р»РѕРіР°"
            else:
                pattern = (
                    r"^\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}:\s+"
                    r"(?P<supplier>.+?)\s{2,}(?P<path>[A-Za-z]:\\.+)$"
                )
                source_label = "СЃС‚СЂРѕРєР° Р»РѕРіР°"

        if not pattern:
            update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР±СЂР°С‚СЊ РїР°С‚С‚РµСЂРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'stock_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
            "РЎРѕС…СЂР°РЅРёС‚СЊ?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='stock_pattern_confirm')],
                [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='stock_pattern_retry')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    if mode == 'proxmox_wizard':
        if stage != 'proxmox_input':
            update.message.reply_text("вќЊ РќРµРІРµСЂРЅС‹Р№ С€Р°Рі РјР°СЃС‚РµСЂР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°.")
            return

        if not user_input:
            update.message.reply_text("вќЊ Р’РІРѕРґ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_mail_pattern_from_fragments(fragments)
            source_label = "С„СЂР°РіРјРµРЅС‚С‹"
        else:
            pattern = _build_mail_pattern_from_subject(user_input)
            source_label = "С‚РµРјР° РїРёСЃСЊРјР°"

        if not pattern:
            update.message.reply_text("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР±СЂР°С‚СЊ РїР°С‚С‚РµСЂРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'proxmox_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "вњ… *Р§РµСЂРЅРѕРІРёРє РїР°С‚С‚РµСЂРЅР° РіРѕС‚РѕРІ!*\n\n"
            f"РСЃС‚РѕС‡РЅРёРє: *{source_label}*\n"
            f"РџР°С‚С‚РµСЂРЅ: `{pattern}`\n\n"
            "РЎРѕС…СЂР°РЅРёС‚СЊ?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("вњ… РЎРѕС…СЂР°РЅРёС‚СЊ", callback_data='proxmox_pattern_confirm')],
                [InlineKeyboardButton("вњЏпёЏ Р’РІРµСЃС‚Рё Р·Р°РЅРѕРІРѕ", callback_data='proxmox_pattern_retry')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        return

    if mode in ('zfs', 'proxmox', 'mail'):
        if not user_input:
            update.message.reply_text("вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        pattern = user_input
        pattern_type = "subject"
        if mode == 'zfs':
            category = 'zfs'
        elif mode == 'proxmox':
            category = 'proxmox'
        else:
            category = 'mail'
        back_callback = context.user_data.get('patterns_back', 'settings_backup')

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (pattern_type, pattern, category)
            )
            conn.commit()

            update.message.reply_text(
                "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
                f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
                f"РўРёРї: *{pattern_type}*\n"
                f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                     InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
        finally:
            context.user_data.pop('adding_backup_pattern', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_category', None)
            context.user_data.pop('backup_pattern_type', None)
            context.user_data.pop('backup_pattern_subject', None)
            context.user_data.pop('backup_pattern_mode', None)
        return

    if stage == 'subject':
        if not user_input:
            update.message.reply_text("вќЊ РўРµРјР° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚РѕР№. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return
        context.user_data['backup_pattern_subject'] = user_input
        context.user_data['backup_pattern_stage'] = 'db_name'
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РёРјСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РёР· С‚РµРјС‹ РїРёСЃСЊРјР°:")
        return

    if stage == 'db_name':
        if not user_input:
            update.message.reply_text("вќЊ РРјСЏ Р±Р°Р·С‹ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        subject = context.user_data.get('backup_pattern_subject')
        db_name = user_input
        escaped_subject = re.escape(subject)
        escaped_db_name = re.escape(db_name)
        if escaped_db_name not in escaped_subject:
            update.message.reply_text(
                "вќЊ РРјСЏ Р±Р°Р·С‹ РЅРµ РЅР°Р№РґРµРЅРѕ РІ С‚РµРјРµ РїРёСЃСЊРјР°. РџСЂРѕРІРµСЂСЊС‚Рµ РІРІРѕРґ Рё РїРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
            )
            return

        pattern = escaped_subject.replace(escaped_db_name, r"([\w.-]+)")
        pattern_type = "subject"
        category = _get_database_category(db_name)

        back_callback = context.user_data.get('patterns_back', 'settings_backup')

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (pattern_type, pattern, category)
            )
            conn.commit()

            update.message.reply_text(
                "вњ… *РџР°С‚С‚РµСЂРЅ РґРѕР±Р°РІР»РµРЅ!*\n\n"
                f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
                f"РўРёРї: *{pattern_type}*\n"
                f"РџР°С‚С‚РµСЂРЅ: `{pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                     InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
        finally:
            context.user_data.pop('adding_backup_pattern', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_category', None)
            context.user_data.pop('backup_pattern_type', None)
            context.user_data.pop('backup_pattern_subject', None)
            context.user_data.pop('backup_pattern_mode', None)

def handle_backup_pattern_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РїР°С‚С‚РµСЂРЅР°"""
    if 'editing_backup_pattern' not in context.user_data:
        return

    new_pattern = update.message.text.strip()
    stage = context.user_data.get('backup_pattern_stage', 'subject')
    mode = context.user_data.get('backup_pattern_mode', 'db')

    if mode in ('zfs', 'proxmox', 'mail', 'stock'):
        if not new_pattern:
            update.message.reply_text("вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        pattern_id = context.user_data.get('editing_backup_pattern_id')
        if not pattern_id:
            update.message.reply_text("вќЊ РќРµ РЅР°Р№РґРµРЅ РїР°С‚С‚РµСЂРЅ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ.")
            context.user_data.pop('editing_backup_pattern', None)
            return

        if mode == 'zfs':
            category = 'zfs'
        elif mode == 'proxmox':
            category = 'proxmox'
        elif mode == 'mail':
            category = 'mail'
        else:
            category = 'stock_load'
        pattern_type = context.user_data.get('backup_pattern_type', 'subject')
        back_callback = context.user_data.get('patterns_back', 'settings_backup')

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern = ?, category = ?, pattern_type = ?
                WHERE id = ?
                """,
                (new_pattern, category, pattern_type, pattern_id)
            )
            conn.commit()

            update.message.reply_text(
                "вњ… *РџР°С‚С‚РµСЂРЅ РѕР±РЅРѕРІР»С‘РЅ!*\n\n"
                f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
                f"РўРёРї: *{pattern_type}*\n"
                f"РџР°С‚С‚РµСЂРЅ: `{new_pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                     InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
        finally:
            context.user_data.pop('editing_backup_pattern', None)
            context.user_data.pop('editing_backup_pattern_id', None)
            context.user_data.pop('backup_pattern_category', None)
            context.user_data.pop('backup_pattern_type', None)
            context.user_data.pop('backup_pattern_subject', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_mode', None)
        return

    if stage == 'subject':
        if not new_pattern:
            update.message.reply_text("вќЊ РўРµРјР° РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚РѕР№. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return
        context.user_data['backup_pattern_subject'] = new_pattern
        context.user_data['backup_pattern_stage'] = 'db_name'
        update.message.reply_text("Р’РІРµРґРёС‚Рµ РёРјСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РёР· С‚РµРјС‹ РїРёСЃСЊРјР°:")
        return

    if stage == 'db_name':
        if not new_pattern:
            update.message.reply_text("вќЊ РРјСЏ Р±Р°Р·С‹ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
            return

        subject = context.user_data.get('backup_pattern_subject')
        db_name = new_pattern
        escaped_subject = re.escape(subject)
        escaped_db_name = re.escape(db_name)
        if escaped_db_name not in escaped_subject:
            update.message.reply_text(
                "вќЊ РРјСЏ Р±Р°Р·С‹ РЅРµ РЅР°Р№РґРµРЅРѕ РІ С‚РµРјРµ РїРёСЃСЊРјР°. РџСЂРѕРІРµСЂСЊС‚Рµ РІРІРѕРґ Рё РїРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:"
            )
            return

        pattern_id = context.user_data.get('editing_backup_pattern_id')
        if not pattern_id:
            update.message.reply_text("вќЊ РќРµ РЅР°Р№РґРµРЅ РїР°С‚С‚РµСЂРЅ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ.")
            context.user_data.pop('editing_backup_pattern', None)
            return

        new_pattern = escaped_subject.replace(escaped_db_name, r"([\w.-]+)")
        category = _get_database_category(db_name)
        pattern_type = "subject"

        back_callback = context.user_data.get('patterns_back', 'settings_backup')

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern = ?, category = ?, pattern_type = ?
                WHERE id = ?
                """,
                (new_pattern, category, pattern_type, pattern_id)
            )
            conn.commit()

            update.message.reply_text(
                "вњ… *РџР°С‚С‚РµСЂРЅ РѕР±РЅРѕРІР»С‘РЅ!*\n\n"
                f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
                f"РўРёРї: *{pattern_type}*\n"
                f"РџР°С‚С‚РµСЂРЅ: `{new_pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                    [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
                     InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ: {e}")
        finally:
            context.user_data.pop('editing_backup_pattern', None)
            context.user_data.pop('editing_backup_pattern_id', None)
            context.user_data.pop('backup_pattern_category', None)
            context.user_data.pop('backup_pattern_type', None)
            context.user_data.pop('backup_pattern_subject', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_mode', None)
    
def handle_default_db_pattern_edit_input(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РґРµС„РѕР»С‚РЅРѕРіРѕ РїР°С‚С‚РµСЂРЅР° Р‘Р”."""
    new_pattern = update.message.text.strip()
    if not new_pattern:
        update.message.reply_text("вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР°:")
        return

    category = context.user_data.get('editing_default_db_category')
    index = context.user_data.get('editing_default_db_index')
    if not category or not index:
        update.message.reply_text("вќЊ РќРµ РЅР°Р№РґРµРЅ РїР°С‚С‚РµСЂРЅ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ.")
        context.user_data.pop('editing_default_db_pattern', None)
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        update.message.reply_text("вќЊ РџР°С‚С‚РµСЂРЅ РЅРµ РЅР°Р№РґРµРЅ.")
        context.user_data.pop('editing_default_db_pattern', None)
        return

    patterns[index - 1] = new_pattern
    db_patterns[category] = patterns
    _save_database_patterns_setting(db_patterns)

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    update.message.reply_text(
        "вњ… *РџР°С‚С‚РµСЂРЅ РѕР±РЅРѕРІР»С‘РЅ!*\n\n"
        f"РљР°С‚РµРіРѕСЂРёСЏ: *{category}*\n"
        f"РџР°С‚С‚РµСЂРЅ: `{new_pattern}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_callback),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_default_db_pattern', None)
    context.user_data.pop('editing_default_db_category', None)
    context.user_data.pop('editing_default_db_index', None)
