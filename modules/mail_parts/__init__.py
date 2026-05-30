"""
/modules/mail_parts/__init__.py
Server Monitoring System v8.62.74
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Decomposed mail monitor package. Старый modules/mail_monitor.py
остаётся тонким фасадом и реэкспортирует BackupProcessor / pattern-
хелперы / run_mail_monitor / main отсюда — внешние импортёры не правятся.
Система мониторинга серверов
Версия: 8.62.74
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет декомпозиции modules/mail_monitor.py (PR6 серии оптимизации).
"""

from __future__ import annotations

from config.db_settings import LOG_DIR, MAIL_MONITOR_LOG_FILE
from lib.logging import setup_logging

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Единый logger для всех подмодулей mail_parts/ — раньше жил
# module-level в modules/mail_monitor.py.
logger = setup_logging("mail_monitor", log_file=MAIL_MONITOR_LOG_FILE)
