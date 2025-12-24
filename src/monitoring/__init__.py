"""
/src/monitoring/__init__.py
Server Monitoring System v4.16.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Package exports
Система мониторинга серверов
Версия: 4.16.5
Автор: Александр Суханов (c)
Лицензия: MIT
Экспорт пакетов
"""

__version__ = "4.16.0"
__author__ = "Александр Суханов"

# Re-exports from lib
from monitoring.lib.logging import debug_log, setup_logging
from monitoring.lib.alerts import send_alert
from monitoring.lib.utils import progress_bar, format_duration, safe_import

# Re-exports from core
from monitoring.core.config_manager import settings_manager
from monitoring.core.checker import ServerChecker

# Re-exports from config
from monitoring.config.settings import (
    TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL,
    MAX_FAIL_TIME, SILENT_START, SILENT_END,
    RESOURCE_CHECK_INTERVAL, RESOURCE_ALERT_INTERVAL,
    RESOURCE_THRESHOLDS, RESOURCE_ALERT_THRESHOLDS,
    SSH_USERNAME, SSH_KEY_PATH
)