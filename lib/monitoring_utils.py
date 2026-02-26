"""
/lib/monitoring_utils.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utilities: diagnostics, reports, statistics
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РЈС‚РёР»РёС‚С‹: РґРёР°РіРЅРѕСЃС‚РёРєР°, РѕС‚С‡РµС‚С‹, СЃС‚Р°С‚РёСЃС‚РёРєР°
"""

import json
from datetime import datetime, timedelta
from config.settings import PROC_UPTIME_FILE, STATS_FILE, DATA_DIR

# === Р”РРђР“РќРћРЎРўРРљРђ SSH (РёР· single_check.py) ===

def diagnose_ssh_command(update, context):
    """Р”РёР°РіРЅРѕСЃС‚РёРєР° SSH РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє РєРѕРЅРєСЂРµС‚РЅРѕРјСѓ СЃРµСЂРІРµСЂСѓ"""
    if not context.args:
        update.message.reply_text("вќЊ РЈРєР°Р¶РёС‚Рµ IP РёР»Рё РёРјСЏ СЃРµСЂРІРµСЂР°: /diagnose_ssh <ip>")
        return

    target = context.args[0]
    
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()
    server = None

    # РС‰РµРј СЃРµСЂРІРµСЂ РїРѕ IP РёР»Рё РёРјРµРЅРё
    for s in servers:
        if s["ip"] == target or s["name"] == target:
            server = s
            break

    if not server:
        update.message.reply_text(f"вќЊ РЎРµСЂРІРµСЂ {target} РЅРµ РЅР°Р№РґРµРЅ РІ СЃРїРёСЃРєРµ РјРѕРЅРёС‚РѕСЂРёРЅРіР°")
        return

    message = f"рџ”§ *Р”РёР°РіРЅРѕСЃС‚РёРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ РґР»СЏ {server['name']} ({server['ip']})*:\n\n"

    try:
        # РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РїРѕСЂС‚Р°
        port = 22
        from core.monitor_core import check_port
        is_port_open = check_port(server["ip"], port, timeout=10)
        message += f"РџРѕСЂС‚ {port} (SSH): {'рџџў РћС‚РєСЂС‹С‚' if is_port_open else 'рџ”ґ Р—Р°РєСЂС‹С‚'}\n"

        if is_port_open:
            # РџСЂРѕРІРµСЂРєР° SSH РїРѕРґРєР»СЋС‡РµРЅРёСЏ
            from core.monitor_core import check_ssh, check_ssh_alternative
            
            message += "\n*РџСЂРѕРІРµСЂРєР° Paramiko (РѕСЃРЅРѕРІРЅРѕР№ РјРµС‚РѕРґ):*\n"
            result1 = check_ssh(server["ip"])
            message += f"- Р РµР·СѓР»СЊС‚Р°С‚: {'рџџў РЈСЃРїРµС€РЅРѕ' if result1 else 'рџ”ґ РћС€РёР±РєР°'}\n"
            
            message += "\n*РџСЂРѕРІРµСЂРєР° СЃРёСЃС‚РµРјРЅС‹Рј SSH (Р°Р»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РјРµС‚РѕРґ):*\n"
            result2 = check_ssh_alternative(server["ip"])
            message += f"- Р РµР·СѓР»СЊС‚Р°С‚: {'рџџў РЈСЃРїРµС€РЅРѕ' if result2 else 'рџ”ґ РћС€РёР±РєР°'}\n"
            
            if not result1 and not result2:
                message += "\nрџ’Ў *Р РµРєРѕРјРµРЅРґР°С†РёРё:*\n"
                message += "- РџСЂРѕРІРµСЂСЊС‚Рµ РїСЂР°РІРёР»СЊРЅРѕСЃС‚СЊ SSH РєР»СЋС‡Р°\n"
                message += "- РЈР±РµРґРёС‚РµСЃСЊ, С‡С‚Рѕ РєР»СЋС‡ РґРѕР±Р°РІР»РµРЅ РІ authorized_keys РЅР° СЃРµСЂРІРµСЂРµ\n"
                message += "- РџСЂРѕРІРµСЂСЊС‚Рµ РЅР°СЃС‚СЂРѕР№РєРё SSH РґРµРјРѕРЅР° РЅР° С†РµР»РµРІРѕРј СЃРµСЂРІРµСЂРµ\n"
            elif result2 and not result1:
                message += "\nвљ пёЏ *РџСЂРѕР±Р»РµРјР° СЃ Paramiko, РЅРѕ СЃРёСЃС‚РµРјРЅС‹Р№ SSH СЂР°Р±РѕС‚Р°РµС‚*\n"
                message += "Р­С‚Рѕ РёР·РІРµСЃС‚РЅР°СЏ РїСЂРѕР±Р»РµРјР° СЃРѕРІРјРµСЃС‚РёРјРѕСЃС‚Рё. РСЃРїРѕР»СЊР·СѓРµРј РѕР±С…РѕРґРЅС‹Рµ РїСѓС‚Рё.\n"
            else:
                message += "\nвњ… РћР±Р° РјРµС‚РѕРґР° СЂР°Р±РѕС‚Р°СЋС‚ РєРѕСЂСЂРµРєС‚РЅРѕ\n"

        else:
            message += "\nвќЊ *РџРѕСЂС‚ SSH Р·Р°РєСЂС‹С‚* - СЃРµСЂРІРµСЂ РЅРµРґРѕСЃС‚СѓРїРµРЅ\n"

    except Exception as e:
        message += f"\nрџ’Ґ *РћС€РёР±РєР° РґРёР°РіРЅРѕСЃС‚РёРєРё:* {str(e)}\n"

    update.message.reply_text(message, parse_mode='Markdown')

def diagnose_menu_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РјРµРЅСЋ РґРёР°РіРЅРѕСЃС‚РёРєРё"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("рџ”§ РњРµРЅСЋ РґРёР°РіРЅРѕСЃС‚РёРєРё Р±СѓРґРµС‚ РґРѕСЃС‚СѓРїРЅРѕ РїРѕСЃР»Рµ РїРѕР»РЅРѕР№ РЅР°СЃС‚СЂРѕР№РєРё")

# === РЎРўРђРўРРЎРўРРљРђ (РёР· stats_collector.py) ===

def save_monitoring_stats():
    """РЎРѕС…СЂР°РЅСЏРµС‚ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    try:
        stats_data = {
            "last_updated": datetime.now().isoformat(),
            "uptime": get_system_uptime(),
            "daily_stats": get_daily_stats()
        }
        
        # РЎРѕР·РґР°РµРј РґРёСЂРµРєС‚РѕСЂРёСЋ РµСЃР»Рё РЅРµ СЃСѓС‰РµСЃС‚РІСѓРµС‚
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATS_FILE.write_text(
            json.dumps(stats_data, indent=2),
            encoding="utf-8",
        )
            
    except Exception as e:
        print(f"вќЊ РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё: {e}")

def get_system_uptime():
    """РџРѕР»СѓС‡Р°РµС‚ РІСЂРµРјСЏ СЂР°Р±РѕС‚С‹ СЃРёСЃС‚РµРјС‹"""
    try:
        # Р”Р»СЏ Linux СЃРёСЃС‚РµРј
        uptime_seconds = float(PROC_UPTIME_FILE.read_text(encoding="utf-8").split()[0])
            
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    except:
        return "РќРµРёР·РІРµСЃС‚РЅРѕ"

def get_daily_stats():
    """РџРѕР»СѓС‡Р°РµС‚ РґРЅРµРІРЅСѓСЋ СЃС‚Р°С‚РёСЃС‚РёРєСѓ"""
    # Р—РґРµСЃСЊ РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ Р»РѕРіРёРєСѓ СЃР±РѕСЂР° РґРЅРµРІРЅРѕР№ СЃС‚Р°С‚РёСЃС‚РёРєРё
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "checks_performed": 0,
        "alerts_sent": 0
    }

# === РћРўР§Р•РўР« (РёР· reports.py) ===

def generate_daily_report():
    """Р“РµРЅРµСЂРёСЂСѓРµС‚ РµР¶РµРґРЅРµРІРЅС‹Р№ РѕС‚С‡РµС‚"""
    # Р—Р°РіР»СѓС€РєР° - СЂРµР°Р»РёР·РѕРІР°С‚СЊ Р»РѕРіРёРєСѓ РѕС‚С‡РµС‚РѕРІ
    return "рџ“Љ Р•Р¶РµРґРЅРµРІРЅС‹Р№ РѕС‚С‡РµС‚ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ"

def get_backup_stats():
    """РЎС‚Р°С‚РёСЃС‚РёРєР° РїРѕ Р±СЌРєР°РїР°Рј РґР»СЏ РѕС‚С‡РµС‚РѕРІ"""
    # Р—Р°РіР»СѓС€РєР° - СЂРµР°Р»РёР·РѕРІР°С‚СЊ Р»РѕРіРёРєСѓ
    return {"total": 0, "successful": 0, "failed": 0}

# === РћР‘Р РђР‘РћРўР§РРљР Р”Р›РЇ BOT_MENU ===

def stats_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /stats"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    stats = get_daily_stats()
    uptime = get_system_uptime()
    
    message = (
        f"рџ“Љ *РЎС‚Р°С‚РёСЃС‚РёРєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР°*\n\n"
        f"вЂў Р”Р°С‚Р°: {stats['date']}\n"
        f"вЂў РџСЂРѕРІРµСЂРѕРє РІС‹РїРѕР»РЅРµРЅРѕ: {stats['checks_performed']}\n"
        f"вЂў РЈРІРµРґРѕРјР»РµРЅРёР№ РѕС‚РїСЂР°РІР»РµРЅРѕ: {stats['alerts_sent']}\n"
        f"вЂў РђРїС‚Р°Р№Рј СЃРёСЃС‚РµРјС‹: {uptime}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("рџ”„ РћР±РЅРѕРІРёС‚СЊ", callback_data='stats_refresh')],
        [InlineKeyboardButton("рџ“Љ РЎС‚Р°С‚СѓСЃ РјРѕРЅРёС‚РѕСЂРёРЅРіР°", callback_data='monitor_status')],
        [InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close')]
    ]
    
    if hasattr(update, 'callback_query'):
        update.callback_query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
