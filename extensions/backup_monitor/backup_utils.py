"""
Server Monitoring System v3.3.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Утилиты для работы с бэкапами
"""

import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

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
    