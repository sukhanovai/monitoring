"""
/extensions/db_settings_server_checks.py
Server Monitoring System v4.18.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database settings values ​​for server_checks
Система мониторинга серверов
Версия: 4.18.1
Автор: Александр Суханов (c)
Лицензия: MIT
Значения настроек БД для server_checks
"""

try:
    from config.db_settings import (
        RDP_SERVERS,
        SSH_SERVERS,
        PING_SERVERS,
        SSH_KEY_PATH,
        SSH_USERNAME,
        RESOURCE_THRESHOLDS,
        WINDOWS_SERVER_CREDENTIALS,
        WINRM_CONFIGS,
        SERVER_CONFIG,
    )
except Exception:
    from config.settings import (
        RDP_SERVERS,
        SSH_SERVERS,
        PING_SERVERS,
        SSH_KEY_PATH,
        SSH_USERNAME,
        RESOURCE_THRESHOLDS,
        WINDOWS_SERVER_CREDENTIALS,
        WINRM_CONFIGS,
        SERVER_CONFIG,
    )

__all__ = [
    "RDP_SERVERS",
    "SSH_SERVERS",
    "PING_SERVERS",
    "SSH_KEY_PATH",
    "SSH_USERNAME",
    "RESOURCE_THRESHOLDS",
    "WINDOWS_SERVER_CREDENTIALS",
    "WINRM_CONFIGS",
    "SERVER_CONFIG",
]