#!/usr/bin/env python3
"""
Скрипт для обновления структуры базы данных бэкапов
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database_structure():
    """Обновляет структуру базы данных для предотвращения дубликатов"""
    db_path = '/opt/monitoring/data/backups.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем временную таблицу для proxmox_backups с UNIQUE constraint
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxmox_backups_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_name TEXT NOT NULL,
                backup_status TEXT NOT NULL,
                task_type TEXT,
                duration TEXT,
                total_size TEXT,
                error_message TEXT,
                email_subject TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(host_name, received_at)
            )
        ''')
        
        # Копируем данные из старой таблицы, игнорируя дубликаты
        cursor.execute('''
            INSERT OR IGNORE INTO proxmox_backups_new 
            (host_name, backup_status, task_type, duration, total_size, error_message, email_subject, received_at)
            SELECT host_name, backup_status, task_type, duration, total_size, error_message, email_subject, received_at
            FROM proxmox_backups
        ''')
        
        # Переименовываем таблицы
        cursor.execute('DROP TABLE IF EXISTS proxmox_backups_old')
        cursor.execute('ALTER TABLE proxmox_backups RENAME TO proxmox_backups_old')
        cursor.execute('ALTER TABLE proxmox_backups_new RENAME TO proxmox_backups')
        
        # Создаем индексы
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_backups_host_date 
            ON proxmox_backups(host_name, received_at)
        ''')
        
        # Для database_backups тоже добавляем UNIQUE constraint
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS database_backups_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_name TEXT NOT NULL,
                database_name TEXT NOT NULL,
                database_display_name TEXT,
                backup_status TEXT NOT NULL,
                backup_type TEXT,
                task_type TEXT,
                error_count INTEGER DEFAULT 0,
                email_subject TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(host_name, database_name, received_at)
            )
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO database_backups_new 
            (host_name, database_name, database_display_name, backup_status, backup_type, task_type, error_count, email_subject, received_at)
            SELECT host_name, database_name, database_display_name, backup_status, backup_type, task_type, error_count, email_subject, received_at
            FROM database_backups
        ''')
        
        cursor.execute('DROP TABLE IF EXISTS database_backups_old')
        cursor.execute('ALTER TABLE database_backups RENAME TO database_backups_old')
        cursor.execute('ALTER TABLE database_backups_new RENAME TO database_backups')
        
        conn.commit()
        logger.info("✅ Структура базы данных успешно обновлена")
        
        # Статистика
        cursor.execute('SELECT COUNT(*) FROM proxmox_backups')
        proxmox_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM database_backups')
        db_count = cursor.fetchone()[0]
        
        logger.info(f"📊 Записей в proxmox_backups: {proxmox_count}")
        logger.info(f"📊 Записей в database_backups: {db_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления структуры БД: {e}")
        conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_database_structure()
    