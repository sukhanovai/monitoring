#!/usr/bin/env python3
"""
Тестовый скрипт для проверки бота
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_import():
    """Тестирует импорт конфигурации"""
    print("🔧 Тестирование импорта конфигурации...")
    
    try:
        from config import TELEGRAM_TOKEN, DEBUG_MODE, BACKUP_DB_FILE
        print(f"✅ TELEGRAM_TOKEN: {'Есть' if TELEGRAM_TOKEN and len(TELEGRAM_TOKEN) > 10 else 'Нет'}")
        print(f"✅ DEBUG_MODE: {DEBUG_MODE}")
        print(f"✅ BACKUP_DB_FILE: {BACKUP_DB_FILE}")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_bot_initialization():
    """Тестирует инициализацию бота"""
    print("\n🤖 Тестирование инициализации бота...")
    
    try:
        from bot import initialize_bot
        updater = initialize_bot()
        if updater:
            print("✅ Бот инициализирован успешно")
            return True
        else:
            print("❌ Бот не инициализирован")
            return False
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_db_connection():
    """Тестирует подключение к базе данных"""
    print("\n🗃️ Тестирование подключения к БД...")
    
    try:
        import sqlite3
        db_path = '/opt/monitoring/data/settings.db'
        
        if not os.path.exists(db_path):
            print(f"❌ База данных не найдена: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем наличие токена
        cursor.execute('SELECT key, value FROM settings WHERE key = "TELEGRAM_TOKEN"')
        token_result = cursor.fetchone()
        
        if token_result:
            print(f"✅ Токен в БД: {token_result[0]} = {token_result[1][:10]}...")
        else:
            print("❌ Токен не найден в БД")
        
        # Считаем все настройки
        cursor.execute('SELECT COUNT(*) FROM settings')
        count = cursor.fetchone()[0]
        print(f"✅ Всего настроек в БД: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Запуск тестов системы мониторинга")
    print("=" * 50)
    
    tests = [
        test_db_connection,
        test_config_import,
        test_bot_initialization
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
        print("\n🚀 Запуск бота:")
        print("systemctl restart server-monitor")
    else:
        print(f"⚠️ {total - passed} тестов не пройдено")
        print("\n🔧 Проблемы нужно исправить перед запуском")