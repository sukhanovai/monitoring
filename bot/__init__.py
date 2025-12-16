"""
/bot/menu/__init__.py
Server Monitoring System v4.13.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot package
Система мониторинга серверов
Версия: 4.13.4
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет Telegram бота
"""

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

def initialize_bot():
    """Инициализирует бота"""
    print("🤖 Инициализация Telegram бота...")
    
    try:
        # Временное решение: получаем токен напрямую из БД
        import sqlite3
        import os
        
        db_path = '/opt/monitoring/data/settings.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = "TELEGRAM_TOKEN"')
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                token = result[0]
                print(f"✅ Токен загружен из БД ({len(token)} символов)")
            else:
                print("❌ Токен не найден в БД")
                return None
        else:
            print(f"❌ База данных не найдена: {db_path}")
            return None
        
        # Создаем Updater и Dispatcher
        updater = Updater(token=token, use_context=True)
        dispatcher = updater.dispatcher
        
        # Регистрируем базовые команды для тестирования
        from telegram import BotCommand
        
        # Устанавливаем команды меню
        commands = [
            BotCommand("start", "Запуск бота"),
            BotCommand("help", "Помощь"),
            BotCommand("check", "Проверить серверы"),
            BotCommand("status", "Статус мониторинга"),
        ]
        
        updater.bot.set_my_commands(commands)
        
        print("✅ Бот инициализирован успешно")
        return updater
        
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        return None