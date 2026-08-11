"""
/bot/handlers/settings_handlers/users.py
Server Monitoring System v8.64.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Users and personal notification settings UI (Telegram)
Система мониторинга серверов
Версия: 8.64.1
Автор: Александр Суханов (c)
Лицензия: MIT

Два меню:

* «🔔 Мои оповещения» — личные настройки текущего пользователя: получать ли
  отчёт, какие уровни и категории оповещений, личные тихие часы. Доступно
  любому пользователю реестра.
* «👥 Пользователи» — администраторское управление реестром: список
  пользователей, их каналы обмена, включение/выключение, привязка текущего
  чата. Общие настройки сбора данных здесь не трогаются — они едины.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.handlers.base import current_user
from core.users import (
    ALERT_LEVEL_LABELS,
    ALERT_LEVELS,
    CHANNEL_LABELS,
    CHANNEL_TELEGRAM,
    PREF_ALERT_CATEGORIES,
    PREF_ALERT_LEVELS,
    PREF_ALERTS_ENABLED,
    PREF_QUIET_END,
    PREF_QUIET_HOURS_ENABLED,
    PREF_QUIET_START,
    PREF_REPORTS_ENABLED,
    ROLE_ADMIN,
    UserRegistryError,
    alert_categories,
    alert_category_label,
    is_admin_telegram_chat,
    legacy_chat_ids,
    user_registry,
)
from lib.logging import debug_log

# Пометка «пользователь не определён» — чат не привязан ни к кому.
_NO_USER_TEXT = (
    "👤 Этот чат не привязан к пользователю системы.\n\n"
    "Откройте «👥 Пользователи» → «➕ Привязать этот чат», чтобы получать "
    "персональный отчёт и оповещения."
)


def _answer(update):
    query = getattr(update, "callback_query", None)
    if query is not None:
        try:
            query.answer()
        except Exception as exc:  # pragma: no cover - Telegram может ответить ошибкой
            debug_log(f"⚠️ Не удалось ответить на callback: {exc}")
    return query


def _render(update, message, keyboard):
    query = getattr(update, "callback_query", None)
    markup = InlineKeyboardMarkup(keyboard)
    if query is not None:
        query.edit_message_text(message, parse_mode="Markdown", reply_markup=markup)
    else:
        update.message.reply_text(message, parse_mode="Markdown", reply_markup=markup)


def _is_admin(update) -> bool:
    """Может ли текущий чат управлять реестром (см. `is_admin_telegram_chat`)."""
    chat = getattr(update, "effective_chat", None)
    if chat is None:
        return False
    try:
        return is_admin_telegram_chat(chat.id)
    except Exception as exc:  # pragma: no cover - реестр не должен запирать меню
        debug_log(f"⚠️ Не удалось проверить права чата: {exc}")
        return current_user(update) is None


# ---------------------------------------------------------------------------
# Личные оповещения
# ---------------------------------------------------------------------------


def show_my_notifications_menu(update, context):
    """Меню личных настроек доставки текущего пользователя."""
    _answer(update)
    user = current_user(update)
    if user is None:
        _render(
            update,
            _NO_USER_TEXT,
            [
                [InlineKeyboardButton("👥 Пользователи", callback_data="settings_users")],
                [InlineKeyboardButton("↩️ Назад", callback_data="settings_main")],
            ],
        )
        return

    user_id = int(user["id"])
    prefs = user_registry.get_preferences(user_id)
    levels = set(prefs.get(PREF_ALERT_LEVELS) or [])
    categories = set(prefs.get(PREF_ALERT_CATEGORIES) or [])

    reports_mark = "✅" if prefs.get(PREF_REPORTS_ENABLED) else "⬜"
    alerts_mark = "✅" if prefs.get(PREF_ALERTS_ENABLED) else "⬜"
    quiet_mark = "✅" if prefs.get(PREF_QUIET_HOURS_ENABLED) else "⬜"
    quiet_range = f"{int(prefs.get(PREF_QUIET_START) or 0):02d}:00–{int(prefs.get(PREF_QUIET_END) or 0):02d}:00"

    message = (
        f"🔔 *Мои оповещения* — {user.get('display_name') or user['username']}\n\n"
        f"{reports_mark} Утренний/сводный отчёт\n"
        f"{alerts_mark} Оповещения мониторинга\n"
        f"📶 Уровни: {', '.join(sorted(levels)) if levels else '—'}\n"
        f"🧩 Категорий выбрано: {len(categories)} из {len(alert_categories())}\n"
        f"{quiet_mark} Личные тихие часы: {quiet_range}\n\n"
        "Настройки личные — сбор данных общий для всех пользователей."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f"{reports_mark} Получать отчёт", callback_data="user_pref_toggle_reports"
            )
        ],
        [
            InlineKeyboardButton(
                f"{alerts_mark} Получать оповещения", callback_data="user_pref_toggle_alerts"
            )
        ],
    ]
    for level in ALERT_LEVELS:
        mark = "✅" if level in levels else "⬜"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{mark} {ALERT_LEVEL_LABELS.get(level, level)}",
                    callback_data=f"user_pref_level_{level}",
                )
            ]
        )
    keyboard.append(
        [InlineKeyboardButton("🧩 Категории оповещений", callback_data="user_pref_categories")]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                f"{quiet_mark} Тихие часы {quiet_range}",
                callback_data="user_pref_toggle_quiet",
            )
        ]
    )
    keyboard.append([InlineKeyboardButton("🗒️ Состав отчёта", callback_data="settings_report")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )
    _render(update, message, keyboard)


def toggle_user_preference_handler(update, context, preference: str):
    """Переключает булеву личную настройку (отчёт/оповещения/тихие часы)."""
    user = current_user(update)
    if user is None:
        show_my_notifications_menu(update, context)
        return

    key = {
        "reports": PREF_REPORTS_ENABLED,
        "alerts": PREF_ALERTS_ENABLED,
        "quiet": PREF_QUIET_HOURS_ENABLED,
    }.get(preference)
    if key is None:
        show_my_notifications_menu(update, context)
        return

    user_id = int(user["id"])
    current = bool(user_registry.get_preference(user_id, key))
    user_registry.set_preference(user_id, key, not current)
    show_my_notifications_menu(update, context)


def toggle_user_alert_level_handler(update, context, level: str):
    """Включает/выключает уровень оповещений у текущего пользователя."""
    user = current_user(update)
    if user is None or level not in ALERT_LEVELS:
        show_my_notifications_menu(update, context)
        return

    user_id = int(user["id"])
    levels = set(user_registry.get_preference(user_id, PREF_ALERT_LEVELS) or [])
    if level in levels:
        levels.discard(level)
    else:
        levels.add(level)
    user_registry.set_preference(
        user_id, PREF_ALERT_LEVELS, [item for item in ALERT_LEVELS if item in levels]
    )
    show_my_notifications_menu(update, context)


def show_user_categories_menu(update, context):
    """Меню подписки на категории оповещений."""
    _answer(update)
    user = current_user(update)
    if user is None:
        show_my_notifications_menu(update, context)
        return

    user_id = int(user["id"])
    selected = set(user_registry.get_preference(user_id, PREF_ALERT_CATEGORIES) or [])

    message = (
        "🧩 *Категории оповещений*\n\n"
        "Отмеченные категории приходят вам; снятые — не приходят, "
        "но продолжают собираться системой для остальных.\n"
    )

    keyboard = []
    for category in alert_categories():
        mark = "✅" if category in selected else "⬜"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{mark} {alert_category_label(category)}",
                    callback_data=f"user_pref_cat_{category}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton("✅ Все", callback_data="user_pref_cat_all"),
            InlineKeyboardButton("⬜ Очистить", callback_data="user_pref_cat_none"),
        ]
    )
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="settings_my_alerts")])
    _render(update, message, keyboard)


def toggle_user_category_handler(update, context, category: str):
    """Переключает подписку на категорию (или «все»/«очистить»)."""
    user = current_user(update)
    if user is None:
        show_my_notifications_menu(update, context)
        return

    user_id = int(user["id"])
    known = alert_categories()
    if category == "all":
        user_registry.set_preference(user_id, PREF_ALERT_CATEGORIES, list(known))
    elif category == "none":
        user_registry.set_preference(user_id, PREF_ALERT_CATEGORIES, [])
    elif category in known:
        selected = set(user_registry.get_preference(user_id, PREF_ALERT_CATEGORIES) or [])
        if category in selected:
            selected.discard(category)
        else:
            selected.add(category)
        user_registry.set_preference(
            user_id, PREF_ALERT_CATEGORIES, [item for item in known if item in selected]
        )
    show_user_categories_menu(update, context)


# ---------------------------------------------------------------------------
# Управление пользователями (админ)
# ---------------------------------------------------------------------------


def show_users_menu(update, context):
    """Список пользователей реестра."""
    _answer(update)
    if not _is_admin(update):
        _render(
            update,
            "⛔ Управление пользователями доступно только администратору.",
            [[InlineKeyboardButton("↩️ Назад", callback_data="settings_main")]],
        )
        return

    users = user_registry.list_users()
    lines = [
        "👥 *Пользователи*\n",
        "Каждый пользователь получает отчёт и оповещения по своим настройкам "
        "в свои каналы. Настройки сбора данных общие для всех.\n",
    ]

    keyboard = []
    for user in users:
        channels = user_registry.list_channels(user_id=int(user["id"]))
        state_mark = "🟢" if user["enabled"] else "🔴"
        role_mark = " 👑" if user["role"] == ROLE_ADMIN else ""
        lines.append(
            f"{state_mark} *{user['display_name']}*{role_mark} "
            f"(`{user['username']}`) — каналов: {len(channels)}"
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{state_mark} {user['display_name']}{role_mark}",
                    callback_data=f"user_card_{user['id']}",
                )
            ]
        )

    if not users:
        lines.append("_Реестр пуст._")

    # Кто владеет текущим чатом — без этой строки непонятно, от чьего имени
    # работают «Мои оповещения» и состав отчёта.
    chat = getattr(update, "effective_chat", None)
    owner = current_user(update)
    lines.append("")
    if owner is not None:
        owner_role = " 👑" if owner["role"] == ROLE_ADMIN else ""
        lines.append(f"📍 Этот чат: *{owner['display_name']}*{owner_role}")
    else:
        lines.append("📍 Этот чат ни к кому не привязан")
    if chat is not None and str(chat.id) in legacy_chat_ids():
        lines.append("_чат есть в общем списке CHAT_IDS — права администратора сохранены_")

    keyboard.append(
        [InlineKeyboardButton("➕ Привязать этот чат", callback_data="user_link_this_chat")]
    )
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="settings_main"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )
    _render(update, "\n".join(lines), keyboard)


def show_user_card(update, context, user_id: int):
    """Карточка пользователя: каналы, состояние, персональные настройки."""
    _answer(update)
    if not _is_admin(update):
        show_users_menu(update, context)
        return

    user = user_registry.get_user(user_id)
    if not user:
        show_users_menu(update, context)
        return

    prefs = user_registry.get_preferences(int(user["id"]))
    channels = user_registry.list_channels(user_id=int(user["id"]))

    lines = [
        f"👤 *{user['display_name']}* (`{user['username']}`)",
        f"Роль: {'администратор 👑' if user['role'] == ROLE_ADMIN else 'пользователь'}",
        f"Состояние: {'🟢 включён' if user['enabled'] else '🔴 выключен'}",
        "",
        "*Каналы обмена:*",
    ]
    if channels:
        for channel in channels:
            label = CHANNEL_LABELS.get(channel["channel_type"], channel["channel_type"])
            mark = "🟢" if channel["enabled"] else "🔴"
            lines.append(f"{mark} {label}: `{channel['channel_ref']}`")
    else:
        lines.append("_каналов нет — сообщения не доставляются_")

    lines.extend(
        [
            "",
            "*Персональные настройки:*",
            f"• Отчёт: {'да' if prefs.get(PREF_REPORTS_ENABLED) else 'нет'}",
            f"• Оповещения: {'да' if prefs.get(PREF_ALERTS_ENABLED) else 'нет'}",
            f"• Уровни: {', '.join(prefs.get(PREF_ALERT_LEVELS) or []) or '—'}",
            f"• Категорий: {len(prefs.get(PREF_ALERT_CATEGORIES) or [])}",
        ]
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔴 Выключить" if user["enabled"] else "🟢 Включить",
                callback_data=f"user_toggle_{user['id']}",
            )
        ],
        [
            InlineKeyboardButton(
                (
                    "👑 Сделать администратором"
                    if user["role"] != ROLE_ADMIN
                    else "👤 Сделать пользователем"
                ),
                callback_data=f"user_role_{user['id']}",
            )
        ],
        [InlineKeyboardButton("🔗 Привязать этот чат", callback_data=f"user_link_{user['id']}")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data=f"user_delete_{user['id']}")],
        [InlineKeyboardButton("↩️ К списку", callback_data="settings_users")],
    ]
    _render(update, "\n".join(lines), keyboard)


def _alert(update, text: str) -> None:
    """Показывает пользователю всплывающее предупреждение на callback."""
    query = getattr(update, "callback_query", None)
    if query is None:
        return
    try:
        query.answer(text, show_alert=True)
    except Exception as exc:  # pragma: no cover - Telegram может ответить ошибкой
        debug_log(f"⚠️ Не удалось показать предупреждение: {exc}")


def toggle_user_enabled_handler(update, context, user_id: int):
    """Включает/выключает пользователя."""
    if not _is_admin(update):
        show_users_menu(update, context)
        return
    user = user_registry.get_user(user_id)
    if user:
        try:
            user_registry.update_user(user_id, enabled=not user["enabled"])
        except UserRegistryError as exc:
            _alert(update, f"❌ {exc}")
    show_user_card(update, context, user_id)


def toggle_user_role_handler(update, context, user_id: int):
    """Переключает роль пользователя (админ ↔ пользователь)."""
    if not _is_admin(update):
        show_users_menu(update, context)
        return
    user = user_registry.get_user(user_id)
    if user:
        new_role = "user" if user["role"] == ROLE_ADMIN else ROLE_ADMIN
        try:
            user_registry.update_user(user_id, role=new_role)
        except UserRegistryError as exc:
            _alert(update, f"❌ {exc}")
    show_user_card(update, context, user_id)


def delete_user_handler(update, context, user_id: int):
    """Удаляет пользователя вместе с каналами и настройками."""
    if not _is_admin(update):
        show_users_menu(update, context)
        return
    try:
        user_registry.delete_user(user_id)
    except UserRegistryError as exc:
        _alert(update, f"❌ {exc}")
        show_user_card(update, context, user_id)
        return
    show_users_menu(update, context)


def link_current_chat_handler(update, context, user_id=None):
    """Привязывает текущий Telegram-чат к пользователю.

    Без ``user_id`` (кнопка «➕ Привязать этот чат» в списке) чат
    привязывается к НОВОМУ пользователю — это способ завести получателя
    прямо из его чата. Если чат уже кому-то принадлежит, ничего не
    переназначается: открывается карточка владельца. Раньше кнопка молча
    уводила чат у прежнего владельца, и администратор, нажавший её в своём
    чате, терял права на управление реестром.

    С явным ``user_id`` (кнопка «🔗 Привязать этот чат» в карточке) перенос
    выполняется — это осознанное действие администратора.
    """
    query = getattr(update, "callback_query", None)
    chat = getattr(update, "effective_chat", None)
    if chat is None:
        show_users_menu(update, context)
        return

    chat_id = str(chat.id)
    title = getattr(chat, "title", None) or getattr(chat, "username", None) or chat_id

    if not _is_admin(update):
        show_users_menu(update, context)
        return

    if user_id is None:
        owner = user_registry.resolve_user(CHANNEL_TELEGRAM, chat_id)
        if owner is not None:
            if query is not None:
                query.answer(f"Этот чат уже привязан к «{owner['display_name']}»", show_alert=True)
            show_user_card(update, context, int(owner["id"]))
            return

        username = f"tg_{chat_id.lstrip('-')}"
        existing = user_registry.get_user_by_username(username)
        # Чат из общего CHAT_IDS до многопользовательского режима имел полный
        # доступ к настройкам — сохраняем за ним административные права.
        role = ROLE_ADMIN if chat_id in legacy_chat_ids() else "user"
        try:
            user = existing or user_registry.create_user(username, display_name=title, role=role)
        except UserRegistryError as exc:
            if query is not None:
                query.answer(f"❌ {exc}", show_alert=True)
            show_users_menu(update, context)
            return
        user_id = int(user["id"])

    try:
        user_registry.link_channel(user_id, CHANNEL_TELEGRAM, chat_id, title=str(title))
    except UserRegistryError as exc:
        if query is not None:
            query.answer(f"❌ {exc}", show_alert=True)
        show_users_menu(update, context)
        return

    show_user_card(update, context, int(user_id))
