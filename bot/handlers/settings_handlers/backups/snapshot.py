"""
/bot/handlers/settings_handlers/backups/snapshot.py
Server Monitoring System v8.62.71
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
ZFS snapshot transfer settings: hosts toggle/delete, pattern menu/handlers. (PR7d).
Система мониторинга серверов
Версия: 8.62.71
Автор: Александр Суханов (c)
Лицензия: MIT
Выделено из bot/handlers/settings_handlers/_legacy.py. Имена сохранены —
фасад пакета settings_handlers через двусторонний re-export продолжает
их отдавать; внутренние ссылки в _legacy.py резолвятся через обратный
`from backups.snapshot import *` блок.
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

# PR7b: supplier_stock-функции вынесены в одноимённый модуль пакета;
# реэкспортируем их сюда же, чтобы внутренние ссылки в _legacy.py
# (например, settings_callback_handler) продолжали работать.
from bot.handlers.settings_handlers.supplier_stock import *  # noqa: F401, F403
from bot.handlers.settings_handlers.zfs import *  # noqa: F401, F403
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


def show_snapshot_hosts_menu(update, context):
    """Показать список и управление хостами передачи снэпшотов."""
    query = update.callback_query
    query.answer()

    hosts = settings_manager.get_setting("SNAPSHOT_TRANSFER_HOSTS", {}) or {}
    if not isinstance(hosts, dict):
        hosts = {}

    message = "📋 *Хосты передач снэпшотов*\n\n"
    if not hosts:
        message += "❌ Список хостов пуст."
    else:
        for idx, (host_name, host_cfg) in enumerate(sorted(hosts.items()), start=1):
            host_cfg = host_cfg if isinstance(host_cfg, dict) else {}
            enabled = bool(host_cfg.get("enabled", True))
            start_time = host_cfg.get("start_time", "не задано")
            message += f"{idx}. {'🟢' if enabled else '🔴'} `{host_name}` (старт: `{start_time}`)\n"

    keyboard = []
    for host_name, host_cfg in sorted(hosts.items()):
        host_cfg = host_cfg if isinstance(host_cfg, dict) else {}
        enabled = bool(host_cfg.get("enabled", True))
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {host_name}", callback_data=f"snapshot_host_edit|{host_name}"
                )
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔴 Выключить" if enabled else "🟢 Включить",
                    callback_data=f"snapshot_host_toggle|{host_name}",
                ),
                InlineKeyboardButton(
                    "🗑️ Удалить", callback_data=f"snapshot_host_delete|{host_name}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⏰ Время старта", callback_data=f"snapshot_host_start|{host_name}"
                )
            ]
        )

    keyboard.extend(
        [
            [InlineKeyboardButton("➕ Добавить хост", callback_data="snapshot_host_add")],
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="settings_snapshot_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )
    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _get_snapshot_hosts_config() -> dict:
    hosts = settings_manager.get_setting("SNAPSHOT_TRANSFER_HOSTS", {}) or {}
    return hosts if isinstance(hosts, dict) else {}


def _save_snapshot_hosts_config(hosts: dict) -> None:
    settings_manager.set_setting("SNAPSHOT_TRANSFER_HOSTS", hosts, "snapshot_transfer_hosts")


def toggle_snapshot_host_handler(update, context, host_name: str) -> None:
    hosts = _get_snapshot_hosts_config()
    if host_name in hosts:
        host_cfg = hosts.get(host_name) if isinstance(hosts.get(host_name), dict) else {}
        host_cfg["enabled"] = not bool(host_cfg.get("enabled", True))
        hosts[host_name] = host_cfg
        _save_snapshot_hosts_config(hosts)


def delete_snapshot_host_handler(update, context, host_name: str) -> None:
    hosts = _get_snapshot_hosts_config()
    if host_name in hosts:
        hosts.pop(host_name, None)
        _save_snapshot_hosts_config(hosts)


def _clear_snapshot_host_input_state(context) -> None:
    """Сбросить флаги текстового ввода для хостов/времени снэпшотов."""
    for key in (
        "adding_snapshot_host",
        "editing_snapshot_host_name",
        "editing_snapshot_start_time",
    ):
        context.user_data.pop(key, None)


def handle_snapshot_host_text_input(update, context) -> bool:
    text = (update.message.text or "").strip()
    if context.user_data.get("adding_snapshot_host"):
        if not text:
            update.message.reply_text("❌ Имя хоста не может быть пустым.")
            return True
        hosts = _get_snapshot_hosts_config()
        if text in hosts:
            update.message.reply_text("❌ Такой хост уже существует.")
            return True
        hosts[text] = {"enabled": True, "start_time": "03:00"}
        _save_snapshot_hosts_config(hosts)
        _clear_snapshot_host_input_state(context)
        update.message.reply_text("✅ Хост добавлен.")
        return True

    old_name = context.user_data.get("editing_snapshot_host_name")
    if old_name is not None:
        new_name = text
        hosts = _get_snapshot_hosts_config()
        if not new_name:
            update.message.reply_text("❌ Имя хоста не может быть пустым.")
            return True
        if old_name not in hosts:
            context.user_data.pop("editing_snapshot_host_name", None)
            update.message.reply_text("❌ Хост не найден.")
            return True
        if new_name != old_name and new_name in hosts:
            update.message.reply_text("❌ Такой хост уже существует.")
            return True
        hosts[new_name] = hosts.pop(old_name)
        _save_snapshot_hosts_config(hosts)
        _clear_snapshot_host_input_state(context)
        update.message.reply_text("✅ Имя хоста обновлено.")
        return True

    edit_start = context.user_data.get("editing_snapshot_start_time")
    if edit_start is not None:
        if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", text):
            update.message.reply_text("❌ Время должно быть в формате HH:MM.")
            return True
        hosts = _get_snapshot_hosts_config()
        if edit_start not in hosts:
            context.user_data.pop("editing_snapshot_start_time", None)
            update.message.reply_text("❌ Хост не найден.")
            return True
        host_cfg = hosts.get(edit_start) if isinstance(hosts.get(edit_start), dict) else {}
        host_cfg["start_time"] = text
        hosts[edit_start] = host_cfg
        _save_snapshot_hosts_config(hosts)
        _clear_snapshot_host_input_state(context)
        update.message.reply_text("✅ Время старта обновлено.")
        return True

    return False


def show_snapshot_transfer_settings(update, context):
    """Показать настройки мониторинга передач снэпшотов"""
    query = update.callback_query
    query.answer()

    patterns_data = settings_manager.get_backup_patterns()
    if isinstance(patterns_data, str):
        try:
            patterns_data = json.loads(patterns_data)
        except json.JSONDecodeError:
            patterns_data = {}

    snapshot_patterns: list[str] = []
    if isinstance(patterns_data, dict):
        raw_snapshot = patterns_data.get("snapshot_transfer", {})
        if isinstance(raw_snapshot, dict):
            snapshot_patterns = [p for p in raw_snapshot.get("subject", []) if isinstance(p, str)]
        elif isinstance(raw_snapshot, list):
            snapshot_patterns = [p for p in raw_snapshot if isinstance(p, str)]

    hosts = _get_snapshot_hosts_config()

    message = "📸 *Передачи снэпшотов*\n\n"
    message += "здесь отображаются последние результаты парсинга писем согласно паттернам\n\n"
    message += "📸 *Паттерны передач снэпшотов*\n\n"

    if snapshot_patterns:
        for idx, pattern in enumerate(snapshot_patterns, 1):
            message += f"{idx}. subject: `{escape_markdown(pattern)}`\n"
    else:
        message += "Паттерны пока не добавлены.\n"

    transfer_rows: dict[str, dict[str, str]] = {}
    recent_transfers: list[dict[str, str]] = []
    try:
        conn = sqlite3.connect(BACKUP_DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT host_name, status, received_at
            FROM snapshot_transfers
            ORDER BY datetime(received_at) DESC, id DESC
            """
        )
        for host_name, transfer_status, received_at in cursor.fetchall():
            host = str(host_name or "").strip()
            status = str(transfer_status or "").upper().strip()
            received = str(received_at or "").strip()
            if not host:
                continue

            if host not in transfer_rows:
                transfer_rows[host] = {
                    "status": status,
                    "received_at": received,
                }

            if len(recent_transfers) < 8:
                recent_transfers.append(
                    {
                        "host_name": host,
                        "status": status or "—",
                        "received_at": received or "—",
                    }
                )
    except Exception as exc:
        debug_logger(f"⚠️ Не удалось загрузить результаты передач снэпшотов: {exc}")
    finally:
        if "conn" in locals():
            conn.close()

    message += "\n📋 *Хосты передач снэпшотов*\n\n"
    if hosts:
        for idx, (host_name, cfg) in enumerate(hosts.items(), 1):
            enabled = cfg.get("enabled", True)
            start_time = cfg.get("start_time", "00:00")
            host_state = "🟢" if enabled else "🔴"

            latest = transfer_rows.get(host_name, {})
            latest_status = str(latest.get("status") or "—")
            if latest_status in {"SUCCESS", "SKIPPED"}:
                transfer_state = "🟢"
            elif latest_status in {"STARTED", "BUSY"}:
                transfer_state = "🟡"
            elif latest_status == "ERROR":
                transfer_state = "🔴"
            else:
                transfer_state = "⚪️"

            message += (
                f"{idx}. {host_state} `{escape_markdown(host_name)}` "
                f"(старт: `{escape_markdown(start_time)}`, "
                f"статус: {transfer_state} `{escape_markdown(latest_status)}`)\n"
            )
    else:
        message += "Список хостов пуст.\n"

    message += "\n🧾 *Последние распарсенные письма*\n\n"
    if recent_transfers:
        for idx, transfer in enumerate(recent_transfers, 1):
            status = transfer.get("status", "—")
            if status in {"SUCCESS", "SKIPPED"}:
                state = "🟢"
            elif status in {"STARTED", "BUSY"}:
                state = "🟡"
            elif status == "ERROR":
                state = "🔴"
            else:
                state = "⚪️"

            message += (
                f"{idx}. `{escape_markdown(transfer.get('host_name', '—'))}` — "
                f"{state} `{escape_markdown(status)}` "
                f"({escape_markdown(transfer.get('received_at', '—'))})\n"
            )
    else:
        message += "Пока нет данных о распарсенных письмах.\n"

    keyboard = [
        [InlineKeyboardButton("📋 Хосты", callback_data="settings_snapshot_hosts")],
        [InlineKeyboardButton("🔍 Паттерны", callback_data="settings_snapshot_patterns")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_snapshot_pattern_handler(update, context):
    """Добавить паттерн для передачи снэпшотов."""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "mail_input"
    context.user_data["backup_pattern_mode"] = "snapshot_transfer_wizard"
    context.user_data.pop("backup_pattern_generated", None)
    context.user_data.pop("backup_pattern_source", None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна передачи снэпшотов*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.\n\n"
        "Пример темы:\n"
        "`zfs sr-srv1 STARTED snapshot transfer`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton(
                        "❌ Отмена",
                        callback_data=context.user_data.get(
                            "patterns_back", "settings_snapshot_menu"
                        ),
                    ),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def snapshot_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна передачи снэпшотов."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get("backup_pattern_generated")
    back_callback = context.user_data.get("patterns_back", "settings_snapshot_menu")

    if not pattern:
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
            ("subject", pattern, "snapshot_transfer"),
        )
        conn.commit()

        source_label = context.user_data.get("backup_pattern_source", "мастер")
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *snapshot_transfer*\n"
            "Тип: *subject*\n"
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
