"""
Server Monitoring System v3.1.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчики для управления настройками через бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from settings_manager import settings_manager
import json

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
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')]
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
    """Показать настройки Telegram"""
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
        [InlineKeyboardButton("🔄 Проверить настройки", callback_data='settings_telegram')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# В show_monitoring_settings добавьте:
def show_monitoring_settings(update, context):
    """Показать настройки мониторинга"""
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_monitoring')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_time')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_resources')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_settings(update, context):
    """Показать настройки бэкапов"""
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
        [InlineKeyboardButton("🗃️ Базы данных", callback_data='backup_databases')],
        [InlineKeyboardButton("🔍 Паттерны", callback_data='backup_patterns')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_backup')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_view_all')],
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')]
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
        show_auth_settings(update, context)
    elif data == 'settings_servers':
        show_servers_settings(update, context)
    elif data == 'settings_backup':
        show_backup_settings(update, context)
    elif data == 'settings_web':
        show_web_settings(update, context)
    elif data == 'settings_view_all':
        show_all_settings(update, context)
    elif data == 'backup_times':
        show_backup_times(update, context)
    elif data == 'backup_databases':
        show_backup_databases(update, context)
    elif data == 'backup_patterns':
        show_backup_patterns_menu(update, context)
    elif data.startswith('set_'):
        handle_setting_input(update, context, data.replace('set_', ''))
    else:
        query.answer("⚙️ Этот раздел в разработке")
    
    query.answer()

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
    }
    
    message = setting_descriptions.get(setting_key, f'Введите новое значение для {setting_key}:')
    
    query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data='settings_main')]
        ])
    )

def handle_setting_value(update, context):
    """Обработчик получения значения настройки"""
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
    """Показать настройки веб-интерфейса"""
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_web')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
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
    """Показать настройки аутентификации"""
    query = update.callback_query
    query.answer()
    
    ssh_username = settings_manager.get_setting('SSH_USERNAME', 'root')
    ssh_key_path = settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')
    
    message = (
        "🔐 *Настройки аутентификации*\n\n"
        f"• SSH пользователь: {ssh_username}\n"
        f"• Путь к SSH ключу: {ssh_key_path}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 SSH пользователь", callback_data='set_ssh_username')],
        [InlineKeyboardButton("🔑 Путь к SSH ключу", callback_data='set_ssh_key_path')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_auth')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_servers_settings(update, context):
    """Показать настройки серверов"""
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='settings_servers')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_times(update, context):
    """Показать настройки временных интервалов бэкапов"""
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_times')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_databases(update, context):
    """Показать настройки баз данных для бэкапов"""
    query = update.callback_query
    query.answer()
    
    db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
    
    message = "🗃️ *Базы данных для бэкапов*\n\n"
    
    for category, databases in db_config.items():
        message += f"*{category.upper()}* ({len(databases)} БД):\n"
        for db_key, db_name in list(databases.items())[:3]:  # Показываем первые 3
            message += f"• {db_name}\n"
        if len(databases) > 3:
            message += f"• ... и еще {len(databases) - 3} БД\n"
        message += "\n"
    
    message += "Выберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("📋 Просмотр всех БД", callback_data='view_all_databases')],
        [InlineKeyboardButton("➕ Добавить БД", callback_data='add_database')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_databases')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_backup_patterns_menu(update, context):
    """Показать меню паттернов бэкапов"""
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
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_patterns')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_backup')]
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
