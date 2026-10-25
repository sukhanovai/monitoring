"""
/core/api_capabilities.py
Server Monitoring System v9.0.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mobile API compatibility contract: baseline version and capability tags.
Система мониторинга серверов
Версия: 9.0.0
Автор: Александр Суханов (c)
Лицензия: MIT
Контракт совместимости мобильного API (сервер ↔ Android-клиент ComDone).

Правило (см. CLAUDE.md, docs/contracts/api_compatibility.md):

1. Всё, что есть в API на момент `API_BASELINE`, поддерживает любой сервер
   этой версии и новее. Клиент вправе вызывать это без проверок.
2. API меняется только аддитивно: поля и эндпоинты не удаляются, не
   переименовываются и не меняют смысл.
3. Каждый эндпоинт, добавленный после baseline, получает метку в
   `API_CAPABILITIES`. Android-клиент перед вызовом проверяет метку
   (`ServerCapabilities.kt`), поэтому бета-приложение из `develop`
   корректно работает со стабильным сервером из `main`, где этой метки
   ещё нет.

Сервер отдаёт обе константы в `GET /v1/mobile/version`.
"""

from __future__ import annotations

API_BASELINE = "9.0.0"

# Метки возможностей, добавленных после API_BASELINE. Пока пусто: всё
# текущее API входит в baseline 9.0.0.
API_CAPABILITIES: tuple[str, ...] = ()
