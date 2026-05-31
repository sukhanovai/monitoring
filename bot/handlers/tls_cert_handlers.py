"""
/bot/handlers/tls_cert_handlers.py
Server Monitoring System v8.62.83
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram handlers for the TLS certificate monitor extension
Система мониторинга серверов
Версия: 8.62.83
Автор: Александр Суханов (c)
Лицензия: MIT
Telegram-обработчики расширения мониторинга TLS-сертификатов
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from extensions.tls_cert_monitor import (
    DEFAULT_CERTS,
    build_status_lines,
    collect_certificates,
    get_domains_config,
    get_settings,
    normalize_domains,
    reissue_certificate,
    save_domains_config,
    save_settings,
)


# ---------------------------------------------------------------------------
# Главное меню
# ---------------------------------------------------------------------------
def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔄 Проверить сейчас", callback_data="tls_check_now")],
            [InlineKeyboardButton("♻️ Перевыпуск (certbot)", callback_data="tls_reissue_list")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="tls_settings")],
            [
                InlineKeyboardButton("🏠 На главную", callback_data="main_menu"),
                InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
            ],
        ]
    )


def show_menu(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("🔐 Опрашиваю сертификаты…", parse_mode="Markdown")
    results, errors = collect_certificates()
    message = "\n".join(build_status_lines(results, errors))
    query.edit_message_text(message, parse_mode="Markdown", reply_markup=_menu_keyboard())


# ---------------------------------------------------------------------------
# Перевыпуск через certbot
# ---------------------------------------------------------------------------
def show_reissue_list(update, context):
    query = update.callback_query
    query.answer()

    certs = get_domains_config()
    settings = get_settings()
    ssh_host = str(settings.get("ssh_host", "")).strip()

    lines = ["♻️ *Перевыпуск сертификатов (certbot по SSH)*", ""]
    if ssh_host:
        lines.append(f"SSH-хост: `{ssh_host}`")
    else:
        lines.append("⚠️ SSH-хост не задан — укажите его в ⚙️ Настройках.")
    lines.append("")
    lines.append("Нажмите сертификат, чтобы перевыпустить:")

    keyboard = []
    for cert_name in sorted(certs.keys()):
        cfg = certs[cert_name]
        mark = "" if cfg.get("enabled", True) else " (выкл.)"
        keyboard.append(
            [InlineKeyboardButton(f"♻️ {cert_name}{mark}", callback_data=f"tls_rs|{cert_name}")]
        )

    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="tls_cert_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )
    query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def confirm_reissue(update, context, cert_name: str):
    query = update.callback_query
    query.answer()
    certs = get_domains_config()
    cfg = certs.get(cert_name, {})
    domains = cfg.get("domains") or [cert_name]
    domains_text = ", ".join(domains)
    keyboard = [
        [InlineKeyboardButton("✅ Да, перевыпустить", callback_data=f"tls_rsdo|{cert_name}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="tls_reissue_list")],
    ]
    query.edit_message_text(
        f"♻️ *Перевыпуск сертификата*\n\n"
        f"Cert-name: `{cert_name}`\n"
        f"Домены (-d): `{domains_text}`\n\n"
        "На SSH-хосте будет выполнено:\n"
        "`certbot certonly --nginx --cert-name … -d … --force-renewal`\n"
        "+ перезапуск nginx.\n\nПродолжить?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def do_reissue(update, context, cert_name: str):
    query = update.callback_query
    query.answer("Запускаю перевыпуск…")
    query.edit_message_text(
        f"♻️ Перевыпускаю `{cert_name}`…\nЭто может занять до нескольких минут.",
        parse_mode="Markdown",
    )
    success, message = reissue_certificate(cert_name)
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить статус", callback_data="tls_check_now")],
        [
            InlineKeyboardButton("↩️ К списку", callback_data="tls_reissue_list"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    # Вывод certbot может содержать спецсимволы — без Markdown.
    query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------------------------------------------------------------------
# Настройки расширения
# ---------------------------------------------------------------------------
def show_settings(update, context):
    query = update.callback_query
    query.answer()

    s = get_settings()
    certs = get_domains_config()
    lines = ["⚙️ *Настройки TLS-мониторинга*", ""]
    lines.append(f"🖥 SSH-хост certbot: `{s.get('ssh_host') or 'не задан'}`")
    lines.append(f"🧩 Команда certbot: `{s.get('certbot_cmd')}`")
    lines.append(f"🔁 Перезапуск nginx: `{s.get('nginx_reload_cmd')}`")
    lines.append(f"⏰ Порог алерта по умолчанию: `{s.get('alert_days_default')}` дн.")
    lines.append(f"📋 Сертификатов настроено: `{len(certs)}`")

    keyboard = [
        [InlineKeyboardButton("🖥 SSH-хост", callback_data="tls_set_ssh")],
        [InlineKeyboardButton("🧩 Команда certbot", callback_data="tls_set_certbot")],
        [InlineKeyboardButton("🔁 Перезапуск nginx", callback_data="tls_set_nginx")],
        [InlineKeyboardButton("⏰ Порог алерта", callback_data="tls_set_alert")],
        [InlineKeyboardButton("📋 Сертификаты", callback_data="tls_certs_cfg")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="tls_cert_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _prompt(update, context, flag: str, text: str, back: str = "tls_settings"):
    query = update.callback_query
    query.answer()
    context.user_data[flag] = True
    query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data=back)]]
        ),
    )


# ---------------------------------------------------------------------------
# Список сертификатов
# ---------------------------------------------------------------------------
def show_certs_cfg(update, context):
    query = update.callback_query
    query.answer()

    certs = get_domains_config()
    lines = ["📋 *Сертификаты под мониторингом*", ""]
    if not certs:
        lines.append("❌ Сертификаты не настроены.")
    else:
        for cert_name in sorted(certs.keys()):
            cfg = certs[cert_name]
            status = "🟢" if cfg.get("enabled", True) else "🔴"
            host = cfg.get("check_host", cert_name)
            ndom = len(cfg.get("domains") or [cert_name])
            lines.append(
                f"{status} `{cert_name}` → {host}:{cfg.get('port', 443)} · "
                f"алерт {cfg.get('alert_days', 14)}д · доменов {ndom}"
            )

    keyboard = []
    for cert_name in sorted(certs.keys()):
        keyboard.append(
            [InlineKeyboardButton(f"⚙️ {cert_name}", callback_data=f"tls_cd|{cert_name}")]
        )
    keyboard.append([InlineKeyboardButton("➕ Добавить сертификат", callback_data="tls_add")])
    keyboard.append([InlineKeyboardButton("🔄 Сбросить к дефолтам", callback_data="tls_reset")])
    keyboard.append(
        [
            InlineKeyboardButton("↩️ Назад", callback_data="tls_settings"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ]
    )
    query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def show_cert_detail(update, context, cert_name: str):
    query = update.callback_query
    query.answer()
    certs = get_domains_config()
    cfg = certs.get(cert_name)
    if cfg is None:
        show_certs_cfg(update, context)
        return

    enabled = bool(cfg.get("enabled", True))
    domains = cfg.get("domains") or [cert_name]
    lines = [
        f"⚙️ *Сертификат* `{cert_name}`",
        "",
        f"Статус: {'🟢 включён' if enabled else '🔴 выключен'}",
        f"Хост проверки: `{cfg.get('check_host', cert_name)}`",
        f"Порт: `{cfg.get('port', 443)}`",
        f"Порог алерта: `{cfg.get('alert_days', 14)}` дн.",
        f"Домены (-d, {len(domains)}): `{', '.join(domains)}`",
    ]
    toggle = "⛔️ Выключить" if enabled else "✅ Включить"
    keyboard = [
        [
            InlineKeyboardButton("🌐 Хост проверки", callback_data=f"tls_eh|{cert_name}"),
            InlineKeyboardButton("🔌 Порт", callback_data=f"tls_ep|{cert_name}"),
        ],
        [
            InlineKeyboardButton("⏰ Порог алерта", callback_data=f"tls_ea|{cert_name}"),
            InlineKeyboardButton("📝 Домены (-d)", callback_data=f"tls_ed|{cert_name}"),
        ],
        [
            InlineKeyboardButton("♻️ Перевыпустить", callback_data=f"tls_rs|{cert_name}"),
            InlineKeyboardButton(toggle, callback_data=f"tls_tg|{cert_name}"),
        ],
        [InlineKeyboardButton("🗑 Удалить сертификат", callback_data=f"tls_rm|{cert_name}")],
        [
            InlineKeyboardButton("↩️ К списку", callback_data="tls_certs_cfg"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def add_cert_prompt(update, context):
    query = update.callback_query
    query.answer()
    context.user_data["tls_add_stage"] = "name"
    query.edit_message_text(
        "➕ *Добавление сертификата*\n\nВведите cert-name (имя сертификата certbot, "
        "например `chat.202020.ru`):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="tls_certs_cfg")]]
        ),
    )


def toggle_cert(update, context, cert_name: str):
    query = update.callback_query
    query.answer()
    certs = get_domains_config()
    if cert_name in certs:
        certs[cert_name]["enabled"] = not bool(certs[cert_name].get("enabled", True))
        save_domains_config(certs)
    show_cert_detail(update, context, cert_name)


def delete_cert(update, context, cert_name: str):
    query = update.callback_query
    query.answer()
    certs = get_domains_config()
    certs.pop(cert_name, None)
    save_domains_config(certs)
    show_certs_cfg(update, context)


def reset_certs(update, context):
    query = update.callback_query
    query.answer("Сброшено к значениям по умолчанию")
    save_domains_config(normalize_domains(DEFAULT_CERTS))
    show_certs_cfg(update, context)


def edit_host_prompt(update, context, cert_name: str):
    context.user_data["tls_edit_host_cert"] = cert_name
    _prompt(
        update,
        context,
        "tls_edit_host",
        f"🌐 *Хост проверки для* `{cert_name}`\n\nВведите хост (домен/IP), к которому "
        "подключаться для живой проверки сертификата:",
        back="tls_certs_cfg",
    )


def edit_port_prompt(update, context, cert_name: str):
    context.user_data["tls_edit_port_cert"] = cert_name
    _prompt(
        update,
        context,
        "tls_edit_port",
        f"🔌 *Порт для* `{cert_name}`\n\nВведите номер порта (1-65535):",
        back="tls_certs_cfg",
    )


def edit_alert_prompt(update, context, cert_name: str):
    context.user_data["tls_edit_alert_cert"] = cert_name
    _prompt(
        update,
        context,
        "tls_edit_alert",
        f"⏰ *Порог алерта для* `{cert_name}`\n\nВведите число дней до истечения (1-180):",
        back="tls_certs_cfg",
    )


def edit_domains_prompt(update, context, cert_name: str):
    certs = get_domains_config()
    current = ", ".join(certs.get(cert_name, {}).get("domains") or [cert_name])
    context.user_data["tls_edit_domains_cert"] = cert_name
    _prompt(
        update,
        context,
        "tls_edit_domains",
        f"📝 *Домены (-d) для* `{cert_name}`\n\nТекущие: `{current}`\n\n"
        "Введите список доменов через запятую/пробел — они пойдут в аргументы "
        "`-d` при перевыпуске:",
        back="tls_certs_cfg",
    )


# ---------------------------------------------------------------------------
# Текстовый ввод
# ---------------------------------------------------------------------------
def _split_domains(text: str) -> list[str]:
    return [part.strip() for part in text.replace(",", " ").split() if part.strip()]


def handle_text_input(update, context):
    """Единый обработчик текстового ввода для tls_*. Возвращает True, если обработал."""
    text = (update.message.text or "").strip()
    ud = context.user_data

    if ud.pop("tls_set_ssh", False):
        save_settings({"ssh_host": text})
        update.message.reply_text(f"✅ SSH-хост сохранён: {text or '(пусто)'}")
        return True

    if ud.pop("tls_set_certbot", False):
        if "{cert_name}" not in text and "{domain}" not in text:
            update.message.reply_text(
                "❌ В команде должен быть плейсхолдер `{cert_name}` (и желательно "
                "`{domain_args}`).",
                parse_mode="Markdown",
            )
            return True
        save_settings({"certbot_cmd": text})
        update.message.reply_text("✅ Команда certbot сохранена.")
        return True

    if ud.pop("tls_set_nginx", False):
        save_settings({"nginx_reload_cmd": text})
        update.message.reply_text("✅ Команда перезапуска nginx сохранена.")
        return True

    if ud.pop("tls_set_alert", False):
        try:
            days = int(text)
            if days < 1 or days > 180:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Введите число от 1 до 180.")
            return True
        save_settings({"alert_days_default": days})
        update.message.reply_text(f"✅ Порог алерта по умолчанию: {days} дн.")
        return True

    if ud.get("tls_edit_host"):
        cert_name = ud.get("tls_edit_host_cert", "")
        certs = get_domains_config()
        if cert_name in certs and text:
            certs[cert_name]["check_host"] = text
            save_domains_config(certs)
            update.message.reply_text(f"✅ Хост проверки для {cert_name}: {text}")
        else:
            update.message.reply_text("❌ Сертификат не найден или пустой хост.")
        ud.pop("tls_edit_host", None)
        ud.pop("tls_edit_host_cert", None)
        return True

    if ud.get("tls_edit_port"):
        cert_name = ud.get("tls_edit_port_cert", "")
        try:
            port = int(text)
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Порт должен быть числом от 1 до 65535.")
            return True
        certs = get_domains_config()
        if cert_name in certs:
            certs[cert_name]["port"] = port
            save_domains_config(certs)
            update.message.reply_text(f"✅ Порт для {cert_name}: {port}")
        else:
            update.message.reply_text("❌ Сертификат не найден.")
        ud.pop("tls_edit_port", None)
        ud.pop("tls_edit_port_cert", None)
        return True

    if ud.get("tls_edit_alert"):
        cert_name = ud.get("tls_edit_alert_cert", "")
        try:
            days = int(text)
            if days < 1 or days > 180:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Введите число от 1 до 180.")
            return True
        certs = get_domains_config()
        if cert_name in certs:
            certs[cert_name]["alert_days"] = days
            save_domains_config(certs)
            update.message.reply_text(f"✅ Порог алерта для {cert_name}: {days} дн.")
        else:
            update.message.reply_text("❌ Сертификат не найден.")
        ud.pop("tls_edit_alert", None)
        ud.pop("tls_edit_alert_cert", None)
        return True

    if ud.get("tls_edit_domains"):
        cert_name = ud.get("tls_edit_domains_cert", "")
        domains = _split_domains(text)
        certs = get_domains_config()
        if cert_name in certs and domains:
            certs[cert_name]["domains"] = domains
            save_domains_config(certs)
            update.message.reply_text(
                f"✅ Домены для {cert_name}: {', '.join(domains)}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📋 К списку", callback_data="tls_certs_cfg")]]
                ),
            )
        else:
            update.message.reply_text("❌ Сертификат не найден или пустой список доменов.")
        ud.pop("tls_edit_domains", None)
        ud.pop("tls_edit_domains_cert", None)
        return True

    stage = ud.get("tls_add_stage")
    if stage == "name":
        name = text
        if not name or "." not in name:
            update.message.reply_text("❌ Введите корректный cert-name (например chat.202020.ru).")
            return True
        if name in get_domains_config():
            update.message.reply_text("❌ Такой сертификат уже есть.")
            return True
        ud["tls_new_name"] = name
        ud["tls_add_stage"] = "host"
        update.message.reply_text(
            f"🌐 Введите хост проверки (Enter «{name}» — взять как cert-name):"
        )
        return True

    if stage == "host":
        name = str(ud.get("tls_new_name", "")).strip()
        ud["tls_new_host"] = text or name
        ud["tls_add_stage"] = "port"
        update.message.reply_text("🔌 Введите порт (по умолчанию 443):")
        return True

    if stage == "port":
        port_raw = text or "443"
        try:
            port = int(port_raw)
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Порт должен быть числом от 1 до 65535.")
            return True
        ud["tls_new_port"] = port
        ud["tls_add_stage"] = "domains"
        name = str(ud.get("tls_new_name", "")).strip()
        update.message.reply_text(
            f"📝 Введите домены (-d) через запятую (Enter — только `{name}`):"
        )
        return True

    if stage == "domains":
        name = str(ud.get("tls_new_name", "")).strip()
        host = str(ud.get("tls_new_host", "")).strip() or name
        port = int(ud.get("tls_new_port", 443))
        domains = _split_domains(text) or [name]
        if not name:
            for key in ("tls_add_stage", "tls_new_name", "tls_new_host", "tls_new_port"):
                ud.pop(key, None)
            update.message.reply_text("❌ Ошибка. Повторите добавление.")
            return True
        certs = get_domains_config()
        certs[name] = {
            "enabled": True,
            "check_host": host,
            "port": port,
            "alert_days": get_settings().get("alert_days_default", 14),
            "domains": domains,
        }
        save_domains_config(certs)
        for key in ("tls_add_stage", "tls_new_name", "tls_new_host", "tls_new_port"):
            ud.pop(key, None)
        update.message.reply_text(
            f"✅ Сертификат {name} добавлен ({host}:{port}, доменов {len(domains)}).",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📋 К списку", callback_data="tls_certs_cfg")]]
            ),
        )
        return True

    return False


# ---------------------------------------------------------------------------
# Диспетчер callback'ов
# ---------------------------------------------------------------------------
def handle_callbacks(update, context, data: str):
    if data in ("tls_cert_menu", "tls_check_now"):
        show_menu(update, context)
    elif data == "tls_reissue_list":
        show_reissue_list(update, context)
    elif data == "tls_settings":
        show_settings(update, context)
    elif data == "tls_certs_cfg":
        show_certs_cfg(update, context)
    elif data == "tls_add":
        add_cert_prompt(update, context)
    elif data == "tls_reset":
        reset_certs(update, context)
    elif data == "tls_set_ssh":
        _prompt(
            update,
            context,
            "tls_set_ssh",
            "🖥 *SSH-хост certbot/nginx*\n\nВведите IP или hostname хоста, "
            "где выполняется certbot и nginx:",
        )
    elif data == "tls_set_certbot":
        _prompt(
            update,
            context,
            "tls_set_certbot",
            "🧩 *Команда certbot*\n\nШаблон с плейсхолдерами `{cert_name}` и `{domain_args}`:\n"
            "`certbot certonly --nginx --cert-name {cert_name} {domain_args} --force-renewal`",
        )
    elif data == "tls_set_nginx":
        _prompt(
            update,
            context,
            "tls_set_nginx",
            "🔁 *Перезапуск nginx*\n\nВведите команду (например `service nginx restart`):",
        )
    elif data == "tls_set_alert":
        _prompt(
            update,
            context,
            "tls_set_alert",
            "⏰ *Порог алерта по умолчанию*\n\nВведите число дней (1-180):",
        )
    elif data.startswith("tls_rsdo|"):
        do_reissue(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_rs|"):
        confirm_reissue(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_cd|"):
        show_cert_detail(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_eh|"):
        edit_host_prompt(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_ep|"):
        edit_port_prompt(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_ea|"):
        edit_alert_prompt(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_ed|"):
        edit_domains_prompt(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_tg|"):
        toggle_cert(update, context, data.split("|", 1)[1])
    elif data.startswith("tls_rm|"):
        delete_cert(update, context, data.split("|", 1)[1])
