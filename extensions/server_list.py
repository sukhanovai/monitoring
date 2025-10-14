from config import RDP_SERVERS, SSH_SERVERS, PING_SERVERS
import socket

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
        "192.168.20.5": "help5-old",
        "192.168.20.8": "help8-old",
        "192.168.20.10": "help10-old",
        "192.168.20.11": "help11-old",
        "192.168.20.13": "SR-DC2-SSH",
        "192.168.20.14": "help14-old",
        "192.168.20.17": "docs",
        "192.168.20.22": "sr-goods",
        "192.168.20.25": "sr-db",
        "192.168.20.30": "bup3",
        "192.168.20.32": "bup",
        "192.168.20.35": "sr-slk",
        "192.168.20.37": "exchange",
        "192.168.20.39": "wms",
        "192.168.20.41": "awiki",
        "192.168.20.44": "np",
        "192.168.20.48": "sr-smb1",
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
    # Proxmox серверы обычно в сети 192.168.30.x или определенные IP
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
