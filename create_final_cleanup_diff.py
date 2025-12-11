# /opt/monitoring/create_final_cleanup_diff.py
"""
Создание финального diff для очистки monitor_core.py
"""

import os
import re
import subprocess
import tempfile

def create_cleanup_diff():
    """Создает diff для очистки monitor_core.py"""
    print("🔧 Создаю diff для окончательной очистки monitor_core.py...")
    
    filepath = '/opt/monitoring/monitor_core.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Создаем модифицированную версию
    modified = content
    
    # 1. Удаляем лямбда-обертки (оставляем комментарии)
    patterns_to_remove = [
        # Полностью удаляем строки с лямбдами
        r'get_server_checker = lambda: server_checker\n',
        r'get_debug_log = lambda: debug_log\n', 
        r'get_progress_bar = lambda: progress_bar\n',
    ]
    
    for pattern in patterns_to_remove:
        modified = re.sub(pattern, '', modified)
    
    # 2. Заменяем вызовы геттеров на прямые вызовы
    replacements = [
        # Заменяем вызовы типа: debug_log = get_debug_log()
        (r'(\s*)debug_log = get_debug_log\(\)', r'\1# debug_log уже импортирован напрямую'),
        (r'(\s*)progress_bar = get_progress_bar\(\)', r'\1# progress_bar уже импортирован напрямую'),
        (r'(\s*)server_checker = get_server_checker\(\)', r'\1# server_checker уже импортирован напрямую'),
        
        # Заменяем использования в коде: get_debug_log() -> debug_log
        (r'get_debug_log\(\)', 'debug_log'),
        (r'get_progress_bar\(\)', 'progress_bar'),
        (r'get_server_checker\(\)', 'server_checker'),
    ]
    
    for old, new in replacements:
        modified = re.sub(old, new, modified)
    
    # 3. Очищаем пустые строки
    lines = modified.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Убираем полностью пустые строки после удаления
        if line.strip() != '' or (i > 0 and lines[i-1].strip() != '' and i < len(lines)-1 and lines[i+1].strip() != ''):
            cleaned_lines.append(line)
    
    modified = '\n'.join(cleaned_lines)
    
    # 4. Создаем временные файлы для diff
    with tempfile.NamedTemporaryFile(mode='w', suffix='.orig', delete=False) as f:
        f.write(content)
        orig_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mod', delete=False) as f:
        f.write(modified)
        mod_file = f.name
    
    # 5. Создаем diff
    result = subprocess.run(
        ['diff', '-u', orig_file, mod_file],
        capture_output=True,
        text=True
    )
    
    # 6. Сохраняем diff
    diff_file = '/opt/monitoring/monitor_core_cleanup.diff'
    if result.stdout:
        with open(diff_file, 'w') as f:
            f.write(result.stdout)
        
        print(f"✅ Diff создан: {diff_file}")
        
        # Показываем изменения
        print("\n🔍 ПРЕДПРОСМОТР ИЗМЕНЕНИЙ:")
        print("=" * 60)
        lines = result.stdout.split('\n')
        changes_shown = 0
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                print(f"  {line}")
                changes_shown += 1
            elif line.startswith('-') and not line.startswith('---'):
                print(f"  {line}")
                changes_shown += 1
            if changes_shown >= 15:  # Ограничиваем вывод
                print("  ... (еще изменения)")
                break
        print("=" * 60)
        
        # Проверяем что diff корректен
        print("\n🧪 Тестируем diff...")
        test_result = subprocess.run(
            ['patch', '--dry-run', filepath, '-i', diff_file],
            capture_output=True,
            text=True
        )
        
        if test_result.returncode == 0:
            print("✅ Diff корректен и может быть применен")
        else:
            print(f"❌ Проблема с diff: {test_result.stderr}")
    
    else:
        print("ℹ️  Нет изменений для создания diff")
    
    # Удаляем временные файлы
    os.unlink(orig_file)
    os.unlink(mod_file)
    
    return bool(result.stdout)

def create_bot_menu_cleanup_diff():
    """Создает diff для очистки bot_menu.py"""
    print("\n🔧 Создаю diff для очистки bot_menu.py...")
    
    filepath = '/opt/monitoring/bot_menu.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = content
    
    # Заменяем лямбда-обертки
    replacements = [
        (r'get_debug_log = lambda: debug_log', '# get_debug_log заменен на прямую функцию debug_log'),
        (r'get_progress_bar = lambda: progress_bar', '# get_progress_bar заменен на прямую функцию progress_bar'),
        
        # Заменяем вызовы
        (r'get_debug_log\(\)', 'debug_log'),
        (r'get_progress_bar\(\)', 'progress_bar'),
    ]
    
    for old, new in replacements:
        modified = re.sub(old, new, modified)
    
    # Создаем diff
    with tempfile.NamedTemporaryFile(mode='w', suffix='.orig', delete=False) as f:
        f.write(content)
        orig_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mod', delete=False) as f:
        f.write(modified)
        mod_file = f.name
    
    result = subprocess.run(
        ['diff', '-u', orig_file, mod_file],
        capture_output=True,
        text=True
    )
    
    diff_file = '/opt/monitoring/bot_menu_cleanup.diff'
    if result.stdout:
        with open(diff_file, 'w') as f:
            f.write(result.stdout)
        print(f"✅ Diff создан: {diff_file}")
    else:
        print("ℹ️  Нет изменений для bot_menu.py")
    
    os.unlink(orig_file)
    os.unlink(mod_file)
    
    return bool(result.stdout)

def main():
    """Основная функция"""
    print("=" * 70)
    print("СОЗДАНИЕ DIFF-ФАЙЛОВ ДЛЯ ОКОНЧАТЕЛЬНОЙ ОЧИСТКИ")
    print("=" * 70)
    
    monitor_diff = create_cleanup_diff()
    bot_menu_diff = create_bot_menu_cleanup_diff()
    
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТ:")
    print("=" * 70)
    
    if monitor_diff or bot_menu_diff:
        print("\n✅ Созданы diff-файлы:")
        if monitor_diff:
            print("  - monitor_core_cleanup.diff")
        if bot_menu_diff:
            print("  - bot_menu_cleanup.diff")
        
        print("\n📋 ИНСТРУКЦИЯ ДЛЯ ПРИМЕНЕНИЯ В VSCODE:")
        print("1. Скопируйте diff-файлы в папку проекта")
        print("2. Примените командами:")
        print("   git apply monitor_core_cleanup.diff")
        print("   git apply bot_menu_cleanup.diff")
        print("3. Или примените через patch:")
        print("   patch -p1 < monitor_core_cleanup.diff")
        print("4. Проверьте изменения:")
        print("   git diff")
        print("5. Протестируйте:")
        print("   python3 check_imports.py")
        print("6. Закоммитьте:")
        print("   git add .")
        print("   git commit -m 'refactor: окончательная очистка ленивых импортов'")
    else:
        print("\nℹ️  Нет изменений для создания diff-файлов")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
    