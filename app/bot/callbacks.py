"""
Server Monitoring System v4.4.12 - Обработчики бота
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
        print(f"✅ CallbackRouter инициализирован, обработчиков: {len(self.handlers)}")
    
    def _load_handlers(self):
        """Загрузка обработчиков по модулям"""
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
        self._add_handler_pattern('^debug_menu$', 'app.bot.debug_menu', 'debug_menu')
        self._add_handler_pattern('^debug_enable$', 'app.bot.debug_menu', 'debug_menu')
        self._add_handler_pattern('^debug_disable$', 'app.bot.debug_menu', 'debug_menu')
        self._add_handler_pattern('^debug_status$', 'app.bot.debug_menu', 'debug_menu')
        self._add_handler_pattern('^debug_clear_logs$', 'app.bot.debug_menu', 'debug_menu')
        self._add_handler_pattern('^debug_diagnose$', 'app.bot.debug_menu', 'debug_menu')
        self._add_handler_pattern('^debug_advanced$', 'app.bot.debug_menu', 'debug_menu')
    
    def _add_handler_pattern(self, pattern, module_path, function_name):
        """Добавить обработчик по шаблону"""
        self.handlers[pattern] = {
            'module': module_path,
            'function': function_name
        }
    
    def route_callback(self, update, context):
        """Маршрутизация callback-запроса"""
        query = update.callback_query
        data = query.data if query else None
        
        if not data:
            print("❌ Callback без данных")
            return
        
        print(f"🔔 Callback получен: {data}")
        
        # ПРОСТОЙ И ЭФФЕКТИВНЫЙ МЕТОД - сначала проверяем частные случаи
        if data == 'full_report':
            print("✅ Обрабатываем full_report напрямую...")
            try:
                from app.bot.handlers import send_morning_report_handler
                return send_morning_report_handler(update, context)
            except Exception as e:
                print(f"❌ Ошибка в обработке full_report: {e}")
                query.answer(f"Ошибка: {e}")
                return
       
        # Точные совпадения (без ^ и $)
        exact_patterns = {
            'main_menu': ('app.bot.menus', 'start_command'),
            'close': ('app.bot.handlers', 'close_menu'),
            'debug_menu': ('app.bot.debug_menu', 'debug_menu'),
            'extensions_menu': ('app.bot.menus', 'show_extensions_menu'),
            'monitor_status': ('app.bot.handlers', 'monitor_status'),
            'control_panel': ('app.bot.handlers', 'control_panel_handler'),
            'manual_check': ('app.bot.handlers', 'manual_check_handler'),
            'check_resources': ('app.bot.handlers', 'check_resources_handler'),
            'silent_status': ('app.bot.handlers', 'silent_status_handler'),
            'backup_main': ('extensions.backup_monitor.bot_handler', 'backup_callback'),
        }
        
        # Проверяем точные совпадения
        if data in exact_patterns:
            print(f"✅ Найден точный обработчик для: {data}")
            module_path, function_name = exact_patterns[data]
            return self._execute_handler({'module': module_path, 'function': function_name}, update, context)
        
        # Частичные совпадения
        if data.startswith('ext_toggle_'):
            return self._execute_handler({'module': 'app.bot.menus', 'function': 'extensions_callback_handler'}, update, context)
        elif data.startswith('debug_'):
            return self._execute_handler({'module': 'app.bot.debug_menu', 'function': 'debug_menu'}, update, context)
        elif data.startswith('check_'):
            return self._execute_handler({'module': 'app.bot.handlers', 'function': 'check_resources_handler'}, update, context)
        elif data in ['force_silent', 'force_loud', 'auto_mode']:
            return self._execute_handler({'module': 'app.bot.handlers', 'function': data + '_handler'}, update, context)
        elif data.startswith('settings_'):
            try:
                from settings_handlers import settings_callback_handler
                return settings_callback_handler(update, context)
            except:
                pass
        
        # Обработчик не найден
        if query:
            try:
                query.answer(f"❌ Команда '{data}' не распознана")
            except:
                pass
        
        print(f"❌ Необработанный callback: {data}")

    def _execute_handler(self, handler_info, update, context):
        """Выполнить обработчик с обработкой ошибок"""
        try:
            module = importlib.import_module(handler_info['module'])
            handler = getattr(module, handler_info['function'])
            return handler(update, context)
        except (ImportError, AttributeError) as e:
            print(f"❌ Ошибка загрузки обработчика {handler_info['module']}.{handler_info['function']}: {e}")
            
            # Безопасная обработка callback_query
            query = getattr(update, 'callback_query', None)
            if query:
                try:
                    query.answer("❌ Ошибка выполнения команды")
                except:
                    pass
            else:
                # Если нет callback_query, возможно это обычное сообщение
                if update.message:
                    update.message.reply_text("❌ Ошибка выполнения команды")

    def get_handlers(self):
        """Получить все обработчики для регистрации"""
        from telegram.ext import CallbackQueryHandler
        
        handlers_list = []
        for pattern in self.handlers.keys():
            handlers_list.append(
                CallbackQueryHandler(self.route_callback, pattern=pattern)
            )
        
        print(f"📋 CallbackRouter.get_handlers() вернул {len(handlers_list)} обработчиков")
        return handlers_list

# Глобальный экземпляр маршрутизатора
callback_router = CallbackRouter()