"""
Обработчик писем от Exiland Backup
"""

import re
from extensions.email_processor.base_handler import BaseEmailHandler

class ExilandBackupHandler(BaseEmailHandler):
    """Обработчик отчетов от Exiland Backup"""
    
    def can_handle(self, email_data):
        """Определяет Exiland Backup по теме"""
        subject = email_data.get('subject', '').lower()
        return 'exiland' in subject or 'ebackup' in subject
    
    def process(self, email_data):
        """Обрабатывает отчет Exiland Backup"""
        # Реализация для Exiland Backup
        pass
    