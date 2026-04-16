"""
/app/modules/targeted_checks.py
Server Monitoring System v8.50.144
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server Spot Check Module
Система мониторинга серверов
Версия: 8.50.144
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль точечных проверок серверов
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lib.common import debug_log
from lib.helpers import progress_bar

class TargetedChecks:
    """Класс для точечных проверок серверов"""
    
    def __init__(self):
        self.server_cache = None
    
    def get_all_servers(self):
        """Получить все серверы из единого источника (настройки)"""
        from core.config_manager import config_manager

        # include_disabled=True, чтобы список в точечных проверках
        # совпадал со списком в «Настройки → Серверы».
        servers = config_manager.get_all_servers(include_disabled=True)
        self.server_cache = servers
        return servers
    
    def get_server_by_selection(self, server_id):
        """Получить сервер по ID (ip или name)"""
        servers = self.get_all_servers()
        
        # Поиск по IP
        for server in servers:
            if server["ip"] == server_id:
                return server
        
        # Поиск по имени
        for server in servers:
            if server["name"].lower() == server_id.lower():
                return server
        
        return None
    
    def check_single_server_availability(self, server_ip_or_name):
        """Проверка доступности одного сервера"""
        try:
            server = self.get_server_by_selection(server_ip_or_name)
            if not server:
                return False, None, f"❌ Сервер '{server_ip_or_name}' не найден"
            
            from extensions.server_checks import check_server_availability
            is_up = check_server_availability(server)
            
            if is_up:
                return True, server, f"✅ Сервер {server['name']} ({server['ip']}) доступен"
            else:
                return False, server, f"🔴 Сервер {server['name']} ({server['ip']}) недоступен"
                
        except Exception as e:
            debug_log(f"❌ Ошибка проверки сервера {server_ip_or_name}: {e}")
            return False, None, f"❌ Ошибка проверки: {str(e)[:100]}"
    
    def check_single_server_resources(self, server_ip_or_name):
        """Проверка ресурсов одного сервера"""
        try:
            server = self.get_server_by_selection(server_ip_or_name)
            if not server:
                return None, None, f"❌ Сервер '{server_ip_or_name}' не найден"
            
            if server["type"] == "ssh":
                from extensions.server_checks import get_linux_resources_improved
                resources = get_linux_resources_improved(server["ip"])
            elif server["type"] == "rdp":
                from extensions.server_checks import get_windows_resources_improved
                resources = get_windows_resources_improved(server["ip"])
            else:
                resources = None
            
            if resources:
                # Форматируем сообщение
                message = f"📊 **Ресурсы сервера {server['name']} ({server['ip']})**\n\n"
                message += f"• CPU: {resources.get('cpu', 0)}%\n"
                message += f"• RAM: {resources.get('ram', 0)}%\n"
                message += f"• Disk: {resources.get('disk', 0)}%\n"
                message += f"• Метод доступа: {resources.get('access_method', 'неизвестно')}\n"
                message += f"• Время проверки: {resources.get('timestamp', 'N/A')}\n"
                
                # Проверка порогов
                from config.db_settings import RESOURCE_THRESHOLDS
                alerts = []
                
                cpu = resources.get('cpu', 0)
                ram = resources.get('ram', 0)
                disk = resources.get('disk', 0)
                
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
                
                if alerts:
                    message += "\n**⚠️ Предупреждения:**\n"
                    for alert in alerts:
                        message += f"• {alert}\n"
                
                return True, server, message
            else:
                return False, server, f"❌ Не удалось получить ресурсы сервера {server['name']}"
                
        except Exception as e:
            debug_log(f"❌ Ошибка проверки ресурсов {server_ip_or_name}: {e}")
            return False, None, f"❌ Ошибка: {str(e)[:100]}"
    
    def create_server_selection_menu(self, action="check_availability"):
        """Создает меню выбора сервера"""
        servers = self.get_all_servers()
        
        # Группируем по типам
        servers_by_type = {}
        for server in servers:
            server_type = server["type"]
            if server_type not in servers_by_type:
                servers_by_type[server_type] = []
            servers_by_type[server_type].append(server)
        
        # Создаем клавиатуру
        keyboard = []
        
        # Добавляем серверы по типам
        for server_type, type_servers in servers_by_type.items():
            # Заголовок типа
            type_name = {
                "rdp": "🪟 Windows",
                "ssh": "🐧 Linux/SSH", 
                "ping": "📡 Ping-серверы"
            }.get(server_type, server_type.upper())
            
            keyboard.append([InlineKeyboardButton(
                f"──────── {type_name} ({len(type_servers)}) ────────",
                callback_data=f"server_type_{server_type}"
            )])
            
            # Добавляем серверы этого типа (по 2 в ряд)
            row = []
            for i, server in enumerate(type_servers):
                button_text = f"{server['name'][:15]}"
                callback_data = f"{action}_{server['ip']}"
                
                row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                
                if len(row) == 2 or i == len(type_servers) - 1:
                    keyboard.append(row)
                    row = []
        
        # Кнопки навигации
        if action == "check_resources":
            keyboard.append([
                InlineKeyboardButton("⚙️ Настройки ресурсов", callback_data="settings_resources")
            ])

        keyboard.append([
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close")
        ])
        
        return InlineKeyboardMarkup(keyboard)

# Глобальный экземпляр
targeted_checks = TargetedChecks()
