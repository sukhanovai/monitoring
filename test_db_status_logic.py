#!/usr/bin/env python3
"""
Тестирование новой логики статусов для БД
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from extensions.backup_monitor.bot_handler import BackupMonitorBot

def test_db_status_logic():
    bot = BackupMonitorBot()
    
    print("🔍 Тестирование новой логики статусов для БД:\n")
    
    # Тестируем несколько известных БД
    test_databases = [
        ('company_database', 'acc30_ge'),
        ('company_database', 'wms'),
        ('barnaul', '1c_smb'),
        ('client', 'unf')
    ]
    
    for backup_type, db_name in test_databases:
        print(f"🎯 БД: {backup_type}.{db_name}")
        
        # Тестируем get_database_recent_status
        recent = bot.get_database_recent_status(backup_type, db_name, 48)
        print(f"   Бэкапов за 48ч: {len(recent)}")
        
        # Тестируем get_database_display_status  
        status = bot.get_database_display_status(backup_type, db_name)
        print(f"   Статус отображения: {status}")
        
        # Показываем последние бэкапы
        if recent:
            for i, (backup_status, received_at, error_count) in enumerate(recent[:2]):
                icon = "✅" if backup_status == 'success' else "❌"
                error_info = f" (ошибок: {error_count})" if error_count else ""
                print(f"     {i+1}. {icon} {received_at}: {backup_status}{error_info}")
        
        print()

if __name__ == "__main__":
    test_db_status_logic()