"""
/extensions/backup_monitor/db_settings_backup_monitor.py
Server Monitoring System v7.1.19
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings from the database for the backup_monitor extension
Система мониторинга серверов
Версия: 7.1.19
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки из БД для расширения backup_monitor
"""

try:
    from config.db_settings import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG, BACKUP_DATABASE_CONFIG  # type: ignore
except Exception:
    from config.settings import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG, BACKUP_DATABASE_CONFIG  # type: ignore

__all__ = ["PROXMOX_HOSTS", "DATABASE_BACKUP_CONFIG", "BACKUP_DATABASE_CONFIG"]