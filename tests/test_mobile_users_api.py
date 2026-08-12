"""
Контракт HTTP-API многопользовательского режима для Android-клиента.

Имена полей здесь — часть контракта: их разбирают Moshi-модели
`android-client/.../api/ApiModels.kt` (`RegistryUser`, `UserPreferences`,
`MeCatalog`, `SettingsReportData`). Переименование поля на сервере молча
ломает приложение, поэтому тест фиксирует именно ключи JSON.

Flask в dev-зависимостях CI нет — при его отсутствии тест пропускается.
"""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("flask", reason="Веб-интерфейс требует Flask")

_config_module = importlib.import_module("core.config_manager")


@pytest.fixture()
def api(tmp_path, monkeypatch):
    """Тест-клиент веб-интерфейса на отдельной временной БД."""
    manager = _config_module.ConfigManager(db_path=str(tmp_path / "settings.db"))
    monkeypatch.setattr(_config_module, "config_manager", manager)

    from core import users as users_module

    registry = users_module.UserRegistry()
    registry._bootstrap_done = True
    registry.ensure_schema()
    monkeypatch.setattr(users_module, "user_registry", registry)

    web = importlib.import_module("extensions.web_interface")
    monkeypatch.setattr(web, "_MOBILE_STATIC_TOKEN", "test-token")

    return web, registry, web.app.test_client()


def _auth(token: str = "test-token") -> dict:
    return {"Authorization": f"Bearer {token}"}


def _device_token(web, subject: str, device_id: str) -> str:
    token, _expires_at, _mask = web._issue_persistent_mobile_token(subject, device_id=device_id)
    return token


def test_me_returns_catalog_for_unlinked_device(api):
    """Непривязанное устройство: user = null, справочники всё равно есть."""
    _web, _registry, client = api

    payload = client.get("/v1/me", headers=_auth()).get_json()

    assert payload["user"] is None
    catalog = payload["catalog"]
    assert "critical" in catalog["alert_levels"]
    category_ids = [item["id"] for item in catalog["alert_categories"]]
    assert "availability" in category_ids
    assert all({"id", "label"} <= set(item) for item in catalog["alert_categories"])


def test_me_resolves_user_by_device_id(api):
    """Устройство опознаётся по device_id токена — ключевой путь Android."""
    web, registry, client = api
    ivan = registry.create_user("ivan", display_name="Иван")
    registry.link_channel(int(ivan["id"]), "mobile", "dev-abc", title="Android Pixel")

    token = _device_token(web, "android-dev-abc", "dev-abc")
    payload = client.get("/v1/me", headers=_auth(token)).get_json()

    user = payload["user"]
    assert user["display_name"] == "Иван"
    assert {"id", "username", "display_name", "role", "enabled", "channels", "preferences"} <= set(
        user
    )
    assert user["channels"][0]["type"] == "mobile"
    assert user["channels"][0]["ref"] == "dev-abc"
    assert {"REPORTS_ENABLED", "ALERTS_ENABLED", "ALERT_LEVELS", "ALERT_CATEGORIES"} <= set(
        user["preferences"]
    )


def test_patch_me_notifications_applies_single_keys(api):
    """Приложение шлёт только изменённый ключ — остальные не трогаются."""
    web, registry, client = api
    ivan = registry.create_user("ivan", display_name="Иван")
    registry.link_channel(int(ivan["id"]), "mobile", "dev-abc")
    token = _device_token(web, "android-dev-abc", "dev-abc")

    response = client.patch(
        "/v1/me/notifications", headers=_auth(token), json={"REPORTS_ENABLED": False}
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["applied"] == ["REPORTS_ENABLED"]
    assert body["user"]["preferences"]["REPORTS_ENABLED"] is False
    # Не переданные ключи остались прежними.
    assert body["user"]["preferences"]["ALERTS_ENABLED"] is True

    levels = client.patch(
        "/v1/me/notifications", headers=_auth(token), json={"ALERT_LEVELS": ["critical"]}
    ).get_json()
    assert levels["user"]["preferences"]["ALERT_LEVELS"] == ["critical"]

    assert registry.wants_report(int(ivan["id"])) is False
    assert registry.wants_alert(int(ivan["id"]), "info") is False
    assert registry.wants_alert(int(ivan["id"]), "critical") is True


def test_patch_me_notifications_rejects_collection_settings(api):
    """Настройки сбора данных персонализировать нельзя и через API."""
    web, registry, client = api
    ivan = registry.create_user("ivan")
    registry.link_channel(int(ivan["id"]), "mobile", "dev-abc")
    token = _device_token(web, "android-dev-abc", "dev-abc")

    response = client.patch(
        "/v1/me/notifications", headers=_auth(token), json={"CHECK_INTERVAL": 5}
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_FAILED"


def test_patch_me_notifications_without_user(api):
    """Непривязанному устройству нечего персонализировать."""
    _web, _registry, client = api

    response = client.patch(
        "/v1/me/notifications", headers=_auth(), json={"REPORTS_ENABLED": False}
    )

    assert response.status_code == 404


def test_users_list_and_device_linking(api):
    """Список пользователей и привязка устройства из приложения."""
    web, registry, client = api
    registry.create_user("boss", display_name="Босс", role="admin")

    listed = client.get("/v1/users", headers=_auth()).get_json()
    assert listed["channel_types"] == ["telegram", "matrix", "mobile", "web"]
    assert [user["username"] for user in listed["users"]] == ["boss"]

    created = client.post(
        "/v1/users", headers=_auth(), json={"username": "ivan", "display_name": "Иван"}
    )
    assert created.status_code == 201
    user_id = created.get_json()["user"]["id"]

    linked = client.post(
        f"/v1/users/{user_id}/channels",
        headers=_auth(),
        json={"type": "mobile", "ref": "dev-abc", "title": "Android Pixel"},
    )
    assert linked.status_code == 200
    channels = linked.get_json()["user"]["channels"]
    assert (channels[0]["type"], channels[0]["ref"]) == ("mobile", "dev-abc")

    # После привязки устройство ходит уже от имени Ивана.
    token = _device_token(web, "android-dev-abc", "dev-abc")
    me = client.get("/v1/me", headers=_auth(token)).get_json()
    assert me["user"]["username"] == "ivan"


def test_report_settings_scope_switches_to_user(api):
    """`scope`/`user` в составе отчёта — их показывает экран приложения."""
    web, registry, client = api

    globals_payload = client.get("/v1/settings/report", headers=_auth()).get_json()["settings"]
    assert globals_payload["scope"] == "global"
    assert globals_payload["user"] is None

    ivan = registry.create_user("ivan", display_name="Иван")
    registry.link_channel(int(ivan["id"]), "mobile", "dev-abc")
    token = _device_token(web, "android-dev-abc", "dev-abc")

    personal = client.get("/v1/settings/report", headers=_auth(token)).get_json()["settings"]
    assert personal["scope"] == "user"
    assert personal["user"]["display_name"] == "Иван"

    updated = client.patch(
        "/v1/settings/report", headers=_auth(token), json={"report_extensions": ["zfs_monitor"]}
    ).get_json()["settings"]
    assert updated["report_extensions"] == ["zfs_monitor"]

    # Общесистемный состав остался прежним — личный выбор его не переписал.
    from lib.report_settings import get_report_extensions

    assert get_report_extensions(use_cache=False) != ["zfs_monitor"]
