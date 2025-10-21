#!/usr/bin/env python3
"""
Утилита для проверки обработки писем с бэкапами
"""

import sqlite3
import os
import sys
from datetime import datetime

def check_email_processing():
    """Проверяет обработку писем и показывает статистику"""
    
    db_path = '/opt/monitoring/data/backups.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute('SELECT COUNT(*) FROM proxmox_backups')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM proxmox_backups WHERE date(received_at) = date("now")')
    today_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM proxmox_backups WHERE backup_status = "failed"')
    failed_count = cursor.fetchone()[0]
    
    # Последние записи
    cursor.execute('''
        SELECT host_name, backup_status, received_at, email_subject 
        FROM proxmox_backups 
        ORDER BY received_at DESC 
        LIMIT 5
    ''')
    recent_entries = cursor.fetchall()
    
    print("📧 Статус обработки писем с бэкапами")
    print("=" * 50)
    print(f"📊 Всего обработано писем: {total_count}")
    print(f"📅 За сегодня: {today_count}")
    print(f"❌ Неудачных бэкапов: {failed_count}")
    print()
    print("⏰ Последние 5 записей:")
    print("-" * 50)
    
    for host, status, received, subject in recent_entries:
        time_str = datetime.strptime(received, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')
        icon = "✅" if status == 'success' else "❌"
        print(f"{icon} {time_str} - {host}: {status}")
        print(f"   Тема: {subject[:60]}{'...' if len(subject) > 60 else ''}")
        print()
    
    conn.close()

def check_raw_email_logs():
    """Проверяет логи обработки писем"""
    log_path = '/opt/monitoring/logs/email_processor.log'
    
    if not os.path.exists(log_path):
        print(f"❌ Файл логов не найден: {log_path}")
        return
    
    print("\n📋 Последние записи из логов:")
    print("=" * 50)
    
    # Показываем последние 10 строк логов
    os.system(f'tail -10 {log_path}')

if __name__ == "__main__":
    check_email_processing()
    check_raw_email_logs()
    