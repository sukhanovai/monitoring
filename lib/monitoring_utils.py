"""
/lib/monitoring_utils.py
Server Monitoring System v8.2.72
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Utilities: diagnostics, reports, statistics
Система мониторинга серверов
Версия: 8.2.72
Автор: Александр Суханов (c)
Лицензия: MIT
Утилиты: диагностика, отчеты, статистика
"""

import json
from datetime import datetime, timedelta
from config.settings import PROC_UPTIME_FILE, STATS_FILE, DATA_DIR

# === ДИАГНОСТИКА SSH (из single_check.py) ===

def diagnose_ssh_command(update, context):
    """Диагностика SSH подключения к конкретному серверу"""
    if not context.args:
        update.message.reply_text("❌ Укажите IP или имя сервера: /diagnose_ssh <ip>")
        return

    target = context.args[0]
    
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()
    server = None

    # Ищем сервер по IP или имени
    for s in servers:
        if s["ip"] == target or s["name"] == target:
            server = s
            break

    if not server:
        update.message.reply_text(f"❌ Сервер {target} не найден в списке мониторинга")
        return

    message = f"🔧 *Диагностика подключения для {server['name']} ({server['ip']})*:\n\n"

    try:
        # Проверка доступности порта
        port = 22
        from core.monitor_core import check_port
        is_port_open = check_port(server["ip"], port, timeout=10)
        message += f"Порт {port} (SSH): {'🟢 Открыт' if is_port_open else '🔴 Закрыт'}\n"

        if is_port_open:
            # Проверка SSH подключения
            from core.monitor_core import check_ssh, check_ssh_alternative
            
            message += "\n*Проверка Paramiko (основной метод):*\n"
            result1 = check_ssh(server["ip"])
            message += f"- Результат: {'🟢 Успешно' if result1 else '🔴 Ошибка'}\n"
            
            message += "\n*Проверка системным SSH (альтернативный метод):*\n"
            result2 = check_ssh_alternative(server["ip"])
            message += f"- Результат: {'🟢 Успешно' if result2 else '🔴 Ошибка'}\n"
            
            if not result1 and not result2:
                message += "\n💡 *Рекомендации:*\n"
                message += "- Проверьте правильность SSH ключа\n"
                message += "- Убедитесь, что ключ добавлен в authorized_keys на сервере\n"
                message += "- Проверьте настройки SSH демона на целевом сервере\n"
            elif result2 and not result1:
                message += "\n⚠️ *Проблема с Paramiko, но системный SSH работает*\n"
                message += "Это известная проблема совместимости. Используем обходные пути.\n"
            else:
                message += "\n✅ Оба метода работают корректно\n"

        else:
            message += "\n❌ *Порт SSH закрыт* - сервер недоступен\n"

    except Exception as e:
        message += f"\n💥 *Ошибка диагностики:* {str(e)}\n"

    update.message.reply_text(message, parse_mode='Markdown')

def diagnose_menu_handler(update, context):
    """Обработчик меню диагностики"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔧 Меню диагностики будет доступно после полной настройки")

# === СТАТИСТИКА (из stats_collector.py) ===

def save_monitoring_stats():
    """Сохраняет статистику мониторинга"""
    try:
        stats_data = {
            "last_updated": datetime.now().isoformat(),
            "uptime": get_system_uptime(),
            "daily_stats": get_daily_stats()
        }
        
        # Создаем директорию если не существует
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATS_FILE.write_text(
            json.dumps(stats_data, indent=2),
            encoding="utf-8",
        )
            
    except Exception as e:
        print(f"❌ Ошибка сохранения статистики: {e}")

def get_system_uptime():
    """Получает время работы системы"""
    try:
        # Для Linux систем
        uptime_seconds = float(PROC_UPTIME_FILE.read_text(encoding="utf-8").split()[0])
            
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    except:
        return "Неизвестно"

def get_daily_stats():
    """Получает дневную статистику"""
    # Здесь можно добавить логику сбора дневной статистики
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "checks_performed": 0,
        "alerts_sent": 0
    }

# === ОТЧЕТЫ (из reports.py) ===

def generate_daily_report():
    """Генерирует ежедневный отчет"""
    # Заглушка - реализовать логику отчетов
    return "📊 Ежедневный отчет в разработке"

def get_backup_stats():
    """Статистика по бэкапам для отчетов"""
    # Заглушка - реализовать логику
    return {"total": 0, "successful": 0, "failed": 0}

# === ОБРАБОТЧИКИ ДЛЯ BOT_MENU ===

def stats_command(update, context):
    """Обработчик команды /stats"""
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    stats = get_daily_stats()
    uptime = get_system_uptime()
    
    message = (
        f"📊 *Статистика мониторинга*\n\n"
        f"• Дата: {stats['date']}\n"
        f"• Проверок выполнено: {stats['checks_performed']}\n"
        f"• Уведомлений отправлено: {stats['alerts_sent']}\n"
        f"• Аптайм системы: {uptime}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='stats_refresh')],
        [InlineKeyboardButton("📊 Статус мониторинга", callback_data='monitor_status')],
        [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
    ]
    
    if hasattr(update, 'callback_query'):
        update.callback_query.edit_message_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
