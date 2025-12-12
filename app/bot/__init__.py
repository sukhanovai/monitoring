"""
Server Monitoring System v4.4.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчики и меню Telegram бота

"""

from .handlers import *
from .menus import (
    setup_menu_commands, create_main_menu, get_start_message, get_help_message,
    start_command, help_command, show_extensions_menu, extensions_callback_handler,
    toggle_extension, enable_all_extensions, disable_all_extensions
)
from .callbacks import callback_router
from .debug_menu import debug_menu

# Создаем временные заглушки для команд которые еще не реализованы
def check_command(update, context):
    update.message.reply_text("✅ Команда /check временно недоступна (рефакторинг)")

def status_command(update, context):
    update.message.reply_text("📊 Команда /status временно недоступна (рефакторинг)")

def silent_command(update, context):
    update.message.reply_text("🔇 Команда /silent временно недоступна (рефакторинг)")

def control_command(update, context):
    update.message.reply_text("🎛️ Команда /control временно недоступна (рефакторинг)")

def servers_command(update, context):
    update.message.reply_text("🖥️ Команда /servers временно недоступна (рефакторинг)")

def report_command(update, context):
    update.message.reply_text("📊 Команда /report временно недоступна (рефакторинг)")

def stats_command(update, context):
    update.message.reply_text("📈 Команда /stats временно недоступна (рефакторинг)")

def diagnose_ssh_command(update, context):
    update.message.reply_text("🔧 Команда /diagnose_ssh временно недоступна (рефакторинг)")

def extensions_command(update, context):
    update.message.reply_text("🛠️ Команда /extensions временно недоступна (рефакторинг)")

def debug_command(update, context):
    update.message.reply_text("🐛 Команда /debug временно недоступна (рефакторинг)")

__all__ = [
    # Из handlers.py
    'close_menu',
    'force_silent_handler',
    'force_loud_handler',
    'auto_mode_handler',
    'toggle_silent_mode_handler',
    'send_morning_report_handler',
    'resource_page_handler',
    'refresh_resources_handler',
    'close_resources_handler',
    'resource_history_command',
    'debug_morning_report',
    'check_linux_resources_handler',
    'check_windows_resources_handler',
    'check_other_resources_handler',
    'check_cpu_resources_handler',
    'check_ram_resources_handler',
    'check_disk_resources_handler',
    'get_handlers',
    
    # Из menus.py
    'setup_menu_commands',
    'create_main_menu', 
    'get_start_message',
    'get_help_message',
    'start_command',
    'help_command',
    'show_extensions_menu',
    'extensions_callback_handler',
    'toggle_extension',
    'enable_all_extensions',
    'disable_all_extensions',
    
    # Временные заглушки
    'check_command',
    'status_command',
    'silent_command',
    'control_command',
    'servers_command',
    'report_command',
    'stats_command',
    'diagnose_ssh_command',
    'extensions_command',
    'debug_command',
    
    # Из callbacks.py
    'callback_router',
    
    # Из debug_menu.py
    'debug_menu',
]
