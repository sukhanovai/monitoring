"""
TamTam bot integration for monitoring controls.
"""

import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from lib.logging import setup_logging

_logger = setup_logging("tamtam")


@dataclass
class TamTamConfig:
    token: str
    chat_ids: list[str]
    api_base: str = "https://botapi.tamtam.chat"


def _get_monitor():
    from core.monitor import monitor

    return monitor


def _run_task(task_name: str, **kwargs):
    from core.task_router import run_task

    return run_task(task_name, **kwargs)


def _set_silent_override(enabled: bool) -> None:
    from lib.alerts import set_silent_override

    set_silent_override(enabled)


class TamTamBotService:
    def __init__(self, config: TamTamConfig):
        self.config = config
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._marker: Optional[int] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="tamtam-poller")
        self._thread.start()
        _logger.info("✅ TamTam бот запущен")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def send_message(self, chat_id: str, text: str) -> bool:
        try:
            # TamTam Bot API ожидает chat_id в query-параметрах.
            self._request(
                "/messages",
                {"text": text},
                method="POST",
                query_params={"chat_id": str(chat_id)},
            )
            return True
        except Exception as exc:
            _logger.warning(f"⚠️ TamTam: ошибка отправки в чат {chat_id}: {exc}")
            return False

    def broadcast(self, text: str) -> bool:
        sent = 0
        for chat_id in self.config.chat_ids:
            if self.send_message(str(chat_id), text):
                sent += 1
        return sent > 0

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                updates = self._get_updates()
                for update in updates:
                    self._handle_update(update)
            except Exception as exc:
                _logger.warning(f"⚠️ TamTam poll error: {exc}")
                time.sleep(3)
            time.sleep(1)

    def _get_updates(self) -> Iterable[Dict[str, Any]]:
        params = {"limit": 100, "timeout": 25}
        if self._marker is not None:
            params["marker"] = self._marker

        data = self._request("/updates", params, method="GET")
        self._marker = data.get("marker", self._marker)
        return data.get("updates", [])

    def _handle_update(self, update: Dict[str, Any]) -> None:
        body = update.get("message") or {}
        sender = body.get("sender", {})
        recipient = body.get("recipient", {})
        text = (body.get("body", {}) or {}).get("text", "").strip()
        chat_id = str(recipient.get("chat_id", ""))
        user_id = str(sender.get("user_id", ""))

        if not text:
            return
        if self.config.chat_ids and chat_id not in {str(c) for c in self.config.chat_ids}:
            return

        reply = handle_tamtam_command(text, user_id=user_id)
        if reply:
            self.send_message(chat_id, reply)

    def _request(
        self,
        path: str,
        params: Dict[str, Any],
        method: str = "POST",
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if method.upper() == "GET":
            query_params = {"access_token": self.config.token, **params}
            url = f"{self.config.api_base}{path}?{urlencode(query_params)}"
            req = Request(url, method="GET")
        else:
            query = urlencode({"access_token": self.config.token, **(query_params or {})})
            url = f"{self.config.api_base}{path}?{query}"
            data = json.dumps(params).encode("utf-8")
            req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urlopen(req, timeout=30) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload) if payload else {}
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
            raise RuntimeError(f"HTTP {exc.code}: {details or exc.reason}") from exc


def _format_availability(payload: Dict[str, Any]) -> str:
    up = len(payload.get("up", []))
    down = payload.get("down", [])
    lines = [f"📡 Доступность: {up} доступно, {len(down)} недоступно"]
    for server in down[:10]:
        lines.append(f"- {server.get('name', server.get('ip', ''))} ({server.get('ip', '')})")
    return "\n".join(lines)


def _format_resources(payload: Dict[str, Any]) -> str:
    stats = payload.get("stats", {})
    return (
        "📊 Ресурсы: "
        f"{stats.get('success', 0)}/{stats.get('total', 0)} успешно, "
        f"{stats.get('failed', 0)} ошибок"
    )


def handle_tamtam_command(text: str, user_id: str = "") -> str:
    cmd, *rest = text.split(maxsplit=1)
    arg = rest[0] if rest else ""

    if cmd in {"/start", "/help"}:
        return (
            "Команды TamTam:\n"
            "/status — состояние мониторинга\n"
            "/check — проверка доступности\n"
            "/resources — проверка ресурсов\n"
            "/check_server <IP|имя> — точечная проверка\n"
            "/monitor_on | /monitor_off\n"
            "/silent_on | /silent_off"
        )

    if cmd == "/status":
        return (
            f"🎛 Мониторинг: {'включен' if _get_monitor().monitoring_active else 'выключен'}\n"
            f"Серверов в памяти: {len(_get_monitor().servers)}"
        )

    if cmd == "/check":
        success, payload = _run_task("availability", force_reload=True)
        return _format_availability(payload) if success else str(payload)

    if cmd == "/resources":
        success, payload = _run_task("resources", force_reload=True)
        return _format_resources(payload) if success else str(payload)

    if cmd == "/check_server":
        if not arg:
            return "❌ Укажите IP или имя: /check_server 192.168.1.10"
        success, payload = _run_task("targeted_checks", server_id=arg, mode="availability")
        if not success:
            return str(payload)
        return payload.get("message", "Нет данных")

    if cmd == "/monitor_on":
        _get_monitor().monitoring_active = True
        return "✅ Мониторинг включен"

    if cmd == "/monitor_off":
        _get_monitor().monitoring_active = False
        return "⏸ Мониторинг выключен"

    if cmd == "/silent_on":
        _set_silent_override(True)
        return "🔕 Тихий режим принудительно включен"

    if cmd == "/silent_off":
        _set_silent_override(False)
        return "🔔 Тихий режим принудительно отключен"

    return "Неизвестная команда. Используйте /help"
