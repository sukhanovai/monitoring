"""
Server Monitoring System v4.11.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot menu package
Система мониторинга серверов
Версия: 4.11.3
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет меню бота
"""

from .builder import setup_menu, build_main_menu_keyboard

# Убираем импорты handlers, делаем их ленивыми
def get_menu_handlers():
    """Возвращает обработчики меню (ленивая загрузка)"""
    from .handlers import (
        start_command,
        help_command,
        show_extensions_menu,
        extensions_callback_handler,
        debug_command,
        show_debug_menu,
        debug_callback_handler
    )
    return {
        'start_command': start_command,
        'help_command': help_command,
        'show_extensions_menu': show_extensions_menu,
        'extensions_callback_handler': extensions_callback_handler,
        'debug_command': debug_command,
        'show_debug_menu': show_debug_menu,
        'debug_callback_handler': debug_callback_handler
    }

__all__ = [
    'setup_menu',
    'build_main_menu_keyboard',
    'get_menu_handlers'
]