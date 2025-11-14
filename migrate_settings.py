#!/usr/bin/env python3
"""
Финальная миграция настроек в БД
"""

import sys
import os
import sqlite3
import json
import shutil

sys.path.insert(0, '/opt/monitoring')

def migrate_final():
    print("🔄 Запуск финальной миграции...")
    
    # Проверяем существование config.py
    if not os.path.exists('/opt/monitoring/config.py'):
        print("❌ config.py не найден!")
        return False
    
    try:
        # Создаем резервную копию
        backup_file = '/opt/monitoring/config_backup_final.py'
        shutil.copy2('/opt/monitoring/config.py', backup_file)
        print(f"✅ Резервная копия создана: {backup_file}")
        
        # Импортируем текущий config
        from config import (
            TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL, MAX_FAIL_TIME,
            SILENT_START, SILENT_END, DATA_COLLECTION_TIME,
            RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_INTERVAL,
            RESOURCE_THRESHOLDS, SSH_USERNAME, SSH_KEY_PATH,
            WINDOWS_CREDENTIALS, WINDOWS_SERVER_CONFIGS,
            SERVER_CONFIG, SERVER_TIMEOUTS, PROXMOX_HOSTS,
            BACKUP_PATTERNS, DATABASE_CONFIG, BACKUP_STATUS_MAP,
            DUPLICATE_IP_HOSTS, HOSTNAME_ALIASES, WEB_PORT, WEB_HOST
        )
        
        print("✅ Текущий config.py загружен")
        
        # Инициализируем менеджер настроек
        from settings_manager import SettingsManager
        settings_manager = SettingsManager()
        
        # Мигрируем основные настройки
        print("📝 Мигрируем основные настройки...")
        
        settings_manager.set_setting('TELEGRAM_TOKEN', TELEGRAM_TOKEN, 'telegram', 'Токен Telegram бота', 'string')
        settings_manager.set_setting('CHAT_IDS', json.dumps(CHAT_IDS), 'telegram', 'ID чатов для уведомлений', 'list')
        settings_manager.set_setting('CHECK_INTERVAL', CHECK_INTERVAL, 'monitoring', 'Интервал проверки серверов (секунды)', 'int')
        settings_manager.set_setting('MAX_FAIL_TIME', MAX_FAIL_TIME, 'monitoring', 'Максимальное время простоя до алерта (секунды)', 'int')
        settings_manager.set_setting('SILENT_START', SILENT_START, 'time', 'Начало тихого режима (час)', 'int')
        settings_manager.set_setting('SILENT_END', SILENT_END, 'time', 'Конец тихого режима (час)', 'int')
        settings_manager.set_setting('DATA_COLLECTION_TIME', DATA_COLLECTION_TIME.strftime('%H:%M'), 'time', 'Время сбора данных для отчета', 'time')
        settings_manager.set_setting('RESOURCE_CHECK_INTERVAL', RESOURCE_CHECK_INTERVAL, 'resources', 'Интервал проверки ресурсов (секунды)', 'int')
        settings_manager.set_setting('RESOURCE_ALERT_INTERVAL', RESOURCE_ALERT_INTERVAL, 'resources', 'Интервал повторных алертов ресурсов (секунды)', 'int')
        settings_manager.set_setting('CPU_WARNING', RESOURCE_THRESHOLDS.get('cpu_warning', 80), 'resources', 'Порог предупреждения CPU (%)', 'int')
        settings_manager.set_setting('CPU_CRITICAL', RESOURCE_THRESHOLDS.get('cpu_critical', 90), 'resources', 'Порог критического CPU (%)', 'int')
        settings_manager.set_setting('RAM_WARNING', RESOURCE_THRESHOLDS.get('ram_warning', 85), 'resources', 'Порог предупреждения RAM (%)', 'int')
        settings_manager.set_setting('RAM_CRITICAL', RESOURCE_THRESHOLDS.get('ram_critical', 95), 'resources', 'Порог критического RAM (%)', 'int')
        settings_manager.set_setting('DISK_WARNING', RESOURCE_THRESHOLDS.get('disk_warning', 80), 'resources', 'Порог предупреждения Disk (%)', 'int')
        settings_manager.set_setting('DISK_CRITICAL', RESOURCE_THRESHOLDS.get('disk_critical', 90), 'resources', 'Порог критического Disk (%)', 'int')
        settings_manager.set_setting('SSH_USERNAME', SSH_USERNAME, 'auth', 'Имя пользователя SSH', 'string')
        settings_manager.set_setting('SSH_KEY_PATH', SSH_KEY_PATH, 'auth', 'Путь к SSH ключу', 'string')
        settings_manager.set_setting('WEB_PORT', WEB_PORT, 'web', 'Порт веб-интерфейса', 'int')
        settings_manager.set_setting('WEB_HOST', WEB_HOST, 'web', 'Хост веб-интерфейса', 'string')
        
        # Мигрируем Windows учетные данные
        print("🖥️ Мигрируем учетные данные Windows...")
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM windows_credentials')
        
        priority = 0
        for cred in WINDOWS_CREDENTIALS:
            cursor.execute('INSERT INTO windows_credentials (username, password, server_type, priority) VALUES (?, ?, ?, ?)',
                         (cred['username'], cred['password'], 'default', priority))
            priority += 1
        
        for server_type, config in WINDOWS_SERVER_CONFIGS.items():
            for cred in config.get('credentials', []):
                cursor.execute('INSERT INTO windows_credentials (username, password, server_type, priority) VALUES (?, ?, ?, ?)',
                             (cred['username'], cred['password'], server_type, 0))
        
        conn.commit()
        conn.close()
        
        # Мигрируем серверы
        print("🔌 Мигрируем серверы...")
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servers')
        
        server_count = 0
        for ip, name in SERVER_CONFIG.get('windows_servers', {}).items():
            server_type = 'standard_windows'
            for win_type, config in WINDOWS_SERVER_CONFIGS.items():
                if ip in config.get('servers', []):
                    server_type = win_type
                    break
            cursor.execute('INSERT INTO servers (ip, name, type, timeout) VALUES (?, ?, ?, ?)', 
                         (ip, name, 'rdp', 30))
            server_count += 1
        
        for ip, name in SERVER_CONFIG.get('linux_servers', {}).items():
            cursor.execute('INSERT INTO servers (ip, name, type, timeout) VALUES (?, ?, ?, ?)', 
                         (ip, name, 'ssh', 15))
            server_count += 1
        
        for ip, name in SERVER_CONFIG.get('ping_servers', {}).items():
            cursor.execute('INSERT INTO servers (ip, name, type, timeout) VALUES (?, ?, ?, ?)', 
                         (ip, name, 'ping', 10))
            server_count += 1
        
        conn.commit()
        conn.close()
        
        # Мигрируем остальные настройки
        print("💾 Мигрируем настройки бэкапов...")
        settings_manager.set_setting('SERVER_TIMEOUTS', json.dumps(SERVER_TIMEOUTS), 'monitoring', 'Таймауты серверов', 'dict')
        settings_manager.set_setting('PROXMOX_HOSTS', json.dumps(PROXMOX_HOSTS), 'backup', 'Хосты Proxmox', 'dict')
        settings_manager.set_setting('DATABASE_CONFIG', json.dumps(DATABASE_CONFIG), 'backup', 'Конфигурация БД', 'dict')
        settings_manager.set_setting('BACKUP_STATUS_MAP', json.dumps(BACKUP_STATUS_MAP), 'backup', 'Статусы бэкапов', 'dict')
        settings_manager.set_setting('DUPLICATE_IP_HOSTS', json.dumps(DUPLICATE_IP_HOSTS), 'backup', 'Хосты с одинаковыми IP', 'dict')
        settings_manager.set_setting('HOSTNAME_ALIASES', json.dumps(HOSTNAME_ALIASES), 'backup', 'Алиасы хостов', 'dict')
        
        # Мигрируем паттерны бэкапов
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM backup_patterns')
        
        pattern_count = 0
        for pattern_type, patterns in BACKUP_PATTERNS.items():
            if isinstance(patterns, list):
                for pattern in patterns:
                    cursor.execute('INSERT INTO backup_patterns (pattern_type, pattern, category) VALUES (?, ?, ?)',
                                 (pattern_type, pattern, 'proxmox'))
                    pattern_count += 1
            elif isinstance(patterns, dict):
                for sub_type, sub_patterns in patterns.items():
                    if isinstance(sub_patterns, list):
                        for pattern in sub_patterns:
                            cursor.execute('INSERT INTO backup_patterns (pattern_type, pattern, category) VALUES (?, ?, ?)',
                                         (f"{pattern_type}_{sub_type}", pattern, 'database'))
                            pattern_count += 1
        
        conn.commit()
        conn.close()
        
        print("✅ Миграция завершена успешно!")
        print(f"📊 Статистика:")
        print(f"   - Настроек: {len(settings_manager.get_all_settings())}")
        print(f"   - Серверов: {server_count}")
        print(f"   - Учетных записей: {len(WINDOWS_CREDENTIALS)}")
        print(f"   - Паттернов: {pattern_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if migrate_final():
        print("\n🎉 Финальная миграция завершена!")
        print("📝 Теперь можно заменить config.py на версию с БД")
    else:
        print("\n❌ Миграция не удалась!")
        