#!/usr/bin/env python3
"""
/scripts/generate_mobile_default_token.py
Server Monitoring System v8.50.91
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Generate bootstrap token for Android auth flow.
Система мониторинга серверов
Версия: 8.50.91
Автор: Александр Суханов (c)
Лицензия: MIT
Генерация bootstrap-токена для Android auth flow

Usage:
  python scripts/generate_mobile_default_token.py
  python scripts/generate_mobile_default_token.py --length 48
"""

from __future__ import annotations

import argparse
import secrets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate MOBILE_DEFAULT_TOKEN for Monitoring Android bootstrap auth."
    )
    parser.add_argument(
        "--length",
        type=int,
        default=48,
        help="Number of random bytes for token generation (default: 48).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    length = max(16, int(args.length))
    token = secrets.token_urlsafe(length)

    print("MOBILE_DEFAULT_TOKEN generated:")
    print(token)
    print()
    print("Add to /etc/systemd/system/server-monitor.service:")
    print(f'Environment="MOBILE_DEFAULT_TOKEN={token}"')
    print('Environment="MOBILE_SESSION_TOKEN_TTL_SEC=0"')
    print()
    print("Then reload and restart:")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl restart server-monitor.service")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
