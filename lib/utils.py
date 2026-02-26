"""
/lib/utils.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utility functions
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Рµ С„СѓРЅРєС†РёРё
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import importlib

def safe_import(module_name: str, class_name: Optional[str] = None) -> Any:
    """
    Р‘РµР·РѕРїР°СЃРЅС‹Р№ РёРјРїРѕСЂС‚ РјРѕРґСѓР»РµР№ СЃ РѕР±СЂР°Р±РѕС‚РєРѕР№ РѕС€РёР±РѕРє
    
    Args:
        module_name: РРјСЏ РјРѕРґСѓР»СЏ
        class_name: РРјСЏ РєР»Р°СЃСЃР° (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)
        
    Returns:
        РРјРїРѕСЂС‚РёСЂРѕРІР°РЅРЅС‹Р№ РјРѕРґСѓР»СЊ РёР»Рё РєР»Р°СЃСЃ, РёР»Рё None РїСЂРё РѕС€РёР±РєРµ
    """
    try:
        module = importlib.import_module(module_name)
        if class_name:
            return getattr(module, class_name)
        return module
    except ImportError as e:
        from lib.logging import debug_log
        debug_log(f"Import error for {module_name}: {e}", force=True)
        return None
    except AttributeError as e:
        from lib.logging import debug_log
        debug_log(f"Attribute error for {module_name}.{class_name}: {e}", force=True)
        return None

def format_duration(seconds: int) -> str:
    """
    Р¤РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёРµ РґР»РёС‚РµР»СЊРЅРѕСЃС‚Рё РІ С‡РёС‚Р°РµРјС‹Р№ РІРёРґ
    
    Args:
        seconds: РљРѕР»РёС‡РµСЃС‚РІРѕ СЃРµРєСѓРЅРґ
        
    Returns:
        РћС‚С„РѕСЂРјР°С‚РёСЂРѕРІР°РЅРЅР°СЏ СЃС‚СЂРѕРєР°
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:02d}s"
    else:
        return f"{seconds}s"

def progress_bar(percentage: float, width: int = 20) -> str:
    """
    РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ РїСЂРѕРіСЂРµСЃСЃ-Р±Р°СЂ
    
    Args:
        percentage: РџСЂРѕС†РµРЅС‚ Р·Р°РІРµСЂС€РµРЅРёСЏ (0-100)
        width: РЁРёСЂРёРЅР° РїСЂРѕРіСЂРµСЃСЃ1Р±Р°СЂР° РІ СЃРёРјРІРѕР»Р°С…
        
    Returns:
        РЎС‚СЂРѕРєР° СЃ РїСЂРѕРіСЂРµСЃСЃ1Р±Р°СЂРѕРј
    """
    filled = int(round(width * percentage / 100))
    bar = f"[{'в–€' * filled}{'в–‘' * (width - filled)}] {percentage:.1f}%"
    return bar

def is_proxmox_server(ip: str) -> bool:
    """
    РџСЂРѕРІРµСЂСЏРµС‚, СЏРІР»СЏРµС‚СЃСЏ Р»Рё СЃРµСЂРІРµСЂ Proxmox
    
    Args:
        ip: IP Р°РґСЂРµСЃ
        
    Returns:
        True РµСЃР»Рё СЃРµСЂРІРµСЂ Proxmox
    """
    return (ip.startswith("192.168.30.") or
           ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])

def parse_time_string(time_str: str) -> datetime.time:
    """
    РџР°СЂСЃРёС‚ СЃС‚СЂРѕРєСѓ РІСЂРµРјРµРЅРё РІ С„РѕСЂРјР°С‚Рµ HH:MM
    
    Args:
        time_str: РЎС‚СЂРѕРєР° РІСЂРµРјРµРЅРё (РЅР°РїСЂРёРјРµСЂ, "08:30")
        
    Returns:
        РћР±СЉРµРєС‚ datetime.time
    """
    from datetime import time
    try:
        hours, minutes = map(int, time_str.split(':'))
        return time(hours, minutes)
    except (ValueError, AttributeError):
        return time(8, 30)  # Р—РЅР°С‡РµРЅРёРµ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ

def get_size_string(size_bytes: int) -> str:
    """
    РџСЂРµРѕР±СЂР°Р·СѓРµС‚ СЂР°Р·РјРµСЂ РІ Р±Р°Р№С‚Р°С… РІ С‡РёС‚Р°РµРјСѓСЋ СЃС‚СЂРѕРєСѓ
    
    Args:
        size_bytes: Р Р°Р·РјРµСЂ РІ Р±Р°Р№С‚Р°С…
        
    Returns:
        Р§РёС‚Р°РµРјР°СЏ СЃС‚СЂРѕРєР° (РЅР°РїСЂРёРјРµСЂ, "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"