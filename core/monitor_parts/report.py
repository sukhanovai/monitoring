"""
/core/monitor_parts/report.py
Server Monitoring System v8.62.82
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning report assembly extracted from core/monitor_core.py
(PR5 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.82
Автор: Александр Суханов (c)
Лицензия: MIT
Сборка ежеутреннего сводного отчёта о доступности серверов и состоянии
резервных копий: `send_morning_report`, `get_backup_summary_for_report`
и отладочная `debug_backup_data`.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from config.db_settings import DATA_DIR
from core.monitor_state import state
from lib.logging import debug_log, error_log


def send_morning_report(manual_call: bool = False) -> bool:
    """Отправляет утренний отчет о доступности серверов и бэкапах.

    Args:
        manual_call: Если True — отчет вызван вручную, если False — по расписанию.
    """
    from core.monitor_core import get_current_server_status, send_alert

    current_time = datetime.now()

    if manual_call:
        debug_log(f"[{current_time}] 📊 Ручной вызов отчета")
        current_status = get_current_server_status()
        state.morning_data = {
            "status": current_status,
            "collection_time": current_time,
            "manual_call": True,
        }
    else:
        debug_log(f"[{current_time}] 📊 Автоматический утренний отчет")
        if not state.morning_data or "status" not in state.morning_data:
            debug_log("❌ Нет данных для утреннего отчета, собираем текущий статус...")
            current_status = get_current_server_status()
            state.morning_data = {
                "status": current_status,
                "collection_time": current_time,
                "manual_call": False,
            }

    status = state.morning_data["status"]
    collection_time = state.morning_data.get("collection_time", datetime.now())
    is_manual = state.morning_data.get("manual_call", False)

    total_servers = len(status["ok"]) + len(status["failed"])
    up_count = len(status["ok"])
    down_count = len(status["failed"])

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

    try:
        from extensions.extension_manager import extension_manager

        include_mail = extension_manager.is_extension_enabled("mail_backup_monitor")
    except Exception:
        include_mail = False

    period_hours = 24 if is_manual else 16
    backup_data = get_backup_summary_for_report(
        period_hours=period_hours, include_mail=include_mail
    )

    message += (
        f"\n💾 *Статус бэкапов ({'за последние 24ч' if is_manual else 'за последние 16ч'})*\n"
    )
    message += backup_data

    if down_count > 0:
        message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"
        by_type: dict[str, list[dict[str, Any]]] = {}
        for server in status["failed"]:
            by_type.setdefault(server["type"], []).append(server)
        for server_type, servers_list in by_type.items():
            message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
            for s in servers_list:
                message += f"• {s['name']} ({s['ip']})\n"
    else:
        message += "\n✅ *Все серверы доступны!*\n"

    message += "\n📋 *Статистика по типам:*\n"
    type_stats: dict[str, dict[str, int]] = {}
    all_servers = status["ok"] + status["failed"]
    for server in all_servers:
        type_stats.setdefault(server["type"], {"total": 0, "up": 0})["total"] += 1
    for server in status["ok"]:
        type_stats[server["type"]]["up"] += 1
    for server_type, stats in type_stats.items():
        up_percent = (stats["up"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        message += f"• {server_type.upper()}: {stats['up']}/{stats['total']} ({up_percent:.1f}%)\n"

    if is_manual:
        message += f"\n⏰ *Отчет сформирован:* {datetime.now().strftime('%H:%M:%S')}"
    else:
        message += f"\n⏰ *Отчет отправлен:* {datetime.now().strftime('%H:%M:%S')}"

    debug_log(
        f"📨 Подготовлен {report_type}: длина={len(message)} символов, "
        f"время_сбора={collection_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    sent_ok = send_alert(message, force=True)
    if sent_ok:
        debug_log(f"✅ {report_type} отправлен: {up_count}/{total_servers} доступно")
    else:
        error_log(f"❌ {report_type} не доставлен во все чаты (или не доставлен вообще)")
    return sent_ok


def debug_backup_data() -> None:
    """Временная функция для отладки данных бэкапов."""
    try:
        db_path = DATA_DIR / "backups.db"

        if not db_path.exists():
            debug_log("❌ База данных backups.db не существует!")
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        debug_log(f"📋 Таблицы в базе: {[t[0] for t in tables]}")

        cursor.execute(
            "SELECT COUNT(*) as count, COUNT(DISTINCT host_name) as hosts "
            "FROM proxmox_backups WHERE received_at >= datetime('now', '-16 hours')"
        )
        proxmox_stats = cursor.fetchone()
        debug_log(f"📊 Proxmox записи: {proxmox_stats[0]}, хостов: {proxmox_stats[1]}")

        cursor.execute(
            "SELECT COUNT(*) as count, COUNT(DISTINCT database_name) as dbs "
            "FROM database_backups WHERE received_at >= datetime('now', '-16 hours')"
        )
        db_stats = cursor.fetchone()
        debug_log(f"📊 DB записи: {db_stats[0]}, баз: {db_stats[1]}")

        cursor.execute(
            """
            SELECT backup_type, COUNT(DISTINCT database_name) as dbs_count
            FROM database_backups
            WHERE received_at >= datetime('now', '-16 hours')
            GROUP BY backup_type
            """
        )
        db_by_type = cursor.fetchall()
        debug_log(f"📊 БД по типам: {dict(db_by_type)}")

        conn.close()
    except Exception as e:
        debug_log(f"❌ Ошибка диагностики: {e}")


def get_backup_summary_for_report(period_hours=16, include_mail=False):
    """Получает сводку по бэкапам за указанный период

    Args:
        period_hours (int): Количество часов для периода (16 для авто-отчета, 24 для ручного)
        include_mail (bool): Добавлять ли бэкапы почтового сервера
    """
    try:
        debug_log(f"🔄 Сбор данных о бэкапах за {period_hours} часов...")

        # ДИАГНОСТИКА КОНФИГУРАЦИИ
        debug_proxmox_config()

        import sqlite3
        from datetime import datetime, timedelta

        db_path = DATA_DIR / "backups.db"

        if not db_path.exists():
            debug_log(f"❌ База данных не найдена: {db_path}")
            return "❌ База данных бэкапов недоступна\n"

        since_time = (datetime.now() - timedelta(hours=period_hours)).strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # ДЕТАЛЬНАЯ ДИАГНОСТИКА: какие хосты есть в базе
        cursor.execute(
            """
            SELECT DISTINCT host_name, COUNT(*) as backup_count,
                   MAX(received_at) as last_backup,
                   SUM(CASE WHEN backup_status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM proxmox_backups
            WHERE received_at >= datetime('now', '-7 days')
            GROUP BY host_name
            ORDER BY last_backup DESC
        """
        )
        all_hosts_from_db = cursor.fetchall()

        debug_log("📊 ДИАГНОСТИКА - Все хосты из БД за 7 дней:")
        for host_name, count, last_backup, success_count in all_hosts_from_db:
            debug_log(f"  - {host_name}: {success_count}/{count} успешно, последний: {last_backup}")

        # 1. Proxmox бэкапы - считаем ПОСЛЕДНИЕ бэкапы для каждого хоста
        cursor.execute(
            """
            SELECT host_name, backup_status, MAX(received_at) as last_backup
            FROM proxmox_backups
            WHERE received_at >= ?
            GROUP BY host_name
        """,
            (since_time,),
        )

        proxmox_results = cursor.fetchall()

        debug_log("📊 ДИАГНОСТИКА - Хосты с бэкапами за указанный период:")
        for host_name, status, last_backup in proxmox_results:
            debug_log(f"  - {host_name}: {status}, последний: {last_backup}")

        # Получаем все хосты из конфигурации
        from config.db_settings import PROXMOX_HOSTS

        def is_proxmox_host_enabled(host_value):
            """Проверяет, включен ли мониторинг хоста Proxmox."""
            if isinstance(host_value, dict):
                return host_value.get("enabled", True)
            return True

        enabled_hosts = [
            host for host, value in PROXMOX_HOSTS.items() if is_proxmox_host_enabled(value)
        ]

        debug_log("📊 ДИАГНОСТИКА - Хосты из конфигурации PROXMOX_HOSTS:")
        for host in enabled_hosts:
            debug_log(f"  - {host}")

        # Определяем активные хосты
        active_host_names = [row[0] for row in all_hosts_from_db]
        all_hosts = [host for host in enabled_hosts if host in active_host_names]

        # Если все еще не 15, используем альтернативный метод
        if len(all_hosts) != 15:
            debug_log(f"⚠️  Найдено {len(all_hosts)} активных хостов, ожидалось 15")
            debug_log("🔍 Пробуем альтернативный метод подсчета...")

            # Метод 2: берем все уникальные хосты из БД за 30 дней
            cursor.execute(
                """
                SELECT DISTINCT host_name
                FROM proxmox_backups
                WHERE received_at >= datetime('now', '-30 days')
                ORDER BY host_name
            """
            )
            all_unique_hosts = [row[0] for row in cursor.fetchall()]

            debug_log("📊 ДИАГНОСТИКА - Все уникальные хосты за 30 дней:")
            for host in all_unique_hosts:
                debug_log(f"  - {host}")

            all_hosts = all_unique_hosts

        debug_log(f"✅ Итоговый список хостов: {len(all_hosts)} - {all_hosts}")

        # Считаем успешные - ВСЕ хосты у которых последний бэкап успешный
        hosts_with_success = len([r for r in proxmox_results if r[1] == "success"])

        debug_log(f"📊 Proxmox итог: {hosts_with_success}/{len(all_hosts)} успешно")

        # 2. Базы данных - ИСПРАВЛЕННАЯ ЛОГИКА: ищем ПОСЛЕДНИЙ бэкап для каждой базы
        cursor.execute(
            """
            SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
            FROM database_backups
            WHERE received_at >= ?
            GROUP BY backup_type, database_name
        """,
            (since_time,),
        )

        db_results = cursor.fetchall()

        # Получаем конфигурацию
        from config.db_settings import DATABASE_BACKUP_CONFIG

        config_databases = {
            "company_database": DATABASE_BACKUP_CONFIG.get("company_databases", {}),
            "barnaul": DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
            "client": DATABASE_BACKUP_CONFIG.get("client_databases", {}),
            "yandex": DATABASE_BACKUP_CONFIG.get("yandex_backups", {}),
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
                        if backup_type == category and db_name == db_key and status == "success":
                            found_success = True
                            break

                    if found_success:
                        successful_count += 1

                db_stats[category] = {"total": total_in_config, "successful": successful_count}
                debug_log(f"📊 {category}: {successful_count}/{total_in_config} успешно")

        # 3. Устаревшие бэкапы (более 24 часов) - ПРАВИЛЬНЫЙ подсчет
        stale_threshold = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        # Устаревшие хосты - те у которых последний бэкап старше 24 часов
        cursor.execute(
            """
            SELECT host_name, MAX(received_at) as last_backup
            FROM proxmox_backups
            GROUP BY host_name
            HAVING last_backup < ?
        """,
            (stale_threshold,),
        )
        stale_hosts = cursor.fetchall()

        # Устаревшие БД - те у которых последний бэкап старше 24 часов
        cursor.execute(
            """
            SELECT backup_type, database_name, MAX(received_at) as last_backup
            FROM database_backups
            GROUP BY backup_type, database_name
            HAVING last_backup < ?
        """,
            (stale_threshold,),
        )
        stale_databases = cursor.fetchall()

        mail_recent = None
        mail_latest = None
        try:
            cursor.execute(
                """
                SELECT backup_status, total_size, backup_path, received_at
                FROM mail_server_backups
                WHERE received_at >= ?
                ORDER BY received_at DESC
                LIMIT 1
            """,
                (since_time,),
            )
            mail_recent = cursor.fetchone()

            cursor.execute(
                """
                SELECT backup_status, total_size, backup_path, received_at
                FROM mail_server_backups
                ORDER BY received_at DESC
                LIMIT 1
            """
            )
            mail_latest = cursor.fetchone()
        except Exception as exc:
            if "no such table: mail_server_backups" in str(exc):
                mail_latest = None
            else:
                raise

        conn.close()

        # Формируем сообщение
        message = ""

        # Proxmox бэкапы
        if len(all_hosts) > 0:
            success_rate = (hosts_with_success / len(all_hosts)) * 100
            message += (
                f"• Proxmox: {hosts_with_success}/{len(all_hosts)} успешно ({success_rate:.1f}%)"
            )

            if stale_hosts:
                message += f" ⚠️ {len(stale_hosts)} хостов без бэкапов >24ч"
            message += "\n"

        # Базы данных
        message += "• Базы данных:\n"

        category_names = {
            "company_database": "Основные",
            "barnaul": "Барнаул",
            "client": "Клиенты",
            "yandex": "Yandex",
        }

        for category in ["company_database", "barnaul", "client", "yandex"]:
            if category in db_stats and db_stats[category]["total"] > 0:
                stats = db_stats[category]
                type_name = category_names[category]

                success_rate = (stats["successful"] / stats["total"]) * 100
                message += f"  - {type_name}: {stats['successful']}/{stats['total']} успешно ({success_rate:.1f}%)"

                # Устаревшие для этого типа
                stale_count = len([db for db in stale_databases if db[0] == category])
                if stale_count > 0:
                    message += f" ⚠️ {stale_count} БД без бэкапов >24ч"
                message += "\n"

        if include_mail:
            try:

                def _mail_time_ago(received_at):
                    if not received_at:
                        return "неизвестно"
                    try:
                        last_time = datetime.strptime(received_at, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        return "неизвестно"
                    hours_ago = int((datetime.now() - last_time).total_seconds() / 3600)
                    if hours_ago >= 24:
                        days = hours_ago // 24
                        hours = hours_ago % 24
                        return f"{days}д {hours}ч назад"
                    return f"{hours_ago}ч назад"

                if not mail_latest:
                    message += "• Почта: нет данных\n"
                else:
                    _, size, path, received_at = mail_latest
                    size_text = size or "неизвестно"
                    path_text = path or "без пути"
                    time_ago = _mail_time_ago(received_at)
                    if mail_recent:
                        message += f"• Почта: {size_text} {path_text} ({time_ago})\n"
                    else:
                        message += (
                            f"• Почта: нет свежих бэкапов "
                            f"(>{period_hours}ч), последний: {size_text} "
                            f"{path_text} ({time_ago})\n"
                        )
            except Exception as exc:
                debug_log(f"⚠️ Ошибка получения данных о бэкапах почты: {exc}")

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


__all__ = [
    "debug_backup_data",
    "get_backup_summary_for_report",
    "send_morning_report",
]
