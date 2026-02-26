"""
/app/modules/targeted_checks.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server Spot Check Module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ С‚РѕС‡РµС‡РЅС‹С… РїСЂРѕРІРµСЂРѕРє СЃРµСЂРІРµСЂРѕРІ
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lib.common import debug_log
from lib.helpers import progress_bar

class TargetedChecks:
    """РљР»Р°СЃСЃ РґР»СЏ С‚РѕС‡РµС‡РЅС‹С… РїСЂРѕРІРµСЂРѕРє СЃРµСЂРІРµСЂРѕРІ"""
    
    def __init__(self):
        self.server_cache = None
    
    def get_all_servers(self):
        """РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ СЃРµСЂРІРµСЂС‹ СЃ РєСЌС€РёСЂРѕРІР°РЅРёРµРј"""
        if self.server_cache is None:
            from extensions.server_checks import initialize_servers
            self.server_cache = initialize_servers()
        return self.server_cache
    
    def get_server_by_selection(self, server_id):
        """РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂ РїРѕ ID (ip РёР»Рё name)"""
        servers = self.get_all_servers()
        
        # РџРѕРёСЃРє РїРѕ IP
        for server in servers:
            if server["ip"] == server_id:
                return server
        
        # РџРѕРёСЃРє РїРѕ РёРјРµРЅРё
        for server in servers:
            if server["name"].lower() == server_id.lower():
                return server
        
        return None
    
    def check_single_server_availability(self, server_ip_or_name):
        """РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        try:
            server = self.get_server_by_selection(server_ip_or_name)
            if not server:
                return False, None, f"вќЊ РЎРµСЂРІРµСЂ '{server_ip_or_name}' РЅРµ РЅР°Р№РґРµРЅ"
            
            from extensions.server_checks import check_server_availability
            is_up = check_server_availability(server)
            
            if is_up:
                return True, server, f"вњ… РЎРµСЂРІРµСЂ {server['name']} ({server['ip']}) РґРѕСЃС‚СѓРїРµРЅ"
            else:
                return False, server, f"рџ”ґ РЎРµСЂРІРµСЂ {server['name']} ({server['ip']}) РЅРµРґРѕСЃС‚СѓРїРµРЅ"
                
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂР° {server_ip_or_name}: {e}")
            return False, None, f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё: {str(e)[:100]}"
    
    def check_single_server_resources(self, server_ip_or_name):
        """РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        try:
            server = self.get_server_by_selection(server_ip_or_name)
            if not server:
                return None, None, f"вќЊ РЎРµСЂРІРµСЂ '{server_ip_or_name}' РЅРµ РЅР°Р№РґРµРЅ"
            
            if server["type"] == "ssh":
                from extensions.server_checks import get_linux_resources_improved
                resources = get_linux_resources_improved(server["ip"])
            elif server["type"] == "rdp":
                from extensions.server_checks import get_windows_resources_improved
                resources = get_windows_resources_improved(server["ip"])
            else:
                resources = None
            
            if resources:
                # Р¤РѕСЂРјР°С‚РёСЂСѓРµРј СЃРѕРѕР±С‰РµРЅРёРµ
                message = f"рџ“Љ **Р РµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР° {server['name']} ({server['ip']})**\n\n"
                message += f"вЂў CPU: {resources.get('cpu', 0)}%\n"
                message += f"вЂў RAM: {resources.get('ram', 0)}%\n"
                message += f"вЂў Disk: {resources.get('disk', 0)}%\n"
                message += f"вЂў РњРµС‚РѕРґ РґРѕСЃС‚СѓРїР°: {resources.get('access_method', 'РЅРµРёР·РІРµСЃС‚РЅРѕ')}\n"
                message += f"вЂў Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё: {resources.get('timestamp', 'N/A')}\n"
                
                # РџСЂРѕРІРµСЂРєР° РїРѕСЂРѕРіРѕРІ
                from config.db_settings import RESOURCE_THRESHOLDS
                alerts = []
                
                cpu = resources.get('cpu', 0)
                ram = resources.get('ram', 0)
                disk = resources.get('disk', 0)
                
                if cpu >= RESOURCE_THRESHOLDS["cpu_critical"]:
                    alerts.append(f"рџљЁ CPU: {cpu}% (РєСЂРёС‚РёС‡РЅРѕ)")
                elif cpu >= RESOURCE_THRESHOLDS["cpu_warning"]:
                    alerts.append(f"вљ пёЏ CPU: {cpu}% (РІС‹СЃРѕРєР°СЏ РЅР°РіСЂСѓР·РєР°)")
                
                if ram >= RESOURCE_THRESHOLDS["ram_critical"]:
                    alerts.append(f"рџљЁ RAM: {ram}% (РєСЂРёС‚РёС‡РЅРѕ)")
                elif ram >= RESOURCE_THRESHOLDS["ram_warning"]:
                    alerts.append(f"вљ пёЏ RAM: {ram}% (РјР°Р»Рѕ СЃРІРѕР±РѕРґРЅРѕР№ РїР°РјСЏС‚Рё)")
                
                if disk >= RESOURCE_THRESHOLDS["disk_critical"]:
                    alerts.append(f"рџљЁ Disk: {disk}% (РєСЂРёС‚РёС‡РЅРѕ)")
                elif disk >= RESOURCE_THRESHOLDS["disk_warning"]:
                    alerts.append(f"вљ пёЏ Disk: {disk}% (РјР°Р»Рѕ РјРµСЃС‚Р°)")
                
                if alerts:
                    message += "\n**вљ пёЏ РџСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ:**\n"
                    for alert in alerts:
                        message += f"вЂў {alert}\n"
                
                return True, server, message
            else:
                return False, server, f"вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕР»СѓС‡РёС‚СЊ СЂРµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР° {server['name']}"
                
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ {server_ip_or_name}: {e}")
            return False, None, f"вќЊ РћС€РёР±РєР°: {str(e)[:100]}"
    
    def create_server_selection_menu(self, action="check_availability"):
        """РЎРѕР·РґР°РµС‚ РјРµРЅСЋ РІС‹Р±РѕСЂР° СЃРµСЂРІРµСЂР°"""
        servers = self.get_all_servers()
        
        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј
        servers_by_type = {}
        for server in servers:
            server_type = server["type"]
            if server_type not in servers_by_type:
                servers_by_type[server_type] = []
            servers_by_type[server_type].append(server)
        
        # РЎРѕР·РґР°РµРј РєР»Р°РІРёР°С‚СѓСЂСѓ
        keyboard = []
        
        # Р”РѕР±Р°РІР»СЏРµРј СЃРµСЂРІРµСЂС‹ РїРѕ С‚РёРїР°Рј
        for server_type, type_servers in servers_by_type.items():
            # Р—Р°РіРѕР»РѕРІРѕРє С‚РёРїР°
            type_name = {
                "rdp": "рџЄџ Windows",
                "ssh": "рџђ§ Linux/SSH", 
                "ping": "рџ“Ў Ping-СЃРµСЂРІРµСЂС‹"
            }.get(server_type, server_type.upper())
            
            keyboard.append([InlineKeyboardButton(
                f"в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ {type_name} ({len(type_servers)}) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ",
                callback_data=f"server_type_{server_type}"
            )])
            
            # Р”РѕР±Р°РІР»СЏРµРј СЃРµСЂРІРµСЂС‹ СЌС‚РѕРіРѕ С‚РёРїР° (РїРѕ 2 РІ СЂСЏРґ)
            row = []
            for i, server in enumerate(type_servers):
                button_text = f"{server['name'][:15]}"
                callback_data = f"{action}_{server['ip']}"
                
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                
                if len(row) == 2 or i == len(type_servers) - 1:
                    keyboard.append(row)
                    row = []
        
        # РљРЅРѕРїРєРё РЅР°РІРёРіР°С†РёРё
        keyboard.append([
            InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ СЃРїРёСЃРѕРє", callback_data=f"refresh_{action}_menu"),
            InlineKeyboardButton("рџ”Ќ РџРѕРёСЃРє СЃРµСЂРІРµСЂР°", callback_data=f"search_{action}")
        ])
        
        keyboard.append([
            InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data="main_menu"),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data="close")
        ])
        
        return InlineKeyboardMarkup(keyboard)

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ
targeted_checks = TargetedChecks()
