#!/usr/bin/env python3
"""
Скрипт для проверки данных в базе backups.db
"""

import sqlite3
from datetime import datetime, timedelta

def check_database_data():
    db_path = '/opt/monitoring/data/backups.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📊 Проверка данных в database_backups:")
    
    # Проверим все записи за последние 48 часов
    since_time = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        SELECT backup_type, database_name, database_display_name, backup_status, COUNT(*), MAX(received_at)
        FROM database_backups 
        WHERE received_at >= ?
        GROUP BY backup_type, database_name, database_display_name, backup_status
        ORDER BY backup_type, database_name
    ''', (since_time,))
    
    results = cursor.fetchall()
    
    print(f"Найдено {len(results)} записей:")
    for backup_type, db_name, display_name, status, count, last_backup in results:
        print(f"  {backup_type} | {db_name} | {display_name} | {status} | {count} | {last_backup}")
    
    conn.close()

if __name__ == "__main__":
    check_database_data()
    