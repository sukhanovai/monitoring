"""
/bot/handlers/callbacks.py
Server Monitoring System v4.14.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
A single router for callbacks.
Система мониторинга серверов
Версия: 4.14.1
Автор: Александр Суханов (c)
Лицензия: MIT
Единый router callback’ов.
"""

from bot.menu.handlers import show_main_menu
from settings_handlers import settings_callback_handler
from monitor_core import (
    manual_check_handler,
    monitor_status,
    silent_status_handler,
    control_panel_handler,
    toggle_monitoring_handler,
)


def callback_router(update, context):
    query = update.callback_query
    data = query.data

    # Меню
    if data == 'main_menu':
        show_main_menu(update, context)

    # Мониторинг
    elif data == 'manual_check':
        manual_check_handler(update, context)

    elif data == 'monitor_status':
        monitor_status(update, context)

    elif data == 'silent_status':
        silent_status_handler(update, context)

    elif data == 'control_panel':
        control_panel_handler(update, context)

    elif data == 'toggle_monitoring':
        toggle_monitoring_handler(update, context)

    # Настройки
    elif data.startswith('settings_'):
        settings_callback_handler(update, context)

    # Закрытие
    elif data == 'close':
        try:
            query.delete_message()
        except:
            query.edit_message_text("✅ Закрыто")

    else:
        query.answer("⚠️ Неизвестное действие")
