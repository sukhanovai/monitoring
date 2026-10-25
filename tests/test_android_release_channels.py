"""
Каналы обновления Android-клиента по GitHub Releases
(core/android_release_channels.py).

Ключевое требование: ответ не зависит от ветки сервера — stable берётся
из последнего обычного релиза, beta — из самой новой сборки вообще.
"""

from __future__ import annotations

from core.android_release_channels import (
    CHANNEL_BETA,
    CHANNEL_STABLE,
    ReleaseChannelResolver,
    parse_tag_version,
    select_channel_releases,
)


def _release(tag, *assets, prerelease=False, draft=False):
    return {
        "tag_name": tag,
        "prerelease": prerelease,
        "draft": draft,
        "assets": [
            {"name": name, "browser_download_url": f"https://dl/{tag}/{name}"} for name in assets
        ],
    }


def test_parse_tag_version_accepts_known_tag_shapes():
    assert parse_tag_version("v9.0.0") == (9, 0, 0)
    assert parse_tag_version("v9.0.1-beta") == (9, 0, 1)
    assert parse_tag_version("v8.67.1-develop") == (8, 67, 1)
    assert parse_tag_version("2.2.1") == (2, 2, 1)
    assert parse_tag_version("release-1") is None


def test_stable_and_beta_are_selected_independently():
    releases = [
        _release("v9.0.2-beta", "ComDone-9.0.2-beta.apk", prerelease=True),
        _release("v9.0.0", "ComDone-9.0.0.apk", "ComDone.apk"),
        _release(
            "v8.67.1-develop",
            "monitoring-android-8.67.1-develop-compactOps-debug.apk",
            prerelease=True,
        ),
    ]
    result = select_channel_releases(releases)
    assert result[CHANNEL_STABLE].version == "9.0.0"
    # Версионное имя предпочтительнее постоянного ComDone.apk.
    assert result[CHANNEL_STABLE].apk_download_url.endswith("/ComDone-9.0.0.apk")
    assert result[CHANNEL_BETA].version == "9.0.2"


def test_beta_never_lags_behind_stable():
    releases = [
        _release("v9.0.1-beta", "ComDone-9.0.1-beta.apk", prerelease=True),
        _release("v9.1.0", "ComDone-9.1.0.apk"),
    ]
    result = select_channel_releases(releases)
    assert result[CHANNEL_BETA].version == "9.1.0"


def test_releases_without_apk_and_drafts_are_ignored():
    releases = [
        _release("v9.5.0", "ComDone-9.5.0.apk", draft=True),
        _release("v8.0.0", "source.zip"),
        _release("v8.67.1-develop", "monitoring-android-8.67.1.apk", prerelease=True),
    ]
    result = select_channel_releases(releases)
    assert CHANNEL_STABLE not in result
    assert result[CHANNEL_BETA].version == "8.67.1"


def test_resolver_caches_success_and_survives_failures():
    calls = []
    now = [0.0]

    def fetcher(repo, token):
        calls.append(repo)
        if len(calls) == 2:
            raise OSError("network down")
        return [_release("v9.0.0", "ComDone-9.0.0.apk")]

    resolver = ReleaseChannelResolver(fetcher=fetcher, clock=lambda: now[0])
    assert resolver.resolve("o/r")[CHANNEL_STABLE].version == "9.0.0"
    assert resolver.resolve("o/r")[CHANNEL_STABLE].version == "9.0.0"
    assert len(calls) == 1  # из кэша

    now[0] += 601  # кэш истёк, GitHub недоступен → None, вызывающий берёт fallback
    assert resolver.resolve("o/r") is None
    now[0] += 60
    assert resolver.resolve("o/r") is None
    assert len(calls) == 2  # ошибка тоже кэшируется, без шторма запросов

    now[0] += 301
    assert resolver.resolve("o/r")[CHANNEL_STABLE].version == "9.0.0"


def test_resolver_reports_reachable_github_without_channel_build():
    """GitHub ответил, но стабильной сборки нет — {} (а не None): fallback не нужен."""
    resolver = ReleaseChannelResolver(
        fetcher=lambda repo, token: [
            _release("v9.0.0-beta", "ComDone-9.0.0-beta.apk", prerelease=True),
            _release("v8.0.0", "source.zip"),
        ]
    )
    result = resolver.resolve("o/r")
    assert result is not None
    assert CHANNEL_STABLE not in result
    assert result[CHANNEL_BETA].version == "9.0.0"
