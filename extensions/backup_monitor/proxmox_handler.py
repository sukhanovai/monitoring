"""
Улучшенный обработчик писем с отчетами о бэкапах Proxmox
"""

import re
import sqlite3
import logging
from datetime import datetime
from email import message_from_bytes
import email.policy

class ProxmoxBackupHandler:
    """Обработчик отчетов о бэкапах от Proxmox"""
    
    def __init__(self):
        self.db_path = '/opt/monitoring/data/backups.db'
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных для бэкапов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxmox_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_name TEXT NOT NULL,
                backup_status TEXT NOT NULL,
                task_type TEXT,
                duration TEXT,
                total_size TEXT,
                error_message TEXT,
                email_subject TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_backups_host_date 
            ON proxmox_backups(host_name, received_at)
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("База данных бэкапов инициализирована")
    
    def parse_email_file(self, file_path):
        """Парсит email файл и извлекает информацию о бэкапе"""
        try:
            with open(file_path, 'rb') as f:
                msg = message_from_bytes(f.read(), policy=email.policy.default)
            
            subject = msg.get('subject', '')
            from_email = msg.get('from', '')
            date_str = msg.get('date', '')
            
            self.logger.info(f"Обработка письма: {subject}")
            
            # Извлекаем информацию из темы
            backup_info = self.parse_subject(subject)
            if not backup_info:
                return None
            
            # Парсим тело письма
            body = self.get_email_body(msg)
            backup_info.update(self.parse_body(body))
            
            # Сохраняем в базу
            self.save_backup_report(backup_info, subject)
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга письма: {e}")
            return None
    
    def parse_subject(self, subject):
        """Парсит тему письма для извлечения ключевой информации"""
        # Пример: "vzdump backup status (sr-pve5.geltd.local): backup successful"
        
        # Извлекаем имя хоста
        host_match = re.search(r'\(([^)]+)\)', subject)
        if not host_match:
            self.logger.warning(f"Не удалось извлечь имя хоста из темы: {subject}")
            return None
        
        host_name = host_match.group(1).split('.')[0]  # Берем только имя хоста без домена
        
        # Извлекаем статус бэкапа
        status_match = re.search(r':\s*([^:]+)$', subject)
        if not status_match:
            self.logger.warning(f"Не удалось извлечь статус из темы: {subject}")
            return None
        
        raw_status = status_match.group(1).strip().lower()
        
        # Нормализуем статус
        status_map = {
            'backup successful': 'success',
            'successful': 'success',
            'ok': 'success',
            'backup failed': 'failed',
            'failed': 'failed',
            'error': 'failed'
        }
        
        normalized_status = status_map.get(raw_status, raw_status)
        
        return {
            'host_name': host_name,
            'backup_status': normalized_status,
            'raw_status': raw_status,
            'task_type': 'vzdump'
        }
    
    def get_email_body(self, msg):
        """Извлекает тело письма"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    return part.get_content()
        else:
            return msg.get_content()
        
        return ""
    
    def parse_body(self, body):
        """Парсит тело письма для извлечения дополнительной информации"""
        info = {
            'duration': None,
            'total_size': None,
            'error_message': None
        }
        
        lines = body.split('\n')
        
        for line in lines:
            line = line.strip()
            line_lower = line.lower()
            
            # Поиск информации о времени выполнения
            if 'duration' in line_lower or 'time' in line_lower:
                duration_match = re.search(r'(\d+:\d+:\d+)', line)
                if duration_match:
                    info['duration'] = duration_match.group(1)
            
            # Поиск информации о размере
            elif 'size' in line_lower or 'total' in line_lower:
                size_match = re.search(r'(\d+\.?\d*\s*[GMK]?B)', line)
                if size_match:
                    info['total_size'] = size_match.group(1)
            
            # Поиск сообщений об ошибках
            elif 'error' in line_lower or 'failed' in line_lower:
                if not info['error_message'] and len(line) > 10:
                    info['error_message'] = line[:200]  # Ограничиваем длину
        
        return info
    
    def save_backup_report(self, backup_info, subject):
        """Сохраняет отчет о бэкапе в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO proxmox_backups 
                (host_name, backup_status, task_type, duration, total_size, error_message, email_subject)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                backup_info['host_name'],
                backup_info['backup_status'],
                backup_info['task_type'],
                backup_info.get('duration'),
                backup_info.get('total_size'),
                backup_info.get('error_message'),
                subject[:500]  # Ограничиваем длину
            ))
            
            conn.commit()
            self.logger.info(f"Сохранен отчет бэкапа для {backup_info['host_name']}: {backup_info['backup_status']}")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения отчета: {e}")
        finally:
            conn.close()
                