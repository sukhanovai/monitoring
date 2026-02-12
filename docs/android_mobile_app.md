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
