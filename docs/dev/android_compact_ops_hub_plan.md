# План и реализация: Вариант A — Compact Ops Hub

## Цель
В этой ветке развёрнут второй Android-вариант интерфейса (Compact Ops Hub) без удаления текущего UI. Это позволяет параллельно дорабатывать оба варианта и переключаться между ними через Build Variant в Android Studio.

## Что сделано
1. В `android-client/app` добавлены product flavors:
   - `legacy` — текущий интерфейс (сохраняется для дальнейшей доработки);
   - `compactOps` — новый интерфейсный вариант Compact Ops Hub.
2. Для каждого flavor задан отдельный `applicationIdSuffix`, поэтому оба APK можно ставить рядом на одно устройство.
3. В `MainActivity` добавлен флаг `BuildConfig.IS_COMPACT_OPS_HUB` и включён компактный Ops-слой:
   - новый заголовок `Compact Ops Hub`;
   - плотный Ops Snapshot-блок с ключевыми счётчиками;
   - быстрые действия в компактной компоновке.
4. Для flavor-ресурсов добавлены разные имена приложения:
   - `Monitoring Legacy`;
   - `Compact Ops Hub`.

## Как переключаться в Android Studio
1. Открыть проект `android-client` в Android Studio.
2. Дождаться Gradle Sync.
3. Открыть окно **Build Variants** (обычно слева снизу; если скрыто: `View -> Tool Windows -> Build Variants`).
4. Для модуля `app` выбрать variant:
   - `legacyDebug` / `legacyRelease` — старый UI;
   - `compactOpsDebug` / `compactOpsRelease` — новый Compact Ops Hub UI.
5. В `Run/Debug Configurations` выбрать запуск `app` и убедиться, что выбран нужный variant.
6. Собрать и запустить:
   - legacy: `./gradlew :app:assembleLegacyDebug`
   - compact: `./gradlew :app:assembleCompactOpsDebug`

## Рабочий процесс в этой же ветке
- Любые изменения по обоим вариантам продолжаем делать в текущей ветке.
- Если новый вариант не устраивает, legacy продолжает жить и развиваться без отката архитектуры.
- При стабилизации можно решить, какой flavor оставить основным для релиза.

## Дальнейшие шаги по дизайну Compact Ops Hub
1. Дожать компактный дизайн для всех крупных секций (серверы, расширения, auth, отчёты) до единого dense-стандарта.
2. Добавить отдельные compact-компоненты (dense cards / compact chips / small buttons).
3. При необходимости выделить `ui/compact` пакет и постепенно переиспользовать существующие action-обработчики ViewModel.
4. После UX-валидации можно:
   - либо сделать `compactOps` основным flavor;
   - либо оставить dual-flavor схему на постоянку.
