"""
/bot/handlers/callbacks.py
Server Monitoring System v4.14.39
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
A single router for callbacks.
Система мониторинга серверов
Версия: 4.14.39
Автор: Александр Суханов (c)
Лицензия: MIT
Единый router callback’ов.
"""

from bot.menu.handlers import show_main_menu
from settings_handlers import settings_callback_handler, BACKUP_SETTINGS_CALLBACKS
from monitor_core import (
    manual_check_handler,
    monitor_status,
    silent_status_handler,
    control_panel_handler,
    toggle_monitoring_handler,
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.base import check_access, deny_access
from modules.targeted_checks import targeted_checks
from extensions.extension_manager import extension_manager
from bot.handlers.extensions import (
    show_extensions_menu,
    extensions_callback_handler
)

from lib.logging import debug_log

def _server_result_keyboard(server_ip: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📡 Доступность", callback_data=f"check_availability_{server_ip}"),
            InlineKeyboardButton("📊 Ресурсы", callback_data=f"check_resources_{server_ip}"),
        ],
        [
            InlineKeyboardButton("🖥 Доступность сервера", callback_data="show_availability_menu"),
            InlineKeyboardButton("💻 Ресурсы сервера", callback_data="show_resources_menu"),
        ],
        [
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ])

def callback_router(update, context):
    debug_log("🧭 ROUTER MARKER v1: entered callback_router()")
    try:
        query = update.callback_query
        data = query.data

        debug_log(f"📥 CALLBACK DATA: {data}")

        # дальше ваш существующий код router...

    except Exception as e:
        debug_log(f"💥 callback_router crashed: {e}\n{traceback.format_exc()}")
        # Фоллбек пользователю (чтобы видеть проблему в Telegram)
        try:
            if update.callback_query:
                update.callback_query.answer("❌ Ошибка обработчика. Подробности в логах.", show_alert=True)
        except Exception:
            pass
        
    query = update.callback_query
    data = query.data

    debug_log(f"📥 CALLBACK DATA: {data}")
    
    if not check_access(update):
        deny_access(update)
        return

    query.answer()

    # ------------------------------------------------
    # Главное меню
    # ------------------------------------------------
    if data == 'main_menu':
        from bot.menu.handlers import show_main_menu
        show_main_menu(update, context)

    # ------------------------------------------------
    # ДОСТУПНОСТЬ ВСЕХ СЕРВЕРОВ (ручная проверка)
    # ------------------------------------------------
    elif data == 'manual_check':
        manual_check_handler(update, context)
        
    # ------------------------------------------------
    # ОДИН СЕРВЕР (доступность)
    # ------------------------------------------------
    elif data == 'show_availability_menu':
        query.edit_message_text(
            "📡 *Выберите сервер для проверки доступности:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_availability"
            )
        )

    elif data.startswith('check_availability_'):
        server_id = data.replace('check_availability_', '')

        success, server, message = targeted_checks.check_single_server_availability(server_id)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=_server_result_keyboard(server_id)
        )

    # ------------------------------------------------
    # РЕСУРСЫ СЕРВЕРА
    # ------------------------------------------------
    elif data == 'show_resources_menu':
        query.edit_message_text(
            "📊 *Выберите сервер для проверки ресурсов:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_resources"
            )
        )

    elif data.startswith('check_resources_'):
        server_id = data.replace('check_resources_', '')

        success, server, message = targeted_checks.check_single_server_resources(server_id)

        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=_server_result_keyboard(server_id)
        )

    # ------------------------------------------------
    # ПРОВЕРКА РЕСУРСОВ ВСЕХ СЕРВЕРОВ
    # ------------------------------------------------
    elif data == 'check_resources':
        query.edit_message_text(
            "📊 *Выберите сервер для проверки ресурсов:*",
            parse_mode='Markdown',
            reply_markup=targeted_checks.create_server_selection_menu(
                action="check_resources"
            )
        )

    # ------------------------------------------------
    # СТАТУС / ПРОВЕРКА / УПРАВЛЕНИЕ (monitor_core)
    # ------------------------------------------------
    elif data == 'monitor_status':
        monitor_status(update, context)

    elif data == 'manual_check':
        manual_check_handler(update, context)

    elif data == 'silent_status':
        silent_status_handler(update, context)

    elif data == 'control_panel':
        control_panel_handler(update, context)

    elif data == 'toggle_monitoring':
        toggle_monitoring_handler(update, context)

    elif data == 'pause_monitoring':
        from monitor_core import pause_monitoring_handler
        pause_monitoring_handler(update, context)

    elif data == 'resume_monitoring':
        from monitor_core import resume_monitoring_handler
        resume_monitoring_handler(update, context)

    elif data == 'servers_list':
        from extensions.server_checks import servers_list_handler
        servers_list_handler(update, context)

    elif data in ('full_report', 'daily_report'):
        # в monitor_core это один и тот же handler в старом меню
        from monitor_core import send_morning_report_handler
        send_morning_report_handler(update, context)

    # ------------------------------------------------
    # НАСТРОЙКИ (settings_handlers)
    # ------------------------------------------------
    elif data.startswith(('settings_', 'set_', 'manage_', 'ssh_', 'windows_')):
        # settings_handlers сам разбирает все эти ветки
        settings_callback_handler(update, context)

    # ------------------------------------------------
    # НАСТРОЙКИ БЭКАПОВ (settings_handlers)
    # ------------------------------------------------
    elif data in BACKUP_SETTINGS_CALLBACKS:
        settings_callback_handler(update, context)

    # ------------------------------------------------
    # РЕСУРСЫ: группы/списки (TargetedChecks)
    # ------------------------------------------------
    elif data.startswith('server_group_'):
        # формат: server_group_<type>_<action>
        # пример: server_group_ssh_check_resources
        parts = data.split('_', 3)
        # parts = ['server', 'group', '<type>', '<action>']
        if len(parts) == 4:
            server_type = parts[2]
            action = parts[3]
            query.edit_message_text(
                f"📋 *Выберите сервер:*",
                parse_mode='Markdown',
                reply_markup=targeted_checks.create_server_group_menu(server_type, action)
            )
        else:
            query.edit_message_text("❌ Некорректные данные меню группы серверов")

    # (по желанию) QUICK SEARCH / REFRESH можно просто гасить
    elif data.startswith(('quick_search_', 'refresh_')):
        query.answer("Функция отключена", show_alert=False)

    # ------------------------------------------------
    # БЭКАПЫ
    # ------------------------------------------------
    elif data == "backup_main":
        debug_log("🧪 BACKUP MAIN: explicit branch hit")
        if not extension_manager.is_extension_enabled("backup_monitor"):
            query.edit_message_text("💾 Модуль бэкапов отключён")
            return

        from extensions.backup_monitor.bot_handler import backup_callback
        backup_callback(update, context)
        return

    elif data and data.startswith('backup_'):
        query = update.callback_query  # локально фиксируем, чтобы точно был в области видимости
        debug_log(f"➡️ BACKUP ROUTE: entering branch, data={data}")

        if not query:
            debug_log("❌ BACKUP ROUTE: callback_query is None")
            return

        # Можно ответить здесь, чтобы Telegram не ругался на долгий обработчик
        try:
            query.answer()
        except Exception:
            pass

        if not extension_manager.is_extension_enabled('backup_monitor'):
            debug_log("⛔ BACKUP ROUTE: backup_monitor extension is disabled")
            query.edit_message_text("💾 Модуль бэкапов отключён")
            return

        try:
            debug_log("📦 BACKUP ROUTE: importing backup_callback...")
            from extensions.backup_monitor.bot_handler import backup_callback
            debug_log("✅ BACKUP ROUTE: import OK, calling backup_callback()")

            backup_callback(update, context)

            debug_log("✅ BACKUP ROUTE: backup_callback() returned successfully")
            return

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            debug_log(f"💥 BACKUP ROUTE: exception: {e}\n{tb}")

            # Пытаемся показать ошибку пользователю
            try:
                query.edit_message_text("❌ Ошибка в модуле бэкапов. Подробности в логах.")
            except Exception:
                try:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ Ошибка в модуле бэкапов. Подробности в логах."
                    )
                except Exception:
                    debug_log("💥 BACKUP ROUTE: failed to notify user about error")
            return

    # ------------------------------------------------
    # РАСШИРЕНИЯ
    # ------------------------------------------------
    elif data == 'extensions_menu':
        show_extensions_menu(update, context)

    elif data.startswith('ext_'):
        extensions_callback_handler(update, context)

    # ------------------------------------------------
    # Закрытие
    # ------------------------------------------------
    elif data == 'close':
        query.delete_message()
