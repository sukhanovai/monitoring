#!/usr/bin/env python3
"""
/main.py
Server Monitoring System v4.16.7
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Entry point for backward compatibility
Система мониторинга серверов
Версия: 4.16.7
Автор: Александр Суханов (c)
Лицензия: MIT
Точка входа для обратной совместимости
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from monitoring.main import build_arg_parser, run_cli_checks, main

if __name__ == "__main__":
    parser = build_arg_parser()
    cli_args = parser.parse_args()

    handled, exit_code = run_cli_checks(cli_args)
    if handled:
        sys.exit(exit_code)

    main(cli_args)
