"""
/bot/handlers/settings_handlers/backups/mail.py
Server Monitoring System v8.62.71
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mail server backup UI settings (PR7f серии оптимизации).
Система мониторинга серверов
Версия: 8.62.71
Автор: Александр Суханов (c)
Лицензия: MIT
Выделено из bot/handlers/settings_handlers/_legacy.py. Имена
сохранены — фасад пакета через двусторонний re-export продолжает
их отдавать; внутренние ссылки в _legacy.py резолвятся через
обратный `from ... import *` блок.
"""

import ast
import json
import re
import sqlite3
from datetime import datetime
from urllib.parse import quote, unquote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler
from telegram.utils.helpers import escape_markdown

from bot.handlers.settings_handlers.backups.db import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.proxmox import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.snapshot import *  # noqa: F401, F403

# PR7b: supplier_stock-функции вынесены в одноимённый модуль пакета;
# реэкспортируем их сюда же, чтобы внутренние ссылки в _legacy.py
# (например, settings_callback_handler) продолжали работать.
from bot.handlers.settings_handlers.supplier_stock import *  # noqa: F401, F403
from bot.handlers.settings_handlers.zfs import *  # noqa: F401, F403
from bot.handlers.zfs_pool_free_space_handlers import handle_text_input as handle_zfsp_text_input
from config.db_settings import BACKUP_DATABASE_CONFIG, load_all_settings
from config.settings import BACKUP_DB_FILE, BACKUP_PATTERNS as DEFAULT_BACKUP_PATTERNS
from core.config_manager import config_manager as settings_manager
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
from extensions.zfs_free_space_monitor import get_zfs_servers_config
from lib.logging import debug_log

BACKUP_SETTINGS_CALLBACKS = {
    "backup_times",
    "settings_backup_databases",
    "backup_db_add_category",
    "view_patterns",
    "add_pattern",
    "add_zfs_pattern",
    "add_proxmox_pattern",
    "add_mail_pattern",
    "add_stock_pattern",
    "add_snapshot_pattern",
    "edit_mail_default_pattern",
    "mail_pattern_confirm",
    "mail_pattern_retry",
    "stock_pattern_confirm",
    "stock_pattern_retry",
    "zfs_pattern_confirm",
    "zfs_pattern_retry",
    "db_pattern_confirm",
    "db_pattern_retry",
    "proxmox_pattern_confirm",
    "proxmox_pattern_retry",
    "snapshot_pattern_confirm",
    "snapshot_pattern_retry",
    "settings_patterns_db_from_backup",
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

    fallback_raw = settings_manager.get_setting("BACKUP_PATTERNS", DEFAULT_BACKUP_PATTERNS)
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
        [InlineKeyboardButton("🔍 Паттерны", callback_data="settings_patterns_mail")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_extensions"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_mail_patterns_menu(update, context):
    """Показать паттерны для бэкапов почты"""
    back_callback = (
        context.user_data.pop("patterns_back_override", None) or "settings_ext_backup_mail"
    )
    context.user_data["patterns_filter"] = "mail"
    context.user_data["patterns_back"] = back_callback
    context.user_data["patterns_add"] = "add_mail_pattern"
    context.user_data["patterns_title"] = "📬 *Паттерны бэкапов почты*"
    view_patterns_handler(update, context)


def add_mail_pattern_handler(update, context):
    """Добавить паттерн для бэкапов почты"""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "mail_input"
    context.user_data["backup_pattern_mode"] = "mail_wizard"

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна почты*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.\n\n"
        "Пример темы:\n"
        "`Бэкап Zimbra - 52G /backups/zimbra/2025-03-01`\n\n"
        "Пример фрагментов:\n"
        "`Бэкап Zimbra; /backups/zimbra`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=context.user_data.get("patterns_back", "settings_backup"),
                    ),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def edit_mail_default_pattern_handler(update, context):
    """Изменить дефолтный паттерн для бэкапов почты"""
    query = update.callback_query
    query.answer()

    fallback_patterns = _get_mail_fallback_patterns()
    current_pattern = fallback_patterns[0] if fallback_patterns else ""

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "pattern_only"
    context.user_data["backup_pattern_mode"] = "mail"

    query.edit_message_text(
        "✏️ *Изменение паттерна почты*\n\n"
        f"Текущий паттерн:\n`{current_pattern}`\n\n"
        "Введите новый regex паттерн темы письма:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=context.user_data.get("patterns_back", "settings_backup"),
                    ),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def mail_pattern_retry_handler(update, context):
    """Повторить ввод темы/фрагментов для паттерна почты."""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "mail_input"
    context.user_data["backup_pattern_mode"] = "mail_wizard"
    context.user_data.pop("backup_pattern_generated", None)
    context.user_data.pop("backup_pattern_source", None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна почты*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=context.user_data.get("patterns_back", "settings_backup"),
                    ),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def mail_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна почты."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get("backup_pattern_generated")
    back_callback = context.user_data.get("patterns_back", "settings_backup")

    if not pattern:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
                ]
            ),
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
            ("subject", pattern, "mail"),
        )
        conn.commit()

        source_label = context.user_data.get("backup_pattern_source", "мастер")
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *mail*\n"
            "Тип: *subject*\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
    finally:
        context.user_data.pop("adding_backup_pattern", None)
        context.user_data.pop("backup_pattern_stage", None)
        context.user_data.pop("backup_pattern_category", None)
        context.user_data.pop("backup_pattern_type", None)
        context.user_data.pop("backup_pattern_subject", None)
        context.user_data.pop("backup_pattern_mode", None)
        context.user_data.pop("backup_pattern_generated", None)
        context.user_data.pop("backup_pattern_source", None)
