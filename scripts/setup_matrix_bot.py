"""
/scripts/setup_matrix_bot.py
Server Monitoring System v8.59.15
Утилита первичной настройки Matrix-бота для уведомлений.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass

import requests


@dataclass
class MatrixBootstrapResult:
    user_id: str
    access_token: str
    room_id: str


def _request_json(method: str, url: str, **kwargs):
    response = requests.request(method, url, timeout=20, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")
    if response.text:
        return response.json()
    return {}


def bootstrap_matrix_bot(homeserver: str, synapse_admin_token: str, username: str, password: str, room_id: str) -> MatrixBootstrapResult:
    base = homeserver.rstrip('/')
    headers = {"Authorization": f"Bearer {synapse_admin_token}"}

    # 1) создаем пользователя через admin API Synapse
    register_url = f"{base}/_synapse/admin/v2/users/@{username}:{homeserver.split('//')[-1]}"
    payload = {
        "password": password,
        "admin": False,
        "deactivated": False,
        "displayname": "Monitoring Bot",
    }
    _request_json("PUT", register_url, headers=headers, json=payload)

    # 2) логинимся как бот и получаем токен
    login_url = f"{base}/_matrix/client/v3/login"
    login_payload = {
        "type": "m.login.password",
        "identifier": {"type": "m.id.user", "user": username},
        "password": password,
    }
    login_data = _request_json("POST", login_url, json=login_payload)
    access_token = login_data.get("access_token")
    user_id = login_data.get("user_id")
    if not access_token or not user_id:
        raise RuntimeError("Не удалось получить access_token/user_id для Matrix-бота")

    # 3) присоединяем бота к комнате
    join_url = f"{base}/_matrix/client/v3/rooms/{requests.utils.quote(room_id, safe='')}/join"
    _request_json("POST", join_url, headers={"Authorization": f"Bearer {access_token}"}, json={})

    return MatrixBootstrapResult(user_id=user_id, access_token=access_token, room_id=room_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Matrix bot for monitoring alerts")
    parser.add_argument("--homeserver", required=True)
    parser.add_argument("--admin-token", required=True, help="Synapse admin access token (не токен бота из настроек Matrix)")
    parser.add_argument("--username", default="monitoring_bot")
    parser.add_argument("--password", required=True, help="Новый пароль Matrix-пользователя бота (задаётся при создании)")
    parser.add_argument("--room-id", required=True)
    args = parser.parse_args()

    result = bootstrap_matrix_bot(
        homeserver=args.homeserver,
        synapse_admin_token=args.admin_token,
        username=args.username,
        password=args.password,
        room_id=args.room_id,
    )

    print(json.dumps({
        "MATRIX_HOMESERVER": args.homeserver.rstrip('/'),
        "MATRIX_ROOM_ID": result.room_id,
        "MATRIX_ACCESS_TOKEN": result.access_token,
        "MATRIX_BOT_USER_ID": result.user_id,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
