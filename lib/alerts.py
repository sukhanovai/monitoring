"""
/lib/alerts.py
Server Monitoring System v6.0.23
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified alert system
Система мониторинга серверов
Версия: 6.0.23
Автор: Александр Суханов (c)
Лицензия: MIT
Единая система оповещений
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime, time as dt_time
from lib.logging import debug_log, error_log, setup_logging

# Логгер для этого модуля
_logger = setup_logging("alerts")

# Глобальные переменные
_telegram_bot = None
_chat_ids = []
_silent_override: Optional[bool] = None
_alert_history: List[Dict[str, Any]] = []
_max_history_size = 1000

def configure_alerts(
    silent_start: Optional[int] = None,
    silent_end: Optional[int] = None,
    enabled: Optional[bool] = None,
    cooldown_seconds: Optional[int] = None,
    thresholds: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    """
    Настраивает базовые параметры алертов из внешних настроек.

    Args:
        silent_start: Час начала тихого режима
        silent_end: Час окончания тихого режима
        enabled: Включены ли алерты
        cooldown_seconds: Минимальный интервал между одинаковыми алертами
        thresholds: Переопределение порогов для типов алертов
    """
    if silent_start is not None:
        _config.silent_start = silent_start
    if silent_end is not None:
        _config.silent_end = silent_end
    if enabled is not None:
        _config.enabled = enabled
    if cooldown_seconds is not None:
        _config.cooldown_seconds = cooldown_seconds
    if thresholds:
        _config.thresholds.update(thresholds)

class AlertConfig:
    """Конфигурация алертов"""
    
    def __init__(self):
        self.silent_start = 20  # 20:00
        self.silent_end = 9     # 09:00
        self.enabled = True
        self.cooldown_seconds = 300  # 5 минут между одинаковыми алертами
        self.max_retries = 3
        self.retry_delay = 5
        
        # Пороги для разных типов алертов
        self.thresholds = {
            "critical": {"priority": 1, "always_send": True},
            "warning": {"priority": 2, "always_send": False},
            "info": {"priority": 3, "always_send": False}
        }

# Глобальный экземпляр конфигурации
_config = AlertConfig()

def init_telegram_bot(bot_instance, chat_ids: List[str]) -> None:
    """
    Инициализация Telegram бота для отправки алертов
    
    Args:
        bot_instance: Экземпляр Telegram бота
        chat_ids: Список ID чатов для отправки
    """
    global _telegram_bot, _chat_ids
    _telegram_bot = bot_instance
    _chat_ids = chat_ids
    debug_log(f"Telegram бот инициализирован для {len(chat_ids)} чатов")

def set_silent_override(enabled: Optional[bool]) -> None:
    """
    Установить принудительное переопределение тихого режима
    
    Args:
        enabled: None - автоматический режим, True - принудительно тихий, False - принудительно громкий
    """
    global _silent_override
    old_value = _silent_override
    _silent_override = enabled
    
    status_map = {
        None: "автоматический режим",
        True: "принудительно тихий",
        False: "принудительно громкий"
    }
    
    debug_log(f"Переопределение тихого режима изменено: {status_map.get(old_value, 'неизвестно')} → {status_map.get(enabled, 'неизвестно')}")

def get_silent_override() -> Optional[bool]:
    """
    Возвращает текущий принудительный режим тихих уведомлений.
    """
    return _silent_override

def is_silent_time() -> bool:
    """
    Проверяет, находится ли текущее время в 'тихом' периоде
    
    Returns:
        True если тихий режим активен
    """
    global _silent_override
    
    # Если есть принудительное переопределение
    if _silent_override is not None:
        return _silent_override  # True - тихий, False - громкий

    # Стандартная проверка по времени
    current_hour = datetime.now().hour
    
    # Если период переходит через полночь (например, 20:00 - 09:00)
    if _config.silent_start > _config.silent_end:
        return current_hour >= _config.silent_start or current_hour < _config.silent_end
    
    # Период в пределах одних суток
    return _config.silent_start <= current_hour < _config.silent_end

def should_send_alert(alert_type: str, force: bool) -> bool:
    """
    Проверяет, нужно ли отправлять алерт
    
    Args:
        alert_type: Тип алерта (critical, warning, info)
        force: Принудительная отправка
        
    Returns:
        True если нужно отправить алерт
    """
    if not _config.enabled:
        debug_log("Алерты отключены в конфигурации")
        return False
    
    if force:
        return True
    
    if is_silent_time():
        return False
    
    if alert_type in _config.thresholds:
        threshold_config = _config.thresholds[alert_type]
        if threshold_config["always_send"]:
            return True
    
    # Проверяем тихий режим для не-критических алертов
    if alert_type != "critical" and is_silent_time():
        debug_log("Тихий режим активен, алерт не отправляется")
        return False
    
    return True

def send_alert(
    message: str,
    alert_type: str = "info",
    force: bool = False,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Универсальная функция отправки алертов
    
    Args:
        message: Текст сообщения
        alert_type: Тип алерта (critical, warning, info)
        force: Принудительная отправка
        tags: Теги для категоризации алерта
        metadata: Дополнительные метаданные
        
    Returns:
        True если сообщение отправлено успешно
    """
    if not should_send_alert(alert_type, force):
        return False
    
    # Проверяем кд для одинаковых алертов
    if not force and _is_cooldown_active(message):
        debug_log(f"Алерт находится в кд: {message[:50]}...")
        return False
    
    # Добавляем префикс в зависимости от типа алерта
    prefixes = {
        "critical": "🚨 ",
        "warning": "⚠️ ",
        "info": "ℹ️ "
    }
    
    prefix = prefixes.get(alert_type, "")
    full_message = f"{prefix}{message}"
    
    # Логируем алерт
    log_levels = {
        "critical": error_log,
        "warning": debug_log,
        "info": debug_log
    }
    
    log_func = log_levels.get(alert_type, debug_log)
    log_func(f"Отправка алерта [{alert_type}]: {message[:100]}...")
    
    # Отправляем через все доступные каналы
    sent = False
    errors = []
    
    # Telegram
    if _telegram_bot and _chat_ids:
        telegram_sent = _send_telegram_alert(full_message, alert_type)
        if telegram_sent:
            sent = True
        else:
            errors.append("Telegram: ошибка отправки")
    
    # Записываем в историю
    _record_alert({
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "type": alert_type,
        "sent": sent,
        "tags": tags or [],
        "metadata": metadata or {},
        "errors": errors
    })
    
    return sent

def _send_telegram_alert(message: str, alert_type: str) -> bool:
    """
    Отправка алерта через Telegram
    
    Args:
        message: Текст сообщения
        alert_type: Тип алерта
        
    Returns:
        True если отправлено успешно
    """
    if not _telegram_bot or not _chat_ids:
        error_log("Telegram бот не инициализирован")
        return False
    
    success_count = 0
    total_chats = len(_chat_ids)
    
    for i, chat_id in enumerate(_chat_ids):
        try:
            # Для критических алертов добавляем дополнительное форматирование
            if alert_type == "critical":
                formatted_message = f"*{message}*"
            else:
                formatted_message = message
            
            _telegram_bot.send_message(
                chat_id=chat_id,
                text=formatted_message,
                parse_mode='Markdown' if alert_type == "critical" else None
            )
            success_count += 1
            
            # Небольшая задержка между отправками чтобы не превысить лимиты
            if i < total_chats - 1:
                time.sleep(0.1)
                
        except Exception as e:
            error_log(f"Ошибка отправки в чат {chat_id}: {e}")
    
    success_rate = success_count / total_chats if total_chats > 0 else 0
    debug_log(f"Telegram алерт отправлен: {success_count}/{total_chats} успешно ({success_rate:.0%})")
    
    return success_count > 0

def _is_cooldown_active(message: str, check_period: int = None) -> bool:
    """
    Проверяет, активен ли кд для сообщения
    
    Args:
        message: Текст сообщения
        check_period: Период проверки в секундах (если None, используется конфиг)
        
    Returns:
        True если кд активен
    """
    period = check_period or _config.cooldown_seconds
    now = time.time()
    
    # Ищем похожие сообщения в истории
    for alert in reversed(_alert_history):
        if alert["message"] == message and alert["sent"]:
            alert_time = datetime.fromisoformat(alert["timestamp"]).timestamp()
            if now - alert_time < period:
                return True
    
    return False

def _record_alert(alert_data: Dict[str, Any]) -> None:
    """
    Записывает алерт в историю
    
    Args:
        alert_data: Данные алерта
    """
    global _alert_history
    
    _alert_history.append(alert_data)
    
    # Ограничиваем размер истории
    if len(_alert_history) > _max_history_size:
        _alert_history = _alert_history[-_max_history_size:]
    
    # Логируем в файл для отладки
    if alert_data.get("sent"):
        status = "✅ Отправлен"
    else:
        status = "❌ Не отправлен"
    
    debug_log(f"Алерт записан в историю: {alert_data['type']} - {status}")

def get_alert_history(
    limit: int = 50,
    alert_type: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Получить историю алертов
    
    Args:
        limit: Максимальное количество записей
        alert_type: Фильтр по типу алерта
        tags: Фильтр по тегам
        
    Returns:
        Список алертов
    """
    filtered_history = _alert_history
    
    if alert_type:
        filtered_history = [a for a in filtered_history if a["type"] == alert_type]
    
    if tags:
        filtered_history = [a for a in filtered_history if any(tag in a.get("tags", []) for tag in tags)]
    
    return filtered_history[-limit:]

def clear_alert_history() -> int:
    """
    Очистить историю алертов
    
    Returns:
        Количество удаленных записей
    """
    global _alert_history
    count = len(_alert_history)
    _alert_history = []
    debug_log(f"История алертов очищена, удалено {count} записей")
    return count

def get_alert_stats() -> Dict[str, Any]:
    """
    Получить статистику по алертам
    
    Returns:
        Словарь со статистикой
    """
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    
    # Фильтруем алерты за сегодня
    today_alerts = [
        a for a in _alert_history 
        if datetime.fromisoformat(a["timestamp"]) >= today_start
    ]
    
    # Группируем по типам
    by_type = {}
    for alert in today_alerts:
        alert_type = alert["type"]
        if alert_type not in by_type:
            by_type[alert_type] = {"total": 0, "sent": 0}
        by_type[alert_type]["total"] += 1
        if alert["sent"]:
            by_type[alert_type]["sent"] += 1
    
    return {
        "total_all_time": len(_alert_history),
        "total_today": len(today_alerts),
        "by_type": by_type,
        "silent_mode": is_silent_time(),
        "silent_override": _silent_override
    }

def configure(
    silent_start: Optional[int] = None,
    silent_end: Optional[int] = None,
    enabled: Optional[bool] = None,
    cooldown_seconds: Optional[int] = None
) -> None:
    """
    Настройка параметров алертов
    
    Args:
        silent_start: Начало тихого режима (0-23)
        silent_end: Конец тихого режима (0-23)
        enabled: Включены ли алерты
        cooldown_seconds: Кд между одинаковыми алертами
    """
    if silent_start is not None:
        _config.silent_start = silent_start
    if silent_end is not None:
        _config.silent_end = silent_end
    if enabled is not None:
        _config.enabled = enabled
    if cooldown_seconds is not None:
        _config.cooldown_seconds = cooldown_seconds
    
    debug_log(f"Конфигурация алертов обновлена: silent={_config.silent_start}:00-{_config.silent_end}:00, enabled={_config.enabled}, cooldown={_config.cooldown_seconds}с")

# Алиасы для обратной совместимости
send_message = send_alert