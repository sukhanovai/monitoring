#!/usr/bin/env python3
"""
Тестирование новой логики отображения статусов
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from extensions.backup_monitor.bot_handler import BackupMonitorBot
from datetime import datetime, timedelta

def test_new_status_logic():
    bot = BackupMonitorBot()
    
    print("🔍 Тестирование новой логики статусов:\n")
    
    test_hosts = ['pve2-rubicon', 'pve-rubicon', 'sr-pve1']
    
    for host in test_hosts:
        print(f"\n🎯 Хост: {host}")
        
        # Старая логика (только последний бэкап)
        details = bot.get_host_status(host)
        if details:
            last_status = details[0][0]
            print(f"📋 Старая логика: {last_status}")
        
        # Новая логика (с учетом периода)
        status = bot.get_host_display_status(host)
        print(f"🆕 Новая логика: {status}")
        
        # Показываем бэкапы за 48 часов
        recent = bot.get_host_recent_status(host, 48)
        print(f"📊 Бэкапы за 48ч: {len(recent)}")
        
        for i, (status, time) in enumerate(recent[:3]):
            icon = "✅" if status == 'success' else "❌"
            print(f"  {i+1}. {icon} {time}: {status}")

if __name__ == "__main__":
    test_new_status_logic()
    