"""
Server Monitoring System v4.4.8 - Ядро мониторинга
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Основной цикл мониторинга

"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from app.core import checker
from app.utils.common import debug_log
from app.config import settings


class MonitoringCore:
    """Основной класс мониторинга серверов"""
    
    def __init__(self):
        self.bot = None
        self.server_status = {}
        self.morning_data = {}
        self.monitoring_active = True
        self.last_check_time = datetime.now()
        self.servers = []
        self.silent_override = None
        self.resource_history = {}
        self.last_resource_check = datetime.now()
        self.resource_alerts_sent = {}
        self.last_report_date = None
        
    def is_silent_time(self) -> bool:
        """Проверяет, находится ли текущее время в 'тихом' периоде с учетом переопределения"""
        # Если есть принудительное переопределение
        if self.silent_override is not None:
            return self.silent_override  # True - тихий, False - громкий

        # Стандартная проверка по времени
        current_hour = datetime.now().hour
        if settings.SILENT_START > settings.SILENT_END:  # Если период переходит через полночь
            return current_hour >= settings.SILENT_START or current_hour < settings.SILENT_END
        return settings.SILENT_START <= current_hour < settings.SILENT_END
    
    def send_alert(self, message: str, force: bool = False) -> None:
        """Отправляет сообщение без блокировок"""
        if self.bot is None:
            from telegram import Bot
            self.bot = Bot(token=settings.TELEGRAM_TOKEN)

        # Логируем для диагностики
        debug_log(f"📨 Отправка: '{message[:50]}...'")

        try:
            if force or not self.is_silent_time():
                for chat_id in settings.CHAT_IDS:
                    self.bot.send_message(chat_id=chat_id, text=message)
                debug_log("    ✅ Сообщение отправлено")
            else:
                debug_log("    ⏸️ Сообщение не отправлено (тихий режим)")
        except Exception as e:
            debug_log(f"    ❌ Ошибка отправки: {e}")
    
    def check_server_availability(self, server: Dict[str, Any]) -> bool:
        """Универсальная проверка доступности сервера"""
        try:
            # Определяем тип проверки в зависимости от сервера
            if self._is_proxmox_server(server):
                return checker.check_ssh_universal(server["ip"])
            elif server["type"] == "rdp":
                return checker.check_port(server["ip"], 3389)
            elif server["type"] == "ping":
                return checker.check_ping(server["ip"])
            else:
                return checker.check_ssh_universal(server["ip"])
        except Exception as e:
            debug_log(f"❌ Ошибка проверки {server['name']}: {e}")
            return False
    
    def _is_proxmox_server(self, server: Dict[str, Any]) -> bool:
        """Проверяет, является ли сервер Proxmox"""
        ip = server["ip"]
        return (ip.startswith("192.168.30.") or
               ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])
    
    def get_current_server_status(self) -> Dict[str, List]:
        """Выполняет быструю проверку статуса серверов"""
        results = {"failed": [], "ok": []}

        # Переинициализируем серверы если список пустой
        if not self.servers:
            from extensions.server_checks import initialize_servers
            self.servers = initialize_servers()
            debug_log(f"🔄 Переинициализирован список серверов: {len(self.servers)} серверов")
        
        for server in self.servers:
            try:
                is_up = self.check_server_availability(server)

                if is_up:
                    results["ok"].append(server)
                else:
                    results["failed"].append(server)
                    
                debug_log(f"🔍 {server['name']} ({server['ip']}) - {'🟢' if is_up else '🔴'}")
                    
            except Exception as e:
                debug_log(f"❌ Ошибка проверки {server['name']}: {e}")
                results["failed"].append(server)

        debug_log(f"📊 Итог проверки: {len(results['ok'])} доступно, {len(results['failed'])} недоступно")
        return results
    
    def start(self) -> None:
        """Запускает основной цикл мониторинга"""
        self._initialize_monitoring()
        
        while True:
            current_time = datetime.now()
            current_time_time = current_time.time()

            # Автоматическая проверка ресурсов
            if (current_time - self.last_resource_check).total_seconds() >= settings.RESOURCE_CHECK_INTERVAL:
                if self.monitoring_active and not self.is_silent_time():
                    debug_log("🔄 Автоматическая проверка ресурсов серверов...")
                    self._check_resources_automatically()
                    self.last_resource_check = current_time
                else:
                    debug_log("⏸️ Проверка ресурсов пропущена (тихий режим или мониторинг неактивен)")

            # Сбор и отправка утреннего отчета
            if (current_time_time.hour == settings.DATA_COLLECTION_TIME.hour and
                current_time_time.minute == settings.DATA_COLLECTION_TIME.minute):

                # Проверяем, что сегодня еще не отправляли отчет
                today = current_time.date()
                if self.last_report_date != today:
                    debug_log(f"[{current_time}] 🔍 Собираем данные для утреннего отчета...")
                    
                    # Собираем текущий статус серверов
                    morning_status = self.get_current_server_status()
                    self.morning_data = {
                        "status": morning_status,
                        "collection_time": current_time,
                        "manual_call": False  # Автоматический вызов
                    }

                    debug_log(f"✅ Данные собраны: {len(morning_status['ok'])} доступно, {len(morning_status['failed'])} недоступно")

                    # СРАЗУ отправляем отчет после сбора данных
                    debug_log(f"[{current_time}] 📊 Отправка утреннего отчета...")
                    self._send_morning_report(manual_call=False)  # Автоматический вызов
                    self.last_report_date = today
                    debug_log("✅ Утренний отчет отправлен")
                    
                    # Добавляем задержку чтобы не запускать повторно в ту же минуту
                    time.sleep(65)  # Спим 65 секунд чтобы выйти за пределы минуты сбора
            
            # Основной цикл мониторинга доступности
            if self.monitoring_active:
                self.last_check_time = current_time
                self._check_all_servers(current_time)

            time.sleep(settings.CHECK_INTERVAL)
    
    def _initialize_monitoring(self) -> None:
        """Инициализирует мониторинг"""
        from extensions.server_checks import initialize_servers
        
        self.servers = initialize_servers()
        
        # Исключаем сервер мониторинга из списка
        monitor_server_ip = "192.168.20.2"
        self.servers = [s for s in self.servers if s["ip"] != monitor_server_ip]
        debug_log(f"✅ Сервер мониторинга {monitor_server_ip} принудительно исключен из списка. Осталось {len(self.servers)} серверов")

        # Инициализация бота
        from telegram import Bot
        self.bot = Bot(token=settings.TELEGRAM_TOKEN)

        # Инициализация server_status (только для оставшихся серверов)
        for server in self.servers:
            self.server_status[server["ip"]] = {
                "last_up": datetime.now(),
                "alert_sent": False,
                "name": server["name"],
                "type": server["type"],
                "resources": None,
                "last_alert": {}
            }

        debug_log(f"✅ Мониторинг запущен для {len(self.servers)} серверов")

        # Обновляем стартовое сообщение
        start_message = (
            "🟢 *Мониторинг серверов запущен*\n\n"
            f"• Серверов в мониторинге: {len(self.servers)}\n"
            f"• Проверка ресурсов: каждые {settings.RESOURCE_CHECK_INTERVAL // 60} минут\n"
            f"• Утренний отчет: {settings.DATA_COLLECTION_TIME.strftime('%H:%M')}\n\n"
        )
        
        # Информация о веб-интерфейсе
        from extensions.extension_manager import extension_manager
        if extension_manager.is_extension_enabled('web_interface'):
            start_message += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
            start_message += "_*доступен только в локальной сети_\n"
        else:
            start_message += "🌐 *Веб-интерфейс:* 🔴 отключен\n"

        self.send_alert(start_message)
        
        # Инициализируем morning_data если она пустая
        if not self.morning_data:
            self.morning_data = {}
    
    def _check_all_servers(self, current_time: datetime) -> None:
        """Проверяет все серверы"""
        for server in self.servers:
            try:
                ip = server["ip"]
                status = self.server_status[ip]

                # ПОЛНОСТЬЮ ИСКЛЮЧАЕМ сервер мониторинга из любых проверок
                if ip == "192.168.20.2":
                    self.server_status[ip]["last_up"] = current_time
                    continue

                # Проверка доступности
                is_up = self.check_server_availability(server)

                if is_up:
                    self._handle_server_up(ip, status, current_time)
                else:
                    self._handle_server_down(ip, status, current_time)
                    
            except Exception as e:
                debug_log(f"❌ Ошибка мониторинга {server['name']}: {e}")
    
    def _handle_server_up(self, ip: str, status: Dict[str, Any], current_time: datetime) -> None:
        """Обработка доступного сервера"""
        if status["alert_sent"]:
            downtime = (current_time - status["last_up"]).total_seconds()
            self.send_alert(f"✅ {status['name']} ({ip}) доступен (простой: {int(downtime//60)} мин)")

        self.server_status[ip] = {
            "last_up": current_time,
            "alert_sent": False,
            "name": status["name"],
            "type": status["type"],
            "resources": self.server_status[ip].get("resources"),
            "last_alert": self.server_status[ip].get("last_alert", {})
        }
    
    def _handle_server_down(self, ip: str, status: Dict[str, Any], current_time: datetime) -> None:
        """Обработка недоступного сервера"""
        downtime = (current_time - status["last_up"]).total_seconds()
        
        if downtime >= settings.MAX_FAIL_TIME and not status["alert_sent"]:
            self.send_alert(f"🚨 {status['name']} ({ip}) не отвечает (проверка: {status['type'].upper()})")
            self.server_status[ip]["alert_sent"] = True
    
    def _check_resources_automatically(self) -> None:
        """Автоматическая проверка ресурсов с умными предупреждениями"""
        debug_log("🔍 Автоматическая проверка ресурсов серверов...")

        if not self.monitoring_active or self.is_silent_time():
            debug_log("⏸️ Проверка ресурсов пропущена (мониторинг неактивен или тихий режим)")
            return

        current_time = datetime.now()
        alerts_found = []

        # Проверяем все серверы
        for server in self.servers:
            try:
                ip = server["ip"]
                server_name = server["name"]

                debug_log(f"🔍 Проверяем ресурсы {server_name} ({ip})")

                # Получаем текущие ресурсы
                current_resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    current_resources = get_linux_resources_improved(ip)
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    current_resources = get_windows_resources_improved(ip)

                if not current_resources:
                    continue

                # Инициализируем историю для сервера если нужно
                if ip not in self.resource_history:
                    self.resource_history[ip] = []

                # Добавляем текущие ресурсы в историю
                resource_entry = {
                    "timestamp": current_time,
                    "cpu": current_resources.get("cpu", 0),
                    "ram": current_resources.get("ram", 0),
                    "disk": current_resources.get("disk", 0),
                    "server_name": server_name
                }

                self.resource_history[ip].append(resource_entry)

                # Ограничиваем историю последними 10 записями
                if len(self.resource_history[ip]) > 10:
                    self.resource_history[ip] = self.resource_history[ip][-10:]

                # Проверяем условия для алертов
                server_alerts = self._check_resource_alerts(ip, resource_entry)

                if server_alerts:
                    alerts_found.extend(server_alerts)
                    debug_log(f"⚠️ Найдены проблемы для {server_name}: {server_alerts}")

            except Exception as e:
                debug_log(f"❌ Ошибка при проверке ресурсов {server['name']}: {e}")
                continue

        # Отправляем алерты если есть
        if alerts_found:
            self._send_resource_alerts(alerts_found)

        self.last_resource_check = current_time
        debug_log(f"✅ Автоматическая проверка ресурсов завершена. Найдено проблем: {len(alerts_found)}")
    
    def _check_resource_alerts(self, ip: str, current_resource: Dict[str, Any]) -> List[str]:
        """Проверяет условия для отправки алертов по ресурсам"""
        alerts = []
        server_name = current_resource["server_name"]

        # Получаем историю проверок (исключая текущую)
        history = self.resource_history.get(ip, [])[:-1]  # Все кроме последней записи

        # Проверка Disk (одна проверка)
        disk_usage = current_resource.get("disk", 0)
        if disk_usage >= settings.RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
            # Проверяем, не отправляли ли уже алерт по диску
            alert_key = f"{ip}_disk"
            if alert_key not in self.resource_alerts_sent or (datetime.now() - self.resource_alerts_sent[alert_key]).total_seconds() > settings.RESOURCE_ALERT_INTERVAL:
                alerts.append(f"💾 **Дисковое пространство** на {server_name}: {disk_usage}% (превышен порог {settings.RESOURCE_ALERT_THRESHOLDS['disk_alert']}%)")
                self.resource_alerts_sent[alert_key] = datetime.now()

        # Проверка CPU (две проверки подряд)
        cpu_usage = current_resource.get("cpu", 0)
        if cpu_usage >= settings.RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
            # Проверяем предыдущую запись
            if len(history) >= 1:
                prev_cpu = history[-1].get("cpu", 0)
                if prev_cpu >= settings.RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
                    alert_key = f"{ip}_cpu"
                    if alert_key not in self.resource_alerts_sent or (datetime.now() - self.resource_alerts_sent[alert_key]).total_seconds() > settings.RESOURCE_ALERT_INTERVAL:
                        alerts.append(f"💻 **Процессор** на {server_name}: {prev_cpu}% → {cpu_usage}% (2 проверки подряд >= {settings.RESOURCE_ALERT_THRESHOLDS['cpu_alert']}%)")
                        self.resource_alerts_sent[alert_key] = datetime.now()

        # Проверка RAM (две проверки подряд)
        ram_usage = current_resource.get("ram", 0)
        if ram_usage >= settings.RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
            # Проверяем предыдущую запись
            if len(history) >= 1:
                prev_ram = history[-1].get("ram", 0)
                if prev_ram >= settings.RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
                    alert_key = f"{ip}_ram"
                    if alert_key not in self.resource_alerts_sent or (datetime.now() - self.resource_alerts_sent[alert_key]).total_seconds() > settings.RESOURCE_ALERT_INTERVAL:
                        alerts.append(f"🧠 **Память** на {server_name}: {prev_ram}% → {ram_usage}% (2 проверки подряд >= {settings.RESOURCE_ALERT_THRESHOLDS['ram_alert']}%)")
                        self.resource_alerts_sent[alert_key] = datetime.now()

        return alerts
    
    def _send_resource_alerts(self, alerts: List[str]) -> None:
        """Отправляет алерты по ресурсам"""
        if not alerts:
            return

        message = "🚨 *Проблемы с ресурсами серверов*\n\n"

        # Группируем алерты по типам ресурсов для лучшей читаемости
        disk_alerts = [a for a in alerts if "💾" in a]
        cpu_alerts = [a for a in alerts if "💻" in a]
        ram_alerts = [a for a in alerts if "🧠" in a]

        # Дисковое пространство
        if disk_alerts:
            message += "💾 **Дисковое пространство:**\n"
            for alert in disk_alerts:
                # Извлекаем информацию из алерта
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

        self.send_alert(message)
        debug_log(f"✅ Отправлены алерты по ресурсам: {len(alerts)} проблем")
    
    def _send_morning_report(self, manual_call: bool = False) -> None:
        """Отправляет утренний отчет о доступности серверов и бэкапах
        
        Args:
            manual_call (bool): Если True - отчет вызван вручную, если False - по расписанию
        """
        current_time = datetime.now()
        
        if manual_call:
            debug_log(f"[{current_time}] 📊 Ручной вызов отчета")
            # Для ручного вызова собираем СВЕЖИЕ данные
            current_status = self.get_current_server_status()
            self.morning_data = {
                "status": current_status,
                "collection_time": current_time,
                "manual_call": True  # Помечаем как ручной вызов
            }
        else:
            debug_log(f"[{current_time}] 📊 Автоматический утренний отчет")
            # Для автоматического отчета используем данные собранные в DATA_COLLECTION_TIME
            if not self.morning_data or "status" not in self.morning_data:
                debug_log("❌ Нет данных для утреннего отчета, собираем текущий статус...")
                current_status = self.get_current_server_status()
                self.morning_data = {
                    "status": current_status,
                    "collection_time": current_time,
                    "manual_call": False
                }
        
        status = self.morning_data["status"]
        collection_time = self.morning_data.get("collection_time", datetime.now())
        is_manual = self.morning_data.get("manual_call", False)

        total_servers = len(status["ok"]) + len(status["failed"])
        up_count = len(status["ok"])
        down_count = len(status["failed"])

        # Формируем сообщение с указанием типа отчета
        if is_manual:
            report_type = "Ручной запрос"
            time_prefix = "⏰ *Время проверки:*"
        else:
            report_type = "Утренний отчет"
            time_prefix = "⏰ *Время сбора данных:*"

        message = f"📊 *{report_type} о доступности серверов*\n\n"
        message += f"{time_prefix} {collection_time.strftime('%H:%M')}\n"
        message += f"🔢 *Всего серверов:* {total_servers}\n"
        message += f"🟢 *Доступно:* {up_count}\n"
        message += f"🔴 *Недоступно:* {down_count}\n"

        # Для ручного отчета используем другой период бэкапов
        if is_manual:
            backup_data = self._get_backup_summary_for_report(period_hours=24)  # Последние 24 часа
        else:
            backup_data = self._get_backup_summary_for_report(period_hours=16)  # С 18:00 предыдущего дня

        message += f"\n💾 *Статус бэкапов ({'за последние 24ч' if is_manual else 'за последние 16ч'})*\n"
        message += backup_data

        if down_count > 0:
            message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"

            # Группируем по типу для удобства чтения
            by_type = {}
            for server in status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)

            for server_type, servers_list in by_type.items():
                message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                for s in servers_list:
                    message += f"• {s['name']} ({s['ip']})\n"

        else:
            message += f"\n✅ *Все серверы доступны!*\n"

        message += f"\n📋 *Статистика по типам:*\n"

        # Статистика по типам серверов
        type_stats = {}
        all_servers = status["ok"] + status["failed"]
        for server in all_servers:
            if server["type"] not in type_stats:
                type_stats[server["type"]] = {"total": 0, "up": 0}
            type_stats[server["type"]]["total"] += 1

        for server in status["ok"]:
            type_stats[server["type"]]["up"] += 1

        for server_type, stats in type_stats.items():
            up_percent = (stats["up"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            message += f"• {server_type.upper()}: {stats['up']}/{stats['total']} ({up_percent:.1f}%)\n"

        if is_manual:
            message += f"\n⏰ *Отчет сформирован:* {datetime.now().strftime('%H:%M:%S')}"
        else:
            message += f"\n⏰ *Отчет отправлен:* {datetime.now().strftime('%H:%M:%S')}"

        # Отправляем отчет принудительно, даже в тихом режиме
        self.send_alert(message, force=True)
        debug_log(f"✅ {report_type} отправлен: {up_count}/{total_servers} доступно")
    
    def _get_backup_summary_for_report(self, period_hours: int = 16) -> str:
        """Получает сводку по бэкапам за указанный период
        
        Args:
            period_hours (int): Количество часов для периода (16 для авто-отчета, 24 для ручного)
        """
        try:
            debug_log(f"🔄 Сбор данных о бэкапах за {period_hours} часов...")
            
            # ДИАГНОСТИКА КОНФИГУРАЦИИ
            self._debug_proxmox_config()
            
            import sqlite3
            import os
            from datetime import datetime, timedelta
            
            db_path = "/opt/monitoring/data/backups.db"
            
            if not os.path.exists(db_path):
                debug_log(f"❌ База данных не найдена: {db_path}")
                return "❌ База данных бэкапов недоступна\n"
            
            since_time = (datetime.now() - timedelta(hours=period_hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # ДЕТАЛЬНАЯ ДИАГНОСТИКА: какие хосты есть в базе
            cursor.execute('''
                SELECT DISTINCT host_name, COUNT(*) as backup_count, 
                       MAX(received_at) as last_backup,
                       SUM(CASE WHEN backup_status = 'success' THEN 1 ELSE 0 END) as success_count
                FROM proxmox_backups 
                WHERE received_at >= datetime('now', '-7 days')
                GROUP BY host_name
                ORDER BY last_backup DESC
            ''')
            all_hosts_from_db = cursor.fetchall()
            
            debug_log("📊 ДИАГНОСТИКА - Все хосты из БД за 7 дней:")
            for host_name, count, last_backup, success_count in all_hosts_from_db:
                debug_log(f"  - {host_name}: {success_count}/{count} успешно, последний: {last_backup}")
            
            # 1. Proxmox бэкапы - считаем ПОСЛЕДНИЕ бэкапы для каждого хоста
            cursor.execute('''
                SELECT host_name, backup_status, MAX(received_at) as last_backup
                FROM proxmox_backups 
                WHERE received_at >= ?
                GROUP BY host_name
            ''', (since_time,))
            
            proxmox_results = cursor.fetchall()
            
            debug_log("📊 ДИАГНОСТИКА - Хосты с бэкапами за указанный период:")
            for host_name, status, last_backup in proxmox_results:
                debug_log(f"  - {host_name}: {status}, последний: {last_backup}")
            
            # Получаем все хосты из конфигурации
            debug_log("📊 ДИАГНОСТИКА - Хосты из конфигурации PROXMOX_HOSTS:")
            for host in settings.PROXMOX_HOSTS.keys():
                debug_log(f"  - {host}")
            
            # Определяем активные хосты
            active_host_names = [row[0] for row in all_hosts_from_db]
            all_hosts = [host for host in settings.PROXMOX_HOSTS.keys() if host in active_host_names]
            
            # Если все еще не 15, используем альтернативный метод
            if len(all_hosts) != 15:
                debug_log(f"⚠️  Найдено {len(all_hosts)} активных хостов, ожидалось 15")
                debug_log("🔍 Пробуем альтернативный метод подсчета...")
                
                # Метод 2: берем все уникальные хосты из БД за 30 дней
                cursor.execute('''
                    SELECT DISTINCT host_name 
                    FROM proxmox_backups 
                    WHERE received_at >= datetime('now', '-30 days')
                    ORDER BY host_name
                ''')
                all_unique_hosts = [row[0] for row in cursor.fetchall()]
                
                debug_log("📊 ДИАГНОСТИКА - Все уникальные хосты за 30 дней:")
                for host in all_unique_hosts:
                    debug_log(f"  - {host}")
                
                all_hosts = all_unique_hosts
            
            debug_log(f"✅ Итоговый список хостов: {len(all_hosts)} - {all_hosts}")
            
            # Считаем успешные - ВСЕ хосты у которых последний бэкап успешный
            hosts_with_success = len([r for r in proxmox_results if r[1] == 'success'])
            
            debug_log(f"📊 Proxmox итог: {hosts_with_success}/{len(all_hosts)} успешно")
            
            # 2. Базы данных - ИСПРАВЛЕННАЯ ЛОГИКА: ищем ПОСЛЕДНИЙ бэкап для каждой базы
            cursor.execute('''
                SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
                FROM database_backups 
                WHERE received_at >= ?
                GROUP BY backup_type, database_name
            ''', (since_time,))
            
            db_results = cursor.fetchall()
            
            config_databases = {
                'company_database': settings.DATABASE_BACKUP_CONFIG.get("company_databases", {}),
                'barnaul': settings.DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
                'client': settings.DATABASE_BACKUP_CONFIG.get("client_databases", {}),
                'yandex': settings.DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
            }
            
            # Считаем статистику - КАЖДАЯ база считается успешной если у нее есть успешный бэкап за период
            db_stats = {}
            for category, databases in config_databases.items():
                total_in_config = len(databases)
                if total_in_config > 0:
                    successful_count = 0
                    
                    # Для каждой базы в категории проверяем есть ли успешный бэкап
                    for db_key in databases.keys():
                        found_success = False
                        for backup_type, db_name, status, last_backup in db_results:
                            if backup_type == category and db_name == db_key and status == 'success':
                                found_success = True
                                break
                        
                        if found_success:
                            successful_count += 1
                    
                    db_stats[category] = {
                        'total': total_in_config,
                        'successful': successful_count
                    }
                    debug_log(f"📊 {category}: {successful_count}/{total_in_config} успешно")
            
            # 3. Устаревшие бэкапы (более 24 часов) - ПРАВИЛЬНЫЙ подсчет
            stale_threshold = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Устаревшие хосты - те у которых последний бэкап старше 24 часов
            cursor.execute('''
                SELECT host_name, MAX(received_at) as last_backup
                FROM proxmox_backups 
                GROUP BY host_name
                HAVING last_backup < ?
            ''', (stale_threshold,))
            stale_hosts = cursor.fetchall()
            
            # Устаревшие БД - те у которых последний бэкап старше 24 часов
            cursor.execute('''
                SELECT backup_type, database_name, MAX(received_at) as last_backup
                FROM database_backups 
                GROUP BY backup_type, database_name
                HAVING last_backup < ?
            ''', (stale_threshold,))
            stale_databases = cursor.fetchall()
            
            conn.close()
            
            # Формируем сообщение
            message = ""
            
            # Proxmox бэкапы
            if len(all_hosts) > 0:
                success_rate = (hosts_with_success / len(all_hosts)) * 100
                message += f"• Proxmox: {hosts_with_success}/{len(all_hosts)} успешно ({success_rate:.1f}%)"
                
                if stale_hosts:
                    message += f" ⚠️ {len(stale_hosts)} хостов без бэкапов >24ч"
                message += "\n"
            
            # Базы данных
            message += "• Базы данных:\n"
            
            category_names = {
                'company_database': 'Основные',
                'barnaul': 'Барнаул', 
                'client': 'Клиенты',
                'yandex': 'Yandex'
            }
            
            for category in ['company_database', 'barnaul', 'client', 'yandex']:
                if category in db_stats and db_stats[category]['total'] > 0:
                    stats = db_stats[category]
                    type_name = category_names[category]
                    
                    success_rate = (stats['successful'] / stats['total']) * 100
                    message += f"  - {type_name}: {stats['successful']}/{stats['total']} успешно ({success_rate:.1f}%)"
                    
                    # Устаревшие для этого типа
                    stale_count = len([db for db in stale_databases if db[0] == category])
                    if stale_count > 0:
                        message += f" ⚠️ {stale_count} БД без бэкапов >24ч"
                    message += "\n"
            
            # Общие проблемы
            total_stale = len(stale_hosts) + len(stale_databases)
            if total_stale > 0:
                message += f"\n🚨 Внимание: {total_stale} проблем:\n"
                if stale_hosts:
                    message += f"• {len(stale_hosts)} хостов без бэкапов >24ч\n"
                if stale_databases:
                    message += f"• {len(stale_databases)} БД без бэкапов >24ч\n"
            
            return message
            
        except Exception as e:
            debug_log(f"💥 Критическая ошибка в get_backup_summary_for_report: {e}")
            import traceback
            debug_log(f"💥 Traceback: {traceback.format_exc()}")
            return "❌ Ошибка формирования отчета о бэкапах\n"
    
    def _debug_proxmox_config(self):
        """Временная функция для диагностики конфигурации Proxmox"""
        try:
            debug_log("=== ДИАГНОСТИКА KONФИГУРАЦИИ PROXMOX ===")
            debug_log(f"Всего хостов в PROXMOX_HOSTS: {len(settings.PROXMOX_HOSTS)}")
            for i, host in enumerate(settings.PROXMOX_HOSTS.keys(), 1):
                debug_log(f"{i}. {host}")
            debug_log("=======================================")
        except Exception as e:
            debug_log(f"❌ Ошибка диагностики конфигурации: {e}")


# Глобальный экземпляр мониторинга
monitoring_core = MonitoringCore()


def start_monitoring():
    """Функция-обертка для запуска мониторинга в отдельном потоке"""
    monitoring_core.start()
