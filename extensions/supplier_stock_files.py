"""
/extensions/supplier_stock_files.py
Server Monitoring System v8.2.48
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Supplier stock files downloader
Система мониторинга серверов
Версия: 8.2.48
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
import tarfile
import zipfile
import csv
import math
from http import cookiejar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from fnmatch import fnmatch
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
        "unpack_archive": False,
        "sources": [],
    },
    "mail": {
        "enabled": False,
        "temp_dir": str(DATA_DIR / "supplier_stock" / "mail_tmp"),
        "archive_dir": str(DATA_DIR / "supplier_stock" / "mail_archive"),
        "unpack_archive": False,
        "sources": [],
    },
    "processing": {
        "rules": [],
        "date_format": "%Y-%m-%d %H:%M",
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
    mail_sources = merged.get("mail", {}).get("sources", [])
    if isinstance(mail_sources, list):
        for source in mail_sources:
            if isinstance(source, dict):
                source.setdefault("enabled", True)
    processing_rules = merged.get("processing", {}).get("rules", [])
    if isinstance(processing_rules, list):
        for rule in processing_rules:
            if isinstance(rule, dict):
                rule.setdefault("enabled", True)
                rule["requires_processing"] = _normalize_requires_processing(rule.get("requires_processing", True))
    return merged


def _normalize_requires_processing(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("false", "0", "no", "нет", "off"):
            return False
        if lowered in ("true", "1", "yes", "да", "on"):
            return True
    return bool(value)


def get_supplier_stock_config() -> Dict[str, Any]:
    config = extension_manager.load_extension_config(SUPPLIER_STOCK_EXTENSION_ID)
    return normalize_supplier_stock_config(config)


def save_supplier_stock_config(config: Dict[str, Any]) -> tuple[bool, str]:
    normalized = normalize_supplier_stock_config(config)
    temp_dir = Path(normalized["download"]["temp_dir"])
    temp_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = Path(normalized["download"]["archive_dir"])
    archive_dir.mkdir(parents=True, exist_ok=True)
    mail_temp_dir = Path(normalized["mail"]["temp_dir"])
    mail_temp_dir.mkdir(parents=True, exist_ok=True)
    mail_archive_dir = Path(normalized["mail"]["archive_dir"])
    mail_archive_dir.mkdir(parents=True, exist_ok=True)
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


def process_supplier_stock_file(
    file_path: str | Path,
    source_id: str | None = None,
    source_kind: str | None = None,
    input_index: int | None = None,
    now: datetime | None = None,
) -> Dict[str, Any] | None:
    config = get_supplier_stock_config()
    path = Path(file_path)
    return _process_supplier_stock_file(
        path,
        config,
        now or datetime.now(),
        source_id,
        source_kind,
        input_index,
    )


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
                if source.get("unpack_archive"):
                    unpacked_path = unpack_archive_file(output_path)
                    if unpacked_path:
                        entry["path"] = str(unpacked_path)
                        entry["unpacked_path"] = str(unpacked_path)
                        output_path = unpacked_path
                        _log("📦 Остатки поставщиков: %s распакован в %s", entry["source_id"], unpacked_path)
                processing_result = _process_supplier_stock_file(
                    output_path,
                    config,
                    now,
                    source_id,
                    "download",
                    1,
                )
                if processing_result:
                    entry["processing"] = processing_result
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


def _process_supplier_stock_file(
    file_path: Path,
    config: Dict[str, Any],
    now: datetime,
    source_id: str | None = None,
    source_kind: str | None = None,
    input_index: int | None = None,
) -> Dict[str, Any] | None:
    processing = config.get("processing", {})
    rules = processing.get("rules", [])
    if not rules:
        return None

    matched_rules = []
    results = []
    candidate_rules = [rule for rule in rules if isinstance(rule, dict)]
    if source_id:
        candidate_rules = [
            rule for rule in candidate_rules
            if not rule.get("source_id") or str(rule.get("source_id")) == str(source_id)
        ]
    if source_kind:
        candidate_rules = [
            rule for rule in candidate_rules
            if _processing_rule_matches_kind(rule, source_kind, config)
        ]
    active_rules = [rule for rule in candidate_rules if rule.get("active")]
    if active_rules:
        candidate_rules = active_rules
    for rule in candidate_rules:
        if not isinstance(rule, dict):
            continue
        if not rule.get("enabled", True):
            continue
        if not _processing_rule_matches(rule, file_path, input_index):
            continue
        matched_rules.append(rule.get("id") or rule.get("name") or "rule")
        try:
            result = _run_processing_rule(file_path, rule, processing, now, input_index)
            results.append(result)
        except Exception as exc:
            _logger.error("⚠️ Ошибка обработки %s: %s", file_path, exc)
            results.append({"status": "error", "error": str(exc), "rule_id": rule.get("id")})

    if not matched_rules:
        return None

    return {
        "rules": matched_rules,
        "results": results,
        "source_id": source_id,
        "source_kind": source_kind,
        "file": str(file_path),
    }


def _processing_rule_matches_kind(
    rule: Dict[str, Any],
    source_kind: str,
    config: Dict[str, Any],
) -> bool:
    rule_kind = rule.get("source_kind")
    if rule_kind:
        return rule_kind == source_kind
    resolved_kind = _resolve_processing_rule_source_kind(rule, config)
    return resolved_kind == source_kind


def _resolve_processing_rule_source_kind(
    rule: Dict[str, Any],
    config: Dict[str, Any],
) -> str | None:
    source_id = rule.get("source_id")
    if not source_id:
        return None
    download_sources = config.get("download", {}).get("sources", [])
    mail_sources = config.get("mail", {}).get("sources", [])
    download_source = next(
        (item for item in download_sources if str(item.get("id")) == str(source_id)),
        None,
    )
    mail_source = next(
        (item for item in mail_sources if str(item.get("id")) == str(source_id)),
        None,
    )
    if download_source and not mail_source:
        return "download"
    if mail_source and not download_source:
        return "mail"
    if download_source and mail_source:
        source_file = str(rule.get("source_file") or "")
        if source_file and source_file == str(download_source.get("output_name") or ""):
            return "download"
        if source_file and source_file == str(mail_source.get("output_template") or ""):
            return "mail"
        rule_name = str(rule.get("name") or "")
        if rule_name and rule_name == str(download_source.get("name") or ""):
            return "download"
        if rule_name and rule_name == str(mail_source.get("name") or ""):
            return "mail"
    return None


def _processing_rule_matches(
    rule: Dict[str, Any],
    file_path: Path,
    input_index: int | None,
) -> bool:
    source_file = str(rule.get("source_file") or "").strip()
    if not source_file:
        return False
    target_name = file_path.name
    if source_file == target_name:
        return True
    rendered_source = _render_output_name_template(source_file, file_path, input_index)
    if rendered_source and rendered_source == target_name:
        return True
    template_pattern = _processing_rule_template_to_glob(source_file)
    if template_pattern != source_file and fnmatch(target_name, template_pattern):
        return True
    if any(char in source_file for char in ("*", "?", "[")):
        return fnmatch(target_name, source_file)
    return False


def _processing_rule_template_to_glob(source_file: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group("key")
        if key in ("index", "name", "filename"):
            return "*"
        return match.group(0)

    return re.sub(r"\{(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?::[^}]*)?\}", _replace, source_file)


def _run_processing_rule(
    file_path: Path,
    rule: Dict[str, Any],
    processing: Dict[str, Any],
    now: datetime,
    input_index: int | None,
) -> Dict[str, Any]:
    if not _normalize_requires_processing(rule.get("requires_processing", True)):
        _logger.info("🧩 Обработка не требуется для %s (%s)", file_path, rule.get("name") or rule.get("id"))
        return {"status": "skipped", "reason": "processing_disabled", "rule_id": rule.get("id")}

    table = _read_supplier_table(file_path)
    if not table:
        return {"status": "error", "error": "empty_table", "rule_id": rule.get("id")}

    data_row = int(rule.get("data_row") or 1)
    variants = rule.get("variants", [])
    results = []
    for variant in variants:
        variant_result = _process_variant(
            table,
            file_path,
            rule,
            variant,
            processing,
            now,
            data_row,
            input_index,
        )
        results.append(variant_result)

    return {"status": "success", "rule_id": rule.get("id"), "variants": results}


def _read_supplier_table(file_path: Path) -> list[list[str]]:
    suffix = file_path.suffix.lower().lstrip(".")
    if suffix == "csv":
        return _read_csv_table(file_path)
    if suffix in ("xlsx",):
        return _read_xlsx_table(file_path)
    if suffix in ("xls",):
        return _read_xls_table(file_path)
    raise ValueError(f"Неизвестный формат файла: {file_path.suffix}")


def _read_csv_table(file_path: Path) -> list[list[str]]:
    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        sample = file.read(2048)
        file.seek(0)
        delimiter = _guess_csv_delimiter(sample)
        reader = csv.reader(file, delimiter=delimiter)
        return [[str(value) for value in row] for row in reader]


def _guess_csv_delimiter(sample: str) -> str:
    if not sample:
        return ","
    comma = sample.count(",")
    semicolon = sample.count(";")
    tab = sample.count("\t")
    if semicolon > comma and semicolon >= tab:
        return ";"
    if tab > comma and tab > semicolon:
        return "\t"
    return ","


def _read_xlsx_table(file_path: Path) -> list[list[str]]:
    try:
        import openpyxl
    except ImportError as exc:
        raise ImportError("openpyxl не установлен для обработки xlsx") from exc
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    rows: list[list[str]] = []
    for row in sheet.iter_rows(values_only=True):
        rows.append([_normalize_cell(value) for value in row])
    return rows


def _read_xls_table(file_path: Path) -> list[list[str]]:
    try:
        import xlrd
    except ImportError as exc:
        if _looks_like_xlsx(file_path):
            _logger.warning(
                "⚠️ Файл %s имеет расширение .xls, но похож на xlsx. Используем openpyxl.",
                file_path.name,
            )
            return _read_xlsx_table(file_path)
        raise ImportError(
            "xlrd не установлен для обработки xls. Установите пакет xlrd или сохраните файл в формате xlsx."
        ) from exc
    try:
        workbook = xlrd.open_workbook(file_path)
    except xlrd.biffh.XLRDError:
        if _looks_like_xlsx(file_path):
            _logger.warning(
                "⚠️ Файл %s имеет расширение .xls, но похож на xlsx. Используем openpyxl.",
                file_path.name,
            )
            return _read_xlsx_table(file_path)
        raise
    sheet = workbook.sheet_by_index(0)
    rows: list[list[str]] = []
    for row_index in range(sheet.nrows):
        rows.append([_normalize_cell(sheet.cell_value(row_index, col)) for col in range(sheet.ncols)])
    return rows


def _looks_like_xlsx(file_path: Path) -> bool:
    try:
        with file_path.open("rb") as file:
            signature = file.read(4)
    except OSError:
        return False
    return signature in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def _normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return str(int(value))
    return str(value)


def _process_variant(
    table: list[list[str]],
    file_path: Path,
    rule: Dict[str, Any],
    variant: Dict[str, Any],
    processing: Dict[str, Any],
    now: datetime,
    data_row: int,
    input_index: int | None,
) -> Dict[str, Any]:
    article_col = int(variant.get("article_col") or 0)
    if article_col <= 0:
        return {"status": "error", "error": "invalid_article_col"}
    data_columns = variant.get("data_columns", [])
    output_names = variant.get("output_names", [])
    output_format = (variant.get("output_format") or "csv").lower()
    article_filter = variant.get("article_filter") or ""
    use_article_filter = variant.get("use_article_filter")
    if use_article_filter is None:
        use_article_filter = bool(article_filter)
    use_article_filter_columns = list(variant.get("use_article_filter_columns", []))
    if len(use_article_filter_columns) < len(data_columns):
        use_article_filter_columns.extend([True] * (len(data_columns) - len(use_article_filter_columns)))
    use_article_filter_columns = use_article_filter_columns[:len(data_columns)]
    article_prefix = variant.get("article_prefix") or ""
    article_postfix = variant.get("article_postfix") or ""
    orc_config = variant.get("orc", {}) if isinstance(variant.get("orc"), dict) else {}
    orc_enabled = bool(orc_config.get("enabled"))
    orc_column = int(orc_config.get("column") or 0)
    orc_target_column = orc_column if orc_column > 0 else (data_columns[0] if data_columns else 0)

    if len(data_columns) != len(output_names):
        return {"status": "error", "error": "columns_names_mismatch"}

    compiled_filter = None
    if use_article_filter and article_filter:
        try:
            compiled_filter = re.compile(article_filter)
        except re.error as exc:
            return {"status": "error", "error": f"invalid_filter: {exc}"}

    rows = table[data_row - 1:] if data_row > 1 else table
    outputs: list[Dict[str, Any]] = []
    for idx, (column_index, output_name) in enumerate(zip(data_columns, output_names)):
        rendered_output_name = _render_output_name_template(output_name, file_path, input_index)
        items: list[list[str]] = []
        orc_items: list[list[str]] = []
        orc_active = orc_enabled and column_index == orc_target_column
        use_filter_for_column = use_article_filter and (
            use_article_filter_columns[idx] if idx < len(use_article_filter_columns) else True
        )
        for row in rows:
            article_raw = _get_cell(row, article_col, preserve_whitespace=True)
            article = article_raw.strip()
            if not article:
                continue
            if compiled_filter and use_filter_for_column and not compiled_filter.search(article):
                continue
            quant_raw = _get_cell(row, column_index)
            quant_value = _parse_quantity(quant_raw)
            if quant_value is None:
                continue
            article_value = _apply_article_postfix(f"{article_prefix}{article_raw}", article_postfix)
            items.append([article_value, quant_value])
            if orc_active:
                orc_prefix = orc_config.get("prefix", "")
                stor = orc_config.get("stor", "")
                orc_column_index = orc_column if orc_column > 0 else column_index
                orc_quant_raw = _get_cell(row, orc_column_index)
                orc_quant_value = _parse_quantity(orc_quant_raw)
                if orc_quant_value is None:
                    continue
                date_text = now.strftime(processing.get("date_format", "%Y-%m-%d %H:%M"))
                orc_items.append([f"{orc_prefix}{article_raw}", stor, orc_quant_value, date_text])

        output_path = _resolve_output_path(file_path.parent, rendered_output_name, output_format)
        output_path = _write_output_file(output_path, output_format, ["Art.", "Quant."], items)

        orc_output = None
        if orc_active:
            orc_output_format = (orc_config.get("output_format") or output_format).lower()
            orc_output_path = _resolve_output_path(
                file_path.parent,
                _append_suffix_to_name(rendered_output_name, "_orc"),
                orc_output_format,
            )
            orc_output_path = _write_output_file(
                orc_output_path,
                orc_output_format,
                ["Art", "Stor", "Quant", "Date"],
                orc_items,
            )
            orc_output = str(orc_output_path)

        outputs.append(
            {
                "output": str(output_path),
                "orc_output": orc_output,
                "rows": len(items),
            }
        )

    return {"status": "success", "outputs": outputs}


def _get_cell(row: list[str], index: int, *, preserve_whitespace: bool = False) -> str:
    if index <= 0:
        return ""
    if index - 1 >= len(row):
        return ""
    value = row[index - 1]
    if value is None:
        return ""
    text = str(value)
    if preserve_whitespace:
        return text
    return text.strip()


def _parse_quantity(value: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    text = text.replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return None
    if number <= 0:
        return None
    if number.is_integer():
        return str(int(number))
    return str(number)


def _apply_article_postfix(article: str, postfix: str) -> str:
    if not postfix:
        return article
    if postfix[0].isspace() or article.endswith((" ", "\t")):
        return f"{article}{postfix}"
    return f"{article} {postfix}"


def _resolve_output_path(folder: Path, output_name: str, output_format: str) -> Path:
    name = output_name.strip()
    suffix = f".{output_format}"
    if not name:
        name = f"output{suffix}"
    if Path(name).suffix.lower() != suffix:
        name = f"{name}{suffix}"
    return folder / name


def _append_suffix_to_name(filename: str, suffix: str) -> str:
    path = Path(filename)
    return f"{path.stem}{suffix}{path.suffix}"


def _render_output_name_template(
    template: str,
    file_path: Path,
    input_index: int | None,
) -> str:
    if not template:
        return template
    values = {
        "index": input_index or 1,
        "name": file_path.stem,
        "filename": file_path.name,
    }
    try:
        return template.format(**values)
    except Exception:
        return template


def _write_output_file(path: Path, fmt: str, headers: list[str], rows: list[list[str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(headers)
            writer.writerows(rows)
        return path
    if fmt == "xlsx":
        if _write_xlsx(path, headers, rows):
            return path
        return _write_fallback_csv(path, headers, rows, fmt)
    if fmt == "xls":
        if _write_xls(path, headers, rows):
            return path
        xlsx_path = path.with_suffix(".xlsx")
        if _write_xlsx(xlsx_path, headers, rows):
            _logger.warning("⚠️ Запись xls недоступна, сохранено как %s", xlsx_path.name)
            return xlsx_path
        return _write_fallback_csv(path, headers, rows, fmt)
    raise ValueError(f"Неизвестный формат выходного файла: {fmt}")


def _write_xlsx(path: Path, headers: list[str], rows: list[list[str]]) -> bool:
    try:
        import openpyxl
    except ImportError as exc:
        _logger.warning("openpyxl не установлен для записи xlsx (%s)", exc)
        return False
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)
    return True


def _write_xls(path: Path, headers: list[str], rows: list[list[str]]) -> bool:
    try:
        import xlwt
    except ImportError as exc:
        _logger.warning("xlwt не установлен для записи xls (%s)", exc)
        return False
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet1")
    for col, header in enumerate(headers):
        sheet.write(0, col, header)
    for row_index, row in enumerate(rows, start=1):
        for col_index, value in enumerate(row):
            sheet.write(row_index, col_index, value)
    workbook.save(str(path))
    return True


def _write_fallback_csv(path: Path, headers: list[str], rows: list[list[str]], fmt: str) -> Path:
    fallback_path = path.with_suffix(".csv")
    _logger.warning("⚠️ Запись %s недоступна, сохранено как %s", fmt, fallback_path.name)
    return _write_output_file(fallback_path, "csv", headers, rows)


def _strip_archive_suffix(path: Path) -> str:
    name = path.name
    for suffix in (".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".zip", ".tar", ".gz", ".bz2", ".xz"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def unpack_archive_file(archive_path: Path) -> Path | None:
    if not archive_path.exists():
        return None
    extracted_path: Path | None = None
    try:
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as zip_file:
                members = [name for name in zip_file.namelist() if name and not name.endswith("/")]
                if not members:
                    return None
                member = members[0]
                extracted_path = Path(zip_file.extract(member, path=archive_path.parent))
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as tar_file:
                members = [member for member in tar_file.getmembers() if member.isfile()]
                if not members:
                    return None
                member = members[0]
                tar_file.extract(member, path=archive_path.parent)
                extracted_path = archive_path.parent / member.name
        else:
            return None

        if not extracted_path or not extracted_path.exists():
            return None

        base_name = _strip_archive_suffix(archive_path)
        new_name = f"{base_name}{extracted_path.suffix}" if extracted_path.suffix else base_name
        target_path = archive_path.with_name(new_name)
        if target_path.exists():
            target_path.unlink()
        extracted_path.replace(target_path)
        archive_path.unlink(missing_ok=True)
        return target_path
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
