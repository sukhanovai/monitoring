"""
/modules/mail_parts/parsers/config_console.py
Server Monitoring System v8.62.83
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ConfigConsoleBackupParserMixin — часть BackupProcessor.
Система мониторинга серверов
Версия: 8.62.83
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin ConfigConsoleBackupParserMixin; объединяется с другими mixin'ами в
BackupProcessor. Парсит итоговое письмо скрипта copy_configs_ssh.sh о
копировании конфигов VM/LXC и историй консолей хостов на бэкап-сервер/NAS
по SSH (одна запись на прогон).
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime

from extensions.extension_manager import extension_manager
from modules.mail_parts import logger
from modules.mail_parts.patterns import get_config_console_patterns_from_config

CONFIG_CONSOLE_FALLBACK_PATTERN = (
    r"^Config backup (?P<host>[\w.-]+) (?P<status>OK|PARTIAL|ERROR)$"
)


class ConfigConsoleBackupParserMixin:
    """Mixin ConfigConsoleBackupParserMixin — письма о бэкапе конфигов и историй."""

    def parse_config_console_backup(self, subject: str, body: str) -> dict | None:
        """Парсит итог копирования конфигов/историй из темы и тела письма."""
        if not extension_manager.is_extension_enabled("config_console_backup_monitor"):
            return None

        patterns = get_config_console_patterns_from_config()
        if not patterns:
            patterns = [CONFIG_CONSOLE_FALLBACK_PATTERN]

        normalized_subject = " ".join((subject or "").split())

        match = None
        for pattern in patterns:
            try:
                match = re.search(pattern, normalized_subject, re.IGNORECASE)
            except re.error as exc:
                logger.warning(
                    "⚠️ Некорректный паттерн Config backup '%s': %s", pattern, exc
                )
                continue
            if match:
                break

        if not match:
            match = re.search(
                CONFIG_CONSOLE_FALLBACK_PATTERN, normalized_subject, re.IGNORECASE
            )

        if not match:
            return None

        host_name = (match.groupdict().get("host") or "").strip()
        status = (match.groupdict().get("status") or "").upper().strip()
        if not host_name or not status:
            return None

        def _extract(pattern: str) -> str | None:
            local = re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            if not local:
                return None
            value = local.group(1).strip()
            return value or None

        def _extract_int(pattern: str) -> int:
            value = _extract(pattern)
            if value is None:
                return 0
            digits = re.search(r"\d+", value)
            return int(digits.group(0)) if digits else 0

        problem_items_raw = _extract(r"Проблемные элементы:\s*(.+)") or ""
        problem_items = ", ".join(
            part.strip() for part in problem_items_raw.split(",") if part.strip()
        )

        logger.info("✅ Бэкап конфигов/историй: %s — %s", host_name, status)
        return {
            "host_name": host_name,
            "status": status,
            "delivery_method": _extract(r"Способ доставки:\s*(.+)"),
            "receiver": _extract(r"Приёмник:\s*(.+)"),
            "started_at_text": _extract(r"Начало:\s*(.+)"),
            "completed_at_text": _extract(r"Завершено:\s*(.+)"),
            "vm_config_count": _extract_int(r"VM конфигов:\s*(.+)"),
            "lxc_config_count": _extract_int(r"LXC конфигов:\s*(.+)"),
            "history_container_count": _extract_int(r"Контейнеров с историей:\s*(.+)"),
            "history_file_count": _extract_int(r"Файлов истории:\s*(.+)"),
            "error_count": _extract_int(r"Ошибок:\s*(.+)"),
            "problem_items": problem_items or None,
        }

    def save_config_console_backup(
        self,
        backup_info: dict,
        subject: str,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет итог копирования конфигов/историй в БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            received_at = (
                email_date.strftime("%Y-%m-%d %H:%M:%S")
                if email_date
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO config_console_backups
                (host_name, status, delivery_method, receiver, started_at_text,
                 completed_at_text, vm_config_count, lxc_config_count,
                 history_container_count, history_file_count, error_count,
                 problem_items, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    backup_info["host_name"],
                    backup_info["status"],
                    backup_info.get("delivery_method"),
                    backup_info.get("receiver"),
                    backup_info.get("started_at_text"),
                    backup_info.get("completed_at_text"),
                    backup_info.get("vm_config_count", 0),
                    backup_info.get("lxc_config_count", 0),
                    backup_info.get("history_container_count", 0),
                    backup_info.get("history_file_count", 0),
                    backup_info.get("error_count", 0),
                    backup_info.get("problem_items"),
                    subject[:500],
                    received_at,
                ),
            )
            conn.commit()
            logger.info(
                "✅ Сохранён итог бэкапа конфигов/историй: %s (%s)",
                backup_info["host_name"],
                backup_info["status"],
            )
        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения итога бэкапа конфигов/историй: {exc}")
        finally:
            if "conn" in locals():
                conn.close()
