"""
/bot/handlers/settings_handlers/backups/db.py
Server Monitoring System v8.62.64
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database backup UI settings extracted from _legacy.py (PR7e серии оптимизации).
Система мониторинга серверов
Версия: 8.62.64
Автор: Александр Суханов (c)
Лицензия: MIT
Самая крупная backup-семья (после supplier_stock): UI Telegram-настроек
бэкапов баз 1C/Cobian — категории БД, записи внутри категорий,
включение/выключение мониторинга, default-паттерны, токенизация
callback-data (`_build_db_*_callback`/`_resolve_db_*_from_callback`).
Имена сохранены — фасад пакета через двусторонний re-export продолжает
их отдавать.
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


def _build_db_monitor_toggle_callback(context, encoded_category: str, encoded_db_key: str) -> str:
    """Собирает короткий callback_data для переключателя мониторинга БД."""
    toggle_map = context.user_data.setdefault("settings_db_toggle_map", {})
    token = f"k{len(toggle_map)}"
    toggle_map[token] = f"{encoded_category}__{encoded_db_key}"
    return f"settings_db_toggle_monitor_{token}"


def _build_db_category_callback(context, action_prefix: str, category: str) -> str:
    """Собирает короткий callback_data для действий над категорией БД."""
    category_map = context.user_data.setdefault("settings_db_category_map", {})
    token = f"c{len(category_map)}"
    category_map[token] = str(category or "")
    return f"{action_prefix}{token}"


def _resolve_db_category_from_callback(context, value: str) -> str:
    """Расшифровать категорию БД из callback_data (token/raw/urlencoded)."""
    category_map = context.user_data.get("settings_db_category_map", {})
    if value in category_map:
        return str(category_map[value] or "")
    decoded = unquote(str(value or "")).strip()
    return decoded


def _build_db_entry_callback(context, action_prefix: str, category: str, db_key: str) -> str:
    """Собирает короткий callback_data для действий над конкретной БД."""
    entry_map = context.user_data.setdefault("settings_db_entry_map", {})
    token = f"d{len(entry_map)}"
    entry_map[token] = f"{category}__{db_key}"
    return f"{action_prefix}{token}"


def _resolve_db_entry_from_callback(context, value: str) -> tuple[str, str]:
    """Расшифровать (category, db_key) из callback_data (token/raw/urlencoded)."""
    entry_map = context.user_data.get("settings_db_entry_map", {})
    raw_value = str(entry_map.get(value, value) or "")
    if "__" not in raw_value:
        return "", ""
    raw_category, raw_db_key = raw_value.split("__", 1)
    return unquote(raw_category).strip(), unquote(raw_db_key).strip()


def _get_settings_db_back_callback(context, default: str = "settings_ext_backup_db") -> str:
    """Вернуть callback для кнопки «Назад» в меню БД."""
    back_callback = str(context.user_data.get("settings_db_back") or "").strip()
    return back_callback or default


def _get_disabled_db_monitors_settings() -> set[tuple[str, str]]:
    """Получить пары (backup_type, db_name), отключённые в мониторинге бэкапов БД."""
    raw_disabled = settings_manager.get_setting("DATABASE_MONITORING_DISABLED", [], use_cache=False)
    if isinstance(raw_disabled, str):
        raw_disabled = [raw_disabled]
    if not isinstance(raw_disabled, list):
        return set()

    disabled_pairs: set[tuple[str, str]] = set()
    for item in raw_disabled:
        value = str(item or "").strip()
        if "__" not in value:
            continue
        backup_type, db_name = value.split("__", 1)
        backup_type = backup_type.strip()
        db_name = db_name.strip()
        if backup_type and db_name:
            disabled_pairs.add((backup_type, db_name))
    return disabled_pairs


def _toggle_database_monitoring_settings(backup_type: str, db_name: str) -> bool:
    """Переключить мониторинг БД. Возвращает True, если мониторинг включён после переключения."""
    backup_type = str(backup_type or "").strip()
    db_name = str(db_name or "").strip()
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
    settings_manager.set_setting(
        "DATABASE_MONITORING_DISABLED", serialized, category="backup", data_type="auto"
    )
    return now_enabled


def _get_database_fallback_patterns() -> dict[str, list[str]]:
    """Получить запасные паттерны для бэкапов БД."""
    fallback_raw = settings_manager.get_setting("BACKUP_PATTERNS", DEFAULT_BACKUP_PATTERNS)
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
    settings_manager.set_setting("BACKUP_PATTERNS", raw_patterns)


def _get_database_names() -> list[str]:
    """Получить список имён БД из настроек."""
    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
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

    replaced = re.sub(re.escape(matched), "__DB__", text, flags=re.IGNORECASE)
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


def show_database_backup_settings(update, context):
    """Показать настройки бэкапов БД в разделе расширений"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    db_categories = list(db_config.keys()) if isinstance(db_config, dict) else []

    message = "🗃️ *Бэкапы БД*\n\n" f"Категорий: {len(db_categories)}\n\n" "Выберите раздел:"

    keyboard = [
        [InlineKeyboardButton("📋 Базы", callback_data="settings_db_main")],
        [InlineKeyboardButton("🔍 Паттерны", callback_data="settings_patterns_db")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_extensions"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_backup_databases_settings(update, context):
    """Показать настройки баз данных для бэкапов"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"

    if not db_config:
        message += "❌ *Базы данных не настроены*\n\n"
        message += "Здесь вы можете настроить категории и базы данных для мониторинга бэкапов."
    else:
        message += "*Текущие настройки:*\n\n"
        for category, databases in db_config.items():
            safe_category = _escape_pattern_text(str(category).upper())
            message += f"📁 *{safe_category}*\n"
            message += f"   Количество БД: {len(databases)}\n"
            # Показываем несколько примеров
            sample_dbs = list(databases.values())[:2]
            for db_name in sample_dbs:
                safe_db_name = _escape_pattern_text(db_name)
                message += f"   • {safe_db_name}\n"
            if len(databases) > 2:
                message += f"   • ... и еще {len(databases) - 2} БД\n"
            message += "\n"

    message += "Выберите действие:"

    back_callback = context.user_data.get("settings_db_back") or "settings_extensions"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить категорию", callback_data="settings_db_add_category")],
        [
            InlineKeyboardButton(
                "✏️ Редактировать категорию", callback_data="settings_db_edit_category"
            )
        ],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data="settings_db_delete_category")],
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data="settings_db_view_all")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_backup_databases_settings(update, context):
    """Показать настройки баз данных для бэкапов без перегруза inline-клавиатуры."""
    query = update.callback_query
    query.answer()

    # Сбрасываем состояния добавления/редактирования БД при выходе в меню
    context.user_data.pop("adding_db_entry", None)
    context.user_data.pop("editing_db_entry", None)
    context.user_data.pop("db_entry_category", None)
    context.user_data.pop("db_entry_key", None)
    context.user_data["settings_db_toggle_map"] = {}
    context.user_data["settings_db_category_map"] = {}
    context.user_data["settings_db_entry_map"] = {}

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"

    disabled_pairs = _get_disabled_db_monitors_settings()
    if not db_config:
        message += "❌ *Базы данных не настроены*\n\n"
    else:
        total_databases = 0
        for category, databases in db_config.items():
            if not isinstance(databases, dict):
                databases = {}
            total_databases += len(databases)
            disabled_in_category = sum(
                1 for db_key in databases if (category, db_key) in disabled_pairs
            )
            message += (
                f"• *{_escape_pattern_text(category.upper())}*: {len(databases)} БД "
                f"(отключён мониторинг: {disabled_in_category})\n"
            )

        message += f"\nИтого баз: *{total_databases}*\n\n"

    message += "Выберите действие:"

    keyboard = []
    sorted_categories = sorted(db_config.keys()) if isinstance(db_config, dict) else []
    category_buttons = [
        InlineKeyboardButton(
            f"⚙️ {category}",
            callback_data=_build_db_category_callback(context, "settings_db_edit_", category),
        )
        for category in sorted_categories[:20]
    ]
    for idx in range(0, len(category_buttons), 2):
        keyboard.append(category_buttons[idx : idx + 2])

    if len(sorted_categories) > 20:
        message += (
            "\n\nℹ️ Показаны первые 20 категорий. Для полного списка откройте «Управление базами»."
        )

    back_callback = _get_settings_db_back_callback(context)
    from_backup = back_callback == "backup_databases"
    view_all_callback = (
        "settings_db_view_all_from_backup" if from_backup else "settings_db_view_all"
    )
    manage_categories_callback = (
        "settings_db_manage_categories_from_backup"
        if from_backup
        else "settings_db_manage_categories"
    )

    keyboard.extend(
        [
            [InlineKeyboardButton("🛠️ Управление базами", callback_data=view_all_callback)],
            [
                InlineKeyboardButton(
                    "🗂️ Управление категориями", callback_data=manage_categories_callback
                )
            ],
            [
                InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_backup_databases(update, context):
    """Показать настройки баз данных для бэкапов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

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
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data="view_all_databases")],
        [
            InlineKeyboardButton("➕ Добавить БД", callback_data="add_database"),
            InlineKeyboardButton("✏️ Редактировать БД", callback_data="edit_databases"),
        ],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_backup_db"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_db_patterns_menu(update, context):
    """Показать паттерны для БД"""
    context.user_data["patterns_filter"] = "db"
    context.user_data["patterns_back"] = "settings_ext_backup_db"
    context.user_data["patterns_add"] = "add_pattern"
    context.user_data["patterns_title"] = "🗃️ *Паттерны бэкапов БД*"
    view_patterns_handler(update, context)


def show_db_patterns_menu_from_backup(update, context):
    """Показать паттерны БД из меню бэкапов БД."""
    context.user_data["patterns_filter"] = "db"
    context.user_data["patterns_back"] = "backup_databases"
    context.user_data["patterns_add"] = "add_pattern"
    context.user_data["patterns_title"] = "🗃️ *Паттерны бэкапов БД*"
    view_patterns_handler(update, context)


def add_database_category_handler(update, context):
    """Обработчик добавления категории БД"""
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "➕ *Добавление категории баз данных*\n\n"
        "Эта функция находится в разработке.\n"
        "Скоро здесь можно будет добавлять новые категории БД для мониторинга.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_backup_db"),
                    InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ]
            ]
        ),
    )


def edit_database_category_handler(update, context):
    """Обработчик редактирования категории БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    if not db_config:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить категорию", callback_data="backup_db_add_category")]
        ]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append(
                [InlineKeyboardButton(f"✏️ {category}", callback_data=f"edit_category_{category}")]
            )

    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_backup_db"),
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        "✏️ *Редактирование категорий баз данных*\n\n" "Выберите категорию для редактирования:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def delete_database_category_handler(update, context):
    """Обработчик удаления категории БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    if not db_config:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить категорию", callback_data="backup_db_add_category")]
        ]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append(
                [InlineKeyboardButton(f"🗑️ {category}", callback_data=f"delete_category_{category}")]
            )

    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_backup_db"),
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        "🗑️ *Удаление категории баз данных*\n\n" "Выберите категорию для удаления:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def view_all_databases_handler(update, context):
    """Обработчик просмотра всех БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    message = "📋 *Все базы данных для мониторинга*\n\n"

    if not db_config:
        message += "❌ *Нет настроенных баз данных*\n\n"
        message += "Добавьте категории и базы данных в настройках."
    else:
        total_dbs = 0
        for category, databases in db_config.items():
            safe_category = _escape_pattern_text(str(category).upper())
            message += f"📁 *{safe_category}* ({len(databases)} БД):\n"
            for db_key, db_name in databases.items():
                safe_db_name = _escape_pattern_text(db_name)
                message += f"   • {safe_db_name}\n"
                total_dbs += 1
            message += "\n"

        message += f"*Итого:* {total_dbs} баз данных в {len(db_config)} категориях"

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_backup_db"),
                    InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ]
            ]
        ),
    )


def view_all_databases_handler(update, context):
    """Просмотр всех БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    if not db_config:
        message = "📋 *Все базы данных*\n\n❌ *Нет настроенных баз данных*"
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Добавить категорию БД", callback_data="settings_db_add_category"
                )
            ]
        ]
    else:
        message = (
            "🛠️ *Управление базами данных*\n\n"
            "Выберите категорию для управления базами.\n"
            "_Детальные действия (редактирование/удаление)_ "
            "доступны внутри категории."
        )
        total_dbs = 0
        keyboard = []

        for category, databases in db_config.items():
            if not isinstance(databases, dict):
                databases = {}
            total_dbs += len(databases)
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📁 {category} ({len(databases)})",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_edit_", category
                        ),
                    )
                ]
            )

        message += f"\n\n*Итого:* {total_dbs} баз данных в {len(db_config)} категориях"

    keyboard.append(
        [InlineKeyboardButton("➕ Добавить новую БД", callback_data="settings_db_add_new")]
    )
    back_callback = context.user_data.get("settings_db_back") or "settings_ext_backup_db"
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_new_database_from_manage_handler(update, context):
    """Быстрое добавление новой БД из экрана 'Управление базами'."""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    if not db_config:
        query.edit_message_text(
            "➕ *Добавление новой БД*\n\n" "Сначала нужно создать хотя бы одну категорию БД.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➕ Добавить категорию", callback_data="settings_db_add_category"
                        )
                    ],
                    [InlineKeyboardButton("↩️ Назад", callback_data="settings_db_view_all")],
                ]
            ),
        )
        return

    keyboard = []
    for category in db_config.keys():
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"📁 {category}",
                    callback_data=_build_db_category_callback(
                        context, "settings_db_add_db_", category
                    ),
                )
            ]
        )

    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="settings_db_view_all")])

    query.edit_message_text(
        "➕ *Добавить новую БД*\n\n" "Выберите категорию, куда добавить базу:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def add_database_category_handler(update, context):
    """Добавить категорию БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()

    context.user_data["adding_db_category"] = True

    message = (
        "➕ *Добавление категории БД*\n\n"
        "Введите название новой категории:\n\n"
        "_Пример: company, client, backup_"
    )

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="settings_db_main")]]
        ),
    )


def manage_database_categories_handler(update, context):
    """Список категорий БД с быстрым редактированием и удалением."""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    categories = sorted(db_config.keys()) if isinstance(db_config, dict) else []
    total_categories = len(categories)
    back_callback = _get_settings_db_back_callback(context)

    lines = [
        "🗂️ *Управление категориями БД*",
        "",
        f"Всего категорий: *{total_categories}*",
    ]

    keyboard = [
        [InlineKeyboardButton("➕ Добавить категорию", callback_data="settings_db_add_category")]
    ]
    if not categories:
        lines.extend(["", "Категории пока не добавлены."])
    else:
        lines.extend(["", "Выберите категорию для действия:"])
        for category in categories:
            db_count = (
                len(db_config.get(category, {})) if isinstance(db_config.get(category), dict) else 0
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"✏️ {category} ({db_count})",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_rename_", category
                        ),
                    ),
                    InlineKeyboardButton(
                        "🗑️",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_delete_", category
                        ),
                    ),
                ]
            )

    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def edit_databases_handler(update, context):
    """Показать список категорий для переименования."""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    if not db_config:
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Добавить категорию", callback_data="settings_db_add_category"
                )
            ]
        ]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"✏️ {category}",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_rename_", category
                        ),
                    )
                ]
            )

    keyboard.append(
        [InlineKeyboardButton("↩️ Назад", callback_data="settings_db_manage_categories")]
    )

    query.edit_message_text(
        "✏️ *Редактирование категорий баз данных*\n\n" "Выберите категорию для переименования:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def start_database_category_edit_handler(update, context, category):
    """Запуск переименования существующей категории БД."""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_manage_categories")]]
            ),
        )
        return

    context.user_data["editing_db_category"] = True
    context.user_data["editing_db_category_old_name"] = category

    query.edit_message_text(
        "✏️ *Переименование категории БД*\n\n"
        f"Текущее название: *{_escape_pattern_text(category)}*\n\n"
        "Введите новое название категории:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="settings_db_manage_categories")]]
        ),
    )


def delete_database_category_handler(update, context):
    """Удалить категорию БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

    if not db_config:
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Добавить категорию", callback_data="settings_db_add_category"
                )
            ]
        ]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🗑️ {category}",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_delete_", category
                        ),
                    )
                ]
            )

    keyboard.append(
        [InlineKeyboardButton("↩️ Назад", callback_data="settings_db_manage_categories")]
    )

    query.edit_message_text(
        "🗑️ *Удаление категории БД*\n\n" "Выберите категорию для удаления:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def edit_database_category_details(update, context, category):
    """Показать детали категории БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(category)
    if databases is not None and not isinstance(databases, dict):
        databases = {}

    if databases is None:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    safe_category = _escape_pattern_text(category)
    message = f"✏️ *Категория {safe_category}*\n\n"
    if not databases:
        message += "❌ В этой категории нет баз данных.\n"
    else:
        message += "Список баз данных:\n"
        for db_key, db_name in databases.items():
            safe_db_name = _escape_pattern_text(db_name)
            safe_db_key = _escape_pattern_text(db_key)
            message += f"• {safe_db_name} (`{safe_db_key}`)\n"

    message += "\nВыберите действие:"

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Добавить БД",
                callback_data=_build_db_category_callback(context, "settings_db_add_db_", category),
            )
        ]
    ]
    for db_key, db_name in databases.items():
        encoded_backup_type = quote(str(category), safe="")
        encoded_db_name = quote(str(db_key), safe="")
        toggle_callback = _build_db_monitor_toggle_callback(
            context, encoded_backup_type, encoded_db_name
        )
        is_disabled = (category, db_key) in _get_disabled_db_monitors_settings()
        toggle_text = "✅ Вкл" if is_disabled else "⛔ Выкл"

        button_text = f"✏️ {db_name}"
        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=_build_db_entry_callback(
                        context, "settings_db_edit_db_", category, db_key
                    ),
                ),
                InlineKeyboardButton(toggle_text, callback_data=toggle_callback),
                InlineKeyboardButton(
                    f"🗑️ {db_name}",
                    callback_data=_build_db_entry_callback(
                        context, "settings_db_delete_db_", category, db_key
                    ),
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_db_view_all"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_database_entry_handler(update, context, category):
    """Запуск добавления базы данных в категорию"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    # Инициализируем состояние добавления БД
    context.user_data["adding_db_entry"] = True
    context.user_data["db_entry_category"] = category
    context.user_data.pop("db_entry_key", None)

    query.edit_message_text(
        "➕ *Добавление базы данных*\n\n"
        f"Категория: *{category}*\n\n"
        "Введите ключ базы данных (латиница/цифры/символы `_`, `-`, `.`):\n\n"
        "_Пример: trade, client_db_01_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="settings_db_main")]]
        ),
    )


def edit_database_entry_handler(update, context, category, db_key):
    """Запуск редактирования базы данных"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    if not isinstance(databases, dict):
        databases = {}
    if db_key not in databases:
        query.edit_message_text(
            "❌ База данных не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    context.user_data["editing_db_entry"] = True
    context.user_data["db_entry_category"] = category
    context.user_data["db_entry_key"] = db_key

    query.edit_message_text(
        "✏️ *Редактирование базы данных*\n\n"
        f"Категория: *{category}*\n"
        f"Ключ: `{db_key}`\n"
        "Введите новый ключ:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="settings_db_main")]]
        ),
    )


def delete_database_entry_confirmation(update, context, category, db_key):
    """Подтверждение удаления базы данных"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    db_name = databases.get(db_key)

    if db_name is None:
        query.edit_message_text(
            "❌ База данных не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    query.edit_message_text(
        "🗑️ *Удаление базы данных*\n\n"
        f"Категория: *{category}*\n"
        f"База: `{db_name}`\n\n"
        "Удалить?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Удалить",
                        callback_data=_build_db_entry_callback(
                            context, "settings_db_delete_db_confirm_", category, db_key
                        ),
                    )
                ],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_db_view_all"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def delete_database_entry_execute(update, context, category, db_key):
    """Удаление базы данных"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    db_name = databases.pop(db_key, None)

    if db_name is None:
        query.edit_message_text(
            "❌ База данных не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    db_config[category] = databases
    settings_manager.set_setting("DATABASE_CONFIG", db_config)

    query.edit_message_text(
        "✅ *База данных удалена!*\n\n" f"Категория: *{category}*\n" f"База: `{db_name}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_db_view_all"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ]
            ]
        ),
    )


def settings_toggle_database_monitoring(update, context, encoded_backup_type, encoded_db_name):
    """Переключение мониторинга конкретной БД из настроек."""
    query = update.callback_query
    query.answer()

    backup_type = unquote(str(encoded_backup_type or "")).strip()
    db_name = unquote(str(encoded_db_name or "")).strip()
    if not backup_type or not db_name:
        query.edit_message_text(
            "❌ Не удалось переключить мониторинг: пустой тип или имя БД.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(backup_type, {})
    if not isinstance(databases, dict):
        databases = {}
    if db_name not in databases:
        query.edit_message_text(
            "❌ База данных не найдена в настройках.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
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
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Назад",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_edit_", backup_type
                        ),
                    )
                ],
                [
                    InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def delete_database_category_confirmation(update, context, category):
    """Подтверждение удаления категории БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main")]]
            ),
        )
        return

    message = "🗑️ *Удаление категории БД*\n\n" f"Категория: *{category}*\n" "Подтвердите удаление:"

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Удалить",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_delete_confirm_", category
                        ),
                    )
                ],
                [InlineKeyboardButton("↩️ Назад", callback_data="settings_db_manage_categories")],
            ]
        ),
    )


def delete_database_category_execute(update, context, category):
    """Удалить категорию БД"""
    query = update.callback_query
    query.answer()

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    if category not in db_config:
        query.edit_message_text(
            "❌ Категория не найдена.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_db_manage_categories")]]
            ),
        )
        return

    db_config.pop(category, None)
    settings_manager.set_setting("DATABASE_CONFIG", db_config)

    query.edit_message_text(
        f"✅ Категория *{category}* удалена.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_db_manage_categories"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ]
            ]
        ),
    )


def handle_db_category_input(update, context):
    """Обработчик ввода категории БД"""
    if "adding_db_category" not in context.user_data:
        return

    category_name = update.message.text.strip()

    try:
        # Получаем текущую конфигурацию БД
        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

        # Добавляем новую категорию
        if category_name not in db_config:
            db_config[category_name] = {}
            settings_manager.set_setting("DATABASE_CONFIG", db_config)

            update.message.reply_text(
                f"✅ *Категория '{category_name}' добавлена!*\n\n"
                "Теперь вы можете добавить базы данных в эту категорию.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✏️ Добавить БД",
                                callback_data=_build_db_category_callback(
                                    context, "settings_db_edit_", category_name
                                ),
                            ),
                            InlineKeyboardButton(
                                "↩️ Назад", callback_data="settings_db_manage_categories"
                            ),
                        ]
                    ]
                ),
            )
        else:
            update.message.reply_text(
                f"❌ Категория '{category_name}' уже существует!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "↩️ Назад", callback_data="settings_db_manage_categories"
                            )
                        ]
                    ]
                ),
            )

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")

    # Очищаем состояние
    context.user_data["adding_db_category"] = False


def handle_db_category_rename_input(update, context):
    """Обработчик переименования категории БД."""
    if "editing_db_category" not in context.user_data:
        return

    old_name = context.user_data.get("editing_db_category_old_name")
    new_name = (update.message.text or "").strip()

    try:
        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})

        if not old_name or old_name not in db_config:
            update.message.reply_text(
                "❌ Исходная категория не найдена.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "↩️ Назад", callback_data="settings_db_manage_categories"
                            )
                        ]
                    ]
                ),
            )
            return

        if not new_name:
            update.message.reply_text("❌ Новое название не может быть пустым. Попробуйте снова:")
            return

        if new_name == old_name:
            update.message.reply_text("ℹ️ Название не изменилось. Введите другое название:")
            return

        if new_name in db_config:
            update.message.reply_text(
                f"❌ Категория '{new_name}' уже существует. Введите другое название:"
            )
            return

        updated_config = dict(db_config)
        updated_config[new_name] = updated_config.pop(old_name)
        settings_manager.set_setting("DATABASE_CONFIG", updated_config)

        update.message.reply_text(
            f"✅ Категория '{old_name}' переименована в '{new_name}'.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ К управлению категориями",
                            callback_data="settings_db_manage_categories",
                        )
                    ]
                ]
            ),
        )
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    finally:
        context.user_data.pop("editing_db_category", None)
        context.user_data.pop("editing_db_category_old_name", None)


def handle_db_entry_input(update, context):
    """Обработчик добавления базы данных"""
    if "adding_db_entry" not in context.user_data:
        return

    user_input = update.message.text.strip()
    category = context.user_data.get("db_entry_category")

    if not category:
        update.message.reply_text("❌ Категория не найдена. Попробуйте снова.")
        context.user_data["adding_db_entry"] = False
        return

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(category, {})
    if not isinstance(databases, dict):
        databases = {}
    if not isinstance(databases, dict):
        databases = {}

    if not user_input:
        update.message.reply_text("❌ Ключ не может быть пустым. Попробуйте снова:")
        return

    if " " in user_input:
        update.message.reply_text("❌ Ключ не должен содержать пробелы. Попробуйте снова:")
        return

    if user_input in databases:
        update.message.reply_text("❌ Такой ключ уже существует. Введите другой:")
        return

    databases[user_input] = user_input
    db_config[category] = databases
    settings_manager.set_setting("DATABASE_CONFIG", db_config)

    update.message.reply_text(
        "✅ *База данных добавлена!*\n\n" f"Категория: *{category}*\n" f"Ключ: `{user_input}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main"),
                    InlineKeyboardButton(
                        "✏️ Добавить еще",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_add_db_", category
                        ),
                    ),
                ]
            ]
        ),
    )

    context.user_data.pop("adding_db_entry", None)
    context.user_data.pop("db_entry_category", None)
    context.user_data.pop("db_entry_key", None)


def handle_db_entry_edit_input(update, context):
    """Обработчик редактирования базы данных"""
    if "editing_db_entry" not in context.user_data:
        return

    user_input = update.message.text.strip()
    category = context.user_data.get("db_entry_category")
    db_key = context.user_data.get("db_entry_key")

    if not category or not db_key:
        update.message.reply_text("❌ Не удалось определить базу данных. Попробуйте снова.")
        context.user_data["editing_db_entry"] = False
        return

    if not user_input:
        update.message.reply_text("❌ Ключ не может быть пустым. Попробуйте снова:")
        return

    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    databases = db_config.get(category, {})

    if db_key not in databases:
        update.message.reply_text("❌ База данных не найдена.")
        context.user_data["editing_db_entry"] = False
        return

    if user_input in databases and user_input != db_key:
        update.message.reply_text("❌ Такой ключ уже существует. Введите другой:")
        return

    databases.pop(db_key, None)
    databases[user_input] = user_input
    db_config[category] = databases
    settings_manager.set_setting("DATABASE_CONFIG", db_config)

    update.message.reply_text(
        "✅ *База данных обновлена!*\n\n"
        f"Категория: *{category}*\n"
        f"Новый ключ: `{user_input}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_db_main"),
                    InlineKeyboardButton(
                        "✏️ Редактировать еще",
                        callback_data=_build_db_category_callback(
                            context, "settings_db_edit_", category
                        ),
                    ),
                ]
            ]
        ),
    )

    context.user_data.pop("editing_db_entry", None)
    context.user_data.pop("db_entry_category", None)
    context.user_data.pop("db_entry_key", None)


def db_pattern_retry_handler(update, context):
    """Повторить ввод темы/фрагментов для паттерна БД."""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "db_input"
    context.user_data["backup_pattern_mode"] = "db_wizard"
    context.user_data.pop("backup_pattern_generated", None)
    context.user_data.pop("backup_pattern_source", None)
    context.user_data.pop("backup_pattern_category", None)
    context.user_data.pop("backup_pattern_db_name", None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна БД*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя БД из настроек.",
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


def _get_database_categories() -> list[str]:
    """Получить список категорий БД из настроек."""
    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    if not isinstance(db_config, dict):
        return []
    return sorted([key for key in db_config.keys() if isinstance(key, str)])


def _show_db_pattern_confirm(update, context):
    """Показать экран подтверждения паттерна БД с выбором категории."""
    pattern = context.user_data.get("backup_pattern_generated")
    db_name = context.user_data.get("backup_pattern_db_name", "")
    category = context.user_data.get("backup_pattern_category", "")
    source_label = context.user_data.get("backup_pattern_source", "мастер")
    back_callback = context.user_data.get("patterns_back", "settings_backup")

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
                    label, callback_data=f"db_pattern_set_category_{category_name}"
                )
            )
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    keyboard.extend(
        [
            [InlineKeyboardButton("✅ Сохранить", callback_data="db_pattern_confirm")],
            [InlineKeyboardButton("✏️ Ввести заново", callback_data="db_pattern_retry")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

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
            message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    update.message.reply_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def db_pattern_set_category_handler(update, context, category: str):
    """Выбрать категорию для паттерна БД."""
    context.user_data["backup_pattern_category"] = category
    _show_db_pattern_confirm(update, context)


def db_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна БД."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get("backup_pattern_generated")
    category = context.user_data.get("backup_pattern_category")
    back_callback = context.user_data.get("patterns_back", "settings_backup")

    if not pattern or not category:
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
            ("subject", pattern, category),
        )
        conn.commit()

        source_label = context.user_data.get("backup_pattern_source", "мастер")
        db_name = context.user_data.get("backup_pattern_db_name", "")
        db_info = f"БД: *{db_name}*\n" if db_name else ""
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            f"{db_info}"
            f"Категория: *{category}*\n"
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
        context.user_data.pop("backup_pattern_db_name", None)


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
    context.user_data["editing_default_db_pattern"] = True
    context.user_data["editing_default_db_category"] = category
    context.user_data["editing_default_db_index"] = index

    back_callback = context.user_data.get("patterns_back", "settings_backup")
    query.edit_message_text(
        "✏️ *Редактирование дефолтного паттерна БД*\n\n"
        f"Категория: *{category}*\n"
        f"Текущий паттерн: `{current_pattern}`\n\n"
        "Введите новый regex паттерн темы письма:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data=back_callback),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
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

    back_callback = context.user_data.get("patterns_back", "settings_backup")
    query.edit_message_text(
        "✅ Дефолтный паттерн удалён.",
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


def _get_database_category(db_name):
    """Получить категорию базы данных по ключу"""
    db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    if not isinstance(db_config, dict):
        return "unknown"
    for category, databases in db_config.items():
        if isinstance(databases, dict) and db_name in databases:
            return category
    return "unknown"


def handle_default_db_pattern_edit_input(update, context):
    """Обработчик редактирования дефолтного паттерна БД."""
    new_pattern = update.message.text.strip()
    if not new_pattern:
        update.message.reply_text("❌ Паттерн не может быть пустым. Попробуйте снова:")
        return

    category = context.user_data.get("editing_default_db_category")
    index = context.user_data.get("editing_default_db_index")
    if not category or not index:
        update.message.reply_text("❌ Не найден паттерн для редактирования.")
        context.user_data.pop("editing_default_db_pattern", None)
        return

    db_patterns = _get_database_patterns_setting()
    patterns = db_patterns.get(category, [])
    if index < 1 or index > len(patterns):
        update.message.reply_text("❌ Паттерн не найден.")
        context.user_data.pop("editing_default_db_pattern", None)
        return

    patterns[index - 1] = new_pattern
    db_patterns[category] = patterns
    _save_database_patterns_setting(db_patterns)

    back_callback = context.user_data.get("patterns_back", "settings_backup")
    update.message.reply_text(
        "✅ *Паттерн обновлён!*\n\n" f"Категория: *{category}*\n" f"Паттерн: `{new_pattern}`",
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

    context.user_data.pop("editing_default_db_pattern", None)
    context.user_data.pop("editing_default_db_category", None)
    context.user_data.pop("editing_default_db_index", None)
