"""
/core/monitor_parts/resource_checks.py
Server Monitoring System v8.62.80
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified CPU/RAM/disk resource check renderers, extracted from
core/monitor_core.py (PR5 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.80
Автор: Александр Суханов (c)
Лицензия: MIT
Параметризованная проверка ресурсов с детальным прогрессом, заменяет
три копии `perform_cpu_check`/`perform_ram_check`/`perform_disk_check`
одной функцией `perform_resource_check(... ResourceCheckSpec)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from lib.logging import debug_log
from lib.utils import progress_bar


@dataclass(frozen=True)
class ResourceCheckSpec:
    """Параметры одного типа ресурсной проверки (CPU/RAM/Disk).

    Унифицирует то, что в монолите `monitor_core.py` повторялось трижды:
    разные пороги, заголовки сообщения и эмодзи, разные надписи в
    статистике, разный набор кнопок reply_markup.
    """

    metric: str  # ключ внутри resources-словаря: "cpu" / "ram" / "disk"
    progress_emoji: str  # "💻" / "🧠" / "💾"
    progress_caption: str  # "Проверка CPU..." и т. п.
    report_title: str  # "Загрузка CPU серверов", "Использование RAM серверов", ...
    warning_threshold: int  # граница «жёлтого» уровня
    critical_threshold: int  # граница «красного» уровня
    stat_label_critical: str  # "Высокая нагрузка (>80%)" и т. п.
    stat_label_warning: str  # "Средняя нагрузка (60-80%)" и т. п.
    callback_id: str  # "check_cpu" / "check_ram" / "check_disk"
    other_buttons: tuple[tuple[str, str], ...]  # (text, callback_data) для соседних метрик


CPU_SPEC = ResourceCheckSpec(
    metric="cpu",
    progress_emoji="💻",
    progress_caption="Проверка CPU...",
    report_title="Загрузка CPU серверов",
    warning_threshold=60,
    critical_threshold=80,
    stat_label_critical="Высокая нагрузка (>80%)",
    stat_label_warning="Средняя нагрузка (60-80%)",
    callback_id="check_cpu",
    other_buttons=(
        ("🧠 Проверить RAM", "check_ram"),
        ("💾 Проверить Disk", "check_disk"),
    ),
)

RAM_SPEC = ResourceCheckSpec(
    metric="ram",
    progress_emoji="🧠",
    progress_caption="Проверка RAM...",
    report_title="Использование RAM серверов",
    warning_threshold=70,
    critical_threshold=85,
    stat_label_critical="Высокое использование (>85%)",
    stat_label_warning="Среднее использование (70-85%)",
    callback_id="check_ram",
    other_buttons=(
        ("💻 Проверить CPU", "check_cpu"),
        ("💾 Проверить Disk", "check_disk"),
    ),
)

DISK_SPEC = ResourceCheckSpec(
    metric="disk",
    progress_emoji="💾",
    progress_caption="Проверка Disk...",
    report_title="Использование дискового пространства",
    warning_threshold=80,
    critical_threshold=90,
    stat_label_critical="Критическое использование (>90%)",
    stat_label_warning="Предупреждение (80-90%)",
    callback_id="check_disk",
    other_buttons=(
        ("💻 Проверить CPU", "check_cpu"),
        ("🧠 Проверить RAM", "check_ram"),
    ),
)


def _format_value(value: int, spec: ResourceCheckSpec) -> str:
    if value > spec.critical_threshold:
        return f"🚨 {value}%"
    if value > spec.warning_threshold:
        return f"⚠️ {value}%"
    return f"{value}%"


def _render_group(results: list[dict[str, Any]], group_label: str, spec: ResourceCheckSpec) -> str:
    text = f"**{group_label}:**\n"
    for result in results[:10]:
        server = result["server"]
        value = result[spec.metric]
        icon = "🟢" if result["success"] else "🔴"
        text += f"{icon} {server['name']}: {_format_value(value, spec)}\n"
    if len(results) > 10:
        text += f"• ... и еще {len(results) - 10} серверов\n"
    return text


def perform_resource_check(
    context: Any,
    chat_id: int,
    progress_message_id: int,
    spec: ResourceCheckSpec,
) -> None:
    """Параметризованная проверка одной метрики ресурсов на всех SSH/RDP серверах.

    Унифицирует поведение бывших `perform_cpu_check` / `perform_ram_check` /
    `perform_disk_check`: рассылает прогресс в Telegram, опрашивает
    `extensions.server_checks.get_(linux|windows)_resources_improved`, собирает
    отчёт с группировкой Windows/Linux и статистикой.
    """

    def update_progress(progress: float, status: str) -> None:
        progress_text = (
            f"{spec.progress_emoji} {spec.progress_caption}\n"
            f"{progress_bar(progress)}\n\n{status}"
        )
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=progress_text
        )

    try:
        update_progress(10, "⏳ Получаем список серверов...")

        from extensions.server_checks import initialize_servers

        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        results: list[dict[str, Any]] = []

        update_progress(15, f"⏳ Начинаем проверку {total_servers} серверов...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75) if total_servers else 90
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"🔍 Проверяем {server_info}...")

            try:
                resources: dict[str, Any] | None = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved

                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved

                    resources = get_windows_resources_improved(server["ip"])

                value = resources.get(spec.metric, 0) if resources else 0
                results.append(
                    {
                        "server": server,
                        spec.metric: value,
                        "success": resources is not None,
                    }
                )
            except Exception:
                results.append({"server": server, spec.metric: 0, "success": False})

        update_progress(95, "⏳ Формируем отчет...")

        results.sort(key=lambda x: x[spec.metric], reverse=True)

        windows_results = [r for r in results if r["server"]["type"] == "rdp"]
        linux_results = [r for r in results if r["server"]["type"] == "ssh"]

        message = f"{spec.progress_emoji} **{spec.report_title}**\n\n"
        message += _render_group(windows_results, "🪟 Windows серверы", spec)
        message += "\n" + _render_group(linux_results, "🐧 Linux серверы", spec)

        critical_count = sum(1 for r in results if r[spec.metric] > spec.critical_threshold)
        warning_count = sum(
            1 for r in results if spec.warning_threshold < r[spec.metric] <= spec.critical_threshold
        )
        successful = sum(1 for r in results if r["success"])

        message += "\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {len(results)}\n"
        message += f"• Успешно проверено: {successful}\n"
        message += f"• {spec.stat_label_critical}: {critical_count}\n"
        message += f"• {spec.stat_label_warning}: {warning_count}\n"
        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=spec.callback_id)],
        ]
        for text, callback_data in spec.other_buttons:
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        keyboard.append(
            [
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ]
        )

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке {spec.metric.upper()}: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=error_msg
        )


def perform_cpu_check(context: Any, chat_id: int, progress_message_id: int) -> None:
    """Обратно-совместимый wrapper, см. `perform_resource_check`."""
    perform_resource_check(context, chat_id, progress_message_id, CPU_SPEC)


def perform_ram_check(context: Any, chat_id: int, progress_message_id: int) -> None:
    """Обратно-совместимый wrapper, см. `perform_resource_check`."""
    perform_resource_check(context, chat_id, progress_message_id, RAM_SPEC)


def perform_disk_check(context: Any, chat_id: int, progress_message_id: int) -> None:
    """Обратно-совместимый wrapper, см. `perform_resource_check`."""
    perform_resource_check(context, chat_id, progress_message_id, DISK_SPEC)


__all__ = [
    "CPU_SPEC",
    "DISK_SPEC",
    "RAM_SPEC",
    "ResourceCheckSpec",
    "perform_cpu_check",
    "perform_disk_check",
    "perform_ram_check",
    "perform_resource_check",
]
