# /opt/monitoring/check_email_status.py

#!/usr/bin/env python3
"""
Скрипт для проверки статуса обработки писем
"""

import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, '/opt/monitoring')

def check_all_status():
    """Проверяет все аспекты системы обработки писем"""
    
    print("🔍 Проверка системы обработки писем\n")
    
    # 1. Проверяем логи обработчика
    print("1. 📧 Логи обработчика писем:")
    email_log = '/opt/monitoring/logs/email_processor.log'
    if os.path.exists(email_log):
        with open(email_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-10:]  # Последние 10 строк
            if lines:
                for line in lines:
                    print(f"   {line.strip()}")
            else:
                print("   Лог пуст")
    else:
        print("   Файл лога не найден")
    
    # 2. Проверяем логи обработанных писем
    print("\n2. 📝 Обработанные письма:")
    processed_log = '/opt/monitoring/logs/processed_emails.log'
    if os.path.exists(processed_log):
        with open(processed_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-5:]  # Последние 5 писем
            if lines:
                for line in lines:
                    print(f"   {line.strip()}")
            else:
                print("   Нет обработанных писем")
    else:
        print("   Файл лога не найден")
    
    # 3. Проверяем базу данных
    print("\n3. 🗄️ База данных бэкапов:")
    db_path = '/opt/monitoring/data/backups.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Общее количество записей
            cursor.execute("SELECT COUNT(*) FROM proxmox_backups")
            total = cursor.fetchone()[0]
            print(f"   Всего записей: {total}")
            
            # Последние записи
            cursor.execute('''
                SELECT host_name, backup_status, datetime(received_at) 
                FROM proxmox_backups 
                ORDER BY received_at DESC 
                LIMIT 5
            ''')
            recent = cursor.fetchall()
            
            if recent:
                print("   Последние записи:")
                for host, status, time in recent:
                    print(f"     • {host}: {status} ({time})")
            else:
                print("   Нет записей в базе")
                
            conn.close()
        except Exception as e:
            print(f"   Ошибка базы данных: {e}")
    else:
        print("   База данных не найдена")
    
    # 4. Проверяем команду бота
    print("\n4. 🤖 Статус команды /backup:")
    try:
        from extensions.backup_monitor.bot_handler import format_backup_summary, BackupMonitorBot
        bot = BackupMonitorBot()
        message = format_backup_summary(bot)
        
        # Выводим только первые несколько строк для краткости
        lines = message.split('\n')[:15]
        for line in lines:
            print(f"   {line}")
            
        if len(message.split('\n')) > 15:
            print("   ... (полный вывод в боте)")
            
    except Exception as e:
        print(f"   Ошибка: {e}")

def check_specific_host(hostname):
    """Проверяет статус конкретного хоста"""
    print(f"\n🔍 Поиск хоста: {hostname}")
    
    db_path = '/opt/monitoring/data/backups.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT host_name, backup_status, duration, total_size, datetime(received_at)
                FROM proxmox_backups 
                WHERE host_name LIKE ? 
                ORDER BY received_at DESC 
                LIMIT 3
            ''', (f'%{hostname}%',))
            
            results = cursor.fetchall()
            
            if results:
                print(f"✅ Найдены записи для {hostname}:")
                for host, status, duration, size, time in results:
                    print(f"   • {time}: {status}")
                    if duration:
                        print(f"     Длительность: {duration}")
                    if size:
                        print(f"     Размер: {size}")
            else:
                print(f"❌ Записей для {hostname} не найдено")
                
            conn.close()
        except Exception as e:
            print(f"   Ошибка: {e}")

if __name__ == "__main__":
    check_all_status()
    
    # Проверяем конкретные хосты которые могли прийти
    check_specific_host('sr-pve4')
    check_specific_host('pve')
    check_specific_host('bup')
    
    print(f"\n⏰ Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    