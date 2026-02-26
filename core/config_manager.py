"""
/core/config_manager.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Configuration Manager
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРµРЅРµРґР¶РµСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё
"""

import sqlite3
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from lib.logging import debug_log, error_log, setup_logging

try:
    from config.settings import DATA_DIR  # type: ignore
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Р›РѕРіРіРµСЂ РґР»СЏ СЌС‚РѕРіРѕ РјРѕРґСѓР»СЏ
_logger = setup_logging("config")

class ConfigManager:
    """РњРµРЅРµРґР¶РµСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЃ РїРѕРґРґРµСЂР¶РєРѕР№ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ РјРµРЅРµРґР¶РµСЂР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё
        
        Args:
            db_path: РџСѓС‚СЊ Рє С„Р°Р№Р»Сѓ Р±Р°Р·С‹ РґР°РЅРЅС‹С…
        """
        self.db_path = Path(db_path) if db_path else DATA_DIR / "settings.db"
        self._cache = {}
        self._local = threading.local()
        self._connection = None
        self.init_database()
        debug_log(f"РњРµРЅРµРґР¶РµСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """РџРѕР»СѓС‡РёС‚СЊ СЃРѕРµРґРёРЅРµРЅРёРµ СЃ Р‘Р” (РѕС‚РґРµР»СЊРЅРѕРµ СЃРѕРµРґРёРЅРµРЅРёРµ РЅР° РїРѕС‚РѕРє)"""
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=30)
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        return conn

    def close_connection(self) -> None:
        """Р—Р°РєСЂС‹С‚СЊ СЃРѕРµРґРёРЅРµРЅРёРµ СЃ Р‘Р” (РґР»СЏ С‚РµРєСѓС‰РµРіРѕ РїРѕС‚РѕРєР°)"""
        conn = getattr(self._local, "connection", None)
        if conn:
            conn.close()
            self._local.connection = None

    def init_database(self) -> None:
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
                type TEXT CHECK(type IN ('rdp', 'ssh', 'ping')),
                credentials TEXT,
                timeout INTEGER DEFAULT 30,
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
        
        # РўР°Р±Р»РёС†Р° РєР°С‚РµРіРѕСЂРёР№ Р±Р°Р· РґР°РЅРЅС‹С…
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS database_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # РўР°Р±Р»РёС†Р° Р±Р°Р· РґР°РЅРЅС‹С…
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS databases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT,
                host TEXT,
                port INTEGER,
                database TEXT,
                username TEXT,
                password TEXT,
                backup_path TEXT,
                enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES database_categories(id)
            )
        ''')
        
        conn.commit()
        self.init_default_settings()
        debug_log("Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅР°СЃС‚СЂРѕРµРє РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅР°")
    
    def init_default_settings(self) -> None:
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
            ('ZFS_SERVERS', '{}', 'backup', 'РЎРїРёСЃРѕРє ZFS СЃРµСЂРІРµСЂРѕРІ Рё РјР°СЃСЃРёРІРѕРІ', 'dict'),
            
            # Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ
            ('WEB_PORT', '5000', 'web', 'РџРѕСЂС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°', 'int'),
            ('WEB_HOST', '0.0.0.0', 'web', 'РҐРѕСЃС‚ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°', 'string'),
            
            # РћС‚Р»Р°РґРєР°
            ('DEBUG_MODE', 'False', 'debug', 'Р РµР¶РёРј РѕС‚Р»Р°РґРєРё', 'bool'),
            ('LOG_LEVEL', 'INFO', 'debug', 'РЈСЂРѕРІРµРЅСЊ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ', 'string'),
            
            # РўР°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ
            ('SERVER_TIMEOUTS', '{}', 'timeouts', 'РўР°Р№РјР°СѓС‚С‹ СЃРµСЂРІРµСЂРѕРІ РїРѕ С‚РёРїР°Рј', 'dict'),
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value, category, description, data_type in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value, category, description, data_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, category, description, data_type))
        
        conn.commit()
        debug_log(f"Р—Р°РіСЂСѓР¶РµРЅРѕ {len(default_settings)} РЅР°СЃС‚СЂРѕРµРє РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ")
    
    def get_setting(
        self, 
        key: str, 
        default: Any = None,
        use_cache: bool = True
    ) -> Any:
        """
        РџРѕР»СѓС‡РёС‚СЊ Р·РЅР°С‡РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєРё
        
        Args:
            key: РљР»СЋС‡ РЅР°СЃС‚СЂРѕР№РєРё
            default: Р—РЅР°С‡РµРЅРёРµ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
            use_cache: РСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РєСЌС€
            
        Returns:
            Р—РЅР°С‡РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєРё
        """
        if use_cache and key in self._cache:
            return self._cache[key]
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT value, data_type FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
        except Exception as e:
            error_log(f"РћС€РёР±РєР° С‡С‚РµРЅРёСЏ РЅР°СЃС‚СЂРѕР№РєРё {key}: {e}")
            self._cache[key] = default
            return default
                
        if not result:
            self._cache[key] = default
            return default
        
        value_str, data_type = result
        
        # РџСЂРµРѕР±СЂР°Р·РѕРІР°РЅРёРµ С‚РёРїРѕРІ
        try:
            if data_type == 'int':
                value = int(value_str) if value_str else default
            elif data_type == 'float':
                value = float(value_str) if value_str else default
            elif data_type == 'bool':
                value = value_str.lower() == 'true' if value_str else default
            elif data_type == 'list':
                value = json.loads(value_str) if value_str else default
            elif data_type == 'dict':
                value = json.loads(value_str) if value_str else default
            elif data_type == 'time':
                value = value_str if value_str else default
            else:  # string
                value = value_str if value_str else default
        except (json.JSONDecodeError, ValueError) as e:
            error_log(f"РћС€РёР±РєР° РїСЂРµРѕР±СЂР°Р·РѕРІР°РЅРёСЏ РЅР°СЃС‚СЂРѕР№РєРё {key}: {e}, Р·РЅР°С‡РµРЅРёРµ: {value_str}")
            value = default
        
        self._cache[key] = value
        return value
    
    def set_setting(
        self, 
        key: str, 
        value: Any, 
        category: str = 'general', 
        description: str = '', 
        data_type: str = 'auto'
    ) -> bool:
        """
        РЈСЃС‚Р°РЅРѕРІРёС‚СЊ Р·РЅР°С‡РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєРё
        
        Args:
            key: РљР»СЋС‡ РЅР°СЃС‚СЂРѕР№РєРё
            value: Р—РЅР°С‡РµРЅРёРµ
            category: РљР°С‚РµРіРѕСЂРёСЏ
            description: РћРїРёСЃР°РЅРёРµ
            data_type: РўРёРї РґР°РЅРЅС‹С… (auto/int/float/bool/list/dict/string/time)
            
        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        # РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РґР°РЅРЅС‹С… РµСЃР»Рё auto
        if data_type == 'auto':
            if isinstance(value, int):
                data_type = 'int'
                value_str = str(value)
            elif isinstance(value, float):
                data_type = 'float'
                value_str = str(value)
            elif isinstance(value, bool):
                data_type = 'bool'
                value_str = str(value).lower()
            elif isinstance(value, list):
                data_type = 'list'
                value_str = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, dict):
                data_type = 'dict'
                value_str = json.dumps(value, ensure_ascii=False)
            else:
                data_type = 'string'
                value_str = str(value)
        else:
            value_str = str(value)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, category, description, data_type, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value_str, category, description, data_type))
            
            conn.commit()
            
            # РћР±РЅРѕРІР»СЏРµРј РєСЌС€
            self._cache[key] = value
            
            debug_log(f"РќР°СЃС‚СЂРѕР№РєР° РѕР±РЅРѕРІР»РµРЅР°: {key} = {value_str[:50]}{'...' if len(value_str) > 50 else ''}")
            return True
            
        except Exception as e:
            error_log(f"РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РЅР°СЃС‚СЂРѕР№РєРё {key}: {e}")
            return False
    
    def get_all_settings(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ РЅР°СЃС‚СЂРѕР№РєРё
        
        Args:
            category: Р¤РёР»СЊС‚СЂ РїРѕ РєР°С‚РµРіРѕСЂРёРё
            
        Returns:
            РЎР»РѕРІР°СЂСЊ РІСЃРµС… РЅР°СЃС‚СЂРѕРµРє
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT key, value, data_type 
                FROM settings 
                WHERE category = ? 
                ORDER BY key
            ''', (category,))
        else:
            cursor.execute('''
                SELECT key, value, data_type 
                FROM settings 
                ORDER BY category, key
            ''')
        
        settings = {}
        for key, value_str, data_type in cursor.fetchall():
            try:
                if data_type == 'int':
                    settings[key] = int(value_str) if value_str else 0
                elif data_type == 'float':
                    settings[key] = float(value_str) if value_str else 0.0
                elif data_type == 'bool':
                    settings[key] = value_str.lower() == 'true'
                elif data_type == 'list':
                    settings[key] = json.loads(value_str) if value_str else []
                elif data_type == 'dict':
                    settings[key] = json.loads(value_str) if value_str else {}
                elif data_type == 'time':
                    settings[key] = value_str if value_str else ''
                else:
                    settings[key] = value_str if value_str else ''
            except (json.JSONDecodeError, ValueError) as e:
                error_log(f"РћС€РёР±РєР° РїСЂРµРѕР±СЂР°Р·РѕРІР°РЅРёСЏ РЅР°СЃС‚СЂРѕР№РєРё {key}: {e}")
                settings[key] = None
        
        return settings
    
    def get_categories(self) -> List[str]:
        """
        РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РєР°С‚РµРіРѕСЂРёР№ РЅР°СЃС‚СЂРѕРµРє
        
        Returns:
            РЎРїРёСЃРѕРє РєР°С‚РµРіРѕСЂРёР№
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM settings ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        
        return categories
    
    def get_servers_by_type(self, server_type: str) -> List[Dict[str, Any]]:
        """
        РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂС‹ РїРѕ С‚РёРїСѓ
        
        Args:
            server_type: РўРёРї СЃРµСЂРІРµСЂР° (rdp, ssh, ping)
            
        Returns:
            РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip, name, type, credentials, timeout 
            FROM servers 
            WHERE type = ? AND enabled = 1
            ORDER BY name
        ''', (server_type,))
        
        servers = []
        for row in cursor.fetchall():
            servers.append({
                'ip': row[0],
                'name': row[1],
                'type': row[2],
                'credentials': json.loads(row[3]) if row[3] else [],
                'timeout': row[4]
            })
        
        return servers
    
    def get_all_servers(self, include_disabled: bool = False) -> List[Dict[str, Any]]:
        """
        РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ

        Args:
            include_disabled: Р’РєР»СЋС‡Р°С‚СЊ РІС‹РєР»СЋС‡РµРЅРЅС‹Рµ СЃРµСЂРІРµСЂС‹

        Returns:
            РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if include_disabled:
            cursor.execute('''
                SELECT ip, name, type, credentials, timeout, enabled
                FROM servers
                ORDER BY type, name
            ''')
        else:
            cursor.execute('''
                SELECT ip, name, type, credentials, timeout, enabled
                FROM servers
                WHERE enabled = 1
                ORDER BY type, name
            ''')

        servers: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            servers.append({
                'ip': row[0],
                'name': row[1],
                'type': row[2],
                'credentials': json.loads(row[3]) if row[3] else [],
                'timeout': row[4],
                'enabled': bool(row[5])
            })

        return servers

    def set_server_enabled(self, ip: str, enabled: bool) -> bool:
        """
        Р’РєР»СЋС‡РёС‚СЊ РёР»Рё РІС‹РєР»СЋС‡РёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂР°

        Args:
            ip: IP Р°РґСЂРµСЃ СЃРµСЂРІРµСЂР°
            enabled: РќРѕРІС‹Р№ СЃС‚Р°С‚СѓСЃ

        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'UPDATE servers SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE ip = ?',
                (1 if enabled else 0, ip)
            )
            conn.commit()

            self._cache = {}

            debug_log(f"РЎРµСЂРІРµСЂ {ip} {'РІРєР»СЋС‡РµРЅ' if enabled else 'РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ'}")
            return cursor.rowcount > 0

        except Exception as e:
            error_log(f"РћС€РёР±РєР° РёР·РјРµРЅРµРЅРёСЏ СЃС‚Р°С‚СѓСЃР° СЃРµСЂРІРµСЂР° {ip}: {e}")
            return False

    def get_server_enabled(self, ip: str) -> bool:
        """
        РџСЂРѕРІРµСЂРёС‚СЊ СЃС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂР°

        Args:
            ip: IP Р°РґСЂРµСЃ СЃРµСЂРІРµСЂР°

        Returns:
            True РµСЃР»Рё СЃРµСЂРІРµСЂ Р°РєС‚РёРІРµРЅ
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT enabled FROM servers WHERE ip = ?', (ip,))
            row = cursor.fetchone()
            if row is None:
                return True
            return bool(row[0])
        except Exception as e:
            error_log(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЃС‚Р°С‚СѓСЃР° СЃРµСЂРІРµСЂР° {ip}: {e}")
            return True


    # ------------------------------------------------------------
    # Backward-compatible API (С‚РѕРЅРєРёР№ Р°РґР°РїС‚РµСЂ)
    # ------------------------------------------------------------
    def get_servers(self) -> List[Dict[str, Any]]:
        """
        Backward-compatible alias.
        РЎС‚Р°СЂС‹Р№ РєРѕРґ РѕР¶РёРґР°РµС‚ ConfigManager.get_servers(), РїРѕСЌС‚РѕРјСѓ РѕСЃС‚Р°РІР»СЏРµРј.
        """
        return self.get_all_servers()


        servers = []
        for row in cursor.fetchall():
            servers.append({
                'ip': row[0],
                'name': row[1],
                'type': row[2],
                'credentials': json.loads(row[3]) if row[3] else [],
                'timeout': row[4]
            })
        
        return servers
    
    def add_server(
        self,
        ip: str,
        name: str,
        server_type: str,
        credentials: Optional[List[Dict]] = None,
        timeout: int = 30,
        enabled: bool = True
    ) -> bool:
        """
        Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ
        
        Args:
            ip: IP Р°РґСЂРµСЃ
            name: РРјСЏ СЃРµСЂРІРµСЂР°
            server_type: РўРёРї СЃРµСЂРІРµСЂР°
            credentials: РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ
            timeout: РўР°Р№РјР°СѓС‚
            
        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        credentials_json = json.dumps(credentials) if credentials else '[]'
        enabled_value = 1 if enabled else 0
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO servers (ip, name, type, credentials, timeout, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ip, name, server_type, credentials_json, timeout, enabled_value))
            
            conn.commit()
            
            # РћС‡РёС‰Р°РµРј РєСЌС€
            self._cache = {}
            
            debug_log(f"РЎРµСЂРІРµСЂ РґРѕР±Р°РІР»РµРЅ: {name} ({ip}) С‚РёРї: {server_type}")
            return True
            
        except Exception as e:
            error_log(f"РћС€РёР±РєР° РґРѕР±Р°РІР»РµРЅРёСЏ СЃРµСЂРІРµСЂР° {ip}: {e}")
            return False
    
    def delete_server(self, ip: str) -> bool:
        """
        РЈРґР°Р»РёС‚СЊ СЃРµСЂРІРµСЂ
        
        Args:
            ip: IP Р°РґСЂРµСЃ СЃРµСЂРІРµСЂР°
            
        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM servers WHERE ip = ?', (ip,))
            conn.commit()
            
            # РћС‡РёС‰Р°РµРј РєСЌС€
            self._cache = {}
            
            debug_log(f"РЎРµСЂРІРµСЂ СѓРґР°Р»РµРЅ: {ip}")
            return True
            
        except Exception as e:
            error_log(f"РћС€РёР±РєР° СѓРґР°Р»РµРЅРёСЏ СЃРµСЂРІРµСЂР° {ip}: {e}")
            return False
    
    def get_windows_credentials_db(self) -> Dict[str, List[Dict[str, str]]]:
        """
        РџРѕР»СѓС‡РёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows РёР· Р‘Р”
        
        Returns:
            РЎР»РѕРІР°СЂСЊ СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С… РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
        """
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
            credentials[server_type].append({
                "username": username,
                "password": password
            })
        
        return credentials
    
    def get_windows_credentials(self, server_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        РџРѕР»СѓС‡РёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows
        
        Args:
            server_type: Р¤РёР»СЊС‚СЂ РїРѕ С‚РёРїСѓ СЃРµСЂРІРµСЂР°
            
        Returns:
            РЎРїРёСЃРѕРє СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…
        """
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
        for row in cursor.fetchall():
            credentials.append({
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'server_type': row[3],
                'priority': row[4],
                'enabled': row[5]
            })
        
        return credentials

    def get_windows_server_types(self) -> List[str]:
        """
        РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє С‚РёРїРѕРІ Windows-СЃРµСЂРІРµСЂРѕРІ РёР· Р±Р°Р·С‹

        Returns:
            РЎРїРёСЃРѕРє СѓРЅРёРєР°Р»СЊРЅС‹С… С‚РёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT server_type
            FROM windows_credentials
            WHERE enabled = 1
            ORDER BY server_type
        ''')

        return [row[0] for row in cursor.fetchall()]
        
    def add_windows_credential(
        self, 
        username: str, 
        password: str, 
        server_type: str = 'default', 
        priority: int = 0
    ) -> bool:
        """
        Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows
        
        Args:
            username: РРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
            password: РџР°СЂРѕР»СЊ
            server_type: РўРёРї СЃРµСЂРІРµСЂР°
            priority: РџСЂРёРѕСЂРёС‚РµС‚
            
        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO windows_credentials (username, password, server_type, priority)
                VALUES (?, ?, ?, ?)
            ''', (username, password, server_type, priority))
            
            conn.commit()
            
            debug_log(f"РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РґРѕР±Р°РІР»РµРЅС‹: {username} РґР»СЏ {server_type}")
            return True
            
        except Exception as e:
            error_log(f"РћС€РёР±РєР° РґРѕР±Р°РІР»РµРЅРёСЏ СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…: {e}")
            return False
    
    def update_windows_credential(
        self, 
        cred_id: int, 
        **kwargs
    ) -> bool:
        """
        РћР±РЅРѕРІРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows
        
        Args:
            cred_id: ID СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…
            **kwargs: РџРѕР»СЏ РґР»СЏ РѕР±РЅРѕРІР»РµРЅРёСЏ
            
        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        allowed_fields = ['username', 'password', 'server_type', 'priority', 'enabled']
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return False
        
        params.append(cred_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                UPDATE windows_credentials 
                SET {', '.join(update_fields)} 
                WHERE id = ?
            ''', params)
            
            conn.commit()
            
            debug_log(f"РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РѕР±РЅРѕРІР»РµРЅС‹: ID {cred_id}")
            return True
            
        except Exception as e:
            error_log(f"РћС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С… ID {cred_id}: {e}")
            return False
    
    def delete_windows_credential(self, cred_id: int) -> bool:
        """
        РЈРґР°Р»РёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows
        
        Args:
            cred_id: ID СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С…
            
        Returns:
            True РµСЃР»Рё СѓСЃРїРµС€РЅРѕ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM windows_credentials WHERE id = ?', (cred_id,))
            conn.commit()
            
            debug_log(f"РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ СѓРґР°Р»РµРЅС‹: ID {cred_id}")
            return True
            
        except Exception as e:
            error_log(f"РћС€РёР±РєР° СѓРґР°Р»РµРЅРёСЏ СѓС‡РµС‚РЅС‹С… РґР°РЅРЅС‹С… ID {cred_id}: {e}")
            return False
    
    def get_backup_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """
        РџРѕР»СѓС‡РёС‚СЊ РїР°С‚С‚РµСЂРЅС‹ Р±СЌРєР°РїРѕРІ
        
        Returns:
            РЎР»РѕРІР°СЂСЊ РїР°С‚С‚РµСЂРЅРѕРІ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern_type, pattern, category 
            FROM backup_patterns 
            WHERE enabled = 1
            ORDER BY category, pattern_type
        ''')
        
        patterns = {}
        for pattern_type, pattern, category in cursor.fetchall():
            if category not in patterns:
                patterns[category] = {}
            if pattern_type not in patterns[category]:
                patterns[category][pattern_type] = []
            patterns[category][pattern_type].append(pattern)
        
        return patterns
    
    def clear_cache(self) -> None:
        """РћС‡РёСЃС‚РёС‚СЊ РєСЌС€ РЅР°СЃС‚СЂРѕРµРє"""
        self._cache = {}
        debug_log("РљСЌС€ РЅР°СЃС‚СЂРѕРµРє РѕС‡РёС‰РµРЅ")

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РјРµРЅРµРґР¶РµСЂР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё
config_manager = ConfigManager()
