"""
/bot/handlers/base.py
Server Monitoring System v8.2.52
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Basic functions: access, universal responses, general checks
Система мониторинга серверов
Версия: 8.2.52
Автор: Александр Суханов (c)
Лицензия: MIT
Базовые функции: доступ, универсальные ответы, общие проверки
"""

from config.settings import CHAT_IDS as DEFAULT_CHAT_IDS
from config.db_settings import CHAT_IDS as DB_CHAT_IDS
from lib.logging import debug_log

def check_access(update):
    """
    Проверка доступа:
    1. Сначала берём CHAT_IDS из БД
    2. Если в БД пусто — используем settings.py
    """
    chat_id = str(update.effective_chat.id)

    allowed_ids = DB_CHAT_IDS if DB_CHAT_IDS else DEFAULT_CHAT_IDS

    debug_log(
        f"Access check | chat_id={chat_id} | allowed={allowed_ids}"
    )

    return chat_id in allowed_ids

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
