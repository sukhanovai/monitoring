#!/usr/bin/env python3
"""
Тестирование команд бота
"""

import sys
import os
sys.path.insert(0, '/opt/monitoring')

def test_bot_commands():
    """Тестирует доступность команд бота"""
    print("🧪 Тестирование команд бота")
    print("=" * 50)
    
    try:
        from bot import initialize_bot
        updater = initialize_bot()
        
        if updater:
            # Получаем информацию о боте
            bot = updater.bot
            print(f"✅ Бот: {bot.username} (ID: {bot.id})")
            
            # Получаем установленные команды
            commands = bot.get_my_commands()
            print(f"\n📋 Установленные команды:")
            for cmd in commands:
                print(f"  • /{cmd.command} - {cmd.description}")
            
            print(f"\n🎯 Бот готов принимать команды")
            print(f"🔗 Ссылка на бота: https://t.me/{bot.username}")
            
            # Останавливаем бота (мы только тестируем)
            updater.stop()
            return True
        else:
            print("❌ Бот не инициализирован")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitor_instance():
    """Тестирует экземпляр мониторинга"""
    print("\n🔍 Тестирование модуля мониторинга")
    print("=" * 30)
    
    try:
        from core.monitor import monitor
        print(f"✅ Модуль monitor загружен")
        
        # Проверяем методы
        methods = [m for m in dir(monitor) if not m.startswith('_')]
        print(f"Доступные методы: {methods}")
        
        # Пробуем получить статус
        status = monitor.get_status()
        print(f"✅ Статус получен: {len(status)} полей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тестирование системы мониторинга")
    print("=" * 50)
    
    tests = [
        test_monitor_instance,
        test_bot_commands
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ Все тесты пройдены успешно!")
        print("\n🎯 Действия:")
        print("1. Бот готов к работе")
        print("2. Используйте /start для проверки")
        print("3. systemctl restart server-monitor")
    else:
        print(f"⚠️ {total - passed} тестов не пройдено")