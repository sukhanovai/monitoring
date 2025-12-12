"""
Server Monitoring System v4.3.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Мониторинг серверов - основной пакет
Версия: 4.3.3
"""

import os
import sys

__version__ = "4.3.3"
__author__ = "Aleksandr Sukhanov"

# Добавляем текущий каталог в путь для импортов
sys.path.insert(0, os.path.dirname(__file__))

# Теперь можем импортировать
try:
    from .utils.common import (
        setup_logging, format_duration, 
        progress_bar, safe_import, DEBUG_MODE,
        debug_log
    )
    from .core.checker import ServerChecker
    
    # Создаем глобальные экземпляры
    logger = setup_logging()
    server_checker = ServerChecker()
    
    __all__ = [
        # Классы
        'ServerChecker',
        
        # Функции
        'setup_logging', 'format_duration', 'progress_bar',
        'safe_import', 'debug_log',
        
        # Переменные
        'DEBUG_MODE',
        
        # Экземпляры
        'logger', 'server_checker'
    ]
    
except ImportError as e:
    print(f"❌ Ошибка импорта в app/__init__.py: {e}")
    # Создаем заглушки чтобы не ломать импорты
    logger = None
    server_checker = None
    __all__ = []