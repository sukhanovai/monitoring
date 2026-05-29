"""
/modules/mail_parts/parsers/proxmox.py
Server Monitoring System v8.62.68
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ProxmoxBackupParserMixin — часть BackupProcessor (PR6c серии оптимизации).
Система мониторинга серверов
Версия: 8.62.68
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin ProxmoxBackupParserMixin; объединяется с другими mixin'ами в BackupProcessor.
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


class ProxmoxBackupParserMixin:
    """Mixin ProxmoxBackupParserMixin — методы для одного типа писем-отчётов."""

    def parse_email_file(self, file_path: Path) -> dict | None:
        """Парсит email файл."""
        try:
            logger.info(f"Обработка файла: {file_path}")

            msg = message_from_bytes(
                Path(file_path).read_bytes(),
                policy=email.policy.default,
            )

            subject = msg.get("subject", "")
            email_date_str = msg.get("date", "")
            logger.info(f"Тема письма: {subject}")
            logger.info(f"Дата письма: {email_date_str}")

            email_date = None
            if email_date_str:
                try:
                    email_date = parsedate_to_datetime(email_date_str)
                    logger.info(f"✅ Дата письма распарсена: {email_date}")
                except Exception as exc:
                    logger.warning(
                        "Не удалось распарсить дату письма '%s': %s",
                        email_date_str,
                        exc,
                    )
                    try:
                        email_date = datetime.strptime(
                            email_date_str,
                            "%a, %d %b %Y %H:%M:%S %z",
                        )
                        logger.info(
                            "✅ Дата письма распарсена альтернативным методом: %s",
                            email_date,
                        )
                    except Exception:
                        logger.warning(
                            "❌ Не удалось распарсить дату альтернативным методом, используем текущее время"
                        )
                        email_date = datetime.now()
            else:
                logger.warning("❌ Дата письма отсутствует, используем текущее время")
                email_date = datetime.now()

            db_backup_info = self.parse_database_backup(subject, self.get_email_body(msg))
            if db_backup_info:
                logger.info(
                    "📊 Обнаружен бэкап базы данных: %s",
                    db_backup_info["database_display_name"],
                )
                self.save_database_backup(db_backup_info, subject, email_date)
                return db_backup_info

            zfs_entries = self.parse_zfs_status(subject)
            if zfs_entries:
                self.save_zfs_status(zfs_entries, subject, email_date)
                return {"zfs_entries": zfs_entries}

            snapshot_transfer = self.parse_snapshot_transfer(subject, self.get_email_body(msg))
            if snapshot_transfer:
                self.save_snapshot_transfer(snapshot_transfer, subject, email_date)
                return {"snapshot_transfer": snapshot_transfer}

            nas_transfer = self.parse_nas_transfer(subject, self.get_email_body(msg))
            if nas_transfer:
                self.save_nas_transfer(nas_transfer, subject, email_date)
                return {"nas_transfer": nas_transfer}

            mail_backup_info = self.parse_mail_backup(subject)
            if mail_backup_info:
                self.save_mail_backup(mail_backup_info, subject, email_date)
                return mail_backup_info

            supplier_stock_info = self.parse_supplier_stock_email(subject, msg, email_date)
            if supplier_stock_info:
                return supplier_stock_info

            stock_load_info = self.parse_stock_load_email(subject, msg, email_date)
            if stock_load_info:
                return stock_load_info

            if not self.is_proxmox_backup_email(subject):
                logger.info(
                    "Пропускаем не-Proxmox/БД/ZFS/передачи снэпшотов/NAS/почта/остатки письмо: %s...",
                    subject[:50],
                )
                return None

            backup_info = self.parse_subject(subject)
            if not backup_info:
                logger.warning("Не удалось извлечь информацию из темы")
                return None

            body = self.get_email_body(msg)
            backup_info.update(self.parse_body(body))

            self.save_backup_report(backup_info, subject, email_date)

            return backup_info

        except Exception as exc:
            logger.error(f"Ошибка парсинга файла {file_path}: {exc}")
            return None

    def is_proxmox_backup_email(self, subject: str) -> bool:
        """Проверяет, является ли письмо отчетом о бэкапе Proxmox."""
        subject_lower = subject.lower()
        return any(
            keyword in subject_lower
            for keyword in [
                "vzdump backup status",
                "proxmox backup",
                "backup successful",
                "backup failed",
            ]
        )

    def _resolve_proxmox_host_name(self, raw_host_name: str) -> str:
        """Нормализует имя хоста Proxmox под конфигурацию (например, sr-pve3)."""
        host_name = str(raw_host_name or "").strip()
        if not host_name:
            return host_name

        normalized = host_name.lower()

        proxmox_hosts = config_manager.get_setting("PROXMOX_HOSTS", {}, use_cache=False)
        if not isinstance(proxmox_hosts, dict):
            return host_name

        configured_hosts = {
            str(config_name).strip(): value
            for config_name, value in proxmox_hosts.items()
            if str(config_name).strip()
        }
        if not configured_hosts:
            return host_name

        for config_name, host_value in configured_hosts.items():
            config_normalized = config_name.lower()
            if normalized == config_normalized:
                return config_name

            if config_normalized.startswith("sr-") and normalized == config_normalized[3:]:
                return config_name

            if config_normalized.endswith(f".{normalized}"):
                return config_name

            if isinstance(host_value, dict):
                alias_candidates = [
                    host_value.get("host"),
                    host_value.get("hostname"),
                    host_value.get("name"),
                    host_value.get("pattern"),
                ]
            else:
                alias_candidates = [host_value]

            for candidate in alias_candidates:
                candidate_str = str(candidate or "").strip().lower()
                if not candidate_str:
                    continue
                if candidate_str == normalized:
                    return config_name
                if candidate_str.startswith("sr-") and candidate_str[3:] == normalized:
                    return config_name
                if normalized in candidate_str:
                    return config_name

        if normalized.startswith(("pve", "bup")):
            sr_candidate = f"sr-{normalized}"
            for config_name in configured_hosts.keys():
                if config_name.lower() == sr_candidate:
                    return config_name

        return host_name

    def parse_subject(self, subject: str) -> dict | None:
        """Парсит тему письма."""
        if "pve2-rubicon" in subject.lower():
            host_name = self._resolve_proxmox_host_name("pve2-rubicon")
            status_match = re.search(r":\s*([^:]+)$", subject)
            if status_match:
                raw_status = status_match.group(1).strip().lower()
                normalized_status = self.normalize_status(raw_status)
                return {
                    "host_name": host_name,
                    "backup_status": normalized_status,
                    "raw_status": raw_status,
                    "task_type": "vzdump",
                }

        if "pve-rubicon" in subject.lower() and "pve2-rubicon" not in subject.lower():
            host_name = self._resolve_proxmox_host_name("pve-rubicon")
            status_match = re.search(r":\s*([^:]+)$", subject)
            if status_match:
                raw_status = status_match.group(1).strip().lower()
                normalized_status = self.normalize_status(raw_status)
                return {
                    "host_name": host_name,
                    "backup_status": normalized_status,
                    "raw_status": raw_status,
                    "task_type": "vzdump",
                }

        host_match = re.search(r"\(([^)]+)\)", subject)
        if not host_match:
            logger.warning(f"Не удалось извлечь имя хоста: {subject}")
            return None

        host_name_raw = host_match.group(1).split(".")[0]
        host_name = self._resolve_proxmox_host_name(host_name_raw)

        status_match = re.search(r":\s*([^:]+)$", subject)
        if not status_match:
            logger.warning(f"Не удалось извлечь статус: {subject}")
            return None

        raw_status = status_match.group(1).strip().lower()
        normalized_status = self.normalize_status(raw_status)

        return {
            "host_name": host_name,
            "backup_status": normalized_status,
            "raw_status": raw_status,
            "task_type": "vzdump",
        }

    def normalize_status(self, raw_status: str) -> str:
        """Нормализует статус бэкапа."""
        normalized_raw_status = re.sub(r"[.\s]+$", "", raw_status.strip().lower())
        status_map = {
            "backup successful": "success",
            "successful": "success",
            "ok": "success",
            "backup failed": "failed",
            "failed": "failed",
            "error": "failed",
        }
        return status_map.get(normalized_raw_status, normalized_raw_status)

    def get_email_body(self, msg) -> str:
        """Извлекает тело письма."""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        return part.get_content()
            else:
                return msg.get_content()
        except Exception as exc:
            logger.error(f"Ошибка извлечения тела письма: {exc}")

        return ""

    def parse_body(self, body: str) -> dict:
        """Парсит тело письма для извлечения корректной информации."""
        info = {
            "duration": None,
            "total_size": None,
            "error_message": None,
            "vm_count": 0,
            "successful_vms": 0,
            "failed_vms": 0,
        }

        try:
            lines = body.split("\n")
            in_details_section = False

            for line in lines:
                line = line.strip()
                line_lower = line.lower()

                if any(
                    keyword in line_lower
                    for keyword in [
                        "total size",
                        "backup size",
                        "size:",
                        "data size",
                        "total backup",
                    ]
                ):
                    size_patterns = [
                        r"(\d+\.?\d*)\s*([TGMK]i?B)",
                        r"(\d[\d,]*\.?\d*)\s*([TGMK]i?B)",
                        r"size[:\s]+(\d+\.?\d*)\s*([TGMK]i?B)",
                    ]

                    for pattern in size_patterns:
                        size_match = re.search(pattern, line, re.IGNORECASE)
                        if size_match:
                            size_value = size_match.group(1).replace(",", "")
                            size_unit = size_match.group(2).upper()
                            info["total_size"] = f"{size_value} {size_unit}"
                            break

                if "total running time" in line_lower:
                    time_match = re.search(r"(\d+[hm]\s*\d*[sm]*)", line, re.IGNORECASE)
                    if time_match:
                        raw_time = time_match.group(1)
                        info["duration"] = self.parse_duration(raw_time)

                elif "vmid" in line_lower and "name" in line_lower and "status" in line_lower:
                    in_details_section = True
                    continue

                elif in_details_section and re.match(r"^\d+\s+", line):
                    parts = line.split()
                    if len(parts) >= 4:
                        info["vm_count"] += 1
                        status = parts[2].lower()
                        if status == "ok":
                            info["successful_vms"] += 1
                        else:
                            info["failed_vms"] += 1

                elif in_details_section and not line:
                    in_details_section = False

                elif "error" in line_lower or "failed" in line_lower:
                    if not info["error_message"] and len(line) > 10:
                        info["error_message"] = line[:200]

            if not info["duration"] and info["vm_count"] > 0:
                total_seconds = 0
                for line in lines:
                    time_match = re.search(r"(\d+m\s*\d*s)", line)
                    if time_match:
                        vm_time = time_match.group(1)
                        total_seconds += self.duration_to_seconds(vm_time)

                if total_seconds > 0:
                    info["duration"] = self.seconds_to_duration(total_seconds)

        except Exception as exc:
            logger.error(f"Ошибка парсинга тела письма: {exc}")

        return info

    def parse_duration(self, duration_str: str) -> str:
        """Парсит строку длительности в читаемый формат."""
        try:
            duration_str = duration_str.lower().replace(" ", "")

            hours = 0
            minutes = 0
            seconds = 0

            h_match = re.search(r"(\d+)h", duration_str)
            if h_match:
                hours = int(h_match.group(1))

            m_match = re.search(r"(\d+)m", duration_str)
            if m_match:
                minutes = int(m_match.group(1))

            s_match = re.search(r"(\d+)s", duration_str)
            if s_match:
                seconds = int(s_match.group(1))

            if hours > 0:
                return f"{hours}h {minutes:02d}m {seconds:02d}s"
            if minutes > 0:
                return f"{minutes}m {seconds:02d}s"
            return f"{seconds}s"

        except Exception as exc:
            logger.error(f"Ошибка парсинга длительности '{duration_str}': {exc}")
            return duration_str

    def duration_to_seconds(self, duration_str: str) -> int:
        """Конвертирует строку длительности в секунды."""
        try:
            total_seconds = 0
            duration_str = duration_str.lower().replace(" ", "")

            m_match = re.search(r"(\d+)m", duration_str)
            if m_match:
                total_seconds += int(m_match.group(1)) * 60

            s_match = re.search(r"(\d+)s", duration_str)
            if s_match:
                total_seconds += int(s_match.group(1))

            return total_seconds
        except Exception:
            return 0

    def seconds_to_duration(self, total_seconds: int) -> str:
        """Конвертирует секунды в читаемую длительность."""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        if minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        return f"{seconds}s"

    def save_backup_report(
        self, backup_info: dict, subject: str, email_date: datetime | None = None
    ) -> None:
        """Сохраняет отчет в базу с корректным временем, игнорируя дубликаты."""
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
                INSERT OR IGNORE INTO proxmox_backups
                (host_name, backup_status, task_type, duration, total_size, error_message,
                email_subject, received_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    backup_info["host_name"],
                    backup_info["backup_status"],
                    backup_info["task_type"],
                    backup_info.get("duration"),
                    backup_info.get("total_size"),
                    backup_info.get("error_message"),
                    subject[:500],
                    received_at,
                ),
            )

            conn.commit()
            logger.info(
                "✅ Сохранен бэкап: %s - %s",
                backup_info["host_name"],
                backup_info["backup_status"],
            )

        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения в БД: {exc}")
        finally:
            if "conn" in locals():
                conn.close()
