"""
/core/monitor_core.py
Server Monitoring System v5.2.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Core system
Система мониторинга серверов
Версия: 5.2.4
Автор: Александр Суханов (c)
Лицензия: MIT
Ядро системы
"""

# Новые импорты из модульной структуры
from lib.logging import debug_log
from lib.alerts import (
    send_alert as base_send_alert,
    configure_alerts,
    init_telegram_bot,
    set_silent_override,
    is_silent_time as alerts_is_silent_time,
    get_silent_override,
)
from lib.utils import progress_bar, format_duration
from config.db_settings import DEBUG_MODE, DATA_DIR
from core.monitor import monitor
from modules.availability import availability_checker
from modules.resources import resources_checker
from modules.morning_report import morning_report
from modules.targeted_checks import targeted_checks

# Старые импорты для совместимости
import os
import threading
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from lib.utils import safe_import
from extensions.server_checks import check_server_availability

# Глобальные переменные
bot = None
server_status = {}
morning_data = {}
monitoring_active = True
last_check_time = datetime.now()
servers = []
resource_history = {}
last_resource_check = datetime.now()
resource_alerts_sent = {}
last_report_date = None

_alerts_configured = False

def ensure_alerts_config():
    """Гарантирует применение настроек алертов из конфигурации."""
    global _alerts_configured
    if _alerts_configured:
        return

    config = get_config()
    configure_alerts(
        silent_start=getattr(config, "SILENT_START", None),
        silent_end=getattr(config, "SILENT_END", None),
    )
    _alerts_configured = True

def ensure_alert_bot():
    """Инициализирует Telegram-бот для lib.alerts при наличии глобального бота."""
    if bot is None:
        return
    try:
        config = get_config()
        init_telegram_bot(bot, config.CHAT_IDS)
    except Exception as e:
        debug_log(f"Не удалось инициализировать бот алертов: {e}")

def send_alert(message, force=False):
    """Обертка над lib.alerts.send_alert с применением настроек и инициализацией бота."""
    ensure_alerts_config()
    ensure_alert_bot()
    return base_send_alert(message, force=force)

def is_silent_time():
    """Использует единый механизм тихого режима из lib.alerts."""
    ensure_alerts_config()
    return alerts_is_silent_time()

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
get_check_interval = lazy_import('config.db_settings', 'CHECK_INTERVAL')
get_silent_times = lazy_import('config.db_settings', 'SILENT_START')
get_data_collection_time = lazy_import('config.db_settings', 'DATA_COLLECTION_TIME')
get_max_fail_time = lazy_import('config.db_settings', 'MAX_FAIL_TIME')
get_resource_config = lazy_import('config.db_settings', 'RESOURCE_CHECK_INTERVAL')

def get_web_interface_url(config):
    """Формирует URL веб-интерфейса из конфигурации."""
    monitor_ip = getattr(config, "MONITOR_SERVER_IP", "") or ""
    if not monitor_ip:
        web_host = getattr(config, "WEB_HOST", "")
        if web_host in ("0.0.0.0", "", None):
            monitor_ip = "localhost"
        else:
            monitor_ip = web_host
    return f"http://{monitor_ip}:{config.WEB_PORT}"

def perform_manual_check(context, chat_id, progress_message_id):
    """Выполняет проверку серверов с обновлением прогресса"""
    global last_check_time

    # Ленивая загрузка серверов
    global servers
    if not servers:
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()

    total_servers = len(servers)
    results = {"failed": [], "ok": []}

    for i, server in enumerate(servers):
        try:
            progress = (i + 1) / total_servers * 100
            progress_text = f"🔍 Проверяю серверы...\n{progress_bar(progress)}\n\n⏳ Проверяю {server['name']} ({server['ip']})..."

            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=progress_text
            )

            # Используем универсальную проверку
            is_up = check_server_availability(server)

            if is_up:
                results["ok"].append(server)
                debug_log(f"✅ {server['name']} ({server['ip']}) - доступен")
            else:
                results["failed"].append(server)
                debug_log(f"❌ {server['name']} ({server['ip']}) - недоступен")

            time.sleep(1)

        except Exception as e:
            debug_log(f"💥 Критическая ошибка при проверке {server['ip']}: {e}")
            results["failed"].append(server)

    last_check_time = datetime.now()
    send_check_results(context, chat_id, progress_message_id, results)

def send_check_results(context, chat_id, progress_message_id, results):
    """Отправляет результаты проверки"""
    if not results["failed"]:
        message = "✅ Все серверы доступны!"
    else:
        message = "⚠️ Проблемные серверы:\n"

        # Группируем по типу для удобства чтения
        by_type = {}
        for server in results["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n{server_type.upper()} серверы:\n"
            for s in servers_list:
                message += f"- {s['name']} ({s['ip']})\n"

    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text=f"🔍 Проверка завершена!\n\n{message}\n\n⏰ Время проверки: {last_check_time.strftime('%H:%M:%S')}"
    )

def manual_check_handler(update, context):
    """Обработчик ручной проверки серверов"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🔍 Начинаю проверку серверов...\n" + progress_bar(0)
    )

    thread = threading.Thread(
        target=perform_manual_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def get_current_server_status():
    """Выполняет быструю проверку статуса серверов"""
    global servers

    # Переинициализируем серверы при каждом запросе
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()
    debug_log(f"🔄 Обновлен список серверов: {len(servers)} серверов")

    results = {"failed": [], "ok": []}

    for server in servers:
        try:
            is_up = check_server_availability(server)

            if is_up:
                results["ok"].append(server)
            else:
                results["failed"].append(server)

            debug_log(f"🔍 {server['name']} ({server['ip']}) - {'🟢' if is_up else '🔴'}")

        except Exception as e:
            debug_log(f"❌ Ошибка проверки {server['name']}: {e}")
            results["failed"].append(server)

    debug_log(f"📊 Итог проверки: {len(results['ok'])} доступно, {len(results['failed'])} недоступно")
    return results

def monitor_status(update, context):
    """Показывает статус мониторинга"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        # Если вызвано как команда, а не callback
        chat_id = update.message.chat_id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    try:
        current_status = get_current_server_status()
        up_count = len(current_status["ok"])
        down_count = len(current_status["failed"])

        status = "🟢 Активен" if monitoring_active else "🔴 Остановлен"

        # Определяем статус тихого режима
        silent_status_text = "🔇 Тихий режим" if is_silent_time() else "🔊 Обычный режим"
        silent_override = get_silent_override()
        if silent_override is not None:
            if silent_override:
                silent_status_text += " (🔇 Принудительно)"
            else:
                silent_status_text += " (🔊 Принудительно)"

        config = get_config()
        next_check = datetime.now() + timedelta(seconds=config.CHECK_INTERVAL)

        message = (
            f"📊 *Статус мониторинга*\n\n"
            f"**Состояние:** {status}\n"
            f"**Режим:** {silent_status_text}\n\n"
            f"⏰ Последняя проверка: {last_check_time.strftime('%H:%M:%S')}\n"
            f"⏳ Следующая проверка: {next_check.strftime('%H:%M:%S')}\n"
            f"🔢 Всего серверов: {len(servers)}\n"
            f"🟢 Доступно: {up_count}\n"
            f"🔴 Недоступно: {down_count}\n"
            f"🔄 Интервал проверки: {config.CHECK_INTERVAL} сек\n\n"
        )

        # Информация о веб-интерфейсе
        from extensions.extension_manager import extension_manager
        if extension_manager.is_extension_enabled('web_interface'):
            message += f"🌐 *Веб-интерфейс:* {get_web_interface_url(config)}\n"
            message += "_*доступен только в локальной сети_\n"
        else:
            message += "🌐 *Веб-интерфейс:* 🔴 отключен\n"

        if down_count > 0:
            message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"

            # Группируем по типу для удобства чтения
            by_type = {}
            for server in current_status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)

            for server_type, servers_list in by_type.items():
                message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                for i, s in enumerate(servers_list[:8]):  # Ограничиваем показ
                    message += f"• {s['name']} ({s['ip']})\n"

                if len(servers_list) > 8:
                    message += f"• ... и еще {len(servers_list) - 8} серверов\n"

        # Отправляем сообщение в зависимости от типа вызова
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить статус", callback_data='monitor_status')],
                    [InlineKeyboardButton("🔍 Проверить сейчас", callback_data='manual_check')],
                    [InlineKeyboardButton("🔇 Управление режимом", callback_data='silent_status')],
                    [InlineKeyboardButton("📋 Список серверов", callback_data='servers_list')],
                    [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
        else:
            update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        debug_log(f"Ошибка в monitor_status: {e}")
        error_msg = "⚠️ Произошла ошибка при получении статуса"
        if query:
            query.edit_message_text(error_msg)
        else:
            update.message.reply_text(error_msg)

def silent_command(update, context):
    """Обработчик команды /silent"""
    config = get_config()
    silent_status = "🟢 активен" if is_silent_time() else "🔴 неактивен"
    message = (
        f"🔇 *Статус тихого режима:* {silent_status}\n\n"
        f"⏰ *Время работы:* {config.SILENT_START}:00 - {config.SILENT_END}:00\n\n"
        f"💡 *В тихом режиме:*\n"
        f"• Регулярные уведомления не отправляются\n"
        f"• Критические ошибки все равно отправляются\n"
        f"• Ручные проверки работают нормально\n"
        f"• Утренние отчеты отправляются принудительно"
    )

    update.message.reply_text(message, parse_mode='Markdown')

def silent_status_handler(update, context):
    """Обработчик кнопки статуса тихого режима"""
    query = update.callback_query
    query.answer()

    # Определяем текущий режим
    silent_override = get_silent_override()
    if silent_override is None:
        mode_text = "🔄 Автоматический"
        mode_desc = "Работает по расписанию"
    elif silent_override:
        mode_text = "🔇 Принудительно тихий"
        mode_desc = "Все уведомления отключены"
    else:
        mode_text = "🔊 Принудительно громкий"
        mode_desc = "Все уведомления включены"

    # Правильно определяем статус - инвертируем для понятности пользователю
    current_status = "🔴 неактивен" if is_silent_time() else "🟢 активен"
    status_description = "тихий режим" if is_silent_time() else "громкий режим"
    config = get_config()
    message = (
        f"🔇 *Управление тихим режимом*\n\n"
        f"**Текущий статус:** {current_status}\n"
        f"**Режим работы:** {mode_text}\n"
        f"*{mode_desc}*\n"
        f"**Фактически:** {status_description}\n\n"
        f"⏰ *Расписание тихого режима:* {config.SILENT_START}:00 - {config.SILENT_END}:00\n\n"
        f"💡 *Пояснение:*\n"
        f"- 🟢 активен = уведомления работают\n"
        f"- 🔴 неактивен = уведомления отключены\n"
        f"- 🔊 громкий режим = все уведомления включены\n"
        f"- 🔇 тихий режим = только критические уведомления"
    )

    keyboard = [
        [InlineKeyboardButton("🔇 Включить принудительно тихий", callback_data='force_silent')],
        [InlineKeyboardButton("🔊 Включить принудительно громкий", callback_data='force_loud')],
        [InlineKeyboardButton("🔄 Вернуть автоматический режим", callback_data='auto_mode')],
        [InlineKeyboardButton("↩️ Назад в управление", callback_data='control_panel'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def force_silent_handler(update, context):
    """Включает принудительный тихий режим"""
    set_silent_override(True)
    query = update.callback_query
    query.answer()

    send_alert("🔇 *Принудительный тихий режим включен*\nВсе уведомления отключены до смены режима.", force=True)

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)

def force_loud_handler(update, context):
    """Включает принудительный громкий режим"""
    set_silent_override(False)
    query = update.callback_query
    query.answer()

    send_alert("🔊 *Принудительный громкий режим включен*\nВсе уведомления активны до смены режима.", force=True)

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)

def auto_mode_handler(update, context):
    """Включает автоматический режим"""
    set_silent_override(None)
    query = update.callback_query
    query.answer()

    current_status = "активен" if is_silent_time() else "неактивен"
    send_alert(f"🔄 *Автоматический режим включен*\nТихий режим сейчас {current_status}.", force=True)

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)

def control_command(update, context):
    """Обработчик команды /control"""
    keyboard = [
        [InlineKeyboardButton("⏸️ Приостановить мониторинг", callback_data='pause_monitoring')],
        [InlineKeyboardButton("▶️ Возобновить мониторинг", callback_data='resume_monitoring')],
        [InlineKeyboardButton("📊 Утренний отчет", callback_data='full_report')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')]
    ]

    status_text = "🟢 Мониторинг активен" if monitoring_active else "🔴 Мониторинг приостановлен"

    update.message.reply_text(
        f"🎛️ *Управление мониторингом*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def control_panel_handler(update, context):
    """Обработчик кнопки панели управления"""
    query = update.callback_query
    query.answer()

    # Создаем кнопку управления мониторингом (объединенная 7.1 и 7.2)
    monitoring_button = InlineKeyboardButton(
        "⏸️ Приостановить мониторинг" if monitoring_active else "▶️ Возобновить мониторинг",
        callback_data='toggle_monitoring'
    )

    keyboard = [
        [monitoring_button],
        [InlineKeyboardButton("📊 Утренний отчет", callback_data='full_report')],
        [InlineKeyboardButton("🔇 Управление тихим режимом", callback_data='silent_status')],
        [InlineKeyboardButton("🔧 Диагностика отчета", callback_data='debug_report')],
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    status_text = "🟢 Мониторинг активен" if monitoring_active else "🔴 Мониторинг приостановлен"

    query.edit_message_text(
        f"🎛️ *Управление мониторинга*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def toggle_monitoring_handler(update, context):
    """Переключает состояние мониторинга"""
    global monitoring_active
    monitoring_active = not monitoring_active
    query = update.callback_query
    query.answer()

    status_text = "▶️ Мониторинг возобновлен" if monitoring_active else "⏸️ Мониторинг приостановлен"

    # Отправляем уведомление о изменении статуса
    if monitoring_active:
        send_alert("🟢 *Мониторинг возобновлен*\nРегулярные проверки серверов активированы.", force=True)
    else:
        send_alert("🔴 *Мониторинг приостановлен*\nРегулярные проверки серверов отключены.", force=True)

    # Возвращаемся в панель управления
    control_panel_handler(update, context)

def pause_monitoring_handler(update, context):
    """Приостановка мониторинга"""
    global monitoring_active
    monitoring_active = False
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "⏸️ Мониторинг приостановлен\n\nУведомления отправляться не будут.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Возобновить", callback_data='resume_monitoring')],
            [InlineKeyboardButton("🎛️ Панель управления", callback_data='control_panel')]
        ])
    )

def resume_monitoring_handler(update, context):
    """Возобновление мониторинга"""
    global monitoring_active
    monitoring_active = True
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "▶️ Мониторинг возобновлен",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎛️ Панель управления", callback_data='control_panel')]
        ])
    )

def check_resources_handler(update, context):
    """Обработчик проверки ресурсов серверов - новое меню с разделением по ресурсам"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    # Меню с разделением по ресурсам
    keyboard = [
        [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
        [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
        [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
        [InlineKeyboardButton("🐧 Linux серверы", callback_data='check_linux')],
        [InlineKeyboardButton("🪟 Windows серверы", callback_data='check_windows')],
        [InlineKeyboardButton("📡 Другие серверы", callback_data='check_other')],
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
         InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]

    if query:
        query.edit_message_text(
            text="🔍 *Выберите что проверить:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text="🔍 *Выберите что проверить:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def check_cpu_resources_handler(update, context):
    """Обработчик проверки только CPU"""
    query = update.callback_query
    if query:
        query.answer("💻 Проверяем CPU...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="💻 *Проверка загрузки CPU...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_cpu_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def check_ram_resources_handler(update, context):
    """Обработчик проверки только RAM"""
    query = update.callback_query
    if query:
        query.answer("🧠 Проверяем RAM...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🧠 *Проверка использования RAM...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_ram_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def check_disk_resources_handler(update, context):
    """Обработчик проверки только Disk"""
    query = update.callback_query
    if query:
        query.answer("💾 Проверяем Disk...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="💾 *Проверка дискового пространства...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_disk_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_cpu_check(context, chat_id, progress_message_id):
    """Выполняет проверку только CPU с детальным прогрессом"""

    def update_progress(progress, status):
        progress_text = f"💻 Проверка CPU...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "⏳ Получаем список серверов...")

        # Получаем все серверы для проверки
        from extensions.server_checks import initialize_servers
        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        cpu_results = []

        update_progress(15, f"⏳ Начинаем проверку {total_servers} серверов...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75)  # 15-90%
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"🔍 Проверяем {server_info}...")

            try:
                resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    resources = get_windows_resources_improved(server["ip"])

                cpu_value = resources.get('cpu', 0) if resources else 0

                cpu_results.append({
                    "server": server,
                    "cpu": cpu_value,
                    "success": resources is not None
                })

            except Exception as e:
                cpu_results.append({
                    "server": server,
                    "cpu": 0,
                    "success": False
                })

        update_progress(95, "⏳ Формируем отчет...")

        # Сортируем по убыванию CPU
        cpu_results.sort(key=lambda x: x["cpu"], reverse=True)

        message = f"💻 **Загрузка CPU серверов**\n\n"

        # Группируем по типам серверов
        windows_cpu = [r for r in cpu_results if r["server"]["type"] == "rdp"]
        linux_cpu = [r for r in cpu_results if r["server"]["type"] == "ssh"]

        # Windows серверы
        message += f"**🪟 Windows серверы:**\n"
        for result in windows_cpu[:10]:  # Показываем топ-10
            server = result["server"]
            cpu_value = result["cpu"]
            status_icon = "🟢" if result["success"] else "🔴"

            if cpu_value > 80:
                cpu_display = f"🚨 {cpu_value}%"
            elif cpu_value > 60:
                cpu_display = f"⚠️ {cpu_value}%"
            else:
                cpu_display = f"{cpu_value}%"

            message += f"{status_icon} {server['name']}: {cpu_display}\n"

        if len(windows_cpu) > 10:
            message += f"• ... и еще {len(windows_cpu) - 10} серверов\n"

        # Linux серверы
        message += f"\n**🐧 Linux серверы:**\n"
        for result in linux_cpu[:10]:  # Показываем топ-10
            server = result["server"]
            cpu_value = result["cpu"]
            status_icon = "🟢" if result["success"] else "🔴"

            if cpu_value > 80:
                cpu_display = f"🚨 {cpu_value}%"
            elif cpu_value > 60:
                cpu_display = f"⚠️ {cpu_value}%"
            else:
                cpu_display = f"{cpu_value}%"

            message += f"{status_icon} {server['name']}: {cpu_display}\n"

        if len(linux_cpu) > 10:
            message += f"• ... и еще {len(linux_cpu) - 10} серверов\n"

        # Статистика
        total_servers = len(cpu_results)
        high_load = len([r for r in cpu_results if r["cpu"] > 80])
        medium_load = len([r for r in cpu_results if 60 < r["cpu"] <= 80])
        successful_checks = len([r for r in cpu_results if r["success"]])

        message += f"\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {total_servers}\n"
        message += f"• Успешно проверено: {successful_checks}\n"
        message += f"• Высокая нагрузка (>80%): {high_load}\n"
        message += f"• Средняя нагрузка (60-80%): {medium_load}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_cpu')],
                [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
                [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке CPU: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def perform_ram_check(context, chat_id, progress_message_id):
    """Выполняет проверку только RAM с детальным прогрессом"""

    def update_progress(progress, status):
        progress_text = f"🧠 Проверка RAM...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "⏳ Получаем список серверов...")

        # Получаем все серверы для проверки
        from extensions.server_checks import initialize_servers
        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        ram_results = []

        update_progress(15, f"⏳ Начинаем проверку {total_servers} серверов...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75)  # 15-90%
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"🔍 Проверяем {server_info}...")

            try:
                resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    resources = get_windows_resources_improved(server["ip"])

                ram_value = resources.get('ram', 0) if resources else 0

                ram_results.append({
                    "server": server,
                    "ram": ram_value,
                    "success": resources is not None
                })

            except Exception as e:
                ram_results.append({
                    "server": server,
                    "ram": 0,
                    "success": False
                })

        update_progress(95, "⏳ Формируем отчет...")

        # Сортируем по убыванию RAM
        ram_results.sort(key=lambda x: x["ram"], reverse=True)

        message = f"🧠 **Использование RAM серверов**\n\n"

        # Группируем по типам серверов
        windows_ram = [r for r in ram_results if r["server"]["type"] == "rdp"]
        linux_ram = [r for r in ram_results if r["server"]["type"] == "ssh"]

        # Windows серверы
        message += f"**🪟 Windows серверы:**\n"
        for result in windows_ram[:10]:  # Показываем топ-10
            server = result["server"]
            ram_value = result["ram"]
            status_icon = "🟢" if result["success"] else "🔴"

            if ram_value > 85:
                ram_display = f"🚨 {ram_value}%"
            elif ram_value > 70:
                ram_display = f"⚠️ {ram_value}%"
            else:
                ram_display = f"{ram_value}%"

            message += f"{status_icon} {server['name']}: {ram_display}\n"

        if len(windows_ram) > 10:
            message += f"• ... и еще {len(windows_ram) - 10} серверов\n"

        # Linux серверы
        message += f"\n**🐧 Linux серверы:**\n"
        for result in linux_ram[:10]:  # Показываем топ-10
            server = result["server"]
            ram_value = result["ram"]
            status_icon = "🟢" if result["success"] else "🔴"

            if ram_value > 85:
                ram_display = f"🚨 {ram_value}%"
            elif ram_value > 70:
                ram_display = f"⚠️ {ram_value}%"
            else:
                ram_display = f"{ram_value}%"

            message += f"{status_icon} {server['name']}: {ram_display}\n"

        if len(linux_ram) > 10:
            message += f"• ... и еще {len(linux_ram) - 10} серверов\n"

        # Статистика
        total_servers = len(ram_results)
        high_usage = len([r for r in ram_results if r["ram"] > 85])
        medium_usage = len([r for r in ram_results if 70 < r["ram"] <= 85])
        successful_checks = len([r for r in ram_results if r["success"]])

        message += f"\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {total_servers}\n"
        message += f"• Успешно проверено: {successful_checks}\n"
        message += f"• Высокое использование (>85%): {high_usage}\n"
        message += f"• Среднее использование (70-85%): {medium_usage}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_ram')],
                [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
                [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке RAM: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def perform_disk_check(context, chat_id, progress_message_id):
    """Выполняет проверку только Disk с детальным прогрессом"""

    def update_progress(progress, status):
        progress_text = f"💾 Проверка Disk...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "⏳ Получаем список серверов...")

        # Получаем все серверы для проверки
        from extensions.server_checks import initialize_servers
        all_servers = initialize_servers()
        ssh_servers = [s for s in all_servers if s["type"] == "ssh"]
        rdp_servers = [s for s in all_servers if s["type"] == "rdp"]
        servers = ssh_servers + rdp_servers

        total_servers = len(servers)
        disk_results = []

        update_progress(15, f"⏳ Начинаем проверку {total_servers} серверов...")

        for i, server in enumerate(servers):
            current_progress = 15 + (i / total_servers * 75)  # 15-90%
            server_info = f"{server['name']} ({server['ip']})"
            update_progress(current_progress, f"🔍 Проверяем {server_info}...")

            try:
                resources = None
                if server["type"] == "ssh":
                    from extensions.server_checks import get_linux_resources_improved
                    resources = get_linux_resources_improved(server["ip"])
                elif server["type"] == "rdp":
                    from extensions.server_checks import get_windows_resources_improved
                    resources = get_windows_resources_improved(server["ip"])

                disk_value = resources.get('disk', 0) if resources else 0

                disk_results.append({
                    "server": server,
                    "disk": disk_value,
                    "success": resources is not None
                })

            except Exception as e:
                disk_results.append({
                    "server": server,
                    "disk": 0,
                    "success": False
                })

        update_progress(95, "⏳ Формируем отчет...")

        # Сортируем по убыванию Disk
        disk_results.sort(key=lambda x: x["disk"], reverse=True)

        message = f"💾 **Использование дискового пространства**\n\n"

        # Группируем по типам серверов
        windows_disk = [r for r in disk_results if r["server"]["type"] == "rdp"]
        linux_disk = [r for r in disk_results if r["server"]["type"] == "ssh"]

        # Windows серверы
        message += f"**🪟 Windows серверы:**\n"
        for result in windows_disk[:10]:  # Показываем топ-10
            server = result["server"]
            disk_value = result["disk"]
            status_icon = "🟢" if result["success"] else "🔴"

            if disk_value > 90:
                disk_display = f"🚨 {disk_value}%"
            elif disk_value > 80:
                disk_display = f"⚠️ {disk_value}%"
            else:
                disk_display = f"{disk_value}%"

            message += f"{status_icon} {server['name']}: {disk_display}\n"

        if len(windows_disk) > 10:
            message += f"• ... и еще {len(windows_disk) - 10} серверов\n"

        # Linux серверы
        message += f"\n**🐧 Linux серверы:**\n"
        for result in linux_disk[:10]:  # Показываем топ-10
            server = result["server"]
            disk_value = result["disk"]
            status_icon = "🟢" if result["success"] else "🔴"

            if disk_value > 90:
                disk_display = f"🚨 {disk_value}%"
            elif disk_value > 80:
                disk_display = f"⚠️ {disk_value}%"
            else:
                disk_display = f"{disk_value}%"

            message += f"{status_icon} {server['name']}: {disk_display}\n"

        if len(linux_disk) > 10:
            message += f"• ... и еще {len(linux_disk) - 10} серверов\n"

        # Статистика
        total_servers = len(disk_results)
        critical_usage = len([r for r in disk_results if r["disk"] > 90])
        warning_usage = len([r for r in disk_results if 80 < r["disk"] <= 90])
        successful_checks = len([r for r in disk_results if r["success"]])

        message += f"\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {total_servers}\n"
        message += f"• Успешно проверено: {successful_checks}\n"
        message += f"• Критическое использование (>90%): {critical_usage}\n"
        message += f"• Предупреждение (80-90%): {warning_usage}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_disk')],
                [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
                [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Disk: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_linux_resources_handler(update, context):
    """Обработчик проверки Linux серверов"""
    query = update.callback_query
    if query:
        query.answer("🐧 Проверяем Linux серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🐧 *Проверка Linux серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_linux_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_linux_check(context, chat_id, progress_message_id):
    """Выполняет проверку Linux серверов с прогрессом"""

    def update_progress(progress, status):
        progress_text = f"🐧 Проверка Linux серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        from extensions.server_checks import check_linux_servers
        update_progress(0, "⏳ Подготовка...")
        results, total_servers = check_linux_servers(update_progress)

        message = f"🐧 **Проверка Linux серверов**\n\n"
        successful_checks = len([r for r in results if r["success"]])
        message += f"✅ Успешно: {successful_checks}/{total_servers}\n\n"

        for result in results:
            server = result["server"]
            resources = result["resources"]

            # Используем правильное имя сервера из конфигурации
            server_name = server["name"]

            if resources:
                message += f"🟢 {server_name}: CPU {resources.get('cpu', 0)}%, RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%\n"
            else:
                message += f"🔴 {server_name}: недоступен\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_linux')],
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
                InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Linux серверов: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_windows_resources_handler(update, context):
    """Обработчик проверки Windows серверов"""
    query = update.callback_query
    if query:
        query.answer("🪟 Проверяем Windows серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🪟 *Проверка Windows серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_windows_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_windows_check(context, chat_id, progress_message_id):
    """Выполняет проверку Windows серверов с прогрессом"""

    def update_progress(progress, status):
        progress_text = f"🪟 Проверка Windows серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    def safe_get(resources, key, default=0):
        """Безопасное получение значения из resources"""
        if resources is None:
            return default
        return resources.get(key, default)

    try:
        # ДИНАМИЧЕСКИЙ ИМПОРТ для избежания циклических зависимостей
        from extensions.server_checks import (
            check_windows_2025_servers,
            check_domain_windows_servers,
            check_admin_windows_servers,
            check_standard_windows_servers
        )

        update_progress(0, "⏳ Подготовка...")

        # Проверяем все типы Windows серверов
        win2025_results, win2025_total = check_windows_2025_servers(update_progress)
        domain_results, domain_total = check_domain_windows_servers(update_progress)
        admin_results, admin_total = check_admin_windows_servers(update_progress)
        win_std_results, win_std_total = check_standard_windows_servers(update_progress)

        message = f"🪟 **Проверка Windows серверов**\n\n"

        # Windows 2025
        win2025_success = len([r for r in win2025_results if r["success"]])
        message += f"**Windows 2025:** {win2025_success}/{win2025_total}\n"
        for result in win2025_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"

            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Доменные серверы
        domain_success = len([r for r in domain_results if r["success"]])
        message += f"\n**Доменные Windows:** {domain_success}/{domain_total}\n"
        for result in domain_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"

            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Серверы с Admin
        admin_success = len([r for r in admin_results if r["success"]])
        message += f"\n**Windows (Admin):** {admin_success}/{admin_total}\n"
        for result in admin_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"

            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Стандартные Windows
        win_std_success = len([r for r in win_std_results if r["success"]])
        message += f"\n**Обычные Windows:** {win_std_success}/{win_std_total}\n"
        for result in win_std_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"

            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_windows')],
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
                InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Windows серверов: {e}"
        debug_log(error_msg)
        import traceback
        debug_log(f"Подробности ошибки: {traceback.format_exc()}")
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_other_resources_handler(update, context):
    """Обработчик проверки других серверов"""
    query = update.callback_query
    if query:
        query.answer("📡 Проверяем другие серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="📡 *Проверка других серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_other_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_other_check(context, chat_id, progress_message_id):
    """Выполняет проверку других серверов"""
    try:
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()
        ping_servers = [s for s in servers if s["type"] == "ping"]

        message = f"📡 **Проверка других серверов**\n\n"
        successful_checks = 0

        for server in ping_servers:
            is_up = check_server_availability(server)
            if is_up:
                successful_checks += 1
                message += f"🟢 {server['name']}: доступен\n"
            else:
                message += f"🔴 {server['name']}: недоступен\n"

        message += f"\n✅ Доступно: {successful_checks}/{len(ping_servers)}"
        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_other')],
                [InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
                InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке других серверов: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_all_resources_handler(update, context):
    """Обработчик полной проверки всех серверов"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🔍 *Запускаю проверку всех серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_full_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_full_check(context, chat_id, progress_message_id):
    """Выполняет полную проверку всех серверов"""

    def update_progress(progress, status):
        progress_text = f"🔍 Полная проверка всех серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        update_progress(10, "⏳ Подготовка...")
        from extensions.server_checks import check_all_servers_by_type
        results, stats = check_all_servers_by_type()

        total_checked = stats["windows_2025"]["checked"] + stats["standard_windows"]["checked"] + stats["linux"]["checked"]
        total_success = stats["windows_2025"]["success"] + stats["standard_windows"]["success"] + stats["linux"]["success"]

        message = f"📊 **Полная проверка серверов**\n\n"
        message += f"✅ Всего доступно: {total_success}/{total_checked}\n\n"

        message += f"**Windows 2025:** {stats['windows_2025']['success']}/{stats['windows_2025']['checked']}\n"
        message += f"**Обычные Windows:** {stats['standard_windows']['success']}/{stats['standard_windows']['checked']}\n"
        message += f"**Linux:** {stats['linux']['success']}/{stats['linux']['checked']}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_all_resources')],
                [InlineKeyboardButton("↩️ Назад", callback_data='check_resources'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при полной проверке: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def start_monitoring():
    """Запускает основной цикл мониторинга"""
    global servers, bot, monitoring_active, last_report_date, morning_data

    # Ленивая инициализация серверов
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()

    # Исключаем сервер мониторинга из списка
    config = get_config()
    monitor_server_ip = getattr(config, "MONITOR_SERVER_IP", "")
    if monitor_server_ip:
        servers = [s for s in servers if s["ip"] != monitor_server_ip]
        debug_log(
            "✅ Сервер мониторинга "
            f"{monitor_server_ip} принудительно исключен из списка. "
            f"Осталось {len(servers)} серверов"
        )
    else:
        debug_log("⚠️ Сервер мониторинга не исключен: MONITOR_SERVER_IP не задан")

    # Ленивая инициализация бота
    from telegram import Bot
    bot = Bot(token=config.TELEGRAM_TOKEN)
    ensure_alerts_config()
    init_telegram_bot(bot, config.CHAT_IDS)
    
    # Инициализация server_status (только для оставшихся серверов)
    for server in servers:
        server_status[server["ip"]] = {
            "last_up": datetime.now(),
            "alert_sent": False,
            "name": server["name"],
            "type": server["type"],
            "resources": None,
            "last_alert": {}
        }

    debug_log(f"✅ Мониторинг запущен для {len(servers)} серверов")

    # Обновляем стартовое сообщение
    start_message = (
        "🟢 *Мониторинг серверов запущен*\n\n"
        f"• Серверов в мониторинге: {len(servers)}\n"
        f"• Проверка ресурсов: каждые {config.RESOURCE_CHECK_INTERVAL // 60} минут\n"
        f"• Утренний отчет: {config.DATA_COLLECTION_TIME.strftime('%H:%M')}\n\n"
    )

    # Информация о веб-интерфейсе
    from extensions.extension_manager import extension_manager
    if extension_manager.is_extension_enabled('web_interface'):
        start_message += f"🌐 *Веб-интерфейс:* {get_web_interface_url(config)}\n"
        start_message += "_*доступен только в локальной сети_\n"
    else:
        start_message += "🌐 *Веб-интерфейс:* 🔴 отключен\n"

    send_alert(start_message)

    last_resource_check = datetime.now()
    last_data_collection = None

    # Инициализируем morning_data если она пустая
    if not morning_data:
        morning_data = {}

    while True:
        current_time = datetime.now()
        current_time_time = current_time.time()

        # Автоматическая проверка ресурсов
        config = get_config()
        if (current_time - last_resource_check).total_seconds() >= config.RESOURCE_CHECK_INTERVAL:
            if monitoring_active and not is_silent_time():
                debug_log("🔄 Автоматическая проверка ресурсов серверов...")
                check_resources_automatically()
                last_resource_check = current_time
            else:
                debug_log("⏸️ Проверка ресурсов пропущена (тихий режим или мониторинг неактивен)")

        # Сбор и отправка утреннего отчета
        config = get_config()
        if (current_time_time.hour == config.DATA_COLLECTION_TIME.hour and
            current_time_time.minute == config.DATA_COLLECTION_TIME.minute):

            # Проверяем, что сегодня еще не отправляли отчет
            today = current_time.date()
            if last_report_date != today:
                debug_log(f"[{current_time}] 🔍 Собираем данные для утреннего отчета...")

                # Собираем текущий статус серверов
                morning_status = get_current_server_status()
                morning_data = {
                    "status": morning_status,
                    "collection_time": current_time,
                    "manual_call": False  # Автоматический вызов
                }
                last_data_collection = current_time

                debug_log(f"✅ Данные собраны: {len(morning_status['ok'])} доступно, {len(morning_status['failed'])} недоступно")

                # СРАЗУ отправляем отчет после сбора данных
                debug_log(f"[{current_time}] 📊 Отправка утреннего отчета...")
                send_morning_report(manual_call=False)  # Автоматический вызов
                last_report_date = today
                debug_log("✅ Утренний отчет отправлен")

                # Добавляем задержку чтобы не запускать повторно в ту же минуту
                time.sleep(65)  # Спим 65 секунд чтобы выйти за пределы минуты сбора
            else:
                debug_log(f"⏭️ Отчет уже отправлен сегодня {last_report_date}")

        # Основной цикл мониторинга доступности
        if monitoring_active:
            last_check_time = current_time

            for server in servers:
                try:
                    ip = server["ip"]
                    status = server_status[ip]

                    # ПОЛНОСТЬЮ ИСКЛЮЧАЕМ сервер мониторинга из любых проверок
                    if ip == monitor_server_ip:
                        server_status[ip]["last_up"] = current_time
                        continue

                    # Проверка доступности
                    is_up = check_server_availability(server)

                    if is_up:
                        handle_server_up(ip, status, current_time)
                    else:
                        handle_server_down(ip, status, current_time)

                except Exception as e:
                    debug_log(f"❌ Ошибка мониторинга {server['name']}: {e}")

        time.sleep(config.CHECK_INTERVAL)

def handle_server_up(ip, status, current_time):
    """Обработка доступного сервера"""
    last_up = status.get("last_up")

    # если по какой-то причине last_up = None — не падаем
    if status.get("alert_sent"):
        if last_up:
            downtime = (current_time - last_up).total_seconds()
            send_alert(
                f"✅ {status['name']} ({ip}) доступен (простой: {int(downtime // 60)} мин)"
            )
        else:
            send_alert(f"✅ {status['name']} ({ip}) доступен")

    server_status[ip] = {
        "last_up": current_time,
        "alert_sent": False,
        "name": status.get("name"),
        "type": status.get("type"),
        "resources": server_status.get(ip, {}).get("resources"),
        "last_alert": server_status.get(ip, {}).get("last_alert", {}),
    }


def handle_server_down(ip, status, current_time):
    """Обработка недоступного сервера"""
    config = get_config()

    last_up = status.get("last_up")
    if not last_up:
        # Самое важное: не даём упасть на None, иначе алерт никогда не уйдёт
        server_status[ip]["last_up"] = current_time
        status["last_up"] = current_time
        last_up = current_time

    downtime = (current_time - last_up).total_seconds()

    if downtime >= config.MAX_FAIL_TIME and not status.get("alert_sent"):
        send_alert(f"🚨 {status['name']} ({ip}) не отвечает (проверка: {status['type'].upper()})")
        server_status[ip]["alert_sent"] = True

def check_resources_automatically():
    """Автоматическая проверка ресурсов с умными предупреждениями"""
    global resource_history, last_resource_check, resource_alerts_sent

    debug_log("🔍 Автоматическая проверка ресурсов серверов...")

    if not monitoring_active or is_silent_time():
        debug_log("⏸️ Проверка ресурсов пропущена (мониторинг неактивен или тихий режим)")
        return

    current_time = datetime.now()
    alerts_found = []

    # Проверяем все серверы
    for server in servers:
        try:
            ip = server["ip"]
            server_name = server["name"]

            debug_log(f"🔍 Проверяем ресурсы {server_name} ({ip})")

            # Получаем текущие ресурсы
            current_resources = None
            if server["type"] == "ssh":
                from extensions.server_checks import get_linux_resources_improved
                current_resources = get_linux_resources_improved(ip)
            elif server["type"] == "rdp":
                from extensions.server_checks import get_windows_resources_improved
                current_resources = get_windows_resources_improved(ip)

            if not current_resources:
                continue

            # Инициализируем историю для сервера если нужно
            if ip not in resource_history:
                resource_history[ip] = []

            # Добавляем текущие ресурсы в историю
            resource_entry = {
                "timestamp": current_time,
                "cpu": current_resources.get("cpu", 0),
                "ram": current_resources.get("ram", 0),
                "disk": current_resources.get("disk", 0),
                "server_name": server_name
            }

            resource_history[ip].append(resource_entry)

            # Ограничиваем историю последними 10 записями
            if len(resource_history[ip]) > 10:
                resource_history[ip] = resource_history[ip][-10:]

            # Проверяем условия для алертов
            server_alerts = check_resource_alerts(ip, resource_entry)

            if server_alerts:
                alerts_found.extend(server_alerts)
                debug_log(f"⚠️ Найдены проблемы для {server_name}: {server_alerts}")

        except Exception as e:
            debug_log(f"❌ Ошибка при проверке ресурсов {server['name']}: {e}")
            continue

    # Отправляем алерты если есть
    if alerts_found:
        send_resource_alerts(alerts_found)

    last_resource_check = current_time
    debug_log(f"✅ Автоматическая проверка ресурсов завершена. Найдено проблем: {len(alerts_found)}")

def check_resource_alerts(ip, current_resource):
    """Проверяет условия для отправки алертов по ресурсам"""
    from config.db_settings import RESOURCE_ALERT_THRESHOLDS, RESOURCE_ALERT_INTERVAL

    alerts = []
    server_name = current_resource["server_name"]

    # Получаем историю проверок (исключая текущую)
    history = resource_history.get(ip, [])[:-1]  # Все кроме последней записи

    # Проверка Disk (одна проверка)
    disk_usage = current_resource.get("disk", 0)
    if disk_usage >= RESOURCE_ALERT_THRESHOLDS["disk_alert"]:
        # Проверяем, не отправляли ли уже алерт по диску
        alert_key = f"{ip}_disk"
        if alert_key not in resource_alerts_sent or (datetime.now() - resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
            alerts.append(f"💾 **Дисковое пространство** на {server_name}: {disk_usage}% (превышен порог {RESOURCE_ALERT_THRESHOLDS['disk_alert']}%)")
            resource_alerts_sent[alert_key] = datetime.now()

    # Проверка CPU (две проверки подряд)
    cpu_usage = current_resource.get("cpu", 0)
    if cpu_usage >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
        # Проверяем предыдущую запись
        if len(history) >= 1:
            prev_cpu = history[-1].get("cpu", 0)
            if prev_cpu >= RESOURCE_ALERT_THRESHOLDS["cpu_alert"]:
                alert_key = f"{ip}_cpu"
                if alert_key not in resource_alerts_sent or (datetime.now() - resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
                    alerts.append(f"💻 **Процессор** на {server_name}: {prev_cpu}% → {cpu_usage}% (2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS['cpu_alert']}%)")
                    resource_alerts_sent[alert_key] = datetime.now()

    # Проверка RAM (две проверки подряд)
    ram_usage = current_resource.get("ram", 0)
    if ram_usage >= RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
        # Проверяем предыдущую запись
        if len(history) >= 1:
            prev_ram = history[-1].get("ram", 0)
            if prev_ram >= RESOURCE_ALERT_THRESHOLDS["ram_alert"]:
                alert_key = f"{ip}_ram"
                if alert_key not in resource_alerts_sent or (datetime.now() - resource_alerts_sent[alert_key]).total_seconds() > RESOURCE_ALERT_INTERVAL:
                    alerts.append(f"🧠 **Память** на {server_name}: {prev_ram}% → {ram_usage}% (2 проверки подряд >= {RESOURCE_ALERT_THRESHOLDS['ram_alert']}%)")
                    resource_alerts_sent[alert_key] = datetime.now()

    return alerts

def send_resource_alerts(alerts):
    """Отправляет алерты по ресурсам"""
    if not alerts:
        return

    message = "🚨 *Проблемы с ресурсами серверов*\n\n"

    # Группируем алерты по типам ресурсов для лучшей читаемости
    disk_alerts = [a for a in alerts if "💾" in a]
    cpu_alerts = [a for a in alerts if "💻" in a]
    ram_alerts = [a for a in alerts if "🧠" in a]

    # Дисковое пространство
    if disk_alerts:
        message += "💾 **Дисковое пространство:**\n"
        for alert in disk_alerts:
            # Извлекаем информацию из алерта
            parts = alert.split("на ")
            if len(parts) > 1:
                server_info = parts[1]
                message += f"• {server_info}\n"
        message += "\n"

    # Процессор
    if cpu_alerts:
        message += "💻 **Процессор (CPU):**\n"
        for alert in cpu_alerts:
            parts = alert.split("на ")
            if len(parts) > 1:
                server_info = parts[1]
                message += f"• {server_info}\n"
        message += "\n"

    # Память
    if ram_alerts:
        message += "🧠 **Память (RAM):**\n"
        for alert in ram_alerts:
            parts = alert.split("на ")
            if len(parts) > 1:
                server_info = parts[1]
                message += f"• {server_info}\n"
        message += "\n"

    message += f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}"

    send_alert(message)
    debug_log(f"✅ Отправлены алерты по ресурсам: {len(alerts)} проблем")

def close_menu(update, context):
    """Закрывает меню"""
    query = update.callback_query
    query.answer()
    query.delete_message()

def diagnose_menu_handler(update, context):
    """Обработчик меню диагностики"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔧 Меню диагностики в разработке")

def daily_report_handler(update, context):
    """Обработчик ежедневного отчета"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("📊 Ежедневный отчет в разработке")

def toggle_silent_mode_handler(update, context):
    """Обработчик переключения тихого режима"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔇 Переключение тихого режима")

def send_morning_report_handler(update, context):
    """Обработчик для принудительной отправки утреннего отчета (через новый modules.morning_report)"""
    query = update.callback_query if hasattr(update, "callback_query") else None
    chat_id = query.message.chat_id if query else update.message.chat_id
    if query:
        try:
            query.answer("⏳ Формирую отчет...")
        except Exception as e:
            debug_log(f"⚠️ Не удалось ответить на callback: {e}")

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    try:
        from modules.morning_report import morning_report

        # Генерируем отчёт (ручной запуск)
        report_text = morning_report.force_report()

        # Отправляем в текущий чат (как отдельное сообщение — надёжнее, чем edit)
        context.bot.send_message(
            chat_id=chat_id,
            text=report_text,
            parse_mode="Markdown"
        )

        if not query:
            update.message.reply_text("📊 Отчет отправлен")

    except Exception as e:
        debug_log(f"❌ Ошибка формирования/отправки утреннего отчёта: {e}")
        import traceback
        debug_log(f"💥 Traceback:\n{traceback.format_exc()}")
        if query:
            query.edit_message_text("❌ Ошибка формирования отчёта")
        else:
            update.message.reply_text("❌ Ошибка формирования отчёта")

def send_morning_report(manual_call=False):
    """Отправляет утренний отчет о доступности серверов и бэкапах

    Args:
        manual_call (bool): Если True - отчет вызван вручную, если False - по расписанию
    """
    global morning_data

    current_time = datetime.now()

    if manual_call:
        debug_log(f"[{current_time}] 📊 Ручной вызов отчета")
        # Для ручного вызова собираем СВЕЖИЕ данные
        current_status = get_current_server_status()
        morning_data = {
            "status": current_status,
            "collection_time": current_time,
            "manual_call": True  # Помечаем как ручной вызов
        }
    else:
        debug_log(f"[{current_time}] 📊 Автоматический утренний отчет")
        # Для автоматического отчета используем данные собранные в DATA_COLLECTION_TIME
        if not morning_data or "status" not in morning_data:
            debug_log("❌ Нет данных для утреннего отчета, собираем текущий статус...")
            current_status = get_current_server_status()
            morning_data = {
                "status": current_status,
                "collection_time": current_time,
                "manual_call": False
            }

    status = morning_data["status"]
    collection_time = morning_data.get("collection_time", datetime.now())
    is_manual = morning_data.get("manual_call", False)

    total_servers = len(status["ok"]) + len(status["failed"])
    up_count = len(status["ok"])
    down_count = len(status["failed"])

    # Формируем сообщение с указанием типа отчета
    if is_manual:
        report_type = "Ручной запрос"
        time_prefix = "⏰ *Время проверки:*"
    else:
        report_type = "Утренний отчет"
        time_prefix = "⏰ *Время сбора данных:*"

    message = f"📊 *{report_type} о доступности серверов*\n\n"
    message += f"{time_prefix} {collection_time.strftime('%H:%M')}\n"
    message += f"🔢 *Всего серверов:* {total_servers}\n"
    message += f"🟢 *Доступно:* {up_count}\n"
    message += f"🔴 *Недоступно:* {down_count}\n"

    # Для ручного отчета используем другой период бэкапов
    if is_manual:
        backup_data = get_backup_summary_for_report(period_hours=24)  # Последние 24 часа
    else:
        backup_data = get_backup_summary_for_report(period_hours=16)  # С 18:00 предыдущего дня

    message += f"\n💾 *Статус бэкапов ({'за последние 24ч' if is_manual else 'за последние 16ч'})*\n"
    message += backup_data

    if down_count > 0:
        message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"

        # Группируем по типу для удобства чтения
        by_type = {}
        for server in status["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
            for s in servers_list:
                message += f"• {s['name']} ({s['ip']})\n"

    else:
        message += f"\n✅ *Все серверы доступны!*\n"

    message += f"\n📋 *Статистика по типам:*\n"

    # Статистика по типам серверов
    type_stats = {}
    all_servers = status["ok"] + status["failed"]
    for server in all_servers:
        if server["type"] not in type_stats:
            type_stats[server["type"]] = {"total": 0, "up": 0}
        type_stats[server["type"]]["total"] += 1

    for server in status["ok"]:
        type_stats[server["type"]]["up"] += 1

    for server_type, stats in type_stats.items():
        up_percent = (stats["up"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        message += f"• {server_type.upper()}: {stats['up']}/{stats['total']} ({up_percent:.1f}%)\n"

    if is_manual:
        message += f"\n⏰ *Отчет сформирован:* {datetime.now().strftime('%H:%M:%S')}"
    else:
        message += f"\n⏰ *Отчет отправлен:* {datetime.now().strftime('%H:%M:%S')}"

    # Отправляем отчет принудительно, даже в тихом режиме
    send_alert(message, force=True)
    debug_log(f"✅ {report_type} отправлен: {up_count}/{total_servers} доступно")

def get_backup_summary_for_report(period_hours=16):
    """Получает сводку по бэкапам за указанный период

    Args:
        period_hours (int): Количество часов для периода (16 для авто-отчета, 24 для ручного)
    """
    try:
        debug_log(f"🔄 Сбор данных о бэкапах за {period_hours} часов...")

        # ДИАГНОСТИКА КОНФИГУРАЦИИ
        debug_proxmox_config()

        import sqlite3
        from datetime import datetime, timedelta

        db_path = DATA_DIR / "backups.db"

        if not db_path.exists():
            debug_log(f"❌ База данных не найдена: {db_path}")
            return "❌ База данных бэкапов недоступна\n"

        since_time = (datetime.now() - timedelta(hours=period_hours)).strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # ДЕТАЛЬНАЯ ДИАГНОСТИКА: какие хосты есть в базе
        cursor.execute('''
            SELECT DISTINCT host_name, COUNT(*) as backup_count,
                   MAX(received_at) as last_backup,
                   SUM(CASE WHEN backup_status = 'success' THEN 1 ELSE 0 END) as success_count
            FROM proxmox_backups
            WHERE received_at >= datetime('now', '-7 days')
            GROUP BY host_name
            ORDER BY last_backup DESC
        ''')
        all_hosts_from_db = cursor.fetchall()

        debug_log("📊 ДИАГНОСТИКА - Все хосты из БД за 7 дней:")
        for host_name, count, last_backup, success_count in all_hosts_from_db:
            debug_log(f"  - {host_name}: {success_count}/{count} успешно, последний: {last_backup}")

        # 1. Proxmox бэкапы - считаем ПОСЛЕДНИЕ бэкапы для каждого хоста
        cursor.execute('''
            SELECT host_name, backup_status, MAX(received_at) as last_backup
            FROM proxmox_backups
            WHERE received_at >= ?
            GROUP BY host_name
        ''', (since_time,))

        proxmox_results = cursor.fetchall()

        debug_log("📊 ДИАГНОСТИКА - Хосты с бэкапами за указанный период:")
        for host_name, status, last_backup in proxmox_results:
            debug_log(f"  - {host_name}: {status}, последний: {last_backup}")

        # Получаем все хосты из конфигурации
        from config.db_settings import PROXMOX_HOSTS

        debug_log("📊 ДИАГНОСТИКА - Хосты из конфигурации PROXMOX_HOSTS:")
        for host in PROXMOX_HOSTS.keys():
            debug_log(f"  - {host}")

        # Определяем активные хосты
        active_host_names = [row[0] for row in all_hosts_from_db]
        all_hosts = [host for host in PROXMOX_HOSTS.keys() if host in active_host_names]

        # Если все еще не 15, используем альтернативный метод
        if len(all_hosts) != 15:
            debug_log(f"⚠️  Найдено {len(all_hosts)} активных хостов, ожидалось 15")
            debug_log("🔍 Пробуем альтернативный метод подсчета...")

            # Метод 2: берем все уникальные хосты из БД за 30 дней
            cursor.execute('''
                SELECT DISTINCT host_name
                FROM proxmox_backups
                WHERE received_at >= datetime('now', '-30 days')
                ORDER BY host_name
            ''')
            all_unique_hosts = [row[0] for row in cursor.fetchall()]

            debug_log("📊 ДИАГНОСТИКА - Все уникальные хосты за 30 дней:")
            for host in all_unique_hosts:
                debug_log(f"  - {host}")

            all_hosts = all_unique_hosts

        debug_log(f"✅ Итоговый список хостов: {len(all_hosts)} - {all_hosts}")

        # Считаем успешные - ВСЕ хосты у которых последний бэкап успешный
        hosts_with_success = len([r for r in proxmox_results if r[1] == 'success'])

        debug_log(f"📊 Proxmox итог: {hosts_with_success}/{len(all_hosts)} успешно")

        # 2. Базы данных - ИСПРАВЛЕННАЯ ЛОГИКА: ищем ПОСЛЕДНИЙ бэкап для каждой базы
        cursor.execute('''
            SELECT backup_type, database_name, backup_status, MAX(received_at) as last_backup
            FROM database_backups
            WHERE received_at >= ?
            GROUP BY backup_type, database_name
        ''', (since_time,))

        db_results = cursor.fetchall()

        # Получаем конфигурацию
        from config.db_settings import DATABASE_BACKUP_CONFIG

        config_databases = {
            'company_database': DATABASE_BACKUP_CONFIG.get("company_databases", {}),
            'barnaul': DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
            'client': DATABASE_BACKUP_CONFIG.get("client_databases", {}),
            'yandex': DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
        }

        # Считаем статистику - КАЖДАЯ база считается успешной если у нее есть успешный бэкап за период
        db_stats = {}
        for category, databases in config_databases.items():
            total_in_config = len(databases)
            if total_in_config > 0:
                successful_count = 0

                # Для каждой базы в категории проверяем есть ли успешный бэкап
                for db_key in databases.keys():
                    found_success = False
                    for backup_type, db_name, status, last_backup in db_results:
                        if backup_type == category and db_name == db_key and status == 'success':
                            found_success = True
                            break

                    if found_success:
                        successful_count += 1

                db_stats[category] = {
                    'total': total_in_config,
                    'successful': successful_count
                }
                debug_log(f"📊 {category}: {successful_count}/{total_in_config} успешно")

        # 3. Устаревшие бэкапы (более 24 часов) - ПРАВИЛЬНЫЙ подсчет
        stale_threshold = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        # Устаревшие хосты - те у которых последний бэкап старше 24 часов
        cursor.execute('''
            SELECT host_name, MAX(received_at) as last_backup
            FROM proxmox_backups
            GROUP BY host_name
            HAVING last_backup < ?
        ''', (stale_threshold,))
        stale_hosts = cursor.fetchall()

        # Устаревшие БД - те у которых последний бэкап старше 24 часов
        cursor.execute('''
            SELECT backup_type, database_name, MAX(received_at) as last_backup
            FROM database_backups
            GROUP BY backup_type, database_name
            HAVING last_backup < ?
        ''', (stale_threshold,))
        stale_databases = cursor.fetchall()

        conn.close()

        # Формируем сообщение
        message = ""

        # Proxmox бэкапы
        if len(all_hosts) > 0:
            success_rate = (hosts_with_success / len(all_hosts)) * 100
            message += f"• Proxmox: {hosts_with_success}/{len(all_hosts)} успешно ({success_rate:.1f}%)"

            if stale_hosts:
                message += f" ⚠️ {len(stale_hosts)} хостов без бэкапов >24ч"
            message += "\n"

        # Базы данных
        message += "• Базы данных:\n"

        category_names = {
            'company_database': 'Основные',
            'barnaul': 'Барнаул',
            'client': 'Клиенты',
            'yandex': 'Yandex'
        }

        for category in ['company_database', 'barnaul', 'client', 'yandex']:
            if category in db_stats and db_stats[category]['total'] > 0:
                stats = db_stats[category]
                type_name = category_names[category]

                success_rate = (stats['successful'] / stats['total']) * 100
                message += f"  - {type_name}: {stats['successful']}/{stats['total']} успешно ({success_rate:.1f}%)"

                # Устаревшие для этого типа
                stale_count = len([db for db in stale_databases if db[0] == category])
                if stale_count > 0:
                    message += f" ⚠️ {stale_count} БД без бэкапов >24ч"
                message += "\n"

        # Общие проблемы
        total_stale = len(stale_hosts) + len(stale_databases)
        if total_stale > 0:
            message += f"\n🚨 Внимание: {total_stale} проблем:\n"
            if stale_hosts:
                message += f"• {len(stale_hosts)} хостов без бэкапов >24ч\n"
            if stale_databases:
                message += f"• {len(stale_databases)} БД без бэкапов >24ч\n"

        return message

    except Exception as e:
        debug_log(f"💥 Критическая ошибка в get_backup_summary_for_report: {e}")
        import traceback
        debug_log(f"💥 Traceback: {traceback.format_exc()}")
        return "❌ Ошибка формирования отчета о бэкапах\n"

def debug_backup_data():
    """Временная функция для отладки данных бэкапов"""
    try:
        import sqlite3
        from datetime import datetime, timedelta

        db_path = DATA_DIR / "backups.db"

        if not db_path.exists():
            debug_log("❌ База данных backups.db не существует!")
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        debug_log(f"📋 Таблицы в базе: {[t[0] for t in tables]}")

        # Данные из proxmox_backups
        cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT host_name) as hosts FROM proxmox_backups WHERE received_at >= datetime('now', '-16 hours')")
        proxmox_stats = cursor.fetchone()
        debug_log(f"📊 Proxmox записи: {proxmox_stats[0]}, хостов: {proxmox_stats[1]}")

        # Данные из database_backups
        cursor.execute("SELECT COUNT(*) as count, COUNT(DISTINCT database_name) as dbs FROM database_backups WHERE received_at >= datetime('now', '-16 hours')")
        db_stats = cursor.fetchone()
        debug_log(f"📊 DB записи: {db_stats[0]}, баз: {db_stats[1]}")

        # Конкретные данные по типам БД
        cursor.execute('''
            SELECT backup_type, COUNT(DISTINCT database_name) as dbs_count
            FROM database_backups
            WHERE received_at >= datetime('now', '-16 hours')
            GROUP BY backup_type
        ''')
        db_by_type = cursor.fetchall()
        debug_log(f"📊 БД по типам: {dict(db_by_type)}")

        conn.close()

    except Exception as e:
        debug_log(f"❌ Ошибка диагностики: {e}")

def debug_morning_report(update, context):
    """Отладочная функция для проверки утреннего отчета"""
    query = update.callback_query
    query.answer()

    debug_log("🔧 Запущена отладочная функция утреннего отчета")

    # Собираем текущий статус
    current_status = get_current_server_status()

    message = f"🔧 *Отладочная информация утреннего отчета*\n\n"
    message += f"🟢 Доступно: {len(current_status['ok'])}\n"
    message += f"🔴 Недоступно: {len(current_status['failed'])}\n"
    message += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"

    # Проверяем данные для отчета
    if morning_data and "status" in morning_data:
        morning_status = morning_data["status"]
        message += f"📊 *Данные утреннего отчета:*\n"
        message += f"• Время сбора: {morning_data.get('collection_time', 'неизвестно')}\n"
        message += f"• Доступно: {len(morning_status['ok'])}\n"
        message += f"• Недоступно: {len(morning_status['failed'])}\n"
    else:
        message += f"❌ *Данные утреннего отчета отсутствуют*\n"

    query.edit_message_text(message, parse_mode='Markdown')

def resource_history_command(update, context):
    """Показывает историю ресурсов"""
    query = update.callback_query
    query.answer()

    message = "📈 *История ресурсов*\n\n"

    if not resource_history:
        message += "История ресурсов пуста\n"
    else:
        for ip, history in list(resource_history.items())[:5]:  # Показываем первые 5 серверов
            server_name = history[0]["server_name"] if history else "Неизвестно"
            message += f"**{server_name}** ({ip}):\n"

            for entry in history[-3:]:  # Последние 3 записи
                message += f"• {entry['timestamp'].strftime('%H:%M')}: CPU {entry['cpu']}%, RAM {entry['ram']}%, Disk {entry['disk']}%\n"
            message += "\n"

    query.edit_message_text(message, parse_mode='Markdown')

def resource_page_handler(update, context):
    """Обработчик постраничного просмотра ресурсов"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("📄 Постраничный просмотр ресурсов в разработке")

def refresh_resources_handler(update, context):
    """Обработчик обновления ресурсов"""
    query = update.callback_query
    query.answer("🔄 Обновляем ресурсы...")
    check_resources_handler(update, context)

def close_resources_handler(update, context):
    """Закрывает меню ресурсов"""
    query = update.callback_query
    query.answer()
    query.delete_message()

def debug_proxmox_config():
    """Временная функция для диагностики конфигурации Proxmox"""
    try:
        from config.db_settings import PROXMOX_HOSTS
        debug_log("=== ДИАГНОСТИКА KONФИГУРАЦИИ PROXMOX ===")
        debug_log(f"Всего хостов в PROXMOX_HOSTS: {len(PROXMOX_HOSTS)}")
        for i, host in enumerate(PROXMOX_HOSTS.keys(), 1):
            debug_log(f"{i}. {host}")
        debug_log("=======================================")
    except Exception as e:
        debug_log(f"❌ Ошибка диагностики конфигурации: {e}")
