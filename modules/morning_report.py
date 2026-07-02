"""
/app/modules/morning_report.py
Server Monitoring System v8.63.36
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning Report Module
Система мониторинга серверов
Версия: 8.63.36
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль утреннего отчета
"""

import html
import sqlite3
import time
from datetime import datetime, timedelta, timezone

from lib.logging import debug_log, info_log

REPORT_DIVIDER = "━━━━━━━━━━━━━━━━━━"


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

    # ------------------------------------------------------------------
    # Форматирование «ok/total (percent%)»
    # ------------------------------------------------------------------

    @staticmethod
    def _ratio(ok, total):
        """Форматирует соотношение вида «15/15 (100%)»."""
        if total <= 0:
            return f"{ok}/{total} (—)"
        percent = ok * 100.0 / total
        if float(percent).is_integer():
            percent_text = f"{percent:.0f}%"
        else:
            percent_text = f"{percent:.1f}%"
        return f"{ok}/{total} ({percent_text})"

    @classmethod
    def _status_line(cls, label, ok, total):
        """Строка секции вида «🟢 Серверы: 49/49 (100%)»."""
        if total <= 0:
            return f"⚪ {label}: нет данных"
        icon = "🟢" if ok >= total else "🔴"
        return f"{icon} {label}: {cls._ratio(ok, total)}"

    # ------------------------------------------------------------------
    # Сборка структуры отчёта
    # ------------------------------------------------------------------

    def build_report(self):
        """Собирает структуру отчёта: метаданные и список секций.

        Каждая секция: {"title", "lines": [str], "has_issues": bool}.
        Секции без проблем в Telegram/Matrix сворачиваются (виден только
        заголовок с флагом состояния), проблемные — раскрыты.
        """
        if not self.morning_data or "status" not in self.morning_data:
            return None

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

        try:
            from config.settings import APP_VERSION
        except Exception:
            APP_VERSION = None

        from extensions.extension_manager import extension_manager

        def _selected(ext_id):
            return ext_id in report_extensions and extension_manager.is_extension_enabled(
                ext_id
            )

        period_label = "за 24ч" if is_manual else "за 16ч"
        period_hours = 24 if is_manual else 16

        sections = []

        def add_section(title, result):
            lines, has_issues = result
            sections.append(
                {"title": title, "lines": list(lines), "has_issues": bool(has_issues)}
            )

        # Доступность серверов — всегда первая секция.
        add_section("🖥 Доступность серверов", self._availability_section(status))

        unavailable_hosts = set()
        for server in status.get("failed", []):
            if server.get("name"):
                unavailable_hosts.add(server.get("name"))
            if server.get("ip"):
                unavailable_hosts.add(server.get("ip"))

        # Бэкапы — отдельные секции по расширениям.
        if _selected("backup_monitor"):
            add_section(
                f"💾 Бэкапы Proxmox ({period_label})",
                self.get_proxmox_summary_for_report(period_hours, unavailable_hosts),
            )

        if _selected("database_backup_monitor"):
            add_section(
                f"🗃️ Бэкапы БД ({period_label})",
                self.get_database_summary_for_report(period_hours),
            )

        if _selected("mail_backup_monitor"):
            add_section(
                f"📬 Бэкапы почты ({period_label})",
                self.get_mail_summary_for_report(period_hours),
            )

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
            add_section(
                f"📦 Загрузка остатков 1С ({period_label})",
                self.get_stock_load_summary_for_report(period_hours),
            )

        if _selected("supplier_stock_files"):
            add_section(
                "🏷️ Остатки поставщиков",
                self.get_supplier_stock_summary_for_report(),
            )

        if _selected("zfs_monitor"):
            add_section("🧊 Статусы ZFS", self.get_zfs_summary_for_report())

        if _selected("zfs_pool_free_space_monitor"):
            add_section("💽 Свободное место ZFS", self.get_zfs_free_space_for_report())

        if _selected("snapshot_transfer_monitor"):
            add_section(
                "📸 Передачи снэпшотов (за 24ч)", self.get_snapshot_transfer_for_report()
            )

        if _selected("tls_cert_monitor"):
            add_section("🔐 TLS-сертификаты", self.get_tls_cert_summary_for_report())

        if _selected("resource_monitor"):
            add_section("💻 Ресурсы серверов", self.get_resources_summary_for_report())

        composition = None
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
        except Exception:
            pass

        return {
            "report_type": "Ручной отчёт" if is_manual else "Утренний отчёт",
            "app_version": APP_VERSION,
            "collection_time": collection_time,
            "sections": sections,
            "problem_areas": [s["title"] for s in sections if s["has_issues"]],
            "composition": composition,
        }

    def _availability_section(self, status):
        """Секция доступности серверов одной строкой «Серверы: 49/49 (100%)»."""
        up_count = len(status.get("ok", []))
        failed = status.get("failed", [])
        down_count = len(failed)
        total = up_count + down_count

        lines = [self._status_line("Серверы", up_count, total)]
        if down_count > 0:
            lines.append(f"Недоступны ({down_count}):")
            by_type = {}
            for server in failed:
                by_type.setdefault(str(server.get("type", "")), []).append(server)
            for server_type, servers_list in sorted(by_type.items()):
                for s in servers_list:
                    name = str(s.get("name", ""))
                    ip = str(s.get("ip", ""))
                    lines.append(f"• {server_type.upper()} {name} ({ip})")
        return lines, down_count > 0

    # ------------------------------------------------------------------
    # Рендеры: plain (Android/фолбэк), Telegram HTML, Matrix HTML
    # ------------------------------------------------------------------

    def _report_meta_line(self, report):
        parts = []
        if report.get("app_version"):
            parts.append(f"v{report['app_version']}")
        collection_time = report.get("collection_time", datetime.now())
        parts.append(collection_time.strftime("%d.%m.%Y"))
        parts.append(collection_time.strftime("%H:%M"))
        return " • ".join(parts)

    def render_plain(self, report):
        """Плоский текст без разметки: Android-клиент и фолбэк каналов."""
        if not report:
            return "❌ Нет данных для отчета"

        problem_areas = report["problem_areas"]
        report_icon = "🔴" if problem_areas else "🟢"
        lines = [
            f"{report_icon} {report['report_type']} мониторинга",
            self._report_meta_line(report),
            REPORT_DIVIDER,
        ]

        if problem_areas:
            lines.append(f"⚠️ Требует внимания ({len(problem_areas)}):")
            lines.extend(f"• {area}" for area in problem_areas)
        else:
            lines.append("✅ Всё в норме — критичных проблем не обнаружено")

        for section in report["sections"]:
            icon = "🔴" if section["has_issues"] else "🟢"
            lines.append("")
            lines.append(f"{icon} {section['title']}")
            lines.extend(section["lines"])

        lines.append(REPORT_DIVIDER)
        if report.get("composition"):
            lines.append(f"🧩 Состав: {report['composition']}")
        collection_time = report.get("collection_time", datetime.now())
        lines.append(f"⏰ Сформирован: {collection_time.strftime('%H:%M:%S')}")
        return "\n".join(lines)

    def render_telegram_html(self, report):
        """HTML для Telegram: все секции свёрнуты в expandable blockquote —
        виден только заголовок с флагом состояния, подробности скрыты до
        разворота. Список проблемных секций виден сразу в блоке «Требует
        внимания» наверху сообщения."""
        if not report:
            return None

        def esc(text):
            return html.escape(str(text), quote=False)

        problem_areas = report["problem_areas"]
        report_icon = "🔴" if problem_areas else "🟢"
        lines = [
            f"{report_icon} <b>{esc(report['report_type'])} мониторинга</b>",
            f"<i>{esc(self._report_meta_line(report))}</i>",
            REPORT_DIVIDER,
        ]

        if problem_areas:
            lines.append(f"⚠️ <b>Требует внимания ({len(problem_areas)}):</b>")
            lines.extend(f"• {esc(area)}" for area in problem_areas)
        else:
            lines.append("✅ <b>Всё в норме</b> — критичных проблем не обнаружено")

        for section in report["sections"]:
            icon = "🔴" if section["has_issues"] else "🟢"
            lines.append("")
            lines.append(f"{icon} <b>{esc(section['title'])}</b>")
            body = "\n".join(esc(line) for line in section["lines"])
            if not body:
                continue
            lines.append(f"<blockquote expandable>{body}</blockquote>")

        lines.append(REPORT_DIVIDER)
        if report.get("composition"):
            lines.append(f"🧩 <i>Состав: {esc(report['composition'])}</i>")
        collection_time = report.get("collection_time", datetime.now())
        lines.append(f"⏰ <i>Сформирован: {collection_time.strftime('%H:%M:%S')}</i>")
        return "\n".join(lines)

    def render_matrix_html(self, report):
        """HTML для Matrix: все секции свёрнуты в <details> — виден только
        заголовок с флагом состояния, подробности скрыты до разворота.
        Список проблемных секций виден сразу в блоке «Требует внимания»."""
        if not report:
            return None

        def esc(text):
            return html.escape(str(text), quote=False)

        problem_areas = report["problem_areas"]
        report_icon = "🔴" if problem_areas else "🟢"
        parts = [
            f"<p>{report_icon} <strong>{esc(report['report_type'])} мониторинга</strong>"
            f"<br/><em>{esc(self._report_meta_line(report))}</em></p>"
        ]

        if problem_areas:
            problem_lines = "<br/>".join(f"• {esc(area)}" for area in problem_areas)
            parts.append(
                f"<p>⚠️ <strong>Требует внимания ({len(problem_areas)}):</strong>"
                f"<br/>{problem_lines}</p>"
            )
        else:
            parts.append("<p>✅ <strong>Всё в норме</strong> — критичных проблем не обнаружено</p>")

        for section in report["sections"]:
            icon = "🔴" if section["has_issues"] else "🟢"
            title = f"{icon} <strong>{esc(section['title'])}</strong>"
            body = "<br/>".join(esc(line) for line in section["lines"])
            parts.append(f"<details><summary>{title}</summary><p>{body}</p></details>")

        footer = []
        if report.get("composition"):
            footer.append(f"🧩 <em>Состав: {esc(report['composition'])}</em>")
        collection_time = report.get("collection_time", datetime.now())
        footer.append(f"⏰ <em>Сформирован: {collection_time.strftime('%H:%M:%S')}</em>")
        parts.append("<p>" + "<br/>".join(footer) + "</p>")
        return "".join(parts)

    def generate_report_message(self):
        """Генерация текстового сообщения отчета (плоский формат)."""
        return self.render_plain(self.build_report())

    def force_report(self):
        """Формирует отчет для ручного запроса и возвращает текст"""
        data_collected = self.collect_morning_data(manual_call=True)
        if not data_collected:
            return "❌ Ошибка сбора данных для отчета"

        return self.generate_report_message()

    def force_report_formats(self):
        """Формирует ручной отчёт во всех форматах каналов доставки.

        Возвращает dict {"plain", "telegram_html", "matrix_html", "payload"};
        HTML-варианты и структурированный payload — None при ошибке сбора
        данных.
        """
        data_collected = self.collect_morning_data(manual_call=True)
        if not data_collected:
            return {
                "plain": "❌ Ошибка сбора данных для отчета",
                "telegram_html": None,
                "matrix_html": None,
                "payload": None,
            }
        report = self.build_report()
        return {
            "plain": self.render_plain(report),
            "telegram_html": self.render_telegram_html(report),
            "matrix_html": self.render_matrix_html(report),
            "payload": self._report_to_json_payload(report),
        }

    def _report_to_json_payload(self, report):
        """JSON-сериализуемое представление отчёта для мобильного API.

        Тот же список секций (title/has_issues/lines), из которого
        render_telegram_html/render_matrix_html строят сворачиваемые
        blockquote/details — Android рендерит по нему такие же
        сворачиваемые карточки на клиенте, без парсинга плоского текста.
        """
        if not report:
            return None
        collection_time = report.get("collection_time") or datetime.now()
        return {
            "report_type": report.get("report_type"),
            "app_version": report.get("app_version"),
            "generated_at": collection_time.isoformat(),
            "has_issues": bool(report["problem_areas"]),
            "problem_areas": list(report["problem_areas"]),
            "composition": report.get("composition"),
            "sections": [
                {
                    "title": section["title"],
                    "has_issues": bool(section["has_issues"]),
                    "lines": list(section["lines"]),
                }
                for section in report["sections"]
            ],
        }

    # ------------------------------------------------------------------
    # Секции расширений: каждая возвращает (lines, has_issues)
    # ------------------------------------------------------------------

    def get_proxmox_summary_for_report(self, period_hours=24, unavailable_hosts=None):
        """Секция бэкапов Proxmox: «Хостов: 15/15 (100%)» + детали проблем."""
        try:
            from extensions.backup_monitor.backup_utils import get_proxmox_backup_stats

            stats = get_proxmox_backup_stats(
                period_hours, unavailable_hosts=unavailable_hosts
            )
            if stats.get("error"):
                return [f"❌ {stats['error']}"], True
            if stats.get("no_data"):
                return ["⚪ Нет данных"], False

            lines = [self._status_line("Хостов", stats["ok"], stats["total"])]
            if stats["stale"]:
                lines.append(f"• Без бэкапов >24ч: {', '.join(stats['stale'])}")
            if stats["unavailable"]:
                lines.append(f"• Хосты недоступны: {', '.join(stats['unavailable'])}")
            has_issues = (
                stats["ok"] < stats["total"]
                or bool(stats["stale"])
                or bool(stats["unavailable"])
            )
            return lines, has_issues
        except Exception as exc:
            debug_log(f"❌ Ошибка секции бэкапов Proxmox: {exc}")
            return ["❌ Данные о бэкапах Proxmox недоступны"], True

    def get_database_summary_for_report(self, period_hours=24):
        """Секция бэкапов БД: строки по категориям в формате N/N (%)."""
        try:
            from extensions.backup_monitor.backup_utils import get_database_backup_stats

            stats = get_database_backup_stats(period_hours)
            if stats.get("error"):
                return [f"❌ {stats['error']}"], True
            if stats.get("no_data"):
                return ["⚪ Нет данных"], False

            lines = []
            has_issues = False
            problem_lines = []
            for category in stats["categories"]:
                lines.append(
                    self._status_line(category["name"], category["ok"], category["total"])
                )
                if category["ok"] < category["total"]:
                    has_issues = True
                if category["missing"]:
                    has_issues = True
                    problem_lines.append(
                        f"• Нет бэкапов за {period_hours}ч — "
                        f"{category['name']}: {', '.join(category['missing'])}"
                    )
                if category["stale"]:
                    has_issues = True
                    problem_lines.append(
                        f"• Без бэкапов >24ч — "
                        f"{category['name']}: {', '.join(category['stale'])}"
                    )
            lines.extend(problem_lines)
            return lines, has_issues
        except Exception as exc:
            debug_log(f"❌ Ошибка секции бэкапов БД: {exc}")
            return ["❌ Данные о бэкапах БД недоступны"], True

    def get_mail_summary_for_report(self, period_hours=24):
        """Секция бэкапа почты: последний бэкап и его свежесть."""
        try:
            from extensions.backup_monitor.backup_utils import get_mail_backup_stats

            stats = get_mail_backup_stats(period_hours)
            if stats.get("error"):
                return [f"❌ {stats['error']}"], True
            latest = stats.get("latest")
            if stats.get("no_data") or not latest:
                return ["⚪ Нет данных"], False

            hours_ago = latest.get("hours_ago")
            if hours_ago is None:
                ago_text = "время неизвестно"
            elif hours_ago >= 24:
                ago_text = f"{hours_ago // 24}д {hours_ago % 24}ч назад"
            else:
                ago_text = f"{hours_ago}ч назад"

            if stats.get("fresh"):
                return [f"🟢 {latest['size']} {latest['path']} ({ago_text})"], False
            return (
                [
                    f"🔴 Нет свежих бэкапов (>{period_hours}ч), "
                    f"последний: {latest['size']} {latest['path']} ({ago_text})"
                ],
                True,
            )
        except Exception as exc:
            debug_log(f"❌ Ошибка секции бэкапов почты: {exc}")
            return ["❌ Данные о бэкапах почты недоступны"], True

    def get_stock_load_summary_for_report(self, period_hours=24):
        """Секция загрузки остатков 1С: «Файлов: 44/44 (100%)».

        Ожидаемое число файлов задаётся настройкой STOCK_LOAD_EXPECTED_FILES
        (0 — не задано, тогда сверка идёт по фактическому количеству).
        """
        try:
            from extensions.backup_monitor.backup_utils import get_stock_load_stats

            stats = get_stock_load_stats(period_hours)
            if stats.get("error"):
                return [f"❌ {stats['error']}"], True

            expected = stats.get("expected", 0)
            if stats.get("no_data"):
                if expected > 0:
                    return (
                        [self._status_line("Файлов", 0, expected)],
                        True,
                    )
                return ["⚪ Нет свежих данных о загрузке остатков"], False

            total = stats["total"]
            success = stats["success"]
            target = expected if expected > 0 else total
            lines = [self._status_line("Файлов", success, target)]
            if expected > 0 and total != expected:
                lines.append(f"• Получено файлов: {total} (ожидалось {expected})")
            if stats["warning"]:
                lines.append(f"• С предупреждениями: {stats['warning']}")
            if stats["failed"]:
                lines.append(f"• Неудачно: {stats['failed']}")
            if stats["unknown"]:
                lines.append(f"• Без статуса: {stats['unknown']}")
            has_issues = (
                success < target or bool(stats["warning"]) or bool(stats["failed"])
            )
            return lines, has_issues
        except Exception as exc:
            debug_log(f"❌ Ошибка секции загрузки остатков: {exc}")
            return ["❌ Данные о загрузке остатков недоступны"], True

    def get_zfs_summary_for_report(self):
        """Секция статусов ZFS: серверы и пулы в формате N/N (%)."""
        try:
            db_path, allowed_servers = self._zfs_db_and_allowed()
            if not db_path:
                return ["❌ База бэкапов не настроена"], True

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
                    return ["❌ Таблица ZFS ещё не создана"], True
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
            for server in expected_servers:
                received_at = latest_by_server.get(server)
                if not received_at:
                    stale_servers.add(server)
                    continue
                if received_at.tzinfo is not None:
                    received_at = received_at.astimezone(timezone.utc).replace(tzinfo=None)
                if received_at < stale_threshold:
                    stale_servers.add(server)

            if not rows and not expected_servers:
                return ["⚪ Данных нет"], False

            total_pools = len(rows)
            ok_pools = sum(
                1
                for server_name, _, pool_state, _ in rows
                if server_name not in stale_servers and str(pool_state).upper() == "ONLINE"
            )
            servers_count = len(expected_servers)
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

            lines = [
                self._status_line("Серверов", servers_ok, servers_count),
                self._status_line("Пулов", ok_pools, total_pools),
            ]
            if stale_servers:
                lines.append(f"• Нет свежих данных: {', '.join(sorted(stale_servers))}")
            has_issues = servers_problem > 0 or ok_pools < total_pools
            return lines, has_issues
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки ZFS: {e}")
            return ["❌ Данные ZFS недоступны"], True

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
        """Секция свободного места ZFS-пулов с процентами по каждому пулу.

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
            return ["❌ Ошибка сбора данных"], True

        if not results:
            if errors:
                return ["❌ Нет данных (ошибки опроса)"], True
            return ["⚪ Нет данных"], False

        total = len(results)
        alert_count = sum(1 for row in results if row.get("is_alert"))
        ok_count = total - alert_count
        lines = [self._status_line("Пулов", ok_count, total)]
        for row in results:
            icon = "🔴" if row.get("is_alert") else "🟢"
            lines.append(
                f"{icon} {row['host_name']} {row['pool']}: свободно {row['free_percent']}%"
            )
        if errors:
            lines.append(f"• Ошибки опроса: {len(errors)}")
        has_issues = alert_count > 0 or bool(errors)
        return lines, has_issues

    def get_snapshot_transfer_for_report(self):
        """Секция передач ZFS-снэпшотов: общая сводка по всем хостам.

        Хосты берутся из настройки SNAPSHOT_TRANSFER_HOSTS (включённые) плюс
        фактические записи за 24 часа; по каждому хосту оценивается последний
        статус (SUCCESS/SKIPPED — успех), а не сырые записи писем. Подробности
        по конкретному хосту в отчёте не нужны — они доступны в отдельном
        меню «Передачи снэпшотов» (Telegram/Matrix), здесь только агрегат.
        """
        try:
            from core.config_manager import config_manager as settings_manager

            db_path, _ = self._zfs_db_and_allowed()
            if not db_path:
                return ["❌ База бэкапов не настроена"], True

            hosts_cfg = settings_manager.get_setting("SNAPSHOT_TRANSFER_HOSTS", {}) or {}
            if not isinstance(hosts_cfg, dict):
                hosts_cfg = {}
            expected_hosts = {
                str(name).strip()
                for name, cfg in hosts_cfg.items()
                if str(name).strip()
                and (not isinstance(cfg, dict) or cfg.get("enabled", True))
            }

            latest_by_host = {}
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT host_name, status, received_at
                    FROM snapshot_transfers
                    WHERE received_at >= datetime('now', '-24 hours')
                    ORDER BY datetime(received_at) DESC, id DESC
                    """
                )
                for host_name, transfer_status, received_at in cursor.fetchall():
                    host = str(host_name or "").strip()
                    if not host or host in latest_by_host:
                        continue
                    latest_by_host[host] = {
                        "status": str(transfer_status or "").upper().strip(),
                        "received_at": str(received_at or "").strip(),
                    }
            except Exception as exc:
                if "no such table: snapshot_transfers" not in str(exc):
                    return ["❌ Ошибка чтения данных"], True
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

            all_hosts = sorted(expected_hosts | set(latest_by_host), key=str.lower)
            if not all_hosts:
                return ["⚪ Нет данных за 24ч"], False

            ok_statuses = {"SUCCESS", "SKIPPED"}
            ok_count = 0
            for host in all_hosts:
                latest = latest_by_host.get(host)
                if latest is not None and (latest["status"] or "") in ok_statuses:
                    ok_count += 1

            lines = [self._status_line("Хостов", ok_count, len(all_hosts))]
            return lines, ok_count < len(all_hosts)
        except Exception as exc:
            debug_log(f"❌ Ошибка секции передач снэпшотов: {exc}")
            return ["❌ Данные о передачах снэпшотов недоступны"], True

    def get_nas_transfer_summary_for_report(self, period_hours=24):
        """Секция передач бэкапов на NAS: «Передач: 1/1 (100%)»."""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from extensions.backup_monitor.backup_utils import filter_nas_transfer_row

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return ["❌ База бэкапов не настроена"], True

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
                    return ["⚪ Данных нет"], False
                raise
            finally:
                conn.close()

            if not rows:
                return ["⚪ За период передач не было"], False

            total = len(rows)
            ok_count = sum(1 for r in rows if str(r[1]).upper() == "OK")
            return (
                [self._status_line("Передач", ok_count, total)],
                ok_count < total,
            )
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки NAS: {exc}")
            return ["❌ Данные о передачах на NAS недоступны"], True

    def get_config_console_summary_for_report(self, period_hours=168):
        """Секция бэкапов конфигов/историй: «Серверов: 15/15 (100%)»."""
        try:
            from config.db_settings import BACKUP_DATABASE_CONFIG
            from extensions.backup_monitor.backup_utils import (
                get_config_console_servers,
                group_config_console_rows,
            )

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return ["❌ База бэкапов не настроена"], True

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
                    return ["⚪ Данных нет"], False
                raise
            finally:
                conn.close()

            expected = get_config_console_servers()
            grouped = group_config_console_rows(rows, expected_servers=expected)
            servers = grouped.get("servers", [])
            if not servers:
                return ["⚪ Данных нет"], False

            total = len(servers)
            missing = grouped.get("missing", [])
            problem = 0
            for srv in servers:
                latest = srv.get("latest")
                if srv.get("missing") or latest is None:
                    continue
                if str(latest[1]).upper() != "OK":
                    problem += 1
            bad = problem + len(missing)
            ok_count = total - bad
            final_mark = "🟢" if grouped.get("final") else "⚪"
            lines = [
                self._status_line("Серверов", ok_count, total),
                f"{final_mark} Финальная передача на NAS",
            ]
            if missing:
                lines.append(f"• Нет свежих отчётов: {', '.join(missing)}")
            return lines, bad > 0
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки конфигов: {exc}")
            return ["❌ Данные о бэкапах конфигов недоступны"], True

    def get_supplier_stock_summary_for_report(self, period_days=7):
        """Секция остатков поставщиков: «Источников: N/N (%)»."""
        try:
            from extensions.supplier_stock_files import summarize_supplier_stock_reports

            grouped = summarize_supplier_stock_reports(period_days=period_days)
            total = 0
            ok_count = 0
            for kind in ("download", "mail"):
                for src in grouped.get(kind, []) or []:
                    total += 1
                    status = (src.get("receive") or {}).get("status", "unknown")
                    if status == "success":
                        ok_count += 1
            if total == 0:
                return ["⚪ Источников нет"], False
            return (
                [self._status_line("Источников", ok_count, total)],
                ok_count < total,
            )
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки остатков поставщиков: {exc}")
            return ["❌ Данные об остатках поставщиков недоступны"], True

    def get_tls_cert_summary_for_report(self):
        """Секция TLS-сертификатов: «Сертификатов: 6/6 (100%)»."""
        try:
            from extensions.tls_cert_monitor import collect_certificates

            results, errors = collect_certificates()
            total = len(results)
            if total == 0 and not errors:
                return ["⚪ Сертификаты не настроены"], False
            alert_count = sum(
                1 for r in results if r.get("is_alert") or not r.get("ok", True)
            )
            ok_count = total - alert_count
            lines = [self._status_line("Сертификатов", ok_count, total)]
            min_days = None
            for r in results:
                days = r.get("days_left")
                if isinstance(days, int) and (min_days is None or days < min_days):
                    min_days = days
            if min_days is not None:
                lines.append(f"• Ближайшее истечение: {min_days} дн.")
            if errors:
                lines.append(f"• Ошибки проверки: {len(errors)}")
            has_issues = bool(errors) or alert_count > 0
            return lines, has_issues
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки TLS: {exc}")
            return ["❌ Данные о TLS-сертификатах недоступны"], True

    def get_resources_summary_for_report(self):
        """Секция ресурсов серверов: «Серверов: N/N (%)» (live-проверка)."""
        try:
            from core.task_router import run_resources_task

            ok, payload = run_resources_task(force_reload=True)
            if not ok or not isinstance(payload, dict):
                return ["❌ Данные о ресурсах недоступны"], True
            stats = payload.get("stats", {}) or {}
            total = int(stats.get("total", 0) or 0)
            success = int(stats.get("success", 0) or 0)
            failed = int(stats.get("failed", 0) or 0)
            if total == 0:
                return ["⚪ Серверов с проверкой ресурсов нет"], False
            return [self._status_line("Серверов", success, total)], failed > 0
        except Exception as exc:
            debug_log(f"❌ Ошибка сводки ресурсов: {exc}")
            return ["❌ Данные о ресурсах недоступны"], True

    # ------------------------------------------------------------------
    # Расписание и отправка
    # ------------------------------------------------------------------

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

            report = self.build_report()
            message = self.render_plain(report)

            # Отправляем через унифицированный канал алертов. Для отчёта
            # просим повесить под Matrix-сообщением кнопку-эмодзи «открыть
            # меню» — пользователю удобно открыть !menu прямо из отчёта.
            # HTML-варианты дают свёрнутые секции в Telegram и Matrix.
            from lib.alerts import send_alert

            sent_ok = send_alert(
                message,
                force=True,
                attach_menu_button=True,
                telegram_html=self.render_telegram_html(report),
                matrix_html=self.render_matrix_html(report),
            )

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
