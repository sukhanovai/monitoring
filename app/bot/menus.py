"""
Server Monitoring System v4.4.12 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Модуль для настройки команд и главного меню

"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

def setup_menu_commands(bot, extension_manager):
    """Настройка команд меню бота"""
    commands = [
        BotCommand("start", "Запуск бота"),
        BotCommand("check", "Проверить серверы"),
        BotCommand("status", "Статус мониторинга"),
        BotCommand("servers", "Список серверов"),
        BotCommand("report", "Ежедневный отчет"),
        BotCommand("stats", "Статистика"),
        BotCommand("control", "Управление"),
        BotCommand("diagnose_ssh", "Диагностика SSH"),
        BotCommand("silent", "Тихий режим"),
        BotCommand("extensions", "🛠️ Управление расширениями"),
        BotCommand("settings", "⚙️ Управление настройками"),
        BotCommand("debug", "🐛 Управление отладкой"),
        BotCommand("help", "Помощь"),
    ]
    
    # Динамическое добавление команд расширений
    if extension_manager.is_extension_enabled('backup_monitor'):
        commands.extend([
            BotCommand("backup", "📊 Бэкапы"),
            BotCommand("backup_search", "🔍 Поиск бэкапов"),
            BotCommand("backup_help", "❓ Помощь по бэкапам"),
        ])
    
    if extension_manager.is_extension_enabled('database_backup_monitor'):
        commands.append(BotCommand("db_backups", "🗃️ Бэкапы БД"))
    
    bot.set_my_commands(commands)
    return True

def create_main_menu(extension_manager):
    """Создание главного меню"""
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить серверы", callback_data='manual_check')],
        [InlineKeyboardButton("📊 Проверить ресурсы", callback_data='check_resources')],
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
        [InlineKeyboardButton("🐛 Отладка", callback_data='debug_menu')],
    ]
    
    if (extension_manager.is_extension_enabled('backup_monitor') or 
        extension_manager.is_extension_enabled('database_backup_monitor')):
        keyboard.append([InlineKeyboardButton("💾 Бэкапы", callback_data='backup_main')])
    
    keyboard.extend([
        [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')],
        [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')] 
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_start_message(extension_manager, debug_mode=False):
    """Получить приветственное сообщение"""
    welcome_text = (
        "🤖 *Серверный мониторинг*\n\n"
        "✅ Система работает\n\n"
    )
    
    welcome_text += f"🐛 *Режим отладки:* {'🟢 ВКЛ' if debug_mode else '🔴 ВЫКЛ'}\n"
    
    if extension_manager.is_extension_enabled('web_interface'):
        welcome_text += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
        welcome_text += "_*доступен только в локальной сети_\n"
    else:
        welcome_text += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
    
    return welcome_text

def get_help_message(extension_manager):
    """Получить сообщение помощи"""
    help_text = (
        "🤖 *Помощь по мониторингу*\n\n"
        "*Основные команды:*\n"
        "• `/start` - Главное меню\n"
        "• `/check` - Быстрая проверка серверов\n"
        "• `/servers` - Список всех серверов\n"
        "• `/control` - Управление мониторингом\n"
        "• `/extensions` - Управление расширениями\n"
        "• `/debug` - Управление отладкой 🆕\n\n"
        "*Диагностика:*\n"
        "• `/diagnose_ssh <ip>` - Проверка SSH подключения\n"
        "• `/silent` - Статус тихого режима\n\n"
        "*Отчеты:*\n"
        "• `/report` - Принудительная отправка утреннего отчета\n"
        "• `/stats` - Статистика работы\n\n"
    )
    
    if extension_manager.is_extension_enabled('backup_monitor'):
        help_text += "*Бэкапы Proxmox:*\n"
        help_text += "• `/backup` - Статус бэкапов\n"
        help_text += "• `/backup_search` - Поиск по бэкапам\n"
        help_text += "• `/backup_help` - Помощь по бэкапам\n\n"
    
    help_text += "*Веб-интерфейс:*\n"
    if extension_manager.is_extension_enabled('web_interface'):
        help_text += "🌐 http://192.168.20.2:5000\n"
        help_text += "_*доступен только в локальной сети_\n\n"
    else:
        help_text += "🔴 В настоящее время отключен\n\n"
    
    help_text += "*Используйте кнопки меню для удобного управления*"
    
    return help_text

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

def start_command(update, context):
    """Обработчик команды /start"""
    from extensions.extension_manager import extension_manager
    
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        return
    
    try:
        from app.config.debug import DEBUG_MODE
        debug_mode = DEBUG_MODE
    except ImportError:
        debug_mode = False
    
    welcome_text = get_start_message(extension_manager, debug_mode)
    reply_markup = create_main_menu(extension_manager)
    
    update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

def help_command(update, context):
    """Обработчик команды /help"""
    from extensions.extension_manager import extension_manager
    
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        return
    
    help_text = get_help_message(extension_manager)
    update.message.reply_text(help_text, parse_mode='Markdown')

def check_access(chat_id):
    """Проверка доступа к боту"""
    from app.config import settings
    return str(chat_id) in settings.CHAT_IDS

def show_extensions_menu(update, context):
    """Показывает меню управления расширениями"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    from extensions.extension_manager import extension_manager
    
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id
    
    extensions_status = extension_manager.get_extensions_status()
    
    message = "🛠️ *Управление расширениями*\n\n"
    message += "📊 *Статус расширений:*\n\n"
    
    # Создаем клавиатуру
    keyboard = []
    
    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']
        
        status_icon = "🟢" if enabled else "🔴"
        toggle_text = "🔴 Выключить" if enabled else "🟢 Включить"
        
        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   Статус: {'Включено' if enabled else 'Отключено'}\n\n"
        
        # Добавляем кнопку переключения для каждого расширения
        keyboard.append([
            InlineKeyboardButton(
                f"{toggle_text} {ext_info['name']}", 
                callback_data=f'ext_toggle_{ext_id}'
            )
        ])
    
    # Добавляем кнопки управления
    keyboard.extend([
        [InlineKeyboardButton("📊 Включить все", callback_data='ext_enable_all')],
        [InlineKeyboardButton("📋 Отключить все", callback_data='ext_disable_all')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

def extensions_callback_handler(update, context):
    """Обработчик callback'ов для управления расширениями"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    from extensions.extension_manager import extension_manager
    
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'extensions_refresh':
        show_extensions_menu(update, context)
    
    elif data == 'ext_enable_all':
        enable_all_extensions(update, context)
    
    elif data == 'ext_disable_all':
        disable_all_extensions(update, context)
    
    elif data.startswith('ext_toggle_'):
        extension_id = data.replace('ext_toggle_', '')
        toggle_extension(update, context, extension_id)
    
    elif data == 'monitor_status':
        try:
            from app.bot.handlers import monitor_status
            monitor_status(update, context)
        except Exception as e:
            print(f"Ошибка при переходе к статусу мониторинга: {e}")
            query.edit_message_text("❌ Ошибка при загрузке статуса мониторинга")
    
    elif data == 'close':
        try:
            query.delete_message()
        except:
            query.edit_message_text("✅ Меню закрыто")

def toggle_extension(update, context, extension_id):
    """Переключает расширение"""
    from extensions.extension_manager import extension_manager
    
    query = update.callback_query
    success, message = extension_manager.toggle_extension(extension_id)
    
    if success:
        query.answer(message)
        show_extensions_menu(update, context)
    else:
        query.answer(message, show_alert=True)

def enable_all_extensions(update, context):
    """Включает все расширения"""
    from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS
    
    query = update.callback_query
    
    enabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.enable_extension(ext_id)
        if success:
            enabled_count += 1
    
    query.answer(f"✅ Включено {enabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
    show_extensions_menu(update, context)

def disable_all_extensions(update, context):
    """Отключает все расширения"""
    from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS
    
    query = update.callback_query
    
    disabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled_count += 1
    
    query.answer(f"✅ Отключено {disabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
    show_extensions_menu(update, context)

def check_command(update, context):
    """Обработчик команды /check"""
    from app.bot.handlers import manual_check_handler
    return manual_check_handler(update, context)

def status_command(update, context):
    """Обработчик команды /status"""
    from app.bot.handlers import monitor_status
    return monitor_status(update, context)

def silent_command(update, context):
    """Обработчик команды /silent"""
    from app.bot.handlers import silent_command as silent_cmd
    return silent_cmd(update, context)

def control_command(update, context):
    """Обработчик команды /control"""
    from app.bot.handlers import control_command as control_cmd
    return control_cmd(update, context)

def servers_command(update, context):
    """Обработчик команды /servers"""
    from extensions.server_checks import servers_command as servers_cmd
    return servers_cmd(update, context)

def report_command(update, context):
    """Обработчик команды /report"""
    from app.bot.handlers import send_morning_report_handler
    return send_morning_report_handler(update, context)

def stats_command(update, context):
    """Обработчик команды /stats"""
    from extensions.utils import stats_command as stats_cmd
    return stats_cmd(update, context)

def diagnose_ssh_command(update, context):
    """Обработчик команды /diagnose_ssh"""
    from extensions.utils import diagnose_ssh_command as diagnose_cmd
    return diagnose_cmd(update, context)

def extensions_command(update, context):
    """Обработчик команды /extensions"""
    from app.bot.menus import show_extensions_menu
    return show_extensions_menu(update, context)

def debug_command(update, context):
    """Обработчик команды /debug"""
    from app.bot.debug_menu import debug_menu
    return debug_menu.show_menu(update, context)

def backup_command(update, context):
    """Обработчик команды /backup"""
    from extensions.extension_manager import extension_manager
    
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')]
            ])
        )
        return
    
    try:
        from extensions.backup_monitor.bot_handler import backup_command as backup_cmd
        return backup_cmd(update, context)
    except ImportError as e:
        update.message.reply_text(f"⚠️ Модуль бэкапов временно недоступен: {e}")

def backup_search_command(update, context):
    """Обработчик команды /backup_search"""
    update.message.reply_text("🔍 Поиск бэкапов временно недоступен (в процессе переноса)")

def backup_help_command(update, context):
    """Обработчик команды /backup_help"""
    update.message.reply_text("❓ Помощь по бэкапам временно недоступна (в процессе переноса)")
