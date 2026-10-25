"""
Контракт `GET /v1/mobile/version` и `GET /v1/mobile/branches`.

Ключи JSON разбирают Moshi-модели `MobileVersionResponse` / `MobileBranch`
в `android-client/.../api/ApiModels.kt`, поэтому тест фиксирует их явно.
Сеть не трогается: резолвер GitHub подменяется.

Flask в dev-зависимостях CI нет — при его отсутствии тест пропускается.
"""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("flask", reason="Веб-интерфейс требует Flask")

from core.android_release_channels import ChannelRelease  # noqa: E402

_AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture()
def web(monkeypatch):
    module = importlib.import_module("extensions.web_interface")
    monkeypatch.setattr(module, "_MOBILE_STATIC_TOKEN", "test-token")
    return module


def _github(monkeypatch, web, releases):
    monkeypatch.setattr(web, "_resolve_github_channel_releases", lambda: releases)


def test_version_reports_channel_release_and_capabilities(web, monkeypatch):
    _github(
        monkeypatch,
        web,
        {
            "stable": ChannelRelease("9.0.0", "https://dl/ComDone-9.0.0.apk"),
            "beta": ChannelRelease("9.0.3", "https://dl/ComDone-9.0.3-beta.apk"),
        },
    )
    client = web.app.test_client()

    beta = client.get(
        "/v1/mobile/version?current_version=9.0.0&branch=develop", headers=_AUTH
    ).get_json()
    assert beta["latest_version"] == "9.0.3"
    assert beta["apk_download_url"].endswith("ComDone-9.0.3-beta.apk")
    assert beta["branch"] == "develop"
    assert {"server_version", "api_baseline", "capabilities"} <= set(beta)
    assert isinstance(beta["capabilities"], list)

    # Старый клиент без `branch` получает стабильный канал, а не версию сервера.
    default = client.get("/v1/mobile/version?current_version=8.67.1", headers=_AUTH).get_json()
    assert default["latest_version"] == "9.0.0"
    assert default["apk_download_url"].endswith("ComDone-9.0.0.apk")


def test_version_falls_back_to_settings_without_github(web, monkeypatch):
    _github(monkeypatch, web, {})
    from config.settings import ANDROID_LATEST_VERSION

    payload = (
        web.app.test_client()
        .get("/v1/mobile/version?branch=develop", headers=_AUTH)
        .get_json()
    )
    assert payload["latest_version"] == ANDROID_LATEST_VERSION
    assert payload["apk_download_url"].endswith(f"ComDone-{ANDROID_LATEST_VERSION}-beta.apk")


def test_branches_keep_stable_ids_and_default_to_stable(web, monkeypatch):
    _github(monkeypatch, web, {})
    payload = web.app.test_client().get("/v1/mobile/branches", headers=_AUTH).get_json()

    names = [b["name"] for b in payload["branches"]]
    # Идентификаторы сохранены у установленных клиентов — не переименовывать.
    assert names == ["main", "develop"]
    assert payload["default_branch"] == "main"
    for branch in payload["branches"]:
        assert {"name", "title", "latest_version", "apk_download_url", "is_default"} <= set(branch)
