"""
/extensions/backup_monitor/backup_utils.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utilities for working with backups
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РЈС‚РёР»РёС‚С‹ РґР»СЏ СЂР°Р±РѕС‚С‹ СЃ Р±СЌРєР°РїР°РјРё
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
    """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅ Р»Рё РјРѕРЅРёС‚РѕСЂРёРЅРі С…РѕСЃС‚Р° Proxmox."""
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
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ С‚РµРєСЃС‚РѕРІСѓСЋ СЃРІРѕРґРєСѓ РїРѕ Р±СЌРєР°РїР°Рј Р·Р° РїРµСЂРёРѕРґ."""
    try:
        from config.db_settings import DATA_DIR, DATABASE_BACKUP_CONFIG, PROXMOX_HOSTS

        db_path = DATA_DIR / "backups.db"
        if not db_path.exists():
            logger.error("Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р±СЌРєР°РїРѕРІ РЅРµРґРѕСЃС‚СѓРїРЅР°: %s", db_path)
            return "вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р±СЌРєР°РїРѕРІ РЅРµРґРѕСЃС‚СѓРїРЅР°\n", True

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
                "Р¤РёР»РёР°Р»С‹",
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
                proxmox_icon = "рџ”ґ" if proxmox_has_issues else "рџџў"
                message += (
                    f"вЂў {proxmox_icon} Proxmox: {hosts_with_success}/{len(all_hosts)} СѓСЃРїРµС€РЅРѕ "
                    f"({success_rate:.1f}%)"
                )
                if stale_hosts:
                    message += f" вљ пёЏ {len(stale_hosts)} С…РѕСЃС‚РѕРІ Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡"
                if unavailable_hosts_set:
                    message += f" вљ пёЏ {len(unavailable_hosts_set)} С…РѕСЃС‚РѕРІ РЅРµРґРѕСЃС‚СѓРїРЅС‹"
                message += "\n"
            else:
                message += "вЂў рџџЎ Proxmox: РЅРµС‚ РґР°РЅРЅС‹С…\n"

        if include_databases:
            message += "вЂў Р‘Р°Р·С‹ РґР°РЅРЅС‹С…:\n"

        if include_databases:
            category_names = {
                'company_database': 'РћСЃРЅРѕРІРЅС‹Рµ',
                'barnaul': 'Р‘Р°СЂРЅР°СѓР»',
                'client': 'РљР»РёРµРЅС‚С‹',
                'yandex': 'Yandex',
            }

            total_configured = sum(
                len(databases) for databases in config_databases.values()
                if isinstance(databases, dict)
            )
            if total_configured == 0:
                if not db_results:
                    message += "  - РќРµС‚ РЅР°СЃС‚СЂРѕРµРЅРЅС‹С… Р‘Р”\n"
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
                        db_icon = "рџџў" if is_ok else "рџ”ґ"
                        message += (
                            f"  - {db_icon} {type_name}: {stats['successful']}/{stats['total']} СѓСЃРїРµС€РЅРѕ "
                            f"({success_rate:.1f}%)"
                        )

                        if stale_count > 0:
                            message += f" вљ пёЏ {stale_count} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡"
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
                    db_icon = "рџџў" if is_ok else "рџ”ґ"
                    message += (
                        f"  - {db_icon} {type_name}: {stats['successful']}/{stats['total']} "
                        f"СѓСЃРїРµС€РЅРѕ ({success_rate:.1f}%)"
                    )

                    if stale_count > 0:
                        message += f" вљ пёЏ {stale_count} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡"
                    if missing_recent > 0:
                        message += f" вљ пёЏ {missing_recent} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ Р·Р° РїРѕСЃР»РµРґРЅРёРµ {period_hours}С‡"
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

            message += f"\nрџљЁ Р’РЅРёРјР°РЅРёРµ: {total_issues} РїСЂРѕР±Р»РµРј:\n"
            if include_proxmox and stale_hosts:
                message += f"вЂў {len(stale_hosts)} С…РѕСЃС‚РѕРІ Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡\n"
            if include_proxmox and unavailable_hosts_set:
                message += f"вЂў {len(unavailable_hosts_set)} С…РѕСЃС‚РѕРІ РЅРµРґРѕСЃС‚СѓРїРЅС‹\n"
            if include_databases and stale_databases and not stale_by_category:
                message += f"вЂў {len(stale_databases)} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡\n"
            if include_databases and total_missing_recent > 0 and not missing_recent_by_category:
                message += (
                    f"вЂў {total_missing_recent} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ Р·Р° РїРѕСЃР»РµРґРЅРёРµ {period_hours}С‡\n"
                )

            if include_proxmox and stale_hosts:
                stale_host_names = sorted({host_name for host_name, _ in stale_hosts})
                stale_host_list = ", ".join(stale_host_names)
                message += f"вЂў РџСЂРѕР±Р»РµРјРЅС‹Рµ С…РѕСЃС‚С‹ (>24С‡): {stale_host_list}\n"

            if include_databases and stale_by_category:
                message += "вЂў РџСЂРѕР±Р»РµРјРЅС‹Рµ Р‘Р” (>24С‡):\n"
                for category in ['company_database', 'barnaul', 'client', 'yandex']:
                    if category not in stale_by_category:
                        continue
                    db_list = ", ".join(sorted(stale_by_category[category]))
                    type_name = category_names.get(category, category)
                    message += f"  - {type_name}: {db_list}\n"

            if include_databases and missing_recent_by_category:
                message += (
                    f"вЂў РќРµС‚ Р±СЌРєР°РїРѕРІ Р·Р° РїРѕСЃР»РµРґРЅРёРµ {period_hours}С‡:\n"
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
                    return "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                try:
                    last_time = datetime.strptime(received_at, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                hours_ago = int((datetime.now() - last_time).total_seconds() / 3600)
                if hours_ago >= 24:
                    days = hours_ago // 24
                    hours = hours_ago % 24
                    return f"{days}Рґ {hours}С‡ РЅР°Р·Р°Рґ"
                return f"{hours_ago}С‡ РЅР°Р·Р°Рґ"

            if not mail_latest:
                message += "вЂў рџџЎ РџРѕС‡С‚Р°: РЅРµС‚ РґР°РЅРЅС‹С…\n"
            else:
                status, size, path, received_at = mail_latest
                size_text = size or "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                path_text = path or "Р±РµР· РїСѓС‚Рё"
                time_ago = _mail_time_ago(received_at)
                mail_has_issues = mail_recent is None
                mail_icon = "рџ”ґ" if mail_has_issues else "рџџў"
                if mail_recent:
                    message += (
                        f"вЂў {mail_icon} РџРѕС‡С‚Р°: {size_text} {path_text} ({time_ago})\n"
                    )
                else:
                    message += (
                        f"вЂў {mail_icon} РџРѕС‡С‚Р°: РЅРµС‚ СЃРІРµР¶РёС… Р±СЌРєР°РїРѕРІ "
                        f"(>{period_hours}С‡), РїРѕСЃР»РµРґРЅРёР№: {size_text} "
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
        logger.exception("РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡РµС‚Р° Рѕ Р±СЌРєР°РїР°С…: %s", e)
        return "вќЊ РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡РµС‚Р° Рѕ Р±СЌРєР°РїР°С…\n", True


def get_stock_load_summary(period_hours=16) -> str:
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРІРѕРґРєСѓ РїРѕ Р·Р°РіСЂСѓР·РєРµ РѕСЃС‚Р°С‚РєРѕРІ Р·Р° РїРµСЂРёРѕРґ."""
    try:
        from config.db_settings import DATA_DIR

        db_path = DATA_DIR / "backups.db"
        if not db_path.exists():
            logger.error("Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р±СЌРєР°РїРѕРІ РЅРµРґРѕСЃС‚СѓРїРЅР°: %s", db_path)
            return "вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р±СЌРєР°РїРѕРІ РЅРµРґРѕСЃС‚СѓРїРЅР°\n"

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
                return "вќЊ РўР°Р±Р»РёС†Р° РѕСЃС‚Р°С‚РєРѕРІ РµС‰С‘ РЅРµ СЃРѕР·РґР°РЅР°.\n"
            raise
        finally:
            conn.close()

        if not rows:
            return "вќЊ РќРµС‚ СЃРІРµР¶РёС… РґР°РЅРЅС‹С… Рѕ Р·Р°РіСЂСѓР·РєРµ РѕСЃС‚Р°С‚РєРѕРІ\n"

        total = len(rows)
        success_count = len([row for row in rows if row[1] == "success"])
        warning_count = len([row for row in rows if row[1] == "warning"])
        failed_count = len([row for row in rows if row[1] == "failed"])
        unknown_count = total - success_count - warning_count - failed_count

        summary = f"вЂў Р¤Р°Р№Р»РѕРІ: {total}, вњ… {success_count} СѓСЃРїРµС€РЅРѕ"
        if warning_count:
            summary += f", вљ пёЏ {warning_count} СЃ РѕС€РёР±РєР°РјРё"
        if failed_count:
            summary += f", вќЊ {failed_count} РЅРµСѓРґР°С‡РЅРѕ"
        if unknown_count:
            summary += f", вќ” {unknown_count} Р±РµР· СЃС‚Р°С‚СѓСЃР°"
        summary += "\n"

        return summary

    except Exception as exc:
        logger.exception("РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ СЃРІРѕРґРєРё РѕСЃС‚Р°С‚РєРѕРІ: %s", exc)
        return "вќЊ РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡РµС‚Р° Рѕ Р·Р°РіСЂСѓР·РєРµ РѕСЃС‚Р°С‚РєРѕРІ\n"


class BackupBase:
    """Р‘Р°Р·РѕРІС‹Р№ РєР»Р°СЃСЃ РґР»СЏ СЂР°Р±РѕС‚С‹ СЃ Р±СЌРєР°РїР°РјРё"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def execute_query(self, query, params=()):
        """Р’С‹РїРѕР»РЅСЏРµС‚ SQL Р·Р°РїСЂРѕСЃ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ СЂРµР·СѓР»СЊС‚Р°С‚С‹"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"РћС€РёР±РєР° РІС‹РїРѕР»РЅРµРЅРёСЏ Р·Р°РїСЂРѕСЃР°: {e}")
            return []
    
    def execute_many(self, query, params_list):
        """Р’С‹РїРѕР»РЅСЏРµС‚ Р·Р°РїСЂРѕСЃ СЃ РЅРµСЃРєРѕР»СЊРєРёРјРё РЅР°Р±РѕСЂР°РјРё РїР°СЂР°РјРµС‚СЂРѕРІ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"РћС€РёР±РєР° РІС‹РїРѕР»РЅРµРЅРёСЏ РјР°СЃСЃРѕРІРѕРіРѕ Р·Р°РїСЂРѕСЃР°: {e}")
            return False
    
    def format_time_ago(self, time_str):
        """Р¤РѕСЂРјР°С‚РёСЂСѓРµС‚ РІСЂРµРјСЏ РІ С‡РёС‚Р°РµРјС‹Р№ С„РѕСЂРјР°С‚ 'XРґ YС‡ РЅР°Р·Р°Рґ'"""
        try:
            if not time_str:
                return "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                
            time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            time_diff = datetime.now() - time_obj
            hours_ago = int(time_diff.total_seconds() / 3600)
            
            if hours_ago >= 24:
                days = hours_ago // 24
                hours = hours_ago % 24
                return f"{days}Рґ {hours}С‡ РЅР°Р·Р°Рґ"
            else:
                return f"{hours_ago}С‡ РЅР°Р·Р°Рґ"
        except Exception:
            return "РѕС€РёР±РєР° РІСЂРµРјРµРЅРё"

class StatusCalculator:
    """РљР°Р»СЊРєСѓР»СЏС‚РѕСЂ СЃС‚Р°С‚СѓСЃРѕРІ РґР»СЏ С…РѕСЃС‚РѕРІ Рё Р‘Р”"""

    @staticmethod
    def calculate_host_status(recent_backups, alert_hours=24, stale_hours=48):
        """Р Р°СЃСЃС‡РёС‚С‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ С…РѕСЃС‚Р° РЅР° РѕСЃРЅРѕРІРµ recent_backups"""
        if not recent_backups:
            return "stale"

        last_status, last_time = recent_backups[0]

        # РџРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї РЅРµСѓСЃРїРµС€РЅС‹Р№
        if last_status != 'success':
            return "failed"

        # Р•СЃС‚СЊ РЅРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ РІ РёСЃС‚РѕСЂРёРё
        recent_failed = any(status != 'success' for status, _ in recent_backups[:3])
        if recent_failed:
            return "recent_failed"

        # РџСЂРѕРІРµСЂСЏРµРј СЃРІРµР¶РµСЃС‚СЊ
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
        """Р Р°СЃСЃС‡РёС‚С‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ Р‘Р” РЅР° РѕСЃРЅРѕРІРµ recent_backups"""
        if not recent_backups:
            return "stale"
        
        last_status, last_time, last_error_count = recent_backups[0]
        
        # РџРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї РЅРµСѓРґР°С‡РЅС‹Р№
        if last_status == 'failed':
            return "failed"
        
        # РћС€РёР±РєРё РІ РїРѕСЃР»РµРґРЅРµРј Р±СЌРєР°РїРµ
        if last_error_count and last_error_count > 0:
            return "warning"
        
        # РќРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ РІ РёСЃС‚РѕСЂРёРё
        recent_failed = any(status == 'failed' for status, _, _ in recent_backups[:3])
        if recent_failed:
            return "recent_failed"
        
        # РћС€РёР±РєРё РІ РёСЃС‚РѕСЂРёРё
        recent_errors = any(error_count and error_count > 0 for _, _, error_count in recent_backups[:3])
        if recent_errors:
            return "recent_errors"
        
        # РџСЂРѕРІРµСЂСЏРµРј СЃРІРµР¶РµСЃС‚СЊ
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
    """Р¤РѕСЂРјР°С‚С‚РµСЂС‹ РґР»СЏ РѕС‚РѕР±СЂР°Р¶РµРЅРёСЏ"""
    
    HOST_STATUS_ICONS = {
        "success": "вњ…",
        "failed": "рџ”ґ", 
        "recent_failed": "рџџ ",
        "old": "рџџЎ",
        "stale": "вљ«",
        "unknown": "вљЄ"
    }
    
    DB_STATUS_ICONS = {
        "success": "вњ…",
        "failed": "рџ”ґ",
        "recent_failed": "рџџ ", 
        "warning": "рџџЎ",
        "recent_errors": "рџџ ",
        "old": "рџџЎ",
        "stale": "вљ«",
        "unknown": "вљЄ"
    }
    
    TYPE_ICONS = {
        'company_database': 'рџЏў',
        'barnaul': 'рџЏ”пёЏ',
        'client': 'рџ‘Ґ', 
        'yandex': 'вЃпёЏ'
    }
    
    TYPE_NAMES = {
        'company_database': 'РћСЃРЅРѕРІРЅС‹Рµ Р‘Р” РєРѕРјРїР°РЅРёРё',
        'barnaul': 'Р‘СЌРєР°РїС‹ Р‘Р°СЂРЅР°СѓР»',
        'client': 'Р‘Р°Р·С‹ РєР»РёРµРЅС‚РѕРІ',
        'yandex': 'Р‘СЌРєР°РїС‹ РЅР° Yandex'
    }
    
    @classmethod
    def get_host_display_name(cls, host_name, status):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕС‚РѕР±СЂР°Р¶Р°РµРјРѕРµ РёРјСЏ С…РѕСЃС‚Р° СЃ РёРєРѕРЅРєРѕР№"""
        icon = cls.HOST_STATUS_ICONS.get(status, "вљЄ")
        return f"{icon} {host_name}"
    
    @classmethod
    def get_db_display_name(cls, display_name, status):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕС‚РѕР±СЂР°Р¶Р°РµРјРѕРµ РёРјСЏ Р‘Р” СЃ РёРєРѕРЅРєРѕР№"""
        icon = cls.DB_STATUS_ICONS.get(status, "вљЄ")
        # РћРіСЂР°РЅРёС‡РёРІР°РµРј РґР»РёРЅСѓ РґР»СЏ РєРЅРѕРїРѕРє
        if len(display_name) > 12:
            display_name = display_name[:10] + ".."
        return f"{icon} {display_name}"
    
    @classmethod
    def get_type_display(cls, backup_type):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕС‚РѕР±СЂР°Р¶Р°РµРјРѕРµ РёРјСЏ С‚РёРїР°"""
        icon = cls.TYPE_ICONS.get(backup_type, 'рџ“Ѓ')
        name = cls.TYPE_NAMES.get(backup_type, backup_type)
        return f"{icon} {name}"
    
