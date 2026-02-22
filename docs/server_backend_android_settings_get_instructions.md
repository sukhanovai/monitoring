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

## Как перенести этот файл в `develop` (если `pathspec` не найден)

Ошибка вида `pathspec ... did not match any file(s) known to git` обычно означает, что:
- вы указали несуществующую локально ветку-источник;
- или файл в этой ветке/коммите ещё не присутствует.

Рабочий сценарий:

```bash
git fetch --all --prune
git branch -a
```

Если файл находится в текущей ветке (например, `work`), перенос в `develop`:

```bash
git checkout develop
git pull origin develop
git checkout work -- docs/server_backend_android_settings_get_instructions.md
git add docs/server_backend_android_settings_get_instructions.md
git commit -m "Добавить инструкцию для backend по GET settings"
git push origin develop
```

Если локальной ветки `work` нет, но есть удалённая `origin/work`:

```bash
git checkout develop
git pull origin develop
git checkout origin/work -- docs/server_backend_android_settings_get_instructions.md
```

Если хотите перенести не только файл, а целиком конкретный коммит:

```bash
git checkout develop
git pull origin develop
git cherry-pick <commit_sha>
```

## Ошибка `Your local changes would be overwritten by merge` при `git pull`

Если при `git pull` видишь:

```text
error: Your local changes to the following files would be overwritten by merge
```

это значит, что у тебя есть незакоммиченные правки, а remote пытается обновить те же файлы.

### Быстрый безопасный сценарий (рекомендую)

```bash
git status
git stash push -m "wip before pull" 
git pull --rebase
git stash pop
```

После `stash pop` могут появиться конфликты — это нормально, тогда решаешь конфликт и делаешь commit.

### Если правки уже готовы

```bash
git add -A
git commit -m "Локальные правки перед pull"
git pull --rebase
```

### Если локальные правки не нужны

```bash
git reset --hard
git pull --rebase
```

> `reset --hard` удалит незакоммиченные изменения безвозвратно.

## Разница тестирования: эмулятор в локальной сети vs телефон снаружи

Да, разница существенная.

### 1) Эмулятор/устройство в той же локальной сети

Что обычно работает проще:
- доступ по внутреннему IP сервера (`192.168.x.x` / `10.x.x.x`);
- меньше сетевых ограничений провайдера;
- проще отладка через `adb reverse`/`adb tcpip` и локальные сертификаты.

На что смотреть:
- открыт ли порт backend (`8443`);
- корректен ли сертификат для используемого хоста/IP;
- нет ли блокировки на роутере/фаерволе.

### 2) Телефон «снаружи» (мобильная сеть/другая сеть)

Добавляются риски:
- NAT/CGNAT и недоступность сервера по локальному IP;
- фильтрация портов/протоколов у провайдера;
- DNS может резолвиться иначе, чем в локалке;
- TLS/сертификат может быть валиден для домена, но не для IP.

### Практический вывод

Если в локалке всё ок, а снаружи timeout/401/403:
1. Проверь, что в Android выставлен внешний `Base URL` (домен/порт), а не локальный IP.
2. Проверь доступность endpoint'ов с телефона вне локалки:
   - `/v1/availability`
   - `/v1/control/action`
   - `/v1/settings/*`
3. Разделяй проблемы:
   - timeout = сеть/маршрутизация/порт;
   - 401/403 = токен/права.

### Минимальный чек-лист для Android

1. `Base URL` указывает на реально доступный извне хост.
2. Токен сохранён и имеет права на нужные endpoint'ы.
3. Для `/v1/settings/*` backend действительно поддерживает `GET`.
4. Сертификат валиден для домена, который указан в `Base URL`.
