#!/usr/bin/env python3
"""
Check settings and token
Проверка настроек и токена
"""

import sys
sys.path.insert(0, '/opt/monitoring')

print("🔍 Проверка настроек системы...")

try:
    # Проверяем настройки из разных источников
    print("1. Проверяем config.settings...")
    try:
        from config.settings import TELEGRAM_TOKEN
        print(f"   TELEGRAM_TOKEN из settings.py: {'Установлен' if TELEGRAM_TOKEN else 'Пустой'}")
        if TELEGRAM_TOKEN:
            print(f"   Длина токена: {len(TELEGRAM_TOKEN)} символов")
            print(f"   Первые 10 символов: {TELEGRAM_TOKEN[:10]}...")
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    print("\n2. Проверяем config.db_settings...")
    try:
        from config.db_settings import TELEGRAM_TOKEN as DB_TOKEN
        print(f"   TELEGRAM_TOKEN из db_settings.py: {'Установлен' if DB_TOKEN else 'Пустой'}")
        if DB_TOKEN:
            print(f"   Длина токена: {len(DB_TOKEN)} символов")
            print(f"   Первые 10 символов: {DB_TOKEN[:10]}...")
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    print("\n3. Проверяем базу данных напрямую...")
    try:
        import sqlite3
        conn = sqlite3.connect('/opt/monitoring/data/settings.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'TELEGRAM_TOKEN'")
        result = cursor.fetchone()
        if result:
            token = result[0]
            print(f"   TELEGRAM_TOKEN из БД: {'Установлен' if token else 'Пустой'}")
            if token:
                print(f"   Длина токена: {len(token)} символов")
                print(f"   Токен: {token[:15]}...")
        else:
            print("   ❌ Токен не найден в базе данных")
        conn.close()
    except Exception as e:
        print(f"   ❌ Ошибка подключения к БД: {e}")

    print("\n4. Проверяем config_manager...")
    try:
        from core.config_manager import config_manager
        token = config_manager.get_setting('TELEGRAM_TOKEN', '')
        print(f"   TELEGRAM_TOKEN из config_manager: {'Установлен' if token else 'Пустой'}")
        if token:
            print(f"   Длина токена: {len(token)} символов")
            print(f"   Первые 10 символов: {token[:10]}...")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

except Exception as e:
    print(f"💥 Общая ошибка: {e}")