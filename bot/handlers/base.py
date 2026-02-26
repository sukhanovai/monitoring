"""
/bot/handlers/base.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Basic functions: access, universal responses, general checks
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р‘Р°Р·РѕРІС‹Рµ С„СѓРЅРєС†РёРё: РґРѕСЃС‚СѓРї, СѓРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Рµ РѕС‚РІРµС‚С‹, РѕР±С‰РёРµ РїСЂРѕРІРµСЂРєРё
"""

from config.settings import CHAT_IDS as DEFAULT_CHAT_IDS
from config.db_settings import CHAT_IDS as DB_CHAT_IDS
from lib.logging import debug_log

def check_access(update):
    """
    РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїР°:
    1. РЎРЅР°С‡Р°Р»Р° Р±РµСЂС‘Рј CHAT_IDS РёР· Р‘Р”
    2. Р•СЃР»Рё РІ Р‘Р” РїСѓСЃС‚Рѕ вЂ” РёСЃРїРѕР»СЊР·СѓРµРј settings.py
    """
    chat_id = str(update.effective_chat.id)

    allowed_ids = DB_CHAT_IDS if DB_CHAT_IDS else DEFAULT_CHAT_IDS

    debug_log(
        f"Access check | chat_id={chat_id} | allowed={allowed_ids}"
    )

    return chat_id in allowed_ids

def deny_access(update):
    if update.message:
        update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЌС‚РѕРіРѕ Р±РѕС‚Р°")
    elif update.callback_query:
        update.callback_query.answer("в›” РќРµС‚ РїСЂР°РІ", show_alert=True)


def safe_reply(update, text, **kwargs):
    if update.message:
        update.message.reply_text(text, **kwargs)
    elif update.callback_query:
        update.callback_query.edit_message_text(text, **kwargs)
