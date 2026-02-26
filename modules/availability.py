"""
/app/modules/availability.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server Availability Monitoring Module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё СЃРµСЂРІРµСЂРѕРІ
"""

import threading
import time
from datetime import datetime, timedelta
from config.db_settings import CHECK_INTERVAL, MAX_FAIL_TIME
from lib.logging import debug_log

# РРјРїРѕСЂС‚РёСЂСѓРµРј РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ
try:
    from extensions.server_checks import initialize_servers, check_server_availability
except ImportError:
    debug_log("вљ пёЏ РњРѕРґСѓР»СЊ server_checks РЅРµРґРѕСЃС‚СѓРїРµРЅ", force=True)
    check_server_availability = None

class AvailabilityMonitor:
    """РљР»Р°СЃСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё СЃРµСЂРІРµСЂРѕРІ"""
    
    def __init__(self):
        self.server_status = {}
        self.monitoring_active = True
        self.servers = []
        self.last_check_time = datetime.now()
        
    def initialize(self):
        """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
        if not check_server_availability:
            debug_log("вќЊ РњРѕРґСѓР»СЊ РїСЂРѕРІРµСЂРѕРє РЅРµРґРѕСЃС‚СѓРїРµРЅ", force=True)
            return False
            
        self.servers = initialize_servers()
        monitor_server_ip = "192.168.20.2"
        
        # РСЃРєР»СЋС‡Р°РµРј СЃРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
        self.servers = [s for s in self.servers if s["ip"] != monitor_server_ip]
        
        # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ СЃС‚Р°С‚СѓСЃРѕРІ
        for server in self.servers:
            self.server_status[server["ip"]] = {
                "last_up": datetime.now(),
                "alert_sent": False,
                "name": server["name"],
                "type": server["type"]
            }
            
        debug_log(f"вњ… РњРѕРЅРёС‚РѕСЂРёРЅРі РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ РґР»СЏ {len(self.servers)} СЃРµСЂРІРµСЂРѕРІ")
        return True
        
    def check_server(self, server):
        """РџСЂРѕРІРµСЂРєР° РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        try:
            return check_server_availability(server)
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё {server['name']}: {e}")
            return False
            
    def handle_server_up(self, ip, status, current_time):
        """РћР±СЂР°Р±РѕС‚РєР° РґРѕСЃС‚СѓРїРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        if status["alert_sent"]:
            downtime = (current_time - status["last_up"]).total_seconds()
            from bot.handlers.commands import send_alert
            send_alert(f"вњ… {status['name']} ({ip}) РґРѕСЃС‚СѓРїРµРЅ (РїСЂРѕСЃС‚РѕР№: {int(downtime//60)} РјРёРЅ)")

        self.server_status[ip] = {
            "last_up": current_time,
            "alert_sent": False,
            "name": status["name"],
            "type": status["type"]
        }

    def handle_server_down(self, ip, status, current_time):
        """РћР±СЂР°Р±РѕС‚РєР° РЅРµРґРѕСЃС‚СѓРїРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        downtime = (current_time - status["last_up"]).total_seconds()
        
        if downtime >= MAX_FAIL_TIME and not status["alert_sent"]:
            from bot.handlers.commands import send_alert
            send_alert(f"рџљЁ {status['name']} ({ip}) РЅРµ РѕС‚РІРµС‡Р°РµС‚ (РїСЂРѕРІРµСЂРєР°: {status['type'].upper()})")
            self.server_status[ip]["alert_sent"] = True
    
    def get_current_status(self):
        """РџРѕР»СѓС‡РёС‚СЊ С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ"""
        results = {"failed": [], "ok": []}
        if not self.servers:
            if not self.initialize():
                debug_log("вќЊ РќРµС‚ РґР°РЅРЅС‹С… Рѕ СЃРµСЂРІРµСЂР°С… РґР»СЏ РїСЂРѕРІРµСЂРєРё", force=True)
                return results

        for server in self.servers:
            try:
                is_up = self.check_server(server)
                if is_up:
                    results["ok"].append(server)
                else:
                    results["failed"].append(server)
            except Exception as e:
                debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё {server['name']}: {e}")
                results["failed"].append(server)
                
        return results
    
    def start_monitoring(self):
        """Р—Р°РїСѓСЃРє С†РёРєР»Р° РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
        if not self.initialize():
            debug_log("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё", force=True)
            return
            
        debug_log("рџ”„ Р—Р°РїСѓСЃРє С†РёРєР»Р° РјРѕРЅРёС‚РѕСЂРёРЅРіР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё")
        
        while True:
            if self.monitoring_active:
                self.last_check_time = datetime.now()
                
                for server in self.servers:
                    try:
                        ip = server["ip"]
                        status = self.server_status.get(ip, {})
                        
                        # РСЃРєР»СЋС‡Р°РµРј СЃРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
                        if ip == "192.168.20.2":
                            self.server_status[ip]["last_up"] = self.last_check_time
                            continue
                            
                        is_up = self.check_server(server)
                        
                        if is_up:
                            self.handle_server_up(ip, status, self.last_check_time)
                        else:
                            self.handle_server_down(ip, status, self.last_check_time)
                            
                    except Exception as e:
                        debug_log(f"вќЊ РћС€РёР±РєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° {server['name']}: {e}")
                        
            time.sleep(CHECK_INTERVAL)

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
availability_monitor = AvailabilityMonitor()


class AvailabilityChecker:
    """РЈС‚РёР»РёС‚С‹ РґР»СЏ СЂР°Р·РѕРІС‹С… РїСЂРѕРІРµСЂРѕРє РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё."""

    def __init__(self):
        self.last_check_time = None

    def check_single_server(self, server):
        """РџСЂРѕРІРµСЂСЏРµС‚ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°."""
        if not check_server_availability:
            debug_log("вќЊ РњРѕРґСѓР»СЊ РїСЂРѕРІРµСЂРѕРє РЅРµРґРѕСЃС‚СѓРїРµРЅ", force=True)
            return False

        try:
            return check_server_availability(server)
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё {server.get('name')}: {e}")
            return False

    def check_multiple_servers(self, servers, progress_callback=None):
        """РџСЂРѕРІРµСЂСЏРµС‚ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ РЅРµСЃРєРѕР»СЊРєРёС… СЃРµСЂРІРµСЂРѕРІ."""
        results = {"up": [], "down": [], "ok": [], "failed": []}
        total = len(servers)

        for index, server in enumerate(servers):
            if progress_callback:
                progress = (index + 1) / total * 100 if total else 100
                progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server.get('name', 'СЃРµСЂРІРµСЂ')}...")

            is_up = self.check_single_server(server)
            if is_up:
                results["up"].append(server)
                results["ok"].append(server)
            else:
                results["down"].append(server)
                results["failed"].append(server)

        self.last_check_time = datetime.now()
        return results


# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ С‡РµРєРµСЂР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
availability_checker = AvailabilityChecker()
