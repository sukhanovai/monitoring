"""
/bot/menu/builder.py
Server Monitoring System v4.12.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu builder for Telegram bot
Система мониторинга серверов
Версия: 4.12.0
Автор: Александр Суханов (c)
Лицензия: MIT
Построитель меню для Telegram бота
"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from lib.logging import debug_log
from config.settings import DEBUG_MODE

class MenuBuilder:
    """Построитель меню бота"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
    
    def build_main_menu(self, update, context):
        """Создает главное меню"""
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить все серверы", callback_data='manual_check')],
            [InlineKeyboardButton("📊 Проверить все ресурсы", callback_data='check_resources')],
            [InlineKeyboardButton("🔍 Проверить один сервер", callback_data='show_availability_menu')],
            [InlineKeyboardButton("📈 Ресурсы одного сервера", callback_data='show_resources_menu')],
            [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
            [InlineKeyboardButton("🐛 Отладка", callback_data='debug_menu')],
        ]
        
        # Проверяем расширения
        try:
            from extensions.extension_manager import extension_manager
            
            if (extension_manager.is_extension_enabled('backup_monitor') or 
                extension_manager.is_extension_enabled('database_backup_monitor')):
                keyboard.append([InlineKeyboardButton("💾 Бэкапы", callback_data='backup_main')])
                
        except ImportError:
            pass
        
        keyboard.extend([
            [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')],
            [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_check_menu(self):
        """Создает меню проверки"""
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить все серверы", callback_data='manual_check')],
            [InlineKeyboardButton("📊 Проверить все ресурсы", callback_data='check_resources')],
            [InlineKeyboardButton("🔍 Проверить один сервер", callback_data='show_availability_menu')],
            [InlineKeyboardButton("📈 Ресурсы одного сервера", callback_data='show_resources_menu')],
            [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_resources_menu(self):
        """Создает меню проверки ресурсов"""
        keyboard = [
            [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
            [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
            [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
            [InlineKeyboardButton("🐧 Linux серверы", callback_data='check_linux')],
            [InlineKeyboardButton("🪟 Windows серверы", callback_data='check_windows')],
            [InlineKeyboardButton("📡 Другие серверы", callback_data='check_other')],
            [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_monitor_status_menu(self):
        """Создает меню статуса мониторинга"""
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить статус", callback_data='monitor_status')],
            [InlineKeyboardButton("🔍 Проверить сейчас", callback_data='manual_check')],
            [InlineKeyboardButton("🔇 Управление режимом", callback_data='silent_status')],
            [InlineKeyboardButton("📋 Список серверов", callback_data='servers_list')],
            [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_control_panel_menu(self, monitoring_active):
        """Создает панель управления"""
        monitoring_button = InlineKeyboardButton(
            "⏸️ Приостановить мониторинг" if monitoring_active else "▶️ Возобновить мониторинг",
            callback_data='toggle_monitoring'
        )
        
        keyboard = [
            [monitoring_button],
            [InlineKeyboardButton("📊 Утренний отчет", callback_data='full_report')],
            [InlineKeyboardButton("🔇 Управление тихим режимом", callback_data='silent_status')],
            [InlineKeyboardButton("🔧 Диагностика отчета", callback_data='debug_report')],
            [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_silent_menu(self, silent_override):
        """Создает меню тихого режима"""
        # Определяем текущий режим
        if silent_override is None:
            mode_text = "🔄 Автоматический"
        elif silent_override:
            mode_text = "🔇 Принудительно тихий"
        else:
            mode_text = "🔊 Принудительно громкий"
        
        keyboard = [
            [InlineKeyboardButton("🔇 Включить принудительно тихий", callback_data='force_silent')],
            [InlineKeyboardButton("🔊 Включить принудительно громкий", callback_data='force_loud')],
            [InlineKeyboardButton("🔄 Вернуть автоматический режим", callback_data='auto_mode')],
            [InlineKeyboardButton("↩️ Назад", callback_data='control_panel'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_debug_menu(self):
        """Создает меню отладки"""
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
    
    def build_extensions_menu(self, extensions_status):
        """Создает меню управления расширениями"""
        keyboard = []
        
        for ext_id, status_info in extensions_status.items():
            enabled = status_info['enabled']
            ext_info = status_info['info']
            
            toggle_text = "🔴 Выключить" if enabled else "🟢 Включить"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{toggle_text} {ext_info['name']}", 
                    callback_data=f'ext_toggle_{ext_id}'
                )
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("📊 Включить все", callback_data='ext_enable_all')],
            [InlineKeyboardButton("📋 Отключить все", callback_data='ext_disable_all')],
            [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def setup_bot_commands(self, bot):
        """Настраивает команды бота"""
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
            try:
                from extensions.extension_manager import extension_manager
                
                if extension_manager.is_extension_enabled('backup_monitor'):
                    commands.extend([
                        BotCommand("backup", "📊 Бэкапы"),
                        BotCommand("backup_search", "🔍 Поиск бэкапов"),
                        BotCommand("backup_help", "❓ Помощь по бэкапам"),
                    ])
                
                if extension_manager.is_extension_enabled('database_backup_monitor'):
                    commands.append(BotCommand("db_backups", "🗃️ Бэкапы БД"))
                    
            except ImportError:
                pass
            
            bot.set_my_commands(commands)
            debug_log("✅ Команды бота настроены успешно")
            return True
            
        except Exception as e:
            debug_log(f"❌ Ошибка настройки команд бота: {e}")
            return False