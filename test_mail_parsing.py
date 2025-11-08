#!/usr/bin/env python3
"""
Тестовый скрипт для проверки идентификации писем от серверов с одинаковым IP
"""

import re
from improved_mail_monitor import BackupProcessor

def test_subject_parsing():
    """Тестирует парсинг различных тем писем"""
    test_cases = [
        "vzdump backup status (pve2-rubicon): backup successful",
        "vzdump backup status (pve-rubicon): backup successful", 
        "vzdump backup status (pve2-rubicon.example.com): backup failed",
        "vzdump backup status (sr-pve1.geltd.local): backup successful",
        "proxmox backup (pve2-rubicon) completed",
        "backup status for pve2-rubicon: successful"
    ]
    
    processor = BackupProcessor()
    
    print("🔍 Тестирование парсинга тем писем:\n")
    
    for subject in test_cases:
        print(f"Тема: {subject}")
        result = processor.parse_subject(subject)
        if result:
            print(f"✅ Результат: {result['host_name']} - {result['backup_status']}")
        else:
            print("❌ Не распознано")
        print("-" * 50)

if __name__ == "__main__":
    test_subject_parsing()
    