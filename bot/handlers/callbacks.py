"""
/bot/handlers/callbacks.py
Server Monitoring System v4.13.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Callback handlers
Система мониторинга серверов
Версия: 4.13.5
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики callback-запросов
"""

from telegram.ext import CallbackQueryHandler
from bot.handlers.base import base_handler
from lib.logging import debug_log
from bot.menu.handlers import menu_handlers

def handle_callback(update, context):
    """Основной обработчик callback-запросов"""
    query = update.callback_query
    data = query.data
    
    debug_log(f"Callback получен: {data}")
    
    try:
        # Делегируем обработку соответствующему обработчику
        if data in menu_handlers:
            return menu_handlers[data](update, context)
        
        # Специальные обработчики
        elif data == 'close':
            return handle_close(update, context)
        elif data == 'main_menu':
            from bot.menu.builder import menu_builder
            return menu_builder.show_main_menu(update, context)
        
        # Группы callback-данных
        elif data.startswith('check_single_'):
            return handle_single_check(update, context, data)
        elif data.startswith('check_resources_'):
            return handle_single_resources(update, context, data)
        elif data.startswith('debug_'):
            return handle_debug_callback(update, context, data)
        elif data.startswith('ext_'):
            return handle_extension_callback(update, context, data)
        elif data.startswith('settings_'):
            return handle_settings_callback(update, context, data)
        
        else:
            query.answer("❌ Неизвестная команда")
            debug_log(f"Неизвестный callback: {data}")
            
    except Exception as e:
        debug_log(f"Ошибка обработки callback {data}: {e}")
        query.answer("❌ Произошла ошибка")

def handle_close(update, context):
    """Закрывает меню"""
    query = update.callback_query
    query.answer()
    try:
        query.delete_message()
    except:
        query.edit_message_text("✅ Меню закрыто")

def handle_single_check(update, context, data):
    """Обработчик точечной проверки"""
    from modules.targeted_checks import handle_single_check_callback
    server_ip = data.replace('check_single_', '')
    return handle_single_check_callback(update, context, server_ip)

def handle_single_resources(update, context, data):
    """Обработчик точечной проверки ресурсов"""
    from modules.targeted_checks import handle_single_resources_callback
    server_ip = data.replace('check_resources_', '')
    return handle_single_resources_callback(update, context, server_ip)

def handle_debug_callback(update, context, data):
    """Обработчик callback-ов отладки"""
    from bot.menu.handlers import debug_callback_handler
    return debug_callback_handler(update, context)

def handle_extension_callback(update, context, data):
    """Обработчик callback-ов расширений"""
    from extensions.extension_manager import extensions_callback_handler
    return extensions_callback_handler(update, context)

def handle_settings_callback(update, context, data):
    """Обработчик callback-ов настроек"""
    # Импортируем динамически чтобы избежать циклических зависимостей
    try:
        from settings_handlers import settings_callback_handler
        return settings_callback_handler(update, context)
    except ImportError:
        query = update.callback_query
        query.answer("⚙️ Модуль настроек временно недоступен")
        return

def get_callback_handlers():
    """Возвращает все обработчики callback-запросов"""
    return [
        # Основной обработчик для всех callback-ов
        CallbackQueryHandler(handle_callback),
        
        # Специальные обработчики (для совместимости со старым кодом)
        CallbackQueryHandler(handle_settings_callback, pattern='^settings_'),
        CallbackQueryHandler(handle_settings_callback, pattern='^set_'),
        CallbackQueryHandler(handle_settings_callback, pattern='^backup_'),
        CallbackQueryHandler(handle_settings_callback, pattern='^manage_'),
    ]