"""
/extensions/zfs_free_space_monitor.py
Server Monitoring System v8.62.13
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ZFS free space monitoring over SSH
Система мониторинга серверов
Версия: 8.62.13
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг свободного места ZFS по SSH
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from extensions.server_checks import run_ssh_command
from lib.logging import debug_log

_ALERT_SENT_AT: dict[str, datetime] = {}
_ALERT_ACTIVE: dict[str, bool] = {}


def normalize_zfs_servers(raw_value: Any) -> dict[str, dict[str, Any]]:
    """Привести ZFS_SERVERS к формату {name: {ip, threshold, enabled}}."""
    if not isinstance(raw_value, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for host_name, host_value in raw_value.items():
        if not isinstance(host_name, str) or not host_name.strip():
            continue

        host_key = host_name.strip()
        if isinstance(host_value, dict):
            ip = str(host_value.get("ip", "")).strip()
            enabled = bool(host_value.get("enabled", True))
            threshold = host_value.get("threshold", host_value.get("alert_threshold", 15))
        else:
            ip = ""
            enabled = True
            threshold = 15

        try:
            threshold_int = int(threshold)
        except (TypeError, ValueError):
            threshold_int = 15

        threshold_int = max(1, min(95, threshold_int))

        normalized[host_key] = {
            "ip": ip,
            "enabled": enabled,
            "threshold": threshold_int,
        }

    return normalized


def get_zfs_servers_config() -> dict[str, dict[str, Any]]:
    """Получить нормализованный конфиг ZFS-серверов."""
    return normalize_zfs_servers(config_manager.get_setting("ZFS_SERVERS", {}))


def _resolve_free_space_alert_threshold(threshold: int) -> float:
    """Нормализовать порог алерта для свободного места.

    - 1..50: интерпретируется как минимальный % свободного места (legacy).
    - 51..95: интерпретируется как % заполнения (used),
      т.е. триггер на free <= (100 - threshold).
    """
    normalized = max(1, min(95, int(threshold)))
    if normalized > 50:
        return float(100 - normalized)
    return float(normalized)


def collect_zfs_free_space() -> tuple[list[dict[str, Any]], list[str]]:
    """Собирает свободное место по пулам всех активных ZFS-хостов."""
    if not extension_manager.is_extension_enabled("zfs_monitor"):
        return [], []

    server_map = get_zfs_servers_config()
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for host_name, host_cfg in sorted(server_map.items()):
        if not host_cfg.get("enabled", True):
            continue

        host_ip = str(host_cfg.get("ip", "")).strip()
        threshold = int(host_cfg.get("threshold", 15))

        if not host_ip:
            errors.append(f"⚠️ {host_name}: не указан IP")
            continue

        command = "zfs list -H -p -o name,used,avail"
        success, stdout, stderr = run_ssh_command(host_ip, command, timeout=20)
        if not success:
            error_text = (stderr or "ошибка подключения").strip()
            errors.append(f"❌ {host_name} ({host_ip}): {error_text[:120]}")
            continue

        rows = [row for row in stdout.splitlines() if row.strip()]
        if not rows:
            errors.append(f"⚠️ {host_name} ({host_ip}): пулы не найдены")
            continue

        for row in rows:
            parts = row.split("\t")
            if len(parts) < 3:
                continue

            dataset_name, used_raw, avail_raw = parts[:3]
            pool_name = dataset_name.split("/", 1)[0].strip()
            if not pool_name or "/" in dataset_name:
                continue

            try:
                used_bytes = int(used_raw)
                avail_bytes = int(avail_raw)
            except ValueError:
                continue

            size_bytes = used_bytes + avail_bytes
            free_percent = (avail_bytes * 100.0 / size_bytes) if size_bytes > 0 else 0.0
            results.append(
                {
                    "host_name": host_name,
                    "ip": host_ip,
                    "pool": pool_name,
                    "size_bytes": size_bytes,
                    "alloc_bytes": used_bytes,
                    "free_bytes": avail_bytes,
                    "free_percent": round(free_percent, 1),
                    "threshold": threshold,
                    "health": "N/A",
                    "is_alert": free_percent <= _resolve_free_space_alert_threshold(threshold),
                }
            )

    results.sort(key=lambda item: (item["host_name"], item["pool"]))
    return results, errors


def _bytes_to_human(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    num = float(max(value, 0))
    for unit in units:
        if num < 1024.0 or unit == units[-1]:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{value} B"


def build_zfs_free_space_lines(results: list[dict[str, Any]], errors: list[str]) -> list[str]:
    """Построить markdown-строки отчета по свободному месту ZFS."""
    lines: list[str] = ["💽 *Свободное место ZFS пулов*", ""]

    if not results:
        lines.append("❌ Нет данных по пулам ZFS.")
    else:
        alerts_count = sum(1 for row in results if row.get("is_alert"))
        lines.append(f"• Пулов: {len(results)} · 🚨 {alerts_count}")
        lines.append("")

        current_host = None
        for row in results:
            host_name = row["host_name"]
            if host_name != current_host:
                current_host = host_name
                lines.append(f"*{host_name}* ({row['ip']})")

            icon = "🚨" if row.get("is_alert") else "🟢"
            threshold = int(row["threshold"])
            threshold_text = (
                f"threshold {threshold}% used / {100 - threshold}% free"
                if threshold > 50
                else f"threshold {threshold}% free"
            )
            lines.append(
                f"{icon} `{row['pool']}` {row['free_percent']}% free"
                f" ({_bytes_to_human(int(row['free_bytes']))} / {_bytes_to_human(int(row['size_bytes']))})"
                f" · {threshold_text}"
            )

        lines.append("")

    if errors:
        lines.append("*Ошибки опроса:*")
        lines.extend(errors)
        lines.append("")

    lines.append(f"🕒 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return lines


def check_zfs_free_space_alerts(send_alert_func, repeat_interval_seconds: int = 1800) -> None:
    """Плановый опрос ZFS и отправка алертов по порогам."""
    if not extension_manager.is_extension_enabled("zfs_monitor"):
        return

    now = datetime.now()
    results, errors = collect_zfs_free_space()

    if errors:
        debug_log(f"⚠️ ZFS free space polling issues: {'; '.join(errors)}")

    for row in results:
        key = f"{row['host_name']}::{row['pool']}"
        is_alert = bool(row.get("is_alert"))
        was_alert = _ALERT_ACTIVE.get(key, False)
        last_sent_at = _ALERT_SENT_AT.get(key)

        if is_alert:
            should_send = (
                not was_alert
                or last_sent_at is None
                or (now - last_sent_at).total_seconds() >= repeat_interval_seconds
            )
            if should_send:
                send_alert_func(
                    "🚨 ZFS: мало свободного места\n"
                    f"• Хост: {row['host_name']} ({row['ip']})\n"
                    f"• Пул: {row['pool']}\n"
                    f"• Свободно: {row['free_percent']}% "
                    f"({_bytes_to_human(int(row['free_bytes']))} из {_bytes_to_human(int(row['size_bytes']))})\n"
                    f"• Порог: {row['threshold']}%\n"
                    f"• Health: {row['health']}"
                )
                _ALERT_SENT_AT[key] = now

            _ALERT_ACTIVE[key] = True
        else:
            if was_alert:
                send_alert_func(
                    "✅ ZFS: свободное место восстановлено\n"
                    f"• Хост: {row['host_name']} ({row['ip']})\n"
                    f"• Пул: {row['pool']}\n"
                    f"• Свободно: {row['free_percent']}%"
                )
            _ALERT_ACTIVE[key] = False
