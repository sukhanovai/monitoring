"""
Тесты расширения mail_cert_monitor: разбор темы CERT, сохранение событий,
статус и одноразовая рассылка оповещений.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime

import pytest

import extensions.mail_cert_monitor as mod


@pytest.fixture()
def db_path(tmp_path) -> str:
    from modules.mail_parts.db.schema import create_schema

    path = str(tmp_path / "backups.db")
    conn = sqlite3.connect(path)
    try:
        create_schema(conn)
    finally:
        conn.close()
    return path


@pytest.fixture(autouse=True)
def _enabled(monkeypatch):
    monkeypatch.setattr(mod.extension_manager, "is_extension_enabled", lambda ext_id: True)
    mod._STALE_ALERT_SENT_AT.clear()


@pytest.mark.parametrize(
    "subject,level,event,params",
    [
        (
            "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89",
            "OK",
            "DEPLOYED",
            {"until": "2027-01-22", "days": "89"},
        ),
        ("CERT WARN sr-pve2 CT101 EXPIRING days=13", "WARN", "EXPIRING", {"days": "13"}),
        ("CERT CRIT sr-pve2 CT101 DEPLOY_FAILED rc=1", "CRIT", "DEPLOY_FAILED", {"rc": "1"}),
        (
            "CERT CRIT sr-pve2 CT101 SRC_MISSING file=cert.pem",
            "CRIT",
            "SRC_MISSING",
            {"file": "cert.pem"},
        ),
        ("CERT CRIT sr-pve2 CT101 SRC_EXPIRED", "CRIT", "SRC_EXPIRED", {}),
        ("CERT CRIT sr-pve2 CT101 SAN_MISMATCH", "CRIT", "SAN_MISMATCH", {}),
        ("CERT CRIT sr-pve2 CT101 KEY_MISMATCH", "CRIT", "KEY_MISMATCH", {}),
        ("CERT CRIT sr-pve2 CT101 NOT_RSA", "CRIT", "NOT_RSA", {}),
        ("CERT CRIT sr-pve2 CT101 CT_DOWN", "CRIT", "CT_DOWN", {}),
    ],
)
def test_parse_all_documented_subjects(subject, level, event, params) -> None:
    parsed = mod.parse_cert_subject(subject)
    assert parsed is not None
    assert parsed["level"] == level
    assert parsed["host_name"] == "sr-pve2"
    assert parsed["ct_id"] == "101"
    assert parsed["event"] == event
    assert parsed["params"] == params
    assert event in mod.EVENT_DESCRIPTIONS


def test_parse_extracts_until_and_days() -> None:
    parsed = mod.parse_cert_subject("CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89")
    assert parsed["until_date"] == "2027-01-22"
    assert parsed["days_left"] == 89


@pytest.mark.parametrize(
    "subject",
    [
        "",
        "Config backup pve3 OK",
        "NAS transfer sr-bup OK",
        "CERT INFO sr-pve2 CT101 DEPLOYED",
        "CERT OK sr-pve2 101 DEPLOYED",
        "Re: CERT OK sr-pve2 CT101 DEPLOYED",
    ],
)
def test_parse_rejects_foreign_subjects(subject) -> None:
    assert mod.parse_cert_subject(subject) is None


def test_parse_accepts_positional_pattern_from_spec() -> None:
    """Паттерн из ТЗ без именованных групп тоже работает."""
    spec = r"^CERT (OK|WARN|CRIT) (\S+) CT(\d+) ([A-Z_]+)(.*)$"
    parsed = mod.parse_cert_subject("CERT CRIT sr-pve3 CT110 CT_DOWN", [spec])
    assert parsed["level"] == "CRIT"
    assert parsed["host_name"] == "sr-pve3"
    assert parsed["ct_id"] == "110"
    assert parsed["event"] == "CT_DOWN"


def test_parse_ignores_broken_custom_pattern() -> None:
    parsed = mod.parse_cert_subject("CERT CRIT sr-pve2 CT101 NOT_RSA", ["(unclosed"])
    assert parsed is not None and parsed["event"] == "NOT_RSA"


def _save(db_path, subject, body="", when="2026-10-20 10:00:00"):
    event = mod.parse_cert_subject(subject)
    return mod.save_event(
        event, subject, body, datetime.strptime(when, "%Y-%m-%d %H:%M:%S"), db_path=db_path
    )


def test_save_is_idempotent_for_same_email(db_path) -> None:
    assert _save(db_path, "CERT CRIT sr-pve2 CT101 NOT_RSA") is True
    assert _save(db_path, "CERT CRIT sr-pve2 CT101 NOT_RSA") is False
    assert len(mod.get_recent_events(db_path=db_path)) == 1


def test_targets_state_uses_latest_event_and_known_until(db_path) -> None:
    _save(
        db_path,
        "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89",
        when="2026-10-20 10:00:00",
    )
    _save(db_path, "CERT WARN sr-pve2 CT101 EXPIRING days=13", when="2027-01-09 06:00:00")

    targets = mod.get_targets_state(db_path=db_path, today=date(2027, 1, 9))
    assert len(targets) == 1
    target = targets[0]
    assert target["last"]["event"] == "EXPIRING"
    assert target["known_until"] == "2027-01-22"
    assert target["known_days_left"] == 13
    assert target["has_problem"] is True


def test_deployed_is_ok_until_close_to_expiry(db_path) -> None:
    _save(db_path, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89")

    fresh = mod.get_targets_state(db_path=db_path, today=date(2026, 10, 25))[0]
    assert fresh["has_problem"] is False

    # Скрипт замолчал: EXPIRING не пришёл, а срок уже близко.
    stale = mod.get_targets_state(db_path=db_path, today=date(2027, 1, 18))[0]
    assert stale["stale_until"] is True
    assert stale["has_problem"] is True


def test_status_lines(db_path) -> None:
    assert "Писем CERT ещё не было" in "\n".join(mod.build_status_lines([], []))

    _save(db_path, "CERT CRIT sr-pve2 CT101 DEPLOY_FAILED rc=1", body="zmcertmgr: error")
    targets = mod.get_targets_state(db_path=db_path)
    text = "\n".join(mod.build_status_lines(targets, mod.get_recent_events(db_path=db_path)))
    assert "Почтовых серверов в норме: 0/1" in text
    assert "sr-pve2 CT101 — DEPLOY_FAILED" in text
    assert "rc=1" in text
    assert "Zimbra отдаёт старый сертификат" in text


def test_alert_message_contains_log_for_problems() -> None:
    event = mod.parse_cert_subject("CERT CRIT sr-pve2 CT101 DEPLOY_FAILED rc=1")
    event["details"] = "line1\nzmcertmgr failed"
    text = mod.build_alert_message(event)
    assert "DEPLOY_FAILED" in text
    assert "sr-pve2 CT101" in text
    assert "rc=1" in text
    assert "zmcertmgr failed" in text

    ok = mod.parse_cert_subject("CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89")
    ok_text = mod.build_alert_message(ok)
    assert "обновлён" in ok_text
    assert "2027-01-22" in ok_text


def test_alerts_sent_once_with_level_mapping(db_path) -> None:
    now = datetime(2026, 10, 24, 12, 0, 0)
    _save(
        db_path,
        "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89",
        when="2026-10-24 09:00:00",
    )
    _save(db_path, "CERT CRIT sr-pve2 CT101 KEY_MISMATCH", when="2026-10-24 10:00:00")
    # processed_at = время сохранения; подгоняем под «сейчас» теста.
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE mail_cert_events SET processed_at = '2026-10-24 11:59:00'")
    conn.commit()
    conn.close()

    calls: list[tuple[str, str]] = []

    def send(message, alert_type="info"):
        calls.append((message, alert_type))
        return True

    assert mod.check_mail_cert_alerts(send, db_path=db_path, now=now) == 2
    assert [c[1] for c in calls] == ["info", "critical"]
    assert "KEY_MISMATCH" in calls[1][0]

    calls.clear()
    assert mod.check_mail_cert_alerts(send, db_path=db_path, now=now) == 0
    assert calls == []


def test_alerts_wait_for_silent_time_to_end(db_path) -> None:
    now = datetime.now()
    _save(db_path, "CERT CRIT sr-pve2 CT101 CT_DOWN", when=now.strftime("%Y-%m-%d %H:%M:%S"))
    calls: list[str] = []

    def send(message, alert_type="info"):
        calls.append(message)
        return True

    assert mod.check_mail_cert_alerts(send, is_silent_func=lambda: True, db_path=db_path) == 0
    assert calls == []
    assert mod.check_mail_cert_alerts(send, is_silent_func=lambda: False, db_path=db_path) == 1
    assert "CT_DOWN" in calls[0]


def test_old_pending_events_are_not_sent(db_path) -> None:
    _save(db_path, "CERT CRIT sr-pve2 CT101 SAN_MISMATCH")
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE mail_cert_events SET processed_at = '2026-01-01 00:00:00'")
    conn.commit()
    conn.close()

    calls: list[str] = []
    sent = mod.check_mail_cert_alerts(
        lambda m, alert_type="info": calls.append(m), db_path=db_path, now=datetime(2026, 10, 24)
    )
    assert sent == 0 and calls == []
    assert mod.get_recent_events(db_path=db_path)[0]["notified"] == 1


def test_stale_until_alert_repeats_daily(db_path) -> None:
    _save(db_path, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89")
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE mail_cert_events SET notified = 1")
    conn.commit()
    conn.close()

    calls: list[tuple[str, str]] = []

    def send(message, alert_type="info"):
        calls.append((message, alert_type))

    first = datetime(2027, 1, 18, 9, 0, 0)
    assert mod.check_mail_cert_alerts(send, db_path=db_path, now=first) == 1
    assert calls[0][1] == "warning"
    assert "писем нет" in calls[0][0]
    assert mod.check_mail_cert_alerts(send, db_path=db_path, now=first.replace(hour=15)) == 0
    assert mod.check_mail_cert_alerts(send, db_path=db_path, now=datetime(2027, 1, 19, 9, 1)) == 1


def test_disabled_extension_sends_nothing(db_path, monkeypatch) -> None:
    monkeypatch.setattr(mod.extension_manager, "is_extension_enabled", lambda ext_id: False)
    _save(db_path, "CERT CRIT sr-pve2 CT101 CT_DOWN")
    assert mod.check_mail_cert_alerts(lambda *a, **k: None, db_path=db_path) == 0


def test_processor_routes_cert_email(tmp_path, monkeypatch) -> None:
    """Письмо CERT в Maildir попадает в mail_cert_events и не уходит в другие парсеры."""
    from modules.mail_parts.processor import BackupProcessor

    processor = BackupProcessor()
    monkeypatch.setattr(processor, "db_path", str(tmp_path / "proc.db"))
    processor.init_database()

    eml = tmp_path / "msg.eml"
    eml.write_bytes(
        b"From: root@sr-pve2\r\n"
        b"Subject: CERT CRIT sr-pve2 CT101 DEPLOY_FAILED rc=1\r\n"
        b"Date: Sat, 24 Oct 2026 10:00:00 +0300\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        b"zmcertmgr deploycrt: ERROR\r\n"
    )
    import modules.mail_parts.parsers.mail_cert as mixin_mod

    monkeypatch.setattr(mixin_mod.extension_manager, "is_extension_enabled", lambda ext_id: True)
    result = processor.parse_email_file(eml)
    assert result is not None and "mail_cert" in result

    events = mod.get_recent_events(db_path=str(tmp_path / "proc.db"))
    assert len(events) == 1
    assert events[0]["event"] == "DEPLOY_FAILED"
    assert "zmcertmgr deploycrt: ERROR" in events[0]["details"]


def test_extension_is_registered_everywhere() -> None:
    import lib.matrix_commands as m
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    from lib.report_settings import REPORT_CAPABLE_EXTENSIONS

    assert mod.EXTENSION_ID in AVAILABLE_EXTENSIONS
    assert mod.EXTENSION_ID in REPORT_CAPABLE_EXTENSIONS
    assert m._EXT_ITEM_BY_COMMAND.get("!mailcert") is not None
    assert hasattr(m.MatrixCommandBot, "_handle_ext_mail_cert")
