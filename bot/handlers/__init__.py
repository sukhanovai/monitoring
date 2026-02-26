"""
/bot/handlers/__init__.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers package exports
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р­РєСЃРїРѕСЂС‚ РІСЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹С… С„СѓРЅРєС†РёР№ РґР»СЏ СЂРµРіРёСЃС‚СЂР°С†РёРё РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ
"""

import importlib

from telegram.ext import CallbackQueryHandler, CommandHandler, Filters, MessageHandler

from bot.handlers.callbacks import callback_router
from bot.handlers.commands import (
    check_command,
    control_panel_command,
    help_command,
    report_command,
    silent_mode_command,
    start_command,
    status_command,
)


def get_command_handlers():
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ РєРѕРјР°РЅРґ."""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("check", check_command),
        CommandHandler("status", status_command),
        CommandHandler("silent", silent_mode_command),
        CommandHandler("control", control_panel_command),
        CommandHandler("report", report_command),
    ]


def get_callback_handlers():
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ callback-Р·Р°РїСЂРѕСЃРѕРІ."""
    return [CallbackQueryHandler(callback_router)]


def get_message_handlers():
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕР±СЂР°Р±РѕС‚С‡РёРєРё С‚РµРєСЃС‚РѕРІС‹С… СЃРѕРѕР±С‰РµРЅРёР№.

    РРјРїРѕСЂС‚РёСЂСѓРµРј Р»РµРЅРёРІРѕ, С‡С‚РѕР±С‹ РЅРµ РїР°РґР°С‚СЊ, РµСЃР»Рё РјРѕРґСѓР»СЊ РЅР°СЃС‚СЂРѕРµРє РЅРµРґРѕСЃС‚СѓРїРµРЅ.
    """
    if importlib.util.find_spec("bot.handlers.settings_handlers") is None:
        return []

    from bot.handlers.settings_handlers import handle_setting_value

    return [MessageHandler(Filters.text & ~Filters.command, handle_setting_value)]


__all__ = [
    "get_command_handlers",
    "get_callback_handlers",
    "get_message_handlers",
]
