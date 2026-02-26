"""
/bot/handlers/callbacks.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
A single router for callbacks.
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р•РґРёРЅС‹Р№ router callbackвЂ™РѕРІ.
"""

import traceback

from telegram.error import BadRequest

from bot.menu.handlers import show_main_menu
from bot.handlers.settings_handlers import settings_callback_handler, BACKUP_SETTINGS_CALLBACKS
from core.monitor_core import (
    manual_check_handler,
    monitor_status,
    silent_status_handler,
    control_panel_handler,
    toggle_monitoring_handler,
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.base import check_access, deny_access
from modules.targeted_checks import targeted_checks
from extensions.extension_manager import extension_manager
from bot.handlers.extensions import (
    show_extensions_menu,
    extensions_callback_handler
)

from lib.logging import debug_log


def _safe_answer(query, **kwargs):
    try:
        query.answer(**kwargs)
    except BadRequest as e:
        # Callback query can be too old or already answered; ignore.
        debug_log(f"вљ пёЏ callback answer skipped: {e}")

def _server_result_keyboard(server_ip: str) -> InlineKeyboardMarkup:
    row_actions = [
        InlineKeyboardButton("рџ“Ў Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ", callback_data=f"check_availability_{server_ip}")
    ]
    row_menus = [
        InlineKeyboardButton("рџ–Ґ Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРµСЂР°", callback_data="show_availability_menu")
    ]

    if extension_manager.is_extension_enabled("resource_monitor"):
        row_actions.append(InlineKeyboardButton("рџ“Љ Р РµСЃСѓСЂСЃС‹", callback_data=f"check_resources_{server_ip}"))
        row_menus.append(InlineKeyboardButton("рџ’» Р РµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР°", callback_data="show_resources_menu"))

    return InlineKeyboardMarkup([
        row_actions,
        row_menus,
        [
            InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data="main_menu"),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data="close"),
        ],
    ])


def handle_check_single_callback(update, context, server_ip):
    """РћР±СЂР°Р±РѕС‚РєР° callback РїСЂРѕРІРµСЂРєРё РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    _safe_answer(query)

    from bot.handlers.commands import handle_check_single_server
    result = handle_check_single_server(update, context, server_ip)

    query.edit_message_text(
        text=result,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџ“Љ РџСЂРѕРІРµСЂРёС‚СЊ СЂРµСЃСѓСЂСЃС‹", callback_data=f'check_resources_{server_ip}')],
            [InlineKeyboardButton("рџ”„ РџСЂРѕРІРµСЂРёС‚СЊ СЃРЅРѕРІР°", callback_data=f'check_single_{server_ip}')],
            [InlineKeyboardButton("в†©пёЏ Р’С‹Р±СЂР°С‚СЊ РґСЂСѓРіРѕР№", callback_data='check_single_menu')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )


def handle_check_resources_callback(update, context, server_ip):
    """РћР±СЂР°Р±РѕС‚РєР° callback РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    _safe_answer(query)

    if not extension_manager.is_extension_enabled("resource_monitor"):
        query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    from bot.handlers.commands import handle_check_server_resources
    result = handle_check_server_resources(update, context, server_ip)

    query.edit_message_text(
        text=result,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data=f'check_resources_{server_ip}')],
            [InlineKeyboardButton("рџ“Ў РџСЂРѕРІРµСЂРёС‚СЊ РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ", callback_data=f'check_single_{server_ip}')],
            [InlineKeyboardButton("в†©пёЏ Р’С‹Р±СЂР°С‚СЊ РґСЂСѓРіРѕР№", callback_data='check_resources_menu')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])
    )


def handle_server_selection_menu(update, context, action="check_single"):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ РІС‹Р±РѕСЂР° СЃРµСЂРІРµСЂР°"""
    query = update.callback_query
    _safe_answer(query)

    from bot.handlers.commands import create_server_selection_keyboard

    if action == "check_single":
        message = "рџ“Ў *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё:*"
    elif action == "check_resources":
        if not extension_manager.is_extension_enabled("resource_monitor"):
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
            return
        message = "рџ“Љ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ:*"
    else:
        message = "рџ”Ќ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ:*"

    keyboard = create_server_selection_keyboard(action=action)

    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

def callback_router(update, context):
    debug_log("рџ§­ ROUTER MARKER v1: entered callback_router()")
    try:
        query = update.callback_query
        data = query.data

        debug_log(f"рџ“Ґ CALLBACK DATA: {data}")

        # РґР°Р»СЊС€Рµ РІР°С€ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ РєРѕРґ router...

    except Exception as e:
        debug_log(f"рџ’Ґ callback_router crashed: {e}\n{traceback.format_exc()}")
        # Р¤РѕР»Р»Р±РµРє РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ (С‡С‚РѕР±С‹ РІРёРґРµС‚СЊ РїСЂРѕР±Р»РµРјСѓ РІ Telegram)
        try:
            if update.callback_query:
                _safe_answer(update.callback_query, text="вќЊ РћС€РёР±РєР° РѕР±СЂР°Р±РѕС‚С‡РёРєР°. РџРѕРґСЂРѕР±РЅРѕСЃС‚Рё РІ Р»РѕРіР°С….", show_alert=True)
        except Exception:
            pass
        
    query = update.callback_query
    data = query.data

    debug_log(f"рџ“Ґ CALLBACK DATA: {data}")
    
    if not check_access(update):
        deny_access(update)
        return

    _safe_answer(query)

    # ------------------------------------------------
    # Р“Р»Р°РІРЅРѕРµ РјРµРЅСЋ
    # ------------------------------------------------
    if data == 'main_menu':
        from bot.menu.handlers import show_main_menu
        show_main_menu(update, context)

    elif data == 'about_bot':
        from bot.menu.handlers import show_about_bot
        show_about_bot(update, context)

    # ------------------------------------------------
    # Р”РћРЎРўРЈРџРќРћРЎРўР¬ Р’РЎР•РҐ РЎР•Р Р’Р•Р РћР’ (СЂСѓС‡РЅР°СЏ РїСЂРѕРІРµСЂРєР°)
    # ------------------------------------------------
    elif data == 'manual_check':
        manual_check_handler(update, context)
        
    # ------------------------------------------------
    # РћР”РРќ РЎР•Р Р’Р•Р  (РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ)
    # ------------------------------------------------
    elif data == 'show_availability_menu':
        query.edit_message_text(
            "рџ“Ў *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_availability"
            )
        )

    elif data.startswith('check_availability_'):
        server_id = data.replace('check_availability_', '')

        success, server, message = targeted_checks.check_single_server_availability(server_id)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=_server_result_keyboard(server_id)
        )

    # ------------------------------------------------
    # Р Р•РЎРЈР РЎР« РЎР•Р Р’Р•Р Рђ
    # ------------------------------------------------
    elif data == 'show_resources_menu':
        if not extension_manager.is_extension_enabled("resource_monitor"):
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
            return
        query.edit_message_text(
            "рџ“Љ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_resources"
            )
        )

    elif data.startswith('check_resources_'):
        if not extension_manager.is_extension_enabled("resource_monitor"):
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
            return
        server_id = data.replace('check_resources_', '')

        success, server, message = targeted_checks.check_single_server_resources(server_id)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=_server_result_keyboard(server_id)
        )

    # ------------------------------------------------
    # РџР РћР’Р•Р РљРђ Р Р•РЎРЈР РЎРћР’ Р’РЎР•РҐ РЎР•Р Р’Р•Р РћР’
    # ------------------------------------------------
    elif data == 'check_resources':
        if not extension_manager.is_extension_enabled("resource_monitor"):
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
            return
        query.edit_message_text(
            "рџ“Љ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ РґР»СЏ РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_resources"
            )
        )

    # ------------------------------------------------
    # РЎРўРђРўРЈРЎ / РџР РћР’Р•Р РљРђ / РЈРџР РђР’Р›Р•РќРР• (monitor_core)
    # ------------------------------------------------
    elif data == 'monitor_status':
        monitor_status(update, context)

    elif data == 'manual_check':
        manual_check_handler(update, context)

    elif data == 'silent_status':
        silent_status_handler(update, context)

    elif data == 'force_silent':
        from core.monitor_core import force_silent_handler
        force_silent_handler(update, context)

    elif data == 'force_loud':
        from core.monitor_core import force_loud_handler
        force_loud_handler(update, context)

    elif data == 'auto_mode':
        from core.monitor_core import auto_mode_handler
        auto_mode_handler(update, context)

    elif data == 'toggle_silent':
        from core.monitor_core import toggle_silent_mode_handler
        toggle_silent_mode_handler(update, context)

    elif data == 'control_panel':
        control_panel_handler(update, context)

    elif data == 'toggle_monitoring':
        toggle_monitoring_handler(update, context)

    elif data == 'pause_monitoring':
        from core.monitor_core import pause_monitoring_handler
        pause_monitoring_handler(update, context)

    elif data == 'resume_monitoring':
        from core.monitor_core import resume_monitoring_handler
        resume_monitoring_handler(update, context)

    elif data == 'servers_list':
        from extensions.server_checks import servers_list_handler
        servers_list_handler(update, context)

    elif data == 'zfs_menu':
        from bot.handlers.settings_handlers import show_zfs_status_summary
        show_zfs_status_summary(update, context)

    elif data in ('full_report', 'daily_report'):
        # РІ monitor_core СЌС‚Рѕ РѕРґРёРЅ Рё С‚РѕС‚ Р¶Рµ handler РІ СЃС‚Р°СЂРѕРј РјРµРЅСЋ
        from core.monitor_core import send_morning_report_handler
        send_morning_report_handler(update, context)

    # ------------------------------------------------
    # РќРђРЎРўР РћР™РљР (settings_handlers)
    # ------------------------------------------------
    elif data.startswith(('settings_', 'set_', 'manage_', 'ssh_', 'windows_', 'server_type_')) or data in {
        'add_chat',
        'remove_chat',
        'add_tamtam_chat',
        'remove_tamtam_chat',
    }:
        # settings_handlers СЃР°Рј СЂР°Р·Р±РёСЂР°РµС‚ РІСЃРµ СЌС‚Рё РІРµС‚РєРё
        settings_callback_handler(update, context)

    # ------------------------------------------------
    # РќРђРЎРўР РћР™РљР Р‘Р­РљРђРџРћР’ (settings_handlers)
    # ------------------------------------------------
    elif data in BACKUP_SETTINGS_CALLBACKS or data.startswith(('delete_pattern_', 'edit_pattern_', 'db_default_', 'stock_pattern_select_')):
        settings_callback_handler(update, context)

    elif data.startswith('supplier_stock_'):
        settings_callback_handler(update, context)

    # ------------------------------------------------
    # Р Р•РЎРЈР РЎР«: РіСЂСѓРїРїС‹/СЃРїРёСЃРєРё (TargetedChecks)
    # ------------------------------------------------
    elif data.startswith('server_group_'):
        # С„РѕСЂРјР°С‚: server_group_<type>_<action>
        # РїСЂРёРјРµСЂ: server_group_ssh_check_resources
        parts = data.split('_', 3)
        # parts = ['server', 'group', '<type>', '<action>']
        if len(parts) == 4:
            server_type = parts[2]
            action = parts[3]
            query.edit_message_text(
                f"рџ“‹ *Р’С‹Р±РµСЂРёС‚Рµ СЃРµСЂРІРµСЂ:*",
                parse_mode='Markdown',
                reply_markup=targeted_checks.create_server_group_menu(server_type, action)
            )
        else:
            query.edit_message_text("вќЊ РќРµРєРѕСЂСЂРµРєС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РјРµРЅСЋ РіСЂСѓРїРїС‹ СЃРµСЂРІРµСЂРѕРІ")

    # (РїРѕ Р¶РµР»Р°РЅРёСЋ) QUICK SEARCH / REFRESH РјРѕР¶РЅРѕ РїСЂРѕСЃС‚Рѕ РіР°СЃРёС‚СЊ
    elif data.startswith(('quick_search_', 'refresh_')):
        _safe_answer(query, text="Р¤СѓРЅРєС†РёСЏ РѕС‚РєР»СЋС‡РµРЅР°", show_alert=False)

    # ------------------------------------------------
    # Р‘Р­РљРђРџР«
    # ------------------------------------------------
    elif data.startswith("backup_") or data.startswith("db_"):
        backup_enabled = extension_manager.is_extension_enabled("backup_monitor")
        db_enabled = extension_manager.is_extension_enabled("database_backup_monitor")
        mail_enabled = extension_manager.is_extension_enabled("mail_backup_monitor")
        stock_enabled = extension_manager.is_extension_enabled("stock_load_monitor")

        if data.startswith("db_") and not db_enabled:
            query.edit_message_text("рџ—ѓпёЏ РњРѕРґСѓР»СЊ Р±СЌРєР°РїРѕРІ Р‘Р” РѕС‚РєР»СЋС‡С‘РЅ")
            return

        if data == "backup_main" and not (backup_enabled or db_enabled or mail_enabled or stock_enabled):
            query.edit_message_text("рџ’ѕ РњРѕРґСѓР»СЊ Р±СЌРєР°РїРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
            return

        if data == "backup_databases" and not db_enabled:
            query.edit_message_text("рџ—ѓпёЏ РњРѕРґСѓР»СЊ Р±СЌРєР°РїРѕРІ Р‘Р” РѕС‚РєР»СЋС‡С‘РЅ")
            return

        if data == "backup_mail" and not mail_enabled:
            query.edit_message_text("рџ“¬ РњРѕРґСѓР»СЊ Р±СЌРєР°РїРѕРІ РїРѕС‡С‚С‹ РѕС‚РєР»СЋС‡С‘РЅ")
            return

        if data == "backup_stock_loads" and not stock_enabled:
            query.edit_message_text("рџ“¦ РњРѕРґСѓР»СЊ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
            return

        if (
            data.startswith("backup_")
            and data not in ("backup_main", "backup_databases", "backup_mail", "backup_stock_loads")
            and not backup_enabled
        ):
            query.edit_message_text("рџ’ѕ РњРѕРґСѓР»СЊ Р±СЌРєР°РїРѕРІ Proxmox РѕС‚РєР»СЋС‡С‘РЅ")
            return

        from extensions.backup_monitor.bot_handler import backup_callback
        backup_callback(update, context)
        return

    # ------------------------------------------------
    # Р РђРЎРЁРР Р•РќРРЇ
    # ------------------------------------------------
    elif data == 'extensions_menu':
        show_extensions_menu(update, context)

    elif data.startswith('ext_'):
        extensions_callback_handler(update, context)

    # ------------------------------------------------
    # Р—Р°РєСЂС‹С‚РёРµ
    # ------------------------------------------------
    elif data == 'close':
        query.delete_message()
