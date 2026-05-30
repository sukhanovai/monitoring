"""
/core/monitor_parts/availability.py
Server Monitoring System v8.62.75
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server availability transition handlers extracted from
core/monitor_core.py (PR5 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.75
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики смены статуса сервера UP/DOWN, выделенные из монолитного
core/monitor_core.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.monitor_state import state


def handle_server_up(ip: str, status: dict[str, Any], current_time: datetime) -> None:
    """Обработка доступного сервера.

    Если ранее был отправлен алерт о падении — отправляет «восстановлен»
    с расчётом длительности простоя. Сбрасывает `alert_sent` в
    state.server_status и переписывает запись свежим временем last_up.
    Зависит от модульного `send_alert`, который импортирован из
    `core.monitor_core` лениво, чтобы не образовывать цикла.
    """
    from core.monitor_core import send_alert

    last_up = status.get("last_up")

    if status.get("alert_sent"):
        if last_up:
            downtime = (current_time - last_up).total_seconds()
            send_alert(f"✅ {status['name']} ({ip}) доступен (простой: {int(downtime // 60)} мин)")
        else:
            send_alert(f"✅ {status['name']} ({ip}) доступен")

    state.server_status[ip] = {
        "last_up": current_time,
        "alert_sent": False,
        "name": status.get("name"),
        "type": status.get("type"),
        "resources": state.server_status.get(ip, {}).get("resources"),
        "last_alert": state.server_status.get(ip, {}).get("last_alert", {}),
    }


def handle_server_down(ip: str, status: dict[str, Any], current_time: datetime) -> None:
    """Обработка недоступного сервера.

    Если простой превысил `MAX_FAIL_TIME` из конфига и алерт ещё не
    отправлялся — шлёт критический алерт и помечает `alert_sent=True`.
    """
    from core.monitor_core import get_config, send_alert

    config = get_config()

    last_up = status.get("last_up")
    if not last_up:
        state.server_status[ip]["last_up"] = current_time
        status["last_up"] = current_time
        last_up = current_time

    downtime = (current_time - last_up).total_seconds()

    if downtime >= config.MAX_FAIL_TIME and not status.get("alert_sent"):
        send_alert(
            f"🚨 {status['name']} ({ip}) не отвечает (проверка: {status['type'].upper()})",
            alert_type="critical",
        )
        state.server_status[ip]["alert_sent"] = True


__all__ = ["handle_server_down", "handle_server_up"]
