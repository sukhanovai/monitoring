"""
/modules/mail_parts/processor.py
Server Monitoring System v8.62.78
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
BackupProcessor extracted from modules/mail_monitor.py (PR6 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.78
Автор: Александр Суханов (c)
Лицензия: MIT
Координатор обработки писем с отчётами о резервных копиях: чтение Maildir
и общие helper-методы. Бизнес-парсеры по типам писем разнесены по
modules/mail_parts/parsers/* mixin'ам (PR6c), DDL — в db/schema.py (PR6b).
"""

from __future__ import annotations

import ast
import email.policy
import fnmatch
import json
import re
import shutil
import sqlite3
import time
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

from config.db_settings import (
    BACKUP_DATABASE_CONFIG,
    BACKUP_PATTERNS,
    DATABASE_BACKUP_CONFIG,
    LOG_DIR,
    MAIL_MONITOR_LOG_FILE,
    MAILDIR_CUR,
    MAILDIR_NEW,
    ZFS_SERVERS,
)
from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from extensions.supplier_stock_files import (
    append_supplier_stock_report,
    cleanup_supplier_stock_archives,
    get_supplier_stock_config,
    process_supplier_stock_file,
    unpack_archive_file,
)
from lib.logging import setup_logging
from modules.mail_parts import logger
from modules.mail_parts.db.schema import create_schema
from modules.mail_parts.parsers import (
    DatabaseBackupParserMixin,
    MailBackupParserMixin,
    NasTransferParserMixin,
    ProxmoxBackupParserMixin,
    StockLoadParserMixin,
    ZfsBackupParserMixin,
)
from modules.mail_parts.patterns import (
    get_database_patterns_from_config,
    get_mail_patterns_from_config,
    get_snapshot_transfer_patterns_from_config,
    get_stock_load_patterns_from_config,
    get_zfs_patterns_from_config,
)


class BackupProcessor(
    ProxmoxBackupParserMixin,
    DatabaseBackupParserMixin,
    ZfsBackupParserMixin,
    MailBackupParserMixin,
    NasTransferParserMixin,
    StockLoadParserMixin,
):
    """Обработчик бэкапов."""

    def __init__(self) -> None:
        self.db_path = BACKUP_DATABASE_CONFIG["backups_db"]
        self.processed_files: set[str] = set()
        self.init_database()

    def init_database(self) -> None:
        """Инициализирует backups.db через `mail_parts.db.schema.create_schema`."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            try:
                create_schema(conn)
            finally:
                conn.close()
            logger.info("База данных бэкапов инициализирована")

        except Exception as exc:
            logger.error(f"Ошибка инициализации БД: {exc}")
            raise

    def process_new_emails(self) -> int:
        """Обрабатывает новые письма из директории new."""
        maildir_new = MAILDIR_NEW
        maildir_cur = MAILDIR_CUR

        if not maildir_new.exists():
            logger.error(f"Директория не существует: {maildir_new}")
            return 0

        processed_count = 0
        for file_path in maildir_new.iterdir():
            if not file_path.is_file():
                continue

            logger.info(f"🔍 Обнаружено новое письмо: {file_path.name}")

            result = self.parse_email_file(file_path)

            if result:
                try:
                    new_path = maildir_cur / file_path.name
                    shutil.move(str(file_path), str(new_path))
                    logger.info(f"✅ Письмо перемещено в cur: {file_path.name}")
                    self.processed_files.add(str(new_path))
                except Exception as exc:
                    logger.error(f"❌ Ошибка перемещения письма: {exc}")
                    self.processed_files.add(str(file_path))

                processed_count += 1
            else:
                logger.warning(f"⚠️ Не удалось обработать письмо: {file_path.name}")
                try:
                    new_path = maildir_cur / file_path.name
                    shutil.move(str(file_path), str(new_path))
                    self.processed_files.add(str(new_path))
                except Exception as exc:
                    logger.error(f"❌ Ошибка перемещения непрочитанного письма: {exc}")

        return processed_count

    def _match_subject_patterns(self, subject: str, patterns: list[str]) -> bool:
        """Проверяет тему письма по списку паттернов."""
        normalized_subject = re.sub(r"\s+", " ", subject).strip()
        for pattern in patterns:
            try:
                if re.search(pattern, subject, re.IGNORECASE):
                    return True
                if normalized_subject != subject and re.search(
                    pattern, normalized_subject, re.IGNORECASE
                ):
                    return True
            except re.error as exc:
                logger.warning("⚠️ Некорректный паттерн '%s': %s", pattern, exc)
        return False

    def _decode_attachment_payload(self, payload: bytes | None) -> str:
        """Пытается декодировать содержимое вложения."""
        if not payload:
            return ""

        for encoding in ("utf-8", "cp1251", "windows-1251", "latin-1"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue

        return payload.decode("utf-8", errors="ignore")

    def _match_regex(self, pattern: str, value: str) -> bool:
        try:
            return bool(re.search(pattern, value, re.IGNORECASE))
        except re.error as exc:
            logger.warning("⚠️ Некорректный паттерн '%s': %s", pattern, exc)
        return False

    def _normalize_rule_pattern(self, value: str) -> str:
        cleaned = str(value or "").strip()
        if not cleaned:
            return ""
        if cleaned[0] in ("'", '"') and cleaned[-1:] == cleaned[0]:
            cleaned = cleaned[1:-1].strip()
        return cleaned

    def _normalize_match_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip()).lower()

    def _decode_header_value(self, value: str | None) -> str:
        if not value:
            return ""
        try:
            parts = decode_header(value)
        except Exception:
            return str(value)
        decoded = []
        for payload, encoding in parts:
            if isinstance(payload, bytes):
                decoded.append(payload.decode(encoding or "utf-8", errors="ignore"))
            else:
                decoded.append(str(payload))
        return "".join(decoded).strip()

    def _get_attachment_filename(self, part) -> str:
        filename = part.get_filename() or part.get_param("name", header="content-type")
        return self._decode_header_value(filename)

    def _match_rule_pattern(self, pattern: str, value: str) -> bool:
        cleaned = self._normalize_rule_pattern(pattern)
        if not cleaned:
            return True
        if cleaned.lower().startswith("re:"):
            return self._match_regex(cleaned[3:].strip(), value)
        fragments = [part.strip() for part in cleaned.split("|") if part.strip()]
        if not fragments:
            return True
        haystack = self._normalize_match_text(value)
        for fragment in fragments:
            needle = self._normalize_match_text(fragment)
            if not needle:
                continue
            if any(char in needle for char in ("*", "?")):
                if fnmatch.fnmatch(haystack, needle):
                    return True
                continue
            if needle in haystack:
                return True
        return False

    def _get_sender_candidates(self, msg) -> list[str]:
        from_header = msg.get("from", "") or ""
        addresses = [addr for _, addr in getaddresses([from_header]) if addr]
        candidates = [from_header, *addresses]
        return [candidate.strip() for candidate in candidates if candidate.strip()]

    def _append_date_suffix(self, filename: str, timestamp: datetime) -> str:
        path = Path(filename)
        stamp = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{path.stem}_{stamp}{path.suffix}"

    def _resolve_attachment_name(self, source: dict, filename: str) -> str:
        base_name = Path(filename).stem if filename else "attachment"
        aliases = source.get("filename_aliases") or {}
        if isinstance(aliases, dict):
            for pattern, alias in aliases.items():
                if not pattern:
                    continue
                if self._match_rule_pattern(str(pattern), filename) or self._match_rule_pattern(
                    str(pattern),
                    base_name,
                ):
                    return str(alias)
        return base_name

    def _resolve_filename_aliases(
        self, source: dict, filename_pattern: str
    ) -> tuple[dict | None, str]:
        aliases = source.get("filename_aliases")
        if isinstance(aliases, dict):
            return aliases, filename_pattern
        if isinstance(filename_pattern, dict):
            return filename_pattern, ""
        if isinstance(filename_pattern, str):
            trimmed = filename_pattern.strip()
            if trimmed.startswith("{") and trimmed.endswith("}"):
                try:
                    parsed = json.loads(trimmed)
                except json.JSONDecodeError:
                    parsed = None
                if not isinstance(parsed, dict):
                    try:
                        parsed = ast.literal_eval(trimmed)
                    except (ValueError, SyntaxError):
                        parsed = None
                if isinstance(parsed, dict):
                    return parsed, ""
        return None, filename_pattern

    def _build_attachment_output_name(
        self,
        template: str,
        filename: str,
        index: int,
        name_override: str | None = None,
    ) -> str:
        base_name = Path(filename).stem if filename else "attachment"
        name_value = name_override or base_name
        try:
            return template.format(index=index, name=name_value, filename=filename, stem=base_name)
        except Exception:
            return template or filename or f"attachment_{index}"

    def _extract_matching_attachments(
        self,
        msg,
        filename_patterns: list[str],
    ) -> list[dict]:
        """Возвращает список вложений, подходящих под паттерны имени файла."""
        matched: list[dict] = []
        if not msg.is_multipart():
            return matched

        for part in msg.walk():
            filename = self._get_attachment_filename(part)
            if not filename:
                continue
            if filename_patterns and not self._match_subject_patterns(
                filename,
                filename_patterns,
            ):
                continue

            payload = part.get_payload(decode=True)
            content = self._decode_attachment_payload(payload)
            matched.append(
                {
                    "filename": filename,
                    "content": content,
                }
            )

        return matched
