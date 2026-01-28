"""
/bot/handlers/__init__.py
Server Monitoring System v8.3.10
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers package exports
Система мониторинга серверов
Версия: 8.3.10
Автор: Александр Суханов (c)
Лицензия: MIT
Экспорт вспомогательных функций для регистрации обработчиков
"""

import importlib

from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler

from bot.handlers.callbacks import callback_router
from bot.handlers.commands import (
    check_command,
    control_panel_command,
    help_command,
    report_command,
    silent_mode_command,
    start_command,
    status_command,
)


def get_command_handlers():
    """Возвращает список обработчиков команд."""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("check", check_command),
        CommandHandler("status", status_command),
        CommandHandler("silent", silent_mode_command),
        CommandHandler("control", control_panel_command),
        CommandHandler("report", report_command),
    ]


def get_callback_handlers():
    """Возвращает список обработчиков callback-запросов."""
    return [CallbackQueryHandler(callback_router)]


def get_message_handlers():
    """
    Возвращает обработчики текстовых сообщений.

    Импортируем лениво, чтобы не падать, если модуль настроек недоступен.
    """
    if importlib.util.find_spec("bot.handlers.settings_handlers") is None:
        return []

    from bot.handlers.settings_handlers import handle_setting_value

    return [MessageHandler(Filters.text & ~Filters.command, handle_setting_value)]


__all__ = [
    "get_command_handlers",
    "get_callback_handlers",
    "get_message_handlers",
]
