#!/usr/bin/env python3
"""
Диагностика настроек
"""

import sys
sys.path.insert(0, '/opt/monitoring')

print("🔧 Диагностика настроек системы\n")

try:
    print("1. Импорт из config.settings:")
    from config.settings import CHAT_IDS, TELEGRAM_TOKEN, DEBUG_MODE
    print(f"   ✅ CHAT_IDS: {CHAT_IDS}")
    print(f"   ✅ TELEGRAM_TOKEN: {'Есть' if TELEGRAM_TOKEN else 'Нет'}")
    print(f"   ✅ DEBUG_MODE: {DEBUG_MODE}")
except ImportError as e:
    print(f"   ❌ Ошибка: {e}")

print("\n2. Проверка БД напрямую:")
try:
    import sqlite3
    import json
    
    conn = sqlite3.connect('/opt/monitoring/data/settings.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM settings WHERE key IN ('CHAT_IDS', 'TELEGRAM_TOKEN', 'DEBUG_MODE')")
    for key, value in cursor.fetchall():
        print(f"   {key}: {value}")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n3. Проверка структуры БД:")
try:
    import sqlite3
    
    conn = sqlite3.connect('/opt/monitoring/data/settings.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"   Таблицы: {[t[0] for t in tables]}")
    
    cursor.execute("PRAGMA table_info(settings)")
    columns = cursor.fetchall()
    print(f"   Колонки таблицы settings:")
    for col in columns:
        print(f"     - {col[1]} ({col[2]})")
    
    conn.close()
except Exception as e:
    print(f"   ❌ Ошибка: {e}")