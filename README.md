🚀 Серверный мониторинг v2.0.0
Полностью переработанная система мониторинга с веб-интерфейсом управления серверами

🆕 Что нового в версии 2.0.0
✨ Основные нововведения
🌐 Веб-интерфейс управления серверами - добавление/удаление серверов через браузер

⚙️ Централизованное управление - единый файл конфигурации серверов

📱 Адаптивный дизайн - полная поддержка мобильных устройств

🔧 Упрощенная настройка - минимальные требования для запуска

🎯 Улучшения функциональности
Динамическое обновление списка серверов без перезапуска системы

Визуальное управление всеми серверами через веб-интерфейс

Автоматическая классификация серверов по типам (Linux/Windows)

Расширенная статистика в реальном времени

🚀 Быстрый старт (5 минут)

1. Клонирование и настройка

# Клонирование репозитория
git clone https://github.com/sukhanovai/monitoring.git
cd monitoring

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

2. Базовая конфигурация

# Копируем шаблон конфигурации
cp config_template.py config.py

# Редактируем конфигурацию
nano config.py

Минимальная конфигурация для запуска:

# 🔐 НАСТРОЙКИ TELEGRAM (обязательно)
TELEGRAM_TOKEN = "ваш_telegram_bot_token"
CHAT_IDS = ["ваш_chat_id"]

# 📁 ПУТИ ДАННЫХ (обязательно)
DATA_DIR = "./data"
STATS_FILE = "./data/monitoring_stats.json"

# 🖥️ ВАШИ СЕРВЕРЫ (обязательно)
RDP_SERVERS = ["192.168.1.10"]  # Ваши Windows серверы
SSH_SERVERS = ["192.168.1.20"]  # Ваши Linux серверы  
PING_SERVERS = []               # Серверы только для ping

3. Запуск системы

# Первый запуск
python main.py

# Или запуск в фоне
nohup python main.py > monitoring.log 2>&1 &

4. Доступ к веб-интерфейсу
Откройте в браузере: http://ваш-сервер:5000

⚙️ Конфигурация системы
Шаг 1: Создание конфигурационного файла
Система использует два конфигурационных файла:

config_template.py - шаблон с комментариями (уже в репозитории)

config.py - ваша реальная конфигурация (создается вручную)

# Копируем шаблон в реальный конфиг
cp config_template.py config.py

# Редактируем конфиг
nano config.py

Шаг 2: Обязательные настройки
Минимальная конфигурация для запуска:

# 🔐 НАСТРОЙКИ TELEGRAM (обязательно)
TELEGRAM_TOKEN = "ваш_telegram_bot_token"
CHAT_IDS = ["ваш_chat_id"]

# 📁 ПУТИ ДАННЫХ (обязательно)
DATA_DIR = "./data"
STATS_FILE = "./data/monitoring_stats.json"

# 🖥️ ВАШИ СЕРВЕРЫ (обязательно)
RDP_SERVERS = ["192.168.1.10"]  # Ваши Windows серверы
SSH_SERVERS = ["192.168.1.20"]  # Ваши Linux серверы  
PING_SERVERS = []               # Серверы только для ping

Шаг 3: Получение Telegram токена и Chat ID
Создание бота:
Напишите @BotFather в Telegram

Отправьте /newbot

Укажите имя бота (например: My Server Monitor)

Укажите username бота (например: my_server_monitor_bot)

Скопируйте токен вида: 7916988741:AAHEX68KdHrJpfAhXKenSJSqsmESdqWeTWM

Получение Chat ID:

# Отправьте сообщение боту, затем выполните:
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates"

# В ответе найдите "chat":{"id":123456789}

Шаг 4: Настройка SSH доступа

# Генерация SSH ключа (если нет)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Копирование ключа на Linux серверы
ssh-copy-id -i ~/.ssh/id_rsa.pub user@server-ip

Шаг 5: Настройка WinRM для Windows
На целевых Windows серверах выполните в PowerShell:

# Включение WinRM
Enable-PSRemoting -Force
Set-NetFirewallRule -Name "WINRM-HTTP-In-TCP" -RemoteAddress Any

# Для доменных серверов
Set-Item -Path WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

Шаг 6: Расширенная конфигурация (опционально)
После базовой настройки можно добавить:

# 🪟 Расширенные учетные данные Windows
WINDOWS_SERVER_CREDENTIALS = {
    "domain_servers": {
        "servers": ["192.168.1.12"],
        "credentials": [
            {"username": "domain\\user", "password": "password"}
        ]
    }
}

# 📊 Настройки алертов
RESOURCE_ALERT_THRESHOLDS = {
    "cpu_alert": 99,
    "ram_alert": 99,  
    "disk_alert": 95,
    "check_consecutive": 2
}

Шаг 7: Проверка конфигурации

# Проверка синтаксиса
python -m py_compile config.py

# Тестовый запуск
python -c "import config; print('✅ Конфигурация загружена успешно')"

# Проверка зависимостей
python -c "import flask, telegram, paramiko; print('✅ Все зависимости установлены')"

🔒 Безопасность конфигурации
Никогда не коммитьте config.py в Git

Храните пароли только в config.py

Используйте разные пароли для разных серверов

Регулярно обновляйте SSH ключи и пароли

🚨 Важные замечания
Файл config.py автоматически добавляется в .gitignore

При обновлении системы сравните config_template.py с вашим config.py

Резервное копирование config.py при миграции на новый сервер

📋 Полная установка (Production)
1. Системные требования

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install python3 python3-pip git

2. Установка в /opt/monitoring

# Создание директории
sudo mkdir -p /opt/monitoring
sudo chown $USER:$USER /opt/monitoring

# Клонирование
git clone https://github.com/sukhanovai/monitoring.git /opt/monitoring
cd /opt/monitoring

# Настройка окружения
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3. Настройка конфигурации

# Копирование шаблона
cp config_template.py config.py

# Редактирование конфигурации
nano config.py

4. Настройка systemd сервиса

sudo nano /etc/systemd/system/server-monitor.service

[Unit]
Description=Server Monitoring System v2.0
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
ExecStart=/opt/monitoring/venv/bin/python /opt/monitoring/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable server-monitor
sudo systemctl start server-monitor
sudo systemctl status server-monitor

🌐 Использование веб-интерфейса
Управление серверами
Откройте http://ваш-сервер:5000

Перейдите на вкладку "⚙️ Управление серверами"

Добавьте серверы через форму:

Название сервера

IP-адрес

Тип (Linux/Windows)

Основные вкладки
📊 Обзор - общая статистика и быстрые действия

🖥️ Сервера - детальный статус всех серверов

🎛️ Управление - запуск проверок и управление режимами

⚙️ Управление серверами - добавление/удаление серверов

🤖 Команды Telegram бота
Основные команды
/start - Главное меню

/status - Статус системы

/check - Быстрая проверка

/servers - Список серверов

Управление
/control - Панель управления

/silent - Тихий режим

/report - Отчет

📊 Мониторинг и логи
Просмотр логов

# Логи systemd
journalctl -u server-monitor -f

# Файлы логов
tail -f /opt/monitoring/monitoring.log

Проверка здоровья

# Health check
curl http://localhost:5000/health

# Статус API
curl http://localhost:5000/api/status

🔧 Диагностика проблем
Частые проблемы и решения
Серверы не добавляются - проверьте права на запись в data/

Web-интерфейс недоступен - проверьте firewall и порт 5000

Telegram бот не отвечает - проверьте токен и Chat ID

SSH подключение не работает - проверьте ключи и доступность серверов

Команды диагностики

# Проверка конфигурации
python -c "import config; print('✅ Config OK')"

# Проверка зависимостей
python -c "import flask, telegram, paramiko; print('✅ Dependencies OK')"

# Тест веб-интерфейса
curl -s http://localhost:5000/api/status | python -m json.tool

📁 Структура проекта

/opt/monitoring/
├── main.py                 # Точка входа
├── config.py              # Конфигурация (создается вручную)
├── config_template.py     # Шаблон конфигурации
├── monitor_core.py        # Ядро мониторинга
├── bot_menu.py            # Telegram бот
├── web_interface.py       # Веб-интерфейс v2.0
├── requirements.txt       # Зависимости
├── server_list.json       # Автоматически создаваемый список серверов
└── extensions/
    ├── server_list.py     # Управление серверами
    ├── resource_check.py  # Проверка ресурсов
    └── ...               # Дополнительные модули

🆘 Поддержка
Документация: https://github.com/sukhanovai/monitoring

Issues: https://github.com/sukhanovai/monitoring/issues

Releases: https://github.com/sukhanovai/monitoring/releases

📄 Лицензия
MIT License - подробности в файле LICENSE

Версия 2.0.0 • Полная переработка с веб-интерфейсом управления

