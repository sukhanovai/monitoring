"""
Server Monitoring System v4.2.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Ядро системы мониторинга
Версия: 4.2.2
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
