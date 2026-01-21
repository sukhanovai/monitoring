"""
/lib/logging.py
Server Monitoring System v8.1.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified logging system
Система мониторинга серверов
Версия: 8.1.8
Автор: Александр Суханов (c)
Лицензия: MIT
Единая система логирования
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

# Глобальные переменные
_loggers = {}

def setup_logging(
    name: str = "monitoring",
    level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: Optional[Path] = None,
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
        LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    
    # Обработчики
    handlers = []
    
    if log_to_file:
        # Создаем директорию для логов если нет
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        target_file = log_file or DEBUG_LOG_FILE
        
        # Файловый обработчик с ротацией
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

def get_logger(name: Optional[str] = None, base_name: str = "monitoring") -> logging.Logger:
    """
    Получить именованный логгер
    
    Args:
        name: Имя вложенного логгера (опционально)
        base_name: Базовое имя логгера
        
    Returns:
        Экземпляр логгера
    """
    if name:
        return logging.getLogger(f"{base_name}.{name}")
    return logging.getLogger(base_name)

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
        (MONITOR_LOG_FILE, "Лог мониторинга"),
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
            file_path = Path(file_path)
            if file_path.exists():
                file_path.write_text("", encoding="utf-8")
                results[file_path.name] = "✅ Очищен"
            else:
                # Создаем пустой файл
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("", encoding="utf-8")
                results[file_path.name] = "✅ Создан пустой файл"
        except Exception as e:
            results[Path(file_path).name] = f"❌ Ошибка: {str(e)}"
    
    return results

# Инициализация логгера по умолчанию
default_logger = setup_logging("monitoring")
