"""
/src/monitoring/app/handlers/callbacks.py
Server Monitoring System v4.16.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot callback handlers
Система мониторинга серверов
Версия: 4.16.3
Автор: Александр Суханов (c)
Лицензия: MIT
Callback-обработчики Telegram бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.logging import debug_log

def handle_check_single_callback(update, context, server_ip):
    """Обработка callback проверки одного сервера"""
    query = update.callback_query
    query.answer()
    
    from app.handlers.commands import handle_check_single_server
    result = handle_check_single_server(update, context, server_ip)
    
    query.edit_message_text(
        text=result,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f'check_resources_{server_ip}')],
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f'check_single_{server_ip}')],
            [InlineKeyboardButton("↩️ Выбрать другой", callback_data='check_single_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_check_resources_callback(update, context, server_ip):
    """Обработка callback проверки ресурсов сервера"""
    query = update.callback_query
    query.answer()
    
    from app.handlers.commands import handle_check_server_resources
    result = handle_check_server_resources(update, context, server_ip)
    
    query.edit_message_text(
        text=result,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Обновить", callback_data=f'check_resources_{server_ip}')],
            [InlineKeyboardButton("📡 Проверить доступность", callback_data=f'check_single_{server_ip}')],
            [InlineKeyboardButton("↩️ Выбрать другой", callback_data='check_resources_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_server_selection_menu(update, context, action="check_single"):
    """Показывает меню выбора сервера"""
    query = update.callback_query
    query.answer()
    
    from app.handlers.commands import create_server_selection_keyboard
    
    if action == "check_single":
        message = "📡 *Выберите сервер для проверки доступности:*"
    elif action == "check_resources":
        message = "📊 *Выберите сервер для проверки ресурсов:*"
    else:
        message = "🔍 *Выберите сервер:*"
    
    keyboard = create_server_selection_keyboard(action=action)
    
    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )