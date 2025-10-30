#!/usr/bin/env python3
"""
Улучшенный мониторинг почтового ящика - исправленная версия
"""

import os
import time
import logging
import sqlite3
import re
import shutil
from email import message_from_bytes
import email.policy
from datetime import datetime
from email.utils import parsedate_to_datetime
from config import (
    PROXMOX_HOSTS, PROXMOX_SUBJECT_PATTERNS, HOSTNAME_PATTERNS, 
    BACKUP_STATUS_MAP, BACKUP_DATABASE_CONFIG
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/monitoring/logs/mail_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupProcessor:
    """Обработчик бэкапов"""
    
    def __init__(self):
        self.db_path = BACKUP_DATABASE_CONFIG['backups_db']
        self.processed_files = set()
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        try:
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
            logger.info("База данных бэкапов инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    def process_new_emails(self):
        """Обрабатывает новые письма из директории new"""
        maildir_new = '/root/Maildir/new'
        maildir_cur = '/root/Maildir/cur'
        
        if not os.path.exists(maildir_new):
            logger.error(f"Директория не существует: {maildir_new}")
            return 0
        
        processed_count = 0
        for filename in os.listdir(maildir_new):
            file_path = os.path.join(maildir_new, filename)
            
            if os.path.isfile(file_path):
                logger.info(f"🔍 Обнаружено новое письмо: {filename}")
                
                # Обрабатываем письмо
                result = self.parse_email_file(file_path)
                
                if result:
                    # Перемещаем обработанное письмо в cur
                    try:
                        new_path = os.path.join(maildir_cur, filename)
                        shutil.move(file_path, new_path)
                        logger.info(f"✅ Письмо перемещено в cur: {filename}")
                        self.processed_files.add(new_path)
                    except Exception as e:
                        logger.error(f"❌ Ошибка перемещения письма: {e}")
                        self.processed_files.add(file_path)
                    
                    processed_count += 1
                else:
                    logger.warning(f"⚠️ Не удалось обработать письмо: {filename}")
                    # Все равно перемещаем, чтобы не зацикливаться
                    try:
                        new_path = os.path.join(maildir_cur, filename)
                        shutil.move(file_path, new_path)
                        self.processed_files.add(new_path)
                    except Exception as e:
                        logger.error(f"❌ Ошибка перемещения непрочитанного письма: {e}")
    
        return processed_count
    
    def parse_email_file(self, file_path):
        """Парсит email файл"""
        try:
            logger.info(f"Обработка файла: {file_path}")
            
            with open(file_path, 'rb') as f:
                msg = message_from_bytes(f.read(), policy=email.policy.default)
            
            subject = msg.get('subject', '')
            email_date_str = msg.get('date', '')
            logger.info(f"Тема письма: {subject}")
            logger.info(f"Дата письма: {email_date_str}")
            
            # Парсим дату письма
            email_date = None
            if email_date_str:
                try:
                    email_date = parsedate_to_datetime(email_date_str)
                except Exception as e:
                    logger.warning(f"Не удалось распарсить дату письма: {e}")
                    email_date = datetime.now()
            
            # Сначала проверяем, это ли письмо о бэкапе базы данных
            db_backup_info = self.parse_database_backup(subject, self.get_email_body(msg))
            if db_backup_info:
                logger.info(f"📊 Обнаружен бэкап базы данных: {db_backup_info['database_display_name']}")
                self.save_database_backup(db_backup_info, subject, email_date)
                return db_backup_info
            
            # Затем проверяем, это ли письмо о бэкапе Proxmox
            if not self.is_proxmox_backup_email(subject):
                logger.info(f"Пропускаем не-Proxmox письмо: {subject[:50]}...")
                return None
            
            # Извлекаем информацию из темы
            backup_info = self.parse_subject(subject)
            if not backup_info:
                logger.warning("Не удалось извлечь информацию из темы")
                return None
            
            # Парсим тело письма
            body = self.get_email_body(msg)
            backup_info.update(self.parse_body(body))
            
            # Сохраняем в базу с корректным временем
            self.save_backup_report(backup_info, subject, email_date)
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Ошибка парсинга файла {file_path}: {e}")
            return None
        
    def is_proxmox_backup_email(self, subject):
        """Проверяет, является ли письмо отчетом о бэкапе Proxmox"""
        subject_lower = subject.lower()
        return any(keyword in subject_lower for keyword in [
            'vzdump backup status',
            'proxmox backup',
            'backup successful',
            'backup failed'
        ])
    
    def parse_subject(self, subject):
        """Парсит тему письма"""
        # Пример: "vzdump backup status (sr-pve4.geltd.local): backup successful"
        
        # Извлекаем имя хоста
        host_match = re.search(r'\(([^)]+)\)', subject)
        if not host_match:
            logger.warning(f"Не удалось извлечь имя хоста: {subject}")
            return None
        
        host_name = host_match.group(1).split('.')[0]  # Берем только имя хоста
        
        # Извлекаем статус бэкапа
        status_match = re.search(r':\s*([^:]+)$', subject)
        if not status_match:
            logger.warning(f"Не удалось извлечь статус: {subject}")
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
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        return part.get_content()
            else:
                return msg.get_content()
        except Exception as e:
            logger.error(f"Ошибка извлечения тела письма: {e}")
        
        return ""
    
    def parse_body(self, body):
        """Парсит тело письма для извлечения корректной информации"""
        info = {
            'duration': None,
            'total_size': None,
            'error_message': None,
            'vm_count': 0,
            'successful_vms': 0,
            'failed_vms': 0
        }
        
        try:
            lines = body.split('\n')
            in_details_section = False
            
            for line in lines:
                line = line.strip()
                line_lower = line.lower()
                
                # Ищем общее время выполнения
                if 'total running time' in line_lower:
                    time_match = re.search(r'(\d+[hm]\s*\d*[sm]*)', line, re.IGNORECASE)
                    if time_match:
                        raw_time = time_match.group(1)
                        # Конвертируем в стандартный формат
                        info['duration'] = self.parse_duration(raw_time)
                
                # Ищем общий размер
                elif 'total size' in line_lower:
                    size_match = re.search(r'(\d+\.?\d*\s*[GMK]?i?B)', line, re.IGNORECASE)
                    if size_match:
                        info['total_size'] = size_match.group(1)
                
                # Ищем секцию с деталями VM
                elif 'vmid' in line_lower and 'name' in line_lower and 'status' in line_lower:
                    in_details_section = True
                    continue
                
                # Парсим строки с VM в секции деталей
                elif in_details_section and re.match(r'^\d+\s+', line):
                    parts = line.split()
                    if len(parts) >= 4:
                        info['vm_count'] += 1
                        status = parts[2].lower()
                        if status == 'ok':
                            info['successful_vms'] += 1
                        else:
                            info['failed_vms'] += 1
                
                # Выходим из секции деталей
                elif in_details_section and not line:
                    in_details_section = False
                
                # Поиск сообщений об ошибках
                elif 'error' in line_lower or 'failed' in line_lower:
                    if not info['error_message'] and len(line) > 10:
                        info['error_message'] = line[:200]
            
            # Если не нашли общее время, но есть VM, суммируем их время
            if not info['duration'] and info['vm_count'] > 0:
                total_seconds = 0
                for line in lines:
                    # Ищем время выполнения для каждой VM (формат: 3m 33s, 1m 14s и т.д.)
                    time_match = re.search(r'(\d+m\s*\d*s)', line)
                    if time_match:
                        vm_time = time_match.group(1)
                        total_seconds += self.duration_to_seconds(vm_time)
                
                if total_seconds > 0:
                    info['duration'] = self.seconds_to_duration(total_seconds)
                    
        except Exception as e:
            logger.error(f"Ошибка парсинга тела письма: {e}")
        
        return info

    def parse_duration(self, duration_str):
        """Парсит строку длительности в читаемый формат"""
        try:
            # Примеры: "31m 31s", "1h 30m", "45s"
            duration_str = duration_str.lower().replace(' ', '')
            
            hours = 0
            minutes = 0
            seconds = 0
            
            # Ищем часы
            h_match = re.search(r'(\d+)h', duration_str)
            if h_match:
                hours = int(h_match.group(1))
            
            # Ищем минуты
            m_match = re.search(r'(\d+)m', duration_str)
            if m_match:
                minutes = int(m_match.group(1))
            
            # Ищем секунды
            s_match = re.search(r'(\d+)s', duration_str)
            if s_match:
                seconds = int(s_match.group(1))
            
            # Форматируем в читаемый вид
            if hours > 0:
                return f"{hours}h {minutes:02d}m {seconds:02d}s"
            elif minutes > 0:
                return f"{minutes}m {seconds:02d}s"
            else:
                return f"{seconds}s"
                
        except Exception as e:
            logger.error(f"Ошибка парсинга длительности '{duration_str}': {e}")
            return duration_str

    def duration_to_seconds(self, duration_str):
        """Конвертирует строку длительности в секунды"""
        try:
            total_seconds = 0
            duration_str = duration_str.lower().replace(' ', '')
            
            # Минуты
            m_match = re.search(r'(\d+)m', duration_str)
            if m_match:
                total_seconds += int(m_match.group(1)) * 60
            
            # Секунды
            s_match = re.search(r'(\d+)s', duration_str)
            if s_match:
                total_seconds += int(s_match.group(1))
            
            return total_seconds
        except:
            return 0

    def seconds_to_duration(self, total_seconds):
        """Конвертирует секунды в читаемую длительность"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        else:
            return f"{seconds}s"

    def save_backup_report(self, backup_info, subject, email_date=None):
        """Сохраняет отчет в базу с корректным временем"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Используем текущее время как время получения, если нет даты из письма
            if email_date:
                received_at = email_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                received_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO proxmox_backups 
                (host_name, backup_status, task_type, duration, total_size, error_message, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backup_info['host_name'],
                backup_info['backup_status'],
                backup_info['task_type'],
                backup_info.get('duration'),
                backup_info.get('total_size'),
                backup_info.get('error_message'),
                subject[:500],
                received_at
            ))
            
            conn.commit()
            logger.info(f"✅ Сохранен бэкап: {backup_info['host_name']} - {backup_info['backup_status']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def parse_database_backup(self, subject, body):
        """Парсит бэкапы баз данных из темы письма"""
        try:
            backup_info = {}
            
            # Проверяем бэкапы основных баз данных
            for pattern in DATABASE_BACKUP_PATTERNS["company"]:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    db_name = match.group(1).lower()
                    display_name = DATABASE_BACKUP_CONFIG["company_databases"].get(db_name, db_name)
                    backup_info = {
                        'host_name': 'sr-bup',
                        'backup_status': 'success',
                        'task_type': 'database_dump',
                        'database_name': db_name,
                        'database_display_name': display_name,
                        'backup_type': 'company_database'
                    }
                    return backup_info
            
            # Проверяем бэкапы Барнаул
            for pattern in DATABASE_BACKUP_PATTERNS["barnaul"]:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    backup_name = match.group(1)
                    error_count = int(match.group(2))
                    display_name = DATABASE_BACKUP_CONFIG["barnaul_backups"].get(backup_name, backup_name)
                    backup_info = {
                        'host_name': 'brn-backup',
                        'backup_status': 'success' if error_count == 0 else 'failed',
                        'task_type': 'cobian_backup',
                        'database_name': backup_name,
                        'database_display_name': display_name,
                        'error_count': error_count,
                        'backup_type': 'barnaul'
                    }
                    return backup_info
            
            # Проверяем бэкапы клиентов
            for pattern in DATABASE_BACKUP_PATTERNS["clients"]:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    db_name = match.group(1).lower()
                    display_name = DATABASE_BACKUP_CONFIG["client_databases"].get(db_name, db_name)
                    backup_info = {
                        'host_name': 'kc-1c',
                        'backup_status': 'success',
                        'task_type': 'client_database_dump',
                        'database_name': db_name,
                        'database_display_name': display_name,
                        'backup_type': 'client'
                    }
                    return backup_info
            
            # Проверяем бэкапы Yandex
            for pattern in DATABASE_BACKUP_PATTERNS["yandex"]:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    client_name = match.group(1)
                    display_name = DATABASE_BACKUP_CONFIG["yandex_backups"].get(client_name, client_name)
                    backup_info = {
                        'host_name': 'yandex-backup',
                        'backup_status': 'success',
                        'task_type': 'yandex_backup',
                        'database_name': client_name,
                        'database_display_name': display_name,
                        'backup_type': 'yandex'
                    }
                    return backup_info
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка парсинга бэкапа БД: {e}")
            return None

    def save_database_backup(self, backup_info, subject, email_date=None):
        """Сохраняет информацию о бэкапе базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу для бэкапов БД если не существует
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS database_backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_name TEXT NOT NULL,
                    database_name TEXT NOT NULL,
                    database_display_name TEXT,
                    backup_status TEXT NOT NULL,
                    backup_type TEXT,
                    task_type TEXT,
                    error_count INTEGER DEFAULT 0,
                    email_subject TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Используем текущее время как время получения, если нет даты из письма
            if email_date:
                received_at = email_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                received_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO database_backups 
                (host_name, database_name, database_display_name, backup_status, backup_type, task_type, error_count, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backup_info['host_name'],
                backup_info['database_name'],
                backup_info.get('database_display_name'),
                backup_info['backup_status'],
                backup_info.get('backup_type'),
                backup_info.get('task_type'),
                backup_info.get('error_count', 0),
                subject[:500],
                received_at
            ))
            
            conn.commit()
            logger.info(f"✅ Сохранен бэкап БД: {backup_info['database_display_name']} - {backup_info['backup_status']}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения бэкапа БД в БД: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

def main():
    """Основная функция"""
    logger.info("🔄 Запуск исправленного мониторинга почты Proxmox бэкапов...")
    
    try:
        processor = BackupProcessor()
        
        logger.info("📧 Мониторинг директорий: /root/Maildir/new и /root/Maildir/cur")
        
        # Основной цикл
        while True:
            try:
                # Обрабатываем новые письма
                processed = processor.process_new_emails()
                if processed > 0:
                    logger.info(f"✅ Обработано новых писем: {processed}")
                
                time.sleep(30)  # Проверяем каждые 30 секунд
                
            except Exception as e:
                logger.error(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(60)
                
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
    