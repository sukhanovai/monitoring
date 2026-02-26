"""
/config/settings.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Application settings - default values
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РќР°СЃС‚СЂРѕР№РєРё РїСЂРёР»РѕР¶РµРЅРёСЏ - Р·РЅР°С‡РµРЅРёСЏ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
"""

import os
from datetime import time as dt_time
from pathlib import Path
from typing import Dict, List, Any

from lib.utils import is_proxmox_server

# Р РµР¶РёРј РѕС‚Р»Р°РґРєРё
DEBUG_MODE = False

# Р’РµСЂСЃРёСЏ РїСЂРёР»РѕР¶РµРЅРёСЏ
APP_VERSION = "8.6.0"

# === Р‘РђР—РћР’Р«Р• РџРЈРўР ===
_DEFAULT_BASE = Path(__file__).resolve().parents[1]
BASE_DIR = Path(
    os.environ.get("MONITORING_BASE_DIR", _DEFAULT_BASE)
).resolve()
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# === РќРђРЎРўР РћР™РљР Р›РћР“РР РћР’РђРќРРЇ ===
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Р¤Р°Р№Р»С‹ Р»РѕРіРѕРІ
DEBUG_LOG_FILE = LOG_DIR / "debug.log"
BOT_LOG_FILE = LOG_DIR / "bot.log"
MONITOR_LOG_FILE = LOG_DIR / "monitor.log"
BOT_DEBUG_LOG_FILE = LOG_DIR / "bot_debug.log"
MAIL_MONITOR_LOG_FILE = LOG_DIR / "mail_monitor.log"

# РџСѓС‚Рё РїРѕС‡С‚РѕРІРѕРіРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
MAILDIR_BASE = Path(os.environ.get("MONITORING_MAILDIR_BASE", "/root/Maildir")).resolve()
MAILDIR_NEW = MAILDIR_BASE / "new"
MAILDIR_CUR = MAILDIR_BASE / "cur"

# РЎРёСЃС‚РµРјРЅС‹Рµ С„Р°Р№Р»С‹
PROC_UPTIME_FILE = Path("/proc/uptime")

# === Р‘РђР—РћР’Р«Р• РќРђРЎРўР РћР™РљР ===
TELEGRAM_TOKEN = ""
CHAT_IDS: List[str] = []
TAMTAM_TOKEN = ""
TAMTAM_CHAT_IDS: List[str] = []

# === РРќРўР•Р Р’РђР›Р« РџР РћР’Р•Р РћРљ ===
CHECK_INTERVAL = 60  # СЃРµРєСѓРЅРґС‹
MAX_FAIL_TIME = 900  # СЃРµРєСѓРЅРґС‹ (15 РјРёРЅСѓС‚)

# === Р’Р Р•РњР•РќРќР«Р• РќРђРЎРўР РћР™РљР ===
SILENT_START = 20  # 20:00
SILENT_END = 9     # 09:00
DATA_COLLECTION_TIME = dt_time(8, 30)  # 08:30

# === РќРђРЎРўР РћР™РљР Р Р•РЎРЈР РЎРћР’ ===
RESOURCE_CHECK_INTERVAL = 1800  # СЃРµРєСѓРЅРґС‹ (30 РјРёРЅСѓС‚)
RESOURCE_ALERT_INTERVAL = 1800  # СЃРµРєСѓРЅРґС‹ (30 РјРёРЅСѓС‚)

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

# === РђРЈРўР•РќРўРР¤РРљРђР¦РРЇ ===
SSH_KEY_PATH = "/root/.ssh/id_rsa"
SSH_USERNAME = "root"

# === РљРћРќР¤РР“РЈР РђР¦РРЇ РЎР•Р Р’Р•Р РћР’ ===
SERVER_CONFIG = {
    "windows_servers": {},  # Р·Р°РїРѕР»РЅСЏРµС‚СЃСЏ РёР· Р‘Р”
    "linux_servers": {},    # Р·Р°РїРѕР»РЅСЏРµС‚СЃСЏ РёР· Р‘Р”
    "ping_servers": {}      # Р·Р°РїРѕР»РЅСЏРµС‚СЃСЏ РёР· Р‘Р”
}

# РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ Windows РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
WINDOWS_CREDENTIALS = [
    # {"username": "user", "password": "pass"},
]

# РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Windows СЃРµСЂРІРµСЂРѕРІ
WINDOWS_SERVER_CREDENTIALS = {
    "windows_2025": {
        "servers": ["192.0.2.10", "192.0.2.11"],
        "credentials": WINDOWS_CREDENTIALS
    },
    "domain_servers": {
        "servers": ["192.0.2.20"],
        "credentials": WINDOWS_CREDENTIALS
    },
    "admin_servers": {
        "servers": ["192.0.2.30"],
        "credentials": WINDOWS_CREDENTIALS
    },
    "standard_windows": {
        "servers": ["192.0.2.40", "192.0.2.41"],
        "credentials": WINDOWS_CREDENTIALS
    }
}

# РћР±СЂР°С‚РЅР°СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ
WINRM_CONFIGS = WINDOWS_CREDENTIALS

# === РЈРќРР¤РР¦РР РћР’РђРќРќР«Р• РўРђР™РњРђРЈРўР« ===
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

# === Р’Р•Р‘-РРќРўР•Р Р¤Р•Р™РЎ ===
WEB_PORT = 5000
WEB_HOST = '0.0.0.0'
MONITOR_SERVER_IP = "192.0.2.1"

# === Р¤РђР™Р›Р« Р”РђРќРќР«РҐ ===
STATS_FILE = DATA_DIR / "monitoring_stats.json"
BACKUP_DB_FILE = DATA_DIR / "backups.db"
SETTINGS_DB_FILE = DATA_DIR / "settings.db"
DEBUG_CONFIG_FILE = DATA_DIR / "debug_config.json"
EXTENSIONS_CONFIG_FILE = DATA_DIR / "extensions" / "extensions_config.json"

# === РљРћРќР¤РР“РЈР РђР¦РРЇ Р‘Р­РљРђРџРћР’ ===
PROXMOX_HOSTS: Dict[str, Any] = {}
DUPLICATE_IP_HOSTS: Dict[str, List[str]] = {}
HOSTNAME_ALIASES: Dict[str, List[str]] = {}
BACKUP_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "mail": {
        "subject": [
            r"^\s*Р±СЌРєР°Рї\s+zimbra\s*-\s*"
            r"(?P<size>\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?)\s+"
            r"(?P<path>/\S+)\s*$"
        ]
    },
    "stock_load": {
        "subject": [
            r"^Р›РѕРіРё\s+Р·Р°РіСЂСѓР·РєРё\s+С„Р°Р№Р»РѕРІ\s+РІ\s+СЂР°Р±РѕС‡СѓСЋ\s+Р±Р°Р·Сѓ(?:\s+\d{2}:\d{2}:\d{2,3})?$"
        ],
        "attachment": [
            r"LogiLogistam\.txt$"
        ],
        "file_entry": [
            (
                r"^\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}:\s+"
                r"(?P<supplier>.+?)\s{2,}(?P<path>(?:[A-Za-z]:\\|\\\\[^\\]+\\).+)$"
            )
        ],
        "success": [
            r"\*{3}РћСЃС‚Р°С‚РєРё Р·Р°РіСЂСѓР¶РµРЅС‹!\*{3}\s+СЃС‚СЂРѕРє\s+(?P<rows>\d+)"
        ],
        "sources": [
            {
                "name": "РћСЃРЅРѕРІРЅРѕРµ РїСЂРµРґРїСЂРёСЏС‚РёРµ",
                "subject": [
                    r"^Р›РѕРіРё\s+Р·Р°РіСЂСѓР·РєРё\s+С„Р°Р№Р»РѕРІ\s+РІ\s+СЂР°Р±РѕС‡СѓСЋ\s+Р±Р°Р·Сѓ(?:\s+\d{2}:\d{2}:\d{2,3})?$"
                ],
            },
            {
                "name": "Р‘Р°СЂРЅР°СѓР»",
                "subject": [
                    r"^Р›РѕРіРё\s+Р·Р°РіСЂСѓР·РєРё\s+С„Р°Р№Р»РѕРІ\s+РІ\s+СЂР°Р±РѕС‡СѓСЋ\s+Р±Р°Р·Сѓ\s+\(Р‘Р°СЂРЅР°СѓР»\)(?:\s+\d{2}:\d{2}:\d{2,3})?$"
                ],
            }
        ],
        "ignore": [
            r"Р’РЅРёРјР°РЅРёРµ!\s*РћС€РёР±РєР°.*СЃС‚СЂРѕРєР° С„Р°Р№Р»Р° =\s*\d+"
        ],
        "failure": [
            r"---\s*РЅРµСѓРґР°С‡Р°!!!.*",
            r"Р’РЅРёРјР°РЅРёРµ!\s*РћС€РёР±РєР°.*",
            r"РћС€РёР±РєР°.*"
        ]
    }
}
ZFS_SERVERS: Dict[str, Dict[str, Any]] = {}
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

# РћР±СЂР°С‚РЅР°СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ
BACKUP_DATABASE_CONFIG = {
    "backups_db": BACKUP_DB_FILE,
    "max_backup_age_days": 90
}

DATABASE_BACKUP_CONFIG = DATABASE_CONFIG

# === РЈРўРР›РРўР« РљРћРќР¤РР“РЈР РђР¦РР ===

def get_windows_servers_by_type(server_type: str) -> List[str]:
    """
    РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂС‹ Windows РїРѕ С‚РёРїСѓ
    
    Args:
        server_type: РўРёРї СЃРµСЂРІРµСЂР°
        
    Returns:
        РЎРїРёСЃРѕРє IP Р°РґСЂРµСЃРѕРІ
    """
    return WINDOWS_SERVER_CREDENTIALS.get(server_type, {}).get('servers', [])

def get_all_windows_servers() -> List[str]:
    """
    РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ Windows СЃРµСЂРІРµСЂС‹
    
    Returns:
        РЎРїРёСЃРѕРє РІСЃРµС… IP Р°РґСЂРµСЃРѕРІ Windows СЃРµСЂРІРµСЂРѕРІ
    """
    all_servers = []
    for config in WINDOWS_SERVER_CREDENTIALS.values():
        all_servers.extend(config.get('servers', []))
    return list(set(all_servers))

def get_server_timeout(server_type: str, default: int = 15) -> int:
    """
    РџРѕР»СѓС‡РёС‚СЊ С‚Р°Р№РјР°СѓС‚ РґР»СЏ С‚РёРїР° СЃРµСЂРІРµСЂР°
    
    Args:
        server_type: РўРёРї СЃРµСЂРІРµСЂР°
        default: РўР°Р№РјР°СѓС‚ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
        
    Returns:
        РўР°Р№РјР°СѓС‚ РІ СЃРµРєСѓРЅРґР°С…
    """
    return SERVER_TIMEOUTS.get(server_type, default)

# РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРё СЃРѕР·РґР°РµРј СЃРїРёСЃРѕРє IP РґР»СЏ РѕР±СЂР°С‚РЅРѕР№ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё
def _generate_ip_lists() -> tuple:
    """Р“РµРЅРµСЂРёСЂСѓРµС‚ СЃРїРёСЃРєРё IP РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё"""
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

# Р“Р»РѕР±Р°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ РґР»СЏ РѕР±СЂР°С‚РЅРѕР№ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё
RDP_SERVERS, SSH_SERVERS, PING_SERVERS = _generate_ip_lists()
