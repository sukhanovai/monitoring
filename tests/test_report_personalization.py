"""
Тесты персонализации доставки:

* `MorningReport.build_report` собирает отчёт по составу конкретного
  пользователя, а секции переиспользуются между получателями (кэш);
* `lib.alerts.send_alert` раскладывает сообщение по личным каналам
  адресатов и падает обратно на общие каналы, когда реестр пуст.
"""

from __future__ import annotations

import importlib
from datetime import datetime

import pytest

from modules.morning_report import MorningReport

_extension_manager_module = importlib.import_module("extensions.extension_manager")


@pytest.fixture()
def report(monkeypatch):
    """Отчёт с готовым слепком данных и включёнными расширениями."""
    monkeypatch.setattr(
        _extension_manager_module.extension_manager,
        "is_extension_enabled",
        lambda extension_id: True,
    )

    instance = MorningReport()
    instance.morning_data = {
        "status": {
            "ok": [{"name": "srv1", "ip": "10.0.0.1", "type": "ssh"}],
            "failed": [],
        },
        "collection_time": datetime(2026, 8, 10, 9, 0),
        "manual_call": True,
    }
    return instance


def _stub_section(instance, monkeypatch, method_name, calls, label):
    def _collector(*args, **kwargs):
        calls.append(label)
        return ([f"{label}: ок"], False)

    monkeypatch.setattr(instance, method_name, _collector)


def test_build_report_uses_explicit_composition(report, monkeypatch):
    calls = []
    _stub_section(report, monkeypatch, "get_zfs_summary_for_report", calls, "zfs")
    _stub_section(report, monkeypatch, "get_proxmox_summary_for_report", calls, "proxmox")

    built = report.build_report(report_extensions=["zfs_monitor"])
    titles = [section["title"] for section in built["sections"]]

    assert titles[0] == "🖥 Доступность серверов"
    assert any("ZFS" in title for title in titles)
    assert not any("Proxmox" in title for title in titles)
    assert calls == ["zfs"]


def test_two_users_get_different_reports(report, monkeypatch):
    calls = []
    _stub_section(report, monkeypatch, "get_zfs_summary_for_report", calls, "zfs")
    _stub_section(report, monkeypatch, "get_proxmox_summary_for_report", calls, "proxmox")

    first = report.build_report(report_extensions=["zfs_monitor"])
    second = report.build_report(report_extensions=["backup_monitor"])

    assert [s["title"] for s in first["sections"]] != [s["title"] for s in second["sections"]]
    assert "🧊 Статусы ZFS" in first["composition"]
    assert "Proxmox" in second["composition"]


def test_section_cache_collects_data_once_for_all_recipients(report, monkeypatch):
    """Общая секция собирается один раз, даже если её выбрали несколько."""
    calls = []
    _stub_section(report, monkeypatch, "get_zfs_summary_for_report", calls, "zfs")
    _stub_section(report, monkeypatch, "get_proxmox_summary_for_report", calls, "proxmox")

    cache = {}
    report.build_report(report_extensions=["zfs_monitor"], section_cache=cache)
    report.build_report(report_extensions=["zfs_monitor", "backup_monitor"], section_cache=cache)

    assert calls == ["zfs", "proxmox"]
    assert set(cache) == {"zfs_monitor", "backup_monitor"}


def test_cached_section_lines_are_not_shared_between_reports(report, monkeypatch):
    calls = []
    _stub_section(report, monkeypatch, "get_zfs_summary_for_report", calls, "zfs")

    cache = {}
    first = report.build_report(report_extensions=["zfs_monitor"], section_cache=cache)
    second = report.build_report(report_extensions=["zfs_monitor"], section_cache=cache)

    first["sections"][-1]["lines"].append("правка в одном отчёте")
    assert second["sections"][-1]["lines"] == ["zfs: ок"]


# ---------------------------------------------------------------------------
# Раскладка оповещений по личным каналам
# ---------------------------------------------------------------------------


@pytest.fixture()
def alerts_module(monkeypatch):
    alerts = importlib.import_module("lib.alerts")
    monkeypatch.setattr(alerts, "_telegram_bot", object())
    monkeypatch.setattr(alerts, "_chat_ids", ["legacy-chat"])
    monkeypatch.setattr(alerts, "_is_cooldown_active", lambda *a, **k: False)
    return alerts


def _capture_channels(alerts, monkeypatch):
    sent = []

    def _telegram(message, alert_type, html=None, reply_markup=None, chat_ids=None):
        sent.append(("telegram", tuple(chat_ids) if chat_ids is not None else None))
        return True

    def _matrix(message, buttons=None, attach_menu_button=False, html=None, room_id=None):
        sent.append(("matrix", room_id))
        return True

    monkeypatch.setattr(alerts, "_send_telegram_alert", _telegram)
    monkeypatch.setattr(alerts, "_send_matrix_alert", _matrix)
    return sent


def test_send_alert_delivers_to_personal_channels(alerts_module, monkeypatch):
    sent = _capture_channels(alerts_module, monkeypatch)
    targets = [
        {
            "user": {"id": 1, "username": "ivan"},
            "telegram": ["111"],
            "matrix": ["!ivan:example.org"],
        },
        {"user": {"id": 2, "username": "petr"}, "telegram": ["222"], "matrix": []},
    ]
    monkeypatch.setattr(alerts_module, "_resolve_delivery_targets", lambda *a, **k: targets)

    assert alerts_module.send_alert("тест", force=True, category="availability") is True
    assert sent == [
        ("telegram", ("111",)),
        ("matrix", "!ivan:example.org"),
        ("telegram", ("222",)),
    ]


def test_send_alert_falls_back_to_common_channels(alerts_module, monkeypatch):
    """Реестр пуст — работает прежний однопользовательский режим."""
    sent = _capture_channels(alerts_module, monkeypatch)
    monkeypatch.setattr(alerts_module, "_resolve_delivery_targets", lambda *a, **k: [])

    assert alerts_module.send_alert("тест", force=True) is True
    assert sent == [("telegram", None), ("matrix", None)]


def test_send_alert_with_explicit_recipients_does_not_broadcast(alerts_module, monkeypatch):
    sent = _capture_channels(alerts_module, monkeypatch)
    monkeypatch.setattr(alerts_module, "_resolve_delivery_targets", lambda *a, **k: [])

    assert alerts_module.send_alert("тест", force=True, user_ids=[42]) is False
    assert sent == []
