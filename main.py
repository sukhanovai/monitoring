#!/usr/bin/env python3
"""
Server Monitoring System v4.7.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.7.0
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import os
import sys
import threading
from app.utils.logging import setup_logging

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

def main():
    """Основная функция запуска с новой структурой"""
    logger = setup_logging()
    
    try:
        logger.info("🚀 Запуск мониторинга v4.7.0...")
        
        # Инициализация Telegram бота
        from app.config.settings import TELEGRAM_TOKEN
        from telegram.ext import Updater
        
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Настройка меню бота
        from bot_menu import setup_menu, get_handlers, get_callback_handlers
        setup_menu(updater.bot)
        
        # Добавление обработчиков
        for handler in get_handlers():
            dispatcher.add_handler(handler)
        
        for handler in get_callback_handlers():
            dispatcher.add_handler(handler)
        
        # Запуск модулей мониторинга
        logger.info("🔄 Запуск модулей мониторинга...")
        
        # Модуль доступности
        from app.modules.availability import availability_monitor
        availability_thread = threading.Thread(
            target=availability_monitor.start_monitoring,
            daemon=True
        )
        availability_thread.start()
        logger.info("✅ Модуль доступности запущен")
        
        # Модуль утреннего отчета
        from app.modules.morning_report import morning_report
        report_thread = threading.Thread(
            target=morning_report.start_scheduler,
            daemon=True
        )
        report_thread.start()
        logger.info("✅ Модуль утреннего отчета запущен")
        
        # Модуль ресурсов
        from app.modules.resources import resource_monitor
        resource_thread = threading.Thread(
            target=resource_monitor.start_automatic_checks,
            daemon=True
        )
        resource_thread.start()
        logger.info("✅ Модуль ресурсов запущен")
        
        # Запуск расширений
        from extensions.extension_manager import extension_manager
        
        if extension_manager.is_extension_enabled('web_interface'):
            from extensions.web_interface import start_web_server
            web_thread = threading.Thread(target=start_web_server, daemon=True)
            web_thread.start()
            logger.info("✅ Веб-сервер запущен")
        
        # Запуск бота
        updater.start_polling()
        logger.info("✅ Бот запущен и работает")
        
        # Блокируем основной поток
        updater.idle()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()