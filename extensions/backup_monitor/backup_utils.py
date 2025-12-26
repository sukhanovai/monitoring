"""
/extensions/backup_monitor/backup_utils.py
Server Monitoring System v4.20.7
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utilities for working with backups
Система мониторинга серверов
Версия: 4.20.7
Автор: Александр Суханов (c)
Лицензия: MIT
Утилиты для работы с бэкапами
"""

import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_backup_summary(period_hours=16):
    """Возвращает текстовую сводку по бэкапам за период."""
    try:
        from config.db_settings import DATA_DIR, DATABASE_BACKUP_CONFIG, PROXMOX_HOSTS

        db_path = DATA_DIR / "backups.db"
        if not db_path.exists():
            logger.error("База данных бэкапов недоступна: %s", db_path)
            return "❌ База данных бэкапов недоступна\n"

        since_time = (datetime.now() - timedelta(hours=period_hours)).strftime('%Y-%m-%d %H:%M:%S')
        stale_threshold = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT host_name
            FROM proxmox_backups
            WHERE received_at >= datetime('now', '-30 days')
            ORDER BY host_name
        ''')
        all_hosts = [row[0] for row in cursor.fetchall()]
        if PROXMOX_HOSTS:
            configured_hosts = set(PROXMOX_HOSTS.keys())
            all_hosts = [host for host in all_hosts if host in configured_hosts]

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

        cursor.execute('''
            SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
            FROM database_backups
            WHERE received_at >= ?
            GROUP BY backup_type, database_name
        ''', (since_time,))
        db_results = cursor.fetchall()

        cursor.execute('''
            SELECT backup_type, database_name, MAX(received_at) as last_backup
            FROM database_backups
            GROUP BY backup_type, database_name
            HAVING last_backup < ?
        ''', (stale_threshold,))
        stale_databases = cursor.fetchall()

        conn.close()

        hosts_with_success = len([r for r in proxmox_results if r[1] == 'success'])

        config_databases = {
            'company_database': DATABASE_BACKUP_CONFIG.get("company_databases", {}),
            'barnaul': DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
            'client': DATABASE_BACKUP_CONFIG.get("client_databases", {}),
            'yandex': DATABASE_BACKUP_CONFIG.get("yandex_backups", {}),
        }

        db_stats = {}
        for category, databases in config_databases.items():
            total_in_config = len(databases)
            if total_in_config == 0:
                continue

            successful_count = 0
            for db_key in databases.keys():
                if any(
                    backup_type == category and db_name == db_key and status == 'success'
                    for backup_type, db_name, status, _ in db_results
                ):
                    successful_count += 1

            db_stats[category] = {
                'total': total_in_config,
                'successful': successful_count,
            }

        message = ""

        if len(all_hosts) > 0:
            success_rate = (hosts_with_success / len(all_hosts)) * 100
            message += f"• Proxmox: {hosts_with_success}/{len(all_hosts)} успешно ({success_rate:.1f}%)"
            if stale_hosts:
                message += f" ⚠️ {len(stale_hosts)} хостов без бэкапов >24ч"
            message += "\n"

        message += "• Базы данных:\n"

        category_names = {
            'company_database': 'Основные',
            'barnaul': 'Барнаул',
            'client': 'Клиенты',
            'yandex': 'Yandex',
        }

        for category in ['company_database', 'barnaul', 'client', 'yandex']:
            if category not in db_stats:
                continue
            stats = db_stats[category]
            if stats['total'] <= 0:
                continue

            type_name = category_names[category]
            success_rate = (stats['successful'] / stats['total']) * 100
            message += f"  - {type_name}: {stats['successful']}/{stats['total']} успешно ({success_rate:.1f}%)"

            stale_count = len([db for db in stale_databases if db[0] == category])
            if stale_count > 0:
                message += f" ⚠️ {stale_count} БД без бэкапов >24ч"
            message += "\n"

        total_stale = len(stale_hosts) + len(stale_databases)
        if total_stale > 0:
            message += f"\n🚨 Внимание: {total_stale} проблем:\n"
            if stale_hosts:
                message += f"• {len(stale_hosts)} хостов без бэкапов >24ч\n"
            if stale_databases:
                message += f"• {len(stale_databases)} БД без бэкапов >24ч\n"

        return message

    except Exception as e:
        logger.exception("Ошибка формирования отчета о бэкапах: %s", e)
        return "❌ Ошибка формирования отчета о бэкапах\n"

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
    def calculate_host_status(recent_backups, hours_threshold=48):
        """Рассчитывает статус хоста на основе recent_backups"""
        if not recent_backups:
            return "stale"
        
        last_status, last_time = recent_backups[0]
        
        # Последний бэкап неудачный
        if last_status == 'failed':
            return "failed"
        
        # Есть неудачные бэкапы в истории
        recent_failed = any(status == 'failed' for status, _ in recent_backups[:3])
        if recent_failed:
            return "recent_failed"
        
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
    
