"""
/modules/mail_parts/parsers/ids_cert.py
Server Monitoring System v9.0.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
IdsCertParserMixin — часть BackupProcessor.
Система мониторинга серверов
Версия: 9.0.0
Автор: Александр Суханов (c)
Лицензия: MIT
Mixin IdsCertParserMixin; объединяется с другими mixin'ами в BackupProcessor.
Письма IDS (взлом контейнеров Proxmox) и CERT (замена сертификата почты)
от скриптов на хосте PVE. Разбор, журнал и автомат состояний — в
extensions/ids_cert_monitor.py; здесь только вызов и защита от потери письма.
"""

from __future__ import annotations

from extensions.ids_cert_monitor import (
    enqueue_processing_error,
    handle_email,
    is_ids_cert_subject,
)
from modules.mail_parts import logger


class IdsCertParserMixin:
    """Mixin IdsCertParserMixin — письма `IDS …` / `CERT …`."""

    def process_ids_cert_email(self, subject: str, msg) -> dict | None:
        """Обрабатывает письмо IDS/CERT. None — письмо не наше.

        Вызывается раньше всех остальных парсеров. Любая ошибка — отдельное
        оповещение, а не строка в логе: письмо безопасности не должно теряться.
        """
        subject = str(subject or "")
        if not is_ids_cert_subject(subject):
            return None
        try:
            result = handle_email(
                subject,
                body=self.get_email_body(msg),
                message_id=str(msg.get("message-id") or ""),
                date_header=str(msg.get("date") or "") or None,
                db_path=str(self.db_path),
            )
        except Exception as exc:
            logger.error("❌ Ошибка обработки письма IDS/CERT '%s': %s", subject[:120], exc)
            enqueue_processing_error(subject, str(exc), db_path=str(self.db_path))
            return {"ids_cert": {"outcome": "error", "error": str(exc)}}
        logger.info("🛡️ %s", (result or {}).get("log", subject[:120]))
        return {"ids_cert": result}
