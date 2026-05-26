"""
/core/monitor_parts/alerts.py
Server Monitoring System v8.62.50
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Automatic resource monitoring + alert pipeline, extracted from
core/monitor_core.py (PR5 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.50
Автор: Александр Суханов (c)
Лицензия: MIT
Автоматическая проверка ресурсов всех серверов, дедупликация алертов
по интервалу из БД и финальная рассылка одного сводного сообщения.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.monitor_state import state
from lib.logging import debug_log


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

    Disk алертит сразу при превышении порога; CPU и RAM — только при
    двух подряд проверках выше порога (защита от точечных всплесков).
    `state.resource_alerts_sent` хранит время последней отправки на
    каждый `{ip}_{metric}`-ключ, чтобы дублировать алерт не чаще, чем
    раз в `RESOURCE_ALERT_INTERVAL`.
    """
    from config.db_settings import RESOURCE_ALERT_INTERVAL, RESOURCE_ALERT_THRESHOLDS

    alerts: list[str] = []
    server_name = current_resource["server_name"]
    history = state.resource_history.get(ip, [])[:-1]

    disk_usage = current_resource.get("disk", 0)
    if disk_usage >= RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
        alert_key = f"{ip}_disk"
        if (
            alert_key not in state.resource_alerts_sent
            or (datetime.now() - state.resource_alerts_sent[alert_key]).total_seconds()
            > RESOURCE_ALERT_INTERVAL
        ):
            alerts.append(
                f"💾 **Дисковое пространство** на {server_name}: {disk_usage}%"
                f" (превышен порог {RESOURCE_ALERT_THRESHOLDS['disk_alert']}%)"
            )
            state.resource_alerts_sent[alert_key] = datetime.now()

    cpu_usage = current_resource.get("cpu", 0)
    if cpu_usage >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"] and len(history) >= 1:
        prev_cpu = history[-1].get("cpu", 0)
        if prev_cpu >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
            alert_key = f"{ip}_cpu"
            if (
                alert_key not in state.resource_alerts_sent
                or (datetime.now() - state.resource_alerts_sent[alert_key]).total_seconds()
                > RESOURCE_ALERT_INTERVAL
            ):
                alerts.append(
                    f"💻 **Процессор** на {server_name}: {prev_cpu}% → {cpu_usage}%"
                    f" (2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS['cpu_alert']}%)"
                )
                state.resource_alerts_sent[alert_key] = datetime.now()

    ram_usage = current_resource.get("ram", 0)
    if ram_usage >= RESOURCE_ALERT_THRESHOLDS["ram_alert"] and len(history) >= 1:
        prev_ram = history[-1].get("ram", 0)
        if prev_ram >= RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
            alert_key = f"{ip}_ram"
            if (
                alert_key not in state.resource_alerts_sent
                or (datetime.now() - state.resource_alerts_sent[alert_key]).total_seconds()
                > RESOURCE_ALERT_INTERVAL
            ):
                alerts.append(
                    f"🧠 **Память** на {server_name}: {prev_ram}% → {ram_usage}%"
                    f" (2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS['ram_alert']}%)"
                )
                state.resource_alerts_sent[alert_key] = datetime.now()

    return alerts


def send_resource_alerts(alerts: list[str]) -> None:
    """Склеивает алерты по типу ресурса и шлёт сводный alert через `send_alert`."""
    from core.monitor_core import send_alert

    if not alerts:
        return

    message = "🚨 *Проблемы с ресурсами серверов*\n\n"

    disk_alerts = [a for a in alerts if "💾" in a]
    cpu_alerts = [a for a in alerts if "💻" in a]
    ram_alerts = [a for a in alerts if "🧠" in a]

    for label, group in (
        ("💾 **Дисковое пространство:**", disk_alerts),
        ("💻 **Процессор (CPU):**", cpu_alerts),
        ("🧠 **Память (RAM):**", ram_alerts),
    ):
        if not group:
            continue
        message += f"{label}\n"
        for alert in group:
            parts = alert.split("на ")
            if len(parts) > 1:
                message += f"• {parts[1]}\n"
        message += "\n"

    message += f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}"

    send_alert(message)
    debug_log(f"✅ Отправлены алерты по ресурсам: {len(alerts)} проблем")


__all__ = [
    "check_resource_alerts",
    "check_resources_automatically",
    "send_resource_alerts",
]
