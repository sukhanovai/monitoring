"""
/app/modules/resources.py
Server Monitoring System v8.62.64
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server resource checking module
Система мониторинга серверов
Версия: 8.62.64
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль проверки ресурсов серверов
"""

from datetime import datetime

from lib.helpers import progress_bar
from lib.logging import debug_log


class ResourceMonitor:
    """Класс мониторинга ресурсов серверов"""

    def __init__(self):
        self.resource_history = {}
        self.resource_alerts_sent = {}
        self.last_resource_check = datetime.now()

    def check_single_server(self, server_ip):
        """Проверка ресурсов одного сервера"""
        try:
            from extensions.server_checks import (
                get_linux_resources_improved,
                get_server_by_ip,
                get_windows_resources_improved,
            )

            server = get_server_by_ip(server_ip)
            if not server:
                debug_log(f"❌ Сервер {server_ip} не найден")
                return None

            if server["type"] == "ssh":
                return get_linux_resources_improved(server_ip)
            elif server["type"] == "rdp":
                return get_windows_resources_improved(server_ip)
            else:
                return None

        except Exception as e:
            debug_log(f"❌ Ошибка проверки ресурсов {server_ip}: {e}")
            return None

    def check_all_resources(self, progress_callback=None):
        """Проверка ресурсов всех серверов"""
        try:
            from extensions.server_checks import initialize_servers

            servers = initialize_servers()

            results = []
            total = len(servers)

            for i, server in enumerate(servers):
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"Проверяем {server['name']}...")

                try:
                    resources = self.check_single_server(server["ip"])
                    results.append(
                        {"server": server, "resources": resources, "success": resources is not None}
                    )
                except Exception as e:
                    results.append({"server": server, "resources": None, "success": False})

            return results

        except Exception as e:
            debug_log(f"❌ Ошибка проверки всех ресурсов: {e}")
            return []

    def check_by_server_type(self, server_type, progress_callback=None):
        """Проверка ресурсов серверов определенного типа"""
        try:
            from extensions.server_checks import get_servers_by_type

            servers = get_servers_by_type(server_type)

            results = []
            total = len(servers)

            for i, server in enumerate(servers):
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"Проверяем {server['name']}...")

                try:
                    resources = self.check_single_server(server["ip"])
                    results.append(
                        {"server": server, "resources": resources, "success": resources is not None}
                    )
                except Exception as e:
                    results.append({"server": server, "resources": None, "success": False})

            return results

        except Exception as e:
            debug_log(f"❌ Ошибка проверки ресурсов типа {server_type}: {e}")
            return []

    def check_by_resource_type(self, resource_type, progress_callback=None):
        """Проверка определенного типа ресурсов на всех серверах"""
        try:
            from extensions.server_checks import initialize_servers

            servers = initialize_servers()

            results = []
            total = len(servers)

            for i, server in enumerate(servers):
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"Проверяем {server['name']}...")

                try:
                    resources = self.check_single_server(server["ip"])
                    if resources:
                        resource_value = resources.get(resource_type, 0)
                        results.append({"server": server, "value": resource_value, "success": True})
                    else:
                        results.append({"server": server, "value": 0, "success": False})
                except Exception as e:
                    results.append({"server": server, "value": 0, "success": False})

            # Сортировка по убыванию значения
            results.sort(key=lambda x: x["value"], reverse=True)
            return results

        except Exception as e:
            debug_log(f"❌ Ошибка проверки ресурса {resource_type}: {e}")
            return []

    def get_resource_history(self, server_ip, limit=10):
        """Получить историю ресурсов сервера"""
        return self.resource_history.get(server_ip, [])[-limit:]

    # PR8: метод `start_automatic_checks`, `perform_automatic_check`,
    # `check_resource_alerts` и `send_resource_alerts` были мёртвым кодом
    # после PR5 — единственный «живой» автоматический цикл живёт в
    # `core.monitor_parts.alerts.check_resources_automatically`. Кроме того,
    # локальная `check_resource_alerts` здесь проверяла только disk
    # (без CPU/RAM), что расходилось с реальной логикой в `monitor_parts`.
    # Чтобы не плодить дубль декларативной схемы, удалены — единая точка
    # правды теперь в `core/monitor_parts/alerts.py`.


# Глобальный экземпляр мониторинга ресурсов
resource_monitor = ResourceMonitor()


class ResourcesChecker:
    """Утилиты для разовых проверок ресурсов серверов."""

    def __init__(self):
        self.resource_history = {}
        self.resource_alerts_sent = {}

    def check_server_resources(self, server):
        """Проверка ресурсов одного сервера."""
        try:
            server_ip = server.get("ip")
            server_name = server.get("name", server_ip)
            server_type = server.get("type")

            resources = None
            if server_type == "ssh":
                from extensions.server_checks import get_linux_resources_improved

                resources = get_linux_resources_improved(server_ip)
            elif server_type == "rdp":
                from extensions.server_checks import get_windows_resources_improved

                resources = get_windows_resources_improved(server_ip)

            if resources is None:
                return False, None

            resources = dict(resources)
            resources["server_name"] = server_name
            return True, resources

        except Exception as e:
            debug_log(f"❌ Ошибка проверки ресурсов {server.get('name')}: {e}")
            return False, None

    def check_multiple_resources(self, servers, progress_callback=None):
        """Проверка ресурсов нескольких серверов."""
        results = []
        total = len(servers)
        success_count = 0

        for index, server in enumerate(servers):
            if progress_callback:
                progress = (index + 1) / total * 100 if total else 100
                progress_callback(progress, f"Проверяем {server.get('name', 'сервер')}...")

            success, resources = self.check_server_resources(server)
            results.append(
                {
                    "server": server,
                    "resources": resources,
                    "success": success,
                }
            )

            if success:
                success_count += 1

        stats = {
            "total": total,
            "success": success_count,
            "failed": total - success_count,
        }

        return results, stats

    def check_resource_alerts(self, ip, current_resources):
        """Проверяет условия для отправки алертов по ресурсам.

        PR8: тонкий wrapper над декларативной схемой `ALERT_RULES` из
        `core.monitor_parts.alerts.evaluate_alert_rules`. Раньше здесь
        был copy-paste из `monitor_core` (три блока disk/cpu/ram). История
        и счётчик отправок живут в полях `ResourcesChecker` — отдельно
        от глобального `state` ядра мониторинга, чтобы разовые ручные
        проверки не мешали автоматическому пайплайну.
        """
        from core.monitor_parts.alerts import evaluate_alert_rules

        if not current_resources:
            return []

        current_time = datetime.now()
        server_name = current_resources.get("server_name", ip)

        if ip not in self.resource_history:
            self.resource_history[ip] = []

        resource_entry = {
            "timestamp": current_time,
            "cpu": current_resources.get("cpu", 0),
            "ram": current_resources.get("ram", 0),
            "disk": current_resources.get("disk", 0),
            "server_name": server_name,
        }

        self.resource_history[ip].append(resource_entry)
        if len(self.resource_history[ip]) > 10:
            self.resource_history[ip] = self.resource_history[ip][-10:]

        history = self.resource_history.get(ip, [])[:-1]
        return evaluate_alert_rules(
            ip,
            resource_entry,
            history,
            self.resource_alerts_sent,
            now=current_time,
        )


# Глобальный экземпляр чекера ресурсов
resources_checker = ResourcesChecker()
