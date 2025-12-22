"""
/bot/handlers/commands.py
Server Monitoring System v4.15.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Only commands, no inline buttons.
Система мониторинга серверов
Версия: 4.15.0
Автор: Александр Суханов (c)
Лицензия: MIT
Только команды, никаких inline-кнопок
"""

from bot.menu.handlers import show_main_menu
from bot.handlers.base import check_access, deny_access
from monitor_core import (
    manual_check_handler,
    monitor_status,
    silent_command,
    control_command,
    send_morning_report_handler,
)


def start_command(update, context):
    show_main_menu(update, context)


def help_command(update, context):
    if not check_access(update):
        deny_access(update)
        return

    update.message.reply_text(
        "ℹ️ Используйте меню для управления мониторингом",
        parse_mode='Markdown'
    )


def check_command(update, context):
    manual_check_handler(update, context)


def status_command(update, context):
    monitor_status(update, context)


def silent_mode_command(update, context):
    silent_command(update, context)


def control_panel_command(update, context):
    control_command(update, context)


def report_command(update, context):
    send_morning_report_handler(update, context)
