"""
/extensions/settings_utils.py
Server Monitoring System v4.17.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings for utils extensions
Система мониторинга серверов
Версия: 4.17.3
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки для utils расширений
"""

from pathlib import Path

try:
    from config.settings import STATS_FILE, DATA_DIR  # type: ignore
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[1]
    DATA_DIR = BASE_DIR / "data"
    STATS_FILE = DATA_DIR / "monitoring_stats.json"

__all__ = ["STATS_FILE", "DATA_DIR"]