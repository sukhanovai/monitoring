"""
Server Monitoring System v4.4.2 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Меню управления отладкой
Версия: 4.4.2
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
import subprocess
import socket
from datetime import datetime

class DebugMenu:
    """Меню управления отладкой"""
    
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
    
    def show_menu(self, update, context):
        """Показать меню отладки"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        chat_id = query.message.chat_id if query else update.message.chat_id
        
        debug_status = "🟢 ВКЛЮЧЕНА" if self.debug_mode else "🔴 ВЫКЛЮЧЕНА"
        
        message = "🐛 *Управление отладкой*\n\n"
        message += f"*Текущий статус:* {debug_status}\n\n"
        
        toggle_text = "🔴 Выключить отладку" if self.debug_mode else "🟢 Включить отладку"
        toggle_data = 'debug_disable' if self.debug_mode else 'debug_enable'

        keyboard = [
            [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
            [InlineKeyboardButton("📊 Статус системы", callback_data='debug_status')],
            [InlineKeyboardButton("🗑️ Очистить логи", callback_data='debug_clear_logs')],
            [InlineKeyboardButton("📋 Диагностика", callback_data='debug_diagnose')],
            [InlineKeyboardButton("🔧 Расширенная отладка", callback_data='debug_advanced')],
            [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    def handle_callback(self, update, context):
        """Обработчик callback-ов отладки"""
        query = update.callback_query
        data = query.data
        
        if data == 'debug_enable':
            self.enable_debug_mode(query)
        elif data == 'debug_disable':
            self.disable_debug_mode(query)
        elif data == 'debug_status':
            self.show_debug_status(query)
        elif data == 'debug_clear_logs':
            self.clear_debug_logs(query)
        elif data == 'debug_diagnose':
            self.run_diagnostic(query)
        elif data == 'debug_advanced':
            self.show_advanced_debug(query)
        elif data == 'debug_menu':
            self.show_menu(update, context)
    
    def enable_debug_mode(self, query):
        """Включить режим отладки"""
        try:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
            
            self.debug_mode = True
            debug_log("🟢 Отладка включена через меню бота")
            
            query.edit_message_text(
                "🟢 *Отладка включена*\n\n"
                "Теперь все операции будут детально логироваться.",
                parse_mode='Markdown',
                reply_markup=self._get_back_to_debug_keyboard()
            )
        except Exception as e:
            query.edit_message_text(f"❌ Ошибка включения отладки: {e}")
    
    # Добавьте остальные методы по аналогии...
    
    def _get_back_to_debug_keyboard(self):
        """Получить клавиатуру для возврата в меню отладки"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')]
        ])

# Глобальный экземпляр
debug_menu = DebugMenu()
