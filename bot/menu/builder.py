"""
/bot/menu/builder.py
Server Monitoring System v5.3.15
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
The place where keyboards are made.
Система мониторинга серверов
Версия: 5.3.15
Автор: Александр Суханов (c)
Лицензия: MIT
Место, где строятся клавиатуры
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(extension_manager):
    keyboard = [
        [InlineKeyboardButton("🔄 Доступность всех серверов", callback_data='manual_check')],
        [InlineKeyboardButton("🔍 Доступность сервера", callback_data='show_availability_menu')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings_main')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("📊 Ресурсы сервера", callback_data='check_resources')])

    if (extension_manager.is_extension_enabled('backup_monitor') or
            extension_manager.is_extension_enabled('database_backup_monitor')):
        keyboard.append(
            [InlineKeyboardButton("💾 Бэкапы", callback_data='backup_main')]
        )

    keyboard.extend([
        [InlineKeyboardButton("🛠️ Расширения", callback_data='extensions_menu')],
        [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
    ])

    return InlineKeyboardMarkup(keyboard)
