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

## 3. Как забрать код через GitHub

```bash
git clone https://github.com/sukhanovai/monitoring.git
cd monitoring
```

Дальше открываешь папку `/workspace/monitoring/android-client` как отдельный проект в Android Studio.

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
