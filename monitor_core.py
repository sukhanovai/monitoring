"""
Server Monitoring System v4.3.1 - Совместимый модуль ядра
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Совместимый модуль для постепенного перехода
Версия: 4.3.1
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

# Экспортируем для совместимости
__all__ = [
    'monitoring_core',
    'start_monitoring',
    'get_alerting_system',
    'debug_log',
    'progress_bar',
    'format_duration',
    'safe_import',
    'settings'
]

# Глобальные переменные для совместимости со старым кодом
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

# Функции для совместимости
def is_silent_time():
    return monitoring_core.is_silent_time()

def send_alert(message, force=False):
    monitoring_core.send_alert(message, force)

def check_server_availability(server):
    return monitoring_core.check_server_availability(server)

def get_current_server_status():
    return monitoring_core.get_current_server_status()

# Обработчики (перенаправляем в новую структуру)
def manual_check_handler(update, context):
    """Обработчик ручной проверки серверов"""
    from app.bot.handlers import manual_check_handler as new_handler
    return new_handler(update, context)

def monitor_status(update, context):
    """Показывает статус мониторинга"""
    from app.bot.handlers import monitor_status as new_handler
    return new_handler(update, context)

def silent_command(update, context):
    """Обработчик команды /silent"""
    from app.bot.handlers import silent_command as new_handler
    return new_handler(update, context)

# ... остальные обработчики будут перенесены на следующем этапе

print("✅ Используется новая структура ядра мониторинга")
