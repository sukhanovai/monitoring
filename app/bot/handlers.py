"""
Server Monitoring System v4.3.5 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Основные обработчики команд бота
Версия: 4.3.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from typing import Dict, List, Any, Optional

from app.core.monitoring import monitoring_core
from app.utils.common import debug_log, progress_bar
from app.config import settings
import threading
import time
from datetime import datetime, timedelta


# ==================== БАЗОВЫЕ ОБРАБОТЧИКИ ====================

def close_menu(update, context):
    """Закрывает меню"""
    query = update.callback_query
    query.answer()
    query.delete_message()


def force_silent_handler(update, context):
    """Включает принудительный тихий режим"""
    monitoring_core.silent_override = True
    query = update.callback_query
    query.answer()

    monitoring_core.send_alert(
        "🔇 *Принудительный тихий режим включен*\nВсе уведомления отключены до смены режима.", 
        force=True
    )

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def force_loud_handler(update, context):
    """Включает принудительный громкий режим"""
    monitoring_core.silent_override = False
    query = update.callback_query
    query.answer()

    monitoring_core.send_alert(
        "🔊 *Принудительный громкий режим включен*\nВсе уведомления активны до смены режима.", 
        force=True
    )

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def auto_mode_handler(update, context):
    """Включает автоматический режим"""
    monitoring_core.silent_override = None
    query = update.callback_query
    query.answer()

    current_status = "активен" if monitoring_core.is_silent_time() else "неактивен"
    monitoring_core.send_alert(
        f"🔄 *Автоматический режим включен*\nТихий режим сейчас {current_status}.", 
        force=True
    )

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def toggle_silent_mode_handler(update, context):
    """Обработчик переключения тихого режима"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔇 Переключение тихого режима")


def send_morning_report_handler(update, context):
    """Обработчик для принудительной отправки утреннего отчета"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    if str(chat_id) not in settings.CHAT_IDS:
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


def resource_history_command(update, context):
    """Показывает историю ресурсов"""
    query = update.callback_query
    query.answer()
    
    message = "📈 *История ресурсов*\n\n"
    
    if not monitoring_core.resource_history:
        message += "История ресурсов пуста\n"
    else:
        for ip, history in list(monitoring_core.resource_history.items())[:5]:
            server_name = history[0]["server_name"] if history else "Неизвестно"
            message += f"**{server_name}** ({ip}):\n"
            
            for entry in history[-3:]:
                message += f"• {entry['timestamp'].strftime('%H:%M')}: CPU {entry['cpu']}%, RAM {entry['ram']}%, Disk {entry['disk']}%\n"
            message += "\n"
    
    query.edit_message_text(message, parse_mode='Markdown')


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


# ==================== ОБРАБОТЧИКИ ПРОВЕРКИ РЕСУРСОВ ====================

def check_linux_resources_handler(update, context):
    """Обработчик проверки Linux серверов"""
    query = update.callback_query
    if query:
        query.answer("🐧 Проверяем Linux серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in settings.CHAT_IDS:
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

    if str(chat_id) not in settings.CHAT_IDS:
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

    if str(chat_id) not in settings.CHAT_IDS:
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


def check_cpu_resources_handler(update, context):
    """Обработчик проверки только CPU"""
    query = update.callback_query
    if query:
        query.answer("💻 Проверяем CPU...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in settings.CHAT_IDS:
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

    if str(chat_id) not in settings.CHAT_IDS:
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

    if str(chat_id) not in settings.CHAT_IDS:
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


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def perform_linux_check(context, chat_id, progress_message_id):
    """Выполняет проверку Linux серверов с прогрессом"""
    # TODO: Реализовать
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text="🐧 *Проверка Linux серверов*\n\n⏳ В разработке..."
    )


def perform_windows_check(context, chat_id, progress_message_id):
    """Выполняет проверку Windows серверов с прогрессом"""
    # TODO: Реализовать
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text="🪟 *Проверка Windows серверов*\n\n⏳ В разработке..."
    )


def perform_other_check(context, chat_id, progress_message_id):
    """Выполняет проверку других серверов"""
    # TODO: Реализовать
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text="📡 *Проверка других серверов*\n\n⏳ В разработке..."
    )


def perform_cpu_check(context, chat_id, progress_message_id):
    """Выполняет проверку только CPU с детальным прогрессом"""
    # TODO: Реализовать
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text="💻 *Проверка CPU*\n\n⏳ В разработке..."
    )


def perform_ram_check(context, chat_id, progress_message_id):
    """Выполняет проверку только RAM с детальным прогрессом"""
    # TODO: Реализовать
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text="🧠 *Проверка RAM*\n\n⏳ В разработке..."
    )


def perform_disk_check(context, chat_id, progress_message_id):
    """Выполняет проверку только Disk с детальным прогрессом"""
    # TODO: Реализовать
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=progress_message_id,
        text="💾 *Проверка Disk*\n\n⏳ В разработке..."
    )


def silent_status_handler(update, context):
    """Обработчик кнопки статуса тихого режима (нужен для force_silent_handler и др.)"""
    from bot_menu import silent_status_handler as bot_menu_handler
    return bot_menu_handler(update, context)


def check_resources_handler(update, context):
    """Обработчик проверки ресурсов серверов"""
    from bot_menu import check_resources_handler as bot_menu_handler
    return bot_menu_handler(update, context)


# Экспортируем все обработчики
__all__ = [
    'close_menu',
    'force_silent_handler',
    'force_loud_handler',
    'auto_mode_handler',
    'toggle_silent_mode_handler',
    'send_morning_report_handler',
    'resource_page_handler',
    'refresh_resources_handler',
    'close_resources_handler',
    'resource_history_command',
    'debug_morning_report',
    'check_linux_resources_handler',
    'check_windows_resources_handler',
    'check_other_resources_handler',
    'check_cpu_resources_handler',
    'check_ram_resources_handler',
    'check_disk_resources_handler',
]
