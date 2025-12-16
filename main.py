#!/usr/bin/env python3
"""
Server Monitoring System v4.11.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.11.0
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import os
import sys
import logging

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

def main():
    """Основная функция запуска"""
    # 1. Сначала загружаем настройки из db_settings
    try:
        from config.db_settings import TELEGRAM_TOKEN, DEBUG_MODE
        print(f"✅ Настройки загружены из db_settings")
        print(f"   Токен: {'Есть' if TELEGRAM_TOKEN else 'Нет'} ({len(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else 0} символов)")
        print(f"   DEBUG_MODE: {DEBUG_MODE}")
    except ImportError as e:
        print(f"❌ Ошибка загрузки db_settings: {e}")
        sys.exit(1)
    
    # 2. Настраиваем логирование
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Запуск системы мониторинга v4.11.0...")
    
    # 3. Проверяем токен
    if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 10:
        logger.error("❌ Telegram токен не найден или слишком короткий!")
        logger.error(f"Токен: '{TELEGRAM_TOKEN}' ({len(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else 0} символов)")
        sys.exit(1)
    
    logger.info(f"✅ Telegram токен получен ({len(TELEGRAM_TOKEN)} символов)")
    
    try:
        # 4. Инициализация бота
        from telegram.ext import Updater
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        logger.info("✅ Telegram бот инициализирован")
        
        # 5. Настройка меню через новую структуру
        from bot import setup_menu, get_bot_handlers, get_bot_message_handler
        
        setup_menu(updater.bot)
        logger.info("✅ Меню настроено")
        
        # 6. Добавляем обработчики команд и callback
        for handler in get_bot_handlers():
            updater.dispatcher.add_handler(handler)
        logger.info("✅ Обработчики команд и callback добавлены")
        
        # 7. Добавляем обработчик сообщений
        updater.dispatcher.add_handler(get_bot_message_handler())
        logger.info("✅ Обработчик сообщений добавлен")
        
        # 8. Обработчики настроек (для обратной совместимости)
        try:
            from settings_handlers import get_settings_handlers
            for handler in get_settings_handlers():
                updater.dispatcher.add_handler(handler)
            logger.info("✅ Обработчики настроек добавлены")
        except ImportError as e:
            logger.warning(f"⚠️ Обработчики настроек недоступны: {e}")
        
        # 9. Расширения
        try:
            from extensions.extension_manager import extension_manager
            
            # Бэкапы
            if extension_manager.is_extension_enabled('backup_monitor'):
                from extensions.backup_monitor.bot_handler import setup_backup_handlers
                setup_backup_handlers(updater.dispatcher)
                logger.info("✅ Обработчики бэкапов настроены")
            
            # Веб-интерфейс
            if extension_manager.is_extension_enabled('web_interface'):
                from extensions.web_interface import start_web_server
                import threading
                web_thread = threading.Thread(target=start_web_server, daemon=True)
                web_thread.start()
                logger.info("✅ Веб-сервер запущен")
                
        except ImportError as e:
            logger.warning(f"⚠️ Расширения недоступны: {e}")
        
        # 10. Сбор статистики
        try:
            from extensions.utils import save_monitoring_stats
            save_monitoring_stats()
            logger.info("✅ Сбор статистики запущен")
        except ImportError:
            logger.warning("⚠️ Модуль статистики недоступен")
        
        # 11. Основной мониторинг
        try:
            from core.monitor import monitor
            import threading
            monitor_thread = threading.Thread(target=monitor.start, daemon=True)
            monitor_thread.start()
            logger.info("✅ Основной мониторинг запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска мониторинга: {e}")
            # Продолжаем без мониторинга
        
        # 12. Стартовое сообщение
        try:
            from lib.alerts import send_alert
            send_alert("🟢 *Мониторинг серверов запущен*\n\n✅ Система работает корректно", force=True)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить стартовое сообщение: {e}")
        
        # 13. Запуск бота
        updater.start_polling()
        logger.info("✅ Бот запущен и работает")
        
        # Блокируем основной поток
        logger.info("✅ Система полностью запущена и готова к работе")
        updater.idle()
        
    except ImportError as e:
        logger.error(f"❌ Критическая ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()