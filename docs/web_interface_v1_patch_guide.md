# Патч-гайд: добавить `/v1/control/actions` и `/v1/settings/monitoring` в `extensions/web_interface/__init__.py`

Ниже — чистый пошаговый план без магии, чтобы в ветке `devel` внести изменения аккуратно.

## Файл, который нужно править

- `/opt/monitoring/extensions/web_interface/__init__.py`

## Новый файл с инструкцией (этот файл)

- `/opt/monitoring/docs/web_interface_v1_patch_guide.md`

---

## 0) Зачем это нужно

Android-клиент вызывает:

- `POST /v1/control/actions`
- `PATCH /v1/settings/monitoring`

Если их нет в Flask-приложении, получаешь `404` даже с валидным токеном.

---

## 1) Бэкап перед правками

```bash
cd /opt/monitoring
cp extensions/web_interface/__init__.py extensions/web_interface/__init__.py.bak.$(date +%F_%H%M%S)
```

---

## 2) Что добавить в imports

В верхней части `extensions/web_interface/__init__.py` проверь/добавь:

```python
import uuid
```

`datetime` уже обычно импортирован, но если нет — добавь:

```python
from datetime import datetime
```

---

## 3) Вставь helper для маппинга actions

Добавь этот блок рядом с API-функциями (например рядом с `api_run_action`):

```python
def _map_mobile_action_to_legacy(action: str) -> str | None:
    mapping = {
        "pause_monitoring": "toggle_monitoring",  # временный fallback
        "resume_monitoring": "toggle_monitoring",  # временный fallback
        "send_morning_report": "morning_report",
        "force_quiet": "toggle_silent",           # временный fallback
        "force_loud": "toggle_silent",            # временный fallback
    }
    return mapping.get(action)
```

> Примечание: для `pause/resume/force_quiet/force_loud` это временный маппинг. Лучше позже сделать отдельные точные handlers.

---

## 4) Добавь endpoint `POST /v1/control/actions`

Вставь **целиком**:

```python
@app.route('/v1/control/actions', methods=['POST'])
def v1_control_actions():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    payload = request.get_json(silent=True) or {}
    action = str(payload.get('action') or '').strip()
    if not action:
        return jsonify({
            "error": {
                "code": "INVALID_ACTION",
                "message": "Field 'action' is required",
                "request_id": request_id,
            }
        }), 400

    legacy_action = _map_mobile_action_to_legacy(action)
    if not legacy_action:
        return jsonify({
            "error": {
                "code": "INVALID_ACTION",
                "message": f"Unsupported action: {action}",
                "request_id": request_id,
            }
        }), 400

    try:
        # Переиспользуем текущую legacy-логику
        with app.test_request_context(f"/api/run_action?action={legacy_action}"):
            legacy_response = api_run_action()

        # Если legacy вернул tuple(response, status)
        if isinstance(legacy_response, tuple):
            response_obj, status_code = legacy_response
        else:
            response_obj, status_code = legacy_response, 200

        data = response_obj.get_json(silent=True) if hasattr(response_obj, 'get_json') else {}
        message = (data or {}).get('message') or 'Action processed'

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted" if status_code < 400 else "rejected",
            "message": message,
        }), (200 if status_code < 400 else status_code)

    except Exception as e:
        return jsonify({
            "error": {
                "code": "CONTROL_ACTION_FAILED",
                "message": str(e),
                "request_id": request_id,
            }
        }), 500
```

---

## 5) Добавь endpoint `PATCH /v1/settings/monitoring`

Вставь **целиком**:

```python
@app.route('/v1/settings/monitoring', methods=['PATCH'])
def v1_settings_monitoring():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    payload = request.get_json(silent=True) or {}

    check_interval = payload.get('check_interval_sec')
    timeout_sec = payload.get('timeout_sec')
    max_downtime = payload.get('max_downtime_sec')

    if check_interval is None and timeout_sec is None and max_downtime is None:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "At least one field is required",
                "request_id": request_id,
            }
        }), 400

    try:
        from config.db_settings_app import settings_manager

        if check_interval is not None:
            check_interval = int(check_interval)
            if check_interval < 5:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "check_interval_sec must be >= 5", "request_id": request_id}}), 400
            settings_manager.set_setting('CHECK_INTERVAL', check_interval, 'monitoring', 'Интервал проверки серверов (секунды)', 'int')
        else:
            check_interval = settings_manager.get_setting('CHECK_INTERVAL', 60)

        if max_downtime is not None:
            max_downtime = int(max_downtime)
            if max_downtime < 30:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "max_downtime_sec must be >= 30", "request_id": request_id}}), 400
            settings_manager.set_setting('MAX_FAIL_TIME', max_downtime, 'monitoring', 'Максимальное время простоя до алерта (секунды)', 'int')
        else:
            max_downtime = settings_manager.get_setting('MAX_FAIL_TIME', 900)

        if timeout_sec is not None:
            timeout_sec = int(timeout_sec)
            if timeout_sec < 1:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "timeout_sec must be >= 1", "request_id": request_id}}), 400
            settings_manager.set_setting('API_TIMEOUT_SEC', timeout_sec, 'monitoring', 'Таймаут API (секунды)', 'int')
        else:
            timeout_sec = settings_manager.get_setting('API_TIMEOUT_SEC', 15)

        return jsonify({
            "request_id": request_id,
            "settings": {
                "check_interval_sec": check_interval,
                "timeout_sec": timeout_sec,
                "max_downtime_sec": max_downtime,
                "updated_at": datetime.now().isoformat(),
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": {
                "code": "CONFIG_STORE_UNAVAILABLE",
                "message": str(e),
                "request_id": request_id,
            }
        }), 500
```

---

## 6) Перезапуск и проверка

### Перезапуск сервиса

```bash
sudo systemctl restart server-monitor.service
sudo systemctl status server-monitor.service --no-pager -l
```

### Локальные проверки (внутренний API)

```bash
curl -i "http://192.168.20.2:5000/v1/monitoring/availability?scope=all" \
  -H "Authorization: Bearer <NEW_TOKEN>"

curl -i -X POST "http://192.168.20.2:5000/v1/control/actions" \
  -H "Authorization: Bearer <NEW_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: debug-control-001" \
  -d '{"action":"pause_monitoring"}'

curl -i -X PATCH "http://192.168.20.2:5000/v1/settings/monitoring" \
  -H "Authorization: Bearer <NEW_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: debug-settings-001" \
  -d '{"check_interval_sec":60,"timeout_sec":15,"max_downtime_sec":300}'
```

### Проверка через внешний nginx

```bash
curl -i -X POST "https://api.202020.ru:8443/v1/control/actions" \
  -H "Authorization: Bearer <NEW_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"action":"pause_monitoring"}'

curl -i -X PATCH "https://api.202020.ru:8443/v1/settings/monitoring" \
  -H "Authorization: Bearer <NEW_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"check_interval_sec":60,"timeout_sec":15,"max_downtime_sec":300}'
```

---

## 7) Быстрый rollback

```bash
cd /opt/monitoring
ls -1t extensions/web_interface/__init__.py.bak.* | head -n 1
cp <последний_бэкап> extensions/web_interface/__init__.py
sudo systemctl restart server-monitor.service
```

---

## 8) Что ещё потом улучшить (после того как «завелось»)

1. Убрать временный маппинг `toggle_*` и сделать отдельные точные handlers под `pause/resume/quiet/loud`.
2. Добавить нормальный store для Opaque токенов (Redis/DB) с revoke endpoint.
3. Добавить unit-тесты на `/v1/control/actions` и `/v1/settings/monitoring`.
