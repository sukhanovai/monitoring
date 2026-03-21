"""
/core/task_router.py
Server Monitoring System v8.33.40
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Task router helpers
Система мониторинга серверов
Версия: 8.33.40
Автор: Александр Суханов (c)
Лицензия: MIT
Хелперы маршрутизации задач
"""

from typing import Any, Dict, Optional, Tuple

from lib.logging import debug_log, setup_logging
from modules.availability import availability_checker
from modules.mail_monitor import run_mail_monitor
from modules.resources import resources_checker
from modules.targeted_checks import targeted_checks
from core.monitor import monitor

# Локальный логгер для CLI/функциональных проверок
_logger = setup_logging("task_router")

# Тип результата: (успех, полезная нагрузка/сообщение)
TaskResult = Tuple[bool, Any]


def get_monitoring_servers(force_reload: bool = False):
    """
    Загружает список серверов для задач мониторинга.
    Позволяет централизованно переиспользовать логику ядра.
    """
    if force_reload or not monitor.servers:
        monitor.servers = monitor.load_servers()
        monitor.initialize_server_status()
        debug_log(f"🔄 Загружено серверов для задач: {len(monitor.servers)}")
    return monitor.servers


def run_availability_task(force_reload: bool = False, **_: Any) -> TaskResult:
    """Проверка доступности всех серверов."""
    servers = get_monitoring_servers(force_reload)
    results = availability_checker.check_multiple_servers(servers)
    return True, results


def run_resources_task(force_reload: bool = False, **_: Any) -> TaskResult:
    """Проверка ресурсов всех серверов."""
    servers = get_monitoring_servers(force_reload)
    results, stats = resources_checker.check_multiple_resources(servers)
    return True, {"results": results, "stats": stats}


def run_targeted_task(
    server_id: Optional[str] = None,
    mode: str = "availability",
    **_: Any,
) -> TaskResult:
    """
    Точечная проверка конкретного сервера.

    Args:
        server_id: IP или имя сервера.
        mode: availability | resources.
    """
    if not server_id:
        return False, "❌ Требуется параметр --server для точечной проверки"

    if mode == "resources":
        success, server, message = targeted_checks.check_single_server_resources(server_id)
    else:
        success, server, message = targeted_checks.check_single_server_availability(server_id)

    return success, {"server": server, "message": message}


def run_mail_monitor_task(**_: Any) -> TaskResult:
    """Обработка новых писем о бэкапах."""
    processed = run_mail_monitor()
    return True, {"processed": processed}


# Соответствие задач файлам и обработчикам
TASK_ROUTES: Dict[str, Dict[str, Any]] = {
    "availability": {
        "module": "modules.availability.py",
        "runner": run_availability_task,
        "description": "Проверка доступности всех серверов",
    },
    "resources": {
        "module": "modules.resources.py",
        "runner": run_resources_task,
        "description": "Проверка ресурсов всех серверов",
    },
    "targeted_checks": {
        "module": "modules.targeted_checks.py",
        "runner": run_targeted_task,
        "description": "Адресные проверки отдельного сервера",
    },
    "mail_monitor": {
        "module": "modules.mail_monitor.py",
        "runner": run_mail_monitor_task,
        "description": "Обработка новых писем с отчётами о бэкапах",
    },
}


def get_task_route(task_name: str) -> Optional[Dict[str, Any]]:
    """Возвращает описание задачи по имени."""
    return TASK_ROUTES.get(task_name)


def run_task(task_name: str, **kwargs: Any) -> TaskResult:
    """Запускает задачу по имени, используя централизованный роутер."""
    route = get_task_route(task_name)
    if not route:
        return False, f"❌ Неизвестная задача: {task_name}"

    runner = route["runner"]
    return runner(**kwargs)


__all__ = [
    "TASK_ROUTES",
    "get_task_route",
    "run_task",
    "get_monitoring_servers",
    "run_availability_task",
    "run_resources_task",
    "run_targeted_task",
    "run_mail_monitor_task",
]