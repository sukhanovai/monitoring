"""
Server Monitoring System v4.4.0 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Централизованная маршрутизация callback-ов
Версия: 4.4.0
"""

from telegram.ext import CallbackQueryHandler
import importlib

class CallbackRouter:
    """Маршрутизатор callback-запросов"""
    
    def __init__(self):
        self.handlers = {}
        self._load_handlers()
    
    def _load_handlers(self):
        """Загрузка обработчиков по модулям"""
        # Основные обработчики из handlers.py
        self._add_handler_pattern('^manual_check$', 'app.bot.handlers', 'manual_check_handler')
        self._add_handler_pattern('^monitor_status$', 'app.bot.handlers', 'monitor_status')
        self._add_handler_pattern('^check_resources$', 'app.bot.handlers', 'check_resources_handler')
        self._add_handler_pattern('^control_panel$', 'app.bot.handlers', 'control_panel_handler')
        self._add_handler_pattern('^close$', 'app.bot.handlers', 'close_menu')
        
        # Обработчики настроек
        self._add_handler_pattern('^settings_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^set_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^manage_', 'settings_handlers', 'settings_callback_handler')
        
        # Добавьте остальные обработчики по аналогии...
    
    def _add_handler_pattern(self, pattern, module_path, function_name):
        """Добавить обработчик по шаблону"""
        self.handlers[pattern] = {
            'module': module_path,
            'function': function_name
        }
    
    def route_callback(self, update, context):
        """Маршрутизация callback-запроса"""
        query = update.callback_query
        data = query.data
        
        # Поиск обработчика по паттерну
        for pattern, handler_info in self.handlers.items():
            if pattern.endswith('$'):
                # Точное совпадение
                if data == pattern[:-1]:
                    return self._execute_handler(handler_info, update, context)
            elif data.startswith(pattern.replace('$', '')):
                # Частичное совпадение (для префиксов)
                return self._execute_handler(handler_info, update, context)
        
        # Обработчик не найден
        query.answer("❌ Команда не распознана")
    
    def _execute_handler(self, handler_info, update, context):
        """Выполнить обработчик"""
        try:
            module = importlib.import_module(handler_info['module'])
            handler = getattr(module, handler_info['function'])
            return handler(update, context)
        except (ImportError, AttributeError) as e:
            print(f"❌ Ошибка загрузки обработчика: {e}")
            update.callback_query.answer("❌ Ошибка выполнения команды")
    
    def get_handlers(self):
        """Получить все обработчики для регистрации"""
        handlers_list = []
        for pattern in self.handlers.keys():
            handlers_list.append(
                CallbackQueryHandler(self.route_callback, pattern=pattern)
            )
        return handlers_list

# Глобальный экземпляр маршрутизатора
callback_router = CallbackRouter()
