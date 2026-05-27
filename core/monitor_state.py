"""
/core/monitor_state.py
Server Monitoring System v8.62.62
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mutable runtime state of the monitoring core extracted from the
monolithic core/monitor_core.py module-level globals.
Система мониторинга серверов
Версия: 8.62.62
Автор: Александр Суханов (c)
Лицензия: MIT
Изменяемое runtime-состояние ядра мониторинга, вынесенное из
module-level глобалов core/monitor_core.py. Подготовка к разделению
монолита на пакет core/monitor/* (PR5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MonitoringState:
    """Singleton-контейнер runtime-состояния ядра мониторинга.

    Поля раньше жили как module-level переменные core/monitor_core.py.
    Все внутренние модули core/monitor/* должны читать и менять
    состояние через единственный экземпляр ``state``.
    """

    bot: Any = None
    server_status: dict[str, Any] = field(default_factory=dict)
    morning_data: dict[str, Any] = field(default_factory=dict)
    monitoring_active: bool = True
    last_check_time: datetime = field(default_factory=datetime.now)
    servers: list[dict[str, Any]] = field(default_factory=list)
    resource_history: dict[str, Any] = field(default_factory=dict)
    last_resource_check: datetime = field(default_factory=datetime.now)
    resource_alerts_sent: dict[str, Any] = field(default_factory=dict)
    last_report_date: Any = None
    last_collection_schedule_time: Any = None
    sent_collection_slots: set[str] = field(default_factory=set)


# Глобальный singleton состояния. Импортируется в monitor_core.py
# и в дальнейшем — в подмодулях core/monitor/*.
state = MonitoringState()


# Имена полей state, проксируемых через core.monitor_core.__getattr__
# ради обратной совместимости с внешними импортёрами
# (`from core.monitor_core import server_status`).
STATE_FIELDS = frozenset(
    {
        "bot",
        "server_status",
        "morning_data",
        "monitoring_active",
        "last_check_time",
        "servers",
        "resource_history",
        "last_resource_check",
        "resource_alerts_sent",
        "last_report_date",
        "last_collection_schedule_time",
        "sent_collection_slots",
    }
)
