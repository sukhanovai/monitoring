#!/usr/bin/env python3
"""
Migration script to update monitor_core.py to use new structure
Скрипт миграции для обновления monitor_core.py
"""

import os
import sys

def update_monitor_core():
    """Обновляет импорты в monitor_core.py"""
    monitor_core_path = "/opt/monitoring/monitor_core.py"
    
    if not os.path.exists(monitor_core_path):
        print(f"❌ Файл {monitor_core_path} не найден")
        return False
    
    # Читаем содержимое файла
    with open(monitor_core_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем старые импорты на новые
    replacements = [
        # Заменяем импорты из app.utils
        ("from app.utils import debug_log, progress_bar, format_duration, safe_import, DEBUG_MODE",
         "from lib.logging import debug_log\nfrom lib.utils import progress_bar, format_duration, safe_import\nfrom config.settings import DEBUG_MODE"),
        
        # Заменяем импорт send_alert если он есть
        ("from lib.alerts import send_alert", ""),  # Удаляем, т.к. будет импортирован из monitor_core
        
        # Добавляем новые импорты в начало файла
        ("\"\"\"\nServer Monitoring System v4.10.3",
         "\"\"\"\nServer Monitoring System v4.10.3 (Updated)\n\nNote: This file uses new modular structure\nПримечание: Этот файл использует новую модульную структуру\n\"\"\"\n\n# Новые импорты из модульной структуры\nfrom lib.logging import debug_log\nfrom lib.alerts import send_alert\nfrom lib.utils import progress_bar, format_duration\nfrom config.settings import DEBUG_MODE\nfrom core.monitor import monitor\nfrom modules.availability import availability_checker\nfrom modules.resources import resources_checker\nfrom modules.morning_report import morning_report\nfrom modules.targeted_checks import targeted_checks\n\n# Старые импорты для совместимости"),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Добавляем предупреждение в начало файла
    warning = "\n" + "#" * 80 + "\n"
    warning += "# ВНИМАНИЕ: Этот файл был автоматически обновлен\n"
    warning += "# Для использования новой структуры импортируйте модули напрямую:\n"
    warning += "# from modules.availability import availability_checker\n"
    warning += "# from modules.resources import resources_checker\n"
    warning += "# и т.д.\n"
    warning += "#" * 80 + "\n\n"
    
    # Вставляем предупреждение после docstring
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '"""' and i > 0:
            # Нашли закрывающий docstring
            lines.insert(i + 1, warning)
            break
    
    content = '\n'.join(lines)
    
    # Создаем резервную копию
    backup_path = monitor_core_path + ".backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(open(monitor_core_path, 'r', encoding='utf-8').read())
    print(f"✅ Создана резервная копия: {backup_path}")
    
    # Сохраняем обновленный файл
    with open(monitor_core_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Файл {monitor_core_path} обновлен")
    return True

if __name__ == "__main__":
    print("🔄 Начинаю миграцию monitor_core.py...")
    if update_monitor_core():
        print("✅ Миграция завершена успешно!")
        print("\n📋 Дальнейшие действия:")
        print("1. Протестируйте систему: python3 test_new_structure.py")
        print("2. Перезапустите бота: systemctl restart monitoring-bot")
        print("3. Проверьте логи: tail -f /opt/monitoring/logs/debug.log")
    else:
        print("❌ Миграция не удалась")
        sys.exit(1)