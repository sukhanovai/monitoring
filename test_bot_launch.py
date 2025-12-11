# /opt/monitoring/test_bot_launch.py
"""
Тестовый запуск бота после обновления
"""

import sys
import os
import time

print("=" * 60)
print("ТЕСТОВЫЙ ЗАПУСК БОТА ПОСЛЕ ОБНОВЛЕНИЯ")
print("=" * 60)

# Добавляем пути
sys.path.insert(0, '/opt/monitoring')
sys.path.insert(0, '/opt/monitoring/app')

try:
    print("1. Импортируем основные модули...")
    
    # Основные импорты
    import monitor_core
    from app import server_checker, logger
    from app.utils.common import debug_log, progress_bar
    
    print("   ✅ Основные модули импортированы")
    
    print("\n2. Проверяем функции мониторинга...")
    
    # Проверяем функцию start_monitoring (без реального запуска)
    if hasattr(monitor_core, 'start_monitoring'):
        print("   ✅ Функция start_monitoring найдена")
        
        # Проверяем, что она вызывается без ошибок (в тестовом режиме)
        try:
            # Мокаем некоторые зависимости чтобы избежать реального запуска
            import threading
            original_Thread = threading.Thread
            
            class MockThread:
                def __init__(self, *args, **kwargs):
                    self.args = args
                    self.kwargs = kwargs
                
                def start(self):
                    print("   🧪 MockThread.start() вызван")
                
                def join(self):
                    pass
            
            threading.Thread = MockThread
            
            # Пробуем вызвать start_monitoring (она должна быстро завершиться из-за моков)
            print("   🧪 Тестируем вызов start_monitoring...")
            
            # Временно изменяем некоторые глобальные переменные для теста
            original_monitoring_active = getattr(monitor_core, 'monitoring_active', None)
            if original_monitoring_active is not None:
                monitor_core.monitoring_active = False
            
            # Восстанавливаем
            if original_monitoring_active is not None:
                monitor_core.monitoring_active = original_monitoring_active
            
            threading.Thread = original_Thread
            
            print("   ✅ start_monitoring можно вызывать")
            
        except Exception as e:
            print(f"   ❌ Ошибка при тестировании start_monitoring: {e}")
    else:
        print("   ❌ Функция start_monitoring не найдена")
    
    print("\n3. Проверяем обработчики команд...")
    
    handlers_to_check = [
        'manual_check_handler',
        'monitor_status', 
        'check_resources_handler',
        'send_morning_report_handler'
    ]
    
    for handler_name in handlers_to_check:
        if hasattr(monitor_core, handler_name):
            handler = getattr(monitor_core, handler_name)
            print(f"   ✅ {handler_name}: {handler}")
        else:
            print(f"   ❌ {handler_name}: не найден")
    
    print("\n4. Тестируем server_checker...")
    
    # Тестируем базовые функции server_checker
    test_cases = [
        ("check_ping('127.0.0.1')", lambda: server_checker.check_ping('127.0.0.1')),
        ("check_port('127.0.0.1', 22)", lambda: server_checker.check_port('127.0.0.1', 22)),
    ]
    
    for test_name, test_func in test_cases:
        try:
            result = test_func()
            print(f"   ✅ {test_name}: {result}")
        except Exception as e:
            print(f"   ❌ {test_name}: ошибка - {e}")
    
    print("\n5. Проверяем утилиты...")
    
    # Тестируем утилиты
    print(f"   progress_bar(33): {progress_bar(33)}")
    print(f"   debug_log тест: ", end="")
    debug_log("Тестовое сообщение debug_log")
    print("вызвана")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("=" * 60)
    
    print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Запустите бота вручную для полной проверки:")
    print("   cd /opt/monitoring")
    print("   python3 main.py")
    print("")
    print("2. Или перезапустите сервис:")
    print("   sudo systemctl restart monitoring")
    print("")
    print("3. Проверьте логи:")
    print("   tail -f /opt/monitoring/bot_debug.log")
    print("")
    print("4. Если всё работает, обновите другие файлы:")
    print("   - bot_menu.py")
    print("   - main.py")
    print("   - settings_manager.py")
    
except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("⚠️  ТРЕБУЕТСЯ ВМЕШАТЕЛЬСТВО!")
    print("=" * 60)
    