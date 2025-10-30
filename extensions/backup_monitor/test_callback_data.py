#!/usr/bin/env python3
"""
Тест реальных callback данных
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def test_real_callback_data():
    """Тестирует реальные callback данные"""
    
    print("🔍 Тестируем реальные callback данные...")
    
    try:
        from extensions.backup_monitor.bot_handler import create_main_keyboard, create_database_backups_keyboard
        
        # Проверим основную клавиатуру
        main_kb = create_main_keyboard()
        print("📋 Основная клавиатура:")
        for row in main_kb.inline_keyboard:
            for button in row:
                print(f"   🎯 {button.text} -> {button.callback_data}")
        
        # Проверим клавиатуру бэкапов БД
        db_kb = create_database_backups_keyboard()
        print("\n📋 Клавиатура бэкапов БД:")
        for row in db_kb.inline_keyboard:
            for button in row:
                print(f"   🎯 {button.text} -> {button.callback_data}")
                
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_real_callback_data()
    