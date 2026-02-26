"""
/config/__init__.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Configuration package
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РџР°РєРµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёРё
"""

# РЎРЅР°С‡Р°Р»Р° РёРјРїРѕСЂС‚РёСЂСѓРµРј РЅР°СЃС‚СЂРѕР№РєРё РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РёР· settings.py
from .settings import (
    BASE_DIR, DATA_DIR, LOG_DIR,
    LOG_FORMAT, LOG_DATE_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT,
    DEBUG_LOG_FILE, BOT_LOG_FILE, MONITOR_LOG_FILE, BOT_DEBUG_LOG_FILE, MAIL_MONITOR_LOG_FILE,
    MAILDIR_BASE, MAILDIR_NEW, MAILDIR_CUR,
    PROC_UPTIME_FILE,    
    TELEGRAM_TOKEN as SETTINGS_TOKEN,
    CHAT_IDS as SETTINGS_CHAT_IDS,
    CHECK_INTERVAL, MAX_FAIL_TIME,
    SILENT_START, SILENT_END, DATA_COLLECTION_TIME,
    RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_INTERVAL,
    RESOURCE_THRESHOLDS, RESOURCE_ALERT_THRESHOLDS,
    SSH_KEY_PATH, SSH_USERNAME,
    SERVER_CONFIG,
    WINDOWS_CREDENTIALS, WINDOWS_SERVER_CREDENTIALS, WINRM_CONFIGS,
    SERVER_TIMEOUTS,
    WEB_PORT, WEB_HOST, MONITOR_SERVER_IP as SETTINGS_MONITOR_SERVER_IP,
    STATS_FILE, BACKUP_DB_FILE, SETTINGS_DB_FILE,
    DEBUG_CONFIG_FILE, EXTENSIONS_CONFIG_FILE,
    PROXMOX_HOSTS, DUPLICATE_IP_HOSTS, HOSTNAME_ALIASES,
    BACKUP_PATTERNS, BACKUP_STATUS_MAP, DATABASE_CONFIG, ZFS_SERVERS,
    BACKUP_DATABASE_CONFIG, DATABASE_BACKUP_CONFIG,
    is_proxmox_server, get_windows_servers_by_type,
    get_all_windows_servers, get_server_timeout,
    RDP_SERVERS, SSH_SERVERS, PING_SERVERS,
    DEBUG_MODE as SETTINGS_DEBUG_MODE
)

# Р—Р°С‚РµРј РёРјРїРѕСЂС‚РёСЂСѓРµРј РёР· db_settings
from .db_settings import (
    get_setting, get_json_setting,
    get_windows_credentials_db, get_windows_server_configs,
    get_servers_config, load_all_settings,
    USE_DB,
    TELEGRAM_TOKEN as DB_TELEGRAM_TOKEN,
    CHAT_IDS as DB_CHAT_IDS,
    DEBUG_MODE as DB_DEBUG_MODE,
    MONITOR_SERVER_IP as DB_MONITOR_SERVER_IP
)

# РћРїСЂРµРґРµР»СЏРµРј РєР°РєРёРµ Р·РЅР°С‡РµРЅРёСЏ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ
# Р•СЃР»Рё USE_DB = True Рё Р·РЅР°С‡РµРЅРёРµ РёР· Р‘Р” РЅРµ РїСѓСЃС‚РѕРµ, РёСЃРїРѕР»СЊР·СѓРµРј РёР· Р‘Р”
# РРЅР°С‡Рµ РёСЃРїРѕР»СЊР·СѓРµРј РёР· settings.py

TELEGRAM_TOKEN = DB_TELEGRAM_TOKEN if USE_DB and DB_TELEGRAM_TOKEN else SETTINGS_TOKEN
CHAT_IDS = DB_CHAT_IDS if USE_DB and DB_CHAT_IDS else SETTINGS_CHAT_IDS
DEBUG_MODE = DB_DEBUG_MODE if USE_DB else SETTINGS_DEBUG_MODE
MONITOR_SERVER_IP = (
    DB_MONITOR_SERVER_IP
    if USE_DB and DB_MONITOR_SERVER_IP
    else SETTINGS_MONITOR_SERVER_IP
)

__all__ = [
    # РџСѓС‚Рё
    'BASE_DIR', 'DATA_DIR', 'LOG_DIR',
    'LOG_FORMAT', 'LOG_DATE_FORMAT', 'LOG_MAX_BYTES', 'LOG_BACKUP_COUNT',
    'DEBUG_LOG_FILE', 'BOT_LOG_FILE', 'MONITOR_LOG_FILE', 'BOT_DEBUG_LOG_FILE',
    'MAIL_MONITOR_LOG_FILE',
    'MAILDIR_BASE', 'MAILDIR_NEW', 'MAILDIR_CUR',
    'PROC_UPTIME_FILE',
        
    # РћСЃРЅРѕРІРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё (СЃ РїСЂРёРѕСЂРёС‚РµС‚РѕРј Р‘Р”)
    'TELEGRAM_TOKEN', 'CHAT_IDS', 'DEBUG_MODE',
    
    # РРЅС‚РµСЂРІР°Р»С‹ РїСЂРѕРІРµСЂРѕРє
    'CHECK_INTERVAL', 'MAX_FAIL_TIME',
    
    # Р’СЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё
    'SILENT_START', 'SILENT_END', 'DATA_COLLECTION_TIME',
    
    # РќР°СЃС‚СЂРѕР№РєРё СЂРµСЃСѓСЂСЃРѕРІ
    'RESOURCE_CHECK_INTERVAL', 'RESOURCE_ALERT_INTERVAL',
    'RESOURCE_THRESHOLDS', 'RESOURCE_ALERT_THRESHOLDS',
    
    # РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ
    'SSH_KEY_PATH', 'SSH_USERNAME',
    
    # РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ СЃРµСЂРІРµСЂРѕРІ
    'SERVER_CONFIG',
    'WINDOWS_CREDENTIALS', 'WINDOWS_SERVER_CREDENTIALS', 'WINRM_CONFIGS',
    'SERVER_TIMEOUTS',
    
    # Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ
    'WEB_PORT', 'WEB_HOST',
    'MONITOR_SERVER_IP',
    
    # Р¤Р°Р№Р»С‹
    'STATS_FILE', 'BACKUP_DB_FILE', 'SETTINGS_DB_FILE',
    'DEBUG_CONFIG_FILE', 'EXTENSIONS_CONFIG_FILE',
    
    # Р‘СЌРєР°РїС‹
    'PROXMOX_HOSTS', 'DUPLICATE_IP_HOSTS', 'HOSTNAME_ALIASES',
    'BACKUP_PATTERNS', 'BACKUP_STATUS_MAP', 'DATABASE_CONFIG', 'ZFS_SERVERS',
    'BACKUP_DATABASE_CONFIG', 'DATABASE_BACKUP_CONFIG',
    
    # Р¤СѓРЅРєС†РёРё
    'is_proxmox_server', 'get_windows_servers_by_type',
    'get_all_windows_servers', 'get_server_timeout',
    
    # РЎРїРёСЃРєРё СЃРµСЂРІРµСЂРѕРІ
    'RDP_SERVERS', 'SSH_SERVERS', 'PING_SERVERS',
    
    # Р¤СѓРЅРєС†РёРё РёР· db_settings
    'get_setting', 'get_json_setting',
    'get_windows_credentials_db', 'get_windows_server_configs',
    'get_servers_config', 'load_all_settings',
    'USE_DB',
]
