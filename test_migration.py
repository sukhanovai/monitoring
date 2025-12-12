#!/usr/bin/env python3
"""
Тестирование переноса конфигурационных файлов
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def test_imports():
    """Тестирование импортов"""
    print("🔍 Тестирование импортов...")
    
    try:
        from app.config.settings import TELEGRAM_TOKEN, CHAT_IDS
        print("✅ app.config.settings - OK")
    except ImportError as e:
        print(f"❌ app.config.settings - ERROR: {e}")
        return False
    
    try:
        from app.config.debug import DebugConfig, debug_config
        print("✅ app.config.debug - OK")
    except ImportError as e:
        print(f"❌ app.config.debug - ERROR: {e}")
        return False
    
    try:
        from app.config.manager import settings_manager
        print("✅ app.config.manager - OK")
    except ImportError as e:
        print(f"❌ app.config.manager - ERROR: {e}")
        return False
    
    return True

def test_config_loading():
    """Тестирование загрузки конфигурации"""
    print("\n🔧 Тестирование загрузки конфигурации...")
    
    try:
        from app.config.settings import get_setting
        interval = get_setting('CHECK_INTERVAL', 60)
        print(f"✅ CHECK_INTERVAL = {interval}")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        return False

def test_debug_config():
    """Тестирование конфигурации отладки"""
    print("\n🐛 Тестирование конфигурации отладки...")
    
    try:
        from app.config.debug import debug_config
        info = debug_config.get_debug_info()
        print(f"✅ Debug config loaded: {info['debug_mode']}")
        return True
    except Exception as e:
        print(f"❌ Ошибка debug config: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Начинаем тестирование миграции конфигурации\n")
    
    success = True
    
    # Тест 1: Импорты
    if not test_imports():
        success = False
    
    # Тест 2: Конфигурация
    if not test_config_loading():
        success = False
    
    # Тест 3: Отладка
    if not test_debug_config():
        success = False
    
    if success:
        print("\n🎉 Все тесты пройдены! Миграция успешна.")
    else:
        print("\n❌ Есть проблемы с миграцией. Проверьте импорты.")
        sys.exit(1)