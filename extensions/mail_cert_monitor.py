"""
/extensions/mail_cert_monitor.py
Server Monitoring System v8.66.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mail server (Zimbra) TLS certificate deployment monitor driven by CERT emails.
Система мониторинга серверов
Версия: 8.66.0
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг сертификата почтового сервера (Zimbra) по письмам скрипта
развёртывания: тема `CERT <OK|WARN|CRIT> <host> CT<id> <EVENT> [key=value…]`.

Скрипт молчит, пока всё в порядке, поэтому каждое письмо — событие:
парсер (`modules/mail_parts/parsers/mail_cert.py`) пишет его в таблицу
`mail_cert_events`, а основной цикл мониторинга (`check_mail_cert_alerts`)
рассылает по нему оповещение ровно один раз.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any

from extensions.extension_manager import extension_manager
from lib.logging import debug_log

EXTENSION_ID = "mail_cert_monitor"

# Категория backup_patterns / BACKUP_PATTERNS для паттернов темы письма.
PATTERN_CATEGORY = "mail_cert"

# Эталонный паттерн темы. Именованные группы обязательны для пользовательских
# паттернов; для паттерна «как в ТЗ» без имён группы берутся по позициям
# (level, host, ct, event, params) — см. `parse_cert_subject`.
CERT_SUBJECT_PATTERN = (
    r"^CERT (?P<level>OK|WARN|CRIT) (?P<host>\S+) CT(?P<ct>\d+) "
    r"(?P<event>[A-Z_]+)(?P<params>.*)$"
)

LEVELS = ("OK", "WARN", "CRIT")
LEVEL_ICONS = {"OK": "✅", "WARN": "⚠️", "CRIT": "🚨"}
LEVEL_ALERT_TYPES = {"OK": "info", "WARN": "warning", "CRIT": "critical"}

# Описания событий скрипта развёртывания (sr-web-fe → Zimbra в CT).
EVENT_DESCRIPTIONS: dict[str, str] = {
    "DEPLOYED": "новый сертификат установлен и проверен",
    "EXPIRING": "до конца срока меньше 14 дней, а certbot на sr-web-fe не продлил",
    "DEPLOY_FAILED": "развёртывание не прошло, Zimbra отдаёт старый сертификат",
    "SRC_MISSING": "на sr-web-fe нет файлов сертификата",
    "SRC_EXPIRED": "на sr-web-fe лежит просроченный сертификат",
    "SAN_MISMATCH": "в сертификате нет mail.202020.ru",
    "KEY_MISMATCH": "ключ не соответствует сертификату",
    "NOT_RSA": "certbot выдал ECDSA, нужен --key-type rsa",
    "CT_DOWN": "контейнер (CT 110 или CT 101) не запущен",
}

# Оповещения рассылаются только по свежим событиям: если расширение долго
# было выключено или основной цикл не работал, старый хвост не всплывает.
NOTIFY_MAX_AGE_HOURS = 48

# Подстраховка на случай, если сломался сам скрипт: срок из последнего
# DEPLOYED (until=…) известен, и если до него осталось ≤ N дней, а писем
# больше не было (EXPIRING не пришёл), поднимаем тревогу сами.
STALE_UNTIL_ALERT_DAYS = 7
STALE_ALERT_REPEAT_SECONDS = 24 * 3600

# Сколько текста из тела письма (лог развёртывания) хранить и показывать.
DETAILS_MAX_CHARS = 4000
ALERT_DETAILS_MAX_CHARS = 1500

_STALE_ALERT_SENT_AT: dict[str, datetime] = {}

_SELECT_COLUMNS = (
    "id, host_name, ct_id, level, event, params, until_date, days_left, "
    "details, email_subject, received_at, processed_at, notified"
)


# ---------------------------------------------------------------------------
# Разбор темы письма
# ---------------------------------------------------------------------------
def parse_params(raw: str) -> dict[str, str]:
    """Разбирает хвост темы `key=value key2=value2` в словарь.

    Токены без `=` складываются в ключ `extra` через пробел.
    """
    params: dict[str, str] = {}
    extra: list[str] = []
    for token in (raw or "").split():
        if "=" in token:
            key, value = token.split("=", 1)
            key = key.strip().lower()
            if key:
                params[key] = value.strip()
                continue
        extra.append(token)
    if extra:
        params["extra"] = " ".join(extra)
    return params


def _parse_int(value: Any) -> int | None:
    match = re.search(r"-?\d+", str(value or ""))
    return int(match.group(0)) if match else None


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    for fmt, size in (("%Y-%m-%d", 10), ("%d.%m.%Y", 10)):
        try:
            return datetime.strptime(text[:size], fmt).date()
        except ValueError:
            continue
    return None


def parse_cert_subject(subject: str, patterns: list[str] | None = None) -> dict[str, Any] | None:
    """Разбирает тему письма CERT. Возвращает None, если тема не наша.

    `patterns` — пользовательские паттерны (из backup_patterns); эталонный
    `CERT_SUBJECT_PATTERN` проверяется всегда последним.
    """
    normalized = " ".join((subject or "").split())
    if not normalized:
        return None

    candidates = [p for p in (patterns or []) if p] + [CERT_SUBJECT_PATTERN]
    match = None
    for pattern in candidates:
        try:
            match = re.search(pattern, normalized)
        except re.error as exc:
            debug_log(f"⚠️ Некорректный паттерн CERT '{pattern}': {exc}")
            continue
        if match:
            break
    if not match:
        return None

    named = match.groupdict()
    if named.get("level") is not None:
        level = named.get("level") or ""
        host = named.get("host") or ""
        ct_id = named.get("ct") or ""
        event = named.get("event") or ""
        raw_params = named.get("params") or ""
    else:
        groups = list(match.groups()) + [""] * 5
        level, host, ct_id, event, raw_params = (str(g or "") for g in groups[:5])

    level = level.strip().upper()
    host = host.strip()
    ct_id = re.sub(r"\D", "", ct_id)
    event = event.strip().upper()
    if level not in LEVELS or not host or not ct_id or not event:
        return None

    params = parse_params(raw_params)
    until = _parse_date(params.get("until"))
    days_left = _parse_int(params.get("days"))
    return {
        "level": level,
        "host_name": host,
        "ct_id": ct_id,
        "event": event,
        "params": params,
        "until_date": until.isoformat() if until else None,
        "days_left": days_left,
    }


def describe_event(event: str) -> str:
    return EVENT_DESCRIPTIONS.get((event or "").upper(), "событие скрипта развёртывания")


def format_params(params: dict[str, Any], skip: tuple[str, ...] = ()) -> str:
    return " ".join(f"{k}={v}" for k, v in params.items() if k not in skip and k != "extra")


# ---------------------------------------------------------------------------
# Хранилище (таблица mail_cert_events в backups.db)
# ---------------------------------------------------------------------------
def _db_path() -> str:
    from config.db_settings import BACKUP_DATABASE_CONFIG

    return str(BACKUP_DATABASE_CONFIG["backups_db"])


def save_event(
    event: dict[str, Any],
    subject: str,
    body: str = "",
    email_date: datetime | None = None,
    db_path: str | None = None,
) -> bool:
    """Сохраняет событие. Возвращает True, если это новое письмо."""
    import json

    now = datetime.now()
    received_at = (email_date or now).strftime("%Y-%m-%d %H:%M:%S")
    details = (body or "").strip()[:DETAILS_MAX_CHARS] or None
    conn = sqlite3.connect(db_path or _db_path())
    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO mail_cert_events
            (host_name, ct_id, level, event, params, until_date, days_left,
             details, email_subject, received_at, processed_at, notified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                event["host_name"],
                event["ct_id"],
                event["level"],
                event["event"],
                json.dumps(event.get("params") or {}, ensure_ascii=False),
                event.get("until_date"),
                event.get("days_left"),
                details,
                (subject or "")[:500],
                received_at,
                now.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def _row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    import json

    keys = [c.strip() for c in _SELECT_COLUMNS.split(",")]
    item = dict(zip(keys, row, strict=False))
    try:
        item["params"] = json.loads(item.get("params") or "{}")
    except (TypeError, ValueError):
        item["params"] = {}
    return item


def _query(
    sql: str, args: tuple[Any, ...] = (), db_path: str | None = None
) -> list[dict[str, Any]]:
    try:
        conn = sqlite3.connect(db_path or _db_path())
    except Exception as exc:  # noqa: BLE001
        debug_log(f"⚠️ mail_cert: не удалось открыть БД: {exc}")
        return []
    try:
        return [_row_to_dict(tuple(r)) for r in conn.execute(sql, args).fetchall()]
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc):
            debug_log(f"⚠️ mail_cert: ошибка чтения: {exc}")
        return []
    finally:
        conn.close()


def get_recent_events(limit: int = 10, db_path: str | None = None) -> list[dict[str, Any]]:
    return _query(
        f"SELECT {_SELECT_COLUMNS} FROM mail_cert_events "
        "ORDER BY datetime(received_at) DESC, id DESC LIMIT ?",
        (int(limit),),
        db_path,
    )


def get_targets_state(
    db_path: str | None = None, today: date | None = None
) -> list[dict[str, Any]]:
    """Текущее состояние по каждой паре (хост, CT): последнее событие + срок.

    Срок (`known_until`) берётся из последнего события с `until=…` (обычно
    DEPLOYED); `known_days_left` пересчитывается от сегодняшней даты, чтобы
    видеть приближение конца срока, даже если писем давно не было.
    """
    today = today or date.today()
    events = _query(
        f"SELECT {_SELECT_COLUMNS} FROM mail_cert_events "
        "ORDER BY datetime(received_at) ASC, id ASC",
        (),
        db_path,
    )
    targets: dict[tuple[str, str], dict[str, Any]] = {}
    for ev in events:
        key = (str(ev["host_name"]), str(ev["ct_id"]))
        target = targets.setdefault(key, {"host_name": key[0], "ct_id": key[1]})
        target["last"] = ev
        if ev.get("until_date"):
            target["known_until"] = ev["until_date"]

    result: list[dict[str, Any]] = []
    for target in targets.values():
        last = target["last"]
        until = _parse_date(target.get("known_until"))
        known_days = (until - today).days if until else None
        target["known_days_left"] = known_days
        stale = (
            last.get("level") == "OK"
            and known_days is not None
            and known_days <= STALE_UNTIL_ALERT_DAYS
        )
        target["stale_until"] = stale
        target["has_problem"] = last.get("level") != "OK" or stale
        result.append(target)
    result.sort(key=lambda t: (t["host_name"], int(t["ct_id"]) if t["ct_id"].isdigit() else 0))
    return result


# ---------------------------------------------------------------------------
# Представление (Telegram / Matrix / web / Android)
# ---------------------------------------------------------------------------
def _short_dt(value: Any) -> str:
    text = str(value or "")
    return text[:16] if len(text) >= 16 else text


def build_status_lines(
    targets: list[dict[str, Any]] | None = None,
    recent: list[dict[str, Any]] | None = None,
    recent_limit: int = 5,
) -> list[str]:
    """Текстовый статус расширения (общий для всех клиентов).

    Первая строка — сводка `Почтовых серверов: ok/всего` (по ней Android
    строит плашку).
    """
    if targets is None:
        targets = get_targets_state()
    if recent is None:
        recent = get_recent_events(limit=recent_limit)

    lines = ["📨 Сертификат почтового сервера (Zimbra)"]
    if not targets:
        lines.append("")
        lines.append("⚪ Писем CERT ещё не было.")
        lines.append(
            "Скрипт молчит, пока всё в порядке: письмо приходит только при "
            "замене сертификата или проблеме."
        )
        return lines

    ok_count = sum(1 for t in targets if not t["has_problem"])
    lines.append(f"Почтовых серверов в норме: {ok_count}/{len(targets)}")
    lines.append("")
    for t in targets:
        last = t["last"]
        level = str(last.get("level") or "")
        icon = "⚠️" if t["stale_until"] else LEVEL_ICONS.get(level, "❔")
        lines.append(f"{icon} {t['host_name']} CT{t['ct_id']} — {last.get('event')}")
        lines.append(f"   {describe_event(str(last.get('event')))}")
        extra = format_params(last.get("params") or {}, skip=("until", "days"))
        if extra:
            lines.append(f"   {extra}")
        if t.get("known_until"):
            days = t.get("known_days_left")
            lines.append(f"   Действует до: {t['known_until']} (осталось {days} дн.)")
        if t["stale_until"]:
            lines.append(
                "   ❗ Срок подходит к концу, а писем от скрипта нет — "
                "проверьте certbot и скрипт развёртывания."
            )
        lines.append(f"   Письмо: {_short_dt(last.get('received_at'))}")

    if recent:
        lines.append("")
        lines.append("🕘 Последние события:")
        for ev in recent[:recent_limit]:
            icon = LEVEL_ICONS.get(str(ev.get("level")), "❔")
            lines.append(
                f"{icon} {_short_dt(ev.get('received_at'))} · {ev.get('host_name')} "
                f"CT{ev.get('ct_id')} · {ev.get('event')}"
            )
    return lines


def get_summary(targets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Короткая сводка для утреннего отчёта."""
    if targets is None:
        targets = get_targets_state()
    total = len(targets)
    ok_count = sum(1 for t in targets if not t["has_problem"])
    days = [t["known_days_left"] for t in targets if isinstance(t.get("known_days_left"), int)]
    return {
        "total": total,
        "ok": ok_count,
        "min_days_left": min(days) if days else None,
        "problems": [t for t in targets if t["has_problem"]],
    }


def build_alert_message(event: dict[str, Any]) -> str:
    """Текст оповещения по одному событию."""
    level = str(event.get("level") or "")
    name = str(event.get("event") or "")
    target = f"{event.get('host_name')} CT{event.get('ct_id')}"
    params = event.get("params") or {}

    # Иконку уровня (🚨/⚠️/ℹ️) добавляет сам send_alert по alert_type.
    if level == "OK" and name == "DEPLOYED":
        lines = [f"📨 Сертификат почты обновлён: {target}"]
    else:
        title = {"WARN": "Сертификат почты: внимание", "CRIT": "Сертификат почты: ошибка"}.get(
            level, "Сертификат почты"
        )
        lines = [f"📨 {title} — {name}", f"• Сервер: {target}"]
    lines.append(f"• {describe_event(name)}")

    if event.get("until_date"):
        lines.append(f"• Действует до: {event['until_date']}")
    if event.get("days_left") is not None:
        lines.append(f"• Осталось: {event['days_left']} дн.")
    extra = format_params(params, skip=("until", "days"))
    if extra:
        lines.append(f"• Параметры: {extra}")
    if params.get("extra"):
        lines.append(f"• {params['extra']}")

    details = str(event.get("details") or "").strip()
    if details and level != "OK":
        if len(details) > ALERT_DETAILS_MAX_CHARS:
            details = "…" + details[-ALERT_DETAILS_MAX_CHARS:]
        lines.append("")
        lines.append("Лог:")
        lines.append(details)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Оповещения (вызывается из основного цикла мониторинга)
# ---------------------------------------------------------------------------
def check_mail_cert_alerts(
    send_alert_func: Callable[..., Any],
    is_silent_func: Callable[[], bool] | None = None,
    db_path: str | None = None,
    now: datetime | None = None,
) -> int:
    """Рассылает оповещения по новым письмам CERT. Возвращает число отправленных.

    `send_alert_func(message, alert_type=...)` — обычно
    `partial(send_alert, category="mail_cert_monitor")`.
    `is_silent_func()` — тихий режим: send_alert в нём глушит любые
    оповещения, поэтому события не тратятся, а ждут его окончания.
    """
    if not extension_manager.is_extension_enabled(EXTENSION_ID):
        return 0
    try:
        if is_silent_func is not None and is_silent_func():
            return 0
    except Exception as exc:  # noqa: BLE001
        debug_log(f"⚠️ mail_cert: не удалось проверить тихий режим: {exc}")

    now = now or datetime.now()
    path = db_path or _db_path()
    pending = _query(
        f"SELECT {_SELECT_COLUMNS} FROM mail_cert_events WHERE notified = 0 ORDER BY id ASC",
        (),
        path,
    )
    sent = 0
    threshold = (now - timedelta(hours=NOTIFY_MAX_AGE_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
    for ev in pending:
        if str(ev.get("processed_at") or "") >= threshold:
            try:
                send_alert_func(
                    build_alert_message(ev),
                    alert_type=LEVEL_ALERT_TYPES.get(str(ev.get("level")), "info"),
                )
                sent += 1
            except Exception as exc:  # noqa: BLE001
                debug_log(f"⚠️ mail_cert: не удалось отправить оповещение: {exc}")
                continue
        _mark_notified(int(ev["id"]), path)

    for target in get_targets_state(db_path=path, today=now.date()):
        key = f"{target['host_name']}:{target['ct_id']}:{target.get('known_until')}"
        if not target["stale_until"]:
            _STALE_ALERT_SENT_AT.pop(key, None)
            continue
        last_sent = _STALE_ALERT_SENT_AT.get(key)
        if last_sent and (now - last_sent).total_seconds() < STALE_ALERT_REPEAT_SECONDS:
            continue
        try:
            send_alert_func(
                "⚠️ Сертификат почты: срок подходит к концу, а писем нет\n"
                f"• Сервер: {target['host_name']} CT{target['ct_id']}\n"
                f"• Действует до: {target.get('known_until')} "
                f"(осталось {target.get('known_days_left')} дн.)\n"
                "• Скрипт должен был прислать EXPIRING или DEPLOYED — "
                "проверьте certbot на sr-web-fe и скрипт развёртывания.",
                alert_type="warning",
            )
        except Exception as exc:  # noqa: BLE001
            debug_log(f"⚠️ mail_cert: не удалось отправить оповещение о сроке: {exc}")
            continue
        _STALE_ALERT_SENT_AT[key] = now
        sent += 1
    return sent


def _mark_notified(event_id: int, db_path: str) -> None:
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("UPDATE mail_cert_events SET notified = 1 WHERE id = ?", (event_id,))
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        debug_log(f"⚠️ mail_cert: не удалось отметить событие {event_id}: {exc}")


__all__ = [
    "CERT_SUBJECT_PATTERN",
    "EVENT_DESCRIPTIONS",
    "EXTENSION_ID",
    "build_alert_message",
    "build_status_lines",
    "check_mail_cert_alerts",
    "describe_event",
    "get_recent_events",
    "get_summary",
    "get_targets_state",
    "parse_cert_subject",
    "parse_params",
    "save_event",
]
