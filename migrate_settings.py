#!/usr/bin/env python3
"""
Миграция настроек из старой структуры в новую
"""

import os
import sys
import json
import sqlite3
from pathlib import Path

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

def migrate_settings_db():
    """Миграция базы данных настроек"""
    old_db_path = '/opt/monitoring/data/settings.db'
    if not os.path.exists(old_db_path):
        print(f"❌ Старая база данных не найдена: {old_db_path}")
        return False
    
    # Подключаемся к новой базе (она создастся автоматически)
    from core.config_manager import config_manager
    print("✅ Новая база данных настроек инициализирована")
    
    # Подключаемся к старой базе
    old_conn = sqlite3.connect(old_db_path)
    old_cursor = old_conn.cursor()
    
    # Мигрируем настройки
    try:
        old_cursor.execute('SELECT key, value, category, description, data_type FROM settings')
        old_settings = old_cursor.fetchall()
        
        migrated = 0
        for key, value, category, description, data_type in old_settings:
            config_manager.set_setting(key, value, category, description, data_type)
            migrated += 1
        
        print(f"✅ Мигрировано {migrated} настроек")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции настроек: {e}")
        return False
    finally:
        old_conn.close()

def migrate_debug_config():
    """Миграция конфигурации отладки"""
    old_config_path = '/opt/monitoring/data/debug_config.json'
    if not os.path.exists(old_config_path):
        print(f"⚠️ Файл конфигурации отладки не найден: {old_config_path}")
        return False
    
    try:
        with open(old_config_path, 'r') as f:
            debug_config = json.load(f)
        
        from core.config_manager import config_manager
        
        # Мигрируем настройки отладки
        if 'debug_mode' in debug_config:
            config_manager.set_setting('DEBUG_MODE', debug_config['debug_mode'], 'debug', 'Режим отладки', 'bool')
        
        if 'log_level' in debug_config:
            config_manager.set_setting('LOG_LEVEL', debug_config['log_level'], 'debug', 'Уровень логирования', 'string')
        
        print(f"✅ Конфигурация отладки мигрирована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции конфигурации отладки: {e}")
        return False

def main():
    print("=== Миграция настроек в новую структуру ===\n")
    
    # 1. Мигрируем базу данных
    print("1. Миграция базы данных настроек...")
    if migrate_settings_db():
        print("✅ Успешно\n")
    else:
        print("⚠️ Пропущено\n")
    
    # 2. Мигрируем конфигурацию отладки
    print("2. Миграция конфигурации отладки...")
    if migrate_debug_config():
        print("✅ Успешно\n")
    else:
        print("⚠️ Пропущено\n")
    
    print("=== Миграция завершена ===")
    print("\nСледующие шаги:")
    print("1. Запустите test_new_structure.py для проверки")
    print("2. Обновите imports в основных модулях")
    print("3. Постепенно переносите остальной функционал")

if __name__ == "__main__":
    main()