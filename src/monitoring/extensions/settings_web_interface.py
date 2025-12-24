"""
/src/monitoring/extensions/settings_web_interface.py
Server Monitoring System v4.16.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface settings (static values)
Система мониторинга серверов
Версия: 4.16.3
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки веб-интерфейса (статические значения)
"""

from pathlib import Path

try:
    from config.settings import STATS_FILE, DATA_DIR  # type: ignore
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[1]
    DATA_DIR = BASE_DIR / "data"
    STATS_FILE = DATA_DIR / "monitoring_stats.json"

__all__ = ["STATS_FILE", "DATA_DIR"]