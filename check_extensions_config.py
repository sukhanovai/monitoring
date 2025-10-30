#!/usr/bin/env python3
"""
Проверка конфигурационного файла расширений
"""

import json
import os

def check_extensions_config():
    """Проверяет конфигурационный файл расширений"""
    
    config_file = '/opt/monitoring/data/extensions_config.json'
    
    print(f"🔍 Проверяем конфигурационный файл: {config_file}")
    
    if not os.path.exists(config_file):
        print("❌ Конфигурационный файл не существует")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("📊 Содержимое конфигурационного файла:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
        # Проверяем backup_monitor
        if 'backup_monitor' in config:
            backup_config = config['backup_monitor']
            print(f"\n🔍 Конфигурация backup_monitor:")
            print(f"   enabled: {backup_config.get('enabled', 'NOT_SET')}")
            print(f"   last_modified: {backup_config.get('last_modified', 'NOT_SET')}")
        else:
            print("❌ backup_monitor не найден в конфигурации")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка чтения конфигурации: {e}")
        return False

if __name__ == "__main__":
    check_extensions_config()
    