"""
/core/monitor.py
Server Monitoring System v8.62.47
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core monitoring module
Система мониторинга серверов
Версия: 8.62.47
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль мониторинга
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List

from config import (
    CHECK_INTERVAL,
    DATA_COLLECTION_TIME,
    MAX_FAIL_TIME,
    RESOURCE_CHECK_INTERVAL,
    SILENT_END,
    SILENT_START,
)
from core.config_manager import config_manager
from lib.alerts import is_silent_time as alerts_is_silent_time, send_alert
from lib.logging import debug_log, info_log
from modules.morning_report import morning_report
from modules.resources import resources_checker


class Monitor:
    """Основной класс мониторинга"""

    def __init__(self):
        """Инициализация мониторинга"""
        self.monitoring_active = True
        self.silent_override = None
        self.server_status = {}
        self.servers = []
        self.bot = None

        self.last_check_time = datetime.now()
        self.last_resource_check = datetime.now()
        self.last_report_date = None
        self.last_collection_schedule_time = []
        self.sent_collection_slots = set()

    def is_silent_time(self) -> bool:
        """
        Проверяет, находится ли текущее время в 'тихом' периоде

        Returns:
            bool: True если тихий режим
        """
        # Если есть принудительное переопределение
        if self.silent_override is not None:
            return self.silent_override

        return alerts_is_silent_time()

    def _get_check_interval_seconds(self) -> int:
        """Возвращает актуальный интервал проверки из БД настроек."""
        try:
            value = config_manager.get_setting("CHECK_INTERVAL", CHECK_INTERVAL, use_cache=False)
            interval = int(value)
            return max(1, interval)
        except Exception:
            return max(1, int(CHECK_INTERVAL))

    def _get_max_fail_time_seconds(self) -> int:
        """Возвращает актуальный порог простоя до алерта из БД настроек."""
        try:
            value = config_manager.get_setting("MAX_FAIL_TIME", MAX_FAIL_TIME, use_cache=False)
            timeout = int(value)
            return max(1, timeout)
        except Exception:
            return max(1, int(MAX_FAIL_TIME))

    def load_servers(self) -> List[Dict]:
        """
        Загружает список серверов для мониторинга

        Returns:
            List[Dict]: Список серверов
        """
        try:
            servers = config_manager.get_all_servers(include_disabled=True)
            if not servers:
                from extensions.server_checks import initialize_servers

                servers = initialize_servers()
                for server in servers:
                    server.setdefault("enabled", True)

            # Исключаем сервер мониторинга
            monitor_server_ip = "192.168.20.2"
            servers = [s for s in servers if s.get("ip") != monitor_server_ip]

            debug_log(f"✅ Загружено {len(servers)} серверов для мониторинга")
            return servers

        except Exception as e:
            debug_log(f"❌ Ошибка загрузки серверов: {e}")
            return []

    def refresh_servers(self) -> None:
        """Обновляет список серверов и статусы."""
        servers = self.load_servers()
        if not servers:
            return

        self.servers = servers
        current_ips = {server.get("ip") for server in servers if server.get("ip")}
        stale_ips = [ip for ip in self.server_status if ip not in current_ips]
        for ip in stale_ips:
            self.server_status.pop(ip, None)

        self.initialize_server_status()

    def is_server_enabled(self, ip: str) -> bool:
        """Проверяет, включен ли мониторинг для сервера."""
        try:
            return config_manager.get_server_enabled(ip)
        except Exception as e:
            debug_log(f"⚠️ Не удалось получить статус сервера {ip}: {e}")
            return True

    def initialize_server_status(self) -> None:
        """Инициализирует статусы серверов"""
        for server in self.servers:
            ip = server.get("ip")
            if ip and ip not in self.server_status:
                self.server_status[ip] = {
                    "last_up": datetime.now(),
                    "alert_sent": False,
                    "name": server.get("name", ip),
                    "type": server.get("type", "unknown"),
                    "resources": None,
                    "last_alert": {},
                    "downtime_start": None,
                    "monitoring_enabled": server.get("enabled", True),
                }

        debug_log(f"✅ Инициализированы статусы для {len(self.server_status)} серверов")

    def check_server_availability(self, server: Dict) -> bool:
        """
        Проверяет доступность сервера

        Args:
            server: Информация о сервере

        Returns:
            bool: True если сервер доступен
        """
        try:
            from extensions.server_checks import check_server_availability

            return check_server_availability(server)
        except Exception as e:
            debug_log(f"❌ Ошибка проверки доступности {server.get('name')}: {e}")
            return False

    def handle_server_up(self, ip: str, status: Dict, current_time: datetime) -> None:
        """
        Обрабатывает доступный сервер

        Args:
            ip: IP сервера
            status: Текущий статус
            current_time: Текущее время
        """
        if status.get("alert_sent"):
            downtime_start = status.get("downtime_start")
            downtime = 0
            if downtime_start:
                downtime = (current_time - downtime_start).total_seconds()

            message = f"✅ {status.get('name')} ({ip}) доступен"
            if downtime > 0:
                message += f" (простой: {int(downtime // 60)} мин {int(downtime % 60)} сек)"

            send_alert(message)

        # Обновляем статус
        self.server_status[ip] = {
            "last_up": current_time,
            "alert_sent": False,
            "name": status.get("name"),
            "type": status.get("type"),
            "resources": self.server_status.get(ip, {}).get("resources"),
            "last_alert": self.server_status.get(ip, {}).get("last_alert", {}),
            "downtime_start": None,
        }

    def handle_server_down(self, ip: str, status: Dict, current_time: datetime) -> bool:
        """
        Обрабатывает недоступный сервер
        """
        downtime_start = status.get("downtime_start")
        if downtime_start is None:
            downtime_start = current_time
            self.server_status[ip]["downtime_start"] = downtime_start

        downtime = (current_time - downtime_start).total_seconds()

        # Проверяем нужно ли отправлять алерт
        max_fail_time = self._get_max_fail_time_seconds()
        if downtime >= max_fail_time and not status.get("alert_sent"):
            message = f"🚨 {status.get('name')} ({ip}) не отвечает"
            message += f" ({int(downtime // 60)} мин {int(downtime % 60)} сек)"

            send_alert(message, alert_type="critical")
            self.server_status[ip]["alert_sent"] = True
            return True

        return False

    def check_resources_automatically(self) -> None:
        """Автоматическая проверка ресурсов серверов"""
        try:
            from extensions.extension_manager import extension_manager

            if not extension_manager.is_extension_enabled("resource_monitor"):
                debug_log("⏸️ Проверка ресурсов пропущена (расширение отключено)")
                return
        except ImportError:
            pass

        if not self.monitoring_active or self.is_silent_time():
            debug_log("⏸️ Проверка ресурсов пропущена (мониторинг неактивен или тихий режим)")
            return

        current_time = datetime.now()

        # Проверяем интервал
        if (current_time - self.last_resource_check).total_seconds() < RESOURCE_CHECK_INTERVAL:
            return

        debug_log("🔍 Автоматическая проверка ресурсов серверов...")

        # Проверяем все серверы
        alerts_found = []

        for server in self.servers:
            try:
                ip = server.get("ip")
                server_name = server.get("name", ip)
                server_type = server.get("type")

                if not self.is_server_enabled(ip):
                    if ip in self.server_status:
                        self.server_status[ip]["last_up"] = current_time
                        self.server_status[ip]["alert_sent"] = False
                        self.server_status[ip]["last_alert"] = {}
                    continue

                # Получаем текущие ресурсы
                success, resources = resources_checker.check_server_resources(server)

                if success and resources:
                    # Проверяем алерты
                    server_alerts = resources_checker.check_resource_alerts(ip, resources)

                    if server_alerts:
                        alerts_found.extend(server_alerts)
                        debug_log(f"⚠️ Найдены проблемы для {server_name}: {server_alerts}")

                    # Сохраняем ресурсы в статус
                    if ip in self.server_status:
                        self.server_status[ip]["resources"] = resources

            except Exception as e:
                debug_log(f"❌ Ошибка при проверке ресурсов {server.get('name')}: {e}")
                continue

        # Отправляем алерты если есть
        if alerts_found:
            self.send_resource_alerts(alerts_found)

        self.last_resource_check = current_time
        debug_log(
            f"✅ Автоматическая проверка ресурсов завершена. Найдено проблем: {len(alerts_found)}"
        )

    def send_resource_alerts(self, alerts: List[str]) -> None:
        """
        Отправляет алерты по ресурсам

        Args:
            alerts: Список сообщений для алертов
        """
        if not alerts:
            return

        message = "🚨 *Проблемы с ресурсами серверов*\n\n"

        # Группируем алерты по типам ресурсов
        disk_alerts = [a for a in alerts if "💾" in a]
        cpu_alerts = [a for a in alerts if "💻" in a]
        ram_alerts = [a for a in alerts if "🧠" in a]

        # Дисковое пространство
        if disk_alerts:
            message += "💾 **Дисковое пространство:**\n"
            for alert in disk_alerts:
                parts = alert.split("на ")
                if len(parts) > 1:
                    server_info = parts[1]
                    message += f"• {server_info}\n"
            message += "\n"

        # Процессор
        if cpu_alerts:
            message += "💻 **Процессор (CPU):**\n"
            for alert in cpu_alerts:
                parts = alert.split("на ")
                if len(parts) > 1:
                    server_info = parts[1]
                    message += f"• {server_info}\n"
            message += "\n"

        # Память
        if ram_alerts:
            message += "🧠 **Память (RAM):**\n"
            for alert in ram_alerts:
                parts = alert.split("на ")
                if len(parts) > 1:
                    server_info = parts[1]
                    message += f"• {server_info}\n"
            message += "\n"

        message += f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}"

        send_alert(message)
        debug_log(f"✅ Отправлены алерты по ресурсам: {len(alerts)} проблем")

    def check_morning_report(self) -> None:
        """Проверяет и отправляет утренний отчет если нужно"""
        current_time = datetime.now()

        # Проверяем актуальное время сбора данных из настроек
        collection_times = morning_report._get_collection_times()
        today = current_time.date()
        normalized_slots = [slot.strftime("%H:%M") for slot in collection_times]

        configured_times_raw = None
        configured_source = "config.settings.DATA_COLLECTION_TIME"
        try:
            from core.config_manager import config_manager as settings_manager

            configured_times_raw = settings_manager.get_setting(
                "DATA_COLLECTION_TIMES", None, use_cache=False
            )
            if configured_times_raw not in (None, ""):
                configured_source = "БД settings: DATA_COLLECTION_TIMES"
            else:
                configured_times_raw = settings_manager.get_setting(
                    "DATA_COLLECTION_TIME", None, use_cache=False
                )
                if configured_times_raw not in (None, ""):
                    configured_source = "БД settings: DATA_COLLECTION_TIME"
        except Exception:
            pass

        if self.last_collection_schedule_time != normalized_slots:
            debug_log(
                "🕒 Обнаружено изменение расписания утреннего отчета: "
                f"{', '.join(self.last_collection_schedule_time) or 'пусто'} -> {', '.join(normalized_slots)}"
            )
            self.sent_collection_slots = {
                slot
                for slot in self.sent_collection_slots
                if not slot.startswith(f"{today.isoformat()} ")
            }
            self.last_collection_schedule_time = normalized_slots

        debug_log(
            "🕒 Проверка автозапуска утреннего отчета: "
            f"текущее={current_time.strftime('%H:%M:%S')} "
            f"план={', '.join(normalized_slots)} "
            f"последний_отчет={self.last_report_date}"
        )
        info_log(
            "[MORNING_REPORT_SCHEDULE] heartbeat "
            f"now={current_time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"plan={','.join(normalized_slots)} "
            f"last_report_date={self.last_report_date}"
        )
        for collection_time in collection_times:
            scheduled_collection_dt = datetime.combine(today, collection_time)
            check_interval_seconds = self._get_check_interval_seconds()
            trigger_window_start = scheduled_collection_dt
            trigger_window_end = scheduled_collection_dt + timedelta(
                seconds=check_interval_seconds - 1
            )
            slot_key = f"{today.isoformat()} {collection_time.strftime('%H:%M')}"
            if not (trigger_window_start <= current_time <= trigger_window_end):
                continue
            if slot_key in self.sent_collection_slots:
                continue
            debug_log(
                f"🚀 Триггер автозапуска утреннего отчета: "
                f"now={current_time.strftime('%Y-%m-%d %H:%M:%S')} "
                f"plan={collection_time.strftime('%H:%M')}"
            )
            debug_log(
                "🗓️ Автозапуск утреннего отчета выполнен по расписанию из меню: "
                "Главное меню → Настройки → Временные настройки → Время сбора данных "
                f"({collection_time.strftime('%H:%M')})"
            )
            info_log(
                "[MORNING_REPORT_SCHEDULE] trigger_from_menu "
                "path='Главное меню → Настройки → Временные настройки → Время сбора данных' "
                f"collection_time={collection_time.strftime('%H:%M')}"
            )
            info_log(
                "[MORNING_REPORT_COLLECTION] start "
                f"now={current_time.strftime('%Y-%m-%d %H:%M:%S')} "
                f"trigger_time={collection_time.strftime('%H:%M')} "
                f"resolved_schedule={','.join(normalized_slots)} "
                f"source='{configured_source}' "
                f"raw='{configured_times_raw}'"
            )
            debug_log(
                f"[{current_time}] 🔍 Собираем данные для утреннего отчета "
                f"(план: {scheduled_collection_dt.strftime('%H:%M')})..."
            )

            # Собираем данные утреннего отчета
            morning_report.collect_morning_data(manual_call=False)

            status = morning_report.morning_data.get("status", {})
            debug_log(f"✅ Данные собраны: {len(status.get('ok', []))} доступно")

            # Отправляем отчет
            debug_log(f"[{current_time}] 📊 Отправка утреннего отчета...")
            sent_ok = morning_report.send_report(manual_call=False, collect_before_send=False)
            if not sent_ok:
                info_log(
                    "[MORNING_REPORT_SCHEDULE] send_failed "
                    f"now={current_time.strftime('%Y-%m-%d %H:%M:%S')} "
                    f"plan={collection_time.strftime('%H:%M')}"
                )
                return

            self.last_report_date = today
            self.sent_collection_slots.add(slot_key)
            debug_log("✅ Утренний отчет отправлен")

            # Короткая пауза, чтобы не запускать повторно в ту же секунду
            time.sleep(2)
            return

    def _send_startup_notification(self) -> None:
        """Формирует и отправляет единое стартовое уведомление.

        Объединяет сведения о версии/хосте и параметры мониторинга в
        одно сообщение, чтобы при перезапуске сервиса в Telegram и
        Matrix приходило одно уведомление вместо двух.
        """
        from lib.alerts import is_startup_muted

        if is_startup_muted():
            debug_log("🔇 Тихий старт: стартовое сообщение подавлено (--silent-start)")
            return

        lines = ["🟢 *Мониторинг серверов запущен*", ""]

        try:
            from config.settings import APP_VERSION

            lines.append(f"🔖 *Версия:* {APP_VERSION}")
        except Exception:
            pass

        try:
            from config.settings import ANDROID_LATEST_VERSION

            lines.append(f"📱 *Android-клиент:* {ANDROID_LATEST_VERSION}")
        except Exception:
            pass

        try:
            import socket

            lines.append(f"🖥 *Хост:* {socket.gethostname()}")
        except Exception:
            pass

        try:
            import platform

            lines.append(f"🐍 *Python:* {platform.python_version()}")
        except Exception:
            pass

        lines.append(f"🕒 *Время запуска:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            report_slots = morning_report._get_collection_times()
            report_time = ", ".join(
                slot.strftime("%H:%M") for slot in report_slots
            ) or DATA_COLLECTION_TIME.strftime("%H:%M")
        except Exception:
            report_time = DATA_COLLECTION_TIME.strftime("%H:%M")

        lines.append("")
        lines.append(f"• Серверов в мониторинге: {len(self.servers)}")
        lines.append(f"• Проверка доступности: каждые {CHECK_INTERVAL} сек")
        lines.append(f"• Утренний отчет: {report_time}")

        try:
            from extensions.extension_manager import extension_manager

            resources_enabled = extension_manager.is_extension_enabled("resource_monitor")
        except ImportError:
            resources_enabled = True

        if resources_enabled:
            lines.append(f"• Проверка ресурсов: каждые {RESOURCE_CHECK_INTERVAL // 60} минут")
        else:
            lines.append("• Проверка ресурсов: отключена")

        try:
            from extensions.extension_manager import extension_manager

            if extension_manager.is_extension_enabled("web_interface"):
                from config import settings as _settings
                from core.monitor_core import get_web_interface_url

                lines.append("")
                lines.append(f"🌐 *Веб-интерфейс:* {get_web_interface_url(_settings)}")
                lines.append("_доступен только в локальной сети_")
            else:
                lines.append("")
                lines.append("🌐 *Веб-интерфейс:* 🔴 отключен")
        except ImportError:
            lines.append("")
            lines.append("🌐 *Веб-интерфейс:* 🔴 модуль не загружен")

        send_alert("\n".join(lines), force=True)

    def start(self) -> None:
        """Запускает основной цикл мониторинга"""
        # Загружаем серверы
        self.servers = self.load_servers()

        # Единое стартовое сообщение (версия, сведения о хосте и
        # параметры мониторинга). Отправляется один раз при запуске
        # сервиса, чтобы в Telegram/Matrix не приходило два уведомления.
        self._send_startup_notification()

        if not self.servers:
            debug_log("❌ Нет серверов для мониторинга")
            return

        # Инициализируем статусы
        self.initialize_server_status()

        debug_log(f"✅ Мониторинг запущен для {len(self.servers)} серверов")

        # Основной цикл мониторинга
        while True:
            current_time = datetime.now()

            # Проверяем утренний отчет
            self.check_morning_report()

            # Автоматическая проверка ресурсов
            self.check_resources_automatically()

            # Основная проверка доступности
            if self.monitoring_active:
                self.last_check_time = current_time

                self.refresh_servers()

                for server in self.servers:
                    try:
                        ip = server.get("ip")
                        if ip not in self.server_status:
                            continue

                        status = self.server_status[ip]

                        # Исключаем сервер мониторинга
                        if ip == "192.168.20.2":
                            self.server_status[ip]["last_up"] = current_time
                            continue

                        monitoring_enabled = self.is_server_enabled(ip)
                        if not monitoring_enabled:
                            self.server_status[ip]["monitoring_enabled"] = False
                            continue

                        if not self.server_status[ip].get("monitoring_enabled", True):
                            self.server_status[ip]["monitoring_enabled"] = True
                            self.server_status[ip]["alert_sent"] = False
                            self.server_status[ip]["last_alert"] = {}

                        # Проверка доступности
                        is_up = self.check_server_availability(server)

                        if is_up:
                            self.handle_server_up(ip, status, current_time)
                        else:
                            self.handle_server_down(ip, status, current_time)

                    except Exception as e:
                        debug_log(f"❌ Ошибка мониторинга {server.get('name')}: {e}")

            # Ожидание перед следующей проверкой
            time.sleep(self._get_check_interval_seconds())

    def stop(self) -> None:
        """Останавливает мониторинг"""
        self.monitoring_active = False
        debug_log("⏸️ Мониторинг приостановлен")

    def resume(self) -> None:
        """Возобновляет мониторинг"""
        self.monitoring_active = True
        debug_log("▶️ Мониторинг возобновлен")

    def get_status(self) -> Dict:
        """
        Получает текущий статус мониторинга

        Returns:
            Dict: Статус мониторинга
        """
        return {
            "monitoring_active": self.monitoring_active,
            "silent_mode": self.is_silent_time(),
            "silent_override": self.silent_override,
            "servers_count": len(self.servers),
            "server_status": self.server_status,
            "last_check_time": self.last_check_time,
            "last_resource_check": self.last_resource_check,
        }


# Глобальный экземпляр для импорта
monitor = Monitor()
