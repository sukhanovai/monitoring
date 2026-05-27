"""
/bot/handlers/settings_handlers/zfs.py
Server Monitoring System v8.62.62
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ZFS settings UI handlers extracted from
bot/handlers/settings_handlers/_legacy.py (PR7c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.62
Автор: Александр Суханов (c)
Лицензия: MIT
Блок UI Telegram-бота для настроек ZFS-мониторинга: меню статуса
ZFS-пулов на серверах (`show_zfs_*`), CRUD-операции над списком
серверов (add/edit/delete/toggle), DB-helpers состояния мониторинга
ZFS-пулов и pattern-меню (`show_zfs_patterns_menu`,
`add_zfs_pattern_handler`, `zfs_pattern_retry_handler`,
`zfs_pattern_confirm_handler`). Имена сохранены — фасад пакета через
двусторонний re-export продолжает отдавать их.
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

# PR7b: supplier_stock-функции вынесены в одноимённый модуль пакета;
# реэкспортируем их сюда же, чтобы внутренние ссылки в _legacy.py
# (например, settings_callback_handler) продолжали работать.
from bot.handlers.settings_handlers.supplier_stock import *  # noqa: F401, F403
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


def _get_zfs_server_names() -> list[str]:
    """Получить список имён ZFS серверов из настроек."""
    zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
    if isinstance(zfs_servers, dict):
        return [name for name in zfs_servers.keys() if isinstance(name, str)]
    return []


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


def show_zfs_patterns_menu(update, context):
    """Показать паттерны для ZFS"""
    context.user_data["patterns_filter"] = "zfs"
    context.user_data["patterns_back"] = "settings_zfs"
    context.user_data["patterns_add"] = "add_zfs_pattern"
    context.user_data["patterns_title"] = "🧊 *Паттерны ZFS*"
    view_patterns_handler(update, context)


def show_zfs_settings(update, context):
    """Показать настройки ZFS"""
    query = update.callback_query
    query.answer()

    show_zfs_main_menu(update, context)


def show_zfs_main_menu(update, context):
    """Показать меню ZFS из главного меню"""
    query = update.callback_query
    query.answer()

    status_lines = _build_zfs_current_status_lines()
    keyboard = [
        [InlineKeyboardButton("📋 Хосты", callback_data="settings_zfs_list")],
        [InlineKeyboardButton("🔍 Паттерны", callback_data="settings_patterns_zfs")],
        [InlineKeyboardButton("⏰ Время старта", callback_data="set_silent_start")],
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        "\n".join(status_lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_zfs_status_summary(update, context):
    """Совместимость: перенаправить в меню ZFS-мониторинга по почтовым паттернам."""
    show_zfs_main_menu(update, context)


def show_zfs_servers_list(update, context):
    """Показать список ZFS серверов"""
    query = update.callback_query
    query.answer()

    zfs_servers = get_zfs_servers_config()

    message = "📋 *ZFS серверы*\n\n"
    if not zfs_servers:
        message += "❌ Серверы не настроены."
    else:
        for server_name in sorted(zfs_servers.keys()):
            server_value = zfs_servers.get(server_name, {})
            enabled = bool(server_value.get("enabled", True))
            status_icon = "🟢" if enabled else "🔴"
            message += (
                f"{status_icon} `{server_name}`\n"
                "   └ Используется для сопоставления с письмами ZFS\n"
            )

    keyboard = []
    for server_name in sorted(zfs_servers.keys()):
        server_value = zfs_servers.get(server_name, {})
        enabled = bool(server_value.get("enabled", True))
        toggle_text = "⛔️ Отключить" if enabled else "✅ Включить"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ Имя: {server_name}", callback_data=f"settings_zfs_edit_name_{server_name}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🗑️ {server_name}", callback_data=f"settings_zfs_delete_{server_name}"
                ),
                InlineKeyboardButton(
                    f"{toggle_text} {server_name}",
                    callback_data=f"settings_zfs_toggle_{server_name}",
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton("➕ Добавить сервер", callback_data="settings_zfs_add")])

    keyboard.append(
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_zfs_server_handler(update, context):
    """Добавить ZFS сервер"""
    query = update.callback_query
    query.answer()

    context.user_data["adding_zfs_server"] = True
    context.user_data["zfs_server_stage"] = "name"

    query.edit_message_text(
        "➕ *Добавление ZFS сервера*\n\n" "Введите имя хоста:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data="settings_zfs"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def _build_zfs_current_status_lines() -> list[str]:
    """Собрать краткий список текущих статусов ZFS из базы писем."""
    zfs_servers = get_zfs_servers_config()
    allowed_servers = {
        name
        for name, server_value in zfs_servers.items()
        if not isinstance(server_value, dict) or server_value.get("enabled", True)
    }

    lines: list[str] = ["🧊 *Мониторинг ZFS*", ""]

    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path:
        lines.append("❌ База бэкапов не настроена.")
        lines.append("")
        lines.append("Выберите раздел:")
        return lines

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
            lines.append("❌ Таблица ZFS ещё не создана.")
            lines.append("Дождитесь первого письма мониторинга.")
        else:
            lines.append(f"❌ Не удалось получить статусы ZFS: {exc}")
        lines.append("")
        lines.append("Выберите раздел:")
        return lines
    finally:
        conn.close()

    if allowed_servers:
        rows = [row for row in rows if row[0] in allowed_servers]
    else:
        rows = []

    if not rows:
        lines.append("❌ Нет данных по пулам ZFS.")
        lines.append("")
        lines.append("Выберите раздел:")
        return lines

    lines.append("📊 *Текущее состояние пулов*")
    lines.append("")
    healthy_states = {"ONLINE"}
    current_server = None
    for server_name, pool_name, pool_state, received_at in rows:
        if server_name != current_server:
            if current_server is not None:
                lines.append("")
            lines.append(f"🖥 *{escape_markdown(str(server_name), version=1)}*")
            current_server = server_name

        normalized_state = str(pool_state or "").strip().upper()
        state_marker = "🟢" if normalized_state in healthy_states else "🔴"
        lines.append(
            f"{state_marker} `{escape_markdown(str(pool_name), version=1)}`: "
            f"`{escape_markdown(str(pool_state), version=1)}` "
            f"({escape_markdown(str(received_at), version=1)})"
        )

    lines.append("")
    lines.append("Выберите раздел:")
    return lines


def delete_zfs_server(update, context, server_name):
    """Удалить ZFS сервер"""
    query = update.callback_query
    query.answer()

    zfs_servers = get_zfs_servers_config()

    if server_name not in zfs_servers:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    zfs_servers.pop(server_name, None)
    settings_manager.set_setting("ZFS_SERVERS", zfs_servers)
    _delete_zfs_monitoring_state(server_name)
    _delete_zfs_server_statuses(server_name)

    query.edit_message_text(
        f"✅ Сервер `{server_name}` удалён.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def handle_zfs_server_input(update, context):
    """Обработчик добавления ZFS сервера"""
    if "adding_zfs_server" not in context.user_data:
        return

    user_input = update.message.text.strip()
    stage = context.user_data.get("zfs_server_stage", "name")
    zfs_servers = get_zfs_servers_config()

    if stage == "name":
        if not user_input:
            update.message.reply_text("❌ Имя сервера не может быть пустым. Попробуйте снова:")
            return

        if user_input in zfs_servers:
            update.message.reply_text("❌ Такой сервер уже есть. Введите другой:")
            return

        host_name = user_input
        zfs_servers[host_name] = {
            "ip": "",
            "threshold": 15,
            "enabled": True,
        }
        settings_manager.set_setting("ZFS_SERVERS", zfs_servers)
        _set_zfs_monitoring_state(host_name, True)

        update.message.reply_text(
            "✅ Сервер добавлен.\n" f"Имя: `{host_name}`\n" "Источник данных: письма/паттерны ZFS",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

        context.user_data.pop("adding_zfs_server", None)
        context.user_data.pop("zfs_server_stage", None)
        context.user_data.pop("zfs_new_server_name", None)
        context.user_data.pop("zfs_new_server_ip", None)


def edit_zfs_server_name_handler(update, context, server_name):
    """Начать редактирование имени ZFS сервера"""
    query = update.callback_query
    query.answer()

    zfs_servers = get_zfs_servers_config()

    if server_name not in zfs_servers:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    context.user_data["editing_zfs_server_name"] = True
    context.user_data["editing_zfs_server_old_name"] = server_name

    query.edit_message_text(
        "✏️ *Редактирование ZFS сервера*\n\n"
        f"Текущее имя: `{server_name}`\n\n"
        "Введите новое имя сервера:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data="settings_zfs"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def handle_zfs_server_name_edit_input(update, context):
    """Обработчик редактирования имени ZFS сервера"""
    if "editing_zfs_server_name" not in context.user_data:
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("❌ Имя сервера не может быть пустым. Попробуйте снова:")
        return

    zfs_servers = get_zfs_servers_config()

    old_name = context.user_data.get("editing_zfs_server_old_name")
    if not old_name or old_name not in zfs_servers:
        update.message.reply_text("❌ Сервер не найден.")
        context.user_data.pop("editing_zfs_server_name", None)
        context.user_data.pop("editing_zfs_server_old_name", None)
        return

    if new_name in zfs_servers and new_name != old_name:
        update.message.reply_text("❌ Такой сервер уже есть. Введите другой:")
        return

    server_value = zfs_servers.pop(old_name, None)
    if not isinstance(server_value, dict):
        server_value = {"enabled": True, "ip": "", "threshold": 15}
    zfs_servers[new_name] = server_value
    settings_manager.set_setting("ZFS_SERVERS", zfs_servers)
    _rename_zfs_server_statuses(old_name, new_name)
    _rename_zfs_monitoring_state(old_name, new_name)

    update.message.reply_text(
        f"✅ Сервер обновлён: `{new_name}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )

    context.user_data.pop("editing_zfs_server_name", None)
    context.user_data.pop("editing_zfs_server_old_name", None)


def edit_zfs_server_ip_handler(update, context, server_name):
    """Начать редактирование IP ZFS сервера."""
    query = update.callback_query
    query.answer()

    zfs_servers = get_zfs_servers_config()
    if server_name not in zfs_servers:
        query.edit_message_text("❌ Сервер не найден.")
        return

    context.user_data["editing_zfs_server_ip"] = True
    context.user_data["editing_zfs_server_ip_name"] = server_name
    current_ip = str(zfs_servers.get(server_name, {}).get("ip", "")).strip()

    query.edit_message_text(
        "🌐 *Редактирование IP ZFS сервера*\n\n"
        f"Хост: `{server_name}`\n"
        f"Текущий IP: `{current_ip or 'не задан'}`\n\n"
        "Введите новый IP:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data="settings_zfs_list"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def handle_zfs_server_ip_edit_input(update, context):
    """Обработчик изменения IP ZFS сервера."""
    if "editing_zfs_server_ip" not in context.user_data:
        return

    new_ip = update.message.text.strip()
    if not new_ip:
        update.message.reply_text("❌ IP адрес не может быть пустым.")
        return

    server_name = str(context.user_data.get("editing_zfs_server_ip_name", "")).strip()
    zfs_servers = get_zfs_servers_config()
    if server_name not in zfs_servers:
        update.message.reply_text("❌ Сервер не найден.")
    else:
        zfs_servers[server_name]["ip"] = new_ip
        settings_manager.set_setting("ZFS_SERVERS", zfs_servers)
        update.message.reply_text(
            f"✅ IP для `{server_name}` обновлен: `{new_ip}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs_list"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

    context.user_data.pop("editing_zfs_server_ip", None)
    context.user_data.pop("editing_zfs_server_ip_name", None)


def edit_zfs_server_threshold_handler(update, context, server_name):
    """Начать редактирование порога свободного места ZFS сервера."""
    query = update.callback_query
    query.answer()

    zfs_servers = get_zfs_servers_config()
    if server_name not in zfs_servers:
        query.edit_message_text("❌ Сервер не найден.")
        return

    threshold = int(zfs_servers.get(server_name, {}).get("threshold", 15))
    context.user_data["editing_zfs_server_threshold"] = True
    context.user_data["editing_zfs_server_threshold_name"] = server_name

    query.edit_message_text(
        "🎯 *Редактирование порога ZFS*\n\n"
        f"Хост: `{server_name}`\n"
        f"Текущий порог: `{threshold}%`\n\n"
        "Введите новый порог (1..95):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data="settings_zfs_list"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def handle_zfs_server_threshold_edit_input(update, context):
    """Обработчик изменения порога ZFS сервера."""
    if "editing_zfs_server_threshold" not in context.user_data:
        return

    try:
        threshold = int(update.message.text.strip())
    except ValueError:
        update.message.reply_text("❌ Порог должен быть целым числом.")
        return

    if threshold < 1 or threshold > 95:
        update.message.reply_text("❌ Порог должен быть в диапазоне 1..95.")
        return

    server_name = str(context.user_data.get("editing_zfs_server_threshold_name", "")).strip()
    zfs_servers = get_zfs_servers_config()
    if server_name not in zfs_servers:
        update.message.reply_text("❌ Сервер не найден.")
    else:
        zfs_servers[server_name]["threshold"] = threshold
        settings_manager.set_setting("ZFS_SERVERS", zfs_servers)
        update.message.reply_text(
            f"✅ Порог для `{server_name}` обновлен: `{threshold}%`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs_list"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

    context.user_data.pop("editing_zfs_server_threshold", None)
    context.user_data.pop("editing_zfs_server_threshold_name", None)


def toggle_zfs_server(update, context, server_name):
    """Включить/отключить мониторинг ZFS сервера"""
    query = update.callback_query
    query.answer()

    zfs_servers = get_zfs_servers_config()

    if server_name not in zfs_servers:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    server_value = zfs_servers.get(server_name)
    if isinstance(server_value, dict):
        enabled = server_value.get("enabled", True)
    else:
        enabled = True
        server_value = {"enabled": True, "ip": "", "threshold": 15}

    server_value["enabled"] = not enabled
    zfs_servers[server_name] = server_value
    settings_manager.set_setting("ZFS_SERVERS", zfs_servers)
    _set_zfs_monitoring_state(server_name, bool(server_value["enabled"]))

    status_text = "включен" if server_value["enabled"] else "отключен"
    query.edit_message_text(
        f"✅ Мониторинг сервера `{server_name}` {status_text}.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_zfs_list"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def _delete_zfs_server_statuses(server_name: str) -> None:
    """Удалить статусы ZFS сервера из БД бэкапов."""
    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path:
        return

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM zfs_pool_status WHERE server_name = ?", (server_name,))
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
            "UPDATE zfs_pool_status SET server_name = ? WHERE server_name = ?", (new_name, old_name)
        )
        conn.commit()
    except Exception as exc:
        if "no such table: zfs_pool_status" not in str(exc):
            debug_logger(f"⚠️ Не удалось переименовать статусы ZFS сервера: {exc}")
    finally:
        conn.close()


def _ensure_zfs_monitoring_state_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS zfs_monitoring_state (
            server_name TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _get_zfs_monitoring_state_map() -> dict[str, bool]:
    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path:
        return {}

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        _ensure_zfs_monitoring_state_table(cursor)
        cursor.execute("SELECT server_name, enabled FROM zfs_monitoring_state")
        rows = cursor.fetchall()
        return {
            str(server_name): bool(int(enabled))
            for server_name, enabled in rows
            if str(server_name).strip()
        }
    except Exception as exc:
        debug_logger(f"⚠️ Не удалось прочитать zfs_monitoring_state: {exc}")
        return {}
    finally:
        conn.close()


def _set_zfs_monitoring_state(server_name: str, enabled: bool) -> None:
    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path or not str(server_name).strip():
        return

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        _ensure_zfs_monitoring_state_table(cursor)
        cursor.execute(
            """
            INSERT INTO zfs_monitoring_state (server_name, enabled, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(server_name)
            DO UPDATE SET enabled = excluded.enabled, updated_at = CURRENT_TIMESTAMP
            """,
            (server_name, 1 if enabled else 0),
        )
        conn.commit()
    except Exception as exc:
        debug_logger(f"⚠️ Не удалось сохранить состояние мониторинга ZFS: {exc}")
    finally:
        conn.close()


def _delete_zfs_monitoring_state(server_name: str) -> None:
    db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
    if not db_path or not str(server_name).strip():
        return

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        _ensure_zfs_monitoring_state_table(cursor)
        cursor.execute("DELETE FROM zfs_monitoring_state WHERE server_name = ?", (server_name,))
        conn.commit()
    except Exception as exc:
        debug_logger(f"⚠️ Не удалось удалить состояние мониторинга ZFS: {exc}")
    finally:
        conn.close()


def _rename_zfs_monitoring_state(old_name: str, new_name: str) -> None:
    if not old_name.strip() or not new_name.strip():
        return

    state_map = _get_zfs_monitoring_state_map()
    if old_name not in state_map:
        return

    _set_zfs_monitoring_state(new_name, state_map[old_name])
    _delete_zfs_monitoring_state(old_name)


def add_zfs_pattern_handler(update, context):
    """Добавить паттерн для ZFS"""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "zfs_input"
    context.user_data["backup_pattern_mode"] = "zfs_wizard"

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна ZFS*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя ZFS сервера из настроек.\n\n"
        "Пример темы:\n"
        "`ZFS alert zfs01: state: ONLINE, state: ONLINE`\n\n"
        "Пример фрагментов:\n"
        "`ZFS alert; zfs01; state:`",
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


def zfs_pattern_retry_handler(update, context):
    """Повторить ввод темы/фрагментов для паттерна ZFS."""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "zfs_input"
    context.user_data["backup_pattern_mode"] = "zfs_wizard"
    context.user_data.pop("backup_pattern_generated", None)
    context.user_data.pop("backup_pattern_source", None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна ZFS*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя ZFS сервера из настроек.",
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


def zfs_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна ZFS."""
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
            ("subject", pattern, "zfs"),
        )
        conn.commit()

        source_label = context.user_data.get("backup_pattern_source", "мастер")
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *zfs*\n"
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
