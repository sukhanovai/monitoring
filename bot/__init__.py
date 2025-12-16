"""
/bot/menu/__init__.py
Server Monitoring System v4.13.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot package
Система мониторинга серверов
Версия: 4.13.1
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет Telegram бота
"""

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

def initialize_bot():
    """Инициализирует бота"""
    from bot.handlers.commands import get_command_handlers
    from bot.handlers.callbacks import get_callback_handlers
    from bot.menu.builder import menu_builder
    from config.settings import TELEGRAM_TOKEN
    from lib.logging import debug_log
    
    try:
        # Создаем Updater и Dispatcher
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Регистрируем обработчики команд
        for handler in get_command_handlers():
            dispatcher.add_handler(handler)
        
        # Регистрируем обработчики callback-запросов
        for handler in get_callback_handlers():
            dispatcher.add_handler(handler)
        
        # Настраиваем меню
        menu_builder.setup_menu(updater.bot)
        
        debug_log("✅ Бот инициализирован успешно")
        return updater
        
    except Exception as e:
        debug_log(f"❌ Ошибка инициализации бота: {e}")
        raise