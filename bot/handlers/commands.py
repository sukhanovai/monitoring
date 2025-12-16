"""
Server Monitoring System v4.11.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot command handlers
Система мониторинга серверов
Версия: 4.11.1
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики команд бота
"""

from telegram.ext import CommandHandler
from lib.logging import debug_log
from bot.utils import check_access, get_access_denied_response  # Импортируем из общего модуля
from bot.handlers.base import lazy_handler

# Удаляем импорты из menu.handlers и делаем их ленивыми

def setup_command_handlers():
    """Настройка обработчиков команд"""
    return [
        CommandHandler("start", lazy_start_command),
        CommandHandler("help", lazy_help_command),
        CommandHandler("check", lambda u,c: lazy_handler('manual_check')(u,c)),
        CommandHandler("status", lambda u,c: lazy_handler('monitor_status')(u,c)),
        CommandHandler("servers", lambda u,c: lazy_handler('servers_list')(u,c)),
        CommandHandler("silent", lambda u,c: lazy_handler('silent_status')(u,c)),
        CommandHandler("report", lambda u,c: lazy_handler('daily_report')(u,c)),
        CommandHandler("stats", lambda u,c: lazy_stats_handler(u,c)),
        CommandHandler("control", lambda u,c: lazy_handler('control_panel')(u,c)),
        CommandHandler("diagnose_ssh", lambda u,c: lazy_diagnose_handler(u,c)),
        CommandHandler("extensions", lambda u,c: lazy_extensions_handler(u,c)),
        CommandHandler("fix_monitor", lambda u,c: lazy_fix_monitor_handler(u,c)),
        CommandHandler("backup", lambda u,c: lazy_backup_handler(u,c)),
        CommandHandler("backup_search", lambda u,c: lazy_backup_search_handler(u,c)),
        CommandHandler("backup_help", lambda u,c: lazy_backup_help_handler(u,c)),
        CommandHandler("debug", lazy_debug_command),
        CommandHandler("diagnose_windows", lambda u,c: lazy_diagnose_windows_handler(u,c)),
        CommandHandler("check_single", lambda u,c: handle_server_selection_menu(u,c, "check_single")),
        CommandHandler("check_resources_single", lambda u,c: handle_server_selection_menu(u,c, "check_resources")),
        CommandHandler("check_server", lambda u,c: check_single_server_command(u,c)),
        CommandHandler("check_res", lambda u,c: check_single_resources_command(u,c)),
    ]

def lazy_start_command(update, context):
    """Ленивая загрузка команды /start"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from bot.menu.handlers import start_command
    return start_command(update, context)

def lazy_help_command(update, context):
    """Ленивая загрузка команды /help"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from bot.menu.handlers import help_command
    return help_command(update, context)

def lazy_debug_command(update, context):
    """Ленивая загрузка команды /debug"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from bot.menu.handlers import debug_command
    return debug_command(update, context)

def lazy_check_handler(handler_name):
    """Ленивая загрузка обработчиков проверок"""
    from bot.handlers.base import lazy_handler
    return lazy_handler(handler_name)

def lazy_stats_handler(update, context):
    """Обработчик команды /stats"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from extensions.utils import stats_command
    return stats_command(update, context)

def lazy_diagnose_handler(update, context):
    """Обработчик команды /diagnose_ssh"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from extensions.utils import diagnose_ssh_command
    return diagnose_ssh_command(update, context)

def lazy_extensions_handler(update, context):
    """Обработчик команды /extensions"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from bot.menu.handlers import show_extensions_menu
    return show_extensions_menu(update, context)

def lazy_fix_monitor_handler(update, context):
    """Обработчик команды /fix_monitor"""
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этой команды")
        return

    try:
        from core.monitor import server_status
        from datetime import datetime
        from config.settings import TELEGRAM_TOKEN
        from telegram import Bot

        monitor_server_ip = "192.168.20.2"

        if monitor_server_ip in server_status:
            server_status[monitor_server_ip]["last_up"] = datetime.now()
            server_status[monitor_server_ip]["alert_sent"] = False

            update.message.reply_text("✅ Статус сервера мониторинга исправлен")

            # Отправляем уведомление
            bot = Bot(token=TELEGRAM_TOKEN)
            from config.settings import CHAT_IDS
            for chat_id in CHAT_IDS:
                bot.send_message(chat_id=chat_id, text="🔧 Статус сервера мониторинга принудительно исправлен")
        else:
            update.message.reply_text("❌ Сервер мониторинга не найден в списке")

    except Exception as e:
        update.message.reply_text(f"❌ Ошибка при исправлении статуса: {e}")
        debug_log(f"Ошибка в fix_monitor_command: {e}")

def lazy_backup_handler(update, context):
    """Обработчик команды /backup"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from extensions.extension_manager import extension_manager
    if not extension_manager.is_extension_enabled('backup_monitor'):
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')]
            ])
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_command
    return backup_command(update, context)

def lazy_backup_search_handler(update, context):
    """Обработчик команды /backup_search"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from extensions.extension_manager import extension_manager
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями."
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_search_command
    return backup_search_command(update, context)

def lazy_backup_help_handler(update, context):
    """Обработчик команды /backup_help"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    from extensions.extension_manager import extension_manager
    if not extension_manager.is_extension_enabled('backup_monitor'):
        update.message.reply_text(
            "❌ Функционал мониторинга бэкапов отключен. "
            "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями."
        )
        return
    
    from extensions.backup_monitor.bot_handler import backup_help_command
    return backup_help_command(update, context)

def lazy_diagnose_windows_handler(update, context):
    """Обработчик команды /diagnose_windows"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    if not context.args:
        update.message.reply_text("❌ Укажите IP Windows сервера: /diagnose_windows <ip>")
        return
    
    ip = context.args[0]
    from extensions.server_checks import (
        get_windows_resources_improved, 
        get_windows_resources_winrm, 
        get_windows_resources_wmi,
        check_ping, 
        check_port
    )
    
    message = f"🔧 *Диагностика Windows сервера {ip}*\n\n"
    
    # Проверка базовой доступности
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

def check_single_server_command(update, context):
    """Команда /check_server - проверка доступности одного сервера"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    if not context.args:
        # Показываем меню выбора
        return show_server_selection_menu(update, context, "check_availability")
    else:
        # Проверяем указанный сервер
        server_id = context.args[0]
        from modules.targeted_checks import handle_single_check
        return handle_single_check(update, context, server_id)

def check_single_resources_command(update, context):
    """Команда /check_res - проверка ресурсов одного сервера"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    if not context.args:
        # Показываем меню выбора
        return show_server_selection_menu(update, context, "check_resources")
    else:
        # Проверяем указанный сервер
        server_id = context.args[0]
        from modules.targeted_checks import handle_single_resources
        return handle_single_resources(update, context, server_id)