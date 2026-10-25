"""
/bot/handlers/ids_cert_handlers.py
Server Monitoring System v8.67.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram handlers for the IDS / mail certificate monitor extension
Система мониторинга серверов
Версия: 8.67.1
Автор: Александр Суханов (c)
Лицензия: MIT
Telegram-обработчики расширения IDS и сертификата почты: статус, журнал,
справка и подтверждение проблем (останавливает напоминания).
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from extensions.ids_cert_monitor import (
    acknowledge,
    build_help_lines,
    build_history_lines,
    build_status_lines,
    get_open_problems,
)

# Telegram режет сообщения длиннее 4096 символов.
_MAX_MESSAGE_CHARS = 4000


def _clip(text: str) -> str:
    if len(text) <= _MAX_MESSAGE_CHARS:
        return text
    return text[: _MAX_MESSAGE_CHARS - 1] + "…"


def _menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for row in get_open_problems():
        if row.get("acknowledged"):
            continue
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✋ Подтвердить: {row['node']}/CT{row['ct']} {row['family']}",
                    callback_data=f"ids_ack|{row['problem_key']}"[:64],
                )
            ]
        )
    keyboard += [
        [InlineKeyboardButton("🔄 Обновить", callback_data="ids_menu")],
        [InlineKeyboardButton("🕘 Журнал за 30 дней", callback_data="ids_history")],
        [InlineKeyboardButton("📖 Справка по событиям", callback_data="ids_help")],
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("↩️ Назад", callback_data="ids_menu")],
            [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
        ]
    )


def show_menu(update, context, prefix: str = "") -> None:
    query = update.callback_query
    query.answer()
    message = prefix + "\n".join(build_status_lines())
    query.edit_message_text(_clip(message), reply_markup=_menu_keyboard())


def handle_callbacks(update, context, data: str) -> None:
    query = update.callback_query
    if data == "ids_history":
        query.answer()
        query.edit_message_text(
            _clip("\n".join(build_history_lines())), reply_markup=_back_keyboard()
        )
    elif data == "ids_help":
        query.answer()
        query.edit_message_text(_clip("\n".join(build_help_lines())), reply_markup=_back_keyboard())
    elif data.startswith("ids_ack|"):
        key = data.split("|", 1)[1]
        user = getattr(update.effective_user, "username", None) or str(
            getattr(update.effective_user, "id", "")
        )
        if acknowledge(key, by=f"telegram:{user}"):
            prefix = f"✋ Подтверждено: {key} — напоминания остановлены\n\n"
        else:
            prefix = f"ℹ️ {key}: открытой проблемы нет\n\n"
        show_menu(update, context, prefix=prefix)
    else:
        show_menu(update, context)
