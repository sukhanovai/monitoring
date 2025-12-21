"""
/modules/targeted_checks.py
Server Monitoring System v4.14.33
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Spot check module
Система мониторинга серверов
Версия: 4.14.33
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль точечных проверок
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from lib.logging import debug_log
from lib.utils import progress_bar
from modules.availability import availability_checker
from modules.resources import resources_checker

class TargetedChecks:
    """Класс для точечных проверок серверов"""
    
    def __init__(self):
        """Инициализация модуля точечных проверок"""
        self.server_cache = None
        self.cache_time = None
        self.cache_ttl = 300  # 5 минут
        
    def get_all_servers(self, force_refresh: bool = False) -> List[Dict]:
        """
        Получает список всех серверов с кэшированием
        
        Args:
            force_refresh: Принудительное обновление кэша
            
        Returns:
            List[Dict]: Список серверов
        """
        if (not force_refresh and self.server_cache is not None and 
            self.cache_time is not None):
            
            cache_age = (datetime.now() - self.cache_time).total_seconds()
            if cache_age < self.cache_ttl:
                debug_log(f"📋 Используем кэшированный список серверов ({len(self.server_cache)} шт)")
                return self.server_cache
        
        try:
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            
            # Исключаем сервер мониторинга
            monitor_server_ip = "192.168.20.2"
            servers = [s for s in servers if s.get("ip") != monitor_server_ip]
            
            self.server_cache = servers
            self.cache_time = datetime.now()
            
            debug_log(f"📋 Список серверов загружен: {len(servers)} шт (кэширован)")
            return servers
            
        except Exception as e:
            debug_log(f"❌ Ошибка загрузки списка серверов: {e}")
            return []
    
    def get_server_by_id(self, server_id: str) -> Optional[Dict]:
        """
        Находит сервер по ID (IP или имени)
        
        Args:
            server_id: IP или имя сервера
            
        Returns:
            Optional[Dict]: Сервер или None
        """
        servers = self.get_all_servers()
        
        for server in servers:
            if server.get("ip") == server_id or server.get("name") == server_id:
                return server
        
        return None
    
    def check_single_server_availability(self, server_id: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Проверяет доступность одного сервера
        
        Args:
            server_id: IP или имя сервера
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (успешно, сервер, сообщение)
        """
        server = self.get_server_by_id(server_id)
        
        if not server:
            return False, None, f"❌ Сервер '{server_id}' не найден"
        
        ip = server.get("ip")
        name = server.get("name", ip)
        server_type = server.get("type", "unknown")
        
        debug_log(f"🔍 Точечная проверка доступности: {name} ({ip})")
        
        try:
            is_up, method = availability_checker.check_server_availability(server)
            
            if is_up:
                message = (f"✅ *{name}* ({ip})\n"
                          f"🟢 **Статус:** Доступен\n"
                          f"📡 **Тип:** {server_type.upper()}\n"
                          f"🔧 **Метод:** {method}\n"
                          f"⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}")
            else:
                message = (f"❌ *{name}* ({ip})\n"
                          f"🔴 **Статус:** Недоступен\n"
                          f"📡 **Тип:** {server_type.upper()}\n"
                          f"🔧 **Метод:** {method}\n"
                          f"⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}")
            
            return True, server, message
            
        except Exception as e:
            error_msg = f"💥 Ошибка проверки {name}: {str(e)[:100]}"
            debug_log(error_msg)
            return False, server, f"❌ Ошибка проверки {name}: {str(e)[:50]}"
    
    def check_single_server_resources(self, server_id: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Проверяет ресурсы одного сервера
        
        Args:
            server_id: IP или имя сервера
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (успешно, сервер, сообщение)
        """
        server = self.get_server_by_id(server_id)
        
        if not server:
            return False, None, f"❌ Сервер '{server_id}' не найден"
        
        ip = server.get("ip")
        name = server.get("name", ip)
        server_type = server.get("type", "unknown")
        
        debug_log(f"📊 Точечная проверка ресурсов: {name} ({ip})")
        
        try:
            success, resources = resources_checker.check_server_resources(server)
            
            if success and resources:
                cpu = resources.get("cpu", 0)
                ram = resources.get("ram", 0)
                disk = resources.get("disk", 0)
                
                # Определяем иконки статуса
                cpu_icon = "🟢" if cpu < 80 else "🟡" if cpu < 90 else "🔴"
                ram_icon = "🟢" if ram < 85 else "🟡" if ram < 95 else "🔴"
                disk_icon = "🟢" if disk < 80 else "🟡" if disk < 90 else "🔴"
                
                message = (f"📊 *Ресурсы {name}* ({ip})\n\n"
                          f"{cpu_icon} **CPU:** {cpu}%\n"
                          f"{ram_icon} **RAM:** {ram}%\n"
                          f"{disk_icon} **Disk:** {disk}%\n\n"
                          f"📡 **Тип:** {server_type.upper()}\n"
                          f"⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}")
                
                # Добавляем предупреждения
                warnings = []
                if cpu >= 80:
                    warnings.append(f"⚠️ Высокая загрузка CPU ({cpu}%)")
                if ram >= 85:
                    warnings.append(f"⚠️ Высокое использование RAM ({ram}%)")
                if disk >= 80:
                    warnings.append(f"⚠️ Мало свободного места на диске ({disk}%)")
                
                if warnings:
                    message += "\n\n🚨 *Предупреждения:*\n" + "\n".join(warnings)
                
            else:
                message = (f"❌ *{name}* ({ip})\n"
                          f"🔴 **Ресурсы:** Не удалось получить\n"
                          f"📡 **Тип:** {server_type.upper()}\n"
                          f"⏰ **Время:** {datetime.now().strftime('%H:%M:%S')}")
            
            return success, server, message
            
        except Exception as e:
            error_msg = f"💥 Ошибка проверки ресурсов {name}: {str(e)[:100]}"
            debug_log(error_msg)
            return False, server, f"❌ Ошибка проверки ресурсов {name}: {str(e)[:50]}"
    
    def create_server_selection_menu(self, action: str) -> InlineKeyboardMarkup:
        """
        Упрощённое меню выбора сервера (вариант А)

        Args:
            action: check_availability | check_resources
        """
        servers = self.get_all_servers()

        if not servers:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Серверы не найдены", callback_data="main_menu")]
            ])

        # сортируем по типу, затем по имени
        servers.sort(key=lambda s: (s.get("type", ""), s.get("name", "")))

        keyboard = []
        row = []

        for i, server in enumerate(servers):
            ip = server.get("ip")
            name = server.get("name", ip)

            # короткое имя
            label = name if len(name) <= 18 else name[:15] + "..."

            row.append(
                InlineKeyboardButton(
                    label,
                    callback_data=f"{action}_{ip}"
                )
            )

            # по 2 кнопки в ряд
            if len(row) == 2 or i == len(servers) - 1:
                keyboard.append(row)
                row = []

        # навигация
        keyboard.append([
            InlineKeyboardButton("↩️ Назад", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close")
        ])

        return InlineKeyboardMarkup(keyboard)
    
"""
    def create_server_group_menu(self, server_type: str, action: str) -> InlineKeyboardMarkup:
"""
"""
        Создает меню для группы серверов
        
        Args:
            server_type: Тип серверов
            action: Действие
            
        Returns:
            InlineKeyboardMarkup: Клавиатура с серверами группы
"""
"""
        servers = self.get_all_servers()
        group_servers = [s for s in servers if s.get("type") == server_type]
        
        if not group_servers:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data=f"show_{action}_menu")]
            ])
        
        # Сортируем по имени
        group_servers.sort(key=lambda x: x.get("name", "").lower())
        
        keyboard = []
        row = []
        
        for i, server in enumerate(group_servers):
            ip = server.get("ip")
            name = server.get("name", ip)
            
            # Обрезаем длинные имена
            display_name = name if len(name) <= 20 else name[:17] + "..."
            
            row.append(InlineKeyboardButton(
                display_name,
                callback_data=f"{action}_{ip}"
            ))
            
            # По 2 кнопки в строку
            if len(row) == 2 or i == len(group_servers) - 1:
                keyboard.append(row)
                row = []
        
        # Кнопки управления
        keyboard.extend([
            [InlineKeyboardButton("↩️ Назад", callback_data=f"show_{action}_menu")],
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{action}"),
             InlineKeyboardButton("✖️ Закрыть", callback_data="close")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
"""
            
"""
    def create_quick_actions_menu(self, server_ip: str) -> InlineKeyboardMarkup:
"""
"""
        Создает меню быстрых действий для сервера
        
        Args:
            server_ip: IP сервера
            
        Returns:
            InlineKeyboardMarkup: Меню действий
"""
"""
        server = self.get_server_by_id(server_ip)
        
        if not server:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data="main_menu")]
            ])
        
        keyboard = [
            [InlineKeyboardButton("🔍 Проверить доступность", callback_data=f"check_availability_{server_ip}")],
            [InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f"check_resources_{server_ip}")],
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_availability_{server_ip}")],
            [InlineKeyboardButton("🔍 Другой сервер", callback_data="show_availability_menu"),
             InlineKeyboardButton("🎛️ Главное меню", callback_data="main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
"""
            
"""
    def perform_async_check(self, context: CallbackContext, chat_id: int, 
                          server_id: str, check_type: str = "availability") -> None:
"""
"""
        Выполняет асинхронную проверку сервера
        
        Args:
            context: Контекст бота
            chat_id: ID чата
            server_id: ID сервера
            check_type: Тип проверки (availability/resources)
"""
"""
        def check_thread():
            try:
                if check_type == "availability":
                    success, server, message = self.check_single_server_availability(server_id)
                else:
                    success, server, message = self.check_single_server_resources(server_id)
                
                # Создаем меню действий
                keyboard = self.create_quick_actions_menu(server_id) if server else None
                
                # Отправляем результат
                if keyboard:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                else:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
            except Exception as e:
                error_msg = f"💥 Ошибка асинхронной проверки: {str(e)[:100]}"
                debug_log(error_msg)
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Ошибка проверки: {str(e)[:50]}"
                )
        
        # Запускаем проверку в отдельном потоке
        thread = threading.Thread(target=check_thread)
        thread.start()
"""
        
# Глобальный экземпляр для импорта
targeted_checks = TargetedChecks()