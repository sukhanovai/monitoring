# 🛰️ Monitoring: Telegram/TamTam-бот и платформа мониторинга серверов

**Monitoring** — это модульная система мониторинга инфраструктуры с управлением через Telegram/TamTam-ботов, CLI-проверками и опциональным веб‑интерфейсом. Проект умеет отслеживать доступность, ресурсы, бэкапы и события из почтовых уведомлений, а также отправлять алерты в чат.

## ✨ Ключевые возможности

- **Мониторинг доступности**: Ping, SSH, RDP, TCP-порты.  
- **Мониторинг ресурсов**: CPU, RAM, Disk, Load Average, Uptime (при доступности).  
- **Точечные проверки**: одиночный сервер, режимы `availability` и `resources`.  
- **Алерты и тихий режим**: гибкие пороги, расписание тишины.  
- **Отчёты**: утренние отчёты и статистика мониторинга.  
- **Бэкапы**: Proxmox, БД, ZFS (по e-mail уведомлениям).  
- **Почтовые события**: разбор почты и автоматизация по шаблонам.  
- **Расширения**: включаемые модули без изменений кода.  
- **CLI‑режим**: быстрые проверки без запуска бота.  
- **Веб‑панель**: запуск проверок и отчётов из браузера.  

## 🧱 Архитектура проекта

```
core/        — ядро мониторинга и маршрутизация задач
bot/         — Telegram/TamTam-боты, команды и меню
modules/     — фоновые модули (ресурсы, отчёты, почта)
extensions/ — расширения (бэкапы, веб, проверки)
config/      — конфигурация и значения по умолчанию
lib/         — служебные утилиты, логирование, алерты
```

## ✅ Требования

- **Python 3.9+**
- Linux (рекомендуется Ubuntu/Debian)
- Telegram Bot Token
- TamTam Bot Token (опционально)

Опционально:
- **Flask + WebSocket** — для веб‑панели.
- **pywinrm / wmi** — для мониторинга Windows.
- **xlrd** — для чтения файлов `.xls` (если нужны именно старые Excel‑файлы).
- **xlwt** — для записи файлов `.xls`.
- **openpyxl** — для чтения файлов `.xlsx`.

## ⚙️ Быстрый старт

### 1. Установка зависимостей
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### 2. Клонирование
```bash
git clone https://github.com/sukhanovai/monitoring.git
cd monitoring
```

### 3. Виртуальное окружение
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Базовая настройка

Минимальный набор настроек задаётся в `config/settings.py`:

```python
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_IDS = ["123456789"]
TAMTAM_TOKEN = "YOUR_TAMTAM_BOT_TOKEN"
TAMTAM_CHAT_IDS = ["<chat_id>"]
```

> После первого запуска настройки автоматически сохраняются в `data/settings.db`.  
> При наличии значений в БД они имеют приоритет над `config/settings.py`.

### 5. Получение Chat ID

Отправьте любое сообщение боту и выполните:
```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates"
```
Найдите:
```json
"chat": {"id": 123456789}
```


### 5.1 Получение TamTam Chat ID

1. Создайте бота через [@BotFather в TamTam](https://tt.me/BotFather).
2. Добавьте бота в нужный чат.
3. Выполните запрос к API:
```bash
curl "https://botapi.tamtam.chat/updates?access_token=<ВАШ_TAMTAM_ТОКЕН>"
```
4. Найдите `recipient.chat_id` и добавьте его в `TAMTAM_CHAT_IDS`.

### 6. Запуск

Основной мониторинг:
```bash
python main.py
```

Мониторинг почты (если используется):
```bash
python -m modules.improved_mail_monitor
```

## 🔧 Переменные окружения

- `MONITORING_BASE_DIR` — базовый каталог данных/логов (по умолчанию корень проекта).
- `MONITORING_MAILDIR_BASE` — путь к Maildir для почтового мониторинга (по умолчанию `/root/Maildir`).

## 🧪 CLI‑режим

Проверки без запуска бота:
```bash
python main.py --check availability
python main.py --check resources
python main.py --check targeted_checks --server 192.168.9.00 --mode resources
```

Дополнительно:
- `--server` — IP/имя сервера для точечной проверки.
- `--mode` — `availability` / `resources`.
- `--reload-servers` — перечитать список серверов перед проверкой.
- `--dry-run` — запуск без сети и Telegram.

## 🤖 Команды бота

Базовые:
- `/start` — главное меню.
- `/check` — быстрая проверка серверов.
- `/status` — статус мониторинга.
- `/servers` — список серверов.
- `/report` — утренний отчёт.
- `/stats` — статистика.
- `/control` — управление мониторингом.
- `/silent` — тихий режим.
- `/extensions` — управление расширениями.
- `/settings` — управление настройками.
- `/check_server` — проверка одного сервера.
- `/check_res` — ресурсы одного сервера.

TamTam (текстовые команды):
- `/help`, `/status`, `/check`, `/resources`.
- `/check_server <IP|имя>`.
- `/monitor_on`, `/monitor_off`.
- `/silent_on`, `/silent_off`.

Команды бэкапов (при активных расширениях):
- `/backup`, `/backup_search`, `/backup_help` — Proxmox.
- `/db_backups` — бэкапы БД.

## 🧩 Расширения

Расширения включаются через конфигурацию и меню бота. Пример структуры:

```python
AVAILABLE_EXTENSIONS = {
    "backup_monitor": {"name": "📊 Мониторинг бэкапов Proxmox", "enabled_by_default": True},
    "database_backup_monitor": {"name": "🗃️ Мониторинг бэкапов БД", "enabled_by_default": True},
    "zfs_monitor": {"name": "🧊 Мониторинг ZFS", "enabled_by_default": True},
    "resource_monitor": {"name": "💻 Мониторинг ресурсов", "enabled_by_default": True},
    "web_interface": {"name": "🌐 Веб-интерфейс", "enabled_by_default": True},
    "email_processor": {"name": "📧 Обработка почты", "enabled_by_default": True}
}
```


## 📱 Android-клиент

В репозитории добавлен Android-проект `android-client/` (Kotlin + Compose), который работает с BFF API по адресу `https://api.202020.ru:8443` и не ломает существующий Telegram-канал управления.

Подробная пошаговая инструкция для запуска и доработки: `docs/android_mobile_app.md`.

### Публикация APK как prerelease только для `develop`

Из терминала Android Studio (PowerShell) можно запустить один скрипт:

```powershell
./scripts/publish_android_prerelease.ps1
```

Что делает скрипт:
- проверяет, что текущая ветка — `develop`;
- собирает `release` APK через Gradle;
- автоматически выбирает APK из `app/build/outputs/apk/release` (`app-release.apk`, `app-release-unsigned.apk` или последний `*.apk`);
- публикует/обновляет GitHub prerelease с тегом `v<версия>-develop`;
- загружает APK в релиз, не затрагивая стабильный релиз в `main`.

Требования:
- либо установлен `gh` (GitHub CLI) и выполнен `gh auth login`;
- либо задан `GH_TOKEN`/`GITHUB_TOKEN` (fallback через GitHub API без `gh`);
- права на создание релизов в репозитории.

Примечание по сборке Android Studio:
- для Kotlin 2.x и включённого Compose в модуле подключён `org.jetbrains.kotlin.plugin.compose`; если после pull IDE ругается на Compose compiler plugin — обновите Gradle Sync и пересоберите проект.

Важно:
- по умолчанию скрипт требует чистое рабочее дерево Git (иначе попросит сделать commit/stash);
- если нужно автоматически спрятать локальные изменения на время релиза и вернуть их обратно, используйте: `./scripts/publish_android_prerelease.ps1 -AutoStashDirty`;
- при необходимости можно форсировать запуск с локальными изменениями без stash: `./scripts/publish_android_prerelease.ps1 -AllowDirty`.

### Как полностью откатить ветку к `origin/develop` и начать заново

Если ветка заехала в конфликтный ад, можно одним скриптом:
- сохранить backup patch текущих изменений;
- сбросить ветку к `origin/develop`;
- очистить untracked файлы.

```powershell
./scripts/recover_local_branch.ps1
```

После этого ветка будет как `origin/develop`, а backup patch сохранится в `artifacts/`.
Если нужно вернуть кусок старых правок — накатывай patch через `git am`.

### Как перенести изменения из Codex в локальный репозиторий

Если в окружении Codex не настроен `origin`/push в GitHub, изменения всё равно можно перенести через patch.

Экспорт последнего коммита в patch:

```powershell
./scripts/export_codex_changes.ps1 -LastCommits 1
```

Экспорт диапазона коммитов:

```powershell
./scripts/export_codex_changes.ps1 -FromRef HEAD~3 -ToRef HEAD
```

Дальше на твоей локальной машине (в реальном репозитории с настроенным origin):

```bash
git am < /path/to/codex-changes-YYYYMMDD-HHMMSS.patch
git push origin <your-branch>
```

### Безопасный `git pull` при локальных изменениях

Если PR в GitHub пишет `This branch has conflicts that must be resolved`, можно прогнать авто-разруливание конфликтов по "шумным" version-файлам (берётся версия из `develop`):

```powershell
./scripts/resolve_pr_conflicts.ps1
```

Скрипт:
- делает `git fetch origin develop`;
- запускает `git merge origin/develop`;
- для набора частоконфликтных version-файлов автоматически берёт сторону `develop` (`--theirs`);
- оставляет ручное разрешение только для действительно содержательных конфликтов.

Если `git pull` падает с ошибкой `Please commit your changes or stash them before you merge`, используйте helper-скрипт:

```powershell
./scripts/git_safe_pull.ps1 -AutoDetectAndroidClientConfigOnly
```

Если этого файла локально ещё нет, сначала подтяни актуальный `develop` из GitHub (или забери файл `scripts/git_safe_pull.ps1` из PR), а потом запускай команду.

Это особенно полезно для типового кейса из Android Studio, когда локально изменён только `android-client/gradle.properties` (или другие целевые Android-конфиги).

Скрипт делает:
- авто-детект: если изменены только Android-конфиги (`build.gradle.kts`, `gradle.properties`, `gradle-wrapper.properties`) — использует безопасный backup/restore без `stash pop`;
- если есть изменения и в других файлах — использует обычный временный stash;
- выполняет `git pull --rebase origin develop`;
- возвращает локальные изменения после pull.

Если нужно принудительно отбросить локальные изменения только в Android-конфигах и взять удалённую версию, используйте:

```powershell
./scripts/git_safe_pull.ps1 -OnlyAndroidClientConfig -ResetAndroidClientConfigToRemote
```

Опции:
- `-NoRebase` — выполнить обычный `git pull` без rebase;
- `-KeepStash` — не делать `stash pop` автоматически;
- `-OnlyAndroidClientConfig` — временно сохраняет и восстанавливает только `android-client/build.gradle.kts`, `android-client/gradle.properties` и `android-client/gradle/wrapper/gradle-wrapper.properties` (без `stash pop` merge для этих файлов).
- `-ResetAndroidClientConfigToRemote` — в режиме `-OnlyAndroidClientConfig` перед pull отбрасывает локальные изменения в этих файлах до состояния текущей ветки (`HEAD`) и затем подтягивает актуальную версию из remote через `git pull` (локальные изменения будут отброшены). Также умеет обработать состояние `unmerged` для этих же файлов (после неудачного `stash pop`) и снять блокировку перед pull.
- `-HardResetToRemote` — полностью отбрасывает все локальные изменения и untracked-файлы (`git fetch`, `git reset --hard <remote>/<branch>`, `git clean -fd`), чтобы быстро получить ровно состояние GitHub-ветки.

Быстрый ручной запуск для твоего кейса:
```powershell
./scripts/git_safe_pull.ps1 -OnlyAndroidClientConfig
```


Если хочешь просто **забить на локальные правки** Android-конфигов и взять версию из GitHub (самый простой путь):
```powershell
./scripts/git_safe_pull.ps1 -OnlyAndroidClientConfig -ResetAndroidClientConfigToRemote
```

Если вообще похуй на любые локальные изменения в репозитории и нужно просто привести проект к состоянию GitHub `develop` одной командой:
```powershell
./scripts/git_safe_pull.ps1 -HardResetToRemote
```

Если хочешь сделать полный reset этих файлов вручную без helper-скрипта (отбрасываем локальные правки и затем тянем GitHub-версию через pull):
```powershell
git restore --staged --worktree -- android-client/build.gradle.kts android-client/gradle.properties android-client/gradle/wrapper/gradle-wrapper.properties
git pull --rebase origin develop
```

Техническая деталь: Android-версия (`versionCode`/`versionName`) вынесена в `android-client/gradle.properties`, чтобы снизить шанс конфликтов в `android-client/app/build.gradle.kts` при обычном `git pull`.

## 🌐 Веб‑интерфейс

Если включено расширение `web_interface`, панель будет доступна по адресу:

```
http://<YOUR_IP>:5000
```

В интерфейсе можно запускать проверку ресурсов и формировать утренний отчёт.

## 🚀 Production‑развёртывание (systemd)

### 1. Основной сервис

Создайте unit:
```bash
sudo nano /etc/systemd/system/server-monitor.service
```

Пример (под текущий production-профиль с `proxychains4`):
```ini
[Unit]
Description=Server Monitoring Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring
Environment=PYTHONUNBUFFERED=1
Environment="MOBILE_DEFAULT_TOKEN=CHANGE_ME_STRONG_BOOTSTRAP_TOKEN"
Environment="MOBILE_SESSION_TOKEN_TTL_SEC=0"

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/usr/bin/proxychains4 -q /opt/monitoring/venv/bin/python /opt/monitoring/main.py
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

Альтернативный вариант без `proxychains4`:
```ini
[Unit]
Description=Server Monitoring Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring
Environment=PYTHONUNBUFFERED=1
Environment="MOBILE_DEFAULT_TOKEN=CHANGE_ME_STRONG_BOOTSTRAP_TOKEN"
Environment="MOBILE_SESSION_TOKEN_TTL_SEC=0"

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

Пояснение по Android-токенам:
- `MOBILE_DEFAULT_TOKEN` — bootstrap-токен для первичной авторизации Android-клиента.
- `MOBILE_SESSION_TOKEN_TTL_SEC` — TTL рабочих токенов, которые сервер выдает приложению после bootstrap:
  - `0` = бессрочно,
  - `>0` = время жизни в секундах.

Сгенерировать `MOBILE_DEFAULT_TOKEN` можно командой:
```bash
python scripts/generate_mobile_default_token.py
```

Рекомендуемый поток:
1. В приложении в поле Bearer токена вставляется `MOBILE_DEFAULT_TOKEN`.
2. При сохранении токена Android вызывает `POST /v1/auth/token`.
3. Сервер выдает новый рабочий токен, сохраняет его в `settings.db` и приложение сохраняет его локально.
4. Далее используется только рабочий токен.

Перевыпуск токена (например, после переустановки приложения):
```bash
curl -k -X POST "https://<host>/v1/auth/token/reissue" \
  -H "Authorization: Bearer <MOBILE_DEFAULT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"android-device-1","subject":"android-client","reissue":true}'
```

Активируйте:
```bash
sudo systemctl daemon-reload
sudo systemctl enable server-monitor
sudo systemctl start server-monitor
```

### 2. Почтовый монитор (опционально)

Если используется почтовый модуль:

```bash
sudo nano /etc/systemd/system/mail-monitor.service
```

```ini
[Unit]
Description=Proxmox Backup Mail Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/usr/bin/proxychains4 -q /opt/monitoring/venv/bin/python /opt/monitoring/modules/mail_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

Альтернативный вариант без `proxychains4`:
```ini
[Unit]
Description=Proxmox Backup Mail Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/monitoring
Environment=PYTHONPATH=/opt/monitoring

ExecStartPre=/bin/mkdir -p /run/samba
ExecStartPre=/bin/chmod 0755 /run/samba

ExecStart=/opt/monitoring/venv/bin/python /opt/monitoring/modules/mail_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

ProtectSystem=strict
ReadWritePaths=/opt/monitoring /opt/monitoring/data /root/.ssh /run/samba

[Install]
WantedBy=multi-user.target
```

Активация:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mail-monitor
sudo systemctl start mail-monitor
```

### 3. Проверка статуса
```bash
systemctl status server-monitor.service
systemctl status mail-monitor.service
```

## ✅ Диагностика

Проверка конфигурации:
```bash
python -c "import config; print('✅ Конфигурация загружена')"
```

Проверка зависимостей:
```bash
python -c "import flask, telegram, paramiko; print('✅ Зависимости OK')"
```

## 📄 Лицензия

MIT License — подробнее в [LICENSE](LICENSE).

## Versioning

This project uses Semantic Versioning (SemVer): `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible API/behavior changes.
- `MINOR`: backward-compatible features.
- `PATCH`: backward-compatible fixes.

Release notes are tracked in `CHANGELOG.md`.
