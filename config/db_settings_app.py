"""
/config/db_settings_app.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database Settings Manager
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРµРЅРµРґР¶РµСЂ РЅР°СЃС‚СЂРѕРµРє Р‘Р”
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
        """РџРѕР»СѓС‡РёС‚СЊ СЃРѕРµРґРёРЅРµРЅРёРµ СЃ Р‘Р”"""
        return sqlite3.connect(str(self.db_path))
    
    def init_database(self):
        """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С… РЅР°СЃС‚СЂРѕРµРє"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # РўР°Р±Р»РёС†Р° РѕСЃРЅРѕРІРЅС‹С… РЅР°СЃС‚СЂРѕРµРє
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
        
        # РўР°Р±Р»РёС†Р° СЃРµСЂРІРµСЂРѕРІ
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
        
        # РўР°Р±Р»РёС†Р° Windows СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…
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
        
        # РўР°Р±Р»РёС†Р° РїР°С‚С‚РµСЂРЅРѕРІ Р±СЌРєР°РїРѕРІ
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
        
        # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ РЅР°СЃС‚СЂРѕРµРє РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
        self.init_default_settings()
    
    def init_default_settings(self):
        """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ РЅР°СЃС‚СЂРѕРµРє РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ"""
        default_settings = [
            # Telegram
            ('TELEGRAM_TOKEN', '', 'telegram', 'РўРѕРєРµРЅ Telegram Р±РѕС‚Р°', 'string'),
            ('CHAT_IDS', '[]', 'telegram', 'ID С‡Р°С‚РѕРІ РґР»СЏ СѓРІРµРґРѕРјР»РµРЅРёР№', 'list'),
            
            # РРЅС‚РµСЂРІР°Р»С‹ РїСЂРѕРІРµСЂРѕРє
            ('CHECK_INTERVAL', '60', 'monitoring', 'РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ (СЃРµРєСѓРЅРґС‹)', 'int'),
            ('MAX_FAIL_TIME', '900', 'monitoring', 'РњР°РєСЃРёРјР°Р»СЊРЅРѕРµ РІСЂРµРјСЏ РїСЂРѕСЃС‚РѕСЏ РґРѕ Р°Р»РµСЂС‚Р° (СЃРµРєСѓРЅРґС‹)', 'int'),
            
            # Р’СЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё
            ('SILENT_START', '20', 'time', 'РќР°С‡Р°Р»Рѕ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (С‡Р°СЃ)', 'int'),
            ('SILENT_END', '9', 'time', 'РљРѕРЅРµС† С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (С‡Р°СЃ)', 'int'),
            ('DATA_COLLECTION_TIME', '08:30', 'time', 'Р’СЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С… РґР»СЏ РѕС‚С‡РµС‚Р°', 'time'),
            
            # РќР°СЃС‚СЂРѕР№РєРё СЂРµСЃСѓСЂСЃРѕРІ
            ('RESOURCE_CHECK_INTERVAL', '1800', 'resources', 'РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ (СЃРµРєСѓРЅРґС‹)', 'int'),
            ('RESOURCE_ALERT_INTERVAL', '1800', 'resources', 'РРЅС‚РµСЂРІР°Р» РїРѕРІС‚РѕСЂРЅС‹С… Р°Р»РµСЂС‚РѕРІ СЂРµСЃСѓСЂСЃРѕРІ (СЃРµРєСѓРЅРґС‹)', 'int'),
            
            # РџРѕСЂРѕРіРё СЂРµСЃСѓСЂСЃРѕРІ
            ('CPU_WARNING', '80', 'resources', 'РџРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ CPU (%)', 'int'),
            ('CPU_CRITICAL', '90', 'resources', 'РџРѕСЂРѕРі РєСЂРёС‚РёС‡РµСЃРєРѕРіРѕ CPU (%)', 'int'),
            ('RAM_WARNING', '85', 'resources', 'РџРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ RAM (%)', 'int'),
            ('RAM_CRITICAL', '95', 'resources', 'РџРѕСЂРѕРі РєСЂРёС‚РёС‡РµСЃРєРѕРіРѕ RAM (%)', 'int'),
            ('DISK_WARNING', '80', 'resources', 'РџРѕСЂРѕРі РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ Disk (%)', 'int'),
            ('DISK_CRITICAL', '90', 'resources', 'РџРѕСЂРѕРі РєСЂРёС‚РёС‡РµСЃРєРѕРіРѕ Disk (%)', 'int'),
            
            # РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ
            ('SSH_USERNAME', 'root', 'auth', 'РРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ SSH', 'string'),
            ('SSH_KEY_PATH', '/root/.ssh/id_rsa', 'auth', 'РџСѓС‚СЊ Рє SSH РєР»СЋС‡Сѓ', 'string'),
            
            # Р‘СЌРєР°РїС‹
            ('BACKUP_ALERT_HOURS', '24', 'backup', 'Р§Р°СЃС‹ РґР»СЏ Р°Р»РµСЂС‚РѕРІ Рѕ Р±СЌРєР°РїР°С…', 'int'),
            ('BACKUP_STALE_HOURS', '36', 'backup', 'Р§Р°СЃС‹ РґР»СЏ СѓСЃС‚Р°СЂРµРІС€РёС… Р±СЌРєР°РїРѕРІ', 'int'),
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
        """РџРѕР»СѓС‡РёС‚СЊ Р·РЅР°С‡РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєРё"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value, data_type FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return default
        
        value, data_type = result
        
        # РџСЂРµРѕР±СЂР°Р·РѕРІР°РЅРёРµ С‚РёРїРѕРІ
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
        """РЈСЃС‚Р°РЅРѕРІРёС‚СЊ Р·РЅР°С‡РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєРё"""
        # РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РґР°РЅРЅС‹С…
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
        """РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ РЅР°СЃС‚СЂРѕР№РєРё"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT key, value, data_type, description FROM settings WHERE category = ? ORDER BY key', (category,))
        else:
            cursor.execute('SELECT key, value, data_type, description FROM settings ORDER BY category, key')
        
        settings = {}
        for key, value, data_type, description in cursor.fetchall():
            # РџСЂРµРѕР±СЂР°Р·РѕРІР°РЅРёРµ С‚РёРїРѕРІ
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
        """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РєР°С‚РµРіРѕСЂРёР№"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM settings ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return categories

    def get_servers_by_type(self, server_type):
        """РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂС‹ РїРѕ С‚РёРїСѓ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT ip, name FROM servers WHERE type = ? AND enabled = 1', (server_type,))
        servers = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return servers

    def add_server(self, ip, name, server_type, credentials=None, timeout=30):
        """Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ"""
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
        """РЈРґР°Р»РёС‚СЊ СЃРµСЂРІРµСЂ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM servers WHERE ip = ?', (ip,))
        
        conn.commit()
        conn.close()
        return True

    def get_all_servers(self):
        """РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ СЃРµСЂРІРµСЂС‹"""
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
        """РџРѕР»СѓС‡РёС‚СЊ РїР°С‚С‚РµСЂРЅС‹ Р±СЌРєР°РїРѕРІ"""
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
        """РџРѕР»СѓС‡РёС‚СЊ РєР°СЂС‚Сѓ СЃС‚Р°С‚СѓСЃРѕРІ Р±СЌРєР°РїРѕРІ"""
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
        """РџРѕР»СѓС‡РёС‚СЊ С…РѕСЃС‚С‹ СЃ РѕРґРёРЅР°РєРѕРІС‹РјРё IP"""
        return self.get_setting('DUPLICATE_IP_HOSTS', {
            '95.170.153.118': ['pve-rubicon', 'pve2-rubicon']
        })

    def get_hostname_aliases(self):
        """РџРѕР»СѓС‡РёС‚СЊ Р°Р»РёР°СЃС‹ РёРјРµРЅ С…РѕСЃС‚РѕРІ"""
        return self.get_setting('HOSTNAME_ALIASES', {
            'pve-rubicon': ['rubicon', 'pve-rubicon', 'rubicon-pve', 'pve1-rubicon'],
            'pve2-rubicon': ['rubicon2', 'pve2-rubicon', 'rubicon2-pve', 'pve-rubicon2'],
        })

    def get_web_settings(self):
        """РџРѕР»СѓС‡РёС‚СЊ РЅР°СЃС‚СЂРѕР№РєРё РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°"""
        return {
            'WEB_PORT': self.get_setting('WEB_PORT', 5000),
            'WEB_HOST': self.get_setting('WEB_HOST', '0.0.0.0')
        }

    def get_windows_credentials_db(self):
        """РџРѕР»СѓС‡РёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows РёР· Р‘Р”"""
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
        """РџРѕР»СѓС‡РёС‚СЊ С…РѕСЃС‚С‹ Proxmox"""
        return self.get_setting('PROXMOX_HOSTS', {})

    def get_database_config(self):
        """РџРѕР»СѓС‡РёС‚СЊ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ Р±Р°Р· РґР°РЅРЅС‹С…"""
        return self.get_setting('DATABASE_CONFIG', {})

    def get_server_timeouts(self):
        """РџРѕР»СѓС‡РёС‚СЊ С‚Р°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ"""
        return self.get_setting('SERVER_TIMEOUTS', {})

    def get_windows_credentials(self, server_type=None):
        """РџРѕР»СѓС‡РёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows"""
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
        """Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows"""
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
        """РћР±РЅРѕРІРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows"""
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
        """РЈРґР°Р»РёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM windows_credentials WHERE id = ?', (cred_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def get_windows_server_types(self):
        """РџРѕР»СѓС‡РёС‚СЊ С‚РёРїС‹ Windows СЃРµСЂРІРµСЂРѕРІ"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT server_type FROM windows_credentials ORDER BY server_type')
        types = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return types
    
# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РјРµРЅРµРґР¶РµСЂР° РЅР°СЃС‚СЂРѕРµРє
settings_manager = SettingsManager()
