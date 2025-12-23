"""
/extensions/settings_extension_manager.py
Server Monitoring System v4.15.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings for extension_manager
Система мониторинга серверов
Версия: 4.15.5
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки для extension_manager
"""

import os

try:
    from config.settings import DATA_DIR  # type: ignore
except Exception:
    DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

__all__ = ["DATA_DIR"]