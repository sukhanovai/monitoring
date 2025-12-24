"""
/__init__.py
Server Monitoring System v4.16.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Proxy package for backward compatibility.
Система мониторинга серверов
Версия: 4.16.4
Автор: Александр Суханов (c)
Лицензия: MIT
Прокси-пакет для обратной совместимости.
"""

from pathlib import Path
import sys
from importlib import import_module

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

_monitoring = import_module("monitoring")

for _name in dir(_monitoring):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_monitoring, _name)

del _monitoring
__all__ = [name for name in globals() if not name.startswith("_")]