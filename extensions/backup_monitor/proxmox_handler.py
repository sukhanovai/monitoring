"""
Обработчик писем с отчетами о бэкапах Proxmox
"""

import re
import sqlite3
from datetime import datetime
from extensions.email_processor.base_handler import BaseEmailHandler

class ProxmoxBackupHandler(BaseEmailHandler):
    """Обработчик отчетов о бэкапах от Proxmox"""
    
    def can_handle(self, email_data):
        """Определяет Proxmox бэкапы по теме и отправителю"""
        subject = email_data.get('subject', '').lower()
        from_email = email_data.get('from_email', '').lower()
        
        # Критерии для Proxmox бэкапов
        proxmox_indicators = [
            'backup' in subject,
            'proxmox' in subject,
            'pve' in subject,
            'katok@202020.ru' in from_email,
            any(host in subject for host in ['pve1', 'pve2', 'pve3', 'pve4', 'pve5'])
        ]
        
        return any(proxmox_indicators)
    
    def process(self, email_data):
        """Обрабатывает отчет о бэкапах Proxmox"""
        try:
            backup_info = self.parse_proxmox_report(email_data)
            self.save_to_database(backup_info, email_data)
            self.logger.info(f"Обработан отчет Proxmox от {backup_info['host_name']}")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки Proxmox отчета: {e}")
    
    def parse_proxmox_report(self, email_data):
        """Парсит отчет Proxmox"""
        body = email_data['body']
        subject = email_data['subject']
        
        # Извлекаем имя хоста
        host_match = re.search(r'(pve\d+)', subject, re.IGNORECASE)
        host_name = host_match.group(1) if host_match else 'unknown'
        
        # Парсим информацию о VM
        backups = []
        for line in body.split('\n'):
            line = line.strip()
            
            # Различные форматы Proxmox отчетов
            patterns = [
                r'VM\s+(\d+).*?:\s*([OK|ERROR]+).*?(\d+\.?\d*[GMK]B)?',
                r'(\d+):.*?(ok|success|error|fail).*?(\d+\.?\d*[GMK]B)?',
                r'TASK\s+OK|ERROR',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    vm_data = self.extract_vm_data(match, line)
                    if vm_data:
                        backups.append(vm_data)
                    break
        
        return {
            'host_name': host_name,
            'backups': backups,
            'total_count': len(backups),
            'success_count': len([b for b in backups if b['status'] == 'success']),
            'failed_count': len([b for b in backups if b['status'] == 'failed'])
        }
    
    def extract_vm_data(self, match, line):
        """Извлекает данные о VM из строки"""
        # Реализация парсинга конкретных форматов
        # ...
        pass
    
    def save_to_database(self, backup_info, email_data):
        """Сохраняет в базу бэкапов"""
        conn = sqlite3.connect('/opt/monitoring/data/backups.db')
        cursor = conn.cursor()
        
        # Сохранение данных
        # ...
        
        conn.commit()
        conn.close()
        