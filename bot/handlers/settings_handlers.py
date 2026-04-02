"""
/bot/handlers/settings_handlers.py
Server Monitoring System v8.0.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for managing settings via a bot
Система мониторинга серверов
Версия: 8.0.1
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики для управления настройками через бота
"""

import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.utils.helpers import escape_markdown
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from core.config_manager import config_manager as settings_manager
from config.db_settings import BACKUP_DATABASE_CONFIG
from config.settings import BACKUP_PATTERNS as DEFAULT_BACKUP_PATTERNS
from extensions.extension_manager import extension_manager
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
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
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

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    proxmox_count = len(proxmox_hosts) if isinstance(proxmox_hosts, dict) else 0

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
        query.answer("⚙️ Перенаправление к модулю бэкапов...")
        # Передаем обработку дальше по цепочке
        return
    if data.startswith('backup_') and data not in BACKUP_SETTINGS_CALLBACKS:
        query.answer("⚙️ Перенаправление к модулю бэкапов...")
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
            context.user_data['settings_extensions_manage_open'] = not context.user_data.get(
                'settings_extensions_manage_open',
                False
            )
            show_settings_extensions_menu(update, context)
        elif data == 'settings_ext_backup_proxmox':
            show_proxmox_backup_settings(update, context)
        elif data == 'settings_ext_backup_db':
            show_database_backup_settings(update, context)
        elif data == 'settings_ext_backup_mail':
            show_mail_backup_settings(update, context)
        elif data == 'settings_ext_stock_load':
            show_stock_load_settings(update, context)
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
                query.answer(message)
                show_extensions_settings_menu(update, context)
            else:
                query.answer(message, show_alert=True)
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
            query.answer("⚙️ Этот раздел в разработке")
    
    except Exception as e:
        print(f"❌ Ошибка в settings_callback_handler: {e}")
        debug_logger(f"Ошибка в settings_callback_handler: {e}")
        query.answer("❌ Произошла ошибка при обработке запроса")
    
    query.answer()

def handle_setting_input(update, context, setting_key):
    """Обработчик ввода значений настроек - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем какое настройку меняем
    context.user_data['editing_setting'] = setting_key
    
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
        
        db_key = setting_key.upper() if setting_key != 'telegram_token' else 'TELEGRAM_TOKEN'
        category = category_map.get(setting_key, 'general')
        
        settings_manager.set_setting(db_key, new_value, category)
        
        # Очищаем контекст
        del context.user_data['editing_setting']
        
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
        if row:
            keyboard.append(row)

    keyboard.extend([
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='settings_db_view_all')],
        [InlineKeyboardButton("➕ Добавить категорию БД", callback_data='settings_db_add_category')],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data='settings_db_delete_category')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_ext_backup_db'),
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

    is_manage_open = context.user_data.get('settings_extensions_manage_open', False)

    message = "🧩 *Расширения*\n\nВыберите раздел:"
    if is_manage_open:
        message += "\n\n📊 *Статус расширений:*\n\n"

    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("💾 Бэкапы Proxmox", callback_data='settings_ext_backup_proxmox')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='settings_ext_backup_db')])

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append([InlineKeyboardButton("📬 Бэкапы почты", callback_data='settings_ext_backup_mail')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("📦 Загрузка остатков 1С", callback_data='settings_ext_stock_load')])

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append([InlineKeyboardButton("🧊 ZFS", callback_data='settings_zfs')])

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("💻 Ресурсы", callback_data='settings_resources')])

    manage_button_text = "🙈 Скрыть настройки расширений" if is_manage_open else "🛠️ Открыть настройки расширений"
    keyboard.append([InlineKeyboardButton(manage_button_text, callback_data='settings_extensions_manage')])

    if is_manage_open:
        extensions_status = extension_manager.get_extensions_status()
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
        ])

    keyboard.extend([
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

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    message = "🖥️ *Бэкапы Proxmox*\n\n"
    if not proxmox_hosts:
        message += "❌ Хосты не настроены.\n\n"
    else:
        message += f"Хостов в списке: {len(proxmox_hosts)}\n\n"

    message += "Выберите действие:"

    keyboard = [
        [InlineKeyboardButton("📋 Список хостов", callback_data='settings_proxmox_list')],
        [InlineKeyboardButton("➕ Добавить хост", callback_data='settings_proxmox_add')],
        [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

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
        InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu'),
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def delete_proxmox_host(update, context, host_name):
    """Удалить хост Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name in proxmox_hosts:
        update.message.reply_text("❌ Такой хост уже есть. Введите другой:")
        return

    proxmox_hosts[host_name] = {'enabled': True}
    settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)

    update.message.reply_text(
        f"✅ Хост `{host_name}` добавлен.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_proxmox'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

    context.user_data.pop('adding_proxmox_host', None)

def edit_proxmox_host_handler(update, context, host_name):
    """Начать редактирование хоста Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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

    proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
    if not isinstance(proxmox_hosts, dict):
        proxmox_hosts = {}

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
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
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu')],
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
                    [InlineKeyboardButton("↩️ Назад", callback_data='main_menu')],
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
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu')],
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
        InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu'),
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_databases')]
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
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_databases')])
    
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
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_databases')])
    
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
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup_databases')]
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
        "_Пример: 192.168.1.100_"
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
    
    if not db_config:
        message = "📋 *Все базы данных*\n\n❌ *Нет настроенных баз данных*"
    else:
        message = "📋 *Все базы данных*\n\n"
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
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
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

    keyboard = [[InlineKeyboardButton("➕ Добавить БД", callback_data=f"settings_db_add_db_{category}")]]
    for db_key, db_name in databases.items():
        button_text = f"✏️ {db_name}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"settings_db_edit_db_{category}__{db_key}"),
            InlineKeyboardButton(f"🗑️ {db_name}", callback_data=f"settings_db_delete_db_{category}__{db_key}")
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
        InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu'),
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
                    [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
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
            [InlineKeyboardButton("🏠 Главное меню", callback_data='main_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

    context.user_data.pop('editing_default_db_pattern', None)
    context.user_data.pop('editing_default_db_category', None)
    context.user_data.pop('editing_default_db_index', None)
