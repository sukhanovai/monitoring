"""
Server Monitoring System v4.0.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчики для управления настройками через бота
Версия: 4.0.3
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from settings_manager import settings_manager
import json

def get_debug_log():
    """Безопасная функция для логирования"""
    try:
        from app.utils.common import debug_log
        return debug_log
    except ImportError:
        # Заглушка если модуль не доступен
        def fallback_log(message):
            print(f"DEBUG: {message}")
        return fallback_log

debug_logger = get_debug_log()

def settings_command(update, context):
    """Команда управления настройками"""
    keyboard = [
        [InlineKeyboardButton("🤖 Настройки бота", callback_data='settings_telegram')],
        [InlineKeyboardButton("⏰ Временные настройки", callback_data='settings_time')],
        [InlineKeyboardButton("🔧 Мониторинг", callback_data='settings_monitoring')],
        [InlineKeyboardButton("💻 Ресурсы", callback_data='settings_resources')],
        [InlineKeyboardButton("🔐 Аутентификация", callback_data='settings_auth')],
        [InlineKeyboardButton("🖥️ Серверы", callback_data='settings_servers')],
        [InlineKeyboardButton("💾 Бэкапы", callback_data='settings_backup')],
        [InlineKeyboardButton("🌐 Веб-интерфейс", callback_data='settings_web')],
        [InlineKeyboardButton("📊 Просмотр всех настроек", callback_data='settings_view_all')],
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')]    
    ]
    
    if update.message:
        update.message.reply_text(
            "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.callback_query.edit_message_text(
            "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def show_telegram_settings(update, context):
    """Показать настройки Telegram - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    token = settings_manager.get_setting('TELEGRAM_TOKEN', '')
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    token_display = "🟢 Установлен" if token else "🔴 Не установлен"
    chats_display = f"{len(chat_ids)} чатов" if chat_ids else "🔴 Не настроены"
    
    message = (
        "🤖 *Настройки Telegram*\n\n"
        f"• Токен бота: {token_display}\n"
        f"• ID чатов: {chats_display}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 Установить токен", callback_data='set_telegram_token')],
        [InlineKeyboardButton("💬 Управление чатами", callback_data='manage_chats')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_monitoring_settings(update, context):
    """Показать настройки мониторинга - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    check_interval = settings_manager.get_setting('CHECK_INTERVAL', 60)
    max_fail_time = settings_manager.get_setting('MAX_FAIL_TIME', 900)
    
    # Новые настройки таймаутов
    windows_2025_timeout = settings_manager.get_setting('WINDOWS_2025_TIMEOUT', 35)
    domain_timeout = settings_manager.get_setting('DOMAIN_SERVERS_TIMEOUT', 20)
    admin_timeout = settings_manager.get_setting('ADMIN_SERVERS_TIMEOUT', 25)
    standard_timeout = settings_manager.get_setting('STANDARD_WINDOWS_TIMEOUT', 30)
    linux_timeout = settings_manager.get_setting('LINUX_TIMEOUT', 15)
    
    message = (
        "🔧 *Настройки мониторинга*\n\n"
        f"• Интервал проверки: {check_interval} сек\n"
        f"• Макс. время простоя: {max_fail_time} сек\n\n"
        "*Таймауты серверов:*\n"
        f"• Windows 2025: {windows_2025_timeout} сек\n"
        f"• Доменные серверы: {domain_timeout} сек\n"
        f"• Admin серверы: {admin_timeout} сек\n"
        f"• Стандартные Windows: {standard_timeout} сек\n"
        f"• Linux серверы: {linux_timeout} сек\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("⏱️ Интервал проверки", callback_data='set_check_interval')],
        [InlineKeyboardButton("🚨 Макс. время простоя", callback_data='set_max_fail_time')],
        [InlineKeyboardButton("⏰ Таймауты серверов", callback_data='server_timeouts')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_time_settings(update, context):
    """Показать временные настройки"""
    query = update.callback_query
    query.answer()
    
    silent_start = settings_manager.get_setting('SILENT_START', 20)
    silent_end = settings_manager.get_setting('SILENT_END', 9)
    data_collection = settings_manager.get_setting('DATA_COLLECTION_TIME', '08:30')
    
    message = (
        "⏰ *Временные настройки*\n\n"
        f"• Тихий режим: {silent_start}:00 - {silent_end}:00\n"
        f"• Сбор данных: {data_collection}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔇 Начало тихого режима", callback_data='set_silent_start')],
        [InlineKeyboardButton("🔊 Конец тихого режима", callback_data='set_silent_end')],
        [InlineKeyboardButton("📊 Время сбора данных", callback_data='set_data_collection')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_resource_settings(update, context):
    """Показать настройки ресурсов"""
    query = update.callback_query
    query.answer()
    
    cpu_warning = settings_manager.get_setting('CPU_WARNING', 80)
    cpu_critical = settings_manager.get_setting('CPU_CRITICAL', 90)
    ram_warning = settings_manager.get_setting('RAM_WARNING', 85)
    ram_critical = settings_manager.get_setting('RAM_CRITICAL', 95)
    disk_warning = settings_manager.get_setting('DISK_WARNING', 80)
    disk_critical = settings_manager.get_setting('DISK_CRITICAL', 90)
    
    message = (
        "💻 *Настройки ресурсов*\n\n"
        f"• CPU предупреждение: {cpu_warning}%\n"
        f"• CPU критический: {cpu_critical}%\n"
        f"• RAM предупреждение: {ram_warning}%\n"
        f"• RAM критический: {ram_critical}%\n"
        f"• Disk предупреждение: {disk_warning}%\n"
        f"• Disk критический: {disk_critical}%\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("💻 CPU предупреждение", callback_data='set_cpu_warning')],
        [InlineKeyboardButton("💻 CPU критический", callback_data='set_cpu_critical')],
        [InlineKeyboardButton("🧠 RAM предупреждение", callback_data='set_ram_warning')],
        [InlineKeyboardButton("🧠 RAM критический", callback_data='set_ram_critical')],
        [InlineKeyboardButton("💾 Disk предупреждение", callback_data='set_disk_warning')],
        [InlineKeyboardButton("💾 Disk критический", callback_data='set_disk_critical')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_settings(update, context):
    """Показать настройки бэкапов - С ИЗМЕНЕННЫМ CALLBACK"""
    query = update.callback_query
    query.answer()
    
    backup_alert_hours = settings_manager.get_setting('BACKUP_ALERT_HOURS', 24)
    backup_stale_hours = settings_manager.get_setting('BACKUP_STALE_HOURS', 36)
    
    database_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    db_categories = list(database_config.keys()) if database_config else []
    
    message = (
        "💾 *Настройки бэкапов*\n\n"
        f"• Алерты через: {backup_alert_hours}ч\n"
        f"• Устаревание через: {backup_stale_hours}ч\n"
        f"• Категории БД: {len(db_categories)}\n\n"
        "Выберите раздел для настройки:"
    )
    
    keyboard = [
        [InlineKeyboardButton("⏰ Временные интервалы", callback_data='backup_times')],
        [InlineKeyboardButton("🗃️ Базы данных", callback_data='settings_db_main')],
        [InlineKeyboardButton("🔍 Паттерны", callback_data='backup_patterns')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases_settings(update, context):
    """Показать настройки баз данных для бэкапов"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"
    
    if not db_config:
        message += "❌ *Базы данных не настроены*\n\n"
        message += "Здесь вы можете настроить категории и базы данных для мониторинга бэкапов."
    else:
        message += "*Текущие настройки:*\n\n"
        for category, databases in db_config.items():
            message += f"📁 *{category.upper()}*\n"
            message += f"   Количество БД: {len(databases)}\n"
            # Показываем несколько примеров
            sample_dbs = list(databases.values())[:2]
            for db_name in sample_dbs:
                message += f"   • {db_name}\n"
            if len(databases) > 2:
                message += f"   • ... и еще {len(databases) - 2} БД\n"
            message += "\n"
    
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить категорию", callback_data='settings_db_add_category')],
        [InlineKeyboardButton("✏️ Редактировать категорию", callback_data='settings_db_edit_category')],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data='settings_db_delete_category')],
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='settings_db_view_all')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_all_settings(update, context):
    """Показать все настройки"""
    query = update.callback_query
    query.answer()
    
    all_settings = settings_manager.get_all_settings()
    
    message = "📊 *Все настройки системы*\n\n"
    
    for category in settings_manager.get_categories():
        message += f"*{category.upper()}:*\n"
        category_settings = {k: v for k, v in all_settings.items() if k.lower().startswith(category.lower()) or settings_manager.get_setting(k, category='') == category}
        
        for key, value in category_settings.items():
            if key == 'TELEGRAM_TOKEN' and value:
                value = '***' + value[-4:]  # Показываем только последние 4 символа
            elif key == 'CHAT_IDS':
                value = f"{len(value)} чатов"
            elif isinstance(value, (list, dict)):
                value = f"{len(value)} элементов"
            
            message += f"• {key}: {value}\n"
        message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def settings_callback_handler(update, context):
    """Обработчик callback'ов настроек"""
    query = update.callback_query
    data = query.data
    
    # если это callback от бэкапов, НЕ обрабатываем здесь
    if data.startswith('db_') or data.startswith('backup_'):
        query.answer("⚙️ Перенаправление к модулю бэкапов...")
        # Передаем обработку дальше по цепочке
        return

    try:
        # Основные категории настроек
        if data == 'settings_main':
            settings_command(update, context)
        elif data == 'settings_telegram':
            show_telegram_settings(update, context)
        elif data == 'settings_monitoring':
            show_monitoring_settings(update, context)
        elif data == 'settings_time':
            show_time_settings(update, context)
        elif data == 'settings_resources':
            show_resource_settings(update, context)
        elif data == 'settings_auth':
            show_auth_settings(update, context)  # Теперь упрощенная версия
        elif data == 'settings_servers':
            show_servers_settings(update, context)
        elif data == 'settings_backup':
            show_backup_settings(update, context)
        elif data == 'settings_web':
            show_web_settings(update, context)
        elif data == 'settings_view_all':
            view_all_settings_handler(update, context)
        
        # Подпункты
        elif data == 'backup_times':
            show_backup_times(update, context)
        elif data == 'backup_patterns':
            show_backup_patterns_menu(update, context)
        
        # Новые обработчики для настроек БД
        elif data == 'settings_db_main':
            show_backup_databases_settings(update, context)
        elif data == 'settings_db_add_category':
            add_database_category_handler(update, context)
        elif data == 'settings_db_edit_category':
            edit_databases_handler(update, context)
        elif data == 'settings_db_delete_category':
            delete_database_category_handler(update, context)
        elif data == 'settings_db_view_all':
            view_all_databases_handler(update, context)
        
        # Обработчики для новых пунктов меню
        elif data == 'manage_chats':
            manage_chats_handler(update, context)
        elif data == 'server_timeouts':
            show_server_timeouts(update, context)  # Теперь упрощенная версия
        elif data == 'add_server':
            add_server_handler(update, context)
        
        # Обработчики для установки значений
        elif data.startswith('set_'):
            handle_setting_input(update, context, data.replace('set_', ''))
        
        # Управление чатами
        elif data == 'add_chat':
            add_chat_handler(update, context)
        elif data == 'remove_chat':
            remove_chat_handler(update, context)
        
        # Паттерны бэкапов
        elif data == 'view_patterns':
            view_patterns_handler(update, context)
        elif data == 'add_pattern':
            add_pattern_handler(update, context)
        
        # Обработчики для редактирования и удаления категорий БД
        elif data.startswith('settings_db_edit_'):
            category = data.replace('settings_db_edit_', '')
            edit_database_category_details(update, context, category)
        elif data.startswith('settings_db_delete_'):
            category = data.replace('settings_db_delete_', '')
            delete_database_category_confirmation(update, context, category)
        
        # Обработчики для серверов
        elif data == 'servers_list':
            show_servers_list(update, context)
        elif data.startswith('delete_server_'):
            ip = data.replace('delete_server_', '')
            delete_server_confirmation(update, context, ip)
        
        # Обработчики для таймаутов серверов
        elif data == 'set_windows_2025_timeout':
            handle_setting_input(update, context, 'windows_2025_timeout')
        elif data == 'set_domain_servers_timeout':
            handle_setting_input(update, context, 'domain_servers_timeout')
        elif data == 'set_admin_servers_timeout':
            handle_setting_input(update, context, 'admin_servers_timeout')
        elif data == 'set_standard_windows_timeout':
            handle_setting_input(update, context, 'standard_windows_timeout')
        elif data == 'set_linux_timeout':
            handle_setting_input(update, context, 'linux_timeout')
        elif data == 'set_ping_timeout':
            handle_setting_input(update, context, 'ping_timeout')
        
        # Обработчики типов серверов
        elif data.startswith('server_type_'):
            handle_server_type(update, context)
        
        # Аутентификация
        elif data == 'settings_auth':
            show_auth_settings(update, context)
        elif data == 'ssh_auth_settings':
            show_ssh_auth_settings(update, context)
        
        # Windows аутентификация
        elif data == 'windows_auth_main':
            show_windows_auth_settings(update, context)
        elif data == 'windows_auth_list':
            show_windows_auth_list(update, context)
        elif data == 'windows_auth_add':
            show_windows_auth_add(update, context)
        elif data == 'windows_auth_by_type':
            show_windows_auth_by_type(update, context)
        elif data == 'windows_auth_manage_types':
            show_windows_auth_manage_types(update, context)
        
        # Обработчики типов для Windows учетных данных
        elif data.startswith('cred_type_'):
            handle_credential_type_selection(update, context)

        # Обработчики управления типами серверов Windows
        elif data.startswith('manage_type_'):
            handle_server_type_management(update, context)

        # Обработчики для управления типами серверов (подтверждение операций)
        elif data.startswith('merge_confirm_'):
            parts = data.replace('merge_confirm_', '').split('_')
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = '_'.join(parts[1:])
                merge_server_types_confirmation(update, context, source_type, target_type)

        elif data.startswith('delete_type_confirm_'):
            server_type = data.replace('delete_type_confirm_', '')
            delete_server_type_confirmation(update, context, server_type)

        # Обработчики для выполнения операций с типами серверов
        elif data.startswith('merge_execute_'):
            parts = data.replace('merge_execute_', '').split('_')
            if len(parts) >= 2:
                source_type = parts[0]
                target_type = '_'.join(parts[1:])
                execute_server_type_merge(update, context, source_type, target_type)

        elif data.startswith('delete_type_execute_'):
            server_type = data.replace('delete_type_execute_', '')
            execute_server_type_delete(update, context, server_type)

        # Обработчики для закрытия меню
        elif data == 'close':
            try:
                query.delete_message()
            except:
                query.edit_message_text("✅ Меню закрыто")
        
        else:
            query.answer("⚙️ Этот раздел в разработке")
    
    except Exception as e:
        print(f"❌ Ошибка в settings_callback_handler: {e}")
        debug_logger(f"Ошибка в settings_callback_handler: {e}")
        query.answer("❌ Произошла ошибка при обработке запроса")
    
    query.answer()

def handle_setting_input(update, context, setting_key):
    """Обработчик ввода значений настроек - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем какое настройку меняем
    context.user_data['editing_setting'] = setting_key
    
    setting_descriptions = {
        # Существующие настройки...
        'telegram_token': 'Введите новый токен Telegram бота:',
        'check_interval': 'Введите новый интервал проверки (в секундах):',
        'max_fail_time': 'Введите максимальное время простоя (в секундах):',
        'silent_start': 'Введите час начала тихого режима (0-23):',
        'silent_end': 'Введите час окончания тихого режима (0-23):',
        'data_collection': 'Введите время сбора данных (формат HH:MM):',
        'cpu_warning': 'Введите порог предупреждения для CPU (%):',
        'cpu_critical': 'Введите критический порог для CPU (%):',
        'ram_warning': 'Введите порог предупреждения для RAM (%):',
        'ram_critical': 'Введите критический порог для RAM (%):',
        'disk_warning': 'Введите порог предупреждения для Disk (%):',
        'disk_critical': 'Введите критический порог для Disk (%):',
        'ssh_username': 'Введите имя пользователя SSH:',
        'ssh_key_path': 'Введите путь к SSH ключу:',
        'web_port': 'Введите порт веб-интерфейса:',
        'web_host': 'Введите хост веб-интерфейса:',
        'backup_alert_hours': 'Введите количество часов для алертов о бэкапах:',
        'backup_stale_hours': 'Введите количество часов для устаревших бэкапов:',
        
        # Новые таймауты серверов
        'windows_2025_timeout': 'Введите таймаут для Windows 2025 серверов (в секундах):',
        'domain_servers_timeout': 'Введите таймаут для доменных серверов (в секундах):',
        'admin_servers_timeout': 'Введите таймаут для Admin серверов (в секундах):',
        'standard_windows_timeout': 'Введите таймаут для стандартных Windows серверов (в секундах):',
        'linux_timeout': 'Введите таймаут для Linux серверов (в секундах):',
        'ping_timeout': 'Введите таймаут для Ping серверов (в секундах):',
    }
    
    message = setting_descriptions.get(setting_key, f'Введите новое значение для {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_main')]
        ])
    )

def handle_setting_value(update, context):
    """Обработчик получения значения настройки - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    # Сначала проверяем, не добавляется ли Windows учетная запись
    if context.user_data.get('adding_windows_cred'):
        return handle_windows_credential_input(update, context)
    
    # Проверяем, не создается ли тип серверов
    if context.user_data.get('creating_server_type'):
        return handle_server_type_creation(update, context)
    
    # Проверяем, не редактируется ли тип серверов
    if context.user_data.get('editing_server_type'):
        return handle_server_type_editing(update, context)
    
    # Затем проверяем, не добавляется ли сервер
    if context.user_data.get('adding_server'):
        return handle_server_input(update, context)
    
    # Затем проверяем, не добавляется ли категория БД
    if context.user_data.get('adding_db_category'):
        return handle_db_category_input(update, context)
    
    # Если это обычная настройка
    if 'editing_setting' not in context.user_data:
        return
        
    setting_key = context.user_data['editing_setting']
    new_value = update.message.text
    
    try:
        # Определяем тип данных и преобразуем
        setting_types = {
            'check_interval': 'int', 'max_fail_time': 'int', 'silent_start': 'int', 'silent_end': 'int',
            'cpu_warning': 'int', 'cpu_critical': 'int', 'ram_warning': 'int', 'ram_critical': 'int',
            'disk_warning': 'int', 'disk_critical': 'int', 'web_port': 'int',
            'backup_alert_hours': 'int', 'backup_stale_hours': 'int'
        }
        
        if setting_key in setting_types and setting_types[setting_key] == 'int':
            new_value = int(new_value)
        elif setting_key == 'data_collection':
            # Проверяем формат времени
            import re
            if not re.match(r'^\d{1,2}:\d{2}$', new_value):
                raise ValueError("Неверный формат времени. Используйте HH:MM")
        
        # Сохраняем настройку
        category_map = {
            'telegram_token': 'telegram',
            'check_interval': 'monitoring', 'max_fail_time': 'monitoring',
            'silent_start': 'time', 'silent_end': 'time', 'data_collection': 'time',
            'cpu_warning': 'resources', 'cpu_critical': 'resources',
            'ram_warning': 'resources', 'ram_critical': 'resources',
            'disk_warning': 'resources', 'disk_critical': 'resources',
            'ssh_username': 'auth', 'ssh_key_path': 'auth',
            'web_port': 'web', 'web_host': 'web',
            'backup_alert_hours': 'backup', 'backup_stale_hours': 'backup'
        }
        
        db_key = setting_key.upper() if setting_key != 'telegram_token' else 'TELEGRAM_TOKEN'
        category = category_map.get(setting_key, 'general')
        
        settings_manager.set_setting(db_key, new_value, category)
        
        # Очищаем контекст
        del context.user_data['editing_setting']
        
        update.message.reply_text(
            f"✅ Настройка {db_key} успешно обновлена!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Вернуться к настройкам", callback_data='settings_main')]
            ])
        )
        
    except ValueError as e:
        update.message.reply_text(f"❌ Ошибка: {e}\nПопробуйте еще раз:")
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка сохранения: {e}")
        
def show_web_settings(update, context):
    """Показать настройки веб-интерфейса - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    web_port = settings_manager.get_setting('WEB_PORT', 5000)
    web_host = settings_manager.get_setting('WEB_HOST', '0.0.0.0')
    
    message = (
        "🌐 *Настройки веб-интерфейса*\n\n"
        f"• Порт: {web_port}\n"
        f"• Хост: {web_host}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔌 Порт веб-интерфейса", callback_data='set_web_port')],
        [InlineKeyboardButton("🌐 Хост веб-интерфейса", callback_data='set_web_host')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def get_settings_handlers():
    """Получить обработчики для настроек"""
    return [
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^manage_'),
        MessageHandler(Filters.text & ~Filters.command, handle_setting_value)
    ]

def show_auth_settings(update, context):
    """Показать настройки аутентификации - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    # Получаем статистику по Windows учетным данным
    windows_creds = settings_manager.get_windows_credentials()
    
    message = (
        "🔐 *Настройки аутентификации*\n\n"
        "*SSH аутентификация:*\n"
        f"• Пользователь: `{ssh_username}`\n"
        f"• Путь к ключу: `{ssh_key_path}`\n\n"
        "*Windows аутентификация:*\n"
        f"• Учетных записей: {len(windows_creds)}\n"
        f"• Типов серверов: {len(settings_manager.get_windows_server_types())}\n\n"
        "Выберите раздел для настройки:"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 SSH аутентификация", callback_data='ssh_auth_settings')],
        [InlineKeyboardButton("🖥️ Windows аутентификация", callback_data='windows_auth_main')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_ssh_auth_settings(update, context):
    """Показать настройки SSH аутентификации"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    message = (
        "👤 *SSH аутентификация*\n\n"
        f"• SSH пользователь: `{ssh_username}`\n"
        f"• Путь к SSH ключу: `{ssh_key_path}`\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 SSH пользователь", callback_data='set_ssh_username')],
        [InlineKeyboardButton("🔑 Путь к SSH ключу", callback_data='set_ssh_key_path')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_auth'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_servers_settings(update, context):
    """Показать настройки серверов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    servers = settings_manager.get_all_servers()
    windows_servers = [s for s in servers if s['type'] == 'rdp']
    linux_servers = [s for s in servers if s['type'] == 'ssh']
    ping_servers = [s for s in servers if s['type'] == 'ping']
    
    message = (
        "🖥️ *Настройки серверов*\n\n"
        f"• Windows серверов: {len(windows_servers)}\n"
        f"• Linux серверов: {len(linux_servers)}\n"
        f"• Ping серверов: {len(ping_servers)}\n"
        f"• Всего серверов: {len(servers)}\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Список серверов", callback_data='servers_list')],
        [InlineKeyboardButton("➕ Добавить сервер", callback_data='add_server')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_times(update, context):
    """Показать настройки временных интервалов бэкапов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    alert_hours = settings_manager.get_setting('BACKUP_ALERT_HOURS', 24)
    stale_hours = settings_manager.get_setting('BACKUP_STALE_HOURS', 36)
    
    message = (
        "⏰ *Временные интервалы бэкапов*\n\n"
        f"• Алерты через: {alert_hours} часов\n"
        f"• Устаревание через: {stale_hours} часов\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚨 Часы для алертов", callback_data='set_backup_alert_hours')],
        [InlineKeyboardButton("📅 Часы для устаревания", callback_data='set_backup_stale_hours')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases_settings(update, context):
    """Показать настройки баз данных для бэкапов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"
    
    if not db_config:
        message += "❌ *Базы данных не настроены*\n\n"
    else:
        for category, databases in db_config.items():
            message += f"*{category.upper()}* ({len(databases)} БД):\n"
            for db_key, db_name in list(databases.items())[:3]:
                message += f"• {db_name}\n"
            if len(databases) > 3:
                message += f"• ... и еще {len(databases) - 3} БД\n"
            message += "\n"
    
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='view_all_databases')],
        [InlineKeyboardButton("➕ Добавить категорию БД", callback_data='add_database_category')],
        [InlineKeyboardButton("✏️ Редактировать БД", callback_data='edit_databases')],
        [InlineKeyboardButton("🗑️ Удалить категорию", callback_data='delete_database_category')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases(update, context):
    """Показать настройки баз данных для бэкапов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Настройки баз данных для бэкапов*\n\n"
    
    for category, databases in db_config.items():
        message += f"*{category.upper()}* ({len(databases)} БД):\n"
        for db_key, db_name in list(databases.items())[:3]:
            message += f"• {db_name}\n"
        if len(databases) > 3:
            message += f"• ... и еще {len(databases) - 3} БД\n"
        message += "\n"
    
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='view_all_databases')],
        [InlineKeyboardButton("➕ Добавить БД", callback_data='add_database'),
         InlineKeyboardButton("✏️ Редактировать БД", callback_data='edit_databases')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_patterns_menu(update, context):
    """Показать меню паттернов бэкапов - С КНОПКОЙ ЗАКРЫТЬ"""
    query = update.callback_query
    query.answer()
    
    patterns = settings_manager.get_backup_patterns()
    
    message = "🔍 *Паттерны бэкапов*\n\n"
    
    total_patterns = 0
    for category, category_patterns in patterns.items():
        if isinstance(category_patterns, dict):
            for pattern_type, pattern_list in category_patterns.items():
                message += f"*{pattern_type}*: {len(pattern_list)} паттернов\n"
                total_patterns += len(pattern_list)
        else:
            message += f"*{category}*: {len(category_patterns)} паттернов\n"
            total_patterns += len(category_patterns)
    
    message += f"\nВсего паттернов: {total_patterns}\n\n"
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("📋 Просмотр паттернов", callback_data='view_patterns')],
        [InlineKeyboardButton("➕ Добавить паттерн", callback_data='add_pattern')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_setting_input(update, context, setting_key):
    """Обработчик ввода значений настроек"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем какое настройку меняем
    context.user_data['editing_setting'] = setting_key
    
    setting_descriptions = {
        'telegram_token': 'Введите новый токен Telegram бота:',
        'check_interval': 'Введите новый интервал проверки (в секундах):',
        'max_fail_time': 'Введите максимальное время простоя (в секундах):',
        'silent_start': 'Введите час начала тихого режима (0-23):',
        'silent_end': 'Введите час окончания тихого режима (0-23):',
        'data_collection': 'Введите время сбора данных (формат HH:MM):',
        'cpu_warning': 'Введите порог предупреждения для CPU (%):',
        'cpu_critical': 'Введите критический порог для CPU (%):',
        'ram_warning': 'Введите порог предупреждения для RAM (%):',
        'ram_critical': 'Введите критический порог для RAM (%):',
        'disk_warning': 'Введите порог предупреждения для Disk (%):',
        'disk_critical': 'Введите критический порог для Disk (%):',
        'ssh_username': 'Введите имя пользователя SSH:',
        'ssh_key_path': 'Введите путь к SSH ключу:',
        'web_port': 'Введите порт веб-интерфейса:',
        'web_host': 'Введите хост веб-интерфейса:',
        'backup_alert_hours': 'Введите количество часов для алертов о бэкапах:',
        'backup_stale_hours': 'Введите количество часов для устаревших бэкапов:',
    }
    
    message = setting_descriptions.get(setting_key, f'Введите новое значение для {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_main')]
        ])
    )

def add_database_category_handler(update, context):
    """Обработчик добавления категории БД"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "➕ *Добавление категории баз данных*\n\n"
        "Эта функция находится в разработке.\n"
        "Скоро здесь можно будет добавлять новые категории БД для мониторинга.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
        ])
    )

def edit_database_category_handler(update, context):
    """Обработчик редактирования категории БД"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='backup_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"✏️ {category}", callback_data=f'edit_category_{category}')])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')])
    
    query.edit_message_text(
        "✏️ *Редактирование категорий баз данных*\n\n"
        "Выберите категорию для редактирования:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_database_category_handler(update, context):
    """Обработчик удаления категории БД"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='backup_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"🗑️ {category}", callback_data=f'delete_category_{category}')])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')])
    
    query.edit_message_text(
        "🗑️ *Удаление категории баз данных*\n\n"
        "Выберите категорию для удаления:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def view_all_databases_handler(update, context):
    """Обработчик просмотра всех БД"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "📋 *Все базы данных для мониторинга*\n\n"
    
    if not db_config:
        message += "❌ *Нет настроенных баз данных*\n\n"
        message += "Добавьте категории и базы данных в настройках."
    else:
        total_dbs = 0
        for category, databases in db_config.items():
            message += f"📁 *{category.upper()}* ({len(databases)} БД):\n"
            for db_key, db_name in databases.items():
                message += f"   • {db_name}\n"
                total_dbs += 1
            message += "\n"
        
        message += f"*Итого:* {total_dbs} баз данных в {len(db_config)} категориях"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
        ])
    )

def manage_chats_handler(update, context):
    """Управление чатами - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ КНОПКИ СПИСКА ВСЕХ ЧАТОВ"""
    query = update.callback_query
    query.answer()
    
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    message = "💬 *Управление чатами*\n\n"
    message += f"Текущее количество чатов: {len(chat_ids)}\n\n"
    
    if chat_ids:
        message += "*Текущие чаты:*\n"
        for i, chat_id in enumerate(chat_ids[:5], 1):
            message += f"{i}. `{chat_id}`\n"
        if len(chat_ids) > 5:
            message += f"... и еще {len(chat_ids) - 5} чатов\n"
    else:
        message += "❌ *Чаты не настроены*\n"
    
    message += "\nВыберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data='add_chat')],
        [InlineKeyboardButton("🗑️ Удалить чат", callback_data='remove_chat')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_telegram'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_server_timeouts(update, context):
    """Таймауты серверов - УПРОЩЕННАЯ БЕЗ MARKDOWN ВЕРСИЯ"""
    query = update.callback_query
    query.answer()
    
    timeouts = settings_manager.get_setting('SERVER_TIMEOUTS', {})
    
    # Простой текст без Markdown
    message = "⏰ Таймауты серверов\n\n"
    
    if timeouts:
        for server_type, timeout in timeouts.items():
            message += f"• {server_type}: {timeout} сек\n"
    else:
        message += "❌ Таймауты не настроены\n"
        message += "Используются значения по умолчанию.\n\n"
        message += "Таймауты по умолчанию:\n"
        message += "• Windows 2025: 35 сек\n"
        message += "• Доменные серверы: 20 сек\n"
        message += "• Admin серверы: 25 сек\n"
        message += "• Стандартные Windows: 30 сек\n"
        message += "• Linux серверы: 15 сек\n"
        message += "• Ping серверы: 10 сек\n"
    
    message += "\nВыберите параметр для изменения:"
    
    keyboard = [
        [InlineKeyboardButton("🖥️ Windows 2025", callback_data='set_windows_2025_timeout')],
        [InlineKeyboardButton("🌐 Доменные серверы", callback_data='set_domain_servers_timeout')],
        [InlineKeyboardButton("🔧 Admin серверы", callback_data='set_admin_servers_timeout')],
        [InlineKeyboardButton("💻 Стандартные Windows", callback_data='set_standard_windows_timeout')],
        [InlineKeyboardButton("🐧 Linux серверы", callback_data='set_linux_timeout')],
        [InlineKeyboardButton("📡 Ping серверы", callback_data='set_ping_timeout')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_monitoring'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,  # Без parse_mode
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_server_handler(update, context):
    """Добавить сервер - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    # Сохраняем состояние добавления сервера
    context.user_data['adding_server'] = True
    context.user_data['server_stage'] = 'ip'
    
    message = (
        "➕ *Добавление сервера*\n\n"
        "Введите IP-адрес сервера:\n\n"
        "_Пример: 192.168.1.100_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_servers')]
        ])
    )

def handle_server_input(update, context):
    """Обработчик ввода данных сервера"""
    if 'adding_server' not in context.user_data or not context.user_data['adding_server']:
        return
    
    user_input = update.message.text
    stage = context.user_data.get('server_stage', 'ip')
    
    try:
        if stage == 'ip':
            # Проверка IP-адреса
            import re
            ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
            if not re.match(ip_pattern, user_input):
                update.message.reply_text("❌ Неверный формат IP-адреса. Попробуйте снова:")
                return
            
            context.user_data['server_ip'] = user_input
            context.user_data['server_stage'] = 'name'
            
            update.message.reply_text(
                "📝 Введите имя сервера:\n\n"
                "_Пример: web-server-01_",
                parse_mode='Markdown'
            )
            
        elif stage == 'name':
            context.user_data['server_name'] = user_input
            context.user_data['server_stage'] = 'type'
            
            keyboard = [
                [InlineKeyboardButton("🖥️ Windows (RDP)", callback_data='server_type_rdp')],
                [InlineKeyboardButton("🐧 Linux (SSH)", callback_data='server_type_ssh')],
                [InlineKeyboardButton("📡 Ping Only", callback_data='server_type_ping')],
                [InlineKeyboardButton("❌ Отмена", callback_data='settings_servers')]
            ]
            
            update.message.reply_text(
                "🔧 Выберите тип сервера:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
        # Сбрасываем состояние при ошибке
        context.user_data['adding_server'] = False

def handle_server_type(update, context):
    """Обработчик выбора типа сервера"""
    query = update.callback_query
    query.answer()
    
    if 'adding_server' not in context.user_data:
        return
    
    server_type = query.data.replace('server_type_', '')
    server_ip = context.user_data.get('server_ip')
    server_name = context.user_data.get('server_name')
    
    try:
        # Добавляем сервер в базу
        success = settings_manager.add_server(server_ip, server_name, server_type)
        
        if success:
            message = f"✅ *Сервер добавлен!*\n\n• IP: `{server_ip}`\n• Имя: `{server_name}`\n• Тип: `{server_type}`"
            
            # Очищаем состояние
            context.user_data['adding_server'] = False
            context.user_data.pop('server_ip', None)
            context.user_pop('server_name', None)
            context.user_data.pop('server_stage', None)
        else:
            message = "❌ Ошибка при добавлении сервера"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад к серверам", callback_data='settings_servers'),
                 InlineKeyboardButton("➕ Добавить еще", callback_data='add_server')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка: {e}")

def view_all_databases_handler(update, context):
    """Просмотр всех БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        message = "📋 *Все базы данных*\n\n❌ *Нет настроенных баз данных*"
    else:
        message = "📋 *Все базы данных*\n\n"
        total_dbs = 0
        
        for category, databases in db_config.items():
            message += f"📁 *{category.upper()}* ({len(databases)} БД):\n"
            for db_key, db_name in databases.items():
                message += f"   • {db_name}\n"
                total_dbs += 1
            message += "\n"
        
        message += f"*Итого:* {total_dbs} баз данных в {len(db_config)} категориях"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def add_database_category_handler(update, context):
    """Добавить категорию БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    context.user_data['adding_db_category'] = True
    
    message = (
        "➕ *Добавление категории БД*\n\n"
        "Введите название новой категории:\n\n"
        "_Пример: company, client, backup_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_db_main')]
        ])
    )

def edit_databases_handler(update, context):
    """Редактировать БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='settings_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"✏️ {category}", callback_data=f'edit_db_category_{category}')])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')])
    
    query.edit_message_text(
        "✏️ *Редактирование баз данных*\n\n"
        "Выберите категорию для редактирования:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_database_category_handler(update, context):
    """Удалить категорию БД - ОСНОВНАЯ РЕАЛИЗАЦИЯ"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    if not db_config:
        keyboard = [[InlineKeyboardButton("➕ Добавить категорию", callback_data='settings_db_add_category')]]
    else:
        keyboard = []
        for category in db_config.keys():
            keyboard.append([InlineKeyboardButton(f"🗑️ {category}", callback_data=f'delete_db_category_{category}')])
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')])
    
    query.edit_message_text(
        "🗑️ *Удаление категории БД*\n\n"
        "Выберите категорию для удаления:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
def not_implemented_handler(update, context, feature_name=""):
    """Обработчик для функций в разработке"""
    query = update.callback_query
    query.answer()
    
    message = f"🛠️ *Функция в разработке*\n\n"
    if feature_name:
        message += f"Функция '{feature_name}' находится в разработке.\n"
    message += "Скоро здесь будет доступна новая функциональность."
    
    # Определяем откуда пришел запрос для кнопки "Назад"
    back_button = 'settings_main'
    if hasattr(query, 'data'):
        if 'telegram' in query.data:
            back_button = 'settings_telegram'
        elif 'backup' in query.data:
            back_button = 'settings_backup'
        elif 'servers' in query.data:
            back_button = 'settings_servers'
        elif 'monitoring' in query.data:
            back_button = 'settings_monitoring'
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data=back_button),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def handle_db_category_input(update, context):
    """Обработчик ввода категории БД"""
    if 'adding_db_category' not in context.user_data:
        return
    
    category_name = update.message.text.strip()
    
    try:
        # Получаем текущую конфигурацию БД
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        
        # Добавляем новую категорию
        if category_name not in db_config:
            db_config[category_name] = {}
            settings_manager.set_setting('DATABASE_CONFIG', db_config)
            
            update.message.reply_text(
                f"✅ *Категория '{category_name}' добавлена!*\n\n"
                "Теперь вы можете добавить базы данных в эту категорию.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Добавить БД", callback_data=f'edit_db_category_{category_name}'),
                     InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
                ])
            )
        else:
            update.message.reply_text(
                f"❌ Категория '{category_name}' уже существует!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='settings_db_main')]
                ])
            )
    
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    
    # Очищаем состояние
    context.user_data['adding_db_category'] = False
    
def show_windows_auth_settings(update, context):
    """Показать настройки аутентификации Windows - ОСНОВНОЕ МЕНЮ"""
    query = update.callback_query
    query.answer()
    
    # Получаем статистику по учетным данным
    credentials = settings_manager.get_windows_credentials()
    server_types = settings_manager.get_windows_server_types()
    
    # Группируем по типам серверов
    stats = {}
    for cred in credentials:
        server_type = cred['server_type']
        if server_type not in stats:
            stats[server_type] = 0
        stats[server_type] += 1
    
    message = "🖥️ *Управление аутентификацией Windows*\n\n"
    message += f"• Всего учетных записей: {len(credentials)}\n"
    message += f"• Типов серверов: {len(server_types)}\n\n"
    
    if stats:
        message += "*Учетные данные по типам:*\n"
        for server_type, count in stats.items():
            message += f"• {server_type}: {count} учетных записей\n"
    else:
        message += "❌ *Учетные данные не настроены*\n"
    
    message += "\nВыберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("👥 Просмотр всех учетных записей", callback_data='windows_auth_list')],
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add')],
        [InlineKeyboardButton("📊 Учетные данные по типам", callback_data='windows_auth_by_type')],
        [InlineKeyboardButton("⚙️ Управление типами серверов", callback_data='windows_auth_manage_types')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_auth'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_windows_auth_list(update, context):
    """Показать список всех учетных записей Windows"""
    query = update.callback_query
    query.answer()
    
    credentials = settings_manager.get_windows_credentials()
    
    message = "👥 *Все учетные записи Windows*\n\n"
    
    if not credentials:
        message += "❌ *Учетные записи не найдены*\n"
    else:
        for i, cred in enumerate(credentials, 1):
            status = "🟢" if cred['enabled'] else "🔴"
            message += f"{status} *{cred['server_type']}* (приоритет: {cred['priority']})\n"
            message += f"   Пользователь: `{cred['username']}`\n"
            message += f"   Пароль: `{'*' * 8}`\n"
            message += f"   ID: {cred['id']}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add')],
        [InlineKeyboardButton("✏️ Редактировать", callback_data='windows_auth_edit')],
        [InlineKeyboardButton("🗑️ Удалить", callback_data='windows_auth_delete')],
        [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_windows_auth_add(update, context):
    """Показать форму добавления учетной записи Windows"""
    query = update.callback_query
    query.answer()
    
    # Начинаем процесс добавления
    context.user_data['adding_windows_cred'] = True
    context.user_data['cred_stage'] = 'username'
    
    message = (
        "➕ *Добавление учетной записи Windows*\n\n"
        "Введите имя пользователя:\n\n"
        "_Пример: Administrator_"
    )
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
        ])
    )

def show_windows_auth_by_type(update, context):
    """Показать учетные данные по типам серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "📊 *Учетные данные по типам серверов*\n\n"
    
    if not server_types:
        message += "❌ *Типы серверов не настроены*\n"
    else:
        for server_type in server_types:
            credentials = settings_manager.get_windows_credentials(server_type)
            message += f"*{server_type}* ({len(credentials)} учетных записей):\n"
            
            for cred in credentials[:3]:  # Показываем первые 3
                status = "🟢" if cred['enabled'] else "🔴"
                message += f"  {status} {cred['username']} (приоритет: {cred['priority']})\n"
            
            if len(credentials) > 3:
                message += f"  ... и еще {len(credentials) - 3} учетных записей\n"
            message += "\n"
    
    keyboard = [
        [InlineKeyboardButton("👥 Просмотр всех", callback_data='windows_auth_list')],
        [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add')],
        [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_windows_credential_input(update, context):
    """Обработчик ввода данных учетной записи Windows"""
    if 'adding_windows_cred' not in context.user_data:
        return
    
    user_input = update.message.text
    stage = context.user_data.get('cred_stage')
    
    try:
        if stage == 'username':
            context.user_data['cred_username'] = user_input
            context.user_data['cred_stage'] = 'password'
            
            update.message.reply_text(
                "🔒 Введите пароль:\n\n"
                "_Пароль будет сохранен в зашифрованном виде_",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
                ])
            )
            
        elif stage == 'password':
            context.user_data['cred_password'] = user_input
            context.user_data['cred_stage'] = 'server_type'
            
            # Предлагаем стандартные типы серверов
            keyboard = [
                [InlineKeyboardButton("🖥️ Windows 2025", callback_data='cred_type_windows_2025')],
                [InlineKeyboardButton("🌐 Доменные серверы", callback_data='cred_type_domain_servers')],
                [InlineKeyboardButton("🔧 Admin серверы", callback_data='cred_type_admin_servers')],
                [InlineKeyboardButton("💻 Стандартные Windows", callback_data='cred_type_standard_windows')],
                [InlineKeyboardButton("⚙️ Другой тип", callback_data='cred_type_custom')],
                [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
            ]
            
            update.message.reply_text(
                "🖥️ Выберите тип серверов для этих учетных данных:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif stage == 'server_type_custom':
            context.user_data['cred_server_type'] = user_input
            context.user_data['cred_stage'] = 'priority'
            
            update.message.reply_text(
                "📊 Введите приоритет (число):\n\n"
                "_Учетные данные с более высоким приоритетом будут использоваться первыми_",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
                ])
            )
            
        elif stage == 'priority':
            try:
                priority = int(user_input)
                context.user_data['cred_priority'] = priority
                
                # Сохраняем учетные данные
                username = context.user_data['cred_username']
                password = context.user_data['cred_password']
                server_type = context.user_data['cred_server_type']
                
                success = settings_manager.add_windows_credential(
                    username, password, server_type, priority
                )
                
                if success:
                    # Очищаем контекст
                    for key in ['adding_windows_cred', 'cred_stage', 'cred_username', 
                               'cred_password', 'cred_server_type', 'cred_priority']:
                        context.user_data.pop(key, None)
                    
                    update.message.reply_text(
                        f"✅ *Учетная запись добавлена!*\n\n"
                        f"• Пользователь: `{username}`\n"
                        f"• Тип серверов: `{server_type}`\n"
                        f"• Приоритет: `{priority}`",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("➕ Добавить еще", callback_data='windows_auth_add'),
                             InlineKeyboardButton("👥 Просмотр всех", callback_data='windows_auth_list')],
                            [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main')]
                        ])
                    )
                else:
                    update.message.reply_text("❌ Ошибка при сохранении учетных данных")
                    
            except ValueError:
                update.message.reply_text("❌ Приоритет должен быть числом. Попробуйте снова:")
                
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
        # Сбрасываем состояние при ошибке
        context.user_data['adding_windows_cred'] = False

def handle_credential_type_selection(update, context):
    """Обработчик выбора типа сервера для учетных данных"""
    query = update.callback_query
    query.answer()
    
    if 'adding_windows_cred' not in context.user_data:
        return
    
    cred_type = query.data.replace('cred_type_', '')
    
    type_mapping = {
        'windows_2025': 'windows_2025',
        'domain_servers': 'domain_servers', 
        'admin_servers': 'admin_servers',
        'standard_windows': 'standard_windows'
    }
    
    if cred_type == 'custom':
        context.user_data['cred_stage'] = 'server_type_custom'
        query.edit_message_text(
            "✏️ Введите название типа серверов:\n\n"
            "_Пример: backup_servers, web_servers_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
            ])
        )
    else:
        context.user_data['cred_server_type'] = type_mapping.get(cred_type, cred_type)
        context.user_data['cred_stage'] = 'priority'
        
        query.edit_message_text(
            "📊 Введите приоритет (число):\n\n"
            "_Учетные данные с более высоким приоритетом будут использоваться первыми_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_main')]
            ])
        )

def show_windows_auth_manage_types(update, context):
    """Управление типами серверов - ОБНОВЛЕННАЯ ВЕРСИЯ С НАСТРОЙКАМИ"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "⚙️ *Управление типами серверов*\n\n"
    
    if not server_types:
        message += "❌ *Типы серверов не настроены*\n"
    else:
        message += "*Существующие типы:*\n"
        for server_type in server_types:
            credentials = settings_manager.get_windows_credentials(server_type)
            enabled_count = sum(1 for cred in credentials if cred['enabled'])
            message += f"• *{server_type}*: {enabled_count}/{len(credentials)} активных учетных записей\n"
    
    message += "\n*Доступные действия:*\n"
    message += "• *Переименовать тип* - изменить название типа серверов\n"
    message += "• *Объединить типы* - объединить два типа в один\n"
    message += "• *Удалить тип* - удалить тип (учетные записи сохранятся)\n"
    
    keyboard = []
    
    # Кнопки для каждого типа серверов
    for server_type in server_types:
        keyboard.append([
            InlineKeyboardButton(f"✏️ {server_type}", callback_data=f'manage_type_edit_{server_type}'),
            InlineKeyboardButton(f"🔄 {server_type}", callback_data=f'manage_type_merge_{server_type}')
        ])
    
    # Общие действия
    keyboard.extend([
        [InlineKeyboardButton("➕ Создать новый тип", callback_data='manage_type_create')],
        [InlineKeyboardButton("🗑️ Удалить тип", callback_data='manage_type_delete')],
        [InlineKeyboardButton("📊 Статистика по типам", callback_data='manage_type_stats')],
        [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_main'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_server_type_management(update, context):
    """Обработчик управления типами серверов"""
    query = update.callback_query
    data = query.data
    
    if data == 'manage_type_create':
        create_server_type_handler(update, context)
    elif data == 'manage_type_delete':
        delete_server_type_handler(update, context)
    elif data == 'manage_type_stats':
        show_server_type_stats(update, context)
    elif data.startswith('manage_type_edit_'):
        server_type = data.replace('manage_type_edit_', '')
        edit_server_type_handler(update, context, server_type)
    elif data.startswith('manage_type_merge_'):
        server_type = data.replace('manage_type_merge_', '')
        merge_server_type_handler(update, context, server_type)
       

def create_server_type_handler(update, context):
    """Создание нового типа серверов"""
    query = update.callback_query
    query.answer()
    
    context.user_data['creating_server_type'] = True
    
    query.edit_message_text(
        "➕ *Создание нового типа серверов*\n\n"
        "Введите название для нового типа:\n\n"
        "_Пример: web_servers, database_servers, backup_servers_",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')]
        ])
    )

def edit_server_type_handler(update, context, old_type):
    """Редактирование типа серверов"""
    query = update.callback_query
    query.answer()
    
    context.user_data['editing_server_type'] = True
    context.user_data['old_server_type'] = old_type
    
    credentials = settings_manager.get_windows_credentials(old_type)
    
    query.edit_message_text(
        f"✏️ *Редактирование типа серверов*\n\n"
        f"Текущее название: *{old_type}*\n"
        f"Количество учетных записей: {len(credentials)}\n\n"
        "Введите новое название для этого типа:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')]
        ])
    )

def merge_server_type_handler(update, context, source_type):
    """Объединение типов серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    # Исключаем текущий тип из списка для объединения
    target_types = [t for t in server_types if t != source_type]
    
    if not target_types:
        query.answer("❌ Нет других типов для объединения")
        return
    
    message = f"🔄 *Объединение типов серверов*\n\n"
    message += f"Источник: *{source_type}*\n"
    message += f"Учетных записей: {len(settings_manager.get_windows_credentials(source_type))}\n\n"
    message += "Выберите целевой тип для объединения:"
    
    keyboard = []
    for target_type in target_types:
        cred_count = len(settings_manager.get_windows_credentials(target_type))
        keyboard.append([
            InlineKeyboardButton(
                f"🔄 {target_type} ({cred_count})", 
                callback_data=f'merge_confirm_{source_type}_{target_type}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def delete_server_type_handler(update, context):
    """Удаление типа серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "🗑️ *Удаление типа серверов*\n\n"
    message += "Выберите тип для удаления:\n\n"
    message += "*Внимание:* При удалении типа все учетные записи этого типа будут перемещены в тип 'default'"
    
    keyboard = []
    for server_type in server_types:
        if server_type != 'default':  # Не позволяем удалить тип 'default'
            cred_count = len(settings_manager.get_windows_credentials(server_type))
            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {server_type} ({cred_count})", 
                    callback_data=f'delete_type_confirm_{server_type}'
                )
            ])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')])
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_server_type_stats(update, context):
    """Показать статистику по типам серверов"""
    query = update.callback_query
    query.answer()
    
    server_types = settings_manager.get_windows_server_types()
    
    message = "📊 *Статистика по типам серверов*\n\n"
    
    total_credentials = 0
    for server_type in server_types:
        credentials = settings_manager.get_windows_credentials(server_type)
        enabled_count = sum(1 for cred in credentials if cred['enabled'])
        total_credentials += len(credentials)
        
        message += f"*{server_type}*\n"
        message += f"• Всего учетных записей: {len(credentials)}\n"
        message += f"• Активных: {enabled_count}\n"
        message += f"• Неактивных: {len(credentials) - enabled_count}\n\n"
    
    message += f"*Общая статистика:*\n"
    message += f"• Типов серверов: {len(server_types)}\n"
    message += f"• Всего учетных записей: {total_credentials}\n"
    message += f"• Среднее на тип: {total_credentials / len(server_types):.1f} учетных записей"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Обновить", callback_data='manage_type_stats')],
            [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_manage_types'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def merge_server_types_confirmation(update, context, source_type, target_type):
    """Подтверждение объединения типов серверов"""
    query = update.callback_query
    query.answer()
    
    source_creds = settings_manager.get_windows_credentials(source_type)
    target_creds = settings_manager.get_windows_credentials(target_type)
    
    message = f"🔄 *Подтверждение объединения*\n\n"
    message += f"*Источник:* {source_type}\n"
    message += f"• Учетных записей: {len(source_creds)}\n\n"
    message += f"*Цель:* {target_type}\n"
    message += f"• Учетных записей: {len(target_creds)}\n\n"
    message += f"*После объединения:*\n"
    message += f"• Тип {source_type} будет удален\n"
    message += f"• Все учетные записи будут перемещены в {target_type}\n"
    message += f"• Итоговое количество: {len(source_creds) + len(target_creds)} учетных записей\n\n"
    message += "Вы уверены, что хотите выполнить объединение?"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, объединить", callback_data=f'merge_execute_{source_type}_{target_type}'),
                InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')
            ]
        ])
    )

def delete_server_type_confirmation(update, context, server_type):
    """Подтверждение удаления типа серверов"""
    query = update.callback_query
    query.answer()
    
    credentials = settings_manager.get_windows_credentials(server_type)
    
    message = f"🗑️ *Подтверждение удаления*\n\n"
    message += f"Тип: *{server_type}*\n"
    message += f"Учетных записей: {len(credentials)}\n\n"
    message += "*Внимание:* Все учетные записи этого типа будут перемещены в тип 'default'\n\n"
    message += "Вы уверены, что хотите удалить этот тип?"
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f'delete_type_execute_{server_type}'),
                InlineKeyboardButton("❌ Отмена", callback_data='windows_auth_manage_types')
            ]
        ])
    )

def execute_server_type_merge(update, context, source_type, target_type):
    """Выполнение объединения типов серверов"""
    query = update.callback_query
    query.answer()
    
    try:
        # Получаем учетные данные исходного типа
        source_credentials = settings_manager.get_windows_credentials(source_type)
        
        # Обновляем тип для каждой учетной записи
        for cred in source_credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type=target_type
            )
        
        message = f"✅ *Типы серверов объединены!*\n\n"
        message += f"• Тип *{source_type}* удален\n"
        message += f"• Все учетные записи перемещены в *{target_type}*\n"
        message += f"• Перемещено учетных записей: {len(source_credentials)}"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка при объединении типов: {str(e)}")

def execute_server_type_delete(update, context, server_type):
    """Выполнение удаления типа серверов"""
    query = update.callback_query
    query.answer()
    
    try:
        # Получаем учетные данные удаляемого типа
        credentials = settings_manager.get_windows_credentials(server_type)
        
        # Перемещаем все учетные записи в тип 'default'
        for cred in credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type='default'
            )
        
        message = f"✅ *Тип серверов удален!*\n\n"
        message += f"• Тип *{server_type}* удален\n"
        message += f"• Все учетные записи перемещены в тип 'default'\n"
        message += f"• Перемещено учетных записей: {len(credentials)}"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка при удалении типа: {str(e)}")

def handle_server_type_creation(update, context):
    """Обработчик создания нового типа серверов"""
    new_type = update.message.text.strip()
    
    try:
        # Проверяем, не существует ли уже такой тип
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types:
            update.message.reply_text(
                f"❌ Тип '{new_type}' уже существует!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_manage_types')]
                ])
            )
            return
        
        # Создаем новую учетную запись с этим типом (можно пустую)
        success = settings_manager.add_windows_credential(
            username=f"user_{new_type}",
            password="temp_password",
            server_type=new_type,
            priority=0
        )
        
        if success:
            # Сразу удаляем временную учетную запись, если нужно
            # или оставляем как шаблон
            
            update.message.reply_text(
                f"✅ *Тип серверов '{new_type}' создан!*\n\n"
                "Теперь вы можете добавить учетные записи для этого типа.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить учетную запись", callback_data='windows_auth_add'),
                     InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
                ])
            )
        else:
            update.message.reply_text("❌ Ошибка при создании типа")
    
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    
    # Очищаем контекст
    context.user_data['creating_server_type'] = False

def handle_server_type_editing(update, context):
    """Обработчик редактирования типа серверов"""
    new_type = update.message.text.strip()
    old_type = context.user_data.get('old_server_type')
    
    try:
        # Проверяем, не существует ли уже такой тип
        existing_types = settings_manager.get_windows_server_types()
        if new_type in existing_types and new_type != old_type:
            update.message.reply_text(
                f"❌ Тип '{new_type}' уже существует!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='windows_auth_manage_types')]
                ])
            )
            return
        
        # Получаем все учетные записи старого типа
        credentials = settings_manager.get_windows_credentials(old_type)
        
        # Обновляем тип для каждой учетной записи
        for cred in credentials:
            settings_manager.update_windows_credential(
                cred['id'], 
                server_type=new_type
            )
        
        update.message.reply_text(
            f"✅ *Тип серверов переименован!*\n\n"
            f"• Старое название: {old_type}\n"
            f"• Новое название: {new_type}\n"
            f"• Обновлено учетных записей: {len(credentials)}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ К управлению типами", callback_data='windows_auth_manage_types')]
            ])
        )
    
    except Exception as e:
        update.message.reply_text(f"❌ Ошибка: {e}")
    
    # Очищаем контекст
    context.user_data['editing_server_type'] = False
    context.user_data.pop('old_server_type', None)

# Обработчики для неработающих кнопок
def add_chat_handler(update, context):
    """Добавить чат - заглушка"""
    not_implemented_handler(update, context, "Добавление чата")

def remove_chat_handler(update, context):
    """Удалить чат - заглушка"""
    not_implemented_handler(update, context, "Удаление чата")

def view_all_settings_handler(update, context):
    """Просмотр всех настроек - заглушка"""
    not_implemented_handler(update, context, "Просмотр всех настроек")

def view_patterns_handler(update, context):
    """Просмотр паттернов - заглушка"""
    not_implemented_handler(update, context, "Просмотр паттернов")

def add_pattern_handler(update, context):
    """Добавить паттерн - заглушка"""
    not_implemented_handler(update, context, "Добавление паттерна")
    