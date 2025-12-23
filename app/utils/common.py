"""
/app/utils/common.py
Server Monitoring System v4.15.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
General system utilities
Система мониторинга серверов
Версия: 4.15.3
Автор: Александр Суханов (c)
Лицензия: MIT
Общие утилиты системы
"""

import os
import time
import logging
import importlib
from datetime import datetime

try:
    from config.settings_app import DEBUG_MODE, LOG_DIR  # type: ignore
except ImportError:
    DEBUG_MODE = False
    LOG_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "logs")

DEBUG_LOG_FILE = os.path.join(LOG_DIR, 'debug.log')

def setup_logging():
    """Настройка централизованного логирования"""
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    
    os.makedirs(LOG_DIR, exist_ok=True)    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(DEBUG_LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def debug_log(message, force=False):
    """Централизованное логирование отладки"""
    if DEBUG_MODE or force:
        logger = logging.getLogger(__name__)
        logger.debug(message)

def safe_import(module_name, class_name=None):
    """Безопасный импорт с обработкой ошибок"""
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
    """Форматирование длительности в читаемый вид"""
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
    """Универсальный прогресс-бар"""
    filled = int(round(width * percentage / 100))
    bar = f"[{'█' * filled}{'░' * (width - filled)}] {percentage:.1f}%"
    return bar

def is_proxmox_server(ip):
    """Проверяет, является ли сервер Proxmox"""
    return (ip.startswith("192.168.30.") or
           ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])
