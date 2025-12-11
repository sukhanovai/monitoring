# /opt/monitoring/final_test_monitor_core.py
"""
Финальный тест monitor_core.py
"""

import sys
import os

print("=" * 70)
print("ФИНАЛЬНЫЙ ТЕСТ MONITOR_CORE.PY")
print("=" * 70)

# Добавляем пути
sys.path.insert(0, '/opt/monitoring')
sys.path.insert(0, '/opt/monitoring/app')

try:
    # 1. Импортируем
    import monitor_core
    print("✅ monitor_core импортирован")
    
    # 2. Проверяем что все ключевые функции доступны
    required_items = [
        # Функции
        'start_monitoring',
        'manual_check_handler',
        'monitor_status',
        'check_resources_handler',
        'send_morning_report',
        'check_server_availability',
        'is_silent_time',
        'send_alert',
        
        # Переменные
        'server_status',
        'monitoring_active',
        'servers',
        'bot',
        'last_check_time',
        'silent_override',
    ]
    
    print("\n🔍 Проверка доступности:")
    missing = []
    for item in required_items:
        if hasattr(monitor_core, item):
            print(f"  ✅ {item}")
        else:
            print(f"  ❌ {item}")
            missing.append(item)
    
    if missing:
        print(f"\n⚠️  Отсутствует: {len(missing)} элементов")
    else:
        print(f"\n✅ Все элементы доступны")
    
    # 3. Проверяем импорты
    print("\n🔄 Проверка импортов:")
    
    # Получаем исходный код
    import inspect
    source = inspect.getsource(monitor_core)
    
    checks = [
        ('from app import', 'Импорты из app'),
        ('from app.utils.common import', 'Импорты из utils.common'),
        ('from app.core.checker import', 'Импорты из core.checker'),
        ('from core_utils import', 'Старые импорты из core_utils'),
        ('core_utils\\.', 'Использования core_utils.'),
    ]
    
    for pattern, description in checks:
        count = source.count(pattern)
        status = "✅" if ('core_utils' not in pattern and count > 0) or ('core_utils' in pattern and count == 0) else "⚠️ "
        print(f"  {status} {description}: {count}")
    
    # 4. Тестируем функции
    print("\n🧪 Тестируем функции:")
    
    # Тест is_proxmox_server
    if hasattr(monitor_core, 'is_proxmox_server'):
        test_cases = [
            ("192.168.30.10", True),
            ("192.168.20.30", True),
            ("192.168.20.2", False),
            ("192.168.1.1", False),
        ]
        
        print("  is_proxmox_server:")
        for ip, expected in test_cases:
            result = monitor_core.is_proxmox_server({"ip": ip})
            status = "✅" if result == expected else "❌"
            print(f"    {status} {ip}: {result} (ожидалось: {expected})")
    
    # Тест is_silent_time
    if hasattr(monitor_core, 'is_silent_time'):
        try:
            result = monitor_core.is_silent_time()
            print(f"  ✅ is_silent_time(): {result}")
        except Exception as e:
            print(f"  ❌ is_silent_time(): ошибка - {e}")
    
    print("\n" + "=" * 70)
    
    # Итог
    if not missing and 'core_utils' not in source:
        print("🎉 MONITOR_CORE.PY УСПЕШНО ОБНОВЛЕН!")
        print("\n📋 Следующие шаги:")
        print("1. Протестируйте запуск бота:")
        print("   python3 /opt/monitoring/main.py")
        print("2. Или запустите тестовый скрипт:")
        print("   python3 test_bot_launch.py")
        print("3. Создайте коммит:")
        print("   git add monitor_core.py")
        print("   git commit -m 'refactor: обновлены импорты для модульной структуры'")
        print("   git push")
        print("4. Переходите к обновлению других файлов:")
        print("   - bot_menu.py")
        print("   - main.py")
        print("   - settings_manager.py")
    else:
        print("⚠️  ТРЕБУЕТСЯ ДОРАБОТКА")
        if missing:
            print(f"   Отсутствуют: {missing}")
        if 'core_utils' in source:
            print("   Есть ссылки на core_utils")
    
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    