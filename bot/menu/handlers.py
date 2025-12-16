"""
Server Monitoring System v4.11.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu handlers
Система мониторинга серверов
Версия: 4.11.1
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики меню бота
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from lib.logging import debug_log
from config.settings import DEBUG_MODE
from bot.menu.builder import (
    build_main_menu_keyboard, 
    build_extensions_menu,
    build_debug_menu
)
from bot.utils import check_access, get_access_denied_response  # Импортируем из общего модуля

def start_command(update, context):
    """Обработчик команды /start с отладочной информацией"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return

    welcome_text = (
        "🤖 *Серверный мониторинг*\n\n"
        "✅ Система работает\n\n"
    )
    
    # Информация о отладке
    try:
        welcome_text += f"🐛 *Режим отладки:* {'🟢 ВКЛ' if DEBUG_MODE else '🔴 ВЫКЛ'}\n"
    except ImportError:
        welcome_text += "🐛 *Режим отладки:* 🔴 Недоступен\n"
    
    from extensions.extension_manager import extension_manager
    if extension_manager.is_extension_enabled('web_interface'):
        welcome_text += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
        welcome_text += "_*доступен только в локальной сети_\n"
    else:
        welcome_text += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
    
    # Отправка сообщения в зависимости от типа обновления
    if update.message:
        update.message.reply_text(welcome_text, parse_mode='Markdown', 
                                 reply_markup=build_main_menu_keyboard())
    elif update.callback_query:
        update.callback_query.edit_message_text(
            welcome_text, 
            parse_mode='Markdown', 
            reply_markup=build_main_menu_keyboard()
        )

def help_command(update, context):
    """Обработчик команды /help"""
    if not check_access(update.effective_chat.id):
        if update.message:
            update.message.reply_text("⛔ У вас нет прав для использования этого бота")
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
    from extensions.extension_manager import extension_manager
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

def show_extensions_menu(update, context):
    """Показывает меню управления расширениями"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
    
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id
    
    from extensions.extension_manager import extension_manager
    extensions_status = extension_manager.get_extensions_status()
    
    message = "🛠️ *Управление расширениями*\n\n"
    message += "📊 *Статус расширений:*\n\n"
    
    for ext_id, status_info in extensions_status.items():
        enabled = status_info['enabled']
        ext_info = status_info['info']
        
        status_icon = "🟢" if enabled else "🔴"
        message += f"{status_icon} *{ext_info['name']}*\n"
        message += f"   {ext_info['description']}\n"
        message += f"   Статус: {'Включено' if enabled else 'Отключено'}\n\n"
    
    if query:
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=build_extensions_menu(extensions_status)
        )
    else:
        update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=build_extensions_menu(extensions_status)
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
        from core.monitor import monitor_status
        monitor_status(update, context)
    
    elif data == 'close':
        try:
            query.delete_message()
        except:
            query.edit_message_text("✅ Меню закрыто")
            
def toggle_extension(update, context, extension_id):
    """Переключает расширение"""
    query = update.callback_query
    
    from extensions.extension_manager import extension_manager
    success, message = extension_manager.toggle_extension(extension_id)
    
    if success:
        query.answer(message)
        show_extensions_menu(update, context)
    else:
        query.answer(message, show_alert=True)

def enable_all_extensions(update, context):
    """Включает все расширения"""
    query = update.callback_query
    
    from extensions.extension_manager import extension_manager
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
    
    from extensions.extension_manager import extension_manager
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    
    disabled_count = 0
    for ext_id in AVAILABLE_EXTENSIONS:
        success, _ = extension_manager.disable_extension(ext_id)
        if success:
            disabled_count += 1
    
    query.answer(f"✅ Отключено {disabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
    show_extensions_menu(update, context)

def debug_command(update, context):
    """Команда управления отладкой"""
    if not check_access(update.effective_chat.id):
        get_access_denied_response(update)
        return
        
    show_debug_menu(update, context)

def show_debug_menu(update, context):
    """Показывает меню управления отладкой"""
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
    
    if query:
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=build_debug_menu()
        )
    else:
        update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=build_debug_menu()
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
            from app.config.debug import debug_config
            debug_config.enable_debug()
        except ImportError:
            pass
        
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
        # Обновляем настройки логирования
        import logging
        logging.getLogger().setLevel(logging.INFO)
        
        # Обновляем конфигурацию отладки если доступна
        try:
            from app.config.debug import debug_config
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
        from app.config.debug import debug_config
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
        
        message += f"\n*Последнее изменение:* {debug_info['last_modified'][:19]}"

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
        
    except ImportError:
        query.edit_message_text(
            "❌ *Расширенная отладка недоступна*\n\n"
            "Модуль debug_config.py не найден.\n"
            "Убедитесь, что файл существует в папке проекта.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='debug_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )
    except Exception as e:
        query.edit_message_text(f"❌ Ошибка загрузки расширенных настроек: {str(e)[:100]}")