"""
/config/__init__.py
Server Monitoring System v8.62.76
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Configuration package
Система мониторинга серверов
Версия: 8.62.76
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет конфигурации
"""

# Сначала импортируем настройки по умолчанию из settings.py
# Затем импортируем из db_settings
from .db_settings import (
    CHAT_IDS as DB_CHAT_IDS,
    DEBUG_MODE as DB_DEBUG_MODE,
    MONITOR_SERVER_IP as DB_MONITOR_SERVER_IP,
    TELEGRAM_TOKEN as DB_TELEGRAM_TOKEN,
    USE_DB,
    get_json_setting,
    get_servers_config,
    get_setting,
    get_windows_credentials_db,
    get_windows_server_configs,
    load_all_settings,
)
from .settings import (
    APP_VERSION,
    BACKUP_DATABASE_CONFIG,
    BACKUP_DB_FILE,
    BACKUP_PATTERNS,
    BACKUP_STATUS_MAP,
    BASE_DIR,
    BOT_DEBUG_LOG_FILE,
    BOT_LOG_FILE,
    CHAT_IDS as SETTINGS_CHAT_IDS,
    CHECK_INTERVAL,
    DATA_COLLECTION_TIME,
    DATA_DIR,
    DATABASE_BACKUP_CONFIG,
    DATABASE_CONFIG,
    DEBUG_CONFIG_FILE,
    DEBUG_LOG_FILE,
    DEBUG_MODE as SETTINGS_DEBUG_MODE,
    DUPLICATE_IP_HOSTS,
    EXTENSIONS_CONFIG_FILE,
    HOSTNAME_ALIASES,
    LOG_BACKUP_COUNT,
    LOG_DATE_FORMAT,
    LOG_DIR,
    LOG_FORMAT,
    LOG_MAX_BYTES,
    MAIL_MONITOR_LOG_FILE,
    MAILDIR_BASE,
    MAILDIR_CUR,
    MAILDIR_NEW,
    MAX_FAIL_TIME,
    MONITOR_LOG_FILE,
    MONITOR_SERVER_IP as SETTINGS_MONITOR_SERVER_IP,
    PING_SERVERS,
    PROC_UPTIME_FILE,
    PROXMOX_HOSTS,
    RDP_SERVERS,
    RESOURCE_ALERT_INTERVAL,
    RESOURCE_ALERT_THRESHOLDS,
    RESOURCE_CHECK_INTERVAL,
    RESOURCE_THRESHOLDS,
    SERVER_CONFIG,
    SERVER_TIMEOUTS,
    SETTINGS_DB_FILE,
    SILENT_END,
    SILENT_START,
    SSH_KEY_PATH,
    SSH_SERVERS,
    SSH_USERNAME,
    STATS_FILE,
    TELEGRAM_TOKEN as SETTINGS_TOKEN,
    WEB_HOST,
    WEB_PORT,
    WINDOWS_CREDENTIALS,
    WINDOWS_SERVER_CREDENTIALS,
    WINRM_CONFIGS,
    ZFS_SERVERS,
    get_all_windows_servers,
    get_server_timeout,
    get_windows_servers_by_type,
    is_proxmox_server,
)

# Определяем какие значения использовать
# Если USE_DB = True и значение из БД не пустое, используем из БД
# Иначе используем из settings.py

TELEGRAM_TOKEN = DB_TELEGRAM_TOKEN if USE_DB and DB_TELEGRAM_TOKEN else SETTINGS_TOKEN
CHAT_IDS = DB_CHAT_IDS if USE_DB and DB_CHAT_IDS else SETTINGS_CHAT_IDS
DEBUG_MODE = DB_DEBUG_MODE if USE_DB else SETTINGS_DEBUG_MODE
MONITOR_SERVER_IP = (
    DB_MONITOR_SERVER_IP if USE_DB and DB_MONITOR_SERVER_IP else SETTINGS_MONITOR_SERVER_IP
)

__all__ = [
    # Пути
    "BASE_DIR",
    "DATA_DIR",
    "LOG_DIR",
    "LOG_FORMAT",
    "LOG_DATE_FORMAT",
    "LOG_MAX_BYTES",
    "LOG_BACKUP_COUNT",
    "DEBUG_LOG_FILE",
    "BOT_LOG_FILE",
    "MONITOR_LOG_FILE",
    "BOT_DEBUG_LOG_FILE",
    "MAIL_MONITOR_LOG_FILE",
    "MAILDIR_BASE",
    "MAILDIR_NEW",
    "MAILDIR_CUR",
    "PROC_UPTIME_FILE",
    # Основные настройки (с приоритетом БД)
    "TELEGRAM_TOKEN",
    "CHAT_IDS",
    "DEBUG_MODE",
    "APP_VERSION",
    # Интервалы проверок
    "CHECK_INTERVAL",
    "MAX_FAIL_TIME",
    # Временные настройки
    "SILENT_START",
    "SILENT_END",
    "DATA_COLLECTION_TIME",
    # Настройки ресурсов
    "RESOURCE_CHECK_INTERVAL",
    "RESOURCE_ALERT_INTERVAL",
    "RESOURCE_THRESHOLDS",
    "RESOURCE_ALERT_THRESHOLDS",
    # Аутентификация
    "SSH_KEY_PATH",
    "SSH_USERNAME",
    # Конфигурация серверов
    "SERVER_CONFIG",
    "WINDOWS_CREDENTIALS",
    "WINDOWS_SERVER_CREDENTIALS",
    "WINRM_CONFIGS",
    "SERVER_TIMEOUTS",
    # Веб-интерфейс
    "WEB_PORT",
    "WEB_HOST",
    "MONITOR_SERVER_IP",
    # Файлы
    "STATS_FILE",
    "BACKUP_DB_FILE",
    "SETTINGS_DB_FILE",
    "DEBUG_CONFIG_FILE",
    "EXTENSIONS_CONFIG_FILE",
    # Бэкапы
    "PROXMOX_HOSTS",
    "DUPLICATE_IP_HOSTS",
    "HOSTNAME_ALIASES",
    "BACKUP_PATTERNS",
    "BACKUP_STATUS_MAP",
    "DATABASE_CONFIG",
    "ZFS_SERVERS",
    "BACKUP_DATABASE_CONFIG",
    "DATABASE_BACKUP_CONFIG",
    # Функции
    "is_proxmox_server",
    "get_windows_servers_by_type",
    "get_all_windows_servers",
    "get_server_timeout",
    # Списки серверов
    "RDP_SERVERS",
    "SSH_SERVERS",
    "PING_SERVERS",
    # Функции из db_settings
    "get_setting",
    "get_json_setting",
    "get_windows_credentials_db",
    "get_windows_server_configs",
    "get_servers_config",
    "load_all_settings",
    "USE_DB",
]
