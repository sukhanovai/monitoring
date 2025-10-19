# 🤖 Серверный мониторинг v1.3.0

**Многофункциональная система мониторинга серверов с Telegram ботом и веб-интерфейсом**

---

## 🚀 Основные возможности

### 📊 Мониторинг доступности
- **Автоматическая проверка** серверов каждые 60 секунд
- **Множественные методы проверки**: Ping, SSH, RDP (порт 3389)
- **Умные уведомления** о проблемах с серверами
- **Группировка серверов** по типам (Windows, Linux, Proxmox)

### 💻 Мониторинг ресурсов
- **Автоматическая проверка** CPU, RAM, Disk каждые 30 минут
- **Раздельная проверка** по типам ресурсов
- **Поддержка ZFS** для Proxmox и бэкап-серверов
- **Умные алерты** при превышении порогов

### 🔇 Гибкие режимы уведомлений
- **Тихий режим** (20:00 - 9:00) - только критические уведомления
- **Принудительное управление** режимами через бота
- **Автоматический режим** по расписанию

### 🌐 Веб-интерфейс
- **Темная тема** с адаптивным дизайном
- **Вкладки**: Обзор, Сервера, Управление
- **API endpoints** для интеграции
- **Авто-обновление** каждые 30 секунд

### 📱 Telegram бот
- **Интерактивное меню** с кнопками
- **Раздельные команды** для всех функций
- **Прогресс-бары** для длительных операций
- **Групповая отправка** уведомлений

---

## 🛠 Технические особенности

### Поддерживаемые системы
- **Windows Server**: 2025, 2019, 2016, 2012 R2
- **Linux**: Ubuntu, Debian, CentOS, Proxmox VE
- **Специальная поддержка**: ZFS, Proxmox кластеры

### Методы доступа
- **SSH**: ключевая аутентификация, поддержка разных алгоритмов
- **WinRM**: для Windows серверов, автоматический подбор учетных данных
- **RDP**: проверка доступности порта
- **Ping**: базовая проверка доступности

### Безопасность
- **Конфигурация в одном файле** (`config.py`)
- **Поддержка нескольких чатов** Telegram
- **Проверка прав доступа** к командам бота
- **Исключение сервера мониторинга** из проверок

---

## 📋 Полный функционал

### Команды Telegram бота

#### Основные команды
- `/start` - Главное меню с кнопками
- `/help` - Полная справка по командам
- `/status` - Текущий статус мониторинга
- `/check` - Быстрая проверка всех серверов

#### Управление мониторингом
- `/control` - Панель управления мониторингом
- `/silent` - Статус и управление тихим режимом
- `/servers` - Список всех серверов
- `/report` - Принудительная отправка утреннего отчета

#### Проверка ресурсов
- `/stats` - Статистика работы системы
- Раздельные проверки через интерактивное меню:
  - 💻 Проверить CPU
  - 🧠 Проверить RAM  
  - 💾 Проверить Disk
  - 🐧 Linux серверы
  - 🪟 Windows серверы
  - 📡 Другие серверы

#### Диагностика
- `/diagnose_ssh <ip>` - Диагностика SSH подключения
- `/fix_monitor` - Исправление статуса сервера мониторинга

### Веб-интерфейс функции

#### Вкладка "Обзор"
- Общая статистика серверов
- Статус мониторинга и режимов
- Информация о ресурсах системы
- Кнопки быстрых действий

#### Вкладка "Сервера"
- Детальный список всех серверов
- Реальная информация о ресурсах (CPU, RAM, Disk)
- Цветовая индикация проблем
- Сортировка по статусу

#### Вкладка "Управление"
- Запуск проверок и отчетов
- Управление режимами мониторинга
- Логи действий в реальном времени
- Перезапуск сервиса

### Автоматические функции

#### Ежедневные отчеты
- **Утренний отчет** в 8:30
- **Статистика доступности** за предыдущий день
- **Группировка проблем** по типам серверов
- **Принудительная отправка** даже в тихом режиме

#### Умные алерты
- **CPU**: 2 проверки подряд ≥99%
- **RAM**: 2 проверки подряд ≥99%  
- **Disk**: текущая проверка ≥95%
- **Интервал повтора**: 30 минут

#### История ресурсов
- **Хранение последних 10 проверок** для каждого сервера
- **Анализ трендов** для умных алертов
- **Визуализация в веб-интерфейсе**

---

## ⚙️ Развертывание конфигурации

### Важно!
Файл `config.py` содержит конфиденциальные данные и **не публикуется** в репозитории. Создайте его вручную по примеру ниже.

### Шаг 1: Создание config.py

Создайте файл `config.py` в корневой директории проекта:

```python
import os
from datetime import time as dt_time

# 🔐 НАСТРОЙКИ TELEGRAM
TELEGRAM_TOKEN = "ваш_telegram_bot_token"
CHAT_IDS = ["ваш_chat_id1", "ваш_chat_id2"]  # ID чатов для уведомлений

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
    "windows_2025": {
        "servers": ["192.168.1.10", "192.168.1.11"],
        "credentials": [
            {"username": "Администратор", "password": "ваш_пароль"},
            {"username": "Administrator", "password": "ваш_пароль"}
        ]
    },
    "domain_servers": {
        "servers": ["192.168.1.12", "192.168.1.13"],
        "credentials": [
            {"username": "domain\\user", "password": "ваш_пароль"}
        ]
    },
    # Добавьте другие типы серверов по необходимости
}

# Общие учетные данные WinRM (fallback)
WINRM_CONFIGS = [
    {"username": "Администратор", "password": "ваш_пароль"},
    {"username": "Administrator", "password": "ваш_пароль"},
    # Добавьте другие учетные записи
]

# 🌐 ВЕБ-ИНТЕРФЕЙС
WEB_PORT = 5000
WEB_HOST = '0.0.0.0'

# 📁 ФАЙЛЫ ДАННЫХ
STATS_FILE = "/opt/monitoring/data/monitoring_stats.json"
DATA_DIR = "/opt/monitoring/data"

# 🖥️ СПИСКИ СЕРВЕРОВ
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
    "windows_2025": 35,
    "domain_servers": 20,
    "admin_servers": 25,
    "standard_windows": 30,
    "linux": 15
}

# Создаем директорию для данных
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

Шаг 2: Настройка параметров

Получение Telegram токена и Chat ID
Создайте бота через @BotFather

Получите токен: /newbot → имя бота → username бота → токен

Получите Chat ID:

Добавьте бота в чат

Отправьте сообщение /start

Выполните: curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates"

Найдите chat.id в ответе

Настройка SSH доступа

# Генерация SSH ключа (если нет)
ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa

# Копирование ключа на серверы
ssh-copy-id -i /root/.ssh/id_rsa.pub user@server-ip

Настройка WinRM для Windows
На целевых Windows серверах выполните в PowerShell:

# Включение WinRM
Enable-PSRemoting -Force
Set-NetFirewallRule -Name "WINRM-HTTP-In-TCP" -RemoteAddress Any

# Для доменных серверов
Set-Item -Path WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

Шаг 3: Заполнение списков серверов
Измените массивы в соответствии с вашей инфраструктурой:

RDP_SERVERS = [
    "192.168.1.10",  # DC-01
    "192.168.1.11",  # FS-01
    # Добавьте ваши Windows серверы
]

SSH_SERVERS = [
    "192.168.1.20",  # web-01
    "192.168.1.21",  # db-01
    # Добавьте ваши Linux серверы
]

Шаг 4: Настройка учетных данных
Добавьте учетные данные для ваших Windows серверов в соответствующие секции:

WINDOWS_SERVER_CREDENTIALS = {
    "windows_2025": {
        "servers": ["192.168.1.10", "192.168.1.11"],
        "credentials": [
            {"username": "Администратор", "password": "real_password_here"},
            {"username": "Administrator", "password": "real_password_here"}
        ]
    },
    # ... другие типы серверов
}

Шаг 5: Проверка конфигурации
После создания config.py выполните проверку:

# Проверка синтаксиса
python -m py_compile config.py

# Тестовый запуск
python -c "import config; print('✅ Конфигурация загружена успешно')"

🚀 Установка и настройка
Требования
Python 3.8+

Доступ к серверам по SSH/WinRM

Telegram бот токен

Linux сервер для размещения

Быстрый старт
Клонировать репозиторий

Создать config.py по инструкции выше

Установить зависимости: pip install -r requirements.txt

Запустить: python main.py

Настройка systemd сервиса

# Создание сервисного файла
sudo nano /etc/systemd/system/server-monitor.service

[Unit]
Description=Server Monitoring Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
ExecStart=/usr/bin/python3 /opt/monitoring/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable server-monitor
sudo systemctl start server-monitor
sudo systemctl status server-monitor

📁 Структура проекта

/opt/monitoring/
├── main.py                 # Основной запускаемый файл
├── config.py              # ⚠️ Конфигурация (создается вручную)
├── monitor_core.py        # Ядро мониторинга
├── bot_menu.py            # Меню и команды бота
├── web_interface.py       # Веб-интерфейс Flask
├── requirements.txt       # Зависимости Python
├── .gitignore            # Исключает config.py из Git
├── extensions/
│   ├── server_list.py     # Управление списком серверов
│   ├── resource_check.py  # Проверка ресурсов серверов
│   ├── separate_checks.py # Раздельная проверка по типам
│   ├── single_check.py    # Диагностика отдельных серверов
│   ├── stats_collector.py # Сбор статистики
│   └── web_interface.py   # Веб-интерфейс
└── data/                  # Директория для данных

Полезные команды
# Проверка статуса сервиса
systemctl status server-monitor

# Просмотр логов
journalctl -u server-monitor -f

# Ручной запуск проверки
python -c "from monitor_core import get_current_server_status; print(get_current_server_status())"

Диагностика проблем
Используйте /diagnose_ssh IP для проверки SSH

Веб-интерфейс доступен по http://ваш-сервер:5000

Логи хранятся в системном journalctl

📄 Лицензия
MIT License - подробности в файле LICENSE
