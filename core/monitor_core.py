"""
/core/monitor_core.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core system
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РЇРґСЂРѕ СЃРёСЃС‚РµРјС‹
"""

# РќРѕРІС‹Рµ РёРјРїРѕСЂС‚С‹ РёР· РјРѕРґСѓР»СЊРЅРѕР№ СЃС‚СЂСѓРєС‚СѓСЂС‹
from lib.logging import debug_log
from lib.alerts import (
    send_alert as base_send_alert,
    configure_alerts,
    init_telegram_bot,
    set_silent_override,
    is_silent_time as alerts_is_silent_time,
    get_silent_override,
)
from lib.utils import progress_bar, format_duration
from config.db_settings import DEBUG_MODE, DATA_DIR
from core.monitor import monitor
from modules.availability import availability_checker
from modules.resources import resources_checker
from modules.morning_report import morning_report
from modules.targeted_checks import targeted_checks

# РЎС‚Р°СЂС‹Рµ РёРјРїРѕСЂС‚С‹ РґР»СЏ СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё
import os
import threading
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lib.utils import safe_import
from extensions.server_checks import check_server_availability
from core.config_manager import config_manager

# Р“Р»РѕР±Р°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ
bot = None
server_status = {}
morning_data = {}
monitoring_active = True
last_check_time = datetime.now()
servers = []
resource_history = {}
last_resource_check = datetime.now()
resource_alerts_sent = {}
last_report_date = None

_alerts_configured = False

def is_server_monitoring_enabled(ip: str) -> bool:
    """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅ Р»Рё РјРѕРЅРёС‚РѕСЂРёРЅРі РґР»СЏ СЃРµСЂРІРµСЂР°."""
    try:
        return config_manager.get_server_enabled(ip)
    except Exception as e:
        debug_log(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕР»СѓС‡РёС‚СЊ СЃС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂР° {ip}: {e}")
        return True

def refresh_servers():
    """РћР±РЅРѕРІР»СЏРµС‚ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ Рё РёС… СЃС‚Р°С‚СѓСЃС‹."""
    global servers, server_status

    try:
        updated_servers = config_manager.get_all_servers(include_disabled=True)
        if not updated_servers:
            from extensions.server_checks import initialize_servers
            updated_servers = initialize_servers()
            for server in updated_servers:
                server.setdefault("enabled", True)

        servers = updated_servers
        current_ips = {server.get("ip") for server in servers if server.get("ip")}

        for ip in list(server_status.keys()):
            if ip not in current_ips:
                server_status.pop(ip, None)

        for server in servers:
            ip = server.get("ip")
            if not ip:
                continue
            if ip not in server_status:
                server_status[ip] = {
                    "last_up": datetime.now(),
                    "alert_sent": False,
                    "name": server.get("name", ip),
                    "type": server.get("type"),
                    "resources": None,
                    "last_alert": {},
                    "monitoring_enabled": server.get("enabled", True)
                }

    except Exception as e:
        debug_log(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ: {e}")

def ensure_alerts_config():
    """Р“Р°СЂР°РЅС‚РёСЂСѓРµС‚ РїСЂРёРјРµРЅРµРЅРёРµ РЅР°СЃС‚СЂРѕРµРє Р°Р»РµСЂС‚РѕРІ РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё."""
    global _alerts_configured
    if _alerts_configured:
        return

    config = get_config()
    configure_alerts(
        silent_start=getattr(config, "SILENT_START", None),
        silent_end=getattr(config, "SILENT_END", None),
    )
    _alerts_configured = True

def ensure_alert_bot():
    """РРЅРёС†РёР°Р»РёР·РёСЂСѓРµС‚ Telegram-Р±РѕС‚ РґР»СЏ lib.alerts РїСЂРё РЅР°Р»РёС‡РёРё РіР»РѕР±Р°Р»СЊРЅРѕРіРѕ Р±РѕС‚Р°."""
    if bot is None:
        return
    try:
        config = get_config()
        init_telegram_bot(bot, config.CHAT_IDS)
    except Exception as e:
        debug_log(f"РќРµ СѓРґР°Р»РѕСЃСЊ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ Р±РѕС‚ Р°Р»РµСЂС‚РѕРІ: {e}")

def send_alert(message, force=False):
    """РћР±РµСЂС‚РєР° РЅР°Рґ lib.alerts.send_alert СЃ РїСЂРёРјРµРЅРµРЅРёРµРј РЅР°СЃС‚СЂРѕРµРє Рё РёРЅРёС†РёР°Р»РёР·Р°С†РёРµР№ Р±РѕС‚Р°."""
    ensure_alerts_config()
    ensure_alert_bot()
    return base_send_alert(message, force=force)

def is_silent_time():
    """РСЃРїРѕР»СЊР·СѓРµС‚ РµРґРёРЅС‹Р№ РјРµС…Р°РЅРёР·Рј С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° РёР· lib.alerts."""
    ensure_alerts_config()
    return alerts_is_silent_time()

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
get_check_interval = lazy_import('config.db_settings', 'CHECK_INTERVAL')
get_silent_times = lazy_import('config.db_settings', 'SILENT_START')
get_data_collection_time = lazy_import('config.db_settings', 'DATA_COLLECTION_TIME')
get_max_fail_time = lazy_import('config.db_settings', 'MAX_FAIL_TIME')
get_resource_config = lazy_import('config.db_settings', 'RESOURCE_CHECK_INTERVAL')

def get_web_interface_url(config):
    """Р¤РѕСЂРјРёСЂСѓРµС‚ URL РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР° РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё."""
    monitor_ip = getattr(config, "MONITOR_SERVER_IP", "") or ""
    if not monitor_ip:
        web_host = getattr(config, "WEB_HOST", "")
        if web_host in ("0.0.0.0", "", None):
            monitor_ip = "localhost"
        else:
            monitor_ip = web_host
    return f"http://{monitor_ip}:{config.WEB_PORT}"

def perform_manual_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ СЃРµСЂРІРµСЂРѕРІ СЃ РѕР±РЅРѕРІР»РµРЅРёРµРј РїСЂРѕРіСЂРµСЃСЃР°"""
    global last_check_time

    # Р›РµРЅРёРІР°СЏ Р·Р°РіСЂСѓР·РєР° СЃРµСЂРІРµСЂРѕРІ
    global servers
    if not servers:
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()

    total_servers = len(servers)
    results = {"failed": [], "ok": []}

    for i, server in enumerate(servers):
        try:
            progress = (i + 1) / total_servers * 100
            progress_text = f"рџ”Ќ РџСЂРѕРІРµСЂСЏСЋ СЃРµСЂРІРµСЂС‹...\n{progress_bar(progress)}\n\nвЏі РџСЂРѕРІРµСЂСЏСЋ {server['name']} ({server['ip']})..."

            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=progress_text
            )

            # РСЃРїРѕР»СЊР·СѓРµРј СѓРЅРёРІРµСЂСЃР°Р»СЊРЅСѓСЋ РїСЂРѕРІРµСЂРєСѓ
            is_up = check_server_availability(server)

            if is_up:
                results["ok"].append(server)
                debug_log(f"вњ… {server['name']} ({server['ip']}) - РґРѕСЃС‚СѓРїРµРЅ")
            else:
                results["failed"].append(server)
                debug_log(f"вќЊ {server['name']} ({server['ip']}) - РЅРµРґРѕСЃС‚СѓРїРµРЅ")

            time.sleep(1)

        except Exception as e:
            debug_log(f"рџ’Ґ РљСЂРёС‚РёС‡РµСЃРєР°СЏ РѕС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ {server['ip']}: {e}")
            results["failed"].append(server)

    last_check_time = datetime.now()
    send_check_results(context, chat_id, progress_message_id, results)

def send_check_results(context, chat_id, progress_message_id, results):
    """РћС‚РїСЂР°РІР»СЏРµС‚ СЂРµР·СѓР»СЊС‚Р°С‚С‹ РїСЂРѕРІРµСЂРєРё"""
    if not results["failed"]:
        message = "вњ… Р’СЃРµ СЃРµСЂРІРµСЂС‹ РґРѕСЃС‚СѓРїРЅС‹!"
    else:
        message = "вљ пёЏ РџСЂРѕР±Р»РµРјРЅС‹Рµ СЃРµСЂРІРµСЂС‹:\n"

        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїСѓ РґР»СЏ СѓРґРѕР±СЃС‚РІР° С‡С‚РµРЅРёСЏ
        by_type = {}
        for server in results["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n{server_type.upper()} СЃРµСЂРІРµСЂС‹:\n"
            for s in servers_list:
                message += f"- {s['name']} ({s['ip']})\n"

    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text=f"рџ”Ќ РџСЂРѕРІРµСЂРєР° Р·Р°РІРµСЂС€РµРЅР°!\n\n{message}\n\nвЏ° Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё: {last_check_time.strftime('%H:%M:%S')}"
    )

def manual_check_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє СЂСѓС‡РЅРѕР№ РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџ”Ќ РќР°С‡РёРЅР°СЋ РїСЂРѕРІРµСЂРєСѓ СЃРµСЂРІРµСЂРѕРІ...\n" + progress_bar(0)
    )

    thread = threading.Thread(
        target=perform_manual_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def get_current_server_status():
    """Р’С‹РїРѕР»РЅСЏРµС‚ Р±С‹СЃС‚СЂСѓСЋ РїСЂРѕРІРµСЂРєСѓ СЃС‚Р°С‚СѓСЃР° СЃРµСЂРІРµСЂРѕРІ"""
    global servers

    # РџРµСЂРµРёРЅРёС†РёР°Р»РёР·РёСЂСѓРµРј СЃРµСЂРІРµСЂС‹ РїСЂРё РєР°Р¶РґРѕРј Р·Р°РїСЂРѕСЃРµ
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()
    debug_log(f"рџ”„ РћР±РЅРѕРІР»РµРЅ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ: {len(servers)} СЃРµСЂРІРµСЂРѕРІ")

    results = {"failed": [], "ok": []}

    for server in servers:
        try:
            is_up = check_server_availability(server)

            if is_up:
                results["ok"].append(server)
            else:
                results["failed"].append(server)

            debug_log(f"рџ”Ќ {server['name']} ({server['ip']}) - {'рџџў' if is_up else 'рџ”ґ'}")

        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё {server['name']}: {e}")
            results["failed"].append(server)

    debug_log(f"рџ“Љ РС‚РѕРі РїСЂРѕРІРµСЂРєРё: {len(results['ok'])} РґРѕСЃС‚СѓРїРЅРѕ, {len(results['failed'])} РЅРµРґРѕСЃС‚СѓРїРЅРѕ")
    return results

def monitor_status(update, context):
    """РџРѕРєР°Р·С‹РІР°РµС‚ СЃС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        # Р•СЃР»Рё РІС‹Р·РІР°РЅРѕ РєР°Рє РєРѕРјР°РЅРґР°, Р° РЅРµ callback
        chat_id = update.message.chat_id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return

    try:
        current_status = get_current_server_status()
        up_count = len(current_status["ok"])
        down_count = len(current_status["failed"])

        status = "рџџў РђРєС‚РёРІРµРЅ" if monitoring_active else "рџ”ґ РћСЃС‚Р°РЅРѕРІР»РµРЅ"

        # РћРїСЂРµРґРµР»СЏРµРј СЃС‚Р°С‚СѓСЃ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°
        silent_status_text = "рџ”‡ РўРёС…РёР№ СЂРµР¶РёРј" if is_silent_time() else "рџ”Љ РћР±С‹С‡РЅС‹Р№ СЂРµР¶РёРј"
        silent_override = get_silent_override()
        if silent_override is not None:
            if silent_override:
                silent_status_text += " (рџ”‡ РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ)"
            else:
                silent_status_text += " (рџ”Љ РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ)"

        config = get_config()
        next_check = datetime.now() + timedelta(seconds=config.CHECK_INTERVAL)

        message = (
            f"рџ“Љ *РЎС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°*\n\n"
            f"**РЎРѕСЃС‚РѕСЏРЅРёРµ:** {status}\n"
            f"**Р РµР¶РёРј:** {silent_status_text}\n\n"
            f"вЏ° РџРѕСЃР»РµРґРЅСЏСЏ РїСЂРѕРІРµСЂРєР°: {last_check_time.strftime('%H:%M:%S')}\n"
            f"вЏі РЎР»РµРґСѓСЋС‰Р°СЏ РїСЂРѕРІРµСЂРєР°: {next_check.strftime('%H:%M:%S')}\n"
            f"рџ”ў Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ: {len(servers)}\n"
            f"рџџў Р”РѕСЃС‚СѓРїРЅРѕ: {up_count}\n"
            f"рџ”ґ РќРµРґРѕСЃС‚СѓРїРЅРѕ: {down_count}\n"
            f"рџ”„ РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё: {config.CHECK_INTERVAL} СЃРµРє\n\n"
        )

        # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃРµ
        from extensions.extension_manager import extension_manager
        if extension_manager.is_extension_enabled('web_interface'):
            message += f"рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* {get_web_interface_url(config)}\n"
            message += "_*РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ РІ Р»РѕРєР°Р»СЊРЅРѕР№ СЃРµС‚Рё_\n"
        else:
            message += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* рџ”ґ РѕС‚РєР»СЋС‡РµРЅ\n"

        if down_count > 0:
            message += f"\nвљ пёЏ *РџСЂРѕР±Р»РµРјРЅС‹Рµ СЃРµСЂРІРµСЂС‹ ({down_count}):*\n"

            # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїСѓ РґР»СЏ СѓРґРѕР±СЃС‚РІР° С‡С‚РµРЅРёСЏ
            by_type = {}
            for server in current_status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)

            for server_type, servers_list in by_type.items():
                message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                for i, s in enumerate(servers_list[:8]):  # РћРіСЂР°РЅРёС‡РёРІР°РµРј РїРѕРєР°Р·
                    message += f"вЂў {s['name']} ({s['ip']})\n"

                if len(servers_list) > 8:
                    message += f"вЂў ... Рё РµС‰Рµ {len(servers_list) - 8} СЃРµСЂРІРµСЂРѕРІ\n"

        # РћС‚РїСЂР°РІР»СЏРµРј СЃРѕРѕР±С‰РµРЅРёРµ РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ С‚РёРїР° РІС‹Р·РѕРІР°
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ СЃС‚Р°С‚СѓСЃ", callback_data='monitor_status')],
                    [InlineKeyboardButton("рџ”Ќ РџСЂРѕРІРµСЂРёС‚СЊ СЃРµР№С‡Р°СЃ", callback_data='manual_check')],
                    [InlineKeyboardButton("рџ”‡ РЈРїСЂР°РІР»РµРЅРёРµ СЂРµР¶РёРјРѕРј", callback_data='silent_status')],
                    [InlineKeyboardButton("рџ“‹ РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ", callback_data='servers_list')],
                    [InlineKeyboardButton("рџЋ›пёЏ РЈРїСЂР°РІР»РµРЅРёРµ", callback_data='control_panel')],
                    [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')],
                    [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
                ])
            )
        else:
            update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        debug_log(f"РћС€РёР±РєР° РІ monitor_status: {e}")
        error_msg = "вљ пёЏ РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР° РїСЂРё РїРѕР»СѓС‡РµРЅРёРё СЃС‚Р°С‚СѓСЃР°"
        if query:
            query.edit_message_text(error_msg)
        else:
            update.message.reply_text(error_msg)

def silent_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /silent"""
    config = get_config()
    silent_status = "рџџў Р°РєС‚РёРІРµРЅ" if is_silent_time() else "рџ”ґ РЅРµР°РєС‚РёРІРµРЅ"
    message = (
        f"рџ”‡ *РЎС‚Р°С‚СѓСЃ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°:* {silent_status}\n\n"
        f"вЏ° *Р’СЂРµРјСЏ СЂР°Р±РѕС‚С‹:* {config.SILENT_START}:00 - {config.SILENT_END}:00\n\n"
        f"рџ’Ў *Р’ С‚РёС…РѕРј СЂРµР¶РёРјРµ:*\n"
        f"вЂў Р РµРіСѓР»СЏСЂРЅС‹Рµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РЅРµ РѕС‚РїСЂР°РІР»СЏСЋС‚СЃСЏ\n"
        f"вЂў РљСЂРёС‚РёС‡РµСЃРєРёРµ РѕС€РёР±РєРё РІСЃРµ СЂР°РІРЅРѕ РѕС‚РїСЂР°РІР»СЏСЋС‚СЃСЏ\n"
        f"вЂў Р СѓС‡РЅС‹Рµ РїСЂРѕРІРµСЂРєРё СЂР°Р±РѕС‚Р°СЋС‚ РЅРѕСЂРјР°Р»СЊРЅРѕ\n"
        f"вЂў РЈС‚СЂРµРЅРЅРёРµ РѕС‚С‡РµС‚С‹ РѕС‚РїСЂР°РІР»СЏСЋС‚СЃСЏ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ"
    )

    update.message.reply_text(message, parse_mode='Markdown')

def silent_status_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРЅРѕРїРєРё СЃС‚Р°С‚СѓСЃР° С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°"""
    query = update.callback_query
    query.answer()

    # РћРїСЂРµРґРµР»СЏРµРј С‚РµРєСѓС‰РёР№ СЂРµР¶РёРј
    silent_override = get_silent_override()
    if silent_override is None:
        mode_text = "рџ”„ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№"
        mode_desc = "Р Р°Р±РѕС‚Р°РµС‚ РїРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ"
    elif silent_override:
        mode_text = "рџ”‡ РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ С‚РёС…РёР№"
        mode_desc = "Р’СЃРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РѕС‚РєР»СЋС‡РµРЅС‹"
    else:
        mode_text = "рџ”Љ РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РіСЂРѕРјРєРёР№"
        mode_desc = "Р’СЃРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РІРєР»СЋС‡РµРЅС‹"

    # РџСЂР°РІРёР»СЊРЅРѕ РѕРїСЂРµРґРµР»СЏРµРј СЃС‚Р°С‚СѓСЃ - РёРЅРІРµСЂС‚РёСЂСѓРµРј РґР»СЏ РїРѕРЅСЏС‚РЅРѕСЃС‚Рё РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ
    current_status = "рџ”ґ РЅРµР°РєС‚РёРІРµРЅ" if is_silent_time() else "рџџў Р°РєС‚РёРІРµРЅ"
    status_description = "С‚РёС…РёР№ СЂРµР¶РёРј" if is_silent_time() else "РіСЂРѕРјРєРёР№ СЂРµР¶РёРј"
    config = get_config()
    message = (
        f"рџ”‡ *РЈРїСЂР°РІР»РµРЅРёРµ С‚РёС…РёРј СЂРµР¶РёРјРѕРј*\n\n"
        f"**РўРµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ:** {current_status}\n"
        f"**Р РµР¶РёРј СЂР°Р±РѕС‚С‹:** {mode_text}\n"
        f"*{mode_desc}*\n"
        f"**Р¤Р°РєС‚РёС‡РµСЃРєРё:** {status_description}\n\n"
        f"вЏ° *Р Р°СЃРїРёСЃР°РЅРёРµ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°:* {config.SILENT_START}:00 - {config.SILENT_END}:00\n\n"
        f"рџ’Ў *РџРѕСЏСЃРЅРµРЅРёРµ:*\n"
        f"- рџџў Р°РєС‚РёРІРµРЅ = СѓРІРµРґРѕРјР»РµРЅРёСЏ СЂР°Р±РѕС‚Р°СЋС‚\n"
        f"- рџ”ґ РЅРµР°РєС‚РёРІРµРЅ = СѓРІРµРґРѕРјР»РµРЅРёСЏ РѕС‚РєР»СЋС‡РµРЅС‹\n"
        f"- рџ”Љ РіСЂРѕРјРєРёР№ СЂРµР¶РёРј = РІСЃРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РІРєР»СЋС‡РµРЅС‹\n"
        f"- рџ”‡ С‚РёС…РёР№ СЂРµР¶РёРј = С‚РѕР»СЊРєРѕ РєСЂРёС‚РёС‡РµСЃРєРёРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ"
    )

    keyboard = [
        [InlineKeyboardButton("рџ”‡ Р’РєР»СЋС‡РёС‚СЊ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ С‚РёС…РёР№", callback_data='force_silent')],
        [InlineKeyboardButton("рџ”Љ Р’РєР»СЋС‡РёС‚СЊ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РіСЂРѕРјРєРёР№", callback_data='force_loud')],
        [InlineKeyboardButton("рџ”„ Р’РµСЂРЅСѓС‚СЊ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЂРµР¶РёРј", callback_data='auto_mode')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ РІ СѓРїСЂР°РІР»РµРЅРёРµ", callback_data='control_panel')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def force_silent_handler(update, context):
    """Р’РєР»СЋС‡Р°РµС‚ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅС‹Р№ С‚РёС…РёР№ СЂРµР¶РёРј"""
    set_silent_override(True)
    query = update.callback_query
    query.answer()

    send_alert("рџ”‡ *РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅС‹Р№ С‚РёС…РёР№ СЂРµР¶РёРј РІРєР»СЋС‡РµРЅ*\nР’СЃРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РѕС‚РєР»СЋС‡РµРЅС‹ РґРѕ СЃРјРµРЅС‹ СЂРµР¶РёРјР°.", force=True)

    # Р’РѕР·РІСЂР°С‰Р°РµРјСЃСЏ РІ СѓРїСЂР°РІР»РµРЅРёРµ С‚РёС…РёРј СЂРµР¶РёРјРѕРј
    silent_status_handler(update, context)

def force_loud_handler(update, context):
    """Р’РєР»СЋС‡Р°РµС‚ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅС‹Р№ РіСЂРѕРјРєРёР№ СЂРµР¶РёРј"""
    set_silent_override(False)
    query = update.callback_query
    query.answer()

    send_alert("рџ”Љ *РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅС‹Р№ РіСЂРѕРјРєРёР№ СЂРµР¶РёРј РІРєР»СЋС‡РµРЅ*\nР’СЃРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ Р°РєС‚РёРІРЅС‹ РґРѕ СЃРјРµРЅС‹ СЂРµР¶РёРјР°.", force=True)

    # Р’РѕР·РІСЂР°С‰Р°РµРјСЃСЏ РІ СѓРїСЂР°РІР»РµРЅРёРµ С‚РёС…РёРј СЂРµР¶РёРјРѕРј
    silent_status_handler(update, context)

def auto_mode_handler(update, context):
    """Р’РєР»СЋС‡Р°РµС‚ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЂРµР¶РёРј"""
    set_silent_override(None)
    query = update.callback_query
    query.answer()

    current_status = "Р°РєС‚РёРІРµРЅ" if is_silent_time() else "РЅРµР°РєС‚РёРІРµРЅ"
    send_alert(f"рџ”„ *РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЂРµР¶РёРј РІРєР»СЋС‡РµРЅ*\nРўРёС…РёР№ СЂРµР¶РёРј СЃРµР№С‡Р°СЃ {current_status}.", force=True)

    # Р’РѕР·РІСЂР°С‰Р°РµРјСЃСЏ РІ СѓРїСЂР°РІР»РµРЅРёРµ С‚РёС…РёРј СЂРµР¶РёРјРѕРј
    silent_status_handler(update, context)

def control_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /control"""
    keyboard = [
        [InlineKeyboardButton("вЏёпёЏ РџСЂРёРѕСЃС‚Р°РЅРѕРІРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі", callback_data='pause_monitoring')],
        [InlineKeyboardButton("в–¶пёЏ Р’РѕР·РѕР±РЅРѕРІРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі", callback_data='resume_monitoring')],
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='monitor_status')]
    ]

    status_text = "рџџў РњРѕРЅРёС‚РѕСЂРёРЅРі Р°РєС‚РёРІРµРЅ" if monitoring_active else "рџ”ґ РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"

    update.message.reply_text(
        f"рџЋ›пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def control_panel_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРЅРѕРїРєРё РїР°РЅРµР»Рё СѓРїСЂР°РІР»РµРЅРёСЏ"""
    query = update.callback_query
    query.answer()

    # РЎРѕР·РґР°РµРј РєРЅРѕРїРєСѓ СѓРїСЂР°РІР»РµРЅРёСЏ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј (РѕР±СЉРµРґРёРЅРµРЅРЅР°СЏ 7.1 Рё 7.2)
    monitoring_button = InlineKeyboardButton(
        "вЏёпёЏ РџСЂРёРѕСЃС‚Р°РЅРѕРІРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі" if monitoring_active else "в–¶пёЏ Р’РѕР·РѕР±РЅРѕРІРёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРі",
        callback_data='toggle_monitoring'
    )

    keyboard = [
        [monitoring_button],
        [InlineKeyboardButton("рџ”‡ РЈРїСЂР°РІР»РµРЅРёРµ С‚РёС…РёРј СЂРµР¶РёРјРѕРј", callback_data='silent_status')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    status_text = "рџџў РњРѕРЅРёС‚РѕСЂРёРЅРі Р°РєС‚РёРІРµРЅ" if monitoring_active else "рџ”ґ РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"

    query.edit_message_text(
        f"рџЋ›пёЏ *РЈРїСЂР°РІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіР°*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def toggle_monitoring_handler(update, context):
    """РџРµСЂРµРєР»СЋС‡Р°РµС‚ СЃРѕСЃС‚РѕСЏРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    global monitoring_active
    monitoring_active = not monitoring_active
    query = update.callback_query
    query.answer()

    status_text = "в–¶пёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РІРѕР·РѕР±РЅРѕРІР»РµРЅ" if monitoring_active else "вЏёпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"

    # РћС‚РїСЂР°РІР»СЏРµРј СѓРІРµРґРѕРјР»РµРЅРёРµ Рѕ РёР·РјРµРЅРµРЅРёРё СЃС‚Р°С‚СѓСЃР°
    if monitoring_active:
        send_alert("рџџў *РњРѕРЅРёС‚РѕСЂРёРЅРі РІРѕР·РѕР±РЅРѕРІР»РµРЅ*\nР РµРіСѓР»СЏСЂРЅС‹Рµ РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ Р°РєС‚РёРІРёСЂРѕРІР°РЅС‹.", force=True)
    else:
        send_alert("рџ”ґ *РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ*\nР РµРіСѓР»СЏСЂРЅС‹Рµ РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ РѕС‚РєР»СЋС‡РµРЅС‹.", force=True)

    # Р’РѕР·РІСЂР°С‰Р°РµРјСЃСЏ РІ РїР°РЅРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ
    control_panel_handler(update, context)

def pause_monitoring_handler(update, context):
    """РџСЂРёРѕСЃС‚Р°РЅРѕРІРєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    global monitoring_active
    monitoring_active = False
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "вЏёпёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ\n\nРЈРІРµРґРѕРјР»РµРЅРёСЏ РѕС‚РїСЂР°РІР»СЏС‚СЊСЃСЏ РЅРµ Р±СѓРґСѓС‚.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("в–¶пёЏ Р’РѕР·РѕР±РЅРѕРІРёС‚СЊ", callback_data='resume_monitoring')],
            [InlineKeyboardButton("рџЋ›пёЏ РџР°РЅРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ", callback_data='control_panel')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')]
        ])
    )

def resume_monitoring_handler(update, context):
    """Р’РѕР·РѕР±РЅРѕРІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    global monitoring_active
    monitoring_active = True
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "в–¶пёЏ РњРѕРЅРёС‚РѕСЂРёРЅРі РІРѕР·РѕР±РЅРѕРІР»РµРЅ",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("рџЋ›пёЏ РџР°РЅРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ", callback_data='control_panel')],
            [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu')]
        ])
    )

def _resource_monitor_enabled() -> bool:
    """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅ Р»Рё РјРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ"""
    try:
        from extensions.extension_manager import extension_manager
        return extension_manager.is_extension_enabled('resource_monitor')
    except ImportError:
        return True

def check_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ - РЅРѕРІРѕРµ РјРµРЅСЋ СЃ СЂР°Р·РґРµР»РµРЅРёРµРј РїРѕ СЂРµСЃСѓСЂСЃР°Рј"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    # РњРµРЅСЋ СЃ СЂР°Р·РґРµР»РµРЅРёРµРј РїРѕ СЂРµСЃСѓСЂСЃР°Рј
    keyboard = [
        [InlineKeyboardButton("рџ’» РџСЂРѕРІРµСЂРёС‚СЊ CPU", callback_data='check_cpu')],
        [InlineKeyboardButton("рџ§  РџСЂРѕРІРµСЂРёС‚СЊ RAM", callback_data='check_ram')],
        [InlineKeyboardButton("рџ’ѕ РџСЂРѕРІРµСЂРёС‚СЊ Disk", callback_data='check_disk')],
        [InlineKeyboardButton("рџђ§ Linux СЃРµСЂРІРµСЂС‹", callback_data='check_linux')],
        [InlineKeyboardButton("рџЄџ Windows СЃРµСЂРІРµСЂС‹", callback_data='check_windows')],
        [InlineKeyboardButton("рџ“Ў Р”СЂСѓРіРёРµ СЃРµСЂРІРµСЂС‹", callback_data='check_other')],
        [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
         InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]

    if query:
        query.edit_message_text(
            text="рџ”Ќ *Р’С‹Р±РµСЂРёС‚Рµ С‡С‚Рѕ РїСЂРѕРІРµСЂРёС‚СЊ:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text="рџ”Ќ *Р’С‹Р±РµСЂРёС‚Рµ С‡С‚Рѕ РїСЂРѕРІРµСЂРёС‚СЊ:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def check_cpu_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё С‚РѕР»СЊРєРѕ CPU"""
    query = update.callback_query
    if query:
        query.answer("рџ’» РџСЂРѕРІРµСЂСЏРµРј CPU...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџ’» *РџСЂРѕРІРµСЂРєР° Р·Р°РіСЂСѓР·РєРё CPU...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_cpu_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def check_ram_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё С‚РѕР»СЊРєРѕ RAM"""
    query = update.callback_query
    if query:
        query.answer("рџ§  РџСЂРѕРІРµСЂСЏРµРј RAM...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџ§  *РџСЂРѕРІРµСЂРєР° РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ RAM...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_ram_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def check_disk_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё С‚РѕР»СЊРєРѕ Disk"""
    query = update.callback_query
    if query:
        query.answer("рџ’ѕ РџСЂРѕРІРµСЂСЏРµРј Disk...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџ’ѕ *РџСЂРѕРІРµСЂРєР° РґРёСЃРєРѕРІРѕРіРѕ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІР°...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_disk_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_cpu_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ С‚РѕР»СЊРєРѕ CPU СЃ РґРµС‚Р°Р»СЊРЅС‹Рј РїСЂРѕРіСЂРµСЃСЃРѕРј"""

    def update_progress(progress, status):
        progress_text = f"рџ’» РџСЂРѕРІРµСЂРєР° CPU...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "вЏі РџРѕР»СѓС‡Р°РµРј СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ...")

        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ СЃРµСЂРІРµСЂС‹ РґР»СЏ РїСЂРѕРІРµСЂРєРё
        from extensions.server_checks import initialize_servers
        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        cpu_results = []

        update_progress(15, f"вЏі РќР°С‡РёРЅР°РµРј РїСЂРѕРІРµСЂРєСѓ {total_servers} СЃРµСЂРІРµСЂРѕРІ...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75)  # 15-90%
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"рџ”Ќ РџСЂРѕРІРµСЂСЏРµРј {server_info}...")

            try:
                resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    resources = get_windows_resources_improved(server["ip"])

                cpu_value = resources.get('cpu', 0) if resources else 0

                cpu_results.append({
                    "server": server,
                    "cpu": cpu_value,
                    "success": resources is not None
                })

            except Exception as e:
                cpu_results.append({
                    "server": server,
                    "cpu": 0,
                    "success": False
                })

        update_progress(95, "вЏі Р¤РѕСЂРјРёСЂСѓРµРј РѕС‚С‡РµС‚...")

        # РЎРѕСЂС‚РёСЂСѓРµРј РїРѕ СѓР±С‹РІР°РЅРёСЋ CPU
        cpu_results.sort(key=lambda x: x["cpu"], reverse=True)

        message = f"рџ’» **Р—Р°РіСЂСѓР·РєР° CPU СЃРµСЂРІРµСЂРѕРІ**\n\n"

        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
        windows_cpu = [r for r in cpu_results if r["server"]["type"] == "rdp"]
        linux_cpu = [r for r in cpu_results if r["server"]["type"] == "ssh"]

        # Windows СЃРµСЂРІРµСЂС‹
        message += f"**рџЄџ Windows СЃРµСЂРІРµСЂС‹:**\n"
        for result in windows_cpu[:10]:  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕРї-10
            server = result["server"]
            cpu_value = result["cpu"]
            status_icon = "рџџў" if result["success"] else "рџ”ґ"

            if cpu_value > 80:
                cpu_display = f"рџљЁ {cpu_value}%"
            elif cpu_value > 60:
                cpu_display = f"вљ пёЏ {cpu_value}%"
            else:
                cpu_display = f"{cpu_value}%"

            message += f"{status_icon} {server['name']}: {cpu_display}\n"

        if len(windows_cpu) > 10:
            message += f"вЂў ... Рё РµС‰Рµ {len(windows_cpu) - 10} СЃРµСЂРІРµСЂРѕРІ\n"

        # Linux СЃРµСЂРІРµСЂС‹
        message += f"\n**рџђ§ Linux СЃРµСЂРІРµСЂС‹:**\n"
        for result in linux_cpu[:10]:  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕРї-10
            server = result["server"]
            cpu_value = result["cpu"]
            status_icon = "рџџў" if result["success"] else "рџ”ґ"

            if cpu_value > 80:
                cpu_display = f"рџљЁ {cpu_value}%"
            elif cpu_value > 60:
                cpu_display = f"вљ пёЏ {cpu_value}%"
            else:
                cpu_display = f"{cpu_value}%"

            message += f"{status_icon} {server['name']}: {cpu_display}\n"

        if len(linux_cpu) > 10:
            message += f"вЂў ... Рё РµС‰Рµ {len(linux_cpu) - 10} СЃРµСЂРІРµСЂРѕРІ\n"

        # РЎС‚Р°С‚РёСЃС‚РёРєР°
        total_servers = len(cpu_results)
        high_load = len([r for r in cpu_results if r["cpu"] > 80])
        medium_load = len([r for r in cpu_results if 60 < r["cpu"] <= 80])
        successful_checks = len([r for r in cpu_results if r["success"]])

        message += f"\n**рџ“Љ РЎС‚Р°С‚РёСЃС‚РёРєР°:**\n"
        message += f"вЂў Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ: {total_servers}\n"
        message += f"вЂў РЈСЃРїРµС€РЅРѕ РїСЂРѕРІРµСЂРµРЅРѕ: {successful_checks}\n"
        message += f"вЂў Р’С‹СЃРѕРєР°СЏ РЅР°РіСЂСѓР·РєР° (>80%): {high_load}\n"
        message += f"вЂў РЎСЂРµРґРЅСЏСЏ РЅР°РіСЂСѓР·РєР° (60-80%): {medium_load}\n"

        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_cpu')],
                [InlineKeyboardButton("рџ§  РџСЂРѕРІРµСЂРёС‚СЊ RAM", callback_data='check_ram')],
                [InlineKeyboardButton("рџ’ѕ РџСЂРѕРІРµСЂРёС‚СЊ Disk", callback_data='check_disk')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ CPU: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def perform_ram_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ С‚РѕР»СЊРєРѕ RAM СЃ РґРµС‚Р°Р»СЊРЅС‹Рј РїСЂРѕРіСЂРµСЃСЃРѕРј"""

    def update_progress(progress, status):
        progress_text = f"рџ§  РџСЂРѕРІРµСЂРєР° RAM...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "вЏі РџРѕР»СѓС‡Р°РµРј СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ...")

        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ СЃРµСЂРІРµСЂС‹ РґР»СЏ РїСЂРѕРІРµСЂРєРё
        from extensions.server_checks import initialize_servers
        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        ram_results = []

        update_progress(15, f"вЏі РќР°С‡РёРЅР°РµРј РїСЂРѕРІРµСЂРєСѓ {total_servers} СЃРµСЂРІРµСЂРѕРІ...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75)  # 15-90%
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"рџ”Ќ РџСЂРѕРІРµСЂСЏРµРј {server_info}...")

            try:
                resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    resources = get_windows_resources_improved(server["ip"])

                ram_value = resources.get('ram', 0) if resources else 0

                ram_results.append({
                    "server": server,
                    "ram": ram_value,
                    "success": resources is not None
                })

            except Exception as e:
                ram_results.append({
                    "server": server,
                    "ram": 0,
                    "success": False
                })

        update_progress(95, "вЏі Р¤РѕСЂРјРёСЂСѓРµРј РѕС‚С‡РµС‚...")

        # РЎРѕСЂС‚РёСЂСѓРµРј РїРѕ СѓР±С‹РІР°РЅРёСЋ RAM
        ram_results.sort(key=lambda x: x["ram"], reverse=True)

        message = f"рџ§  **РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ RAM СЃРµСЂРІРµСЂРѕРІ**\n\n"

        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
        windows_ram = [r for r in ram_results if r["server"]["type"] == "rdp"]
        linux_ram = [r for r in ram_results if r["server"]["type"] == "ssh"]

        # Windows СЃРµСЂРІРµСЂС‹
        message += f"**рџЄџ Windows СЃРµСЂРІРµСЂС‹:**\n"
        for result in windows_ram[:10]:  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕРї-10
            server = result["server"]
            ram_value = result["ram"]
            status_icon = "рџџў" if result["success"] else "рџ”ґ"

            if ram_value > 85:
                ram_display = f"рџљЁ {ram_value}%"
            elif ram_value > 70:
                ram_display = f"вљ пёЏ {ram_value}%"
            else:
                ram_display = f"{ram_value}%"

            message += f"{status_icon} {server['name']}: {ram_display}\n"

        if len(windows_ram) > 10:
            message += f"вЂў ... Рё РµС‰Рµ {len(windows_ram) - 10} СЃРµСЂРІРµСЂРѕРІ\n"

        # Linux СЃРµСЂРІРµСЂС‹
        message += f"\n**рџђ§ Linux СЃРµСЂРІРµСЂС‹:**\n"
        for result in linux_ram[:10]:  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕРї-10
            server = result["server"]
            ram_value = result["ram"]
            status_icon = "рџџў" if result["success"] else "рџ”ґ"

            if ram_value > 85:
                ram_display = f"рџљЁ {ram_value}%"
            elif ram_value > 70:
                ram_display = f"вљ пёЏ {ram_value}%"
            else:
                ram_display = f"{ram_value}%"

            message += f"{status_icon} {server['name']}: {ram_display}\n"

        if len(linux_ram) > 10:
            message += f"вЂў ... Рё РµС‰Рµ {len(linux_ram) - 10} СЃРµСЂРІРµСЂРѕРІ\n"

        # РЎС‚Р°С‚РёСЃС‚РёРєР°
        total_servers = len(ram_results)
        high_usage = len([r for r in ram_results if r["ram"] > 85])
        medium_usage = len([r for r in ram_results if 70 < r["ram"] <= 85])
        successful_checks = len([r for r in ram_results if r["success"]])

        message += f"\n**рџ“Љ РЎС‚Р°С‚РёСЃС‚РёРєР°:**\n"
        message += f"вЂў Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ: {total_servers}\n"
        message += f"вЂў РЈСЃРїРµС€РЅРѕ РїСЂРѕРІРµСЂРµРЅРѕ: {successful_checks}\n"
        message += f"вЂў Р’С‹СЃРѕРєРѕРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ (>85%): {high_usage}\n"
        message += f"вЂў РЎСЂРµРґРЅРµРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ (70-85%): {medium_usage}\n"

        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_ram')],
                [InlineKeyboardButton("рџ’» РџСЂРѕРІРµСЂРёС‚СЊ CPU", callback_data='check_cpu')],
                [InlineKeyboardButton("рџ’ѕ РџСЂРѕРІРµСЂРёС‚СЊ Disk", callback_data='check_disk')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ RAM: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def perform_disk_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ С‚РѕР»СЊРєРѕ Disk СЃ РґРµС‚Р°Р»СЊРЅС‹Рј РїСЂРѕРіСЂРµСЃСЃРѕРј"""

    def update_progress(progress, status):
        progress_text = f"рџ’ѕ РџСЂРѕРІРµСЂРєР° Disk...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "вЏі РџРѕР»СѓС‡Р°РµРј СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ...")

        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ СЃРµСЂРІРµСЂС‹ РґР»СЏ РїСЂРѕРІРµСЂРєРё
        from extensions.server_checks import initialize_servers
        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        disk_results = []

        update_progress(15, f"вЏі РќР°С‡РёРЅР°РµРј РїСЂРѕРІРµСЂРєСѓ {total_servers} СЃРµСЂРІРµСЂРѕРІ...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75)  # 15-90%
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"рџ”Ќ РџСЂРѕРІРµСЂСЏРµРј {server_info}...")

            try:
                resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    resources = get_windows_resources_improved(server["ip"])

                disk_value = resources.get('disk', 0) if resources else 0

                disk_results.append({
                    "server": server,
                    "disk": disk_value,
                    "success": resources is not None
                })

            except Exception as e:
                disk_results.append({
                    "server": server,
                    "disk": 0,
                    "success": False
                })

        update_progress(95, "вЏі Р¤РѕСЂРјРёСЂСѓРµРј РѕС‚С‡РµС‚...")

        # РЎРѕСЂС‚РёСЂСѓРµРј РїРѕ СѓР±С‹РІР°РЅРёСЋ Disk
        disk_results.sort(key=lambda x: x["disk"], reverse=True)

        message = f"рџ’ѕ **РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ РґРёСЃРєРѕРІРѕРіРѕ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІР°**\n\n"

        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
        windows_disk = [r for r in disk_results if r["server"]["type"] == "rdp"]
        linux_disk = [r for r in disk_results if r["server"]["type"] == "ssh"]

        # Windows СЃРµСЂРІРµСЂС‹
        message += f"**рџЄџ Windows СЃРµСЂРІРµСЂС‹:**\n"
        for result in windows_disk[:10]:  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕРї-10
            server = result["server"]
            disk_value = result["disk"]
            status_icon = "рџџў" if result["success"] else "рџ”ґ"

            if disk_value > 90:
                disk_display = f"рџљЁ {disk_value}%"
            elif disk_value > 80:
                disk_display = f"вљ пёЏ {disk_value}%"
            else:
                disk_display = f"{disk_value}%"

            message += f"{status_icon} {server['name']}: {disk_display}\n"

        if len(windows_disk) > 10:
            message += f"вЂў ... Рё РµС‰Рµ {len(windows_disk) - 10} СЃРµСЂРІРµСЂРѕРІ\n"

        # Linux СЃРµСЂРІРµСЂС‹
        message += f"\n**рџђ§ Linux СЃРµСЂРІРµСЂС‹:**\n"
        for result in linux_disk[:10]:  # РџРѕРєР°Р·С‹РІР°РµРј С‚РѕРї-10
            server = result["server"]
            disk_value = result["disk"]
            status_icon = "рџџў" if result["success"] else "рџ”ґ"

            if disk_value > 90:
                disk_display = f"рџљЁ {disk_value}%"
            elif disk_value > 80:
                disk_display = f"вљ пёЏ {disk_value}%"
            else:
                disk_display = f"{disk_value}%"

            message += f"{status_icon} {server['name']}: {disk_display}\n"

        if len(linux_disk) > 10:
            message += f"вЂў ... Рё РµС‰Рµ {len(linux_disk) - 10} СЃРµСЂРІРµСЂРѕРІ\n"

        # РЎС‚Р°С‚РёСЃС‚РёРєР°
        total_servers = len(disk_results)
        critical_usage = len([r for r in disk_results if r["disk"] > 90])
        warning_usage = len([r for r in disk_results if 80 < r["disk"] <= 90])
        successful_checks = len([r for r in disk_results if r["success"]])

        message += f"\n**рџ“Љ РЎС‚Р°С‚РёСЃС‚РёРєР°:**\n"
        message += f"вЂў Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ: {total_servers}\n"
        message += f"вЂў РЈСЃРїРµС€РЅРѕ РїСЂРѕРІРµСЂРµРЅРѕ: {successful_checks}\n"
        message += f"вЂў РљСЂРёС‚РёС‡РµСЃРєРѕРµ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ (>90%): {critical_usage}\n"
        message += f"вЂў РџСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ (80-90%): {warning_usage}\n"

        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_disk')],
                [InlineKeyboardButton("рџ’» РџСЂРѕРІРµСЂРёС‚СЊ CPU", callback_data='check_cpu')],
                [InlineKeyboardButton("рџ§  РџСЂРѕРІРµСЂРёС‚СЊ RAM", callback_data='check_ram')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ Disk: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_linux_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё Linux СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    if query:
        query.answer("рџђ§ РџСЂРѕРІРµСЂСЏРµРј Linux СЃРµСЂРІРµСЂС‹...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџђ§ *РџСЂРѕРІРµСЂРєР° Linux СЃРµСЂРІРµСЂРѕРІ...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_linux_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_linux_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ Linux СЃРµСЂРІРµСЂРѕРІ СЃ РїСЂРѕРіСЂРµСЃСЃРѕРј"""

    def update_progress(progress, status):
        progress_text = f"рџђ§ РџСЂРѕРІРµСЂРєР° Linux СЃРµСЂРІРµСЂРѕРІ...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        from extensions.server_checks import check_linux_servers
        update_progress(0, "вЏі РџРѕРґРіРѕС‚РѕРІРєР°...")
        results, total_servers = check_linux_servers(update_progress)

        message = f"рџђ§ **РџСЂРѕРІРµСЂРєР° Linux СЃРµСЂРІРµСЂРѕРІ**\n\n"
        successful_checks = len([r for r in results if r["success"]])
        message += f"вњ… РЈСЃРїРµС€РЅРѕ: {successful_checks}/{total_servers}\n\n"

        for result in results:
            server = result["server"]
            resources = result["resources"]

            # РСЃРїРѕР»СЊР·СѓРµРј РїСЂР°РІРёР»СЊРЅРѕРµ РёРјСЏ СЃРµСЂРІРµСЂР° РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё
            server_name = server["name"]

            if resources:
                message += f"рџџў {server_name}: CPU {resources.get('cpu', 0)}%, RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%\n"
            else:
                message += f"рџ”ґ {server_name}: РЅРµРґРѕСЃС‚СѓРїРµРЅ\n"

        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_linux')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ Linux СЃРµСЂРІРµСЂРѕРІ: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_windows_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё Windows СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    if query:
        query.answer("рџЄџ РџСЂРѕРІРµСЂСЏРµРј Windows СЃРµСЂРІРµСЂС‹...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџЄџ *РџСЂРѕРІРµСЂРєР° Windows СЃРµСЂРІРµСЂРѕРІ...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_windows_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_windows_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ Windows СЃРµСЂРІРµСЂРѕРІ СЃ РїСЂРѕРіСЂРµСЃСЃРѕРј"""

    def update_progress(progress, status):
        progress_text = f"рџЄџ РџСЂРѕРІРµСЂРєР° Windows СЃРµСЂРІРµСЂРѕРІ...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    def safe_get(resources, key, default=0):
        """Р‘РµР·РѕРїР°СЃРЅРѕРµ РїРѕР»СѓС‡РµРЅРёРµ Р·РЅР°С‡РµРЅРёСЏ РёР· resources"""
        if resources is None:
            return default
        return resources.get(key, default)

    try:
        # Р”РРќРђРњРР§Р•РЎРљРР™ РРњРџРћР Рў РґР»СЏ РёР·Р±РµР¶Р°РЅРёСЏ С†РёРєР»РёС‡РµСЃРєРёС… Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
        from extensions.server_checks import (
            check_windows_2025_servers,
            check_domain_windows_servers,
            check_admin_windows_servers,
            check_standard_windows_servers
        )

        update_progress(0, "вЏі РџРѕРґРіРѕС‚РѕРІРєР°...")

        # РџСЂРѕРІРµСЂСЏРµРј РІСЃРµ С‚РёРїС‹ Windows СЃРµСЂРІРµСЂРѕРІ
        win2025_results, win2025_total = check_windows_2025_servers(update_progress)
        domain_results, domain_total = check_domain_windows_servers(update_progress)
        admin_results, admin_total = check_admin_windows_servers(update_progress)
        win_std_results, win_std_total = check_standard_windows_servers(update_progress)

        message = f"рџЄџ **РџСЂРѕРІРµСЂРєР° Windows СЃРµСЂРІРµСЂРѕРІ**\n\n"

        # Windows 2025
        win2025_success = len([r for r in win2025_results if r["success"]])
        message += f"**Windows 2025:** {win2025_success}/{win2025_total}\n"
        for result in win2025_results:
            server = result["server"]
            resources = result["resources"]
            status = "рџџў" if result["success"] else "рџ”ґ"

            # Р—РђР©РР©Р•РќРќР«Р™ Р”РћРЎРўРЈРџ Рљ Р Р•РЎРЈР РЎРђРњ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Р”РѕРјРµРЅРЅС‹Рµ СЃРµСЂРІРµСЂС‹
        domain_success = len([r for r in domain_results if r["success"]])
        message += f"\n**Р”РѕРјРµРЅРЅС‹Рµ Windows:** {domain_success}/{domain_total}\n"
        for result in domain_results:
            server = result["server"]
            resources = result["resources"]
            status = "рџџў" if result["success"] else "рџ”ґ"

            # Р—РђР©РР©Р•РќРќР«Р™ Р”РћРЎРўРЈРџ Рљ Р Р•РЎРЈР РЎРђРњ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # РЎРµСЂРІРµСЂС‹ СЃ Admin
        admin_success = len([r for r in admin_results if r["success"]])
        message += f"\n**Windows (Admin):** {admin_success}/{admin_total}\n"
        for result in admin_results:
            server = result["server"]
            resources = result["resources"]
            status = "рџџў" if result["success"] else "рџ”ґ"

            # Р—РђР©РР©Р•РќРќР«Р™ Р”РћРЎРўРЈРџ Рљ Р Р•РЎРЈР РЎРђРњ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ Windows
        win_std_success = len([r for r in win_std_results if r["success"]])
        message += f"\n**РћР±С‹С‡РЅС‹Рµ Windows:** {win_std_success}/{win_std_total}\n"
        for result in win_std_results:
            server = result["server"]
            resources = result["resources"]
            status = "рџџў" if result["success"] else "рџ”ґ"

            # Р—РђР©РР©Р•РќРќР«Р™ Р”РћРЎРўРЈРџ Рљ Р Р•РЎРЈР РЎРђРњ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_windows')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ Windows СЃРµСЂРІРµСЂРѕРІ: {e}"
        debug_log(error_msg)
        import traceback
        debug_log(f"РџРѕРґСЂРѕР±РЅРѕСЃС‚Рё РѕС€РёР±РєРё: {traceback.format_exc()}")
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_other_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїСЂРѕРІРµСЂРєРё РґСЂСѓРіРёС… СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    if query:
        query.answer("рџ“Ў РџСЂРѕРІРµСЂСЏРµРј РґСЂСѓРіРёРµ СЃРµСЂРІРµСЂС‹...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџ“Ў *РџСЂРѕРІРµСЂРєР° РґСЂСѓРіРёС… СЃРµСЂРІРµСЂРѕРІ...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_other_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_other_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїСЂРѕРІРµСЂРєСѓ РґСЂСѓРіРёС… СЃРµСЂРІРµСЂРѕРІ"""
    try:
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()
        ping_servers = [s for s in servers if s["type"] == "ping"]

        message = f"рџ“Ў **РџСЂРѕРІРµСЂРєР° РґСЂСѓРіРёС… СЃРµСЂРІРµСЂРѕРІ**\n\n"
        successful_checks = 0

        for server in ping_servers:
            is_up = check_server_availability(server)
            if is_up:
                successful_checks += 1
                message += f"рџџў {server['name']}: РґРѕСЃС‚СѓРїРµРЅ\n"
            else:
                message += f"рџ”ґ {server['name']}: РЅРµРґРѕСЃС‚СѓРїРµРЅ\n"

        message += f"\nвњ… Р”РѕСЃС‚СѓРїРЅРѕ: {successful_checks}/{len(ping_servers)}"
        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_other')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ РґСЂСѓРіРёС… СЃРµСЂРІРµСЂРѕРІ: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_all_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїРѕР»РЅРѕР№ РїСЂРѕРІРµСЂРєРё РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return
    
    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        else:
            update.message.reply_text("рџ“Љ РњРѕРЅРёС‚РѕСЂРёРЅРі СЂРµСЃСѓСЂСЃРѕРІ РѕС‚РєР»СЋС‡С‘РЅ")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="рџ”Ќ *Р—Р°РїСѓСЃРєР°СЋ РїСЂРѕРІРµСЂРєСѓ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ...*\n\nвЏі РџРѕРґРіРѕС‚РѕРІРєР°...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_full_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_full_check(context, chat_id, progress_message_id):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РїРѕР»РЅСѓСЋ РїСЂРѕРІРµСЂРєСѓ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ"""

    def update_progress(progress, status):
        progress_text = f"рџ”Ќ РџРѕР»РЅР°СЏ РїСЂРѕРІРµСЂРєР° РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "вЏі РџРѕРґРіРѕС‚РѕРІРєР°...")
        from extensions.server_checks import check_all_servers_by_type
        results, stats = check_all_servers_by_type()

        total_checked = stats["windows_2025"]["checked"] + stats["standard_windows"]["checked"] + stats["linux"]["checked"]
        total_success = stats["windows_2025"]["success"] + stats["standard_windows"]["success"] + stats["linux"]["success"]

        message = f"рџ“Љ **РџРѕР»РЅР°СЏ РїСЂРѕРІРµСЂРєР° СЃРµСЂРІРµСЂРѕРІ**\n\n"
        message += f"вњ… Р’СЃРµРіРѕ РґРѕСЃС‚СѓРїРЅРѕ: {total_success}/{total_checked}\n\n"

        message += f"**Windows 2025:** {stats['windows_2025']['success']}/{stats['windows_2025']['checked']}\n"
        message += f"**РћР±С‹С‡РЅС‹Рµ Windows:** {stats['standard_windows']['success']}/{stats['standard_windows']['checked']}\n"
        message += f"**Linux:** {stats['linux']['success']}/{stats['linux']['checked']}\n"

        message += f"\nвЏ° РћР±РЅРѕРІР»РµРЅРѕ: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='check_all_resources')],
                [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='check_resources')],
                [InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
                 InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"вќЊ РћС€РёР±РєР° РїСЂРё РїРѕР»РЅРѕР№ РїСЂРѕРІРµСЂРєРµ: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def start_monitoring():
    """Р—Р°РїСѓСЃРєР°РµС‚ РѕСЃРЅРѕРІРЅРѕР№ С†РёРєР» РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    global servers, bot, monitoring_active, last_report_date, morning_data

    # Р›РµРЅРёРІР°СЏ РёРЅРёС†РёР°Р»РёР·Р°С†РёСЏ СЃРµСЂРІРµСЂРѕРІ
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()

    # РСЃРєР»СЋС‡Р°РµРј СЃРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РёР· СЃРїРёСЃРєР°
    config = get_config()
    monitor_server_ip = getattr(config, "MONITOR_SERVER_IP", "")
    if monitor_server_ip:
        servers = [s for s in servers if s["ip"] != monitor_server_ip]
        debug_log(
            "вњ… РЎРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР° "
            f"{monitor_server_ip} РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РёСЃРєР»СЋС‡РµРЅ РёР· СЃРїРёСЃРєР°. "
            f"РћСЃС‚Р°Р»РѕСЃСЊ {len(servers)} СЃРµСЂРІРµСЂРѕРІ"
        )
    else:
        debug_log("вљ пёЏ РЎРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РЅРµ РёСЃРєР»СЋС‡РµРЅ: MONITOR_SERVER_IP РЅРµ Р·Р°РґР°РЅ")

    # Р›РµРЅРёРІР°СЏ РёРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Р±РѕС‚Р°
    from telegram import Bot
    bot = Bot(token=config.TELEGRAM_TOKEN)
    ensure_alerts_config()
    init_telegram_bot(bot, config.CHAT_IDS)
    
    # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ server_status (С‚РѕР»СЊРєРѕ РґР»СЏ РѕСЃС‚Р°РІС€РёС…СЃСЏ СЃРµСЂРІРµСЂРѕРІ)
    for server in servers:
        server_status[server["ip"]] = {
            "last_up": datetime.now(),
            "alert_sent": False,
            "name": server["name"],
            "type": server["type"],
            "resources": None,
            "last_alert": {},
            "monitoring_enabled": server.get("enabled", True)
        }

    debug_log(f"вњ… РњРѕРЅРёС‚РѕСЂРёРЅРі Р·Р°РїСѓС‰РµРЅ РґР»СЏ {len(servers)} СЃРµСЂРІРµСЂРѕРІ")

    # РћР±РЅРѕРІР»СЏРµРј СЃС‚Р°СЂС‚РѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ
    start_message = "рџџў *РњРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂРѕРІ Р·Р°РїСѓС‰РµРЅ*\n\n"
    if getattr(config, "APP_VERSION", None):
        start_message += f"рџ”– *Р’РµСЂСЃРёСЏ:* {config.APP_VERSION}\n"
    start_message += (
        f"вЂў РЎРµСЂРІРµСЂРѕРІ РІ РјРѕРЅРёС‚РѕСЂРёРЅРіРµ: {len(servers)}\n"
        f"вЂў РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ: РєР°Р¶РґС‹Рµ {config.RESOURCE_CHECK_INTERVAL // 60} РјРёРЅСѓС‚\n"
        f"вЂў РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚: {config.DATA_COLLECTION_TIME.strftime('%H:%M')}\n\n"
    )

    # РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РІРµР±-РёРЅС‚РµСЂС„РµР№СЃРµ
    from extensions.extension_manager import extension_manager
    if extension_manager.is_extension_enabled('web_interface'):
        start_message += f"рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* {get_web_interface_url(config)}\n"
        start_message += "_*РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ РІ Р»РѕРєР°Р»СЊРЅРѕР№ СЃРµС‚Рё_\n"
    else:
        start_message += "рџЊђ *Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ:* рџ”ґ РѕС‚РєР»СЋС‡РµРЅ\n"

    send_alert(start_message)

    last_resource_check = datetime.now()
    last_data_collection = None

    # РРЅРёС†РёР°Р»РёР·РёСЂСѓРµРј morning_data РµСЃР»Рё РѕРЅР° РїСѓСЃС‚Р°СЏ
    if not morning_data:
        morning_data = {}

    while True:
        current_time = datetime.now()
        current_time_time = current_time.time()

        # РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ
        config = get_config()
        if (current_time - last_resource_check).total_seconds() >= config.RESOURCE_CHECK_INTERVAL:
            if monitoring_active and not is_silent_time():
                debug_log("рџ”„ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ...")
                check_resources_automatically()
                last_resource_check = current_time
            else:
                debug_log("вЏёпёЏ РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РїСЂРѕРїСѓС‰РµРЅР° (С‚РёС…РёР№ СЂРµР¶РёРј РёР»Рё РјРѕРЅРёС‚РѕСЂРёРЅРі РЅРµР°РєС‚РёРІРµРЅ)")

        # РЎР±РѕСЂ Рё РѕС‚РїСЂР°РІРєР° СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°
        config = get_config()
        if (current_time_time.hour == config.DATA_COLLECTION_TIME.hour and
            current_time_time.minute == config.DATA_COLLECTION_TIME.minute):

            # РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЃРµРіРѕРґРЅСЏ РµС‰Рµ РЅРµ РѕС‚РїСЂР°РІР»СЏР»Рё РѕС‚С‡РµС‚
            today = current_time.date()
            if last_report_date != today:
                debug_log(f"[{current_time}] рџ”Ќ РЎРѕР±РёСЂР°РµРј РґР°РЅРЅС‹Рµ РґР»СЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°...")

                # РЎРѕР±РёСЂР°РµРј С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂРѕРІ
                morning_status = get_current_server_status()
                morning_data = {
                    "status": morning_status,
                    "collection_time": current_time,
                    "manual_call": False  # РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ РІС‹Р·РѕРІ
                }
                last_data_collection = current_time

                debug_log(f"вњ… Р”Р°РЅРЅС‹Рµ СЃРѕР±СЂР°РЅС‹: {len(morning_status['ok'])} РґРѕСЃС‚СѓРїРЅРѕ, {len(morning_status['failed'])} РЅРµРґРѕСЃС‚СѓРїРЅРѕ")

                # РЎР РђР—РЈ РѕС‚РїСЂР°РІР»СЏРµРј РѕС‚С‡РµС‚ РїРѕСЃР»Рµ СЃР±РѕСЂР° РґР°РЅРЅС‹С…
                debug_log(f"[{current_time}] рџ“Љ РћС‚РїСЂР°РІРєР° СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°...")
                send_morning_report(manual_call=False)  # РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ РІС‹Р·РѕРІ
                last_report_date = today
                debug_log("вњ… РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚ РѕС‚РїСЂР°РІР»РµРЅ")

                # Р”РѕР±Р°РІР»СЏРµРј Р·Р°РґРµСЂР¶РєСѓ С‡С‚РѕР±С‹ РЅРµ Р·Р°РїСѓСЃРєР°С‚СЊ РїРѕРІС‚РѕСЂРЅРѕ РІ С‚Сѓ Р¶Рµ РјРёРЅСѓС‚Сѓ
                time.sleep(65)  # РЎРїРёРј 65 СЃРµРєСѓРЅРґ С‡С‚РѕР±С‹ РІС‹Р№С‚Рё Р·Р° РїСЂРµРґРµР»С‹ РјРёРЅСѓС‚С‹ СЃР±РѕСЂР°
            else:
                debug_log(f"вЏ­пёЏ РћС‚С‡РµС‚ СѓР¶Рµ РѕС‚РїСЂР°РІР»РµРЅ СЃРµРіРѕРґРЅСЏ {last_report_date}")

        # РћСЃРЅРѕРІРЅРѕР№ С†РёРєР» РјРѕРЅРёС‚РѕСЂРёРЅРіР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
        if monitoring_active:
            last_check_time = current_time

            refresh_servers()

            for server in servers:
                try:
                    ip = server["ip"]
                    status = server_status[ip]

                    # РџРћР›РќРћРЎРўР¬Р® РРЎРљР›Р®Р§РђР•Рњ СЃРµСЂРІРµСЂ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РёР· Р»СЋР±С‹С… РїСЂРѕРІРµСЂРѕРє
                    if ip == monitor_server_ip:
                        server_status[ip]["last_up"] = current_time
                        continue

                    monitoring_enabled = is_server_monitoring_enabled(ip)
                    if not monitoring_enabled:
                        server_status[ip]["monitoring_enabled"] = False
                        continue

                    if not status.get("monitoring_enabled", True):
                        server_status[ip]["monitoring_enabled"] = True
                        server_status[ip]["alert_sent"] = False
                        server_status[ip]["last_alert"] = {}

                    # РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
                    is_up = check_server_availability(server)

                    if is_up:
                        handle_server_up(ip, status, current_time)
                    else:
                        handle_server_down(ip, status, current_time)

                except Exception as e:
                    debug_log(f"вќЊ РћС€РёР±РєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° {server['name']}: {e}")

        time.sleep(config.CHECK_INTERVAL)

def handle_server_up(ip, status, current_time):
    """РћР±СЂР°Р±РѕС‚РєР° РґРѕСЃС‚СѓРїРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    last_up = status.get("last_up")

    # РµСЃР»Рё РїРѕ РєР°РєРѕР№-С‚Рѕ РїСЂРёС‡РёРЅРµ last_up = None вЂ” РЅРµ РїР°РґР°РµРј
    if status.get("alert_sent"):
        if last_up:
            downtime = (current_time - last_up).total_seconds()
            send_alert(
                f"вњ… {status['name']} ({ip}) РґРѕСЃС‚СѓРїРµРЅ (РїСЂРѕСЃС‚РѕР№: {int(downtime // 60)} РјРёРЅ)"
            )
        else:
            send_alert(f"вњ… {status['name']} ({ip}) РґРѕСЃС‚СѓРїРµРЅ")

    server_status[ip] = {
        "last_up": current_time,
        "alert_sent": False,
        "name": status.get("name"),
        "type": status.get("type"),
        "resources": server_status.get(ip, {}).get("resources"),
        "last_alert": server_status.get(ip, {}).get("last_alert", {}),
    }


def handle_server_down(ip, status, current_time):
    """РћР±СЂР°Р±РѕС‚РєР° РЅРµРґРѕСЃС‚СѓРїРЅРѕРіРѕ СЃРµСЂРІРµСЂР°"""
    config = get_config()

    last_up = status.get("last_up")
    if not last_up:
        # РЎР°РјРѕРµ РІР°Р¶РЅРѕРµ: РЅРµ РґР°С‘Рј СѓРїР°СЃС‚СЊ РЅР° None, РёРЅР°С‡Рµ Р°Р»РµСЂС‚ РЅРёРєРѕРіРґР° РЅРµ СѓР№РґС‘С‚
        server_status[ip]["last_up"] = current_time
        status["last_up"] = current_time
        last_up = current_time

    downtime = (current_time - last_up).total_seconds()

    if downtime >= config.MAX_FAIL_TIME and not status.get("alert_sent"):
        send_alert(f"рџљЁ {status['name']} ({ip}) РЅРµ РѕС‚РІРµС‡Р°РµС‚ (РїСЂРѕРІРµСЂРєР°: {status['type'].upper()})")
        server_status[ip]["alert_sent"] = True

def check_resources_automatically():
    """РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ СЃ СѓРјРЅС‹РјРё РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏРјРё"""
    global resource_history, last_resource_check, resource_alerts_sent

    if not _resource_monitor_enabled():
        debug_log("вЏёпёЏ РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РїСЂРѕРїСѓС‰РµРЅР° (СЂР°СЃС€РёСЂРµРЅРёРµ РѕС‚РєР»СЋС‡РµРЅРѕ)")
        return

    debug_log("рџ”Ќ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ СЃРµСЂРІРµСЂРѕРІ...")

    if not monitoring_active or is_silent_time():
        debug_log("вЏёпёЏ РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РїСЂРѕРїСѓС‰РµРЅР° (РјРѕРЅРёС‚РѕСЂРёРЅРі РЅРµР°РєС‚РёРІРµРЅ РёР»Рё С‚РёС…РёР№ СЂРµР¶РёРј)")
        return

    current_time = datetime.now()
    alerts_found = []

    # РџСЂРѕРІРµСЂСЏРµРј РІСЃРµ СЃРµСЂРІРµСЂС‹
    for server in servers:
        try:
            ip = server["ip"]
            server_name = server["name"]

            if not is_server_monitoring_enabled(ip):
                continue

            debug_log(f"рџ”Ќ РџСЂРѕРІРµСЂСЏРµРј СЂРµСЃСѓСЂСЃС‹ {server_name} ({ip})")

            # РџРѕР»СѓС‡Р°РµРј С‚РµРєСѓС‰РёРµ СЂРµСЃСѓСЂСЃС‹
            current_resources = None
            if server["type"] == "ssh":
                from extensions.server_checks import get_linux_resources_improved
                current_resources = get_linux_resources_improved(ip)
            elif server["type"] == "rdp":
                from extensions.server_checks import get_windows_resources_improved
                current_resources = get_windows_resources_improved(ip)

            if not current_resources:
                continue

            # РРЅРёС†РёР°Р»РёР·РёСЂСѓРµРј РёСЃС‚РѕСЂРёСЋ РґР»СЏ СЃРµСЂРІРµСЂР° РµСЃР»Рё РЅСѓР¶РЅРѕ
            if ip not in resource_history:
                resource_history[ip] = []

            # Р”РѕР±Р°РІР»СЏРµРј С‚РµРєСѓС‰РёРµ СЂРµСЃСѓСЂСЃС‹ РІ РёСЃС‚РѕСЂРёСЋ
            resource_entry = {
                "timestamp": current_time,
                "cpu": current_resources.get("cpu", 0),
                "ram": current_resources.get("ram", 0),
                "disk": current_resources.get("disk", 0),
                "server_name": server_name
            }

            resource_history[ip].append(resource_entry)

            # РћРіСЂР°РЅРёС‡РёРІР°РµРј РёСЃС‚РѕСЂРёСЋ РїРѕСЃР»РµРґРЅРёРјРё 10 Р·Р°РїРёСЃСЏРјРё
            if len(resource_history[ip]) > 10:
                resource_history[ip] = resource_history[ip][-10:]

            # РџСЂРѕРІРµСЂСЏРµРј СѓСЃР»РѕРІРёСЏ РґР»СЏ Р°Р»РµСЂС‚РѕРІ
            server_alerts = check_resource_alerts(ip, resource_entry)

            if server_alerts:
                alerts_found.extend(server_alerts)
                debug_log(f"вљ пёЏ РќР°Р№РґРµРЅС‹ РїСЂРѕР±Р»РµРјС‹ РґР»СЏ {server_name}: {server_alerts}")

        except Exception as e:
            debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРё РїСЂРѕРІРµСЂРєРµ СЂРµСЃСѓСЂСЃРѕРІ {server['name']}: {e}")
            continue

    # РћС‚РїСЂР°РІР»СЏРµРј Р°Р»РµСЂС‚С‹ РµСЃР»Рё РµСЃС‚СЊ
    if alerts_found:
        send_resource_alerts(alerts_found)

    last_resource_check = current_time
    debug_log(f"вњ… РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РїСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ Р·Р°РІРµСЂС€РµРЅР°. РќР°Р№РґРµРЅРѕ РїСЂРѕР±Р»РµРј: {len(alerts_found)}")

def check_resource_alerts(ip, current_resource):
    """РџСЂРѕРІРµСЂСЏРµС‚ СѓСЃР»РѕРІРёСЏ РґР»СЏ РѕС‚РїСЂР°РІРєРё Р°Р»РµСЂС‚РѕРІ РїРѕ СЂРµСЃСѓСЂСЃР°Рј"""
    from config.db_settings import RESOURCE_ALERT_THRESHOLDS, RESOURCE_ALERT_INTERVAL

    alerts = []
    server_name = current_resource["server_name"]

    # РџРѕР»СѓС‡Р°РµРј РёСЃС‚РѕСЂРёСЋ РїСЂРѕРІРµСЂРѕРє (РёСЃРєР»СЋС‡Р°СЏ С‚РµРєСѓС‰СѓСЋ)
    history = resource_history.get(ip, [])[:-1]  # Р’СЃРµ РєСЂРѕРјРµ РїРѕСЃР»РµРґРЅРµР№ Р·Р°РїРёСЃРё

    # РџСЂРѕРІРµСЂРєР° Disk (РѕРґРЅР° РїСЂРѕРІРµСЂРєР°)
    disk_usage = current_resource.get("disk", 0)
    if disk_usage >= RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
        # РџСЂРѕРІРµСЂСЏРµРј, РЅРµ РѕС‚РїСЂР°РІР»СЏР»Рё Р»Рё СѓР¶Рµ Р°Р»РµСЂС‚ РїРѕ РґРёСЃРєСѓ
        alert_key = f"{ip}_disk"
        if alert_key not in resource_alerts_sent or (datetime.now() - resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
            alerts.append(f"рџ’ѕ **Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ** РЅР° {server_name}: {disk_usage}% (РїСЂРµРІС‹С€РµРЅ РїРѕСЂРѕРі {RESOURCE_ALERT_THRESHOLDS['disk_alert']}%)")
            resource_alerts_sent[alert_key] = datetime.now()

    # РџСЂРѕРІРµСЂРєР° CPU (РґРІРµ РїСЂРѕРІРµСЂРєРё РїРѕРґСЂСЏРґ)
    cpu_usage = current_resource.get("cpu", 0)
    if cpu_usage >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
        # РџСЂРѕРІРµСЂСЏРµРј РїСЂРµРґС‹РґСѓС‰СѓСЋ Р·Р°РїРёСЃСЊ
        if len(history) >= 1:
            prev_cpu = history[-1].get("cpu", 0)
            if prev_cpu >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
                alert_key = f"{ip}_cpu"
                if alert_key not in resource_alerts_sent or (datetime.now() - resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
                    alerts.append(f"рџ’» **РџСЂРѕС†РµСЃСЃРѕСЂ** РЅР° {server_name}: {prev_cpu}% в†’ {cpu_usage}% (2 РїСЂРѕРІРµСЂРєРё РїРѕРґСЂСЏРґ >= {RESOURCE_ALERT_THRESHOLDS['cpu_alert']}%)")
                    resource_alerts_sent[alert_key] = datetime.now()

    # РџСЂРѕРІРµСЂРєР° RAM (РґРІРµ РїСЂРѕРІРµСЂРєРё РїРѕРґСЂСЏРґ)
    ram_usage = current_resource.get("ram", 0)
    if ram_usage >= RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
        # РџСЂРѕРІРµСЂСЏРµРј РїСЂРµРґС‹РґСѓС‰СѓСЋ Р·Р°РїРёСЃСЊ
        if len(history) >= 1:
            prev_ram = history[-1].get("ram", 0)
            if prev_ram >= RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
                alert_key = f"{ip}_ram"
                if alert_key not in resource_alerts_sent or (datetime.now() - resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
                    alerts.append(f"рџ§  **РџР°РјСЏС‚СЊ** РЅР° {server_name}: {prev_ram}% в†’ {ram_usage}% (2 РїСЂРѕРІРµСЂРєРё РїРѕРґСЂСЏРґ >= {RESOURCE_ALERT_THRESHOLDS['ram_alert']}%)")
                    resource_alerts_sent[alert_key] = datetime.now()

    return alerts

def send_resource_alerts(alerts):
    """РћС‚РїСЂР°РІР»СЏРµС‚ Р°Р»РµСЂС‚С‹ РїРѕ СЂРµСЃСѓСЂСЃР°Рј"""
    if not alerts:
        return

    message = "рџљЁ *РџСЂРѕР±Р»РµРјС‹ СЃ СЂРµСЃСѓСЂСЃР°РјРё СЃРµСЂРІРµСЂРѕРІ*\n\n"

    # Р“СЂСѓРїРїРёСЂСѓРµРј Р°Р»РµСЂС‚С‹ РїРѕ С‚РёРїР°Рј СЂРµСЃСѓСЂСЃРѕРІ РґР»СЏ Р»СѓС‡С€РµР№ С‡РёС‚Р°РµРјРѕСЃС‚Рё
    disk_alerts = [a for a in alerts if "рџ’ѕ" in a]
    cpu_alerts = [a for a in alerts if "рџ’»" in a]
    ram_alerts = [a for a in alerts if "рџ§ " in a]

    # Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ
    if disk_alerts:
        message += "рџ’ѕ **Р”РёСЃРєРѕРІРѕРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІРѕ:**\n"
        for alert in disk_alerts:
            # РР·РІР»РµРєР°РµРј РёРЅС„РѕСЂРјР°С†РёСЋ РёР· Р°Р»РµСЂС‚Р°
            parts = alert.split("РЅР° ")
            if len(parts) > 1:
                server_info = parts[1]
                message += f"вЂў {server_info}\n"
        message += "\n"

    # РџСЂРѕС†РµСЃСЃРѕСЂ
    if cpu_alerts:
        message += "рџ’» **РџСЂРѕС†РµСЃСЃРѕСЂ (CPU):**\n"
        for alert in cpu_alerts:
            parts = alert.split("РЅР° ")
            if len(parts) > 1:
                server_info = parts[1]
                message += f"вЂў {server_info}\n"
        message += "\n"

    # РџР°РјСЏС‚СЊ
    if ram_alerts:
        message += "рџ§  **РџР°РјСЏС‚СЊ (RAM):**\n"
        for alert in ram_alerts:
            parts = alert.split("РЅР° ")
            if len(parts) > 1:
                server_info = parts[1]
                message += f"вЂў {server_info}\n"
        message += "\n"

    message += f"вЏ° Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё: {datetime.now().strftime('%H:%M:%S')}"

    send_alert(message)
    debug_log(f"вњ… РћС‚РїСЂР°РІР»РµРЅС‹ Р°Р»РµСЂС‚С‹ РїРѕ СЂРµСЃСѓСЂСЃР°Рј: {len(alerts)} РїСЂРѕР±Р»РµРј")

def close_menu(update, context):
    """Р—Р°РєСЂС‹РІР°РµС‚ РјРµРЅСЋ"""
    query = update.callback_query
    query.answer()
    query.delete_message()

def diagnose_menu_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РјРµРЅСЋ РґРёР°РіРЅРѕСЃС‚РёРєРё"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("рџ”§ РњРµРЅСЋ РґРёР°РіРЅРѕСЃС‚РёРєРё РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ")

def daily_report_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РµР¶РµРґРЅРµРІРЅРѕРіРѕ РѕС‚С‡РµС‚Р°"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("рџ“Љ Р•Р¶РµРґРЅРµРІРЅС‹Р№ РѕС‚С‡РµС‚ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ")

def toggle_silent_mode_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("рџ”‡ РџРµСЂРµРєР»СЋС‡РµРЅРёРµ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°")

def send_morning_report_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РґР»СЏ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕР№ РѕС‚РїСЂР°РІРєРё СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р° (С‡РµСЂРµР· РЅРѕРІС‹Р№ modules.morning_report)"""
    query = update.callback_query if hasattr(update, "callback_query") else None
    chat_id = query.message.chat_id if query else update.message.chat_id
    if query:
        try:
            query.answer("вЏі Р¤РѕСЂРјРёСЂСѓСЋ РѕС‚С‡РµС‚...")
        except Exception as e:
            debug_log(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РІРµС‚РёС‚СЊ РЅР° callback: {e}")

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        else:
            update.message.reply_text("в›” РЈ РІР°СЃ РЅРµС‚ РїСЂР°РІ РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ СЌС‚РѕР№ РєРѕРјР°РЅРґС‹")
        return

    try:
        from modules.morning_report import morning_report

        # Р“РµРЅРµСЂРёСЂСѓРµРј РѕС‚С‡С‘С‚ (СЂСѓС‡РЅРѕР№ Р·Р°РїСѓСЃРє)
        report_text = morning_report.force_report()

        # РћС‚РїСЂР°РІР»СЏРµРј РІ С‚РµРєСѓС‰РёР№ С‡Р°С‚ (РєР°Рє РѕС‚РґРµР»СЊРЅРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ вЂ” РЅР°РґС‘Р¶РЅРµРµ, С‡РµРј edit)
        # Р•СЃР»Рё Telegram РЅРµ РјРѕР¶РµС‚ СЂР°СЃРїР°СЂСЃРёС‚СЊ Markdown (РёР·-Р·Р° СЃРїРµС†СЃРёРјРІРѕР»РѕРІ РІ РґР°РЅРЅС‹С…),
        # РѕС‚РїСЂР°РІР»СЏРµРј РѕС‚С‡С‘С‚ РѕР±С‹С‡РЅС‹Рј С‚РµРєСЃС‚РѕРј, С‡С‚РѕР±С‹ РєРѕРјР°РЅРґР° РЅРµ РїР°РґР°Р»Р°.
        try:
            context.bot.send_message(
                chat_id=chat_id,
                text=report_text,
                parse_mode="Markdown"
            )
        except Exception as send_error:
            error_text = str(send_error).lower()
            if "parse entities" not in error_text:
                raise

            debug_log(
                "вљ пёЏ РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡С‘С‚ СЃРѕРґРµСЂР¶РёС‚ РЅРµРІР°Р»РёРґРЅС‹Р№ Markdown, "
                "РїРѕРІС‚РѕСЂРЅР°СЏ РѕС‚РїСЂР°РІРєР° СЃ РѕС‚РєР»СЋС‡С‘РЅРЅС‹Рј parse_mode"
            )
            context.bot.send_message(
                chat_id=chat_id,
                text=report_text,
                parse_mode=None
            )

        if not query:
            update.message.reply_text("рџ“Љ РћС‚С‡РµС‚ РѕС‚РїСЂР°РІР»РµРЅ")

    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ/РѕС‚РїСЂР°РІРєРё СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡С‘С‚Р°: {e}")
        import traceback
        debug_log(f"рџ’Ґ Traceback:\n{traceback.format_exc()}")
        if query:
            query.edit_message_text("вќЊ РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡С‘С‚Р°")
        else:
            update.message.reply_text("вќЊ РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡С‘С‚Р°")

def send_morning_report(manual_call=False):
    """РћС‚РїСЂР°РІР»СЏРµС‚ СѓС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚ Рѕ РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё СЃРµСЂРІРµСЂРѕРІ Рё Р±СЌРєР°РїР°С…

    Args:
        manual_call (bool): Р•СЃР»Рё True - РѕС‚С‡РµС‚ РІС‹Р·РІР°РЅ РІСЂСѓС‡РЅСѓСЋ, РµСЃР»Рё False - РїРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ
    """
    global morning_data

    current_time = datetime.now()

    if manual_call:
        debug_log(f"[{current_time}] рџ“Љ Р СѓС‡РЅРѕР№ РІС‹Р·РѕРІ РѕС‚С‡РµС‚Р°")
        # Р”Р»СЏ СЂСѓС‡РЅРѕРіРѕ РІС‹Р·РѕРІР° СЃРѕР±РёСЂР°РµРј РЎР’Р•Р–РР• РґР°РЅРЅС‹Рµ
        current_status = get_current_server_status()
        morning_data = {
            "status": current_status,
            "collection_time": current_time,
            "manual_call": True  # РџРѕРјРµС‡Р°РµРј РєР°Рє СЂСѓС‡РЅРѕР№ РІС‹Р·РѕРІ
        }
    else:
        debug_log(f"[{current_time}] рџ“Љ РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СѓС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚")
        # Р”Р»СЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕРіРѕ РѕС‚С‡РµС‚Р° РёСЃРїРѕР»СЊР·СѓРµРј РґР°РЅРЅС‹Рµ СЃРѕР±СЂР°РЅРЅС‹Рµ РІ DATA_COLLECTION_TIME
        if not morning_data or "status" not in morning_data:
            debug_log("вќЊ РќРµС‚ РґР°РЅРЅС‹С… РґР»СЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°, СЃРѕР±РёСЂР°РµРј С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ...")
            current_status = get_current_server_status()
            morning_data = {
                "status": current_status,
                "collection_time": current_time,
                "manual_call": False
            }

    status = morning_data["status"]
    collection_time = morning_data.get("collection_time", datetime.now())
    is_manual = morning_data.get("manual_call", False)

    total_servers = len(status["ok"]) + len(status["failed"])
    up_count = len(status["ok"])
    down_count = len(status["failed"])

    # Р¤РѕСЂРјРёСЂСѓРµРј СЃРѕРѕР±С‰РµРЅРёРµ СЃ СѓРєР°Р·Р°РЅРёРµРј С‚РёРїР° РѕС‚С‡РµС‚Р°
    if is_manual:
        report_type = "Р СѓС‡РЅРѕР№ Р·Р°РїСЂРѕСЃ"
        time_prefix = "вЏ° *Р’СЂРµРјСЏ РїСЂРѕРІРµСЂРєРё:*"
    else:
        report_type = "РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚"
        time_prefix = "вЏ° *Р’СЂРµРјСЏ СЃР±РѕСЂР° РґР°РЅРЅС‹С…:*"

    message = f"рџ“Љ *{report_type} Рѕ РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё СЃРµСЂРІРµСЂРѕРІ*\n\n"
    message += f"{time_prefix} {collection_time.strftime('%H:%M')}\n"
    message += f"рџ”ў *Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ:* {total_servers}\n"
    message += f"рџџў *Р”РѕСЃС‚СѓРїРЅРѕ:* {up_count}\n"
    message += f"рџ”ґ *РќРµРґРѕСЃС‚СѓРїРЅРѕ:* {down_count}\n"

    # Р”Р»СЏ СЂСѓС‡РЅРѕРіРѕ РѕС‚С‡РµС‚Р° РёСЃРїРѕР»СЊР·СѓРµРј РґСЂСѓРіРѕР№ РїРµСЂРёРѕРґ Р±СЌРєР°РїРѕРІ
    try:
        from extensions.extension_manager import extension_manager
        include_mail = extension_manager.is_extension_enabled('mail_backup_monitor')
    except Exception:
        include_mail = False

    if is_manual:
        backup_data = get_backup_summary_for_report(
            period_hours=24,
            include_mail=include_mail,
        )  # РџРѕСЃР»РµРґРЅРёРµ 24 С‡Р°СЃР°
    else:
        backup_data = get_backup_summary_for_report(
            period_hours=16,
            include_mail=include_mail,
        )  # РЎ 18:00 РїСЂРµРґС‹РґСѓС‰РµРіРѕ РґРЅСЏ

    message += f"\nрџ’ѕ *РЎС‚Р°С‚СѓСЃ Р±СЌРєР°РїРѕРІ ({'Р·Р° РїРѕСЃР»РµРґРЅРёРµ 24С‡' if is_manual else 'Р·Р° РїРѕСЃР»РµРґРЅРёРµ 16С‡'})*\n"
    message += backup_data

    if down_count > 0:
        message += f"\nвљ пёЏ *РџСЂРѕР±Р»РµРјРЅС‹Рµ СЃРµСЂРІРµСЂС‹ ({down_count}):*\n"

        # Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ С‚РёРїСѓ РґР»СЏ СѓРґРѕР±СЃС‚РІР° С‡С‚РµРЅРёСЏ
        by_type = {}
        for server in status["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
            for s in servers_list:
                message += f"вЂў {s['name']} ({s['ip']})\n"

    else:
        message += f"\nвњ… *Р’СЃРµ СЃРµСЂРІРµСЂС‹ РґРѕСЃС‚СѓРїРЅС‹!*\n"

    message += f"\nрџ“‹ *РЎС‚Р°С‚РёСЃС‚РёРєР° РїРѕ С‚РёРїР°Рј:*\n"

    # РЎС‚Р°С‚РёСЃС‚РёРєР° РїРѕ С‚РёРїР°Рј СЃРµСЂРІРµСЂРѕРІ
    type_stats = {}
    all_servers = status["ok"] + status["failed"]
    for server in all_servers:
        if server["type"] not in type_stats:
            type_stats[server["type"]] = {"total": 0, "up": 0}
        type_stats[server["type"]]["total"] += 1

    for server in status["ok"]:
        type_stats[server["type"]]["up"] += 1

    for server_type, stats in type_stats.items():
        up_percent = (stats["up"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        message += f"вЂў {server_type.upper()}: {stats['up']}/{stats['total']} ({up_percent:.1f}%)\n"

    if is_manual:
        message += f"\nвЏ° *РћС‚С‡РµС‚ СЃС„РѕСЂРјРёСЂРѕРІР°РЅ:* {datetime.now().strftime('%H:%M:%S')}"
    else:
        message += f"\nвЏ° *РћС‚С‡РµС‚ РѕС‚РїСЂР°РІР»РµРЅ:* {datetime.now().strftime('%H:%M:%S')}"

    # РћС‚РїСЂР°РІР»СЏРµРј РѕС‚С‡РµС‚ РїСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ, РґР°Р¶Рµ РІ С‚РёС…РѕРј СЂРµР¶РёРјРµ
    send_alert(message, force=True)
    debug_log(f"вњ… {report_type} РѕС‚РїСЂР°РІР»РµРЅ: {up_count}/{total_servers} РґРѕСЃС‚СѓРїРЅРѕ")

def get_backup_summary_for_report(period_hours=16, include_mail=False):
    """РџРѕР»СѓС‡Р°РµС‚ СЃРІРѕРґРєСѓ РїРѕ Р±СЌРєР°РїР°Рј Р·Р° СѓРєР°Р·Р°РЅРЅС‹Р№ РїРµСЂРёРѕРґ

    Args:
        period_hours (int): РљРѕР»РёС‡РµСЃС‚РІРѕ С‡Р°СЃРѕРІ РґР»СЏ РїРµСЂРёРѕРґР° (16 РґР»СЏ Р°РІС‚Рѕ-РѕС‚С‡РµС‚Р°, 24 РґР»СЏ СЂСѓС‡РЅРѕРіРѕ)
        include_mail (bool): Р”РѕР±Р°РІР»СЏС‚СЊ Р»Рё Р±СЌРєР°РїС‹ РїРѕС‡С‚РѕРІРѕРіРѕ СЃРµСЂРІРµСЂР°
    """
    try:
        debug_log(f"рџ”„ РЎР±РѕСЂ РґР°РЅРЅС‹С… Рѕ Р±СЌРєР°РїР°С… Р·Р° {period_hours} С‡Р°СЃРѕРІ...")

        # Р”РРђР“РќРћРЎРўРРљРђ РљРћРќР¤РР“РЈР РђР¦РР
        debug_proxmox_config()

        import sqlite3
        from datetime import datetime, timedelta

        db_path = DATA_DIR / "backups.db"

        if not db_path.exists():
            debug_log(f"вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… РЅРµ РЅР°Р№РґРµРЅР°: {db_path}")
            return "вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р±СЌРєР°РїРѕРІ РЅРµРґРѕСЃС‚СѓРїРЅР°\n"

        since_time = (datetime.now() - timedelta(hours=period_hours)).strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Р”Р•РўРђР›Р¬РќРђРЇ Р”РРђР“РќРћРЎРўРРљРђ: РєР°РєРёРµ С…РѕСЃС‚С‹ РµСЃС‚СЊ РІ Р±Р°Р·Рµ
        cursor.execute('''
            SELECT DISTINCT host_name, COUNT(*) as backup_count,
                   MAX(received_at) as last_backup,
                   SUM(CASE WHEN backup_status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM proxmox_backups
            WHERE received_at >= datetime('now', '-7 days')
            GROUP BY host_name
            ORDER BY last_backup DESC
        ''')
        all_hosts_from_db = cursor.fetchall()

        debug_log("рџ“Љ Р”РРђР“РќРћРЎРўРРљРђ - Р’СЃРµ С…РѕСЃС‚С‹ РёР· Р‘Р” Р·Р° 7 РґРЅРµР№:")
        for host_name, count, last_backup, success_count in all_hosts_from_db:
            debug_log(f"  - {host_name}: {success_count}/{count} СѓСЃРїРµС€РЅРѕ, РїРѕСЃР»РµРґРЅРёР№: {last_backup}")

        # 1. Proxmox Р±СЌРєР°РїС‹ - СЃС‡РёС‚Р°РµРј РџРћРЎР›Р•Р”РќРР• Р±СЌРєР°РїС‹ РґР»СЏ РєР°Р¶РґРѕРіРѕ С…РѕСЃС‚Р°
        cursor.execute('''
            SELECT host_name, backup_status, MAX(received_at) as last_backup
            FROM proxmox_backups
            WHERE received_at >= ?
            GROUP BY host_name
        ''', (since_time,))

        proxmox_results = cursor.fetchall()

        debug_log("рџ“Љ Р”РРђР“РќРћРЎРўРРљРђ - РҐРѕСЃС‚С‹ СЃ Р±СЌРєР°РїР°РјРё Р·Р° СѓРєР°Р·Р°РЅРЅС‹Р№ РїРµСЂРёРѕРґ:")
        for host_name, status, last_backup in proxmox_results:
            debug_log(f"  - {host_name}: {status}, РїРѕСЃР»РµРґРЅРёР№: {last_backup}")

        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ С…РѕСЃС‚С‹ РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё
        from config.db_settings import PROXMOX_HOSTS

        def is_proxmox_host_enabled(host_value):
            """РџСЂРѕРІРµСЂСЏРµС‚, РІРєР»СЋС‡РµРЅ Р»Рё РјРѕРЅРёС‚РѕСЂРёРЅРі С…РѕСЃС‚Р° Proxmox."""
            if isinstance(host_value, dict):
                return host_value.get("enabled", True)
            return True

        enabled_hosts = [
            host for host, value in PROXMOX_HOSTS.items()
            if is_proxmox_host_enabled(value)
        ]

        debug_log("рџ“Љ Р”РРђР“РќРћРЎРўРРљРђ - РҐРѕСЃС‚С‹ РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё PROXMOX_HOSTS:")
        for host in enabled_hosts:
            debug_log(f"  - {host}")

        # РћРїСЂРµРґРµР»СЏРµРј Р°РєС‚РёРІРЅС‹Рµ С…РѕСЃС‚С‹
        active_host_names = [row[0] for row in all_hosts_from_db]
        all_hosts = [host for host in enabled_hosts if host in active_host_names]

        # Р•СЃР»Рё РІСЃРµ РµС‰Рµ РЅРµ 15, РёСЃРїРѕР»СЊР·СѓРµРј Р°Р»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РјРµС‚РѕРґ
        if len(all_hosts) != 15:
            debug_log(f"вљ пёЏ  РќР°Р№РґРµРЅРѕ {len(all_hosts)} Р°РєС‚РёРІРЅС‹С… С…РѕСЃС‚РѕРІ, РѕР¶РёРґР°Р»РѕСЃСЊ 15")
            debug_log("рџ”Ќ РџСЂРѕР±СѓРµРј Р°Р»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РјРµС‚РѕРґ РїРѕРґСЃС‡РµС‚Р°...")

            # РњРµС‚РѕРґ 2: Р±РµСЂРµРј РІСЃРµ СѓРЅРёРєР°Р»СЊРЅС‹Рµ С…РѕСЃС‚С‹ РёР· Р‘Р” Р·Р° 30 РґРЅРµР№
            cursor.execute('''
                SELECT DISTINCT host_name
                FROM proxmox_backups
                WHERE received_at >= datetime('now', '-30 days')
                ORDER BY host_name
            ''')
            all_unique_hosts = [row[0] for row in cursor.fetchall()]

            debug_log("рџ“Љ Р”РРђР“РќРћРЎРўРРљРђ - Р’СЃРµ СѓРЅРёРєР°Р»СЊРЅС‹Рµ С…РѕСЃС‚С‹ Р·Р° 30 РґРЅРµР№:")
            for host in all_unique_hosts:
                debug_log(f"  - {host}")

            all_hosts = all_unique_hosts

        debug_log(f"вњ… РС‚РѕРіРѕРІС‹Р№ СЃРїРёСЃРѕРє С…РѕСЃС‚РѕРІ: {len(all_hosts)} - {all_hosts}")

        # РЎС‡РёС‚Р°РµРј СѓСЃРїРµС€РЅС‹Рµ - Р’РЎР• С…РѕСЃС‚С‹ Сѓ РєРѕС‚РѕСЂС‹С… РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї СѓСЃРїРµС€РЅС‹Р№
        hosts_with_success = len([r for r in proxmox_results if r[1] == 'success'])

        debug_log(f"рџ“Љ Proxmox РёС‚РѕРі: {hosts_with_success}/{len(all_hosts)} СѓСЃРїРµС€РЅРѕ")

        # 2. Р‘Р°Р·С‹ РґР°РЅРЅС‹С… - РРЎРџР РђР’Р›Р•РќРќРђРЇ Р›РћР“РРљРђ: РёС‰РµРј РџРћРЎР›Р•Р”РќРР™ Р±СЌРєР°Рї РґР»СЏ РєР°Р¶РґРѕР№ Р±Р°Р·С‹
        cursor.execute('''
            SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
            FROM database_backups
            WHERE received_at >= ?
            GROUP BY backup_type, database_name
        ''', (since_time,))

        db_results = cursor.fetchall()

        # РџРѕР»СѓС‡Р°РµРј РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ
        from config.db_settings import DATABASE_BACKUP_CONFIG

        config_databases = {
            'company_database': DATABASE_BACKUP_CONFIG.get("company_databases", {}),
            'barnaul': DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
            'client': DATABASE_BACKUP_CONFIG.get("client_databases", {}),
            'yandex': DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
        }

        # РЎС‡РёС‚Р°РµРј СЃС‚Р°С‚РёСЃС‚РёРєСѓ - РљРђР–Р”РђРЇ Р±Р°Р·Р° СЃС‡РёС‚Р°РµС‚СЃСЏ СѓСЃРїРµС€РЅРѕР№ РµСЃР»Рё Сѓ РЅРµРµ РµСЃС‚СЊ СѓСЃРїРµС€РЅС‹Р№ Р±СЌРєР°Рї Р·Р° РїРµСЂРёРѕРґ
        db_stats = {}
        for category, databases in config_databases.items():
            total_in_config = len(databases)
            if total_in_config > 0:
                successful_count = 0

                # Р”Р»СЏ РєР°Р¶РґРѕР№ Р±Р°Р·С‹ РІ РєР°С‚РµРіРѕСЂРёРё РїСЂРѕРІРµСЂСЏРµРј РµСЃС‚СЊ Р»Рё СѓСЃРїРµС€РЅС‹Р№ Р±СЌРєР°Рї
                for db_key in databases.keys():
                    found_success = False
                    for backup_type, db_name, status, last_backup in db_results:
                        if backup_type == category and db_name == db_key and status == 'success':
                            found_success = True
                            break

                    if found_success:
                        successful_count += 1

                db_stats[category] = {
                    'total': total_in_config,
                    'successful': successful_count
                }
                debug_log(f"рџ“Љ {category}: {successful_count}/{total_in_config} СѓСЃРїРµС€РЅРѕ")

        # 3. РЈСЃС‚Р°СЂРµРІС€РёРµ Р±СЌРєР°РїС‹ (Р±РѕР»РµРµ 24 С‡Р°СЃРѕРІ) - РџР РђР’РР›Р¬РќР«Р™ РїРѕРґСЃС‡РµС‚
        stale_threshold = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        # РЈСЃС‚Р°СЂРµРІС€РёРµ С…РѕСЃС‚С‹ - С‚Рµ Сѓ РєРѕС‚РѕСЂС‹С… РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї СЃС‚Р°СЂС€Рµ 24 С‡Р°СЃРѕРІ
        cursor.execute('''
            SELECT host_name, MAX(received_at) as last_backup
            FROM proxmox_backups
            GROUP BY host_name
            HAVING last_backup < ?
        ''', (stale_threshold,))
        stale_hosts = cursor.fetchall()

        # РЈСЃС‚Р°СЂРµРІС€РёРµ Р‘Р” - С‚Рµ Сѓ РєРѕС‚РѕСЂС‹С… РїРѕСЃР»РµРґРЅРёР№ Р±СЌРєР°Рї СЃС‚Р°СЂС€Рµ 24 С‡Р°СЃРѕРІ
        cursor.execute('''
            SELECT backup_type, database_name, MAX(received_at) as last_backup
            FROM database_backups
            GROUP BY backup_type, database_name
            HAVING last_backup < ?
        ''', (stale_threshold,))
        stale_databases = cursor.fetchall()

        mail_recent = None
        mail_latest = None
        try:
            cursor.execute(
                '''
                SELECT backup_status, total_size, backup_path, received_at
                FROM mail_server_backups
                WHERE received_at >= ?
                ORDER BY received_at DESC
                LIMIT 1
            ''',
                (since_time,),
            )
            mail_recent = cursor.fetchone()

            cursor.execute(
                '''
                SELECT backup_status, total_size, backup_path, received_at
                FROM mail_server_backups
                ORDER BY received_at DESC
                LIMIT 1
            '''
            )
            mail_latest = cursor.fetchone()
        except Exception as exc:
            if "no such table: mail_server_backups" in str(exc):
                mail_latest = None
            else:
                raise

        conn.close()

        # Р¤РѕСЂРјРёСЂСѓРµРј СЃРѕРѕР±С‰РµРЅРёРµ
        message = ""

        # Proxmox Р±СЌРєР°РїС‹
        if len(all_hosts) > 0:
            success_rate = (hosts_with_success / len(all_hosts)) * 100
            message += f"вЂў Proxmox: {hosts_with_success}/{len(all_hosts)} СѓСЃРїРµС€РЅРѕ ({success_rate:.1f}%)"

            if stale_hosts:
                message += f" вљ пёЏ {len(stale_hosts)} С…РѕСЃС‚РѕРІ Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡"
            message += "\n"

        # Р‘Р°Р·С‹ РґР°РЅРЅС‹С…
        message += "вЂў Р‘Р°Р·С‹ РґР°РЅРЅС‹С…:\n"

        category_names = {
            'company_database': 'РћСЃРЅРѕРІРЅС‹Рµ',
            'barnaul': 'Р‘Р°СЂРЅР°СѓР»',
            'client': 'РљР»РёРµРЅС‚С‹',
            'yandex': 'Yandex'
        }

        for category in ['company_database', 'barnaul', 'client', 'yandex']:
            if category in db_stats and db_stats[category]['total'] > 0:
                stats = db_stats[category]
                type_name = category_names[category]

                success_rate = (stats['successful'] / stats['total']) * 100
                message += f"  - {type_name}: {stats['successful']}/{stats['total']} СѓСЃРїРµС€РЅРѕ ({success_rate:.1f}%)"

                # РЈСЃС‚Р°СЂРµРІС€РёРµ РґР»СЏ СЌС‚РѕРіРѕ С‚РёРїР°
                stale_count = len([db for db in stale_databases if db[0] == category])
                if stale_count > 0:
                    message += f" вљ пёЏ {stale_count} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡"
                message += "\n"

        if include_mail:
            try:
                def _mail_time_ago(received_at):
                    if not received_at:
                        return "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                    try:
                        last_time = datetime.strptime(received_at, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        return "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                    hours_ago = int((datetime.now() - last_time).total_seconds() / 3600)
                    if hours_ago >= 24:
                        days = hours_ago // 24
                        hours = hours_ago % 24
                        return f"{days}Рґ {hours}С‡ РЅР°Р·Р°Рґ"
                    return f"{hours_ago}С‡ РЅР°Р·Р°Рґ"

                if not mail_latest:
                    message += "вЂў РџРѕС‡С‚Р°: РЅРµС‚ РґР°РЅРЅС‹С…\n"
                else:
                    _, size, path, received_at = mail_latest
                    size_text = size or "РЅРµРёР·РІРµСЃС‚РЅРѕ"
                    path_text = path or "Р±РµР· РїСѓС‚Рё"
                    time_ago = _mail_time_ago(received_at)
                    if mail_recent:
                        message += f"вЂў РџРѕС‡С‚Р°: {size_text} {path_text} ({time_ago})\n"
                    else:
                        message += (
                            f"вЂў РџРѕС‡С‚Р°: РЅРµС‚ СЃРІРµР¶РёС… Р±СЌРєР°РїРѕРІ "
                            f"(>{period_hours}С‡), РїРѕСЃР»РµРґРЅРёР№: {size_text} "
                            f"{path_text} ({time_ago})\n"
                        )
            except Exception as exc:
                debug_log(f"вљ пёЏ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РґР°РЅРЅС‹С… Рѕ Р±СЌРєР°РїР°С… РїРѕС‡С‚С‹: {exc}")

        # РћР±С‰РёРµ РїСЂРѕР±Р»РµРјС‹
        total_stale = len(stale_hosts) + len(stale_databases)
        if total_stale > 0:
            message += f"\nрџљЁ Р’РЅРёРјР°РЅРёРµ: {total_stale} РїСЂРѕР±Р»РµРј:\n"
            if stale_hosts:
                message += f"вЂў {len(stale_hosts)} С…РѕСЃС‚РѕРІ Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡\n"
            if stale_databases:
                message += f"вЂў {len(stale_databases)} Р‘Р” Р±РµР· Р±СЌРєР°РїРѕРІ >24С‡\n"

        return message

    except Exception as e:
        debug_log(f"рџ’Ґ РљСЂРёС‚РёС‡РµСЃРєР°СЏ РѕС€РёР±РєР° РІ get_backup_summary_for_report: {e}")
        import traceback
        debug_log(f"рџ’Ґ Traceback: {traceback.format_exc()}")
        return "вќЊ РћС€РёР±РєР° С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡РµС‚Р° Рѕ Р±СЌРєР°РїР°С…\n"

def debug_backup_data():
    """Р’СЂРµРјРµРЅРЅР°СЏ С„СѓРЅРєС†РёСЏ РґР»СЏ РѕС‚Р»Р°РґРєРё РґР°РЅРЅС‹С… Р±СЌРєР°РїРѕРІ"""
    try:
        import sqlite3
        from datetime import datetime, timedelta

        db_path = DATA_DIR / "backups.db"

        if not db_path.exists():
            debug_log("вќЊ Р‘Р°Р·Р° РґР°РЅРЅС‹С… backups.db РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚!")
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # РџСЂРѕРІРµСЂСЏРµРј С‚Р°Р±Р»РёС†С‹
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        debug_log(f"рџ“‹ РўР°Р±Р»РёС†С‹ РІ Р±Р°Р·Рµ: {[t[0] for t in tables]}")

        # Р”Р°РЅРЅС‹Рµ РёР· proxmox_backups
        cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT host_name) as hosts FROM proxmox_backups WHERE received_at >= datetime('now', '-16 hours')")
        proxmox_stats = cursor.fetchone()
        debug_log(f"рџ“Љ Proxmox Р·Р°РїРёСЃРё: {proxmox_stats[0]}, С…РѕСЃС‚РѕРІ: {proxmox_stats[1]}")

        # Р”Р°РЅРЅС‹Рµ РёР· database_backups
        cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT database_name) as dbs FROM database_backups WHERE received_at >= datetime('now', '-16 hours')")
        db_stats = cursor.fetchone()
        debug_log(f"рџ“Љ DB Р·Р°РїРёСЃРё: {db_stats[0]}, Р±Р°Р·: {db_stats[1]}")

        # РљРѕРЅРєСЂРµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРѕ С‚РёРїР°Рј Р‘Р”
        cursor.execute('''
            SELECT backup_type, COUNT(DISTINCT database_name) as dbs_count
            FROM database_backups
            WHERE received_at >= datetime('now', '-16 hours')
            GROUP BY backup_type
        ''')
        db_by_type = cursor.fetchall()
        debug_log(f"рџ“Љ Р‘Р” РїРѕ С‚РёРїР°Рј: {dict(db_by_type)}")

        conn.close()

    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РґРёР°РіРЅРѕСЃС‚РёРєРё: {e}")

def debug_morning_report(update, context):
    """РћС‚Р»Р°РґРѕС‡РЅР°СЏ С„СѓРЅРєС†РёСЏ РґР»СЏ РїСЂРѕРІРµСЂРєРё СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°"""
    query = update.callback_query
    query.answer()

    debug_log("рџ”§ Р—Р°РїСѓС‰РµРЅР° РѕС‚Р»Р°РґРѕС‡РЅР°СЏ С„СѓРЅРєС†РёСЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°")

    # РЎРѕР±РёСЂР°РµРј С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ
    current_status = get_current_server_status()

    message = f"рџ”§ *РћС‚Р»Р°РґРѕС‡РЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°*\n\n"
    message += f"рџџў Р”РѕСЃС‚СѓРїРЅРѕ: {len(current_status['ok'])}\n"
    message += f"рџ”ґ РќРµРґРѕСЃС‚СѓРїРЅРѕ: {len(current_status['failed'])}\n"
    message += f"вЏ° Р’СЂРµРјСЏ: {datetime.now().strftime('%H:%M:%S')}\n\n"

    # РџСЂРѕРІРµСЂСЏРµРј РґР°РЅРЅС‹Рµ РґР»СЏ РѕС‚С‡РµС‚Р°
    if morning_data and "status" in morning_data:
        morning_status = morning_data["status"]
        message += f"рџ“Љ *Р”Р°РЅРЅС‹Рµ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°:*\n"
        message += f"вЂў Р’СЂРµРјСЏ СЃР±РѕСЂР°: {morning_data.get('collection_time', 'РЅРµРёР·РІРµСЃС‚РЅРѕ')}\n"
        message += f"вЂў Р”РѕСЃС‚СѓРїРЅРѕ: {len(morning_status['ok'])}\n"
        message += f"вЂў РќРµРґРѕСЃС‚СѓРїРЅРѕ: {len(morning_status['failed'])}\n"
    else:
        message += f"вќЊ *Р”Р°РЅРЅС‹Рµ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р° РѕС‚СЃСѓС‚СЃС‚РІСѓСЋС‚*\n"

    query.edit_message_text(message, parse_mode='Markdown')

def resource_history_command(update, context):
    """РџРѕРєР°Р·С‹РІР°РµС‚ РёСЃС‚РѕСЂРёСЋ СЂРµСЃСѓСЂСЃРѕРІ"""
    query = update.callback_query
    query.answer()

    message = "рџ“€ *РСЃС‚РѕСЂРёСЏ СЂРµСЃСѓСЂСЃРѕРІ*\n\n"

    if not resource_history:
        message += "РСЃС‚РѕСЂРёСЏ СЂРµСЃСѓСЂСЃРѕРІ РїСѓСЃС‚Р°\n"
    else:
        for ip, history in list(resource_history.items())[:5]:  # РџРѕРєР°Р·С‹РІР°РµРј РїРµСЂРІС‹Рµ 5 СЃРµСЂРІРµСЂРѕРІ
            server_name = history[0]["server_name"] if history else "РќРµРёР·РІРµСЃС‚РЅРѕ"
            message += f"**{server_name}** ({ip}):\n"

            for entry in history[-3:]:  # РџРѕСЃР»РµРґРЅРёРµ 3 Р·Р°РїРёСЃРё
                message += f"вЂў {entry['timestamp'].strftime('%H:%M')}: CPU {entry['cpu']}%, RAM {entry['ram']}%, Disk {entry['disk']}%\n"
            message += "\n"

    query.edit_message_text(message, parse_mode='Markdown')

def resource_page_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РїРѕСЃС‚СЂР°РЅРёС‡РЅРѕРіРѕ РїСЂРѕСЃРјРѕС‚СЂР° СЂРµСЃСѓСЂСЃРѕРІ"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("рџ“„ РџРѕСЃС‚СЂР°РЅРёС‡РЅС‹Р№ РїСЂРѕСЃРјРѕС‚СЂ СЂРµСЃСѓСЂСЃРѕРІ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ")

def refresh_resources_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РѕР±РЅРѕРІР»РµРЅРёСЏ СЂРµСЃСѓСЂСЃРѕРІ"""
    query = update.callback_query
    query.answer("рџ”„ РћР±РЅРѕРІР»СЏРµРј СЂРµСЃСѓСЂСЃС‹...")
    check_resources_handler(update, context)

def close_resources_handler(update, context):
    """Р—Р°РєСЂС‹РІР°РµС‚ РјРµРЅСЋ СЂРµСЃСѓСЂСЃРѕРІ"""
    query = update.callback_query
    query.answer()
    query.delete_message()

def debug_proxmox_config():
    """Р’СЂРµРјРµРЅРЅР°СЏ С„СѓРЅРєС†РёСЏ РґР»СЏ РґРёР°РіРЅРѕСЃС‚РёРєРё РєРѕРЅС„РёРіСѓСЂР°С†РёРё Proxmox"""
    try:
        from config.db_settings import PROXMOX_HOSTS
        debug_log("=== Р”РРђР“РќРћРЎРўРРљРђ KONР¤РР“РЈР РђР¦РР PROXMOX ===")
        enabled_hosts = [
            host for host, value in PROXMOX_HOSTS.items()
            if not isinstance(value, dict) or value.get("enabled", True)
        ]
        debug_log(f"Р’СЃРµРіРѕ С…РѕСЃС‚РѕРІ РІ PROXMOX_HOSTS: {len(enabled_hosts)}")
        for i, host in enumerate(enabled_hosts, 1):
            debug_log(f"{i}. {host}")
        debug_log("=======================================")
    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РґРёР°РіРЅРѕСЃС‚РёРєРё РєРѕРЅС„РёРіСѓСЂР°С†РёРё: {e}")
