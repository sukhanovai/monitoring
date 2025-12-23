"""
/extensions/server_checks/settings.py
Server Monitoring System v4.15.7
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Auxiliary settings for server_checks
Система мониторинга серверов
Версия: 4.15.7
Автор: Александр Суханов (c)
Лицензия: MIT
Вспомогательные настройки для server_checks
"""

import os

try:
    from config.settings import BASE_DIR  # type: ignore
except Exception:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

__all__ = ["BASE_DIR"]