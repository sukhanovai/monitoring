"""
Server Monitoring System v4.4.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
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
