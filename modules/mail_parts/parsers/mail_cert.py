"""
/modules/mail_parts/parsers/mail_cert.py
Server Monitoring System v8.66.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
MailCertParserMixin — часть BackupProcessor.
Система мониторинга серверов
Версия: 8.66.0
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin MailCertParserMixin; объединяется с другими mixin'ами в BackupProcessor.
Парсит письма скрипта развёртывания сертификата почтового сервера (Zimbra):
тема `CERT <OK|WARN|CRIT> <host> CT<id> <EVENT> [key=value…]`, в теле — лог.
Разбор и хранение — в extensions/mail_cert_monitor.py.
"""

from __future__ import annotations

from datetime import datetime

from extensions.extension_manager import extension_manager
from extensions.mail_cert_monitor import EXTENSION_ID, parse_cert_subject, save_event
from modules.mail_parts import logger
from modules.mail_parts.patterns import get_mail_cert_patterns_from_config


class MailCertParserMixin:
    """Mixin MailCertParserMixin — методы для писем CERT о сертификате почты."""

    def parse_mail_cert(self, subject: str) -> dict | None:
        """Разбирает тему письма CERT; None — письмо не наше или расширение выключено."""
        if not extension_manager.is_extension_enabled(EXTENSION_ID):
            return None
        event = parse_cert_subject(subject, get_mail_cert_patterns_from_config())
        if event:
            logger.info(
                "✅ Сертификат почты: %s CT%s %s %s",
                event["host_name"],
                event["ct_id"],
                event["level"],
                event["event"],
            )
        return event

    def save_mail_cert(
        self,
        event: dict,
        subject: str,
        body: str = "",
        email_date: datetime | None = None,
    ) -> None:
        """Сохраняет событие CERT в mail_cert_events (оповещение шлёт основной цикл)."""
        try:
            is_new = save_event(event, subject, body, email_date, db_path=str(self.db_path))
            if is_new:
                logger.info("✅ Сохранено событие сертификата почты: %s", subject[:120])
            else:
                logger.info("ℹ️ Событие сертификата почты уже было сохранено: %s", subject[:120])
        except Exception as exc:
            logger.error(f"❌ Ошибка сохранения события сертификата почты: {exc}")
