"""
/bot/handlers/commands.py
Server Monitoring System v4.13.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Command handlers
Система мониторинга серверов
Версия: 4.13.1
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики команд
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from bot.handlers.base import base_handler, check_access
from bot.menu.builder import menu_builder
from lib.logging import debug_log

@base_handler.access_check_decorator
def start_command(update, context):
    """Обработчик команды /start"""
    debug_log("Вызвана команда /start")
    return menu_builder.show_main_menu(update, context)

@base_handler.access_check_decorator
def help_command(update, context):
    """Обработчик команды /help"""
    help_text = (
        "🤖 *Помощь по мониторингу*\n\n"
        "*Основные команды:*\n"
        "• `/start` - Главное меню\n"
        "• `/check` - Быстрая проверка серверов\n"
        "• `/servers` - Список всех серверов\n"
        "• `/control` - Управление мониторингом\n"
        "• `/extensions` - Управление расширениями\n"
        "• `/debug` - Управление отладкой\n\n"
        "*Диагностика:*\n"
        "• `/diagnose_ssh <ip>` - Проверка SSH подключения\n"
        "• `/silent` - Статус тихого режима\n\n"
        "*Отчеты:*\n"
        "• `/report` - Принудительная отправка утреннего отчета\n"
        "• `/stats` - Статистика работы\n\n"
        "*Используйте кнопки меню для удобного управления*"
    )
    
    update.message.reply_text(help_text, parse_mode='Markdown')

@base_handler.access_check_decorator
def check_command(update, context):
    """Обработчик команды /check"""
    from core.monitor import manual_check_handler
    return manual_check_handler(update, context)

@base_handler.access_check_decorator
def status_command(update, context):
    """Обработчик команды /status"""
    from core.monitor import monitor_status
    return monitor_status(update, context)

@base_handler.access_check_decorator
def silent_command(update, context):
    """Обработчик команды /silent"""
    from core.monitor import silent_command
    return silent_command(update, context)

@base_handler.access_check_decorator
def control_command(update, context):
    """Обработчик команды /control"""
    from core.monitor import control_command
    return control_command(update, context)

@base_handler.access_check_decorator
def servers_command(update, context):
    """Обработчик команды /servers"""
    # Импортируем динамически чтобы избежать циклических зависимостей
    from extensions.server_checks import servers_command
    return servers_command(update, context)

@base_handler.access_check_decorator
def report_command(update, context):
    """Обработчик команды /report"""
    from modules.morning_report import send_morning_report_handler
    return send_morning_report_handler(update, context)

@base_handler.access_check_decorator
def stats_command(update, context):
    """Обработчик команды /stats"""
    from extensions.utils import stats_command
    return stats_command(update, context)

@base_handler.access_check_decorator
def diagnose_ssh_command(update, context):
    """Обработчик команды /diagnose_ssh"""
    from extensions.utils import diagnose_ssh_command
    return diagnose_ssh_command(update, context)

@base_handler.access_check_decorator
def extensions_command(update, context):
    """Обработчик команды /extensions"""
    from extensions.extension_manager import show_extensions_menu
    return show_extensions_menu(update, context)

@base_handler.access_check_decorator
def debug_command(update, context):
    """Обработчик команды /debug"""
    from bot.menu.handlers import show_debug_menu
    return show_debug_menu(update, context)

@base_handler.access_check_decorator
def backup_command(update, context):
    """Обработчик команды /backup"""
    from extensions.extension_manager import extension_manager
    
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')]
            ])
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_command
    return backup_command(update, context)

def get_command_handlers():
    """Возвращает все обработчики команд"""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("check", check_command),
        CommandHandler("status", status_command),
        CommandHandler("servers", servers_command),
        CommandHandler("silent", silent_command),
        CommandHandler("report", report_command),
        CommandHandler("stats", stats_command),
        CommandHandler("control", control_command),
        CommandHandler("diagnose_ssh", diagnose_ssh_command),
        CommandHandler("extensions", extensions_command),
        CommandHandler("debug", debug_command),
        CommandHandler("backup", backup_command),
        CommandHandler("backup_search", backup_search_command),
        CommandHandler("backup_help", backup_help_command),
    ]

# Временные заглушки для команд бэкапов
@base_handler.access_check_decorator
def backup_search_command(update, context):
    """Временная заглушка для /backup_search"""
    from extensions.extension_manager import extension_manager
    
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен."
        )
        return
    
    update.message.reply_text("🔍 Поиск бэкапов временно недоступен")

@base_handler.access_check_decorator
def backup_help_command(update, context):
    """Временная заглушка для /backup_help"""
    from extensions.extension_manager import extension_manager
    
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен."
        )
        return
    
    update.message.reply_text("❓ Помощь по бэкапам временно недоступна")