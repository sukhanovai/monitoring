"""
/core/task_router.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Task router helpers
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РҐРµР»РїРµСЂС‹ РјР°СЂС€СЂСѓС‚РёР·Р°С†РёРё Р·Р°РґР°С‡
"""

from typing import Any, Dict, Optional, Tuple

from lib.logging import debug_log, setup_logging
from modules.availability import availability_checker
from modules.mail_monitor import run_mail_monitor
from modules.resources import resources_checker
from modules.targeted_checks import targeted_checks
from core.monitor import monitor

# Р›РѕРєР°Р»СЊРЅС‹Р№ Р»РѕРіРіРµСЂ РґР»СЏ CLI/С„СѓРЅРєС†РёРѕРЅР°Р»СЊРЅС‹С… РїСЂРѕРІРµСЂРѕРє
_logger = setup_logging("task_router")

# РўРёРї СЂРµР·СѓР»СЊС‚Р°С‚Р°: (СѓСЃРїРµС…, РїРѕР»РµР·РЅР°СЏ РЅР°РіСЂСѓР·РєР°/СЃРѕРѕР±С‰РµРЅРёРµ)
TaskResult = Tuple[bool, Any]


def get_monitoring_servers(force_reload: bool = False):
    """
    Р—Р°РіСЂСѓР¶Р°РµС‚ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ РґР»СЏ Р·Р°РґР°С‡ РјРѕРЅРёС‚РѕСЂРёРЅРіР°.
    РџРѕР·РІРѕР»СЏРµС‚ С†РµРЅС‚СЂР°Р»РёР·РѕРІР°РЅРЅРѕ РїРµСЂРµРёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ Р»РѕРіРёРєСѓ СЏРґСЂР°.
    """
    if force_reload or not monitor.servers:
        monitor.servers = monitor.load_servers()
        monitor.initialize_server_status()
        debug_log(f"рџ”„ Р—Р°РіСЂСѓР¶РµРЅРѕ СЃРµСЂРІРµСЂРѕРІ РґР»СЏ Р·Р°РґР°С‡: {len(monitor.servers)}")
    return monitor.servers


def run_availability_task(force_reload: bool = False, **_: Any) -> TaskResult:
    """РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ."""
    servers = get_monitoring_servers(force_reload)
    results = availability_checker.check_multiple_servers(servers)
    return True, results


def run_resources_task(force_reload: bool = False, **_: Any) -> TaskResult:
    """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ."""
    servers = get_monitoring_servers(force_reload)
    results, stats = resources_checker.check_multiple_resources(servers)
    return True, {"results": results, "stats": stats}


def run_targeted_task(
    server_id: Optional[str] = None,
    mode: str = "availability",
    **_: Any,
) -> TaskResult:
    """
    РўРѕС‡РµС‡РЅР°СЏ РїСЂРѕРІРµСЂРєР° РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ СЃРµСЂРІРµСЂР°.

    Args:
        server_id: IP РёР»Рё РёРјСЏ СЃРµСЂРІРµСЂР°.
        mode: availability | resources.
    """
    if not server_id:
        return False, "вќЊ РўСЂРµР±СѓРµС‚СЃСЏ РїР°СЂР°РјРµС‚СЂ --server РґР»СЏ С‚РѕС‡РµС‡РЅРѕР№ РїСЂРѕРІРµСЂРєРё"

    if mode == "resources":
        success, server, message = targeted_checks.check_single_server_resources(server_id)
    else:
        success, server, message = targeted_checks.check_single_server_availability(server_id)

    return success, {"server": server, "message": message}


def run_mail_monitor_task(**_: Any) -> TaskResult:
    """РћР±СЂР°Р±РѕС‚РєР° РЅРѕРІС‹С… РїРёСЃРµРј Рѕ Р±СЌРєР°РїР°С…."""
    processed = run_mail_monitor()
    return True, {"processed": processed}


# РЎРѕРѕС‚РІРµС‚СЃС‚РІРёРµ Р·Р°РґР°С‡ С„Р°Р№Р»Р°Рј Рё РѕР±СЂР°Р±РѕС‚С‡РёРєР°Рј
TASK_ROUTES: Dict[str, Dict[str, Any]] = {
    "availability": {
        "module": "modules.availability.py",
        "runner": run_availability_task,
        "description": "РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ",
    },
    "resources": {
        "module": "modules.resources.py",
        "runner": run_resources_task,
        "description": "РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ",
    },
    "targeted_checks": {
        "module": "modules.targeted_checks.py",
        "runner": run_targeted_task,
        "description": "РђРґСЂРµСЃРЅС‹Рµ РїСЂРѕРІРµСЂРєРё РѕС‚РґРµР»СЊРЅРѕРіРѕ СЃРµСЂРІРµСЂР°",
    },
    "mail_monitor": {
        "module": "modules.mail_monitor.py",
        "runner": run_mail_monitor_task,
        "description": "РћР±СЂР°Р±РѕС‚РєР° РЅРѕРІС‹С… РїРёСЃРµРј СЃ РѕС‚С‡С‘С‚Р°РјРё Рѕ Р±СЌРєР°РїР°С…",
    },
}


def get_task_route(task_name: str) -> Optional[Dict[str, Any]]:
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕРїРёСЃР°РЅРёРµ Р·Р°РґР°С‡Рё РїРѕ РёРјРµРЅРё."""
    return TASK_ROUTES.get(task_name)


def run_task(task_name: str, **kwargs: Any) -> TaskResult:
    """Р—Р°РїСѓСЃРєР°РµС‚ Р·Р°РґР°С‡Сѓ РїРѕ РёРјРµРЅРё, РёСЃРїРѕР»СЊР·СѓСЏ С†РµРЅС‚СЂР°Р»РёР·РѕРІР°РЅРЅС‹Р№ СЂРѕСѓС‚РµСЂ."""
    route = get_task_route(task_name)
    if not route:
        return False, f"вќЊ РќРµРёР·РІРµСЃС‚РЅР°СЏ Р·Р°РґР°С‡Р°: {task_name}"

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