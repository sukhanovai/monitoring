#!/usr/bin/env python3
"""
Мониторинг почтового ящика для обработки писем о бэкапах
"""

import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from extensions.email_processor.proxmox_handler import ProxmoxBackupHandler

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

class MaildirHandler(FileSystemEventHandler):
    """Обработчик событий в Maildir"""
    
    def __init__(self):
        self.backup_handler = ProxmoxBackupHandler()
        self.processed_files = set()
    
    def on_created(self, event):
        """Обрабатывает создание новых файлов"""
        if not event.is_directory:
            self.process_email_file(event.src_path)
    
    def on_moved(self, event):
        """Обрабатывает перемещение файлов"""
        if not event.is_directory:
            self.process_email_file(event.dest_path)
    
    def process_email_file(self, file_path):
        """Обрабатывает email файл"""
        try:
            if file_path in self.processed_files:
                return
                
            logger.info(f"Обнаружен новый файл: {file_path}")
            
            # Ждем пока файл полностью запишется
            time.sleep(2)
            
            # Парсим письмо
            result = self.backup_handler.parse_email_file(file_path)
            
            if result:
                logger.info(f"Обработан бэкап от {result['host_name']}: {result['backup_status']}")
                self.processed_files.add(file_path)
            else:
                logger.warning(f"Не удалось обработать файл: {file_path}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки файла {file_path}: {e}")

def start_mail_monitor():
    """Запускает мониторинг почтового ящика"""
    maildir_path = '/root/Maildir/cur'
    
    if not os.path.exists(maildir_path):
        logger.error(f"Директория не существует: {maildir_path}")
        return
    
    event_handler = MaildirHandler()
    observer = Observer()
    observer.schedule(event_handler, maildir_path, recursive=False)
    
    logger.info(f"Запуск мониторинга директории: {maildir_path}")
    observer.start()
    
    try:
        # Обрабатываем существующие файлы
        for filename in os.listdir(maildir_path):
            file_path = os.path.join(maildir_path, filename)
            if os.path.isfile(file_path):
                event_handler.process_email_file(file_path)
        
        # Бесконечный цикл
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    start_mail_monitor()
    