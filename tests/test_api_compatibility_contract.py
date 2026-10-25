"""
Контракт совместимости мобильного API (docs/contracts/api_compatibility.md).

Бета-приложение из `develop` должно работать со стабильным сервером из
`main`. Тест статически (без Flask и Android SDK) проверяет:

1. каждый эндпоинт, который вызывает Android-клиент (MonitoringApi.kt),
   либо входит в baseline 9.0.0, либо защищён меткой capability в
   ServerCapabilities.kt;
2. каждая такая метка объявлена сервером (core/api_capabilities.py);
3. сервер по-прежнему обслуживает весь baseline — API меняется только
   аддитивно, удалять/переименовывать эндпоинты нельзя.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.api_capabilities import API_BASELINE, API_CAPABILITIES

ROOT = Path(__file__).resolve().parents[1]
API_KT = ROOT / "android-client/app/src/main/java/ru/monitoring/mobile/api/MonitoringApi.kt"
CAPS_KT = ROOT / "android-client/app/src/main/java/ru/monitoring/mobile/api/ServerCapabilities.kt"
BASELINE = ROOT / f"docs/contracts/api_baseline_{API_BASELINE}.txt"
SERVER_SOURCES = sorted((ROOT / "extensions").rglob("*.py"))

_CLIENT_RE = re.compile(r'@(GET|POST|PATCH|DELETE|PUT)\("([^"?]+)')
_ROUTE_RE = re.compile(r'@app\.route\("/?(v1/[^"]+)"(?:\s*,\s*methods=\[([^\]]*)\])?')
_PARAM_RE = re.compile(r"\{[^}]+\}|<[^>]+>")


def _norm(path: str) -> str:
    return _PARAM_RE.sub("{}", path.strip().lstrip("/"))


def _client_endpoints() -> set[str]:
    return {f"{m} {_norm(p)}" for m, p in _CLIENT_RE.findall(API_KT.read_text(encoding="utf-8"))}


def _baseline() -> set[str]:
    lines = BASELINE.read_text(encoding="utf-8").splitlines()
    result = set()
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            method, path = line.split(maxsplit=1)
            result.add(f"{method} {_norm(path)}")
    return result


def _guarded_endpoints() -> dict[str, str]:
    text = CAPS_KT.read_text(encoding="utf-8")
    pairs = re.findall(r'"((?:GET|POST|PATCH|DELETE|PUT) [^"]+)"\s+to\s+"([^"]+)"', text)
    return {f"{k.split()[0]} {_norm(k.split(maxsplit=1)[1])}": v for k, v in pairs}


def _server_endpoints() -> set[str]:
    result = set()
    for source in SERVER_SOURCES:
        for path, methods in _ROUTE_RE.findall(source.read_text(encoding="utf-8")):
            for method in re.findall(r"[A-Z]+", methods) or ["GET"]:
                result.add(f"{method} {_norm(path)}")
    return result


def test_client_endpoints_are_baseline_or_capability_guarded():
    unguarded = _client_endpoints() - _baseline() - set(_guarded_endpoints())
    assert not unguarded, (
        "Эндпоинты новее baseline без метки capability — бета-клиент сломается "
        "на стабильном сервере. Добавьте метку в core/api_capabilities.py и "
        f"ServerCapabilities.ENDPOINT_CAPABILITIES: {sorted(unguarded)}"
    )


def test_client_capabilities_are_declared_by_server():
    missing = set(_guarded_endpoints().values()) - set(API_CAPABILITIES)
    assert not missing, f"Метки не объявлены в core/api_capabilities.py: {sorted(missing)}"


def test_server_still_serves_whole_baseline():
    removed = _baseline() - _server_endpoints()
    assert not removed, f"Сервер больше не обслуживает baseline-эндпоинты: {sorted(removed)}"
