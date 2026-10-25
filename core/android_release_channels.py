"""
/core/android_release_channels.py
Server Monitoring System v9.0.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Android update channels (stable / beta) resolved from GitHub Releases.
Система мониторинга серверов
Версия: 9.0.0
Автор: Александр Суханов (c)
Лицензия: MIT
Каналы обновления Android-клиента ComDone, вычисляемые по GitHub Releases.

Зачем: раньше «последняя версия» бралась из config/settings.py того
сервера, который отвечает клиенту. Сервер на `main` не знал о свежей бете,
а сервер на `develop` — о последнем стабильном релизе. Теперь оба канала
определяются по реальным релизам репозитория, поэтому ответ не зависит от
того, на какой ветке развёрнут сервер:

- stable — последний обычный (не prerelease) релиз с APK;
- beta   — самая новая сборка вообще (prerelease или обычный релиз), чтобы
  бета-пользователь никогда не застревал ниже стабильной версии.

Сеть не обязательна: при недоступности GitHub вызывающий код использует
статический fallback из config/settings.py.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CHANNEL_STABLE = "stable"
CHANNEL_BETA = "beta"

# Версия из тега: `v9.0.0`, `v9.0.1-beta`, `v8.67.1-develop`, `2.2.1`.
_TAG_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")
# Предпочтительное имя APK начиная с 9.0.0 (`ComDone-9.0.0.apk`,
# `ComDone-9.0.1-beta.apk`). Старые релизы содержат `monitoring-android-*.apk`
# — они тоже принимаются, чтобы канал работал и до первой сборки 9.x.
_PREFERRED_APK_PREFIX = "ComDone-"

_SUCCESS_TTL_SECONDS = 3600
_FAILURE_TTL_SECONDS = 300
_HTTP_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class ChannelRelease:
    """Последняя сборка канала: версия X.Y.Z и прямая ссылка на APK."""

    version: str
    apk_download_url: str


def parse_tag_version(tag: str) -> tuple[int, int, int] | None:
    match = _TAG_VERSION_RE.match(str(tag or "").strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _pick_apk_url(assets: Any) -> str | None:
    apks = [
        a
        for a in (assets or [])
        if isinstance(a, dict)
        and str(a.get("name") or "").lower().endswith(".apk")
        and a.get("browser_download_url")
    ]
    if not apks:
        return None
    # Версионный `ComDone-X.Y.Z.apk` важнее постоянного `ComDone.apk`:
    # имя файла в загрузках сразу показывает версию.
    apks.sort(
        key=lambda a: (
            not str(a["name"]).startswith(_PREFERRED_APK_PREFIX),
            str(a["name"]) == "ComDone.apk",
        )
    )
    return str(apks[0]["browser_download_url"])


def select_channel_releases(releases: Any) -> dict[str, ChannelRelease]:
    """Чистая функция: из ответа GitHub `/releases` выбирает сборки каналов."""
    best: dict[str, tuple[tuple[int, int, int], ChannelRelease]] = {}
    for release in releases or []:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        semver = parse_tag_version(str(release.get("tag_name") or ""))
        url = _pick_apk_url(release.get("assets"))
        if semver is None or url is None:
            continue
        candidate = ChannelRelease(version="%d.%d.%d" % semver, apk_download_url=url)
        channels = [CHANNEL_BETA]
        if not release.get("prerelease"):
            channels.append(CHANNEL_STABLE)
        for channel in channels:
            current = best.get(channel)
            if current is None or semver > current[0]:
                best[channel] = (semver, candidate)
    return {channel: item[1] for channel, item in best.items()}


def _fetch_releases_from_github(repo: str, token: str = "") -> Any:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases?per_page=50",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ComDone-server",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


class ReleaseChannelResolver:
    """Кэширующий резолвер каналов. Потокобезопасен.

    Успешный ответ кэшируется на час (лимит GitHub без токена — 60 запросов
    в час с IP), ошибка — на 5 минут, чтобы не тормозить каждый запрос
    клиента таймаутом при недоступном GitHub.
    """

    def __init__(
        self,
        fetcher: Callable[[str, str], Any] = _fetch_releases_from_github,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetcher = fetcher
        self._clock = clock
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, dict[str, ChannelRelease]]] = {}

    def resolve(self, repo: str, token: str = "") -> dict[str, ChannelRelease]:
        now = self._clock()
        with self._lock:
            cached = self._cache.get(repo)
            if cached and cached[0] > now:
                return cached[1]
            try:
                result = select_channel_releases(self._fetcher(repo, token))
                ttl = _SUCCESS_TTL_SECONDS if result else _FAILURE_TTL_SECONDS
            except Exception:  # noqa: BLE001 — сеть/JSON/HTTP: работаем на fallback
                result = {}
                ttl = _FAILURE_TTL_SECONDS
            self._cache[repo] = (now + ttl, result)
            return result


default_resolver = ReleaseChannelResolver()
