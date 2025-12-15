"""
Server Monitoring System v4.9.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Network utilities
Система мониторинга серверов
Версия: 4.9.1
Автор: Александр Суханов (c)
Лицензия: MIT
Сетевые утилиты
"""

import socket
import subprocess
import time
from typing import Optional, Tuple
from lib.logging import debug_log

def check_port(ip: str, port: int, timeout: int = 5) -> bool:
    """
    Проверка доступности порта
    
    Args:
        ip: IP адрес
        port: Номер порта
        timeout: Таймаут в секундах
        
    Returns:
        True если порт доступен
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        debug_log(f"Port check error for {ip}:{port}: {e}", force=True)
        return False

def check_ping(ip: str, timeout: int = 10) -> bool:
    """
    Проверка доступности через ping
    
    Args:
        ip: IP адрес
        timeout: Таймаут в секундах
        
    Returns:
        True если сервер отвечает на ping
    """
    try:
        result = subprocess.run(
            ['ping', '-c', '2', '-W', '2', ip],
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        debug_log(f"Ping timeout for {ip}", force=True)
        return False
    except Exception as e:
        debug_log(f"Ping error for {ip}: {e}", force=True)
        return False

def resolve_hostname(ip: str) -> str:
    """
    Разрешает IP в hostname
    
    Args:
        ip: IP адрес
        
    Returns:
        Hostname или оригинальный IP при ошибке
    """
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except socket.herror:
        return ip
    except Exception as e:
        debug_log(f"Hostname resolution error for {ip}: {e}", force=True)
        return ip

def get_network_latency(ip: str, count: int = 3) -> Optional[float]:
    """
    Измеряет сетевую задержку
    
    Args:
        ip: IP адрес
        count: Количество попыток
        
    Returns:
        Средняя задержка в мс или None при ошибке
    """
    try:
        total_time = 0
        successful = 0
        
        for _ in range(count):
            start_time = time.time()
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Парсим время из вывода ping
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        try:
                            time_str = line.split('time=')[1].split(' ')[0]
                            latency = float(time_str)
                            total_time += latency
                            successful += 1
                        except (ValueError, IndexError):
                            pass
        
        if successful > 0:
            return total_time / successful
        return None
        
    except Exception as e:
        debug_log(f"Latency measurement error for {ip}: {e}", force=True)
        return None