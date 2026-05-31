"""
Unit-тесты для группировки config_console (backup_utils.group_config_console_rows).

Проверяют: выбор самой свежей записи на хост, подсветку отсутствующих
ожидаемых серверов и вынос финальной передачи (delivery_method=nas-final)
в отдельную позицию.
"""

from __future__ import annotations


def _row(host, status, delivery="ssh-rsync", received="2026-05-31 03:00:00", files=10):
    # Порядок колонок как в BackupBot.get_config_console_backups:
    # host, status, delivery_method, receiver, started, completed,
    # vm, lxc, hist_containers, hist_files, errors, problem_items, received_at
    return (
        host, status, delivery, "rcv", "start", "done",
        2, 5, 5, files, 0, None, received,
    )


def test_latest_per_host_and_missing():
    from extensions.backup_monitor.backup_utils import group_config_console_rows

    rows = [
        _row("sr-pve5", "OK", received="2026-05-31 04:00:00"),
        _row("sr-pve5", "ERROR", received="2026-05-31 02:00:00"),  # старее — игнор
        _row("sr-pve6", "PARTIAL", received="2026-05-31 03:30:00"),
    ]
    grouped = group_config_console_rows(rows, expected_servers=["sr-pve5", "sr-pve6", "sr-bup"])

    by_host = {s["host"]: s for s in grouped["servers"]}
    # порядок — как в expected
    assert [s["host"] for s in grouped["servers"]] == ["sr-pve5", "sr-pve6", "sr-bup"]
    # самая свежая запись sr-pve5 — OK
    assert by_host["sr-pve5"]["latest"][1] == "OK"
    assert by_host["sr-pve5"]["runs"] == 2
    # sr-bup нет в данных → missing
    assert by_host["sr-bup"]["missing"] is True
    assert by_host["sr-bup"]["latest"] is None
    assert grouped["missing"] == ["sr-bup"]
    assert grouped["final"] is None


def test_final_transfer_separated():
    from extensions.backup_monitor.backup_utils import group_config_console_rows

    rows = [
        _row("sr-bup", "OK", delivery="nas-final", received="2026-05-31 05:00:00"),
        _row("sr-pve5", "OK", received="2026-05-31 04:00:00"),
    ]
    grouped = group_config_console_rows(rows, expected_servers=["sr-pve5"])

    # финальная передача вынесена отдельно и НЕ входит в per-host серверы
    assert grouped["final"] is not None
    assert grouped["final"][2] == "nas-final"
    assert [s["host"] for s in grouped["servers"]] == ["sr-pve5"]
    assert grouped["missing"] == []


def test_no_expected_groups_by_fact():
    from extensions.backup_monitor.backup_utils import group_config_console_rows

    rows = [_row("sr-pve5", "OK"), _row("sr-pve6", "OK")]
    grouped = group_config_console_rows(rows, expected_servers=[])
    assert {s["host"] for s in grouped["servers"]} == {"sr-pve5", "sr-pve6"}
    assert all(not s["missing"] for s in grouped["servers"])
    assert grouped["missing"] == []
