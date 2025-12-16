"""
Server Monitoring System v4.10.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Configuration package
Система мониторинга серверов
Версия: 4.10.0
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет конфигурации
"""

from .settings import *
from .db_settings import *

__all__ = [
    # Из settings.py
    'BASE_DIR', 'DATA_DIR', 'LOG_DIR',
    'TELEGRAM_TOKEN', 'CHAT_IDS',
    'CHECK_INTERVAL', 'MAX_FAIL_TIME',
    'SILENT_START', 'SILENT_END', 'DATA_COLLECTION_TIME',
    'RESOURCE_CHECK_INTERVAL', 'RESOURCE_ALERT_INTERVAL',
    'RESOURCE_THRESHOLDS', 'RESOURCE_ALERT_THRESHOLDS',
    'SSH_KEY_PATH', 'SSH_USERNAME',
    'SERVER_CONFIG',
    'WINDOWS_CREDENTIALS', 'WINDOWS_SERVER_CREDENTIALS', 'WINRM_CONFIGS',
    'SERVER_TIMEOUTS',
    'WEB_PORT', 'WEB_HOST',
    'STATS_FILE', 'BACKUP_DB_FILE', 'SETTINGS_DB_FILE',
    'DEBUG_CONFIG_FILE', 'EXTENSIONS_CONFIG_FILE',
    'PROXMOX_HOSTS', 'DUPLICATE_IP_HOSTS', 'HOSTNAME_ALIASES',
    'BACKUP_PATTERNS', 'BACKUP_STATUS_MAP', 'DATABASE_CONFIG',
    'BACKUP_DATABASE_CONFIG', 'DATABASE_BACKUP_CONFIG',
    'is_proxmox_server', 'get_windows_servers_by_type',
    'get_all_windows_servers', 'get_server_timeout',
    'RDP_SERVERS', 'SSH_SERVERS', 'PING_SERVERS',
    
    # Из db_settings.py
    'get_setting', 'get_json_setting',
    'get_windows_credentials_db', 'get_windows_server_configs',
    'get_servers_config', 'load_all_settings',
    'USE_DB',
]