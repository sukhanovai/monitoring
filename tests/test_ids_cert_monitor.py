"""
Тесты расширения ids_cert_monitor: разбор писем IDS/CERT, автомат состояний,
сторожевые проверки, напоминания и рассылка очереди (сценарии из ТЗ, п. 7).
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta
from email.utils import format_datetime

import pytest

import extensions.ids_cert_monitor as mod

NAMES = {"101": "почтовый сервер Zimbra"}
T0 = datetime(2026, 10, 24, 5, 0, 0)

INTRUSION_BODY = """level=CRIT
node=sr-pve2
ct=101
event=INTRUSION
time=2026-10-24 05:50:25


EXEC_FROM_TMP pid=4242 /tmp/.x/kworker
EXEC_IN_TMP /tmp/.x/kworker
FAKE_KTHREAD pid=4242 [kworker/0:1]
"""


@pytest.fixture()
def db(tmp_path) -> str:
    return str(tmp_path / "backups.db")


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(mod.extension_manager, "is_extension_enabled", lambda ext_id: True)
    monkeypatch.setattr(mod, "get_ct_names", lambda: dict(NAMES))
    monkeypatch.setattr(mod, "get_expected_sources", lambda: ["sr-pve2/CT101"])
    monkeypatch.setattr(mod, "_STARTED_AT", None)
    monkeypatch.setattr(mod, "_LAST_WATCHDOG_AT", None)


def mail(db, subject, when, body="", msgid=None, now=None):
    return mod.handle_email(
        subject,
        body,
        message_id=msgid or f"<{uuid.uuid4()}@sr-pve2>",
        date_header=format_datetime(when.astimezone()),
        db_path=db,
        now=now or when,
        ct_names=NAMES,
    )


def state(db, key):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM ids_state WHERE problem_key = ?", (key,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def pending(db):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM ids_outbox WHERE status = 'pending' ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def drain(db):
    conn = sqlite3.connect(db)
    conn.execute("UPDATE ids_outbox SET status = 'sent'")
    conn.commit()
    conn.close()


KEY_INTRUSION = "IDS/sr-pve2/CT101/intrusion"
KEY_CONFIG = "IDS/sr-pve2/CT101/config"
KEY_AVAIL = "IDS/sr-pve2/CT101/availability"
KEY_WATCHDOG = "IDS/sr-pve2/CT101/watchdog"
KEY_CERT = "CERT/sr-pve2/CT101/cert"
KEY_CERT_WD = "CERT/sr-pve2/CT101/cert_watchdog"


# ---- разбор ---------------------------------------------------------------


def test_parse_subject_and_fields() -> None:
    parsed = mod.parse_subject(
        "IDS CRIT sr-pve2 CT101 INTRUSION n=3 types=EXEC_IN_TMP,FAKE_KTHREAD"
    )
    assert parsed == {
        "source": "IDS",
        "level": "CRIT",
        "node": "sr-pve2",
        "ct": "101",
        "event": "INTRUSION",
        "fields": {"n": "3", "types": "EXEC_IN_TMP,FAKE_KTHREAD"},
    }
    assert mod.parse_subject("CERT CRIT sr-pve2 CT101 SRC_EXPIRED")["fields"] == {}
    assert mod.parse_subject("IDS BROKEN subject") is None
    assert mod.is_ids_cert_subject("IDS BROKEN subject")
    assert not mod.is_ids_cert_subject("Config backup pve3 OK")
    assert not mod.is_ids_cert_subject("IDSX CRIT sr-pve2 CT101 DOWN")


def test_parse_body_splits_meta_and_details() -> None:
    meta, details = mod.parse_body(INTRUSION_BODY)
    assert meta["event"] == "INTRUSION"
    assert meta["time"] == "2026-10-24 05:50:25"
    assert details.splitlines()[0].startswith("EXEC_FROM_TMP")


def test_event_time_priority() -> None:
    received = datetime(2026, 10, 24, 9, 0, 0)
    meta = {"time": "2026-10-24 05:50:25"}
    header = format_datetime(datetime(2026, 10, 24, 5, 55).astimezone())
    assert mod.resolve_event_time(header, meta, received) == datetime(2026, 10, 24, 5, 55)
    assert mod.resolve_event_time("garbage", meta, received) == datetime(2026, 10, 24, 5, 50, 25)
    assert mod.resolve_event_time(None, {}, received) == received


def test_details_limits_and_config_priority() -> None:
    long = "\n".join(f"line {i}" for i in range(100))
    assert len(mod.prepare_details("INTRUSION", long).splitlines()) == 25
    assert len(mod.prepare_details("INTRUSION", "x" * 5000)) <= 3000
    details = "+ ACCT new@x\n- ALIAS old@x\n+ FWD boss@x -> evil@ext\n+ ADMIN root@x"
    ordered = mod.prepare_details("ZIMBRA_CONFIG", details).splitlines()
    assert ordered[:2] == ["+ FWD boss@x -> evil@ext", "+ ADMIN root@x"]


# ---- сценарии ТЗ, п. 7 ------------------------------------------------------


def test_spec_sequence(db) -> None:
    # 1. HEARTBEAT — сигнал жизни обновлён, оповещений нет.
    r = mail(db, "IDS OK sr-pve2 CT101 HEARTBEAT findings=0 zimbra=0 lastrun=3m", T0)
    assert r["outcome"] == "processed"
    assert pending(db) == []

    # 2. INTRUSION CRIT — OK→CRIT, 🔴 с тремя расшифровками.
    t2 = T0 + timedelta(minutes=50)
    msgid = "<intrusion-1@sr-pve2>"
    mail(
        db,
        "IDS CRIT sr-pve2 CT101 INTRUSION n=3 types=EXEC_FROM_TMP,EXEC_IN_TMP,FAKE_KTHREAD",
        t2,
        INTRUSION_BODY,
        msgid=msgid,
    )
    assert state(db, KEY_INTRUSION)["state"] == "CRIT"
    [alert] = pending(db)
    assert alert["level"] == "CRIT"
    text = alert["message"]
    assert text.startswith("🔴 CRIT  sr-pve2 / CT101 (почтовый сервер Zimbra)")
    assert "Вторжение: 3 находки" in text
    assert "• Процесс маскируется под поток ядра" in text
    assert "• Процесс запущен из временного каталога" in text
    assert "• Исполняемый файл во временном каталоге" in text
    assert "ip link set veth101i0 down" in text
    assert "EXEC_FROM_TMP pid=4242" in text
    drain(db)

    # 3. Тот же Message-ID — игнор.
    r = mail(
        db,
        "IDS CRIT sr-pve2 CT101 INTRUSION n=3 types=EXEC_FROM_TMP,EXEC_IN_TMP,FAKE_KTHREAD",
        t2,
        INTRUSION_BODY,
        msgid=msgid,
    )
    assert r["outcome"] == "duplicate"
    assert pending(db) == []

    # 4. WARN после CRIT — остаётся CRIT, детали обновлены, «обновление».
    t4 = t2 + timedelta(minutes=10)
    mail(
        db,
        "IDS WARN sr-pve2 CT101 INTRUSION n=1 types=FILE_CHANGED",
        t4,
        "FILE_CHANGED /etc/passwd",
    )
    st = state(db, KEY_INTRUSION)
    assert st["state"] == "CRIT"
    assert st["last_details"] == "FILE_CHANGED /etc/passwd"
    [alert] = pending(db)
    assert "обновление" in alert["message"].splitlines()[0]
    drain(db)

    # 17. RESOLVED с Date раньше, чем у п.4 — состояние не меняется.
    r = mail(
        db,
        "IDS OK sr-pve2 CT101 RESOLVED",
        t4 - timedelta(minutes=5),
        now=t4 + timedelta(minutes=1),
    )
    assert "out-of-order" in r["log"]
    assert state(db, KEY_INTRUSION)["state"] == "CRIT"
    assert pending(db) == []

    # 5. RESOLVED — CRIT→OK, 🟢 с длительностью.
    t5 = t2 + timedelta(hours=1, minutes=12)
    mail(db, "IDS OK sr-pve2 CT101 RESOLVED", t5)
    assert state(db, KEY_INTRUSION)["state"] == "OK"
    [alert] = pending(db)
    assert alert["message"].startswith("🟢 OK  sr-pve2 / CT101 (почтовый сервер Zimbra)")
    assert "Вторжение: находки исчезли. Длительность: 1 ч 12 мин" in alert["message"]
    drain(db)

    # 6–7. ZIMBRA_CONFIG — config OK→CRIT, затем →OK.
    t6 = t5 + timedelta(minutes=5)
    mail(db, "IDS CRIT sr-pve2 CT101 ZIMBRA_CONFIG n=1 kinds=ADMIN", t6, "+ ADMIN evil@202020.ru")
    assert state(db, KEY_CONFIG)["state"] == "CRIT"
    assert "• Администраторы" in pending(db)[0]["message"]
    assert "ip link set" not in pending(db)[0]["message"]
    drain(db)
    mail(db, "IDS OK sr-pve2 CT101 ZIMBRA_CONFIG_RESOLVED", t6 + timedelta(minutes=30))
    assert state(db, KEY_CONFIG)["state"] == "OK"
    drain(db)

    # 8–9. STALE → availability CRIT, HEARTBEAT OK закрывает.
    t8 = t6 + timedelta(hours=1)
    mail(db, "IDS CRIT sr-pve2 CT101 STALE lastrun=40m", t8)
    assert state(db, KEY_AVAIL)["state"] == "CRIT"
    mail(
        db,
        "IDS OK sr-pve2 CT101 HEARTBEAT findings=0 zimbra=0 lastrun=2m",
        t8 + timedelta(minutes=5),
    )
    assert state(db, KEY_AVAIL)["state"] == "OK"
    drain(db)

    # 10. DOWN, затем UP.
    t10 = t8 + timedelta(hours=1)
    mail(db, "IDS CRIT sr-pve2 CT101 DOWN", t10)
    assert state(db, KEY_AVAIL)["state"] == "CRIT"
    mail(db, "IDS OK sr-pve2 CT101 UP", t10 + timedelta(minutes=3))
    assert state(db, KEY_AVAIL)["state"] == "OK"
    drain(db)

    # 11. DEPLOYED — cert_until запомнен, без пуша.
    t11 = t10 + timedelta(hours=1)
    mail(db, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89", t11)
    assert pending(db) == []
    assert mod.get_overview(db, t11)["certs"][0]["until_date"] == "2027-01-22"

    # 12–13. DEPLOY_FAILED → cert CRIT, DEPLOYED → OK.
    mail(
        db,
        "CERT CRIT sr-pve2 CT101 DEPLOY_FAILED rc=1",
        t11 + timedelta(days=1),
        "zmcertmgr: ERROR",
    )
    assert state(db, KEY_CERT)["state"] == "CRIT"
    assert "rc=1" in pending(db)[0]["message"]
    drain(db)
    mail(db, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-03-22 days=89", t11 + timedelta(days=2))
    assert state(db, KEY_CERT)["state"] == "OK"
    assert "действует до 2027-03-22" in pending(db)[0]["message"]
    assert mod.get_overview(db, t11)["certs"][0]["until_date"] == "2027-03-22"


def test_unparsed_subject_alerts_warn(db) -> None:
    # 14. Битое письмо IDS/CERT — WARN «нераспознанное письмо».
    r = mail(db, "IDS BROKEN subject", T0)
    assert r["outcome"] == "unparsed"
    [alert] = pending(db)
    assert alert["level"] == "WARN"
    assert "Нераспознанное письмо IDS/CERT" in alert["message"]
    assert "IDS BROKEN subject" in alert["message"]


def test_foreign_subject_is_not_ours(db) -> None:
    assert mod.handle_email("NAS transfer sr-bup OK", db_path=db) is None


def test_heartbeat_watchdog(db) -> None:
    # 15. Нет HEARTBEAT 2 ч — watchdog CRIT; следующий HEARTBEAT закрывает.
    mail(db, "IDS OK sr-pve2 CT101 HEARTBEAT findings=0 zimbra=0 lastrun=3m", T0)
    conn = mod._connect(db)
    try:
        mod.run_watchdogs(conn, T0 + timedelta(hours=1), T0, NAMES, [])
        assert state(db, KEY_WATCHDOG) is None
        mod.run_watchdogs(conn, T0 + timedelta(hours=2, minutes=5), T0, NAMES, [])
        conn.commit()
    finally:
        conn.close()
    assert state(db, KEY_WATCHDOG)["state"] == "CRIT"
    [alert] = pending(db)
    assert "Нет сигнала жизни от IDS 2 часа" in alert["message"]
    drain(db)

    # Повторная проверка с теми же данными не дублирует оповещение.
    conn = mod._connect(db)
    try:
        mod.run_watchdogs(conn, T0 + timedelta(hours=2, minutes=10), T0, NAMES, [])
        conn.commit()
    finally:
        conn.close()
    assert pending(db) == []

    mail(
        db, "IDS OK sr-pve2 CT101 HEARTBEAT findings=0 zimbra=0 lastrun=1m", T0 + timedelta(hours=3)
    )
    assert state(db, KEY_WATCHDOG)["state"] == "OK"
    assert pending(db)[0]["message"].startswith("🟢 OK")


def test_expected_source_without_heartbeat(db) -> None:
    conn = mod._connect(db)
    try:
        mod.run_watchdogs(conn, T0 + timedelta(hours=1), T0, NAMES, ["sr-pve2/CT101"])
        assert state(db, KEY_WATCHDOG) is None
        mod.run_watchdogs(conn, T0 + timedelta(hours=2), T0, NAMES, ["sr-pve2/CT101"])
        conn.commit()
    finally:
        conn.close()
    assert state(db, KEY_WATCHDOG)["state"] == "CRIT"
    assert "ни разу не приходил" in pending(db)[0]["message"]


def test_cert_watchdog(db) -> None:
    # 16. До конца срока < 10 дней — cert_watchdog CRIT; новый DEPLOYED закрывает.
    mail(db, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89", T0)
    now = datetime(2027, 1, 13, 12, 0, 0)
    conn = mod._connect(db)
    try:
        mod.run_watchdogs(conn, now - timedelta(days=1), T0, NAMES, [])
        assert state(db, KEY_CERT_WD) is None
        mod.run_watchdogs(conn, now, T0, NAMES, [])
        conn.commit()
    finally:
        conn.close()
    assert state(db, KEY_CERT_WD)["state"] == "CRIT"
    assert "Сертификат истекает 2027-01-22 (осталось 9 дн.), автозамена не сработала" in (
        pending(db)[0]["message"]
    )
    drain(db)
    mail(db, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-04-22 days=89", now + timedelta(hours=1))
    assert state(db, KEY_CERT_WD)["state"] == "OK"


def test_heartbeat_warn_opens_intrusion_only_when_closed(db) -> None:
    mail(db, "IDS WARN sr-pve2 CT101 HEARTBEAT findings=2 zimbra=0 lastrun=3m", T0)
    st = state(db, KEY_INTRUSION)
    assert st["state"] == "WARN"
    assert "незакрытых находках" in pending(db)[0]["message"]
    drain(db)
    mail(
        db,
        "IDS WARN sr-pve2 CT101 HEARTBEAT findings=2 zimbra=0 lastrun=3m",
        T0 + timedelta(hours=1),
    )
    assert pending(db) == []


def test_escalation_warn_to_crit(db) -> None:
    mail(db, "IDS WARN sr-pve2 CT101 INTRUSION n=1 types=NEW_PORT", T0)
    drain(db)
    mail(db, "IDS CRIT sr-pve2 CT101 INTRUSION n=1 types=WEB_RCE", T0 + timedelta(minutes=5))
    assert state(db, KEY_INTRUSION)["state"] == "CRIT"
    [alert] = pending(db)
    assert alert["level"] == "CRIT" and "повышение" in alert["message"]
    assert "Веб-сервер Zimbra запустил команду" in alert["message"]


def test_reminders_and_acknowledge(db) -> None:
    mail(db, "IDS CRIT sr-pve2 CT101 INTRUSION n=1 types=UID0", T0)
    mail(db, "IDS WARN sr-pve2 CT101 MONITOR_ERROR what=ldap accounts=10/12", T0)
    drain(db)
    conn = mod._connect(db)
    try:
        assert mod.run_reminders(conn, T0 + timedelta(hours=1), NAMES) == 0
        assert mod.run_reminders(conn, T0 + timedelta(hours=2), NAMES) == 1
        conn.commit()
    finally:
        conn.close()
    [reminder] = pending(db)
    assert "напоминание" in reminder["message"]
    assert "Длится: 2 ч" in reminder["message"]
    drain(db)

    assert mod.acknowledge(KEY_INTRUSION, by="test", db_path=db) is True
    conn = mod._connect(db)
    try:
        # CRIT подтверждён — молчит; WARN напомнит через 12 ч.
        assert mod.run_reminders(conn, T0 + timedelta(hours=6), NAMES) == 0
        assert mod.run_reminders(conn, T0 + timedelta(hours=12), NAMES) == 1
        conn.commit()
    finally:
        conn.close()
    assert (
        "MONITOR_ERROR" in pending(db)[0]["message"] or "сбой проверки" in pending(db)[0]["message"]
    )
    assert mod.acknowledge(KEY_CONFIG, db_path=db) is False


def test_dispatch_crit_forced_others_wait_for_silence(db) -> None:
    mail(db, "IDS CRIT sr-pve2 CT101 DOWN", T0)
    mail(db, "IDS WARN sr-pve2 CT101 MONITOR_ERROR what=ldap", T0)
    calls: list[tuple[str, str, bool]] = []

    def send(message, alert_type="info", force=False):
        calls.append((message, alert_type, force))
        return True

    sent = mod.tick(send, is_silent_func=lambda: True, db_path=db, now=T0 + timedelta(minutes=1))
    assert sent == 1
    assert calls[0][1:] == ("critical", True)
    assert len(pending(db)) == 1

    sent = mod.tick(send, is_silent_func=lambda: False, db_path=db, now=T0 + timedelta(minutes=2))
    assert sent == 1
    assert calls[1][1:] == ("warning", False)
    assert pending(db) == []


def test_dispatch_warn_intrusion_bypasses_silence(db) -> None:
    mail(db, "IDS WARN sr-pve2 CT101 INTRUSION n=1 types=FILE_CHANGED", T0)
    mail(db, "IDS WARN sr-pve2 CT101 MONITOR_ERROR what=ldap", T0)
    calls: list[tuple[str, str, bool]] = []

    def send(message, alert_type="info", force=False):
        calls.append((message, alert_type, force))
        return True

    sent = mod.tick(send, is_silent_func=lambda: True, db_path=db, now=T0 + timedelta(minutes=1))
    assert sent == 1
    assert calls[0][1:] == ("warning", True)
    assert "Вторжение" in calls[0][0]
    assert len(pending(db)) == 1  # MONITOR_ERROR ждёт конца тихих часов


def test_is_immediate_rules() -> None:
    key = "IDS/sr-pve2/CT101/intrusion"
    assert mod.is_immediate("CRIT", "reminder", "IDS/sr-pve2/CT101/monitor")
    assert mod.is_immediate("WARN", "new", key)
    assert mod.is_immediate("WARN", "update", "IDS/sr-pve2/CT101/config")
    assert not mod.is_immediate("WARN", "reminder", key)
    assert not mod.is_immediate("OK", "recovery", key)
    assert not mod.is_immediate("WARN", "new", "IDS/sr-pve2/CT101/monitor")
    assert not mod.is_immediate("WARN", "new", None)


def test_outbox_expires_old_items(db) -> None:
    mail(db, "IDS WARN sr-pve2 CT101 MONITOR_ERROR what=ldap", T0)
    calls: list[str] = []
    conn = mod._connect(db)
    try:
        sent = mod.dispatch_outbox(conn, lambda m, **k: calls.append(m), T0 + timedelta(days=3))
    finally:
        conn.close()
    assert sent == 0 and calls == [] and pending(db) == []


def test_state_survives_new_connection(db) -> None:
    mail(db, "IDS CRIT sr-pve2 CT101 INTRUSION n=1 types=UID0", T0)
    mod._SCHEMA_READY.clear()
    assert mod.get_open_problems(db)[0]["problem_key"] == KEY_INTRUSION


def test_status_lines_for_tile(db) -> None:
    assert "Писем IDS/CERT ещё не было" in "\n".join(mod.build_status_lines(db))
    mail(db, "IDS OK sr-pve2 CT101 HEARTBEAT findings=0 zimbra=0 lastrun=3m", T0)
    mail(db, "IDS CRIT sr-pve2 CT101 INTRUSION n=1 types=UID0", T0 + timedelta(minutes=1))
    mail(db, "CERT OK sr-pve2 CT101 DEPLOYED until=2027-01-22 days=89", T0 + timedelta(minutes=2))
    lines = mod.build_status_lines(db, now=T0 + timedelta(minutes=30))
    # Android-плашка разбирает вторую строку.
    assert lines[1] == "Контейнеров в норме: 0/1 · 🔴 1 · 🟡 0"
    text = "\n".join(lines)
    assert "Лишний пользователь с правами root" in text
    assert "до 2027-01-22" in text
    assert "💓 Сигнал жизни IDS" in text
    history = "\n".join(mod.build_history_lines(db_path=db))
    assert "INTRUSION · OK→CRIT" in history


def test_processor_routes_ids_email_first(tmp_path, monkeypatch) -> None:
    """Письмо IDS из Maildir обрабатывается раньше всех парсеров и попадает в журнал."""
    from modules.mail_parts.processor import BackupProcessor

    processor = BackupProcessor()
    monkeypatch.setattr(processor, "db_path", str(tmp_path / "proc.db"))
    processor.init_database()
    eml = tmp_path / "msg.eml"
    eml.write_bytes(
        b"From: root@sr-pve2\r\n"
        b"Subject: IDS CRIT sr-pve2 CT101 INTRUSION n=1 types=WEB_RCE\r\n"
        b"Message-ID: <abc@sr-pve2>\r\n"
        b"Date: Sat, 24 Oct 2026 05:50:25 +0300\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n\r\n" + INTRUSION_BODY.encode("utf-8")
    )
    result = processor.parse_email_file(eml)
    assert result["ids_cert"]["outcome"] == "processed"
    problems = mod.get_open_problems(str(tmp_path / "proc.db"))
    assert problems[0]["problem_key"] == KEY_INTRUSION


def test_processing_error_becomes_alert(tmp_path, monkeypatch) -> None:
    from modules.mail_parts.processor import BackupProcessor

    processor = BackupProcessor()
    monkeypatch.setattr(processor, "db_path", str(tmp_path / "proc.db"))
    processor.init_database()

    import modules.mail_parts.parsers.ids_cert as mixin

    def boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(mixin, "handle_email", boom)
    eml = tmp_path / "msg.eml"
    eml.write_bytes(b"Subject: IDS CRIT sr-pve2 CT101 DOWN\r\n\r\nbody\r\n")
    result = processor.parse_email_file(eml)
    assert result["ids_cert"]["outcome"] == "error"
    [alert] = pending(str(tmp_path / "proc.db"))
    assert "Ошибка обработки письма IDS/CERT" in alert["message"]


def test_extension_is_registered_everywhere() -> None:
    import lib.matrix_commands as m
    from extensions.extension_manager import AVAILABLE_EXTENSIONS
    from lib.report_settings import REPORT_CAPABLE_EXTENSIONS

    assert mod.EXTENSION_ID in AVAILABLE_EXTENSIONS
    assert mod.EXTENSION_ID in REPORT_CAPABLE_EXTENSIONS
    assert m._EXT_ITEM_BY_COMMAND.get("!ids") is not None
    assert hasattr(m.MatrixCommandBot, "_handle_ext_ids_cert")
    assert "ids_cert_monitor" in dict(m._EXTENSION_SETTINGS)
