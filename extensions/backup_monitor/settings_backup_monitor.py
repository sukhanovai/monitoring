"""
/extensions/backup_monitor/settings_backup_monitor.py
Server Monitoring System v4.15.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings for the backup_monitor extension
Система мониторинга серверов
Версия: 4.15.2
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки для расширения backup_monitor
"""

import os

try:
    from config.settings import (
        BASE_DIR,
        DATA_DIR,
        LOG_DIR,
        PROXMOX_HOSTS,
        DATABASE_BACKUP_CONFIG,
        BACKUP_DATABASE_CONFIG,
    )  # type: ignore
except Exception:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    PROXMOX_HOSTS = {}
    DATABASE_BACKUP_CONFIG = {}
    BACKUP_DATABASE_CONFIG = {"backups_db": os.path.join(DATA_DIR, "backups.db")}

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "LOG_DIR",
    "PROXMOX_HOSTS",
    "DATABASE_BACKUP_CONFIG",
    "BACKUP_DATABASE_CONFIG",
]