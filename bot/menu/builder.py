"""
/bot/menu/builder.py
Server Monitoring System v4.13.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu builder
Система мониторинга серверов
Версия: 4.13.5
Автор: Александр Суханов (c)
Лицензия: MIT
Построитель меню
"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.base import base_handler
from lib.logging import debug_log

class MenuBuilder:
    """Класс для построения меню бота"""
    
    def __init__(self):
        self.debug_log = debug_log
    
    def setup_menu(self, bot):
        """Настройка меню бота"""
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
                self.debug_log("❌ Менеджер расширений недоступен")
            
            bot.set_my_commands(commands)
            self.debug_log("✅ Меню настроено успешно")
            return True
        except Exception as e:
            self.debug_log(f"❌ Ошибка настройки меню: {e}")
            return False
    
    def build_main_menu(self):
        """Строит главное меню"""
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить все серверы", callback_data='manual_check')],
            [InlineKeyboardButton("📊 Проверить все ресурсы", callback_data='check_resources')],
            [InlineKeyboardButton("🔍 Проверить один сервер", callback_data='show_availability_menu')],
            [InlineKeyboardButton("📈 Ресурсы одного сервера", callback_data='show_resources_menu')],
            [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
            [InlineKeyboardButton("🐛 Отладка", callback_data='debug_menu')],
        ]
        
        # Добавляем бэкапы если расширение включено
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
    
    def build_control_menu(self):
        """Строит меню управления"""
        from core.monitor import monitoring_active
        
        monitoring_button = InlineKeyboardButton(
            "⏸️ Приостановить мониторинг" if monitoring_active else "▶️ Возобновить мониторинг",
            callback_data='toggle_monitoring'
        )
        
        keyboard = [
            [monitoring_button],
            [InlineKeyboardButton("📊 Утренний отчет", callback_data='full_report')],
            [InlineKeyboardButton("🔇 Управление тихим режимом", callback_data='silent_status')],
            [InlineKeyboardButton("🔧 Диагностика отчета", callback_data='debug_report')],
            base_handler.create_back_button('main_menu'),
            base_handler.create_close_button()
        ]
        
        return base_handler.create_keyboard(*keyboard)
    
    def build_resources_menu(self):
        """Строит меню проверки ресурсов"""
        keyboard = [
            [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
            [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
            [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
            [InlineKeyboardButton("🐧 Linux серверы", callback_data='check_linux')],
            [InlineKeyboardButton("🪟 Windows серверы", callback_data='check_windows')],
            [InlineKeyboardButton("📡 Другие серверы", callback_data='check_other')],
            base_handler.create_back_button('main_menu'),
            base_handler.create_close_button()
        ]
        
        return base_handler.create_keyboard(*keyboard)
    
    def show_main_menu(self, update, context):
        """Показывает главное меню"""
        welcome_text = (
            "🤖 *Серверный мониторинг*\n\n"
            "✅ Система работает\n\n"
        )
        
        # Информация о отладке
        try:
            from config.settings import DEBUG_MODE
            welcome_text += f"🐛 *Режим отладки:* {'🟢 ВКЛ' if DEBUG_MODE else '🔴 ВЫКЛ'}\n"
        except ImportError:
            welcome_text += "🐛 *Режим отладки:* 🔴 Недоступен\n"
        
        # Информация о веб-интерфейсе
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('web_interface'):
                welcome_text += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
                welcome_text += "_*доступен только в локальной сети_\n"
            else:
                welcome_text += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
        except ImportError:
            welcome_text += "🌐 *Веб-интерфейс:* 🔴 недоступен\n"
        
        reply_markup = self.build_main_menu()
        
        # Отправка сообщения в зависимости от типа обновления
        if update.message:
            update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
        elif update.callback_query:
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                welcome_text, 
                parse_mode='Markdown', 
                reply_markup=reply_markup
            )

# Создаем экземпляр построителя меню
menu_builder = MenuBuilder()