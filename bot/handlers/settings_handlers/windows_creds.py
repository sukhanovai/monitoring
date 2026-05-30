"""
/bot/handlers/settings_handlers/windows_creds.py
Server Monitoring System v8.62.75
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Windows credentials input handler (PR7f серии оптимизации).
Система мониторинга серверов
Версия: 8.62.75
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


def handle_windows_credential_input(update, context):
    """Обработчик ввода данных учетной записи Windows"""
    if "adding_windows_cred" not in context.user_data:
        return

    user_input = update.message.text
    stage = context.user_data.get("cred_stage")

    try:
        if stage == "username":
            context.user_data["cred_username"] = user_input
            context.user_data["cred_stage"] = "password"

            update.message.reply_text(
                "🔒 Введите пароль:\n\n" "_Пароль будет сохранен в зашифрованном виде_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_main")]]
                ),
            )

        elif stage == "password":
            context.user_data["cred_password"] = user_input
            context.user_data["cred_stage"] = "server_type"

            # Предлагаем стандартные типы серверов
            keyboard = [
                [InlineKeyboardButton("🖥️ Windows 2025", callback_data="cred_type_windows_2025")],
                [
                    InlineKeyboardButton(
                        "🌐 Доменные серверы", callback_data="cred_type_domain_servers"
                    )
                ],
                [InlineKeyboardButton("🔧 Admin серверы", callback_data="cred_type_admin_servers")],
                [
                    InlineKeyboardButton(
                        "💻 Стандартные Windows", callback_data="cred_type_standard_windows"
                    )
                ],
                [InlineKeyboardButton("⚙️ Другой тип", callback_data="cred_type_custom")],
                [InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_main")],
            ]

            update.message.reply_text(
                "🖥️ Выберите тип серверов для этих учетных данных:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        elif stage == "server_type_custom":
            context.user_data["cred_server_type"] = user_input
            context.user_data["cred_stage"] = "priority"

            update.message.reply_text(
                "📊 Введите приоритет (число):\n\n"
                "_Учетные данные с более высоким приоритетом будут использоваться первыми_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_main")]]
                ),
            )

        elif stage == "priority":
            try:
                priority = int(user_input)
                context.user_data["cred_priority"] = priority

                # Сохраняем учетные данные
                username = context.user_data["cred_username"]
                password = context.user_data["cred_password"]
                server_type = context.user_data["cred_server_type"]

                success = settings_manager.add_windows_credential(
                    username, password, server_type, priority
                )

                if success:
                    # Очищаем контекст
                    for key in [
                        "adding_windows_cred",
                        "cred_stage",
                        "cred_username",
                        "cred_password",
                        "cred_server_type",
                        "cred_priority",
                    ]:
                        context.user_data.pop(key, None)

                    update.message.reply_text(
                        f"✅ *Учетная запись добавлена!*\n\n"
                        f"• Пользователь: `{username}`\n"
                        f"• Тип серверов: `{server_type}`\n"
                        f"• Приоритет: `{priority}`",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "➕ Добавить еще", callback_data="windows_auth_add"
                                    ),
                                    InlineKeyboardButton(
                                        "👥 Просмотр всех", callback_data="windows_auth_list"
                                    ),
                                ],
                                [
                                    InlineKeyboardButton(
                                        "↩️ Назад", callback_data="windows_auth_main"
                                    )
                                ],
                            ]
                        ),
                    )
                else:
                    update.message.reply_text("❌ Ошибка при сохранении учетных данных")

            except ValueError:
                update.message.reply_text("❌ Приоритет должен быть числом. Попробуйте снова:")

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
        # Сбрасываем состояние при ошибке
        context.user_data["adding_windows_cred"] = False


def handle_credential_type_selection(update, context):
    """Обработчик выбора типа сервера для учетных данных"""
    query = update.callback_query
    query.answer()

    if "adding_windows_cred" not in context.user_data:
        return

    cred_type = query.data.replace("cred_type_", "")

    type_mapping = {
        "windows_2025": "windows_2025",
        "domain_servers": "domain_servers",
        "admin_servers": "admin_servers",
        "standard_windows": "standard_windows",
    }

    if cred_type == "custom":
        context.user_data["cred_stage"] = "server_type_custom"
        query.edit_message_text(
            "✏️ Введите название типа серверов:\n\n" "_Пример: backup_servers, web_servers_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_main")]]
            ),
        )
    else:
        context.user_data["cred_server_type"] = type_mapping.get(cred_type, cred_type)
        context.user_data["cred_stage"] = "priority"

        query.edit_message_text(
            "📊 Введите приоритет (число):\n\n"
            "_Учетные данные с более высоким приоритетом будут использоваться первыми_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_main")]]
            ),
        )
