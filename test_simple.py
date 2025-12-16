#!/usr/bin/env python3
"""
Simple test after fixes
"""

import sys
sys.path.insert(0, '/opt/monitoring')

print("🧪 Простой тест после исправлений...")

try:
    # 1. Проверяем импорт токена
    from config.db_settings import TELEGRAM_TOKEN, DEBUG_MODE
    print(f"✅ Токен из db_settings: {'Есть' if TELEGRAM_TOKEN else 'Нет'}")
    print(f"   Длина: {len(TELEGRAM_TOKEN)} символов")
    print(f"   DEBUG_MODE: {DEBUG_MODE}")
    
    # 2. Проверяем импорт из config
    from config import TELEGRAM_TOKEN as CONFIG_TOKEN
    print(f"✅ Токен из config: {'Есть' if CONFIG_TOKEN else 'Нет'}")
    
    # 3. Сравниваем
    if TELEGRAM_TOKEN == CONFIG_TOKEN:
        print("✅ Токены совпадают!")
    else:
        print("⚠️  Токены не совпадают!")
        
    # 4. Проверяем монитор
    from core.monitor import monitor
    print(f"✅ Монитор загружен: {type(monitor).__name__}")
    
    # 5. Проверяем модули
    from modules.availability import availability_checker
    from modules.resources import resources_checker
    print(f"✅ Модули загружены")
    
    print("\n🎉 Все системы работают!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()