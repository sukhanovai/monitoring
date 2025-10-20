#!/usr/bin/env python3
"""
Инициализация системы обработки писем
"""

import sqlite3
import os

def init_databases():
    """Инициализирует все базы данных"""
    
    # База бэкапов
    conn = sqlite3.connect('/opt/monitoring/data/backups.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proxmox_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_name TEXT NOT NULL,
            vm_id TEXT,
            vm_name TEXT,
            status TEXT NOT NULL,
            size TEXT,
            duration TEXT,
            backup_date TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exiland_backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            status TEXT NOT NULL,
            files_count INTEGER,
            total_size TEXT,
            backup_date TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
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
    
    print("✅ Все базы данных инициализированы")

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
    