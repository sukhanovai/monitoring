"""
/bot/handlers/settings_handlers/auth.py
Server Monitoring System v8.62.62
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
SSH/Windows authentication UI settings (PR7f серии оптимизации).
Система мониторинга серверов
Версия: 8.62.62
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


def show_auth_settings(update, context):
    """Показать настройки аутентификации - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()

    ssh_username = settings_manager.get_setting("SSH_USERNAME", "root")
    ssh_key_path = settings_manager.get_setting("SSH_KEY_PATH", "/root/.ssh/id_rsa")

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
        [InlineKeyboardButton("👤 SSH аутентификация", callback_data="ssh_auth_settings")],
        [InlineKeyboardButton("🖥️ Windows аутентификация", callback_data="windows_auth_main")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_ssh_auth_settings(update, context):
    """Показать настройки SSH аутентификации"""
    query = update.callback_query
    query.answer()

    ssh_username = settings_manager.get_setting("SSH_USERNAME", "root")
    ssh_key_path = settings_manager.get_setting("SSH_KEY_PATH", "/root/.ssh/id_rsa")

    message = (
        "👤 *SSH аутентификация*\n\n"
        f"• SSH пользователь: `{ssh_username}`\n"
        f"• Путь к SSH ключу: `{ssh_key_path}`\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("👤 SSH пользователь", callback_data="set_ssh_username")],
        [InlineKeyboardButton("🔑 Путь к SSH ключу", callback_data="set_ssh_key_path")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_auth"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


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
        server_type = cred["server_type"]
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
        [
            InlineKeyboardButton(
                "👥 Просмотр всех учетных записей", callback_data="windows_auth_list"
            )
        ],
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data="windows_auth_add")],
        [InlineKeyboardButton("📊 Учетные данные по типам", callback_data="windows_auth_by_type")],
        [
            InlineKeyboardButton(
                "⚙️ Управление типами серверов", callback_data="windows_auth_manage_types"
            )
        ],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_auth"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


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
            status = "🟢" if cred["enabled"] else "🔴"
            message += f"{status} *{cred['server_type']}* (приоритет: {cred['priority']})\n"
            message += f"   Пользователь: `{cred['username']}`\n"
            message += f"   Пароль: `{'*' * 8}`\n"
            message += f"   ID: {cred['id']}\n\n"

    keyboard = [
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data="windows_auth_add")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="windows_auth_edit")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data="windows_auth_delete")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="windows_auth_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_windows_auth_add(update, context):
    """Показать форму добавления учетной записи Windows"""
    query = update.callback_query
    query.answer()

    # Начинаем процесс добавления
    context.user_data["adding_windows_cred"] = True
    context.user_data["cred_stage"] = "username"

    message = (
        "➕ *Добавление учетной записи Windows*\n\n"
        "Введите имя пользователя:\n\n"
        "_Пример: Administrator_"
    )

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_main")]]
        ),
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
                status = "🟢" if cred["enabled"] else "🔴"
                message += f"  {status} {cred['username']} (приоритет: {cred['priority']})\n"

            if len(credentials) > 3:
                message += f"  ... и еще {len(credentials) - 3} учетных записей\n"
            message += "\n"

    keyboard = [
        [InlineKeyboardButton("👥 Просмотр всех", callback_data="windows_auth_list")],
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data="windows_auth_add")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="windows_auth_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
            enabled_count = sum(1 for cred in credentials if cred["enabled"])
            message += (
                f"• *{server_type}*: {enabled_count}/{len(credentials)} активных учетных записей\n"
            )

    message += "\n*Доступные действия:*\n"
    message += "• *Переименовать тип* - изменить название типа серверов\n"
    message += "• *Объединить типы* - объединить два типа в один\n"
    message += "• *Удалить тип* - удалить тип (учетные записи сохранятся)\n"

    keyboard = []

    # Кнопки для каждого типа серверов
    for server_type in server_types:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {server_type}", callback_data=f"manage_type_edit_{server_type}"
                ),
                InlineKeyboardButton(
                    f"🔄 {server_type}", callback_data=f"manage_type_merge_{server_type}"
                ),
            ]
        )

    # Общие действия
    keyboard.extend(
        [
            [InlineKeyboardButton("➕ Создать новый тип", callback_data="manage_type_create")],
            [InlineKeyboardButton("🗑️ Удалить тип", callback_data="manage_type_delete")],
            [InlineKeyboardButton("📊 Статистика по типам", callback_data="manage_type_stats")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="windows_auth_main"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )
