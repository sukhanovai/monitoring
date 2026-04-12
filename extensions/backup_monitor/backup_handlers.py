"""
/extensions/backup_monitor/backup_handlers.py
Server Monitoring System v8.50.57
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Handlers for the backup bot
Система мониторинга серверов
Версия: 8.50.57
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики для бота бэкапов
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from extensions.extension_manager import extension_manager
from .backup_utils import DisplayFormatters
formatters = DisplayFormatters()
from telegram.utils.helpers import escape_markdown

def _md(s) -> str:
    return escape_markdown(str(s or ""), version=1)

logger = logging.getLogger(__name__)

# === УТИЛИТЫ ДЛЯ СОЗДАНИЯ КЛАВИАТУР ===

def create_main_menu():
    """Создает главное меню бэкапов"""
    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([InlineKeyboardButton("💾 Бэкапы Proxmox", callback_data='backup_proxmox')])

    if extension_manager.is_extension_enabled('database_backup_monitor'):
        keyboard.append([InlineKeyboardButton("🗃️ Бэкапы БД", callback_data='backup_databases')])

    if extension_manager.is_extension_enabled('mail_backup_monitor'):
        keyboard.append([InlineKeyboardButton("📬 Бэкапы почты", callback_data='backup_mail')])

    if extension_manager.is_extension_enabled('stock_load_monitor'):
        keyboard.append([InlineKeyboardButton("📦 Остатки 1С", callback_data='backup_stock_loads')])

    keyboard.extend([
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])

    return InlineKeyboardMarkup(keyboard)

def create_proxmox_menu():
    """Создает меню бэкапов Proxmox"""
    keyboard = []

    if extension_manager.is_extension_enabled('backup_monitor'):
        keyboard.append([
            InlineKeyboardButton("⚙️ Управление хостами", callback_data='backup_hosts_manage'),
            InlineKeyboardButton("⚙️ Настройка паттернов", callback_data='backup_proxmox_patterns'),
        ])

    keyboard.extend([
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])

    return InlineKeyboardMarkup(keyboard)

def create_proxmox_patterns_menu():
    """Создает меню настройки паттернов Proxmox."""
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать паттерны", callback_data='backup_proxmox_patterns')],
        [InlineKeyboardButton("🗑️ Удалить паттерны", callback_data='backup_proxmox_patterns')],
        [InlineKeyboardButton("➕ Добавить паттерн", callback_data='add_proxmox_pattern')],
        [InlineKeyboardButton("↩️ Назад", callback_data='backup_proxmox_menu')],
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_navigation_buttons(back_button='backup_main', refresh_button=None, close=True):
    """Создает стандартные кнопки навигации"""
    buttons = []
    
    if refresh_button:
        buttons.append([InlineKeyboardButton("🔄 Обновить", callback_data=refresh_button)])
    
    buttons.append([InlineKeyboardButton("↩️ Назад", callback_data=back_button)])
    buttons.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])
    
    if close:
        buttons.append([InlineKeyboardButton("✖️ Закрыть", callback_data='close')])
    
    return InlineKeyboardMarkup(buttons)

def create_hosts_keyboard(
    hosts,
    host_statuses,
    show_problems_button=True,
    back_button='backup_main',
):
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
    
    keyboard.append([
        InlineKeyboardButton("⚙️ Управление хостами", callback_data='backup_hosts_manage'),
        InlineKeyboardButton("⚙️ Настройка паттернов", callback_data='backup_proxmox_patterns'),
    ])

    navigation_row = [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]
    if back_button:
        navigation_row.insert(0, InlineKeyboardButton("↩️ Назад", callback_data=back_button))
    navigation_row.append(InlineKeyboardButton("✖️ Закрыть", callback_data='close'))
    keyboard.append(navigation_row)
    
    return InlineKeyboardMarkup(keyboard)

def create_hosts_management_keyboard(hosts, backup_bot):
    """Создает клавиатуру управления хостами Proxmox."""
    keyboard = [[InlineKeyboardButton("➕ Добавить новый хост", callback_data='backup_host_add_prompt')]]

    for host_name in hosts:
        enabled = backup_bot.is_host_enabled(host_name)
        toggle_text = "⛔ Деактивировать" if enabled else "✅ Активировать"
        keyboard.append([
            InlineKeyboardButton(f"✏️ {host_name}", callback_data=f'backup_host_edit_prompt_{host_name}'),
            InlineKeyboardButton(f"🗑️ {host_name}", callback_data=f'backup_host_delete_{host_name}'),
        ])
        keyboard.append([
            InlineKeyboardButton(f"{toggle_text} {host_name}", callback_data=f'backup_host_toggle_{host_name}')
        ])

    keyboard.append([
        InlineKeyboardButton("↩️ Назад к хостам", callback_data='backup_hosts'),
        InlineKeyboardButton("🏠 На главную", callback_data='main_menu'),
        InlineKeyboardButton("✖️ Закрыть", callback_data='close'),
    ])
    return InlineKeyboardMarkup(keyboard)

def show_hosts_management_menu(query, backup_bot):
    """Показывает меню управления хостами Proxmox."""
    hosts = backup_bot.get_all_hosts(include_disabled=True)
    message = "⚙️ *Управление хостами Proxmox*\n\n"
    if not hosts:
        message += "Список пуст. Добавьте первый хост."
    else:
        message += "🟢 — активен\n🔴 — деактивирован\n\n"
        for host_name in hosts:
            status_icon = "🟢" if backup_bot.is_host_enabled(host_name) else "🔴"
            message += f"{status_icon} `{host_name}`\n"

    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=create_hosts_management_keyboard(hosts, backup_bot),
    )

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
        [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ])
    
    return InlineKeyboardMarkup(keyboard)

# === ОСНОВНЫЕ ОБРАБОТЧИКИ ===

def show_main_menu(query, backup_bot):
    """Показывает главное меню бэкапов"""
    query.edit_message_text(
        "💾 *Мониторинг бэкапов Proxmox*\n\nВыберите опцию:",
        parse_mode='Markdown',
        reply_markup=create_main_menu()
    )

def show_proxmox_menu(query, backup_bot):
    """Показывает меню бэкапов Proxmox"""
    query.edit_message_text(
        "💾 *Бэкапы Proxmox*\n\nВыберите опцию:",
        parse_mode='Markdown',
        reply_markup=create_proxmox_menu()
    )

def show_proxmox_patterns_menu(query):
    """Показывает меню настройки паттернов Proxmox."""
    query.edit_message_text(
        "⚙️ *Настройка паттернов Proxmox*\n\n"
        "Выберите действие: редактирование, удаление или добавление нового паттерна.",
        parse_mode='Markdown',
        reply_markup=create_proxmox_patterns_menu(),
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
        hosts = backup_bot.get_all_hosts(include_disabled=True)
        
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
            if not backup_bot.is_host_enabled(host_name):
                status = 'disabled'
            else:
                status = backup_bot.get_host_display_status(host_name)
            host_statuses[host_name] = status

        # Создаем сообщение с легендой
        message = "🖥️ *Выберите хост для просмотра бэкапов:*\n\n"
        message += "*Легенда:*\n"
        message += "✅ - все бэкапы успешны\n"
        message += "🔴 - последний бэкап неудачен\n"
        message += "🟠 - есть неудачные бэкапы в истории\n"
        message += f"🟡 - последний бэкап старше {backup_bot.backup_alert_hours}ч\n"
        message += f"⚫ - нет бэкапов >{backup_bot.backup_stale_hours}ч\n"
        message += "⚪ - хост деактивирован или статус неизвестен\n\n"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_hosts_keyboard(
                hosts,
                host_statuses,
                back_button=None,
            )
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
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]
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

def _normalize_db_key(name: str) -> str:
    return str(name or "").replace("-", "_").lower()

def _normalize_backup_type(backup_type: str, db_name: str) -> str:
    if _normalize_db_key(db_name) == "trade" and backup_type == "client":
        return "company_database"
    return backup_type

def _normalize_config_backup_type(category: str) -> str:
    normalized = _normalize_db_key(category)
    if normalized in ("company", "company_database"):
        return "company_database"
    if normalized in ("barnaul", "barnaul_backups"):
        return "barnaul"
    if normalized in ("client", "client_databases"):
        return "client"
    if normalized in ("yandex", "yandex_backups"):
        return "yandex"
    return category


def _get_disabled_db_monitors() -> set[tuple[str, str]]:
    """Возвращает список отключённых пар (backup_type, db_name)."""
    try:
        from core.config_manager import config_manager

        raw_disabled = config_manager.get_setting("DATABASE_MONITORING_DISABLED", [], use_cache=False)
    except Exception:
        raw_disabled = []

    if isinstance(raw_disabled, str):
        raw_disabled = [raw_disabled]
    if not isinstance(raw_disabled, list):
        return set()

    disabled_pairs: set[tuple[str, str]] = set()
    for item in raw_disabled:
        value = str(item or "").strip()
        if "__" not in value:
            continue
        backup_type, db_name = value.split("__", 1)
        backup_type = backup_type.strip()
        db_name = db_name.strip()
        if backup_type and db_name:
            disabled_pairs.add((backup_type, db_name))
    return disabled_pairs


def _toggle_database_monitoring(backup_type: str, db_name: str) -> bool:
    """Переключает мониторинг БД; возвращает True, если мониторинг включен после переключения."""
    disabled_pairs = _get_disabled_db_monitors()
    pair = (backup_type, db_name)

    if pair in disabled_pairs:
        disabled_pairs.remove(pair)
        now_enabled = True
    else:
        disabled_pairs.add(pair)
        now_enabled = False

    serialized = sorted(f"{item_type}__{item_name}" for item_type, item_name in disabled_pairs)
    from core.config_manager import config_manager
    config_manager.set_setting("DATABASE_MONITORING_DISABLED", serialized, "backup", data_type="auto")
    return now_enabled

def get_database_monitor_snapshot(backup_bot):
    """Возвращает унифицированный список БД и статусов из settings DB + backups DB."""
    from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG

    config = DATABASE_BACKUP_CONFIG if isinstance(DATABASE_BACKUP_CONFIG, dict) else {}
    disabled_pairs = _get_disabled_db_monitors()

    rows = backup_bot.execute_query(
        """
        SELECT DISTINCT
            backup_type,
            database_name,
            COALESCE(database_display_name, '')
        FROM database_backups
        ORDER BY backup_type, database_name
        """,
        ()
    ) or []

    entries_by_type = {}
    allowed_by_type = {}

    for category, databases in config.items():
        if not isinstance(databases, dict):
            continue
        backup_type = _normalize_config_backup_type(category)
        allowed_by_type.setdefault(backup_type, set())
        bucket = entries_by_type.setdefault(backup_type, {})
        for db_name, configured_label in databases.items():
            normalized_key = _normalize_db_key(db_name)
            allowed_by_type[backup_type].add(normalized_key)
            if normalized_key not in bucket:
                bucket[normalized_key] = {
                    "backup_type": backup_type,
                    "db_name": str(db_name),
                    "display_name": str(configured_label or db_name),
                    "category": category,
                    "db_key": db_name,
                }

    for raw_backup_type, raw_db_name, raw_display_name in rows:
        if not raw_backup_type or not raw_db_name:
            continue
        backup_type = _normalize_backup_type(raw_backup_type, raw_db_name)
        normalized_key = _normalize_db_key(raw_db_name)
        if backup_type not in allowed_by_type or normalized_key not in allowed_by_type[backup_type]:
            continue

        bucket = entries_by_type.setdefault(backup_type, {})
        existing = bucket.get(normalized_key)
        if existing is None:
            bucket[normalized_key] = {
                "backup_type": backup_type,
                "db_name": str(raw_db_name),
                "display_name": str(raw_display_name or raw_db_name),
            }
            continue
        if raw_display_name and str(raw_display_name).strip():
            existing["display_name"] = str(raw_display_name).strip()

    snapshot = []
    for backup_type in sorted(entries_by_type.keys()):
        for item in sorted(entries_by_type[backup_type].values(), key=lambda row: row["display_name"].lower()):
            db_name = item["db_name"]
            effective_type = _get_latest_backup_type(backup_bot, db_name, hours=48) or backup_type
            status = backup_bot.get_database_display_status(effective_type, db_name)
            item["status"] = status
            item["is_disabled"] = (backup_type, db_name) in disabled_pairs
            snapshot.append(item)

    return snapshot

DB_BACKUPS_MENU_PAGE_SIZE = 10000


def show_database_backups_menu(query, backup_bot, page=0):
    """Показывает меню с базами данных (из конфигурации и backups.db) на одной странице."""
    try:
        logger.info("🧪 BACKUP DB: entering show_database_backups_menu")

        snapshot = get_database_monitor_snapshot(backup_bot)
        entries = sorted(
            snapshot,
            key=lambda row: (row["backup_type"], row["display_name"].lower()),
        )

        if not entries:
            message = "🗃️ *Бэкапы баз данных*\n\n❌ Нет данных о бэкапах БД."
            keyboard = [
                [InlineKeyboardButton("🛠️ Управление базами", callback_data='settings_db_view_all_from_backup')],
                [InlineKeyboardButton("🗂️ Управление категориями", callback_data='settings_db_manage_categories_from_backup')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]
            ]
            try:
                query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except BadRequest as exc:
                if "Message is not modified" in str(exc):
                    query.answer("Меню уже открыто", show_alert=False)
                    return
                raise
            return

        total_pages = 1
        safe_page = max(0, min(int(page or 0), total_pages - 1))
        start = safe_page * DB_BACKUPS_MENU_PAGE_SIZE
        end = start + DB_BACKUPS_MENU_PAGE_SIZE
        page_entries = entries[start:end]

        keyboard = []
        previous_type = None
        pending_row = []
        for entry in page_entries:
            backup_type = entry["backup_type"]
            db_name = entry["db_name"]
            display_name = entry["display_name"]

            if backup_type != previous_type:
                if pending_row:
                    keyboard.append(pending_row)
                    pending_row = []
                type_display = formatters.get_type_display(backup_type)
                keyboard.append([InlineKeyboardButton(
                    f"───── {type_display} ─────",
                    callback_data='no_action'
                )])
                previous_type = backup_type

            try:
                status = entry["status"]
                is_disabled = entry["is_disabled"]
                display_btn = (
                    f"⚪ {display_name}"
                    if is_disabled
                    else formatters.get_db_display_name(display_name, status)
                )

                pending_row.append(InlineKeyboardButton(
                    display_btn,
                    callback_data=f'db_detail_{backup_type}__{db_name}'
                ))
                if len(pending_row) == 2:
                    keyboard.append(pending_row)
                    pending_row = []
            except Exception as e:
                logger.error(f"❌ Ошибка обработки БД {backup_type}/{db_name}: {e}")
                continue

        if pending_row:
            keyboard.append(pending_row)

        keyboard.extend([
            [InlineKeyboardButton("🛠️ Управление базами", callback_data='settings_db_view_all_from_backup')],
            [InlineKeyboardButton("🗂️ Управление категориями", callback_data='settings_db_manage_categories_from_backup')],
            [InlineKeyboardButton("⚙️ Настройка паттернов", callback_data='settings_patterns_db_from_backup')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')]
        ])

        message = "🗃️ *Бэкапы баз данных*\n\n"
        message += "*Легенда:*\n"
        message += "✅ - все бэкапы успешны\n"
        message += "🔴 - последний бэкап неудачен\n"
        message += "🟠 - есть неудачные бэкапы в истории\n"
        message += "🟡 - есть ошибки или последний бэкап старше 24ч\n"
        message += "⚫ - нет бэкапов >48ч\n"
        message += "⚪ - мониторинг базы отключён\n\n"
        message += "Выберите базу данных для просмотра деталей:"
        try:
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as exc:
            if "Message is not modified" in str(exc):
                query.answer("Меню уже открыто", show_alert=False)
                return
            raise

    except Exception as e:
        logger.error(f"Ошибка в show_database_backups_menu: {e}")
        import traceback
        logger.error(traceback.format_exc())
        query.edit_message_text("❌ Ошибка при формировании меню баз данных")

def show_mail_backups(query, backup_bot, hours=72):
    """Показывает последние бэкапы почтового сервера"""
    try:
        backups = backup_bot.get_mail_backups(hours=hours, limit=10)

        if not backups:
            message = (
                "📬 *Бэкапы почтового сервера*\n\n"
                f"❌ Нет данных за последние {hours} часов."
            )
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚙️ Настройка паттернов почты", callback_data='backup_mail_patterns')],
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
                ])
            )
            return

        message = f"📬 *Бэкапы почтового сервера (за {hours}ч)*\n\n"
        for status, size, path, received_at in backups:
            status_icon = "✅" if status == "success" else "❌"
            time_ago = backup_bot.format_time_ago(received_at)
            size_text = _md(size) if size else "—"
            path_text = _md(path) if path else "—"
            message += f"{status_icon} {size_text} — {path_text} ({_md(time_ago)})\n"

        navigation = [
            [InlineKeyboardButton("⚙️ Настройка паттернов почты", callback_data='backup_mail_patterns')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
        ]

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(navigation)
        )

    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            query.answer("Меню уже открыто", show_alert=False)
            return
        raise
    except Exception as e:
        logger.error(f"Ошибка в show_mail_backups: {e}")
        query.edit_message_text("❌ Ошибка при получении данных по почтовым бэкапам")

def show_stock_loads(query, backup_bot, hours=24):
    """Показывает результаты загрузки остатков 1С."""
    try:
        results = backup_bot.get_stock_loads(hours=hours)

        if not results:
            message = (
                "📦 *Загрузка остатков 1С*\n\n"
                f"❌ Нет данных за последние {hours} часов."
            )
            query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚙️ Настройка паттернов почты", callback_data='backup_mail_patterns')],
                    [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
                ])
            )
            return

        grouped = {}
        for source_name, supplier, status, rows_count, error_sample, received_at in results:
            grouped.setdefault(source_name or "Основное предприятие", []).append(
                (supplier, status, rows_count, error_sample, received_at)
            )

        total_suppliers = sum(len(items) for items in grouped.values())
        message = f"📦 *Загрузка остатков 1С (за {hours}ч)*\n"
        message += f"Всего поставщиков: {total_suppliers}\n\n"

        for source_name, items in grouped.items():
            message += f"*{_md(source_name)}* ({len(items)})\n"
            for supplier, status, rows_count, error_sample, received_at in items:
                status_icon = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
                time_ago = backup_bot.format_time_ago(received_at)
                rows_text = f"{rows_count} строк" if rows_count else "строки: —"
                error_text = f" — {error_sample}" if error_sample else ""
                message += f"{status_icon} {_md(supplier)} ({rows_text}){error_text} ({_md(time_ago)})\n"
            message += "\n"

        query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=create_navigation_buttons(
                back_button='main_menu',
                refresh_button='backup_stock_loads'
            )
        )

    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            query.answer("Меню уже открыто", show_alert=False)
            return
        raise
    except Exception as e:
        logger.error(f"Ошибка в show_stock_loads: {e}")
        query.edit_message_text("❌ Ошибка при получении данных по остаткам")
                                
def show_stale_databases(query, backup_bot):
    """Показывает только проблемные базы данных"""
    try:
        from .db_settings_backup_monitor import DATABASE_BACKUP_CONFIG
        
        problem_databases = []
        disabled_pairs = _get_disabled_db_monitors()
        
        # Проверяем все базы из конфигурации
        config_mapping = []
        for category, databases in DATABASE_BACKUP_CONFIG.items():
            if not isinstance(databases, dict):
                continue
            config_mapping.append((_normalize_config_backup_type(category), databases))

        for backup_type, config_dict in config_mapping:
            for db_name in config_dict.keys():
                if (backup_type, db_name) in disabled_pairs:
                    continue
                status = backup_bot.get_database_display_status(backup_type, db_name)
                if status not in ['success', 'unknown']:
                    recent = backup_bot.get_database_recent_status(backup_type, db_name, 72)
                    last_time = recent[0][1] if recent else None
                    problem_databases.append((backup_type, db_name, db_name, status, last_time))

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
        disabled_pairs = _get_disabled_db_monitors()
        for backup_type, db_name, db_display, status, count, last_backup in stats:
            normalized_type = _normalize_backup_type(backup_type, db_name)
            if (normalized_type, db_name) in disabled_pairs:
                continue
            if normalized_type not in by_type:
                by_type[normalized_type] = []
            by_type[normalized_type].append((db_name, db_display, status, count, last_backup))

        if not by_type:
            query.edit_message_text(
                f"📊 *Бэкапы БД ({hours}ч)*\n\nВсе базы сейчас исключены из мониторинга.",
                parse_mode='Markdown',
                reply_markup=create_navigation_buttons(
                    back_button='backup_databases',
                    refresh_button=f'db_backups_{hours}h'
                )
            )
            return

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

def _esc_md(text: str) -> str:
    """Экранирует спецсимволы Markdown (parse_mode='Markdown')."""
    if text is None:
        return ""
    s = str(text)
    # для Markdown v1 достаточно экранировать базовые символы
    return (s.replace("\\", "\\\\")
             .replace("_", "\\_")
             .replace("*", "\\*")
             .replace("[", "\\[")
             .replace("`", "\\`"))

def _get_latest_database_display_name(backup_bot, backup_type, db_name):
    try:
        rows = backup_bot.execute_query(
            """
            SELECT database_display_name
            FROM database_backups
            WHERE backup_type = ? AND database_name = ?
              AND database_display_name IS NOT NULL
              AND TRIM(database_display_name) != ''
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (backup_type, db_name),
        )
        if rows:
            return rows[0][0]
    except Exception as e:
        logger.error(f"Ошибка получения display_name для {backup_type}/{db_name}: {e}")
    return None


def _get_latest_backup_type(backup_bot, db_name, hours=168):
    try:
        since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        rows = backup_bot.execute_query(
            """
            SELECT backup_type
            FROM database_backups
            WHERE database_name = ? AND received_at >= ?
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (db_name, since_time),
        )
        if rows:
            return rows[0][0]
    except Exception as e:
        logger.error(f"Ошибка получения backup_type для {db_name}: {e}")
    return None


def _get_client_suffix(display_name: str | None) -> str | None:
    if not display_name:
        return None
    if "КС" in display_name.split():
        return "КС"
    if "Рубикон" in display_name:
        return "Рубикон"
    return None


def _get_details_display_name(backup_bot, backup_type, db_name):
    base_name = db_name
    if backup_type == "barnaul":
        return f"{base_name} Барнаул"
    if backup_type == "client":
        display_name = _get_latest_database_display_name(backup_bot, backup_type, db_name)
        client_suffix = _get_client_suffix(display_name)
        if client_suffix:
            return f"{base_name} {client_suffix}"
    return base_name


def format_database_details(backup_bot, backup_type, db_name, hours=168):
    """Форматирует детальную информацию по БД."""
    try:
        requested_type = backup_type
        display_name = _get_details_display_name(backup_bot, requested_type, db_name)

        details = backup_bot.get_database_details(backup_type, db_name, hours)
        if not details:
            fallback_type = _get_latest_backup_type(backup_bot, db_name, hours)
            if fallback_type and fallback_type != backup_type:
                details = backup_bot.get_database_details(fallback_type, db_name, hours)
        if not details:
            return f"📋 Детали по {_esc_md(display_name)}\n\nНет данных за последние {hours} часов"

        type_display = formatters.get_type_display(requested_type)

        message = f"📋 *Детали по {_esc_md(display_name)}*\n"
        message += f"*Тип:* {_esc_md(type_display)}\n"
        message += f"*Период:* {hours} часов\n\n"

        # expected tuple: (status, task_type, error_count, subject, received_at)
        success_count = sum(1 for d in details if d and d[0] == 'success')
        failed_count = sum(1 for d in details if d and d[0] == 'failed')
        total_count = len(details)

        message += "📊 *Статистика:*\n"
        message += f"✅ Успешных: {success_count}\n"
        message += f"❌ Ошибок: {failed_count}\n"
        message += f"📈 Всего: {total_count}\n\n"

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
            except Exception:
                time_str = (received_at or "")[:16]

            task_display = task_type_names.get(task_type, task_type or 'Резервное копирование')

            line = f"{status_icon} *{_esc_md(time_str)}* - {_esc_md(status)} - {_esc_md(task_display)}"
            if error_count and int(error_count) > 0:
                line += f" (ошибок: {int(error_count)})"
            message += line + "\n"

        message += f"\n🕒 *Обновлено:* {datetime.now().strftime('%H:%M:%S')}"
        return message

    except Exception as e:
        logger.exception(f"Ошибка в format_database_details: {e}")
        return f"❌ Ошибка при получении деталей БД: {e}"
    
def show_database_details(query, backup_bot, backup_type, db_name):
    """Показывает детальную информацию по БД"""
    try:
        details_text = format_database_details(backup_bot, backup_type, db_name, 168)
        
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад", callback_data='db_backups_list')],
            [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
        ])

        query.edit_message_text(
            details_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Ошибка в show_database_details: {e}")
        query.edit_message_text("❌ Ошибка при получении деталей БД")


def toggle_database_monitoring(query, backup_type, db_name):
    """Обработчик переключения мониторинга БД."""
    try:
        now_enabled = _toggle_database_monitoring(backup_type, db_name)
        state_text = "включён" if now_enabled else "отключён"
        query.answer(f"Мониторинг {state_text}", show_alert=False)
        query.edit_message_text(
            (
                f"🗃️ *{_esc_md(db_name)}* \\({_esc_md(backup_type)}\\)\n\n"
                f"Мониторинг: *{state_text}*\\.\n\n"
                "Нажмите «📋 Список БД», чтобы обновить список."
            ),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Список БД", callback_data='db_backups_list')],
                [InlineKeyboardButton("↩️ Назад", callback_data='backup_main')],
                [InlineKeyboardButton("🏠 На главную", callback_data='main_menu')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')],
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка переключения мониторинга БД: {e}")
        query.answer("❌ Не удалось переключить мониторинг", show_alert=True)
        
