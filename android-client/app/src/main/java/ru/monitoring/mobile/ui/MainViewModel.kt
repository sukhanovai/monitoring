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
import kotlinx.coroutines.async
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
        refreshSettingsFromServer()
    }

    fun setTokenInput(value: String) {
        state = state.copy(token = value)
    }

    fun setCheckIntervalInput(value: String) {
        state = state.copy(checkIntervalInput = value)
    }

    fun setTimeoutInput(value: String) {
        state = state.copy(timeoutInput = value)
    }

    fun setMaxDowntimeInput(value: String) {
        state = state.copy(maxDowntimeInput = value)
    }

    fun setTelegramTokenInput(value: String) {
        state = state.copy(telegramTokenInput = value)
    }

    fun setTelegramChatIdInput(value: String) {
        state = state.copy(telegramChatIdInput = value)
    }

    fun setQuietStartInput(value: String) {
        state = state.copy(quietStartInput = value)
    }

    fun setQuietEndInput(value: String) {
        state = state.copy(quietEndInput = value)
    }

    fun setMetricsTimeInput(value: String) {
        state = state.copy(metricsTimeInput = value)
    }

    fun setAuthModeInput(value: String) {
        state = state.copy(authModeInput = value)
    }

    fun setSshUsernameInput(value: String) {
        state = state.copy(sshUsernameInput = value)
    }

    fun setSshPortInput(value: String) {
        state = state.copy(sshPortInput = value)
    }

    fun setWindowsUsernameInput(value: String) {
        state = state.copy(windowsUsernameInput = value)
    }

    fun toggleApiTokenVisibility() {
        state = state.copy(isApiTokenVisible = !state.isApiTokenVisible)
    }

    fun toggleTelegramTokenVisibility() {
        state = state.copy(isTelegramTokenVisible = !state.isTelegramTokenVisible)
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

    fun refreshSettingsFromServer() {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching {
                val monitoringDeferred = async { api.getMonitoringSettings() }
                val botDeferred = async { api.getBotSettings() }
                val timeDeferred = async { api.getTimeSettings() }
                val authDeferred = async { api.getAuthSettings() }

                SettingsSnapshot(
                    monitoring = monitoringDeferred.await(),
                    bot = botDeferred.await(),
                    time = timeDeferred.await(),
                    auth = authDeferred.await()
                )
            }.onSuccess { snapshot ->
                val monitoring = snapshot.monitoring
                val monitoringData = monitoring.settings

                val botData = snapshot.bot.settings

                val time = snapshot.time
                val timeData = time.settings

                val auth = snapshot.auth
                val authData = auth.settings

                state = state.copy(
                    isLoading = false,
                    checkIntervalInput = (monitoringData?.checkIntervalSec ?: monitoring.checkIntervalSec)?.toString() ?: "",
                    timeoutInput = (monitoringData?.timeoutSec ?: monitoring.timeoutSec)?.toString() ?: "",
                    maxDowntimeInput = (monitoringData?.maxDowntimeSec ?: monitoring.maxDowntimeSec)?.toString() ?: "",
                    telegramTokenInput = botData?.maskedToken ?: botData?.telegramBotToken ?: "",
                    telegramChatIdInput = botData?.telegramChatId ?: "",
                    quietStartInput = timeData?.quietStart ?: time.quietStart ?: "",
                    quietEndInput = timeData?.quietEnd ?: time.quietEnd ?: "",
                    metricsTimeInput = timeData?.metricsCollectionTime ?: time.metricsCollectionTime ?: "",
                    authModeInput = authData?.authMode ?: auth.authMode ?: "",
                    sshUsernameInput = authData?.sshUsername ?: auth.sshUsername ?: "",
                    sshPortInput = (authData?.sshPort ?: auth.sshPort)?.toString() ?: "",
                    windowsUsernameInput = authData?.windowsUsername ?: auth.windowsUsername ?: "",
                    message = "Настройки подтянуты из БД"
                )
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = "Не удалось подтянуть настройки: ${formatNetworkError(error)}")
            }
        }
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

    fun updateMonitoringSettings() {
        val checkInterval = state.checkIntervalInput
        val timeout = state.timeoutInput
        val maxDowntime = state.maxDowntimeInput

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
            }.onSuccess {
                state = state.copy(isLoading = false, message = "Настройки мониторинга обновлены")
                refreshSettingsFromServer()
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateBotSettings() {
        val telegramToken = state.telegramTokenInput
        val telegramChatId = state.telegramChatIdInput

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
            }.onSuccess {
                state = state.copy(isLoading = false, message = "Настройки бота обновлены")
                refreshSettingsFromServer()
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateTimeSettings() {
        val quietStart = state.quietStartInput
        val quietEnd = state.quietEndInput
        val metricsCollectionTime = state.metricsTimeInput

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
            }.onSuccess {
                state = state.copy(isLoading = false, message = "Временные настройки обновлены")
                refreshSettingsFromServer()
            }.onFailure { error ->
                state = state.copy(isLoading = false, message = formatNetworkError(error))
            }
        }
    }

    fun updateAuthSettings() {
        val authMode = state.authModeInput
        val sshUsername = state.sshUsernameInput
        val sshPort = state.sshPortInput
        val windowsUsername = state.windowsUsernameInput

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
            }.onSuccess {
                state = state.copy(isLoading = false, message = "Auth-настройки обновлены")
                refreshSettingsFromServer()
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

private data class SettingsSnapshot(
    val monitoring: ru.monitoring.mobile.api.SettingsMonitoringResponse,
    val bot: ru.monitoring.mobile.api.SettingsBotResponse,
    val time: ru.monitoring.mobile.api.SettingsTimeResponse,
    val auth: ru.monitoring.mobile.api.SettingsAuthResponse
)

data class MainUiState(
    val token: String = "",
    val isApiTokenVisible: Boolean = false,
    val isTelegramTokenVisible: Boolean = false,
    val isLoading: Boolean = false,
    val summaryText: String = "Нажми \"Обновить\", чтобы получить статус",
    val servers: List<ServerAvailability> = emptyList(),
    val message: String = "",
    val checkIntervalInput: String = "",
    val timeoutInput: String = "",
    val maxDowntimeInput: String = "",
    val telegramTokenInput: String = "",
    val telegramChatIdInput: String = "",
    val quietStartInput: String = "",
    val quietEndInput: String = "",
    val metricsTimeInput: String = "",
    val authModeInput: String = "",
    val sshUsernameInput: String = "",
    val sshPortInput: String = "",
    val windowsUsernameInput: String = ""
)
