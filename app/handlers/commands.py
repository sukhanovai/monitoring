"""
/app/handlers/commands.py
Server Monitoring System v4.14.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot command handlers
Система мониторинга серверов
Версия: 4.14.2
Автор: Александр Суханов (c)
Лицензия: MIT
Обработчики команд Telegram бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from app.utils.common import debug_log

def send_alert(message, force=False):
    """Отправляет сообщение в Telegram"""
    try:
        from app.modules.availability import availability_monitor
        from app.config.settings import is_silent_time
        
        if force or not is_silent_time():
            from monitor_core import bot
            if bot:
                from app.config.settings import CHAT_IDS
                for chat_id in CHAT_IDS:
                    bot.send_message(chat_id=chat_id, text=message)
                debug_log("✅ Сообщение отправлено")
                return True
        else:
            debug_log("⏸️ Сообщение не отправлено (тихий режим)")
            
        return False
    except Exception as e:
        debug_log(f"❌ Ошибка отправки сообщения: {e}")
        return False

def handle_check_single_server(update, context, server_ip):
    """Обработка проверки одного сервера"""
    try:
        from extensions.server_checks import get_server_by_ip, check_server_availability
        
        server = get_server_by_ip(server_ip)
        if not server:
            return "❌ Сервер не найден"
        
        is_up = check_server_availability(server)
        
        if is_up:
            return f"✅ Сервер {server['name']} ({server_ip}) доступен"
        else:
            return f"🔴 Сервер {server['name']} ({server_ip}) недоступен"
            
    except Exception as e:
        debug_log(f"❌ Ошибка проверки сервера {server_ip}: {e}")
        return f"❌ Ошибка проверки: {str(e)[:100]}"

def handle_check_server_resources(update, context, server_ip):
    """Обработка проверки ресурсов одного сервера"""
    try:
        from app.modules.resources import resource_monitor
        
        resources = resource_monitor.check_single_server(server_ip)
        
        if not resources:
            return "❌ Не удалось получить ресурсы сервера"
        
        from extensions.server_checks import get_server_by_ip
        server = get_server_by_ip(server_ip)
        
        message = f"📊 **Ресурсы сервера {server['name']} ({server_ip})**\n\n"
        message += f"• CPU: {resources.get('cpu', 0)}%\n"
        message += f"• RAM: {resources.get('ram', 0)}%\n"
        message += f"• Disk: {resources.get('disk', 0)}%\n"
        message += f"• Метод доступа: {resources.get('access_method', 'неизвестно')}\n"
        message += f"• Время проверки: {resources.get('timestamp', 'N/A')}\n"
        
        # Проверка порогов
        from app.config.settings import RESOURCE_THRESHOLDS
        alerts = []
        
        cpu = resources.get('cpu', 0)
        ram = resources.get('ram', 0)
        disk = resources.get('disk', 0)
        
        if cpu >= RESOURCE_THRESHOLDS["cpu_critical"]:
            alerts.append(f"🚨 CPU: {cpu}% (критично)")
        elif cpu >= RESOURCE_THRESHOLDS["cpu_warning"]:
            alerts.append(f"⚠️ CPU: {cpu}% (высокая нагрузка)")
        
        if ram >= RESOURCE_THRESHOLDS["ram_critical"]:
            alerts.append(f"🚨 RAM: {ram}% (критично)")
        elif ram >= RESOURCE_THRESHOLDS["ram_warning"]:
            alerts.append(f"⚠️ RAM: {ram}% (мало свободной памяти)")
        
        if disk >= RESOURCE_THRESHOLDS["disk_critical"]:
            alerts.append(f"🚨 Disk: {disk}% (критично)")
        elif disk >= RESOURCE_THRESHOLDS["disk_warning"]:
            alerts.append(f"⚠️ Disk: {disk}% (мало места)")
        
        if alerts:
            message += "\n**⚠️ Предупреждения:**\n"
            for alert in alerts:
                message += f"• {alert}\n"
        
        return message
        
    except Exception as e:
        debug_log(f"❌ Ошибка проверки ресурсов сервера {server_ip}: {e}")
        return f"❌ Ошибка: {str(e)[:100]}"

def create_server_selection_keyboard(server_type=None, action="check_single"):
    """Создает клавиатуру для выбора сервера"""
    try:
        from extensions.server_checks import initialize_servers
        
        servers = initialize_servers()
        
        if server_type:
            servers = [s for s in servers if s["type"] == server_type]
        
        # Группируем по типу для удобства
        keyboard = []
        current_row = []
        
        for i, server in enumerate(servers):
            button_text = f"{server['name'][:15]}"
            callback_data = f"{action}_{server['ip']}"
            
            current_row.append(
                InlineKeyboardButton(button_text, callback_data=callback_data)
            )
            
            # Добавляем по 2 кнопки в ряд
            if len(current_row) == 2 or i == len(servers) - 1:
                keyboard.append(current_row)
                current_row = []
        
        # Добавляем кнопки навигации
        keyboard.append([
            InlineKeyboardButton("↩️ Назад", callback_data='main_menu'),
            InlineKeyboardButton("✖️ Закрыть", callback_data='close')
        ])
        
        return InlineKeyboardMarkup(keyboard)
        
    except Exception as e:
        debug_log(f"❌ Ошибка создания клавиатуры выбора сервера: {e}")
        return InlineKeyboardMarkup([[]])