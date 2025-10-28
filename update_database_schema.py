#!/usr/bin/env python3
"""
Обновление схемы базы данных для бэкапов
"""

import sqlite3
import os

def update_database_schema():
    """Обновляет схему базы данных до актуальной версии"""
    
    db_path = '/opt/monitoring/data/backups.db'
    
    print("🔄 Обновление схемы базы данных...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем текущую структуру таблицы
        cursor.execute("PRAGMA table_info(proxmox_backups)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📊 Текущие колонки: {column_names}")
        
        # Создаем новую таблицу с правильной структурой
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxmox_backups_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_name TEXT NOT NULL,
                host_ip TEXT,
                backup_status TEXT NOT NULL,
                task_type TEXT,
                vm_count INTEGER DEFAULT 0,
                successful_vms INTEGER DEFAULT 0,
                failed_vms INTEGER DEFAULT 0,
                start_time TEXT,
                end_time TEXT,
                duration TEXT,
                total_size TEXT,
                error_message TEXT,
                email_subject TEXT,
                raw_subject TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(host_name, received_at)
            )
        ''')
        
        # Если старая таблица существует, переносим данные
        if 'proxmox_backups' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
            print("🔄 Перенос данных из старой таблицы...")
            
            # Пробуем перенести данные, если структура совместима
            try:
                cursor.execute('''
                    INSERT INTO proxmox_backups_new 
                    (host_name, backup_status, duration, total_size, error_message, received_at)
                    SELECT host_name, status, duration, size, error_message, received_at 
                    FROM proxmox_backups
                ''')
                print("✅ Данные успешно перенесены")
            except Exception as e:
                print(f"⚠️ Не удалось перенести данные: {e}")
                print("📝 Создаем пустую таблицу")
            
            # Удаляем старую таблицу
            cursor.execute('DROP TABLE IF EXISTS proxmox_backups')
        
        # Переименовываем новую таблицу
        cursor.execute('ALTER TABLE proxmox_backups_new RENAME TO proxmox_backups')
        
        # Создаем индексы
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_proxmox_backups_host_date 
            ON proxmox_backups(host_name, received_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_proxmox_backups_status 
            ON proxmox_backups(backup_status, received_at)
        ''')
        
        # Очищаем старые записи
        cursor.execute('''
            DELETE FROM proxmox_backups 
            WHERE received_at < datetime('now', '-90 days')
        ''')
        
        conn.commit()
        print("✅ Схема базы данных успешно обновлена")
        
        # Проверяем новую структуру
        cursor.execute("PRAGMA table_info(proxmox_backups)")
        new_columns = cursor.fetchall()
        print(f"📊 Новые колонки: {[col[1] for col in new_columns]}")
        
    except Exception as e:
        print(f"❌ Ошибка обновления схемы: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_database_from_scratch():
    """Инициализирует базу данных с нуля"""
    
    print("🆕 Инициализация базы данных с нуля...")
    
    # Удаляем старую базу
    db_path = '/opt/monitoring/data/backups.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Удалена старая база данных")
    
    # Инициализируем заново
    from init_email_system import init_databases
    init_databases()
    
    print("✅ База данных инициализирована с нуля")

if __name__ == "__main__":
    print("🗄️  Обновление базы данных бэкапов\n")
    
    # Сначала пробуем обновить схему
    update_database_schema()
    
    # Если не получилось, инициализируем с нуля
    input("\n🔄 Нажмите Enter для добавления тестовых данных...")
    
    # Добавляем тестовые данные
    from test_email_processing import add_sample_data
    add_sample_data()