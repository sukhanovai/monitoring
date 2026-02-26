"""
/app/modules/resources.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server resource checking module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ
"""

import threading
from datetime import datetime, timedelta
from config.db_settings import RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_THRESHOLDS, RESOURCE_ALERT_INTERVAL
from lib.logging import debug_log
from lib.helpers import progress_bar

class ResourceMonitor:
    """РљР»Р°СЃСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ"""
    
    def __init__(self):
        self.resource_history = {}
        self.resource_alerts_sent = {}
        self.last_resource_check = datetime.now()
        
    def check_single_server(self, server_ip):
        """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        try:
            from extensions.server_checks import (
                get_server_by_ip,
                get_linux_resources_improved,
                get_windows_resources_improved
            )
            
            server = get_server_by_ip(server_ip)
            if not server:
                debug_log(f"вќЊ РЎРµСЂРІРµСЂ {server_ip} РЅРµ РЅР°Р№РґРµРЅ")
                return None
                
            if server["type"] == "ssh":
                return get_linux_resources_improved(server_ip)
            elif server["type"] == "rdp":
                return get_windows_resources_improved(server_ip)
            else:
                return None
                
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ {server_ip}: {e}")
            return None
    
    def check_all_resources(self, progress_callback=None):
        """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ"""
        try:
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            
            results = []
            total = len(servers)
            
            for i, server in enumerate(servers):
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server['name']}...")
                
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
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё РІСЃРµС… СЂРµСЃСѓСЂСЃРѕРІ: {e}")
            return []
    
    def check_by_server_type(self, server_type, progress_callback=None):
        """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ РѕРїСЂРµРґРµР»РµРЅРЅРѕРіРѕ С‚РёРїР°"""
        try:
            from extensions.server_checks import get_servers_by_type
            servers = get_servers_by_type(server_type)
            
            results = []
            total = len(servers)
            
            for i, server in enumerate(servers):
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server['name']}...")
                
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
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ С‚РёРїР° {server_type}: {e}")
            return []
    
    def check_by_resource_type(self, resource_type, progress_callback=None):
        """РџСЂРѕРІРµСЂРєР° РѕРїСЂРµРґРµР»РµРЅРЅРѕРіРѕ С‚РёРїР° СЂРµСЃСѓСЂСЃРѕРІ РЅР° РІСЃРµС… СЃРµСЂРІРµСЂР°С…"""
        try:
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            
            results = []
            total = len(servers)
            
            for i, server in enumerate(servers):
                if progress_callback:
                    progress = (i + 1) / total * 100
                    progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server['name']}...")
                
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
            
            # РЎРѕСЂС‚РёСЂРѕРІРєР° РїРѕ СѓР±С‹РІР°РЅРёСЋ Р·РЅР°С‡РµРЅРёСЏ
            results.sort(key=lambda x: x["value"], reverse=True)
            return results
            
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃР° {resource_type}: {e}")
            return []
    
    def get_resource_history(self, server_ip, limit=10):
        """РџРѕР»СѓС‡РёС‚СЊ РёСЃС‚РѕСЂРёСЋ СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂР°"""
        return self.resource_history.get(server_ip, [])[-limit:]
    
    def start_automatic_checks(self):
        """Р—Р°РїСѓСЃРє Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёС… РїСЂРѕРІРµСЂРѕРє СЂРµСЃСѓСЂСЃРѕРІ"""
        debug_log("рџ”„ Р—Р°РїСѓСЃРє Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёС… РїСЂРѕРІРµСЂРѕРє СЂРµСЃСѓСЂСЃРѕРІ")
        
        while True:
            current_time = datetime.now()
            
            # РџСЂРѕРІРµСЂСЏРµРј РёРЅС‚РµСЂРІР°Р»
            if (current_time - self.last_resource_check).total_seconds() >= RESOURCE_CHECK_INTERVAL:
                debug_log("рџ”Ќ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ...")
                self.perform_automatic_check()
                self.last_resource_check = current_time
            
            time.sleep(60)  # РџСЂРѕРІРµСЂСЏРµРј РєР°Р¶РґСѓСЋ РјРёРЅСѓС‚Сѓ
    
    def perform_automatic_check(self):
        """Р’С‹РїРѕР»РЅРµРЅРёРµ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕР№ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ"""
        try:
            results = self.check_all_resources()
            
            # РђРЅР°Р»РёР· СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ Рё РѕС‚РїСЂР°РІРєР° Р°Р»РµСЂС‚РѕРІ
            alerts = []
            for result in results:
                if result["success"] and result["resources"]:
                    server_alerts = self.check_resource_alerts(
                        result["server"]["ip"],
                        result["resources"]
                    )
                    if server_alerts:
                        alerts.extend(server_alerts)
            
            # РћС‚РїСЂР°РІРєР° Р°Р»РµСЂС‚РѕРІ РµСЃР»Рё РµСЃС‚СЊ
            if alerts:
                self.send_resource_alerts(alerts)
                
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕР№ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ: {e}")
    
    def check_resource_alerts(self, ip, resources):
        """РџСЂРѕРІРµСЂРєР° СѓСЃР»РѕРІРёР№ РґР»СЏ Р°Р»РµСЂС‚РѕРІ"""
        alerts = []
        
        # РџСЂРѕРІРµСЂРєР° Disk (РѕРґРЅР° РїСЂРѕРІРµСЂРєР°)
        disk_usage = resources.get('disk', 0)
        if disk_usage >= RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
            alert_key = f"{ip}_disk"
            if alert_key not in self.resource_alerts_sent or \
               (datetime.now() - self.resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
                alerts.append(f"рџ’ѕ **Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ** РЅР° СЃРµСЂРІРµСЂРµ: {disk_usage}%")
                self.resource_alerts_sent[alert_key] = datetime.now()
        
        # Р—РґРµСЃСЊ РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РїСЂРѕРІРµСЂРєРё CPU Рё RAM
        
        return alerts
    
    def send_resource_alerts(self, alerts):
        """РћС‚РїСЂР°РІРєР° Р°Р»РµСЂС‚РѕРІ РїРѕ СЂРµСЃСѓСЂСЃР°Рј"""
        if not alerts:
            return
            
        message = "рџљЁ *РџСЂРѕР±Р»РµРјС‹ СЃ СЂРµСЃСѓСЂСЃР°РјРё СЃРµСЂРІРµСЂРѕРІ*\n\n"
        message += "\n".join(alerts)
        message += f"\nвЏ° Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё: {datetime.now().strftime('%H:%M:%S')}"
        
        from bot.handlers.commands import send_alert
        send_alert(message)

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЂРµСЃСѓСЂСЃРѕРІ
resource_monitor = ResourceMonitor()


class ResourcesChecker:
    """РЈС‚РёР»РёС‚С‹ РґР»СЏ СЂР°Р·РѕРІС‹С… РїСЂРѕРІРµСЂРѕРє СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ."""

    def __init__(self):
        self.resource_history = {}
        self.resource_alerts_sent = {}

    def check_server_resources(self, server):
        """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°."""
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
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ {server.get('name')}: {e}")
            return False, None

    def check_multiple_resources(self, servers, progress_callback=None):
        """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РЅРµСЃРєРѕР»СЊРєРёС… СЃРµСЂРІРµСЂРѕРІ."""
        results = []
        total = len(servers)
        success_count = 0

        for index, server in enumerate(servers):
            if progress_callback:
                progress = (index + 1) / total * 100 if total else 100
                progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server.get('name', 'СЃРµСЂРІРµСЂ')}...")

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
        """РџСЂРѕРІРµСЂСЏРµС‚ СѓСЃР»РѕРІРёСЏ РґР»СЏ РѕС‚РїСЂР°РІРєРё Р°Р»РµСЂС‚РѕРІ РїРѕ СЂРµСЃСѓСЂСЃР°Рј."""
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
                    f"рџ’ѕ **Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ** РЅР° {server_name}: {disk_usage}% "
                    f"(РїСЂРµРІС‹С€РµРЅ РїРѕСЂРѕРі {RESOURCE_ALERT_THRESHOLDS['disk_alert']}%)"
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
                        f"рџ’» **РџСЂРѕС†РµСЃСЃРѕСЂ** РЅР° {server_name}: {prev_cpu}% в†’ {cpu_usage}% "
                        f"(2 РїСЂРѕРІРµСЂРєРё РїРѕРґСЂСЏРґ >= {RESOURCE_ALERT_THRESHOLDS['cpu_alert']}%)"
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
                        f"рџ§  **РџР°РјСЏС‚СЊ** РЅР° {server_name}: {prev_ram}% в†’ {ram_usage}% "
                        f"(2 РїСЂРѕРІРµСЂРєРё РїРѕРґСЂСЏРґ >= {RESOURCE_ALERT_THRESHOLDS['ram_alert']}%)"
                    )
                    self.resource_alerts_sent[alert_key] = current_time

        return alerts


# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ С‡РµРєРµСЂР° СЂРµСЃСѓСЂСЃРѕРІ
resources_checker = ResourcesChecker()
