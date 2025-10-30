#!/usr/bin/env python3
"""
Тест обработки писем с бэкапами
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from improved_mail_monitor import BackupProcessor

def test_email_processing():
    """Тестирует обработку писем"""
    print("🧪 Тестируем обработку писем...")
    
    processor = BackupProcessor()
    
    # Проверяем новые письма
    processed = processor.process_new_emails()
    print(f"✅ Обработано новых писем: {processed}")
    
    # Проверяем базу данных после обработки
    if processed > 0:
        print("🔄 Проверяем обновления в базе данных...")
        import sqlite3
        from config import BACKUP_DATABASE_CONFIG
        
        conn = sqlite3.connect(BACKUP_DATABASE_CONFIG['backups_db'])
        cursor = conn.cursor()
        
        # Последние записи
        cursor.execute('''
            SELECT host_name, backup_status, task_type, received_at 
            FROM proxmox_backups 
            ORDER BY received_at DESC 
            LIMIT 5
        ''')
        recent = cursor.fetchall()
        
        print("📝 Последние записи в базе:")
        for record in recent:
            print(f"   - {record}")
        
        conn.close()

if __name__ == "__main__":
    test_email_processing()