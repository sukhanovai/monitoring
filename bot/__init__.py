"""
/bot/__init__.py
Server Monitoring System v8.3.29
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot module
Система мониторинга серверов
Версия: 8.3.29
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль Telegram-бота
"""

from bot.handlers import (
    get_callback_handlers,
    get_command_handlers,
    get_message_handlers,
)
from bot.menu import main_menu, show_main_menu

__all__ = [
    "get_command_handlers",
    "get_callback_handlers",
    "get_message_handlers",
    "main_menu",
    "show_main_menu",
]
