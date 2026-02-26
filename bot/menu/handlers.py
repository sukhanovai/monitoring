"""
/bot/menu/handlers.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot menu handlers
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РћР±СЂР°Р±РѕС‚С‡РёРєРё РјРµРЅСЋ Р±РѕС‚Р°
"""

from pathlib import Path
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from bot.menu.builder import main_menu
from bot.handlers.base import check_access as base_check_access, deny_access
from extensions.extension_manager import extension_manager
from lib.logging import debug_log
from lib.utils import progress_bar, format_duration
from config.db_settings import (
    DEBUG_MODE,
    LOG_DIR,
    DATA_DIR,
    DEBUG_LOG_FILE,
    BOT_DEBUG_LOG_FILE,
    MAIL_MONITOR_LOG_FILE,
)
from modules.targeted_checks import targeted_checks


def show_main_menu(update, context):
    if not base_check_access(update):
        deny_access(update)
        return

    config = get_config()
    text = "рџ¤– *РЎРµСЂРІРµСЂРЅС‹Р№ РјРѕРЅРёС‚РѕСЂРёРЅРі*\n"
    if getattr(config, "APP_VERSION", None):
        text += f"рџ”– *Р’РµСЂСЃРёСЏ:* {config.APP_VERSION}\n"
    text += "\nвњ… РЎРёСЃС‚РµРјР° Р°РєС‚РёРІРЅР°"

    if update.message:
        update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=main_menu(extension_manager)
        )
    else:
        update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=main_menu(extension_manager)
        )

# Р›РµРЅРёРІС‹Рµ РёРјРїРѕСЂС‚С‹ РґР»СЏ РЅР°СЃС‚СЂРѕРµРє
def lazy_import_settings_handler():
    """Р›РµРЅРёРІР°СЏ Р·Р°РіСЂСѓР·РєР° РѕР±СЂР°Р±РѕС‚С‡РёРєР° РЅР°СЃС‚СЂРѕРµРє"""
    try:
        from bot.handlers.settings_handlers import settings_callback_handler
        return settings_callback_handler
    except ImportError as e:
        print(f"вќЊ РћС€РёР±РєР° РёРјРїРѕСЂС‚Р° settings_callback_handler: {e}")
        # Р—Р°РіР»СѓС€РєР° РЅР° СЃР»СѓС‡Р°Р№ РѕС€РёР±РєРё
        def fallback_handler(update, context):
            query = update.callback_query
            query.answer("вљ™пёЏ РњРѕРґСѓР»СЊ РЅР°СЃС‚СЂРѕРµРє РІСЂРµРјРµРЅРЅРѕ РЅРµРґРѕСЃС‚СѓРїРµРЅ")
        return fallback_handler

# РџРѕР»СѓС‡Р°РµРј РѕР±СЂР°Р±РѕС‚С‡РёРє РЅР°СЃС‚СЂРѕРµРє
settings_callback_handler = lazy_import_settings_handler()

def lazy_import(module_name, attribute_name=None):
    """Р›РµРЅРёРІР°СЏ Р·Р°РіСЂСѓР·РєР° РјРѕРґСѓР»РµР№ СЃ РїРѕРґРґРµСЂР¶РєРѕР№ СЃРѕСЃС‚Р°РІРЅС‹С… РїСѓС‚РµР№"""
    def import_func():
        # Р”Р»СЏ СЃРѕСЃС‚Р°РІРЅС‹С… РїСѓС‚РµР№ С‚РёРїР° 'config.db_settings'
        if '.' in module_name:
            parts = module_name.split('.')
            # РРјРїРѕСЂС‚РёСЂСѓРµРј РєРѕСЂРЅРµРІРѕР№ РјРѕРґСѓР»СЊ
            module = __import__(parts[0])
            # РџСЂРѕС…РѕРґРёРј РїРѕ РІР»РѕР¶РµРЅРЅС‹Рј РјРѕРґСѓР»СЏРј
            for part in parts[1:]:
                module = getattr(module, part)
        else:
            # РћР±С‹С‡РЅС‹Р№ РёРјРїРѕСЂС‚
            module = __import__(module_name, fromlist=[attribute_name] if attribute_name else [])
        
        return getattr(module, attribute_name) if attribute_name else module
    return import_func

# Р›РµРЅРёРІС‹Рµ РёРјРїРѕСЂС‚С‹ РєРѕРЅС„РёРіР°
get_config = lazy_import('config.db_settings')
get_chat_ids = lazy_import('config.db_settings', 'CHAT_IDS')
get_telegram_token = lazy_import('config.db_settings', 'TELEGRAM_TOKEN')

# Р›РµРЅРёРІС‹Рµ РёРјРїРѕСЂС‚С‹ СѓС‚РёР»РёС‚
get_debug_log = lambda: debug_log
get_progress_bar = lambda: progress_bar
get_extension_manager = lazy_import('extensions.extension_manager', 'extension_manager')

def setup_menu(bot):
    """РќР°СЃС‚СЂРѕР№РєР° РјРµРЅСЋ Р±РѕС‚Р° СЃ Р»РµРЅРёРІРѕР№ Р·Р°РіСЂСѓР·РєРѕР№ СЂР°СЃС€РёСЂРµРЅРёР№"""
    try:
        commands = [
            BotCommand("start", "Р—Р°РїСѓСЃРє Р±РѕС‚Р°"),
            BotCommand("check", "РџСЂРѕРІРµСЂРёС‚СЊ СЃРµСЂРІРµСЂС‹"),
            BotCommand("status", "РЎС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"),
            BotCommand("servers", "РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ"),
            BotCommand("report", "Р•Р¶РµРґРЅРµРІРЅС‹Р№ РѕС‚С‡РµС‚"),
            BotCommand("stats", "РЎС‚Р°С‚РёСЃС‚РёРєР°"),
            BotCommand("control", "РЈРїСЂР°РІР»РµРЅРёРµ"),
            BotCommand("diagnose_ssh", "Р”РёР°РіРЅРѕСЃС‚РёРєР° SSH"),
            BotCommand("silent", "РўРёС…РёР№ СЂРµР¶РёРј"),
            BotCommand("extensions", "рџ› пёЏ РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё"),
            BotCommand("settings", "вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєР°РјРё"),
            BotCommand("debug", "рџђ› РЈРїСЂР°РІР»РµРЅРёРµ РѕС‚Р»Р°РґРєРѕР№"),
            BotCommand("help", "РџРѕРјРѕС‰СЊ"),
            BotCommand("check_server", "рџ”Ќ РџСЂРѕРІРµСЂРёС‚СЊ РѕРґРёРЅ СЃРµСЂРІРµСЂ"),
        ]
        
        # Р”РёРЅР°РјРёС‡РµСЃРєРѕРµ РґРѕР±Р°РІР»РµРЅРёРµ РєРѕРјР°РЅРґ СЂР°СЃС€РёСЂРµРЅРёР№
        extension_manager = get_extension_manager()
        if extension_manager.is_extension_enabled('backup_monitor'):
            commands.extend([
                BotCommand("backup", "рџ“Љ Р‘СЌРєР°РїС‹"),
                BotCommand("backup_search", "рџ”Ќ РџРѕРёСЃРє Р±СЌРєР°РїРѕРІ"),
                BotCommand("backup_help", "вќ“ РџРѕРјРѕС‰СЊ РїРѕ Р±СЌРєР°РїР°Рј"),
            ])
        
        if extension_manager.is_extension_enabled('database_backup_monitor'):
            commands.append(BotCommand("db_backups", "рџ—ѓпёЏ Р‘СЌРєР°РїС‹ Р‘Р”"))

        if extension_manager.is_extension_enabled('resource_monitor'):
            commands.append(BotCommand("check_res", "рџ“Љ Р РµСЃСѓСЂСЃС‹ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"))
        
        bot.set_my_commands(commands)
        debug_log("вњ… РњРµРЅСЋ РЅР°СЃС‚СЂРѕРµРЅРѕ СѓСЃРїРµС€РЅРѕ")
        return True
    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РЅР°СЃС‚СЂРѕР№РєРё РјРµРЅСЋ: {e}")
        return False

def legacy_check_access(chat_id):
    """РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїР° Рє Р±РѕС‚Сѓ (legacy)"""
    config = get_config()
    return str(chat_id) in config.CHAT_IDS

def start_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /start СЃ РѕС‚Р»Р°РґРѕС‡РЅРѕР№ РёРЅС„РѕСЂРјР°С†РёРµР№"""
    if not legacy_check_access(update.effective_chat.id):
        # Р”Р»СЏ callback Рё РѕР±С‹С‡РЅС‹С… СЃРѕРѕР±С‰РµРЅРёР№
        if update.message:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЌС‚РѕРіРѕ Р±РѕС‚Р°")
        elif update.callback_query:
            update.callback_query.answer("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ")
            update.callback_query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЌС‚РѕРіРѕ Р±РѕС‚Р°")
        return

    keyboard = [
        [InlineKeyboardButton("рџЊ… РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚", callback_data='daily_report')],
        [InlineKeyboardButton("рџ”„ РџСЂРѕРІРµСЂРёС‚СЊ РІСЃРµ СЃРµСЂРІРµСЂС‹", callback_data='manual_check')],
        [InlineKeyboardButton("рџ”Ќ РџСЂРѕРІРµСЂРёС‚СЊ РѕРґРёРЅ СЃРµСЂРІРµСЂ", callback_data='show_availability_menu')],
        [InlineKeyboardButton("рџђ› РћС‚Р»Р°РґРєР°", callback_data='debug_menu')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.insert(1, [InlineKeyboardButton("рџ“Љ РџСЂРѕРІРµСЂРёС‚СЊ РІСЃРµ СЂРµСЃСѓСЂСЃС‹", callback_data='check_resources')])
        keyboard.insert(3, [InlineKeyboardButton("рџ“€ Р РµСЃСѓСЂСЃС‹ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°", callback_data='show_resources_menu')])
   
    extension_manager = get_extension_manager()
    if (
        extension_manager.is_extension_enabled('backup_monitor')
        or extension_manager.is_extension_enabled('database_backup_monitor')
        or extension_manager.is_extension_enabled('mail_backup_monitor')
        or extension_manager.is_extension_enabled('stock_load_monitor')
    ):
        keyboard.append([InlineKeyboardButton("рџ’ѕ Р‘СЌРєР°РїС‹", callback_data='backup_main')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“¦ РћСЃС‚Р°С‚РєРё 1РЎ", callback_data='backup_stock_loads')])
    
    keyboard.extend([
        [InlineKeyboardButton("рџ› пёЏ РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё", callback_data='extensions_menu')],
        [InlineKeyboardButton("рџЋ›пёЏ РЈРїСЂР°РІР»РµРЅРёРµ", callback_data='control_panel')],
        [InlineKeyboardButton("вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ РЅР°СЃС‚СЂРѕР№РєР°РјРё", callback_data='settings_main')],
        [InlineKeyboardButton("в„№пёЏ Рћ Р±РѕС‚Рµ", callback_data='about_bot')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')] 
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    config = get_config()
    welcome_text = "рџ¤– *РЎРµСЂРІРµСЂРЅС‹Р№ РјРѕРЅРёС‚РѕСЂРёРЅРі*\n"
    if getattr(config, "APP_VERSION", None):
        welcome_text += f"рџ”– *Р’РµСЂСЃРёСЏ:* {config.APP_VERSION}\n"
    welcome_text += "\nвњ… РЎРёСЃС‚РµРјР° СЂР°Р±РѕС‚Р°РµС‚\n\n"
    
    # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РѕС‚Р»Р°РґРєРµ
    try:
        welcome_text += f"рџђ› *Р РµР¶РёРј РѕС‚Р»Р°РґРєРё:* {'рџџў Р’РљР›' if DEBUG_MODE else 'рџ”ґ Р’Р«РљР›'}\n"
    except ImportError:
        welcome_text += "рџђ› *Р РµР¶РёРј РѕС‚Р»Р°РґРєРё:* рџ”ґ РќРµРґРѕСЃС‚СѓРїРµРЅ\n"
    
    if extension_manager.is_extension_enabled('web_interface'):
        welcome_text += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* http://192.168.20.2:5000\n"
        welcome_text += "_*РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ РІ Р»РѕРєР°Р»СЊРЅРѕР№ СЃРµС‚Рё_\n"
    else:
        welcome_text += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* рџ”ґ РѕС‚РєР»СЋС‡РµРЅ\n"
    
    # РћС‚РїСЂР°РІРєР° СЃРѕРѕР±С‰РµРЅРёСЏ РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ С‚РёРїР° РѕР±РЅРѕРІР»РµРЅРёСЏ
    if update.message:
        update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.edit_message_text(
            welcome_text, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )

def show_about_bot(update, context):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЃРІРµРґРµРЅРёСЏ Рѕ Р±РѕС‚Рµ"""
    if not base_check_access(update):
        deny_access(update)
        return

    config = get_config()
    about_text = "в„№пёЏ *Рћ Р±РѕС‚Рµ*\n\n"
    if getattr(config, "APP_VERSION", None):
        about_text += f"рџ”– *Р’РµСЂСЃРёСЏ:* {config.APP_VERSION}\n"
    about_text += (
        "рџ‘¤ *Р Р°Р·СЂР°Р±РѕС‚С‡РёРє:* РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ\n"
        "вњ‰пёЏ *РЎРІСЏР·СЊ:* aleksandr.i.sukhanov@gmail.com\n"
        "рџ“„ *Р›РёС†РµРЅР·РёСЏ:* MIT\n"
        "рџ›  *РќР°Р·РЅР°С‡РµРЅРёРµ:* РјРѕРЅРёС‚РѕСЂРёРЅРі РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё СЃРµСЂРІРµСЂРѕРІ.\n"
        "вћ• *Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ:* СЂРµСЃСѓСЂСЃС‹, Р±СЌРєР°РїС‹, СЃР±РѕСЂ Рё РїСЂРѕРІРµСЂРєР° РґР°РЅРЅС‹С… РїРѕ РѕСЃС‚Р°С‚РєР°Рј С‚РѕРІР°СЂРѕРІ РґР»СЏ Р‘Р”.\n"
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
    ])

    if update.message:
        update.message.reply_text(about_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.edit_message_text(
            about_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

def help_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /help"""
    if not legacy_check_access(update.effective_chat.id):
        return

    help_text = (
        "рџ¤– *РџРѕРјРѕС‰СЊ РїРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіСѓ*\n\n"
        "*РћСЃРЅРѕРІРЅС‹Рµ РєРѕРјР°РЅРґС‹:*\n"
        "вЂў `/start` - Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ\n"
        "вЂў `/check` - Р‘С‹СЃС‚СЂР°СЏ РїСЂРѕРІРµСЂРєР° СЃРµСЂРІРµСЂРѕРІ\n"
        "вЂў `/servers` - РЎРїРёСЃРѕРє РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ\n"
        "вЂў `/control` - РЈРїСЂР°РІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј\n"
        "вЂў `/extensions` - РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё\n"
        "вЂў `/debug` - РЈРїСЂР°РІР»РµРЅРёРµ РѕС‚Р»Р°РґРєРѕР№ рџ†•\n\n"
        "*Р”РёР°РіРЅРѕСЃС‚РёРєР°:*\n"
        "вЂў `/diagnose_ssh <ip>` - РџСЂРѕРІРµСЂРєР° SSH РїРѕРґРєР»СЋС‡РµРЅРёСЏ\n"
        "вЂў `/silent` - РЎС‚Р°С‚СѓСЃ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°\n\n"
        "*РћС‚С‡РµС‚С‹:*\n"
        "вЂў `/report` - РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅР°СЏ РѕС‚РїСЂР°РІРєР° СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°\n"
        "вЂў `/stats` - РЎС‚Р°С‚РёСЃС‚РёРєР° СЂР°Р±РѕС‚С‹\n\n"
    )
    
    # Р”РѕР±Р°РІР»СЏРµРј РєРѕРјР°РЅРґС‹ Р±СЌРєР°РїРѕРІ С‚РѕР»СЊРєРѕ РµСЃР»Рё СЂР°СЃС€РёСЂРµРЅРёРµ РІРєР»СЋС‡РµРЅРѕ
    extension_manager = get_extension_manager()
    if extension_manager.is_extension_enabled('backup_monitor'):
        help_text += "*Р‘СЌРєР°РїС‹ Proxmox:*\n"
        help_text += "вЂў `/backup` - РЎС‚Р°С‚СѓСЃ Р±СЌРєР°РїРѕРІ\n"
        help_text += "вЂў `/backup_search` - РџРѕРёСЃРє РїРѕ Р±СЌРєР°РїР°Рј\n"
        help_text += "вЂў `/backup_help` - РџРѕРјРѕС‰СЊ РїРѕ Р±СЌРєР°РїР°Рј\n\n"
    
    help_text += "*Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:*\n"
    if extension_manager.is_extension_enabled('web_interface'):
        help_text += "рџЊђ http://192.168.20.2:5000\n"
        help_text += "_*РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ РІ Р»РѕРєР°Р»СЊРЅРѕР№ СЃРµС‚Рё_\n\n"
    else:
        help_text += "рџ”ґ Р’ РЅР°СЃС‚РѕСЏС‰РµРµ РІСЂРµРјСЏ РѕС‚РєР»СЋС‡РµРЅ\n\n"
    
    help_text += "*РСЃРїРѕР»СЊР·СѓР№С‚Рµ РєРЅРѕРїРєРё РјРµРЅСЋ РґР»СЏ СѓРґРѕР±РЅРѕРіРѕ СѓРїСЂР°РІР»РµРЅРёСЏ*"
    
    update.message.reply_text(help_text, parse_mode='Markdown')

def main_menu_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґР»СЏ РіР»Р°РІРЅРѕРіРѕ РјРµРЅСЋ"""
    return start_command(update, context)

def monitor_main_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґР»СЏ РіР»Р°РІРЅРѕРіРѕ РјРµРЅСЋ"""
    return start_command(update, context)

# Р—Р°РіР»СѓС€РєРё РґР»СЏ РєРѕРјР°РЅРґ (РёРјРїРѕСЂС‚С‹ РІРЅСѓС‚СЂРё С„СѓРЅРєС†РёР№ С‡С‚РѕР±С‹ РёР·Р±РµР¶Р°С‚СЊ С†РёРєР»РёС‡РµСЃРєРёС… РёРјРїРѕСЂС‚РѕРІ)
def check_command(update, context):
    from core.monitor_core import manual_check_handler
    return manual_check_handler(update, context)

def status_command(update, context):
    from core.monitor_core import monitor_status
    return monitor_status(update, context)

def silent_command(update, context):
    from core.monitor_core import silent_command as silent_cmd
    return silent_cmd(update, context)

def control_command(update, context):
    from core.monitor_core import control_command as control_cmd
    return control_cmd(update, context)

def servers_command(update, context):
    from extensions.server_checks import servers_command as servers_cmd
    return servers_cmd(update, context)

def report_command(update, context):
    """РљРѕРјР°РЅРґР° РґР»СЏ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕР№ РѕС‚РїСЂР°РІРєРё СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°"""
    from core.monitor_core import send_morning_report_handler
    return send_morning_report_handler(update, context)

def stats_command(update, context):
    from lib.monitoring_utils import stats_command as stats_cmd
    return stats_cmd(update, context)

def diagnose_ssh_command(update, context):
    from lib.monitoring_utils import diagnose_ssh_command as diagnose_cmd
    return diagnose_cmd(update, context)

def backup_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /backup"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "вќЊ Р¤СѓРЅРєС†РёРѕРЅР°Р» РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡РµРЅ. "
            "Р’РєР»СЋС‡РёС‚Рµ СЂР°СЃС€РёСЂРµРЅРёРµ 'рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox' РІ СЂР°Р·РґРµР»Рµ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ› пёЏ РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё", callback_data='extensions_menu')]
            ])
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_command as backup_cmd
    return backup_cmd(update, context)

def backup_search_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /backup_search"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "вќЊ Р¤СѓРЅРєС†РёРѕРЅР°Р» РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡РµРЅ. "
            "Р’РєР»СЋС‡РёС‚Рµ СЂР°СЃС€РёСЂРµРЅРёРµ 'рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox' РІ СЂР°Р·РґРµР»Рµ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё."
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_search_command as backup_search_cmd
    return backup_search_cmd(update, context)

def backup_help_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /backup_help"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "вќЊ Р¤СѓРЅРєС†РёРѕРЅР°Р» РјРѕРЅРёС‚РѕСЂРёРЅРіР° Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡РµРЅ. "
            "Р’РєР»СЋС‡РёС‚Рµ СЂР°СЃС€РёСЂРµРЅРёРµ 'рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox' РІ СЂР°Р·РґРµР»Рµ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё."
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_help_command as backup_help_cmd
    return backup_help_cmd(update, context)

def fix_monitor_command(update, context):
    """РљРѕРјР°РЅРґР° РґР»СЏ РёСЃРїСЂР°РІР»РµРЅРёСЏ СЃС‚Р°С‚СѓСЃР° СЃРµСЂРІРµСЂР° РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    if not legacy_check_access(update.effective_chat.id):
        update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return

    try:
        # Р”РёРЅР°РјРёС‡РµСЃРєРёР№ РёРјРїРѕСЂС‚ С‡С‚РѕР±С‹ РёР·Р±РµР¶Р°С‚СЊ С†РёРєР»РёС‡РµСЃРєРёС… Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
        from core.monitor_core import server_status
        from datetime import datetime

        config = get_config()
        monitor_server_ip = "192.168.20.2"

        if monitor_server_ip in server_status:
            server_status[monitor_server_ip]["last_up"] = datetime.now()
            server_status[monitor_server_ip]["alert_sent"] = False

            update.message.reply_text("вњ… РЎС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° РёСЃРїСЂР°РІР»РµРЅ")

            # РћС‚РїСЂР°РІР»СЏРµРј СѓРІРµРґРѕРјР»РµРЅРёРµ
            from telegram import Bot
            bot = Bot(token=config.TELEGRAM_TOKEN)
            for chat_id in config.CHAT_IDS:
                bot.send_message(chat_id=chat_id, text="рџ”§ РЎС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РёСЃРїСЂР°РІР»РµРЅ")
        else:
            update.message.reply_text("вќЊ РЎРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РЅРµ РЅР°Р№РґРµРЅ РІ СЃРїРёСЃРєРµ")

    except Exception as e:
        update.message.reply_text(f"вќЊ РћС€РёР±РєР° РїСЂРё РёСЃРїСЂР°РІР»РµРЅРёРё СЃС‚Р°С‚СѓСЃР°: {e}")
        debug_log(f"РћС€РёР±РєР° РІ fix_monitor_command: {e}")

def extensions_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /extensions"""
    if not legacy_check_access(update.effective_chat.id):
        update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЌС‚РѕРіРѕ Р±РѕС‚Р°")
        return
    
    show_extensions_menu(update, context)

def show_extensions_menu(update, context):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id
    
    extension_manager = get_extension_manager()
    extensions_status = extension_manager.get_extensions_status()
    
    message = "рџ› пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё*\n\n"
    message += "рџ“Љ *РЎС‚Р°С‚СѓСЃ СЂР°СЃС€РёСЂРµРЅРёР№:*\n\n"
    
    # РЎРѕР·РґР°РµРј РєР»Р°РІРёР°С‚СѓСЂСѓ
    keyboard = []
    
    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']
        
        status_icon = "рџџў" if enabled else "рџ”ґ"
        toggle_text = "рџ”ґ Р’С‹РєР»СЋС‡РёС‚СЊ" if enabled else "рџџў Р’РєР»СЋС‡РёС‚СЊ"
        
        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   РЎС‚Р°С‚СѓСЃ: {'Р’РєР»СЋС‡РµРЅРѕ' if enabled else 'РћС‚РєР»СЋС‡РµРЅРѕ'}\n\n"
        
        # Р”РѕР±Р°РІР»СЏРµРј РєРЅРѕРїРєСѓ РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ РґР»СЏ РєР°Р¶РґРѕРіРѕ СЂР°СЃС€РёСЂРµРЅРёСЏ
        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}", 
                callback_data=f'ext_toggle_{ext_id}'
            )
        ])
    
    # Р”РѕР±Р°РІР»СЏРµРј РєРЅРѕРїРєРё СѓРїСЂР°РІР»РµРЅРёСЏ
    keyboard.extend([
        [InlineKeyboardButton("рџ“Љ Р’РєР»СЋС‡РёС‚СЊ РІСЃРµ", callback_data='ext_enable_all')],
        [InlineKeyboardButton("рџ“‹ РћС‚РєР»СЋС‡РёС‚СЊ РІСЃРµ", callback_data='ext_disable_all')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='monitor_status')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
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
    """РћР±СЂР°Р±РѕС‚С‡РёРє callback'РѕРІ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃС€РёСЂРµРЅРёСЏРјРё"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'extensions_refresh':
        show_extensions_menu(update, context)
    
    elif data == 'ext_enable_all':
        enable_all_extensions(update, context)
    
    elif data == 'ext_disable_all':
        disable_all_extensions(update, context)
    
    elif data.startswith('ext_toggle_'):
        extension_id = data.replace('ext_toggle_', '')
        toggle_extension(update, context, extension_id)
    
    elif data == 'monitor_status':
        # РћРџРўРРњРР—РђР¦РРЇ: РёСЃРїРѕР»СЊР·СѓРµРј Р»РµРЅРёРІСѓСЋ Р·Р°РіСЂСѓР·РєСѓ С‡С‚РѕР±С‹ РёР·Р±РµР¶Р°С‚СЊ С†РёРєР»РёС‡РµСЃРєРёС… РёРјРїРѕСЂС‚РѕРІ
        try:
            from core.monitor_core import monitor_status
            monitor_status(update, context)
        except Exception as e:
            debug_log(f"РћС€РёР±РєР° РїСЂРё РїРµСЂРµС…РѕРґРµ Рє СЃС‚Р°С‚СѓСЃСѓ РјРѕРЅРёС‚РѕСЂРёРЅРіР°: {e}")
            query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё Р·Р°РіСЂСѓР·РєРµ СЃС‚Р°С‚СѓСЃР° РјРѕРЅРёС‚РѕСЂРёРЅРіР°")
    
    elif data == 'close':
        try:
            query.delete_message()
        except:
            query.edit_message_text("вњ… РњРµРЅСЋ Р·Р°РєСЂС‹С‚Рѕ")
            
def toggle_extension(update, context, extension_id):
    """РџРµСЂРµРєР»СЋС‡Р°РµС‚ СЂР°СЃС€РёСЂРµРЅРёРµ"""
    query = update.callback_query
    
    extension_manager = get_extension_manager()
    success, message = extension_manager.toggle_extension(extension_id)
    
    if success:
        query.answer(message)
        show_extensions_menu(update, context)
    else:
        query.answer(message, show_alert=True)

def enable_all_extensions(update, context):
    """Р’РєР»СЋС‡Р°РµС‚ РІСЃРµ СЂР°СЃС€РёСЂРµРЅРёСЏ"""
    query = update.callback_query
    
    extension_manager = get_extension_manager()
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    
    enabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.enable_extension(ext_id)
        if success:
            enabled_count += 1
    
    query.answer(f"вњ… Р’РєР»СЋС‡РµРЅРѕ {enabled_count}/{len(AVAILABLE_EXTENSIONS)} СЂР°СЃС€РёСЂРµРЅРёР№")
    show_extensions_menu(update, context)

def disable_all_extensions(update, context):
    """РћС‚РєР»СЋС‡Р°РµС‚ РІСЃРµ СЂР°СЃС€РёСЂРµРЅРёСЏ"""
    query = update.callback_query
    
    extension_manager = get_extension_manager()
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    
    disabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled_count += 1
    
    query.answer(f"вњ… РћС‚РєР»СЋС‡РµРЅРѕ {disabled_count}/{len(AVAILABLE_EXTENSIONS)} СЂР°СЃС€РёСЂРµРЅРёР№")
    show_extensions_menu(update, context)

# РќРћР’РђРЇ Р¤РЈРќРљР¦РРћРќРђР›Р¬РќРћРЎРўР¬: РЈРџР РђР’Р›Р•РќРР• РћРўР›РђР”РљРћР™
def debug_command(update, context):
    """РљРѕРјР°РЅРґР° СѓРїСЂР°РІР»РµРЅРёСЏ РѕС‚Р»Р°РґРєРѕР№"""
    if not legacy_check_access(update.effective_chat.id):
        update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ СЌС‚РѕРіРѕ Р±РѕС‚Р°")
        return
        
    show_debug_menu(update, context)

def show_debug_menu(update, context):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ СѓРїСЂР°РІР»РµРЅРёСЏ РѕС‚Р»Р°РґРєРѕР№ - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id
    
    # РџРѕР»СѓС‡Р°РµРј СЃС‚Р°С‚СѓСЃ РѕС‚Р»Р°РґРєРё
    debug_status = "рџ”ґ Р’Р«РљР›Р®Р§Р•РќРђ"
    try:
        debug_status = "рџџў Р’РљР›Р®Р§Р•РќРђ" if DEBUG_MODE else "рџ”ґ Р’Р«РљР›Р®Р§Р•РќРђ"
    except ImportError:
        debug_status = "рџ”ґ РќР•Р”РћРЎРўРЈРџРќРђ"
    
    message = "рџђ› *РЈРїСЂР°РІР»РµРЅРёРµ РѕС‚Р»Р°РґРєРѕР№*\n\n"
    message += f"*РўРµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ:* {debug_status}\n\n"
    
    # РљРЅРѕРїРєР°-РїРµСЂРµРєР»СЋС‡Р°С‚РµР»СЊ РІРјРµСЃС‚Рѕ РґРІСѓС… РѕС‚РґРµР»СЊРЅС‹С…
    toggle_text = "рџ”ґ Р’С‹РєР»СЋС‡РёС‚СЊ РѕС‚Р»Р°РґРєСѓ" if DEBUG_MODE else "рџџў Р’РєР»СЋС‡РёС‚СЊ РѕС‚Р»Р°РґРєСѓ"
    toggle_data = 'debug_disable' if DEBUG_MODE else 'debug_enable'

    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("рџ“Љ РЎС‚Р°С‚СѓСЃ СЃРёСЃС‚РµРјС‹", callback_data='debug_status')],
        [InlineKeyboardButton("рџ—‘пёЏ РћС‡РёСЃС‚РёС‚СЊ Р»РѕРіРё", callback_data='debug_clear_logs')],
        [InlineKeyboardButton("рџ“‹ Р”РёР°РіРЅРѕСЃС‚РёРєР°", callback_data='debug_diagnose')],
        [InlineKeyboardButton("рџ”§ Р Р°СЃС€РёСЂРµРЅРЅР°СЏ РѕС‚Р»Р°РґРєР°", callback_data='debug_advanced')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
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

def debug_callback_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє callback'РѕРІ РґР»СЏ РѕС‚Р»Р°РґРєРё"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'debug_enable':
        enable_debug_mode(query)
    elif data == 'debug_disable':
        disable_debug_mode(query)
    elif data == 'debug_status':
        show_debug_status(query)
    elif data == 'debug_clear_logs':
        clear_debug_logs(query)
    elif data == 'debug_diagnose':
        run_diagnostic(query)
    elif data == 'debug_advanced':
        show_advanced_debug(query)
    elif data == 'debug_menu':
        show_debug_menu(update, context)

def enable_debug_mode(query):
    """Р’РєР»СЋС‡Р°РµС‚ СЂРµР¶РёРј РѕС‚Р»Р°РґРєРё"""
    try:
        
        # РћР±РЅРѕРІР»СЏРµРј РЅР°СЃС‚СЂРѕР№РєРё Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        
        # РћР±РЅРѕРІР»СЏРµРј РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ РѕС‚Р»Р°РґРєРё РµСЃР»Рё РґРѕСЃС‚СѓРїРЅР°
        try:
            from config.debug import debug_config
            debug_config.enable_debug()
        except ImportError:
            pass
        
        debug_log("рџџў РћС‚Р»Р°РґРєР° РІРєР»СЋС‡РµРЅР° С‡РµСЂРµР· РјРµРЅСЋ Р±РѕС‚Р°")
        
        query.edit_message_text(
            "рџџў *РћС‚Р»Р°РґРєР° РІРєР»СЋС‡РµРЅР°*\n\n"
            "РўРµРїРµСЂСЊ РІСЃРµ РѕРїРµСЂР°С†РёРё Р±СѓРґСѓС‚ РґРµС‚Р°Р»СЊРЅРѕ Р»РѕРіРёСЂРѕРІР°С‚СЊСЃСЏ.\n"
            f"Р›РѕРіРё СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ РІ {DEBUG_LOG_FILE}\n\n"
            "*Р’РєР»СЋС‡РµРЅС‹ С„СѓРЅРєС†РёРё:*\n"
            "вЂў Р”РµС‚Р°Р»СЊРЅРѕРµ Р»РѕРіРёСЂРѕРІР°РЅРёРµ РѕРїРµСЂР°С†РёР№\n"
            "вЂў РћС‚Р»Р°РґРѕС‡РЅС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ РІ РєРѕРЅСЃРѕР»Рё\n"
            "вЂў Р”РёР°РіРЅРѕСЃС‚РёРєР° РїРѕРґРєР»СЋС‡РµРЅРёР№",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”ґ Р’С‹РєР»СЋС‡РёС‚СЊ", callback_data='debug_disable')],
                [InlineKeyboardButton("рџ”§ Р Р°СЃС€РёСЂРµРЅРЅР°СЏ", callback_data='debug_advanced')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РІРєР»СЋС‡РµРЅРёСЏ РѕС‚Р»Р°РґРєРё: {e}")

def disable_debug_mode(query):
    """Р’С‹РєР»СЋС‡Р°РµС‚ СЂРµР¶РёРј РѕС‚Р»Р°РґРєРё"""
    try:
        # РћР±РЅРѕРІР»СЏРµРј РЅР°СЃС‚СЂРѕР№РєРё Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
        import logging
        logging.getLogger().setLevel(logging.INFO)
        
        # РћР±РЅРѕРІР»СЏРµРј РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ РѕС‚Р»Р°РґРєРё РµСЃР»Рё РґРѕСЃС‚СѓРїРЅР°
        try:
            from config.debug import debug_config
            debug_config.disable_debug()
        except ImportError:
            pass
        
        debug_log("рџ”ґ РћС‚Р»Р°РґРєР° РІС‹РєР»СЋС‡РµРЅР° С‡РµСЂРµР· РјРµРЅСЋ Р±РѕС‚Р°")
        
        query.edit_message_text(
            "рџ”ґ *РћС‚Р»Р°РґРєР° РІС‹РєР»СЋС‡РµРЅР°*\n\n"
            "Р”РµС‚Р°Р»СЊРЅРѕРµ Р»РѕРіРёСЂРѕРІР°РЅРёРµ РѕС‚РєР»СЋС‡РµРЅРѕ.\n"
            "РЎРѕС…СЂР°РЅСЏРµС‚СЃСЏ С‚РѕР»СЊРєРѕ РѕСЃРЅРѕРІРЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџџў Р’РєР»СЋС‡РёС‚СЊ", callback_data='debug_enable')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РІС‹РєР»СЋС‡РµРЅРёСЏ РѕС‚Р»Р°РґРєРё: {e}")

def show_debug_status(query):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ РѕС‚Р»Р°РґРєРё Рё СЃРёСЃС‚РµРјРЅСѓСЋ РёРЅС„РѕСЂРјР°С†РёСЋ - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    import os
    from datetime import datetime
    
    try:
        # РџС‹С‚Р°РµРјСЃСЏ РёРјРїРѕСЂС‚РёСЂРѕРІР°С‚СЊ psutil, РЅРѕ РµСЃР»Рё РЅРµС‚ - СЂР°Р±РѕС‚Р°РµРј Р±РµР· РЅРµРіРѕ
        try:
            import psutil
            psutil_available = True
        except ImportError:
            psutil_available = False
        
        message = "рџ“Љ *РЎС‚Р°С‚СѓСЃ СЃРёСЃС‚РµРјС‹ Рё РѕС‚Р»Р°РґРєРё*\n\n"
        
        # РЎС‚Р°С‚СѓСЃ РѕС‚Р»Р°РґРєРё
        try:
            debug_status = "рџџў Р’РљР›" if DEBUG_MODE else "рџ”ґ Р’Р«РљР›"
        except ImportError:
            debug_status = "рџ”ґ РќР•Р”РћРЎРўРЈРџР•Рќ"
        
        message += f"рџђ› *Р РµР¶РёРј РѕС‚Р»Р°РґРєРё:* {debug_status}\n\n"
        
        # РЎРёСЃС‚РµРјРЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ (РµСЃР»Рё psutil РґРѕСЃС‚СѓРїРµРЅ)
        if psutil_available:
            try:
                disk_usage = psutil.disk_usage('/')
                memory = psutil.virtual_memory()
                load = psutil.getloadavg()
                
                message += "*РЎРёСЃС‚РµРјРЅС‹Рµ СЂРµСЃСѓСЂСЃС‹:*\n"
                message += f"вЂў Р—Р°РіСЂСѓР·РєР° CPU: {load[0]:.2f} {load[1]:.2f} {load[2]:.2f}\n"
                message += f"вЂў РџР°РјСЏС‚СЊ: {memory.percent:.1f}% РёСЃРїРѕР»СЊР·РѕРІР°РЅРѕ\n"
                message += f"вЂў Р”РёСЃРє: {disk_usage.percent:.1f}% РёСЃРїРѕР»СЊР·РѕРІР°РЅРѕ\n\n"
            except Exception as e:
                message += f"*РЎРёСЃС‚РµРјРЅС‹Рµ СЂРµСЃСѓСЂСЃС‹:* РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ: {str(e)[:50]}\n\n"
        else:
            message += "*РЎРёСЃС‚РµРјРЅС‹Рµ СЂРµСЃСѓСЂСЃС‹:* РњРѕРґСѓР»СЊ psutil РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ\n\n"
        
        # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ Р»РѕРіР°С…
        message += "*Р›РѕРіРё:*\n"
        log_files = {
            'debug.log': DEBUG_LOG_FILE,
            'bot_debug.log': BOT_DEBUG_LOG_FILE,
            'mail_monitor.log': MAIL_MONITOR_LOG_FILE,
        }
        
        for log_name, log_path in log_files.items():
            try:
                log_path = Path(log_path)
                if log_path.exists():
                    log_size = log_path.stat().st_size
                    message += f"вЂў {log_name}: {log_size / 1024 / 1024:.2f} MB\n"
                else:
                    message += f"вЂў {log_name}: С„Р°Р№Р» РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚\n"
            except Exception as e:
                message += f"вЂў {log_name}: РѕС€РёР±РєР° РїСЂРѕРІРµСЂРєРё\n"
        
        message += "\n"
        
        # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РїСЂРѕС†РµСЃСЃР°С…
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'python3'], capture_output=True, text=True)
            python_processes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            message += f"*РџСЂРѕС†РµСЃСЃС‹ Python:* {python_processes}\n"
        except:
            message += "*РџСЂРѕС†РµСЃСЃС‹ Python:* РќРµРґРѕСЃС‚СѓРїРЅРѕ\n"
        
        # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ СЂР°СЃС€РёСЂРµРЅРёСЏС…
        try:
            extension_manager = get_extension_manager()
            enabled_extensions = extension_manager.get_enabled_extensions()
            message += f"*Р’РєР»СЋС‡РµРЅРѕ СЂР°СЃС€РёСЂРµРЅРёР№:* {len(enabled_extensions)}\n"
        except:
            message += "*Р’РєР»СЋС‡РµРЅРѕ СЂР°СЃС€РёСЂРµРЅРёР№:* РќРµРґРѕСЃС‚СѓРїРЅРѕ\n"
        
        message += f"\nрџ•’ *РћР±РЅРѕРІР»РµРЅРѕ:* {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='debug_status')],
                [InlineKeyboardButton("рџ—‘пёЏ РћС‡РёСЃС‚РёС‚СЊ Р»РѕРіРё", callback_data='debug_clear_logs')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЃС‚Р°С‚СѓСЃР°: {str(e)[:100]}")

def clear_debug_logs(query):
    """РћС‡РёС‰Р°РµС‚ С„Р°Р№Р»С‹ Р»РѕРіРѕРІ - Р‘Р•Р— РљРќРћРџРљР Р”РРђР“РќРћРЎРўРРљР"""
    import logging
    
    try:
        log_files = [
            DEBUG_LOG_FILE,
            BOT_DEBUG_LOG_FILE,
            MAIL_MONITOR_LOG_FILE,
        ]
        
        cleared = 0
        errors = []
        
        for log_file in log_files:
            try:
                log_file = Path(log_file)
                if log_file.exists():
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
                    
                    # РџРµСЂРµРєРѕРЅС„РёРіСѓСЂРёСЂСѓРµРј Р»РѕРіРіРµСЂ РµСЃР»Рё СЌС‚Рѕ debug.log
                    if log_file.name == 'debug.log':
                        logging.getLogger().handlers[0].flush()
                else:
                    # РЎРѕР·РґР°РµРј РїСѓСЃС‚РѕР№ С„Р°Р№Р» РµСЃР»Рё РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
            except Exception as e:
                errors.append(f"РћС€РёР±РєР° РѕС‡РёСЃС‚РєРё {log_file}: {e}")
        
        message = f"вњ… *Р›РѕРіРё РѕС‡РёС‰РµРЅС‹*\n\nРћС‡РёС‰РµРЅРѕ С„Р°Р№Р»РѕРІ: {cleared}/{len(log_files)}"
        
        if errors:
            message += f"\n\n*РћС€РёР±РєРё:*\n" + "\n".join(errors[:3])
        
        debug_log("рџ—‘пёЏ Р›РѕРіРё РѕС‡РёС‰РµРЅС‹ С‡РµСЂРµР· РјРµРЅСЋ Р±РѕС‚Р°")
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='debug_clear_logs')],
                [InlineKeyboardButton("рџ“Љ РЎС‚Р°С‚СѓСЃ СЃРёСЃС‚РµРјС‹", callback_data='debug_status')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РѕС‡РёСЃС‚РєРё Р»РѕРіРѕРІ: {e}")

def run_diagnostic(query):
    """Р—Р°РїСѓСЃРєР°РµС‚ РґРёР°РіРЅРѕСЃС‚РёРєСѓ СЃРёСЃС‚РµРјС‹ - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р’Р•Р РЎРРЇ"""
    import subprocess
    import socket
    import os
    from datetime import datetime
    
    try:
        message = "рџ”§ *Р”РёР°РіРЅРѕСЃС‚РёРєР° СЃРёСЃС‚РµРјС‹*\n\n"
        
        # РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє Р±Р°Р·РѕРІС‹Рј СЃРµСЂРІРёСЃР°Рј
        checks = [
            ("Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ", "192.168.20.2", 5000),
            ("SSH РґРµРјРѕРЅ", "localhost", 22),
            ("Р‘Р°Р·Р° Р±СЌРєР°РїРѕРІ", "localhost", None),
        ]
        
        for service, host, port in checks:
            try:
                if port:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    status = "рџџў" if result == 0 else "рџ”ґ"
                    message += f"{status} {service}: {'РґРѕСЃС‚СѓРїРµРЅ' if result == 0 else 'РЅРµРґРѕСЃС‚СѓРїРµРЅ'}\n"
                else:
                    # РџСЂРѕРІРµСЂРєР° С„Р°Р№Р»Р° Р±Р°Р·С‹ РґР°РЅРЅС‹С…
                    db_path = DATA_DIR / 'backups.db'
                    if db_path.exists():
                        status = "рџџў"
                        message += f"{status} {service}: С„Р°Р№Р» СЃСѓС‰РµСЃС‚РІСѓРµС‚\n"
                    else:
                        status = "рџ”ґ"
                        message += f"{status} {service}: С„Р°Р№Р» РЅРµ РЅР°Р№РґРµРЅ\n"
            except Exception as e:
                # Р­РєСЂР°РЅРёСЂСѓРµРј СЃРїРµС†РёР°Р»СЊРЅС‹Рµ СЃРёРјРІРѕР»С‹ Markdown
                error_msg = str(e)[:50].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
                message += f"рџ”ґ {service}: РѕС€РёР±РєР° РїСЂРѕРІРµСЂРєРё ({error_msg})\n"
        
        message += "\n*РџСЂРѕРІРµСЂРєР° РїСЂРѕС†РµСЃСЃРѕРІ:*\n"
        
        # РџСЂРѕРІРµСЂРєР° РѕСЃРЅРѕРІРЅС‹С… РїСЂРѕС†РµСЃСЃРѕРІ
        processes = [
            "python3",
            "main.py", 
            "improved_mail_monitor.py"
        ]
        
        for process in processes:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', process],
                    capture_output=True, 
                    text=True
                )
                running = len(result.stdout.strip().split('\n')) > 0 and result.stdout.strip() != ''
                status = "рџџў" if running else "рџ”ґ"
                message += f"{status} {process}: {'Р·Р°РїСѓС‰РµРЅ' if running else 'РЅРµ Р·Р°РїСѓС‰РµРЅ'}\n"
            except Exception as e:
                message += f"рџ”ґ {process}: РѕС€РёР±РєР° РїСЂРѕРІРµСЂРєРё\n"
        
        # РџСЂРѕРІРµСЂРєР° СЂР°СЃС€РёСЂРµРЅРёР№
        message += "\n*РџСЂРѕРІРµСЂРєР° СЂР°СЃС€РёСЂРµРЅРёР№:*\n"
        try:
            extension_manager = get_extension_manager()
            enabled_extensions = extension_manager.get_enabled_extensions()
            
            for ext_id in enabled_extensions:
                status = "рџџў"
                message += f"{status} {ext_id}: РІРєР»СЋС‡РµРЅРѕ\n"
        except Exception as e:
            message += "рџ”ґ Р Р°СЃС€РёСЂРµРЅРёСЏ: РѕС€РёР±РєР° РїСЂРѕРІРµСЂРєРё\n"
        
        message += f"\nрџ•’ *Р”РёР°РіРЅРѕСЃС‚РёРєР° Р·Р°РІРµСЂС€РµРЅР°:* {datetime.now().strftime('%H:%M:%S')}"

        # Р­РєСЂР°РЅРёСЂСѓРµРј РІСЃРµ СЃРѕРѕР±С‰РµРЅРёРµ РґР»СЏ Р±РµР·РѕРїР°СЃРЅРѕРіРѕ РѕС‚РѕР±СЂР°Р¶РµРЅРёСЏ РІ Markdown
        safe_message = message.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')

        query.edit_message_text(
            safe_message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ", callback_data='debug_diagnose')],
                [InlineKeyboardButton("рџ”§ Р Р°СЃС€РёСЂРµРЅРЅР°СЏ", callback_data='debug_advanced')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° РґРёР°РіРЅРѕСЃС‚РёРєРё: {str(e)[:100]}")

def show_advanced_debug(query):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЂР°СЃС€РёСЂРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё РѕС‚Р»Р°РґРєРё - Р‘Р•Р— РљРќРћРџРљР РћРЎРќРћР’РќР«РҐ РќРђРЎРўР РћР•Рљ"""
    try:
        from config.debug import debug_config
        debug_info = debug_config.get_debug_info()
        
        message = "рџ”§ *Р Р°СЃС€РёСЂРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё РѕС‚Р»Р°РґРєРё*\n\n"
        
        message += f"*РћСЃРЅРѕРІРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё:*\n"
        message += f"вЂў Р РµР¶РёРј РѕС‚Р»Р°РґРєРё: {'рџџў Р’РљР›' if debug_info['debug_mode'] else 'рџ”ґ Р’Р«РљР›'}\n"
        message += f"вЂў РЈСЂРѕРІРµРЅСЊ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ: {debug_info['log_level']}\n"
        message += f"вЂў РњР°РєСЃ. СЂР°Р·РјРµСЂ Р»РѕРіР°: {debug_info['max_log_size']} MB\n\n"
        
        message += f"*Р”РµС‚Р°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё:*\n"
        message += f"вЂў SSH РѕС‚Р»Р°РґРєР°: {'рџџў Р’РљР›' if debug_info['ssh_debug'] else 'рџ”ґ Р’Р«РљР›'}\n"
        message += f"вЂў Р РµСЃСѓСЂСЃС‹ РѕС‚Р»Р°РґРєР°: {'рџџў Р’РљР›' if debug_info['resource_debug'] else 'рџ”ґ Р’Р«РљР›'}\n"
        message += f"вЂў Р‘СЌРєР°РїС‹ РѕС‚Р»Р°РґРєР°: {'рџџў Р’РљР›' if debug_info['backup_debug'] else 'рџ”ґ Р’Р«РљР›'}\n\n"
        
        message += f"*РЎС‚Р°С‚СѓСЃ Р»РѕРіРѕРІ:*\n"
        
        # Р”РѕР±Р°РІР»СЏРµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ СЂР°Р·РјРµСЂР°С… Р»РѕРіРѕРІ
        log_files = {
            'debug.log': DEBUG_LOG_FILE,
            'bot_debug.log': BOT_DEBUG_LOG_FILE,
            'mail_monitor.log': MAIL_MONITOR_LOG_FILE,
        }
        
        for log_name, log_path in log_files.items():
            try:
                log_path = Path(log_path)
                if log_path.exists():
                    size = log_path.stat().st_size / 1024 / 1024
                    message += f"вЂў {log_name}: {size:.2f} MB\n"
                else:
                    message += f"вЂў {log_name}: С„Р°Р№Р» РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚\n"
            except:
                message += f"вЂў {log_name}: РѕС€РёР±РєР° РїСЂРѕРІРµСЂРєРё\n"
        
        message += f"\n*РџРѕСЃР»РµРґРЅРµРµ РёР·РјРµРЅРµРЅРёРµ:* {debug_info['last_modified'][:19]}"

        keyboard = [
            [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='debug_advanced')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ]

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except ImportError:
        query.edit_message_text(
            "вќЊ *Р Р°СЃС€РёСЂРµРЅРЅР°СЏ РѕС‚Р»Р°РґРєР° РЅРµРґРѕСЃС‚СѓРїРЅР°*\n\n"
            "РњРѕРґСѓР»СЊ debug_config.py РЅРµ РЅР°Р№РґРµРЅ.\n"
            "РЈР±РµРґРёС‚РµСЃСЊ, С‡С‚Рѕ С„Р°Р№Р» СЃСѓС‰РµСЃС‚РІСѓРµС‚ РІ РїР°РїРєРµ РїСЂРѕРµРєС‚Р°.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='debug_menu')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё СЂР°СЃС€РёСЂРµРЅРЅС‹С… РЅР°СЃС‚СЂРѕРµРє: {str(e)[:100]}")

def diagnose_windows_command(update, context):
    """Р”РёР°РіРЅРѕСЃС‚РёРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє Windows СЃРµСЂРІРµСЂР°Рј"""
    if not context.args:
        update.message.reply_text("вќЊ РЈРєР°Р¶РёС‚Рµ IP Windows СЃРµСЂРІРµСЂР°: /diagnose_windows <ip>")
        return
    
    ip = context.args[0]
    
    from extensions.server_checks import get_windows_resources_improved, get_windows_resources_winrm, get_windows_resources_wmi
    
    message = f"рџ”§ *Р”РёР°РіРЅРѕСЃС‚РёРєР° Windows СЃРµСЂРІРµСЂР° {ip}*\n\n"
    
    # РџСЂРѕРІРµСЂРєР° Р±Р°Р·РѕРІРѕР№ РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
    from extensions.server_checks import check_ping, check_port
    ping_ok = check_ping(ip)
    rdp_ok = check_port(ip, 3389)
    winrm_ok = check_port(ip, 5985)
    
    message += f"вЂў Ping: {'рџџў OK' if ping_ok else 'рџ”ґ FAIL'}\n"
    message += f"вЂў RDP РїРѕСЂС‚ (3389): {'рџџў OK' if rdp_ok else 'рџ”ґ FAIL'}\n" 
    message += f"вЂў WinRM РїРѕСЂС‚ (5985): {'рџџў OK' if winrm_ok else 'рџ”ґ FAIL'}\n\n"
    
    # РўРµСЃС‚РёСЂСѓРµРј РјРµС‚РѕРґС‹ РїРѕР»СѓС‡РµРЅРёСЏ СЂРµСЃСѓСЂСЃРѕРІ
    message += "*РўРµСЃС‚РёСЂРѕРІР°РЅРёРµ РјРµС‚РѕРґРѕРІ:*\n"
    
    # WinRM
    winrm_result = get_windows_resources_winrm(ip)
    if winrm_result:
        message += f"вЂў WinRM: рџџў OK (CPU: {winrm_result.get('cpu', 0)}%, RAM: {winrm_result.get('ram', 0)}%)\n"
    else:
        message += "вЂў WinRM: рџ”ґ FAIL\n"
    
    # WMI  
    wmi_result = get_windows_resources_wmi(ip)
    if wmi_result:
        message += f"вЂў WMI: рџџў OK (CPU: {wmi_result.get('cpu', 0)}%, RAM: {wmi_result.get('ram', 0)}%)\n"
    else:
        message += "вЂў WMI: рџ”ґ FAIL\n"
    
    # РљРѕРјР±РёРЅРёСЂРѕРІР°РЅРЅС‹Р№ РјРµС‚РѕРґ
    combined_result = get_windows_resources_improved(ip)
    if combined_result:
        message += f"вЂў Combined: рџџў OK (CPU: {combined_result.get('cpu', 0)}%, RAM: {combined_result.get('ram', 0)}%, Disk: {combined_result.get('disk', 0)}%)\n"
        message += f"вЂў Method: {combined_result.get('access_method', 'unknown')}\n"
    else:
        message += "вЂў Combined: рџ”ґ FAIL\n"
    
    update.message.reply_text(message, parse_mode='Markdown')

def get_handlers():
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕР±СЂР°Р±РѕС‚С‡РёРєРё РєРѕРјР°РЅРґ РґР»СЏ Р±РѕС‚Р°"""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("check", check_command),
        CommandHandler("status", status_command),
        CommandHandler("servers", servers_command),
        CommandHandler("silent", silent_command),
        CommandHandler("report", report_command),
        CommandHandler("stats", stats_command),
        CommandHandler("control", control_command),
        CommandHandler("diagnose_ssh", diagnose_ssh_command),
        CommandHandler("extensions", extensions_command),
        CommandHandler("fix_monitor", fix_monitor_command),
        CommandHandler("backup", backup_command),
        CommandHandler("backup_search", backup_search_command),
        CommandHandler("backup_help", backup_help_command),
        CommandHandler("debug", debug_command),
        CommandHandler("diagnose_windows", diagnose_windows_command),
        CommandHandler("check_single", lambda u,c: show_server_selection_menu(u,c, "check_availability")),
        CommandHandler("check_resources_single", lambda u,c: show_server_selection_menu(u,c, "check_resources")),
        CommandHandler("check_server", check_single_server_command),
        CommandHandler("check_res", check_single_resources_command),
        
        # РћР±СЂР°Р±РѕС‚С‡РёРє СЃРѕРѕР±С‰РµРЅРёР№ СЃ Р»РµРЅРёРІРѕР№ Р·Р°РіСЂСѓР·РєРѕР№
        MessageHandler(Filters.text & ~Filters.command, lazy_message_handler()),
    ]

def get_callback_handlers():
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕР±СЂР°Р±РѕС‚С‡РёРєРё callback-Р·Р°РїСЂРѕСЃРѕРІ СЃ Р»РµРЅРёРІРѕР№ Р·Р°РіСЂСѓР·РєРѕР№"""
    return [
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РЅР°СЃС‚СЂРѕРµРє (РёСЃРїРѕР»СЊР·СѓРµРј Р»РµРЅРёРІСѓСЋ Р·Р°РіСЂСѓР·РєСѓ)
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_times$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_patterns$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^manage_'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_auth$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^ssh_auth_settings$'),
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё Windows Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё
        CallbackQueryHandler(settings_callback_handler, pattern='^windows_auth_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^cred_type_'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ С‚Р°Р№РјР°СѓС‚РѕРІ СЃРµСЂРІРµСЂРѕРІ
        CallbackQueryHandler(settings_callback_handler, pattern='^server_timeouts$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_windows_2025_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_domain_servers_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_admin_servers_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_standard_windows_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_linux_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_ping_timeout$'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РЅР°СЃС‚СЂРѕРµРє Р‘Р”
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_main$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_add_category$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_edit_category$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_delete_category$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_view_all$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_edit_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_delete_'),

        # РћСЃРЅРѕРІРЅС‹Рµ РѕР±СЂР°Р±РѕС‚С‡РёРєРё
        CallbackQueryHandler(lambda u, c: lazy_handler('manual_check')(u, c), pattern='^manual_check$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('monitor_status')(u, c), pattern='^monitor_status$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('servers_list')(u, c), pattern='^servers_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('silent_status')(u, c), pattern='^silent_status$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_resources')(u, c), pattern='^check_resources$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('control_panel')(u, c), pattern='^control_panel$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('daily_report')(u, c), pattern='^daily_report$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('diagnose_menu')(u, c), pattern='^diagnose_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close')(u, c), pattern='^close$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('full_report')(u, c), pattern='^full_report$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('force_silent')(u, c), pattern='^force_silent$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('force_loud')(u, c), pattern='^force_loud$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('auto_mode')(u, c), pattern='^auto_mode$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('toggle_silent')(u, c), pattern='^toggle_silent$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('resource_history')(u, c), pattern='^resource_history$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('debug_report')(u, c), pattern='^debug_report$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('monitor_main')(u, c), pattern='^monitor_main$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('main_menu')(u, c), pattern='^main_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('toggle_monitoring')(u, c), pattern='^toggle_monitoring$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close')(u, c), pattern='^close$'),

        # РѕР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РЅР°СЃС‚СЂРѕРµРє
        CallbackQueryHandler(settings_callback_handler, pattern='^add_chat$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^remove_chat$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^view_patterns$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^add_pattern$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_view_all$'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РЅР°СЃС‚СЂРѕРµРє (РґРѕР»Р¶РЅС‹ Р±С‹С‚СЊ Р’Р«РЁР• РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ Р±СЌРєР°РїРѕРІ)
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_today')(u, c), pattern='^db_backups_today$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_summary')(u, c), pattern='^db_backups_summary$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_detailed')(u, c), pattern='^db_backups_detailed$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_list')(u, c), pattern='^db_backups_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_detail_')(u, c), pattern='^db_detail_'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ РїРѕСЃС‚СЂР°РЅРёС‡РЅРѕРіРѕ РїСЂРѕСЃРјРѕС‚СЂР° СЂРµСЃСѓСЂСЃРѕРІ
        CallbackQueryHandler(lambda u, c: lazy_handler('resource_page')(u, c), pattern='^resource_page_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('refresh_resources')(u, c), pattern='^refresh_resources$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close_resources')(u, c), pattern='^close_resources$'),
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЂР°Р·РґРµР»СЊРЅРѕР№ РїСЂРѕРІРµСЂРєРё РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
        CallbackQueryHandler(lambda u, c: lazy_handler('check_linux')(u, c), pattern='^check_linux$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_windows')(u, c), pattern='^check_windows$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_other')(u, c), pattern='^check_other$'),
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЂР°Р·РґРµР»СЊРЅРѕР№ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ
        CallbackQueryHandler(lambda u, c: lazy_handler('check_cpu')(u, c), pattern='^check_cpu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_ram')(u, c), pattern='^check_ram$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_disk')(u, c), pattern='^check_disk$'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ Р±СЌРєР°РїРѕРІ
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_hosts')(u, c), pattern='^backup_hosts$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_refresh')(u, c), pattern='^backup_refresh$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_host_')(u, c), pattern='^backup_host_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_today')(u, c), pattern='^db_backups_today$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_summary')(u, c), pattern='^db_backups_summary$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_detailed')(u, c), pattern='^db_backups_detailed$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_list')(u, c), pattern='^db_backups_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_main')(u, c), pattern='^backup_main$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_proxmox')(u, c), pattern='^backup_proxmox$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_databases')(u, c), pattern='^backup_databases$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_mail')(u, c), pattern='^backup_mail$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_host_')(u, c), pattern='^backup_host_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_detail_')(u, c), pattern='^db_detail_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_stale_hosts')(u, c), pattern='^backup_stale_hosts$'),

        # РћР±СЂР°Р±РѕС‚С‡РёРєРё СЂР°СЃС€РёСЂРµРЅРёР№
        CallbackQueryHandler(lambda u, c: lazy_handler('extensions_menu')(u, c), pattern='^extensions_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('extensions_refresh')(u, c), pattern='^extensions_refresh$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('ext_enable_all')(u, c), pattern='^ext_enable_all$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('ext_disable_all')(u, c), pattern='^ext_disable_all$'),
        CallbackQueryHandler(lambda u, c: extensions_callback_handler(u, c), pattern='^ext_toggle_'),
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЃРµСЂРІРµСЂРѕРІ
        CallbackQueryHandler(settings_callback_handler, pattern='^server_type_'),
        
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ Р‘Р”
        CallbackQueryHandler(settings_callback_handler, pattern='^edit_db_category_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^delete_db_category_'),

        # РќРћР’Р«Р• РћР‘Р РђР‘РћРўР§РРљР РћРўР›РђР”РљР
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_enable$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_disable$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_status$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_clear_logs$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_diagnose$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_advanced$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('debug_menu')(u, c), pattern='^debug_menu$'),

        CallbackQueryHandler(lambda u,c: show_server_selection_menu(u,c, "check_availability"), pattern='^show_availability_menu$'),
        CallbackQueryHandler(lambda u,c: show_server_selection_menu(u,c, "check_resources"), pattern='^show_resources_menu$'),
        CallbackQueryHandler(lambda u,c: handle_single_check(u,c, u.callback_query.data.replace('check_availability_', '')), pattern='^check_availability_'),
        CallbackQueryHandler(lambda u,c: handle_single_resources(u,c, u.callback_query.data.replace('check_resources_', '')), pattern='^check_resources_'),
        CallbackQueryHandler(lambda u,c: refresh_server_menu(u,c), pattern='^refresh_'),
    ]

def lazy_handler(pattern):
    """Р›РµРЅРёРІР°СЏ Р·Р°РіСЂСѓР·РєР° РѕР±СЂР°Р±РѕС‚С‡РёРєРѕРІ"""
    def wrapper(update, context):
        # Р”РёРЅР°РјРёС‡РµСЃРєРё РёРјРїРѕСЂС‚РёСЂСѓРµРј РѕР±СЂР°Р±РѕС‚С‡РёРє РїСЂРё РІС‹Р·РѕРІРµ
        if pattern == 'main_menu':
            return start_command(update, context)
        elif pattern == 'manual_check':
            from core.monitor_core import manual_check_handler as handler
        elif pattern == 'monitor_status':
            from core.monitor_core import monitor_status as handler
        elif pattern == 'silent_status':
            from core.monitor_core import silent_status_handler as handler
        elif pattern == 'pause_monitoring':
            from core.monitor_core import pause_monitoring_handler as handler
        elif pattern == 'resume_monitoring':
            from core.monitor_core import resume_monitoring_handler as handler
        elif pattern == 'check_resources':
            from core.monitor_core import check_resources_handler as handler
        elif pattern == 'control_panel':
            from core.monitor_core import control_panel_handler as handler
        elif pattern == 'toggle_monitoring':
            from core.monitor_core import toggle_monitoring_handler as handler
        elif pattern == 'daily_report':
            from core.monitor_core import send_morning_report_handler as handler
        elif pattern == 'diagnose_menu':
            from core.monitor_core import diagnose_menu_handler as handler
        elif pattern == 'close':
            from core.monitor_core import close_menu as handler
        elif pattern == 'force_silent':
            from core.monitor_core import force_silent_handler as handler
        elif pattern == 'force_loud':
            from core.monitor_core import force_loud_handler as handler
        elif pattern == 'auto_mode':
            from core.monitor_core import auto_mode_handler as handler
        elif pattern == 'toggle_silent':
            from core.monitor_core import toggle_silent_mode_handler as handler
        elif pattern == 'servers_list':
            from extensions.server_checks import servers_list_handler as handler
        elif pattern == 'full_report':
            from core.monitor_core import send_morning_report_handler as handler
        elif pattern == 'resource_page':
            from core.monitor_core import resource_page_handler as handler
        elif pattern == 'refresh_resources':
            from core.monitor_core import refresh_resources_handler as handler
        elif pattern == 'close_resources':
            from core.monitor_core import close_resources_handler as handler
        # РќРѕРІС‹Рµ РѕР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЂР°Р·РґРµР»СЊРЅРѕР№ РїСЂРѕРІРµСЂРєРё
        elif pattern == 'check_linux':
            from core.monitor_core import check_linux_resources_handler as handler
        elif pattern == 'check_windows':
            from core.monitor_core import check_windows_resources_handler as handler
        elif pattern == 'check_other':
            from core.monitor_core import check_other_resources_handler as handler
        # РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ СЂР°Р·РґРµР»СЊРЅРѕР№ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ
        elif pattern == 'check_cpu':
            from core.monitor_core import check_cpu_resources_handler as handler
        elif pattern == 'check_ram':
            from core.monitor_core import check_ram_resources_handler as handler
        elif pattern == 'check_disk':
            from core.monitor_core import check_disk_resources_handler as handler
        elif pattern == 'resource_history':
            from core.monitor_core import resource_history_command as handler
        elif pattern == 'debug_report':
            from core.monitor_core import debug_morning_report as handler
        elif pattern == 'backup_today':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_24h':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_24h':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_48h':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_failed':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_hosts':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_refresh':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern.startswith('backup_host_'):
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_main':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_proxmox':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_databases':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_mail':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_summary':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_detailed':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_list':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern.startswith('db_detail_'):
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_stale_hosts':
            from extensions.backup_monitor.bot_handler import show_stale_hosts as handler
        elif pattern == 'db_stale_list':
            from extensions.backup_monitor.bot_handler import show_stale_databases as handler
        elif pattern == 'extensions_menu':
            handler = show_extensions_menu
        elif pattern == 'extensions_refresh':
            handler = show_extensions_menu
        elif pattern == 'ext_enable_all':
            handler = enable_all_extensions
        elif pattern == 'ext_disable_all':
            handler = disable_all_extensions
        elif pattern == 'debug_menu':
            handler = show_debug_menu
        else:
            def default_handler(update, context):
                query = update.callback_query
                query.answer()
                query.edit_message_text("вќЊ РћР±СЂР°Р±РѕС‚С‡РёРє РЅРµ РЅР°Р№РґРµРЅ")
            return default_handler(update, context)

        return handler(update, context)
    return wrapper

def lazy_message_handler():
    """Р›РµРЅРёРІР°СЏ Р·Р°РіСЂСѓР·РєР° РѕР±СЂР°Р±РѕС‚С‡РёРєР° СЃРѕРѕР±С‰РµРЅРёР№"""
    def handler(update, context):
        try:
            from bot.handlers.settings_handlers import handle_setting_value
            return handle_setting_value(update, context)
        except ImportError as e:
            print(f"вќЊ РћС€РёР±РєР° РёРјРїРѕСЂС‚Р° handle_setting_value: {e}")
            # Р•СЃР»Рё РЅРµ СѓРґР°Р»РѕСЃСЊ РёРјРїРѕСЂС‚РёСЂРѕРІР°С‚СЊ, РїСЂРѕСЃС‚Рѕ РёРіРЅРѕСЂРёСЂСѓРµРј СЃРѕРѕР±С‰РµРЅРёРµ
            return
    return handler

def check_single_server_command(update, context):
    """РљРѕРјР°РЅРґР° /check_server - РїСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    if not context.args:
        # РџРѕРєР°Р·С‹РІР°РµРј РјРµРЅСЋ РІС‹Р±РѕСЂР°
        return show_server_selection_menu(update, context, "check_availability")
    else:
        # РџСЂРѕРІРµСЂСЏРµРј СѓРєР°Р·Р°РЅРЅС‹Р№ СЃРµСЂРІРµСЂ
        server_id = context.args[0]
        return handle_single_check(update, context, server_id)

def check_single_resources_command(update, context):
    """РљРѕРјР°РЅРґР° /check_res - РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('resource_monitor'):
        if update.message:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        elif update.callback_query:
            update.callback_query.answer("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ", show_alert=True)
        return

    if not context.args:
        # РџРѕРєР°Р·С‹РІР°РµРј РјРµРЅСЋ РІС‹Р±РѕСЂР°
        return show_server_selection_menu(update, context, "check_resources")
    else:
        # РџСЂРѕРІРµСЂСЏРµРј СѓРєР°Р·Р°РЅРЅС‹Р№ СЃРµСЂРІРµСЂ
        server_id = context.args[0]
        return handle_single_resources(update, context, server_id)

def show_server_selection_menu(update, context, action="check_availability"):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ РІС‹Р±РѕСЂР° СЃРµСЂРІРµСЂР°"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    extension_manager = get_extension_manager()
    
    # РћРїСЂРµРґРµР»СЏРµРј Р·Р°РіРѕР»РѕРІРѕРє
    titles = {
        "check_availability": "рџ“Ў *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё:*",
        "check_resources": "рџ“Љ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ:*"
    }
    
    title = titles.get(action, "рџ”Ќ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ:*")

    if action == "check_resources" and not extension_manager.is_extension_enabled('resource_monitor'):
        message = "рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ"
        if query:
            query.answer()
            query.edit_message_text(text=message)
        elif update.message:
            update.message.reply_text(text=message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return

    # РџРѕР»СѓС‡Р°РµРј РєР»Р°РІРёР°С‚СѓСЂСѓ
    keyboard = targeted_checks.create_server_selection_menu(action)
    
    # Р•СЃР»Рё РІС‹Р·РІР°РЅРѕ РёР· callback (РєРЅРѕРїРєР°)
    if query:
        query.answer()
        query.edit_message_text(text=title, parse_mode='Markdown', reply_markup=keyboard)
    # Р•СЃР»Рё РІС‹Р·РІР°РЅРѕ РєРѕРјР°РЅРґРѕР№
    elif update.message:
        update.message.reply_text(text=title, parse_mode='Markdown', reply_markup=keyboard)
    # Р•СЃР»Рё РІС‹Р·РІР°РЅРѕ РёР· РґСЂСѓРіРѕРіРѕ РѕР±СЂР°Р±РѕС‚С‡РёРєР°
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=title,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

def handle_single_check(update, context, server_id):
    """РћР±СЂР°Р±РѕС‚РєР° РїСЂРѕРІРµСЂРєРё РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    if query:
        query.answer("рџ”Ќ РџСЂРѕРІРµСЂСЏРµРј СЃРµСЂРІРµСЂ...")
    
    # Р’С‹РїРѕР»РЅСЏРµРј РїСЂРѕРІРµСЂРєСѓ
    success, server, message = targeted_checks.check_single_server_availability(server_id)
    
    # РЎРѕР·РґР°РµРј РєР»Р°РІРёР°С‚СѓСЂСѓ РґР»СЏ РґРµР№СЃС‚РІРёР№
    keyboard = []
    if server:
        row_actions = [InlineKeyboardButton("рџ”„ РџСЂРѕРІРµСЂРёС‚СЊ СЃРЅРѕРІР°", callback_data=f"check_availability_{server['ip']}")]
        if extension_manager.is_extension_enabled('resource_monitor'):
            row_actions.insert(0, InlineKeyboardButton("рџ“Љ РџСЂРѕРІРµСЂРёС‚СЊ СЂРµСЃСѓСЂСЃС‹", callback_data=f"check_resources_{server['ip']}"))
        keyboard.append(row_actions)
    
    keyboard.append([
        InlineKeyboardButton("рџ”Ќ Р’С‹Р±СЂР°С‚СЊ РґСЂСѓРіРѕР№", callback_data="show_availability_menu")
    ])
    keyboard.append([
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data="main_menu"),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data="close")
    ])
    
    if query:
        query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

def handle_single_resources(update, context, server_id):
    """РћР±СЂР°Р±РѕС‚РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    if query:
        query.answer("рџ“Љ РџСЂРѕРІРµСЂСЏРµРј СЂРµСЃСѓСЂСЃС‹...")

    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('resource_monitor'):
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    # Р’С‹РїРѕР»РЅСЏРµРј РїСЂРѕРІРµСЂРєСѓ
    success, server, message = targeted_checks.check_single_server_resources(server_id)
    
    # РЎРѕР·РґР°РµРј РєР»Р°РІРёР°С‚СѓСЂСѓ РґР»СЏ РґРµР№СЃС‚РІРёР№
    keyboard = []
    if server:
        keyboard.append([
            InlineKeyboardButton("рџ“Ў РџСЂРѕРІРµСЂРёС‚СЊ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ", callback_data=f"check_availability_{server['ip']}"),
            InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ СЂРµСЃСѓСЂСЃС‹", callback_data=f"check_resources_{server['ip']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("рџ”Ќ Р’С‹Р±СЂР°С‚СЊ РґСЂСѓРіРѕР№", callback_data="show_resources_menu")
    ])
    keyboard.append([
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data="main_menu"),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data="close")
    ])
    
    if query:
        query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

def add_quick_check_buttons(keyboard, server_ip=None):
    """Р”РѕР±Р°РІР»СЏРµС‚ РєРЅРѕРїРєРё Р±С‹СЃС‚СЂРѕР№ РїСЂРѕРІРµСЂРєРё РІ РєР»Р°РІРёР°С‚СѓСЂСѓ"""
    if server_ip:
        extension_manager = get_extension_manager()
        row_actions = [InlineKeyboardButton("рџ”Ќ РџСЂРѕРІРµСЂРёС‚СЊ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ", callback_data=f'check_availability_{server_ip}')]
        if extension_manager.is_extension_enabled('resource_monitor'):
            row_actions.append(InlineKeyboardButton("рџ“Љ РџСЂРѕРІРµСЂРёС‚СЊ СЂРµСЃСѓСЂСЃС‹", callback_data=f'check_resources_{server_ip}'))
        keyboard.append(row_actions)
    
    keyboard.append([
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])
    
    return keyboard

def create_quick_actions_menu(server_ip):
    """РЎРѕР·РґР°РµС‚ РјРµРЅСЋ Р±С‹СЃС‚СЂС‹С… РґРµР№СЃС‚РІРёР№ РґР»СЏ СЃРµСЂРІРµСЂР°"""
    extension_manager = get_extension_manager()
    keyboard = [
        [InlineKeyboardButton("рџ”Ќ РџСЂРѕРІРµСЂРёС‚СЊ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ", callback_data=f'check_availability_{server_ip}')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“Љ РџСЂРѕРІРµСЂРёС‚СЊ СЂРµСЃСѓСЂСЃС‹", callback_data=f'check_resources_{server_ip}')])

    keyboard.extend([
        [InlineKeyboardButton("рџ“‹ РРЅС„РѕСЂРјР°С†РёСЏ Рѕ СЃРµСЂРІРµСЂРµ", callback_data=f'server_info_{server_ip}')],
        [InlineKeyboardButton("рџ”„ РџСЂРѕРІРµСЂРёС‚СЊ СЃРЅРѕРІР°", callback_data=f'check_availability_{server_ip}')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def refresh_server_menu(update, context):
    """РћР±РЅРѕРІР»РµРЅРёРµ РјРµРЅСЋ РІС‹Р±РѕСЂР° СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    if not query:
        return
    
    query.answer("рџ”„ РћР±РЅРѕРІР»СЏРµРј СЃРїРёСЃРѕРє...")
    
    # РћРїСЂРµРґРµР»СЏРµРј С‚РёРї РґРµР№СЃС‚РІРёСЏ РёР· callback_data
    data = query.data
    if "availability" in data:
        action = "check_availability"
    else:
        action = "check_resources"
    
    # РћР±РЅРѕРІР»СЏРµРј РєСЌС€
    targeted_checks.server_cache = None
    
    # РџРѕРєР°Р·С‹РІР°РµРј РѕР±РЅРѕРІР»РµРЅРЅРѕРµ РјРµРЅСЋ
    show_server_selection_menu(update, context, action)
