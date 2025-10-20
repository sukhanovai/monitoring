"""
Ядро системы обработки писем
"""

import sys
import os
import logging
from .routers import EmailRouter

# Добавляем путь для импорта расширений
sys.path.insert(0, '/opt/monitoring')

class EmailProcessorCore:
    """Основной класс обработки входящих писем"""
    
    def __init__(self):
        self.setup_logging()
        self.router = EmailRouter()
        self.setup_handlers()
    
    def setup_logging(self):
        """Настройка логирования"""
        os.makedirs('/opt/monitoring/logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/opt/monitoring/logs/email_processor.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_handlers(self):
        """Регистрация всех обработчиков"""
        try:
            # Динамическая регистрация обработчиков из расширений
            from extensions.backup_monitor.proxmox_handler import ProxmoxBackupHandler
            from extensions.backup_monitor.exiland_handler import ExilandBackupHandler
            from extensions.zfs_monitor.zfs_handler import ZFSStatusHandler
            from extensions.inventory_monitor.email_handler import InventoryEmailHandler
            
            self.router.register_handler(ProxmoxBackupHandler())
            self.router.register_handler(ExilandBackupHandler())
            self.router.register_handler(ZFSStatusHandler())
            self.router.register_handler(InventoryEmailHandler())
            
            self.logger.info("Все обработчики зарегистрированы")
            
        except ImportError as e:
            self.logger.warning(f"Не все обработчики доступны: {e}")
    
    def process_email(self, raw_email):
        """Основной метод обработки письма"""
        if not raw_email or not raw_email.strip():
            self.logger.error("Получено пустое письмо")
            return False
        
        self.logger.info("Начало обработки письма")
        return self.router.route_email(raw_email)

def main():
    """Точка входа для вызова из Postfix"""
    processor = EmailProcessorCore()
    raw_email = sys.stdin.read()
    
    success = processor.process_email(raw_email)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
    