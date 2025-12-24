"""
/src/monitoring/extensions/web_interface/db_settings.py
Server Monitoring System v4.16.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Database settings for the web interface
Система мониторинга серверов
Версия: 4.16.0
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки БД для веб-интерфейса
"""

try:
    from config.db_settings import WEB_PORT, WEB_HOST, CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL  # type: ignore
except Exception:
    from config.settings import WEB_PORT, WEB_HOST, CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL  # type: ignore

__all__ = ["WEB_PORT", "WEB_HOST", "CHECK_INTERVAL", "RESOURCE_CHECK_INTERVAL"]