"""
/lib/alerts.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified alert system
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р•РґРёРЅР°СЏ СЃРёСЃС‚РµРјР° РѕРїРѕРІРµС‰РµРЅРёР№
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime, time as dt_time
from lib.logging import debug_log, error_log, setup_logging

# Р›РѕРіРіРµСЂ РґР»СЏ СЌС‚РѕРіРѕ РјРѕРґСѓР»СЏ
_logger = setup_logging("alerts")

# Р“Р»РѕР±Р°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ
_telegram_bot = None
_chat_ids = []
_tamtam_sender = None
_silent_override: Optional[bool] = None
_alert_history: List[Dict[str, Any]] = []
_max_history_size = 1000

def configure_alerts(
    silent_start: Optional[int] = None,
    silent_end: Optional[int] = None,
    enabled: Optional[bool] = None,
    cooldown_seconds: Optional[int] = None,
    thresholds: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """
    РќР°СЃС‚СЂР°РёРІР°РµС‚ Р±Р°Р·РѕРІС‹Рµ РїР°СЂР°РјРµС‚СЂС‹ Р°Р»РµСЂС‚РѕРІ РёР· РІРЅРµС€РЅРёС… РЅР°СЃС‚СЂРѕРµРє.

    Args:
        silent_start: Р§Р°СЃ РЅР°С‡Р°Р»Р° С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°
        silent_end: Р§Р°СЃ РѕРєРѕРЅС‡Р°РЅРёСЏ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°
        enabled: Р’РєР»СЋС‡РµРЅС‹ Р»Рё Р°Р»РµСЂС‚С‹
        cooldown_seconds: РњРёРЅРёРјР°Р»СЊРЅС‹Р№ РёРЅС‚РµСЂРІР°Р» РјРµР¶РґСѓ РѕРґРёРЅР°РєРѕРІС‹РјРё Р°Р»РµСЂС‚Р°РјРё
        thresholds: РџРµСЂРµРѕРїСЂРµРґРµР»РµРЅРёРµ РїРѕСЂРѕРіРѕРІ РґР»СЏ С‚РёРїРѕРІ Р°Р»РµСЂС‚РѕРІ
    """
    if silent_start is not None:
        _config.silent_start = silent_start
    if silent_end is not None:
        _config.silent_end = silent_end
    if enabled is not None:
        _config.enabled = enabled
    if cooldown_seconds is not None:
        _config.cooldown_seconds = cooldown_seconds
    if thresholds:
        _config.thresholds.update(thresholds)

class AlertConfig:
    """РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р°Р»РµСЂС‚РѕРІ"""
    
    def __init__(self):
        self.silent_start = 20  # 20:00
        self.silent_end = 9     # 09:00
        self.enabled = True
        self.cooldown_seconds = 300  # 5 РјРёРЅСѓС‚ РјРµР¶РґСѓ РѕРґРёРЅР°РєРѕРІС‹РјРё Р°Р»РµСЂС‚Р°РјРё
        self.max_retries = 3
        self.retry_delay = 5
        
        # РџРѕСЂРѕРіРё РґР»СЏ СЂР°Р·РЅС‹С… С‚РёРїРѕРІ Р°Р»РµСЂС‚РѕРІ
        self.thresholds = {
            "critical": {"priority": 1, "always_send": True},
            "warning": {"priority": 2, "always_send": False},
            "info": {"priority": 3, "always_send": False}
        }

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё
_config = AlertConfig()

def init_telegram_bot(bot_instance, chat_ids: List[str]) -> None:
    """
    РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Telegram Р±РѕС‚Р° РґР»СЏ РѕС‚РїСЂР°РІРєРё Р°Р»РµСЂС‚РѕРІ
    
    Args:
        bot_instance: Р­РєР·РµРјРїР»СЏСЂ Telegram Р±РѕС‚Р°
        chat_ids: РЎРїРёСЃРѕРє ID С‡Р°С‚РѕРІ РґР»СЏ РѕС‚РїСЂР°РІРєРё
    """
    global _telegram_bot, _chat_ids
    _telegram_bot = bot_instance
    _chat_ids = chat_ids
    debug_log(f"Telegram Р±РѕС‚ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ РґР»СЏ {len(chat_ids)} С‡Р°С‚РѕРІ")



def init_tamtam_sender(sender) -> None:
    """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ РѕС‚РїСЂР°РІС‰РёРєР° TamTam РґР»СЏ Р°Р»РµСЂС‚РѕРІ."""
    global _tamtam_sender
    _tamtam_sender = sender
    debug_log("TamTam РѕС‚РїСЂР°РІС‰РёРє Р°Р»РµСЂС‚РѕРІ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ")


def set_silent_override(enabled: Optional[bool]) -> None:
    """
    РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕРµ РїРµСЂРµРѕРїСЂРµРґРµР»РµРЅРёРµ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°
    
    Args:
        enabled: None - Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЂРµР¶РёРј, True - РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ С‚РёС…РёР№, False - РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РіСЂРѕРјРєРёР№
    """
    global _silent_override
    old_value = _silent_override
    _silent_override = enabled
    
    status_map = {
        None: "Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЂРµР¶РёРј",
        True: "РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ С‚РёС…РёР№",
        False: "РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РіСЂРѕРјРєРёР№"
    }
    
    debug_log(f"РџРµСЂРµРѕРїСЂРµРґРµР»РµРЅРёРµ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° РёР·РјРµРЅРµРЅРѕ: {status_map.get(old_value, 'РЅРµРёР·РІРµСЃС‚РЅРѕ')} в†’ {status_map.get(enabled, 'РЅРµРёР·РІРµСЃС‚РЅРѕ')}")

def get_silent_override() -> Optional[bool]:
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ С‚РµРєСѓС‰РёР№ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅС‹Р№ СЂРµР¶РёРј С‚РёС…РёС… СѓРІРµРґРѕРјР»РµРЅРёР№.
    """
    return _silent_override

def is_silent_time() -> bool:
    """
    РџСЂРѕРІРµСЂСЏРµС‚, РЅР°С…РѕРґРёС‚СЃСЏ Р»Рё С‚РµРєСѓС‰РµРµ РІСЂРµРјСЏ РІ 'С‚РёС…РѕРј' РїРµСЂРёРѕРґРµ
    
    Returns:
        True РµСЃР»Рё С‚РёС…РёР№ СЂРµР¶РёРј Р°РєС‚РёРІРµРЅ
    """
    global _silent_override
    
    # Р•СЃР»Рё РµСЃС‚СЊ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕРµ РїРµСЂРµРѕРїСЂРµРґРµР»РµРЅРёРµ
    if _silent_override is not None:
        return _silent_override  # True - С‚РёС…РёР№, False - РіСЂРѕРјРєРёР№

    # РЎС‚Р°РЅРґР°СЂС‚РЅР°СЏ РїСЂРѕРІРµСЂРєР° РїРѕ РІСЂРµРјРµРЅРё
    current_hour = datetime.now().hour
    
    # Р•СЃР»Рё РїРµСЂРёРѕРґ РїРµСЂРµС…РѕРґРёС‚ С‡РµСЂРµР· РїРѕР»РЅРѕС‡СЊ (РЅР°РїСЂРёРјРµСЂ, 20:00 - 09:00)
    if _config.silent_start > _config.silent_end:
        return current_hour >= _config.silent_start or current_hour < _config.silent_end
    
    # РџРµСЂРёРѕРґ РІ РїСЂРµРґРµР»Р°С… РѕРґРЅРёС… СЃСѓС‚РѕРє
    return _config.silent_start <= current_hour < _config.silent_end

def should_send_alert(alert_type: str, force: bool) -> bool:
    """
    РџСЂРѕРІРµСЂСЏРµС‚, РЅСѓР¶РЅРѕ Р»Рё РѕС‚РїСЂР°РІР»СЏС‚СЊ Р°Р»РµСЂС‚
    
    Args:
        alert_type: РўРёРї Р°Р»РµСЂС‚Р° (critical, warning, info)
        force: РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅР°СЏ РѕС‚РїСЂР°РІРєР°
        
    Returns:
        True РµСЃР»Рё РЅСѓР¶РЅРѕ РѕС‚РїСЂР°РІРёС‚СЊ Р°Р»РµСЂС‚
    """
    if not _config.enabled:
        debug_log("РђР»РµСЂС‚С‹ РѕС‚РєР»СЋС‡РµРЅС‹ РІ РєРѕРЅС„РёРіСѓСЂР°С†РёРё")
        return False
    
    if force:
        return True
    
    if is_silent_time():
        return False
    
    if alert_type in _config.thresholds:
        threshold_config = _config.thresholds[alert_type]
        if threshold_config["always_send"]:
            return True
    
    # РџСЂРѕРІРµСЂСЏРµРј С‚РёС…РёР№ СЂРµР¶РёРј РґР»СЏ РЅРµ-РєСЂРёС‚РёС‡РµСЃРєРёС… Р°Р»РµСЂС‚РѕРІ
    if alert_type != "critical" and is_silent_time():
        debug_log("РўРёС…РёР№ СЂРµР¶РёРј Р°РєС‚РёРІРµРЅ, Р°Р»РµСЂС‚ РЅРµ РѕС‚РїСЂР°РІР»СЏРµС‚СЃСЏ")
        return False
    
    return True

def send_alert(
    message: str,
    alert_type: str = "info",
    force: bool = False,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ С„СѓРЅРєС†РёСЏ РѕС‚РїСЂР°РІРєРё Р°Р»РµСЂС‚РѕРІ
    
    Args:
        message: РўРµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ
        alert_type: РўРёРї Р°Р»РµСЂС‚Р° (critical, warning, info)
        force: РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅР°СЏ РѕС‚РїСЂР°РІРєР°
        tags: РўРµРіРё РґР»СЏ РєР°С‚РµРіРѕСЂРёР·Р°С†РёРё Р°Р»РµСЂС‚Р°
        metadata: Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РјРµС‚Р°РґР°РЅРЅС‹Рµ
        
    Returns:
        True РµСЃР»Рё СЃРѕРѕР±С‰РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ СѓСЃРїРµС€РЅРѕ
    """
    if not should_send_alert(alert_type, force):
        return False
    
    # РџСЂРѕРІРµСЂСЏРµРј РєРґ РґР»СЏ РѕРґРёРЅР°РєРѕРІС‹С… Р°Р»РµСЂС‚РѕРІ
    if not force and _is_cooldown_active(message):
        debug_log(f"РђР»РµСЂС‚ РЅР°С…РѕРґРёС‚СЃСЏ РІ РєРґ: {message[:50]}...")
        return False
    
    # Р”РѕР±Р°РІР»СЏРµРј РїСЂРµС„РёРєСЃ РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ С‚РёРїР° Р°Р»РµСЂС‚Р°
    prefixes = {
        "critical": "рџљЁ ",
        "warning": "вљ пёЏ ",
        "info": "в„№пёЏ "
    }
    
    prefix = prefixes.get(alert_type, "")
    full_message = f"{prefix}{message}"
    
    # Р›РѕРіРёСЂСѓРµРј Р°Р»РµСЂС‚
    log_levels = {
        "critical": error_log,
        "warning": debug_log,
        "info": debug_log
    }
    
    log_func = log_levels.get(alert_type, debug_log)
    log_func(f"РћС‚РїСЂР°РІРєР° Р°Р»РµСЂС‚Р° [{alert_type}]: {message[:100]}...")
    
    # РћС‚РїСЂР°РІР»СЏРµРј С‡РµСЂРµР· РІСЃРµ РґРѕСЃС‚СѓРїРЅС‹Рµ РєР°РЅР°Р»С‹
    sent = False
    errors = []
    
    # Telegram
    if _telegram_bot and _chat_ids:
        telegram_sent = _send_telegram_alert(full_message, alert_type)
        if telegram_sent:
            sent = True
        else:
            errors.append("Telegram: РѕС€РёР±РєР° РѕС‚РїСЂР°РІРєРё")

    # TamTam
    if _tamtam_sender:
        try:
            tamtam_sent = bool(_tamtam_sender(full_message))
            if tamtam_sent:
                sent = True
            else:
                errors.append("TamTam: РѕС€РёР±РєР° РѕС‚РїСЂР°РІРєРё")
        except Exception as e:
            errors.append(f"TamTam: {e}")

    # Р—Р°РїРёСЃС‹РІР°РµРј РІ РёСЃС‚РѕСЂРёСЋ
    _record_alert({
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "type": alert_type,
        "sent": sent,
        "tags": tags or [],
        "metadata": metadata or {},
        "errors": errors
    })
    
    return sent

def _send_telegram_alert(message: str, alert_type: str) -> bool:
    """
    РћС‚РїСЂР°РІРєР° Р°Р»РµСЂС‚Р° С‡РµСЂРµР· Telegram
    
    Args:
        message: РўРµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ
        alert_type: РўРёРї Р°Р»РµСЂС‚Р°
        
    Returns:
        True РµСЃР»Рё РѕС‚РїСЂР°РІР»РµРЅРѕ СѓСЃРїРµС€РЅРѕ
    """
    if not _telegram_bot or not _chat_ids:
        error_log("Telegram Р±РѕС‚ РЅРµ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ")
        return False
    
    success_count = 0
    total_chats = len(_chat_ids)
    
    for i, chat_id in enumerate(_chat_ids):
        try:
            # Р”Р»СЏ РєСЂРёС‚РёС‡РµСЃРєРёС… Р°Р»РµСЂС‚РѕРІ РґРѕР±Р°РІР»СЏРµРј РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕРµ С„РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёРµ
            if alert_type == "critical":
                formatted_message = f"*{message}*"
            else:
                formatted_message = message
            
            _telegram_bot.send_message(
                chat_id=chat_id,
                text=formatted_message,
                parse_mode='Markdown' if alert_type == "critical" else None
            )
            success_count += 1
            
            # РќРµР±РѕР»СЊС€Р°СЏ Р·Р°РґРµСЂР¶РєР° РјРµР¶РґСѓ РѕС‚РїСЂР°РІРєР°РјРё С‡С‚РѕР±С‹ РЅРµ РїСЂРµРІС‹СЃРёС‚СЊ Р»РёРјРёС‚С‹
            if i < total_chats - 1:
                time.sleep(0.1)
                
        except Exception as e:
            error_log(f"РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё РІ С‡Р°С‚ {chat_id}: {e}")
    
    success_rate = success_count / total_chats if total_chats > 0 else 0
    debug_log(f"Telegram Р°Р»РµСЂС‚ РѕС‚РїСЂР°РІР»РµРЅ: {success_count}/{total_chats} СѓСЃРїРµС€РЅРѕ ({success_rate:.0%})")
    
    return success_count > 0

def _is_cooldown_active(message: str, check_period: int = None) -> bool:
    """
    РџСЂРѕРІРµСЂСЏРµС‚, Р°РєС‚РёРІРµРЅ Р»Рё РєРґ РґР»СЏ СЃРѕРѕР±С‰РµРЅРёСЏ
    
    Args:
        message: РўРµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ
        check_period: РџРµСЂРёРѕРґ РїСЂРѕРІРµСЂРєРё РІ СЃРµРєСѓРЅРґР°С… (РµСЃР»Рё None, РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РєРѕРЅС„РёРі)
        
    Returns:
        True РµСЃР»Рё РєРґ Р°РєС‚РёРІРµРЅ
    """
    period = check_period or _config.cooldown_seconds
    now = time.time()
    
    # РС‰РµРј РїРѕС…РѕР¶РёРµ СЃРѕРѕР±С‰РµРЅРёСЏ РІ РёСЃС‚РѕСЂРёРё
    for alert in reversed(_alert_history):
        if alert["message"] == message and alert["sent"]:
            alert_time = datetime.fromisoformat(alert["timestamp"]).timestamp()
            if now - alert_time < period:
                return True
    
    return False

def _record_alert(alert_data: Dict[str, Any]) -> None:
    """
    Р—Р°РїРёСЃС‹РІР°РµС‚ Р°Р»РµСЂС‚ РІ РёСЃС‚РѕСЂРёСЋ
    
    Args:
        alert_data: Р”Р°РЅРЅС‹Рµ Р°Р»РµСЂС‚Р°
    """
    global _alert_history
    
    _alert_history.append(alert_data)
    
    # РћРіСЂР°РЅРёС‡РёРІР°РµРј СЂР°Р·РјРµСЂ РёСЃС‚РѕСЂРёРё
    if len(_alert_history) > _max_history_size:
        _alert_history = _alert_history[-_max_history_size:]
    
    # Р›РѕРіРёСЂСѓРµРј РІ С„Р°Р№Р» РґР»СЏ РѕС‚Р»Р°РґРєРё
    if alert_data.get("sent"):
        status = "вњ… РћС‚РїСЂР°РІР»РµРЅ"
    else:
        status = "вќЊ РќРµ РѕС‚РїСЂР°РІР»РµРЅ"
    
    debug_log(f"РђР»РµСЂС‚ Р·Р°РїРёСЃР°РЅ РІ РёСЃС‚РѕСЂРёСЋ: {alert_data['type']} - {status}")

def get_alert_history(
    limit: int = 50,
    alert_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    РџРѕР»СѓС‡РёС‚СЊ РёСЃС‚РѕСЂРёСЋ Р°Р»РµСЂС‚РѕРІ
    
    Args:
        limit: РњР°РєСЃРёРјР°Р»СЊРЅРѕРµ РєРѕР»РёС‡РµСЃС‚РІРѕ Р·Р°РїРёСЃРµР№
        alert_type: Р¤РёР»СЊС‚СЂ РїРѕ С‚РёРїСѓ Р°Р»РµСЂС‚Р°
        tags: Р¤РёР»СЊС‚СЂ РїРѕ С‚РµРіР°Рј
        
    Returns:
        РЎРїРёСЃРѕРє Р°Р»РµСЂС‚РѕРІ
    """
    filtered_history = _alert_history
    
    if alert_type:
        filtered_history = [a for a in filtered_history if a["type"] == alert_type]
    
    if tags:
        filtered_history = [a for a in filtered_history if any(tag in a.get("tags", []) for tag in tags)]
    
    return filtered_history[-limit:]

def clear_alert_history() -> int:
    """
    РћС‡РёСЃС‚РёС‚СЊ РёСЃС‚РѕСЂРёСЋ Р°Р»РµСЂС‚РѕРІ
    
    Returns:
        РљРѕР»РёС‡РµСЃС‚РІРѕ СѓРґР°Р»РµРЅРЅС‹С… Р·Р°РїРёСЃРµР№
    """
    global _alert_history
    count = len(_alert_history)
    _alert_history = []
    debug_log(f"РСЃС‚РѕСЂРёСЏ Р°Р»РµСЂС‚РѕРІ РѕС‡РёС‰РµРЅР°, СѓРґР°Р»РµРЅРѕ {count} Р·Р°РїРёСЃРµР№")
    return count

def get_alert_stats() -> Dict[str, Any]:
    """
    РџРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ Р°Р»РµСЂС‚Р°Рј
    
    Returns:
        РЎР»РѕРІР°СЂСЊ СЃРѕ СЃС‚Р°С‚РёСЃС‚РёРєРѕР№
    """
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    
    # Р¤РёР»СЊС‚СЂСѓРµРј Р°Р»РµСЂС‚С‹ Р·Р° СЃРµРіРѕРґРЅСЏ
    today_alerts = [
        a for a in _alert_history 
        if datetime.fromisoformat(a["timestamp"]) >= today_start
    ]
    
    # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј
    by_type = {}
    for alert in today_alerts:
        alert_type = alert["type"]
        if alert_type not in by_type:
            by_type[alert_type] = {"total": 0, "sent": 0}
        by_type[alert_type]["total"] += 1
        if alert["sent"]:
            by_type[alert_type]["sent"] += 1
    
    return {
        "total_all_time": len(_alert_history),
        "total_today": len(today_alerts),
        "by_type": by_type,
        "silent_mode": is_silent_time(),
        "silent_override": _silent_override
    }

def configure(
    silent_start: Optional[int] = None,
    silent_end: Optional[int] = None,
    enabled: Optional[bool] = None,
    cooldown_seconds: Optional[int] = None
) -> None:
    """
    РќР°СЃС‚СЂРѕР№РєР° РїР°СЂР°РјРµС‚СЂРѕРІ Р°Р»РµСЂС‚РѕРІ
    
    Args:
        silent_start: РќР°С‡Р°Р»Рѕ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (0-23)
        silent_end: РљРѕРЅРµС† С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° (0-23)
        enabled: Р’РєР»СЋС‡РµРЅС‹ Р»Рё Р°Р»РµСЂС‚С‹
        cooldown_seconds: РљРґ РјРµР¶РґСѓ РѕРґРёРЅР°РєРѕРІС‹РјРё Р°Р»РµСЂС‚Р°РјРё
    """
    if silent_start is not None:
        _config.silent_start = silent_start
    if silent_end is not None:
        _config.silent_end = silent_end
    if enabled is not None:
        _config.enabled = enabled
    if cooldown_seconds is not None:
        _config.cooldown_seconds = cooldown_seconds
    
    debug_log(f"РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р°Р»РµСЂС‚РѕРІ РѕР±РЅРѕРІР»РµРЅР°: silent={_config.silent_start}:00-{_config.silent_end}:00, enabled={_config.enabled}, cooldown={_config.cooldown_seconds}СЃ")

# РђР»РёР°СЃС‹ РґР»СЏ РѕР±СЂР°С‚РЅРѕР№ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё
send_message = send_alert