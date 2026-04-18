"""
/bot/menu/handlers.py
Server Monitoring System v8.55.7
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot menu handlers
Система мониторинга серверов
Версия: 8.55.7
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики меню бота
"""

from pathlib import Path
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from bot.menu.builder import main_menu
from bot.handlers.base import check_access as base_check_access, deny_access
from extensions.extension_manager import extension_manager
from lib.logging import debug_log
from lib.utils import progress_bar, format_duration
from config.db_settings import (
    DEBUG_MODE,
    LOG_DIR,
    DATA_DIR,
    DEBUG_LOG_FILE,
    BOT_DEBUG_LOG_FILE,
    MAIL_MONITOR_LOG_FILE,
)
from modules.targeted_checks import targeted_checks


def show_main_menu(update, context):
    if not base_check_access(update):
        deny_access(update)
        return

    config = get_config()
    text = "🤖 *Серверный мониторинг*\n"
    if getattr(config, "APP_VERSION", None):
        text += f"🔖 *Версия:* {config.APP_VERSION}\n"
    text += "\n✅ Система активна"

    if update.message:
        update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=main_menu(extension_manager)
        )
    else:
        update.callback_query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=main_menu(extension_manager)
        )

# Ленивые импорты для настроек
def lazy_import_settings_handler():
    """Ленивая загрузка обработчика настроек"""
    try:
        from bot.handlers.settings_handlers import settings_callback_handler
        return settings_callback_handler
    except ImportError as e:
        print(f"❌ Ошибка импорта settings_callback_handler: {e}")
        # Заглушка на случай ошибки
        def fallback_handler(update, context):
            query = update.callback_query
            query.answer("⚙️ Модуль настроек временно недоступен")
        return fallback_handler

# Получаем обработчик настроек
settings_callback_handler = lazy_import_settings_handler()

def lazy_import(module_name, attribute_name=None):
    """Ленивая загрузка модулей с поддержкой составных путей"""
    def import_func():
        # Для составных путей типа 'config.db_settings'
        if '.' in module_name:
            parts = module_name.split('.')
            # Импортируем корневой модуль
            module = __import__(parts[0])
            # Проходим по вложенным модулям
            for part in parts[1:]:
                module = getattr(module, part)
        else:
            # Обычный импорт
            module = __import__(module_name, fromlist=[attribute_name] if attribute_name else [])
        
        return getattr(module, attribute_name) if attribute_name else module
    return import_func

# Ленивые импорты конфига
get_config = lazy_import('config.db_settings')
get_chat_ids = lazy_import('config.db_settings', 'CHAT_IDS')
get_telegram_token = lazy_import('config.db_settings', 'TELEGRAM_TOKEN')

# Ленивые импорты утилит
get_debug_log = lambda: debug_log
get_progress_bar = lambda: progress_bar
get_extension_manager = lazy_import('extensions.extension_manager', 'extension_manager')

def setup_menu(bot):
    """Настройка меню бота с ленивой загрузкой расширений"""
    try:
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
            BotCommand("check_server", "🔍 Проверить один сервер"),
        ]
        
        # Динамическое добавление команд расширений
        extension_manager = get_extension_manager()
        if extension_manager.is_extension_enabled('backup_monitor'):
            commands.extend([
                BotCommand("backup", "📊 Бэкапы"),
                BotCommand("backup_search", "🔍 Поиск бэкапов"),
                BotCommand("backup_help", "❓ Помощь по бэкапам"),
            ])
        
        if extension_manager.is_extension_enabled('database_backup_monitor'):
            commands.append(BotCommand("db_backups", "🗃️ Бэкапы БД"))

        if extension_manager.is_extension_enabled('resource_monitor'):
            commands.append(BotCommand("check_res", "📊 Ресурсы одного сервера"))
        
        bot.set_my_commands(commands)
        debug_log("✅ Меню настроено успешно")
        return True
    except Exception as e:
        debug_log(f"❌ Ошибка настройки меню: {e}")
        return False

def legacy_check_access(chat_id):
    """Проверка доступа к боту (legacy)"""
    config = get_config()
    return str(chat_id) in config.CHAT_IDS

def start_command(update, context):
    """Обработчик команды /start с отладочной информацией"""
    if not legacy_check_access(update.effective_chat.id):
        # Для callback и обычных сообщений
        if update.message:
            update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        elif update.callback_query:
            update.callback_query.answer("⛔ У вас нет прав")
            update.callback_query.edit_message_text("⛔ У вас нет прав для использования этого бота")
        return

    keyboard = [
        [InlineKeyboardButton("🌅 Утренний отчет", callback_data='daily_report')],
        [InlineKeyboardButton("🔄 Проверить все серверы", callback_data='manual_check')],
        [InlineKeyboardButton("🔍 Проверить один сервер", callback_data='show_availability_menu')],
        [InlineKeyboardButton("🐛 Отладка", callback_data='debug_menu')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.insert(1, [InlineKeyboardButton("📊 Проверить все ресурсы", callback_data='check_resources')])
        keyboard.insert(3, [InlineKeyboardButton("📈 Ресурсы одного сервера", callback_data='show_resources_menu')])
   
    extension_manager = get_extension_manager()
    if (
        extension_manager.is_extension_enabled('backup_monitor')
        or extension_manager.is_extension_enabled('database_backup_monitor')
        or extension_manager.is_extension_enabled('mail_backup_monitor')
        or extension_manager.is_extension_enabled('stock_load_monitor')
    ):
        keyboard.append([InlineKeyboardButton("💾 Бэкапы", callback_data='backup_main')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("📦 Остатки 1С", callback_data='backup_stock_loads')])

    if extension_manager.is_extension_enabled('zfs_monitor'):
        keyboard.append([InlineKeyboardButton("🧊 ZFS", callback_data='zfs_menu')])
    if extension_manager.is_extension_enabled('zfs_pool_free_space_monitor'):
        keyboard.append([InlineKeyboardButton("💽 Свободное место ZFS пулов", callback_data='zfs_pool_free_space_menu')])
    
    keyboard.extend([
        [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')],
        [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
        [InlineKeyboardButton("⚙️ Управление настройками", callback_data='settings_main')],
        [InlineKeyboardButton("ℹ️ О боте", callback_data='about_bot')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')] 
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    config = get_config()
    welcome_text = "🤖 *Серверный мониторинг*\n"
    if getattr(config, "APP_VERSION", None):
        welcome_text += f"🔖 *Версия:* {config.APP_VERSION}\n"
    welcome_text += "\n✅ Система работает\n\n"
    
    # Информация о отладке
    try:
        welcome_text += f"🐛 *Режим отладки:* {'🟢 ВКЛ' if DEBUG_MODE else '🔴 ВЫКЛ'}\n"
    except ImportError:
        welcome_text += "🐛 *Режим отладки:* 🔴 Недоступен\n"
    
    if extension_manager.is_extension_enabled('web_interface'):
        welcome_text += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
        welcome_text += "_*доступен только в локальной сети_\n"
    else:
        welcome_text += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
    
    # Отправка сообщения в зависимости от типа обновления
    if update.message:
        update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.edit_message_text(
            welcome_text, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )

def show_about_bot(update, context):
    """Показывает сведения о боте"""
    if not base_check_access(update):
        deny_access(update)
        return

    config = get_config()
    about_text = "ℹ️ *О боте*\n\n"
    if getattr(config, "APP_VERSION", None):
        about_text += f"🔖 *Версия:* {config.APP_VERSION}\n"
    about_text += (
        "👤 *Разработчик:* Александр Суханов\n"
        "✉️ *Связь:* aleksandr.i.sukhanov@gmail.com\n"
        "📄 *Лицензия:* MIT\n"
        "🛠 *Назначение:* мониторинг доступности серверов.\n"
        "➕ *Дополнительно:* ресурсы, бэкапы, сбор и проверка данных по остаткам товаров для БД.\n"
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
    ])

    if update.message:
        update.message.reply_text(about_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.edit_message_text(
            about_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

def help_command(update, context):
    """Обработчик команды /help"""
    if not legacy_check_access(update.effective_chat.id):
        return

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
    
    # Добавляем команды бэкапов только если расширение включено
    extension_manager = get_extension_manager()
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
    
    update.message.reply_text(help_text, parse_mode='Markdown')

def main_menu_handler(update, context):
    """Обработчик для главного меню"""
    return start_command(update, context)

def monitor_main_handler(update, context):
    """Обработчик для главного меню"""
    return start_command(update, context)

# Заглушки для команд (импорты внутри функций чтобы избежать циклических импортов)
def check_command(update, context):
    from core.monitor_core import manual_check_handler
    return manual_check_handler(update, context)

def status_command(update, context):
    from core.monitor_core import monitor_status
    return monitor_status(update, context)

def silent_command(update, context):
    from core.monitor_core import silent_command as silent_cmd
    return silent_cmd(update, context)

def control_command(update, context):
    from core.monitor_core import control_command as control_cmd
    return control_cmd(update, context)

def servers_command(update, context):
    from extensions.server_checks import servers_command as servers_cmd
    return servers_cmd(update, context)

def report_command(update, context):
    """Команда для принудительной отправки утреннего отчета"""
    from core.monitor_core import send_morning_report_handler
    return send_morning_report_handler(update, context)

def stats_command(update, context):
    from lib.monitoring_utils import stats_command as stats_cmd
    return stats_cmd(update, context)

def diagnose_ssh_command(update, context):
    from lib.monitoring_utils import diagnose_ssh_command as diagnose_cmd
    return diagnose_cmd(update, context)

def backup_command(update, context):
    """Обработчик команды /backup"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')]
            ])
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_command as backup_cmd
    return backup_cmd(update, context)

def backup_search_command(update, context):
    """Обработчик команды /backup_search"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями."
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_search_command as backup_search_cmd
    return backup_search_cmd(update, context)

def backup_help_command(update, context):
    """Обработчик команды /backup_help"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями."
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_help_command as backup_help_cmd
    return backup_help_cmd(update, context)

def fix_monitor_command(update, context):
    """Команда для исправления статуса сервера мониторинга"""
    if not legacy_check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этой команды")
        return

    try:
        # Динамический импорт чтобы избежать циклических зависимостей
        from core.monitor_core import server_status
        from datetime import datetime

        config = get_config()
        monitor_server_ip = "192.168.20.2"

        if monitor_server_ip in server_status:
            server_status[monitor_server_ip]["last_up"] = datetime.now()
            server_status[monitor_server_ip]["alert_sent"] = False

            update.message.reply_text("✅ Статус сервера мониторинга исправлен")

            # Отправляем уведомление
            from telegram import Bot
            bot = Bot(token=config.TELEGRAM_TOKEN)
            for chat_id in config.CHAT_IDS:
                bot.send_message(chat_id=chat_id, text="🔧 Статус сервера мониторинга принудительно исправлен")
        else:
            update.message.reply_text("❌ Сервер мониторинга не найден в списке")

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при исправлении статуса: {e}")
        debug_log(f"Ошибка в fix_monitor_command: {e}")

def extensions_command(update, context):
    """Обработчик команды /extensions"""
    if not legacy_check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        return
    
    show_extensions_menu(update, context)

def show_extensions_menu(update, context):
    """Показывает меню управления расширениями"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id
    
    extension_manager = get_extension_manager()
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
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
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
        # ОПТИМИЗАЦИЯ: используем ленивую загрузку чтобы избежать циклических импортов
        try:
            from core.monitor_core import monitor_status
            monitor_status(update, context)
        except Exception as e:
            debug_log(f"Ошибка при переходе к статусу мониторинга: {e}")
            query.edit_message_text("❌ Ошибка при загрузке статуса мониторинга")
    
    elif data == 'close':
        try:
            query.delete_message()
        except:
            query.edit_message_text("✅ Меню закрыто")
            
def toggle_extension(update, context, extension_id):
    """Переключает расширение"""
    query = update.callback_query
    
    extension_manager = get_extension_manager()
    success, message = extension_manager.toggle_extension(extension_id)
    
    if success:
        query.answer(message)
        show_extensions_menu(update, context)
    else:
        query.answer(message, show_alert=True)

def enable_all_extensions(update, context):
    """Включает все расширения"""
    query = update.callback_query
    
    extension_manager = get_extension_manager()
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    
    enabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.enable_extension(ext_id)
        if success:
            enabled_count += 1
    
    query.answer(f"✅ Включено {enabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
    show_extensions_menu(update, context)

def disable_all_extensions(update, context):
    """Отключает все расширения"""
    query = update.callback_query
    
    extension_manager = get_extension_manager()
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    
    disabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled_count += 1
    
    query.answer(f"✅ Отключено {disabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
    show_extensions_menu(update, context)

# НОВАЯ ФУНКЦИОНАЛЬНОСТЬ: УПРАВЛЕНИЕ ОТЛАДКОЙ
def debug_command(update, context):
    """Команда управления отладкой"""
    if not legacy_check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        return
        
    show_debug_menu(update, context)

def show_debug_menu(update, context):
    """Показывает меню управления отладкой - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id
    
    # Получаем статус отладки
    debug_status = "🔴 ВЫКЛЮЧЕНА"
    try:
        debug_status = "🟢 ВКЛЮЧЕНА" if DEBUG_MODE else "🔴 ВЫКЛЮЧЕНА"
    except ImportError:
        debug_status = "🔴 НЕДОСТУПНА"
    
    message = "🐛 *Управление отладкой*\n\n"
    message += f"*Текущий статус:* {debug_status}\n\n"
    
    # Кнопка-переключатель вместо двух отдельных
    toggle_text = "🔴 Выключить отладку" if DEBUG_MODE else "🟢 Включить отладку"
    toggle_data = 'debug_disable' if DEBUG_MODE else 'debug_enable'

    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("📊 Статус системы", callback_data='debug_status')],
        [InlineKeyboardButton("🗑️ Очистить логи", callback_data='debug_clear_logs')],
        [InlineKeyboardButton("📋 Диагностика", callback_data='debug_diagnose')],
        [InlineKeyboardButton("🔧 Расширенная отладка", callback_data='debug_advanced')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
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

def debug_callback_handler(update, context):
    """Обработчик callback'ов для отладки"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'debug_enable':
        enable_debug_mode(query)
    elif data == 'debug_disable':
        disable_debug_mode(query)
    elif data == 'debug_status':
        show_debug_status(query)
    elif data == 'debug_clear_logs':
        clear_debug_logs(query)
    elif data == 'debug_diagnose':
        run_diagnostic(query)
    elif data == 'debug_advanced':
        show_advanced_debug(query)
    elif data == 'debug_menu':
        show_debug_menu(update, context)

def enable_debug_mode(query):
    """Включает режим отладки"""
    try:
        
        # Обновляем настройки логирования
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        
        # Обновляем конфигурацию отладки если доступна
        try:
            from config.debug import debug_config
            debug_config.enable_debug()
        except ImportError:
            pass
        
        debug_log("🟢 Отладка включена через меню бота")
        
        query.edit_message_text(
            "🟢 *Отладка включена*\n\n"
            "Теперь все операции будут детально логироваться.\n"
            f"Логи сохраняются в {DEBUG_LOG_FILE}\n\n"
            "*Включены функции:*\n"
            "• Детальное логирование операций\n"
            "• Отладочные сообщения в консоли\n"
            "• Диагностика подключений",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 Выключить", callback_data='debug_disable')],
                [InlineKeyboardButton("🔧 Расширенная", callback_data='debug_advanced')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка включения отладки: {e}")

def disable_debug_mode(query):
    """Выключает режим отладки"""
    try:
        # Обновляем настройки логирования
        import logging
        logging.getLogger().setLevel(logging.INFO)
        
        # Обновляем конфигурацию отладки если доступна
        try:
            from config.debug import debug_config
            debug_config.disable_debug()
        except ImportError:
            pass
        
        debug_log("🔴 Отладка выключена через меню бота")
        
        query.edit_message_text(
            "🔴 *Отладка выключена*\n\n"
            "Детальное логирование отключено.\n"
            "Сохраняется только основная информация.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 Включить", callback_data='debug_enable')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка выключения отладки: {e}")

def show_debug_status(query):
    """Показывает статус отладки и системную информацию - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    import os
    from datetime import datetime
    
    try:
        # Пытаемся импортировать psutil, но если нет - работаем без него
        try:
            import psutil
            psutil_available = True
        except ImportError:
            psutil_available = False
        
        message = "📊 *Статус системы и отладки*\n\n"
        
        # Статус отладки
        try:
            debug_status = "🟢 ВКЛ" if DEBUG_MODE else "🔴 ВЫКЛ"
        except ImportError:
            debug_status = "🔴 НЕДОСТУПЕН"
        
        message += f"🐛 *Режим отладки:* {debug_status}\n\n"
        
        # Системная информация (если psutil доступен)
        if psutil_available:
            try:
                disk_usage = psutil.disk_usage('/')
                memory = psutil.virtual_memory()
                load = psutil.getloadavg()
                
                message += "*Системные ресурсы:*\n"
                message += f"• Загрузка CPU: {load[0]:.2f} {load[1]:.2f} {load[2]:.2f}\n"
                message += f"• Память: {memory.percent:.1f}% использовано\n"
                message += f"• Диск: {disk_usage.percent:.1f}% использовано\n\n"
            except Exception as e:
                message += f"*Системные ресурсы:* Ошибка получения: {str(e)[:50]}\n\n"
        else:
            message += "*Системные ресурсы:* Модуль psutil не установлен\n\n"
        
        # Информация о логах
        message += "*Логи:*\n"
        log_files = {
            'debug.log': DEBUG_LOG_FILE,
            'bot_debug.log': BOT_DEBUG_LOG_FILE,
            'mail_monitor.log': MAIL_MONITOR_LOG_FILE,
        }
        
        for log_name, log_path in log_files.items():
            try:
                log_path = Path(log_path)
                if log_path.exists():
                    log_size = log_path.stat().st_size
                    message += f"• {log_name}: {log_size / 1024 / 1024:.2f} MB\n"
                else:
                    message += f"• {log_name}: файл не существует\n"
            except Exception as e:
                message += f"• {log_name}: ошибка проверки\n"
        
        message += "\n"
        
        # Информация о процессах
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'python3'], capture_output=True, text=True)
            python_processes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            message += f"*Процессы Python:* {python_processes}\n"
        except:
            message += "*Процессы Python:* Недоступно\n"
        
        # Информация о расширениях
        try:
            extension_manager = get_extension_manager()
            enabled_extensions = extension_manager.get_enabled_extensions()
            message += f"*Включено расширений:* {len(enabled_extensions)}\n"
        except:
            message += "*Включено расширений:* Недоступно\n"
        
        message += f"\n🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='debug_status')],
                [InlineKeyboardButton("🗑️ Очистить логи", callback_data='debug_clear_logs')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка получения статуса: {str(e)[:100]}")

def clear_debug_logs(query):
    """Очищает файлы логов - БЕЗ КНОПКИ ДИАГНОСТИКИ"""
    import logging
    
    try:
        log_files = [
            DEBUG_LOG_FILE,
            BOT_DEBUG_LOG_FILE,
            MAIL_MONITOR_LOG_FILE,
        ]
        
        cleared = 0
        errors = []
        
        for log_file in log_files:
            try:
                log_file = Path(log_file)
                if log_file.exists():
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
                    
                    # Переконфигурируем логгер если это debug.log
                    if log_file.name == 'debug.log':
                        logging.getLogger().handlers[0].flush()
                else:
                    # Создаем пустой файл если не существует
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
            except Exception as e:
                errors.append(f"Ошибка очистки {log_file}: {e}")
        
        message = f"✅ *Логи очищены*\n\nОчищено файлов: {cleared}/{len(log_files)}"
        
        if errors:
            message += f"\n\n*Ошибки:*\n" + "\n".join(errors[:3])
        
        debug_log("🗑️ Логи очищены через меню бота")
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='debug_clear_logs')],
                [InlineKeyboardButton("📊 Статус системы", callback_data='debug_status')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка очистки логов: {e}")

def run_diagnostic(query):
    """Запускает диагностику системы - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    import subprocess
    import socket
    import os
    from datetime import datetime
    
    try:
        message = "🔧 *Диагностика системы*\n\n"
        
        # Проверка подключения к базовым сервисам
        checks = [
            ("Веб-интерфейс", "192.168.20.2", 5000),
            ("SSH демон", "localhost", 22),
            ("База бэкапов", "localhost", None),
        ]
        
        for service, host, port in checks:
            try:
                if port:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    status = "🟢" if result == 0 else "🔴"
                    message += f"{status} {service}: {'доступен' if result == 0 else 'недоступен'}\n"
                else:
                    # Проверка файла базы данных
                    db_path = DATA_DIR / 'backups.db'
                    if db_path.exists():
                        status = "🟢"
                        message += f"{status} {service}: файл существует\n"
                    else:
                        status = "🔴"
                        message += f"{status} {service}: файл не найден\n"
            except Exception as e:
                # Экранируем специальные символы Markdown
                error_msg = str(e)[:50].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
                message += f"🔴 {service}: ошибка проверки ({error_msg})\n"
        
        message += "\n*Проверка процессов:*\n"
        
        # Проверка основных процессов
        processes = [
            "python3",
            "main.py", 
            "improved_mail_monitor.py"
        ]
        
        for process in processes:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', process],
                    capture_output=True, 
                    text=True
                )
                running = len(result.stdout.strip().split('\n')) > 0 and result.stdout.strip() != ''
                status = "🟢" if running else "🔴"
                message += f"{status} {process}: {'запущен' if running else 'не запущен'}\n"
            except Exception as e:
                message += f"🔴 {process}: ошибка проверки\n"
        
        # Проверка расширений
        message += "\n*Проверка расширений:*\n"
        try:
            extension_manager = get_extension_manager()
            enabled_extensions = extension_manager.get_enabled_extensions()
            
            for ext_id in enabled_extensions:
                status = "🟢"
                message += f"{status} {ext_id}: включено\n"
        except Exception as e:
            message += "🔴 Расширения: ошибка проверки\n"
        
        message += f"\n🕒 *Диагностика завершена:* {datetime.now().strftime('%H:%M:%S')}"

        # Экранируем все сообщение для безопасного отображения в Markdown
        safe_message = message.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')

        query.edit_message_text(
            safe_message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Перезапустить", callback_data='debug_diagnose')],
                [InlineKeyboardButton("🔧 Расширенная", callback_data='debug_advanced')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка диагностики: {str(e)[:100]}")

def show_advanced_debug(query):
    """Показывает расширенные настройки отладки - БЕЗ КНОПКИ ОСНОВНЫХ НАСТРОЕК"""
    try:
        from config.debug import debug_config
        debug_info = debug_config.get_debug_info()
        
        message = "🔧 *Расширенные настройки отладки*\n\n"
        
        message += f"*Основные настройки:*\n"
        message += f"• Режим отладки: {'🟢 ВКЛ' if debug_info['debug_mode'] else '🔴 ВЫКЛ'}\n"
        message += f"• Уровень логирования: {debug_info['log_level']}\n"
        message += f"• Макс. размер лога: {debug_info['max_log_size']} MB\n\n"
        
        message += f"*Детальные настройки:*\n"
        message += f"• SSH отладка: {'🟢 ВКЛ' if debug_info['ssh_debug'] else '🔴 ВЫКЛ'}\n"
        message += f"• Ресурсы отладка: {'🟢 ВКЛ' if debug_info['resource_debug'] else '🔴 ВЫКЛ'}\n"
        message += f"• Бэкапы отладка: {'🟢 ВКЛ' if debug_info['backup_debug'] else '🔴 ВЫКЛ'}\n\n"
        
        message += f"*Статус логов:*\n"
        
        # Добавляем информацию о размерах логов
        log_files = {
            'debug.log': DEBUG_LOG_FILE,
            'bot_debug.log': BOT_DEBUG_LOG_FILE,
            'mail_monitor.log': MAIL_MONITOR_LOG_FILE,
        }
        
        for log_name, log_path in log_files.items():
            try:
                log_path = Path(log_path)
                if log_path.exists():
                    size = log_path.stat().st_size / 1024 / 1024
                    message += f"• {log_name}: {size:.2f} MB\n"
                else:
                    message += f"• {log_name}: файл не существует\n"
            except:
                message += f"• {log_name}: ошибка проверки\n"
        
        message += f"\n*Последнее изменение:* {debug_info['last_modified'][:19]}"

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='debug_advanced')],
            [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except ImportError:
        query.edit_message_text(
            "❌ *Расширенная отладка недоступна*\n\n"
            "Модуль debug_config.py не найден.\n"
            "Убедитесь, что файл существует в папке проекта.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка загрузки расширенных настроек: {str(e)[:100]}")

def diagnose_windows_command(update, context):
    """Диагностика подключения к Windows серверам"""
    if not context.args:
        update.message.reply_text("❌ Укажите IP Windows сервера: /diagnose_windows <ip>")
        return
    
    ip = context.args[0]
    
    from extensions.server_checks import get_windows_resources_improved, get_windows_resources_winrm, get_windows_resources_wmi
    
    message = f"🔧 *Диагностика Windows сервера {ip}*\n\n"
    
    # Проверка базовой доступности
    from extensions.server_checks import check_ping, check_port
    ping_ok = check_ping(ip)
    rdp_ok = check_port(ip, 3389)
    winrm_ok = check_port(ip, 5985)
    
    message += f"• Ping: {'🟢 OK' if ping_ok else '🔴 FAIL'}\n"
    message += f"• RDP порт (3389): {'🟢 OK' if rdp_ok else '🔴 FAIL'}\n" 
    message += f"• WinRM порт (5985): {'🟢 OK' if winrm_ok else '🔴 FAIL'}\n\n"
    
    # Тестируем методы получения ресурсов
    message += "*Тестирование методов:*\n"
    
    # WinRM
    winrm_result = get_windows_resources_winrm(ip)
    if winrm_result:
        message += f"• WinRM: 🟢 OK (CPU: {winrm_result.get('cpu', 0)}%, RAM: {winrm_result.get('ram', 0)}%)\n"
    else:
        message += "• WinRM: 🔴 FAIL\n"
    
    # WMI  
    wmi_result = get_windows_resources_wmi(ip)
    if wmi_result:
        message += f"• WMI: 🟢 OK (CPU: {wmi_result.get('cpu', 0)}%, RAM: {wmi_result.get('ram', 0)}%)\n"
    else:
        message += "• WMI: 🔴 FAIL\n"
    
    # Комбинированный метод
    combined_result = get_windows_resources_improved(ip)
    if combined_result:
        message += f"• Combined: 🟢 OK (CPU: {combined_result.get('cpu', 0)}%, RAM: {combined_result.get('ram', 0)}%, Disk: {combined_result.get('disk', 0)}%)\n"
        message += f"• Method: {combined_result.get('access_method', 'unknown')}\n"
    else:
        message += "• Combined: 🔴 FAIL\n"
    
    update.message.reply_text(message, parse_mode='Markdown')

def get_handlers():
    """Возвращает обработчики команд для бота"""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("check", check_command),
        CommandHandler("status", status_command),
        CommandHandler("servers", servers_command),
        CommandHandler("silent", silent_command),
        CommandHandler("report", report_command),
        CommandHandler("stats", stats_command),
        CommandHandler("control", control_command),
        CommandHandler("diagnose_ssh", diagnose_ssh_command),
        CommandHandler("extensions", extensions_command),
        CommandHandler("fix_monitor", fix_monitor_command),
        CommandHandler("backup", backup_command),
        CommandHandler("backup_search", backup_search_command),
        CommandHandler("backup_help", backup_help_command),
        CommandHandler("debug", debug_command),
        CommandHandler("diagnose_windows", diagnose_windows_command),
        CommandHandler("check_single", lambda u,c: show_server_selection_menu(u,c, "check_availability")),
        CommandHandler("check_resources_single", lambda u,c: show_server_selection_menu(u,c, "check_resources")),
        CommandHandler("check_server", check_single_server_command),
        CommandHandler("check_res", check_single_resources_command),
        
        # Обработчик сообщений с ленивой загрузкой
        MessageHandler(Filters.text & ~Filters.command, lazy_message_handler()),
    ]

def get_callback_handlers():
    """Возвращает обработчики callback-запросов с ленивой загрузкой"""
    return [
        # Обработчики настроек (используем ленивую загрузку)
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_times$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^backup_patterns$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^manage_'),

        # Обработчики аутентификации
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_auth$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^ssh_auth_settings$'),
        
        # Обработчики Windows аутентификации
        CallbackQueryHandler(settings_callback_handler, pattern='^windows_auth_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^cred_type_'),

        # Обработчики для таймаутов серверов
        CallbackQueryHandler(settings_callback_handler, pattern='^server_timeouts$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_windows_2025_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_domain_servers_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_admin_servers_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_standard_windows_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_linux_timeout$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_ping_timeout$'),

        # Обработчики для настроек БД
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_main$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_add_category$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_edit_category$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_delete_category$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_view_all$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_edit_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_db_delete_'),

        # Основные обработчики
        CallbackQueryHandler(lambda u, c: lazy_handler('manual_check')(u, c), pattern='^manual_check$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('monitor_status')(u, c), pattern='^monitor_status$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('servers_list')(u, c), pattern='^servers_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('silent_status')(u, c), pattern='^silent_status$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_resources')(u, c), pattern='^check_resources$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('control_panel')(u, c), pattern='^control_panel$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('daily_report')(u, c), pattern='^daily_report$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('diagnose_menu')(u, c), pattern='^diagnose_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close')(u, c), pattern='^close$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('full_report')(u, c), pattern='^full_report$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('force_silent')(u, c), pattern='^force_silent$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('force_loud')(u, c), pattern='^force_loud$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('auto_mode')(u, c), pattern='^auto_mode$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('toggle_silent')(u, c), pattern='^toggle_silent$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('resource_history')(u, c), pattern='^resource_history$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('debug_report')(u, c), pattern='^debug_report$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('monitor_main')(u, c), pattern='^monitor_main$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('main_menu')(u, c), pattern='^main_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('toggle_monitoring')(u, c), pattern='^toggle_monitoring$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close')(u, c), pattern='^close$'),

        # обработчики для настроек
        CallbackQueryHandler(settings_callback_handler, pattern='^add_chat$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^remove_chat$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^view_patterns$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^add_pattern$'),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_view_all$'),

        # Обработчики настроек (должны быть ВЫШЕ обработчиков бэкапов)
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_today')(u, c), pattern='^db_backups_today$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_summary')(u, c), pattern='^db_backups_summary$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_detailed')(u, c), pattern='^db_backups_detailed$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_list')(u, c), pattern='^db_backups_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_detail_')(u, c), pattern='^db_detail_'),

        # Обработчики для постраничного просмотра ресурсов
        CallbackQueryHandler(lambda u, c: lazy_handler('resource_page')(u, c), pattern='^resource_page_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('refresh_resources')(u, c), pattern='^refresh_resources$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close_resources')(u, c), pattern='^close_resources$'),
        
        # Обработчики для раздельной проверки по типам серверов
        CallbackQueryHandler(lambda u, c: lazy_handler('check_linux')(u, c), pattern='^check_linux$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_windows')(u, c), pattern='^check_windows$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_other')(u, c), pattern='^check_other$'),
        
        # Обработчики для раздельной проверки ресурсов
        CallbackQueryHandler(lambda u, c: lazy_handler('check_cpu')(u, c), pattern='^check_cpu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_ram')(u, c), pattern='^check_ram$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_disk')(u, c), pattern='^check_disk$'),

        # Обработчики для бэкапов
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_hosts')(u, c), pattern='^backup_hosts$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_refresh')(u, c), pattern='^backup_refresh$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_host_')(u, c), pattern='^backup_host_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_today')(u, c), pattern='^db_backups_today$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_summary')(u, c), pattern='^db_backups_summary$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_detailed')(u, c), pattern='^db_backups_detailed$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_backups_list')(u, c), pattern='^db_backups_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_main')(u, c), pattern='^backup_main$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_proxmox')(u, c), pattern='^backup_proxmox$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_proxmox_menu')(u, c), pattern='^backup_proxmox_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_proxmox_patterns')(u, c), pattern='^backup_proxmox_patterns$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_databases')(u, c), pattern='^backup_databases$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_mail')(u, c), pattern='^backup_mail$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_host_')(u, c), pattern='^backup_host_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('db_detail_')(u, c), pattern='^db_detail_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_stale_hosts')(u, c), pattern='^backup_stale_hosts$'),

        # Обработчики расширений
        CallbackQueryHandler(lambda u, c: lazy_handler('extensions_menu')(u, c), pattern='^extensions_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('extensions_refresh')(u, c), pattern='^extensions_refresh$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('ext_enable_all')(u, c), pattern='^ext_enable_all$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('ext_disable_all')(u, c), pattern='^ext_disable_all$'),
        CallbackQueryHandler(lambda u, c: extensions_callback_handler(u, c), pattern='^ext_toggle_'),
        
        # Обработчики для серверов
        CallbackQueryHandler(settings_callback_handler, pattern='^server_type_'),
        
        # Обработчики для БД
        CallbackQueryHandler(settings_callback_handler, pattern='^edit_db_category_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^delete_db_category_'),

        # НОВЫЕ ОБРАБОТЧИКИ ОТЛАДКИ
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_enable$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_disable$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_status$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_clear_logs$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_diagnose$'),
        CallbackQueryHandler(debug_callback_handler, pattern='^debug_advanced$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('debug_menu')(u, c), pattern='^debug_menu$'),

        CallbackQueryHandler(lambda u,c: show_server_selection_menu(u,c, "check_availability"), pattern='^show_availability_menu$'),
        CallbackQueryHandler(lambda u,c: show_server_selection_menu(u,c, "check_resources"), pattern='^show_resources_menu$'),
        CallbackQueryHandler(lambda u,c: handle_single_check(u,c, u.callback_query.data.replace('check_availability_', '')), pattern='^check_availability_'),
        CallbackQueryHandler(lambda u,c: handle_single_resources(u,c, u.callback_query.data.replace('check_resources_', '')), pattern='^check_resources_'),
        CallbackQueryHandler(lambda u,c: refresh_server_menu(u,c), pattern='^refresh_'),
    ]

def lazy_handler(pattern):
    """Ленивая загрузка обработчиков"""
    def wrapper(update, context):
        # Динамически импортируем обработчик при вызове
        if pattern == 'main_menu':
            return start_command(update, context)
        elif pattern == 'manual_check':
            from core.monitor_core import manual_check_handler as handler
        elif pattern == 'monitor_status':
            from core.monitor_core import monitor_status as handler
        elif pattern == 'silent_status':
            from core.monitor_core import silent_status_handler as handler
        elif pattern == 'pause_monitoring':
            from core.monitor_core import pause_monitoring_handler as handler
        elif pattern == 'resume_monitoring':
            from core.monitor_core import resume_monitoring_handler as handler
        elif pattern == 'check_resources':
            from core.monitor_core import check_resources_handler as handler
        elif pattern == 'control_panel':
            from core.monitor_core import control_panel_handler as handler
        elif pattern == 'toggle_monitoring':
            from core.monitor_core import toggle_monitoring_handler as handler
        elif pattern == 'daily_report':
            from core.monitor_core import send_morning_report_handler as handler
        elif pattern == 'diagnose_menu':
            from core.monitor_core import diagnose_menu_handler as handler
        elif pattern == 'close':
            from core.monitor_core import close_menu as handler
        elif pattern == 'force_silent':
            from core.monitor_core import force_silent_handler as handler
        elif pattern == 'force_loud':
            from core.monitor_core import force_loud_handler as handler
        elif pattern == 'auto_mode':
            from core.monitor_core import auto_mode_handler as handler
        elif pattern == 'toggle_silent':
            from core.monitor_core import toggle_silent_mode_handler as handler
        elif pattern == 'servers_list':
            from extensions.server_checks import servers_list_handler as handler
        elif pattern == 'full_report':
            from core.monitor_core import send_morning_report_handler as handler
        elif pattern == 'resource_page':
            from core.monitor_core import resource_page_handler as handler
        elif pattern == 'refresh_resources':
            from core.monitor_core import refresh_resources_handler as handler
        elif pattern == 'close_resources':
            from core.monitor_core import close_resources_handler as handler
        # Новые обработчики для раздельной проверки
        elif pattern == 'check_linux':
            from core.monitor_core import check_linux_resources_handler as handler
        elif pattern == 'check_windows':
            from core.monitor_core import check_windows_resources_handler as handler
        elif pattern == 'check_other':
            from core.monitor_core import check_other_resources_handler as handler
        # Обработчики для раздельной проверки ресурсов
        elif pattern == 'check_cpu':
            from core.monitor_core import check_cpu_resources_handler as handler
        elif pattern == 'check_ram':
            from core.monitor_core import check_ram_resources_handler as handler
        elif pattern == 'check_disk':
            from core.monitor_core import check_disk_resources_handler as handler
        elif pattern == 'resource_history':
            from core.monitor_core import resource_history_command as handler
        elif pattern == 'debug_report':
            from core.monitor_core import debug_morning_report as handler
        elif pattern == 'backup_today':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_24h':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_24h':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_48h':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_failed':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_hosts':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_refresh':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern.startswith('backup_host_'):
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_main':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_proxmox':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_proxmox_menu':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_proxmox_patterns':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_databases':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_mail':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_summary':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_detailed':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'db_backups_list':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern.startswith('db_detail_'):
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_stale_hosts':
            from extensions.backup_monitor.bot_handler import show_stale_hosts as handler
        elif pattern == 'db_stale_list':
            from extensions.backup_monitor.bot_handler import show_stale_databases as handler
        elif pattern == 'extensions_menu':
            handler = show_extensions_menu
        elif pattern == 'extensions_refresh':
            handler = show_extensions_menu
        elif pattern == 'ext_enable_all':
            handler = enable_all_extensions
        elif pattern == 'ext_disable_all':
            handler = disable_all_extensions
        elif pattern == 'debug_menu':
            handler = show_debug_menu
        else:
            def default_handler(update, context):
                query = update.callback_query
                query.answer()
                query.edit_message_text("❌ Обработчик не найден")
            return default_handler(update, context)

        return handler(update, context)
    return wrapper

def lazy_message_handler():
    """Ленивая загрузка обработчика сообщений"""
    def handler(update, context):
        try:
            from bot.handlers.settings_handlers import handle_setting_value
            return handle_setting_value(update, context)
        except ImportError as e:
            print(f"❌ Ошибка импорта handle_setting_value: {e}")
            # Если не удалось импортировать, просто игнорируем сообщение
            return
    return handler

def check_single_server_command(update, context):
    """Команда /check_server - проверка доступности одного сервера"""
    if not context.args:
        # Показываем меню выбора
        return show_server_selection_menu(update, context, "check_availability")
    else:
        # Проверяем указанный сервер
        server_id = context.args[0]
        return handle_single_check(update, context, server_id)

def check_single_resources_command(update, context):
    """Команда /check_res - проверка ресурсов одного сервера"""
    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('resource_monitor'):
        if update.message:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        elif update.callback_query:
            update.callback_query.answer("📊 Мониторинг ресурсов отключён", show_alert=True)
        return

    if not context.args:
        # Показываем меню выбора
        return show_server_selection_menu(update, context, "check_resources")
    else:
        # Проверяем указанный сервер
        server_id = context.args[0]
        return handle_single_resources(update, context, server_id)

def show_server_selection_menu(update, context, action="check_availability"):
    """Показывает меню выбора сервера"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    extension_manager = get_extension_manager()
    
    # Определяем заголовок
    titles = {
        "check_availability": "📡 *Выберите сервер для проверки доступности:*",
        "check_resources": "📊 *Выберите сервер для проверки ресурсов:*"
    }
    
    title = titles.get(action, "🔍 *Выберите сервер:*")

    if action == "check_resources" and not extension_manager.is_extension_enabled('resource_monitor'):
        message = "📊 Мониторинг ресурсов отключён"
        if query:
            query.answer()
            query.edit_message_text(text=message)
        elif update.message:
            update.message.reply_text(text=message)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return

    # Получаем клавиатуру
    keyboard = targeted_checks.create_server_selection_menu(action)
    
    # Если вызвано из callback (кнопка)
    if query:
        query.answer()
        query.edit_message_text(text=title, parse_mode='Markdown', reply_markup=keyboard)
    # Если вызвано командой
    elif update.message:
        update.message.reply_text(text=title, parse_mode='Markdown', reply_markup=keyboard)
    # Если вызвано из другого обработчика
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=title,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

def handle_single_check(update, context, server_id):
    """Обработка проверки одного сервера"""
    query = update.callback_query
    if query:
        query.answer("🔍 Проверяем сервер...")
    
    # Выполняем проверку
    success, server, message = targeted_checks.check_single_server_availability(server_id)
    
    # Создаем клавиатуру для действий
    keyboard = []
    if server:
        row_actions = [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_availability_{server['ip']}")]
        if extension_manager.is_extension_enabled('resource_monitor'):
            row_actions.insert(0, InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f"check_resources_{server['ip']}"))
        keyboard.append(row_actions)
    
    keyboard.append([
        InlineKeyboardButton("🔍 Выбрать другой", callback_data="show_availability_menu")
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
        InlineKeyboardButton("✖️ Закрыть", callback_data="close")
    ])
    
    if query:
        query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

def handle_single_resources(update, context, server_id):
    """Обработка проверки ресурсов одного сервера"""
    query = update.callback_query
    if query:
        query.answer("📊 Проверяем ресурсы...")

    extension_manager = get_extension_manager()
    if not extension_manager.is_extension_enabled('resource_monitor'):
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    # Выполняем проверку
    success, server, message = targeted_checks.check_single_server_resources(server_id)
    
    # Создаем клавиатуру для действий
    keyboard = []
    if server:
        keyboard.append([
            InlineKeyboardButton("📡 Проверить доступность", callback_data=f"check_availability_{server['ip']}"),
            InlineKeyboardButton("🔄 Обновить ресурсы", callback_data=f"check_resources_{server['ip']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔍 Выбрать другой", callback_data="show_resources_menu")
    ])
    keyboard.append([
        InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
        InlineKeyboardButton("✖️ Закрыть", callback_data="close")
    ])
    
    if query:
        query.edit_message_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text=message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

def add_quick_check_buttons(keyboard, server_ip=None):
    """Добавляет кнопки быстрой проверки в клавиатуру"""
    if server_ip:
        extension_manager = get_extension_manager()
        row_actions = [InlineKeyboardButton("🔍 Проверить доступность", callback_data=f'check_availability_{server_ip}')]
        if extension_manager.is_extension_enabled('resource_monitor'):
            row_actions.append(InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f'check_resources_{server_ip}'))
        keyboard.append(row_actions)
    
    keyboard.append([
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])
    
    return keyboard

def create_quick_actions_menu(server_ip):
    """Создает меню быстрых действий для сервера"""
    extension_manager = get_extension_manager()
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить доступность", callback_data=f'check_availability_{server_ip}')],
    ]

    if extension_manager.is_extension_enabled('resource_monitor'):
        keyboard.append([InlineKeyboardButton("📊 Проверить ресурсы", callback_data=f'check_resources_{server_ip}')])

    keyboard.extend([
        [InlineKeyboardButton("📋 Информация о сервере", callback_data=f'server_info_{server_ip}')],
        [InlineKeyboardButton("🔄 Проверить снова", callback_data=f'check_availability_{server_ip}')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def refresh_server_menu(update, context):
    """Обновление меню выбора сервера"""
    query = update.callback_query
    if not query:
        return
    
    query.answer("🔄 Обновляем список...")
    
    # Определяем тип действия из callback_data
    data = query.data
    if "availability" in data:
        action = "check_availability"
    else:
        action = "check_resources"
    
    # Обновляем кэш
    targeted_checks.server_cache = None
    
    # Показываем обновленное меню
    show_server_selection_menu(update, context, action)
