#!/usr/bin/env python3
"""
/main.py
Server Monitoring System v4.15.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.15.1
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    opt_root = Path("/opt")
    if str(opt_root) not in sys.path:
        sys.path.insert(0, str(opt_root))

    from opt.monitoring.main import main