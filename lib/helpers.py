"""
/lib/helpers.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Auxiliary utilities
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Рµ СѓС‚РёР»РёС‚С‹
"""

import warnings

def progress_bar(percentage, width=20):
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ РїСЂРѕРіСЂРµСЃСЃ-Р±Р°СЂ"""
    filled = int(round(width * percentage / 100))
    bar = f"[{'в–€' * filled}{'в–‘' * (width - filled)}] {percentage:.1f}%"
    return bar

def format_duration(seconds):
    """Р¤РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёРµ РґР»РёС‚РµР»СЊРЅРѕСЃС‚Рё РІ С‡РёС‚Р°РµРјС‹Р№ РІРёРґ"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:02d}s"
    else:
        return f"{seconds}s"

def is_proxmox_server(ip):
    """РџСЂРѕРІРµСЂСЏРµС‚, СЏРІР»СЏРµС‚СЃСЏ Р»Рё СЃРµСЂРІРµСЂ Proxmox (СѓСЃС‚Р°СЂРµРІС€Р°СЏ РѕР±РµСЂС‚РєР°)."""
    warnings.warn(
        "lib.helpers.is_proxmox_server СѓСЃС‚Р°СЂРµР»Р°; РёСЃРїРѕР»СЊР·СѓР№С‚Рµ lib.utils.is_proxmox_server.",
        DeprecationWarning,
        stacklevel=2,
    )
    from lib.utils import is_proxmox_server as _is_proxmox_server
    return _is_proxmox_server(ip)
