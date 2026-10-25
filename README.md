# 🛰️ ComDone: Telegram/Matrix-бот и платформа мониторинга серверов

**ComDone** — это модульная система мониторинга инфраструктуры (communication done, контроль done) с управлением через Telegram/Matrix-ботов, CLI-проверками и опциональным веб‑интерфейсом. Проект умеет отслеживать доступность, ресурсы, бэкапы и события из почтовых уведомлений, а также отправлять алерты в чат.

## ✨ Ключевые возможности

- **Мониторинг доступности**: Ping, SSH, RDP, TCP-порты.  
- **Мониторинг ресурсов**: CPU, RAM, Disk, Load Average, Uptime (при доступности).  
- **Точечные проверки**: одиночный сервер, режимы `availability` и `resources`.  
- **Алерты и тихий режим**: гибкие пороги, расписание тишины.  
- **Отчёты**: утренние отчёты и статистика мониторинга.  
- **Бэкапы**: Proxmox, БД, ZFS (по e-mail уведомлениям).  
- **Почтовые события**: разбор почты и автоматизация по шаблонам.  
- **Расширения**: включаемые модули без изменений кода.  
- **Многопользовательский режим**: у каждого пользователя свой состав отчёта, свои подписки на оповещения и свой канал обмена с ботом при общих настройках сбора данных (`docs/multi_user.md`).  
- **CLI‑режим**: быстрые проверки без запуска бота.  
- **Веб‑панель**: запуск проверок и отчётов из браузера.  
- **Android-приложение ComDone**: оперативный центр, отчёты, настройки и уведомления на телефоне.  

## 🧱 Архитектура проекта

```
core/        — ядро мониторинга и маршрутизация задач
bot/         — Telegram/Matrix-боты, команды и меню
modules/     — фоновые модули (ресурсы, отчёты, почта)
extensions/ — расширения (бэкапы, веб, проверки)
config/      — конфигурация и значения по умолчанию
lib/         — служебные утилиты, логирование, алерты
```

## ✅ Требования

- Linux (рекомендуется Debian 12 / Ubuntu 22.04+)
- **Python 3.10–3.12** (рекомендуется 3.11)
- Telegram Bot Token
- Для Android-приложения — доменное имя и TLS-сертификат
- Matrix-аккаунт бота — опционально

## 🚀 Установка

Полная пошаговая инструкция: установка, настройка, systemd, обратный прокси
и TLS, Android, Matrix, обновление (в том числе с 8.x), бэкап и откат —
**[docs/deployment.md](docs/deployment.md)**.

Коротко:

```bash
sudo git clone https://github.com/sukhanovai/monitoring.git /opt/monitoring
cd /opt/monitoring
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
sudo venv/bin/pip install -r requirements-matrix.txt   # только если нужен Matrix
```

Затем задайте токен бота и чаты ([раздел 4](docs/deployment.md#4-первичная-настройка))
и запустите сервис ([раздел 5](docs/deployment.md#5-запуск-как-сервис-systemd)).

## 🔧 Переменные окружения

Основные: `MONITORING_BASE_DIR`, `MONITORING_MAILDIR_BASE`,
`MOBILE_DEFAULT_TOKEN`, `MATRIX_*`, `ANDROID_*`. Полный справочник —
[docs/deployment.md, раздел 13](docs/deployment.md#13-справочник-переменных-окружения).

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

Matrix command-bot (текстовые команды, паритет с Telegram):
- `!status`, `!resources`, `!report`, `!servers`.
- `!check <IP|имя>`, `!res <IP|имя>`.
- `!pause`, `!resume`, `!silent`, `!loud`, `!auto`.
- `!settings` — просмотр и изменение настроек.
- `!me` — личные настройки доставки, `!users` — реестр пользователей (админ).

Команды бэкапов (при активных расширениях):
- `/backup`, `/backup_search`, `/backup_help` — Proxmox.
- `/db_backups` — бэкапы БД.

## 👥 Пользователи и персональные отчёты

Данные собираются один раз для всей системы, а доставляются каждому по его
настройкам. У пользователя есть свой канал обмена с ботом (Telegram-чат,
Matrix-комната, устройство Android, логин веба) и личные настройки:

- состав утреннего/ручного отчёта — какие расширения в него включать;
- получать ли отчёт и оповещения, какие уровни (критические/предупреждения/
  информационные) и категории (доступность, ресурсы, конкретные расширения);
- личные тихие часы (критические сообщения приходят всегда).

Общие настройки сбора данных (серверы, интервалы, паттерны писем, учётные
данные, включённость расширений) остаются едиными и персонализации не
подлежат.

Где настраивается:

- Telegram: `⚙️ Настройки` → `🔔 Мои оповещения`, `🗒️ Состав отчёта`,
  `👥 Пользователи` (админ, там же «➕ Привязать этот чат»).
- Matrix: `!me`, `!report config`, `!users add|link|enable|disable|delete`.
- Android: `⚙️ Настройки` → `🔔 Мои оповещения` (отчёт, уровни, категории,
  тихие часы) и карточка «📱 Это устройство» для привязки телефона
  к пользователю; `🗒️ Состав отчёта` подписан владельцем.
- API: `GET /v1/me`, `PATCH /v1/me/notifications`,
  `GET|PATCH /v1/settings/report`, `GET|POST /v1/users`,
  `POST|DELETE /v1/users/<id>/channels`.

Обновление с однопользовательской конфигурации проходит без ручных шагов:
существующие `CHAT_IDS`, `MATRIX_ROOM_ID` и `WEB_LOGIN` автоматически
становятся каналами администратора. Подробности — `docs/multi_user.md`.

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

## 🟩 Matrix

Бот принимает команды и шлёт те же уведомления, что и в Telegram, в том числе
в зашифрованные комнаты. Настройка —
[docs/deployment.md, раздел 8](docs/deployment.md#8-matrix-опционально),
эксплуатация и список команд — [docs/matrix_bot_management.md](docs/matrix_bot_management.md).

> Если `MATRIX_*` не заданы, Matrix-канал отключён, Telegram работает как обычно.

## 📱 Android-приложение ComDone

Последняя стабильная версия:
**[ComDone.apk](https://github.com/sukhanovai/monitoring/releases/latest/download/ComDone.apk)**
(Android 8.0+).

Установка, подключение к серверу и токены —
[docs/deployment.md, раздел 7](docs/deployment.md#7-android-приложение).
Обновления ставятся из самого приложения (**Настройки → Обновление**,
каналы «Стабильная» и «Бета») поверх установленной версии, настройки
сохраняются.

## 🌐 Веб‑интерфейс

Если включено расширение `web_interface`, панель и API для Android доступны
на порту `5000` (наружу — через обратный прокси с TLS, см.
[docs/deployment.md, раздел 6](docs/deployment.md#6-веб-панель-и-api-обратный-прокси-и-tls)).
В панели можно запускать проверки, смотреть ресурсы и формировать отчёты.

## 📚 Документация

| Документ | О чём |
|---|---|
| [deployment.md](docs/deployment.md) | установка, настройка, обновление, бэкап, диагностика |
| [multi_user.md](docs/multi_user.md) | пользователи, личные оповещения и состав отчёта |
| [matrix_bot_management.md](docs/matrix_bot_management.md) | Matrix-бот |
| [ids_cert_monitor.md](docs/ids_cert_monitor.md) | IDS контейнеров и сертификаты почты |
| [tls_cert_monitor.md](docs/tls_cert_monitor.md) | мониторинг TLS-сертификатов |
| [nas_transfer_monitor.md](docs/nas_transfer_monitor.md) | перенос бэкапов на NAS |
| [config_console_backup_monitor.md](docs/config_console_backup_monitor.md) | бэкапы конфигураций |
| [zfs_data_flow.md](docs/zfs_data_flow.md) | мониторинг ZFS |
| [development.md](docs/development.md) | для разработчиков: ветки, сборка, выпуск релизов |

## 📄 Лицензия

MIT License — подробнее в [LICENSE](LICENSE).

## Versioning

This project uses Semantic Versioning (SemVer): `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible API/behavior changes.
- `MINOR`: backward-compatible features.
- `PATCH`: backward-compatible fixes.

Release notes are tracked in `CHANGELOG.md`.
