"""
/lib/matrix_commands.py
Server Monitoring System v8.61.29
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Incoming commands from Matrix (sync + router + ACL + audit + reaction buttons).
Система мониторинга серверов
Версия: 8.61.29
Автор: Александр Суханов (c)
Лицензия: MIT
Входящие команды из Matrix (sync + router + ACL + аудит + кнопки-реакции).
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Dict, List, Optional, Set, Tuple
import sys

try:
    from nio import (
        AsyncClient,
        MatrixRoom,
        RoomMessage,
        RoomMessageNotice,
        RoomMessageText,
    )
    _MATRIX_NIO_AVAILABLE = True
except ImportError:
    AsyncClient = None  # type: ignore[assignment]
    MatrixRoom = object  # type: ignore[assignment]
    RoomMessage = object  # type: ignore[assignment]
    RoomMessageNotice = object  # type: ignore[assignment]
    RoomMessageText = object  # type: ignore[assignment]
    _MATRIX_NIO_AVAILABLE = False

try:
    from nio import ReactionEvent  # type: ignore[attr-defined]
    _MATRIX_REACTION_EVENT_AVAILABLE = True
except ImportError:
    ReactionEvent = object  # type: ignore[assignment]
    _MATRIX_REACTION_EVENT_AVAILABLE = False

try:
    from nio import UnknownEvent  # type: ignore[attr-defined]
    _MATRIX_UNKNOWN_EVENT_AVAILABLE = True
except ImportError:
    UnknownEvent = object  # type: ignore[assignment]
    _MATRIX_UNKNOWN_EVENT_AVAILABLE = False

from lib.logging import debug_log, info_log
from core.task_router import (
    run_availability_task,
    run_resources_task,
    run_targeted_task,
    get_monitoring_servers,
)
from modules.morning_report import morning_report


# Кнопки меню как в Telegram: emoji-реакция -> команда.
# Реакции работают в Element, Element X и web-клиенте Matrix.
MENU_BUTTONS: List[Tuple[str, str]] = [
    ("📡", "!status"),
    ("📊", "!resources"),
    ("🌅", "!report"),
    ("🖥️", "!servers"),
    ("⏸️", "!pause"),
    ("▶️", "!resume"),
    ("🔇", "!silent"),
    ("🔊", "!loud"),
    ("🔄", "!auto"),
    ("ℹ️", "!about"),
]
_BUTTON_BY_EMOJI: Dict[str, str] = {emoji: command for emoji, command in MENU_BUTTONS}


@dataclass
class MatrixACL:
    allowed_users: Set[str]
    allowed_room_ids: Set[str]

    def allows(self, user_id: str, room_id: str) -> bool:
        user_ok = (not self.allowed_users) or (user_id in self.allowed_users)
        room_ok = (not self.allowed_room_ids) or (room_id in self.allowed_room_ids)
        return user_ok and room_ok


class MatrixCommandBot:
    """Простой long-polling Matrix-бот на /sync с кнопками-реакциями."""

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
        if _MATRIX_REACTION_EVENT_AVAILABLE:
            self.client.add_event_callback(self._on_reaction, ReactionEvent)
        if _MATRIX_UNKNOWN_EVENT_AVAILABLE:
            self.client.add_event_callback(self._on_unknown_event, UnknownEvent)
        self._started = False
        self._ignored_events_count = 0
        # event_id меню-сообщений (для маппинга реакций на команды)
        self._menu_event_ids: "OrderedDict[str, str]" = OrderedDict()
        # уже обработанные реакции (защита от повторной доставки в sync)
        self._processed_reactions: "OrderedDict[str, bool]" = OrderedDict()

    @property
    def enabled(self) -> bool:
        return bool(self.homeserver and self.access_token and self.default_room_id)

    @staticmethod
    def _cap_ordered(store: "OrderedDict", max_items: int) -> None:
        while len(store) > max_items:
            store.popitem(last=False)

    async def _send_text(self, room_id: str, message: str) -> Optional[str]:
        response = await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
        )
        return getattr(response, "event_id", None)

    async def _send_reaction(self, room_id: str, target_event_id: str, key: str) -> None:
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.reaction",
                content={
                    "m.relates_to": {
                        "rel_type": "m.annotation",
                        "event_id": target_event_id,
                        "key": key,
                    }
                },
            )
        except Exception as exc:
            debug_log(f"⚠️ Не удалось добавить Matrix-реакцию '{key}': {exc}")

    async def _post_menu(self, room_id: str, text: str) -> None:
        """Отправляет меню и навешивает кнопки-реакции на это сообщение."""
        event_id = await self._send_text(room_id, text)
        if not event_id:
            debug_log("⚠️ Matrix меню отправлено без event_id: кнопки-реакции пропущены")
            return

        self._menu_event_ids[event_id] = room_id
        self._cap_ordered(self._menu_event_ids, 50)

        for emoji, _command in MENU_BUTTONS:
            await self._send_reaction(room_id, event_id, emoji)

    def _audit(self, user_id: str, room_id: str, command: str, status: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        info_log(
            f"[MATRIX_AUDIT] ts={ts} user={user_id} room={room_id} command={command} status={status}"
        )

    # ------------------------------------------------------------------
    # Обработчики команд (переиспользуют backend, без Telegram-объектов)
    # ------------------------------------------------------------------
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

    async def _handle_resources_all(self) -> str:
        try:
            ok, payload = run_resources_task(force_reload=True)
        except Exception as exc:
            return f"❌ Ошибка проверки ресурсов: {str(exc)[:160]}"
        if not ok:
            return "❌ Не удалось выполнить проверку ресурсов"

        results = payload.get("results", [])
        stats = payload.get("stats", {})
        lines = [
            "📊 Ресурсы серверов: "
            f"всего {stats.get('total', len(results))}, "
            f"успешно {stats.get('success', 0)}, "
            f"ошибок {stats.get('failed', 0)}"
        ]
        shown = 0
        for item in results:
            if shown >= 15:
                lines.append("…")
                break
            server = item.get("server", {}) or {}
            name = server.get("name", server.get("ip", "unknown"))
            res = item.get("resources") or {}
            if item.get("success") and res:
                lines.append(
                    f"• {name}: CPU {res.get('cpu', 0)}% / "
                    f"RAM {res.get('ram', 0)}% / Disk {res.get('disk', 0)}%"
                )
            else:
                lines.append(f"• {name}: ❌ нет данных")
            shown += 1
        return "\n".join(lines)

    async def _handle_targeted(self, command_text: str, mode: str) -> str:
        parts = command_text.strip().split(maxsplit=1)
        arg = parts[1].strip() if len(parts) > 1 else ""

        if not arg:
            if mode == "resources":
                return await self._handle_resources_all()
            return await self._handle_status()

        try:
            ok, payload = run_targeted_task(server_id=arg, mode=mode)
        except Exception as exc:
            return f"❌ Ошибка проверки '{arg}': {str(exc)[:160]}"

        if isinstance(payload, str):
            return payload
        message = (payload or {}).get("message")
        if message:
            return message
        return "✅ Проверка выполнена" if ok else "❌ Проверка завершилась с ошибкой"

    async def _handle_servers(self) -> str:
        try:
            servers = get_monitoring_servers(force_reload=True)
        except Exception as exc:
            return f"❌ Ошибка загрузки списка серверов: {str(exc)[:160]}"
        if not servers:
            return "ℹ️ Список серверов пуст"

        lines = [f"🖥️ Серверы под мониторингом: {len(servers)}"]
        for server in servers[:40]:
            name = server.get("name", "unknown")
            ip = server.get("ip", "n/a")
            stype = server.get("type", "?")
            enabled = server.get("enabled", True)
            flag = "🟢" if enabled else "⚪"
            lines.append(f"{flag} {name} ({ip}) [{stype}]")
        if len(servers) > 40:
            lines.append(f"… и ещё {len(servers) - 40}")
        return "\n".join(lines)

    async def _handle_report(self) -> str:
        return morning_report.force_report()

    @staticmethod
    def _set_monitoring_active(active: bool) -> None:
        import core.monitor_core as monitor_core

        monitor_core.monitoring_active = active

    @staticmethod
    def _is_monitoring_active() -> bool:
        try:
            import core.monitor_core as monitor_core

            return bool(getattr(monitor_core, "monitoring_active", True))
        except Exception:
            return True

    async def _handle_pause(self) -> str:
        self._set_monitoring_active(False)
        try:
            from lib.alerts import send_alert

            send_alert(
                "🔴 *Мониторинг приостановлен*\nРегулярные проверки серверов отключены.",
                force=True,
            )
        except Exception as exc:
            debug_log(f"⚠️ Не удалось отправить алерт о паузе: {exc}")
        return "⏸️ Мониторинг приостановлен. Уведомления о регулярных проверках не отправляются."

    async def _handle_resume(self) -> str:
        self._set_monitoring_active(True)
        try:
            from lib.alerts import send_alert

            send_alert(
                "🟢 *Мониторинг возобновлён*\nРегулярные проверки серверов активированы.",
                force=True,
            )
        except Exception as exc:
            debug_log(f"⚠️ Не удалось отправить алерт о возобновлении: {exc}")
        return "▶️ Мониторинг возобновлён. Регулярные проверки активны."

    @staticmethod
    def _silent_schedule() -> Tuple[int, int]:
        for module_name in ("config.db_settings", "config.settings"):
            try:
                module = __import__(module_name, fromlist=["SILENT_START", "SILENT_END"])
                start = getattr(module, "SILENT_START", None)
                end = getattr(module, "SILENT_END", None)
                if start is not None and end is not None:
                    return int(start), int(end)
            except Exception:
                continue
        return 20, 9

    async def _handle_silent_mode(self, override: Optional[bool]) -> str:
        try:
            from lib.alerts import set_silent_override

            set_silent_override(override)
        except Exception as exc:
            return f"❌ Не удалось изменить тихий режим: {str(exc)[:160]}"

        if override is True:
            return "🔇 Принудительный тихий режим включён. Уведомления отключены до смены режима."
        if override is False:
            return "🔊 Принудительный громкий режим включён. Все уведомления активны."
        return "🔄 Возвращён автоматический режим тихого периода (по расписанию)."

    async def _handle_mode_status(self) -> str:
        try:
            from lib.alerts import get_silent_override, is_silent_time

            override = get_silent_override()
            silent_now = is_silent_time()
        except Exception as exc:
            return f"❌ Не удалось получить статус режима: {str(exc)[:160]}"

        if override is None:
            mode_text = "🔄 автоматический (по расписанию)"
        elif override:
            mode_text = "🔇 принудительно тихий"
        else:
            mode_text = "🔊 принудительно громкий"

        start, end = self._silent_schedule()
        monitoring = "🟢 активен" if self._is_monitoring_active() else "🔴 приостановлен"
        notify = "🔴 отключены (тихо)" if silent_now else "🟢 включены (громко)"
        return (
            "🎛️ Состояние управления:\n"
            f"• Мониторинг: {monitoring}\n"
            f"• Режим уведомлений: {mode_text}\n"
            f"• Сейчас уведомления: {notify}\n"
            f"• Расписание тихого режима: {start}:00 – {end}:00"
        )

    async def _handle_about(self) -> str:
        version = "n/a"
        for module_name in ("config.settings", "config.db_settings"):
            try:
                module = __import__(module_name, fromlist=["APP_VERSION"])
                version = getattr(module, "APP_VERSION", version)
                if version != "n/a":
                    break
            except Exception:
                continue
        return (
            "ℹ️ Система мониторинга серверов\n"
            f"• Версия: {version}\n"
            "• Автор: Александр Суханов\n"
            "• Канал: Matrix command-bot (паритет с Telegram)\n"
            "Напиши !menu для списка команд и кнопок."
        )

    async def _handle_settings(self, command_text: str) -> str:
        help_text = (
            "⚙️ Доступные настройки в Matrix:\n"
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
            "🤖 Управление мониторингом (паритет с Telegram).\n"
            "Жми кнопки-реакции под этим сообщением или пиши команды:\n\n"
            "📡 !status — доступность всех серверов\n"
            "📊 !resources — ресурсы всех серверов\n"
            "🌅 !report — утренний/сводный отчёт\n"
            "🖥️ !servers — список серверов под мониторингом\n"
            "⏸️ !pause — приостановить мониторинг\n"
            "▶️ !resume — возобновить мониторинг\n"
            "🔇 !silent — принудительно тихий режим\n"
            "🔊 !loud — принудительно громкий режим\n"
            "🔄 !auto — авто тихий режим по расписанию\n"
            "ℹ️ !about — версия и сведения о боте\n\n"
            "Команды с аргументом:\n"
            "• !check <имя|ip> — проверить один сервер\n"
            "• !res <имя|ip> — ресурсы одного сервера\n"
            "• !settings get <KEY> — значение настройки\n"
            "• !mode — текущее состояние управления\n"
            "• !diag / !ping — диагностика command-bot"
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
            f"• reaction_buttons: {'yes' if _MATRIX_REACTION_EVENT_AVAILABLE else 'no'}\n"
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
        if command == "!resources":
            return command, await self._handle_resources_all()
        if command == "!report":
            return command, await self._handle_report()
        if command == "!servers" or command == "!list":
            return command, await self._handle_servers()
        if command == "!check":
            return command, await self._handle_targeted(normalized, mode="availability")
        if command == "!res":
            return command, await self._handle_targeted(normalized, mode="resources")
        if command == "!pause":
            return command, await self._handle_pause()
        if command == "!resume":
            return command, await self._handle_resume()
        if command == "!silent":
            return command, await self._handle_silent_mode(True)
        if command == "!loud":
            return command, await self._handle_silent_mode(False)
        if command == "!auto":
            return command, await self._handle_silent_mode(None)
        if command == "!mode":
            return command, await self._handle_mode_status()
        if command == "!about":
            return command, await self._handle_about()
        if command == "!settings":
            return command, await self._handle_settings(normalized)
        if command == "!diag":
            return command, self._format_diag(sender=sender, room_id=room_id, command_text=normalized)
        if command == "!ping":
            return command, "🏓 pong"
        return command or "unknown", "ℹ️ Неизвестная команда. Напиши !menu для списка команд."

    def _extract_command(self, raw_body: str, *, allow_inline: bool = True) -> str:
        body = (raw_body or "").replace("！", "!").strip()
        if not body:
            return ""

        if body.startswith("!"):
            if len(re.findall(r"![a-z0-9_]+", body, flags=re.IGNORECASE)) > 1:
                return ""
            return body

        for line in body.splitlines():
            clean = line.strip()
            if not clean or clean.startswith(">"):
                continue
            if clean.startswith("!"):
                return clean
            if allow_inline:
                inline_command = re.search(r"(^|\s)(![a-z0-9_]+(?:\s+[^\n]+)?)", clean, flags=re.IGNORECASE)
                if inline_command:
                    return inline_command.group(2).strip()

        return ""

    async def _should_ignore_event(self, event: RoomMessage, room_id: str) -> bool:
        sender = getattr(event, "sender", "") or ""
        raw_body = getattr(event, "body", "") or ""

        if sender == getattr(self.client, "user_id", None):
            own_command = self._extract_command(raw_body, allow_inline=False)
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

    async def _dispatch_and_reply(self, command_text: str, sender: str, room_id: str) -> None:
        if not self.acl.allows(sender, room_id):
            self._audit(sender, room_id, command_text, "denied")
            await self._send_text(room_id, "⛔ Доступ запрещён для этой комнаты/пользователя")
            return

        routed_command, response_text = await self._route_command(
            command_text, sender=sender, room_id=room_id
        )
        self._audit(sender, room_id, routed_command, "accepted")
        try:
            if routed_command in {"!start", "!menu", "!help"}:
                await self._post_menu(room_id, response_text)
            else:
                await self._send_text(room_id, response_text)
        except Exception as exc:
            debug_log(
                f"❌ Ошибка отправки Matrix-ответа (room={room_id}, sender={sender}, "
                f"command={command_text}): {exc}"
            )
            raise

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
                f"(room={getattr(room, 'room_id', 'unknown')}, "
                f"sender={getattr(event, 'sender', 'unknown')}, body='{preview}')"
            )
            return

        info_log(
            "📩 Matrix команда получена: "
            f"room={room_id}, sender={sender}, command={body}"
        )
        await self._dispatch_and_reply(body, sender=sender, room_id=room_id)

    def _reaction_target_and_key(self, event) -> Tuple[str, str]:
        """Достаёт (target_event_id, emoji) из ReactionEvent или UnknownEvent."""
        target = getattr(event, "reacts_to", "") or ""
        key = getattr(event, "key", "") or ""
        if target and key:
            return target, key

        source = getattr(event, "source", None) or {}
        content = (source.get("content") or {}) if isinstance(source, dict) else {}
        relates = content.get("m.relates_to") or {}
        return relates.get("event_id", "") or "", relates.get("key", "") or ""

    async def _process_reaction(self, room: MatrixRoom, event) -> None:
        sender = getattr(event, "sender", "") or ""
        room_id = getattr(room, "room_id", "") or self.default_room_id
        reaction_event_id = getattr(event, "event_id", "") or ""

        if sender and sender == getattr(self.client, "user_id", None):
            return

        if reaction_event_id and reaction_event_id in self._processed_reactions:
            return

        target_event_id, key = self._reaction_target_and_key(event)
        if not target_event_id or target_event_id not in self._menu_event_ids:
            return

        command = _BUTTON_BY_EMOJI.get(key)
        if not command:
            normalized_key = (key or "").strip()
            command = _BUTTON_BY_EMOJI.get(normalized_key)
        if not command:
            debug_log(
                f"ℹ️ Matrix реакция без сопоставленной кнопки (key='{key}', room={room_id})"
            )
            return

        if reaction_event_id:
            self._processed_reactions[reaction_event_id] = True
            self._cap_ordered(self._processed_reactions, 500)

        info_log(
            "📩 Matrix кнопка нажата: "
            f"room={room_id}, sender={sender}, key={key}, command={command}"
        )
        await self._dispatch_and_reply(command, sender=sender, room_id=room_id)

    async def _on_reaction(self, room: MatrixRoom, event) -> None:
        try:
            await self._process_reaction(room, event)
        except Exception as exc:
            debug_log(f"❌ Ошибка обработки Matrix-реакции: {exc}")

    async def _on_unknown_event(self, room: MatrixRoom, event) -> None:
        # Fallback для сборок nio без отдельного ReactionEvent.
        if _MATRIX_REACTION_EVENT_AVAILABLE:
            return
        if getattr(event, "type", "") != "m.reaction":
            return
        try:
            await self._process_reaction(room, event)
        except Exception as exc:
            debug_log(f"❌ Ошибка обработки Matrix-реакции (unknown): {exc}")

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
            f"allowed_users={len(self.acl.allowed_users)}, allowed_rooms={len(self.acl.allowed_room_ids)}, "
            f"reaction_buttons={'on' if _MATRIX_REACTION_EVENT_AVAILABLE else 'fallback'}"
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
