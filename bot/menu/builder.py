"""
/bot/menu/builder.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
The place where keyboards are made.
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРµСЃС‚Рѕ, РіРґРµ СЃС‚СЂРѕСЏС‚СЃСЏ РєР»Р°РІРёР°С‚СѓСЂС‹
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(extension_manager):
    keyboard = [
        [InlineKeyboardButton("рџЊ… РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚", callback_data='daily_report')],
        [InlineKeyboardButton("рџ”„ Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ", callback_data='manual_check')],
        [InlineKeyboardButton("рџ”Ќ Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРµСЂР°", callback_data='show_availability_menu')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("рџ“Љ Р РµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР°", callback_data='check_resources')])

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append(
            [InlineKeyboardButton("рџ’ѕ Р‘СЌРєР°РїС‹ Proxmox", callback_data='backup_hosts')]
        )

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append(
            [InlineKeyboardButton("рџ—ѓпёЏ Р‘СЌРєР°РїС‹ Р‘Р”", callback_data='backup_databases')]
        )

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append(
            [InlineKeyboardButton("рџ“¬ Р‘СЌРєР°РїС‹ РїРѕС‡С‚С‹", callback_data='backup_mail')]
        )

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append(
            [InlineKeyboardButton("рџ“¦ РћСЃС‚Р°С‚РєРё 1РЎ", callback_data='backup_stock_loads')]
        )

    if extension_manager.is_extension_enabled('supplier_stock_files'):
        keyboard.append(
            [InlineKeyboardButton("рџ“¦ Р РµР·СѓР»СЊС‚Р°С‚С‹ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ", callback_data='supplier_stock_reports')]
        )

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append(
            [InlineKeyboardButton("рџ§Љ ZFS", callback_data='zfs_menu')]
        )

    keyboard.extend([
        [InlineKeyboardButton("рџ› пёЏ Р Р°СЃС€РёСЂРµРЅРёСЏ", callback_data='extensions_menu')],
        [InlineKeyboardButton("рџЋ›пёЏ РЈРїСЂР°РІР»РµРЅРёРµ", callback_data='control_panel')],
        [InlineKeyboardButton("вљ™пёЏ РќР°СЃС‚СЂРѕР№РєРё", callback_data='settings_main')],
        [InlineKeyboardButton("в„№пёЏ Рћ Р±РѕС‚Рµ", callback_data='about_bot')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')],
    ])

    return InlineKeyboardMarkup(keyboard)
