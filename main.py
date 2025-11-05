#!/usr/bin/env python3
"""
Server Monitoring System v1.3.0
Copyright (c) 2024 Aleksandr Sukhanov
License: MIT
"""
import os
import sys
import time
import logging
import signal
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/monitoring/bot_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска"""
    try:
        sys.path.insert(0, '/opt/monitoring')
        
        from config import TELEGRAM_TOKEN
        from bot_menu import setup_menu, get_handlers, get_callback_handlers
        from extensions.web_interface import start_web_server
        from extensions.stats_collector import save_monitoring_stats
        from monitor_core import start_monitoring
        
        from telegram.ext import Application
        import threading
        
        logger.info("🚀 Запуск полной версии мониторинга...")
        
        # Инициализируем бота с новой версией API
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Настраиваем меню
        setup_menu(application.bot)
        
        # Добавляем обработчики
        for handler in get_handlers():
            application.add_handler(handler)
            
        for handler in get_callback_handlers():
            application.add_handler(handler)
        
        # Настраиваем обработчики бэкапов
        from extensions.backup_monitor.bot_handler import setup_backup_handlers
        setup_backup_handlers(application)
        
        # Запускаем веб-сервер в отдельном потоке
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        logger.info("✅ Веб-сервер запущен")
        
        # Запускаем сбор статистики
        save_monitoring_stats()
        logger.info("✅ Сбор статистики запущен")
        
        # Запускаем основной мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
        monitor_thread.start()
        logger.info("✅ Основный мониторинг запущен")
        
        # Запускаем бота
        application.run_polling()
        logger.info("✅ Бот запущен и работает")
        
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    