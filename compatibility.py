"""
Server Monitoring System v4.0.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Модуль совместимости для плавного перехода на новую структуру
Версия: 4.0.1
Используется только во время миграции
"""

import sys
import os

# Добавляем новую структуру в путь
sys.path.insert(0, '/opt/monitoring/app')

# Словарь для перехвата импортов
IMPORT_MAP = {}

def setup_compatibility():
    """Настраивает совместимость между старой и новой структурой"""
    
    try:
        # Импортируем из новой структуры
        from app import (
            server_checker, logger,
            format_duration, progress_bar,
            safe_import, debug_log, DEBUG_MODE
        )
        
        # Заполняем карту совместимости
        IMPORT_MAP.update({
            'server_checker': server_checker,
            'logger': logger,
            'format_duration': format_duration,
            'progress_bar': progress_bar,
            'safe_import': safe_import,
            'debug_log': debug_log,
            'DEBUG_MODE': DEBUG_MODE,
        })
        
        print("✅ Совместимость настроена (новая структура)")
        
    except ImportError as e:
        print(f"⚠️ Не удалось импортировать из новой структуры: {e}")
        print("⏮️ Используем старую структуру...")
        
        # Импортируем из старой структуры
        try:
            from core_utils import (
                server_checker, debug_log, progress_bar,
                format_duration, safe_import, DEBUG_MODE, logger
            )
            
            IMPORT_MAP.update({
                'server_checker': server_checker,
                'logger': logger,
                'format_duration': format_duration,
                'progress_bar': progress_bar,
                'safe_import': safe_import,
                'debug_log': debug_log,
                'DEBUG_MODE': DEBUG_MODE,
            })
            
            print("✅ Совместимость настроена (старая структура)")
            
        except ImportError as e2:
            print(f"❌ Критическая ошибка: {e2}")
            raise

# Автоматическая настройка при импорте
setup_compatibility()

# Экспортируем всё для обратной совместимости
globals().update(IMPORT_MAP)

# Экспортируем специально для импорта "from compatibility import *"
__all__ = list(IMPORT_MAP.keys())
