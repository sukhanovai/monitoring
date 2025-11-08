"""
Server Monitoring System v2.3.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Унифицированные проверки серверов: ресурсы, доступность, список
"""

import re
import subprocess
import socket
from datetime import datetime
import sys
import os
sys.path.insert(0, '/opt/monitoring')

from config import (RDP_SERVERS, SSH_SERVERS, PING_SERVERS, SSH_KEY_PATH, SSH_USERNAME, 
                   RESOURCE_THRESHOLDS, WINDOWS_SERVER_CREDENTIALS, WINRM_CONFIGS)

# === СПИСОК СЕРВЕРОВ (из server_list.py) ===

def initialize_servers():
    """Инициализация списка серверов с привязкой IP к именам"""
    servers = []
    
    # Windows RDP серверы - ПРАВИЛЬНЫЕ ИМЕНА
    windows_servers = {
        "192.168.20.3": "SR-DC2",
        "192.168.20.4": "SR-DC1", 
        "192.168.20.6": "ts1",
        "192.168.20.9": "TSR-SR7",
        "192.168.20.26": "SR-WTW",
        "192.168.20.38": "ts4",
        "192.168.20.42": "TOOLS",
        "192.168.20.47": "ts2",
        "192.168.20.56": "ts3",
        "192.168.20.57": "ts5",
        "192.168.21.133": "TSR-1C72"
    }
    
    for ip in RDP_SERVERS:
        name = windows_servers.get(ip, f"Windows-{ip.split('.')[-1]}")
        servers.append({
            "ip": ip,
            "name": name,
            "type": "rdp"
        })
    
    # Linux SSH серверы - ПРАВИЛЬНЫЕ ИМЕНА
    linux_servers = {
        "192.168.30.101": "pve1",
        "192.168.30.102": "pve2",
        "192.168.30.103": "pve3",
        "192.168.30.104": "pve4",
        "192.168.30.105": "pve5",
        "192.168.30.106": "pve6",
        "192.168.30.108": "pve8",
        "192.168.30.110": "pve10",
        "192.168.30.112": "pve12",
        "192.168.30.113": "pve13",
        "192.168.30.114": "pve14",
        "192.168.20.5": "network",
        "192.168.20.8": "sr-1cork",
        "192.168.20.10": "sr-web-fe",
        "192.168.20.11": "sr-web",
        "192.168.20.13": "unifi",
        "192.168.20.14": "smb3",
        "192.168.20.17": "docs",
        "192.168.20.22": "sr-goods",
        "192.168.20.25": "db",
        "192.168.20.30": "bup3",
        "192.168.20.32": "bup",
        "192.168.20.35": "sr-slk",
        "192.168.20.37": "exchange",
        "192.168.20.39": "wms",
        "192.168.20.41": "awiki",
        "192.168.20.44": "np",
        "192.168.20.48": "smb1",
        "192.168.20.49": "mail",
        "192.168.20.51": "buh",
        "192.168.20.58": "devel",
        "192.168.20.59": "bup2",
        "192.168.20.74": "smb4"
    }
    
    for ip in SSH_SERVERS:
        name = linux_servers.get(ip, f"Linux-{ip.split('.')[-1]}")
        servers.append({
            "ip": ip,
            "name": name,
            "type": "ssh"
        })
    
    # Ping-only серверы
    for ip in PING_SERVERS:
        servers.append({
            "ip": ip,
            "name": f"Ping-{ip.split('.')[-1]}",
            "type": "ping"
        })
    
    return servers

def resolve_hostname(ip):
    """Разрешает IP в hostname"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except:
        return ip

def is_proxmox_server(server):
    """Проверяет, является ли сервер Proxmox"""
    ip = server["ip"]
    return (ip.startswith("192.168.30.") or
           ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])

def get_server_by_ip(ip):
    """Получить сервер по IP"""
    servers = initialize_servers()
    for server in servers:
        if server["ip"] == ip:
            return server
    return None

def get_server_by_name(name):
    """Получить сервер по имени"""
    servers = initialize_servers()
    for server in servers:
        if server["name"] == name:
            return server
    return None

def get_servers_by_type(server_type):
    """Получить серверы по типу"""
    servers = initialize_servers()
    return [s for s in servers if s["type"] == server_type]

def servers_command(update, context):
    """Обработчик команды /servers"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    servers = initialize_servers()
    
    # Группируем серверы по типу
    by_type = {}
    for server in servers:
        if server["type"] not in by_type:
            by_type[server["type"]] = []
        by_type[server["type"]].append(server)
    
    message = "📋 *Список серверов*\n\n"
    
    for server_type, servers_list in by_type.items():
        message += f"**{server_type.upper()} серверы ({len(servers_list)}):**\n"
        for server in servers_list:
            message += f"• {server['name']} ({server['ip']})\n"
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить список", callback_data='servers_list')],
        [InlineKeyboardButton("📊 Статус мониторинга", callback_data='monitor_status')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
    """Обработчик кнопки списка серверов"""
    return servers_command(update, context)

# === УТИЛИТЫ ПРОВЕРКИ (из resource_check.py) ===

def check_port(ip, port, timeout=5):
    """Проверка доступности порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_ping(ip):
    """Проверка доступности через ping"""
    try:
        result = subprocess.run(['ping', '-c', '2', '-W', '2', ip], 
                              capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False

def run_ssh_command(ip, command, timeout=10):
    """Выполняет команду через SSH с обработкой ошибок"""
    try:
        cmd = f"timeout {timeout} ssh -o ConnectTimeout=8 -o BatchMode=yes -o StrictHostKeyChecking=no -i {SSH_KEY_PATH} {SSH_USERNAME}@{ip} '{command}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout+2)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def get_windows_server_credentials(ip):
    """Возвращает специфичные учетные данные для Windows сервера"""
    for server_type, config in WINDOWS_SERVER_CREDENTIALS.items():
        if ip in config["servers"]:
            return config["credentials"]
    
    return WINRM_CONFIGS

def get_windows_server_type(ip):
    """Определяет тип Windows сервера"""
    for server_type, config in WINDOWS_SERVER_CREDENTIALS.items():
        if ip in config["servers"]:
            return server_type
    return "unknown"

# === РАЗДЕЛЬНЫЕ ПРОВЕРКИ (из separate_checks.py) ===

def check_linux_servers(progress_callback=None):
    """Проверка всех Linux серверов"""
    servers = get_servers_by_type("ssh")
    results = []
    
    for i, server in enumerate(servers):
        if progress_callback:
            progress = (i + 1) / len(servers) * 100
            progress_callback(progress, f"Проверяем {server['name']}...")
        
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
    """Проверка Windows Server 2025"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["windows_2025"]["servers"]]
    results = []
    
    for i, server in enumerate(servers):
        if progress_callback:
            progress = (i + 1) / len(servers) * 100
            progress_callback(progress, f"Проверяем {server['name']}...")
        
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

def check_all_servers_by_type():
    """Проверка всех серверов по типам"""
    linux_results, linux_total = check_linux_servers()
    win2025_results, win2025_total = check_windows_2025_servers()
    
    stats = {
        "linux": {"checked": linux_total, "success": len([r for r in linux_results if r["success"]])},
        "windows_2025": {"checked": win2025_total, "success": len([r for r in win2025_results if r["success"]])},
        "standard_windows": {"checked": 0, "success": 0}  # Можно добавить другие типы
    }
    
    all_results = linux_results + win2025_results
    return all_results, stats

# === ОСНОВНЫЕ ФУНКЦИИ ПРОВЕРКИ РЕСУРСОВ ===

def get_linux_resources_improved(ip, timeout=20):
    """Получение ресурсов Linux сервера"""
    # Реализация из resource_check.py (сокращено для примера)
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
    """Улучшенное получение ресурсов Windows сервера"""
    # Реализация из resource_check.py (сокращено для примера)
    if not check_ping(ip):
        return None

    # Упрощенная реализация - в реальном коде здесь будет полная логика
    return {
        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
        "load_avg": "N/A", "uptime": "N/A", 
        "os": "Windows Server",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "available",
        "access_method": "WinRM",
        "server_type": get_windows_server_type(ip)
    }

def check_resource_thresholds(ip, resources, server_name):
    """Проверяет превышение порогов ресурсов"""
    alerts = []
    if not resources:
        return alerts

    cpu = resources.get("cpu", 0)
    ram = resources.get("ram", 0)
    disk = resources.get("disk", 0)

    if cpu >= RESOURCE_THRESHOLDS["cpu_critical"]:
        alerts.append(f"🚨 CPU: {cpu}% (критично)")
    elif cpu >= RESOURCE_THRESHOLDS["cpu_warning"]:
        alerts.append(f"⚠️ CPU: {cpu}% (высокая нагрузка)")

    if ram >= RESOURCE_THRESHOLDS["ram_critical"]:
        alerts.append(f"🚨 RAM: {ram}% (критично)")
    elif ram >= RESOURCE_THRESHOLDS["ram_warning"]:
        alerts.append(f"⚠️ RAM: {ram}% (мало свободной памяти)")

    if disk >= RESOURCE_THRESHOLDS["disk_critical"]:
        alerts.append(f"🚨 Disk: {disk}% (критично)")
    elif disk >= RESOURCE_THRESHOLDS["disk_warning"]:
        alerts.append(f"⚠️ Disk: {disk}% (мало места)")

    return alerts
