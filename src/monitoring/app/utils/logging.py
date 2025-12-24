"""
/src/monitoring/app/utils/logging.py
Server Monitoring System v4.16.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Logging module
Версия: 4.16.1
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль логирования
"""

import logging
import logging.handlers
from pathlib import Path

try:
    from config.settings_app import (
        DEBUG_MODE,
        LOG_DIR,
        DEBUG_LOG_FILE,
        LOG_FORMAT,
        LOG_DATE_FORMAT,
        LOG_MAX_BYTES,
        LOG_BACKUP_COUNT,
    )
except ImportError:
    DEBUG_MODE = False
    LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
    DEBUG_LOG_FILE = LOG_DIR / "debug.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5

def setup_logging():
    """Настройка централизованного логирования"""
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    
    # Создаем директорию для логов если не существует
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Формат логов
    log_format = LOG_FORMAT
    
    # Основной логгер
    logger = logging.getLogger('server_monitor')
    logger.setLevel(log_level)
    
    # Удаляем существующие обработчики чтобы избежать дублирования
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Файловый обработчик (ротация по размеру)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=DEBUG_LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=LOG_DATE_FORMAT))
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=LOG_DATE_FORMAT))
    
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
