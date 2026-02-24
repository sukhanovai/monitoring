package ru.monitoring.mobile.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.ControlActionRequest
import ru.monitoring.mobile.api.ServerAvailability
import ru.monitoring.mobile.api.SettingsMonitoringRequest
import ru.monitoring.mobile.logging.ConnectionLogger
import ru.monitoring.mobile.storage.AppPreferences
import java.io.IOException
import java.net.SocketTimeoutException
import java.util.Locale
import java.util.UUID
import retrofit2.HttpException

class MainViewModel(
    private val preferences: AppPreferences
) : ViewModel() {
    private val api = ApiFactory.createApi { preferences.apiToken }

    var state by mutableStateOf(MainUiState())
        private set

    fun saveToken(token: String) {
        preferences.apiToken = token
        state = state.copy(token = token, message = "Токен сохранён")
    }

    fun loadInitialState() {
        state = state.copy(token = preferences.apiToken)
    }

    fun refreshAvailability() {
        viewModelScope.launch {
            val requestId = UUID.randomUUID().toString()
            val host = "api.202020.ru"
            val endpoint = "/v1/monitoring/availability"
            val method = "GET"
            val tokenPresent = preferences.apiToken.trim().isNotBlank()
            val startedAt = System.nanoTime()

            ConnectionLogger.info(
                event = "availability_all_click_started",
                fields = mapOf(
                    "request_id" to requestId,
                    "base_url_host" to host,
                    "endpoint" to endpoint,
                    "http_method" to method,
                    "token_present" to tokenPresent,
                    "network_type" to "unknown"
                )
            )

            ConnectionLogger.info(
                event = "availability_all_request_prepared",
                fields = mapOf(
                    "request_id" to requestId,
                    "base_url_host" to host,
                    "endpoint" to endpoint,
                    "http_method" to method,
                    "token_present" to tokenPresent,
                    "network_type" to "unknown"
                )
            )

            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.getAvailability(requestId)
            }.onSuccess { response ->
                val payload = response.data
                if (payload == null) {
                    ConnectionLogger.warn(
                        event = "availability_all_failed",
                        fields = mapOf(
                            "request_id" to requestId,
                            "base_url_host" to host,
                            "endpoint" to endpoint,
                            "http_method" to method,
                            "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                            "network_type" to "unknown",
                            "error_type" to "UNKNOWN",
                            "error_message_short" to ConnectionLogger.shortErrorMessage(response.error?.message)
                        )
                    )
                    state = state.copy(
                        isLoading = false,
                        message = response.error?.message ?: "Пустой ответ от API"
                    )
                    ConnectionLogger.info(
                        event = "availability_all_result_rendered",
                        fields = mapOf(
                            "request_id" to requestId,
                            "base_url_host" to host,
                            "endpoint" to endpoint,
                            "http_method" to method,
                            "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                            "network_type" to "unknown",
                            "error_type" to "UNKNOWN"
                        )
                    )
                    return@onSuccess
                }

                state = state.copy(
                    isLoading = false,
                    servers = payload.servers,
                    summaryText = "UP: ${payload.summary.up}, DOWN: ${payload.summary.down}, UNKNOWN: ${payload.summary.unknown}",
                    message = "Данные обновлены"
                )

                ConnectionLogger.info(
                    event = "availability_all_result_rendered",
                    fields = mapOf(
                        "request_id" to requestId,
                        "base_url_host" to host,
                        "endpoint" to endpoint,
                        "http_method" to method,
                        "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                        "network_type" to "unknown"
                    )
                )
            }.onFailure { error ->
                ConnectionLogger.error(
                    event = "availability_all_failed",
                    fields = mapOf(
                        "request_id" to requestId,
                        "base_url_host" to host,
                        "endpoint" to endpoint,
                        "http_method" to method,
                        "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                        "network_type" to "unknown",
                        "error_type" to mapErrorType(error),
                        "error_message_short" to ConnectionLogger.shortErrorMessage(error.message),
                        "http_status" to (error as? HttpException)?.code()
                    )
                )
                state = state.copy(isLoading = false, message = error.message ?: "Ошибка запроса")
                ConnectionLogger.info(
                    event = "availability_all_result_rendered",
                    fields = mapOf(
                        "request_id" to requestId,
                        "base_url_host" to host,
                        "endpoint" to endpoint,
                        "http_method" to method,
                        "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                        "network_type" to "unknown",
                        "error_type" to mapErrorType(error)
                    )
                )
            }
        }
    }

    private fun mapErrorType(error: Throwable): String {
        return when (error) {
            is HttpException -> if (error.code() == 401) "HTTP_401" else "UNKNOWN"
            is SocketTimeoutException -> "TIMEOUT"
            is javax.net.ssl.SSLException -> "SSL"
            is IOException -> {
                val text = error.message?.lowercase(Locale.US).orEmpty()
                if (text.contains("unreachable") || text.contains("failed to connect")) "NO_NETWORK" else "UNKNOWN"
            }

            else -> "UNKNOWN"
        }
    }

    fun sendAction(action: String) {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.runControlAction(ControlActionRequest(action))
            }.onSuccess { response ->
                val data = response.data
                state = state.copy(
                    isLoading = false,
                    message = data?.message ?: response.error?.message ?: "Команда отправлена"
                )
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = error.message ?: "Ошибка команды")
            }
        }
    }

    fun updateSettings(checkInterval: String, timeout: String, maxDowntime: String) {
        val request = SettingsMonitoringRequest(
            checkIntervalSec = checkInterval.toIntOrNull(),
            timeoutSec = timeout.toIntOrNull(),
            maxDowntimeSec = maxDowntime.toIntOrNull()
        )

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.updateMonitoringSettings(request)
            }.onSuccess { response ->
                val data = response.data
                val msg = if (data != null) {
                    "Сохранено: interval=${data.checkIntervalSec}, timeout=${data.timeoutSec}, maxDown=${data.maxDowntimeSec}"
                } else {
                    response.error?.message ?: "Настройки обновлены"
                }

                state = state.copy(isLoading = false, message = msg)
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = error.message ?: "Ошибка сохранения")
            }
        }
    }

    @Suppress("UNCHECKED_CAST")
    class Factory(
        private val preferences: AppPreferences
    ) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return MainViewModel(preferences) as T
        }
    }
}

data class MainUiState(
    val token: String = "",
    val isLoading: Boolean = false,
    val summaryText: String = "Нажми \"Обновить\", чтобы получить статус",
    val servers: List<ServerAvailability> = emptyList(),
    val message: String = ""
)
