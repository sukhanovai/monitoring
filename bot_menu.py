"""
Server Monitoring System v1.3.0
Copyright (c) 2024 Aleksandr Sukhanov
License: MIT
"""

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from config import CHAT_IDS, TELEGRAM_TOKEN
from telegram import Bot
from extensions.backup_monitor.bot_handler import setup_backup_commands
from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS

import requests
import json

def setup_menu(bot):
    """Настройка меню бота"""
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
            BotCommand("backup", "📊 Статус бэкапов Proxmox"),
            BotCommand("backup_search", "🔍 Поиск бэкапов по серверу"),
            BotCommand("backup_help", "❓ Помощь по бэкапам"),
            BotCommand("help", "Помощь")
        ]
        bot.set_my_commands(commands)
        print("✅ Меню настроено успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка настройки меню: {e}")
        return False

def check_access(chat_id):
    """Проверка доступа к боту"""
    return str(chat_id) in CHAT_IDS

def start_command(update, context):
    """Обработчик команды /start"""
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        return

    keyboard = [
        [InlineKeyboardButton("🔄 Проверить серверы", callback_data='manual_check')],
        [InlineKeyboardButton("ℹ️ Статус мониторинга", callback_data='monitor_status')],
        [InlineKeyboardButton("📋 Список серверов", callback_data='servers_list')],
        [InlineKeyboardButton("📊 Проверить ресурсы", callback_data='check_resources')],
        [InlineKeyboardButton("📊 Бэкапы Proxmox", callback_data='backup_today')],
        [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')],
        [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
        [InlineKeyboardButton("🔧 Диагностика", callback_data='diagnose_menu')],
        [InlineKeyboardButton("🔇 Тихий режим", callback_data='silent_status')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🤖 *Серверный мониторинг - help*\n\n"
        "✅ Система работает\n\n"
        "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
        "_*доступен только в локальной сети_"
    )
    update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

def help_command(update, context):
    """Обработчик команды /help"""
    if not check_access(update.effective_chat.id):
        return

    help_text = (
        "🤖 *Помощь по мониторингу*\n\n"
        "*Основные команды:*\n"
        "• `/start` - Главное меню\n"
        "• `/status` - Статус мониторинга\n"
        "• `/check` - Быстрая проверка серверов\n"
        "• `/servers` - Список всех серверов\n"
        "• `/control` - Управление мониторингом\n\n"
        "• `/extensions` - Управление расширениями\n\n"
        "*Диагностика:*\n"
        "• `/diagnose_ssh <ip>` - Проверка SSH подключения\n"
        "• `/silent` - Статус тихого режима\n\n"
        "*Отчеты:*\n"
        "• `/report` - Принудительная отправка утреннего отчета\n"
        "• `/stats` - Статистика работы\n\n"
        "*Расширения:*\n"
        "*Веб-интерфейс:*\n"
        "🌐 http://192.168.20.2:5000\n"
        "_*доступен только в локальной сети_\n\n"
        "*Используйте кнопки меню для удобного управления*"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')

# Заглушки для команд (импорты внутри функций чтобы избежать циклических импортов)
def check_command(update, context):
    from monitor_core import manual_check_handler
    return manual_check_handler(update, context)

def status_command(update, context):
    from monitor_core import monitor_status
    return monitor_status(update, context)

def silent_command(update, context):
    from monitor_core import silent_command as silent_cmd
    return silent_cmd(update, context)

def control_command(update, context):
    from monitor_core import control_command as control_cmd
    return control_cmd(update, context)

def servers_command(update, context):
    from extensions.server_list import servers_command as servers_cmd
    return servers_cmd(update, context)

def report_command(update, context):
    """Команда для принудительной отправки утреннего отчета"""
    from monitor_core import send_morning_report_handler
    return send_morning_report_handler(update, context)

def stats_command(update, context):
    from extensions.reports import stats_command as stats_cmd
    return stats_cmd(update, context)

def diagnose_ssh_command(update, context):
    from extensions.single_check import diagnose_ssh_command as diagnose_cmd
    return diagnose_cmd(update, context)

def backup_command(update, context):
    """Обработчик команды /backup"""
    from extensions.backup_monitor.bot_handler import backup_command as backup_cmd
    return backup_cmd(update, context)

def backup_search_command(update, context):
    """Обработчик команды /backup_search"""
    from extensions.backup_monitor.bot_handler import backup_search_command as backup_search_cmd
    return backup_search_cmd(update, context)

def backup_help_command(update, context):
    """Обработчик команды /backup_help"""
    from extensions.backup_monitor.bot_handler import backup_help_command as backup_help_cmd
    return backup_help_cmd(update, context)

def fix_monitor_command(update, context):
    """Команда для исправления статуса сервера мониторинга"""
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этой команды")
        return

    try:
        # Динамический импорт чтобы избежать циклических зависимостей
        from monitor_core import server_status
        from datetime import datetime

        monitor_server_ip = "192.168.20.2"

        if monitor_server_ip in server_status:
            server_status[monitor_server_ip]["last_up"] = datetime.now()
            server_status[monitor_server_ip]["alert_sent"] = False

            update.message.reply_text("✅ Статус сервера мониторинга исправлен")

            # Отправляем уведомление
            bot = Bot(token=TELEGRAM_TOKEN)
            for chat_id in CHAT_IDS:
                bot.send_message(chat_id=chat_id, text="🔧 Статус сервера мониторинга принудительно исправлен")
        else:
            update.message.reply_text("❌ Сервер мониторинга не найден в списке")

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при исправлении статуса: {e}")
        import traceback
        print(f"Ошибка в fix_monitor_command: {traceback.format_exc()}")

def extensions_command(update, context):
    """Обработчик команды /extensions"""
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
        return
    
    show_extensions_menu(update, context)

def show_extensions_menu(update, context):
    """Показывает меню управления расширениями"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
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
        [InlineKeyboardButton("🔄 Обновить статус", callback_data='extensions_refresh')],
        [InlineKeyboardButton("📊 Включить все", callback_data='ext_enable_all')],
        [InlineKeyboardButton("📋 Отключить все", callback_data='ext_disable_all')],
        [InlineKeyboardButton("↩️ Назад в главное меню", callback_data='monitor_status')]
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

def toggle_extension(update, context, extension_id):
    """Переключает расширение"""
    query = update.callback_query
    
    success, message = extension_manager.toggle_extension(extension_id)
    
    if success:
        query.answer(message)
        show_extensions_menu(update, context)
    else:
        query.answer(message, show_alert=True)

def enable_all_extensions(update, context):
    """Включает все расширения"""
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
    query = update.callback_query
    
    disabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled_count += 1
    
    query.answer(f"✅ Отключено {disabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
    show_extensions_menu(update, context)

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
    ]

def lazy_handler(pattern):
    """Ленивая загрузка обработчиков"""
    def wrapper(update, context):
        # Динамически импортируем обработчик при вызове
        if pattern == 'manual_check':
            from monitor_core import manual_check_handler as handler
        elif pattern == 'monitor_status':
            from monitor_core import monitor_status as handler
        elif pattern == 'silent_status':
            from monitor_core import silent_status_handler as handler
        elif pattern == 'pause_monitoring':
            from monitor_core import pause_monitoring_handler as handler
        elif pattern == 'resume_monitoring':
            from monitor_core import resume_monitoring_handler as handler
        elif pattern == 'check_resources':
            from monitor_core import check_resources_handler as handler
        elif pattern == 'control_panel':
            from monitor_core import control_panel_handler as handler
        elif pattern == 'daily_report':
            from monitor_core import send_morning_report_handler as handler
        elif pattern == 'diagnose_menu':
            from monitor_core import diagnose_menu_handler as handler
        elif pattern == 'close':
            from monitor_core import close_menu as handler
        elif pattern == 'force_silent':
            from monitor_core import force_silent_handler as handler
        elif pattern == 'force_loud':
            from monitor_core import force_loud_handler as handler
        elif pattern == 'auto_mode':
            from monitor_core import auto_mode_handler as handler
        elif pattern == 'toggle_silent':
            from monitor_core import toggle_silent_mode_handler as handler
        elif pattern == 'servers_list':
            from extensions.server_list import servers_list_handler as handler
        elif pattern == 'full_report':
            from monitor_core import send_morning_report_handler as handler
        elif pattern == 'resource_page':
            from monitor_core import resource_page_handler as handler
        elif pattern == 'refresh_resources':
            from monitor_core import refresh_resources_handler as handler
        elif pattern == 'close_resources':
            from monitor_core import close_resources_handler as handler
        # Новые обработчики для раздельной проверки
        elif pattern == 'check_linux':
            from monitor_core import check_linux_resources_handler as handler
        elif pattern == 'check_windows':
            from monitor_core import check_windows_resources_handler as handler
        elif pattern == 'check_other':
            from monitor_core import check_other_resources_handler as handler
        elif pattern == 'check_all_resources':
            from monitor_core import check_all_resources_handler as handler
        # НОВЫЕ ОБРАБОТЧИКИ ДЛЯ РАЗДЕЛЬНОЙ ПРОВЕРКИ РЕСУРСОВ
        elif pattern == 'check_cpu':
            from monitor_core import check_cpu_resources_handler as handler
        elif pattern == 'check_ram':
            from monitor_core import check_ram_resources_handler as handler
        elif pattern == 'check_disk':
            from monitor_core import check_disk_resources_handler as handler
        elif pattern == 'resource_history':
            from monitor_core import resource_history_command as handler
        elif pattern == 'debug_report':
            from monitor_core import debug_morning_report as handler
        elif pattern == 'backup_today':
            from extensions.backup_monitor.bot_handler import backup_callback as handler
            return handler(update, context)
        elif pattern == 'backup_24h':
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
        elif pattern == 'extensions_menu':
            from bot_menu import show_extensions_menu as handler
        elif pattern == 'extensions_refresh':
            from bot_menu import show_extensions_menu as handler
        elif pattern == 'ext_enable_all':
            from bot_menu import enable_all_extensions as handler
        elif pattern == 'ext_disable_all':
            from bot_menu import disable_all_extensions as handler
        else:
            def default_handler(update, context):
                query = update.callback_query
                query.answer()
                query.edit_message_text("❌ Обработчик не найден")
            return default_handler(update, context)

        return handler(update, context)
    return wrapper

def get_callback_handlers():
    """Возвращает обработчики callback-запросов с ленивой загрузкой"""
    return [
        CallbackQueryHandler(lambda u, c: lazy_handler('manual_check')(u, c), pattern='^manual_check$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('monitor_status')(u, c), pattern='^monitor_status$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('servers_list')(u, c), pattern='^servers_list$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('silent_status')(u, c), pattern='^silent_status$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('pause_monitoring')(u, c), pattern='^pause_monitoring$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('resume_monitoring')(u, c), pattern='^resume_monitoring$'),
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
        
        # Обработчики для постраничного просмотра ресурсов
        CallbackQueryHandler(lambda u, c: lazy_handler('resource_page')(u, c), pattern='^resource_page_'),
        CallbackQueryHandler(lambda u, c: lazy_handler('refresh_resources')(u, c), pattern='^refresh_resources$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('close_resources')(u, c), pattern='^close_resources$'),
        
        # Обработчики для раздельной проверки по типам серверов
        CallbackQueryHandler(lambda u, c: lazy_handler('check_linux')(u, c), pattern='^check_linux$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_windows')(u, c), pattern='^check_windows$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_other')(u, c), pattern='^check_other$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_all_resources')(u, c), pattern='^check_all_resources$'),
        
        # НОВЫЕ ОБРАБОТЧИКИ ДЛЯ РАЗДЕЛЬНОЙ ПРОВЕРКИ РЕСУРСОВ
        CallbackQueryHandler(lambda u, c: lazy_handler('check_cpu')(u, c), pattern='^check_cpu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_ram')(u, c), pattern='^check_ram$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('check_disk')(u, c), pattern='^check_disk$'),

        # ОБРАБОТЧИКИ ДЛЯ БЭКАПОВ
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_today')(u, c), pattern='^backup_today$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_24h')(u, c), pattern='^backup_24h$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_failed')(u, c), pattern='^backup_failed$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_hosts')(u, c), pattern='^backup_hosts$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_refresh')(u, c), pattern='^backup_refresh$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('backup_host_')(u, c), pattern='^backup_host_'),
        
        # Обработчики расширений
        CallbackQueryHandler(lambda u, c: lazy_handler('extensions_menu')(u, c), pattern='^extensions_menu$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('extensions_refresh')(u, c), pattern='^extensions_refresh$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('ext_enable_all')(u, c), pattern='^ext_enable_all$'),
        CallbackQueryHandler(lambda u, c: lazy_handler('ext_disable_all')(u, c), pattern='^ext_disable_all$'),
        CallbackQueryHandler(lambda u, c: extensions_callback_handler(u, c), pattern='^ext_toggle_'),
    ]
