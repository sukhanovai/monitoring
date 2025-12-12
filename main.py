#!/usr/bin/env python3
"""
Server Monitoring System v4.2.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Основной модуль запуска
Версия: 4.2.2
"""

import os
import sys
import time
import logging
from datetime import datetime

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

print(f"DEBUG_MODE из common.py: {app.utils.common.DEBUG_MODE}")

# Импортируем из новой структуры
try:
    from app.utils.common import debug_log, add_python_path, ensure_directory
    print("✅ Утилиты загружены из новой структуры")
except ImportError as e:
    print(f"❌ Ошибка импорта утилит: {e}")
    # Используем локальные функции как запасной вариант
    def debug_log(message, force=False):
        print(f"[DEBUG] {message}")
    
    def add_python_path(path):
        if path not in sys.path:
            sys.path.insert(0, path)
    
    def ensure_directory(path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)


def setup_logging():
    """Настройка логирования с учетом отладки"""
    try:
        from app.config import settings
        log_level = logging.DEBUG if settings.DEBUG_MODE else logging.INFO
        print(f"✅ Настройки загружены, DEBUG_MODE={settings.DEBUG_MODE}")
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать настройки: {e}")
        # Используем переменную окружения как запасной вариант
        log_level = logging.DEBUG if os.environ.get('DEBUG_MODE') == 'True' else logging.INFO

    # Создаем директорию для логов если ее нет
    ensure_directory('/opt/monitoring/logs')
    
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
        logger.info("🚀 Запуск оптимизированной версии мониторинга...")
        
        # Тестируем основные импорты
        logger.info("🧪 Тестируем основные импорты...")
        
        try:
            from app.config import settings
            logger.info(f"✅ Конфигурация загружена: TELEGRAM_TOKEN={'установлен' if settings.TELEGRAM_TOKEN else 'нет'}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            return
        
        try:
            from app.core.monitoring import start_monitoring
            logger.info("✅ Ядро мониторинга загружено")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки ядра мониторинга: {e}")
            return
        
        try:
            from app.core.checker import server_checker
            logger.info("✅ Checker загружен")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки checker: {e}")
            return
        
        # Инициализация бота
        from telegram.ext import Updater
        import threading

        updater = Updater(token=settings.TELEGRAM_TOKEN, use_context=True)
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

        # Запускаем основной мониторинг (из новой структуры)
        logger.info("🔄 Запуск основного цикла мониторинга...")
        from app.core.monitoring import start_monitoring
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
