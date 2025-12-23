"""
/modules/mail_monitor.py
Server Monitoring System v4.15.7
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
A wrapper around the backup email handler.
Система мониторинга серверов
Версия: 4.15.7
Автор: Александр Суханов (c)
Лицензия: MIT
Обёртка над обработчиком почты бэкапов.
"""
from improved_mail_monitor import BackupProcessor


def run_mail_monitor() -> int:
    """
    Запускает обработку новых писем с отчётами о бэкапах.

    Returns:
        Количество обработанных писем.
    """
    processor = BackupProcessor()
    return processor.process_new_emails()