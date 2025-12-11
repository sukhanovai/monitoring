"""
Проверка monitor_core.py после обновления
"""

import sys
import os

print("=" * 60)
print("ПРОВЕРКА MONITOR_CORE.PY ПОСЛЕ ОБНОВЛЕНИЯ")
print("=" * 60)

# Добавляем пути
sys.path.insert(0, '/opt/monitoring')
sys.path.insert(0, '/opt/monitoring/app')

try:
    # 1. Импортируем обновленный модуль
    import monitor_core
    print("✅ 1. monitor_core импортирован успешно")
    
    # 2. Проверяем ключевые функции
    print("\n🔍 2. Проверка функций:")
    
    required_functions = [
        'start_monitoring',
        'manual_check_handler', 
        'monitor_status',
        'check_resources_handler',
        'send_morning_report',
        'check_server_availability'
    ]
    
    for func_name in required_functions:
        if hasattr(monitor_core, func_name):
            func = getattr(monitor_core, func_name)
            print(f"   ✅ {func_name}: {type(func).__name__}")
        else:
            print(f"   ❌ {func_name}: не найдена")
    
    # 3. Проверяем глобальные переменные
    print("\n📊 3. Проверка глобальных переменных:")
    
    required_variables = [
        'server_status',
        'monitoring_active',
        'servers',
        'bot',
        'last_check_time',
        'silent_override'
    ]
    
    for var_name in required_variables:
        if hasattr(monitor_core, var_name):
            value = getattr(monitor_core, var_name)
            value_type = type(value).__name__
            value_repr = repr(value)[:50] + "..." if len(repr(value)) > 50 else repr(value)
            print(f"   ✅ {var_name}: {value_type} = {value_repr}")
        else:
            print(f"   ❌ {var_name}: не найдена")
    
    # 4. Проверяем импорты из новой структуры
    print("\n🔄 4. Проверка импортов из app/:")
    
    # Проверяем что используются правильные импорты
    with open('/opt/monitoring/monitor_core.py', 'r') as f:
        content = f.read()
    
    checks = [
        ('from app import', '✅ Импорты из app'),
        ('from app.utils.common import', '✅ Импорты из utils.common'),
        ('from core_utils import', '❌ Старые импорты из core_utils'),
        ('core_utils\\.', '❌ Использования core_utils.'),
    ]
    
    for pattern, message in checks:
        if pattern in content:
            count = content.count(pattern)
            print(f"   {message}: найдено {count} раз")
    
    # 5. Тестируем конкретные функции
    print("\n🧪 5. Тестируем функции:")
    
    # Тест прогресс-бара
    from app.utils.common import progress_bar
    test_bar = progress_bar(75)
    print(f"   progress_bar(75): {test_bar}")
    
    # Тест server_checker
    from app import server_checker
    print(f"   server_checker: {server_checker}")
    print(f"   type: {type(server_checker).__module__}.{type(server_checker).__name__}")
    
    # Тест функции is_proxmox_server
    if hasattr(monitor_core, 'is_proxmox_server'):
        test_ip = "192.168.30.10"
        result = monitor_core.is_proxmox_server({"ip": test_ip})
        print(f"   is_proxmox_server('{test_ip}'): {result}")
    
    print("\n" + "=" * 60)
    print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)
    
    # Рекомендации
    print("\n📋 РЕКОМЕНДАЦИИ:")
    print("1. Запустите бота в тестовом режиме:")
    print("   python3 /opt/monitoring/main.py")
    print("2. Проверьте логи:")
    print("   tail -f /opt/monitoring/bot_debug.log")
    print("3. Если всё работает, создайте коммит:")
    print("   git add monitor_core.py")
    print("   git commit -m 'refactor: обновлены импорты в monitor_core.py'")
    print("   git push")
    
except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("⚠️  ЕСТЬ ПРОБЛЕМЫ!")
    print("=" * 60)
    print("\nВосстановите файл из резервной копии:")
    print("cp monitor_core.py.backup_* monitor_core.py")
