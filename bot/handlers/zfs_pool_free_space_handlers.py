"""
/bot/handlers/zfs_pool_free_space_handlers.py
Server Monitoring System v8.56.13
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram handlers for ZFS pool free space extension
Система мониторинга серверов
Версия: 8.56.13
Автор: Александр Суханов (c)
Лицензия: MIT
Telegram-обработчики расширения свободного места ZFS-пулов
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from extensions.zfs_pool_free_space import (
    build_status_lines,
    collect_zfs_pool_free_space,
    get_hosts_config,
    save_hosts_config,
)


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚙️ Настройка хостов", callback_data="zfsp_hosts_list")],
            [InlineKeyboardButton("🏠 На главную", callback_data="main_menu")],
            [InlineKeyboardButton("✖️ Закрыть", callback_data="close")],
        ]
    )


def show_zfs_pool_free_space_menu(update, context):
    query = update.callback_query
    query.answer()

    results, errors = collect_zfs_pool_free_space()
    message = "\n".join(build_status_lines(results, errors))
    query.edit_message_text(message, parse_mode="Markdown", reply_markup=_menu_keyboard())


def show_hosts_list(update, context):
    query = update.callback_query
    query.answer()

    hosts = get_hosts_config()
    lines = ["⚙️ *Хосты мониторинга свободного места ZFS*", ""]
    if not hosts:
        lines.append("❌ Хосты не настроены.")
    else:
        for host_name in sorted(hosts.keys()):
            host = hosts[host_name]
            status = "🟢" if host.get("enabled", True) else "🔴"
            ip = str(host.get("ip", "")).strip() or "не задан"
            threshold = int(host.get("threshold", 15))
            lines.append(f"{status} `{host_name}`")
            lines.append(f"   └ IP: `{ip}` · Порог: `{threshold}%`")

    keyboard = []
    for host_name in sorted(hosts.keys()):
        host = hosts[host_name]
        enabled = bool(host.get("enabled", True))
        toggle_text = "⛔️ Отключить" if enabled else "✅ Включить"
        keyboard.extend(
            [
                [InlineKeyboardButton(f"✏️ Имя: {host_name}", callback_data=f"zfsp_edit_name_{host_name}")],
                [InlineKeyboardButton(f"🌐 IP: {host_name}", callback_data=f"zfsp_edit_ip_{host_name}")],
                [InlineKeyboardButton(f"🎚 Порог: {host_name}", callback_data=f"zfsp_edit_threshold_{host_name}")],
                [
                    InlineKeyboardButton(f"🗑 Удалить: {host_name}", callback_data=f"zfsp_delete_{host_name}"),
                    InlineKeyboardButton(f"{toggle_text}: {host_name}", callback_data=f"zfsp_toggle_{host_name}"),
                ],
            ]
        )

    keyboard.extend(
        [
            [InlineKeyboardButton("➕ Добавить хост", callback_data="zfsp_add")],
            [
                InlineKeyboardButton("↩️ Назад", callback_data="zfs_pool_free_space_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )

    query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


def add_host_prompt(update, context):
    query = update.callback_query
    query.answer()
    context.user_data["adding_zfsp_host"] = True
    context.user_data["zfsp_host_stage"] = "name"

    query.edit_message_text(
        "➕ *Добавление хоста*\n\nВведите имя хоста:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="zfsp_hosts_list")]]
        ),
    )


def _cleanup_add(context):
    for key in ("adding_zfsp_host", "zfsp_host_stage", "zfsp_new_host_name", "zfsp_new_host_ip"):
        context.user_data.pop(key, None)


def handle_add_input(update, context):
    if not context.user_data.get("adding_zfsp_host"):
        return False
    stage = context.user_data.get("zfsp_host_stage", "name")
    text = (update.message.text or "").strip()
    hosts = get_hosts_config()

    if stage == "name":
        if not text:
            update.message.reply_text("❌ Имя не может быть пустым.")
            return True
        if text in hosts:
            update.message.reply_text("❌ Хост с таким именем уже существует.")
            return True
        context.user_data["zfsp_new_host_name"] = text
        context.user_data["zfsp_host_stage"] = "ip"
        update.message.reply_text("🌐 Введите IP адрес:")
        return True

    if stage == "ip":
        if not text:
            update.message.reply_text("❌ IP не может быть пустым.")
            return True
        context.user_data["zfsp_new_host_ip"] = text
        context.user_data["zfsp_host_stage"] = "threshold"
        update.message.reply_text("🎚 Введите порог свободного места в % (1-95):")
        return True

    if stage == "threshold":
        try:
            threshold = int(text)
            if threshold < 1 or threshold > 95:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Порог должен быть числом от 1 до 95.")
            return True

        name = str(context.user_data.get("zfsp_new_host_name", "")).strip()
        ip = str(context.user_data.get("zfsp_new_host_ip", "")).strip()
        if not name or not ip:
            _cleanup_add(context)
            update.message.reply_text("❌ Не удалось сохранить хост. Повторите попытку.")
            return True

        hosts[name] = {"ip": ip, "threshold": threshold, "enabled": True}
        save_hosts_config(hosts)
        _cleanup_add(context)
        update.message.reply_text("✅ Хост добавлен. Откройте меню хостов для управления.")
        return True

    return False


def _edit_prompt(update, context, flag_key: str, name_key: str, server_name: str, text: str, back: str):
    query = update.callback_query
    query.answer()
    context.user_data[flag_key] = True
    context.user_data[name_key] = server_name
    query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data=back)]]),
    )


def edit_name_prompt(update, context, server_name: str):
    _edit_prompt(
        update,
        context,
        "editing_zfsp_name",
        "editing_zfsp_name_old",
        server_name,
        f"✏️ *Изменение имени*\n\nТекущее имя: `{server_name}`\nВведите новое имя:",
        "zfsp_hosts_list",
    )


def edit_ip_prompt(update, context, server_name: str):
    hosts = get_hosts_config()
    current_ip = str(hosts.get(server_name, {}).get("ip", "")).strip()
    _edit_prompt(
        update,
        context,
        "editing_zfsp_ip",
        "editing_zfsp_ip_name",
        server_name,
        f"🌐 *Изменение IP*\n\nХост: `{server_name}`\nТекущий IP: `{current_ip or 'не задан'}`\nВведите новый IP:",
        "zfsp_hosts_list",
    )


def edit_threshold_prompt(update, context, server_name: str):
    hosts = get_hosts_config()
    threshold = int(hosts.get(server_name, {}).get("threshold", 15))
    _edit_prompt(
        update,
        context,
        "editing_zfsp_threshold",
        "editing_zfsp_threshold_name",
        server_name,
        f"🎚 *Изменение порога*\n\nХост: `{server_name}`\nТекущий порог: `{threshold}%`\nВведите новый порог (1-95):",
        "zfsp_hosts_list",
    )


def handle_edit_name_input(update, context):
    if not context.user_data.get("editing_zfsp_name"):
        return False
    new_name = (update.message.text or "").strip()
    old_name = str(context.user_data.get("editing_zfsp_name_old", "")).strip()
    hosts = get_hosts_config()

    if not old_name or old_name not in hosts:
        context.user_data.pop("editing_zfsp_name", None)
        context.user_data.pop("editing_zfsp_name_old", None)
        update.message.reply_text("❌ Хост не найден.")
        return True
    if not new_name:
        update.message.reply_text("❌ Имя не может быть пустым.")
        return True
    if new_name in hosts and new_name != old_name:
        update.message.reply_text("❌ Хост с таким именем уже существует.")
        return True

    host_data = hosts.pop(old_name)
    hosts[new_name] = host_data
    save_hosts_config(hosts)
    context.user_data.pop("editing_zfsp_name", None)
    context.user_data.pop("editing_zfsp_name_old", None)
    update.message.reply_text("✅ Имя хоста обновлено.")
    return True


def handle_edit_ip_input(update, context):
    if not context.user_data.get("editing_zfsp_ip"):
        return False
    new_ip = (update.message.text or "").strip()
    name = str(context.user_data.get("editing_zfsp_ip_name", "")).strip()
    hosts = get_hosts_config()
    if name in hosts and new_ip:
        hosts[name]["ip"] = new_ip
        save_hosts_config(hosts)
        update.message.reply_text("✅ IP обновлён.")
    else:
        update.message.reply_text("❌ Хост не найден или IP пустой.")
    context.user_data.pop("editing_zfsp_ip", None)
    context.user_data.pop("editing_zfsp_ip_name", None)
    return True


def handle_edit_threshold_input(update, context):
    if not context.user_data.get("editing_zfsp_threshold"):
        return False
    name = str(context.user_data.get("editing_zfsp_threshold_name", "")).strip()
    hosts = get_hosts_config()
    try:
        threshold = int((update.message.text or "").strip())
        if threshold < 1 or threshold > 95:
            raise ValueError
    except ValueError:
        update.message.reply_text("❌ Порог должен быть числом от 1 до 95.")
        return True

    if name in hosts:
        hosts[name]["threshold"] = threshold
        save_hosts_config(hosts)
        update.message.reply_text("✅ Порог обновлён.")
    else:
        update.message.reply_text("❌ Хост не найден.")
    context.user_data.pop("editing_zfsp_threshold", None)
    context.user_data.pop("editing_zfsp_threshold_name", None)
    return True


def delete_host(update, context, server_name: str):
    query = update.callback_query
    query.answer()
    hosts = get_hosts_config()
    hosts.pop(server_name, None)
    save_hosts_config(hosts)
    show_hosts_list(update, context)


def toggle_host(update, context, server_name: str):
    query = update.callback_query
    query.answer()
    hosts = get_hosts_config()
    if server_name in hosts:
        hosts[server_name]["enabled"] = not bool(hosts[server_name].get("enabled", True))
        save_hosts_config(hosts)
    show_hosts_list(update, context)


def handle_callbacks(update, context, data: str):
    if data == "zfs_pool_free_space_menu":
        show_zfs_pool_free_space_menu(update, context)
    elif data == "zfsp_hosts_list":
        show_hosts_list(update, context)
    elif data == "zfsp_add":
        add_host_prompt(update, context)
    elif data.startswith("zfsp_edit_name_"):
        edit_name_prompt(update, context, data.replace("zfsp_edit_name_", "", 1))
    elif data.startswith("zfsp_edit_ip_"):
        edit_ip_prompt(update, context, data.replace("zfsp_edit_ip_", "", 1))
    elif data.startswith("zfsp_edit_threshold_"):
        edit_threshold_prompt(update, context, data.replace("zfsp_edit_threshold_", "", 1))
    elif data.startswith("zfsp_delete_"):
        delete_host(update, context, data.replace("zfsp_delete_", "", 1))
    elif data.startswith("zfsp_toggle_"):
        toggle_host(update, context, data.replace("zfsp_toggle_", "", 1))


def handle_text_input(update, context):
    if handle_add_input(update, context):
        return True
    if handle_edit_name_input(update, context):
        return True
    if handle_edit_ip_input(update, context):
        return True
    if handle_edit_threshold_input(update, context):
        return True
    return False
