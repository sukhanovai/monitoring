"""
/bot/handlers/settings_handlers/supplier_stock.py
Server Monitoring System v8.62.82
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Supplier stock UI handlers extracted from
bot/handlers/settings_handlers/_legacy.py (PR7b серии оптимизации).
Система мониторинга серверов
Версия: 8.62.82
Автор: Александр Суханов (c)
Лицензия: MIT
Самодостаточный блок UI Telegram-бота для настроек supplier-stock
расширения: ~84 функции (меню источников/писем/обработки/расписания/
ресурсов/FTP, мастера создания и редактирования, обработчики ввода
и пр.). Имена сохранены — фасадный `__init__.py` пакета продолжает
реэкспортировать всё.
"""

import ast
import json
import re
import sqlite3
from datetime import datetime
from urllib.parse import quote, unquote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler
from telegram.utils.helpers import escape_markdown

from bot.handlers.zfs_pool_free_space_handlers import handle_text_input as handle_zfsp_text_input
from config.db_settings import BACKUP_DATABASE_CONFIG, load_all_settings
from config.settings import BACKUP_DB_FILE, BACKUP_PATTERNS as DEFAULT_BACKUP_PATTERNS
from core.config_manager import config_manager as settings_manager
from extensions.extension_manager import extension_manager
from extensions.supplier_stock_files import (
    SUPPLIER_STOCK_EXTENSION_ID,
    build_supplier_stock_source_stats,
    get_supplier_stock_config,
    get_supplier_stock_reports,
    parse_supplier_stock_schedule_times,
    save_supplier_stock_config,
    summarize_supplier_stock_reports,
)
from extensions.zfs_free_space_monitor import get_zfs_servers_config
from lib.logging import debug_log

BACKUP_SETTINGS_CALLBACKS = {
    "backup_times",
    "settings_backup_databases",
    "backup_db_add_category",
    "view_patterns",
    "add_pattern",
    "add_zfs_pattern",
    "add_proxmox_pattern",
    "add_mail_pattern",
    "add_stock_pattern",
    "add_snapshot_pattern",
    "edit_mail_default_pattern",
    "mail_pattern_confirm",
    "mail_pattern_retry",
    "stock_pattern_confirm",
    "stock_pattern_retry",
    "zfs_pattern_confirm",
    "zfs_pattern_retry",
    "db_pattern_confirm",
    "db_pattern_retry",
    "proxmox_pattern_confirm",
    "proxmox_pattern_retry",
    "snapshot_pattern_confirm",
    "snapshot_pattern_retry",
    "settings_patterns_db_from_backup",
}


debug_logger = debug_log


def _build_stock_subject_pattern(subject: str) -> str:
    """Собрать regex паттерн для темы письма загрузки остатков."""
    if not subject:
        return ""

    normalized = subject.strip()
    if not normalized:
        return ""

    time_regex = r"\b\d{2}:\d{2}:\d{2}\b"
    date_regex = r"\b\d{2}[./-]\d{2}[./-]\d{2,4}\b"

    draft = re.sub(time_regex, "__TIME__", normalized)
    draft = re.sub(date_regex, "__DATE__", draft)

    escaped = re.escape(draft)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)

    escaped = escaped.replace(re.escape("__TIME__"), r"\d{2}:\d{2}:\d{2}")
    escaped = escaped.replace(re.escape("__DATE__"), r"\d{2}[./-]\d{2}[./-]\d{2,4}")
    return escaped


def _build_stock_pattern_from_fragments(fragments: list[str]) -> str:
    """Собрать regex паттерн для остатков из обязательных фрагментов."""
    return _build_mail_pattern_from_fragments(fragments)


def _build_stock_success_pattern(sample: str) -> str:
    """Собрать regex паттерн успеха по примеру строки."""
    normalized = sample.strip()
    if not normalized:
        return ""

    date_regex = r"\b\d{2}\.\d{2}\.\d{2}\b"
    time_regex = r"\b\d{2}:\d{2}:\d{2}\b"

    draft = re.sub(date_regex, "__DATE__", normalized)
    draft = re.sub(time_regex, "__TIME__", draft)
    draft = re.sub(r"(строк\s+)\d+", r"\1__ROWS__", draft, flags=re.IGNORECASE)

    escaped = re.escape(draft)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)

    escaped = escaped.replace(re.escape("__DATE__"), r"\d{2}\.\d{2}\.\d{2}")
    escaped = escaped.replace(re.escape("__TIME__"), r"\d{2}:\d{2}:\d{2}")
    escaped = escaped.replace(re.escape("__ROWS__"), r"(?P<rows>\d+)")
    return escaped


def _get_stock_load_fallback_patterns() -> dict[str, list[str]]:
    """Получить запасные паттерны для загрузки остатков."""
    fallback_raw = settings_manager.get_setting("BACKUP_PATTERNS", DEFAULT_BACKUP_PATTERNS)
    if isinstance(fallback_raw, str):
        try:
            fallback_raw = json.loads(fallback_raw)
        except json.JSONDecodeError:
            fallback_raw = {}
    if not fallback_raw:
        fallback_raw = DEFAULT_BACKUP_PATTERNS

    stock_patterns = fallback_raw.get("stock_load", {})
    if not isinstance(stock_patterns, dict):
        return {}

    return {
        key: [p for p in value if isinstance(p, str)]
        for key, value in stock_patterns.items()
        if isinstance(value, list)
    }


def show_stock_load_settings(update, context):
    """Показать настройки загрузки остатков 1С в разделе расширений."""
    query = update.callback_query
    query.answer()

    pattern_count = 0
    source_label = "база"
    patterns = settings_manager.get_backup_patterns()
    if isinstance(patterns, str):
        try:
            patterns = json.loads(patterns)
        except json.JSONDecodeError:
            patterns = {}

    stock_patterns = patterns.get("stock_load", {})
    if isinstance(stock_patterns, dict):
        pattern_count = sum(
            len(value) for value in stock_patterns.values() if isinstance(value, list)
        )

    if pattern_count == 0:
        fallback_patterns = _get_stock_load_fallback_patterns()
        pattern_count = sum(len(value) for value in fallback_patterns.values())
        if pattern_count:
            source_label = "по умолчанию"
        else:
            source_label = "не настроены"

    message = (
        "📦 *Загрузка остатков 1С*\n\n"
        f"Паттернов: {pattern_count} ({source_label})\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("🔍 Паттерны", callback_data="settings_patterns_stock")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_extensions"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_settings(update, context):
    """Показать настройки получения файлов остатков поставщиков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_edit", None)
    context.user_data.pop("supplier_stock_archive_cleanup_back", None)
    context.user_data.pop("supplier_stock_archive_cleanup_back", None)
    context.user_data.pop("supplier_stock_add_source", None)
    context.user_data.pop("supplier_stock_mail_edit", None)
    context.user_data.pop("supplier_stock_mail_add_source", None)
    context.user_data.pop("supplier_stock_processing_add", None)
    context.user_data.pop("supplier_stock_processing_stage", None)
    context.user_data.pop("supplier_stock_processing_data", None)
    context.user_data.pop("supplier_stock_processing_edit", None)
    context.user_data.pop("supplier_stock_processing_edit_id", None)
    context.user_data.pop("supplier_stock_source_settings_id", None)
    context.user_data.pop("supplier_stock_mail_source_settings_id", None)
    context.user_data.pop("supplier_stock_source_field", None)
    context.user_data.pop("supplier_stock_source_field_id", None)
    context.user_data.pop("supplier_stock_mail_source_field", None)
    context.user_data.pop("supplier_stock_mail_source_field_id", None)
    context.user_data.pop("supplier_stock_resource_settings_id", None)
    context.user_data.pop("supplier_stock_resource_field", None)
    context.user_data.pop("supplier_stock_resource_field_id", None)
    context.user_data.pop("supplier_stock_resource_add", None)
    context.user_data.pop("supplier_stock_resource_stage", None)
    context.user_data.pop("supplier_stock_resource_data", None)
    context.user_data.pop("supplier_stock_ftp_field", None)

    config = get_supplier_stock_config()
    download = config.get("download", {})
    sources = download.get("sources", [])
    schedule = download.get("schedule", {})
    mail_settings = config.get("mail", {})
    mail_status = "🟢 Включено" if mail_settings.get("enabled") else "🔴 Выключено"
    mail_rules = len(mail_settings.get("sources", []))

    schedule_state = "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено"
    schedule_time = schedule.get("time", "не задано")

    reporting_days = config.get("reporting", {}).get("period_days", 7)
    message = (
        "📦 *Остатки поставщиков*\n\n"
        f"Источников: {len(sources)}\n"
        f"Расписание: {schedule_state} ({schedule_time})\n\n"
        "📧 *Почтовые сообщения (остатки)*\n\n"
        f"Статус: {mail_status}\n"
        f"Правил: {mail_rules}\n\n"
        "🗓 *Отчёты*\n"
        f"Период: {reporting_days} дн.\n\n"
        "Выберите раздел:"
    )

    keyboard = [
        [InlineKeyboardButton("🌐 Скачивание файлов", callback_data="supplier_stock_download")],
        [InlineKeyboardButton("📧 Почтовые сообщения", callback_data="supplier_stock_mail")],
        [InlineKeyboardButton("🗓 Период отчётов", callback_data="supplier_stock_report_period")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_extensions"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _format_supplier_stock_timestamp(value: str | None) -> str:
    """Сформировать читаемое время запуска."""
    if not value:
        return "неизвестно"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(value)


def _supplier_stock_status_label(status: str | None, fallback: str = "неизвестно") -> str:
    """Сформировать короткую метку статуса."""
    if status == "success":
        return "🟢 успешно"
    if status == "error":
        return "🔴 ошибка"
    if status == "skipped":
        return "⚪️ пропущено"
    return f"🟡 {fallback}"


def _supplier_stock_processing_status(processing: dict | None) -> str:
    """Определить статус обработки."""
    if not processing:
        return "⏭️ не запускалась"
    if processing.get("status") == "skipped":
        return "⚪️ пропущено"
    results = processing.get("results") or []
    if not results:
        return "🟡 нет результатов"
    statuses = [item.get("status") for item in results if isinstance(item, dict)]
    if not statuses:
        return "🟡 нет результатов"
    if all(status == "success" for status in statuses):
        return "🟢 успешно"
    if any(status == "error" for status in statuses):
        return "🔴 ошибка"
    if all(status == "skipped" for status in statuses):
        return "⚪️ пропущено"
    return "🟡 частично"


def _supplier_stock_transfer_status(transfer: dict | None) -> str:
    """Определить статус выгрузки."""
    if not transfer:
        return "⏭️ не запускалась"
    status = transfer.get("status")
    if status == "skipped":
        return "⚪️ пропущено"
    if status and status != "success":
        return "🔴 ошибка"
    items = transfer.get("items") or []
    ftp_items = transfer.get("ftp_ork", {}).get("items") or []
    statuses = [
        item.get("status") for item in list(items) + list(ftp_items) if isinstance(item, dict)
    ]
    if not statuses:
        return "🟡 нет файлов"
    if all(status == "success" for status in statuses):
        return "🟢 успешно"
    if any(status == "error" for status in statuses):
        return "🔴 ошибка"
    return "🟡 частично"


def _supplier_stock_stage_label(is_ok: bool) -> str:
    return "ОК" if is_ok else "не ОК"


def _supplier_stock_processing_ok(processing: dict | None) -> bool:
    if not processing:
        return False
    if processing.get("status") == "skipped":
        return False
    results = processing.get("results") or []
    statuses = [item.get("status") for item in results if isinstance(item, dict)]
    if not statuses:
        return False
    return all(status == "success" for status in statuses)


def _supplier_stock_transfer_ok(transfer: dict | None) -> bool:
    if not transfer:
        return False
    status = transfer.get("status")
    if status == "skipped":
        return False
    items = transfer.get("items") or []
    ftp_items = transfer.get("ftp_ork", {}).get("items") or []
    statuses = [
        item.get("status") for item in list(items) + list(ftp_items) if isinstance(item, dict)
    ]
    if not statuses:
        return False
    return status == "success" and all(item_status == "success" for item_status in statuses)


def _build_supplier_stock_daily_summary(
    reports: list[dict],
    source_kind: str,
) -> list[dict]:
    summary: list[dict] = []
    seen_sources: set[str] = set()
    for entry in reports:
        source_id = str(entry.get("source_id") or entry.get("source_name") or "unknown")
        if source_id in seen_sources:
            continue
        seen_sources.add(source_id)
        processing_info = entry.get("processing") if entry.get("status") == "success" else None
        receive_ok = entry.get("status") == "success"
        processing_ok = _supplier_stock_processing_ok(processing_info)
        transfer_ok = _supplier_stock_transfer_ok(
            processing_info.get("transfer") if processing_info else None
        )
        summary.append(
            {
                "entry": entry,
                "source_id": source_id,
                "source_name": entry.get("source_name") or source_id,
                "source_kind": source_kind,
                "receive_ok": receive_ok,
                "processing_ok": processing_ok,
                "transfer_ok": transfer_ok,
            }
        )
    return summary


def _supplier_stock_processing_mode_label(value: str | None) -> str:
    """Сформировать читаемую метку режима обработки."""
    mode = (value or "table").strip().lower()
    if mode == "iek_json":
        return "IEK JSON"
    return "Табличный"


def show_supplier_stock_reports(update, context, source_kind: str = "download") -> None:
    """Показать результаты загрузки, обработки и выгрузки остатков поставщиков."""
    query = update.callback_query
    query.answer()

    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        query.edit_message_text(
            "📦 Остатки поставщиков отключены в настройках.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 На главную", callback_data="main_menu")]]
            ),
        )
        return

    reporting_days = 1
    reports = get_supplier_stock_reports(
        limit=None, period_days=reporting_days, source_kind=source_kind
    )
    title = "полученные скачиванием" if source_kind == "download" else "полученные по почте"
    message_lines = [
        "📦 *Остатки поставщиков — результаты*",
        "",
        f"Группа: {title}",
        "Период: последние 24 часа",
        "",
    ]
    summary = _build_supplier_stock_daily_summary(reports, source_kind)
    if not summary:
        message_lines.append("⚪️ За сутки данных нет.")
    else:
        message_lines.append("Кликни источник, чтобы открыть историю за сутки.")
        for entry in summary:
            source_name = _escape_pattern_text(entry.get("source_name") or "неизвестный источник")
            receive_label = _supplier_stock_stage_label(entry["receive_ok"])
            processing_label = _supplier_stock_stage_label(entry["processing_ok"])
            transfer_label = _supplier_stock_stage_label(entry["transfer_ok"])
            message_lines.extend(
                [
                    "",
                    f"• *{source_name}*",
                    f"  📥 Загрузка: {receive_label}",
                    f"  🧩 Обработка: {processing_label}",
                    f"  📤 Выгрузка: {transfer_label}",
                ]
            )

    def _split_message(lines: list[str], max_length: int = 3500) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for line in lines:
            candidate_len = current_len + len(line) + (1 if current else 0)
            if current and candidate_len > max_length:
                chunks.append("\n".join(current))
                current = [line]
                current_len = len(line)
            else:
                current.append(line)
                current_len = candidate_len
        if current:
            chunks.append("\n".join(current))
        return chunks

    message_chunks = _split_message(message_lines)
    keyboard = [
        [
            InlineKeyboardButton("⬇️ Скачивание", callback_data="supplier_stock_reports_download"),
            InlineKeyboardButton("📧 Почта", callback_data="supplier_stock_reports_mail"),
        ],
    ]
    entry_map: dict[str, dict] = {}
    if summary:
        for index, item in enumerate(summary, start=1):
            entry_key = str(index)
            entry_map[entry_key] = item
            source_id = str(item.get("source_id") or "")
            source_name = str(item.get("source_name") or source_id)
            source_label = source_name[:24]
            row = [
                InlineKeyboardButton(
                    f"📊 {source_label}",
                    callback_data=f"supplier_stock_report_source_day|{source_kind}|{source_id}",
                )
            ]
            if not (
                item.get("receive_ok") and item.get("processing_ok") and item.get("transfer_ok")
            ):
                row.append(
                    InlineKeyboardButton(
                        "❗ Детали",
                        callback_data=f"supplier_stock_report_entry|{entry_key}",
                    )
                )
            keyboard.append(row)
        context.user_data["supplier_stock_report_entries"] = entry_map
        context.user_data["supplier_stock_report_entries_kind"] = source_kind
    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "🔄 Обновить", callback_data=f"supplier_stock_reports_{source_kind}"
                )
            ],
            [InlineKeyboardButton("🛠️ Настройки", callback_data="settings_ext_supplier_stock")],
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
        ]
    )

    query.edit_message_text(
        message_chunks[0] if message_chunks else "\n".join(message_lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    for chunk in message_chunks[1:]:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=chunk,
            parse_mode="Markdown",
        )


def show_supplier_stock_report_sources(update, context, source_kind: str = "download") -> None:
    """Показать список источников остатков с текущими статусами."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    reporting_days = config.get("reporting", {}).get("period_days", 7)
    grouped = summarize_supplier_stock_reports(period_days=reporting_days)
    sources = grouped.get(source_kind, [])
    group_label = "полученные скачиванием" if source_kind == "download" else "полученные по почте"

    message_lines = [
        "📦 *Остатки поставщиков — источники*",
        "",
        f"Группа: {group_label}",
        f"Период: {reporting_days} дн.",
        "",
    ]

    if not sources:
        message_lines.append("⚪️ Источников за период нет.")
    else:
        for entry in sources:
            source_name = (
                entry.get("source_name") or entry.get("source_id") or "неизвестный источник"
            )
            time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
            message_lines.extend(
                [
                    "",
                    f"• *{_escape_pattern_text(source_name)}* ({_escape_pattern_text(time_label)})",
                    f"  📥 Загрузка: {entry.get('receive', {}).get('icon', '⚪️')}",
                    f"  🧩 Обработка: {entry.get('processing', {}).get('icon', '⚪️')}",
                    f"  📤 Выгрузка: {entry.get('transfer', {}).get('icon', '⚪️')}",
                ]
            )

    keyboard = [
        [
            InlineKeyboardButton(
                "⬇️ Скачивание", callback_data="supplier_stock_reports_sources_download"
            ),
            InlineKeyboardButton("📧 Почта", callback_data="supplier_stock_reports_sources_mail"),
        ],
    ]
    if sources:
        row: list[InlineKeyboardButton] = []
        for entry in sources:
            source_id = str(entry.get("source_id") or entry.get("source_name") or "")
            if not source_id:
                continue
            row.append(
                InlineKeyboardButton(
                    f"📊 {source_id}",
                    callback_data=f"supplier_stock_report_source|{source_kind}|{source_id}",
                )
            )
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "↩️ Назад", callback_data=f"supplier_stock_reports_{source_kind}"
                )
            ],
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
        ]
    )

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def show_supplier_stock_report_source_stats(
    update,
    context,
    source_id: str,
    source_kind: str = "download",
    period_days: int | None = None,
) -> None:
    """Показать подробную статистику по источнику остатков."""
    query = update.callback_query
    query.answer()

    if not source_id:
        query.edit_message_text(
            "⚪️ Источник не выбран.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ Назад", callback_data=f"supplier_stock_reports_sources_{source_kind}"
                        )
                    ],
                ]
            ),
        )
        return

    if period_days is None:
        config = get_supplier_stock_config()
        reporting_days = config.get("reporting", {}).get("period_days", 7)
    else:
        reporting_days = period_days
    stats = build_supplier_stock_source_stats(source_id, source_kind, reporting_days)
    summary = stats.get("summary", {})
    entries = stats.get("entries", [])

    message_lines = [
        "📦 *Остатки поставщиков — статистика источника*",
        "",
        f"Источник: {_escape_pattern_text(source_id)}",
        f"Группа: {'полученные скачиванием' if source_kind == 'download' else 'полученные по почте'}",
        f"Период: {reporting_days} дн.",
        "",
        f"Всего запусков: {summary.get('total', 0)}",
        f"📥 Успешно: {summary.get('receive_success', 0)} | Ошибок: {summary.get('receive_error', 0)}",
        f"🧩 Успешно: {summary.get('processing_success', 0)} | Ошибок: {summary.get('processing_error', 0)}",
        f"📤 Успешно: {summary.get('transfer_success', 0)} | Ошибок: {summary.get('transfer_error', 0)}",
        "",
        "*Последние события:*",
    ]

    if not entries:
        message_lines.append("⚪️ Записей пока нет.")
    else:
        for entry in entries[:10]:
            time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
            message_lines.extend(
                [
                    "",
                    f"• {_escape_pattern_text(time_label)}",
                    f"  📥 {entry.get('receive', {}).get('icon', '⚪️')}",
                    f"  🧩 {entry.get('processing', {}).get('icon', '⚪️')}",
                    f"  📤 {entry.get('transfer', {}).get('icon', '⚪️')}",
                ]
            )
            if entry.get("error"):
                message_lines.append(f"  ❗ Ошибка: {_escape_pattern_text(entry.get('error'))}")

    keyboard = [
        [
            InlineKeyboardButton(
                "↩️ Назад", callback_data=f"supplier_stock_reports_sources_{source_kind}"
            )
        ],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
    ]

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def show_supplier_stock_report_entry_details(update, context, entry_key: str) -> None:
    """Показать детали последнего запуска по источнику."""
    query = update.callback_query
    query.answer()

    entry_map = context.user_data.get("supplier_stock_report_entries", {})
    source_kind = context.user_data.get("supplier_stock_report_entries_kind", "download")
    summary = entry_map.get(entry_key)
    if not summary:
        query.edit_message_text(
            "⚪️ Детали недоступны, обновите результаты.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ Назад", callback_data=f"supplier_stock_reports_{source_kind}"
                        )
                    ],
                ]
            ),
        )
        return

    entry = summary.get("entry", {})
    source_id = summary.get("source_id") or entry.get("source_id") or "неизвестно"
    source_name = entry.get("source_name") or source_id
    time_label = _format_supplier_stock_timestamp(entry.get("timestamp"))
    download_status = _supplier_stock_status_label(entry.get("status"))
    processing_info = entry.get("processing") if entry.get("status") == "success" else None
    processing_status = _supplier_stock_processing_status(processing_info)
    transfer_status = _supplier_stock_transfer_status(
        processing_info.get("transfer") if processing_info else None
    )
    if entry.get("status") != "success":
        processing_status = "⏭️ не запускалась"
        transfer_status = "⏭️ не запускалась"

    message_lines = [
        "📦 *Остатки поставщиков — подробности*",
        "",
        f"Источник: {_escape_pattern_text(source_name)}",
        f"Группа: {'полученные скачиванием' if source_kind == 'download' else 'полученные по почте'}",
        f"Запуск: {_escape_pattern_text(time_label)}",
        "",
        f"📥 Загрузка: {download_status}",
        f"🧩 Обработка: {processing_status}",
        f"📤 Выгрузка: {transfer_status}",
    ]
    if entry.get("error"):
        message_lines.append(f"\n❗ Ошибка: {_escape_pattern_text(entry.get('error'))}")

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 История источника",
                callback_data=f"supplier_stock_report_source_day|{source_kind}|{source_id}",
            )
        ],
        [InlineKeyboardButton("↩️ Назад", callback_data=f"supplier_stock_reports_{source_kind}")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
    ]

    query.edit_message_text(
        "\n".join(message_lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def show_supplier_stock_download_settings(update, context):
    """Показать настройки скачивания файлов остатков поставщиков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_edit", None)

    config = get_supplier_stock_config()
    download = config.get("download", {})
    temp_dir = download.get("temp_dir", "")
    sources = download.get("sources", [])
    schedule = download.get("schedule", {})
    unpack_enabled = sum(1 for source in sources if source.get("unpack_archive"))
    unpack_state = f"{unpack_enabled}/{len(sources)}" if sources else "нет"
    schedule_state = "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено"
    schedule_time = schedule.get("time", "не задано")
    archive_cleanup = _format_archive_cleanup_days(config.get("archive_cleanup_days"))

    message = (
        "📦 *Скачивание файлов остатков*\n\n"
        f"Временный каталог: `{temp_dir}`\n"
        f"Архив: `{download.get('archive_dir', '')}`\n"
        f"Очистка архива: {archive_cleanup}\n"
        f"Распаковка в источниках: {unpack_state}\n"
        f"Источников: {len(sources)}\n"
        f"Расписание: {schedule_state} ({schedule_time})\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("📁 Временный каталог", callback_data="supplier_stock_temp_dir")],
        [InlineKeyboardButton("🗄️ Каталог архива", callback_data="supplier_stock_archive_dir")],
        [
            InlineKeyboardButton(
                "🧹 Период очистки архива", callback_data="supplier_stock_archive_cleanup_download"
            )
        ],
        [InlineKeyboardButton("⏰ Расписание", callback_data="supplier_stock_schedule")],
        [InlineKeyboardButton("📦 Источники", callback_data="supplier_stock_sources")],
        [InlineKeyboardButton("📤 Ресурсы выгрузки", callback_data="supplier_stock_resources")],
        [InlineKeyboardButton("📡 FTP ОРК", callback_data="supplier_stock_ftp")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_supplier_stock"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_mail_settings(update, context):
    """Показать настройки получения остатков через почту."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_mail_edit", None)
    context.user_data.pop("supplier_stock_archive_cleanup_back", None)
    context.user_data.pop("supplier_stock_mail_add_source", None)
    context.user_data.pop("supplier_stock_mail_source_stage", None)
    context.user_data.pop("supplier_stock_mail_source_data", None)
    context.user_data.pop("supplier_stock_mail_edit_source", None)
    context.user_data.pop("supplier_stock_mail_edit_source_stage", None)
    context.user_data.pop("supplier_stock_mail_edit_source_id", None)

    config = get_supplier_stock_config()
    mail_settings = config.get("mail", {})
    sources = mail_settings.get("sources", [])
    status_text = "🟢 Включено" if mail_settings.get("enabled") else "🔴 Выключено"
    temp_dir = mail_settings.get("temp_dir") or ""
    archive_dir = mail_settings.get("archive_dir") or ""
    unpack_enabled = sum(1 for source in sources if source.get("unpack_archive"))
    unpack_state = f"{unpack_enabled}/{len(sources)}" if sources else "нет"
    archive_cleanup = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
    message = (
        "📧 *Почтовые сообщения (остатки)*\n\n"
        f"Статус: {status_text}\n"
        f"Временный каталог: `{_escape_pattern_text(temp_dir)}`\n"
        f"Архив: `{_escape_pattern_text(archive_dir)}`\n"
        f"Очистка архива: {archive_cleanup}\n"
        f"Распаковка в правилах: {unpack_state}\n"
        f"Правил: {len(sources)}\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [InlineKeyboardButton("🔁 Включить/выключить", callback_data="supplier_stock_mail_toggle")],
        [
            InlineKeyboardButton(
                "📁 Временный каталог", callback_data="supplier_stock_mail_temp_dir"
            )
        ],
        [InlineKeyboardButton("🗄️ Каталог архива", callback_data="supplier_stock_mail_archive_dir")],
        [
            InlineKeyboardButton(
                "🧹 Период очистки архива", callback_data="supplier_stock_archive_cleanup_mail"
            )
        ],
        [InlineKeyboardButton("📎 Правила вложений", callback_data="supplier_stock_mail_sources")],
        [InlineKeyboardButton("📤 Ресурсы выгрузки", callback_data="supplier_stock_resources")],
        [InlineKeyboardButton("📡 FTP ОРК", callback_data="supplier_stock_ftp")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_supplier_stock"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_resources_menu(update, context):
    """Показать список ресурсов выгрузки по умолчанию."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_resource_settings_id", None)
    context.user_data.pop("supplier_stock_resource_field", None)
    context.user_data.pop("supplier_stock_resource_field_id", None)
    context.user_data.pop("supplier_stock_resource_add", None)
    context.user_data.pop("supplier_stock_resource_stage", None)
    context.user_data.pop("supplier_stock_resource_data", None)

    config = get_supplier_stock_config()
    resources = config.get("resources", [])

    if not resources:
        message = "📤 *Ресурсы выгрузки*\n\n❌ Ресурсы не настроены."
    else:
        message_lines = ["📤 *Ресурсы выгрузки*\n"]
        for index, resource in enumerate(resources, start=1):
            name = _escape_pattern_text(
                resource.get("name") or resource.get("id") or f"Ресурс {index}"
            )
            unc_path = _escape_pattern_text(resource.get("unc_path") or "не задано")
            login = _escape_pattern_text(resource.get("login") or "не задано")
            enabled = resource.get("enabled", True)
            status_icon = "🟢" if enabled else "🔴"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   • UNC: `{unc_path}`\n"
                    f"   • Логин: `{login}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить ресурс", callback_data="supplier_stock_resource_add")],
    ]

    for resource in resources:
        resource_id = resource.get("id") or ""
        if not resource_id:
            continue
        enabled = resource.get("enabled", True)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"⚙️ {resource.get('name', resource_id)}",
                    callback_data=f"supplier_stock_resource_settings|{resource_id}",
                ),
                InlineKeyboardButton(
                    toggle_text, callback_data=f"supplier_stock_resource_toggle_{resource_id}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🗑️", callback_data=f"supplier_stock_resource_delete_{resource_id}"
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_supplier_stock"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_resource_settings(update, context, resource_id: str) -> None:
    """Показать настройки конкретного ресурса выгрузки."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_resource_settings_id"] = resource_id
    context.user_data.pop("supplier_stock_resource_field", None)
    context.user_data.pop("supplier_stock_resource_field_id", None)

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        query.edit_message_text(
            "❌ Ресурс не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_resources")]]
            ),
        )
        return

    name = _escape_pattern_text(resource.get("name") or resource_id)
    unc_path = _escape_pattern_text(resource.get("unc_path") or "не задано")
    login = _escape_pattern_text(resource.get("login") or "не задано")
    password = "задано" if resource.get("password") else "не задано"
    status_icon = "🟢" if resource.get("enabled", True) else "🔴"

    message = (
        "⚙️ *Ресурс выгрузки*\n\n"
        f"{status_icon} *{name}*\n"
        f"• UNC путь: `{unc_path}`\n"
        f"• Логин: `{login}`\n"
        f"• Пароль: `{password}`\n\n"
        "Выберите настройку:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ Название", callback_data=f"supplier_stock_resource_field|{resource_id}|name"
            ),
            InlineKeyboardButton(
                "📂 UNC путь", callback_data=f"supplier_stock_resource_field|{resource_id}|unc_path"
            ),
        ],
        [
            InlineKeyboardButton(
                "👤 Логин", callback_data=f"supplier_stock_resource_field|{resource_id}|login"
            ),
            InlineKeyboardButton(
                "🔐 Пароль", callback_data=f"supplier_stock_resource_field|{resource_id}|password"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔁 Включить/выключить",
                callback_data=f"supplier_stock_resource_toggle_{resource_id}",
            )
        ],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_resources"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_ftp_settings(update, context) -> None:
    """Показать настройки FTP ОРК."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_ftp_field", None)

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})
    host = _escape_pattern_text(ftp_settings.get("host") or "не задано")
    login = _escape_pattern_text(ftp_settings.get("login") or "не задано")
    password = "задано" if ftp_settings.get("password") else "не задано"

    message = (
        "📡 *FTP ОРК*\n\n"
        f"HOST FTP: `{host}`\n"
        f"Логин FTP: `{login}`\n"
        f"Пароль FTP: `{password}`\n\n"
        "Выберите параметр:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🌐 HOST FTP", callback_data="supplier_stock_ftp_field|host"),
            InlineKeyboardButton("👤 Логин FTP", callback_data="supplier_stock_ftp_field|login"),
        ],
        [InlineKeyboardButton("🔐 Пароль FTP", callback_data="supplier_stock_ftp_field|password")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_supplier_stock"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_processing_menu(
    update,
    context,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
    action_prefix: str = "supplier_stock_processing",
    title: str = "🧩 *Обработка файлов остатков*",
):
    """Показать настройки обработки полученных файлов остатков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_processing_add", None)
    context.user_data.pop("supplier_stock_processing_stage", None)
    context.user_data.pop("supplier_stock_processing_data", None)
    context.user_data.pop("supplier_stock_processing_edit", None)
    context.user_data.pop("supplier_stock_processing_edit_id", None)
    context.user_data.pop("supplier_stock_processing_variant_index", None)
    context.user_data.pop("supplier_stock_processing_data_columns_expected", None)
    context.user_data.pop("supplier_stock_processing_data_columns", None)
    context.user_data.pop("supplier_stock_processing_output_names_expected", None)
    context.user_data.pop("supplier_stock_processing_output_names", None)
    context.user_data.pop("supplier_stock_processing_rule_dirty", None)
    context.user_data["supplier_stock_processing_source_id"] = source_id
    context.user_data["supplier_stock_processing_source_kind"] = source_kind
    context.user_data["supplier_stock_processing_back"] = back_callback
    context.user_data["supplier_stock_processing_action_prefix"] = action_prefix
    context.user_data["supplier_stock_processing_title"] = title

    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    if source_id is not None:
        rules = [
            rule
            for rule in rules
            if _processing_rule_matches_source(rule, source_id, source_kind, config)
        ]

    if not rules:
        message = f"{title}\n\n❌ Правила обработки не настроены."
    else:
        message_lines = [f"{title}\n"]
        for index, rule in enumerate(rules, start=1):
            name = _escape_pattern_text(rule.get("name") or rule.get("id") or f"Правило {index}")
            source_file = _escape_pattern_text(rule.get("source_file") or "не задано")
            enabled = rule.get("enabled", True)
            active = rule.get("active", False)
            status_icon = "🟢" if enabled else "🔴"
            processing_text = (
                "обработка" if rule.get("requires_processing", True) else "без обработки"
            )
            active_text = "да" if active else "нет"
            message_lines.append(
                (
                    f"{index}. {status_icon}{'⭐' if active else ''} *{name}*\n"
                    f"   • Файл источника: `{source_file}`\n"
                    f"   • Режим: `{processing_text}`\n"
                    f"   • Активно: `{active_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить правило", callback_data=f"{action_prefix}|add")],
    ]

    for rule in rules:
        rule_id = rule.get("id") or ""
        if not rule_id:
            continue
        enabled = rule.get("enabled", True)
        active = rule.get("active", False)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        active_text = "⛔️ Отключить активность" if active else "⭐ Включить активность"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {rule.get('name', rule_id)}",
                    callback_data=f"{action_prefix}|edit|{rule_id}",
                ),
                InlineKeyboardButton(
                    f"{toggle_text}", callback_data=f"{action_prefix}|toggle|{rule_id}"
                ),
                InlineKeyboardButton("🗑️", callback_data=f"{action_prefix}|delete|{rule_id}"),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    active_text, callback_data=f"{action_prefix}|activate|{rule_id}"
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _set_supplier_stock_processing_active_rule(
    rules: list[dict],
    rule_id: str,
    source_id: str | None = None,
    source_kind: str | None = None,
) -> None:
    config = get_supplier_stock_config()
    for rule in rules:
        if source_id is not None and str(rule.get("source_id")) != str(source_id):
            continue
        if source_kind and not _processing_rule_matches_source(
            rule, source_id, source_kind, config
        ):
            continue
        if str(rule.get("id")) == str(rule_id):
            rule["active"] = not rule.get("active", False)
            if rule["active"]:
                rule["enabled"] = True


def _find_supplier_source(sources: list[dict], source_id: str) -> dict | None:
    return next((item for item in sources if str(item.get("id")) == str(source_id)), None)


def show_supplier_stock_processing_rule_menu(update, context) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    _fill_processing_rule_from_source(data)
    context.user_data["supplier_stock_processing_rule_data"] = data
    requires_processing = data.get("requires_processing", True)
    variants = data.get("variants", [])
    variants_count = len(variants)
    if requires_processing and not variants_count:
        _sync_processing_variants_count(data, 1)
        data["variants_count"] = 1
        variants = data.get("variants", [])
        variants_count = len(variants)
    variant_index = 0 if variants_count else None
    message = _processing_rule_summary(data)

    toggle_text = "✅ Требуется обработка" if requires_processing else "⛔️ Обработка не требуется"

    keyboard = [
        [InlineKeyboardButton("— Настройки правила —", callback_data="supplier_stock_noop")]
    ]
    if not data.get("source_id"):
        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        "✏️ Название", callback_data="supplier_stock_processing_rule|field|name"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📄 Файл источника",
                        callback_data="supplier_stock_processing_rule|field|source_file",
                    )
                ],
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                toggle_text, callback_data="supplier_stock_processing_rule|toggle_processing"
            )
        ]
    )

    if requires_processing:
        variant = _ensure_processing_variant(data, variant_index or 0)
        orc = variant.get("orc", {})
        orc_enabled = orc.get("enabled", False)
        orc_text = "да" if orc_enabled else "нет"
        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        "📍 Первая строка с данными",
                        callback_data="supplier_stock_processing_rule|field|data_row",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔎 Номер колонки с артикулом",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_col",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🧪 Условия отбора артикулов",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_filter",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🧪 Условия отбора по еще одной колонке",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|extra_filter",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏷️ Префикс в артикуле",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_prefix",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏷️ Постфикс артикула",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_postfix",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🧹 Изменение входящего артикула",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_transform",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Колонки с данными",
                        callback_data=f"supplier_stock_processing_columns|menu|{variant_index}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🧾 Формат файла на выходе",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|output_format",
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"📦 Файл для ОРК: {orc_text}",
                        callback_data=f"supplier_stock_processing_variant|toggle_orc|{variant_index}",
                    )
                ],
            ]
        )
        if orc_enabled:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⚙️ Настройки файла ОРК",
                        callback_data=f"supplier_stock_processing_orc|menu|{variant_index}",
                    )
                ]
            )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📄 Имя файла на выходе",
                    callback_data="supplier_stock_processing_rule|field|output_name",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_processing_rule|back"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_processing_variant_menu(update, context, variant_index: int) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    variant = _ensure_processing_variant(data, variant_index)
    context.user_data["supplier_stock_processing_rule_data"] = data

    article_col = variant.get("article_col") or "не задано"
    article_filter = _escape_pattern_text(variant.get("article_filter") or "не задано")
    extra_filter_col = variant.get("extra_filter_col")
    extra_filter = variant.get("extra_filter")
    if extra_filter_col and extra_filter:
        extra_filter_text = f"№{extra_filter_col}: {_escape_pattern_text(extra_filter)}"
    else:
        extra_filter_text = "не задано"
    article_prefix = _escape_pattern_text(variant.get("article_prefix") or "не задано")
    article_postfix = _escape_pattern_text(variant.get("article_postfix") or "не задано")
    article_transform = variant.get("article_transform") or {}
    transform_pattern = article_transform.get("pattern") or ""
    transform_replacement = article_transform.get("replacement") or ""
    if transform_pattern:
        transform_text = f"{_escape_pattern_text(transform_pattern)} => {_escape_pattern_text(transform_replacement)}"
    else:
        transform_text = "не задано"
    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    output_format = variant.get("output_format") or "не задано"
    orc = variant.get("orc", {})
    orc_enabled = orc.get("enabled", False)
    orc_text = "да" if orc_enabled else "нет"
    orc_column = orc.get("column") or "не задано"
    orc_input_index = orc.get("input_index")
    orc_output_index = orc.get("output_index")
    orc_output_format = orc.get("output_format")
    orc_output_name = _escape_pattern_text(orc.get("output_name") or "")
    if orc_output_format:
        orc_output_text = orc_output_format
    elif output_format != "не задано":
        orc_output_text = f"как основной ({output_format})"
    else:
        orc_output_text = "не задано"

    message = (
        "📦 *Настройка файла обработки*\n\n"
        f"• Номер колонки с артикулом: `{article_col}`\n"
        f"• Условия отбора артикулов: `{article_filter}`\n"
        f"• Условия отбора по доп. колонке: `{extra_filter_text}`\n"
        f"• Префикс артикула: `{article_prefix}`\n"
        f"• Постфикс артикула: `{article_postfix}`\n"
        f"• Изменение входящего артикула: `{transform_text}`\n"
        f"• Колонки с данными: `{data_columns_count or 'не задано'}`\n"
        f"• Формат файла на выходе: `{output_format}`\n"
        f"• Файл для ОРК: `{orc_text}`"
    )
    if orc_enabled:
        message += (
            f"\n• Колонка данных для ОРК: `{orc_column}`"
            f"\n• Формат файла ОРК на выходе: `{_escape_pattern_text(orc_output_text)}`"
            f"\n• Имя выходного файла ОРК: `{orc_output_name or 'по умолчанию (_orc)'}`"
        )
        if orc_input_index:
            message += f"\n• Файл источника (вход): `№{orc_input_index}`"
        if orc_output_index:
            output_label = f"№{orc_output_index}"
            if data_columns_count and orc_output_index <= data_columns_count:
                names = variant.get("output_names", [])
                name_value = (
                    names[orc_output_index - 1] if orc_output_index - 1 < len(names) else ""
                )
                if name_value:
                    output_label = f"{orc_output_index}. {_escape_pattern_text(name_value)}"
            message += f"\n• Файл источника (выход): `{output_label}`"

    keyboard = [
        [InlineKeyboardButton("— Настройки файла —", callback_data="supplier_stock_noop")],
        [
            InlineKeyboardButton(
                "🔎 Номер колонки с артикулом",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_col",
            )
        ],
        [
            InlineKeyboardButton(
                "🧪 Условия отбора артикулов",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_filter",
            )
        ],
        [
            InlineKeyboardButton(
                "🧪 Условия отбора по еще одной колонке",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|extra_filter",
            )
        ],
        [
            InlineKeyboardButton(
                "🏷️ Префикс в артикуле",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_prefix",
            )
        ],
        [
            InlineKeyboardButton(
                "🏷️ Постфикс артикула",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_postfix",
            )
        ],
        [
            InlineKeyboardButton(
                "🧹 Изменение входящего артикула",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|article_transform",
            )
        ],
    ]

    keyboard.append(
        [InlineKeyboardButton("— Колонки с данными —", callback_data="supplier_stock_noop")]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ Добавить колонку",
                callback_data=f"supplier_stock_processing_variant|add_column|{variant_index}",
            )
        ]
    )

    if data_columns_count:
        for idx in range(data_columns_count):
            label = variant.get("data_columns", [])
            value = label[idx] if idx < len(label) else "не задано"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📈 Колонка {idx + 1}: {value or 'не задано'}",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|data_column|{idx}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("— Имена файлов —", callback_data="supplier_stock_noop")]
        )
        for idx in range(data_columns_count):
            names = variant.get("output_names", [])
            name_value = names[idx] if idx < len(names) else "не задано"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📄 Имя файла {idx + 1}: {name_value or 'не задано'}",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|output_name|{idx}",
                    )
                ]
            )

    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "🧾 Формат файла на выходе",
                    callback_data=f"supplier_stock_processing_variant|field|{variant_index}|output_format",
                )
            ],
            [
                InlineKeyboardButton(
                    f"📦 Файл для ОРК: {orc_text}",
                    callback_data=f"supplier_stock_processing_variant|toggle_orc|{variant_index}",
                )
            ],
        ]
    )

    if orc_enabled:
        keyboard.extend(
            [
                [InlineKeyboardButton("— Файл для ОРК —", callback_data="supplier_stock_noop")],
                [
                    InlineKeyboardButton(
                        "🏷️ Префикс в артикуле",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_prefix",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📦 Stor",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_stor",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📈 Колонка с данными",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_column",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🧾 Формат файла ОРК на выходе",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_output_format",
                    )
                ],
            ]
        )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_processing_rule|menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_processing_columns_menu(update, context, variant_index: int) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    variant = _ensure_processing_variant(data, variant_index)
    context.user_data["supplier_stock_processing_rule_data"] = data

    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    columns = variant.get("data_columns", [])
    names = variant.get("output_names", [])
    column_filters = variant.get("use_article_filter_columns", [])

    use_article_filter = variant.get("use_article_filter")
    if use_article_filter is None:
        use_article_filter = bool(variant.get("article_filter"))
    filter_text = "да" if use_article_filter else "нет"
    message_lines = [
        "📊 *Колонки с данными*\n",
        f"Количество колонок: `{data_columns_count or 0}`",
        f"Использовать условия отбора артикулов: `{filter_text}`",
    ]
    for idx in range(data_columns_count or 0):
        col_value = columns[idx] if idx < len(columns) else "не задано"
        name_value = names[idx] if idx < len(names) else "не задано"
        filter_enabled = column_filters[idx] if idx < len(column_filters) else True
        filter_text_line = "да" if filter_enabled else "нет"
        message_lines.append(
            f"{idx + 1}. Колонка: `{col_value or 'не задано'}` → файл: `{_escape_pattern_text(name_value)}`"
            f" (фильтр: `{filter_text_line}`)"
        )
    message = "\n".join(message_lines)

    toggle_text = (
        "✅ Использовать условия отбора артикулов"
        if use_article_filter
        else "⛔️ Не использовать условия отбора артикулов"
    )
    keyboard = [
        [InlineKeyboardButton("— Колонки с данными —", callback_data="supplier_stock_noop")],
        [
            InlineKeyboardButton(
                toggle_text,
                callback_data=f"supplier_stock_processing_columns|toggle_article_filter|{variant_index}",
            )
        ],
        [
            InlineKeyboardButton(
                "➕ Добавить колонку",
                callback_data=f"supplier_stock_processing_columns|add_column|{variant_index}",
            )
        ],
    ]

    if data_columns_count:
        for idx in range(data_columns_count):
            value = columns[idx] if idx < len(columns) else "не задано"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📈 Колонка {idx + 1}: {value or 'не задано'}",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|data_column|{idx}",
                    ),
                    InlineKeyboardButton(
                        "🗑️",
                        callback_data=f"supplier_stock_processing_columns|remove_column|{variant_index}|{idx}",
                    ),
                ]
            )
            filter_enabled = column_filters[idx] if idx < len(column_filters) else True
            filter_toggle_text = (
                f"✅ Фильтр артикулов {idx + 1}"
                if filter_enabled
                else f"⛔️ Фильтр артикулов {idx + 1}"
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        filter_toggle_text,
                        callback_data=f"supplier_stock_processing_columns|tac|{variant_index}|{idx}",
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("— Имена файлов —", callback_data="supplier_stock_noop")]
        )
        for idx in range(data_columns_count):
            name_value = names[idx] if idx < len(names) else "не задано"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📄 Имя файла {idx + 1}: {name_value or 'не задано'}",
                        callback_data=f"supplier_stock_processing_variant|field|{variant_index}|output_name|{idx}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_processing_rule|menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_processing_orc_menu(update, context, variant_index: int) -> None:
    query = update.callback_query
    query.answer()

    data = context.user_data.get("supplier_stock_processing_rule_data", {})
    variant = _ensure_processing_variant(data, variant_index)
    context.user_data["supplier_stock_processing_rule_data"] = data

    orc = variant.get("orc", {})
    orc_prefix = _escape_pattern_text(orc.get("prefix") or "не задано")
    orc_stor = _escape_pattern_text(orc.get("stor") or "не задано")
    orc_column = orc.get("column") or "не задано"
    orc_input_index = orc.get("input_index")
    orc_output_index = orc.get("output_index")
    base_output_format = variant.get("output_format")
    orc_output_format = orc.get("output_format")
    orc_output_name = _escape_pattern_text(orc.get("output_name") or "")
    if orc_output_format:
        orc_output_text = orc_output_format
    elif base_output_format:
        orc_output_text = f"как основной ({base_output_format})"
    else:
        orc_output_text = "не задано"

    config = get_supplier_stock_config()
    source_kind, source = _resolve_processing_rule_source(data, config)
    input_count = 0
    if source_kind == "mail" and source:
        input_count = int(source.get("expected_attachments") or 1)

    data_columns_count = variant.get("data_columns_count") or max(
        len(variant.get("data_columns", [])),
        len(variant.get("output_names", [])),
    )
    if data_columns_count:
        _sync_variant_columns(variant, data_columns_count)
    output_names = variant.get("output_names", [])

    message_lines = [
        "📦 *Файл для ОРК*\n",
        f"• Префикс в артикуле: `{orc_prefix}`",
        f"• Stor: `{orc_stor}`",
        f"• Колонка с данными: `{orc_column}`",
        f"• Формат файла ОРК на выходе: `{_escape_pattern_text(orc_output_text)}`",
        f"• Имя выходного файла ОРК: `{orc_output_name or 'по умолчанию (_orc)'}`",
    ]
    if input_count > 1:
        input_label = f"№{orc_input_index}" if orc_input_index else "не задано"
        message_lines.append(f"• Файл источника (вход): `{input_label}`")
    if data_columns_count > 1:
        output_label = "не задано"
        if orc_output_index:
            output_label = f"№{orc_output_index}"
            if orc_output_index <= data_columns_count:
                name_value = (
                    output_names[orc_output_index - 1]
                    if orc_output_index - 1 < len(output_names)
                    else ""
                )
                if name_value:
                    output_label = f"{orc_output_index}. {_escape_pattern_text(name_value)}"
        message_lines.append(f"• Файл источника (выход): `{output_label}`")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("— Файл для ОРК —", callback_data="supplier_stock_noop")],
        [
            InlineKeyboardButton(
                "🏷️ Префикс в артикуле",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_prefix",
            )
        ],
        [
            InlineKeyboardButton(
                "📦 Stor",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_stor",
            )
        ],
        [
            InlineKeyboardButton(
                "📈 Колонка с данными",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_column",
            )
        ],
        [
            InlineKeyboardButton(
                "📄 Имя выходного файла ОРК",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_output_name",
            )
        ],
        [
            InlineKeyboardButton(
                "🧾 Формат файла ОРК на выходе",
                callback_data=f"supplier_stock_processing_variant|field|{variant_index}|orc_output_format",
            )
        ],
    ]

    if input_count > 1:
        keyboard.append(
            [InlineKeyboardButton("— Файл источника (вход) —", callback_data="supplier_stock_noop")]
        )
        for idx in range(1, input_count + 1):
            selected = "✅" if orc_input_index == idx else "📥"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{selected} Вход {idx}",
                        callback_data=f"supplier_stock_processing_orc|set_input|{variant_index}|{idx}",
                    )
                ]
            )
        if orc_input_index:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🚫 Сбросить выбор входа",
                        callback_data=f"supplier_stock_processing_orc|clear_input|{variant_index}",
                    )
                ]
            )

    if data_columns_count > 1:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "— Файл источника (выход) —", callback_data="supplier_stock_noop"
                )
            ]
        )
        for idx in range(1, data_columns_count + 1):
            name_value = output_names[idx - 1] if idx - 1 < len(output_names) else ""
            label = f"Выход {idx}"
            if name_value:
                label = f"{idx}. {name_value}"
            selected = "✅" if orc_output_index == idx else "📤"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{selected} {label}",
                        callback_data=f"supplier_stock_processing_orc|set_output|{variant_index}|{idx}",
                    )
                ]
            )
        if orc_output_index:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🚫 Сбросить выбор выхода",
                        callback_data=f"supplier_stock_processing_orc|clear_output|{variant_index}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_processing_rule|menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def supplier_stock_start_processing_rule_menu(
    update,
    context,
    rule_id: str | None = None,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_processing_stage", None)
    context.user_data.pop("supplier_stock_processing_data", None)
    context.user_data.pop("supplier_stock_processing_add", None)
    context.user_data.pop("supplier_stock_processing_edit", None)

    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    rule = None
    if rule_id:
        rule = next((item for item in rules if str(item.get("id")) == rule_id), None)
        if not rule:
            query.edit_message_text(
                "❌ Правило не найдено.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
                ),
            )
            return
        context.user_data["supplier_stock_processing_rule_edit_id"] = rule_id
        context.user_data["supplier_stock_processing_rule_add"] = False
        data = dict(rule)
    else:
        context.user_data["supplier_stock_processing_rule_edit_id"] = None
        context.user_data["supplier_stock_processing_rule_add"] = True
        data = {
            "name": "",
            "source_file": "",
            "output_name": "",
            "enabled": True,
            "requires_processing": True,
            "variants_count": 0,
            "variants": [],
        }
    if source_id:
        data["source_id"] = source_id
        context.user_data["supplier_stock_processing_source_id"] = source_id
    if source_kind:
        data["source_kind"] = source_kind
        context.user_data["supplier_stock_processing_source_kind"] = source_kind
    _fill_processing_rule_from_source(data)
    context.user_data["supplier_stock_processing_rule_data"] = data
    context.user_data["supplier_stock_processing_back"] = back_callback
    context.user_data["supplier_stock_processing_rule_dirty"] = False
    show_supplier_stock_processing_rule_menu(update, context)


def supplier_stock_start_processing_field_edit(
    update,
    context,
    field: str,
    variant_index: int | None = None,
    item_index: int | None = None,
) -> None:
    query = update.callback_query
    query.answer()

    rule_data = context.user_data.get("supplier_stock_processing_rule_data", {})
    if rule_data.get("source_id") and field in ("name", "source_file"):
        query.edit_message_text(
            "ℹ️ Название и файл источника берутся из настроек источника.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ Назад", callback_data="supplier_stock_processing_rule|menu"
                        )
                    ]
                ]
            ),
        )
        return

    context.user_data["supplier_stock_processing_field"] = field
    context.user_data["supplier_stock_processing_variant_index"] = variant_index
    context.user_data["supplier_stock_processing_item_index"] = item_index

    prompts = {
        "name": "Введите название правила:",
        "source_file": "Введите имя файла источника:",
        "data_row": "Введите номер первой строки с данными:",
        "output_name": "Введите имя файла на выходе (можно использовать {index}, {name}, {filename}):",
        "article_col": "Введите номер колонки с артикулом:",
        "article_filter": (
            "Введите условия отбора артикулов (regex) или '-' для всех.\n\n"
            "Примеры:\n"
            "• $1 ~ /^[0-9]/ && $col+0 > 0\n"
            "• $1 ~ /^[A-Z].*/ && $4 ~ /^[0-9]+$/\n"
            "• grep -E '^DKS [0-9A-Z]{6,},'\n"
            '• gsub(/^\\./, "", art); gsub(/[A-Za-z]+$/, "", art);\n'
            '• ($3+0 > 0) && ($4 == "Москва")'
        ),
        "extra_filter": (
            "Введите номер колонки и условие отбора (regex) через ';'.\n"
            "Пример: 4;^Москва$\n"
            "Или '-' чтобы отключить дополнительный фильтр."
        ),
        "article_prefix": (
            "Введите префикс артикула (или '-' если не нужен). "
            "Если нужен пробел в конце, можно указать \\s:"
        ),
        "article_postfix": "Введите постфикс артикула (или '-' если не нужен). Пробелы в конце сохраняются:",
        "article_transform": (
            "Введите правило изменения артикула (regex) или '-' чтобы отключить.\n\n"
            "Формат: паттерн => замена (замена может быть пустой).\n"
            "Примеры:\n"
            "• ^0+ =>\n"
            "• [^0-9A-Za-z]+ =>\n"
            "• \\s+ => -"
        ),
        "data_column": "Введите номер колонки с данными:",
        "output_format": "Введите формат выходного файла (xls, xlsx, csv):",
        "orc_prefix": "Введите префикс артикула для файла ОРК (или '-' если не нужен):",
        "orc_stor": "Введите параметр Stor для файла ОРК:",
        "orc_column": "Введите номер колонки с данными для файла ОРК:",
        "orc_output_name": (
            "Введите имя выходного файла ОРК "
            "(можно использовать {index}, {name}, {filename}) "
            "или '-' чтобы использовать добавление _orc:"
        ),
        "orc_output_format": (
            "Введите формат файла ОРК на выходе (xls, xlsx, csv) "
            "или '-' чтобы использовать формат основного файла:"
        ),
    }
    prompt = prompts.get(field, "Введите значение:")
    if field == "output_name" and variant_index is not None:
        prompt = "Введите имя выходного файла (можно использовать {index}, {name}, {filename}):"

    current_value = None
    if variant_index is not None:
        variant = _ensure_processing_variant(rule_data, variant_index)
        if field == "article_col":
            current_value = variant.get("article_col")
        elif field == "article_filter":
            current_value = variant.get("article_filter")
        elif field == "extra_filter":
            extra_filter_col = variant.get("extra_filter_col")
            extra_filter = variant.get("extra_filter")
            if extra_filter_col and extra_filter:
                current_value = f"{extra_filter_col}; {extra_filter}"
            else:
                current_value = None
        elif field == "article_prefix":
            current_value = variant.get("article_prefix")
        elif field == "article_postfix":
            current_value = variant.get("article_postfix")
        elif field == "article_transform":
            article_transform = variant.get("article_transform") or {}
            pattern = article_transform.get("pattern") or ""
            replacement = article_transform.get("replacement") or ""
            if pattern:
                current_value = f"{pattern} => {replacement}"
            else:
                current_value = None
        elif field == "data_column":
            columns = variant.get("data_columns", [])
            if item_index is not None and item_index < len(columns):
                current_value = columns[item_index]
        elif field == "output_name":
            names = variant.get("output_names", [])
            if item_index is not None and item_index < len(names):
                current_value = names[item_index]
        elif field == "output_format":
            current_value = variant.get("output_format")
        elif field in (
            "orc_prefix",
            "orc_stor",
            "orc_column",
            "orc_output_name",
            "orc_output_format",
        ):
            orc = variant.get("orc", {})
            if field == "orc_prefix":
                current_value = orc.get("prefix")
            elif field == "orc_stor":
                current_value = orc.get("stor")
            elif field == "orc_column":
                current_value = orc.get("column")
            elif field == "orc_output_name":
                current_value = orc.get("output_name")
            elif field == "orc_output_format":
                if orc.get("output_format"):
                    current_value = orc.get("output_format")
                elif variant.get("output_format"):
                    current_value = f"как основной ({variant.get('output_format')})"
    else:
        if field == "name":
            current_value = rule_data.get("name")
        elif field == "source_file":
            current_value = rule_data.get("source_file")
        elif field == "data_row":
            current_value = rule_data.get("data_row")
        elif field == "output_name":
            current_value = rule_data.get("output_name")

    current_hint = _format_current_hint(current_value)
    back_callback = "supplier_stock_processing_rule|menu"
    if variant_index is not None:
        back_callback = f"supplier_stock_processing_variant|menu|{variant_index}"
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: {current_hint}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
        ),
    )


def supplier_stock_save_processing_rule(update, context) -> None:
    query = update.callback_query
    query.answer()

    if not _save_processing_rule_data(update, context):
        return
    context.user_data["supplier_stock_processing_rule_dirty"] = False
    back_callback = context.user_data.get(
        "supplier_stock_processing_back", "supplier_stock_processing"
    )
    query.edit_message_text(
        "✅ Настройки сохранены.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
        ),
    )


def show_supplier_stock_mail_sources_menu(update, context):
    """Показать список правил вложений для почты."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_mail_source_settings_id", None)
    context.user_data.pop("supplier_stock_mail_add_source", None)
    context.user_data.pop("supplier_stock_mail_source_stage", None)
    context.user_data.pop("supplier_stock_mail_source_data", None)
    context.user_data.pop("supplier_stock_mail_edit_source", None)
    context.user_data.pop("supplier_stock_mail_edit_source_stage", None)
    context.user_data.pop("supplier_stock_mail_edit_source_id", None)

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])

    if not sources:
        message = "📎 *Правила вложений*\n\n❌ Правила не настроены."
    else:
        message_lines = ["📎 *Правила вложений*\n"]
        for index, source in enumerate(sources, start=1):
            name = _escape_pattern_text(
                source.get("name") or source.get("id") or f"Правило {index}"
            )
            sender = _escape_pattern_text(source.get("sender_pattern") or "любой")
            subject = _escape_pattern_text(source.get("subject_pattern") or "любой")
            mime_pattern = _escape_pattern_text(source.get("mime_pattern") or "application/.*")
            filename_pattern = _escape_pattern_text(source.get("filename_pattern") or "любой")
            expected = source.get("expected_attachments", 1)
            output_template = _escape_pattern_text(source.get("output_template") or "не задано")
            enabled = source.get("enabled", True)
            unpack_enabled = source.get("unpack_archive", False)
            status_icon = "🟢" if enabled else "🔴"
            unpack_text = "да" if unpack_enabled else "нет"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   • Отправитель: `{sender}`\n"
                    f"   • Тема: `{subject}`\n"
                    f"   • MIME: `{mime_pattern}`\n"
                    f"   • Имя файла: `{filename_pattern}`\n"
                    f"   • Ожидается: `{expected}`\n"
                    f"   • Шаблон: `{output_template}`\n"
                    f"   • Распаковка: `{unpack_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Добавить правило", callback_data="supplier_stock_mail_source_add"
            )
        ],
    ]

    for source in sources:
        source_id = source.get("id") or ""
        if not source_id:
            continue
        enabled = source.get("enabled", True)
        unpack_enabled = source.get("unpack_archive", False)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        unpack_text = "📦 Распаковка: вкл" if unpack_enabled else "📦 Распаковка: выкл"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"⚙️ {source.get('name', source_id)}",
                    callback_data=f"supplier_stock_mail_source_settings|{source_id}",
                ),
                InlineKeyboardButton(
                    f"{toggle_text}", callback_data=f"supplier_stock_mail_source_toggle_{source_id}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    unpack_text,
                    callback_data=f"supplier_stock_mail_source_unpack_toggle_{source_id}",
                ),
                InlineKeyboardButton(
                    "🗑️", callback_data=f"supplier_stock_mail_source_delete_{source_id}"
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_schedule_menu(update, context):
    """Показать меню расписания загрузки остатков поставщиков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_edit", None)

    config = get_supplier_stock_config()
    schedule = config.get("download", {}).get("schedule", {})
    schedule_state = "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено"
    schedule_time = schedule.get("time", "не задано")

    message = (
        "⏰ *Расписание загрузки остатков*\n\n"
        f"Статус: {schedule_state}\n"
        f"Время: {schedule_time}\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔁 Включить/выключить", callback_data="supplier_stock_schedule_toggle"
            )
        ],
        [InlineKeyboardButton("🕒 Изменить время", callback_data="supplier_stock_schedule_time")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_download"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_sources_menu(update, context):
    """Показать список источников файлов остатков."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_source_settings_id", None)
    context.user_data.pop("supplier_stock_add_source", None)
    context.user_data.pop("supplier_stock_source_stage", None)
    context.user_data.pop("supplier_stock_source_data", None)
    context.user_data.pop("supplier_stock_edit_source", None)
    context.user_data.pop("supplier_stock_edit_source_stage", None)
    context.user_data.pop("supplier_stock_edit_source_id", None)

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])

    if not sources:
        message = "📦 *Источники файлов остатков*\n\n❌ Источники не настроены."
    else:
        message_lines = ["📦 *Источники файлов остатков*\n"]
        for index, source in enumerate(sources, start=1):
            name = _escape_pattern_text(
                source.get("name") or source.get("id") or f"Источник {index}"
            )
            url = _escape_pattern_text(source.get("url") or "URL не задан")
            output_name = _escape_pattern_text(source.get("output_name") or "не задано")
            method = _escape_pattern_text(source.get("method") or "http")
            processing_mode = _escape_pattern_text(
                _supplier_stock_processing_mode_label(source.get("processing_mode"))
            )
            enabled = source.get("enabled", True)
            unpack_enabled = source.get("unpack_archive", False)
            status_icon = "🟢" if enabled else "🔴"
            unpack_text = "да" if unpack_enabled else "нет"
            message_lines.append(
                (
                    f"{index}. {status_icon} *{name}*\n"
                    f"   • URL: `{url}`\n"
                    f"   • Файл: `{output_name}`\n"
                    f"   • Метод: `{method}`\n"
                    f"   • Обработка: `{processing_mode}`\n"
                    f"   • Распаковка: `{unpack_text}`\n"
                )
            )
        message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("➕ Добавить источник", callback_data="supplier_stock_source_add")],
    ]

    for source in sources:
        source_id = source.get("id") or ""
        if not source_id:
            continue
        enabled = source.get("enabled", True)
        unpack_enabled = source.get("unpack_archive", False)
        toggle_text = "⛔️ Выключить" if enabled else "✅ Включить"
        unpack_text = "📦 Распаковка: вкл" if unpack_enabled else "📦 Распаковка: выкл"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"⚙️ {source.get('name', source_id)}",
                    callback_data=f"supplier_stock_source_settings|{source_id}",
                ),
                InlineKeyboardButton(
                    f"{toggle_text}", callback_data=f"supplier_stock_source_toggle_{source_id}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    unpack_text, callback_data=f"supplier_stock_source_unpack_toggle_{source_id}"
                ),
                InlineKeyboardButton(
                    "🗑️", callback_data=f"supplier_stock_source_delete_{source_id}"
                ),
            ]
        )

    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data="main_menu")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_download"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_settings(update, context, source_id: str):
    """Показать настройки конкретного источника остатков."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_source_settings_id"] = source_id
    context.user_data.pop("supplier_stock_source_field", None)
    context.user_data.pop("supplier_stock_source_field_id", None)
    context.user_data.pop("supplier_stock_source_iek_field", None)
    context.user_data.pop("supplier_stock_source_iek_field_id", None)

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return

    name = _escape_pattern_text(source.get("name") or source_id)
    url = _escape_pattern_text(source.get("url") or "не задан")
    output_name = _escape_pattern_text(source.get("output_name") or "не задано")
    method = _escape_pattern_text(source.get("method") or "http")
    processing_mode = source.get("processing_mode") or "table"
    processing_label = _escape_pattern_text(_supplier_stock_processing_mode_label(processing_mode))
    discover = source.get("discover")
    discover_text = "не задано"
    if isinstance(discover, dict):
        discover_text = _escape_pattern_text(
            f"{discover.get('url', '')} | {discover.get('pattern', '')} | {discover.get('prefix', '')}"
        )
    vars_map = source.get("vars") or {}
    vars_text = (
        ", ".join([f"{key}={value}" for key, value in vars_map.items()])
        if vars_map
        else "не задано"
    )
    auth_state = "задано" if source.get("auth") else "не задано"
    pre_request = source.get("pre_request") or {}
    pre_request_text = "не задано"
    if pre_request:
        pre_request_text = _escape_pattern_text(
            f"{pre_request.get('url', '')} | {pre_request.get('data', '')}"
        )
    options = []
    if source.get("include_headers"):
        options.append("headers")
    if source.get("append"):
        options.append("append")
    options_text = ", ".join(options) if options else "не задано"
    upload_subdir = _escape_pattern_text(source.get("upload_subdir") or "не задано")
    individual_dir = source.get("individual_directory") or {}
    individual_enabled = individual_dir.get("enabled", False)
    individual_status = "вкл" if individual_enabled else "выкл"
    individual_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")
    status_icon = "🟢" if source.get("enabled", True) else "🔴"
    unpack_text = "вкл" if source.get("unpack_archive", False) else "выкл"

    rules = config.get("processing", {}).get("rules", [])
    matched_rules = [
        rule
        for rule in rules
        if _processing_rule_matches_source(rule, source_id, "download", config)
    ]
    iek_section: list[str] = []
    if processing_mode == "iek_json":
        iek_settings = source.get("iek_json") or {}
        stores = iek_settings.get("stores", {})
        orc_stores = iek_settings.get("orc_stores", [])
        outputs = iek_settings.get("outputs", {})
        stores_text = _escape_pattern_text(
            ", ".join([f"{key}={value}" for key, value in stores.items()]) or "не задано"
        )
        orc_text = _escape_pattern_text(
            ", ".join(
                [
                    f"{item.get('key')}={item.get('stor')}"
                    for item in orc_stores
                    if isinstance(item, dict)
                ]
            )
            or "не задано"
        )
        outputs_text = _escape_pattern_text(
            ", ".join([f"{key}={value}" for key, value in outputs.items()]) or "не задано"
        )
        prefix_text = _escape_pattern_text(iek_settings.get("prefix") or "не задано")
        msk_stores = iek_settings.get("msk_stores", [])
        msk_text = _escape_pattern_text(", ".join(msk_stores) or "не задано")
        nsk_text = _escape_pattern_text(iek_settings.get("nsk_store") or "не задано")
        iek_section = [
            "⚙️ *IEK JSON*",
            f"• Склады: `{stores_text}`",
            f"• МСК склады: `{msk_text}`",
            f"• НСК склад: `{nsk_text}`",
            f"• ORK stor: `{orc_text}`",
            f"• Префикс артикула: `{prefix_text}`",
            f"• Файлы: `{outputs_text}`",
        ]

    message_lines = [
        "⚙️ *Источник остатков*\n",
        f"{status_icon} *{name}*",
        f"• URL: `{url}`",
        f"• Файл: `{output_name}`",
        f"• Метод: `{method}`",
        f"• Обработка: `{processing_label}`",
        f"• Поиск ссылки: `{discover_text}`",
        f"• Переменные: `{_escape_pattern_text(vars_text)}`",
        f"• Авторизация: `{auth_state}`",
        f"• Предзапрос: `{pre_request_text}`",
        f"• Опции: `{_escape_pattern_text(options_text)}`",
        f"• Подкаталог выгрузки: `{upload_subdir}`",
        f"• Индивидуальный каталог: `{individual_status}`",
        f"• UNC индивидуального каталога: `{individual_path}`",
        f"• Распаковка: `{unpack_text}`",
    ]
    if iek_section:
        message_lines.extend(["", *iek_section])
    message_lines.extend(
        [
            "\n🧩 *Обработка файлов*",
            f"Правил: {len(matched_rules)}",
        ]
    )
    if matched_rules:
        for index, rule in enumerate(matched_rules, start=1):
            rule_name = _escape_pattern_text(
                rule.get("name") or rule.get("id") or f"Правило {index}"
            )
            source_file = _escape_pattern_text(rule.get("source_file") or "не задано")
            enabled = rule.get("enabled", True)
            status = "🟢" if enabled else "🔴"
            message_lines.append(f"{index}. {status} *{rule_name}* (`{source_file}`)")

    message_lines.append("\nВыберите настройку:")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("— Настройки источника —", callback_data="supplier_stock_noop")],
        [
            InlineKeyboardButton(
                "✏️ Название", callback_data=f"supplier_stock_source_field|{source_id}|name"
            ),
            InlineKeyboardButton(
                "🔗 URL", callback_data=f"supplier_stock_source_field|{source_id}|url"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔎 Поиск ссылки", callback_data=f"supplier_stock_source_field|{source_id}|discover"
            ),
            InlineKeyboardButton(
                "🧩 Переменные", callback_data=f"supplier_stock_source_field|{source_id}|vars"
            ),
        ],
        [
            InlineKeyboardButton(
                "📄 Имя файла", callback_data=f"supplier_stock_source_field|{source_id}|output_name"
            ),
            InlineKeyboardButton(
                "🔐 Авторизация", callback_data=f"supplier_stock_source_field|{source_id}|auth"
            ),
        ],
        [
            InlineKeyboardButton(
                "📬 Предзапрос",
                callback_data=f"supplier_stock_source_field|{source_id}|pre_request",
            ),
            InlineKeyboardButton(
                "⚙️ Опции", callback_data=f"supplier_stock_source_field|{source_id}|options"
            ),
        ],
        [
            InlineKeyboardButton(
                "🧩 Тип обработки",
                callback_data=f"supplier_stock_source_field|{source_id}|processing_mode",
            ),
            InlineKeyboardButton(
                "📂 Подкаталог выгрузки",
                callback_data=f"supplier_stock_source_field|{source_id}|upload_subdir",
            ),
        ],
    ]
    if processing_mode == "iek_json":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ IEK JSON", callback_data=f"supplier_stock_source_iek_settings|{source_id}"
                )
            ]
        )
    keyboard.extend(
        [
            [
                InlineKeyboardButton(
                    "📁 Индивидуальный каталог",
                    callback_data=f"supplier_stock_source_individual|{source_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔁 Включить/выключить",
                    callback_data=f"supplier_stock_source_toggle_{source_id}",
                ),
                InlineKeyboardButton(
                    f"📦 Распаковка: {unpack_text}",
                    callback_data=f"supplier_stock_source_unpack_toggle_{source_id}",
                ),
            ],
            [InlineKeyboardButton("— Обработка файлов —", callback_data="supplier_stock_noop")],
            [
                InlineKeyboardButton(
                    "📋 Правила обработки",
                    callback_data=f"supplier_stock_processing_source|{source_id}|menu",
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Добавить правило",
                    callback_data=f"supplier_stock_processing_source|{source_id}|add",
                )
            ],
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_individual_settings(update, context, source_id: str) -> None:
    """Показать настройки индивидуального каталога источника."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return

    individual_dir = source.get("individual_directory") or {}
    enabled = individual_dir.get("enabled", False)
    status_text = "🟢 Включено" if enabled else "🔴 Выключено"
    unc_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")
    login = _escape_pattern_text(individual_dir.get("login") or "не задано")
    password = "задано" if individual_dir.get("password") else "не задано"

    message = (
        "📁 *Индивидуальный каталог*\n\n"
        f"Статус: {status_text}\n"
        f"UNC путь: `{unc_path}`\n"
        f"Логин: `{login}`\n"
        f"Пароль: `{password}`\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔁 Включить/выключить",
                callback_data=f"supplier_stock_source_individual_toggle_{source_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "📂 UNC путь",
                callback_data=f"supplier_stock_source_field|{source_id}|individual_path",
            ),
            InlineKeyboardButton(
                "👤 Логин",
                callback_data=f"supplier_stock_source_field|{source_id}|individual_login",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔐 Пароль",
                callback_data=f"supplier_stock_source_field|{source_id}|individual_password",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ Назад", callback_data=f"supplier_stock_source_settings|{source_id}"
            )
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_source_iek_settings(update, context, source_id: str) -> None:
    """Показать настройки обработки IEK JSON."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return

    iek_settings = source.get("iek_json") or {}
    stores = iek_settings.get("stores", {})
    orc_stores = iek_settings.get("orc_stores", [])
    outputs = iek_settings.get("outputs", {})

    stores_text = _escape_pattern_text(
        ", ".join([f"{key}={value}" for key, value in stores.items()]) or "не задано"
    )
    orc_text = _escape_pattern_text(
        ", ".join(
            [
                f"{item.get('key')}={item.get('stor')}"
                for item in orc_stores
                if isinstance(item, dict)
            ]
        )
        or "не задано"
    )
    outputs_text = _escape_pattern_text(
        ", ".join([f"{key}={value}" for key, value in outputs.items()]) or "не задано"
    )
    prefix_text = _escape_pattern_text(iek_settings.get("prefix") or "не задано")
    msk_stores = iek_settings.get("msk_stores", [])
    msk_text = _escape_pattern_text(", ".join(msk_stores) or "не задано")
    nsk_text = _escape_pattern_text(iek_settings.get("nsk_store") or "не задано")

    message = (
        "⚙️ *IEK JSON*\n\n"
        f"Склады: `{stores_text}`\n"
        f"МСК склады: `{msk_text}`\n"
        f"НСК склад: `{nsk_text}`\n"
        f"ОРК stor: `{orc_text}`\n"
        f"Префикс артикула: `{prefix_text}`\n"
        f"Файлы: `{outputs_text}`\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🗺️ Склады", callback_data=f"supplier_stock_source_iek_field|{source_id}|stores"
            )
        ],
        [
            InlineKeyboardButton(
                "📍 МСК склады",
                callback_data=f"supplier_stock_source_iek_field|{source_id}|msk_stores",
            )
        ],
        [
            InlineKeyboardButton(
                "📍 НСК склад",
                callback_data=f"supplier_stock_source_iek_field|{source_id}|nsk_store",
            )
        ],
        [
            InlineKeyboardButton(
                "🧾 ORK stor",
                callback_data=f"supplier_stock_source_iek_field|{source_id}|orc_stores",
            )
        ],
        [
            InlineKeyboardButton(
                "🏷️ Префикс артикула",
                callback_data=f"supplier_stock_source_iek_field|{source_id}|prefix",
            )
        ],
        [
            InlineKeyboardButton(
                "📄 Файлы", callback_data=f"supplier_stock_source_iek_field|{source_id}|outputs"
            )
        ],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton(
                "↩️ Назад", callback_data=f"supplier_stock_source_settings|{source_id}"
            ),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_mail_source_settings(update, context, source_id: str):
    """Показать настройки правила вложений."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_mail_source_settings_id"] = source_id
    context.user_data.pop("supplier_stock_mail_source_field", None)
    context.user_data.pop("supplier_stock_mail_source_field_id", None)

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return

    name = _escape_pattern_text(source.get("name") or source_id)
    sender = _escape_pattern_text(source.get("sender_pattern") or "любой")
    subject = _escape_pattern_text(source.get("subject_pattern") or "любой")
    mime_pattern = _escape_pattern_text(source.get("mime_pattern") or "application/.*")
    filename_pattern = _escape_pattern_text(source.get("filename_pattern") or "любой")
    expected = source.get("expected_attachments", 1)
    output_template = _escape_pattern_text(source.get("output_template") or "не задано")
    enabled = source.get("enabled", True)
    unpack_enabled = source.get("unpack_archive", False)
    status_icon = "🟢" if enabled else "🔴"
    unpack_text = "вкл" if unpack_enabled else "выкл"
    upload_subdir = _escape_pattern_text(source.get("upload_subdir") or "не задано")
    individual_dir = source.get("individual_directory") or {}
    individual_enabled = individual_dir.get("enabled", False)
    individual_status = "вкл" if individual_enabled else "выкл"
    individual_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")

    rules = config.get("processing", {}).get("rules", [])
    matched_rules = [
        rule for rule in rules if _processing_rule_matches_source(rule, source_id, "mail", config)
    ]

    message_lines = [
        "📎 *Правило вложений*\n",
        f"{status_icon} *{name}*",
        f"• Отправитель: `{sender}`",
        f"• Тема: `{subject}`",
        f"• MIME: `{mime_pattern}`",
        f"• Имя файла: `{filename_pattern}`",
        f"• Ожидается: `{expected}`",
        f"• Шаблон: `{output_template}`",
        f"• Подкаталог выгрузки: `{upload_subdir}`",
        f"• Индивидуальный каталог: `{individual_status}`",
        f"• UNC индивидуального каталога: `{individual_path}`",
        f"• Распаковка: `{unpack_text}`\n",
        "🧩 *Обработка файлов*",
        f"Правил: {len(matched_rules)}",
    ]
    if matched_rules:
        for index, rule in enumerate(matched_rules, start=1):
            rule_name = _escape_pattern_text(
                rule.get("name") or rule.get("id") or f"Правило {index}"
            )
            source_file = _escape_pattern_text(rule.get("source_file") or "не задано")
            enabled_rule = rule.get("enabled", True)
            status = "🟢" if enabled_rule else "🔴"
            message_lines.append(f"{index}. {status} *{rule_name}* (`{source_file}`)")

    message_lines.append("\nВыберите настройку:")
    message = "\n".join(message_lines)

    keyboard = [
        [InlineKeyboardButton("— Настройки правила —", callback_data="supplier_stock_noop")],
        [
            InlineKeyboardButton(
                "✏️ Название", callback_data=f"supplier_stock_mail_field|{source_id}|name"
            ),
            InlineKeyboardButton(
                "👤 Отправитель", callback_data=f"supplier_stock_mail_field|{source_id}|sender"
            ),
        ],
        [
            InlineKeyboardButton(
                "📝 Тема", callback_data=f"supplier_stock_mail_field|{source_id}|subject"
            ),
            InlineKeyboardButton(
                "🧾 MIME", callback_data=f"supplier_stock_mail_field|{source_id}|mime"
            ),
        ],
        [
            InlineKeyboardButton(
                "📄 Имя файла", callback_data=f"supplier_stock_mail_field|{source_id}|filename"
            ),
            InlineKeyboardButton(
                "🔢 Кол-во вложений",
                callback_data=f"supplier_stock_mail_field|{source_id}|expected",
            ),
        ],
        [
            InlineKeyboardButton(
                "📦 Шаблон файла", callback_data=f"supplier_stock_mail_field|{source_id}|output"
            ),
        ],
        [
            InlineKeyboardButton(
                "📂 Подкаталог выгрузки",
                callback_data=f"supplier_stock_mail_field|{source_id}|upload_subdir",
            ),
            InlineKeyboardButton(
                "📁 Индивидуальный каталог",
                callback_data=f"supplier_stock_mail_source_individual|{source_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔁 Включить/выключить",
                callback_data=f"supplier_stock_mail_source_toggle_{source_id}",
            ),
            InlineKeyboardButton(
                f"📦 Распаковка: {unpack_text}",
                callback_data=f"supplier_stock_mail_source_unpack_toggle_{source_id}",
            ),
        ],
        [InlineKeyboardButton("— Обработка файлов —", callback_data="supplier_stock_noop")],
        [
            InlineKeyboardButton(
                "📋 Правила обработки",
                callback_data=f"supplier_stock_processing_mail|{source_id}|menu",
            )
        ],
        [
            InlineKeyboardButton(
                "➕ Добавить правило",
                callback_data=f"supplier_stock_processing_mail|{source_id}|add",
            )
        ],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_supplier_stock_mail_source_individual_settings(update, context, source_id: str) -> None:
    """Показать настройки индивидуального каталога правила вложений."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return

    individual_dir = source.get("individual_directory") or {}
    enabled = individual_dir.get("enabled", False)
    status_text = "🟢 Включено" if enabled else "🔴 Выключено"
    unc_path = _escape_pattern_text(individual_dir.get("unc_path") or "не задано")
    login = _escape_pattern_text(individual_dir.get("login") or "не задано")
    password = "задано" if individual_dir.get("password") else "не задано"

    message = (
        "📁 *Индивидуальный каталог*\n\n"
        f"Статус: {status_text}\n"
        f"UNC путь: `{unc_path}`\n"
        f"Логин: `{login}`\n"
        f"Пароль: `{password}`\n\n"
        "Выберите действие:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔁 Включить/выключить",
                callback_data=f"supplier_stock_mail_source_individual_toggle_{source_id}",
            )
        ],
        [
            InlineKeyboardButton(
                "📂 UNC путь",
                callback_data=f"supplier_stock_mail_field|{source_id}|individual_path",
            ),
            InlineKeyboardButton(
                "👤 Логин", callback_data=f"supplier_stock_mail_field|{source_id}|individual_login"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔐 Пароль",
                callback_data=f"supplier_stock_mail_field|{source_id}|individual_password",
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ Назад", callback_data=f"supplier_stock_mail_source_settings|{source_id}"
            )
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def supplier_stock_start_source_field_edit(update, context, source_id: str, field: str) -> None:
    """Запросить изменение конкретного поля источника."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return

    context.user_data["supplier_stock_source_field"] = field
    context.user_data["supplier_stock_source_field_id"] = source_id

    prompts = {
        "name": "Введите название источника (или '-' чтобы оставить):",
        "url": "Введите URL для скачивания (или '-' чтобы оставить):",
        "discover": "Введите параметры поиска URL (URL | regex | prefix), '-' чтобы оставить или 'none' чтобы очистить:",
        "vars": "Введите переменные подстановки key=value через запятую, '-' чтобы оставить или 'none' чтобы очистить:",
        "output_name": "Введите имя файла назначения (или '-' чтобы оставить):",
        "auth": "Введите login:password, '-' чтобы оставить или 'none' чтобы очистить:",
        "pre_request": "Введите URL | данные для предзапроса, '-' чтобы оставить или 'none' чтобы очистить:",
        "options": "Введите опции (headers, append) через запятую, '-' чтобы оставить или 'none' чтобы очистить:",
        "processing_mode": "Введите тип обработки (`table` или `iek\\_json`), '-' чтобы оставить:",
        "upload_subdir": "Введите подкаталог для выгрузки (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_path": "Введите UNC путь индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_login": "Введите логин индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_password": "Введите пароль индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    current_values = {
        "name": source.get("name") or source_id,
        "url": source.get("url") or "-",
        "discover": source.get("discover") or "-",
        "vars": source.get("vars") or "-",
        "output_name": source.get("output_name") or "-",
        "auth": "задано" if source.get("auth") else "-",
        "pre_request": source.get("pre_request") or "-",
        "options": (
            "headers/append" if (source.get("include_headers") or source.get("append")) else "-"
        ),
        "processing_mode": source.get("processing_mode") or "table",
        "upload_subdir": source.get("upload_subdir") or "-",
        "individual_path": (source.get("individual_directory") or {}).get("unc_path") or "-",
        "individual_login": (source.get("individual_directory") or {}).get("login") or "-",
        "individual_password": (
            "задано" if (source.get("individual_directory") or {}).get("password") else "-"
        ),
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    if isinstance(current_value, dict):
        current_value = json.dumps(current_value, ensure_ascii=False)
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ Отмена", callback_data=f"supplier_stock_source_settings|{source_id}"
                    )
                ]
            ]
        ),
    )


def supplier_stock_start_source_iek_field_edit(update, context, source_id: str, field: str) -> None:
    """Запросить изменение параметров IEK JSON."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return

    context.user_data["supplier_stock_source_iek_field"] = field
    context.user_data["supplier_stock_source_iek_field_id"] = source_id

    prompts = {
        "stores": "Введите склады в формате key=uuid через запятую:",
        "msk_stores": "Введите список складов МСК через запятую (например: sherbinka, chehov):",
        "nsk_store": "Введите ключ склада НСК (например: novosibirsk):",
        "orc_stores": "Введите ORK stor в формате key=stor через запятую:",
        "prefix": "Введите префикс артикула для ORK (или 'none' чтобы очистить):",
        "outputs": "Введите имена файлов в формате orig=..., msk=..., nsk=..., orc=... через запятую:",
    }

    iek_settings = source.get("iek_json") or {}
    current_values = {
        "stores": iek_settings.get("stores") or "-",
        "msk_stores": iek_settings.get("msk_stores") or "-",
        "nsk_store": iek_settings.get("nsk_store") or "-",
        "orc_stores": iek_settings.get("orc_stores") or "-",
        "prefix": iek_settings.get("prefix") or "-",
        "outputs": iek_settings.get("outputs") or "-",
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    if isinstance(current_value, (dict, list)):
        current_value = json.dumps(current_value, ensure_ascii=False)

    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ Отмена", callback_data=f"supplier_stock_source_iek_settings|{source_id}"
                    )
                ],
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
            ]
        ),
    )


def supplier_stock_start_mail_source_field_edit(
    update, context, source_id: str, field: str
) -> None:
    """Запросить изменение конкретного поля правила вложений."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return

    context.user_data["supplier_stock_mail_source_field"] = field
    context.user_data["supplier_stock_mail_source_field_id"] = source_id

    prompts = {
        "name": "Введите название правила (или '-' чтобы оставить):",
        "sender": "Введите regex/адрес отправителя, '-' чтобы оставить или 'none' чтобы очистить:",
        "subject": "Введите regex темы письма, '-' чтобы оставить или 'none' чтобы очистить:",
        "mime": "Введите MIME-фильтр, '-' чтобы оставить или 'none' чтобы очистить:",
        "filename": "Введите regex имени вложения, '-' чтобы оставить или 'none' чтобы очистить:",
        "expected": "Введите количество ожидаемых вложений (или '-' чтобы оставить):",
        "output": "Введите шаблон имени выходного файла (или '-' чтобы оставить):",
        "upload_subdir": "Введите подкаталог для выгрузки (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_path": "Введите UNC путь индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_login": "Введите логин индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
        "individual_password": "Введите пароль индивидуального каталога (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    current_values = {
        "name": source.get("name") or source_id,
        "sender": source.get("sender_pattern") or "-",
        "subject": source.get("subject_pattern") or "-",
        "mime": source.get("mime_pattern") or "application/.*",
        "filename": source.get("filename_pattern") or "-",
        "expected": source.get("expected_attachments", 1),
        "output": source.get("output_template") or "-",
        "upload_subdir": source.get("upload_subdir") or "-",
        "individual_path": (source.get("individual_directory") or {}).get("unc_path") or "-",
        "individual_login": (source.get("individual_directory") or {}).get("login") or "-",
        "individual_password": (
            "задано" if (source.get("individual_directory") or {}).get("password") else "-"
        ),
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=f"supplier_stock_mail_source_settings|{source_id}",
                    )
                ]
            ]
        ),
    )


def supplier_stock_start_resource_wizard(update, context) -> None:
    """Запуск мастера добавления ресурса выгрузки."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_resource_stage"] = "name"
    context.user_data["supplier_stock_resource_data"] = {}
    context.user_data["supplier_stock_resource_add"] = True

    query.edit_message_text(
        "➕ *Новый ресурс выгрузки*\n\nВведите название ресурса:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_resources")]]
        ),
    )


def supplier_stock_start_resource_field_edit(update, context, resource_id: str, field: str) -> None:
    """Запросить изменение поля ресурса выгрузки."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        query.edit_message_text(
            "❌ Ресурс не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_resources")]]
            ),
        )
        return

    context.user_data["supplier_stock_resource_field"] = field
    context.user_data["supplier_stock_resource_field_id"] = resource_id

    prompts = {
        "name": "Введите название ресурса (или '-' чтобы оставить):",
        "unc_path": "Введите UNC путь корневого каталога (или '-' чтобы оставить):",
        "login": "Введите логин ресурса (или '-' чтобы оставить, 'none' чтобы очистить):",
        "password": "Введите пароль ресурса (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    current_values = {
        "name": resource.get("name") or resource_id,
        "unc_path": resource.get("unc_path") or "-",
        "login": resource.get("login") or "-",
        "password": "задано" if resource.get("password") else "-",
    }

    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ Отмена", callback_data=f"supplier_stock_resource_settings|{resource_id}"
                    )
                ]
            ]
        ),
    )


def supplier_stock_start_ftp_field_edit(update, context, field: str) -> None:
    """Запросить изменение параметра FTP."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_ftp_field"] = field
    prompts = {
        "host": "Введите HOST FTP (или '-' чтобы оставить):",
        "login": "Введите логин FTP (или '-' чтобы оставить, 'none' чтобы очистить):",
        "password": "Введите пароль FTP (или '-' чтобы оставить, 'none' чтобы очистить):",
    }

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})
    current_values = {
        "host": ftp_settings.get("host") or "-",
        "login": ftp_settings.get("login") or "-",
        "password": "задано" if ftp_settings.get("password") else "-",
    }
    prompt = prompts.get(field, "Введите значение:")
    current_value = current_values.get(field, "-")
    _supplier_stock_remember_prompt_message(context, query)
    query.edit_message_text(
        f"{prompt}\n\nТекущее значение: `{_escape_pattern_text(str(current_value))}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_ftp")]]
        ),
    )


def supplier_stock_start_processing_wizard(
    update,
    context,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    """Запуск мастера добавления правила обработки."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_edit", None)
    context.user_data.pop("supplier_stock_add_source", None)
    context.user_data.pop("supplier_stock_edit_source", None)
    context.user_data.pop("supplier_stock_mail_edit", None)
    context.user_data.pop("supplier_stock_mail_add_source", None)
    context.user_data.pop("supplier_stock_mail_edit_source", None)
    context.user_data["supplier_stock_processing_stage"] = "name"
    context.user_data["supplier_stock_processing_data"] = {}
    context.user_data["supplier_stock_processing_add"] = True
    context.user_data["supplier_stock_processing_source_id"] = source_id
    context.user_data["supplier_stock_processing_source_kind"] = source_kind
    context.user_data["supplier_stock_processing_back"] = back_callback

    if source_id:
        context.user_data["supplier_stock_processing_data"]["source_id"] = source_id
    if source_kind:
        context.user_data["supplier_stock_processing_data"]["source_kind"] = source_kind

    query.edit_message_text(
        "➕ *Новое правило обработки*\n\nВведите название правила:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data=back_callback)]]
        ),
    )


def supplier_stock_start_processing_edit_wizard(
    update,
    context,
    rule_id: str,
    source_id: str | None = None,
    source_kind: str | None = None,
    back_callback: str = "settings_ext_supplier_stock",
) -> None:
    """Запуск мастера редактирования правила обработки."""
    query = update.callback_query
    query.answer()

    context.user_data.pop("supplier_stock_edit", None)
    context.user_data.pop("supplier_stock_add_source", None)
    context.user_data.pop("supplier_stock_edit_source", None)
    context.user_data.pop("supplier_stock_mail_edit", None)
    context.user_data.pop("supplier_stock_mail_add_source", None)
    context.user_data.pop("supplier_stock_mail_edit_source", None)
    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    rule = next((item for item in rules if str(item.get("id")) == rule_id), None)

    if not rule:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
            ),
        )
        return

    context.user_data["supplier_stock_processing_edit"] = True
    context.user_data["supplier_stock_processing_edit_id"] = rule_id
    context.user_data["supplier_stock_processing_data"] = dict(rule)
    context.user_data["supplier_stock_processing_stage"] = "edit_name"
    context.user_data["supplier_stock_processing_source_id"] = source_id
    context.user_data["supplier_stock_processing_source_kind"] = source_kind
    context.user_data["supplier_stock_processing_back"] = back_callback

    if source_id:
        context.user_data["supplier_stock_processing_data"]["source_id"] = source_id
    if source_kind:
        context.user_data["supplier_stock_processing_data"]["source_kind"] = source_kind

    query.edit_message_text(
        f"✏️ *Редактирование правила обработки*\n\n"
        f"Текущее имя: `{_escape_pattern_text(rule.get('name'))}`\n"
        "Введите новое имя (или '-' чтобы оставить текущее):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data=back_callback)]]
        ),
    )


def supplier_stock_handle_processing_input(update, context):
    """Обработка ввода мастера настройки обработки."""
    stage = context.user_data.get("supplier_stock_processing_stage")
    data = context.user_data.get("supplier_stock_processing_data", {})
    raw_input = update.message.text or ""
    user_input = raw_input.rstrip("\n")
    user_input_stripped = user_input.strip()
    source_id = context.user_data.get("supplier_stock_processing_source_id")
    source_kind = context.user_data.get("supplier_stock_processing_source_kind")
    if source_id:
        data["source_id"] = source_id
    if source_kind:
        data["source_kind"] = source_kind
    back_callback = context.user_data.get(
        "supplier_stock_processing_back", "supplier_stock_processing"
    )

    if context.user_data.get("supplier_stock_processing_field"):
        field = context.user_data.pop("supplier_stock_processing_field")
        variant_index = context.user_data.pop("supplier_stock_processing_variant_index", None)
        item_index = context.user_data.pop("supplier_stock_processing_item_index", None)
        rule_data = context.user_data.get("supplier_stock_processing_rule_data", {})
        if source_id:
            rule_data["source_id"] = source_id
        if source_kind:
            rule_data["source_kind"] = source_kind
        variant_fields = {
            "article_col",
            "article_filter",
            "extra_filter",
            "article_prefix",
            "article_postfix",
            "article_transform",
            "data_columns_count",
            "data_column",
            "output_name",
            "output_format",
            "orc_prefix",
            "orc_stor",
            "orc_column",
            "orc_output_name",
            "orc_output_format",
        }
        if variant_index is not None and field in variant_fields:
            variant = _ensure_processing_variant(rule_data, variant_index)
            if field == "article_col":
                article_col = _parse_positive_int(user_input_stripped)
                if article_col is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                variant["article_col"] = article_col
            elif field == "article_filter":
                if user_input_stripped not in ("-", ""):
                    variant["article_filter"] = user_input_stripped
                    if variant.get("use_article_filter") is None:
                        variant["use_article_filter"] = True
                else:
                    variant.pop("article_filter", None)
            elif field == "extra_filter":
                if user_input_stripped in ("-", ""):
                    variant.pop("extra_filter", None)
                    variant.pop("extra_filter_col", None)
                else:
                    if ";" not in user_input_stripped:
                        update.message.reply_text("❌ Укажите номер колонки и условие через ';'.")
                        return None
                    col_part, filter_part = user_input_stripped.split(";", 1)
                    extra_filter_col = _parse_positive_int(col_part.strip())
                    extra_filter_value = filter_part.strip()
                    if extra_filter_col is None:
                        update.message.reply_text(
                            "❌ Номер колонки должен быть целым числом больше 0."
                        )
                        return None
                    if not extra_filter_value:
                        update.message.reply_text("❌ Укажите условие отбора после ';'.")
                        return None
                    variant["extra_filter_col"] = extra_filter_col
                    variant["extra_filter"] = extra_filter_value
            elif field == "article_prefix":
                if user_input_stripped in ("-", ""):
                    variant["article_prefix"] = ""
                else:
                    variant["article_prefix"] = user_input
            elif field == "article_postfix":
                raw_value = user_input
                if raw_value == "":
                    variant["article_postfix"] = ""
                elif raw_value.strip() == "-":
                    variant["article_postfix"] = ""
                else:
                    variant["article_postfix"] = raw_value
            elif field == "article_transform":
                raw_value = user_input
                if raw_value.strip() in ("", "-"):
                    variant["article_transform"] = {
                        "pattern": "",
                        "replacement": "",
                    }
                else:
                    if "=>" in raw_value:
                        pattern_part, replacement_part = raw_value.split("=>", 1)
                        pattern_value = pattern_part.strip()
                        replacement_value = replacement_part
                    else:
                        pattern_value = raw_value.strip()
                        replacement_value = ""
                    if not pattern_value:
                        update.message.reply_text(
                            "❌ Укажите regex-паттерн для изменения артикула."
                        )
                        return None
                    variant["article_transform"] = {
                        "pattern": pattern_value,
                        "replacement": replacement_value,
                    }
            elif field == "data_columns_count":
                columns_count = _parse_positive_int(user_input_stripped)
                if columns_count is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                _sync_variant_columns(variant, columns_count)
            elif field == "data_column":
                col_value = _parse_positive_int(user_input_stripped)
                if col_value is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                columns = list(variant.get("data_columns", []))
                if item_index is None or item_index >= len(columns):
                    update.message.reply_text("❌ Неверный индекс колонки.")
                    return None
                columns[item_index] = col_value
                variant["data_columns"] = columns
            elif field == "output_name":
                if not user_input_stripped:
                    update.message.reply_text(
                        "❌ Имя файла не может быть пустым. Попробуйте снова:"
                    )
                    return None
                names = list(variant.get("output_names", []))
                if item_index is None or item_index >= len(names):
                    update.message.reply_text("❌ Неверный индекс файла.")
                    return None
                names[item_index] = user_input_stripped
                variant["output_names"] = names
            elif field == "output_format":
                format_value = user_input_stripped.lower()
                if format_value not in ("xls", "xlsx", "csv"):
                    update.message.reply_text("❌ Допустимые форматы: xls, xlsx, csv.")
                    return None
                variant["output_format"] = format_value
            elif field == "orc_prefix":
                orc = variant.get("orc", {})
                if user_input_stripped in ("-", ""):
                    orc["prefix"] = ""
                else:
                    orc["prefix"] = user_input
                variant["orc"] = orc
            elif field == "orc_stor":
                if not user_input_stripped:
                    update.message.reply_text("❌ Stor не может быть пустым. Попробуйте снова:")
                    return None
                orc = variant.get("orc", {})
                orc["stor"] = user_input_stripped
                variant["orc"] = orc
            elif field == "orc_column":
                col_value = _parse_positive_int(user_input_stripped)
                if col_value is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                orc = variant.get("orc", {})
                orc["column"] = col_value
                variant["orc"] = orc
            elif field == "orc_output_name":
                orc = variant.get("orc", {})
                if user_input_stripped in ("-", ""):
                    orc.pop("output_name", None)
                else:
                    orc["output_name"] = user_input_stripped
                variant["orc"] = orc
            elif field == "orc_output_format":
                if user_input_stripped in ("-", ""):
                    orc = variant.get("orc", {})
                    orc.pop("output_format", None)
                    variant["orc"] = orc
                else:
                    format_value = user_input_stripped.lower()
                    if format_value not in ("xls", "xlsx", "csv"):
                        update.message.reply_text("❌ Допустимые форматы: xls, xlsx, csv.")
                        return None
                    orc = variant.get("orc", {})
                    orc["output_format"] = format_value
                    variant["orc"] = orc
            rule_data["variants"][variant_index] = variant
        else:
            if field == "name":
                if not user_input_stripped:
                    update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
                    return None
                rule_data["name"] = user_input_stripped
            elif field == "source_file":
                if not user_input_stripped:
                    update.message.reply_text(
                        "❌ Имя файла не может быть пустым. Попробуйте снова:"
                    )
                    return None
                rule_data["source_file"] = user_input_stripped
            elif field == "data_row":
                data_row = _parse_positive_int(user_input_stripped)
                if data_row is None:
                    update.message.reply_text("❌ Введите целое число больше 0.")
                    return None
                rule_data["data_row"] = data_row
            elif field == "output_name":
                if not user_input_stripped:
                    update.message.reply_text(
                        "❌ Имя файла не может быть пустым. Попробуйте снова:"
                    )
                    return None
                rule_data["output_name"] = user_input_stripped
            else:
                update.message.reply_text("❌ Не удалось определить вариант настройки.")
                return None
        context.user_data["supplier_stock_processing_rule_data"] = rule_data
        context.user_data["supplier_stock_processing_rule_dirty"] = True
        _supplier_stock_close_prompt_message(context)
        if variant_index is None:
            update.message.reply_text(
                "✅ Готово.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "↩️ Назад", callback_data="supplier_stock_processing_rule|menu"
                            )
                        ]
                    ]
                ),
            )
        else:
            update.message.reply_text(
                "✅ Готово.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "↩️ Назад",
                                callback_data=f"supplier_stock_processing_variant|menu|{variant_index}",
                            )
                        ]
                    ]
                ),
            )
        _persist_processing_rule_data(context)
        return None

    if stage == "name":
        if not user_input_stripped:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        data["name"] = user_input_stripped
        data["id"] = _slugify_supplier_source_id(user_input_stripped)
        context.user_data["supplier_stock_processing_stage"] = "source_file"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Введите файл источника (например: supplier_1_orig.xls):")
        return None

    if stage == "edit_name":
        if user_input_stripped and user_input_stripped not in ("-",):
            data["name"] = user_input_stripped
        context.user_data["supplier_stock_processing_stage"] = "edit_source_file"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text(
            f"Текущий файл источника: {data.get('source_file', '-')}\n"
            "Введите новый файл источника (или '-' чтобы оставить текущее):"
        )
        return None

    if stage == "edit_source_file":
        if user_input_stripped and user_input_stripped not in ("-",):
            data["source_file"] = user_input_stripped
        context.user_data["supplier_stock_processing_stage"] = "edit_reconfigure"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Перенастроить обработку? (да/нет):")
        return None

    if stage == "edit_reconfigure":
        reconfigure = _parse_yes_no(user_input_stripped)
        if reconfigure is None:
            update.message.reply_text("❌ Ответьте 'да' или 'нет'.")
            return None
        if not reconfigure:
            _save_supplier_stock_processing_rule(context, data, edit_id=data.get("id"))
            update.message.reply_text(
                "✅ Правило обновлено.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
                ),
            )
            return None
        data.pop("variants", None)
        data.pop("variants_count", None)
        data.pop("data_row", None)
        data.pop("requires_processing", None)
        context.user_data["supplier_stock_processing_stage"] = "needs_processing"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Требуется обработка файла? (да/нет):")
        return None

    if stage == "source_file":
        if not user_input_stripped:
            update.message.reply_text("❌ Файл источника не может быть пустым. Попробуйте снова:")
            return None
        data["source_file"] = user_input_stripped
        context.user_data["supplier_stock_processing_stage"] = "needs_processing"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Требуется обработка файла? (да/нет):")
        return None

    if stage == "needs_processing":
        needs_processing = _parse_yes_no(user_input_stripped)
        if needs_processing is None:
            update.message.reply_text("❌ Ответьте 'да' или 'нет'.")
            return None
        data["requires_processing"] = needs_processing
        if not needs_processing:
            edit_id = (
                data.get("id") if context.user_data.get("supplier_stock_processing_edit") else None
            )
            _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
            done_text = (
                "✅ Правило обновлено."
                if context.user_data.get("supplier_stock_processing_edit")
                else "✅ Правило добавлено."
            )
            update.message.reply_text(
                done_text,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
                ),
            )
            return None
        context.user_data["supplier_stock_processing_stage"] = "variants_count"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Сколько вариантов конечных файлов требуется? (число):")
        return None

    if stage == "variants_count":
        variants_count = _parse_positive_int(user_input_stripped)
        if variants_count is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        data["variants_count"] = variants_count
        data["variants"] = []
        context.user_data["supplier_stock_processing_variant_index"] = 0
        context.user_data["supplier_stock_processing_stage"] = "data_row"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Введите номер первой строки с данными (например: 2):")
        return None

    if stage == "data_row":
        data_row = _parse_positive_int(user_input_stripped)
        if data_row is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        data["data_row"] = data_row
        context.user_data["supplier_stock_processing_stage"] = "variant_article_col"
        context.user_data["supplier_stock_processing_data"] = data
        update.message.reply_text("Введите номер колонки с артикулом:")
        return None

    if stage == "variant_article_col":
        article_col = _parse_positive_int(user_input_stripped)
        if article_col is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        context.user_data["supplier_stock_processing_current_variant"] = {
            "article_col": article_col,
        }
        context.user_data["supplier_stock_processing_stage"] = "variant_article_filter"
        update.message.reply_text(
            "Введите условия отбора артикулов (regex) или '-' для всех.\n\n"
            "Примеры условий:\n"
            "• $1 ~ /^[0-9]/ && $col+0 > 0\n"
            "• $1 ~ /^[A-Z].*/ && $4 ~ /^[0-9]+$/\n"
            "• grep -E '^DKS [0-9A-Z]{6,},'\n"
            '• gsub(/^\./, "", art); gsub(/[A-Za-z]+$/, "", art);\n'
            '• ($3+0 > 0) && ($4 == "Москва")'
        )
        return None

    if stage == "variant_article_filter":
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        if user_input_stripped not in ("-", ""):
            variant["article_filter"] = user_input_stripped
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_stage"] = "variant_prefix"
        update.message.reply_text(
            "Введите префикс артикула (или '-' если не нужен). "
            "Пробелы в конце сохраняются, либо используйте \\s."
        )
        return None

    if stage == "variant_prefix":
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        if user_input_stripped in ("-", ""):
            variant["article_prefix"] = ""
        else:
            variant["article_prefix"] = user_input
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_stage"] = "variant_postfix"
        update.message.reply_text(
            "Введите постфикс артикула (или '-' если не нужен). " "Пробелы в конце сохраняются."
        )
        return None

    if stage == "variant_postfix":
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        raw_value = user_input
        if raw_value == "":
            variant["article_postfix"] = ""
        elif raw_value.strip() == "-":
            variant["article_postfix"] = ""
        else:
            variant["article_postfix"] = raw_value
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_stage"] = "data_columns_count"
        update.message.reply_text("Сколько колонок с данными нужно использовать? (число):")
        return None

    if stage == "data_columns_count":
        columns_count = _parse_positive_int(user_input_stripped)
        if columns_count is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        context.user_data["supplier_stock_processing_data_columns_expected"] = columns_count
        context.user_data["supplier_stock_processing_data_columns"] = []
        context.user_data["supplier_stock_processing_stage"] = "data_column"
        update.message.reply_text("Введите номер колонки с данными 1 из %d:" % columns_count)
        return None

    if stage == "data_column":
        col_value = _parse_positive_int(user_input_stripped)
        if col_value is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        columns = context.user_data.get("supplier_stock_processing_data_columns", [])
        columns.append(col_value)
        context.user_data["supplier_stock_processing_data_columns"] = columns
        expected = context.user_data.get("supplier_stock_processing_data_columns_expected", 0)
        if len(columns) < expected:
            update.message.reply_text(
                "Введите номер колонки с данными %d из %d:" % (len(columns) + 1, expected)
            )
            return None
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        variant["data_columns"] = columns
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_output_names_expected"] = expected
        context.user_data["supplier_stock_processing_output_names"] = []
        context.user_data["supplier_stock_processing_stage"] = "output_name"
        update.message.reply_text(
            "Введите имя выходного файла для колонки 1 из %d "
            "(можно использовать {index}, {name}, {filename}):" % expected
        )
        return None

    if stage == "output_name":
        if not user_input_stripped:
            update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
            return None
        names = context.user_data.get("supplier_stock_processing_output_names", [])
        names.append(user_input_stripped)
        context.user_data["supplier_stock_processing_output_names"] = names
        expected = context.user_data.get("supplier_stock_processing_output_names_expected", 0)
        if len(names) < expected:
            update.message.reply_text(
                "Введите имя выходного файла для колонки %d из %d "
                "(можно использовать {index}, {name}, {filename}):" % (len(names) + 1, expected)
            )
            return None
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        variant["output_names"] = names
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_stage"] = "output_format"
        update.message.reply_text("Введите формат выходного файла (xls, xlsx, csv):")
        return None

    if stage == "output_format":
        format_value = user_input_stripped.lower()
        if format_value not in ("xls", "xlsx", "csv"):
            update.message.reply_text("❌ Допустимые форматы: xls, xlsx, csv.")
            return None
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        variant["output_format"] = format_value
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_stage"] = "orc_required"
        update.message.reply_text("Нужно формировать отдельный файл для ОРК? (да/нет):")
        return None

    if stage == "orc_required":
        orc_required = _parse_yes_no(user_input_stripped)
        if orc_required is None:
            update.message.reply_text("❌ Ответьте 'да' или 'нет'.")
            return None
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        variant["orc"] = {"enabled": orc_required}
        context.user_data["supplier_stock_processing_current_variant"] = variant
        if not orc_required:
            return _supplier_stock_finish_variant(update, context, data)
        context.user_data["supplier_stock_processing_stage"] = "orc_prefix"
        update.message.reply_text(
            "Введите префикс артикула для файла ОРК (или '-' если не нужен). "
            "Пробелы в конце сохраняются."
        )
        return None

    if stage == "orc_prefix":
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        if user_input_stripped in ("-", ""):
            variant["orc"]["prefix"] = ""
        else:
            variant["orc"]["prefix"] = user_input
        context.user_data["supplier_stock_processing_current_variant"] = variant
        context.user_data["supplier_stock_processing_stage"] = "orc_stor"
        update.message.reply_text("Введите параметр Stor для файла ОРК:")
        return None

    if stage == "orc_stor":
        if not user_input_stripped:
            update.message.reply_text("❌ Stor не может быть пустым. Попробуйте снова:")
            return None
        variant = context.user_data.get("supplier_stock_processing_current_variant", {})
        variant["orc"]["stor"] = user_input_stripped
        context.user_data["supplier_stock_processing_current_variant"] = variant
        return _supplier_stock_finish_variant(update, context, data)

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None


def supplier_stock_start_source_wizard(update, context):
    """Запуск мастера добавления источника остатков."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_source_stage"] = "name"
    context.user_data["supplier_stock_source_data"] = {}
    context.user_data["supplier_stock_add_source"] = True

    query.edit_message_text(
        "➕ *Новый источник остатков*\n\nВведите название источника:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_sources")]]
        ),
    )


def supplier_stock_start_edit_wizard(update, context, source_id: str):
    """Запуск мастера редактирования источника остатков."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return

    context.user_data["supplier_stock_edit_source"] = True
    context.user_data["supplier_stock_edit_source_stage"] = "name"
    context.user_data["supplier_stock_edit_source_id"] = source_id

    query.edit_message_text(
        f"✏️ *Редактирование источника*\n\nТекущее имя: `{_escape_pattern_text(source.get('name'))}`\n"
        "Введите новое имя (или '-' чтобы оставить текущее):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_sources")]]
        ),
    )


def supplier_stock_handle_input(update, context):
    """Обработчик ввода для настроек остатков поставщиков."""
    if context.user_data.get("supplier_stock_source_iek_field"):
        return supplier_stock_handle_source_iek_field_input(update, context)
    if context.user_data.get("supplier_stock_resource_field"):
        return supplier_stock_handle_resource_field_input(update, context)
    if context.user_data.get("supplier_stock_resource_add"):
        return supplier_stock_handle_resource_input(update, context)
    if context.user_data.get("supplier_stock_ftp_field"):
        return supplier_stock_handle_ftp_input(update, context)
    if context.user_data.get("supplier_stock_source_field"):
        return supplier_stock_handle_source_field_input(update, context)
    if context.user_data.get("supplier_stock_mail_source_field"):
        return supplier_stock_handle_mail_source_field_input(update, context)
    if context.user_data.get("supplier_stock_processing_field"):
        return supplier_stock_handle_processing_input(update, context)
    if context.user_data.get("supplier_stock_edit"):
        return supplier_stock_handle_edit_input(update, context)
    if context.user_data.get("supplier_stock_processing_add") or context.user_data.get(
        "supplier_stock_processing_edit"
    ):
        return supplier_stock_handle_processing_input(update, context)
    if context.user_data.get("supplier_stock_mail_edit"):
        return supplier_stock_handle_mail_edit_input(update, context)
    if context.user_data.get("supplier_stock_mail_edit_source"):
        return supplier_stock_handle_mail_source_edit_input(update, context)
    if context.user_data.get("supplier_stock_mail_add_source"):
        return supplier_stock_handle_mail_source_input(update, context)
    if context.user_data.get("supplier_stock_edit_source"):
        return supplier_stock_handle_source_edit_input(update, context)
    if context.user_data.get("supplier_stock_add_source"):
        return supplier_stock_handle_source_input(update, context)
    return None


def _supplier_stock_remember_prompt_message(context, query):
    """Запомнить сообщение с запросом ввода параметра."""
    if not query or not query.message:
        return
    context.user_data["supplier_stock_prompt_message_id"] = query.message.message_id
    context.user_data["supplier_stock_prompt_chat_id"] = query.message.chat_id


def _supplier_stock_close_prompt_message(context):
    """Удалить сообщение с запросом ввода параметра."""
    message_id = context.user_data.pop("supplier_stock_prompt_message_id", None)
    chat_id = context.user_data.pop("supplier_stock_prompt_chat_id", None)
    if not message_id or not chat_id:
        return
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


def supplier_stock_handle_edit_input(update, context):
    """Обработка ввода для изменения настроек остатков поставщиков."""
    field = context.user_data.get("supplier_stock_edit")
    if not field:
        return None

    message = update.message
    if not message or not message.text:
        debug_logger("⚠️ supplier_stock_handle_edit_input: получено пустое сообщение.")
        return None

    user_input = message.text.strip()
    config = get_supplier_stock_config()

    if field == "temp_dir":
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config["download"]["temp_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_edit", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Временный каталог обновлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_download")]]
            ),
        )
        return None

    if field == "schedule_time":
        schedule_times = parse_supplier_stock_schedule_times(user_input)
        if not schedule_times:
            update.message.reply_text(
                "❌ Неверный формат времени. Используйте HH:MM и разделители: пробел, запятая или ;"
            )
            return None
        config["download"]["schedule"]["time"] = ", ".join(schedule_times)
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_edit", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Время расписания обновлено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_schedule")]]
            ),
        )
        return None

    if field == "archive_cleanup_days":
        try:
            cleanup_days = int(user_input)
        except ValueError:
            update.message.reply_text("❌ Введите целое число дней (0 — отключить).")
            return None
        if cleanup_days < 0:
            update.message.reply_text("❌ Период не может быть отрицательным.")
            return None
        config["archive_cleanup_days"] = cleanup_days
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_edit", None)
        back_callback = context.user_data.pop(
            "supplier_stock_archive_cleanup_back", "supplier_stock_download"
        )
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Период очистки архива обновлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
            ),
        )
        return None

    if field == "report_period_days":
        try:
            period_days = int(user_input)
        except ValueError:
            update.message.reply_text("❌ Введите целое число дней (минимум 1).")
            return None
        if period_days < 1:
            update.message.reply_text("❌ Период должен быть минимум 1 день.")
            return None
        config.setdefault("reporting", {})["period_days"] = period_days
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_edit", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Период отчётов обновлён.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_supplier_stock")]]
            ),
        )
        return None

    if field == "archive_dir":
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config["download"]["archive_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_edit", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Каталог архива обновлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_download")]]
            ),
        )
        return None

    return None


def supplier_stock_handle_mail_edit_input(update, context):
    """Обработка ввода для общих настроек почты остатков."""
    field = context.user_data.get("supplier_stock_mail_edit")
    if not field:
        return None

    user_input = update.message.text.strip()
    config = get_supplier_stock_config()

    if field == "temp_dir":
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config["mail"]["temp_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_mail_edit", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Временный каталог обновлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail")]]
            ),
        )
        return None

    if field == "archive_dir":
        if not user_input:
            update.message.reply_text("❌ Путь не может быть пустым. Попробуйте снова:")
            return None
        config["mail"]["archive_dir"] = user_input
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_mail_edit", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Каталог архива обновлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail")]]
            ),
        )
        return None

    return None


def supplier_stock_start_mail_source_wizard(update, context):
    """Запуск мастера добавления правила вложений почты."""
    query = update.callback_query
    query.answer()

    context.user_data["supplier_stock_mail_source_stage"] = "name"
    context.user_data["supplier_stock_mail_source_data"] = {}
    context.user_data["supplier_stock_mail_add_source"] = True

    query.edit_message_text(
        "➕ *Новое правило вложений*\n\nВведите название правила:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_mail_sources")]]
        ),
    )


def supplier_stock_start_mail_edit_wizard(update, context, source_id: str):
    """Запуск мастера редактирования правила вложений почты."""
    query = update.callback_query
    query.answer()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        query.edit_message_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return

    context.user_data["supplier_stock_mail_edit_source"] = True
    context.user_data["supplier_stock_mail_edit_source_stage"] = "name"
    context.user_data["supplier_stock_mail_edit_source_id"] = source_id

    query.edit_message_text(
        f"✏️ *Редактирование правила*\n\n"
        f"Текущее имя: `{_escape_pattern_text(source.get('name'))}`\n"
        "Введите новое имя (или '-' чтобы оставить текущее):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_mail_sources")]]
        ),
    )


def supplier_stock_handle_mail_source_input(update, context):
    """Обработка ввода в мастере добавления правила вложений."""
    stage = context.user_data.get("supplier_stock_mail_source_stage")
    source_data = context.user_data.get("supplier_stock_mail_source_data", {})
    user_input = update.message.text.strip()

    if stage == "name":
        if not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        source_data["name"] = user_input
        source_data["id"] = _slugify_supplier_source_id(user_input)
        context.user_data["supplier_stock_mail_source_stage"] = "sender"
        context.user_data["supplier_stock_mail_source_data"] = source_data
        update.message.reply_text(
            "Введите regex или адрес отправителя (например: sender@example.com) "
            "или '-' чтобы принимать любые письма:"
        )
        return None

    if stage == "sender":
        if user_input not in ("-", ""):
            source_data["sender_pattern"] = user_input
        context.user_data["supplier_stock_mail_source_stage"] = "subject"
        context.user_data["supplier_stock_mail_source_data"] = source_data
        update.message.reply_text(
            "Введите regex для темы письма или '-' чтобы принимать любую тему:"
        )
        return None

    if stage == "subject":
        if user_input not in ("-", ""):
            source_data["subject_pattern"] = user_input
        context.user_data["supplier_stock_mail_source_stage"] = "mime"
        context.user_data["supplier_stock_mail_source_data"] = source_data
        update.message.reply_text(
            "Введите MIME-фильтр (например: application/vnd.ms-excel) "
            "или '-' чтобы использовать application/.*:"
        )
        return None

    if stage == "mime":
        if user_input not in ("-", ""):
            source_data["mime_pattern"] = user_input
        context.user_data["supplier_stock_mail_source_stage"] = "filename"
        context.user_data["supplier_stock_mail_source_data"] = source_data
        update.message.reply_text(
            "Введите regex для имени вложения или '-' чтобы принимать любые файлы:"
        )
        return None

    if stage == "filename":
        if user_input not in ("-", ""):
            source_data["filename_pattern"] = user_input
        context.user_data["supplier_stock_mail_source_stage"] = "expected"
        context.user_data["supplier_stock_mail_source_data"] = source_data
        update.message.reply_text("Введите количество ожидаемых вложений (например: 1 или 2):")
        return None

    if stage == "expected":
        expected = _parse_expected_attachments(user_input)
        if expected is None:
            update.message.reply_text("❌ Введите целое число больше 0.")
            return None
        source_data["expected_attachments"] = expected
        context.user_data["supplier_stock_mail_source_stage"] = "output"
        context.user_data["supplier_stock_mail_source_data"] = source_data
        update.message.reply_text(
            "Введите шаблон имени выходного файла "
            "(например: supplier_{index}_orig.xls, доступны {index}, {name}):"
        )
        return None

    if stage == "output":
        if not user_input:
            update.message.reply_text("❌ Шаблон не может быть пустым. Попробуйте снова:")
            return None
        source_data["output_template"] = user_input
        source_data.setdefault("enabled", True)
        source_data.setdefault("unpack_archive", False)

        config = get_supplier_stock_config()
        sources = config["mail"].get("sources", [])
        source_data["id"] = _unique_supplier_source_id(source_data.get("id", "source"), sources)
        sources.append(source_data)
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop("supplier_stock_mail_add_source", None)
        context.user_data.pop("supplier_stock_mail_source_stage", None)
        context.user_data.pop("supplier_stock_mail_source_data", None)

        update.message.reply_text(
            "✅ Правило добавлено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None


def supplier_stock_handle_mail_source_edit_input(update, context):
    """Обработка ввода при редактировании правила вложений."""
    stage = context.user_data.get("supplier_stock_mail_edit_source_stage")
    source_id = context.user_data.get("supplier_stock_mail_edit_source_id")
    user_input = update.message.text.strip()

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return None

    if stage == "name":
        if user_input and user_input not in ("-",):
            source["name"] = user_input
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data["supplier_stock_mail_edit_source_stage"] = "sender"
        current_sender = source.get("sender_pattern") or "-"
        update.message.reply_text(
            "Введите regex/адрес отправителя, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_sender}"
        )
        return None

    if stage == "sender":
        if user_input.lower() in ("none", "нет"):
            source.pop("sender_pattern", None)
        elif user_input not in ("-",):
            source["sender_pattern"] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data["supplier_stock_mail_edit_source_stage"] = "subject"
        current_subject = source.get("subject_pattern") or "-"
        update.message.reply_text(
            "Введите regex для темы письма, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_subject}"
        )
        return None

    if stage == "subject":
        if user_input.lower() in ("none", "нет"):
            source.pop("subject_pattern", None)
        elif user_input not in ("-",):
            source["subject_pattern"] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data["supplier_stock_mail_edit_source_stage"] = "mime"
        current_mime = source.get("mime_pattern") or "-"
        update.message.reply_text(
            "Введите MIME-фильтр, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_mime}"
        )
        return None

    if stage == "mime":
        if user_input.lower() in ("none", "нет"):
            source.pop("mime_pattern", None)
        elif user_input not in ("-",):
            source["mime_pattern"] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data["supplier_stock_mail_edit_source_stage"] = "filename"
        current_filename = source.get("filename_pattern") or "-"
        update.message.reply_text(
            "Введите regex для имени вложения, '-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_filename}"
        )
        return None

    if stage == "filename":
        if user_input.lower() in ("none", "нет"):
            source.pop("filename_pattern", None)
        elif user_input not in ("-",):
            source["filename_pattern"] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data["supplier_stock_mail_edit_source_stage"] = "expected"
        current_expected = source.get("expected_attachments", 1)
        update.message.reply_text(
            "Введите количество ожидаемых вложений, '-' чтобы оставить текущее.\n"
            f"Текущее значение: {current_expected}"
        )
        return None

    if stage == "expected":
        if user_input not in ("-",):
            expected = _parse_expected_attachments(user_input)
            if expected is None:
                update.message.reply_text("❌ Введите целое число больше 0 или '-'.")
                return None
            source["expected_attachments"] = expected
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data["supplier_stock_mail_edit_source_stage"] = "output"
        current_output = source.get("output_template") or "-"
        update.message.reply_text(
            "Введите шаблон имени выходного файла, '-' чтобы оставить текущее.\n"
            f"Текущее значение: {current_output}"
        )
        return None

    if stage == "output":
        if user_input and user_input not in ("-",):
            source["output_template"] = user_input
        config["mail"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop("supplier_stock_mail_edit_source", None)
        context.user_data.pop("supplier_stock_mail_edit_source_stage", None)
        context.user_data.pop("supplier_stock_mail_edit_source_id", None)

        update.message.reply_text(
            "✅ Правило обновлено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг редактирования. Попробуйте снова.")
    return None


def supplier_stock_handle_source_field_input(update, context):
    """Обработка ввода при редактировании отдельного поля источника."""
    field = context.user_data.get("supplier_stock_source_field")
    source_id = context.user_data.get("supplier_stock_source_field_id")
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return None

    if field == "name":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        else:
            source["name"] = user_input
    elif field == "url":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ URL не может быть пустым. Попробуйте снова:")
            return None
        else:
            source["url"] = user_input
    elif field == "discover":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("discover", None)
        else:
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | regex | prefix, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source["discover"] = discover
    elif field == "vars":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("vars", None)
        else:
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text(
                    "❌ Формат должен быть key=value, разделители запятая/новая строка."
                )
                return None
            source["vars"] = vars_map
    elif field == "output_name":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
            return None
        else:
            source["output_name"] = user_input
    elif field == "auth":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("auth", None)
        else:
            if ":" not in user_input:
                update.message.reply_text(
                    "❌ Формат должен быть login:password или 'none'. Попробуйте снова:"
                )
                return None
            username, password = user_input.split(":", 1)
            source["auth"] = {"username": username, "password": password}
    elif field == "pre_request":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("pre_request", None)
        else:
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | данные, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source["pre_request"] = pre_request
    elif field == "options":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("include_headers", None)
            source.pop("append", None)
        else:
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "❌ Формат должен быть списком через запятую (headers, append), '-' или 'none'."
                )
                return None
            source.update(options)
    elif field == "processing_mode":
        if user_input in ("-", ""):
            pass
        else:
            mode = _normalize_supplier_processing_mode(user_input)
            if not mode:
                update.message.reply_text("❌ Допустимые значения: table, iek_json.")
                return None
            source["processing_mode"] = mode
            if mode == "iek_json":
                source.setdefault("iek_json", {})
    elif field == "upload_subdir":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("upload_subdir", None)
        else:
            source["upload_subdir"] = user_input
    elif field == "individual_path":
        individual_dir = source.setdefault("individual_directory", {})
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            individual_dir.pop("unc_path", None)
        else:
            individual_dir["unc_path"] = user_input
    elif field == "individual_login":
        individual_dir = source.setdefault("individual_directory", {})
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            individual_dir.pop("login", None)
        else:
            individual_dir["login"] = user_input
    elif field == "individual_password":
        individual_dir = source.setdefault("individual_directory", {})
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            individual_dir.pop("password", None)
        else:
            individual_dir["password"] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["download"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop("supplier_stock_source_field", None)
    context.user_data.pop("supplier_stock_source_field_id", None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Назад", callback_data=f"supplier_stock_source_settings|{source_id}"
                    )
                ]
            ]
        ),
    )
    return None


def supplier_stock_handle_source_iek_field_input(update, context):
    """Обработка ввода при редактировании параметров IEK JSON."""
    field = context.user_data.get("supplier_stock_source_iek_field")
    source_id = context.user_data.get("supplier_stock_source_iek_field_id")
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return None

    iek_settings = source.setdefault("iek_json", {})

    if user_input in ("-", ""):
        config["download"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data.pop("supplier_stock_source_iek_field", None)
        context.user_data.pop("supplier_stock_source_iek_field_id", None)
        _supplier_stock_close_prompt_message(context)
        update.message.reply_text(
            "✅ Настройка обновлена.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↩️ Назад",
                            callback_data=f"supplier_stock_source_iek_settings|{source_id}",
                        )
                    ],
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
                ]
            ),
        )
        return None
    if field == "stores":
        if user_input.lower() in ("none", "нет"):
            iek_settings["stores"] = {}
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text(
                    "❌ Формат должен быть key=uuid через запятую/новую строку."
                )
                return None
            iek_settings["stores"] = parsed
    elif field == "msk_stores":
        if user_input.lower() in ("none", "нет"):
            iek_settings["msk_stores"] = []
        else:
            if not user_input:
                update.message.reply_text("❌ Список не может быть пустым.")
                return None
            iek_settings["msk_stores"] = [
                item.strip() for item in re.split(r"[,\n]+", user_input) if item.strip()
            ]
    elif field == "nsk_store":
        if user_input.lower() in ("none", "нет"):
            iek_settings["nsk_store"] = ""
        else:
            if not user_input:
                update.message.reply_text("❌ Значение не может быть пустым.")
                return None
            iek_settings["nsk_store"] = user_input
    elif field == "orc_stores":
        if user_input.lower() in ("none", "нет"):
            iek_settings["orc_stores"] = []
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text(
                    "❌ Формат должен быть key=stor через запятую/новую строку."
                )
                return None
            iek_settings["orc_stores"] = [
                {"key": key, "stor": value} for key, value in parsed.items()
            ]
    elif field == "prefix":
        iek_settings["prefix"] = "" if user_input.lower() in ("none", "нет") else user_input
    elif field == "outputs":
        if user_input.lower() in ("none", "нет"):
            iek_settings["outputs"] = {}
        else:
            parsed = _parse_supplier_vars(user_input)
            if parsed is None:
                update.message.reply_text(
                    "❌ Формат должен быть orig=..., msk=..., nsk=..., orc=... через запятую."
                )
                return None
            iek_settings["outputs"] = parsed
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    source["iek_json"] = iek_settings
    config["download"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop("supplier_stock_source_iek_field", None)
    context.user_data.pop("supplier_stock_source_iek_field_id", None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Назад", callback_data=f"supplier_stock_source_iek_settings|{source_id}"
                    )
                ],
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
            ]
        ),
    )
    return None


def supplier_stock_handle_mail_source_field_input(update, context):
    """Обработка ввода при редактировании отдельного поля правила вложений."""
    field = context.user_data.get("supplier_stock_mail_source_field")
    source_id = context.user_data.get("supplier_stock_mail_source_field_id")
    user_input = (update.message.text or "").strip()

    if not field or not source_id:
        return None

    config = get_supplier_stock_config()
    sources = config.get("mail", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text(
            "❌ Правило не найдено.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_mail_sources")]]
            ),
        )
        return None

    if field == "name":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        else:
            source["name"] = user_input
    elif field == "sender":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("sender_pattern", None)
        else:
            source["sender_pattern"] = user_input
    elif field == "subject":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("subject_pattern", None)
        else:
            source["subject_pattern"] = user_input
    elif field == "mime":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("mime_pattern", None)
        else:
            source["mime_pattern"] = user_input
    elif field == "filename":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("filename_pattern", None)
        else:
            source["filename_pattern"] = user_input
    elif field == "expected":
        if user_input in ("-", ""):
            pass
        else:
            expected = _parse_expected_attachments(user_input)
            if expected is None:
                update.message.reply_text("❌ Введите целое число больше 0.")
                return None
            source["expected_attachments"] = expected
    elif field == "output":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ Шаблон не может быть пустым. Попробуйте снова:")
            return None
        else:
            source["output_template"] = user_input
    elif field == "upload_subdir":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            source.pop("upload_subdir", None)
        else:
            source["upload_subdir"] = user_input
    elif field == "individual_path":
        individual_dir = source.setdefault("individual_directory", {})
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            individual_dir.pop("unc_path", None)
        else:
            individual_dir["unc_path"] = user_input
    elif field == "individual_login":
        individual_dir = source.setdefault("individual_directory", {})
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            individual_dir.pop("login", None)
        else:
            individual_dir["login"] = user_input
    elif field == "individual_password":
        individual_dir = source.setdefault("individual_directory", {})
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            individual_dir.pop("password", None)
        else:
            individual_dir["password"] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["mail"]["sources"] = sources
    save_supplier_stock_config(config)

    context.user_data.pop("supplier_stock_mail_source_field", None)
    context.user_data.pop("supplier_stock_mail_source_field_id", None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Назад", callback_data=f"supplier_stock_mail_source_settings|{source_id}"
                    )
                ]
            ]
        ),
    )
    return None


def supplier_stock_handle_resource_input(update, context):
    """Обработка ввода в мастере добавления ресурса выгрузки."""
    stage = context.user_data.get("supplier_stock_resource_stage")
    resource_data = context.user_data.get("supplier_stock_resource_data", {})
    user_input = (update.message.text or "").strip()

    if stage == "name":
        if not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        resource_data["name"] = user_input
        resource_data["id"] = _slugify_supplier_source_id(user_input)
        context.user_data["supplier_stock_resource_stage"] = "unc_path"
        context.user_data["supplier_stock_resource_data"] = resource_data
        update.message.reply_text("Введите UNC путь корневого каталога:")
        return None

    if stage == "unc_path":
        if not user_input:
            update.message.reply_text("❌ UNC путь не может быть пустым. Попробуйте снова:")
            return None
        resource_data["unc_path"] = user_input
        context.user_data["supplier_stock_resource_stage"] = "login"
        context.user_data["supplier_stock_resource_data"] = resource_data
        update.message.reply_text("Введите логин ресурса (или '-' чтобы пропустить):")
        return None

    if stage == "login":
        if user_input not in ("-", ""):
            resource_data["login"] = user_input
        context.user_data["supplier_stock_resource_stage"] = "password"
        context.user_data["supplier_stock_resource_data"] = resource_data
        update.message.reply_text("Введите пароль ресурса (или '-' чтобы пропустить):")
        return None

    if stage == "password":
        if user_input not in ("-", ""):
            resource_data["password"] = user_input
        resource_data.setdefault("enabled", True)
        config = get_supplier_stock_config()
        resources = config.get("resources", [])
        resource_data["id"] = _unique_supplier_source_id(
            resource_data.get("id", "resource"), resources
        )
        resources.append(resource_data)
        config["resources"] = resources
        save_supplier_stock_config(config)

        context.user_data.pop("supplier_stock_resource_add", None)
        context.user_data.pop("supplier_stock_resource_stage", None)
        context.user_data.pop("supplier_stock_resource_data", None)

        update.message.reply_text(
            "✅ Ресурс добавлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_resources")]]
            ),
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None


def supplier_stock_handle_resource_field_input(update, context):
    """Обработка ввода при редактировании ресурса выгрузки."""
    field = context.user_data.get("supplier_stock_resource_field")
    resource_id = context.user_data.get("supplier_stock_resource_field_id")
    user_input = (update.message.text or "").strip()

    if not field or not resource_id:
        return None

    config = get_supplier_stock_config()
    resources = config.get("resources", [])
    resource = next((item for item in resources if str(item.get("id")) == resource_id), None)

    if not resource:
        update.message.reply_text(
            "❌ Ресурс не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_resources")]]
            ),
        )
        return None

    if field == "name":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        else:
            resource["name"] = user_input
    elif field == "unc_path":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ UNC путь не может быть пустым. Попробуйте снова:")
            return None
        else:
            resource["unc_path"] = user_input
    elif field == "login":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            resource.pop("login", None)
        else:
            resource["login"] = user_input
    elif field == "password":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            resource.pop("password", None)
        else:
            resource["password"] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["resources"] = resources
    save_supplier_stock_config(config)

    context.user_data.pop("supplier_stock_resource_field", None)
    context.user_data.pop("supplier_stock_resource_field_id", None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "↩️ Назад", callback_data=f"supplier_stock_resource_settings|{resource_id}"
                    )
                ]
            ]
        ),
    )
    return None


def supplier_stock_handle_ftp_input(update, context):
    """Обработка ввода для настроек FTP ОРК."""
    field = context.user_data.get("supplier_stock_ftp_field")
    user_input = (update.message.text or "").strip()

    if not field:
        return None

    config = get_supplier_stock_config()
    ftp_settings = config.get("ftp_ork", {})

    if field == "host":
        if user_input in ("-", ""):
            pass
        elif not user_input:
            update.message.reply_text("❌ HOST FTP не может быть пустым. Попробуйте снова:")
            return None
        else:
            ftp_settings["host"] = user_input
    elif field == "login":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            ftp_settings.pop("login", None)
        else:
            ftp_settings["login"] = user_input
    elif field == "password":
        if user_input in ("-", ""):
            pass
        elif user_input.lower() in ("none", "нет"):
            ftp_settings.pop("password", None)
        else:
            ftp_settings["password"] = user_input
    else:
        update.message.reply_text("❌ Не удалось определить поле настройки.")
        return None

    config["ftp_ork"] = ftp_settings
    save_supplier_stock_config(config)

    context.user_data.pop("supplier_stock_ftp_field", None)
    _supplier_stock_close_prompt_message(context)

    update.message.reply_text(
        "✅ Настройка обновлена.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_ftp")]]
        ),
    )
    return None


def supplier_stock_handle_source_input(update, context):
    """Обработка ввода в мастере добавления источника."""
    stage = context.user_data.get("supplier_stock_source_stage")
    source_data = context.user_data.get("supplier_stock_source_data", {})
    user_input = update.message.text.strip()

    if stage == "name":
        if not user_input:
            update.message.reply_text("❌ Название не может быть пустым. Попробуйте снова:")
            return None
        source_data["name"] = user_input
        source_data["id"] = _slugify_supplier_source_id(user_input)
        context.user_data["supplier_stock_source_stage"] = "url"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text(
            "Введите URL для скачивания. "
            "Можно использовать переменные формата подстановки вида {abc} "
            "для дальнейшей подмены значений."
        )
        return None

    if stage == "url":
        if not user_input:
            update.message.reply_text("❌ URL не может быть пустым. Попробуйте снова:")
            return None
        source_data["url"] = user_input
        context.user_data["supplier_stock_source_stage"] = "discover"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text(
            "Если нужно искать ссылку на странице, введите URL, regex и префикс через '|'.\n"
            "Пример: http://site/page | ostatki_msk_ot_[^\"']*\\.xls | http://site/f/\n"
            "Введите '-' если не нужно:"
        )
        return None

    if stage == "discover":
        if user_input not in ("-", ""):
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | regex | prefix (префикс можно оставить пустым)."
                )
                return None
            source_data["discover"] = discover

        context.user_data["supplier_stock_source_stage"] = "vars"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text(
            "Введите ранее указанные переменные подстановки в формате key=value через запятую "
            "(пример: abc=DKC_Maga_Del_1200_$(date '%d.%m.%Y').zip). "
            "Введите '-' если не нужно:"
        )
        return None

    if stage == "vars":
        if user_input not in ("-", ""):
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text(
                    "❌ Формат должен быть key=value, разделители запятая/новая строка."
                )
                return None
            source_data["vars"] = vars_map

        context.user_data["supplier_stock_source_stage"] = "output_name"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text("Введите имя файла назначения (например: dkc_orig.zip):")
        return None

    if stage == "output_name":
        if not user_input:
            update.message.reply_text("❌ Имя файла не может быть пустым. Попробуйте снова:")
            return None
        source_data["output_name"] = user_input
        context.user_data["supplier_stock_source_stage"] = "auth"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text(
            "Введите логин и пароль через двоеточие (login:password) "
            "или '-' чтобы пропустить и сохранить:"
        )
        return None

    if stage == "auth":
        if user_input not in ("-", "нет", "Нет", "none", "None"):
            if ":" not in user_input:
                update.message.reply_text(
                    "❌ Формат должен быть login:password или '-'. Попробуйте снова:"
                )
                return None
            username, password = user_input.split(":", 1)
            source_data["auth"] = {"username": username, "password": password}

        context.user_data["supplier_stock_source_stage"] = "pre_request"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text(
            "Если нужен предварительный POST-запрос для авторизации, "
            "введите URL и данные через '|'.\n"
            "Пример: http://www.owen.ru/dealers | login=...&password=...&iTask=login\n"
            "Введите '-' если не нужно:"
        )
        return None

    if stage == "pre_request":
        if user_input not in ("-", ""):
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | данные. Попробуйте снова или введите '-'."
                )
                return None
            source_data["pre_request"] = pre_request

        context.user_data["supplier_stock_source_stage"] = "options"
        context.user_data["supplier_stock_source_data"] = source_data
        update.message.reply_text(
            "Введите дополнительные параметры сохранения: headers (с заголовками), append (дописывать).\n"
            "Пример: headers, append\n"
            "Введите '-' если не нужно:"
        )
        return None

    if stage == "options":
        if user_input not in ("-", ""):
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "❌ Формат должен быть списком через запятую (headers, append)."
                )
                return None
            source_data.update(options)

        source_data.setdefault("method", "http")
        source_data.setdefault("enabled", True)
        source_data.setdefault("unpack_archive", False)

        config = get_supplier_stock_config()
        sources = config["download"].get("sources", [])
        source_data["id"] = _unique_supplier_source_id(source_data.get("id", "source"), sources)
        sources.append(source_data)
        config["download"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop("supplier_stock_add_source", None)
        context.user_data.pop("supplier_stock_source_stage", None)
        context.user_data.pop("supplier_stock_source_data", None)

        update.message.reply_text(
            "✅ Источник добавлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг мастера. Попробуйте снова.")
    return None


def supplier_stock_handle_source_edit_input(update, context):
    """Обработка ввода при редактировании источника остатков."""
    stage = context.user_data.get("supplier_stock_edit_source_stage")
    source_id = context.user_data.get("supplier_stock_edit_source_id")
    user_input = update.message.text.strip()

    config = get_supplier_stock_config()
    sources = config.get("download", {}).get("sources", [])
    source = next((item for item in sources if str(item.get("id")) == source_id), None)

    if not source:
        update.message.reply_text(
            "❌ Источник не найден.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return None

    if stage == "name":
        if user_input and user_input not in ("-",):
            source["name"] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data["supplier_stock_edit_source_stage"] = "url"
        update.message.reply_text(
            "Введите новый URL (или '-' чтобы оставить текущее). "
            "Можно использовать переменные формата подстановки вида {abc} "
            "для дальнейшей подмены значений:\n"
            f"{source.get('url')}"
        )
        return None

    if stage == "url":
        if user_input and user_input not in ("-",):
            source["url"] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data["supplier_stock_edit_source_stage"] = "discover"
        update.message.reply_text(
            "Введите параметры поиска ссылки на странице в формате URL | regex | prefix, "
            "'-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            "Пример: http://site/page | ostatki_msk_ot_[^\"']*\\.xls | http://site/f/"
        )
        return None

    if stage == "discover":
        if user_input.lower() in ("none", "нет"):
            source.pop("discover", None)
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        elif user_input not in ("-",):
            discover = _parse_supplier_discover(user_input)
            if discover is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | regex | prefix, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source["discover"] = discover
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)

        context.user_data["supplier_stock_edit_source_stage"] = "vars"
        update.message.reply_text(
            "Введите ранее указанные переменные подстановки в формате key=value через запятую "
            "(пример: abc=DKC_Maga_Del_1200_$(date '%d.%m.%Y').zip). "
            "'-' чтобы оставить текущее или 'none' чтобы очистить:"
        )
        return None

    if stage == "vars":
        if user_input.lower() in ("none", "нет"):
            source.pop("vars", None)
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        elif user_input not in ("-",):
            vars_map = _parse_supplier_vars(user_input)
            if vars_map is None:
                update.message.reply_text(
                    "❌ Формат должен быть key=value, разделители запятая/новая строка."
                )
                return None
            source["vars"] = vars_map
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)

        context.user_data["supplier_stock_edit_source_stage"] = "output_name"
        update.message.reply_text(
            f"Текущий файл назначения: {source.get('output_name')}\n"
            "Введите новое имя файла назначения (или '-' чтобы оставить текущее):"
        )
        return None

    if stage == "output_name":
        if user_input and user_input not in ("-",):
            source["output_name"] = user_input
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
        context.user_data["supplier_stock_edit_source_stage"] = "auth"
        update.message.reply_text(
            "Введите логин и пароль через двоеточие (login:password), "
            "'-' чтобы оставить текущее или 'none' чтобы очистить:"
        )
        return None

    if stage == "auth":
        if user_input.lower() in ("none", "нет"):
            source.pop("auth", None)
        elif user_input not in ("-",):
            if ":" not in user_input:
                update.message.reply_text(
                    "❌ Формат должен быть login:password, '-' или 'none'. Попробуйте снова:"
                )
                return None
            username, password = user_input.split(":", 1)
            source["auth"] = {"username": username, "password": password}

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)
        context.user_data["supplier_stock_edit_source_stage"] = "pre_request"
        current_pre = source.get("pre_request") or {}
        current_pre_url = current_pre.get("url", "-")
        current_pre_data = current_pre.get("data", "-")
        update.message.reply_text(
            "Введите предварительный POST-запрос для авторизации в формате URL | данные, "
            "'-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_pre_url} | {current_pre_data}"
        )
        return None

    if stage == "pre_request":
        if user_input.lower() in ("none", "нет"):
            source.pop("pre_request", None)
        elif user_input not in ("-",):
            pre_request = _parse_supplier_pre_request(user_input)
            if pre_request is None:
                update.message.reply_text(
                    "❌ Формат должен быть URL | данные, '-' или 'none'. Попробуйте снова:"
                )
                return None
            source["pre_request"] = pre_request

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data["supplier_stock_edit_source_stage"] = "options"
        current_options = []
        if source.get("include_headers"):
            current_options.append("headers")
        if source.get("append"):
            current_options.append("append")
        current_label = ", ".join(current_options) if current_options else "-"
        update.message.reply_text(
            "Введите дополнительные параметры сохранения: headers (с заголовками), append (дописывать). "
            "'-' чтобы оставить текущее или 'none' чтобы очистить.\n"
            f"Текущее значение: {current_label}"
        )
        return None

    if stage == "options":
        if user_input.lower() in ("none", "нет"):
            source.pop("include_headers", None)
            source.pop("append", None)
        elif user_input not in ("-",):
            options = _parse_supplier_options(user_input)
            if options is None:
                update.message.reply_text(
                    "❌ Формат должен быть списком через запятую (headers, append), '-' или 'none'."
                )
                return None
            source.update(options)

        config["download"]["sources"] = sources
        save_supplier_stock_config(config)

        context.user_data.pop("supplier_stock_edit_source", None)
        context.user_data.pop("supplier_stock_edit_source_stage", None)
        context.user_data.pop("supplier_stock_edit_source_id", None)

        update.message.reply_text(
            "✅ Источник обновлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Назад", callback_data="supplier_stock_sources")]]
            ),
        )
        return None

    update.message.reply_text("❌ Не удалось определить шаг редактирования. Попробуйте снова.")
    return None


def _slugify_supplier_source_id(value: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return raw.strip("_") or "source"


def _unique_supplier_source_id(source_id: str, sources: list[dict]) -> str:
    existing = {str(item.get("id")) for item in sources if item.get("id")}
    if source_id not in existing:
        return source_id
    index = 2
    while f"{source_id}_{index}" in existing:
        index += 1
    return f"{source_id}_{index}"


def _normalize_supplier_processing_mode(value: str) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    if lowered in ("table", "табличный", "таблица"):
        return "table"
    if lowered in ("iek_json", "iek", "json"):
        return "iek_json"
    return None


def _save_supplier_stock_processing_rule(
    context,
    data: dict,
    edit_id: str | None = None,
    keep_context: bool = False,
) -> None:
    config = get_supplier_stock_config()
    rules = config.get("processing", {}).get("rules", [])
    if edit_id:
        updated = False
        for index, rule in enumerate(rules):
            if str(rule.get("id")) == str(edit_id):
                data["id"] = edit_id
                data.setdefault("enabled", rule.get("enabled", True))
                data.setdefault("active", rule.get("active", False))
                rules[index] = data
                updated = True
                break
        if not updated:
            data["id"] = edit_id
            data.setdefault("enabled", True)
            data.setdefault("active", False)
            rules.append(data)
    else:
        data.setdefault("enabled", True)
        data.setdefault("active", False)
        data["id"] = _unique_supplier_source_id(data.get("id", "rule"), rules)
        rules.append(data)
    config.setdefault("processing", {})["rules"] = rules
    save_supplier_stock_config(config)
    if not keep_context:
        context.user_data.pop("supplier_stock_processing_add", None)
        context.user_data.pop("supplier_stock_processing_edit", None)
        context.user_data.pop("supplier_stock_processing_stage", None)
        context.user_data.pop("supplier_stock_processing_data", None)
        context.user_data.pop("supplier_stock_processing_edit_id", None)
        context.user_data.pop("supplier_stock_processing_variant_index", None)
        context.user_data.pop("supplier_stock_processing_data_columns_expected", None)
        context.user_data.pop("supplier_stock_processing_data_columns", None)
        context.user_data.pop("supplier_stock_processing_output_names_expected", None)
        context.user_data.pop("supplier_stock_processing_output_names", None)
        context.user_data.pop("supplier_stock_processing_current_variant", None)


def _supplier_stock_finish_variant(update, context, data: dict):
    variant = context.user_data.get("supplier_stock_processing_current_variant", {})
    data.setdefault("variants", []).append(variant)
    total = data.get("variants_count", 1)
    current_index = context.user_data.get("supplier_stock_processing_variant_index", 0) + 1
    if current_index < total:
        context.user_data["supplier_stock_processing_variant_index"] = current_index
        context.user_data["supplier_stock_processing_stage"] = "variant_article_col"
        context.user_data.pop("supplier_stock_processing_data_columns_expected", None)
        context.user_data.pop("supplier_stock_processing_data_columns", None)
        context.user_data.pop("supplier_stock_processing_output_names_expected", None)
        context.user_data.pop("supplier_stock_processing_output_names", None)
        context.user_data.pop("supplier_stock_processing_current_variant", None)
        update.message.reply_text(
            f"Настройка варианта {current_index + 1} из {total}.\n"
            "Введите номер колонки с артикулом:"
        )
        return None

    edit_id = data.get("id") if context.user_data.get("supplier_stock_processing_edit") else None
    _save_supplier_stock_processing_rule(context, data, edit_id=edit_id)
    back_callback = context.user_data.get(
        "supplier_stock_processing_back", "supplier_stock_processing"
    )
    update.message.reply_text(
        "✅ Правило обработки сохранено.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data=back_callback)]]
        ),
    )
    return None


def _parse_supplier_vars(raw_value: str) -> dict | None:
    if not raw_value:
        return {}
    parts = re.split(r"[,\n]+", raw_value)
    result = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            return None
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            return None
        result[key] = value
    return result


def _parse_supplier_pre_request(raw_value: str) -> dict | None:
    if not raw_value:
        return None
    if "|" in raw_value:
        url, data = raw_value.split("|", 1)
    elif "\n" in raw_value:
        url, data = raw_value.split("\n", 1)
    else:
        return None
    url = url.strip()
    data = data.strip()
    if not url:
        return None
    if data in ("-", ""):
        data = ""
    return {"url": url, "data": data}


def _parse_supplier_discover(raw_value: str) -> dict | None:
    if not raw_value:
        return None
    parts = [part.strip() for part in raw_value.split("|")]
    if len(parts) < 2:
        return None
    url = parts[0]
    pattern = parts[1]
    prefix = parts[2] if len(parts) > 2 else ""
    if not url or not pattern:
        return None
    return {"url": url, "pattern": pattern, "prefix": prefix}


def _parse_supplier_options(raw_value: str) -> dict | None:
    if not raw_value:
        return None
    parts = [part.strip().lower() for part in re.split(r"[,\n]+", raw_value) if part.strip()]
    if not parts:
        return None
    options = {}
    for part in parts:
        if part in ("headers", "header"):
            options["include_headers"] = True
        elif part in ("append", "дописать"):
            options["append"] = True
        else:
            return None
    return options


def show_stock_load_patterns_menu(update, context):
    """Показать паттерны для загрузки остатков."""
    context.user_data["patterns_filter"] = "stock_load"
    context.user_data["patterns_back"] = "settings_ext_stock_load"
    context.user_data["patterns_add"] = "add_stock_pattern"
    context.user_data["patterns_title"] = "📦 *Паттерны загрузки остатков*"
    view_patterns_handler(update, context)


def show_stock_pattern_type_menu(update, context):
    """Показать выбор типа паттерна для остатков."""
    query = update.callback_query
    query.answer()

    message = "📦 *Добавление паттерна для загрузки остатков*\n\n" "Выберите, что нужно настроить:"

    keyboard = [
        [InlineKeyboardButton("🧾 Тема письма", callback_data="stock_pattern_select_subject")],
        [InlineKeyboardButton("🗂️ Источник отчета", callback_data="stock_pattern_select_source")],
        [InlineKeyboardButton("📎 Имя вложения", callback_data="stock_pattern_select_attachment")],
        [InlineKeyboardButton("📄 Строка файла", callback_data="stock_pattern_select_file_entry")],
        [
            InlineKeyboardButton(
                "✅ Успешная загрузка", callback_data="stock_pattern_select_success"
            )
        ],
        [
            InlineKeyboardButton(
                "🙈 Игнорировать строки", callback_data="stock_pattern_select_ignore"
            )
        ],
        [InlineKeyboardButton("❌ Ошибка загрузки", callback_data="stock_pattern_select_failure")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_patterns_stock"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def stock_pattern_select_handler(update, context, pattern_type: str):
    """Запустить мастер для выбранного типа паттерна остатков."""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "stock_input"
    if pattern_type == "subject":
        context.user_data["backup_pattern_mode"] = "stock_subject_wizard"
    elif pattern_type == "source":
        context.user_data["backup_pattern_mode"] = "stock_source_wizard"
    else:
        context.user_data["backup_pattern_mode"] = "stock_log_wizard"
    context.user_data["backup_pattern_stock_type"] = pattern_type
    context.user_data.pop("backup_pattern_generated", None)
    context.user_data.pop("backup_pattern_source", None)
    context.user_data.pop("backup_pattern_stock_label", None)

    if pattern_type == "subject":
        prompt = (
            "🧙 *Мастер добавления темы*\n\n"
            "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
            "Фрагменты учитываются в указанном порядке.\n\n"
            "Пример:\n"
            "`Логи загрузки файлов в рабочую базу 07:38:14`"
        )
    elif pattern_type == "source":
        prompt = (
            "🧙 *Мастер добавления источника отчета*\n\n"
            "Введите название источника и тему письма через `|`.\n"
            "В теме можно использовать фрагменты через `;`/`,`.\n\n"
            "Пример:\n"
            "`Филиал Москва | Логи загрузки файлов в рабочую базу 07:38:14`"
        )
    elif pattern_type == "attachment":
        prompt = (
            "🧙 *Мастер добавления имени вложения*\n\n"
            "Введите имя файла или фрагменты через `;`/`,`.\n\n"
            "Пример:\n"
            "`LogiLogistam.txt`"
        )
    elif pattern_type == "file_entry":
        prompt = (
            "🧙 *Мастер добавления строки файла*\n\n"
            "Введите строку с названием поставщика и путем к файлу.\n\n"
            "Пример:\n"
            "`19.01.26 07:35:36: ЗЭТА  НСК  D:\\Obmen\\OCTATKu\\ЗЭТА\\Остатки ЗЭТА НСК.csv`"
        )
    elif pattern_type == "success":
        prompt = (
            "🧙 *Мастер добавления строки успеха*\n\n"
            "Введите строку с результатом успешной загрузки.\n\n"
            "Пример:\n"
            "`19.01.26 07:35:39: ***Остатки загружены!***   строк 348   07:35:39`"
        )
    elif pattern_type == "ignore":
        prompt = (
            "🧙 *Мастер добавления игнорируемой строки*\n\n"
            "Введите строку или обязательные фрагменты через `;`/`,`.\n"
            "Эти строки будут пропускаться при разборе.\n\n"
            "Пример:\n"
            "`Внимание! Ошибка в номенклатуре Артикул=`"
        )
    else:
        prompt = (
            "🧙 *Мастер добавления строки ошибки*\n\n"
            "Введите строку с ошибкой или обязательные фрагменты через `;`/`,`.\n\n"
            "Пример:\n"
            "`--- неудача!!! пустая загрузка`"
        )

    query.edit_message_text(
        prompt,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=context.user_data.get("patterns_back", "settings_backup"),
                    ),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def stock_pattern_retry_handler(update, context):
    """Повторить ввод для паттернов остатков."""
    query = update.callback_query
    query.answer()

    pattern_type = context.user_data.get("backup_pattern_stock_type", "subject")
    stock_pattern_select_handler(update, context, pattern_type)


def stock_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна остатков."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get("backup_pattern_generated")
    pattern_type = context.user_data.get("backup_pattern_stock_type")
    back_callback = context.user_data.get("patterns_back", "settings_backup")
    label = context.user_data.get("backup_pattern_stock_label")

    if not pattern or not pattern_type:
        query.edit_message_text(
            "❌ Паттерн не найден. Начните добавление заново.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("↩️ Назад", callback_data=back_callback)],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
                ]
            ),
        )
        return

    try:
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
            VALUES (?, ?, ?, 1)
            """,
            (pattern_type, pattern, "stock_load"),
        )
        conn.commit()

        source_label = context.user_data.get("backup_pattern_source", "мастер")
        label_text = f"Метка: *{label}*\n" if label else ""
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *stock_load*\n"
            f"Тип: *{pattern_type}*\n"
            f"{label_text}"
            f"Источник: *{source_label}*\n"
            f"Паттерн: `{pattern}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data=back_callback),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка сохранения: {e}")
    finally:
        context.user_data.pop("adding_backup_pattern", None)
        context.user_data.pop("backup_pattern_stage", None)
        context.user_data.pop("backup_pattern_category", None)
        context.user_data.pop("backup_pattern_type", None)
        context.user_data.pop("backup_pattern_subject", None)
        context.user_data.pop("backup_pattern_mode", None)
        context.user_data.pop("backup_pattern_generated", None)
        context.user_data.pop("backup_pattern_source", None)
        context.user_data.pop("backup_pattern_stock_type", None)
        context.user_data.pop("backup_pattern_stock_label", None)
