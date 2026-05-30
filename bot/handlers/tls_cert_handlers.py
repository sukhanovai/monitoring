"""
/bot/handlers/tls_cert_handlers.py
Server Monitoring System v8.62.77
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram handlers for the TLS certificate monitor extension
Система мониторинга серверов
Версия: 8.62.77
Автор: Александр Суханов (c)
Лицензия: MIT
Telegram-обработчики расширения мониторинга TLS-сертификатов
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from extensions.tls_cert_monitor import (
    DEFAULT_DOMAINS,
    PAID_CERT_DOMAIN,
    build_status_lines,
    certificate_key_match,
    collect_certificates,
    get_domains_config,
    get_paid_cert_info,
    get_paid_cert_url,
    get_settings,
    normalize_domains,
    reissue_certificate,
    save_domains_config,
    save_paid_certificate,
    save_paid_key,
    save_settings,
    set_paid_cert_url,
)

# Максимальный размер загружаемого cert/key (защита от мусора).
_MAX_UPLOAD_BYTES = 256 * 1024


# ---------------------------------------------------------------------------
# Главное меню
# ---------------------------------------------------------------------------
def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔄 Проверить сейчас", callback_data="tls_check_now")],
            [InlineKeyboardButton("♻️ Перевыпуск (certbot)", callback_data="tls_domains")],
            [InlineKeyboardButton("📜 Платный сертификат", callback_data="tls_paid")],
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
def show_domains_reissue(update, context):
    query = update.callback_query
    query.answer()

    domains = get_domains_config()
    settings = get_settings()
    ssh_host = str(settings.get("ssh_host", "")).strip()

    lines = ["♻️ *Перевыпуск сертификатов (certbot по SSH)*", ""]
    if ssh_host:
        lines.append(f"SSH-хост: `{ssh_host}`")
    else:
        lines.append("⚠️ SSH-хост не задан — укажите его в ⚙️ Настройках.")
    lines.append("")
    lines.append("Нажмите домен, чтобы перевыпустить сертификат:")

    keyboard = []
    for domain in sorted(domains.keys()):
        cfg = domains[domain]
        mark = "" if cfg.get("enabled", True) else " (выкл.)"
        keyboard.append(
            [InlineKeyboardButton(f"♻️ {domain}{mark}", callback_data=f"tls_reissue_{domain}")]
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


def confirm_reissue(update, context, domain: str):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("✅ Да, перевыпустить", callback_data=f"tls_reissue_do_{domain}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="tls_domains")],
    ]
    query.edit_message_text(
        f"♻️ *Перевыпуск сертификата*\n\nДомен: `{domain}`\n\n"
        "Будет выполнено на SSH-хосте:\n"
        "`certbot certonly --nginx --force-renewal` + перезапуск nginx.\n\n"
        "Продолжить?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def do_reissue(update, context, domain: str):
    query = update.callback_query
    query.answer("Запускаю перевыпуск…")
    query.edit_message_text(
        f"♻️ Перевыпускаю `{domain}`…\nЭто может занять до нескольких минут.",
        parse_mode="Markdown",
    )
    success, message = reissue_certificate(domain)
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить статус", callback_data="tls_check_now")],
        [
            InlineKeyboardButton("↩️ К списку", callback_data="tls_domains"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    # Сообщение certbot может содержать спецсимволы — без Markdown.
    query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------------------------------------------------------------------
# Платный сертификат 202020.ru
# ---------------------------------------------------------------------------
def show_paid_menu(update, context):
    query = update.callback_query
    query.answer()

    info = get_paid_cert_info()
    paid_url = get_paid_cert_url()
    lines = [f"📜 *Платный сертификат* `{PAID_CERT_DOMAIN}`", ""]
    if info.get("ok"):
        end = info["not_after"].strftime("%Y-%m-%d") if info.get("not_after") else "?"
        lines.append(f"🟢 Сертификат загружен, действует до {end} ({info.get('days_left')} дн.)")
        lines.append(f"   Файл: `{info.get('cert_path')}`")
    elif info.get("error"):
        lines.append(f"⚠️ {info['error']}")
    else:
        lines.append("❌ Сертификат не загружен.")
    lines.append(f"Ключ: {'🟢 загружен' if info.get('has_key') else '❌ нет'}")
    lines.append(f"🔗 URL проверки сертификата: {paid_url or 'не задан'}")
    lines.append("")
    lines.append("Загрузите файлы как *документы* (PEM): сначала нажмите кнопку,")
    lines.append("затем пришлите соответствующий файл в этот чат.")
    lines.append("")
    lines.append("Файлы сохраняются в `data/certificates`; применение в nginx — вручную.")

    keyboard = [
        [InlineKeyboardButton("⬆️ Загрузить сертификат (.crt/.pem)", callback_data="tls_paid_cert")],
        [InlineKeyboardButton("🔑 Загрузить ключ (.key)", callback_data="tls_paid_key")],
        [InlineKeyboardButton("🔍 Проверить пару cert/key", callback_data="tls_paid_match")],
        [InlineKeyboardButton("✅ Проверить по URL", callback_data="tls_paid_check_url")],
        [InlineKeyboardButton("🔗 Изменить URL проверки", callback_data="tls_set_paid_url")],
        [
            InlineKeyboardButton("↩️ Назад", callback_data="tls_cert_menu"),
            InlineKeyboardButton("✖️ Закрыть", callback_data="close"),
        ],
    ]
    query.edit_message_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def check_paid_url(update, context):
    query = update.callback_query
    query.answer("Проверяю сертификат по URL…")
    from extensions.tls_cert_monitor import check_paid_cert_url

    info = check_paid_cert_url()
    lines = ["✅ *Проверка сертификата по URL*", ""]
    lines.append(f"URL: `{info.get('url') or 'не задан'}`")
    if info.get("ok"):
        end = info["not_after"].strftime("%Y-%m-%d") if info.get("not_after") else "?"
        days = info.get("days_left")
        icon = "🟢" if (days is None or days > 0) else "⛔️"
        lines.append(f"{icon} Сертификат валиден до {end} (осталось {days} дн.)")
        if info.get("issuer"):
            lines.append(f"Издатель: `{info['issuer']}`")
    else:
        lines.append(f"❌ {info.get('error', 'не удалось проверить')}")

    query.edit_message_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data="tls_paid")]]
        ),
    )


def prompt_paid_upload(update, context, kind: str):
    query = update.callback_query
    query.answer()
    context.user_data["tls_paid_upload"] = kind
    label = "сертификата (PEM/CRT)" if kind == "cert" else "приватного ключа (PEM/KEY)"
    query.edit_message_text(
        f"⬆️ Пришлите файл {label} как *документ* в этот чат.\n\n" "Для отмены нажмите «Назад».",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data="tls_paid")]]
        ),
    )


def check_paid_match(update, context):
    query = update.callback_query
    query.answer()
    ok, message = certificate_key_match()
    icon = "✅" if ok else "❌"
    query.edit_message_text(
        f"{icon} {message}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩️ Назад", callback_data="tls_paid")]]
        ),
    )


def handle_document_input(update, context):
    """Обрабатывает загруженный документ (cert или key). Возвращает True, если обработал."""
    kind = context.user_data.get("tls_paid_upload")
    if not kind:
        return False

    message = update.message
    document = getattr(message, "document", None)
    if document is None:
        message.reply_text("❌ Пришлите файл именно как документ (вложение).")
        return True

    if document.file_size and document.file_size > _MAX_UPLOAD_BYTES:
        message.reply_text("❌ Файл слишком большой для сертификата/ключа.")
        context.user_data.pop("tls_paid_upload", None)
        return True

    try:
        tg_file = context.bot.get_file(document.file_id)
        data = bytes(tg_file.download_as_bytearray())
    except Exception as exc:  # pragma: no cover - сетевые ошибки Telegram
        message.reply_text(f"❌ Не удалось скачать файл: {exc}")
        context.user_data.pop("tls_paid_upload", None)
        return True

    if kind == "cert":
        ok, msg = save_paid_certificate(data)
    else:
        ok, msg = save_paid_key(data)

    context.user_data.pop("tls_paid_upload", None)
    icon = "✅" if ok else "❌"
    extra = ""
    if ok:
        match_ok, match_msg = certificate_key_match()
        extra = f"\n{'✅' if match_ok else '⚠️'} {match_msg}"
    message.reply_text(
        f"{icon} {msg}{extra}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📜 К платному сертификату", callback_data="tls_paid")]]
        ),
    )
    return True


# ---------------------------------------------------------------------------
# Настройки расширения
# ---------------------------------------------------------------------------
def show_settings(update, context):
    query = update.callback_query
    query.answer()

    s = get_settings()
    domains = get_domains_config()
    paid_url = get_paid_cert_url()
    lines = ["⚙️ *Настройки TLS-мониторинга*", ""]
    lines.append(f"🖥 SSH-хост certbot: `{s.get('ssh_host') or 'не задан'}`")
    lines.append(f"🧩 Команда certbot: `{s.get('certbot_cmd')}`")
    lines.append(f"🔁 Перезапуск nginx: `{s.get('nginx_reload_cmd')}`")
    lines.append(f"⏰ Порог алерта по умолчанию: `{s.get('alert_days_default')}` дн.")
    lines.append(f"🔗 URL проверки сертификата: `{paid_url or 'не задан'}`")
    lines.append(f"📋 Доменов настроено: `{len(domains)}`")

    keyboard = [
        [InlineKeyboardButton("🖥 SSH-хост", callback_data="tls_set_ssh")],
        [InlineKeyboardButton("🧩 Команда certbot", callback_data="tls_set_certbot")],
        [InlineKeyboardButton("🔁 Перезапуск nginx", callback_data="tls_set_nginx")],
        [InlineKeyboardButton("⏰ Порог алерта", callback_data="tls_set_alert")],
        [InlineKeyboardButton("🔗 URL проверки сертификата", callback_data="tls_set_paid_url")],
        [InlineKeyboardButton("📋 Домены", callback_data="tls_domains_cfg")],
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
# Настройка доменов
# ---------------------------------------------------------------------------
def show_domains_cfg(update, context):
    query = update.callback_query
    query.answer()

    domains = get_domains_config()
    lines = ["📋 *Домены под мониторингом*", ""]
    if not domains:
        lines.append("❌ Домены не настроены.")
    else:
        for domain in sorted(domains.keys()):
            cfg = domains[domain]
            status = "🟢" if cfg.get("enabled", True) else "🔴"
            lines.append(
                f"{status} `{domain}` · порт `{cfg.get('port', 443)}` · "
                f"алерт `{cfg.get('alert_days', 14)}` дн."
            )

    keyboard = []
    for domain in sorted(domains.keys()):
        cfg = domains[domain]
        enabled = bool(cfg.get("enabled", True))
        toggle = "⛔️ Откл." if enabled else "✅ Вкл."
        keyboard.append(
            [
                InlineKeyboardButton(f"🔌 {domain}: порт", callback_data=f"tls_port_{domain}"),
                InlineKeyboardButton("⏰ алерт", callback_data=f"tls_alert_{domain}"),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(f"{toggle}", callback_data=f"tls_toggle_{domain}"),
                InlineKeyboardButton("🗑 Удалить", callback_data=f"tls_del_{domain}"),
            ]
        )

    keyboard.append([InlineKeyboardButton("➕ Добавить домен", callback_data="tls_add")])
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


def add_domain_prompt(update, context):
    query = update.callback_query
    query.answer()
    context.user_data["tls_add_stage"] = "domain"
    query.edit_message_text(
        "➕ *Добавление домена*\n\nВведите имя домена (например `chat.202020.ru`):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Отмена", callback_data="tls_domains_cfg")]]
        ),
    )


def toggle_domain(update, context, domain: str):
    query = update.callback_query
    query.answer()
    domains = get_domains_config()
    if domain in domains:
        domains[domain]["enabled"] = not bool(domains[domain].get("enabled", True))
        save_domains_config(domains)
    show_domains_cfg(update, context)


def delete_domain(update, context, domain: str):
    query = update.callback_query
    query.answer()
    domains = get_domains_config()
    domains.pop(domain, None)
    save_domains_config(domains)
    show_domains_cfg(update, context)


def reset_domains(update, context):
    query = update.callback_query
    query.answer("Сброшено к значениям по умолчанию")
    save_domains_config(normalize_domains(DEFAULT_DOMAINS))
    show_domains_cfg(update, context)


def edit_port_prompt(update, context, domain: str):
    context.user_data["tls_edit_port_domain"] = domain
    _prompt(
        update,
        context,
        "tls_edit_port",
        f"🔌 *Порт для* `{domain}`\n\nВведите номер порта (1-65535):",
        back="tls_domains_cfg",
    )


def edit_alert_prompt(update, context, domain: str):
    context.user_data["tls_edit_alert_domain"] = domain
    _prompt(
        update,
        context,
        "tls_edit_alert",
        f"⏰ *Порог алерта для* `{domain}`\n\nВведите число дней до истечения (1-180):",
        back="tls_domains_cfg",
    )


# ---------------------------------------------------------------------------
# Текстовый ввод
# ---------------------------------------------------------------------------
def handle_text_input(update, context):
    """Единый обработчик текстового ввода для tls_*. Возвращает True, если обработал."""
    text = (update.message.text or "").strip()
    ud = context.user_data

    if ud.pop("tls_set_ssh", False):
        save_settings({"ssh_host": text})
        update.message.reply_text(f"✅ SSH-хост сохранён: {text or '(пусто)'}")
        return True

    if ud.pop("tls_set_certbot", False):
        if "{domain}" not in text:
            update.message.reply_text(
                "❌ В команде должен быть плейсхолдер `{domain}`.", parse_mode="Markdown"
            )
            return True
        save_settings({"certbot_cmd": text})
        update.message.reply_text("✅ Команда certbot сохранена.")
        return True

    if ud.pop("tls_set_nginx", False):
        save_settings({"nginx_reload_cmd": text})
        update.message.reply_text("✅ Команда перезапуска nginx сохранена.")
        return True

    if ud.pop("tls_set_paid_url", False):
        if text and not (text.startswith("http://") or text.startswith("https://")):
            update.message.reply_text(
                "❌ URL должен начинаться с http:// или https:// "
                "(или отправьте «-», чтобы очистить)."
            )
            ud["tls_set_paid_url"] = True
            return True
        cleaned = "" if text in ("", "-") else text
        set_paid_cert_url(cleaned)
        update.message.reply_text(
            f"✅ URL проверки сертификата сохранён: {cleaned or '(очищено)'}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📜 К платному сертификату", callback_data="tls_paid")]]
            ),
        )
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

    if ud.get("tls_edit_port"):
        domain = ud.get("tls_edit_port_domain", "")
        try:
            port = int(text)
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Порт должен быть числом от 1 до 65535.")
            return True
        domains = get_domains_config()
        if domain in domains:
            domains[domain]["port"] = port
            save_domains_config(domains)
            update.message.reply_text(f"✅ Порт для {domain}: {port}")
        else:
            update.message.reply_text("❌ Домен не найден.")
        ud.pop("tls_edit_port", None)
        ud.pop("tls_edit_port_domain", None)
        return True

    if ud.get("tls_edit_alert"):
        domain = ud.get("tls_edit_alert_domain", "")
        try:
            days = int(text)
            if days < 1 or days > 180:
                raise ValueError
        except ValueError:
            update.message.reply_text("❌ Введите число от 1 до 180.")
            return True
        domains = get_domains_config()
        if domain in domains:
            domains[domain]["alert_days"] = days
            save_domains_config(domains)
            update.message.reply_text(f"✅ Порог алерта для {domain}: {days} дн.")
        else:
            update.message.reply_text("❌ Домен не найден.")
        ud.pop("tls_edit_alert", None)
        ud.pop("tls_edit_alert_domain", None)
        return True

    stage = ud.get("tls_add_stage")
    if stage == "domain":
        domain = text.lower()
        if not domain or "." not in domain:
            update.message.reply_text("❌ Введите корректное имя домена.")
            return True
        if domain in get_domains_config():
            update.message.reply_text("❌ Такой домен уже есть.")
            return True
        ud["tls_new_domain"] = domain
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
        domain = str(ud.get("tls_new_domain", "")).strip()
        if not domain:
            for key in ("tls_add_stage", "tls_new_domain"):
                ud.pop(key, None)
            update.message.reply_text("❌ Ошибка. Повторите добавление.")
            return True
        domains = get_domains_config()
        domains[domain] = {
            "enabled": True,
            "port": port,
            "alert_days": get_settings().get("alert_days_default", 14),
        }
        save_domains_config(domains)
        for key in ("tls_add_stage", "tls_new_domain"):
            ud.pop(key, None)
        update.message.reply_text(
            f"✅ Домен {domain}:{port} добавлен.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📋 К доменам", callback_data="tls_domains_cfg")]]
            ),
        )
        return True

    return False


# ---------------------------------------------------------------------------
# Диспетчер callback'ов
# ---------------------------------------------------------------------------
def handle_callbacks(update, context, data: str):
    if data == "tls_cert_menu":
        show_menu(update, context)
    elif data == "tls_check_now":
        show_menu(update, context)
    elif data == "tls_domains":
        show_domains_reissue(update, context)
    elif data == "tls_settings":
        show_settings(update, context)
    elif data == "tls_domains_cfg":
        show_domains_cfg(update, context)
    elif data == "tls_paid":
        show_paid_menu(update, context)
    elif data == "tls_paid_cert":
        prompt_paid_upload(update, context, "cert")
    elif data == "tls_paid_key":
        prompt_paid_upload(update, context, "key")
    elif data == "tls_paid_match":
        check_paid_match(update, context)
    elif data == "tls_paid_check_url":
        check_paid_url(update, context)
    elif data == "tls_add":
        add_domain_prompt(update, context)
    elif data == "tls_reset":
        reset_domains(update, context)
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
            "🧩 *Команда certbot*\n\nВведите шаблон (используйте `{domain}`):\n"
            "`certbot certonly --nginx --cert-name {domain} -d {domain} --force-renewal`",
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
    elif data == "tls_set_paid_url":
        _prompt(
            update,
            context,
            "tls_set_paid_url",
            "🔗 *URL проверки сертификата*\n\nВведите URL живого эндпоинта, на котором "
            "отдаётся сертификат домена и его можно проверить на валидность "
            "(начиная с https://).\nОтправьте «-», чтобы очистить.",
        )
    elif data.startswith("tls_reissue_do_"):
        do_reissue(update, context, data[len("tls_reissue_do_") :])
    elif data.startswith("tls_reissue_"):
        confirm_reissue(update, context, data[len("tls_reissue_") :])
    elif data.startswith("tls_toggle_"):
        toggle_domain(update, context, data[len("tls_toggle_") :])
    elif data.startswith("tls_del_"):
        delete_domain(update, context, data[len("tls_del_") :])
    elif data.startswith("tls_port_"):
        edit_port_prompt(update, context, data[len("tls_port_") :])
    elif data.startswith("tls_alert_"):
        edit_alert_prompt(update, context, data[len("tls_alert_") :])
