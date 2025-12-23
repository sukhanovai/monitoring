"""
/core/__init__.py
Server Monitoring System v4.15.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core system package
Система мониторинга серверов
Версия: 4.15.8
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет ядра системы
"""

from .config_manager import config_manager, ConfigManager
from .checker import ServerChecker
from .monitor import monitor, Monitor
from .task_router import (
    TASK_ROUTES,
    get_task_route,
    run_task,
    get_monitoring_servers,
    run_availability_task,
    run_resources_task,
    run_targeted_task,
)

__all__ = [
    'config_manager',
    'ConfigManager',
    'ServerChecker',
    'monitor',
    'Monitor',
    'TASK_ROUTES',
    'get_task_route',
    'run_task',
    'get_monitoring_servers',
    'run_availability_task',
    'run_resources_task',
    'run_targeted_task',
]