"""
Server Monitoring System v2.4.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ШАБЛОН КОНФИГУРАЦИИ - скопируйте в config.py и настройте под свои нужды
"""

import os
from datetime import time as dt_time

# === БАЗОВЫЕ НАСТРОЙКИ ===
# 🔐 НАСТРОЙКИ TELEGRAM (ОБЯЗАТЕЛЬНО)
# Получите токен у @BotFather и Chat ID через /getUpdates
TELEGRAM_TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN_ЗДЕСЬ"
CHAT_IDS = ["ВАШ_CHAT_ID_ЗДЕСЬ"]  # Можно несколько через запятую

# === ИНТЕРВАЛЫ ПРОВЕРОК ===
CHECK_INTERVAL = 60  # секунды между проверками доступности
MAX_FAIL_TIME = 900  # 15 минут в секундах до отправки алерта

# === ВРЕМЕННЫЕ НАСТРОЙКИ ===
SILENT_START = 20  # 20:00 - начало тихого режима
SILENT_END = 9     # 9:00 - конец тихого режима
DATA_COLLECTION_TIME = dt_time(8, 30)  # Сбор данных для утреннего отчета

# === НАСТРОЙКИ РЕСУРСОВ ===
RESOURCE_CHECK_INTERVAL = 1800  # 30 минут в секундах между проверками ресурсов
RESOURCE_ALERT_INTERVAL = 1800  # 30 минут между повторными алертами

# Пороги для предупреждений
RESOURCE_THRESHOLDS = {
    "cpu_warning": 80,      # Предупреждение при загрузке CPU > 80%
    "cpu_critical": 90,     # Критично при загрузке CPU > 90%
    "ram_warning": 85,      # Предупреждение при использовании RAM > 85%
    "ram_critical": 95,     # Критично при использовании RAM > 95%
    "disk_warning": 80,     # Предупреждение при использовании диска > 80%
    "disk_critical": 90     # Критично при использовании диска > 90%
}

# Пороги для автоматических алертов
RESOURCE_ALERT_THRESHOLDS = {
    "cpu_alert": 99,        # Алерт при загрузке CPU (2 проверки подряд)
    "ram_alert": 99,        # Алерт при использовании RAM (2 проверки подряд)
    "disk_alert": 95,       # Алерт при использовании диска (1 проверка)
    "check_consecutive": 2  # Количество последовательных проверок для алерта
}

# === АУТЕНТИФИКАЦИЯ LINUX ===
# Настройки SSH подключения к Linux серверам
SSH_KEY_PATH = "/root/.ssh/id_rsa"  # Путь к приватному SSH ключу
SSH_USERNAME = "root"               # Пользователь для SSH подключения

# === УНИФИЦИРОВАННЫЕ УЧЕТНЫЕ ДАННЫЕ WINDOWS ===
# Базовые учетные данные для всех типов Windows серверов
WINDOWS_CREDENTIALS = [
    {"username": "Администратор", "password": "ВАШ_ПАРОЛЬ"},
    {"username": "Administrator", "password": "ВАШ_ПАРОЛЬ"},
    {"username": "admin", "password": "ВАШ_ПАРОЛЬ"},
    # Добавьте свои учетные данные здесь
]

# Конфигурация Windows серверов с наследованием учетных данных
WINDOWS_SERVER_CONFIGS = {
    "windows_2025": {
        "servers": ["192.168.1.10", "192.168.1.11"],
        "credentials": WINDOWS_CREDENTIALS[:2]  # Только первые 2 варианта
    },
    "domain_servers": {
        "servers": ["192.168.1.12", "192.168.1.13"],
        "credentials": [WINDOWS_CREDENTIALS[0]]  # Доменные учетки
    },
    "admin_servers": {
        "servers": ["192.168.1.14"],
        "credentials": WINDOWS_CREDENTIALS  # Все варианты
    },
    "standard_windows": {
        "servers": ["192.168.1.15", "192.168.1.16"],
        "credentials": WINDOWS_CREDENTIALS  # Все варианты
    }
}

# Обратная совместимость для старого кода
WINDOWS_SERVER_CREDENTIALS = WINDOWS_SERVER_CONFIGS
WINRM_CONFIGS = WINDOWS_CREDENTIALS

# === КОНФИГУРАЦИЯ СЕРВЕРОВ ===
# ⚠️ ОСНОВНАЯ КОНФИГУРАЦИЯ СЕРВЕРОВ (ОБЯЗАТЕЛЬНО)
SERVER_CONFIG = {
    "windows_servers": {
        # "IP-адрес": "Название сервера"
        "192.168.1.10": "SRV-WIN-01",
        "192.168.1.11": "SRV-WIN-02",
    },
    
    "linux_servers": {
        # "IP-адрес": "Название сервера"  
        "192.168.1.20": "SRV-LINUX-01",
        "192.168.1.21": "SRV-LINUX-02",
    },
    
    "ping_servers": {
        # Серверы только для проверки ping
        "192.168.1.30": "NETWORK-SWITCH",
    }
}

# Автоматическая генерация списков IP для обратной совместимости
RDP_SERVERS = list(SERVER_CONFIG["windows_servers"].keys())
SSH_SERVERS = list(SERVER_CONFIG["linux_servers"].keys()) 
PING_SERVERS = list(SERVER_CONFIG["ping_servers"].keys())

# === УНИФИЦИРОВАННЫЕ ТАЙМАУТЫ ===
SERVER_TIMEOUTS = {
    "windows_2025": 35,      # Таймаут для Windows Server 2025
    "domain_servers": 20,    # Таймаут для доменных серверов
    "admin_servers": 25,     # Таймаут для серверов с Admin
    "standard_windows": 30,  # Таймаут для обычных Windows
    "linux": 15,             # Таймаут для Linux серверов
    "ping": 10,              # Таймаут для ping проверок
    "port_check": 5,         # Таймаут для проверки портов
    "ssh": 15                # Таймаут для SSH подключений
}

# === ВЕБ-ИНТЕРФЕЙС ===
WEB_PORT = 5000    # Порт для веб-интерфейса
WEB_HOST = '0.0.0.0'  # Хост для веб-интерфейса

# === ФАЙЛЫ ДАННЫХ ===
DATA_DIR = "/opt/monitoring/data"  # Директория для данных
STATS_FILE = os.path.join(DATA_DIR, "monitoring_stats.json")  # Статистика
BACKUP_DB_FILE = os.path.join(DATA_DIR, "backups.db")  # База данных бэкапов

# Создаем директорию для данных
os.makedirs(DATA_DIR, exist_ok=True)

# === КОНФИГУРАЦИЯ PROXMOX БЭКАПОВ ===
# Настройки для мониторинга бэкапов Proxmox
PROXMOX_HOSTS = {
    # Основные Proxmox серверы
    'pve1': '192.168.1.100',
    'pve2': '192.168.1.101',
    
    # Бэкап серверы
    'backup1': '192.168.1.200',
    'backup2': '192.168.1.201',
    
    # Внешние серверы (пример)
    'external-pve': '195.208.128.5',
}

# Специальные настройки для хостов с одинаковыми IP
DUPLICATE_IP_HOSTS = {
    '95.170.153.118': ['pve-rubicon', 'pve2-rubicon']  # Пример
}

HOSTNAME_ALIASES = {
    'pve1': ['pve1', 'proxmox1', 'main-pve'],
    'pve2': ['pve2', 'proxmox2', 'backup-pve'],
}

# === УНИФИЦИРОВАННЫЕ ПАТТЕРНЫ ДЛЯ БЭКАПОВ ===
BACKUP_PATTERNS = {
    "proxmox_subject": [
        r'vzdump backup status',
        r'proxmox backup',
        r'pve\d+ backup', 
        r'bup\d+ backup',
    ],
    
    "hostname_extraction": [
        r'\(([^)]+)\)',
        r'from\s+([^\s]+)', 
        r'host\s+([^\s]+)',
    ],
    
    "database": {
        "company": [
            r'sr-bup (\w+) dump complete',
            r'(\w+)_dump complete', 
            r'dump (\w+) complete',
        ],
        "barnaul": [
            r'cobian BRN backup (\w+), errors:(\d+)'
        ],
        "client": [
            r'kc-1c (\w+) dump complete',
            r'rubicon-1c (\w+) dump complete' 
        ],
        "yandex": [
            r'yandex (\w+) backup'
        ]
    }
}

# Статусы бэкапов
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
    'partial': 'partial'
}

# === КОНФИГУРАЦИЯ БАЗ ДАННЫХ ===
# Настройки для мониторинга бэкапов баз данных
DATABASE_CONFIG = {
    "company": {
        # "имя_в_логе": "Отображаемое имя"
        "acc30_ge": "ACC30 ГЕ",
        "acc30_np": "ACC30 НП",
        "hrm31_ge": "HRM31 ГЕ",
        "wms": "WMS система",
    },
    
    "barnaul": {
        "1c_smb": "1C SMB Барнаул",
        "doc_nas": "Документы NAS", 
    },
    
    "client": {
        "unf": "УНФ Клиент",
        "zup": "ЗУП Клиент",
    },
    
    "yandex": {
        "RUBIKON": "Рубикон",
        "KC": "Клиентский центр",
    }
}

# Обратная совместимость для старого кода
BACKUP_DATABASE_CONFIG = {
    'backups_db': BACKUP_DB_FILE,
    'max_backup_age_days': 90
}

DATABASE_BACKUP_CONFIG = DATABASE_CONFIG

# === УТИЛИТЫ КОНФИГУРАЦИИ ===

def get_windows_servers_by_type(server_type):
    """Получить серверы Windows по типу"""
    return WINDOWS_SERVER_CONFIGS.get(server_type, {}).get('servers', [])

def get_all_windows_servers():
    """Получить все Windows серверы"""
    all_servers = []
    for config in WINDOWS_SERVER_CONFIGS.values():
        all_servers.extend(config['servers'])
    return list(set(all_servers))  # Убираем дубликаты

def get_server_timeout(server_type, default=15):
    """Получить таймаут для типа сервера"""
    return SERVER_TIMEOUTS.get(server_type, default)

def is_proxmox_server(ip):
    """Проверяет, является ли сервер Proxmox"""
    return (ip.startswith("192.168.30.") or
           ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])

# === ОБРАТНАЯ СОВМЕСТИМОСТЬ ДЛЯ БЭКАПОВ ===

# Старая структура для совместимости с существующим кодом
DATABASE_BACKUP_CONFIG = {
    "company_databases": DATABASE_CONFIG["company"],
    "barnaul_backups": DATABASE_CONFIG["barnaul"],
    "client_databases": DATABASE_CONFIG["client"],
    "yandex_backups": DATABASE_CONFIG["yandex"],
    "backups_db": BACKUP_DB_FILE,
    "max_backup_age_days": 90
}

# Псевдонимы для полной совместимости
BACKUP_DATABASE_CONFIG = DATABASE_BACKUP_CONFIG

# === НАСТРОЙКИ РАСШИРЕНИЙ ===
# Расширения включаются/выключаются автоматически через менеджер расширений
# Настройки ниже используются как значения по умолчанию

# === ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ===

# Настройки логирования
DEBUG_MODE = False  # Включить детальное логирование для отладки

# Настройки почтового мониторинга (для бэкапов)
MAIL_MONITOR_CONFIG = {
    'imap_server': 'imap.yandex.ru',
    'imap_port': 993,
    'email': 'your-email@yandex.ru',
    'password': 'your-app-password',
    'folder': 'INBOX',
    'check_interval': 300  # 5 минут между проверками почты
}

# === ПРОВЕРКА КОНФИГУРАЦИИ ===
def validate_config():
    """Проверяет корректность конфигурации"""
    errors = []
    
    # Проверка обязательных настроек
    if TELEGRAM_TOKEN == "ВАШ_TELEGRAM_BOT_TOKEN_ЗДЕСЬ":
        errors.append("Не настроен TELEGRAM_TOKEN")
    
    if not CHAT_IDS or CHAT_IDS[0] == "ВАШ_CHAT_ID_ЗДЕСЬ":
        errors.append("Не настроены CHAT_IDS")
    
    # Проверка серверов
    if not SERVER_CONFIG["windows_servers"] and not SERVER_CONFIG["linux_servers"]:
        errors.append("Не настроены серверы для мониторинга")
    
    # Проверка SSH ключа
    if not os.path.exists(SSH_KEY_PATH):
        errors.append(f"SSH ключ не найден: {SSH_KEY_PATH}")
    
    return errors

# Автопроверка при импорте
if __name__ != "config":
    config_errors = validate_config()
    if config_errors:
        print("❌ Ошибки конфигурации:")
        for error in config_errors:
            print(f"   - {error}")
        print("\n⚠️  Отредактируйте config.py перед запуском системы")
    else:
        print("✅ Конфигурация загружена успешно")

# === КОНЕЦ КОНФИГУРАЦИИ ===
