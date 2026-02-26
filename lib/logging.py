"""
/lib/logging.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified logging system
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р•РґРёРЅР°СЏ СЃРёСЃС‚РµРјР° Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from config.settings import (
        LOG_DIR,
        DEBUG_MODE,
        DEBUG_LOG_FILE,
        BOT_LOG_FILE,
        MONITOR_LOG_FILE,
        LOG_FORMAT,
        LOG_DATE_FORMAT,
        LOG_MAX_BYTES,
        LOG_BACKUP_COUNT,
    )
except Exception:
    LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
    DEBUG_MODE = False
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5    

DEBUG_LOG_FILE = Path(DEBUG_LOG_FILE) if "DEBUG_LOG_FILE" in globals() else LOG_DIR / "debug.log"
BOT_LOG_FILE = Path(BOT_LOG_FILE) if "BOT_LOG_FILE" in globals() else LOG_DIR / "bot.log"
MONITOR_LOG_FILE = (
    Path(MONITOR_LOG_FILE) if "MONITOR_LOG_FILE" in globals() else LOG_DIR / "monitor.log"
)

# Р“Р»РѕР±Р°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ
_loggers = {}

def setup_logging(
    name: str = "monitoring",
    level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    РќР°СЃС‚СЂРѕР№РєР° Р»РѕРіРёСЂРѕРІР°РЅРёСЏ РґР»СЏ РјРѕРґСѓР»СЏ
    
    Args:
        name: РРјСЏ Р»РѕРіРіРµСЂР°
        level: РЈСЂРѕРІРµРЅСЊ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Р—Р°РїРёСЃС‹РІР°С‚СЊ Р»Рё РІ С„Р°Р№Р»
        log_to_console: Р’С‹РІРѕРґРёС‚СЊ Р»Рё РІ РєРѕРЅСЃРѕР»СЊ
        
    Returns:
        РќР°СЃС‚СЂРѕРµРЅРЅС‹Р№ Р»РѕРіРіРµСЂ
    """
    if name in _loggers:
        return _loggers[name]
    
    # РЎРѕР·РґР°РµРј Р»РѕРіРіРµСЂ
    logger = logging.getLogger(name)
    
    # РЈСЃС‚Р°РЅР°РІР»РёРІР°РµРј СѓСЂРѕРІРµРЅСЊ
    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    
    logger.setLevel(log_level)
    
    # Р¤РѕСЂРјР°С‚С‚РµСЂ
    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    
    # РћР±СЂР°Р±РѕС‚С‡РёРєРё
    handlers = []
    
    if log_to_file:
        # РЎРѕР·РґР°РµРј РґРёСЂРµРєС‚РѕСЂРёСЋ РґР»СЏ Р»РѕРіРѕРІ РµСЃР»Рё РЅРµС‚
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        target_file = log_file or DEBUG_LOG_FILE
        
        # Р¤Р°Р№Р»РѕРІС‹Р№ РѕР±СЂР°Р±РѕС‚С‡РёРє СЃ СЂРѕС‚Р°С†РёРµР№
        file_handler = logging.handlers.RotatingFileHandler(
            target_file,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    if log_to_console:
        # РљРѕРЅСЃРѕР»СЊРЅС‹Р№ РѕР±СЂР°Р±РѕС‚С‡РёРє
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    # РЈРґР°Р»СЏРµРј СЃС‚Р°СЂС‹Рµ РѕР±СЂР°Р±РѕС‚С‡РёРєРё Рё РґРѕР±Р°РІР»СЏРµРј РЅРѕРІС‹Рµ
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    for handler in handlers:
        logger.addHandler(handler)
    
    _loggers[name] = logger
    return logger

def get_logger(name: Optional[str] = None, base_name: str = "monitoring") -> logging.Logger:
    """
    РџРѕР»СѓС‡РёС‚СЊ РёРјРµРЅРѕРІР°РЅРЅС‹Р№ Р»РѕРіРіРµСЂ
    
    Args:
        name: РРјСЏ РІР»РѕР¶РµРЅРЅРѕРіРѕ Р»РѕРіРіРµСЂР° (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)
        base_name: Р‘Р°Р·РѕРІРѕРµ РёРјСЏ Р»РѕРіРіРµСЂР°
        
    Returns:
        Р­РєР·РµРјРїР»СЏСЂ Р»РѕРіРіРµСЂР°
    """
    if name:
        return logging.getLogger(f"{base_name}.{name}")
    return logging.getLogger(base_name)

def debug_log(message: str, force: bool = False, logger_name: str = "monitoring") -> None:
    """
    Р¦РµРЅС‚СЂР°Р»РёР·РѕРІР°РЅРЅРѕРµ Р»РѕРіРёСЂРѕРІР°РЅРёРµ РѕС‚Р»Р°РґРєРё
    
    Args:
        message: РЎРѕРѕР±С‰РµРЅРёРµ РґР»СЏ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
        force: РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ Р»РѕРіРёСЂРѕРІР°С‚СЊ РґР°Р¶Рµ РµСЃР»Рё РЅРµ РІ СЂРµР¶РёРјРµ РѕС‚Р»Р°РґРєРё
        logger_name: РРјСЏ Р»РѕРіРіРµСЂР°
    """
    logger = setup_logging(logger_name)
    
    if DEBUG_MODE or force:
        logger.debug(message)
    else:
        logger.info(message)

def info_log(message: str, logger_name: str = "monitoring") -> None:
    """Р›РѕРіРёСЂРѕРІР°РЅРёРµ РёРЅС„РѕСЂРјР°С†РёРѕРЅРЅС‹С… СЃРѕРѕР±С‰РµРЅРёР№"""
    logger = setup_logging(logger_name)
    logger.info(message)

def warning_log(message: str, logger_name: str = "monitoring") -> None:
    """Р›РѕРіРёСЂРѕРІР°РЅРёРµ РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёР№"""
    logger = setup_logging(logger_name)
    logger.warning(message)

def error_log(message: str, logger_name: str = "monitoring") -> None:
    """Р›РѕРіРёСЂРѕРІР°РЅРёРµ РѕС€РёР±РѕРє"""
    logger = setup_logging(logger_name)
    logger.error(message)

def critical_log(message: str, logger_name: str = "monitoring") -> None:
    """Р›РѕРіРёСЂРѕРІР°РЅРёРµ РєСЂРёС‚РёС‡РµСЃРєРёС… РѕС€РёР±РѕРє"""
    logger = setup_logging(logger_name)
    logger.critical(message)

def exception_log(message: str, exc: Exception = None, logger_name: str = "monitoring") -> None:
    """
    Р›РѕРіРёСЂРѕРІР°РЅРёРµ РёСЃРєР»СЋС‡РµРЅРёР№ СЃ С‚СЂР°СЃСЃРёСЂРѕРІРєРѕР№
    
    Args:
        message: РЎРѕРѕР±С‰РµРЅРёРµ РѕР± РѕС€РёР±РєРµ
        exc: РСЃРєР»СЋС‡РµРЅРёРµ (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)
        logger_name: РРјСЏ Р»РѕРіРіРµСЂР°
    """
    logger = setup_logging(logger_name)
    if exc:
        logger.exception(f"{message}: {exc}")
    else:
        logger.exception(message)

def set_debug_mode(enabled: bool) -> None:
    """
    Р’РєР»СЋС‡РµРЅРёРµ/РІС‹РєР»СЋС‡РµРЅРёРµ СЂРµР¶РёРјР° РѕС‚Р»Р°РґРєРё
    
    Args:
        enabled: Р’РєР»СЋС‡РёС‚СЊ СЂРµР¶РёРј РѕС‚Р»Р°РґРєРё
    """
    global DEBUG_MODE
    DEBUG_MODE = enabled
    
    # РћР±РЅРѕРІР»СЏРµРј СѓСЂРѕРІРЅРё Р»РѕРіРёСЂРѕРІР°РЅРёСЏ Сѓ РІСЃРµС… Р»РѕРіРіРµСЂРѕРІ
    new_level = logging.DEBUG if enabled else logging.INFO
    
    for logger in _loggers.values():
        logger.setLevel(new_level)
        for handler in logger.handlers:
            handler.setLevel(new_level)
    
    debug_log(f"Р РµР¶РёРј РѕС‚Р»Р°РґРєРё {'РІРєР»СЋС‡РµРЅ' if enabled else 'РІС‹РєР»СЋС‡РµРЅ'}")

def get_log_file_stats() -> dict:
    """
    РџРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ Р»РѕРі-С„Р°Р№Р»Р°Рј
    
    Returns:
        РЎР»РѕРІР°СЂСЊ СЃРѕ СЃС‚Р°С‚РёСЃС‚РёРєРѕР№
    """
    stats = {}
    
    for log_file, desc in [
        (DEBUG_LOG_FILE, "РћСЃРЅРѕРІРЅРѕР№ Р»РѕРі"),
        (BOT_LOG_FILE, "Р›РѕРі Р±РѕС‚Р°"),
        (MONITOR_LOG_FILE, "Р›РѕРі РјРѕРЅРёС‚РѕСЂРёРЅРіР°"),
    ]:
        try:
            log_path = Path(log_file)
            if log_path.exists():
                size = log_path.stat().st_size
                mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
                stats[desc] = {
                    "size_mb": size / (1024 * 1024),
                    "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "path": str(log_path),
                }
            else:
                stats[desc] = {"error": "Р¤Р°Р№Р» РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚"}
        except Exception as e:
            stats[desc] = {"error": str(e)}
    
    return stats

def clear_logs(log_type: str = "all") -> dict:
    """
    РћС‡РёСЃС‚РєР° Р»РѕРі-С„Р°Р№Р»РѕРІ
    
    Args:
        log_type: РўРёРї Р»РѕРіР° РґР»СЏ РѕС‡РёСЃС‚РєРё (all, debug, bot, monitor)
        
    Returns:
        РЎР»РѕРІР°СЂСЊ СЃ СЂРµР·СѓР»СЊС‚Р°С‚Р°РјРё
    """
    files_to_clear = []
    
    if log_type in ["all", "debug"]:
        files_to_clear.append(DEBUG_LOG_FILE)
    if log_type in ["all", "bot"]:
        files_to_clear.append(BOT_LOG_FILE)
    if log_type in ["all", "monitor"]:
        files_to_clear.append(MONITOR_LOG_FILE)
    
    results = {}
    for file_path in files_to_clear:
        try:
            file_path = Path(file_path)
            if file_path.exists():
                file_path.write_text("", encoding="utf-8")
                results[file_path.name] = "вњ… РћС‡РёС‰РµРЅ"
            else:
                # РЎРѕР·РґР°РµРј РїСѓСЃС‚РѕР№ С„Р°Р№Р»
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("", encoding="utf-8")
                results[file_path.name] = "вњ… РЎРѕР·РґР°РЅ РїСѓСЃС‚РѕР№ С„Р°Р№Р»"
        except Exception as e:
            results[Path(file_path).name] = f"вќЊ РћС€РёР±РєР°: {str(e)}"
    
    return results

# РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Р»РѕРіРіРµСЂР° РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ
default_logger = setup_logging("monitoring")
