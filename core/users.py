"""
/core/users.py
Server Monitoring System v8.65.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Multi-user registry: users, their channels and personal preferences
Система мониторинга серверов
Версия: 8.65.0
Автор: Александр Суханов (c)
Лицензия: MIT

Реестр пользователей системы мониторинга.

Разделение ответственности:

* **Общие настройки сбора данных** (серверы, интервалы, паттерны писем,
  учётные данные, расписание сбора) остаются глобальными — они лежат в
  таблице ``settings`` и одинаковы для всех. Персонализировать их нельзя:
  данные собираются один раз для всей системы.
* **Персональные настройки доставки** (состав отчёта, какие оповещения
  получать, личные тихие часы) хранятся здесь, отдельно на каждого
  пользователя.

Каждый пользователь может иметь свои каналы обмена с ботом:
``telegram`` (chat_id), ``matrix`` (room_id), ``mobile`` (subject токена
мобильного клиента), ``web`` (логин веб-интерфейса). Один пользователь —
сколько угодно каналов; один канал принадлежит ровно одному пользователю.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from lib.logging import debug_log, error_log

# --- Типы каналов обмена -------------------------------------------------

CHANNEL_TELEGRAM = "telegram"
CHANNEL_MATRIX = "matrix"
CHANNEL_MOBILE = "mobile"
CHANNEL_WEB = "web"

CHANNEL_TYPES = (CHANNEL_TELEGRAM, CHANNEL_MATRIX, CHANNEL_MOBILE, CHANNEL_WEB)

CHANNEL_LABELS = {
    CHANNEL_TELEGRAM: "💬 Telegram",
    CHANNEL_MATRIX: "🔷 Matrix",
    CHANNEL_MOBILE: "📱 Android",
    CHANNEL_WEB: "🌐 Веб-интерфейс",
}

# --- Роли ----------------------------------------------------------------

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLES = (ROLE_ADMIN, ROLE_USER)

# --- Персональные настройки ----------------------------------------------

PREF_REPORT_EXTENSIONS = "REPORT_EXTENSIONS"
PREF_REPORTS_ENABLED = "REPORTS_ENABLED"
PREF_ALERTS_ENABLED = "ALERTS_ENABLED"
PREF_ALERT_LEVELS = "ALERT_LEVELS"
PREF_ALERT_CATEGORIES = "ALERT_CATEGORIES"
PREF_QUIET_HOURS_ENABLED = "QUIET_HOURS_ENABLED"
PREF_QUIET_START = "QUIET_START"
PREF_QUIET_END = "QUIET_END"

ALERT_LEVELS = ("critical", "warning", "info")

ALERT_LEVEL_LABELS = {
    "critical": "🚨 Критические",
    "warning": "⚠️ Предупреждения",
    "info": "ℹ️ Информационные",
}

# Категории оповещений: базовый функционал + расширения. Категория
# передаётся в `lib.alerts.send_alert(category=...)`; неизвестные категории
# считаются «системными» и приходят всем, кто вообще получает оповещения.
ALERT_CATEGORY_AVAILABILITY = "availability"
ALERT_CATEGORY_RESOURCES = "resources"
ALERT_CATEGORY_SYSTEM = "system"

BASE_ALERT_CATEGORIES = (
    ALERT_CATEGORY_AVAILABILITY,
    ALERT_CATEGORY_RESOURCES,
    ALERT_CATEGORY_SYSTEM,
)

BASE_ALERT_CATEGORY_LABELS = {
    ALERT_CATEGORY_AVAILABILITY: "🖥 Доступность серверов",
    ALERT_CATEGORY_RESOURCES: "💻 Ресурсы серверов",
    ALERT_CATEGORY_SYSTEM: "⚙️ Системные события",
}


def alert_categories() -> List[str]:
    """Полный список категорий оповещений: базовые + расширения."""
    categories = list(BASE_ALERT_CATEGORIES)
    try:
        from lib.report_settings import REPORT_CAPABLE_EXTENSIONS

        for ext_id in REPORT_CAPABLE_EXTENSIONS:
            if ext_id not in categories:
                categories.append(ext_id)
    except Exception:  # pragma: no cover - защита от проблем с импортом
        pass
    return categories


def alert_category_label(category: str) -> str:
    """Человекочитаемая подпись категории оповещений."""
    if category in BASE_ALERT_CATEGORY_LABELS:
        return BASE_ALERT_CATEGORY_LABELS[category]
    try:
        from lib.report_settings import get_report_extension_label

        return get_report_extension_label(category)
    except Exception:  # pragma: no cover
        return category


def _default_report_extensions() -> List[str]:
    try:
        from lib.report_settings import DEFAULT_REPORT_EXTENSIONS

        return list(DEFAULT_REPORT_EXTENSIONS)
    except Exception:  # pragma: no cover
        return []


# Значения по умолчанию персональных настроек. Callable — вычисляется на
# момент чтения (списки расширений зависят от состава системы).
PREFERENCE_DEFAULTS: Dict[str, Any] = {
    PREF_REPORT_EXTENSIONS: _default_report_extensions,
    PREF_REPORTS_ENABLED: True,
    PREF_ALERTS_ENABLED: True,
    PREF_ALERT_LEVELS: lambda: list(ALERT_LEVELS),
    PREF_ALERT_CATEGORIES: alert_categories,
    PREF_QUIET_HOURS_ENABLED: False,
    PREF_QUIET_START: 22,
    PREF_QUIET_END: 8,
}

# Только эти ключи персонализируются. Всё остальное (сбор данных) —
# общесистемное и живёт в таблице `settings`.
PERSONAL_PREFERENCE_KEYS = tuple(PREFERENCE_DEFAULTS.keys())


class UserRegistryError(Exception):
    """Ошибка операций с реестром пользователей."""


class UserRegistry:
    """Реестр пользователей, их каналов и персональных настроек.

    Хранится в той же БД, что и настройки (`data/settings.db`), через
    соединение `core.config_manager.config_manager` — отдельное на поток.
    """

    def __init__(self) -> None:
        self._schema_ready = False
        self._bootstrap_done = False
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Схема и подключение
    # ------------------------------------------------------------------

    def _connection(self) -> sqlite3.Connection:
        from core.config_manager import config_manager

        conn = config_manager.get_connection()
        try:
            conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            # Соединение потока могли закрыть снаружи (веб-интерфейс берёт
            # его же для таблицы mobile_api_tokens) — переоткрываем.
            config_manager.close_connection()
            conn = config_manager.get_connection()
        # Веб-интерфейс сбрасывает row_factory в None на общем соединении.
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_schema(self) -> None:
        """Создаёт таблицы реестра (идемпотентно)."""
        if self._schema_ready:
            return
        with self._lock:
            if self._schema_ready:
                return
            conn = self._connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    role TEXT DEFAULT 'user',
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    channel_type TEXT NOT NULL,
                    channel_ref TEXT NOT NULL,
                    title TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(channel_type, channel_ref),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, key),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_channels_user ON user_channels(user_id)"
            )
            conn.commit()
            self._schema_ready = True

    # ------------------------------------------------------------------
    # Пользователи
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"]),
            "username": row["username"],
            "display_name": row["display_name"] or row["username"],
            "role": row["role"] or ROLE_USER,
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
        }

    def list_users(self, include_disabled: bool = True) -> List[Dict[str, Any]]:
        """Все пользователи реестра (по умолчанию — включая выключенных)."""
        self.ensure_schema()
        self.bootstrap_if_empty()
        query = "SELECT * FROM users"
        if not include_disabled:
            query += " WHERE enabled = 1"
        query += " ORDER BY id"
        try:
            cursor = self._connection().cursor()
            cursor.execute(query)
            return [self._row_to_user(row) for row in cursor.fetchall()]
        except Exception as exc:
            error_log(f"Ошибка чтения списка пользователей: {exc}")
            return []

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Пользователь по внутреннему id."""
        self.ensure_schema()
        try:
            cursor = self._connection().cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
            row = cursor.fetchone()
        except Exception as exc:
            error_log(f"Ошибка чтения пользователя {user_id}: {exc}")
            return None
        return self._row_to_user(row) if row else None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Пользователь по логину (регистронезависимо)."""
        self.ensure_schema()
        try:
            cursor = self._connection().cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (str(username).strip(),),
            )
            row = cursor.fetchone()
        except Exception as exc:
            error_log(f"Ошибка чтения пользователя {username}: {exc}")
            return None
        return self._row_to_user(row) if row else None

    def create_user(
        self,
        username: str,
        display_name: Optional[str] = None,
        role: str = ROLE_USER,
        enabled: bool = True,
    ) -> Dict[str, Any]:
        """Создаёт пользователя. Логин уникален (регистронезависимо)."""
        self.ensure_schema()
        username = str(username or "").strip()
        if not username:
            raise UserRegistryError("Логин пользователя не может быть пустым")
        if role not in ROLES:
            role = ROLE_USER
        if self.get_user_by_username(username):
            raise UserRegistryError(f"Пользователь «{username}» уже существует")

        conn = self._connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, display_name, role, enabled)
            VALUES (?, ?, ?, ?)
            """,
            (username, display_name or username, role, 1 if enabled else 0),
        )
        conn.commit()
        user_id = int(cursor.lastrowid)
        debug_log(f"👤 Создан пользователь {username} (id={user_id}, role={role})")
        created = self.get_user(user_id)
        if created is None:  # pragma: no cover - insert только что прошёл
            raise UserRegistryError("Пользователь не создан")
        return created

    def update_user(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        role: Optional[str] = None,
        enabled: Optional[bool] = None,
        username: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Обновляет карточку пользователя (только переданные поля)."""
        self.ensure_schema()
        user = self.get_user(user_id)
        if not user:
            return None

        fields: List[str] = []
        values: List[Any] = []
        if username is not None:
            new_username = str(username).strip()
            if not new_username:
                raise UserRegistryError("Логин пользователя не может быть пустым")
            existing = self.get_user_by_username(new_username)
            if existing and int(existing["id"]) != int(user_id):
                raise UserRegistryError(f"Пользователь «{new_username}» уже существует")
            fields.append("username = ?")
            values.append(new_username)
        if display_name is not None:
            fields.append("display_name = ?")
            values.append(str(display_name).strip() or user["username"])
        if role is not None:
            if role not in ROLES:
                raise UserRegistryError(f"Неизвестная роль: {role}")
            # Последнего администратора нельзя разжаловать — иначе реестром
            # станет некому управлять.
            if (
                user["role"] == ROLE_ADMIN
                and role != ROLE_ADMIN
                and self.count_admins(exclude_user_id=user_id) == 0
            ):
                raise UserRegistryError(
                    "Нельзя снять роль с последнего администратора: "
                    "сначала назначьте администратором кого-то ещё"
                )
            fields.append("role = ?")
            values.append(role)
        if enabled is not None:
            if (
                not enabled
                and user["role"] == ROLE_ADMIN
                and self.count_admins(exclude_user_id=user_id) == 0
            ):
                raise UserRegistryError(
                    "Нельзя выключить последнего администратора: "
                    "сначала назначьте администратором кого-то ещё"
                )
            fields.append("enabled = ?")
            values.append(1 if enabled else 0)

        if not fields:
            return user

        fields.append("updated_at = CURRENT_TIMESTAMP")
        conn = self._connection()
        conn.cursor().execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
            (*values, int(user_id)),
        )
        conn.commit()
        return self.get_user(user_id)

    def count_admins(self, exclude_user_id: Optional[int] = None) -> int:
        """Сколько включённых администраторов в реестре (кроме указанного)."""
        self.ensure_schema()
        query = "SELECT COUNT(*) FROM users WHERE enabled = 1 AND role = ?"
        params: List[Any] = [ROLE_ADMIN]
        if exclude_user_id is not None:
            query += " AND id != ?"
            params.append(int(exclude_user_id))
        try:
            cursor = self._connection().cursor()
            cursor.execute(query, params)
            return int(cursor.fetchone()[0])
        except Exception as exc:  # pragma: no cover
            error_log(f"Ошибка подсчёта администраторов: {exc}")
            return 0

    def has_reachable_admin(self, channel_type: Optional[str] = None) -> bool:
        """Есть ли администратор, до которого можно достучаться каналом.

        Администратор без единого канала обмена ничем управлять не может —
        для UI это равносильно его отсутствию, поэтому такие не считаются.
        """
        self.ensure_schema()
        self.bootstrap_if_empty()
        query = """
            SELECT COUNT(*) FROM users u
            JOIN user_channels c ON c.user_id = u.id AND c.enabled = 1
            WHERE u.enabled = 1 AND u.role = ?
        """
        params: List[Any] = [ROLE_ADMIN]
        if channel_type is not None:
            query += " AND c.channel_type = ?"
            params.append(channel_type)
        try:
            cursor = self._connection().cursor()
            cursor.execute(query, params)
            return int(cursor.fetchone()[0]) > 0
        except Exception as exc:  # pragma: no cover
            error_log(f"Ошибка поиска достижимого администратора: {exc}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя вместе с каналами и персональными настройками."""
        self.ensure_schema()
        user = self.get_user(user_id)
        if (
            user
            and user["role"] == ROLE_ADMIN
            and user["enabled"]
            and self.count_admins(exclude_user_id=user_id) == 0
        ):
            raise UserRegistryError(
                "Нельзя удалить последнего администратора: "
                "сначала назначьте администратором кого-то ещё"
            )
        conn = self._connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_channels WHERE user_id = ?", (int(user_id),))
        cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (int(user_id),))
        cursor.execute("DELETE FROM users WHERE id = ?", (int(user_id),))
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            debug_log(f"👤 Удалён пользователь id={user_id}")
        return deleted

    # ------------------------------------------------------------------
    # Каналы обмена
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_ref(channel_type: str, channel_ref: Any) -> str:
        ref = str(channel_ref or "").strip()
        if channel_type in (CHANNEL_MATRIX, CHANNEL_WEB):
            return ref
        return ref

    def list_channels(
        self, user_id: Optional[int] = None, channel_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Каналы пользователя (или все каналы указанного типа)."""
        self.ensure_schema()
        self.bootstrap_if_empty()
        query = "SELECT * FROM user_channels WHERE 1 = 1"
        params: List[Any] = []
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(int(user_id))
        if channel_type is not None:
            query += " AND channel_type = ?"
            params.append(channel_type)
        query += " ORDER BY channel_type, id"
        try:
            cursor = self._connection().cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except Exception as exc:
            error_log(f"Ошибка чтения каналов пользователей: {exc}")
            return []
        return [
            {
                "id": int(row["id"]),
                "user_id": int(row["user_id"]),
                "channel_type": row["channel_type"],
                "channel_ref": row["channel_ref"],
                "title": row["title"],
                "enabled": bool(row["enabled"]),
            }
            for row in rows
        ]

    def link_channel(
        self,
        user_id: int,
        channel_type: str,
        channel_ref: Any,
        title: Optional[str] = None,
        enabled: bool = True,
    ) -> Dict[str, Any]:
        """Привязывает канал к пользователю (перепривязывает, если занят)."""
        self.ensure_schema()
        if channel_type not in CHANNEL_TYPES:
            raise UserRegistryError(f"Неизвестный тип канала: {channel_type}")
        ref = self._normalize_ref(channel_type, channel_ref)
        if not ref:
            raise UserRegistryError("Идентификатор канала не может быть пустым")
        if not self.get_user(user_id):
            raise UserRegistryError(f"Пользователь id={user_id} не найден")

        conn = self._connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_channels (user_id, channel_type, channel_ref, title, enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(channel_type, channel_ref) DO UPDATE SET
                user_id = excluded.user_id,
                title = COALESCE(excluded.title, user_channels.title),
                enabled = excluded.enabled
            """,
            (int(user_id), channel_type, ref, title, 1 if enabled else 0),
        )
        conn.commit()
        debug_log(f"🔗 Канал {channel_type}:{ref} привязан к пользователю id={user_id}")
        channels = self.list_channels(user_id=user_id, channel_type=channel_type)
        for channel in channels:
            if channel["channel_ref"] == ref:
                return channel
        raise UserRegistryError("Канал не привязан")  # pragma: no cover

    def unlink_channel(self, channel_type: str, channel_ref: Any) -> bool:
        """Отвязывает канал (по типу и идентификатору)."""
        self.ensure_schema()
        ref = self._normalize_ref(channel_type, channel_ref)
        conn = self._connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_channels WHERE channel_type = ? AND channel_ref = ?",
            (channel_type, ref),
        )
        conn.commit()
        return cursor.rowcount > 0

    def resolve_user(self, channel_type: str, channel_ref: Any) -> Optional[Dict[str, Any]]:
        """Ищет пользователя по каналу обмена.

        Это точка входа всех ботов и приложений: Telegram передаёт chat_id,
        Matrix — room_id или MXID отправителя, мобильный клиент — subject
        токена, веб — логин.
        """
        self.ensure_schema()
        self.bootstrap_if_empty()
        ref = self._normalize_ref(channel_type, channel_ref)
        if not ref:
            return None
        try:
            cursor = self._connection().cursor()
            cursor.execute(
                """
                SELECT u.* FROM users u
                JOIN user_channels c ON c.user_id = u.id
                WHERE c.channel_type = ? AND c.channel_ref = ? AND c.enabled = 1
                LIMIT 1
                """,
                (channel_type, ref),
            )
            row = cursor.fetchone()
        except Exception as exc:
            error_log(f"Ошибка поиска пользователя по каналу {channel_type}:{ref}: {exc}")
            return None
        return self._row_to_user(row) if row else None

    def resolve_user_id(self, channel_type: str, channel_ref: Any) -> Optional[int]:
        """id пользователя по каналу обмена (или None)."""
        user = self.resolve_user(channel_type, channel_ref)
        return int(user["id"]) if user else None

    # ------------------------------------------------------------------
    # Персональные настройки
    # ------------------------------------------------------------------

    @staticmethod
    def default_preference(key: str) -> Any:
        """Значение персональной настройки по умолчанию."""
        default = PREFERENCE_DEFAULTS.get(key)
        return default() if callable(default) else default

    def get_preference(self, user_id: Optional[int], key: str, default: Any = None) -> Any:
        """Персональная настройка пользователя.

        Порядок разрешения: значение пользователя → глобальное значение
        того же ключа (если ключ есть в таблице ``settings``) → дефолт.
        Глобальное значение работает как «настройка по умолчанию для всех»:
        админ задаёт её один раз, а пользователь при желании переопределяет.
        """
        if key not in PERSONAL_PREFERENCE_KEYS:
            raise UserRegistryError(f"Настройка {key} не персонализируется")

        if user_id is not None:
            self.ensure_schema()
            try:
                cursor = self._connection().cursor()
                cursor.execute(
                    "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
                    (int(user_id), key),
                )
                row = cursor.fetchone()
            except Exception as exc:
                error_log(f"Ошибка чтения настройки {key} пользователя {user_id}: {exc}")
                row = None
            if row is not None and row[0] is not None:
                try:
                    return json.loads(row[0])
                except (ValueError, TypeError):
                    return row[0]

        global_value = self._global_default(key)
        if global_value is not None:
            return global_value

        if default is not None:
            return default
        return self.default_preference(key)

    @staticmethod
    def _global_default(key: str) -> Any:
        """Глобальное значение настройки — дефолт для всех пользователей."""
        try:
            from core.config_manager import config_manager

            return config_manager.get_setting(key, None, use_cache=False)
        except Exception:  # pragma: no cover - БД может быть недоступна
            return None

    def set_preference(self, user_id: int, key: str, value: Any) -> bool:
        """Сохраняет персональную настройку пользователя."""
        if key not in PERSONAL_PREFERENCE_KEYS:
            raise UserRegistryError(f"Настройка {key} не персонализируется")
        self.ensure_schema()
        try:
            payload = json.dumps(value, ensure_ascii=False)
            conn = self._connection()
            conn.cursor().execute(
                """
                INSERT INTO user_preferences (user_id, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (int(user_id), key, payload),
            )
            conn.commit()
            return True
        except Exception as exc:
            error_log(f"Ошибка сохранения настройки {key} пользователя {user_id}: {exc}")
            return False

    def reset_preference(self, user_id: int, key: str) -> bool:
        """Сбрасывает персональную настройку к общесистемному значению."""
        self.ensure_schema()
        try:
            conn = self._connection()
            conn.cursor().execute(
                "DELETE FROM user_preferences WHERE user_id = ? AND key = ?",
                (int(user_id), key),
            )
            conn.commit()
            return True
        except Exception as exc:
            error_log(f"Ошибка сброса настройки {key} пользователя {user_id}: {exc}")
            return False

    def get_preferences(self, user_id: Optional[int]) -> Dict[str, Any]:
        """Все персональные настройки пользователя (с дефолтами)."""
        return {key: self.get_preference(user_id, key) for key in PERSONAL_PREFERENCE_KEYS}

    # ------------------------------------------------------------------
    # Фильтрация доставки
    # ------------------------------------------------------------------

    def wants_alert(
        self,
        user_id: Optional[int],
        alert_type: str = "info",
        category: Optional[str] = None,
        force: bool = False,
        now: Optional[datetime] = None,
    ) -> bool:
        """Нужно ли доставлять пользователю это оповещение."""
        if user_id is None:
            return True

        user = self.get_user(user_id)
        if user is not None and not user["enabled"]:
            return False

        if not self.get_preference(user_id, PREF_ALERTS_ENABLED):
            return False

        levels = self.get_preference(user_id, PREF_ALERT_LEVELS) or []
        if alert_type not in levels:
            return False

        if category:
            known = alert_categories()
            if category in known:
                selected = self.get_preference(user_id, PREF_ALERT_CATEGORIES) or []
                if category not in selected:
                    return False

        if force or alert_type == "critical":
            return True

        if self.get_preference(user_id, PREF_QUIET_HOURS_ENABLED):
            start = int(self.get_preference(user_id, PREF_QUIET_START) or 0)
            end = int(self.get_preference(user_id, PREF_QUIET_END) or 0)
            if self._in_quiet_hours(start, end, now or datetime.now()):
                return False

        return True

    @staticmethod
    def _in_quiet_hours(start: int, end: int, now: datetime) -> bool:
        """Попадает ли момент в интервал тихих часов (с переходом через полночь)."""
        start %= 24
        end %= 24
        hour = now.hour
        if start == end:
            return False
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    def wants_report(self, user_id: Optional[int]) -> bool:
        """Получает ли пользователь утренний/сводный отчёт."""
        if user_id is None:
            return True
        user = self.get_user(user_id)
        if user is not None and not user["enabled"]:
            return False
        return bool(self.get_preference(user_id, PREF_REPORTS_ENABLED))

    # ------------------------------------------------------------------
    # Адресаты доставки
    # ------------------------------------------------------------------

    def delivery_targets(
        self,
        alert_type: str = "info",
        category: Optional[str] = None,
        force: bool = False,
        report: bool = False,
    ) -> List[Dict[str, Any]]:
        """Кому и куда доставлять сообщение.

        Возвращает список ``{"user": {...}, "telegram": [chat_id],
        "matrix": [room_id]}`` только для тех пользователей, кто по своим
        настройкам должен получить сообщение и у кого есть хотя бы один
        канал доставки.
        """
        targets: List[Dict[str, Any]] = []
        for user in self.list_users(include_disabled=False):
            user_id = int(user["id"])
            if report:
                if not self.wants_report(user_id):
                    continue
            elif not self.wants_alert(user_id, alert_type, category, force):
                continue

            channels = self.list_channels(user_id=user_id)
            telegram = [
                c["channel_ref"]
                for c in channels
                if c["channel_type"] == CHANNEL_TELEGRAM and c["enabled"]
            ]
            matrix = [
                c["channel_ref"]
                for c in channels
                if c["channel_type"] == CHANNEL_MATRIX and c["enabled"]
            ]
            if not telegram and not matrix:
                continue
            targets.append({"user": user, "telegram": telegram, "matrix": matrix})
        return targets

    def has_users(self) -> bool:
        """Есть ли в реестре хотя бы один пользователь с каналом доставки."""
        self.ensure_schema()
        self.bootstrap_if_empty()
        try:
            cursor = self._connection().cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE enabled = 1")
            return int(cursor.fetchone()[0]) > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Миграция с однопользовательской конфигурации
    # ------------------------------------------------------------------

    def bootstrap_if_empty(self) -> None:
        """Создаёт админа из существующих CHAT_IDS/MATRIX_ROOM_ID/WEB_LOGIN.

        Выполняется один раз: пока реестр пуст, система работает точно так
        же, как раньше (все каналы принадлежат одному администратору и
        получают одинаковый отчёт). Разделение пользователей начинается с
        первого добавленного администратором пользователя.
        """
        if self._bootstrap_done:
            return
        with self._lock:
            if self._bootstrap_done:
                return
            self._bootstrap_done = True
            try:
                self.ensure_schema()
                cursor = self._connection().cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                if int(cursor.fetchone()[0]) > 0:
                    return
                self._bootstrap_from_legacy_settings()
            except Exception as exc:  # pragma: no cover - миграция не критична
                debug_log(f"⚠️ Первичная миграция пользователей пропущена: {exc}")

    def _bootstrap_from_legacy_settings(self) -> None:
        from core.config_manager import config_manager

        admin = self.create_user(
            "admin",
            display_name="Администратор",
            role=ROLE_ADMIN,
        )
        admin_id = int(admin["id"])

        chat_ids = config_manager.get_setting("CHAT_IDS", [], use_cache=False) or []
        if isinstance(chat_ids, str):
            chat_ids = [part.strip() for part in chat_ids.split(",") if part.strip()]
        for chat_id in chat_ids:
            try:
                self.link_channel(admin_id, CHANNEL_TELEGRAM, chat_id, title="Telegram")
            except UserRegistryError as exc:
                debug_log(f"⚠️ Канал Telegram {chat_id} не привязан: {exc}")

        room_id = config_manager.get_setting("MATRIX_ROOM_ID", "", use_cache=False)
        if room_id:
            try:
                self.link_channel(admin_id, CHANNEL_MATRIX, room_id, title="Matrix")
            except UserRegistryError as exc:
                debug_log(f"⚠️ Канал Matrix {room_id} не привязан: {exc}")

        web_login = config_manager.get_setting("WEB_LOGIN", "", use_cache=False)
        if web_login:
            for channel_type in (CHANNEL_WEB, CHANNEL_MOBILE):
                try:
                    self.link_channel(admin_id, channel_type, web_login, title="Веб/Android")
                except UserRegistryError as exc:
                    debug_log(f"⚠️ Канал {channel_type} {web_login} не привязан: {exc}")

        # Состав отчёта админа наследует текущий общесистемный выбор.
        stored = config_manager.get_setting("REPORT_EXTENSIONS", None, use_cache=False)
        if stored:
            try:
                from lib.report_settings import normalize_report_extensions

                self.set_preference(
                    admin_id, PREF_REPORT_EXTENSIONS, normalize_report_extensions(stored)
                )
            except Exception as exc:  # pragma: no cover
                debug_log(f"⚠️ Состав отчёта админа не перенесён: {exc}")

        debug_log("👥 Реестр пользователей инициализирован из однопользовательских настроек")


# Глобальный экземпляр реестра
user_registry = UserRegistry()


# ---------------------------------------------------------------------------
# Удобные функции-обёртки (используются ботами и API)
# ---------------------------------------------------------------------------


def resolve_user(channel_type: str, channel_ref: Any) -> Optional[Dict[str, Any]]:
    """Пользователь по каналу обмена."""
    return user_registry.resolve_user(channel_type, channel_ref)


def resolve_user_id(channel_type: str, channel_ref: Any) -> Optional[int]:
    """id пользователя по каналу обмена."""
    return user_registry.resolve_user_id(channel_type, channel_ref)


def resolve_telegram_user(chat_id: Any) -> Optional[Dict[str, Any]]:
    """Пользователь Telegram-чата."""
    return user_registry.resolve_user(CHANNEL_TELEGRAM, chat_id)


def resolve_matrix_user(room_id: Any, sender: Any = None) -> Optional[Dict[str, Any]]:
    """Пользователь Matrix: сначала по MXID отправителя, затем по комнате."""
    if sender:
        user = user_registry.resolve_user(CHANNEL_MATRIX, sender)
        if user:
            return user
    return user_registry.resolve_user(CHANNEL_MATRIX, room_id)


def resolve_mobile_user(subject: Any, device_id: Any = None) -> Optional[Dict[str, Any]]:
    """Пользователь мобильного клиента.

    Порядок поиска: устройство (device_id) → subject токена → логин веба.
    Привязка по device_id позволяет развести пользователей мобильного
    клиента, даже когда учётные данные веб-интерфейса общие: администратор
    привязывает конкретное устройство к конкретному пользователю.
    """
    if device_id:
        user = user_registry.resolve_user(CHANNEL_MOBILE, device_id)
        if user:
            return user
    user = user_registry.resolve_user(CHANNEL_MOBILE, subject)
    if user:
        return user
    return user_registry.resolve_user(CHANNEL_WEB, subject)


def legacy_chat_ids() -> List[str]:
    """Общий список CHAT_IDS из настроек (однопользовательский режим)."""
    try:
        from core.config_manager import config_manager

        raw = config_manager.get_setting("CHAT_IDS", []) or []
    except Exception:  # pragma: no cover
        return []
    if isinstance(raw, str):
        return [part.strip() for part in raw.split(",") if part.strip()]
    return [str(item) for item in raw]


def is_authorized_telegram_chat(chat_id: Any) -> bool:
    """Разрешён ли чат к работе с ботом.

    Доступ даёт либо привязка чата к включённому пользователю реестра,
    либо присутствие чата в общем списке `CHAT_IDS` — чтобы обновление на
    многопользовательскую схему никого не отрезало от бота.
    """
    chat_ref = str(chat_id)
    user = resolve_telegram_user(chat_ref)
    if user and user.get("enabled"):
        return True
    return chat_ref in legacy_chat_ids()


def can_manage_users(user: Optional[Dict[str, Any]]) -> bool:
    """Может ли пользователь управлять реестром.

    Управление доступно администратору, а также — как аварийный выход —
    когда в реестре не осталось ни одного администратора с каналом связи.
    Без этого правила реестр можно было бы «запереть» (например, отдав
    последний чат администратора обычному пользователю) и чинить только
    правкой БД руками.

    Достижимость администратора проверяется по ВСЕМ каналам сразу, а не по
    тому, откуда пришла команда. Иначе аварийный выход открывался бы на
    каждом транспорте отдельно: администратор в Telegram есть, но в Matrix
    его нет — и обычный пользователь Matrix получал бы право удалять
    пользователей.
    """
    if user is not None and user.get("role") == ROLE_ADMIN and user.get("enabled", True):
        return True
    try:
        return not user_registry.has_reachable_admin()
    except Exception:  # pragma: no cover
        return False


def is_admin_telegram_chat(chat_id: Any) -> bool:
    """Может ли этот Telegram-чат управлять пользователями.

    Правила по убыванию приоритета:

    1. чат принадлежит пользователю с ролью администратора;
    2. чат перечислен в общем `CHAT_IDS` — до многопользовательского режима
       такие чаты имели полный доступ к настройкам бота, и оставить их без
       управления пользователями значило бы урезать права молча;
    3. чат вообще не привязан к пользователю (однопользовательский режим);
    4. во всём реестре не осталось достижимого администратора — ни на одном
       из каналов (аварийный выход).
    """
    chat_ref = str(chat_id)
    user = resolve_telegram_user(chat_ref)
    if user is not None and user.get("role") == ROLE_ADMIN and user.get("enabled", True):
        return True
    if chat_ref in legacy_chat_ids():
        return True
    if user is None:
        return True
    return can_manage_users(user)


def user_label(user: Optional[Dict[str, Any]]) -> str:
    """Подпись пользователя для UI."""
    if not user:
        return "—"
    name = user.get("display_name") or user.get("username") or "—"
    if user.get("role") == ROLE_ADMIN:
        return f"{name} 👑"
    return str(name)


def iter_enabled_users() -> Iterable[Dict[str, Any]]:
    """Итератор по включённым пользователям."""
    return iter(user_registry.list_users(include_disabled=False))
