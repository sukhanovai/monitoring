#!/usr/bin/env python3
"""
Скрипт миграции настроек из config.py в базу данных
"""

import sys
import os
import sqlite3
import json

# Добавляем путь для импортов
sys.path.insert(0, '/opt/monitoring')

def migrate_settings():
    """Перенос настроек из config.py в базу данных"""
    
    print("🔄 Начинаем миграцию настроек в базу данных...")
    
    # Импортируем старый config
    try:
        from config import (
            TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL, MAX_FAIL_TIME,
            SILENT_START, SILENT_END, DATA_COLLECTION_TIME,
            RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_INTERVAL,
            RESOURCE_THRESHOLDS, SSH_USERNAME, SSH_KEY_PATH,
            WINDOWS_CREDENTIALS, WINDOWS_SERVER_CONFIGS,
            SERVER_CONFIG, SERVER_TIMEOUTS, PROXMOX_HOSTS,
            BACKUP_PATTERNS, DATABASE_CONFIG
        )
        print("✅ Старый config.py загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки config.py: {e}")
        return False
    
    # Инициализируем менеджер настроек
    from settings_manager import SettingsManager
    settings_manager = SettingsManager()
    
    try:
        # === БАЗОВЫЕ НАСТРОЙКИ ===
        print("📝 Переносим базовые настройки...")
        settings_manager.set_setting('TELEGRAM_TOKEN', TELEGRAM_TOKEN, 'telegram', 'Токен Telegram бота', 'string')
        settings_manager.set_setting('CHAT_IDS', json.dumps(CHAT_IDS), 'telegram', 'ID чатов для уведомлений', 'list')
        
        # === ИНТЕРВАЛЫ ПРОВЕРОК ===
        settings_manager.set_setting('CHECK_INTERVAL', CHECK_INTERVAL, 'monitoring', 'Интервал проверки серверов (секунды)', 'int')
        settings_manager.set_setting('MAX_FAIL_TIME', MAX_FAIL_TIME, 'monitoring', 'Максимальное время простоя до алерта (секунды)', 'int')
        
        # === ВРЕМЕННЫЕ НАСТРОЙКИ ===
        settings_manager.set_setting('SILENT_START', SILENT_START, 'time', 'Начало тихого режима (час)', 'int')
        settings_manager.set_setting('SILENT_END', SILENT_END, 'time', 'Конец тихого режима (час)', 'int')
        settings_manager.set_setting('DATA_COLLECTION_TIME', DATA_COLLECTION_TIME.strftime('%H:%M'), 'time', 'Время сбора данных для отчета', 'time')
        
        # === НАСТРОЙКИ РЕСУРСОВ ===
        settings_manager.set_setting('RESOURCE_CHECK_INTERVAL', RESOURCE_CHECK_INTERVAL, 'resources', 'Интервал проверки ресурсов (секунды)', 'int')
        settings_manager.set_setting('RESOURCE_ALERT_INTERVAL', RESOURCE_ALERT_INTERVAL, 'resources', 'Интервал повторных алертов ресурсов (секунды)', 'int')
        
        # Пороги ресурсов
        settings_manager.set_setting('CPU_WARNING', RESOURCE_THRESHOLDS.get('cpu_warning', 80), 'resources', 'Порог предупреждения CPU (%)', 'int')
        settings_manager.set_setting('CPU_CRITICAL', RESOURCE_THRESHOLDS.get('cpu_critical', 90), 'resources', 'Порог критического CPU (%)', 'int')
        settings_manager.set_setting('RAM_WARNING', RESOURCE_THRESHOLDS.get('ram_warning', 85), 'resources', 'Порог предупреждения RAM (%)', 'int')
        settings_manager.set_setting('RAM_CRITICAL', RESOURCE_THRESHOLDS.get('ram_critical', 95), 'resources', 'Порог критического RAM (%)', 'int')
        settings_manager.set_setting('DISK_WARNING', RESOURCE_THRESHOLDS.get('disk_warning', 80), 'resources', 'Порог предупреждения Disk (%)', 'int')
        settings_manager.set_setting('DISK_CRITICAL', RESOURCE_THRESHOLDS.get('disk_critical', 90), 'resources', 'Порог критического Disk (%)', 'int')
        
        # === АУТЕНТИФИКАЦИЯ ===
        settings_manager.set_setting('SSH_USERNAME', SSH_USERNAME, 'auth', 'Имя пользователя SSH', 'string')
        settings_manager.set_setting('SSH_KEY_PATH', SSH_KEY_PATH, 'auth', 'Путь к SSH ключу', 'string')
        
        print("✅ Базовые настройки перенесены")
        
        # === УЧЕТНЫЕ ДАННЫЕ WINDOWS ===
        print("🖥️ Переносим учетные данные Windows...")
        migrate_windows_credentials(settings_manager, WINDOWS_CREDENTIALS, WINDOWS_SERVER_CONFIGS)
        
        # === СЕРВЕРЫ ===
        print("🔌 Переносим настройки серверов...")
        migrate_servers(settings_manager, SERVER_CONFIG, WINDOWS_SERVER_CONFIGS)
        
        # === ТАЙМАУТЫ ===
        print("⏱️ Переносим таймауты...")
        migrate_timeouts(settings_manager, SERVER_TIMEOUTS)
        
        # === БЭКАПЫ ===
        print("💾 Переносим настройки бэкапов...")
        migrate_backup_settings(settings_manager, BACKUP_PATTERNS, DATABASE_CONFIG, PROXMOX_HOSTS)
        
        print("🎉 Миграция завершена успешно!")
        print("\n📊 Статистика миграции:")
        show_migration_stats(settings_manager)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_windows_credentials(settings_manager, windows_credentials, windows_server_configs):
    """Перенос учетных данных Windows"""
    conn = sqlite3.connect(settings_manager.db_path)
    cursor = conn.cursor()
    
    # Очищаем старые данные
    cursor.execute('DELETE FROM windows_credentials')
    
    # Добавляем базовые учетные данные
    priority = 0
    for cred in windows_credentials:
        cursor.execute('''
            INSERT INTO windows_credentials (username, password, server_type, priority)
            VALUES (?, ?, ?, ?)
        ''', (cred['username'], cred['password'], 'default', priority))
        priority += 1
    
    # Добавляем специфичные для типов серверов
    for server_type, config in windows_server_configs.items():
        for cred in config.get('credentials', []):
            cursor.execute('''
                INSERT INTO windows_credentials (username, password, server_type, priority)
                VALUES (?, ?, ?, ?)
            ''', (cred['username'], cred['password'], server_type, 0))
    
    conn.commit()
    conn.close()
    print(f"✅ Учетные данные Windows перенесены: {len(windows_credentials)} записей")

def migrate_servers(settings_manager, server_config, windows_server_configs):
    """Перенос настроек серверов"""
    conn = sqlite3.connect(settings_manager.db_path)
    cursor = conn.cursor()
    
    # Очищаем старые данные
    cursor.execute('DELETE FROM servers')
    
    server_count = 0
    
    # Windows серверы
    for ip, name in server_config.get('windows_servers', {}).items():
        # Определяем тип Windows сервера
        server_type = 'standard_windows'
        for win_type, config in windows_server_configs.items():
            if ip in config.get('servers', []):
                server_type = win_type
                break
        
        cursor.execute('''
            INSERT INTO servers (ip, name, type, timeout)
            VALUES (?, ?, ?, ?)
        ''', (ip, name, 'rdp', 30))
        server_count += 1
    
    # Linux серверы
    for ip, name in server_config.get('linux_servers', {}).items():
        cursor.execute('''
            INSERT INTO servers (ip, name, type, timeout)
            VALUES (?, ?, ?, ?)
        ''', (ip, name, 'ssh', 15))
        server_count += 1
    
    # Ping серверы
    for ip, name in server_config.get('ping_servers', {}).items():
        cursor.execute('''
            INSERT INTO servers (ip, name, type, timeout)
            VALUES (?, ?, ?, ?)
        ''', (ip, name, 'ping', 10))
        server_count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Серверы перенесены: {server_count} серверов")

def migrate_timeouts(settings_manager, server_timeouts):
    """Перенос таймаутов"""
    # Сохраняем таймауты как JSON в настройках
    settings_manager.set_setting('SERVER_TIMEOUTS', json.dumps(server_timeouts), 'monitoring', 'Таймауты для разных типов серверов', 'dict')
    print(f"✅ Таймауты перенесены: {len(server_timeouts)} настроек")

def migrate_backup_settings(settings_manager, backup_patterns, database_config, proxmox_hosts):
    """Перенос настроек бэкапов"""
    conn = sqlite3.connect(settings_manager.db_path)
    cursor = conn.cursor()
    
    # Очищаем старые данные
    cursor.execute('DELETE FROM backup_patterns')
    
    # Паттерны Proxmox
    pattern_count = 0
    for pattern_type, patterns in backup_patterns.items():
        if isinstance(patterns, list):
            for pattern in patterns:
                cursor.execute('''
                    INSERT INTO backup_patterns (pattern_type, pattern, category)
                    VALUES (?, ?, ?)
                ''', (pattern_type, pattern, 'proxmox'))
                pattern_count += 1
        elif isinstance(patterns, dict):
            for sub_type, sub_patterns in patterns.items():
                if isinstance(sub_patterns, list):
                    for pattern in sub_patterns:
                        cursor.execute('''
                            INSERT INTO backup_patterns (pattern_type, pattern, category)
                            VALUES (?, ?, ?)
                        ''', (f"{pattern_type}_{sub_type}", pattern, 'database'))
                        pattern_count += 1
    
    # Сохраняем конфигурацию баз данных
    settings_manager.set_setting('DATABASE_CONFIG', json.dumps(database_config), 'backup', 'Конфигурация баз данных для бэкапов', 'dict')
    
    # Сохраняем хосты Proxmox
    settings_manager.set_setting('PROXMOX_HOSTS', json.dumps(proxmox_hosts), 'backup', 'Хосты Proxmox для мониторинга бэкапов', 'dict')
    
    conn.commit()
    conn.close()
    print(f"✅ Настройки бэкапов перенесены: {pattern_count} паттернов")

def show_migration_stats(settings_manager):
    """Показать статистику миграции"""
    conn = sqlite3.connect(settings_manager.db_path)
    cursor = conn.cursor()
    
    # Настройки
    cursor.execute('SELECT COUNT(*) FROM settings')
    settings_count = cursor.fetchone()[0]
    
    # Серверы
    cursor.execute('SELECT COUNT(*) FROM servers')
    servers_count = cursor.fetchone()[0]
    
    # Учетные данные Windows
    cursor.execute('SELECT COUNT(*) FROM windows_credentials')
    credentials_count = cursor.fetchone()[0]
    
    # Паттерны бэкапов
    cursor.execute('SELECT COUNT(*) FROM backup_patterns')
    patterns_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"📁 Настроек: {settings_count}")
    print(f"🔌 Серверов: {servers_count}")
    print(f"🔑 Учетных записей Windows: {credentials_count}")
    print(f"🔍 Паттернов бэкапов: {patterns_count}")
    
    # Показываем основные настройки
    print("\n🔧 Основные настройки:")
    important_settings = [
        'TELEGRAM_TOKEN', 'CHECK_INTERVAL', 'SILENT_START', 'SILENT_END',
        'RESOURCE_CHECK_INTERVAL', 'CPU_WARNING', 'RAM_WARNING', 'DISK_WARNING'
    ]
    
    for setting in important_settings:
        value = settings_manager.get_setting(setting)
        print(f"   {setting}: {value}")

def backup_old_config():
    """Создать резервную копию старого config.py"""
    import shutil
    from datetime import datetime
    
    backup_dir = '/opt/monitoring/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'config_backup_{timestamp}.py')
    
    try:
        shutil.copy2('/opt/monitoring/config.py', backup_file)
        print(f"✅ Резервная копия создана: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 МИГРАЦИЯ НАСТРОЕК В БАЗУ ДАННЫХ")
    print("=" * 50)
    
    # Создаем резервную копию
    if not backup_old_config():
        print("❌ Не удалось создать резервную копию. Прерываем миграцию.")
        sys.exit(1)
    
    # Выполняем миграцию
    if migrate_settings():
        print("\n✅ Миграция завершена успешно!")
        print("\n📝 Дальнейшие действия:")
        print("1. Убедитесь, что миграция прошла успешно")
        print("2. Проверьте работу бота с новыми настройками")
        print("3. Удалите старые настройки из config.py (опционально)")
        print("4. Используйте команду /settings в боте для управления настройками")
    else:
        print("\n❌ Миграция завершилась с ошибками!")
        print("⚠️  Система продолжит использовать старый config.py")
    
    print("=" * 50)
    