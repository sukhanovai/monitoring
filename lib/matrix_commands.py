"""
/lib/matrix_commands.py
Server Monitoring System v8.62.18
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Incoming commands from Matrix (sync + router + ACL + audit + reaction buttons + E2EE).
Система мониторинга серверов
Версия: 8.62.18
Автор: Александр Суханов (c)
Лицензия: MIT
Входящие команды из Matrix (sync + router + ACL + аудит + кнопки-реакции + E2EE).
"""

from __future__ import annotations

import asyncio
import copy
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
# Команды расширений вынесены в подменю !extensions (см. EXTENSION_MENU_ITEMS).
MENU_BUTTONS: List[Tuple[str, str]] = [
    ("📡", "!status"),
    ("🌅", "!report"),
    ("🖥️", "!servers"),
    ("⏸️", "!pause"),
    ("▶️", "!resume"),
    ("🔇", "!silent"),
    ("🔊", "!loud"),
    ("🔄", "!auto"),
    ("🧩", "!extensions"),
    ("ℹ️", "!about"),
]
_BUTTON_BY_EMOJI: Dict[str, str] = {emoji: command for emoji, command in MENU_BUTTONS}

# Описание команд главного меню. Ключ — команда из MENU_BUTTONS; строки
# меню строятся из этого словаря, поэтому emoji в тексте всегда совпадает
# с emoji кнопки-реакции под сообщением.
_MENU_DESCRIPTIONS: Dict[str, str] = {
    "!status": "доступность всех серверов",
    "!report": "утренний/сводный отчёт",
    "!servers": "список серверов под мониторингом",
    "!pause": "приостановить мониторинг",
    "!resume": "возобновить мониторинг",
    "!silent": "принудительно тихий режим",
    "!loud": "принудительно громкий режим",
    "!auto": "авто тихий режим по расписанию",
    "!extensions": "меню расширений (бэкапы, ресурсы, ZFS и т.д.)",
    "!about": "версия и сведения о боте",
}


@dataclass(frozen=True)
class ExtensionMenuItem:
    """Команда/кнопка подменю «расширения».

    Появляется в !extensions и навешивается реакцией только если
    расширение extension_id включено в extension_manager.
    handler — имя async-метода MatrixCommandBot без аргументов.
    """

    extension_id: str
    emoji: str
    command: str
    label: str
    handler: str


# Порядок определяет порядок строк и кнопок-реакций в подменю.
# Расширения без headless-данных (snapshot_transfer_monitor,
# email_processor) сюда не входят: им нечего показать командой.
EXTENSION_MENU_ITEMS: List[ExtensionMenuItem] = [
    ExtensionMenuItem(
        "resource_monitor", "📊", "!resources",
        "ресурсы всех серверов", "_handle_resources_all",
    ),
    ExtensionMenuItem(
        "backup_monitor", "💾", "!backup",
        "бэкапы Proxmox", "_handle_ext_proxmox_backup",
    ),
    ExtensionMenuItem(
        "database_backup_monitor", "🗃️", "!dbbackup",
        "бэкапы баз данных", "_handle_ext_db_backup",
    ),
    ExtensionMenuItem(
        "mail_backup_monitor", "📬", "!mailbackup",
        "бэкапы почтового сервера", "_handle_ext_mail_backup",
    ),
    ExtensionMenuItem(
        "stock_load_monitor", "📦", "!stock",
        "загрузка остатков 1С", "_handle_ext_stock_load",
    ),
    ExtensionMenuItem(
        "zfs_monitor", "🧊", "!zfs",
        "детальный статус пулов ZFS (почта)", "_handle_ext_zfs",
    ),
    ExtensionMenuItem(
        "zfs_pool_free_space_monitor", "💽", "!zfsfree",
        "свободное место ZFS (SSH)", "_handle_ext_zfs_free",
    ),
    ExtensionMenuItem(
        "supplier_stock_files", "🏷️", "!supplier",
        "остатки поставщиков", "_handle_ext_supplier",
    ),
    ExtensionMenuItem(
        "web_interface", "🌐", "!web",
        "адрес веб-интерфейса", "_handle_ext_web",
    ),
]
_EXT_ITEM_BY_COMMAND: Dict[str, ExtensionMenuItem] = {
    item.command: item for item in EXTENSION_MENU_ITEMS
}

# Длинные ответы (списки серверов/ресурсов/настроек) Matrix-клиенты обрезают
# или плохо рендерят. Режем на части по границам строк и шлём пачкой.
_MAX_MESSAGE_CHARS = 3500


def _split_message(message: str, limit: int = _MAX_MESSAGE_CHARS) -> List[str]:
    """Режет сообщение на части <= limit символов по границам строк.

    Возвращает список с маркерами «(n/total)», если частей больше одной.
    Сверхдлинные одиночные строки дробятся жёстко по символам.
    """
    text = message or ""
    if len(text) <= limit:
        return [text]

    chunks: List[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)

    total = len(chunks)
    if total <= 1:
        return chunks
    return [f"({idx}/{total})\n{chunk}" for idx, chunk in enumerate(chunks, 1)]


# === Схема настроек для команды !settings ===
#
# «Основные настройки системы» показываются строго в этом порядке —
# по группам и ключам, независимо от категории в БД.
_CORE_SETTINGS_GROUPS: "OrderedDict[str, List[str]]" = OrderedDict((
    ("telegram", ["CHAT_IDS", "TELEGRAM_TOKEN"]),
    ("matrix", [
        "MATRIX_ACCESS_TOKEN", "MATRIX_BOT_PASSWORD",
        "MATRIX_BOT_USER_ID", "MATRIX_ROOM_ID",
    ]),
    ("monitoring", [
        "API_TIMEOUT_SEC", "CHECK_INTERVAL", "CPU_WARNING",
        "MAX_FAIL_TIME", "SERVER_TIMEOUTS",
    ]),
    ("time", [
        "DATA_COLLECTION", "DATA_COLLECTION_TIME", "DATA_COLLECTION_TIMES",
        "SILENT_END", "SILENT_START",
    ]),
    ("auth", ["SSH_KEY_PATH", "SSH_USERNAME"]),
))
_CORE_KEYS: Set[str] = {
    key for keys in _CORE_SETTINGS_GROUPS.values() for key in keys
}

# Параметры расширений. Показываются в секции «Расширения» только если
# расширение включено в extension_manager. Привязка по явным ключам и/или
# по категории настройки в БД.
_EXTENSION_SETTINGS: "OrderedDict[str, Dict[str, object]]" = OrderedDict((
    ("resource_monitor", {
        "label": "💻 ресурсы",
        "keys": [
            "RESOURCE_CHECK_INTERVAL", "RESOURCE_ALERT_INTERVAL",
            "CPU_CRITICAL", "RAM_WARNING", "RAM_CRITICAL",
            "DISK_WARNING", "DISK_CRITICAL",
        ],
        "categories": ["resources"],
    }),
    ("backup_monitor", {
        "label": "📊 бэкапы Proxmox",
        "keys": ["BACKUP_ALERT_HOURS", "BACKUP_STALE_HOURS", "PROXMOX_HOSTS"],
        "categories": ["backup"],
    }),
    ("database_backup_monitor", {
        "label": "🗃️ бэкапы БД",
        "keys": ["DATABASE_CONFIG"],
        "categories": ["database"],
    }),
    ("mail_backup_monitor", {
        "label": "📬 бэкапы почтового сервера",
        "keys": [],
        "categories": ["mail"],
    }),
    ("stock_load_monitor", {
        "label": "📦 загрузка остатков 1С",
        "keys": [],
        "categories": ["stock_load"],
    }),
    ("zfs_monitor", {
        "label": "🧊 ZFS",
        "keys": ["ZFS_SERVERS"],
        "categories": ["zfs"],
    }),
    ("zfs_pool_free_space_monitor", {
        "label": "💽 свободное место ZFS",
        "keys": ["ZFS_POOL_FREE_SPACE_HOSTS"],
        "categories": ["zfs_pool_free_space"],
    }),
    ("snapshot_transfer_monitor", {
        "label": "📸 передачи снэпшотов",
        "keys": ["SNAPSHOT_TRANSFER_HOSTS"],
        "categories": ["snapshot_transfer"],
    }),
    ("web_interface", {
        "label": "🌐 веб-интерфейс",
        "keys": ["WEB_PORT", "WEB_HOST"],
        "categories": ["web"],
    }),
))

# debug управляется на стороне сервера (config/debug.py, modules.debug),
# tamtam удалён из проекта — оба не показываются и не меняются из бота.
_HIDDEN_SETTING_CATEGORIES: Set[str] = {"debug", "tamtam"}
_HIDDEN_SETTING_KEYS: Set[str] = {"DEBUG_MODE", "LOG_LEVEL"}


def _is_tamtam_setting(key: str, category: str) -> bool:
    return (key or "").upper().startswith("TAMTAM") or (category or "").lower() == "tamtam"


def _is_debug_setting(key: str, category: str) -> bool:
    return (
        (key or "").upper() in _HIDDEN_SETTING_KEYS
        or (category or "").lower() == "debug"
    )


# Однозначный владелец параметра: явный ключ имеет приоритет над категорией.
_EXT_KEY_OWNER: Dict[str, str] = {
    key: ext_id
    for ext_id, spec in _EXTENSION_SETTINGS.items()
    for key in spec["keys"]  # type: ignore[index]
}
_EXT_CATEGORY_OWNER: Dict[str, str] = {}
for _ext_id, _spec in _EXTENSION_SETTINGS.items():
    for _cat in _spec["categories"]:  # type: ignore[index]
        _EXT_CATEGORY_OWNER.setdefault(_cat, _ext_id)


def _extension_for_setting(key: str, category: str) -> Optional[str]:
    """Расширение-владелец параметра по явному ключу или по категории."""
    if key in _EXT_KEY_OWNER:
        return _EXT_KEY_OWNER[key]
    return _EXT_CATEGORY_OWNER.get((category or "").lower())


# BACKUP_PATTERNS — единый параметр-словарь, но его разделы верхнего
# уровня принадлежат РАЗНЫМ расширениям (как в Telegram-боте, где паттерны
# разнесены по меню каждого расширения). В !settings раздуваем его в
# виртуальные строки BACKUP_PATTERNS.<раздел> и привязываем каждую к
# своему расширению, а не валим весь блок под «📊 бэкапы Proxmox».
_BACKUP_PATTERNS_KEY = "BACKUP_PATTERNS"
_BACKUP_PATTERN_DEFAULT_OWNER = "backup_monitor"
_BACKUP_PATTERN_SECTION_OWNER: Dict[str, str] = {
    "mail": "mail_backup_monitor",
    "zfs": "zfs_monitor",
    "snapshot_transfer": "snapshot_transfer_monitor",
    "stock_load": "stock_load_monitor",
    "database": "database_backup_monitor",
    "proxmox": "backup_monitor",
    "proxmox_subject": "backup_monitor",
    "hostname_extraction": "backup_monitor",
}
_BACKUP_PATTERN_SECTION_DESC: Dict[str, str] = {
    "mail": "Регэкспы писем бэкапа Zimbra (почтовый сервер)",
    "zfs": "Регэкспы писем статуса ZFS-массивов",
    "snapshot_transfer": "Регэкспы писем передачи ZFS-снэпшотов",
    "stock_load": "Регэкспы логов загрузки остатков 1С",
    "database": "Регэкспы писем бэкапов баз данных",
    "proxmox": "Регэкспы писем бэкапов Proxmox/PBS",
    "proxmox_subject": "Регэкспы темы писем бэкапов Proxmox/PBS",
    "hostname_extraction": "Регэкспы извлечения имени хоста Proxmox",
}
_BACKUP_PATTERN_SECTION_HINT = "; правится через меню паттернов расширений"

# Канонический раздел паттернов для каждого расширения-владельца. Если в
# эффективном BACKUP_PATTERNS у владельца нет ни одного раздела, в
# !settings всё равно показывается пустой раздел-плейсхолдер — чтобы
# 🧊 ZFS / 📸 передачи снэпшотов / 📬 почта / … были видны так же, как
# 📊 Proxmox и 🗃️ БД, а не пропадали молча.
_PATTERN_OWNER_PRIMARY_SECTION: Dict[str, str] = {
    "backup_monitor": "proxmox",
    "database_backup_monitor": "database",
    "mail_backup_monitor": "mail",
    "zfs_monitor": "zfs",
    "snapshot_transfer_monitor": "snapshot_transfer",
    "stock_load_monitor": "stock_load",
}


def _parse_backup_patterns_value(raw) -> Optional[dict]:
    """Парсит значение BACKUP_PATTERNS в словарь; None — если не словарь."""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _effective_backup_patterns(row: dict) -> Optional[dict]:
    """Эффективный BACKUP_PATTERNS для !settings (объединение хранилищ).

    Разделы паттернов живут в ДВУХ хранилищах: legacy-JSON
    ``settings.BACKUP_PATTERNS`` (его правит ``!settings set`` и старый
    путь бота) и таблица ``backup_patterns``, которой управляют меню
    паттернов Telegram-бота (``zfs``, ``snapshot_transfer``,
    ``proxmox``, …) и из которой реально читает рантайм
    (``modules.mail_monitor``). Раньше ``!settings`` показывал только
    JSON, поэтому разделы, заведённые через таблицу (🧊 ZFS,
    📸 передачи снэпшотов и т.п.), не были видны вовсе, хотя
    📊 Proxmox / 🗃️ БД из JSON показывались.

    Слияние на уровне раздела: дефолты ``config.settings`` ← legacy-JSON
    ← таблица (таблица авторитетна, как в рантайме). ``None`` — если ни
    одно из хранилищ не дало непустого словаря.
    """
    merged: dict = {}
    try:
        from config import settings as _defaults

        base = getattr(_defaults, "BACKUP_PATTERNS", None)
        if isinstance(base, dict):
            merged.update(copy.deepcopy(base))
    except Exception:
        pass
    stored = _parse_backup_patterns_value(row.get("value", ""))
    if isinstance(stored, dict):
        for section, value in stored.items():
            merged[section] = copy.deepcopy(value)
    try:
        from core.config_manager import config_manager

        table = config_manager.get_backup_patterns()
        if isinstance(table, dict):
            for section, value in table.items():
                if value:
                    merged[section] = copy.deepcopy(value)
    except Exception:
        pass
    return merged or None


def _expand_backup_patterns(row: dict) -> List[Tuple[dict, str]]:
    """Раздувает BACKUP_PATTERNS в список (виртуальная_строка, владелец).

    Источник — эффективный словарь (legacy-JSON ⊕ таблица паттернов ⊕
    дефолты), а не только сырое значение строки. Для каждого
    расширения-владельца паттернов гарантируется хотя бы один раздел
    (пустой плейсхолдер, если паттернов ещё нет), чтобы 🧊 ZFS /
    📸 передачи снэпшотов / 📬 почта были видны так же, как
    📊 Proxmox / 🗃️ БД. Если ни одно хранилище не дало словаря —
    возвращается исходная строка с владельцем по умолчанию (как раньше).
    """
    parsed = _effective_backup_patterns(row)
    if not parsed:
        return [(row, _BACKUP_PATTERN_DEFAULT_OWNER)]
    category = row.get("category", "backup")
    out: List[Tuple[dict, str]] = []
    seen_owners: Set[str] = set()
    for section in sorted(parsed.keys()):
        owner = _BACKUP_PATTERN_SECTION_OWNER.get(
            section, _BACKUP_PATTERN_DEFAULT_OWNER
        )
        seen_owners.add(owner)
        try:
            section_value = json.dumps(parsed[section], ensure_ascii=False)
        except (TypeError, ValueError):
            section_value = str(parsed[section])
        desc = _BACKUP_PATTERN_SECTION_DESC.get(
            section, f"Регэкспы раздела «{section}» BACKUP_PATTERNS"
        )
        out.append((
            {
                "key": f"{_BACKUP_PATTERNS_KEY}.{section}",
                "value": section_value,
                "category": category,
                "description": desc + _BACKUP_PATTERN_SECTION_HINT,
                "data_type": "dict",
            },
            owner,
        ))
    for owner, section in _PATTERN_OWNER_PRIMARY_SECTION.items():
        if owner in seen_owners:
            continue
        desc = _BACKUP_PATTERN_SECTION_DESC.get(
            section, f"Регэкспы раздела «{section}» BACKUP_PATTERNS"
        )
        out.append((
            {
                "key": f"{_BACKUP_PATTERNS_KEY}.{section}",
                "value": "{}",
                "category": category,
                "description": (
                    desc + " (паттерны не заданы)"
                    + _BACKUP_PATTERN_SECTION_HINT
                ),
                "data_type": "dict",
            },
            owner,
        ))
    return out


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
        # event_id сообщений подменю «расширения»: реакции на них
        # резолвятся по EXTENSION_MENU_ITEMS с учётом включённости
        self._ext_menu_event_ids: "OrderedDict[str, str]" = OrderedDict()
        # event_id сообщений сводки !backup: реакции-кнопки с именами
        # серверов резолвятся в детализацию по конкретному хосту Proxmox
        self._backup_menu_event_ids: "OrderedDict[str, str]" = OrderedDict()
        # event_id сообщений сводки !dbbackup: реакции-кнопки с именами
        # баз резолвятся в статистику по конкретной БД
        self._dbbackup_menu_event_ids: "OrderedDict[str, str]" = OrderedDict()
        # label кнопки -> (backup_type, db_name, display_name) для !dbbackup
        self._dbbackup_index: "OrderedDict[str, Tuple[str, str, str]]" = OrderedDict()
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

    async def _send_long_text(self, room_id: str, message: str) -> None:
        """Шлёт ответ, при необходимости разбивая на несколько сообщений."""
        for part in _split_message(message):
            await self._send_text(room_id, part)

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

    async def _post_extensions_menu(self, room_id: str) -> None:
        """Отправляет подменю расширений и навешивает кнопки только
        для включённых расширений."""
        enabled = self._enabled_extensions()
        text = self._extensions_menu_text(enabled)
        event_id = await self._send_text(room_id, text)
        if not event_id:
            debug_log("⚠️ Matrix подменю расширений отправлено без event_id")
            return

        self._ext_menu_event_ids[event_id] = room_id
        self._cap_ordered(self._ext_menu_event_ids, 50)

        for item in EXTENSION_MENU_ITEMS:
            if item.extension_id in enabled:
                await self._send_reaction(room_id, event_id, item.emoji)

    # Лимит кнопок-реакций под сводкой !backup. Matrix-клиенты плохо
    # рендерят десятки реакций на одном сообщении; при превышении лимита
    # подсказываем точечную команду !backup <хост>.
    _BACKUP_MENU_MAX_BUTTONS = 40

    async def _post_backup_menu(self, room_id: str, body: str) -> None:
        """Отправляет сводку !backup и навешивает кнопки-реакции с именами
        серверов Proxmox для перехода к детализации по конкретному хосту."""
        if "backup_monitor" not in self._enabled_extensions():
            await self._send_long_text(room_id, body)
            return

        hosts = self._proxmox_backup_hosts()
        if not hosts:
            await self._send_long_text(room_id, body)
            return

        limited = hosts[: self._BACKUP_MENU_MAX_BUTTONS]
        hint = [
            "",
            "🔘 Жми кнопку с именем сервера под этим сообщением — "
            "покажу детали бэкапов по нему.",
            "Либо команда: !backup <имя_сервера>",
        ]
        if len(hosts) > len(limited):
            hint.append(
                f"ⓘ Серверов {len(hosts)}, кнопок показано {len(limited)} "
                "(остальные — командой !backup <имя_сервера>)."
            )
        event_id = await self._send_text(room_id, body + "\n" + "\n".join(hint))
        if not event_id:
            debug_log("⚠️ Matrix сводка !backup без event_id: кнопки-реакции пропущены")
            return

        self._backup_menu_event_ids[event_id] = room_id
        self._cap_ordered(self._backup_menu_event_ids, 50)

        for host_name in limited:
            await self._send_reaction(room_id, event_id, host_name)

    # Иконки статуса БД (как в Telegram DisplayFormatters.DB_STATUS_ICONS).
    _DB_STATUS_ICONS: Dict[str, str] = {
        "success": "✅",
        "failed": "🔴",
        "recent_failed": "🟠",
        "warning": "🟡",
        "recent_errors": "🟠",
        "old": "🟡",
        "stale": "⚫",
        "unknown": "⚪",
    }
    _DB_STATUS_LABEL: Dict[str, str] = {
        "success": "🟢 в норме",
        "old": "🟡 устаревает",
        "warning": "🟡 ошибки в последнем бэкапе",
        "recent_errors": "🟠 ошибки в истории",
        "recent_failed": "🟠 есть неудачные бэкапы",
        "failed": "🔴 последний бэкап неудачен",
        "stale": "⚫ нет свежих бэкапов",
        "unknown": "❔ статус не определён",
    }

    @staticmethod
    def _database_backup_entries() -> List[dict]:
        """Снимок БД и их статусов (для кнопок под !dbbackup).

        Источник тот же, что и в Telegram-боте
        (get_database_monitor_snapshot): конфиг + backups.db.
        """
        try:
            from extensions.backup_monitor.bot_handler import BackupMonitorBot
            from extensions.backup_monitor.backup_handlers import (
                get_database_monitor_snapshot,
            )

            snapshot = get_database_monitor_snapshot(BackupMonitorBot())
        except Exception as exc:
            debug_log(f"⚠️ Не удалось получить список БД для !dbbackup: {exc}")
            return []

        entries: List[dict] = []
        for item in snapshot or []:
            db_name = str(item.get("db_name") or "").strip()
            backup_type = str(item.get("backup_type") or "").strip()
            if not db_name or not backup_type:
                continue
            entries.append(
                {
                    "backup_type": backup_type,
                    "db_name": db_name,
                    "display_name": str(
                        item.get("display_name") or db_name
                    ).strip()
                    or db_name,
                    "status": str(item.get("status") or "unknown"),
                    "is_disabled": bool(item.get("is_disabled")),
                }
            )
        return entries

    def _build_dbbackup_index(
        self, entries: List[dict]
    ) -> "OrderedDict[str, Tuple[str, str, str]]":
        """label кнопки-реакции -> (backup_type, db_name, display_name).

        Лейблы делаем уникальными: Matrix агрегирует реакции по одинаковому
        ключу, поэтому при совпадении display_name добавляем тип/счётчик.
        """
        index: "OrderedDict[str, Tuple[str, str, str]]" = OrderedDict()
        for entry in entries:
            status = str(entry.get("status") or "unknown")
            icon = (
                "⚪"
                if entry.get("is_disabled")
                else self._DB_STATUS_ICONS.get(status, "⚪")
            )
            display_name = entry["display_name"]
            base = f"{icon} {display_name}"
            label = base
            if label in index:
                label = f"{base} ({entry['backup_type']})"
                suffix = 2
                while label in index:
                    label = f"{base} #{suffix}"
                    suffix += 1
            index[label] = (
                entry["backup_type"],
                entry["db_name"],
                display_name,
            )
        return index

    def _resolve_db_entry(
        self, label: str
    ) -> Optional[Tuple[str, str, str]]:
        """Резолвит ключ реакции/аргумент в (backup_type, db_name, display).

        Сначала по актуальному индексу из последнего меню, затем по свежему
        снимку — чтобы `!dbbackup <имя>` работал и без открытого меню.
        """
        label = (label or "").strip()
        if not label:
            return None

        indices = [self._dbbackup_index]
        for index in indices:
            if not index:
                continue
            if label in index:
                return index[label]
            low = label.lower()
            for lbl, target in index.items():
                if low in (lbl.lower(), target[2].lower(), target[1].lower()):
                    return target

        fresh = self._build_dbbackup_index(self._database_backup_entries())
        if not fresh:
            return None
        if label in fresh:
            return fresh[label]
        low = label.lower()
        for lbl, target in fresh.items():
            if low in (lbl.lower(), target[2].lower(), target[1].lower()):
                return target
        return None

    # Лимит кнопок-реакций под сводкой !dbbackup (см. _BACKUP_MENU_MAX_BUTTONS).
    _DBBACKUP_MENU_MAX_BUTTONS = 40

    async def _post_dbbackup_menu(self, room_id: str, body: str) -> None:
        """Отправляет сводку !dbbackup и навешивает кнопки-реакции с именами
        баз для перехода к статистике бэкапов по конкретной БД."""
        if "database_backup_monitor" not in self._enabled_extensions():
            await self._send_long_text(room_id, body)
            return

        entries = self._database_backup_entries()
        if not entries:
            await self._send_long_text(room_id, body)
            return

        index = self._build_dbbackup_index(entries)
        self._dbbackup_index = index

        labels = list(index.keys())[: self._DBBACKUP_MENU_MAX_BUTTONS]
        hint = [
            "",
            "🔘 Жми кнопку с именем базы под этим сообщением — "
            "покажу статистику бэкапов по ней.",
            "Либо команда: !dbbackup <имя_базы>",
        ]
        if len(index) > len(labels):
            hint.append(
                f"ⓘ Баз {len(index)}, кнопок показано {len(labels)} "
                "(остальные — командой !dbbackup <имя_базы>)."
            )
        event_id = await self._send_text(
            room_id, body + "\n" + "\n".join(hint)
        )
        if not event_id:
            debug_log(
                "⚠️ Matrix сводка !dbbackup без event_id: кнопки-реакции пропущены"
            )
            return

        self._dbbackup_menu_event_ids[event_id] = room_id
        self._cap_ordered(self._dbbackup_menu_event_ids, 50)

        for label in labels:
            await self._send_reaction(room_id, event_id, label)

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
            for item in down:
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
        for item in results:
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
        for server in servers:
            name = server.get("name", "unknown")
            ip = server.get("ip", "n/a")
            stype = server.get("type", "?")
            enabled = server.get("enabled", True)
            flag = "🟢" if enabled else "⚪"
            lines.append(f"{flag} {name} ({ip}) [{stype}]")
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

    # ------------------------------------------------------------------
    # Команды расширений (подменю !extensions)
    # ------------------------------------------------------------------
    async def _run_extension_command(self, item: ExtensionMenuItem) -> str:
        """Выполняет команду расширения, если оно включено."""
        if item.extension_id not in self._enabled_extensions():
            return (
                f"❌ Команда {item.command} недоступна: "
                f"расширение «{item.extension_id}» выключено.\n"
                "Включить можно в управлении расширениями (Telegram/веб-интерфейс)."
            )
        handler = getattr(self, item.handler, None)
        if handler is None:
            return f"❌ Обработчик для {item.command} не найден"
        try:
            return await handler()
        except Exception as exc:
            return f"❌ Ошибка выполнения {item.command}: {str(exc)[:160]}"

    @staticmethod
    def _backup_summary(period_hours: int, *, proxmox: bool, databases: bool, mail: bool) -> str:
        from extensions.backup_monitor.backup_utils import get_backup_summary

        text, _has_issues = get_backup_summary(
            period_hours=period_hours,
            include_proxmox=proxmox,
            include_databases=databases,
            include_mail=mail,
        )
        return (text or "").strip() or "ℹ️ Нет данных за период"

    async def _handle_ext_proxmox_backup(self) -> str:
        body = self._backup_summary(24, proxmox=True, databases=False, mail=False)
        return f"💾 Бэкапы Proxmox (24ч):\n{body}"

    _BACKUP_HOST_STATUS_LABEL: Dict[str, str] = {
        "success": "🟢 в норме",
        "old": "🟡 устаревает",
        "stale": "⚫ нет свежих бэкапов",
        "failed": "🔴 последний бэкап неудачен",
        "recent_failed": "🟠 есть неудачные бэкапы",
        "unknown": "❔ статус не определён",
    }

    @staticmethod
    def _proxmox_backup_hosts() -> List[str]:
        """Список включённых хостов Proxmox (для кнопок под !backup)."""
        try:
            from extensions.backup_monitor.bot_handler import BackupMonitorBot

            hosts = BackupMonitorBot().get_all_hosts()
        except Exception as exc:
            debug_log(f"⚠️ Не удалось получить список хостов Proxmox: {exc}")
            return []
        return [str(h).strip() for h in hosts if str(h).strip()]

    async def _handle_backup_host_detail(self, host_name: str) -> str:
        """Детализация бэкапов одного хоста Proxmox (последние записи)."""
        host_name = (host_name or "").strip()
        if not host_name:
            return "ℹ️ Не указано имя сервера. Использование: !backup <имя_сервера>"
        try:
            from extensions.backup_monitor.bot_handler import BackupMonitorBot

            bot = BackupMonitorBot()
            rows = bot.get_host_status(host_name)
        except Exception as exc:
            return f"❌ Ошибка получения данных по «{host_name}»: {str(exc)[:160]}"

        if not rows:
            return (
                f"🖥️ Бэкапы {host_name}\n"
                "Нет данных по этому хосту за последнее время."
            )

        try:
            status_key = bot.get_host_display_status(host_name)
        except Exception:
            status_key = ""
        status_label = self._BACKUP_HOST_STATUS_LABEL.get(
            str(status_key), str(status_key) or ""
        )

        lines = [f"🖥️ Бэкапы {host_name}"]
        if status_label:
            lines.append(f"Статус: {status_label}")
        lines.append("")
        for backup_status, duration, total_size, error_message, received_at in rows:
            icon = "✅" if str(backup_status) == "success" else "❌"
            try:
                backup_time = datetime.strptime(
                    str(received_at), "%Y-%m-%d %H:%M:%S"
                )
                time_str = backup_time.strftime("%d.%m %H:%M")
            except Exception:
                time_str = str(received_at)[:16]
            lines.append(f"{icon} {time_str} — {backup_status}")
            if duration:
                lines.append(f"• Время: {duration}")
            if total_size:
                lines.append(f"• Размер: {total_size}")
            if error_message and str(backup_status) != "success":
                lines.append(f"• Ошибка: {str(error_message)[:160]}")
            lines.append("")
        lines.append(f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}")
        return "\n".join(lines).rstrip()

    async def _handle_ext_db_backup(self) -> str:
        body = self._backup_summary(24, proxmox=False, databases=True, mail=False)
        return f"🗃️ Бэкапы баз данных (24ч):\n{body}"

    _DB_DETAIL_HOURS = 168
    _DB_TASK_TYPE_NAMES: Dict[str, str] = {
        "database_dump": "Дамп БД",
        "client_database_dump": "Дамп клиентской БД",
        "cobian_backup": "Резервное копирование",
        "yandex_backup": "Yandex Backup",
    }

    async def _handle_db_backup_detail(self, label: str) -> str:
        """Статистика бэкапов одной БД (как деталь в Telegram-боте)."""
        label = (label or "").strip()
        if not label:
            return (
                "ℹ️ Не указано имя базы. "
                "Использование: !dbbackup <имя_базы>"
            )

        target = self._resolve_db_entry(label)
        if target is None:
            return (
                f"ℹ️ База «{label}» не найдена. Открой список командой "
                "!dbbackup и жми кнопку под сводкой."
            )

        backup_type, db_name, display_name = target
        try:
            from extensions.backup_monitor.bot_handler import BackupMonitorBot

            bot = BackupMonitorBot()
            details = bot.get_database_details(
                backup_type, db_name, self._DB_DETAIL_HOURS
            )
            try:
                status_key = bot.get_database_display_status(
                    backup_type, db_name
                )
            except Exception:
                status_key = ""
        except Exception as exc:
            return (
                f"❌ Ошибка получения данных по «{display_name}»: "
                f"{str(exc)[:160]}"
            )

        if not details:
            return (
                f"🗃️ Бэкапы БД: {display_name}\n"
                f"Нет данных по этой базе за последние "
                f"{self._DB_DETAIL_HOURS} часов."
            )

        status_label = self._DB_STATUS_LABEL.get(
            str(status_key), str(status_key) or ""
        )
        success = sum(1 for d in details if d and d[0] == "success")
        failed = sum(1 for d in details if d and d[0] == "failed")
        total = len(details)

        lines = [f"🗃️ Бэкапы БД: {display_name}"]
        if status_label:
            lines.append(f"Статус: {status_label}")
        lines.append(f"Период: {self._DB_DETAIL_HOURS} часов")
        lines.append("")
        lines.append("📊 Статистика:")
        lines.append(f"✅ Успешных: {success}")
        lines.append(f"❌ Ошибок: {failed}")
        lines.append(f"📈 Всего: {total}")
        lines.append("")
        lines.append("⏰ Последние бэкапы:")
        for status, task_type, error_count, _subject, received_at in details[:10]:
            icon = "✅" if status == "success" else "❌"
            try:
                backup_time = datetime.strptime(
                    str(received_at), "%Y-%m-%d %H:%M:%S"
                )
                time_str = backup_time.strftime("%d.%m %H:%M")
            except Exception:
                time_str = str(received_at)[:16]
            task_display = self._DB_TASK_TYPE_NAMES.get(
                task_type, task_type or "Резервное копирование"
            )
            line = f"{icon} {time_str} — {status} — {task_display}"
            try:
                if error_count and int(error_count) > 0:
                    line += f" (ошибок: {int(error_count)})"
            except (TypeError, ValueError):
                pass
            lines.append(line)
        lines.append("")
        lines.append(f"🕒 Обновлено: {datetime.now().strftime('%H:%M:%S')}")
        return "\n".join(lines).rstrip()

    async def _handle_ext_mail_backup(self) -> str:
        body = self._backup_summary(72, proxmox=False, databases=False, mail=True)
        return f"📬 Бэкапы почтового сервера (72ч):\n{body}"

    async def _handle_ext_stock_load(self) -> str:
        # stock_load_monitor — отдаём детальную загрузку остатков по
        # источникам/поставщикам (как в Telegram-боте), а не краткую
        # сводку get_stock_load_summary.
        return await self._handle_stock()

    async def _handle_ext_zfs(self) -> str:
        # zfs_monitor — почтовый монитор: статусы пулов берутся из БД
        # бэкапов (таблица zfs_pool_status). Отдаём детальный список пулов
        # по серверам (как в Telegram-боте), а не агрегированную сводку.
        return await self._handle_zfs()

    async def _handle_ext_zfs_free(self) -> str:
        from extensions.zfs_pool_free_space import (
            build_status_lines,
            collect_zfs_pool_free_space,
        )

        results, errors = collect_zfs_pool_free_space()
        return "\n".join(build_status_lines(results, errors))

    async def _handle_ext_supplier(self) -> str:
        from extensions.supplier_stock_files import summarize_supplier_stock_reports

        grouped = summarize_supplier_stock_reports()
        lines = ["🏷️ Остатки поставщиков:"]
        any_source = False
        for kind in ("download", "mail"):
            sources = grouped.get(kind) or []
            if not sources:
                continue
            any_source = True
            title = "загрузка" if kind == "download" else "почта"
            lines.append(f"• {title}: источников {len(sources)}")
            for src in sources:
                name = src.get("source_name") or src.get("source_id") or "?"
                recv = (src.get("receive") or {}).get("icon", "⚪️")
                proc = (src.get("processing") or {}).get("icon", "⚪️")
                tran = (src.get("transfer") or {}).get("icon", "⚪️")
                lines.append(
                    f"  {name}: приём {recv} обработка {proc} передача {tran}"
                )
        if not any_source:
            lines.append("ℹ️ Нет данных по источникам")
        return "\n".join(lines)

    async def _handle_ext_web(self) -> str:
        from core.config_manager import config_manager

        host = config_manager.get_setting("WEB_HOST", "127.0.0.1") or "127.0.0.1"
        port = config_manager.get_setting("WEB_PORT", 5000) or 5000
        return (
            "🌐 Веб-интерфейс управления:\n"
            f"• http://{host}:{port}\n"
            "Открой адрес в браузере из доверенной сети."
        )

    def _extensions_menu_text(self, enabled: Optional[Set[str]] = None) -> str:
        if enabled is None:
            enabled = self._enabled_extensions()
        items = [it for it in EXTENSION_MENU_ITEMS if it.extension_id in enabled]
        lines = [
            "🧩 Расширения (показаны только включённые).",
            "Жми кнопки-реакции под этим сообщением или пиши команды:",
            "",
        ]
        if not items:
            lines.append("ℹ️ Нет включённых расширений с командами.")
        else:
            for it in items:
                lines.append(f"{it.emoji} {it.command} — {it.label}")
        arg_commands: List[str] = []
        if "resource_monitor" in enabled:
            arg_commands.append("• !res <имя|ip> — ресурсы одного сервера")
        if "backup_monitor" in enabled:
            arg_commands.append(
                "• !backup <имя_сервера> — детали бэкапов по серверу "
                "(или жми кнопку-реакцию под сводкой !backup)"
            )
        if "database_backup_monitor" in enabled:
            arg_commands.append(
                "• !dbbackup <имя_базы> — статистика бэкапов по базе "
                "(или жми кнопку-реакцию под сводкой !dbbackup)"
            )
        if arg_commands:
            lines.append("")
            lines.append("Команды с аргументом:")
            lines.extend(arg_commands)
        lines.append("")
        lines.append("Назад: !menu")
        return "\n".join(lines)

    _SETTINGS_USAGE = (
        "⚙️ Управление настройками:\n"
        "• !settings — этот хелп и список параметров\n"
        "• !settings list [группа] — параметры с текущими значениями\n"
        "• !settings get <KEY> — значение одного параметра\n"
        "• !settings set <KEY> <значение> — изменить параметр\n"
        "Примеры:\n"
        "  !settings get CHECK_INTERVAL\n"
        "  !settings set CHECK_INTERVAL 120\n"
        "  !settings list monitoring\n"
        "ⓘ Отладка (DEBUG_MODE/LOG_LEVEL) управляется на стороне сервера."
    )

    @staticmethod
    def _is_secret_key(key: str) -> bool:
        upper = (key or "").upper()
        return any(token in upper for token in ("TOKEN", "PASSWORD", "SECRET"))

    @classmethod
    def _format_setting_value(cls, key: str, value, *, reveal: bool = False) -> str:
        # reveal=True — явный запрос одного параметра (!settings get <KEY>):
        # секреты не маскируются, длинные значения не обрезаются.
        if cls._is_secret_key(key) and not reveal:
            return "•••• (скрыто)" if str(value or "") else "(пусто)"
        text = "" if value is None else str(value)
        if text == "":
            return "(пусто)"
        if not reveal and len(text) > 120:
            return text[:120] + "…"
        return text

    @staticmethod
    def _convert_setting_value(raw: str, data_type: str):
        dt = (data_type or "string").lower()
        if dt == "int":
            return int(raw)
        if dt == "float":
            return float(raw)
        if dt == "bool":
            low = raw.strip().lower()
            if low in ("true", "1", "yes", "on", "да"):
                return True
            if low in ("false", "0", "no", "off", "нет"):
                return False
            raise ValueError("ожидается true/false")
        if dt in ("list", "dict"):
            parsed = json.loads(raw)
            if dt == "list" and not isinstance(parsed, list):
                raise ValueError("ожидается JSON-массив")
            if dt == "dict" and not isinstance(parsed, dict):
                raise ValueError("ожидается JSON-объект")
            return parsed
        return raw

    @staticmethod
    def _enabled_extensions() -> Set[str]:
        try:
            from extensions.extension_manager import extension_manager

            return set(extension_manager.get_enabled_extensions())
        except Exception:
            return set()

    def _build_settings_view(self) -> Tuple[List[Tuple[str, List[Tuple[str, list]]]], int]:
        """Структурированное представление настроек для !settings.

        Возвращает (sections, total), где sections — список
        (заголовок_секции, [(подзаголовок_группы, [meta_row, ...]), ...]).
        Скрытые параметры (debug/tamtam) и параметры выключенных
        расширений не попадают в результат.
        """
        from core.config_manager import config_manager

        rows = config_manager.get_all_settings_meta()
        by_key = {row.get("key", ""): row for row in rows}
        enabled = self._enabled_extensions()

        # --- Основные настройки системы ---
        core_groups: List[Tuple[str, list]] = []
        for group, keys in _CORE_SETTINGS_GROUPS.items():
            present = [by_key[k] for k in keys if k in by_key]
            if present:
                core_groups.append((group, present))

        # --- Распределение остальных параметров по расширениям ---
        # У каждого параметра ровно один владелец (явный ключ > категория).
        ext_buckets: Dict[str, list] = {}
        leftover: list = []
        for key, row in by_key.items():
            if key in _CORE_KEYS:
                continue
            category = row.get("category", "")
            if _is_tamtam_setting(key, category) or _is_debug_setting(key, category):
                continue
            if key == _BACKUP_PATTERNS_KEY:
                # Раздел верхнего уровня → своё расширение (как в Telegram).
                for vrow, vowner in _expand_backup_patterns(row):
                    ext_buckets.setdefault(vowner, []).append(vrow)
                continue
            owner = _extension_for_setting(key, category)
            if owner is None:
                leftover.append(row)
            else:
                ext_buckets.setdefault(owner, []).append(row)

        ext_groups: List[Tuple[str, list]] = []
        for ext_id, spec in _EXTENSION_SETTINGS.items():
            if ext_id not in enabled:
                continue  # параметры выключенного расширения не показываем
            members = ext_buckets.get(ext_id)
            if not members:
                continue
            key_order = {k: i for i, k in enumerate(spec["keys"])}  # type: ignore[index]
            members.sort(
                key=lambda r: (
                    key_order.get(r.get("key", ""), len(key_order)),
                    r.get("key", ""),
                )
            )
            ext_groups.append((str(spec["label"]), members))

        if leftover:
            leftover.sort(key=lambda r: r.get("key", ""))
            ext_groups.append(("🧩 прочее", leftover))

        sections: List[Tuple[str, List[Tuple[str, list]]]] = []
        if core_groups:
            sections.append(("🔧 Основные настройки системы", core_groups))
        if ext_groups:
            sections.append(("🧩 Расширения", ext_groups))

        total = sum(
            len(members)
            for _, groups in sections
            for _, members in groups
        )
        return sections, total

    def _render_settings_sections(
        self,
        sections: List[Tuple[str, List[Tuple[str, list]]]],
        with_desc: bool,
    ) -> List[str]:
        lines: List[str] = []
        for title, groups in sections:
            lines.append(f"\n══ {title} ══")
            for group, members in groups:
                lines.append(f"\n— {group} —")
                for row in members:
                    key = row.get("key", "")
                    dtype = row.get("data_type", "string")
                    value = self._format_setting_value(key, row.get("value", ""))
                    lines.append(f"• {key} [{dtype}] = {value}")
                    if with_desc:
                        lines.append(f"   {row.get('description') or 'без описания'}")
        return lines

    def _settings_help(self) -> str:
        try:
            sections, total = self._build_settings_view()
        except Exception as exc:
            return f"{self._SETTINGS_USAGE}\n\n❌ Не удалось загрузить список: {exc}"

        lines = [self._SETTINGS_USAGE, "", f"📋 Параметры ({total}):"]
        lines.extend(self._render_settings_sections(sections, with_desc=True))
        return "\n".join(lines)

    def _settings_list(self, group_filter: Optional[str]) -> str:
        try:
            sections, total = self._build_settings_view()
        except Exception as exc:
            return f"❌ Не удалось загрузить настройки: {exc}"

        if not sections:
            return "ℹ️ Список настроек пуст"

        if group_filter:
            needle = group_filter.strip().lower()
            filtered: List[Tuple[str, List[Tuple[str, list]]]] = []
            for title, groups in sections:
                matched = [
                    (group, members)
                    for group, members in groups
                    if needle in group.lower()
                ]
                if matched:
                    filtered.append((title, matched))
            if not filtered:
                return (
                    f"ℹ️ Группа «{group_filter}» не найдена или её "
                    "параметры скрыты (расширение выключено)."
                )
            lines = [f"⚙️ Настройки: «{group_filter}»"]
            lines.extend(self._render_settings_sections(filtered, with_desc=False))
            return "\n".join(lines)

        lines = [f"⚙️ Все настройки: {total}"]
        lines.extend(self._render_settings_sections(sections, with_desc=False))
        return "\n".join(lines)

    def _check_setting_access(self, setting_key: str, meta: dict) -> Optional[str]:
        """Возвращает текст ошибки, если параметр недоступен из бота."""
        category = meta.get("category", "")
        if _is_tamtam_setting(setting_key, category):
            return (
                f"❌ Параметр {setting_key} удалён из проекта "
                "(интеграция TamTam отключена)."
            )
        if _is_debug_setting(setting_key, category):
            return (
                f"ⓘ {setting_key} — параметр отладки. "
                "Управление отладкой вынесено на сторону сервера, "
                "из command-bot он недоступен."
            )
        if setting_key not in _CORE_KEYS:
            ext_id = _extension_for_setting(setting_key, category)
            if ext_id and ext_id not in self._enabled_extensions():
                return (
                    f"❌ Параметр {setting_key} относится к выключенному "
                    f"расширению «{ext_id}» и недоступен."
                )
        return None

    def _settings_get_backup_section(self, section_raw: str) -> str:
        try:
            from core.config_manager import config_manager

            data = _effective_backup_patterns(
                {"value": config_manager.get_setting(_BACKUP_PATTERNS_KEY, None)}
            )
            if not data:
                return (
                    "❌ BACKUP_PATTERNS пуст или не является словарём. "
                    "Полностью: !settings get BACKUP_PATTERNS"
                )
            match = next(
                (k for k in data if k.lower() == section_raw.lower()), None
            )
            if match is None:
                avail = ", ".join(sorted(data.keys())) or "—"
                return (
                    f"❌ Раздел «{section_raw}» в BACKUP_PATTERNS не найден.\n"
                    f"• доступные разделы: {avail}"
                )
            owner = _BACKUP_PATTERN_SECTION_OWNER.get(
                match.lower(), _BACKUP_PATTERN_DEFAULT_OWNER
            )
            desc = _BACKUP_PATTERN_SECTION_DESC.get(
                match, f"Регэкспы раздела «{match}» BACKUP_PATTERNS"
            )
            shown = json.dumps(data[match], ensure_ascii=False, indent=2)
            return (
                f"✅ BACKUP_PATTERNS.{match} =\n{shown}\n"
                "• тип: dict (раздел BACKUP_PATTERNS)\n"
                f"• расширение: {owner}\n"
                f"• описание: {desc}{_BACKUP_PATTERN_SECTION_HINT}"
            )
        except Exception as exc:
            return f"❌ Ошибка чтения раздела BACKUP_PATTERNS: {exc}"

    def _settings_get(self, setting_key: str) -> str:
        if setting_key.split(".", 1)[0] == _BACKUP_PATTERNS_KEY and "." in setting_key:
            return self._settings_get_backup_section(setting_key.split(".", 1)[1])
        try:
            from core.config_manager import config_manager

            meta = config_manager.get_setting_meta(setting_key)
            if meta is None:
                return (
                    f"❌ Настройка {setting_key} не найдена. "
                    "Список: !settings list"
                )
            blocked = self._check_setting_access(setting_key, meta)
            if blocked:
                return blocked
            value = config_manager.get_setting(setting_key, None)
            desc = meta.get("description") or "без описания"
            dtype = meta.get("data_type", "string")
            shown = self._format_setting_value(setting_key, value, reveal=True)
            return (
                f"✅ {setting_key} = {shown}\n"
                f"• тип: {dtype}\n"
                f"• описание: {desc}"
            )
        except Exception as exc:
            return f"❌ Ошибка чтения настройки: {exc}"

    def _settings_set(self, setting_key: str, raw_value: str) -> str:
        if setting_key.split(".", 1)[0] == _BACKUP_PATTERNS_KEY and "." in setting_key:
            return (
                "ⓘ Разделы BACKUP_PATTERNS по отдельности из command-bot "
                "не редактируются — паттерны правятся через меню паттернов "
                "соответствующего расширения в Telegram-боте. Целиком: "
                "!settings set BACKUP_PATTERNS <JSON>."
            )
        try:
            from core.config_manager import config_manager

            meta = config_manager.get_setting_meta(setting_key)
            if meta is None:
                return (
                    f"❌ Настройка {setting_key} не найдена, изменение "
                    "отклонено. Доступные параметры: !settings list"
                )

            blocked = self._check_setting_access(setting_key, meta)
            if blocked:
                return blocked

            data_type = meta.get("data_type", "string")
            try:
                converted = self._convert_setting_value(raw_value, data_type)
            except (ValueError, json.JSONDecodeError) as exc:
                return (
                    f"❌ Неверное значение для {setting_key} "
                    f"(тип {data_type}): {exc}"
                )

            ok = config_manager.set_setting(
                setting_key,
                converted,
                category=meta.get("category", "general"),
                description=meta.get("description", ""),
                data_type="auto",
            )
            if not ok:
                return f"❌ Не удалось сохранить настройку {setting_key}"

            shown = self._format_setting_value(
                setting_key, converted, reveal=True
            )
            self._audit(
                "settings", "settings", f"set {setting_key}", "applied"
            )
            return (
                f"✅ {setting_key} обновлена: {shown}\n"
                "ⓘ Часть параметров применяется при следующем "
                "цикле проверки."
            )
        except Exception as exc:
            return f"❌ Ошибка изменения настройки: {exc}"

    async def _handle_settings(self, command_text: str) -> str:
        parts = command_text.strip().split()
        if len(parts) < 2 or parts[1].lower() in ("help", "?"):
            return self._settings_help()

        action = parts[1].lower()

        if action == "list":
            group = parts[2].strip() if len(parts) > 2 else None
            return self._settings_list(group)

        if action == "get":
            if len(parts) < 3:
                return "ℹ️ Использование: !settings get <KEY>"
            return self._settings_get(parts[2].strip().upper())

        if action == "set":
            if len(parts) < 4:
                return (
                    "ℹ️ Использование: !settings set <KEY> <значение>\n"
                    "Пример: !settings set CHECK_INTERVAL 120"
                )
            setting_key = parts[2].strip().upper()
            raw_value = command_text.split(maxsplit=3)[3].strip()
            return self._settings_set(setting_key, raw_value)

        return (
            f"ℹ️ Неизвестное действие «{action}».\n\n{self._SETTINGS_USAGE}"
        )

    async def _handle_zfs(self) -> str:
        try:
            import sqlite3

            from config.db_settings import BACKUP_DATABASE_CONFIG
            from core.config_manager import config_manager
        except Exception as exc:
            return f"❌ Не удалось загрузить модули ZFS: {exc}"

        db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
        if not db_path:
            return "❌ База бэкапов не настроена."

        zfs_servers = config_manager.get_setting("ZFS_SERVERS", {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}
        allowed_servers = {
            name
            for name, server_value in zfs_servers.items()
            if not isinstance(server_value, dict) or server_value.get("enabled", True)
        }

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT s.server_name, s.pool_name, s.pool_state, s.received_at
                FROM zfs_pool_status s
                JOIN (
                    SELECT server_name, pool_name, MAX(received_at) AS last_seen
                    FROM zfs_pool_status
                    GROUP BY server_name, pool_name
                ) latest
                ON s.server_name = latest.server_name
                AND s.pool_name = latest.pool_name
                AND s.received_at = latest.last_seen
                ORDER BY s.server_name, s.pool_name
                """
            )
            rows = cursor.fetchall()
        except Exception as exc:
            if "no such table: zfs_pool_status" in str(exc):
                return "❌ Таблица ZFS ещё не создана. Дождитесь первого письма мониторинга."
            return f"❌ Не удалось получить статусы ZFS: {exc}"
        finally:
            conn.close()

        if allowed_servers:
            rows = [row for row in rows if row[0] in allowed_servers]
        else:
            rows = []

        if not rows:
            return "🧊 Мониторинг ZFS\n\n❌ Нет данных по пулам ZFS."

        lines = ["🧊 Мониторинг ZFS", "", "📊 Текущее состояние пулов", ""]
        healthy_states = {"ONLINE"}
        current_server = None
        for server_name, pool_name, pool_state, received_at in rows:
            if server_name != current_server:
                if current_server is not None:
                    lines.append("")
                lines.append(f"🖥 {server_name}")
                current_server = server_name
            normalized_state = str(pool_state or "").strip().upper()
            marker = "🟢" if normalized_state in healthy_states else "🔴"
            lines.append(f"{marker} {pool_name}: {pool_state} ({received_at})")
        return "\n".join(lines)

    @staticmethod
    def _format_time_ago(time_str: str) -> str:
        """Человекочитаемое 'Xд Yч назад' (как format_time_ago в Telegram)."""
        try:
            if not time_str:
                return "неизвестно"
            time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            hours_ago = int((datetime.now() - time_obj).total_seconds() / 3600)
            if hours_ago >= 24:
                return f"{hours_ago // 24}д {hours_ago % 24}ч назад"
            return f"{hours_ago}ч назад"
        except Exception:
            return "ошибка времени"

    async def _handle_stock(self, hours: int = 24) -> str:
        try:
            import sqlite3
            from datetime import timedelta

            from config.db_settings import BACKUP_DATABASE_CONFIG
        except Exception as exc:
            return f"❌ Не удалось загрузить модули остатков: {exc}"

        db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
        if not db_path:
            return "❌ База бэкапов не настроена."

        since_time = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                WITH normalized AS (
                    SELECT
                        id,
                        COALESCE(source_name, 'Основное предприятие') AS source_name,
                        CASE
                            WHEN supplier_name IS NULL OR supplier_name = 'неизвестно'
                                THEN COALESCE(source_name, 'Основное предприятие')
                            ELSE supplier_name
                        END AS supplier_name,
                        status,
                        rows_count,
                        error_sample,
                        received_at
                    FROM stock_load_results
                    WHERE received_at >= ?
                ),
                ranked AS (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (
                            PARTITION BY source_name, supplier_name
                            ORDER BY received_at DESC, id DESC
                        ) AS row_num
                    FROM normalized
                )
                SELECT source_name, supplier_name, status, rows_count, error_sample, received_at
                FROM ranked
                WHERE row_num = 1
                ORDER BY source_name, supplier_name
                """,
                (since_time,),
            )
            results = cursor.fetchall()
        except Exception as exc:
            if "no such table: stock_load_results" in str(exc):
                return "❌ Таблица остатков ещё не создана."
            return f"❌ Не удалось получить данные по остаткам: {exc}"
        finally:
            conn.close()

        header = f"📦 Загрузка остатков 1С (за {hours}ч)"
        if not results:
            return f"{header}\n\n❌ Нет данных за последние {hours} часов."

        grouped: Dict[str, List[Tuple]] = {}
        for source_name, supplier, status, rows_count, error_sample, received_at in results:
            grouped.setdefault(source_name or "Основное предприятие", []).append(
                (supplier, status, rows_count, error_sample, received_at)
            )
        total_suppliers = sum(len(items) for items in grouped.values())

        lines: List[str] = [header, f"Всего поставщиков: {total_suppliers}", ""]
        for source_name, items in grouped.items():
            lines.append(f"{source_name} ({len(items)})")
            for supplier, status, rows_count, error_sample, received_at in items:
                icon = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
                rows_text = f"{rows_count} строк" if rows_count else "строки: —"
                error_text = f" — {error_sample}" if error_sample else ""
                time_ago = self._format_time_ago(received_at)
                lines.append(f"{icon} {supplier} ({rows_text}){error_text} ({time_ago})")
            lines.append("")
        return "\n".join(lines).rstrip()

    def _control_menu_text(self) -> str:
        lines = [
            "🤖 Управление мониторингом (паритет с Telegram).",
            "Жми кнопки-реакции под этим сообщением или пиши команды:",
            "",
        ]
        for emoji, command in MENU_BUTTONS:
            desc = _MENU_DESCRIPTIONS.get(command, "")
            lines.append(f"{emoji} {command} — {desc}" if desc else f"{emoji} {command}")
        lines += [
            "",
            "Команды с аргументом:",
            "• !settings — хелп и список всех параметров",
            "• !settings list [группа] — параметры со значениями",
            "• !settings get <KEY> — значение настройки",
            "• !settings set <KEY> <значение> — изменить настройку",
            "• !help — краткая справка по Matrix-командам",
            "• !diag / !ping — диагностика command-bot",
            "",
            "Длинные списки приходят несколькими сообщениями "
            "с маркером (n/total).",
        ]
        return "\n".join(lines)

    def _help_text(self) -> str:
        return (
            "🆘 Краткая справка Matrix command-bot:\n\n"
            "• !menu или !start — главное меню с кнопками-реакциями\n"
            "• !status — доступность всех серверов\n"
            "• !report — утренний/сводный отчёт\n"
            "• !servers — список серверов под мониторингом\n"
            "• !pause / !resume — пауза и возобновление мониторинга\n"
            "• !silent / !loud / !auto — режим тишины\n"
            "• !extensions (!ext) — меню расширений (бэкапы, ресурсы, ZFS)\n"
            "• !about — версия и сведения о боте\n"
            "• !settings — управление настройками (help/list/get/set)\n"
            "• !diag / !ping — диагностика command-bot\n\n"
            "Подсказка: открой !menu и жми кнопки-реакции под сообщением.\n"
            "Пример настройки: !settings get CHECK_INTERVAL"
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

        if command in {"!start", "!menu"}:
            return command, self._control_menu_text()
        if command == "!help":
            return command, self._help_text()
        if command in {"!extensions", "!ext"}:
            return command, self._extensions_menu_text()
        if command == "!backup":
            if "backup_monitor" not in self._enabled_extensions():
                return command, (
                    "❌ Команда !backup недоступна: расширение "
                    "«backup_monitor» выключено."
                )
            parts = normalized.split(maxsplit=1)
            arg = parts[1].strip() if len(parts) > 1 else ""
            if arg:
                return command, await self._handle_backup_host_detail(arg)
            return command, await self._handle_ext_proxmox_backup()
        if command == "!dbbackup":
            if "database_backup_monitor" not in self._enabled_extensions():
                return command, (
                    "❌ Команда !dbbackup недоступна: расширение "
                    "«database_backup_monitor» выключено."
                )
            parts = normalized.split(maxsplit=1)
            arg = parts[1].strip() if len(parts) > 1 else ""
            if arg:
                return command, await self._handle_db_backup_detail(arg)
            return command, await self._handle_ext_db_backup()
        ext_item = _EXT_ITEM_BY_COMMAND.get(command)
        if ext_item is not None:
            return command, await self._run_extension_command(ext_item)
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
            if routed_command in {"!start", "!menu"}:
                await self._post_menu(room_id, response_text)
            elif routed_command in {"!extensions", "!ext"}:
                await self._post_extensions_menu(room_id)
            elif routed_command == "!backup" and len(command_text.split()) <= 1:
                # «!backup» без аргумента — сводка + кнопки по серверам.
                # «!backup <хост>» уже вернул готовую детализацию текстом.
                await self._post_backup_menu(room_id, response_text)
            elif routed_command == "!dbbackup" and len(command_text.split()) <= 1:
                # «!dbbackup» без аргумента — сводка + кнопки по базам.
                # «!dbbackup <база>» уже вернул статистику текстом.
                await self._post_dbbackup_menu(room_id, response_text)
            else:
                await self._send_long_text(room_id, response_text)
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

    def _ext_command_by_emoji(self, key: str) -> Optional[str]:
        """Резолвит emoji подменю в команду расширения только если
        соответствующее расширение сейчас включено."""
        if not key:
            return None
        enabled = self._enabled_extensions()
        for item in EXTENSION_MENU_ITEMS:
            if item.emoji == key and item.extension_id in enabled:
                return item.command
        return None

    async def _process_reaction(self, room: MatrixRoom, event) -> None:
        sender = getattr(event, "sender", "") or ""
        room_id = getattr(room, "room_id", "") or self.default_room_id
        reaction_event_id = getattr(event, "event_id", "") or ""

        if sender and sender == getattr(self.client, "user_id", None):
            return

        if reaction_event_id and reaction_event_id in self._processed_reactions:
            return

        target_event_id, key = self._reaction_target_and_key(event)
        if not target_event_id:
            return

        is_main_menu = target_event_id in self._menu_event_ids
        is_ext_menu = target_event_id in self._ext_menu_event_ids
        is_backup_menu = target_event_id in self._backup_menu_event_ids
        is_dbbackup_menu = target_event_id in self._dbbackup_menu_event_ids
        if not (
            is_main_menu or is_ext_menu or is_backup_menu or is_dbbackup_menu
        ):
            return

        normalized_key = (key or "").strip()
        if is_backup_menu:
            # Ключ реакции — имя сервера Proxmox. Игнорируем посторонние
            # emoji-реакции, реагируем только на known-хосты.
            if normalized_key and normalized_key in set(self._proxmox_backup_hosts()):
                command = f"!backup {normalized_key}"
            else:
                command = ""
        elif is_dbbackup_menu:
            # Ключ реакции — лейбл базы из последнего меню !dbbackup.
            # Посторонние emoji-реакции под сводкой игнорируем.
            if normalized_key and normalized_key in self._dbbackup_index:
                command = f"!dbbackup {normalized_key}"
            else:
                command = ""
        elif is_ext_menu:
            command = self._ext_command_by_emoji(key) or self._ext_command_by_emoji(
                normalized_key
            )
        else:
            command = _BUTTON_BY_EMOJI.get(key) or _BUTTON_BY_EMOJI.get(normalized_key)
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
        info_log(
            "ⓘ Отладка управляется на стороне сервера (из command-bot убрана). "
            "Команды: python -c \"from modules.debug import debug_manager; "
            "debug_manager.toggle_debug_mode(True)\" — включить DEBUG; "
            "...toggle_debug_mode(False) — выключить; "
            "...get_debug_info() — статус. Файл: data/debug_config.json."
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
