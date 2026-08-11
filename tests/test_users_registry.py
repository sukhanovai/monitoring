"""
Тесты многопользовательского режима (`core/users.py`):

* реестр пользователей и их каналов обмена;
* персональные настройки (состав отчёта, подписки на оповещения);
* фильтрация доставки: уровень, категория, личные тихие часы;
* общие настройки сбора данных персонализации не подлежат.
"""

from __future__ import annotations

import importlib
from datetime import datetime

import pytest

# `core.config_manager` как атрибут пакета `core` — это singleton-объект
# (в `core/__init__.py` есть `from .config_manager import config_manager`),
# поэтому модуль берём через importlib, а не через getattr по строке.
_config_module = importlib.import_module("core.config_manager")

from core.users import (
    CHANNEL_MATRIX,
    CHANNEL_MOBILE,
    CHANNEL_TELEGRAM,
    PREF_ALERT_CATEGORIES,
    PREF_ALERT_LEVELS,
    PREF_ALERTS_ENABLED,
    PREF_QUIET_END,
    PREF_QUIET_HOURS_ENABLED,
    PREF_QUIET_START,
    PREF_REPORT_EXTENSIONS,
    PREF_REPORTS_ENABLED,
    ROLE_ADMIN,
    ROLE_USER,
    UserRegistry,
    UserRegistryError,
    alert_categories,
    resolve_mobile_user,
)


@pytest.fixture()
def registry(tmp_path, monkeypatch):
    """Реестр на отдельной временной БД настроек."""
    manager = _config_module.ConfigManager(db_path=str(tmp_path / "settings.db"))
    monkeypatch.setattr(_config_module, "config_manager", manager)

    instance = UserRegistry()
    # Миграция из однопользовательских настроек в этих тестах не нужна:
    # сценарий bootstrap проверяется отдельным тестом.
    instance._bootstrap_done = True
    instance.ensure_schema()
    return instance


def _make_user(registry, username, **kwargs):
    return registry.create_user(username, **kwargs)


def test_create_user_and_resolve_by_channel(registry):
    user = _make_user(registry, "ivan", display_name="Иван")
    registry.link_channel(int(user["id"]), CHANNEL_TELEGRAM, "111")

    resolved = registry.resolve_user(CHANNEL_TELEGRAM, "111")
    assert resolved is not None
    assert resolved["username"] == "ivan"
    assert resolved["display_name"] == "Иван"
    assert registry.resolve_user(CHANNEL_TELEGRAM, "999") is None


def test_duplicate_username_rejected(registry):
    _make_user(registry, "ivan")
    with pytest.raises(UserRegistryError):
        _make_user(registry, "IVAN")


def test_channel_belongs_to_single_user(registry):
    first = _make_user(registry, "ivan")
    second = _make_user(registry, "petr")
    registry.link_channel(int(first["id"]), CHANNEL_TELEGRAM, "111")
    # Повторная привязка того же чата переносит его другому пользователю.
    registry.link_channel(int(second["id"]), CHANNEL_TELEGRAM, "111")

    resolved = registry.resolve_user(CHANNEL_TELEGRAM, "111")
    assert resolved["username"] == "petr"
    assert registry.list_channels(user_id=int(first["id"])) == []


def test_personal_report_composition_is_independent(registry):
    ivan = _make_user(registry, "ivan")
    petr = _make_user(registry, "petr")

    registry.set_preference(int(ivan["id"]), PREF_REPORT_EXTENSIONS, ["zfs_monitor"])
    registry.set_preference(int(petr["id"]), PREF_REPORT_EXTENSIONS, ["backup_monitor"])

    assert registry.get_preference(int(ivan["id"]), PREF_REPORT_EXTENSIONS) == ["zfs_monitor"]
    assert registry.get_preference(int(petr["id"]), PREF_REPORT_EXTENSIONS) == ["backup_monitor"]


def test_preference_falls_back_to_global_default(registry, monkeypatch):
    """Пользователь без личного выбора получает общесистемное значение."""
    _config_module.config_manager.set_setting(
        "REPORT_EXTENSIONS", ["mail_backup_monitor"], category="report", data_type="list"
    )
    user = _make_user(registry, "ivan")

    assert registry.get_preference(int(user["id"]), PREF_REPORT_EXTENSIONS) == [
        "mail_backup_monitor"
    ]

    # Личный выбор перекрывает общесистемный.
    registry.set_preference(int(user["id"]), PREF_REPORT_EXTENSIONS, ["zfs_monitor"])
    assert registry.get_preference(int(user["id"]), PREF_REPORT_EXTENSIONS) == ["zfs_monitor"]

    # Сброс возвращает к общесистемному.
    registry.reset_preference(int(user["id"]), PREF_REPORT_EXTENSIONS)
    assert registry.get_preference(int(user["id"]), PREF_REPORT_EXTENSIONS) == [
        "mail_backup_monitor"
    ]


def test_collection_settings_are_not_personalizable(registry):
    """Настройки сбора данных общие: персонализировать их нельзя."""
    user = _make_user(registry, "ivan")
    for key in ("CHECK_INTERVAL", "BACKUP_PATTERNS", "SERVER_TIMEOUTS"):
        with pytest.raises(UserRegistryError):
            registry.set_preference(int(user["id"]), key, 5)
        with pytest.raises(UserRegistryError):
            registry.get_preference(int(user["id"]), key)


def test_wants_alert_respects_levels_and_categories(registry):
    user = _make_user(registry, "ivan")
    user_id = int(user["id"])

    registry.set_preference(user_id, PREF_ALERT_LEVELS, ["critical"])
    assert registry.wants_alert(user_id, "critical") is True
    assert registry.wants_alert(user_id, "info") is False

    registry.set_preference(user_id, PREF_ALERT_LEVELS, ["critical", "info"])
    registry.set_preference(user_id, PREF_ALERT_CATEGORIES, ["availability"])
    assert registry.wants_alert(user_id, "info", category="availability") is True
    assert registry.wants_alert(user_id, "info", category="tls_cert_monitor") is False
    # Неизвестная категория (системное событие) проходит всегда.
    assert registry.wants_alert(user_id, "info", category="something-new") is True

    registry.set_preference(user_id, PREF_ALERTS_ENABLED, False)
    assert registry.wants_alert(user_id, "critical") is False


def test_wants_alert_quiet_hours(registry):
    user = _make_user(registry, "ivan")
    user_id = int(user["id"])
    registry.set_preference(user_id, PREF_QUIET_HOURS_ENABLED, True)
    registry.set_preference(user_id, PREF_QUIET_START, 22)
    registry.set_preference(user_id, PREF_QUIET_END, 8)

    night = datetime(2026, 8, 10, 23, 30)
    day = datetime(2026, 8, 10, 12, 0)

    assert registry.wants_alert(user_id, "warning", now=night) is False
    assert registry.wants_alert(user_id, "warning", now=day) is True
    # Критические и принудительные проходят даже в тихие часы.
    assert registry.wants_alert(user_id, "critical", now=night) is True
    assert registry.wants_alert(user_id, "warning", force=True, now=night) is True


def test_quiet_hours_without_midnight_crossing(registry):
    assert UserRegistry._in_quiet_hours(9, 18, datetime(2026, 8, 10, 12, 0)) is True
    assert UserRegistry._in_quiet_hours(9, 18, datetime(2026, 8, 10, 20, 0)) is False
    assert UserRegistry._in_quiet_hours(0, 0, datetime(2026, 8, 10, 3, 0)) is False


def test_delivery_targets_filters_and_groups_channels(registry):
    ivan = _make_user(registry, "ivan")
    petr = _make_user(registry, "petr")
    no_channels = _make_user(registry, "empty")
    disabled = _make_user(registry, "off", enabled=False)

    registry.link_channel(int(ivan["id"]), CHANNEL_TELEGRAM, "111")
    registry.link_channel(int(ivan["id"]), CHANNEL_MATRIX, "!room:example.org")
    registry.link_channel(int(petr["id"]), CHANNEL_TELEGRAM, "222")
    registry.link_channel(int(disabled["id"]), CHANNEL_TELEGRAM, "333")
    registry.set_preference(int(petr["id"]), PREF_ALERT_CATEGORIES, ["resources"])

    targets = registry.delivery_targets(alert_type="info", category="availability")
    usernames = {target["user"]["username"] for target in targets}

    assert usernames == {"ivan"}
    assert targets[0]["telegram"] == ["111"]
    assert targets[0]["matrix"] == ["!room:example.org"]
    assert no_channels["username"] not in usernames


def test_report_recipients_respect_reports_flag(registry):
    ivan = _make_user(registry, "ivan")
    petr = _make_user(registry, "petr")
    registry.link_channel(int(ivan["id"]), CHANNEL_TELEGRAM, "111")
    registry.link_channel(int(petr["id"]), CHANNEL_TELEGRAM, "222")
    registry.set_preference(int(petr["id"]), PREF_REPORTS_ENABLED, False)

    targets = registry.delivery_targets(report=True, force=True)
    assert [target["user"]["username"] for target in targets] == ["ivan"]


def test_bootstrap_creates_admin_from_legacy_settings(tmp_path, monkeypatch):
    """Обновление с однопользовательской конфигурации никого не теряет."""
    manager = _config_module.ConfigManager(db_path=str(tmp_path / "settings.db"))
    monkeypatch.setattr(_config_module, "config_manager", manager)
    manager.set_setting("CHAT_IDS", ["111", "222"], category="telegram", data_type="list")
    manager.set_setting(
        "MATRIX_ROOM_ID", "!room:example.org", category="matrix", data_type="string"
    )
    manager.set_setting("REPORT_EXTENSIONS", ["zfs_monitor"], category="report", data_type="list")

    instance = UserRegistry()
    users = instance.list_users()

    assert [user["username"] for user in users] == ["admin"]
    admin = users[0]
    assert admin["role"] == ROLE_ADMIN

    channels = instance.list_channels(user_id=int(admin["id"]))
    refs = {(channel["channel_type"], channel["channel_ref"]) for channel in channels}
    assert (CHANNEL_TELEGRAM, "111") in refs
    assert (CHANNEL_TELEGRAM, "222") in refs
    assert (CHANNEL_MATRIX, "!room:example.org") in refs

    # Прежний состав отчёта стал личным составом администратора.
    assert instance.get_preference(int(admin["id"]), PREF_REPORT_EXTENSIONS) == ["zfs_monitor"]


def test_alert_categories_include_extensions():
    categories = alert_categories()
    assert "availability" in categories
    assert "resources" in categories
    assert "backup_monitor" in categories


def test_resolve_mobile_user_prefers_device(registry, monkeypatch):
    monkeypatch.setattr("core.users.user_registry", registry)
    ivan = _make_user(registry, "ivan")
    petr = _make_user(registry, "petr")
    registry.link_channel(int(ivan["id"]), CHANNEL_MOBILE, "admin")
    registry.link_channel(int(petr["id"]), CHANNEL_MOBILE, "device-42")

    assert resolve_mobile_user("admin")["username"] == "ivan"
    assert resolve_mobile_user("admin", "device-42")["username"] == "petr"


# ---------------------------------------------------------------------------
# Права на управление реестром: реестр нельзя «запереть» без администратора
# ---------------------------------------------------------------------------


def test_last_admin_cannot_be_demoted_disabled_or_deleted(registry):
    admin = _make_user(registry, "boss", role=ROLE_ADMIN)
    _make_user(registry, "ivan")
    admin_id = int(admin["id"])

    with pytest.raises(UserRegistryError):
        registry.update_user(admin_id, role=ROLE_USER)
    with pytest.raises(UserRegistryError):
        registry.update_user(admin_id, enabled=False)
    with pytest.raises(UserRegistryError):
        registry.delete_user(admin_id)

    assert registry.get_user(admin_id)["role"] == ROLE_ADMIN

    # Как только появился второй администратор — первого можно разжаловать.
    second = _make_user(registry, "boss2", role=ROLE_ADMIN)
    assert registry.update_user(admin_id, role=ROLE_USER)["role"] == ROLE_USER
    assert registry.count_admins() == 1
    assert int(second["id"]) != admin_id


def test_has_reachable_admin_requires_a_channel(registry):
    admin = _make_user(registry, "boss", role=ROLE_ADMIN)
    assert registry.has_reachable_admin() is False

    registry.link_channel(int(admin["id"]), CHANNEL_TELEGRAM, "111")
    assert registry.has_reachable_admin() is True
    assert registry.has_reachable_admin(CHANNEL_TELEGRAM) is True
    assert registry.has_reachable_admin(CHANNEL_MATRIX) is False


def test_can_manage_users_falls_back_when_no_admin_reachable(registry, monkeypatch):
    from core import users as users_module

    monkeypatch.setattr(users_module, "user_registry", registry)
    admin = _make_user(registry, "boss", role=ROLE_ADMIN)
    plain = _make_user(registry, "ivan")

    # Администратор без каналов недостижим — управление открыто всем,
    # иначе реестр остался бы запертым.
    assert users_module.can_manage_users(plain) is True

    registry.link_channel(int(admin["id"]), CHANNEL_TELEGRAM, "111")
    assert users_module.can_manage_users(plain) is False
    assert users_module.can_manage_users(admin) is True


def test_legacy_chat_keeps_admin_rights(registry, monkeypatch):
    """Чат из CHAT_IDS имел полный доступ до многопользовательского режима."""
    from core import users as users_module

    monkeypatch.setattr(users_module, "user_registry", registry)
    _config_module.config_manager.set_setting(
        "CHAT_IDS", ["111"], category="telegram", data_type="list"
    )

    admin = _make_user(registry, "boss", role=ROLE_ADMIN)
    registry.link_channel(int(admin["id"]), CHANNEL_TELEGRAM, "999")

    # Чат 111 отдали обычному пользователю — права на управление остаются,
    # потому что чат перечислен в общем CHAT_IDS.
    plain = _make_user(registry, "ivan")
    registry.link_channel(int(plain["id"]), CHANNEL_TELEGRAM, "111")

    assert users_module.is_admin_telegram_chat("111") is True
    # Чужой чат обычного пользователя прав не получает.
    registry.link_channel(int(plain["id"]), CHANNEL_TELEGRAM, "222")
    assert users_module.is_admin_telegram_chat("222") is False
    assert users_module.is_admin_telegram_chat("999") is True
