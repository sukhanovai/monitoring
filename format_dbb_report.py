#!/usr/bin/env python3
"""
Тест форматирования отчета по бэкапам БД
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def test_format_function():
    """Тестирует функцию форматирования"""
    
    print("📊 Тестируем форматирование отчета...")
    
    try:
        from extensions.backup_monitor.bot_handler import format_database_backups_report, BackupMonitorBot
        
        backup_bot = BackupMonitorBot()
        
        # Тестируем разные периоды
        for hours in [24, 48]:
            print(f"\n🔹 Тест за {hours} часов:")
            message = format_database_backups_report(backup_bot, hours)
            
            if message:
                print(f"✅ Сообщение создано ({len(message)} символов)")
                print("📝 Превью:")
                print(message[:200] + "..." if len(message) > 200 else message)
            else:
                print("❌ Сообщение не создано")
                
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_format_function()
    