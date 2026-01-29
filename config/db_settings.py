"""
/config/db_settings.py
Server Monitoring System v8.3.23
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database-backed settings loader
Система мониторинга серверов
Версия: 8.3.23
Автор: Александр Суханов (c)
Лицензия: MIT
Загрузчик настроек из базы данных
"""

from datetime import time as dt_time
from typing import Dict, List, Any, Optional
from lib.logging import debug_log, error_log, setup_logging
from core.config_manager import config_manager
from config import settings as defaults
from config.settings import *

# Логгер для этого модуля
_logger = setup_logging("db_settings")

# Флаг использования БД
USE_DB = True

def get_setting(key: str, default: Any = None) -> Any:
    """
    Безопасное получение настройки из БД
    
    Args:
        key: Ключ настройки
        default: Значение по умолчанию
        
    Returns:
        Значение настройки
    """
    if USE_DB:
        try:
            return config_manager.get_setting(key, default)
        except Exception as e:
            error_log(f"Ошибка получения настройки {key} из БД: {e}")
            return default
    return default

def get_json_setting(key: str, default: Any = None) -> Any:
    """
    Получение JSON настройки из БД
    
    Args:
        key: Ключ настройки
        default: Значение по умолчанию
        
    Returns:
        Значение настройки
    """
    if USE_DB:
        try:
            return config_manager.get_setting(key, default)
        except Exception as e:
            error_log(f"Ошибка получения JSON настройки {key}: {e}")
            return default
    return default

def get_windows_credentials_db() -> Dict[str, List[Dict[str, str]]]:
    """
    Получить учетные данные Windows из БД
    
    Returns:
        Словарь учетных данных по типам серверов
    """
    if not USE_DB:
        return {'default': []}
    
    try:
        return config_manager.get_windows_credentials_db()
    except Exception as e:
        error_log(f"Ошибка получения учетных данных из БД: {e}")
        return {'default': []}

def get_windows_server_configs() -> Dict[str, Dict[str, Any]]:
    """
    Получить конфигурацию Windows серверов из БД
    
    Returns:
        Конфигурация Windows серверов
    """
    if not USE_DB:
        return {}
    
    try:
        configs = {}
        servers = config_manager.get_all_servers()
        
        # Группируем серверы по типам
        windows_servers = [s for s in servers if s['type'] == 'rdp']
        
        # Получаем учетные данные из БД
        credentials_db = get_windows_credentials_db()
        
        default_groups = {
            group: config.get("servers", [])
            for group, config in defaults.WINDOWS_SERVER_CREDENTIALS.items()
        }
        server_groups = get_json_setting('WINDOWS_SERVER_GROUPS', default_groups)

        # windows_2025 серверы
        win2025_ips = [
            s['ip'] for s in windows_servers
            if s['ip'] in server_groups.get("windows_2025", [])
        ]
        configs["windows_2025"] = {
            "servers": win2025_ips,
            "credentials": credentials_db.get('windows_2025', [])
        }

        # domain серверы
        domain_ips = [
            s['ip'] for s in windows_servers
            if s['ip'] in server_groups.get("domain_servers", [])
        ]
        configs["domain_servers"] = {
            "servers": domain_ips,
            "credentials": credentials_db.get('domain_servers', [])
        }

        # admin серверы
        admin_ips = [
            s['ip'] for s in windows_servers
            if s['ip'] in server_groups.get("admin_servers", [])
        ]
        configs["admin_servers"] = {
            "servers": admin_ips,
            "credentials": credentials_db.get('admin_servers', [])
        }

        # standard windows серверы
        standard_ips = [
            s['ip'] for s in windows_servers
            if s['ip'] in server_groups.get("standard_windows", [])
        ]
        configs["standard_windows"] = {
            "servers": standard_ips,
            "credentials": credentials_db.get('standard_windows', [])
        }

        return configs
        
    except Exception as e:
        error_log(f"Ошибка получения конфигурации серверов из БД: {e}")
        return {}

def get_servers_config() -> Dict[str, Dict[str, str]]:
    """
    Получить конфигурацию серверов из БД
    
    Returns:
        Конфигурация серверов
    """
    if not USE_DB:
        return {"windows_servers": {}, "linux_servers": {}, "ping_servers": {}}
    
    try:
        servers = config_manager.get_all_servers()
        
        config = {
            "windows_servers": {},
            "linux_servers": {},
            "ping_servers": {}
        }

        for server in servers:
            ip = server['ip']
            name = server['name']
            server_type = server['type']

            if server_type == 'rdp':
                config["windows_servers"][ip] = name
            elif server_type == 'ssh':
                config["linux_servers"][ip] = name
            elif server_type == 'ping':
                config["ping_servers"][ip] = name

        return config
        
    except Exception as e:
        error_log(f"Ошибка получения серверов из БД: {e}")
        return {"windows_servers": {}, "linux_servers": {}, "ping_servers": {}}

def load_all_settings() -> None:
    """
    Загрузить все настройки из БД в глобальные переменные
    
    Эта функция должна вызываться при инициализации приложения
    """
    global USE_DB, TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL, MAX_FAIL_TIME
    global SILENT_START, SILENT_END, DATA_COLLECTION_TIME
    global RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_INTERVAL
    global RESOURCE_THRESHOLDS, RESOURCE_ALERT_THRESHOLDS
    global SSH_KEY_PATH, SSH_USERNAME, SERVER_CONFIG
    global WINDOWS_SERVER_CONFIGS, WINDOWS_SERVER_CREDENTIALS, WINRM_CONFIGS
    global SERVER_TIMEOUTS, WEB_PORT, WEB_HOST, MONITOR_SERVER_IP
    global RDP_SERVERS, SSH_SERVERS, PING_SERVERS
    global PROXMOX_HOSTS, DUPLICATE_IP_HOSTS, HOSTNAME_ALIASES
    global BACKUP_PATTERNS, BACKUP_STATUS_MAP, DATABASE_CONFIG, ZFS_SERVERS
    global BACKUP_DATABASE_CONFIG, DATABASE_BACKUP_CONFIG
    
    if not USE_DB:
        debug_log("⚠️ Используются настройки по умолчанию (БД недоступна)")
        return
    
    try:
        # === БАЗОВЫЕ НАСТРОЙКИ ===
        TELEGRAM_TOKEN = get_setting('TELEGRAM_TOKEN', defaults.TELEGRAM_TOKEN)
        CHAT_IDS = get_setting('CHAT_IDS', defaults.CHAT_IDS)

        # === ИНТЕРВАЛЫ ПРОВЕРОК ===
        CHECK_INTERVAL = get_setting('CHECK_INTERVAL', defaults.CHECK_INTERVAL)
        MAX_FAIL_TIME = get_setting('MAX_FAIL_TIME', defaults.MAX_FAIL_TIME)

        # === ВРЕМЕННЫЕ НАСТРОЙКИ ===
        SILENT_START = get_setting('SILENT_START', defaults.SILENT_START)
        SILENT_END = get_setting('SILENT_END', defaults.SILENT_END)

        default_collection_time = defaults.DATA_COLLECTION_TIME
        if isinstance(default_collection_time, dt_time):
            default_time_str = default_collection_time.strftime('%H:%M')
        else:
            default_time_str = str(default_collection_time)
        DATA_COLLECTION_TIME_STR = get_setting('DATA_COLLECTION_TIME', default_time_str)
        try:
            hours, minutes = map(int, DATA_COLLECTION_TIME_STR.split(':'))
            DATA_COLLECTION_TIME = dt_time(hours, minutes)
        except:
            DATA_COLLECTION_TIME = defaults.DATA_COLLECTION_TIME

        # === НАСТРОЙКИ РЕСУРСОВ ===
        RESOURCE_CHECK_INTERVAL = get_setting(
            'RESOURCE_CHECK_INTERVAL',
            defaults.RESOURCE_CHECK_INTERVAL,
        )
        RESOURCE_ALERT_INTERVAL = get_setting(
            'RESOURCE_ALERT_INTERVAL',
            defaults.RESOURCE_ALERT_INTERVAL,
        )

        RESOURCE_THRESHOLDS = {
            "cpu_warning": get_setting(
                'CPU_WARNING',
                defaults.RESOURCE_THRESHOLDS.get("cpu_warning", 80),
            ),
            "cpu_critical": get_setting(
                'CPU_CRITICAL',
                defaults.RESOURCE_THRESHOLDS.get("cpu_critical", 90),
            ),
            "ram_warning": get_setting(
                'RAM_WARNING',
                defaults.RESOURCE_THRESHOLDS.get("ram_warning", 85),
            ),
            "ram_critical": get_setting(
                'RAM_CRITICAL',
                defaults.RESOURCE_THRESHOLDS.get("ram_critical", 95),
            ),
            "disk_warning": get_setting(
                'DISK_WARNING',
                defaults.RESOURCE_THRESHOLDS.get("disk_warning", 80),
            ),
            "disk_critical": get_setting(
                'DISK_CRITICAL',
                defaults.RESOURCE_THRESHOLDS.get("disk_critical", 90),
            ),
        }

        RESOURCE_ALERT_THRESHOLDS = get_json_setting(
            'RESOURCE_ALERT_THRESHOLDS',
            defaults.RESOURCE_ALERT_THRESHOLDS,
        )

        # === АУТЕНТИФИКАЦИЯ ===
        SSH_KEY_PATH = get_setting('SSH_KEY_PATH', defaults.SSH_KEY_PATH)
        SSH_USERNAME = get_setting('SSH_USERNAME', defaults.SSH_USERNAME)

        # === КОНФИГУРАЦИЯ WINDOWS СЕРВЕРОВ ===
        WINDOWS_SERVER_CONFIGS = get_windows_server_configs()
        WINDOWS_SERVER_CREDENTIALS = WINDOWS_SERVER_CONFIGS
        WINRM_CONFIGS = []

        # Загружаем учетные данные из БД
        windows_creds_db = get_windows_credentials_db()
        if windows_creds_db.get('default'):
            WINRM_CONFIGS = windows_creds_db['default']

        # === КОНФИГУРАЦИЯ СЕРВЕРОВ ===
        SERVER_CONFIG = get_servers_config()

        # Автоматическая генерация списков IP для обратной совместимости
        RDP_SERVERS = list(SERVER_CONFIG["windows_servers"].keys())
        SSH_SERVERS = list(SERVER_CONFIG["linux_servers"].keys())
        PING_SERVERS = list(SERVER_CONFIG["ping_servers"].keys())

        # === УНИФИЦИРОВАННЫЕ ТАЙМАУТЫ ===
        SERVER_TIMEOUTS = get_json_setting(
            'SERVER_TIMEOUTS',
            defaults.SERVER_TIMEOUTS,
        )

        # === ВЕБ-ИНТЕРФЕЙС ===
        WEB_PORT = get_setting('WEB_PORT', defaults.WEB_PORT)
        WEB_HOST = get_setting('WEB_HOST', defaults.WEB_HOST)
        MONITOR_SERVER_IP = get_setting(
            'MONITOR_SERVER_IP',
            defaults.MONITOR_SERVER_IP,
        )

        # === КОНФИГУРАЦИЯ БЭКАПОВ ===
        PROXMOX_HOSTS = get_json_setting('PROXMOX_HOSTS', defaults.PROXMOX_HOSTS)
        DUPLICATE_IP_HOSTS = get_json_setting(
            'DUPLICATE_IP_HOSTS',
            defaults.DUPLICATE_IP_HOSTS,
        )
        HOSTNAME_ALIASES = get_json_setting(
            'HOSTNAME_ALIASES',
            defaults.HOSTNAME_ALIASES,
        )
        BACKUP_PATTERNS = get_json_setting('BACKUP_PATTERNS', defaults.BACKUP_PATTERNS)
        ZFS_SERVERS = get_json_setting('ZFS_SERVERS', defaults.ZFS_SERVERS)
        BACKUP_STATUS_MAP = get_json_setting(
            'BACKUP_STATUS_MAP',
            defaults.BACKUP_STATUS_MAP,
        )
        DATABASE_CONFIG = get_json_setting('DATABASE_CONFIG', defaults.DATABASE_CONFIG)

        # Обратная совместимость для старого кода
        BACKUP_DATABASE_CONFIG = {
            'backups_db': BACKUP_DB_FILE,
            'max_backup_age_days': 90
        }

        DATABASE_BACKUP_CONFIG = DATABASE_CONFIG
        
        debug_log("✅ Настройки успешно загружены из базы данных")
        
    except Exception as e:
        error_log(f"❌ Ошибка загрузки настроек из БД: {e}")
        debug_log("⚠️ Используются настройки по умолчанию")

# === ИНИЦИАЛИЗАЦИЯ ===

# Загружаем настройки при импорте модуля
load_all_settings()

if USE_DB:
    debug_log("✅ config.db_settings загружает настройки из базы данных")
else:
    debug_log("⚠️ config.db_settings использует значения по умолчанию (база данных недоступна)")

# Удаляем ошибочную строку с __all__.append('monitor')
# Вместо этого определим __all__ вверху файла
