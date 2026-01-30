"""
/core/__init__.py
Server Monitoring System v8.3.28
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core system package
Система мониторинга серверов
Версия: 8.3.28
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет ядра системы
"""

from .config_manager import config_manager, ConfigManager
from .checker import ServerChecker

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

def __getattr__(name):
    if name in {"monitor", "Monitor"}:
        from .monitor import monitor, Monitor
        globals().update({"monitor": monitor, "Monitor": Monitor})
        return globals()[name]

    task_router_exports = {
        "TASK_ROUTES",
        "get_task_route",
        "run_task",
        "get_monitoring_servers",
        "run_availability_task",
        "run_resources_task",
        "run_targeted_task",
    }

    if name in task_router_exports:
        from .task_router import (
            TASK_ROUTES,
            get_task_route,
            run_task,
            get_monitoring_servers,
            run_availability_task,
            run_resources_task,
            run_targeted_task,
        )
        globals().update(
            {
                "TASK_ROUTES": TASK_ROUTES,
                "get_task_route": get_task_route,
                "run_task": run_task,
                "get_monitoring_servers": get_monitoring_servers,
                "run_availability_task": run_availability_task,
                "run_resources_task": run_resources_task,
                "run_targeted_task": run_targeted_task,
            }
        )
        return globals()[name]

    raise AttributeError(f"module 'core' has no attribute {name!r}")
