"""
/extensions/backup_monitor/bot_handler.py
Server Monitoring System v8.38.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring Proxmox backups
Система мониторинга серверов
Версия: 8.38.3
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг бэкапов Proxmox
"""

import sys
import ast
import json
from datetime import datetime, timedelta
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
import traceback
from .settings_backup_monitor import BASE_DIR, DATA_DIR
from config.settings import BOT_DEBUG_LOG_FILE
from lib.logging import debug_log, setup_logging
from extensions.backup_monitor.backup_handlers import (
    show_main_menu,
    show_proxmox_menu,
    show_today_status,
    show_recent_backups,
    show_failed_backups,
    show_hosts_menu,
    show_host_status,
    show_stale_hosts,
    show_database_backups_menu,
    show_database_backups_summary,
    show_database_details,
    show_stale_databases,
    show_mail_backups,
    show_stock_loads,
)
from extensions.extension_manager import extension_manager

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
logger = setup_logging("backup_monitor_bot", level="DEBUG", log_file=BOT_DEBUG_LOG_FILE)

# Импортируем наши утилиты и обработчики
try:
    from .backup_utils import BackupBase, StatusCalculator, DisplayFormatters
    from .backup_handlers import (
        create_main_menu, create_navigation_buttons,
        show_main_menu, show_today_status, show_recent_backups, show_failed_backups,
        show_hosts_menu, show_stale_hosts, show_host_status,
        show_database_backups_menu, show_stale_databases,
        show_database_backups_summary, show_database_details,
        show_stock_loads,
        format_database_details
    )
    logger.info("✅ Модули backup_utils и backup_handlers успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта модулей: {e}")
    # Альтернативный импорт для случаев, когда относительные импорты не работают
    try:
        import sys
        sys.path.append(str(Path(BASE_DIR) / 'extensions' / 'backup_monitor'))
        from .backup_utils import BackupBase, StatusCalculator, DisplayFormatters
        from .backup_handlers import (
            create_main_menu, create_navigation_buttons,
            show_main_menu, show_today_status, show_recent_backups, show_failed_backups,
            show_hosts_menu, show_stale_hosts, show_host_status,
            show_database_backups_menu, show_stale_databases,
            show_database_backups_summary, show_database_details,
            show_stock_loads,
            format_database_details
        )
        logger.info("✅ Модули импортированы через абсолютный путь")
    except ImportError as e2:
        logger.error(f"❌ Критическая ошибка импорта: {e2}")
        raise

class BackupMonitorBot(BackupBase):
    """Оптимизированный класс для мониторинга бэкапов"""
    
    def __init__(self):
        from .db_settings_backup_monitor import BACKUP_DATABASE_CONFIG
        super().__init__(BACKUP_DATABASE_CONFIG['backups_db'])
        self.status_calc = StatusCalculator()
        self.formatters = DisplayFormatters()
        self.backup_alert_hours, self.backup_stale_hours = self._get_backup_thresholds()

    @staticmethod
    def _get_backup_thresholds():
        """Получает пороги свежести бэкапов из настроек."""
        default_alert = 24
        default_stale = 36
        try:
            from core.config_manager import config_manager

            alert_hours = config_manager.get_setting("BACKUP_ALERT_HOURS", default_alert)
            stale_hours = config_manager.get_setting("BACKUP_STALE_HOURS", default_stale)
        except Exception:
            alert_hours = default_alert
            stale_hours = default_stale

        try:
            alert_hours = int(alert_hours)
        except (TypeError, ValueError):
            alert_hours = default_alert

        try:
            stale_hours = int(stale_hours)
        except (TypeError, ValueError):
            stale_hours = default_stale

        if stale_hours <= alert_hours:
            stale_hours = alert_hours + 1

        return alert_hours, stale_hours

    # === БАЗОВЫЕ МЕТОДЫ ===
    
    def get_database_display_names(self) -> dict:
        """
        Возвращает отображаемые имена БД (ключ -> display name),
        берём из SETTINGS.DB: settings.key='DATABASE_CONFIG'
        Формат DATABASE_CONFIG: {category: {db_key: db_display_name, ...}, ...}
        """
        try:
            import json
            import sqlite3

            db_path = Path(DATA_DIR) / "settings.db"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key='DATABASE_CONFIG' LIMIT 1")
            row = cur.fetchone()
            conn.close()

            if not row or not row[0]:
                return {}

            raw = row[0]
            cfg = json.loads(raw) if isinstance(raw, str) else (raw or {})
            if not isinstance(cfg, dict):
                return {}

            # Собираем в плоский словарь: db_key -> display_name
            names = {}
            for _category, db_map in cfg.items():
                if not isinstance(db_map, dict):
                    continue
                for db_key, display_name in db_map.items():
                    # display_name может быть None/"" — подстрахуемся
                    names[str(db_key)] = str(display_name) if display_name else str(db_key)

            return names

        except Exception as e:
            logger.exception(f"get_database_display_names: failed: {e}")
            return {}

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
        db_hosts = [row[0] for row in results]

        proxmox_hosts = self._get_proxmox_hosts_runtime()
        if not isinstance(proxmox_hosts, dict):
            return db_hosts

        enabled_hosts = {
            host for host, value in proxmox_hosts.items()
            if not isinstance(value, dict) or value.get("enabled", True)
        }

        filtered_hosts = [host for host in db_hosts if host in enabled_hosts]
        return filtered_hosts or list(enabled_hosts)

    @staticmethod
    def _normalize_proxmox_hosts(raw_hosts) -> dict:
        if isinstance(raw_hosts, dict):
            return raw_hosts
        if isinstance(raw_hosts, str):
            try:
                parsed_hosts = json.loads(raw_hosts)
            except Exception:
                try:
                    parsed_hosts = ast.literal_eval(raw_hosts)
                except Exception:
                    parsed_hosts = {}
            return parsed_hosts if isinstance(parsed_hosts, dict) else {}
        return {}

    @classmethod
    def _get_proxmox_hosts_runtime(cls) -> dict:
        try:
            from core.config_manager import config_manager
            proxmox_hosts = cls._normalize_proxmox_hosts(
                config_manager.get_setting('PROXMOX_HOSTS', {}, use_cache=False)
            )
            if proxmox_hosts:
                return proxmox_hosts
        except Exception:
            pass

        try:
            from .db_settings_backup_monitor import PROXMOX_HOSTS
        except Exception:
            PROXMOX_HOSTS = {}

        return cls._normalize_proxmox_hosts(PROXMOX_HOSTS)

    def get_host_recent_status(self, host_name, hours=48):
        """Получает статус хоста за указанный период"""
        query = '''
            SELECT backup_status, received_at
            FROM proxmox_backups
            WHERE host_name = ?
        '''
        params = [host_name]
        if hours is not None:
            since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            query += " AND received_at >= ?"
            params.append(since_time)
        query += " ORDER BY received_at DESC"
        return self.execute_query(query, tuple(params))

    def get_host_display_status(self, host_name):
        """Определяет отображаемый статус хоста"""
        recent_backups = self.get_host_recent_status(host_name, None)
        return self.status_calc.calculate_host_status(
            recent_backups,
            alert_hours=self.backup_alert_hours,
            stale_hours=self.backup_stale_hours,
        )

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

    # === МЕТОДЫ ДЛЯ ПОЧТОВЫХ БЭКАПОВ ===

    def get_mail_backups(self, hours=72, limit=10):
        """Получает последние бэкапы почтового сервера"""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            SELECT backup_status, total_size, backup_path, received_at
            FROM mail_server_backups
            WHERE received_at >= ?
            ORDER BY received_at DESC
            LIMIT ?
        '''
        try:
            return self.execute_query(query, (since_time, limit))
        except Exception as exc:
            logger.error(f"Ошибка получения почтовых бэкапов: {exc}")
            return []

    # === МЕТОДЫ ДЛЯ ЗАГРУЗКИ ОСТАТКОВ ===

    def get_stock_loads(self, hours=24):
        """Получает последние результаты загрузки остатков товаров по каждому поставщику."""
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        query = '''
            WITH normalized AS (
                SELECT
                    id,
                    COALESCE(source_name, 'Основное предприятие') AS source_name,
                    CASE
                        WHEN supplier_name IS NULL OR supplier_name = 'неизвестно'
                            THEN COALESCE(source_name, 'Основное предприятие')
                        ELSE supplier_name
                    END AS supplier_name,
                    status,
                    rows_count,
                    error_sample,
                    received_at
                FROM stock_load_results
                WHERE received_at >= ?
            ),
            ranked AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY source_name, supplier_name
                        ORDER BY received_at DESC, id DESC
                    ) AS row_num
                FROM normalized
            )
            SELECT source_name, supplier_name, status, rows_count, error_sample, received_at
            FROM ranked
            WHERE row_num = 1
            ORDER BY source_name, supplier_name
        '''
        try:
            return self.execute_query(query, (since_time,))
        except Exception as exc:
            logger.error(f"Ошибка получения остатков: {exc}")
            return []

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
        from .db_settings_backup_monitor import PROXMOX_HOSTS, DATABASE_BACKUP_CONFIG
        
        all_configured_hosts = [
            host for host, value in PROXMOX_HOSTS.items()
            if not isinstance(value, dict) or value.get("enabled", True)
        ]
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
            "• 📬 Бэкапы почты - Бэкапы почтового сервера\n"
            "• 📦 Остатки 1С - Результаты загрузки остатков\n"
            "• 🔄 Обновить - Обновить данные\n\n"
            "*Данные обновляются автоматически при получении писем от Proxmox/почтового сервера*"
        )

        update.message.reply_text(help_text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка в backup_help_command: {e}")
        update.message.reply_text("❌ Ошибка при выполнении команды")

# === CALLBACK ОБРАБОТЧИКИ ===

def backup_callback(update, context):
    """Обработчик callback'ов для бэкапов"""
    query = update.callback_query
    data = query.data
    logger.info(
        f"🧩 backup_callback: START | file={__file__} | data={data}"
    )

    try:
        # ВАЖНО: все логи — внутри try
        debug_log(f"🧩 backup_callback: START | file={__file__} | data={data}")

        if not query:
            debug_log("❌ backup_callback: update.callback_query is None")
            return

        query.answer()

        data = query.data
        backup_bot = BackupMonitorBot()

        if data == 'no_action':
            return

        if data == 'backup_today':
            show_today_status(query, backup_bot)

        elif data == 'backup_24h':
            show_recent_backups(query, backup_bot)

        elif data == 'backup_failed':
            show_failed_backups(query, backup_bot)

        elif data == 'backup_hosts':
            if not extension_manager.is_extension_enabled('backup_monitor'):
                query.edit_message_text("🖥️ Мониторинг бэкапов Proxmox отключён")
                return
            show_hosts_menu(query, backup_bot)

        elif data == 'backup_refresh':
            show_main_menu(query, backup_bot)

        elif data == 'backup_databases':
            if not extension_manager.is_extension_enabled('database_backup_monitor'):
                query.edit_message_text("🗃️ Мониторинг бэкапов БД отключён")
                return
            logger.info("🧪 BACKUP DB: entering show_database_backups_menu")
            show_database_backups_menu(query, backup_bot)

        elif data == 'backup_mail':
            if not extension_manager.is_extension_enabled('mail_backup_monitor'):
                query.edit_message_text("📬 Мониторинг бэкапов почты отключён")
                return
            show_mail_backups(query, backup_bot)

        elif data == 'backup_stock_loads':
            if not extension_manager.is_extension_enabled('stock_load_monitor'):
                query.edit_message_text("📦 Мониторинг остатков 1С отключён")
                return
            show_stock_loads(query, backup_bot)

        elif data == 'backup_proxmox':
            show_proxmox_menu(query, backup_bot)

        elif data == 'backup_stale_hosts':
            show_stale_hosts(query, backup_bot)

        elif data.startswith('backup_host_'):
            host_name = data.replace('backup_host_', '')
            show_host_status(query, backup_bot, host_name)

        elif data == 'backup_main':
            show_main_menu(query, backup_bot)

        # --- DB handlers ---
        elif data.startswith('db_detail_'):
            remaining = data.replace('db_detail_', '')
            if '__' in remaining:
                backup_type, db_name = remaining.split('__', 1)
                logger.info("🧪 DB detail")
                show_database_details(query, backup_bot, backup_type, db_name)
            else:
                last_underscore = remaining.rfind('_')
                if last_underscore != -1:
                    backup_type = remaining[:last_underscore]
                    db_name = remaining[last_underscore + 1:]
                    show_database_details(query, backup_bot, backup_type, db_name)
                else:
                    query.edit_message_text("❌ Ошибка: неверный формат запроса")

        elif data == 'db_backups_24h':
            logger.info("🧪 db backups 24h")
            show_database_backups_summary(query, backup_bot, 24)

        elif data == 'db_backups_48h':
            logger.info("🧪 db backups 48h")
            show_database_backups_summary(query, backup_bot, 48)

        elif data in ('db_backups_today', 'db_backups_summary'):
            logger.info("🧪 db backups today")
            show_database_backups_summary(query, backup_bot, 24)

        elif data == 'db_backups_list':
            logger.info("🧪 db backups list")
            show_database_backups_menu(query, backup_bot)

        elif data == 'db_stale_list':
            logger.info("🧪 db state list")
            show_stale_databases(query, backup_bot)

        else:
            debug_log(f"⚠️ backup_callback: unknown callback data={data}")
            query.answer("Неизвестная команда", show_alert=True)

    except Exception as e:
        debug_log(f"💥 backup_callback ERROR: {e}\n{traceback.format_exc()}")
        try:
            query.edit_message_text("❌ Ошибка в модуле бэкапов. Подробности в логах.")
        except Exception:
            try:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Ошибка в модуле бэкапов (не удалось обновить меню). Подробности в логах."
                )
            except Exception:
                pass

def get_database_config(self):
    """Получает полную конфигурацию баз данных"""
    from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG
    
    return {
        "company_databases": DATABASE_BACKUP_CONFIG.get("company_databases", {}),
        "barnaul_backups": DATABASE_BACKUP_CONFIG.get("barnaul_backups", {}),
        "client_databases": DATABASE_BACKUP_CONFIG.get("client_databases", {}),
        "yandex_backups": DATABASE_BACKUP_CONFIG.get("yandex_backups", {})
    }

def get_database_config_for_report(self):
    """Получает конфигурацию баз данных для отчета"""
    from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG
    
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
