#!/usr/bin/env python3
"""
Тестирование отображения статуса хостов
"""

from bot_handler import BackupMonitorBot

def test_host_statuses():
    backup_bot = BackupMonitorBot()
    
    print("🔍 Тестирование статусов хостов:\n")
    
    # Получаем все хосты с их статусами
    hosts_with_status = backup_bot.get_all_hosts_with_status()
    
    for host_name, last_status in hosts_with_status:
        print(f"Хост: {host_name}")
        print(f"Последний статус: {last_status}")
        
        # Получаем детальную информацию
        host_details = backup_bot.get_host_status(host_name)
        if host_details:
            print(f"Последние бэкапы:")
            for i, (status, duration, size, error, received_at) in enumerate(host_details[:3]):
                print(f"  {i+1}. {received_at}: {status}")
        print("-" * 50)

if __name__ == "__main__":
    test_host_statuses()
    