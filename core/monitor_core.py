"""
/core/monitor_core.py
Server Monitoring System v8.62.68
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core system
Система мониторинга серверов
Версия: 8.62.68
Автор: Александр Суханов (c)
Лицензия: MIT
Ядро системы
"""

# Новые импорты из модульной структуры
# Старые импорты для совместимости
import os
import threading
import time
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.db_settings import DATA_DIR, DEBUG_MODE
from core.config_manager import config_manager
from core.monitor import monitor
from core.monitor_state import STATE_FIELDS, state
from extensions.server_checks import check_server_availability
from extensions.zfs_pool_free_space import check_zfs_pool_free_space_alerts
from lib.alerts import (
    configure_alerts,
    get_silent_override,
    init_matrix_bot,
    init_telegram_bot,
    is_silent_time as alerts_is_silent_time,
    send_alert as base_send_alert,
    set_silent_override,
)
from lib.logging import debug_log
from lib.utils import format_duration, progress_bar, safe_import
from modules.availability import availability_checker
from modules.morning_report import morning_report
from modules.resources import resources_checker
from modules.targeted_checks import targeted_checks

# Runtime-состояние ядра вынесено в core/monitor_state.MonitoringState.
# Прежние module-level переменные (bot, state.server_status, state.monitoring_active,
# servers, ...) теперь поля state-объекта; обратная совместимость для
# внешних импортёров обеспечена через module-level __getattr__ ниже.

_alerts_configured = False


def __getattr__(name: str):
    """Backwards-compat: external `from core.monitor_core import X` для
    бывших module-level переменных проксируется к ``state``."""
    if name in STATE_FIELDS:
        return getattr(state, name)
    raise AttributeError(f"module 'core.monitor_core' has no attribute {name!r}")


def is_server_monitoring_enabled(ip: str) -> bool:
    """Проверяет, включен ли мониторинг для сервера."""
    try:
        return config_manager.get_server_enabled(ip)
    except Exception as e:
        debug_log(f"⚠️ Не удалось получить статус сервера {ip}: {e}")
        return True


def refresh_servers():
    """Обновляет список серверов и их статусы."""
    # global-стейт вынесен в core.monitor_state.state
    try:
        updated_servers = config_manager.get_all_servers(include_disabled=True)
        if not updated_servers:
            from extensions.server_checks import initialize_servers

            updated_servers = initialize_servers()
            for server in updated_servers:
                server.setdefault("enabled", True)

        state.servers = updated_servers
        current_ips = {server.get("ip") for server in state.servers if server.get("ip")}

        for ip in list(state.server_status.keys()):
            if ip not in current_ips:
                state.server_status.pop(ip, None)

        for server in state.servers:
            ip = server.get("ip")
            if not ip:
                continue
            if ip not in state.server_status:
                state.server_status[ip] = {
                    "last_up": datetime.now(),
                    "alert_sent": False,
                    "name": server.get("name", ip),
                    "type": server.get("type"),
                    "resources": None,
                    "last_alert": {},
                    "monitoring_enabled": server.get("enabled", True),
                }

    except Exception as e:
        debug_log(f"⚠️ Не удалось обновить список серверов: {e}")


def ensure_alerts_config():
    """Гарантирует применение настроек алертов из конфигурации."""
    global _alerts_configured
    if _alerts_configured:
        return

    config = get_config()
    configure_alerts(
        silent_start=getattr(config, "SILENT_START", None),
        silent_end=getattr(config, "SILENT_END", None),
    )
    _alerts_configured = True


def ensure_alert_bot() -> None:
    """Инициализирует Telegram-бот для lib.alerts при наличии глобального бота."""
    if state.bot is None:
        return
    try:
        config = get_config()
        init_telegram_bot(state.bot, config.CHAT_IDS)
        init_matrix_bot(config.MATRIX_HOMESERVER, config.MATRIX_ACCESS_TOKEN, config.MATRIX_ROOM_ID)
    except Exception as e:
        debug_log(f"Не удалось инициализировать бот алертов: {e}")


def send_alert(message, force=False, alert_type="info"):
    """Обертка над lib.alerts.send_alert с применением настроек и инициализацией бота."""
    ensure_alerts_config()
    ensure_alert_bot()
    return base_send_alert(message, force=force, alert_type=alert_type)


def is_silent_time():
    """Использует единый механизм тихого режима из lib.alerts."""
    ensure_alerts_config()
    return alerts_is_silent_time()


def lazy_import(module_name, attribute_name=None):
    """Ленивая загрузка модулей с поддержкой составных путей"""

    def import_func():
        # Для составных путей типа 'config.db_settings'
        if "." in module_name:
            parts = module_name.split(".")
            # Импортируем корневой модуль
            module = __import__(parts[0])
            # Проходим по вложенным модулям
            for part in parts[1:]:
                module = getattr(module, part)
        else:
            # Обычный импорт
            module = __import__(module_name, fromlist=[attribute_name] if attribute_name else [])

        return getattr(module, attribute_name) if attribute_name else module

    return import_func


# Ленивые импорты конфига
get_config = lazy_import("config.db_settings")
get_check_interval = lazy_import("config.db_settings", "CHECK_INTERVAL")
get_silent_times = lazy_import("config.db_settings", "SILENT_START")
get_data_collection_time = lazy_import("config.db_settings", "DATA_COLLECTION_TIME")
get_max_fail_time = lazy_import("config.db_settings", "MAX_FAIL_TIME")
get_resource_config = lazy_import("config.db_settings", "RESOURCE_CHECK_INTERVAL")


def get_web_interface_url(config):
    """Формирует URL веб-интерфейса из конфигурации."""
    monitor_ip = getattr(config, "MONITOR_SERVER_IP", "") or ""
    if not monitor_ip:
        web_host = getattr(config, "WEB_HOST", "")
        if web_host in ("0.0.0.0", "", None):
            monitor_ip = "localhost"
        else:
            monitor_ip = web_host
    return f"http://{monitor_ip}:{config.WEB_PORT}"


def perform_manual_check(context, chat_id, progress_message_id):
    """Выполняет проверку серверов с обновлением прогресса"""
    # global-стейт вынесен в core.monitor_state.state
    # Ленивая загрузка серверов
    if not state.servers:
        from extensions.server_checks import initialize_servers

        state.servers = initialize_servers()

    total_servers = len(state.servers)
    results = {"failed": [], "ok": []}

    for i, server in enumerate(state.servers):
        try:
            progress = (i + 1) / total_servers * 100
            progress_text = f"🔍 Проверяю серверы...\n{progress_bar(progress)}\n\n⏳ Проверяю {server['name']} ({server['ip']})..."

            context.bot.edit_message_text(
                chat_id=chat_id, message_id=progress_message_id, text=progress_text
            )

            # Используем универсальную проверку
            is_up = check_server_availability(server)

            if is_up:
                results["ok"].append(server)
                debug_log(f"✅ {server['name']} ({server['ip']}) - доступен")
            else:
                results["failed"].append(server)
                debug_log(f"❌ {server['name']} ({server['ip']}) - недоступен")

            time.sleep(1)

        except Exception as e:
            debug_log(f"💥 Критическая ошибка при проверке {server['ip']}: {e}")
            results["failed"].append(server)

    state.last_check_time = datetime.now()
    send_check_results(context, chat_id, progress_message_id, results)


def send_check_results(context, chat_id, progress_message_id, results):
    """Отправляет результаты проверки"""
    if not results["failed"]:
        message = "✅ Все серверы доступны!"
    else:
        message = "⚠️ Проблемные серверы:\n"

        # Группируем по типу для удобства чтения
        by_type = {}
        for server in results["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n{server_type.upper()} серверы:\n"
            for s in servers_list:
                message += f"- {s['name']} ({s['ip']})\n"

    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text=f"🔍 Проверка завершена!\n\n{message}\n\n⏰ Время проверки: {state.last_check_time.strftime('%H:%M:%S')}",
    )


# Все handler/командные функции перенесены в core/monitor_parts/telegram_handlers.py.
from core.monitor_parts.telegram_handlers import (  # noqa: E402
    auto_mode_handler,
    check_all_resources_handler,
    check_cpu_resources_handler,
    check_disk_resources_handler,
    check_linux_resources_handler,
    check_other_resources_handler,
    check_ram_resources_handler,
    check_resources_handler,
    check_windows_resources_handler,
    close_menu,
    close_resources_handler,
    control_command,
    control_panel_handler,
    daily_report_handler,
    debug_morning_report,
    diagnose_menu_handler,
    force_loud_handler,
    force_silent_handler,
    manual_check_handler,
    monitor_status,
    pause_monitoring_handler,
    perform_full_check,
    perform_linux_check,
    perform_other_check,
    perform_windows_check,
    refresh_resources_handler,
    resource_history_command,
    resource_page_handler,
    resume_monitoring_handler,
    send_morning_report_handler,
    silent_command,
    silent_status_handler,
    toggle_monitoring_handler,
    toggle_silent_mode_handler,
)


def get_current_server_status():
    """Выполняет быструю проверку статуса серверов"""
    # global-стейт вынесен в core.monitor_state.state
    # Переинициализируем серверы при каждом запросе
    from extensions.server_checks import initialize_servers

    state.servers = initialize_servers()
    debug_log(f"🔄 Обновлен список серверов: {len(state.servers)} серверов")

    results = {"failed": [], "ok": []}

    for server in state.servers:
        try:
            is_up = check_server_availability(server)

            if is_up:
                results["ok"].append(server)
            else:
                results["failed"].append(server)

            debug_log(f"🔍 {server['name']} ({server['ip']}) - {'🟢' if is_up else '🔴'}")

        except Exception as e:
            debug_log(f"❌ Ошибка проверки {server['name']}: {e}")
            results["failed"].append(server)

    debug_log(
        f"📊 Итог проверки: {len(results['ok'])} доступно, {len(results['failed'])} недоступно"
    )
    return results


def _resource_monitor_enabled() -> bool:
    """Проверяет, включен ли мониторинг ресурсов"""
    try:
        from extensions.extension_manager import extension_manager

        return extension_manager.is_extension_enabled("resource_monitor")
    except ImportError:
        return True


# perform_cpu_check / perform_ram_check / perform_disk_check вынесены в
# core/monitor_parts/resource_checks.py. Реэкспорт через __getattr__ фасада в
# конце файла, для прямых вызовов внутри monitor_core — алиасы:
# start_monitoring вынесен в core/monitor_parts/lifecycle.py.
# handle_server_up / handle_server_down вынесены в core/monitor_parts/availability.py.
# check_resources_automatically / check_resource_alerts / send_resource_alerts
# вынесены в core/monitor_parts/alerts.py.
from core.monitor_parts.alerts import (
    check_resource_alerts,
    check_resources_automatically,
    send_resource_alerts,
)
from core.monitor_parts.availability import handle_server_down, handle_server_up
from core.monitor_parts.lifecycle import start_monitoring

# send_morning_report / get_backup_summary_for_report / debug_backup_data
# вынесены в core/monitor_parts/report.py.
from core.monitor_parts.report import (
    debug_backup_data,
    get_backup_summary_for_report,
    send_morning_report,
)
from core.monitor_parts.resource_checks import (
    perform_cpu_check,
    perform_disk_check,
    perform_ram_check,
)


def debug_proxmox_config():
    """Временная функция для диагностики конфигурации Proxmox"""
    try:
        from config.db_settings import PROXMOX_HOSTS

        debug_log("=== ДИАГНОСТИКА KONФИГУРАЦИИ PROXMOX ===")
        enabled_hosts = [
            host
            for host, value in PROXMOX_HOSTS.items()
            if not isinstance(value, dict) or value.get("enabled", True)
        ]
        debug_log(f"Всего хостов в PROXMOX_HOSTS: {len(enabled_hosts)}")
        for i, host in enumerate(enabled_hosts, 1):
            debug_log(f"{i}. {host}")
        debug_log("=======================================")
    except Exception as e:
        debug_log(f"❌ Ошибка диагностики конфигурации: {e}")
