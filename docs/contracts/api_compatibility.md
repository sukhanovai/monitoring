# Совместимость мобильного API ComDone

Server Monitoring System v9.0.0

## Зачем

Стабильный сервер (`main`) и бета-приложение (`develop`) живут независимо:
пользователь может поставить бету, а его сервер ещё на стабильной версии.
Бета обязана корректно работать с таким сервером. Стабильное приложение
обязано работать с более новым сервером.

## Правила

1. **Baseline.** Эндпоинты из
   [`api_baseline_9.0.0.txt`](api_baseline_9.0.0.txt) поддерживает любой
   сервер 9.x. Клиент вызывает их без проверок.
2. **Только добавление.** Существующие эндпоинты и поля JSON не удаляются,
   не переименовываются и не меняют смысл. Новое поле в ответе допустимо:
   Moshi игнорирует неизвестные поля, а отсутствующие у старого сервера
   поля в моделях клиента — nullable со значением по умолчанию.
3. **Метка возможности для нового эндпоинта.**
   - Сервер: метка добавляется в `API_CAPABILITIES`
     (`core/api_capabilities.py`) и отдаётся в `capabilities` ответа
     `GET /v1/mobile/version`.
   - Клиент: `"<METHOD> <путь>" to "<метка>"` в
     `ServerCapabilities.ENDPOINT_CAPABILITIES`. Перед показом функции UI
     проверяет `ServerCapabilities.supports(state.serverCapabilities, "<метка>")`.
4. **Сервер старше 9.0** не отдаёт `capabilities`. Клиент считает, что он
   умеет baseline. Ошибка HTTP 404 показывается как «функция недоступна на
   этом сервере».

## Автоматическая проверка

`tests/test_api_compatibility_contract.py` (CI) проверяет:

- каждый эндпоинт из `MonitoringApi.kt` входит в baseline или имеет метку;
- каждая метка клиента объявлена сервером;
- сервер обслуживает весь baseline.

## Пример: новый эндпоинт после 9.0.0

```python
# core/api_capabilities.py
API_CAPABILITIES: tuple[str, ...] = ("backup_calendar",)
```

```kotlin
// ServerCapabilities.kt
val ENDPOINT_CAPABILITIES = mapOf(
    "GET v1/backups/calendar" to "backup_calendar",
)

// UI
if (ServerCapabilities.supports(state.serverCapabilities, "backup_calendar")) {
    BackupCalendarCard(...)
}
```

Новый baseline (например `api_baseline_10.0.0.txt`) фиксируется только при
мажорном выпуске. Тогда же можно удалить устаревшее API.
