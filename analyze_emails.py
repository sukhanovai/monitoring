#!/usr/bin/env python3
"""
Анализ почтовых писем на наличие бэкапов баз данных
"""

import os
import re
from email import message_from_bytes
import email.policy

def analyze_email_files():
    """Анализирует письма в директориях"""
    
    maildir_cur = '/root/Maildir/cur'
    
    if not os.path.exists(maildir_cur):
        print("❌ Директория cur не найдена")
        return
    
    emails = os.listdir(maildir_cur)
    print(f"📧 Найдено писем в cur: {len(emails)}")
    
    # Паттерны для бэкапов баз данных
    db_patterns = {
        'company': r'(\w+)_dump complete',
        'barnaul': r'cobian BRN backup (\w+), errors:(\d+)',
        'clients': r'kc-1c (\w+) dump complete', 
        'yandex': r'yandex (\w+) backup'
    }
    
    db_emails_found = 0
    
    for email_file in emails[:20]:  # Проверим первые 20 писем
        file_path = os.path.join(maildir_cur, email_file)
        
        try:
            with open(file_path, 'rb') as f:
                msg = message_from_bytes(f.read(), policy=email.policy.default)
            
            subject = msg.get('subject', '')
            
            # Проверяем паттерны баз данных
            for db_type, pattern in db_patterns.items():
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    db_emails_found += 1
                    print(f"✅ Найден бэкап БД ({db_type}): {subject}")
                    break
            
        except Exception as e:
            print(f"⚠️ Ошибка чтения {email_file}: {e}")
    
    print(f"\n📊 Итог: найдено писем с бэкапами БД: {db_emails_found}")

if __name__ == "__main__":
    analyze_email_files()
    