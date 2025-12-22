"""
/lib/logging.py
Server Monitoring System v4.14.44
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified logging system
Система мониторинга серверов
Версия: 4.14.44
Автор: Александр Суханов (c)
Лицензия: MIT
Единая система логирования
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

# Пути к логам
LOG_DIR = "/opt/monitoring/logs"
DEBUG_LOG_FILE = os.path.join(LOG_DIR, "debug.log")
BOT_LOG_FILE = os.path.join(LOG_DIR, "bot.log")
MONITOR_LOG_FILE = os.path.join(LOG_DIR, "monitor.log")

# Глобальные переменные
DEBUG_MODE = False
_loggers = {}

def setup_logging(
    name: str = "monitoring",
    level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Настройка логирования для модуля
    
    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Записывать ли в файл
        log_to_console: Выводить ли в консоль
        
    Returns:
        Настроенный логгер
    """
    if name in _loggers:
        return _loggers[name]
    
    # Создаем логгер
    logger = logging.getLogger(name)
    
    # Устанавливаем уровень
    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    
    logger.setLevel(log_level)
    
    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчики
    handlers = []
    
    if log_to_file:
        # Создаем директорию для логов если нет
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Файловый обработчик с ротацией
        file_handler = logging.handlers.RotatingFileHandler(
            DEBUG_LOG_FILE,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    if log_to_console:
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    # Удаляем старые обработчики и добавляем новые
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    for handler in handlers:
        logger.addHandler(handler)
    
    _loggers[name] = logger
    return logger

def debug_log(message: str, force: bool = False, logger_name: str = "monitoring") -> None:
    """
    Централизованное логирование отладки
    
    Args:
        message: Сообщение для логирования
        force: Принудительно логировать даже если не в режиме отладки
        logger_name: Имя логгера
    """
    logger = setup_logging(logger_name)
    
    if DEBUG_MODE or force:
        logger.debug(message)
    else:
        logger.info(message)

def info_log(message: str, logger_name: str = "monitoring") -> None:
    """Логирование информационных сообщений"""
    logger = setup_logging(logger_name)
    logger.info(message)

def warning_log(message: str, logger_name: str = "monitoring") -> None:
    """Логирование предупреждений"""
    logger = setup_logging(logger_name)
    logger.warning(message)

def error_log(message: str, logger_name: str = "monitoring") -> None:
    """Логирование ошибок"""
    logger = setup_logging(logger_name)
    logger.error(message)

def critical_log(message: str, logger_name: str = "monitoring") -> None:
    """Логирование критических ошибок"""
    logger = setup_logging(logger_name)
    logger.critical(message)

def exception_log(message: str, exc: Exception = None, logger_name: str = "monitoring") -> None:
    """
    Логирование исключений с трассировкой
    
    Args:
        message: Сообщение об ошибке
        exc: Исключение (опционально)
        logger_name: Имя логгера
    """
    logger = setup_logging(logger_name)
    if exc:
        logger.exception(f"{message}: {exc}")
    else:
        logger.exception(message)

def set_debug_mode(enabled: bool) -> None:
    """
    Включение/выключение режима отладки
    
    Args:
        enabled: Включить режим отладки
    """
    global DEBUG_MODE
    DEBUG_MODE = enabled
    
    # Обновляем уровни логирования у всех логгеров
    new_level = logging.DEBUG if enabled else logging.INFO
    
    for logger in _loggers.values():
        logger.setLevel(new_level)
        for handler in logger.handlers:
            handler.setLevel(new_level)
    
    debug_log(f"Режим отладки {'включен' if enabled else 'выключен'}")

def get_log_file_stats() -> dict:
    """
    Получить статистику по лог-файлам
    
    Returns:
        Словарь со статистикой
    """
    stats = {}
    
    for log_file, desc in [
        (DEBUG_LOG_FILE, "Основной лог"),
        (BOT_LOG_FILE, "Лог бота"),
        (MONITOR_LOG_FILE, "Лог мониторинга")
    ]:
        try:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                stats[desc] = {
                    "size_mb": size / (1024 * 1024),
                    "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                    "path": log_file
                }
            else:
                stats[desc] = {"error": "Файл не существует"}
        except Exception as e:
            stats[desc] = {"error": str(e)}
    
    return stats

def clear_logs(log_type: str = "all") -> dict:
    """
    Очистка лог-файлов
    
    Args:
        log_type: Тип лога для очистки (all, debug, bot, monitor)
        
    Returns:
        Словарь с результатами
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
            if os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write('')
                results[os.path.basename(file_path)] = "✅ Очищен"
            else:
                # Создаем пустой файл
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write('')
                results[os.path.basename(file_path)] = "✅ Создан пустой файл"
        except Exception as e:
            results[os.path.basename(file_path)] = f"❌ Ошибка: {str(e)}"
    
    return results

# Инициализация логгера по умолчанию
default_logger = setup_logging("monitoring")