"""
/bot/handlers/mail_cert_handlers.py
Server Monitoring System v8.66.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram handlers for the mail server certificate monitor extension
Система мониторинга серверов
Версия: 8.66.0
Автор: Александр Суханов (c)
Лицензия: MIT
Telegram-обработчики расширения мониторинга сертификата почтового сервера
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from extensions.mail_cert_monitor import (
    EVENT_DESCRIPTIONS,
    build_status_lines,
    get_recent_events,
)

# Telegram режет сообщения длиннее 4096 символов.
_MAX_MESSAGE_CHARS = 4000


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔄 Обновить", callback_data="mail_cert_menu")],
            [InlineKeyboardButton("🕘 История событий", callback_data="mail_cert_history")],
            [InlineKeyboardButton("📖 Справка по событиям", callback_data="mail_cert_help")],
            [
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("↩️ Назад", callback_data="mail_cert_menu")],
            [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
        ]
    )


def _clip(text: str) -> str:
    if len(text) <= _MAX_MESSAGE_CHARS:
        return text
    return text[: _MAX_MESSAGE_CHARS - 1] + "…"


def show_menu(update, context):
    query = update.callback_query
    query.answer()
    message = "\n".join(build_status_lines())
    query.edit_message_text(_clip(message), reply_markup=_menu_keyboard())


def show_history(update, context):
    query = update.callback_query
    query.answer()
    events = get_recent_events(limit=20)
    lines = ["🕘 История событий сертификата почты (последние 20)", ""]
    if not events:
        lines.append("⚪ Писем CERT ещё не было.")
    for ev in events:
        icon = {"OK": "✅", "WARN": "⚠️", "CRIT": "🚨"}.get(str(ev.get("level")), "❔")
        lines.append(
            f"{icon} {str(ev.get('received_at') or '')[:16]} · {ev.get('host_name')} "
            f"CT{ev.get('ct_id')} · {ev.get('event')}"
        )
    query.edit_message_text(_clip("\n".join(lines)), reply_markup=_back_keyboard())


def show_help(update, context):
    query = update.callback_query
    query.answer()
    lines = [
        "📖 Письма скрипта развёртывания сертификата почты",
        "",
        "Тема: CERT <OK|WARN|CRIT> <хост> CT<id> <СОБЫТИЕ> [key=value…]",
        "",
    ]
    for event, description in EVENT_DESCRIPTIONS.items():
        lines.append(f"• {event} — {description}")
    lines.extend(
        [
            "",
            "Скрипт молчит, пока всё в порядке. Каждое письмо — оповещение. "
            "Если до конца срока из последнего DEPLOYED осталось ≤ 7 дней, а "
            "писем нет, мониторинг предупредит сам.",
        ]
    )
    query.edit_message_text(_clip("\n".join(lines)), reply_markup=_back_keyboard())


def handle_callbacks(update, context, data: str) -> None:
    if data == "mail_cert_history":
        show_history(update, context)
    elif data == "mail_cert_help":
        show_help(update, context)
    else:
        show_menu(update, context)
