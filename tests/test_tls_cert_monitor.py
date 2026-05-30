"""
Unit-тесты расширения мониторинга TLS-сертификатов
(`extensions.tls_cert_monitor`).

Проверяют чистые функции: нормализацию конфигурации сертификатов (cert-name,
хост проверки, домены `-d`), парсинг дат openssl, сборку статуса и поведение
перевыпуска (в т.ч. мультидоменного) certbot по SSH.
"""

from __future__ import annotations

from datetime import datetime

import pytest  # noqa: F401  (используется через monkeypatch-фикстуру)


def test_normalize_domains_clamps_and_defaults() -> None:
    from extensions.tls_cert_monitor import normalize_domains

    result = normalize_domains(
        {
            "api.202020.ru": {"port": "8443", "alert_days": "300", "enabled": False},
            "bad.example": "не-словарь",
            "": {"port": 443},
            123: {"port": 443},
        }
    )

    assert result["api.202020.ru"] == {
        "enabled": False,
        "check_host": "api.202020.ru",
        "port": 8443,
        "alert_days": 180,  # клампится к 180
        "domains": ["api.202020.ru"],
    }
    # Значение-строка превращается в дефолт с домен-списком из cert-name.
    assert result["bad.example"]["domains"] == ["bad.example"]
    assert result["bad.example"]["check_host"] == "bad.example"
    # Пустые/нестроковые ключи отбрасываются.
    assert "" not in result and 123 not in result


def test_normalize_domains_multidomain_and_check_host() -> None:
    from extensions.tls_cert_monitor import normalize_domains

    result = normalize_domains(
        {
            "202020.ru": {
                "check_host": "202020.ru",
                "port": 443,
                "domains": ["202020.ru", "www.202020.ru", "mail.202020.ru"],
            }
        }
    )
    entry = result["202020.ru"]
    assert entry["domains"] == ["202020.ru", "www.202020.ru", "mail.202020.ru"]
    assert entry["check_host"] == "202020.ru"


def test_normalize_domains_domains_from_string() -> None:
    from extensions.tls_cert_monitor import normalize_domains

    result = normalize_domains({"c": {"domains": "a.ru, b.ru  c.ru"}})
    assert result["c"]["domains"] == ["a.ru", "b.ru", "c.ru"]


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

    monkeypatch.setattr(mod.config_manager, "get_setting", lambda *a, **k: {})
    cfg = mod.get_domains_config()
    assert set(cfg.keys()) == set(mod.DEFAULT_CERTS.keys())
    assert "rtc.matrix.202020.ru" in cfg
    assert cfg["api.202020.ru"]["port"] == 8443
    # Мультидоменный сертификат 202020.ru.
    assert len(cfg["202020.ru"]["domains"]) > 1


def test_get_settings_merges_defaults(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod.config_manager, "get_setting", lambda *a, **k: {"ssh_host": "10.0.0.5"})
    s = mod.get_settings()
    assert s["ssh_host"] == "10.0.0.5"
    assert s["certbot_cmd"] == mod.DEFAULT_CERTBOT_CMD
    assert s["nginx_reload_cmd"] == mod.DEFAULT_NGINX_RELOAD_CMD


def test_reissue_without_ssh_host_returns_error(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(
        mod, "get_domains_config", lambda: {"api.202020.ru": {"domains": ["api.202020.ru"]}}
    )
    monkeypatch.setattr(mod, "get_settings", lambda: dict(mod.DEFAULT_SETTINGS))
    ok, msg = mod.reissue_certificate("api.202020.ru")
    assert ok is False
    assert "SSH" in msg


def test_reissue_unknown_cert(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    monkeypatch.setattr(mod, "get_domains_config", lambda: {})
    ok, msg = mod.reissue_certificate("nope.example")
    assert ok is False
    assert "не настроен" in msg


def test_reissue_multidomain_builds_all_d_args(monkeypatch) -> None:
    import extensions.tls_cert_monitor as mod

    captured: dict = {}

    def fake_ssh(host, command, timeout):
        captured["host"] = host
        captured["command"] = command
        return True, "Congratulations! certificate issued", ""

    monkeypatch.setattr(
        mod,
        "get_domains_config",
        lambda: {"202020.ru": {"domains": ["202020.ru", "www.202020.ru", "mail.202020.ru"]}},
    )
    monkeypatch.setattr(
        mod, "get_settings", lambda: {**mod.DEFAULT_SETTINGS, "ssh_host": "10.0.0.5"}
    )
    monkeypatch.setattr(mod, "run_ssh_command", fake_ssh)

    ok, _msg = mod.reissue_certificate("202020.ru")
    assert ok is True
    assert captured["host"] == "10.0.0.5"
    assert "--cert-name 202020.ru" in captured["command"]
    # Все домены попали в аргументы -d.
    assert "-d 202020.ru" in captured["command"]
    assert "-d www.202020.ru" in captured["command"]
    assert "-d mail.202020.ru" in captured["command"]
    assert "service nginx restart" in captured["command"]


def test_build_status_lines_renders_cert_name_and_alert() -> None:
    import extensions.tls_cert_monitor as mod

    results = [
        {
            "cert_name": "api.202020.ru",
            "check_host": "api.202020.ru",
            "port": 8443,
            "ok": True,
            "days_left": 5,
            "not_after": datetime(2026, 6, 4),
            "is_alert": True,
            "alert_days": 14,
            "domains": ["api.202020.ru"],
        },
        {
            "cert_name": "202020.ru",
            "check_host": "202020.ru",
            "port": 443,
            "ok": True,
            "days_left": 64,
            "not_after": datetime(2026, 8, 3),
            "is_alert": False,
            "alert_days": 14,
            "domains": ["202020.ru", "www.202020.ru"],
        },
    ]
    text = "\n".join(mod.build_status_lines(results, []))
    assert "api.202020.ru" in text
    assert "api.202020.ru:8443" in text
    assert "осталось 5 дн." in text
    # Мультидоменный сертификат помечается числом доменов.
    assert "2 доменов" in text
    # Платный сертификат больше не упоминается.
    assert "латный" not in text


def test_matrix_bot_exposes_tls_extension() -> None:
    """Расширение TLS должно быть встроено в Matrix-бота (меню + настройки)."""
    import lib.matrix_commands as m

    ids = [item.extension_id for item in m.EXTENSION_MENU_ITEMS]
    assert "tls_cert_monitor" in ids
    assert m._EXT_ITEM_BY_COMMAND.get("!tls") is not None
    assert hasattr(m.MatrixCommandBot, "_handle_ext_tls_cert")
    settings = dict(m._EXTENSION_SETTINGS)
    assert "tls_cert_monitor" in settings
    assert "TLS_CERT_DOMAINS" in settings["tls_cert_monitor"]["keys"]
