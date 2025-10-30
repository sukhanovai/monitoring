#!/usr/bin/env python3
"""
Повторная обработка только писем с бэкапами баз данных
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from improved_mail_monitor import BackupProcessor
import os
import shutil
import re

def process_database_backups_only():
    """Обрабатывает только письма с бэкапами баз данных"""
    
    maildir_cur = '/root/Maildir/cur'
    
    print("🗃️ Обрабатываем только письма с бэкапами БД...")
    
    if not os.path.exists(maildir_cur):
        print("❌ Директория cur не найдена")
        return
    
    emails = os.listdir(maildir_cur)
    print(f"📧 Всего писем в cur: {len(emails)}")
    
    # Паттерны для бэкапов баз данных
    db_patterns = {
        'company': r'(\w+)_dump complete',
        'barnaul': r'cobian BRN backup (\w+), errors:(\d+)',
        'clients': r'kc-1c (\w+) dump complete', 
        'yandex': r'yandex (\w+) backup'
    }
    
    # Находим письма с бэкапами БД
    db_emails = []
    for email_file in emails:
        file_path = os.path.join(maildir_cur, email_file)
        
        try:
            with open(file_path, 'rb') as f:
                from email import message_from_bytes
                import email.policy
                msg = message_from_bytes(f.read(), policy=email.policy.default)
            
            subject = msg.get('subject', '')
            
            # Проверяем паттерны баз данных
            for db_type, pattern in db_patterns.items():
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    db_emails.append((email_file, subject, db_type))
                    break
            
        except Exception as e:
            print(f"⚠️ Ошибка чтения {email_file}: {e}")
    
    print(f"🔍 Найдено писем с бэкапами БД: {len(db_emails)}")
    
    if not db_emails:
        print("❌ Не найдено писем с бэкапами БД")
        return
    
    # Создаем обработчик
    processor = BackupProcessor()
    
    # Обрабатываем найденные письма
    processed_count = 0
    for email_file, subject, db_type in db_emails:
        file_path = os.path.join(maildir_cur, email_file)
        
        print(f"🔍 Обрабатываем: {email_file}")
        print(f"   Тема: {subject}")
        print(f"   Тип: {db_type}")
        
        # Обрабатываем письмо
        result = processor.parse_email_file(file_path)
        
        if result:
            print(f"✅ Успешно обработано")
            processed_count += 1
        else:
            print(f"❌ Ошибка обработки")
    
    print(f"📊 Итог: обработано {processed_count} писем с бэкапами БД")
    
    # Проверяем базу данных
    check_database_after_db_processing()

def check_database_after_db_processing():
    """Проверяет базу данных после обработки бэкапов БД"""
    import sqlite3
    
    db_path = '/opt/monitoring/data/backups.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 Проверяем базу данных после обработки бэкапов БД:")
    
    # Бэкапы баз данных
    cursor.execute('SELECT COUNT(*) FROM database_backups')
    db_count = cursor.fetchone()[0]
    print(f"   Бэкапов БД: {db_count}")
    
    # Последние 10 бэкапов БД
    cursor.execute('''
        SELECT database_display_name, backup_status, backup_type, received_at 
        FROM database_backups 
        ORDER BY received_at DESC 
        LIMIT 10
    ''')
    recent_db = cursor.fetchall()
    
    print("   Последние бэкапы БД:")
    for db in recent_db:
        name, status, btype, received = db
        print(f"     - {name}: {status} ({btype}) - {received}")
    
    # Статистика по типам
    cursor.execute('''
        SELECT backup_type, COUNT(*) 
        FROM database_backups 
        GROUP BY backup_type
    ''')
    type_stats = cursor.fetchall()
    
    print("   Статистика по типам:")
    for btype, count in type_stats:
        print(f"     - {btype}: {count}")
    
    conn.close()

if __name__ == "__main__":
    process_database_backups_only()
    