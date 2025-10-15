import threading
import time
import socket
import paramiko
import subprocess
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
# Отключаем проблемные алгоритмы
paramiko.transport.Transport._preferred_keys = ('ssh-rsa', 'ecdsa-sha2-nistp256', 'ecdsa-sha2-nistp384', 'ecdsa-sha2-nistp521', 'ssh-ed25519')

from config import (
    TELEGRAM_TOKEN, CHAT_IDS, CHECK_INTERVAL, MAX_FAIL_TIME,
    SILENT_START, SILENT_END, DATA_COLLECTION_TIME,
    REPORT_WINDOW_START, REPORT_WINDOW_END, SSH_KEY_PATH, SSH_USERNAME,
    RDP_SERVERS, PING_SERVERS, SSH_SERVERS, RESOURCE_THRESHOLDS,
    WINDOWS_SERVER_CREDENTIALS, WINRM_CONFIGS
)

from extensions.server_list import initialize_servers
from extensions.resource_check import get_linux_resources_improved, get_windows_resources_improved, check_resource_thresholds, format_resource_message

# Глобальные переменные
bot = None
server_status = {}
morning_data = {}
monitoring_active = True
last_check_time = datetime.now()
servers = []
silent_override = None  # None - авто, True - принудительно тихий, False - принудительно громкий

def is_proxmox_server(server):
    """Проверяет, является ли сервер Proxmox"""
    ip = server["ip"]
    # Proxmox серверы обычно в сети 192.168.30.x или определенные IP
    return (ip.startswith("192.168.30.") or
           ip in ["192.168.20.30", "192.168.20.32", "192.168.20.59"])

def is_silent_time():
    """Проверяет, находится ли текущее время в 'тихом' периоде с учетом переопределения"""
    global silent_override

    # Если есть принудительное переопределение
    if silent_override is not None:
        return silent_override  # True - тихий, False - громкий

    # Стандартная проверка по времени
    current_hour = datetime.now().hour
    if SILENT_START > SILENT_END:  # Если период переходит через полночь (например, 20:00-9:00)
        return current_hour >= SILENT_START or current_hour < SILENT_END
    return SILENT_START <= current_hour < SILENT_END

def send_alert(message, force=False):
    """Отправляет сообщение без блокировок"""
    global bot
    if bot is None:
        from telegram import Bot
        bot = Bot(token=TELEGRAM_TOKEN)

    # Логируем для диагностики
    silent_status = is_silent_time()
    print(f"[{datetime.now()}] 📨 Отправка: '{message[:50]}...'")

    try:
        if force or not is_silent_time():
            for chat_id in CHAT_IDS:
                bot.send_message(chat_id=chat_id, text=message)
            print(f"    ✅ Сообщение отправлено")
        else:
            print(f"    ⏸️ Сообщение не отправлено (тихий режим)")
    except Exception as e:
        print(f"    ❌ Ошибка отправки: {e}")

def check_ping(ip):
    """Проверка доступности через ping"""
    try:
        result = subprocess.run(
            ['ping', '-c', '2', '-W', '2', ip],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )
        return result.returncode == 0
    except:
        return False

def check_port(ip, port=3389, timeout=5):
    """Проверка доступности порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_ssh(ip):
    """Проверка доступности через SSH с улучшенной обработкой разных типов ключей"""
    is_proxmox = is_proxmox_server({"ip": ip})

    timeout_val = 15 if is_proxmox else 10
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Базовые настройки подключения
        client.connect(
            hostname=ip,
            username=SSH_USERNAME,
            key_filename=SSH_KEY_PATH,
            timeout=timeout_val,
            banner_timeout=timeout_val,
            auth_timeout=timeout_val,
            look_for_keys=False,  # Не искать другие ключи
            allow_agent=False,    # Не использовать SSH агент
        )

        # Простая проверка
        stdin, stdout, stderr = client.exec_command('echo "test"', timeout=5)
        exit_code = stdout.channel.recv_exit_status()
        client.close()

        return exit_code == 0

    except paramiko.ssh_exception.AuthenticationException as e:
        print(f"❌ Ошибка аутентификации для {ip}: {e}")
        return False
    except paramiko.ssh_exception.SSHException as e:
        print(f"❌ SSH ошибка для {ip}: {e}")
        return False
    except socket.timeout:
        print(f"⏰ Таймаут подключения к {ip}")
        return False
    except Exception as e:
        print(f"⚠️ Общая ошибка для {ip}: {e}")
        return False

def check_ssh_alternative(ip):
    """Альтернативная проверка через системный SSH"""
    try:
        result = subprocess.run([
            'ssh', '-o', 'ConnectTimeout=10',
            '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-i', SSH_KEY_PATH,
            f'{SSH_USERNAME}@{ip}',
            'echo "success"'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

        return result.returncode == 0 and "success" in result.stdout.decode()
    except subprocess.TimeoutExpired:
        print(f"⏰ Таймаут системного SSH для {ip}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка системного SSH для {ip}: {e}")
        return False

def check_ssh_improved(ip):
    """Улучшенная проверка SSH с обработкой ошибок ключей"""
    print(f"🔍 Проверяем SSH для {ip}")

    # Пробуем основной метод
    result1 = check_ssh(ip)
    if result1:
        print(f"✅ Основной метод сработал для {ip}")
        return True

    # Если не сработало, пробуем альтернативный
    print(f"🔄 Пробуем альтернативный метод для {ip}")
    result2 = check_ssh_alternative(ip)
    if result2:
        print(f"✅ Альтернативный метод сработал для {ip}")
        return True

    # Если оба метода не сработали, пробуем с другим ключом
    print(f"🔑 Пробуем с другим SSH ключом для {ip}")
    result3 = check_ssh_with_fallback_key(ip)
    if result3:
        print(f"✅ Метод с fallback ключом сработал для {ip}")
        return True

    print(f"❌ Все методы не сработали для {ip}")
    return False

def check_ssh_with_fallback_key(ip):
    """Проверка SSH с альтернативным ключом"""
    try:
        # Пробуем стандартный ключ если доступен
        fallback_key = "/root/.ssh/id_rsa"
        if os.path.exists(fallback_key):
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10',
                '-o', 'BatchMode=yes',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-i', fallback_key,
                f'{SSH_USERNAME}@{ip}',
                'echo "success"'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

            return result.returncode == 0 and "success" in result.stdout.decode()
        return False

    except subprocess.TimeoutExpired:
        print(f"⏰ Таймаут fallback SSH для {ip}")
        return False
    except Exception as e:
        print(f"⚠️ Ошибка fallback SSH для {ip}: {e}")
        return False


def progress_bar(percentage, width=20):
    """Генерирует текстовый прогресс-бар"""
    filled = int(round(width * percentage / 100))
    return f"[{'█' * filled}{'░' * (width - filled)}] {percentage:.1f}%"

def perform_manual_check(context, chat_id, progress_message_id):
    """Выполняет проверку серверов с обновлением прогресса"""
    global last_check_time
    total_servers = len(servers)
    results = {"failed": [], "ok": []}

    for i, server in enumerate(servers):
        try:
            progress = (i + 1) / total_servers * 100
            progress_text = f"🔍 Проверяю серверы...\n{progress_bar(progress)}\n\n⏳ Проверяю {server['name']} ({server['ip']})..."

            context.bot.edit_message_text(chat_id=chat_id, message_id=progress_message_id, text=progress_text)

            # Улучшенная проверка доступности сервера
            is_up = False

            if is_proxmox_server(server):
                # Для Proxmox используем улучшенную SSH проверку
                is_up = check_ssh_improved(server["ip"])
            elif server["type"] == "rdp":
                is_up = check_port(server["ip"], 3389)
            elif server["type"] == "ping":
                is_up = check_ping(server["ip"])
            else:
                # Для остальных SSH серверов тоже используем улучшенную проверку
                is_up = check_ssh_improved(server["ip"])

            if is_up:
                results["ok"].append(server)
                print(f"✅ {server['name']} ({server['ip']}) - доступен")
            else:
                results["failed"].append(server)
                print(f"❌ {server['name']} ({server['ip']}) - недоступен")

            time.sleep(1)  # Увеличиваем задержку между проверками

        except Exception as e:
            print(f"💥 Критическая ошибка при проверке {server['ip']}: {e}")
            results["failed"].append(server)

    last_check_time = datetime.now()

    # Формируем отчет
    if not results["failed"]:
        message = "✅ Все серверы доступны!"
    else:
        message = "⚠️ Проблемные серверы:\n"
        # Группируем по типу для удобства чтения
        by_type = {}
        for server in results["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n{server_type.upper()} серверы:\n"
            for s in servers_list:
                message += f"- {s['name']} ({s['ip']})\n"

    context.bot.edit_message_text(
        chat_id=chat_id, message_id=progress_message_id,
        text=f"🔍 Проверка завершена!\n\n{message}\n\n⏰ Время проверки: {last_check_time.strftime('%H:%M:%S')}"
    )

def manual_check_handler(update, context):
    """Обработчик ручной проверки серверов"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🔍 Начинаю проверку серверов...\n" + progress_bar(0)
    )

    thread = threading.Thread(
        target=perform_manual_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def get_current_server_status():
    """Выполняет быструю проверку статуса серверов"""
    results = {"failed": [], "ok": []}

    for server in servers:
        try:
            if is_proxmox_server(server):
                is_up = check_ssh_improved(server["ip"])
            elif server["type"] == "rdp":
                is_up = check_port(server["ip"], 3389, timeout=2)
            elif server["type"] == "ping":
                is_up = check_ping(server["ip"])
            else:
                is_up = check_ssh_improved(server["ip"])

            if is_up:
                results["ok"].append(server)
            else:
                results["failed"].append(server)
        except:
            results["failed"].append(server)

    return results

def monitor_status(update, context):
    """Показывает статус мониторинга"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        # Если вызвано как команда, а не callback
        chat_id = update.message.chat_id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    try:
        current_status = get_current_server_status()
        up_count = len(current_status["ok"])
        down_count = len(current_status["failed"])

        status = "🟢 Активен" if monitoring_active else "🔴 Остановлен"

        # Определяем статус тихого режима
        silent_status_text = "🔇 Тихий режим" if is_silent_time() else "🔊 Обычный режим"
        if silent_override is not None:
            if silent_override:
                silent_status_text += " (🔇 Принудительно)"
            else:
                silent_status_text += " (🔊 Принудительно)"

        next_check = datetime.now() + timedelta(seconds=CHECK_INTERVAL)

        message = (
            f"📊 *Статус мониторинга* - help\n\n"
            f"**Состояние:** {status}\n"
            f"**Режим:** {silent_status_text}\n\n"
            f"⏰ Последняя проверка: {last_check_time.strftime('%H:%M:%S')}\n"
            f"⏳ Следующая проверка: {next_check.strftime('%H:%M:%S')}\n"
            f"🔢 Всего серверов: {len(servers)}\n"
            f"🟢 Доступно: {up_count}\n"
            f"🔴 Недоступно: {down_count}\n"
            f"🔄 Интервал проверки: {CHECK_INTERVAL} сек\n"
        )

        if down_count > 0:
            message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"

            # Группируем по типу для удобства чтения
            by_type = {}
            for server in current_status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)

            for server_type, servers_list in by_type.items():
                message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                for i, s in enumerate(servers_list[:8]):  # Ограничиваем показ
                    message += f"• {s['name']} ({s['ip']})\n"

                if len(servers_list) > 8:
                    message += f"• ... и еще {len(servers_list) - 8} серверов\n"

        # Отправляем сообщение в зависимости от типа вызова
        if query:
            query.edit_message_text(
                text=message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Обновить статус", callback_data='monitor_status')],
                    [InlineKeyboardButton("🔍 Проверить сейчас", callback_data='manual_check')],
                    [InlineKeyboardButton("🔇 Управление режимом", callback_data='silent_status')],
                    [InlineKeyboardButton("📋 Список серверов", callback_data='servers_list')],
                    [InlineKeyboardButton("🎛️ Управление", callback_data='control_panel')],
                    [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
                ])
            )
        else:
            update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        print(f"Ошибка в monitor_status: {e}")
        error_msg = "⚠️ Произошла ошибка при получении статуса"
        if query:
            query.edit_message_text(error_msg)
        else:
            update.message.reply_text(error_msg)

def silent_command(update, context):
    """Обработчик команды /silent"""
    silent_status = "🟢 активен" if is_silent_time() else "🔴 неактивен"
    message = (
        f"🔇 *Статус тихого режима:* {silent_status}\n\n"
        f"⏰ *Время работы:* {SILENT_START}:00 - {SILENT_END}:00\n\n"
        f"💡 *В тихом режиме:*\n"
        f"• Регулярные уведомления не отправляются\n"
        f"• Критические ошибки все равно отправляются\n"
        f"• Ручные проверки работают нормально\n"
        f"• Утренние отчеты отправляются принудительно"
    )

    update.message.reply_text(message, parse_mode='Markdown')

def silent_status_handler(update, context):
    """Обработчик кнопки статуса тихого режима"""
    query = update.callback_query
    query.answer()

    # Определяем текущий режим
    if silent_override is None:
        mode_text = "🔄 Автоматический"
        mode_desc = "Работает по расписанию"
    elif silent_override:
        mode_text = "🔇 Принудительно тихий"
        mode_desc = "Все уведомления отключены"
    else:
        mode_text = "🔊 Принудительно громкий"
        mode_desc = "Все уведомления включены"

    # Правильно определяем статус - инвертируем для понятности пользователю
    current_status = "🔴 неактивен" if is_silent_time() else "🟢 активен"
    status_description = "тихий режим" if is_silent_time() else "громкий режим"

    message = (
        f"🔇 *Управление тихим режимом*\n\n"
        f"**Текущий статус:** {current_status}\n"
        f"**Режим работы:** {mode_text}\n"
        f"*{mode_desc}*\n"
        f"**Фактически:** {status_description}\n\n"
        f"⏰ *Расписание тихого режима:* {SILENT_START}:00 - {SILENT_END}:00\n\n"
        f"💡 *Пояснение:*\n"
        f"- 🟢 активен = уведомления работают\n"
        f"- 🔴 неактивен = уведomления отключены\n"
        f"- 🔊 громкий режим = все уведомления включены\n"
        f"- 🔇 тихий режим = только критические уведомления"
    )

    query.edit_message_text(
        text=message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔇 Включить принудительно тихий", callback_data='force_silent')],
            [InlineKeyboardButton("🔊 Включить принудительно громкий", callback_data='force_loud')],
            [InlineKeyboardButton("🔄 Вернуть автоматический режим", callback_data='auto_mode')],
            [InlineKeyboardButton("📊 Статус мониторинга", callback_data='monitor_status')],
            [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
        ])
    )

def force_silent_handler(update, context):
    """Включает принудительный тихий режим"""
    global silent_override
    silent_override = True
    query = update.callback_query
    query.answer()

    # Отправляем уведомление о изменении режима
    send_alert("🔇 *Принудительный тихий режим включен*\nВсе уведомления отключены до смены режима.", force=True)

    query.edit_message_text(
        "🔇 *Принудительный тихий режим включен*\n\n✅ Все уведомления отключены до следующего изменения режима.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔊 Включить громкий режим", callback_data='force_loud')],
            [InlineKeyboardButton("🔄 Автоматический режим", callback_data='auto_mode')],
            [InlineKeyboardButton("📊 Статус мониторинга", callback_data='monitor_status')]
        ])
    )

def force_loud_handler(update, context):
    """Включает принудительный громкий режим"""
    global silent_override
    silent_override = False
    query = update.callback_query
    query.answer()

    # Отправляем уведомление о изменении режима
    send_alert("🔊 *Принудительный громкий режим включен*\nВсе уведомления активны до смена режима.", force=True)

    query.edit_message_text(
        "🔊 *Принудительный громкий режим включен*\n\n✅ Все уведomления активны до следующего изменения режима.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔇 Включить тихий режим", callback_data='force_silent')],
            [InlineKeyboardButton("🔄 Автоматический режим", callback_data='auto_mode')],
            [InlineKeyboardButton("📊 Статус мониторинга", callback_data='monitor_status')]
        ])
    )

def auto_mode_handler(update, context):
    """Включает автоматический режим"""
    global silent_override
    silent_override = None
    query = update.callback_query
    query.answer()

    current_status = "активен" if is_silent_time() else "неактивен"
    send_alert(f"🔄 *Автоматический режим включен*\nТихий режим сейчас {current_status}.", force=True)

    query.edit_message_text(
        f"🔄 *Автоматический режим включен*\n\n✅ Тихий режим работает по расписанию.\n📊 Текущий статус: {current_status}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔇 Принудительно тихий", callback_data='force_silent')],
            [InlineKeyboardButton("🔊 Принудительно громкий", callback_data='force_loud')],
            [InlineKeyboardButton("📊 Статус мониторинга", callback_data='monitor_status')]
        ])
    )

def control_command(update, context):
    """Обработчик команды /control"""
    keyboard = [
        [InlineKeyboardButton("⏸️ Приостановить мониторинг", callback_data='pause_monitoring')],
        [InlineKeyboardButton("▶️ Возобновить мониторинг", callback_data='resume_monitoring')],
        [InlineKeyboardButton("🔍 Проверить ресурсы", callback_data='check_resources')],
        [InlineKeyboardButton("📊 Полный отчет", callback_data='full_report')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')]
    ]

    status_text = "🟢 Мониторинг активен" if monitoring_active else "🔴 Мониторинг приостановлен"

    update.message.reply_text(
        f"🎛️ *Управление мониторингом*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def control_panel_handler(update, context):
    """Обработчик кнопки панели управления"""
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("⏸️ Приостановить мониторинг", callback_data='pause_monitoring')],
        [InlineKeyboardButton("▶️ Возобновить мониторинг", callback_data='resume_monitoring')],
        [InlineKeyboardButton("🔍 Проверить ресурсы", callback_data='check_resources')],
        [InlineKeyboardButton("📊 Полный отчет", callback_data='full_report')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')]
    ]

    status_text = "🟢 Мониторинг активен" if monitoring_active else "🔴 Мониторинг приостановлен"

    query.edit_message_text(
        f"🎛️ *Управление мониторингом*\n\n{status_text}",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def pause_monitoring_handler(update, context):
    """Приостановка мониторинга"""
    global monitoring_active
    query = update.callback_query
    query.answer()

    monitoring_active = False
    query.edit_message_text(
        "⏸️ Мониторинг приостановлен\n\nУведомления отправляться не будут.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Возобновить", callback_data='resume_monitoring')],
            [InlineKeyboardButton("🎛️ Панель управления", callback_data='control_panel')]
        ])
    )

def resume_monitoring_handler(update, context):
    """Возобновление мониторинга"""
    global monitoring_active
    query = update.callback_query
    query.answer()

    monitoring_active = True
    query.edit_message_text(
        "▶️ Мониторинг возобновлен",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎛️ Панель управления", callback_data='control_panel')]
        ])
    )

def check_resources_handler(update, context):
    """Обработчик проверки ресурсов серверов - новое меню с разделением по ресурсам"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    # НОВОЕ МЕНЮ с разделением по ресурсам
    keyboard = [
        [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
        [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
        [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
        [InlineKeyboardButton("🔍 Все ресурсы", callback_data='check_all_resources')],
        [InlineKeyboardButton("🐧 Linux серверы", callback_data='check_linux')],
        [InlineKeyboardButton("🪟 Windows серверы", callback_data='check_windows')],
        [InlineKeyboardButton("📡 Другие серверы", callback_data='check_other')],
        [InlineKeyboardButton("↩️ Назад", callback_data='control_panel')]
    ]

    if query:
        query.edit_message_text(
            text="🔍 *Выберите что проверить:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text="🔍 *Выберите что проверить:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# НОВЫЕ ФУНКЦИИ ДЛЯ РАЗДЕЛЬНОЙ ПРОВЕРКИ РЕСУРСОВ

def check_cpu_resources_handler(update, context):
    """Обработчик проверки только CPU"""
    query = update.callback_query
    if query:
        query.answer("💻 Проверяем CPU...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="💻 *Проверка загрузки CPU...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_cpu_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def check_ram_resources_handler(update, context):
    """Обработчик проверки только RAM"""
    query = update.callback_query
    if query:
        query.answer("🧠 Проверяем RAM...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🧠 *Проверка использования RAM...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_ram_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def check_disk_resources_handler(update, context):
    """Обработчик проверки только Disk"""
    query = update.callback_query
    if query:
        query.answer("💾 Проверяем Disk...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="💾 *Проверка дискового пространства...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_disk_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_cpu_check(context, chat_id, progress_message_id):
    """Выполняет проверку только CPU"""
    def update_progress(progress, status):
        progress_text = f"💻 Проверка CPU...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        from extensions.separate_checks import check_all_servers_by_type
        results, stats = check_all_servers_by_type()

        # Фильтруем только CPU и сортируем по убыванию нагрузки
        cpu_results = []
        for result in results:
            server = result["server"]
            resources = result["resources"]
            cpu_value = resources.get('cpu', 0) if resources else 0
            
            cpu_results.append({
                "server": server,
                "cpu": cpu_value,
                "success": result["success"]
            })

        # Сортируем по убыванию CPU
        cpu_results.sort(key=lambda x: x["cpu"], reverse=True)

        message = f"💻 **Загрузка CPU серверов**\n\n"
        
        # Группируем по типам серверов
        windows_cpu = [r for r in cpu_results if r["server"]["type"] == "rdp"]
        linux_cpu = [r for r in cpu_results if r["server"]["type"] == "ssh"]
        
        # Windows серверы
        message += f"**🪟 Windows серверы:**\n"
        for result in windows_cpu[:10]:  # Показываем топ-10
            server = result["server"]
            cpu_value = result["cpu"]
            status_icon = "🟢" if result["success"] else "🔴"
            
            if cpu_value > 80:
                cpu_display = f"🚨 {cpu_value}%"
            elif cpu_value > 60:
                cpu_display = f"⚠️ {cpu_value}%"
            else:
                cpu_display = f"{cpu_value}%"
                
            message += f"{status_icon} {server['name']}: {cpu_display}\n"
        
        if len(windows_cpu) > 10:
            message += f"• ... и еще {len(windows_cpu) - 10} серверов\n"
        
        # Linux серверы
        message += f"\n**🐧 Linux серверы:**\n"
        for result in linux_cpu[:10]:  # Показываем топ-10
            server = result["server"]
            cpu_value = result["cpu"]
            status_icon = "🟢" if result["success"] else "🔴"
            
            if cpu_value > 80:
                cpu_display = f"🚨 {cpu_value}%"
            elif cpu_value > 60:
                cpu_display = f"⚠️ {cpu_value}%"
            else:
                cpu_display = f"{cpu_value}%"
                
            message += f"{status_icon} {server['name']}: {cpu_display}\n"
        
        if len(linux_cpu) > 10:
            message += f"• ... и еще {len(linux_cpu) - 10} серверов\n"
        
        # Статистика
        total_servers = len(cpu_results)
        high_load = len([r for r in cpu_results if r["cpu"] > 80])
        medium_load = len([r for r in cpu_results if 60 < r["cpu"] <= 80])
        
        message += f"\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {total_servers}\n"
        message += f"• Высокая нагрузка (>80%): {high_load}\n"
        message += f"• Средняя нагрузка (60-80%): {medium_load}\n"
        
        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_cpu')],
                [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
                [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
                [InlineKeyboardButton("🔍 Все ресурсы", callback_data='check_resources')],
                [InlineKeyboardButton("↩️ Назад", callback_data='control_panel')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке CPU: {e}"
        print(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def perform_ram_check(context, chat_id, progress_message_id):
    """Выполняет проверку только RAM"""
    def update_progress(progress, status):
        progress_text = f"🧠 Проверка RAM...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        from extensions.separate_checks import check_all_servers_by_type
        results, stats = check_all_servers_by_type()

        # Фильтруем только RAM и сортируем по убыванию использования
        ram_results = []
        for result in results:
            server = result["server"]
            resources = result["resources"]
            ram_value = resources.get('ram', 0) if resources else 0
            
            ram_results.append({
                "server": server,
                "ram": ram_value,
                "success": result["success"]
            })

        # Сортируем по убыванию RAM
        ram_results.sort(key=lambda x: x["ram"], reverse=True)

        message = f"🧠 **Использование RAM серверов**\n\n"
        
        # Группируем по типам серверов
        windows_ram = [r for r in ram_results if r["server"]["type"] == "rdp"]
        linux_ram = [r for r in ram_results if r["server"]["type"] == "ssh"]
        
        # Windows серверы
        message += f"**🪟 Windows серверы:**\n"
        for result in windows_ram[:10]:  # Показываем топ-10
            server = result["server"]
            ram_value = result["ram"]
            status_icon = "🟢" if result["success"] else "🔴"
            
            if ram_value > 85:
                ram_display = f"🚨 {ram_value}%"
            elif ram_value > 70:
                ram_display = f"⚠️ {ram_value}%"
            else:
                ram_display = f"{ram_value}%"
                
            message += f"{status_icon} {server['name']}: {ram_display}\n"
        
        if len(windows_ram) > 10:
            message += f"• ... и еще {len(windows_ram) - 10} серверов\n"
        
        # Linux серверы
        message += f"\n**🐧 Linux серверы:**\n"
        for result in linux_ram[:10]:  # Показываем топ-10
            server = result["server"]
            ram_value = result["ram"]
            status_icon = "🟢" if result["success"] else "🔴"
            
            if ram_value > 85:
                ram_display = f"🚨 {ram_value}%"
            elif ram_value > 70:
                ram_display = f"⚠️ {ram_value}%"
            else:
                ram_display = f"{ram_value}%"
                
            message += f"{status_icon} {server['name']}: {ram_display}\n"
        
        if len(linux_ram) > 10:
            message += f"• ... и еще {len(linux_ram) - 10} серверов\n"
        
        # Статистика
        total_servers = len(ram_results)
        high_usage = len([r for r in ram_results if r["ram"] > 85])
        medium_usage = len([r for r in ram_results if 70 < r["ram"] <= 85])
        
        message += f"\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {total_servers}\n"
        message += f"• Высокое использование (>85%): {high_usage}\n"
        message += f"• Среднее использование (70-85%): {medium_usage}\n"
        
        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_ram')],
                [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
                [InlineKeyboardButton("💾 Проверить Disk", callback_data='check_disk')],
                [InlineKeyboardButton("🔍 Все ресурсы", callback_data='check_resources')],
                [InlineKeyboardButton("↩️ Назад", callback_data='control_panel')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке RAM: {e}"
        print(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def perform_disk_check(context, chat_id, progress_message_id):
    """Выполняет проверку только Disk"""
    def update_progress(progress, status):
        progress_text = f"💾 Проверка Disk...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        from extensions.separate_checks import check_all_servers_by_type
        results, stats = check_all_servers_by_type()

        # Фильтруем только Disk и сортируем по убыванию использования
        disk_results = []
        for result in results:
            server = result["server"]
            resources = result["resources"]
            disk_value = resources.get('disk', 0) if resources else 0
            
            disk_results.append({
                "server": server,
                "disk": disk_value,
                "success": result["success"]
            })

        # Сортируем по убыванию Disk
        disk_results.sort(key=lambda x: x["disk"], reverse=True)

        message = f"💾 **Использование дискового пространства**\n\n"
        
        # Группируем по типам серверов
        windows_disk = [r for r in disk_results if r["server"]["type"] == "rdp"]
        linux_disk = [r for r in disk_results if r["server"]["type"] == "ssh"]
        
        # Windows серверы
        message += f"**🪟 Windows серверы:**\n"
        for result in windows_disk[:10]:  # Показываем топ-10
            server = result["server"]
            disk_value = result["disk"]
            status_icon = "🟢" if result["success"] else "🔴"
            
            if disk_value > 90:
                disk_display = f"🚨 {disk_value}%"
            elif disk_value > 80:
                disk_display = f"⚠️ {disk_value}%"
            else:
                disk_display = f"{disk_value}%"
                
            message += f"{status_icon} {server['name']}: {disk_display}\n"
        
        if len(windows_disk) > 10:
            message += f"• ... и еще {len(windows_disk) - 10} серверов\n"
        
        # Linux серверы
        message += f"\n**🐧 Linux серверы:**\n"
        for result in linux_disk[:10]:  # Показываем топ-10
            server = result["server"]
            disk_value = result["disk"]
            status_icon = "🟢" if result["success"] else "🔴"
            
            if disk_value > 90:
                disk_display = f"🚨 {disk_value}%"
            elif disk_value > 80:
                disk_display = f"⚠️ {disk_value}%"
            else:
                disk_display = f"{disk_value}%"
                
            message += f"{status_icon} {server['name']}: {disk_display}\n"
        
        if len(linux_disk) > 10:
            message += f"• ... и еще {len(linux_disk) - 10} серверов\n"
        
        # Статистика
        total_servers = len(disk_results)
        critical_usage = len([r for r in disk_results if r["disk"] > 90])
        warning_usage = len([r for r in disk_results if 80 < r["disk"] <= 90])
        
        message += f"\n**📊 Статистика:**\n"
        message += f"• Всего серверов: {total_servers}\n"
        message += f"• Критическое использование (>90%): {critical_usage}\n"
        message += f"• Предупреждение (80-90%): {warning_usage}\n"
        
        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить", callback_data='check_disk')],
                [InlineKeyboardButton("💻 Проверить CPU", callback_data='check_cpu')],
                [InlineKeyboardButton("🧠 Проверить RAM", callback_data='check_ram')],
                [InlineKeyboardButton("🔍 Все ресурсы", callback_data='check_resources')],
                [InlineKeyboardButton("↩️ Назад", callback_data='control_panel')]
            ])
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Disk: {e}"
        print(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )
        
    if query:
        query.edit_message_text(
            text="🔍 *Выберите тип серверов для проверки:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            text="🔍 *Выберите тип серверов для проверки:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Добавляем импорт os в начало файла
import os

def start_monitoring():
    """Запускает основной цикл мониторинга"""
    global servers, bot, monitoring_active

    servers = initialize_servers()

    # Инициализируем бота
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)

    # Инициализация server_status
    for server in servers:
        server_status[server["ip"]] = {
            "last_up": datetime.now(),
            "alert_sent": False,
            "name": server["name"],
            "type": server["type"],
            "resources": None,
            "last_alert": {}
        }

    # КРИТИЧЕСКИ ВАЖНО: полностью исключаем сервер мониторинга
    monitor_server_ip = "192.168.20.2"
    if monitor_server_ip in server_status:
        server_status[monitor_server_ip]["last_up"] = datetime.now()
        server_status[monitor_server_ip]["alert_sent"] = True
        server_status[monitor_server_ip]["excluded"] = True
        print(f"✅ Сервер мониторинга {monitor_server_ip} полностью исключен")

    send_alert("🟢 Мониторинг серверов запущен с проверкой ресурсов")

    last_resource_check = datetime.now()
    resource_check_interval = 3600  # Проверять ресурсы каждый час
    last_data_collection = None
    report_sent_today = False
    last_report_date = None  # Добавляем отслеживание даты последнего отчета

    while True:
        current_time = datetime.now()
        current_time_time = current_time.time()

        # Автоматическая проверка ресурсов раз в час
        if (current_time - last_resource_check).total_seconds() >= resource_check_interval:
            if monitoring_active and not is_silent_time():
                print("🔄 Автоматическая проверка ресурсов серверов...")
                check_resources_automatically()
                last_resource_check = current_time

        # Сбор данных в 8:30
        if (current_time_time.hour == DATA_COLLECTION_TIME.hour and
            current_time_time.minute == DATA_COLLECTION_TIME.minute and
            (last_data_collection is None or current_time.date() != last_data_collection.date())):

            print(f"[{current_time}] 🔍 Собираем данные для утреннего отчета...")
            # Собираем текущий статус серверов
            morning_status = get_current_server_status()
            morning_data["status"] = morning_status
            morning_data["collection_time"] = current_time
            last_data_collection = current_time
            report_sent_today = False
            print(f"✅ Данные для утреннего отчета собраны: {len(morning_status['ok'])} доступно, {len(morning_status['failed'])} недоступно")
            
            # СРАЗУ отправляем отчет после сбора данных
            print(f"[{current_time}] 📊 Отправка утреннего отчета...")
            send_morning_report()
            report_sent_today = True
            last_report_date = current_time.date()
            print("✅ Утренний отчет отправлен")

        # Основной цикл мониторинга доступности
        if monitoring_active:
            last_check_time = current_time

            for server in servers:
                ip = server["ip"]
                status = server_status[ip]

                # ПОЛНОСТЬЮ ИСКЛЮЧАЕМ сервер мониторинга из любых проверок
                if ip == monitor_server_ip:
                    server_status[ip]["last_up"] = current_time
                    continue

                # Проверка доступности
                if is_proxmox_server(server):
                    is_up = check_ssh_improved(ip)
                elif server["type"] == "rdp":
                    is_up = check_port(ip, 3389)
                elif server["type"] == "ping":
                    is_up = check_ping(ip)
                else:
                    is_up = check_ssh_improved(ip)

                if is_up:
                    if status["alert_sent"]:
                        downtime = (current_time - status["last_up"]).total_seconds()
                        send_alert(f"✅ {status['name']} ({ip}) доступен (простой: {int(downtime//60)} мин)")

                    server_status[ip] = {
                        "last_up": current_time,
                        "alert_sent": False,
                        "name": status["name"],
                        "type": status["type"],
                        "resources": server_status[ip].get("resources"),
                        "last_alert": server_status[ip].get("last_alert", {})
                    }
                else:
                    downtime = (current_time - status["last_up"]).total_seconds()
                    if downtime >= MAX_FAIL_TIME and not status["alert_sent"]:
                        send_alert(f"🚨 {status['name']} ({ip}) не отвечает (проверка: {status['type'].upper()})")
                        server_status[ip]["alert_sent"] = True

        time.sleep(CHECK_INTERVAL)

def send_morning_report():
    """Отправляет утренний отчет о доступности серверов"""
    global morning_data

    if not morning_data or "status" not in morning_data:
        print("❌ Нет данных для утреннего отчета")
        return

    status = morning_data["status"]
    collection_time = morning_data.get("collection_time", datetime.now())

    total_servers = len(status["ok"]) + len(status["failed"])
    up_count = len(status["ok"])
    down_count = len(status["failed"])

    # Формируем сообщение
    message = f"📊 *Утренний отчет о доступности серверов*\n\n"
    message += f"⏰ *Время сбора данных:* {collection_time.strftime('%H:%M')}\n"
    message += f"🔢 *Всего серверов:* {total_servers}\n"
    message += f"🟢 *Доступно:* {up_count}\n"
    message += f"🔴 *Недоступно:* {down_count}\n"

    if down_count > 0:
        message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"

        # Группируем по типу для удобства чтения
        by_type = {}
        for server in status["failed"]:
            if server["type"] not in by_type:
                by_type[server["type"]] = []
            by_type[server["type"]].append(server)

        for server_type, servers_list in by_type.items():
            message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
            for s in servers_list:
                message += f"• {s['name']} ({s['ip']})\n"

    else:
        message += f"\n✅ *Все серверы доступны!*\n"

    message += f"\n📋 *Статистика по типам:*\n"

    # Статистика по типам серверов
    type_stats = {}
    all_servers = status["ok"] + status["failed"]
    for server in all_servers:
        if server["type"] not in type_stats:
            type_stats[server["type"]] = {"total": 0, "up": 0}
        type_stats[server["type"]]["total"] += 1

    for server in status["ok"]:
        type_stats[server["type"]]["up"] += 1

    for server_type, stats in type_stats.items():
        up_percent = (stats["up"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        message += f"• {server_type.upper()}: {stats['up']}/{stats['total']} ({up_percent:.1f}%)\n"

    message += f"\n⏰ *Отчет отправлен:* {datetime.now().strftime('%H:%M:%S')}"

    # Отправляем отчет принудительно, даже в тихом режиме
    send_alert(message, force=True)
    print(f"✅ Утренний отчет отправлен: {up_count}/{total_servers} доступно")

def send_morning_report_handler(update, context):
    """Обработчик для принудительной отправки утреннего отчета"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    chat_id = query.message.chat_id if query else update.message.chat_id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    # Собираем актуальные данные
    current_status = get_current_server_status()
    global morning_data
    morning_data = {
        "status": current_status,
        "collection_time": datetime.now()
    }

    # Отправляем отчет
    send_morning_report()

    response = "📊 Утренний отчет отправлен принудительно"
    if query:
        query.edit_message_text(response)
    else:
        update.message.reply_text(response)

# Заглушки для отсутствующих функций
def check_resources_automatically():
    """Заглушка для автоматической проверки ресурсов"""
    print("🔍 Автоматическая проверка ресурсов...")

def close_menu(update, context):
    """Закрывает меню"""
    query = update.callback_query
    query.answer()
    query.delete_message()

def diagnose_menu_handler(update, context):
    """Обработчик меню диагностики"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔧 Меню диагностики в разработке")

def daily_report_handler(update, context):
    """Обработчик ежедневного отчета"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("📊 Ежедневный отчет в разработке")

def toggle_silent_mode_handler(update, context):
    """Обработчик переключения тихого режима"""
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔇 Переключение тихого режима")

# Добавляем функции для раздельной проверки ресурсов
def check_linux_resources_handler(update, context):
    """Обработчик проверки Linux серверов"""
    from extensions.separate_checks import check_linux_servers
    query = update.callback_query
    if query:
        query.answer("🐧 Проверяем Linux серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🐧 *Проверка Linux серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_linux_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_linux_check(context, chat_id, progress_message_id):
    """Выполняет проверку Linux серверов с прогрессом"""
    def update_progress(progress, status):
        progress_text = f"🐧 Проверка Linux серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    try:
        from extensions.separate_checks import check_linux_servers
        update_progress(0, "⏳ Подготовка...")
        results, total_servers = check_linux_servers(update_progress)

        message = f"🐧 **Проверка Linux серверов**\n\n"
        successful_checks = len([r for r in results if r["success"]])
        message += f"✅ Успешно: {successful_checks}/{total_servers}\n\n"

        for result in results:
            server = result["server"]
            resources = result["resources"]

            # Используем правильное имя сервера из конфигурации
            server_name = server["name"]

            if resources:
                message += f"🟢 {server_name}: CPU {resources.get('cpu', 0)}%, RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%\n"
            else:
                message += f"🔴 {server_name}: недоступен\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown'
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Linux серверов: {e}"
        print(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_windows_resources_handler(update, context):
    """Обработчик проверки Windows серверов"""
    query = update.callback_query
    if query:
        query.answer("🪟 Проверяем Windows серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🪟 *Проверка Windows серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_windows_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_windows_check(context, chat_id, progress_message_id):
    """Выполняет проверку Windows серверов с прогрессом"""
    def update_progress(progress, status):
        progress_text = f"🪟 Проверка Windows серверов...\n{progress_bar(progress)}\n\n{status}"
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=progress_text
        )

    def safe_get(resources, key, default=0):
        """Безопасное получение значения из resources"""
        if resources is None:
            return default
        return resources.get(key, default)

    try:
        from extensions.separate_checks import (check_windows_2025_servers, check_domain_windows_servers,
                                              check_admin_windows_servers, check_standard_windows_servers)

        update_progress(0, "⏳ Подготовка...")

        # Проверяем все типы Windows серверов
        win2025_results, win2025_total = check_windows_2025_servers(update_progress)
        domain_results, domain_total = check_domain_windows_servers(update_progress)
        admin_results, admin_total = check_admin_windows_servers(update_progress)
        win_std_results, win_std_total = check_standard_windows_servers(update_progress)

        message = f"🪟 **Проверка Windows серверов**\n\n"

        # Windows 2025
        win2025_success = len([r for r in win2025_results if r["success"]])
        message += f"**Windows 2025:** {win2025_success}/{win2025_total}\n"
        for result in win2025_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"
            
            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')
            
            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Доменные серверы
        domain_success = len([r for r in domain_results if r["success"]])
        message += f"\n**Доменные Windows:** {domain_success}/{domain_total}\n"
        for result in domain_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"
            
            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')
            
            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Серверы с Admin
        admin_success = len([r for r in admin_results if r["success"]])
        message += f"\n**Windows (Admin):** {admin_success}/{admin_total}\n"
        for result in admin_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"
            
            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')
            
            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        # Стандартные Windows
        win_std_success = len([r for r in win_std_results if r["success"]])
        message += f"\n**Обычные Windows:** {win_std_success}/{win_std_total}\n"
        for result in win_std_results:
            server = result["server"]
            resources = result["resources"]
            status = "🟢" if result["success"] else "🔴"
            
            # ЗАЩИЩЕННЫЙ ДОСТУП К РЕСУРСАМ
            cpu_value = safe_get(resources, 'cpu')
            ram_value = safe_get(resources, 'ram')
            disk_value = safe_get(resources, 'disk')
            
            disk_info = f", Disk {disk_value}%" if disk_value > 0 else ""
            message += f"{status} {server['name']}: CPU {cpu_value}%, RAM {ram_value}%{disk_info}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown'
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке Windows серверов: {e}"
        print(error_msg)
        import traceback
        print(f"Подробности ошибки: {traceback.format_exc()}")
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_other_resources_handler(update, context):
    """Обработчик проверки других серверов"""
    query = update.callback_query
    if query:
        query.answer("📡 Проверяем другие серверы...")
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="📡 *Проверка других серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_other_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_other_check(context, chat_id, progress_message_id):
    """Выполняет проверку других серверов"""
    try:
        from extensions.server_list import initialize_servers
        servers = initialize_servers()
        ping_servers = [s for s in servers if s["type"] == "ping"]

        message = f"📡 **Проверка других серверов**\n\n"
        successful_checks = 0

        for server in ping_servers:
            is_up = check_ping(server["ip"])
            if is_up:
                successful_checks += 1
                message += f"🟢 {server['name']}: доступен\n"
            else:
                message += f"🔴 {server['name']}: недоступен\n"

        message += f"\n✅ Доступно: {successful_checks}/{len(ping_servers)}"
        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown'
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при проверке других серверов: {e}"
        print(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )

def check_all_resources_handler(update, context):
    """Обработчик полной проверки всех серверов"""
    query = update.callback_query
    if query:
        query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.effective_chat.id

    if str(chat_id) not in CHAT_IDS:
        if query:
            query.edit_message_text("⛔ У вас нет прав для выполнения этой команды")
        else:
            update.message.reply_text("⛔ У вас нет прав для выполнения этой команды")
        return

    progress_message = context.bot.send_message(
        chat_id=chat_id,
        text="🔍 *Запускаю проверку всех серверов...*\n\n⏳ Подготовка...",
        parse_mode='Markdown'
    )

    thread = threading.Thread(
        target=perform_full_check,
        args=(context, chat_id, progress_message.message_id)
    )
    thread.start()

def perform_full_check(context, chat_id, progress_message_id):
    """Выполняет полную проверку всех серверов"""
    try:
        from extensions.separate_checks import check_all_servers_by_type
        results, stats = check_all_servers_by_type()

        total_checked = stats["windows_2025"]["checked"] + stats["standard_windows"]["checked"] + stats["linux"]["checked"]
        total_success = stats["windows_2025"]["success"] + stats["standard_windows"]["success"] + stats["linux"]["success"]

        message = f"📊 **Полная проверка серверов**\n\n"
        message += f"✅ Всего доступно: {total_success}/{total_checked}\n\n"

        message += f"**Windows 2025:** {stats['windows_2025']['success']}/{stats['windows_2025']['checked']}\n"
        message += f"**Обычные Windows:** {stats['standard_windows']['success']}/{stats['standard_windows']['checked']}\n"
        message += f"**Linux:** {stats['linux']['success']}/{stats['linux']['checked']}\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%H:%M:%S')}"

        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=message,
            parse_mode='Markdown'
        )

    except Exception as e:
        error_msg = f"❌ Ошибка при полной проверке: {e}"
        print(error_msg)
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message_id,
            text=error_msg
        )
