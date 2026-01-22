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

import base64
import json
import logging
import re
import ssl
import threading
from http import cookiejar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import (
    HTTPBasicAuthHandler,
    HTTPCookieProcessor,
    HTTPPasswordMgrWithDefaultRealm,
    HTTPSHandler,
    Request,
    build_opener,
)

from config.settings import DATA_DIR
from extensions.extension_manager import extension_manager
from lib.logging import debug_log

SUPPLIER_STOCK_EXTENSION_ID = "supplier_stock_files"
_logger = logging.getLogger("supplier_stock_files")
_monitor_logger = logging.getLogger("monitoring")

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


def _is_ascii(value: str) -> bool:
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def _open_with_auth_retry(
    opener: Any,
    url: str,
    headers: Dict[str, str],
    timeout: int,
    username: str,
    password: str,
    handlers: list,
) -> Any:
    request = Request(url, headers=headers)
    try:
        return opener.open(request, timeout=timeout)
    except HTTPError as exc:
        if exc.code != 401 or not (username or password):
            raise
    auth_headers = dict(headers)
    if "Authorization" not in auth_headers:
        credentials = f"{username}:{password}".encode("utf-8")
        auth_headers["Authorization"] = "Basic " + base64.b64encode(credentials).decode("ascii")
    if _is_ascii(f"{username}{password}"):
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, username, password)
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        auth_opener = build_opener(*handlers, auth_handler)
        request = Request(url, headers=auth_headers)
        return auth_opener.open(request, timeout=timeout)
    request = Request(url, headers=auth_headers)
    return opener.open(request, timeout=timeout)


def _download_http(
    source: Dict[str, Any],
    output_path: Path,
    now: datetime,
    render_context: Dict[str, Any],
) -> Dict[str, Any]:
    timeout = int(source.get("timeout", 300))
    headers = dict(source.get("headers") or {})
    verify_ssl = bool(source.get("verify_ssl", True))
    auth = source.get("auth") or {}
    username = auth.get("username") or ""
    password = auth.get("password") or ""

    handlers = []
    cookie_jar = cookiejar.CookieJar()
    cookie_handler = HTTPCookieProcessor(cookie_jar)
    handlers.append(cookie_handler)
    if username or password:
        auth_encoding = str(auth.get("encoding", "utf-8"))
        credentials = f"{username}:{password}".encode(auth_encoding)
        headers["Authorization"] = "Basic " + base64.b64encode(credentials).decode("ascii")
    if not verify_ssl:
        handlers.append(HTTPSHandler(context=ssl._create_unverified_context()))

    opener = build_opener(*handlers)
    pre_request = source.get("pre_request")
    if pre_request:
        pre_result = _run_pre_request(pre_request, opener, now, render_context, timeout)
        if not pre_result.get("success"):
            return pre_result

    discover = source.get("discover")
    if discover:
        discover_result = _discover_url(discover, opener, now, render_context, timeout)
        if not discover_result.get("success"):
            return discover_result
        url = discover_result.get("url", "")
    else:
        url = _render_template(str(source.get("url", "")), now, render_context)

    try:
        response = _open_with_auth_retry(
            opener,
            url,
            headers,
            timeout,
            username,
            password,
            handlers,
        )
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    try:
        _ensure_parent(output_path)
        with response:
            data = response.read()
        include_headers = bool(source.get("include_headers"))
        append_mode = bool(source.get("append"))
        if include_headers:
            version_map = {10: "1.0", 11: "1.1"}
            http_version = version_map.get(getattr(response, "version", 11), "1.1")
            status_line = f"HTTP/{http_version} {response.status} {response.reason}\r\n"
            header_lines = [f"{key}: {value}\r\n" for key, value in response.getheaders()]
            header_block = status_line + "".join(header_lines) + "\r\n"
            data = header_block.encode("utf-8") + data
        write_mode = "ab" if append_mode else "wb"
        with output_path.open(write_mode) as file:
            file.write(data)
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


def _run_pre_request(
    pre_request: Dict[str, Any],
    opener: Any,
    now: datetime,
    render_context: Dict[str, Any],
    timeout: int,
) -> Dict[str, Any]:
    if not isinstance(pre_request, dict):
        return {"success": False, "error": "Некорректные данные pre_request"}
    url = _render_template(str(pre_request.get("url", "")), now, render_context)
    if not url:
        return {"success": False, "error": "pre_request: URL не задан"}
    method = str(pre_request.get("method", "POST")).upper()
    headers = dict(pre_request.get("headers") or {})
    data_value = pre_request.get("data")
    data_bytes: bytes | None
    if data_value is None:
        data_bytes = b"" if method in ("POST", "PUT", "PATCH") else None
    else:
        data_text = _render_template(str(data_value), now, render_context)
        data_bytes = data_text.encode("utf-8")
    if data_bytes is not None and "Content-Type" not in headers:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    max_redirects = 3
    current_url = url
    current_method = method
    current_data = data_bytes
    for _ in range(max_redirects + 1):
        request = Request(current_url, data=current_data, headers=headers, method=current_method)
        try:
            response = opener.open(request, timeout=timeout)
            with response:
                response.read()
            return {"success": True}
        except HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
                current_url = urljoin(current_url, exc.headers["Location"])
                if exc.code == 303:
                    current_method = "GET"
                    current_data = None
                continue
            return {"success": False, "error": f"pre_request: {exc}"}
        except Exception as exc:
            return {"success": False, "error": f"pre_request: {exc}"}
    return {"success": False, "error": "pre_request: слишком много перенаправлений"}


def _discover_url(
    discover: Dict[str, Any],
    opener: Any,
    now: datetime,
    render_context: Dict[str, Any],
    timeout: int,
) -> Dict[str, Any]:
    if not isinstance(discover, dict):
        return {"success": False, "error": "Некорректные данные discover"}
    source_url = _render_template(str(discover.get("url", "")), now, render_context)
    pattern = _render_template(str(discover.get("pattern", "")), now, render_context)
    prefix = _render_template(str(discover.get("prefix", "")), now, render_context)
    if not source_url or not pattern:
        return {"success": False, "error": "discover: URL или шаблон не задан"}
    try:
        request = Request(source_url)
        with opener.open(request, timeout=timeout) as response:
            page_content = response.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return {"success": False, "error": f"discover: {exc}"}

    match = re.search(pattern, page_content)
    if not match:
        return {"success": False, "error": "discover: ссылка не найдена"}
    discovered = match.group(0)
    if prefix:
        discovered = prefix + discovered
    return {"success": True, "url": discovered}


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
        try:
            _logger.info(message, *args)
        except Exception:
            pass
        try:
            _monitor_logger.info(message, *args)
        except Exception:
            pass

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
            if not rendered_url:
                entry.update({"status": "error", "error": "URL не задан"})
                append_supplier_stock_report(entry)
                results.append(entry)
                _log("📦 Остатки поставщиков: %s -> error (URL не задан)", entry["source_id"])
                continue
            if output_name:
                output_name = _render_template(str(output_name), now, render_context)
                output_path = temp_dir / output_name
            else:
                output_path = temp_dir / f"{source_id}_orig"

            entry.update({"url": rendered_url, "output_name": output_name})
            _log("📦 Остатки поставщиков: %s -> старт (%s)", entry["source_id"], rendered_url)

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
