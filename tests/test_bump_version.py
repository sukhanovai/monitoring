"""
Unit-тесты для scripts/bump_version.py (PR9).

Скрипт работает с настоящим деревом репозитория, поэтому тесты:
1. На «чистом» состоянии develop проверяют, что `--check` зелёный,
   что и закрепляет инвариант для pre-commit hook.
2. На временном дереве (tmp_path) проверяют bump-логику изолированно
   — модифицируем копии файлов, не настоящий репо.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


@pytest.fixture(scope="module")
def bump_module():
    """Импорт bump_version как модуля для прямого вызова функций."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        module = importlib.import_module("bump_version")
        yield module
    finally:
        sys.modules.pop("bump_version", None)
        if str(SCRIPTS_DIR) in sys.path:
            sys.path.remove(str(SCRIPTS_DIR))


def test_canonical_version_matches_app_version(bump_module) -> None:
    """`read_canonical_version` достаёт ту же строку, что лежит в
    config/settings.py:APP_VERSION."""
    version = bump_module.read_canonical_version()
    assert bump_module.VERSION_RE.match(version), f"Версия не SemVer-patch: {version!r}"

    text = (REPO_ROOT / "config" / "settings.py").read_text(encoding="utf-8")
    assert f'APP_VERSION = "{version}"' in text


def test_check_consistency_on_clean_tree(bump_module, capsys) -> None:
    """На чистом дереве develop `--check` должен вернуть 0 — это
    инвариант, на который опирается pre-commit hook."""
    rc = bump_module.check_consistency()
    assert rc == 0
    out = capsys.readouterr().out
    assert "согласована" in out


def test_explicit_sites_have_required_paths(bump_module) -> None:
    """Все жёстко-захардкоженные сайты должны существовать в репо.
    Если кто-то переименовал config/settings.py — заметим сразу."""
    for site in bump_module.EXPLICIT_SITES:
        assert site.path.exists(), f"Не найден файл: {site.path}"


def test_discover_header_files_includes_known_modules(bump_module) -> None:
    """Гарантируем, что скрипт обходит main.py, modules/*, extensions/*,
    bot/*, core/*, lib/*, config/*, scripts/* и docs/*."""
    files = bump_module.discover_header_files()
    rel_paths = {f.relative_to(REPO_ROOT) for f in files}
    expected_anchors = [
        Path("main.py"),
        Path("modules/mail_monitor.py"),
        Path("extensions/extension_manager.py"),
        Path("bot/handlers/callbacks.py"),
        Path("core/monitor_core.py"),
        Path("lib/utils.py"),
        Path("config/settings.py"),
        Path("scripts/bump_version.py"),
    ]
    for anchor in expected_anchors:
        assert anchor in rel_paths, anchor


def test_bump_to_updates_temp_settings_file(bump_module, tmp_path, monkeypatch) -> None:
    """Изолированный тест: создаём fake config/settings.py в tmp,
    переключаем REPO_ROOT, вызываем `bump_to`, проверяем результат."""
    fake_root = tmp_path
    (fake_root / "config").mkdir()
    settings_path = fake_root / "config" / "settings.py"
    settings_path.write_text(
        'APP_VERSION = "8.62.61"\nANDROID_LATEST_VERSION = "8.62.61"\n',
        encoding="utf-8",
    )

    # Подменяем константы модуля на fake-root.
    monkeypatch.setattr(bump_module, "REPO_ROOT", fake_root)
    new_canonical_site = bump_module.VersionSite(
        path=settings_path,
        pattern=bump_module.CANONICAL_SITE.pattern,
        label="fake config/settings.py:APP_VERSION",
    )
    new_android_site = bump_module.VersionSite(
        path=settings_path,
        pattern=bump_module._site(
            "config/settings.py",
            r'^ANDROID_LATEST_VERSION\s*=\s*"(\d+\.\d+\.\d+)"\s*$',
            "x",
        ).pattern,
        label="fake config/settings.py:ANDROID_LATEST_VERSION",
    )
    monkeypatch.setattr(bump_module, "CANONICAL_SITE", new_canonical_site)
    monkeypatch.setattr(bump_module, "EXPLICIT_SITES", (new_canonical_site, new_android_site))

    rc = bump_module.bump_to("8.62.99")
    assert rc == 0

    updated = settings_path.read_text(encoding="utf-8")
    assert 'APP_VERSION = "8.62.99"' in updated
    assert 'ANDROID_LATEST_VERSION = "8.62.99"' in updated
    assert "8.62.61" not in updated


def test_bump_to_rejects_non_semver(bump_module, capsys) -> None:
    """Любой формат, кроме X.Y.Z, должен вернуть код 2 и не пытаться
    править файлы."""
    rc = bump_module.bump_to("v8.62.99")
    assert rc == 2
    out = capsys.readouterr().out
    assert "не похоже на SemVer" in out

    rc = bump_module.bump_to("8.62")
    assert rc == 2


def test_bump_then_check_round_trip(bump_module, tmp_path, monkeypatch) -> None:
    """Round-trip: bump → check на том же дереве должен дать 0."""
    fake_root = tmp_path
    (fake_root / "config").mkdir()
    settings_path = fake_root / "config" / "settings.py"
    settings_path.write_text(
        'APP_VERSION = "8.62.10"\nANDROID_LATEST_VERSION = "8.62.10"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(bump_module, "REPO_ROOT", fake_root)
    canonical = bump_module.VersionSite(
        path=settings_path,
        pattern=bump_module.CANONICAL_SITE.pattern,
        label="fake APP_VERSION",
    )
    android = bump_module.VersionSite(
        path=settings_path,
        pattern=bump_module._site(
            "config/settings.py",
            r'^ANDROID_LATEST_VERSION\s*=\s*"(\d+\.\d+\.\d+)"\s*$',
            "x",
        ).pattern,
        label="fake ANDROID_LATEST_VERSION",
    )
    monkeypatch.setattr(bump_module, "CANONICAL_SITE", canonical)
    monkeypatch.setattr(bump_module, "EXPLICIT_SITES", (canonical, android))
    # На fake-root заголовков нет.
    monkeypatch.setattr(bump_module, "discover_header_files", lambda: [])

    assert bump_module.bump_to("8.62.50") == 0
    assert bump_module.check_consistency() == 0
