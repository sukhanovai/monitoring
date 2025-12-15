# Добавьте в конец тестового скрипта, после существующих тестов:

print("\n7. Тестируем модули ядра...")
try:
    from core.config_manager import config_manager
    from core.checker import ServerChecker
    from core.monitor import *
    
    print("✅ Все модули ядра загружены")
    
    # Тестируем ServerChecker
    checker = ServerChecker()
    print(f"✅ ServerChecker создан: timeout={checker.ssh_timeout}")
    
    # Тестируем config_manager
    all_settings = config_manager.get_all_settings()
    print(f"✅ ConfigManager: {len(all_settings)} настроек")
    
    print("✅ Модули ядра: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта модулей ядра: {e}")
except Exception as e:
    print(f"❌ Модули ядра: Ошибка - {e}")
    import traceback
    traceback.print_exc()

print("\n8. Тестируем модули приложения...")
try:
    from modules import availability, resources, morning_report, targeted_checks
    
    print("✅ Все модули приложения загружены")
    print(f"  - availability: {availability.__name__}")
    print(f"  - resources: {resources.__name__}")
    print(f"  - morning_report: {morning_report.__name__}")
    print(f"  - targeted_checks: {targeted_checks.__name__}")
    
    print("✅ Модули приложения: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта модулей приложения: {e}")
except Exception as e:
    print(f"❌ Модули приложения: Ошибка - {e}")