"""
/core/monitor_parts/alerts.py
Server Monitoring System v8.62.63
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Automatic resource monitoring + alert pipeline, extracted from
core/monitor_core.py (PR5) and unified across modules/resources.py (PR8).
Система мониторинга серверов
Версия: 8.62.63
Автор: Александр Суханов (c)
Лицензия: MIT
Автоматическая проверка ресурсов всех серверов, дедупликация алертов
по интервалу из БД и финальная рассылка одного сводного сообщения.
PR8 ввёл декларативную схему ``ResourceAlertRule`` + pure-функцию
``evaluate_alert_rules``, чтобы заменить три копи-пастных блока
(disk/cpu/ram) и устранить дубликаты с ``modules/resources.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from core.monitor_state import state
from lib.logging import debug_log


@dataclass(frozen=True)
class ResourceAlertRule:
    """Декларативное правило одного типа ресурсного алерта.

    Заменяет три параллельных copy-paste-блока в прежнем
    ``check_resource_alerts``. `requires_streak` = 1 для disk (срабатывает
    сразу), = 2 для cpu/ram (защита от точечных всплесков — нужно
    две проверки подряд выше порога).
    """

    metric: str  # ключ в resource_entry: "disk" / "cpu" / "ram"
    threshold_key: str  # ключ в RESOURCE_ALERT_THRESHOLDS: "disk_alert" и т.п.
    requires_streak: int  # 1 — сразу, 2 — две подряд (текущая + предыдущая)
    label: str  # человекочитаемая метка, входит в текст алерта
    emoji: str  # эмодзи-маркер, используется группировкой `send_resource_alerts`
    immediate_template: str  # шаблон сообщения для streak=1
    streak_template: str  # шаблон сообщения для streak>=2 (с двумя значениями)


ALERT_RULES: tuple[ResourceAlertRule, ...] = (
    ResourceAlertRule(
        metric="disk",
        threshold_key="disk_alert",
        requires_streak=1,
        label="Дисковое пространство",
        emoji="💾",
        immediate_template=(
            "{emoji} **{label}** на {server}: {current}% (превышен порог {threshold}%)"
        ),
        streak_template="",  # не используется — disk алертит сразу
    ),
    ResourceAlertRule(
        metric="cpu",
        threshold_key="cpu_alert",
        requires_streak=2,
        label="Процессор",
        emoji="💻",
        immediate_template="",  # не используется — cpu требует 2 подряд
        streak_template=(
            "{emoji} **{label}** на {server}: {prev}% → {current}%"
            " (2 проверки подряд >= {threshold}%)"
        ),
    ),
    ResourceAlertRule(
        metric="ram",
        threshold_key="ram_alert",
        requires_streak=2,
        label="Память",
        emoji="🧠",
        immediate_template="",
        streak_template=(
            "{emoji} **{label}** на {server}: {prev}% → {current}%"
            " (2 проверки подряд >= {threshold}%)"
        ),
    ),
)


def evaluate_alert_rules(
    ip: str,
    current_resource: dict[str, Any],
    history: list[dict[str, Any]],
    sent_state: dict[str, datetime],
    *,
    rules: tuple[ResourceAlertRule, ...] = ALERT_RULES,
    thresholds: dict[str, int] | None = None,
    alert_interval_seconds: int | None = None,
    now: datetime | None = None,
) -> list[str]:
    """Pure-функция: применяет декларативный список правил к одной
    проверке ресурсов и возвращает список текстов сработавших алертов.

    Параметры намеренно инжектируемые — то же ядро используется и из
    `state.resource_history` / `state.resource_alerts_sent` (центральный
    цикл мониторинга), и из локальных полей `ResourcesChecker` (разовые
    ручные проверки), и из unit-тестов с in-memory dict-ами.

    Побочный эффект: при срабатывании каждого правила `sent_state[key]`
    обновляется текущим временем (`now` или `datetime.now()`).
    """
    if thresholds is None or alert_interval_seconds is None:
        from config.db_settings import RESOURCE_ALERT_INTERVAL, RESOURCE_ALERT_THRESHOLDS

        if thresholds is None:
            thresholds = RESOURCE_ALERT_THRESHOLDS
        if alert_interval_seconds is None:
            alert_interval_seconds = RESOURCE_ALERT_INTERVAL

    moment = now or datetime.now()
    server_name = current_resource.get("server_name", ip)
    alerts: list[str] = []

    for rule in rules:
        threshold = thresholds.get(rule.threshold_key)
        if threshold is None:
            continue

        current_value = current_resource.get(rule.metric, 0)
        if current_value < threshold:
            continue

        # Для streak > 1 проверяем предыдущие записи истории
        if rule.requires_streak > 1:
            need_prev = rule.requires_streak - 1
            if len(history) < need_prev:
                continue
            previous_values = [entry.get(rule.metric, 0) for entry in history[-need_prev:]]
            if not all(value >= threshold for value in previous_values):
                continue
            prev_value = previous_values[-1]
            text = rule.streak_template.format(
                emoji=rule.emoji,
                label=rule.label,
                server=server_name,
                prev=prev_value,
                current=current_value,
                threshold=threshold,
            )
        else:
            text = rule.immediate_template.format(
                emoji=rule.emoji,
                label=rule.label,
                server=server_name,
                current=current_value,
                threshold=threshold,
            )

        # Дедупликация по интервалу
        alert_key = f"{ip}_{rule.metric}"
        last_sent = sent_state.get(alert_key)
        if last_sent is not None and (moment - last_sent).total_seconds() <= alert_interval_seconds:
            continue

        alerts.append(text)
        sent_state[alert_key] = moment

    return alerts


def check_resources_automatically() -> None:
    """Автоматическая проверка ресурсов с умными предупреждениями.

    Раз в `RESOURCE_CHECK_INTERVAL` (вызывается из основного цикла
    `start_monitoring`) обходит все серверы, опрашивает `extensions.server_checks`,
    накапливает историю в `state.resource_history` (максимум 10 точек на сервер)
    и через `check_resource_alerts` собирает срабатывающие правила.
    Все срабатывания склеиваются и шлются одним сообщением через
    `send_resource_alerts`.
    """
    from core.monitor_core import (
        _resource_monitor_enabled,
        is_server_monitoring_enabled,
        is_silent_time,
    )

    if not _resource_monitor_enabled():
        debug_log("⏸️ Проверка ресурсов пропущена (расширение отключено)")
        return

    debug_log("🔍 Автоматическая проверка ресурсов серверов...")

    if not state.monitoring_active or is_silent_time():
        debug_log("⏸️ Проверка ресурсов пропущена (мониторинг неактивен или тихий режим)")
        return

    current_time = datetime.now()
    alerts_found: list[str] = []

    for server in state.servers:
        try:
            ip = server["ip"]
            server_name = server["name"]

            if not is_server_monitoring_enabled(ip):
                continue

            debug_log(f"🔍 Проверяем ресурсы {server_name} ({ip})")

            current_resources: dict[str, Any] | None = None
            if server["type"] == "ssh":
                from extensions.server_checks import get_linux_resources_improved

                current_resources = get_linux_resources_improved(ip)
            elif server["type"] == "rdp":
                from extensions.server_checks import get_windows_resources_improved

                current_resources = get_windows_resources_improved(ip)

            if not current_resources:
                continue

            if ip not in state.resource_history:
                state.resource_history[ip] = []

            resource_entry = {
                "timestamp": current_time,
                "cpu": current_resources.get("cpu", 0),
                "ram": current_resources.get("ram", 0),
                "disk": current_resources.get("disk", 0),
                "server_name": server_name,
            }

            state.resource_history[ip].append(resource_entry)

            if len(state.resource_history[ip]) > 10:
                state.resource_history[ip] = state.resource_history[ip][-10:]

            server_alerts = check_resource_alerts(ip, resource_entry)

            if server_alerts:
                alerts_found.extend(server_alerts)
                debug_log(f"⚠️ Найдены проблемы для {server_name}: {server_alerts}")

        except Exception as e:
            debug_log(f"❌ Ошибка при проверке ресурсов {server['name']}: {e}")
            continue

    if alerts_found:
        send_resource_alerts(alerts_found)

    state.last_resource_check = current_time
    debug_log(
        f"✅ Автоматическая проверка ресурсов завершена. Найдено проблем: {len(alerts_found)}"
    )


def check_resource_alerts(ip: str, current_resource: dict[str, Any]) -> list[str]:
    """Возвращает список текстов алертов, которые должны быть отправлены сейчас.

    Тонкая обёртка над декларативной `evaluate_alert_rules`, привязанная
    к глобальному `state.resource_history` / `state.resource_alerts_sent`.
    Логика дублирования по интервалу и streak'ов CPU/RAM вынесена в схему
    `ALERT_RULES` — три копии (по одной на метрику) больше не нужны.
    """
    history = state.resource_history.get(ip, [])[:-1]
    return evaluate_alert_rules(
        ip,
        current_resource,
        history,
        state.resource_alerts_sent,
    )


def send_resource_alerts(alerts: list[str]) -> None:
    """Склеивает алерты по типу ресурса и шлёт сводный alert через `send_alert`."""
    from core.monitor_core import send_alert

    if not alerts:
        return

    message = "🚨 *Проблемы с ресурсами серверов*\n\n"

    # Группировка по эмодзи из ALERT_RULES — порядок групп = порядок правил.
    rule_order: dict[str, ResourceAlertRule] = {rule.emoji: rule for rule in ALERT_RULES}
    grouped: dict[str, list[str]] = {emoji: [] for emoji in rule_order}
    for alert in alerts:
        for emoji in rule_order:
            if emoji in alert:
                grouped[emoji].append(alert)
                break

    for emoji, rule in rule_order.items():
        group = grouped.get(emoji, [])
        if not group:
            continue
        message += f"{emoji} **{rule.label}:**\n"
        for alert in group:
            parts = alert.split("на ")
            if len(parts) > 1:
                message += f"• {parts[1]}\n"
        message += "\n"

    message += f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}"

    send_alert(message)
    debug_log(f"✅ Отправлены алерты по ресурсам: {len(alerts)} проблем")


__all__ = [
    "ALERT_RULES",
    "ResourceAlertRule",
    "check_resource_alerts",
    "check_resources_automatically",
    "evaluate_alert_rules",
    "send_resource_alerts",
]
