"""
/modules/mail_parts/parsers/stock_load.py
Server Monitoring System v8.62.70
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
StockLoadParserMixin — часть BackupProcessor (PR6c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.70
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin StockLoadParserMixin; объединяется с другими mixin'ами в BackupProcessor.
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
from modules.mail_parts.patterns import (
    get_database_patterns_from_config,
    get_mail_patterns_from_config,
    get_snapshot_transfer_patterns_from_config,
    get_stock_load_patterns_from_config,
    get_zfs_patterns_from_config,
)


class StockLoadParserMixin:
    """Mixin StockLoadParserMixin — методы для одного типа писем-отчётов."""

    def parse_supplier_stock_email(
        self,
        subject: str,
        msg,
        email_date: datetime | None,
    ) -> dict | None:
        """Парсит письма с файлами остатков поставщиков."""
        if not extension_manager.is_extension_enabled("supplier_stock_files"):
            return None

        config = get_supplier_stock_config()
        mail_config = config.get("mail", {})
        if not mail_config.get("enabled"):
            return None

        sources = mail_config.get("sources", [])
        if not isinstance(sources, list) or not sources:
            return None

        now = email_date or datetime.now()
        temp_dir = Path(mail_config.get("temp_dir") or "")
        temp_dir.mkdir(parents=True, exist_ok=True)

        sender_candidates = self._get_sender_candidates(msg)
        matched_files: list[str] = []

        for source in sources:
            if not isinstance(source, dict):
                continue
            if not source.get("enabled", True):
                continue

            sender_pattern = source.get("sender_pattern") or ""
            if sender_pattern:
                if not any(
                    self._match_rule_pattern(sender_pattern, candidate)
                    for candidate in sender_candidates
                ):
                    continue

            subject_pattern = source.get("subject_pattern") or ""
            if subject_pattern and not self._match_rule_pattern(subject_pattern, subject):
                continue

            expected = int(source.get("expected_attachments") or 1)
            mime_pattern = source.get("mime_pattern") or "application/"
            raw_filename_pattern = source.get("filename_pattern") or ""
            filename_aliases, filename_pattern = self._resolve_filename_aliases(
                source,
                str(raw_filename_pattern),
            )
            output_template = str(source.get("output_template") or "").strip()
            source_context = dict(source)
            if filename_aliases:
                source_context["filename_aliases"] = filename_aliases

            collected = 0
            if not msg.is_multipart():
                continue

            for part in msg.walk():
                filename = self._get_attachment_filename(part)
                if not filename:
                    continue

                content_type = part.get_content_type() or ""
                if mime_pattern and not self._match_rule_pattern(mime_pattern, content_type):
                    continue

                if filename_pattern and not self._match_rule_pattern(filename_pattern, filename):
                    continue

                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                output_name = filename
                if output_template:
                    name_override = self._resolve_attachment_name(source_context, filename)
                    output_name = self._build_attachment_output_name(
                        output_template,
                        filename,
                        collected + 1,
                        name_override,
                    )
                output_path = temp_dir / output_name
                output_path.write_bytes(payload)
                original_path = output_path

                if source.get("unpack_archive"):
                    unpacked_path = unpack_archive_file(output_path)
                    if unpacked_path:
                        output_path = unpacked_path
                        logger.info(
                            "📦 Вложение поставщика распаковано: %s -> %s",
                            filename,
                            output_path,
                        )
                processing_result = process_supplier_stock_file(
                    output_path,
                    source.get("id") or source.get("name"),
                    "mail",
                    collected + 1,
                    original_path,
                )
                source_id = source.get("id") or source.get("name") or "unknown"
                source_name = source.get("name") or source_id
                report_entry = {
                    "timestamp": now.isoformat(),
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_kind": "mail",
                    "status": "success",
                    "filename": filename,
                    "output_name": output_name,
                    "path": str(output_path),
                }
                if processing_result:
                    report_entry["processing"] = processing_result
                append_supplier_stock_report(report_entry)
                if processing_result:
                    logger.info(
                        "🧩 Обработка остатков выполнена: %s",
                        processing_result.get("rules"),
                    )

                matched_files.append(str(output_path))
                collected += 1

                logger.info(
                    "📦 Сохранено вложение поставщика: %s -> %s",
                    filename,
                    output_path,
                )

                if collected >= expected:
                    break

            if collected < expected:
                logger.warning(
                    "⚠️ Для правила '%s' найдено %s/%s вложений",
                    source.get("name") or source.get("id") or "без имени",
                    collected,
                    expected,
                )

        if not matched_files:
            logger.info(
                "📭 Письмо не соответствует правилам остатков поставщиков: %s",
                subject[:80],
            )
            return None

        cleanup_supplier_stock_archives(config, now)
        return {"supplier_stock_files": matched_files}

    def _match_stock_load_source(self, subject: str, patterns: dict[str, list[str]]) -> str:
        """Определяет источник отчёта по теме письма."""
        sources = patterns.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                name = str(source.get("name") or "").strip()
                if not name:
                    continue
                subject_patterns = source.get("subject", [])
                if not isinstance(subject_patterns, list):
                    continue
                if self._match_subject_patterns(subject, subject_patterns):
                    return name
        return "Основное предприятие"

    def parse_stock_load_log(
        self,
        content: str,
        patterns: dict[str, list[str]],
    ) -> list[dict]:
        """Парсит содержимое лога загрузки остатков."""
        file_entry_patterns = patterns.get("file_entry", [])
        success_patterns = patterns.get("success", [])
        failure_patterns = patterns.get("failure", [])
        ignore_patterns = patterns.get("ignore", [])

        default_file_entry = (
            r"^\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}:\s+"
            r"(?P<supplier>.+?)\s{2,}(?P<path>(?:[A-Za-z]:\\|\\\\[^\\]+\\).+)$"
        )
        if default_file_entry not in file_entry_patterns:
            file_entry_patterns = [*file_entry_patterns, default_file_entry]

        file_entry_regexes = [re.compile(pat, re.IGNORECASE) for pat in file_entry_patterns]
        success_regexes = [re.compile(pat, re.IGNORECASE) for pat in success_patterns]
        failure_regexes = [re.compile(pat, re.IGNORECASE) for pat in failure_patterns]
        ignore_regexes = [re.compile(pat, re.IGNORECASE) for pat in ignore_patterns]

        entries: list[dict] = []
        current: dict | None = None
        fallback_entry = {
            "supplier_name": "неизвестно",
            "file_path": None,
            "rows_count": None,
            "errors": [],
            "has_success": False,
            "has_failure": False,
            "log_timestamp": None,
        }

        def finalize_current() -> None:
            nonlocal current
            if not current:
                return

            has_success = current.get("has_success", False)
            has_failure = current.get("has_failure", False)
            if has_success and has_failure:
                status = "warning"
            elif has_success:
                status = "success"
            elif has_failure:
                status = "failed"
            else:
                status = "unknown"

            current["status"] = status
            current["error_count"] = len(current.get("errors", []))
            if current.get("errors"):
                current["error_sample"] = current["errors"][0][:500]
            else:
                current["error_sample"] = None

            entries.append(current)
            current = None

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            file_match = None
            for regex in file_entry_regexes:
                file_match = regex.search(line)
                if file_match:
                    break

            if file_match:
                finalize_current()

                supplier = None
                path = None
                match_groups = file_match.groupdict()
                if match_groups:
                    supplier = match_groups.get("supplier")
                    path = match_groups.get("path")
                if supplier is None and file_match.lastindex:
                    supplier = file_match.group(1)
                if path is None and file_match.lastindex and file_match.lastindex >= 2:
                    path = file_match.group(2)

                supplier = " ".join((supplier or "").split()) or "неизвестно"
                path = path.strip() if isinstance(path, str) else None

                timestamp_match = re.match(
                    r"^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
                    line,
                )
                log_timestamp = timestamp_match.group(1) if timestamp_match else None

                current = {
                    "supplier_name": supplier,
                    "file_path": path,
                    "rows_count": None,
                    "errors": [],
                    "has_success": False,
                    "has_failure": False,
                    "log_timestamp": log_timestamp,
                }
                continue

            if not current:
                ignored = False
                for regex in ignore_regexes:
                    if regex.search(line):
                        ignored = True
                        break
                if ignored:
                    continue

                success_match = None
                for regex in success_regexes:
                    success_match = regex.search(line)
                    if success_match:
                        break

                if success_match:
                    fallback_entry["has_success"] = True
                    if fallback_entry["log_timestamp"] is None:
                        timestamp_match = re.match(
                            r"^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
                            line,
                        )
                        fallback_entry["log_timestamp"] = (
                            timestamp_match.group(1) if timestamp_match else None
                        )
                    rows_value = None
                    match_groups = success_match.groupdict()
                    if match_groups:
                        rows_value = match_groups.get("rows")
                    if rows_value is None and success_match.lastindex:
                        rows_value = success_match.group(1)
                    try:
                        fallback_entry["rows_count"] = int(str(rows_value)) if rows_value else None
                    except ValueError:
                        fallback_entry["rows_count"] = None
                    continue

                failure_match = None
                for regex in failure_regexes:
                    failure_match = regex.search(line)
                    if failure_match:
                        break

                if failure_match:
                    fallback_entry["has_failure"] = True
                    if fallback_entry["log_timestamp"] is None:
                        timestamp_match = re.match(
                            r"^(\d{2}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})",
                            line,
                        )
                        fallback_entry["log_timestamp"] = (
                            timestamp_match.group(1) if timestamp_match else None
                        )
                    fallback_entry["errors"].append(line)
                continue

            ignored = False
            for regex in ignore_regexes:
                if regex.search(line):
                    ignored = True
                    break
            if ignored:
                continue

            success_match = None
            for regex in success_regexes:
                success_match = regex.search(line)
                if success_match:
                    break

            if success_match:
                current["has_success"] = True
                rows_value = None
                match_groups = success_match.groupdict()
                if match_groups:
                    rows_value = match_groups.get("rows")
                if rows_value is None and success_match.lastindex:
                    rows_value = success_match.group(1)
                try:
                    current["rows_count"] = int(str(rows_value)) if rows_value else None
                except ValueError:
                    current["rows_count"] = None
                continue

            failure_match = None
            for regex in failure_regexes:
                failure_match = regex.search(line)
                if failure_match:
                    break

            if failure_match:
                current["has_failure"] = True
                current["errors"].append(line)
                continue

        finalize_current()

        if not entries and (fallback_entry["has_success"] or fallback_entry["has_failure"]):
            has_success = fallback_entry.get("has_success", False)
            has_failure = fallback_entry.get("has_failure", False)
            if has_success and has_failure:
                status = "warning"
            elif has_success:
                status = "success"
            elif has_failure:
                status = "failed"
            else:
                status = "unknown"

            fallback_entry["status"] = status
            fallback_entry["error_count"] = len(fallback_entry.get("errors", []))
            if fallback_entry.get("errors"):
                fallback_entry["error_sample"] = fallback_entry["errors"][0][:500]
            else:
                fallback_entry["error_sample"] = None

            entries.append(fallback_entry)

        return entries

    def save_stock_load_entries(
        self,
        entries: list[dict],
        subject: str,
        attachment_name: str | None,
        source_name: str | None,
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет результаты загрузки остатков в БД."""
        if not entries:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            received_at = (
                email_date.strftime("%Y-%m-%d %H:%M:%S")
                if email_date
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            for entry in entries:
                supplier_name = entry.get("supplier_name")
                if not supplier_name or supplier_name == "неизвестно":
                    supplier_name = source_name or "неизвестно"
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO stock_load_results
                    (supplier_name, source_name, file_path, status, rows_count, error_count, error_sample,
                    attachment_name, log_timestamp, email_subject, received_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        supplier_name,
                        source_name,
                        entry.get("file_path"),
                        entry.get("status", "unknown"),
                        entry.get("rows_count"),
                        entry.get("error_count", 0),
                        entry.get("error_sample"),
                        attachment_name,
                        entry.get("log_timestamp"),
                        subject[:500],
                        received_at,
                    ),
                )

            conn.commit()
            logger.info("✅ Сохранены результаты загрузки остатков: %s", len(entries))

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения остатков в БД: {exc}")
        finally:
            if "conn" in locals():
                conn.close()

    def parse_stock_load_email(
        self,
        subject: str,
        msg,
        email_date: datetime | None,
    ) -> dict | None:
        """Парсит письмо с логами загрузки остатков."""
        if not extension_manager.is_extension_enabled("stock_load_monitor"):
            return None

        patterns = get_stock_load_patterns_from_config()
        subject_patterns = patterns.get("subject", [])
        sources = patterns.get("sources", [])
        matches_subject = (
            self._match_subject_patterns(subject, subject_patterns) if subject_patterns else True
        )
        matches_source = False
        if isinstance(sources, list) and sources:
            for source in sources:
                if not isinstance(source, dict):
                    continue
                source_subject = source.get("subject", [])
                if not isinstance(source_subject, list):
                    continue
                if self._match_subject_patterns(subject, source_subject):
                    matches_source = True
                    break

        if not matches_subject and not matches_source:
            return None

        source_name = self._match_stock_load_source(subject, patterns)

        attachment_patterns = patterns.get("attachment", [])
        attachments = self._extract_matching_attachments(msg, attachment_patterns)
        if not attachments:
            logger.warning("⚠️ Лог остатков не найден во вложениях письма: %s", subject)
            return None

        all_entries: list[dict] = []
        for attachment in attachments:
            content = attachment.get("content", "")
            entries = self.parse_stock_load_log(content, patterns)
            self.save_stock_load_entries(
                entries,
                subject,
                attachment.get("filename"),
                source_name,
                email_date,
            )
            all_entries.extend(entries)

        if not all_entries:
            logger.warning("⚠️ Не удалось извлечь результаты остатков из письма: %s", subject)
            return None

        return {"stock_load_entries": all_entries}
