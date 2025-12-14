#!/usr/bin/env python3
"""
Server Monitoring System v4.8.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.8.1
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import os
import sys
import time
import logging
from datetime import datetime
from app.modules.targeted_checks import targeted_checks

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

# Используем старый импорт для обратной совместимости
from app.utils.common import debug_log, progress_bar, format_duration, safe_import, DEBUG_MODE

def setup_logging():
    """Настройка логирования с учетом отладки - временная функция"""
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/opt/monitoring/bot_debug.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def main():
    """Основная функция запуска"""
    try:
        logger.info("🚀 Запуск мониторинга...")
        
        # Инициализируем модули
        targeted_checks.get_all_servers()  # Предзагрузка кэша
        logger.info("✅ Модуль точечных проверок инициализирован")
        
        # Ленивая загрузка конфигурации
        from app.config.settings import TELEGRAM_TOKEN
        
        # Инициализация бота
        from telegram.ext import Updater
        import threading

        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        # Настройка меню
        from bot_menu import setup_menu, get_handlers, get_callback_handlers
        setup_menu(updater.bot)

        # Добавляем обработчики
        for handler in get_handlers():
            dispatcher.add_handler(handler)

        for handler in get_callback_handlers():
            dispatcher.add_handler(handler)

        # Добавляем обработчики настроек
        try:
            from settings_handlers import get_settings_handlers
            for handler in get_settings_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Обработчики настроек добавлены")
        except ImportError as e:
            logger.warning(f"⚠️ Обработчики настроек недоступны: {e}")

        # Ленивая загрузка расширений
        from extensions.extension_manager import extension_manager
        
        # Настраиваем обработчики бэкапов если расширение включено
        if extension_manager.is_extension_enabled('backup_monitor'):
            from extensions.backup_monitor.bot_handler import setup_backup_handlers
            setup_backup_handlers(dispatcher)
            logger.info("✅ Обработчики бэкапов настроены")

        # Запускаем веб-сервер если расширение включено
        if extension_manager.is_extension_enabled('web_interface'):
            from extensions.web_interface import start_web_server
            web_thread = threading.Thread(target=start_web_server, daemon=True)
            web_thread.start()
            logger.info("✅ Веб-сервер запущен")

        # Запускаем сбор статистики
        from extensions.utils import save_monitoring_stats
        save_monitoring_stats()
        logger.info("✅ Сбор статистики запущен")

        # Запускаем основной мониторинг
        from monitor_core import start_monitoring
        monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
        monitor_thread.start()
        logger.info("✅ Основной мониторинг запущен")

        # Запускаем бота
        updater.start_polling()
        logger.info("✅ Бот запущен и работает")

        # Блокируем основной поток
        updater.idle()

    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        
        # Попытка graceful shutdown
        try:
            updater.stop()
        except:
            pass

if __name__ == "__main__":
    main()