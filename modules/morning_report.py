"""
/app/modules/morning_report.py
Server Monitoring System v7.3.16
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning Report Module
Система мониторинга серверов
Версия: 7.3.16
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль утреннего отчета
"""

import threading
import time
from datetime import datetime, timedelta
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

        message = f"📊 *{report_type}*\n\n"
        message += "🖥 *Доступность серверов*\n"
        message += (
            f"• Всего: {total_servers} "
            f"(🟢 {up_count} / 🔴 {down_count})\n"
        )

        from telegram.utils.helpers import escape_markdown

        if down_count > 0:
            message += f"\n🔴 *Проблемные серверы ({down_count}):*\n"
            # Группируем по типу
            by_type = {}
            for server in status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)
                
            for server_type, servers_list in by_type.items():
                safe_type = escape_markdown(str(server_type).upper(), version=1)
                message += f"\n**{safe_type} ({len(servers_list)}):**\n"
                for s in servers_list:
                    safe_name = escape_markdown(str(s.get('name', '')), version=1)
                    safe_ip = escape_markdown(str(s.get('ip', '')), version=1)
                    message += f"• {safe_name} ({safe_ip})\n"

        # Добавляем информацию о бэкапах
        try:
            from extensions.extension_manager import extension_manager
            show_proxmox = extension_manager.is_extension_enabled('backup_monitor')
            show_databases = extension_manager.is_extension_enabled('database_backup_monitor')
            show_mail = extension_manager.is_extension_enabled('mail_backup_monitor')
            show_backups = show_proxmox or show_databases or show_mail
            if show_backups:
                backup_summary = self.get_backup_summary_for_report(
                    24 if is_manual else 16,
                    include_proxmox=True,
                    include_databases=show_databases,
                    include_mail=show_mail,
                )
                message += f"\n💾 *Статус бэкапов ({'за последние 24ч' if is_manual else 'за последние 16ч'})*\n"
                message += backup_summary
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
                message += stock_summary
        except Exception as e:
            debug_log(f"⚠️ Ошибка получения данных о загрузке остатков: {e}")
            message += "\n📦 *Загрузка остатков 1С:* данные недоступны\n"

        # Добавляем информацию о ZFS
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('zfs_monitor'):
                zfs_summary = self.get_zfs_summary_for_report()
                message += "\n🧊 *Статусы ZFS (последние)*\n"
                message += zfs_summary
        except Exception as e:
            debug_log(f"⚠️ Ошибка получения данных о ZFS: {e}")
            message += "\n🧊 *Статусы ZFS:* данные недоступны\n"
            
        message += f"\n⏰ *Отчёт сформирован:* {collection_time.strftime('%H:%M:%S')}"
        return message

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
            )
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки по бэкапам: {e}")
            return "❌ Данные о бэкапах недоступны"

    def get_zfs_summary_for_report(self):
        """Получает сводку по ZFS"""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from core.config_manager import config_manager as settings_manager

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return "❌ База бэкапов не настроена\n"

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
                    return "❌ Таблица ZFS ещё не создана.\n"
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

            latest_by_server = {}
            for server_name, _, _, received_at in rows:
                if server_name not in latest_by_server:
                    latest_by_server[server_name] = received_at
                else:
                    if received_at > latest_by_server[server_name]:
                        latest_by_server[server_name] = received_at

            stale_servers = set()
            stale_threshold = datetime.now() - timedelta(hours=24)
            for server in expected_servers:
                received_at = latest_by_server.get(server)
                if not received_at:
                    stale_servers.add(server)
                    continue
                try:
                    last_seen = datetime.strptime(received_at, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    stale_servers.add(server)
                    continue
                if last_seen < stale_threshold:
                    stale_servers.add(server)

            if not rows and expected_servers:
                stale_list = ", ".join(sorted(stale_servers))
                servers_total = len(expected_servers)
                servers_problem = len(stale_servers)
                servers_ok = servers_total - servers_problem
                return (
                    f"• Серверов: {servers_total} (🟢 {servers_ok} / 🔴 {servers_problem})\n"
                    "• Пулов: 0 (🟢 0 / 🔴 0)\n"
                    f"• Нет свежих данных (>24ч): {stale_list}\n"
                )
            if not rows:
                return "• Данных нет\n"

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

            if stale_servers:
                stale_list = ", ".join(sorted(stale_servers))
                summary += f"• Нет свежих данных (>24ч): {stale_list}\n"

            return summary
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки ZFS: {e}")
            return "❌ Данные ZFS недоступны\n"
    
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
