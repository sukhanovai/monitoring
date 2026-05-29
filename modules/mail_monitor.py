"""
/modules/mail_monitor.py
Server Monitoring System v8.62.65
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mailbox monitoring — тонкий фасад над пакетом modules/mail_parts/.
Система мониторинга серверов
Версия: 8.62.65
Автор: Александр Суханов (c)
Лицензия: MIT
Тонкий фасад: класс BackupProcessor и pattern-хелперы перенесены в
modules/mail_parts/, здесь остаются точка входа `run_mail_monitor` и
`main` для systemd-юнита mail-monitor.service.
"""

from __future__ import annotations

import time

from modules.mail_parts import logger
from modules.mail_parts.patterns import (
    get_database_patterns_from_config,
    get_mail_patterns_from_config,
    get_snapshot_transfer_patterns_from_config,
    get_stock_load_patterns_from_config,
    get_zfs_patterns_from_config,
)
from modules.mail_parts.processor import BackupProcessor


def run_mail_monitor() -> int:
    """
    Запускает обработку новых писем с отчётами о бэкапах.

    Returns:
        Количество обработанных писем.
    """
    processor = BackupProcessor()
    return processor.process_new_emails()


def main() -> None:
    """Основная функция."""
    logger.info("🔄 Запуск исправленного мониторинга почты Proxmox бэкапов...")

    try:
        processor = BackupProcessor()

        logger.info("📧 Мониторинг директорий: /root/Maildir/new и /root/Maildir/cur")

        while True:
            try:
                processed = processor.process_new_emails()
                if processed > 0:
                    logger.info(f"✅ Обработано новых писем: {processed}")

                time.sleep(30)

            except Exception as exc:
                logger.error(f"❌ Ошибка в основном цикле: {exc}")
                time.sleep(60)

    except Exception as exc:
        logger.error(f"💥 Критическая ошибка: {exc}")
        raise


__all__ = [
    "BackupProcessor",
    "get_database_patterns_from_config",
    "get_mail_patterns_from_config",
    "get_snapshot_transfer_patterns_from_config",
    "get_stock_load_patterns_from_config",
    "get_zfs_patterns_from_config",
    "main",
    "run_mail_monitor",
]


if __name__ == "__main__":
    main()
