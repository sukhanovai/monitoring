"""
/lib/helpers.py
Server Monitoring System v8.2.22
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Auxiliary utilities
Система мониторинга серверов
Версия: 8.2.22
Автор: Александр Суханов (c)
Лицензия: MIT
Вспомогательные утилиты
"""

import warnings

def progress_bar(percentage, width=20):
    """Универсальный прогресс-бар"""
    filled = int(round(width * percentage / 100))
    bar = f"[{'█' * filled}{'░' * (width - filled)}] {percentage:.1f}%"
    return bar

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

def is_proxmox_server(ip):
    """Проверяет, является ли сервер Proxmox (устаревшая обертка)."""
    warnings.warn(
        "lib.helpers.is_proxmox_server устарела; используйте lib.utils.is_proxmox_server.",
        DeprecationWarning,
        stacklevel=2,
    )
    from lib.utils import is_proxmox_server as _is_proxmox_server
    return _is_proxmox_server(ip)
