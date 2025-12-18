"""
/bot/handlers/callbacks.py
Server Monitoring System v4.14.13
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
A single router for callbacks.
Система мониторинга серверов
Версия: 4.14.13
Автор: Александр Суханов (c)
Лицензия: MIT
Единый router callback’ов.
"""

from bot.menu.handlers import show_main_menu
from settings_handlers import settings_callback_handler
from monitor_core import (
    manual_check_handler,
    monitor_status,
    silent_status_handler,
    control_panel_handler,
    toggle_monitoring_handler,
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.base import check_access, deny_access
from modules.targeted_checks import targeted_checks
from extensions.extension_manager import extension_manager
from bot.handlers.extensions import (
    show_extensions_menu,
    extensions_callback_handler
)

from lib.logging import debug_log

def _server_result_keyboard(server_ip: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📡 Доступность", callback_data=f"check_availability_{server_ip}"),
            InlineKeyboardButton("📊 Ресурсы", callback_data=f"check_resources_{server_ip}"),
        ],
        [
            InlineKeyboardButton("🖥 Доступность сервера", callback_data="show_availability_menu"),
            InlineKeyboardButton("💻 Ресурсы сервера", callback_data="show_resources_menu"),
        ],
        [
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ])

def callback_router(update, context):
    query = update.callback_query
    data = query.data

    debug_log(f"📥 CALLBACK DATA: {data}")
    
    if not check_access(update):
        deny_access(update)
        return

    query.answer()

    # ------------------------------------------------
    # Главное меню
    # ------------------------------------------------
    if data == 'main_menu':
        from bot.menu.handlers import show_main_menu
        show_main_menu(update, context)

    # ------------------------------------------------
    # ДОСТУПНОСТЬ ВСЕХ СЕРВЕРОВ (ручная проверка)
    # ------------------------------------------------
    elif data == 'manual_check':
        manual_check_handler(update, context)
        
    # ------------------------------------------------
    # ОДИН СЕРВЕР (доступность)
    # ------------------------------------------------
    elif data == 'show_availability_menu':
        query.edit_message_text(
            "📡 *Выберите сервер для проверки доступности:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_availability"
            )
        )

    elif data.startswith('check_availability_'):
        server_id = data.replace('check_availability_', '')

        success, server, message = targeted_checks.check_single_server_availability(server_id)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=_server_result_keyboard(server_id)
        )

    # ------------------------------------------------
    # РЕСУРСЫ СЕРВЕРА
    # ------------------------------------------------
    elif data == 'show_resources_menu':
        query.edit_message_text(
            "📊 *Выберите сервер для проверки ресурсов:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_resources"
            )
        )

    elif data.startswith('check_resources_'):
        server_id = data.replace('check_resources_', '')

        success, server, message = targeted_checks.check_single_server_resources(server_id)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=_server_result_keyboard(server_id)
        )

    # ------------------------------------------------
    # ПРОВЕРКА РЕСУРСОВ ВСЕХ СЕРВЕРОВ
    # ------------------------------------------------
    elif data == 'check_resources':
        query.edit_message_text(
            "📊 *Выберите сервер для проверки ресурсов:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_resources"
            )
        )

    # ------------------------------------------------
    # БЭКАПЫ
    # ------------------------------------------------
    elif data.startswith('backup_'):
        if extension_manager.is_extension_enabled('backup_monitor'):
            from extensions.backup_monitor.bot_handler import backup_callback
            backup_callback(update, context)
        else:
            query.edit_message_text("💾 Модуль бэкапов отключён")

    # ------------------------------------------------
    # РАСШИРЕНИЯ
    # ------------------------------------------------
    elif data == 'extensions_menu':
        show_extensions_menu(update, context)

    elif data.startswith('ext_'):
        extensions_callback_handler(update, context)

    # ------------------------------------------------
    # Закрытие
    # ------------------------------------------------
    elif data == 'close':
        query.delete_message()
