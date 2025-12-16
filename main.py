"""
/main.py
Server Monitoring System v4.13.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main entry point
Система мониторинга серверов
Версия: 4.13.3
Автор: Александр Суханов (c)
Лицензия: MIT
Главная точка входа
"""

import threading
import time
from datetime import datetime
from lib.logging import debug_log, setup_logging

def main():
    """Главная функция запуска системы"""
    
    # Настраиваем логирование
    setup_logging()
    
    debug_log("🚀 Запуск Server Monitoring System v4.13.3")
    debug_log("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # Инициализируем бота
        debug_log("🤖 Инициализация Telegram бота...")
        from bot import initialize_bot
        updater = initialize_bot()
        
        # Запускаем бота в отдельном потоке
        bot_thread = threading.Thread(target=updater.start_polling)
        bot_thread.daemon = True
        bot_thread.start()
        debug_log("✅ Telegram бот запущен")
        
        # Запускаем основной мониторинг в отдельном потоке
        debug_log("🔍 Запуск основного мониторинга...")
        from core.monitor import start_monitoring
        monitor_thread = threading.Thread(target=start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        debug_log("✅ Основной мониторинг запущен")
        
        # Запускаем мониторинг почты если расширение включено
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('mail_monitor'):
                debug_log("📧 Запуск мониторинга почты...")
                from extensions.mail_monitor import start_mail_monitoring
                mail_thread = threading.Thread(target=start_mail_monitoring)
                mail_thread.daemon = True
                mail_thread.start()
                debug_log("✅ Мониторинг почты запущен")
        except ImportError:
            debug_log("📧 Мониторинг почты недоступен")
        
        # Запускаем веб-интерфейс если расширение включено
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('web_interface'):
                debug_log("🌐 Запуск веб-интерфейса...")
                from extensions.web_interface import start_web_interface
                web_thread = threading.Thread(target=start_web_interface)
                web_thread.daemon = True
                web_thread.start()
                debug_log("✅ Веб-интерфейс запущен")
        except ImportError:
            debug_log("🌐 Веб-интерфейс недоступен")
        
        debug_log("✅ Все компоненты запущены")
        debug_log("📊 Система готова к работе")
        
        # Основной цикл (держим программу активной)
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        debug_log("🛑 Получен сигнал прерывания")
    except Exception as e:
        debug_log(f"💥 Критическая ошибка: {e}")
        import traceback
        debug_log(f"💥 Traceback: {traceback.format_exc()}")
    finally:
        debug_log("👋 Завершение работы системы")

if __name__ == "__main__":
    main()