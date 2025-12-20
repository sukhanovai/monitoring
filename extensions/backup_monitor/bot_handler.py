"""
/extensions/backup_monitor/bot_handler.py
Server Monitoring System v4.14.27
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring Proxmox backups
Система мониторинга серверов
Версия: 4.14.27
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг бэкапов Proxmox
"""

import logging
import sys
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler

from telegram.ext import CommandHandler, CallbackQueryHandler
from lib.logging import debug_log

def register_handlers(dispatcher):
    """
    Регистрирует handlers расширения backup_monitor.
    Если команды уже где-то регистрируются — можно оставить пустым.
    """
    try:
        # если у расширения есть команды вида /backup
        # dispatcher.add_handler(CommandHandler("backup", backup_command))
        # dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
        # dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))

        # Если хочешь, чтобы расширение само ловило свои callback_data:
        # dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern=r"^backup_"))

        debug_log("✅ backup_monitor: handlers зарегистрированы")
    except Exception as e:
        debug_log(f"❌ backup_monitor: ошибка регистрации handlers: {e}")

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/monitoring/bot_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Импортируем наши утилиты и обработчики
try:
    from .backup_utils import BackupBase, StatusCalculator, DisplayFormatters
    from .backup_handlers import (
        create_main_menu, create_navigation_buttons,
        show_main_menu, show_today_status, show_recent_backups, show_failed_backups,
        show_hosts_menu, show_stale_hosts, show_host_status,
        show_database_backups_menu, show_stale_databases,
        show_database_backups_summary, show_database_details,
        format_database_details
    )
    logger.info("✅ Модули backup_utils и backup_handlers успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта модулей: {e}")
    # Альтернативный импорт для случаев, когда относительные импорты не работают
    try:
        import os
        import sys
        sys.path.append('/opt/monitoring/extensions/backup_monitor')
        from .backup_utils import BackupBase, StatusCalculator, DisplayFormatters
        from .backup_handlers import (
            create_main_menu, create_navigation_buttons,
            show_main_menu, show_today_status, show_recent_backups, show_failed_backups,
            show_hosts_menu, show_stale_hosts, show_host_status,
            show_database_backups_menu, show_stale_databases,
            show_database_backups_summary, show_database_details,
            format_database_details
        )
        logger.info("✅ Модули импортированы через абсолютный путь")
    except ImportError as e2:
        logger.error(f"❌ Критическая ошибка импорта: {e2}")
        raise

class BackupMonitorBot(BackupBase):
    """Оптимизированный класс для мониторинга бэкапов"""
    
    def __init__(self):
        from config.settings import BACKUP_DATABASE_CONFIG
        super().__init__(BACKUP_DATABASE_CONFIG['backups_db'])
        self.status_calc = StatusCalculator()
        self.formatters = DisplayFormatters()

    # === БАЗОВЫЕ МЕТОДЫ ===
    
    def get_database_display_names(self):
        """Получает отображаемые имена баз данных из конфигурации"""
        from config.settings import DATABASE_BACKUP_CONFIG
        
        display_names = {}
        
        # Объединяем все базы из конфигурации
        config_sections = [
            DATABASE_BACKUP_CONFIG["company_databases"],
            DATABASE_BACKUP_CONFIG["barnaul_backups"], 
            DATABASE_BACKUP_CONFIG["client_databases"],
            DATABASE_BACKUP_CONFIG["yandex_backups"]
        ]
        
        for section in config_sections:
            display_names.update(section)
        
        return display_names

    # === МЕТОДЫ ДЛЯ ХОСТОВ ===
    
    def get_today_status(self):
        """Статус бэкапов за сегодня"""
        today = datetime.now().strftime('%Y-%m-%d')
        query = '''
            SELECT host_name, backup_status, COUNT(*) as report_count, MAX(received_at) as last_report
            FROM proxmox_backups
            WHERE date(received_at) = ?
            GROUP BY host_name, backup_status
            ORDER BY host_name, last_report DESC
        '''
        return self.execute_query(query, (today,))

    def get_recent_backups(self, hours=24):
        """Последние бэкапы за указанный период"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT host_name, backup_status, duration, total_size, error_message, received_at
            FROM proxmox_backups
            WHERE received_at >= ?
            ORDER BY received_at DESC
            LIMIT 15
        '''
        return self.execute_query(query, (since_time,))

    def get_host_status(self, host_name):
        """Статус конкретного хоста"""
        query = '''
            SELECT backup_status, duration, total_size, error_message, received_at
            FROM proxmox_backups
            WHERE host_name = ?
            ORDER BY received_at DESC
            LIMIT 5
        '''
        return self.execute_query(query, (host_name,))

    def get_failed_backups(self, days=1):
        """Неудачные бэкапы за период"""
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '''
            SELECT host_name, backup_status, error_message, received_at
            FROM proxmox_backups
            WHERE backup_status = 'failed'
            AND date(received_at) >= ?
            ORDER BY received_at DESC
        '''
        return self.execute_query(query, (since_date,))

    def get_all_hosts(self):
        """Получает список всех хостов из базы"""
        query = 'SELECT DISTINCT host_name FROM proxmox_backups ORDER BY host_name'
        results = self.execute_query(query)
        return [row[0] for row in results]

    def get_host_recent_status(self, host_name, hours=48):
        """Получает статус хоста за указанный период"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, received_at
            FROM proxmox_backups
            WHERE host_name = ? AND received_at >= ?
            ORDER BY received_at DESC
        '''
        return self.execute_query(query, (host_name, since_time))

    def get_host_display_status(self, host_name):
        """Определяет отображаемый статус хоста"""
        recent_backups = self.get_host_recent_status(host_name, 48)
        return self.status_calc.calculate_host_status(recent_backups)

    # === МЕТОДЫ ДЛЯ БАЗ ДАННЫХ ===
    
    def get_database_backups_stats(self, hours=24):
        """Получает статистику по бэкапам баз данных"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_type, database_name, database_display_name, 
                   backup_status, COUNT(*) as backup_count, MAX(received_at) as last_backup
            FROM database_backups 
            WHERE received_at >= ?
            GROUP BY backup_type, database_name, database_display_name, backup_status
            ORDER BY backup_type, database_name, last_backup DESC
        '''
        return self.execute_query(query, (since_time,))

    def get_database_backups_stats_fixed(self, hours=24):
        """Исправленная версия получения статистики"""
        return self.get_database_backups_stats(hours)

    def get_database_details(self, backup_type, db_name, hours=168):
        """Получает детальную информацию по конкретной базе данных"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, task_type, error_count, email_subject, received_at
            FROM database_backups 
            WHERE backup_type = ? AND database_name = ? AND received_at >= ?
            ORDER BY received_at DESC
            LIMIT 10
        '''
        return self.execute_query(query, (backup_type, db_name, since_time))

    def get_database_recent_status(self, backup_type, db_name, hours=48):
        """Получает статус БД за указанный период"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, received_at, error_count
            FROM database_backups
            WHERE backup_type = ? AND database_name = ? AND received_at >= ?
            ORDER BY received_at DESC
        '''
        return self.execute_query(query, (backup_type, db_name, since_time))

    def get_database_display_status(self, backup_type, db_name):
        """Определяет отображаемый статус БД"""
        recent_backups = self.get_database_recent_status(backup_type, db_name, 48)
        return self.status_calc.calculate_db_status(recent_backups)

    # === МЕТОДЫ ДЛЯ ОТЧЕТОВ ===
    
    def get_stale_proxmox_backups(self, hours_threshold=24):
        """Получает хосты без свежих бэкапов"""
        threshold_time = (datetime.now() - timedelta(hours=hours_threshold)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT host_name, MAX(received_at) as last_backup
            FROM proxmox_backups 
            GROUP BY host_name
            HAVING last_backup < ?
            ORDER BY last_backup ASC
        '''
        return self.execute_query(query, (threshold_time,))

    def get_stale_database_backups(self, hours_threshold=24):
        """Получает БД без свежих бэкапов"""
        threshold_time = (datetime.now() - timedelta(hours=hours_threshold)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_type, database_name, database_display_name, MAX(received_at) as last_backup
            FROM database_backups 
            GROUP BY backup_type, database_name, database_display_name
            HAVING last_backup < ?
            ORDER BY last_backup ASC
        '''
        return self.execute_query(query, (threshold_time,))

    def get_backup_coverage_report(self, hours_threshold=24):
        """Получает полный отчет о покрытии бэкапов"""
        stale_hosts = self.get_stale_proxmox_backups(hours_threshold)
        stale_databases = self.get_stale_database_backups(hours_threshold)
        
        # Получаем все известные хосты и БД из конфигурации
        from config.settings import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG
        
        all_configured_hosts = list(PROXMOX_HOSTS.keys())
        all_configured_databases = []
        
        # Собираем все БД из конфигурации
        config_mapping = [
            ('company_database', DATABASE_BACKUP_CONFIG["company_databases"]),
            ('barnaul', DATABASE_BACKUP_CONFIG["barnaul_backups"]),
            ('client', DATABASE_BACKUP_CONFIG["client_databases"]), 
            ('yandex', DATABASE_BACKUP_CONFIG["yandex_backups"])
        ]
        
        for backup_type, config_dict in config_mapping:
            for db_key in config_dict.keys():
                all_configured_databases.append((backup_type, db_key))
        
        return {
            'stale_hosts': stale_hosts,
            'stale_databases': stale_databases,
            'all_configured_hosts': all_configured_hosts,
            'all_configured_databases': all_configured_databases,
            'hours_threshold': hours_threshold
        }

# === КОМАНДЫ БОТА ===

def backup_command(update, context):
    """Обработчик команды /backup"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text(
                "❌ Функционал мониторинга бэкапов отключен. "
                "Включите расширение '📊 Мониторинг бэкапов Proxmox' в разделе управления расширениями."
            )
            return

        update.message.reply_text(
            "💾 *Мониторинг бэкапов Proxmox*\n\nВыберите опцию:",
            parse_mode='Markdown',
            reply_markup=create_main_menu()
        )

    except Exception as e:
        logger.error(f"Ошибка в backup_command: {e}")
        update.message.reply_text("❌ Ошибка при выполнении команды")

def backup_search_command(update, context):
    """Обработчик команды /backup_search"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text("❌ Функционал мониторинга бэкапов отключен.")
            return

        update.message.reply_text("🔍 Поиск по бэкапам в разработке...")

    except Exception as e:
        logger.error(f"Ошибка в backup_search_command: {e}")
        update.message.reply_text("❌ Ошибка при выполнении команды")

def backup_help_command(update, context):
    """Обработчик команды /backup_help"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text("❌ Функционал мониторинга бэкапов отключен.")
            return

        help_text = (
            "💾 *Помощь по мониторингу бэкапов*\n\n"
            "*Команды:*\n"
            "• `/backup` - Главное меню бэкапов\n"
            "• `/backup_search` - Поиск по бэкапам\n"
            "• `/backup_help` - Эта справка\n\n"
            "*Опции в меню:*\n"
            "• 📊 Сегодня - Статус за сегодня\n"
            "• ⏰ 24 часа - Последние бэкапы\n"
            "• ❌ Ошибки - Неудачные бэкапы\n"
            "• 🖥️ По хостам - Статус по серверам\n"
            "• 🗃️ Бэкапы БД - Бэкапы баз данных\n"
            "• 🔄 Обновить - Обновить данные\n\n"
            "*Данные обновляются автоматически при получении писем от Proxmox*"
        )

        update.message.reply_text(help_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в backup_help_command: {e}")
        update.message.reply_text("❌ Ошибка при выполнении команды")

# === CALLBACK ОБРАБОТЧИКИ ===

def backup_callback(update, context):
    """Обработчик callback'ов для бэкапов"""
    try:
        query = update.callback_query
        query.answer()
        
        data = query.data
        backup_bot = BackupMonitorBot()

        if data == 'no_action':
            # Заглушка для заголовков секций - ничего не делаем
            return
            
        if data == 'backup_today':
            show_today_status(query, backup_bot)
        elif data == 'backup_24h':
            show_recent_backups(query, backup_bot)
        elif data == 'backup_failed':
            show_failed_backups(query, backup_bot)
        elif data == 'backup_hosts':
            show_hosts_menu(query, backup_bot)
        elif data == 'backup_refresh':
            show_main_menu(query, backup_bot)
        elif data == 'backup_databases':
            show_database_backups_menu(query, backup_bot)
        elif data == 'backup_proxmox':
            show_main_menu(query, backup_bot)
        elif data == 'backup_stale_hosts':
            show_stale_hosts(query, backup_bot)
        elif data.startswith('backup_host_'):
            host_name = data.replace('backup_host_', '')
            show_host_status(query, backup_bot, host_name)
        elif data == 'backup_main':
            show_main_menu(query, backup_bot)
            
        # Обработчики для баз данных
        elif data.startswith('db_detail_'):
            # Обработка деталей БД
            try:
                remaining = data.replace('db_detail_', '')
                if '__' in remaining:
                    parts = remaining.split('__', 1)
                    backup_type = parts[0]
                    db_name = parts[1]
                    show_database_details(query, backup_bot, backup_type, db_name)
                else:
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        backup_type = remaining[:last_underscore]
                        db_name = remaining[last_underscore + 1:]
                        show_database_details(query, backup_bot, backup_type, db_name)
                    else:
                        query.edit_message_text("❌ Ошибка: неверный формат запроса")
                    
            except Exception as e:
                logger.error(f"Ошибка при разборе db_detail: {e}")
                query.edit_message_text("❌ Ошибка при обработке запроса")
                
        elif data == 'db_backups_24h':
            show_database_backups_summary(query, backup_bot, 24)
        elif data == 'db_backups_48h':
            show_database_backups_summary(query, backup_bot, 48)
        elif data == 'db_backups_today':
            show_database_backups_summary(query, backup_bot, 24)
        elif data == 'db_backups_summary':
            show_database_backups_summary(query, backup_bot, 24)
        elif data == 'db_backups_list':
            show_database_backups_menu(query, backup_bot)
        elif data == 'db_stale_list':
            show_stale_databases(query, backup_bot)
        elif data == 'backup_main':
            show_main_menu(query, backup_bot)

    except Exception:
        logger.exception("Ошибка в backup_callback")
        try:
            query.edit_message_text("❌ Ошибка при обработке запроса")
        except Exception:
            # если edit_message_text не сработал (например, сообщение нельзя редактировать)
            try:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Ошибка при обработке запроса (не удалось обновить меню)."
                )
            except Exception:
                logger.exception("Не удалось отправить fallback-сообщение об ошибке")

def get_database_config(self):
    """Получает полную конфигурацию баз данных"""
    from config.settings import DATABASE_BACKUP_CONFIG
    
    return {
        "company_databases": DATABASE_BACKUP_CONFIG.get("company_databases", {}),
        "barnaul_backups": DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
        "client_databases": DATABASE_BACKUP_CONFIG.get("client_databases", {}),
        "yandex_backups": DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
    }

def get_database_config_for_report(self):
    """Получает конфигурацию баз данных для отчета"""
    from config.settings import DATABASE_BACKUP_CONFIG
    
    # Собираем все базы из конфигурации
    all_databases = {}
    all_databases.update(DATABASE_BACKUP_CONFIG.get("company_databases", {}))
    all_databases.update(DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}))
    all_databases.update(DATABASE_BACKUP_CONFIG.get("client_databases", {}))
    all_databases.update(DATABASE_BACKUP_CONFIG.get("yandex_backups", {}))
    
    return all_databases

# === НАСТРОЙКА ОБРАБОТЧИКОВ ===

def setup_backup_handlers(dispatcher):
    """Настраивает обработчики для бэкапов"""
    dispatcher.add_handler(CommandHandler("backup", backup_command))
    dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
    dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^backup_'))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^db_'))
