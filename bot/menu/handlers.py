"""
/bot/menu/handlers.py
Server Monitoring System v4.13.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu handlers
Система мониторинга серверов
Версия: 4.13.1
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики меню
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.base import base_handler
from lib.logging import debug_log

# Реестр обработчиков меню
menu_handlers = {}

def register_menu_handler(pattern):
    """Декоратор для регистрации обработчиков меню"""
    def decorator(func):
        menu_handlers[pattern] = func
        return func
    return decorator

@register_menu_handler('manual_check')
@base_handler.access_check_decorator
def handle_manual_check(update, context):
    """Обработчик ручной проверки серверов"""
    from core.monitor import manual_check_handler
    return manual_check_handler(update, context)

@register_menu_handler('check_resources')
@base_handler.access_check_decorator
def handle_check_resources(update, context):
    """Обработчик проверки ресурсов"""
    from core.monitor import check_resources_handler
    return check_resources_handler(update, context)

@register_menu_handler('control_panel')
@base_handler.access_check_decorator
def handle_control_panel(update, context):
    """Обработчик панели управления"""
    from core.monitor import control_panel_handler
    return control_panel_handler(update, context)

@register_menu_handler('monitor_status')
@base_handler.access_check_decorator
def handle_monitor_status(update, context):
    """Обработчик статуса мониторинга"""
    from core.monitor import monitor_status
    return monitor_status(update, context)

@register_menu_handler('servers_list')
@base_handler.access_check_decorator
def handle_servers_list(update, context):
    """Обработчик списка серверов"""
    from extensions.server_checks import servers_list_handler
    return servers_list_handler(update, context)

@register_menu_handler('silent_status')
@base_handler.access_check_decorator
def handle_silent_status(update, context):
    """Обработчик статуса тихого режима"""
    from core.monitor import silent_status_handler
    return silent_status_handler(update, context)

@register_menu_handler('full_report')
@base_handler.access_check_decorator
def handle_full_report(update, context):
    """Обработчик полного отчета"""
    from modules.morning_report import send_morning_report_handler
    return send_morning_report_handler(update, context)

@register_menu_handler('toggle_monitoring')
@base_handler.access_check_decorator
def handle_toggle_monitoring(update, context):
    """Обработчик переключения мониторинга"""
    from core.monitor import toggle_monitoring_handler
    return toggle_monitoring_handler(update, context)

@register_menu_handler('force_silent')
@base_handler.access_check_decorator
def handle_force_silent(update, context):
    """Обработчик принудительного тихого режима"""
    from core.monitor import force_silent_handler
    return force_silent_handler(update, context)

@register_menu_handler('force_loud')
@base_handler.access_check_decorator
def handle_force_loud(update, context):
    """Обработчик принудительного громкого режима"""
    from core.monitor import force_loud_handler
    return force_loud_handler(update, context)

@register_menu_handler('auto_mode')
@base_handler.access_check_decorator
def handle_auto_mode(update, context):
    """Обработчик автоматического режима"""
    from core.monitor import auto_mode_handler
    return auto_mode_handler(update, context)

@register_menu_handler('extensions_menu')
@base_handler.access_check_decorator
def handle_extensions_menu(update, context):
    """Обработчик меню расширений"""
    from extensions.extension_manager import show_extensions_menu
    return show_extensions_menu(update, context)

# Обработчики для раздельной проверки ресурсов
@register_menu_handler('check_cpu')
@base_handler.access_check_decorator
def handle_check_cpu(update, context):
    """Обработчик проверки CPU"""
    from core.monitor import check_cpu_resources_handler
    return check_cpu_resources_handler(update, context)

@register_menu_handler('check_ram')
@base_handler.access_check_decorator
def handle_check_ram(update, context):
    """Обработчик проверки RAM"""
    from core.monitor import check_ram_resources_handler
    return check_ram_resources_handler(update, context)

@register_menu_handler('check_disk')
@base_handler.access_check_decorator
def handle_check_disk(update, context):
    """Обработчик проверки Disk"""
    from core.monitor import check_disk_resources_handler
    return check_disk_resources_handler(update, context)

@register_menu_handler('check_linux')
@base_handler.access_check_decorator
def handle_check_linux(update, context):
    """Обработчик проверки Linux"""
    from core.monitor import check_linux_resources_handler
    return check_linux_resources_handler(update, context)

@register_menu_handler('check_windows')
@base_handler.access_check_decorator
def handle_check_windows(update, context):
    """Обработчик проверки Windows"""
    from core.monitor import check_windows_resources_handler
    return check_windows_resources_handler(update, context)

@register_menu_handler('check_other')
@base_handler.access_check_decorator
def handle_check_other(update, context):
    """Обработчик проверки других серверов"""
    from core.monitor import check_other_resources_handler
    return check_other_resources_handler(update, context)

# Обработчики для точечных проверок
@register_menu_handler('show_availability_menu')
@base_handler.access_check_decorator
def handle_show_availability_menu(update, context):
    """Показывает меню выбора сервера для проверки доступности"""
    from modules.targeted_checks import show_server_selection_menu
    return show_server_selection_menu(update, context, "check_availability")

@register_menu_handler('show_resources_menu')
@base_handler.access_check_decorator
def handle_show_resources_menu(update, context):
    """Показывает меню выбора сервера для проверки ресурсов"""
    from modules.targeted_checks import show_server_selection_menu
    return show_server_selection_menu(update, context, "check_resources")

# Обработчики отладки
@register_menu_handler('debug_menu')
@base_handler.access_check_decorator
def show_debug_menu(update, context):
    """Показывает меню управления отладкой"""
    from config.settings import DEBUG_MODE
    
    debug_status = "🟢 ВКЛЮЧЕНА" if DEBUG_MODE else "🔴 ВЫКЛЮЧЕНА"
    
    message = "🐛 *Управление отладкой*\n\n"
    message += f"*Текущий статус:* {debug_status}\n\n"
    
    # Кнопка-переключатель
    toggle_text = "🔴 Выключить отладку" if DEBUG_MODE else "🟢 Включить отладку"
    toggle_data = 'debug_disable' if DEBUG_MODE else 'debug_enable'

    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton("📊 Статус системы", callback_data='debug_status')],
        [InlineKeyboardButton("🗑️ Очистить логи", callback_data='debug_clear_logs')],
        [InlineKeyboardButton("📋 Диагностика", callback_data='debug_diagnose')],
        [InlineKeyboardButton("🔧 Расширенная отладка", callback_data='debug_advanced')],
        base_handler.create_back_button('main_menu'),
        base_handler.create_close_button()
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        query.answer()
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

@register_menu_handler('debug_report')
@base_handler.access_check_decorator
def handle_debug_report(update, context):
    """Обработчик диагностики отчета"""
    from core.monitor import debug_morning_report
    return debug_morning_report(update, context)

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

def enable_debug_mode(query):
    """Включает режим отладки"""
    try:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        
        debug_log("🟢 Отладка включена через меню бота")
        
        query.edit_message_text(
            "🟢 *Отладка включена*\n\n"
            "Теперь все операции будут детально логироваться.\n"
            "Логи сохраняются в /opt/monitoring/logs/debug.log\n\n"
            "*Включены функции:*\n"
            "• Детальное логирование операций\n"
            "• Отладочные сообщения в консоли\n"
            "• Диагностика подключений",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 Выключить", callback_data='debug_disable')],
                [InlineKeyboardButton("🔧 Расширенная", callback_data='debug_advanced')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка включения отладки: {e}")

def disable_debug_mode(query):
    """Выключает режим отладки"""
    try:
        import logging
        logging.getLogger().setLevel(logging.INFO)
        
        debug_log("🔴 Отладка выключена через меню бота")
        
        query.edit_message_text(
            "🔴 *Отладка выключена*\n\n"
            "Детальное логирование отключено.\n"
            "Сохраняется только основная информация.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 Включить", callback_data='debug_enable')],
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка выключения отладки: {e}")

def show_debug_status(query):
    """Показывает статус отладки и системную информацию"""
    import os
    from datetime import datetime
    
    try:
        message = "📊 *Статус системы и отладки*\n\n"
        
        # Статус отладки
        try:
            from config.settings import DEBUG_MODE
            debug_status = "🟢 ВКЛ" if DEBUG_MODE else "🔴 ВЫКЛ"
        except ImportError:
            debug_status = "🔴 НЕДОСТУПЕН"
        
        message += f"🐛 *Режим отладки:* {debug_status}\n\n"
        
        # Информация о логах
        message += "*Логи:*\n"
        log_files = {
            'debug.log': '/opt/monitoring/logs/debug.log',
            'bot_debug.log': '/opt/monitoring/bot_debug.log', 
            'mail_monitor.log': '/opt/monitoring/logs/mail_monitor.log'
        }
        
        for log_name, log_path in log_files.items():
            try:
                if os.path.exists(log_path):
                    log_size = os.path.getsize(log_path)
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
            from extensions.extension_manager import extension_manager
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
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка получения статуса: {str(e)[:100]}")

def clear_debug_logs(query):
    """Очищает файлы логов"""
    import os
    import logging
    
    try:
        log_files = [
            '/opt/monitoring/logs/debug.log',
            '/opt/monitoring/bot_debug.log',
            '/opt/monitoring/logs/mail_monitor.log'
        ]
        
        cleared = 0
        errors = []
        
        for log_file in log_files:
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'w') as f:
                        f.write('')
                    cleared += 1
                    
                    # Переконфигурируем логгер если это debug.log
                    if log_file.endswith('debug.log'):
                        logging.getLogger().handlers[0].flush()
                else:
                    # Создаем пустой файл если не существует
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    with open(log_file, 'w') as f:
                        f.write('')
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
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка очистки логов: {e}")

def run_diagnostic(query):
    """Запускает диагностику системы"""
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
                    db_path = '/opt/monitoring/data/backups.db'
                    if os.path.exists(db_path):
                        status = "🟢"
                        message += f"{status} {service}: файл существует\n"
                    else:
                        status = "🔴"
                        message += f"{status} {service}: файл не найден\n"
            except Exception as e:
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
            from extensions.extension_manager import extension_manager
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
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка диагностики: {str(e)[:100]}")

def show_advanced_debug(query):
    """Показывает расширенные настройки отладки"""
    try:
        from config.settings import DEBUG_MODE
        
        message = "🔧 *Расширенные настройки отладки*\n\n"
        message += f"*Основные настройки:*\n"
        message += f"• Режим отладки: {'🟢 ВКЛ' if DEBUG_MODE else '🔴 ВЫКЛ'}\n"
        
        message += f"\n*Статус логов:*\n"
        
        # Добавляем информацию о размерах логов
        log_files = {
            'debug.log': '/opt/monitoring/logs/debug.log',
            'bot_debug.log': '/opt/monitoring/bot_debug.log',
            'mail_monitor.log': '/opt/monitoring/logs/mail_monitor.log'
        }
        
        for log_name, log_path in log_files.items():
            try:
                if os.path.exists(log_path):
                    size = os.path.getsize(log_path) / 1024 / 1024
                    message += f"• {log_name}: {size:.2f} MB\n"
                else:
                    message += f"• {log_name}: файл не существует\n"
            except:
                message += f"• {log_name}: ошибка проверки\n"

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data='debug_advanced')],
            [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ]

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка загрузки расширенных настроек: {str(e)[:100]}")