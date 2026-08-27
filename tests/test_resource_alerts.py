"""
Unit-тесты для декларативной схемы ресурсных алертов
(`core.monitor_parts.alerts.evaluate_alert_rules`).

PR8: pure-функция `evaluate_alert_rules` заменяет три копи-пастных
блока в монолитном `check_resource_alerts` (и удаляет дубликат в
`modules/resources.py`). Тесты закрепляют поведение по трём сценариям:
1. Disk-алерт срабатывает сразу (streak=1).
2. CPU/RAM требуют двух подряд проверок выше порога.
3. Дедупликация по интервалу не даёт повторно отправлять тот же алерт.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

THRESHOLDS = {"disk_alert": 80, "cpu_alert": 85, "ram_alert": 90}
INTERVAL = 600  # секунд


def _make_entry(*, cpu: int = 0, ram: int = 0, disk: int = 0, name: str = "test-srv") -> dict:
    return {"cpu": cpu, "ram": ram, "disk": disk, "server_name": name}


def test_disk_alert_fires_immediately_without_history() -> None:
    """Disk-правило streak=1 — алерт уходит при первой же высокой пробе."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    sent: dict = {}
    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(disk=95),
        history=[],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert len(alerts) == 1
    assert "💾" in alerts[0]
    assert "95%" in alerts[0]
    assert "10.0.0.1_disk" in sent


def test_cpu_requires_two_consecutive_high_checks() -> None:
    """CPU streak=2: одна высокая текущая без истории — пусто."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    sent: dict = {}
    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(cpu=92),
        history=[],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert alerts == []
    assert sent == {}


def test_cpu_alert_fires_after_two_consecutive_high() -> None:
    """CPU streak=2: текущая 92% + предыдущая 88% (обе >= 85) → алерт."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    sent: dict = {}
    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(cpu=92),
        history=[_make_entry(cpu=88)],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert len(alerts) == 1
    assert "💻" in alerts[0]
    assert "88% → 92%" in alerts[0]


def test_ram_streak_broken_by_low_prev() -> None:
    """RAM: предыдущая 50% < порога 90 → текущая 95% алерт не даёт."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    sent: dict = {}
    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(ram=95),
        history=[_make_entry(ram=50)],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert alerts == []


def test_dedup_within_interval_suppresses_repeat() -> None:
    """Повторный вызов в пределах interval — алерт не пере-отправляется."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    base_time = datetime(2026, 1, 1, 12, 0, 0)
    sent: dict = {}

    first = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(disk=95),
        history=[],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=base_time,
    )
    assert len(first) == 1
    sent_first = dict(sent)

    second = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(disk=96),
        history=[],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=base_time + timedelta(seconds=INTERVAL - 1),
    )
    assert second == []
    assert sent == sent_first  # не обновился


def test_dedup_after_interval_allows_repeat() -> None:
    """После interval+1 секунд — повторный алерт уходит снова."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    base_time = datetime(2026, 1, 1, 12, 0, 0)
    sent: dict = {"10.0.0.1_disk": base_time}

    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(disk=95),
        history=[],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=base_time + timedelta(seconds=INTERVAL + 1),
    )
    assert len(alerts) == 1
    # Время отправки обновилось
    assert sent["10.0.0.1_disk"] == base_time + timedelta(seconds=INTERVAL + 1)


def test_all_three_rules_fire_independently() -> None:
    """Если все три метрики превышены (и для CPU/RAM есть streak) —
    три алерта в одном вызове, по одному на правило."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    sent: dict = {}
    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(cpu=92, ram=95, disk=90),
        history=[_make_entry(cpu=87, ram=91)],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
        now=datetime(2026, 1, 1, 12, 0, 0),
    )
    emojis = {a[0] for a in alerts}
    assert emojis == {"💾", "💻", "🧠"}
    assert set(sent.keys()) == {
        "10.0.0.1_disk",
        "10.0.0.1_cpu",
        "10.0.0.1_ram",
    }


def test_below_threshold_no_alert() -> None:
    """Все метрики ниже порога — пусто."""
    from core.monitor_parts.alerts import evaluate_alert_rules

    sent: dict = {}
    alerts = evaluate_alert_rules(
        "10.0.0.1",
        _make_entry(cpu=70, ram=80, disk=50),
        history=[_make_entry(cpu=70, ram=80, disk=50)],
        sent_state=sent,
        thresholds=THRESHOLDS,
        alert_interval_seconds=INTERVAL,
    )
    assert alerts == []
    assert sent == {}


def test_alert_rules_export_contains_three_metrics() -> None:
    """Защита от потери правила: ALERT_RULES должен содержать ровно
    три правила — по одному на disk, cpu, ram."""
    from core.monitor_parts.alerts import ALERT_RULES

    metrics = {rule.metric for rule in ALERT_RULES}
    assert metrics == {"disk", "cpu", "ram"}
    by_metric = {rule.metric: rule for rule in ALERT_RULES}
    assert by_metric["disk"].requires_streak == 1
    assert by_metric["cpu"].requires_streak == 2
    assert by_metric["ram"].requires_streak == 2
