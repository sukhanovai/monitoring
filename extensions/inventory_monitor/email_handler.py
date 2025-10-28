"""
Обработчик писем с остатками товаров
"""

import os
from extensions.email_processor.base_handler import BaseEmailHandler

class InventoryEmailHandler(BaseEmailHandler):
    """Обработчик писем с остатками товаров"""
    
    def can_handle(self, email_data):
        """Определяет письма с остатками"""
        subject = email_data.get('subject', '').lower()
        has_attachments = len(email_data.get('attachments', [])) > 0
        
        inventory_indicators = [
            'остатки' in subject,
            'остаток' in subject,
            'склад' in subject,
            'inventory' in subject,
            'stock' in subject
        ]
        
        return any(inventory_indicators) and has_attachments
    
    def process(self, email_data):
        """Обрабатывает письма с остатками товаров"""
        try:
            # Сохраняем вложения
            for attachment in email_data.get('attachments', []):
                self.save_attachment(attachment)
            
            # Логируем получение
            self.logger.info(f"Получены остатки товаров: {len(email_data['attachments'])} вложений")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки остатков товаров: {e}")
    
    def save_attachment(self, attachment):
        """Сохраняет вложение для последующей обработки"""
        attachments_dir = '/opt/monitoring/data/email_attachments'
        os.makedirs(attachments_dir, exist_ok=True)
        
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{attachment['filename']}"
        filepath = os.path.join(attachments_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(attachment['data'])
        
        self.logger.info(f"Сохранено вложение: {filename}")
        