"""
Обработчик команд бота для мониторинга бэкапов Proxmox с кнопками
"""

import sqlite3
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class BackupMonitorBot:
    def __init__(self):
        self.db_path = '/opt/monitoring/data/backups.db'
    
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
    
    return message

def format_host_status(backup_bot, host_name):
    """Форматирует статус конкретного хоста"""
    host_status = backup_bot.get_host_status(host_name)
    
    if not host_status:
        return f"🔍 *Статус {host_name}*\n\nНет данных о бэкапах"
    
    message = f"🔍 *Статус бэкапов {host_name}*\n\n"
    
    for status, duration, size, error, received_at in host_status:
        icon = "✅" if status == 'success' else "❌"
        time_str = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')
        
        message += f"{icon} *{time_str}* - {status}\n"
        if duration:
            message += f"   Длительность: {duration}\n"
        if size:
            message += f"   Размер: {size}\n"
        if error:
            message += f"   Ошибка: {error[:60]}...\n"
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

def setup_backup_commands(dispatcher):
    """Настройка команд бота для мониторинга бэкапов"""
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
    
    backup_bot = BackupMonitorBot()
    
    def backup_command(update, context):
        """Обработчик команды /backup"""
        message = format_backup_summary(backup_bot)
        
        update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )
    
    def backup_callback(update, context):
        """Обработчик callback'ов для бэкапов"""
        query = update.callback_query
        query.answer()
        
        backup_bot = BackupMonitorBot()
        
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
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def backup_search_command(update, context):
        """Обработчик поиска по хостам через сообщение"""
        if not context.args:
            # Показываем список хостов если не указан конкретный
            message = format_hosts_list(backup_bot)
            update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=create_hosts_keyboard(backup_bot)
            )
            return
        
        host_name = context.args[0].lower()
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
    
    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler("backup", backup_command))
    dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
    dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^backup_'))
    