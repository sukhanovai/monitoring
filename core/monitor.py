"""
/core/monitor.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core monitoring module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РћСЃРЅРѕРІРЅРѕР№ РјРѕРґСѓР»СЊ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
"""

import time
import threading
from datetime import datetime
from typing import Dict, List

from lib.logging import debug_log
from lib.alerts import send_alert, is_silent_time as alerts_is_silent_time
from config import (
    CHECK_INTERVAL,
    MAX_FAIL_TIME,
    RESOURCE_CHECK_INTERVAL,
    DATA_COLLECTION_TIME,
    SILENT_START,
    SILENT_END,
)
from modules.resources import resources_checker
from modules.morning_report import morning_report
from core.config_manager import config_manager

class Monitor:
    """РћСЃРЅРѕРІРЅРѕР№ РєР»Р°СЃСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    
    def __init__(self):
        """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
        self.monitoring_active = True
        self.silent_override = None
        self.server_status = {}
        self.servers = []
        self.bot = None
        
        self.last_check_time = datetime.now()
        self.last_resource_check = datetime.now()
        self.last_report_date = None
        
    def is_silent_time(self) -> bool:
        """
        РџСЂРѕРІРµСЂСЏРµС‚, РЅР°С…РѕРґРёС‚СЃСЏ Р»Рё С‚РµРєСѓС‰РµРµ РІСЂРµРјСЏ РІ 'С‚РёС…РѕРј' РїРµСЂРёРѕРґРµ
        
        Returns:
            bool: True РµСЃР»Рё С‚РёС…РёР№ СЂРµР¶РёРј
        """
        # Р•СЃР»Рё РµСЃС‚СЊ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕРµ РїРµСЂРµРѕРїСЂРµРґРµР»РµРЅРёРµ
        if self.silent_override is not None:
            return self.silent_override
        
        return alerts_is_silent_time()
    
    def load_servers(self) -> List[Dict]:
        """
        Р—Р°РіСЂСѓР¶Р°РµС‚ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
        
        Returns:
            List[Dict]: РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ
        """
        try:
            servers = config_manager.get_all_servers(include_disabled=True)
            if not servers:
                from extensions.server_checks import initialize_servers
                servers = initialize_servers()
                for server in servers:
                    server.setdefault("enabled", True)
            
            # РСЃРєР»СЋС‡Р°РµРј СЃРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
            monitor_server_ip = "192.168.20.2"
            servers = [s for s in servers if s.get("ip") != monitor_server_ip]
            
            debug_log(f"вњ… Р—Р°РіСЂСѓР¶РµРЅРѕ {len(servers)} СЃРµСЂРІРµСЂРѕРІ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°")
            return servers
            
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё СЃРµСЂРІРµСЂРѕРІ: {e}")
            return []

    def refresh_servers(self) -> None:
        """РћР±РЅРѕРІР»СЏРµС‚ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ Рё СЃС‚Р°С‚СѓСЃС‹."""
        servers = self.load_servers()
        if not servers:
            return

        self.servers = servers
        current_ips = {server.get("ip") for server in servers if server.get("ip")}
        stale_ips = [ip for ip in self.server_status if ip not in current_ips]
        for ip in stale_ips:
            self.server_status.pop(ip, None)

        self.initialize_server_status()

    def is_server_enabled(self, ip: str) -> bool:
        """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅ Р»Рё РјРѕРЅРёС‚РѕСЂРёРЅРі РґР»СЏ СЃРµСЂРІРµСЂР°."""
        try:
            return config_manager.get_server_enabled(ip)
        except Exception as e:
            debug_log(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂР° {ip}: {e}")
            return True
    
    def initialize_server_status(self) -> None:
        """РРЅРёС†РёР°Р»РёР·РёСЂСѓРµС‚ СЃС‚Р°С‚СѓСЃС‹ СЃРµСЂРІРµСЂРѕРІ"""
        for server in self.servers:
            ip = server.get("ip")
            if ip and ip not in self.server_status:
                self.server_status[ip] = {
                    "last_up": datetime.now(),
                    "alert_sent": False,
                    "name": server.get("name", ip),
                    "type": server.get("type", "unknown"),
                    "resources": None,
                    "last_alert": {},
                    "downtime_start": None,
                    "monitoring_enabled": server.get("enabled", True)
                }
        
        debug_log(f"вњ… РРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅС‹ СЃС‚Р°С‚СѓСЃС‹ РґР»СЏ {len(self.server_status)} СЃРµСЂРІРµСЂРѕРІ")
    
    def check_server_availability(self, server: Dict) -> bool:
        """
        РџСЂРѕРІРµСЂСЏРµС‚ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРµСЂР°
        
        Args:
            server: РРЅС„РѕСЂРјР°С†РёСЏ Рѕ СЃРµСЂРІРµСЂРµ
            
        Returns:
            bool: True РµСЃР»Рё СЃРµСЂРІРµСЂ РґРѕСЃС‚СѓРїРµРЅ
        """
        try:
            from extensions.server_checks import check_server_availability
            return check_server_availability(server)
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё {server.get('name')}: {e}")
            return False
    
    def handle_server_up(self, ip: str, status: Dict, current_time: datetime) -> None:
        """
        РћР±СЂР°Р±Р°С‚С‹РІР°РµС‚ РґРѕСЃС‚СѓРїРЅС‹Р№ СЃРµСЂРІРµСЂ
        
        Args:
            ip: IP СЃРµСЂРІРµСЂР°
            status: РўРµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ
            current_time: РўРµРєСѓС‰РµРµ РІСЂРµРјСЏ
        """
        if status.get("alert_sent"):
            last_up = status.get("last_up")
            downtime = 0
            if downtime_start:
                downtime = (current_time - downtime_start).total_seconds()

            message = f"вњ… {status.get('name')} ({ip}) РґРѕСЃС‚СѓРїРµРЅ"
            if downtime > 0:
                message += f" (РїСЂРѕСЃС‚РѕР№: {int(downtime // 60)} РјРёРЅ {int(downtime % 60)} СЃРµРє)"

            send_alert(message)
        
        # РћР±РЅРѕРІР»СЏРµРј СЃС‚Р°С‚СѓСЃ
        self.server_status[ip] = {
            "last_up": current_time,
            "alert_sent": False,
            "name": status.get("name"),
            "type": status.get("type"),
            "resources": self.server_status.get(ip, {}).get("resources"),
            "last_alert": self.server_status.get(ip, {}).get("last_alert", {}),
            "downtime_start": None
        }
    
    def handle_server_down(self, ip: str, status: Dict, current_time: datetime) -> bool:
        """
        РћР±СЂР°Р±Р°С‚С‹РІР°РµС‚ РЅРµРґРѕСЃС‚СѓРїРЅС‹Р№ СЃРµСЂРІРµСЂ
        """
        downtime_start = status.get("downtime_start")
        if downtime_start is None:
            downtime_start = current_time
            self.server_status[ip]["downtime_start"] = downtime_start

        downtime = (current_time - downtime_start).total_seconds()

        # РџСЂРѕРІРµСЂСЏРµРј РЅСѓР¶РЅРѕ Р»Рё РѕС‚РїСЂР°РІР»СЏС‚СЊ Р°Р»РµСЂС‚
        if downtime >= MAX_FAIL_TIME and not status.get("alert_sent"):
            message = f"рџљЁ {status.get('name')} ({ip}) РЅРµ РѕС‚РІРµС‡Р°РµС‚"
            message += f" ({int(downtime // 60)} РјРёРЅ {int(downtime % 60)} СЃРµРє)"

            send_alert(message)
            self.server_status[ip]["alert_sent"] = True
            return True

        return False
    
    def check_resources_automatically(self) -> None:
        """РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ"""
        try:
            from extensions.extension_manager import extension_manager
            if not extension_manager.is_extension_enabled('resource_monitor'):
                debug_log("вЏёпёЏ РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РїСЂРѕРїСѓС‰РµРЅР° (СЂР°СЃС€РёСЂРµРЅРёРµ РѕС‚РєР»СЋС‡РµРЅРѕ)")
                return
        except ImportError:
            pass

        if not self.monitoring_active or self.is_silent_time():
            debug_log("вЏёпёЏ РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РїСЂРѕРїСѓС‰РµРЅР° (РјРѕРЅРёС‚РѕСЂРёРЅРі РЅРµР°РєС‚РёРІРµРЅ РёР»Рё С‚РёС…РёР№ СЂРµР¶РёРј)")
            return
        
        current_time = datetime.now()
        
        # РџСЂРѕРІРµСЂСЏРµРј РёРЅС‚РµСЂРІР°Р»
        if (current_time - self.last_resource_check).total_seconds() < RESOURCE_CHECK_INTERVAL:
            return
        
        debug_log("рџ”Ќ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ...")
        
        # РџСЂРѕРІРµСЂСЏРµРј РІСЃРµ СЃРµСЂРІРµСЂС‹
        alerts_found = []
        
        for server in self.servers:
            try:
                ip = server.get("ip")
                server_name = server.get("name", ip)
                server_type = server.get("type")

                if not self.is_server_enabled(ip):
                    if ip in self.server_status:
                        self.server_status[ip]["last_up"] = current_time
                        self.server_status[ip]["alert_sent"] = False
                        self.server_status[ip]["last_alert"] = {}
                    continue

                # РџРѕР»СѓС‡Р°РµРј С‚РµРєСѓС‰РёРµ СЂРµСЃСѓСЂСЃС‹
                success, resources = resources_checker.check_server_resources(server)
                
                if success and resources:
                    # РџСЂРѕРІРµСЂСЏРµРј Р°Р»РµСЂС‚С‹
                    server_alerts = resources_checker.check_resource_alerts(ip, resources)
                    
                    if server_alerts:
                        alerts_found.extend(server_alerts)
                        debug_log(f"вљ пёЏ РќР°Р№РґРµРЅС‹ РїСЂРѕР±Р»РµРјС‹ РґР»СЏ {server_name}: {server_alerts}")
                    
                    # РЎРѕС…СЂР°РЅСЏРµРј СЂРµСЃСѓСЂСЃС‹ РІ СЃС‚Р°С‚СѓСЃ
                    if ip in self.server_status:
                        self.server_status[ip]["resources"] = resources
                
            except Exception as e:
                debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ СЂРµСЃСѓСЂСЃРѕРІ {server.get('name')}: {e}")
                continue
        
        # РћС‚РїСЂР°РІР»СЏРµРј Р°Р»РµСЂС‚С‹ РµСЃР»Рё РµСЃС‚СЊ
        if alerts_found:
            self.send_resource_alerts(alerts_found)
        
        self.last_resource_check = current_time
        debug_log(f"вњ… РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ Р·Р°РІРµСЂС€РµРЅР°. РќР°Р№РґРµРЅРѕ РїСЂРѕР±Р»РµРј: {len(alerts_found)}")
    
    def send_resource_alerts(self, alerts: List[str]) -> None:
        """
        РћС‚РїСЂР°РІР»СЏРµС‚ Р°Р»РµСЂС‚С‹ РїРѕ СЂРµСЃСѓСЂСЃР°Рј
        
        Args:
            alerts: РЎРїРёСЃРѕРє СЃРѕРѕР±С‰РµРЅРёР№ РґР»СЏ Р°Р»РµСЂС‚РѕРІ
        """
        if not alerts:
            return
        
        message = "рџљЁ *РџСЂРѕР±Р»РµРјС‹ СЃ СЂРµСЃСѓСЂСЃР°РјРё СЃРµСЂРІРµСЂРѕРІ*\n\n"
        
        # Р“СЂСѓРїРїРёСЂСѓРµРј Р°Р»РµСЂС‚С‹ РїРѕ С‚РёРїР°Рј СЂРµСЃСѓСЂСЃРѕРІ
        disk_alerts = [a for a in alerts if "рџ’ѕ" in a]
        cpu_alerts = [a for a in alerts if "рџ’»" in a]
        ram_alerts = [a for a in alerts if "рџ§ " in a]
        
        # Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ
        if disk_alerts:
            message += "рџ’ѕ **Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ:**\n"
            for alert in disk_alerts:
                parts = alert.split("РЅР° ")
                if len(parts) > 1:
                    server_info = parts[1]
                    message += f"вЂў {server_info}\n"
            message += "\n"
        
        # РџСЂРѕС†РµСЃСЃРѕСЂ
        if cpu_alerts:
            message += "рџ’» **РџСЂРѕС†РµСЃСЃРѕСЂ (CPU):**\n"
            for alert in cpu_alerts:
                parts = alert.split("РЅР° ")
                if len(parts) > 1:
                    server_info = parts[1]
                    message += f"вЂў {server_info}\n"
            message += "\n"
        
        # РџР°РјСЏС‚СЊ
        if ram_alerts:
            message += "рџ§  **РџР°РјСЏС‚СЊ (RAM):**\n"
            for alert in ram_alerts:
                parts = alert.split("РЅР° ")
                if len(parts) > 1:
                    server_info = parts[1]
                    message += f"вЂў {server_info}\n"
            message += "\n"
        
        message += f"вЏ° Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё: {datetime.now().strftime('%H:%M:%S')}"
        
        send_alert(message)
        debug_log(f"вњ… РћС‚РїСЂР°РІР»РµРЅС‹ Р°Р»РµСЂС‚С‹ РїРѕ СЂРµСЃСѓСЂСЃР°Рј: {len(alerts)} РїСЂРѕР±Р»РµРј")
    
    def check_morning_report(self) -> None:
        """РџСЂРѕРІРµСЂСЏРµС‚ Рё РѕС‚РїСЂР°РІР»СЏРµС‚ СѓС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚ РµСЃР»Рё РЅСѓР¶РЅРѕ"""
        current_time = datetime.now()
        current_time_time = current_time.time()
        
        # РџСЂРѕРІРµСЂСЏРµРј РІСЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С…
        if (current_time_time.hour == DATA_COLLECTION_TIME.hour and
            current_time_time.minute == DATA_COLLECTION_TIME.minute):
            
            # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЃРµРіРѕРґРЅСЏ РµС‰Рµ РЅРµ РѕС‚РїСЂР°РІР»СЏР»Рё РѕС‚С‡РµС‚
            today = current_time.date()
            if self.last_report_date != today:
                debug_log(f"[{current_time}] рџ”Ќ РЎРѕР±РёСЂР°РµРј РґР°РЅРЅС‹Рµ РґР»СЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°...")
                
                # РЎРѕР±РёСЂР°РµРј РґР°РЅРЅС‹Рµ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°
                morning_report.collect_morning_data(manual_call=False)

                status = morning_report.morning_data.get("status", {})
                debug_log(f"вњ… Р”Р°РЅРЅС‹Рµ СЃРѕР±СЂР°РЅС‹: {len(status.get('ok', []))} РґРѕСЃС‚СѓРїРЅРѕ")

                # РћС‚РїСЂР°РІР»СЏРµРј РѕС‚С‡РµС‚
                debug_log(f"[{current_time}] рџ“Љ РћС‚РїСЂР°РІРєР° СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°...")
                report_text = morning_report.generate_report_message()
                send_alert(report_text, force=True)
                
                self.last_report_date = today
                debug_log("вњ… РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚ РѕС‚РїСЂР°РІР»РµРЅ")
                
                # Р”РѕР±Р°РІР»СЏРµРј Р·Р°РґРµСЂР¶РєСѓ С‡С‚РѕР±С‹ РЅРµ Р·Р°РїСѓСЃРєР°С‚СЊ РїРѕРІС‚РѕСЂРЅРѕ
                time.sleep(65)
    
    def start(self) -> None:
        """Р—Р°РїСѓСЃРєР°РµС‚ РѕСЃРЅРѕРІРЅРѕР№ С†РёРєР» РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
        # Р—Р°РіСЂСѓР¶Р°РµРј СЃРµСЂРІРµСЂС‹
        self.servers = self.load_servers()
        
        if not self.servers:
            debug_log("вќЊ РќРµС‚ СЃРµСЂРІРµСЂРѕРІ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°")
            return
        
        # РРЅРёС†РёР°Р»РёР·РёСЂСѓРµРј СЃС‚Р°С‚СѓСЃС‹
        self.initialize_server_status()
        
        # РћС‚РїСЂР°РІР»СЏРµРј СЃС‚Р°СЂС‚РѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ
        try:
            from config.settings import APP_VERSION
        except Exception:
            APP_VERSION = None

        start_message = "рџџў *РњРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂРѕРІ Р·Р°РїСѓС‰РµРЅ*\n\n"
        if APP_VERSION:
            start_message += f"рџ”– *Р’РµСЂСЃРёСЏ:* {APP_VERSION}\n"
        start_message += (
            f"вЂў РЎРµСЂРІРµСЂРѕРІ РІ РјРѕРЅРёС‚РѕСЂРёРЅРіРµ: {len(self.servers)}\n"
            f"вЂў РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё: РєР°Р¶РґС‹Рµ {CHECK_INTERVAL} СЃРµРє\n"
            f"вЂў РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚: {DATA_COLLECTION_TIME.strftime('%H:%M')}\n\n"
        )

        resources_enabled = True
        try:
            from extensions.extension_manager import extension_manager
            resources_enabled = extension_manager.is_extension_enabled('resource_monitor')
        except ImportError:
            resources_enabled = True

        if resources_enabled:
            start_message += f"вЂў РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ: РєР°Р¶РґС‹Рµ {RESOURCE_CHECK_INTERVAL // 60} РјРёРЅСѓС‚\n"
        else:
            start_message += "вЂў РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ: РѕС‚РєР»СЋС‡РµРЅР°\n"
        
        # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃРµ
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('web_interface'):
                start_message += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* http://192.168.20.2:5000\n"
                start_message += "_*РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ РІ Р»РѕРєР°Р»СЊРЅРѕР№ СЃРµС‚Рё_\n"
            else:
                start_message += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* рџ”ґ РѕС‚РєР»СЋС‡РµРЅ\n"
        except ImportError:
            start_message += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* рџ”ґ РјРѕРґСѓР»СЊ РЅРµ Р·Р°РіСЂСѓР¶РµРЅ\n"
        
        send_alert(start_message)
        debug_log(f"вњ… РњРѕРЅРёС‚РѕСЂРёРЅРі Р·Р°РїСѓС‰РµРЅ РґР»СЏ {len(self.servers)} СЃРµСЂРІРµСЂРѕРІ")
        
        # РћСЃРЅРѕРІРЅРѕР№ С†РёРєР» РјРѕРЅРёС‚РѕСЂРёРЅРіР°
        while True:
            current_time = datetime.now()
            
            # РџСЂРѕРІРµСЂСЏРµРј СѓС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚
            self.check_morning_report()
            
            # РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ
            self.check_resources_automatically()
            
            # РћСЃРЅРѕРІРЅР°СЏ РїСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
            if self.monitoring_active:
                self.last_check_time = current_time

                self.refresh_servers()
                
                for server in self.servers:
                    try:
                        ip = server.get("ip")
                        if ip not in self.server_status:
                            continue
                        
                        status = self.server_status[ip]
                        
                        # РСЃРєР»СЋС‡Р°РµРј СЃРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
                        if ip == "192.168.20.2":
                            self.server_status[ip]["last_up"] = current_time
                            continue

                        monitoring_enabled = self.is_server_enabled(ip)
                        if not monitoring_enabled:
                            self.server_status[ip]["monitoring_enabled"] = False
                            continue

                        if not self.server_status[ip].get("monitoring_enabled", True):
                            self.server_status[ip]["monitoring_enabled"] = True
                            self.server_status[ip]["alert_sent"] = False
                            self.server_status[ip]["last_alert"] = {}
                        
                        # РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
                        is_up = self.check_server_availability(server)
                        
                        if is_up:
                            self.handle_server_up(ip, status, current_time)
                        else:
                            self.handle_server_down(ip, status, current_time)
                            
                    except Exception as e:
                        debug_log(f"вќЊ РћС€РёР±РєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° {server.get('name')}: {e}")
            
            # РћР¶РёРґР°РЅРёРµ РїРµСЂРµРґ СЃР»РµРґСѓСЋС‰РµР№ РїСЂРѕРІРµСЂРєРѕР№
            time.sleep(CHECK_INTERVAL)
    
    def stop(self) -> None:
        """РћСЃС‚Р°РЅР°РІР»РёРІР°РµС‚ РјРѕРЅРёС‚РѕСЂРёРЅРі"""
        self.monitoring_active = False
        debug_log("вЏёпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ")
    
    def resume(self) -> None:
        """Р’РѕР·РѕР±РЅРѕРІР»СЏРµС‚ РјРѕРЅРёС‚РѕСЂРёРЅРі"""
        self.monitoring_active = True
        debug_log("в–¶пёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РІРѕР·РѕР±РЅРѕРІР»РµРЅ")
    
    def get_status(self) -> Dict:
        """
        РџРѕР»СѓС‡Р°РµС‚ С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
        
        Returns:
            Dict: РЎС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
        """
        return {
            "monitoring_active": self.monitoring_active,
            "silent_mode": self.is_silent_time(),
            "silent_override": self.silent_override,
            "servers_count": len(self.servers),
            "server_status": self.server_status,
            "last_check_time": self.last_check_time,
            "last_resource_check": self.last_resource_check
        }

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РґР»СЏ РёРјРїРѕСЂС‚Р°
monitor = Monitor()
