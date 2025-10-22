# /opt/monitoring/email_processor.py

#!/usr/bin/env python3
"""
Обработчик входящих писем для пользователя root
"""

import sys
import os
import logging
import tempfile
import re
from email import message_from_string
from email.policy import default

# Добавляем путь для импорта наших модулей
sys.path.insert(0, '/opt/monitoring')

def setup_logging():
    """Настраивает логирование с обработкой ошибок прав доступа"""
    try:
        # Создаем директорию логов если не существует
        os.makedirs('/opt/monitoring/logs', exist_ok=True)
        
        # Настраиваем базовое логирование в файл
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/monitoring/logs/email_processor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    except Exception as e:
        # Фолбэк на консольное логирование
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка настройки логирования: {e}")
        return logger

logger = setup_logging()

def main():
    """Основная функция обработки писем"""
    try:
        # Читаем все из STDIN
        raw_email = sys.stdin.read()
        
        if not raw_email or len(raw_email.strip()) < 10:
            logger.warning("Получено пустое или слишком короткое письмо")
            return 0
            
        logger.info(f"📨 Получено письмо размером {len(raw_email)} байт")
        
        # Парсим письмо для получения информации
        try:
            msg = message_from_string(raw_email, policy=default)
            subject = msg.get('subject', 'Без темы')
            from_email = msg.get('from', 'Неизвестный отправитель')
            to_email = msg.get('to', 'Неизвестный получатель')
            
            logger.info(f"📧 Письмо от: {from_email}")
            logger.info(f"📨 Письмо к: {to_email}") 
            logger.info(f"📝 Тема: {subject}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга письма: {e}")
            subject = "Ошибка парсинга"
            from_email = "Неизвестно"
            to_email = "Неизвестно"
        
        # Проверяем, является ли письмо пересланным письмом от Proxmox
        original_proxmox_email = extract_original_proxmox_email(raw_email)
        
        if original_proxmox_email:
            logger.info("🎯 Обнаружено пересланное письмо от Proxmox, извлекаем оригинал")
            process_proxmox_backup_email(original_proxmox_email, "Пересланное: " + subject, from_email)
        else:
            # Проверяем, является ли письмо прямым письмом от Proxmox
            is_proxmox = is_proxmox_email(subject, from_email, raw_email)
            
            if is_proxmox:
                logger.info("🎯 Обнаружено прямое письмо от Proxmox, запускаем обработку")
                process_proxmox_backup_email(raw_email, subject, from_email)
            else:
                logger.info("⏭️ Письмо не от Proxmox, пропускаем")
                # Логируем непрочитанные письма для отладки
                log_unknown_email(subject, from_email, raw_email)
        
        return 0  # Успешное завершение
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в обработчике: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1  # Ошибка

def extract_original_proxmox_email(raw_email):
    """Извлекает оригинальное письмо Proxmox из пересланного письма"""
    try:
        # Ищем признаки пересланного письма от Proxmox
        if 'vzdump backup status' in raw_email and 'sr-pve' in raw_email:
            logger.info("🔍 Обнаружены признаки пересланного Proxmox письма")
            
            # Пытаемся извлечь оригинальное письмо
            # Ищем начало оригинального письма (обычно после заголовков пересылки)
            patterns = [
                # Паттерн для писем с полными заголовками
                r'Content-Type: multipart/alternative;\s*boundary="----_=_NextPart_\d+_\d+"',
                # Паттерн для начала MIME части
                r'------_=_NextPart_\d+_\d+',
                # Паттерн для начала письма с Subject
                r'Subject: vzdump backup status',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, raw_email)
                if match:
                    start_pos = match.start()
                    original_email = raw_email[start_pos:]
                    logger.info(f"✅ Оригинальное письмо извлечено с позиции {start_pos}")
                    return original_email
            
            # Если не нашли по паттернам, пробуем извлечь по ключевым словам
            if 'vzdump backup status' in raw_email and 'From: vzdump backup tool' in raw_email:
                # Находим начало оригинального письма
                start_marker = 'From: vzdump backup tool'
                start_pos = raw_email.find(start_marker)
                if start_pos != -1:
                    # Находим конец письма (перед следующими заголовками пересылки или концом)
                    end_markers = [
                        '\nResent-',
                        '\nReceived:',
                        '\n------',
                        '\n--'
                    ]
                    end_pos = len(raw_email)
                    for marker in end_markers:
                        pos = raw_email.find(marker, start_pos + 100)  # Ищем после начала
                        if pos != -1 and pos < end_pos:
                            end_pos = pos
                    
                    original_email = raw_email[start_pos:end_pos].strip()
                    logger.info(f"✅ Оригинальное письмо извлечено по маркерам")
                    return original_email
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Ошибка извлечения оригинального письма: {e}")
        return None

def is_proxmox_email(subject, from_email, raw_email):
    """Определяет, является ли письмо от Proxmox"""
    subject_lower = str(subject).lower()
    from_lower = str(from_email).lower()
    raw_lower = raw_email.lower()
    
    # Ключевые признаки Proxmox писем в теме
    subject_indicators = [
        'vzdump backup status' in subject_lower,
        'proxmox' in subject_lower,
        'vzdump' in subject_lower,
        'backup' in subject_lower and 'status' in subject_lower,
    ]
    
    # Ключевые признаки в отправителе
    from_indicators = [
        'pve' in from_lower,
        'bup' in from_lower,
        'root@pve' in from_lower,
        'root@bup' in from_lower,
        'sr-pve' in from_lower,
        'sr-bup' in from_lower,
        'localdomain' in from_lower,
    ]
    
    # Ключевые признаки в теле письма
    body_indicators = [
        'vzdump' in raw_lower,
        'proxmox' in raw_lower,
        'backup' in raw_lower,
        'vm' in raw_lower and 'successful' in raw_lower,
    ]
    
    # Проверяем различные комбинации
    result = (any(subject_indicators) or 
              any(from_indicators) or 
              any(body_indicators))
    
    # Детальное логирование
    logger.info(f"🔍 Проверка Proxmox письма:")
    logger.info(f"   Тема: {subject_lower}")
    logger.info(f"   От: {from_lower}")
    logger.info(f"   Признаки темы: {[i for i in subject_indicators if i]}")
    logger.info(f"   Признаки отправителя: {[i for i in from_indicators if i]}")
    logger.info(f"   Признаки тела: {[i for i in body_indicators if i]}")
    logger.info(f"   Результат: {result}")
    
    return result

def log_unknown_email(subject, from_email, raw_email):
    """Логирует непрочитанные письма для отладки"""
    try:
        log_file = '/opt/monitoring/logs/unknown_emails.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"\n{'='*50}\n")
            f.write(f"Время: {timestamp}\n")
            f.write(f"Тема: {subject}\n")
            f.write(f"От: {from_email}\n")
            f.write(f"Содержимое (первые 500 символов):\n{raw_email[:500]}\n")
            f.write(f"{'='*50}\n")
        logger.info(f"📝 Неизвестное письмо записано в лог: {log_file}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось записать неизвестное письмо в лог: {e}")

def process_proxmox_backup_email(raw_email, subject, from_email):
    """Обрабатывает письмо с бэкапом от Proxmox"""
    try:
        from extensions.email_processor.core import EmailProcessorCore
        
        processor = EmailProcessorCore()
        result = processor.process_email(raw_email)
        
        if result:
            logger.info("✅ Письмо с бэкапом успешно обработано и сохранено в базу")
            
            # Логируем успешную обработку
            log_successful_processing(subject, from_email)
            
            # Проверяем что данные действительно сохранились
            check_database_after_processing()
        else:
            logger.warning("⚠️ Письмо с бэкапом не было обработано обработчиком")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки письма с бэкапом: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def log_successful_processing(subject, from_email):
    """Логирует успешную обработку письма"""
    try:
        log_file = '/opt/monitoring/logs/processed_emails.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} - Обработано: {subject} (от: {from_email})\n")
        logger.info(f"📝 Запись добавлена в лог: {log_file}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось записать в лог processed_emails: {e}")

def check_database_after_processing():
    """Проверяет базу данных после обработки"""
    try:
        from extensions.backup_monitor.bot_handler import BackupMonitorBot
        
        bot = BackupMonitorBot()
        today_status = bot.get_today_status()
        
        logger.info(f"📊 Проверка базы данных: {len(today_status)} записей за сегодня")
        
        for host, status, count, last_report in today_status:
            logger.info(f"   🏠 {host}: {status} (отчетов: {count})")
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки базы данных: {e}")

if __name__ == "__main__":
    sys.exit(main())
    