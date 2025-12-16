"""
Server Monitoring System v4.11.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot callback handlers
Система мониторинга серверов
Версия: 4.11.4
Автор: Александр Суханов (c)
Лицензия: MIT
Callback обработчики бота
"""

from telegram.ext import CallbackQueryHandler
from lib.logging import debug_log
from bot.handlers.base import lazy_handler

def setup_callback_handlers():
    """Настройка обработчиков callback-запросов"""
    return [
        # Обработчики настроек
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^backup_times$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^backup_patterns$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^manage_'),

        # Обработчики аутентификации
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_auth$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^ssh_auth_settings$'),
        
        # Обработчики Windows аутентификации
        CallbackQueryHandler(lazy_settings_handler(), pattern='^windows_auth_'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^cred_type_'),

        # Обработчики для таймаутов серверов
        CallbackQueryHandler(lazy_settings_handler(), pattern='^server_timeouts$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_windows_2025_timeout$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_domain_servers_timeout$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_admin_servers_timeout$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_standard_windows_timeout$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_linux_timeout$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^set_ping_timeout$'),

        # Обработчики для настроек БД
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_main$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_add_category$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_edit_category$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_delete_category$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_view_all$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_edit_'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_db_delete_'),

        # Основные обработчики
        CallbackQueryHandler(lazy_handler('manual_check'), pattern='^manual_check$'),
        CallbackQueryHandler(lazy_handler('monitor_status'), pattern='^monitor_status$'),
        CallbackQueryHandler(lazy_handler('servers_list'), pattern='^servers_list$'),
        CallbackQueryHandler(lazy_handler('silent_status'), pattern='^silent_status$'),
        CallbackQueryHandler(lazy_handler('check_resources'), pattern='^check_resources$'),
        CallbackQueryHandler(lazy_handler('control_panel'), pattern='^control_panel$'),
        CallbackQueryHandler(lazy_handler('daily_report'), pattern='^daily_report$'),
        CallbackQueryHandler(lazy_handler('diagnose_menu'), pattern='^diagnose_menu$'),
        CallbackQueryHandler(lazy_handler('close'), pattern='^close$'),
        CallbackQueryHandler(lazy_handler('full_report'), pattern='^full_report$'),
        CallbackQueryHandler(lazy_handler('force_silent'), pattern='^force_silent$'),
        CallbackQueryHandler(lazy_handler('force_loud'), pattern='^force_loud$'),
        CallbackQueryHandler(lazy_handler('auto_mode'), pattern='^auto_mode$'),
        CallbackQueryHandler(lazy_handler('toggle_silent'), pattern='^toggle_silent$'),
        CallbackQueryHandler(lazy_handler('resource_history'), pattern='^resource_history$'),
        CallbackQueryHandler(lazy_handler('debug_report'), pattern='^debug_report$'),
        CallbackQueryHandler(lazy_handler('monitor_main'), pattern='^monitor_main$'),
        CallbackQueryHandler(lazy_handler('main_menu'), pattern='^main_menu$'),
        CallbackQueryHandler(lazy_handler('toggle_monitoring'), pattern='^toggle_monitoring$'),
        CallbackQueryHandler(lazy_handler('close'), pattern='^close$'),

        # Обработчики для настроек
        CallbackQueryHandler(lazy_settings_handler(), pattern='^add_chat$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^remove_chat$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^view_patterns$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^add_pattern$'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^settings_view_all$'),

        # Обработчики бэкапов
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_today$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_summary$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_detailed$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_list$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_detail_'),

        # Обработчики для постраничного просмотра ресурсов
        CallbackQueryHandler(lazy_handler('resource_page'), pattern='^resource_page_'),
        CallbackQueryHandler(lazy_handler('refresh_resources'), pattern='^refresh_resources$'),
        CallbackQueryHandler(lazy_handler('close_resources'), pattern='^close_resources$'),
        
        # Обработчики для раздельной проверки по типам серверов
        CallbackQueryHandler(lazy_handler('check_linux'), pattern='^check_linux$'),
        CallbackQueryHandler(lazy_handler('check_windows'), pattern='^check_windows$'),
        CallbackQueryHandler(lazy_handler('check_other'), pattern='^check_other$'),
        
        # Обработчики для раздельной проверки ресурсов
        CallbackQueryHandler(lazy_handler('check_cpu'), pattern='^check_cpu$'),
        CallbackQueryHandler(lazy_handler('check_ram'), pattern='^check_ram$'),
        CallbackQueryHandler(lazy_handler('check_disk'), pattern='^check_disk$'),

        # Обработчики для бэкапов
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_hosts$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_refresh$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_host_'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_today$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_summary$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_detailed$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_backups_list$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_main$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_proxmox$'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_databases$'),                
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_host_'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^db_detail_'),
        CallbackQueryHandler(lazy_backup_handler(), pattern='^backup_stale_hosts$'),

        # Обработчики расширений
        CallbackQueryHandler(lazy_handler('extensions_menu'), pattern='^extensions_menu$'),
        CallbackQueryHandler(lazy_handler('extensions_refresh'), pattern='^extensions_refresh$'),
        CallbackQueryHandler(lazy_handler('ext_enable_all'), pattern='^ext_enable_all$'),
        CallbackQueryHandler(lazy_handler('ext_disable_all'), pattern='^ext_disable_all$'),
        CallbackQueryHandler(lazy_extensions_callback_handler(), pattern='^ext_toggle_'),
        
        # Обработчики для серверов
        CallbackQueryHandler(lazy_settings_handler(), pattern='^server_type_'),
        
        # Обработчики для БД
        CallbackQueryHandler(lazy_settings_handler(), pattern='^edit_db_category_'),
        CallbackQueryHandler(lazy_settings_handler(), pattern='^delete_db_category_'),

        # Обработчики отладки
        CallbackQueryHandler(lazy_debug_callback_handler(), pattern='^debug_enable$'),
        CallbackQueryHandler(lazy_debug_callback_handler(), pattern='^debug_disable$'),
        CallbackQueryHandler(lazy_debug_callback_handler(), pattern='^debug_status$'),
        CallbackQueryHandler(lazy_debug_callback_handler(), pattern='^debug_clear_logs$'),
        CallbackQueryHandler(lazy_debug_callback_handler(), pattern='^debug_diagnose$'),
        CallbackQueryHandler(lazy_debug_callback_handler(), pattern='^debug_advanced$'),
        CallbackQueryHandler(lazy_handler('debug_menu'), pattern='^debug_menu$'),

        # Обработчики проверок отдельных серверов
        CallbackQueryHandler(lambda u,c: lazy_server_selection_handler('check_single')(u,c), pattern='^check_single_menu$'),
        CallbackQueryHandler(lambda u,c: lazy_server_selection_handler('check_resources')(u,c), pattern='^check_resources_menu$'),
        CallbackQueryHandler(lambda u,c: lazy_check_single_callback(u,c), pattern='^check_single_'),
        CallbackQueryHandler(lambda u,c: lazy_check_resources_callback(u,c), pattern='^check_resources_'),

        CallbackQueryHandler(lambda u,c: lazy_show_server_selection(u,c, "check_availability"), pattern='^show_availability_menu$'),
        CallbackQueryHandler(lambda u,c: lazy_show_server_selection(u,c, "check_resources"), pattern='^show_resources_menu$'),
        CallbackQueryHandler(lambda u,c: lazy_check_availability_callback(u,c), pattern='^check_availability_'),
        CallbackQueryHandler(lambda u,c: lazy_check_resources_single_callback(u,c), pattern='^check_resources_'),
        CallbackQueryHandler(lambda u,c: lazy_refresh_server_menu(u,c), pattern='^refresh_'),
    ]

def lazy_settings_handler():
    """Ленивая загрузка обработчика настроек"""
    def handler(update, context):
        try:
            from settings_handlers import settings_callback_handler
            return settings_callback_handler(update, context)
        except ImportError as e:
            debug_log(f"❌ Ошибка импорта settings_callback_handler: {e}")
            query = update.callback_query
            query.answer("⚙️ Модуль настроек временно недоступен")
    return handler

def lazy_backup_handler():
    """Ленивая загрузка обработчика бэкапов"""
    def handler(update, context):
        try:
            from extensions.backup_monitor.bot_handler import backup_callback
            return backup_callback(update, context)
        except ImportError as e:
            debug_log(f"❌ Ошибка импорта backup_callback: {e}")
            query = update.callback_query
            query.answer("💾 Модуль бэкапов временно недоступен")
    return handler

def lazy_extensions_callback_handler():
    """Ленивая загрузка обработчика расширений"""
    def handler(update, context):
        try:
            from bot.menu.handlers import extensions_callback_handler
            return extensions_callback_handler(update, context)
        except ImportError as e:
            debug_log(f"❌ Ошибка импорта extensions_callback_handler: {e}")
            query = update.callback_query
            query.answer("🛠️ Модуль расширений временно недоступен")
    return handler

def lazy_debug_callback_handler():
    """Ленивая загрузка обработчика отладки"""
    def handler(update, context):
        try:
            from bot.menu.handlers import debug_callback_handler
            return debug_callback_handler(update, context)
        except ImportError as e:
            debug_log(f"❌ Ошибка импорта debug_callback_handler: {e}")
            query = update.callback_query
            query.answer("🐛 Модуль отладки временно недоступен")
    return handler

def lazy_server_selection_handler(action_type):
    """Ленивая загрузка обработчика выбора сервера"""
    def handler(update, context):
        try:
            from modules.targeted_checks import handle_server_selection_menu
            return handle_server_selection_menu(update, context, action_type)
        except ImportError as e:
            debug_log(f"❌ Ошибка импорта handle_server_selection_menu: {e}")
            query = update.callback_query
            query.answer("🔍 Модуль выбора сервера временно недоступен")
    return handler

def lazy_show_server_selection(update, context, action):
    """Ленивая загрузка показа меню выбора сервера"""
    try:
        from modules.targeted_checks import show_server_selection_menu
        return show_server_selection_menu(update, context, action)
    except ImportError as e:
        debug_log(f"❌ Ошибка импорта show_server_selection_menu: {e}")
        query = update.callback_query
        query.answer("🔍 Модуль выбора сервера временно недоступен")

def lazy_check_single_callback(update, context):
    """Ленивая загрузка обработчика проверки одного сервера"""
    try:
        from modules.targeted_checks import handle_check_single_callback
        server_ip = update.callback_query.data.replace('check_single_', '')
        return handle_check_single_callback(update, context, server_ip)
    except ImportError as e:
        debug_log(f"❌ Ошибка импорта handle_check_single_callback: {e}")
        query = update.callback_query
        query.answer("🔍 Ошибка проверки сервера")

def lazy_check_resources_callback(update, context):
    """Ленивая загрузка обработчика проверки ресурсов сервера"""
    try:
        from modules.targeted_checks import handle_check_resources_callback
        server_ip = update.callback_query.data.replace('check_resources_', '')
        return handle_check_resources_callback(update, context, server_ip)
    except ImportError as e:
        debug_log(f"❌ Ошибка импорта handle_check_resources_callback: {e}")
        query = update.callback_query
        query.answer("📊 Ошибка проверки ресурсов")

def lazy_check_availability_callback(update, context):
    """Ленивая загрузка обработчика проверки доступности"""
    try:
        from modules.targeted_checks import handle_single_check
        server_id = update.callback_query.data.replace('check_availability_', '')
        return handle_single_check(update, context, server_id)
    except ImportError as e:
        debug_log(f"❌ Ошибка импорта handle_single_check: {e}")
        query = update.callback_query
        query.answer("🔍 Ошибка проверки доступности")

def lazy_check_resources_single_callback(update, context):
    """Ленивая загрузка обработчика проверки ресурсов"""
    try:
        from modules.targeted_checks import handle_single_resources
        server_id = update.callback_query.data.replace('check_resources_', '')
        return handle_single_resources(update, context, server_id)
    except ImportError as e:
        debug_log(f"❌ Ошибка импорта handle_single_resources: {e}")
        query = update.callback_query
        query.answer("📊 Ошибка проверки ресурсов")

def lazy_refresh_server_menu(update, context):
    """Ленивая загрузка обновления меню серверов"""
    try:
        from modules.targeted_checks import refresh_server_menu
        return refresh_server_menu(update, context)
    except ImportError as e:
        debug_log(f"❌ Ошибка импорта refresh_server_menu: {e}")
        query = update.callback_query
        query.answer("🔄 Ошибка обновления меню")