"""
Server Monitoring System v4.11.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database-backed settings loader
Система мониторинга серверов
Версия: 4.11.4
Автор: Александр Суханов (c)
Лицензия: MIT
Загрузчик настроек из базы данных
"""

import os
from datetime import time as dt_time
from typing import Dict, List, Any, Optional
from lib.logging import debug_log, error_log, setup_logging
from core.config_manager import config_manager

# Логгер для этого модуля
_logger = setup_logging("db_settings")

# Флаг использования БД
USE_DB = True

# Импортируем базовые настройки для значений по умолчанию
try:
    from config.settings import *
except ImportError:
    # Если файл с базовыми настройками не найден, используем значения по умолчанию
    debug_log("⚠️ Файл config.settings не найден, используем значения по умолчанию")
    
    # Базовые пути
    BASE_DIR = "/opt/monitoring"
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # Базовые настройки
    TELEGRAM_TOKEN = ""
    CHAT_IDS = []
    
    # Интервалы проверок
    CHECK_INTERVAL = 60
    MAX_FAIL_TIME = 900
    
    # Временные настройки
    SILENT_START = 20
    SILENT_END = 9
    DATA_COLLECTION_TIME = dt_time(8, 30)
    
    # Настройки ресурсов
    RESOURCE_CHECK_INTERVAL = 1800
    RESOURCE_ALERT_INTERVAL = 1800
    
    RESOURCE_THRESHOLDS = {
        "cpu_warning": 80,
        "cpu_critical": 90,
        "ram_warning": 85,
        "ram_critical": 95,
        "disk_warning": 80,
        "disk_critical": 90
    }
    
    RESOURCE_ALERT_THRESHOLDS = {
        "cpu_alert": 99,
        "ram_alert": 99,
        "disk_alert": 95,
        "check_consecutive": 2
    }
    
    # Аутентификация
    SSH_KEY_PATH = "/root/.ssh/id_rsa"
    SSH_USERNAME = "root"

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
        
        # windows_2025 серверы
        win2025_ips = [
            s['ip'] for s in windows_servers 
            if s['ip'] in ["192.168.20.6", "192.168.20.38", "192.168.20.47", 
                          "192.168.20.56", "192.168.20.57"]
        ]
        configs["windows_2025"] = {
            "servers": win2025_ips,
            "credentials": credentials_db.get('windows_2025', [])
        }

        # domain серверы
        domain_ips = [
            s['ip'] for s in windows_servers 
            if s['ip'] in ["192.168.20.3", "192.168.20.4"]
        ]
        configs["domain_servers"] = {
            "servers": domain_ips,
            "credentials": credentials_db.get('domain_servers', [])
        }

        # admin серверы
        admin_ips = [
            s['ip'] for s in windows_servers 
            if s['ip'] in ["192.168.21.133"]
        ]
        configs["admin_servers"] = {
            "servers": admin_ips,
            "credentials": credentials_db.get('admin_servers', [])
        }

        # standard windows серверы
        standard_ips = [
            s['ip'] for s in windows_servers 
            if s['ip'] in ["192.168.20.9", "192.168.20.26", "192.168.20.42"]
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
    global SERVER_TIMEOUTS, WEB_PORT, WEB_HOST
    global RDP_SERVERS, SSH_SERVERS, PING_SERVERS
    global PROXMOX_HOSTS, DUPLICATE_IP_HOSTS, HOSTNAME_ALIASES
    global BACKUP_PATTERNS, BACKUP_STATUS_MAP, DATABASE_CONFIG
    global BACKUP_DATABASE_CONFIG, DATABASE_BACKUP_CONFIG
    global DEBUG_MODE
    
    if not USE_DB:
        debug_log("⚠️ Используются настройки по умолчанию (БД недоступна)")
        return
    
    try:
        # === БАЗОВЫЕ НАСТРОЙКИ ===
        TELEGRAM_TOKEN = get_setting('TELEGRAM_TOKEN', "")
        CHAT_IDS = get_setting('CHAT_IDS', [])
        DEBUG_MODE = True

        debug_log(f"🔍 ДИАГНОСТИКА: TELEGRAM_TOKEN из БД: {TELEGRAM_TOKEN[:10]}...")
        debug_log(f"🔍 ДИАГНОСТИКА: CHAT_IDS из БД: {CHAT_IDS}")
        debug_log(f"🔍 ДИАГНОСТИКА: DEBUG_MODE: {DEBUG_MODE}")        

        # === ИНТЕРВАЛЫ ПРОВЕРОК ===
        CHECK_INTERVAL = get_setting('CHECK_INTERVAL', 60)
        MAX_FAIL_TIME = get_setting('MAX_FAIL_TIME', 900)

        # === ВРЕМЕННЫЕ НАСТРОЙКИ ===
        SILENT_START = get_setting('SILENT_START', 20)
        SILENT_END = get_setting('SILENT_END', 9)

        DATA_COLLECTION_TIME_STR = get_setting('DATA_COLLECTION_TIME', '08:30')
        try:
            hours, minutes = map(int, DATA_COLLECTION_TIME_STR.split(':'))
            DATA_COLLECTION_TIME = dt_time(hours, minutes)
        except:
            DATA_COLLECTION_TIME = dt_time(8, 30)

        # === НАСТРОЙКИ РЕСУРСОВ ===
        RESOURCE_CHECK_INTERVAL = get_setting('RESOURCE_CHECK_INTERVAL', 1800)
        RESOURCE_ALERT_INTERVAL = get_setting('RESOURCE_ALERT_INTERVAL', 1800)

        RESOURCE_THRESHOLDS = {
            "cpu_warning": get_setting('CPU_WARNING', 80),
            "cpu_critical": get_setting('CPU_CRITICAL', 90),
            "ram_warning": get_setting('RAM_WARNING', 85),
            "ram_critical": get_setting('RAM_CRITICAL', 95),
            "disk_warning": get_setting('DISK_WARNING', 80),
            "disk_critical": get_setting('DISK_CRITICAL', 90)
        }

        RESOURCE_ALERT_THRESHOLDS = get_json_setting('RESOURCE_ALERT_THRESHOLDS', {
            "cpu_alert": 99,
            "ram_alert": 99,
            "disk_alert": 95,
            "check_consecutive": 2
        })

        # === АУТЕНТИФИКАЦИЯ ===
        SSH_KEY_PATH = get_setting('SSH_KEY_PATH', "/root/.ssh/id_rsa")
        SSH_USERNAME = get_setting('SSH_USERNAME', "root")

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
        SERVER_TIMEOUTS = get_json_setting('SERVER_TIMEOUTS', {
            "windows_2025": 35,
            "domain_servers": 20,
            "admin_servers": 25,
            "standard_windows": 30,
            "linux": 15,
            "ping": 10,
            "port_check": 5,
            "ssh": 15
        })

        # === ВЕБ-ИНТЕРФЕЙС ===
        WEB_PORT = get_setting('WEB_PORT', 5000)
        WEB_HOST = get_setting('WEB_HOST', '0.0.0.0')

        # === КОНФИГУРАЦИЯ БЭКАПОВ ===
        PROXMOX_HOSTS = get_json_setting('PROXMOX_HOSTS', {})
        DUPLICATE_IP_HOSTS = get_json_setting('DUPLICATE_IP_HOSTS', {})
        HOSTNAME_ALIASES = get_json_setting('HOSTNAME_ALIASES', {})
        BACKUP_PATTERNS = get_json_setting('BACKUP_PATTERNS', {})
        BACKUP_STATUS_MAP = get_json_setting('BACKUP_STATUS_MAP', {})
        DATABASE_CONFIG = get_json_setting('DATABASE_CONFIG', {})

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