"""
/config/settings.py
Server Monitoring System v4.20.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Application settings - default values
Система мониторинга серверов
Версия: 4.20.5
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки приложения - значения по умолчанию
"""

import os
from datetime import time as dt_time
from pathlib import Path
from typing import Dict, List, Any

# Режим отладки
DEBUG_MODE = False

# === БАЗОВЫЕ ПУТИ ===
_DEFAULT_BASE = Path(__file__).resolve().parents[1]
BASE_DIR = Path(
    os.environ.get("MONITORING_BASE_DIR", _DEFAULT_BASE)
).resolve()
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Файлы логов
DEBUG_LOG_FILE = LOG_DIR / "debug.log"
BOT_LOG_FILE = LOG_DIR / "bot.log"
MONITOR_LOG_FILE = LOG_DIR / "monitor.log"
BOT_DEBUG_LOG_FILE = LOG_DIR / "bot_debug.log"
MAIL_MONITOR_LOG_FILE = LOG_DIR / "mail_monitor.log"

# Пути почтового мониторинга
MAILDIR_BASE = Path(os.environ.get("MONITORING_MAILDIR_BASE", "/root/Maildir")).resolve()
MAILDIR_NEW = MAILDIR_BASE / "new"
MAILDIR_CUR = MAILDIR_BASE / "cur"

# Системные файлы
PROC_UPTIME_FILE = Path("/proc/uptime")

# === БАЗОВЫЕ НАСТРОЙКИ ===
TELEGRAM_TOKEN = ""
CHAT_IDS: List[str] = []

# === ИНТЕРВАЛЫ ПРОВЕРОК ===
CHECK_INTERVAL = 60  # секунды
MAX_FAIL_TIME = 900  # секунды (15 минут)

# === ВРЕМЕННЫЕ НАСТРОЙКИ ===
SILENT_START = 20  # 20:00
SILENT_END = 9     # 09:00
DATA_COLLECTION_TIME = dt_time(8, 30)  # 08:30

# === НАСТРОЙКИ РЕСУРСОВ ===
RESOURCE_CHECK_INTERVAL = 1800  # секунды (30 минут)
RESOURCE_ALERT_INTERVAL = 1800  # секунды (30 минут)

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

# === АУТЕНТИФИКАЦИЯ ===
SSH_KEY_PATH = "/root/.ssh/id_rsa"
SSH_USERNAME = "root"

# === КОНФИГУРАЦИЯ СЕРВЕРОВ ===
SERVER_CONFIG = {
    "windows_servers": {},  # заполняется из БД
    "linux_servers": {},    # заполняется из БД
    "ping_servers": {}      # заполняется из БД
}

# Учетные данные Windows по умолчанию
WINDOWS_CREDENTIALS = [
    # {"username": "user", "password": "pass"},
]

# Конфигурация Windows серверов
WINDOWS_SERVER_CREDENTIALS = {
    "windows_2025": {
        "servers": ["192.168.20.6", "192.168.20.38", "192.168.20.47", "192.168.20.56", "192.168.20.57"],
        "credentials": WINDOWS_CREDENTIALS
    },
    "domain_servers": {
        "servers": ["192.168.20.3", "192.168.20.4"],
        "credentials": WINDOWS_CREDENTIALS
    },
    "admin_servers": {
        "servers": ["192.168.21.133"],
        "credentials": WINDOWS_CREDENTIALS
    },
    "standard_windows": {
        "servers": ["192.168.20.9", "192.168.20.26", "192.168.20.42"],
        "credentials": WINDOWS_CREDENTIALS
    }
}

# Обратная совместимость
WINRM_CONFIGS = WINDOWS_CREDENTIALS

# === УНИФИЦИРОВАННЫЕ ТАЙМАУТЫ ===
SERVER_TIMEOUTS = {
    "windows_2025": 35,
    "domain_servers": 20,
    "admin_servers": 25,
    "standard_windows": 30,
    "linux": 15,
    "ping": 10,
    "port_check": 5,
    "ssh": 15
}

# === ВЕБ-ИНТЕРФЕЙС ===
WEB_PORT = 5000
WEB_HOST = '0.0.0.0'

# === ФАЙЛЫ ДАННЫХ ===
STATS_FILE = DATA_DIR / "monitoring_stats.json"
BACKUP_DB_FILE = DATA_DIR / "backups.db"
SETTINGS_DB_FILE = DATA_DIR / "settings.db"
DEBUG_CONFIG_FILE = DATA_DIR / "debug_config.json"
EXTENSIONS_CONFIG_FILE = DATA_DIR / "extensions" / "extensions_config.json"

# === КОНФИГУРАЦИЯ БЭКАПОВ ===
PROXMOX_HOSTS: Dict[str, Any] = {}
DUPLICATE_IP_HOSTS: Dict[str, List[str]] = {}
HOSTNAME_ALIASES: Dict[str, List[str]] = {}
BACKUP_PATTERNS: Dict[str, Dict[str, List[str]]] = {}
BACKUP_STATUS_MAP = {
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
}

DATABASE_CONFIG: Dict[str, Any] = {}

# Обратная совместимость
BACKUP_DATABASE_CONFIG = {
    "backups_db": BACKUP_DB_FILE,
    "max_backup_age_days": 90
}

DATABASE_BACKUP_CONFIG = DATABASE_CONFIG

# === УТИЛИТЫ КОНФИГУРАЦИИ ===

def is_proxmox_server(ip: str) -> bool:
    """
    Проверяет, является ли сервер Proxmox
    
    Args:
        ip: IP адрес
        
    Returns:
        True если сервер Proxmox
    """
    return (ip.startswith("192.168.30.") or
            ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])

def get_windows_servers_by_type(server_type: str) -> List[str]:
    """
    Получить серверы Windows по типу
    
    Args:
        server_type: Тип сервера
        
    Returns:
        Список IP адресов
    """
    return WINDOWS_SERVER_CREDENTIALS.get(server_type, {}).get('servers', [])

def get_all_windows_servers() -> List[str]:
    """
    Получить все Windows серверы
    
    Returns:
        Список всех IP адресов Windows серверов
    """
    all_servers = []
    for config in WINDOWS_SERVER_CREDENTIALS.values():
        all_servers.extend(config.get('servers', []))
    return list(set(all_servers))

def get_server_timeout(server_type: str, default: int = 15) -> int:
    """
    Получить таймаут для типа сервера
    
    Args:
        server_type: Тип сервера
        default: Таймаут по умолчанию
        
    Returns:
        Таймаут в секундах
    """
    return SERVER_TIMEOUTS.get(server_type, default)

# Автоматически создаем список IP для обратной совместимости
def _generate_ip_lists() -> tuple:
    """Генерирует списки IP из конфигурации"""
    rdp_servers = []
    ssh_servers = []
    ping_servers = []
    
    for ip, _ in SERVER_CONFIG["windows_servers"].items():
        rdp_servers.append(ip)
    
    for ip, _ in SERVER_CONFIG["linux_servers"].items():
        ssh_servers.append(ip)
    
    for ip, _ in SERVER_CONFIG["ping_servers"].items():
        ping_servers.append(ip)
    
    return rdp_servers, ssh_servers, ping_servers

# Глобальные переменные для обратной совместимости
RDP_SERVERS, SSH_SERVERS, PING_SERVERS = _generate_ip_lists()