"""
Базовый класс для всех обработчиков писем
"""

import abc
import logging
from datetime import datetime
from email import message_from_string
from email.policy import default

class BaseEmailHandler(abc.ABC):
    """Абстрактный базовый класс для обработчиков email"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abc.abstractmethod
    def can_handle(self, email_data):
        """Проверяет, может ли обработчик работать с этим письмом"""
        pass
    
    @abc.abstractmethod
    def process(self, email_data):
        """Обрабатывает письмо"""
        pass
    
    def extract_email_data(self, raw_email):
        """Извлекает структурированные данные из сырого email"""
        try:
            msg = message_from_string(raw_email, policy=default)
            
            # Базовые поля email
            email_data = {
                'subject': msg.get('subject', '').strip(),
                'from_email': msg.get('from', '').strip(),
                'date': msg.get('date', '').strip(),
                'to': msg.get('to', '').strip(),
                'body': '',
                'attachments': [],
                'raw_email': raw_email,
                'received_at': datetime.now().isoformat()
            }
            
            # Извлекаем тело письма и вложения
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" in content_disposition:
                        # Обработка вложений
                        filename = part.get_filename()
                        if filename:
                            attachment_data = {
                                'filename': filename,
                                'content_type': content_type,
                                'data': part.get_payload(decode=True),
                                'size': len(part.get_payload(decode=True))
                            }
                            email_data['attachments'].append(attachment_data)
                    
                    elif content_type == "text/plain":
                        email_data['body'] = part.get_content()
            else:
                email_data['body'] = msg.get_content()
            
            return email_data
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения данных из email: {e}")
            return None
        