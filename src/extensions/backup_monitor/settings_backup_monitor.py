"""
/extensions/backup_monitor/settings_backup_monitor.py
Server Monitoring System v4.17.6
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings for the backup_monitor extension
Система мониторинга серверов
Версия: 4.17.6
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки для расширения backup_monitor
"""

from pathlib import Path

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
    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = BASE_DIR / "data"
    LOG_DIR = BASE_DIR / "logs"
    PROXMOX_HOSTS = {}
    DATABASE_BACKUP_CONFIG = {}
    BACKUP_DATABASE_CONFIG = {"backups_db": DATA_DIR / "backups.db"}

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "LOG_DIR",
    "PROXMOX_HOSTS",
    "DATABASE_BACKUP_CONFIG",
    "BACKUP_DATABASE_CONFIG",
]