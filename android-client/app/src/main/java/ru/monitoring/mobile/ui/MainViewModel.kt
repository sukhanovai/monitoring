package ru.monitoring.mobile.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import javax.net.ssl.SSLException
import kotlinx.coroutines.launch
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.ControlActionRequest
import ru.monitoring.mobile.api.ServerAvailability
import ru.monitoring.mobile.api.SettingsMonitoringRequest
import ru.monitoring.mobile.storage.AppPreferences

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


    private fun formatNetworkError(error: Throwable): String = when (error) {
        is SocketTimeoutException -> "Таймаут запроса. Проверь интернет на устройстве и доступность api.202020.ru:8443"
        is UnknownHostException -> "DNS не резолвит хост api.202020.ru. Проверь сеть/мобильный интернет"
        is ConnectException -> "Нет соединения с api.202020.ru:8443. Проверь доступ к серверу и фаервол"
        is SSLException -> "Ошибка TLS/сертификата. Проверь дату/время устройства и SSL-конфиг сервера"
        else -> error.message ?: "Ошибка сети"
    }

    fun refreshAvailability() {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.getAvailability()
            }.onSuccess { response ->
                val payload = response.data
                if (payload == null) {
                    state = state.copy(
                        isLoading = false,
                        message = response.error?.message ?: "Пустой ответ от API"
                    )
                    return@onSuccess
                }

                state = state.copy(
                    isLoading = false,
                    servers = payload.servers,
                    summaryText = "UP: ${payload.summary.up}, DOWN: ${payload.summary.down}, UNKNOWN: ${payload.summary.unknown}",
                    message = "Данные обновлены"
                )
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
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
                state = state.copy(isLoading = false, message = formatNetworkError(error))
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
                state = state.copy(isLoading = false, message = formatNetworkError(error))
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
