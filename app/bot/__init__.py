"""
Server Monitoring System v4.4.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчики и меню Telegram бота

"""

from .handlers import *
from .menus import (
    setup_menu_commands, create_main_menu, get_start_message, get_help_message,
    start_command, help_command, show_extensions_menu, extensions_callback_handler,
    toggle_extension, enable_all_extensions, disable_all_extensions, check_command, 
    status_command, silent_command, control_command, servers_command, report_command, 
    stats_command, diagnose_ssh_command, extensions_command, debug_command
)
from .callbacks import callback_router
from .debug_menu import debug_menu

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
