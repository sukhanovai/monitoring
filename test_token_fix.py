#!/usr/bin/env python3
"""
Test token fix
Тест исправления токена
"""

import sys
sys.path.insert(0, '/opt/monitoring')

print("🧪 Тестирование исправления токена...")

# Тест 1: Проверяем импорт из config
print("\n1. Проверяем импорт из config:")
try:
    from config import TELEGRAM_TOKEN, USE_DB
    print(f"   ✅ TELEGRAM_TOKEN из config: {'Есть' if TELEGRAM_TOKEN else 'Нет'}")
    print(f"   ✅ USE_DB: {USE_DB}")
    if TELEGRAM_TOKEN:
        print(f"   📏 Длина токена: {len(TELEGRAM_TOKEN)}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# Тест 2: Проверяем функцию get_telegram_token
print("\n2. Проверяем функцию get_telegram_token:")
try:
    import os
    sys.path.insert(0, '/opt/monitoring')
    
    def test_get_token():
        """Тестовая функция получения токена"""
        # Пробуем из db_settings
        try:
            from config.db_settings import TELEGRAM_TOKEN
            if TELEGRAM_TOKEN and len(TELEGRAM_TOKEN) > 10:
                return f"db_settings ({len(TELEGRAM_TOKEN)} chars)"
        except:
            pass
        
        # Пробуем из config_manager
        try:
            from core.config_manager import config_manager
            token = config_manager.get_setting('TELEGRAM_TOKEN', '')
            if token and len(token) > 10:
                return f"config_manager ({len(token)} chars)"
        except:
            pass
        
        return "Не найден"
    
    result = test_get_token()
    print(f"   ✅ Результат: {result}")
    
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# Тест 3: Проверяем старый main.py импорт
print("\n3. Проверяем старый main.py импорт:")
try:
    # Симулируем то что делает старый main.py
    from config.settings import TELEGRAM_TOKEN as OLD_TOKEN
    print(f"   ⚠️  Старый импорт из settings.py: {'Есть' if OLD_TOKEN else 'Нет (ОЖИДАЕМО)'}")
    
    from config.db_settings import TELEGRAM_TOKEN as NEW_TOKEN
    print(f"   ✅ Новый импорт из db_settings.py: {'Есть' if NEW_TOKEN else 'Нет'}")
    
    print(f"\n   📊 Итог:")
    print(f"   - settings.py токен: {'🟢' if OLD_TOKEN else '🔴'}")
    print(f"   - db_settings.py токен: {'🟢' if NEW_TOKEN else '🔴'}")
    print(f"   - Правильный токен в БД: {'🟢' if NEW_TOKEN else '🔴'}")
    
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n✅ Тест завершен!")