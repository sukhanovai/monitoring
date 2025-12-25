"""
/extensions/web_interface/settings.py
Server Monitoring System v4.17.6
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface settings (static values)
Система мониторинга серверов
Версия: 4.17.6
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки веб-интерфейса (статические значения)
"""

from pathlib import Path

try:
    from config.settings import STATS_FILE, DATA_DIR  # type: ignore
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = BASE_DIR / "data"
    STATS_FILE = DATA_DIR / "monitoring_stats.json"

__all__ = ["STATS_FILE", "DATA_DIR"]