# ComDone — установка, настройка и обновление

Server Monitoring System v9.0.0

Пошаговая инструкция для развёртывания ComDone на своём сервере: от чистой
системы до работающих Telegram-бота, Matrix-бота, веб-панели и
Android-приложения. Отдельный раздел — обновление уже работающей установки
(в том числе с 8.x на 9.x).

Стабильная версия всегда лежит в ветке `main` и в разделе
[Releases](https://github.com/sukhanovai/monitoring/releases/latest).

## Содержание

1. [Как устроена система](#1-как-устроена-система)
2. [Требования](#2-требования)
3. [Установка сервера](#3-установка-сервера)
4. [Первичная настройка](#4-первичная-настройка)
5. [Запуск как сервис (systemd)](#5-запуск-как-сервис-systemd)
6. [Веб-панель и API: обратный прокси и TLS](#6-веб-панель-и-api-обратный-прокси-и-tls)
7. [Android-приложение](#7-android-приложение)
8. [Matrix (опционально)](#8-matrix-опционально)
9. [Почтовый монитор бэкапов (опционально)](#9-почтовый-монитор-бэкапов-опционально)
10. [Обновление](#10-обновление)
11. [Резервное копирование и откат](#11-резервное-копирование-и-откат)
12. [Диагностика](#12-диагностика)
13. [Справочник переменных окружения](#13-справочник-переменных-окружения)

---

## 1. Как устроена система

```
                 ┌──────────────── сервер ComDone ────────────────┐
 Telegram ◄────► │ main.py (systemd: server-monitor)              │
 Matrix   ◄────► │  ├─ Telegram-бот, Matrix-бот                   │
                 │  ├─ мониторинг серверов, ресурсов, бэкапов     │
 Браузер,        │  └─ веб-панель + API для Android :5000 (HTTP)  │
 Android ──HTTPS─► nginx/Apache :443 или :8443 (TLS) ─► :5000     │
                 │                                                │
 Почта ────────► │ mail_monitor.py (systemd: mail-monitor, опц.)  │
                 │ data/  — настройки (settings.db), токены, кэш  │
                 └────────────────────────────────────────────────┘
```

- Один процесс `main.py` обслуживает сразу всё: ботов, мониторинг, веб-панель
  и API для Android.
- Все настройки и токены хранятся в каталоге `data/` (`settings.db` и др.).
  Этот каталог не отслеживается git и **не затрагивается обновлениями**.
- Android-приложению нужен HTTPS с действительным сертификатом, поэтому
  API публикуется наружу через обратный прокси с TLS.

## 2. Требования

| Компонент | Требование |
|---|---|
| ОС | Linux, рекомендуется Debian 12 / Ubuntu 22.04+ |
| Python | **3.10–3.12** (рекомендуется 3.11). Python 3.13 не поддерживается: `python-telegram-bot` 13.x использует удалённый в 3.13 модуль `imghdr` |
| Права | root (systemd-сервис, доступ к `/root/.ssh` для SSH-проверок, Maildir) |
| Сеть | исходящий доступ к `api.telegram.org`, `api.github.com` (проверка обновлений Android), к контролируемым серверам |
| Для Android | доменное имя и TLS-сертификат (например Let's Encrypt) |
| Telegram | токен бота от [@BotFather](https://t.me/BotFather) |
| Matrix (опц.) | аккаунт бота на вашем homeserver |

## 3. Установка сервера

Каталог установки в примерах — `/opt/monitoring`.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

sudo git clone https://github.com/sukhanovai/monitoring.git /opt/monitoring
cd /opt/monitoring
sudo git checkout main            # стабильная версия

sudo python3 -m venv venv
sudo venv/bin/pip install --upgrade pip
sudo venv/bin/pip install -r requirements.txt
```

Matrix нужен? Поставьте его зависимости **вторым шагом**:

```bash
sudo venv/bin/pip install -r requirements-matrix.txt
```

> pip выведет предупреждение
> `python-telegram-bot 13.15 requires cachetools==4.2.2, but you have cachetools …`.
> Это ожидаемо и безопасно: бот работает с новой версией `cachetools`.
> Из-за этого конфликта Matrix вынесен в отдельный файл — одной командой
> pip такие зависимости не ставит.

Проверка:

```bash
sudo venv/bin/python -c "import telegram, flask, paramiko; print('OK')"
```

## 4. Первичная настройка

Настройки хранятся в `data/settings.db`. **Не редактируйте
`config/settings.py`**: это файл из репозитория, локальные правки помешают
обновлению через `git pull`.

### 4.1. Токен Telegram-бота и чаты

1. Создайте бота у [@BotFather](https://t.me/BotFather) и получите токен.
2. Напишите боту любое сообщение и узнайте `chat.id`:

   ```bash
   curl -s "https://api.telegram.org/bot<ТОКЕН>/getUpdates" | grep -o '"chat":{"id":-\?[0-9]*'
   ```

3. Запишите оба значения в базу настроек (один раз):

   ```bash
   cd /opt/monitoring
   sudo venv/bin/python - <<'EOF'
   from config.db_settings_app import settings_manager as s
   s.set_setting("TELEGRAM_TOKEN", "123456:ABC-ваш-токен", "telegram", "Токен Telegram-бота", "string")
   s.set_setting("CHAT_IDS", ["123456789"], "telegram", "ID чатов для уведомлений", "auto")
   EOF
   ```

   Чаты из `CHAT_IDS` автоматически становятся каналами администратора (см.
   [multi_user.md](multi_user.md)).

Дальше серверы, пороги, расписание, расширения и пользователи настраиваются
из бота (`/settings`), веб-панели или Android-приложения.

### 4.2. Секреты окружения

Секреты, которые читаются из переменных окружения, держите в отдельном файле
с правами только для root:

```bash
sudo install -d -m 700 /etc/comdone
sudo install -m 600 /dev/null /etc/comdone/comdone.env
sudo nano /etc/comdone/comdone.env
```

```ini
# Bootstrap-токен для первого входа Android-приложения
# (сгенерировать: venv/bin/python scripts/generate_mobile_default_token.py)
MOBILE_DEFAULT_TOKEN=замените_на_длинный_случайный_токен
# Срок жизни рабочих токенов Android в секундах, 0 — бессрочно
MOBILE_SESSION_TOKEN_TTL_SEC=0

# Matrix (раздел 8) — оставьте пустыми, если Matrix не используется
MATRIX_HOMESERVER=
MATRIX_ACCESS_TOKEN=
MATRIX_ROOM_ID=
```

Полный список переменных — [раздел 13](#13-справочник-переменных-окружения).

### 4.3. Проверка без запуска бота

```bash
cd /opt/monitoring
sudo venv/bin/python main.py --check availability --dry-run
```

## 5. Запуск как сервис (systemd)

```bash
sudo nano /etc/systemd/system/server-monitor.service
```

```ini
[Unit]
Description=ComDone server monitoring
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-/etc/comdone/comdone.env

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba
ExecStart=/opt/monitoring/venv/bin/python /opt/monitoring/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

Если исходящий трафик идёт через прокси, замените `ExecStart` на
`ExecStart=/usr/bin/proxychains4 -q /opt/monitoring/venv/bin/python /opt/monitoring/main.py`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now server-monitor
sudo systemctl status server-monitor
journalctl -u server-monitor -f      # живой лог
```

Напишите боту `/start` — должно появиться главное меню.

## 6. Веб-панель и API: обратный прокси и TLS

Расширение `web_interface` (включено по умолчанию) слушает
`0.0.0.0:5000` по HTTP. Порт и адрес меняются настройками `WEB_PORT` и
`WEB_HOST` в боте (`/settings`). Наружу публикуйте его только через
обратный прокси с TLS, а порт 5000 закройте файрволом:

```bash
sudo ufw allow 443/tcp          # или 8443, если 443 занят
sudo ufw deny 5000/tcp
```

### 6.1. nginx + Let's Encrypt

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/comdone
```

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        # WebSocket веб-панели
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120s;
    }
}
```

```bash
sudo certbot certonly --nginx -d api.example.com
sudo ln -s /etc/nginx/sites-available/comdone /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 6.2. Apache (если уже используется)

```bash
sudo a2enmod ssl proxy proxy_http proxy_wstunnel headers
```

```apache
<VirtualHost *:443>
    ServerName api.example.com
    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/api.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/api.example.com/privkey.pem

    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"
    ProxyPass        / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>
```

Если прокси стоит на другой машине (сервер за NAT), укажите в `ProxyPass`
внутренний адрес сервера ComDone вместо `127.0.0.1` и разрешите порт 5000
только с адреса прокси.

### 6.3. Проверка

```bash
curl -s https://api.example.com/v1/mobile/version \
  -H "Authorization: Bearer <MOBILE_DEFAULT_TOKEN>"
```

Ожидается JSON с `latest_version` и `server_version`. Ответ `401`
означает, что API доступен, но токен не тот. `404` или `502` означает,
что прокси не достучался до `:5000`.

Вход в веб-панель задаётся настройками `WEB_LOGIN` и `WEB_PASSWORD` в боте.

## 7. Android-приложение

### 7.1. Установка

1. Скачайте на телефон последнюю стабильную версию:
   **<https://github.com/sukhanovai/monitoring/releases/latest/download/ComDone.apk>**
2. Откройте файл и разрешите установку из этого источника, когда Android
   спросит.
3. Нужен Android 8.0 или новее.

### 7.2. Подключение к серверу

1. Откройте ComDone → **Настройки**.
2. **Base URL** — адрес из раздела 6, например `https://api.example.com/`
   (с портом, если он не 443: `https://api.example.com:8443/`).
3. **Токен** — значение `MOBILE_DEFAULT_TOKEN` из `/etc/comdone/comdone.env`.
4. Сохраните. Приложение обменяет bootstrap-токен на личный рабочий токен
   устройства и дальше использует только его.
5. Чтобы получать личные оповещения, привяжите устройство к пользователю:
   **Настройки → 📱 Это устройство** (подробнее — [multi_user.md](multi_user.md)).

Приложение принимает только HTTPS с доверенным сертификатом: публичным
(Let's Encrypt) или из установленного на телефон пользовательского CA.

### 7.3. Обновления приложения

**Настройки → Обновление** — проверка и установка новой версии прямо из
приложения:

| Канал | Что приходит |
|---|---|
| **Стабильная** (по умолчанию) | только стабильные релизы |
| **Бета** | тестовые сборки раньше стабильного релиза |

Обновление ставится поверх установленного приложения, токен и настройки
сохраняются. Версии каналов сервер берёт с GitHub, поэтому серверу нужен
исходящий доступ к `api.github.com`. Без него используется версия,
указанная в самом сервере.

### 7.4. Перевыпуск токена устройства

Если телефон потерян или приложение переустановлено «с нуля»:

```bash
curl -X POST "https://api.example.com/v1/auth/token/reissue" \
  -H "Authorization: Bearer <MOBILE_DEFAULT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"android-device-1","subject":"android-client","reissue":true}'
```

## 8. Matrix (опционально)

1. Установите зависимости: `sudo venv/bin/pip install -r requirements-matrix.txt`.
2. Создайте аккаунт бота на своём homeserver и комнату для уведомлений,
   пригласите туда бота.
3. Заполните в `/etc/comdone/comdone.env`:

   ```ini
   MATRIX_HOMESERVER=https://matrix.example.com
   MATRIX_BOT_USER_ID=@comdone-bot:matrix.example.com
   MATRIX_BOT_PASSWORD=пароль_бота
   MATRIX_ROOM_ID=!roomid:matrix.example.com
   MATRIX_ALLOWED_USER_IDS=@admin:matrix.example.com
   ```

   Вход по паролю нужен для зашифрованных комнат: он даёт постоянное
   устройство и хранилище ключей в `data/matrix_store/`. Не удаляйте этот
   каталог и не меняйте `MATRIX_DEVICE_NAME`, иначе бот появится как новое
   устройство и потеряет ключи.
4. `sudo systemctl restart server-monitor`.

Подробно, включая автоматическое создание бота через Synapse Admin API,
описано в [matrix_bot_management.md](matrix_bot_management.md).

## 9. Почтовый монитор бэкапов (опционально)

Разбирает письма о бэкапах (Proxmox, БД, ZFS и др.) из локального Maildir
(`MONITORING_MAILDIR_BASE`, по умолчанию `/root/Maildir`).

```bash
sudo nano /etc/systemd/system/mail-monitor.service
```

```ini
[Unit]
Description=ComDone backup mail monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring
EnvironmentFile=-/etc/comdone/comdone.env
ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba
ExecStart=/opt/monitoring/venv/bin/python /opt/monitoring/modules/mail_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba /root/Maildir

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mail-monitor
```

## 10. Обновление

### 10.1. Обычное обновление (в пределах 9.x)

```bash
cd /opt/monitoring
sudo git status --short          # должно быть пусто (см. ниже, если нет)
sudo tar czf /root/comdone-data-$(date +%F).tgz data   # бэкап, раздел 11
sudo systemctl stop server-monitor mail-monitor
sudo git pull --ff-only origin main
sudo venv/bin/pip install -r requirements.txt
# если используется Matrix:
sudo venv/bin/pip install -r requirements-matrix.txt
sudo systemctl start server-monitor mail-monitor
journalctl -u server-monitor -n 50 --no-pager
```

Если `git status` показывает изменённые файлы (обычно вы правили
`config/settings.py`), перенесите значения в базу настроек или в
`/etc/comdone/comdone.env` (раздел 4), затем верните файл:
`sudo git checkout -- config/settings.py`.

Android-клиенты обновляются сами через **Настройки → Обновление**.

### 10.2. Обновление с 8.x на 9.0

Данные и подключения сохраняются: токены Telegram и Matrix, ключи Matrix,
токены Android-устройств и пользователи лежат в `data/`, а этот каталог
обновление не трогает. Что нужно учесть:

1. **Ветка.** Стабильная версия теперь всегда в `main`. Если сервер стоял на
   `develop`, переключите его: `sudo git checkout main && sudo git pull`.
   Либо оставайтесь на `develop`, если хотите получать тестовые версии.
2. **Зависимости.** Matrix вынесен в `requirements-matrix.txt` (раздел 3).
   Уже установленные пакеты остаются на месте, повторная установка ничего
   не ломает.
3. **Android-приложение.** Название файла теперь `ComDone-<версия>.apk`.
   Приложение обновляется **поверх** (пакет и подпись прежние), переустанавливать
   не нужно, токен и настройки сохраняются. Каналы обновления называются
   «Стабильная» и «Бета». Если выбор канала не делался, после обновления
   сервера по умолчанию будет «Стабильная».
4. **Переменная `ANDROID_DEFAULT_UPDATE_BRANCH`.** Значение по умолчанию —
   `main`. Если вы задавали её явно, проверьте значение.

## 11. Резервное копирование и откат

Всё состояние системы находится в `data/` (плюс `/etc/comdone/comdone.env`
и unit-файлы systemd). Код восстанавливается из git.

```bash
# бэкап (например, ежедневно из cron)
sudo tar czf /root/comdone-data-$(date +%F).tgz -C /opt/monitoring data
sudo cp /etc/comdone/comdone.env /root/comdone.env.bak
```

Откат на предыдущую версию:

```bash
cd /opt/monitoring
sudo systemctl stop server-monitor mail-monitor
sudo git log --oneline -5                     # найти нужный коммит/тег
sudo git checkout <тег-или-коммит>            # например v9.0.0
sudo tar xzf /root/comdone-data-ДАТА.tgz -C /opt/monitoring   # если нужно вернуть и данные
sudo systemctl start server-monitor mail-monitor
```

После отката вернитесь на ветку командой `sudo git checkout main`, когда
исправление выйдет.

## 12. Диагностика

| Симптом | Что проверить |
|---|---|
| Бот молчит | `journalctl -u server-monitor -n 100`; токен в `settings.db`; доступ к `api.telegram.org` (при необходимости `proxychains4`) |
| `409 Conflict` от Telegram | этот же токен используется вторым процессом — остановите его |
| Android: «Нет соединения с API» | Base URL и порт, файрвол, `curl` из раздела 6.3 |
| Android: ошибка TLS | срок и имя сертификата, дата и время на телефоне |
| Android: HTTP 401 | токен устройства отозван — повторно введите `MOBILE_DEFAULT_TOKEN` или перевыпустите (7.4) |
| Android: «Функция недоступна на этом сервере» | приложение новее сервера (бета-версия) — обновите сервер |
| Не видно обновлений в приложении | серверу нужен доступ к `api.github.com`; `ANDROID_RELEASES_FROM_GITHUB=1` |
| Matrix не отвечает в зашифрованной комнате | вход по паролю (`MATRIX_BOT_USER_ID`/`MATRIX_BOT_PASSWORD`), сохранность `data/matrix_store/` |

Быстрые проверки:

```bash
cd /opt/monitoring
sudo venv/bin/python -c "import config; print('конфигурация OK')"
sudo venv/bin/python main.py --check availability --dry-run
curl -s http://127.0.0.1:5000/v1/mobile/version -H "Authorization: Bearer <MOBILE_DEFAULT_TOKEN>"
```

## 13. Справочник переменных окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `MONITORING_BASE_DIR` | каталог проекта | где лежат `data/` и `logs/` |
| `MONITORING_MAILDIR_BASE` | `/root/Maildir` | Maildir почтового монитора |
| `MOBILE_DEFAULT_TOKEN` | — | bootstrap-токен для первого входа Android |
| `MOBILE_SESSION_TOKEN_TTL_SEC` | `0` | срок жизни рабочих токенов Android (0 — бессрочно) |
| `MATRIX_HOMESERVER` | — | адрес Matrix homeserver |
| `MATRIX_ACCESS_TOKEN` | — | токен бота (если не используется вход по паролю) |
| `MATRIX_BOT_USER_ID`, `MATRIX_BOT_PASSWORD` | — | вход бота по паролю (нужен для E2EE) |
| `MATRIX_ROOM_ID` | — | комната уведомлений |
| `MATRIX_ALLOWED_USER_IDS`, `MATRIX_ALLOWED_ROOM_IDS` | — | кому разрешены команды |
| `MATRIX_DEVICE_NAME` | `monitoring-command-bot` | имя устройства бота (не менять после первого входа) |
| `MATRIX_STORE_PATH` | `data/matrix_store` | хранилище ключей E2EE |
| `ANDROID_RELEASE_REPO` | `sukhanovai/monitoring` | репозиторий с релизами APK |
| `ANDROID_RELEASES_FROM_GITHUB` | `1` | определять версии каналов по GitHub Releases |
| `ANDROID_RELEASES_GITHUB_TOKEN` | — | токен GitHub (приватный репозиторий или лимиты API) |
| `ANDROID_DEFAULT_UPDATE_BRANCH` | `main` | канал обновления по умолчанию: `main` (стабильная) или `develop` (бета) |
| `ANDROID_APK_DOWNLOAD_URL` | `…/releases/latest/download/ComDone.apk` | запасная ссылка на APK |
