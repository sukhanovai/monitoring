package ru.monitoring.mobile.api

/**
 * Совместимость клиента с сервером ComDone.
 *
 * Бета-сборки приложения (ветка `develop`) обязаны работать со стабильным
 * сервером (`main`). Правило (docs/contracts/api_compatibility.md):
 *
 * - всё API на момент baseline 9.0.0 любой сервер 9.x поддерживает — его
 *   можно вызывать без проверок;
 * - эндпоинт, добавленный после baseline, обязан иметь метку возможности:
 *   сервер объявляет её в `capabilities` ответа `GET /v1/mobile/version`
 *   (`core/api_capabilities.py`), а клиент перед вызовом проверяет
 *   [supports] и скрывает функцию, если сервер её ещё не умеет.
 *
 * [ENDPOINT_CAPABILITIES] сверяется тестом
 * `tests/test_api_compatibility_contract.py`: каждый путь из MonitoringApi.kt
 * должен быть либо в baseline (`docs/contracts/api_baseline_9.0.0.txt`),
 * либо здесь, а метка — объявлена сервером.
 */
object ServerCapabilities {
    const val API_BASELINE = "9.0.0"

    /** Путь эндпоинта (как в аннотации MonitoringApi) → метка возможности. */
    val ENDPOINT_CAPABILITIES: Map<String, String> = emptyMap()

    fun supports(serverCapabilities: Set<String>, capability: String): Boolean =
        capability in serverCapabilities
}
