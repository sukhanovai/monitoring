"""
Обработчик писем с отчетами о бэкапах Proxmox
"""

import re
import sqlite3
import logging
from datetime import datetime
from extensions.email_processor.base_handler import BaseEmailHandler

try:
    from config.backup_config import (
        PROXMOX_HOSTS,
        PROXMOX_SUBJECT_PATTERNS,
        HOSTNAME_PATTERNS,
        BACKUP_STATUS_MAP,
        DATABASE_CONFIG
    )
except ImportError:
    # Fallback конфигурация если файл не найден
    PROXMOX_HOSTS = {}
    PROXMOX_SUBJECT_PATTERNS = [r'vzdump backup status']
    HOSTNAME_PATTERNS = [r'\(([^)]+)\)']
    BACKUP_STATUS_MAP = {
        'backup successful': 'success',
        'backup failed': 'failed',
    }
    DATABASE_CONFIG = {
        'backups_db': '/opt/monitoring/data/backups.db',
        'max_backup_age_days': 90,
    }
    logging.getLogger(__name__).warning("Используется fallback конфигурация бэкапов")

class ProxmoxBackupHandler(BaseEmailHandler):
    """Обработчик отчетов о бэкапах от Proxmox"""
    
    def __init__(self):
        super().__init__()
        self.db_path = DATABASE_CONFIG['backups_db']
        self.host_ip_map = PROXMOX_HOSTS
        self.subject_patterns = PROXMOX_SUBJECT_PATTERNS
        self.hostname_patterns = HOSTNAME_PATTERNS
        self.status_map = BACKUP_STATUS_MAP
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных для бэкапов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения статусов бэкапов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxmox_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_name TEXT NOT NULL,
                host_ip TEXT,
                backup_status TEXT NOT NULL,
                task_type TEXT,
                vm_count INTEGER DEFAULT 0,
                successful_vms INTEGER DEFAULT 0,
                failed_vms INTEGER DEFAULT 0,
                start_time TEXT,
                end_time TEXT,
                duration TEXT,
                total_size TEXT,
                error_message TEXT,
                email_subject TEXT,
                raw_subject TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(host_name, received_at)
            )
        ''')
        
        # Создаем индекс для быстрого поиска
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_proxmox_backups_host_date 
            ON proxmox_backups(host_name, received_at)
        ''')
        
        # Создаем индекс для статусов
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_proxmox_backups_status 
            ON proxmox_backups(backup_status, received_at)
        ''')
        
        # Очищаем старые записи
        cursor.execute('''
            DELETE FROM proxmox_backups 
            WHERE received_at < datetime('now', ?)
        ''', (f"-{DATABASE_CONFIG['max_backup_age_days']} days",))
        
        conn.commit()
        conn.close()
        self.logger.info("База данных Proxmox бэкапов инициализирована")
    
    def can_handle(self, email_data):
        """Определяет Proxmox бэкапы по теме письма и отправителю"""
        subject = email_data.get('subject', '').lower()
        from_email = email_data.get('from_email', '').lower()
        
        # Проверяем паттерны в теме
        subject_match = any(
            re.search(pattern, subject, re.IGNORECASE) 
            for pattern in self.subject_patterns
        )
        
        # Проверяем отправителя (обычно root@pveX.localdomain)
        from_match = any(
            host in from_email for host in self.host_ip_map.keys()
        ) or any(
            f"pve{num}" in from_email for num in range(1, 15)
        ) or 'pve' in from_email
        
        # Проверяем наличие известных имен хостов в теме
        host_in_subject = any(
            host in subject for host in self.host_ip_map.keys()
        )
        
        return subject_match or from_match or host_in_subject
    
    def process(self, email_data):
        """Обрабатывает отчет о бэкапах Proxmox"""
        try:
            self.logger.info(f"Обработка Proxmox бэкапа: {email_data['subject']}")
            
            # Парсим основную информацию из темы
            backup_info = self.parse_subject(email_data['subject'])
            
            if not backup_info:
                self.logger.warning("Не удалось извлечь информацию из темы письма")
                return
            
            # Дополняем информацией из тела письма
            backup_info.update(self.parse_body(email_data['body']))
            
            # Сохраняем в базу
            self.save_backup_report(backup_info, email_data)
            
            self.logger.info(f"Обработан бэкап от {backup_info['host_name']}: {backup_info['backup_status']}")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки Proxmox отчета: {e}")
    
    def parse_subject(self, subject):
        """Парсит тему письма для извлечения ключевой информации"""
        # Пример: "vzdump backup status (pve13.geltd.local): backup successful"
        
        # Извлекаем имя хоста используя все паттерны
        host_name = self.extract_hostname(subject)
        if not host_name:
            self.logger.warning(f"Не удалось извлечь имя хоста из темы: {subject}")
            return None
        
        # Извлекаем статус бэкапа (после последнего двоеточия)
        status_match = re.search(r':\s*([^:]+)$', subject)
        raw_status = status_match.group(1).strip().lower() if status_match else 'unknown'
        
        # Нормализуем статус
        normalized_status = self.status_map.get(raw_status, raw_status)
        
        return {
            'host_name': host_name,
            'backup_status': normalized_status,
            'raw_status': raw_status,
            'task_type': 'vzdump',
            'raw_subject': subject
        }
    
    def extract_hostname(self, subject):
        """Извлекает имя хоста из темы письма используя различные паттерны"""
        subject_lower = subject.lower()
        
        # Сначала ищем точное совпадение с известными хостами
        for host_name in self.host_ip_map.keys():
            if host_name in subject_lower:
                return host_name
        
        # Ищем по паттернам из конфига
        for pattern in self.hostname_patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                host_candidate = match.group(1)
                # Очищаем имя хоста (убираем домен и т.д.)
                clean_host = self.clean_hostname(host_candidate)
                if clean_host:
                    return clean_host
        
        # Пробуем извлечь по общим паттернам Proxmox
        proxmox_patterns = [
            r'(pve\d+)',
            r'(bup\d+)', 
            r'(pve-kc)',
            r'(sr-pve\d+)',
        ]
        
        for pattern in proxmox_patterns:
            match = re.search(pattern, subject_lower)
            if match:
                return match.group(1)
        
        return None
    
    def clean_hostname(self, hostname):
        """Очищает имя хоста от домена и лишних частей"""
        if not hostname:
            return None
        
        # Убираем домен (все что после первой точки)
        clean_name = hostname.split('.')[0].lower()
        
        # Убираем префиксы/суффиксы если нужно
        clean_name = clean_name.replace('(', '').replace(')', '').strip()
        
        # Проверяем что это валидное имя хоста
        if re.match(r'^[a-z0-9-]+$', clean_name):
            return clean_name
        
        return None
    
    def parse_body(self, body):
        """Парсит тело письма для извлечения дополнительной информации"""
        info = {
            'vm_count': 0,
            'successful_vms': 0,
            'failed_vms': 0,
            'duration': None,
            'total_size': None,
            'error_message': None
        }
        
        lines = body.split('\n')
        
        for line in lines:
            line = line.strip()
            line_lower = line.lower()
            
            # Поиск информации о времени выполнения
            if any(keyword in line_lower for keyword in ['duration', 'time taken', 'время выполнения']):
                duration_match = re.search(r'(\d+:\d+:\d+|\d+\s*(hours|minutes|seconds))', line, re.IGNORECASE)
                if duration_match:
                    info['duration'] = duration_match.group(1)
            
            # Поиск информации о размере
            elif any(keyword in line_lower for keyword in ['size', 'total', 'размер', 'общий']):
                size_match = re.search(r'(\d+\.?\d*\s*[GMK]?B)', line, re.IGNORECASE)
                if size_match:
                    info['total_size'] = size_match.group(1)
            
            # Поиск сообщений об ошибках
            elif any(keyword in line_lower for keyword in ['error', 'failed', 'ошибка', 'сбой']):
                if not info['error_message'] and len(line) > 10:  # Не слишком короткие строки
                    info['error_message'] = line[:200]  # Ограничиваем длину
            
            # Подсчет VM (если упоминаются в письме)
            elif 'vm' in line_lower:
                if any(success in line_lower for success in ['ok', 'success', 'успех']):
                    info['successful_vms'] += 1
                    info['vm_count'] += 1
                elif any(fail in line_lower for fail in ['error', 'fail', 'failed', 'ошибка']):
                    info['failed_vms'] += 1
                    info['vm_count'] += 1
                elif info['vm_count'] == 0:
                    # Если VM упоминаются но статус не ясен, считаем их
                    info['vm_count'] += 1
        
        return info
    
    def save_backup_report(self, backup_info, email_data):
        """Сохраняет отчет о бэкапе в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO proxmox_backups 
                (host_name, host_ip, backup_status, task_type, vm_count, 
                 successful_vms, failed_vms, duration, total_size, error_message, 
                 email_subject, raw_subject)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backup_info['host_name'],
                self.get_host_ip(backup_info['host_name']),
                backup_info['backup_status'],
                backup_info['task_type'],
                backup_info.get('vm_count', 0),
                backup_info.get('successful_vms', 0),
                backup_info.get('failed_vms', 0),
                backup_info.get('duration'),
                backup_info.get('total_size'),
                backup_info.get('error_message'),
                email_data['subject'][:500],  # Ограничиваем длину
                backup_info.get('raw_subject', '')[:500]
            ))
            
            conn.commit()
            self.logger.debug(f"Сохранен отчет бэкапа для {backup_info['host_name']}")
            
        except sqlite3.IntegrityError:
            self.logger.warning(f"Дублирующийся отчет для {backup_info['host_name']}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения отчета: {e}")
        finally:
            conn.close()
    
    def get_host_ip(self, host_name):
        """Получает IP адрес хоста по имени"""
        # Обработка префикса sr-
        clean_name = host_name[3:] if host_name.startswith('sr-') else host_name
        
        return self.host_ip_map.get(clean_name, 'unknown')
    