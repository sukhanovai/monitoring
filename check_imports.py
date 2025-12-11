#!/usr/bin/env python3
"""
Быстрая проверка импортов после миграции
"""

import sys
sys.path.insert(0, '/opt/monitoring')

print("🔍 Быстрая проверка импортов...")

try:
    # Проверяем основные импорты
    import monitor_core
    import bot_menu
    from app import server_checker, logger
    from app.utils.common import progress_bar, debug_log, DEBUG_MODE
    
    print("✅ Все основные импорты работают")
    print(f"   server_checker: {server_checker}")
    print(f"   progress_bar(75): {progress_bar(75)}")
    print(f"   DEBUG_MODE: {DEBUG_MODE}")
    
    # Проверяем что core_utils не используется
    import ast
    with open('monitor_core.py', 'r') as f:
        content = f.read()
    
    if 'core_utils' in content:
        print("⚠️  Внимание: 'core_utils' все еще упоминается в monitor_core.py")
    else:
        print("✅ 'core_utils' не упоминается в monitor_core.py")
    
    print("\n🎉 Проверка завершена успешно!")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    