"""
/app/core/__init__.py
Server Monitoring System v4.14.41
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core system
Система мониторинга серверов
Версия: 4.14.41
Автор: Александр Суханов (c)
Лицензия: MIT
Ядро системы мониторинга
"""

import sys
import os

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from .checker import ServerChecker
    __all__ = ['ServerChecker']
except ImportError as e:
    print(f"❌ Ошибка импорта в app/core/__init__.py: {e}")
    __all__ = []
