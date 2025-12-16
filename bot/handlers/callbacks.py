"""
/bot/handlers/callbacks.py
Server Monitoring System v4.12.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Callback handlers for Telegram bot
Система мониторинга серверов
Версия: 4.12.1
Автор: Александр Суханов (c)
Лицензия: MIT
Callback-обработчики для Telegram бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from lib.logging import debug_log
from bot.handlers.base import BaseHandlers

class CallbackHandlers(BaseHandlers):
    """Обработчики callback-запросов"""
    
    def __init__(self, config_manager=None):
        super().__init__(config_manager)
    
    def handle_main_menu(self, update: Update, context: CallbackContext):
        """Обработчик главного меню"""
        query = update.callback_query
        if query:
            query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        return menu_handlers.show_main_menu(update, context)
    
    def handle_check_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий проверки"""
        query = update.callback_query
        query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        if query.data == 'manual_check':
            return menu_handlers.perform_manual_check(update, context)
        elif query.data == 'check_resources':
            return menu_handlers.show_resources_menu(update, context)
        elif query.data == 'check_linux':
            return menu_handlers.check_linux_servers(update, context)
        elif query.data == 'check_windows':
            return menu_handlers.check_windows_servers(update, context)
        elif query.data == 'check_other':
            return menu_handlers.check_other_servers(update, context)
        elif query.data == 'check_cpu':
            return menu_handlers.check_cpu_resources(update, context)
        elif query.data == 'check_ram':
            return menu_handlers.check_ram_resources(update, context)
        elif query.data == 'check_disk':
            return menu_handlers.check_disk_resources(update, context)
    
    def handle_monitor_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий мониторинга"""
        query = update.callback_query
        query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        if query.data == 'monitor_status':
            return menu_handlers.show_monitor_status(update, context)
        elif query.data == 'silent_status':
            return menu_handlers.show_silent_menu(update, context)
        elif query.data == 'control_panel':
            return menu_handlers.show_control_panel(update, context)
        elif query.data == 'toggle_monitoring':
            return menu_handlers.toggle_monitoring(update, context)
    
    def handle_report_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий отчетов"""
        query = update.callback_query
        query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        if query.data == 'full_report':
            return menu_handlers.send_morning_report(update, context)
        elif query.data == 'debug_report':
            return menu_handlers.debug_morning_report(update, context)
    
    def handle_silent_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий тихого режима"""
        query = update.callback_query
        query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        if query.data == 'force_silent':
            return menu_handlers.force_silent_mode(update, context)
        elif query.data == 'force_loud':
            return menu_handlers.force_loud_mode(update, context)
        elif query.data == 'auto_mode':
            return menu_handlers.auto_silent_mode(update, context)
        elif query.data == 'toggle_silent':
            return menu_handlers.toggle_silent_mode(update, context)
    
    def handle_debug_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий отладки"""
        query = update.callback_query
        query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        if query.data == 'debug_menu':
            return menu_handlers.show_debug_menu(update, context)
        elif query.data == 'debug_enable':
            return menu_handlers.enable_debug_mode(update, context)
        elif query.data == 'debug_disable':
            return menu_handlers.disable_debug_mode(update, context)
        elif query.data == 'debug_status':
            return menu_handlers.show_debug_status(update, context)
        elif query.data == 'debug_clear_logs':
            return menu_handlers.clear_debug_logs(update, context)
        elif query.data == 'debug_diagnose':
            return menu_handlers.run_diagnostic(update, context)
        elif query.data == 'debug_advanced':
            return menu_handlers.show_advanced_debug(update, context)
    
    def handle_extensions_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий расширений"""
        query = update.callback_query
        query.answer()
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        
        if query.data == 'extensions_menu':
            return menu_handlers.show_extensions_menu(update, context)
        elif query.data.startswith('ext_toggle_'):
            extension_id = query.data.replace('ext_toggle_', '')
            return menu_handlers.toggle_extension(update, context, extension_id)
        elif query.data == 'ext_enable_all':
            return menu_handlers.enable_all_extensions(update, context)
        elif query.data == 'ext_disable_all':
            return menu_handlers.disable_all_extensions(update, context)
    
    def handle_backup_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий бэкапов"""
        query = update.callback_query
        query.answer()
        
        # Ленивая загрузка обработчика бэкапов
        try:
            from extensions.backup_monitor.bot_handler import backup_callback_handler
            return backup_callback_handler(update, context)
        except ImportError as e:
            debug_log(f"Ошибка загрузки обработчика бэкапов: {e}")
            query.answer("❌ Модуль бэкапов недоступен", show_alert=True)
            return
    
    def handle_settings_actions(self, update: Update, context: CallbackContext):
        """Обработчик действий настроек"""
        query = update.callback_query
        query.answer()
        
        # Ленивая загрузка обработчика настроек
        try:
            from settings_handlers import settings_callback_handler
            return settings_callback_handler(update, context)
        except ImportError as e:
            debug_log(f"Ошибка загрузки обработчика настроек: {e}")
            query.answer("❌ Модуль настроек недоступен", show_alert=True)
            return
    
    def handle_close(self, update: Update, context: CallbackContext):
        """Обработчик закрытия меню"""
        query = update.callback_query
        query.answer()
        
        try:
            query.delete_message()
        except:
            query.edit_message_text("✅ Меню закрыто")
    
    def get_callback_handlers(self):
        """Возвращает список обработчиков callback"""
        return [
            # Основные меню
            CallbackQueryHandler(self.handle_main_menu, pattern='^main_menu$'),
            CallbackQueryHandler(self.handle_close, pattern='^close$'),
            
            # Проверки
            CallbackQueryHandler(self.handle_check_actions, pattern='^manual_check$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_resources$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_linux$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_windows$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_other$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_cpu$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_ram$'),
            CallbackQueryHandler(self.handle_check_actions, pattern='^check_disk$'),
            
            # Мониторинг
            CallbackQueryHandler(self.handle_monitor_actions, pattern='^monitor_status$'),
            CallbackQueryHandler(self.handle_monitor_actions, pattern='^silent_status$'),
            CallbackQueryHandler(self.handle_monitor_actions, pattern='^control_panel$'),
            CallbackQueryHandler(self.handle_monitor_actions, pattern='^toggle_monitoring$'),
            
            # Отчеты
            CallbackQueryHandler(self.handle_report_actions, pattern='^full_report$'),
            CallbackQueryHandler(self.handle_report_actions, pattern='^debug_report$'),
            
            # Тихий режим
            CallbackQueryHandler(self.handle_silent_actions, pattern='^force_silent$'),
            CallbackQueryHandler(self.handle_silent_actions, pattern='^force_loud$'),
            CallbackQueryHandler(self.handle_silent_actions, pattern='^auto_mode$'),
            CallbackQueryHandler(self.handle_silent_actions, pattern='^toggle_silent$'),
            
            # Отладка
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_menu$'),
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_enable$'),
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_disable$'),
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_status$'),
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_clear_logs$'),
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_diagnose$'),
            CallbackQueryHandler(self.handle_debug_actions, pattern='^debug_advanced$'),
            
            # Расширения
            CallbackQueryHandler(self.handle_extensions_actions, pattern='^extensions_menu$'),
            CallbackQueryHandler(self.handle_extensions_actions, pattern='^ext_toggle_'),
            CallbackQueryHandler(self.handle_extensions_actions, pattern='^ext_enable_all$'),
            CallbackQueryHandler(self.handle_extensions_actions, pattern='^ext_disable_all$'),
            
            # Бэкапы
            CallbackQueryHandler(self.handle_backup_actions, pattern='^backup_'),
            CallbackQueryHandler(self.handle_backup_actions, pattern='^db_'),
            
            # Настройки
            CallbackQueryHandler(self.handle_settings_actions, pattern='^settings_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^set_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^add_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^remove_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^edit_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^delete_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^view_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^manage_'),
            
            # Серверы и таймауты
            CallbackQueryHandler(self.handle_settings_actions, pattern='^server_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^timeout_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^cred_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^ssh_'),
            CallbackQueryHandler(self.handle_settings_actions, pattern='^windows_'),
            
            # Целевые проверки
            CallbackQueryHandler(lambda u,c: self.handle_targeted_checks(u,c), pattern='^show_availability_menu$'),
            CallbackQueryHandler(lambda u,c: self.handle_targeted_checks(u,c), pattern='^show_resources_menu$'),
            CallbackQueryHandler(lambda u,c: self.handle_targeted_checks(u,c), pattern='^check_availability_'),
            CallbackQueryHandler(lambda u,c: self.handle_targeted_checks(u,c), pattern='^check_resources_'),
            CallbackQueryHandler(lambda u,c: self.handle_targeted_checks(u,c), pattern='^refresh_'),
        ]
    
    def handle_targeted_checks(self, update: Update, context: CallbackContext):
        """Обработчик целевых проверок"""
        query = update.callback_query
        query.answer()
        
        # Ленивая загрузка модуля целевых проверок
        try:
            from modules.targeted_checks import targeted_checks
            
            data = query.data
            
            if data == 'show_availability_menu':
                targeted_checks.show_server_selection_menu(update, context, "check_availability")
            elif data == 'show_resources_menu':
                targeted_checks.show_server_selection_menu(update, context, "check_resources")
            elif data.startswith('check_availability_'):
                server_id = data.replace('check_availability_', '')
                targeted_checks.handle_single_check(update, context, server_id)
            elif data.startswith('check_resources_'):
                server_id = data.replace('check_resources_', '')
                targeted_checks.handle_single_resources(update, context, server_id)
            elif data.startswith('refresh_'):
                targeted_checks.refresh_server_menu(update, context)
                
        except ImportError as e:
            debug_log(f"Ошибка загрузки модуля целевых проверок: {e}")
            query.answer("❌ Модуль проверок недоступен", show_alert=True)