"""
/extensions/tls_cert_monitor.py
Server Monitoring System v8.62.79
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
TLS certificate monitor: expiry checks and manual certbot re-issue over SSH.
Система мониторинга серверов
Версия: 8.62.79
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг TLS-сертификатов: проверка срока и ручной перевыпуск certbot по SSH.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Any

from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from extensions.server_checks import run_ssh_command
from lib.logging import debug_log

EXTENSION_ID = "tls_cert_monitor"

# Ключи настроек в config_manager (settings.db).
# DOMAINS_SETTING_KEY исторически хранит карту сертификатов (ключ — cert-name
# certbot). Имя ключа сохранено ради обратной совместимости с уже сохранёнными
# конфигурациями.
DOMAINS_SETTING_KEY = "TLS_CERT_DOMAINS"
SETTINGS_KEY = "TLS_CERT_SETTINGS"

# Сертификаты под управлением certbot (по cert-name). Для каждого:
# - check_host: хост, к которому подключаемся для живой проверки (по умолчанию
#   совпадает с cert-name);
# - port: порт живой проверки;
# - alert_days: порог алерта по сроку;
# - domains: список доменов для аргументов `-d` при перевыпуске (по умолчанию
#   [cert-name]). Для мультидоменных сертификатов перечисляются все SAN.
DEFAULT_CERTS: dict[str, dict[str, Any]] = {
    "api.202020.ru": {
        "enabled": True,
        "check_host": "api.202020.ru",
        "port": 8443,
        "alert_days": 14,
        "domains": ["api.202020.ru"],
    },
    "rtc.matrix.202020.ru": {
        "enabled": True,
        "check_host": "rtc.matrix.202020.ru",
        "port": 443,
        "alert_days": 14,
        "domains": ["rtc.matrix.202020.ru"],
    },
    "202020.ru": {
        "enabled": True,
        "check_host": "202020.ru",
        "port": 443,
        "alert_days": 14,
        "domains": [
            "202020.ru",
            "911.202020.ru",
            "ban.202020.ru",
            "cloud.202020.ru",
            "ez.202020.ru",
            "goods.202020.ru",
            "help.202020.ru",
            "mail.202020.ru",
            "office.202020.ru",
            "statement.202020.ru",
            "static.202020.ru",
            "wiki.202020.ru",
            "www.202020.ru",
        ],
    },
    "chat.202020.ru": {
        "enabled": True,
        "check_host": "chat.202020.ru",
        "port": 443,
        "alert_days": 14,
        "domains": ["chat.202020.ru"],
    },
    "share.202020.ru": {
        "enabled": True,
        "check_host": "share.202020.ru",
        "port": 443,
        "alert_days": 14,
        "domains": ["share.202020.ru"],
    },
    "matrix.202020.ru": {
        "enabled": True,
        "check_host": "matrix.202020.ru",
        "port": 443,
        "alert_days": 14,
        "domains": ["matrix.202020.ru"],
    },
}

# Обратная совместимость со старым именем константы.
DEFAULT_DOMAINS = DEFAULT_CERTS

# Шаблон перевыпуска. {cert_name} — имя сертификата certbot, {domain_args} —
# подставляемые аргументы `-d <домен>` для всех доменов сертификата.
DEFAULT_CERTBOT_CMD = (
    "certbot certonly --nginx --cert-name {cert_name} {domain_args} --force-renewal"
)
DEFAULT_NGINX_RELOAD_CMD = "service nginx restart"

DEFAULT_SETTINGS: dict[str, Any] = {
    "ssh_host": "",
    "certbot_cmd": DEFAULT_CERTBOT_CMD,
    "nginx_reload_cmd": DEFAULT_NGINX_RELOAD_CMD,
    "alert_days_default": 14,
    "reissue_timeout": 300,
}

_ALERT_SENT_AT: dict[str, datetime] = {}
_ALERT_ACTIVE: dict[str, bool] = {}


# ---------------------------------------------------------------------------
# Конфигурация сертификатов (ключ — cert-name certbot)
# ---------------------------------------------------------------------------
def normalize_domains(raw_value: Any) -> dict[str, dict[str, Any]]:
    """Приводит конфигурацию сертификатов к каноничному виду.

    Совместима со старой схемой `{domain: {enabled, port, alert_days}}` —
    отсутствующие `check_host`/`domains` достраиваются из имени сертификата.
    """
    if not isinstance(raw_value, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for cert_name, cert_value in raw_value.items():
        if not isinstance(cert_name, str) or not cert_name.strip():
            continue

        key = cert_name.strip()
        if isinstance(cert_value, dict):
            enabled = bool(cert_value.get("enabled", True))
            check_host = str(cert_value.get("check_host", "") or "").strip() or key
            port = cert_value.get("port", 443)
            alert_days = cert_value.get("alert_days", 14)
            raw_domains = cert_value.get("domains")
        else:
            enabled = True
            check_host = key
            port = 443
            alert_days = 14
            raw_domains = None

        try:
            port_int = int(port)
        except (TypeError, ValueError):
            port_int = 443
        port_int = max(1, min(65535, port_int))

        try:
            alert_days_int = int(alert_days)
        except (TypeError, ValueError):
            alert_days_int = 14
        alert_days_int = max(1, min(180, alert_days_int))

        if isinstance(raw_domains, (list, tuple)):
            domains = [str(d).strip() for d in raw_domains if str(d).strip()]
        elif isinstance(raw_domains, str) and raw_domains.strip():
            domains = [
                part.strip() for part in raw_domains.replace(",", " ").split() if part.strip()
            ]
        else:
            domains = []
        if not domains:
            domains = [key]

        normalized[key] = {
            "enabled": enabled,
            "check_host": check_host,
            "port": port_int,
            "alert_days": alert_days_int,
            "domains": domains,
        }
    return normalized


def get_domains_config() -> dict[str, dict[str, Any]]:
    """Возвращает сертификаты из настроек, при пустой конфигурации — дефолты."""
    stored = normalize_domains(config_manager.get_setting(DOMAINS_SETTING_KEY, {}))
    if stored:
        return stored
    return normalize_domains(DEFAULT_CERTS)


def save_domains_config(domains: dict[str, dict[str, Any]]) -> None:
    config_manager.set_setting(DOMAINS_SETTING_KEY, normalize_domains(domains))


# ---------------------------------------------------------------------------
# Глобальные настройки расширения
# ---------------------------------------------------------------------------
def get_settings() -> dict[str, Any]:
    """Возвращает глобальные настройки с подстановкой дефолтов."""
    stored = config_manager.get_setting(SETTINGS_KEY, {})
    result = dict(DEFAULT_SETTINGS)
    if isinstance(stored, dict):
        for key in DEFAULT_SETTINGS:
            if key in stored and stored[key] not in (None, ""):
                result[key] = stored[key]
    try:
        result["alert_days_default"] = int(result["alert_days_default"])
    except (TypeError, ValueError):
        result["alert_days_default"] = 14
    try:
        result["reissue_timeout"] = int(result["reissue_timeout"])
    except (TypeError, ValueError):
        result["reissue_timeout"] = 300
    return result


def save_settings(settings: dict[str, Any]) -> None:
    current = config_manager.get_setting(SETTINGS_KEY, {})
    if not isinstance(current, dict):
        current = {}
    current.update(settings)
    config_manager.set_setting(SETTINGS_KEY, current)


# ---------------------------------------------------------------------------
# Чтение живого сертификата эндпоинта через openssl
# ---------------------------------------------------------------------------
def _parse_openssl_date(value: str) -> datetime | None:
    """Парсит дату формата openssl `notAfter` (e.g. `May 30 12:00:00 2026 GMT`)."""
    value = value.strip()
    for fmt in ("%b %d %H:%M:%S %Y %Z", "%b %d %H:%M:%S %Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def check_certificate(domain: str, port: int = 443, timeout: int = 12) -> dict[str, Any]:
    """Считывает сертификат, который эндпоинт реально отдаёт по TLS.

    Использует openssl s_client — это устойчиво к истёкшим/недоверенным
    сертификатам (в отличие от ssl.getpeercert, требующего валидации).
    """
    result: dict[str, Any] = {
        "domain": domain,
        "port": port,
        "ok": False,
        "not_after": None,
        "days_left": None,
        "issuer": None,
        "subject": None,
        "error": None,
    }

    command = (
        f"echo | openssl s_client -connect {domain}:{port} -servername {domain} "
        f"2>/dev/null | openssl x509 -noout -enddate -issuer -subject"
    )
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "таймаут TLS-подключения"
        return result
    except Exception as exc:  # pragma: no cover - защитный код
        result["error"] = str(exc)
        return result

    output = (proc.stdout or "").strip()
    if not output:
        result["error"] = (proc.stderr or "не удалось прочитать сертификат").strip()[:160]
        return result

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("notAfter="):
            not_after_raw = line[len("notAfter=") :].strip()
            parsed = _parse_openssl_date(not_after_raw)
            if parsed:
                result["not_after"] = parsed
                result["days_left"] = (parsed - datetime.utcnow()).days
        elif line.startswith("issuer="):
            result["issuer"] = line[len("issuer=") :].strip()
        elif line.startswith("subject="):
            result["subject"] = line[len("subject=") :].strip()

    if result["not_after"] is not None:
        result["ok"] = True
    else:
        result["error"] = "не удалось разобрать срок действия сертификата"
    return result


def collect_certificates() -> tuple[list[dict[str, Any]], list[str]]:
    """Опрашивает все включённые сертификаты, возвращает статусы и ошибки."""
    certs = get_domains_config()
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for cert_name in sorted(certs.keys()):
        cfg = certs[cert_name]
        if not cfg.get("enabled", True):
            continue
        check_host = str(cfg.get("check_host") or cert_name).strip() or cert_name
        port = int(cfg.get("port", 443))
        alert_days = int(cfg.get("alert_days", 14))
        info = check_certificate(check_host, port)
        info["cert_name"] = cert_name
        info["check_host"] = check_host
        info["alert_days"] = alert_days
        info["domains"] = list(cfg.get("domains") or [cert_name])
        if info.get("ok"):
            info["is_alert"] = info["days_left"] is not None and info["days_left"] <= alert_days
        else:
            info["is_alert"] = True
            errors.append(f"❌ {cert_name} ({check_host}:{port}): {info.get('error', 'ошибка')}")
        results.append(info)

    return results, errors


def build_status_lines(results: list[dict[str, Any]], errors: list[str]) -> list[str]:
    """Текст статуса сертификатов для Telegram (Markdown)."""
    lines: list[str] = ["🔐 *TLS-сертификаты*", ""]

    if not results:
        lines.append("❌ Нет сертификатов для проверки.")
    else:
        alerts = sum(1 for r in results if r.get("is_alert"))
        lines.append(f"• Сертификатов: {len(results)} · 🚨 {alerts}")
        lines.append("")
        for r in results:
            cert_name = r.get("cert_name", r.get("domain"))
            check_host = r.get("check_host", r.get("domain"))
            port = r["port"]
            target = f"{check_host}:{port}"
            if not r.get("ok"):
                lines.append(f"❌ `{cert_name}` ({target}) — {r.get('error', 'ошибка')}")
                continue
            days = r.get("days_left")
            if r.get("is_alert"):
                icon = "🚨" if (days is None or days >= 0) else "⛔️"
            else:
                icon = "🟢"
            end = r["not_after"].strftime("%Y-%m-%d") if r.get("not_after") else "?"
            extra = ""
            domains = r.get("domains") or []
            if len(domains) > 1:
                extra = f" · {len(domains)} доменов"
            lines.append(f"{icon} `{cert_name}` ({target}) — осталось {days} дн. (до {end}){extra}")
        lines.append("")

    if errors:
        lines.append("*Ошибки опроса:*")
        lines.extend(errors)
        lines.append("")

    lines.append(f"🕒 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return lines


# ---------------------------------------------------------------------------
# Перевыпуск через certbot по SSH
# ---------------------------------------------------------------------------
def reissue_certificate(cert_name: str) -> tuple[bool, str]:
    """Перевыпускает сертификат (по cert-name) certbot'ом по SSH.

    Подставляет все домены сертификата в аргументы `-d`. Возвращает
    (успех, текстовое_сообщение).
    """
    certs = get_domains_config()
    if cert_name not in certs:
        return False, f"Сертификат {cert_name} не настроен."

    cfg = certs[cert_name]
    domains = list(cfg.get("domains") or [cert_name])

    settings = get_settings()
    ssh_host = str(settings.get("ssh_host", "")).strip()
    if not ssh_host:
        return False, ("Не задан SSH-хост с certbot/nginx.\nУкажите его в ⚙️ Настройках расширения.")

    certbot_cmd = str(settings.get("certbot_cmd") or DEFAULT_CERTBOT_CMD)
    nginx_cmd = str(settings.get("nginx_reload_cmd") or DEFAULT_NGINX_RELOAD_CMD)
    timeout = int(settings.get("reissue_timeout", 300))

    domain_args = " ".join(f"-d {d}" for d in domains)
    try:
        certbot_part = certbot_cmd.format(
            cert_name=cert_name,
            domain_args=domain_args,
            # обратная совместимость со старым шаблоном `{domain}`
            domain=cert_name,
        )
    except (KeyError, IndexError, ValueError):
        certbot_part = (
            f"certbot certonly --nginx --cert-name {cert_name} {domain_args} --force-renewal"
        )

    full_command = f"{certbot_part} && {nginx_cmd}"
    debug_log(f"🔐 TLS reissue {cert_name} on {ssh_host}: {full_command}")

    success, stdout, stderr = run_ssh_command(ssh_host, full_command, timeout=timeout)
    if success:
        tail = (stdout or "").strip().splitlines()[-4:]
        details = "\n".join(tail) if tail else "выполнено"
        return True, f"✅ Сертификат {cert_name} перевыпущен.\n{details}"

    err = (stderr or stdout or "неизвестная ошибка").strip()
    return False, f"❌ Не удалось перевыпустить {cert_name}:\n{err[:400]}"


# ---------------------------------------------------------------------------
# Плановая проверка истечения сертификатов (вызывается из lifecycle loop)
# ---------------------------------------------------------------------------
def check_tls_cert_alerts(send_alert_func, repeat_interval_seconds: int = 1800) -> None:
    """Периодическая проверка сроков сертификатов и алертинг."""
    if not extension_manager.is_extension_enabled(EXTENSION_ID):
        return

    now = datetime.now()
    results, errors = collect_certificates()
    if errors:
        debug_log(f"⚠️ TLS cert polling issues: {'; '.join(errors)}")

    for r in results:
        cert_name = r.get("cert_name", r.get("domain"))
        key = f"{cert_name}:{r.get('port', 0)}"
        is_alert = bool(r.get("is_alert"))
        was_alert = _ALERT_ACTIVE.get(key, False)
        last_sent_at = _ALERT_SENT_AT.get(key)

        if is_alert:
            should_send = (
                not was_alert
                or last_sent_at is None
                or (now - last_sent_at).total_seconds() >= repeat_interval_seconds
            )
            if should_send:
                if not r.get("ok"):
                    send_alert_func(
                        "🔐 TLS: проблема с сертификатом\n"
                        f"• Сертификат: {cert_name} ({r.get('check_host')}:{r.get('port', '')})\n"
                        f"• Ошибка: {r.get('error', 'неизвестно')}"
                    )
                else:
                    days = r.get("days_left")
                    send_alert_func(
                        "🔐 TLS: сертификат скоро истекает\n"
                        f"• Сертификат: {cert_name}\n"
                        f"• Осталось: {days} дн.\n"
                        f"• Порог: {r.get('alert_days')} дн."
                    )
                _ALERT_SENT_AT[key] = now
            _ALERT_ACTIVE[key] = True
            continue

        if was_alert:
            send_alert_func(
                "✅ TLS: сертификат в норме\n"
                f"• Сертификат: {cert_name}\n"
                f"• Осталось: {r.get('days_left')} дн."
            )
        _ALERT_ACTIVE[key] = False
