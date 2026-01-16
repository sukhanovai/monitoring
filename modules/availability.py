"""
/app/modules/availability.py
Server Monitoring System v7.1.25
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server Availability Monitoring Module
Система мониторинга серверов
Версия: 7.1.25
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль мониторинга доступности серверов
"""

import threading
import time
from datetime import datetime, timedelta
from config.db_settings import CHECK_INTERVAL, MAX_FAIL_TIME
from lib.logging import debug_log

# Импортируем проверки серверов
try:
    from extensions.server_checks import initialize_servers, check_server_availability
except ImportError:
    debug_log("⚠️ Модуль server_checks недоступен", force=True)
    check_server_availability = None

class AvailabilityMonitor:
    """Класс мониторинга доступности серверов"""
    
    def __init__(self):
        self.server_status = {}
        self.monitoring_active = True
        self.servers = []
        self.last_check_time = datetime.now()
        
    def initialize(self):
        """Инициализация мониторинга"""
        if not check_server_availability:
            debug_log("❌ Модуль проверок недоступен", force=True)
            return False
            
        self.servers = initialize_servers()
        monitor_server_ip = "192.168.20.2"
        
        # Исключаем сервер мониторинга
        self.servers = [s for s in self.servers if s["ip"] != monitor_server_ip]
        
        # Инициализация статусов
        for server in self.servers:
            self.server_status[server["ip"]] = {
                "last_up": datetime.now(),
                "alert_sent": False,
                "name": server["name"],
                "type": server["type"]
            }
            
        debug_log(f"✅ Мониторинг доступности инициализирован для {len(self.servers)} серверов")
        return True
        
    def check_server(self, server):
        """Проверка одного сервера"""
        try:
            return check_server_availability(server)
        except Exception as e:
            debug_log(f"❌ Ошибка проверки {server['name']}: {e}")
            return False
            
    def handle_server_up(self, ip, status, current_time):
        """Обработка доступного сервера"""
        if status["alert_sent"]:
            downtime = (current_time - status["last_up"]).total_seconds()
            from bot.handlers.commands import send_alert
            send_alert(f"✅ {status['name']} ({ip}) доступен (простой: {int(downtime//60)} мин)")

        self.server_status[ip] = {
            "last_up": current_time,
            "alert_sent": False,
            "name": status["name"],
            "type": status["type"]
        }

    def handle_server_down(self, ip, status, current_time):
        """Обработка недоступного сервера"""
        downtime = (current_time - status["last_up"]).total_seconds()
        
        if downtime >= MAX_FAIL_TIME and not status["alert_sent"]:
            from bot.handlers.commands import send_alert
            send_alert(f"🚨 {status['name']} ({ip}) не отвечает (проверка: {status['type'].upper()})")
            self.server_status[ip]["alert_sent"] = True
    
    def get_current_status(self):
        """Получить текущий статус всех серверов"""
        results = {"failed": [], "ok": []}
        if not self.servers:
            if not self.initialize():
                debug_log("❌ Нет данных о серверах для проверки", force=True)
                return results

        for server in self.servers:
            try:
                is_up = self.check_server(server)
                if is_up:
                    results["ok"].append(server)
                else:
                    results["failed"].append(server)
            except Exception as e:
                debug_log(f"❌ Ошибка проверки {server['name']}: {e}")
                results["failed"].append(server)
                
        return results
    
    def start_monitoring(self):
        """Запуск цикла мониторинга"""
        if not self.initialize():
            debug_log("❌ Не удалось инициализировать мониторинг доступности", force=True)
            return
            
        debug_log("🔄 Запуск цикла мониторинга доступности")
        
        while True:
            if self.monitoring_active:
                self.last_check_time = datetime.now()
                
                for server in self.servers:
                    try:
                        ip = server["ip"]
                        status = self.server_status.get(ip, {})
                        
                        # Исключаем сервер мониторинга
                        if ip == "192.168.20.2":
                            self.server_status[ip]["last_up"] = self.last_check_time
                            continue
                            
                        is_up = self.check_server(server)
                        
                        if is_up:
                            self.handle_server_up(ip, status, self.last_check_time)
                        else:
                            self.handle_server_down(ip, status, self.last_check_time)
                            
                    except Exception as e:
                        debug_log(f"❌ Ошибка мониторинга {server['name']}: {e}")
                        
            time.sleep(CHECK_INTERVAL)

# Глобальный экземпляр мониторинга
availability_monitor = AvailabilityMonitor()


class AvailabilityChecker:
    """Утилиты для разовых проверок доступности."""

    def __init__(self):
        self.last_check_time = None

    def check_single_server(self, server):
        """Проверяет доступность одного сервера."""
        if not check_server_availability:
            debug_log("❌ Модуль проверок недоступен", force=True)
            return False

        try:
            return check_server_availability(server)
        except Exception as e:
            debug_log(f"❌ Ошибка проверки {server.get('name')}: {e}")
            return False

    def check_multiple_servers(self, servers, progress_callback=None):
        """Проверяет доступность нескольких серверов."""
        results = {"up": [], "down": [], "ok": [], "failed": []}
        total = len(servers)

        for index, server in enumerate(servers):
            if progress_callback:
                progress = (index + 1) / total * 100 if total else 100
                progress_callback(progress, f"Проверяем {server.get('name', 'сервер')}...")

            is_up = self.check_single_server(server)
            if is_up:
                results["up"].append(server)
                results["ok"].append(server)
            else:
                results["down"].append(server)
                results["failed"].append(server)

        self.last_check_time = datetime.now()
        return results


# Глобальный экземпляр чекера доступности
availability_checker = AvailabilityChecker()
