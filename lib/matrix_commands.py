"""
/lib/matrix_commands.py
Server Monitoring System v8.61.25
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Incoming commands from Matrix (sync + router + ACL + audit).
Система мониторинга серверов
Версия: 8.61.25
Автор: Александр Суханов (c)
Лицензия: MIT
Входящие команды из Matrix (sync + router + ACL + аудит).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Dict, List, Optional, Set, Tuple
import sys

try:
    from nio import AsyncClient, MatrixRoom, RoomMessage, RoomMessageNotice, RoomMessageText
    _MATRIX_NIO_AVAILABLE = True
except ImportError:
    AsyncClient = None  # type: ignore[assignment]
    MatrixRoom = object  # type: ignore[assignment]
    RoomMessage = object  # type: ignore[assignment]
    RoomMessageNotice = object  # type: ignore[assignment]
    RoomMessageText = object  # type: ignore[assignment]
    _MATRIX_NIO_AVAILABLE = False

from lib.logging import debug_log, info_log
from core.task_router import run_availability_task
from modules.morning_report import morning_report


@dataclass
class MatrixACL:
    allowed_users: Set[str]
    allowed_room_ids: Set[str]

    def allows(self, user_id: str, room_id: str) -> bool:
        user_ok = (not self.allowed_users) or (user_id in self.allowed_users)
        room_ok = (not self.allowed_room_ids) or (room_id in self.allowed_room_ids)
        return user_ok and room_ok


class MatrixCommandBot:
    """Простой long-polling Matrix-бот на /sync."""

    def __init__(
        self,
        homeserver: str,
        access_token: str,
        room_id: str,
        whitelist_user_ids: Optional[List[str]] = None,
        allowed_room_ids: Optional[List[str]] = None,
    ) -> None:
        self.homeserver = (homeserver or "").rstrip("/")
        self.access_token = access_token or ""
        self.default_room_id = room_id or ""
        self.acl = MatrixACL(
            allowed_users={i.strip() for i in (whitelist_user_ids or []) if i and i.strip()},
            allowed_room_ids={i.strip() for i in (allowed_room_ids or []) if i and i.strip()},
        )
        self.client = AsyncClient(self.homeserver, user="")
        self.client.access_token = self.access_token
        self.client.add_event_callback(self._on_message, RoomMessageText)
        self.client.add_event_callback(self._on_message, RoomMessageNotice)
        self.client.add_event_callback(self._on_any_message, RoomMessage)
        self._started = False
        self._ignored_events_count = 0

    @property
    def enabled(self) -> bool:
        return bool(self.homeserver and self.access_token and self.default_room_id)

    async def _send_text(self, room_id: str, message: str) -> None:
        await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )

    def _audit(self, user_id: str, room_id: str, command: str, status: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        info_log(
            f"[MATRIX_AUDIT] ts={ts} user={user_id} room={room_id} command={command} status={status}"
        )

    async def _handle_status(self) -> str:
        ok, payload = run_availability_task(force_reload=True)
        if not ok:
            return "❌ Не удалось выполнить проверку статуса"
        up = len(payload.get("ok", []))
        down = payload.get("failed", [])
        lines = [f"📡 Статус мониторинга: доступно {up}, недоступно {len(down)}"]
        if down:
            lines.append("Проблемные серверы:")
            for item in down[:10]:
                lines.append(f"- {item.get('name', item.get('ip', 'unknown'))} ({item.get('ip', 'n/a')})")
        return "\n".join(lines)

    async def _handle_report(self) -> str:
        return morning_report.force_report()

    async def _handle_settings(self, command_text: str) -> str:
        help_text = (
            "⚙️ Доступные настройки в Matrix MVP:\n"
            "- !settings\n"
            "- !settings get <KEY>\n"
            "Пример: !settings get CHECK_INTERVAL"
        )
        parts = command_text.strip().split()
        if len(parts) < 3 or parts[1].lower() != "get":
            return help_text

        setting_key = parts[2].strip().upper()
        try:
            from core.config_manager import config_manager

            value = config_manager.get_setting(setting_key, None)
            if value is None:
                return f"❌ Настройка {setting_key} не найдена"
            return f"✅ {setting_key} = {value}"
        except Exception as exc:
            return f"❌ Ошибка чтения настройки: {exc}"

    def _control_menu_text(self) -> str:
        return (
            "🤖 Управление мониторингом (как в Telegram):\n"
            "• !start или !menu — открыть меню команд\n"
            "• !help — краткая справка по Matrix-командам\n"
            "• !status — текущий статус серверов\n"
            "• !report — сводный отчёт\n"
            "• !settings — справка по настройкам\n"
            "• !settings get <KEY> — значение настройки\n\n"
            "• !diag — диагностика Matrix command-bot\n"
            "• !ping — проверка отклика command-bot\n\n"
            "Пример: !settings get CHECK_INTERVAL"
        )

    def _format_diag(self, sender: str, room_id: str, command_text: str) -> str:
        acl_allowed = self.acl.allows(sender, room_id)
        bot_user_id = getattr(self.client, "user_id", "") or "unknown"
        return (
            "🩺 Matrix диагностика:\n"
            f"• bot_user_id: {bot_user_id}\n"
            f"• sender: {sender or 'unknown'}\n"
            f"• room_id: {room_id or 'unknown'}\n"
            f"• acl_allowed: {'yes' if acl_allowed else 'no'}\n"
            f"• allowed_users: {len(self.acl.allowed_users)}\n"
            f"• allowed_rooms: {len(self.acl.allowed_room_ids)}\n"
            f"• homeserver: {self.homeserver or 'empty'}\n"
            f"• command: {command_text or 'empty'}"
        )

    async def _route_command(self, command_text: str, sender: str, room_id: str) -> Tuple[str, str]:
        normalized = command_text.strip()
        command = normalized.split()[0].lower() if normalized else ""

        if command in {"!start", "!menu", "!help"}:
            return command, self._control_menu_text()
        if command == "!status":
            return command, await self._handle_status()
        if command == "!report":
            return command, await self._handle_report()
        if command == "!settings":
            return command, await self._handle_settings(normalized)
        if command == "!diag":
            return command, self._format_diag(sender=sender, room_id=room_id, command_text=normalized)
        if command == "!ping":
            return command, "🏓 pong"
        return command or "unknown", "ℹ️ Неизвестная команда. Напиши !menu для списка команд."

    def _extract_command(self, raw_body: str) -> str:
        body = (raw_body or "").replace("！", "!").strip()
        if not body:
            return ""

        if body.startswith("!"):
            return body

        for line in body.splitlines():
            clean = line.strip()
            if not clean or clean.startswith(">"):
                continue
            if clean.startswith("!"):
                return clean
            inline_command = re.search(r"(^|\s)(![a-z0-9_]+(?:\s+[^\n]+)?)", clean, flags=re.IGNORECASE)
            if inline_command:
                return inline_command.group(2).strip()

        return ""

    async def _should_ignore_event(self, event: RoomMessage, room_id: str) -> bool:
        sender = getattr(event, "sender", "") or ""
        raw_body = getattr(event, "body", "") or ""

        if sender == getattr(self.client, "user_id", None):
            normalized_body = (raw_body or "").replace("！", "!").lstrip()
            if not normalized_body.startswith("!"):
                debug_log(f"ℹ️ Matrix событие проигнорировано: echo от самого бота (room={room_id})")
                return True

            own_command = self._extract_command(raw_body)
            if not own_command.startswith("!"):
                debug_log(f"ℹ️ Matrix событие проигнорировано: echo от самого бота (room={room_id})")
                return True

            debug_log(
                f"ℹ️ Matrix self-command принят к обработке (room={room_id}, command='{own_command[:80]}')"
            )

        if "!" not in raw_body:
            self._ignored_events_count += 1
            if self._ignored_events_count <= 3 or self._ignored_events_count % 100 == 0:
                preview = raw_body.replace("\n", "\\n")[:200]
                debug_log(
                    "ℹ️ Matrix событие проигнорировано: в сообщении нет командного префикса "
                    f"(room={room_id}, sender={sender}, body='{preview}', ignored={self._ignored_events_count})"
                )
            return True

        return False


    async def _on_any_message(self, room: MatrixRoom, event: RoomMessage) -> None:
        """Диагностический callback для любых m.room.message-событий."""
        event_type = event.__class__.__name__
        sender = getattr(event, "sender", "") or "unknown"
        room_id = getattr(room, "room_id", "unknown")
        body = (getattr(event, "body", "") or "").replace("\n", "\\n")[:120]

        if isinstance(event, (RoomMessageText, RoomMessageNotice)):
            return

        debug_log(
            "ℹ️ Matrix событие получено (не text/notice): "
            f"type={event_type}, room={room_id}, sender={sender}, body='{body}'"
        )

    async def _on_message(self, room: MatrixRoom, event: RoomMessage) -> None:
        sender = event.sender or ""
        room_id = room.room_id

        if await self._should_ignore_event(event, room_id):
            return

        raw_body = getattr(event, "body", "") or ""
        body = self._extract_command(raw_body)
        if not body:
            preview = raw_body.replace("\n", "\\n")[:200]
            debug_log(
                "ℹ️ Matrix событие проигнорировано: команда не найдена "
                f"(room={getattr(room, 'room_id', 'unknown')}, sender={getattr(event, 'sender', 'unknown')}, body='{preview}')"
            )
            return

        info_log(
            "📩 Matrix команда получена: "
            f"room={room_id}, sender={sender}, command={body}"
        )

        if not self.acl.allows(sender, room_id):
            self._audit(sender, room_id, body, "denied")
            await self._send_text(room_id, "⛔ Доступ запрещён для этой комнаты/пользователя")
            return

        routed_command, response_text = await self._route_command(body, sender=sender, room_id=room_id)
        self._audit(sender, room_id, routed_command, "accepted")
        try:
            await self._send_text(room_id, response_text)
        except Exception as exc:
            debug_log(
                f"❌ Ошибка отправки Matrix-ответа (room={room_id}, sender={sender}, command={body}): {exc}"
            )
            raise

    async def run_forever(self) -> None:
        if not self.enabled:
            debug_log(
                "ℹ️ Matrix command bot отключён: не хватает MATRIX_* параметров "
                f"(homeserver={'ok' if self.homeserver else 'empty'}, "
                f"token={'ok' if self.access_token else 'empty'}, "
                f"room_id={'ok' if self.default_room_id else 'empty'})"
            )
            return

        info_log(
            "🚀 Matrix command bot запущен: "
            f"homeserver={self.homeserver}, default_room={self.default_room_id or 'empty'}, "
            f"allowed_users={len(self.acl.allowed_users)}, allowed_rooms={len(self.acl.allowed_room_ids)}"
        )

        if not self._started:
            try:
                whoami = await self.client.whoami()
                user_id = getattr(whoami, "user_id", None)
                if user_id:
                    self.client.user_id = user_id
                    debug_log(f"✅ Matrix whoami: user_id={user_id}")
            except Exception as exc:
                debug_log(f"⚠️ Matrix whoami failed: {exc}")

            try:
                await self.client.sync(timeout=3000, full_state=True)
                self._started = True
            except Exception as exc:
                debug_log(f"❌ Matrix initial sync failed: {exc}")

        while True:
            try:
                await self.client.sync(timeout=30000)
            except Exception as exc:
                debug_log(f"⚠️ Matrix sync loop error: {exc}")
                await asyncio.sleep(3)


def run_matrix_command_bot(**kwargs) -> None:
    """Синхронная обёртка для запуска в отдельном потоке."""
    if not _MATRIX_NIO_AVAILABLE:
        info_log(
            "Matrix command sync пропущен: dependency matrix-nio не установлена для текущего интерпретатора "
            f"{sys.executable}. Установи так: {sys.executable} -m pip install 'matrix-nio[e2e]'."
        )
        return

    bot = MatrixCommandBot(**kwargs)
    asyncio.run(bot.run_forever())
