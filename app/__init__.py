"""
Server Monitoring System v4.0.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Мониторинг серверов - основной пакет
Версия: 4.0.0
"""

__version__ = "4.0.0"
__author__ = "Aleksandr Sukhanov"

# Экспортируем основные компоненты
from .utils.common import (
    setup_logging, format_duration, 
    progress_bar, safe_import, DEBUG_MODE,
    debug_log
)
from .core.checker import ServerChecker

# Создаем глобальные экземпляры для обратной совместимости
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