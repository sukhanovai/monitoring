"""
/bot/handlers/extensions.py
Server Monitoring System v8.62.24
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
UI handlers for managing extensions
Система мониторинга серверов
Версия: 8.62.24
Автор: Александр Суханов (c)
Лицензия: MIT
UI-обработчики управления расширениями
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS
from bot.handlers.base import check_access, deny_access
from lib.logging import debug_log


def show_extensions_menu(update, context):
    """Показывает меню управления расширениями"""
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id

    extensions_status = extension_manager.get_extensions_status()

    message = "🛠️ *Управление расширениями*\n\n"
    message += "📊 *Статус расширений:*\n\n"

    keyboard = []

    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']

        status_icon = "🟢" if enabled else "🔴"
        toggle_text = "🔴 Выключить" if enabled else "🟢 Включить"

        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   Статус: {'Включено' if enabled else 'Отключено'}\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}",
                callback_data=f'ext_toggle_{ext_id}'
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("📊 Включить все", callback_data='ext_enable_all')],
        [InlineKeyboardButton("📋 Отключить все", callback_data='ext_disable_all')],
        [
            InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ]
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


def extensions_callback_handler(update, context):
    """Callback-обработчик управления расширениями"""
    query = update.callback_query
    data = query.data
    query.answer()

    if data == 'ext_enable_all':
        _enable_all_extensions(query)
        show_extensions_menu(update, context)

    elif data == 'ext_disable_all':
        _disable_all_extensions(query)
        show_extensions_menu(update, context)

    elif data.startswith('ext_toggle_'):
        extension_id = data.replace('ext_toggle_', '')
        success, message = extension_manager.toggle_extension(extension_id)
        if success:
            query.answer(message)
            show_extensions_menu(update, context)
        else:
            query.answer(message, show_alert=True)


def _enable_all_extensions(query):
    enabled = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.enable_extension(ext_id)
        if success:
            enabled += 1
    query.answer(f"✅ Включено {enabled}/{len(AVAILABLE_EXTENSIONS)} расширений")


def _disable_all_extensions(query):
    disabled = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled += 1
    query.answer(f"✅ Отключено {disabled}/{len(AVAILABLE_EXTENSIONS)} расширений")
