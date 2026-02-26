"""
/lib/common.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
General system utilities
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РћР±С‰РёРµ СѓС‚РёР»РёС‚С‹ СЃРёСЃС‚РµРјС‹
"""

import importlib
import warnings

try:
    from config.db_settings import DEBUG_MODE
except ImportError:
    DEBUG_MODE = False
from lib.logging import setup_logging as _setup_logging, get_logger

def setup_logging():
    """РќР°СЃС‚СЂРѕР№РєР° С†РµРЅС‚СЂР°Р»РёР·РѕРІР°РЅРЅРѕРіРѕ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ"""
    return _setup_logging()

def debug_log(message, force=False):
    """Р¦РµРЅС‚СЂР°Р»РёР·РѕРІР°РЅРЅРѕРµ Р»РѕРіРёСЂРѕРІР°РЅРёРµ РѕС‚Р»Р°РґРєРё"""
    logger = get_logger(__name__)
    if DEBUG_MODE or force:
        logger.debug(message)
    else:
        logger.info(message)
        
def safe_import(module_name, class_name=None):
    """Р‘РµР·РѕРїР°СЃРЅС‹Р№ РёРјРїРѕСЂС‚ СЃ РѕР±СЂР°Р±РѕС‚РєРѕР№ РѕС€РёР±РѕРє"""
    try:
        module = importlib.import_module(module_name)
        if class_name:
            return getattr(module, class_name)
        return module
    except ImportError as e:
        debug_log(f"Import error for {module_name}: {e}")
        return None
    except AttributeError as e:
        debug_log(f"Attribute error for {module_name}.{class_name}: {e}")
        return None

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

def progress_bar(percentage, width=20):
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ РїСЂРѕРіСЂРµСЃСЃ-Р±Р°СЂ"""
    filled = int(round(width * percentage / 100))
    bar = f"[{'в–€' * filled}{'в–‘' * (width - filled)}] {percentage:.1f}%"
    return bar

def is_proxmox_server(ip):
    """РџСЂРѕРІРµСЂСЏРµС‚, СЏРІР»СЏРµС‚СЃСЏ Р»Рё СЃРµСЂРІРµСЂ Proxmox (СѓСЃС‚Р°СЂРµРІС€Р°СЏ РѕР±РµСЂС‚РєР°)."""
    warnings.warn(
        "lib.common.is_proxmox_server СѓСЃС‚Р°СЂРµР»Р°; РёСЃРїРѕР»СЊР·СѓР№С‚Рµ lib.utils.is_proxmox_server.",
        DeprecationWarning,
        stacklevel=2,
    )
    from lib.utils import is_proxmox_server as _is_proxmox_server
    return _is_proxmox_server(ip)
