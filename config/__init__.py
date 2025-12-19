"""
/config/__init__.py
Server Monitoring System v4.14.22
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Configuration package
Система мониторинга серверов
Версия: 4.14.22
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет конфигурации
"""

# Сначала импортируем настройки по умолчанию из settings.py
from .settings import (
    BASE_DIR, DATA_DIR, LOG_DIR,
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
    WEB_PORT, WEB_HOST,
    STATS_FILE, BACKUP_DB_FILE, SETTINGS_DB_FILE,
    DEBUG_CONFIG_FILE, EXTENSIONS_CONFIG_FILE,
    PROXMOX_HOSTS, DUPLICATE_IP_HOSTS, HOSTNAME_ALIASES,
    BACKUP_PATTERNS, BACKUP_STATUS_MAP, DATABASE_CONFIG,
    BACKUP_DATABASE_CONFIG, DATABASE_BACKUP_CONFIG,
    is_proxmox_server, get_windows_servers_by_type,
    get_all_windows_servers, get_server_timeout,
    RDP_SERVERS, SSH_SERVERS, PING_SERVERS,
    DEBUG_MODE as SETTINGS_DEBUG_MODE
)

# Затем импортируем из db_settings
from .db_settings import (
    get_setting, get_json_setting,
    get_windows_credentials_db, get_windows_server_configs,
    get_servers_config, load_all_settings,
    USE_DB,
    TELEGRAM_TOKEN as DB_TELEGRAM_TOKEN,
    CHAT_IDS as DB_CHAT_IDS,
    DEBUG_MODE as DB_DEBUG_MODE
)

# Определяем какие значения использовать
# Если USE_DB = True и значение из БД не пустое, используем из БД
# Иначе используем из settings.py

TELEGRAM_TOKEN = DB_TELEGRAM_TOKEN if USE_DB and DB_TELEGRAM_TOKEN else SETTINGS_TOKEN
CHAT_IDS = DB_CHAT_IDS if USE_DB and DB_CHAT_IDS else SETTINGS_CHAT_IDS
DEBUG_MODE = DB_DEBUG_MODE if USE_DB else SETTINGS_DEBUG_MODE

__all__ = [
    # Пути
    'BASE_DIR', 'DATA_DIR', 'LOG_DIR',
    
    # Основные настройки (с приоритетом БД)
    'TELEGRAM_TOKEN', 'CHAT_IDS', 'DEBUG_MODE',
    
    # Интервалы проверок
    'CHECK_INTERVAL', 'MAX_FAIL_TIME',
    
    # Временные настройки
    'SILENT_START', 'SILENT_END', 'DATA_COLLECTION_TIME',
    
    # Настройки ресурсов
    'RESOURCE_CHECK_INTERVAL', 'RESOURCE_ALERT_INTERVAL',
    'RESOURCE_THRESHOLDS', 'RESOURCE_ALERT_THRESHOLDS',
    
    # Аутентификация
    'SSH_KEY_PATH', 'SSH_USERNAME',
    
    # Конфигурация серверов
    'SERVER_CONFIG',
    'WINDOWS_CREDENTIALS', 'WINDOWS_SERVER_CREDENTIALS', 'WINRM_CONFIGS',
    'SERVER_TIMEOUTS',
    
    # Веб-интерфейс
    'WEB_PORT', 'WEB_HOST',
    
    # Файлы
    'STATS_FILE', 'BACKUP_DB_FILE', 'SETTINGS_DB_FILE',
    'DEBUG_CONFIG_FILE', 'EXTENSIONS_CONFIG_FILE',
    
    # Бэкапы
    'PROXMOX_HOSTS', 'DUPLICATE_IP_HOSTS', 'HOSTNAME_ALIASES',
    'BACKUP_PATTERNS', 'BACKUP_STATUS_MAP', 'DATABASE_CONFIG',
    'BACKUP_DATABASE_CONFIG', 'DATABASE_BACKUP_CONFIG',
    
    # Функции
    'is_proxmox_server', 'get_windows_servers_by_type',
    'get_all_windows_servers', 'get_server_timeout',
    
    # Списки серверов
    'RDP_SERVERS', 'SSH_SERVERS', 'PING_SERVERS',
    
    # Функции из db_settings
    'get_setting', 'get_json_setting',
    'get_windows_credentials_db', 'get_windows_server_configs',
    'get_servers_config', 'load_all_settings',
    'USE_DB',
]