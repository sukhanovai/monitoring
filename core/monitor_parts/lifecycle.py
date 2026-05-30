"""
/core/monitor_parts/lifecycle.py
Server Monitoring System v8.62.76
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main monitoring loop entry-point extracted from core/monitor_core.py
(PR5 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.76
Автор: Александр Суханов (c)
Лицензия: MIT
Жизненный цикл монитора: однократная инициализация бота/state, затем
вечный цикл с ресурсной проверкой по интервалу, сбором утреннего
отчёта по расписанию и опросом доступности всех серверов.
"""

from __future__ import annotations

import time
from datetime import datetime

from core.monitor_state import state
from lib.logging import debug_log, info_log


def start_monitoring() -> None:
    """Запускает основной цикл мониторинга.

    Один и тот же поток инициализирует Telegram-бота, исключает
    monitor_server_ip из проверок, заполняет начальный
    `state.server_status` и затем бесконечно крутит:
    проверку ресурсов (через `check_resources_automatically`),
    отправку утреннего отчёта в окно из `morning_report._get_collection_times()`,
    проход по `state.servers` с `check_server_availability` и
    плановую проверку свободного места ZFS пулов.
    """
    from core.monitor_core import (
        ensure_alerts_config,
        get_config,
        get_current_server_status,
        get_web_interface_url,
        is_server_monitoring_enabled,
        is_silent_time,
        refresh_servers,
        send_alert,
    )
    from core.monitor_parts.alerts import check_resources_automatically
    from core.monitor_parts.availability import handle_server_down, handle_server_up
    from core.monitor_parts.report import send_morning_report
    from extensions.server_checks import (
        check_server_availability,
        initialize_servers,
    )
    from extensions.tls_cert_monitor import check_tls_cert_alerts
    from extensions.zfs_pool_free_space import check_zfs_pool_free_space_alerts
    from lib.alerts import init_telegram_bot, is_startup_muted
    from modules.morning_report import morning_report

    state.servers = initialize_servers()

    config = get_config()
    monitor_server_ip = getattr(config, "MONITOR_SERVER_IP", "")
    if monitor_server_ip:
        state.servers = [s for s in state.servers if s["ip"] != monitor_server_ip]
        debug_log(
            "✅ Сервер мониторинга "
            f"{monitor_server_ip} принудительно исключен из списка. "
            f"Осталось {len(state.servers)} серверов"
        )
    else:
        debug_log("⚠️ Сервер мониторинга не исключен: MONITOR_SERVER_IP не задан")

    from telegram import Bot

    state.bot = Bot(token=config.TELEGRAM_TOKEN)
    ensure_alerts_config()
    init_telegram_bot(state.bot, config.CHAT_IDS)

    for server in state.servers:
        state.server_status[server["ip"]] = {
            "last_up": datetime.now(),
            "alert_sent": False,
            "name": server["name"],
            "type": server["type"],
            "resources": None,
            "last_alert": {},
            "monitoring_enabled": server.get("enabled", True),
        }

    debug_log(f"✅ Мониторинг запущен для {len(state.servers)} серверов")

    start_message = "🟢 *Мониторинг серверов запущен*\n\n"
    if getattr(config, "APP_VERSION", None):
        start_message += f"🔖 *Версия:* {config.APP_VERSION}\n"
    try:
        report_slots = morning_report._get_collection_times()
        report_time = ", ".join(
            slot.strftime("%H:%M") for slot in report_slots
        ) or config.DATA_COLLECTION_TIME.strftime("%H:%M")
    except Exception:
        report_time = config.DATA_COLLECTION_TIME.strftime("%H:%M")
    start_message += (
        f"• Серверов в мониторинге: {len(state.servers)}\n"
        f"• Проверка ресурсов: каждые {config.RESOURCE_CHECK_INTERVAL // 60} минут\n"
        f"• Утренний отчет: {report_time}\n\n"
    )

    from extensions.extension_manager import extension_manager

    if extension_manager.is_extension_enabled("web_interface"):
        start_message += f"🌐 *Веб-интерфейс:* {get_web_interface_url(config)}\n"
        start_message += "_*доступен только в локальной сети_\n"
    else:
        start_message += "🌐 *Веб-интерфейс:* 🔴 отключен\n"

    if is_startup_muted():
        debug_log("🔇 Тихий старт: стартовое сообщение мониторинга подавлено (--silent-start)")
    else:
        send_alert(start_message)

    state.last_resource_check = datetime.now()

    if not state.morning_data:
        state.morning_data = {}

    while True:
        current_time = datetime.now()
        config = get_config()

        if (
            current_time - state.last_resource_check
        ).total_seconds() >= config.RESOURCE_CHECK_INTERVAL:
            if state.monitoring_active and not is_silent_time():
                debug_log("🔄 Автоматическая проверка ресурсов серверов...")
                check_resources_automatically()
                state.last_resource_check = current_time
            else:
                debug_log("⏸️ Проверка ресурсов пропущена (тихий режим или мониторинг неактивен)")

        collection_times = morning_report._get_collection_times()
        today = current_time.date()
        normalized_slots = [slot.strftime("%H:%M") for slot in collection_times]

        if state.last_collection_schedule_time != normalized_slots:
            debug_log(
                "🕒 Обнаружено изменение расписания утреннего отчета: "
                f"{', '.join(state.last_collection_schedule_time or []) or 'пусто'}"
                f" -> {', '.join(normalized_slots)}"
            )
            state.sent_collection_slots = {
                slot
                for slot in state.sent_collection_slots
                if not slot.startswith(f"{today.isoformat()} ")
            }
            state.last_collection_schedule_time = normalized_slots

        debug_log(
            f"🕒 План отчета: now={current_time.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"scheduled={','.join(normalized_slots)} | "
            f"state.last_report_date={state.last_report_date}"
        )

        for collection_time in collection_times:
            scheduled_collection_dt = datetime.combine(today, collection_time)
            slot_key = f"{today.isoformat()} {collection_time.strftime('%H:%M')}"
            if current_time < scheduled_collection_dt or slot_key in state.sent_collection_slots:
                continue

            info_log(
                "[MORNING_REPORT_COLLECTION] start "
                f"now={current_time.strftime('%Y-%m-%d %H:%M:%S')} "
                f"trigger_time={collection_time.strftime('%H:%M')} "
                f"resolved_schedule={','.join(normalized_slots)}"
            )
            debug_log(
                f"[{current_time}] 🔍 Собираем данные для утреннего отчета "
                f"(план: {scheduled_collection_dt.strftime('%H:%M')})..."
            )

            morning_status = get_current_server_status()
            state.morning_data = {
                "status": morning_status,
                "collection_time": current_time,
                "manual_call": False,
            }

            debug_log(
                f"✅ Данные собраны: {len(morning_status['ok'])} доступно, "
                f"{len(morning_status['failed'])} недоступно"
            )

            debug_log(f"[{current_time}] 📊 Отправка утреннего отчета...")
            sent_ok = send_morning_report(manual_call=False)
            if sent_ok:
                state.last_report_date = today
                state.sent_collection_slots.add(slot_key)
                debug_log("✅ Утренний отчет отправлен")
            else:
                debug_log("❌ Утренний отчет НЕ отправлен, повторим на следующем цикле")

            time.sleep(2)
            break

        if state.monitoring_active:
            state.last_check_time = current_time

            refresh_servers()

            for server in state.servers:
                try:
                    ip = server["ip"]
                    status = state.server_status[ip]

                    if ip == monitor_server_ip:
                        state.server_status[ip]["last_up"] = current_time
                        continue

                    monitoring_enabled = is_server_monitoring_enabled(ip)
                    if not monitoring_enabled:
                        state.server_status[ip]["monitoring_enabled"] = False
                        continue

                    if not status.get("monitoring_enabled", True):
                        state.server_status[ip]["monitoring_enabled"] = True
                        state.server_status[ip]["alert_sent"] = False
                        state.server_status[ip]["last_alert"] = {}

                    is_up = check_server_availability(server)

                    if is_up:
                        handle_server_up(ip, status, current_time)
                    else:
                        handle_server_down(ip, status, current_time)

                except Exception as e:
                    debug_log(f"❌ Ошибка мониторинга {server['name']}: {e}")

            try:
                check_zfs_pool_free_space_alerts(
                    send_alert_func=send_alert,
                    repeat_interval_seconds=max(
                        int(config.RESOURCE_ALERT_INTERVAL), int(config.CHECK_INTERVAL)
                    ),
                )
            except Exception as exc:
                debug_log(f"⚠️ Ошибка плановой проверки свободного места ZFS пулов: {exc}")

            try:
                check_tls_cert_alerts(
                    send_alert_func=send_alert,
                    repeat_interval_seconds=max(
                        int(config.RESOURCE_ALERT_INTERVAL), int(config.CHECK_INTERVAL)
                    ),
                )
            except Exception as exc:
                debug_log(f"⚠️ Ошибка плановой проверки TLS-сертификатов: {exc}")

        time.sleep(config.CHECK_INTERVAL)


__all__ = ["start_monitoring"]
