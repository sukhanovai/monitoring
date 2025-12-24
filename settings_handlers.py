"""
/settings_handlers.py
Server Monitoring System v4.16.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Proxy module for backward compatibility
Система мониторинга серверов
Версия: 4.16.4
Автор: Александр Суханов (c)
Лицензия: MIT
Прокси-модуль для обратной совместимости
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from monitoring.settings_handlers import *