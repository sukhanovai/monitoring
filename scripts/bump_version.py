#!/usr/bin/env python3
"""
/scripts/bump_version.py
Server Monitoring System v8.62.71
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Version bump helper extracted from the manual procedure in CLAUDE.md
(PR9 серии оптимизации).
Система мониторинга серверов
Версия: 8.62.71
Автор: Александр Суханов (c)
Лицензия: MIT
Скрипт автоматизирует ручную процедуру синхронизации версии,
описанную в CLAUDE.md. Канонический источник — `config/settings.py`:
`APP_VERSION` и `ANDROID_LATEST_VERSION`. Все остальные места
(заголовки `*.py`, `android-client/gradle.properties`, ссылки на
prerelease APK в `README.md` / `docs/android_mobile_app.md`,
верхняя запись `CHANGELOG.md`) должны совпадать.

Использование:
    python scripts/bump_version.py --check          # сверить согласованность
    python scripts/bump_version.py <new-version>    # обновить везде
    python scripts/bump_version.py --print          # вывести текущую версию

Pre-commit hook вызывает `--check` — рассинхрон ломает коммит.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Регекс для версии формата SemVer-patch без префикса (например, 8.62.61).
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class VersionSite:
    """Декларативное описание одной точки, где версия должна быть синхронизирована."""

    path: Path  # относительный путь от корня репо
    pattern: re.Pattern[str]  # должен содержать одну группу с версией
    label: str  # для отчёта/ошибок


def _site(path: str, pattern: str, label: str) -> VersionSite:
    return VersionSite(
        path=REPO_ROOT / path,
        pattern=re.compile(pattern, re.MULTILINE),
        label=label,
    )


# Канонический источник правды — config/settings.py
CANONICAL_SITE = _site(
    "config/settings.py",
    r'^APP_VERSION\s*=\s*"(\d+\.\d+\.\d+)"\s*$',
    "config/settings.py:APP_VERSION (канонический)",
)

# Точечные сайты — обязаны совпадать с APP_VERSION
EXPLICIT_SITES: tuple[VersionSite, ...] = (
    CANONICAL_SITE,
    _site(
        "config/settings.py",
        r'^ANDROID_LATEST_VERSION\s*=\s*"(\d+\.\d+\.\d+)"\s*$',
        "config/settings.py:ANDROID_LATEST_VERSION",
    ),
    _site(
        "android-client/gradle.properties",
        r"^ANDROID_VERSION_NAME=(\d+\.\d+\.\d+)\s*$",
        "android-client/gradle.properties:ANDROID_VERSION_NAME",
    ),
    _site(
        "README.md",
        r"releases/download/v(\d+\.\d+\.\d+)-develop/monitoring-android-\d+\.\d+\.\d+-develop-debug\.apk",
        "README.md:ANDROID_PRERELEASE_APK_LINK",
    ),
    _site(
        "docs/android_mobile_app.md",
        r"releases/download/v(\d+\.\d+\.\d+)-develop/monitoring-android-\d+\.\d+\.\d+-develop-debug\.apk",
        "docs/android_mobile_app.md:ANDROID_PRERELEASE_APK_LINK",
    ),
)

# Шаблоны для заголовков .py-файлов: `Server Monitoring System v<ver>` и `Версия: <ver>`
HEADER_VERSION_RE = re.compile(r"Server Monitoring System v(\d+\.\d+\.\d+)")
HEADER_VERSION_RU_RE = re.compile(r"Версия:\s*(\d+\.\d+\.\d+)")

# Где искать заголовки. Совпадает со списком из CLAUDE.md.
HEADER_DIRS_GLOB = (
    "main.py",
    "modules/**/*.py",
    "extensions/**/*.py",
    "docs/**/*.md",
)


def discover_header_files() -> list[Path]:
    """Перечень файлов с шапками Server Monitoring System."""
    files: list[Path] = []
    for pattern in HEADER_DIRS_GLOB:
        files.extend(sorted(REPO_ROOT.glob(pattern)))
    # Сюда же явно — заголовки в pyproject подразделениях, чтобы не править регулярки.
    extra_globs = (
        "bot/**/*.py",
        "core/**/*.py",
        "lib/**/*.py",
        "config/**/*.py",
        "scripts/**/*.py",
    )
    for pattern in extra_globs:
        files.extend(sorted(REPO_ROOT.glob(pattern)))
    # Удаляем дубликаты и пути, попавшие через несколько glob'ов.
    return sorted({f.resolve() for f in files if f.is_file()})


def read_canonical_version() -> str:
    """Читает APP_VERSION из config/settings.py — единая точка правды."""
    text = CANONICAL_SITE.path.read_text(encoding="utf-8")
    for line in text.splitlines():
        match = CANONICAL_SITE.pattern.match(line)
        if match:
            return match.group(1)
    raise RuntimeError(f"APP_VERSION не найден в {CANONICAL_SITE.path}")


def _scan_file_for_versions(
    path: Path, patterns: Iterable[re.Pattern[str]]
) -> list[tuple[int, str, str]]:
    """Возвращает список (line_no, matched_substring, version) для всех
    встречаний любого из `patterns` в файле."""
    matches: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return matches
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern in patterns:
            for match in pattern.finditer(line):
                matches.append((line_no, match.group(0), match.group(1)))
    return matches


def collect_explicit_mismatches(
    expected: str, sites: Iterable[VersionSite] | None = None
) -> list[tuple[VersionSite, str | None]]:
    """Возвращает сайты с неверной/отсутствующей версией.

    `sites=None` → читается актуальный `EXPLICIT_SITES` из модуля (важно,
    чтобы pytest-monkeypatch видел подмену в тестах — default-аргументы
    Python захватывают значение в момент определения функции).
    """
    if sites is None:
        sites = EXPLICIT_SITES
    mismatches: list[tuple[VersionSite, str | None]] = []
    for site in sites:
        if not site.path.exists():
            mismatches.append((site, None))
            continue
        text = site.path.read_text(encoding="utf-8")
        found: str | None = None
        for line in text.splitlines():
            match = site.pattern.search(line)
            if match:
                found = match.group(1)
                break
        if found != expected:
            mismatches.append((site, found))
    return mismatches


def collect_header_mismatches(
    expected: str, files: Iterable[Path]
) -> list[tuple[Path, int, str, str]]:
    """Возвращает заголовки с версией, отличной от expected.

    Игнорирует исторические упоминания в комментариях/докстрингах,
    которые не выглядят как `Server Monitoring System v…` / `Версия:…`.
    """
    mismatches: list[tuple[Path, int, str, str]] = []
    patterns = (HEADER_VERSION_RE, HEADER_VERSION_RU_RE)
    for path in files:
        for line_no, snippet, version in _scan_file_for_versions(path, patterns):
            if version != expected:
                mismatches.append((path, line_no, snippet, version))
    return mismatches


def check_consistency() -> int:
    """`bump_version.py --check` — главная команда pre-commit hook."""
    expected = read_canonical_version()

    bad_explicit = collect_explicit_mismatches(expected)
    headers = discover_header_files()
    bad_headers = collect_header_mismatches(expected, headers)

    if not bad_explicit and not bad_headers:
        print(f"✅ Версия {expected} согласована во всех {len(headers)} файлах")
        return 0

    def _rel(path: Path) -> Path | str:
        try:
            return path.relative_to(REPO_ROOT)
        except ValueError:
            return path

    print(f"❌ Канонический APP_VERSION = {expected}, но найдены расхождения:\n")
    for site, found in bad_explicit:
        rel = _rel(site.path)
        if found is None:
            print(f"   • {rel} — пропущен (паттерн {site.pattern.pattern!r})")
        else:
            print(f"   • {site.label}: {found}  ({rel})")

    if bad_headers:
        print(
            f"\n   {len(bad_headers)} расхождений в заголовках Server Monitoring System / Версия:"
        )
        for path, line_no, snippet, version in bad_headers[:10]:
            rel = _rel(path)
            print(f"   • {rel}:{line_no}: {snippet!r} (нужно {expected}, найдено {version})")
        if len(bad_headers) > 10:
            print(f"   • ... и ещё {len(bad_headers) - 10}")

    print(
        f"\nПодсказка: `python scripts/bump_version.py {expected}` "
        "обновит все места до канонической версии."
    )
    return 1


def _replace_explicit_sites(new_version: str) -> int:
    """Обновляет EXPLICIT_SITES (config/settings.py, gradle.properties,
    README.md, docs/android_mobile_app.md) до new_version."""

    def _replace(match: re.Match[str]) -> str:
        return match.group(0).replace(match.group(1), new_version)

    touched = 0
    for site in EXPLICIT_SITES:
        if not site.path.exists():
            continue
        text = site.path.read_text(encoding="utf-8")
        new_text = site.pattern.sub(_replace, text)
        if new_text != text:
            site.path.write_text(new_text, encoding="utf-8")
            touched += 1
    return touched


def _replace_headers(new_version: str, files: Iterable[Path]) -> int:
    """Обновляет шапки `Server Monitoring System v…` / `Версия:…` до new_version."""

    def _replace(match: re.Match[str]) -> str:
        return match.group(0).replace(match.group(1), new_version)

    touched = 0
    patterns = (HEADER_VERSION_RE, HEADER_VERSION_RU_RE)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new_text = text
        for pattern in patterns:
            new_text = pattern.sub(_replace, new_text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            touched += 1
    return touched


def bump_to(new_version: str) -> int:
    """Полный bump: обновляет EXPLICIT_SITES + все заголовки.

    `ANDROID_VERSION_CODE` НЕ инкрементируется — это отдельная семантика
    (увеличивается раз на релиз Android-клиента, не привязан к patch-бампу),
    обновлять вручную или отдельной утилитой.
    `CHANGELOG.md` запись добавляется ВРУЧНУЮ перед коммитом — скрипт не
    подменяет смысл сообщения автору.
    """
    if not VERSION_RE.match(new_version):
        print(f"❌ '{new_version}' не похоже на SemVer-patch (ожидается X.Y.Z)")
        return 2

    touched_explicit = _replace_explicit_sites(new_version)
    headers = discover_header_files()
    touched_headers = _replace_headers(new_version, headers)

    print(
        f"✅ Версия обновлена до {new_version}\n"
        f"   • {touched_explicit}/{len(EXPLICIT_SITES)} точечных сайтов;\n"
        f"   • {touched_headers}/{len(headers)} файлов с шапками."
    )
    if touched_explicit + touched_headers == 0:
        print("ℹ️  Все файлы уже на этой версии — ничего не изменено.")
    print(
        "\nНе забудь вручную:\n"
        "  1. Добавить запись в CHANGELOG.md (RU+EN);\n"
        "  2. Инкрементировать android-client/gradle.properties:ANDROID_VERSION_CODE\n"
        "     (отдельная семантика, скрипт его не трогает)."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bump_version.py",
        description=("Синхронизация версии проекта по всем файлам, перечисленным в CLAUDE.md."),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="проверить согласованность версии (выход 1 при рассинхроне)",
    )
    group.add_argument(
        "--print",
        action="store_true",
        help="вывести текущую каноническую версию из config/settings.py",
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="новая версия (X.Y.Z); без неё работает --check или --print",
    )
    args = parser.parse_args(argv)

    if args.print:
        print(read_canonical_version())
        return 0

    if args.check or args.version is None:
        return check_consistency()

    return bump_to(args.version)


if __name__ == "__main__":
    raise SystemExit(main())
