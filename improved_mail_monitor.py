#!/usr/bin/env python3
"""
Улучшенный мониторинг почтового ящика
"""

import os
import time
import logging
import sqlite3
import re
from email import message_from_bytes
import email.policy
from datetime import datetime

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
        self.db_path = '/opt/monitoring/data/backups.db'
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
    
    def parse_email_file(self, file_path):
        """Парсит email файл"""
        try:
            if file_path in self.processed_files:
                return None
                
            logger.info(f"Обработка файла: {file_path}")
            
            with open(file_path, 'rb') as f:
                msg = message_from_bytes(f.read(), policy=email.policy.default)
            
            subject = msg.get('subject', '')
            logger.info(f"Тема письма: {subject}")
            
            # Извлекаем информацию из темы
            backup_info = self.parse_subject(subject)
            if not backup_info:
                logger.warning("Не удалось извлечь информацию из темы")
                return None
            
            # Парсим тело письма
            body = self.get_email_body(msg)
            backup_info.update(self.parse_body(body))
            
            # Сохраняем в базу
            self.save_backup_report(backup_info, subject)
            
            self.processed_files.add(file_path)
            return backup_info
            
        except Exception as e:
            logger.error(f"Ошибка парсинга файла {file_path}: {e}")
            return None
    
    def parse_subject(self, subject):
        """Парсит тему письма"""
        # Пример: "vzdump backup status (sr-pve5.geltd.local): backup successful"
        
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
        """Парсит тело письма"""
        info = {
            'duration': None,
            'total_size': None,
            'error_message': None
        }
        
        try:
            lines = body.split('\n')
            
            for line in lines:
                line = line.strip()
                line_lower = line.lower()
                
                # Время выполнения
                if 'duration' in line_lower or 'time' in line_lower:
                    duration_match = re.search(r'(\d+:\d+:\d+)', line)
                    if duration_match:
                        info['duration'] = duration_match.group(1)
                
                # Размер
                elif 'size' in line_lower or 'total' in line_lower:
                    size_match = re.search(r'(\d+\.?\d*\s*[GMK]?B)', line, re.IGNORECASE)
                    if size_match:
                        info['total_size'] = size_match.group(1)
                
                # Ошибки
                elif 'error' in line_lower or 'failed' in line_lower:
                    if not info['error_message'] and len(line) > 10:
                        info['error_message'] = line[:200]
                        
        except Exception as e:
            logger.error(f"Ошибка парсинга тела письма: {e}")
        
        return info
    
    def save_backup_report(self, backup_info, subject):
        """Сохраняет отчет в базу"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
                subject[:500]
            ))
            
            conn.commit()
            logger.info(f"Сохранен бэкап: {backup_info['host_name']} - {backup_info['backup_status']}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

def main():
    """Основная функция"""
    logger.info("Запуск мониторинга почты Proxmox бэкапов...")
    
    try:
        processor = BackupProcessor()
        maildir_path = '/root/Maildir/cur'
        
        if not os.path.exists(maildir_path):
            logger.error(f"Директория не существует: {maildir_path}")
            return
        
        logger.info(f"Мониторинг директории: {maildir_path}")
        
        # Основной цикл
        while True:
            try:
                # Проверяем новые файлы
                for filename in os.listdir(maildir_path):
                    file_path = os.path.join(maildir_path, filename)
                    if os.path.isfile(file_path) and file_path not in processor.processed_files:
                        processor.parse_email_file(file_path)
                
                time.sleep(30)  # Проверяем каждые 30 секунд
                
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                time.sleep(60)
                
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
    