"""
Server Monitoring System v4.11.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot handlers package
Система мониторинга серверов
Версия: 4.11.2
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет обработчиков бота
"""

from .base import lazy_handler, lazy_message_handler
from .commands import setup_command_handlers
from .callbacks import setup_callback_handlers
from bot.utils import check_access, get_access_denied_response

__all__ = [
    'check_access',
    'get_access_denied_response',
    'lazy_handler',
    'lazy_message_handler',
    'setup_command_handlers',
    'setup_callback_handlers'
]