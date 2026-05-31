"""
/bot/handlers/settings_handlers/settings_value.py
Server Monitoring System v8.62.82
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчик текстового ввода значений настроек (PR11 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.82
Автор: Александр Суханов (c)
Лицензия: MIT
Выделено из bot/handlers/settings_handlers/_legacy.py. Имя
сохранено — фасад пакета через двусторонний re-export продолжает
его отдавать; внутренние ссылки в _legacy.py резолвятся через
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

from bot.handlers.settings_handlers.auth import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.db import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.mail import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.proxmox import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.snapshot import *  # noqa: F401, F403

# PR7b: supplier_stock-функции вынесены в одноимённый модуль пакета;
# реэкспортируем их сюда же, чтобы внутренние ссылки в _legacy.py
# (например, settings_callback_handler) продолжали работать.
from bot.handlers.settings_handlers.supplier_stock import *  # noqa: F401, F403
from bot.handlers.settings_handlers.windows_creds import *  # noqa: F401, F403
from bot.handlers.settings_handlers.zfs import *  # noqa: F401, F403
from bot.handlers.tls_cert_handlers import handle_text_input as handle_tls_text_input
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


def handle_setting_value(update, context):
    """Обработчик получения значения настройки - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    if handle_snapshot_host_text_input(update, context):
        return

    if handle_zfsp_text_input(update, context):
        return

    if handle_tls_text_input(update, context):
        return

    # Сначала проверяем, не добавляется ли Windows учетная запись
    if context.user_data.get("adding_windows_cred"):
        return handle_windows_credential_input(update, context)

    if (
        context.user_data.get("supplier_stock_edit")
        or context.user_data.get("supplier_stock_add_source")
        or context.user_data.get("supplier_stock_edit_source")
        or context.user_data.get("supplier_stock_source_field")
        or context.user_data.get("supplier_stock_source_iek_field")
        or context.user_data.get("supplier_stock_resource_add")
        or context.user_data.get("supplier_stock_resource_field")
        or context.user_data.get("supplier_stock_ftp_field")
        or context.user_data.get("supplier_stock_processing_add")
        or context.user_data.get("supplier_stock_processing_edit")
        or context.user_data.get("supplier_stock_processing_field")
        or context.user_data.get("supplier_stock_mail_edit")
        or context.user_data.get("supplier_stock_mail_add_source")
        or context.user_data.get("supplier_stock_mail_edit_source")
        or context.user_data.get("supplier_stock_mail_source_field")
    ):
        return supplier_stock_handle_input(update, context)

    # Проверяем, не создается ли тип серверов
    if context.user_data.get("creating_server_type"):
        return handle_server_type_creation(update, context)

    # Проверяем, не редактируется ли тип серверов
    if context.user_data.get("editing_server_type"):
        return handle_server_type_editing(update, context)

    # Проверяем, не редактируется ли сервер
    if context.user_data.get("editing_server"):
        return handle_server_edit_input(update, context)

    # Затем проверяем, не добавляется ли сервер
    if context.user_data.get("adding_server"):
        return handle_server_input(update, context)

    # Затем проверяем, не добавляется/редактируется ли категория БД
    if context.user_data.get("adding_db_category"):
        return handle_db_category_input(update, context)
    if context.user_data.get("editing_db_category"):
        return handle_db_category_rename_input(update, context)

    # Проверяем, не добавляется ли хост Proxmox
    if context.user_data.get("adding_proxmox_host"):
        return handle_proxmox_host_input(update, context)

    # Проверяем, не редактируется ли хост Proxmox
    if context.user_data.get("editing_proxmox_host"):
        return handle_proxmox_host_edit_input(update, context)

    # Проверяем, не добавляется ли ZFS сервер
    if context.user_data.get("adding_zfs_server"):
        return handle_zfs_server_input(update, context)

    # Проверяем, не редактируется ли имя ZFS сервера
    if context.user_data.get("editing_zfs_server_name"):
        return handle_zfs_server_name_edit_input(update, context)
    if context.user_data.get("editing_zfs_server_ip"):
        return handle_zfs_server_ip_edit_input(update, context)
    if context.user_data.get("editing_zfs_server_threshold"):
        return handle_zfs_server_threshold_edit_input(update, context)

    # Проверяем, не добавляется ли база данных
    if context.user_data.get("adding_db_entry"):
        return handle_db_entry_input(update, context)

    # Проверяем, не редактируется ли база данных
    if context.user_data.get("editing_db_entry"):
        return handle_db_entry_edit_input(update, context)

    # Проверяем, не добавляется ли паттерн бэкапов
    if context.user_data.get("adding_backup_pattern"):
        return handle_backup_pattern_input(update, context)

    # Проверяем, не редактируется ли паттерн бэкапов
    if context.user_data.get("editing_backup_pattern"):
        return handle_backup_pattern_edit_input(update, context)

    # Проверяем, не редактируется ли дефолтный паттерн БД
    if context.user_data.get("editing_default_db_pattern"):
        return handle_default_db_pattern_edit_input(update, context)

    # Добавление баз в игнор-список расширения «Передача бэкапов на NAS»
    if context.user_data.get("nas_add_ignore_base"):
        context.user_data.pop("nas_add_ignore_base", None)
        from extensions.backup_monitor.backup_handlers import add_nas_ignore_base_value

        return add_nas_ignore_base_value(update, update.message.text)

    # Если это обычная настройка
    if "editing_setting" not in context.user_data:
        return

    setting_key = context.user_data["editing_setting"]
    new_value = update.message.text

    try:
        # Определяем тип данных и преобразуем
        setting_types = {
            "check_interval": "int",
            "max_fail_time": "int",
            "silent_start": "int",
            "silent_end": "int",
            "cpu_warning": "int",
            "cpu_critical": "int",
            "ram_warning": "int",
            "ram_critical": "int",
            "disk_warning": "int",
            "disk_critical": "int",
            "web_port": "int",
            "backup_alert_hours": "int",
            "backup_stale_hours": "int",
            "windows_2025_timeout": "int",
            "domain_servers_timeout": "int",
            "admin_servers_timeout": "int",
            "standard_windows_timeout": "int",
            "linux_timeout": "int",
            "ping_timeout": "int",
        }

        if setting_key in {"silent_start", "silent_end"}:
            normalized = str(new_value).strip()
            if ":" in normalized:
                hour_part, minute_part = normalized.split(":", 1)
                if not minute_part.isdigit() or len(minute_part) != 2:
                    raise ValueError("Неверный формат времени. Используйте HH:MM")
                hour_value = int(hour_part)
                minute_value = int(minute_part)
                if not (0 <= hour_value <= 23 and 0 <= minute_value <= 59):
                    raise ValueError("Время должно быть в диапазоне 00:00-23:59")
                new_value = hour_value
            else:
                hour_value = int(normalized)
                if not (0 <= hour_value <= 23):
                    raise ValueError("Час должен быть в диапазоне 0-23")
                new_value = hour_value
        elif setting_key in setting_types and setting_types[setting_key] == "int":
            new_value = int(new_value)
        elif setting_key == "data_collection":
            # Проверяем и нормализуем список времен HH:MM,HH:MM
            normalized = str(new_value).strip()
            raw_points = [
                item.strip() for item in normalized.replace(";", ",").split(",") if item.strip()
            ]
            if not raw_points:
                raise ValueError("Укажите хотя бы одно время в формате HH:MM")
            normalized_points = []
            for point in raw_points:
                if not re.match(r"^\d{1,2}:\d{2}$", point):
                    raise ValueError("Неверный формат времени. Используйте HH:MM или HH:MM,HH:MM")
                hour_part, minute_part = point.split(":", 1)
                hour_value = int(hour_part)
                minute_value = int(minute_part)
                if not (0 <= hour_value <= 23 and 0 <= minute_value <= 59):
                    raise ValueError("Время должно быть в диапазоне 00:00-23:59")
                normalized_points.append(f"{hour_value:02d}:{minute_value:02d}")
            new_value = ",".join(sorted(set(normalized_points)))

        # Сохраняем настройку
        category_map = {
            "telegram_token": "telegram",
            "matrix_homeserver": "matrix",
            "matrix_access_token": "matrix",
            "matrix_room_id": "matrix",
            "matrix_bot_user_id": "matrix",
            "matrix_bot_password": "matrix",
            "matrix_store_path": "matrix",
            "check_interval": "monitoring",
            "max_fail_time": "monitoring",
            "silent_start": "time",
            "silent_end": "time",
            "data_collection": "time",
            "cpu_warning": "resources",
            "cpu_critical": "resources",
            "ram_warning": "resources",
            "ram_critical": "resources",
            "disk_warning": "resources",
            "disk_critical": "resources",
            "ssh_username": "auth",
            "ssh_key_path": "auth",
            "web_port": "web",
            "web_host": "web",
            "backup_alert_hours": "backup",
            "backup_stale_hours": "backup",
            "windows_2025_timeout": "timeouts",
            "domain_servers_timeout": "timeouts",
            "admin_servers_timeout": "timeouts",
            "standard_windows_timeout": "timeouts",
            "linux_timeout": "timeouts",
            "ping_timeout": "timeouts",
        }

        special_db_keys = {
            "telegram_token": "TELEGRAM_TOKEN",
            "matrix_homeserver": "MATRIX_HOMESERVER",
            "matrix_access_token": "MATRIX_ACCESS_TOKEN",
            "matrix_room_id": "MATRIX_ROOM_ID",
            "matrix_bot_user_id": "MATRIX_BOT_USER_ID",
            "matrix_bot_password": "MATRIX_BOT_PASSWORD",
            "matrix_store_path": "MATRIX_STORE_PATH",
            "data_collection": "DATA_COLLECTION_TIMES",
        }
        db_key = special_db_keys.get(setting_key, setting_key.upper())
        category = category_map.get(setting_key, "general")

        settings_manager.set_setting(db_key, new_value, category)

        # Подтягиваем обновленные значения из БД в runtime-конфиг,
        # чтобы цикл мониторинга сразу увидел новое время отчета.
        load_all_settings()
        if db_key == "DATA_COLLECTION_TIMES":
            settings_manager.set_setting(
                "DATA_COLLECTION_TIME", new_value.split(",")[0], category="time"
            )
            debug_log(f"🕒 Обновлено расписание сбора данных для утреннего отчета: {new_value}")

        # Очищаем контекст
        del context.user_data["editing_setting"]
        prompt_message_id = context.user_data.pop("editing_setting_message_id", None)
        prompt_chat_id = context.user_data.pop("editing_setting_chat_id", None)
        if prompt_message_id and prompt_chat_id:
            try:
                context.bot.delete_message(chat_id=prompt_chat_id, message_id=prompt_message_id)
            except Exception:
                pass

        update.message.reply_text(
            f"✅ Настройка {db_key} успешно обновлена!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚙️ Вернуться к настройкам", callback_data="settings_main")]]
            ),
        )

    except ValueError as e:
        update.message.reply_text(f"❌ Ошибка: {e}\nПопробуйте еще раз:")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка сохранения: {e}")
