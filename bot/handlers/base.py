"""
/bot/handlers/base.py
Server Monitoring System v4.12.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Base handlers for Telegram bot
Система мониторинга серверов
Версия: 4.12.1
Автор: Александр Суханов (c)
Лицензия: MIT
Базовые обработчики для Telegram бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lib.logging import debug_log
from config.settings import DEBUG_MODE

class BaseHandlers:
    """Базовые обработчики для бота"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
    
    def check_access(self, chat_id):
        """Проверка доступа к боту"""
        try:
            if self.config_manager:
                chat_ids = self.config_manager.get_setting('CHAT_IDS', [])
            else:
                from config.settings import CHAT_IDS
                chat_ids = CHAT_IDS
            
            return str(chat_id) in chat_ids
        except Exception as e:
            debug_log(f"Ошибка проверки доступа: {e}")
            return False
    
    def start_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        if not self.check_access(update.effective_chat.id):
            if update.message:
                update.message.reply_text("⛔ У вас нет прав для использования этого бота")
            elif update.callback_query:
                update.callback_query.answer("⛔ У вас нет прав")
                if update.callback_query.message:
                    update.callback_query.edit_message_text("⛔ У вас нет прав для использования этого бота")
            return
        
        # Заглушка - реализация будет в menu/handlers.py
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        return menu_handlers.show_main_menu(update, context)
    
    def help_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /help"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для использования этого бота")
            return
        
        help_text = (
            "🤖 *Помощь по мониторингу*\n\n"
            "*Основные команды:*\n"
            "• `/start` - Главное меню\n"
            "• `/check` - Быстрая проверка серверов\n"
            "• `/servers` - Список всех серверов\n"
            "• `/control` - Управление мониторингом\n"
            "• `/extensions` - Управление расширениями\n"
            "• `/debug` - Управление отладкой\n\n"
            "*Диагностика:*\n"
            "• `/diagnose_ssh <ip>` - Проверка SSH подключения\n"
            "• `/silent` - Статус тихого режима\n\n"
            "*Отчеты:*\n"
            "• `/report` - Принудительная отправка утреннего отчета\n"
            "• `/stats` - Статистика работы\n\n"
            "*Веб-интерфейс:*\n"
        )
        
        # Проверяем доступность веб-интерфейса через менеджер расширений
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('web_interface'):
                help_text += "🌐 http://192.168.20.2:5000\n"
                help_text += "_*доступен только в локальной сети_\n\n"
            else:
                help_text += "🔴 В настоящее время отключен\n\n"
        except ImportError:
            help_text += "🔴 Модуль расширений недоступен\n\n"
        
        help_text += "*Используйте кнопки меню для удобного управления*"
        
        update.message.reply_text(help_text, parse_mode='Markdown')
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Обработчик ошибок"""
        error_text = f"❌ Произошла ошибка: {context.error}"
        debug_log(f"Ошибка в боте: {context.error}")
        
        # Пытаемся отправить сообщение об ошибке
        try:
            if update and update.effective_chat:
                update.effective_chat.send_message(
                    "⚠️ Произошла ошибка при обработке команды. Попробуйте снова."
                )
        except:
            pass
        
        # Дополнительное логирование для серьезных ошибок
        import traceback
        debug_log(f"Traceback: {traceback.format_exc()}")