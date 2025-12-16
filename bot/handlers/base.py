"""
Server Monitoring System v4.11.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Base bot handlers
Система мониторинга серверов
Версия: 4.11.3
Автор: Александр Суханов (c)
Лицензия: MIT
Базовые обработчики бота
"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from lib.logging import debug_log
from config.settings import DEBUG_MODE
from bot.utils import check_access, get_access_denied_response

def lazy_handler(handler_name):
    """Ленивая загрузка обработчиков"""
    def wrapper(update, context):
        # Динамически импортируем обработчик при вызове
        if handler_name == 'main_menu':
            from bot.menu.handlers import start_command
            return start_command(update, context)
        elif handler_name == 'manual_check':
            from core.monitor import manual_check_handler
            return manual_check_handler(update, context)
        elif handler_name == 'monitor_status':
            from core.monitor import monitor_status
            return monitor_status(update, context)
        elif handler_name == 'silent_status':
            from core.monitor import silent_status_handler
            return silent_status_handler(update, context)
        elif handler_name == 'check_resources':
            from core.monitor import check_resources_handler
            return check_resources_handler(update, context)
        elif handler_name == 'control_panel':
            from core.monitor import control_panel_handler
            return control_panel_handler(update, context)
        elif handler_name == 'toggle_monitoring':
            from core.monitor import toggle_monitoring_handler
            return toggle_monitoring_handler(update, context)
        elif handler_name == 'daily_report':
            from modules.morning_report import send_morning_report_handler
            return send_morning_report_handler(update, context)
        elif handler_name == 'close':
            from core.monitor import close_menu
            return close_menu(update, context)
        elif handler_name == 'force_silent':
            from core.monitor import force_silent_handler
            return force_silent_handler(update, context)
        elif handler_name == 'force_loud':
            from core.monitor import force_loud_handler
            return force_loud_handler(update, context)
        elif handler_name == 'auto_mode':
            from core.monitor import auto_mode_handler
            return auto_mode_handler(update, context)
        elif handler_name == 'toggle_silent':
            from core.monitor import toggle_silent_mode_handler
            return toggle_silent_mode_handler(update, context)
        elif handler_name == 'servers_list':
            from extensions.server_checks import servers_list_handler
            return servers_list_handler(update, context)
        elif handler_name == 'debug_report':
            from core.monitor import debug_morning_report
            return debug_morning_report(update, context)
        elif handler_name == 'check_linux':
            from core.monitor import check_linux_resources_handler
            return check_linux_resources_handler(update, context)
        elif handler_name == 'check_windows':
            from core.monitor import check_windows_resources_handler
            return check_windows_resources_handler(update, context)
        elif handler_name == 'check_other':
            from core.monitor import check_other_resources_handler
            return check_other_resources_handler(update, context)
        elif handler_name == 'check_cpu':
            from core.monitor import check_cpu_resources_handler
            return check_cpu_resources_handler(update, context)
        elif handler_name == 'check_ram':
            from core.monitor import check_ram_resources_handler
            return check_ram_resources_handler(update, context)
        elif handler_name == 'check_disk':
            from core.monitor import check_disk_resources_handler
            return check_disk_resources_handler(update, context)
        elif handler_name == 'extensions_menu':
            from bot.menu.handlers import show_extensions_menu
            return show_extensions_menu(update, context)
        elif handler_name == 'extensions_refresh':
            from bot.menu.handlers import show_extensions_menu
            return show_extensions_menu(update, context)
        elif handler_name == 'ext_enable_all':
            from bot.menu.handlers import enable_all_extensions
            return enable_all_extensions(update, context)
        elif handler_name == 'ext_disable_all':
            from bot.menu.handlers import disable_all_extensions
            return disable_all_extensions(update, context)
        elif handler_name == 'debug_menu':
            from bot.menu.handlers import show_debug_menu
            return show_debug_menu(update, context)
        else:
            def default_handler(update, context):
                query = update.callback_query
                query.answer()
                query.edit_message_text("❌ Обработчик не найден")
            return default_handler(update, context)
    return wrapper

def lazy_message_handler():
    """Ленивая загрузка обработчика сообщений"""
    def handler(update, context):
        try:
            from settings_handlers import handle_setting_value
            return handle_setting_value(update, context)
        except ImportError as e:
            debug_log(f"❌ Ошибка импорта handle_setting_value: {e}")
            return
    return handler