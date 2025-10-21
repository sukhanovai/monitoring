# /opt/monitoring/test_email_processing.py

#!/usr/bin/env python3
"""
Инструмент тестирования обработки писем с бэкапами
"""

import sys
import os
import sqlite3
from datetime import datetime

# Добавляем путь для импорта
sys.path.insert(0, '/opt/monitoring')

def test_backup_database():
    """Проверяет базу данных бэкапов"""
    print("🔍 Проверка базы данных бэкапов...")
    
    db_path = '/opt/monitoring/data/backups.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем таблицу
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proxmox_backups'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Таблица proxmox_backups не найдена!")
            return False
        
        # Проверяем данные
        cursor.execute("SELECT COUNT(*) FROM proxmox_backups")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT DISTINCT host_name FROM proxmox_backups LIMIT 5")
        hosts = cursor.fetchall()
        
        print(f"✅ База данных работает")
        print(f"📊 Записей в базе: {count}")
        print(f"🏠 Хосты в базе: {[h[0] for h in hosts]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def test_sample_email_processing():
    """Тестирует обработку примерного письма"""
    print("\n🔍 Тестирование обработки письма...")
    
    try:
        from extensions.email_processor.core import EmailProcessorCore
        
        # Пример письма от Proxmox
        sample_email = """Subject: vzdump backup status (pve13): backup successful
From: root@pve13.localdomain
Date: Tue, 21 Oct 2024 03:00:01 +0300

Backup completed successfully
Duration: 02:15:30
Total size: 145.8GB
VMs: 12 successful, 0 failed
"""
        
        processor = EmailProcessorCore()
        result = processor.process_email(sample_email)
        
        print(f"✅ Обработка письма: {'УСПЕХ' if result else 'НЕУДАЧА'}")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка обработки письма: {e}")
        return False

def test_bot_commands():
    """Тестирует команды бота"""
    print("\n🔍 Тестирование команд бота...")
    
    try:
        from extensions.backup_monitor.bot_handler import BackupMonitorBot
        
        bot = BackupMonitorBot()
        
        # Тестируем основные методы
        today = bot.get_today_status()
        hosts = bot.get_all_hosts()
        recent = bot.get_recent_backups(24)
        
        print(f"✅ Команды бота работают")
        print(f"📊 Данные за сегодня: {len(today)} записей")
        print(f"🏠 Всего хостов: {len(hosts)}")
        print(f"📅 Последние бэкапы: {len(recent)} записей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка команд бота: {e}")
        return False

def add_sample_data():
    """Добавляет тестовые данные в базу"""
    print("\n📝 Добавление тестовых данных...")
    
    try:
        conn = sqlite3.connect('/opt/monitoring/data/backups.db')
        cursor = conn.cursor()
        
        # Добавляем тестовые записи
        test_data = [
            ('pve13', 'success', '02:15:30', '145.8GB', None, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('pve12', 'failed', '01:45:12', '89.2GB', 'Storage full', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('bup3', 'success', '03:22:45', '234.1GB', None, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ]
        
        for host, status, duration, size, error, received_at in test_data:
            cursor.execute('''
                INSERT OR REPLACE INTO proxmox_backups 
                (host_name, backup_status, duration, total_size, error_message, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (host, status, duration, size, error, received_at))
        
        conn.commit()
        conn.close()
        
        print("✅ Тестовые данные добавлены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка добавления данных: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование системы мониторинга бэкапов\n")
    
    # Запускаем тесты
    db_ok = test_backup_database()
    
    if not db_ok:
        print("\n🔄 Инициализация базы данных...")
        from init_email_system import init_databases
        init_databases()
        db_ok = test_backup_database()
    
    # Добавляем тестовые данные если база пустая
    if db_ok:
        add_sample_data()
    
    # Тестируем обработку писем
    email_ok = test_sample_email_processing()
    
    # Тестируем команды бота
    bot_ok = test_bot_commands()
    
    print(f"\n📊 ИТОГ ТЕСТИРОВАНИЯ:")
    print(f"✅ База данных: {'РАБОТАЕТ' if db_ok else 'НЕ РАБОТАЕТ'}")
    print(f"✅ Обработка писем: {'РАБОТАЕТ' if email_ok else 'НЕ РАБОТАЕТ'}")
    print(f"✅ Команды бота: {'РАБОТАЕТ' if bot_ok else 'НЕ РАБОТАЕТ'}")
    
    if db_ok and bot_ok:
        print(f"\n🎉 Система готова к работе! Используйте /backup в боте")
    else:
        print(f"\n❌ Требуется дополнительная настройка")
        