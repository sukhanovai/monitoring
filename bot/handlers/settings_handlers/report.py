"""
/bot/handlers/settings_handlers/report.py
Server Monitoring System v8.63.40
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Report composition settings UI (Telegram)
Система мониторинга серверов
Версия: 8.63.40
Автор: Александр Суханов (c)
Лицензия: MIT
Меню настройки состава утреннего/ручного отчёта: мультивыбор расширений,
сведения которых добавляются в отчёт помимо базовых данных мониторинга.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from extensions.extension_manager import extension_manager
from lib.report_settings import (
    REPORT_CAPABLE_EXTENSIONS,
    get_report_extension_label,
    get_report_extensions,
    is_heavy_report_extension,
    set_report_extensions,
    toggle_report_extension,
)


def _build_report_settings_view():
    """Готовит текст и клавиатуру меню состава отчёта."""
    selected = set(get_report_extensions(use_cache=False))

    message = (
        "🗒️ *Состав отчёта*\n\n"
        "Базовые данные мониторинга доступности серверов в утреннем/ручном "
        "отчёте присутствуют всегда. Ниже отметьте расширения, сведения "
        "которых добавлять в отчёт.\n\n"
    )

    keyboard = []
    for ext_id in REPORT_CAPABLE_EXTENSIONS:
        label = get_report_extension_label(ext_id)
        in_report = ext_id in selected
        enabled = extension_manager.is_extension_enabled(ext_id)

        mark = "✅" if in_report else "⬜"
        suffix = "" if enabled else " (⚠️ расширение выключено)"
        if is_heavy_report_extension(ext_id):
            suffix += " (🐢 live-сбор)"
        message += f"{mark} {label}{suffix}\n"

        button_label = label
        if is_heavy_report_extension(ext_id):
            button_label = f"{label} 🐢"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{mark} {button_label}",
                    callback_data=f"report_ext_toggle_{ext_id}",
                )
            ]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton("✅ Включить все", callback_data="report_ext_all"),
                InlineKeyboardButton("⬜ Очистить", callback_data="report_ext_none"),
            ],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    message += (
        "\nВыключенные расширения не дают данных, даже если отмечены здесь.\n"
        "🐢 — live-сбор (SSH/опрос), может заметно замедлить отчёт."
    )
    return message, InlineKeyboardMarkup(keyboard)


def show_report_settings_menu(update, context):
    """Показать меню настройки состава отчёта."""
    query = update.callback_query
    if query is not None:
        query.answer()

    message, markup = _build_report_settings_view()

    if query is not None:
        query.edit_message_text(message, parse_mode="Markdown", reply_markup=markup)
    else:
        update.message.reply_text(message, parse_mode="Markdown", reply_markup=markup)


def toggle_report_extension_handler(update, context, extension_id):
    """Переключить присутствие расширения в отчёте и перерисовать меню."""
    toggle_report_extension(extension_id)
    show_report_settings_menu(update, context)


def set_all_report_extensions_handler(update, context):
    """Включить все расширения в отчёт."""
    set_report_extensions(list(REPORT_CAPABLE_EXTENSIONS))
    show_report_settings_menu(update, context)


def clear_report_extensions_handler(update, context):
    """Убрать все расширения из отчёта (останутся только данные мониторинга)."""
    set_report_extensions([])
    show_report_settings_menu(update, context)
