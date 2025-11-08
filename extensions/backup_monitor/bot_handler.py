"""
Server Monitoring System v2.3.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Обработчик команд бота для мониторинга бэкапов
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

    def get_database_display_names(self):
        """Получает отображаемые имена баз данных из конфигурации"""
        from config import DATABASE_BACKUP_CONFIG
        
        display_names = {}
        
        # Основные базы компании
        for db_key, display_name in DATABASE_BACKUP_CONFIG["company_databases"].items():
            display_names[db_key] = display_name
        
        # Базы Барнаул
        for db_key, display_name in DATABASE_BACKUP_CONFIG["barnaul_backups"].items():
            display_names[db_key] = display_name
        
        # Клиентские базы
        for db_key, display_name in DATABASE_BACKUP_CONFIG["client_databases"].items():
            display_names[db_key] = display_name
        
        # Yandex базы
        for db_key, display_name in DATABASE_BACKUP_CONFIG["yandex_backups"].items():
            display_names[db_key] = display_name
        
        return display_names

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
        
    def get_database_backups_stats_fixed(self, hours=24):
        """Исправленная версия получения статистики по бэкапам БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"🔍 DEBUG: Запрос данных с {since_time}")
        
        # ИСПРАВЛЕННЫЙ ЗАПРОС - правильное количество полей
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
        
        print(f"🔍 DEBUG: get_database_backups_stats_fixed вернула {len(results)} записей")
        
        # Группируем результаты по типам для отладки
        type_stats = {}
        for backup_type, db_name, db_display, status, count, last_backup in results:
            if backup_type not in type_stats:
                type_stats[backup_type] = 0
            type_stats[backup_type] += 1
        
        print(f"🔍 DEBUG: Распределение по типам: {type_stats}")
        
        return results

    def get_stale_proxmox_backups(self, hours_threshold=24):
        """Получает хосты, у которых не было бэкапов более указанного времени"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold_time = (datetime.now() - timedelta(hours=hours_threshold)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Получаем последний бэкап для каждого хоста
        cursor.execute('''
            SELECT 
                host_name,
                MAX(received_at) as last_backup
            FROM proxmox_backups 
            GROUP BY host_name
            HAVING last_backup < ?
            ORDER BY last_backup ASC
        ''', (threshold_time,))
        
        stale_hosts = cursor.fetchall()
        conn.close()
        
        return stale_hosts

    def get_stale_database_backups(self, hours_threshold=24):
        """Получает базы данных, у которых не было бэкапов более указанного времени"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold_time = (datetime.now() - timedelta(hours=hours_threshold)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Получаем последний бэкап для каждой базы данных
        cursor.execute('''
            SELECT 
                backup_type,
                database_name,
                database_display_name,
                MAX(received_at) as last_backup
            FROM database_backups 
            GROUP BY backup_type, database_name, database_display_name
            HAVING last_backup < ?
            ORDER BY last_backup ASC
        ''', (threshold_time,))
        
        stale_databases = cursor.fetchall()
        conn.close()
        
        return stale_databases

    def get_backup_coverage_report(self, hours_threshold=24):
        """Получает полный отчет о покрытии бэкапов - ОБНОВЛЕНО для дублирующих IP"""
        stale_hosts = self.get_stale_proxmox_backups(hours_threshold)
        stale_databases = self.get_stale_database_backups(hours_threshold)
        
        # Получаем все известные хосты из конфигурации
        from config import PROXMOX_HOSTS
        all_configured_hosts = list(PROXMOX_HOSTS.keys())
        
        # Получаем все известные базы из конфигурации
        from config import DATABASE_BACKUP_CONFIG
        all_configured_databases = []
        
        # Основные базы компании
        for db_key in DATABASE_BACKUP_CONFIG["company_databases"].keys():
            all_configured_databases.append(('company_database', db_key))
        
        # Базы Барнаул
        for db_key in DATABASE_BACKUP_CONFIG["barnaul_backups"].keys():
            all_configured_databases.append(('barnaul', db_key))
        
        # Клиентские базы
        for db_key in DATABASE_BACKUP_CONFIG["client_databases"].keys():
            all_configured_databases.append(('client', db_key))
        
        # Yandex базы
        for db_key in DATABASE_BACKUP_CONFIG["yandex_backups"].keys():
            all_configured_databases.append(('yandex', db_key))
        
        # ФИЛЬТРУЕМ дублирующиеся хосты для корректного отображения
        unique_stale_hosts = []
        seen_ips = set()
        
        for host_name, last_backup in stale_hosts:
            ip = PROXMOX_HOSTS.get(host_name)
            if ip not in seen_ips:
                unique_stale_hosts.append((host_name, last_backup))
                seen_ips.add(ip)
            else:
                # Для дублирующихся IP добавляем оба имени через запятую
                for i, (existing_host, existing_backup) in enumerate(unique_stale_hosts):
                    if PROXMOX_HOSTS.get(existing_host) == ip:
                        unique_stale_hosts[i] = (f"{existing_host}, {host_name}", last_backup)
                        break
        
        return {
            'stale_hosts': unique_stale_hosts,
            'stale_databases': stale_databases,
            'all_configured_hosts': all_configured_hosts,
            'all_configured_databases': all_configured_databases,
            'hours_threshold': hours_threshold
        }

def format_database_details(backup_bot, backup_type, db_name, hours=168):
    """ИСПРАВЛЕННАЯ ВЕРСИЯ: Детальная информация по конкретной базе данных"""
    try:
        print(f"🔍 DEBUG: Получен запрос для {backup_type}.{db_name}")
        
        # Получаем правильное отображаемое имя через метод класса
        display_names = backup_bot.get_database_display_names()
        display_name = display_names.get(db_name, db_name)
        
        # Получаем детальные данные
        details = backup_bot.get_database_details(backup_type, db_name, hours)
        
        print(f"🔍 DEBUG: Получено {len(details)} записей")
        
        if not details:
            return f"📋 Детали по {display_name}\n\nНет данных за последние {hours} часов"
                
        type_names = {
            'company_database': '🏢 Основная БД',
            'barnaul': '🏔️ Барнаул', 
            'client': '👥 Клиентская',
            'yandex': '☁️ Yandex'
        }
        
        type_display = type_names.get(backup_type, f"📁 {backup_type}")
        
        message = f"📋 *Детали по {display_name}*\n"
        message += f"*Тип:* {type_display}\n"
        message += f"*Период:* {hours} часов\n\n"
        
        # Статистика
        success_count = len([d for d in details if d[0] == 'success'])
        failed_count = len([d for d in details if d[0] == 'failed'])
        total_count = len(details)
        
        message += f"📊 *Статистика:*\n"
        message += f"✅ Успешных: {success_count}\n"
        message += f"❌ Ошибок: {failed_count}\n"
        message += f"📈 Всего: {total_count}\n\n"
        
        # Последние бэкапы
        message += "⏰ *Последние бэкапы:*\n"
        
        task_type_names = {
            'database_dump': 'Дамп БД',
            'client_database_dump': 'Дамп клиентской БД', 
            'cobian_backup': 'Резервное копирование',
            'yandex_backup': 'Yandex Backup'
        }
        
        for status, task_type, error_count, subject, received_at in details[:5]:
            status_icon = "✅" if status == 'success' else "❌"
            try:
                backup_time = datetime.strptime(received_at, '%Y-%m-%d %H:%M:%S')
                time_str = backup_time.strftime('%d.%m %H:%M')
            except:
                time_str = received_at[:16]
            
            # Преобразуем тип задачи в понятный формат
            task_display = task_type_names.get(task_type, task_type or 'Резервное копирование')
            
            message += f"{status_icon} *{time_str}* - {status} - {task_display}"
            if error_count and error_count > 0:
                message += f" (ошибок: {error_count})"
            message += "\n"
        
        message += f"\n🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
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
            [InlineKeyboardButton("🔄 Обновить", callback_data='backup_refresh')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
            show_main_menu(query)
        elif data == 'backup_databases':
            show_database_backups_menu(query, backup_bot)
        elif data == 'backup_proxmox':
            show_main_menu(query)
        elif data.startswith('backup_host_'):
            host_name = data.replace('backup_host_', '')
            show_host_status(query, backup_bot, host_name)
        elif data == 'backup_stale_hosts':
            show_stale_hosts(query, backup_bot)
        elif data.startswith('db_detail_'):
            # Обработка деталей БД - ИСПРАВЛЕННАЯ ВЕРСИЯ С ДВОЙНЫМ РАЗДЕЛИТЕЛЕМ
            try:
                # Убираем префикс
                remaining = data.replace('db_detail_', '')
                print(f"🔍 DEBUG: Обрабатываем db_detail, remaining={remaining}")
                
                # Используем двойное подчеркивание как разделитель
                if '__' in remaining:
                    parts = remaining.split('__', 1)  # Разделяем только на 2 части
                    backup_type = parts[0]
                    db_name = parts[1]
                    print(f"🔍 DEBUG: Извлечено backup_type={backup_type}, db_name={db_name}")
                    show_database_details(query, backup_bot, backup_type, db_name)
                else:
                    # Fallback: пробуем найти последнее подчеркивание
                    last_underscore = remaining.rfind('_')
                    if last_underscore != -1:
                        backup_type = remaining[:last_underscore]
                        db_name = remaining[last_underscore + 1:]
                        print(f"🔍 DEBUG: Fallback - backup_type={backup_type}, db_name={db_name}")
                        show_database_details(query, backup_bot, backup_type, db_name)
                    else:
                        print(f"❌ DEBUG: Не найден разделитель в: {remaining}")
                        query.edit_message_text("❌ Ошибка: неверный формат запроса")
                    
            except Exception as e:
                print(f"❌ DEBUG: Ошибка при разборе db_detail: {e}")
                query.edit_message_text("❌ Ошибка при обработке запроса")
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
        elif data == 'db_stale_list':
            show_stale_databases(query, backup_bot)
        elif data == 'backup_main':
            show_main_menu(query)

    except Exception as e:
        logger.error(f"Ошибка в backup_callback: {e}")
        try:
            query.edit_message_text("❌ Ошибка при обработке запроса")
        except:
            pass

def show_main_menu(query):
    """Показывает главное меню бэкапов с кнопкой закрыть"""
    keyboard = [
        [InlineKeyboardButton("📊 Сегодня", callback_data='backup_today')],
        [InlineKeyboardButton("⏰ 24 часа", callback_data='backup_24h')],
        [InlineKeyboardButton("❌ Ошибки", callback_data='backup_failed')],
        [InlineKeyboardButton("🖥️ По хостам", callback_data='backup_hosts')],
        [InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='backup_refresh')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_failed_backups: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_hosts_menu(query, backup_bot):
    """Показывает меню выбора хостов с отметкой об устаревших бэкапах"""
    try:
        hosts = backup_bot.get_all_hosts()
        
        # Получаем информацию об устаревших бэкапах
        coverage_report = backup_bot.get_backup_coverage_report(24)
        stale_hosts_dict = {host[0]: host[1] for host in coverage_report['stale_hosts']}
        
        if not hosts:
            query.edit_message_text(
                "🖥️ *Бэкапы по хостам*\n\nНет данных о хостах",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
            return

        keyboard = []
        
        # Добавляем заголовок с информацией об устаревших бэкапах
        stale_count = len(coverage_report['stale_hosts'])
        total_configured = len(coverage_report['all_configured_hosts'])
        
        if stale_count > 0:
            keyboard.append([InlineKeyboardButton(
                f"⚠️ {stale_count}/{total_configured} хостов без бэкапов >24ч",
                callback_data='no_action'
            )])
            keyboard.append([])  # Пустая строка для разделения
        
        # Создаем кнопки по 2 в ряд
        for i in range(0, len(hosts), 2):
            row = []
            if i < len(hosts):
                host_name = hosts[i]
                # Проверяем, есть ли у хоста устаревшие бэкапы
                if host_name in stale_hosts_dict:
                    display_name = f"🕒 {host_name}"
                    last_backup = stale_hosts_dict[host_name]
                    try:
                        last_time = datetime.strptime(last_backup, '%Y-%m-%d %H:%M:%S')
                        hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                        if hours_ago > 24:
                            display_name = f"❌ {host_name}"
                        elif hours_ago > 12:
                            display_name = f"🕒 {host_name}"
                    except:
                        display_name = f"🕒 {host_name}"
                else:
                    display_name = f"✅ {host_name}"
                
                row.append(InlineKeyboardButton(display_name, callback_data=f'backup_host_{host_name}'))
                
            if i + 1 < len(hosts):
                host_name = hosts[i + 1]
                if host_name in stale_hosts_dict:
                    display_name = f"🕒 {host_name}"
                    last_backup = stale_hosts_dict[host_name]
                    try:
                        last_time = datetime.strptime(last_backup, '%Y-%m-%d %H:%M:%S')
                        hours_ago = (datetime.now() - last_time).total_seconds() / 3600
                        if hours_ago > 24:
                            display_name = f"❌ {host_name}"
                        elif hours_ago > 12:
                            display_name = f"🕒 {host_name}"
                    except:
                        display_name = f"🕒 {host_name}"
                else:
                    display_name = f"✅ {host_name}"
                
                row.append(InlineKeyboardButton(display_name, callback_data=f'backup_host_{host_name}'))
            
            keyboard.append(row)
        
        # Добавляем кнопку для просмотра только проблемных хостов
        if stale_count > 0:
            keyboard.append([InlineKeyboardButton(
                f"🔍 Показать только проблемные ({stale_count})", 
                callback_data='backup_stale_hosts'
            )])
        
        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='backup_main')])

        message = "🖥️ *Выберите хост для просмотра бэкапов:*\n\n"
        message += "✅ - нормальные бэкапы\n"
        message += "🕒 - бэкапы >12 часов\n"
        message += "❌ - бэкапы >24 часов\n\n"
        message += f"*Статус:* {len(hosts) - stale_count}/{len(hosts)} хостов в норме"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка в show_hosts_menu: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_stale_hosts(query, backup_bot):
    """Показывает только хосты с устаревшими бэкапами"""
    try:
        coverage_report = backup_bot.get_backup_coverage_report(24)
        stale_hosts = coverage_report['stale_hosts']
        
        if not stale_hosts:
            query.edit_message_text(
                "🎉 *Проблемные хосты*\n\nНет хостов с устаревшими бэкапами!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_hosts')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
            return
        
        keyboard = []
        message = "❌ *Хосты без бэкапов более 24 часов:*\n\n"
        
        for host_name, last_backup in stale_hosts:
            try:
                last_time = datetime.strptime(last_backup, '%Y-%m-%d %H:%M:%S')
                hours_ago = int((datetime.now() - last_time).total_seconds() / 3600)
                days_ago = hours_ago // 24
                remaining_hours = hours_ago % 24
                
                if days_ago > 0:
                    time_ago = f"{days_ago}д {remaining_hours}ч"
                else:
                    time_ago = f"{hours_ago}ч"
                
                message += f"• {host_name} - {time_ago} назад\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"🔍 {host_name} ({time_ago})", 
                    callback_data=f'backup_host_{host_name}'
                )])
                
            except Exception as e:
                message += f"• {host_name} - ошибка времени\n"
        
        message += f"\n*Всего проблемных хостов:* {len(stale_hosts)}"
        
        keyboard.extend([
            [InlineKeyboardButton("🔄 Обновить", callback_data='backup_stale_hosts')],
            [InlineKeyboardButton("📋 Все хосты", callback_data='backup_hosts')],
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')]
        ])
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_stale_hosts: {e}")
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
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_hosts')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_hosts')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_host_status: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_backups_menu(query, backup_bot):
    """Показывает меню бэкапов баз данных с кнопкой закрыть"""
    keyboard = [
        [InlineKeyboardButton("📊 Сводка за 24ч", callback_data='db_backups_24h')],
        [InlineKeyboardButton("📈 Сводка за 48ч", callback_data='db_backups_48h')],
        [InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                    [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
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
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_summary: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_backups_list(query, backup_bot):
    """УЛУЧШЕННАЯ ВЕРСИЯ: Показывает список всех баз данных из конфигурации с отметкой об устаревших бэкапах"""
    try:
        # Получаем информацию об устаревших бэкапах
        coverage_report = backup_bot.get_backup_coverage_report(24)
        stale_databases_dict = {}
        for backup_type, db_name, db_display, last_backup in coverage_report['stale_databases']:
            stale_databases_dict[(backup_type, db_name)] = last_backup
        
        # Получаем все отображаемые имена из конфигурации
        display_names = backup_bot.get_database_display_names()
        print(f"🔍 DEBUG: Все базы из конфига: {list(display_names.keys())}")
        
        # Группируем базы по типам из конфигурации
        databases_by_type = {
            'company_database': [],
            'barnaul': [],
            'client': [],
            'yandex': []
        }
        
        # Получаем статистику за более длительный период (7 дней) чтобы увидеть все базы
        stats = backup_bot.get_database_backups_stats_fixed(168)  # 7 дней
        
        # Создаем словарь для статистики по базам
        db_stats = {}
        if stats:
            for backup_type, db_name, db_display, status, count, last_backup in stats:
                key = (backup_type, db_name)
                if key not in db_stats:
                    db_stats[key] = {'success': 0, 'failed': 0, 'last_backup': last_backup}
                db_stats[key][status] += count
        
        # Заполняем списки базами из конфигурации
        from config import DATABASE_BACKUP_CONFIG
        
        # Основные базы компании
        for db_name, display_name in DATABASE_BACKUP_CONFIG["company_databases"].items():
            key = ('company_database', db_name)
            stats_info = db_stats.get(key, {'success': 0, 'failed': 0, 'last_backup': None})
            databases_by_type['company_database'].append({
                'original_name': db_name,
                'display_name': display_name,
                'success': stats_info['success'],
                'failed': stats_info['failed'],
                'last_backup': stats_info['last_backup']
            })
        
        # Базы Барнаул
        for db_name, display_name in DATABASE_BACKUP_CONFIG["barnaul_backups"].items():
            key = ('barnaul', db_name)
            stats_info = db_stats.get(key, {'success': 0, 'failed': 0, 'last_backup': None})
            databases_by_type['barnaul'].append({
                'original_name': db_name,
                'display_name': display_name,
                'success': stats_info['success'],
                'failed': stats_info['failed'],
                'last_backup': stats_info['last_backup']
            })
        
        # Клиентские базы
        for db_name, display_name in DATABASE_BACKUP_CONFIG["client_databases"].items():
            key = ('client', db_name)
            stats_info = db_stats.get(key, {'success': 0, 'failed': 0, 'last_backup': None})
            databases_by_type['client'].append({
                'original_name': db_name,
                'display_name': display_name,
                'success': stats_info['success'],
                'failed': stats_info['failed'],
                'last_backup': stats_info['last_backup']
            })
        
        # Yandex базы
        for db_name, display_name in DATABASE_BACKUP_CONFIG["yandex_backups"].items():
            key = ('yandex', db_name)
            stats_info = db_stats.get(key, {'success': 0, 'failed': 0, 'last_backup': None})
            databases_by_type['yandex'].append({
                'original_name': db_name,
                'display_name': display_name,
                'success': stats_info['success'],
                'failed': stats_info['failed'],
                'last_backup': stats_info['last_backup']
            })

        print(f"🔍 DEBUG: Базы из конфига по типам: { {k: len(v) for k, v in databases_by_type.items()} }")
        
        # Создаем клавиатуру с группировкой по типам
        keyboard = []
        
        type_configs = {
            'company_database': {'icon': '🏢', 'name': 'Основные БД компании'},
            'barnaul': {'icon': '🏔️', 'name': 'Бэкапы Барнаул'}, 
            'client': {'icon': '👥', 'name': 'Базы клиентов'},
            'yandex': {'icon': '☁️', 'name': 'Бэкапы на Yandex'}
        }

        # Добавляем заголовки и кнопки для каждого типа
        sections_added = 0
        for backup_type, type_config in type_configs.items():
            databases = databases_by_type[backup_type]
            if databases:
                sections_added += 1
                # Добавляем заголовок секции
                keyboard.append([InlineKeyboardButton(
                    f"───── {type_config['icon']} {type_config['name']} ─────",
                    callback_data='no_action'
                )])
                
                print(f"🔍 DEBUG: Добавляем секцию '{backup_type}' с {len(databases)} базами")
                
                # Добавляем кнопки баз данных для этого типа
                current_row = []
                for i, db_info in enumerate(sorted(databases, key=lambda x: x['display_name'])):
                    success = db_info.get('success', 0)
                    failed = db_info.get('failed', 0)
                    total = success + failed
                    
                    display_name = db_info['display_name']
                    original_name = db_info['original_name']
                    
                    # Проверяем, есть ли у базы устаревшие бэкапы
                    is_stale = (backup_type, original_name) in stale_databases_dict
                    
                    if total > 0:
                        success_rate = (success / total) * 100
                        if is_stale:
                            status_icon = "❌"  # Бэкапов нет более 24 часов
                        elif success_rate >= 80:
                            status_icon = "✅"
                        elif success_rate >= 50:
                            status_icon = "🟡"
                        else:
                            status_icon = "🔴"
                        button_text = f"{status_icon} {display_name}"
                    else:
                        # Если вообще нет бэкапов
                        status_icon = "❌"
                        button_text = f"{status_icon} {display_name}"
                    
                    # Ограничиваем длину текста кнопки
                    if len(button_text) > 15:
                        button_text = button_text[:12] + ".."
                    
                    print(f"🔍 DEBUG: Создаем кнопку: {button_text} для {original_name}")
                    
                    current_row.append(InlineKeyboardButton(
                        button_text, 
                        callback_data=f'db_detail_{backup_type}__{original_name}'
                    ))
                    
                    # Размещаем по 2 кнопки в строке
                    if len(current_row) == 2 or i == len(databases) - 1:
                        keyboard.append(current_row)
                        current_row = []
                
                # Добавляем пустую строку между секциями для визуального разделения
                keyboard.append([])
        
        print(f"🔍 DEBUG: Добавлено секций: {sections_added}")
        
        # Убираем последнюю пустую строку если есть
        if keyboard and not keyboard[-1]:
            keyboard.pop()
        
        # Добавляем кнопку для просмотра только проблемных БД
        stale_db_count = len(coverage_report['stale_databases'])
        if stale_db_count > 0:
            keyboard.append([InlineKeyboardButton(
                f"🔍 Показать только проблемные БД ({stale_db_count})", 
                callback_data='db_stale_list'
            )])
        
        # Если нет ни одной базы данных, показываем сообщение
        if sections_added == 0:
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_list')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ]
            query.edit_message_text(
                "📋 *Список баз данных*\n\nНет данных о базах данных в конфигурации",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Добавляем кнопки управления
        keyboard.extend([
            [InlineKeyboardButton("🔄 Обновить", callback_data='db_backups_list')],
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])

        print(f"🔍 DEBUG: Итоговая клавиатура: {len(keyboard)} строк")
        
        query.edit_message_text(
            "📋 *Список баз данных*\n\n*Легенда:*\n✅ - нормальные бэкапы\n🟡 - есть проблемы\n🔴 - много ошибок\n❌ - нет бэкапов >24ч\n\n*Секции:*\n🏢 Основные БД компании\n🏔️ Бэкапы Барнаул\n👥 Базы клиентов\n☁️ Бэкапы на Yandex\n\nВыберите базу для просмотра деталей:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_list: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_stale_databases(query, backup_bot):
    """Показывает только базы данных с устаревшими бэкапами"""
    try:
        coverage_report = backup_bot.get_backup_coverage_report(24)
        stale_databases = coverage_report['stale_databases']
        
        if not stale_databases:
            query.edit_message_text(
                "🎉 *Проблемные базы данных*\n\nНет БД с устаревшими бэкапами!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='db_backups_list')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
            return
        
        keyboard = []
        message = "❌ *Базы данных без бэкапов более 24 часов:*\n\n"
        
        type_names = {
            'company_database': '🏢',
            'barnaul': '🏔️', 
            'client': '👥',
            'yandex': '☁️'
        }
        
        for backup_type, db_name, db_display, last_backup in stale_databases:
            try:
                last_time = datetime.strptime(last_backup, '%Y-%m-%d %H:%M:%S')
                hours_ago = int((datetime.now() - last_time).total_seconds() / 3600)
                days_ago = hours_ago // 24
                remaining_hours = hours_ago % 24
                
                if days_ago > 0:
                    time_ago = f"{days_ago}д {remaining_hours}ч"
                else:
                    time_ago = f"{hours_ago}ч"
                
                type_icon = type_names.get(backup_type, '📁')
                display_name = db_display or db_name
                
                message += f"• {type_icon} {display_name} - {time_ago} назад\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"🔍 {display_name} ({time_ago})", 
                    callback_data=f'db_detail_{backup_type}__{db_name}'
                )])
                
            except Exception as e:
                message += f"• {db_name} - ошибка времени\n"
        
        message += f"\n*Всего проблемных БД:* {len(stale_databases)}"
        
        keyboard.extend([
            [InlineKeyboardButton("🔄 Обновить", callback_data='db_stale_list')],
            [InlineKeyboardButton("📋 Все БД", callback_data='db_backups_list')],
            [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')]
        ])
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_stale_databases: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_details(query, backup_bot, backup_type, db_name):
    """Показывает детальную информацию по конкретной базе данных - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        print(f"🔍 DEBUG: show_database_details вызвана с backup_type={backup_type}, db_name={db_name}")
        
        details_text = format_database_details(backup_bot, backup_type, db_name, 168)
        
        query.edit_message_text(
            details_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data=f'db_detail_{backup_type}_{db_name}')],
                [InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_details: {e}")
        import traceback
        logger.error(f"Подробности: {traceback.format_exc()}")
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
