"""
Server Monitoring System v4.0.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Временный адаптер для замены core_utils.py
Версия: 4.0.1
Будет удален после полного перехода
"""

import sys
import os

# Перенаправляем импорты
sys.path.insert(0, os.path.dirname(__file__))

# Пробуем импортировать из новой структуры
try:
    from app import (
        server_checker, logger,
        format_duration, progress_bar,
        safe_import, debug_log, DEBUG_MODE
    )
    
    print("🔄 adapter_core_utils: Используется новая структура")
    
except ImportError:
    # Если не удалось, пробуем из старой
    try:
        sys.path.insert(0, '/opt/monitoring')
        from core_utils import (
            server_checker, debug_log, progress_bar,
            format_duration, safe_import, DEBUG_MODE, logger
        )
        
        print("🔄 adapter_core_utils: Используется старая структура")
        
    except ImportError as e:
        print(f"❌ Критическая ошибка в адаптере: {e}")
        raise

# Экспортируем всё что экспортировал старый core_utils.py
__all__ = [
    'server_checker', 'debug_log', 'progress_bar',
    'format_duration', 'safe_import', 'DEBUG_MODE', 'logger'
]
