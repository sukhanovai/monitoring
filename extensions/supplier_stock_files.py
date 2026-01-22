"""
/extensions/supplier_stock_files.py
Server Monitoring System v8.0.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Supplier stock files downloader
Система мониторинга серверов
Версия: 8.0.0
Автор: Александр Суханов (c)
Лицензия: MIT
Получение файлов остатков поставщиков
"""

from __future__ import annotations

import json
import base64
import re
import ssl
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.request import HTTPSHandler, Request, build_opener

from config.settings import DATA_DIR
from extensions.extension_manager import extension_manager
from lib.logging import debug_log

SUPPLIER_STOCK_EXTENSION_ID = "supplier_stock_files"

DEFAULT_SUPPLIER_STOCK_CONFIG: Dict[str, Any] = {
    "download": {
        "temp_dir": str(DATA_DIR / "supplier_stock" / "tmp"),
        "archive_dir": str(DATA_DIR / "supplier_stock" / "archive"),
        "reports_file": str(DATA_DIR / "supplier_stock" / "reports.jsonl"),
        "schedule": {"enabled": False, "time": "06:00"},
        "sources": [],
    },
    "mail": {
        "enabled": False,
    },
}

_scheduler_lock = threading.Lock()
_scheduler_started = False
_last_run_marker: str | None = None


def _merge_dicts(defaults: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(defaults)
    for key, value in current.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def normalize_supplier_stock_config(config: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(config, dict):
        return dict(DEFAULT_SUPPLIER_STOCK_CONFIG)
    merged = _merge_dicts(DEFAULT_SUPPLIER_STOCK_CONFIG, config)
    sources = merged.get("download", {}).get("sources", [])
    if isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict):
                source.setdefault("enabled", True)
    return merged


def get_supplier_stock_config() -> Dict[str, Any]:
    config = extension_manager.load_extension_config(SUPPLIER_STOCK_EXTENSION_ID)
    return normalize_supplier_stock_config(config)


def save_supplier_stock_config(config: Dict[str, Any]) -> tuple[bool, str]:
    normalized = normalize_supplier_stock_config(config)
    temp_dir = Path(normalized["download"]["temp_dir"])
    temp_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = Path(normalized["download"]["archive_dir"])
    archive_dir.mkdir(parents=True, exist_ok=True)
    return extension_manager.save_extension_config(SUPPLIER_STOCK_EXTENSION_ID, normalized)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _render_template(value: str, now: datetime, extra_context: Dict[str, Any] | None = None) -> str:
    context = {
        "date": now.strftime("%d.%m.%Y"),
        "date_iso": now.strftime("%Y-%m-%d"),
        "datetime": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "time": now.strftime("%H-%M-%S"),
    }
    if extra_context:
        context.update(extra_context)
    def _replace_date(match: re.Match[str]) -> str:
        fmt = match.group("format") or ""
        fmt = fmt.replace("\\'", "'")
        try:
            return now.strftime(fmt)
        except Exception:
            return match.group(0)

    rendered = re.sub(r"\$\(\s*date\s+'(?P<format>[^']+)'\s*\)", _replace_date, value)
    try:
        rendered = rendered.format_map(context)
    except Exception:
        pass
    rendered = re.sub(
        r"\$\{(?P<key>[A-Za-z_][A-Za-z0-9_]*)\}",
        lambda m: str(context.get(m.group("key"), m.group(0))),
        rendered,
    )
    return re.sub(
        r"\$(?P<key>[A-Za-z_][A-Za-z0-9_]*)",
        lambda m: str(context.get(m.group("key"), m.group(0))),
        rendered,
    )


def _build_render_context(source: Dict[str, Any], now: datetime) -> Dict[str, Any]:
    context: Dict[str, Any] = {}
    vars_map = source.get("vars", {})
    if isinstance(vars_map, dict):
        for key, value in vars_map.items():
            context[key] = _render_template(str(value), now, context)
    return context


def _download_http(
    source: Dict[str, Any],
    output_path: Path,
    now: datetime,
    render_context: Dict[str, Any],
) -> Dict[str, Any]:
    url = _render_template(str(source.get("url", "")), now, render_context)
    timeout = int(source.get("timeout", 300))
    headers = dict(source.get("headers") or {})
    verify_ssl = bool(source.get("verify_ssl", True))
    auth = source.get("auth") or {}
    username = auth.get("username") or ""
    password = auth.get("password") or ""

    handlers = []
    if username or password:
        auth_encoding = str(auth.get("encoding", "utf-8"))
        credentials = f"{username}:{password}".encode(auth_encoding)
        headers["Authorization"] = "Basic " + base64.b64encode(credentials).decode("ascii")
    if not verify_ssl:
        handlers.append(HTTPSHandler(context=ssl._create_unverified_context()))

    request = Request(url, headers=headers)
    opener = build_opener(*handlers)
    try:
        response = opener.open(request, timeout=timeout)
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    try:
        _ensure_parent(output_path)
        with response:
            data = response.read()
            output_path.write_bytes(data)
        return {
            "success": True,
            "bytes": output_path.stat().st_size,
            "path": str(output_path),
        }
    finally:
        try:
            response.close()
        except Exception:
            pass


def _run_shell_command(
    source: Dict[str, Any],
    now: datetime,
    temp_dir: Path,
    render_context: Dict[str, Any],
) -> Dict[str, Any]:
    import subprocess

    command = _render_template(str(source.get("command", "")), now, render_context)
    if not command:
        return {"success": False, "error": "Команда не задана"}

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output_name = _render_template(str(source.get("output_name", "")), now)
    output_path = str(temp_dir / output_name) if output_name else ""

    return {
        "success": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "path": output_path,
    }


def append_supplier_stock_report(entry: Dict[str, Any]) -> None:
    config = get_supplier_stock_config()
    reports_file = Path(config["download"]["reports_file"])
    _ensure_parent(reports_file)
    with reports_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_supplier_stock_reports(limit: int = 20) -> List[Dict[str, Any]]:
    config = get_supplier_stock_config()
    reports_file = Path(config["download"]["reports_file"])
    if not reports_file.exists():
        return []

    entries: List[Dict[str, Any]] = []
    with reports_file.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return entries[-limit:][::-1]


def run_supplier_stock_fetch() -> Dict[str, Any]:
    config = get_supplier_stock_config()
    download_config = config.get("download", {})
    temp_dir = Path(download_config.get("temp_dir", DEFAULT_SUPPLIER_STOCK_CONFIG["download"]["temp_dir"]))
    temp_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = Path(download_config.get("archive_dir", DEFAULT_SUPPLIER_STOCK_CONFIG["download"]["archive_dir"]))
    archive_dir.mkdir(parents=True, exist_ok=True)

    sources = download_config.get("sources", [])
    now = datetime.now()
    results: List[Dict[str, Any]] = []
    def _log(message: str, *args: object) -> None:
        try:
            debug_log(message, *args)
        except Exception:
            formatted = message % args if args else message
            debug_log(formatted)

    _log("📦 Остатки поставщиков: источников к обработке %s", len(sources))

    for source in sources:
        source_id = source.get("id") or source.get("name") or "unknown"
        name = source.get("name") or source_id
        if not source.get("enabled", True):
            _log("📦 Остатки поставщиков: %s пропущен (выключен)", source_id)
            results.append({"source_id": source_id, "source_name": name, "status": "skipped"})
            continue

        entry: Dict[str, Any] = {
            "timestamp": now.isoformat(),
            "source_id": source_id,
            "source_name": name,
            "method": source.get("method", "http"),
        }

        try:
            render_context = _build_render_context(source, now)
            output_name = source.get("output_name")
            rendered_url = _render_template(str(source.get("url", "")), now, render_context)
            if output_name:
                output_name = _render_template(str(output_name), now, render_context)
                output_path = temp_dir / output_name
            else:
                output_path = temp_dir / f"{source_id}_orig"

            entry.update({"url": rendered_url, "output_name": output_name})

            if entry["method"] == "shell":
                result = _run_shell_command(source, now, temp_dir, render_context)
            else:
                result = _download_http(source, output_path, now, render_context)

            entry.update(result)
            entry["status"] = "success" if result.get("success") else "error"

            if entry["status"] == "success" and output_path.exists():
                archive_path = _archive_original_file(output_path, archive_dir, now)
                if archive_path:
                    entry["archive_path"] = str(archive_path)
        except Exception as exc:
            entry.update({"status": "error", "error": str(exc)})

        append_supplier_stock_report(entry)
        results.append(entry)
        if entry.get("status") == "error" and entry.get("error"):
            _log(
                "📦 Остатки поставщиков: %s -> error (%s)",
                entry["source_id"],
                entry["error"],
            )
        else:
            _log("📦 Остатки поставщиков: %s -> %s", entry["source_id"], entry["status"])

    success_count = sum(1 for item in results if item.get("status") == "success")
    return {
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results,
    }


def _should_run_schedule(schedule: Dict[str, Any], now: datetime) -> bool:
    if not schedule.get("enabled"):
        return False

    schedule_time = str(schedule.get("time", ""))
    if not schedule_time:
        return False

    try:
        hours, minutes = [int(part) for part in schedule_time.split(":", 1)]
    except ValueError:
        return False

    if now.hour != hours or now.minute != minutes:
        return False

    global _last_run_marker
    current_date = now.strftime("%Y-%m-%d")
    marker = f"{current_date}|{schedule_time}"
    if _last_run_marker == marker:
        return False

    _last_run_marker = marker
    return True


def start_supplier_stock_scheduler() -> None:
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    def _loop() -> None:
        debug_log("⏰ Запуск планировщика загрузки остатков поставщиков")
        while True:
            now = datetime.now()
            schedule = get_supplier_stock_config().get("download", {}).get("schedule", {})
            if _should_run_schedule(schedule, now):
                debug_log("📦 Плановая загрузка остатков поставщиков")
                run_supplier_stock_fetch()
            threading.Event().wait(30)

    threading.Thread(target=_loop, daemon=True).start()


def _archive_original_file(source_path: Path, archive_dir: Path, now: datetime) -> Path | None:
    if not source_path.exists():
        return None
    archive_dir.mkdir(parents=True, exist_ok=True)
    date_stamp = now.strftime("%Y-%m-%d")
    if source_path.suffix:
        archive_name = f"{source_path.stem}_{date_stamp}{source_path.suffix}"
    else:
        archive_name = f"{source_path.name}_{date_stamp}"
    archive_path = archive_dir / archive_name
    try:
        import shutil

        shutil.copy2(source_path, archive_path)
        return archive_path
    except Exception:
        return None


def summarize_supplier_stock_sources(sources: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary = []
    for source in sources:
        summary.append(
            {
                "id": source.get("id"),
                "name": source.get("name"),
                "url": source.get("url"),
                "output_name": source.get("output_name"),
                "method": source.get("method", "http"),
                "enabled": source.get("enabled", True),
            }
        )
    return summary
