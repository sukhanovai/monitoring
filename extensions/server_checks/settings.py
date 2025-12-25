"""
/extensions/server_checks/settings.py
Server Monitoring System v4.18.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Auxiliary settings for server_checks
Система мониторинга серверов
Версия: 4.18.1
Автор: Александр Суханов (c)
Лицензия: MIT
Вспомогательные настройки для server_checks
"""

from pathlib import Path

try:
    from config.settings import BASE_DIR  # type: ignore
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[2]

__all__ = ["BASE_DIR"]