"""
/extensions/ids_cert_monitor.py
Server Monitoring System v8.67.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
IDS (container intrusion detection) and CERT (mail TLS certificate) monitor.
Система мониторинга серверов
Версия: 8.67.1
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг взлома контейнеров Proxmox (IDS) и замены TLS-сертификата
почтового сервера (CERT) по письмам скриптов на хосте PVE.

Тема письма: `<IDS|CERT> <OK|WARN|CRIT> <узел> CT<id> <СОБЫТИЕ> [key=value…]`.
Тело: строки `key=value` до пустой строки (метаданные), дальше — детали.

Устройство:
- `handle_email` (вызывает mail-monitor) пишет письмо в журнал `ids_events`,
  прогоняет автомат состояний `ids_state` (ключ `source/node/CTct/family`) и
  кладёт оповещения в очередь `ids_outbox`;
- `tick` (вызывает основной цикл мониторинга) раз в 5 минут запускает
  сторожевые проверки (нет HEARTBEAT, истекает сертификат) и напоминания,
  а на каждом проходе рассылает очередь.
Всё состояние хранится в backups.db и переживает перезапуск.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Callable
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

from core.config_manager import config_manager
from extensions.extension_manager import extension_manager
from lib.logging import debug_log

EXTENSION_ID = "ids_cert_monitor"

SUBJECT_RE = re.compile(r"^(IDS|CERT) (OK|WARN|CRIT) (\S+) CT(\d+) ([A-Z_]+)(?: (.*))?$")

LEVEL_RANK = {"OK": 0, "WARN": 1, "CRIT": 2}
LEVEL_ICONS = {"OK": "🟢", "WARN": "🟡", "CRIT": "🔴"}
ALERT_TYPES = {"OK": "info", "WARN": "warning", "CRIT": "critical"}

TIME_FMT = "%Y-%m-%d %H:%M:%S"

# Настройки (config_manager / settings.db).
CT_NAMES_SETTING = "IDS_CT_NAMES"
EXPECTED_SOURCES_SETTING = "IDS_EXPECTED_SOURCES"
DEFAULT_CT_NAMES: dict[str, str] = {"101": "почтовый сервер Zimbra"}
DEFAULT_EXPECTED_SOURCES: list[str] = ["sr-pve2/CT101"]

# Сроки из ТЗ.
HEARTBEAT_TIMEOUT = timedelta(hours=2)
CERT_WATCHDOG_DAYS = 10
WATCHDOG_INTERVAL = timedelta(minutes=5)
REMINDER_INTERVALS = {"CRIT": timedelta(hours=2), "WARN": timedelta(hours=12)}
OUTBOX_MAX_AGE = timedelta(hours=48)
# Признаки взлома (семейства intrusion/config) — оповещаем сразу при любом
# уровне, мимо тихих часов: WARN «изменились системные файлы» в 20:10 не
# должен ждать 09:00. Напоминания по ним подчиняются тихим часам как обычно.
IMMEDIATE_FAMILIES = ("intrusion", "config")
IMMEDIATE_KINDS = ("new", "escalate", "update")
ALERT_DETAILS_MAX_LINES = 25
ALERT_DETAILS_MAX_CHARS = 3000
JOURNAL_DETAILS_MAX_CHARS = 20000

# Что делает событие с проблемой своего семейства.
OPEN = "open"
CLOSE = "close"
HEARTBEAT = "heartbeat"
DEPLOYED = "deployed"
INFO = "info"

IDS_EVENTS: dict[str, tuple[str, str]] = {
    "INTRUSION": ("intrusion", OPEN),
    "RESOLVED": ("intrusion", CLOSE),
    "ZIMBRA_CONFIG": ("config", OPEN),
    "ZIMBRA_CONFIG_RESOLVED": ("config", CLOSE),
    "DOWN": ("availability", OPEN),
    "STALE": ("availability", OPEN),
    "UP": ("availability", CLOSE),
    "MONITOR_ERROR": ("monitor", OPEN),
    "HEARTBEAT": ("heartbeat", HEARTBEAT),
    "BASELINE": ("info", INFO),
    "TEST": ("info", INFO),
}

CERT_EVENT_DESCRIPTIONS: dict[str, str] = {
    "DEPLOYED": "новый сертификат установлен и проверен",
    "EXPIRING": "до конца срока меньше 14 дней, а certbot на sr-web-fe не продлил",
    "DEPLOY_FAILED": "развёртывание не прошло, Zimbra отдаёт старый сертификат",
    "SRC_MISSING": "на sr-web-fe нет файлов сертификата",
    "SRC_EXPIRED": "на sr-web-fe лежит просроченный сертификат",
    "SAN_MISMATCH": "в сертификате нет mail.202020.ru",
    "KEY_MISMATCH": "ключ не соответствует сертификату",
    "NOT_RSA": "certbot выдал ECDSA, нужен --key-type rsa",
    "CT_DOWN": "CT 110 или CT 101 не запущен",
}

IDS_EVENT_DESCRIPTIONS: dict[str, str] = {
    "INTRUSION": "находки IDS в контейнере (n=, types=)",
    "RESOLVED": "находки исчезли",
    "ZIMBRA_CONFIG": "изменились админы/пересылки/настройки Zimbra (n=, kinds=)",
    "ZIMBRA_CONFIG_RESOLVED": "изменения конфигурации закрыты",
    "DOWN": "контейнер не работает",
    "STALE": "проверки IDS не запускаются (lastrun=)",
    "UP": "контейнер и проверки снова работают",
    "MONITOR_ERROR": "сбой самой проверки (what=, accounts=)",
    "HEARTBEAT": "сигнал жизни IDS (findings=, zimbra=, lastrun=)",
    "BASELINE": "снят эталон — только в журнал",
    "TEST": "тестовое письмо — только в журнал",
}

INTRUSION_TYPES: dict[str, str] = {
    "WEB_RCE": "Веб-сервер Zimbra запустил команду (веб-шелл / удалённое выполнение)",
    "FAKE_KTHREAD": "Процесс маскируется под поток ядра",
    "EXEC_FROM_TMP": "Процесс запущен из временного каталога",
    "DELETED_EXE": "Процесс работает из удалённого файла",
    "EXEC_IN_TMP": "Исполняемый файл во временном каталоге",
    "UID0": "Лишний пользователь с правами root",
    "FW_OUT_DROP": "Попытка соединения наружу заблокирована firewall",
    "WEB_EXPLOIT": "Успешный запрос к подозрительному URL",
    "FILE_CHANGED": "Изменились системные файлы (часто после обновления)",
    "NEW_PORT": "Открылся новый сетевой порт",
}

CONFIG_KINDS: dict[str, str] = {
    "ADMIN": "Администраторы",
    "DELEGATED": "Делегированные админы",
    "FWD": "Внешние пересылки",
    "REDIR": "Внешние sieve-redirect",
    "CFG": "Настройки MTA",
    "ACCT": "Учётки",
    "ALIAS": "Алиасы",
}
# Строки деталей ZIMBRA_CONFIG, которые показываются первыми.
_CONFIG_PRIORITY_RE = re.compile(r"^\s*\+\s*(ADMIN|FWD|REDIR|CFG)\b")

FAMILY_LABELS: dict[str, str] = {
    "intrusion": "Вторжение",
    "config": "Конфигурация Zimbra",
    "availability": "Работа IDS",
    "monitor": "Ошибка проверки",
    "watchdog": "Сигнал жизни IDS",
    "cert": "Сертификат",
    "cert_watchdog": "Срок сертификата",
}

RECOVERY_TEXT: dict[str, str] = {
    "intrusion": "Вторжение: находки исчезли",
    "config": "Конфигурация Zimbra: изменения закрыты",
    "availability": "IDS: контейнер и проверки снова работают",
    "monitor": "IDS: ошибка проверки устранена",
    "watchdog": "IDS: сигнал жизни восстановлен",
    "cert": "Сертификат заменён",
    "cert_watchdog": "Срок сертификата продлён",
}

_STARTED_AT: datetime | None = None
_LAST_WATCHDOG_AT: datetime | None = None
_SCHEMA_READY: set[str] = set()


# ---------------------------------------------------------------------------
# Мелкие помощники
# ---------------------------------------------------------------------------
def _ts(value: datetime) -> str:
    return value.strftime(TIME_FMT)


def _dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:19], TIME_FMT)
    except ValueError:
        return None


def _parse_date(value: Any) -> date | None:
    try:
        return datetime.strptime(str(value or "").strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _int(value: Any) -> int | None:
    match = re.search(r"-?\d+", str(value or ""))
    return int(match.group(0)) if match else None


def _plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def format_duration(delta: timedelta) -> str:
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 1:
        return "меньше минуты"
    days, rest = divmod(minutes, 24 * 60)
    hours, mins = divmod(rest, 60)
    parts = []
    if days:
        parts.append(f"{days} дн")
    if hours:
        parts.append(f"{hours} ч")
    if mins and not days:
        parts.append(f"{mins} мин")
    return " ".join(parts)


def _short(value: datetime | None) -> str:
    return value.strftime("%d.%m %H:%M") if value else "—"


def problem_key(source: str, node: str, ct: str, family: str) -> str:
    return f"{source}/{node}/CT{ct}/{family}"


def source_key(source: str, node: str, ct: str) -> str:
    return f"{source}/{node}/CT{ct}"


def get_ct_names() -> dict[str, str]:
    raw = config_manager.get_setting(CT_NAMES_SETTING, DEFAULT_CT_NAMES)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = None
    if not isinstance(raw, dict):
        return dict(DEFAULT_CT_NAMES)
    return {str(k).strip(): str(v).strip() for k, v in raw.items() if str(k).strip()}


def get_expected_sources() -> list[str]:
    raw = config_manager.get_setting(EXPECTED_SOURCES_SETTING, DEFAULT_EXPECTED_SOURCES)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = [part for part in re.split(r"[,\s]+", raw) if part]
    if not isinstance(raw, list):
        return list(DEFAULT_EXPECTED_SOURCES)
    return [str(item).strip() for item in raw if str(item).strip()]


def target_label(node: str, ct: str, ct_names: dict[str, str] | None = None) -> str:
    names = ct_names if ct_names is not None else get_ct_names()
    name = names.get(str(ct))
    return f"{node} / CT{ct}" + (f" ({name})" if name else "")


# ---------------------------------------------------------------------------
# Разбор письма
# ---------------------------------------------------------------------------
def normalize_subject(subject: str) -> str:
    return " ".join((subject or "").split())


def is_ids_cert_subject(subject: str) -> bool:
    """Письмо наше, если тема начинается с `IDS ` или `CERT ` (даже битая)."""
    normalized = normalize_subject(subject)
    return normalized.startswith("IDS ") or normalized.startswith("CERT ")


def parse_fields(raw: str | None) -> dict[str, str]:
    fields: dict[str, str] = {}
    extra: list[str] = []
    for token in (raw or "").split():
        key, sep, value = token.partition("=")
        if sep and key:
            fields[key.strip().lower()] = value.strip()
        else:
            extra.append(token)
    if extra:
        fields["extra"] = " ".join(extra)
    return fields


def parse_subject(subject: str) -> dict[str, Any] | None:
    match = SUBJECT_RE.match(normalize_subject(subject))
    if not match:
        return None
    source, level, node, ct, event, raw_fields = match.groups()
    return {
        "source": source,
        "level": level,
        "node": node,
        "ct": ct,
        "event": event,
        "fields": parse_fields(raw_fields),
    }


def parse_body(body: str) -> tuple[dict[str, str], str]:
    """Метаданные `key=value` до пустой строки и детали после неё."""
    lines = (body or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    meta: dict[str, str] = {}
    while index < len(lines):
        line = lines[index].strip()
        if not line or not re.match(r"^[A-Za-z_][\w.-]*=", line):
            break
        key, _, value = line.partition("=")
        meta[key.strip().lower()] = value.strip()
        index += 1
    if not meta:
        return {}, (body or "").strip()
    return meta, "\n".join(lines[index:]).strip("\n").strip()


def resolve_event_time(
    date_header: str | None, meta: dict[str, str], received_at: datetime
) -> datetime:
    """Время события: заголовок Date → `time=` в теле → время получения."""
    if date_header:
        try:
            parsed = parsedate_to_datetime(date_header)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone().replace(tzinfo=None)
            return parsed.replace(microsecond=0)
        except (TypeError, ValueError, IndexError):
            pass
    from_body = _dt(meta.get("time"))
    if from_body:
        return from_body
    return received_at.replace(microsecond=0)


def classify(source: str, event: str, level: str) -> tuple[str, str]:
    """(family, действие) для события. Неизвестные WARN/CRIT — отдельная проблема."""
    if source == "CERT":
        return ("cert", DEPLOYED if event == "DEPLOYED" else OPEN)
    if event in IDS_EVENTS:
        return IDS_EVENTS[event]
    if level in ("WARN", "CRIT"):
        return (event.lower(), OPEN)
    return ("info", INFO)


def prepare_details(event: str, details: str) -> str:
    """Детали для оповещения: первые 25 строк, не больше 3000 символов."""
    lines = [line.rstrip() for line in (details or "").strip("\n").split("\n")]
    if event == "ZIMBRA_CONFIG":
        priority = [line for line in lines if _CONFIG_PRIORITY_RE.match(line)]
        lines = priority + [line for line in lines if not _CONFIG_PRIORITY_RE.match(line)]
    text = "\n".join(lines[:ALERT_DETAILS_MAX_LINES]).strip()
    if len(text) > ALERT_DETAILS_MAX_CHARS:
        text = text[: ALERT_DETAILS_MAX_CHARS - 1] + "…"
    return text


# ---------------------------------------------------------------------------
# Тексты оповещений
# ---------------------------------------------------------------------------
def _fields_text(fields: dict[str, Any], skip: tuple[str, ...] = ()) -> str:
    return " ".join(f"{k}={v}" for k, v in fields.items() if k not in skip and k != "extra")


def headline_lines(
    source: str, event: str, fields: dict[str, Any], now: datetime | None = None
) -> list[str]:
    """Человекочитаемая суть события (без значка и цели)."""
    if event == "INTRUSION":
        types = [t for t in str(fields.get("types") or "").split(",") if t]
        count = _int(fields.get("n")) or len(types)
        lines = [f"Вторжение: {count} {_plural(count, 'находка', 'находки', 'находок')}"]
        lines += [f"• {INTRUSION_TYPES.get(t, t)}" for t in types]
        return lines
    if event == "ZIMBRA_CONFIG":
        kinds = [k for k in str(fields.get("kinds") or "").split(",") if k]
        count = _int(fields.get("n")) or len(kinds)
        word = _plural(count, "изменение", "изменения", "изменений")
        lines = [f"Конфигурация Zimbra: {count} {word}"]
        lines += [f"• {CONFIG_KINDS.get(k, k)}" for k in kinds]
        return lines
    if event == "HEARTBEAT":
        return [
            "Heartbeat сообщает о незакрытых находках "
            f"(findings={fields.get('findings', '?')}, zimbra={fields.get('zimbra', '?')})"
        ]
    if event == "DOWN":
        return ["IDS: контейнер не работает"]
    if event == "STALE":
        lastrun = fields.get("lastrun")
        tail = f" (последний прогон {lastrun} назад)" if lastrun else ""
        return [f"IDS: проверки не запускаются{tail}"]
    if event == "MONITOR_ERROR":
        return [f"IDS: сбой проверки {_fields_text(fields)}".rstrip()]
    if event == "WATCHDOG":
        if fields.get("never"):
            return [
                "Нет сигнала жизни от IDS: HEARTBEAT ни разу не приходил за 2 ч после "
                "запуска мониторинга — скрипт не работает, сломан cron или отправка почты"
            ]
        last = _dt(fields.get("last"))
        hours = int((now - last).total_seconds() // 3600) if now and last else None
        span = f" {hours} {_plural(hours, 'час', 'часа', 'часов')}" if hours is not None else ""
        return [
            f"Нет сигнала жизни от IDS{span}: сломан хост, cron, отправка почты "
            "или хост скомпрометирован"
        ]
    if event == "CERT_WATCHDOG":
        until = _parse_date(fields.get("until"))
        left = f" (осталось {(until - now.date()).days} дн.)" if until and now else ""
        return [f"Сертификат истекает {fields.get('until')}{left}, автозамена не сработала"]
    if source == "CERT":
        lines = [f"Сертификат: {CERT_EVENT_DESCRIPTIONS.get(event, event)}"]
        extra = _fields_text(fields, skip=("until",))
        if extra:
            lines.append(f"• {extra}")
        return lines
    extra = _fields_text(fields)
    return [f"Событие {event}" + (f": {extra}" if extra else "")]


def format_problem_alert(
    kind: str,
    level: str,
    ev: dict[str, Any],
    ct_names: dict[str, str],
    since: datetime | None = None,
    now: datetime | None = None,
) -> str:
    """Оповещение о проблеме. kind: new | update | escalate | reminder."""
    suffix = {
        "update": " — обновление",
        "escalate": " — повышение",
        "reminder": " — напоминание",
    }.get(kind, "")
    lines = [
        f"{LEVEL_ICONS.get(level, '❔')} {level}  {target_label(ev['node'], ev['ct'], ct_names)}{suffix}"
    ]
    lines += headline_lines(ev["source"], ev["event"], ev.get("fields") or {}, now=now)
    if kind == "reminder" and since and now:
        lines.append(f"Длится: {format_duration(now - since)}")
    lines.append(f"Время: {_short(ev.get('time'))}")
    details = prepare_details(ev["event"], ev.get("details") or "")
    if details:
        lines += ["---", details, "---"]
    if ev["source"] == "IDS" and level == "CRIT" and ev["event"] == "INTRUSION":
        lines.append(
            f"Что делать: изолировать CT —  ip link set veth{ev['ct']}i0 down  (на {ev['node']})"
        )
    return "\n".join(lines)


def format_recovery_alert(
    family: str,
    ev: dict[str, Any],
    since: datetime | None,
    ct_names: dict[str, str],
) -> str:
    text = RECOVERY_TEXT.get(family, f"{FAMILY_LABELS.get(family, family)}: в норме")
    until = (ev.get("fields") or {}).get("until")
    if family in ("cert", "cert_watchdog") and until:
        text += f", действует до {until}"
    if since and ev.get("time"):
        text += f". Длительность: {format_duration(ev['time'] - since)}"
    return f"🟢 OK  {target_label(ev['node'], ev['ct'], ct_names)}\n{text}"


def format_unparsed_alert(subject: str, event_time: datetime) -> str:
    return (
        "🟡 WARN  Нераспознанное письмо IDS/CERT\n"
        f"Тема: {subject}\n"
        f"Время: {_short(event_time)}\n"
        "Формат темы: <IDS|CERT> <OK|WARN|CRIT> <узел> CT<id> <СОБЫТИЕ> [key=value…]"
    )


# ---------------------------------------------------------------------------
# Хранилище
# ---------------------------------------------------------------------------
def _db_path() -> str:
    from config.db_settings import BACKUP_DATABASE_CONFIG

    return str(BACKUP_DATABASE_CONFIG["backups_db"])


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or _db_path()
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    if path not in _SCHEMA_READY:
        from modules.mail_parts.db.schema import create_schema

        create_schema(conn)
        _SCHEMA_READY.add(path)
    return conn


def _row_event(row: Any) -> dict[str, Any]:
    """Событие из строки ids_state (sqlite3.Row или dict) — для напоминаний и статуса."""
    try:
        fields = json.loads(row["last_fields"] or "{}")
    except ValueError:
        fields = {}
    return {
        "source": row["source"],
        "node": row["node"],
        "ct": row["ct"],
        "event": row["last_event"] or "",
        "fields": fields,
        "details": row["last_details"] or "",
        "time": _dt(row["last_event_at"]),
    }


def _get_state(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    row: sqlite3.Row | None = conn.execute(
        "SELECT * FROM ids_state WHERE problem_key = ?", (key,)
    ).fetchone()
    return row


def _enqueue(
    conn: sqlite3.Connection,
    now: datetime,
    level: str,
    kind: str,
    key: str | None,
    message: str,
) -> None:
    conn.execute(
        "INSERT INTO ids_outbox (created_at, level, kind, problem_key, message) "
        "VALUES (?, ?, ?, ?, ?)",
        (_ts(now), level, kind, key, message),
    )


def _write_state(
    conn: sqlite3.Connection,
    key: str,
    ev: dict[str, Any],
    family: str,
    state: str,
    since: datetime | None,
    notified_at: str | None,
    acknowledged: int,
) -> None:
    conn.execute(
        """
        INSERT INTO ids_state
            (problem_key, source, node, ct, family, state, since, last_event_at,
             last_event, last_subject, last_fields, last_details, last_notified_at,
             acknowledged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(problem_key) DO UPDATE SET
            state = excluded.state,
            since = excluded.since,
            last_event_at = excluded.last_event_at,
            last_event = excluded.last_event,
            last_subject = excluded.last_subject,
            last_fields = excluded.last_fields,
            last_details = excluded.last_details,
            last_notified_at = excluded.last_notified_at,
            acknowledged = excluded.acknowledged
        """,
        (
            key,
            ev["source"],
            ev["node"],
            ev["ct"],
            family,
            state,
            _ts(since) if since else None,
            _ts(ev["time"]),
            ev["event"],
            ev.get("subject"),
            json.dumps(ev.get("fields") or {}, ensure_ascii=False, sort_keys=True),
            ev.get("details") or "",
            notified_at,
            acknowledged,
        ),
    )


# ---------------------------------------------------------------------------
# Автомат состояний
# ---------------------------------------------------------------------------
def _open_problem(
    conn: sqlite3.Connection,
    ev: dict[str, Any],
    family: str,
    level: str,
    now: datetime,
    ct_names: dict[str, str],
) -> str:
    key = problem_key(ev["source"], ev["node"], ev["ct"], family)
    row = _get_state(conn, key)
    last_at = _dt(row["last_event_at"]) if row else None
    if last_at and ev["time"] < last_at:
        return f"{key} out-of-order (письмо старше последнего), состояние не меняется"

    current = row["state"] if row else "OK"
    fields_json = json.dumps(ev.get("fields") or {}, ensure_ascii=False, sort_keys=True)
    changed = (
        row is None
        or row["last_event"] != ev["event"]
        or row["last_fields"] != fields_json
        or (row["last_details"] or "") != (ev.get("details") or "")
    )

    if current == "OK":
        _enqueue(
            conn, now, level, "new", key, format_problem_alert("new", level, ev, ct_names, now=now)
        )
        _write_state(conn, key, ev, family, level, ev["time"], _ts(now), 0)
        return f"{key} OK→{level} notified"

    since = _dt(row["since"]) if row else None
    if LEVEL_RANK[level] > LEVEL_RANK[current]:
        message = format_problem_alert("escalate", level, ev, ct_names, now=now)
        _enqueue(conn, now, level, "escalate", key, message)
        _write_state(conn, key, ev, family, level, since, _ts(now), 0)
        return f"{key} {current}→{level} notified"

    # Тот же или более низкий уровень: CRIT не понижаем до закрывающего события.
    acknowledged = int(row["acknowledged"] or 0) if row else 0
    if changed:
        message = format_problem_alert("update", current, ev, ct_names, now=now)
        _enqueue(conn, now, current, "update", key, message)
        _write_state(conn, key, ev, family, current, since, _ts(now), acknowledged)
        return f"{key} {current} updated notified"

    notified = row["last_notified_at"] if row else None
    _write_state(conn, key, ev, family, current, since, notified, acknowledged)
    return f"{key} {current} duplicate"


def _close_problem(
    conn: sqlite3.Connection,
    ev: dict[str, Any],
    family: str,
    now: datetime,
    ct_names: dict[str, str],
    check_order: bool = True,
) -> str:
    key = problem_key(ev["source"], ev["node"], ev["ct"], family)
    row = _get_state(conn, key)
    if row is None:
        return f"{key} OK (нечего закрывать)"
    last_at = _dt(row["last_event_at"])
    if check_order and last_at and ev["time"] < last_at:
        return f"{key} out-of-order (письмо старше последнего), состояние не меняется"
    if row["state"] == "OK":
        conn.execute(
            "UPDATE ids_state SET last_event_at = ? WHERE problem_key = ?",
            (_ts(max(ev["time"], last_at) if last_at else ev["time"]), key),
        )
        return f"{key} OK (уже закрыто)"

    since = _dt(row["since"])
    _enqueue(conn, now, "OK", "recovery", key, format_recovery_alert(family, ev, since, ct_names))
    _write_state(conn, key, ev, family, "OK", ev["time"], _ts(now), 0)
    return f"{key} {row['state']}→OK notified"


def _is_open(conn: sqlite3.Connection, key: str) -> bool:
    row = _get_state(conn, key)
    return bool(row and row["state"] != "OK")


def _apply_heartbeat(
    conn: sqlite3.Connection, ev: dict[str, Any], now: datetime, ct_names: dict[str, str]
) -> list[str]:
    hb_key = source_key(ev["source"], ev["node"], ev["ct"])
    row = conn.execute(
        "SELECT last_at FROM ids_heartbeat WHERE source_key = ?", (hb_key,)
    ).fetchone()
    last_at = _dt(row["last_at"]) if row else None
    if last_at and ev["time"] < last_at:
        return [f"{hb_key} heartbeat out-of-order, игнор"]
    conn.execute(
        """
        INSERT INTO ids_heartbeat (source_key, node, ct, last_at, level, fields)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_key) DO UPDATE SET
            last_at = excluded.last_at, level = excluded.level, fields = excluded.fields
        """,
        (
            hb_key,
            ev["node"],
            ev["ct"],
            _ts(ev["time"]),
            ev["level"],
            json.dumps(ev.get("fields") or {}, ensure_ascii=False, sort_keys=True),
        ),
    )
    outcomes = [f"{hb_key} heartbeat обновлён"]
    # Сигнал жизни закрывает watchdog независимо от порядка: следующая
    # сторожевая проверка переоткроет его, если и этот heartbeat старый.
    outcomes.append(_close_problem(conn, ev, "watchdog", now, ct_names, check_order=False))
    if ev["level"] == "OK":
        outcomes.append(_close_problem(conn, ev, "availability", now, ct_names))
        outcomes.append(_close_problem(conn, ev, "monitor", now, ct_names))
        return outcomes

    intrusion_key = problem_key(ev["source"], ev["node"], ev["ct"], "intrusion")
    config_key = problem_key(ev["source"], ev["node"], ev["ct"], "config")
    if _is_open(conn, intrusion_key) or _is_open(conn, config_key):
        outcomes.append(f"{hb_key} heartbeat WARN: проблемы уже открыты")
        return outcomes
    outcomes.append(_open_problem(conn, ev, "intrusion", "WARN", now, ct_names))
    return outcomes


def _apply_deployed(
    conn: sqlite3.Connection, ev: dict[str, Any], now: datetime, ct_names: dict[str, str]
) -> list[str]:
    outcomes = [_close_problem(conn, ev, "cert", now, ct_names)]
    until = _parse_date((ev.get("fields") or {}).get("until"))
    if until is None:
        outcomes.append("DEPLOYED без until= — срок сертификата не обновлён")
        return outcomes
    cu_key = source_key(ev["source"], ev["node"], ev["ct"])
    row = conn.execute(
        "SELECT until_date FROM ids_cert_until WHERE source_key = ?", (cu_key,)
    ).fetchone()
    old_until = _parse_date(row["until_date"]) if row else None
    if old_until and until <= old_until:
        outcomes.append(f"{cu_key} срок {old_until} не меняется")
        return outcomes
    conn.execute(
        """
        INSERT INTO ids_cert_until (source_key, node, ct, until_date, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(source_key) DO UPDATE SET
            until_date = excluded.until_date, updated_at = excluded.updated_at
        """,
        (cu_key, ev["node"], ev["ct"], until.isoformat(), _ts(now)),
    )
    outcomes.append(f"{cu_key} cert_until={until.isoformat()}")
    outcomes.append(_close_problem(conn, ev, "cert_watchdog", now, ct_names, check_order=False))
    return outcomes


def _apply_event(
    conn: sqlite3.Connection, ev: dict[str, Any], now: datetime, ct_names: dict[str, str]
) -> tuple[str, list[str]]:
    family, action = classify(ev["source"], ev["event"], ev["level"])
    if action == OPEN:
        if ev["level"] == "OK":
            return family, [f"{ev['event']} с уровнем OK — только журнал"]
        return family, [_open_problem(conn, ev, family, ev["level"], now, ct_names)]
    if action == CLOSE:
        return family, [_close_problem(conn, ev, family, now, ct_names)]
    if action == HEARTBEAT:
        return family, _apply_heartbeat(conn, ev, now, ct_names)
    if action == DEPLOYED:
        return family, _apply_deployed(conn, ev, now, ct_names)
    return family, ["info — только журнал"]


def handle_email(
    subject: str,
    body: str = "",
    message_id: str | None = None,
    date_header: str | None = None,
    db_path: str | None = None,
    now: datetime | None = None,
    ct_names: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Обрабатывает письмо IDS/CERT. None — письмо не наше.

    Возвращает {"outcome": "processed"|"duplicate"|"unparsed", "log": str, …}.
    """
    normalized = normalize_subject(subject)
    if not is_ids_cert_subject(normalized):
        return None

    now = (now or datetime.now()).replace(microsecond=0)
    names = ct_names if ct_names is not None else get_ct_names()
    meta, details = parse_body(body)
    event_time = resolve_event_time(date_header, meta, now)
    msg_id = (message_id or "").strip() or (
        "nomsgid:"
        + hashlib.sha1(
            f"{normalized}|{date_header or ''}|{body or ''}".encode(), usedforsecurity=False
        ).hexdigest()
    )
    parsed = parse_subject(normalized)

    conn = _connect(db_path)
    try:
        journal = {
            "source": parsed["source"] if parsed else normalized.split(" ", 1)[0],
            "level": parsed["level"] if parsed else "WARN",
            "node": parsed["node"] if parsed else None,
            "ct": parsed["ct"] if parsed else None,
            "event": parsed["event"] if parsed else "UNPARSED",
            "fields": parsed["fields"] if parsed else {},
        }
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO ids_events
                (message_id, source, level, node, ct, event, fields, details,
                 subject, event_time, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg_id,
                journal["source"],
                journal["level"],
                journal["node"],
                journal["ct"],
                journal["event"],
                json.dumps(journal["fields"], ensure_ascii=False, sort_keys=True),
                details[:JOURNAL_DETAILS_MAX_CHARS],
                normalized[:500],
                _ts(event_time),
                _ts(now),
            ),
        )
        if cursor.rowcount == 0:
            conn.commit()
            return {
                "outcome": "duplicate",
                "log": f"{normalized[:80]} — повтор Message-ID, игнор",
            }
        event_id = cursor.lastrowid

        if parsed is None:
            _enqueue(
                conn, now, "WARN", "unparsed", None, format_unparsed_alert(normalized, event_time)
            )
            conn.execute(
                "UPDATE ids_events SET outcome = ? WHERE id = ?", ("unparsed notified", event_id)
            )
            conn.commit()
            return {
                "outcome": "unparsed",
                "log": f"{normalized[:80]} — нераспознано, WARN notified",
            }

        ev = dict(parsed, details=details, time=event_time, subject=normalized)
        family, outcomes = _apply_event(conn, ev, now, names)
        outcome_text = "; ".join(outcomes)
        conn.execute(
            "UPDATE ids_events SET family = ?, problem_key = ?, outcome = ? WHERE id = ?",
            (
                family,
                problem_key(ev["source"], ev["node"], ev["ct"], family),
                outcome_text,
                event_id,
            ),
        )
        conn.commit()
        return {
            "outcome": "processed",
            "source": ev["source"],
            "level": ev["level"],
            "event": ev["event"],
            "family": family,
            "log": f"{ev['source']} {ev['level']} {ev['node']}/CT{ev['ct']}/{family} {outcome_text}",
        }
    finally:
        conn.close()


def enqueue_processing_error(subject: str, error: str, db_path: str | None = None) -> bool:
    """Оповещение об ошибке обработки IDS/CERT-письма (письмо не должно потеряться)."""
    try:
        conn = _connect(db_path)
        try:
            _enqueue(
                conn,
                datetime.now(),
                "WARN",
                "error",
                None,
                "🟡 WARN  Ошибка обработки письма IDS/CERT\n"
                f"Тема: {normalize_subject(subject)}\n"
                f"Ошибка: {error[:500]}\n"
                "Письмо лежит в Maildir/cur — проверьте его вручную.",
            )
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception as exc:  # noqa: BLE001
        debug_log(f"❌ ids_cert: не удалось поставить оповещение об ошибке: {exc}")
        return False


# ---------------------------------------------------------------------------
# Сторожевые проверки, напоминания, рассылка (основной цикл)
# ---------------------------------------------------------------------------
def _parse_expected(item: str) -> tuple[str, str] | None:
    match = re.match(r"^\s*([^/\s]+)\s*/\s*CT(\d+)\s*$", item or "", re.IGNORECASE)
    return (match.group(1), match.group(2)) if match else None


def run_watchdogs(
    conn: sqlite3.Connection,
    now: datetime,
    started_at: datetime,
    ct_names: dict[str, str],
    expected: list[str],
) -> list[str]:
    outcomes: list[str] = []
    heartbeats = {
        (row["node"], row["ct"]): _dt(row["last_at"])
        for row in conn.execute("SELECT node, ct, last_at FROM ids_heartbeat").fetchall()
    }
    for (node, ct), last_at in heartbeats.items():
        if last_at and now - last_at > HEARTBEAT_TIMEOUT:
            ev = {
                "source": "IDS",
                "node": node,
                "ct": ct,
                "event": "WATCHDOG",
                "level": "CRIT",
                "fields": {"last": _ts(last_at)},
                "details": f"Последний HEARTBEAT: {_short(last_at)}",
                "time": now,
            }
            outcomes.append(_open_problem(conn, ev, "watchdog", "CRIT", now, ct_names))

    if now - started_at >= HEARTBEAT_TIMEOUT:
        for item in expected:
            parsed = _parse_expected(item)
            if not parsed or parsed in heartbeats:
                continue
            node, ct = parsed
            ev = {
                "source": "IDS",
                "node": node,
                "ct": ct,
                "event": "WATCHDOG",
                "level": "CRIT",
                "fields": {"never": _ts(started_at)},
                "details": f"Мониторинг запущен {_short(started_at)}, HEARTBEAT не приходил.",
                "time": now,
            }
            outcomes.append(_open_problem(conn, ev, "watchdog", "CRIT", now, ct_names))

    for row in conn.execute("SELECT node, ct, until_date FROM ids_cert_until").fetchall():
        until = _parse_date(row["until_date"])
        if until is None or (until - now.date()).days >= CERT_WATCHDOG_DAYS:
            continue
        ev = {
            "source": "CERT",
            "node": row["node"],
            "ct": row["ct"],
            "event": "CERT_WATCHDOG",
            "level": "CRIT",
            "fields": {"until": until.isoformat()},
            "details": f"Сертификат действует до {until.isoformat()}; письма DEPLOYED с новым сроком не было.",
            "time": now,
        }
        outcomes.append(_open_problem(conn, ev, "cert_watchdog", "CRIT", now, ct_names))
    return outcomes


def run_reminders(conn: sqlite3.Connection, now: datetime, ct_names: dict[str, str]) -> int:
    count = 0
    rows = conn.execute(
        "SELECT * FROM ids_state WHERE state IN ('WARN', 'CRIT') AND COALESCE(acknowledged, 0) = 0"
    ).fetchall()
    for row in rows:
        interval = REMINDER_INTERVALS[row["state"]]
        last = _dt(row["last_notified_at"])
        if last and now - last < interval:
            continue
        ev = _row_event(row)
        message = format_problem_alert(
            "reminder", row["state"], ev, ct_names, since=_dt(row["since"]), now=now
        )
        _enqueue(conn, now, row["state"], "reminder", row["problem_key"], message)
        conn.execute(
            "UPDATE ids_state SET last_notified_at = ? WHERE problem_key = ?",
            (_ts(now), row["problem_key"]),
        )
        count += 1
    return count


def is_immediate(level: str, kind: str | None, key: str | None) -> bool:
    """Оповещение уходит сразу, мимо тихих часов."""
    if level == "CRIT":
        return True
    family = (key or "").rsplit("/", 1)[-1]
    return family in IMMEDIATE_FAMILIES and kind in IMMEDIATE_KINDS


def dispatch_outbox(
    conn: sqlite3.Connection,
    send_alert_func: Callable[..., Any],
    now: datetime,
    silent: bool = False,
) -> int:
    """Рассылает очередь.

    CRIT и новые признаки взлома (см. `is_immediate`) — немедленно (force,
    мимо тихих часов), остальное в тихие часы ждёт их окончания.
    """
    sent = 0
    threshold = _ts(now - OUTBOX_MAX_AGE)
    rows = conn.execute(
        "SELECT id, created_at, level, kind, problem_key, message FROM ids_outbox "
        "WHERE status = 'pending' ORDER BY id"
    ).fetchall()
    for row in rows:
        if str(row["created_at"]) < threshold:
            conn.execute("UPDATE ids_outbox SET status = 'expired' WHERE id = ?", (row["id"],))
            continue
        level = str(row["level"])
        force = is_immediate(level, row["kind"], row["problem_key"])
        if silent and not force:
            continue
        try:
            result = send_alert_func(
                row["message"],
                alert_type=ALERT_TYPES.get(level, "info"),
                force=force,
            )
        except Exception as exc:  # noqa: BLE001
            debug_log(f"⚠️ ids_cert: ошибка отправки оповещения #{row['id']}: {exc}")
            continue
        status = "failed" if result is False else "sent"
        conn.execute(
            "UPDATE ids_outbox SET status = ?, sent_at = ? WHERE id = ?",
            (status, _ts(now), row["id"]),
        )
        conn.commit()
        sent += 1 if status == "sent" else 0
    conn.commit()
    return sent


def tick(
    send_alert_func: Callable[..., Any],
    is_silent_func: Callable[[], bool] | None = None,
    db_path: str | None = None,
    now: datetime | None = None,
    force_watchdog: bool = False,
) -> int:
    """Проход основного цикла: сторожа и напоминания раз в 5 минут, затем рассылка."""
    global _STARTED_AT, _LAST_WATCHDOG_AT
    if not extension_manager.is_extension_enabled(EXTENSION_ID):
        return 0
    now = (now or datetime.now()).replace(microsecond=0)
    if _STARTED_AT is None:
        _STARTED_AT = now
    silent = False
    if is_silent_func is not None:
        try:
            silent = bool(is_silent_func())
        except Exception as exc:  # noqa: BLE001
            debug_log(f"⚠️ ids_cert: не удалось проверить тихий режим: {exc}")

    conn = _connect(db_path)
    try:
        if (
            force_watchdog
            or _LAST_WATCHDOG_AT is None
            or now - _LAST_WATCHDOG_AT >= WATCHDOG_INTERVAL
        ):
            names = get_ct_names()
            for outcome in run_watchdogs(conn, now, _STARTED_AT, names, get_expected_sources()):
                if "notified" in outcome:
                    debug_log(f"🛡️ ids_cert watchdog: {outcome}")
            run_reminders(conn, now, names)
            conn.commit()
            _LAST_WATCHDOG_AT = now
        return dispatch_outbox(conn, send_alert_func, now, silent=silent)
    finally:
        conn.close()


def acknowledge(key: str, by: str = "", db_path: str | None = None) -> bool:
    """Подтверждение проблемы человеком: напоминания по ней прекращаются."""
    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "UPDATE ids_state SET acknowledged = 1, ack_by = ?, ack_at = ? "
            "WHERE problem_key = ? AND state != 'OK'",
            (by or None, _ts(datetime.now()), key),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Представление (Telegram / Matrix / web / Android / отчёт)
# ---------------------------------------------------------------------------
def get_open_problems(db_path: str | None = None) -> list[dict[str, Any]]:
    """Открытые проблемы: сначала CRIT, затем WARN, внутри — по ключу."""
    conn = _connect(db_path)
    try:
        rows = conn.execute("SELECT * FROM ids_state WHERE state != 'OK'").fetchall()
    finally:
        conn.close()
    items = [dict(row) for row in rows]
    items.sort(key=lambda r: (-LEVEL_RANK.get(r["state"], 0), r["problem_key"]))
    return items


def get_overview(db_path: str | None = None, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    conn = _connect(db_path)
    try:
        states = [dict(r) for r in conn.execute("SELECT * FROM ids_state").fetchall()]
        heartbeats = [dict(r) for r in conn.execute("SELECT * FROM ids_heartbeat").fetchall()]
        certs = [dict(r) for r in conn.execute("SELECT * FROM ids_cert_until").fetchall()]
        since = _ts(now - timedelta(days=30))
        level_counts = {
            row["level"]: row["cnt"]
            for row in conn.execute(
                "SELECT level, COUNT(*) AS cnt FROM ids_events WHERE event_time >= ? GROUP BY level",
                (since,),
            ).fetchall()
        }
    finally:
        conn.close()

    targets: dict[tuple[str, str], str] = {}
    for item in get_expected_sources():
        parsed = _parse_expected(item)
        if parsed:
            targets.setdefault(parsed, "OK")
    for row in heartbeats + certs:
        targets.setdefault((row["node"], row["ct"]), "OK")
    for row in states:
        target = (row["node"], row["ct"])
        current = targets.get(target, "OK")
        if LEVEL_RANK.get(row["state"], 0) > LEVEL_RANK.get(current, 0):
            current = row["state"]
        targets[target] = current

    open_problems = [r for r in states if r["state"] != "OK"]
    open_problems.sort(key=lambda r: (-LEVEL_RANK.get(r["state"], 0), r["problem_key"]))
    return {
        "targets": targets,
        "total": len(targets),
        "ok": sum(1 for s in targets.values() if s == "OK"),
        "crit": sum(1 for r in open_problems if r["state"] == "CRIT"),
        "warn": sum(1 for r in open_problems if r["state"] == "WARN"),
        "open": open_problems,
        "states": states,
        "heartbeats": heartbeats,
        "certs": certs,
        "events_30d": level_counts,
    }


def build_status_lines(db_path: str | None = None, now: datetime | None = None) -> list[str]:
    """Статус для всех клиентов. Вторая строка `Контейнеров в норме: x/y` — для плашки."""
    now = now or datetime.now()
    names = get_ct_names()
    ov = get_overview(db_path, now)
    lines = ["🛡️ IDS и сертификат почты"]
    if not (ov["states"] or ov["heartbeats"] or ov["certs"] or ov["events_30d"]):
        lines += ["", "⚪ Писем IDS/CERT ещё не было."]
        expected = get_expected_sources()
        if expected:
            lines.append(
                f"Ожидается HEARTBEAT от: {', '.join(expected)} — если не придёт за 2 ч "
                "после запуска мониторинга, будет CRIT."
            )
        return lines
    lines.append(
        f"Контейнеров в норме: {ov['ok']}/{ov['total']} · 🔴 {ov['crit']} · 🟡 {ov['warn']}"
    )

    lines.append("")
    if ov["open"]:
        lines.append("Открытые проблемы:")
        for row in ov["open"]:
            since = _dt(row["since"])
            duration = format_duration(now - since) if since else "?"
            label = FAMILY_LABELS.get(row["family"], row["family"])
            ack = " · ✋ подтверждено" if row.get("acknowledged") else ""
            lines.append(
                f"{LEVEL_ICONS.get(row['state'], '❔')} {row['state']} "
                f"{target_label(row['node'], row['ct'], names)} · {label}{ack}"
            )
            lines.append(f"   с {_short(since)} ({duration}) · {row.get('last_event') or ''}")
            ev = _row_event(row)
            for headline in headline_lines(ev["source"], ev["event"], ev["fields"], now=now)[:4]:
                lines.append(f"   {headline}")
    else:
        lines.append("🟢 Открытых проблем нет")

    if ov["heartbeats"]:
        lines += ["", "💓 Сигнал жизни IDS:"]
        for hb in sorted(ov["heartbeats"], key=lambda r: r["source_key"]):
            last = _dt(hb["last_at"])
            age = format_duration(now - last) if last else "?"
            stale = " ❗" if last and now - last > HEARTBEAT_TIMEOUT else ""
            try:
                fields = json.loads(hb.get("fields") or "{}")
            except ValueError:
                fields = {}
            extra = _fields_text(fields)
            lines.append(
                f"   {hb['node']}/CT{hb['ct']}: {age} назад{stale}"
                + (f" ({extra})" if extra else "")
            )

    if ov["certs"]:
        lines += ["", "📜 Сертификат:"]
        for cert in sorted(ov["certs"], key=lambda r: r["source_key"]):
            until = _parse_date(cert["until_date"])
            left = (until - now.date()).days if until else None
            mark = " ❗" if left is not None and left < CERT_WATCHDOG_DAYS else ""
            lines.append(
                f"   {cert['node']}/CT{cert['ct']}: до {cert['until_date']} (осталось {left} дн.){mark}"
            )

    counts = ov["events_30d"]
    if counts:
        total = sum(counts.values())
        lines += [
            "",
            f"🕘 За 30 дней: {total} {_plural(total, 'письмо', 'письма', 'писем')} "
            f"(🔴 {counts.get('CRIT', 0)} · 🟡 {counts.get('WARN', 0)} · 🟢 {counts.get('OK', 0)})",
        ]
    return lines


def get_history(
    days: int = 30, limit: int = 30, db_path: str | None = None, now: datetime | None = None
) -> list[dict[str, Any]]:
    now = now or datetime.now()
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM ids_events WHERE event_time >= ? ORDER BY event_time DESC, id DESC LIMIT ?",
            (_ts(now - timedelta(days=days)), int(limit)),
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def build_history_lines(days: int = 30, limit: int = 30, db_path: str | None = None) -> list[str]:
    events = get_history(days, limit, db_path)
    lines = [f"🕘 Журнал IDS/CERT за {days} дней (последние {limit})", ""]
    if not events:
        lines.append("⚪ Писем не было.")
    for ev in events:
        icon = LEVEL_ICONS.get(str(ev.get("level")), "❔")
        target = f"{ev.get('node')}/CT{ev.get('ct')}" if ev.get("node") else "—"
        outcome = str(ev.get("outcome") or "")
        mark = ""
        if "→" in outcome:
            mark = " · " + ", ".join(re.findall(r"\b(?:OK|WARN|CRIT)→(?:OK|WARN|CRIT)\b", outcome))
        elif "out-of-order" in outcome:
            mark = " · старое письмо"
        lines.append(
            f"{icon} {_short(_dt(ev.get('event_time')))} {ev.get('source')} {target} "
            f"{ev.get('event')}{mark}"
        )
    return lines


def build_help_lines() -> list[str]:
    lines = [
        "📖 Письма IDS и CERT (скрипты на хосте PVE)",
        "",
        "Тема: <IDS|CERT> <OK|WARN|CRIT> <узел> CT<id> <СОБЫТИЕ> [key=value…]",
        "",
        "IDS — мониторинг взлома контейнера:",
    ]
    lines += [f"• {k} — {v}" for k, v in IDS_EVENT_DESCRIPTIONS.items()]
    lines += ["", "CERT — замена TLS-сертификата почты:"]
    lines += [f"• {k} — {v}" for k, v in CERT_EVENT_DESCRIPTIONS.items()]
    lines += [
        "",
        "CRIT, а также новое «Вторжение» или «Конфигурация Zimbra» любого уровня — "
        "сразу, мимо тихих часов. Напоминания: CRIT каждые 2 ч, WARN раз в 12 ч.",
        "«Подтвердить» только прекращает напоминания; проблема закрывается, когда IDS "
        "пришлёт RESOLVED (или OK-событие своего семейства).",
        "Сторож: нет HEARTBEAT 2 ч → CRIT; до конца срока сертификата < 10 дней → CRIT.",
    ]
    return lines


def get_report_summary(db_path: str | None = None) -> tuple[list[str], bool]:
    """Секция утреннего отчёта."""
    now = datetime.now()
    ov = get_overview(db_path, now)
    if not (ov["states"] or ov["heartbeats"] or ov["certs"]):
        return ["⚪ Писем IDS/CERT ещё не было"], False
    names = get_ct_names()
    lines = [f"Контейнеров в норме: {ov['ok']}/{ov['total']}"]
    for row in ov["open"]:
        lines.append(
            f"{LEVEL_ICONS.get(row['state'], '❔')} {target_label(row['node'], row['ct'], names)}: "
            f"{FAMILY_LABELS.get(row['family'], row['family'])} ({row.get('last_event')})"
        )
    for cert in ov["certs"]:
        until = _parse_date(cert["until_date"])
        if until:
            lines.append(
                f"• Сертификат {cert['node']}/CT{cert['ct']}: до {until} ({(until - now.date()).days} дн.)"
            )
    return lines, bool(ov["open"])


__all__ = [
    "EXTENSION_ID",
    "acknowledge",
    "build_help_lines",
    "build_history_lines",
    "build_status_lines",
    "enqueue_processing_error",
    "format_duration",
    "get_open_problems",
    "get_overview",
    "get_report_summary",
    "handle_email",
    "headline_lines",
    "is_ids_cert_subject",
    "parse_body",
    "parse_subject",
    "prepare_details",
    "tick",
]
