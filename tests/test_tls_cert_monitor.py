"""
Unit-тесты расширения мониторинга TLS-сертификатов
(`extensions.tls_cert_monitor`).

Проверяют чистые функции (нормализация конфигурации доменов, парсинг дат
openssl, сборка статуса, поведение перевыпуска без SSH-хоста) и — при наличии
бинарника openssl — валидацию загруженного сертификата/ключа и проверку пары.
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timedelta

import pytest

OPENSSL = shutil.which("openssl")
requires_openssl = pytest.mark.skipif(OPENSSL is None, reason="openssl не установлен")


def test_normalize_domains_clamps_and_defaults() -> None:
    from extensions.tls_cert_monitor import normalize_domains

    result = normalize_domains(
        {
            "  API.202020.ru ": {"port": "8443", "alert_days": "300", "enabled": False},
            "bad.example": "не-словарь",
            "": {"port": 443},
            123: {"port": 443},
        }
    )

    assert "api.202020.ru" in result  # нормализация регистра и пробелов
    assert result["api.202020.ru"] == {"enabled": False, "port": 8443, "alert_days": 180}
    # Значение-строка превращается в дефолт.
    assert result["bad.example"] == {"enabled": True, "port": 443, "alert_days": 14}
    # Пустые/нестроковые ключи отбрасываются.
    assert "" not in result and 123 not in result


def test_normalize_domains_invalid_input() -> None:
    from extensions.tls_cert_monitor import normalize_domains

    assert normalize_domains(None) == {}
    assert normalize_domains("строка") == {}
    assert normalize_domains([1, 2, 3]) == {}


def test_parse_openssl_date() -> None:
    from extensions.tls_cert_monitor import _parse_openssl_date

    parsed = _parse_openssl_date("May 30 12:00:00 2026 GMT")
    assert parsed == datetime(2026, 5, 30, 12, 0, 0)
    assert _parse_openssl_date("чепуха") is None


def test_get_domains_config_falls_back_to_defaults(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    # Пустое хранилище → дефолтные пять доменов.
    monkeypatch.setattr(mod.config_manager, "get_setting", lambda *a, **k: {})
    cfg = mod.get_domains_config()
    assert set(cfg.keys()) == set(mod.DEFAULT_DOMAINS.keys())
    assert cfg["api.202020.ru"]["port"] == 8443


def test_get_settings_merges_defaults(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod.config_manager, "get_setting", lambda *a, **k: {"ssh_host": "10.0.0.5"})
    s = mod.get_settings()
    assert s["ssh_host"] == "10.0.0.5"
    # Остальное берётся из дефолтов.
    assert s["certbot_cmd"] == mod.DEFAULT_CERTBOT_CMD
    assert s["nginx_reload_cmd"] == mod.DEFAULT_NGINX_RELOAD_CMD


def test_reissue_without_ssh_host_returns_error(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod, "get_domains_config", lambda: {"api.202020.ru": {"port": 8443}})
    monkeypatch.setattr(mod, "get_settings", lambda: dict(mod.DEFAULT_SETTINGS))
    ok, msg = mod.reissue_certificate("api.202020.ru")
    assert ok is False
    assert "SSH" in msg


def test_reissue_unknown_domain(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod, "get_domains_config", lambda: {})
    ok, msg = mod.reissue_certificate("nope.example")
    assert ok is False
    assert "не настроен" in msg


def test_reissue_builds_command_and_calls_ssh(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    captured: dict = {}

    def fake_ssh(host, command, timeout):
        captured["host"] = host
        captured["command"] = command
        return True, "Congratulations! certificate issued", ""

    monkeypatch.setattr(mod, "get_domains_config", lambda: {"matrix.202020.ru": {"port": 443}})
    monkeypatch.setattr(
        mod,
        "get_settings",
        lambda: {
            **mod.DEFAULT_SETTINGS,
            "ssh_host": "10.0.0.5",
        },
    )
    monkeypatch.setattr(mod, "run_ssh_command", fake_ssh)

    ok, msg = mod.reissue_certificate("matrix.202020.ru")
    assert ok is True
    assert captured["host"] == "10.0.0.5"
    assert "--cert-name matrix.202020.ru" in captured["command"]
    assert "service nginx restart" in captured["command"]


def test_build_status_lines_renders_alert(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod, "get_paid_cert_info", lambda: {"ok": False, "error": None})
    results = [
        {
            "domain": "api.202020.ru",
            "port": 8443,
            "ok": True,
            "days_left": 5,
            "not_after": datetime(2026, 6, 4),
            "is_alert": True,
            "alert_days": 14,
        },
        {
            "domain": "rtc.202020.ru",
            "port": 443,
            "ok": False,
            "is_alert": True,
            "error": "таймаут",
        },
    ]
    text = "\n".join(mod.build_status_lines(results, ["❌ rtc.202020.ru:443: таймаут"]))
    assert "api.202020.ru:8443" in text
    assert "осталось 5 дн." in text
    assert "rtc.202020.ru" in text
    assert "не загружен" in text


def _make_self_signed(tmp_path):
    """Генерирует самоподписанный сертификат и ключ для тестов."""
    key = tmp_path / "k.pem"
    crt = tmp_path / "c.pem"
    subprocess.run(
        [
            OPENSSL,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(crt),
            "-days",
            "30",
            "-subj",
            "/CN=202020.ru",
        ],
        check=True,
        capture_output=True,
    )
    return crt.read_bytes(), key.read_bytes()


@requires_openssl
def test_validate_and_match_paid_certificate(tmp_path, monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    cert_bytes, key_bytes = _make_self_signed(tmp_path)

    store = tmp_path / "certs"
    monkeypatch.setattr(mod, "PAID_CERT_DIR", store)
    monkeypatch.setattr(mod, "PAID_CERT_FILE", store / "202020.ru.crt")
    monkeypatch.setattr(mod, "PAID_KEY_FILE", store / "202020.ru.key")

    ok, _ = mod.save_paid_certificate(cert_bytes)
    assert ok is True
    ok, _ = mod.save_paid_key(key_bytes)
    assert ok is True

    match_ok, match_msg = mod.certificate_key_match()
    assert match_ok is True, match_msg

    info = mod.get_paid_cert_info()
    assert info["ok"] is True
    assert info["has_key"] is True
    assert info["days_left"] is not None and info["days_left"] > 0


@requires_openssl
def test_validate_rejects_garbage(tmp_path, monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod, "PAID_CERT_DIR", tmp_path / "certs")
    ok, msg = mod.validate_certificate_pem(b"not a certificate")
    assert ok is False
    ok, msg = mod.validate_private_key_pem(b"not a key")
    assert ok is False


@requires_openssl
def test_mismatched_cert_and_key(tmp_path, monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    cert_a, _ = _make_self_signed(tmp_path)
    # Второй независимый ключ в отдельной папке.
    sub = tmp_path / "second"
    sub.mkdir()
    _, key_b = _make_self_signed(sub)

    store = tmp_path / "certs"
    monkeypatch.setattr(mod, "PAID_CERT_DIR", store)
    monkeypatch.setattr(mod, "PAID_CERT_FILE", store / "202020.ru.crt")
    monkeypatch.setattr(mod, "PAID_KEY_FILE", store / "202020.ru.key")

    mod.save_paid_certificate(cert_a)
    mod.save_paid_key(key_b)
    match_ok, _ = mod.certificate_key_match()
    assert match_ok is False
