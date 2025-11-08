"""
Server Monitoring System v2.2.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
"""
def diagnose_ssh_command(update, context):
    """Диагностика SSH подключения к конкретному серверу"""
    if not context.args:
        update.message.reply_text("❌ Укажите IP или имя сервера: /diagnose_ssh <ip>")
        return

    target = context.args[0]
    
    from extensions.server_list import initialize_servers
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
        from monitor_core import check_port
        is_port_open = check_port(server["ip"], port, timeout=10)
        message += f"Порт {port} (SSH): {'🟢 Открыт' if is_port_open else '🔴 Закрыт'}\n"

        if is_port_open:
            # Проверка SSH подключения
            from monitor_core import check_ssh, check_ssh_alternative
            
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
