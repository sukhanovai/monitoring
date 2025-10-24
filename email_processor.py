# /opt/monitoring/email_processor.py

"""
Обработчик входящих писем для пользователя root
Упрощенная версия без ответов
"""

import sys
import os
import logging
import re
from email import message_from_string
from email.policy import default

# Добавляем путь для импорта наших модулей
sys.path.insert(0, '/opt/monitoring')

def setup_logging():
    """Настраивает логирование"""
    try:
        os.makedirs('/opt/monitoring/logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/monitoring/logs/email_processor.log'),
            ]
        )
        return logging.getLogger(__name__)
    except Exception as e:
        return logging.getLogger(__name__)

logger = setup_logging()

def parse_mbox_email(raw_email):
    """Парсит письмо в формате mbox который использует Postfix"""
    try:
        # Убираем строку "From ..." которую добавляет Postfix
        lines = raw_email.split('\n')
        if lines and lines[0].startswith('From '):
            email_content = '\n'.join(lines[1:])
        else:
            email_content = raw_email
        
        msg = message_from_string(email_content, policy=default)
        subject = msg.get('subject', 'Без темы')
        from_email = msg.get('from', 'Неизвестный отправитель')
        
        logger.info(f"📨 Письмо: {subject} от {from_email}")
        
        return msg, subject, from_email, email_content
        
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        return None, "Ошибка", "Неизвестно", raw_email

def main():
    """Основная функция обработки писем"""
    try:
        # Читаем все из STDIN
        raw_email = sys.stdin.read()
        
        if not raw_email or len(raw_email.strip()) < 10:
            return 0
            
        # Парсим письмо
        msg, subject, from_email, email_content = parse_mbox_email(raw_email)
        
        # Извлекаем оригинальное письмо Proxmox если это пересылка
        original_proxmox_email = extract_original_proxmox_email(email_content)
        
        if original_proxmox_email:
            logger.info("🎯 Обнаружено пересланное письмо от Proxmox")
            process_proxmox_backup_email(original_proxmox_email)
        else:
            # Проверяем прямое письмо от Proxmox
            is_proxmox = is_proxmox_email(subject, from_email, email_content)
            if is_proxmox:
                logger.info("🎯 Обнаружено прямое письмо от Proxmox")
                process_proxmox_backup_email(email_content)
        
        return 0  # Всегда возвращаем успех чтобы избежать ответов
        
    except Exception as e:
        logger.error(f"💥 Ошибка: {e}")
        return 0  # Всегда возвращаем успех чтобы избежать ответов

def extract_original_proxmox_email(raw_email):
    """Извлекает оригинальное письмо Proxmox из пересланного письма"""
    try:
        if 'vzdump backup status' in raw_email and 'sr-pve' in raw_email:
            patterns = [
                r'Content-Type: multipart/alternative;\s*boundary="----_=_NextPart_\d+_\d+"',
                r'------_=_NextPart_\d+_\d+',
                r'Subject: vzdump backup status',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, raw_email)
                if match:
                    return raw_email[match.start():]
        
        return None
    except Exception as e:
        return None

def is_proxmox_email(subject, from_email, raw_email):
    """Определяет, является ли письмо от Proxmox"""
    subject_lower = str(subject).lower()
    from_lower = str(from_email).lower()
    raw_lower = raw_email.lower()
    
    return ('vzdump backup status' in subject_lower or
            'proxmox' in subject_lower or
            'pve' in from_lower or
            'bup' in from_lower or
            'vzdump' in raw_lower)

def process_proxmox_backup_email(raw_email):
    """Обрабатывает письмо с бэкапом от Proxmox"""
    try:
        from extensions.email_processor.core import EmailProcessorCore
        processor = EmailProcessorCore()
        result = processor.process_email(raw_email)
        
        if result:
            logger.info("✅ Письмо обработано и сохранено в базу")
        else:
            logger.warning("⚠️ Письмо не обработано")
            
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
    