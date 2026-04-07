"""
/extensions/server_checks.py
Server Monitoring System v8.41.45
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Unified server checks: resources, availability, list
Система мониторинга серверов
Версия: 8.41.45
Автор: Александр Суханов (c)
Лицензия: MIT
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
                   RESOURCE_THRESHOLDS, WINDOWS_SERVER_CREDENTIALS, WINRM_CONFIGS,
                   SERVER_CONFIG)

# === СПИСОК СЕРВЕРОВ ===

def initialize_servers():
    """Инициализация списка серверов из конфигурации"""
    servers = []
    
    # Windows RDP серверы
    for ip, name in SERVER_CONFIG["windows_servers"].items():
        servers.append({
            "ip": ip,
            "name": name,
            "type": "rdp"
        })
    
    # Linux SSH серверы
    for ip, name in SERVER_CONFIG["linux_servers"].items():
        servers.append({
            "ip": ip,
            "name": name,
            "type": "ssh"
        })
    
    # Ping-only серверы
    for ip, name in SERVER_CONFIG["ping_servers"].items():
        servers.append({
            "ip": ip,
            "name": name,
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
        [
            InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close'),
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
    """Обработчик кнопки списка серверов"""
    return servers_command(update, context)

# === УТИЛИТЫ ПРОВЕРКИ ===

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

# === РАЗДЕЛЬНЫЕ ПРОВЕРКИ WINDOWS СЕРВЕРОВ ===

def check_domain_windows_servers(progress_callback=None):
    """Проверка доменных Windows серверов"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["domain_servers"]["servers"]]
    return check_windows_servers_generic(servers, "domain", progress_callback)

def check_admin_windows_servers(progress_callback=None):
    """Проверка Windows серверов с учеткой Admin"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["admin_servers"]["servers"]]
    return check_windows_servers_generic(servers, "admin", progress_callback)

def check_standard_windows_servers(progress_callback=None):
    """Проверка стандартных Windows серверов"""
    servers = [s for s in get_servers_by_type("rdp") 
               if s["ip"] in WINDOWS_SERVER_CREDENTIALS["standard_windows"]["servers"]]
    return check_windows_servers_generic(servers, "standard", progress_callback)

def check_windows_servers_generic(servers, server_type, progress_callback=None):
    """Универсальная функция проверки Windows серверов"""
    results = []
    
    for i, server in enumerate(servers):
        if progress_callback:
            progress = (i + 1) / len(servers) * 100
            progress_callback(progress, f"Проверяем {server['name']} ({server_type})...")
        
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

# === РАЗДЕЛЬНЫЕ ПРОВЕРКИ LINUX СЕРВЕРОВ ===

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
    return check_windows_servers_generic(servers, "windows_2025", progress_callback)

def check_all_servers_by_type():
    """Проверка всех серверов по типам"""
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

# === ОСНОВНЫЕ ФУНКЦИИ ПРОВЕРКИ РЕСУРСОВ ===

def get_linux_resources_improved(ip, timeout=20):
    """Получение ресурсов Linux сервера"""
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
    """Улучшенное получение ресурсов Windows сервера с несколькими методами"""
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
    
    # Метод 1: Попробуем WinRM с PowerShell (с исправленной кодировкой)
    try:
        winrm_result = get_windows_resources_winrm(ip, timeout)
        if winrm_result and any([winrm_result.get("cpu", 0) > 0, winrm_result.get("ram", 0) > 0, winrm_result.get("disk", 0) > 0]):
            print(f"✅ WinRM успешно получил данные для {ip}: CPU={winrm_result.get('cpu')}%, RAM={winrm_result.get('ram')}%, Disk={winrm_result.get('disk')}%")
            return winrm_result
        elif winrm_result:
            print(f"⚠️ WinRM подключился к {ip}, но не получил метрики")
    except Exception as e:
        print(f"❌ WinRM ошибка для {ip}: {e}")
    
    # Метод 2: Попробуем WMI
    try:
        wmi_result = get_windows_resources_wmi(ip, timeout)
        if wmi_result and any([wmi_result.get("cpu", 0) > 0, wmi_result.get("ram", 0) > 0, wmi_result.get("disk", 0) > 0]):
            print(f"✅ WMI успешно получил данные для {ip}: CPU={wmi_result.get('cpu')}%, RAM={wmi_result.get('ram')}%, Disk={wmi_result.get('disk')}%")
            return wmi_result
    except Exception as e:
        print(f"❌ WMI ошибка для {ip}: {e}")
    
    # Если все методы не сработали, но сервер доступен
    if check_port(ip, 3389, 5):
        resources["status"] = "available_no_metrics"
        resources["access_method"] = "RDP_only"
        resources["cpu"] = 0.0
        resources["ram"] = 0.0
        resources["disk"] = 0.0
        print(f"⚠️ Сервер {ip} доступен по RDP, но метрики не получены")
        return resources
    
    print(f"❌ Сервер {ip} недоступен для мониторинга ресурсов")
    return None

def get_windows_resources_winrm(ip, timeout=30):
    """Получение ресурсов через WinRM с исправлением кодировки"""
    try:
        import winrm
        
        credentials = get_windows_server_credentials(ip)
        
        for cred in credentials:
            try:
                username = cred["username"]
                password = cred["password"]
                domain = ""
                
                # Если имя пользователя содержит домен
                if "\\" in username:
                    domain, username = username.split("\\", 1)
                
                # Подключаемся к WinRM
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
                
                # Простая проверка подключения
                result = session.run_cmd('hostname')
                if result.status_code != 0:
                    continue
                
                resources = {
                    "cpu": 0.0, "ram": 0.0, "disk": 0.0,
                    "os": "Windows Server",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "access_method": "WinRM"
                }
                
                # Комплексный PowerShell скрипт для получения всех метрик
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
                    # ИСПРАВЛЕНИЕ: корректная обработка вывода с учетом кодировки
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
                
                # Если получили хоть какие-то данные
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
    """Получение ресурсов через WMI (альтернативный метод)"""
    try:
        import pythoncom
        import wmi
        
        credentials = get_windows_server_credentials(ip)
        
        for cred in credentials:
            try:
                username = cred["username"]
                password = cred["password"]
                
                # Инициализация COM для WMI
                pythoncom.CoInitialize()
                
                # Подключаемся к WMI
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
                
                # CPU - средняя загрузка всех процессоров
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
                
                # Если получили данные
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
    """Минимальная проверка - только диск через разные методы"""
    try:
        # Простая проверка через net use (если доступны общие папки)
        import subprocess
        
        credentials = get_windows_server_credentials(ip)
        
        for cred in credentials:
            try:
                username = cred["username"]
                password = cred["password"]
                
                # Пробуем подключиться к административной share
                cmd = f'net use \\\\{ip}\\admin$ {password} /user:{username}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Если подключились, пытаемся получить информацию о диске
                    ps_script = "Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID='C:'\" | Select-Object Size,FreeSpace"
                    # Здесь можно добавить выполнение PowerShell через psexec или аналоги
                    
                    resources = {
                        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
                        "os": "Windows Server",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "access_method": "NetUse",
                        "status": "basic_access"
                    }
                    
                    # Отключаем соединение
                    subprocess.run(f'net use \\\\{ip}\\admin$ /delete', shell=True, capture_output=True)
                    return resources
                    
            except Exception as e:
                continue
                
        return None
        
    except Exception as e:
        print(f"Disk only check error for {ip}: {e}")
        return None
        
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
