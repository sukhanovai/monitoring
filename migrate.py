"""
Server Monitoring System config - DATABASE VERSION
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
"""

import os
from datetime import time as dt_time

# Импортируем менеджер настроек
try:
    from settings_manager import settings_manager
    USE_DB = True
except ImportError:
    USE_DB = False
    print("⚠️ SettingsManager не доступен, используем значения по умолчанию")

def get_setting(key, default):
    """Безопасное получение настройки"""
    if USE_DB:
        return settings_manager.get_setting(key, default)
    return default

def get_json_setting(key, default):
    """Получение JSON настройки"""
    if USE_DB:
        return settings_manager.get_setting(key, default)
    return default

# === БАЗОВЫЕ НАСТРОЙКИ ===
TELEGRAM_TOKEN = get_setting('TELEGRAM_TOKEN', "")
CHAT_IDS = get_setting('CHAT_IDS', [])

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

# === УНИФИЦИРОВАННЫЕ УЧЕТНЫЕ ДАННЫЕ WINDOWS ===
def get_windows_credentials_db():
    """Получить учетные данные Windows из БД"""
    if not USE_DB:
        return {'default': []}

    try:
        return settings_manager.get_windows_credentials_db()
    except Exception as e:
        print(f"❌ Ошибка получения учетных данных из БД: {e}")
        return {'default': []}

# Базовые учетные данные для всех типов Windows серверов
WINDOWS_CREDENTIALS_DB = get_windows_credentials_db()
WINDOWS_CREDENTIALS = WINDOWS_CREDENTIALS_DB.get('default', [])

# Конфигурация Windows серверов с наследованием учетных данных
def get_windows_server_configs():
    """Получить конфигурацию Windows серверов из БД"""
    if not USE_DB:
        return {}

    try:
        configs = {}
        servers = settings_manager.get_all_servers()
        
        # Группируем серверы по типам из БД
        windows_servers = [s for s in servers if s['type'] == 'rdp']
        
        # Получаем IP из БД
        windows_2025_ips = get_setting('WINDOWS_2025_SERVERS', [])
        domain_ips = get_setting('DOMAIN_SERVERS', [])
        admin_ips = get_setting('ADMIN_SERVERS', [])
        standard_ips = get_setting('STANDARD_WINDOWS_SERVERS', [])
        
        # Фильтруем только существующие серверы
        windows_2025_servers = [ip for ip in windows_2025_ips if any(s['ip'] == ip for s in windows_servers)]
        domain_servers = [ip for ip in domain_ips if any(s['ip'] == ip for s in windows_servers)]
        admin_servers = [ip for ip in admin_ips if any(s['ip'] == ip for s in windows_servers)]
        standard_servers = [ip for ip in standard_ips if any(s['ip'] == ip for s in windows_servers)]
        
        configs["windows_2025"] = {
            "servers": windows_2025_servers,
            "credentials": WINDOWS_CREDENTIALS_DB.get('windows_2025', [])
        }
        
        configs["domain_servers"] = {
            "servers": domain_servers,
            "credentials": WINDOWS_CREDENTIALS_DB.get('domain_servers', [])
        }
        
        configs["admin_servers"] = {
            "servers": admin_servers,
            "credentials": WINDOWS_CREDENTIALS_DB.get('admin_servers', [])
        }
        
        configs["standard_windows"] = {
            "servers": standard_servers,
            "credentials": WINDOWS_CREDENTIALS_DB.get('standard_windows', [])
        }
        
        return configs
    except Exception as e:
        print(f"❌ Ошибка получения конфигурации серверов из БД: {e}")
        return {}

WINDOWS_SERVER_CONFIGS = get_windows_server_configs()

# Обратная совместимость для старого кода
WINDOWS_SERVER_CREDENTIALS = WINDOWS_SERVER_CONFIGS
WINRM_CONFIGS = WINDOWS_CREDENTIALS

# === КОНФИГУРАЦИЯ СЕРВЕРОВ ===
def get_servers_config():
    """Получить конфигурацию серверов из БД"""
    if not USE_DB:
        return {"windows_servers": {}, "linux_servers": {}, "ping_servers": {}}

    try:
        servers = settings_manager.get_all_servers()

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
        print(f"❌ Ошибка получения серверов из БД: {e}")
        return {"windows_servers": {}, "linux_servers": {}, "ping_servers": {}}

SERVER_CONFIG = get_servers_config()

# Автоматическая генерация списков IP для обратной совместимости
RDP_SERVERS = list(SERVER_CONFIG["windows_servers"].keys())
SSH_SERVERS = list(SERVER_CONFIG["linux_servers"].keys())
PING_SERVERS = list(SERVER_CONFIG["ping_servers"].keys())

# === УНИФИЦИРОВАННЫЕ ТАЙМАУТЫ ===
SERVER_TIMEOUTS = {
    "windows_2025": get_setting('WINDOWS_2025_TIMEOUT', 35),
    "domain_servers": get_setting('DOMAIN_SERVERS_TIMEOUT', 20),
    "admin_servers": get_setting('ADMIN_SERVERS_TIMEOUT', 25),
    "standard_windows": get_setting('STANDARD_WINDOWS_TIMEOUT', 30),
    "linux": get_setting('LINUX_TIMEOUT', 15),
    "ping": get_setting('PING_TIMEOUT', 10),
    "port_check": get_setting('PORT_CHECK_TIMEOUT', 5),
    "ssh": get_setting('SSH_TIMEOUT', 15)
}

# === ВЕБ-ИНТЕРФЕЙС ===
WEB_PORT = get_setting('WEB_PORT', 5000)
WEB_HOST = get_setting('WEB_HOST', '0.0.0.0')

# === ФАЙЛЫ ДАННЫХ ===
DATA_DIR = get_setting('DATA_DIR', "/opt/monitoring/data")
STATS_FILE = get_setting('STATS_FILE', os.path.join(DATA_DIR, "monitoring_stats.json"))
BACKUP_DB_FILE = get_setting('BACKUP_DB_FILE', os.path.join(DATA_DIR, "backups.db"))
MAX_BACKUP_AGE_DAYS = get_setting('MAX_BACKUP_AGE_DAYS', 90)

# === КОНФИГУРАЦИЯ БЭКАПОВ ===
PROXMOX_HOSTS = get_json_setting('PROXMOX_HOSTS', {})
DUPLICATE_IP_HOSTS = get_json_setting('DUPLICATE_IP_HOSTS', {})
HOSTNAME_ALIASES = get_json_setting('HOSTNAME_ALIASES', {})
BACKUP_PATTERNS = get_json_setting('BACKUP_PATTERNS', {})
BACKUP_STATUS_MAP = get_json_setting('BACKUP_STATUS_MAP', {})
DATABASE_CONFIG = get_json_setting('DATABASE_CONFIG', {})

# Обратная совместимость для старого кода
BACKUP_DATABASE_CONFIG = {
    "company_databases": DATABASE_CONFIG.get("company", {}),
    "barnaul_backups": DATABASE_CONFIG.get("barnaul", {}),
    "client_databases": DATABASE_CONFIG.get("client", {}),
    "yandex_backups": DATABASE_CONFIG.get("yandex", {}),
    "backups_db": BACKUP_DB_FILE,
    "max_backup_age_days": MAX_BACKUP_AGE_DAYS
}

DATABASE_BACKUP_CONFIG = DATABASE_CONFIG

# Создаем директорию для данных
os.makedirs(DATA_DIR, exist_ok=True)

# === УТИЛИТЫ КОНФИГУРАЦИИ ===

def get_windows_servers_by_type(server_type):
    """Получить серверы Windows по типу"""
    return WINDOWS_SERVER_CONFIGS.get(server_type, {}).get('servers', [])

def get_all_windows_servers():
    """Получить все Windows серверы"""
    all_servers = []
    for config in WINDOWS_SERVER_CONFIGS.values():
        all_servers.extend(config['servers'])
    return list(set(all_servers))

def get_server_timeout(server_type, default=15):
    """Получить таймаут для типа сервера"""
    return SERVER_TIMEOUTS.get(server_type, default)

def is_proxmox_server(ip):
    """Проверяет, является ли сервер Proxmox"""
    proxmox_networks = get_setting('PROXMOX_NETWORKS', [])
    return any(ip.startswith(network) if network.endswith('.') else ip == network 
               for network in proxmox_networks)

# === ИНИЦИАЛИЗАЦИЯ ===
if USE_DB:
    print("✅ Config загружает настройки из базы данных")
else:
    print("⚠️ Config использует значения по умолчанию (база данных недоступна)")