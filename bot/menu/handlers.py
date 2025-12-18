"""
/bot/menu/handlers.py
Server Monitoring System v4.14.14
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Displaying the menu (without any logic)
Система мониторинга серверов
Версия: 4.14.14
Автор: Александр Суханов (c)
Лицензия: MIT
Отображение меню (без логики)
"""

from bot.menu.builder import main_menu
from bot.handlers.base import check_access, deny_access
from extensions.extension_manager import extension_manager


def show_main_menu(update, context):
    if not check_access(update):
        deny_access(update)
        return

    text = (
        "🤖 *Серверный мониторинг*\n\n"
        "✅ Система активна"
    )

    if update.message:
        update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=main_menu(extension_manager)
        )
    else:
        update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=main_menu(extension_manager)
        )
