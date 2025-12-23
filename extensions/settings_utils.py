"""
/extensions/settings_utils.py
Server Monitoring System v4.15.6
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings for utils extensions
Система мониторинга серверов
Версия: 4.15.6
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки для utils расширений
"""

import os

try:
    from config.settings import STATS_FILE, DATA_DIR  # type: ignore
except Exception:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    STATS_FILE = os.path.join(DATA_DIR, "monitoring_stats.json")

__all__ = ["STATS_FILE", "DATA_DIR"]