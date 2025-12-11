"""
Безопасное обновление импортов в monitor_core.py
"""

import os
import re
import tempfile
import subprocess

def backup_file(filepath):
    """Создает резервную копию файла"""
    import shutil
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    
    shutil.copy2(filepath, backup_path)
    print(f"📋 Создана резервная копия: {backup_path}")
    return backup_path

def test_imports(filepath):
    """Тестирует импорты в файле"""
    print(f"\n🧪 Тестируем импорты в {filepath}...")
    
    test_code = f"""
import sys
import os

# Добавляем пути
sys.path.insert(0, '/opt/monitoring')
sys.path.insert(0, '/opt/monitoring/app')

# Пробуем импортировать обновленный файл
try:
    # Сначала импортируем необходимые модули
    from app import server_checker, logger
    from app.utils.common import debug_log, progress_bar, format_duration, safe_import, DEBUG_MODE
    
    print("✅ Базовые импорты работают")
    
    # Теперь пробуем импортировать сам файл
    module_name = os.path.basename('{filepath}').replace('.py', '')
    module = __import__(module_name)
    
    print(f"✅ Модуль {{module_name}} импортирован")
    
    # Проверяем наличие ключевых функций
    required_funcs = ['start_monitoring', 'manual_check_handler', 'monitor_status']
    for func in required_funcs:
        if hasattr(module, func):
            print(f"✅ Функция {{func}} найдена")
        else:
            print(f"⚠️  Функция {{func}} не найдена")
    
    print("\\n🎉 Все импорты работают корректно!")
    return True
    
except Exception as e:
    print(f"❌ Ошибка импорта: {{e}}")
    import traceback
    traceback.print_exc()
    return False
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        test_file = f.name
    
    try:
        result = subprocess.run(['python3', test_file], 
                              capture_output=True, text=True, timeout=10)
        
        os.unlink(test_file)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Тест не пройден:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        os.unlink(test_file)
        print("❌ Тест превысил время выполнения")
        return False

def update_imports(filepath):
    """Обновляет импорты в файле"""
    print(f"\n🔄 Обновляю импорты в {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Сначала добавляем новые импорты в начало (после docstring)
    new_imports = """
# ============================================================================
# НОВАЯ МОДУЛЬНАЯ СТРУКТУРА v4.0
# Импорты из app/ (замена core_utils)
# ============================================================================
from app import server_checker, logger
from app.utils.common import debug_log, progress_bar, format_duration, safe_import, DEBUG_MODE
"""
    
    # Находим позицию для вставки (после docstring)
    lines = content.split('\n')
    insert_pos = 0
    
    for i, line in enumerate(lines):
        if i == 0 and line.startswith('#!/'):
            continue  # Пропускаем shebang
        if line.startswith('"""') or line.startswith("'''"):
            # Нашли docstring, ищем его конец
            for j in range(i + 1, len(lines)):
                if lines[j].startswith('"""') or lines[j].startswith("'''"):
                    insert_pos = j + 1
                    break
            break
        elif i > 5:  # Если нет явного docstring
            # Ищем первый не-импорт
            if not line.startswith('import ') and not line.startswith('from '):
                insert_pos = i
                break
    
    # Вставляем новые импорты
    if insert_pos > 0:
        lines.insert(insert_pos, new_imports)
    
    # 2. Заменяем использования ленивых импортов
    updated_content = '\n'.join(lines)
    
    # Заменяем get_debug_log() на debug_log
    updated_content = re.sub(
        r'get_debug_log = lazy_import\(\'core_utils\', \'debug_log\'\)',
        '# get_debug_log заменен на прямую функцию debug_log\nget_debug_log = lambda: debug_log',
        updated_content
    )
    
    updated_content = re.sub(
        r'get_progress_bar = lazy_import\(\'core_utils\', \'progress_bar\'\)',
        '# get_progress_bar заменен на прямую функцию progress_bar\nget_progress_bar = lambda: progress_bar',
        updated_content
    )
    
    updated_content = re.sub(
        r'get_server_checker = lazy_import\(\'core_utils\', \'server_checker\'\)',
        '# get_server_checker заменен на server_checker из app\nget_server_checker = lambda: server_checker',
        updated_content
    )
    
    # 3. Заменяем вызовы этих функций
    updated_content = re.sub(
        r'debug_log = get_debug_log\(\)',
        '# debug_log теперь импортируется напрямую\n# debug_log = debug_log (уже импортировано)',
        updated_content
    )
    
    updated_content = re.sub(
        r'progress_bar = get_progress_bar\(\)',
        '# progress_bar теперь импортируется напрямую\n# progress_bar = progress_bar (уже импортировано)',
        updated_content
    )
    
    # 4. Заменяем прямые использования core_utils
    replacements = [
        (r'from core_utils import debug_log', '# from core_utils import debug_log (заменено выше)'),
        (r'from core_utils import progress_bar', '# from core_utils import progress_bar (заменено выше)'),
        (r'from core_utils import format_duration', '# from core_utils import format_duration (заменено выше)'),
        (r'from core_utils import safe_import', '# from core_utils import safe_import (заменено выше)'),
        (r'core_utils\.debug_log', 'debug_log'),
        (r'core_utils\.progress_bar', 'progress_bar'),
        (r'core_utils\.format_duration', 'format_duration'),
        (r'core_utils\.safe_import', 'safe_import'),
        (r'core_utils\.DEBUG_MODE', 'DEBUG_MODE'),
    ]
    
    for old, new in replacements:
        updated_content = re.sub(old, new, updated_content)
    
    # 5. Убираем дублирование импортов config
    updated_content = re.sub(
        r'get_config = lazy_import\(\'config\'\)',
        'get_config = lambda: __import__(\'config\')',
        updated_content
    )
    
    updated_content = re.sub(
        r'get_check_interval = lazy_import\(\'config\', \'CHECK_INTERVAL\'\)',
        'get_check_interval = lambda: __import__(\'config\').CHECK_INTERVAL',
        updated_content
    )
    
    # Добавляем комментарий в конце файла
    if not updated_content.strip().endswith('# end of file'):
        updated_content += '\n\n# ============================================================================\n'
        updated_content += '# КОНЕЦ ФАЙЛА - импорты обновлены для новой структуры\n'
        updated_content += '# ============================================================================\n'
    
    return original_content, updated_content

def main():
    """Основная функция"""
    print("=" * 70)
    print("БЕЗОПАСНОЕ ОБНОВЛЕНИЕ IMPORTS В MONITOR_CORE.PY")
    print("=" * 70)
    
    filepath = '/opt/monitoring/monitor_core.py'
    
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return
    
    print(f"📄 Файл: {filepath}")
    print(f"📏 Размер: {os.path.getsize(filepath)} байт")
    
    # Шаг 1: Создаем резервную копию
    backup_path = backup_file(filepath)
    
    # Шаг 2: Обновляем импорты
    original, updated = update_imports(filepath)
    
    # Шаг 3: Сохраняем во временный файл и тестируем
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(updated)
        temp_file = tmp.name
    
    print(f"\n📝 Создан временный файл для тестирования: {temp_file}")
    
    # Шаг 4: Тестируем импорты
    if test_imports(temp_file):
        print("\n✅ Тест пройден! Сохраняем изменения...")
        
        # Сохраняем обновленный файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        
        print(f"✅ Файл обновлен: {filepath}")
        
        # Дополнительная проверка синтаксиса
        print("\n🧪 Дополнительная проверка синтаксиса...")
        result = subprocess.run(['python3', '-m', 'py_compile', filepath],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Синтаксис корректен")
            
            # Запускаем быстрый тест функций
            print("\n🧪 Тестируем основные функции...")
            test_functions = """
import sys
sys.path.insert(0, '/opt/monitoring')

try:
    import monitor_core
    
    # Проверяем основные функции
    funcs_to_check = ['start_monitoring', 'manual_check_handler', 'monitor_status']
    
    for func_name in funcs_to_check:
        if hasattr(monitor_core, func_name):
            func = getattr(monitor_core, func_name)
            print(f"✅ {{func_name}}: {{func}}")
        else:
            print(f"❌ {{func_name}}: не найдена")
    
    # Проверяем глобальные переменные
    globals_to_check = ['server_status', 'monitoring_active', 'servers']
    
    for var_name in globals_to_check:
        if hasattr(monitor_core, var_name):
            print(f"✅ {{var_name}}: найдена")
        else:
            print(f"⚠️  {{var_name}}: не найдена")
    
    print("\\n🎉 Все проверки пройдены!")
    
except Exception as e:
    print(f"❌ Ошибка: {{e}}")
    import traceback
    traceback.print_exc()
"""
            
            result = subprocess.run(['python3', '-c', test_functions],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Ошибка тестирования функций: {result.stderr}")
        
        else:
            print(f"❌ Ошибка синтаксиса: {result.stderr}")
            print("\n⚠️  Восстанавливаю из резервной копии...")
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            print(f"✅ Файл восстановлен из: {backup_path}")
    
    else:
        print("\n❌ Тест не пройден. Отмена изменений...")
        
        # Восстанавливаем из резервной копии
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        
        print(f"✅ Файл восстановлен из резервной копии: {backup_path}")
    
    # Удаляем временный файл
    try:
        os.unlink(temp_file)
    except:
        pass
    
    print("\n" + "=" * 70)
    print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
    print("=" * 70)
    print(f"\nРезервная копия: {backup_path}")
    print(f"Основной файл:   {filepath}")

if __name__ == "__main__":
    main()
