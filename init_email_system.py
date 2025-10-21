# /opt/monitoring/init_email_system.py

#!/usr/bin/env python3
"""
Инициализация системы обработки писем
"""

import sqlite3
import os

def init_databases():
    """Инициализирует все базы данных с правильной схемой"""
    
    print("🗄️  Инициализация баз данных...")
    
    # База бэкапов Proxmox
    conn = sqlite3.connect('/opt/monitoring/data/backups.db')
    cursor = conn.cursor()
    
    # Удаляем старую таблицу если есть неправильная схема
    cursor.execute('DROP TABLE IF EXISTS proxmox_backups')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proxmox_backups (
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
    
    # Создаем индексы для производительности
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_proxmox_backups_host_date 
        ON proxmox_backups(host_name, received_at)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_proxmox_backups_status 
        ON proxmox_backups(backup_status, received_at)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных Proxmox бэкапов инициализирована")
    
    # База ZFS статусов
    conn = sqlite3.connect('/opt/monitoring/data/zfs_status.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zfs_pools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_name TEXT NOT NULL,
            status TEXT NOT NULL,
            health TEXT,
            size TEXT,
            used TEXT,
            available TEXT,
            scrub_date TEXT,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных ZFS статусов инициализирована")
    
    # База остатков товаров
    conn = sqlite3.connect('/opt/monitoring/data/inventory.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER,
            warehouse TEXT,
            report_date TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инвентаря инициализирована")
    
    print("🎯 Все базы данных готовы к работе")

def create_directories():
    """Создает необходимые директории"""
    directories = [
        '/opt/monitoring/data/email_attachments',
        '/opt/monitoring/data/inventory_files',
        '/opt/monitoring/logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Создана директория: {directory}")

if __name__ == "__main__":
    create_directories()
    init_databases()
    print("🎯 Система обработки писем готова к работе!")
    