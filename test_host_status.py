#!/usr/bin/env python3
"""
Тестирование отображения статуса хостов
"""

import sys
import os

# Добавляем путь для импорта модулей из поддиректорий
sys.path.append('/opt/monitoring/extensions/backup_monitor')

from bot_handler import BackupMonitorBot

def test_host_statuses():
    backup_bot = BackupMonitorBot()
    
    print("🔍 Тестирование статусов хостов:\n")
    
    # Получаем все хосты
    all_hosts = backup_bot.get_all_hosts()
    print(f"Всего хостов в базе: {len(all_hosts)}")
    
    for host_name in all_hosts:
        print(f"\nХост: {host_name}")
        
        # Получаем последний статус
        host_details = backup_bot.get_host_status(host_name)
        if host_details:
            last_status = host_details[0][0]  # статус первого (последнего) бэкапа
            last_time = host_details[0][4]    # время последнего бэкапа
            print(f"Последний статус: {last_status}")
            print(f"Время последнего бэкапа: {last_time}")
            
            # Показываем последние 3 бэкапа
            print(f"Последние бэкапы:")
            for i, (status, duration, size, error, received_at) in enumerate(host_details[:3]):
                status_icon = "✅" if status == 'success' else "❌"
                print(f"  {i+1}. {status_icon} {received_at}: {status}")
                if duration:
                    print(f"     Время: {duration}")
                if size:
                    print(f"     Размер: {size}")
                if error and status == 'failed':
                    print(f"     Ошибка: {error[:100]}...")
        else:
            print("❌ Нет данных о бэкапах")
        print("-" * 50)

if __name__ == "__main__":
    test_host_statuses()