"""
/modules/availability.py
Server Monitoring System v4.14.8
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server availability check module
Система мониторинга серверов
Версия: 4.14.8
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль проверки доступности серверов
"""

import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

from lib.logging import debug_log
from config.settings import MAX_FAIL_TIME
from core.checker import ServerChecker

class AvailabilityChecker:
    """Класс для проверки доступности серверов"""
    
    def __init__(self, checker: ServerChecker = None):
        """Инициализация проверяющего"""
        self.checker = checker or ServerChecker()
        self.server_status = {}  # Кэш статусов серверов
        
    def check_server_availability(self, server: Dict) -> Tuple[bool, str]:
        """
        Проверяет доступность одного сервера
        
        Args:
            server: Словарь с информацией о сервере
            
        Returns:
            Tuple[bool, str]: (доступен ли, метод проверки)
        """
        ip = server.get("ip", "")
        server_type = server.get("type", "ssh")
        name = server.get("name", ip)
        
        try:
            is_up = False
            method = ""
            
            if server_type == "rdp":
                # Проверка Windows через RDP порт
                is_up = self.checker.check_port(ip, 3389)
                method = "RDP port check"
            elif server_type == "ping":
                # Простая проверка ping
                is_up = self.checker.check_ping(ip)
                method = "Ping"
            else:  # ssh и другие
                # Проверка через SSH
                is_up = self.checker.check_ssh_universal(ip)
                method = "SSH"
            
            debug_log(f"🔍 {name} ({ip}): {'🟢 доступен' if is_up else '🔴 недоступен'} - {method}")
            return is_up, method
            
        except Exception as e:
            debug_log(f"❌ Ошибка проверки {name} ({ip}): {e}")
            return False, f"Error: {str(e)[:50]}"
    
    def check_multiple_servers(self, servers: List[Dict]) -> Dict[str, List]:
        """
        Проверяет доступность нескольких серверов
        
        Args:
            servers: Список серверов для проверки
            
        Returns:
            Dict: {'up': [...], 'down': [...]}
        """
        results = {"up": [], "down": []}
        
        debug_log(f"🔍 Начинаю проверку {len(servers)} серверов...")
        
        for server in servers:
            is_up, method = self.check_server_availability(server)
            
            server_copy = server.copy()
            server_copy["check_method"] = method
            server_copy["check_time"] = datetime.now()
            
            if is_up:
                results["up"].append(server_copy)
            else:
                results["down"].append(server_copy)
            
            # Небольшая задержка между проверками
            time.sleep(0.5)
        
        debug_log(f"📊 Результаты проверки: {len(results['up'])} доступно, {len(results['down'])} недоступно")
        return results
    
    def check_server_with_retry(self, server: Dict, retries: int = 2) -> Tuple[bool, str]:
        """
        Проверяет сервер с повторными попытками
        
        Args:
            server: Словарь с информацией о сервере
            retries: Количество повторных попыток
            
        Returns:
            Tuple[bool, str]: (доступен ли, метод проверки)
        """
        for attempt in range(retries + 1):
            is_up, method = self.check_server_availability(server)
            
            if is_up:
                return True, method
            
            if attempt < retries:
                debug_log(f"🔄 Повторная попытка {attempt + 1}/{retries} для {server.get('name')}")
                time.sleep(2)
        
        return False, f"Failed after {retries} retries: {method}"
    
    def get_server_status(self, server: Dict) -> Dict[str, Any]:
        """
        Получает полный статус сервера
        
        Args:
            server: Словарб с информацией о сервере
            
        Returns:
            Dict: Статус сервера
        """
        ip = server.get("ip")
        name = server.get("name", ip)
        
        # Проверяем доступность
        is_up, method = self.check_server_availability(server)
        
        # Получаем текущее время
        current_time = datetime.now()
        
        # Проверяем есть ли статус в кэше
        if ip in self.server_status:
            cached_status = self.server_status[ip]
            
            # Проверяем время последней проверки
            last_check = cached_status.get("last_check")
            if last_check and (current_time - last_check).total_seconds() < 60:
                # Возвращаем кэшированный статус если он актуален
                return cached_status
        
        # Создаем новый статус
        status = {
            "ip": ip,
            "name": name,
            "type": server.get("type"),
            "is_up": is_up,
            "check_method": method,
            "last_check": current_time,
            "alert_sent": False,
            "downtime_start": None if is_up else current_time
        }
        
        # Обновляем кэш
        self.server_status[ip] = status
        
        return status
    
    def update_server_status(self, server: Dict, global_status: Dict) -> None:
        """
        Обновляет глобальный статус сервера и обрабатывает алерты
        
        Args:
            server: Информация о сервере
            global_status: Глобальный словарь статусов
        """
        ip = server.get("ip")
        name = server.get("name", ip)
        current_time = datetime.now()
        
        # Получаем текущий статус
        is_up, method = self.check_server_availability(server)
        
        if is_up:
            # Сервер доступен
            if ip in global_status and global_status[ip].get("alert_sent"):
                # Сервер восстановился после простоя
                downtime_start = global_status[ip].get("downtime_start")
                downtime = 0
                if downtime_start:
                    downtime = (current_time - downtime_start).total_seconds()
                
                debug_log(f"✅ {name} ({ip}) восстановился после простоя {int(downtime)} сек")
                
                # Сбрасываем флаг алерта
                global_status[ip]["alert_sent"] = False
            
            # Обновляем статус
            global_status[ip] = {
                "last_up": current_time,
                "alert_sent": False,
                "name": name,
                "type": server.get("type"),
                "downtime_start": None
            }
            
        else:
            # Сервер недоступен
            if ip not in global_status:
                # Первый раз недоступен
                global_status[ip] = {
                    "last_up": current_time,
                    "alert_sent": False,
                    "name": name,
                    "type": server.get("type"),
                    "downtime_start": current_time
                }
            else:
                # Уже был недоступен
                downtime_start = global_status[ip].get("downtime_start", current_time)
                downtime = (current_time - downtime_start).total_seconds()
                
                # Проверяем нужно ли отправлять алерт
                if downtime >= MAX_FAIL_TIME and not global_status[ip].get("alert_sent"):
                    global_status[ip]["alert_sent"] = True
                    return True  # Нужно отправить алерт
        
        return False  # Алерт не нужен

# Глобальный экземпляр для импорта
availability_checker = AvailabilityChecker()