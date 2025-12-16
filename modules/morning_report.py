"""
/modules/morning_report.py
Server Monitoring System v4.13.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning report module
Система мониторинга серверов
Версия: 4.13.3
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль утреннего отчета
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from lib.logging import debug_log
from config.settings import DATA_COLLECTION_TIME

class MorningReport:
    """Класс для генерации утреннего отчета"""
    
    def __init__(self):
        """Инициализация модуля отчета"""
        self.morning_data = {}
        self.last_report_date = None
        
    def collect_morning_data(self, servers_status: Dict) -> Dict:
        """
        Собирает данные для утреннего отчета
        
        Args:
            servers_status: Статус серверов
            
        Returns:
            Dict: Данные для отчета
        """
        current_time = datetime.now()
        
        report_data = {
            "status": servers_status,
            "collection_time": current_time,
            "manual_call": False,
            "backup_summary": self._get_backup_summary(period_hours=16)
        }
        
        self.morning_data = report_data
        debug_log(f"📊 Данные для утреннего отчета собраны: {len(servers_status.get('ok', []))} доступно")
        
        return report_data
    
    def generate_report(self, manual_call: bool = False) -> str:
        """
        Генерирует текст отчета
        
        Args:
            manual_call: Ручной вызов
            
        Returns:
            str: Текст отчета
        """
        if not self.morning_data or "status" not in self.morning_data:
            debug_log("⚠️ Нет данных для отчета, собираем текущие")
            from modules.availability import availability_checker
            from extensions.server_checks import initialize_servers
            
            servers = initialize_servers()
            current_status = availability_checker.check_multiple_servers(servers)
            self.collect_morning_data(current_status)
        
        status = self.morning_data["status"]
        collection_time = self.morning_data.get("collection_time", datetime.now())
        backup_summary = self.morning_data.get("backup_summary", "")
        is_manual = self.morning_data.get("manual_call", False)
        
        # Формируем заголовок
        if is_manual:
            report_type = "Ручной запрос"
            time_prefix = "⏰ *Время проверки:*"
        else:
            report_type = "Утренний отчет"
            time_prefix = "⏰ *Время сбора данных:*"
        
        total_servers = len(status.get("ok", [])) + len(status.get("failed", []))
        up_count = len(status.get("ok", []))
        down_count = len(status.get("failed", []))
        
        # Начинаем формировать сообщение
        message = f"📊 *{report_type} о доступности серверов*\n\n"
        message += f"{time_prefix} {collection_time.strftime('%H:%M')}\n"
        message += f"🔢 *Всего серверов:* {total_servers}\n"
        message += f"🟢 *Доступно:* {up_count}\n"
        message += f"🔴 *Недоступно:* {down_count}\n"
        
        # Добавляем сводку по бэкапам
        if backup_summary:
            backup_period = "за последние 24ч" if is_manual else "за последние 16ч"
            message += f"\n💾 *Статус бэкапов ({backup_period})*\n"
            message += backup_summary
        
        # Добавляем проблемные серверы
        if down_count > 0:
            message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"
            
            # Группируем по типу
            by_type = {}
            for server in status.get("failed", []):
                server_type = server.get("type", "unknown")
                if server_type not in by_type:
                    by_type[server_type] = []
                by_type[server_type].append(server)
            
            for server_type, servers_list in by_type.items():
                message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                for s in servers_list:
                    message += f"• {s.get('name', 'Unknown')} ({s.get('ip', 'Unknown')})\n"
        
        else:
            message += f"\n✅ *Все серверы доступны!*\n"
        
        # Статистика по типам серверов
        message += f"\n📋 *Статистика по типам:*\n"
        
        type_stats = {}
        all_servers = status.get("ok", []) + status.get("failed", [])
        for server in all_servers:
            server_type = server.get("type", "unknown")
            if server_type not in type_stats:
                type_stats[server_type] = {"total": 0, "up": 0}
            type_stats[server_type]["total"] += 1
        
        for server in status.get("ok", []):
            server_type = server.get("type", "unknown")
            type_stats[server_type]["up"] += 1
        
        for server_type, stats in type_stats.items():
            up_percent = (stats["up"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            message += f"• {server_type.upper()}: {stats['up']}/{stats['total']} ({up_percent:.1f}%)\n"
        
        # Время формирования
        if is_manual:
            message += f"\n⏰ *Отчет сформирован:* {datetime.now().strftime('%H:%M:%S')}"
        else:
            message += f"\n⏰ *Отчет отправлен:* {datetime.now().strftime('%H:%M:%S')}"
        
        return message
    
    def _get_backup_summary(self, period_hours: int = 16) -> str:
        """
        Получает сводку по бэкапам
        
        Args:
            period_hours: Период в часах
            
        Returns:
            str: Сводка по бэкапам
        """
        try:
            debug_log(f"🔄 Сбор данных о бэкапах за {period_hours} часов...")
            
            db_path = "/opt/monitoring/data/backups.db"
            
            if not os.path.exists(db_path):
                debug_log(f"❌ База данных не найдена: {db_path}")
                return "❌ База данных бэкапов недоступна\n"
            
            since_time = (datetime.now() - timedelta(hours=period_hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Получаем все хосты за 7 дней
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
            
            # Получаем последние бэкапы за период
            cursor.execute('''
                SELECT host_name, backup_status, MAX(received_at) as last_backup
                FROM proxmox_backups 
                WHERE received_at >= ?
                GROUP BY host_name
            ''', (since_time,))
            proxmox_results = cursor.fetchall()
            
            # Получаем конфигурацию
            from config.settings import PROXMOX_HOSTS
            
            # Определяем активные хосты
            active_host_names = [row[0] for row in all_hosts_from_db]
            all_hosts = [host for host in PROXMOX_HOSTS.keys() if host in active_host_names]
            
            if len(all_hosts) != 15:
                # Альтернативный метод
                cursor.execute('''
                    SELECT DISTINCT host_name 
                    FROM proxmox_backups 
                    WHERE received_at >= datetime('now', '-30 days')
                    ORDER BY host_name
                ''')
                all_unique_hosts = [row[0] for row in cursor.fetchall()]
                all_hosts = all_unique_hosts
            
            # Считаем успешные
            hosts_with_success = len([r for r in proxmox_results if r[1] == 'success'])
            
            # Базы данных
            cursor.execute('''
                SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
                FROM database_backups 
                WHERE received_at >= ?
                GROUP BY backup_type, database_name
            ''', (since_time,))
            db_results = cursor.fetchall()
            
            from config.settings import DATABASE_BACKUP_CONFIG
            
            config_databases = {
                'company_database': DATABASE_BACKUP_CONFIG.get("company_databases", {}),
                'barnaul': DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
                'client': DATABASE_BACKUP_CONFIG.get("client_databases", {}),
                'yandex': DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
            }
            
            db_stats = {}
            for category, databases in config_databases.items():
                total_in_config = len(databases)
                if total_in_config > 0:
                    successful_count = 0
                    
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
            
            # Устаревшие бэкапы
            stale_threshold = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                SELECT host_name, MAX(received_at) as last_backup
                FROM proxmox_backups 
                GROUP BY host_name
                HAVING last_backup < ?
            ''', (stale_threshold,))
            stale_hosts = cursor.fetchall()
            
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
            debug_log(f"💥 Критическая ошибка в get_backup_summary: {e}")
            import traceback
            debug_log(f"💥 Traceback: {traceback.format_exc()}")
            return "❌ Ошибка формирования отчета о бэкапах\n"
    
    def should_send_report(self) -> bool:
        """
        Проверяет, нужно ли отправлять отчет
        
        Returns:
            bool: True если нужно отправить
        """
        current_time = datetime.now()
        current_time_time = current_time.time()
        
        # Проверяем время сбора данных
        if (current_time_time.hour == DATA_COLLECTION_TIME.hour and
            current_time_time.minute == DATA_COLLECTION_TIME.minute):
            
            # Проверяем, что сегодня еще не отправляли отчет
            today = current_time.date()
            if self.last_report_date != today:
                self.last_report_date = today
                return True
        
        return False
    
    def force_report(self) -> str:
        """
        Принудительная генерация отчета
        
        Returns:
            str: Текст отчета
        """
        debug_log("📊 Ручной вызов отчета")
        
        from modules.availability import availability_checker
        from extensions.server_checks import initialize_servers
        
        servers = initialize_servers()
        current_status = availability_checker.check_multiple_servers(servers)
        
        self.morning_data = {
            "status": current_status,
            "collection_time": datetime.now(),
            "manual_call": True,
            "backup_summary": self._get_backup_summary(period_hours=24)
        }
        
        return self.generate_report(manual_call=True)

# Глобальный экземпляр для импорта
morning_report = MorningReport()