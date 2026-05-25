"""
Общая настройка pytest. Изолирует тесты от рабочего окружения:
- MONITORING_BASE_DIR указывает на tmp, чтобы config/settings.py не
  создавал data/ и logs/ в репозитории.
- MAILDIR_BASE указывает на tmp, чтобы mail_monitor не пытался
  читать /root/Maildir.
- В sys.modules подкладываются лёгкие заглушки runtime-зависимостей
  (requests и т.п.), чтобы smoke-тесты на импорты работали в CI,
  где из dev-зависимостей ставится только ruff/black/mypy/pytest.
"""

from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path

# Корень проекта добавляем в sys.path до любых импортов, чтобы тесты
# работали без установки пакета.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _install_stub(name: str) -> None:
    """Подложить пустой модуль-заглушку, если настоящая либа не установлена."""
    if name in sys.modules:
        return
    try:
        __import__(name)
    except ImportError:
        sys.modules[name] = types.ModuleType(name)


# Третьесторонние runtime-зависимости, которые подгружаются по цепочке
# config/__init__.py → db_settings → core/__init__.py → checker и
# lib/__init__.py → alerts даже при импорте «лёгких» config.settings /
# lib.utils. В CI runtime deps не ставятся.
for _stub in ("requests", "paramiko"):
    _install_stub(_stub)

_TMP_BASE = Path(tempfile.mkdtemp(prefix="monitoring-test-"))
os.environ.setdefault("MONITORING_BASE_DIR", str(_TMP_BASE))
os.environ.setdefault("MONITORING_MAILDIR_BASE", str(_TMP_BASE / "Maildir"))
# Пустые токены — реальный коннект из тестов невозможен.
os.environ.setdefault("MATRIX_ACCESS_TOKEN", "")
os.environ.setdefault("MATRIX_BOT_PASSWORD", "")
