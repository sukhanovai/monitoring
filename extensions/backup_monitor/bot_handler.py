"""
Обработчик команд бота для мониторинга бэкапов Proxmox с кнопками
"""

import sqlite3
import logging
import sys
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования в файл
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/monitoring/bot_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BackupMonitorBot:
    def __init__(self):
        from config import BACKUP_DATABASE_CONFIG
        self.db_path = BACKUP_DATABASE_CONFIG['backups_db']

    def get_today_status(self):
        """Статус бэкапов за сегодня"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT
                host_name,
                backup_status,
                COUNT(*) as report_count,
                MAX(received_at) as last_report
            FROM proxmox_backups
            WHERE date(received_at) = ?
            GROUP BY host_name, backup_status
            ORDER BY host_name, last_report DESC
        ''', (today,))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_recent_backups(self, hours=24):
        """Последние бэкапы за указанный период"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            SELECT
                host_name,
                backup_status,
                duration,
                total_size,
                error_message,
                received_at
            FROM proxmox_backups
            WHERE received_at >= ?
            ORDER BY received_at DESC
            LIMIT 15
        ''', (since_time,))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_host_status(self, host_name):
        """Статус конкретного хоста"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                backup_status,
                duration,
                total_size,
                error_message,
                received_at
            FROM proxmox_backups
            WHERE host_name = ?
            ORDER BY received_at DESC
            LIMIT 5
        ''', (host_name,))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_failed_backups(self, days=1):
        """Неудачные бэкапы за период"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT
                host_name,
                backup_status,
                error_message,
                received_at
            FROM proxmox_backups
            WHERE backup_status = 'failed'
            AND date(received_at) >= ?
            ORDER BY received_at DESC
        ''', (since_date,))

        results = cursor.fetchall()
        conn.close()

        return results

    def get_all_hosts(self):
        """Получает список всех хостов из базы"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT host_name
            FROM proxmox_backups
            ORDER BY host_name
        ''')

        results = [row[0] for row in cursor.fetchall()]
        conn.close()

        return results
    
    def get_database_backups_stats(self, hours=24):
        """Получает статистику по бэкапам баз данных - СОВМЕСТИМАЯ ВЕРСИЯ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        # ВЕРСИЯ ДЛЯ СОВМЕСТИМОСТИ: возвращает 6 значений
        cursor.execute('''
            SELECT 
                backup_type,
                database_name,
                database_display_name,
                backup_status,
                COUNT(*) as backup_count,
                MAX(received_at) as last_backup
            FROM database_backups 
            WHERE received_at >= ?
            GROUP BY backup_type, database_name, database_display_name, backup_status
            ORDER BY backup_type, database_name, last_backup DESC
        ''', (since_time,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def get_database_backups_summary(self, hours=24):
        """Сводка по бэкапам баз данных"""
        stats = self.get_database_backups_stats(hours)
        
        if not stats:
            return {}
        
        summary = {}
        for backup_type, db_name, status, count, last_backup in stats:
            if backup_type not in summary:
                summary[backup_type] = {}
            if db_name not in summary[backup_type]:
                summary[backup_type][db_name] = {'success': 0, 'failed': 0, 'last_backup': last_backup}
            
            summary[backup_type][db_name][status] = count
        
        return summary

    def get_database_details(self, backup_type, db_name, hours=168):
        """Получает детальную информацию по конкретной базе данных - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            print(f"🔍 DEBUG: Получен запрос для {backup_type}.{db_name}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                SELECT 
                    backup_status,
                    task_type,
                    error_count,
                    email_subject,
                    received_at
                FROM database_backups 
                WHERE backup_type = ? 
                AND database_name = ? 
                AND received_at >= ?
                ORDER BY received_at DESC
                LIMIT 10
            ''', (backup_type, db_name, since_time))
            
            results = cursor.fetchall()
            conn.close()
            
            print(f"🔍 DEBUG: Получено {len(results)} записей")
            return results
            
        except Exception as e:
            print(f"❌ Ошибка в get_database_details: {e}")
            import traceback
            print(f"Подробности: {traceback.format_exc()}")
            return []

def format_database_details(backup_bot, backup_type, db_name, hours=168):
    """Детальная информация по конкретной базе данных - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        print(f"🔍 DEBUG: Получен запрос для {backup_type}.{db_name}")
        
        # Получаем детальные данные ИЗ КЛАССА
        details = backup_bot.get_database_details(backup_type, db_name, hours)
        
        print(f"🔍 DEBUG: Получено {len(details)} записей, структура: {details}")
        
        if not details:
            return f"📋 Детали по {db_name}\n\nНет данных за последние {hours} часов"
                
        type_names = {
            'company_database': '🏢 Основная БД',
            'barnaul': '🏔️ Барнаул', 
            'client': '👥 Клиентская',
            'yandex': '☁️ Yandex'
        }
        
        type_display = type_names.get(backup_type, f"📁 {backup_type}")
        
        message = f"📋 Детали по {db_name}\n"
        message += f"Тип: {type_display}\n"
        message += f"Период: {hours} часов\n\n"
        
        # Статистика
        success_count = len([d for d in details if d[0] == 'success'])
        failed_count = len([d for d in details if d[0] == 'failed'])
        total_count = len(details)
        
        message += f"📊 Статистика:\n"
        message += f"✅ Успешных: {success_count}\n"
        message += f"❌ Ошибок: {failed_count}\n"
        message += f"📈 Всего: {total_count}\n\n"
        
        # Последние бэкапы
        message += "⏰ Последние бэкапы:\n"
        
        for status, task_type, error_count, subject, received_at in details[:5]:
            status_icon = "✅" if status == 'success' else "❌"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"{status_icon} {time_str} - {status}"
            if error_count and error_count > 0:
                message += f" (ошибок: {error_count})"
            if task_type:
                message += f" - {task_type}"
            message += "\n"
        
        message += f"\n🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        return message
        
    except Exception as e:
        print(f"❌ Ошибка в format_database_details: {e}")
        import traceback
        print(f"Подробности: {traceback.format_exc()}")
        return f"❌ Ошибка при получении деталей БД: {e}"

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

        keyboard = [
            [InlineKeyboardButton("📊 Сегодня", callback_data='backup_today')],
            [InlineKeyboardButton("⏰ 24 часа", callback_data='backup_24h')],
            [InlineKeyboardButton("❌ Ошибки", callback_data='backup_failed')],
            [InlineKeyboardButton("🖥️ По хостам", callback_data='backup_hosts')],
            [InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')],
            [InlineKeyboardButton("🔄 Обновить", callback_data='backup_refresh')]
        ]

        update.message.reply_text(
            "💾 *Мониторинг бэкапов Proxmox*\n\nВыберите опцию:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка в backup_command: {e}")
        update.message.reply_text("❌ Ошибка при выполнении команды")

def backup_search_command(update, context):
    """Обработчик команды /backup_search"""
    try:
        from extensions.extension_manager import extension_manager
        if not extension_manager.is_extension_enabled('backup_monitor'):
            update.message.reply_text(
                "❌ Функционал мониторинга бэкапов отключен."
            )
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
            update.message.reply_text(
                "❌ Функционал мониторинга бэкапов отключен."
            )
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

def backup_callback(update, context):
    """Обработчик callback'ов для бэкапов"""
    try:
        query = update.callback_query
        query.answer()
        
        data = query.data
        backup_bot = BackupMonitorBot()

        if data == 'backup_today':
            show_today_status(query, backup_bot)
        elif data == 'backup_24h':
            show_recent_backups(query, backup_bot)
        elif data == 'backup_failed':
            show_failed_backups(query, backup_bot)
        elif data == 'backup_hosts':
            show_hosts_menu(query, backup_bot)
        elif data == 'backup_refresh':
            show_main_menu(query)
        elif data == 'backup_databases':
            show_database_backups_menu(query, backup_bot)
        elif data == 'backup_proxmox':
            show_main_menu(query)
        elif data.startswith('backup_host_'):
            host_name = data.replace('backup_host_', '')
            show_host_status(query, backup_bot, host_name)
        elif data.startswith('db_detail_'):
            # Обработка деталей БД
            parts = data.replace('db_detail_', '').split('_')
            if len(parts) >= 2:
                backup_type = parts[0]
                db_name = '_'.join(parts[1:])
                show_database_details(query, backup_bot, backup_type, db_name)
        elif data == 'db_backups_24h':
            show_database_backups_summary(query, backup_bot, 24)
        elif data == 'db_backups_48h':
            show_database_backups_summary(query, backup_bot, 48)
        elif data == 'db_backups_today':
            show_database_backups_summary(query, backup_bot, 24)
        elif data == 'db_backups_summary':
            show_database_backups_summary(query, backup_bot, 24)
        elif data == 'db_backups_detailed':
            show_database_backups_detailed(query, backup_bot)
        elif data == 'db_backups_list':
            show_database_backups_list(query, backup_bot)
        elif data == 'backup_main':
            show_main_menu(query)

    except Exception as e:
        logger.error(f"Ошибка в backup_callback: {e}")
        try:
            query.edit_message_text("❌ Ошибка при обработке запроса")
        except:
            pass

def show_main_menu(query):
    """Показывает главное меню бэкапов"""
    keyboard = [
        [InlineKeyboardButton("📊 Сегодня", callback_data='backup_today')],
        [InlineKeyboardButton("⏰ 24 часа", callback_data='backup_24h')],
        [InlineKeyboardButton("❌ Ошибки", callback_data='backup_failed')],
        [InlineKeyboardButton("🖥️ По хостам", callback_data='backup_hosts')],
        [InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_refresh')]
    ]

    query.edit_message_text(
        "💾 *Мониторинг бэкапов Proxmox*\n\nВыберите опцию:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_today_status(query, backup_bot):
    """Показывает статус бэкапов за сегодня"""
    try:
        results = backup_bot.get_today_status()
        
        if not results:
            query.edit_message_text(
                "📊 *Бэкапы за сегодня*\n\nНет данных за сегодня",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data='backup_today')],
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
                ])
            )
            return

        message = "📊 *Бэкапы за сегодня*\n\n"
        
        # Группируем по хостам
        hosts = {}
        for host_name, status, count, last_report in results:
            if host_name not in hosts:
                hosts[host_name] = []
            hosts[host_name].append((status, count, last_report))

        for host_name, backups in hosts.items():
            message += f"*{host_name}:*\n"
            for status, count, last_report in backups:
                status_icon = "✅" if status == 'success' else "❌"
                message += f"{status_icon} {status}: {count} отчетов\n"
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='backup_today')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_today_status: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_recent_backups(query, backup_bot):
    """Показывает последние бэкапы"""
    try:
        results = backup_bot.get_recent_backups(24)
        
        if not results:
            query.edit_message_text(
                "⏰ *Последние бэкапы (24ч)*\n\nНет данных за последние 24 часа",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data='backup_24h')],
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
                ])
            )
            return

        message = "⏰ *Последние бэкапы (24ч)*\n\n"
        
        for host_name, status, duration, total_size, error_message, received_at in results[:10]:
            status_icon = "✅" if status == 'success' else "❌"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"{status_icon} *{host_name}* ({time_str})\n"
            message += f"Статус: {status}\n"
            if duration:
                message += f"Время: {duration}\n"
            if total_size:
                message += f"Размер: {total_size}\n"
            if error_message and status == 'failed':
                message += f"Ошибка: {error_message[:100]}...\n"
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='backup_24h')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_recent_backups: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_failed_backups(query, backup_bot):
    """Показывает неудачные бэкапы"""
    try:
        results = backup_bot.get_failed_backups(1)
        
        if not results:
            query.edit_message_text(
                "❌ *Неудачные бэкапы (24ч)*\n\nНет неудачных бэкапов за последние 24 часа 🎉",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data='backup_failed')],
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
                ])
            )
            return

        message = "❌ *Неудачные бэкапы (24ч)*\n\n"
        
        for host_name, status, error_message, received_at in results:
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"*{host_name}* ({time_str})\n"
            if error_message:
                message += f"Ошибка: {error_message[:150]}...\n"
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='backup_failed')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_failed_backups: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_hosts_menu(query, backup_bot):
    """Показывает меню выбора хостов"""
    try:
        hosts = backup_bot.get_all_hosts()
        
        if not hosts:
            query.edit_message_text(
                "🖥️ *Бэкапы по хостам*\n\nНет данных о хостах",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
                ])
            )
            return

        keyboard = []
        # Создаем кнопки по 2 в ряд
        for i in range(0, len(hosts), 2):
            row = []
            if i < len(hosts):
                row.append(InlineKeyboardButton(hosts[i], callback_data=f'backup_host_{hosts[i]}'))
            if i + 1 < len(hosts):
                row.append(InlineKeyboardButton(hosts[i + 1], callback_data=f'backup_host_{hosts[i + 1]}'))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='backup_main')])

        query.edit_message_text(
            "🖥️ *Выберите хост для просмотра бэкапов:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка в show_hosts_menu: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_host_status(query, backup_bot, host_name):
    """Показывает статус конкретного хоста"""
    try:
        results = backup_bot.get_host_status(host_name)
        
        if not results:
            query.edit_message_text(
                f"🖥️ *Бэкапы {host_name}*\n\nНет данных по этому хосту",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_hosts')]
                ])
            )
            return

        message = f"🖥️ *Бэкапы {host_name}*\n\n"
        
        for status, duration, total_size, error_message, received_at in results:
            status_icon = "✅" if status == 'success' else "❌"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            message += f"{status_icon} *{time_str}* - {status}\n"
            if duration:
                message += f"Время: {duration}\n"
            if total_size:
                message += f"Размер: {total_size}\n"
            if error_message and status == 'failed':
                message += f"Ошибка: {error_message[:100]}...\n"
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=f'backup_host_{host_name}')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_hosts')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_host_status: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_backups_menu(query, backup_bot):
    """Показывает меню бэкапов баз данных"""
    keyboard = [
        [InlineKeyboardButton("📊 Сводка за 24ч", callback_data='db_backups_24h')],
        [InlineKeyboardButton("📈 Сводка за 48ч", callback_data='db_backups_48h')],
        [InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
    ]

    query.edit_message_text(
        "🗃️ *Бэкапы баз данных*\n\nВыберите опцию:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_database_backups_summary(query, backup_bot, hours):
    """Показывает сводку по бэкапам БД"""
    try:
        summary = backup_bot.get_database_backups_summary(hours)
        
        if not summary:
            query.edit_message_text(
                f"📊 *Бэкапы БД ({hours}ч)*\n\nНет данных за последние {hours} часов",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data=f'db_backups_{hours}h')],
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
                ])
            )
            return

        message = f"📊 *Бэкапы БД ({hours}ч)*\n\n"
        
        type_names = {
            'company_database': '🏢 Основные БД',
            'barnaul': '🏔️ Барнаул', 
            'client': '👥 Клиентские',
            'yandex': '☁️ Yandex'
        }

        for backup_type, databases in summary.items():
            type_display = type_names.get(backup_type, f"📁 {backup_type}")
            message += f"*{type_display}:*\n"
            
            for db_name, stats in databases.items():
                success = stats.get('success', 0)
                failed = stats.get('failed', 0)
                total = success + failed
                
                if total > 0:
                    success_rate = (success / total) * 100
                    status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
                    message += f"{status_icon} {db_name}: {success}/{total} ({success_rate:.1f}%)\n"
            
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=f'db_backups_{hours}h')],
                [InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_summary: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_backups_list(query, backup_bot):
    """Показывает список всех баз данных с кнопками для деталей"""
    try:
        stats = backup_bot.get_database_backups_stats(24)
        
        if not stats:
            query.edit_message_text(
                "📋 *Список баз данных*\n\nНет данных за последние 24 часа",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_list')],
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
                ])
            )
            return

        # Группируем по типам и базам
        databases = {}
        for backup_type, db_name, db_display, status, count, last_backup in stats:
            key = (backup_type, db_name)
            if key not in databases:
                databases[key] = {'success': 0, 'failed': 0, 'display_name': db_display or db_name}
            databases[key][status] += count

        # Создаем клавиатуру
        keyboard = []
        current_row = []
        
        type_names = {
            'company_database': '🏢',
            'barnaul': '🏔️', 
            'client': '👥',
            'yandex': '☁️'
        }

        for (backup_type, db_name), stats in databases.items():
            type_icon = type_names.get(backup_type, '📁')
            success = stats.get('success', 0)
            failed = stats.get('failed', 0)
            total = success + failed
            
            if total > 0:
                success_rate = (success / total) * 100
                status_icon = "🟢" if success_rate >= 80 else "🟡" if success_rate >= 50 else "🔴"
                button_text = f"{type_icon}{status_icon} {db_name}"
            else:
                button_text = f"{type_icon}⚪ {db_name}"
            
            # Ограничиваем длину текста кнопки
            if len(button_text) > 15:
                button_text = button_text[:15] + ".."
            
            current_row.append(InlineKeyboardButton(
                button_text, 
                callback_data=f'db_detail_{backup_type}_{db_name}'
            ))
            
            if len(current_row) >= 2:
                keyboard.append(current_row)
                current_row = []
        
        if current_row:
            keyboard.append(current_row)
        
        keyboard.extend([
            [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_list')],
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
        ])

        query.edit_message_text(
            "📋 *Список баз данных*\n\nВыберите базу для просмотра деталей:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_list: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_details(query, backup_bot, backup_type, db_name):
    """Показывает детальную информацию по конкретной базе данных"""
    try:
        details_text = format_database_details(backup_bot, backup_type, db_name, 168)
        
        query.edit_message_text(
            details_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=f'db_detail_{backup_type}_{db_name}')],
                [InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_details: {e}")
        query.edit_message_text("❌ Ошибка при получении деталей БД")

def show_database_backups_detailed(query, backup_bot):
    """Показывает детальную информацию по всем бэкапам БД"""
    try:
        stats = backup_bot.get_database_backups_stats(24)
        
        if not stats:
            query.edit_message_text(
                "📈 *Детальные бэкапы БД*\n\nНет данных за последние 24 часа",
                parse_mode='Markdown'
            )
            return

        message = "📈 *Детальные бэкапы БД (24ч)*\n\n"
        
        # Группируем по типам
        by_type = {}
        for backup_type, db_name, db_display, status, count, last_backup in stats:
            if backup_type not in by_type:
                by_type[backup_type] = []
            by_type[backup_type].append((db_name, db_display, status, count, last_backup))

        type_names = {
            'company_database': '🏢 Основные БД',
            'barnaul': '🏔️ Барнаул', 
            'client': '👥 Клиентские',
            'yandex': '☁️ Yandex'
        }

        for backup_type, databases in by_type.items():
            type_display = type_names.get(backup_type, f"📁 {backup_type}")
            message += f"*{type_display}:*\n"
            
            # Группируем по базам
            db_stats = {}
            for db_name, db_display, status, count, last_backup in databases:
                if db_name not in db_stats:
                    db_stats[db_name] = {'success': 0, 'failed': 0, 'display_name': db_display}
                db_stats[db_name][status] += count
            
            for db_name, stats in db_stats.items():
                success = stats.get('success', 0)
                failed = stats.get('failed', 0)
                total = success + failed
                
                if total > 0:
                    success_rate = (success / total) * 100
                    status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
                    display_name = stats.get('display_name', db_name)
                    message += f"{status_icon} {display_name}: {success}/{total} ({success_rate:.1f}%)\n"
            
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_detailed: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def setup_backup_handlers(dispatcher):
    """Настраивает обработчики для бэкапов"""
    from telegram.ext import CommandHandler, CallbackQueryHandler
    
    dispatcher.add_handler(CommandHandler("backup", backup_command))
    dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
    dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^backup_'))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^db_'))
    