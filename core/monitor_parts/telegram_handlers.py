"""
/core/monitor_parts/telegram_handlers.py
Server Monitoring System v8.62.71
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram callback / command handlers extracted from core/monitor_core.py
(PR5b серии оптимизации).
Система мониторинга серверов
Версия: 8.62.71
Автор: Александр Суханов (c)
Лицензия: MIT
~30 handler-функций UI Telegram-бота, выделенных из монолитного
core/monitor_core.py. perform_linux/windows/other/full_check оставлены
рядом с вызывающими их check_*_resources_handler — они не handlers
сами по себе, но в монолите всегда жили парой.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from core.monitor_state import state
from lib.logging import debug_log
from lib.utils import format_duration, progress_bar


def manual_check_handler(update, context):
    """Обработчик ручной проверки серверов"""
    query = update.callback_query if hasattr(update, "callback_query") else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id, text="🔍 Начинаю проверку серверов...\n" + progress_bar(0)
    )

    thread = threading.Thread(
        target=perform_manual_check, args=(context, chat_id, progress_message.message_id)
    )
    thread.start()


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

        status = "🟢 Активен" if state.monitoring_active else "🔴 Остановлен"

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
            f"⏰ Последняя проверка: {state.last_check_time.strftime('%H:%M:%S')}\n"
            f"⏳ Следующая проверка: {next_check.strftime('%H:%M:%S')}\n"
            f"🔢 Всего серверов: {len(state.servers)}\n"
            f"🟢 Доступно: {up_count}\n"
            f"🔴 Недоступно: {down_count}\n"
            f"🔄 Интервал проверки: {config.CHECK_INTERVAL} сек\n\n"
        )

        # Информация о веб-интерфейсе
        from extensions.extension_manager import extension_manager

        if extension_manager.is_extension_enabled("web_interface"):
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
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🔄 Обновить статус", callback_data="monitor_status"
                            )
                        ],
                        [InlineKeyboardButton("🔍 Проверить сейчас", callback_data="manual_check")],
                        [
                            InlineKeyboardButton(
                                "🔇 Управление режимом", callback_data="silent_status"
                            )
                        ],
                        [InlineKeyboardButton("📋 Список серверов", callback_data="servers_list")],
                        [InlineKeyboardButton("🎛️ Управление", callback_data="control_panel")],
                        [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
                        [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
                    ]
                ),
            )
        else:
            update.message.reply_text(message, parse_mode="Markdown")

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

    update.message.reply_text(message, parse_mode="Markdown")


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
        [InlineKeyboardButton("🔇 Включить принудительно тихий", callback_data="force_silent")],
        [InlineKeyboardButton("🔊 Включить принудительно громкий", callback_data="force_loud")],
        [InlineKeyboardButton("🔄 Вернуть автоматический режим", callback_data="auto_mode")],
        [InlineKeyboardButton("↩️ Назад в управление", callback_data="control_panel")],
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    query.edit_message_text(
        text=message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def force_silent_handler(update, context):
    """Включает принудительный тихий режим"""
    set_silent_override(True)
    query = update.callback_query
    query.answer()

    send_alert(
        "🔇 *Принудительный тихий режим включен*\nВсе уведомления отключены до смены режима.",
        force=True,
    )

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def force_loud_handler(update, context):
    """Включает принудительный громкий режим"""
    set_silent_override(False)
    query = update.callback_query
    query.answer()

    send_alert(
        "🔊 *Принудительный громкий режим включен*\nВсе уведомления активны до смены режима.",
        force=True,
    )

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def auto_mode_handler(update, context):
    """Включает автоматический режим"""
    set_silent_override(None)
    query = update.callback_query
    query.answer()

    current_status = "активен" if is_silent_time() else "неактивен"
    send_alert(
        f"🔄 *Автоматический режим включен*\nТихий режим сейчас {current_status}.", force=True
    )

    # Возвращаемся в управление тихим режимом
    silent_status_handler(update, context)


def control_command(update, context):
    """Обработчик команды /control"""
    keyboard = [
        [InlineKeyboardButton("⏸️ Приостановить мониторинг", callback_data="pause_monitoring")],
        [InlineKeyboardButton("▶️ Возобновить мониторинг", callback_data="resume_monitoring")],
        [InlineKeyboardButton("↩️ Назад", callback_data="monitor_status")],
    ]

    status_text = (
        "🟢 Мониторинг активен" if state.monitoring_active else "🔴 Мониторинг приостановлен"
    )

    update.message.reply_text(
        f"🎛️ *Управление мониторингом*\n\n{status_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def control_panel_handler(update, context):
    """Обработчик кнопки панели управления"""
    query = update.callback_query
    query.answer()

    # Создаем кнопку управления мониторингом (объединенная 7.1 и 7.2)
    monitoring_button = InlineKeyboardButton(
        "⏸️ Приостановить мониторинг" if state.monitoring_active else "▶️ Возобновить мониторинг",
        callback_data="toggle_monitoring",
    )

    keyboard = [
        [monitoring_button],
        [InlineKeyboardButton("🔇 Управление тихим режимом", callback_data="silent_status")],
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    status_text = (
        "🟢 Мониторинг активен" if state.monitoring_active else "🔴 Мониторинг приостановлен"
    )

    query.edit_message_text(
        f"🎛️ *Управление мониторинга*\n\n{status_text}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def toggle_monitoring_handler(update, context):
    """Переключает состояние мониторинга"""
    # global-стейт вынесен в core.monitor_state.state
    state.monitoring_active = not state.monitoring_active
    query = update.callback_query
    query.answer()

    status_text = (
        "▶️ Мониторинг возобновлен" if state.monitoring_active else "⏸️ Мониторинг приостановлен"
    )

    # Отправляем уведомление о изменении статуса
    if state.monitoring_active:
        send_alert(
            "🟢 *Мониторинг возобновлен*\nРегулярные проверки серверов активированы.", force=True
        )
    else:
        send_alert(
            "🔴 *Мониторинг приостановлен*\nРегулярные проверки серверов отключены.", force=True
        )

    # Возвращаемся в панель управления
    control_panel_handler(update, context)


def pause_monitoring_handler(update, context):
    """Приостановка мониторинга"""
    # global-стейт вынесен в core.monitor_state.state
    state.monitoring_active = False
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "⏸️ Мониторинг приостановлен\n\nУведомления отправляться не будут.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("▶️ Возобновить", callback_data="resume_monitoring")],
                [InlineKeyboardButton("🎛️ Панель управления", callback_data="control_panel")],
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            ]
        ),
    )


def resume_monitoring_handler(update, context):
    """Возобновление мониторинга"""
    # global-стейт вынесен в core.monitor_state.state
    state.monitoring_active = True
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        "▶️ Мониторинг возобновлен",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🎛️ Панель управления", callback_data="control_panel")],
                [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            ]
        ),
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    # Меню с разделением по ресурсам
    keyboard = [
        [InlineKeyboardButton("💻 Проверить CPU", callback_data="check_cpu")],
        [InlineKeyboardButton("🧠 Проверить RAM", callback_data="check_ram")],
        [InlineKeyboardButton("💾 Проверить Disk", callback_data="check_disk")],
        [InlineKeyboardButton("🐧 Linux серверы", callback_data="check_linux")],
        [InlineKeyboardButton("🪟 Windows серверы", callback_data="check_windows")],
        [InlineKeyboardButton("📡 Другие серверы", callback_data="check_other")],
        [
            InlineKeyboardButton(
                "⚙️ Настроить параметры проверки", callback_data="settings_resources"
            )
        ],
        [
            InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]

    if query:
        query.edit_message_text(
            text="🔍 *Выберите что проверить:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        update.message.reply_text(
            text="🔍 *Выберите что проверить:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="💻 *Проверка загрузки CPU...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_cpu_check, args=(context, chat_id, progress_message.message_id)
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🧠 *Проверка использования RAM...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_ram_check, args=(context, chat_id, progress_message.message_id)
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="💾 *Проверка дискового пространства...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_disk_check, args=(context, chat_id, progress_message.message_id)
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

    config = get_config()
    if str(chat_id) not in config.CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🐧 *Проверка Linux серверов...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_linux_check, args=(context, chat_id, progress_message.message_id)
    )
    thread.start()


def perform_linux_check(context, chat_id, progress_message_id):
    """Выполняет проверку Linux серверов с прогрессом"""

    def update_progress(progress, status):
        progress_text = f"🐧 Проверка Linux серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=progress_text
        )

    try:
        from extensions.server_checks import check_linux_servers

        update_progress(0, "⏳ Подготовка...")
        results, total_servers = check_linux_servers(update_progress)

        message = "🐧 **Проверка Linux серверов**\n\n"
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
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔄 Обновить", callback_data="check_linux")],
                    [
                        InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Linux серверов: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=error_msg
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🪟 *Проверка Windows серверов...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_windows_check, args=(context, chat_id, progress_message.message_id)
    )
    thread.start()


def perform_windows_check(context, chat_id, progress_message_id):
    """Выполняет проверку Windows серверов с прогрессом"""

    def update_progress(progress, status):
        progress_text = f"🪟 Проверка Windows серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=progress_text
        )

    def safe_get(resources, key, default=0):
        """Безопасное получение значения из resources"""
        if resources is None:
            return default
        return resources.get(key, default)

    try:
        # ДИНАМИЧЕСКИЙ ИМПОРТ для избежания циклических зависимостей
        from extensions.server_checks import (
            check_admin_windows_servers,
            check_domain_windows_servers,
            check_standard_windows_servers,
            check_windows_2025_servers,
        )

        update_progress(0, "⏳ Подготовка...")

        # Проверяем все типы Windows серверов
        win2025_results, win2025_total = check_windows_2025_servers(update_progress)
        domain_results, domain_total = check_domain_windows_servers(update_progress)
        admin_results, admin_total = check_admin_windows_servers(update_progress)
        win_std_results, win_std_total = check_standard_windows_servers(update_progress)

        message = "🪟 **Проверка Windows серверов**\n\n"

        # Windows 2025
        win2025_success = len([r for r in win2025_results if r["success"]])
        message += f"**Windows 2025:** {win2025_success}/{win2025_total}\n"
        for result in win2025_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"

            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, "cpu")
            ram_value = safe_get(resources, "ram")
            disk_value = safe_get(resources, "disk")

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
            cpu_value = safe_get(resources, "cpu")
            ram_value = safe_get(resources, "ram")
            disk_value = safe_get(resources, "disk")

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
            cpu_value = safe_get(resources, "cpu")
            ram_value = safe_get(resources, "ram")
            disk_value = safe_get(resources, "disk")

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
            cpu_value = safe_get(resources, "cpu")
            ram_value = safe_get(resources, "ram")
            disk_value = safe_get(resources, "disk")

            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔄 Обновить", callback_data="check_windows")],
                    [
                        InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Windows серверов: {e}"
        debug_log(error_msg)
        import traceback

        debug_log(f"Подробности ошибки: {traceback.format_exc()}")
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=error_msg
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="📡 *Проверка других серверов...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_other_check, args=(context, chat_id, progress_message.message_id)
    )
    thread.start()


def perform_other_check(context, chat_id, progress_message_id):
    """Выполняет проверку других серверов"""
    try:
        from extensions.server_checks import initialize_servers

        servers = initialize_servers()
        ping_servers = [s for s in servers if s["type"] == "ping"]

        message = "📡 **Проверка других серверов**\n\n"
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
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔄 Обновить", callback_data="check_other")],
                    [
                        InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке других серверов: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=error_msg
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

    if not _resource_monitor_enabled():
        if query:
            query.edit_message_text("📊 Мониторинг ресурсов отключён")
        else:
            update.message.reply_text("📊 Мониторинг ресурсов отключён")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🔍 *Запускаю проверку всех серверов...*\n\n⏳ Подготовка...",
        parse_mode="Markdown",
    )

    thread = threading.Thread(
        target=perform_full_check, args=(context, chat_id, progress_message.message_id)
    )
    thread.start()


def perform_full_check(context, chat_id, progress_message_id):
    """Выполняет полную проверку всех серверов"""

    def update_progress(progress, status):
        progress_text = f"🔍 Полная проверка всех серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=progress_text
        )

    try:
        update_progress(10, "⏳ Подготовка...")
        from extensions.server_checks import check_all_servers_by_type

        results, stats = check_all_servers_by_type()

        total_checked = (
            stats["windows_2025"]["checked"]
            + stats["standard_windows"]["checked"]
            + stats["linux"]["checked"]
        )
        total_success = (
            stats["windows_2025"]["success"]
            + stats["standard_windows"]["success"]
            + stats["linux"]["success"]
        )

        message = "📊 **Полная проверка серверов**\n\n"
        message += f"✅ Всего доступно: {total_success}/{total_checked}\n\n"

        message += f"**Windows 2025:** {stats['windows_2025']['success']}/{stats['windows_2025']['checked']}\n"
        message += f"**Обычные Windows:** {stats['standard_windows']['success']}/{stats['standard_windows']['checked']}\n"
        message += f"**Linux:** {stats['linux']['success']}/{stats['linux']['checked']}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔄 Обновить", callback_data="check_all_resources")],
                    [InlineKeyboardButton("↩️ Назад", callback_data="check_resources")],
                    [
                        InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                        InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
                    ],
                ]
            ),
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при полной проверке: {e}"
        debug_log(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_message_id, text=error_msg
        )


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
        # Если Telegram не может распарсить Markdown (из-за спецсимволов в данных),
        # отправляем отчёт обычным текстом, чтобы команда не падала.
        try:
            context.bot.send_message(chat_id=chat_id, text=report_text, parse_mode="Markdown")
        except Exception as send_error:
            error_text = str(send_error).lower()
            if "parse entities" not in error_text:
                raise

            debug_log(
                "⚠️ Утренний отчёт содержит невалидный Markdown, "
                "повторная отправка с отключённым parse_mode"
            )
            context.bot.send_message(chat_id=chat_id, text=report_text, parse_mode=None)

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


def debug_morning_report(update, context):
    """Отладочная функция для проверки утреннего отчета"""
    query = update.callback_query
    query.answer()

    debug_log("🔧 Запущена отладочная функция утреннего отчета")

    # Собираем текущий статус
    current_status = get_current_server_status()

    message = "🔧 *Отладочная информация утреннего отчета*\n\n"
    message += f"🟢 Доступно: {len(current_status['ok'])}\n"
    message += f"🔴 Недоступно: {len(current_status['failed'])}\n"
    message += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"

    # Проверяем данные для отчета
    if state.morning_data and "status" in state.morning_data:
        morning_status = state.morning_data["status"]
        message += "📊 *Данные утреннего отчета:*\n"
        message += f"• Время сбора: {state.morning_data.get('collection_time', 'неизвестно')}\n"
        message += f"• Доступно: {len(morning_status['ok'])}\n"
        message += f"• Недоступно: {len(morning_status['failed'])}\n"
    else:
        message += "❌ *Данные утреннего отчета отсутствуют*\n"

    query.edit_message_text(message, parse_mode="Markdown")


def resource_history_command(update, context):
    """Показывает историю ресурсов"""
    query = update.callback_query
    query.answer()

    message = "📈 *История ресурсов*\n\n"

    if not state.resource_history:
        message += "История ресурсов пуста\n"
    else:
        for ip, history in list(state.resource_history.items())[:5]:  # Показываем первые 5 серверов
            server_name = history[0]["server_name"] if history else "Неизвестно"
            message += f"**{server_name}** ({ip}):\n"

            for entry in history[-3:]:  # Последние 3 записи
                message += f"• {entry['timestamp'].strftime('%H:%M')}: CPU {entry['cpu']}%, RAM {entry['ram']}%, Disk {entry['disk']}%\n"
            message += "\n"

    query.edit_message_text(message, parse_mode="Markdown")


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


__all__ = [
    "auto_mode_handler",
    "check_all_resources_handler",
    "check_cpu_resources_handler",
    "check_disk_resources_handler",
    "check_linux_resources_handler",
    "check_other_resources_handler",
    "check_ram_resources_handler",
    "check_resources_handler",
    "check_windows_resources_handler",
    "close_menu",
    "close_resources_handler",
    "control_command",
    "control_panel_handler",
    "daily_report_handler",
    "debug_morning_report",
    "diagnose_menu_handler",
    "force_loud_handler",
    "force_silent_handler",
    "manual_check_handler",
    "monitor_status",
    "pause_monitoring_handler",
    "perform_full_check",
    "perform_linux_check",
    "perform_other_check",
    "perform_windows_check",
    "refresh_resources_handler",
    "resource_history_command",
    "resource_page_handler",
    "resume_monitoring_handler",
    "send_morning_report_handler",
    "silent_command",
    "silent_status_handler",
    "toggle_monitoring_handler",
    "toggle_silent_mode_handler",
]
