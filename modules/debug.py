"""
/app/modules/debug.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Debugging and diagnostics module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ РѕС‚Р»Р°РґРєРё Рё РґРёР°РіРЅРѕСЃС‚РёРєРё
"""

import subprocess
import socket
import logging
from datetime import datetime
from pathlib import Path
from lib.logging import debug_log
from config.db_settings import (
    DATA_DIR,
    DEBUG_LOG_FILE,
    BOT_DEBUG_LOG_FILE,
    MAIL_MONITOR_LOG_FILE,
)

class DebugManager:
    """РљР»Р°СЃСЃ СѓРїСЂР°РІР»РµРЅРёСЏ РѕС‚Р»Р°РґРєРѕР№ Рё РґРёР°РіРЅРѕСЃС‚РёРєРѕР№"""
    
    def __init__(self):
        self.debug_config = None
        self.load_debug_config()
    
    def load_debug_config(self):
        """Р—Р°РіСЂСѓР·РєР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё РѕС‚Р»Р°РґРєРё"""
        try:
            from config.debug_app import debug_config
            self.debug_config = debug_config
        except ImportError:
            debug_log("вљ пёЏ РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РѕС‚Р»Р°РґРєРё РЅРµРґРѕСЃС‚СѓРїРЅР°", force=True)
            self.debug_config = None
    
    def get_system_status(self):
        """РџРѕР»СѓС‡РµРЅРёРµ СЃС‚Р°С‚СѓСЃР° СЃРёСЃС‚РµРјС‹"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "resources": {},
            "processes": {},
            "logs": {}
        }
        
        # РџСЂРѕРІРµСЂРєР° СЃРµСЂРІРёСЃРѕРІ
        services = [
            ("SSH", "localhost", 22),
            ("Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ", "192.168.20.2", 5000),
            ("Р‘Р°Р·Р° РґР°РЅРЅС‹С…", "localhost", None)
        ]
        
        for name, host, port in services:
            try:
                if port:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    status["services"][name] = "рџџў" if result == 0 else "рџ”ґ"
                else:
                    # РџСЂРѕРІРµСЂРєР° С„Р°Р№Р»Р° Р±Р°Р·С‹
                    db_path = DATA_DIR / 'backups.db'
                    status["services"][name] = "рџџў" if db_path.exists() else "рџ”ґ"
            except Exception as e:
                status["services"][name] = f"рџ”ґ ({str(e)[:30]})"
        
        # РџСЂРѕРІРµСЂРєР° РїСЂРѕС†РµСЃСЃРѕРІ
        processes = ["python3", "main.py", "improved_mail_monitor.py"]
        for process in processes:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', process],
                    capture_output=True,
                    text=True
                )
                running = len(result.stdout.strip().split('\n')) > 0 and result.stdout.strip() != ''
                status["processes"][process] = "рџџў" if running else "рџ”ґ"
            except Exception as e:
                status["processes"][process] = "рџ”ґ"
        
        # РџСЂРѕРІРµСЂРєР° Р»РѕРіРѕРІ
        log_files = {
            'debug.log': DEBUG_LOG_FILE,
            'bot_debug.log': BOT_DEBUG_LOG_FILE,
        }
        
        for name, path in log_files.items():
            try:
                log_path = Path(path)
                if log_path.exists():
                    size = log_path.stat().st_size / 1024 / 1024
                    status["logs"][name] = f"{size:.2f} MB"
                else:
                    status["logs"][name] = "С„Р°Р№Р» РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚"
            except Exception as e:
                status["logs"][name] = "РѕС€РёР±РєР° РїСЂРѕРІРµСЂРєРё"
        
        return status
    
    def diagnose_server_connection(self, server_ip):
        """Р”РёР°РіРЅРѕСЃС‚РёРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє СЃРµСЂРІРµСЂСѓ"""
        try:
            from extensions.server_checks import get_server_by_ip
            server = get_server_by_ip(server_ip)
            
            if not server:
                return f"вќЊ РЎРµСЂРІРµСЂ {server_ip} РЅРµ РЅР°Р№РґРµРЅ РІ СЃРїРёСЃРєРµ"
            
            result = {
                "server": f"{server['name']} ({server_ip})",
                "type": server["type"],
                "checks": {}
            }
            
            # РџСЂРѕРІРµСЂРєР° ping
            from extensions.server_checks import check_ping
            result["checks"]["ping"] = "рџџў OK" if check_ping(server_ip) else "рџ”ґ FAIL"
            
            # РџСЂРѕРІРµСЂРєР° РїРѕСЂС‚РѕРІ РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ С‚РёРїР°
            if server["type"] == "ssh":
                from extensions.server_checks import check_port
                result["checks"]["ssh_port"] = "рџџў OK" if check_port(server_ip, 22) else "рџ”ґ FAIL"
            
            elif server["type"] == "rdp":
                from extensions.server_checks import check_port
                result["checks"]["rdp_port"] = "рџџў OK" if check_port(server_ip, 3389) else "рџ”ґ FAIL"
                result["checks"]["winrm_port"] = "рџџў OK" if check_port(server_ip, 5985) else "рџ”ґ FAIL"
            
            # Р¤РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёРµ СЂРµР·СѓР»СЊС‚Р°С‚Р°
            message = f"рџ”§ *Р”РёР°РіРЅРѕСЃС‚РёРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ*\n\n"
            message += f"**РЎРµСЂРІРµСЂ:** {result['server']}\n"
            message += f"**РўРёРї:** {result['type']}\n\n"
            message += "**РџСЂРѕРІРµСЂРєРё:**\n"
            
            for check_name, check_result in result["checks"].items():
                message += f"вЂў {check_name}: {check_result}\n"
            
            return message
            
        except Exception as e:
            return f"вќЊ РћС€РёР±РєР° РґРёР°РіРЅРѕСЃС‚РёРєРё: {str(e)[:100]}"
    
    def clear_logs(self):
        """РћС‡РёСЃС‚РєР° Р»РѕРіРѕРІ"""
        log_files = [
            DEBUG_LOG_FILE,
            BOT_DEBUG_LOG_FILE,
            MAIL_MONITOR_LOG_FILE,
        ]
        
        cleared = 0
        errors = []
        
        for log_file in log_files:
            try:
                log_file = Path(log_file)
                if log_file.exists():
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
                else:
                    # РЎРѕР·РґР°РµРј РїСѓСЃС‚РѕР№ С„Р°Р№Р» РµСЃР»Рё РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
            except Exception as e:
                errors.append(f"{Path(log_file).name}: {str(e)[:50]}")
        
        return cleared, errors
    
    def toggle_debug_mode(self, enable=True):
        """РџРµСЂРµРєР»СЋС‡РµРЅРёРµ СЂРµР¶РёРјР° РѕС‚Р»Р°РґРєРё"""
        if not self.debug_config:
            return False, "РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РѕС‚Р»Р°РґРєРё РЅРµРґРѕСЃС‚СѓРїРЅР°"
        
        try:
            if enable:
                self.debug_config.enable_debug()
                logging.getLogger().setLevel(logging.DEBUG)
                return True, "рџџў РћС‚Р»Р°РґРєР° РІРєР»СЋС‡РµРЅР°"
            else:
                self.debug_config.disable_debug()
                logging.getLogger().setLevel(logging.INFO)
                return True, "рџ”ґ РћС‚Р»Р°РґРєР° РІС‹РєР»СЋС‡РµРЅР°"
        except Exception as e:
            return False, f"РћС€РёР±РєР°: {str(e)}"
    
    def get_debug_info(self):
        """РџРѕР»СѓС‡РµРЅРёРµ РёРЅС„РѕСЂРјР°С†РёРё РѕР± РѕС‚Р»Р°РґРєРµ"""
        if not self.debug_config:
            return {"error": "РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РѕС‚Р»Р°РґРєРё РЅРµРґРѕСЃС‚СѓРїРЅР°"}
        
        return self.debug_config.get_debug_info()

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РјРµРЅРµРґР¶РµСЂР° РѕС‚Р»Р°РґРєРё
debug_manager = DebugManager()
