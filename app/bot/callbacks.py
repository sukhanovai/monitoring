"""
Server Monitoring System v4.4.6 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Централизованная маршрутизация callback-ов

"""

from telegram.ext import CallbackQueryHandler
import importlib

class CallbackRouter:
    """Маршрутизатор callback-запросов"""
    
    def __init__(self):
        self.handlers = {}
        self._load_handlers()
    
    def _load_handlers(self):
        """Загрузка обработчиков по модулям - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        # ========== ГЛАВНОЕ МЕНЮ ==========
        self._add_handler_pattern('^manual_check$', 'app.bot.handlers', 'manual_check_handler')
        self._add_handler_pattern('^monitor_status$', 'app.bot.handlers', 'monitor_status')
        self._add_handler_pattern('^check_resources$', 'app.bot.handlers', 'check_resources_handler')
        self._add_handler_pattern('^settings_main$', 'settings_handlers', 'settings_command')
        self._add_handler_pattern('^debug_menu$', 'app.bot.debug_menu', 'debug_menu.show_menu')
        self._add_handler_pattern('^backup_main$', 'extensions.backup_monitor.bot_handler', 'backup_callback')
        self._add_handler_pattern('^extensions_menu$', 'app.bot.menus', 'show_extensions_menu')
        self._add_handler_pattern('^control_panel$', 'app.bot.handlers', 'control_panel_handler')
        self._add_handler_pattern('^close$', 'app.bot.handlers', 'close_menu')
        self._add_handler_pattern('^main_menu$', 'app.bot.menus', 'start_command')
        self._add_handler_pattern('^monitor_main$', 'app.bot.menus', 'start_command')
        
        # ========== ТИХИЙ РЕЖИМ ==========
        self._add_handler_pattern('^silent_status$', 'app.bot.handlers', 'silent_status_handler')
        self._add_handler_pattern('^force_silent$', 'app.bot.handlers', 'force_silent_handler')
        self._add_handler_pattern('^force_loud$', 'app.bot.handlers', 'force_loud_handler')
        self._add_handler_pattern('^auto_mode$', 'app.bot.handlers', 'auto_mode_handler')
        self._add_handler_pattern('^toggle_silent$', 'app.bot.handlers', 'toggle_silent_mode_handler')
        
        # ========== УПРАВЛЕНИЕ ==========
        self._add_handler_pattern('^toggle_monitoring$', 'app.bot.handlers', 'toggle_monitoring_handler')
        self._add_handler_pattern('^daily_report$', 'app.bot.handlers', 'send_morning_report_handler')
        self._add_handler_pattern('^full_report$', 'app.bot.handlers', 'send_morning_report_handler')
        self._add_handler_pattern('^debug_report$', 'app.bot.handlers', 'debug_morning_report')
        
        # ========== РЕСУРСЫ ==========
        self._add_handler_pattern('^resource_history$', 'app.bot.handlers', 'resource_history_command')
        self._add_handler_pattern('^resource_page_', 'app.bot.handlers', 'resource_page_handler')
        self._add_handler_pattern('^refresh_resources$', 'app.bot.handlers', 'refresh_resources_handler')
        self._add_handler_pattern('^close_resources$', 'app.bot.handlers', 'close_resources_handler')
        
        # ========== ПРОВЕРКА ПО ТИПАМ ==========
        self._add_handler_pattern('^check_linux$', 'app.bot.handlers', 'check_linux_resources_handler')
        self._add_handler_pattern('^check_windows$', 'app.bot.handlers', 'check_windows_resources_handler')
        self._add_handler_pattern('^check_other$', 'app.bot.handlers', 'check_other_resources_handler')
        self._add_handler_pattern('^check_cpu$', 'app.bot.handlers', 'check_cpu_resources_handler')
        self._add_handler_pattern('^check_ram$', 'app.bot.handlers', 'check_ram_resources_handler')
        self._add_handler_pattern('^check_disk$', 'app.bot.handlers', 'check_disk_resources_handler')
        
        # ========== СЕРВЕРЫ ==========
        self._add_handler_pattern('^servers_list$', 'extensions.server_checks', 'servers_list_handler')
        
        # ========== НАСТРОЙКИ ==========
        self._add_handler_pattern('^settings_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^set_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^manage_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^ssh_auth_settings$', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^windows_auth_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^cred_type_', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^server_timeouts$', 'settings_handlers', 'settings_callback_handler')
        self._add_handler_pattern('^server_type_', 'settings_handlers', 'settings_callback_handler')
        
        # ========== БЭКАПЫ ==========
        self._add_handler_pattern('^backup_', 'extensions.backup_monitor.bot_handler', 'backup_callback')
        self._add_handler_pattern('^db_backups_', 'extensions.backup_monitor.bot_handler', 'backup_callback')
        self._add_handler_pattern('^db_detail_', 'extensions.backup_monitor.bot_handler', 'backup_callback')
        
        # ========== РАСШИРЕНИЯ ==========
        self._add_handler_pattern('^extensions_menu$', 'app.bot.menus', 'show_extensions_menu')
        self._add_handler_pattern('^extensions_refresh$', 'app.bot.menus', 'show_extensions_menu')
        self._add_handler_pattern('^ext_enable_all$', 'app.bot.menus', 'enable_all_extensions')
        self._add_handler_pattern('^ext_disable_all$', 'app.bot.menus', 'disable_all_extensions')
        self._add_handler_pattern('^ext_toggle_', 'app.bot.menus', 'extensions_callback_handler')
        
        # ========== ОТЛАДКА ==========
        self._add_handler_pattern('^debug_menu$', 'app.bot.debug_menu', 'debug_menu.show_menu')
        self._add_handler_pattern('^debug_enable$', 'app.bot.debug_menu', 'debug_menu.handle_callback')
        self._add_handler_pattern('^debug_disable$', 'app.bot.debug_menu', 'debug_menu.handle_callback')
        self._add_handler_pattern('^debug_status$', 'app.bot.debug_menu', 'debug_menu.handle_callback')
        self._add_handler_pattern('^debug_clear_logs$', 'app.bot.debug_menu', 'debug_menu.handle_callback')
        self._add_handler_pattern('^debug_diagnose$', 'app.bot.debug_menu', 'debug_menu.handle_callback')
        self._add_handler_pattern('^debug_advanced$', 'app.bot.debug_menu', 'debug_menu.handle_callback')

    def _add_handler_pattern(self, pattern, module_path, function_name):
        """Добавить обработчик по шаблону"""
        self.handlers[pattern] = {
            'module': module_path,
            'function': function_name
        }
    
def route_callback(self, update, context):
    """Маршрутизация callback-запроса - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    data = query.data
    
    print(f"🔔 Callback получен: {data}")  # Для отладки
    
    # Сначала проверяем точные совпадения (паттерны с $)
    for pattern, handler_info in self.handlers.items():
        if pattern.endswith('$'):
            # Убираем $ для сравнения
            if data == pattern[:-1]:
                print(f"✅ Найден точный обработчик для: {data}")
                return self._execute_handler(handler_info, update, context)
    
    # Затем проверяем частичные совпадения (паттерны без $ в конце)
    for pattern, handler_info in self.handlers.items():
        if not pattern.endswith('$') and pattern.endswith('_'):
            # Для паттернов типа ^settings_ или ^backup_
            if data.startswith(pattern[1:-1]):  # Убираем ^ и _
                print(f"✅ Найден частичный обработчик для: {data}")
                return self._execute_handler(handler_info, update, context)
    
    # Если не нашли, ищем любой частичный match
    for pattern, handler_info in self.handlers.items():
        pattern_clean = pattern.replace('^', '').replace('$', '')
        if data.startswith(pattern_clean):
            print(f"⚠️ Найден приблизительный обработчик для: {data}")
            return self._execute_handler(handler_info, update, context)
    
    # Обработчик не найден
    query.answer(f"❌ Команда '{data}' не распознана")
    print(f"❌ Необработанный callback: {data}")
    
    # Покажем меню снова как fallback
    try:
        from app.bot.menus import start_command
        return start_command(update, context)
    except:
        query.edit_message_text("❌ Ошибка обработки команды. Попробуйте /start")
            
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
