"""
/bot/handlers/base.py
Server Monitoring System v4.14.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Basic functions: access, universal responses, general checks
Система мониторинга серверов
Версия: 4.14.0
Автор: Александр Суханов (c)
Лицензия: MIT
Базовые функции: доступ, универсальные ответы, общие проверки
"""

from config.settings import CHAT_IDS
from lib.logging import debug_log


def check_access(update):
    chat_id = update.effective_chat.id
    return str(chat_id) in CHAT_IDS


def deny_access(update):
    if update.message:
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
    elif update.callback_query:
        update.callback_query.answer("⛔ Нет прав", show_alert=True)


def safe_reply(update, text, **kwargs):
    if update.message:
        update.message.reply_text(text, **kwargs)
    elif update.callback_query:
        update.callback_query.edit_message_text(text, **kwargs)
