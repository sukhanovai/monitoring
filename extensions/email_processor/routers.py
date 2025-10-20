"""
Маршрутизатор писем к соответствующим обработчикам
"""

import logging
from typing import List, Optional

class EmailRouter:
    """Маршрутизирует письма к подходящим обработчикам"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.handlers = []
    
    def register_handler(self, handler):
        """Регистрирует обработчик"""
        self.handlers.append(handler)
        self.logger.info(f"Зарегистрирован обработчик: {handler.__class__.__name__}")
    
    def route_email(self, raw_email):
        """Маршрутизирует письмо к подходящему обработчику"""
        email_data = None
        processed = False
        
        for handler in self.handlers:
            try:
                # Первый обработчик извлекает данные
                if email_data is None:
                    email_data = handler.extract_email_data(raw_email)
                    if not email_data:
                        self.logger.error("Не удалось извлечь данные из email")
                        return False
                
                # Проверяем может ли обработчик работать с этим письмом
                if handler.can_handle(email_data):
                    self.logger.info(f"Обработчик {handler.__class__.__name__} принимает письмо")
                    handler.process(email_data)
                    processed = True
                    # Не прерываем - несколько обработчиков могут работать с одним письмом
                    
            except Exception as e:
                self.logger.error(f"Ошибка в обработчике {handler.__class__.__name__}: {e}")
                continue
        
        if processed:
            self.logger.info("Письмо успешно обработано")
        else:
            self.logger.warning("Не найден подходящий обработчик для письма")
        
        return processed
    