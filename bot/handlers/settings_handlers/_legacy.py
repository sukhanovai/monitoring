"""
/bot/handlers/settings_handlers.py
Server Monitoring System v8.62.83
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for managing settings via a bot
Система мониторинга серверов
Версия: 8.62.83
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики для управления настройками через бота
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
from bot.handlers.settings_handlers.callback_dispatcher import *  # noqa: F401, F403
from bot.handlers.settings_handlers.settings_value import *  # noqa: F401, F403

# PR7b: supplier_stock-функции вынесены в одноимённый модуль пакета;
# реэкспортируем их сюда же, чтобы внутренние ссылки в _legacy.py
# (например, settings_callback_handler) продолжали работать.
from bot.handlers.settings_handlers.supplier_stock import *  # noqa: F401, F403
from bot.handlers.settings_handlers.windows_creds import *  # noqa: F401, F403
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


def _safe_query_answer(query, text: str | None = None, **kwargs) -> None:
    try:
        if text is None:
            query.answer(**kwargs)
        else:
            query.answer(text, **kwargs)
    except (BadRequest, TelegramError):
        pass


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


def _get_backup_patterns_setting() -> dict:
    """Получить полные паттерны из настроек."""
    raw_patterns = settings_manager.get_setting("BACKUP_PATTERNS", DEFAULT_BACKUP_PATTERNS)
    if isinstance(raw_patterns, str):
        try:
            raw_patterns = json.loads(raw_patterns)
        except json.JSONDecodeError:
            raw_patterns = {}
    if not isinstance(raw_patterns, dict):
        return {}
    return raw_patterns


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

    replaced = re.sub(re.escape(matched), "__SERVER__", text, flags=re.IGNORECASE)
    return replaced, True


def settings_command(update, context):
    """Команда управления настройками"""
    keyboard = [
        [InlineKeyboardButton("🤖 Настройки Telegram", callback_data="settings_telegram")],
        [InlineKeyboardButton("🟦 Настройки Matrix", callback_data="settings_matrix")],
        [InlineKeyboardButton("⏰ Временные настройки", callback_data="settings_time")],
        [InlineKeyboardButton("🔧 Мониторинг", callback_data="settings_monitoring")],
    ]

    keyboard.extend(
        [
            [InlineKeyboardButton("🔐 Аутентификация", callback_data="settings_auth")],
            [InlineKeyboardButton("🖥️ Серверы", callback_data="settings_servers")],
        ]
    )

    keyboard.append([InlineKeyboardButton("🧩 Расширения", callback_data="settings_extensions")])

    if extension_manager.is_extension_enabled("web_interface"):
        keyboard.append([InlineKeyboardButton("🌐 Веб-интерфейс", callback_data="settings_web")])

    keyboard.extend(
        [
            [
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ]
        ]
    )

    if update.message:
        update.message.reply_text(
            "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        update.callback_query.edit_message_text(
            "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


def show_telegram_settings(update, context):
    """Показать настройки Telegram - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()

    token = settings_manager.get_setting("TELEGRAM_TOKEN", "")
    chat_ids = settings_manager.get_setting("CHAT_IDS", [])

    token_display = "🟢 Установлен" if token else "🔴 Не установлен"
    chats_display = f"{len(chat_ids)} чатов" if chat_ids else "🔴 Не настроены"

    message = (
        "🤖 *Настройки Telegram*\n\n"
        f"• Токен бота: {token_display}\n"
        f"• ID чатов: {chats_display}\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("🔑 Установить токен", callback_data="set_telegram_token")],
        [InlineKeyboardButton("💬 Управление чатами", callback_data="manage_chats")],
        [InlineKeyboardButton("🧪 Тест Telegram", callback_data="test_alert_telegram")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_matrix_settings(update, context):
    """Показать настройки Matrix"""
    query = update.callback_query
    query.answer()

    homeserver = settings_manager.get_setting("MATRIX_HOMESERVER", "")
    access_token = settings_manager.get_setting("MATRIX_ACCESS_TOKEN", "")
    room_id = settings_manager.get_setting("MATRIX_ROOM_ID", "")
    bot_user_id = settings_manager.get_setting("MATRIX_BOT_USER_ID", "")
    bot_password = settings_manager.get_setting("MATRIX_BOT_PASSWORD", "")
    store_path = settings_manager.get_setting("MATRIX_STORE_PATH", "")

    def _mono(value):
        # Значения могут содержать _ * ` [ — в legacy-Markdown это ломает
        # парсинг entity, поэтому выводим как inline-code (внутри backticks
        # спецсимволы литеральны), убирая сами backticks из значения.
        return "`" + str(value).replace("`", "'") + "`"

    homeserver_display = _mono(homeserver) if homeserver else "🔴 Не настроен"
    token_display = "🟢 Установлен" if access_token else "🔴 Не установлен"
    room_display = _mono(room_id) if room_id else "🔴 Не настроена"
    bot_user_display = _mono(bot_user_id) if bot_user_id else "🔴 Не задан"
    bot_pass_display = "🟢 Установлен" if bot_password else "🔴 Не установлен"
    store_display = _mono(store_path) if store_path else "по умолчанию (`data/matrix_store`)"
    e2ee_display = (
        "🟢 включится (есть user+password)"
        if (bot_user_id and bot_password)
        else "🔴 выкл (нужны user ID и пароль)"
    )

    message = (
        "🟦 *Настройки Matrix*\n\n"
        f"• Homeserver: {homeserver_display}\n"
        f"• Access token: {token_display}\n"
        f"• Room ID: {room_display}\n\n"
        "*E2EE (зашифрованные комнаты)*\n"
        f"• Bot user ID: {bot_user_display}\n"
        f"• Bot password: {bot_pass_display}\n"
        f"• Store path: {store_display}\n"
        f"• Статус E2EE: {e2ee_display}\n\n"
        "Без user ID + пароля команды читаются только из *НЕ*зашифрованных "
        "комнат. Изменения применяются после перезапуска сервиса.\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("🌐 Установить homeserver", callback_data="set_matrix_homeserver")],
        [
            InlineKeyboardButton(
                "🔑 Установить access token", callback_data="set_matrix_access_token"
            )
        ],
        [InlineKeyboardButton("💬 Установить room ID", callback_data="set_matrix_room_id")],
        [
            InlineKeyboardButton(
                "👤 Установить bot user ID (E2EE)", callback_data="set_matrix_bot_user_id"
            )
        ],
        [
            InlineKeyboardButton(
                "🔐 Установить bot password (E2EE)", callback_data="set_matrix_bot_password"
            )
        ],
        [
            InlineKeyboardButton(
                "📁 Установить store path (опц.)", callback_data="set_matrix_store_path"
            )
        ],
        [InlineKeyboardButton("🧪 Тест Matrix", callback_data="test_alert_matrix")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_monitoring_settings(update, context):
    """Показать настройки мониторинга - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()

    check_interval = settings_manager.get_setting("CHECK_INTERVAL", 60)
    max_fail_time = settings_manager.get_setting("MAX_FAIL_TIME", 900)

    # Новые настройки таймаутов
    windows_2025_timeout = settings_manager.get_setting("WINDOWS_2025_TIMEOUT", 35)
    domain_timeout = settings_manager.get_setting("DOMAIN_SERVERS_TIMEOUT", 20)
    admin_timeout = settings_manager.get_setting("ADMIN_SERVERS_TIMEOUT", 25)
    standard_timeout = settings_manager.get_setting("STANDARD_WINDOWS_TIMEOUT", 30)
    linux_timeout = settings_manager.get_setting("LINUX_TIMEOUT", 15)

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
        [InlineKeyboardButton("⏱️ Интервал проверки", callback_data="set_check_interval")],
        [InlineKeyboardButton("🚨 Макс. время простоя", callback_data="set_max_fail_time")],
        [InlineKeyboardButton("⏰ Таймауты серверов", callback_data="server_timeouts")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_time_settings(update, context):
    """Показать временные настройки"""
    query = update.callback_query
    query.answer()

    silent_start = settings_manager.get_setting("SILENT_START", 20)
    silent_end = settings_manager.get_setting("SILENT_END", 9)
    data_collection = settings_manager.get_setting(
        "DATA_COLLECTION_TIMES", settings_manager.get_setting("DATA_COLLECTION_TIME", "08:30")
    )

    message = (
        "⏰ *Временные настройки*\n\n"
        f"• Тихий режим: {silent_start}:00 - {silent_end}:00\n"
        f"• Сбор данных: {data_collection}\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("🔇 Начало тихого режима", callback_data="set_silent_start")],
        [InlineKeyboardButton("🔊 Конец тихого режима", callback_data="set_silent_end")],
        [InlineKeyboardButton("📊 Время(а) сбора данных", callback_data="set_data_collection")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_resource_settings(update, context):
    """Показать настройки ресурсов"""
    query = update.callback_query
    query.answer()

    cpu_warning = settings_manager.get_setting("CPU_WARNING", 80)
    cpu_critical = settings_manager.get_setting("CPU_CRITICAL", 90)
    ram_warning = settings_manager.get_setting("RAM_WARNING", 85)
    ram_critical = settings_manager.get_setting("RAM_CRITICAL", 95)
    disk_warning = settings_manager.get_setting("DISK_WARNING", 80)
    disk_critical = settings_manager.get_setting("DISK_CRITICAL", 90)

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
        [InlineKeyboardButton("💻 CPU предупреждение", callback_data="set_cpu_warning")],
        [InlineKeyboardButton("💻 CPU критический", callback_data="set_cpu_critical")],
        [InlineKeyboardButton("🧠 RAM предупреждение", callback_data="set_ram_warning")],
        [InlineKeyboardButton("🧠 RAM критический", callback_data="set_ram_critical")],
        [InlineKeyboardButton("💾 Disk предупреждение", callback_data="set_disk_warning")],
        [InlineKeyboardButton("💾 Disk критический", callback_data="set_disk_critical")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="check_resources"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_backup_settings(update, context):
    """Показать настройки бэкапов - С ИЗМЕНЕННЫМ CALLBACK"""
    query = update.callback_query
    query.answer()

    backup_alert_hours = settings_manager.get_setting("BACKUP_ALERT_HOURS", 24)
    backup_stale_hours = settings_manager.get_setting("BACKUP_STALE_HOURS", 36)

    database_config = settings_manager.get_setting("DATABASE_CONFIG", {})
    db_categories = list(database_config.keys()) if database_config else []
    proxmox_hosts = settings_manager.get_setting("PROXMOX_HOSTS", {})
    proxmox_count = len(proxmox_hosts) if isinstance(proxmox_hosts, dict) else 0
    zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
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
        [InlineKeyboardButton("⏰ Временные интервалы", callback_data="backup_times")],
    ]

    if extension_manager.is_extension_enabled("backup_monitor"):
        keyboard.append(
            [InlineKeyboardButton("🖥️ Proxmox бэкапы", callback_data="settings_backup_proxmox")]
        )
        keyboard.append(
            [InlineKeyboardButton("🖥️ Паттерны Proxmox", callback_data="settings_patterns_proxmox")]
        )

    if extension_manager.is_extension_enabled("database_backup_monitor"):
        keyboard.append([InlineKeyboardButton("🗃️ Базы данных", callback_data="settings_db_main")])
        keyboard.append(
            [InlineKeyboardButton("🗃️ Паттерны БД", callback_data="settings_patterns_db")]
        )

    if extension_manager.is_extension_enabled("zfs_monitor"):
        keyboard.append([InlineKeyboardButton("🧊 ZFS", callback_data="settings_zfs")])

    keyboard.extend(
        [
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_all_settings(update, context):
    """Показать все настройки"""
    query = update.callback_query
    query.answer()

    all_settings = settings_manager.get_all_settings()

    message = "📊 *Все настройки системы*\n\n"

    for category in settings_manager.get_categories():
        message += f"*{category.upper()}:*\n"
        category_settings = {
            k: v
            for k, v in all_settings.items()
            if k.lower().startswith(category.lower())
            or settings_manager.get_setting(k, category="") == category
        }

        for key, value in category_settings.items():
            if key == "TELEGRAM_TOKEN" and value:
                value = "***" + value[-4:]  # Показываем только последние 4 символа
            elif key == "CHAT_IDS":
                value = f"{len(value)} чатов"
            elif isinstance(value, (list, dict)):
                value = f"{len(value)} элементов"

            message += f"• {key}: {value}\n"
        message += "\n"

    keyboard = [
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data="settings_main")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


_SETTING_KEY_TO_DB_KEY = {
    "check_interval": "CHECK_INTERVAL",
    "max_fail_time": "MAX_FAIL_TIME",
    "silent_start": "SILENT_START",
    "silent_end": "SILENT_END",
    "data_collection": "DATA_COLLECTION_TIMES",
    "cpu_warning": "CPU_WARNING",
    "cpu_critical": "CPU_CRITICAL",
    "ram_warning": "RAM_WARNING",
    "ram_critical": "RAM_CRITICAL",
    "disk_warning": "DISK_WARNING",
    "disk_critical": "DISK_CRITICAL",
    "ssh_username": "SSH_USERNAME",
    "ssh_key_path": "SSH_KEY_PATH",
    "web_port": "WEB_PORT",
    "web_host": "WEB_HOST",
    "backup_alert_hours": "BACKUP_ALERT_HOURS",
    "backup_stale_hours": "BACKUP_STALE_HOURS",
    "windows_2025_timeout": "WINDOWS_2025_TIMEOUT",
    "domain_servers_timeout": "DOMAIN_SERVERS_TIMEOUT",
    "admin_servers_timeout": "ADMIN_SERVERS_TIMEOUT",
    "standard_windows_timeout": "STANDARD_WINDOWS_TIMEOUT",
    "linux_timeout": "LINUX_TIMEOUT",
    "ping_timeout": "PING_TIMEOUT",
}


def _format_current_setting_value(setting_key: str) -> str:
    """Возвращает строку «Текущее значение: ...» для подсказок ввода.

    Берём значение через settings_manager по тому же ключу БД, который
    показывают экраны выбора параметра, чтобы пользователь видел, от какого
    значения отталкиваться при вводе нового.
    """
    db_key = _SETTING_KEY_TO_DB_KEY.get(setting_key)
    if not db_key:
        return ""
    try:
        value = settings_manager.get_setting(db_key)
    except Exception as exc:  # noqa: BLE001
        debug_logger(f"⚠️ Не удалось получить текущее значение {db_key}: {exc}")
        return ""
    if value is None or value == "" or value == {} or value == []:
        return ""
    return f"📍 Текущее значение: {value}"


def handle_setting_input(update, context, setting_key):
    """Обработчик ввода значений настроек - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()

    # Сохраняем какое настройку меняем
    context.user_data["editing_setting"] = setting_key
    context.user_data["editing_setting_message_id"] = query.message.message_id
    context.user_data["editing_setting_chat_id"] = query.message.chat_id

    setting_descriptions = {
        # Существующие настройки...
        "telegram_token": "Введите новый токен Telegram бота:",
        "matrix_homeserver": "Введите URL Matrix homeserver (например https://matrix.example.com):",
        "matrix_access_token": "Введите Matrix access token:",
        "matrix_room_id": "Введите Matrix room ID (например !roomid:example.com):",
        "matrix_bot_user_id": "Введите полный MXID бота для E2EE (например @comdone:matrix.202020.ru):",
        "matrix_bot_password": "Введите пароль аккаунта Matrix-бота (для E2EE-логина):",
        "matrix_store_path": "Введите путь к persistent crypto-store (пусто = data/matrix_store):",
        "check_interval": "Введите новый интервал проверки (в секундах):",
        "max_fail_time": "Введите максимальное время простоя (в секундах):",
        "silent_start": "Введите час начала тихого режима (0-23):",
        "silent_end": "Введите час окончания тихого режима (0-23):",
        "data_collection": "Введите время сбора данных (формат HH:MM):",
        "cpu_warning": "Введите порог предупреждения для CPU (%):",
        "cpu_critical": "Введите критический порог для CPU (%):",
        "ram_warning": "Введите порог предупреждения для RAM (%):",
        "ram_critical": "Введите критический порог для RAM (%):",
        "disk_warning": "Введите порог предупреждения для Disk (%):",
        "disk_critical": "Введите критический порог для Disk (%):",
        "ssh_username": "Введите имя пользователя SSH:",
        "ssh_key_path": "Введите путь к SSH ключу:",
        "web_port": "Введите порт веб-интерфейса:",
        "web_host": "Введите хост веб-интерфейса:",
        "backup_alert_hours": "Введите количество часов для алертов о бэкапах:",
        "backup_stale_hours": "Введите количество часов для устаревших бэкапов:",
        # Новые таймауты серверов
        "windows_2025_timeout": "Введите таймаут для Windows 2025 серверов (в секундах):",
        "domain_servers_timeout": "Введите таймаут для доменных серверов (в секундах):",
        "admin_servers_timeout": "Введите таймаут для Admin серверов (в секундах):",
        "standard_windows_timeout": "Введите таймаут для стандартных Windows серверов (в секундах):",
        "linux_timeout": "Введите таймаут для Linux серверов (в секундах):",
        "ping_timeout": "Введите таймаут для Ping серверов (в секундах):",
    }

    message = setting_descriptions.get(setting_key, f"Введите новое значение для {setting_key}:")

    current_value_hint = _format_current_setting_value(setting_key)
    if current_value_hint:
        message = f"{current_value_hint}\n\n{message}"

    cancel_callback = "settings_main"
    if setting_key in {
        "cpu_warning",
        "cpu_critical",
        "ram_warning",
        "ram_critical",
        "disk_warning",
        "disk_critical",
    }:
        cancel_callback = "settings_resources"
    elif setting_key in {
        "windows_2025_timeout",
        "domain_servers_timeout",
        "admin_servers_timeout",
        "standard_windows_timeout",
        "linux_timeout",
        "ping_timeout",
    }:
        cancel_callback = "server_timeouts"
    elif setting_key in {"check_interval", "max_fail_time"}:
        cancel_callback = "settings_monitoring"
    elif setting_key in {"silent_start", "silent_end", "data_collection"}:
        cancel_callback = "settings_time"

    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data=cancel_callback)]]
        ),
    )


def set_setting_handler(update, context, setting_key):
    """Совместимость для callback'ов с полными ключами настроек."""
    key_map = {
        "SNAPSHOT_TRANSFER_HOSTS": "snapshot_transfer_hosts",
        "BACKUP_START_TIME": "backup_start_time",
    }
    normalized_key = key_map.get(setting_key, str(setting_key or "").lower())
    handle_setting_input(update, context, normalized_key)


def show_web_settings(update, context):
    """Показать настройки веб-интерфейса - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()

    web_port = settings_manager.get_setting("WEB_PORT", 5000)
    web_host = settings_manager.get_setting("WEB_HOST", "0.0.0.0")

    message = (
        "🌐 *Настройки веб-интерфейса*\n\n"
        f"• Порт: {web_port}\n"
        f"• Хост: {web_host}\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("🔌 Порт веб-интерфейса", callback_data="set_web_port")],
        [InlineKeyboardButton("🌐 Хост веб-интерфейса", callback_data="set_web_host")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def get_settings_handlers():
    """Получить обработчики для настроек"""
    return [
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(settings_callback_handler, pattern="^settings_"),
        CallbackQueryHandler(settings_callback_handler, pattern="^set_"),
        CallbackQueryHandler(settings_callback_handler, pattern="^backup_"),
        CallbackQueryHandler(settings_callback_handler, pattern="^manage_"),
        MessageHandler(Filters.text & ~Filters.command, handle_setting_value),
    ]


def show_servers_settings(update, context):
    """Показать настройки серверов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)
    enabled_servers = [s for s in servers if s.get("enabled", True)]
    paused_servers = [s for s in servers if not s.get("enabled", True)]
    windows_servers = [s for s in servers if s["type"] == "rdp"]
    linux_servers = [s for s in servers if s["type"] == "ssh"]
    ping_servers = [s for s in servers if s["type"] == "ping"]

    # Сбрасываем состояния редактирования, если вернулись в меню
    context.user_data.pop("adding_server", None)
    context.user_data.pop("editing_server", None)
    context.user_data.pop("server_stage", None)
    context.user_data.pop("edit_server_stage", None)
    context.user_data.pop("edit_server_ip", None)
    context.user_data.pop("edit_server_data", None)

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
        [InlineKeyboardButton("📋 Список серверов", callback_data="settings_servers_list")],
        [InlineKeyboardButton("➕ Добавить сервер", callback_data="settings_add_server")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _get_server_by_ip(servers, ip):
    """Найти сервер по IP из списка"""
    for server in servers:
        if server.get("ip") == ip:
            return server
    return None


def show_servers_list(update, context):
    """Показать список серверов с действиями"""
    query = update.callback_query
    query.answer()

    servers = settings_manager.get_all_servers(include_disabled=True)

    # Сбрасываем состояния редактирования при показе списка
    context.user_data.pop("editing_server", None)
    context.user_data.pop("edit_server_stage", None)
    context.user_data.pop("edit_server_ip", None)
    context.user_data.pop("edit_server_data", None)

    if not servers:
        message = "📋 *Список серверов*\n\n❌ Серверы не настроены."
        keyboard = [
            [InlineKeyboardButton("➕ Добавить сервер", callback_data="settings_add_server")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="settings_servers"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
        query.edit_message_text(
            message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    message_lines = ["📋 *Список серверов*\n"]
    for server in servers:
        status_icon = "🟢" if server.get("enabled", True) else "⏸️"
        status_text = "мониторинг" if server.get("enabled", True) else "пауза"
        message_lines.append(
            f"• {status_icon} {server['name']} (`{server['ip']}`) — {server['type'].upper()} — {status_text}"
        )

    keyboard = [
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_servers"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    ]
    for server in servers:
        toggle_text = "⏸️ Пауза" if server.get("enabled", True) else "▶️ Возобновить"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {server['name']}", callback_data=f"settings_edit_server_{server['ip']}"
                ),
                InlineKeyboardButton(
                    toggle_text, callback_data=f"settings_toggle_server_{server['ip']}"
                ),
                InlineKeyboardButton("🗑️", callback_data=f"settings_delete_server_{server['ip']}"),
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("➕ Добавить сервер", callback_data="settings_add_server")]
    )
    query.edit_message_text(
        "\n".join(message_lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    message = (
        "🗑️ *Удаление сервера*\n\n"
        f"Сервер: *{server['name']}* (`{server['ip']}`)\n"
        "Подтвердите удаление:"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Удалить", callback_data=f"settings_confirm_delete_server_{ip}")],
        [InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад к списку", callback_data="settings_servers_list")]]
        ),
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    status_text = "🟢 Включен" if server.get("enabled", True) else "⏸️ Приостановлен"
    message = (
        "✏️ *Редактирование сервера*\n\n"
        f"• Имя: *{server['name']}*\n"
        f"• IP: `{server['ip']}`\n"
        f"• Тип: *{server['type'].upper()}*\n\n"
        f"• Статус: *{status_text}*\n\n"
        "Выберите действие:"
    )

    toggle_text = (
        "⏸️ Приостановить мониторинг" if server.get("enabled", True) else "▶️ Возобновить мониторинг"
    )
    keyboard = [
        [InlineKeyboardButton("📝 Изменить имя", callback_data=f"settings_edit_server_name_{ip}")],
        [InlineKeyboardButton("🔧 Изменить тип", callback_data=f"settings_edit_server_type_{ip}")],
        [InlineKeyboardButton(toggle_text, callback_data=f"settings_toggle_server_{ip}")],
        [InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    new_status = not server.get("enabled", True)
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
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад к списку", callback_data="settings_servers_list")]]
        ),
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    context.user_data["editing_server"] = True
    context.user_data["edit_server_stage"] = "name"
    context.user_data["edit_server_ip"] = ip
    context.user_data["edit_server_data"] = server

    query.edit_message_text(
        "📝 Введите новое имя сервера:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="settings_servers_list")]]
        ),
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
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    context.user_data["editing_server"] = True
    context.user_data["edit_server_stage"] = "type"
    context.user_data["edit_server_ip"] = ip
    context.user_data["edit_server_data"] = server

    keyboard = [
        [
            InlineKeyboardButton(
                "🖥️ Windows (RDP)", callback_data=f"settings_edit_server_type_select_rdp_{ip}"
            )
        ],
        [
            InlineKeyboardButton(
                "🐧 Linux (SSH)", callback_data=f"settings_edit_server_type_select_ssh_{ip}"
            )
        ],
        [
            InlineKeyboardButton(
                "📡 Ping Only", callback_data=f"settings_edit_server_type_select_ping_{ip}"
            )
        ],
        [InlineKeyboardButton("❌ Отмена", callback_data="settings_servers_list")],
    ]

    query.edit_message_text(
        "🔧 Выберите новый тип сервера:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def handle_server_type_selection(update, context):
    """Обработчик выбора нового типа сервера"""
    query = update.callback_query
    query.answer()

    if not context.user_data.get("editing_server"):
        return

    data = query.data.replace("settings_edit_server_type_select_", "")
    parts = data.split("_")
    if len(parts) < 2:
        query.edit_message_text(
            "❌ Неверный формат выбора типа.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    server_type = parts[0]
    ip = "_".join(parts[1:])
    server = context.user_data.get("edit_server_data") or {}
    if server.get("ip") != ip:
        servers = settings_manager.get_all_servers(include_disabled=True)
        server = _get_server_by_ip(servers, ip)

    if not server:
        query.edit_message_text(
            "❌ Сервер не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_servers_list")]]
            ),
        )
        return

    success = settings_manager.add_server(
        ip,
        server.get("name", ip),
        server_type,
        server.get("credentials"),
        server.get("timeout", 30),
        server.get("enabled", True),
    )

    context.user_data.pop("editing_server", None)
    context.user_data.pop("edit_server_stage", None)
    context.user_data.pop("edit_server_ip", None)
    context.user_data.pop("edit_server_data", None)

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
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад к списку", callback_data="settings_servers_list")]]
        ),
    )


def handle_server_edit_input(update, context):
    """Обработчик ввода для редактирования сервера"""
    if not context.user_data.get("editing_server"):
        return

    stage = context.user_data.get("edit_server_stage")
    if stage != "name":
        return

    new_name = update.message.text.strip()
    if not new_name:
        update.message.reply_text("❌ Имя не может быть пустым. Попробуйте снова:")
        return

    server = context.user_data.get("edit_server_data") or {}
    ip = context.user_data.get("edit_server_ip")
    if not ip:
        update.message.reply_text("❌ Не удалось определить сервер.")
        return

    success = settings_manager.add_server(
        ip,
        new_name,
        server.get("type", "ping"),
        server.get("credentials"),
        server.get("timeout", 30),
        server.get("enabled", True),
    )

    context.user_data.pop("editing_server", None)
    context.user_data.pop("edit_server_stage", None)
    context.user_data.pop("edit_server_ip", None)
    context.user_data.pop("edit_server_data", None)

    if success:
        message = "✅ Имя сервера обновлено.\n\n" f"• IP: `{ip}`\n" f"• Новое имя: *{new_name}*"
    else:
        message = "❌ Не удалось обновить имя сервера."

    update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад к списку", callback_data="settings_servers_list")]]
        ),
    )


def show_backup_times(update, context):
    """Показать настройки временных интервалов бэкапов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()

    alert_hours = settings_manager.get_setting("BACKUP_ALERT_HOURS", 24)
    stale_hours = settings_manager.get_setting("BACKUP_STALE_HOURS", 36)

    message = (
        "⏰ *Временные интервалы бэкапов*\n\n"
        f"• Алерты через: {alert_hours} часов\n"
        f"• Устаревание через: {stale_hours} часов\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("🚨 Часы для алертов", callback_data="set_backup_alert_hours")],
        [InlineKeyboardButton("📅 Часы для устаревания", callback_data="set_backup_stale_hours")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_backup"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_settings_extensions_menu(update, context):
    """Показать меню расширений в настройках"""
    query = update.callback_query
    query.answer()

    message = "🧩 *Расширения*\n\nВыберите раздел:"

    keyboard = []

    if extension_manager.is_extension_enabled("stock_load_monitor"):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📦 Загрузка остатков 1С", callback_data="settings_ext_stock_load"
                )
            ]
        )

    if extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📦 Остатки поставщиков", callback_data="settings_ext_supplier_stock"
                )
            ]
        )

    keyboard.extend(
        [
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
        enabled = status_info["enabled"]
        ext_info = status_info["info"]

        status_icon = "🟢" if enabled else "🔴"
        toggle_text = "🔴 Выключить" if enabled else "🟢 Включить"

        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   Статус: {'Включено' if enabled else 'Отключено'}\n\n"

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{toggle_text} {ext_info['name']}",
                    callback_data=f"settings_ext_toggle_{ext_id}",
                )
            ]
        )

    keyboard.extend(
        [
            [InlineKeyboardButton("📊 Включить все", callback_data="settings_ext_enable_all")],
            [InlineKeyboardButton("📋 Отключить все", callback_data="settings_ext_disable_all")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="settings_extensions"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text(
        text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
    edit_id = context.user_data.get("supplier_stock_processing_rule_edit_id") or data.get("id")
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
    return True


def _persist_processing_rule_data(context) -> None:
    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    source_id = context.user_data.get("supplier_stock_processing_source_id")
    if source_id:
        data["source_id"] = source_id
    _fill_processing_rule_from_source(data)
    edit_id = context.user_data.get("supplier_stock_processing_rule_edit_id") or data.get("id")
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id, keep_context=True)
    if not edit_id:
        context.user_data["supplier_stock_processing_rule_edit_id"] = data.get("id")
        context.user_data["supplier_stock_processing_rule_add"] = False
    elif data.get("id"):
        context.user_data["supplier_stock_processing_rule_edit_id"] = data.get("id")
    context.user_data["supplier_stock_processing_rule_data"] = data


def _show_processing_rule_back_menu(update, context, back_callback: str) -> None:
    if back_callback == "settings_ext_supplier_stock":
        show_supplier_stock_settings(update, context)
        return
    if back_callback == "supplier_stock_processing":
        show_supplier_stock_processing_menu(
            update, context, action_prefix="supplier_stock_processing"
        )
        return
    if back_callback.startswith("supplier_stock_source_settings|"):
        source_id = back_callback.split("|", 1)[1]
        show_supplier_stock_source_settings(update, context, source_id)
        return
    if back_callback.startswith("supplier_stock_mail_source_settings|"):
        source_id = back_callback.split("|", 1)[1]
        show_supplier_stock_mail_source_settings(update, context, source_id)
        return

    update.callback_query.edit_message_text(
        "✅ Настройки сохранены.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
        ),
    )


def _parse_yes_no(value: str) -> bool | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in ("да", "yes", "y", "true", "1"):
        return True
    if lowered in ("нет", "no", "n", "false", "0"):
        return False
    return None


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


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


def manage_chats_handler(update, context):
    """Управление чатами - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ КНОПКИ СПИСКА ВСЕХ ЧАТОВ"""
    query = update.callback_query
    query.answer()

    chat_ids = settings_manager.get_setting("CHAT_IDS", [])

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
        [InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")],
        [InlineKeyboardButton("🗑️ Удалить чат", callback_data="remove_chat")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_telegram"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_server_timeouts(update, context):
    """Таймауты серверов с текущими значениями.

    Раньше функция читала только агрегированный словарь SERVER_TIMEOUTS из БД
    и при его отсутствии показывала надпись «не настроены» с захардкоженными
    значениями, что выглядело как «меню не открылось» и расходилось со
    значениями, которые правятся ниже через кнопки. Теперь читаем те же
    индивидуальные ключи, которые меняются из этого меню, чтобы экран всегда
    отражал реально применяемые таймауты.
    """
    query = update.callback_query
    query.answer()

    windows_2025_timeout = settings_manager.get_setting("WINDOWS_2025_TIMEOUT", 35)
    domain_timeout = settings_manager.get_setting("DOMAIN_SERVERS_TIMEOUT", 20)
    admin_timeout = settings_manager.get_setting("ADMIN_SERVERS_TIMEOUT", 25)
    standard_timeout = settings_manager.get_setting("STANDARD_WINDOWS_TIMEOUT", 30)
    linux_timeout = settings_manager.get_setting("LINUX_TIMEOUT", 15)
    ping_timeout = settings_manager.get_setting("PING_TIMEOUT", 10)

    message = (
        "⏰ *Таймауты серверов*\n\n"
        f"• Windows 2025: {windows_2025_timeout} сек\n"
        f"• Доменные серверы: {domain_timeout} сек\n"
        f"• Admin серверы: {admin_timeout} сек\n"
        f"• Стандартные Windows: {standard_timeout} сек\n"
        f"• Linux серверы: {linux_timeout} сек\n"
        f"• Ping серверы: {ping_timeout} сек\n\n"
        "Выберите параметр для изменения:"
    )

    keyboard = [
        [InlineKeyboardButton("🖥️ Windows 2025", callback_data="set_windows_2025_timeout")],
        [InlineKeyboardButton("🌐 Доменные серверы", callback_data="set_domain_servers_timeout")],
        [InlineKeyboardButton("🔧 Admin серверы", callback_data="set_admin_servers_timeout")],
        [
            InlineKeyboardButton(
                "💻 Стандартные Windows", callback_data="set_standard_windows_timeout"
            )
        ],
        [InlineKeyboardButton("🐧 Linux серверы", callback_data="set_linux_timeout")],
        [InlineKeyboardButton("📡 Ping серверы", callback_data="set_ping_timeout")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_monitoring"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    try:
        query.edit_message_text(
            message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except (BadRequest, TelegramError) as exc:
        debug_logger(f"⚠️ show_server_timeouts edit_message_text Markdown failed: {exc}")
        query.edit_message_text(
            message.replace("*", ""), reply_markup=InlineKeyboardMarkup(keyboard)
        )


def add_server_handler(update, context):
    """Добавить сервер - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()

    # Сохраняем состояние добавления сервера
    context.user_data["adding_server"] = True
    context.user_data["server_stage"] = "ip"

    message = (
        "➕ *Добавление сервера*\n\n" "Введите IP-адрес сервера:\n\n" "_Пример: 192.168.9.000_"
    )

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="settings_servers")]]
        ),
    )


def handle_server_input(update, context):
    """Обработчик ввода данных сервера"""
    if "adding_server" not in context.user_data or not context.user_data["adding_server"]:
        return

    user_input = update.message.text
    stage = context.user_data.get("server_stage", "ip")

    try:
        if stage == "ip":
            # Проверка IP-адреса
            import re

            ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
            if not re.match(ip_pattern, user_input):
                update.message.reply_text("❌ Неверный формат IP-адреса. Попробуйте снова:")
                return

            context.user_data["server_ip"] = user_input
            context.user_data["server_stage"] = "name"

            update.message.reply_text(
                "📝 Введите имя сервера:\n\n" "_Пример: web-server-01_", parse_mode="Markdown"
            )

        elif stage == "name":
            context.user_data["server_name"] = user_input
            context.user_data["server_stage"] = "type"

            keyboard = [
                [InlineKeyboardButton("🖥️ Windows (RDP)", callback_data="server_type_rdp")],
                [InlineKeyboardButton("🐧 Linux (SSH)", callback_data="server_type_ssh")],
                [InlineKeyboardButton("📡 Ping Only", callback_data="server_type_ping")],
                [InlineKeyboardButton("❌ Отмена", callback_data="settings_servers")],
            ]

            update.message.reply_text(
                "🔧 Выберите тип сервера:", reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
        # Сбрасываем состояние при ошибке
        context.user_data["adding_server"] = False


def handle_server_type(update, context):
    """Обработчик выбора типа сервера"""
    query = update.callback_query
    query.answer()

    if "adding_server" not in context.user_data:
        return

    server_type = query.data.replace("server_type_", "")
    server_ip = context.user_data.get("server_ip")
    server_name = context.user_data.get("server_name")

    try:
        # Добавляем сервер в базу
        success = settings_manager.add_server(server_ip, server_name, server_type)

        if success:
            message = f"✅ *Сервер добавлен!*\n\n• IP: `{server_ip}`\n• Имя: `{server_name}`\n• Тип: `{server_type}`"

            # Очищаем состояние
            context.user_data["adding_server"] = False
            context.user_data.pop("server_ip", None)
            context.user_data.pop("server_name", None)
            context.user_data.pop("server_stage", None)
        else:
            message = "❌ Ошибка при добавлении сервера"

        query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ Назад к серверам", callback_data="settings_servers"
                        ),
                        InlineKeyboardButton(
                            "➕ Добавить еще", callback_data="settings_add_server"
                        ),
                    ]
                ]
            ),
        )

    except Exception as e:
        query.edit_message_text(f"❌ Ошибка: {e}")


def not_implemented_handler(update, context, feature_name=""):
    """Обработчик для функций в разработке"""
    query = update.callback_query
    query.answer()

    message = "🛠️ *Функция в разработке*\n\n"
    if feature_name:
        message += f"Функция '{feature_name}' находится в разработке.\n"
    message += "Скоро здесь будет доступна новая функциональность."

    # Определяем откуда пришел запрос для кнопки "Назад"
    back_button = "settings_main"
    if hasattr(query, "data"):
        if "telegram" in query.data:
            back_button = "settings_telegram"
        elif "backup" in query.data:
            back_button = "settings_backup"
        elif "servers" in query.data:
            back_button = "settings_servers"
        elif "monitoring" in query.data:
            back_button = "settings_monitoring"

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("↩️ Назад", callback_data=back_button),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ]
            ]
        ),
    )


def handle_server_type_management(update, context):
    """Обработчик управления типами серверов"""
    query = update.callback_query
    data = query.data

    if data == "manage_type_create":
        create_server_type_handler(update, context)
    elif data == "manage_type_delete":
        delete_server_type_handler(update, context)
    elif data == "manage_type_stats":
        show_server_type_stats(update, context)
    elif data.startswith("manage_type_edit_"):
        server_type = data.replace("manage_type_edit_", "")
        edit_server_type_handler(update, context, server_type)
    elif data.startswith("manage_type_merge_"):
        server_type = data.replace("manage_type_merge_", "")
        merge_server_type_handler(update, context, server_type)


def create_server_type_handler(update, context):
    """Создание нового типа серверов"""
    query = update.callback_query
    query.answer()

    context.user_data["creating_server_type"] = True

    query.edit_message_text(
        "➕ *Создание нового типа серверов*\n\n"
        "Введите название для нового типа:\n\n"
        "_Пример: web_servers, database_servers, backup_servers_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_manage_types")]]
        ),
    )


def edit_server_type_handler(update, context, old_type):
    """Редактирование типа серверов"""
    query = update.callback_query
    query.answer()

    context.user_data["editing_server_type"] = True
    context.user_data["old_server_type"] = old_type

    credentials = settings_manager.get_windows_credentials(old_type)

    query.edit_message_text(
        f"✏️ *Редактирование типа серверов*\n\n"
        f"Текущее название: *{old_type}*\n"
        f"Количество учетных записей: {len(credentials)}\n\n"
        "Введите новое название для этого типа:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_manage_types")]]
        ),
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

    message = "🔄 *Объединение типов серверов*\n\n"
    message += f"Источник: *{source_type}*\n"
    message += f"Учетных записей: {len(settings_manager.get_windows_credentials(source_type))}\n\n"
    message += "Выберите целевой тип для объединения:"

    keyboard = []
    for target_type in target_types:
        cred_count = len(settings_manager.get_windows_credentials(target_type))
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔄 {target_type} ({cred_count})",
                    callback_data=f"merge_confirm_{source_type}_{target_type}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_manage_types")])

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
        if server_type != "default":  # Не позволяем удалить тип 'default'
            cred_count = len(settings_manager.get_windows_credentials(server_type))
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🗑️ {server_type} ({cred_count})",
                        callback_data=f"delete_type_confirm_{server_type}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_manage_types")])

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
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
        enabled_count = sum(1 for cred in credentials if cred["enabled"])
        total_credentials += len(credentials)

        message += f"*{server_type}*\n"
        message += f"• Всего учетных записей: {len(credentials)}\n"
        message += f"• Активных: {enabled_count}\n"
        message += f"• Неактивных: {len(credentials) - enabled_count}\n\n"

    message += "*Общая статистика:*\n"
    message += f"• Типов серверов: {len(server_types)}\n"
    message += f"• Всего учетных записей: {total_credentials}\n"
    message += f"• Среднее на тип: {total_credentials / len(server_types):.1f} учетных записей"

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔄 Обновить", callback_data="manage_type_stats")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="windows_auth_manage_types"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def merge_server_types_confirmation(update, context, source_type, target_type):
    """Подтверждение объединения типов серверов"""
    query = update.callback_query
    query.answer()

    source_creds = settings_manager.get_windows_credentials(source_type)
    target_creds = settings_manager.get_windows_credentials(target_type)

    message = "🔄 *Подтверждение объединения*\n\n"
    message += f"*Источник:* {source_type}\n"
    message += f"• Учетных записей: {len(source_creds)}\n\n"
    message += f"*Цель:* {target_type}\n"
    message += f"• Учетных записей: {len(target_creds)}\n\n"
    message += "*После объединения:*\n"
    message += f"• Тип {source_type} будет удален\n"
    message += f"• Все учетные записи будут перемещены в {target_type}\n"
    message += f"• Итоговое количество: {len(source_creds) + len(target_creds)} учетных записей\n\n"
    message += "Вы уверены, что хотите выполнить объединение?"

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Да, объединить",
                        callback_data=f"merge_execute_{source_type}_{target_type}",
                    ),
                    InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_manage_types"),
                ]
            ]
        ),
    )


def delete_server_type_confirmation(update, context, server_type):
    """Подтверждение удаления типа серверов"""
    query = update.callback_query
    query.answer()

    credentials = settings_manager.get_windows_credentials(server_type)

    message = "🗑️ *Подтверждение удаления*\n\n"
    message += f"Тип: *{server_type}*\n"
    message += f"Учетных записей: {len(credentials)}\n\n"
    message += "*Внимание:* Все учетные записи этого типа будут перемещены в тип 'default'\n\n"
    message += "Вы уверены, что хотите удалить этот тип?"

    query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Да, удалить", callback_data=f"delete_type_execute_{server_type}"
                    ),
                    InlineKeyboardButton("❌ Отмена", callback_data="windows_auth_manage_types"),
                ]
            ]
        ),
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
            settings_manager.update_windows_credential(cred["id"], server_type=target_type)

        message = "✅ *Типы серверов объединены!*\n\n"
        message += f"• Тип *{source_type}* удален\n"
        message += f"• Все учетные записи перемещены в *{target_type}*\n"
        message += f"• Перемещено учетных записей: {len(source_credentials)}"

        query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ К управлению типами", callback_data="windows_auth_manage_types"
                        )
                    ]
                ]
            ),
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
            settings_manager.update_windows_credential(cred["id"], server_type="default")

        message = "✅ *Тип серверов удален!*\n\n"
        message += f"• Тип *{server_type}* удален\n"
        message += "• Все учетные записи перемещены в тип 'default'\n"
        message += f"• Перемещено учетных записей: {len(credentials)}"

        query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ К управлению типами", callback_data="windows_auth_manage_types"
                        )
                    ]
                ]
            ),
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
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data="windows_auth_manage_types")]]
                ),
            )
            return

        # Создаем новую учетную запись с этим типом (можно пустую)
        success = settings_manager.add_windows_credential(
            username=f"user_{new_type}", password="temp_password", server_type=new_type, priority=0
        )

        if success:
            # Сразу удаляем временную учетную запись, если нужно
            # или оставляем как шаблон

            update.message.reply_text(
                f"✅ *Тип серверов '{new_type}' создан!*\n\n"
                "Теперь вы можете добавить учетные записи для этого типа.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "➕ Добавить учетную запись", callback_data="windows_auth_add"
                            ),
                            InlineKeyboardButton(
                                "↩️ К управлению типами", callback_data="windows_auth_manage_types"
                            ),
                        ]
                    ]
                ),
            )
        else:
            update.message.reply_text("❌ Ошибка при создании типа")

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")

    # Очищаем контекст
    context.user_data["creating_server_type"] = False


def handle_server_type_editing(update, context):
    """Обработчик редактирования типа серверов"""
    new_type = update.message.text.strip()
    old_type = context.user_data.get("old_server_type")

    try:
        # Проверяем, не существует ли уже такой тип
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types and new_type != old_type:
            update.message.reply_text(
                f"❌ Тип '{new_type}' уже существует!",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data="windows_auth_manage_types")]]
                ),
            )
            return

        # Получаем все учетные записи старого типа
        credentials = settings_manager.get_windows_credentials(old_type)

        # Обновляем тип для каждой учетной записи
        for cred in credentials:
            settings_manager.update_windows_credential(cred["id"], server_type=new_type)

        update.message.reply_text(
            f"✅ *Тип серверов переименован!*\n\n"
            f"• Старое название: {old_type}\n"
            f"• Новое название: {new_type}\n"
            f"• Обновлено учетных записей: {len(credentials)}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ К управлению типами", callback_data="windows_auth_manage_types"
                        )
                    ]
                ]
            ),
        )

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")

    # Очищаем контекст
    context.user_data["editing_server_type"] = False
    context.user_data.pop("old_server_type", None)


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

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "db_input"
    context.user_data["backup_pattern_mode"] = "db_wizard"

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна БД*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Во фрагментах обязательно укажите имя БД из настроек.\n\n"
        "Пример темы:\n"
        "`Backup db company_main completed`\n\n"
        "Пример фрагментов:\n"
        "`Backup db; company_main; completed`",
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


def view_patterns_handler(update, context):
    """Просмотр паттернов"""
    query = update.callback_query
    query.answer()

    conn = settings_manager.get_connection()
    cursor = conn.cursor()
    filter_mode = context.user_data.get("patterns_filter", "all")
    if filter_mode == "zfs":
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'zfs'
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == "db":
        # Паттерны бэкапов БД — это произвольные категории-группы БД из
        # DATABASE_CONFIG (+ 'database'/'unknown'). Категории других,
        # независимых расширений (snapshot_transfer, stock_load, mail,
        # zfs, proxmox) сюда попадать не должны — иначе паттерны разных
        # расширений сваливаются в одну кучу в меню «Паттерны бэкапов БД».
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1
            AND category NOT IN (
                'mail', 'zfs', 'proxmox', 'snapshot_transfer', 'stock_load'
            )
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == "proxmox":
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1
            AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == "mail":
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'mail'
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == "stock_load":
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'stock_load'
            ORDER BY category, pattern_type, id
            """
        )
    elif filter_mode == "snapshot_transfer":
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category
            FROM backup_patterns
            WHERE enabled = 1 AND category = 'snapshot_transfer'
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

    title = context.user_data.get("patterns_title", "📋 *Паттерны*")
    display_rows = rows
    if filter_mode == "db":
        display_rows = []
        for pattern_id, pattern_type, pattern, category in rows:
            if category == "database" and pattern_type.startswith("proxmox"):
                continue
            display_category = category
            display_type = pattern_type
            if category == "database" and pattern_type.startswith("database"):
                normalized = pattern_type
                while normalized.startswith("database"):
                    normalized = normalized[len("database") :]
                display_category = normalized or category
                display_type = "subject"
            display_rows.append((pattern_id, display_type, pattern, display_category))
    if filter_mode == "proxmox":
        display_rows = []
        for pattern_id, pattern_type, pattern, category in rows:
            display_category = category
            display_type = pattern_type
            if category == "database" and pattern_type.startswith("proxmox"):
                normalized = pattern_type[len("proxmox") :]
                display_category = "proxmox"
                display_type = normalized or "subject"
            display_rows.append((pattern_id, display_type, pattern, display_category))
    if filter_mode == "stock_load":
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
    if not display_rows and filter_mode == "mail":
        fallback_patterns = _get_mail_fallback_patterns()
    if not display_rows and filter_mode == "db":
        fallback_db_patterns = _get_database_fallback_patterns()
    if not display_rows and filter_mode == "stock_load":
        fallback_stock_patterns = _get_stock_load_fallback_patterns()

    if (
        not display_rows
        and not fallback_patterns
        and not fallback_db_patterns
        and not fallback_stock_patterns
    ):
        message = f"{title}\n\n❌ Паттерны не настроены."
    else:
        message = f"{title}\n\n"
        current_category = None
        for index, (pattern_id, pattern_type, pattern, category) in enumerate(
            display_rows, start=1
        ):
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
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {index}. {category}:{pattern_type}",
                    callback_data=f"edit_pattern_{pattern_id}",
                ),
                InlineKeyboardButton(
                    f"🗑️ {index}. {category}:{pattern_type}",
                    callback_data=f"delete_pattern_{pattern_id}",
                ),
            ]
        )

    if fallback_patterns and filter_mode == "mail":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "✏️ Изменить дефолтный паттерн", callback_data="edit_mail_default_pattern"
                )
            ]
        )
    if fallback_db_patterns and filter_mode == "db":
        for category, patterns in fallback_db_patterns.items():
            for index, _ in enumerate(patterns, start=1):
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"✏️ {category} #{index}",
                            callback_data=f"db_default_edit_{category}__{index}",
                        ),
                        InlineKeyboardButton(
                            f"🗑️ {category} #{index}",
                            callback_data=f"db_default_delete_{category}__{index}",
                        ),
                    ]
                )

    add_callback = context.user_data.get("patterns_add")
    if add_callback:
        keyboard.append([InlineKeyboardButton("➕ Добавить паттерн", callback_data=add_callback)])

    back_callback = context.user_data.get("patterns_back", "settings_backup")
    if filter_mode in {"zfs", "snapshot_transfer"}:
        keyboard.append(
            [
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ]
        )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


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
    cursor.execute("UPDATE backup_patterns SET enabled = 0 WHERE id = ?", (pattern_id_int,))
    conn.commit()

    back_callback = context.user_data.get("patterns_back", "settings_backup")
    query.edit_message_text(
        "✅ Паттерн удалён.",
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
        (pattern_id_int,),
    )
    row = cursor.fetchone()

    if not row:
        back_callback = context.user_data.get("patterns_back", "settings_backup")
        query.edit_message_text(
            "❌ Паттерн не найден.",
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
        return

    _, pattern_type, pattern, category = row
    context.user_data["editing_backup_pattern"] = True
    context.user_data["editing_backup_pattern_id"] = pattern_id_int
    context.user_data["backup_pattern_category"] = category
    context.user_data["backup_pattern_type"] = pattern_type
    if category == "zfs":
        context.user_data["backup_pattern_mode"] = "zfs"
        context.user_data["backup_pattern_stage"] = "pattern_only"
    elif category == "proxmox":
        context.user_data["backup_pattern_mode"] = "proxmox"
        context.user_data["backup_pattern_stage"] = "pattern_only"
    elif category == "mail":
        context.user_data["backup_pattern_mode"] = "mail"
        context.user_data["backup_pattern_stage"] = "pattern_only"
    elif category == "stock_load":
        context.user_data["backup_pattern_mode"] = "stock"
        context.user_data["backup_pattern_stage"] = "pattern_only"
    else:
        context.user_data["backup_pattern_mode"] = "db"
        context.user_data["backup_pattern_stage"] = "subject"

    back_callback = context.user_data.get("patterns_back", "settings_backup")
    if category in ("zfs", "proxmox", "mail"):
        prompt = "Введите паттерн темы письма:"
    elif category == "stock_load":
        prompt = "Введите regex паттерн для выбранного типа:"
    else:
        prompt = "Введите тему письма (как приходит в почте):"

    query.edit_message_text(
        "✏️ *Редактирование паттерна*\n\n"
        f"Категория: *{category}*\n"
        f"Тип: *{pattern_type}*\n"
        f"Текущий паттерн: `{pattern}`\n\n"
        f"{prompt}",
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


def handle_backup_pattern_input(update, context):
    """Обработчик добавления паттерна"""
    if "adding_backup_pattern" not in context.user_data:
        return

    user_input = update.message.text.strip()
    stage = context.user_data.get("backup_pattern_stage", "category")
    mode = context.user_data.get("backup_pattern_mode", "db")

    if mode == "db_wizard":
        if stage != "db_input":
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
            context.user_data.pop("adding_backup_pattern", None)
            context.user_data.pop("backup_pattern_stage", None)
            context.user_data.pop("backup_pattern_mode", None)
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
                "❌ Не удалось определить категорию БД.\n" "Проверьте, что БД есть в настройках."
            )
            return

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "db_confirm"
        context.user_data["backup_pattern_category"] = category
        context.user_data["backup_pattern_db_name"] = db_name

        _show_db_pattern_confirm(update, context)
        return

    if mode == "zfs_wizard":
        if stage != "zfs_input":
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
            context.user_data.pop("adding_backup_pattern", None)
            context.user_data.pop("backup_pattern_stage", None)
            context.user_data.pop("backup_pattern_mode", None)
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

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "zfs_confirm"

        back_callback = context.user_data.get("patterns_back", "settings_backup")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✅ Сохранить", callback_data="zfs_pattern_confirm")],
                    [InlineKeyboardButton("✏️ Ввести заново", callback_data="zfs_pattern_retry")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode == "mail_wizard":
        if stage != "mail_input":
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

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "mail_confirm"

        back_callback = context.user_data.get("patterns_back", "settings_backup")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✅ Сохранить", callback_data="mail_pattern_confirm")],
                    [InlineKeyboardButton("✏️ Ввести заново", callback_data="mail_pattern_retry")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode == "snapshot_transfer_wizard":
        if stage != "mail_input":
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return
        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return
        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]
        pattern = (
            _build_mail_pattern_from_fragments(fragments)
            if len(fragments) > 1
            else _build_mail_pattern_from_subject(user_input)
        )
        source_label = "фрагменты" if len(fragments) > 1 else "тема письма"
        if not pattern:
            update.message.reply_text("❌ Не удалось собрать паттерн. Попробуйте снова:")
            return
        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "snapshot_confirm"
        back_callback = context.user_data.get("patterns_back", "settings_snapshot_menu")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Сохранить", callback_data="snapshot_pattern_confirm"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "✏️ Ввести заново", callback_data="snapshot_pattern_retry"
                        )
                    ],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode == "stock_subject_wizard":
        if stage != "stock_input":
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

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "stock_confirm"

        back_callback = context.user_data.get("patterns_back", "settings_backup")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✅ Сохранить", callback_data="stock_pattern_confirm")],
                    [InlineKeyboardButton("✏️ Ввести заново", callback_data="stock_pattern_retry")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode == "stock_source_wizard":
        if stage != "stock_input":
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        if "|" not in user_input:
            update.message.reply_text("❌ Нужен формат `Название | Тема письма`. Попробуйте снова:")
            return

        label_raw, subject_raw = (part.strip() for part in user_input.split("|", 1))
        if not label_raw or not subject_raw:
            update.message.reply_text("❌ Название и тема не могут быть пустыми. Попробуйте снова:")
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

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "stock_confirm"
        context.user_data["backup_pattern_stock_type"] = f"source:{label_raw}"
        context.user_data["backup_pattern_stock_label"] = label_raw

        back_callback = context.user_data.get("patterns_back", "settings_backup")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Метка: *{label_raw}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✅ Сохранить", callback_data="stock_pattern_confirm")],
                    [InlineKeyboardButton("✏️ Ввести заново", callback_data="stock_pattern_retry")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode == "stock_log_wizard":
        if stage != "stock_input":
            update.message.reply_text("❌ Неверный шаг мастера. Попробуйте снова.")
            return

        if not user_input:
            update.message.reply_text("❌ Ввод не может быть пустым. Попробуйте снова:")
            return

        pattern_type = context.user_data.get("backup_pattern_stock_type", "file_entry")
        fragments = [chunk.strip() for chunk in re.split(r"[;,\n]+", user_input)]
        fragments = [fragment for fragment in fragments if fragment]

        if len(fragments) > 1:
            pattern = _build_stock_pattern_from_fragments(fragments)
            source_label = "фрагменты"
        else:
            if pattern_type == "success":
                pattern = _build_stock_success_pattern(user_input)
                source_label = "строка лога"
            elif pattern_type == "attachment":
                pattern = re.escape(user_input.strip()) + r"$"
                source_label = "имя файла"
            elif pattern_type == "ignore":
                pattern = _build_stock_pattern_from_fragments([user_input])
                source_label = "строка лога"
            elif pattern_type == "failure":
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

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "stock_confirm"

        back_callback = context.user_data.get("patterns_back", "settings_backup")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✅ Сохранить", callback_data="stock_pattern_confirm")],
                    [InlineKeyboardButton("✏️ Ввести заново", callback_data="stock_pattern_retry")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode == "proxmox_wizard":
        if stage != "proxmox_input":
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

        context.user_data["backup_pattern_generated"] = pattern
        context.user_data["backup_pattern_source"] = source_label
        context.user_data["backup_pattern_stage"] = "proxmox_confirm"

        back_callback = context.user_data.get("patterns_back", "settings_backup")
        update.message.reply_text(
            "✅ *Черновик паттерна готов!*\n\n"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`\n\n"
            "Сохранить?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("✅ Сохранить", callback_data="proxmox_pattern_confirm")],
                    [
                        InlineKeyboardButton(
                            "✏️ Ввести заново", callback_data="proxmox_pattern_retry"
                        )
                    ],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    if mode in ("zfs", "proxmox", "mail"):
        if not user_input:
            update.message.reply_text("❌ Паттерн не может быть пустым. Попробуйте снова:")
            return

        pattern = user_input
        pattern_type = "subject"
        if mode == "zfs":
            category = "zfs"
        elif mode == "proxmox":
            category = "proxmox"
        else:
            category = "mail"
        back_callback = context.user_data.get("patterns_back", "settings_backup")

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (pattern_type, pattern, category),
            )
            conn.commit()

            update.message.reply_text(
                "✅ *Паттерн добавлен!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
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
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        finally:
            context.user_data.pop("adding_backup_pattern", None)
            context.user_data.pop("backup_pattern_stage", None)
            context.user_data.pop("backup_pattern_category", None)
            context.user_data.pop("backup_pattern_type", None)
            context.user_data.pop("backup_pattern_subject", None)
            context.user_data.pop("backup_pattern_mode", None)
        return

    if stage == "subject":
        if not user_input:
            update.message.reply_text("❌ Тема не может быть пустой. Попробуйте снова:")
            return
        context.user_data["backup_pattern_subject"] = user_input
        context.user_data["backup_pattern_stage"] = "db_name"
        update.message.reply_text("Введите имя базы данных из темы письма:")
        return

    if stage == "db_name":
        if not user_input:
            update.message.reply_text("❌ Имя базы не может быть пустым. Попробуйте снова:")
            return

        subject = context.user_data.get("backup_pattern_subject")
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

        back_callback = context.user_data.get("patterns_back", "settings_backup")

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (pattern_type, pattern, category),
            )
            conn.commit()

            update.message.reply_text(
                "✅ *Паттерн добавлен!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
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
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        finally:
            context.user_data.pop("adding_backup_pattern", None)
            context.user_data.pop("backup_pattern_stage", None)
            context.user_data.pop("backup_pattern_category", None)
            context.user_data.pop("backup_pattern_type", None)
            context.user_data.pop("backup_pattern_subject", None)
            context.user_data.pop("backup_pattern_mode", None)


def handle_backup_pattern_edit_input(update, context):
    """Обработчик редактирования паттерна"""
    if "editing_backup_pattern" not in context.user_data:
        return

    new_pattern = update.message.text.strip()
    stage = context.user_data.get("backup_pattern_stage", "subject")
    mode = context.user_data.get("backup_pattern_mode", "db")

    if mode in ("zfs", "proxmox", "mail", "stock"):
        if not new_pattern:
            update.message.reply_text("❌ Паттерн не может быть пустым. Попробуйте снова:")
            return

        pattern_id = context.user_data.get("editing_backup_pattern_id")
        if not pattern_id:
            update.message.reply_text("❌ Не найден паттерн для редактирования.")
            context.user_data.pop("editing_backup_pattern", None)
            return

        if mode == "zfs":
            category = "zfs"
        elif mode == "proxmox":
            category = "proxmox"
        elif mode == "mail":
            category = "mail"
        else:
            category = "stock_load"
        pattern_type = context.user_data.get("backup_pattern_type", "subject")
        back_callback = context.user_data.get("patterns_back", "settings_backup")

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern = ?, category = ?, pattern_type = ?
                WHERE id = ?
                """,
                (new_pattern, category, pattern_type, pattern_id),
            )
            conn.commit()

            update.message.reply_text(
                "✅ *Паттерн обновлён!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
                f"Паттерн: `{new_pattern}`",
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
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        finally:
            context.user_data.pop("editing_backup_pattern", None)
            context.user_data.pop("editing_backup_pattern_id", None)
            context.user_data.pop("backup_pattern_category", None)
            context.user_data.pop("backup_pattern_type", None)
            context.user_data.pop("backup_pattern_subject", None)
            context.user_data.pop("backup_pattern_stage", None)
            context.user_data.pop("backup_pattern_mode", None)
        return

    if stage == "subject":
        if not new_pattern:
            update.message.reply_text("❌ Тема не может быть пустой. Попробуйте снова:")
            return
        context.user_data["backup_pattern_subject"] = new_pattern
        context.user_data["backup_pattern_stage"] = "db_name"
        update.message.reply_text("Введите имя базы данных из темы письма:")
        return

    if stage == "db_name":
        if not new_pattern:
            update.message.reply_text("❌ Имя базы не может быть пустым. Попробуйте снова:")
            return

        subject = context.user_data.get("backup_pattern_subject")
        db_name = new_pattern
        escaped_subject = re.escape(subject)
        escaped_db_name = re.escape(db_name)
        if escaped_db_name not in escaped_subject:
            update.message.reply_text(
                "❌ Имя базы не найдено в теме письма. Проверьте ввод и попробуйте снова:"
            )
            return

        pattern_id = context.user_data.get("editing_backup_pattern_id")
        if not pattern_id:
            update.message.reply_text("❌ Не найден паттерн для редактирования.")
            context.user_data.pop("editing_backup_pattern", None)
            return

        new_pattern = escaped_subject.replace(escaped_db_name, r"([\w.-]+)")
        category = _get_database_category(db_name)
        pattern_type = "subject"

        back_callback = context.user_data.get("patterns_back", "settings_backup")

        try:
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern = ?, category = ?, pattern_type = ?
                WHERE id = ?
                """,
                (new_pattern, category, pattern_type, pattern_id),
            )
            conn.commit()

            update.message.reply_text(
                "✅ *Паттерн обновлён!*\n\n"
                f"Категория: *{category}*\n"
                f"Тип: *{pattern_type}*\n"
                f"Паттерн: `{new_pattern}`",
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
            update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        finally:
            context.user_data.pop("editing_backup_pattern", None)
            context.user_data.pop("editing_backup_pattern_id", None)
            context.user_data.pop("backup_pattern_category", None)
            context.user_data.pop("backup_pattern_type", None)
            context.user_data.pop("backup_pattern_subject", None)
            context.user_data.pop("backup_pattern_stage", None)
            context.user_data.pop("backup_pattern_mode", None)
