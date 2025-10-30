#!/usr/bin/env python3
"""
Обработка всех писем из директории cur
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from improved_mail_monitor import BackupProcessor
import os
import shutil

def process_existing_emails():
    """Обрабатывает все письма из директории cur"""
    
    maildir_cur = '/root/Maildir/cur'
    maildir_tmp = '/root/Maildir/tmp_processing'
    
    print("🔄 Обрабатываем существующие письма из cur...")
    
    if not os.path.exists(maildir_cur):
        print("❌ Директория cur не найдена")
        return
    
    # Создаем временную директорию для обработки
    if not os.path.exists(maildir_tmp):
        os.makedirs(maildir_tmp)
    
    emails = os.listdir(maildir_cur)
    print(f"📧 Найдено писем для обработки: {len(emails)}")
    
    # Перемещаем письма во временную директорию для обработки
    for email_file in emails:
        src_path = os.path.join(maildir_cur, email_file)
        dst_path = os.path.join(maildir_tmp, email_file)
        shutil.move(src_path, dst_path)
    
    print(f"✅ Письма перемещены во временную директорию")
    
    # Создаем обработчик
    processor = BackupProcessor()
    
    # Обрабатываем письма из временной директории
    processed_count = 0
    for email_file in os.listdir(maildir_tmp):
        file_path = os.path.join(maildir_tmp, email_file)
        
        if os.path.isfile(file_path):
            print(f"🔍 Обрабатываем: {email_file}")
            
            # Обрабатываем письмо
            result = processor.parse_email_file(file_path)
            
            if result:
                print(f"✅ Обработано: {email_file}")
                processed_count += 1
            else:
                print(f"⚠️ Не удалось обработать: {email_file}")
            
            # Перемещаем обратно в cur
            final_path = os.path.join(maildir_cur, email_file)
            shutil.move(file_path, final_path)
    
    # Удаляем временную директорию
    if os.path.exists(maildir_tmp):
        os.rmdir(maildir_tmp)
    
    print(f"📊 Итог: обработано {processed_count} писем")
    
    # Проверяем базу данных после обработки
    check_database_after_processing()

def check_database_after_processing():
    """Проверяет базу данных после обработки"""
    import sqlite3
    
    db_path = '/opt/monitoring/data/backups.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 Проверяем базу данных после обработки:")
    
    # Proxmox бэкапы
    cursor.execute('SELECT COUNT(*) FROM proxmox_backups')
    proxmox_count = cursor.fetchone()[0]
    print(f"   Proxmox бэкапов: {proxmox_count}")
    
    # Бэкапы баз данных
    cursor.execute('SELECT COUNT(*) FROM database_backups')
    db_count = cursor.fetchone()[0]
    print(f"   Бэкапов БД: {db_count}")
    
    # Последние 5 бэкапов БД
    cursor.execute('''
        SELECT database_display_name, backup_status, backup_type, received_at 
        FROM database_backups 
        ORDER BY received_at DESC 
        LIMIT 5
    ''')
    recent_db = cursor.fetchall()
    
    print("   Последние бэкапы БД:")
    for db in recent_db:
        name, status, btype, received = db
        print(f"     - {name}: {status} ({btype}) - {received}")
    
    conn.close()

if __name__ == "__main__":
    process_existing_emails()
    