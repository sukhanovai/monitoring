"""
Server Monitoring System v4.4.5 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Основные обработчики команд бота

"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from app.core.monitoring import monitoring_core
from app.utils.common import debug_log, progress_bar
from app.config import settings


# ==================== БАЗОВЫЕ ФУНКЦИИ ====================

def check_access(chat_id):
    """Проверка доступа к боту"""
    return str(chat_id) in settings.CHAT_IDS


# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ ====================

def manual_check_handler(update, context):
    """Обработчик ручной проверки серверов"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    if not check_access(chat_id):
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


def perform_manual_check(context, chat_id, progress_message_id):
    """Выполняет проверку серверов с обновлением прогресса"""
    total_servers = len(monitoring_core.servers)
    results = {"failed": [], "ok": []}

    for i, server in enumerate(monitoring_core.servers):
        try:
            progress = (i + 1) / total_servers * 100
            progress_text = f"🔍 Проверяю серверы...\n{progress_bar(progress)}\n\n⏳ Проверяю {server['name']} ({server['ip']})..."

            context.bot.edit_message_text(
                chat_id=chat_id, 
                message_id=progress_message_id, 
                text=progress_text
            )

            # Используем универсальную проверку
            is_up = monitoring_core.check_server_availability(server)

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

    monitoring_core.last_check_time = datetime.now()
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
        text=f"🔍 Проверка завершена!\n\n{message}\n\n⏰ Время проверки: {monitoring_core.last_check_time.strftime('%H:%M:%S')}"
    )


def monitor_status(update, context):
    """Показывает статус мониторинга"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        # Если вызвано как команда, а не callback
        chat_id = update.message.chat_id

    if not check_access(chat_id):
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    try:
        current_status = monitoring_core.get_current_server_status()
        up_count = len(current_status["ok"])
        down_count = len(current_status["failed"])

        status = "🟢 Активен" if monitoring_core.monitoring_active else "🔴 Остановлен"

        # Определяем статус тихого режима
        silent_status_text = "🔇 Тихий режим" if monitoring_core.is_silent_time() else "🔊 Обычный режим"
        if monitoring_core.silent_override is not None:
            if monitoring_core.silent_override:
                silent_status_text += " (🔇 Принудительно)"
            else:
                silent_status_text += " (🔊 Принудительно)"

        next_check = datetime.now() + timedelta(seconds=settings.CHECK_INTERVAL)

        message = (
            f"📊 *Статус мониторинга*\n\n"
            f"**Состояние:** {status}\n"
            f"**Режим:** {silent_status_text}\n\n"
            f"⏰ Последняя проверка: {monitoring_core.last_check_time.strftime('%H:%M:%S')}\n"
            f"⏳ Следующая проверка: {next_check.strftime('%H:%M:%S')}\n"
            f"🔢 Всего серверов: {len(monitoring_core.servers)}\n"
            f"🟢 Доступно: {up_count}\n"
            f"🔴 Недоступно: {down_count}\n"
            f"🔄 Интервал проверки: {settings.CHECK_INTERVAL} сек\n\n"
        )

        # Информация о веб-интерфейсе
        from extensions.extension_manager import extension_manager
        if extension_manager.is_extension_enabled('web_interface'):
            message += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
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
    silent_status = "🟢 активен" if monitoring_core.is_silent_time() else "🔴 неактивен"
    message = (
        f"🔇 *Статус тихого режима:* {silent_status}\n\n"
        f"⏰ *Время работы:* {settings.SILENT_START}:00 - {settings.SILENT_END}:00\n\n"
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
    if monitoring_core.silent_override is None:
        mode_text = "🔄 Автоматический"
        mode_desc = "Работает по расписанию"
    elif monitoring_core.silent_override:
        mode_text = "🔇 Принудительно тихий"
        mode_desc = "Все уведомления отключены"
    else:
        mode_text = "🔊 Принудительно громкий"
        mode_desc = "Все уведомления включены"

    # Правильно определяем статус - инвертируем для понятности пользователю
    current_status = "🔴 неактивен" if monitoring_core.is_silent_time() else "🟢 активен"
    status_description = "тихий режим" if monitoring_core.is_silent_time() else "громкий режим"

    message = (
        f"🔇 *Управление тихим режимом*\n\n"
        f"**Текущий статус:** {current_status}\n"
        f"**Режим работы:** {mode_text}\n"
        f"*{mode_desc}*\n"
        f"**Фактически:** {status_description}\n\n"
        f"⏰ *Расписание тихого режима:* {settings.SILENT_START}:00 - {settings.SILENT_END}:00\n\n"
        f"💡 *Пояснение:*\n"
        f"- 🟢 активен = уведомления работают\n"
        f"- 🔴 неактивен = уведомления отключены\n"
        f"- 🔊 громкий режим = все уведомления включены\n"
        f"- 🔇 тихий режим = только критические уведомления"
    )

    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔇 Включить принудительно тихий", callback_data='force_silent')],
            [InlineKeyboardButton("🔊 Включить принудительно громкий", callback_data='force_loud')],
            [InlineKeyboardButton("🔄 Вернуть автоматический режим", callback_data='auto_mode')],
            [InlineKeyboardButton("↩️ Назад в управление", callback_data='control_panel'),
             InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )


def force_silent_handler(update, context):
    """Включает принудительный тихий режим"""
    monitoring_core.silent_override = True
    query = update.callback_query
    query.answer()

    monitoring_core.send_alert("🔇 *Принудительный тихий режим включен*\nВсе уведомления отключены до смены режима.", force=True)

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def force_loud_handler(update, context):
    """Включает принудительный громкий режим"""
    monitoring_core.silent_override = False
    query = update.callback_query
    query.answer()

    monitoring_core.send_alert("🔊 *Принудительный громкий режим включен*\nВсе уведомления активны до смены режима.", force=True)

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def auto_mode_handler(update, context):
    """Включает автоматический режим"""
    monitoring_core.silent_override = None
    query = update.callback_query
    query.answer()

    current_status = "активен" if monitoring_core.is_silent_time() else "неактивен"
    monitoring_core.send_alert(f"🔄 *Автоматический режим включен*\nТихий режим сейчас {current_status}.", force=True)

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def control_panel_handler(update, context):
    """Обработчик кнопки панели управления"""
    query = update.callback_query
    query.answer()

    # Создаем кнопку управления мониторингом
    monitoring_button = InlineKeyboardButton(
        "⏸️ Приостановить мониторинг" if monitoring_core.monitoring_active else "▶️ Возобновить мониторинг",
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
    
    status_text = "🟢 Мониторинг активен" if monitoring_core.monitoring_active else "🔴 Мониторинг приостановлен"

    query.edit_message_text(
        f"🎛️ *Управление мониторинга*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def toggle_monitoring_handler(update, context):
    """Переключает состояние мониторинга"""
    monitoring_core.monitoring_active = not monitoring_core.monitoring_active
    query = update.callback_query
    query.answer()

    status_text = "▶️ Мониторинг возобновлен" if monitoring_core.monitoring_active else "⏸️ Мониторинг приостановлен"
    
    # Отправляем уведомление о изменении статуса
    if monitoring_core.monitoring_active:
        monitoring_core.send_alert("🟢 *Мониторинг возобновлен*\nРегулярные проверки серверов активированы.", force=True)
    else:
        monitoring_core.send_alert("🔴 *Мониторинг приостановлен*\nРегулярные проверки серверов отключены.", force=True)

    # Возвращаемся в панель управления
    control_panel_handler(update, context)


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
    """Обработчик для принудительной отправки утреннего отчета"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    if not check_access(chat_id):
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    # Вызываем отчет с флагом manual_call=True
    monitoring_core._send_morning_report(manual_call=True)

    response = "📊 Отчет отправлен (данные актуальны на момент запроса)"
    if query:
        query.edit_message_text(response)
    else:
        update.message.reply_text(response)


def debug_morning_report(update, context):
    """Отладочная функция для проверки утреннего отчета"""
    query = update.callback_query
    query.answer()
    
    debug_log("🔧 Запущена отладочная функция утреннего отчета")
    
    # Собираем текущий статус
    current_status = monitoring_core.get_current_server_status()
    
    message = f"🔧 *Отладочная информация утреннего отчета*\n\n"
    message += f"🟢 Доступно: {len(current_status['ok'])}\n"
    message += f"🔴 Недоступно: {len(current_status['failed'])}\n"
    message += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    # Проверяем данные для отчета
    if monitoring_core.morning_data and "status" in monitoring_core.morning_data:
        morning_status = monitoring_core.morning_data["status"]
        message += f"📊 *Данные утреннего отчета:*\n"
        message += f"• Время сбора: {monitoring_core.morning_data.get('collection_time', 'неизвестно')}\n"
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
    
    if not monitoring_core.resource_history:
        message += "История ресурсов пуста\n"
    else:
        for ip, history in list(monitoring_core.resource_history.items())[:5]:  # Показываем первые 5 серверов
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


# ==================== ОБРАБОТЧИКИ ПРОВЕРКИ РЕСУРСОВ ====================

def check_resources_handler(update, context):
    """Обработчик проверки ресурсов серверов - новое меню с разделением по ресурсам"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if not check_access(chat_id):
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

    if not check_access(chat_id):
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

    if not check_access(chat_id):
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

    if not check_access(chat_id):
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


def check_linux_resources_handler(update, context):
    """Обработчик проверки Linux серверов"""
    query = update.callback_query
    if query:
        query.answer("🐧 Проверяем Linux серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if not check_access(chat_id):
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


def check_windows_resources_handler(update, context):
    """Обработчик проверки Windows серверов"""
    query = update.callback_query
    if query:
        query.answer("🪟 Проверяем Windows серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if not check_access(chat_id):
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


def check_other_resources_handler(update, context):
    """Обработчик проверки других серверов"""
    query = update.callback_query
    if query:
        query.answer("📡 Проверяем другие серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if not check_access(chat_id):
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


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

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
        
        # Получаем все серверы для проверку
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


def perform_other_check(context, chat_id, progress_message_id):
    """Выполняет проверку других серверов"""
    try:
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()
        ping_servers = [s for s in servers if s["type"] == "ping"]

        message = f"📡 **Проверка других серверов**\n\n"
        successful_checks = 0

        for server in ping_servers:
            is_up = monitoring_core.check_server_availability(server)
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


# ==================== ЭКСПОРТ ====================

__all__ = [
    # Основные обработчики
    'manual_check_handler',
    'monitor_status',
    'silent_command',
    'silent_status_handler',
    'control_panel_handler',
    'toggle_monitoring_handler',
    'close_menu',
    'diagnose_menu_handler',
    'daily_report_handler',
    'toggle_silent_mode_handler',
    
    # Тихий режим
    'force_silent_handler',
    'force_loud_handler',
    'auto_mode_handler',
    
    # Отчеты
    'send_morning_report_handler',
    'debug_morning_report',
    
    # Ресурсы
    'check_resources_handler',
    'resource_page_handler',
    'refresh_resources_handler',
    'close_resources_handler',
    'resource_history_command',
    
    # Проверка ресурсов по типам
    'check_cpu_resources_handler',
    'check_ram_resources_handler',
    'check_disk_resources_handler',
    'check_linux_resources_handler',
    'check_windows_resources_handler',
    'check_other_resources_handler',
    
    # Вспомогательные функции
    'check_access',
    'perform_manual_check',
    'send_check_results',
    'perform_cpu_check',
    'perform_ram_check',
    'perform_disk_check',
    'perform_linux_check',
    'perform_windows_check',
    'perform_other_check',
]

# ==================== ЭКСПОРТ И РЕГИСТРАЦИЯ ====================

def get_handlers():
    """Получить все обработчики команд для бота"""
    from telegram.ext import CommandHandler
    
    # Импортируем все доступные команды
    from app.bot.menus import (
        start_command, help_command, check_command, status_command,
        silent_command, control_command, servers_command, report_command,
        stats_command, diagnose_ssh_command, extensions_command, debug_command,
        backup_command, backup_search_command, backup_help_command
    )
    
    handlers = [
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
        CommandHandler("debug", debug_command),
        CommandHandler("backup", backup_command),
        CommandHandler("backup_search", backup_search_command),
        CommandHandler("backup_help", backup_help_command),
        CommandHandler("fix_monitor", fix_monitor_command),
        CommandHandler("diagnose_windows", diagnose_windows_command),
    ]
    
    return handlers

def fix_monitor_command(update, context):
    """Команда для исправления статуса сервера мониторинга"""
    from app.bot.menus import check_access
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этой команды")
        return
    
    update.message.reply_text("🔧 Команда /fix_monitor временно недоступна (в процессе переноса)")

def diagnose_windows_command(update, context):
    """Диагностика подключения к Windows серверам"""
    from app.bot.menus import check_access
    if not check_access(update.effective_chat.id):
        update.message.reply_text("⛔ У вас нет прав для использования этой команды")
        return
    
    if not context.args:
        update.message.reply_text("❌ Укажите IP Windows сервера: /diagnose_windows <ip>")
        return
    
    update.message.reply_text(f"🔧 Диагностика Windows сервера {context.args[0]} временно недоступна (в процессе переноса)")
