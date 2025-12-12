"""
Server Monitoring System v4.4.0 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Модуль для настройки команд и главного меню
Версия: 4.4.0
"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

def setup_menu_commands(bot, extension_manager):
    """Настройка команд меню бота"""
    commands = [
        BotCommand("start", "Запуск бота"),
        BotCommand("check", "Проверить серверы"),
        BotCommand("status", "Статус мониторинга"),
        BotCommand("servers", "Список серверов"),
        BotCommand("report", "Ежедневный отчет"),
        BotCommand("stats", "Статистика"),
        BotCommand("control", "Управление"),
        BotCommand("diagnose_ssh", "Диагностика SSH"),
        BotCommand("silent", "Тихий режим"),
        BotCommand("extensions", "🛠️ Управление расширениями"),
        BotCommand("settings", "⚙️ Управление настройками"),
        BotCommand("debug", "🐛 Управление отладкой"),
        BotCommand("help", "Помощь"),
    ]
    
    # Динамическое добавление команд расширений
    if extension_manager.is_extension_enabled('backup_monitor'):
        commands.extend([
            BotCommand("backup", "📊 Бэкапы"),
            BotCommand("backup_search", "🔍 Поиск бэкапов"),
            BotCommand("backup_help", "❓ Помощь по бэкапам"),
        ])
    
    if extension_manager.is_extension_enabled('database_backup_monitor'):
        commands.append(BotCommand("db_backups", "🗃️ Бэкапы БД"))
    
    bot.set_my_commands(commands)
    return True

def create_main_menu(extension_manager):
    """Создание главного меню"""
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить серверы", callback_data='manual_check')],
        [InlineKeyboardButton("📊 Проверить ресурсы", callback_data='check_resources')],
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
        [InlineKeyboardButton("🐛 Отладка", callback_data='debug_menu')],
    ]
    
    if (extension_manager.is_extension_enabled('backup_monitor') or 
        extension_manager.is_extension_enabled('database_backup_monitor')):
        keyboard.append([InlineKeyboardButton("💾 Бэкапы", callback_data='backup_main')])
    
    keyboard.extend([
        [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')],
        [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')] 
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_start_message(extension_manager, debug_mode=False):
    """Получить приветственное сообщение"""
    welcome_text = (
        "🤖 *Серверный мониторинг*\n\n"
        "✅ Система работает\n\n"
    )
    
    welcome_text += f"🐛 *Режим отладки:* {'🟢 ВКЛ' if debug_mode else '🔴 ВЫКЛ'}\n"
    
    if extension_manager.is_extension_enabled('web_interface'):
        welcome_text += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
        welcome_text += "_*доступен только в локальной сети_\n"
    else:
        welcome_text += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
    
    return welcome_text

def get_help_message(extension_manager):
    """Получить сообщение помощи"""
    help_text = (
        "🤖 *Помощь по мониторингу*\n\n"
        "*Основные команды:*\n"
        "• `/start` - Главное меню\n"
        "• `/check` - Быстрая проверка серверов\n"
        "• `/servers` - Список всех серверов\n"
        "• `/control` - Управление мониторингом\n"
        "• `/extensions` - Управление расширениями\n"
        "• `/debug` - Управление отладкой 🆕\n\n"
        "*Диагностика:*\n"
        "• `/diagnose_ssh <ip>` - Проверка SSH подключения\n"
        "• `/silent` - Статус тихого режима\n\n"
        "*Отчеты:*\n"
        "• `/report` - Принудительная отправка утреннего отчета\n"
        "• `/stats` - Статистика работы\n\n"
    )
    
    if extension_manager.is_extension_enabled('backup_monitor'):
        help_text += "*Бэкапы Proxmox:*\n"
        help_text += "• `/backup` - Статус бэкапов\n"
        help_text += "• `/backup_search` - Поиск по бэкапам\n"
        help_text += "• `/backup_help` - Помощь по бэкапам\n\n"
    
    help_text += "*Веб-интерфейс:*\n"
    if extension_manager.is_extension_enabled('web_interface'):
        help_text += "🌐 http://192.168.20.2:5000\n"
        help_text += "_*доступен только в локальной сети_\n\n"
    else:
        help_text += "🔴 В настоящее время отключен\n\n"
    
    help_text += "*Используйте кнопки меню для удобного управления*"
    
    return help_text