"""
/extensions/server_checks/__init__.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified server checks: resources, availability, list
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РЈРЅРёС„РёС†РёСЂРѕРІР°РЅРЅС‹Рµ РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ: СЂРµСЃСѓСЂСЃС‹, РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ, СЃРїРёСЃРѕРє
"""

import re
import subprocess
import socket
from datetime import datetime
import sys
import os
from lib.network import check_port as net_check_port, check_ping as net_check_ping
from config.settings import BASE_DIR
from config.db_settings import (
    RDP_SERVERS,
    SSH_SERVERS,
    PING_SERVERS,
    SSH_KEY_PATH,
    SSH_USERNAME,
    RESOURCE_THRESHOLDS,
    WINDOWS_SERVER_CREDENTIALS,
    WINRM_CONFIGS,
    SERVER_CONFIG,
    get_servers_config,
)
from core.checker import ServerChecker
from lib.logging import debug_log
sys.path.insert(0, str(BASE_DIR))

# Р›РѕРєР°Р»СЊРЅС‹Р№ СЌРєР·РµРјРїР»СЏСЂ РїСЂРѕРІРµСЂСЏСЋС‰РµРіРѕ
_server_checker = ServerChecker()

# === РЎРџРРЎРћРљ РЎР•Р Р’Р•Р РћР’ ===

def initialize_servers():
    """РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ РёР· РєРѕРЅС„РёРіСѓСЂР°С†РёРё"""
    servers = []
    servers_config = get_servers_config()
    if not any(servers_config.values()):
        servers_config = SERVER_CONFIG
        if not any(servers_config.values()):
            debug_log("вљ пёЏ РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ СЃРµСЂРІРµСЂРѕРІ РїСѓСЃС‚Р°")
    
    # Windows RDP СЃРµСЂРІРµСЂС‹
    for ip, name in servers_config.get("windows_servers", {}).items():
        servers.append({
            "ip": ip,
            "name": name,
            "type": "rdp"
        })
    
    # Linux SSH СЃРµСЂРІРµСЂС‹
    for ip, name in servers_config.get("linux_servers", {}).items():
        servers.append({
            "ip": ip,
            "name": name,
            "type": "ssh"
        })
    
    # Ping-only СЃРµСЂРІРµСЂС‹
    for ip, name in servers_config.get("ping_servers", {}).items():
        servers.append({
            "ip": ip,
            "name": name,
            "type": "ping"
        })
    
    return servers

def resolve_hostname(ip):
    """Р Р°Р·СЂРµС€Р°РµС‚ IP РІ hostname"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except:
        return ip

def get_server_by_ip(ip):
    """РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂ РїРѕ IP"""
    servers = initialize_servers()
    for server in servers:
        if server["ip"] == ip:
            return server
    return None

def get_server_by_name(name):
    """РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂ РїРѕ РёРјРµРЅРё"""
    servers = initialize_servers()
    for server in servers:
        if server["name"] == name:
            return server
    return None

def get_servers_by_type(server_type):
    """РџРѕР»СѓС‡РёС‚СЊ СЃРµСЂРІРµСЂС‹ РїРѕ С‚РёРїСѓ"""
    servers = initialize_servers()
    return [s for s in servers if s["type"] == server_type]

def servers_command(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРѕРјР°РЅРґС‹ /servers"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    servers = initialize_servers()
    
    # Р“СЂСѓРїРїРёСЂСѓРµРј СЃРµСЂРІРµСЂС‹ РїРѕ С‚РёРїСѓ
    by_type = {}
    for server in servers:
        if server["type"] not in by_type:
            by_type[server["type"]] = []
        by_type[server["type"]].append(server)
    
    message = "рџ“‹ *РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ*\n\n"
    
    for server_type, servers_list in by_type.items():
        message += f"**{server_type.upper()} СЃРµСЂРІРµСЂС‹ ({len(servers_list)}):**\n"
        for server in servers_list:
            message += f"вЂў {server['name']} ({server['ip']})\n"
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("в†©пёЏ РќР°Р·Р°Рґ", callback_data='settings_servers')],
        [
            InlineKeyboardButton("рџЏ  РќР° РіР»Р°РІРЅСѓСЋ", callback_data='main_menu'),
            InlineKeyboardButton("вњ–пёЏ Р—Р°РєСЂС‹С‚СЊ", callback_data='close'),
        ],
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

def servers_list_handler(update, context):
    """РћР±СЂР°Р±РѕС‚С‡РёРє РєРЅРѕРїРєРё СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ"""
    return servers_command(update, context)

# === РЈРўРР›РРўР« РџР РћР’Р•Р РљР ===

def check_port(ip, port, timeout=5):
    """РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё РїРѕСЂС‚Р°"""
    return net_check_port(ip, port, timeout=timeout)

def check_ping(ip):
    """РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё С‡РµСЂРµР· ping"""
    return net_check_ping(ip, timeout=10)

def run_ssh_command(ip, command, timeout=10):
    """Р’С‹РїРѕР»РЅСЏРµС‚ РєРѕРјР°РЅРґСѓ С‡РµСЂРµР· SSH СЃ РѕР±СЂР°Р±РѕС‚РєРѕР№ РѕС€РёР±РѕРє"""
    try:
        cmd = f"timeout {timeout} ssh -o ConnectTimeout=8 -o BatchMode=yes -o StrictHostKeyChecking=no -i {SSH_KEY_PATH} {SSH_USERNAME}@{ip} '{command}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout+2)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def get_windows_server_credentials(ip):
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРµС†РёС„РёС‡РЅС‹Рµ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РґР»СЏ Windows СЃРµСЂРІРµСЂР°"""
    for server_type, config in WINDOWS_SERVER_CREDENTIALS.items():
        if ip in config["servers"]:
            return config["credentials"]
    
    return WINRM_CONFIGS

def get_windows_server_type(ip):
    """РћРїСЂРµРґРµР»СЏРµС‚ С‚РёРї Windows СЃРµСЂРІРµСЂР°"""
    for server_type, config in WINDOWS_SERVER_CREDENTIALS.items():
        if ip in config["servers"]:
            return server_type
    return "unknown"

# === Р РђР—Р”Р•Р›Р¬РќР«Р• РџР РћР’Р•Р РљР WINDOWS РЎР•Р Р’Р•Р РћР’ ===

def check_domain_windows_servers(progress_callback=None):
    """РџСЂРѕРІРµСЂРєР° РґРѕРјРµРЅРЅС‹С… Windows СЃРµСЂРІРµСЂРѕРІ"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["domain_servers"]["servers"]]
    return check_windows_servers_generic(servers, "domain", progress_callback)

def check_admin_windows_servers(progress_callback=None):
    """РџСЂРѕРІРµСЂРєР° Windows СЃРµСЂРІРµСЂРѕРІ СЃ СѓС‡РµС‚РєРѕР№ Admin"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["admin_servers"]["servers"]]
    return check_windows_servers_generic(servers, "admin", progress_callback)

def check_standard_windows_servers(progress_callback=None):
    """РџСЂРѕРІРµСЂРєР° СЃС‚Р°РЅРґР°СЂС‚РЅС‹С… Windows СЃРµСЂРІРµСЂРѕРІ"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["standard_windows"]["servers"]]
    return check_windows_servers_generic(servers, "standard", progress_callback)

def check_windows_servers_generic(servers, server_type, progress_callback=None):
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ С„СѓРЅРєС†РёСЏ РїСЂРѕРІРµСЂРєРё Windows СЃРµСЂРІРµСЂРѕРІ"""
    results = []
    
    for i, server in enumerate(servers):
        if progress_callback:
            progress = (i + 1) / len(servers) * 100
            progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server['name']} ({server_type})...")
        
        try:
            resources = get_windows_resources_improved(server["ip"])
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None
            })
        except Exception as e:
            results.append({
                "server": server,
                "resources": None,
                "success": False,
                "error": str(e)
            })
    
    return results, len(servers)

# === Р РђР—Р”Р•Р›Р¬РќР«Р• РџР РћР’Р•Р РљР LINUX РЎР•Р Р’Р•Р РћР’ ===

def check_linux_servers(progress_callback=None):
    """РџСЂРѕРІРµСЂРєР° РІСЃРµС… Linux СЃРµСЂРІРµСЂРѕРІ"""
    servers = get_servers_by_type("ssh")
    results = []
    
    for i, server in enumerate(servers):
        if progress_callback:
            progress = (i + 1) / len(servers) * 100
            progress_callback(progress, f"РџСЂРѕРІРµСЂСЏРµРј {server['name']}...")
        
        try:
            resources = get_linux_resources_improved(server["ip"])
            results.append({
                "server": server,
                "resources": resources,
                "success": resources is not None
            })
        except Exception as e:
            results.append({
                "server": server,
                "resources": None,
                "success": False,
                "error": str(e)
            })
    
    return results, len(servers)

def check_windows_2025_servers(progress_callback=None):
    """РџСЂРѕРІРµСЂРєР° Windows Server 2025"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["windows_2025"]["servers"]]
    return check_windows_servers_generic(servers, "windows_2025", progress_callback)

def check_all_servers_by_type():
    """РџСЂРѕРІРµСЂРєР° РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ РїРѕ С‚РёРїР°Рј"""
    linux_results, linux_total = check_linux_servers()
    win2025_results, win2025_total = check_windows_2025_servers()
    domain_results, domain_total = check_domain_windows_servers()
    admin_results, admin_total = check_admin_windows_servers()
    standard_results, standard_total = check_standard_windows_servers()
    
    stats = {
        "linux": {"checked": linux_total, "success": len([r for r in linux_results if r["success"]])},
        "windows_2025": {"checked": win2025_total, "success": len([r for r in win2025_results if r["success"]])},
        "domain_windows": {"checked": domain_total, "success": len([r for r in domain_results if r["success"]])},
        "admin_windows": {"checked": admin_total, "success": len([r for r in admin_results if r["success"]])},
        "standard_windows": {"checked": standard_total, "success": len([r for r in standard_results if r["success"]])}
    }
    
    all_results = (linux_results + win2025_results + domain_results + 
                   admin_results + standard_results)
    return all_results, stats

# === РћРЎРќРћР’РќР«Р• Р¤РЈРќРљР¦РР РџР РћР’Р•Р РљР Р Р•РЎРЈР РЎРћР’ ===

def get_linux_resources_improved(ip, timeout=20):
    """РџРѕР»СѓС‡РµРЅРёРµ СЂРµСЃСѓСЂСЃРѕРІ Linux СЃРµСЂРІРµСЂР°"""
    if not check_port(ip, 22, 3):
        return None
    
    resources = {
        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
        "load_avg": "N/A", "uptime": "N/A", "os": "Linux",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "access_method": "SSH"
    }
    
    # CPU usage
    success, output, error = run_ssh_command(ip, "cat /proc/stat | head -1", 5)
    if success and output:
        try:
            parts = output.split()
            if len(parts) >= 8:
                user = int(parts[1])
                nice = int(parts[2]) 
                system = int(parts[3])
                idle = int(parts[4])
                
                total = user + nice + system + idle
                if total > 0:
                    resources["cpu"] = round((user + nice + system) * 100.0 / total, 1)
        except:
            pass
    
    # RAM usage
    success, output, error = run_ssh_command(ip, "free -b | head -2", 5)
    if success and output:
        try:
            lines = output.split('\n')
            for line in lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    if len(parts) >= 7:
                        total_mem = int(parts[1])
                        used_mem = int(parts[2])
                        if total_mem > 0:
                            resources["ram"] = round(used_mem * 100.0 / total_mem, 1)
        except:
            pass
    
    # Disk usage
    success, output, error = run_ssh_command(ip, "df / | tail -1", 5)
    if success and output:
        try:
            parts = output.split()
            if len(parts) >= 5:
                usage_str = parts[4]
                if usage_str.endswith('%'):
                    resources["disk"] = float(usage_str[:-1])
        except:
            pass
    
    return resources

def get_windows_resources_improved(ip, timeout=30):
    """РЈР»СѓС‡С€РµРЅРЅРѕРµ РїРѕР»СѓС‡РµРЅРёРµ СЂРµСЃСѓСЂСЃРѕРІ Windows СЃРµСЂРІРµСЂР° СЃ РЅРµСЃРєРѕР»СЊРєРёРјРё РјРµС‚РѕРґР°РјРё"""
    if not check_ping(ip):
        return None

    resources = {
        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
        "load_avg": "N/A", "uptime": "N/A", 
        "os": "Windows Server",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "available",
        "access_method": "Mixed",
        "server_type": get_windows_server_type(ip)
    }
    
    # РњРµС‚РѕРґ 1: РџРѕРїСЂРѕР±СѓРµРј WinRM СЃ PowerShell (СЃ РёСЃРїСЂР°РІР»РµРЅРЅРѕР№ РєРѕРґРёСЂРѕРІРєРѕР№)
    try:
        winrm_result = get_windows_resources_winrm(ip, timeout)
        if winrm_result and any([winrm_result.get("cpu", 0) > 0, winrm_result.get("ram", 0) > 0, winrm_result.get("disk", 0) > 0]):
            print(f"вњ… WinRM СѓСЃРїРµС€РЅРѕ РїРѕР»СѓС‡РёР» РґР°РЅРЅС‹Рµ РґР»СЏ {ip}: CPU={winrm_result.get('cpu')}%, RAM={winrm_result.get('ram')}%, Disk={winrm_result.get('disk')}%")
            return winrm_result
        elif winrm_result:
            print(f"вљ пёЏ WinRM РїРѕРґРєР»СЋС‡РёР»СЃСЏ Рє {ip}, РЅРѕ РЅРµ РїРѕР»СѓС‡РёР» РјРµС‚СЂРёРєРё")
    except Exception as e:
        print(f"вќЊ WinRM РѕС€РёР±РєР° РґР»СЏ {ip}: {e}")
    
    # РњРµС‚РѕРґ 2: РџРѕРїСЂРѕР±СѓРµРј WMI
    try:
        wmi_result = get_windows_resources_wmi(ip, timeout)
        if wmi_result and any([wmi_result.get("cpu", 0) > 0, wmi_result.get("ram", 0) > 0, wmi_result.get("disk", 0) > 0]):
            print(f"вњ… WMI СѓСЃРїРµС€РЅРѕ РїРѕР»СѓС‡РёР» РґР°РЅРЅС‹Рµ РґР»СЏ {ip}: CPU={wmi_result.get('cpu')}%, RAM={wmi_result.get('ram')}%, Disk={wmi_result.get('disk')}%")
            return wmi_result
    except Exception as e:
        print(f"вќЊ WMI РѕС€РёР±РєР° РґР»СЏ {ip}: {e}")
    
    # Р•СЃР»Рё РІСЃРµ РјРµС‚РѕРґС‹ РЅРµ СЃСЂР°Р±РѕС‚Р°Р»Рё, РЅРѕ СЃРµСЂРІРµСЂ РґРѕСЃС‚СѓРїРµРЅ
    if check_port(ip, 3389, 5):
        resources["status"] = "available_no_metrics"
        resources["access_method"] = "RDP_only"
        resources["cpu"] = 0.0
        resources["ram"] = 0.0
        resources["disk"] = 0.0
        print(f"вљ пёЏ РЎРµСЂРІРµСЂ {ip} РґРѕСЃС‚СѓРїРµРЅ РїРѕ RDP, РЅРѕ РјРµС‚СЂРёРєРё РЅРµ РїРѕР»СѓС‡РµРЅС‹")
        return resources
    
    print(f"вќЊ РЎРµСЂРІРµСЂ {ip} РЅРµРґРѕСЃС‚СѓРїРµРЅ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЂРµСЃСѓСЂСЃРѕРІ")
    return None

def get_windows_resources_winrm(ip, timeout=30):
    """РџРѕР»СѓС‡РµРЅРёРµ СЂРµСЃСѓСЂСЃРѕРІ С‡РµСЂРµР· WinRM СЃ РёСЃРїСЂР°РІР»РµРЅРёРµРј РєРѕРґРёСЂРѕРІРєРё"""
    try:
        import winrm
        
        credentials = get_windows_server_credentials(ip)
        
        for cred in credentials:
            try:
                username = cred["username"]
                password = cred["password"]
                domain = ""
                
                # Р•СЃР»Рё РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ СЃРѕРґРµСЂР¶РёС‚ РґРѕРјРµРЅ
                if "\\" in username:
                    domain, username = username.split("\\", 1)
                
                # РџРѕРґРєР»СЋС‡Р°РµРјСЃСЏ Рє WinRM
                if domain:
                    session = winrm.Session(
                        ip,
                        auth=(f"{domain}\\{username}", password),
                        transport='ntlm',
                        server_cert_validation='ignore',
                        read_timeout_sec=timeout
                    )
                else:
                    session = winrm.Session(
                        ip,
                        auth=(username, password),
                        transport='ntlm', 
                        server_cert_validation='ignore',
                        read_timeout_sec=timeout
                    )
                
                # РџСЂРѕСЃС‚Р°СЏ РїСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ
                result = session.run_cmd('hostname')
                if result.status_code != 0:
                    continue
                
                resources = {
                    "cpu": 0.0, "ram": 0.0, "disk": 0.0,
                    "os": "Windows Server",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "access_method": "WinRM"
                }
                
                # РљРѕРјРїР»РµРєСЃРЅС‹Р№ PowerShell СЃРєСЂРёРїС‚ РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ РІСЃРµС… РјРµС‚СЂРёРє
                ps_script = """
# CPU Usage
$cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object -ExpandProperty Average
if (-not $cpu) { $cpu = 0 }

# Memory Usage  
$os = Get-WmiObject -Class Win32_OperatingSystem
$totalMem = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$freeMem = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$usedMem = $totalMem - $freeMem
$memPercent = [math]::Round(($usedMem / $totalMem) * 100, 1)

# Disk Usage
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
if ($disk) {
    $diskPercent = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 1)
} else {
    $diskPercent = 0
}

# Output as CSV
"$cpu,$memPercent,$diskPercent"
"""
                
                result = session.run_ps(ps_script)
                if result.status_code == 0:
                    # РРЎРџР РђР’Р›Р•РќРР•: РєРѕСЂСЂРµРєС‚РЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР° РІС‹РІРѕРґР° СЃ СѓС‡РµС‚РѕРј РєРѕРґРёСЂРѕРІРєРё
                    output = ""
                    if hasattr(result, 'std_out') and result.std_out:
                        if isinstance(result.std_out, bytes):
                            output = result.std_out.decode('utf-8', errors='ignore')
                        else:
                            output = str(result.std_out)
                    
                    if output:
                        parts = output.strip().split(',')
                        if len(parts) == 3:
                            try:
                                resources["cpu"] = float(parts[0]) if parts[0] and parts[0].strip() else 0.0
                                resources["ram"] = float(parts[1]) if parts[1] and parts[1].strip() else 0.0
                                resources["disk"] = float(parts[2]) if parts[2] and parts[2].strip() else 0.0
                            except (ValueError, TypeError) as e:
                                print(f"Error parsing resources for {ip}: {e}, parts: {parts}")
                
                # Р•СЃР»Рё РїРѕР»СѓС‡РёР»Рё С…РѕС‚СЊ РєР°РєРёРµ-С‚Рѕ РґР°РЅРЅС‹Рµ
                if resources["cpu"] > 0 or resources["ram"] > 0 or resources["disk"] > 0:
                    return resources
                    
            except Exception as e:
                print(f"WinRM error for {ip} with {cred['username']}: {e}")
                continue
                
        return None
        
    except ImportError:
        print("WinRM library not available")
        return None
    except Exception as e:
        print(f"WinRM general error for {ip}: {e}")
        return None
    
def get_windows_resources_wmi(ip, timeout=30):
    """РџРѕР»СѓС‡РµРЅРёРµ СЂРµСЃСѓСЂСЃРѕРІ С‡РµСЂРµР· WMI (Р°Р»СЊС‚РµСЂРЅР°С‚РёРІРЅС‹Р№ РјРµС‚РѕРґ)"""
    try:
        import pythoncom
        import wmi
        
        credentials = get_windows_server_credentials(ip)
        
        for cred in credentials:
            try:
                username = cred["username"]
                password = cred["password"]
                
                # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ COM РґР»СЏ WMI
                pythoncom.CoInitialize()
                
                # РџРѕРґРєР»СЋС‡Р°РµРјСЃСЏ Рє WMI
                connection = wmi.WMI(
                    computer=ip,
                    user=username,
                    password=password
                )
                
                resources = {
                    "cpu": 0.0, "ram": 0.0, "disk": 0.0,
                    "os": "Windows Server", 
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "access_method": "WMI"
                }
                
                # CPU - СЃСЂРµРґРЅСЏСЏ Р·Р°РіСЂСѓР·РєР° РІСЃРµС… РїСЂРѕС†РµСЃСЃРѕСЂРѕРІ
                cpu_loads = []
                for processor in connection.Win32_Processor():
                    if processor.LoadPercentage:
                        cpu_loads.append(float(processor.LoadPercentage))
                
                if cpu_loads:
                    resources["cpu"] = round(sum(cpu_loads) / len(cpu_loads), 1)
                
                # Memory
                for os in connection.Win32_OperatingSystem():
                    total = int(os.TotalVisibleMemorySize)
                    free = int(os.FreePhysicalMemory)
                    if total > 0:
                        resources["ram"] = round(((total - free) / total) * 100, 1)
                
                # Disk C:
                for disk in connection.Win32_LogicalDisk(DeviceID='C:'):
                    total_size = int(disk.Size)
                    free_space = int(disk.FreeSpace)
                    if total_size > 0:
                        resources["disk"] = round(((total_size - free_space) / total_size) * 100, 1)
                
                pythoncom.CoUninitialize()
                
                # Р•СЃР»Рё РїРѕР»СѓС‡РёР»Рё РґР°РЅРЅС‹Рµ
                if resources["cpu"] > 0 or resources["ram"] > 0 or resources["disk"] > 0:
                    return resources
                    
            except Exception as e:
                print(f"WMI error for {ip} with {cred['username']}: {e}")
                continue
                
        return None
        
    except ImportError:
        print("WMI library not available")
        return None
    except Exception as e:
        print(f"WMI general error for {ip}: {e}")
        return None

def get_windows_disk_only(ip, timeout=30):
    """РњРёРЅРёРјР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° - С‚РѕР»СЊРєРѕ РґРёСЃРє С‡РµСЂРµР· СЂР°Р·РЅС‹Рµ РјРµС‚РѕРґС‹"""
    try:
        # РџСЂРѕСЃС‚Р°СЏ РїСЂРѕРІРµСЂРєР° С‡РµСЂРµР· net use (РµСЃР»Рё РґРѕСЃС‚СѓРїРЅС‹ РѕР±С‰РёРµ РїР°РїРєРё)
        import subprocess
        
        credentials = get_windows_server_credentials(ip)
        
        for cred in credentials:
            try:
                username = cred["username"]
                password = cred["password"]
                
                # РџСЂРѕР±СѓРµРј РїРѕРґРєР»СЋС‡РёС‚СЊСЃСЏ Рє Р°РґРјРёРЅРёСЃС‚СЂР°С‚РёРІРЅРѕР№ share
                cmd = f'net use \\\\{ip}\\admin$ {password} /user:{username}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Р•СЃР»Рё РїРѕРґРєР»СЋС‡РёР»РёСЃСЊ, РїС‹С‚Р°РµРјСЃСЏ РїРѕР»СѓС‡РёС‚СЊ РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ РґРёСЃРєРµ
                    ps_script = "Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID='C:'\" | Select-Object Size,FreeSpace"
                    # Р—РґРµСЃСЊ РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РІС‹РїРѕР»РЅРµРЅРёРµ PowerShell С‡РµСЂРµР· psexec РёР»Рё Р°РЅР°Р»РѕРіРё
                    
                    resources = {
                        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
                        "os": "Windows Server",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "access_method": "NetUse",
                        "status": "basic_access"
                    }
                    
                    # РћС‚РєР»СЋС‡Р°РµРј СЃРѕРµРґРёРЅРµРЅРёРµ
                    subprocess.run(f'net use \\\\{ip}\\admin$ /delete', shell=True, capture_output=True)
                    return resources
                    
            except Exception as e:
                continue
                
        return None
        
    except Exception as e:
        print(f"Disk only check error for {ip}: {e}")
        return None
        
def check_resource_thresholds(ip, resources, server_name):
    """РџСЂРѕРІРµСЂСЏРµС‚ РїСЂРµРІС‹С€РµРЅРёРµ РїРѕСЂРѕРіРѕРІ СЂРµСЃСѓСЂСЃРѕРІ"""
    alerts = []
    if not resources:
        return alerts

    cpu = resources.get("cpu", 0)
    ram = resources.get("ram", 0)
    disk = resources.get("disk", 0)

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

    return alerts

def check_server_availability(server):
    """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё СЃРµСЂРІРµСЂР° - Р РђР‘РћР§РђРЇ Р’Р•Р РЎРРЇ"""
    try:
        server_type = server.get("type", "ssh")
        ip = server["ip"]
        
        if server_type == "rdp":
            return check_port(ip, 3389)
        elif server_type == "ping":
            return check_ping(ip)
        else:
            return _server_checker.check_ssh_universal(ip)
    except Exception as e:
        debug_log(f"вќЊ РћС€РёР±РєР° РїСЂРѕРІРµСЂРєРё {server.get('name', 'unknown')}: {e}")
        return False
    
