"""
Server Monitoring System v4.4.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчики и меню Telegram бота
Версия: 4.4.0
"""

from .handlers import *
from .menus import setup_menu_commands, create_main_menu, get_start_message, get_help_message
from .callbacks import callback_router
# Добавьте другие модули по мере создания

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
    
    # Из menus.py
    'setup_menu_commands',
    'create_main_menu', 
    'get_start_message',
    'get_help_message',
    
    # Из callbacks.py
    'callback_router',
]