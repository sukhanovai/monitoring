#!/usr/bin/env python3
"""
Тестирование новой структуры проекта
"""

import sys
import os
sys.path.insert(0, '/opt/monitoring')

print("=== Тестирование новой структуры проекта ===\n")

# 1. Тестируем логирование
print("1. Тестируем модуль логирования...")
try:
    from lib.logging import setup_logging, debug_log, set_debug_mode
    logger = setup_logging("test")
    debug_log("✅ Модуль логирования работает")
    set_debug_mode(True)
    debug_log("✅ Режим отладки включен")
    print("✅ Логирование: OK")
except Exception as e:
    print(f"❌ Логирование: Ошибка - {e}")

# 2. Тестируем алерты
print("\n2. Тестируем модуль алертов...")
try:
    from lib.alerts import send_alert, configure
    configure(silent_start=20, silent_end=9)
    print("✅ Модуль алертов загружен")
    print("✅ Конфигурация алертов: OK")
except Exception as e:
    print(f"❌ Алерты: Ошибка - {e}")

# 3. Тестируем менеджер конфигурации
print("\n3. Тестируем менеджер конфигурации...")
try:
    from core.config_manager import config_manager
    print(f"✅ Менеджер конфигурации инициализирован: {config_manager.db_path}")
    
    # Тестируем получение настроек
    token = config_manager.get_setting('TELEGRAM_TOKEN', 'test')
    print(f"✅ Получение настроек: TELEGRAM_TOKEN = {token[:10]}...")
    
    # Тестируем сохранение настроек
    config_manager.set_setting('TEST_KEY', 'test_value', 'test', 'Тестовая настройка')
    test_value = config_manager.get_setting('TEST_KEY')
    print(f"✅ Сохранение настроек: TEST_KEY = {test_value}")
    
    # Очищаем тестовую настройку
    config_manager.clear_cache()
    print("✅ Очистка кэша: OK")
except Exception as e:
    print(f"❌ Конфигурация: Ошибка - {e}")

# 4. Тестируем настройки из БД
print("\n4. Тестируем загрузку настроек из БД...")
try:
    from config.db_settings import load_all_settings, TELEGRAM_TOKEN, CHECK_INTERVAL
    load_all_settings()
    print(f"✅ Настройки загружены из БД")
    print(f"  TELEGRAM_TOKEN: {'установлен' if TELEGRAM_TOKEN else 'не установлен'}")
    print(f"  CHECK_INTERVAL: {CHECK_INTERVAL} сек")
except Exception as e:
    print(f"❌ Загрузка настроек: Ошибка - {e}")

print("\n=== Тестирование завершено ===")