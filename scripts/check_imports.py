#!/usr/bin/env python3
"""
Скрипт для проверки импортов после реорганизации
"""
import os
import sys
import re

def check_file_imports(filepath):
    """Проверяет импорты в файле"""
    issues = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем проблемные импорты
    patterns = [
        (r'from config import', 'config → app.config.settings'),
        (r'import config', 'config → app.config.settings'),
        (r'from core_utils import', 'core_utils → app.utils.common'),
        (r'import core_utils', 'core_utils → app.utils.common'),
        (r'from monitor_core import', 'monitor_core → app.core.monitoring'),
        (r'import monitor_core', 'monitor_core → app.core.monitoring'),
        (r'from settings_manager import', 'settings_manager → app.config.settings_manager'),
        (r'import settings_manager', 'settings_manager → app.config.settings_manager'),
        (r'from settings_handlers import', 'settings_handlers → app.bot.handlers'),
        (r'import settings_handlers', 'settings_handlers → app.bot.handlers'),
        (r'from bot_menu import', 'bot_menu → app.bot.menus'),
        (r'import bot_menu', 'bot_menu → app.bot.menus'),
        (r'from extensions\.', 'extensions. → app.extensions.'),
    ]
    
    for i, line in enumerate(content.split('\n'), 1):
        for pattern, replacement in patterns:
            if re.search(pattern, line):
                issues.append(f"  Строка {i}: {line.strip()} → {replacement}")
    
    return issues

def main():
    """Основная функция"""
    print("🔍 Проверка импортов после реорганизации...")
    
    files_to_check = [
        'app/core/monitoring.py',
        'app/utils/common.py',
        'app/config/settings.py',
        'app/config/settings_manager.py',
        'app/bot/menus.py',
        'app/bot/handlers.py',
        'app/extensions/extension_manager.py',
        'app/extensions/server_checks.py',
        'app/extensions/utils.py',
        'app/extensions/web_interface.py',
        'app/extensions/backup_monitor/bot_handler.py',
        'app/extensions/backup_monitor/backup_handlers.py',
        'app/extensions/backup_monitor/backup_utils.py',
        'app/extensions/mail_monitor.py',
        'main.py'
    ]
    
    all_issues = []
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            print(f"\n📄 Проверка {filepath}...")
            issues = check_file_imports(filepath)
            
            if issues:
                all_issues.extend([f"{filepath}: {issue}" for issue in issues])
                for issue in issues:
                    print(f"  ⚠️  {issue}")
            else:
                print("  ✅ Нет проблемных импортов")
        else:
            print(f"\n📄 {filepath}: ❌ Файл не существует")
    
    if all_issues:
        print(f"\n⚠️  Всего проблем: {len(all_issues)}")
        print("\nДля исправления выполните:")
        print("1. Откройте каждый проблемный файл")
        print("2. Найдите строки с импортами")
        print("3. Замените старые пути на новые согласно указаниям выше")
    else:
        print("\n🎉 Все импорты корректны!")

if __name__ == "__main__":
    main()
    