"""
/modules/resources.py
Server Monitoring System v4.14.36
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server resource monitoring module
Система мониторинга серверов
Версия: 4.14.36
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль проверки ресурсов серверов
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from lib.logging import debug_log
from lib.utils import progress_bar
from config.settings import (
    RESOURCE_CHECK_INTERVAL, 
    RESOURCE_ALERT_INTERVAL,
    RESOURCE_THRESHOLDS,
    RESOURCE_ALERT_THRESHOLDS
)

class ResourcesChecker:
    """Класс для проверки ресурсов серверов"""
    
    def __init__(self):
        """Инициализация проверяющего ресурсы"""
        self.resource_history = {}  # История ресурсов по IP
        self.resource_alerts_sent = {}  # Отправленные алерты
        self.last_resource_check = datetime.now()
        
    def check_linux_resources(self, ip: str) -> Optional[Dict[str, float]]:
        """
        Проверяет ресурсы Linux сервера через SSH
        
        Args:
            ip: IP адрес сервера
            
        Returns:
            Dict с ресурсами или None при ошибке
        """
        try:
            # Динамический импорт чтобы избежать циклических зависимостей
            from extensions.server_checks import get_linux_resources_improved
            
            resources = get_linux_resources_improved(ip)
            
            if resources:
                debug_log(f"✅ Linux ресурсы {ip}: CPU {resources.get('cpu', 0)}%, "
                         f"RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%")
                return resources
            else:
                debug_log(f"❌ Не удалось получить ресурсы Linux сервера {ip}")
                return None
                
        except Exception as e:
            debug_log(f"💥 Ошибка проверки Linux ресурсов {ip}: {e}")
            return None
    
    def check_windows_resources(self, ip: str) -> Optional[Dict[str, float]]:
        """
        Проверяет ресурсы Windows сервера
        
        Args:
            ip: IP адрес сервера
            
        Returns:
            Dict с ресурсами или None при ошибке
        """
        try:
            # Динамический импорт чтобы избежать циклических зависимостей
            from extensions.server_checks import get_windows_resources_improved
            
            resources = get_windows_resources_improved(ip)
            
            if resources:
                debug_log(f"✅ Windows ресурсы {ip}: CPU {resources.get('cpu', 0)}%, "
                         f"RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%")
                return resources
            else:
                debug_log(f"❌ Не удалось получить ресурсы Windows сервера {ip}")
                return None
                
        except Exception as e:
            debug_log(f"💥 Ошибка проверки Windows ресурсов {ip}: {e}")
            return None
    
    def check_server_resources(self, server: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Проверяет ресурсы одного сервера по его типу
        
        Args:
            server: Словарь с информацией о сервере
            
        Returns:
            Tuple[bool, Optional[Dict]]: (успешно ли, ресурсы)
        """
        ip = server.get("ip")
        server_type = server.get("type")
        name = server.get("name", ip)
        
        if not ip:
            return False, None
        
        try:
            resources = None
            
            if server_type == "ssh":
                resources = self.check_linux_resources(ip)
            elif server_type == "rdp":
                resources = self.check_windows_resources(ip)
            else:
                debug_log(f"⚠️ Неподдерживаемый тип сервера для проверки ресурсов: {server_type}")
                return False, None
            
            success = resources is not None
            
            if success:
                # Добавляем информацию о сервере в ресурсы
                resources["server_name"] = name
                resources["server_ip"] = ip
                resources["server_type"] = server_type
                resources["check_time"] = datetime.now()
                
                # Сохраняем в историю
                self._add_to_history(ip, resources)
            
            return success, resources
            
        except Exception as e:
            debug_log(f"💥 Критическая ошибка проверки ресурсов {name}: {e}")
            return False, None
    
    def check_multiple_resources(self, servers: List[Dict], 
                               progress_callback=None) -> Tuple[List[Dict], Dict]:
        """
        Проверяет ресурсы нескольких серверов
        
        Args:
            servers: Список серверов
            progress_callback: Функция для обновления прогресса
            
        Returns:
            Tuple[List[Dict], Dict]: (результаты, статистика)
        """
        results = []
        stats = {
            "total": len(servers),
            "success": 0,
            "failed": 0,
            "high_cpu": 0,
            "high_ram": 0,
            "high_disk": 0
        }
        
        debug_log(f"🔍 Начинаю проверку ресурсов {len(servers)} серверов...")
        
        for i, server in enumerate(servers):
            if progress_callback:
                progress = (i + 1) / len(servers) * 100
                progress_callback(progress, f"Проверяю {server.get('name')}...")
            
            success, resources = self.check_server_resources(server)
            
            result = {
                "server": server,
                "success": success,
                "resources": resources,
                "check_time": datetime.now()
            }
            
            results.append(result)
            
            if success:
                stats["success"] += 1
                
                # Проверяем пороги
                cpu = resources.get("cpu", 0)
                ram = resources.get("ram", 0)
                disk = resources.get("disk", 0)
                
                if cpu >= RESOURCE_THRESHOLDS.get("cpu_warning", 80):
                    stats["high_cpu"] += 1
                if ram >= RESOURCE_THRESHOLDS.get("ram_warning", 85):
                    stats["high_ram"] += 1
                if disk >= RESOURCE_THRESHOLDS.get("disk_warning", 80):
                    stats["high_disk"] += 1
            else:
                stats["failed"] += 1
            
            # Небольшая задержка между проверками
            time.sleep(1)
        
        debug_log(f"📊 Ресурсы проверены: {stats['success']}/{stats['total']} успешно")
        
        return results, stats
    
    def _add_to_history(self, ip: str, resources: Dict) -> None:
        """Добавляет ресурсы в историю"""
        if ip not in self.resource_history:
            self.resource_history[ip] = []
        
        self.resource_history[ip].append(resources)
        
        # Ограничиваем историю последними 10 записями
        if len(self.resource_history[ip]) > 10:
            self.resource_history[ip] = self.resource_history[ip][-10:]
    
    def check_resource_alerts(self, ip: str, current_resource: Dict) -> List[str]:
        """
        Проверяет условия для отправки алертов по ресурсам
        
        Args:
            ip: IP адрес
            current_resource: Текущие ресурсы
            
        Returns:
            List[str]: Список сообщений для алертов
        """
        alerts = []
        server_name = current_resource.get("server_name", ip)
        
        # Получаем историю (исключая текущую запись)
        history = self.resource_history.get(ip, [])[:-1]
        
        # Проверка диска (одна проверка)
        disk_usage = current_resource.get("disk", 0)
        if disk_usage >= RESOURCE_ALERT_THRESHOLDS.get("disk_alert", 95):
            alert_key = f"{ip}_disk"
            if self._should_send_alert(alert_key):
                alerts.append(f"💾 **Дисковое пространство** на {server_name}: {disk_usage}% "
                            f"(превышен порог {RESOURCE_ALERT_THRESHOLDS.get('disk_alert', 95)}%)")
                self.resource_alerts_sent[alert_key] = datetime.now()
        
        # Проверка CPU (две проверки подряд)
        cpu_usage = current_resource.get("cpu", 0)
        if cpu_usage >= RESOURCE_ALERT_THRESHOLDS.get("cpu_alert", 99):
            if len(history) >= 1:
                prev_cpu = history[-1].get("cpu", 0)
                if prev_cpu >= RESOURCE_ALERT_THRESHOLDS.get("cpu_alert", 99):
                    alert_key = f"{ip}_cpu"
                    if self._should_send_alert(alert_key):
                        alerts.append(f"💻 **Процессор** на {server_name}: {prev_cpu}% → {cpu_usage}% "
                                    f"(2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS.get('cpu_alert', 99)}%)")
                        self.resource_alerts_sent[alert_key] = datetime.now()
        
        # Проверка RAM (две проверки подряд)
        ram_usage = current_resource.get("ram", 0)
        if ram_usage >= RESOURCE_ALERT_THRESHOLDS.get("ram_alert", 99):
            if len(history) >= 1:
                prev_ram = history[-1].get("ram", 0)
                if prev_ram >= RESOURCE_ALERT_THRESHOLDS.get("ram_alert", 99):
                    alert_key = f"{ip}_ram"
                    if self._should_send_alert(alert_key):
                        alerts.append(f"🧠 **Память** на {server_name}: {prev_ram}% → {ram_usage}% "
                                    f"(2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS.get('ram_alert', 99)}%)")
                        self.resource_alerts_sent[alert_key] = datetime.now()
        
        return alerts
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """Проверяет, можно ли отправлять алерт"""
        if alert_key not in self.resource_alerts_sent:
            return True
        
        last_sent = self.resource_alerts_sent[alert_key]
        time_since_last = (datetime.now() - last_sent).total_seconds()
        
        return time_since_last > RESOURCE_ALERT_INTERVAL
    
    def get_resource_history(self, ip: str, limit: int = 5) -> List[Dict]:
        """Получает историю ресурсов для сервера"""
        history = self.resource_history.get(ip, [])
        return history[-limit:] if limit else history
    
    def clear_history(self, ip: str = None) -> None:
        """Очищает историю ресурсов"""
        if ip:
            if ip in self.resource_history:
                del self.resource_history[ip]
            debug_log(f"🗑️ История ресурсов очищена для {ip}")
        else:
            self.resource_history.clear()
            debug_log("🗑️ Вся история ресурсов очищена")

# Глобальный экземпляр для импорта
resources_checker = ResourcesChecker()

def check_resources(update, context):
    """
    Ручной запуск проверки ресурсов всех серверов (через Telegram)
    """
    try:
        from core.config_manager import config_manager

        servers = config_manager.get_servers()
        if not servers:
            return

        resources_checker.check_multiple_resources(servers)

        update.callback_query.answer("Проверка ресурсов запущена")

    except Exception as e:
        debug_log(f"💥 Ошибка ручного запуска проверки ресурсов: {e}")
