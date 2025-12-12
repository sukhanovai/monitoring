"""
Server Monitoring System v4.3.6 - Совместимый модуль ядра
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Совместимый модуль для постепенного перехода
Версия: 4.2.2
"""

import os
import sys

# Добавляем путь к новым модулям
sys.path.insert(0, '/opt/monitoring')

# Импортируем из новой структуры
from app.core.monitoring import monitoring_core, start_monitoring
from app.core.alerting import get_alerting_system
from app.utils.common import debug_log, progress_bar, format_duration, safe_import
from app.config import settings

# Импортируем все обработчики из нового места
try:
    from app.bot.handlers import *
    print("✅ Все обработчики загружены из новой структуры")
except ImportError as e:
    print(f"⚠️ Ошибка импорта обработчиков: {e}")

# Экспортируем все для совместимости
__all__ = [
    'monitoring_core',
    'start_monitoring',
    'get_alerting_system',
    'debug_log',
    'progress_bar',
    'format_duration',
    'safe_import',
    'settings',
]

# Добавляем все обработчики в __all__
try:
    from app.bot.handlers import __all__ as handler_exports
    __all__.extend(handler_exports)
except:
    pass

# Глобальные переменные для совместимости
bot = None
server_status = monitoring_core.server_status
morning_data = monitoring_core.morning_data
monitoring_active = monitoring_core.monitoring_active
last_check_time = monitoring_core.last_check_time
servers = monitoring_core.servers
silent_override = monitoring_core.silent_override
resource_history = monitoring_core.resource_history
last_resource_check = monitoring_core.last_resource_check
resource_alerts_sent = monitoring_core.resource_alerts_sent
last_report_date = monitoring_core.last_report_date

# Функции-обертки для совместимости
def is_silent_time():
    return monitoring_core.is_silent_time()

def send_alert(message, force=False):
    monitoring_core.send_alert(message, force)

def check_server_availability(server):
    return monitoring_core.check_server_availability(server)

def get_current_server_status():
    return monitoring_core.get_current_server_status()

print("✅ Используется новая модульная структура")