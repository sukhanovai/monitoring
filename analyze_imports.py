# /opt/monitoring/analyze_imports.py
"""
Анализ импортов в monitor_core.py
"""

import re
import os

def analyze_file(filepath):
    """Анализирует импорты в файле"""
    print(f"📊 Анализ файла: {filepath}")
    print("=" * 60)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим все импорты
    import_patterns = [
        (r'from\s+(\S+)\s+import', 'from ... import'),
        (r'import\s+(\S+)', 'import ...'),
    ]
    
    imports = {}
    
    for pattern, label in import_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match not in imports:
                imports[match] = 0
            imports[match] += 1
    
    # Группируем импорты
    print("\n📦 ИМПОРТЫ В ФАЙЛЕ:")
    print("-" * 40)
    
    app_imports = []
    core_utils_imports = []
    other_imports = []
    
    for imp, count in sorted(imports.items()):
        if 'app' in imp:
            app_imports.append((imp, count))
        elif 'core_utils' in imp:
            core_utils_imports.append((imp, count))
        else:
            other_imports.append((imp, count))
    
    if app_imports:
        print("\n✅ ИМПОРТЫ ИЗ APP/:")
        for imp, count in app_imports:
            print(f"  {imp}: {count} раз")
    
    if core_utils_imports:
        print("\n⚠️  ИМПОРТЫ ИЗ CORE_UTILS (нужно обновить):")
        for imp, count in core_utils_imports:
            print(f"  {imp}: {count} раз")
    
    if other_imports:
        print("\n📚 ДРУГИЕ ИМПОРТЫ:")
        for imp, count in other_imports[:10]:  # Первые 10
            print(f"  {imp}: {count} раз")
        if len(other_imports) > 10:
            print(f"  ... и еще {len(other_imports) - 10} импортов")
    
    # Проверяем использования функций
    print("\n🔍 ИСПОЛЬЗОВАНИЯ ФУНКЦИЙ:")
    print("-" * 40)
    
    functions_to_check = [
        ('debug_log', 'debug_log'),
        ('progress_bar', 'progress_bar'),
        ('format_duration', 'format_duration'),
        ('safe_import', 'safe_import'),
        ('server_checker', 'server_checker'),
        ('DEBUG_MODE', 'DEBUG_MODE'),
    ]
    
    for old_name, new_name in functions_to_check:
        # Ищем старый формат: core_utils.xxx
        old_pattern = f'core_utils\\.{old_name}'
        old_count = len(re.findall(old_pattern, content))
        
        # Ищем новый формат: прямое использование
        new_count = len(re.findall(f'\\b{new_name}\\b', content))
        
        if old_count > 0:
            print(f"  ❌ {old_name}: {old_count} раз через core_utils")
        else:
            print(f"  ✅ {new_name}: {new_count} раз (обновлено)")
    
    # Проверяем ленивые импорты
    print("\n🔄 ЛЕНИВЫЕ ИМПОРТЫ:")
    print("-" * 40)
    
    lazy_patterns = [
        (r'lazy_import\(\'core_utils\'', 'lazy_import core_utils'),
        (r'get_debug_log\s*=', 'get_debug_log'),
        (r'get_progress_bar\s*=', 'get_progress_bar'),
        (r'get_server_checker\s*=', 'get_server_checker'),
    ]
    
    for pattern, name in lazy_patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"  ⚠️  {name}: найдено {len(matches)} раз")
        else:
            print(f"  ✅ {name}: не найдено")
    
    # Статистика
    print("\n📈 СТАТИСТИКА:")
    print("-" * 40)
    print(f"  Всего строк: {len(content.split('\\n'))}")
    print(f"  Уникальных импортов: {len(imports)}")
    print(f"  Импортов из app: {len(app_imports)}")
    print(f"  Импортов из core_utils: {len(core_utils_imports)}")
    
    return len(core_utils_imports) == 0

def check_actual_imports():
    """Проверяет реальные импорты при выполнении"""
    print("\n" + "=" * 60)
    print("🧪 ПРОВЕРКА РЕАЛЬНЫХ ИМПОРТОВ ПРИ ВЫПОЛНЕНИИ")
    print("=" * 60)
    
    import sys
    sys.path.insert(0, '/opt/monitoring')
    
    test_code = """
# Пробуем импортировать и проверить откуда берутся функции
import monitor_core

print("1. Проверяем debug_log:")
try:
    if hasattr(monitor_core, 'debug_log'):
        print("   ✅ debug_log есть в monitor_core")
        print(f"   module: {monitor_core.debug_log.__module__}")
    else:
        print("   ❌ debug_log нет в monitor_core")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\\n2. Проверяем progress_bar:")
try:
    if hasattr(monitor_core, 'progress_bar'):
        print("   ✅ progress_bar есть в monitor_core")
        print(f"   module: {monitor_core.progress_bar.__module__}")
    else:
        print("   ❌ progress_bar нет в monitor_core")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\\n3. Проверяем server_checker:")
try:
    if hasattr(monitor_core, 'server_checker'):
        print("   ✅ server_checker есть в monitor_core")
        print(f"   module: {monitor_core.server_checker.__module__}")
        print(f"   type: {type(monitor_core.server_checker)}")
    else:
        print("   ❌ server_checker нет в monitor_core")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\\n4. Проверяем глобальные переменные:")
try:
    from app import server_checker as app_checker
    from app.utils.common import debug_log as app_debug_log
    
    # Сравниваем
    if hasattr(monitor_core, 'server_checker'):
        if monitor_core.server_checker is app_checker:
            print("   ✅ server_checker совпадает с app.server_checker")
        else:
            print("   ⚠️  server_checker НЕ совпадает с app.server_checker")
            print(f"      monitor_core: {monitor_core.server_checker}")
            print(f"      app: {app_checker}")
    
    print("\\n5. Проверяем импорты в коде:")
    import inspect
    source = inspect.getsource(monitor_core)
    
    if 'from app import' in source:
        print("   ✅ Есть импорты из app")
    else:
        print("   ❌ Нет импортов из app")
    
    if 'from core_utils import' in source:
        print("   ⚠️  Есть импорты из core_utils")
    else:
        print("   ✅ Нет импортов из core_utils")
    
except Exception as e:
    print(f"   ❌ Ошибка проверки: {e}")
    import traceback
    traceback.print_exc()
"""
    
    import subprocess
    result = subprocess.run(['python3', '-c', test_code], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        return True
    else:
        print(f"❌ Ошибка выполнения: {result.stderr}")
        return False

def main():
    """Основная функция"""
    filepath = '/opt/monitoring/monitor_core.py'
    
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return
    
    # Анализируем файл
    is_updated = analyze_file(filepath)
    
    # Проверяем реальные импорты
    check_actual_imports()
    
    print("\n" + "=" * 60)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 60)
    
    if is_updated:
        print("\n✅ Файл уже обновлен!")
        print("   Все импорты из core_utils заменены на app/")
        print("\n📋 Действия:")
        print("   1. Запустите тест бота: python3 test_bot_launch.py")
        print("   2. Если всё работает, переходите к обновлению других файлов")
        print("   3. Начните с bot_menu.py или main.py")
    else:
        print("\n⚠️  Файл требует обновления!")
        print("   Есть импорты из core_utils")
        print("\n📋 Действия:")
        print("   1. Запустите: python3 update_monitor_core_fix.py")
        print("   2. Проверьте результат: python3 check_monitor_core.py")
        print("   3. Протестируйте бота: python3 test_bot_launch.py")

if __name__ == "__main__":
    main()
    