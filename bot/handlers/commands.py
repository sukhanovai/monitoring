"""
/bot/handlers/commands.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Only commands, no inline buttons.
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РўРѕР»СЊРєРѕ РєРѕРјР°РЅРґС‹, РЅРёРєР°РєРёС… inline-РєРЅРѕРїРѕРє
"""

from bot.menu.handlers import show_main_menu
from bot.handlers.base import check_access, deny_access
from lib.common import debug_log
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.monitor_core import (
    manual_check_handler,
    monitor_status,
    silent_command,
    control_command,
    send_morning_report_handler,
)


def start_command(update, context):
    show_main_menu(update, context)


def help_command(update, context):
    if not check_access(update):
        deny_access(update)
        return

    update.message.reply_text(
        "в„№пёЏ РСЃРїРѕР»СЊР·СѓР№С‚Рµ РјРµРЅСЋ РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј",
        parse_mode='Markdown'
    )


def check_command(update, context):
    manual_check_handler(update, context)


def status_command(update, context):
    monitor_status(update, context)


def silent_mode_command(update, context):
    silent_command(update, context)


def control_panel_command(update, context):
    control_command(update, context)


def report_command(update, context):
    send_morning_report_handler(update, context)


def send_alert(message, force=False):
    """РћС‚РїСЂР°РІР»СЏРµС‚ СЃРѕРѕР±С‰РµРЅРёРµ РІ Telegram"""
    try:
        from modules.availability import availability_monitor
        from lib.alerts import is_silent_time

        if force or not is_silent_time():
            from core.monitor_core import bot
            if bot:
                from config.db_settings import CHAT_IDS
                for chat_id in CHAT_IDS:
                    bot.send_message(chat_id=chat_id, text=message)
                debug_log("вњ… РЎРѕРѕР±С‰РµРЅРёРµ РѕС‚РїСЂР°РІР»РµРЅРѕ")
                return True
        else:
            debug_log("вЏёпёЏ РЎРѕРѕР±С‰РµРЅРёРµ РЅРµ РѕС‚РїСЂР°РІР»РµРЅРѕ (С‚РёС…РёР№ СЂРµР¶РёРј)")

        return False
    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё СЃРѕРѕР±С‰РµРЅРёСЏ: {e}")
        return False


def handle_check_single_server(update, context, server_ip):
    """РћР±СЂР°Р±РѕС‚РєР° РїСЂРѕРІРµСЂРєРё РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    try:
        from extensions.server_checks import get_server_by_ip, check_server_availability

        server = get_server_by_ip(server_ip)
        if not server:
            return "вќЊ РЎРµСЂРІРµСЂ РЅРµ РЅР°Р№РґРµРЅ"

        is_up = check_server_availability(server)

        if is_up:
            return f"вњ… РЎРµСЂРІРµСЂ {server['name']} ({server_ip}) РґРѕСЃС‚СѓРїРµРЅ"
        return f"рџ”ґ РЎРµСЂРІРµСЂ {server['name']} ({server_ip}) РЅРµРґРѕСЃС‚СѓРїРµРЅ"

    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂР° {server_ip}: {e}")
        return f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё: {str(e)[:100]}"


def handle_check_server_resources(update, context, server_ip):
    """РћР±СЂР°Р±РѕС‚РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ РѕРґРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('resource_monitor'):
            return "рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ"

        from modules.resources import resource_monitor

        resources = resource_monitor.check_single_server(server_ip)

        if not resources:
            return "вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕР»СѓС‡РёС‚СЊ СЂРµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР°"

        from extensions.server_checks import get_server_by_ip
        server = get_server_by_ip(server_ip)

        message = f"рџ“Љ **Р РµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР° {server['name']} ({server_ip})**\n\n"
        message += f"вЂў CPU: {resources.get('cpu', 0)}%\n"
        message += f"вЂў RAM: {resources.get('ram', 0)}%\n"
        message += f"вЂў Disk: {resources.get('disk', 0)}%\n"
        message += f"вЂў РњРµС‚РѕРґ РґРѕСЃС‚СѓРїР°: {resources.get('access_method', 'РЅРµРёР·РІРµСЃС‚РЅРѕ')}\n"
        message += f"вЂў Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё: {resources.get('timestamp', 'N/A')}\n"

        from config.db_settings import RESOURCE_THRESHOLDS
        alerts = []

        cpu = resources.get('cpu', 0)
        ram = resources.get('ram', 0)
        disk = resources.get('disk', 0)

        if cpu >= RESOURCE_THRESHOLDS["cpu_critical"]:
            alerts.append(f"рџљЁ CPU: {cpu}% (РєСЂРёС‚РёС‡РЅРѕ)")
        elif cpu >= RESOURCE_THRESHOLDS["cpu_warning"]:
            alerts.append(f"вљ пёЏ CPU: {cpu}% (РІС‹СЃРѕРєР°СЏ РЅР°РіСЂСѓР·РєР°)")

        if ram >= RESOURCE_THRESHOLDS["ram_critical"]:
            alerts.append(f"рџљЁ RAM: {ram}% (РєСЂРёС‚РёС‡РЅРѕ)")
        elif ram >= RESOURCE_THRESHOLDS["ram_warning"]:
            alerts.append(f"вљ пёЏ RAM: {ram}% (РјР°Р»Рѕ СЃРІРѕР±РѕРґРЅРѕР№ РїР°РјСЏС‚Рё)")

        if disk >= RESOURCE_THRESHOLDS["disk_critical"]:
            alerts.append(f"рџљЁ Disk: {disk}% (РєСЂРёС‚РёС‡РЅРѕ)")
        elif disk >= RESOURCE_THRESHOLDS["disk_warning"]:
            alerts.append(f"вљ пёЏ Disk: {disk}% (РјР°Р»Рѕ РјРµСЃС‚Р°)")

        if alerts:
            message += "\n**вљ пёЏ РџСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ:**\n"
            for alert in alerts:
                message += f"вЂў {alert}\n"

        return message

    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂР° {server_ip}: {e}")
        return f"вќЊ РћС€РёР±РєР°: {str(e)[:100]}"


def create_server_selection_keyboard(server_type=None, action="check_single"):
    """РЎРѕР·РґР°РµС‚ РєР»Р°РІРёР°С‚СѓСЂСѓ РґР»СЏ РІС‹Р±РѕСЂР° СЃРµСЂРІРµСЂР°"""
    try:
        from extensions.server_checks import initialize_servers

        servers = initialize_servers()

        if server_type:
            servers = [s for s in servers if s["type"] == server_type]

        keyboard = []
        current_row = []

        for i, server in enumerate(servers):
            button_text = f"{server['name'][:15]}"
            callback_data = f"{action}_{server['ip']}"

            current_row.append(
                InlineKeyboardButton(button_text, callback_data=callback_data)
            )

            if len(current_row) == 2 or i == len(servers) - 1:
                keyboard.append(current_row)
                current_row = []

        keyboard.append([
            InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')
        ])

        return InlineKeyboardMarkup(keyboard)

    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ РєР»Р°РІРёР°С‚СѓСЂС‹ РІС‹Р±РѕСЂР° СЃРµСЂРІРµСЂР°: {e}")
        return InlineKeyboardMarkup([[]])
