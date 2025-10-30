#!/usr/bin/env python3
"""
Диагностика базы данных бэкапов
"""

import sqlite3
import os
from datetime import datetime, timedelta

def check_database():
    """Проверяет содержимое базы данных бэкапов"""
    
    db_path = '/opt/monitoring/data/backups.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    print(f"🔍 Проверяем базу данных: {db_path}")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("📊 Таблицы в базе:")
    for table in tables:
        print(f"   - {table[0]}")
    
    print("\n" + "=" * 60)
    
    # Проверяем Proxmox бэкапы
    print("📋 Proxmox бэкапы (последние 10 записей):")
    cursor.execute('''
        SELECT host_name, backup_status, task_type, duration, received_at 
        FROM proxmox_backups 
        ORDER BY received_at DESC 
        LIMIT 10
    ''')
    proxmox_backups = cursor.fetchall()
    
    if not proxmox_backups:
        print("   ❌ Нет записей о Proxmox бэкапах")
    else:
        for backup in proxmox_backups:
            host, status, task_type, duration, received_at = backup
            print(f"   🖥️  {host}: {status} ({task_type}) - {received_at}")
    
    print("\n" + "=" * 60)
    
    # Проверяем бэкапы баз данных
    print("🗃️ Бэкапы баз данных (последние 10 записей):")
    cursor.execute('''
        SELECT host_name, database_name, database_display_name, backup_status, backup_type, received_at 
        FROM database_backups 
        ORDER BY received_at DESC 
        LIMIT 10
    ''')
    db_backups = cursor.fetchall()
    
    if not db_backups:
        print("   ❌ Нет записей о бэкапах баз данных")
    else:
        for backup in db_backups:
            host, db_name, display_name, status, backup_type, received_at = backup
            print(f"   💾 {host}: {display_name} ({db_name}) - {status} - {backup_type} - {received_at}")
    
    print("\n" + "=" * 60)
    
    # Статистика по типам бэкапов
    print("📈 Статистика по типам бэкапов:")
    
    # Proxmox
    cursor.execute('''
        SELECT backup_status, COUNT(*) 
        FROM proxmox_backups 
        WHERE received_at >= datetime('now', '-7 days')
        GROUP BY backup_status
    ''')
    proxmox_stats = cursor.fetchall()
    print("   Proxmox (за 7 дней):")
    for status, count in proxmox_stats:
        print(f"     {status}: {count}")
    
    # Базы данных
    cursor.execute('''
        SELECT backup_type, backup_status, COUNT(*) 
        FROM database_backups 
        WHERE received_at >= datetime('now', '-7 days')
        GROUP BY backup_type, backup_status
    ''')
    db_stats = cursor.fetchall()
    print("   Базы данных (за 7 дней):")
    for backup_type, status, count in db_stats:
        print(f"     {backup_type} - {status}: {count}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Диагностика завершена")

def check_recent_emails():
    """Проверяет наличие новых писем для обработки"""
    print("\n📧 Проверяем почтовые директории...")
    
    maildir_new = '/root/Maildir/new'
    maildir_cur = '/root/Maildir/cur'
    
    if os.path.exists(maildir_new):
        new_emails = os.listdir(maildir_new)
        print(f"   📨 Новые письма (new): {len(new_emails)}")
        for email in new_emails[:5]:  # Показываем первые 5
            print(f"     - {email}")
    else:
        print("   ❌ Директория new не найдена")
    
    if os.path.exists(maildir_cur):
        cur_emails = os.listdir(maildir_cur)
        print(f"   📁 Обработанные письма (cur): {len(cur_emails)}")
    else:
        print("   ❌ Директория cur не найдена")

if __name__ == "__main__":
    check_database()
    check_recent_emails()
    