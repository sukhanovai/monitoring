"""
/extensions/backup_monitor/db_settings_backup_monitor.py
Server Monitoring System v8.62.78
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings from the database for the backup_monitor extension
Система мониторинга серверов
Версия: 8.62.78
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки из БД для расширения backup_monitor
"""

try:
    from config.db_settings import (  # type: ignore
        BACKUP_DATABASE_CONFIG,
        DATABASE_BACKUP_CONFIG,
        PROXMOX_HOSTS,
    )
except Exception:
    from config.settings import (  # type: ignore
        BACKUP_DATABASE_CONFIG,
        DATABASE_BACKUP_CONFIG,
        PROXMOX_HOSTS,
    )

__all__ = ["PROXMOX_HOSTS", "DATABASE_BACKUP_CONFIG", "BACKUP_DATABASE_CONFIG"]
