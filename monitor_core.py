"""
Server Monitoring System v4.3.5 - Совместимый модуль ядра
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

# Импортируем обработчики из нового места
try:
    from app.bot.handlers import (
        close_menu,
        force_silent_handler,
        force_loud_handler,
        auto_mode_handler,
        toggle_silent_mode_handler,
        send_morning_report_handler,
        resource_page_handler,
        refresh_resources_handler,
        close_resources_handler,
        resource_history_command,
        debug_morning_report,
        check_linux_resources_handler,
        check_windows_resources_handler,
        check_other_resources_handler,
        check_cpu_resources_handler,
        check_ram_resources_handler,
        check_disk_resources_handler,
    )
    print("✅ Обработчики загружены из новой структуры")
except ImportError as e:
    print(f"⚠️ Ошибка импорта обработчиков: {e}")

# Экспортируем для совместимости
__all__ = [
    'monitoring_core',
    'start_monitoring',
    'get_alerting_system',
    'debug_log',
    'progress_bar',
    'format_duration',
    'safe_import',
    'settings',
    # Обработчики
    'close_menu',
    'force_silent_handler',
    'force_loud_handler',
    'auto_mode_handler',
    'toggle_silent_mode_handler',
    'send_morning_report_handler',
    'resource_page_handler',
    'refresh_resources_handler',
    'close_resources_handler',
    'resource_history_command',
    'debug_morning_report',
    'check_linux_resources_handler',
    'check_windows_resources_handler',
    'check_other_resources_handler',
    'check_cpu_resources_handler',
    'check_ram_resources_handler',
    'check_disk_resources_handler',
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

print("✅ Используется новая структура ядра мониторинга")
