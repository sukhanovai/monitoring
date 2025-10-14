# 🤖 Серверный мониторинг

Система мониторинга серверов с Telegram ботом для уведомлений и управления.

## 📋 Функциональность

- Мониторинг доступности серверов (RDP, SSH, Ping)
- Проверка ресурсов (CPU, RAM, Disk)
- Уведомления в Telegram
- Веб-интерфейс для просмотра статуса
- Гибкие настройки проверок

## 🏗️ Структура проекта

monitoring/
├── main.py # Главный запускаемый файл
├── config.py # Конфигурация (НЕ ДОБАВЛЯТЬ В GIT!)
├── bot_menu.py # Меню и команды бота
├── monitor_core.py # Основная логика мониторинга
├── requirements.txt # Зависимости Python
├── .gitignore # Исключаемые файлы
└── extensions/ # Дополнительные модули
├── server_list.py # Списки серверов
├── resource_check.py # Проверка ресурсов
├── separate_checks.py # Раздельные проверки
├── web_interface.py # Веб-интерфейс
├── single_check.py # Одиночные проверки
└── reports.py # Отчеты


## ⚙️ Установка

1. Клонировать репозиторий
2. Создать виртуальное окружение: `python -m venv venv`
3. Активировать окружение: `source venv/bin/activate`
4. Установить зависимости: `pip install -r requirements.txt`
5. Создать config.py на основе config.example.py
6. Настроить доступы к серверам

## 🚀 Запуск

```bash
python main.py

📝 Конфигурация
Создайте файл config.py на основе примера и настройте:

Токен Telegram бота

ID чатов для уведомлений

Учетные данные серверов

Настройки мониторинга


**Создаем config.example.py (шаблон для конфигурации):**
```bash
cat > /opt/monitoring/config.example.py << 'EOF'
import os
from datetime import time as dt_time

# Настройки Telegram бота
TELEGRAM_TOKEN = "your_telegram_bot_token_here"
CHAT_IDS = ["your_chat_id_here"]

# Интервалы проверок
CHECK_INTERVAL = 60  # секунды
MAX_FAIL_TIME = 900  # 15 минут в секундах

# Тихий режим (ночные часы)
SILENT_START = 20  # 20:00
SILENT_END = 9     # 9:00

# Время сбора данных и отчетов
DATA_COLLECTION_TIME = dt_time(8, 15)  # Сбор данных в 8:15
REPORT_WINDOW_START = dt_time(8, 30)   # Окно отправки отчета 8:30-8:35
REPORT_WINDOW_END = dt_time(8, 35)

# Пороги ресурсов
RESOURCE_THRESHOLDS = {
    "cpu_warning": 80,
    "cpu_critical": 90,
    "ram_warning": 85,
    "ram_critical": 95,
    "disk_warning": 80,
    "disk_critical": 90
}

# SSH настройки
SSH_KEY_PATH = "/path/to/your/ssh/key"
SSH_USERNAME = "your_ssh_username"

# Списки серверов
RDP_SERVERS = [
    "192.168.1.100",
    "192.168.1.101"
]

SSH_SERVERS = [
    "192.168.1.200",
    "192.168.1.201"
]

PING_SERVERS = [
    "192.168.1.50"
]

# Учетные данные Windows серверов
WINDOWS_SERVER_CREDENTIALS = {
    "windows_2025": {
        "servers": ["192.168.1.100"],
        "credentials": [
            {"username": "Administrator", "password": "your_password"}
        ]
    }
}

# Веб-интерфейс
WEB_PORT = 5000
WEB_HOST = '0.0.0.0'

# Пути к файлам данных
STATS_FILE = "/opt/monitoring/data/monitoring_stats.json"
DATA_DIR = "/opt/monitoring/data"

# Создаем директорию для данных
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
EOF
