"""
/config/db_settings_app.py
Server Monitoring System v6.0.16
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database Settings Manager
Система мониторинга серверов
Версия: 6.0.16
Автор: Александр Суханов (c)
Лицензия: MIT
Менеджер настроек БД
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
try:
    from config.settings import DATA_DIR  # type: ignore
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[1] / "data"

class SettingsManager:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DATA_DIR / "settings.db"
        self.init_database()
    
    def get_connection(self):
        """Получить соединение с БД"""
        return sqlite3.connect(str(self.db_path))
    
    def init_database(self):
        """Инициализация базы данных настроек"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица основных настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                description TEXT,
                data_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица серверов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT UNIQUE,
                name TEXT,
                type TEXT,
                credentials TEXT,
                timeout INTEGER,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица Windows учетных данных
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS windows_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT,
                server_type TEXT,
                priority INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица паттернов бэкапов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern TEXT,
                category TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Инициализация настроек по умолчанию
        self.init_default_settings()
    
    def init_default_settings(self):
        """Инициализация настроек по умолчанию"""
        default_settings = [
            # Telegram
            ('TELEGRAM_TOKEN', '', 'telegram', 'Токен Telegram бота', 'string'),
            ('CHAT_IDS', '[]', 'telegram', 'ID чатов для уведомлений', 'list'),
            
            # Интервалы проверок
            ('CHECK_INTERVAL', '60', 'monitoring', 'Интервал проверки серверов (секунды)', 'int'),
            ('MAX_FAIL_TIME', '900', 'monitoring', 'Максимальное время простоя до алерта (секунды)', 'int'),
            
            # Временные настройки
            ('SILENT_START', '20', 'time', 'Начало тихого режима (час)', 'int'),
            ('SILENT_END', '9', 'time', 'Конец тихого режима (час)', 'int'),
            ('DATA_COLLECTION_TIME', '08:30', 'time', 'Время сбора данных для отчета', 'time'),
            
            # Настройки ресурсов
            ('RESOURCE_CHECK_INTERVAL', '1800', 'resources', 'Интервал проверки ресурсов (секунды)', 'int'),
            ('RESOURCE_ALERT_INTERVAL', '1800', 'resources', 'Интервал повторных алертов ресурсов (секунды)', 'int'),
            
            # Пороги ресурсов
            ('CPU_WARNING', '80', 'resources', 'Порог предупреждения CPU (%)', 'int'),
            ('CPU_CRITICAL', '90', 'resources', 'Порог критического CPU (%)', 'int'),
            ('RAM_WARNING', '85', 'resources', 'Порог предупреждения RAM (%)', 'int'),
            ('RAM_CRITICAL', '95', 'resources', 'Порог критического RAM (%)', 'int'),
            ('DISK_WARNING', '80', 'resources', 'Порог предупреждения Disk (%)', 'int'),
            ('DISK_CRITICAL', '90', 'resources', 'Порог критического Disk (%)', 'int'),
            
            # Аутентификация
            ('SSH_USERNAME', 'root', 'auth', 'Имя пользователя SSH', 'string'),
            ('SSH_KEY_PATH', '/root/.ssh/id_rsa', 'auth', 'Путь к SSH ключу', 'string'),
            
            # Бэкапы
            ('BACKUP_ALERT_HOURS', '24', 'backup', 'Часы для алертов о бэкапах', 'int'),
            ('BACKUP_STALE_HOURS', '36', 'backup', 'Часы для устаревших бэкапов', 'int'),
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value, category, description, data_type in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value, category, description, data_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, category, description, data_type))
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key, default=None):
        """Получить значение настройки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value, data_type FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return default
        
        value, data_type = result
        
        # Преобразование типов
        if data_type == 'int':
            return int(value) if value else default
        elif data_type == 'float':
            return float(value) if value else default
        elif data_type == 'bool':
            return value.lower() == 'true' if value else default
        elif data_type == 'list':
            return json.loads(value) if value else default
        elif data_type == 'dict':
            return json.loads(value) if value else default
        else:
            return value if value else default
    
    def set_setting(self, key, value, category='general', description='', data_type='string'):
        """Установить значение настройки"""
        # Определяем тип данных
        if data_type == 'auto':
            if isinstance(value, int):
                data_type = 'int'
                value = str(value)
            elif isinstance(value, float):
                data_type = 'float'
                value = str(value)
            elif isinstance(value, bool):
                data_type = 'bool'
                value = str(value).lower()
            elif isinstance(value, (list, dict)):
                data_type = 'list' if isinstance(value, list) else 'dict'
                value = json.dumps(value, ensure_ascii=False)
            else:
                data_type = 'string'
                value = str(value)
        else:
            value = str(value)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, category, description, data_type, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, value, category, description, data_type))
        
        conn.commit()
        conn.close()
        return True
    
    def get_all_settings(self, category=None):
        """Получить все настройки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT key, value, data_type, description FROM settings WHERE category = ? ORDER BY key', (category,))
        else:
            cursor.execute('SELECT key, value, data_type, description FROM settings ORDER BY category, key')
        
        settings = {}
        for key, value, data_type, description in cursor.fetchall():
            # Преобразование типов
            if data_type == 'int':
                settings[key] = int(value) if value else 0
            elif data_type == 'float':
                settings[key] = float(value) if value else 0.0
            elif data_type == 'bool':
                settings[key] = value.lower() == 'true'
            elif data_type == 'list':
                settings[key] = json.loads(value) if value else []
            elif data_type == 'dict':
                settings[key] = json.loads(value) if value else {}
            else:
                settings[key] = value
        
        conn.close()
        return settings
    
    def get_categories(self):
        """Получить список категорий"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM settings ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return categories

    def get_servers_by_type(self, server_type):
        """Получить серверы по типу"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ip, name FROM servers WHERE type = ? AND enabled = 1', (server_type,))
        servers = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return servers

    def add_server(self, ip, name, server_type, credentials=None, timeout=30):
        """Добавить сервер"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        credentials_json = json.dumps(credentials) if credentials else '[]'
        
        cursor.execute('''
            INSERT OR REPLACE INTO servers (ip, name, type, credentials, timeout)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip, name, server_type, credentials_json, timeout))
        
        conn.commit()
        conn.close()
        return True

    def delete_server(self, ip):
        """Удалить сервер"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM servers WHERE ip = ?', (ip,))
        
        conn.commit()
        conn.close()
        return True

    def get_all_servers(self):
        """Получить все серверы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ip, name, type, credentials, timeout FROM servers WHERE enabled = 1')
        
        servers = []
        for ip, name, server_type, credentials_json, timeout in cursor.fetchall():
            credentials = json.loads(credentials_json) if credentials_json else []
            servers.append({
                'ip': ip,
                'name': name,
                'type': server_type,
                'credentials': credentials,
                'timeout': timeout
            })
        
        conn.close()
        return servers

    def get_backup_patterns(self):
        """Получить паттерны бэкапов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT pattern_type, pattern, category FROM backup_patterns WHERE enabled = 1')
        
        patterns = {}
        for pattern_type, pattern, category in cursor.fetchall():
            if category not in patterns:
                patterns[category] = {}
            if pattern_type not in patterns[category]:
                patterns[category][pattern_type] = []
            patterns[category][pattern_type].append(pattern)
        
        conn.close()
        return patterns

    def get_backup_status_map(self):
        """Получить карту статусов бэкапов"""
        return self.get_setting('BACKUP_STATUS_MAP', {
            'backup successful': 'success',
            'successful': 'success',
            'ok': 'success',
            'completed': 'success', 
            'finished': 'success',
            'backup failed': 'failed',
            'failed': 'failed',
            'error': 'failed',
            'errors': 'failed',
            'warning': 'warning',
            'partial': 'partial'
        })

    def get_duplicate_ip_hosts(self):
        """Получить хосты с одинаковыми IP"""
        return self.get_setting('DUPLICATE_IP_HOSTS', {
            '95.170.153.118': ['pve-rubicon', 'pve2-rubicon']
        })

    def get_hostname_aliases(self):
        """Получить алиасы имен хостов"""
        return self.get_setting('HOSTNAME_ALIASES', {
            'pve-rubicon': ['rubicon', 'pve-rubicon', 'rubicon-pve', 'pve1-rubicon'],
            'pve2-rubicon': ['rubicon2', 'pve2-rubicon', 'rubicon2-pve', 'pve-rubicon2'],
        })

    def get_web_settings(self):
        """Получить настройки веб-интерфейса"""
        return {
            'WEB_PORT': self.get_setting('WEB_PORT', 5000),
            'WEB_HOST': self.get_setting('WEB_HOST', '0.0.0.0')
        }

    def get_windows_credentials_db(self):
        """Получить учетные данные Windows из БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, password, server_type 
            FROM windows_credentials 
            WHERE enabled = 1 
            ORDER BY server_type, priority
        ''')
        
        credentials = {}
        for username, password, server_type in cursor.fetchall():
            if server_type not in credentials:
                credentials[server_type] = []
            credentials[server_type].append({"username": username, "password": password})
        
        conn.close()
        return credentials
        
    def get_proxmox_hosts(self):
        """Получить хосты Proxmox"""
        return self.get_setting('PROXMOX_HOSTS', {})

    def get_database_config(self):
        """Получить конфигурацию баз данных"""
        return self.get_setting('DATABASE_CONFIG', {})

    def get_server_timeouts(self):
        """Получить таймауты серверов"""
        return self.get_setting('SERVER_TIMEOUTS', {})

    def get_windows_credentials(self, server_type=None):
        """Получить учетные данные Windows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if server_type:
            cursor.execute('''
                SELECT id, username, password, server_type, priority, enabled 
                FROM windows_credentials 
                WHERE server_type = ? AND enabled = 1 
                ORDER BY priority
            ''', (server_type,))
        else:
            cursor.execute('''
                SELECT id, username, password, server_type, priority, enabled 
                FROM windows_credentials 
                WHERE enabled = 1 
                ORDER BY server_type, priority
            ''')
        
        credentials = []
        for id, username, password, cred_server_type, priority, enabled in cursor.fetchall():
            credentials.append({
                'id': id,
                'username': username,
                'password': password,
                'server_type': cred_server_type,
                'priority': priority,
                'enabled': enabled
            })
        
        conn.close()
        return credentials
    
    def add_windows_credential(self, username, password, server_type='default', priority=0):
        """Добавить учетные данные Windows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO windows_credentials (username, password, server_type, priority)
            VALUES (?, ?, ?, ?)
        ''', (username, password, server_type, priority))
        
        conn.commit()
        conn.close()
        return True
    
    def update_windows_credential(self, cred_id, username=None, password=None, server_type=None, priority=None, enabled=None):
        """Обновить учетные данные Windows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        update_fields = []
        params = []
        
        if username is not None:
            update_fields.append("username = ?")
            params.append(username)
        if password is not None:
            update_fields.append("password = ?")
            params.append(password)
        if server_type is not None:
            update_fields.append("server_type = ?")
            params.append(server_type)
        if priority is not None:
            update_fields.append("priority = ?")
            params.append(priority)
        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(enabled)
        
        if not update_fields:
            return False
        
        params.append(cred_id)
        
        cursor.execute(f'''
            UPDATE windows_credentials 
            SET {', '.join(update_fields)} 
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
        return True
    
    def delete_windows_credential(self, cred_id):
        """Удалить учетные данные Windows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM windows_credentials WHERE id = ?', (cred_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_windows_server_types(self):
        """Получить типы Windows серверов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT server_type FROM windows_credentials ORDER BY server_type')
        types = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return types
    
# Глобальный экземпляр менеджера настроек
settings_manager = SettingsManager()
