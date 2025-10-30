#!/usr/bin/env python3
"""
Скрипт для создания таблицы database_backups
"""

import sqlite3
import os

def create_database_backups_table():
    """Создает таблицу для бэкапов баз данных"""
    
    db_path = '/opt/monitoring/data/backups.db'
    
    print(f"🔧 Создаем таблицу database_backups в {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицу для бэкапов баз данных
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS database_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_name TEXT NOT NULL,
            database_name TEXT NOT NULL,
            database_display_name TEXT,
            backup_status TEXT NOT NULL,
            backup_type TEXT,
            task_type TEXT,
            error_count INTEGER DEFAULT 0,
            email_subject TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Создаем индекс для быстрого поиска
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_db_backups_type_date 
        ON database_backups(backup_type, received_at)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Таблица database_backups создана")

def check_table_exists():
    """Проверяет существование таблицы"""
    db_path = '/opt/monitoring/data/backups.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='database_backups'")
    table_exists = cursor.fetchone()
    
    conn.close()
    
    if table_exists:
        print("✅ Таблица database_backups существует")
        return True
    else:
        print("❌ Таблица database_backups не существует")
        return False

if __name__ == "__main__":
    create_database_backups_table()
    check_table_exists()
    