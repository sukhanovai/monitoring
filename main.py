#!/usr/bin/env python3
"""
Server Monitoring System v4.10.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.10.4
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

# Импортируем модуль логирования ДО всех других импортов
from lib.logging import debug_log, setup_logging, set_debug_mode

def setup_environment():
    """Настройка окружения и логирования"""
    # Получаем DEBUG_MODE из db_settings
    try:
        from config.db_settings import DEBUG_MODE
        debug_mode = DEBUG_MODE
    except ImportError:
        debug_mode = False
    
    # Устанавливаем режим отладки
    set_debug_mode(debug_mode)
    
    # Настраиваем логирование
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Настройка окружения...")
    
    return logger, debug_mode

def get_telegram_token():
    """Получает токен Telegram из правильного источника"""
    # Сначала пробуем получить из db_settings (самый надежный способ)
    try:
        from config.db_settings import TELEGRAM_TOKEN
        if TELEGRAM_TOKEN and len(TELEGRAM_TOKEN) > 10:
            debug_log(f"✅ Токен загружен из db_settings ({len(TELEGRAM_TOKEN)} символов)")
            return TELEGRAM_TOKEN
    except ImportError as e:
        debug_log(f"⚠️ Не удалось загрузить токен из db_settings: {e}")
    
    # Затем пробуем через config_manager
    try:
        from core.config_manager import config_manager
        token = config_manager.get_setting('TELEGRAM_TOKEN', '')
        if token and len(token) > 10:
            debug_log(f"✅ Токен загружен из config_manager ({len(token)} символов)")
            return token
    except Exception as e:
        debug_log(f"⚠️ Не удалось загрузить токен из config_manager: {e}")
    
    # Проверяем переменную окружения
    token = os.environ.get('TELEGRAM_TOKEN', '')
    if token and len(token) > 10:
        debug_log(f"✅ Токен загружен из переменной окружения ({len(token)} символов)")
        return token
    
    # Пробуем напрямую из базы данных
    try:
        import sqlite3
        conn = sqlite3.connect('/opt/monitoring/data/settings.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'TELEGRAM_TOKEN'")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] and len(result[0]) > 10:
            debug_log(f"✅ Токен загружен напрямую из БД ({len(result[0])} символов)")
            return result[0]
    except Exception as e:
        debug_log(f"⚠️ Не удалось загрузить токен из БД: {e}")
    
    return ''

def main():
    """Основная функция запуска"""
    logger, debug_mode = setup_environment()
    
    try:
        logger.info("🚀 Запуск системы мониторинга v4.9.2...")
        
        # Получаем токен Telegram
        TELEGRAM_TOKEN = get_telegram_token()
        
        if not TELEGRAM_TOKEN:
            logger.error("❌ Telegram токен не найден!")
            logger.error("Токен должен быть установлен в базе данных:")
            logger.error("sqlite3 /opt/monitoring/data/settings.db \\")
            logger.error("  \"INSERT OR REPLACE INTO settings (key, value) VALUES ('TELEGRAM_TOKEN', 'ваш_токен');\"")
            sys.exit(1)
        
        logger.info(f"✅ Telegram токен получен ({len(TELEGRAM_TOKEN)} символов)")
        
        # Инициализация модулей
        logger.info("🔄 Инициализация модулей...")
        
        try:
            from modules.targeted_checks import targeted_checks
            targeted_checks.get_all_servers()
            logger.info("✅ Модуль точечных проверок инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации targeted_checks: {e}")
        
        try:
            from core.monitor import monitor
            logger.info("✅ Основной мониторинг инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации монитора: {e}")
            raise
        
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
            logger.error("Файлы bot_menu.py не найдены!")
            sys.exit(1)
        
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
        try:
            monitor_thread = threading.Thread(target=monitor.start, daemon=True)
            monitor_thread.start()
            logger.info("✅ Основной мониторинг запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска мониторинга: {e}")
        
        # Запускаем бота
        updater.start_polling()
        logger.info("✅ Бот запущен и работает")
        
        # Отправляем стартовое сообщение
        try:
            from lib.alerts import send_alert
            send_alert("🟢 *Мониторинг серверов запущен*\n\n✅ Новая модульная структура v4.9.2 активна", force=True)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить стартовое сообщение: {e}")
        
        # Блокируем основной поток
        logger.info("✅ Система полностью запущена и готова к работе")
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
        
        sys.exit(1)

if __name__ == "__main__":
    main()