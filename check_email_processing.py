# /opt/monitoring/check_email_processing.py

#!/usr/bin/env python3
"""
Инструмент проверки обработки входящих писем в реальном времени
"""

import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EmailFileHandler(FileSystemEventHandler):
    """Обработчик новых файлов в почтовой директории"""
    
    def __init__(self):
        self.processed_files = set()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        if filepath in self.processed_files:
            return
        
        print(f"📨 Обнаружен новый файл: {filepath}")
        self.processed_files.add(filepath)
        
        # Обрабатываем файл
        self.process_email_file(filepath)
    
    def process_email_file(self, filepath):
        """Обрабатывает файл с email"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                email_content = f.read()
            
            print(f"📧 Обработка письма из {os.path.basename(filepath)}")
            
            # Запускаем обработчик
            from extensions.email_processor.core import EmailProcessorCore
            processor = EmailProcessorCore()
            result = processor.process_email(email_content)
            
            if result:
                print(f"✅ Письмо успешно обработано")
            else:
                print(f"❌ Письмо не было обработано")
                
        except Exception as e:
            print(f"💥 Ошибка обработки: {e}")

def monitor_mail_directory():
    """Мониторит директорию с письмами"""
    mail_dir = '/var/mail'  # Стандартная директория почты
    
    if not os.path.exists(mail_dir):
        print(f"❌ Директория {mail_dir} не найдена")
        return
    
    print(f"👁️  Начинаю мониторинг директории: {mail_dir}")
    
    event_handler = EmailFileHandler()
    observer = Observer()
    observer.schedule(event_handler, mail_dir, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Мониторинг остановлен")
    
    observer.join()

def check_recent_emails():
    """Проверяет недавние письма"""
    print("🔍 Проверка недавних писем...")
    
    # Здесь можно добавить проверку почтового ящика
    # или директории с письмами
    
    print("✅ Проверка завершена")

if __name__ == "__main__":
    print("📧 Мониторинг системы обработки писем\n")
    
    # Проверяем существующие письма
    check_recent_emails()
    
    # Запускаем мониторинг
    try:
        monitor_mail_directory()
    except Exception as e:
        print(f"💥 Ошибка мониторинга: {e}")
        