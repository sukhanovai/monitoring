"""
/app/modules/morning_report.py
Server Monitoring System v8.63.11
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning Report Module
Система мониторинга серверов
Версия: 8.63.11
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль утреннего отчета
"""

import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone

from lib.logging import debug_log, info_log


class MorningReport:
    """Класс управления утренними отчетами"""

    def __init__(self):
        self.morning_data = {}
        self.last_report_date = None
        self.last_data_collection = None

    def collect_morning_data(self, manual_call=False):
        """Сбор данных для утреннего отчета"""
        try:
            info_log(
                "[MORNING_REPORT_COLLECTION] collect_start "
                f"manual_call={manual_call} now={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            from modules.availability import availability_monitor

            current_status = availability_monitor.get_current_status()

            self.morning_data = {
                "status": current_status,
                "collection_time": datetime.now(),
                "manual_call": manual_call,
            }

            debug_log(
                f"✅ Данные для отчета собраны: {len(current_status['ok'])} доступно, {len(current_status['failed'])} недоступно"
            )
            return True
        except Exception as e:
            debug_log(f"❌ Ошибка сбора данных для отчета: {e}")
            return False

    def generate_report_message(self):
        """Генерация сообщения отчета"""
        if not self.morning_data or "status" not in self.morning_data:
            return "❌ Нет данных для отчета"

        status = self.morning_data["status"]
        collection_time = self.morning_data.get("collection_time", datetime.now())
        is_manual = self.morning_data.get("manual_call", False)

        # Состав отчёта: какие расширения пользователь выбрал для включения
        # сведений помимо базовых данных мониторинга доступности.
        try:
            from lib.report_settings import get_report_extensions

            # use_cache=False — иначе после переключения состава отчёта в
            # настройках генерация читала бы устаревшее значение из кэша и
            # включение/выключение расширений не вступало бы в силу.
            report_extensions = set(get_report_extensions(use_cache=False))
        except Exception as exc:
            debug_log(f"⚠️ Не удалось получить состав отчёта: {exc}")
            from lib.report_settings import DEFAULT_REPORT_EXTENSIONS

            report_extensions = set(DEFAULT_REPORT_EXTENSIONS)

        total_servers = len(status["ok"]) + len(status["failed"])
        up_count = len(status["ok"])
        down_count = len(status["failed"])

        # Определяем тип отчета
        report_type = "Ручной отчёт" if is_manual else "Утренний отчёт"
        try:
            from config.settings import APP_VERSION
        except Exception:
            APP_VERSION = None

        from extensions.extension_manager import extension_manager
        from telegram.utils.helpers import escape_markdown

        def _selected(ext_id):
            return ext_id in report_extensions and extension_manager.is_extension_enabled(
                ext_id
            )

        period_label = "за 24ч" if is_manual else "за 16ч"
        period_hours = 24 if is_manual else 16

        # --- Сбор секций расширений ---
        # Каждая секция: {"title", "body", "has_issues"}.
        sections = []

        def add_section(title, result):
            body, has_issues = result
            sections.append({"title": title, "body": body, "has_issues": bool(has_issues)})

        # Бэкапы (Proxmox/БД/почта) — объединённая секция.
        show_proxmox = _selected("backup_monitor")
        show_databases = _selected("database_backup_monitor")
        show_mail = _selected("mail_backup_monitor")
        if show_proxmox or show_databases or show_mail:
            try:
                unavailable_hosts = set()
                for server in status.get("failed", []):
                    if server.get("name"):
                        unavailable_hosts.add(server.get("name"))
                    if server.get("ip"):
                        unavailable_hosts.add(server.get("ip"))
                add_section(
                    f"💾 Бэкапы ({period_label})",
                    self.get_backup_summary_for_report(
                        period_hours,
                        include_proxmox=show_proxmox,
                        include_databases=show_databases,
                        include_mail=show_mail,
                        unavailable_hosts=unavailable_hosts,
                    ),
                )
            except Exception as e:
                debug_log(f"⚠️ Ошибка получения данных о бэкапах: {e}")
                add_section("💾 Бэкапы", ("данные недоступны", True))

        if _selected("config_console_backup_monitor"):
            add_section(
                "🗂️ Бэкап конфигов и историй",
                self.get_config_console_summary_for_report(),
            )

        if _selected("nas_transfer_monitor"):
            add_section(
                f"📤 Передача бэкапов на NAS ({period_label})",
                self.get_nas_transfer_summary_for_report(period_hours),
            )

        if _selected("stock_load_monitor"):
            try:
                from extensions.backup_monitor.backup_utils import get_stock_load_summary

                add_section(
                    "📦 Загрузка остатков 1С",
                    (get_stock_load_summary(period_hours), False),
                )
            except Exception as e:
                debug_log(f"⚠️ Ошибка получения данных о загрузке остатков: {e}")
                add_section("📦 Загрузка остатков 1С", ("данные недоступны", True))

        if _selected("supplier_stock_files"):
            add_section(
                "🏷️ Остатки поставщиков",
                self.get_supplier_stock_summary_for_report(),
            )

        # ZFS: пулы; место и снэпшоты — встроенными строками, если их
        # расширения тоже выбраны. Если zfs_monitor не выбран, но выбраны
        # место/снэпшоты — показываем их отдельными секциями.
        show_zfs = _selected("zfs_monitor")
        show_free = _selected("zfs_pool_free_space_monitor")
        show_snap = _selected("snapshot_transfer_monitor")
        if show_zfs:
            try:
                add_section(
                    "🧊 Статусы ZFS",
                    self.get_zfs_summary_for_report(
                        include_free_space=show_free, include_snapshots=show_snap
                    ),
                )
            except Exception as e:
                debug_log(f"⚠️ Ошибка получения данных о ZFS: {e}")
                add_section("🧊 Статусы ZFS", ("данные недоступны", True))
        else:
            if show_free:
                add_section("💽 Свободное место ZFS", self.get_zfs_free_space_for_report())
            if show_snap:
                add_section("📸 Передачи снэпшотов", self.get_snapshot_transfer_for_report())

        if _selected("tls_cert_monitor"):
            add_section("🔐 TLS-сертификаты", self.get_tls_cert_summary_for_report())

        if _selected("resource_monitor"):
            add_section("💻 Ресурсы серверов", self.get_resources_summary_for_report())

        # --- Сборка сообщения ---
        divider = "━━━━━━━━━━━━━━━━━━"
        availability_has_issues = down_count > 0

        # Список проблемных областей для блока «Требует внимания».
        problem_areas = []
        if availability_has_issues:
            problem_areas.append(f"🖥 Недоступно серверов: {down_count}")
        problem_areas.extend(s["title"] for s in sections if s["has_issues"])

        report_icon = "🔴" if problem_areas else "🟢"
        message = f"{report_icon} *{report_type} мониторинга*\n"
        meta_parts = []
        if APP_VERSION:
            meta_parts.append(f"v{APP_VERSION}")
        meta_parts.append(collection_time.strftime("%d.%m.%Y"))
        meta_parts.append(collection_time.strftime("%H:%M"))
        message += "_" + " • ".join(meta_parts) + "_\n"
        message += divider + "\n"

        # Блок-итог состояния.
        if problem_areas:
            message += f"⚠️ *Требует внимания ({len(problem_areas)}):*\n"
            for area in problem_areas:
                message += f"• {area}\n"
        else:
            message += "✅ *Всё в норме* — критичных проблем не обнаружено\n"

        # Доступность серверов.
        avail_icon = "🔴" if availability_has_issues else "🟢"
        message += f"\n{avail_icon} *Доступность серверов*\n"
        availability_rows = [
            ("Всего", str(total_servers)),
            ("🟢 Доступно", str(up_count)),
            ("🔴 Недоступно", str(down_count)),
        ]
        message += self._render_key_value_table(availability_rows)

        if down_count > 0:
            message += f"\n🔴 *Проблемные серверы ({down_count})*\n"
            by_type = {}
            for server in status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)
            problem_rows = []
            for server_type, servers_list in sorted(by_type.items(), key=lambda item: str(item[0])):
                for s in servers_list:
                    safe_type = escape_markdown(str(server_type).upper(), version=1)
                    safe_name = escape_markdown(str(s.get("name", "")), version=1)
                    safe_ip = escape_markdown(str(s.get("ip", "")), version=1)
                    problem_rows.append((safe_type, safe_name, safe_ip))
            message += self._render_table(
                headers=("Тип", "Сервер", "IP"),
                rows=problem_rows,
            )

        # Секции расширений с цветовым маркером состояния.
        for section in sections:
            icon = "🔴" if section["has_issues"] else "🟢"
            message += f"\n{icon} *{section['title']}*\n"
            message += self._render_plain_block(section["body"])

        # Подвал: состав отчёта + время формирования.
        message += divider + "\n"
        try:
            from lib.report_settings import (
                REPORT_CAPABLE_EXTENSIONS,
                get_report_extension_label,
            )

            included_labels = [
                get_report_extension_label(ext_id)
                for ext_id in REPORT_CAPABLE_EXTENSIONS
                if ext_id in report_extensions
            ]
            composition = ", ".join(included_labels) if included_labels else "только мониторинг"
            message += f"🧩 _Состав: {composition}_\n"
        except Exception:
            pass
        message += f"⏰ _Сформирован: {collection_time.strftime('%H:%M:%S')}_"
        return message

    def _render_table(self, headers, rows):
        """Рендерит компактную ASCII-таблицу в markdown code block."""
        normalized_rows = [tuple(str(cell) for cell in row) for row in rows]
        normalized_headers = tuple(str(cell) for cell in headers)
        widths = [len(normalized_headers[i]) for i in range(len(normalized_headers))]

        for row in normalized_rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell))

        def format_row(row_values):
            return " | ".join(row_values[i].ljust(widths[i]) for i in range(len(row_values)))

        separator = "-+-".join("-" * width for width in widths)
        lines = [format_row(normalized_headers), separator]
        lines.extend(format_row(row) for row in normalized_rows)
        return "```\n" + "\n".join(lines) + "\n```\n"

    def _render_key_value_table(self, rows):
        """Рендерит компактную 2-колоночную таблицу без заголовков."""
        normalized_rows = [tuple(str(cell) for cell in row) for row in rows]
        if not normalized_rows:
            return "```\nнет данных\n```\n"

        left_width = max(len(row[0]) for row in normalized_rows)
        lines = [f"{key.ljust(left_width)} | {value}" for key, value in normalized_rows]
        return "```\n" + "\n".join(lines) + "\n```\n"

    def _render_plain_block(self, text):
        """Приводит markdown-списки к компактному блоку фиксированной ширины."""
        lines = []
        for raw_line in str(text).splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("• "):
                line = line[2:]
            if line.startswith("- "):
                line = line[2:]
            lines.append(line)
        if not lines:
            return "```\nнет данных\n```\n"
        return "```\n" + "\n".join(lines) + "\n```\n"

    def force_report(self):
        """Формирует отчет для ручного запроса и возвращает текст"""
        data_collected = self.collect_morning_data(manual_call=True)
        if not data_collected:
            return "❌ Ошибка сбора данных для отчета"

        return self.generate_report_message()

    def get_backup_summary_for_report(
        self,
        period_hours=16,
        include_proxmox=True,
        include_databases=True,
        include_mail=False,
        unavailable_hosts=None,
    ):
        """Получает сводку по бэкапам"""
        try:
            # Импорт функций бэкапов
            from extensions.backup_monitor.backup_utils import get_backup_summary

            return get_backup_summary(
                period_hours,
                include_proxmox=include_proxmox,
                include_databases=include_databases,
                include_mail=include_mail,
                unavailable_hosts=unavailable_hosts,
            )
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки по бэкапам: {e}")
            return "❌ Данные о бэкапах недоступны", True

    def get_zfs_summary_for_report(self, include_free_space=True, include_snapshots=True):
        """Получает сводку по ZFS (пулы; опционально место и снэпшоты)."""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from core.config_manager import config_manager as settings_manager

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return "❌ База бэкапов не настроена\n", True

            zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
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
                    return "❌ Таблица ZFS ещё не создана.\n", True
                raise
            finally:
                conn.close()

            if allowed_servers:
                rows = [row for row in rows if row[0] in allowed_servers]
            else:
                rows = []

            expected_servers = set(allowed_servers)
            if not expected_servers:
                expected_servers = {row[0] for row in rows}

            def parse_received_at(value):
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8")
                    except Exception:
                        return None
                if isinstance(value, (int, float)):
                    try:
                        return datetime.fromtimestamp(value)
                    except (ValueError, OSError):
                        return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    normalized = value.strip()
                    if normalized.endswith("Z"):
                        normalized = f"{normalized[:-1]}+00:00"
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                        try:
                            return datetime.strptime(normalized, fmt)
                        except ValueError:
                            continue
                    if len(normalized) >= 19:
                        try:
                            return datetime.strptime(normalized[:19], "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            pass
                    try:
                        return datetime.fromisoformat(normalized)
                    except ValueError:
                        return None
                return None

            latest_by_server = {}
            for server_name, _, _, received_at in rows:
                parsed_time = parse_received_at(received_at)
                if server_name not in latest_by_server:
                    latest_by_server[server_name] = parsed_time
                    continue
                current_latest = latest_by_server.get(server_name)
                if not current_latest or (parsed_time and parsed_time > current_latest):
                    latest_by_server[server_name] = parsed_time

            stale_servers = set()
            stale_threshold = datetime.now() - timedelta(hours=24)

            def parse_received_at(value):
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                    try:
                        return datetime.fromisoformat(value)
                    except ValueError:
                        return None
                return None

            for server in expected_servers:
                received_at = latest_by_server.get(server)
                if not received_at:
                    stale_servers.add(server)
                    continue
                if received_at.tzinfo is not None:
                    received_at = received_at.astimezone(timezone.utc).replace(tzinfo=None)
                if received_at < stale_threshold:
                    stale_servers.add(server)

            if not rows and expected_servers:
                servers_total = len(expected_servers)
                servers_problem = len(stale_servers)
                servers_ok = servers_total - servers_problem
                summary = (
                    f"• Серверов: {servers_total} (🟢 {servers_ok} / 🔴 {servers_problem})\n"
                    "• Пулов: 0 (🟢 0 / 🔴 0)\n"
                )
                return summary, True
            if not rows:
                return "• Данных нет\n", False

            total_pools = len(rows)
            ok_pools = sum(
                1
                for server_name, _, pool_state, _ in rows
                if server_name not in stale_servers and str(pool_state).upper() == "ONLINE"
            )
            bad_pools = sum(
                1
                for server_name, _, pool_state, _ in rows
                if server_name not in stale_servers and str(pool_state).upper() != "ONLINE"
            )
            servers_count = (
                len(expected_servers) if expected_servers else len({row[0] for row in rows})
            )
            server_problem_flags = {server: False for server in expected_servers}
            for server_name, _, pool_state, _ in rows:
                if server_name in stale_servers:
                    continue
                if str(pool_state).upper() != "ONLINE":
                    server_problem_flags[server_name] = True

            servers_problem = len(
                {
                    server
                    for server in expected_servers
                    if server in stale_servers or server_problem_flags.get(server)
                }
            )
            servers_ok = servers_count - servers_problem

            summary = (
                f"• Серверов: {servers_count} (🟢 {servers_ok} / 🔴 {servers_problem})\n"
                f"• Пулов: {total_pools} (🟢 {ok_pools} / 🔴 {bad_pools})\n"
            )
            has_issues = servers_problem > 0 or bad_pools > 0 or bool(stale_servers)

            if include_free_space:
                free_space_summary, free_space_has_issues = self._get_zfs_free_space_summary(
                    db_path, allowed_servers
                )
                summary += f"• Свободное место ZFS пулов: {free_space_summary}\n"
                has_issues = has_issues or free_space_has_issues

            if include_snapshots:
                snapshot_summary, snapshot_has_issues = self._get_snapshot_transfer_summary(
                    db_path, allowed_servers
                )
                summary += f"• Передачи снэпшотов: {snapshot_summary}\n"
                has_issues = has_issues or snapshot_has_issues

            return summary, has_issues
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки ZFS: {e}")
            return "❌ Данные ZFS недоступны\n", True

    def _get_zfs_free_space_summary(self, db_path, allowed_servers):
        """Сводка по свободному месту ZFS-пулов.

        Данные по свободному месту нигде не персистятся в БД — расширение
        `zfs_pool_free_space_monitor` собирает их «вживую» по SSH. Поэтому
        для отчёта мы тоже опрашиваем пулы напрямую (это «тяжёлое»
        расширение, включается осознанно).
        """
        try:
            from extensions.zfs_pool_free_space import collect_zfs_pool_free_space

            results, errors = collect_zfs_pool_free_space()
        except Exception as exc:
            debug_log(f"⚠️ Ошибка сбора свободного места ZFS: {exc}")
            return "ошибка сбора", True

        if not results:
            if errors:
                return "нет данных (ошибки опроса)", True
            return "нет данных", False

        total = len(results)
        alert_count = sum(1 for row in results if row.get("is_alert"))
        ok_count = total - alert_count
        has_issues = alert_count > 0 or bool(errors)
        return f"{total} (🟢 {ok_count} / 🔴 {alert_count})", has_issues

    def _get_snapshot_transfer_summary(self, db_path, allowed_servers):
        """Сводка по передачам снэпшотов за 24 часа."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT host_name, status
                FROM snapshot_transfers
                WHERE received_at >= datetime('now', '-24 hours')
                ORDER BY received_at DESC
                """
            )
            rows = cursor.fetchall()
        except Exception as exc:
            if "no such table: snapshot_transfers" in str(exc):
                return "нет данных", False
            return "ошибка чтения", True
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if allowed_servers:
            rows = [row for row in rows if row[0] in allowed_servers]

        if not rows:
            return "за 24ч: 0", False

        total = len(rows)
        ok_statuses = {"SUCCESS", "SKIPPED"}
        ok_count = sum(1 for _, status in rows if str(status).upper() in ok_statuses)
        bad_count = total - ok_count
        return f"за 24ч: {total} (🟢 {ok_count} / 🔴 {bad_count})", bad_count > 0

    def _zfs_db_and_allowed(self):
        """Возвращает (db_path, allowed_servers) для ZFS-сводок."""
        from config.db_settings import BACKUP_DATABASE_CONFIG
        from core.config_manager import config_manager as settings_manager

        db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
        zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}
        allowed_servers = {
            name
            for name, server_value in zfs_servers.items()
            if not isinstance(server_value, dict) or server_value.get("enabled", True)
        }
        return db_path, allowed_servers

    def get_zfs_free_space_for_report(self):
        """Отдельная сводка по свободному месту ZFS-пулов.

        Свободное место собирается «вживую» по SSH (см.
        `_get_zfs_free_space_summary`), поэтому база бэкапов здесь не нужна.
        """
        summary, has_issues = self._get_zfs_free_space_summary(None, None)
        return f"• Пулов: {summary}", has_issues

    def get_snapshot_transfer_for_report(self):
        """Отдельная сводка по передачам ZFS-снэпшотов."""
        db_path, allowed_servers = self._zfs_db_and_allowed()
        if not db_path:
            return "❌ База бэкапов не настроена", True
        summary, has_issues = self._get_snapshot_transfer_summary(db_path, allowed_servers)
        return f"• Передачи: {summary}", has_issues

    def get_nas_transfer_summary_for_report(self, period_hours=24):
        """Сводка по передачам бэкапов на NAS за период."""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from extensions.backup_monitor.backup_utils import filter_nas_transfer_row

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return "❌ База бэкапов не настроена", True

            since = (datetime.now() - timedelta(hours=period_hours)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT host_name, status, nas_mounted, started_at_text,
                           completed_at_text, bases_processed, error_count,
                           problem_bases, received_at
                    FROM nas_transfers
                    WHERE received_at >= ?
                    ORDER BY received_at DESC
                    """,
                    (since,),
                )
                rows = [filter_nas_transfer_row(tuple(r)) for r in cursor.fetchall()]
            except Exception as exc:
                if "no such table: nas_transfers" in str(exc):
                    return "• Данных нет", False
                raise
            finally:
                conn.close()

            if not rows:
                return "• За период передач не было", False

            total = len(rows)
            ok_count = sum(1 for r in rows if str(r[1]).upper() == "OK")
            bad_count = total - ok_count
            return f"• Передач: {total} (🟢 {ok_count} / 🔴 {bad_count})", bad_count > 0
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки NAS: {exc}")
            return "❌ Данные о передачах на NAS недоступны", True

    def get_config_console_summary_for_report(self, period_hours=168):
        """Сводка по бэкапам конфигов/историй консолей."""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from extensions.backup_monitor.backup_utils import (
                get_config_console_servers,
                group_config_console_rows,
            )

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return "❌ База бэкапов не настроена", True

            since = (datetime.now() - timedelta(hours=period_hours)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT host_name, status, delivery_method, receiver,
                           started_at_text, completed_at_text, vm_config_count,
                           lxc_config_count, history_container_count,
                           history_file_count, error_count, problem_items, received_at
                    FROM config_console_backups
                    WHERE received_at >= ?
                    ORDER BY received_at DESC
                    """,
                    (since,),
                )
                rows = cursor.fetchall()
            except Exception as exc:
                if "no such table: config_console_backups" in str(exc):
                    return "• Данных нет", False
                raise
            finally:
                conn.close()

            expected = get_config_console_servers()
            grouped = group_config_console_rows(rows, expected_servers=expected)
            servers = grouped.get("servers", [])
            if not servers:
                return "• Данных нет", False

            total = len(servers)
            missing = len(grouped.get("missing", []))
            problem = 0
            for srv in servers:
                latest = srv.get("latest")
                if srv.get("missing") or latest is None:
                    continue
                if str(latest[1]).upper() != "OK":
                    problem += 1
            bad = problem + missing
            ok_count = total - bad
            final_mark = "🟢" if grouped.get("final") else "⚪"
            return (
                f"• Серверов: {total} (🟢 {ok_count} / 🔴 {bad})\n"
                f"• Финальная передача на NAS: {final_mark}",
                bad > 0,
            )
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки конфигов: {exc}")
            return "❌ Данные о бэкапах конфигов недоступны", True

    def get_supplier_stock_summary_for_report(self, period_days=7):
        """Сводка по получению остатков поставщиков."""
        try:
            from extensions.supplier_stock_files import summarize_supplier_stock_reports

            grouped = summarize_supplier_stock_reports(period_days=period_days)
            total = 0
            ok_count = 0
            bad_count = 0
            for kind in ("download", "mail"):
                for src in grouped.get(kind, []) or []:
                    total += 1
                    status = (src.get("receive") or {}).get("status", "unknown")
                    if status == "success":
                        ok_count += 1
                    else:
                        bad_count += 1
            if total == 0:
                return "• Источников нет", False
            return f"• Источников: {total} (🟢 {ok_count} / 🔴 {bad_count})", bad_count > 0
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки остатков поставщиков: {exc}")
            return "❌ Данные об остатках поставщиков недоступны", True

    def get_tls_cert_summary_for_report(self):
        """Сводка по TLS-сертификатам (live-проверка)."""
        try:
            from extensions.tls_cert_monitor import collect_certificates

            results, errors = collect_certificates()
            total = len(results)
            if total == 0 and not errors:
                return "• Сертификаты не настроены", False
            alert_count = sum(
                1 for r in results if r.get("is_alert") or not r.get("ok", True)
            )
            ok_count = total - alert_count
            min_days = None
            for r in results:
                days = r.get("days_left")
                if isinstance(days, int) and (min_days is None or days < min_days):
                    min_days = days
            summary = f"• Сертификатов: {total} (🟢 {ok_count} / 🔴 {alert_count})"
            if min_days is not None:
                summary += f"\n• Ближайшее истечение: {min_days} дн."
            has_issues = bool(errors) or alert_count > 0
            return summary, has_issues
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки TLS: {exc}")
            return "❌ Данные о TLS-сертификатах недоступны", True

    def get_resources_summary_for_report(self):
        """Сводка по ресурсам серверов (live-проверка CPU/RAM/Disk)."""
        try:
            from core.task_router import run_resources_task

            ok, payload = run_resources_task(force_reload=True)
            if not ok or not isinstance(payload, dict):
                return "❌ Данные о ресурсах недоступны", True
            stats = payload.get("stats", {}) or {}
            total = int(stats.get("total", 0) or 0)
            success = int(stats.get("success", 0) or 0)
            failed = int(stats.get("failed", 0) or 0)
            if total == 0:
                return "• Серверов с проверкой ресурсов нет", False
            return f"• Серверов: {total} (🟢 {success} / 🔴 {failed})", failed > 0
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки ресурсов: {exc}")
            return "❌ Данные о ресурсах недоступны", True

    def _parse_collection_times(self, raw_value):
        """Парсит одно или несколько значений времени в список time."""
        if raw_value is None:
            return []

        values = []
        if isinstance(raw_value, (list, tuple, set)):
            values = [str(item).strip() for item in raw_value]
        else:
            normalized = str(raw_value).replace(";", ",")
            values = [item.strip() for item in normalized.split(",") if item.strip()]

        parsed = []
        for value in values:
            try:
                parts = value.split(":")
                if len(parts) < 2:
                    continue
                hours = int(parts[0])
                minutes = int(parts[1])
                parsed.append(datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M").time())
            except Exception:
                continue
        return sorted(parsed, key=lambda t: (t.hour, t.minute))

    def _get_collection_times(self):
        """Возвращает актуальные времена автосбора из настроек."""
        default_time = None
        configured_source = "config.settings.DATA_COLLECTION_TIME"
        try:
            from config.db_settings import DATA_COLLECTION_TIME as runtime_default

            default_time = runtime_default
        except Exception:
            pass

        try:
            from core.config_manager import config_manager as settings_manager

            raw_value = settings_manager.get_setting("DATA_COLLECTION_TIMES", None, use_cache=False)
            if raw_value not in (None, ""):
                configured_source = "БД settings: DATA_COLLECTION_TIMES"
            if raw_value in (None, ""):
                raw_value = settings_manager.get_setting(
                    "DATA_COLLECTION_TIME", default_time, use_cache=False
                )
                if raw_value not in (None, ""):
                    configured_source = "БД settings: DATA_COLLECTION_TIME"
        except Exception:
            raw_value = default_time

        parsed = self._parse_collection_times(raw_value)
        resolved_slots = ",".join(slot.strftime("%H:%M") for slot in parsed) if parsed else ""
        info_log(
            "[MORNING_REPORT_SCHEDULE] resolve_collection_times "
            f"source='{configured_source}' raw='{raw_value}' resolved='{resolved_slots}'"
        )
        if parsed:
            return parsed
        if hasattr(raw_value, "hour") and hasattr(raw_value, "minute"):
            return [raw_value]

        try:
            from config.settings import DATA_COLLECTION_TIME as static_default

            return [static_default]
        except Exception:
            return [datetime.now().time().replace(second=0, microsecond=0)]

    def send_report(self, manual_call=False, collect_before_send=True):
        """Отправка отчета"""
        try:
            # По умолчанию собираем данные перед отправкой, но при автозапуске
            # можно переиспользовать уже собранный слепок, чтобы не запускать
            # повторный сбор и не блокировать отправку отчета.
            if collect_before_send:
                collected = self.collect_morning_data(manual_call)
                if not collected:
                    return False

            # Генерируем сообщение
            message = self.generate_report_message()

            # Отправляем через унифицированный канал алертов. Для отчёта
            # просим повесить под Matrix-сообщением кнопку-эмодзи «открыть
            # меню» — пользователю удобно открыть !menu прямо из отчёта.
            from lib.alerts import send_alert

            sent_ok = send_alert(message, force=True, attach_menu_button=True)

            if sent_ok:
                debug_log(f"✅ Отчет отправлен ({'ручной' if manual_call else 'автоматический'})")
            else:
                debug_log(
                    f"❌ Отчет не доставлен ({'ручной' if manual_call else 'автоматический'}): "
                    "канал отправки вернул sent=False"
                )
            return sent_ok
        except Exception as e:
            debug_log(f"❌ Ошибка отправки отчета: {e}")
            return False

    def start_scheduler(self):
        """Запуск планировщика отчетов"""
        debug_log("⏰ Запуск планировщика утренних отчетов")

        while True:
            current_time = datetime.now()
            current_time_time = current_time.time()

            # Проверяем все актуальные времена сбора данных
            collection_times = self._get_collection_times()
            today = current_time.date()

            for collection_time in collection_times:
                if (
                    current_time_time.hour == collection_time.hour
                    and current_time_time.minute == collection_time.minute
                ):

                    # Проверяем, что сегодня еще не отправляли отчет
                    if self.last_report_date != today:
                        debug_log(
                            f"📊 Автоматический сбор данных для утреннего отчета ({collection_time.strftime('%H:%M')})"
                        )
                        self.send_report(manual_call=False)
                        self.last_report_date = today

                        # Задержка чтобы не запускать повторно в ту же минуту
                        time.sleep(65)
                    else:
                        debug_log(f"⏭️ Отчет уже отправлен сегодня {self.last_report_date}")
                    break

            time.sleep(60)  # Проверяем каждую минуту


# Глобальный экземпляр отчета
morning_report = MorningReport()
