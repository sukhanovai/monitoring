#!/usr/bin/env python3
"""
Проверка статуса бота и команд
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def check_bot_status():
    """Проверяет статус бота"""
    
    print("🤖 Проверяем статус бота...")
    
    try:
        from telegram import Bot
        from config import TELEGRAM_TOKEN
        
        bot = Bot(token=TELEGRAM_TOKEN)
        
        # Проверяем информацию о боте
        me = bot.get_me()
        print(f"✅ Бот активен: @{me.username} ({me.first_name})")
        
        # Проверяем установленные команды
        commands = bot.get_my_commands()
        print(f"📋 Установлено команд: {len(commands)}")
        
        # Ищем команду db_backups
        db_backups_found = False
        for cmd in commands:
            if cmd.command == 'db_backups':
                db_backups_found = True
                print(f"✅ Команда /db_backups найдена: {cmd.description}")
                break
        
        if not db_backups_found:
            print("❌ Команда /db_backups не найдена в установленных командах")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки бота: {e}")
        return False

def test_database_backups_command():
    """Тестирует функцию database_backups_command"""
    
    print("\n🧪 Тестируем обработчик database_backups_command...")
    
    try:
        from extensions.backup_monitor.bot_handler import database_backups_command, BackupMonitorBot
        
        # Создаем mock объекты для тестирования
        class MockUpdate:
            def __init__(self):
                self.message = MockMessage()
                
        class MockMessage:
            def __init__(self):
                self.chat_id = 1
                
            def reply_text(self, text, parse_mode=None, reply_markup=None):
                print(f"✅ Бот отправил сообщение ({len(text)} символов)")
                if "Бэкапы баз данных" in text:
                    print("✅ Сообщение содержит данные о бэкапах БД")
                else:
                    print("❌ Сообщение не содержит данные о бэкапах БД")
                return True
                
        class MockContext:
            def __init__(self):
                self.args = []
                
        update = MockUpdate()
        context = MockContext()
        
        # Тестируем без аргументов
        print("🔹 Тест без аргументов:")
        database_backups_command(update, context)
        
        # Тестируем с аргументом
        print("🔹 Тест с аргументом 48:")
        context.args = ['48']
        database_backups_command(update, context)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_bot_status()
    test_database_backups_command()
    