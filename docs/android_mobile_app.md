Status: Draft
Owner: Александр Суханов
Last updated: 2026-02-11

# Android-приложение для Monitoring (без отказа от Telegram)

Этот файл — практическая инструкция для одного исполнителя (без опыта Android), чтобы поднять мобильный клиент и не сломать существующий Telegram-бот.

## 0. Что уже сделано в репозитории

Добавлен новый Android-проект в каталоге `android-client/`:

- Kotlin + Jetpack Compose;
- подключение к `https://api.202020.ru:8443`;
- экраны:
  - сохранение Bearer-токена;
  - получение статуса доступности серверов;
  - отправка control action (`pause/resume/report/quiet`);
  - изменение настроек мониторинга (`check_interval_sec`, `timeout_sec`, `max_downtime_sec`).

Telegram-функционал бэкенда не тронут: мобильное приложение работает через BFF API поверх интернета и не вмешивается в код Telegram-бота.

---

## 1. Что установить на рабочий ноутбук/ПК

### Обязательно

1. **Git**
   - Windows: https://git-scm.com/download/win
   - Linux: `sudo apt install git`
2. **Android Studio (Hedgehog/Koala и новее)**
   - https://developer.android.com/studio
3. **Android SDK Platform 34**
4. **Android Emulator** (если нет физического устройства)
5. **JDK не ставим отдельно**, Android Studio принесёт свой JetBrains Runtime.

### Опционально, но полезно

- GitHub Desktop (если неудобен терминал);
- ADB USB Driver (для Windows и реального телефона).

---

## 2. Первый запуск Android Studio (один раз)

1. Открыть Android Studio.
2. Перейти в **More Actions -> SDK Manager**.
3. Убедиться, что установлены:
   - `Android SDK Platform 34`;
   - `Android SDK Build-Tools`;
   - `Android SDK Platform-Tools`;
   - `Android Emulator`.
4. В **Settings -> Build, Execution, Deployment -> Gradle**:
   - Gradle JDK = встроенный JDK (обычно `jbr-17`);
   - Build and run using = Gradle.

---

## 3. Как забрать код через GitHub (подробно)

Ниже — два рабочих сценария. Если ты просто запускаешь проект у себя, бери **Вариант A**.

### Вариант A: просто скачать и запустить (без форка)

```bash
git clone https://github.com/sukhanovai/monitoring.git
cd monitoring
git branch
```

Что проверить после клонирования:

1. В выводе `git branch` есть активная ветка (обычно `main` или `master`).
2. В корне есть папка `android-client/`.
3. Внутри `android-client/` есть файлы `settings.gradle.kts` и `app/build.gradle.kts`.

Быстрая проверка командами:

```bash
ls
ls android-client
```

### Вариант B: если хочешь коммитить в свой GitHub (правильный путь для доработок)

1. Сделай Fork репозитория в своём GitHub-аккаунте (кнопка **Fork** в интерфейсе GitHub).
2. Клонируй **свой** форк:

```bash
git clone https://github.com/<твой_логин>/monitoring.git
cd monitoring
```

3. Добавь оригинальный репозиторий как `upstream` (чтобы подтягивать свежие изменения):

```bash
git remote add upstream https://github.com/sukhanovai/monitoring.git
git remote -v
```

4. Создай отдельную рабочую ветку под Android-изменения:

```bash
git checkout -b feature/android-mobile
```

### Как жить с моделью `main` / `develop` и Android-разработкой

Твоя схема (`main` = стабильные релизы, `develop` = основная разработка) — нормальная и рабочая.

**Короткий ответ:**
- отдельный **fork не обязателен**, если ты один и имеешь доступ в основной репозиторий;
- отдельная **ветка под Android обязательна** (`feature/android-mobile`) — это сильно упрощает жизнь.

Рекомендуемый поток без лишнего геморроя:

1. Базовая ветка для Android-фичи: `develop`.
2. Работаешь в `feature/android-mobile`.
3. Регулярно подтягиваешь изменения из `develop` (rebase или merge).
4. Когда Android-кусок готов — вливаешь его в `develop`.
5. В `main` попадает только проверенный релиз через merge из `develop`.

Команды для синка Android-ветки с `develop`:

```bash
git checkout develop
git pull origin develop
git checkout feature/android-mobile
git rebase develop
```

Если rebase пока страшновато, можно безопаснее через merge:

```bash
git checkout feature/android-mobile
git merge develop
```

### Почему ветку не видно в GitHub и что делать с `no upstream branch`

Это частая история: ты создал ветку локально, но **ещё ни разу не запушил её в origin**.
Пока не сделаешь первый push с установкой upstream, GitHub про эту ветку не знает.

Ошибка:

```text
fatal: The current branch feature/android-mobile has no upstream branch.
```

Лечение (один раз для новой ветки):

```bash
git push --set-upstream origin feature/android-mobile
```

После этого будет работать обычный короткий push:

```bash
git push
```

Проверка, что всё ок:

```bash
git branch -vv
git remote -v
```

В `git branch -vv` у ветки должно появиться что-то вроде `[origin/feature/android-mobile]`.

Чтобы Git сам ставил upstream для новых веток по умолчанию, включи один раз:

```bash
git config --global push.autoSetupRemote true
```

И ещё важный момент, из-за которого «в GitHub пусто»: если в ветке нет новых коммитов относительно `develop`, то даже после push диффа не будет. Проверь:

```bash
git status
git log --oneline --decorate --graph -20
```

---

### Когда всё-таки нужен отдельный fork под Android

Делать Android в отдельном fork имеет смысл, если:

1. хочешь полностью изолировать эксперименты и не светить сырой код в основном репо;
2. будут внешние разработчики без прямого доступа;
3. нужно отдельное управление правами/CI/секретами именно для мобильного клиента.

Минус отдельного форка: надо чаще синкать `develop`, иначе начинаются конфликты и ебля с интеграцией.

Практично для твоего кейса (один разработчик):

- держи всё в одном репозитории;
- Android делай в ветке `feature/android-mobile` от `develop`;
- параллельные доработки backend в `develop` регулярно подтягивай в Android-ветку;
- релизный срез в `main` делай только после smoke/regression проверки.

---

### Как открыть проект в Android Studio (важный момент)

Открывать нужно **папку `android-client`**, а не весь монорепо:

1. Android Studio -> **Open**.
2. Выбрать путь вида:
   - Linux/macOS: `/home/<user>/.../monitoring/android-client`
   - Windows: `C:\Users\<user>\...\monitoring\android-client`
3. Нажать **Trust Project** (если спросит).
4. Дождаться Sync Gradle (первый sync может занять 5–15 минут).

Если открыть не `android-client`, а корень Python-проекта, Android Studio может не увидеть Android-модуль — и дальше начнётся ебаный цирк с «почему не запускается». Поэтому открываем строго `android-client`.

---

## 4. Запуск приложения

### Вариант А: эмулятор

1. **Device Manager -> Create Device**.
2. Выбрать Pixel + Android 14 (API 34).
3. Нажать **Run** (зелёный треугольник).

### Вариант Б: живой Android-телефон

1. В телефоне включить Developer Options + USB Debugging.
2. Подключить по USB.
3. Выбрать устройство в Android Studio.
4. Нажать **Run**.

---

## 5. Как подключить к вашему API

В приложении уже зашит base URL:

- `https://api.202020.ru:8443/`

Что нужно сделать в UI:

1. Получить рабочий Bearer-токен на вашей стороне (из auth-сервиса/BFF).

### Быстрый способ найти endpoint выдачи токена

Если запускаешь скрипт **на самом сервере**, используй локальный/внутренний адрес:

```bash
./scripts/auth_token_probe.sh --insecure https://localhost <login> <password>
# или
./scripts/auth_token_probe.sh --insecure https://192.168.20.2 <login> <password>
```

Внешний URL `https://api.202020.ru:8443` нужен в основном для клиентов извне сервера.

Если у сервера self-signed сертификат, добавляй `--insecure` (или `-k`), иначе `curl` упирается в `SSL certificate problem`.

### Практический сценарий: токен для ветки `android-mobile`, когда `develop` стоит за NAT

Если backend в `develop` не торчит наружу напрямую, получай токен из консоли самого сервера, где поднят проект.

1. Подключись по SSH к серверу и перейди в рабочую копию проекта:

```bash
ssh <user>@<server>
cd /path/to/monitoring
```

2. Проверь, что ты на актуальном `develop` (Android-клиент в своей ветке использует тот же API):

```bash
git checkout develop
git pull origin develop
```

3. Запусти discovery токен-эндпоинта через локальный адрес сервера:

```bash
./scripts/auth_token_probe.sh --insecure https://localhost <login> <password>
```

4. Если трафик идёт только через reverse proxy с обязательным `Host`, пробуй так:

```bash
./scripts/auth_token_probe.sh --insecure --host api.202020.ru https://localhost <login> <password>
```

5. Если API висит под префиксом (`/api`, `/bff` и т.п.), добавь `--prefix`:

```bash
./scripts/auth_token_probe.sh --insecure --host api.202020.ru --prefix /api https://localhost <login> <password>
```

6. Скопируй полученный `access_token` и вставь в Android-приложение в поле Bearer Token.

Мини-проверка, что токен живой (подставь свой токен):

```bash
curl -k -H "Authorization: Bearer <access_token>" https://localhost/api/v1/monitor/status
```

Если этот запрос возвращает 200/JSON со статусами, токен норм и его можно использовать в ветке `feature/android-mobile`.


### Если `login/password` нет вообще (и ты сам админ сервера)

Если видишь только Apache-страницу помощи (`/ -> 200`, а `/v1/...` и `/api/...` -> 404), проблема не в токене, а в роутинге до BFF.
В таком состоянии логин не заработает вообще — сначала нужно найти, где реально крутится API.

1. Найди, кто слушает порты и есть ли локальный backend-порт (5000/8000/8080/9000/8443):

```bash
ss -lntp | grep -E '(:443|:8443|:5000|:8000|:8080|:9000)'
```

2. Посмотри vhost и proxy-настройки Apache/Nginx (ищем `ProxyPass`, `proxy_pass`, `RewriteRule`):

```bash
apache2ctl -S
grep -R "ProxyPass\|RewriteRule\|api.202020.ru" /etc/apache2/sites-enabled /etc/apache2/sites-available
nginx -T 2>/dev/null | grep -E "server_name|proxy_pass|api.202020.ru"
```

3. Если backend запущен в Docker/Compose — найди сервис API и его внутренний порт:

```bash
docker ps --format 'table {{.Names}}	{{.Ports}}'
docker compose ps
```

4. Когда нашёл локальный API-порт, проверь его напрямую (минуя внешний reverse proxy):

```bash
./scripts/auth_token_probe.sh --insecure https://localhost:<API_PORT>
./scripts/auth_token_probe.sh --insecure --prefix /api https://localhost:<API_PORT>
```

5. Если на прямом порту есть не-404 ответы по `/v1/...` или `/api/v1/...`, значит ты попал в BFF.
Дальше уже нужно либо получить тестовую учётку, либо выпустить сервисный токен в том auth-сервисе, который этот BFF использует.

#### Что делать прямо сейчас по твоему логу (коротко и без гаданий)

По твоему выводу сейчас факт такой: `https://localhost:443` отдаёт не API, а страницу помощи Apache.
Значит, endpoint токена на этом URL не появится, хоть обдолбись `--host/--prefix`.

Сделай в таком порядке:

```bash
# 1) Ищем живой локальный API-порт
ss -lntp | grep -E '(:443|:8443|:5000|:8000|:8080|:9000)'

# 2) Проверяем, куда Apache должен проксировать api.202020.ru
apache2ctl -S
grep -R "api.202020.ru\|ProxyPass\|RewriteRule\|ProxyPassReverse" /etc/apache2/sites-enabled /etc/apache2/sites-available

# 3) Если используется Docker — ищем контейнер API и его порт
docker ps --format 'table {{.Names}}	{{.Ports}}'
```

Если в конфиге нет `ProxyPass`/`RewriteRule` на `/v1` или `/api` к backend-порту — проблема найдена: reverse proxy просто не прокидывает API.

После правки proxy-конфига проверка должна стать такой (пример):

```bash
curl -k -I -H "Host: api.202020.ru" https://localhost/v1/monitoring/availability?scope=all
# ожидаемо: не 404 от Apache (может быть 200/401/403 — это уже живой API)
```

Только после этого имеет смысл добывать токен (через login endpoint или сервисную учётку auth-сервиса).

#### Отдельно по твоему выводу `apache2ctl -S`

У тебя в `*:443` есть только vhost `help` (`help-ssl.conf`), а `api.202020.ru` в конфиге не видно.
Это и есть корень проблемы: Apache обслуживает другой проект из `/var/www/html`, поэтому `/v1/...` и `/api/...` закономерно 404.

Минимально что надо сделать:

```bash
# 1) Создать/добавить SSL vhost для API-домена (пример)
cat >/etc/apache2/sites-available/api.202020.ru-ssl.conf <<'EOF'
<VirtualHost *:443>
    ServerName api.202020.ru

    SSLEngine on
    SSLCertificateFile /path/to/fullchain.pem
    SSLCertificateKeyFile /path/to/privkey.pem

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/
</VirtualHost>
EOF

# 2) Включить модули и сайт
apache2enmod proxy proxy_http ssl headers rewrite
apache2ensite api.202020.ru-ssl.conf
apache2ctl configtest && systemctl reload apache2

# 3) Проверить, что vhost появился
apache2ctl -S | grep api.202020.ru
```

После этого снова проверяй:

```bash
curl -k -I -H "Host: api.202020.ru" https://localhost/v1/monitoring/availability?scope=all
```

Если уже не Apache 404, значит ты наконец попал в BFF и можно переходить к получению токена.

### Схема NAT + отдельный reverse proxy (как у тебя) и получение токена с сервера проекта

Твоя целевая схема:
- backend/BFF крутится на **сервере проекта** во внутренней сети;
- отдельный **reverse proxy** в той же сети принимает `api.202020.ru:8443`;
- SSL-сертификат висит на reverse proxy;
- токен нужно получить из консоли сервера проекта.

Рабочая логика в таком сетапе:
1. На сервере проекта проверяешь, что сам BFF живой на локальном/internal порту.
2. Отдельно проверяешь, что с сервера проекта можно попасть в reverse proxy по `api.202020.ru:8443` (или через внутренний IP proxy + Host/SNI).
3. Токен запрашиваешь у того endpoint, который реально отвечает не Apache-страницей, а API/BFF.

Команды (по порядку):

```bash
# 1) Найти внутренний порт BFF на сервере проекта
ss -lntp | grep -E '(:5000|:8000|:8080|:8443|:9000)'

# 2) Пробный discovery напрямую в backend (без reverse proxy)
./scripts/auth_token_probe.sh --insecure https://localhost:<BFF_PORT>
./scripts/auth_token_probe.sh --insecure --prefix /api https://localhost:<BFF_PORT>

# 3) Проверка reverse proxy из консоли сервера проекта (если DNS резолвит наружу криво)
# подставь внутренний IP reverse proxy
curl -k -I --resolve api.202020.ru:8443:<REVERSE_PROXY_LAN_IP> https://api.202020.ru:8443/

# 4) Discovery через reverse proxy (с принудительным resolve)
./scripts/auth_token_probe.sh --insecure https://api.202020.ru:8443
# при необходимости:
./scripts/auth_token_probe.sh --insecure --prefix /api https://api.202020.ru:8443
```

Если в шаге 4 снова видишь HTML/Apache 404 — значит proxy не прокидывает нужный route до BFF.
Если получаешь API-ответы (хотя бы 401/403 на auth/monitoring), маршрут живой и можно получать токен.

Практично: сначала добейся **не-404 Apache**, потом уже ебись с кредами/token payload.

#### Расшифровка именно твоего текущего вывода

По твоим новым проверкам видно уже точнее:
- `http://192.168.20.2:5000/` открывает веб-интерфейс бота, но падает с ошибкой `can't compare offset-naive and offset-aware datetimes`;
- `http://192.168.20.2:5000/api/v1/` возвращает `Not Found`;
- `http://192.168.20.2:80/` — вообще другой LAN-сайт, не относящийся к проекту.

Итог: процесс на `:5000` сейчас не даёт нужный mobile/BFF API маршрут. Поэтому тупо прокинуть `/v1` на `:5000` — хуёвая идея, токен это не вылечит.

Что делать правильно перед правками Nginx:

```bash
# 1) Убедиться, какие роуты реально есть у python-сервиса на :5000
curl -sS http://192.168.20.2:5000/ | head
curl -sS -o /dev/null -w "%{http_code}\n" http://192.168.20.2:5000/v1/monitoring/availability?scope=all
curl -sS -o /dev/null -w "%{http_code}\n" http://192.168.20.2:5000/api/v1/monitoring/availability?scope=all

# 2) Посмотреть логи python-процесса (ошибка datetime может ломать и API-ветку)
journalctl -u <service_name> -n 200 --no-pager
# или, если запускается руками/через screen/supervisor/docker, смотреть соответствующие логи
```

Если на прямом `:5000` нет валидного API endpoint'а (получаешь 404/500), сначала нужно починить backend-приложение,
а уже потом настраивать reverse proxy.

Минимальный критерий "можно идти в Nginx":
- прямой запрос на внутренний endpoint должен давать API-ответ (200/401/403/JSON), а не `Not Found`/HTML-страницу.

Только после этого на reverse proxy настраиваешь `location` на **реально существующий** route backend'а (а не «наугад /v1»),
делаешь `nginx -t && systemctl reload nginx` и повторно проверяешь `auth_token_probe.sh` через `https://api.202020.ru:8443`.

#### Текущий статус по твоим последним командам

По твоему `ps` и `journalctl` картина такая:
- запущен `server-monitor.service` с процессом `/opt/monitoring/venv/bin/python /opt/monitoring/main.py`;
- `/` отдаёт `200`, но в логах есть `❌ Ошибка получения статистики: No module named 'extensions.server_list'`;
- `/v1/monitoring/availability` и `/api/v1/monitoring/availability` на `:5000` стабильно дают `404`.

Это значит, что текущий инстанс — рабочий бот/веб-морда, но не готовый mobile BFF API.
Поэтому токен сейчас не получить: endpoint'а для Android тупо нет в этом рантайме.

Что делать дальше по-быстрому:

```bash
# 1) Проверить, какая ревизия и ветка реально крутится на сервере
cd /opt/monitoring
git rev-parse --abbrev-ref HEAD
git log --oneline -n 5
# ожидаемо: ветка develop и свежий merge из origin/develop

# 2) Проверить, есть ли модуль web API в текущем коде и окружении
python3 -c "import extensions.web_interface as m; print(m.__file__)"
python3 -c "from importlib.util import find_spec; print(find_spec('extensions.server_list'))"

# 3) Проверить, опубликованы ли API-роуты после перезапуска сервиса
# если снова странная ошибка про importlib/util, проверь, не перекрыт ли stdlib модулем importlib.py в проекте
python3 - <<'PY'
import importlib
print(importlib.__file__)
PY

systemctl restart server-monitor.service
curl -sS -o /dev/null -w "%{http_code}\n" http://192.168.20.2:5000/v1/monitoring/availability?scope=all
curl -sS -o /dev/null -w "%{http_code}\n" http://192.168.20.2:5000/api/v1/monitoring/availability?scope=all
```

Если после этого всё ещё `404`, значит нужно отдельно поднимать/подключать BFF API (или обновлять код/конфиг до версии, где эти маршруты реально есть),
и только потом возвращаться к reverse proxy и Bearer токену.

### Откуда взять `<login>` и `<password>`

Коротко: в этом репозитории их нет.

Если ты админ и не понимаешь, где auth, делай по-пацански и без магии:
1. Сначала почини маршрут `Apache/Nginx -> BFF`, чтобы `/v1/...` не отдавал 404 от страницы помощи.
2. Потом найди auth-сервис (обычно отдельный контейнер/процесс) и его endpoint (`/auth/login`, `/v1/auth/token` и т.д.).
3. Создай там тестового пользователя или сервисный account и получи токен любым рабочим способом этого сервиса.

Пока учётки нет, всё равно можно запускать discovery для проверки маршрутов:

```bash
./scripts/auth_token_probe.sh --insecure https://localhost
./scripts/auth_token_probe.sh --insecure --host api.202020.ru https://localhost
./scripts/auth_token_probe.sh --insecure --host api.202020.ru --prefix /api https://localhost
```

В репозитории есть helper-скрипт для первичного проброса auth-вариантов:

```bash
./scripts/auth_token_probe.sh --insecure https://localhost <login> <password>
```

Что он делает:
1. Проверяет ответ `GET /v1/monitoring/availability?scope=all` без токена (часто там видно требования к auth/scope).
2. Пробует типовые endpoint'ы выдачи токена: `/v1/auth/token`, `/v1/auth/login`, `/auth/token`, `/auth/login`, `/token`.
3. Для каждого endpoint пробует JSON и `x-www-form-urlencoded` payload.

Если в ответе приходит `access_token`:
- вставь его в Android UI (`Bearer токен`);
- проверь claims/TTL:

```bash
TOKEN='<вставь_сюда_JWT>'
python3 -c 'import base64,json,os; t=os.environ["TOKEN"]; p=t.split(".")[1]; p+="="*(-len(p)%4); print(json.dumps(json.loads(base64.urlsafe_b64decode(p)),indent=2,ensure_ascii=False))'
```

Смотри поля `scope`/`scp`/`roles`, `exp`, `iat` — это закроет вопросы про scope и TTL.


### Если видишь 404 от Apache и токена нет

Это значит, что запрос прилетает не в BFF, а в дефолтный vhost Apache на `:443`.

Проверь сначала порт `8443`:

```bash
./scripts/auth_token_probe.sh --insecure https://localhost:8443 <login> <password>
# или
./scripts/auth_token_probe.sh --insecure https://192.168.20.2:8443 <login> <password>
```


Если `8443` проброшен только снаружи и локально не слушает — это нормально. Тогда на сервере проверь, какие порты реально открыты:

```bash
ss -lntp | grep -E '(:443|:8443)'
```

Если API живёт за Apache/Nginx на `:443` и маршрутизация идёт по доменному vhost, запускай с Host header:

```bash
./scripts/auth_token_probe.sh --insecure --host api.202020.ru https://localhost:443 <login> <password>
```


Если и с `--host` получаешь `404`, вероятно у API есть префикс (например, `/api` или `/bff`).
Проверь так:

```bash
./scripts/auth_token_probe.sh --insecure --host api.202020.ru --prefix /api https://localhost:443 <login> <password>
# или
./scripts/auth_token_probe.sh --insecure --host api.202020.ru --prefix /bff https://localhost:443 <login> <password>
```


Начиная с текущей версии скрипта: если probe сразу даёт `Apache 404`, скрипт **останавливается**, делает быструю проверку типовых маршрутов (`/health`, `/openapi.json`, `/docs`) и не спамит сотней POST-запросов.
Если хочешь принудительно прогнать все POST-варианты — добавь `--force-probe`.


Если в quick-check видно картину как у тебя (`/ -> 200`, всё остальное `404`), это почти наверняка значит:
- Apache отвечает страницей сайта,
- а маршруты BFF (`/v1/...`) в этот vhost не прокинуты.

То есть токен тут не извлечь никаким перебором endpoint'ов — сначала надо починить роутинг reverse proxy до BFF.


```bash
./scripts/auth_token_probe.sh --insecure --host api.202020.ru --prefix /api https://localhost:443 <login> <password> --force-probe
```




Также важно: сообщение `rg: команда не найдена` — это старая версия скрипта. В новой версии используется `grep`, без зависимости от `rg`.

### Можно ли достать Bearer-токен из SQL?

В текущем репозитории `settings.db` хранит настройки мониторинга (например, `TELEGRAM_TOKEN`, `SSH_USERNAME`), но не кэш access/refresh токенов мобильного auth-flow.
Поэтому обычно **нет**, вытаскивать Bearer из этой БД нечего.

Проверить, что в `settings` нет auth access token, можно так:

```bash
sqlite3 data/settings.db "SELECT key FROM settings WHERE lower(key) LIKE '%token%' OR lower(key) LIKE '%auth%';"
```

Если ваш BFF хранит сессии в отдельной БД (PostgreSQL/MySQL/Redis) — искать надо там, а не в `settings.db` этого проекта.


2. Вставить токен в поле `Bearer токен`.
3. Нажать `Сохранить токен`.
4. Нажать `Обновить` — получишь список серверов и summary.

---

## 6. Что с Telegram-ботом

- Мы **не удаляем** и **не переписываем** Telegram-логику.
- Бот остаётся отдельным каналом управления.
- Android — дополнительный канал через тот же backend/BFF.

Так что пункт «функционал и связь с Telegram не теряем» соблюдён.

---

## 7. Структура Android-кода

```text
android-client/
  build.gradle.kts
  settings.gradle.kts
  app/
    build.gradle.kts
    src/main/
      AndroidManifest.xml
      java/ru/monitoring/mobile/
        MainActivity.kt
        api/
          ApiFactory.kt
          ApiModels.kt
          MonitoringApi.kt
        storage/
          AppPreferences.kt
        ui/
          MainViewModel.kt
      res/xml/network_security_config.xml
      res/values/themes.xml
```

---

## 8. Команды для сборки (через терминал)

Если открываешь проект впервые, проще собрать из Android Studio кнопкой **Run**.

Дальше можно через gradle wrapper (после его генерации студией):

```bash
cd android-client
./gradlew assembleDebug
```

APK обычно будет в:

```text
android-client/app/build/outputs/apk/debug/app-debug.apk
```

---

## 9. Мини-чеклист перед выкладкой

1. API токен не захардкожен в коде.
2. В логах не светятся секреты.
3. `cleartextTrafficPermitted=false` (HTTP без TLS запрещён).
4. Проверены сценарии:
   - refresh availability;
   - control action;
   - update settings.

---

## 10. Что делать дальше (эволюция по шагам)

Следующий этап, который логично накатить после базового MVP:

1. Добавить нормальный login flow (получение токена в приложении).
2. Разнести экран на вкладки (Dashboard / Alerts / Settings).
3. Вынести API-модели в отдельный shared-модуль и покрыть unit-тестами.
4. Добавить push-уведомления о DOWN серверах.
5. Добавить feature-flag, если какой-то endpoint на бэке ещё не готов.

---

## 11. Почему документацию в `/docs` не удаляли

Ты прав, когда документация без кода — толку мало. Но удалять текущие файлы не стали, потому что:

1. они фиксируют черновые API-контракты;
2. оттуда взяты endpoint'ы для мобильного клиента;
3. это уменьшает риск разъезда между приложением и BFF.

Если нужно — можно позже подчистить и оставить только актуальные доки (после стабилизации API).
