"""
/bot/menu/builder.py
Server Monitoring System v8.33.61
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
The place where keyboards are made.
Система мониторинга серверов
Версия: 8.33.61
Автор: Александр Суханов (c)
Лицензия: MIT
Место, где строятся клавиатуры
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(extension_manager):
    keyboard = [
        [InlineKeyboardButton("🌅 Утренний отчет", callback_data='daily_report')],
        [InlineKeyboardButton("🔄 Доступность всех серверов", callback_data='manual_check')],
        [InlineKeyboardButton("🔍 Доступность сервера", callback_data='show_availability_menu')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("📊 Ресурсы сервера", callback_data='check_resources')])

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append(
            [InlineKeyboardButton("💾 Бэкапы Proxmox", callback_data='backup_hosts')]
        )

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append(
            [InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')]
        )

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append(
            [InlineKeyboardButton("📬 Бэкапы почты", callback_data='backup_mail')]
        )

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append(
            [InlineKeyboardButton("📦 Остатки 1С", callback_data='backup_stock_loads')]
        )

    if extension_manager.is_extension_enabled('supplier_stock_files'):
        keyboard.append(
            [InlineKeyboardButton("📦 Результаты остатков поставщиков", callback_data='supplier_stock_reports')]
        )

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append(
            [InlineKeyboardButton("🧊 ZFS", callback_data='zfs_menu')]
        )

    keyboard.extend([
        [InlineKeyboardButton("🛠️ Расширения", callback_data='extensions_menu')],
        [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings_main')],
        [InlineKeyboardButton("ℹ️ О боте", callback_data='about_bot')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
    ])

    return InlineKeyboardMarkup(keyboard)
