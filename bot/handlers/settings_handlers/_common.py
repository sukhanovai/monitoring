"""
/bot/handlers/settings_handlers/_common.py
Server Monitoring System v8.62.99
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Общие низкоуровневые помощники модулей настроек.
Система мониторинга серверов
Версия: 8.62.99
Автор: Александр Суханов (c)
Лицензия: MIT
Лист-модуль без зависимостей от других модулей пакета settings_handlers.
Здесь живут приватные (`_`-префикс) утилиты, которые нужны сразу нескольким
модулям пакета (`_legacy`, `callback_dispatcher`, `supplier_stock`,
`backups/*`). Раньше они объявлялись в `_legacy.py`, но из-за того, что
`from ... import *` не переносит имена с ведущим подчёркиванием, ссылки на
них из вынесенных модулей падали с `name '...' is not defined`. Импортируйте
их отсюда явным списком.
"""

from __future__ import annotations

import re

from telegram.error import BadRequest, TelegramError
from telegram.utils.helpers import escape_markdown

from extensions.extension_manager import extension_manager


def _safe_query_answer(query, text: str | None = None, **kwargs) -> None:
    try:
        if text is None:
            query.answer(**kwargs)
        else:
            query.answer(text, **kwargs)
    except (BadRequest, TelegramError):
        pass


def _escape_pattern_text(text: str) -> str:
    """Экранирует текст для Markdown."""
    return escape_markdown(str(text or ""), version=1)


def _build_mail_pattern_from_fragments(fragments: list[str]) -> str:
    """Собрать regex паттерн из обязательных фрагментов."""
    cleaned = [fragment.strip() for fragment in fragments if fragment.strip()]
    if not cleaned:
        return ""
    escaped_parts = [re.escape(fragment) for fragment in cleaned]
    return r".*".join(escaped_parts)


def _format_current_hint(value, default: str = "не задано") -> str:
    """Сформировать подсказку для текущего значения."""
    if value is None:
        return default
    if isinstance(value, str) and value.strip() == "":
        return default
    return str(value)


def _format_archive_cleanup_days(value) -> str:
    """Сформировать отображение периода очистки архива."""
    try:
        days = int(str(value).strip())
    except (TypeError, ValueError):
        days = 0
    if days <= 0:
        return "выключено"
    return f"{days} дн."


def _parse_yes_no(value: str) -> bool | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in ("да", "yes", "y", "true", "1"):
        return True
    if lowered in ("нет", "no", "n", "false", "0"):
        return False
    return None


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parse_expected_attachments(raw_value: str) -> int | None:
    if not raw_value:
        return None
    try:
        value = int(raw_value)
    except ValueError:
        return None
    return value if value > 0 else None


def _enable_all_extensions_settings(query):
    enabled = 0
    for ext_id in extension_manager.get_extensions_status():
        success, _ = extension_manager.enable_extension(ext_id)
        if success:
            enabled += 1
    query.answer(f"✅ Включено {enabled} расширений")


def _disable_all_extensions_settings(query):
    disabled = 0
    for ext_id in extension_manager.get_extensions_status():
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled += 1
    query.answer(f"✅ Отключено {disabled} расширений")
