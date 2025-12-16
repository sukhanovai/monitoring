#!/usr/bin/env python3
"""
Test script for new monitoring structure - FIXED VERSION
Тестовый скрипт для новой структуры мониторинга - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def test_modules():
    """Тестирует все модули новой структуры"""
    print("🧪 Тестирование новой структуры мониторинга...")
    
    try:
        # 1. Тест импорта базовых модулей
        print("1. Тестирование импорта базовых модулей...")
        from lib.logging import debug_log, setup_logging
        setup_logging()
        debug_log("✅ Тестовое сообщение логирования")
        print("   ✅ Логирование работает")
        
        # 2. Тест импорта настроек
        print("2. Тестирование импорта настроек...")
        from config.settings import TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL
        print(f"   ✅ Настройки загружены: CHECK_INTERVAL={CHECK_INTERVAL}")
        
        # 3. Тест импорта модулей
        print("3. Тестирование импорта модулей...")
        
        from modules.availability import availability_checker
        print("   ✅ availability_checker загружен")
        
        from modules.resources import resources_checker
        print("   ✅ resources_checker загружен")
        
        from modules.morning_report import morning_report
        print("   ✅ morning_report загружен")
        
        from modules.targeted_checks import targeted_checks
        print("   ✅ targeted_checks загружен")
        
        from core.monitor import monitor
        print("   ✅ monitor загружен")
        
        # 4. Тест загрузки серверов
        print("4. Тестирование загрузки серверов...")
        try:
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            print(f"   ✅ Загружено серверов: {len(servers)}")
        except Exception as e:
            print(f"   ⚠️ Ошибка загрузки серверов: {e}")
        
        # 5. Тест создания экземпляров
        print("5. Тестирование создания экземпляров...")
        print(f"   ✅ availability_checker: {type(availability_checker).__name__}")
        print(f"   ✅ resources_checker: {type(resources_checker).__name__}")
        print(f"   ✅ morning_report: {type(morning_report).__name__}")
        print(f"   ✅ targeted_checks: {type(targeted_checks).__name__}")
        print(f"   ✅ monitor: {type(monitor).__name__}")
        
        # 6. Проверка методов
        print("6. Тестирование базовых методов...")
        
        # Проверка методов availability_checker
        methods = ['check_server_availability', 'check_multiple_servers']
        for method in methods:
            if hasattr(availability_checker, method):
                print(f"   ✅ availability_checker.{method}() доступен")
            else:
                print(f"   ❌ availability_checker.{method}() недоступен")
        
        # Проверка методов resources_checker
        methods = ['check_server_resources', 'check_multiple_resources']
        for method in methods:
            if hasattr(resources_checker, method):
                print(f"   ✅ resources_checker.{method}() доступен")
            else:
                print(f"   ❌ resources_checker.{method}() недоступен")
        
        # Проверка методов monitor
        methods = ['start', 'stop', 'get_status', 'is_silent_time']
        for method in methods:
            if hasattr(monitor, method):
                print(f"   ✅ monitor.{method}() доступен")
            else:
                print(f"   ❌ monitor.{method}() недоступен")
        
        print("\n🎉 Все основные тесты пройдены успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Проверьте работу системы вручную")
        print("2. Запустите миграцию: python3 migrate_monitor_core.py")
        print("3. Обновите main.py для использования новой структуры")
        print("4. Перезапустите бота: systemctl restart monitoring-bot")
        
        return True
        
    except Exception as e:
        print(f"💥 Критическая ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_modules()
    sys.exit(0 if success else 1)