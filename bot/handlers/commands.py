"""
/bot/handlers/commands.py
Server Monitoring System v4.12.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Command handlers for Telegram bot
Система мониторинга серверов
Версия: 4.12.0
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики команд для Telegram бота
"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from lib.logging import debug_log
from bot.handlers.base import BaseHandlers
from modules.availability import availability_checker
from modules.resources import resources_checker
from modules.morning_report import morning_report

class CommandHandlers(BaseHandlers):
    """Обработчики команд бота"""
    
    def __init__(self, config_manager=None):
        super().__init__(config_manager)
    
    def check_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /check - проверка всех серверов"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        # Используем модуль availability для проверки
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        return menu_handlers.show_check_menu(update, context)
    
    def status_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /status - статус мониторинга"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        from core.monitor import monitor
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        return menu_handlers.show_monitor_status(update, context)
    
    def servers_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /servers - список серверов"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()
        
        message = "📋 *Список серверов в мониторинге*\n\n"
        
        # Группируем по типам
        by_type = {}
        for server in servers:
            server_type = server.get("type", "unknown")
            if server_type not in by_type:
                by_type[server_type] = []
            by_type[server_type].append(server)
        
        for server_type, servers_list in by_type.items():
            message += f"**{server_type.upper()} ({len(servers_list)}):**\n"
            for server in servers_list:
                status = "🟢" if server.get("enabled", True) else "🔴"
                message += f"{status} {server['name']} ({server['ip']})\n"
            message += "\n"
        
        update.message.reply_text(message, parse_mode='Markdown')
    
    def silent_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /silent - статус тихого режима"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        from config.settings import SILENT_START, SILENT_END
        from core.monitor import monitor
        
        silent_status = "🟢 активен" if monitor.is_silent_time() else "🔴 неактивен"
        message = (
            f"🔇 *Статус тихого режима:* {silent_status}\n\n"
            f"⏰ *Время работы:* {SILENT_START}:00 - {SILENT_END}:00\n\n"
            f"💡 *В тихом режиме:*\n"
            f"• Регулярные уведомления не отправляются\n"
            f"• Критические ошибки все равно отправляются\n"
            f"• Ручные проверки работают нормально\n"
            f"• Утренние отчеты отправляются принудительно"
        )
        
        update.message.reply_text(message, parse_mode='Markdown')
    
    def report_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /report - принудительная отправка отчета"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        # Используем модуль morning_report
        report_text = morning_report.generate_report(manual_call=True)
        
        # Отправляем через алерты
        from lib.alerts import send_alert
        send_alert(report_text, force=True)
        
        update.message.reply_text("📊 Отчет отправлен (данные актуальны на момент запроса)")
    
    def stats_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /stats - статистика работы"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        try:
            import json
            import os
            from datetime import datetime
            
            stats_file = "/opt/monitoring/data/monitoring_stats.json"
            
            if not os.path.exists(stats_file):
                update.message.reply_text("📊 Статистика еще не собрана")
                return
            
            with open(stats_file, 'r') as f:
                stats_data = json.load(f)
            
            message = "📊 *Статистика работы мониторинга*\n\n"
            
            # Общая статистика
            if 'overall' in stats_data:
                overall = stats_data['overall']
                message += f"**Общая статистика:**\n"
                message += f"• Запусков: {overall.get('total_runs', 0)}\n"
                message += f"• Успешных проверок: {overall.get('successful_checks', 0)}\n"
                message += f"• Обнаружено проблем: {overall.get('problems_detected', 0)}\n"
                message += f"• Отправлено уведомлений: {overall.get('alerts_sent', 0)}\n\n"
            
            # Ежедневная статистика
            if 'daily' in stats_data and stats_data['daily']:
                today = datetime.now().strftime('%Y-%m-%d')
                if today in stats_data['daily']:
                    daily = stats_data['daily'][today]
                    message += f"**Сегодня ({today}):**\n"
                    message += f"• Проверок: {daily.get('checks', 0)}\n"
                    message += f"• Проблемных серверов: {daily.get('problem_servers', 0)}\n"
                    message += f"• Уведомлений: {daily.get('alerts', 0)}\n"
                    message += f"• Ресурсных проверок: {daily.get('resource_checks', 0)}\n\n"
            
            # Самые проблемные серверы
            if 'problem_servers' in stats_data and stats_data['problem_servers']:
                message += "**Частые проблемы:**\n"
                for server, count in list(stats_data['problem_servers'].items())[:5]:
                    message += f"• {server}: {count} проблем\n"
            
            update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            debug_log(f"Ошибка получения статистики: {e}")
            update.message.reply_text("❌ Ошибка при получении статистики")
    
    def diagnose_ssh_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /diagnose_ssh - диагностика SSH"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        if not context.args:
            update.message.reply_text("❌ Укажите IP сервера: /diagnose_ssh <ip>")
            return
        
        ip = context.args[0]
        
        from core.checker import ServerChecker
        checker = ServerChecker()
        
        message = f"🔧 *Диагностика SSH подключения к {ip}*\n\n"
        
        # Проверяем ping
        ping_ok = checker.check_ping(ip)
        message += f"• Ping: {'🟢 OK' if ping_ok else '🔴 FAIL'}\n"
        
        # Проверяем порт 22
        port_ok = checker.check_port(ip, 22)
        message += f"• SSH порт (22): {'🟢 OK' if port_ok else '🔴 FAIL'}\n\n"
        
        if ping_ok and port_ok:
            message += "🔍 *Проверяем SSH подключение...*\n"
            
            # Пробуем подключиться
            ssh_ok = checker.check_ssh_universal(ip)
            message += f"• SSH подключение: {'🟢 OK' if ssh_ok else '🔴 FAIL'}\n"
            
            if ssh_ok:
                message += "\n✅ *SSH подключение работает корректно*"
            else:
                message += "\n❌ *SSH подключение не работает*\n"
                message += "*Возможные причины:*\n"
                message += "• Неправильные учетные данные\n"
                message += "• SSH ключ не настроен\n"
                message += "• Ограничения в firewall\n"
        else:
            message += "❌ *Сервер недоступен для базовых проверок*\n"
            message += "Проверьте доступность сервера в сети."
        
        update.message.reply_text(message, parse_mode='Markdown')
    
    def debug_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /debug - управление отладкой"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для использования этого бота")
            return
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        return menu_handlers.show_debug_menu(update, context)
    
    def extensions_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /extensions - управление расширениями"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для использования этого бота")
            return
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        return menu_handlers.show_extensions_menu(update, context)
    
    def get_command_handlers(self):
        """Возвращает список обработчиков команд"""
        return [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("check", self.check_command),
            CommandHandler("status", self.status_command),
            CommandHandler("servers", self.servers_command),
            CommandHandler("silent", self.silent_command),
            CommandHandler("report", self.report_command),
            CommandHandler("stats", self.stats_command),
            CommandHandler("diagnose_ssh", self.diagnose_ssh_command),
            CommandHandler("debug", self.debug_command),
            CommandHandler("extensions", self.extensions_command),
            CommandHandler("control", lambda u,c: self.control_command(u,c)),
        ]
    
    def control_command(self, update: Update, context: CallbackContext):
        """Обработчик команды /control - управление мониторингом"""
        if not self.check_access(update.effective_chat.id):
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
            return
        
        from bot.menu.handlers import MenuHandlers
        menu_handlers = MenuHandlers(self.config_manager)
        return menu_handlers.show_control_panel(update, context)