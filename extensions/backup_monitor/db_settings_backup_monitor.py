"""
/extensions/backup_monitor/db_settings_backup_monitor.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings from the database for the backup_monitor extension
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РќР°СЃС‚СЂРѕР№РєРё РёР· Р‘Р” РґР»СЏ СЂР°СЃС€РёСЂРµРЅРёСЏ backup_monitor
"""

try:
    from config.db_settings import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG, BACKUP_DATABASE_CONFIG  # type: ignore
except Exception:
    from config.settings import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG, BACKUP_DATABASE_CONFIG  # type: ignore

__all__ = ["PROXMOX_HOSTS", "DATABASE_BACKUP_CONFIG", "BACKUP_DATABASE_CONFIG"]