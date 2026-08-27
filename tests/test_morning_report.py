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


def test_render_telegram_html_hides_all_section_bodies_by_default():
    """Telegram: в тексте только заголовки секций; подробностей нет вовсе.

    Telegram сворачивает <blockquote expandable> лишь при контенте длиннее
    ~3 строк — короткие секции показывались целиком. Поэтому тела секций
    из текста убраны полностью (разворачиваются кнопками секций).
    """
    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False},
            {"title": "📤 Передача бэкапов на NAS", "lines": ["🔴 Передач: 0/1 (0%)"], "has_issues": True},
        ]
    )
    html_text = mr.render_telegram_html(report)
    # Заголовки секций с флагами на месте.
    assert "🟢 <b>🖥 Доступность серверов</b>" in html_text
    assert "🔴 <b>📤 Передача бэкапов на NAS</b>" in html_text
    # А содержимое секций в тексте отсутствует.
    assert "Серверы: 2/2 (100%)" not in html_text
    assert "Передач: 0/1 (0%)" not in html_text
    assert "blockquote" not in html_text


def test_render_telegram_html_expands_sections_by_mask():
    """Кнопка секции разворачивает её тело (битовая маска expanded_mask)."""
    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False},
            {"title": "📤 Передача бэкапов на NAS", "lines": ["🔴 Передач: 0/1 (0%)"], "has_issues": True},
        ]
    )
    # Раскрыта только вторая секция (бит 1).
    html_text = mr.render_telegram_html(report, expanded_mask=0b10)
    assert "Серверы: 2/2 (100%)" not in html_text
    assert "<blockquote>🔴 Передач: 0/1 (0%)</blockquote>" in html_text
    # Раскрыты обе.
    html_text = mr.render_telegram_html(report, expanded_mask=0b11)
    assert "<blockquote>🟢 Серверы: 2/2 (100%)</blockquote>" in html_text
    assert "<blockquote>🔴 Передач: 0/1 (0%)</blockquote>" in html_text


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
    html_text = mr.render_telegram_html(report, expanded_mask=0b1)
    assert "<script>" not in html_text
    assert "&lt;script&gt;" in html_text


def test_report_registry_roundtrip_and_eviction():
    """Реестр payload'ов: get после register; вытеснение старых записей."""
    import modules.morning_report as mrmod

    payload = {"sections": [{"title": "t", "has_issues": False, "lines": ["x"]}]}
    report_id = mrmod.register_report_payload(payload)
    assert mrmod.get_report_payload(report_id) is payload

    # Реестр ограничен: после LIMIT новых записей старая вытесняется.
    for _ in range(mrmod._REPORT_REGISTRY_LIMIT):
        mrmod.register_report_payload({"sections": []})
    assert mrmod.get_report_payload(report_id) is None


def test_build_report_keyboard_buttons(monkeypatch):
    """Клавиатура отчёта: кнопка на секцию (2 в ряд) + «развернуть всё»."""
    import telegram

    import modules.morning_report as mrmod

    monkeypatch.setattr(telegram, "InlineKeyboardButton", lambda text, callback_data: (text, callback_data))
    monkeypatch.setattr(telegram, "InlineKeyboardMarkup", lambda rows: rows)

    payload = {
        "sections": [
            {"title": "🖥 Доступность серверов", "has_issues": False, "lines": ["a"]},
            {"title": "💾 Бэкапы Proxmox (за 24ч)", "has_issues": False, "lines": ["b"]},
            {"title": "📤 Передача бэкапов на NAS (за 24ч)", "has_issues": True, "lines": ["c"]},
        ]
    }
    rows = mrmod.build_report_keyboard("rid1", payload, expanded_mask=0b001)

    flat = [button for row in rows for button in row]
    labels = [text for text, _ in flat]
    callbacks = [data for _, data in flat]

    # Раскрытая секция — «▾», свёрнутые — «▸»; суффикс «(за 24ч)» убран.
    assert labels[0].startswith("▾ ")
    assert labels[1] == "▸ 💾 Бэкапы Proxmox"
    assert "(за 24ч)" not in labels[1]
    # callback_data несёт report_id, индекс секции и текущую маску.
    assert callbacks[0] == "mrs|rid1|0|1"
    assert callbacks[1] == "mrs|rid1|1|1"
    assert callbacks[2] == "mrs|rid1|2|1"
    # Служебный ряд: маска не полная и не нулевая — обе кнопки.
    assert "mrs|rid1|a|1" in callbacks
    assert "mrs|rid1|n|1" in callbacks
    # Последний ряд — «Закрыть» на общем для бота callback_data="close".
    assert rows[-1] == [("✖️ Закрыть", "close")]


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


def test_report_to_json_payload_is_json_safe_and_matches_sections():
    """Структурированный payload для мобильного API (Android): JSON-safe,
    те же секции title/has_issues/lines, что рендерятся в Telegram/Matrix.
    """
    import json

    mr = MorningReport()
    report = _make_report(
        [
            {"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False},
            {"title": "📤 Передача бэкапов на NAS", "lines": ["🔴 Передач: 0/1 (0%)"], "has_issues": True},
        ]
    )
    payload = mr._report_to_json_payload(report)

    # Сериализуется без ошибок (datetime уже приведён к строке).
    encoded = json.dumps(payload, ensure_ascii=False)
    assert isinstance(encoded, str)

    assert payload["report_type"] == "Ручной отчёт"
    assert payload["app_version"] == "1.0.0"
    assert payload["generated_at"] == "2026-07-02T12:14:14"
    assert payload["has_issues"] is True
    assert payload["problem_areas"] == ["📤 Передача бэкапов на NAS"]
    assert payload["composition"] == "💾 Бэкапы Proxmox"
    assert payload["sections"] == [
        {"title": "🖥 Доступность серверов", "has_issues": False, "lines": ["🟢 Серверы: 2/2 (100%)"]},
        {"title": "📤 Передача бэкапов на NAS", "has_issues": True, "lines": ["🔴 Передач: 0/1 (0%)"]},
    ]


def test_report_to_json_payload_none_when_no_report():
    mr = MorningReport()
    assert mr._report_to_json_payload(None) is None


def test_force_report_formats_includes_payload():
    mr = MorningReport()
    formats = mr.force_report_formats()
    assert set(formats.keys()) == {"plain", "telegram_html", "matrix_html", "payload"}
    assert isinstance(formats["payload"], dict)
    assert "sections" in formats["payload"]


def test_backup_wizard_flags_delegated_from_handle_setting_value(monkeypatch):
    """Регрессия: мастера ввода backup_monitor не сохраняли значения.

    Флаги cc_add_server / cc_add_pattern / nas_add_pattern /
    backup_add_proxmox_host / backup_edit_proxmox_host_name проверялись
    только в backup_host_settings_input_handler
    (extensions/backup_monitor/bot_handler.py), который никогда не
    вызывается: весь текстовый ввод первым перехватывает
    handle_setting_value (та же group=0 диспетчера python-telegram-bot).
    Теперь эти флаги делегируются оригинальному обработчику.
    """
    from types import SimpleNamespace
    from unittest.mock import Mock

    import extensions.backup_monitor.backup_handlers as backup_handlers
    import extensions.backup_monitor.bot_handler as bot_handler
    from bot.handlers.settings_handlers.settings_value import handle_setting_value
    from extensions.backup_monitor.backup_utils import get_config_console_servers

    # Тестовые заглушки telegram.* не принимают аргументы конструктора.
    monkeypatch.setattr(backup_handlers, "InlineKeyboardButton", lambda *a, **k: None)
    monkeypatch.setattr(backup_handlers, "InlineKeyboardMarkup", lambda *a, **k: None)
    monkeypatch.setattr(bot_handler, "InlineKeyboardButton", lambda *a, **k: None)
    monkeypatch.setattr(bot_handler, "InlineKeyboardMarkup", lambda *a, **k: None)

    # cc_add_server: сервер попадает в CONFIG_CONSOLE_SERVERS.
    update = SimpleNamespace(message=SimpleNamespace(text="sr-test-host", reply_text=Mock()))
    context = SimpleNamespace(user_data={"cc_add_server": True})
    handle_setting_value(update, context)
    assert "cc_add_server" not in context.user_data
    assert "sr-test-host" in get_config_console_servers()
    update.message.reply_text.assert_called()

    # backup_add_proxmox_host: хост появляется в PROXMOX_HOSTS.
    update2 = SimpleNamespace(message=SimpleNamespace(text="pve-test-99", reply_text=Mock()))
    context2 = SimpleNamespace(user_data={"backup_add_proxmox_host": True})
    handle_setting_value(update2, context2)
    assert "backup_add_proxmox_host" not in context2.user_data
    hosts = bot_handler.BackupMonitorBot().get_proxmox_hosts_config()
    assert "pve-test-99" in hosts
    update2.message.reply_text.assert_called()


def test_render_plain_all_ok_summary():
    mr = MorningReport()
    report = _make_report(
        [{"title": "🖥 Доступность серверов", "lines": ["🟢 Серверы: 2/2 (100%)"], "has_issues": False}]
    )
    text = mr.render_plain(report)
    assert "✅ Всё в норме" in text
    assert "Требует внимания" not in text
