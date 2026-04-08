"""
/bot/handlers/settings_handlers.py
Server Monitoring System v8.45.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for managing settings via a bot
Система мониторинга серверов
Версия: 8.45.2
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики для управления настройками через бота
"""

import sqlite3
from datetime import datetime
import ast

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
from urllib.parse import quote, unquote

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
    'settings_patterns_db_from_backup',
}

debug_logger = debug_log

def _normalize_proxmox_hosts(raw_hosts) -> dict:
    """Нормализует PROXMOX_HOSTS к словарю для всех входных форматов."""
    if isinstance(raw_hosts, dict):
        return raw_hosts
    if isinstance(raw_hosts, str):
        try:
            parsed_hosts = json.loads(raw_hosts)
        except Exception:
            try:
                parsed_hosts = ast.literal_eval(raw_hosts)
            except Exception:
                parsed_hosts = {}
        return parsed_hosts if isinstance(parsed_hosts, dict) else {}
    return {}

def _get_proxmox_hosts_for_settings() -> dict:
    """Получить PROXMOX_HOSTS с fallback, как в мобильном API настроек."""
    proxmox_hosts = _normalize_proxmox_hosts(settings_manager.get_setting('PROXMOX_HOSTS', {}))
    if proxmox_hosts:
        return proxmox_hosts

    try:
        from config.db_settings import PROXMOX_HOSTS as runtime_proxmox_hosts
    except Exception:
        runtime_proxmox_hosts = {}
    runtime_proxmox_hosts = _normalize_proxmox_hosts(runtime_proxmox_hosts)
    if runtime_proxmox_hosts:
        return runtime_proxmox_hosts

    try:
        from config.settings import PROXMOX_HOSTS as fallback_proxmox_hosts
    except Exception:
        fallback_proxmox_hosts = {}
    return _normalize_proxmox_hosts(fallback_proxmox_hosts)

def _safe_query_answer(query, text: str | None = None, **kwargs) -> None:
    try:
        if text is None:
            query.answer(**kwargs)
        else:
            query.answer(text, **kwargs)
    except (BadRequest, TelegramError):
        pass

def _build_db_monitor_toggle_callback(context, encoded_category: str, encoded_db_key: str) -> str:
    """Собирает короткий callback_data для переключателя мониторинга БД."""
    toggle_map = context.user_data.setdefault('settings_db_toggle_map', {})
    token = f"k{len(toggle_map)}"
    toggle_map[token] = f"{encoded_category}__{encoded_db_key}"
    return f"settings_db_toggle_monitor_{token}"


def _get_disabled_db_monitors_settings() -> set[tuple[str, str]]:
    """Получить пары (backup_type, db_name), отключённые в мониторинге бэкапов БД."""
    raw_disabled = settings_manager.get_setting('DATABASE_MONITORING_DISABLED', [], use_cache=False)
    if isinstance(raw_disabled, str):
        raw_disabled = [raw_disabled]
    if not isinstance(raw_disabled, list):
        return set()

    disabled_pairs: set[tuple[str, str]] = set()
    for item in raw_disabled:
        value = str(item or '').strip()
        if '__' not in value:
            continue
        backup_type, db_name = value.split('__', 1)
        backup_type = backup_type.strip()
        db_name = db_name.strip()
        if backup_type and db_name:
            disabled_pairs.add((backup_type, db_name))
    return disabled_pairs


def _toggle_database_monitoring_settings(backup_type: str, db_name: str) -> bool:
    """Переключить мониторинг БД. Возвращает True, если мониторинг включён после переключения."""
    backup_type = str(backup_type or '').strip()
    db_name = str(db_name or '').strip()
    if not backup_type or not db_name:
        raise ValueError("Не указан тип или имя базы")

    disabled_pairs = _get_disabled_db_monitors_settings()
    pair = (backup_type, db_name)
    if pair in disabled_pairs:
        disabled_pairs.remove(pair)
        now_enabled = True
    else:
        disabled_pairs.add(pair)
        now_enabled = False

    serialized = sorted(f"{item_type}__{item_name}" for item_type, item_name in disabled_pairs)
    settings_manager.set_setting('DATABASE_MONITORING_DISABLED', serialized, category='backup', data_type='auto')
    return now_enabled

def _get_mail_fallback_patterns() -> list:
    """Получить запасные паттерны для бэкапов почты."""
    default_pattern = (
        r"^\s*бэкап\s+zimbra\s*-\s*"
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
    """Экранирует текст для Markdown."""
    return escape_markdown(str(text or ""), version=1)

def _format_current_hint(value, default: str = "не задано") -> str:
    """Сформировать подсказку для текущего значения."""
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    return str(value)

def _format_archive_cleanup_days(value) -> str:
    """Сформировать отображение периода очистки архива."""
    try:
        days = int(str(value).strip())
    except (TypeError, ValueError):
        days = 0
    if days <= 0:
        return "выключено"
    return f"{days} дн."

def _build_mail_pattern_from_subject(subject: str) -> str:
    """Собрать regex паттерн по теме письма."""
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
    """Собрать regex паттерн из обязательных фрагментов."""
    cleaned = [fragment.strip() for fragment in fragments if fragment.strip()]
    if not cleaned:
        return ""
    escaped_parts = [re.escape(fragment) for fragment in cleaned]
    return r".*".join(escaped_parts)

def _build_stock_subject_pattern(subject: str) -> str:
    """Собрать regex паттерн для темы письма загрузки остатков."""
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
    """Собрать regex паттерн для остатков из обязательных фрагментов."""
    return _build_mail_pattern_from_fragments(fragments)

def _build_stock_success_pattern(sample: str) -> str:
    """Собрать regex паттерн успеха по примеру строки."""
    normalized = sample.strip()
    if not normalized:
        return ""

    date_regex = r"\b\d{2}\.\d{2}\.\d{2}\b"
    time_regex = r"\b\d{2}:\d{2}:\d{2}\b"

    draft = re.sub(date_regex, "__DATE__", normalized)
    draft = re.sub(time_regex, "__TIME__", draft)
    draft = re.sub(r"(строк\s+)\d+", r"\1__ROWS__", draft, flags=re.IGNORECASE)

    escaped = re.escape(draft)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)

    escaped = escaped.replace(re.escape("__DATE__"), r"\d{2}\.\d{2}\.\d{2}")
    escaped = escaped.replace(re.escape("__TIME__"), r"\d{2}:\d{2}:\d{2}")
    escaped = escaped.replace(re.escape("__ROWS__"), r"(?P<rows>\d+)")
    return escaped

def _get_stock_load_fallback_patterns() -> dict[str, list[str]]:
    """Получить запасные паттерны для загрузки остатков."""
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
    """Получить запасные паттерны для бэкапов БД."""
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
    """Получить полные паттерны из настроек."""
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
    """Получить паттерны БД из настроек в нормализованном виде."""
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
    """Сохранить паттерны БД в настройках."""
    raw_patterns = _get_backup_patterns_setting()
    raw_patterns["database"] = db_patterns
    settings_manager.set_setting('BACKUP_PATTERNS', raw_patterns)

def _get_database_names() -> list[str]:
    """Получить список имён БД из настроек."""
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if not isinstance(db_config, dict):
        return []

    names: list[str] = []
    for databases in db_config.values():
        if isinstance(databases, dict):
            names.extend([name for name in databases.keys() if isinstance(name, str)])
    return names

def _inject_db_placeholder(text: str, db_names: list[str]) -> tuple[str, str | None]:
    """Подменить имя БД на плейсхолдер, если найдено."""
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
    """Собрать regex паттерн БД по теме письма."""
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
    """Собрать regex паттерн БД из обязательных фрагментов."""
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
    """Получить список имён ZFS серверов из настроек."""
    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if isinstance(zfs_servers, dict):
        return [name for name in zfs_servers.keys() if isinstance(name, str)]
    return []

def _inject_server_placeholder(text: str, server_names: list[str]) -> tuple[str, bool]:
    """Подменить имя сервера на плейсхолдер, если найдено."""
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
    """Собрать regex паттерн ZFS по теме письма."""
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
    """Собрать regex паттерн ZFS из обязательных фрагментов."""
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
    """Команда управления настройками"""
    keyboard = [
        [InlineKeyboardButton("🤖 Настройки бота", callback_data='settings_telegram')],
        [InlineKeyboardButton("⏰ Временные настройки", callback_data='settings_time')],
        [InlineKeyboardButton("🔧 Мониторинг", callback_data='settings_monitoring')],
    ]

    keyboard.extend([
        [InlineKeyboardButton("🔐 Аутентификация", callback_data='settings_auth')],
        [InlineKeyboardButton("🖥️ Серверы", callback_data='settings_servers')],
    ])

    keyboard.append([InlineKeyboardButton("🧩 Расширения", callback_data='settings_extensions')])

    if extension_manager.is_extension_enabled('web_interface'):
        keyboard.append([InlineKeyboardButton("🌐 Веб-интерфейс", callback_data='settings_web')])

    keyboard.extend([
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    if update.message:
        update.message.reply_text(
            "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.callback_query.edit_message_text(
            "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def show_telegram_settings(update, context):
    """Показать настройки Telegram - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    token = settings_manager.get_setting('TELEGRAM_TOKEN', '')
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    token_display = "🟢 Установлен" if token else "🔴 Не установлен"
    chats_display = f"{len(chat_ids)} чатов" if chat_ids else "🔴 Не настроены"

    message = (
        "🤖 *Настройки Telegram*\n\n"
        f"• Токен бота: {token_display}\n"
        f"• ID чатов: {chats_display}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 Установить токен", callback_data='set_telegram_token')],
        [InlineKeyboardButton("💬 Управление чатами", callback_data='manage_chats')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_monitoring_settings(update, context):
    """Показать настройки мониторинга - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    check_interval = settings_manager.get_setting('CHECK_INTERVAL', 60)
    max_fail_time = settings_manager.get_setting('MAX_FAIL_TIME', 900)
    
    # Новые настройки таймаутов
    windows_2025_timeout = settings_manager.get_setting('WINDOWS_2025_TIMEOUT', 35)
    domain_timeout = settings_manager.get_setting('DOMAIN_SERVERS_TIMEOUT', 20)
    admin_timeout = settings_manager.get_setting('ADMIN_SERVERS_TIMEOUT', 25)
    standard_timeout = settings_manager.get_setting('STANDARD_WINDOWS_TIMEOUT', 30)
    linux_timeout = settings_manager.get_setting('LINUX_TIMEOUT', 15)
    
    message = (
        "🔧 *Настройки мониторинга*\n\n"
        f"• Интервал проверки: {check_interval} сек\n"
        f"• Макс. время простоя: {max_fail_time} сек\n\n"
        "*Таймауты серверов:*\n"
        f"• Windows 2025: {windows_2025_timeout} сек\n"
        f"• Доменные серверы: {domain_timeout} сек\n"
        f"• Admin серверы: {admin_timeout} сек\n"
        f"• Стандартные Windows: {standard_timeout} сек\n"
        f"• Linux серверы: {linux_timeout} сек\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("⏱️ Интервал проверки", callback_data='set_check_interval')],
        [InlineKeyboardButton("🚨 Макс. время простоя", callback_data='set_max_fail_time')],
        [InlineKeyboardButton("⏰ Таймауты серверов", callback_data='server_timeouts')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_time_settings(update, context):
    """Показать временные настройки"""
    query = update.callback_query
    query.answer()
    
    silent_start = settings_manager.get_setting('SILENT_START', 20)
    silent_end = settings_manager.get_setting('SILENT_END', 9)
    data_collection = settings_manager.get_setting('DATA_COLLECTION_TIME', '08:30')
    
    message = (
        "⏰ *Временные настройки*\n\n"
        f"• Тихий режим: {silent_start}:00 - {silent_end}:00\n"
        f"• Сбор данных: {data_collection}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔇 Начало тихого режима", callback_data='set_silent_start')],
        [InlineKeyboardButton("🔊 Конец тихого режима", callback_data='set_silent_end')],
        [InlineKeyboardButton("📊 Время сбора данных", callback_data='set_data_collection')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_resource_settings(update, context):
    """Показать настройки ресурсов"""
    query = update.callback_query
    query.answer()
    
    cpu_warning = settings_manager.get_setting('CPU_WARNING', 80)
    cpu_critical = settings_manager.get_setting('CPU_CRITICAL', 90)
    ram_warning = settings_manager.get_setting('RAM_WARNING', 85)
    ram_critical = settings_manager.get_setting('RAM_CRITICAL', 95)
    disk_warning = settings_manager.get_setting('DISK_WARNING', 80)
    disk_critical = settings_manager.get_setting('DISK_CRITICAL', 90)
    
    message = (
        "💻 *Настройки ресурсов*\n\n"
        f"• CPU предупреждение: {cpu_warning}%\n"
        f"• CPU критический: {cpu_critical}%\n"
        f"• RAM предупреждение: {ram_warning}%\n"
        f"• RAM критический: {ram_critical}%\n"
        f"• Disk предупреждение: {disk_warning}%\n"
        f"• Disk критический: {disk_critical}%\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💻 CPU предупреждение", callback_data='set_cpu_warning')],
        [InlineKeyboardButton("💻 CPU критический", callback_data='set_cpu_critical')],
        [InlineKeyboardButton("🧠 RAM предупреждение", callback_data='set_ram_warning')],
        [InlineKeyboardButton("🧠 RAM критический", callback_data='set_ram_critical')],
        [InlineKeyboardButton("💾 Disk предупреждение", callback_data='set_disk_warning')],
        [InlineKeyboardButton("💾 Disk критический", callback_data='set_disk_critical')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_settings(update, context):
    """Показать настройки бэкапов - С ИЗМЕНЕННЫМ CALLBACK"""
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
        "💾 *Настройки бэкапов*\n\n"
        f"• Алерты через: {backup_alert_hours}ч\n"
        f"• Устаревание через: {backup_stale_hours}ч\n"
        f"• Категории БД: {len(db_categories)}\n\n"
        f"• Proxmox хосты: {proxmox_count}\n\n"
        f"• ZFS серверы: {zfs_count}\n\n"
        "Выберите раздел для настройки:"
    )
    
    keyboard = [
        [InlineKeyboardButton("⏰ Временные интервалы", callback_data='backup_times')],
    ]

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("🖥️ Proxmox бэкапы", callback_data='settings_backup_proxmox')])
        keyboard.append([InlineKeyboardButton("🖥️ Паттерны Proxmox", callback_data='settings_patterns_proxmox')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("🗃️ Базы данных", callback_data='settings_db_main')])
        keyboard.append([InlineKeyboardButton("🗃️ Паттерны БД", callback_data='settings_patterns_db')])

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append([InlineKeyboardButton("🧊 ZFS", callback_data='settings_zfs')])

    keyboard.extend([
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_proxmox_backup_settings(update, context):
    """Показать настройки бэкапов Proxmox в разделе расширений"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()
    proxmox_count = len(proxmox_hosts)

    message = (
        "🖥️ *Бэкапы Proxmox*\n\n"
        f"Хостов в списке: {proxmox_count}\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("📋 Хосты", callback_data='settings_backup_proxmox')],
        [InlineKeyboardButton("🔍 Паттерны", callback_data='settings_patterns_proxmox')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_database_backup_settings(update, context):
    """Показать настройки бэкапов БД в разделе расширений"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    db_categories = list(db_config.keys()) if isinstance(db_config, dict) else []

    message = (
        "🗃️ *Бэкапы БД*\n\n"
        f"Категорий: {len(db_categories)}\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("📋 Базы", callback_data='settings_db_main')],
        [InlineKeyboardButton("🔍 Паттерны", callback_data='settings_patterns_db')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases_settings(update, context):
    """Показать настройки баз данных для бэкапов"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"
    
    if not db_config:
        message += "❌ *Базы данных не настроены*\n\n"
        message += "Здесь вы можете настроить категории и базы данных для мониторинга бэкапов."
    else:
        message += "*Текущие настройки:*\n\n"
        for category, databases in db_config.items():
            message += f"📁 *{category.upper()}*\n"
            message += f"   Количество БД: {len(databases)}\n"
            # Показываем несколько примеров
            sample_dbs = list(databases.values())[:2]
            for db_name in sample_dbs:
                message += f"   • {db_name}\n"
            if len(databases) > 2:
                message += f"   • ... и еще {len(databases) - 2} БД\n"
            message += "\n"
    
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить категорию", callback_data='settings_db_add_category')],
        [InlineKeyboardButton("✏️ Редактировать категорию", callback_data='settings_db_edit_category')],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data='settings_db_delete_category')],
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='settings_db_view_all')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_all_settings(update, context):
    """Показать все настройки"""
    query = update.callback_query
    query.answer()
    
    all_settings = settings_manager.get_all_settings()
    
    message = "📊 *Все настройки системы*\n\n"
    
    for category in settings_manager.get_categories():
        message += f"*{category.upper()}:*\n"
        category_settings = {k: v for k, v in all_settings.items() if k.lower().startswith(category.lower()) or settings_manager.get_setting(k, category='') == category}
        
        for key, value in category_settings.items():
            if key == 'TELEGRAM_TOKEN' and value:
                value = '***' + value[-4:]  # Показываем только последние 4 символа
            elif key == 'CHAT_IDS':
                value = f"{len(value)} чатов"
            elif isinstance(value, (list, dict)):
                value = f"{len(value)} элементов"
            
            message += f"• {key}: {value}\n"
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def settings_callback_handler(update, context):
    """Обработчик callback'ов настроек"""
    query = update.callback_query
    data = query.data
    
    # если это callback от бэкапов, НЕ обрабатываем здесь
    if (
        data.startswith('db_')
        and data not in BACKUP_SETTINGS_CALLBACKS
        and not data.startswith('db_default_')
    ):
        _safe_query_answer(query, "⚙️ Перенаправление к модулю бэкапов...")
        # Передаем обработку дальше по цепочке
        return
    if data.startswith('backup_') and data not in BACKUP_SETTINGS_CALLBACKS:
        _safe_query_answer(query, "⚙️ Перенаправление к модулю бэкапов...")
        # Передаем обработку дальше по цепочке
        return

    try:
        # Основные категории настроек
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
            show_auth_settings(update, context)  # Теперь упрощенная версия
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
        elif data == 'settings_patterns_db_from_backup':
            show_db_patterns_menu_from_backup(update, context)
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
                    title="🧩 *Обработка файлов (источник)*",
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
                    title="🧩 *Обработка файлов (источник)*",
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
                    title="🧩 *Обработка файлов (почта)*",
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
                    title="🧩 *Обработка файлов (почта)*",
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
                "Введите путь к временному каталогу для почтовых файлов:\n"
                f"Текущее значение: {current_temp_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_mail')]
                ])
            )
        elif data == 'supplier_stock_mail_archive_dir':
            context.user_data['supplier_stock_mail_edit'] = 'archive_dir'
            config = get_supplier_stock_config()
            current_archive_dir = _format_current_hint(config.get("mail", {}).get("archive_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите путь к каталогу архива для почтовых файлов:\n"
                f"Текущее значение: {current_archive_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_mail')]
                ])
            )
        elif data == 'supplier_stock_archive_cleanup_mail':
            context.user_data['supplier_stock_edit'] = 'archive_cleanup_days'
            context.user_data['supplier_stock_archive_cleanup_back'] = 'supplier_stock_mail'
            config = get_supplier_stock_config()
            current_value = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите период очистки архива в днях (0 — отключить):\n"
                f"Текущее значение: {current_value}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_mail')]
                ])
            )
        elif data == 'supplier_stock_report_period':
            context.user_data['supplier_stock_edit'] = 'report_period_days'
            config = get_supplier_stock_config()
            current_value = config.get("reporting", {}).get("period_days", 7)
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите период отчётов в днях (минимум 1):\n"
                f"Текущее значение: {current_value}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='settings_ext_supplier_stock')]
                ])
            )
        elif data == 'supplier_stock_mail_unpack_toggle':
            query.answer("ℹ️ Распаковка теперь на уровне правил", show_alert=False)
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
                query.answer("⚠️ Правило не найдено", show_alert=False)
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
                "Введите путь к временному каталогу:\n"
                f"Текущее значение: {current_temp_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_download')]
                ])
            )
        elif data == 'supplier_stock_schedule':
            show_supplier_stock_schedule_menu(update, context)
        elif data == 'supplier_stock_unpack_toggle':
            query.answer("ℹ️ Распаковка теперь на уровне источников", show_alert=False)
            show_supplier_stock_download_settings(update, context)
        elif data == 'supplier_stock_archive_dir':
            context.user_data['supplier_stock_edit'] = 'archive_dir'
            config = get_supplier_stock_config()
            current_archive_dir = _format_current_hint(config.get("download", {}).get("archive_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите путь к каталогу архива:\n"
                f"Текущее значение: {current_archive_dir}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_download')]
                ])
            )
        elif data == 'supplier_stock_archive_cleanup_download':
            context.user_data['supplier_stock_edit'] = 'archive_cleanup_days'
            context.user_data['supplier_stock_archive_cleanup_back'] = 'supplier_stock_download'
            config = get_supplier_stock_config()
            current_value = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите период очистки архива в днях (0 — отключить):\n"
                f"Текущее значение: {current_value}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_download')]
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
                "Введите одно или несколько времен запуска (HH:MM).\n"
                "Разделители: пробел, запятая или точка с запятой.\n"
                f"Текущее значение: {current_time}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_schedule')]
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
                query.answer("⚠️ Источник не найден", show_alert=False)
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
        
        # Подпункты
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
        
        # Новые обработчики для настроек БД
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
        
        # Обработчики для новых пунктов меню
        elif data == 'manage_chats':
            manage_chats_handler(update, context)
        elif data == 'server_timeouts':
            show_server_timeouts(update, context)  # Теперь упрощенная версия
        elif data == 'settings_add_server':
            add_server_handler(update, context)
        
        # Обработчики для установки значений
        elif data.startswith('set_'):
            handle_setting_input(update, context, data.replace('set_', ''))
        
        # Управление чатами
        elif data == 'add_chat':
            add_chat_handler(update, context)
        elif data == 'remove_chat':
            remove_chat_handler(update, context)
        # Паттерны бэкапов
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
        
        # Обработчики для редактирования и удаления категорий БД
        elif data.startswith('settings_db_add_db_'):
            category = data.replace('settings_db_add_db_', '')
            add_database_entry_handler(update, context, category)
        elif data.startswith('settings_db_edit_db_'):
            raw_value = data.replace('settings_db_edit_db_', '')
            if '__' in raw_value:
                category, db_key = raw_value.split('__', 1)
                edit_database_entry_handler(update, context, category, db_key)
        elif data.startswith('settings_db_toggle_monitor_'):
            raw_value = data.replace('settings_db_toggle_monitor_', '', 1)
            if '__' in raw_value:
                encoded_backup_type, encoded_db_name = raw_value.split('__', 1)
                settings_toggle_database_monitoring(update, context, encoded_backup_type, encoded_db_name)
            else:
                toggle_map = context.user_data.get('settings_db_toggle_map', {})
                encoded_pair = toggle_map.get(raw_value, '')
                if '__' in encoded_pair:
                    encoded_backup_type, encoded_db_name = encoded_pair.split('__', 1)
                    settings_toggle_database_monitoring(update, context, encoded_backup_type, encoded_db_name)
                else:
                    _safe_query_answer(query, "Не удалось определить базу данных", show_alert=True)
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
        
        # Обработчики для серверов
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
        
        # Обработчики для таймаутов серверов
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
        
        # Обработчики типов серверов
        elif data.startswith('server_type_'):
            handle_server_type(update, context)
        
        # Аутентификация
        elif data == 'settings_auth':
            show_auth_settings(update, context)
        elif data == 'ssh_auth_settings':
            show_ssh_auth_settings(update, context)
        
        # Windows аутентификация
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
        
        # Обработчики типов для Windows учетных данных
        elif data.startswith('cred_type_'):
            handle_credential_type_selection(update, context)

        # Обработчики управления типами серверов Windows
        elif data.startswith('manage_type_'):
            handle_server_type_management(update, context)

        # Обработчики для управления типами серверов (подтверждение операций)
        elif data.startswith('merge_confirm_'):
            parts = data.replace('merge_confirm_', '').split('_')
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = '_'.join(parts[1:])
                merge_server_types_confirmation(update, context, source_type, target_type)

        elif data.startswith('delete_type_confirm_'):
            server_type = data.replace('delete_type_confirm_', '')
            delete_server_type_confirmation(update, context, server_type)

        # Обработчики для выполнения операций с типами серверов
        elif data.startswith('merge_execute_'):
            parts = data.replace('merge_execute_', '').split('_')
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = '_'.join(parts[1:])
                execute_server_type_merge(update, context, source_type, target_type)

        elif data.startswith('delete_type_execute_'):
            server_type = data.replace('delete_type_execute_', '')
            execute_server_type_delete(update, context, server_type)

        # Обработчики для закрытия меню
        elif data == 'close':
            try:
                query.delete_message()
            except:
                query.edit_message_text("✅ Меню закрыто")
        
        else:
            _safe_query_answer(query, "⚙️ Этот раздел в разработке")
    
    except Exception as e:
        print(f"❌ Ошибка в settings_callback_handler: {e}")
        debug_logger(f"Ошибка в settings_callback_handler: {e}")
        _safe_query_answer(query, "❌ Произошла ошибка при обработке запроса")
    
    _safe_query_answer(query)

def handle_setting_input(update, context, setting_key):
    """Обработчик ввода значений настроек - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем какое настройку меняем
    context.user_data['editing_setting'] = setting_key
    context.user_data['editing_setting_message_id'] = query.message.message_id
    context.user_data['editing_setting_chat_id'] = query.message.chat_id
    
    setting_descriptions = {
        # Существующие настройки...
        'telegram_token': 'Введите новый токен Telegram бота:',
        'check_interval': 'Введите новый интервал проверки (в секундах):',
        'max_fail_time': 'Введите максимальное время простоя (в секундах):',
        'silent_start': 'Введите час начала тихого режима (0-23):',
        'silent_end': 'Введите час окончания тихого режима (0-23):',
        'data_collection': 'Введите время сбора данных (формат HH:MM):',
        'cpu_warning': 'Введите порог предупреждения для CPU (%):',
        'cpu_critical': 'Введите критический порог для CPU (%):',
        'ram_warning': 'Введите порог предупреждения для RAM (%):',
        'ram_critical': 'Введите критический порог для RAM (%):',
        'disk_warning': 'Введите порог предупреждения для Disk (%):',
        'disk_critical': 'Введите критический порог для Disk (%):',
        'ssh_username': 'Введите имя пользователя SSH:',
        'ssh_key_path': 'Введите путь к SSH ключу:',
        'web_port': 'Введите порт веб-интерфейса:',
        'web_host': 'Введите хост веб-интерфейса:',
        'backup_alert_hours': 'Введите количество часов для алертов о бэкапах:',
        'backup_stale_hours': 'Введите количество часов для устаревших бэкапов:',
        
        # Новые таймауты серверов
        'windows_2025_timeout': 'Введите таймаут для Windows 2025 серверов (в секундах):',
        'domain_servers_timeout': 'Введите таймаут для доменных серверов (в секундах):',
        'admin_servers_timeout': 'Введите таймаут для Admin серверов (в секундах):',
        'standard_windows_timeout': 'Введите таймаут для стандартных Windows серверов (в секундах):',
        'linux_timeout': 'Введите таймаут для Linux серверов (в секундах):',
        'ping_timeout': 'Введите таймаут для Ping серверов (в секундах):',
    }
    
    message = setting_descriptions.get(setting_key, f'Введите новое значение для {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_main')]
        ])
    )

def handle_setting_value(update, context):
    """Обработчик получения значения настройки - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    # Сначала проверяем, не добавляется ли Windows учетная запись
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
    
    # Проверяем, не создается ли тип серверов
    if context.user_data.get('creating_server_type'):
        return handle_server_type_creation(update, context)
    
    # Проверяем, не редактируется ли тип серверов
    if context.user_data.get('editing_server_type'):
        return handle_server_type_editing(update, context)

    # Проверяем, не редактируется ли сервер
    if context.user_data.get('editing_server'):
        return handle_server_edit_input(update, context)
    
    # Затем проверяем, не добавляется ли сервер
    if context.user_data.get('adding_server'):
        return handle_server_input(update, context)
    
    # Затем проверяем, не добавляется ли категория БД
    if context.user_data.get('adding_db_category'):
        return handle_db_category_input(update, context)

    # Проверяем, не добавляется ли хост Proxmox
    if context.user_data.get('adding_proxmox_host'):
        return handle_proxmox_host_input(update, context)

    # Проверяем, не редактируется ли хост Proxmox
    if context.user_data.get('editing_proxmox_host'):
        return handle_proxmox_host_edit_input(update, context)

    # Проверяем, не добавляется ли ZFS сервер
    if context.user_data.get('adding_zfs_server'):
        return handle_zfs_server_input(update, context)

    # Проверяем, не редактируется ли имя ZFS сервера
    if context.user_data.get('editing_zfs_server_name'):
        return handle_zfs_server_name_edit_input(update, context)

    # Проверяем, не добавляется ли база данных
    if context.user_data.get('adding_db_entry'):
        return handle_db_entry_input(update, context)

    # Проверяем, не редактируется ли база данных
    if context.user_data.get('editing_db_entry'):
        return handle_db_entry_edit_input(update, context)

    # Проверяем, не добавляется ли паттерн бэкапов
    if context.user_data.get('adding_backup_pattern'):
        return handle_backup_pattern_input(update, context)

    # Проверяем, не редактируется ли паттерн бэкапов
    if context.user_data.get('editing_backup_pattern'):
        return handle_backup_pattern_edit_input(update, context)

    # Проверяем, не редактируется ли дефолтный паттерн БД
    if context.user_data.get('editing_default_db_pattern'):
        return handle_default_db_pattern_edit_input(update, context)

    # Если это обычная настройка
    if 'editing_setting' not in context.user_data:
        return
        
    setting_key = context.user_data['editing_setting']
    new_value = update.message.text
    
    try:
        # Определяем тип данных и преобразуем
        setting_types = {
            'check_interval': 'int', 'max_fail_time': 'int', 'silent_start': 'int', 'silent_end': 'int',
            'cpu_warning': 'int', 'cpu_critical': 'int', 'ram_warning': 'int', 'ram_critical': 'int',
            'disk_warning': 'int', 'disk_critical': 'int', 'web_port': 'int',
            'backup_alert_hours': 'int', 'backup_stale_hours': 'int'
        }
        
        if setting_key in setting_types and setting_types[setting_key] == 'int':
            new_value = int(new_value)
        elif setting_key == 'data_collection':
            # Проверяем формат времени
            import re
            if not re.match(r'^\d{1,2}:\d{2}$', new_value):
                raise ValueError("Неверный формат времени. Используйте HH:MM")
        
        # Сохраняем настройку
        category_map = {
            'telegram_token': 'telegram',
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
        }
        db_key = special_db_keys.get(setting_key, setting_key.upper())
        category = category_map.get(setting_key, 'general')
        
        settings_manager.set_setting(db_key, new_value, category)
        
        # Очищаем контекст
        del context.user_data['editing_setting']
        prompt_message_id = context.user_data.pop('editing_setting_message_id', None)
        prompt_chat_id = context.user_data.pop('editing_setting_chat_id', None)
        if prompt_message_id and prompt_chat_id:
            try:
                context.bot.delete_message(chat_id=prompt_chat_id, message_id=prompt_message_id)
            except Exception:
                pass
        
        update.message.reply_text(
            f"✅ Настройка {db_key} успешно обновлена!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Вернуться к настройкам", callback_data='settings_main')]
            ])
        )
        
    except ValueError as e:
        update.message.reply_text(f"❌ Ошибка: {e}\nПопробуйте еще раз:")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        
def show_web_settings(update, context):
    """Показать настройки веб-интерфейса - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    web_port = settings_manager.get_setting('WEB_PORT', 5000)
    web_host = settings_manager.get_setting('WEB_HOST', '0.0.0.0')
    
    message = (
        "🌐 *Настройки веб-интерфейса*\n\n"
        f"• Порт: {web_port}\n"
        f"• Хост: {web_host}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔌 Порт веб-интерфейса", callback_data='set_web_port')],
        [InlineKeyboardButton("🌐 Хост веб-интерфейса", callback_data='set_web_host')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_settings_handlers():
    """Получить обработчики для настроек"""
    return [
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^manage_'),
        MessageHandler(Filters.text & ~Filters.command, handle_setting_value)
    ]

def show_auth_settings(update, context):
    """Показать настройки аутентификации - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    # Получаем статистику по Windows учетным данным
    windows_creds = settings_manager.get_windows_credentials()
    
    message = (
        "🔐 *Настройки аутентификации*\n\n"
        "*SSH аутентификация:*\n"
        f"• Пользователь: `{ssh_username}`\n"
        f"• Путь к ключу: `{ssh_key_path}`\n\n"
        "*Windows аутентификация:*\n"
        f"• Учетных записей: {len(windows_creds)}\n"
        f"• Типов серверов: {len(settings_manager.get_windows_server_types())}\n\n"
        "Выберите раздел для настройки:"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 SSH аутентификация", callback_data='ssh_auth_settings')],
        [InlineKeyboardButton("🖥️ Windows аутентификация", callback_data='windows_auth_main')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_ssh_auth_settings(update, context):
    """Показать настройки SSH аутентификации"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    message = (
        "👤 *SSH аутентификация*\n\n"
        f"• SSH пользователь: `{ssh_username}`\n"
        f"• Путь к SSH ключу: `{ssh_key_path}`\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 SSH пользователь", callback_data='set_ssh_username')],
        [InlineKeyboardButton("🔑 Путь к SSH ключу", callback_data='set_ssh_key_path')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_auth'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_servers_settings(update, context):
    """Показать настройки серверов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    servers = settings_manager.get_all_servers(include_disabled=True)
    enabled_servers = [s for s in servers if s.get('enabled', True)]
    paused_servers = [s for s in servers if not s.get('enabled', True)]
    windows_servers = [s for s in servers if s['type'] == 'rdp']
    linux_servers = [s for s in servers if s['type'] == 'ssh']
    ping_servers = [s for s in servers if s['type'] == 'ping']
    
    # Сбрасываем состояния редактирования, если вернулись в меню
    context.user_data.pop('adding_server', None)
    context.user_data.pop('editing_server', None)
    context.user_data.pop('server_stage', None)
    context.user_data.pop('edit_server_stage', None)
    context.user_data.pop('edit_server_ip', None)
    context.user_data.pop('edit_server_data', None)

    message = (
        "🖥️ *Настройки серверов*\n\n"
        f"• Windows серверов: {len(windows_servers)}\n"
        f"• Linux серверов: {len(linux_servers)}\n"
        f"• Ping серверов: {len(ping_servers)}\n"
        f"• Всего серверов: {len(servers)}\n"
        f"• Активных: {len(enabled_servers)}\n"
        f"• Приостановлено: {len(paused_servers)}\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Список серверов", callback_data='settings_servers_list')],
        [InlineKeyboardButton("➕ Добавить сервер", callback_data='settings_add_server')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _get_server_by_ip(servers, ip):
    """Найти сервер по IP из списка"""
    for server in servers:
        if server.get('ip') == ip:
            return server
    return None

def show_servers_list(update, context):
    """Показать список серверов с действиями"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)

    # Сбрасываем состояния редактирования при показе списка
    context.user_data.pop('editing_server', None)
    context.user_data.pop('edit_server_stage', None)
    context.user_data.pop('edit_server_ip', None)
    context.user_data.pop('edit_server_data', None)

    if not servers:
        message = "📋 *Список серверов*\n\n❌ Серверы не настроены."
        keyboard = [
            [InlineKeyboardButton("➕ Добавить сервер", callback_data='settings_add_server')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    message_lines = ["📋 *Список серверов*\n"]
    for server in servers:
        status_icon = "🟢" if server.get('enabled', True) else "⏸️"
        status_text = "мониторинг" if server.get('enabled', True) else "пауза"
        message_lines.append(
            f"• {status_icon} {server['name']} (`{server['ip']}`) — {server['type'].upper()} — {status_text}"
        )

    keyboard = [
        [
            InlineKeyboardButton("↩️ Назад", callback_data='settings_servers'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ]
    ]
    for server in servers:
        toggle_text = "⏸️ Пауза" if server.get('enabled', True) else "▶️ Возобновить"
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {server['name']}",
                callback_data=f"settings_edit_server_{server['ip']}"
            ),
            InlineKeyboardButton(
                toggle_text,
                callback_data=f"settings_toggle_server_{server['ip']}"
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f"settings_delete_server_{server['ip']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Добавить сервер", callback_data='settings_add_server')
    ])
    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_confirmation(update, context, ip):
    """Подтверждение удаления сервера"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
            ])
        )
        return

    message = (
        "🗑️ *Удаление сервера*\n\n"
        f"Сервер: *{server['name']}* (`{server['ip']}`)\n"
        "Подтвердите удаление:"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Удалить", callback_data=f"settings_confirm_delete_server_{ip}")],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_execute(update, context, ip):
    """Удалить сервер"""
    query = update.callback_query
    query.answer()

    success = settings_manager.delete_server(ip)
    if success:
        message = f"✅ Сервер `{ip}` удален."
    else:
        message = f"❌ Не удалось удалить сервер `{ip}`."

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к списку", callback_data='settings_servers_list')]
        ])
    )

def show_server_edit_menu(update, context, ip):
    """Меню редактирования сервера"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
            ])
        )
        return

    status_text = "🟢 Включен" if server.get('enabled', True) else "⏸️ Приостановлен"
    message = (
        "✏️ *Редактирование сервера*\n\n"
        f"• Имя: *{server['name']}*\n"
        f"• IP: `{server['ip']}`\n"
        f"• Тип: *{server['type'].upper()}*\n\n"
        f"• Статус: *{status_text}*\n\n"
        "Выберите действие:"
    )

    toggle_text = "⏸️ Приостановить мониторинг" if server.get('enabled', True) else "▶️ Возобновить мониторинг"
    keyboard = [
        [InlineKeyboardButton("📝 Изменить имя", callback_data=f"settings_edit_server_name_{ip}")],
        [InlineKeyboardButton("🔧 Изменить тип", callback_data=f"settings_edit_server_type_{ip}")],
        [InlineKeyboardButton(toggle_text, callback_data=f"settings_toggle_server_{ip}")],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def toggle_server_monitoring(update, context, ip):
    """Переключить мониторинг сервера"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
            ])
        )
        return

    new_status = not server.get('enabled', True)
    success = settings_manager.set_server_enabled(ip, new_status)

    if success:
        status_text = "🟢 Мониторинг включен" if new_status else "⏸️ Мониторинг приостановлен"
        message = (
            "✅ Статус мониторинга обновлен.\n\n"
            f"• Сервер: *{server.get('name', ip)}*\n"
            f"• Статус: *{status_text}*"
        )
    else:
        message = "❌ Не удалось обновить статус мониторинга."

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к списку", callback_data='settings_servers_list')]
        ])
    )

def start_server_name_edit(update, context, ip):
    """Запуск редактирования имени сервера"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
            ])
        )
        return

    context.user_data['editing_server'] = True
    context.user_data['edit_server_stage'] = 'name'
    context.user_data['edit_server_ip'] = ip
    context.user_data['edit_server_data'] = server

    query.edit_message_text(
        "📝 Введите новое имя сервера:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_servers_list')]
        ])
    )

def start_server_type_edit(update, context, ip):
    """Запуск редактирования типа сервера"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    server = _get_server_by_ip(servers, ip)
    if not server:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
            ])
        )
        return

    context.user_data['editing_server'] = True
    context.user_data['edit_server_stage'] = 'type'
    context.user_data['edit_server_ip'] = ip
    context.user_data['edit_server_data'] = server

    keyboard = [
        [InlineKeyboardButton("🖥️ Windows (RDP)", callback_data=f"settings_edit_server_type_select_rdp_{ip}")],
        [InlineKeyboardButton("🐧 Linux (SSH)", callback_data=f"settings_edit_server_type_select_ssh_{ip}")],
        [InlineKeyboardButton("📡 Ping Only", callback_data=f"settings_edit_server_type_select_ping_{ip}")],
        [InlineKeyboardButton("❌ Отмена", callback_data='settings_servers_list')]
    ]

    query.edit_message_text(
        "🔧 Выберите новый тип сервера:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_server_type_selection(update, context):
    """Обработчик выбора нового типа сервера"""
    query = update.callback_query
    query.answer()

    if not context.user_data.get('editing_server'):
        return

    data = query.data.replace('settings_edit_server_type_select_', '')
    parts = data.split('_')
    if len(parts) < 2:
        query.edit_message_text(
            "❌ Неверный формат выбора типа.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
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
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_servers_list')]
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
            "✅ Тип сервера обновлен.\n\n"
            f"• Сервер: *{server.get('name', ip)}*\n"
            f"• Новый тип: *{server_type.upper()}*"
        )
    else:
        message = "❌ Не удалось обновить тип сервера."

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к списку", callback_data='settings_servers_list')]
        ])
    )

def handle_server_edit_input(update, context):
    """Обработчик ввода для редактирования сервера"""
    if not context.user_data.get('editing_server'):
        return

    stage = context.user_data.get('edit_server_stage')
    if stage != 'name':
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("❌ Имя не может быть пустым. Попробуйте снова:")
        return

    server = context.user_data.get('edit_server_data') or {}
    ip = context.user_data.get('edit_server_ip')
    if not ip:
        update.message.reply_text("❌ Не удалось определить сервер.")
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
            "✅ Имя сервера обновлено.\n\n"
            f"• IP: `{ip}`\n"
            f"• Новое имя: *{new_name}*"
        )
    else:
        message = "❌ Не удалось обновить имя сервера."

    update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к списку", callback_data='settings_servers_list')]
        ])
    )

def show_backup_times(update, context):
    """Показать настройки временных интервалов бэкапов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    alert_hours = settings_manager.get_setting('BACKUP_ALERT_HOURS', 24)
    stale_hours = settings_manager.get_setting('BACKUP_STALE_HOURS', 36)
    
    message = (
        "⏰ *Временные интервалы бэкапов*\n\n"
        f"• Алерты через: {alert_hours} часов\n"
        f"• Устаревание через: {stale_hours} часов\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚨 Часы для алертов", callback_data='set_backup_alert_hours')],
        [InlineKeyboardButton("📅 Часы для устаревания", callback_data='set_backup_stale_hours')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases_settings(update, context):
    """Показать настройки баз данных для бэкапов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()

    # Сбрасываем состояния добавления/редактирования БД при выходе в меню
    context.user_data.pop('adding_db_entry', None)
    context.user_data.pop('editing_db_entry', None)
    context.user_data.pop('db_entry_category', None)
    context.user_data.pop('db_entry_key', None)
    context.user_data['settings_db_toggle_map'] = {}
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"
    
    if not db_config:
        message += "❌ *Базы данных не настроены*\n\n"
    else:
        for category, databases in db_config.items():
            if not isinstance(databases, dict):
                databases = {}
            message += f"*{category.upper()}* ({len(databases)} БД):\n"
            for db_key in databases.keys():
                message += f"• `{db_key}`\n"
            message += "\n"
    
    message += "Выберите действие:"
    
    disabled_pairs = _get_disabled_db_monitors_settings()
    keyboard = []

    for category, databases in db_config.items():
        if not isinstance(databases, dict):
            databases = {}
        keyboard.append([InlineKeyboardButton(
            f"➕ Добавить БД в {category}",
            callback_data=f"settings_db_add_db_{category}"
        )])
        row = []
        for db_key in databases.keys():
            row.append(InlineKeyboardButton(
                f"✏️ {db_key}",
                callback_data=f"settings_db_edit_db_{category}__{db_key}"
            ))
            row.append(InlineKeyboardButton(
                f"🗑️ {db_key}",
                callback_data=f"settings_db_delete_db_{category}__{db_key}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
            is_disabled = (category, db_key) in disabled_pairs
            monitor_text = "⚪ Мониторинг выкл" if is_disabled else "🟢 Мониторинг вкл"
            encoded_category = quote(category, safe='')
            encoded_db_key = quote(db_key, safe='')
            keyboard.append([
                InlineKeyboardButton(
                    f"{monitor_text}: {db_key}",
                    callback_data=_build_db_monitor_toggle_callback(
                        context,
                        encoded_category,
                        encoded_db_key,
                    )
                )
            ])
        if row:
            keyboard.append(row)

    keyboard.extend([
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='settings_db_view_all')],
        [InlineKeyboardButton("➕ Добавить категорию БД", callback_data='settings_db_add_category')],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data='settings_db_delete_category')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
         InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases(update, context):
    """Показать настройки баз данных для бэкапов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"
    
    for category, databases in db_config.items():
        message += f"*{category.upper()}* ({len(databases)} БД):\n"
        for db_key, db_name in list(databases.items())[:3]:
            message += f"• {db_name}\n"
        if len(databases) > 3:
            message += f"• ... и еще {len(databases) - 3} БД\n"
        message += "\n"
    
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='view_all_databases')],
        [InlineKeyboardButton("➕ Добавить БД", callback_data='add_database'),
         InlineKeyboardButton("✏️ Редактировать БД", callback_data='edit_databases')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_settings_extensions_menu(update, context):
    """Показать меню расширений в настройках"""
    query = update.callback_query
    query.answer()

    message = "🧩 *Расширения*\n\nВыберите раздел:"

    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("💾 Бэкапы Proxmox", callback_data='settings_ext_backup_proxmox')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='settings_ext_backup_db')])

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append([InlineKeyboardButton("📬 Бэкапы почты", callback_data='settings_ext_backup_mail')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("📦 Загрузка остатков 1С", callback_data='settings_ext_stock_load')])

    if extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        keyboard.append([InlineKeyboardButton("📦 Остатки поставщиков", callback_data='settings_ext_supplier_stock')])

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append([InlineKeyboardButton("🧊 ZFS", callback_data='settings_zfs')])

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("💻 Ресурсы", callback_data='settings_resources')])

    keyboard.extend([
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_extensions_settings_menu(update, context):
    """Показать управление расширениями с возвратом в настройки"""
    query = update.callback_query
    query.answer()

    extensions_status = extension_manager.get_extensions_status()

    message = "🛠️ *Управление расширениями*\n\n"
    message += "📊 *Статус расширений:*\n\n"

    keyboard = []

    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']

        status_icon = "🟢" if enabled else "🔴"
        toggle_text = "🔴 Выключить" if enabled else "🟢 Включить"

        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   Статус: {'Включено' if enabled else 'Отключено'}\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}",
                callback_data=f'settings_ext_toggle_{ext_id}'
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("📊 Включить все", callback_data='settings_ext_enable_all')],
        [InlineKeyboardButton("📋 Отключить все", callback_data='settings_ext_disable_all')],
        [
            InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ]
    ])

    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_mail_backup_settings(update, context):
    """Показать настройки бэкапов почты в разделе расширений"""
    query = update.callback_query
    query.answer()

    pattern_count = 0
    source_label = "база"
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
            source_label = "по умолчанию"
        else:
            source_label = "не настроены"

    message = (
        "📬 *Бэкапы почты*\n\n"
        f"Паттернов: {pattern_count} ({source_label})\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Паттерны", callback_data='settings_patterns_mail')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_stock_load_settings(update, context):
    """Показать настройки загрузки остатков 1С в разделе расширений."""
    query = update.callback_query
    query.answer()

    pattern_count = 0
    source_label = "база"
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
            source_label = "по умолчанию"
        else:
            source_label = "не настроены"

    message = (
        "📦 *Загрузка остатков 1С*\n\n"
        f"Паттернов: {pattern_count} ({source_label})\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Паттерны", callback_data='settings_patterns_stock')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_settings(update, context):
    """Показать настройки получения файлов остатков поставщиков."""
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
    mail_status = "🟢 Включено" if mail_settings.get("enabled") else "🔴 Выключено"
    mail_rules = len(mail_settings.get("sources", []))

    schedule_state = "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено"
    schedule_time = schedule.get("time", "не задано")

    reporting_days = config.get("reporting", {}).get("period_days", 7)
    message = (
        "📦 *Остатки поставщиков*\n\n"
        f"Источников: {len(sources)}\n"
        f"Расписание: {schedule_state} ({schedule_time})\n\n"
        "📧 *Почтовые сообщения (остатки)*\n\n"
        f"Статус: {mail_status}\n"
        f"Правил: {mail_rules}\n\n"
        "🗓 *Отчёты*\n"
        f"Период: {reporting_days} дн.\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("🌐 Скачивание файлов", callback_data='supplier_stock_download')],
        [InlineKeyboardButton("📧 Почтовые сообщения", callback_data='supplier_stock_mail')],
        [InlineKeyboardButton("🗓 Период отчётов", callback_data='supplier_stock_report_period')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_extensions'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _format_supplier_stock_timestamp(value: str | None) -> str:
    """Сформировать читаемое время запуска."""
    if not value:
        return "неизвестно"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(value)

def _supplier_stock_status_label(status: str | None, fallback: str = "неизвестно") -> str:
    """Сформировать короткую метку статуса."""
    if status == "success":
        return "🟢 успешно"
    if status == "error":
        return "🔴 ошибка"
    if status == "skipped":
        return "⚪️ пропущено"
    return f"🟡 {fallback}"

def _supplier_stock_processing_status(processing: dict | None) -> str:
    """Определить статус обработки."""
    if not processing:
        return "⏭️ не запускалась"
    if processing.get("status") == "skipped":
        return "⚪️ пропущено"
    results = processing.get("results") or []
    if not results:
        return "🟡 нет результатов"
    statuses = [item.get("status") for item in results if isinstance(item, dict)]
    if not statuses:
        return "🟡 нет результатов"
    if all(status == "success" for status in statuses):
        return "🟢 успешно"
    if any(status == "error" for status in statuses):
        return "🔴 ошибка"
    if all(status == "skipped" for status in statuses):
        return "⚪️ пропущено"
    return "🟡 частично"

def _supplier_stock_transfer_status(transfer: dict | None) -> str:
    """Определить статус выгрузки."""
    if not transfer:
        return "⏭️ не запускалась"
    status = transfer.get("status")
    if status == "skipped":
        return "⚪️ пропущено"
    if status and status != "success":
        return "🔴 ошибка"
    items = transfer.get("items") or []
    ftp_items = transfer.get("ftp_ork", {}).get("items") or []
    statuses = [
        item.get("status")
        for item in list(items) + list(ftp_items)
        if isinstance(item, dict)
    ]
    if not statuses:
        return "🟡 нет файлов"
    if all(status == "success" for status in statuses):
        return "🟢 успешно"
    if any(status == "error" for status in statuses):
        return "🔴 ошибка"
    return "🟡 частично"

def _supplier_stock_stage_label(is_ok: bool) -> str:
    return "ОК" if is_ok else "не ОК"

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
    """Сформировать читаемую метку режима обработки."""
    mode = (value or "table").strip().lower()
    if mode == "iek_json":
        return "IEK JSON"
    return "Табличный"

def show_supplier_stock_reports(update, context, source_kind: str = "download") -> None:
    """Показать результаты загрузки, обработки и выгрузки остатков поставщиков."""
    query = update.callback_query
    query.answer()

    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        query.edit_message_text(
            "📦 Остатки поставщиков отключены в настройках.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]]
            ),
        )
        return

    reporting_days = 1
    reports = get_supplier_stock_reports(limit=None, period_days=reporting_days, source_kind=source_kind)
    title = "полученные скачиванием" if source_kind == "download" else "полученные по почте"
    message_lines = [
        "📦 *Остатки поставщиков — результаты*",
        "",
        f"Группа: {title}",
        "Период: последние 24 часа",
        "",
    ]
    summary = _build_supplier_stock_daily_summary(reports, source_kind)
    if not summary:
        message_lines.append("⚪️ За сутки данных нет.")
    else:
        message_lines.append("Кликни источник, чтобы открыть историю за сутки.")
        for entry in summary:
            source_name = _escape_pattern_text(entry.get("source_name") or "неизвестный источник")
            receive_label = _supplier_stock_stage_label(entry["receive_ok"])
            processing_label = _supplier_stock_stage_label(entry["processing_ok"])
            transfer_label = _supplier_stock_stage_label(entry["transfer_ok"])
            message_lines.extend([
                "",
                f"• *{source_name}*",
                f"  📥 Загрузка: {receive_label}",
                f"  🧩 Обработка: {processing_label}",
                f"  📤 Выгрузка: {transfer_label}",
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
            InlineKeyboardButton("⬇️ Скачивание", callback_data='supplier_stock_reports_download'),
            InlineKeyboardButton("📧 Почта", callback_data='supplier_stock_reports_mail'),
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
                    f"📊 {source_label}",
                    callback_data=f'supplier_stock_report_source_day|{source_kind}|{source_id}',
                )
            ]
            if not (item.get("receive_ok") and item.get("processing_ok") and item.get("transfer_ok")):
                row.append(
                    InlineKeyboardButton(
                        "❗ Детали",
                        callback_data=f'supplier_stock_report_entry|{entry_key}',
                    )
                )
            keyboard.append(row)
        context.user_data["supplier_stock_report_entries"] = entry_map
        context.user_data["supplier_stock_report_entries_kind"] = source_kind
    keyboard.extend([
        [InlineKeyboardButton("🔄 Обновить", callback_data=f'supplier_stock_reports_{source_kind}')],
        [InlineKeyboardButton("🛠️ Настройки", callback_data='settings_ext_supplier_stock')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
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
    """Показать список источников остатков с текущими статусами."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    reporting_days = config.get("reporting", {}).get("period_days", 7)
    grouped = summarize_supplier_stock_reports(period_days=reporting_days)
    sources = grouped.get(source_kind, [])
    group_label = "полученные скачиванием" if source_kind == "download" else "полученные по почте"

    message_lines = [
        "📦 *Остатки поставщиков — источники*",
        "",
        f"Группа: {group_label}",
        f"Период: {reporting_days} дн.",
        "",
    ]

    if not sources:
        message_lines.append("⚪️ Источников за период нет.")
    else:
        for entry in sources:
            source_name = entry.get("source_name") or entry.get("source_id") or "неизвестный источник"
            time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
            message_lines.extend([
                "",
                f"• *{_escape_pattern_text(source_name)}* ({_escape_pattern_text(time_label)})",
                f"  📥 Загрузка: {entry.get('receive', {}).get('icon', '⚪️')}",
                f"  🧩 Обработка: {entry.get('processing', {}).get('icon', '⚪️')}",
                f"  📤 Выгрузка: {entry.get('transfer', {}).get('icon', '⚪️')}",
            ])

    keyboard = [
        [
            InlineKeyboardButton("⬇️ Скачивание", callback_data='supplier_stock_reports_sources_download'),
            InlineKeyboardButton("📧 Почта", callback_data='supplier_stock_reports_sources_mail'),
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
                    f"📊 {source_id}",
                    callback_data=f'supplier_stock_report_source|{source_kind}|{source_id}',
                )
            )
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
    keyboard.extend([
        [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_reports_{source_kind}')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
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
    """Показать подробную статистику по источнику остатков."""
    query = update.callback_query
    query.answer()

    if not source_id:
        query.edit_message_text(
            "⚪️ Источник не выбран.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_reports_sources_{source_kind}')],
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
        "📦 *Остатки поставщиков — статистика источника*",
        "",
        f"Источник: {_escape_pattern_text(source_id)}",
        f"Группа: {'полученные скачиванием' if source_kind == 'download' else 'полученные по почте'}",
        f"Период: {reporting_days} дн.",
        "",
        f"Всего запусков: {summary.get('total', 0)}",
        f"📥 Успешно: {summary.get('receive_success', 0)} | Ошибок: {summary.get('receive_error', 0)}",
        f"🧩 Успешно: {summary.get('processing_success', 0)} | Ошибок: {summary.get('processing_error', 0)}",
        f"📤 Успешно: {summary.get('transfer_success', 0)} | Ошибок: {summary.get('transfer_error', 0)}",
        "",
        "*Последние события:*",
    ]

    if not entries:
        message_lines.append("⚪️ Записей пока нет.")
    else:
        for entry in entries[:10]:
            time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
            message_lines.extend([
                "",
                f"• {_escape_pattern_text(time_label)}",
                f"  📥 {entry.get('receive', {}).get('icon', '⚪️')}",
                f"  🧩 {entry.get('processing', {}).get('icon', '⚪️')}",
                f"  📤 {entry.get('transfer', {}).get('icon', '⚪️')}",
            ])
            if entry.get("error"):
                message_lines.append(f"  ❗ Ошибка: {_escape_pattern_text(entry.get('error'))}")

    keyboard = [
        [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_reports_sources_{source_kind}')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
    ]

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def show_supplier_stock_report_entry_details(update, context, entry_key: str) -> None:
    """Показать детали последнего запуска по источнику."""
    query = update.callback_query
    query.answer()

    entry_map = context.user_data.get("supplier_stock_report_entries", {})
    source_kind = context.user_data.get("supplier_stock_report_entries_kind", "download")
    summary = entry_map.get(entry_key)
    if not summary:
        query.edit_message_text(
            "⚪️ Детали недоступны, обновите результаты.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_reports_{source_kind}')],
            ]),
        )
        return

    entry = summary.get("entry", {})
    source_id = summary.get("source_id") or entry.get("source_id") or "неизвестно"
    source_name = entry.get("source_name") or source_id
    time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
    download_status = _supplier_stock_status_label(entry.get("status"))
    processing_info = entry.get("processing") if entry.get("status") == "success" else None
    processing_status = _supplier_stock_processing_status(processing_info)
    transfer_status = _supplier_stock_transfer_status(
        processing_info.get("transfer") if processing_info else None
    )
    if entry.get("status") != "success":
        processing_status = "⏭️ не запускалась"
        transfer_status = "⏭️ не запускалась"

    message_lines = [
        "📦 *Остатки поставщиков — подробности*",
        "",
        f"Источник: {_escape_pattern_text(source_name)}",
        f"Группа: {'полученные скачиванием' if source_kind == 'download' else 'полученные по почте'}",
        f"Запуск: {_escape_pattern_text(time_label)}",
        "",
        f"📥 Загрузка: {download_status}",
        f"🧩 Обработка: {processing_status}",
        f"📤 Выгрузка: {transfer_status}",
    ]
    if entry.get("error"):
        message_lines.append(f"\n❗ Ошибка: {_escape_pattern_text(entry.get('error'))}")

    keyboard = [
        [InlineKeyboardButton(
            "📊 История источника",
            callback_data=f'supplier_stock_report_source_day|{source_kind}|{source_id}',
        )],
        [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_reports_{source_kind}')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
    ]

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

def show_supplier_stock_download_settings(update, context):
    """Показать настройки скачивания файлов остатков поставщиков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)

    config = get_supplier_stock_config()
    download = config.get("download", {})
    temp_dir = download.get("temp_dir", "")
    sources = download.get("sources", [])
    schedule = download.get("schedule", {})
    unpack_enabled = sum(1 for source in sources if source.get("unpack_archive"))
    unpack_state = f"{unpack_enabled}/{len(sources)}" if sources else "нет"
    schedule_state = "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено"
    schedule_time = schedule.get("time", "не задано")
    archive_cleanup = _format_archive_cleanup_days(config.get("archive_cleanup_days"))

    message = (
        "📦 *Скачивание файлов остатков*\n\n"
        f"Временный каталог: `{temp_dir}`\n"
        f"Архив: `{download.get('archive_dir', '')}`\n"
        f"Очистка архива: {archive_cleanup}\n"
        f"Распаковка в источниках: {unpack_state}\n"
        f"Источников: {len(sources)}\n"
        f"Расписание: {schedule_state} ({schedule_time})\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("📁 Временный каталог", callback_data='supplier_stock_temp_dir')],
        [InlineKeyboardButton("🗄️ Каталог архива", callback_data='supplier_stock_archive_dir')],
        [InlineKeyboardButton("🧹 Период очистки архива", callback_data='supplier_stock_archive_cleanup_download')],
        [InlineKeyboardButton("⏰ Расписание", callback_data='supplier_stock_schedule')],
        [InlineKeyboardButton("📦 Источники", callback_data='supplier_stock_sources')],
        [InlineKeyboardButton("📤 Ресурсы выгрузки", callback_data='supplier_stock_resources')],
        [InlineKeyboardButton("📡 FTP ОРК", callback_data='supplier_stock_ftp')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_supplier_stock'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_mail_settings(update, context):
    """Показать настройки получения остатков через почту."""
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
    status_text = "🟢 Включено" if mail_settings.get("enabled") else "🔴 Выключено"
    temp_dir = mail_settings.get("temp_dir") or ""
    archive_dir = mail_settings.get("archive_dir") or ""
    unpack_enabled = sum(1 for source in sources if source.get("unpack_archive"))
    unpack_state = f"{unpack_enabled}/{len(sources)}" if sources else "нет"
    archive_cleanup = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
    message = (
        "📧 *Почтовые сообщения (остатки)*\n\n"
        f"Статус: {status_text}\n"
        f"Временный каталог: `{_escape_pattern_text(temp_dir)}`\n"
        f"Архив: `{_escape_pattern_text(archive_dir)}`\n"
        f"Очистка архива: {archive_cleanup}\n"
        f"Распаковка в правилах: {unpack_state}\n"
        f"Правил: {len(sources)}\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Включить/выключить", callback_data='supplier_stock_mail_toggle')],
        [InlineKeyboardButton("📁 Временный каталог", callback_data='supplier_stock_mail_temp_dir')],
        [InlineKeyboardButton("🗄️ Каталог архива", callback_data='supplier_stock_mail_archive_dir')],
        [InlineKeyboardButton("🧹 Период очистки архива", callback_data='supplier_stock_archive_cleanup_mail')],
        [InlineKeyboardButton("📎 Правила вложений", callback_data='supplier_stock_mail_sources')],
        [InlineKeyboardButton("📤 Ресурсы выгрузки", callback_data='supplier_stock_resources')],
        [InlineKeyboardButton("📡 FTP ОРК", callback_data='supplier_stock_ftp')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_supplier_stock'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_resources_menu(update, context):
    """Показать список ресурсов выгрузки по умолчанию."""
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
        message = "📤 *Ресурсы выгрузки*\n\n❌ Ресурсы не настроены."
    else:
        message_lines = ["📤 *Ресурсы выгрузки*\n"]
        for index, resource in enumerate(resources, start=1):
            name = _escape_pattern_text(resource.get("name") or resource.get("id") or f"Ресурс {index}")
            unc_path = _escape_pattern_text(resource.get("unc_path") or "не задано")
            login = _escape_pattern_text(resource.get("login") or "не задано")
            enabled = resource.get("enabled", True)
            status_icon = "🟢" if enabled else "🔴"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   • UNC: `{unc_path}`\n"
                    f"   • Логин: `{login}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить ресурс", callback_data='supplier_stock_resource_add')],
    ]

    for resource in resources:
        resource_id = resource.get("id") or ""
        if not resource_id:
            continue
        enabled = resource.get("enabled", True)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        keyboard.append([
            InlineKeyboardButton(
                f"⚙️ {resource.get('name', resource_id)}",
                callback_data=f'supplier_stock_resource_settings|{resource_id}'
            ),
            InlineKeyboardButton(
                toggle_text,
                callback_data=f'supplier_stock_resource_toggle_{resource_id}'
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                "🗑️",
                callback_data=f'supplier_stock_resource_delete_{resource_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_supplier_stock'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_resource_settings(update, context, resource_id: str) -> None:
    """Показать настройки конкретного ресурса выгрузки."""
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
            "❌ Ресурс не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_resources')]
            ])
        )
        return

    name = _escape_pattern_text(resource.get("name") or resource_id)
    unc_path = _escape_pattern_text(resource.get("unc_path") or "не задано")
    login = _escape_pattern_text(resource.get("login") or "не задано")
    password = "задано" if resource.get("password") else "не задано"
    status_icon = "🟢" if resource.get("enabled", True) else "🔴"

    message = (
        "⚙️ *Ресурс выгрузки*\n\n"
        f"{status_icon} *{name}*\n"
        f"• UNC путь: `{unc_path}`\n"
        f"• Логин: `{login}`\n"
        f"• Пароль: `{password}`\n\n"
        "Выберите настройку:"
    )

    keyboard = [
        [
            InlineKeyboardButton("✏️ Название", callback_data=f'supplier_stock_resource_field|{resource_id}|name'),
            InlineKeyboardButton("📂 UNC путь", callback_data=f'supplier_stock_resource_field|{resource_id}|unc_path'),
        ],
        [
            InlineKeyboardButton("👤 Логин", callback_data=f'supplier_stock_resource_field|{resource_id}|login'),
            InlineKeyboardButton("🔐 Пароль", callback_data=f'supplier_stock_resource_field|{resource_id}|password'),
        ],
        [InlineKeyboardButton("🔁 Включить/выключить", callback_data=f'supplier_stock_resource_toggle_{resource_id}')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [
            InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_resources'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_ftp_settings(update, context) -> None:
    """Показать настройки FTP ОРК."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_ftp_field', None)

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})
    host = _escape_pattern_text(ftp_settings.get("host") or "не задано")
    login = _escape_pattern_text(ftp_settings.get("login") or "не задано")
    password = "задано" if ftp_settings.get("password") else "не задано"

    message = (
        "📡 *FTP ОРК*\n\n"
        f"HOST FTP: `{host}`\n"
        f"Логин FTP: `{login}`\n"
        f"Пароль FTP: `{password}`\n\n"
        "Выберите параметр:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🌐 HOST FTP", callback_data='supplier_stock_ftp_field|host'),
            InlineKeyboardButton("👤 Логин FTP", callback_data='supplier_stock_ftp_field|login'),
        ],
        [InlineKeyboardButton("🔐 Пароль FTP", callback_data='supplier_stock_ftp_field|password')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [
            InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_supplier_stock'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
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
    title: str = "🧩 *Обработка файлов остатков*",
):
    """Показать настройки обработки полученных файлов остатков."""
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
        message = f"{title}\n\n❌ Правила обработки не настроены."
    else:
        message_lines = [f"{title}\n"]
        for index, rule in enumerate(rules, start=1):
            name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"Правило {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "не задано")
            enabled = rule.get("enabled", True)
            active = rule.get("active", False)
            status_icon = "🟢" if enabled else "🔴"
            processing_text = "обработка" if rule.get("requires_processing", True) else "без обработки"
            active_text = "да" if active else "нет"
            message_lines.append(
                (
                    f"{index}. {status_icon}{'⭐' if active else ''} *{name}*\n"
                    f"   • Файл источника: `{source_file}`\n"
                    f"   • Режим: `{processing_text}`\n"
                    f"   • Активно: `{active_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить правило", callback_data=f'{action_prefix}|add')],
    ]

    for rule in rules:
        rule_id = rule.get("id") or ""
        if not rule_id:
            continue
        enabled = rule.get("enabled", True)
        active = rule.get("active", False)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        active_text = "⛔️ Отключить активность" if active else "⭐ Включить активность"
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {rule.get('name', rule_id)}",
                callback_data=f'{action_prefix}|edit|{rule_id}'
            ),
            InlineKeyboardButton(
                f"{toggle_text}",
                callback_data=f'{action_prefix}|toggle|{rule_id}'
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f'{action_prefix}|delete|{rule_id}'
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                active_text,
                callback_data=f'{action_prefix}|activate|{rule_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
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
    processing_text = "да" if requires_processing else "нет"
    name = _escape_pattern_text(data.get("name") or "не задано")
    source_file = _escape_pattern_text(data.get("source_file") or "не задано")
    output_name = _escape_pattern_text(data.get("output_name") or "не задано")
    lines = [
        "🧩 *Настройка обработки*\n",
        f"• Название: `{name}`",
        f"• Файл источника: `{source_file}`",
        f"• Требуется обработка: `{processing_text}`",
    ]
    if requires_processing:
        data_row = data.get("data_row")
        lines.append(f"• Первая строка с данными: `{data_row or 'не задано'}`")
    else:
        lines.append(f"• Имя файла на выходе: `{output_name}`")
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

    toggle_text = "✅ Требуется обработка" if requires_processing else "⛔️ Обработка не требуется"

    keyboard = [[InlineKeyboardButton("— Настройки правила —", callback_data='supplier_stock_noop')]]
    if not data.get("source_id"):
        keyboard.extend([
            [InlineKeyboardButton("✏️ Название", callback_data='supplier_stock_processing_rule|field|name')],
            [InlineKeyboardButton("📄 Файл источника", callback_data='supplier_stock_processing_rule|field|source_file')],
        ])
    keyboard.append([InlineKeyboardButton(toggle_text, callback_data='supplier_stock_processing_rule|toggle_processing')])

    if requires_processing:
        variant = _ensure_processing_variant(data, variant_index or 0)
        orc = variant.get("orc", {})
        orc_enabled = orc.get("enabled", False)
        orc_text = "да" if orc_enabled else "нет"
        keyboard.extend([
            [InlineKeyboardButton("📍 Первая строка с данными", callback_data='supplier_stock_processing_rule|field|data_row')],
            [
                InlineKeyboardButton(
                    "🔎 Номер колонки с артикулом",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_col'
                )
            ],
            [
                InlineKeyboardButton(
                    "🧪 Условия отбора артикулов",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_filter'
                )
            ],
            [
                InlineKeyboardButton(
                    "🧪 Условия отбора по еще одной колонке",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|extra_filter'
                )
            ],
            [
                InlineKeyboardButton(
                    "🏷️ Префикс в артикуле",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_prefix'
                )
            ],
            [
                InlineKeyboardButton(
                    "🏷️ Постфикс артикула",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_postfix'
                )
            ],
            [
                InlineKeyboardButton(
                    "🧹 Изменение входящего артикула",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_transform'
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Колонки с данными",
                    callback_data=f'supplier_stock_processing_columns|menu|{variant_index}'
                )
            ],
            [
                InlineKeyboardButton(
                    "🧾 Формат файла на выходе",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_format'
                )
            ],
            [
                InlineKeyboardButton(
                    f"📦 Файл для ОРК: {orc_text}",
                    callback_data=f'supplier_stock_processing_variant|toggle_orc|{variant_index}'
                )
            ],
        ])
        if orc_enabled:
            keyboard.append([
                InlineKeyboardButton(
                    "⚙️ Настройки файла ОРК",
                    callback_data=f'supplier_stock_processing_orc|menu|{variant_index}'
                )
            ])
    else:
        keyboard.append([
            InlineKeyboardButton("📄 Имя файла на выходе", callback_data='supplier_stock_processing_rule|field|output_name')
        ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_processing_rule|back'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
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

    article_col = variant.get("article_col") or "не задано"
    article_filter = _escape_pattern_text(variant.get("article_filter") or "не задано")
    extra_filter_col = variant.get("extra_filter_col")
    extra_filter = variant.get("extra_filter")
    if extra_filter_col and extra_filter:
        extra_filter_text = f"№{extra_filter_col}: {_escape_pattern_text(extra_filter)}"
    else:
        extra_filter_text = "не задано"
    article_prefix = _escape_pattern_text(variant.get("article_prefix") or "не задано")
    article_postfix = _escape_pattern_text(variant.get("article_postfix") or "не задано")
    article_transform = variant.get("article_transform") or {}
    transform_pattern = article_transform.get("pattern") or ""
    transform_replacement = article_transform.get("replacement") or ""
    if transform_pattern:
        transform_text = f"{_escape_pattern_text(transform_pattern)} => {_escape_pattern_text(transform_replacement)}"
    else:
        transform_text = "не задано"
    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    output_format = variant.get("output_format") or "не задано"
    orc = variant.get("orc", {})
    orc_enabled = orc.get("enabled", False)
    orc_text = "да" if orc_enabled else "нет"
    orc_column = orc.get("column") or "не задано"
    orc_input_index = orc.get("input_index")
    orc_output_index = orc.get("output_index")
    orc_output_format = orc.get("output_format")
    orc_output_name = _escape_pattern_text(orc.get("output_name") or "")
    if orc_output_format:
        orc_output_text = orc_output_format
    elif output_format != "не задано":
        orc_output_text = f"как основной ({output_format})"
    else:
        orc_output_text = "не задано"

    message = (
        "📦 *Настройка файла обработки*\n\n"
        f"• Номер колонки с артикулом: `{article_col}`\n"
        f"• Условия отбора артикулов: `{article_filter}`\n"
        f"• Условия отбора по доп. колонке: `{extra_filter_text}`\n"
        f"• Префикс артикула: `{article_prefix}`\n"
        f"• Постфикс артикула: `{article_postfix}`\n"
        f"• Изменение входящего артикула: `{transform_text}`\n"
        f"• Колонки с данными: `{data_columns_count or 'не задано'}`\n"
        f"• Формат файла на выходе: `{output_format}`\n"
        f"• Файл для ОРК: `{orc_text}`"
    )
    if orc_enabled:
        message += (
            f"\n• Колонка данных для ОРК: `{orc_column}`"
            f"\n• Формат файла ОРК на выходе: `{_escape_pattern_text(orc_output_text)}`"
            f"\n• Имя выходного файла ОРК: `{orc_output_name or 'по умолчанию (_orc)'}`"
        )
        if orc_input_index:
            message += f"\n• Файл источника (вход): `№{orc_input_index}`"
        if orc_output_index:
            output_label = f"№{orc_output_index}"
            if data_columns_count and orc_output_index <= data_columns_count:
                names = variant.get("output_names", [])
                name_value = names[orc_output_index - 1] if orc_output_index - 1 < len(names) else ""
                if name_value:
                    output_label = f"{orc_output_index}. {_escape_pattern_text(name_value)}"
            message += f"\n• Файл источника (выход): `{output_label}`"

    keyboard = [
        [InlineKeyboardButton("— Настройки файла —", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("🔎 Номер колонки с артикулом", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_col')],
        [InlineKeyboardButton("🧪 Условия отбора артикулов", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_filter')],
        [
            InlineKeyboardButton(
                "🧪 Условия отбора по еще одной колонке",
                callback_data=f'supplier_stock_processing_variant|field|{variant_index}|extra_filter'
            )
        ],
        [InlineKeyboardButton("🏷️ Префикс в артикуле", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_prefix')],
        [InlineKeyboardButton("🏷️ Постфикс артикула", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_postfix')],
        [InlineKeyboardButton("🧹 Изменение входящего артикула", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|article_transform')],
    ]

    keyboard.append([InlineKeyboardButton("— Колонки с данными —", callback_data='supplier_stock_noop')])
    keyboard.append([
        InlineKeyboardButton("➕ Добавить колонку", callback_data=f'supplier_stock_processing_variant|add_column|{variant_index}')
    ])

    if data_columns_count:
        for idx in range(data_columns_count):
            label = variant.get("data_columns", [])
            value = label[idx] if idx < len(label) else "не задано"
            keyboard.append([
                InlineKeyboardButton(
                    f"📈 Колонка {idx + 1}: {value or 'не задано'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|data_column|{idx}'
                )
            ])
        keyboard.append([InlineKeyboardButton("— Имена файлов —", callback_data='supplier_stock_noop')])
        for idx in range(data_columns_count):
            names = variant.get("output_names", [])
            name_value = names[idx] if idx < len(names) else "не задано"
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 Имя файла {idx + 1}: {name_value or 'не задано'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_name|{idx}'
                )
            ])

    keyboard.extend([
        [InlineKeyboardButton("🧾 Формат файла на выходе", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_format')],
        [InlineKeyboardButton(f"📦 Файл для ОРК: {orc_text}", callback_data=f'supplier_stock_processing_variant|toggle_orc|{variant_index}')],
    ])

    if orc_enabled:
        keyboard.extend([
            [InlineKeyboardButton("— Файл для ОРК —", callback_data='supplier_stock_noop')],
            [InlineKeyboardButton("🏷️ Префикс в артикуле", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_prefix')],
            [InlineKeyboardButton("📦 Stor", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_stor')],
            [InlineKeyboardButton("📈 Колонка с данными", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_column')],
            [
                InlineKeyboardButton(
                    "🧾 Формат файла ОРК на выходе",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_output_format'
                )
            ],
        ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_processing_rule|menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
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
    filter_text = "да" if use_article_filter else "нет"
    message_lines = [
        "📊 *Колонки с данными*\n",
        f"Количество колонок: `{data_columns_count or 0}`",
        f"Использовать условия отбора артикулов: `{filter_text}`",
    ]
    for idx in range(data_columns_count or 0):
        col_value = columns[idx] if idx < len(columns) else "не задано"
        name_value = names[idx] if idx < len(names) else "не задано"
        filter_enabled = column_filters[idx] if idx < len(column_filters) else True
        filter_text_line = "да" if filter_enabled else "нет"
        message_lines.append(
            f"{idx + 1}. Колонка: `{col_value or 'не задано'}` → файл: `{_escape_pattern_text(name_value)}`"
            f" (фильтр: `{filter_text_line}`)"
        )
    message = "\n".join(message_lines)

    toggle_text = (
        "✅ Использовать условия отбора артикулов"
        if use_article_filter
        else "⛔️ Не использовать условия отбора артикулов"
    )
    keyboard = [
        [InlineKeyboardButton("— Колонки с данными —", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton(toggle_text, callback_data=f'supplier_stock_processing_columns|toggle_article_filter|{variant_index}')],
        [InlineKeyboardButton("➕ Добавить колонку", callback_data=f'supplier_stock_processing_columns|add_column|{variant_index}')],
    ]

    if data_columns_count:
        for idx in range(data_columns_count):
            value = columns[idx] if idx < len(columns) else "не задано"
            keyboard.append([
                InlineKeyboardButton(
                    f"📈 Колонка {idx + 1}: {value or 'не задано'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|data_column|{idx}'
                ),
                InlineKeyboardButton(
                    "🗑️",
                    callback_data=f'supplier_stock_processing_columns|remove_column|{variant_index}|{idx}'
                ),
            ])
            filter_enabled = column_filters[idx] if idx < len(column_filters) else True
            filter_toggle_text = (
                f"✅ Фильтр артикулов {idx + 1}"
                if filter_enabled
                else f"⛔️ Фильтр артикулов {idx + 1}"
            )
            keyboard.append([
                InlineKeyboardButton(
                    filter_toggle_text,
                    callback_data=f'supplier_stock_processing_columns|tac|{variant_index}|{idx}'
                )
            ])
        keyboard.append([InlineKeyboardButton("— Имена файлов —", callback_data='supplier_stock_noop')])
        for idx in range(data_columns_count):
            name_value = names[idx] if idx < len(names) else "не задано"
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 Имя файла {idx + 1}: {name_value or 'не задано'}",
                    callback_data=f'supplier_stock_processing_variant|field|{variant_index}|output_name|{idx}'
                )
            ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_processing_rule|menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
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
    orc_prefix = _escape_pattern_text(orc.get("prefix") or "не задано")
    orc_stor = _escape_pattern_text(orc.get("stor") or "не задано")
    orc_column = orc.get("column") or "не задано"
    orc_input_index = orc.get("input_index")
    orc_output_index = orc.get("output_index")
    base_output_format = variant.get("output_format")
    orc_output_format = orc.get("output_format")
    orc_output_name = _escape_pattern_text(orc.get("output_name") or "")
    if orc_output_format:
        orc_output_text = orc_output_format
    elif base_output_format:
        orc_output_text = f"как основной ({base_output_format})"
    else:
        orc_output_text = "не задано"

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
        "📦 *Файл для ОРК*\n",
        f"• Префикс в артикуле: `{orc_prefix}`",
        f"• Stor: `{orc_stor}`",
        f"• Колонка с данными: `{orc_column}`",
        f"• Формат файла ОРК на выходе: `{_escape_pattern_text(orc_output_text)}`",
        f"• Имя выходного файла ОРК: `{orc_output_name or 'по умолчанию (_orc)'}`",
    ]
    if input_count > 1:
        input_label = f"№{orc_input_index}" if orc_input_index else "не задано"
        message_lines.append(f"• Файл источника (вход): `{input_label}`")
    if data_columns_count > 1:
        output_label = "не задано"
        if orc_output_index:
            output_label = f"№{orc_output_index}"
            if orc_output_index <= data_columns_count:
                name_value = output_names[orc_output_index - 1] if orc_output_index - 1 < len(output_names) else ""
                if name_value:
                    output_label = f"{orc_output_index}. {_escape_pattern_text(name_value)}"
        message_lines.append(f"• Файл источника (выход): `{output_label}`")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("— Файл для ОРК —", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("🏷️ Префикс в артикуле", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_prefix')],
        [InlineKeyboardButton("📦 Stor", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_stor')],
        [InlineKeyboardButton("📈 Колонка с данными", callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_column')],
        [
            InlineKeyboardButton(
                "📄 Имя выходного файла ОРК",
                callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_output_name'
            )
        ],
        [
            InlineKeyboardButton(
                "🧾 Формат файла ОРК на выходе",
                callback_data=f'supplier_stock_processing_variant|field|{variant_index}|orc_output_format'
            )
        ],
    ]

    if input_count > 1:
        keyboard.append([InlineKeyboardButton("— Файл источника (вход) —", callback_data='supplier_stock_noop')])
        for idx in range(1, input_count + 1):
            selected = "✅" if orc_input_index == idx else "📥"
            keyboard.append([
                InlineKeyboardButton(
                    f"{selected} Вход {idx}",
                    callback_data=f'supplier_stock_processing_orc|set_input|{variant_index}|{idx}'
                )
            ])
        if orc_input_index:
            keyboard.append([
                InlineKeyboardButton(
                    "🚫 Сбросить выбор входа",
                    callback_data=f'supplier_stock_processing_orc|clear_input|{variant_index}'
                )
            ])

    if data_columns_count > 1:
        keyboard.append([InlineKeyboardButton("— Файл источника (выход) —", callback_data='supplier_stock_noop')])
        for idx in range(1, data_columns_count + 1):
            name_value = output_names[idx - 1] if idx - 1 < len(output_names) else ""
            label = f"Выход {idx}"
            if name_value:
                label = f"{idx}. {name_value}"
            selected = "✅" if orc_output_index == idx else "📤"
            keyboard.append([
                InlineKeyboardButton(
                    f"{selected} {label}",
                    callback_data=f'supplier_stock_processing_orc|set_output|{variant_index}|{idx}'
                )
            ])
        if orc_output_index:
            keyboard.append([
                InlineKeyboardButton(
                    "🚫 Сбросить выбор выхода",
                    callback_data=f'supplier_stock_processing_orc|clear_output|{variant_index}'
                )
            ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_processing_rule|menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
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
                "❌ Правило не найдено.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
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
            "ℹ️ Название и файл источника берутся из настроек источника.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_processing_rule|menu')]
            ])
        )
        return

    context.user_data['supplier_stock_processing_field'] = field
    context.user_data['supplier_stock_processing_variant_index'] = variant_index
    context.user_data['supplier_stock_processing_item_index'] = item_index

    prompts = {
        "name": "Введите название правила:",
        "source_file": "Введите имя файла источника:",
        "data_row": "Введите номер первой строки с данными:",
        "output_name": "Введите имя файла на выходе (можно использовать {index}, {name}, {filename}):",
        "article_col": "Введите номер колонки с артикулом:",
        "article_filter": (
            "Введите условия отбора артикулов (regex) или '-' для всех.\n\n"
            "Примеры:\n"
            "• $1 ~ /^[0-9]/ && $col+0 > 0\n"
            "• $1 ~ /^[A-Z].*/ && $4 ~ /^[0-9]+$/\n"
            "• grep -E '^DKS [0-9A-Z]{6,},'\n"
            "• gsub(/^\\./, \"\", art); gsub(/[A-Za-z]+$/, \"\", art);\n"
            "• ($3+0 > 0) && ($4 == \"Москва\")"
        ),
        "extra_filter": (
            "Введите номер колонки и условие отбора (regex) через ';'.\n"
            "Пример: 4;^Москва$\n"
            "Или '-' чтобы отключить дополнительный фильтр."
        ),
        "article_prefix": (
            "Введите префикс артикула (или '-' если не нужен). "
            "Если нужен пробел в конце, можно указать \\s:"
        ),
        "article_postfix": "Введите постфикс артикула (или '-' если не нужен). Пробелы в конце сохраняются:",
        "article_transform": (
            "Введите правило изменения артикула (regex) или '-' чтобы отключить.\n\n"
            "Формат: паттерн => замена (замена может быть пустой).\n"
            "Примеры:\n"
            "• ^0+ =>\n"
            "• [^0-9A-Za-z]+ =>\n"
            "• \\s+ => -"
        ),
        "data_column": "Введите номер колонки с данными:",
        "output_format": "Введите формат выходного файла (xls, xlsx, csv):",
        "orc_prefix": "Введите префикс артикула для файла ОРК (или '-' если не нужен):",
        "orc_stor": "Введите параметр Stor для файла ОРК:",
        "orc_column": "Введите номер колонки с данными для файла ОРК:",
        "orc_output_name": (
            "Введите имя выходного файла ОРК "
            "(можно использовать {index}, {name}, {filename}) "
            "или '-' чтобы использовать добавление _orc:"
        ),
        "orc_output_format": (
            "Введите формат файла ОРК на выходе (xls, xlsx, csv) "
            "или '-' чтобы использовать формат основного файла:"
        ),
    }
    prompt = prompts.get(field, "Введите значение:")
    if field == "output_name" and variant_index is not None:
        prompt = "Введите имя выходного файла (можно использовать {index}, {name}, {filename}):"

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
                    current_value = f"как основной ({variant.get('output_format')})"
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
        f"{prompt}\n\nТекущее значение: {current_hint}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
        ])
    )

def _validate_processing_rule(data: dict) -> list[str]:
    missing = []
    if data.get("requires_processing", True):
        variants = data.get("variants", [])
        variants_count = len(variants)
        if not variants_count:
            missing.append("файлы обработки")
        if not data.get("data_row"):
            missing.append("первая строка с данными")
        for idx in range(variants_count):
            variant = _ensure_processing_variant(data, idx)
            if not variant.get("article_col"):
                missing.append(f"колонка артикула (файл {idx + 1})")
            columns_count = variant.get("data_columns_count") or max(
                len(variant.get("data_columns", [])),
                len(variant.get("output_names", [])),
            )
            if not columns_count:
                missing.append(f"кол-во колонок (файл {idx + 1})")
            columns = variant.get("data_columns", [])
            if any(col is None for col in columns) or len(columns) < columns_count:
                missing.append(f"колонки данных (файл {idx + 1})")
            names = variant.get("output_names", [])
            if len(names) < columns_count or any(not name for name in names):
                missing.append(f"имена файлов (файл {idx + 1})")
            if not variant.get("output_format"):
                missing.append(f"формат файла (файл {idx + 1})")
            orc = variant.get("orc", {})
            if orc.get("enabled"):
                if not orc.get("stor"):
                    missing.append(f"Stor ОРК (файл {idx + 1})")
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
        query.answer("Заполните: " + ", ".join(missing), show_alert=True)
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
        "✅ Настройки сохранены.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
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
        "✅ Настройки сохранены.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
        ])
    )

def show_supplier_stock_mail_sources_menu(update, context):
    """Показать список правил вложений для почты."""
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
        message = "📎 *Правила вложений*\n\n❌ Правила не настроены."
    else:
        message_lines = ["📎 *Правила вложений*\n"]
        for index, source in enumerate(sources, start=1):
            name = _escape_pattern_text(source.get("name") or source.get("id") or f"Правило {index}")
            sender = _escape_pattern_text(source.get("sender_pattern") or "любой")
            subject = _escape_pattern_text(source.get("subject_pattern") or "любой")
            mime_pattern = _escape_pattern_text(source.get("mime_pattern") or "application/.*")
            filename_pattern = _escape_pattern_text(source.get("filename_pattern") or "любой")
            expected = source.get("expected_attachments", 1)
            output_template = _escape_pattern_text(source.get("output_template") or "не задано")
            enabled = source.get("enabled", True)
            unpack_enabled = source.get("unpack_archive", False)
            status_icon = "🟢" if enabled else "🔴"
            unpack_text = "да" if unpack_enabled else "нет"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   • Отправитель: `{sender}`\n"
                    f"   • Тема: `{subject}`\n"
                    f"   • MIME: `{mime_pattern}`\n"
                    f"   • Имя файла: `{filename_pattern}`\n"
                    f"   • Ожидается: `{expected}`\n"
                    f"   • Шаблон: `{output_template}`\n"
                    f"   • Распаковка: `{unpack_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить правило", callback_data='supplier_stock_mail_source_add')],
    ]

    for source in sources:
        source_id = source.get("id") or ""
        if not source_id:
            continue
        enabled = source.get("enabled", True)
        unpack_enabled = source.get("unpack_archive", False)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        unpack_text = "📦 Распаковка: вкл" if unpack_enabled else "📦 Распаковка: выкл"
        keyboard.append([
            InlineKeyboardButton(
                f"⚙️ {source.get('name', source_id)}",
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
                "🗑️",
                callback_data=f'supplier_stock_mail_source_delete_{source_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_schedule_menu(update, context):
    """Показать меню расписания загрузки остатков поставщиков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop('supplier_stock_edit', None)

    config = get_supplier_stock_config()
    schedule = config.get("download", {}).get("schedule", {})
    schedule_state = "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено"
    schedule_time = schedule.get("time", "не задано")

    message = (
        "⏰ *Расписание загрузки остатков*\n\n"
        f"Статус: {schedule_state}\n"
        f"Время: {schedule_time}\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Включить/выключить", callback_data='supplier_stock_schedule_toggle')],
        [InlineKeyboardButton("🕒 Изменить время", callback_data='supplier_stock_schedule_time')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_download'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_sources_menu(update, context):
    """Показать список источников файлов остатков."""
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
        message = "📦 *Источники файлов остатков*\n\n❌ Источники не настроены."
    else:
        message_lines = ["📦 *Источники файлов остатков*\n"]
        for index, source in enumerate(sources, start=1):
            name = _escape_pattern_text(source.get("name") or source.get("id") or f"Источник {index}")
            url = _escape_pattern_text(source.get("url") or "URL не задан")
            output_name = _escape_pattern_text(source.get("output_name") or "не задано")
            method = _escape_pattern_text(source.get("method") or "http")
            processing_mode = _escape_pattern_text(_supplier_stock_processing_mode_label(source.get("processing_mode")))
            enabled = source.get("enabled", True)
            unpack_enabled = source.get("unpack_archive", False)
            status_icon = "🟢" if enabled else "🔴"
            unpack_text = "да" if unpack_enabled else "нет"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   • URL: `{url}`\n"
                    f"   • Файл: `{output_name}`\n"
                    f"   • Метод: `{method}`\n"
                    f"   • Обработка: `{processing_mode}`\n"
                    f"   • Распаковка: `{unpack_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить источник", callback_data='supplier_stock_source_add')],
    ]

    for source in sources:
        source_id = source.get("id") or ""
        if not source_id:
            continue
        enabled = source.get("enabled", True)
        unpack_enabled = source.get("unpack_archive", False)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        unpack_text = "📦 Распаковка: вкл" if unpack_enabled else "📦 Распаковка: выкл"
        keyboard.append([
            InlineKeyboardButton(
                f"⚙️ {source.get('name', source_id)}",
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
                "🗑️",
                callback_data=f'supplier_stock_source_delete_{source_id}'
            ),
        ])

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_download'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_source_settings(update, context, source_id: str):
    """Показать настройки конкретного источника остатков."""
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
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return

    name = _escape_pattern_text(source.get("name") or source_id)
    url = _escape_pattern_text(source.get("url") or "не задан")
    output_name = _escape_pattern_text(source.get("output_name") or "не задано")
    method = _escape_pattern_text(source.get("method") or "http")
    processing_mode = source.get("processing_mode") or "table"
    processing_label = _escape_pattern_text(_supplier_stock_processing_mode_label(processing_mode))
    discover = source.get("discover")
    discover_text = "не задано"
    if isinstance(discover, dict):
        discover_text = _escape_pattern_text(
            f"{discover.get('url', '')} | {discover.get('pattern', '')} | {discover.get('prefix', '')}"
        )
    vars_map = source.get("vars") or {}
    vars_text = ", ".join([f"{key}={value}" for key, value in vars_map.items()]) if vars_map else "не задано"
    auth_state = "задано" if source.get("auth") else "не задано"
    pre_request = source.get("pre_request") or {}
    pre_request_text = "не задано"
    if pre_request:
        pre_request_text = _escape_pattern_text(f"{pre_request.get('url', '')} | {pre_request.get('data', '')}")
    options = []
    if source.get("include_headers"):
        options.append("headers")
    if source.get("append"):
        options.append("append")
    options_text = ", ".join(options) if options else "не задано"
    upload_subdir = _escape_pattern_text(source.get("upload_subdir") or "не задано")
    individual_dir = source.get("individual_directory") or {}
    individual_enabled = individual_dir.get("enabled", False)
    individual_status = "вкл" if individual_enabled else "выкл"
    individual_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")
    status_icon = "🟢" if source.get("enabled", True) else "🔴"
    unpack_text = "вкл" if source.get("unpack_archive", False) else "выкл"

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
            ", ".join([f"{key}={value}" for key, value in stores.items()]) or "не задано"
        )
        orc_text = _escape_pattern_text(
            ", ".join([f"{item.get('key')}={item.get('stor')}" for item in orc_stores if isinstance(item, dict)])
            or "не задано"
        )
        outputs_text = _escape_pattern_text(
            ", ".join([f"{key}={value}" for key, value in outputs.items()]) or "не задано"
        )
        prefix_text = _escape_pattern_text(iek_settings.get("prefix") or "не задано")
        msk_stores = iek_settings.get("msk_stores", [])
        msk_text = _escape_pattern_text(", ".join(msk_stores) or "не задано")
        nsk_text = _escape_pattern_text(iek_settings.get("nsk_store") or "не задано")
        iek_section = [
            "⚙️ *IEK JSON*",
            f"• Склады: `{stores_text}`",
            f"• МСК склады: `{msk_text}`",
            f"• НСК склад: `{nsk_text}`",
            f"• ORK stor: `{orc_text}`",
            f"• Префикс артикула: `{prefix_text}`",
            f"• Файлы: `{outputs_text}`",
        ]

    message_lines = [
        f"⚙️ *Источник остатков*\n",
        f"{status_icon} *{name}*",
        f"• URL: `{url}`",
        f"• Файл: `{output_name}`",
        f"• Метод: `{method}`",
        f"• Обработка: `{processing_label}`",
        f"• Поиск ссылки: `{discover_text}`",
        f"• Переменные: `{_escape_pattern_text(vars_text)}`",
        f"• Авторизация: `{auth_state}`",
        f"• Предзапрос: `{pre_request_text}`",
        f"• Опции: `{_escape_pattern_text(options_text)}`",
        f"• Подкаталог выгрузки: `{upload_subdir}`",
        f"• Индивидуальный каталог: `{individual_status}`",
        f"• UNC индивидуального каталога: `{individual_path}`",
        f"• Распаковка: `{unpack_text}`",
    ]
    if iek_section:
        message_lines.extend(["", *iek_section])
    message_lines.extend([
        "\n🧩 *Обработка файлов*",
        f"Правил: {len(matched_rules)}",
    ])
    if matched_rules:
        for index, rule in enumerate(matched_rules, start=1):
            rule_name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"Правило {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "не задано")
            enabled = rule.get("enabled", True)
            status = "🟢" if enabled else "🔴"
            message_lines.append(f"{index}. {status} *{rule_name}* (`{source_file}`)")

    message_lines.append("\nВыберите настройку:")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("— Настройки источника —", callback_data='supplier_stock_noop')],
        [
            InlineKeyboardButton("✏️ Название", callback_data=f'supplier_stock_source_field|{source_id}|name'),
            InlineKeyboardButton("🔗 URL", callback_data=f'supplier_stock_source_field|{source_id}|url'),
        ],
        [
            InlineKeyboardButton("🔎 Поиск ссылки", callback_data=f'supplier_stock_source_field|{source_id}|discover'),
            InlineKeyboardButton("🧩 Переменные", callback_data=f'supplier_stock_source_field|{source_id}|vars'),
        ],
        [
            InlineKeyboardButton("📄 Имя файла", callback_data=f'supplier_stock_source_field|{source_id}|output_name'),
            InlineKeyboardButton("🔐 Авторизация", callback_data=f'supplier_stock_source_field|{source_id}|auth'),
        ],
        [
            InlineKeyboardButton("📬 Предзапрос", callback_data=f'supplier_stock_source_field|{source_id}|pre_request'),
            InlineKeyboardButton("⚙️ Опции", callback_data=f'supplier_stock_source_field|{source_id}|options'),
        ],
        [
            InlineKeyboardButton("🧩 Тип обработки", callback_data=f'supplier_stock_source_field|{source_id}|processing_mode'),
            InlineKeyboardButton("📂 Подкаталог выгрузки", callback_data=f'supplier_stock_source_field|{source_id}|upload_subdir'),
        ],
    ]
    if processing_mode == "iek_json":
        keyboard.append([
            InlineKeyboardButton("⚙️ IEK JSON", callback_data=f'supplier_stock_source_iek_settings|{source_id}')
        ])
    keyboard.extend([
        [
            InlineKeyboardButton("📁 Индивидуальный каталог", callback_data=f'supplier_stock_source_individual|{source_id}'),
        ],
        [
            InlineKeyboardButton("🔁 Включить/выключить", callback_data=f'supplier_stock_source_toggle_{source_id}'),
            InlineKeyboardButton(f"📦 Распаковка: {unpack_text}", callback_data=f'supplier_stock_source_unpack_toggle_{source_id}')
        ],
        [InlineKeyboardButton("— Обработка файлов —", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("📋 Правила обработки", callback_data=f'supplier_stock_processing_source|{source_id}|menu')],
        [InlineKeyboardButton("➕ Добавить правило", callback_data=f'supplier_stock_processing_source|{source_id}|add')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [
            InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ],
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_individual_settings(update, context, source_id: str) -> None:
    """Показать настройки индивидуального каталога источника."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return

    individual_dir = source.get("individual_directory") or {}
    enabled = individual_dir.get("enabled", False)
    status_text = "🟢 Включено" if enabled else "🔴 Выключено"
    unc_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")
    login = _escape_pattern_text(individual_dir.get("login") or "не задано")
    password = "задано" if individual_dir.get("password") else "не задано"

    message = (
        "📁 *Индивидуальный каталог*\n\n"
        f"Статус: {status_text}\n"
        f"UNC путь: `{unc_path}`\n"
        f"Логин: `{login}`\n"
        f"Пароль: `{password}`\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Включить/выключить", callback_data=f'supplier_stock_source_individual_toggle_{source_id}')],
        [
            InlineKeyboardButton("📂 UNC путь", callback_data=f'supplier_stock_source_field|{source_id}|individual_path'),
            InlineKeyboardButton("👤 Логин", callback_data=f'supplier_stock_source_field|{source_id}|individual_login'),
        ],
        [InlineKeyboardButton("🔐 Пароль", callback_data=f'supplier_stock_source_field|{source_id}|individual_password')],
        [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_source_settings|{source_id}')],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_iek_settings(update, context, source_id: str) -> None:
    """Показать настройки обработки IEK JSON."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return

    iek_settings = source.get("iek_json") or {}
    stores = iek_settings.get("stores", {})
    orc_stores = iek_settings.get("orc_stores", [])
    outputs = iek_settings.get("outputs", {})

    stores_text = _escape_pattern_text(", ".join([f"{key}={value}" for key, value in stores.items()]) or "не задано")
    orc_text = _escape_pattern_text(
        ", ".join([f"{item.get('key')}={item.get('stor')}" for item in orc_stores if isinstance(item, dict)])
        or "не задано"
    )
    outputs_text = _escape_pattern_text(
        ", ".join([f"{key}={value}" for key, value in outputs.items()]) or "не задано"
    )
    prefix_text = _escape_pattern_text(iek_settings.get("prefix") or "не задано")
    msk_stores = iek_settings.get("msk_stores", [])
    msk_text = _escape_pattern_text(", ".join(msk_stores) or "не задано")
    nsk_text = _escape_pattern_text(iek_settings.get("nsk_store") or "не задано")

    message = (
        "⚙️ *IEK JSON*\n\n"
        f"Склады: `{stores_text}`\n"
        f"МСК склады: `{msk_text}`\n"
        f"НСК склад: `{nsk_text}`\n"
        f"ОРК stor: `{orc_text}`\n"
        f"Префикс артикула: `{prefix_text}`\n"
        f"Файлы: `{outputs_text}`\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("🗺️ Склады", callback_data=f'supplier_stock_source_iek_field|{source_id}|stores')],
        [InlineKeyboardButton("📍 МСК склады", callback_data=f'supplier_stock_source_iek_field|{source_id}|msk_stores')],
        [InlineKeyboardButton("📍 НСК склад", callback_data=f'supplier_stock_source_iek_field|{source_id}|nsk_store')],
        [InlineKeyboardButton("🧾 ORK stor", callback_data=f'supplier_stock_source_iek_field|{source_id}|orc_stores')],
        [InlineKeyboardButton("🏷️ Префикс артикула", callback_data=f'supplier_stock_source_iek_field|{source_id}|prefix')],
        [InlineKeyboardButton("📄 Файлы", callback_data=f'supplier_stock_source_iek_field|{source_id}|outputs')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [
            InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_source_settings|{source_id}'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_supplier_stock_mail_source_settings(update, context, source_id: str):
    """Показать настройки правила вложений."""
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
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    name = _escape_pattern_text(source.get("name") or source_id)
    sender = _escape_pattern_text(source.get("sender_pattern") or "любой")
    subject = _escape_pattern_text(source.get("subject_pattern") or "любой")
    mime_pattern = _escape_pattern_text(source.get("mime_pattern") or "application/.*")
    filename_pattern = _escape_pattern_text(source.get("filename_pattern") or "любой")
    expected = source.get("expected_attachments", 1)
    output_template = _escape_pattern_text(source.get("output_template") or "не задано")
    enabled = source.get("enabled", True)
    unpack_enabled = source.get("unpack_archive", False)
    status_icon = "🟢" if enabled else "🔴"
    unpack_text = "вкл" if unpack_enabled else "выкл"
    upload_subdir = _escape_pattern_text(source.get("upload_subdir") or "не задано")
    individual_dir = source.get("individual_directory") or {}
    individual_enabled = individual_dir.get("enabled", False)
    individual_status = "вкл" if individual_enabled else "выкл"
    individual_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")

    rules = config.get("processing", {}).get("rules", [])
    matched_rules = [
        rule for rule in rules
        if _processing_rule_matches_source(rule, source_id, "mail", config)
    ]

    message_lines = [
        "📎 *Правило вложений*\n",
        f"{status_icon} *{name}*",
        f"• Отправитель: `{sender}`",
        f"• Тема: `{subject}`",
        f"• MIME: `{mime_pattern}`",
        f"• Имя файла: `{filename_pattern}`",
        f"• Ожидается: `{expected}`",
        f"• Шаблон: `{output_template}`",
        f"• Подкаталог выгрузки: `{upload_subdir}`",
        f"• Индивидуальный каталог: `{individual_status}`",
        f"• UNC индивидуального каталога: `{individual_path}`",
        f"• Распаковка: `{unpack_text}`\n",
        "🧩 *Обработка файлов*",
        f"Правил: {len(matched_rules)}",
    ]
    if matched_rules:
        for index, rule in enumerate(matched_rules, start=1):
            rule_name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"Правило {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "не задано")
            enabled_rule = rule.get("enabled", True)
            status = "🟢" if enabled_rule else "🔴"
            message_lines.append(f"{index}. {status} *{rule_name}* (`{source_file}`)")

    message_lines.append("\nВыберите настройку:")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("— Настройки правила —", callback_data='supplier_stock_noop')],
        [
            InlineKeyboardButton("✏️ Название", callback_data=f'supplier_stock_mail_field|{source_id}|name'),
            InlineKeyboardButton("👤 Отправитель", callback_data=f'supplier_stock_mail_field|{source_id}|sender'),
        ],
        [
            InlineKeyboardButton("📝 Тема", callback_data=f'supplier_stock_mail_field|{source_id}|subject'),
            InlineKeyboardButton("🧾 MIME", callback_data=f'supplier_stock_mail_field|{source_id}|mime'),
        ],
        [
            InlineKeyboardButton("📄 Имя файла", callback_data=f'supplier_stock_mail_field|{source_id}|filename'),
            InlineKeyboardButton("🔢 Кол-во вложений", callback_data=f'supplier_stock_mail_field|{source_id}|expected'),
        ],
        [
            InlineKeyboardButton("📦 Шаблон файла", callback_data=f'supplier_stock_mail_field|{source_id}|output'),
        ],
        [
            InlineKeyboardButton("📂 Подкаталог выгрузки", callback_data=f'supplier_stock_mail_field|{source_id}|upload_subdir'),
            InlineKeyboardButton("📁 Индивидуальный каталог", callback_data=f'supplier_stock_mail_source_individual|{source_id}'),
        ],
        [
            InlineKeyboardButton("🔁 Включить/выключить", callback_data=f'supplier_stock_mail_source_toggle_{source_id}'),
            InlineKeyboardButton(f"📦 Распаковка: {unpack_text}", callback_data=f'supplier_stock_mail_source_unpack_toggle_{source_id}')
        ],
        [InlineKeyboardButton("— Обработка файлов —", callback_data='supplier_stock_noop')],
        [InlineKeyboardButton("📋 Правила обработки", callback_data=f'supplier_stock_processing_mail|{source_id}|menu')],
        [InlineKeyboardButton("➕ Добавить правило", callback_data=f'supplier_stock_processing_mail|{source_id}|add')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [
            InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_mail_source_individual_settings(update, context, source_id: str) -> None:
    """Показать настройки индивидуального каталога правила вложений."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    individual_dir = source.get("individual_directory") or {}
    enabled = individual_dir.get("enabled", False)
    status_text = "🟢 Включено" if enabled else "🔴 Выключено"
    unc_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")
    login = _escape_pattern_text(individual_dir.get("login") or "не задано")
    password = "задано" if individual_dir.get("password") else "не задано"

    message = (
        "📁 *Индивидуальный каталог*\n\n"
        f"Статус: {status_text}\n"
        f"UNC путь: `{unc_path}`\n"
        f"Логин: `{login}`\n"
        f"Пароль: `{password}`\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Включить/выключить", callback_data=f'supplier_stock_mail_source_individual_toggle_{source_id}')],
        [
            InlineKeyboardButton("📂 UNC путь", callback_data=f'supplier_stock_mail_field|{source_id}|individual_path'),
            InlineKeyboardButton("👤 Логин", callback_data=f'supplier_stock_mail_field|{source_id}|individual_login'),
        ],
        [InlineKeyboardButton("🔐 Пароль", callback_data=f'supplier_stock_mail_field|{source_id}|individual_password')],
        [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_mail_source_settings|{source_id}')],
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def supplier_stock_start_source_field_edit(update, context, source_id: str, field: str) -> None:
    """Запросить изменение конкретного поля источника."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_source_field'] = field
    context.user_data['supplier_stock_source_field_id'] = source_id

    prompts = {
        "name": "Введите название источника (или '-' чтобы оставить):",
        "url": "Введите URL для скачивания (или '-' чтобы оставить):",
        "discover": "Введите параметры поиска URL (URL | regex | prefix), '-' чтобы оставить или 'none' чтобы очистить:",
        "vars": "Введите переменные подстановки key=value через запятую, '-' чтобы оставить или 'none' чтобы очистить:",
        "output_name": "Введите имя файла назначения (или '-' чтобы оставить):",
        "auth": "Введите login:password, '-' чтобы оставить или 'none' чтобы очистить:",
        "pre_request": "Введите URL | данные для предзапроса, '-' чтобы оставить или 'none' чтобы очистить:",
        "options": "Введите опции (headers, append) через запятую, '-' чтобы оставить или 'none' чтобы очистить:",
        "processing_mode": "Введите тип обработки (`table` или `iek\\_json`), '-' чтобы оставить:",
        "upload_subdir": "Введите подкаталог для выгрузки (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_path": "Введите UNC путь индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_login": "Введите логин индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_password": "Введите пароль индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    current_values = {
        "name": source.get("name") or source_id,
        "url": source.get("url") or "-",
        "discover": source.get("discover") or "-",
        "vars": source.get("vars") or "-",
        "output_name": source.get("output_name") or "-",
        "auth": "задано" if source.get("auth") else "-",
        "pre_request": source.get("pre_request") or "-",
        "options": "headers/append" if (source.get("include_headers") or source.get("append")) else "-",
        "processing_mode": source.get("processing_mode") or "table",
        "upload_subdir": source.get("upload_subdir") or "-",
        "individual_path": (source.get("individual_directory") or {}).get("unc_path") or "-",
        "individual_login": (source.get("individual_directory") or {}).get("login") or "-",
        "individual_password": "задано" if (source.get("individual_directory") or {}).get("password") else "-",
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    if isinstance(current_value, dict):
        current_value = json.dumps(current_value, ensure_ascii=False)
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data=f'supplier_stock_source_settings|{source_id}')]
        ])
    )

def supplier_stock_start_source_iek_field_edit(update, context, source_id: str, field: str) -> None:
    """Запросить изменение параметров IEK JSON."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_source_iek_field'] = field
    context.user_data['supplier_stock_source_iek_field_id'] = source_id

    prompts = {
        "stores": "Введите склады в формате key=uuid через запятую:",
        "msk_stores": "Введите список складов МСК через запятую (например: sherbinka, chehov):",
        "nsk_store": "Введите ключ склада НСК (например: novosibirsk):",
        "orc_stores": "Введите ORK stor в формате key=stor через запятую:",
        "prefix": "Введите префикс артикула для ORK (или 'none' чтобы очистить):",
        "outputs": "Введите имена файлов в формате orig=..., msk=..., nsk=..., orc=... через запятую:",
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

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    if isinstance(current_value, (dict, list)):
        current_value = json.dumps(current_value, ensure_ascii=False)

    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data=f'supplier_stock_source_iek_settings|{source_id}')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
        ])
    )

def supplier_stock_start_mail_source_field_edit(update, context, source_id: str, field: str) -> None:
    """Запросить изменение конкретного поля правила вложений."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_mail_source_field'] = field
    context.user_data['supplier_stock_mail_source_field_id'] = source_id

    prompts = {
        "name": "Введите название правила (или '-' чтобы оставить):",
        "sender": "Введите regex/адрес отправителя, '-' чтобы оставить или 'none' чтобы очистить:",
        "subject": "Введите regex темы письма, '-' чтобы оставить или 'none' чтобы очистить:",
        "mime": "Введите MIME-фильтр, '-' чтобы оставить или 'none' чтобы очистить:",
        "filename": "Введите regex имени вложения, '-' чтобы оставить или 'none' чтобы очистить:",
        "expected": "Введите количество ожидаемых вложений (или '-' чтобы оставить):",
        "output": "Введите шаблон имени выходного файла (или '-' чтобы оставить):",
        "upload_subdir": "Введите подкаталог для выгрузки (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_path": "Введите UNC путь индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_login": "Введите логин индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_password": "Введите пароль индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
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
        "individual_password": "задано" if (source.get("individual_directory") or {}).get("password") else "-",
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data=f'supplier_stock_mail_source_settings|{source_id}')]
        ])
    )


def supplier_stock_start_resource_wizard(update, context) -> None:
    """Запуск мастера добавления ресурса выгрузки."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_resource_stage'] = 'name'
    context.user_data['supplier_stock_resource_data'] = {}
    context.user_data['supplier_stock_resource_add'] = True

    query.edit_message_text(
        "➕ *Новый ресурс выгрузки*\n\nВведите название ресурса:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_resources')]
        ])
    )


def supplier_stock_start_resource_field_edit(update, context, resource_id: str, field: str) -> None:
    """Запросить изменение поля ресурса выгрузки."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        query.edit_message_text(
            "❌ Ресурс не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_resources')]
            ])
        )
        return

    context.user_data['supplier_stock_resource_field'] = field
    context.user_data['supplier_stock_resource_field_id'] = resource_id

    prompts = {
        "name": "Введите название ресурса (или '-' чтобы оставить):",
        "unc_path": "Введите UNC путь корневого каталога (или '-' чтобы оставить):",
        "login": "Введите логин ресурса (или '-' чтобы оставить, 'none' чтобы очистить):",
        "password": "Введите пароль ресурса (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    current_values = {
        "name": resource.get("name") or resource_id,
        "unc_path": resource.get("unc_path") or "-",
        "login": resource.get("login") or "-",
        "password": "задано" if resource.get("password") else "-",
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data=f'supplier_stock_resource_settings|{resource_id}')]
        ])
    )


def supplier_stock_start_ftp_field_edit(update, context, field: str) -> None:
    """Запросить изменение параметра FTP."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_ftp_field'] = field
    prompts = {
        "host": "Введите HOST FTP (или '-' чтобы оставить):",
        "login": "Введите логин FTP (или '-' чтобы оставить, 'none' чтобы очистить):",
        "password": "Введите пароль FTP (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})
    current_values = {
        "host": ftp_settings.get("host") or "-",
        "login": ftp_settings.get("login") or "-",
        "password": "задано" if ftp_settings.get("password") else "-",
    }
    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_ftp')]
        ])
    )

def supplier_stock_start_processing_wizard(
    update,
    context,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    """Запуск мастера добавления правила обработки."""
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
        "➕ *Новое правило обработки*\n\nВведите название правила:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data=back_callback)]
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
    """Запуск мастера редактирования правила обработки."""
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
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
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
        f"✏️ *Редактирование правила обработки*\n\n"
        f"Текущее имя: `{_escape_pattern_text(rule.get('name'))}`\n"
        "Введите новое имя (или '-' чтобы оставить текущее):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data=back_callback)]
        ])
    )

def supplier_stock_handle_processing_input(update, context):
    """Обработка ввода мастера настройки обработки."""
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
                    update.message.reply_text("❌ Введите целое число больше 0.")
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
                        update.message.reply_text("❌ Укажите номер колонки и условие через ';'.")
                        return None
                    col_part, filter_part = user_input_stripped.split(';', 1)
                    extra_filter_col = _parse_positive_int(col_part.strip())
                    extra_filter_value = filter_part.strip()
                    if extra_filter_col is None:
                        update.message.reply_text("❌ Номер колонки должен быть целым числом больше 0.")
                        return None
                    if not extra_filter_value:
                        update.message.reply_text("❌ Укажите условие отбора после ';'.")
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
                        update.message.reply_text("❌ Укажите regex-паттерн для изменения артикула.")
                        return None
                    variant['article_transform'] = {
                        "pattern": pattern_value,
                        "replacement": replacement_value,
                    }
            elif field == 'data_columns_count':
                columns_count = _parse_positive_int(user_input_stripped)
                if columns_count is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                _sync_variant_columns(variant, columns_count)
            elif field == 'data_column':
                col_value = _parse_positive_int(user_input_stripped)
                if col_value is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                columns = list(variant.get("data_columns", []))
                if item_index is None or item_index >= len(columns):
                    update.message.reply_text("❌ Неверный индекс колонки.")
                    return None
                columns[item_index] = col_value
                variant['data_columns'] = columns
            elif field == 'output_name':
                if not user_input_stripped:
                    update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
                    return None
                names = list(variant.get("output_names", []))
                if item_index is None or item_index >= len(names):
                    update.message.reply_text("❌ Неверный индекс файла.")
                    return None
                names[item_index] = user_input_stripped
                variant['output_names'] = names
            elif field == 'output_format':
                format_value = user_input_stripped.lower()
                if format_value not in ('xls', 'xlsx', 'csv'):
                    update.message.reply_text("❌ Допустимые форматы: xls, xlsx, csv.")
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
                    update.message.reply_text("❌ Stor не может быть пустым. Попробуйте снова:")
                    return None
                orc = variant.get("orc", {})
                orc['stor'] = user_input_stripped
                variant['orc'] = orc
            elif field == 'orc_column':
                col_value = _parse_positive_int(user_input_stripped)
                if col_value is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
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
                        update.message.reply_text("❌ Допустимые форматы: xls, xlsx, csv.")
                        return None
                    orc = variant.get("orc", {})
                    orc['output_format'] = format_value
                    variant['orc'] = orc
            rule_data['variants'][variant_index] = variant
        else:
            if field == 'name':
                if not user_input_stripped:
                    update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
                    return None
                rule_data['name'] = user_input_stripped
            elif field == 'source_file':
                if not user_input_stripped:
                    update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
                    return None
                rule_data['source_file'] = user_input_stripped
            elif field == 'data_row':
                data_row = _parse_positive_int(user_input_stripped)
                if data_row is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                rule_data['data_row'] = data_row
            elif field == 'output_name':
                if not user_input_stripped:
                    update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
                    return None
                rule_data['output_name'] = user_input_stripped
            else:
                update.message.reply_text("❌ Не удалось определить вариант настройки.")
                return None
        context.user_data['supplier_stock_processing_rule_data'] = rule_data
        context.user_data['supplier_stock_processing_rule_dirty'] = True
        _supplier_stock_close_prompt_message(context)
        if variant_index is None:
            update.message.reply_text(
                "✅ Готово.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_processing_rule|menu')]
                ])
            )
        else:
            update.message.reply_text(
                "✅ Готово.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_processing_variant|menu|{variant_index}')]
                ])
            )
        _persist_processing_rule_data(context)
        return None

    if stage == 'name':
        if not user_input_stripped:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        data['name'] = user_input_stripped
        data['id'] = _slugify_supplier_source_id(user_input_stripped)
        context.user_data['supplier_stock_processing_stage'] = 'source_file'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Введите файл источника (например: supplier_1_orig.xls):")
        return None

    if stage == 'edit_name':
        if user_input_stripped and user_input_stripped not in ('-',):
            data['name'] = user_input_stripped
        context.user_data['supplier_stock_processing_stage'] = 'edit_source_file'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text(
            f"Текущий файл источника: {data.get('source_file', '-')}\n"
            "Введите новый файл источника (или '-' чтобы оставить текущее):"
        )
        return None

    if stage == 'edit_source_file':
        if user_input_stripped and user_input_stripped not in ('-',):
            data['source_file'] = user_input_stripped
        context.user_data['supplier_stock_processing_stage'] = 'edit_reconfigure'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text(
            "Перенастроить обработку? (да/нет):"
        )
        return None

    if stage == 'edit_reconfigure':
        reconfigure = _parse_yes_no(user_input_stripped)
        if reconfigure is None:
            update.message.reply_text("❌ Ответьте 'да' или 'нет'.")
            return None
        if not reconfigure:
            _save_supplier_stock_processing_rule(context, data, edit_id=data.get("id"))
            update.message.reply_text(
                "✅ Правило обновлено.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
                ])
            )
            return None
        data.pop('variants', None)
        data.pop('variants_count', None)
        data.pop('data_row', None)
        data.pop('requires_processing', None)
        context.user_data['supplier_stock_processing_stage'] = 'needs_processing'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Требуется обработка файла? (да/нет):")
        return None

    if stage == 'source_file':
        if not user_input_stripped:
            update.message.reply_text("❌ Файл источника не может быть пустым. Попробуйте снова:")
            return None
        data['source_file'] = user_input_stripped
        context.user_data['supplier_stock_processing_stage'] = 'needs_processing'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Требуется обработка файла? (да/нет):")
        return None

    if stage == 'needs_processing':
        needs_processing = _parse_yes_no(user_input_stripped)
        if needs_processing is None:
            update.message.reply_text("❌ Ответьте 'да' или 'нет'.")
            return None
        data['requires_processing'] = needs_processing
        if not needs_processing:
            edit_id = data.get("id") if context.user_data.get('supplier_stock_processing_edit') else None
            _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
            done_text = "✅ Правило обновлено." if context.user_data.get('supplier_stock_processing_edit') else "✅ Правило добавлено."
            update.message.reply_text(
                done_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
                ])
            )
            return None
        context.user_data['supplier_stock_processing_stage'] = 'variants_count'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Сколько вариантов конечных файлов требуется? (число):")
        return None

    if stage == 'variants_count':
        variants_count = _parse_positive_int(user_input_stripped)
        if variants_count is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        data['variants_count'] = variants_count
        data['variants'] = []
        context.user_data['supplier_stock_processing_variant_index'] = 0
        context.user_data['supplier_stock_processing_stage'] = 'data_row'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Введите номер первой строки с данными (например: 2):")
        return None

    if stage == 'data_row':
        data_row = _parse_positive_int(user_input_stripped)
        if data_row is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        data['data_row'] = data_row
        context.user_data['supplier_stock_processing_stage'] = 'variant_article_col'
        context.user_data['supplier_stock_processing_data'] = data
        update.message.reply_text("Введите номер колонки с артикулом:")
        return None

    if stage == 'variant_article_col':
        article_col = _parse_positive_int(user_input_stripped)
        if article_col is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        context.user_data['supplier_stock_processing_current_variant'] = {
            "article_col": article_col,
        }
        context.user_data['supplier_stock_processing_stage'] = 'variant_article_filter'
        update.message.reply_text(
            "Введите условия отбора артикулов (regex) или '-' для всех.\n\n"
            "Примеры условий:\n"
            "• $1 ~ /^[0-9]/ && $col+0 > 0\n"
            "• $1 ~ /^[A-Z].*/ && $4 ~ /^[0-9]+$/\n"
            "• grep -E '^DKS [0-9A-Z]{6,},'\n"
            "• gsub(/^\./, \"\", art); gsub(/[A-Za-z]+$/, \"\", art);\n"
            "• ($3+0 > 0) && ($4 == \"Москва\")"
        )
        return None

    if stage == 'variant_article_filter':
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        if user_input_stripped not in ('-', ''):
            variant['article_filter'] = user_input_stripped
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'variant_prefix'
        update.message.reply_text(
            "Введите префикс артикула (или '-' если не нужен). "
            "Пробелы в конце сохраняются, либо используйте \\s."
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
            "Введите постфикс артикула (или '-' если не нужен). "
            "Пробелы в конце сохраняются."
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
        update.message.reply_text("Сколько колонок с данными нужно использовать? (число):")
        return None

    if stage == 'data_columns_count':
        columns_count = _parse_positive_int(user_input_stripped)
        if columns_count is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        context.user_data['supplier_stock_processing_data_columns_expected'] = columns_count
        context.user_data['supplier_stock_processing_data_columns'] = []
        context.user_data['supplier_stock_processing_stage'] = 'data_column'
        update.message.reply_text("Введите номер колонки с данными 1 из %d:" % columns_count)
        return None

    if stage == 'data_column':
        col_value = _parse_positive_int(user_input_stripped)
        if col_value is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        columns = context.user_data.get('supplier_stock_processing_data_columns', [])
        columns.append(col_value)
        context.user_data['supplier_stock_processing_data_columns'] = columns
        expected = context.user_data.get('supplier_stock_processing_data_columns_expected', 0)
        if len(columns) < expected:
            update.message.reply_text(
                "Введите номер колонки с данными %d из %d:" % (len(columns) + 1, expected)
            )
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['data_columns'] = columns
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_output_names_expected'] = expected
        context.user_data['supplier_stock_processing_output_names'] = []
        context.user_data['supplier_stock_processing_stage'] = 'output_name'
        update.message.reply_text(
            "Введите имя выходного файла для колонки 1 из %d "
            "(можно использовать {index}, {name}, {filename}):" % expected
        )
        return None

    if stage == 'output_name':
        if not user_input_stripped:
            update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
            return None
        names = context.user_data.get('supplier_stock_processing_output_names', [])
        names.append(user_input_stripped)
        context.user_data['supplier_stock_processing_output_names'] = names
        expected = context.user_data.get('supplier_stock_processing_output_names_expected', 0)
        if len(names) < expected:
            update.message.reply_text(
                "Введите имя выходного файла для колонки %d из %d "
                "(можно использовать {index}, {name}, {filename}):" % (len(names) + 1, expected)
            )
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['output_names'] = names
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'output_format'
        update.message.reply_text("Введите формат выходного файла (xls, xlsx, csv):")
        return None

    if stage == 'output_format':
        format_value = user_input_stripped.lower()
        if format_value not in ('xls', 'xlsx', 'csv'):
            update.message.reply_text("❌ Допустимые форматы: xls, xlsx, csv.")
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['output_format'] = format_value
        context.user_data['supplier_stock_processing_current_variant'] = variant
        context.user_data['supplier_stock_processing_stage'] = 'orc_required'
        update.message.reply_text("Нужно формировать отдельный файл для ОРК? (да/нет):")
        return None

    if stage == 'orc_required':
        orc_required = _parse_yes_no(user_input_stripped)
        if orc_required is None:
            update.message.reply_text("❌ Ответьте 'да' или 'нет'.")
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['orc'] = {"enabled": orc_required}
        context.user_data['supplier_stock_processing_current_variant'] = variant
        if not orc_required:
            return _supplier_stock_finish_variant(update, context, data)
        context.user_data['supplier_stock_processing_stage'] = 'orc_prefix'
        update.message.reply_text(
            "Введите префикс артикула для файла ОРК (или '-' если не нужен). "
            "Пробелы в конце сохраняются."
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
        update.message.reply_text("Введите параметр Stor для файла ОРК:")
        return None

    if stage == 'orc_stor':
        if not user_input_stripped:
            update.message.reply_text("❌ Stor не может быть пустым. Попробуйте снова:")
            return None
        variant = context.user_data.get('supplier_stock_processing_current_variant', {})
        variant['orc']['stor'] = user_input_stripped
        context.user_data['supplier_stock_processing_current_variant'] = variant
        return _supplier_stock_finish_variant(update, context, data)

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None

def supplier_stock_start_source_wizard(update, context):
    """Запуск мастера добавления источника остатков."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_source_stage'] = 'name'
    context.user_data['supplier_stock_source_data'] = {}
    context.user_data['supplier_stock_add_source'] = True

    query.edit_message_text(
        "➕ *Новый источник остатков*\n\nВведите название источника:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_sources')]
        ])
    )

def supplier_stock_start_edit_wizard(update, context, source_id: str):
    """Запуск мастера редактирования источника остатков."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_edit_source'] = True
    context.user_data['supplier_stock_edit_source_stage'] = 'name'
    context.user_data['supplier_stock_edit_source_id'] = source_id

    query.edit_message_text(
        f"✏️ *Редактирование источника*\n\nТекущее имя: `{_escape_pattern_text(source.get('name'))}`\n"
        "Введите новое имя (или '-' чтобы оставить текущее):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_sources')]
        ])
    )

def supplier_stock_handle_input(update, context):
    """Обработчик ввода для настроек остатков поставщиков."""
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
    """Запомнить сообщение с запросом ввода параметра."""
    if not query or not query.message:
        return
    context.user_data['supplier_stock_prompt_message_id'] = query.message.message_id
    context.user_data['supplier_stock_prompt_chat_id'] = query.message.chat_id

def _supplier_stock_close_prompt_message(context):
    """Удалить сообщение с запросом ввода параметра."""
    message_id = context.user_data.pop('supplier_stock_prompt_message_id', None)
    chat_id = context.user_data.pop('supplier_stock_prompt_chat_id', None)
    if not message_id or not chat_id:
        return
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

def supplier_stock_handle_edit_input(update, context):
    """Обработка ввода для изменения настроек остатков поставщиков."""
    field = context.user_data.get('supplier_stock_edit')
    if not field:
        return None

    message = update.message
    if not message or not message.text:
        debug_logger("⚠️ supplier_stock_handle_edit_input: получено пустое сообщение.")
        return None

    user_input = message.text.strip()
    config = get_supplier_stock_config()

    if field == 'temp_dir':
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config['download']['temp_dir'] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Временный каталог обновлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_download')]
            ])
        )
        return None

    if field == 'schedule_time':
        schedule_times = parse_supplier_stock_schedule_times(user_input)
        if not schedule_times:
            update.message.reply_text(
                "❌ Неверный формат времени. Используйте HH:MM и разделители: пробел, запятая или ;"
            )
            return None
        config['download']['schedule']['time'] = ', '.join(schedule_times)
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Время расписания обновлено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_schedule')]
            ])
        )
        return None

    if field == 'archive_cleanup_days':
        try:
            cleanup_days = int(user_input)
        except ValueError:
            update.message.reply_text("❌ Введите целое число дней (0 — отключить).")
            return None
        if cleanup_days < 0:
            update.message.reply_text("❌ Период не может быть отрицательным.")
            return None
        config["archive_cleanup_days"] = cleanup_days
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        back_callback = context.user_data.pop('supplier_stock_archive_cleanup_back', 'supplier_stock_download')
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Период очистки архива обновлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
            ])
        )
        return None

    if field == 'report_period_days':
        try:
            period_days = int(user_input)
        except ValueError:
            update.message.reply_text("❌ Введите целое число дней (минимум 1).")
            return None
        if period_days < 1:
            update.message.reply_text("❌ Период должен быть минимум 1 день.")
            return None
        config.setdefault("reporting", {})["period_days"] = period_days
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Период отчётов обновлён.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_supplier_stock')]
            ])
        )
        return None

    if field == 'archive_dir':
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config['download']['archive_dir'] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Каталог архива обновлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_download')]
            ])
        )
        return None

    return None

def supplier_stock_handle_mail_edit_input(update, context):
    """Обработка ввода для общих настроек почты остатков."""
    field = context.user_data.get('supplier_stock_mail_edit')
    if not field:
        return None

    user_input = update.message.text.strip()
    config = get_supplier_stock_config()

    if field == 'temp_dir':
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config["mail"]["temp_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_mail_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Временный каталог обновлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail')]
            ])
        )
        return None

    if field == 'archive_dir':
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config["mail"]["archive_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop('supplier_stock_mail_edit', None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Каталог архива обновлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail')]
            ])
        )
        return None

    return None

def supplier_stock_start_mail_source_wizard(update, context):
    """Запуск мастера добавления правила вложений почты."""
    query = update.callback_query
    query.answer()

    context.user_data['supplier_stock_mail_source_stage'] = 'name'
    context.user_data['supplier_stock_mail_source_data'] = {}
    context.user_data['supplier_stock_mail_add_source'] = True

    query.edit_message_text(
        "➕ *Новое правило вложений*\n\nВведите название правила:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_mail_sources')]
        ])
    )

def supplier_stock_start_mail_edit_wizard(update, context, source_id: str):
    """Запуск мастера редактирования правила вложений почты."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return

    context.user_data['supplier_stock_mail_edit_source'] = True
    context.user_data['supplier_stock_mail_edit_source_stage'] = 'name'
    context.user_data['supplier_stock_mail_edit_source_id'] = source_id

    query.edit_message_text(
        f"✏️ *Редактирование правила*\n\n"
        f"Текущее имя: `{_escape_pattern_text(source.get('name'))}`\n"
        "Введите новое имя (или '-' чтобы оставить текущее):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='supplier_stock_mail_sources')]
        ])
    )

def supplier_stock_handle_mail_source_input(update, context):
    """Обработка ввода в мастере добавления правила вложений."""
    stage = context.user_data.get('supplier_stock_mail_source_stage')
    source_data = context.user_data.get('supplier_stock_mail_source_data', {})
    user_input = update.message.text.strip()

    if stage == 'name':
        if not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        source_data['name'] = user_input
        source_data['id'] = _slugify_supplier_source_id(user_input)
        context.user_data['supplier_stock_mail_source_stage'] = 'sender'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Введите regex или адрес отправителя (например: sender@example.com) "
            "или '-' чтобы принимать любые письма:"
        )
        return None

    if stage == 'sender':
        if user_input not in ('-', ''):
            source_data['sender_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'subject'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Введите regex для темы письма или '-' чтобы принимать любую тему:"
        )
        return None

    if stage == 'subject':
        if user_input not in ('-', ''):
            source_data['subject_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'mime'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Введите MIME-фильтр (например: application/vnd.ms-excel) "
            "или '-' чтобы использовать application/.*:"
        )
        return None

    if stage == 'mime':
        if user_input not in ('-', ''):
            source_data['mime_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'filename'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Введите regex для имени вложения или '-' чтобы принимать любые файлы:"
        )
        return None

    if stage == 'filename':
        if user_input not in ('-', ''):
            source_data['filename_pattern'] = user_input
        context.user_data['supplier_stock_mail_source_stage'] = 'expected'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Введите количество ожидаемых вложений (например: 1 или 2):"
        )
        return None

    if stage == 'expected':
        expected = _parse_expected_attachments(user_input)
        if expected is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        source_data['expected_attachments'] = expected
        context.user_data['supplier_stock_mail_source_stage'] = 'output'
        context.user_data['supplier_stock_mail_source_data'] = source_data
        update.message.reply_text(
            "Введите шаблон имени выходного файла "
            "(например: supplier_{index}_orig.xls, доступны {index}, {name}):"
        )
        return None

    if stage == 'output':
        if not user_input:
            update.message.reply_text("❌ Шаблон не может быть пустым. Попробуйте снова:")
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
            "✅ Правило добавлено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None

def supplier_stock_handle_mail_source_edit_input(update, context):
    """Обработка ввода при редактировании правила вложений."""
    stage = context.user_data.get('supplier_stock_mail_edit_source_stage')
    source_id = context.user_data.get('supplier_stock_mail_edit_source_id')
    user_input = update.message.text.strip()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("❌ Правило не найдено.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
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
            "Введите regex/адрес отправителя, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_sender}"
        )
        return None

    if stage == 'sender':
        if user_input.lower() in ('none', 'нет'):
            source.pop('sender_pattern', None)
        elif user_input not in ('-',):
            source['sender_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'subject'
        current_subject = source.get("subject_pattern") or "-"
        update.message.reply_text(
            "Введите regex для темы письма, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_subject}"
        )
        return None

    if stage == 'subject':
        if user_input.lower() in ('none', 'нет'):
            source.pop('subject_pattern', None)
        elif user_input not in ('-',):
            source['subject_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'mime'
        current_mime = source.get("mime_pattern") or "-"
        update.message.reply_text(
            "Введите MIME-фильтр, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_mime}"
        )
        return None

    if stage == 'mime':
        if user_input.lower() in ('none', 'нет'):
            source.pop('mime_pattern', None)
        elif user_input not in ('-',):
            source['mime_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'filename'
        current_filename = source.get("filename_pattern") or "-"
        update.message.reply_text(
            "Введите regex для имени вложения, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_filename}"
        )
        return None

    if stage == 'filename':
        if user_input.lower() in ('none', 'нет'):
            source.pop('filename_pattern', None)
        elif user_input not in ('-',):
            source['filename_pattern'] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'expected'
        current_expected = source.get("expected_attachments", 1)
        update.message.reply_text(
            "Введите количество ожидаемых вложений, '-' чтобы оставить текущее.\n"
            f"Текущее значение: {current_expected}"
        )
        return None

    if stage == 'expected':
        if user_input not in ('-',):
            expected = _parse_expected_attachments(user_input)
            if expected is None:
                update.message.reply_text("❌ Введите целое число больше 0 или '-'.")
                return None
            source['expected_attachments'] = expected
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data['supplier_stock_mail_edit_source_stage'] = 'output'
        current_output = source.get("output_template") or "-"
        update.message.reply_text(
            "Введите шаблон имени выходного файла, '-' чтобы оставить текущее.\n"
            f"Текущее значение: {current_output}"
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
            "✅ Правило обновлено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
            ])
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг редактирования. Попробуйте снова.")
    return None

def supplier_stock_handle_source_field_input(update, context):
    """Обработка ввода при редактировании отдельного поля источника."""
    field = context.user_data.get('supplier_stock_source_field')
    source_id = context.user_data.get('supplier_stock_source_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("❌ Источник не найден.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
        ]))
        return None

    if field == 'name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        else:
            source['name'] = user_input
    elif field == 'url':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ URL не может быть пустым. Попробуйте снова:")
            return None
        else:
            source['url'] = user_input
    elif field == 'discover':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('discover', None)
        else:
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | regex | prefix, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source['discover'] = discover
    elif field == 'vars':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('vars', None)
        else:
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text("❌ Формат должен быть key=value, разделители запятая/новая строка.")
                return None
            source['vars'] = vars_map
    elif field == 'output_name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
            return None
        else:
            source['output_name'] = user_input
    elif field == 'auth':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('auth', None)
        else:
            if ':' not in user_input:
                update.message.reply_text("❌ Формат должен быть login:password или 'none'. Попробуйте снова:")
                return None
            username, password = user_input.split(':', 1)
            source['auth'] = {'username': username, 'password': password}
    elif field == 'pre_request':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('pre_request', None)
        else:
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | данные, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source['pre_request'] = pre_request
    elif field == 'options':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('include_headers', None)
            source.pop('append', None)
        else:
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "❌ Формат должен быть списком через запятую (headers, append), '-' или 'none'."
                )
                return None
            source.update(options)
    elif field == 'processing_mode':
        if user_input in ('-', ''):
            pass
        else:
            mode = _normalize_supplier_processing_mode(user_input)
            if not mode:
                update.message.reply_text("❌ Допустимые значения: table, iek_json.")
                return None
            source['processing_mode'] = mode
            if mode == "iek_json":
                source.setdefault("iek_json", {})
    elif field == 'upload_subdir':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('upload_subdir', None)
        else:
            source['upload_subdir'] = user_input
    elif field == 'individual_path':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            individual_dir.pop('unc_path', None)
        else:
            individual_dir['unc_path'] = user_input
    elif field == 'individual_login':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            individual_dir.pop('login', None)
        else:
            individual_dir['login'] = user_input
    elif field == 'individual_password':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            individual_dir.pop('password', None)
        else:
            individual_dir['password'] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["download"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_source_field', None)
    context.user_data.pop('supplier_stock_source_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_source_settings|{source_id}')]
        ])
    )
    return None

def supplier_stock_handle_source_iek_field_input(update, context):
    """Обработка ввода при редактировании параметров IEK JSON."""
    field = context.user_data.get('supplier_stock_source_iek_field')
    source_id = context.user_data.get('supplier_stock_source_iek_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("❌ Источник не найден.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
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
            "✅ Настройка обновлена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_source_iek_settings|{source_id}')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
            ])
        )
        return None
    if field == "stores":
        if user_input.lower() in ("none", "нет"):
            iek_settings["stores"] = {}
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text("❌ Формат должен быть key=uuid через запятую/новую строку.")
                return None
            iek_settings["stores"] = parsed
    elif field == "msk_stores":
        if user_input.lower() in ("none", "нет"):
            iek_settings["msk_stores"] = []
        else:
            if not user_input:
                update.message.reply_text("❌ Список не может быть пустым.")
                return None
            iek_settings["msk_stores"] = [item.strip() for item in re.split(r"[,\n]+", user_input) if item.strip()]
    elif field == "nsk_store":
        if user_input.lower() in ("none", "нет"):
            iek_settings["nsk_store"] = ""
        else:
            if not user_input:
                update.message.reply_text("❌ Значение не может быть пустым.")
                return None
            iek_settings["nsk_store"] = user_input
    elif field == "orc_stores":
        if user_input.lower() in ("none", "нет"):
            iek_settings["orc_stores"] = []
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text("❌ Формат должен быть key=stor через запятую/новую строку.")
                return None
            iek_settings["orc_stores"] = [{"key": key, "stor": value} for key, value in parsed.items()]
    elif field == "prefix":
        iek_settings["prefix"] = "" if user_input.lower() in ("none", "нет") else user_input
    elif field == "outputs":
        if user_input.lower() in ("none", "нет"):
            iek_settings["outputs"] = {}
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text("❌ Формат должен быть orig=..., msk=..., nsk=..., orc=... через запятую.")
                return None
            iek_settings["outputs"] = parsed
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    source["iek_json"] = iek_settings
    config["download"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_source_iek_field', None)
    context.user_data.pop('supplier_stock_source_iek_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_source_iek_settings|{source_id}')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
        ])
    )
    return None

def supplier_stock_handle_mail_source_field_input(update, context):
    """Обработка ввода при редактировании отдельного поля правила вложений."""
    field = context.user_data.get('supplier_stock_mail_source_field')
    source_id = context.user_data.get('supplier_stock_mail_source_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("❌ Правило не найдено.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_mail_sources')]
        ]))
        return None

    if field == 'name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        else:
            source['name'] = user_input
    elif field == 'sender':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('sender_pattern', None)
        else:
            source['sender_pattern'] = user_input
    elif field == 'subject':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('subject_pattern', None)
        else:
            source['subject_pattern'] = user_input
    elif field == 'mime':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('mime_pattern', None)
        else:
            source['mime_pattern'] = user_input
    elif field == 'filename':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('filename_pattern', None)
        else:
            source['filename_pattern'] = user_input
    elif field == 'expected':
        if user_input in ('-', ''):
            pass
        else:
            expected = _parse_expected_attachments(user_input)
            if expected is None:
                update.message.reply_text("❌ Введите целое число больше 0.")
                return None
            source['expected_attachments'] = expected
    elif field == 'output':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ Шаблон не может быть пустым. Попробуйте снова:")
            return None
        else:
            source['output_template'] = user_input
    elif field == 'upload_subdir':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            source.pop('upload_subdir', None)
        else:
            source['upload_subdir'] = user_input
    elif field == 'individual_path':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            individual_dir.pop('unc_path', None)
        else:
            individual_dir['unc_path'] = user_input
    elif field == 'individual_login':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            individual_dir.pop('login', None)
        else:
            individual_dir['login'] = user_input
    elif field == 'individual_password':
        individual_dir = source.setdefault('individual_directory', {})
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            individual_dir.pop('password', None)
        else:
            individual_dir['password'] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["mail"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_mail_source_field', None)
    context.user_data.pop('supplier_stock_mail_source_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_mail_source_settings|{source_id}')]
        ])
    )
    return None


def supplier_stock_handle_resource_input(update, context):
    """Обработка ввода в мастере добавления ресурса выгрузки."""
    stage = context.user_data.get('supplier_stock_resource_stage')
    resource_data = context.user_data.get('supplier_stock_resource_data', {})
    user_input = (update.message.text or "").strip()

    if stage == 'name':
        if not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        resource_data['name'] = user_input
        resource_data['id'] = _slugify_supplier_source_id(user_input)
        context.user_data['supplier_stock_resource_stage'] = 'unc_path'
        context.user_data['supplier_stock_resource_data'] = resource_data
        update.message.reply_text("Введите UNC путь корневого каталога:")
        return None

    if stage == 'unc_path':
        if not user_input:
            update.message.reply_text("❌ UNC путь не может быть пустым. Попробуйте снова:")
            return None
        resource_data['unc_path'] = user_input
        context.user_data['supplier_stock_resource_stage'] = 'login'
        context.user_data['supplier_stock_resource_data'] = resource_data
        update.message.reply_text("Введите логин ресурса (или '-' чтобы пропустить):")
        return None

    if stage == 'login':
        if user_input not in ('-', ''):
            resource_data['login'] = user_input
        context.user_data['supplier_stock_resource_stage'] = 'password'
        context.user_data['supplier_stock_resource_data'] = resource_data
        update.message.reply_text("Введите пароль ресурса (или '-' чтобы пропустить):")
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
            "✅ Ресурс добавлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_resources')]
            ])
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None


def supplier_stock_handle_resource_field_input(update, context):
    """Обработка ввода при редактировании ресурса выгрузки."""
    field = context.user_data.get('supplier_stock_resource_field')
    resource_id = context.user_data.get('supplier_stock_resource_field_id')
    user_input = (update.message.text or "").strip()

    if not field or not resource_id:
        return None

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        update.message.reply_text("❌ Ресурс не найден.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_resources')]
        ]))
        return None

    if field == 'name':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        else:
            resource['name'] = user_input
    elif field == 'unc_path':
        if user_input in ('-', ''):
            pass
        elif not user_input:
            update.message.reply_text("❌ UNC путь не может быть пустым. Попробуйте снова:")
            return None
        else:
            resource['unc_path'] = user_input
    elif field == 'login':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            resource.pop('login', None)
        else:
            resource['login'] = user_input
    elif field == 'password':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            resource.pop('password', None)
        else:
            resource['password'] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["resources"] = resources
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_resource_field', None)
    context.user_data.pop('supplier_stock_resource_field_id', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=f'supplier_stock_resource_settings|{resource_id}')]
        ])
    )
    return None


def supplier_stock_handle_ftp_input(update, context):
    """Обработка ввода для настроек FTP ОРК."""
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
            update.message.reply_text("❌ HOST FTP не может быть пустым. Попробуйте снова:")
            return None
        else:
            ftp_settings['host'] = user_input
    elif field == 'login':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            ftp_settings.pop('login', None)
        else:
            ftp_settings['login'] = user_input
    elif field == 'password':
        if user_input in ('-', ''):
            pass
        elif user_input.lower() in ('none', 'нет'):
            ftp_settings.pop('password', None)
        else:
            ftp_settings['password'] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["ftp_ork"] = ftp_settings
    save_supplier_stock_config(config)

    context.user_data.pop('supplier_stock_ftp_field', None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_ftp')]
        ])
    )
    return None

def supplier_stock_handle_source_input(update, context):
    """Обработка ввода в мастере добавления источника."""
    stage = context.user_data.get('supplier_stock_source_stage')
    source_data = context.user_data.get('supplier_stock_source_data', {})
    user_input = update.message.text.strip()

    if stage == 'name':
        if not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        source_data['name'] = user_input
        source_data['id'] = _slugify_supplier_source_id(user_input)
        context.user_data['supplier_stock_source_stage'] = 'url'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Введите URL для скачивания. "
            "Можно использовать переменные формата подстановки вида {abc} "
            "для дальнейшей подмены значений."
        )
        return None

    if stage == 'url':
        if not user_input:
            update.message.reply_text("❌ URL не может быть пустым. Попробуйте снова:")
            return None
        source_data['url'] = user_input
        context.user_data['supplier_stock_source_stage'] = 'discover'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Если нужно искать ссылку на странице, введите URL, regex и префикс через '|'.\n"
            "Пример: http://site/page | ostatki_msk_ot_[^\"']*\\.xls | http://site/f/\n"
            "Введите '-' если не нужно:"
        )
        return None

    if stage == 'discover':
        if user_input not in ('-', ''):
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | regex | prefix (префикс можно оставить пустым)."
                )
                return None
            source_data['discover'] = discover

        context.user_data['supplier_stock_source_stage'] = 'vars'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Введите ранее указанные переменные подстановки в формате key=value через запятую "
            "(пример: abc=DKC_Maga_Del_1200_$(date '%d.%m.%Y').zip). "
            "Введите '-' если не нужно:"
        )
        return None

    if stage == 'vars':
        if user_input not in ('-', ''):
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text("❌ Формат должен быть key=value, разделители запятая/новая строка.")
                return None
            source_data['vars'] = vars_map

        context.user_data['supplier_stock_source_stage'] = 'output_name'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Введите имя файла назначения (например: dkc_orig.zip):"
        )
        return None

    if stage == 'output_name':
        if not user_input:
            update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
            return None
        source_data['output_name'] = user_input
        context.user_data['supplier_stock_source_stage'] = 'auth'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Введите логин и пароль через двоеточие (login:password) "
            "или '-' чтобы пропустить и сохранить:"
        )
        return None

    if stage == 'auth':
        if user_input not in ('-', 'нет', 'Нет', 'none', 'None'):
            if ':' not in user_input:
                update.message.reply_text("❌ Формат должен быть login:password или '-'. Попробуйте снова:")
                return None
            username, password = user_input.split(':', 1)
            source_data['auth'] = {'username': username, 'password': password}

        context.user_data['supplier_stock_source_stage'] = 'pre_request'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Если нужен предварительный POST-запрос для авторизации, "
            "введите URL и данные через '|'.\n"
            "Пример: http://www.owen.ru/dealers | login=...&password=...&iTask=login\n"
            "Введите '-' если не нужно:"
        )
        return None

    if stage == 'pre_request':
        if user_input not in ('-', ''):
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | данные. Попробуйте снова или введите '-'."
                )
                return None
            source_data['pre_request'] = pre_request

        context.user_data['supplier_stock_source_stage'] = 'options'
        context.user_data['supplier_stock_source_data'] = source_data
        update.message.reply_text(
            "Введите дополнительные параметры сохранения: headers (с заголовками), append (дописывать).\n"
            "Пример: headers, append\n"
            "Введите '-' если не нужно:"
        )
        return None

    if stage == 'options':
        if user_input not in ('-', ''):
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "❌ Формат должен быть списком через запятую (headers, append)."
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
            "✅ Источник добавлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None

def supplier_stock_handle_source_edit_input(update, context):
    """Обработка ввода при редактировании источника остатков."""
    stage = context.user_data.get('supplier_stock_edit_source_stage')
    source_id = context.user_data.get('supplier_stock_edit_source_id')
    user_input = update.message.text.strip()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text("❌ Источник не найден.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
        ]))
        return None

    if stage == 'name':
        if user_input and user_input not in ('-',):
            source['name'] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data['supplier_stock_edit_source_stage'] = 'url'
        update.message.reply_text(
            "Введите новый URL (или '-' чтобы оставить текущее). "
            "Можно использовать переменные формата подстановки вида {abc} "
            "для дальнейшей подмены значений:\n"
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
            "Введите параметры поиска ссылки на странице в формате URL | regex | prefix, "
            "'-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            "Пример: http://site/page | ostatki_msk_ot_[^\"']*\\.xls | http://site/f/"
        )
        return None

    if stage == 'discover':
        if user_input.lower() in ('none', 'нет'):
            source.pop('discover', None)
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        elif user_input not in ('-',):
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | regex | prefix, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source['discover'] = discover
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)

        context.user_data['supplier_stock_edit_source_stage'] = 'vars'
        update.message.reply_text(
            "Введите ранее указанные переменные подстановки в формате key=value через запятую "
            "(пример: abc=DKC_Maga_Del_1200_$(date '%d.%m.%Y').zip). "
            "'-' чтобы оставить текущее или 'none' чтобы очистить:"
        )
        return None

    if stage == 'vars':
        if user_input.lower() in ('none', 'нет'):
            source.pop('vars', None)
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        elif user_input not in ('-',):
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text("❌ Формат должен быть key=value, разделители запятая/новая строка.")
                return None
            source['vars'] = vars_map
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)

        context.user_data['supplier_stock_edit_source_stage'] = 'output_name'
        update.message.reply_text(
            f"Текущий файл назначения: {source.get('output_name')}\n"
            "Введите новое имя файла назначения (или '-' чтобы оставить текущее):"
        )
        return None

    if stage == 'output_name':
        if user_input and user_input not in ('-',):
            source['output_name'] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data['supplier_stock_edit_source_stage'] = 'auth'
        update.message.reply_text(
            "Введите логин и пароль через двоеточие (login:password), "
            "'-' чтобы оставить текущее или 'none' чтобы очистить:"
        )
        return None

    if stage == 'auth':
        if user_input.lower() in ('none', 'нет'):
            source.pop('auth', None)
        elif user_input not in ('-',):
            if ':' not in user_input:
                update.message.reply_text("❌ Формат должен быть login:password, '-' или 'none'. Попробуйте снова:")
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
            "Введите предварительный POST-запрос для авторизации в формате URL | данные, "
            "'-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_pre_url} | {current_pre_data}"
        )
        return None

    if stage == 'pre_request':
        if user_input.lower() in ('none', 'нет'):
            source.pop('pre_request', None)
        elif user_input not in ('-',):
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | данные, '-' или 'none'. Попробуйте снова:"
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
            "Введите дополнительные параметры сохранения: headers (с заголовками), append (дописывать). "
            "'-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_label}"
        )
        return None

    if stage == 'options':
        if user_input.lower() in ('none', 'нет'):
            source.pop('include_headers', None)
            source.pop('append', None)
        elif user_input not in ('-',):
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "❌ Формат должен быть списком через запятую (headers, append), '-' или 'none'."
                )
                return None
            source.update(options)

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop('supplier_stock_edit_source', None)
        context.user_data.pop('supplier_stock_edit_source_stage', None)
        context.user_data.pop('supplier_stock_edit_source_id', None)

        update.message.reply_text(
            "✅ Источник обновлен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='supplier_stock_sources')]
            ])
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг редактирования. Попробуйте снова.")
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
    if lowered in ('да', 'yes', 'y', 'true', '1'):
        return True
    if lowered in ('нет', 'no', 'n', 'false', '0'):
        return False
    return None

def _normalize_supplier_processing_mode(value: str) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in ("table", "табличный", "таблица"):
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
            f"Настройка варианта {current_index + 1} из {total}.\n"
            "Введите номер колонки с артикулом:"
        )
        return None

    edit_id = data.get("id") if context.user_data.get('supplier_stock_processing_edit') else None
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
    back_callback = context.user_data.get('supplier_stock_processing_back', 'supplier_stock_processing')
    update.message.reply_text(
        "✅ Правило обработки сохранено.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]
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
        elif part in ("append", "дописать"):
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
    query.answer(f"✅ Включено {enabled} расширений")

def _disable_all_extensions_settings(query):
    disabled = 0
    for ext_id in extension_manager.get_extensions_status():
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled += 1
    query.answer(f"✅ Отключено {disabled} расширений")

def show_db_patterns_menu(update, context):
    """Показать паттерны для БД"""
    context.user_data['patterns_filter'] = 'db'
    context.user_data['patterns_back'] = 'settings_ext_backup_db'
    context.user_data['patterns_add'] = 'add_pattern'
    context.user_data['patterns_title'] = "🗃️ *Паттерны бэкапов БД*"
    view_patterns_handler(update, context)

def show_db_patterns_menu_from_backup(update, context):
    """Показать паттерны БД из меню бэкапов БД."""
    context.user_data['patterns_filter'] = 'db'
    context.user_data['patterns_back'] = 'backup_databases'
    context.user_data['patterns_add'] = 'add_pattern'
    context.user_data['patterns_title'] = "🗃️ *Паттерны бэкапов БД*"
    view_patterns_handler(update, context)

def show_proxmox_patterns_menu(update, context):
    """Показать паттерны для Proxmox"""
    context.user_data['patterns_filter'] = 'proxmox'
    context.user_data['patterns_back'] = 'settings_ext_backup_proxmox'
    context.user_data['patterns_add'] = 'add_proxmox_pattern'
    context.user_data['patterns_title'] = "🖥️ *Паттерны бэкапов Proxmox*"
    view_patterns_handler(update, context)

def show_zfs_patterns_menu(update, context):
    """Показать паттерны для ZFS"""
    context.user_data['patterns_filter'] = 'zfs'
    context.user_data['patterns_back'] = 'settings_zfs'
    context.user_data['patterns_add'] = 'add_zfs_pattern'
    context.user_data['patterns_title'] = "🧊 *Паттерны ZFS*"
    view_patterns_handler(update, context)

def show_mail_patterns_menu(update, context):
    """Показать паттерны для бэкапов почты"""
    context.user_data['patterns_filter'] = 'mail'
    context.user_data['patterns_back'] = 'settings_ext_backup_mail'
    context.user_data['patterns_add'] = 'add_mail_pattern'
    context.user_data['patterns_title'] = "📬 *Паттерны бэкапов почты*"
    view_patterns_handler(update, context)

def show_stock_load_patterns_menu(update, context):
    """Показать паттерны для загрузки остатков."""
    context.user_data['patterns_filter'] = 'stock_load'
    context.user_data['patterns_back'] = 'settings_ext_stock_load'
    context.user_data['patterns_add'] = 'add_stock_pattern'
    context.user_data['patterns_title'] = "📦 *Паттерны загрузки остатков*"
    view_patterns_handler(update, context)

def show_backup_proxmox_settings(update, context):
    """Показать настройки бэкапов Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    message = "🖥️ *Бэкапы Proxmox*\n\n"
    if not proxmox_hosts:
        message += "❌ Хосты не настроены.\n\n"
    else:
        message += f"Хостов в списке: {len(proxmox_hosts)}\n\n"

    message += "Выберите действие:"

    keyboard = [
        [InlineKeyboardButton("📋 Список хостов", callback_data='settings_proxmox_list')],
        [InlineKeyboardButton("➕ Добавить хост", callback_data='settings_proxmox_add')],
        [InlineKeyboardButton("✏️/🗑️ Редактировать и удалить паттерны", callback_data='settings_patterns_proxmox')],
        [InlineKeyboardButton("➕ Добавить паттерн", callback_data='add_proxmox_pattern')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_proxmox'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_proxmox_hosts_list(update, context):
    """Показать список хостов Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    message = "📋 *Хосты Proxmox*\n\n"
    if not proxmox_hosts:
        message += "❌ Хосты не настроены."
    else:
        for host_name in sorted(proxmox_hosts.keys()):
            host_value = proxmox_hosts.get(host_name)
            enabled = True
            if isinstance(host_value, dict):
                enabled = host_value.get('enabled', True)
            status_icon = "🟢" if enabled else "🔴"
            message += f"{status_icon} `{host_name}`\n"

    keyboard = []
    for host_name in sorted(proxmox_hosts.keys()):
        host_value = proxmox_hosts.get(host_name)
        enabled = True
        if isinstance(host_value, dict):
            enabled = host_value.get('enabled', True)
        toggle_text = "⛔️ Отключить" if enabled else "✅ Включить"
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {host_name}",
                callback_data=f"settings_proxmox_edit_{host_name}"
            ),
            InlineKeyboardButton(
                f"🗑️ {host_name}",
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
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_proxmox_host_handler(update, context):
    """Добавить хост Proxmox"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_proxmox_host'] = True

    query.edit_message_text(
        "➕ *Добавление Proxmox хоста*\n\n"
        "Введите имя хоста (как в письмах бэкапов):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def delete_proxmox_host(update, context, host_name):
    """Удалить хост Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    proxmox_hosts.pop(host_name, None)
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    query.edit_message_text(
        f"✅ Хост `{host_name}` удалён.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_proxmox_host_input(update, context):
    """Обработчик добавления хоста Proxmox"""
    if 'adding_proxmox_host' not in context.user_data:
        return

    host_name = update.message.text.strip()
    if not host_name:
        update.message.reply_text("❌ Имя хоста не может быть пустым. Попробуйте снова:")
        return

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name in proxmox_hosts:
        update.message.reply_text("❌ Такой хост уже есть. Введите другой:")
        return

    proxmox_hosts[host_name] = {'enabled': True}
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    update.message.reply_text(
        f"✅ Хост `{host_name}` добавлен.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

    context.user_data.pop('adding_proxmox_host', None)

def edit_proxmox_host_handler(update, context, host_name):
    """Начать редактирование хоста Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    context.user_data['editing_proxmox_host'] = True
    context.user_data['editing_proxmox_host_name'] = host_name

    query.edit_message_text(
        "✏️ *Редактирование хоста Proxmox*\n\n"
        f"Текущий хост: `{host_name}`\n\n"
        "Введите новое имя хоста:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_proxmox_host_edit_input(update, context):
    """Обработчик редактирования хоста Proxmox"""
    if 'editing_proxmox_host' not in context.user_data:
        return

    new_host_name = update.message.text.strip()
    if not new_host_name:
        update.message.reply_text("❌ Имя хоста не может быть пустым. Попробуйте снова:")
        return

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    old_host_name = context.user_data.get('editing_proxmox_host_name')
    if not old_host_name or old_host_name not in proxmox_hosts:
        update.message.reply_text("❌ Хост не найден.")
        context.user_data.pop('editing_proxmox_host', None)
        context.user_data.pop('editing_proxmox_host_name', None)
        return

    if new_host_name in proxmox_hosts and new_host_name != old_host_name:
        update.message.reply_text("❌ Такой хост уже есть. Введите другой:")
        return

    host_value = proxmox_hosts.pop(old_host_name, None)
    if not isinstance(host_value, dict):
        host_value = {'enabled': True}
    proxmox_hosts[new_host_name] = host_value
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    update.message.reply_text(
        f"✅ Хост обновлён: `{new_host_name}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_proxmox_host', None)
    context.user_data.pop('editing_proxmox_host_name', None)

def toggle_proxmox_host(update, context, host_name):
    """Включить/отключить мониторинг хоста Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

    status_text = "включен" if host_value['enabled'] else "отключен"
    query.edit_message_text(
        f"✅ Мониторинг хоста `{host_name}` {status_text}.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def show_zfs_settings(update, context):
    """Показать настройки ZFS"""
    query = update.callback_query
    query.answer()

    show_zfs_main_menu(update, context)

def show_zfs_main_menu(update, context):
    """Показать меню ZFS из главного меню"""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("📋 Хосты", callback_data='settings_zfs_list')],
        [InlineKeyboardButton("🔍 Паттерны", callback_data='settings_patterns_zfs')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        "🧊 *Мониторинг ZFS*\n\nВыберите раздел:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_zfs_status_summary(update, context):
    """Показать последние статусы ZFS массивов"""
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
            "🧊 *ZFS статусы*\n\n❌ База бэкапов не настроена.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                "🧊 *ZFS статусы*\n\n❌ Таблица ZFS ещё не создана.\n"
                "Дождитесь первого письма или перезапустите мониторинг.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
        message = "📊 *ZFS статусы*\n\n❌ Данных нет."
    else:
        def _md(value: object) -> str:
            return escape_markdown(str(value or ""), version=1)

        message = "📊 *ZFS статусы (последние)*\n\n"
        current_server = None
        for server_name, pool_name, pool_state, received_at in rows:
            if server_name != current_server:
                if current_server is not None:
                    message += "\n"
                message += f"*{_md(server_name)}*\n"
                current_server = server_name
            message += (
                f"• {_md(pool_name)}: `{_md(pool_state)}` ({_md(received_at)})\n"
            )

    keyboard = [
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_zfs_servers_list(update, context):
    """Показать список ZFS серверов"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    message = "📋 *ZFS серверы*\n\n"
    if not zfs_servers:
        message += "❌ Серверы не настроены."
    else:
        for server_name in sorted(zfs_servers.keys()):
            server_value = zfs_servers.get(server_name, {})
            enabled = True
            if isinstance(server_value, dict):
                enabled = server_value.get('enabled', True)
            status_icon = "🟢" if enabled else "🔴"
            message += f"{status_icon} `{server_name}`\n"

    keyboard = []
    for server_name in sorted(zfs_servers.keys()):
        server_value = zfs_servers.get(server_name, {})
        enabled = True
        if isinstance(server_value, dict):
            enabled = server_value.get('enabled', True)
        toggle_text = "⛔️ Отключить" if enabled else "✅ Включить"
        keyboard.append([
            InlineKeyboardButton(
                f"✏️ {server_name}",
                callback_data=f"settings_zfs_edit_name_{server_name}"
            ),
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {server_name}",
                callback_data=f"settings_zfs_delete_{server_name}"
            ),
            InlineKeyboardButton(
                f"{toggle_text} {server_name}",
                callback_data=f"settings_zfs_toggle_{server_name}"
            ),
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Добавить сервер", callback_data='settings_zfs_add')
    ])

    keyboard.append([
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_zfs_server_handler(update, context):
    """Добавить ZFS сервер"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_zfs_server'] = True
    context.user_data['zfs_server_stage'] = 'name'

    query.edit_message_text(
        "➕ *Добавление ZFS сервера*\n\n"
        "Введите имя сервера (как приходит в теме письма):",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_zfs'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def delete_zfs_server(update, context, server_name):
    """Удалить ZFS сервер"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    if server_name not in zfs_servers:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    zfs_servers.pop(server_name, None)
    settings_manager.set_setting('ZFS_SERVERS', zfs_servers)
    _delete_zfs_server_statuses(server_name)

    query.edit_message_text(
        f"✅ Сервер `{server_name}` удалён.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_zfs_server_input(update, context):
    """Обработчик добавления ZFS сервера"""
    if 'adding_zfs_server' not in context.user_data:
        return

    user_input = update.message.text.strip()
    stage = context.user_data.get('zfs_server_stage', 'name')

    if stage == 'name':
        if not user_input:
            update.message.reply_text("❌ Имя сервера не может быть пустым. Попробуйте снова:")
            return

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        if user_input in zfs_servers:
            update.message.reply_text("❌ Такой сервер уже есть. Введите другой:")
            return

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        zfs_servers[user_input] = {
            'enabled': True,
        }
        settings_manager.set_setting('ZFS_SERVERS', zfs_servers)

        update.message.reply_text(
            "✅ Сервер добавлен.\n"
            f"Имя: `{user_input}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

        context.user_data.pop('adding_zfs_server', None)
        context.user_data.pop('zfs_server_stage', None)

def edit_zfs_server_name_handler(update, context, server_name):
    """Начать редактирование имени ZFS сервера"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    if server_name not in zfs_servers:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    context.user_data['editing_zfs_server_name'] = True
    context.user_data['editing_zfs_server_old_name'] = server_name

    query.edit_message_text(
        "✏️ *Редактирование ZFS сервера*\n\n"
        f"Текущее имя: `{server_name}`\n\n"
        "Введите новое имя сервера:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_zfs'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_zfs_server_name_edit_input(update, context):
    """Обработчик редактирования имени ZFS сервера"""
    if 'editing_zfs_server_name' not in context.user_data:
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("❌ Имя сервера не может быть пустым. Попробуйте снова:")
        return

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    old_name = context.user_data.get('editing_zfs_server_old_name')
    if not old_name or old_name not in zfs_servers:
        update.message.reply_text("❌ Сервер не найден.")
        context.user_data.pop('editing_zfs_server_name', None)
        context.user_data.pop('editing_zfs_server_old_name', None)
        return

    if new_name in zfs_servers and new_name != old_name:
        update.message.reply_text("❌ Такой сервер уже есть. Введите другой:")
        return

    server_value = zfs_servers.pop(old_name, None)
    if not isinstance(server_value, dict):
        server_value = {'enabled': True}
    zfs_servers[new_name] = server_value
    settings_manager.set_setting('ZFS_SERVERS', zfs_servers)
    _rename_zfs_server_statuses(old_name, new_name)

    update.message.reply_text(
        f"✅ Сервер обновлён: `{new_name}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_zfs_server_name', None)
    context.user_data.pop('editing_zfs_server_old_name', None)

def toggle_zfs_server(update, context, server_name):
    """Включить/отключить мониторинг ZFS сервера"""
    query = update.callback_query
    query.answer()

    zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
    if not isinstance(zfs_servers, dict):
        zfs_servers = {}

    if server_name not in zfs_servers:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

    status_text = "включен" if server_value['enabled'] else "отключен"
    query.edit_message_text(
        f"✅ Мониторинг сервера `{server_name}` {status_text}.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_zfs'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def _delete_zfs_server_statuses(server_name: str) -> None:
    """Удалить статусы ZFS сервера из БД бэкапов."""
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
            debug_logger(f"⚠️ Не удалось удалить статусы ZFS сервера: {exc}")
    finally:
        conn.close()

def _rename_zfs_server_statuses(old_name: str, new_name: str) -> None:
    """Переименовать статусы ZFS сервера в БД бэкапов."""
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
            debug_logger(f"⚠️ Не удалось переименовать статусы ZFS сервера: {exc}")
    finally:
        conn.close()

def handle_setting_input(update, context, setting_key):
    """Обработчик ввода значений настроек"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем какое настройку меняем
    context.user_data['editing_setting'] = setting_key
    context.user_data['editing_setting_message_id'] = query.message.message_id
    context.user_data['editing_setting_chat_id'] = query.message.chat_id
    
    setting_descriptions = {
        'telegram_token': 'Введите новый токен Telegram бота:',
        'check_interval': 'Введите новый интервал проверки (в секундах):',
        'max_fail_time': 'Введите максимальное время простоя (в секундах):',
        'silent_start': 'Введите час начала тихого режима (0-23):',
        'silent_end': 'Введите час окончания тихого режима (0-23):',
        'data_collection': 'Введите время сбора данных (формат HH:MM):',
        'cpu_warning': 'Введите порог предупреждения для CPU (%):',
        'cpu_critical': 'Введите критический порог для CPU (%):',
        'ram_warning': 'Введите порог предупреждения для RAM (%):',
        'ram_critical': 'Введите критический порог для RAM (%):',
        'disk_warning': 'Введите порог предупреждения для Disk (%):',
        'disk_critical': 'Введите критический порог для Disk (%):',
        'ssh_username': 'Введите имя пользователя SSH:',
        'ssh_key_path': 'Введите путь к SSH ключу:',
        'web_port': 'Введите порт веб-интерфейса:',
        'web_host': 'Введите хост веб-интерфейса:',
        'backup_alert_hours': 'Введите количество часов для алертов о бэкапах:',
        'backup_stale_hours': 'Введите количество часов для устаревших бэкапов:',
    }
    
    message = setting_descriptions.get(setting_key, f'Введите новое значение для {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_main')]
        ])
    )

def add_database_category_handler(update, context):
    """Обработчик добавления категории БД"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "➕ *Добавление категории баз данных*\n\n"
        "Эта функция находится в разработке.\n"
        "Скоро здесь можно будет добавлять новые категории БД для мониторинга.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
                InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
                InlineKeyboardButton("✖️ Закрыть", callback_data='close'),
            ]
        ])
    )

def edit_database_category_handler(update, context):
    """Обработчик редактирования категории БД"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='backup_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"✏️ {category}", callback_data=f'edit_category_{category}')])
    
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close'),
    ])
    
    query.edit_message_text(
        "✏️ *Редактирование категорий баз данных*\n\n"
        "Выберите категорию для редактирования:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_database_category_handler(update, context):
    """Обработчик удаления категории БД"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='backup_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"🗑️ {category}", callback_data=f'delete_category_{category}')])
    
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close'),
    ])
    
    query.edit_message_text(
        "🗑️ *Удаление категории баз данных*\n\n"
        "Выберите категорию для удаления:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def view_all_databases_handler(update, context):
    """Обработчик просмотра всех БД"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "📋 *Все базы данных для мониторинга*\n\n"
    
    if not db_config:
        message += "❌ *Нет настроенных баз данных*\n\n"
        message += "Добавьте категории и базы данных в настройках."
    else:
        total_dbs = 0
        for category, databases in db_config.items():
            message += f"📁 *{category.upper()}* ({len(databases)} БД):\n"
            for db_key, db_name in databases.items():
                message += f"   • {db_name}\n"
                total_dbs += 1
            message += "\n"
        
        message += f"*Итого:* {total_dbs} баз данных в {len(db_config)} категориях"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
                InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
                InlineKeyboardButton("✖️ Закрыть", callback_data='close'),
            ]
        ])
    )

def manage_chats_handler(update, context):
    """Управление чатами - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ КНОПКИ СПИСКА ВСЕХ ЧАТОВ"""
    query = update.callback_query
    query.answer()
    
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    message = "💬 *Управление чатами*\n\n"
    message += f"Текущее количество чатов: {len(chat_ids)}\n\n"
    
    if chat_ids:
        message += "*Текущие чаты:*\n"
        for i, chat_id in enumerate(chat_ids[:5], 1):
            message += f"{i}. `{chat_id}`\n"
        if len(chat_ids) > 5:
            message += f"... и еще {len(chat_ids) - 5} чатов\n"
    else:
        message += "❌ *Чаты не настроены*\n"
    
    message += "\nВыберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data='add_chat')],
        [InlineKeyboardButton("🗑️ Удалить чат", callback_data='remove_chat')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_telegram'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_server_timeouts(update, context):
    """Таймауты серверов - УПРОЩЕННАЯ БЕЗ MARKDOWN ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    timeouts = settings_manager.get_setting('SERVER_TIMEOUTS', {})
    
    # Простой текст без Markdown
    message = "⏰ Таймауты серверов\n\n"
    
    if timeouts:
        for server_type, timeout in timeouts.items():
            message += f"• {server_type}: {timeout} сек\n"
    else:
        message += "❌ Таймауты не настроены\n"
        message += "Используются значения по умолчанию.\n\n"
        message += "Таймауты по умолчанию:\n"
        message += "• Windows 2025: 35 сек\n"
        message += "• Доменные серверы: 20 сек\n"
        message += "• Admin серверы: 25 сек\n"
        message += "• Стандартные Windows: 30 сек\n"
        message += "• Linux серверы: 15 сек\n"
        message += "• Ping серверы: 10 сек\n"
    
    message += "\nВыберите параметр для изменения:"
    
    keyboard = [
        [InlineKeyboardButton("🖥️ Windows 2025", callback_data='set_windows_2025_timeout')],
        [InlineKeyboardButton("🌐 Доменные серверы", callback_data='set_domain_servers_timeout')],
        [InlineKeyboardButton("🔧 Admin серверы", callback_data='set_admin_servers_timeout')],
        [InlineKeyboardButton("💻 Стандартные Windows", callback_data='set_standard_windows_timeout')],
        [InlineKeyboardButton("🐧 Linux серверы", callback_data='set_linux_timeout')],
        [InlineKeyboardButton("📡 Ping серверы", callback_data='set_ping_timeout')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_monitoring'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,  # Без parse_mode
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_server_handler(update, context):
    """Добавить сервер - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем состояние добавления сервера
    context.user_data['adding_server'] = True
    context.user_data['server_stage'] = 'ip'
    
    message = (
        "➕ *Добавление сервера*\n\n"
        "Введите IP-адрес сервера:\n\n"
        "_Пример: 192.168.9.000_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_servers')]
        ])
    )

def handle_server_input(update, context):
    """Обработчик ввода данных сервера"""
    if 'adding_server' not in context.user_data or not context.user_data['adding_server']:
        return
    
    user_input = update.message.text
    stage = context.user_data.get('server_stage', 'ip')
    
    try:
        if stage == 'ip':
            # Проверка IP-адреса
            import re
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            if not re.match(ip_pattern, user_input):
                update.message.reply_text("❌ Неверный формат IP-адреса. Попробуйте снова:")
                return
            
            context.user_data['server_ip'] = user_input
            context.user_data['server_stage'] = 'name'
            
            update.message.reply_text(
                "📝 Введите имя сервера:\n\n"
                "_Пример: web-server-01_",
                parse_mode='Markdown'
            )
            
        elif stage == 'name':
            context.user_data['server_name'] = user_input
            context.user_data['server_stage'] = 'type'
            
            keyboard = [
                [InlineKeyboardButton("🖥️ Windows (RDP)", callback_data='server_type_rdp')],
                [InlineKeyboardButton("🐧 Linux (SSH)", callback_data='server_type_ssh')],
                [InlineKeyboardButton("📡 Ping Only", callback_data='server_type_ping')],
                [InlineKeyboardButton("❌ Отмена", callback_data='settings_servers')]
            ]
            
            update.message.reply_text(
                "🔧 Выберите тип сервера:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
        # Сбрасываем состояние при ошибке
        context.user_data['adding_server'] = False

def handle_server_type(update, context):
    """Обработчик выбора типа сервера"""
    query = update.callback_query
    query.answer()
    
    if 'adding_server' not in context.user_data:
        return
    
    server_type = query.data.replace('server_type_', '')
    server_ip = context.user_data.get('server_ip')
    server_name = context.user_data.get('server_name')
    
    try:
        # Добавляем сервер в базу
        success = settings_manager.add_server(server_ip, server_name, server_type)
        
        if success:
            message = f"✅ *Сервер добавлен!*\n\n• IP: `{server_ip}`\n• Имя: `{server_name}`\n• Тип: `{server_type}`"
            
            # Очищаем состояние
            context.user_data['adding_server'] = False
            context.user_data.pop('server_ip', None)
            context.user_data.pop('server_name', None)
            context.user_data.pop('server_stage', None)
        else:
            message = "❌ Ошибка при добавлении сервера"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад к серверам", callback_data='settings_servers'),
                 InlineKeyboardButton("➕ Добавить еще", callback_data='settings_add_server')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка: {e}")

def view_all_databases_handler(update, context):
    """Просмотр всех БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    disabled_pairs = _get_disabled_db_monitors_settings()
    context.user_data['settings_db_toggle_map'] = {}

    if not db_config:
        message = "📋 *Все базы данных*\n\n❌ *Нет настроенных баз данных*"
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию БД", callback_data='settings_db_add_category')]]
    else:
        message = "📋 *Все базы данных*\n\n"
        total_dbs = 0
        keyboard = []

        for category, databases in db_config.items():
            if not isinstance(databases, dict):
                databases = {}
            message += f"📁 *{category.upper()}* ({len(databases)} БД):\n"
            for db_key, db_name in databases.items():
                message += f"   • {db_name}\n"
                total_dbs += 1
                is_disabled = (category, db_key) in disabled_pairs
                monitor_text = "⚪ Мониторинг выкл" if is_disabled else "🟢 Мониторинг вкл"
                encoded_category = quote(category, safe='')
                encoded_db_key = quote(db_key, safe='')
                keyboard.append([
                    InlineKeyboardButton(
                        f"{monitor_text}: {db_name}",
                        callback_data=_build_db_monitor_toggle_callback(
                            context,
                            encoded_category,
                            encoded_db_key,
                        )
                    )
                ])
            message += "\n"

        message += f"*Итого:* {total_dbs} баз данных в {len(db_config)} категориях"

    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_database_category_handler(update, context):
    """Добавить категорию БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    context.user_data['adding_db_category'] = True
    
    message = (
        "➕ *Добавление категории БД*\n\n"
        "Введите название новой категории:\n\n"
        "_Пример: company, client, backup_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_db_main')]
        ])
    )

def edit_databases_handler(update, context):
    """Редактировать БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='settings_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"✏️ {category}", callback_data=f'settings_db_edit_{category}')])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')])
    
    query.edit_message_text(
        "✏️ *Редактирование баз данных*\n\n"
        "Выберите категорию для редактирования:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_database_category_handler(update, context):
    """Удалить категорию БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='settings_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"🗑️ {category}", callback_data=f'settings_db_delete_{category}')])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')])
    
    query.edit_message_text(
        "🗑️ *Удаление категории БД*\n\n"
        "Выберите категорию для удаления:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def edit_database_category_details(update, context, category):
    """Показать детали категории БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category)
    if databases is not None and not isinstance(databases, dict):
        databases = {}

    if databases is None:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    message = f"✏️ *Категория {category}*\n\n"
    if not databases:
        message += "❌ В этой категории нет баз данных.\n"
    else:
        message += "Список баз данных:\n"
        for db_key, db_name in databases.items():
            message += f"• {db_name} (`{db_key}`)\n"

    message += "\nВыберите действие:"

    disabled_pairs = _get_disabled_db_monitors_settings()
    keyboard = [[InlineKeyboardButton("➕ Добавить БД", callback_data=f"settings_db_add_db_{category}")]]
    for db_key, db_name in databases.items():
        button_text = f"✏️ {db_name}"
        is_disabled = (category, db_key) in disabled_pairs
        toggle_text = "✅ Включить мониторинг" if is_disabled else "⛔ Отключить мониторинг"
        encoded_category = quote(category, safe='')
        encoded_db_key = quote(db_key, safe='')
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"settings_db_edit_db_{category}__{db_key}"),
            InlineKeyboardButton(f"🗑️ {db_name}", callback_data=f"settings_db_delete_db_{category}__{db_key}")
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text}: {db_name}",
                callback_data=f"settings_db_toggle_monitor_{encoded_category}__{encoded_db_key}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_database_entry_handler(update, context, category):
    """Запуск добавления базы данных в категорию"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    # Инициализируем состояние добавления БД
    context.user_data['adding_db_entry'] = True
    context.user_data['db_entry_category'] = category
    context.user_data.pop('db_entry_key', None)

    query.edit_message_text(
        "➕ *Добавление базы данных*\n\n"
        f"Категория: *{category}*\n\n"
        "Введите ключ базы данных (латиница/цифры/символы `_`, `-`, `.`):\n\n"
        "_Пример: trade, client_db_01_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_db_main')]
        ])
    )

def edit_database_entry_handler(update, context, category, db_key):
    """Запуск редактирования базы данных"""
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
            "❌ База данных не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    context.user_data['editing_db_entry'] = True
    context.user_data['db_entry_category'] = category
    context.user_data['db_entry_key'] = db_key

    query.edit_message_text(
        "✏️ *Редактирование базы данных*\n\n"
        f"Категория: *{category}*\n"
        f"Ключ: `{db_key}`\n"
        "Введите новый ключ:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_db_main')]
        ])
    )

def delete_database_entry_confirmation(update, context, category, db_key):
    """Подтверждение удаления базы данных"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    db_name = databases.get(db_key)

    if db_name is None:
        query.edit_message_text(
            "❌ База данных не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    query.edit_message_text(
        "🗑️ *Удаление базы данных*\n\n"
        f"Категория: *{category}*\n"
        f"База: `{db_name}`\n\n"
        "Удалить?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Удалить", callback_data=f"settings_db_delete_db_confirm_{category}__{db_key}")],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def delete_database_entry_execute(update, context, category, db_key):
    """Удаление базы данных"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    db_name = databases.pop(db_key, None)

    if db_name is None:
        query.edit_message_text(
            "❌ База данных не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    db_config[category] = databases
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    query.edit_message_text(
        "✅ *База данных удалена!*\n\n"
        f"Категория: *{category}*\n"
        f"База: `{db_name}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )


def settings_toggle_database_monitoring(update, context, encoded_backup_type, encoded_db_name):
    """Переключение мониторинга конкретной БД из настроек."""
    query = update.callback_query
    query.answer()

    backup_type = unquote(str(encoded_backup_type or '')).strip()
    db_name = unquote(str(encoded_db_name or '')).strip()
    if not backup_type or not db_name:
        query.edit_message_text(
            "❌ Не удалось переключить мониторинг: пустой тип или имя БД.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(backup_type, {})
    if not isinstance(databases, dict):
        databases = {}
    if db_name not in databases:
        query.edit_message_text(
            "❌ База данных не найдена в настройках.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    now_enabled = _toggle_database_monitoring_settings(backup_type, db_name)
    status_text = "🟢 включён" if now_enabled else "⚪ отключён"
    query.edit_message_text(
        (
            "🗃️ *Мониторинг базы обновлён*\n\n"
            f"• Категория: `{backup_type}`\n"
            f"• База: `{db_name}`\n"
            f"• Статус: {status_text}"
        ),
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 К списку баз", callback_data='settings_db_main')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def delete_database_category_confirmation(update, context, category):
    """Подтверждение удаления категории БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    message = (
        "🗑️ *Удаление категории БД*\n\n"
        f"Категория: *{category}*\n"
        "Подтвердите удаление:"
    )

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Удалить", callback_data=f"settings_db_delete_confirm_{category}")],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
        ])
    )

def delete_database_category_execute(update, context, category):
    """Удалить категорию БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
            ])
        )
        return

    db_config.pop(category, None)
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    query.edit_message_text(
        f"✅ Категория *{category}* удалена.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )
    
def not_implemented_handler(update, context, feature_name=""):
    """Обработчик для функций в разработке"""
    query = update.callback_query
    query.answer()
    
    message = f"🛠️ *Функция в разработке*\n\n"
    if feature_name:
        message += f"Функция '{feature_name}' находится в разработке.\n"
    message += "Скоро здесь будет доступна новая функциональность."
    
    # Определяем откуда пришел запрос для кнопки "Назад"
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
            [InlineKeyboardButton("↩️ Назад", callback_data=back_button),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_db_category_input(update, context):
    """Обработчик ввода категории БД"""
    if 'adding_db_category' not in context.user_data:
        return
    
    category_name = update.message.text.strip()
    
    try:
        # Получаем текущую конфигурацию БД
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        
        # Добавляем новую категорию
        if category_name not in db_config:
            db_config[category_name] = {}
            settings_manager.set_setting('DATABASE_CONFIG', db_config)
            
            update.message.reply_text(
                f"✅ *Категория '{category_name}' добавлена!*\n\n"
                "Теперь вы можете добавить базы данных в эту категорию.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Добавить БД", callback_data=f'settings_db_edit_{category_name}'),
                     InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
                ])
            )
        else:
            update.message.reply_text(
                f"❌ Категория '{category_name}' уже существует!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
                ])
            )
    
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    
    # Очищаем состояние
    context.user_data['adding_db_category'] = False

def handle_db_entry_input(update, context):
    """Обработчик добавления базы данных"""
    if 'adding_db_entry' not in context.user_data:
        return

    user_input = update.message.text.strip()
    category = context.user_data.get('db_entry_category')

    if not category:
        update.message.reply_text("❌ Категория не найдена. Попробуйте снова.")
        context.user_data['adding_db_entry'] = False
        return

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    if not isinstance(databases, dict):
        databases = {}

    if not user_input:
        update.message.reply_text("❌ Ключ не может быть пустым. Попробуйте снова:")
        return

    if ' ' in user_input:
        update.message.reply_text("❌ Ключ не должен содержать пробелы. Попробуйте снова:")
        return

    if user_input in databases:
        update.message.reply_text("❌ Такой ключ уже существует. Введите другой:")
        return

    databases[user_input] = user_input
    db_config[category] = databases
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    update.message.reply_text(
        "✅ *База данных добавлена!*\n\n"
        f"Категория: *{category}*\n"
        f"Ключ: `{user_input}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✏️ Добавить еще", callback_data=f'settings_db_add_db_{category}')]
        ])
    )

    context.user_data.pop('adding_db_entry', None)
    context.user_data.pop('db_entry_category', None)
    context.user_data.pop('db_entry_key', None)

def handle_db_entry_edit_input(update, context):
    """Обработчик редактирования базы данных"""
    if 'editing_db_entry' not in context.user_data:
        return

    user_input = update.message.text.strip()
    category = context.user_data.get('db_entry_category')
    db_key = context.user_data.get('db_entry_key')

    if not category or not db_key:
        update.message.reply_text("❌ Не удалось определить базу данных. Попробуйте снова.")
        context.user_data['editing_db_entry'] = False
        return

    if not user_input:
        update.message.reply_text("❌ Ключ не может быть пустым. Попробуйте снова:")
        return

    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    databases = db_config.get(category, {})

    if db_key not in databases:
        update.message.reply_text("❌ База данных не найдена.")
        context.user_data['editing_db_entry'] = False
        return

    if user_input in databases and user_input != db_key:
        update.message.reply_text("❌ Такой ключ уже существует. Введите другой:")
        return

    databases.pop(db_key, None)
    databases[user_input] = user_input
    db_config[category] = databases
    settings_manager.set_setting('DATABASE_CONFIG', db_config)

    update.message.reply_text(
        "✅ *База данных обновлена!*\n\n"
        f"Категория: *{category}*\n"
        f"Новый ключ: `{user_input}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✏️ Редактировать еще", callback_data=f'settings_db_edit_{category}')]
        ])
    )

    context.user_data.pop('editing_db_entry', None)
    context.user_data.pop('db_entry_category', None)
    context.user_data.pop('db_entry_key', None)
    
def show_windows_auth_settings(update, context):
    """Показать настройки аутентификации Windows - ОСНОВНОЕ МЕНЮ"""
    query = update.callback_query
    query.answer()
    
    # Получаем статистику по учетным данным
    credentials = settings_manager.get_windows_credentials()
    server_types = settings_manager.get_windows_server_types()
    
    # Группируем по типам серверов
    stats = {}
    for cred in credentials:
        server_type = cred['server_type']
        if server_type not in stats:
            stats[server_type] = 0
        stats[server_type] += 1
    
    message = "🖥️ *Управление аутентификацией Windows*\n\n"
    message += f"• Всего учетных записей: {len(credentials)}\n"
    message += f"• Типов серверов: {len(server_types)}\n\n"
    
    if stats:
        message += "*Учетные данные по типам:*\n"
        for server_type, count in stats.items():
            message += f"• {server_type}: {count} учетных записей\n"
    else:
        message += "❌ *Учетные данные не настроены*\n"
    
    message += "\nВыберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("👥 Просмотр всех учетных записей", callback_data='windows_auth_list')],
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add')],
        [InlineKeyboardButton("📊 Учетные данные по типам", callback_data='windows_auth_by_type')],
        [InlineKeyboardButton("⚙️ Управление типами серверов", callback_data='windows_auth_manage_types')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_auth'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_windows_auth_list(update, context):
    """Показать список всех учетных записей Windows"""
    query = update.callback_query
    query.answer()
    
    credentials = settings_manager.get_windows_credentials()
    
    message = "👥 *Все учетные записи Windows*\n\n"
    
    if not credentials:
        message += "❌ *Учетные записи не найдены*\n"
    else:
        for i, cred in enumerate(credentials, 1):
            status = "🟢" if cred['enabled'] else "🔴"
            message += f"{status} *{cred['server_type']}* (приоритет: {cred['priority']})\n"
            message += f"   Пользователь: `{cred['username']}`\n"
            message += f"   Пароль: `{'*' * 8}`\n"
            message += f"   ID: {cred['id']}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add')],
        [InlineKeyboardButton("✏️ Редактировать", callback_data='windows_auth_edit')],
        [InlineKeyboardButton("🗑️ Удалить", callback_data='windows_auth_delete')],
        [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_windows_auth_add(update, context):
    """Показать форму добавления учетной записи Windows"""
    query = update.callback_query
    query.answer()
    
    # Начинаем процесс добавления
    context.user_data['adding_windows_cred'] = True
    context.user_data['cred_stage'] = 'username'
    
    message = (
        "➕ *Добавление учетной записи Windows*\n\n"
        "Введите имя пользователя:\n\n"
        "_Пример: Administrator_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
        ])
    )

def show_windows_auth_by_type(update, context):
    """Показать учетные данные по типам серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "📊 *Учетные данные по типам серверов*\n\n"
    
    if not server_types:
        message += "❌ *Типы серверов не настроены*\n"
    else:
        for server_type in server_types:
            credentials = settings_manager.get_windows_credentials(server_type)
            message += f"*{server_type}* ({len(credentials)} учетных записей):\n"
            
            for cred in credentials[:3]:  # Показываем первые 3
                status = "🟢" if cred['enabled'] else "🔴"
                message += f"  {status} {cred['username']} (приоритет: {cred['priority']})\n"
            
            if len(credentials) > 3:
                message += f"  ... и еще {len(credentials) - 3} учетных записей\n"
            message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("👥 Просмотр всех", callback_data='windows_auth_list')],
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add')],
        [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_windows_credential_input(update, context):
    """Обработчик ввода данных учетной записи Windows"""
    if 'adding_windows_cred' not in context.user_data:
        return
    
    user_input = update.message.text
    stage = context.user_data.get('cred_stage')
    
    try:
        if stage == 'username':
            context.user_data['cred_username'] = user_input
            context.user_data['cred_stage'] = 'password'
            
            update.message.reply_text(
                "🔒 Введите пароль:\n\n"
                "_Пароль будет сохранен в зашифрованном виде_",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
                ])
            )
            
        elif stage == 'password':
            context.user_data['cred_password'] = user_input
            context.user_data['cred_stage'] = 'server_type'
            
            # Предлагаем стандартные типы серверов
            keyboard = [
                [InlineKeyboardButton("🖥️ Windows 2025", callback_data='cred_type_windows_2025')],
                [InlineKeyboardButton("🌐 Доменные серверы", callback_data='cred_type_domain_servers')],
                [InlineKeyboardButton("🔧 Admin серверы", callback_data='cred_type_admin_servers')],
                [InlineKeyboardButton("💻 Стандартные Windows", callback_data='cred_type_standard_windows')],
                [InlineKeyboardButton("⚙️ Другой тип", callback_data='cred_type_custom')],
                [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
            ]
            
            update.message.reply_text(
                "🖥️ Выберите тип серверов для этих учетных данных:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif stage == 'server_type_custom':
            context.user_data['cred_server_type'] = user_input
            context.user_data['cred_stage'] = 'priority'
            
            update.message.reply_text(
                "📊 Введите приоритет (число):\n\n"
                "_Учетные данные с более высоким приоритетом будут использоваться первыми_",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
                ])
            )
            
        elif stage == 'priority':
            try:
                priority = int(user_input)
                context.user_data['cred_priority'] = priority
                
                # Сохраняем учетные данные
                username = context.user_data['cred_username']
                password = context.user_data['cred_password']
                server_type = context.user_data['cred_server_type']
                
                success = settings_manager.add_windows_credential(
                    username, password, server_type, priority
                )
                
                if success:
                    # Очищаем контекст
                    for key in ['adding_windows_cred', 'cred_stage', 'cred_username', 
                               'cred_password', 'cred_server_type', 'cred_priority']:
                        context.user_data.pop(key, None)
                    
                    update.message.reply_text(
                        f"✅ *Учетная запись добавлена!*\n\n"
                        f"• Пользователь: `{username}`\n"
                        f"• Тип серверов: `{server_type}`\n"
                        f"• Приоритет: `{priority}`",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("➕ Добавить еще", callback_data='windows_auth_add'),
                             InlineKeyboardButton("👥 Просмотр всех", callback_data='windows_auth_list')],
                            [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main')]
                        ])
                    )
                else:
                    update.message.reply_text("❌ Ошибка при сохранении учетных данных")
                    
            except ValueError:
                update.message.reply_text("❌ Приоритет должен быть числом. Попробуйте снова:")
                
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
        # Сбрасываем состояние при ошибке
        context.user_data['adding_windows_cred'] = False

def handle_credential_type_selection(update, context):
    """Обработчик выбора типа сервера для учетных данных"""
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
            "✏️ Введите название типа серверов:\n\n"
            "_Пример: backup_servers, web_servers_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
            ])
        )
    else:
        context.user_data['cred_server_type'] = type_mapping.get(cred_type, cred_type)
        context.user_data['cred_stage'] = 'priority'
        
        query.edit_message_text(
            "📊 Введите приоритет (число):\n\n"
            "_Учетные данные с более высоким приоритетом будут использоваться первыми_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
            ])
        )

def show_windows_auth_manage_types(update, context):
    """Управление типами серверов - ОБНОВЛЕННАЯ ВЕРСИЯ С НАСТРОЙКАМИ"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "⚙️ *Управление типами серверов*\n\n"
    
    if not server_types:
        message += "❌ *Типы серверов не настроены*\n"
    else:
        message += "*Существующие типы:*\n"
        for server_type in server_types:
            credentials = settings_manager.get_windows_credentials(server_type)
            enabled_count = sum(1 for cred in credentials if cred['enabled'])
            message += f"• *{server_type}*: {enabled_count}/{len(credentials)} активных учетных записей\n"
    
    message += "\n*Доступные действия:*\n"
    message += "• *Переименовать тип* - изменить название типа серверов\n"
    message += "• *Объединить типы* - объединить два типа в один\n"
    message += "• *Удалить тип* - удалить тип (учетные записи сохранятся)\n"
    
    keyboard = []
    
    # Кнопки для каждого типа серверов
    for server_type in server_types:
        keyboard.append([
            InlineKeyboardButton(f"✏️ {server_type}", callback_data=f'manage_type_edit_{server_type}'),
            InlineKeyboardButton(f"🔄 {server_type}", callback_data=f'manage_type_merge_{server_type}')
        ])
    
    # Общие действия
    keyboard.extend([
        [InlineKeyboardButton("➕ Создать новый тип", callback_data='manage_type_create')],
        [InlineKeyboardButton("🗑️ Удалить тип", callback_data='manage_type_delete')],
        [InlineKeyboardButton("📊 Статистика по типам", callback_data='manage_type_stats')],
        [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_server_type_management(update, context):
    """Обработчик управления типами серверов"""
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
    """Создание нового типа серверов"""
    query = update.callback_query
    query.answer()
    
    context.user_data['creating_server_type'] = True
    
    query.edit_message_text(
        "➕ *Создание нового типа серверов*\n\n"
        "Введите название для нового типа:\n\n"
        "_Пример: web_servers, database_servers, backup_servers_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')]
        ])
    )

def edit_server_type_handler(update, context, old_type):
    """Редактирование типа серверов"""
    query = update.callback_query
    query.answer()
    
    context.user_data['editing_server_type'] = True
    context.user_data['old_server_type'] = old_type
    
    credentials = settings_manager.get_windows_credentials(old_type)
    
    query.edit_message_text(
        f"✏️ *Редактирование типа серверов*\n\n"
        f"Текущее название: *{old_type}*\n"
        f"Количество учетных записей: {len(credentials)}\n\n"
        "Введите новое название для этого типа:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')]
        ])
    )

def merge_server_type_handler(update, context, source_type):
    """Объединение типов серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    # Исключаем текущий тип из списка для объединения
    target_types = [t for t in server_types if t != source_type]
    
    if not target_types:
        query.answer("❌ Нет других типов для объединения")
        return
    
    message = f"🔄 *Объединение типов серверов*\n\n"
    message += f"Источник: *{source_type}*\n"
    message += f"Учетных записей: {len(settings_manager.get_windows_credentials(source_type))}\n\n"
    message += "Выберите целевой тип для объединения:"
    
    keyboard = []
    for target_type in target_types:
        cred_count = len(settings_manager.get_windows_credentials(target_type))
        keyboard.append([
            InlineKeyboardButton(
                f"🔄 {target_type} ({cred_count})", 
                callback_data=f'merge_confirm_{source_type}_{target_type}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_type_handler(update, context):
    """Удаление типа серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "🗑️ *Удаление типа серверов*\n\n"
    message += "Выберите тип для удаления:\n\n"
    message += "*Внимание:* При удалении типа все учетные записи этого типа будут перемещены в тип 'default'"
    
    keyboard = []
    for server_type in server_types:
        if server_type != 'default':  # Не позволяем удалить тип 'default'
            cred_count = len(settings_manager.get_windows_credentials(server_type))
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {server_type} ({cred_count})", 
                    callback_data=f'delete_type_confirm_{server_type}'
                )
            ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_server_type_stats(update, context):
    """Показать статистику по типам серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "📊 *Статистика по типам серверов*\n\n"
    
    total_credentials = 0
    for server_type in server_types:
        credentials = settings_manager.get_windows_credentials(server_type)
        enabled_count = sum(1 for cred in credentials if cred['enabled'])
        total_credentials += len(credentials)
        
        message += f"*{server_type}*\n"
        message += f"• Всего учетных записей: {len(credentials)}\n"
        message += f"• Активных: {enabled_count}\n"
        message += f"• Неактивных: {len(credentials) - enabled_count}\n\n"
    
    message += f"*Общая статистика:*\n"
    message += f"• Типов серверов: {len(server_types)}\n"
    message += f"• Всего учетных записей: {total_credentials}\n"
    message += f"• Среднее на тип: {total_credentials / len(server_types):.1f} учетных записей"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Обновить", callback_data='manage_type_stats')],
            [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_manage_types'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def merge_server_types_confirmation(update, context, source_type, target_type):
    """Подтверждение объединения типов серверов"""
    query = update.callback_query
    query.answer()
    
    source_creds = settings_manager.get_windows_credentials(source_type)
    target_creds = settings_manager.get_windows_credentials(target_type)
    
    message = f"🔄 *Подтверждение объединения*\n\n"
    message += f"*Источник:* {source_type}\n"
    message += f"• Учетных записей: {len(source_creds)}\n\n"
    message += f"*Цель:* {target_type}\n"
    message += f"• Учетных записей: {len(target_creds)}\n\n"
    message += f"*После объединения:*\n"
    message += f"• Тип {source_type} будет удален\n"
    message += f"• Все учетные записи будут перемещены в {target_type}\n"
    message += f"• Итоговое количество: {len(source_creds) + len(target_creds)} учетных записей\n\n"
    message += "Вы уверены, что хотите выполнить объединение?"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, объединить", callback_data=f'merge_execute_{source_type}_{target_type}'),
                InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')
            ]
        ])
    )

def delete_server_type_confirmation(update, context, server_type):
    """Подтверждение удаления типа серверов"""
    query = update.callback_query
    query.answer()
    
    credentials = settings_manager.get_windows_credentials(server_type)
    
    message = f"🗑️ *Подтверждение удаления*\n\n"
    message += f"Тип: *{server_type}*\n"
    message += f"Учетных записей: {len(credentials)}\n\n"
    message += "*Внимание:* Все учетные записи этого типа будут перемещены в тип 'default'\n\n"
    message += "Вы уверены, что хотите удалить этот тип?"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f'delete_type_execute_{server_type}'),
                InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')
            ]
        ])
    )

def execute_server_type_merge(update, context, source_type, target_type):
    """Выполнение объединения типов серверов"""
    query = update.callback_query
    query.answer()
    
    try:
        # Получаем учетные данные исходного типа
        source_credentials = settings_manager.get_windows_credentials(source_type)
        
        # Обновляем тип для каждой учетной записи
        for cred in source_credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type=target_type
            )
        
        message = f"✅ *Типы серверов объединены!*\n\n"
        message += f"• Тип *{source_type}* удален\n"
        message += f"• Все учетные записи перемещены в *{target_type}*\n"
        message += f"• Перемещено учетных записей: {len(source_credentials)}"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка при объединении типов: {str(e)}")

def execute_server_type_delete(update, context, server_type):
    """Выполнение удаления типа серверов"""
    query = update.callback_query
    query.answer()
    
    try:
        # Получаем учетные данные удаляемого типа
        credentials = settings_manager.get_windows_credentials(server_type)
        
        # Перемещаем все учетные записи в тип 'default'
        for cred in credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type='default'
            )
        
        message = f"✅ *Тип серверов удален!*\n\n"
        message += f"• Тип *{server_type}* удален\n"
        message += f"• Все учетные записи перемещены в тип 'default'\n"
        message += f"• Перемещено учетных записей: {len(credentials)}"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка при удалении типа: {str(e)}")

def handle_server_type_creation(update, context):
    """Обработчик создания нового типа серверов"""
    new_type = update.message.text.strip()
    
    try:
        # Проверяем, не существует ли уже такой тип
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types:
            update.message.reply_text(
                f"❌ Тип '{new_type}' уже существует!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_manage_types')]
                ])
            )
            return
        
        # Создаем новую учетную запись с этим типом (можно пустую)
        success = settings_manager.add_windows_credential(
            username=f"user_{new_type}",
            password="temp_password",
            server_type=new_type,
            priority=0
        )
        
        if success:
            # Сразу удаляем временную учетную запись, если нужно
            # или оставляем как шаблон
            
            update.message.reply_text(
                f"✅ *Тип серверов '{new_type}' создан!*\n\n"
                "Теперь вы можете добавить учетные записи для этого типа.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add'),
                     InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
                ])
            )
        else:
            update.message.reply_text("❌ Ошибка при создании типа")
    
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    
    # Очищаем контекст
    context.user_data['creating_server_type'] = False

def handle_server_type_editing(update, context):
    """Обработчик редактирования типа серверов"""
    new_type = update.message.text.strip()
    old_type = context.user_data.get('old_server_type')
    
    try:
        # Проверяем, не существует ли уже такой тип
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types and new_type != old_type:
            update.message.reply_text(
                f"❌ Тип '{new_type}' уже существует!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_manage_types')]
                ])
            )
            return
        
        # Получаем все учетные записи старого типа
        credentials = settings_manager.get_windows_credentials(old_type)
        
        # Обновляем тип для каждой учетной записи
        for cred in credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type=new_type
            )
        
        update.message.reply_text(
            f"✅ *Тип серверов переименован!*\n\n"
            f"• Старое название: {old_type}\n"
            f"• Новое название: {new_type}\n"
            f"• Обновлено учетных записей: {len(credentials)}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
            ])
        )
    
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    
    # Очищаем контекст
    context.user_data['editing_server_type'] = False
    context.user_data.pop('old_server_type', None)

# Обработчики для неработающих кнопок
def add_chat_handler(update, context):
    """Добавить чат - заглушка"""
    not_implemented_handler(update, context, "Добавление чата")

def remove_chat_handler(update, context):
    """Удалить чат - заглушка"""
    not_implemented_handler(update, context, "Удаление чата")

def view_all_settings_handler(update, context):
    """Просмотр всех настроек - заглушка"""
    not_implemented_handler(update, context, "Просмотр всех настроек")

def add_pattern_handler(update, context):
    """Добавить паттерн - заглушка"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'db_input'
    context.user_data['backup_pattern_mode'] = 'db_wizard'

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна БД*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя БД из настроек.\n\n"
        "Пример темы:\n"
        "`Backup db company_main completed`\n\n"
        "Пример фрагментов:\n"
        "`Backup db; company_main; completed`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def add_zfs_pattern_handler(update, context):
    """Добавить паттерн для ZFS"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'zfs_input'
    context.user_data['backup_pattern_mode'] = 'zfs_wizard'

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна ZFS*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя ZFS сервера из настроек.\n\n"
        "Пример темы:\n"
        "`ZFS alert zfs01: state: ONLINE, state: ONLINE`\n\n"
        "Пример фрагментов:\n"
        "`ZFS alert; zfs01; state:`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def add_proxmox_pattern_handler(update, context):
    """Добавить паттерн для Proxmox"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'proxmox_input'
    context.user_data['backup_pattern_mode'] = 'proxmox_wizard'

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна Proxmox*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.\n\n"
        "Пример темы:\n"
        "`vzdump backup status`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def add_mail_pattern_handler(update, context):
    """Добавить паттерн для бэкапов почты"""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'mail_input'
    context.user_data['backup_pattern_mode'] = 'mail_wizard'

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна почты*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.\n\n"
        "Пример темы:\n"
        "`Бэкап Zimbra - 52G /backups/zimbra/2025-03-01`\n\n"
        "Пример фрагментов:\n"
        "`Бэкап Zimbra; /backups/zimbra`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def show_stock_pattern_type_menu(update, context):
    """Показать выбор типа паттерна для остатков."""
    query = update.callback_query
    query.answer()

    message = (
        "📦 *Добавление паттерна для загрузки остатков*\n\n"
        "Выберите, что нужно настроить:"
    )

    keyboard = [
        [InlineKeyboardButton("🧾 Тема письма", callback_data='stock_pattern_select_subject')],
        [InlineKeyboardButton("🗂️ Источник отчета", callback_data='stock_pattern_select_source')],
        [InlineKeyboardButton("📎 Имя вложения", callback_data='stock_pattern_select_attachment')],
        [InlineKeyboardButton("📄 Строка файла", callback_data='stock_pattern_select_file_entry')],
        [InlineKeyboardButton("✅ Успешная загрузка", callback_data='stock_pattern_select_success')],
        [InlineKeyboardButton("🙈 Игнорировать строки", callback_data='stock_pattern_select_ignore')],
        [InlineKeyboardButton("❌ Ошибка загрузки", callback_data='stock_pattern_select_failure')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_patterns_stock'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def stock_pattern_select_handler(update, context, pattern_type: str):
    """Запустить мастер для выбранного типа паттерна остатков."""
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
            "🧙 *Мастер добавления темы*\n\n"
            "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
            "Фрагменты учитываются в указанном порядке.\n\n"
            "Пример:\n"
            "`Логи загрузки файлов в рабочую базу 07:38:14`"
        )
    elif pattern_type == 'source':
        prompt = (
            "🧙 *Мастер добавления источника отчета*\n\n"
            "Введите название источника и тему письма через `|`.\n"
            "В теме можно использовать фрагменты через `;`/`,`.\n\n"
            "Пример:\n"
            "`Филиал Москва | Логи загрузки файлов в рабочую базу 07:38:14`"
        )
    elif pattern_type == 'attachment':
        prompt = (
            "🧙 *Мастер добавления имени вложения*\n\n"
            "Введите имя файла или фрагменты через `;`/`,`.\n\n"
            "Пример:\n"
            "`LogiLogistam.txt`"
        )
    elif pattern_type == 'file_entry':
        prompt = (
            "🧙 *Мастер добавления строки файла*\n\n"
            "Введите строку с названием поставщика и путем к файлу.\n\n"
            "Пример:\n"
            "`19.01.26 07:35:36: ЗЭТА  НСК  D:\\Obmen\\OCTATKu\\ЗЭТА\\Остатки ЗЭТА НСК.csv`"
        )
    elif pattern_type == 'success':
        prompt = (
            "🧙 *Мастер добавления строки успеха*\n\n"
            "Введите строку с результатом успешной загрузки.\n\n"
            "Пример:\n"
            "`19.01.26 07:35:39: ***Остатки загружены!***   строк 348   07:35:39`"
        )
    elif pattern_type == 'ignore':
        prompt = (
            "🧙 *Мастер добавления игнорируемой строки*\n\n"
            "Введите строку или обязательные фрагменты через `;`/`,`.\n"
            "Эти строки будут пропускаться при разборе.\n\n"
            "Пример:\n"
            "`Внимание! Ошибка в номенклатуре Артикул=`"
        )
    else:
        prompt = (
            "🧙 *Мастер добавления строки ошибки*\n\n"
            "Введите строку с ошибкой или обязательные фрагменты через `;`/`,`.\n\n"
            "Пример:\n"
            "`--- неудача!!! пустая загрузка`"
        )

    query.edit_message_text(
        prompt,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def stock_pattern_retry_handler(update, context):
    """Повторить ввод для паттернов остатков."""
    query = update.callback_query
    query.answer()

    pattern_type = context.user_data.get('backup_pattern_stock_type', 'subject')
    stock_pattern_select_handler(update, context, pattern_type)

def stock_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна остатков."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    pattern_type = context.user_data.get('backup_pattern_stock_type')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    label = context.user_data.get('backup_pattern_stock_label')

    if not pattern or not pattern_type:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

        source_label = context.user_data.get('backup_pattern_source', 'мастер')
        label_text = f"Метка: *{label}*\n" if label else ""
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *stock_load*\n"
            f"Тип: *{pattern_type}*\n"
            f"{label_text}"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
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
    """Изменить дефолтный паттерн для бэкапов почты"""
    query = update.callback_query
    query.answer()

    fallback_patterns = _get_mail_fallback_patterns()
    current_pattern = fallback_patterns[0] if fallback_patterns else ""

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'pattern_only'
    context.user_data['backup_pattern_mode'] = 'mail'

    query.edit_message_text(
        "✏️ *Изменение паттерна почты*\n\n"
        f"Текущий паттерн:\n`{current_pattern}`\n\n"
        "Введите новый regex паттерн темы письма:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def mail_pattern_retry_handler(update, context):
    """Повторить ввод темы/фрагментов для паттерна почты."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'mail_input'
    context.user_data['backup_pattern_mode'] = 'mail_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна почты*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def mail_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна почты."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

        source_label = context.user_data.get('backup_pattern_source', 'мастер')
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *mail*\n"
            "Тип: *subject*\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
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
    """Повторить ввод темы/фрагментов для паттерна БД."""
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
        "🧙 *Мастер добавления паттерна БД*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя БД из настроек.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def _get_database_categories() -> list[str]:
    """Получить список категорий БД из настроек."""
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if not isinstance(db_config, dict):
        return []
    return sorted([key for key in db_config.keys() if isinstance(key, str)])

def _show_db_pattern_confirm(update, context):
    """Показать экран подтверждения паттерна БД с выбором категории."""
    pattern = context.user_data.get('backup_pattern_generated')
    db_name = context.user_data.get('backup_pattern_db_name', '')
    category = context.user_data.get('backup_pattern_category', '')
    source_label = context.user_data.get('backup_pattern_source', 'мастер')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        return

    categories = _get_database_categories()
    keyboard: list[list[InlineKeyboardButton]] = []
    if categories:
        row: list[InlineKeyboardButton] = []
        for category_name in categories:
            label = f"✅ {category_name}" if category_name == category else category_name
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
        [InlineKeyboardButton("✅ Сохранить", callback_data='db_pattern_confirm')],
        [InlineKeyboardButton("✏️ Ввести заново", callback_data='db_pattern_retry')],
        [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])

    message = (
        "✅ *Черновик паттерна готов!*\n\n"
        f"БД: *{db_name}*\n"
        f"Категория: *{category}*\n"
        f"Источник: *{source_label}*\n"
        f"Паттерн: `{pattern}`\n"
    )
    if categories:
        message += "\nВыберите категорию перед сохранением:"
    else:
        message += "\n⚠️ Нет доступных категорий БД."

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
    """Выбрать категорию для паттерна БД."""
    context.user_data['backup_pattern_category'] = category
    _show_db_pattern_confirm(update, context)

def db_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна БД."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    category = context.user_data.get('backup_pattern_category')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern or not category:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

        source_label = context.user_data.get('backup_pattern_source', 'мастер')
        db_name = context.user_data.get('backup_pattern_db_name', '')
        db_info = f"БД: *{db_name}*\n" if db_name else ""
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            f"{db_info}"
            f"Категория: *{category}*\n"
            "Тип: *subject*\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
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
    """Редактировать дефолтный паттерн БД."""
    query = update.callback_query
    query.answer()

    try:
        index = int(index_value)
    except ValueError:
        query.edit_message_text("❌ Некорректный индекс паттерна.")
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        query.edit_message_text("❌ Паттерн не найден.")
        return

    current_pattern = patterns[index - 1]
    context.user_data['editing_default_db_pattern'] = True
    context.user_data['editing_default_db_category'] = category
    context.user_data['editing_default_db_index'] = index

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    query.edit_message_text(
        "✏️ *Редактирование дефолтного паттерна БД*\n\n"
        f"Категория: *{category}*\n"
        f"Текущий паттерн: `{current_pattern}`\n\n"
        "Введите новый regex паттерн темы письма:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=back_callback),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def delete_default_db_pattern_handler(update, context, category: str, index_value: str):
    """Удалить дефолтный паттерн БД."""
    query = update.callback_query
    query.answer()

    try:
        index = int(index_value)
    except ValueError:
        query.edit_message_text("❌ Некорректный индекс паттерна.")
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        query.edit_message_text("❌ Паттерн не найден.")
        return

    patterns.pop(index - 1)
    if patterns:
        db_patterns[category] = patterns
    else:
        db_patterns.pop(category, None)

    _save_database_patterns_setting(db_patterns)

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    query.edit_message_text(
        "✅ Дефолтный паттерн удалён.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def zfs_pattern_retry_handler(update, context):
    """Повторить ввод темы/фрагментов для паттерна ZFS."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'zfs_input'
    context.user_data['backup_pattern_mode'] = 'zfs_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна ZFS*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя ZFS сервера из настроек.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def zfs_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна ZFS."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

        source_label = context.user_data.get('backup_pattern_source', 'мастер')
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *zfs*\n"
            "Тип: *subject*\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
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
    """Повторить ввод темы/фрагментов для паттерна Proxmox."""
    query = update.callback_query
    query.answer()

    context.user_data['adding_backup_pattern'] = True
    context.user_data['backup_pattern_stage'] = 'proxmox_input'
    context.user_data['backup_pattern_mode'] = 'proxmox_wizard'
    context.user_data.pop('backup_pattern_generated', None)
    context.user_data.pop('backup_pattern_source', None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна Proxmox*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=context.user_data.get('patterns_back', 'settings_backup')),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def proxmox_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна Proxmox."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get('backup_pattern_generated')
    back_callback = context.user_data.get('patterns_back', 'settings_backup')

    if not pattern:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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

        source_label = context.user_data.get('backup_pattern_source', 'мастер')
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *proxmox*\n"
            "Тип: *subject*\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
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
    """Просмотр паттернов"""
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

    title = context.user_data.get('patterns_title', "📋 *Паттерны*")
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
        message = f"{title}\n\n❌ Паттерны не настроены."
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
            message += "*mail (по умолчанию)*\n"
            for index, pattern in enumerate(fallback_patterns, start=1):
                message += f"{index}. subject: `{_escape_pattern_text(pattern)}`\n"
        if fallback_db_patterns:
            if rows or fallback_patterns:
                message += "\n"
            message += "*database (по умолчанию)*\n"
            for category, patterns in fallback_db_patterns.items():
                message += f"*{_escape_pattern_text(category)}*\n"
                for index, pattern in enumerate(patterns, start=1):
                    message += f"{index}. subject: `{_escape_pattern_text(pattern)}`\n"
        if fallback_stock_patterns:
            if rows or fallback_patterns or fallback_db_patterns:
                message += "\n"
            message += "*stock_load (по умолчанию)*\n"
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
                f"✏️ {index}. {category}:{pattern_type}",
                callback_data=f"edit_pattern_{pattern_id}"
            ),
            InlineKeyboardButton(
                f"🗑️ {index}. {category}:{pattern_type}",
                callback_data=f"delete_pattern_{pattern_id}"
            )
        ])

    if fallback_patterns and filter_mode == 'mail':
        keyboard.append([
            InlineKeyboardButton("✏️ Изменить дефолтный паттерн", callback_data='edit_mail_default_pattern')
        ])
    if fallback_db_patterns and filter_mode == 'db':
        for category, patterns in fallback_db_patterns.items():
            for index, _ in enumerate(patterns, start=1):
                keyboard.append([
                    InlineKeyboardButton(
                        f"✏️ {category} #{index}",
                        callback_data=f"db_default_edit_{category}__{index}"
                    ),
                    InlineKeyboardButton(
                        f"🗑️ {category} #{index}",
                        callback_data=f"db_default_delete_{category}__{index}"
                    )
                ])

    add_callback = context.user_data.get('patterns_add')
    if add_callback:
        keyboard.append([InlineKeyboardButton("➕ Добавить паттерн", callback_data=add_callback)])

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    keyboard.append([
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def _get_database_category(db_name):
    """Получить категорию базы данных по ключу"""
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    if not isinstance(db_config, dict):
        return "unknown"
    for category, databases in db_config.items():
        if isinstance(databases, dict) and db_name in databases:
            return category
    return "unknown"

def delete_pattern_handler(update, context, pattern_id):
    """Удалить паттерн"""
    query = update.callback_query
    query.answer()

    try:
        pattern_id_int = int(pattern_id)
    except ValueError:
        query.edit_message_text("❌ Некорректный идентификатор паттерна.")
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
        "✅ Паттерн удалён.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def edit_pattern_handler(update, context, pattern_id):
    """Редактировать паттерн"""
    query = update.callback_query
    query.answer()

    try:
        pattern_id_int = int(pattern_id)
    except ValueError:
        query.edit_message_text("❌ Некорректный идентификатор паттерна.")
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
            "❌ Паттерн не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
        prompt = "Введите паттерн темы письма:"
    elif category == 'stock_load':
        prompt = "Введите regex паттерн для выбранного типа:"
    else:
        prompt = "Введите тему письма (как приходит в почте):"

    query.edit_message_text(
        "✏️ *Редактирование паттерна*\n\n"
        f"Категория: *{category}*\n"
        f"Тип: *{pattern_type}*\n"
        f"Текущий паттерн: `{pattern}`\n\n"
        f"{prompt}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data=back_callback),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_backup_pattern_input(update, context):
    """Обработчик добавления паттерна"""
    if 'adding_backup_pattern' not in context.user_data:
        return

    user_input = update.message.text.strip()
    stage = context.user_data.get('backup_pattern_stage', 'category')
    mode = context.user_data.get('backup_pattern_mode', 'db')

    if mode == 'db_wizard':
        if stage != 'db_input':
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        db_names = _get_database_names()
        if not db_names:
            update.message.reply_text(
                "❌ Базы данных не настроены. Сначала добавьте БД в настройках."
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
            source_label = "фрагменты"
        else:
            pattern, db_name = _build_db_pattern_from_subject(
                user_input,
                db_names,
            )
            source_label = "тема письма"

        if not pattern or not db_name:
            update.message.reply_text(
                "❌ Не найдено имя БД из настроек.\n"
                "Добавьте в тему или фрагменты имя БД и попробуйте снова:"
            )
            return

        category = _get_database_category(db_name)
        if category == "unknown":
            update.message.reply_text(
                "❌ Не удалось определить категорию БД.\n"
                "Проверьте, что БД есть в настройках."
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
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        server_names = _get_zfs_server_names()
        if not server_names:
            update.message.reply_text(
                "❌ ZFS серверы не настроены. Сначала добавьте серверы в настройках ZFS."
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
            source_label = "фрагменты"
        else:
            pattern, has_server = _build_zfs_pattern_from_subject(
                user_input,
                server_names,
            )
            source_label = "тема письма"

        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return

        if not has_server:
            update.message.reply_text(
                "❌ Не найдено имя ZFS сервера из настроек.\n"
                "Добавьте в тему или фрагменты имя сервера и попробуйте снова:"
            )
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'zfs_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Сохранить", callback_data='zfs_pattern_confirm')],
                [InlineKeyboardButton("✏️ Ввести заново", callback_data='zfs_pattern_retry')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    if mode == 'mail_wizard':
        if stage != 'mail_input':
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_mail_pattern_from_fragments(fragments)
            source_label = "фрагменты"
        else:
            pattern = _build_mail_pattern_from_subject(user_input)
            source_label = "тема письма"

        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'mail_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Сохранить", callback_data='mail_pattern_confirm')],
                [InlineKeyboardButton("✏️ Ввести заново", callback_data='mail_pattern_retry')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    if mode == 'stock_subject_wizard':
        if stage != 'stock_input':
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "фрагменты"
        else:
            pattern = _build_stock_subject_pattern(user_input)
            source_label = "тема письма"

        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'stock_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Сохранить", callback_data='stock_pattern_confirm')],
                [InlineKeyboardButton("✏️ Ввести заново", callback_data='stock_pattern_retry')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    if mode == 'stock_source_wizard':
        if stage != 'stock_input':
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        if "|" not in user_input:
            update.message.reply_text(
                "❌ Нужен формат `Название | Тема письма`. Попробуйте снова:"
            )
            return

        label_raw, subject_raw = [part.strip() for part in user_input.split("|", 1)]
        if not label_raw or not subject_raw:
            update.message.reply_text(
                "❌ Название и тема не могут быть пустыми. Попробуйте снова:"
            )
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", subject_raw)]
        fragments = [fragment for fragment in fragments if fragment]
        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "фрагменты"
        else:
            pattern = _build_stock_subject_pattern(subject_raw)
            source_label = "тема письма"

        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'stock_confirm'
        context.user_data['backup_pattern_stock_type'] = f"source:{label_raw}"
        context.user_data['backup_pattern_stock_label'] = label_raw

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Метка: *{label_raw}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Сохранить", callback_data='stock_pattern_confirm')],
                [InlineKeyboardButton("✏️ Ввести заново", callback_data='stock_pattern_retry')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    if mode == 'stock_log_wizard':
        if stage != 'stock_input':
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        pattern_type = context.user_data.get('backup_pattern_stock_type', 'file_entry')
        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "фрагменты"
        else:
            if pattern_type == 'success':
                pattern = _build_stock_success_pattern(user_input)
                source_label = "строка лога"
            elif pattern_type == 'attachment':
                pattern = re.escape(user_input.strip()) + r"$"
                source_label = "имя файла"
            elif pattern_type == 'ignore':
                pattern = _build_stock_pattern_from_fragments([user_input])
                source_label = "строка лога"
            elif pattern_type == 'failure':
                pattern = _build_stock_pattern_from_fragments([user_input])
                source_label = "строка лога"
            else:
                pattern = (
                    r"^\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}:\s+"
                    r"(?P<supplier>.+?)\s{2,}(?P<path>[A-Za-z]:\\.+)$"
                )
                source_label = "строка лога"

        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'stock_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Сохранить", callback_data='stock_pattern_confirm')],
                [InlineKeyboardButton("✏️ Ввести заново", callback_data='stock_pattern_retry')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    if mode == 'proxmox_wizard':
        if stage != 'proxmox_input':
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_mail_pattern_from_fragments(fragments)
            source_label = "фрагменты"
        else:
            pattern = _build_mail_pattern_from_subject(user_input)
            source_label = "тема письма"

        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return

        context.user_data['backup_pattern_generated'] = pattern
        context.user_data['backup_pattern_source'] = source_label
        context.user_data['backup_pattern_stage'] = 'proxmox_confirm'

        back_callback = context.user_data.get('patterns_back', 'settings_backup')
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Сохранить", callback_data='proxmox_pattern_confirm')],
                [InlineKeyboardButton("✏️ Ввести заново", callback_data='proxmox_pattern_retry')],
                [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        return

    if mode in ('zfs', 'proxmox', 'mail'):
        if not user_input:
            update.message.reply_text("❌ Паттерн не может быть пустым. Попробуйте снова:")
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
                "✅ *Паттерн добавлен!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
                f"Паттерн: `{pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                     InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
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
            update.message.reply_text("❌ Тема не может быть пустой. Попробуйте снова:")
            return
        context.user_data['backup_pattern_subject'] = user_input
        context.user_data['backup_pattern_stage'] = 'db_name'
        update.message.reply_text("Введите имя базы данных из темы письма:")
        return

    if stage == 'db_name':
        if not user_input:
            update.message.reply_text("❌ Имя базы не может быть пустым. Попробуйте снова:")
            return

        subject = context.user_data.get('backup_pattern_subject')
        db_name = user_input
        escaped_subject = re.escape(subject)
        escaped_db_name = re.escape(db_name)
        if escaped_db_name not in escaped_subject:
            update.message.reply_text(
                "❌ Имя базы не найдено в теме письма. Проверьте ввод и попробуйте снова:"
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
                "✅ *Паттерн добавлен!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
                f"Паттерн: `{pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                     InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        finally:
            context.user_data.pop('adding_backup_pattern', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_category', None)
            context.user_data.pop('backup_pattern_type', None)
            context.user_data.pop('backup_pattern_subject', None)
            context.user_data.pop('backup_pattern_mode', None)

def handle_backup_pattern_edit_input(update, context):
    """Обработчик редактирования паттерна"""
    if 'editing_backup_pattern' not in context.user_data:
        return

    new_pattern = update.message.text.strip()
    stage = context.user_data.get('backup_pattern_stage', 'subject')
    mode = context.user_data.get('backup_pattern_mode', 'db')

    if mode in ('zfs', 'proxmox', 'mail', 'stock'):
        if not new_pattern:
            update.message.reply_text("❌ Паттерн не может быть пустым. Попробуйте снова:")
            return

        pattern_id = context.user_data.get('editing_backup_pattern_id')
        if not pattern_id:
            update.message.reply_text("❌ Не найден паттерн для редактирования.")
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
                "✅ *Паттерн обновлён!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
                f"Паттерн: `{new_pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                     InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
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
            update.message.reply_text("❌ Тема не может быть пустой. Попробуйте снова:")
            return
        context.user_data['backup_pattern_subject'] = new_pattern
        context.user_data['backup_pattern_stage'] = 'db_name'
        update.message.reply_text("Введите имя базы данных из темы письма:")
        return

    if stage == 'db_name':
        if not new_pattern:
            update.message.reply_text("❌ Имя базы не может быть пустым. Попробуйте снова:")
            return

        subject = context.user_data.get('backup_pattern_subject')
        db_name = new_pattern
        escaped_subject = re.escape(subject)
        escaped_db_name = re.escape(db_name)
        if escaped_db_name not in escaped_subject:
            update.message.reply_text(
                "❌ Имя базы не найдено в теме письма. Проверьте ввод и попробуйте снова:"
            )
            return

        pattern_id = context.user_data.get('editing_backup_pattern_id')
        if not pattern_id:
            update.message.reply_text("❌ Не найден паттерн для редактирования.")
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
                "✅ *Паттерн обновлён!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
                f"Паттерн: `{new_pattern}`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                     InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
        except Exception as e:
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        finally:
            context.user_data.pop('editing_backup_pattern', None)
            context.user_data.pop('editing_backup_pattern_id', None)
            context.user_data.pop('backup_pattern_category', None)
            context.user_data.pop('backup_pattern_type', None)
            context.user_data.pop('backup_pattern_subject', None)
            context.user_data.pop('backup_pattern_stage', None)
            context.user_data.pop('backup_pattern_mode', None)
    
def handle_default_db_pattern_edit_input(update, context):
    """Обработчик редактирования дефолтного паттерна БД."""
    new_pattern = update.message.text.strip()
    if not new_pattern:
        update.message.reply_text("❌ Паттерн не может быть пустым. Попробуйте снова:")
        return

    category = context.user_data.get('editing_default_db_category')
    index = context.user_data.get('editing_default_db_index')
    if not category or not index:
        update.message.reply_text("❌ Не найден паттерн для редактирования.")
        context.user_data.pop('editing_default_db_pattern', None)
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        update.message.reply_text("❌ Паттерн не найден.")
        context.user_data.pop('editing_default_db_pattern', None)
        return

    patterns[index - 1] = new_pattern
    db_patterns[category] = patterns
    _save_database_patterns_setting(db_patterns)

    back_callback = context.user_data.get('patterns_back', 'settings_backup')
    update.message.reply_text(
        "✅ *Паттерн обновлён!*\n\n"
        f"Категория: *{category}*\n"
        f"Паттерн: `{new_pattern}`",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_default_db_pattern', None)
    context.user_data.pop('editing_default_db_category', None)
    context.user_data.pop('editing_default_db_index', None)
