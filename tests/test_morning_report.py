"""
Тесты рендеров утреннего/ручного отчёта (modules/morning_report.py):
формат N/N (%), сворачивание ВСЕХ секций (включая проблемные) в Telegram
(<blockquote expandable>) и Matrix (<details>), секция доступности
одной строкой.
"""

from __future__ import annotations

from datetime import datetime

from modules.morning_report import MorningReport


def _make_report(sections):
    return {
        "report_type": "Ручной отчёт",
        "app_version": "1.0.0",
        "collection_time": datetime(2026, 7, 2, 12, 14, 14),
        "sections": sections,
        "problem_areas": [s["title"] for s in sections if s["has_issues"]],
        "composition": "💾 Бэкапы Proxmox",
    }


def test_ratio_formatting():
    mr = MorningReport()
    assert mr._ratio(49, 49) == "49/49 (100%)"
    assert mr._ratio(8, 9) == "8/9 (88.9%)"
    assert mr._ratio(0, 1) == "0/1 (0%)"
    assert mr._ratio(0, 0) == "0/0 (—)"


def test_status_line():
    mr = MorningReport()
    assert mr._status_line("Серверы", 49, 49) == "🟢 Серверы: 49/49 (100%)"
    assert mr._status_line("Передач", 0, 1) == "🔴 Передач: 0/1 (0%)"
    assert mr._status_line("Файлов", 0, 0) == "⚪ Файлов: нет данных"


def test_availability_section_single_line_when_ok():
    mr = MorningReport()
    status = {"ok": [{"name": f"s{i}", "ip": f"10.0.0.{i}", "type": "lan"} for i in range(3)], "failed": []}
    lines, has_issues = mr._availability_section(status)
    assert lines == ["🟢 Серверы: 3/3 (100%)"]
    assert has_issues is False


def test_availability_section_lists_failed_servers():
    mr = MorningReport()
    status = {
        "ok": [{"name": "s1", "ip": "10.0.0.1", "type": "lan"}],
        "failed": [{"name": "s2", "ip": "10.0.0.2", "type": "wan"}],
    }
    lines, has_issues = mr._availability_section(status)
    assert lines[0] == "🔴 Серверы: 1/2 (50%)"
    assert has_issues is True
    assert any("WAN s2 (10.0.0.2)" in line for line in lines)


def test_render_plain_contains_sections_and_problems():
    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False},
            {"title": "📤 Передача бэкапов на NAS", "lines": ["🔴 Передач: 0/1 (0%)"], "has_issues": True},
        ]
    )
    text = mr.render_plain(report)
    assert "🔴 Ручной отчёт мониторинга" in text
    assert "⚠️ Требует внимания (1):" in text
    assert "• 📤 Передача бэкапов на NAS" in text
    assert "🟢 Серверы: 2/2 (100%)" in text


def test_render_telegram_html_collapses_all_sections():
    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False},
            {"title": "📤 Передача бэкапов на NAS", "lines": ["🔴 Передач: 0/1 (0%)"], "has_issues": True},
        ]
    )
    html_text = mr.render_telegram_html(report)
    # Обе секции — и проблемная, и без проблем — свёрнуты в expandable blockquote.
    assert "<blockquote expandable>🟢 Серверы: 2/2 (100%)</blockquote>" in html_text
    assert "<blockquote expandable>🔴 Передач: 0/1 (0%)</blockquote>" in html_text


def test_render_matrix_html_uses_details_for_all_sections():
    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False},
            {"title": "📤 Передача бэкапов на NAS", "lines": ["🔴 Передач: 0/1 (0%)"], "has_issues": True},
        ]
    )
    html_text = mr.render_matrix_html(report)
    assert "<details><summary>🟢 <strong>🖥 Доступность серверов</strong></summary>" in html_text
    assert "<details><summary>🔴 <strong>📤 Передача бэкапов на NAS</strong></summary>" in html_text
    assert "🔴 Передач: 0/1 (0%)" in html_text


def test_render_escapes_html_in_data():
    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🔴 <script> s1 (10.0.0.1)"], "has_issues": True},
        ]
    )
    html_text = mr.render_telegram_html(report)
    assert "<script>" not in html_text
    assert "&lt;script&gt;" in html_text


def test_snapshot_transfer_section_keeps_only_aggregate(monkeypatch):
    """«Передачи снэпшотов»: только общая строка, без деталей по хостам."""
    import sqlite3

    from core.config_manager import config_manager as settings_manager

    mr = MorningReport()

    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE snapshot_transfers "
        "(id INTEGER PRIMARY KEY, host_name TEXT, status TEXT, received_at TEXT)"
    )
    conn.execute(
        "INSERT INTO snapshot_transfers (host_name, status, received_at) "
        "VALUES ('host-a', 'SUCCESS', datetime('now'))"
    )
    conn.execute(
        "INSERT INTO snapshot_transfers (host_name, status, received_at) "
        "VALUES ('host-b', 'ERROR', datetime('now'))"
    )
    conn.commit()

    monkeypatch.setattr(
        mr,
        "_zfs_db_and_allowed",
        lambda: (":memory:", set()),
    )
    monkeypatch.setattr(sqlite3, "connect", lambda *_a, **_k: conn)
    monkeypatch.setattr(
        settings_manager,
        "get_setting",
        lambda key, default=None, **_k: (
            {"host-a": {"enabled": True}, "host-b": {"enabled": True}}
            if key == "SNAPSHOT_TRANSFER_HOSTS"
            else default
        ),
    )

    lines, has_issues = mr.get_snapshot_transfer_for_report()
    assert lines == ["🔴 Хостов: 1/2 (50%)"]
    assert has_issues is True


def test_stock_expected_files_saved_via_handle_setting_value(monkeypatch):
    """Регрессия: ввод «Ожидаемое кол-во файлов» (Остатки 1С) не сохранялся.

    Причина: флаг `stock_set_expected_files` проверялся только в
    `extensions/backup_monitor/bot_handler.py` (backup_host_settings_input_handler),
    а весь текстовый ввод бота сначала перехватывает `handle_setting_value`
    (bot/handlers/settings_handlers/settings_value.py) — они регистрируются в
    одной group=0 диспетчера python-telegram-bot, и до второго обработчика
    дело не доходит. Флаг теперь проверяется прямо в handle_setting_value.
    """
    from types import SimpleNamespace
    from unittest.mock import Mock

    import extensions.backup_monitor.backup_handlers as backup_handlers
    from bot.handlers.settings_handlers.settings_value import handle_setting_value
    from extensions.backup_monitor.backup_utils import get_stock_load_expected_files

    # Тестовые заглушки telegram.* (см. tests/conftest.py) не принимают позиционные
    # аргументы конструктора — подменяем клавиатуру-хелперы no-op'ами, поскольку
    # содержимое UI-ответа для этого теста не важно.
    monkeypatch.setattr(backup_handlers, "InlineKeyboardButton", lambda *a, **k: None)
    monkeypatch.setattr(backup_handlers, "InlineKeyboardMarkup", lambda *a, **k: None)

    update = SimpleNamespace(message=SimpleNamespace(text="7", reply_text=Mock()))
    context = SimpleNamespace(user_data={"stock_set_expected_files": True})

    handle_setting_value(update, context)

    assert "stock_set_expected_files" not in context.user_data
    assert get_stock_load_expected_files() == 7
    update.message.reply_text.assert_called_once()


def test_render_plain_all_ok_summary():
    mr = MorningReport()
    report = _make_report(
        [{"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False}]
    )
    text = mr.render_plain(report)
    assert "✅ Всё в норме" in text
    assert "Требует внимания" not in text
