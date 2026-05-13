"""
/lib/matrix_commands.py
Server Monitoring System v8.60.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Incoming commands from Matrix (sync + router + ACL + audit).
Система мониторинга серверов
Версия: 8.60.4
Автор: Александр Суханов (c)
Лицензия: MIT
Входящие команды из Matrix (sync + router + ACL + аудит).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from nio import AsyncClient, MatrixRoom, RoomMessageText

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
        self._started = False

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

    async def _route_command(self, command_text: str) -> str:
        normalized = command_text.strip()
        if normalized.startswith("!status"):
            return await self._handle_status()
        if normalized.startswith("!report"):
            return await self._handle_report()
        if normalized.startswith("!settings"):
            return await self._handle_settings(normalized)
        return "ℹ️ Неизвестная команда. Доступно: !status, !report, !settings"

    def _extract_command(self, raw_body: str) -> str:
        body = (raw_body or "").strip()
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

        return ""

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText) -> None:
        body = self._extract_command(event.body or "")
        if not body:
            return

        sender = event.sender or ""
        room_id = room.room_id

        if sender == getattr(self.client, "user_id", None):
            return

        if not self.acl.allows(sender, room_id):
            self._audit(sender, room_id, body, "denied")
            await self._send_text(room_id, "⛔ Доступ запрещён для этой комнаты/пользователя")
            return

        self._audit(sender, room_id, body, "accepted")
        response_text = await self._route_command(body)
        await self._send_text(room_id, response_text)

    async def run_forever(self) -> None:
        if not self.enabled:
            debug_log("ℹ️ Matrix command bot отключён: не хватает MATRIX_* параметров")
            return

        if not self._started:
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
    bot = MatrixCommandBot(**kwargs)
    asyncio.run(bot.run_forever())
