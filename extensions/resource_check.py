"""
Server Monitoring System v2.2.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
"""
import re
import subprocess
import socket
from datetime import datetime
import sys
import os
sys.path.insert(0, '/opt/monitoring')

from config import SSH_KEY_PATH, SSH_USERNAME, RESOURCE_THRESHOLDS, WINDOWS_SERVER_CREDENTIALS, WINRM_CONFIGS

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
            print(f"🔑 Используем {server_type} учетные данные для {ip}")
            return config["credentials"]
    
    # Если сервер не найден в специфичных конфигурациях, используем общие
    print(f"🔑 Используем общие учетные данные для {ip}")
    return WINRM_CONFIGS

def get_windows_disk_usage_standard(session):
    """Стандартный метод получения использования диска для обычных Windows серверов"""
    disk_commands = [
        'powershell -Command "$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID=\'C:\'\"; Write-Output \"SIZE:$($disk.Size) FREE:$($disk.FreeSpace)\""',
        'wmic logicaldisk where "DeviceID=\'C:\'" get Size,FreeSpace /value',
        'powershell -Command "Get-PSDrive C | Select-Object Used,Free"',
        'powershell -Command "(Get-CimInstance -ClassName Win32_LogicalDisk -Filter \"DeviceID=\'C:\'\").Size, (Get-CimInstance -ClassName Win32_LogicalDisk -Filter \"DeviceID=\'C:\'\").FreeSpace"'
    ]
    
    for disk_cmd in disk_commands:
        try:
            result = session.run_cmd(disk_cmd)
            if result.status_code == 0:
                output = result.std_out.decode('utf-8', errors='ignore').strip()
                print(f"🔍 Команда диска: {disk_cmd[:60]}...")
                print(f"🔍 Вывод: {output[:200]}")
                
                # Вариант 1: Формат SIZE:... FREE:...
                if "SIZE:" in output and "FREE:" in output:
                    try:
                        size_match = re.search(r'SIZE:(\d+)', output)
                        free_match = re.search(r'FREE:(\d+)', output)
                        if size_match and free_match:
                            size = int(size_match.group(1))
                            free = int(free_match.group(1))
                            if size > 0:
                                disk_usage = round((size - free) * 100.0 / size, 1)
                                print(f"✅ Disk usage: {disk_usage}%")
                                return disk_usage
                    except Exception as e:
                        print(f"❌ Ошибка парсинга SIZE/FREE: {e}")
                
                # Вариант 2: Формат WMIC (Size=... FreeSpace=...)
                elif "Size=" in output and "FreeSpace=" in output:
                    try:
                        size_match = re.search(r'Size=(\d+)', output)
                        free_match = re.search(r'FreeSpace=(\d+)', output)
                        if size_match and free_match:
                            size = int(size_match.group(1))
                            free = int(free_match.group(1))
                            if size > 0:
                                disk_usage = round((size - free) * 100.0 / size, 1)
                                print(f"✅ Disk usage: {disk_usage}%")
                                return disk_usage
                    except Exception as e:
                        print(f"❌ Ошибка парсинга WMIC: {e}")
                
                # Вариант 3: Формат Get-PSDrive (Used/Free)
                elif "Used" in output and "Free" in output:
                    try:
                        lines = [line.strip() for line in output.split('\n') if line.strip() and line.strip().isdigit()]
                        if len(lines) >= 2:
                            used = int(lines[0])
                            free = int(lines[1])
                            total = used + free
                            if total > 0:
                                disk_usage = round(used * 100.0 / total, 1)
                                print(f"✅ Disk usage: {disk_usage}%")
                                return disk_usage
                    except Exception as e:
                        print(f"❌ Ошибка парсинга PSDrive: {e}")
                
                # Вариант 4: Простой поиск двух больших чисел
                else:
                    numbers = re.findall(r'\d+', output)
                    large_numbers = [int(n) for n in numbers if int(n) > 1000000000]  # > 1GB
                    if len(large_numbers) >= 2:
                        try:
                            size = max(large_numbers)
                            free = min(large_numbers)
                            if size > free:
                                disk_usage = round((size - free) * 100.0 / size, 1)
                                print(f"✅ Disk usage (numbers): {disk_usage}%")
                                return disk_usage
                        except Exception as e:
                            print(f"❌ Ошибка парсинга чисел: {e}")
                        
        except Exception as e:
            print(f"⚠️ Ошибка команды диска: {e}")
            continue
    
    print("❌ Не удалось получить данные о диске")
    return 0.0

def get_windows_disk_usage_windows2025(session):
    """Специальный метод для Windows Server 2025"""
    print("🔍 Используем специальный метод для Windows 2025")
    
    # Пробуем разные команды для Windows 2025
    disk_commands_2025 = [
        'powershell -Command "Get-Volume -DriveLetter C | Select-Object Size, SizeRemaining"',
        'powershell -Command "(Get-Volume -DriveLetter C).Size, (Get-Volume -DriveLetter C).SizeRemaining"',
        'powershell -Command "Get-CimInstance -ClassName Win32_LogicalDisk -Filter \"DeviceID=\'C:\'\" | Select-Object Size, FreeSpace"',
        'powershell -Command "Get-WmiObject -Class Win32_LogicalDisk -Filter \"DeviceID=\'C:\'\" | Select-Object Size, FreeSpace"'
    ]
    
    for disk_cmd in disk_commands_2025:
        try:
            result = session.run_cmd(disk_cmd)
            if result.status_code == 0:
                output = result.std_out.decode('utf-8', errors='ignore').strip()
                print(f"🔍 Команда 2025: {disk_cmd[:60]}...")
                print(f"🔍 Вывод 2025: {output[:200]}")
                
                # Парсим вывод Windows 2025
                numbers = re.findall(r'\d+', output)
                large_numbers = [int(n) for n in numbers if int(n) > 1000000000]
                
                if len(large_numbers) >= 2:
                    try:
                        size = max(large_numbers)
                        free = min(large_numbers)
                        if size > free:
                            disk_usage = round((size - free) * 100.0 / size, 1)
                            print(f"✅ Windows 2025 Disk usage: {disk_usage}%")
                            return disk_usage
                    except Exception as e:
                        print(f"❌ Ошибка парсинга Windows 2025: {e}")
                        
        except Exception as e:
            print(f"⚠️ Ошибка команды Windows 2025: {e}")
            continue
    
    # Если специальные команды не сработали, пробуем стандартный метод
    print("🔄 Пробуем стандартный метод для Windows 2025")
    return get_windows_disk_usage_standard(session)

def get_windows_disk_usage(session, ip):
    """Умный выбор метода получения использования диска в зависимости от сервера"""
    # Определяем тип сервера по IP
    windows_2025_servers = WINDOWS_SERVER_CREDENTIALS["windows_2025"]["servers"]
    
    if ip in windows_2025_servers:
        return get_windows_disk_usage_windows2025(session)
    else:
        return get_windows_disk_usage_standard(session)

def get_windows_resources_optimized_old(ip, timeout=25):
    """Оптимизированное получение ресурсов для старых Windows серверов (2012, 2012 R2)"""
    print(f"🔍 Проверяем старый Windows сервер {ip} (оптимизированный метод)")

    # Проверяем доступность сервера
    if not check_ping(ip):
        print(f"❌ Сервер {ip} недоступен (ping failed)")
        return None

    # Для старых серверов проверяем только RDP порт
    rdp_available = check_port(ip, 3389, 3)
    print(f"ℹ️ RDP порт: {'✅' if rdp_available else '❌'}")

    # Пробуем WinRM если доступен
    winrm_available = check_port(ip, 5985, 2)
    if winrm_available:
        try:
            import winrm
            print(f"🔄 Пробуем WinRM подключение к {ip}...")

            # Получаем специфичные учетные данные для этого сервера
            creds_to_try = get_windows_server_credentials(ip)

            for config in creds_to_try:
                username = config["username"]
                password = config["password"]

                print(f"🔑 Пробуем: {username}")

                try:
                    # Для старых серверов используем правильные настройки timeout
                    session = winrm.Session(
                        ip,
                        auth=(username, password),
                        transport='ntlm',
                        server_cert_validation='ignore',
                        read_timeout_sec=timeout + 10,
                        operation_timeout_sec=timeout
                    )

                    # Упрощенная тестовая команда для старых серверов - БЕЗ timeout параметра
                    result = session.run_cmd('echo %COMPUTERNAME%')
                    if result.status_code == 0:
                        print(f"✅ Аутентификация успешна для {ip}")

                        # Получаем только базовые метрики для старых серверов
                        resources = get_windows_basic_resources_old(session, ip)
                        if resources:
                            resources["access_method"] = "WinRM"
                            resources["server_type"] = get_windows_server_type(ip)
                            return resources
                        else:
                            print(f"⚠️ Ресурсы не получены, но аутентификация успешна")
                            # Возвращаем базовую информацию о доступности
                            return {
                                "cpu": 0.0,
                                "ram": 0.0,
                                "disk": 0.0,
                                "load_avg": "N/A",
                                "uptime": "N/A",
                                "os": "Windows Server (old)",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "status": "available",
                                "access_method": "WinRM",
                                "server_type": get_windows_server_type(ip)
                            }

                except Exception as e:
                    error_str = str(e)
                    if "Authentication" in error_str or "credentials" in error_str.lower():
                        print(f"❌ Ошибка аутентификации для {username}")
                    elif "Operation timed out" in error_str or "read_timeout_sec" in error_str:
                        print(f"⏰ Таймаут/ошибка timeout для {username} на {ip}: {e}")
                        # Для таймаутов сразу переходим к fallback
                        break
                    else:
                        print(f"❌ Ошибка WinRM для {username}: {e}")
                    continue

            print("⚠️ Все учетные данные не подошли или таймауты")

        except ImportError:
            print("❌ Модуль winrm не установлен")
        except Exception as e:
            print(f"❌ Общая ошибка WinRM: {e}")

    # Если RDP доступен или сервер пингуется, используем fallback
    if rdp_available:
        print(f"ℹ️ Используем RDP fallback для {ip}")
        resources = get_windows_fallback_resources(ip, "RDP")
        if resources:
            resources["access_method"] = "RDP"
            resources["server_type"] = get_windows_server_type(ip)
        return resources

    # Если сервер пингуется, но порты закрыты
    print(f"ℹ️ Сервер {ip} доступен по ping")
    resources = get_windows_fallback_resources(ip, "Ping")
    if resources:
        resources["access_method"] = "Ping"
        resources["server_type"] = get_windows_server_type(ip)
    return resources

def get_windows_basic_resources_old(session, ip):
    """Получаем только базовые метрики для старых Windows серверов с упрощенными командами"""
    try:
        cpu_usage = 0.0
        ram_usage = 0.0
        disk_usage = 0.0
        os_info = "Windows Server"

        # 1. Получаем информацию о системе (самая простая команда)
        print("🔍 Получаем базовую информацию о системе...")

        # Пробуем самую простую команду для получения ОС - БЕЗ timeout
        result = session.run_cmd('ver')
        if result.status_code == 0:
            output = result.std_out.decode('utf-8', errors='ignore')
            if 'Microsoft' in output:
                os_info = output.strip()
                print(f"✅ ОС: {os_info}")

        # 2. Получаем использование CPU (самый простой метод)
        print("🔍 Получаем CPU (простой метод)...")
        result = session.run_cmd('wmic cpu get loadpercentage /value')
        if result.status_code == 0:
            output = result.std_out.decode('utf-8', errors='ignore')
            for line in output.split('\n'):
                if 'LoadPercentage' in line:
                    try:
                        cpu_usage = float(line.split('=')[1].strip())
                        print(f"✅ CPU: {cpu_usage}%")
                        break
                    except:
                        pass

        # 3. Получаем использование RAM (простой метод)
        print("🔍 Получаем RAM (простой метод)...")
        result = session.run_cmd('systeminfo | find "Available Physical Memory"')
        if result.status_code == 0:
            output = result.std_out.decode('utf-8', errors='ignore')
            # Парсим вывод systeminfo для получения памяти
            lines = output.split('\n')
            for line in lines:
                if 'Available Physical Memory' in line:
                    try:
                        # Формат: "Available Physical Memory: 8,192 MB"
                        parts = line.split(':')
                        if len(parts) > 1:
                            available_mem_str = parts[1].strip()
                            # Убираем запятые и получаем число
                            available_mem = int(available_mem_str.split()[0].replace(',', ''))

                            # Получаем общую память
                            result_total = session.run_cmd('systeminfo | find "Total Physical Memory"')
                            if result_total.status_code == 0:
                                total_output = result_total.std_out.decode('utf-8', errors='ignore')
                                for total_line in total_output.split('\n'):
                                    if 'Total Physical Memory' in total_line:
                                        total_parts = total_line.split(':')
                                        if len(total_parts) > 1:
                                            total_mem_str = total_parts[1].strip()
                                            total_mem = int(total_mem_str.split()[0].replace(',', ''))

                                            if total_mem > 0:
                                                ram_usage = round((total_mem - available_mem) * 100.0 / total_mem, 1)
                                                print(f"✅ RAM: {ram_usage}%")
                                                break
                    except Exception as e:
                        print(f"❌ Ошибка парсинга RAM: {e}")

        # 4. Получаем использование диска (простой метод)
        print("🔍 Получаем Disk (простой метод)...")
        result = session.run_cmd('fsutil volume diskfree C:')
        if result.status_code == 0:
            output = result.std_out.decode('utf-8', errors='ignore')
            # Парсим вывод fsutil
            total_bytes = 0
            free_bytes = 0

            for line in output.split('\n'):
                if 'Total # of bytes' in line:
                    try:
                        total_bytes = int(line.split(':')[1].strip())
                    except:
                        pass
                elif 'Total # of free bytes' in line:
                    try:
                        free_bytes = int(line.split(':')[1].strip())
                    except:
                        pass

            if total_bytes > 0 and free_bytes > 0:
                used_bytes = total_bytes - free_bytes
                disk_usage = round(used_bytes * 100.0 / total_bytes, 1)
                print(f"✅ Disk: {disk_usage}%")

        if cpu_usage > 0 or ram_usage > 0 or disk_usage > 0:
            print(f"✅ Базовые метрики: CPU={cpu_usage}%, RAM={ram_usage}%, Disk={disk_usage}%")

            return {
                "cpu": cpu_usage,
                "ram": ram_usage,
                "disk": disk_usage,
                "load_avg": "N/A",
                "uptime": "N/A",
                "os": os_info,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "available"
            }
        else:
            print("⚠️ Базовые метрики не получены")
            return None

    except Exception as e:
        print(f"❌ Ошибка получения базовых ресурсов: {e}")
        return None

# Альтернативный метод для совсем проблемных серверов
def get_windows_resources_simple_fallback(ip):
    """Очень простой fallback метод для проблемных Windows серверов"""
    print(f"🔧 Используем простой fallback для {ip}")
    
    # Проверяем базовую доступность
    if not check_ping(ip):
        return None
        
    rdp_available = check_port(ip, 3389, 3)
    
    return {
        "cpu": 0.0,
        "ram": 0.0,
        "disk": 0.0,
        "load_avg": "N/A",
        "uptime": "N/A",
        "os": "Windows Server (fallback)",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "available" if rdp_available else "limited",
        "access_method": "RDP" if rdp_available else "Ping",
        "server_type": get_windows_server_type(ip)
    }

def get_windows_resources_improved(ip, timeout=30):
    """Улучшенное получение ресурсов Windows сервера с учетом типа и версии сервера"""
    print(f"🔍 Проверяем Windows сервер {ip}")

    # Определяем тип сервера
    server_type = get_windows_server_type(ip)
    
    # Для доменных серверов (старые версии Windows) используем оптимизированный метод
    if server_type == "domain_servers":
        print(f"🔄 Используем оптимизированный метод для доменного сервера {ip}")
        resources = get_windows_resources_optimized_old(ip, 15)  # Уменьшаем timeout для старых серверов
        
        # Если даже оптимизированный метод не сработал, используем простой fallback
        if not resources:
            print(f"🔄 Оптимизированный метод не сработал, используем простой fallback для {ip}")
            resources = get_windows_resources_simple_fallback(ip)
            
        return resources
    
    # Для остальных серверов используем стандартный метод
    return get_windows_resources_standard(ip, timeout)

def get_windows_resources_standard(ip, timeout=30):
    """Стандартный метод получения ресурсов для обычных Windows серверов"""
    print(f"🔍 Проверяем Windows сервер {ip} (стандартный метод)")

    # Проверяем доступность сервера
    if not check_ping(ip):
        print(f"❌ Сервер {ip} недоступен (ping failed)")
        return None

    # Проверяем порты
    winrm_available = check_port(ip, 5985, 3)
    rdp_available = check_port(ip, 3389, 3)

    print(f"ℹ️ Порты: WinRM: {'✅' if winrm_available else '❌'}, RDP: {'✅' if rdp_available else '❌'}")

    # Пробуем WinRM если порт открыт
    if winrm_available:
        try:
            import winrm

            print(f"🔄 Пробуем WinRM подключение...")

            # Получаем специфичные учетные данные для этого сервера
            creds_to_try = get_windows_server_credentials(ip)

            for config in creds_to_try:
                username = config["username"]
                password = config["password"]

                print(f"🔑 Пробуем: {username}")

                try:
                    session = winrm.Session(
                        ip,
                        auth=(username, password),
                        transport='ntlm',
                        server_cert_validation='ignore',
                        read_timeout_sec=timeout
                    )

                    # Тестовая команда
                    result = session.run_cmd('echo test')
                    if result.status_code == 0:
                        print(f"✅ Аутентификация успешна")

                        # Получаем ресурсы
                        resources = get_windows_resources_via_systeminfo(session, ip)
                        if resources:
                            resources["access_method"] = "WinRM"
                            resources["server_type"] = get_windows_server_type(ip)
                            return resources
                        else:
                            print(f"⚠️ Ресурсы не получены, но аутентификация успешна")

                except Exception as e:
                    error_str = str(e)
                    if "Authentication" in error_str or "credentials" in error_str.lower():
                        print(f"❌ Ошибка аутентификации для {username}")
                    elif "Operation timed out" in error_str:
                        print(f"⏰ Таймаут для {username}")
                    else:
                        print(f"❌ Ошибка: {e}")
                    continue

            print("⚠️ Все учетные данные не подошли")

        except ImportError:
            print("❌ Модуль winrm не установлен")
        except Exception as e:
            print(f"❌ Ошибка WinRM: {e}")

    # Если RDP доступен, используем fallback
    if rdp_available:
        print(f"ℹ️ Используем RDP fallback")
        resources = get_windows_fallback_resources(ip)
        if resources:
            resources["access_method"] = "RDP"
            resources["server_type"] = get_windows_server_type(ip)
        return resources

    # Если сервер пингуется, но порты закрыты
    print(f"ℹ️ Сервер доступен по ping")
    resources = get_windows_fallback_resources(ip)
    if resources:
        resources["access_method"] = "Ping"
        resources["server_type"] = get_windows_server_type(ip)
    return resources

def get_windows_server_type(ip):
    """Определяет тип Windows сервера"""
    for server_type, config in WINDOWS_SERVER_CREDENTIALS.items():
        if ip in config["servers"]:
            return server_type
    return "unknown"

def get_windows_resources_via_systeminfo(session, ip):
    """Получаем метрики через systeminfo и PowerShell"""
    try:
        cpu_usage = 0.0
        ram_usage = 0.0
        disk_usage = 0.0
        os_info = "Windows Server"
        total_mem = 0
        available_mem = 0
        
        # 1. Получаем информацию о системе
        print("🔍 Получаем systeminfo...")
        result = session.run_cmd('systeminfo')
        if result.status_code == 0:
            output = result.std_out.decode('utf-8', errors='ignore')
            print(f"✅ Systeminfo выполнен")
            
            # Парсим systeminfo
            for line in output.split('\n'):
                line = line.strip()
                
                if 'OS Name' in line and 'Windows' in line:
                    os_info = line.split(':', 1)[1].strip()
                    print(f"✅ ОС: {os_info}")
                
                elif 'Total Physical Memory' in line:
                    try:
                        total_mem_str = line.split(':', 1)[1].strip()
                        total_mem = int(''.join(filter(str.isdigit, total_mem_str.split()[0])))
                        print(f"✅ Память: {total_mem} MB")
                    except:
                        pass
                
                elif 'Available Physical Memory' in line:
                    try:
                        available_mem_str = line.split(':', 1)[1].strip()
                        available_mem = int(''.join(filter(str.isdigit, available_mem_str.split()[0])))
                    except:
                        pass
            
            # Рассчитываем использование RAM
            if total_mem > 0 and available_mem > 0:
                ram_usage = round((total_mem - available_mem) * 100.0 / total_mem, 1)
                print(f"✅ RAM: {ram_usage}%")
        
        # 2. Получаем использование CPU
        print("🔍 Получаем CPU...")
        result = session.run_cmd('powershell -Command "Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average | Select-Object Average"')
        if result.status_code == 0:
            output = result.std_out.decode('utf-8', errors='ignore')
            for line in output.split('\n'):
                line = line.strip()
                numbers = re.findall(r'\d+\.?\d*', line)
                if numbers:
                    try:
                        cpu_usage = float(numbers[0])
                        print(f"✅ CPU: {cpu_usage}%")
                        break
                    except:
                        pass
        
        # 3. Получаем использование диска через умную функцию
        print("🔍 Получаем Disk...")
        disk_usage = get_windows_disk_usage(session, ip)
        if disk_usage > 0:
            print(f"✅ Disk: {disk_usage}%")
        
        if cpu_usage > 0 or ram_usage > 0 or disk_usage > 0:
            print(f"✅ Метрики: CPU={cpu_usage}%, RAM={ram_usage}%, Disk={disk_usage}%")
            
            return {
                "cpu": cpu_usage,
                "ram": ram_usage,
                "disk": disk_usage,
                "load_avg": "N/A",
                "uptime": "N/A",
                "os": os_info,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "available"
            }
        else:
            print("⚠️ Метрики не получены")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_windows_fallback_resources(ip, method="unknown"):
    """Fallback метод с информацией о методе доступа"""
    print(f"🔄 Fallback для {ip} ({method})")
    
    # Получаем информацию из ping
    try:
        ping_result = subprocess.run(['ping', '-c', '1', ip], 
                                   capture_output=True, text=True, timeout=5)
        ttl_info = "неизвестно"
        os_guess = "Windows"
        
        if ping_result.returncode == 0 and "ttl=" in ping_result.stdout.lower():
            for line in ping_result.stdout.split('\n'):
                if 'ttl=' in line.lower():
                    try:
                        ttl = int(line.split('ttl=')[1].split()[0])
                        if ttl <= 64:
                            os_guess = "Windows 10/11"
                        elif ttl <= 128:
                            os_guess = "Windows Server"
                        ttl_info = str(ttl)
                    except:
                        pass
        
        return {
            "cpu": 0.0,
            "ram": 0.0,
            "disk": 0.0,
            "load_avg": "N/A",
            "uptime": "N/A",
            "os": os_guess,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "status": "available",
            "ping": True,
            "ttl": ttl_info,
            "access_method": method,
            "server_type": get_windows_server_type(ip)
        }
    except:
        return {
            "cpu": 0.0,
            "ram": 0.0,
            "disk": 0.0,
            "load_avg": "N/A",
            "uptime": "N/A",
            "os": "Windows",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "status": "available",
            "ping": False,
            "ttl": "неизвестно",
            "access_method": method,
            "server_type": get_windows_server_type(ip)
        }

def get_linux_resources_improved(ip, timeout=20):
    """ИСПРАВЛЕННОЕ получение ресурсов Linux сервера с поддержкой ZFS"""
    print(f"🔍 Проверяем Linux ресурсы для {ip}")
    
    if not check_port(ip, 22, 3):
        print(f"❌ Порт 22 закрыт для {ip}")
        return None
    
    resources = {
        "cpu": 0.0,
        "ram": 0.0, 
        "disk": 0.0,
        "load_avg": "N/A",
        "uptime": "N/A",
        "os": "Linux",
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
                iowait = int(parts[5]) if len(parts) > 5 else 0
                
                total = user + nice + system + idle + iowait
                if total > 0:
                    resources["cpu"] = round((user + nice + system) * 100.0 / total, 1)
                    print(f"✅ CPU: {resources['cpu']}%")
        except Exception as e:
            print(f"❌ Ошибка парсинга CPU: {e}")
    
    # RAM usage - ИСПРАВЛЕННАЯ ЛОГИКА
    print("🔍 Получаем RAM...")
    
    # Пробуем разные команды для получения RAM
    ram_commands = [
        "free -b | head -2",  # Байты для точности
        "free -m | head -2",  # Мегабайты
        "cat /proc/meminfo",  # Информация о памяти
        "free | head -2"      # Простой free
    ]
    
    for cmd in ram_commands:
        success, output, error = run_ssh_command(ip, cmd, 5)
        if success and output:
            print(f"✅ Команда RAM: {cmd}")
            print(f"Вывод RAM: {output[:200]}...")
            
            try:
                # Метод 1: Парсим вывод free -b (байты)
                if "Mem:" in output and "free -b" in cmd:
                    lines = output.split('\n')
                    for line in lines:
                        if line.startswith('Mem:'):
                            parts = line.split()
                            if len(parts) >= 7:
                                total_mem = int(parts[1])  # Total
                                used_mem = int(parts[2])   # Used
                                if total_mem > 0:
                                    ram_usage = round(used_mem * 100.0 / total_mem, 1)
                                    resources["ram"] = ram_usage
                                    print(f"✅ RAM (free -b): {ram_usage}%")
                                    break
                
                # Метод 2: Парсим вывод free -m (мегабайты)
                elif "Mem:" in output and "free -m" in cmd:
                    lines = output.split('\n')
                    for line in lines:
                        if line.startswith('Mem:'):
                            parts = line.split()
                            if len(parts) >= 7:
                                total_mem = int(parts[1]) * 1024 * 1024  # Convert MB to bytes
                                used_mem = int(parts[2]) * 1024 * 1024   # Convert MB to bytes
                                if total_mem > 0:
                                    ram_usage = round(used_mem * 100.0 / total_mem, 1)
                                    resources["ram"] = ram_usage
                                    print(f"✅ RAM (free -m): {ram_usage}%")
                                    break
                
                # Метод 3: Парсим /proc/meminfo
                elif "MemTotal:" in output and "MemAvailable:" in output:
                    mem_total = 0
                    mem_available = 0
                    
                    for line in output.split('\n'):
                        if line.startswith('MemTotal:'):
                            mem_total = int(line.split()[1]) * 1024  # Convert KB to bytes
                        elif line.startswith('MemAvailable:'):
                            mem_available = int(line.split()[1]) * 1024  # Convert KB to bytes
                    
                    if mem_total > 0 and mem_available > 0:
                        used_mem = mem_total - mem_available
                        ram_usage = round(used_mem * 100.0 / mem_total, 1)
                        resources["ram"] = ram_usage
                        print(f"✅ RAM (meminfo): {ram_usage}%")
                        break
                
                # Метод 4: Простой free
                elif "Mem:" in output:
                    lines = output.split('\n')
                    for line in lines:
                        if line.startswith('Mem:'):
                            parts = line.split()
                            if len(parts) >= 7:
                                total_mem = int(parts[1])
                                used_mem = int(parts[2])
                                if total_mem > 0:
                                    # Если числа маленькие, это вероятно в KB
                                    if total_mem < 1000000:  # Меньше 1GB в KB
                                        total_mem *= 1024  # Convert KB to bytes
                                        used_mem *= 1024   # Convert KB to bytes
                                    
                                    ram_usage = round(used_mem * 100.0 / total_mem, 1)
                                    resources["ram"] = ram_usage
                                    print(f"✅ RAM (simple free): {ram_usage}%")
                                    break
                
                if resources["ram"] > 0:
                    break
                    
            except Exception as e:
                print(f"❌ Ошибка парсинга RAM для команды {cmd}: {e}")
                continue
    
    # Disk usage - ИСПРАВЛЕННАЯ ЛОГИКА ДЛЯ ZFS
    print("🔍 Получаем Disk usage...")
    
    # Определяем тип сервера для выбора метода проверки диска
    is_proxmox = ip.startswith("192.168.30.")  # Proxmox серверы
    is_backup = ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"]  # bup серверы
    
    if is_proxmox or is_backup:
        # Для Proxmox и бэкап серверов используем zpool list
        print(f"🔍 Используем ZFS для {ip}")
        
        # Определяем имя пула
        if ip == "192.168.20.32":  # bup сервер
            pool_name = "zfs"
        else:  # Proxmox и другие бэкап серверы
            pool_name = "rpool"
        
        zfs_commands = [
            f"zpool list -H -o name,size,alloc,free {pool_name}",
            f"zpool list -H -o allocated,size {pool_name}",
            "zpool list -H -o name,size,alloc,free",
            "zpool list -H -o allocated,size"
        ]
        
        for zfs_cmd in zfs_commands:
            success, output, error = run_ssh_command(ip, zfs_cmd, 5)
            if success and output:
                print(f"✅ ZFS команда: {zfs_cmd}")
                print(f"ZFS вывод: {output}")
                
                try:
                    parts = output.strip().split('\t')
                    print(f"ZFS части: {parts}")
                    
                    if len(parts) >= 3:
                        # Формат: name size alloc free
                        if len(parts) == 4:
                            size_str = parts[1]
                            alloc_str = parts[2]
                        # Формат: alloc size  
                        elif len(parts) == 2:
                            alloc_str = parts[0]
                            size_str = parts[1]
                        else:
                            continue
                        
                        # Парсим размеры (удаляем суффиксы G, T и т.д.)
                        def parse_size(size_str):
                            size_str = size_str.upper().strip()
                            multiplier = 1
                            
                            if size_str.endswith('T'):
                                multiplier = 1024 * 1024 * 1024 * 1024
                                size_str = size_str[:-1]
                            elif size_str.endswith('G'):
                                multiplier = 1024 * 1024 * 1024
                                size_str = size_str[:-1]
                            elif size_str.endswith('M'):
                                multiplier = 1024 * 1024
                                size_str = size_str[:-1]
                            elif size_str.endswith('K'):
                                multiplier = 1024
                                size_str = size_str[:-1]
                            
                            try:
                                return float(size_str) * multiplier
                            except:
                                return 0
                        
                        total_size = parse_size(size_str)
                        used_size = parse_size(alloc_str)
                        
                        if total_size > 0 and used_size > 0:
                            disk_usage = round(used_size * 100.0 / total_size, 1)
                            resources["disk"] = disk_usage
                            print(f"✅ ZFS Disk: {disk_usage}% (Total: {total_size}, Used: {used_size})")
                            break
                            
                except Exception as e:
                    print(f"❌ Ошибка парсинга ZFS: {e}")
                    continue
    else:
        # Для обычных Linux серверов используем стандартный df
        success, output, error = run_ssh_command(ip, "df / | tail -1", 5)
        if success and output:
            try:
                parts = output.split()
                if len(parts) >= 5:
                    usage_str = parts[4]
                    if usage_str.endswith('%'):
                        resources["disk"] = float(usage_str[:-1])
                        print(f"✅ Standard Disk: {resources['disk']}%")
            except Exception as e:
                print(f"❌ Ошибка парсинга Disk: {e}")
    
    # Load average
    success, output, error = run_ssh_command(ip, "cat /proc/loadavg", 5)
    if success and output:
        try:
            parts = output.split()
            if len(parts) >= 3:
                resources["load_avg"] = f"{parts[0]}, {parts[1]}, {parts[2]}"
        except:
            pass
    
    # Uptime
    success, output, error = run_ssh_command(ip, "cat /proc/uptime", 5)
    if success and output:
        try:
            uptime_seconds = float(output.split()[0])
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            resources["uptime"] = f"{days}d {hours}h"
        except:
            pass
    
    print(f"✅ Итоговые метрики для {ip}: CPU={resources['cpu']}%, RAM={resources['ram']}%, Disk={resources['disk']}%")
    return resources

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

def format_resource_message_compact(server_name, resources, alerts=None):
    """Компактное сообщение с ресурсами сервера"""
    if not resources:
        return f"❌ {server_name}"

    status_icon = "🟢"
    if alerts:
        for alert in alerts:
            if "🚨" in alert:
                status_icon = "🔴"
                break
            elif "⚠️" in alert:
                status_icon = "🟡"

    cpu = resources.get("cpu", 0)
    ram = resources.get("ram", 0)
    disk = resources.get("disk", 0)
    access_method = resources.get("access_method", "")
    server_type = resources.get("server_type", "")

    message = f"{status_icon} {server_name}"

    parts = []
    
    # Показываем метрики если они есть
    if cpu > 0:
        parts.append(f"C:{cpu}%")
    if ram > 0:
        parts.append(f"R:{ram}%")
    if disk > 0:
        parts.append(f"D:{disk}%")
    
    # Если нет метрик, показываем статус WinRM
    if not parts:
        if access_method == "WinRM":
            parts.append("🪟✅")
        elif "WinRM" in access_method:
            parts.append("🪟❌")
        else:
            parts.append("🪟")

    if parts:
        message += ": " + " ".join(parts)
        
    # Добавляем тип сервера если известен
    if server_type and server_type != "unknown":
        message += f" [{server_type}]"

    return message

def format_resource_message(server_name, resources, alerts=None):
    """Полное сообщение с ресурсами сервера"""
    if not resources:
        return f"❌ {server_name}: данные недоступны"

    status_icon = "🟢"
    if alerts:
        for alert in alerts:
            if "🚨" in alert:
                status_icon = "🔴"
                break
            elif "⚠️" in alert:
                status_icon = "🟡"

    message = f"{status_icon} **{server_name}**\n"
    message += f"• **CPU:** {resources.get('cpu', 0)}%\n"
    message += f"• **RAM:** {resources.get('ram', 0)}%\n"
    message += f"• **Disk:** {resources.get('disk', 0)}%\n"
    message += f"• **Load:** {resources.get('load_avg', 'N/A')}\n"
    message += f"• **Uptime:** {resources.get('uptime', 'N/A')}\n"
    message += f"• **OS:** {resources.get('os', 'Unknown')}\n"
    message += f"• **Тип:** {resources.get('server_type', 'unknown')}\n"
    message += f"• **Метод:** {resources.get('access_method', 'unknown')}\n"
    message += f"• **Время:** {resources.get('timestamp', 'N/A')}"

    if alerts:
        message += "\n\n**⚠️ Проблемы:**\n" + "\n".join(alerts)

    return message
