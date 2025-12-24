"""
/app/__init__.py
Server Monitoring System v4.16.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Proxy package for backward compatibility.
Система мониторинга серверов
Версия: 4.16.0
Автор: Александр Суханов (c)
Лицензия: MIT
Прокси-пакет для обратной совместимости.
"""

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
_monitoring_path = Path(__file__).resolve().parent.parent / "src" / "monitoring" / __name__
if _monitoring_path.exists():
    __path__.append(str(_monitoring_path))