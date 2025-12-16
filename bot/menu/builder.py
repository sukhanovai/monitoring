"""
Server Monitoring System v4.11.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu builder
Система мониторинга серверов
Версия: 4.11.3
Автор: Александр Суханов (c)
Лицензия: MIT
Построитель меню бота
"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from lib.logging import debug_log
from extensions.extension_manager import extension_manager

def setup_menu(bot):
    """Настройка меню бота с ленивой загрузкой расширений"""
    try:
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
            BotCommand("check_server", "🔍 Проверить один сервер"),
            BotCommand("check_res", "📊 Ресурсы одного сервера"),
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
        debug_log("✅ Меню настроено успешно")
        return True
    except Exception as e:
        debug_log(f"❌ Ошибка настройки меню: {e}")
        return False

def build_main_menu_keyboard():
    """Построение главного меню"""
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить все серверы", callback_data='manual_check')],
        [InlineKeyboardButton("📊 Проверить все ресурсы", callback_data='check_resources')],
        [InlineKeyboardButton("🔍 Проверить один сервер", callback_data='show_availability_menu')],
        [InlineKeyboardButton("📈 Ресурсы одного сервера", callback_data='show_resources_menu')],
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

def build_extensions_menu(extensions_status):
    """Построение меню управления расширениями"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    
    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']
        
        toggle_text = "🔴 Выключить" if enabled else "🟢 Включить"
        
        # Добавляем кнопку переключения для каждого расширения
        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}", 
                callback_data=f'ext_toggle_{ext_id}'
            )
        ])
    
    # Добавляем кнопки управления
    keyboard.extend([
        [InlineKeyboardButton("📊 Включить все", callback_data='ext_enable_all')],
        [InlineKeyboardButton("📋 Отключить все", callback_data='ext_disable_all')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def build_debug_menu():
    """Построение меню управления отладкой"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    from config.settings import DEBUG_MODE
    toggle_text = "🔴 Выключить отладку" if DEBUG_MODE else "🟢 Включить отладку"
    toggle_data = 'debug_disable' if DEBUG_MODE else 'debug_enable'

    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("📊 Статус системы", callback_data='debug_status')],
        [InlineKeyboardButton("🗑️ Очистить логи", callback_data='debug_clear_logs')],
        [InlineKeyboardButton("📋 Диагностика", callback_data='debug_diagnose')],
        [InlineKeyboardButton("🔧 Расширенная отладка", callback_data='debug_advanced')],
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def add_quick_check_buttons(keyboard, server_ip=None):
    """Добавляет кнопки быстрой проверки в клавиатуру"""
    if server_ip:
        keyboard.append([
            InlineKeyboardButton("🔍 Проверить доступность", callback_data=f'check_availability_{server_ip}'),
            InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f'check_resources_{server_ip}')
        ])
    
    keyboard.append([
        InlineKeyboardButton("🎛️ Главное меню", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])
    
    return keyboard

def create_quick_actions_menu(server_ip):
    """Создает меню быстрых действий для сервера"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить доступность", callback_data=f'check_availability_{server_ip}')],
        [InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f'check_resources_{server_ip}')],
        [InlineKeyboardButton("📋 Информация о сервере", callback_data=f'server_info_{server_ip}')],
        [InlineKeyboardButton("🔄 Проверить снова", callback_data=f'check_availability_{server_ip}')],
        [InlineKeyboardButton("🎛️ Главное меню", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    return InlineKeyboardMarkup(keyboard)