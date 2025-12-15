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
project_root = '/opt/monitoring'
sys.path.insert(0, project_root)

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
        import traceback
        traceback.print_exc()
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
            print(f"✅ DEBUG_MODE мигрирован: {debug_config['debug_mode']}")
        
        if 'log_level' in debug_config:
            config_manager.set_setting('LOG_LEVEL', debug_config['log_level'], 'debug', 'Уровень логирования', 'string')
            print(f"✅ LOG_LEVEL мигрирован: {debug_config['log_level']}")
        
        if 'enable_ssh_debug' in debug_config:
            config_manager.set_setting('SSH_DEBUG', debug_config['enable_ssh_debug'], 'debug', 'Отладка SSH', 'bool')
        
        if 'enable_resource_debug' in debug_config:
            config_manager.set_setting('RESOURCE_DEBUG', debug_config['enable_resource_debug'], 'debug', 'Отладка ресурсов', 'bool')
        
        if 'enable_backup_debug' in debug_config:
            config_manager.set_setting('BACKUP_DEBUG', debug_config['enable_backup_debug'], 'debug', 'Отладка бэкапов', 'bool')
        
        print(f"✅ Конфигурация отладки мигрирована")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции конфигурации отладки: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_extensions_config():
    """Миграция конфигурации расширений"""
    old_config_path = '/opt/monitoring/data/extensions_config.json'
    if not os.path.exists(old_config_path):
        print(f"⚠️ Файл конфигурации расширений не найден: {old_config_path}")
        return False
    
    try:
        with open(old_config_path, 'r') as f:
            extensions_config = json.load(f)
        
        from core.config_manager import config_manager
        
        # Мигрируем конфигурацию расширений
        config_manager.set_setting('EXTENSIONS_CONFIG', extensions_config, 'extensions', 'Конфигурация расширений', 'dict')
        print(f"✅ Конфигурация расширений мигрирована: {len(extensions_config)} записей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции конфигурации расширений: {e}")
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
    
    # 3. Мигрируем конфигурацию расширений
    print("3. Миграция конфигурации расширений...")
    if migrate_extensions_config():
        print("✅ Успешно\n")
    else:
        print("⚠️ Пропущено\n")
    
    print("="*50)
    print("=== МИГРАЦИЯ ЗАВЕРШЕНА ===")
    print("="*50)
    print("\nСледующие шаги:")
    print("1. Запустите тестирование новой структуры:")
    print("   python3 test_new_structure.py")
    print("\n2. Постепенно обновляйте imports в существующих модулях:")
    print("   - from app.utils.common import debug_log → from lib.logging import debug_log")
    print("   - from app.config.settings import * → from config.db_settings import *")
    print("   - Функции отправки сообщений → from lib.alerts import send_alert")
    print("\n3. Начните перенос основного функционала (вторая очередь рефакторинга)")

if __name__ == "__main__":
    main()