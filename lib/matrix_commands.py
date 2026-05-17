"""
/lib/matrix_commands.py
Server Monitoring System v8.61.29
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Incoming commands from Matrix (sync + router + ACL + audit + reaction buttons + E2EE).
Система мониторинга серверов
Версия: 8.61.29
Автор: Александр Суханов (c)
Лицензия: MIT
Входящие команды из Matrix (sync + router + ACL + аудит + кнопки-реакции + E2EE).
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import re
from typing import Dict, List, Optional, Set, Tuple
import sys

try:
    from nio import (
        AsyncClient,
        AsyncClientConfig,
        LoginResponse,
        MatrixRoom,
        RoomMessage,
        RoomMessageNotice,
        RoomMessageText,
    )
    _MATRIX_NIO_AVAILABLE = True
except ImportError:
    AsyncClient = None  # type: ignore[assignment]
    AsyncClientConfig = None  # type: ignore[assignment]
    LoginResponse = object  # type: ignore[assignment]
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

try:
    from nio import MegolmEvent  # type: ignore[attr-defined]
    _MATRIX_MEGOLM_EVENT_AVAILABLE = True
except ImportError:
    MegolmEvent = object  # type: ignore[assignment]
    _MATRIX_MEGOLM_EVENT_AVAILABLE = False

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
    """Long-polling Matrix-бот на /sync с кнопками-реакциями и E2EE."""

    def __init__(
        self,
        homeserver: str,
        access_token: str,
        room_id: str,
        whitelist_user_ids: Optional[List[str]] = None,
        allowed_room_ids: Optional[List[str]] = None,
        bot_user_id: str = "",
        bot_password: str = "",
        store_path: str = "",
        device_name: str = "monitoring-command-bot",
    ) -> None:
        self.homeserver = (homeserver or "").rstrip("/")
        self.access_token = access_token or ""
        self.default_room_id = room_id or ""
        self.bot_user_id = (bot_user_id or "").strip()
        self.bot_password = bot_password or ""
        self.store_path = (store_path or "").strip()
        self.device_name = device_name or "monitoring-command-bot"
        self.acl = MatrixACL(
            allowed_users={i.strip() for i in (whitelist_user_ids or []) if i and i.strip()},
            allowed_room_ids={i.strip() for i in (allowed_room_ids or []) if i and i.strip()},
        )
        self.client: Optional[AsyncClient] = None
        self._e2e_enabled = False
        self._started = False
        self._ignored_events_count = 0
        # event_id меню-сообщений (для маппинга реакций на команды)
        self._menu_event_ids: "OrderedDict[str, str]" = OrderedDict()
        # уже обработанные реакции (защита от повторной доставки в sync)
        self._processed_reactions: "OrderedDict[str, bool]" = OrderedDict()
        # event_id собственных исходящих сообщений: защита от петли, когда
        # бот залогинен под тем же MXID, что и человек (ответ бота не должен
        # повторно маршрутизироваться как команда)
        self._sent_event_ids: "OrderedDict[str, bool]" = OrderedDict()

    @property
    def enabled(self) -> bool:
        return bool(self.homeserver and self.default_room_id and (
            self.access_token or (self.bot_user_id and self.bot_password)
        ))

    @property
    def _credentials_file(self) -> str:
        return os.path.join(self.store_path, "credentials.json")

    @staticmethod
    def _cap_ordered(store: "OrderedDict", max_items: int) -> None:
        while len(store) > max_items:
            store.popitem(last=False)

    # ------------------------------------------------------------------
    # Создание клиента: E2EE (login+store) или legacy (token-only)
    # ------------------------------------------------------------------
    def _load_saved_credentials(self) -> Optional[Dict[str, str]]:
        try:
            with open(self._credentials_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("user_id") and data.get("device_id") and data.get("access_token"):
                return data
        except FileNotFoundError:
            return None
        except Exception as exc:
            debug_log(f"⚠️ Не удалось прочитать Matrix credentials: {exc}")
        return None

    def _save_credentials(self, user_id: str, device_id: str, access_token: str) -> None:
        try:
            os.makedirs(self.store_path, exist_ok=True)
            with open(self._credentials_file, "w", encoding="utf-8") as fh:
                json.dump(
                    {"user_id": user_id, "device_id": device_id, "access_token": access_token},
                    fh,
                )
            try:
                os.chmod(self._credentials_file, 0o600)
            except OSError:
                pass
        except Exception as exc:
            debug_log(f"⚠️ Не удалось сохранить Matrix credentials: {exc}")

    def _register_callbacks(self) -> None:
        self.client.add_event_callback(self._on_message, RoomMessageText)
        self.client.add_event_callback(self._on_message, RoomMessageNotice)
        self.client.add_event_callback(self._on_any_message, RoomMessage)
        if _MATRIX_REACTION_EVENT_AVAILABLE:
            self.client.add_event_callback(self._on_reaction, ReactionEvent)
        if _MATRIX_UNKNOWN_EVENT_AVAILABLE:
            self.client.add_event_callback(self._on_unknown_event, UnknownEvent)
        if _MATRIX_MEGOLM_EVENT_AVAILABLE:
            self.client.add_event_callback(self._on_undecrypted, MegolmEvent)

    async def _setup_client(self) -> bool:
        """Готовит клиент. Возвращает True, если можно запускать sync."""
        want_e2e = bool(self.bot_password and self.bot_user_id and self.store_path)

        if not want_e2e:
            # Legacy-режим: только token (работает для НЕзашифрованных комнат).
            self.client = AsyncClient(self.homeserver, user=self.bot_user_id or "")
            self.client.access_token = self.access_token
            self._register_callbacks()
            if not self.access_token:
                debug_log("❌ Matrix: нет ни access_token, ни пары user/password")
                return False
            info_log(
                "ℹ️ Matrix command bot в legacy-режиме (без E2EE). "
                "Зашифрованные комнаты требуют MATRIX_BOT_USER_ID + MATRIX_BOT_PASSWORD."
            )
            return True

        os.makedirs(self.store_path, exist_ok=True)
        config = AsyncClientConfig(
            store_sync_tokens=True,
            encryption_enabled=True,
        )

        creds = self._load_saved_credentials()
        if creds:
            self.client = AsyncClient(
                self.homeserver,
                user=creds["user_id"],
                device_id=creds["device_id"],
                store_path=self.store_path,
                config=config,
            )
            self.client.restore_login(
                user_id=creds["user_id"],
                device_id=creds["device_id"],
                access_token=creds["access_token"],
            )
            try:
                self.client.load_store()
                self._e2e_enabled = True
                self._register_callbacks()
                info_log(
                    "✅ Matrix E2EE: восстановлен device "
                    f"{creds['device_id']} из crypto-store"
                )
                return True
            except Exception as exc:
                debug_log(
                    f"⚠️ Не удалось загрузить Matrix crypto-store ({exc}); "
                    "выполняю свежий логин по паролю"
                )
                try:
                    await self.client.close()
                except Exception:
                    pass

        # Свежий логин по паролю → стабильный device + crypto-store.
        self.client = AsyncClient(
            self.homeserver,
            user=self.bot_user_id,
            store_path=self.store_path,
            config=config,
        )
        try:
            resp = await self.client.login(
                self.bot_password, device_name=self.device_name
            )
        except Exception as exc:
            debug_log(f"❌ Matrix login исключение: {exc}")
            return False

        if not isinstance(resp, LoginResponse):
            debug_log(f"❌ Matrix login не удался: {resp}")
            return False

        self._save_credentials(resp.user_id, resp.device_id, resp.access_token)
        try:
            self.client.load_store()
        except Exception as exc:
            debug_log(f"⚠️ load_store после логина: {exc}")
        self._e2e_enabled = True
        self._register_callbacks()
        info_log(
            f"✅ Matrix E2EE: выполнен логин, device_id={resp.device_id}, "
            f"store={self.store_path}"
        )
        return True

    async def _ensure_keys(self) -> None:
        if not self._e2e_enabled or not self.client:
            return
        try:
            if getattr(self.client, "should_upload_keys", False):
                await self.client.keys_upload()
                debug_log("🔑 Matrix: ключи устройства выгружены")
            if getattr(self.client, "should_query_keys", False):
                await self.client.keys_query()
        except Exception as exc:
            debug_log(f"⚠️ Matrix keys upload/query: {exc}")

    async def _send_text(self, room_id: str, message: str) -> Optional[str]:
        response = await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
            ignore_unverified_devices=True,
        )
        event_id = getattr(response, "event_id", None)
        if event_id:
            self._sent_event_ids[event_id] = True
            self._cap_ordered(self._sent_event_ids, 500)
        return event_id

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
                ignore_unverified_devices=True,
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
        e2e = "вкл" if self._e2e_enabled else "выкл"
        return (
            "ℹ️ Система мониторинга серверов\n"
            f"• Версия: {version}\n"
            f"• E2EE: {e2e}\n"
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
        device_id = getattr(self.client, "device_id", "") or "unknown"
        return (
            "🩺 Matrix диагностика:\n"
            f"• bot_user_id: {bot_user_id}\n"
            f"• device_id: {device_id}\n"
            f"• e2ee: {'on' if self._e2e_enabled else 'off'}\n"
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
        event_id = getattr(event, "event_id", "") or ""

        # Сообщение, которое отправил сам бот: не маршрутизируем повторно.
        # Критично, когда бот залогинен под тем же MXID, что и человек —
        # иначе ответ-меню/хелп с строками "!cmd ..." уходит в бесконечный цикл.
        if event_id and event_id in self._sent_event_ids:
            debug_log(
                "ℹ️ Matrix событие проигнорировано: это собственный ответ бота "
                f"(room={room_id}, event_id={event_id})"
            )
            return True

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

    async def _on_undecrypted(self, room: MatrixRoom, event) -> None:
        """E2EE: сообщение не расшифровано — логируем и просим ключ комнаты."""
        room_id = getattr(room, "room_id", "unknown")
        sender = getattr(event, "sender", "unknown")
        info_log(
            "🔒 Matrix: входящее не расшифровано (нет ключа сессии) "
            f"room={room_id}, sender={sender}. Запрашиваю room key."
        )
        try:
            if self.client and hasattr(self.client, "request_room_key"):
                await self.client.request_room_key(event)
        except Exception as exc:
            debug_log(f"⚠️ request_room_key не удался: {exc}")

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
                f"room_id={'ok' if self.default_room_id else 'empty'}, "
                f"auth={'token' if self.access_token else ('login' if (self.bot_user_id and self.bot_password) else 'empty')})"
            )
            return

        ready = await self._setup_client()
        if not ready or not self.client:
            debug_log("❌ Matrix command bot: клиент не инициализирован, остановка")
            return

        info_log(
            "🚀 Matrix command bot запущен: "
            f"homeserver={self.homeserver}, default_room={self.default_room_id or 'empty'}, "
            f"e2ee={'on' if self._e2e_enabled else 'off'}, "
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
                await self._ensure_keys()
                self._started = True
            except Exception as exc:
                debug_log(f"❌ Matrix initial sync failed: {exc}")

        while True:
            try:
                await self.client.sync_forever(
                    timeout=30000,
                    full_state=True,
                    loop_sleep_time=1000,
                )
            except Exception as exc:
                debug_log(f"⚠️ Matrix sync_forever error: {exc}")
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
