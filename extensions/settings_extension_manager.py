"""
/extensions/settings_extension_manager.py
Server Monitoring System v4.15.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Settings for extension_manager
Система мониторинга серверов
Версия: 4.15.8
Автор: Александр Суханов (c)
Лицензия: MIT
Настройки для extension_manager
"""

from pathlib import Path

try:
    from config.settings import DATA_DIR  # type: ignore
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[1] / "data"
    
__all__ = ["DATA_DIR"]