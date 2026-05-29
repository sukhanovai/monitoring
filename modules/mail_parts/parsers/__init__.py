"""
/modules/mail_parts/parsers/__init__.py
Server Monitoring System v8.62.72
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Parser-mixins для BackupProcessor (PR6c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.72
Автор: Александр Суханов (c)
Лицензия: MIT
Пять mixin'ов, по одному на семейство писем-отчётов: Proxmox vzdump,
БД-дампы, ZFS pool/snapshot, mail-сервер, supplier-stock логи.
Собираются в final BackupProcessor через множественное наследование.
"""

from __future__ import annotations

from modules.mail_parts.parsers.database import DatabaseBackupParserMixin
from modules.mail_parts.parsers.mail import MailBackupParserMixin
from modules.mail_parts.parsers.nas_transfer import NasTransferParserMixin
from modules.mail_parts.parsers.proxmox import ProxmoxBackupParserMixin
from modules.mail_parts.parsers.stock_load import StockLoadParserMixin
from modules.mail_parts.parsers.zfs import ZfsBackupParserMixin

__all__ = [
    "DatabaseBackupParserMixin",
    "MailBackupParserMixin",
    "NasTransferParserMixin",
    "ProxmoxBackupParserMixin",
    "StockLoadParserMixin",
    "ZfsBackupParserMixin",
]
