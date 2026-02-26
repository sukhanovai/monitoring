"""
/extensions/backup_monitor/bot_handler.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring Proxmox backups
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
import traceback
from .settings_backup_monitor import BASE_DIR, DATA_DIR
from config.settings import BOT_DEBUG_LOG_FILE
from lib.logging import debug_log, setup_logging
from extensions.backup_monitor.backup_handlers import (
    show_main_menu,
    show_proxmox_menu,
    show_today_status,
    show_recent_backups,
    show_failed_backups,
    show_hosts_menu,
    show_host_status,
    show_stale_hosts,
    show_database_backups_menu,
    show_database_backups_summary,
    show_database_details,
    show_stale_databases,
    show_mail_backups,
    show_stock_loads,
)
from extensions.extension_manager import extension_manager

def register_handlers(dispatcher):
    """
    Р РµРіРёСЃС‚СЂРёСЂСѓРµС‚ handlers СЂР°СЃС€РёСЂРµРЅРёСЏ backup_monitor.
    Р•СЃР»Рё РєРѕРјР°РЅРґС‹ СѓР¶Рµ РіРґРµ-С‚Рѕ СЂРµРіРёСЃС‚СЂРёСЂСѓСЋС‚СЃСЏ вЂ” РјРѕР¶РЅРѕ РѕСЃС‚Р°РІРёС‚СЊ РїСѓСЃС‚С‹Рј.
    """
    try:
        # РµСЃР»Рё Сѓ СЂР°СЃС€РёСЂРµРЅРёСЏ РµСЃС‚СЊ РєРѕРјР°РЅРґС‹ РІРёРґР° /backup
        # dispatcher.add_handler(CommandHandler("backup", backup_command))
        # dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
        # dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))

        # Р•СЃР»Рё С…РѕС‡РµС€СЊ, С‡С‚РѕР±С‹ СЂР°СЃС€РёСЂРµРЅРёРµ СЃР°РјРѕ Р»РѕРІРёР»Рѕ СЃРІРѕРё callback_data:
        # dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern=r"^backup_"))

        debug_log("вњ… backup_monitor: handlers Р·Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°РЅС‹")
    except Exception as e:
        debug_log(f"вќЊ backup_monitor: РѕС€РёР±РєР° СЂРµРіРёСЃС‚СЂР°С†РёРё handlers: {e}")

# РќР°СЃС‚СЂРѕР№РєР° Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
logger = setup_logging("backup_monitor_bot", level="DEBUG", log_file=BOT_DEBUG_LOG_FILE)

# РРјРїРѕСЂС‚РёСЂСѓРµРј РЅР°С€Рё СѓС‚РёР»РёС‚С‹ Рё РѕР±СЂР°Р±РѕС‚С‡РёРєРё
try:
    from .backup_utils import BackupBase, StatusCalculator, DisplayFormatters
    from .backup_handlers import (
        create_main_menu, create_navigation_buttons,
        show_main_menu, show_today_status, show_recent_backups, show_failed_backups,
        show_hosts_menu, show_stale_hosts, show_host_status,
        show_database_backups_menu, show_stale_databases,
        show_database_backups_summary, show_database_details,
        show_stock_loads,
        format_database_details
    )
    logger.info("вњ… РњРѕРґСѓР»Рё backup_utils Рё backup_handlers СѓСЃРїРµС€РЅРѕ РёРјРїРѕСЂС‚РёСЂРѕРІР°РЅС‹")
except ImportError as e:
    logger.error(f"вќЊ РћС€РёР±РєР° РёРјРїРѕСЂС‚Р° РјРѕРґСѓР»РµР№: {e}")
    # РђР»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РёРјРїРѕСЂС‚ РґР»СЏ СЃР»СѓС‡Р°РµРІ, РєРѕРіРґР° РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅС‹Рµ РёРјРїРѕСЂС‚С‹ РЅРµ СЂР°Р±РѕС‚Р°СЋС‚
    try:
        import sys
        sys.path.append(str(Path(BASE_DIR) / 'extensions' / 'backup_monitor'))
        from .backup_utils import BackupBase, StatusCalculator, DisplayFormatters
        from .backup_handlers import (
            create_main_menu, create_navigation_buttons,
            show_main_menu, show_today_status, show_recent_backups, show_failed_backups,
            show_hosts_menu, show_stale_hosts, show_host_status,
            show_database_backups_menu, show_stale_databases,
            show_database_backups_summary, show_database_details,
            show_stock_loads,
            format_database_details
        )
        logger.info("вњ… РњРѕРґСѓР»Рё РёРјРїРѕСЂС‚РёСЂРѕРІР°РЅС‹ С‡РµСЂРµР· Р°Р±СЃРѕР»СЋС‚РЅС‹Р№ РїСѓС‚СЊ")
    except ImportError as e2:
        logger.error(f"вќЊ РљСЂРёС‚РёС‡РµСЃРєР°СЏ РѕС€РёР±РєР° РёРјРїРѕСЂС‚Р°: {e2}")
        raise

class BackupMonitorBot(BackupBase):
    """РћРїС‚РёРјРёР·РёСЂРѕРІР°РЅРЅС‹Р№ РєР»Р°СЃСЃ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ"""
    
    def __init__(self):
        from .db_settings_backup_monitor import BACKUP_DATABASE_CONFIG
        super().__init__(BACKUP_DATABASE_CONFIG['backups_db'])
        self.status_calc = StatusCalculator()
        self.formatters = DisplayFormatters()
        self.backup_alert_hours, self.backup_stale_hours = self._get_backup_thresholds()

    @staticmethod
    def _get_backup_thresholds():
        """РџРѕР»СѓС‡Р°РµС‚ РїРѕСЂРѕРіРё СЃРІРµР¶РµСЃС‚Рё Р±СЌРєР°РїРѕРІ РёР· РЅР°СЃС‚СЂРѕРµРє."""
        default_alert = 24
        default_stale = 36
        try:
            from core.config_manager import config_manager

            alert_hours = config_manager.get_setting("BACKUP_ALERT_HOURS", default_alert)
            stale_hours = config_manager.get_setting("BACKUP_STALE_HOURS", default_stale)
        except Exception:
            alert_hours = default_alert
            stale_hours = default_stale

        try:
            alert_hours = int(alert_hours)
        except (TypeError, ValueError):
            alert_hours = default_alert

        try:
            stale_hours = int(stale_hours)
        except (TypeError, ValueError):
            stale_hours = default_stale

        if stale_hours <= alert_hours:
            stale_hours = alert_hours + 1

        return alert_hours, stale_hours

    # === Р‘РђР—РћР’Р«Р• РњР•РўРћР”Р« ===
    
    def get_database_display_names(self) -> dict:
        """
        Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕС‚РѕР±СЂР°Р¶Р°РµРјС‹Рµ РёРјРµРЅР° Р‘Р” (РєР»СЋС‡ -> display name),
        Р±РµСЂС‘Рј РёР· SETTINGS.DB: settings.key='DATABASE_CONFIG'
        Р¤РѕСЂРјР°С‚ DATABASE_CONFIG: {category: {db_key: db_display_name, ...}, ...}
        """
        try:
            import json
            import sqlite3

            db_path = Path(DATA_DIR) / "settings.db"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key='DATABASE_CONFIG' LIMIT 1")
            row = cur.fetchone()
            conn.close()

            if not row or not row[0]:
                return {}

            raw = row[0]
            cfg = json.loads(raw) if isinstance(raw, str) else (raw or {})
            if not isinstance(cfg, dict):
                return {}

            # РЎРѕР±РёСЂР°РµРј РІ РїР»РѕСЃРєРёР№ СЃР»РѕРІР°СЂСЊ: db_key -> display_name
            names = {}
            for _category, db_map in cfg.items():
                if not isinstance(db_map, dict):
                    continue
                for db_key, display_name in db_map.items():
                    # display_name РјРѕР¶РµС‚ Р±С‹С‚СЊ None/"" вЂ” РїРѕРґСЃС‚СЂР°С…СѓРµРјСЃСЏ
                    names[str(db_key)] = str(display_name) if display_name else str(db_key)

            return names

        except Exception as e:
            logger.exception(f"get_database_display_names: failed: {e}")
            return {}

    # === РњР•РўРћР”Р« Р”Р›РЇ РҐРћРЎРўРћР’ ===
    
    def get_today_status(self):
        """РЎС‚Р°С‚СѓСЃ Р±СЌРєР°РїРѕРІ Р·Р° СЃРµРіРѕРґРЅСЏ"""
        today = datetime.now().strftime('%Y-%m-%d')
        query = '''
            SELECT host_name, backup_status, COUNT(*) as report_count, MAX(received_at) as last_report
            FROM proxmox_backups
            WHERE date(received_at) = ?
            GROUP BY host_name, backup_status
            ORDER BY host_name, last_report DESC
        '''
        return self.execute_query(query, (today,))

    def get_recent_backups(self, hours=24):
        """РџРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹ Р·Р° СѓРєР°Р·Р°РЅРЅС‹Р№ РїРµСЂРёРѕРґ"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT host_name, backup_status, duration, total_size, error_message, received_at
            FROM proxmox_backups
            WHERE received_at >= ?
            ORDER BY received_at DESC
            LIMIT 15
        '''
        return self.execute_query(query, (since_time,))

    def get_host_status(self, host_name):
        """РЎС‚Р°С‚СѓСЃ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ С…РѕСЃС‚Р°"""
        query = '''
            SELECT backup_status, duration, total_size, error_message, received_at
            FROM proxmox_backups
            WHERE host_name = ?
            ORDER BY received_at DESC
            LIMIT 5
        '''
        return self.execute_query(query, (host_name,))

    def get_failed_backups(self, days=1):
        """РќРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ Р·Р° РїРµСЂРёРѕРґ"""
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
            SELECT host_name, backup_status, error_message, received_at
            FROM proxmox_backups
            WHERE backup_status = 'failed'
            AND date(received_at) >= ?
            ORDER BY received_at DESC
        '''
        return self.execute_query(query, (since_date,))

    def get_all_hosts(self):
        """РџРѕР»СѓС‡Р°РµС‚ СЃРїРёСЃРѕРє РІСЃРµС… С…РѕСЃС‚РѕРІ РёР· Р±Р°Р·С‹"""
        query = 'SELECT DISTINCT host_name FROM proxmox_backups ORDER BY host_name'
        results = self.execute_query(query)
        db_hosts = [row[0] for row in results]

        try:
            from .db_settings_backup_monitor import PROXMOX_HOSTS
        except Exception:
            PROXMOX_HOSTS = {}

        if not isinstance(PROXMOX_HOSTS, dict):
            return db_hosts

        enabled_hosts = {
            host for host, value in PROXMOX_HOSTS.items()
            if not isinstance(value, dict) or value.get("enabled", True)
        }

        filtered_hosts = [host for host in db_hosts if host in enabled_hosts]
        return filtered_hosts or list(enabled_hosts)

    def get_host_recent_status(self, host_name, hours=48):
        """РџРѕР»СѓС‡Р°РµС‚ СЃС‚Р°С‚СѓСЃ С…РѕСЃС‚Р° Р·Р° СѓРєР°Р·Р°РЅРЅС‹Р№ РїРµСЂРёРѕРґ"""
        query = '''
            SELECT backup_status, received_at
            FROM proxmox_backups
            WHERE host_name = ?
        '''
        params = [host_name]
        if hours is not None:
            since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            query += " AND received_at >= ?"
            params.append(since_time)
        query += " ORDER BY received_at DESC"
        return self.execute_query(query, tuple(params))

    def get_host_display_status(self, host_name):
        """РћРїСЂРµРґРµР»СЏРµС‚ РѕС‚РѕР±СЂР°Р¶Р°РµРјС‹Р№ СЃС‚Р°С‚СѓСЃ С…РѕСЃС‚Р°"""
        recent_backups = self.get_host_recent_status(host_name, None)
        return self.status_calc.calculate_host_status(
            recent_backups,
            alert_hours=self.backup_alert_hours,
            stale_hours=self.backup_stale_hours,
        )

    # === РњР•РўРћР”Р« Р”Р›РЇ Р‘РђР— Р”РђРќРќР«РҐ ===
    
    def get_database_backups_stats(self, hours=24):
        """РџРѕР»СѓС‡Р°РµС‚ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РїРѕ Р±СЌРєР°РїР°Рј Р±Р°Р· РґР°РЅРЅС‹С…"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_type, database_name, database_display_name, 
                   backup_status, COUNT(*) as backup_count, MAX(received_at) as last_backup
            FROM database_backups 
            WHERE received_at >= ?
            GROUP BY backup_type, database_name, database_display_name, backup_status
            ORDER BY backup_type, database_name, last_backup DESC
        '''
        return self.execute_query(query, (since_time,))

    def get_database_backups_stats_fixed(self, hours=24):
        """РСЃРїСЂР°РІР»РµРЅРЅР°СЏ РІРµСЂСЃРёСЏ РїРѕР»СѓС‡РµРЅРёСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё"""
        return self.get_database_backups_stats(hours)

    def get_database_details(self, backup_type, db_name, hours=168):
        """РџРѕР»СѓС‡Р°РµС‚ РґРµС‚Р°Р»СЊРЅСѓСЋ РёРЅС„РѕСЂРјР°С†РёСЋ РїРѕ РєРѕРЅРєСЂРµС‚РЅРѕР№ Р±Р°Р·Рµ РґР°РЅРЅС‹С…"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, task_type, error_count, email_subject, received_at
            FROM database_backups 
            WHERE backup_type = ? AND database_name = ? AND received_at >= ?
            ORDER BY received_at DESC
            LIMIT 10
        '''
        return self.execute_query(query, (backup_type, db_name, since_time))

    def get_database_recent_status(self, backup_type, db_name, hours=48):
        """РџРѕР»СѓС‡Р°РµС‚ СЃС‚Р°С‚СѓСЃ Р‘Р” Р·Р° СѓРєР°Р·Р°РЅРЅС‹Р№ РїРµСЂРёРѕРґ"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, received_at, error_count
            FROM database_backups
            WHERE backup_type = ? AND database_name = ? AND received_at >= ?
            ORDER BY received_at DESC
        '''
        return self.execute_query(query, (backup_type, db_name, since_time))

    def get_database_display_status(self, backup_type, db_name):
        """РћРїСЂРµРґРµР»СЏРµС‚ РѕС‚РѕР±СЂР°Р¶Р°РµРјС‹Р№ СЃС‚Р°С‚СѓСЃ Р‘Р”"""
        recent_backups = self.get_database_recent_status(backup_type, db_name, 48)
        return self.status_calc.calculate_db_status(recent_backups)

    # === РњР•РўРћР”Р« Р”Р›РЇ РџРћР§РўРћР’Р«РҐ Р‘Р­РљРђРџРћР’ ===

    def get_mail_backups(self, hours=72, limit=10):
        """РџРѕР»СѓС‡Р°РµС‚ РїРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, total_size, backup_path, received_at
            FROM mail_server_backups
            WHERE received_at >= ?
            ORDER BY received_at DESC
            LIMIT ?
        '''
        try:
            return self.execute_query(query, (since_time, limit))
        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РїРѕС‡С‚РѕРІС‹С… Р±СЌРєР°РїРѕРІ: {exc}")
            return []

    # === РњР•РўРћР”Р« Р”Р›РЇ Р—РђР“Р РЈР—РљР РћРЎРўРђРўРљРћР’ ===

    def get_stock_loads(self, hours=24):
        """РџРѕР»СѓС‡Р°РµС‚ РїРѕСЃР»РµРґРЅРёРµ СЂРµР·СѓР»СЊС‚Р°С‚С‹ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ С‚РѕРІР°СЂРѕРІ РїРѕ РєР°Р¶РґРѕРјСѓ РїРѕСЃС‚Р°РІС‰РёРєСѓ."""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            WITH normalized AS (
                SELECT
                    id,
                    COALESCE(source_name, 'РћСЃРЅРѕРІРЅРѕРµ РїСЂРµРґРїСЂРёСЏС‚РёРµ') AS source_name,
                    CASE
                        WHEN supplier_name IS NULL OR supplier_name = 'РЅРµРёР·РІРµСЃС‚РЅРѕ'
                            THEN COALESCE(source_name, 'РћСЃРЅРѕРІРЅРѕРµ РїСЂРµРґРїСЂРёСЏС‚РёРµ')
                        ELSE supplier_name
                    END AS supplier_name,
                    status,
                    rows_count,
                    error_sample,
                    received_at
                FROM stock_load_results
                WHERE received_at >= ?
            ),
            ranked AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY source_name, supplier_name
                        ORDER BY received_at DESC, id DESC
                    ) AS row_num
                FROM normalized
            )
            SELECT source_name, supplier_name, status, rows_count, error_sample, received_at
            FROM ranked
            WHERE row_num = 1
            ORDER BY source_name, supplier_name
        '''
        try:
            return self.execute_query(query, (since_time,))
        except Exception as exc:
            logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РѕСЃС‚Р°С‚РєРѕРІ: {exc}")
            return []

    # === РњР•РўРћР”Р« Р”Р›РЇ РћРўР§Р•РўРћР’ ===
    
    def get_stale_proxmox_backups(self, hours_threshold=24):
        """РџРѕР»СѓС‡Р°РµС‚ С…РѕСЃС‚С‹ Р±РµР· СЃРІРµР¶РёС… Р±СЌРєР°РїРѕРІ"""
        threshold_time = (datetime.now() - timedelta(hours=hours_threshold)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT host_name, MAX(received_at) as last_backup
            FROM proxmox_backups 
            GROUP BY host_name
            HAVING last_backup < ?
            ORDER BY last_backup ASC
        '''
        return self.execute_query(query, (threshold_time,))

    def get_stale_database_backups(self, hours_threshold=24):
        """РџРѕР»СѓС‡Р°РµС‚ Р‘Р” Р±РµР· СЃРІРµР¶РёС… Р±СЌРєР°РїРѕРІ"""
        threshold_time = (datetime.now() - timedelta(hours=hours_threshold)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_type, database_name, database_display_name, MAX(received_at) as last_backup
            FROM database_backups 
            GROUP BY backup_type, database_name, database_display_name
            HAVING last_backup < ?
            ORDER BY last_backup ASC
        '''
        return self.execute_query(query, (threshold_time,))

    def get_backup_coverage_report(self, hours_threshold=24):
        """РџРѕР»СѓС‡Р°РµС‚ РїРѕР»РЅС‹Р№ РѕС‚С‡РµС‚ Рѕ РїРѕРєСЂС‹С‚РёРё Р±СЌРєР°РїРѕРІ"""
        stale_hosts = self.get_stale_proxmox_backups(hours_threshold)
        stale_databases = self.get_stale_database_backups(hours_threshold)
        
        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ РёР·РІРµСЃС‚РЅС‹Рµ С…РѕСЃС‚С‹ Рё Р‘Р” РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё
        from .db_settings_backup_monitor import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG
        
        all_configured_hosts = [
            host for host, value in PROXMOX_HOSTS.items()
            if not isinstance(value, dict) or value.get("enabled", True)
        ]
        all_configured_databases = []
        
        # РЎРѕР±РёСЂР°РµРј РІСЃРµ Р‘Р” РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё
        config_mapping = [
            ('company_database', DATABASE_BACKUP_CONFIG["company_databases"]),
            ('barnaul', DATABASE_BACKUP_CONFIG["barnaul_backups"]),
            ('client', DATABASE_BACKUP_CONFIG["client_databases"]), 
            ('yandex', DATABASE_BACKUP_CONFIG["yandex_backups"])
        ]
        
        for backup_type, config_dict in config_mapping:
            for db_key in config_dict.keys():
                all_configured_databases.append((backup_type, db_key))
        
        return {
            'stale_hosts': stale_hosts,
            'stale_databases': stale_databases,
            'all_configured_hosts': all_configured_hosts,
            'all_configured_databases': all_configured_databases,
            'hours_threshold': hours_threshold
        }

# === РљРћРњРђРќР”Р« Р‘РћРўРђ ===

def backup_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /backup"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text(
                "вќЊ Р¤СѓРЅРєС†РёРѕРЅР°Р» РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡РµРЅ. "
                "Р’РєР»СЋС‡РёС‚Рµ СЂР°СЃС€РёСЂРµРЅРёРµ 'рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox' РІ СЂР°Р·РґРµР»Рµ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё."
            )
            return

        update.message.reply_text(
            "рџ’ѕ *РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox*\n\nР’С‹Р±РµСЂРёС‚Рµ РѕРїС†РёСЋ:",
            parse_mode='Markdown',
            reply_markup=create_main_menu()
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ backup_command: {e}")
        update.message.reply_text("вќЊ РћС€РёР±РєР° РїСЂРё РІС‹РїРѕР»РЅРµРЅРёРё РєРѕРјР°РЅРґС‹")

def backup_search_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /backup_search"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text("вќЊ Р¤СѓРЅРєС†РёРѕРЅР°Р» РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡РµРЅ.")
            return

        update.message.reply_text("рџ”Ќ РџРѕРёСЃРє РїРѕ Р±СЌРєР°РїР°Рј РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ...")

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ backup_search_command: {e}")
        update.message.reply_text("вќЊ РћС€РёР±РєР° РїСЂРё РІС‹РїРѕР»РЅРµРЅРёРё РєРѕРјР°РЅРґС‹")

def backup_help_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /backup_help"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text("вќЊ Р¤СѓРЅРєС†РёРѕРЅР°Р» РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡РµРЅ.")
            return

        help_text = (
            "рџ’ѕ *РџРѕРјРѕС‰СЊ РїРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіСѓ Р±СЌРєР°РїРѕРІ*\n\n"
            "*РљРѕРјР°РЅРґС‹:*\n"
            "вЂў `/backup` - Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ Р±СЌРєР°РїРѕРІ\n"
            "вЂў `/backup_search` - РџРѕРёСЃРє РїРѕ Р±СЌРєР°РїР°Рј\n"
            "вЂў `/backup_help` - Р­С‚Р° СЃРїСЂР°РІРєР°\n\n"
            "*РћРїС†РёРё РІ РјРµРЅСЋ:*\n"
            "вЂў рџ“Љ РЎРµРіРѕРґРЅСЏ - РЎС‚Р°С‚СѓСЃ Р·Р° СЃРµРіРѕРґРЅСЏ\n"
            "вЂў вЏ° 24 С‡Р°СЃР° - РџРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹\n"
            "вЂў вќЊ РћС€РёР±РєРё - РќРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹\n"
            "вЂў рџ–ҐпёЏ РџРѕ С…РѕСЃС‚Р°Рј - РЎС‚Р°С‚СѓСЃ РїРѕ СЃРµСЂРІРµСЂР°Рј\n"
            "вЂў рџ—ѓпёЏ Р‘СЌРєР°РїС‹ Р‘Р” - Р‘СЌРєР°РїС‹ Р±Р°Р· РґР°РЅРЅС‹С…\n"
            "вЂў рџ“¬ Р‘СЌРєР°РїС‹ РїРѕС‡С‚С‹ - Р‘СЌРєР°РїС‹ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°\n"
            "вЂў рџ“¦ РћСЃС‚Р°С‚РєРё 1РЎ - Р РµР·СѓР»СЊС‚Р°С‚С‹ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ\n"
            "вЂў рџ”„ РћР±РЅРѕРІРёС‚СЊ - РћР±РЅРѕРІРёС‚СЊ РґР°РЅРЅС‹Рµ\n\n"
            "*Р”Р°РЅРЅС‹Рµ РѕР±РЅРѕРІР»СЏСЋС‚СЃСЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РїРёСЃРµРј РѕС‚ Proxmox/РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°*"
        )

        update.message.reply_text(help_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ backup_help_command: {e}")
        update.message.reply_text("вќЊ РћС€РёР±РєР° РїСЂРё РІС‹РїРѕР»РЅРµРЅРёРё РєРѕРјР°РЅРґС‹")

# === CALLBACK РћР‘Р РђР‘РћРўР§РРљР ===

def backup_callback(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє callback'РѕРІ РґР»СЏ Р±СЌРєР°РїРѕРІ"""
    query = update.callback_query
    data = query.data
    logger.info(
        f"рџ§© backup_callback: START | file={__file__} | data={data}"
    )

    try:
        # Р’РђР–РќРћ: РІСЃРµ Р»РѕРіРё вЂ” РІРЅСѓС‚СЂРё try
        debug_log(f"рџ§© backup_callback: START | file={__file__} | data={data}")

        if not query:
            debug_log("вќЊ backup_callback: update.callback_query is None")
            return

        query.answer()

        data = query.data
        backup_bot = BackupMonitorBot()

        if data == 'no_action':
            return

        if data == 'backup_today':
            show_today_status(query, backup_bot)

        elif data == 'backup_24h':
            show_recent_backups(query, backup_bot)

        elif data == 'backup_failed':
            show_failed_backups(query, backup_bot)

        elif data == 'backup_hosts':
            if not extension_manager.is_extension_enabled('backup_monitor'):
                query.edit_message_text("рџ–ҐпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox РѕС‚РєР»СЋС‡С‘РЅ")
                return
            show_hosts_menu(query, backup_bot)

        elif data == 'backup_refresh':
            show_main_menu(query, backup_bot)

        elif data == 'backup_databases':
            if not extension_manager.is_extension_enabled('database_backup_monitor'):
                query.edit_message_text("рџ—ѓпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Р‘Р” РѕС‚РєР»СЋС‡С‘РЅ")
                return
            logger.info("рџ§Є BACKUP DB: entering show_database_backups_menu")
            show_database_backups_menu(query, backup_bot)

        elif data == 'backup_mail':
            if not extension_manager.is_extension_enabled('mail_backup_monitor'):
                query.edit_message_text("рџ“¬ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹ РѕС‚РєР»СЋС‡С‘РЅ")
                return
            show_mail_backups(query, backup_bot)

        elif data == 'backup_stock_loads':
            if not extension_manager.is_extension_enabled('stock_load_monitor'):
                query.edit_message_text("рџ“¦ РњРѕРЅРёС‚РѕСЂРёРЅРі РѕСЃС‚Р°С‚РєРѕРІ 1РЎ РѕС‚РєР»СЋС‡С‘РЅ")
                return
            show_stock_loads(query, backup_bot)

        elif data == 'backup_proxmox':
            show_proxmox_menu(query, backup_bot)

        elif data == 'backup_stale_hosts':
            show_stale_hosts(query, backup_bot)

        elif data.startswith('backup_host_'):
            host_name = data.replace('backup_host_', '')
            show_host_status(query, backup_bot, host_name)

        elif data == 'backup_main':
            show_main_menu(query, backup_bot)

        # --- DB handlers ---
        elif data.startswith('db_detail_'):
            remaining = data.replace('db_detail_', '')
            if '__' in remaining:
                backup_type, db_name = remaining.split('__', 1)
                logger.info("рџ§Є DB detail")
                show_database_details(query, backup_bot, backup_type, db_name)
            else:
                last_underscore = remaining.rfind('_')
                if last_underscore != -1:
                    backup_type = remaining[:last_underscore]
                    db_name = remaining[last_underscore + 1:]
                    show_database_details(query, backup_bot, backup_type, db_name)
                else:
                    query.edit_message_text("вќЊ РћС€РёР±РєР°: РЅРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ Р·Р°РїСЂРѕСЃР°")

        elif data == 'db_backups_24h':
            logger.info("рџ§Є db backups 24h")
            show_database_backups_summary(query, backup_bot, 24)

        elif data == 'db_backups_48h':
            logger.info("рџ§Є db backups 48h")
            show_database_backups_summary(query, backup_bot, 48)

        elif data in ('db_backups_today', 'db_backups_summary'):
            logger.info("рџ§Є db backups today")
            show_database_backups_summary(query, backup_bot, 24)

        elif data == 'db_backups_list':
            logger.info("рџ§Є db backups list")
            show_database_backups_menu(query, backup_bot)

        elif data == 'db_stale_list':
            logger.info("рџ§Є db state list")
            show_stale_databases(query, backup_bot)

        else:
            debug_log(f"вљ пёЏ backup_callback: unknown callback data={data}")
            query.answer("РќРµРёР·РІРµСЃС‚РЅР°СЏ РєРѕРјР°РЅРґР°", show_alert=True)

    except Exception as e:
        debug_log(f"рџ’Ґ backup_callback ERROR: {e}\n{traceback.format_exc()}")
        try:
            query.edit_message_text("вќЊ РћС€РёР±РєР° РІ РјРѕРґСѓР»Рµ Р±СЌРєР°РїРѕРІ. РџРѕРґСЂРѕР±РЅРѕСЃС‚Рё РІ Р»РѕРіР°С….")
        except Exception:
            try:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="вќЊ РћС€РёР±РєР° РІ РјРѕРґСѓР»Рµ Р±СЌРєР°РїРѕРІ (РЅРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ РјРµРЅСЋ). РџРѕРґСЂРѕР±РЅРѕСЃС‚Рё РІ Р»РѕРіР°С…."
                )
            except Exception:
                pass

def get_database_config(self):
    """РџРѕР»СѓС‡Р°РµС‚ РїРѕР»РЅСѓСЋ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ Р±Р°Р· РґР°РЅРЅС‹С…"""
    from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG
    
    return {
        "company_databases": DATABASE_BACKUP_CONFIG.get("company_databases", {}),
        "barnaul_backups": DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
        "client_databases": DATABASE_BACKUP_CONFIG.get("client_databases", {}),
        "yandex_backups": DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
    }

def get_database_config_for_report(self):
    """РџРѕР»СѓС‡Р°РµС‚ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ Р±Р°Р· РґР°РЅРЅС‹С… РґР»СЏ РѕС‚С‡РµС‚Р°"""
    from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG
    
    # РЎРѕР±РёСЂР°РµРј РІСЃРµ Р±Р°Р·С‹ РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё
    all_databases = {}
    all_databases.update(DATABASE_BACKUP_CONFIG.get("company_databases", {}))
    all_databases.update(DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}))
    all_databases.update(DATABASE_BACKUP_CONFIG.get("client_databases", {}))
    all_databases.update(DATABASE_BACKUP_CONFIG.get("yandex_backups", {}))
    
    return all_databases

# === РќРђРЎРўР РћР™РљРђ РћР‘Р РђР‘РћРўР§РРљРћР’ ===

def setup_backup_handlers(dispatcher):
    """РќР°СЃС‚СЂР°РёРІР°РµС‚ РѕР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ Р±СЌРєР°РїРѕРІ"""
    dispatcher.add_handler(CommandHandler("backup", backup_command))
    dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
    dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^backup_'))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^db_'))
