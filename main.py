#!/usr/bin/env python3
"""
Server Monitoring System v4.4.11
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Основной модуль запуска

"""

import os
import sys
import time
import logging
from datetime import datetime
from app.bot.callbacks import callback_router

print("🚀 Начало запуска мониторинга...")

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

# Импортируем из новой структуры
try:
    from app import debug_log, DEBUG_MODE
    from app.utils.common import add_python_path, ensure_directory
    print(f"✅ Утилиты загружены (DEBUG_MODE={DEBUG_MODE})")
except ImportError as e:
    print(f"⚠️ Используем fallback функции: {e}")
    def debug_log(message, force=False):
        print(f"[DEBUG] {message}")
    
    def add_python_path(path):
        if path not in sys.path:
            sys.path.insert(0, path)
    
    def ensure_directory(path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    
    DEBUG_MODE = False

# Настраиваем логирование
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
ensure_directory('/opt/monitoring/logs')

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/monitoring/bot_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_imports():
    """Тестируем все необходимые импорты"""
    logger.info("🧪 Тестируем импорты...")
    
    imports_to_test = [
        ("app.config.settings", "TELEGRAM_TOKEN"),
        ("app.core.monitoring", "start_monitoring"),
        ("app.core.checker", "server_checker"),
        ("app.bot.handlers", "manual_check_handler"),
        ("app.bot.menus", "setup_menu_commands"),
        ("extensions.extension_manager", "extension_manager"),
    ]
    
    for module, attr in imports_to_test:
        try:
            if attr:
                exec(f"from {module} import {attr}")
                logger.info(f"✅ {module}.{attr}")
            else:
                exec(f"import {module}")
                logger.info(f"✅ {module}")
        except Exception as e:
            logger.error(f"❌ {module}.{attr}: {e}")
            return False
    
    return True

def main():
    """Основная функция запуска"""
    logger.info("🚀 Запуск оптимизированной версии мониторинга...")
    
    if not test_imports():
        logger.error("❌ Критические ошибки импорта. Завершаем работу.")
        return
    
    try:
        from app.config import settings
        from telegram.ext import Updater
        import threading
        from app.core.monitoring import monitoring_core, start_monitoring
        
        # ТЕСТИРУЕМ ИНИЦИАЛИЗАЦИЮ СЕРВЕРОВ ПРИ ЗАПУСКЕ
        logger.info("🔍 Тестируем инициализацию серверов...")
        try:
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            logger.info(f"✅ Получено серверов: {len(servers)}")
            for i, server in enumerate(servers[:3]):  # Покажем первые 3
                logger.info(f"  {i+1}. {server['name']} ({server['ip']}) тип: {server.get('type', 'ssh')}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации серверов: {e}")
        
        # Импортируем extension_manager здесь
        from extensions.extension_manager import extension_manager
        
        # Инициализация бота
        updater = Updater(token=settings.TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        # Настройка меню
        from app.bot.menus import setup_menu_commands
        setup_menu_commands(updater.bot, extension_manager)

        # Получаем обработчики
        from app.bot.handlers import get_handlers
        from app.bot.callbacks import callback_router
        
        # Добавляем обработчики
        for handler in get_handlers():
            dispatcher.add_handler(handler)

        for handler in callback_router.get_handlers():
            dispatcher.add_handler(handler)

        # Добавляем обработчики настроек
        try:
            from settings_handlers import get_settings_handlers
            for handler in get_settings_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Обработчики настроек добавлены")
        except ImportError as e:
            logger.warning(f"⚠️ Обработчики настроек недоступны: {e}")

        # Расширения
        if extension_manager.is_extension_enabled('backup_monitor'):
            from extensions.backup_monitor.bot_handler import setup_backup_handlers
            setup_backup_handlers(dispatcher)
            logger.info("✅ Обработчики бэкапов настроены")

        if extension_manager.is_extension_enabled('web_interface'):
            from extensions.web_interface import start_web_server
            web_thread = threading.Thread(target=start_web_server, daemon=True)
            web_thread.start()
            logger.info("✅ Веб-сервер запущен")

        # Запускаем мониторинг
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
        
        try:
            updater.stop()
        except:
            pass

if __name__ == "__main__":
    main()
    