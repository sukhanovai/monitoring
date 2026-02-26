"""
/extensions/backup_monitor/backup_handlers.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for the backup bot
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РћР±СЂР°Р±РѕС‚С‡РёРєРё РґР»СЏ Р±РѕС‚Р° Р±СЌРєР°РїРѕРІ
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from extensions.extension_manager import extension_manager
from .backup_utils import DisplayFormatters
formatters = DisplayFormatters()
from telegram.utils.helpers import escape_markdown

def _md(s) -> str:
    return escape_markdown(str(s or ""), version=1)

logger = logging.getLogger(__name__)

# === РЈРўРР›РРўР« Р”Р›РЇ РЎРћР—Р”РђРќРРЇ РљР›РђР’РРђРўРЈР  ===

def create_main_menu():
    """РЎРѕР·РґР°РµС‚ РіР»Р°РІРЅРѕРµ РјРµРЅСЋ Р±СЌРєР°РїРѕРІ"""
    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ–ҐпёЏ РџРѕ С…РѕСЃС‚Р°Рј", callback_data='backup_hosts')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ—ѓпёЏ Р‘СЌРєР°РїС‹ Р‘Р”", callback_data='backup_databases')])

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“¬ Р‘СЌРєР°РїС‹ РїРѕС‡С‚С‹", callback_data='backup_mail')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“¦ РћСЃС‚Р°С‚РєРё 1РЎ", callback_data='backup_stock_loads')])

    keyboard.extend([
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])

    return InlineKeyboardMarkup(keyboard)

def create_proxmox_menu():
    """РЎРѕР·РґР°РµС‚ РјРµРЅСЋ Р±СЌРєР°РїРѕРІ Proxmox"""
    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("рџ–ҐпёЏ РџРѕ С…РѕСЃС‚Р°Рј", callback_data='backup_hosts')])

    keyboard.extend([
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])

    return InlineKeyboardMarkup(keyboard)

def create_navigation_buttons(back_button='backup_main', refresh_button=None, close=True):
    """РЎРѕР·РґР°РµС‚ СЃС‚Р°РЅРґР°СЂС‚РЅС‹Рµ РєРЅРѕРїРєРё РЅР°РІРёРіР°С†РёРё"""
    buttons = []
    
    if refresh_button:
        buttons.append([InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data=refresh_button)])
    
    buttons.append([InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_button)])
    buttons.append([InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')])
    
    if close:
        buttons.append([InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')])
    
    return InlineKeyboardMarkup(buttons)

def create_hosts_keyboard(
    hosts,
    host_statuses,
    show_problems_button=True,
    back_button='backup_main',
):
    """РЎРѕР·РґР°РµС‚ РєР»Р°РІРёР°С‚СѓСЂСѓ РґР»СЏ СЃРїРёСЃРєР° С…РѕСЃС‚РѕРІ"""
    keyboard = []
    
    # РЎС‚Р°С‚РёСЃС‚РёРєР°
    success_count = sum(1 for status in host_statuses.values() if status == 'success')
    problem_count = len(hosts) - success_count
    
    keyboard.append([InlineKeyboardButton(
        f"рџ“Љ РЎС‚Р°С‚СѓСЃ: {success_count}вњ… {problem_count}рџљЁ",
        callback_data='no_action'
    )])
    keyboard.append([])
    
    # РЎРѕСЂС‚РёСЂСѓРµРј С…РѕСЃС‚С‹ РїРѕ СЃС‚Р°С‚СѓСЃСѓ
    sorted_hosts = sorted(hosts, key=lambda x: (
        host_statuses[x] != "failed",
        host_statuses[x] != "recent_failed", 
        host_statuses[x] != "stale",
        host_statuses[x] != "old",
        x.lower()
    ))
    
    # РЎРѕР·РґР°РµРј РєРЅРѕРїРєРё РїРѕ 2 РІ СЂСЏРґ
    for i in range(0, len(sorted_hosts), 2):
        row = []
        for j in range(2):
            if i + j < len(sorted_hosts):
                host_name = sorted_hosts[i + j]
                status = host_statuses[host_name]
                display_name = formatters.get_host_display_name(host_name, status)
                row.append(InlineKeyboardButton(display_name, callback_data=f'backup_host_{host_name}'))
        if row:
            keyboard.append(row)
    
    # РљРЅРѕРїРєР° РїСЂРѕР±Р»РµРјРЅС‹С… С…РѕСЃС‚РѕРІ
    if show_problems_button and problem_count > 0:
        keyboard.append([InlineKeyboardButton(
            f"рџ”Ќ РџРѕРєР°Р·Р°С‚СЊ РїСЂРѕР±Р»РµРјРЅС‹Рµ ({problem_count})", 
            callback_data='backup_stale_hosts'
        )])
    
    keyboard.append([
        InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data=back_button),
        InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
        InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_databases_keyboard(databases_by_type, problem_db_count=0):
    """РЎРѕР·РґР°РµС‚ РєР»Р°РІРёР°С‚СѓСЂСѓ РґР»СЏ СЃРїРёСЃРєР° Р±Р°Р· РґР°РЅРЅС‹С…"""
    keyboard = []
    
    # Р”РѕР±Р°РІР»СЏРµРј СЃРµРєС†РёРё РґР»СЏ РєР°Р¶РґРѕРіРѕ С‚РёРїР°
    for backup_type, databases in databases_by_type.items():
        if databases:
            # РЎС‚Р°С‚РёСЃС‚РёРєР° РґР»СЏ С‚РёРїР°
            type_success = sum(1 for db in databases if db['status'] == 'success')
            type_total = len(databases)
            
            keyboard.append([InlineKeyboardButton(
                f"в”Ђв”Ђв”Ђв”Ђв”Ђ {formatters.get_type_display(backup_type)} ({type_success}вњ… {type_total-type_success}рџљЁ) в”Ђв”Ђв”Ђв”Ђв”Ђ",
                callback_data='no_action'
            )])
            
            # РљРЅРѕРїРєРё Р±Р°Р· РґР°РЅРЅС‹С…
            current_row = []
            for i, db_info in enumerate(sorted(databases, key=lambda x: x['display_name'])):
                display_name = formatters.get_db_display_name(db_info['display_name'], db_info['status'])
                
                current_row.append(InlineKeyboardButton(
                    display_name, 
                    callback_data=f'db_detail_{backup_type}__{db_info["original_name"]}'
                ))
                
                # Р Р°Р·РјРµС‰Р°РµРј РїРѕ 2 РєРЅРѕРїРєРё РІ СЃС‚СЂРѕРєРµ
                if len(current_row) == 2 or i == len(databases) - 1:
                    keyboard.append(current_row)
                    current_row = []
            
            keyboard.append([])  # РџСѓСЃС‚Р°СЏ СЃС‚СЂРѕРєР° РјРµР¶РґСѓ СЃРµРєС†РёСЏРјРё
    
    # РЈР±РёСЂР°РµРј РїРѕСЃР»РµРґРЅСЋСЋ РїСѓСЃС‚СѓСЋ СЃС‚СЂРѕРєСѓ
    if keyboard and not keyboard[-1]:
        keyboard.pop()
    
    # РљРЅРѕРїРєРё СѓРїСЂР°РІР»РµРЅРёСЏ
    keyboard.extend([
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='backup_databases')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

# === РћРЎРќРћР’РќР«Р• РћР‘Р РђР‘РћРўР§РРљР ===

def show_main_menu(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РіР»Р°РІРЅРѕРµ РјРµРЅСЋ Р±СЌРєР°РїРѕРІ"""
    query.edit_message_text(
        "рџ’ѕ *РњРѕРЅРёС‚РѕСЂРёРЅРі Р±СЌРєР°РїРѕРІ Proxmox*\n\nР’С‹Р±РµСЂРёС‚Рµ РѕРїС†РёСЋ:",
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

def show_proxmox_menu(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ Р±СЌРєР°РїРѕРІ Proxmox"""
    query.edit_message_text(
        "рџ’ѕ *Р‘СЌРєР°РїС‹ Proxmox*\n\nР’С‹Р±РµСЂРёС‚Рµ РѕРїС†РёСЋ:",
        parse_mode='Markdown',
        reply_markup=create_proxmox_menu()
    )

def show_today_status(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ Р±СЌРєР°РїРѕРІ Р·Р° СЃРµРіРѕРґРЅСЏ"""
    try:
        results = backup_bot.get_today_status()
        
        if not results:
            query.edit_message_text(
                "рџ“Љ *Р‘СЌРєР°РїС‹ Р·Р° СЃРµРіРѕРґРЅСЏ*\n\nРќРµС‚ РґР°РЅРЅС‹С… Р·Р° СЃРµРіРѕРґРЅСЏ",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(refresh_button='backup_today')
            )
            return

        message = "рџ“Љ *Р‘СЌРєР°РїС‹ Р·Р° СЃРµРіРѕРґРЅСЏ*\n\n"
        
        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С…РѕСЃС‚Р°Рј
        hosts = {}
        for host_name, status, count, last_report in results:
            if host_name not in hosts:
                hosts[host_name] = []
            hosts[host_name].append((status, count, last_report))

        for host_name, backups in hosts.items():
            message += f"*{host_name}:*\n"
            for status, count, last_report in backups:
                status_icon = "вњ…" if status == 'success' else "вќЊ"
                message += f"{status_icon} {status}: {count} РѕС‚С‡РµС‚РѕРІ\n"
            message += "\n"

        message += f"рџ•’ РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(refresh_button='backup_today')
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_today_status: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def show_recent_backups(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РїРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹"""
    try:
        results = backup_bot.get_recent_backups(24)
        
        if not results:
            query.edit_message_text(
                "вЏ° *РџРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹ (24С‡)*\n\nРќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРѕСЃР»РµРґРЅРёРµ 24 С‡Р°СЃР°",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(refresh_button='backup_24h')
            )
            return

        message = "вЏ° *РџРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹ (24С‡)*\n\n"
        
        for host_name, status, duration, total_size, error_message, received_at in results[:10]:
            status_icon = "вњ…" if status == 'success' else "вќЊ"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"{status_icon} *{host_name}* ({time_str})\n"
            message += f"РЎС‚Р°С‚СѓСЃ: {status}\n"
            if duration:
                message += f"Р’СЂРµРјСЏ: {duration}\n"
            if total_size:
                message += f"Р Р°Р·РјРµСЂ: {total_size}\n"
            if error_message and status == 'failed':
                message += f"РћС€РёР±РєР°: {error_message[:100]}...\n"
            message += "\n"

        message += f"рџ•’ РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(refresh_button='backup_24h')
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_recent_backups: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def show_failed_backups(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РЅРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹"""
    try:
        results = backup_bot.get_failed_backups(1)
        
        if not results:
            query.edit_message_text(
                "вќЊ *РќРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ (24С‡)*\n\nРќРµС‚ РЅРµСѓРґР°С‡РЅС‹С… Р±СЌРєР°РїРѕРІ Р·Р° РїРѕСЃР»РµРґРЅРёРµ 24 С‡Р°СЃР° рџЋ‰",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(refresh_button='backup_failed')
            )
            return

        message = "вќЊ *РќРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ (24С‡)*\n\n"
        
        for host_name, status, error_message, received_at in results:
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"*{host_name}* ({time_str})\n"
            if error_message:
                message += f"РћС€РёР±РєР°: {error_message[:150]}...\n"
            message += "\n"

        message += f"рџ•’ РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(refresh_button='backup_failed')
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_failed_backups: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def show_hosts_menu(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ РІС‹Р±РѕСЂР° С…РѕСЃС‚РѕРІ"""
    try:
        hosts = backup_bot.get_all_hosts()
        
        if not hosts:
            query.edit_message_text(
                "рџ–ҐпёЏ *Р‘СЌРєР°РїС‹ РїРѕ С…РѕСЃС‚Р°Рј*\n\nРќРµС‚ РґР°РЅРЅС‹С… Рѕ С…РѕСЃС‚Р°С…",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons()
            )
            return

        # РџРѕР»СѓС‡Р°РµРј СЃС‚Р°С‚СѓСЃС‹ РґР»СЏ РІСЃРµС… С…РѕСЃС‚РѕРІ
        host_statuses = {}
        for host_name in hosts:
            status = backup_bot.get_host_display_status(host_name)
            host_statuses[host_name] = status

        # РЎРѕР·РґР°РµРј СЃРѕРѕР±С‰РµРЅРёРµ СЃ Р»РµРіРµРЅРґРѕР№
        message = "рџ–ҐпёЏ *Р’С‹Р±РµСЂРёС‚Рµ С…РѕСЃС‚ РґР»СЏ РїСЂРѕСЃРјРѕС‚СЂР° Р±СЌРєР°РїРѕРІ:*\n\n"
        message += "*Р›РµРіРµРЅРґР°:*\n"
        message += "вњ… - РІСЃРµ Р±СЌРєР°РїС‹ СѓСЃРїРµС€РЅС‹\n"
        message += "рџ”ґ - РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї РЅРµСѓРґР°С‡РµРЅ\n"
        message += "рџџ  - РµСЃС‚СЊ РЅРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ РІ РёСЃС‚РѕСЂРёРё\n"
        message += f"рџџЎ - РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї СЃС‚Р°СЂС€Рµ {backup_bot.backup_alert_hours}С‡\n"
        message += f"вљ« - РЅРµС‚ Р±СЌРєР°РїРѕРІ >{backup_bot.backup_stale_hours}С‡\n"
        message += "вљЄ - СЃС‚Р°С‚СѓСЃ РЅРµРёР·РІРµСЃС‚РµРЅ\n\n"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_hosts_keyboard(
                hosts,
                host_statuses,
                back_button='main_menu',
            )
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_hosts_menu: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def show_stale_hosts(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ С‚РѕР»СЊРєРѕ РїСЂРѕР±Р»РµРјРЅС‹Рµ С…РѕСЃС‚С‹"""
    try:
        hosts = backup_bot.get_all_hosts()
        problem_hosts = []
        
        for host_name in hosts:
            status = backup_bot.get_host_display_status(host_name)
            if status in ["failed", "recent_failed", "stale"]:
                recent = backup_bot.get_host_recent_status(host_name, 72)
                last_time = recent[0][1] if recent else None
                problem_hosts.append((host_name, status, last_time))
        
        if not problem_hosts:
            query.edit_message_text(
                "рџЋ‰ *РџСЂРѕР±Р»РµРјРЅС‹Рµ С…РѕСЃС‚С‹*\n\nРќРµС‚ С…РѕСЃС‚РѕРІ СЃ РїСЂРѕР±Р»РµРјРЅС‹РјРё Р±СЌРєР°РїР°РјРё!",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='backup_hosts')
            )
            return
        
        keyboard = []
        message = "рџљЁ *РџСЂРѕР±Р»РµРјРЅС‹Рµ С…РѕСЃС‚С‹:*\n\n"
        
        # РЎРѕСЂС‚РёСЂСѓРµРј РїРѕ СЃРµСЂСЊРµР·РЅРѕСЃС‚Рё РїСЂРѕР±Р»РµРјС‹
        problem_hosts.sort(key=lambda x: (x[1] != "failed", x[1] != "recent_failed", x[1] != "stale"))
        
        for host_name, problem_type, last_backup in problem_hosts:
            time_ago = backup_bot.format_time_ago(last_backup)
            
            if problem_type == 'failed':
                problem_text = f"рџ”ґ {host_name} - РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї РЅРµСѓРґР°С‡РµРЅ ({time_ago})"
            elif problem_type == 'recent_failed':
                problem_text = f"рџџ  {host_name} - РµСЃС‚СЊ РЅРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ ({time_ago})"
            else:
                problem_text = f"вљ« {host_name} - РЅРµС‚ СЃРІРµР¶РёС… Р±СЌРєР°РїРѕРІ ({time_ago})"
            
            message += f"вЂў {problem_text}\n"
            
            keyboard.append([InlineKeyboardButton(
                f"рџ”Ќ {host_name}", 
                callback_data=f'backup_host_{host_name}'
            )])
        
        message += f"\n*Р’СЃРµРіРѕ РїСЂРѕР±Р»РµРјРЅС‹С… С…РѕСЃС‚РѕРІ:* {len(problem_hosts)}"
        
        keyboard.extend([
            [InlineKeyboardButton("рџ“‹ Р’СЃРµ С…РѕСЃС‚С‹", callback_data='backup_hosts')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')]
        ])
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_stale_hosts: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def show_host_status(query, backup_bot, host_name):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ С…РѕСЃС‚Р°"""
    try:
        results = backup_bot.get_host_status(host_name)
        
        if not results:
            query.edit_message_text(
                f"рџ–ҐпёЏ *Р‘СЌРєР°РїС‹ {host_name}*\n\nРќРµС‚ РґР°РЅРЅС‹С… РїРѕ СЌС‚РѕРјСѓ С…РѕСЃС‚Сѓ",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='backup_hosts')
            )
            return

        message = f"рџ–ҐпёЏ *Р‘СЌРєР°РїС‹ {host_name}*\n\n"
        
        for status, duration, total_size, error_message, received_at in results:
            status_icon = "вњ…" if status == 'success' else "вќЊ"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"{status_icon} *{time_str}* - {status}\n"
            if duration:
                message += f"Р’СЂРµРјСЏ: {duration}\n"
            if total_size:
                message += f"Р Р°Р·РјРµСЂ: {total_size}\n"
            if error_message and status == 'failed':
                message += f"РћС€РёР±РєР°: {error_message[:100]}...\n"
            message += "\n"

        message += f"рџ•’ РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='backup_hosts', 
                refresh_button=None
            )
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_host_status: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def _normalize_db_key(name: str) -> str:
    return str(name or "").replace("-", "_").lower()

def _normalize_backup_type(backup_type: str, db_name: str) -> str:
    if _normalize_db_key(db_name) == "trade" and backup_type == "client":
        return "company_database"
    return backup_type

def _normalize_config_backup_type(category: str) -> str:
    normalized = _normalize_db_key(category)
    if normalized in ("company", "company_database"):
        return "company_database"
    if normalized in ("barnaul", "barnaul_backups"):
        return "barnaul"
    if normalized in ("client", "client_databases"):
        return "client"
    if normalized in ("yandex", "yandex_backups"):
        return "yandex"
    return category

def show_database_backups_menu(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РјРµРЅСЋ СЃ Р±Р°Р·Р°РјРё РґР°РЅРЅС‹С… (РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё Рё backups.db)"""
    try:
        logger.info("рџ§Є BACKUP DB: entering show_database_backups_menu")

        from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG

        if not isinstance(DATABASE_BACKUP_CONFIG, dict):
            DATABASE_BACKUP_CONFIG = {}

        rows = backup_bot.execute_query(
            """
            SELECT DISTINCT
                backup_type,
                database_name,
                COALESCE(database_display_name, '')
            FROM database_backups
            ORDER BY backup_type, database_name
            """,
            ()
        ) or []

        # Р“СЂСѓРїРїРёСЂСѓРµРј Р‘Р” РїРѕ С‚РёРїСѓ (Р±РµСЂС‘Рј РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё)
        db_by_type = {}
        allowed_by_type = {}

        for category, databases in DATABASE_BACKUP_CONFIG.items():
            if not isinstance(databases, dict):
                continue
            backup_type = _normalize_config_backup_type(category)
            allowed_by_type.setdefault(backup_type, set())
            for db_name in databases.keys():
                normalized_key = _normalize_db_key(db_name)
                allowed_by_type[backup_type].add(normalized_key)
                db_by_type.setdefault(backup_type, {})
                if normalized_key not in db_by_type[backup_type]:
                    db_by_type[backup_type][normalized_key] = {
                        "db_name": db_name,
                        "label": db_name,
                    }

        for backup_type, db_name, display_name in rows:
            if not backup_type or not db_name:
                continue

            backup_type = _normalize_backup_type(backup_type, db_name)
            normalized_key = _normalize_db_key(db_name)
            if backup_type not in allowed_by_type:
                continue
            if normalized_key not in allowed_by_type[backup_type]:
                continue
            db_by_type.setdefault(backup_type, {})
            if normalized_key not in db_by_type[backup_type]:
                db_by_type[backup_type][normalized_key] = {
                    "db_name": db_name,
                    "label": db_name,
                }

        if not db_by_type:
            message = "рџ—ѓпёЏ *Р‘СЌРєР°РїС‹ Р±Р°Р· РґР°РЅРЅС‹С…*\n\nвќЊ РќРµС‚ РґР°РЅРЅС‹С… Рѕ Р±СЌРєР°РїР°С… Р‘Р”."
            keyboard = [
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ]
            try:
                query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except BadRequest as exc:
                if "Message is not modified" in str(exc):
                    query.answer("РњРµРЅСЋ СѓР¶Рµ РѕС‚РєСЂС‹С‚Рѕ", show_alert=False)
                    return
                raise
            return

        keyboard = []
        for backup_type in sorted(db_by_type.keys()):
            type_display = formatters.get_type_display(backup_type)
            keyboard.append([InlineKeyboardButton(
                f"в”Ђв”Ђв”Ђв”Ђв”Ђ {type_display} в”Ђв”Ђв”Ђв”Ђв”Ђ",
                callback_data='no_action'
            )])

            current_row = []
            entries = list(db_by_type[backup_type].values())
            entries.sort(key=lambda item: item["label"].lower())
            for entry in entries:
                db_name = entry["db_name"]
                display_name = entry["label"]
                try:
                    effective_type = _get_latest_backup_type(backup_bot, db_name, hours=48) or backup_type
                    status = backup_bot.get_database_display_status(effective_type, db_name)
                    display_btn = formatters.get_db_display_name(display_name, status)

                    current_row.append(InlineKeyboardButton(
                        display_btn,
                        callback_data=f'db_detail_{backup_type}__{db_name}'
                    ))

                    if len(current_row) == 2:
                        keyboard.append(current_row)
                        current_row = []
                except Exception as e:
                    logger.error(f"вќЊ РћС€РёР±РєР° РѕР±СЂР°Р±РѕС‚РєРё Р‘Р” {backup_type}/{db_name}: {e}")
                    continue

            if current_row:
                keyboard.append(current_row)

        keyboard.extend([
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
             InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
        ])

        message = "рџ—ѓпёЏ *Р‘СЌРєР°РїС‹ Р±Р°Р· РґР°РЅРЅС‹С…*\n\n"
        message += "*Р›РµРіРµРЅРґР°:*\n"
        message += "вњ… - РІСЃРµ Р±СЌРєР°РїС‹ СѓСЃРїРµС€РЅС‹\n"
        message += "рџ”ґ - РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї РЅРµСѓРґР°С‡РµРЅ\n"
        message += "рџџ  - РµСЃС‚СЊ РЅРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ РІ РёСЃС‚РѕСЂРёРё\n"
        message += "рџџЎ - РµСЃС‚СЊ РѕС€РёР±РєРё РёР»Рё РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї СЃС‚Р°СЂС€Рµ 24С‡\n"
        message += "вљ« - РЅРµС‚ Р±СЌРєР°РїРѕРІ >48С‡\n"
        message += "вљЄ - СЃС‚Р°С‚СѓСЃ РЅРµРёР·РІРµСЃС‚РµРЅ\n\n"
        message += "Р’С‹Р±РµСЂРёС‚Рµ Р±Р°Р·Сѓ РґР°РЅРЅС‹С… РґР»СЏ РїСЂРѕСЃРјРѕС‚СЂР° РґРµС‚Р°Р»РµР№:"
        try:
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as exc:
            if "Message is not modified" in str(exc):
                query.answer("РњРµРЅСЋ СѓР¶Рµ РѕС‚РєСЂС‹С‚Рѕ", show_alert=False)
                return
            raise

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_database_backups_menu: {e}")
        import traceback
        logger.error(traceback.format_exc())
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё С„РѕСЂРјРёСЂРѕРІР°РЅРёРё РјРµРЅСЋ Р±Р°Р· РґР°РЅРЅС‹С…")

def show_mail_backups(query, backup_bot, hours=72):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РїРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    try:
        backups = backup_bot.get_mail_backups(hours=hours, limit=10)

        if not backups:
            message = (
                "рџ“¬ *Р‘СЌРєР°РїС‹ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°*\n\n"
                f"вќЊ РќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРѕСЃР»РµРґРЅРёРµ {hours} С‡Р°СЃРѕРІ."
            )
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='main_menu')
            )
            return

        message = f"рџ“¬ *Р‘СЌРєР°РїС‹ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР° (Р·Р° {hours}С‡)*\n\n"
        for status, size, path, received_at in backups:
            status_icon = "вњ…" if status == "success" else "вќЊ"
            time_ago = backup_bot.format_time_ago(received_at)
            size_text = _md(size) if size else "вЂ”"
            path_text = _md(path) if path else "вЂ”"
            message += f"{status_icon} {size_text} вЂ” {path_text} ({_md(time_ago)})\n"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='main_menu',
                refresh_button='backup_mail'
            )
        )

    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            query.answer("РњРµРЅСЋ СѓР¶Рµ РѕС‚РєСЂС‹С‚Рѕ", show_alert=False)
            return
        raise
    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_mail_backups: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С… РїРѕ РїРѕС‡С‚РѕРІС‹Рј Р±СЌРєР°РїР°Рј")

def show_stock_loads(query, backup_bot, hours=24):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЂРµР·СѓР»СЊС‚Р°С‚С‹ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ 1РЎ."""
    try:
        results = backup_bot.get_stock_loads(hours=hours)

        if not results:
            message = (
                "рџ“¦ *Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ 1РЎ*\n\n"
                f"вќЊ РќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРѕСЃР»РµРґРЅРёРµ {hours} С‡Р°СЃРѕРІ."
            )
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='main_menu')
            )
            return

        grouped = {}
        for source_name, supplier, status, rows_count, error_sample, received_at in results:
            grouped.setdefault(source_name or "РћСЃРЅРѕРІРЅРѕРµ РїСЂРµРґРїСЂРёСЏС‚РёРµ", []).append(
                (supplier, status, rows_count, error_sample, received_at)
            )

        total_suppliers = sum(len(items) for items in grouped.values())
        message = f"рџ“¦ *Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ 1РЎ (Р·Р° {hours}С‡)*\n"
        message += f"Р’СЃРµРіРѕ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ: {total_suppliers}\n\n"

        for source_name, items in grouped.items():
            message += f"*{_md(source_name)}* ({len(items)})\n"
            for supplier, status, rows_count, error_sample, received_at in items:
                status_icon = "вњ…" if status == "success" else "вљ пёЏ" if status == "warning" else "вќЊ"
                time_ago = backup_bot.format_time_ago(received_at)
                rows_text = f"{rows_count} СЃС‚СЂРѕРє" if rows_count else "СЃС‚СЂРѕРєРё: вЂ”"
                error_text = f" вЂ” {error_sample}" if error_sample else ""
                message += f"{status_icon} {_md(supplier)} ({rows_text}){error_text} ({_md(time_ago)})\n"
            message += "\n"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='main_menu',
                refresh_button='backup_stock_loads'
            )
        )

    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            query.answer("РњРµРЅСЋ СѓР¶Рµ РѕС‚РєСЂС‹С‚Рѕ", show_alert=False)
            return
        raise
    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_stock_loads: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С… РїРѕ РѕСЃС‚Р°С‚РєР°Рј")
                                
def show_stale_databases(query, backup_bot):
    """РџРѕРєР°Р·С‹РІР°РµС‚ С‚РѕР»СЊРєРѕ РїСЂРѕР±Р»РµРјРЅС‹Рµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…"""
    try:
        from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG
        
        problem_databases = []
        
        # РџСЂРѕРІРµСЂСЏРµРј РІСЃРµ Р±Р°Р·С‹ РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё
        config_mapping = []
        for category, databases in DATABASE_BACKUP_CONFIG.items():
            if not isinstance(databases, dict):
                continue
            config_mapping.append((_normalize_config_backup_type(category), databases))
        
        for backup_type, config_dict in config_mapping:
            for db_name in config_dict.keys():
                status = backup_bot.get_database_display_status(backup_type, db_name)
                if status not in ['success', 'unknown']:
                    recent = backup_bot.get_database_recent_status(backup_type, db_name, 72)
                    last_time = recent[0][1] if recent else None
                    problem_databases.append((backup_type, db_name, db_name, status, last_time))

        if not problem_databases:
            query.edit_message_text(
                "рџЋ‰ *РџСЂРѕР±Р»РµРјРЅС‹Рµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…*\n\nРќРµС‚ Р‘Р” СЃ РїСЂРѕР±Р»РµРјРЅС‹РјРё Р±СЌРєР°РїР°РјРё!",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='db_backups_list')
            )
            return
        
        keyboard = []
        message = "рџљЁ *РџСЂРѕР±Р»РµРјРЅС‹Рµ Р±Р°Р·С‹ РґР°РЅРЅС‹С…:*\n\n"
        
        # РЎРѕСЂС‚РёСЂСѓРµРј РїРѕ СЃРµСЂСЊРµР·РЅРѕСЃС‚Рё РїСЂРѕР±Р»РµРјС‹
        problem_priority = {'failed': 1, 'recent_failed': 2, 'warning': 3, 'recent_errors': 4, 'stale': 5, 'old': 6}
        problem_databases.sort(key=lambda x: (problem_priority.get(x[3], 99), x[2]))
        
        for backup_type, db_name, display_name, problem_type, last_backup in problem_databases:
            type_icon = formatters.TYPE_ICONS.get(backup_type, 'рџ“Ѓ')
            time_ago = backup_bot.format_time_ago(last_backup)
            
            if problem_type == 'failed':
                problem_text = f"рџ”ґ {type_icon} {display_name} - РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї РЅРµСѓРґР°С‡РµРЅ ({time_ago})"
            elif problem_type == 'recent_failed':
                problem_text = f"рџџ  {type_icon} {display_name} - РµСЃС‚СЊ РЅРµСѓРґР°С‡РЅС‹Рµ Р±СЌРєР°РїС‹ ({time_ago})"
            elif problem_type in ['warning', 'recent_errors']:
                problem_text = f"рџџЎ {type_icon} {display_name} - РµСЃС‚СЊ РѕС€РёР±РєРё РІ Р±СЌРєР°РїР°С… ({time_ago})"
            elif problem_type == 'stale':
                problem_text = f"вљ« {type_icon} {display_name} - РЅРµС‚ СЃРІРµР¶РёС… Р±СЌРєР°РїРѕРІ ({time_ago})"
            elif problem_type == 'old':
                problem_text = f"рџџЎ {type_icon} {display_name} - Р±СЌРєР°РїС‹ СѓСЃС‚Р°СЂРµР»Рё ({time_ago})"
            else:
                problem_text = f"вљЄ {type_icon} {display_name} - РїСЂРѕР±Р»РµРјР° ({time_ago})"
            
            message += f"вЂў {problem_text}\n"
            
            keyboard.append([InlineKeyboardButton(
                f"рџ”Ќ {display_name}", 
                callback_data=f'db_detail_{backup_type}__{db_name}'
            )])
        
        message += f"\n*Р’СЃРµРіРѕ РїСЂРѕР±Р»РµРјРЅС‹С… Р‘Р”:* {len(problem_databases)}"
        
        keyboard.extend([
            [InlineKeyboardButton("рџ“‹ Р’СЃРµ Р‘Р”", callback_data='db_backups_list')],
            [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='backup_databases')]
        ])
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_stale_databases: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def show_database_backups_summary(query, backup_bot, hours):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЃРІРѕРґРєСѓ РїРѕ Р±СЌРєР°РїР°Рј Р‘Р”"""
    try:
        stats = backup_bot.get_database_backups_stats(hours)
        
        if not stats:
            query.edit_message_text(
                f"рџ“Љ *Р‘СЌРєР°РїС‹ Р‘Р” ({hours}С‡)*\n\nРќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРѕСЃР»РµРґРЅРёРµ {hours} С‡Р°СЃРѕРІ",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(
                    back_button='backup_databases',
                    refresh_button=f'db_backups_{hours}h'
                )
            )
            return

        message = f"рџ“Љ *Р‘СЌРєР°РїС‹ Р‘Р” ({hours}С‡)*\n\n"
        
        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј
        by_type = {}
        for backup_type, db_name, db_display, status, count, last_backup in stats:
            normalized_type = _normalize_backup_type(backup_type, db_name)
            if normalized_type not in by_type:
                by_type[normalized_type] = []
            by_type[normalized_type].append((db_name, db_display, status, count, last_backup))

        for backup_type, databases in by_type.items():
            type_display = formatters.get_type_display(backup_type)
            message += f"*{type_display}:*\n"
            
            # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ Р±Р°Р·Р°Рј
            db_stats = {}
            for db_name, db_display, status, count, last_backup in databases:
                if db_name not in db_stats:
                    db_stats[db_name] = {'success': 0, 'failed': 0, 'display_name': db_display}
                db_stats[db_name][status] += count
            
            for db_name, stats_info in db_stats.items():
                success = stats_info.get('success', 0)
                failed = stats_info.get('failed', 0)
                total = success + failed
                
                if total > 0:
                    success_rate = (success / total) * 100
                    status_icon = "вњ…" if success_rate >= 80 else "вљ пёЏ" if success_rate >= 50 else "вќЊ"
                    display_name = stats_info.get('display_name', db_name)
                    message += f"{status_icon} {display_name}: {success}/{total} ({success_rate:.1f}%)\n"
            
            message += "\n"

        message += f"рџ•’ РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='backup_databases',
                refresh_button=f'db_backups_{hours}h'
            )
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_database_backups_summary: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґР°РЅРЅС‹С…")

def _esc_md(text: str) -> str:
    """Р­РєСЂР°РЅРёСЂСѓРµС‚ СЃРїРµС†СЃРёРјРІРѕР»С‹ Markdown (parse_mode='Markdown')."""
    if text is None:
        return ""
    s = str(text)
    # РґР»СЏ Markdown v1 РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ СЌРєСЂР°РЅРёСЂРѕРІР°С‚СЊ Р±Р°Р·РѕРІС‹Рµ СЃРёРјРІРѕР»С‹
    return (s.replace("\\", "\\\\")
             .replace("_", "\\_")
             .replace("*", "\\*")
             .replace("[", "\\[")
             .replace("`", "\\`"))

def _get_latest_database_display_name(backup_bot, backup_type, db_name):
    try:
        rows = backup_bot.execute_query(
            """
            SELECT database_display_name
            FROM database_backups
            WHERE backup_type = ? AND database_name = ?
              AND database_display_name IS NOT NULL
              AND TRIM(database_display_name) != ''
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (backup_type, db_name),
        )
        if rows:
            return rows[0][0]
    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ display_name РґР»СЏ {backup_type}/{db_name}: {e}")
    return None


def _get_latest_backup_type(backup_bot, db_name, hours=168):
    try:
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        rows = backup_bot.execute_query(
            """
            SELECT backup_type
            FROM database_backups
            WHERE database_name = ? AND received_at >= ?
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (db_name, since_time),
        )
        if rows:
            return rows[0][0]
    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ backup_type РґР»СЏ {db_name}: {e}")
    return None


def _get_client_suffix(display_name: str | None) -> str | None:
    if not display_name:
        return None
    if "РљРЎ" in display_name.split():
        return "РљРЎ"
    if "Р СѓР±РёРєРѕРЅ" in display_name:
        return "Р СѓР±РёРєРѕРЅ"
    return None


def _get_details_display_name(backup_bot, backup_type, db_name):
    base_name = db_name
    if backup_type == "barnaul":
        return f"{base_name} Р‘Р°СЂРЅР°СѓР»"
    if backup_type == "client":
        display_name = _get_latest_database_display_name(backup_bot, backup_type, db_name)
        client_suffix = _get_client_suffix(display_name)
        if client_suffix:
            return f"{base_name} {client_suffix}"
    return base_name


def format_database_details(backup_bot, backup_type, db_name, hours=168):
    """Р¤РѕСЂРјР°С‚РёСЂСѓРµС‚ РґРµС‚Р°Р»СЊРЅСѓСЋ РёРЅС„РѕСЂРјР°С†РёСЋ РїРѕ Р‘Р”."""
    try:
        requested_type = backup_type
        display_name = _get_details_display_name(backup_bot, requested_type, db_name)

        details = backup_bot.get_database_details(backup_type, db_name, hours)
        if not details:
            fallback_type = _get_latest_backup_type(backup_bot, db_name, hours)
            if fallback_type and fallback_type != backup_type:
                details = backup_bot.get_database_details(fallback_type, db_name, hours)
        if not details:
            return f"рџ“‹ Р”РµС‚Р°Р»Рё РїРѕ {_esc_md(display_name)}\n\nРќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРѕСЃР»РµРґРЅРёРµ {hours} С‡Р°СЃРѕРІ"

        type_display = formatters.get_type_display(requested_type)

        message = f"рџ“‹ *Р”РµС‚Р°Р»Рё РїРѕ {_esc_md(display_name)}*\n"
        message += f"*РўРёРї:* {_esc_md(type_display)}\n"
        message += f"*РџРµСЂРёРѕРґ:* {hours} С‡Р°СЃРѕРІ\n\n"

        # expected tuple: (status, task_type, error_count, subject, received_at)
        success_count = sum(1 for d in details if d and d[0] == 'success')
        failed_count = sum(1 for d in details if d and d[0] == 'failed')
        total_count = len(details)

        message += "рџ“Љ *РЎС‚Р°С‚РёСЃС‚РёРєР°:*\n"
        message += f"вњ… РЈСЃРїРµС€РЅС‹С…: {success_count}\n"
        message += f"вќЊ РћС€РёР±РѕРє: {failed_count}\n"
        message += f"рџ“€ Р’СЃРµРіРѕ: {total_count}\n\n"

        message += "вЏ° *РџРѕСЃР»РµРґРЅРёРµ Р±СЌРєР°РїС‹:*\n"

        task_type_names = {
            'database_dump': 'Р”Р°РјРї Р‘Р”',
            'client_database_dump': 'Р”Р°РјРї РєР»РёРµРЅС‚СЃРєРѕР№ Р‘Р”',
            'cobian_backup': 'Р РµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ',
            'yandex_backup': 'Yandex Backup'
        }

        for status, task_type, error_count, subject, received_at in details[:5]:
            status_icon = "вњ…" if status == 'success' else "вќЊ"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except Exception:
                time_str = (received_at or "")[:16]

            task_display = task_type_names.get(task_type, task_type or 'Р РµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ')

            line = f"{status_icon} *{_esc_md(time_str)}* - {_esc_md(status)} - {_esc_md(task_display)}"
            if error_count and int(error_count) > 0:
                line += f" (РѕС€РёР±РѕРє: {int(error_count)})"
            message += line + "\n"

        message += f"\nрџ•’ *РћР±РЅРѕРІР»РµРЅРѕ:* {datetime.now().strftime('%H:%M:%S')}"
        return message

    except Exception as e:
        logger.exception(f"РћС€РёР±РєР° РІ format_database_details: {e}")
        return f"вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґРµС‚Р°Р»РµР№ Р‘Р”: {e}"
    
def show_database_details(query, backup_bot, backup_type, db_name):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РґРµС‚Р°Р»СЊРЅСѓСЋ РёРЅС„РѕСЂРјР°С†РёСЋ РїРѕ Р‘Р”"""
    try:
        details_text = format_database_details(backup_bot, backup_type, db_name, 168)
        
        query.edit_message_text(
            details_text,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='db_backups_list',
                refresh_button=f'db_detail_{backup_type}__{db_name}'
            )
        )

    except Exception as e:
        logger.error(f"РћС€РёР±РєР° РІ show_database_details: {e}")
        query.edit_message_text("вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё РґРµС‚Р°Р»РµР№ Р‘Р”")
        
