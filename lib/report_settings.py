"""
/lib/report_settings.py
Server Monitoring System v8.62.89
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Report composition settings helper
Система мониторинга серверов
Версия: 8.62.89
Автор: Александр Суханов (c)
Лицензия: MIT
Хелпер настройки состава утреннего/ручного отчёта.

Определяет, сведения из каких расширений включать в отчёт ПОМИМО базовых
данных мониторинга доступности серверов (которые присутствуют всегда).
Используется бэкендом отчёта (`modules/morning_report.py`), Telegram-ботом,
Matrix-командами и мобильным API (`extensions/web_interface`).
"""

from __future__ import annotations

import json

from lib.logging import debug_log

# Ключ настройки в БД (`core.config_manager`).
REPORT_EXTENSIONS_SETTING = "REPORT_EXTENSIONS"
REPORT_EXTENSIONS_CATEGORY = "report"
REPORT_EXTENSIONS_DESCRIPTION = (
    "Расширения, сведения которых включаются в утренний/ручной отчёт "
    "(JSON-список ID расширений)"
)

# Расширения, данные которых умеет отображать утренний/ручной отчёт.
# Порядок определяет порядок секций в отчёте. Только эти расширения можно
# выбирать в настройке состава отчёта — остальным нечего показать в нём.
REPORT_CAPABLE_EXTENSIONS = [
    "backup_monitor",
    "database_backup_monitor",
    "mail_backup_monitor",
    "stock_load_monitor",
    "zfs_monitor",
]

# Короткие подписи для UI (бот/Matrix). Полные имена берутся из
# extensions.extension_manager.AVAILABLE_EXTENSIONS, но здесь держим
# компактные варианты для кнопок и текстовых меню.
REPORT_EXTENSION_LABELS = {
    "backup_monitor": "💾 Бэкапы Proxmox",
    "database_backup_monitor": "🗃️ Бэкапы БД",
    "mail_backup_monitor": "📬 Бэкапы почты",
    "stock_load_monitor": "📦 Загрузка остатков 1С",
    "zfs_monitor": "🧊 Статусы ZFS",
}

# По умолчанию в отчёт включены все поддерживаемые расширения — это сохраняет
# прежнее поведение отчёта до появления настройки.
DEFAULT_REPORT_EXTENSIONS = list(REPORT_CAPABLE_EXTENSIONS)


def _normalize(raw_value):
    """Приводит произвольное хранимое значение к списку известных ID."""
    if raw_value is None:
        return list(DEFAULT_REPORT_EXTENSIONS)

    value = raw_value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return list(DEFAULT_REPORT_EXTENSIONS)
        try:
            parsed = json.loads(text)
            value = parsed if isinstance(parsed, list) else [text]
        except (ValueError, json.JSONDecodeError):
            value = [item.strip() for item in text.replace(";", ",").split(",")]

    if not isinstance(value, (list, tuple, set)):
        return list(DEFAULT_REPORT_EXTENSIONS)

    selected = {str(item).strip() for item in value}
    # Сохраняем канонический порядок и отбрасываем неизвестные расширения.
    return [ext for ext in REPORT_CAPABLE_EXTENSIONS if ext in selected]


def get_report_extensions(use_cache: bool = True):
    """Возвращает список ID расширений, выбранных для включения в отчёт."""
    try:
        from core.config_manager import config_manager

        raw_value = config_manager.get_setting(
            REPORT_EXTENSIONS_SETTING, None, use_cache=use_cache
        )
    except Exception as exc:  # pragma: no cover - защита от проблем с БД
        debug_log(f"⚠️ Не удалось прочитать {REPORT_EXTENSIONS_SETTING}: {exc}")
        return list(DEFAULT_REPORT_EXTENSIONS)

    return _normalize(raw_value)


def set_report_extensions(extensions) -> bool:
    """Сохраняет выбранный состав отчёта (нормализуя и упорядочивая список)."""
    normalized = _normalize(list(extensions) if extensions is not None else [])
    try:
        from core.config_manager import config_manager

        return config_manager.set_setting(
            REPORT_EXTENSIONS_SETTING,
            normalized,
            category=REPORT_EXTENSIONS_CATEGORY,
            description=REPORT_EXTENSIONS_DESCRIPTION,
            data_type="list",
        )
    except Exception as exc:  # pragma: no cover
        debug_log(f"⚠️ Не удалось сохранить {REPORT_EXTENSIONS_SETTING}: {exc}")
        return False


def toggle_report_extension(extension_id: str) -> list:
    """Переключает наличие расширения в отчёте и возвращает новый список."""
    if extension_id not in REPORT_CAPABLE_EXTENSIONS:
        return get_report_extensions(use_cache=False)
    current = set(get_report_extensions(use_cache=False))
    if extension_id in current:
        current.discard(extension_id)
    else:
        current.add(extension_id)
    set_report_extensions(current)
    return get_report_extensions(use_cache=False)


def is_report_extension_enabled(extension_id: str, selected=None) -> bool:
    """True, если расширение выбрано для включения в отчёт."""
    if selected is None:
        selected = get_report_extensions()
    return extension_id in selected


def get_report_extension_label(extension_id: str) -> str:
    """Человекочитаемая подпись расширения для UI отчёта."""
    label = REPORT_EXTENSION_LABELS.get(extension_id)
    if label:
        return label
    try:
        from extensions.extension_manager import AVAILABLE_EXTENSIONS

        return AVAILABLE_EXTENSIONS.get(extension_id, {}).get("name", extension_id)
    except Exception:
        return extension_id
