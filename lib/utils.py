"""
/lib/utils.py
Server Monitoring System v6.0.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utility functions
Система мониторинга серверов
Версия: 6.0.3
Автор: Александр Суханов (c)
Лицензия: MIT
Вспомогательные функции
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import importlib

def safe_import(module_name: str, class_name: Optional[str] = None) -> Any:
    """
    Безопасный импорт модулей с обработкой ошибок
    
    Args:
        module_name: Имя модуля
        class_name: Имя класса (опционально)
        
    Returns:
        Импортированный модуль или класс, или None при ошибке
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
    Форматирование длительности в читаемый вид
    
    Args:
        seconds: Количество секунд
        
    Returns:
        Отформатированная строка
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
    Универсальный прогресс-бар
    
    Args:
        percentage: Процент завершения (0-100)
        width: Ширина прогресс1бара в символах
        
    Returns:
        Строка с прогресс1баром
    """
    filled = int(round(width * percentage / 100))
    bar = f"[{'█' * filled}{'░' * (width - filled)}] {percentage:.1f}%"
    return bar

def is_proxmox_server(ip: str) -> bool:
    """
    Проверяет, является ли сервер Proxmox
    
    Args:
        ip: IP адрес
        
    Returns:
        True если сервер Proxmox
    """
    return (ip.startswith("192.168.30.") or
           ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])

def parse_time_string(time_str: str) -> datetime.time:
    """
    Парсит строку времени в формате HH:MM
    
    Args:
        time_str: Строка времени (например, "08:30")
        
    Returns:
        Объект datetime.time
    """
    from datetime import time
    try:
        hours, minutes = map(int, time_str.split(':'))
        return time(hours, minutes)
    except (ValueError, AttributeError):
        return time(8, 30)  # Значение по умолчанию

def get_size_string(size_bytes: int) -> str:
    """
    Преобразует размер в байтах в читаемую строку
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        Читаемая строка (например, "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"