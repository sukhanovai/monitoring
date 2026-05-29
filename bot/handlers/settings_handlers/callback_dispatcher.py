"""
/bot/handlers/settings_handlers/callback_dispatcher.py
Server Monitoring System v8.62.70
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Главный диспатчер callback-кнопок настроек (PR11 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.70
Автор: Александр Суханов (c)
Лицензия: MIT
Выделено из bot/handlers/settings_handlers/_legacy.py. Имя
сохранено — фасад пакета через двусторонний re-export продолжает
его отдавать; внутренние ссылки в _legacy.py резолвятся через
обратный `from ... import *` блок.
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

from bot.handlers.settings_handlers.auth import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.db import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.mail import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.proxmox import *  # noqa: F401, F403
from bot.handlers.settings_handlers.backups.snapshot import *  # noqa: F401, F403

# PR7b: supplier_stock-функции вынесены в одноимённый модуль пакета;
# реэкспортируем их сюда же, чтобы внутренние ссылки в _legacy.py
# (например, settings_callback_handler) продолжали работать.
from bot.handlers.settings_handlers.supplier_stock import *  # noqa: F401, F403
from bot.handlers.settings_handlers.windows_creds import *  # noqa: F401, F403
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


_LEGACY_BINDINGS_DONE = False


def _ensure_legacy_bindings() -> None:
    """Подтягивает имена из _legacy в globals этого модуля.

    `settings_callback_handler` выделен из _legacy.py (PR11), но обращается
    к множеству хелперов и show_*-меню, которые остались в _legacy
    (`settings_command`, `_safe_query_answer`, `show_telegram_settings`, …).
    Статический импорт _legacy сюда невозможен — _legacy сам делает
    `from .callback_dispatcher import *` (циклический импорт). Поэтому
    связываем недостающие имена лениво, на первом вызове, когда оба модуля
    уже полностью загружены. `setdefault` не перетирает собственные имена
    этого модуля.
    """
    global _LEGACY_BINDINGS_DONE
    if _LEGACY_BINDINGS_DONE:
        return

    from bot.handlers.settings_handlers import _legacy

    module_globals = globals()
    for name in dir(_legacy):
        if name.startswith("__"):
            continue
        module_globals.setdefault(name, getattr(_legacy, name))
    _LEGACY_BINDINGS_DONE = True


def settings_callback_handler(update, context):
    """Обработчик callback'ов настроек"""
    _ensure_legacy_bindings()
    query = update.callback_query
    data = query.data

    # если это callback от бэкапов, НЕ обрабатываем здесь
    if (
        data.startswith("db_")
        and data not in BACKUP_SETTINGS_CALLBACKS
        and not data.startswith("db_default_")
    ):
        _safe_query_answer(query, "⚙️ Перенаправление к модулю бэкапов...")
        # Передаем обработку дальше по цепочке
        return
    if data.startswith("backup_") and data not in BACKUP_SETTINGS_CALLBACKS:
        _safe_query_answer(query, "⚙️ Перенаправление к модулю бэкапов...")
        # Передаем обработку дальше по цепочке
        return

    try:
        # Основные категории настроек
        if data == "settings_main":
            settings_command(update, context)
        elif data == "settings_telegram":
            show_telegram_settings(update, context)
        elif data == "settings_matrix":
            show_matrix_settings(update, context)
        elif data == "settings_monitoring":
            show_monitoring_settings(update, context)
        elif data == "settings_time":
            show_time_settings(update, context)
        elif data == "settings_resources":
            show_resource_settings(update, context)
        elif data == "settings_auth":
            show_auth_settings(update, context)  # Теперь упрощенная версия
        elif data == "settings_servers":
            show_servers_settings(update, context)
        elif data == "settings_backup":
            show_backup_settings(update, context)
        elif data == "settings_extensions":
            show_settings_extensions_menu(update, context)
        elif data == "settings_extensions_manage":
            show_extensions_settings_menu(update, context)
        elif data == "settings_ext_backup_proxmox":
            show_proxmox_backup_settings(update, context)
        elif data == "settings_ext_backup_db":
            context.user_data.pop("settings_db_back", None)
            show_database_backup_settings(update, context)
        elif data == "settings_ext_backup_mail":
            show_mail_backup_settings(update, context)
        elif data == "settings_ext_stock_load":
            show_stock_load_settings(update, context)
        elif data == "settings_ext_supplier_stock":
            show_supplier_stock_settings(update, context)
        elif data == "settings_snapshot_menu":
            show_snapshot_transfer_settings(update, context)
        elif data == "settings_patterns_db":
            show_db_patterns_menu(update, context)
        elif data == "settings_patterns_db_from_backup":
            show_db_patterns_menu_from_backup(update, context)
        elif data == "settings_patterns_proxmox":
            show_proxmox_patterns_menu(update, context)
        elif data == "settings_patterns_zfs":
            show_zfs_patterns_menu(update, context)
        elif data == "settings_patterns_mail":
            show_mail_patterns_menu(update, context)
        elif data == "settings_patterns_stock":
            show_stock_load_patterns_menu(update, context)
        elif data == "settings_snapshot_hosts":
            show_snapshot_hosts_menu(update, context)
        elif data == "settings_snapshot_patterns":
            context.user_data["patterns_filter"] = "snapshot_transfer"
            context.user_data["patterns_back"] = "settings_snapshot_menu"
            context.user_data["patterns_add"] = "add_snapshot_pattern"
            context.user_data["patterns_title"] = "📸 *Паттерны передач снэпшотов*"
            view_patterns_handler(update, context)
        elif data == "add_snapshot_pattern":
            _clear_snapshot_host_input_state(context)
            add_snapshot_pattern_handler(update, context)
        elif data == "settings_web":
            show_web_settings(update, context)
        elif data == "settings_view_all":
            view_all_settings_handler(update, context)

        elif data == "supplier_stock_download":
            show_supplier_stock_download_settings(update, context)
        elif data == "supplier_stock_mail":
            show_supplier_stock_mail_settings(update, context)
        elif data == "supplier_stock_reports":
            show_supplier_stock_reports(update, context, source_kind="download")
        elif data == "supplier_stock_reports_download":
            show_supplier_stock_reports(update, context, source_kind="download")
        elif data == "supplier_stock_reports_mail":
            show_supplier_stock_reports(update, context, source_kind="mail")
        elif data == "supplier_stock_reports_sources_download":
            show_supplier_stock_report_sources(update, context, source_kind="download")
        elif data == "supplier_stock_reports_sources_mail":
            show_supplier_stock_report_sources(update, context, source_kind="mail")
        elif data.startswith("supplier_stock_report_source_day|"):
            _, source_kind, source_id = data.split("|", 2)
            show_supplier_stock_report_source_stats(
                update, context, source_id, source_kind, period_days=1
            )
        elif data.startswith("supplier_stock_report_source|"):
            _, source_kind, source_id = data.split("|", 2)
            show_supplier_stock_report_source_stats(update, context, source_id, source_kind)
        elif data.startswith("supplier_stock_report_entry|"):
            _, entry_key = data.split("|", 1)
            show_supplier_stock_report_entry_details(update, context, entry_key)
        elif data == "supplier_stock_processing":
            show_supplier_stock_processing_menu(
                update, context, action_prefix="supplier_stock_processing"
            )
        elif data.startswith("supplier_stock_processing|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            rule_id = parts[2] if len(parts) > 2 else ""
            if action == "add":
                supplier_stock_start_processing_rule_menu(update, context)
            elif action == "edit" and rule_id:
                supplier_stock_start_processing_rule_menu(update, context, rule_id=rule_id)
            elif action in ("toggle", "delete", "activate") and rule_id:
                config = get_supplier_stock_config()
                rules = config.get("processing", {}).get("rules", [])
                if action == "toggle":
                    for rule in rules:
                        if str(rule.get("id")) == rule_id:
                            rule["enabled"] = not rule.get("enabled", True)
                            if not rule.get("enabled", True):
                                rule["active"] = False
                            break
                elif action == "activate":
                    _set_supplier_stock_processing_active_rule(rules, rule_id)
                elif action == "delete":
                    rules = [item for item in rules if str(item.get("id")) != rule_id]
                config.setdefault("processing", {})["rules"] = rules
                save_supplier_stock_config(config)
                show_supplier_stock_processing_menu(
                    update, context, action_prefix="supplier_stock_processing"
                )
        elif data.startswith("supplier_stock_processing_rule|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            if action == "menu":
                show_supplier_stock_processing_rule_menu(update, context)
            elif action == "save":
                supplier_stock_save_processing_rule(update, context)
            elif action == "save_back":
                if _save_processing_rule_data(update, context):
                    back_callback = context.user_data.get(
                        "supplier_stock_processing_back", "supplier_stock_processing"
                    )
                    _show_processing_rule_back_menu(update, context, back_callback)
            elif action == "back":
                if context.user_data.get("supplier_stock_processing_rule_dirty"):
                    _persist_processing_rule_data(context)
                    context.user_data["supplier_stock_processing_rule_dirty"] = False
                back_callback = context.user_data.get(
                    "supplier_stock_processing_back", "supplier_stock_processing"
                )
                _show_processing_rule_back_menu(update, context, back_callback)
            elif action == "toggle_processing":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                data["requires_processing"] = not data.get("requires_processing", True)
                if data.get("requires_processing") and not data.get("variants"):
                    _sync_processing_variants_count(data, 1)
                    data["variants_count"] = 1
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_rule_menu(update, context)
            elif action in ("add_variant", "remove_variant"):
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variants = data.get("variants", [])
                current_count = len(variants)
                if action == "add_variant":
                    new_count = current_count + 1
                else:
                    new_count = max(current_count - 1, 0)
                _sync_processing_variants_count(data, new_count)
                data["variants_count"] = new_count
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_rule_menu(update, context)
            elif action == "variant" and len(parts) > 2:
                variant_index = int(parts[2])
                context.user_data["supplier_stock_processing_variant_index"] = variant_index
                show_supplier_stock_processing_variant_menu(update, context, variant_index)
            elif action == "field" and len(parts) > 2:
                field = parts[2]
                supplier_stock_start_processing_field_edit(update, context, field)
        elif data.startswith("supplier_stock_processing_variant|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            variant_index = int(parts[2]) if len(parts) > 2 else 0
            if action == "menu":
                show_supplier_stock_processing_variant_menu(update, context, variant_index)
            elif action == "add_column":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                columns_count = variant.get("data_columns_count") or len(
                    variant.get("data_columns", [])
                )
                _sync_variant_columns(variant, columns_count + 1)
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_variant_menu(update, context, variant_index)
            elif action == "toggle_orc":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get("orc", {})
                orc["enabled"] = not orc.get("enabled", False)
                variant["orc"] = orc
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_rule_menu(update, context)
            elif action == "field" and len(parts) > 3:
                field = parts[3]
                item_index = int(parts[4]) if len(parts) > 4 else None
                supplier_stock_start_processing_field_edit(
                    update,
                    context,
                    field,
                    variant_index=variant_index,
                    item_index=item_index,
                )
        elif data.startswith("supplier_stock_processing_columns|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            variant_index = int(parts[2]) if len(parts) > 2 else 0
            if action == "menu":
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action == "toggle_article_filter":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                current_value = variant.get("use_article_filter")
                if current_value is None:
                    current_value = bool(variant.get("article_filter"))
                variant["use_article_filter"] = not current_value
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action in ("tac", "toggle_article_filter_column") and len(parts) > 3:
                column_index = int(parts[3])
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                columns_count = variant.get("data_columns_count") or len(
                    variant.get("data_columns", [])
                )
                _sync_variant_columns(variant, columns_count)
                filters = list(variant.get("use_article_filter_columns", []))
                if 0 <= column_index < len(filters):
                    filters[column_index] = not filters[column_index]
                    variant["use_article_filter_columns"] = filters
                    data["variants"][variant_index] = variant
                    context.user_data["supplier_stock_processing_rule_data"] = data
                    context.user_data["supplier_stock_processing_rule_dirty"] = True
                    _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action == "add_column":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                columns_count = variant.get("data_columns_count") or len(
                    variant.get("data_columns", [])
                )
                _sync_variant_columns(variant, columns_count + 1)
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
            elif action == "remove_column" and len(parts) > 3:
                column_index = int(parts[3])
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                if _remove_variant_column(variant, column_index):
                    data["variants"][variant_index] = variant
                    context.user_data["supplier_stock_processing_rule_data"] = data
                    context.user_data["supplier_stock_processing_rule_dirty"] = True
                    _persist_processing_rule_data(context)
                show_supplier_stock_processing_columns_menu(update, context, variant_index)
        elif data.startswith("supplier_stock_processing_orc|"):
            parts = data.split("|")
            action = parts[1] if len(parts) > 1 else ""
            variant_index = int(parts[2]) if len(parts) > 2 else 0
            if action == "menu":
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == "set_input" and len(parts) > 3:
                input_index = int(parts[3])
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get("orc", {})
                orc["input_index"] = input_index
                variant["orc"] = orc
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == "clear_input":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get("orc", {})
                orc.pop("input_index", None)
                variant["orc"] = orc
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == "set_output" and len(parts) > 3:
                output_index = int(parts[3])
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get("orc", {})
                orc["output_index"] = output_index
                variant["orc"] = orc
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
            elif action == "clear_output":
                data = context.user_data.get("supplier_stock_processing_rule_data", {})
                variant = _ensure_processing_variant(data, variant_index)
                orc = variant.get("orc", {})
                orc.pop("output_index", None)
                variant["orc"] = orc
                data["variants"][variant_index] = variant
                context.user_data["supplier_stock_processing_rule_data"] = data
                context.user_data["supplier_stock_processing_rule_dirty"] = True
                _persist_processing_rule_data(context)
                show_supplier_stock_processing_orc_menu(update, context, variant_index)
        elif data.startswith("supplier_stock_processing_source|"):
            parts = data.split("|")
            source_id = parts[1] if len(parts) > 1 else ""
            action = parts[2] if len(parts) > 2 else ""
            rule_id = parts[3] if len(parts) > 3 else ""
            back_callback = f"supplier_stock_source_settings|{source_id}"
            action_prefix = f"supplier_stock_processing_source|{source_id}"
            if action == "menu":
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="🧩 *Обработка файлов (источник)*",
                )
            elif action == "add":
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                )
            elif action == "edit" and rule_id:
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    rule_id,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                )
            elif action in ("toggle", "delete", "activate") and rule_id:
                config = get_supplier_stock_config()
                rules = config.get("processing", {}).get("rules", [])
                if action == "toggle":
                    for rule in rules:
                        if str(rule.get("id")) == rule_id:
                            rule["enabled"] = not rule.get("enabled", True)
                            if not rule.get("enabled", True):
                                rule["active"] = False
                            break
                elif action == "activate":
                    _set_supplier_stock_processing_active_rule(
                        rules,
                        rule_id,
                        source_id=source_id,
                        source_kind="download",
                    )
                elif action == "delete":
                    rules = [item for item in rules if str(item.get("id")) != rule_id]
                config.setdefault("processing", {})["rules"] = rules
                save_supplier_stock_config(config)
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="download",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="🧩 *Обработка файлов (источник)*",
                )
        elif data.startswith("supplier_stock_processing_mail|"):
            parts = data.split("|")
            source_id = parts[1] if len(parts) > 1 else ""
            action = parts[2] if len(parts) > 2 else ""
            rule_id = parts[3] if len(parts) > 3 else ""
            back_callback = f"supplier_stock_mail_source_settings|{source_id}"
            action_prefix = f"supplier_stock_processing_mail|{source_id}"
            if action == "menu":
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="🧩 *Обработка файлов (почта)*",
                )
            elif action == "add":
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                )
            elif action == "edit" and rule_id:
                supplier_stock_start_processing_rule_menu(
                    update,
                    context,
                    rule_id,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                )
            elif action in ("toggle", "delete", "activate") and rule_id:
                config = get_supplier_stock_config()
                rules = config.get("processing", {}).get("rules", [])
                if action == "toggle":
                    for rule in rules:
                        if str(rule.get("id")) == rule_id:
                            rule["enabled"] = not rule.get("enabled", True)
                            if not rule.get("enabled", True):
                                rule["active"] = False
                            break
                elif action == "activate":
                    _set_supplier_stock_processing_active_rule(
                        rules,
                        rule_id,
                        source_id=source_id,
                        source_kind="mail",
                    )
                elif action == "delete":
                    rules = [item for item in rules if str(item.get("id")) != rule_id]
                config.setdefault("processing", {})["rules"] = rules
                save_supplier_stock_config(config)
                show_supplier_stock_processing_menu(
                    update,
                    context,
                    source_id=source_id,
                    source_kind="mail",
                    back_callback=back_callback,
                    action_prefix=action_prefix,
                    title="🧩 *Обработка файлов (почта)*",
                )
        elif data == "supplier_stock_noop":
            query.answer(" ", show_alert=False)
        elif data == "supplier_stock_mail_toggle":
            config = get_supplier_stock_config()
            mail_settings = config.get("mail", {})
            mail_settings["enabled"] = not mail_settings.get("enabled", False)
            config["mail"] = mail_settings
            save_supplier_stock_config(config)
            show_supplier_stock_mail_settings(update, context)
        elif data == "supplier_stock_mail_temp_dir":
            context.user_data["supplier_stock_mail_edit"] = "temp_dir"
            config = get_supplier_stock_config()
            current_temp_dir = _format_current_hint(config.get("mail", {}).get("temp_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите путь к временному каталогу для почтовых файлов:\n"
                f"Текущее значение: {current_temp_dir}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_mail")]]
                ),
            )
        elif data == "supplier_stock_mail_archive_dir":
            context.user_data["supplier_stock_mail_edit"] = "archive_dir"
            config = get_supplier_stock_config()
            current_archive_dir = _format_current_hint(config.get("mail", {}).get("archive_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите путь к каталогу архива для почтовых файлов:\n"
                f"Текущее значение: {current_archive_dir}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_mail")]]
                ),
            )
        elif data == "supplier_stock_archive_cleanup_mail":
            context.user_data["supplier_stock_edit"] = "archive_cleanup_days"
            context.user_data["supplier_stock_archive_cleanup_back"] = "supplier_stock_mail"
            config = get_supplier_stock_config()
            current_value = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите период очистки архива в днях (0 — отключить):\n"
                f"Текущее значение: {current_value}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_mail")]]
                ),
            )
        elif data == "supplier_stock_report_period":
            context.user_data["supplier_stock_edit"] = "report_period_days"
            config = get_supplier_stock_config()
            current_value = config.get("reporting", {}).get("period_days", 7)
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите период отчётов в днях (минимум 1):\n" f"Текущее значение: {current_value}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "❌ Отмена", callback_data="settings_ext_supplier_stock"
                            )
                        ]
                    ]
                ),
            )
        elif data == "supplier_stock_mail_unpack_toggle":
            query.answer("ℹ️ Распаковка теперь на уровне правил", show_alert=False)
            show_supplier_stock_mail_settings(update, context)
        elif data == "supplier_stock_mail_sources":
            show_supplier_stock_mail_sources_menu(update, context)
        elif data == "supplier_stock_resources":
            show_supplier_stock_resources_menu(update, context)
        elif data == "supplier_stock_ftp":
            show_supplier_stock_ftp_settings(update, context)
        elif data == "supplier_stock_mail_source_add":
            supplier_stock_start_mail_source_wizard(update, context)
        elif data.startswith("supplier_stock_mail_source_settings|"):
            source_id = data.split("|", 1)[1]
            show_supplier_stock_mail_source_settings(update, context, source_id)
        elif data.startswith("supplier_stock_mail_source_individual|"):
            source_id = data.split("|", 1)[1]
            show_supplier_stock_mail_source_individual_settings(update, context, source_id)
        elif data.startswith("supplier_stock_mail_field|"):
            _, source_id, field = data.split("|", 2)
            supplier_stock_start_mail_source_field_edit(update, context, source_id, field)
        elif data.startswith("supplier_stock_mail_source_individual_toggle_"):
            source_id = data.replace("supplier_stock_mail_source_individual_toggle_", "")
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    individual_dir = source.setdefault("individual_directory", {})
                    individual_dir["enabled"] = not individual_dir.get("enabled", False)
                    break
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_mail_source_individual_settings(update, context, source_id)
        elif data.startswith("supplier_stock_mail_source_unpack_toggle_"):
            source_id = data.replace("supplier_stock_mail_source_unpack_toggle_", "")
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            updated = False
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["unpack_archive"] = not source.get("unpack_archive", False)
                    updated = True
                    break
            if not updated:
                query.answer("⚠️ Правило не найдено", show_alert=False)
                return
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get("supplier_stock_mail_source_settings_id") == source_id:
                show_supplier_stock_mail_source_settings(update, context, source_id)
            else:
                show_supplier_stock_mail_sources_menu(update, context)
        elif data.startswith("supplier_stock_mail_source_toggle_"):
            source_id = data.replace("supplier_stock_mail_source_toggle_", "")
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["enabled"] = not source.get("enabled", True)
                    break
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get("supplier_stock_mail_source_settings_id") == source_id:
                show_supplier_stock_mail_source_settings(update, context, source_id)
            else:
                show_supplier_stock_mail_sources_menu(update, context)
        elif data.startswith("supplier_stock_mail_source_delete_"):
            source_id = data.replace("supplier_stock_mail_source_delete_", "")
            config = get_supplier_stock_config()
            sources = config.get("mail", {}).get("sources", [])
            sources = [item for item in sources if str(item.get("id")) != source_id]
            config["mail"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_mail_sources_menu(update, context)
        elif data.startswith("supplier_stock_resource_settings|"):
            resource_id = data.split("|", 1)[1]
            show_supplier_stock_resource_settings(update, context, resource_id)
        elif data.startswith("supplier_stock_resource_field|"):
            _, resource_id, field = data.split("|", 2)
            supplier_stock_start_resource_field_edit(update, context, resource_id, field)
        elif data == "supplier_stock_resource_add":
            supplier_stock_start_resource_wizard(update, context)
        elif data.startswith("supplier_stock_resource_toggle_"):
            resource_id = data.replace("supplier_stock_resource_toggle_", "")
            config = get_supplier_stock_config()
            resources = config.get("resources", [])
            for resource in resources:
                if str(resource.get("id")) == resource_id:
                    resource["enabled"] = not resource.get("enabled", True)
                    break
            config["resources"] = resources
            save_supplier_stock_config(config)
            show_supplier_stock_resources_menu(update, context)
        elif data.startswith("supplier_stock_resource_delete_"):
            resource_id = data.replace("supplier_stock_resource_delete_", "")
            config = get_supplier_stock_config()
            resources = [
                item for item in config.get("resources", []) if str(item.get("id")) != resource_id
            ]
            config["resources"] = resources
            save_supplier_stock_config(config)
            show_supplier_stock_resources_menu(update, context)
        elif data.startswith("supplier_stock_ftp_field|"):
            _, field = data.split("|", 1)
            supplier_stock_start_ftp_field_edit(update, context, field)
        elif data == "supplier_stock_temp_dir":
            context.user_data["supplier_stock_edit"] = "temp_dir"
            config = get_supplier_stock_config()
            current_temp_dir = _format_current_hint(config.get("download", {}).get("temp_dir"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите путь к временному каталогу:\n" f"Текущее значение: {current_temp_dir}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_download")]]
                ),
            )
        elif data == "supplier_stock_schedule":
            show_supplier_stock_schedule_menu(update, context)
        elif data == "supplier_stock_unpack_toggle":
            query.answer("ℹ️ Распаковка теперь на уровне источников", show_alert=False)
            show_supplier_stock_download_settings(update, context)
        elif data == "supplier_stock_archive_dir":
            context.user_data["supplier_stock_edit"] = "archive_dir"
            config = get_supplier_stock_config()
            current_archive_dir = _format_current_hint(
                config.get("download", {}).get("archive_dir")
            )
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите путь к каталогу архива:\n" f"Текущее значение: {current_archive_dir}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_download")]]
                ),
            )
        elif data == "supplier_stock_archive_cleanup_download":
            context.user_data["supplier_stock_edit"] = "archive_cleanup_days"
            context.user_data["supplier_stock_archive_cleanup_back"] = "supplier_stock_download"
            config = get_supplier_stock_config()
            current_value = _format_archive_cleanup_days(config.get("archive_cleanup_days"))
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите период очистки архива в днях (0 — отключить):\n"
                f"Текущее значение: {current_value}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_download")]]
                ),
            )
        elif data == "supplier_stock_unpack_toggle":
            config = get_supplier_stock_config()
            download_settings = config.get("download", {})
            download_settings["unpack_archive"] = not download_settings.get("unpack_archive", False)
            config["download"] = download_settings
            save_supplier_stock_config(config)
            show_supplier_stock_download_settings(update, context)
        elif data == "supplier_stock_schedule_toggle":
            config = get_supplier_stock_config()
            schedule = config.get("download", {}).get("schedule", {})
            schedule["enabled"] = not schedule.get("enabled", False)
            config["download"]["schedule"] = schedule
            save_supplier_stock_config(config)
            show_supplier_stock_schedule_menu(update, context)
        elif data == "supplier_stock_schedule_time":
            context.user_data["supplier_stock_edit"] = "schedule_time"
            config = get_supplier_stock_config()
            current_time = _format_current_hint(
                config.get("download", {}).get("schedule", {}).get("time")
            )
            _supplier_stock_remember_prompt_message(context, query)
            query.edit_message_text(
                "Введите одно или несколько времен запуска (HH:MM).\n"
                "Разделители: пробел, запятая или точка с запятой.\n"
                f"Текущее значение: {current_time}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Отмена", callback_data="supplier_stock_schedule")]]
                ),
            )
        elif data == "supplier_stock_sources":
            show_supplier_stock_sources_menu(update, context)
        elif data == "supplier_stock_source_add":
            supplier_stock_start_source_wizard(update, context)
        elif data.startswith("supplier_stock_source_settings|"):
            source_id = data.split("|", 1)[1]
            show_supplier_stock_source_settings(update, context, source_id)
        elif data.startswith("supplier_stock_source_individual|"):
            source_id = data.split("|", 1)[1]
            show_supplier_stock_source_individual_settings(update, context, source_id)
        elif data.startswith("supplier_stock_source_field|"):
            _, source_id, field = data.split("|", 2)
            supplier_stock_start_source_field_edit(update, context, source_id, field)
        elif data.startswith("supplier_stock_source_iek_settings|"):
            source_id = data.split("|", 1)[1]
            show_supplier_stock_source_iek_settings(update, context, source_id)
        elif data.startswith("supplier_stock_source_iek_field|"):
            _, source_id, field = data.split("|", 2)
            supplier_stock_start_source_iek_field_edit(update, context, source_id, field)
        elif data.startswith("supplier_stock_source_individual_toggle_"):
            source_id = data.replace("supplier_stock_source_individual_toggle_", "")
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    individual_dir = source.setdefault("individual_directory", {})
                    individual_dir["enabled"] = not individual_dir.get("enabled", False)
                    break
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_source_individual_settings(update, context, source_id)
        elif data.startswith("supplier_stock_source_unpack_toggle_"):
            source_id = data.replace("supplier_stock_source_unpack_toggle_", "")
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            updated = False
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["unpack_archive"] = not source.get("unpack_archive", False)
                    updated = True
                    break
            if not updated:
                query.answer("⚠️ Источник не найден", show_alert=False)
                return
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get("supplier_stock_source_settings_id") == source_id:
                show_supplier_stock_source_settings(update, context, source_id)
            else:
                show_supplier_stock_sources_menu(update, context)
        elif data.startswith("supplier_stock_source_toggle_"):
            source_id = data.replace("supplier_stock_source_toggle_", "")
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            for source in sources:
                if str(source.get("id")) == source_id:
                    source["enabled"] = not source.get("enabled", True)
                    break
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            if context.user_data.get("supplier_stock_source_settings_id") == source_id:
                show_supplier_stock_source_settings(update, context, source_id)
            else:
                show_supplier_stock_sources_menu(update, context)
        elif data.startswith("supplier_stock_source_delete_"):
            source_id = data.replace("supplier_stock_source_delete_", "")
            config = get_supplier_stock_config()
            sources = config.get("download", {}).get("sources", [])
            sources = [item for item in sources if str(item.get("id")) != source_id]
            config["download"]["sources"] = sources
            save_supplier_stock_config(config)
            show_supplier_stock_sources_menu(update, context)

        # Подпункты
        elif data == "backup_times":
            show_backup_times(update, context)
        elif data == "settings_backup_proxmox":
            show_backup_proxmox_settings(update, context)
        elif data == "settings_proxmox_add":
            add_proxmox_host_handler(update, context)
        elif data == "settings_proxmox_list":
            show_proxmox_hosts_list(update, context)
        elif data.startswith("settings_proxmox_delete_"):
            host_name = data.replace("settings_proxmox_delete_", "")
            delete_proxmox_host(update, context, host_name)
        elif data.startswith("settings_proxmox_edit_"):
            host_name = data.replace("settings_proxmox_edit_", "")
            edit_proxmox_host_handler(update, context, host_name)
        elif data.startswith("settings_proxmox_toggle_"):
            host_name = data.replace("settings_proxmox_toggle_", "")
            toggle_proxmox_host(update, context, host_name)
        elif data == "settings_zfs":
            show_zfs_settings(update, context)
        elif data == "settings_zfs_list":
            show_zfs_servers_list(update, context)
        elif data == "settings_zfs_add":
            add_zfs_server_handler(update, context)
        elif data.startswith("settings_zfs_edit_name_"):
            server_name = data.replace("settings_zfs_edit_name_", "")
            edit_zfs_server_name_handler(update, context, server_name)
        elif data.startswith("settings_zfs_edit_ip_"):
            server_name = data.replace("settings_zfs_edit_ip_", "")
            edit_zfs_server_ip_handler(update, context, server_name)
        elif data.startswith("settings_zfs_edit_threshold_"):
            server_name = data.replace("settings_zfs_edit_threshold_", "")
            edit_zfs_server_threshold_handler(update, context, server_name)
        elif data.startswith("settings_zfs_delete_"):
            server_name = data.replace("settings_zfs_delete_", "")
            delete_zfs_server(update, context, server_name)
        elif data.startswith("settings_zfs_toggle_"):
            server_name = data.replace("settings_zfs_toggle_", "")
            toggle_zfs_server(update, context, server_name)

        # Новые обработчики для настроек БД
        elif data == "settings_db_main":
            show_backup_databases_settings(update, context)
        elif data == "settings_db_main_from_backup":
            context.user_data["settings_db_back"] = "backup_databases"
            show_backup_databases_settings(update, context)
        elif data == "settings_db_add_category":
            add_database_category_handler(update, context)
        elif data == "settings_db_manage_categories":
            manage_database_categories_handler(update, context)
        elif data == "settings_db_manage_categories_from_backup":
            context.user_data["settings_db_back"] = "backup_databases"
            manage_database_categories_handler(update, context)
        elif data == "settings_db_edit_category":
            edit_databases_handler(update, context)
        elif data == "settings_db_delete_category":
            delete_database_category_handler(update, context)
        elif data == "settings_db_view_all":
            view_all_databases_handler(update, context)
        elif data == "settings_db_view_all_from_backup":
            context.user_data["settings_db_back"] = "backup_databases"
            view_all_databases_handler(update, context)
        elif data == "settings_db_add_new":
            add_new_database_from_manage_handler(update, context)

        # Обработчики для новых пунктов меню
        elif data == "manage_chats":
            manage_chats_handler(update, context)
        elif data == "server_timeouts":
            show_server_timeouts(update, context)  # Теперь упрощенная версия
        elif data == "settings_add_server":
            add_server_handler(update, context)

        # Обработчики для установки значений
        elif data.startswith("set_"):
            handle_setting_input(update, context, data.replace("set_", ""))

        # Управление чатами
        elif data == "add_chat":
            add_chat_handler(update, context)
        elif data == "remove_chat":
            remove_chat_handler(update, context)
        # Паттерны бэкапов
        elif data == "view_patterns":
            view_patterns_handler(update, context)
        elif data == "add_pattern":
            add_pattern_handler(update, context)
        elif data == "add_zfs_pattern":
            add_zfs_pattern_handler(update, context)
        elif data == "add_proxmox_pattern":
            add_proxmox_pattern_handler(update, context)
        elif data == "add_mail_pattern":
            add_mail_pattern_handler(update, context)
        elif data == "add_snapshot_pattern":
            _clear_snapshot_host_input_state(context)
            add_snapshot_pattern_handler(update, context)
        elif data == "snapshot_host_add":
            _clear_snapshot_host_input_state(context)
            context.user_data["adding_snapshot_host"] = True
            context.user_data["snapshot_add_back_callback"] = "settings_snapshot_hosts"
            query.edit_message_text(
                "➕ *Добавление хоста передачи снэпшотов*\n\n"
                "Введите имя хоста (например: `sr-srv1`)",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data="settings_snapshot_hosts")]]
                ),
            )
        elif data.startswith("snapshot_host_edit|"):
            _, host_name = data.split("|", 1)
            _clear_snapshot_host_input_state(context)
            context.user_data["editing_snapshot_host_name"] = host_name
            context.user_data["snapshot_add_back_callback"] = "settings_snapshot_hosts"
            query.edit_message_text(
                f"✏️ *Переименование хоста*\n\nТекущий: `{escape_markdown(host_name, version=1)}`\nВведите новое имя:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data="settings_snapshot_hosts")]]
                ),
            )
        elif data.startswith("snapshot_host_toggle|"):
            _, host_name = data.split("|", 1)
            toggle_snapshot_host_handler(update, context, host_name)
            show_snapshot_hosts_menu(update, context)
        elif data.startswith("snapshot_host_delete|"):
            _, host_name = data.split("|", 1)
            delete_snapshot_host_handler(update, context, host_name)
            show_snapshot_hosts_menu(update, context)
        elif data.startswith("snapshot_host_start|"):
            _, host_name = data.split("|", 1)
            _clear_snapshot_host_input_state(context)
            context.user_data["editing_snapshot_start_time"] = host_name
            context.user_data["snapshot_add_back_callback"] = "settings_snapshot_hosts"
            query.edit_message_text(
                f"⏰ *Время старта для `{escape_markdown(host_name, version=1)}`*\n\nВведите время в формате HH:MM",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("↩️ Назад", callback_data="settings_snapshot_hosts")]]
                ),
            )
        elif data == "add_stock_pattern":
            show_stock_pattern_type_menu(update, context)
        elif data == "edit_mail_default_pattern":
            edit_mail_default_pattern_handler(update, context)
        elif data == "db_pattern_confirm":
            db_pattern_confirm_handler(update, context)
        elif data == "db_pattern_retry":
            db_pattern_retry_handler(update, context)
        elif data.startswith("db_pattern_set_category_"):
            category = data.replace("db_pattern_set_category_", "")
            db_pattern_set_category_handler(update, context, category)
        elif data == "zfs_pattern_confirm":
            zfs_pattern_confirm_handler(update, context)
        elif data == "zfs_pattern_retry":
            zfs_pattern_retry_handler(update, context)
        elif data == "proxmox_pattern_confirm":
            proxmox_pattern_confirm_handler(update, context)
        elif data == "proxmox_pattern_retry":
            proxmox_pattern_retry_handler(update, context)
        elif data == "stock_pattern_confirm":
            stock_pattern_confirm_handler(update, context)
        elif data == "stock_pattern_retry":
            stock_pattern_retry_handler(update, context)
        elif data.startswith("stock_pattern_select_"):
            pattern_type = data.replace("stock_pattern_select_", "")
            stock_pattern_select_handler(update, context, pattern_type)
        elif data.startswith("db_default_edit_"):
            raw_value = data.replace("db_default_edit_", "")
            if "__" in raw_value:
                category, index_value = raw_value.split("__", 1)
                edit_default_db_pattern_handler(update, context, category, index_value)
        elif data.startswith("db_default_delete_"):
            raw_value = data.replace("db_default_delete_", "")
            if "__" in raw_value:
                category, index_value = raw_value.split("__", 1)
                delete_default_db_pattern_handler(update, context, category, index_value)
        elif data == "mail_pattern_confirm":
            mail_pattern_confirm_handler(update, context)
        elif data == "mail_pattern_retry":
            mail_pattern_retry_handler(update, context)
        elif data == "snapshot_pattern_confirm":
            snapshot_pattern_confirm_handler(update, context)
        elif data == "snapshot_pattern_retry":
            add_snapshot_pattern_handler(update, context)
        elif data == "settings_ext_enable_all":
            _enable_all_extensions_settings(query)
            show_extensions_settings_menu(update, context)
        elif data == "settings_ext_disable_all":
            _disable_all_extensions_settings(query)
            show_extensions_settings_menu(update, context)
        elif data.startswith("settings_ext_toggle_"):
            extension_id = data.replace("settings_ext_toggle_", "")
            success, message = extension_manager.toggle_extension(extension_id)
            if success:
                _safe_query_answer(query, message)
                show_extensions_settings_menu(update, context)
            else:
                _safe_query_answer(query, message, show_alert=True)
        elif data.startswith("delete_pattern_"):
            pattern_id = data.replace("delete_pattern_", "")
            delete_pattern_handler(update, context, pattern_id)
        elif data.startswith("edit_pattern_"):
            pattern_id = data.replace("edit_pattern_", "")
            edit_pattern_handler(update, context, pattern_id)

        # Обработчики для редактирования и удаления категорий БД
        elif data.startswith("settings_db_add_db_"):
            raw_value = data.replace("settings_db_add_db_", "", 1)
            category = _resolve_db_category_from_callback(context, raw_value)
            add_database_entry_handler(update, context, category)
        elif data.startswith("settings_db_edit_db_"):
            raw_value = data.replace("settings_db_edit_db_", "", 1)
            category, db_key = _resolve_db_entry_from_callback(context, raw_value)
            if category and db_key:
                edit_database_entry_handler(update, context, category, db_key)
        elif data.startswith("settings_db_toggle_monitor_"):
            raw_value = data.replace("settings_db_toggle_monitor_", "", 1)
            if "__" in raw_value:
                encoded_backup_type, encoded_db_name = raw_value.split("__", 1)
                settings_toggle_database_monitoring(
                    update, context, encoded_backup_type, encoded_db_name
                )
            else:
                toggle_map = context.user_data.get("settings_db_toggle_map", {})
                encoded_pair = toggle_map.get(raw_value, "")
                if "__" in encoded_pair:
                    encoded_backup_type, encoded_db_name = encoded_pair.split("__", 1)
                    settings_toggle_database_monitoring(
                        update, context, encoded_backup_type, encoded_db_name
                    )
                else:
                    _safe_query_answer(query, "Не удалось определить базу данных", show_alert=True)
        elif data.startswith("settings_db_delete_db_confirm_"):
            raw_value = data.replace("settings_db_delete_db_confirm_", "", 1)
            category, db_key = _resolve_db_entry_from_callback(context, raw_value)
            if category and db_key:
                delete_database_entry_execute(update, context, category, db_key)
        elif data.startswith("settings_db_delete_db_"):
            raw_value = data.replace("settings_db_delete_db_", "", 1)
            category, db_key = _resolve_db_entry_from_callback(context, raw_value)
            if category and db_key:
                delete_database_entry_confirmation(update, context, category, db_key)
        elif data.startswith("settings_db_delete_confirm_"):
            raw_value = data.replace("settings_db_delete_confirm_", "", 1)
            category = _resolve_db_category_from_callback(context, raw_value)
            delete_database_category_execute(update, context, category)
        elif data.startswith("settings_db_delete_"):
            raw_value = data.replace("settings_db_delete_", "", 1)
            category = _resolve_db_category_from_callback(context, raw_value)
            delete_database_category_confirmation(update, context, category)
        elif data.startswith("settings_db_rename_"):
            raw_value = data.replace("settings_db_rename_", "", 1)
            category = _resolve_db_category_from_callback(context, raw_value)
            start_database_category_edit_handler(update, context, category)
        elif data.startswith("settings_db_edit_"):
            raw_value = data.replace("settings_db_edit_", "", 1)
            category = _resolve_db_category_from_callback(context, raw_value)
            edit_database_category_details(update, context, category)

        # Обработчики для серверов
        elif data == "settings_servers_list":
            show_servers_list(update, context)
        elif data.startswith("settings_delete_server_"):
            ip = data.replace("settings_delete_server_", "")
            delete_server_confirmation(update, context, ip)
        elif data.startswith("settings_confirm_delete_server_"):
            ip = data.replace("settings_confirm_delete_server_", "")
            delete_server_execute(update, context, ip)
        elif data.startswith("settings_edit_server_type_select_"):
            handle_server_type_selection(update, context)
        elif data.startswith("settings_edit_server_name_"):
            ip = data.replace("settings_edit_server_name_", "")
            start_server_name_edit(update, context, ip)
        elif data.startswith("settings_edit_server_type_"):
            ip = data.replace("settings_edit_server_type_", "")
            start_server_type_edit(update, context, ip)
        elif data.startswith("settings_edit_server_"):
            ip = data.replace("settings_edit_server_", "")
            show_server_edit_menu(update, context, ip)
        elif data.startswith("settings_toggle_server_"):
            ip = data.replace("settings_toggle_server_", "")
            toggle_server_monitoring(update, context, ip)

        # Обработчики для таймаутов серверов
        elif data == "set_windows_2025_timeout":
            handle_setting_input(update, context, "windows_2025_timeout")
        elif data == "set_domain_servers_timeout":
            handle_setting_input(update, context, "domain_servers_timeout")
        elif data == "set_admin_servers_timeout":
            handle_setting_input(update, context, "admin_servers_timeout")
        elif data == "set_standard_windows_timeout":
            handle_setting_input(update, context, "standard_windows_timeout")
        elif data == "set_linux_timeout":
            handle_setting_input(update, context, "linux_timeout")
        elif data == "set_ping_timeout":
            handle_setting_input(update, context, "ping_timeout")

        # Обработчики типов серверов
        elif data.startswith("server_type_"):
            handle_server_type(update, context)

        # Аутентификация
        elif data == "settings_auth":
            show_auth_settings(update, context)
        elif data == "ssh_auth_settings":
            show_ssh_auth_settings(update, context)

        # Windows аутентификация
        elif data == "windows_auth_main":
            show_windows_auth_settings(update, context)
        elif data == "windows_auth_list":
            show_windows_auth_list(update, context)
        elif data == "windows_auth_add":
            show_windows_auth_add(update, context)
        elif data == "windows_auth_by_type":
            show_windows_auth_by_type(update, context)
        elif data == "windows_auth_manage_types":
            show_windows_auth_manage_types(update, context)

        # Обработчики типов для Windows учетных данных
        elif data.startswith("cred_type_"):
            handle_credential_type_selection(update, context)

        # Обработчики управления типами серверов Windows
        elif data.startswith("manage_type_"):
            handle_server_type_management(update, context)

        # Обработчики для управления типами серверов (подтверждение операций)
        elif data.startswith("merge_confirm_"):
            parts = data.replace("merge_confirm_", "").split("_")
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = "_".join(parts[1:])
                merge_server_types_confirmation(update, context, source_type, target_type)

        elif data.startswith("delete_type_confirm_"):
            server_type = data.replace("delete_type_confirm_", "")
            delete_server_type_confirmation(update, context, server_type)

        # Обработчики для выполнения операций с типами серверов
        elif data.startswith("merge_execute_"):
            parts = data.replace("merge_execute_", "").split("_")
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = "_".join(parts[1:])
                execute_server_type_merge(update, context, source_type, target_type)

        elif data.startswith("delete_type_execute_"):
            server_type = data.replace("delete_type_execute_", "")
            execute_server_type_delete(update, context, server_type)

        # Обработчики для закрытия меню
        elif data == "close":
            try:
                query.delete_message()
            except:
                query.edit_message_text("✅ Меню закрыто")

        else:
            _safe_query_answer(query, "⚙️ Этот раздел в разработке")

    except Exception as e:
        print(f"❌ Ошибка в settings_callback_handler: {e}")
        debug_logger(f"Ошибка в settings_callback_handler: {e}")
        _safe_query_answer(query, "❌ Произошла ошибка при обработке запроса")

    _safe_query_answer(query)
