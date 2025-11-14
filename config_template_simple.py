"""
Server Monitoring System - Минимальная конфигурация
Скопируйте в config.py и настройте только обязательные параметры
"""

import os
from datetime import time as dt_time

# === ОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ ===

# 🔐 TELEGRAM НАСТРОЙКИ
TELEGRAM_TOKEN = "ВАШ_TELEGRAM_BOT_TOKEN"  # Получите у @BotFather
CHAT_IDS = ["ВАШ_CHAT_ID"]  # Получите через /getUpdates

# 🖥️ ВАШИ СЕРВЕРЫ
SERVER_CONFIG = {
    "windows_servers": {
        "192.168.1.10": "Мой Windows сервер",
    },
    "linux_servers": {
        "192.168.1.20": "Мой Linux сервер", 
    },
    "ping_servers": {}
}

# === БАЗОВЫЕ НАСТРОЙКИ ===

# Пути
DATA_DIR = "/opt/monitoring/data"
os.makedirs(DATA_DIR, exist_ok=True)

# SSH настройки
SSH_KEY_PATH = "/root/.ssh/id_rsa"
SSH_USERNAME = "root"

# Учетные данные Windows
WINDOWS_CREDENTIALS = [
    {"username": "Administrator", "password": "ВАШ_ПАРОЛЬ"},
]

# Интервалы проверок
CHECK_INTERVAL = 60
MAX_FAIL_TIME = 900

# Веб-интерфейс
WEB_PORT = 5000
WEB_HOST = '0.0.0.0'

print("✅ Минимальная конфигурация загружена")
print("⚠️  Настройте TELEGRAM_TOKEN, CHAT_IDS и серверы перед использованием")
