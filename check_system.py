#!/usr/bin/env python3
"""
Проверка системы мониторинга
"""

import sys
import os
sys.path.insert(0, '/opt/monitoring')

print("🔍 Проверка системы мониторинга")
print("=" * 50)

# 1. Проверяем core.monitor.py
print("1. Проверка core.monitor.py:")
try:
    import core.monitor
    print(f"   ✅ Модуль загружен")
    
    # Смотрим что есть в модуле
    functions = [f for f in dir(core.monitor) if not f.startswith('_')]
    print(f"   Доступные функции: {functions[:10]}...")
    
    # Проверяем есть ли start_monitoring
    if 'start_monitoring' in dir(core.monitor):
        print("   ✅ start_monitoring найдена")
    else:
        print("   ❌ start_monitoring не найдена")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 2. Проверяем config
print("\n2. Проверка config:")
try:
    from config import TELEGRAM_TOKEN, DEBUG_MODE
    print(f"   ✅ TELEGRAM_TOKEN: {'Есть' if TELEGRAM_TOKEN and len(TELEGRAM_TOKEN) > 10 else 'Нет'}")
    print(f"   ✅ DEBUG_MODE: {DEBUG_MODE}")
except Exception as e:
    print(f"   ❌ Ошибка импорта из config: {e}")

# 3. Проверяем bot
print("\n3. Проверка bot:")
try:
    from bot import initialize_bot
    print("   ✅ Функция initialize_bot найдена")
    
    # Пробуем инициализировать бота
    updater = initialize_bot()
    if updater:
        print("   ✅ Бот успешно инициализирован")
        updater.stop()
    else:
        print("   ❌ Бот не инициализирован")
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")