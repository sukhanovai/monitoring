"""
/extensions/backup_monitor/backup_handlers.py
Server Monitoring System v4.14.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for the backup bot
Система мониторинга серверов
Версия: 4.14.0
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики для бота бэкапов
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from backup_utils import DisplayFormatters

logger = logging.getLogger(__name__)
formatters = DisplayFormatters()

# === УТИЛИТЫ ДЛЯ СОЗДАНИЯ КЛАВИАТУР ===

def create_main_menu():
    """Создает главное меню бэкапов"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖥️ По хостам", callback_data='backup_hosts')],
        [InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')],
        [InlineKeyboardButton("↩️ Назад", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])

def create_navigation_buttons(back_button='backup_main', refresh_button=None, close=True):
    """Создает стандартные кнопки навигации"""
    buttons = []
    
    if refresh_button:
        buttons.append([InlineKeyboardButton("🔄 Обновить", callback_data=refresh_button)])
    
    buttons.append([InlineKeyboardButton("↩️ Назад", callback_data=back_button)])
    
    if close:
        buttons.append([InlineKeyboardButton("✖️ Закрыть", callback_data='close')])
    
    return InlineKeyboardMarkup(buttons)

def create_hosts_keyboard(hosts, host_statuses, show_problems_button=True):
    """Создает клавиатуру для списка хостов"""
    keyboard = []
    
    # Статистика
    success_count = sum(1 for status in host_statuses.values() if status == 'success')
    problem_count = len(hosts) - success_count
    
    keyboard.append([InlineKeyboardButton(
        f"📊 Статус: {success_count}✅ {problem_count}🚨",
        callback_data='no_action'
    )])
    keyboard.append([])
    
    # Сортируем хосты по статусу
    sorted_hosts = sorted(hosts, key=lambda x: (
        host_statuses[x] != "failed",
        host_statuses[x] != "recent_failed", 
        host_statuses[x] != "stale",
        host_statuses[x] != "old",
        x.lower()
    ))
    
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(sorted_hosts), 2):
        row = []
        for j in range(2):
            if i + j < len(sorted_hosts):
                host_name = sorted_hosts[i + j]
                status = host_statuses[host_name]
                display_name = formatters.get_host_display_name(host_name, status)
                row.append(InlineKeyboardButton(display_name, callback_data=f'backup_host_{host_name}'))
        if row:
            keyboard.append(row)
    
    # Кнопка проблемных хостов
    if show_problems_button and problem_count > 0:
        keyboard.append([InlineKeyboardButton(
            f"🔍 Показать проблемные ({problem_count})", 
            callback_data='backup_stale_hosts'
        )])
    
    keyboard.append([
        InlineKeyboardButton("↩️ Назад", callback_data='backup_main'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close')
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_databases_keyboard(databases_by_type, problem_db_count=0):
    """Создает клавиатуру для списка баз данных"""
    keyboard = []
    
    # Добавляем секции для каждого типа
    for backup_type, databases in databases_by_type.items():
        if databases:
            # Статистика для типа
            type_success = sum(1 for db in databases if db['status'] == 'success')
            type_total = len(databases)
            
            keyboard.append([InlineKeyboardButton(
                f"───── {formatters.get_type_display(backup_type)} ({type_success}✅ {type_total-type_success}🚨) ─────",
                callback_data='no_action'
            )])
            
            # Кнопки баз данных
            current_row = []
            for i, db_info in enumerate(sorted(databases, key=lambda x: x['display_name'])):
                display_name = formatters.get_db_display_name(db_info['display_name'], db_info['status'])
                
                current_row.append(InlineKeyboardButton(
                    display_name, 
                    callback_data=f'db_detail_{backup_type}__{db_info["original_name"]}'
                ))
                
                # Размещаем по 2 кнопки в строке
                if len(current_row) == 2 or i == len(databases) - 1:
                    keyboard.append(current_row)
                    current_row = []
            
            keyboard.append([])  # Пустая строка между секциями
    
    # Убираем последнюю пустую строку
    if keyboard and not keyboard[-1]:
        keyboard.pop()
    
    # Кнопки управления
    keyboard.extend([
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_databases')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

# === ОСНОВНЫЕ ОБРАБОТЧИКИ ===

def show_main_menu(query):
    """Показывает главное меню бэкапов"""
    query.edit_message_text(
        "💾 *Мониторинг бэкапов Proxmox*\n\nВыберите опцию:",
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

def show_today_status(query, backup_bot):
    """Показывает статус бэкапов за сегодня"""
    try:
        results = backup_bot.get_today_status()
        
        if not results:
            query.edit_message_text(
                "📊 *Бэкапы за сегодня*\n\nНет данных за сегодня",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(refresh_button='backup_today')
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
            reply_markup=create_navigation_buttons(refresh_button='backup_today')
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
                reply_markup=create_navigation_buttons(refresh_button='backup_24h')
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
            reply_markup=create_navigation_buttons(refresh_button='backup_24h')
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
                reply_markup=create_navigation_buttons(refresh_button='backup_failed')
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
            reply_markup=create_navigation_buttons(refresh_button='backup_failed')
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
                reply_markup=create_navigation_buttons()
            )
            return

        # Получаем статусы для всех хостов
        host_statuses = {}
        for host_name in hosts:
            status = backup_bot.get_host_display_status(host_name)
            host_statuses[host_name] = status

        # Создаем сообщение с легендой
        message = "🖥️ *Выберите хост для просмотра бэкапов:*\n\n"
        message += "*Легенда:*\n"
        message += "✅ - все бэкапы успешны\n"
        message += "🔴 - последний бэкап неудачен\n"
        message += "🟠 - есть неудачные бэкапы в истории\n"
        message += "🟡 - последний бэкап старше 24ч\n"
        message += "⚫ - нет бэкапов >48ч\n"
        message += "⚪ - статус неизвестен\n\n"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_hosts_keyboard(hosts, host_statuses)
        )

    except Exception as e:
        logger.error(f"Ошибка в show_hosts_menu: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_stale_hosts(query, backup_bot):
    """Показывает только проблемные хосты"""
    try:
        hosts = backup_bot.get_all_hosts()
        problem_hosts = []
        
        for host_name in hosts:
            status = backup_bot.get_host_display_status(host_name)
            if status in ["failed", "recent_failed", "stale"]:
                recent = backup_bot.get_host_recent_status(host_name, 72)
                last_time = recent[0][1] if recent else None
                problem_hosts.append((host_name, status, last_time))
        
        if not problem_hosts:
            query.edit_message_text(
                "🎉 *Проблемные хосты*\n\nНет хостов с проблемными бэкапами!",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='backup_hosts')
            )
            return
        
        keyboard = []
        message = "🚨 *Проблемные хосты:*\n\n"
        
        # Сортируем по серьезности проблемы
        problem_hosts.sort(key=lambda x: (x[1] != "failed", x[1] != "recent_failed", x[1] != "stale"))
        
        for host_name, problem_type, last_backup in problem_hosts:
            time_ago = backup_bot.format_time_ago(last_backup)
            
            if problem_type == 'failed':
                problem_text = f"🔴 {host_name} - последний бэкап неудачен ({time_ago})"
            elif problem_type == 'recent_failed':
                problem_text = f"🟠 {host_name} - есть неудачные бэкапы ({time_ago})"
            else:
                problem_text = f"⚫ {host_name} - нет свежих бэкапов ({time_ago})"
            
            message += f"• {problem_text}\n"
            
            keyboard.append([InlineKeyboardButton(
                f"🔍 {host_name}", 
                callback_data=f'backup_host_{host_name}'
            )])
        
        message += f"\n*Всего проблемных хостов:* {len(problem_hosts)}"
        
        keyboard.extend([
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
                reply_markup=create_navigation_buttons(back_button='backup_hosts')
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
            reply_markup=create_navigation_buttons(
                back_button='backup_hosts', 
                refresh_button=None
            )
        )

    except Exception as e:
        logger.error(f"Ошибка в show_host_status: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def show_database_backups_menu(query, backup_bot):
    """Показывает меню бэкапов баз данных с прямым доступом к БД"""
    try:
        from app.config.settings import DATABASE_BACKUP_CONFIG
        
        # Создаем клавиатуру с кнопками для каждой БД
        keyboard = []
        
        # Используем правильную структуру из конфига
        config_mapping = [
            ('company_database', DATABASE_BACKUP_CONFIG.get("company_databases", {})),
            ('barnaul', DATABASE_BACKUP_CONFIG.get("barnaul_backups", {})),
            ('client', DATABASE_BACKUP_CONFIG.get("client_databases", {})),
            ('yandex', DATABASE_BACKUP_CONFIG.get("yandex_backups", {}))
        ]
        
        has_databases = False
        
        for backup_type, config_dict in config_mapping:
            if config_dict:
                has_databases = True
                
                # Добавляем заголовок типа
                type_display = formatters.get_type_display(backup_type)
                keyboard.append([InlineKeyboardButton(
                    f"───── {type_display} ─────",
                    callback_data='no_action'
                )])
                
                # Добавляем кнопки БД
                current_row = []
                for db_name, display_name in sorted(config_dict.items()):
                    try:
                        status = backup_bot.get_database_display_status(backup_type, db_name)
                        display_btn = formatters.get_db_display_name(display_name, status)
                        
                        current_row.append(InlineKeyboardButton(
                            display_btn,
                            callback_data=f'db_detail_{backup_type}__{db_name}'
                        ))
                        
                        # По 2 кнопки в строке
                        if len(current_row) == 2:
                            keyboard.append(current_row)
                            current_row = []
                    except Exception as e:
                        logger.error(f"❌ Ошибка обработки БД {db_name}: {e}")
                        continue
                
                if current_row:
                    keyboard.append(current_row)
                
                keyboard.append([])  # Пустая строка между типами
        
        # Если нет БД, показываем сообщение
        if not has_databases:
            message = "🗃️ *Бэкапы баз данных*\n\n❌ Нет настроенных баз данных в конфигурации."
            keyboard = [
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ]
        else:
            # Убираем последнюю пустую строку
            if keyboard and not keyboard[-1]:
                keyboard.pop()
            
            # Кнопки навигации - ИСПРАВЛЕНО: правильный callback_data
            keyboard.extend([
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main'),
                 InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ])
            
            message = "🗃️ *Бэкапы баз данных*\n\nВыберите базу данных для просмотра деталей:"
        
        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_menu: {e}")
        import traceback
        logger.error(traceback.format_exc())
        query.edit_message_text("❌ Ошибка при получении данных конфигурации БД")
                                
def show_stale_databases(query, backup_bot):
    """Показывает только проблемные базы данных"""
    try:
        from app.config.settings import DATABASE_BACKUP_CONFIG
        
        problem_databases = []
        
        # Проверяем все базы из конфигурации
        config_mapping = [
            ('company_database', DATABASE_BACKUP_CONFIG.get("company_databases", {})),
            ('barnaul', DATABASE_BACKUP_CONFIG.get("barnaul_backups", {})),
            ('client', DATABASE_BACKUP_CONFIG.get("client_databases", {})),
            ('yandex', DATABASE_BACKUP_CONFIG.get("yandex_backups", {}))
        ]
        
        for backup_type, config_dict in config_mapping:
            for db_name, display_name in config_dict.items():
                status = backup_bot.get_database_display_status(backup_type, db_name)
                if status not in ['success', 'unknown']:
                    recent = backup_bot.get_database_recent_status(backup_type, db_name, 72)
                    last_time = recent[0][1] if recent else None
                    problem_databases.append((backup_type, db_name, display_name, status, last_time))

        if not problem_databases:
            query.edit_message_text(
                "🎉 *Проблемные базы данных*\n\nНет БД с проблемными бэкапами!",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(back_button='db_backups_list')
            )
            return
        
        keyboard = []
        message = "🚨 *Проблемные базы данных:*\n\n"
        
        # Сортируем по серьезности проблемы
        problem_priority = {'failed': 1, 'recent_failed': 2, 'warning': 3, 'recent_errors': 4, 'stale': 5, 'old': 6}
        problem_databases.sort(key=lambda x: (problem_priority.get(x[3], 99), x[2]))
        
        for backup_type, db_name, display_name, problem_type, last_backup in problem_databases:
            type_icon = formatters.TYPE_ICONS.get(backup_type, '📁')
            time_ago = backup_bot.format_time_ago(last_backup)
            
            if problem_type == 'failed':
                problem_text = f"🔴 {type_icon} {display_name} - последний бэкап неудачен ({time_ago})"
            elif problem_type == 'recent_failed':
                problem_text = f"🟠 {type_icon} {display_name} - есть неудачные бэкапы ({time_ago})"
            elif problem_type in ['warning', 'recent_errors']:
                problem_text = f"🟡 {type_icon} {display_name} - есть ошибки в бэкапах ({time_ago})"
            elif problem_type == 'stale':
                problem_text = f"⚫ {type_icon} {display_name} - нет свежих бэкапов ({time_ago})"
            elif problem_type == 'old':
                problem_text = f"🟡 {type_icon} {display_name} - бэкапы устарели ({time_ago})"
            else:
                problem_text = f"⚪ {type_icon} {display_name} - проблема ({time_ago})"
            
            message += f"• {problem_text}\n"
            
            keyboard.append([InlineKeyboardButton(
                f"🔍 {display_name}", 
                callback_data=f'db_detail_{backup_type}__{db_name}'
            )])
        
        message += f"\n*Всего проблемных БД:* {len(problem_databases)}"
        
        keyboard.extend([
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

def show_database_backups_summary(query, backup_bot, hours):
    """Показывает сводку по бэкапам БД"""
    try:
        stats = backup_bot.get_database_backups_stats(hours)
        
        if not stats:
            query.edit_message_text(
                f"📊 *Бэкапы БД ({hours}ч)*\n\nНет данных за последние {hours} часов",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(
                    back_button='backup_databases',
                    refresh_button=f'db_backups_{hours}h'
                )
            )
            return

        message = f"📊 *Бэкапы БД ({hours}ч)*\n\n"
        
        # Группируем по типам
        by_type = {}
        for backup_type, db_name, db_display, status, count, last_backup in stats:
            if backup_type not in by_type:
                by_type[backup_type] = []
            by_type[backup_type].append((db_name, db_display, status, count, last_backup))

        for backup_type, databases in by_type.items():
            type_display = formatters.get_type_display(backup_type)
            message += f"*{type_display}:*\n"
            
            # Группируем по базам
            db_stats = {}
            for db_name, db_display, status, count, last_backup in databases:
                if db_name not in db_stats:
                    db_stats[db_name] = {'success': 0, 'failed': 0, 'display_name': db_display}
                db_stats[db_name][status] += count
            
            for db_name, stats_info in db_stats.items():
                success = stats_info.get('success', 0)
                failed = stats_info.get('failed', 0)
                total = success + failed
                
                if total > 0:
                    success_rate = (success / total) * 100
                    status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
                    display_name = stats_info.get('display_name', db_name)
                    message += f"{status_icon} {display_name}: {success}/{total} ({success_rate:.1f}%)\n"
            
            message += "\n"

        message += f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='backup_databases',
                refresh_button=f'db_backups_{hours}h'
            )
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_summary: {e}")
        query.edit_message_text("❌ Ошибка при получении данных")

def format_database_details(backup_bot, backup_type, db_name, hours=168):
    """Форматирует детальную информацию по БД"""
    try:
        display_names = backup_bot.get_database_display_names()
        display_name = display_names.get(db_name, db_name)
        
        details = backup_bot.get_database_details(backup_type, db_name, hours)
        
        if not details:
            return f"📋 Детали по {display_name}\n\nНет данных за последние {hours} часов"
                
        type_display = formatters.get_type_display(backup_type)
        
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
            
            task_display = task_type_names.get(task_type, task_type or 'Резервное копирование')
            
            message += f"{status_icon} *{time_str}* - {status} - {task_display}"
            if error_count and error_count > 0:
                message += f" (ошибок: {error_count})"
            message += "\n"
        
        message += f"\n🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
        return message
        
    except Exception as e:
        logger.error(f"Ошибка в format_database_details: {e}")
        return f"❌ Ошибка при получении деталей БД: {e}"

def show_database_details(query, backup_bot, backup_type, db_name):
    """Показывает детальную информацию по БД"""
    try:
        details_text = format_database_details(backup_bot, backup_type, db_name, 168)
        
        query.edit_message_text(
            details_text,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='db_backups_list',
                refresh_button=f'db_detail_{backup_type}__{db_name}'
            )
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_details: {e}")
        query.edit_message_text("❌ Ошибка при получении деталей БД")
        