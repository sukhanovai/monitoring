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
import ru.monitoring.mobile.api.AvailabilityItem
import ru.monitoring.mobile.api.ControlActionRequest
import ru.monitoring.mobile.api.ServerAvailability
import ru.monitoring.mobile.api.SettingsAuthRequest
import ru.monitoring.mobile.api.SettingsBotRequest
import ru.monitoring.mobile.api.SettingsMonitoringRequest
import ru.monitoring.mobile.api.SettingsTimeRequest
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

    private fun mapItemsToServers(items: List<AvailabilityItem>): List<ServerAvailability> =
        items.mapIndexed { index, item ->
            ServerAvailability(
                id = item.serverId?.ifBlank { null } ?: "server-${index + 1}",
                name = item.serverId?.ifBlank { null } ?: "server-${index + 1}",
                status = item.status ?: "UNKNOWN",
                lastCheckedAt = item.checkedAt
            )
        }

    private fun buildSummaryText(servers: List<ServerAvailability>): String {
        val up = servers.count { it.status.equals("UP", ignoreCase = true) }
        val down = servers.count { it.status.equals("DOWN", ignoreCase = true) }
        val unknown = (servers.size - up - down).coerceAtLeast(0)
        return "UP: $up, DOWN: $down, UNKNOWN: $unknown"
    }

    private fun hasAnyValue(vararg values: String): Boolean = values.any { it.isNotBlank() }

    private fun parseOptionalInt(value: String, fieldName: String): Int? {
        if (value.isBlank()) {
            return null
        }
        return value.toIntOrNull() ?: throw IllegalArgumentException("Поле $fieldName должно быть числом")
    }

    fun refreshAvailability() {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.getAvailability()
            }.onSuccess { response ->
                val servers = if (response.servers.isNotEmpty()) {
                    response.servers
                } else {
                    mapItemsToServers(response.items)
                }

                if (servers.isEmpty()) {
                    state = state.copy(
                        isLoading = false,
                        message = "API ответил, но список серверов пуст"
                    )
                    return@onSuccess
                }

                state = state.copy(
                    isLoading = false,
                    servers = servers,
                    summaryText = buildSummaryText(servers),
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
                state = state.copy(
                    isLoading = false,
                    message = response.message ?: response.result ?: "Команда отправлена"
                )
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateMonitoringSettings(checkInterval: String, timeout: String, maxDowntime: String) {
        if (!hasAnyValue(checkInterval, timeout, maxDowntime)) {
            state = state.copy(message = "Заполни хотя бы одно поле monitoring")
            return
        }

        val request = runCatching {
            SettingsMonitoringRequest(
                checkIntervalSec = parseOptionalInt(checkInterval, "check_interval_sec"),
                timeoutSec = parseOptionalInt(timeout, "timeout_sec"),
                maxDowntimeSec = parseOptionalInt(maxDowntime, "max_downtime_sec")
            )
        }.getOrElse { error ->
            state = state.copy(message = error.message ?: "Ошибка в полях monitoring")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.updateMonitoringSettings(request)
            }.onSuccess { response ->
                val settings = response.settings
                val interval = settings?.checkIntervalSec ?: response.checkIntervalSec
                val timeoutValue = settings?.timeoutSec ?: response.timeoutSec
                val maxDown = settings?.maxDowntimeSec ?: response.maxDowntimeSec

                val msg = if (interval != null && timeoutValue != null && maxDown != null) {
                    "Сохранено: interval=$interval, timeout=$timeoutValue, maxDown=$maxDown"
                } else {
                    "Настройки мониторинга обновлены"
                }

                state = state.copy(isLoading = false, message = msg)
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateBotSettings(telegramToken: String, telegramChatId: String) {
        if (!hasAnyValue(telegramToken, telegramChatId)) {
            state = state.copy(message = "Заполни хотя бы одно поле bot")
            return
        }

        val request = SettingsBotRequest(
            telegramBotToken = telegramToken.ifBlank { null },
            telegramChatId = telegramChatId.ifBlank { null }
        )

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.updateBotSettings(request)
            }.onSuccess { response ->
                val settings = response.settings
                val chatId = settings?.telegramChatId ?: "-"
                val tokenInfo = settings?.maskedToken ?: "обновлён"
                state = state.copy(
                    isLoading = false,
                    message = "Bot settings: chat_id=$chatId, token=$tokenInfo"
                )
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateTimeSettings(quietStart: String, quietEnd: String, metricsCollectionTime: String) {
        if (!hasAnyValue(quietStart, quietEnd, metricsCollectionTime)) {
            state = state.copy(message = "Заполни хотя бы одно поле time")
            return
        }

        val request = SettingsTimeRequest(
            quietStart = quietStart.ifBlank { null },
            quietEnd = quietEnd.ifBlank { null },
            metricsCollectionTime = metricsCollectionTime.ifBlank { null }
        )

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.updateTimeSettings(request)
            }.onSuccess { response ->
                val settings = response.settings
                val quiet = "${settings?.quietStart ?: "-"}..${settings?.quietEnd ?: "-"}"
                val metricsTime = settings?.metricsCollectionTime ?: "-"
                state = state.copy(
                    isLoading = false,
                    message = "Time settings: quiet=$quiet, metrics_time=$metricsTime"
                )
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateAuthSettings(authMode: String, sshUsername: String, sshPort: String, windowsUsername: String) {
        if (!hasAnyValue(authMode, sshUsername, sshPort, windowsUsername)) {
            state = state.copy(message = "Заполни хотя бы одно поле auth")
            return
        }

        val request = runCatching {
            SettingsAuthRequest(
                authMode = authMode.ifBlank { null },
                sshUsername = sshUsername.ifBlank { null },
                sshPort = parseOptionalInt(sshPort, "ssh_port"),
                windowsUsername = windowsUsername.ifBlank { null }
            )
        }.getOrElse { error ->
            state = state.copy(message = error.message ?: "Ошибка в полях auth")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                api.updateAuthSettings(request)
            }.onSuccess { response ->
                val settings = response.settings
                state = state.copy(
                    isLoading = false,
                    message = "Auth settings: mode=${settings?.authMode ?: "-"}, ssh=${settings?.sshUsername ?: "-"}, win=${settings?.windowsUsername ?: "-"}"
                )
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
