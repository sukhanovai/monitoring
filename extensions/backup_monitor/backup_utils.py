"""
/extensions/backup_monitor/backup_utils.py
Server Monitoring System v8.2.66
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utilities for working with backups
Система мониторинга серверов
Версия: 8.2.66
Автор: Александр Суханов (c)
Лицензия: MIT
Утилиты для работы с бэкапами
"""

import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def _normalize_db_key(name: str) -> str:
    return str(name or "").replace("-", "_").lower()


def _normalize_backup_type(backup_type: str, db_name: str) -> str:
    if _normalize_db_key(db_name) == "trade" and backup_type == "client":
        return "company_database"
    return backup_type


def _normalize_host_key(value: object) -> str:
    return str(value or "").strip().lower()


def _is_proxmox_host_enabled(host_value: object) -> bool:
    """Проверяет, включен ли мониторинг хоста Proxmox."""
    if isinstance(host_value, dict):
        return host_value.get("enabled", True)
    return True


def get_backup_summary(
    period_hours=16,
    include_proxmox=True,
    include_databases=True,
    include_mail=False,
    unavailable_hosts=None,
):
    """Возвращает текстовую сводку по бэкапам за период."""
    try:
        from config.db_settings import DATA_DIR, DATABASE_BACKUP_CONFIG, PROXMOX_HOSTS

        db_path = DATA_DIR / "backups.db"
        if not db_path.exists():
            logger.error("База данных бэкапов недоступна: %s", db_path)
            return "❌ База данных бэкапов недоступна\n", True

        since_time = (datetime.now() - timedelta(hours=period_hours)).strftime('%Y-%m-%d %H:%M:%S')
        stale_threshold = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        proxmox_results = []
        stale_hosts = []
        all_hosts = []
        unavailable_hosts_norm = {_normalize_host_key(host) for host in (unavailable_hosts or [])}
        if include_proxmox:
            cursor.execute('''
                SELECT DISTINCT host_name
                FROM proxmox_backups
                WHERE received_at >= datetime('now', '-30 days')
                ORDER BY host_name
            ''')
            all_hosts = [row[0] for row in cursor.fetchall()]
            if PROXMOX_HOSTS:
                configured_hosts = {
                    host for host, value in PROXMOX_HOSTS.items()
                    if _is_proxmox_host_enabled(value)
                }
                db_hosts = set(all_hosts)
                matched_hosts = sorted(configured_hosts & db_hosts)
                all_hosts = matched_hosts or list(configured_hosts)

            cursor.execute('''
                SELECT host_name, backup_status, MAX(received_at) as last_backup
                FROM proxmox_backups
                WHERE received_at >= ?
                GROUP BY host_name
            ''', (since_time,))
            proxmox_results = cursor.fetchall()

            cursor.execute('''
                SELECT host_name, MAX(received_at) as last_backup
                FROM proxmox_backups
                GROUP BY host_name
                HAVING last_backup < ?
            ''', (stale_threshold,))
            stale_hosts = cursor.fetchall()

        db_results = []
        stale_databases = []
        if include_databases:
            cursor.execute('''
                SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
                FROM database_backups
                WHERE received_at >= ?
                GROUP BY backup_type, database_name
            ''', (since_time,))
            db_results = cursor.fetchall()
            db_results = [
                (_normalize_backup_type(backup_type, db_name), db_name, status, last_backup)
                for backup_type, db_name, status, last_backup in db_results
            ]

            cursor.execute('''
                SELECT backup_type, database_name, MAX(received_at) as last_backup
                FROM database_backups
                GROUP BY backup_type, database_name
                HAVING last_backup < ?
            ''', (stale_threshold,))
            stale_databases = cursor.fetchall()
            stale_databases = [
                (_normalize_backup_type(backup_type, db_name), db_name, last_backup)
                for backup_type, db_name, last_backup in stale_databases
            ]

        mail_recent = None
        mail_latest = None
        if include_mail:
            try:
                cursor.execute(
                    '''
                    SELECT backup_status, total_size, backup_path, received_at
                    FROM mail_server_backups
                    WHERE received_at >= ?
                    ORDER BY received_at DESC
                    LIMIT 1
                ''',
                    (since_time,),
                )
                mail_recent = cursor.fetchone()

                cursor.execute(
                    '''
                    SELECT backup_status, total_size, backup_path, received_at
                    FROM mail_server_backups
                    ORDER BY received_at DESC
                    LIMIT 1
                '''
                )
                mail_latest = cursor.fetchone()
            except Exception as exc:
                if "no such table: mail_server_backups" in str(exc):
                    mail_latest = None
                else:
                    raise

        conn.close()

        allowed_hosts = set(all_hosts)
        unavailable_hosts_set = set()
        if include_proxmox and PROXMOX_HOSTS and unavailable_hosts_norm:
            for host_name, host_value in PROXMOX_HOSTS.items():
                if host_name not in allowed_hosts:
                    continue
                aliases = {_normalize_host_key(host_name)}
                if isinstance(host_value, dict):
                    for key in ("ip", "host", "hostname", "name", "address", "addr"):
                        value = host_value.get(key)
                        if isinstance(value, (list, tuple, set)):
                            aliases.update(_normalize_host_key(item) for item in value)
                        elif value:
                            aliases.add(_normalize_host_key(value))
                elif host_value:
                    aliases.add(_normalize_host_key(host_value))
                if aliases & unavailable_hosts_norm:
                    unavailable_hosts_set.add(host_name)
        if unavailable_hosts_norm and not unavailable_hosts_set:
            unavailable_hosts_set = {
                host_name for host_name in allowed_hosts
                if _normalize_host_key(host_name) in unavailable_hosts_norm
            }
        hosts_with_success = len([
            r for r in proxmox_results
            if r[1] == 'success' and r[0] in allowed_hosts
            and r[0] not in unavailable_hosts_set
        ])

        def _get_db_config(config: dict, *keys: str) -> dict:
            for key in keys:
                value = config.get(key)
                if isinstance(value, dict):
                    return value
            return {}

        company_databases = _get_db_config(
            DATABASE_BACKUP_CONFIG,
            "company_databases",
            "company_database",
            "company",
        )
        client_databases = _get_db_config(
            DATABASE_BACKUP_CONFIG,
            "client_databases",
            "client",
            "clients",
        )
        if "trade" in client_databases and "trade" in company_databases:
            client_databases = {
                key: value for key, value in client_databases.items() if key != "trade"
            }

        config_databases = {
            'company_database': company_databases,
            'barnaul': _get_db_config(
                DATABASE_BACKUP_CONFIG,
                "barnaul_backups",
                "barnaul",
                "Филиалы",
            ),
            'client': client_databases,
            'yandex': _get_db_config(DATABASE_BACKUP_CONFIG, "yandex_backups", "yandex"),
        }

        db_stats = {}
        configured_databases = {
            category: set(databases.keys())
            for category, databases in config_databases.items()
            if databases
        }
        configured_db_keys = {
            (category, db_name)
            for category, databases in configured_databases.items()
            for db_name in databases
        }
        recent_db_keys = {
            (backup_type, db_name)
            for backup_type, db_name, _, _ in db_results
        }
        successful_db_keys = {
            (backup_type, db_name)
            for backup_type, db_name, status, _ in db_results
            if status == 'success'
        }

        missing_recent_db_keys = {
            (category, db_name)
            for category, databases in configured_databases.items()
            for db_name in databases
            if (category, db_name) not in recent_db_keys
        }

        stale_databases = [
            (backup_type, db_name, last_backup)
            for backup_type, db_name, last_backup in stale_databases
            if (backup_type, db_name) in configured_db_keys
        ]
        stale_databases = [
            (backup_type, db_name, last_backup)
            for backup_type, db_name, last_backup in stale_databases
            if (backup_type, db_name) not in recent_db_keys
        ]
        stale_databases_unique = {}
        for backup_type, db_name, last_backup in stale_databases:
            key = (backup_type, db_name)
            current_last = stale_databases_unique.get(key)
            if current_last is None or last_backup > current_last:
                stale_databases_unique[key] = last_backup
        stale_databases = [
            (backup_type, db_name, last_backup)
            for (backup_type, db_name), last_backup in stale_databases_unique.items()
        ]
        stale_databases = [
            (backup_type, db_name, last_backup)
            for backup_type, db_name, last_backup in stale_databases
            if (backup_type, db_name) not in missing_recent_db_keys
        ]

        for category, databases in config_databases.items():
            total_in_config = len(databases)
            if total_in_config == 0:
                continue

            successful_count = 0
            missing_recent = 0
            for db_key in databases.keys():
                if (category, db_key) in successful_db_keys:
                    successful_count += 1
                if (category, db_key) not in recent_db_keys:
                    missing_recent += 1

            db_stats[category] = {
                'total': total_in_config,
                'successful': successful_count,
                'missing_recent': missing_recent,
            }

        message = ""

        if include_proxmox:
            if len(all_hosts) > 0:
                success_rate = (hosts_with_success / len(all_hosts)) * 100
                proxmox_has_issues = (
                    bool(stale_hosts)
                    or bool(unavailable_hosts_set)
                    or hosts_with_success < len(all_hosts)
                )
                proxmox_icon = "🔴" if proxmox_has_issues else "🟢"
                message += (
                    f"• {proxmox_icon} Proxmox: {hosts_with_success}/{len(all_hosts)} успешно "
                    f"({success_rate:.1f}%)"
                )
                if stale_hosts:
                    message += f" ⚠️ {len(stale_hosts)} хостов без бэкапов >24ч"
                if unavailable_hosts_set:
                    message += f" ⚠️ {len(unavailable_hosts_set)} хостов недоступны"
                message += "\n"
            else:
                message += "• 🟡 Proxmox: нет данных\n"

        if include_databases:
            message += "• Базы данных:\n"

        if include_databases:
            category_names = {
                'company_database': 'Основные',
                'barnaul': 'Барнаул',
                'client': 'Клиенты',
                'yandex': 'Yandex',
            }

            total_configured = sum(
                len(databases) for databases in config_databases.values()
                if isinstance(databases, dict)
            )
            if total_configured == 0:
                if not db_results:
                    message += "  - Нет настроенных БД\n"
                else:
                    fallback_stats = {}
                    for backup_type, db_name, status, _ in db_results:
                        stats = fallback_stats.setdefault(
                            backup_type,
                            {"total": 0, "successful": 0},
                        )
                        stats["total"] += 1
                        if status == 'success':
                            stats["successful"] += 1

                    for backup_type in ['company_database', 'barnaul', 'client', 'yandex']:
                        if backup_type not in fallback_stats:
                            continue
                        stats = fallback_stats[backup_type]
                        if stats["total"] <= 0:
                            continue

                        type_name = category_names.get(backup_type, backup_type)
                        success_rate = (stats["successful"] / stats["total"]) * 100
                        stale_count = len([db for db in stale_databases if db[0] == backup_type])
                        is_ok = stats["successful"] == stats["total"] and stale_count == 0
                        db_icon = "🟢" if is_ok else "🔴"
                        message += (
                            f"  - {db_icon} {type_name}: {stats['successful']}/{stats['total']} успешно "
                            f"({success_rate:.1f}%)"
                        )

                        if stale_count > 0:
                            message += f" ⚠️ {stale_count} БД без бэкапов >24ч"
                        message += "\n"
            else:
                for category in ['company_database', 'barnaul', 'client', 'yandex']:
                    if category not in db_stats:
                        continue
                    stats = db_stats[category]
                    if stats['total'] <= 0:
                        continue

                    type_name = category_names[category]
                    success_rate = (stats['successful'] / stats['total']) * 100
                    stale_count = len([db for db in stale_databases if db[0] == category])
                    missing_recent = stats.get('missing_recent', 0)
                    is_ok = (
                        stats['successful'] == stats['total']
                        and stale_count == 0
                        and missing_recent == 0
                    )
                    db_icon = "🟢" if is_ok else "🔴"
                    message += (
                        f"  - {db_icon} {type_name}: {stats['successful']}/{stats['total']} "
                        f"успешно ({success_rate:.1f}%)"
                    )

                    if stale_count > 0:
                        message += f" ⚠️ {stale_count} БД без бэкапов >24ч"
                    if missing_recent > 0:
                        message += f" ⚠️ {missing_recent} БД без бэкапов за последние {period_hours}ч"
                    message += "\n"

        total_stale = 0
        if include_proxmox:
            total_stale += len(stale_hosts)
        if include_databases:
            total_stale += len(stale_databases)
        total_unavailable = len(unavailable_hosts_set) if include_proxmox else 0

        total_missing_recent = 0
        if include_databases:
            total_missing_recent = sum(
                stats.get('missing_recent', 0) for stats in db_stats.values()
            )

        total_issues = total_stale + total_missing_recent + total_unavailable
        if total_issues > 0:
            stale_by_category = {}
            if include_databases:
                for backup_type, db_name, _ in stale_databases:
                    stale_by_category.setdefault(backup_type, []).append(db_name)

            missing_recent_by_category = {}
            if include_databases:
                for backup_type, db_name in sorted(missing_recent_db_keys):
                    missing_recent_by_category.setdefault(backup_type, []).append(db_name)

            message += f"\n🚨 Внимание: {total_issues} проблем:\n"
            if include_proxmox and stale_hosts:
                message += f"• {len(stale_hosts)} хостов без бэкапов >24ч\n"
            if include_proxmox and unavailable_hosts_set:
                message += f"• {len(unavailable_hosts_set)} хостов недоступны\n"
            if include_databases and stale_databases and not stale_by_category:
                message += f"• {len(stale_databases)} БД без бэкапов >24ч\n"
            if include_databases and total_missing_recent > 0 and not missing_recent_by_category:
                message += (
                    f"• {total_missing_recent} БД без бэкапов за последние {period_hours}ч\n"
                )

            if include_proxmox and stale_hosts:
                stale_host_names = sorted({host_name for host_name, _ in stale_hosts})
                stale_host_list = ", ".join(stale_host_names)
                message += f"• Проблемные хосты (>24ч): {stale_host_list}\n"

            if include_databases and stale_by_category:
                message += "• Проблемные БД (>24ч):\n"
                for category in ['company_database', 'barnaul', 'client', 'yandex']:
                    if category not in stale_by_category:
                        continue
                    db_list = ", ".join(sorted(stale_by_category[category]))
                    type_name = category_names.get(category, category)
                    message += f"  - {type_name}: {db_list}\n"

            if include_databases and missing_recent_by_category:
                message += (
                    f"• Нет бэкапов за последние {period_hours}ч:\n"
                )
                for category in ['company_database', 'barnaul', 'client', 'yandex']:
                    if category not in missing_recent_by_category:
                        continue
                    db_list = ", ".join(sorted(missing_recent_by_category[category]))
                    type_name = category_names.get(category, category)
                    message += f"  - {type_name}: {db_list}\n"

        if include_mail:
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
                message += "• 🟡 Почта: нет данных\n"
            else:
                status, size, path, received_at = mail_latest
                size_text = size or "неизвестно"
                path_text = path or "без пути"
                time_ago = _mail_time_ago(received_at)
                mail_has_issues = mail_recent is None
                mail_icon = "🔴" if mail_has_issues else "🟢"
                if mail_recent:
                    message += (
                        f"• {mail_icon} Почта: {size_text} {path_text} ({time_ago})\n"
                    )
                else:
                    message += (
                        f"• {mail_icon} Почта: нет свежих бэкапов "
                        f"(>{period_hours}ч), последний: {size_text} "
                        f"{path_text} ({time_ago})\n"
                    )

        has_issues = total_issues > 0
        if include_proxmox and all_hosts and hosts_with_success < len(all_hosts):
            has_issues = True
        if include_proxmox and unavailable_hosts_set:
            has_issues = True
        if include_mail and mail_latest and mail_recent is None:
            has_issues = True

        return message, has_issues

    except Exception as e:
        logger.exception("Ошибка формирования отчета о бэкапах: %s", e)
        return "❌ Ошибка формирования отчета о бэкапах\n", True


def get_stock_load_summary(period_hours=16) -> str:
    """Возвращает сводку по загрузке остатков за период."""
    try:
        from config.db_settings import DATA_DIR

        db_path = DATA_DIR / "backups.db"
        if not db_path.exists():
            logger.error("База данных бэкапов недоступна: %s", db_path)
            return "❌ База данных бэкапов недоступна\n"

        since_time = (datetime.now() - timedelta(hours=period_hours)).strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT supplier_name, status, rows_count, error_sample, received_at
                FROM stock_load_results
                WHERE received_at >= ?
                ORDER BY received_at DESC
            """,
                (since_time,),
            )
            rows = cursor.fetchall()
        except Exception as exc:
            if "no such table: stock_load_results" in str(exc):
                return "❌ Таблица остатков ещё не создана.\n"
            raise
        finally:
            conn.close()

        if not rows:
            return "❌ Нет свежих данных о загрузке остатков\n"

        total = len(rows)
        success_count = len([row for row in rows if row[1] == "success"])
        warning_count = len([row for row in rows if row[1] == "warning"])
        failed_count = len([row for row in rows if row[1] == "failed"])
        unknown_count = total - success_count - warning_count - failed_count

        summary = f"• Файлов: {total}, ✅ {success_count} успешно"
        if warning_count:
            summary += f", ⚠️ {warning_count} с ошибками"
        if failed_count:
            summary += f", ❌ {failed_count} неудачно"
        if unknown_count:
            summary += f", ❔ {unknown_count} без статуса"
        summary += "\n"

        return summary

    except Exception as exc:
        logger.exception("Ошибка формирования сводки остатков: %s", exc)
        return "❌ Ошибка формирования отчета о загрузке остатков\n"


class BackupBase:
    """Базовый класс для работы с бэкапами"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def execute_query(self, query, params=()):
        """Выполняет SQL запрос и возвращает результаты"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return []
    
    def execute_many(self, query, params_list):
        """Выполняет запрос с несколькими наборами параметров"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка выполнения массового запроса: {e}")
            return False
    
    def format_time_ago(self, time_str):
        """Форматирует время в читаемый формат 'Xд Yч назад'"""
        try:
            if not time_str:
                return "неизвестно"
                
            time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            time_diff = datetime.now() - time_obj
            hours_ago = int(time_diff.total_seconds() / 3600)
            
            if hours_ago >= 24:
                days = hours_ago // 24
                hours = hours_ago % 24
                return f"{days}д {hours}ч назад"
            else:
                return f"{hours_ago}ч назад"
        except Exception:
            return "ошибка времени"

class StatusCalculator:
    """Калькулятор статусов для хостов и БД"""

    @staticmethod
    def calculate_host_status(recent_backups, alert_hours=24, stale_hours=48):
        """Рассчитывает статус хоста на основе recent_backups"""
        if not recent_backups:
            return "stale"

        last_status, last_time = recent_backups[0]

        # Последний бэкап неуспешный
        if last_status != 'success':
            return "failed"

        # Есть неудачные бэкапы в истории
        recent_failed = any(status != 'success' for status, _ in recent_backups[:3])
        if recent_failed:
            return "recent_failed"

        # Проверяем свежесть
        try:
            last_backup_time = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
            hours_since_last = (datetime.now() - last_backup_time).total_seconds() / 3600

            if hours_since_last > stale_hours:
                return "stale"
            elif hours_since_last > alert_hours:
                return "old"
            else:
                return "success"
        except Exception:
            return "unknown"
    
    @staticmethod
    def calculate_db_status(recent_backups, hours_threshold=48):
        """Рассчитывает статус БД на основе recent_backups"""
        if not recent_backups:
            return "stale"
        
        last_status, last_time, last_error_count = recent_backups[0]
        
        # Последний бэкап неудачный
        if last_status == 'failed':
            return "failed"
        
        # Ошибки в последнем бэкапе
        if last_error_count and last_error_count > 0:
            return "warning"
        
        # Неудачные бэкапы в истории
        recent_failed = any(status == 'failed' for status, _, _ in recent_backups[:3])
        if recent_failed:
            return "recent_failed"
        
        # Ошибки в истории
        recent_errors = any(error_count and error_count > 0 for _, _, error_count in recent_backups[:3])
        if recent_errors:
            return "recent_errors"
        
        # Проверяем свежесть
        try:
            last_backup_time = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
            hours_since_last = (datetime.now() - last_backup_time).total_seconds() / 3600
            
            if hours_since_last > hours_threshold:
                return "stale"
            elif hours_since_last > 24:
                return "old"
            else:
                return "success"
        except Exception:
            return "unknown"

class DisplayFormatters:
    """Форматтеры для отображения"""
    
    HOST_STATUS_ICONS = {
        "success": "✅",
        "failed": "🔴", 
        "recent_failed": "🟠",
        "old": "🟡",
        "stale": "⚫",
        "unknown": "⚪"
    }
    
    DB_STATUS_ICONS = {
        "success": "✅",
        "failed": "🔴",
        "recent_failed": "🟠", 
        "warning": "🟡",
        "recent_errors": "🟠",
        "old": "🟡",
        "stale": "⚫",
        "unknown": "⚪"
    }
    
    TYPE_ICONS = {
        'company_database': '🏢',
        'barnaul': '🏔️',
        'client': '👥', 
        'yandex': '☁️'
    }
    
    TYPE_NAMES = {
        'company_database': 'Основные БД компании',
        'barnaul': 'Бэкапы Барнаул',
        'client': 'Базы клиентов',
        'yandex': 'Бэкапы на Yandex'
    }
    
    @classmethod
    def get_host_display_name(cls, host_name, status):
        """Возвращает отображаемое имя хоста с иконкой"""
        icon = cls.HOST_STATUS_ICONS.get(status, "⚪")
        return f"{icon} {host_name}"
    
    @classmethod
    def get_db_display_name(cls, display_name, status):
        """Возвращает отображаемое имя БД с иконкой"""
        icon = cls.DB_STATUS_ICONS.get(status, "⚪")
        # Ограничиваем длину для кнопок
        if len(display_name) > 12:
            display_name = display_name[:10] + ".."
        return f"{icon} {display_name}"
    
    @classmethod
    def get_type_display(cls, backup_type):
        """Возвращает отображаемое имя типа"""
        icon = cls.TYPE_ICONS.get(backup_type, '📁')
        name = cls.TYPE_NAMES.get(backup_type, backup_type)
        return f"{icon} {name}"
    
