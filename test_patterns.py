#!/usr/bin/env python3
"""
Тест паттернов для бэкапов баз данных
"""

import re
from config import DATABASE_BACKUP_PATTERNS

def test_patterns():
    """Тестирует паттерны на примерах"""
    
    test_subjects = [
        "sr-bup unf dump complete",
        "cobian BRN backup 1c_smb, errors:0", 
        "kc-1c zup dump complete",
        "yandex RUBIKON backup Рез.копия создана Backup",
        "vzdump backup status (sr-pve4): backup successful"  # Proxmox для сравнения
    ]
    
    print("🧪 Тестируем паттерны бэкапов БД:")
    print("=" * 60)
    
    for subject in test_subjects:
        print(f"\n📨 Тема: {subject}")
        found = False
        
        for category, patterns in DATABASE_BACKUP_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    print(f"   ✅ Распознан как: {category}")
                    print(f"   📍 Паттерн: {pattern}")
                    print(f"   🔍 Совпадение: {match.groups()}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            print("   ❌ Не распознан как бэкап БД")

if __name__ == "__main__":
    test_patterns()