"""
Тесты обработки писем с остатками поставщиков.

Закрепляют два бага, из-за которых письмо «остатки» с вложением
поставщика падало в лог как необработанное:

1. смена шаблона вложения (`asd_orig.xls` → `asd_orig.xlsx`) не доходила
   до привязанного правила обработки — «подходящие правила обработки не
   найдены», файл выгружался без обработки;
2. очистка архива сравнивала дату письма (с таймзоной) с mtime файла
   (без таймзоны) — `can't compare offset-naive and offset-aware
   datetimes`, письмо не помечалось обработанным и разбиралось заново.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _config_with_mail_rule(template: str, rule_source_file: str) -> dict:
    return {
        "mail": {
            "enabled": True,
            "sources": [
                {
                    "id": "source",
                    "name": "АСД",
                    "enabled": True,
                    "output_template": template,
                }
            ],
        },
        "processing": {
            "rules": [
                {
                    "id": "rule-asd",
                    "name": "АСД",
                    "source_id": "source",
                    "source_kind": "mail",
                    "source_file": rule_source_file,
                    "enabled": True,
                    "active": True,
                }
            ]
        },
    }


def test_processing_rule_picks_up_new_attachment_template() -> None:
    """Правило берёт имя файла из источника, а не из своей старой копии."""
    from extensions.supplier_stock_files import normalize_supplier_stock_config

    normalized = normalize_supplier_stock_config(
        _config_with_mail_rule("asd_orig.xlsx", "asd_orig.xls")
    )

    rule = normalized["processing"]["rules"][0]
    assert rule["source_file"] == "asd_orig.xlsx"


def test_processing_rule_matches_file_after_template_change(tmp_path) -> None:
    """После синхронизации правило подходит к пришедшему файлу."""
    from extensions.supplier_stock_files import (
        _processing_rule_matches,
        normalize_supplier_stock_config,
    )

    normalized = normalize_supplier_stock_config(
        _config_with_mail_rule("asd_orig.xlsx", "asd_orig.xls")
    )
    rule = normalized["processing"]["rules"][0]
    incoming = tmp_path / "asd_orig.xlsx"
    incoming.write_bytes(b"")

    assert _processing_rule_matches(rule, incoming, 1)


def test_processing_rule_without_source_is_not_touched() -> None:
    """Правило без привязки к источнику остаётся как есть."""
    from extensions.supplier_stock_files import normalize_supplier_stock_config

    config = _config_with_mail_rule("asd_orig.xlsx", "manual.xls")
    config["processing"]["rules"][0].pop("source_id")

    normalized = normalize_supplier_stock_config(config)
    assert normalized["processing"]["rules"][0]["source_file"] == "manual.xls"


def test_processing_rule_keeps_value_when_source_template_empty() -> None:
    """Пустой шаблон источника не затирает имя файла в правиле."""
    from extensions.supplier_stock_files import normalize_supplier_stock_config

    config = _config_with_mail_rule("", "asd_orig.xls")
    normalized = normalize_supplier_stock_config(config)

    assert normalized["processing"]["rules"][0]["source_file"] == "asd_orig.xls"


def test_cleanup_archives_accepts_aware_email_date(tmp_path, monkeypatch) -> None:
    """Дата письма с таймзоной не роняет очистку архива."""
    import extensions.supplier_stock_files as supplier_stock_files

    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    stale = archive_dir / "old.xlsx"
    stale.write_bytes(b"")
    fresh = archive_dir / "new.xlsx"
    fresh.write_bytes(b"")

    now = datetime(2026, 8, 5, 1, 44, 36, tzinfo=timezone.utc)
    local_now = now.astimezone().replace(tzinfo=None)
    stale_mtime = (local_now - timedelta(days=10)).timestamp()
    import os

    os.utime(stale, (stale_mtime, stale_mtime))
    fresh_mtime = local_now.timestamp()
    os.utime(fresh, (fresh_mtime, fresh_mtime))

    config = {
        "archive_cleanup_days": 3,
        "download": {"archive_dir": str(tmp_path / "download-archive")},
        "mail": {"archive_dir": str(archive_dir)},
    }
    monkeypatch.setattr(
        supplier_stock_files,
        "_parse_archive_cleanup_days",
        lambda _config: 3,
    )

    result = supplier_stock_files.cleanup_supplier_stock_archives(config, now)

    assert result["removed"] == 1
    assert not stale.exists()
    assert fresh.exists()
