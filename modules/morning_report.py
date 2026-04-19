"""
/app/modules/morning_report.py
Server Monitoring System v8.56.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning Report Module
Система мониторинга серверов
Версия: 8.56.1
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль утреннего отчета
"""

import threading
import time
from datetime import datetime, timedelta, timezone
import sqlite3
from config.db_settings import DATA_COLLECTION_TIME
from lib.logging import debug_log

class MorningReport:
    """Класс управления утренними отчетами"""
    
    def __init__(self):
        self.morning_data = {}
        self.last_report_date = None
        self.last_data_collection = None
        
    def collect_morning_data(self, manual_call=False):
        """Сбор данных для утреннего отчета"""
        try:
            from modules.availability import availability_monitor
            current_status = availability_monitor.get_current_status()
            
            self.morning_data = {
                "status": current_status,
                "collection_time": datetime.now(),
                "manual_call": manual_call
            }
            
            debug_log(f"✅ Данные для отчета собраны: {len(current_status['ok'])} доступно, {len(current_status['failed'])} недоступно")
            return True
        except Exception as e:
            debug_log(f"❌ Ошибка сбора данных для отчета: {e}")
            return False
    
    def generate_report_message(self):
        """Генерация сообщения отчета"""
        if not self.morning_data or "status" not in self.morning_data:
            return "❌ Нет данных для отчета"
            
        status = self.morning_data["status"]
        collection_time = self.morning_data.get("collection_time", datetime.now())
        is_manual = self.morning_data.get("manual_call", False)
        
        total_servers = len(status["ok"]) + len(status["failed"])
        up_count = len(status["ok"])
        down_count = len(status["failed"])
        
        # Определяем тип отчета
        report_type = "Ручной отчёт мониторинга" if is_manual else "Утренний отчёт мониторинга"
        try:
            from config.settings import APP_VERSION
        except Exception:
            APP_VERSION = None

        message = f"📊 *{report_type}*\n\n"
        if APP_VERSION:
            message += f"🔖 *Версия:* {APP_VERSION}\n"
        message += "🖥 *Доступность серверов*\n"
        availability_rows = [
            ("Всего", str(total_servers)),
            ("🟢 Доступно", str(up_count)),
            ("🔴 Недоступно", str(down_count)),
        ]
        message += self._render_key_value_table(availability_rows)

        from telegram.utils.helpers import escape_markdown

        if down_count > 0:
            message += f"\n🔴 *Проблемные серверы ({down_count})*\n"
            # Группируем по типу
            by_type = {}
            for server in status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)
            problem_rows = []
            for server_type, servers_list in sorted(by_type.items(), key=lambda item: str(item[0])):
                for s in servers_list:
                    safe_type = escape_markdown(str(server_type).upper(), version=1)
                    safe_name = escape_markdown(str(s.get('name', '')), version=1)
                    safe_ip = escape_markdown(str(s.get('ip', '')), version=1)
                    problem_rows.append((safe_type, safe_name, safe_ip))
            message += self._render_table(
                headers=("Тип", "Сервер", "IP"),
                rows=problem_rows,
            )

        # Добавляем информацию о бэкапах
        try:
            from extensions.extension_manager import extension_manager
            show_proxmox = extension_manager.is_extension_enabled('backup_monitor')
            show_databases = extension_manager.is_extension_enabled('database_backup_monitor')
            show_mail = extension_manager.is_extension_enabled('mail_backup_monitor')
            show_backups = show_proxmox or show_databases or show_mail
            if show_backups:
                unavailable_hosts = set()
                for server in status.get("failed", []):
                    if server.get("name"):
                        unavailable_hosts.add(server.get("name"))
                    if server.get("ip"):
                        unavailable_hosts.add(server.get("ip"))
                backup_summary, backup_has_issues = self.get_backup_summary_for_report(
                    24 if is_manual else 16,
                    include_proxmox=show_proxmox,
                    include_databases=show_databases,
                    include_mail=show_mail,
                    unavailable_hosts=unavailable_hosts,
                )
                backup_header_icon = "🔴" if backup_has_issues else "🟢"
                message += (
                    f"\n{backup_header_icon} *Статус бэкапов "
                    f"({'за последние 24ч' if is_manual else 'за последние 16ч'})*\n"
                )
                message += self._render_plain_block(backup_summary)
        except Exception as e:
            debug_log(f"⚠️ Ошибка получения данных о бэкапах: {e}")
            message += "\n💾 *Статус бэкапов:* данные недоступны\n"

        # Добавляем информацию о загрузке остатков 1С
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('stock_load_monitor'):
                from extensions.backup_monitor.backup_utils import get_stock_load_summary

                stock_summary = get_stock_load_summary(24 if is_manual else 16)
                message += "\n📦 *Загрузка остатков 1С*\n"
                message += self._render_plain_block(stock_summary)
        except Exception as e:
            debug_log(f"⚠️ Ошибка получения данных о загрузке остатков: {e}")
            message += "\n📦 *Загрузка остатков 1С:* данные недоступны\n"

        # Добавляем информацию о ZFS
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('zfs_monitor'):
                zfs_summary, zfs_has_issues = self.get_zfs_summary_for_report()
                zfs_header_icon = "🔴" if zfs_has_issues else "🟢"
                message += f"\n{zfs_header_icon} *Статусы ZFS (последние)*\n"
                message += self._render_plain_block(zfs_summary)
        except Exception as e:
            debug_log(f"⚠️ Ошибка получения данных о ZFS: {e}")
            message += "\n🧊 *Статусы ZFS:* данные недоступны\n"
            
        message += f"\n⏰ *Отчёт сформирован:* {collection_time.strftime('%H:%M:%S')}"
        return message

    def _render_table(self, headers, rows):
        """Рендерит компактную ASCII-таблицу в markdown code block."""
        normalized_rows = [tuple(str(cell) for cell in row) for row in rows]
        normalized_headers = tuple(str(cell) for cell in headers)
        widths = [len(normalized_headers[i]) for i in range(len(normalized_headers))]

        for row in normalized_rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        def format_row(row_values):
            return " | ".join(row_values[i].ljust(widths[i]) for i in range(len(row_values)))

        separator = "-+-".join("-" * width for width in widths)
        lines = [format_row(normalized_headers), separator]
        lines.extend(format_row(row) for row in normalized_rows)
        return "```\n" + "\n".join(lines) + "\n```\n"

    def _render_key_value_table(self, rows):
        """Рендерит компактную 2-колоночную таблицу без заголовков."""
        normalized_rows = [tuple(str(cell) for cell in row) for row in rows]
        if not normalized_rows:
            return "```\nнет данных\n```\n"

        left_width = max(len(row[0]) for row in normalized_rows)
        lines = [f"{key.ljust(left_width)} | {value}" for key, value in normalized_rows]
        return "```\n" + "\n".join(lines) + "\n```\n"

    def _render_plain_block(self, text):
        """Приводит markdown-списки к компактному блоку фиксированной ширины."""
        lines = []
        for raw_line in str(text).splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("• "):
                line = line[2:]
            if line.startswith("- "):
                line = line[2:]
            lines.append(line)
        if not lines:
            return "```\nнет данных\n```\n"
        return "```\n" + "\n".join(lines) + "\n```\n"

    def force_report(self):
        """Формирует отчет для ручного запроса и возвращает текст"""
        data_collected = self.collect_morning_data(manual_call=True)
        if not data_collected:
            return "❌ Ошибка сбора данных для отчета"

        return self.generate_report_message()
    
    def get_backup_summary_for_report(
        self,
        period_hours=16,
        include_proxmox=True,
        include_databases=True,
        include_mail=False,
        unavailable_hosts=None,
    ):
        """Получает сводку по бэкапам"""
        try:
            # Импорт функций бэкапов
            from extensions.backup_monitor.backup_utils import get_backup_summary
            return get_backup_summary(
                period_hours,
                include_proxmox=include_proxmox,
                include_databases=include_databases,
                include_mail=include_mail,
                unavailable_hosts=unavailable_hosts,
            )
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки по бэкапам: {e}")
            return "❌ Данные о бэкапах недоступны", True

    def get_zfs_summary_for_report(self):
        """Получает сводку по ZFS"""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from core.config_manager import config_manager as settings_manager

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return "❌ База бэкапов не настроена\n", True

            zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
            if not isinstance(zfs_servers, dict):
                zfs_servers = {}

            allowed_servers = {
                name
                for name, server_value in zfs_servers.items()
                if not isinstance(server_value, dict) or server_value.get('enabled', True)
            }

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT s.server_name, s.pool_name, s.pool_state, s.received_at
                    FROM zfs_pool_status s
                    JOIN (
                        SELECT server_name, pool_name, MAX(received_at) AS last_seen
                        FROM zfs_pool_status
                        GROUP BY server_name, pool_name
                    ) latest
                    ON s.server_name = latest.server_name
                    AND s.pool_name = latest.pool_name
                    AND s.received_at = latest.last_seen
                    ORDER BY s.server_name, s.pool_name
                    """
                )
                rows = cursor.fetchall()
            except Exception as exc:
                if "no such table: zfs_pool_status" in str(exc):
                    return "❌ Таблица ZFS ещё не создана.\n", True
                raise
            finally:
                conn.close()

            if allowed_servers:
                rows = [row for row in rows if row[0] in allowed_servers]
            else:
                rows = []

            expected_servers = set(allowed_servers)
            if not expected_servers:
                expected_servers = {row[0] for row in rows}

            def parse_received_at(value):
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8")
                    except Exception:
                        return None
                if isinstance(value, (int, float)):
                    try:
                        return datetime.fromtimestamp(value)
                    except (ValueError, OSError):
                        return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    normalized = value.strip()
                    if normalized.endswith("Z"):
                        normalized = f"{normalized[:-1]}+00:00"
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                        try:
                            return datetime.strptime(normalized, fmt)
                        except ValueError:
                            continue
                    if len(normalized) >= 19:
                        try:
                            return datetime.strptime(normalized[:19], "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            pass
                    try:
                        return datetime.fromisoformat(normalized)
                    except ValueError:
                        return None
                return None

            latest_by_server = {}
            for server_name, _, _, received_at in rows:
                parsed_time = parse_received_at(received_at)
                if server_name not in latest_by_server:
                    latest_by_server[server_name] = parsed_time
                    continue
                current_latest = latest_by_server.get(server_name)
                if not current_latest or (parsed_time and parsed_time > current_latest):
                    latest_by_server[server_name] = parsed_time

            stale_servers = set()
            stale_threshold = datetime.now() - timedelta(hours=24)

            def parse_received_at(value):
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                    try:
                        return datetime.fromisoformat(value)
                    except ValueError:
                        return None
                return None
            for server in expected_servers:
                received_at = latest_by_server.get(server)
                if not received_at:
                    stale_servers.add(server)
                    continue
                if received_at.tzinfo is not None:
                    received_at = received_at.astimezone(timezone.utc).replace(tzinfo=None)
                if received_at < stale_threshold:
                    stale_servers.add(server)

            if not rows and expected_servers:
                servers_total = len(expected_servers)
                servers_problem = len(stale_servers)
                servers_ok = servers_total - servers_problem
                summary = (
                    f"• Серверов: {servers_total} (🟢 {servers_ok} / 🔴 {servers_problem})\n"
                    "• Пулов: 0 (🟢 0 / 🔴 0)\n"
                )
                return summary, True
            if not rows:
                return "• Данных нет\n", False

            total_pools = len(rows)
            ok_pools = sum(
                1
                for server_name, _, pool_state, _ in rows
                if server_name not in stale_servers and str(pool_state).upper() == "ONLINE"
            )
            bad_pools = sum(
                1
                for server_name, _, pool_state, _ in rows
                if server_name not in stale_servers and str(pool_state).upper() != "ONLINE"
            )
            servers_count = len(expected_servers) if expected_servers else len({row[0] for row in rows})
            server_problem_flags = {server: False for server in expected_servers}
            for server_name, _, pool_state, _ in rows:
                if server_name in stale_servers:
                    continue
                if str(pool_state).upper() != "ONLINE":
                    server_problem_flags[server_name] = True

            servers_problem = len(
                {server for server in expected_servers if server in stale_servers or server_problem_flags.get(server)}
            )
            servers_ok = servers_count - servers_problem

            summary = (
                f"• Серверов: {servers_count} (🟢 {servers_ok} / 🔴 {servers_problem})\n"
                f"• Пулов: {total_pools} (🟢 {ok_pools} / 🔴 {bad_pools})\n"
            )

            has_issues = servers_problem > 0 or bad_pools > 0 or bool(stale_servers)
            return summary, has_issues
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки ZFS: {e}")
            return "❌ Данные ZFS недоступны\n", True
    
    def send_report(self, manual_call=False):
        """Отправка отчета"""
        try:
            # Собираем данные
            self.collect_morning_data(manual_call)
            
            # Генерируем сообщение
            message = self.generate_report_message()
            
            # Отправляем через обработчик
            from bot.handlers.commands import send_alert
            send_alert(message, force=True)
            
            debug_log(f"✅ Отчет отправлен ({'ручной' if manual_call else 'автоматический'})")
            return True
        except Exception as e:
            debug_log(f"❌ Ошибка отправки отчета: {e}")
            return False
    
    def start_scheduler(self):
        """Запуск планировщика отчетов"""
        debug_log("⏰ Запуск планировщика утренних отчетов")
        
        while True:
            current_time = datetime.now()
            current_time_time = current_time.time()
            
            # Проверяем время сбора данных
            if (current_time_time.hour == DATA_COLLECTION_TIME.hour and
                current_time_time.minute == DATA_COLLECTION_TIME.minute):
                
                # Проверяем, что сегодня еще не отправляли отчет
                today = current_time.date()
                if self.last_report_date != today:
                    debug_log(f"📊 Автоматический сбор данных для утреннего отчета")
                    self.send_report(manual_call=False)
                    self.last_report_date = today
                    
                    # Задержка чтобы не запускать повторно в ту же минуту
                    time.sleep(65)
                else:
                    debug_log(f"⏭️ Отчет уже отправлен сегодня {self.last_report_date}")
            
            time.sleep(60)  # Проверяем каждую минуту

# Глобальный экземпляр отчета
morning_report = MorningReport()
