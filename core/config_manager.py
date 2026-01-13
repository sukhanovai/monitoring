"""
/core/config_manager.py
Server Monitoring System v7.1.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Configuration Manager
Система мониторинга серверов
Версия: 7.1.0
Автор: Александр Суханов (c)
Лицензия: MIT
Менеджер конфигурации
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

# Логгер для этого модуля
_logger = setup_logging("config")

class ConfigManager:
    """Менеджер конфигурации с поддержкой базы данных"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Инициализация менеджера конфигурации
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = Path(db_path) if db_path else DATA_DIR / "settings.db"
        self._cache = {}
        self._local = threading.local()
        self._connection = None
        self.init_database()
        debug_log(f"Менеджер конфигурации инициализирован: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД (отдельное соединение на поток)"""
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=30)
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        return conn

    def close_connection(self) -> None:
        """Закрыть соединение с БД (для текущего потока)"""
        conn = getattr(self._local, "connection", None)
        if conn:
            conn.close()
            self._local.connection = None

    def init_database(self) -> None:
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
                type TEXT CHECK(type IN ('rdp', 'ssh', 'ping')),
                credentials TEXT,
                timeout INTEGER DEFAULT 30,
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
        
        # Таблица категорий баз данных
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS database_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица баз данных
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
        debug_log("База данных настроек инициализирована")
    
    def init_default_settings(self) -> None:
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
            ('ZFS_SERVERS', '{}', 'backup', 'Список ZFS серверов и массивов', 'dict'),
            
            # Веб-интерфейс
            ('WEB_PORT', '5000', 'web', 'Порт веб-интерфейса', 'int'),
            ('WEB_HOST', '0.0.0.0', 'web', 'Хост веб-интерфейса', 'string'),
            
            # Отладка
            ('DEBUG_MODE', 'False', 'debug', 'Режим отладки', 'bool'),
            ('LOG_LEVEL', 'INFO', 'debug', 'Уровень логирования', 'string'),
            
            # Таймауты серверов
            ('SERVER_TIMEOUTS', '{}', 'timeouts', 'Таймауты серверов по типам', 'dict'),
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value, category, description, data_type in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value, category, description, data_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, category, description, data_type))
        
        conn.commit()
        debug_log(f"Загружено {len(default_settings)} настроек по умолчанию")
    
    def get_setting(
        self, 
        key: str, 
        default: Any = None,
        use_cache: bool = True
    ) -> Any:
        """
        Получить значение настройки
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            use_cache: Использовать кэш
            
        Returns:
            Значение настройки
        """
        if use_cache and key in self._cache:
            return self._cache[key]
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT value, data_type FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
        except Exception as e:
            error_log(f"Ошибка чтения настройки {key}: {e}")
            self._cache[key] = default
            return default
                
        if not result:
            self._cache[key] = default
            return default
        
        value_str, data_type = result
        
        # Преобразование типов
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
            error_log(f"Ошибка преобразования настройки {key}: {e}, значение: {value_str}")
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
        Установить значение настройки
        
        Args:
            key: Ключ настройки
            value: Значение
            category: Категория
            description: Описание
            data_type: Тип данных (auto/int/float/bool/list/dict/string/time)
            
        Returns:
            True если успешно
        """
        # Определяем тип данных если auto
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
            
            # Обновляем кэш
            self._cache[key] = value
            
            debug_log(f"Настройка обновлена: {key} = {value_str[:50]}{'...' if len(value_str) > 50 else ''}")
            return True
            
        except Exception as e:
            error_log(f"Ошибка сохранения настройки {key}: {e}")
            return False
    
    def get_all_settings(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить все настройки
        
        Args:
            category: Фильтр по категории
            
        Returns:
            Словарь всех настроек
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
                error_log(f"Ошибка преобразования настройки {key}: {e}")
                settings[key] = None
        
        return settings
    
    def get_categories(self) -> List[str]:
        """
        Получить список категорий настроек
        
        Returns:
            Список категорий
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT category FROM settings ORDER BY category')
        categories = [row[0] for row in cursor.fetchall()]
        
        return categories
    
    def get_servers_by_type(self, server_type: str) -> List[Dict[str, Any]]:
        """
        Получить серверы по типу
        
        Args:
            server_type: Тип сервера (rdp, ssh, ping)
            
        Returns:
            Список серверов
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
        Получить список серверов

        Args:
            include_disabled: Включать выключенные серверы

        Returns:
            Список серверов
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
        Включить или выключить мониторинг сервера

        Args:
            ip: IP адрес сервера
            enabled: Новый статус

        Returns:
            True если успешно
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

            debug_log(f"Сервер {ip} {'включен' if enabled else 'приостановлен'}")
            return cursor.rowcount > 0

        except Exception as e:
            error_log(f"Ошибка изменения статуса сервера {ip}: {e}")
            return False

    def get_server_enabled(self, ip: str) -> bool:
        """
        Проверить статус мониторинга сервера

        Args:
            ip: IP адрес сервера

        Returns:
            True если сервер активен
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
            error_log(f"Ошибка получения статуса сервера {ip}: {e}")
            return True


    # ------------------------------------------------------------
    # Backward-compatible API (тонкий адаптер)
    # ------------------------------------------------------------
    def get_servers(self) -> List[Dict[str, Any]]:
        """
        Backward-compatible alias.
        Старый код ожидает ConfigManager.get_servers(), поэтому оставляем.
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
        Добавить сервер
        
        Args:
            ip: IP адрес
            name: Имя сервера
            server_type: Тип сервера
            credentials: Учетные данные
            timeout: Таймаут
            
        Returns:
            True если успешно
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
            
            # Очищаем кэш
            self._cache = {}
            
            debug_log(f"Сервер добавлен: {name} ({ip}) тип: {server_type}")
            return True
            
        except Exception as e:
            error_log(f"Ошибка добавления сервера {ip}: {e}")
            return False
    
    def delete_server(self, ip: str) -> bool:
        """
        Удалить сервер
        
        Args:
            ip: IP адрес сервера
            
        Returns:
            True если успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM servers WHERE ip = ?', (ip,))
            conn.commit()
            
            # Очищаем кэш
            self._cache = {}
            
            debug_log(f"Сервер удален: {ip}")
            return True
            
        except Exception as e:
            error_log(f"Ошибка удаления сервера {ip}: {e}")
            return False
    
    def get_windows_credentials_db(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Получить учетные данные Windows из БД
        
        Returns:
            Словарь учетных данных по типам серверов
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
        Получить учетные данные Windows
        
        Args:
            server_type: Фильтр по типу сервера
            
        Returns:
            Список учетных данных
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
        Получить список типов Windows-серверов из базы

        Returns:
            Список уникальных типов серверов
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
        Добавить учетные данные Windows
        
        Args:
            username: Имя пользователя
            password: Пароль
            server_type: Тип сервера
            priority: Приоритет
            
        Returns:
            True если успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO windows_credentials (username, password, server_type, priority)
                VALUES (?, ?, ?, ?)
            ''', (username, password, server_type, priority))
            
            conn.commit()
            
            debug_log(f"Учетные данные добавлены: {username} для {server_type}")
            return True
            
        except Exception as e:
            error_log(f"Ошибка добавления учетных данных: {e}")
            return False
    
    def update_windows_credential(
        self, 
        cred_id: int, 
        **kwargs
    ) -> bool:
        """
        Обновить учетные данные Windows
        
        Args:
            cred_id: ID учетных данных
            **kwargs: Поля для обновления
            
        Returns:
            True если успешно
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
            
            debug_log(f"Учетные данные обновлены: ID {cred_id}")
            return True
            
        except Exception as e:
            error_log(f"Ошибка обновления учетных данных ID {cred_id}: {e}")
            return False
    
    def delete_windows_credential(self, cred_id: int) -> bool:
        """
        Удалить учетные данные Windows
        
        Args:
            cred_id: ID учетных данных
            
        Returns:
            True если успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM windows_credentials WHERE id = ?', (cred_id,))
            conn.commit()
            
            debug_log(f"Учетные данные удалены: ID {cred_id}")
            return True
            
        except Exception as e:
            error_log(f"Ошибка удаления учетных данных ID {cred_id}: {e}")
            return False
    
    def get_backup_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Получить паттерны бэкапов
        
        Returns:
            Словарь паттернов
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
        """Очистить кэш настроек"""
        self._cache = {}
        debug_log("Кэш настроек очищен")

# Глобальный экземпляр менеджера конфигурации
config_manager = ConfigManager()
