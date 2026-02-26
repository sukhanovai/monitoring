"""
/bot/handlers/extensions.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
UI handlers for managing extensions
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
UI-РѕР±СЂР°Р±РѕС‚С‡РёРєРё СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS
from bot.handlers.base import check_access, deny_access
from lib.logging import debug_log


def show_extensions_menu(update, context):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё"""
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id

    extensions_status = extension_manager.get_extensions_status()

    message = "рџ› пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё*\n\n"
    message += "рџ“Љ *РЎС‚Р°С‚СѓСЃ СЂР°СЃС€РёСЂРµРЅРёР№:*\n\n"

    keyboard = []

    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']

        status_icon = "рџџў" if enabled else "рџ”ґ"
        toggle_text = "рџ”ґ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "рџџў Р’РєР»СЋС‡РёС‚СЊ"

        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   РЎС‚Р°С‚СѓСЃ: {'Р’РєР»СЋС‡РµРЅРѕ' if enabled else 'РћС‚РєР»СЋС‡РµРЅРѕ'}\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}",
                callback_data=f'ext_toggle_{ext_id}'
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("рџ“Љ Р’РєР»СЋС‡РёС‚СЊ РІСЃРµ", callback_data='ext_enable_all')],
        [InlineKeyboardButton("рџ“‹ РћС‚РєР»СЋС‡РёС‚СЊ РІСЃРµ", callback_data='ext_disable_all')],
        [
            InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
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
    """Callback-РѕР±СЂР°Р±РѕС‚С‡РёРє СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё"""
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
    query.answer(f"вњ… Р’РєР»СЋС‡РµРЅРѕ {enabled}/{len(AVAILABLE_EXTENSIONS)} СЂР°СЃС€РёСЂРµРЅРёР№")


def _disable_all_extensions(query):
    disabled = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled += 1
    query.answer(f"вњ… РћС‚РєР»СЋС‡РµРЅРѕ {disabled}/{len(AVAILABLE_EXTENSIONS)} СЂР°СЃС€РёСЂРµРЅРёР№")
