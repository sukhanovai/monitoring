"""
/modules/mail_parts/parsers/nas_transfer.py
Server Monitoring System v8.62.73
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
NasTransferParserMixin — часть BackupProcessor.
Система мониторинга серверов
Версия: 8.62.73
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin NasTransferParserMixin; объединяется с другими mixin'ами в BackupProcessor.
Парсит итоговое письмо скрипта move_and_clear_backups.sh о передаче бэкапов
1С на NAS (одна запись на прогон).
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime

from extensions.extension_manager import extension_manager
from modules.mail_parts import logger
from modules.mail_parts.patterns import get_nas_transfer_patterns_from_config

NAS_TRANSFER_FALLBACK_PATTERN = (
    r"^NAS transfer (?P<host>[\w.-]+) (?P<status>OK|ERROR|SKIPPED|STARTED|BUSY)$"
)


class NasTransferParserMixin:
    """Mixin NasTransferParserMixin — методы для писем о передаче бэкапов на NAS."""

    def parse_nas_transfer(self, subject: str, body: str) -> dict | None:
        """Парсит итог передачи бэкапов на NAS из темы и тела письма."""
        if not extension_manager.is_extension_enabled("nas_transfer_monitor"):
            return None

        patterns = get_nas_transfer_patterns_from_config()
        if not patterns:
            patterns = [NAS_TRANSFER_FALLBACK_PATTERN]

        normalized_subject = " ".join((subject or "").split())

        match = None
        for pattern in patterns:
            try:
                match = re.search(pattern, normalized_subject, re.IGNORECASE)
            except re.error as exc:
                logger.warning("⚠️ Некорректный паттерн NAS transfer '%s': %s", pattern, exc)
                continue
            if match:
                break

        if not match:
            match = re.search(NAS_TRANSFER_FALLBACK_PATTERN, normalized_subject, re.IGNORECASE)

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

        mounted_text = (_extract(r"NAS примонтирован:\s*(.+)") or "").strip().lower()
        nas_mounted = 1 if mounted_text in ("да", "yes", "true", "1") else 0

        problem_bases_raw = _extract(r"Проблемные базы:\s*(.+)") or ""
        problem_bases = ", ".join(
            part.strip() for part in problem_bases_raw.split(",") if part.strip()
        )

        logger.info("✅ Передача на NAS: %s — %s", host_name, status)
        return {
            "host_name": host_name,
            "status": status,
            "nas_mounted": nas_mounted,
            "started_at_text": _extract(r"Начало:\s*(.+)"),
            "completed_at_text": _extract(r"Завершено:\s*(.+)"),
            "bases_processed": _extract_int(r"Баз обработано:\s*(.+)"),
            "error_count": _extract_int(r"Ошибок:\s*(.+)"),
            "problem_bases": problem_bases or None,
        }

    def save_nas_transfer(
        self,
        transfer_info: dict,
        subject: str,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет итог передачи бэкапов на NAS в БД."""
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
                INSERT OR IGNORE INTO nas_transfers
                (host_name, status, nas_mounted, started_at_text, completed_at_text,
                 bases_processed, error_count, problem_bases, email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transfer_info["host_name"],
                    transfer_info["status"],
                    transfer_info.get("nas_mounted", 0),
                    transfer_info.get("started_at_text"),
                    transfer_info.get("completed_at_text"),
                    transfer_info.get("bases_processed", 0),
                    transfer_info.get("error_count", 0),
                    transfer_info.get("problem_bases"),
                    subject[:500],
                    received_at,
                ),
            )
            conn.commit()
            logger.info(
                "✅ Сохранён итог передачи на NAS: %s (%s)",
                transfer_info["host_name"],
                transfer_info["status"],
            )
        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения итога передачи на NAS: {exc}")
        finally:
            if "conn" in locals():
                conn.close()
