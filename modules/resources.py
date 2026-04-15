"""
/app/modules/resources.py
Server Monitoring System v8.50.135
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server resource checking module
Система мониторинга серверов
Версия: 8.50.135
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль проверки ресурсов серверов
"""

import threading
from datetime import datetime, timedelta
from config.db_settings import RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_THRESHOLDS, RESOURCE_ALERT_INTERVAL
from lib.logging import debug_log
from lib.helpers import progress_bar

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
                get_server_by_ip,
                get_linux_resources_improved,
                get_windows_resources_improved
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
                    results.append({
                        "server": server,
                        "resources": resources,
                        "success": resources is not None
                    })
                except Exception as e:
                    results.append({
                        "server": server,
                        "resources": None,
                        "success": False
                    })
            
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
                    results.append({
                        "server": server,
                        "resources": resources,
                        "success": resources is not None
                    })
                except Exception as e:
                    results.append({
                        "server": server,
                        "resources": None,
                        "success": False
                    })
            
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
                        results.append({
                            "server": server,
                            "value": resource_value,
                            "success": True
                        })
                    else:
                        results.append({
                            "server": server,
                            "value": 0,
                            "success": False
                        })
                except Exception as e:
                    results.append({
                        "server": server,
                        "value": 0,
                        "success": False
                    })
            
            # Сортировка по убыванию значения
            results.sort(key=lambda x: x["value"], reverse=True)
            return results
            
        except Exception as e:
            debug_log(f"❌ Ошибка проверки ресурса {resource_type}: {e}")
            return []
    
    def get_resource_history(self, server_ip, limit=10):
        """Получить историю ресурсов сервера"""
        return self.resource_history.get(server_ip, [])[-limit:]
    
    def start_automatic_checks(self):
        """Запуск автоматических проверок ресурсов"""
        debug_log("🔄 Запуск автоматических проверок ресурсов")
        
        while True:
            current_time = datetime.now()
            
            # Проверяем интервал
            if (current_time - self.last_resource_check).total_seconds() >= RESOURCE_CHECK_INTERVAL:
                debug_log("🔍 Автоматическая проверка ресурсов...")
                self.perform_automatic_check()
                self.last_resource_check = current_time
            
            time.sleep(60)  # Проверяем каждую минуту
    
    def perform_automatic_check(self):
        """Выполнение автоматической проверки ресурсов"""
        try:
            results = self.check_all_resources()
            
            # Анализ результатов и отправка алертов
            alerts = []
            for result in results:
                if result["success"] and result["resources"]:
                    server_alerts = self.check_resource_alerts(
                        result["server"]["ip"],
                        result["resources"]
                    )
                    if server_alerts:
                        alerts.extend(server_alerts)
            
            # Отправка алертов если есть
            if alerts:
                self.send_resource_alerts(alerts)
                
        except Exception as e:
            debug_log(f"❌ Ошибка автоматической проверки ресурсов: {e}")
    
    def check_resource_alerts(self, ip, resources):
        """Проверка условий для алертов"""
        alerts = []
        
        # Проверка Disk (одна проверка)
        disk_usage = resources.get('disk', 0)
        if disk_usage >= RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
            alert_key = f"{ip}_disk"
            if alert_key not in self.resource_alerts_sent or \
               (datetime.now() - self.resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
                alerts.append(f"💾 **Дисковое пространство** на сервере: {disk_usage}%")
                self.resource_alerts_sent[alert_key] = datetime.now()
        
        # Здесь можно добавить проверки CPU и RAM
        
        return alerts
    
    def send_resource_alerts(self, alerts):
        """Отправка алертов по ресурсам"""
        if not alerts:
            return
            
        message = "🚨 *Проблемы с ресурсами серверов*\n\n"
        message += "\n".join(alerts)
        message += f"\n⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}"
        
        from bot.handlers.commands import send_alert
        send_alert(message)

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
            results.append({
                "server": server,
                "resources": resources,
                "success": success,
            })

            if success:
                success_count += 1

        stats = {
            "total": total,
            "success": success_count,
            "failed": total - success_count,
        }

        return results, stats

    def check_resource_alerts(self, ip, current_resources):
        """Проверяет условия для отправки алертов по ресурсам."""
        from config import RESOURCE_ALERT_THRESHOLDS, RESOURCE_ALERT_INTERVAL

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
        alerts = []

        disk_usage = resource_entry.get("disk", 0)
        if disk_usage >= RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
            alert_key = f"{ip}_disk"
            if alert_key not in self.resource_alerts_sent or (
                current_time - self.resource_alerts_sent[alert_key]
            ).total_seconds() > RESOURCE_ALERT_INTERVAL:
                alerts.append(
                    f"💾 **Дисковое пространство** на {server_name}: {disk_usage}% "
                    f"(превышен порог {RESOURCE_ALERT_THRESHOLDS['disk_alert']}%)"
                )
                self.resource_alerts_sent[alert_key] = current_time

        cpu_usage = resource_entry.get("cpu", 0)
        if cpu_usage >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"] and len(history) >= 1:
            prev_cpu = history[-1].get("cpu", 0)
            if prev_cpu >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
                alert_key = f"{ip}_cpu"
                if alert_key not in self.resource_alerts_sent or (
                    current_time - self.resource_alerts_sent[alert_key]
                ).total_seconds() > RESOURCE_ALERT_INTERVAL:
                    alerts.append(
                        f"💻 **Процессор** на {server_name}: {prev_cpu}% → {cpu_usage}% "
                        f"(2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS['cpu_alert']}%)"
                    )
                    self.resource_alerts_sent[alert_key] = current_time

        ram_usage = resource_entry.get("ram", 0)
        if ram_usage >= RESOURCE_ALERT_THRESHOLDS["ram_alert"] and len(history) >= 1:
            prev_ram = history[-1].get("ram", 0)
            if prev_ram >= RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
                alert_key = f"{ip}_ram"
                if alert_key not in self.resource_alerts_sent or (
                    current_time - self.resource_alerts_sent[alert_key]
                ).total_seconds() > RESOURCE_ALERT_INTERVAL:
                    alerts.append(
                        f"🧠 **Память** на {server_name}: {prev_ram}% → {ram_usage}% "
                        f"(2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS['ram_alert']}%)"
                    )
                    self.resource_alerts_sent[alert_key] = current_time

        return alerts


# Глобальный экземпляр чекера ресурсов
resources_checker = ResourcesChecker()
