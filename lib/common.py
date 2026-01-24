"""
/lib/common.py
Server Monitoring System v8.2.13
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
General system utilities
Система мониторинга серверов
Версия: 8.2.13
Автор: Александр Суханов (c)
Лицензия: MIT
Общие утилиты системы
"""

import importlib
import warnings

try:
    from config.db_settings import DEBUG_MODE
except ImportError:
    DEBUG_MODE = False
from lib.logging import setup_logging as _setup_logging, get_logger

def setup_logging():
    """Настройка централизованного логирования"""
    return _setup_logging()

def debug_log(message, force=False):
    """Централизованное логирование отладки"""
    logger = get_logger(__name__)
    if DEBUG_MODE or force:
        logger.debug(message)
    else:
        logger.info(message)
        
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
    """Проверяет, является ли сервер Proxmox (устаревшая обертка)."""
    warnings.warn(
        "lib.common.is_proxmox_server устарела; используйте lib.utils.is_proxmox_server.",
        DeprecationWarning,
        stacklevel=2,
    )
    from lib.utils import is_proxmox_server as _is_proxmox_server
    return _is_proxmox_server(ip)
