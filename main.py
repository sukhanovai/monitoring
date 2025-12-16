#!/usr/bin/env python3
"""
Server Monitoring System v4.10.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.10.2
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

# Импортируем новое логирование
from lib.logging import debug_log, setup_logging, set_debug_mode

def setup_environment():
    """Настройка окружения и логирования"""
    # Проверяем наличие DEBUG_MODE
    try:
        from config.settings import DEBUG_MODE
    except ImportError:
        # Если DEBUG_MODE нет в settings, ищем в других местах
        try:
            from config.db_settings import DEBUG_MODE
        except ImportError:
            # Используем значение по умолчанию
            DEBUG_MODE = False
    
    # Устанавливаем режим отладки
    set_debug_mode(DEBUG_MODE)
    
    # Настраиваем базовое логирование
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Настройка окружения...")
    
    return logger

def main():
    """Основная функция запуска - ОБНОВЛЕННАЯ"""
    logger = setup_environment()
    
    try:
        logger.info("🚀 Запуск системы мониторинга v4.9.2...")
        
        # Инициализация модулей
        from modules.targeted_checks import targeted_checks
        targeted_checks.get_all_servers()  # Предзагрузка кэша
        logger.info("✅ Модуль точечных проверок инициализирован")
        
        # Инициализация мониторинга
        from core.monitor import monitor
        logger.info("✅ Основной мониторинг инициализирован")
        
        # Инициализация бота
        from telegram.ext import Updater
        
        # Получаем токен из настроек
        try:
            from config.settings import TELEGRAM_TOKEN
        except ImportError:
            from config.db_settings import TELEGRAM_TOKEN
        
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Настройка меню (новая структура)
        try:
            from bot.menu.builder import setup_menu
            from bot.handlers.commands import get_command_handlers
            from bot.handlers.callbacks import get_callback_handlers
            
            # Настраиваем меню бота
            setup_menu(updater.bot)
            logger.info("✅ Меню бота настроено")
            
            # Добавляем обработчики команд
            for handler in get_command_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Обработчики команд добавлены")
            
            # Добавляем обработчики callback
            for handler in get_callback_handlers():
                dispatcher.add_handler(handler)
            logger.info("✅ Обработчики callback добавлены")
            
        except ImportError as e:
            logger.error(f"❌ Ошибка импорта новых обработчиков: {e}")
            logger.info("🔄 Пробуем использовать старые обработчики...")
            
            # Запасной вариант: старые обработчики
            try:
                from bot_menu import setup_menu, get_handlers, get_callback_handlers
                
                setup_menu(updater.bot)
                for handler in get_handlers():
                    dispatcher.add_handler(handler)
                for handler in get_callback_handlers():
                    dispatcher.add_handler(handler)
                
                logger.info("✅ Используются старые обработчики для совместимости")
            except ImportError as e2:
                logger.error(f"❌ Ошибка импорта старых обработчиков: {e2}")
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