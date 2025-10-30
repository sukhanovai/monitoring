"""
Обработчик команд бота для мониторинга бэкапов Proxmox с кнопками
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
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
        """Получает статистику по бэкапам баз данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT 
                backup_type,
                database_display_name,
                backup_status,
                COUNT(*) as backup_count,
                MAX(received_at) as last_backup
            FROM database_backups 
            WHERE received_at >= ?
            GROUP BY backup_type, database_display_name, backup_status
            ORDER BY backup_type, database_display_name, last_backup DESC
        ''', (since_time,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    def get_database_backups_summary(self, hours=24):
        """Сводка по бэкапам баз данных"""
        stats = self.get_database_backups_stats(hours)
        
        if not stats:
            return "📊 *Бэкапы баз данных*\n\nНет данных о бэкапах БД за указанный период"
        
        summary = {}
        for backup_type, db_name, status, count, last_backup in stats:
            if backup_type not in summary:
                summary[backup_type] = {}
            if db_name not in summary[backup_type]:
                summary[backup_type][db_name] = {'success': 0, 'failed': 0, 'last_backup': last_backup}
            
            summary[backup_type][db_name][status] = count
        
        return summary

def format_backup_summary(backup_bot):
    """Форматирует сводку по бэкапам за сегодня"""
    today_status = backup_bot.get_today_status()

    if not today_status:
        return "📊 *Бэкапы Proxmox за сегодня*\n\nНет данных о бэкапах за сегодня"

    # Группируем по хостам
    hosts = {}
    for host, status, count, last_report in today_status:
        if host not in hosts:
            hosts[host] = []
        hosts[host].append((status, count, last_report))

    message = "📊 *Бэкапы Proxmox за сегодня*\n\n"

    for host in sorted(hosts.keys()):
        host_reports = hosts[host]

        # Определяем общий статус хоста
        has_success = any(status == 'success' for status, count, _ in host_reports)
        has_failed = any(status == 'failed' for status, count, _ in host_reports)

        if has_failed:
            icon = "❌"
        elif has_success:
            icon = "✅"
        else:
            icon = "⚠️"

        message += f"{icon} *{host}*:\n"

        for status, count, last_report in host_reports:
            status_icon = "✅" if status == 'success' else "❌" if status == 'failed' else "⚠️"
            time_str = datetime.strptime(last_report, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
            message += f"   {status_icon} {status}: {count} отчетов (последний: {time_str})\n"

        message += "\n"

    # Добавляем время обновления, чтобы сообщение всегда было уникальным
    message += f"🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}\n"
    message += "💡 Используйте кнопки ниже для детальной информации"

    return message

def format_recent_backups(backup_bot, hours=24):
    """Форматирует список последних бэкапов"""
    recent = backup_bot.get_recent_backups(hours)

    if not recent:
        return f"📅 *Бэкапы за {hours} часов*\n\nНет данных за указанный период"

    message = f"📅 *Последние бэкапы ({hours}ч)*\n\n"

    for host, status, duration, size, error, received_at in recent:
        icon = "✅" if status == 'success' else "❌"
        time_str = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')

        message += f"{icon} *{time_str}* - {host}\n"
        message += f"   Статус: {status}\n"
        if duration:
            message += f"   Время: {duration}\n"
        if size:
            message += f"   Размер: {size}\n"
        if error:
            message += f"   Ошибка: {error[:50]}...\n"
        message += "\n"

    # Добавляем время обновления
    message += f"🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
    
    return message

def format_failed_backups(backup_bot, days=1):
    """Форматирует список неудачных бэкапов"""
    failed = backup_bot.get_failed_backups(days)

    if not failed:
        return f"❌ *Неудачные бэкапы ({days}д)*\n\nНет ошибок за указанный период ✅"

    message = f"❌ *Неудачные бэкапы ({days}д)*\n\n"

    for host, status, error, received_at in failed:
        time_str = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')

        message += f"🕒 *{time_str}* - {host}\n"
        if error:
            message += f"   Ошибка: {error[:80]}{'...' if len(error) > 80 else ''}\n"
        else:
            message += f"   Ошибка: не указана\n"
        message += "\n"

    # Добавляем время обновления
    message += f"🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
    
    return message

def format_host_status(backup_bot, host_name):
    """Форматирует статус конкретного хоста с правильным временем"""
    host_status = backup_bot.get_host_status(host_name)

    if not host_status:
        return f"🔍 *Статус {host_name}*\n\nНет данных о бэкапах"

    message = f"🔍 *Статус бэкапов {host_name}*\n\n"

    for status, duration, size, error, received_at in host_status:
        icon = "✅" if status == 'success' else "❌"

        # Парсим время и форматируем в локальное
        try:
            received_dt = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
            time_str = received_dt.strftime('%m-%d %H:%M')  # Месяц-день Час:Минута
        except:
            time_str = received_at[:16]  # Fallback

        message += f"{icon} *{time_str}* - {status}\n"

        if duration:
            message += f"   ⏱️ Длительность: {duration}\n"
        if size:
            message += f"   💾 Размер: {size}\n"
        if error:
            message += f"   ❗ Ошибка: {error[:60]}...\n"
        message += "\n"

    return message

def format_hosts_list(backup_bot):
    """Форматирует список всех хостов"""
    hosts = backup_bot.get_all_hosts()

    if not hosts:
        return "📋 *Список серверов*\n\nНет данных о серверах"

    message = "📋 *Выберите сервер для просмотра*\n\n"
    message += "Доступные серверы:\n\n"

    for host in sorted(hosts):
        message += f"• {host}\n"

    message += "\nНажмите на кнопку с именем сервера для просмотра его статуса"

    return message

def format_database_backups_report(backup_bot, hours=24):
    """Форматирует отчет по бэкапам баз данных"""
    summary = backup_bot.get_database_backups_summary(hours)
    
    if not summary:
        return f"📊 *Бэкапы баз данных ({hours}ч)*\n\nНет данных о бэкапах БД"
    
    message = f"📊 *Бэкапы баз данных ({hours}ч)*\n\n"
    
    # Основные базы данных компании
    if 'company_database' in summary:
        message += "🏢 *Основные базы данных:*\n"
        for db_name, stats in summary['company_database'].items():
            status_icon = "✅" if stats['success'] > 0 else "❌"
            message += f"{status_icon} {db_name}: {stats['success']} успешных\n"
        message += "\n"
    
    # Бэкапы Барнаул
    if 'barnaul' in summary:
        message += "🏔️ *Бэкапы Барнаул:*\n"
        for db_name, stats in summary['barnaul'].items():
            if stats['success'] > 0:
                status_icon = "✅"
            elif stats['failed'] > 0:
                status_icon = "❌"
            else:
                status_icon = "⚠️"
            message += f"{status_icon} {db_name}: успешных {stats['success']}, ошибок {stats['failed']}\n"
        message += "\n"
    
    # Бэкапы клиентов
    if 'client' in summary:
        message += "👥 *Базы клиентов:*\n"
        for db_name, stats in summary['client'].items():
            status_icon = "✅" if stats['success'] > 0 else "❌"
            message += f"{status_icon} {db_name}: {stats['success']} успешных\n"
        message += "\n"
    
    # Бэкапы Yandex
    if 'yandex' in summary:
        message += "☁️ *Бэкапы Yandex:*\n"
        for db_name, stats in summary['yandex'].items():
            status_icon = "✅" if stats['success'] > 0 else "❌"
            message += f"{status_icon} {db_name}: {stats['success']} успешных\n"
    
    message += f"\n🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
    
    return message

def create_main_keyboard():
    """Создает основную клавиатуру для бэкапов"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Сегодня", callback_data='backup_today'),
         InlineKeyboardButton("📅 24 часа", callback_data='backup_24h')],
        [InlineKeyboardButton("❌ Ошибки", callback_data='backup_failed'),
         InlineKeyboardButton("📋 Все серверы", callback_data='backup_hosts')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_refresh')]
    ])

def create_hosts_keyboard(backup_bot):
    """Создает клавиатуру со списком хостов"""
    hosts = backup_bot.get_all_hosts()

    # Создаем кнопки по 2 в ряд
    keyboard = []
    row = []

    for host in sorted(hosts):
        row.append(InlineKeyboardButton(host, callback_data=f'backup_host_{host}'))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:  # Добавляем последний неполный ряд
        keyboard.append(row)

    # Добавляем кнопку возврата
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='backup_today')])

    return InlineKeyboardMarkup(keyboard)

def create_back_keyboard():
    """Создает клавиатуру с кнопкой возврата"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад к обзору", callback_data='backup_today')]
    ])

def backup_command(update, context):
    """Обработчик команды /backup"""
    backup_bot = BackupMonitorBot()
    message = format_backup_summary(backup_bot)

    update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )

def backup_search_command(update, context):
    """Обработчик команды поиска по серверу"""
    if not context.args:
        update.message.reply_text("❌ Укажите имя сервера: `/backup_search pve13`", parse_mode='Markdown')
        return

    host_name = context.args[0]
    backup_bot = BackupMonitorBot()
    message = format_host_status(backup_bot, host_name)

    update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=create_back_keyboard()
    )

def backup_help_command(update, context):
    """Помощь по командам бэкапов"""
    help_text = """
🤖 *Команды мониторинга бэкапов*

*/backup* - Основная сводка за сегодня
*/backup_search [host]* - Поиск по конкретному серверу
*/backup_help* - Эта справка

*Кнопки управления:*
📊 *Сегодня* - Сводка за текущий день
📅 *24 часа* - История за последние сутки
❌ *Ошибки* - Список неудачных бэкапов
📋 *Все серверы* - Выбор конкретного сервера
🔄 *Обновить* - Обновить данные

*Примеры:*
`/backup` - общая сводка
`/backup_search pve13` - статус pve13
"""

    update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )

def backup_callback(update, context):
    """Обработчик callback'ов для бэкапов"""
    query = update.callback_query
    query.answer()

    try:
        backup_bot = BackupMonitorBot()
        current_message = query.message.text
        current_keyboard = query.message.reply_markup

        if query.data == 'backup_today':
            message = format_backup_summary(backup_bot)
            keyboard = create_main_keyboard()

        elif query.data == 'backup_24h':
            message = format_recent_backups(backup_bot, 24)
            keyboard = create_back_keyboard()

        elif query.data == 'backup_failed':
            message = format_failed_backups(backup_bot, 1)
            keyboard = create_back_keyboard()

        elif query.data == 'backup_hosts':
            message = format_hosts_list(backup_bot)
            keyboard = create_hosts_keyboard(backup_bot)

        elif query.data == 'backup_refresh':
            message = format_backup_summary(backup_bot)
            keyboard = create_main_keyboard()

        elif query.data.startswith('backup_host_'):
            host_name = query.data.replace('backup_host_', '')
            message = format_host_status(backup_bot, host_name)
            keyboard = create_back_keyboard()

        else:
            message = "❌ Неизвестная команда"
            keyboard = create_main_keyboard()

        # Проверяем, изменилось ли сообщение или клавиатура
        message_changed = (message != current_message)
        keyboard_changed = (keyboard.to_json() != current_keyboard.to_json() if current_keyboard else True)

        if message_changed or keyboard_changed:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        else:
            # Если ничего не изменилось, просто отвечаем на callback без изменений
            query.answer("✅ Данные актуальны")

    except Exception as e:
        logger.error(f"Ошибка в callback обработчике: {e}")
        
        # Проверяем, не является ли ошибка "message not modified"
        if "Message is not modified" in str(e):
            query.answer("✅ Данные актуальны")
        else:
            error_message = f"❌ Ошибка при обработке запроса: {str(e)}"
            try:
                query.edit_message_text(
                    error_message,
                    reply_markup=create_main_keyboard()
                )
            except Exception as edit_error:
                # Если не удалось отредактировать сообщение, просто логируем
                logger.error(f"Не удалось отредактировать сообщение: {edit_error}")
                query.answer("❌ Произошла ошибка")


def setup_backup_commands(dispatcher):
    """Настройка команд бота для мониторинга бэкапов"""
    from telegram.ext import CommandHandler, CallbackQueryHandler

    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler("backup", backup_command))
    dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
    dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^backup_'))
    dispatcher.add_handler(CommandHandler("db_backups", database_backups_command))

    logger.info("Команды мониторинга бэкапов зарегистрированы")

def get_backup_history(self, days=30, host_name=None):
    """Получает историю бэкапов за период"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    query = '''
        SELECT
            host_name,
            backup_status,
            duration,
            total_size,
            error_message,
            received_at
        FROM proxmox_backups
        WHERE received_at >= datetime('now', ?)
    '''
    params = [f'-{days} days']

    if host_name:
        query += ' AND host_name = ?'
        params.append(host_name)

    query += ' ORDER BY received_at DESC'

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results

def get_backup_statistics(self, days=30):
    """Статистика бэкапов за период"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            host_name,
            backup_status,
            COUNT(*) as count,
            MAX(received_at) as last_backup
        FROM proxmox_backups
        WHERE received_at >= datetime('now', ?)
        GROUP BY host_name, backup_status
        ORDER BY host_name, last_backup DESC
    ''', (f'-{days} days',))

    results = cursor.fetchall()
    conn.close()

    return results

def database_backups_command(update, context):
    """Обработчик команды для просмотра бэкапов баз данных"""
    backup_bot = BackupMonitorBot()
    
    # По умолчанию показываем за 24 часа
    hours = 24
    if context.args:
        try:
            hours = int(context.args[0])
        except ValueError:
            update.message.reply_text("❌ Укажите корректное количество часов: `/db_backups 24`", parse_mode='Markdown')
            return
    
    message = format_database_backups_report(backup_bot, hours)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_refresh')],
        [InlineKeyboardButton("📊 Proxmox бэкапы", callback_data='backup_today')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_today')]
    ])
    
    update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )
