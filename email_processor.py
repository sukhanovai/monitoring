#!/usr/bin/env python3
"""
Обработчик входящих писем для пользователя root
"""

import sys
import os
import logging
import tempfile
from email import message_from_string
from email.policy import default

# Добавляем путь для импорта наших модулей
sys.path.insert(0, '/opt/monitoring')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/monitoring/logs/email_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция обработки писем"""
    try:
        # Читаем все из STDIN
        raw_email = sys.stdin.read()
        
        if not raw_email or len(raw_email.strip()) < 10:
            logger.warning("Получено пустое или слишком короткое письмо")
            return 0
            
        logger.info(f"📨 Получено письмо размером {len(raw_email)} байт")
        
        # Сохраняем письмо во временный файл для диагностики
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.eml') as f:
            f.write(raw_email)
            temp_filename = f.name
            logger.info(f"💾 Письмо сохранено во временный файл: {temp_filename}")
        
        # Парсим письмо для получения информации
        try:
            msg = message_from_string(raw_email, policy=default)
            subject = msg.get('subject', 'Без темы')
            from_email = msg.get('from', 'Неизвестный отправитель')
            
            logger.info(f"📧 Письмо от: {from_email}")
            logger.info(f"📝 Тема: {subject}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга письма: {e}")
            subject = "Ошибка парсинга"
            from_email = "Неизвестно"
        
        # Проверяем, является ли письмо от Proxmox
        if is_proxmox_email(subject, from_email, raw_email):
            logger.info("🎯 Обнаружено письмо от Proxmox, запускаем обработку")
            process_proxmox_backup_email(raw_email, subject)
        else:
            logger.info("⏭️ Письмо не от Proxmox, пропускаем")
            
        # Удаляем временный файл
        os.unlink(temp_filename)
        
        return 0  # Успешное завершение
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в обработчике: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1  # Ошибка

def is_proxmox_email(subject, from_email, raw_email):
    """Определяет, является ли письмо от Proxmox"""
    subject_lower = subject.lower()
    from_lower = from_email.lower()
    
    # Ключевые признаки Proxmox писем
    proxmox_indicators = [
        'vzdump backup status' in subject_lower,
        'proxmox' in subject_lower,
        'pve' in from_lower,
        'bup' in from_lower,
        'root@pve' in from_lower,
        'root@bup' in from_lower,
        'sr-pve' in from_lower,
        'sr-bup' in from_lower,
        'vzdump' in subject_lower,
        'backup' in subject_lower and 'status' in subject_lower
    ]
    
    # Дополнительная проверка по домену
    domain_indicators = [
        'localdomain' in from_lower,
        'geltd.local' in from_lower,
        'pve' in from_lower,
        'bup' in from_lower
    ]
    
    result = any(proxmox_indicators) or any(domain_indicators)
    logger.info(f"🔍 Проверка Proxmox письма: {result} (индикаторы: {proxmox_indicators})")
    
    return result

def process_proxmox_backup_email(raw_email, subject):
    """Обрабатывает письмо с бэкапом от Proxmox"""
    try:
        from extensions.email_processor.core import EmailProcessorCore
        
        processor = EmailProcessorCore()
        result = processor.process_email(raw_email)
        
        if result:
            logger.info("✅ Письмо с бэкапом успешно обработано и сохранено в базу")
            
            # Логируем успешную обработку
            log_successful_processing(subject)
        else:
            logger.warning("⚠️ Письмо с бэкапом не было обработано обработчиком")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки письма с бэкапом: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def log_successful_processing(subject):
    """Логирует успешную обработку письма"""
    try:
        log_file = '/opt/monitoring/logs/processed_emails.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Обработано: {subject}\n")
    except Exception as e:
        logger.error(f"Ошибка логирования: {e}")

if __name__ == "__main__":
    sys.exit(main())