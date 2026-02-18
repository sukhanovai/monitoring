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

---

## 12. Пошаговый план для новичка (куда нажимать в Android Studio)

Ниже — прям «режим за руку», чтобы ты не плавал в интерфейсе.

### Этап 1. Открываем проект правильно

1. Запусти **Android Studio**.
2. На стартовом экране нажми **Open**.
3. Выбери папку `monitoring/android-client`.
4. Нажми **OK**.
5. Если появится окно **Trust Project** — нажми **Trust Project**.
6. Дождись окончания индексации и Gradle Sync (внизу появится `Sync finished`).

Если сверху есть жёлтая плашка с предложением обновить Gradle — пока жми **Ignore**, сначала просто добьёмся запуска.

### Этап 2. Создаём эмулятор

1. Справа вверху нажми иконку телефона или открой **Tools -> Device Manager**.
2. Нажми **+ Create device**.
3. Выбери, например, **Phone -> Pixel 6 -> Next**.
4. В списке system image выбери **Android 14 (API 34)**.
5. Нажми **Download** (если ещё не скачан), дождись установки.
6. Нажми **Next -> Finish**.
7. В списке устройств нажми кнопку **▶** напротив созданного эмулятора.

### Этап 3. Первый запуск приложения

1. В верхней панели Android Studio:
   - конфигурация: `app`;
   - устройство: твой эмулятор.
2. Нажми зелёную кнопку **Run 'app'** (▶).
3. Подожди сборку и установку APK.
4. Когда приложение откроется, проверь что виден главный экран с полем токена.

Если у тебя в верхней панели написано **"Добавить конфигурацию..."** (а не `app`), значит конфигурация запуска ещё не создана. Сделай так:

1. Нажми **"Добавить конфигурацию..."**.
2. В окне **Run/Debug Configurations** нажми **+**.
3. Выбери **Android App**.
4. Name: `app`.
5. Module: `app`.
6. Нажми **OK**.
7. Снова нажми **Run 'app'**.

Если в этом окне у тебя ошибка **"Модуль не указан"** и в поле `Module` только **`<нет модуля>`**, значит Android Studio не видит Android-модуль. Обычно это потому, что открыт не тот каталог.

Сделай жёстко по шагам:

1. Нажми **Cancel** в окне конфигурации.
2. В Android Studio: **File -> Close Project**.
3. На стартовом экране: **Open**.
4. Выбери именно папку `.../monitoring/android-client` (не корень `monitoring`).
5. Дождись **Gradle Sync finished**.
6. Проверь слева, что есть модуль `app`.
7. Снова открой **Add Configuration -> Android App** и выбери `Module: app`.

Если после этого `app` всё равно не появляется:

1. **File -> Sync Project with Gradle Files**.
2. **File -> Invalidate Caches / Restart -> Invalidate and Restart**.
3. После перезапуска снова открой `android-client` и повтори выбор `Module: app`.

Если после запуска видишь просто домашний экран Android (иконки Gmail/YouTube и т.д.), то приложение ещё не открыто. Это лечится так:

1. На эмуляторе свайпни вверх и открой список приложений.
2. Найди приложение **Monitoring** (или `app`, если без брендинга).
3. Тапни по иконке приложения.
4. Должен открыться экран с полем **Bearer токен** и кнопкой сохранения.

Если иконки приложения нет вообще, значит APK не установился:

1. Проверь вкладку **Build** внизу Android Studio.
2. Исправь ошибку сборки (обычно Gradle Sync / SDK / зависимости).
3. Нажми **Run 'app'** повторно.

Если сборка падает:
- нажми **Build -> Clean Project**;
- затем **Build -> Make Project** (или `Ctrl+F9`);
- и снова **Run**.

> В некоторых версиях Android Studio пункта **Build -> Rebuild Project** нет (это нормально, не баг).
> Используй связку **Clean Project + Make Project** или запусти Gradle-задачу `assembleDebug` из панели Gradle.

### Этап 4. Где находится код и что менять в первую очередь

Открой левую панель **Project** и переключи режим на **Android** (в выпадающем списке сверху панели).

Основные файлы:

- `app/src/main/java/ru/monitoring/mobile/MainActivity.kt` — точка входа;
- `app/src/main/java/ru/monitoring/mobile/ui/MainViewModel.kt` — бизнес-логика экрана;
- `app/src/main/java/ru/monitoring/mobile/api/MonitoringApi.kt` — описание API;
- `app/src/main/java/ru/monitoring/mobile/storage/AppPreferences.kt` — хранение токена.

### Этап 5. Первая безопасная правка (чтобы не сломать проект)

Сделай маленькое изменение интерфейса, чтобы почувствовать цикл разработки.

1. Открой `MainActivity.kt`.
2. Найди текст заголовка экрана (обычно `Text(...)`).
3. Замени строку на что-то вроде `"Monitoring Mobile (dev)"`.
4. Сохрани файл (`Ctrl+S`).
5. Нажми **Run**.
6. Убедись, что новый текст появился на экране.

### Этап 6. Как делать изменения без боли

Перед каждой задачей:

1. В терминале в корне репозитория:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/android-<короткое-имя-задачи>
   ```
2. Вноси изменения маленькими кусками (1 задача = 1 коммит).
3. После каждого куска запускай приложение на эмуляторе.
4. Если всё ок — коммить.

### Частая ошибка сборки: `resource style/Theme.Material3.DayNight.NoActionBar not found`

Если видишь ошибку AAPT вида:

```text
resource style/Theme.Material3.DayNight.NoActionBar not found
error: failed linking references
```

значит в проекте не подтянута библиотека Material Components для XML-тем.

Что должно быть в `app/build.gradle.kts`:

```kotlin
implementation("com.google.android.material:material:1.12.0")
```

После этого:

1. Нажми **File -> Sync Project with Gradle Files**.
2. Перезапусти сборку: **Build -> Make Project** (или `Ctrl+F9`).

Если пункта `Rebuild Project` нет — это ожидаемо для части сборок Android Studio.

---

### Ошибка Kotlin: `Conflicting import ... Moshi/KotlinJsonAdapterFactory is ambiguous`

Если видишь ошибки вида:

```text
Conflicting import, imported name 'Moshi' is ambiguous
Conflicting import, imported name 'KotlinJsonAdapterFactory' is ambiguous
```

значит в `ApiFactory.kt` IDE/merge оставил конфликтующие импорты.

Быстрый фикс:

1. Удали дубли/конфликтующие `import` для `Moshi` и `KotlinJsonAdapterFactory`.
2. Либо используй полные имена классов прямо в коде:
   - `com.squareup.moshi.Moshi.Builder()`
   - `com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory()`
3. Выполни **Build -> Clean Project** и **Build -> Make Project**.

---

### Ошибка Kotlin: `Conflicting declarations: val moshi`

Если в `ApiFactory.kt` видишь ошибку:

```text
Conflicting declarations: val moshi: Moshi!, val moshi: Moshi!
```

значит в файле случайно осталось **две одинаковые переменные** `moshi` (обычно после нескольких правок подряд).

Как исправить:

1. Открой `ApiFactory.kt`.
2. Оставь только **одну** декларацию `moshi`.
3. Нажми **Code -> Reformat Code** (или `Ctrl+Alt+L`).
4. Выполни **Build -> Clean Project** и затем **Build -> Make Project**.

---

### Частая проблема: таймаут (`timeout`) при `Обновить`

Если после нажатия `Обновить` видишь timeout, проверь по шагам:

1. Открой в браузере телефона `https://api.202020.ru:8443/` (или любой health endpoint, если он есть).
2. Временно выключи Wi‑Fi и проверь через мобильный интернет (или наоборот).
3. Проверь, что на сервере открыт порт `8443` извне (Security Group / firewall / iptables).
4. Проверь DNS: домен `api.202020.ru` должен резолвиться на внешний IP сервера.
5. Проверь TLS-сертификат и корректные дату/время на телефоне.

В Android-клиенте увеличены сетевые таймауты и включён retry:

- `connectTimeout = 30s`
- `readTimeout = 60s`
- `writeTimeout = 60s`
- `retryOnConnectionFailure = true`

Если timeout остаётся, проблема почти наверняка в сети/доступности API, а не в UI приложения.

---

### Частая ошибка API: `Unable to create converter for ApiEnvelope<...>`

Если после нажатия `Обновить` видишь ошибку:

```text
Unable to create converter for ru.monitoring.mobile.api.ApiEnvelope<...>
```

это означает, что Retrofit/Moshi не смог создать адаптер для Kotlin data class (обычно не подключён `KotlinJsonAdapterFactory`).

Проверь `ApiFactory.kt`, должно быть так:

```kotlin
val moshi = Moshi.Builder()
    .add(KotlinJsonAdapterFactory())
    .build()

.addConverterFactory(MoshiConverterFactory.create(moshi))
```

После правки:

1. **Build -> Clean Project**
2. **Build -> Make Project** (или `Ctrl+F9`)
3. Перезапусти приложение и снова нажми `Обновить`.

Если нужно, собери APK напрямую через `Build -> Build APK(s)` или Gradle `assembleDebug`.

---

### Этап 7. Чеклист «я не ебу, почему не работает»

1. Проверил ли ты, что открыт именно `android-client`, а не корень Python-проекта.
2. Видно ли внизу Android Studio сообщение `Gradle sync finished`.
3. Запущен ли эмулятор и выбран ли он в верхней панели.
4. Выбрана ли конфигурация `app` (а не пустое **"Добавить конфигурацию..."**).
5. В Run Configuration выбран ли `Module: app` (а не **`<нет модуля>`**).
6. После `Run` действительно ли открылось приложение Monitoring, а не просто домашний экран Android.
7. Есть ли интернет в эмуляторе (открой браузер внутри эмулятора).
8. Валидный ли Bearer-токен вставлен в приложение.
9. Доступен ли API `https://api.202020.ru:8443` с твоей сети.

### Этап 8. Что делаем дальше по шагам (план обучения)

1. Научиться уверенно запускать/перезапускать приложение.
2. Научиться вносить мелкие UI-изменения в Compose.
3. Научиться править `ViewModel` и работать с состоянием.
4. Научиться подключать новый endpoint в `MonitoringApi`.
5. Добавить экран логина (получение токена в приложении).
6. Добавить базовые unit-тесты ViewModel.

Если хочешь, в следующем шаге можем начать **с нуля по кнопкам**: я дам первое маленькое задание (добавим новую кнопку в UI), и ты просто повторишь клики один в один.
