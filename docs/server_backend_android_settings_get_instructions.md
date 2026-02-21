Status: Draft
Owner: Android/BFF integration
Last updated: 2026-02-20

# Что нужно сделать на сервере для Android автосинхронизации настроек

Сейчас Android-клиент автоматически запрашивает настройки при старте/после сохранения токена.
Если backend отвечает `HTTP 405`, клиент не может подтянуть значения из БД.

## Нужные endpoint'ы (GET)

Реализовать read-only endpoint'ы:

1. `GET /v1/settings/monitoring`
2. `GET /v1/settings/bot`
3. `GET /v1/settings/time`
4. `GET /v1/settings/auth`

## Ожидаемые поля ответов

### 1) Monitoring

```json
{
  "request_id": "...",
  "settings": {
    "check_interval_sec": 60,
    "timeout_sec": 15,
    "max_downtime_sec": 300
  }
}
```

### 2) Bot

```json
{
  "request_id": "...",
  "settings": {
    "telegram_chat_id": "-100123...",
    "masked_token": "123456:***"
  }
}
```

### 3) Time

```json
{
  "request_id": "...",
  "settings": {
    "quiet_start": "23:00",
    "quiet_end": "08:00",
    "metrics_collection_time": "07:30"
  }
}
```

### 4) Auth

```json
{
  "request_id": "...",
  "settings": {
    "auth_mode": "mixed",
    "ssh_username": "root",
    "ssh_port": 22,
    "windows_username": "Administrator",
    "masked_ssh_password": "********",
    "masked_windows_password": "********"
  }
}
```

## Важно по безопасности

- Не отдавать в GET открытые токены и пароли.
- Возвращать только masked-значения для секретов.
- Сохранять `request_id` в ответах и логах.

## Минимальная проверка после внедрения

```bash
curl -k -H "Authorization: Bearer <token>" https://api.202020.ru:8443/v1/settings/monitoring
curl -k -H "Authorization: Bearer <token>" https://api.202020.ru:8443/v1/settings/bot
curl -k -H "Authorization: Bearer <token>" https://api.202020.ru:8443/v1/settings/time
curl -k -H "Authorization: Bearer <token>" https://api.202020.ru:8443/v1/settings/auth
```

Ожидаемо: `200 OK`, а не `405 Method Not Allowed`.