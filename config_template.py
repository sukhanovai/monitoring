import os
from datetime import time as dt_time

# 🔐 НАСТРОЙКИ TELEGRAM
TELEGRAM_TOKEN = "your_telegram_bot_token_here"
CHAT_IDS = ["your_chat_id_1", "your_chat_id_2"]

# ⏰ ИНТЕРВАЛЫ ПРОВЕРОК
CHECK_INTERVAL = 60  # секунды между проверками доступности
MAX_FAIL_TIME = 900  # 15 минут в секундах до отправки алерта

# 🌙 ВРЕМЕННЫЕ НАСТРОЙКИ
SILENT_START = 20    # 20:00 - начало тихого режима
SILENT_END = 9       # 9:00 - конец тихого режима
DATA_COLLECTION_TIME = dt_time(8, 30)  # Время утреннего отчета

# 📊 НАСТРОЙКИ РЕСУРСОВ
RESOURCE_CHECK_INTERVAL = 1800  # 30 минут между проверками ресурсов
RESOURCE_ALERT_THRESHOLDS = {
    "cpu_alert": 99,
    "ram_alert": 99,  
    "disk_alert": 95,
    "check_consecutive": 2
}
RESOURCE_ALERT_INTERVAL = 1800  # 30 минут между повторными алертами

RESOURCE_THRESHOLDS = {
    "cpu_warning": 80,
    "cpu_critical": 90,
    "ram_warning": 85,
    "ram_critical": 95,
    "disk_warning": 80,
    "disk_critical": 90
}

# 🔑 НАСТРОЙКИ АУТЕНТИФИКАЦИИ
SSH_KEY_PATH = "/root/.ssh/id_rsa"  # Путь к SSH ключу
SSH_USERNAME = "root"               # Пользователь для SSH

# 🪟 УЧЕТНЫЕ ДАННЫЕ WINDOWS СЕРВЕРОВ
WINDOWS_SERVER_CREDENTIALS = {
    "windows_servers": {
        "servers": ["192.168.1.10", "192.168.1.11"],
        "credentials": [
            {"username": "Administrator", "password": "your_windows_password"}
        ]
    }
}

# Общие учетные данные WinRM (fallback)
WINRM_CONFIGS = [
    {"username": "Administrator", "password": "your_windows_password"},
]

# 🌐 ВЕБ-ИНТЕРФЕЙС
WEB_PORT = 5000
WEB_HOST = '0.0.0.0'

# 📁 ФАЙЛЫ ДАННЫХ
STATS_FILE = "/opt/monitoring/data/monitoring_stats.json"
DATA_DIR = "/opt/monitoring/data"

# 🖥️ СПИСКИ СЕРВЕРОВ (настройте под вашу инфраструктуру)
RDP_SERVERS = [
    "192.168.1.10", "192.168.1.11",  # Windows серверы
]

SSH_SERVERS = [
    "192.168.1.20", "192.168.1.21",  # Linux серверы
]

PING_SERVERS = [
    "192.168.1.30",  # Серверы только для ping проверки
]

# ⏱️ ТАЙМАУТЫ ДЛЯ РАЗНЫХ ТИПОВ СЕРВЕРОВ
SERVER_TIMEOUTS = {
    "windows_servers": 30,
    "linux": 15
}

# Создаем директорию для данных
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    