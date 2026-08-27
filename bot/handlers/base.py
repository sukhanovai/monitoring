"""
/bot/handlers/base.py
Server Monitoring System v8.65.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Basic functions: access, universal responses, general checks
Система мониторинга серверов
Версия: 8.65.1
Автор: Александр Суханов (c)
Лицензия: MIT
Базовые функции: доступ, универсальные ответы, общие проверки
"""

from config.db_settings import CHAT_IDS as DB_CHAT_IDS
from config.settings import CHAT_IDS as DEFAULT_CHAT_IDS
from lib.logging import debug_log


def current_user(update):
    """Пользователь реестра, которому принадлежит чат апдейта (или None)."""
    try:
        from core.users import resolve_telegram_user

        chat = getattr(update, "effective_chat", None)
        if chat is None:
            return None
        return resolve_telegram_user(str(chat.id))
    except Exception as exc:  # pragma: no cover - реестр не должен ронять бота
        debug_log(f"⚠️ Не удалось определить пользователя чата: {exc}")
        return None


def current_user_id(update):
    """id пользователя реестра для чата апдейта (или None)."""
    user = current_user(update)
    return int(user["id"]) if user else None


def check_access(update):
    """
    Проверка доступа:
    1. Чат привязан к включённому пользователю реестра (`core/users.py`)
    2. Иначе — legacy-список CHAT_IDS из БД
    3. Если в БД пусто — используем settings.py
    """
    chat_id = str(update.effective_chat.id)

    user = current_user(update)
    if user and user.get("enabled"):
        debug_log(f"Access check | chat_id={chat_id} | пользователь={user['username']}")
        return True

    allowed_ids = DB_CHAT_IDS if DB_CHAT_IDS else DEFAULT_CHAT_IDS

    debug_log(f"Access check | chat_id={chat_id} | allowed={allowed_ids}")

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


# Спецсимволы legacy-Markdown Telegram (parse_mode="Markdown").
_MARKDOWN_SPECIAL_CHARS = "_*[`"


def escape_md(value) -> str:
    """Экранирует данные пользователя для parse_mode="Markdown".

    Имена, логины и идентификаторы каналов приходят извне: Telegram-логин
    вида ``ivan_petrov`` или название чата со звёздочкой ломали разметку
    целого меню («Can't parse entities»), и сообщение вообще не доходило.
    Собственная реализация вместо `telegram.utils.helpers.escape_markdown`
    — чтобы не зависеть от версии python-telegram-bot и работать в тестах.
    """
    text = str(value if value is not None else "")
    return "".join(f"\\{char}" if char in _MARKDOWN_SPECIAL_CHARS else char for char in text)


def render_markdown(update, text, reply_markup=None):
    """Показывает Markdown-сообщение с фолбэком на обычный текст.

    Если Telegram не смог разобрать разметку (неэкранированный спецсимвол
    в данных), сообщение отправляется без parse_mode — пользователь видит
    меню, пусть и без форматирования, вместо пустого экрана и ошибки
    в логе.
    """
    query = getattr(update, "callback_query", None)

    def _send(parse_mode):
        if query is not None:
            query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        else:
            update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)

    try:
        _send("Markdown")
    except Exception as exc:
        if "parse entities" not in str(exc).lower():
            raise
        debug_log(f"⚠️ Markdown не разобран, повтор без разметки: {exc}")
        _send(None)
