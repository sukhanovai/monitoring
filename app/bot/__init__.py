"""
Server Monitoring System v4.3.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчики и меню Telegram бота
Версия: 4.3.8
"""

from .handlers import *

__all__ = [
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
]
