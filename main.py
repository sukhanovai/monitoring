#!/usr/bin/env python3
"""
Server Monitoring System v4.10.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.10.3
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

def get_telegram_token():
    """Получает токен Telegram из различных источников"""
    token_sources = [
        # 1. Прямой импорт из settings
        lambda: __import__('config.settings').TELEGRAM_TOKEN,
        # 2. Через db_settings
        lambda: __import__('config.db_settings').TELEGRAM_TOKEN,
        # 3. Из базы данных через config_manager
        lambda: __import__('core.config_manager').config_manager.get_setting('TELEGRAM_TOKEN', ''),
        # 4. Из переменной окружения
        lambda: os.environ.get('TELEGRAM_TOKEN', ''),
    ]
    
    for source in token_sources:
        try:
            token = source()
            if token and isinstance(token, str) and len(token) > 10:
                print(f"✅ Токен найден из источника {source.__name__ if hasattr(source, '__name__') else source}")
                return token
        except Exception:
            continue
    
    return ''

def setup_logging():
    """Настройка логирования"""
    # Проверяем наличие DEBUG_MODE
    debug_mode = False
    try:
        from config.settings import DEBUG_MODE
        debug_mode = DEBUG_MODE
    except ImportError:
        try:
            from config.db_settings import DEBUG_MODE
            debug_mode = DEBUG_MODE
        except ImportError:
            pass
    
    # Настраиваем логирование
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/opt/monitoring/logs/bot.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """Основная функция запуска"""
    logger = setup_logging()
    
    try:
        logger.info("🚀 Запуск системы мониторинга v4.9.2...")
        
        # Получаем токен Telegram
        TELEGRAM_TOKEN = get_telegram_token()
        
        if not TELEGRAM_TOKEN:
            logger.error("❌ Telegram токен не найден!")
            logger.error("Пожалуйста, установите токен одним из способов:")
            logger.error("1. В базе данных: INSERT INTO settings (key, value) VALUES ('TELEGRAM_TOKEN', 'ваш_токен')")
            logger.error("2. В config/settings.py: TELEGRAM_TOKEN = 'ваш_токен'")
            logger.error("3. В переменной окружения: export TELEGRAM_TOKEN='ваш_токен'")
            sys.exit(1)
        
        logger.info(f"✅ Telegram токен получен ({len(TELEGRAM_TOKEN)} символов)")
        
        # Инициализация модулей
        logger.info("🔄 Инициализация модулей...")
        
        from modules.targeted_checks import targeted_checks
        targeted_checks.get_all_servers()
        logger.info("✅ Модуль точечных проверок инициализирован")
        
        from core.monitor import monitor
        logger.info("✅ Основной мониторинг инициализирован")
        
        # Инициализация бота
        logger.info("🔄 Инициализация Telegram бота...")
        from telegram.ext import Updater
        
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        logger.info("✅ Бот инициализирован")
        
        # Настройка меню (старая структура для совместимости)
        logger.info("🔄 Настройка меню...")
        try:
            from bot_menu import setup_menu, get_handlers, get_callback_handlers
            
            setup_menu(updater.bot)
            logger.info("✅ Меню настроено")
            
            for handler in get_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Обработчики команд добавлены")
            
            for handler in get_callback_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Callback обработчики добавлены")
            
        except ImportError as e:
            logger.error(f"❌ Ошибка импорта обработчиков: {e}")
            raise
        
        # Добавляем обработчики настроек
        try:
            from settings_handlers import get_settings_handlers
            for handler in get_settings_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Обработчики настроек добавлены")
        except ImportError as e:
            logger.warning(f"⚠️ Обработчики настроек недоступны: {e}")
        
        # Настраиваем обработчики расширений
        try:
            from extensions.extension_manager import extension_manager
            
            # Бэкапы
            if extension_manager.is_extension_enabled('backup_monitor'):
                from extensions.backup_monitor.bot_handler import setup_backup_handlers
                setup_backup_handlers(dispatcher)
                logger.info("✅ Обработчики бэкапов настроены")
            
            # Веб-интерфейс
            if extension_manager.is_extension_enabled('web_interface'):
                from extensions.web_interface import start_web_server
                web_thread = threading.Thread(target=start_web_server, daemon=True)
                web_thread.start()
                logger.info("✅ Веб-сервер запущен")
                
        except ImportError as e:
            logger.warning(f"⚠️ Расширения недоступны: {e}")
        
        # Запускаем сбор статистики
        try:
            from extensions.utils import save_monitoring_stats
            save_monitoring_stats()
            logger.info("✅ Сбор статистики запущен")
        except ImportError:
            logger.warning("⚠️ Модуль статистики недоступен")
        
        # Запускаем основной мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=monitor.start, daemon=True)
        monitor_thread.start()
        logger.info("✅ Основной мониторинг запущен")
        
        # Запускаем бота
        updater.start_polling()
        logger.info("✅ Бот запущен и работает")
        
        # Отправляем стартовое сообщение
        try:
            from lib.alerts import send_alert
            send_alert("🟢 *Мониторинг серверов запущен*\n\nИспользуется новая модульная структура v4.9.2", force=True)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить стартовое сообщение: {e}")
        
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