"""
/__init__.py
Server Monitoring System v4.14.36
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Package exports
Система мониторинга серверов
Версия: 4.14.36
Автор: Александр Суханов (c)
Лицензия: MIT
Экспорт пакетов
"""

__version__ = "4.14.36"
__author__ = "Александр Суханов"

# Re-exports from lib
from lib.logging import debug_log, setup_logging
from lib.alerts import send_alert
from lib.utils import progress_bar, format_duration, safe_import

# Re-exports from core
from core.config_manager import settings_manager
from core.checker import ServerChecker

# Re-exports from config
from config.settings import (
    TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL,
    MAX_FAIL_TIME, SILENT_START, SILENT_END,
    RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_INTERVAL,
    RESOURCE_THRESHOLDS, RESOURCE_ALERT_THRESHOLDS,
    SSH_USERNAME, SSH_KEY_PATH
)
