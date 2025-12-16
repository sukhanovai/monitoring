"""
Server Monitoring System v4.11.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot menu package
Система мониторинга серверов
Версия: 4.11.0
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет меню бота
"""

from .builder import setup_menu, build_main_menu_keyboard
from .handlers import (
    start_command,
    help_command,
    show_extensions_menu,
    extensions_callback_handler,
    debug_command,
    show_debug_menu,
    debug_callback_handler
)

__all__ = [
    'setup_menu',
    'build_main_menu_keyboard',
    'start_command',
    'help_command',
    'show_extensions_menu',
    'extensions_callback_handler',
    'debug_command',
    'show_debug_menu',
    'debug_callback_handler'
]