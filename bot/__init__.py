"""
/bot/__init__.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ Telegram-Р±РѕС‚Р°
"""

from bot.handlers import (
    get_callback_handlers,
    get_command_handlers,
    get_message_handlers,
)
from bot.menu import main_menu, show_main_menu

__all__ = [
    "get_command_handlers",
    "get_callback_handlers",
    "get_message_handlers",
    "main_menu",
    "show_main_menu",
]
