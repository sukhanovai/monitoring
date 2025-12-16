"""
Server Monitoring System v4.11.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot package
Система мониторинга серверов
Версия: 4.11.4
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет бота
"""

from .menu import setup_menu
from .handlers import (
    setup_command_handlers,
    setup_callback_handlers,
    lazy_message_handler
)
from .utils import check_access, get_access_denied_response

def get_bot_handlers():
    """Возвращает все обработчики для бота"""
    handlers = []
    handlers.extend(setup_command_handlers())
    handlers.extend(setup_callback_handlers())
    return handlers

def get_bot_message_handler():
    """Возвращает обработчик сообщений"""
    from telegram.ext import MessageHandler, Filters
    return MessageHandler(Filters.text & ~Filters.command, lazy_message_handler())

__all__ = [
    'setup_menu',
    'get_bot_handlers',
    'get_bot_message_handler',
    'check_access',
    'get_access_denied_response'
]