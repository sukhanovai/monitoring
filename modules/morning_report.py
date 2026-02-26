"""
/app/modules/morning_report.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning Report Module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°
"""

import threading
import time
from datetime import datetime, timedelta, timezone
import sqlite3
from config.db_settings import DATA_COLLECTION_TIME
from lib.logging import debug_log

class MorningReport:
    """РљР»Р°СЃСЃ СѓРїСЂР°РІР»РµРЅРёСЏ СѓС‚СЂРµРЅРЅРёРјРё РѕС‚С‡РµС‚Р°РјРё"""
    
    def __init__(self):
        self.morning_data = {}
        self.last_report_date = None
        self.last_data_collection = None
        
    def collect_morning_data(self, manual_call=False):
        """РЎР±РѕСЂ РґР°РЅРЅС‹С… РґР»СЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°"""
        try:
            from modules.availability import availability_monitor
            current_status = availability_monitor.get_current_status()
            
            self.morning_data = {
                "status": current_status,
                "collection_time": datetime.now(),
                "manual_call": manual_call
            }
            
            debug_log(f"вњ… Р”Р°РЅРЅС‹Рµ РґР»СЏ РѕС‚С‡РµС‚Р° СЃРѕР±СЂР°РЅС‹: {len(current_status['ok'])} РґРѕСЃС‚СѓРїРЅРѕ, {len(current_status['failed'])} РЅРµРґРѕСЃС‚СѓРїРЅРѕ")
            return True
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° СЃР±РѕСЂР° РґР°РЅРЅС‹С… РґР»СЏ РѕС‚С‡РµС‚Р°: {e}")
            return False
    
    def generate_report_message(self):
        """Р“РµРЅРµСЂР°С†РёСЏ СЃРѕРѕР±С‰РµРЅРёСЏ РѕС‚С‡РµС‚Р°"""
        if not self.morning_data or "status" not in self.morning_data:
            return "вќЊ РќРµС‚ РґР°РЅРЅС‹С… РґР»СЏ РѕС‚С‡РµС‚Р°"
            
        status = self.morning_data["status"]
        collection_time = self.morning_data.get("collection_time", datetime.now())
        is_manual = self.morning_data.get("manual_call", False)
        
        total_servers = len(status["ok"]) + len(status["failed"])
        up_count = len(status["ok"])
        down_count = len(status["failed"])
        
        # РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РѕС‚С‡РµС‚Р°
        report_type = "Р СѓС‡РЅРѕР№ РѕС‚С‡С‘С‚ РјРѕРЅРёС‚РѕСЂРёРЅРіР°" if is_manual else "РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡С‘С‚ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"
        try:
            from config.settings import APP_VERSION
        except Exception:
            APP_VERSION = None

        message = f"рџ“Љ *{report_type}*\n\n"
        if APP_VERSION:
            message += f"рџ”– *Р’РµСЂСЃРёСЏ:* {APP_VERSION}\n"
        message += "рџ–Ґ *Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРµСЂРѕРІ*\n"
        message += (
            f"вЂў Р’СЃРµРіРѕ: {total_servers} "
            f"(рџџў {up_count} / рџ”ґ {down_count})\n"
        )

        from telegram.utils.helpers import escape_markdown

        if down_count > 0:
            message += f"\nрџ”ґ *РџСЂРѕР±Р»РµРјРЅС‹Рµ СЃРµСЂРІРµСЂС‹ ({down_count}):*\n"
            # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїСѓ
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
                    message += f"вЂў {safe_name} ({safe_ip})\n"

        # Р”РѕР±Р°РІР»СЏРµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ Р±СЌРєР°РїР°С…
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
                backup_header_icon = "рџ”ґ" if backup_has_issues else "рџџў"
                message += (
                    f"\n{backup_header_icon} *РЎС‚Р°С‚СѓСЃ Р±СЌРєР°РїРѕРІ "
                    f"({'Р·Р° РїРѕСЃР»РµРґРЅРёРµ 24С‡' if is_manual else 'Р·Р° РїРѕСЃР»РµРґРЅРёРµ 16С‡'})*\n"
                )
                message += backup_summary
        except Exception as e:
            debug_log(f"вљ пёЏ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РґР°РЅРЅС‹С… Рѕ Р±СЌРєР°РїР°С…: {e}")
            message += "\nрџ’ѕ *РЎС‚Р°С‚СѓСЃ Р±СЌРєР°РїРѕРІ:* РґР°РЅРЅС‹Рµ РЅРµРґРѕСЃС‚СѓРїРЅС‹\n"

        # Р”РѕР±Р°РІР»СЏРµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ Р·Р°РіСЂСѓР·РєРµ РѕСЃС‚Р°С‚РєРѕРІ 1РЎ
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('stock_load_monitor'):
                from extensions.backup_monitor.backup_utils import get_stock_load_summary

                stock_summary = get_stock_load_summary(24 if is_manual else 16)
                message += "\nрџ“¦ *Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ 1РЎ*\n"
                message += stock_summary
        except Exception as e:
            debug_log(f"вљ пёЏ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РґР°РЅРЅС‹С… Рѕ Р·Р°РіСЂСѓР·РєРµ РѕСЃС‚Р°С‚РєРѕРІ: {e}")
            message += "\nрџ“¦ *Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ 1РЎ:* РґР°РЅРЅС‹Рµ РЅРµРґРѕСЃС‚СѓРїРЅС‹\n"

        # Р”РѕР±Р°РІР»СЏРµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ ZFS
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('zfs_monitor'):
                zfs_summary, zfs_has_issues = self.get_zfs_summary_for_report()
                zfs_header_icon = "рџ”ґ" if zfs_has_issues else "рџџў"
                message += f"\n{zfs_header_icon} *РЎС‚Р°С‚СѓСЃС‹ ZFS (РїРѕСЃР»РµРґРЅРёРµ)*\n"
                message += zfs_summary
        except Exception as e:
            debug_log(f"вљ пёЏ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РґР°РЅРЅС‹С… Рѕ ZFS: {e}")
            message += "\nрџ§Љ *РЎС‚Р°С‚СѓСЃС‹ ZFS:* РґР°РЅРЅС‹Рµ РЅРµРґРѕСЃС‚СѓРїРЅС‹\n"
            
        message += f"\nвЏ° *РћС‚С‡С‘С‚ СЃС„РѕСЂРјРёСЂРѕРІР°РЅ:* {collection_time.strftime('%H:%M:%S')}"
        return message

    def force_report(self):
        """Р¤РѕСЂРјРёСЂСѓРµС‚ РѕС‚С‡РµС‚ РґР»СЏ СЂСѓС‡РЅРѕРіРѕ Р·Р°РїСЂРѕСЃР° Рё РІРѕР·РІСЂР°С‰Р°РµС‚ С‚РµРєСЃС‚"""
        data_collected = self.collect_morning_data(manual_call=True)
        if not data_collected:
            return "вќЊ РћС€РёР±РєР° СЃР±РѕСЂР° РґР°РЅРЅС‹С… РґР»СЏ РѕС‚С‡РµС‚Р°"

        return self.generate_report_message()
    
    def get_backup_summary_for_report(
        self,
        period_hours=16,
        include_proxmox=True,
        include_databases=True,
        include_mail=False,
        unavailable_hosts=None,
    ):
        """РџРѕР»СѓС‡Р°РµС‚ СЃРІРѕРґРєСѓ РїРѕ Р±СЌРєР°РїР°Рј"""
        try:
            # РРјРїРѕСЂС‚ С„СѓРЅРєС†РёР№ Р±СЌРєР°РїРѕРІ
            from extensions.backup_monitor.backup_utils import get_backup_summary
            return get_backup_summary(
                period_hours,
                include_proxmox=include_proxmox,
                include_databases=include_databases,
                include_mail=include_mail,
                unavailable_hosts=unavailable_hosts,
            )
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЃРІРѕРґРєРё РїРѕ Р±СЌРєР°РїР°Рј: {e}")
            return "вќЊ Р”Р°РЅРЅС‹Рµ Рѕ Р±СЌРєР°РїР°С… РЅРµРґРѕСЃС‚СѓРїРЅС‹", True

    def get_zfs_summary_for_report(self):
        """РџРѕР»СѓС‡Р°РµС‚ СЃРІРѕРґРєСѓ РїРѕ ZFS"""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from core.config_manager import config_manager as settings_manager

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return "вќЊ Р‘Р°Р·Р° Р±СЌРєР°РїРѕРІ РЅРµ РЅР°СЃС‚СЂРѕРµРЅР°\n", True

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
                    return "вќЊ РўР°Р±Р»РёС†Р° ZFS РµС‰С‘ РЅРµ СЃРѕР·РґР°РЅР°.\n", True
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
                    f"вЂў РЎРµСЂРІРµСЂРѕРІ: {servers_total} (рџџў {servers_ok} / рџ”ґ {servers_problem})\n"
                    "вЂў РџСѓР»РѕРІ: 0 (рџџў 0 / рџ”ґ 0)\n"
                )
                return summary, True
            if not rows:
                return "вЂў Р”Р°РЅРЅС‹С… РЅРµС‚\n", False

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
                f"вЂў РЎРµСЂРІРµСЂРѕРІ: {servers_count} (рџџў {servers_ok} / рџ”ґ {servers_problem})\n"
                f"вЂў РџСѓР»РѕРІ: {total_pools} (рџџў {ok_pools} / рџ”ґ {bad_pools})\n"
            )

            has_issues = servers_problem > 0 or bad_pools > 0 or bool(stale_servers)
            return summary, has_issues
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЃРІРѕРґРєРё ZFS: {e}")
            return "вќЊ Р”Р°РЅРЅС‹Рµ ZFS РЅРµРґРѕСЃС‚СѓРїРЅС‹\n", True
    
    def send_report(self, manual_call=False):
        """РћС‚РїСЂР°РІРєР° РѕС‚С‡РµС‚Р°"""
        try:
            # РЎРѕР±РёСЂР°РµРј РґР°РЅРЅС‹Рµ
            self.collect_morning_data(manual_call)
            
            # Р“РµРЅРµСЂРёСЂСѓРµРј СЃРѕРѕР±С‰РµРЅРёРµ
            message = self.generate_report_message()
            
            # РћС‚РїСЂР°РІР»СЏРµРј С‡РµСЂРµР· РѕР±СЂР°Р±РѕС‚С‡РёРє
            from bot.handlers.commands import send_alert
            send_alert(message, force=True)
            
            debug_log(f"вњ… РћС‚С‡РµС‚ РѕС‚РїСЂР°РІР»РµРЅ ({'СЂСѓС‡РЅРѕР№' if manual_call else 'Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№'})")
            return True
        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё РѕС‚С‡РµС‚Р°: {e}")
            return False
    
    def start_scheduler(self):
        """Р—Р°РїСѓСЃРє РїР»Р°РЅРёСЂРѕРІС‰РёРєР° РѕС‚С‡РµС‚РѕРІ"""
        debug_log("вЏ° Р—Р°РїСѓСЃРє РїР»Р°РЅРёСЂРѕРІС‰РёРєР° СѓС‚СЂРµРЅРЅРёС… РѕС‚С‡РµС‚РѕРІ")
        
        while True:
            current_time = datetime.now()
            current_time_time = current_time.time()
            
            # РџСЂРѕРІРµСЂСЏРµРј РІСЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С…
            if (current_time_time.hour == DATA_COLLECTION_TIME.hour and
                current_time_time.minute == DATA_COLLECTION_TIME.minute):
                
                # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЃРµРіРѕРґРЅСЏ РµС‰Рµ РЅРµ РѕС‚РїСЂР°РІР»СЏР»Рё РѕС‚С‡РµС‚
                today = current_time.date()
                if self.last_report_date != today:
                    debug_log(f"рџ“Љ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЃР±РѕСЂ РґР°РЅРЅС‹С… РґР»СЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°")
                    self.send_report(manual_call=False)
                    self.last_report_date = today
                    
                    # Р—Р°РґРµСЂР¶РєР° С‡С‚РѕР±С‹ РЅРµ Р·Р°РїСѓСЃРєР°С‚СЊ РїРѕРІС‚РѕСЂРЅРѕ РІ С‚Сѓ Р¶Рµ РјРёРЅСѓС‚Сѓ
                    time.sleep(65)
                else:
                    debug_log(f"вЏ­пёЏ РћС‚С‡РµС‚ СѓР¶Рµ РѕС‚РїСЂР°РІР»РµРЅ СЃРµРіРѕРґРЅСЏ {self.last_report_date}")
            
            time.sleep(60)  # РџСЂРѕРІРµСЂСЏРµРј РєР°Р¶РґСѓСЋ РјРёРЅСѓС‚Сѓ

# Р“Р»РѕР±Р°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РѕС‚С‡РµС‚Р°
morning_report = MorningReport()
