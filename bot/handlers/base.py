"""
/bot/handlers/base.py
Server Monitoring System v4.13.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Base handlers
Система мониторинга серверов
Версия: 4.13.2
Автор: Александр Суханов (c)
Лицензия: MIT
Базовые обработчики
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from lib.logging import debug_log
from config.settings import CHAT_IDS

def check_access(chat_id):
    """Проверка доступа к боту"""
    return str(chat_id) in CHAT_IDS

class BaseHandler:
    """Базовый класс для всех обработчиков"""
    
    def __init__(self):
        self.debug_log = debug_log
    
    def access_check_decorator(self, func):
        """Декоратор для проверки доступа"""
        def wrapper(update, context, *args, **kwargs):
            if not check_access(update.effective_chat.id):
                if update.message:
                    update.message.reply_text("⛔ У вас нет прав для использования этого бота")
                elif update.callback_query:
                    update.callback_query.answer("⛔ У вас нет прав")
                    update.callback_query.edit_message_text("⛔ У вас нет прав для использования этого бота")
                return
            return func(update, context, *args, **kwargs)
        return wrapper
    
    def create_back_button(self, callback_data='main_menu'):
        """Создает кнопку 'Назад'"""
        return [InlineKeyboardButton("↩️ Назад", callback_data=callback_data)]
    
    def create_close_button(self, callback_data='close'):
        """Создает кнопку 'Закрыть'"""
        return [InlineKeyboardButton("✖️ Закрыть", callback_data=callback_data)]
    
    def create_keyboard_row(self, *buttons):
        """Создает ряд кнопок"""
        return list(buttons)
    
    def create_keyboard(self, *rows):
        """Создает клавиатуру"""
        keyboard = []
        for row in rows:
            if isinstance(row, list):
                keyboard.append(row)
            else:
                keyboard.append([row])
        return InlineKeyboardMarkup(keyboard)

# Создаем экземпляр базового обработчика
base_handler = BaseHandler()