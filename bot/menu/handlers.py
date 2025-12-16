"""
/bot/menu/handlers.py
Server Monitoring System v4.12.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu handlers for Telegram bot
Система мониторинга серверов
Версия: 4.12.0
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики меню для Telegram бота
"""

import time
import threading
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lib.logging import debug_log
from lib.utils import progress_bar, format_duration
from lib.alerts import send_alert
from bot.menu.builder import MenuBuilder
from bot.handlers.base import BaseHandlers
from core.monitor import monitor
from modules.availability import availability_checker
from modules.resources import resources_checker
from modules.morning_report import morning_report

class MenuHandlers(BaseHandlers):
    """Обработчики меню бота"""
    
    def __init__(self, config_manager=None):
        super().__init__(config_manager)
        self.menu_builder = MenuBuilder(config_manager)
    
    def show_main_menu(self, update: Update, context: CallbackContext):
        """Показывает главное меню"""
        welcome_text = (
            "🤖 *Серверный мониторинг*\n\n"
            "✅ Система работает\n\n"
        )
        
        # Информация о отладке
        try:
            from config.settings import DEBUG_MODE
            welcome_text += f"🐛 *Режим отладки:* {'🟢 ВКЛ' if DEBUG_MODE else '🔴 ВЫКЛ'}\n"
        except ImportError:
            welcome_text += "🐛 *Режим отладки:* 🔴 Недоступен\n"
        
        # Информация о веб-интерфейсе
        try:
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('web_interface'):
                welcome_text += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
                welcome_text += "_*доступен только в локальной сети_\n"
            else:
                welcome_text += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
        except ImportError:
            welcome_text += "🌐 *Веб-интерфейс:* 🔴 модуль не загружен\n"
        
        keyboard = self.menu_builder.build_main_menu(update, context)
        
        if hasattr(update, 'callback_query'):
            update.callback_query.edit_message_text(
                welcome_text, 
                parse_mode='Markdown', 
                reply_markup=keyboard
            )
        else:
            update.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    def show_check_menu(self, update: Update, context: CallbackContext):
        """Показывает меню проверки"""
        query = update.callback_query
        if query:
            query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        keyboard = self.menu_builder.build_check_menu()
        message = "🔍 *Выберите тип проверки:*"
        
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            update.message.reply_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    def show_resources_menu(self, update: Update, context: CallbackContext):
        """Показывает меню проверки ресурсов"""
        query = update.callback_query
        if query:
            query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        keyboard = self.menu_builder.build_resources_menu()
        message = "🔍 *Выберите что проверить:*"
        
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            update.message.reply_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    def perform_manual_check(self, update: Update, context: CallbackContext):
        """Выполняет ручную проверку серверов"""
        query = update.callback_query
        if query:
            query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._perform_check_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _perform_check_thread(self, context, chat_id, progress_message_id):
        """Поток для выполнения проверки"""
        def update_progress(progress, status):
            progress_text = f"🔍 Проверяю серверы...\n{progress_bar(progress)}\n\n{status}"
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=progress_text
            )
        
        try:
            update_progress(10, "⏳ Получаем список серверов...")
            
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            total_servers = len(servers)
            results = {"failed": [], "ok": []}
            
            update_progress(20, f"⏳ Начинаем проверку {total_servers} серверов...")
            
            for i, server in enumerate(servers):
                current_progress = 20 + (i / total_servers * 70)
                server_info = f"{server['name']} ({server['ip']})"
                update_progress(current_progress, f"🔍 Проверяю {server_info}...")
                
                try:
                    # Используем модуль availability для проверки
                    is_up = availability_checker.check_single_server(server)
                    
                    if is_up:
                        results["ok"].append(server)
                        debug_log(f"✅ {server['name']} ({server['ip']}) - доступен")
                    else:
                        results["failed"].append(server)
                        debug_log(f"❌ {server['name']} ({server['ip']}) - недоступен")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    debug_log(f"💥 Ошибка при проверке {server['ip']}: {e}")
                    results["failed"].append(server)
            
            update_progress(95, "⏳ Формируем результаты...")
            
            # Формируем сообщение с результатами
            if not results["failed"]:
                message = "✅ *Все серверы доступны!*\n"
            else:
                message = f"⚠️ *Проблемные серверы ({len(results['failed'])}):*\n\n"
                
                # Группируем по типу
                by_type = {}
                for server in results["failed"]:
                    server_type = server.get("type", "unknown")
                    if server_type not in by_type:
                        by_type[server_type] = []
                    by_type[server_type].append(server)
                
                for server_type, servers_list in by_type.items():
                    message += f"**{server_type.upper()} ({len(servers_list)}):**\n"
                    for s in servers_list:
                        message += f"• {s['name']} ({s['ip']})\n"
                    message += "\n"
            
            message += f"\n⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}"
            
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Проверить снова", callback_data='manual_check')],
                    [InlineKeyboardButton("🎛️ Главное меню", callback_data='main_menu'),
                     InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
            
        except Exception as e:
            error_msg = f"❌ Ошибка при проверке: {e}"
            debug_log(error_msg)
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=error_msg
            )
    
    def show_monitor_status(self, update: Update, context: CallbackContext):
        """Показывает статус мониторинга"""
        query = update.callback_query
        if query:
            query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
            if query:
                query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
            else:
                update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        try:
            # Получаем текущий статус из модуля availability
            current_status = availability_checker.get_current_status()
            up_count = len(current_status.get("up", []))
            down_count = len(current_status.get("down", []))
            total_servers = up_count + down_count
            
            status = "🟢 Активен" if monitor.monitoring_active else "🔴 Остановлен"
            
            # Определяем статус тихого режима
            silent_status_text = "🔇 Тихий режим" if monitor.is_silent_time() else "🔊 Обычный режим"
            if monitor.silent_override is not None:
                if monitor.silent_override:
                    silent_status_text += " (🔇 Принудительно)"
                else:
                    silent_status_text += " (🔊 Принудительно)"
            
            # Получаем конфигурацию
            from config.settings import CHECK_INTERVAL
            next_check = datetime.now() + time.timedelta(seconds=CHECK_INTERVAL)
            
            message = (
                f"📊 *Статус мониторинга*\n\n"
                f"**Состояние:** {status}\n"
                f"**Режим:** {silent_status_text}\n\n"
                f"⏰ Последняя проверка: {monitor.last_check_time.strftime('%H:%M:%S')}\n"
                f"⏳ Следующая проверка: {next_check.strftime('%H:%M:%S')}\n"
                f"🔢 Всего серверов: {total_servers}\n"
                f"🟢 Доступно: {up_count}\n"
                f"🔴 Недоступно: {down_count}\n"
                f"🔄 Интервал проверки: {CHECK_INTERVAL} сек\n\n"
            )
            
            # Информация о веб-интерфейсе
            try:
                from extensions.extension_manager import extension_manager
                if extension_manager.is_extension_enabled('web_interface'):
                    message += "🌐 *Веб-интерфейс:* http://192.168.20.2:5000\n"
                    message += "_*доступен только в локальной сети_\n"
                else:
                    message += "🌐 *Веб-интерфейс:* 🔴 отключен\n"
            except ImportError:
                message += "🌐 *Веб-интерфейс:* 🔴 модуль не загружен\n"
            
            if down_count > 0:
                message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"
                
                # Получаем список недоступных серверов
                down_servers = current_status.get("down", [])
                
                # Группируем по типу
                by_type = {}
                for server in down_servers:
                    server_type = server.get("type", "unknown")
                    if server_type not in by_type:
                        by_type[server_type] = []
                    by_type[server_type].append(server)
                
                for server_type, servers_list in by_type.items():
                    message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                    for i, s in enumerate(servers_list[:8]):  # Ограничиваем показ
                        message += f"• {s['name']} ({s['ip']})\n"
                    
                    if len(servers_list) > 8:
                        message += f"• ... и еще {len(servers_list) - 8} серверов\n"
            
            keyboard = self.menu_builder.build_monitor_status_menu()
            
            if query:
                query.edit_message_text(
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            else:
                update.message.reply_text(
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
        except Exception as e:
            debug_log(f"Ошибка в show_monitor_status: {e}")
            error_msg = "⚠️ Произошла ошибка при получении статуса"
            if query:
                query.edit_message_text(error_msg)
            else:
                update.message.reply_text(error_msg)
    
    def show_control_panel(self, update: Update, context: CallbackContext):
        """Показывает панель управления"""
        query = update.callback_query
        query.answer()
        
        status_text = "🟢 Мониторинг активен" if monitor.monitoring_active else "🔴 Мониторинг приостановлен"
        keyboard = self.menu_builder.build_control_panel_menu(monitor.monitoring_active)
        
        query.edit_message_text(
            f"🎛️ *Управление мониторинга*\n\n{status_text}",
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def toggle_monitoring(self, update: Update, context: CallbackContext):
        """Переключает состояние мониторинга"""
        query = update.callback_query
        query.answer()
        
        if monitor.monitoring_active:
            monitor.stop()
            status_text = "⏸️ Мониторинг приостановлен"
            send_alert("🔴 *Мониторинг приостановлен*\nРегулярные проверки серверов отключены.", force=True)
        else:
            monitor.resume()
            status_text = "▶️ Мониторинг возобновлен"
            send_alert("🟢 *Мониторинг возобновлен*\nРегулярные проверки серверов активированы.", force=True)
        
        # Возвращаемся в панель управления
        self.show_control_panel(update, context)
    
    def show_silent_menu(self, update: Update, context: CallbackContext):
        """Показывает меню тихого режима"""
        query = update.callback_query
        query.answer()
        
        # Определяем текущий режим
        if monitor.silent_override is None:
            mode_text = "🔄 Автоматический"
            mode_desc = "Работает по расписанию"
        elif monitor.silent_override:
            mode_text = "🔇 Принудительно тихий"
            mode_desc = "Все уведомления отключены"
        else:
            mode_text = "🔊 Принудительно громкий"
            mode_desc = "Все уведомления включены"
        
        # Правильно определяем статус
        current_status = "🔴 неактивен" if monitor.is_silent_time() else "🟢 активен"
        status_description = "тихий режим" if monitor.is_silent_time() else "громкий режим"
        
        from config.settings import SILENT_START, SILENT_END
        message = (
            f"🔇 *Управление тихим режимом*\n\n"
            f"**Текущий статус:** {current_status}\n"
            f"**Режим работы:** {mode_text}\n"
            f"*{mode_desc}*\n"
            f"**Фактически:** {status_description}\n\n"
            f"⏰ *Расписание тихого режима:* {SILENT_START}:00 - {SILENT_END}:00\n\n"
            f"💡 *Пояснение:*\n"
            f"- 🟢 активен = уведомления работают\n"
            f"- 🔴 неактивен = уведомления отключены\n"
            f"- 🔊 громкий режим = все уведомления включены\n"
            f"- 🔇 тихий режим = только критические уведомления"
        )
        
        keyboard = self.menu_builder.build_silent_menu(monitor.silent_override)
        
        query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def force_silent_mode(self, update: Update, context: CallbackContext):
        """Включает принудительный тихий режим"""
        query = update.callback_query
        query.answer()
        
        monitor.silent_override = True
        send_alert("🔇 *Принудительный тихий режим включен*\nВсе уведомления отключены до смены режима.", force=True)
        
        # Возвращаемся в управление тихим режимом
        self.show_silent_menu(update, context)
    
    def force_loud_mode(self, update: Update, context: CallbackContext):
        """Включает принудительный громкий режим"""
        query = update.callback_query
        query.answer()
        
        monitor.silent_override = False
        send_alert("🔊 *Принудительный громкий режим включен*\nВсе уведомления активны до смены режима.", force=True)
        
        # Возвращаемся в управление тихим режимом
        self.show_silent_menu(update, context)
    
    def auto_silent_mode(self, update: Update, context: CallbackContext):
        """Включает автоматический режим"""
        query = update.callback_query
        query.answer()
        
        monitor.silent_override = None
        current_status = "активен" if monitor.is_silent_time() else "неактивен"
        send_alert(f"🔄 *Автоматический режим включен*\nТихий режим сейчас {current_status}.", force=True)
        
        # Возвращаемся в управление тихим режимом
        self.show_silent_menu(update, context)
    
    def send_morning_report(self, update: Update, context: CallbackContext):
        """Отправляет утренний отчет"""
        query = update.callback_query
        if query:
            query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
            if query:
                query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
            else:
                update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        # Используем модуль morning_report
        report_text = morning_report.generate_report(manual_call=True)
        send_alert(report_text, force=True)
        
        response = "📊 Отчет отправлен (данные актуальны на момент запроса)"
        if query:
            query.edit_message_text(response)
        else:
            update.message.reply_text(response)
    
    def debug_morning_report(self, update: Update, context: CallbackContext):
        """Отладочная функция для проверки утреннего отчета"""
        query = update.callback_query
        query.answer()
        
        debug_log("🔧 Запущена отладочная функция утреннего отчета")
        
        # Получаем текущий статус из модуля availability
        current_status = availability_checker.get_current_status()
        
        message = f"🔧 *Отладочная информация утреннего отчета*\n\n"
        message += f"🟢 Доступно: {len(current_status.get('up', []))}\n"
        message += f"🔴 Недоступно: {len(current_status.get('down', []))}\n"
        message += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        # Проверяем данные для отчета
        report_data = morning_report.get_report_data()
        if report_data:
            message += f"📊 *Данные утреннего отчета:*\n"
            message += f"• Время сбора: {report_data.get('collection_time', 'неизвестно')}\n"
            message += f"• Доступно: {len(report_data.get('status', {}).get('up', []))}\n"
            message += f"• Недоступно: {len(report_data.get('status', {}).get('down', []))}\n"
        else:
            message += f"❌ *Данные утреннего отчета отсутствуют*\n"
        
        query.edit_message_text(message, parse_mode='Markdown')
    
    def check_linux_servers(self, update: Update, context: CallbackContext):
        """Проверяет Linux серверы"""
        query = update.callback_query
        if query:
            query.answer("🐧 Проверяем Linux серверы...")
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._check_linux_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _check_linux_thread(self, context, chat_id, progress_message_id):
        """Поток для проверки Linux серверов"""
        def update_progress(progress, status):
            progress_text = f"🐧 Проверка Linux серверов...\n{progress_bar(progress)}\n\n{status}"
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=progress_text
            )
        
        try:
            update_progress(10, "⏳ Получаем список серверов...")
            
            from extensions.server_checks import check_linux_servers
            results, total_servers = check_linux_servers(update_progress)
            
            message = f"🐧 **Проверка Linux серверов**\n\n"
            successful_checks = len([r for r in results if r["success"]])
            message += f"✅ Успешно: {successful_checks}/{total_servers}\n\n"
            
            for result in results:
                server = result["server"]
                resources = result["resources"]
                
                if resources:
                    message += f"🟢 {server['name']}: CPU {resources.get('cpu', 0)}%, RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%\n"
                else:
                    message += f"🔴 {server['name']}: недоступен\n"
            
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
    
    def check_windows_servers(self, update: Update, context: CallbackContext):
        """Проверяет Windows серверы"""
        query = update.callback_query
        if query:
            query.answer("🪟 Проверяем Windows серверы...")
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._check_windows_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _check_windows_thread(self, context, chat_id, progress_message_id):
        """Поток для проверки Windows серверов"""
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
            update_progress(10, "⏳ Получаем список серверов...")
            
            from extensions.server_checks import (
                check_windows_2025_servers,
                check_domain_windows_servers,
                check_admin_windows_servers,
                check_standard_windows_servers
            )
            
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
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_message_id,
                text=error_msg
            )
    
    def check_other_servers(self, update: Update, context: CallbackContext):
        """Проверяет другие серверы"""
        query = update.callback_query
        if query:
            query.answer("📡 Проверяем другие серверы...")
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._check_other_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _check_other_thread(self, context, chat_id, progress_message_id):
        """Поток для проверки других серверов"""
        try:
            from extensions.server_checks import initialize_servers
            servers = initialize_servers()
            ping_servers = [s for s in servers if s["type"] == "ping"]
            
            message = f"📡 **Проверка других серверов**\n\n"
            successful_checks = 0
            
            for server in ping_servers:
                # Используем модуль availability для проверки
                is_up = availability_checker.check_single_server(server)
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
    
    def check_cpu_resources(self, update: Update, context: CallbackContext):
        """Проверяет только CPU"""
        query = update.callback_query
        if query:
            query.answer("💻 Проверяем CPU...")
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._check_cpu_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _check_cpu_thread(self, context, chat_id, progress_message_id):
        """Поток для проверки CPU"""
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
                current_progress = 15 + (i / total_servers * 75)
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
            for result in windows_cpu[:10]:
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
            for result in linux_cpu[:10]:
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
    
    def check_ram_resources(self, update: Update, context: CallbackContext):
        """Проверяет только RAM"""
        query = update.callback_query
        if query:
            query.answer("🧠 Проверяем RAM...")
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._check_ram_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _check_ram_thread(self, context, chat_id, progress_message_id):
        """Поток для проверки RAM"""
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
                current_progress = 15 + (i / total_servers * 75)
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
            for result in windows_ram[:10]:
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
            for result in linux_ram[:10]:
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
    
    def check_disk_resources(self, update: Update, context: CallbackContext):
        """Проверяет только Disk"""
        query = update.callback_query
        if query:
            query.answer("💾 Проверяем Disk...")
            chat_id = query.message.chat_id
        else:
            chat_id = update.effective_chat.id
        
        if not self.check_access(chat_id):
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
            target=self._check_disk_thread,
            args=(context, chat_id, progress_message.message_id)
        )
        thread.start()
    
    def _check_disk_thread(self, context, chat_id, progress_message_id):
        """Поток для проверки Disk"""
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
                current_progress = 15 + (i / total_servers * 75)
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
            for result in windows_disk[:10]:
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
            for result in linux_disk[:10]:
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
    
    def show_debug_menu(self, update: Update, context: CallbackContext):
        """Показывает меню управления отладкой"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        chat_id = query.message.chat_id if query else update.message.chat_id
        
        # Получаем статус отладки
        try:
            from config.settings import DEBUG_MODE
            debug_status = "🟢 ВКЛЮЧЕНА" if DEBUG_MODE else "🔴 ВЫКЛЮЧЕНА"
        except ImportError:
            debug_status = "🔴 НЕДОСТУПНА"
        
        message = "🐛 *Управление отладкой*\n\n"
        message += f"*Текущий статус:* {debug_status}\n\n"
        
        keyboard = self.menu_builder.build_debug_menu()
        
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            update.message.reply_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    def enable_debug_mode(self, update: Update, context: CallbackContext):
        """Включает режим отладки"""
        query = update.callback_query
        query.answer()
        
        try:
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
    
    def disable_debug_mode(self, update: Update, context: CallbackContext):
        """Выключает режим отладки"""
        query = update.callback_query
        query.answer()
        
        try:
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
    
    def show_debug_status(self, update: Update, context: CallbackContext):
        """Показывает статус отладки и системную информацию"""
        query = update.callback_query
        query.answer()
        
        import os
        from datetime import datetime
        
        try:
            # Пытаемся импортировать psutil
            try:
                import psutil
                psutil_available = True
            except ImportError:
                psutil_available = False
            
            message = "📊 *Статус системы и отладки*\n\n"
            
            # Статус отладки
            try:
                from config.settings import DEBUG_MODE
                debug_status = "🟢 ВКЛ" if DEBUG_MODE else "🔴 ВЫКЛ"
            except ImportError:
                debug_status = "🔴 НЕДОСТУПЕН"
            
            message += f"🐛 *Режим отладки:* {debug_status}\n\n"
            
            # Системная информация
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
    
    def clear_debug_logs(self, update: Update, context: CallbackContext):
        """Очищает файлы логов"""
        query = update.callback_query
        query.answer()
        
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
    
    def run_diagnostic(self, update: Update, context: CallbackContext):
        """Запускает диагностику системы"""
        query = update.callback_query
        query.answer()
        
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
            
            # Экранируем сообщение для безопасного отображения в Markdown
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
    
    def show_advanced_debug(self, update: Update, context: CallbackContext):
        """Показывает расширенные настройки отладки"""
        query = update.callback_query
        query.answer()
        
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
            import os
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
    
    def show_extensions_menu(self, update: Update, context: CallbackContext):
        """Показывает меню управления расширениями"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        chat_id = query.message.chat_id if query else update.message.chat_id
        
        try:
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
            
            keyboard = self.menu_builder.build_extensions_menu(extensions_status)
            
            if query:
                query.edit_message_text(
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            else:
                update.message.reply_text(
                    text=message,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
        except ImportError as e:
            error_msg = "❌ Модуль управления расширениями недоступен"
            if query:
                query.edit_message_text(error_msg)
            else:
                update.message.reply_text(error_msg)
    
    def toggle_extension(self, update: Update, context: CallbackContext, extension_id: str):
        """Переключает расширение"""
        query = update.callback_query
        query.answer()
        
        try:
            from extensions.extension_manager import extension_manager
            success, message = extension_manager.toggle_extension(extension_id)
            
            if success:
                query.answer(message)
                self.show_extensions_menu(update, context)
            else:
                query.answer(message, show_alert=True)
                
        except ImportError as e:
            query.answer("❌ Модуль управления расширениями недоступен", show_alert=True)
    
    def enable_all_extensions(self, update: Update, context: CallbackContext):
        """Включает все расширения"""
        query = update.callback_query
        query.answer()
        
        try:
            from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS
            
            enabled_count = 0
            for ext_id in AVAILABLE_EXTENSIONS:
                success, _ = extension_manager.enable_extension(ext_id)
                if success:
                    enabled_count += 1
            
            query.answer(f"✅ Включено {enabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
            self.show_extensions_menu(update, context)
            
        except ImportError as e:
            query.answer("❌ Модуль управления расширениями недоступен", show_alert=True)
    
    def disable_all_extensions(self, update: Update, context: CallbackContext):
        """Отключает все расширения"""
        query = update.callback_query
        query.answer()
        
        try:
            from extensions.extension_manager import extension_manager, AVAILABLE_EXTENSIONS
            
            disabled_count = 0
            for ext_id in AVAILABLE_EXTENSIONS:
                success, _ = extension_manager.disable_extension(ext_id)
                if success:
                    disabled_count += 1
            
            query.answer(f"✅ Отключено {disabled_count}/{len(AVAILABLE_EXTENSIONS)} расширений")
            self.show_extensions_menu(update, context)
            
        except ImportError as e:
            query.answer("❌ Модуль управления расширениями недоступен", show_alert=True)