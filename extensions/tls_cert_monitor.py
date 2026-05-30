"""
/extensions/tls_cert_monitor.py
Server Monitoring System v8.62.73
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
TLS certificate monitor: expiry checks, manual certbot re-issue over SSH and
manual upload of the paid 202020.ru certificate.
Система мониторинга серверов
Версия: 8.62.73
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг TLS-сертификатов: проверка срока, ручной перевыпуск через certbot по
SSH и ручная загрузка платного сертификата 202020.ru.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import DATA_DIR
from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from extensions.server_checks import run_ssh_command
from lib.logging import debug_log

EXTENSION_ID = "tls_cert_monitor"

# Ключи настроек в config_manager (settings.db).
DOMAINS_SETTING_KEY = "TLS_CERT_DOMAINS"
SETTINGS_KEY = "TLS_CERT_SETTINGS"

# Платный wildcard/одиночный сертификат, который ставится вручную.
PAID_CERT_DOMAIN = "202020.ru"
PAID_CERT_DIR = Path(DATA_DIR) / "certificates"
PAID_CERT_FILE = PAID_CERT_DIR / "202020.ru.crt"
PAID_KEY_FILE = PAID_CERT_DIR / "202020.ru.key"

# Домены под управлением certbot (перевыпуск по кнопке).
DEFAULT_DOMAINS: dict[str, dict[str, Any]] = {
    "api.202020.ru": {"enabled": True, "port": 8443, "alert_days": 14},
    "rtc.202020.ru": {"enabled": True, "port": 443, "alert_days": 14},
    "chat.202020.ru": {"enabled": True, "port": 443, "alert_days": 14},
    "share.202020.ru": {"enabled": True, "port": 443, "alert_days": 14},
    "matrix.202020.ru": {"enabled": True, "port": 443, "alert_days": 14},
}

# Шаблон перевыпуска повторяет ручную команду пользователя. {domain} —
# подстановка имени домена. Команда выполняется на SSH-хосте с certbot/nginx.
DEFAULT_CERTBOT_CMD = "certbot certonly --nginx --cert-name {domain} -d {domain} --force-renewal"
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
# Конфигурация доменов
# ---------------------------------------------------------------------------
def normalize_domains(raw_value: Any) -> dict[str, dict[str, Any]]:
    """Приводит конфигурацию доменов к каноничному виду."""
    if not isinstance(raw_value, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for domain_name, domain_value in raw_value.items():
        if not isinstance(domain_name, str) or not domain_name.strip():
            continue

        key = domain_name.strip().lower()
        if isinstance(domain_value, dict):
            enabled = bool(domain_value.get("enabled", True))
            port = domain_value.get("port", 443)
            alert_days = domain_value.get("alert_days", 14)
        else:
            enabled = True
            port = 443
            alert_days = 14

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

        normalized[key] = {
            "enabled": enabled,
            "port": port_int,
            "alert_days": alert_days_int,
        }
    return normalized


def get_domains_config() -> dict[str, dict[str, Any]]:
    """Возвращает домены из настроек, при пустой конфигурации — дефолты."""
    stored = normalize_domains(config_manager.get_setting(DOMAINS_SETTING_KEY, {}))
    if stored:
        return stored
    return normalize_domains(DEFAULT_DOMAINS)


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
    """Опрашивает все включённые домены, возвращает статусы и ошибки."""
    domains = get_domains_config()
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for domain_name in sorted(domains.keys()):
        cfg = domains[domain_name]
        if not cfg.get("enabled", True):
            continue
        port = int(cfg.get("port", 443))
        alert_days = int(cfg.get("alert_days", 14))
        info = check_certificate(domain_name, port)
        info["alert_days"] = alert_days
        if info.get("ok"):
            info["is_alert"] = info["days_left"] is not None and info["days_left"] <= alert_days
        else:
            info["is_alert"] = True
            errors.append(f"❌ {domain_name}:{port}: {info.get('error', 'ошибка')}")
        results.append(info)

    return results, errors


def build_status_lines(results: list[dict[str, Any]], errors: list[str]) -> list[str]:
    """Текст статуса сертификатов для Telegram (Markdown)."""
    lines: list[str] = ["🔐 *TLS-сертификаты*", ""]

    if not results:
        lines.append("❌ Нет доменов для проверки.")
    else:
        alerts = sum(1 for r in results if r.get("is_alert"))
        lines.append(f"• Доменов: {len(results)} · 🚨 {alerts}")
        lines.append("")
        for r in results:
            domain = r["domain"]
            port = r["port"]
            if not r.get("ok"):
                lines.append(f"❌ `{domain}:{port}` — {r.get('error', 'ошибка')}")
                continue
            days = r.get("days_left")
            if r.get("is_alert"):
                icon = "🚨" if (days is None or days >= 0) else "⛔️"
            else:
                icon = "🟢"
            end = r["not_after"].strftime("%Y-%m-%d") if r.get("not_after") else "?"
            lines.append(f"{icon} `{domain}:{port}` — осталось {days} дн. (до {end})")
        lines.append("")

    # Платный сертификат 202020.ru.
    paid = get_paid_cert_info()
    lines.append("*Платный сертификат* `202020.ru`")
    if paid.get("ok"):
        end = paid["not_after"].strftime("%Y-%m-%d") if paid.get("not_after") else "?"
        lines.append(f"   └ загружен · осталось {paid.get('days_left')} дн. (до {end})")
    elif paid.get("error"):
        lines.append(f"   └ {paid['error']}")
    else:
        lines.append("   └ не загружен")
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
def reissue_certificate(domain: str) -> tuple[bool, str]:
    """Перевыпускает сертификат домена certbot'ом на удалённом хосте по SSH.

    Возвращает (успех, текстовое_сообщение).
    """
    domains = get_domains_config()
    if domain not in domains:
        return False, f"Домен {domain} не настроен."

    settings = get_settings()
    ssh_host = str(settings.get("ssh_host", "")).strip()
    if not ssh_host:
        return False, (
            "Не задан SSH-хост с certbot/nginx.\n" "Укажите его в ⚙️ Настройках расширения."
        )

    certbot_cmd = str(settings.get("certbot_cmd") or DEFAULT_CERTBOT_CMD)
    nginx_cmd = str(settings.get("nginx_reload_cmd") or DEFAULT_NGINX_RELOAD_CMD)
    timeout = int(settings.get("reissue_timeout", 300))

    try:
        certbot_part = certbot_cmd.format(domain=domain)
    except (KeyError, IndexError, ValueError):
        certbot_part = certbot_cmd

    full_command = f"{certbot_part} && {nginx_cmd}"
    debug_log(f"🔐 TLS reissue {domain} on {ssh_host}: {full_command}")

    success, stdout, stderr = run_ssh_command(ssh_host, full_command, timeout=timeout)
    if success:
        tail = (stdout or "").strip().splitlines()[-4:]
        details = "\n".join(tail) if tail else "выполнено"
        return True, f"✅ Сертификат {domain} перевыпущен.\n{details}"

    err = (stderr or stdout or "неизвестная ошибка").strip()
    return False, f"❌ Не удалось перевыпустить {domain}:\n{err[:400]}"


# ---------------------------------------------------------------------------
# Платный сертификат 202020.ru: загрузка и валидация
# ---------------------------------------------------------------------------
def _openssl_cert_info(cert_path: Path) -> dict[str, Any]:
    """Возвращает срок/issuer/subject из PEM-файла сертификата."""
    info: dict[str, Any] = {
        "ok": False,
        "not_after": None,
        "days_left": None,
        "issuer": None,
        "subject": None,
        "error": None,
    }
    try:
        proc = subprocess.run(
            ["openssl", "x509", "-noout", "-enddate", "-issuer", "-subject", "-in", str(cert_path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - защитный код
        info["error"] = str(exc)
        return info

    if proc.returncode != 0:
        info["error"] = (proc.stderr or "невалидный сертификат").strip()[:160]
        return info

    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("notAfter="):
            parsed = _parse_openssl_date(line[len("notAfter=") :])
            if parsed:
                info["not_after"] = parsed
                info["days_left"] = (parsed - datetime.utcnow()).days
        elif line.startswith("issuer="):
            info["issuer"] = line[len("issuer=") :].strip()
        elif line.startswith("subject="):
            info["subject"] = line[len("subject=") :].strip()

    info["ok"] = info["not_after"] is not None
    if not info["ok"] and not info["error"]:
        info["error"] = "не удалось разобрать срок действия"
    return info


def validate_certificate_pem(data: bytes) -> tuple[bool, str]:
    """Проверяет, что переданные байты — валидный PEM-сертификат."""
    if b"BEGIN CERTIFICATE" not in data:
        return False, "Файл не похож на PEM-сертификат (нет BEGIN CERTIFICATE)."
    PAID_CERT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = PAID_CERT_DIR / ".tmp_cert.pem"
    try:
        tmp.write_bytes(data)
        info = _openssl_cert_info(tmp)
    finally:
        tmp.unlink(missing_ok=True)
    if not info.get("ok"):
        return False, info.get("error", "невалидный сертификат")
    return True, "ok"


def validate_private_key_pem(data: bytes) -> tuple[bool, str]:
    """Проверяет, что переданные байты — валидный приватный ключ PEM."""
    if b"PRIVATE KEY" not in data:
        return False, "Файл не похож на приватный ключ PEM."
    PAID_CERT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = PAID_CERT_DIR / ".tmp_key.pem"
    try:
        tmp.write_bytes(data)
        proc = subprocess.run(
            ["openssl", "pkey", "-in", str(tmp), "-noout"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - защитный код
        tmp.unlink(missing_ok=True)
        return False, str(exc)
    finally:
        tmp.unlink(missing_ok=True)
    if proc.returncode != 0:
        return False, (proc.stderr or "невалидный приватный ключ").strip()[:160]
    return True, "ok"


def _pubkey_of_cert(cert_path: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["openssl", "x509", "-in", str(cert_path), "-pubkey", "-noout"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:  # pragma: no cover
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _pubkey_of_key(key_path: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["openssl", "pkey", "-in", str(key_path), "-pubout"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:  # pragma: no cover
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def certificate_key_match() -> tuple[bool, str]:
    """Проверяет, что загруженные cert и key — это пара (совпадают pubkey)."""
    if not PAID_CERT_FILE.exists() or not PAID_KEY_FILE.exists():
        return False, "Загружены не оба файла (нужны и сертификат, и ключ)."
    cert_pub = _pubkey_of_cert(PAID_CERT_FILE)
    key_pub = _pubkey_of_key(PAID_KEY_FILE)
    if not cert_pub or not key_pub:
        return False, "Не удалось извлечь публичные ключи для сравнения."
    if cert_pub != key_pub:
        return False, "Сертификат и ключ не соответствуют друг другу."
    return True, "Сертификат и ключ совпадают."


def save_paid_certificate(data: bytes) -> tuple[bool, str]:
    """Валидирует и сохраняет платный сертификат в data/certificates."""
    ok, msg = validate_certificate_pem(data)
    if not ok:
        return False, msg
    PAID_CERT_DIR.mkdir(parents=True, exist_ok=True)
    PAID_CERT_FILE.write_bytes(data)
    try:
        os.chmod(PAID_CERT_FILE, 0o644)
    except OSError:
        pass
    info = _openssl_cert_info(PAID_CERT_FILE)
    end = info["not_after"].strftime("%Y-%m-%d") if info.get("not_after") else "?"
    return True, f"Сертификат сохранён (действует до {end})."


def save_paid_key(data: bytes) -> tuple[bool, str]:
    """Валидирует и сохраняет приватный ключ платного сертификата."""
    ok, msg = validate_private_key_pem(data)
    if not ok:
        return False, msg
    PAID_CERT_DIR.mkdir(parents=True, exist_ok=True)
    PAID_KEY_FILE.write_bytes(data)
    try:
        os.chmod(PAID_KEY_FILE, 0o600)
    except OSError:
        pass
    return True, "Приватный ключ сохранён."


def get_paid_cert_info() -> dict[str, Any]:
    """Информация о загруженном платном сертификате 202020.ru."""
    if not PAID_CERT_FILE.exists():
        return {"ok": False, "error": None, "has_key": PAID_KEY_FILE.exists()}
    info = _openssl_cert_info(PAID_CERT_FILE)
    info["has_key"] = PAID_KEY_FILE.exists()
    info["cert_path"] = str(PAID_CERT_FILE)
    info["key_path"] = str(PAID_KEY_FILE)
    return info


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

    # Плановая проверка платного сертификата по дефолтному порогу.
    paid = get_paid_cert_info()
    if paid.get("ok"):
        alert_days = get_settings().get("alert_days_default", 14)
        results.append(
            {
                "domain": PAID_CERT_DOMAIN,
                "port": 0,
                "ok": True,
                "days_left": paid.get("days_left"),
                "not_after": paid.get("not_after"),
                "is_alert": (
                    paid.get("days_left") is not None and paid["days_left"] <= int(alert_days)
                ),
                "alert_days": int(alert_days),
                "issuer": paid.get("issuer"),
            }
        )

    for r in results:
        key = f"{r['domain']}:{r.get('port', 0)}"
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
                        f"• Домен: {r['domain']}:{r.get('port', '')}\n"
                        f"• Ошибка: {r.get('error', 'неизвестно')}"
                    )
                else:
                    days = r.get("days_left")
                    send_alert_func(
                        "🔐 TLS: сертификат скоро истекает\n"
                        f"• Домен: {r['domain']}\n"
                        f"• Осталось: {days} дн.\n"
                        f"• Порог: {r.get('alert_days')} дн."
                    )
                _ALERT_SENT_AT[key] = now
            _ALERT_ACTIVE[key] = True
            continue

        if was_alert:
            send_alert_func(
                "✅ TLS: сертификат в норме\n"
                f"• Домен: {r['domain']}\n"
                f"• Осталось: {r.get('days_left')} дн."
            )
        _ALERT_ACTIVE[key] = False
