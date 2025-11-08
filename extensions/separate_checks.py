"""
Server Monitoring System v2.1.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Модуль для раздельной проверки ресурсов по типам серверов
"""

from extensions.resource_check import get_linux_resources_improved, get_windows_resources_improved
from extensions.server_list import initialize_servers
from config import WINDOWS_SERVER_CREDENTIALS
import time

def progress_bar(percentage, width=20):
    """Генерирует текстовый прогресс-бар"""
    filled = int(round(width * percentage / 100))
    return f"[{'█' * filled}{'░' * (width - filled)}] {percentage:.1f}%"

def check_windows_2025_servers(update_progress=None):
    """Проверка только Windows Server 2025 с прогрессом"""
    servers = initialize_servers()
    windows_2025_ips = WINDOWS_SERVER_CREDENTIALS["windows_2025"]["servers"]

    target_servers = [s for s in servers if s["ip"] in windows_2025_ips and s["type"] == "rdp"]
    results = []

    print(f"🔍 Проверяем Windows 2025 серверы: {len(target_servers)} серверов")

    for i, server in enumerate(target_servers):
        if update_progress:
            progress = (i + 1) / len(target_servers) * 100
            update_progress(progress, f"⏳ {server['name']} ({server['ip']})")

        print(f"🔄 Проверяем {server['name']} ({server['ip']})")
        try:
            resources = get_windows_resources_improved(server["ip"], timeout=35)
            # ГАРАНТИРУЕМ, ЧТО resources НЕ БУДЕТ None
            if resources is None:
                resources = {
                    "cpu": 0.0,
                    "ram": 0.0, 
                    "disk": 0.0,
                    "status": "unavailable"
                }
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None and resources.get("status") != "unavailable"
            })
        except Exception as e:
            print(f"❌ Ошибка при проверке {server['ip']}: {e}")
            results.append({
                "server": server,
                "resources": {
                    "cpu": 0.0,
                    "ram": 0.0,
                    "disk": 0.0,
                    "status": "error",
                    "error": str(e)
                },
                "success": False
            })

        time.sleep(2)  # Задержка между проверками

    return results, len(target_servers)

def check_domain_windows_servers(update_progress=None):
    """Проверка доменных Windows серверов с прогрессом и оптимизацией для старых серверов"""
    servers = initialize_servers()
    domain_ips = WINDOWS_SERVER_CREDENTIALS["domain_servers"]["servers"]

    target_servers = [s for s in servers if s["ip"] in domain_ips and s["type"] == "rdp"]
    results = []

    print(f"🔍 Проверяем доменные Windows серверы: {len(target_servers)} серверов")

    for i, server in enumerate(target_servers):
        if update_progress:
            progress = (i + 1) / len(target_servers) * 100
            update_progress(progress, f"⏳ {server['name']} ({server['ip']})")

        print(f"🔄 Проверяем {server['name']} ({server['ip']})")
        try:
            # Для доменных серверов используем оптимизированный метод с меньшим timeout
            resources = get_windows_resources_improved(server["ip"], timeout=15)
            
            # ГАРАНТИРУЕМ, ЧТО resources НЕ БУДЕТ None
            if resources is None:
                resources = {
                    "cpu": 0.0,
                    "ram": 0.0, 
                    "disk": 0.0,
                    "status": "unavailable",
                    "os": "Windows Server (unavailable)",
                    "access_method": "none",
                    "server_type": "domain_servers"
                }
                
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None and resources.get("status") != "unavailable"
            })
        except Exception as e:
            print(f"❌ Ошибка при проверке {server['ip']}: {e}")
            results.append({
                "server": server,
                "resources": {
                    "cpu": 0.0,
                    "ram": 0.0,
                    "disk": 0.0,
                    "status": "error",
                    "os": "Windows Server (error)",
                    "access_method": "error",
                    "server_type": "domain_servers",
                    "error": str(e)
                },
                "success": False
            })

        # Увеличиваем задержку между проверками старых серверов
        time.sleep(2)

    return results, len(target_servers)

def check_standard_windows_servers(update_progress=None):
    """Проверка обычных Windows серверов с прогрессом"""
    servers = initialize_servers()
    standard_ips = WINDOWS_SERVER_CREDENTIALS["standard_windows"]["servers"]

    target_servers = [s for s in servers if s["ip"] in standard_ips and s["type"] == "rdp"]
    results = []

    print(f"🔍 Проверяем стандартные Windows серверы: {len(target_servers)} серверов")

    for i, server in enumerate(target_servers):
        if update_progress:
            progress = (i + 1) / len(target_servers) * 100
            update_progress(progress, f"⏳ {server['name']} ({server['ip']})")

        print(f"🔄 Проверяем {server['name']} ({server['ip']})")
        try:
            resources = get_windows_resources_improved(server["ip"], timeout=30)
            # ГАРАНТИРУЕМ, ЧТО resources НЕ БУДЕТ None
            if resources is None:
                resources = {
                    "cpu": 0.0,
                    "ram": 0.0, 
                    "disk": 0.0,
                    "status": "unavailable"
                }
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None and resources.get("status") != "unavailable"
            })
        except Exception as e:
            print(f"❌ Ошибка при проверке {server['ip']}: {e}")
            results.append({
                "server": server,
                "resources": {
                    "cpu": 0.0,
                    "ram": 0.0,
                    "disk": 0.0,
                    "status": "error",
                    "error": str(e)
                },
                "success": False
            })

        time.sleep(1)

    return results, len(target_servers)

def check_admin_windows_servers(update_progress=None):
    """Проверка Windows серверов с учеткой Admin с прогрессом"""
    servers = initialize_servers()
    admin_ips = WINDOWS_SERVER_CREDENTIALS["admin_servers"]["servers"]

    target_servers = [s for s in servers if s["ip"] in admin_ips and s["type"] == "rdp"]
    results = []

    print(f"🔍 Проверяем Windows серверы (Admin): {len(target_servers)} серверов")

    for i, server in enumerate(target_servers):
        if update_progress:
            progress = (i + 1) / len(target_servers) * 100
            update_progress(progress, f"⏳ {server['name']} ({server['ip']})")

        print(f"🔄 Проверяем {server['name']} ({server['ip']})")
        try:
            resources = get_windows_resources_improved(server["ip"], timeout=30)
            # ГАРАНТИРУЕМ, ЧТО resources НЕ БУДЕТ None
            if resources is None:
                resources = {
                    "cpu": 0.0,
                    "ram": 0.0, 
                    "disk": 0.0,
                    "status": "unavailable"
                }
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None and resources.get("status") != "unavailable"
            })
        except Exception as e:
            print(f"❌ Ошибка при проверке {server['ip']}: {e}")
            results.append({
                "server": server,
                "resources": {
                    "cpu": 0.0,
                    "ram": 0.0,
                    "disk": 0.0,
                    "status": "error",
                    "error": str(e)
                },
                "success": False
            })

        time.sleep(1)

    return results, len(target_servers)

def check_linux_servers(update_progress=None):
    """Проверка Linux серверов с прогрессом"""
    servers = initialize_servers()
    target_servers = [s for s in servers if s["type"] == "ssh"]
    results = []

    print(f"🔍 Проверяем Linux серверы: {len(target_servers)} серверов")

    for i, server in enumerate(target_servers):
        if update_progress:
            progress = (i + 1) / len(target_servers) * 100
            update_progress(progress, f"⏳ {server['name']} ({server['ip']})")

        print(f"🔄 Проверяем {server['name']} ({server['ip']})")
        try:
            resources = get_linux_resources_improved(server["ip"])
            # ГАРАНТИРУЕМ, ЧТО resources НЕ БУДЕТ None
            if resources is None:
                resources = {
                    "cpu": 0.0,
                    "ram": 0.0, 
                    "disk": 0.0,
                    "status": "unavailable"
                }
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None and resources.get("status") != "unavailable"
            })
        except Exception as e:
            print(f"❌ Ошибка при проверке {server['ip']}: {e}")
            results.append({
                "server": server,
                "resources": {
                    "cpu": 0.0,
                    "ram": 0.0,
                    "disk": 0.0,
                    "status": "error",
                    "error": str(e)
                },
                "success": False
            })

        time.sleep(0.5)

    return results, len(target_servers)

def check_all_servers_by_type(update_progress=None):
    """Проверка всех серверов с группировкой по типам"""
    print("🚀 Запуск проверки серверов по типам...")

    # Проверяем все типы Windows серверов
    win2025_results, win2025_total = check_windows_2025_servers(update_progress)
    domain_results, domain_total = check_domain_windows_servers(update_progress)
    admin_results, admin_total = check_admin_windows_servers(update_progress)
    win_std_results, win_std_total = check_standard_windows_servers(update_progress)

    # Проверяем Linux
    linux_results, linux_total = check_linux_servers(update_progress)

    # Собираем статистику
    stats = {
        "windows_2025": {
            "checked": win2025_total,
            "success": len([r for r in win2025_results if r["success"]]),
            "failed": len([r for r in win2025_results if not r["success"]])
        },
        "domain_windows": {
            "checked": domain_total,
            "success": len([r for r in domain_results if r["success"]]),
            "failed": len([r for r in domain_results if not r["success"]])
        },
        "admin_windows": {
            "checked": admin_total,
            "success": len([r for r in admin_results if r["success"]]),
            "failed": len([r for r in admin_results if not r["success"]])
        },
        "standard_windows": {
            "checked": win_std_total,
            "success": len([r for r in win_std_results if r["success"]]),
            "failed": len([r for r in win_std_results if not r["success"]])
        },
        "linux": {
            "checked": linux_total,
            "success": len([r for r in linux_results if r["success"]]),
            "failed": len([r for r in linux_results if not r["success"]])
        }
    }

    # Объединяем все результаты
    all_results = (win2025_results + domain_results + admin_results +
                   win_std_results + linux_results)

    return all_results, stats
