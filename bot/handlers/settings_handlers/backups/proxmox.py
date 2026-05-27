"""
/bot/handlers/settings_handlers/backups/proxmox.py
Server Monitoring System v8.62.63
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Proxmox vzdump backup settings: hosts list CRUD, pattern menu/handlers. (PR7d).
Система мониторинга серверов
Версия: 8.62.63
Автор: Александр Суханов (c)
Лицензия: MIT
Выделено из bot/handlers/settings_handlers/_legacy.py. Имена сохранены —
фасад пакета settings_handlers через двусторонний re-export продолжает
их отдавать; внутренние ссылки в _legacy.py резолвятся через обратный
`from backups.proxmox import *` блок.
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


def _normalize_proxmox_hosts(raw_hosts) -> dict:
    """Нормализует PROXMOX_HOSTS к словарю для всех входных форматов."""
    if isinstance(raw_hosts, dict):
        return raw_hosts
    if isinstance(raw_hosts, str):
        try:
            parsed_hosts = json.loads(raw_hosts)
        except Exception:
            try:
                parsed_hosts = ast.literal_eval(raw_hosts)
            except Exception:
                parsed_hosts = {}
        return parsed_hosts if isinstance(parsed_hosts, dict) else {}
    return {}


def _get_proxmox_hosts_for_settings() -> dict:
    """Получить PROXMOX_HOSTS с fallback, как в мобильном API настроек."""
    proxmox_hosts = _normalize_proxmox_hosts(settings_manager.get_setting("PROXMOX_HOSTS", {}))
    if proxmox_hosts:
        return proxmox_hosts

    try:
        from config.db_settings import PROXMOX_HOSTS as runtime_proxmox_hosts
    except Exception:
        runtime_proxmox_hosts = {}
    runtime_proxmox_hosts = _normalize_proxmox_hosts(runtime_proxmox_hosts)
    if runtime_proxmox_hosts:
        return runtime_proxmox_hosts

    try:
        from config.settings import PROXMOX_HOSTS as fallback_proxmox_hosts
    except Exception:
        fallback_proxmox_hosts = {}
    return _normalize_proxmox_hosts(fallback_proxmox_hosts)


def show_proxmox_backup_settings(update, context):
    """Показать настройки бэкапов Proxmox в разделе расширений"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()
    proxmox_count = len(proxmox_hosts)

    message = "🖥️ *Бэкапы Proxmox*\n\n" f"Хостов в списке: {proxmox_count}\n\n" "Выберите раздел:"

    keyboard = [
        [InlineKeyboardButton("📋 Хосты", callback_data="settings_backup_proxmox")],
        [InlineKeyboardButton("🔍 Паттерны", callback_data="settings_patterns_proxmox")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_extensions"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_proxmox_patterns_menu(update, context):
    """Показать паттерны для Proxmox"""
    back_callback = (
        context.user_data.pop("patterns_back_override", None) or "settings_ext_backup_proxmox"
    )
    context.user_data["patterns_filter"] = "proxmox"
    context.user_data["patterns_back"] = back_callback
    context.user_data["patterns_add"] = "add_proxmox_pattern"
    context.user_data["patterns_title"] = "🖥️ *Паттерны бэкапов Proxmox*"
    view_patterns_handler(update, context)


def show_backup_proxmox_settings(update, context):
    """Показать настройки бэкапов Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    message = "🖥️ *Бэкапы Proxmox*\n\n"
    if not proxmox_hosts:
        message += "❌ Хосты не настроены.\n\n"
    else:
        message += f"Хостов в списке: {len(proxmox_hosts)}\n\n"

    message += "Выберите действие:"

    keyboard = [
        [InlineKeyboardButton("📋 Список хостов", callback_data="settings_proxmox_list")],
        [InlineKeyboardButton("➕ Добавить хост", callback_data="settings_proxmox_add")],
        [
            InlineKeyboardButton(
                "✏️/🗑️ Редактировать и удалить паттерны", callback_data="settings_patterns_proxmox"
            )
        ],
        [InlineKeyboardButton("➕ Добавить паттерн", callback_data="add_proxmox_pattern")],
        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_ext_backup_proxmox"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_proxmox_hosts_list(update, context):
    """Показать список хостов Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    message = "📋 *Хосты Proxmox*\n\n"
    if not proxmox_hosts:
        message += "❌ Хосты не настроены."
    else:
        for host_name in sorted(proxmox_hosts.keys()):
            host_value = proxmox_hosts.get(host_name)
            enabled = True
            if isinstance(host_value, dict):
                enabled = host_value.get("enabled", True)
            status_icon = "🟢" if enabled else "🔴"
            message += f"{status_icon} `{host_name}`\n"

    keyboard = []
    for host_name in sorted(proxmox_hosts.keys()):
        host_value = proxmox_hosts.get(host_name)
        enabled = True
        if isinstance(host_value, dict):
            enabled = host_value.get("enabled", True)
        toggle_text = "⛔️ Отключить" if enabled else "✅ Включить"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {host_name}", callback_data=f"settings_proxmox_edit_{host_name}"
                ),
                InlineKeyboardButton(
                    f"🗑️ {host_name}", callback_data=f"settings_proxmox_delete_{host_name}"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{toggle_text} {host_name}",
                    callback_data=f"settings_proxmox_toggle_{host_name}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )

    query.edit_message_text(
        message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_proxmox_host_handler(update, context):
    """Добавить хост Proxmox"""
    query = update.callback_query
    query.answer()

    context.user_data["adding_proxmox_host"] = True

    query.edit_message_text(
        "➕ *Добавление Proxmox хоста*\n\n" "Введите имя хоста (как в письмах бэкапов):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data="settings_backup_proxmox"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def delete_proxmox_host(update, context, host_name):
    """Удалить хост Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    proxmox_hosts.pop(host_name, None)
    settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)

    query.edit_message_text(
        f"✅ Хост `{host_name}` удалён.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def handle_proxmox_host_input(update, context):
    """Обработчик добавления хоста Proxmox"""
    if "adding_proxmox_host" not in context.user_data:
        return

    host_name = update.message.text.strip()
    if not host_name:
        update.message.reply_text("❌ Имя хоста не может быть пустым. Попробуйте снова:")
        return

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name in proxmox_hosts:
        update.message.reply_text("❌ Такой хост уже есть. Введите другой:")
        return

    proxmox_hosts[host_name] = {"enabled": True}
    settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)

    update.message.reply_text(
        f"✅ Хост `{host_name}` добавлен.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )

    context.user_data.pop("adding_proxmox_host", None)


def edit_proxmox_host_handler(update, context, host_name):
    """Начать редактирование хоста Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    context.user_data["editing_proxmox_host"] = True
    context.user_data["editing_proxmox_host_name"] = host_name

    query.edit_message_text(
        "✏️ *Редактирование хоста Proxmox*\n\n"
        f"Текущий хост: `{host_name}`\n\n"
        "Введите новое имя хоста:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("❌ Отмена", callback_data="settings_backup_proxmox"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def handle_proxmox_host_edit_input(update, context):
    """Обработчик редактирования хоста Proxmox"""
    if "editing_proxmox_host" not in context.user_data:
        return

    new_host_name = update.message.text.strip()
    if not new_host_name:
        update.message.reply_text("❌ Имя хоста не может быть пустым. Попробуйте снова:")
        return

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    old_host_name = context.user_data.get("editing_proxmox_host_name")
    if not old_host_name or old_host_name not in proxmox_hosts:
        update.message.reply_text("❌ Хост не найден.")
        context.user_data.pop("editing_proxmox_host", None)
        context.user_data.pop("editing_proxmox_host_name", None)
        return

    if new_host_name in proxmox_hosts and new_host_name != old_host_name:
        update.message.reply_text("❌ Такой хост уже есть. Введите другой:")
        return

    host_value = proxmox_hosts.pop(old_host_name, None)
    if not isinstance(host_value, dict):
        host_value = {"enabled": True}
    proxmox_hosts[new_host_name] = host_value
    settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)

    update.message.reply_text(
        f"✅ Хост обновлён: `{new_host_name}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )

    context.user_data.pop("editing_proxmox_host", None)
    context.user_data.pop("editing_proxmox_host_name", None)


def toggle_proxmox_host(update, context, host_name):
    """Включить/отключить мониторинг хоста Proxmox"""
    query = update.callback_query
    query.answer()

    proxmox_hosts = _get_proxmox_hosts_for_settings()

    if host_name not in proxmox_hosts:
        query.edit_message_text(
            "❌ Хост не найден.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                    [
                        InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )
        return

    host_value = proxmox_hosts.get(host_name)
    if isinstance(host_value, dict):
        enabled = host_value.get("enabled", True)
    else:
        enabled = True
        host_value = {"enabled": True}

    host_value["enabled"] = not enabled
    proxmox_hosts[host_name] = host_value
    settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)

    status_text = "включен" if host_value["enabled"] else "отключен"
    query.edit_message_text(
        f"✅ Мониторинг хоста `{host_name}` {status_text}.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                [
                    InlineKeyboardButton("↩️ Назад", callback_data="settings_backup_proxmox"),
                    InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                ],
            ]
        ),
    )


def add_proxmox_pattern_handler(update, context):
    """Добавить паттерн для Proxmox"""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "proxmox_input"
    context.user_data["backup_pattern_mode"] = "proxmox_wizard"

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна Proxmox*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.\n\n"
        "Пример темы:\n"
        "`vzdump backup status`",
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


def proxmox_pattern_retry_handler(update, context):
    """Повторить ввод темы/фрагментов для паттерна Proxmox."""
    query = update.callback_query
    query.answer()

    context.user_data["adding_backup_pattern"] = True
    context.user_data["backup_pattern_stage"] = "proxmox_input"
    context.user_data["backup_pattern_mode"] = "proxmox_wizard"
    context.user_data.pop("backup_pattern_generated", None)
    context.user_data.pop("backup_pattern_source", None)

    query.edit_message_text(
        "🧙 *Мастер добавления паттерна Proxmox*\n\n"
        "Введите тему письма целиком или обязательные фрагменты через `;`/`,`.\n"
        "Фрагменты учитываются в указанном порядке.",
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


def proxmox_pattern_confirm_handler(update, context):
    """Подтвердить сохранение паттерна Proxmox."""
    query = update.callback_query
    query.answer()

    pattern = context.user_data.get("backup_pattern_generated")
    back_callback = context.user_data.get("patterns_back", "settings_backup")

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
            ("subject", pattern, "proxmox"),
        )
        conn.commit()

        source_label = context.user_data.get("backup_pattern_source", "мастер")
        query.edit_message_text(
            "✅ *Паттерн добавлен!*\n\n"
            "Категория: *proxmox*\n"
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
