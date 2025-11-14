#!/usr/bin/env python3
"""
Скрипт для дополнения БД недостающими настройками
"""

import sys
import os
import json

sys.path.insert(0, '/opt/monitoring')

def complete_migration():
    print("🔄 Дополняем БД недостающими настройками...")
    
    # Импортируем оригинальный config для получения недостающих данных
    try:
        from config_original import (
            RESOURCE_ALERT_THRESHOLDS, BACKUP_PATTERNS
        )
        print("✅ Оригинальный config загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки оригинального config: {e}")
        return False
    
    from settings_manager import settings_manager
    
    try:
        # Добавляем RESOURCE_ALERT_THRESHOLDS если его нет
        current_alert_thresholds = settings_manager.get_setting('RESOURCE_ALERT_THRESHOLDS', {})
        if not current_alert_thresholds:
            settings_manager.set_setting('RESOURCE_ALERT_THRESHOLDS', 
                                       json.dumps(RESOURCE_ALERT_THRESHOLDS),
                                       'resources', 
                                       'Пороги для алертов ресурсов', 
                                       'dict')
            print("✅ RESOURCE_ALERT_THRESHOLDS добавлен в БД")
        
        # Дополняем паттерны бэкапов
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        
        # Проверим какие паттерны уже есть
        cursor.execute("SELECT pattern FROM backup_patterns")
        existing_patterns = [row[0] for row in cursor.fetchall()]
        
        added_patterns = 0
        
        # Добавляем недостающие паттерны из database раздела
        if 'database' in BACKUP_PATTERNS:
            for db_type, patterns in BACKUP_PATTERNS['database'].items():
                for pattern in patterns:
                    if pattern not in existing_patterns:
                        cursor.execute(
                            "INSERT INTO backup_patterns (pattern_type, pattern, category) VALUES (?, ?, ?)",
                            (f"database_{db_type}", pattern, 'database')
                        )
                        added_patterns += 1
                        existing_patterns.append(pattern)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Добавлено {added_patterns} недостающих паттернов бэкапов")
        
        # Добавим настройки для интервалов бэкапов если их нет
        backup_settings = [
            ('BACKUP_ALERT_HOURS', '24', 'backup', 'Часы для алертов о бэкапах', 'int'),
            ('BACKUP_STALE_HOURS', '36', 'backup', 'Часы для устаревших бэкапов', 'int'),
        ]
        
        for key, default_value, category, description, data_type in backup_settings:
            current_value = settings_manager.get_setting(key, None)
            if current_value is None:
                settings_manager.set_setting(key, default_value, category, description, data_type)
                print(f"✅ {key} добавлен в БД")
        
        print("🎯 Миграция завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if complete_migration():
        print("\n✅ Все недостающие настройки добавлены в БД!")
    else:
        print("\n❌ Миграция не удалась!")
        