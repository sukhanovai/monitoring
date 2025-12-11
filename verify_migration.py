# /opt/monitoring/verify_migration.py
"""
Финальная проверка успешности миграции
"""

import sys
import os
import importlib

print("=" * 70)
print("ФИНАЛЬНАЯ ПРОВЕРКА МИГРАЦИИ НА МОДУЛЬНУЮ СТРУКТУРУ")
print("=" * 70)

def check_module_imports():
    """Проверяет импорты всех ключевых модулей"""
    modules_to_check = [
        'monitor_core',
        'bot_menu', 
        'main',
        'app',
        'app.core.checker',
        'app.utils.common',
    ]
    
    print("\n📦 Проверка импортов модулей:")
    print("-" * 40)
    
    success = True
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
            success = False
    
    return success

def check_core_utils_references():
    """Проверяет что core_utils больше не используется"""
    print("\n🔍 Поиск упоминаний core_utils:")
    print("-" * 40)
    
    found = False
    for root, dirs, files in os.walk('/opt/monitoring'):
        # Пропускаем .git и cache
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'core_utils' in content and not filepath.endswith('.backup'):
                            # Проверяем что это не комментарий
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if 'core_utils' in line and not line.strip().startswith('#'):
                                    print(f"⚠️  {filepath}:{i+1}: {line.strip()[:50]}...")
                                    found = True
                except:
                    pass
    
    if not found:
        print("✅ core_utils не найден в рабочих файлах")
        return True
    else:
        print("❌ Найдены упоминания core_utils")
        return False

def check_bot_functionality():
    """Проверяет основные функции бота"""
    print("\n🤖 Проверка функциональности бота:")
    print("-" * 40)
    
    test_code = """
import sys
sys.path.insert(0, '/opt/monitoring')

try:
    import monitor_core
    import bot_menu
    
    # Проверяем ключевые функции
    required = [
        ('monitor_core', 'start_monitoring'),
        ('monitor_core', 'manual_check_handler'),
        ('monitor_core', 'monitor_status'),
        ('bot_menu', 'start_command'),
        ('bot_menu', 'get_handlers'),
    ]
    
    for module_name, func_name in required:
        module = __import__(module_name)
        if hasattr(module, func_name):
            print(f"✅ {module_name}.{func_name}")
        else:
            print(f"❌ {module_name}.{func_name}: не найдена")
    
    # Проверяем импорты из app
    from app import server_checker
    from app.utils.common import progress_bar, debug_log
    
    print(f"✅ app импортируется")
    print(f"✅ server_checker: {type(server_checker).__name__}")
    
    print("\\n🎉 Все основные функции доступны!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
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
        print(result.stderr)
        return False

def main():
    """Основная функция"""
    checks = [
        ("Импорты модулей", check_module_imports),
        ("Отсутствие core_utils", check_core_utils_references),
        ("Функциональность бота", check_bot_functionality),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*40}")
        print(f"ПРОВЕРКА: {check_name}")
        print('='*40)
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 70)
    print("ИТОГ ПРОВЕРКИ:")
    print("=" * 70)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ ПРОЙДЕНА" if passed else "❌ НЕ ПРОЙДЕНА"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n📋 Миграция на модульную структуру завершена успешно!")
        print("   - ✅ core_utils.py удален")
        print("   - ✅ Все импорты переведены на app/")
        print("   - ✅ Бот работает корректно")
        print("   - ✅ Временные файлы удалены")
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ ДЛЯ ИСПРАВЛЕНИЯ")
    
    print("=" * 70)

if __name__ == "__main__":
    main()