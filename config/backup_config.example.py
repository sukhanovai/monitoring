"""
ПРИМЕР конфигурационного файла для мониторинга бэкапов
Скопируйте этот файл в backup_config.py и заполните реальными данными
"""

# Сопоставление имен Proxmox хостов с IP адресами
PROXMOX_HOSTS = {
    'pve1': '192.168.30.1',
    'pve2': '192.168.30.2', 
    # ... заполните реальными IP ваших серверов
    'bup1': '192.168.20.1',
    'bup2': '192.168.20.2',
}

# Паттерны для определения Proxmox писем в теме
PROXMOX_SUBJECT_PATTERNS = [
    r'vzdump backup status',
    r'proxmox backup',
]

# Паттерны для определения Proxmox писем в теме
PROXMOX_SUBJECT_PATTERNS = [
    r'vzdump backup status',
    r'proxmox backup',
    r'pve\d+ backup',
    r'bup\d+ backup',
]

# Паттерны для извлечения имен хостов из темы письма
HOSTNAME_PATTERNS = [
    r'\(([^)]+)\)',  # Извлекает текст в скобках: (pve13.geltd.local)
    r'from\s+([^\s]+)',  # Извлекает после "from"
    r'host\s+([^\s]+)',  # Извлекает после "host"
]

# Статусы бэкапов и их нормализация
BACKUP_STATUS_MAP = {
    'backup successful': 'success',
    'successful': 'success', 
    'ok': 'success',
    'completed': 'success',
    'finished': 'success',
    'backup failed': 'failed',
    'failed': 'failed',
    'error': 'failed',
    'errors': 'failed',
    'warning': 'warning',
    'partial': 'partial',
}

# Настройки базы данных
DATABASE_CONFIG = {
    'backups_db': '/opt/monitoring/data/backups.db',
    'max_backup_age_days': 90,  # Хранить данные 90 дней
}
