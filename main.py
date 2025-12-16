"""
/main.py
Server Monitoring System v4.13.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main entry point
Система мониторинга серверов
Версия: 4.13.5
Автор: Александр Суханов (c)
Лицензия: MIT
Главная точка входа
"""

import threading
import time
from datetime import datetime

def main():
    """Упрощенная главная функция"""
    print(f"🚀 Запуск Server Monitoring System v4.13.5")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Инициализируем бота
        print("🤖 Инициализация Telegram бота...")
        from bot import initialize_bot
        updater = initialize_bot()
        
        if updater:
            # Запускаем бота в отдельном потоке
            bot_thread = threading.Thread(target=updater.start_polling)
            bot_thread.daemon = True
            bot_thread.start()
            print("✅ Telegram бот запущен")
            
            # Отправляем тестовое сообщение
            from config import CHAT_IDS, TELEGRAM_TOKEN
            if TELEGRAM_TOKEN and CHAT_IDS:
                from telegram import Bot
                bot = Bot(token=TELEGRAM_TOKEN)
                for chat_id in CHAT_IDS:
                    try:
                        bot.send_message(
                            chat_id=chat_id,
                            text="✅ Система мониторинга запущена в тестовом режиме"
                        )
                        print(f"✅ Тестовое сообщение отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки сообщения: {e}")
            
            # Держим программу активной
            print("📊 Система работает в тестовом режиме")
            print("📝 Используйте /start для проверки бота")
            
            while True:
                time.sleep(60)
                
        else:
            print("❌ Бот не инициализирован")
            
    except KeyboardInterrupt:
        print("🛑 Получен сигнал прерывания")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()