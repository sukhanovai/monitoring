#!/usr/bin/env python3
"""
Тест обработчиков команд бэкапов
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def test_handlers():
    """Тестирует наличие обработчиков"""
    
    print("🔍 Проверяем обработчики команд...")
    
    try:
        from extensions.backup_monitor.bot_handler import (
            backup_command, backup_search_command, backup_help_command,
            database_backups_command, setup_backup_commands
        )
        print("✅ Все обработчики импортируются")
        
        # Проверим функцию setup
        from telegram.ext import Dispatcher
        class MockDispatcher:
            def __init__(self):
                self.handlers = []
            def add_handler(self, handler):
                self.handlers.append(handler)
        
        mock_dp = MockDispatcher()
        setup_backup_commands(mock_dp)
        
        print(f"✅ Зарегистрировано обработчиков: {len(mock_dp.handlers)}")
        for handler in mock_dp.handlers:
            print(f"   - {type(handler).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_handlers()
    