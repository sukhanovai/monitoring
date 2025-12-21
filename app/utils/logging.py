"""
/app/utils/logging.py
Server Monitoring System v4.14.37
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Logging module
Версия: 4.14.37
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль логирования
"""

import os
import logging
import logging.handlers
from datetime import datetime

try:
    from app.config.settings import DEBUG_MODE
except ImportError:
    DEBUG_MODE = False

def setup_logging():
    """Настройка централизованного логирования"""
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    
    # Создаем директорию для логов если не существует
    log_dir = '/opt/monitoring/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Основной логгер
    logger = logging.getLogger('server_monitor')
    logger.setLevel(log_level)
    
    # Удаляем существующие обработчики чтобы избежать дублирования
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Файловый обработчик (ротация по размеру)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'debug.log'),
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def debug_log(message, force=False):
    """Централизованное логирование отладки"""
    logger = logging.getLogger('server_monitor')
    
    if DEBUG_MODE or force:
        logger.debug(message)
    else:
        # В обычном режиме пишем информационные сообщения
        logger.info(message)

def get_logger(name=None):
    """Получить именованный логгер"""
    if name:
        return logging.getLogger(f'server_monitor.{name}')
    return logging.getLogger('server_monitor')
