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

def format_backup_summary(backup_bot):
    """Форматирует сводку по бэкапам за сегодня"""
    today_status = backup_bot.get_today_status()

    if not today_status:
        return "📊 Бэкапы Proxmox за сегодня\n\nНет данных о бэкапах за сегодня"

    # Группируем по хостам
    hosts = {}
    for host, status, count, last_report in today_status:
        if host not in hosts:
            hosts[host] = []
        hosts[host].append((status, count, last_report))

    message = "📊 Бэкапы Proxmox за сегодня\n\n"

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

        message += f"{icon} {host}:\n"

        for status, count, last_report in host_reports:
            status_icon = "✅" if status == 'success' else "❌" if status == 'failed' else "⚠️"
            time_str = datetime.strptime(last_report, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
            message += f"   {status_icon} {status}: {count} отчетов (последний: {time_str})\n"

        message += "\n"

    # Добавляем время обновления, чтобы сообщение всегда было уникальным
    message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}\n"
    message += "💡 Используйте кнопки ниже для детальной информации"

    return message

def format_recent_backups(backup_bot, hours=24):
    """Форматирует список последних бэкапов"""
    recent = backup_bot.get_recent_backups(hours)

    if not recent:
        return f"📅 Бэкапы за {hours} часов\n\nНет данных за указанный период"

    message = f"📅 Последние бэкапы ({hours}ч)\n\n"

    for host, status, duration, size, error, received_at in recent:
        icon = "✅" if status == 'success' else "❌"
        time_str = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')

        message += f"{icon} {time_str} - {host}\n"
        message += f"   Статус: {status}\n"
        if duration:
            message += f"   Время: {duration}\n"
        if size:
            message += f"   Размер: {size}\n"
        if error:
            message += f"   Ошибка: {error[:50]}...\n"
        message += "\n"

    # Добавляем время обновления
    message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
    
    return message

def format_failed_backups(backup_bot, days=1):
    """Форматирует список неудачных бэкапов"""
    failed = backup_bot.get_failed_backups(days)

    if not failed:
        return f"❌ Неудачные бэкапы ({days}д)\n\nНет ошибок за указанный период ✅"

    message = f"❌ Неудачные бэкапы ({days}д)\n\n"

    for host, status, error, received_at in failed:
        time_str = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M')

        message += f"🕒 {time_str} - {host}\n"
        if error:
            message += f"   Ошибка: {error[:80]}{'...' if len(error) > 80 else ''}\n"
        else:
            message += f"   Ошибка: не указана\n"
        message += "\n"

    # Добавляем время обновления
    message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
    
    return message

def format_host_status(backup_bot, host_name):
    """Форматирует статус конкретного хоста с правильным временем"""
    host_status = backup_bot.get_host_status(host_name)

    if not host_status:
        return f"🔍 Статус {host_name}\n\nНет данных о бэкапах"

    message = f"🔍 Статус бэкапов {host_name}\n\n"

    for status, duration, size, error, received_at in host_status:
        icon = "✅" if status == 'success' else "❌"

        # Парсим время и форматируем в локальное
        try:
            received_dt = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
            time_str = received_dt.strftime('%m-%d %H:%M')  # Месяц-день Час:Минута
        except:
            time_str = received_at[:16]  # Fallback

        message += f"{icon} {time_str} - {status}\n"

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
        return "📋 Список серверов\n\nНет данных о серверах"

    message = "📋 Выберите сервер для просмотра\n\n"
    message += "Доступные серверы:\n\n"

    for host in sorted(hosts):
        message += f"• {host}\n"

    message += "\nНажмите на кнопку с именем сервера для просмотра его статуса"

    return message

def format_database_backups_report(backup_bot, hours=24):
    """Форматирует отчет по бэкапам баз данных - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    try:
        stats = backup_bot.get_database_backups_stats(hours)
        
        if not stats:
            return f"📊 Бэкапы баз данных ({hours}ч)\n\nНет данных о бэкапах БД за указанный период"
        
        # ОБНОВЛЕНИЕ: работа с 6 значениями
        summary = {}
        type_names = {
            'company_database': '🏢 Основные БД',
            'barnaul': '🏔️ Барнаул', 
            'client': '👥 Клиенты',
            'yandex': '☁️ Yandex'
        }
        
        for backup_type, db_name, display_name, status, count, last_backup in stats:
            if backup_type not in summary:
                summary[backup_type] = {}
            if db_name not in summary[backup_type]:
                summary[backup_type][db_name] = {'success': 0, 'failed': 0, 'last_backup': last_backup}
            
            if status == 'success':
                summary[backup_type][db_name]['success'] += count
            elif status == 'failed':
                summary[backup_type][db_name]['failed'] += count
        
        # Формируем сообщение БЕЗ Markdown разметки
        message = f"📊 Бэкапы баз данных ({hours}ч)\n\n"
        
        for backup_type, databases in summary.items():
            type_display = type_names.get(backup_type, f"📁 {backup_type}")
            message += f"{type_display}:\n"
            
            for db_name, stats in databases.items():
                total = stats['success'] + stats['failed']
                if stats['success'] > 0 and stats['failed'] == 0:
                    status_icon = "✅"
                elif stats['failed'] > 0:
                    status_icon = "❌"
                else:
                    status_icon = "⚠️"
                    
                message += f"{status_icon} {db_name}: {stats['success']}/{total}\n"
            
            message += "\n"
        
        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        
        return message
        
    except Exception as e:
        logger.error(f"Ошибка в format_database_backups_report: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
        return f"❌ Ошибка при формировании отчета: {e}"
        
def format_detailed_database_backups(backup_bot, hours=24):
    """Детальный отчет по бэкапам БД с историей - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    try:
        stats = backup_bot.get_database_backups_stats(hours)
        
        if not stats:
            return f"📋 Детальный отчет по БД ({hours}ч)\n\nНет данных"
        
        message = f"📋 Детальный отчет по БД ({hours}ч)\n\n"
        
        # ОБНОВЛЕНИЕ: работа с 6 значениями
        db_details = {}
        for backup_type, db_name, display_name, status, count, last_backup in stats:
            key = (backup_type, db_name)
            if key not in db_details:
                db_details[key] = {'success': 0, 'failed': 0, 'last_backup': last_backup}
            
            if status == 'success':
                db_details[key]['success'] += count
            elif status == 'failed':
                db_details[key]['failed'] += count
        
        type_names = {
            'company_database': '🏢',
            'barnaul': '🏔️', 
            'client': '👥',
            'yandex': '☁️'
        }
        
        # Сортируем по типу и имени БД
        sorted_dbs = sorted(db_details.items(), key=lambda x: (x[0][0], x[0][1]))
        
        for (backup_type, db_name), stats in sorted_dbs:
            type_icon = type_names.get(backup_type, '📁')
            
            # Определяем общий статус
            if stats['success'] > 0 and stats['failed'] == 0:
                status_icon = "✅"
            elif stats['failed'] > 0:
                status_icon = "❌"
            else:
                status_icon = "⚠️"
            
            message += f"{type_icon} {db_name} {status_icon}\n"
            message += f"   Всего бэкапов: {stats['success'] + stats['failed']}\n"
            message += f"   Успешных: {stats['success']}\n"
            message += f"   Ошибок: {stats['failed']}\n"
            
            # Находим последний бэкап
            if stats['last_backup']:
                try:
                    last_time = datetime.strptime(stats['last_backup'], '%Y-%m-%d %H:%M:%S')
                    message += f"   Последний: {last_time.strftime('%d.%m %H:%M')}\n"
                except:
                    message += f"   Последний: {stats['last_backup'][:16]}\n"
            
            message += "\n"
        
        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        return message
        
    except Exception as e:
        logger.error(f"Ошибка в format_detailed_database_backups: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
        return f"❌ Ошибка при формировании детального отчета: {e}"
        
def get_database_list(backup_bot, hours=168):
    """Получает список всех баз данных для меню выбора - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    try:
        stats = backup_bot.get_database_backups_stats(hours)
        
        if not stats:
            return f"📋 Список баз данных\n\nНет данных о бэкапах БД за последние {hours} часов"
        
        # ОБНОВЛЕНИЕ: работа с 6 значениями
        databases = set()
        for backup_type, db_name, display_name, status, count, last_backup in stats:
            databases.add((backup_type, db_name))
        
        message = "📋 Выберите базу данных для просмотра\n\n"
        message += "Доступные базы:\n\n"
        
        type_names = {
            'company_database': '🏢',
            'barnaul': '🏔️', 
            'client': '👥',
            'yandex': '☁️'
        }
        
        for backup_type, db_name in sorted(databases):
            type_icon = type_names.get(backup_type, '📁')
            message += f"• {type_icon} {db_name}\n"
        
        message += f"\nНажмите на базу данных для просмотра деталей (данные за {hours}ч)"
        return message
        
    except Exception as e:
        logger.error(f"Ошибка в get_database_list: {e}")
        return f"❌ Ошибка при получении списка БД: {e}"
            
def format_database_details(backup_bot, backup_type, db_name, hours=168):
    """Детальная информация по конкретной базе данных"""
    try:
        stats = backup_bot.get_database_backups_stats(hours)
        
        if not stats:
            return f"📋 Детали по {db_name}\n\nНет данных за указанный период"
        
        # Фильтруем по конкретной базе - используем database_name из базы
        db_stats = [s for s in stats if s[0] == backup_type and s[1] == db_name]
        
        if not db_stats:
            return f"📋 Детали по {db_name}\n\nНет данных за указанный период"
        
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
        
        # Группируем по статусам
        success_count = sum(s[3] for s in db_stats if s[2] == 'success')
        failed_count = sum(s[3] for s in db_stats if s[2] == 'failed')
        total_count = success_count + failed_count
        
        message += f"📊 Статистика:\n"
        message += f"✅ Успешных: {success_count}\n"
        message += f"❌ Ошибок: {failed_count}\n"
        message += f"📈 Всего: {total_count}\n\n"
        
        # Последние бэкапы
        message += "⏰ Последние бэкапы:\n"
        recent_backups = sorted(db_stats, key=lambda x: x[4], reverse=True)[:5]
        
        for backup in recent_backups:
            status_icon = "✅" if backup[2] == 'success' else "❌"
            try:
                backup_time = datetime.strptime(backup[4], '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = backup[4][:16]
            
            message += f"{status_icon} {time_str} - {backup[2]}\n"
        
        message += f"\n🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        return message
        
    except Exception as e:
        logger.error(f"Ошибка в format_database_details: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
        return f"❌ Ошибка при получении деталей БД: {e}"
        
def create_main_backup_keyboard():
    """Создает главное меню бэкапов"""
    from extensions.extension_manager import extension_manager
    
    keyboard = []
    
    # Кнопка Proxmox бэкапов (только если расширение включено)
    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("🖥️ Бэкапы Proxmox", callback_data='backup_proxmox')])
    
    # Кнопка бэкапов БД (только если расширение включено)
    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')])
    
    # Общие кнопки
    keyboard.extend([
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_refresh'),
         InlineKeyboardButton("📋 Помощь", callback_data='backup_help')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status'),
         InlineKeyboardButton("⚫ Закрыть", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_proxmox_backup_keyboard():
    """Создает меню бэкапов Proxmox"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Сегодня", callback_data='backup_today'),
         InlineKeyboardButton("📅 24 часа", callback_data='backup_24h')],
        [InlineKeyboardButton("❌ Ошибки", callback_data='backup_failed'),
         InlineKeyboardButton("📋 Все серверы", callback_data='backup_hosts')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_main'),
         InlineKeyboardButton("⚫ Закрыть", callback_data='close')]
    ])

def create_database_backup_keyboard():
    """Создает меню бэкапов баз данных"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Общий отчет", callback_data='db_backups_summary'),
         InlineKeyboardButton("📋 Детальный отчет", callback_data='db_backups_detailed')],
        [InlineKeyboardButton("🗃️ Список БД", callback_data='db_backups_list'),
         InlineKeyboardButton("🕐 За 48ч", callback_data='db_backups_48h')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_main'),
         InlineKeyboardButton("⚫ Закрыть", callback_data='close')]
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

    # Добавляем кнопку возврата и закрытия
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='backup_proxmox'),
        InlineKeyboardButton("⚫ Закрыть", callback_data='close')
    ])

    return InlineKeyboardMarkup(keyboard)

def create_database_list_keyboard(backup_bot, hours=24):
    """Создает клавиатуру со списком баз данных - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    stats = backup_bot.get_database_backups_stats(hours)
    
    if not stats:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
        ])
    
    # ОБНОВЛЕНИЕ: работа с 6 значениями
    databases = set()
    for backup_type, db_name, display_name, status, count, last_backup in stats:
        databases.add((backup_type, db_name))
    
    keyboard = []
    row = []
    
    for backup_type, db_name in sorted(databases):
        callback_data = f"db_detail_{backup_type}_{db_name}"
        button_text = db_name
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Кнопки управления
    keyboard.extend([
        [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_list'),
         InlineKeyboardButton("📊 Общий отчет", callback_data='db_backups_summary')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases'),
         InlineKeyboardButton("⚫ Закрыть", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_database_details(self, backup_type, db_name, hours=24):
    """Получает детальную информацию по конкретной базе данных"""
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
    
    return results

def format_database_details(backup_bot, backup_type, db_name, hours=24):
    """Детальная информация по конкретной базе данных"""
    try:
        # Получаем детальные данные
        details = backup_bot.get_database_details(backup_type, db_name, hours)
        
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
            if error_count > 0:
                message += f" (ошибок: {error_count})"
            message += "\n"
        
        message += f"\n🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        return message
        
    except Exception as e:
        logger.error(f"Ошибка в format_database_details: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
        return f"❌ Ошибка при получении деталей БД: {e}"
    
def create_database_detail_keyboard(backup_type, db_name):
    """Создает клавиатуру для детального просмотра БД"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data=f'db_detail_{backup_type}_{db_name.replace(" ", "_")}'),
         InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
        [InlineKeyboardButton("↩️ Назад к БД", callback_data='backup_databases'),
         InlineKeyboardButton("⚫ Закрыть", callback_data='close')]
    ])

def create_back_keyboard():
    """Создает клавиатуру с кнопкой возврата"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад к обзору", callback_data='backup_today')]
    ])

def backup_command(update, context):
    """Обработчик команды /backup - главное меню бэкапов"""
    message = (
        "📊 Главное меню бэкапов\n\n"
        "Выберите тип бэкапов для просмотра:"
    )

    update.message.reply_text(
        message,
        parse_mode=None,
        reply_markup=create_main_backup_keyboard()
    )

def backup_search_command(update, context):
    """Обработчик команды поиска по серверу"""
    if not context.args:
        update.message.reply_text("❌ Укажите имя сервера: /backup_search pve13", parse_mode=None)
        return

    host_name = context.args[0]
    backup_bot = BackupMonitorBot()
    message = format_host_status(backup_bot, host_name)

    update.message.reply_text(
        message,
        parse_mode=None,
        reply_markup=create_back_keyboard()
    )

def backup_help_command(update, context):
    """Помощь по командам бэкапов"""
    help_text = """
🤖 Команды мониторинга бэкапов

/backup - Основная сводка за сегодня
/backup_search [host] - Поиск по конкретному серверу
/db_backups [hours] - Бэкапы баз данных (по умолчанию 24ч)
/backup_help - Эта справка

Кнопки управления:
📊 Сегодня - Сводка за текущий день
📅 24 часа - История за последние сутки
❌ Ошибки - Список неудачных бэкапов
📋 Все серверы - Выбор конкретного сервера
🗃️ Базы данных - Бэкапы СУБД и приложений
🔄 Обновить - Обновить данные

Примеры:
/backup - общая сводка
/backup_search pve13 - статус pve13
/db_backups 48 - бэкапы БД за 48 часов
"""

    update.message.reply_text(
        help_text,
        parse_mode=None,
        reply_markup=create_main_backup_keyboard()
    )

def backup_callback(update, context):
    """Обработчик callback'ов для бэкапов"""
    query = update.callback_query
    query.answer()

    # ДОБАВИМ ОТЛАДОЧНЫЙ ВЫВОД
    print(f"🔍 DEBUG: Получен callback: {query.data}")
    logger.info(f"🔍 DEBUG: Получен callback: {query.data}")

    try:
        backup_bot = BackupMonitorBot()

        # Обработка выбора конкретного хоста
        if query.data.startswith('backup_host_'):
            print(f"🔍 DEBUG: Обрабатываем backup_host_")
            host_name = query.data.replace('backup_host_', '')
            message = format_host_status(backup_bot, host_name)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Назад к серверам", callback_data='backup_hosts'),
                 InlineKeyboardButton("⚫ Закрыть", callback_data='close')]
            ])

        # Обработка бэкапов БД
        elif query.data == 'db_backups_summary':
            print(f"🔍 DEBUG: Обрабатываем db_backups_summary")
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('database_backup_monitor'):
                message = format_database_backups_report(backup_bot, 24)
                keyboard = create_database_backup_keyboard()
            else:
                message = "❌ Мониторинг бэкапов БД отключен"
                keyboard = create_main_backup_keyboard()

        elif query.data == 'db_backups_detailed':
            print(f"🔍 DEBUG: Обрабатываем db_backups_detailed")
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('database_backup_monitor'):
                message = format_detailed_database_backups(backup_bot, 24)
                keyboard = create_database_backup_keyboard()
            else:
                message = "❌ Мониторинг бэкапов БД отключен"
                keyboard = create_main_backup_keyboard()

        elif query.data == 'db_backups_list':
            print(f"🔍 DEBUG: Обрабатываем db_backups_list")
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('database_backup_monitor'):
                message = get_database_list(backup_bot, 24)
                keyboard = create_database_list_keyboard(backup_bot, 24)
            else:
                message = "❌ Мониторинг бэкапов БД отключен"
                keyboard = create_main_backup_keyboard()

        elif query.data == 'db_backups_48h':
            print(f"🔍 DEBUG: Обрабатываем db_backups_48h")
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('database_backup_monitor'):
                message = format_database_backups_report(backup_bot, 48)
                keyboard = create_database_backup_keyboard()
            else:
                message = "❌ Мониторинг бэкапов БД отключен"
                keyboard = create_main_backup_keyboard()

        # Обработка детального просмотра конкретной БД
        elif query.data.startswith('db_detail_'):
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('database_backup_monitor'):
                # Извлекаем тип и имя БД из callback_data
                parts = query.data.replace('db_detail_', '').split('_', 1)
                if len(parts) == 2:
                    backup_type = parts[0]
                    db_name = parts[1]
                    message = format_database_details(backup_bot, backup_type, db_name, 24)
                    keyboard = create_database_detail_keyboard(backup_type, db_name)
                else:
                    message = "❌ Ошибка формата запроса"
                    keyboard = create_database_backup_keyboard()
            else:
                message = "❌ Мониторинг бэкапов БД отключен"
                keyboard = create_main_backup_keyboard()

        elif query.data == 'backup_main':
            message = "📊 Главное меню бэкапов\n\nВыберите тип бэкапов для просмотра:"
            keyboard = create_main_backup_keyboard()

        elif query.data == 'backup_proxmox':
            message = "🖥️ Бэкапы Proxmox\n\nВыберите период для просмотра:"
            keyboard = create_proxmox_backup_keyboard()

        elif query.data == 'backup_databases':
            from extensions.extension_manager import extension_manager
            if extension_manager.is_extension_enabled('database_backup_monitor'):
                message = "🗃️ Бэкапы баз данных\n\nВыберите тип отчета:"
                keyboard = create_database_backup_keyboard()
            else:
                message = "❌ Мониторинг бэкапов БД отключен\n\nВключите расширение '🗃️ Мониторинг бэкапов БД' в управлении расширениями."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛠️ Управление расширениями", callback_data='extensions_menu')],
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
                ])

        elif query.data == 'backup_today':
            message = format_backup_summary(backup_bot)
            keyboard = create_proxmox_backup_keyboard()

        elif query.data == 'backup_24h':
            message = format_recent_backups(backup_bot, 24)
            keyboard = create_proxmox_backup_keyboard()

        elif query.data == 'backup_failed':
            message = format_failed_backups(backup_bot, 1)
            keyboard = create_proxmox_backup_keyboard()

        elif query.data == 'backup_hosts':
            message = format_hosts_list(backup_bot)
            keyboard = create_hosts_keyboard(backup_bot)

        elif query.data == 'backup_help':
            # ИСПРАВЛЕНО: вместо присваивания функции вызываем ее
            help_text = """
🤖 Команды мониторинга бэкапов

/backup - Основная сводка за сегодня
/backup_search [host] - Поиск по конкретному серверу
/db_backups [hours] - Бэкапы баз данных (по умолчанию 24ч)
/backup_help - Эта справка

Кнопки управления:
📊 Сегодня - Сводка за текущий день
📅 24 часа - История за последние сутки
❌ Ошибки - Список неудачных бэкапов
📋 Все серверы - Выбор конкретного сервера
🗃️ Базы данных - Бэкапы СУБД и приложений
🔄 Обновить - Обновить данные

Примеры:
/backup - общая сводка
/backup_search pve13 - статус pve13
/db_backups 48 - бэкапы БД за 48 часов
"""
            message = help_text
            keyboard = create_main_backup_keyboard()

        elif query.data == 'backup_refresh':
            message = "📊 Главное меню бэкапов\n\nВыберите тип бэкапов для просмотра:"
            keyboard = create_main_backup_keyboard()

        else:
            message = "❌ Неизвестная команда"
            keyboard = create_main_backup_keyboard()

        # ДОБАВИМ ОТЛАДКУ ПЕРЕД ОТПРАВКОЙ
        print(f"🔍 DEBUG: Отправляем сообщение длиной {len(message)} символов")
        logger.info(f"🔍 DEBUG: Отправляем сообщение: {message[:100]}...")

        query.edit_message_text(
            text=message,
            parse_mode=None,
            reply_markup=keyboard
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при обработке запроса: {e}"
        print(f"🔍 DEBUG: ОШИБКА: {error_msg}")
        logger.error(error_msg)
        import traceback
        logger.error(f"🔍 DEBUG: Подробности ошибки: {traceback.format_exc()}")
        query.edit_message_text(error_msg)
        
def setup_backup_commands(dispatcher):
    """Настройка команд бота для мониторинга бэкапов"""
    from telegram.ext import CommandHandler, CallbackQueryHandler

    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler("backup", backup_command))
    dispatcher.add_handler(CommandHandler("backup_search", backup_search_command))
    dispatcher.add_handler(CommandHandler("db_backups", database_backups_command))
    dispatcher.add_handler(CommandHandler("backup_help", backup_help_command))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^backup_'))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^db_backups_'))
    dispatcher.add_handler(CallbackQueryHandler(backup_callback, pattern='^db_detail_'))

    logger.info("Команды мониторинга бэкапов зарегистрированы")

def database_backups_command(update, context):
    """Обработчик команды для просмотра бэкапов баз данных"""
    backup_bot = BackupMonitorBot()
    
    # По умолчанию показываем за 24 часа
    hours = 24
    if context.args:
        try:
            hours = int(context.args[0])
        except ValueError:
            update.message.reply_text("❌ Укажите корректное количество часов: /db_backups 24", parse_mode=None)
            return
    
    message = format_database_backups_report(backup_bot, hours)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_refresh')],
        [InlineKeyboardButton("📊 Proxmox бэкапы", callback_data='backup_today')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_today')]
    ])
    
    update.message.reply_text(
        message,
        parse_mode=None,
        reply_markup=keyboard
    )
