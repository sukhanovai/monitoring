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
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.withTimeout
import retrofit2.HttpException
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
        if (token.isNotBlank()) {
            refreshSettingsFromServer()
        }
    }

    fun loadInitialState() {
        val token = preferences.apiToken
        state = state.copy(token = token)
        if (token.isNotBlank()) {
            refreshSettingsFromServer()
        }
    }

    fun setTokenInput(value: String) { state = state.copy(token = value) }
    fun setCheckIntervalInput(value: String) { state = state.copy(checkIntervalInput = value) }
    fun setTimeoutInput(value: String) { state = state.copy(timeoutInput = value) }
    fun setMaxDowntimeInput(value: String) { state = state.copy(maxDowntimeInput = value) }
    fun setTelegramTokenInput(value: String) { state = state.copy(telegramTokenInput = value) }
    fun setTelegramChatIdInput(value: String) { state = state.copy(telegramChatIdInput = value) }
    fun setQuietStartInput(value: String) { state = state.copy(quietStartInput = value) }
    fun setQuietEndInput(value: String) { state = state.copy(quietEndInput = value) }
    fun setMetricsTimeInput(value: String) { state = state.copy(metricsTimeInput = value) }
    fun setAuthModeInput(value: String) { state = state.copy(authModeInput = value) }
    fun setSshUsernameInput(value: String) { state = state.copy(sshUsernameInput = value) }
    fun setSshPortInput(value: String) { state = state.copy(sshPortInput = value) }
    fun setWindowsUsernameInput(value: String) { state = state.copy(windowsUsernameInput = value) }
    fun setSshPasswordInput(value: String) { state = state.copy(sshPasswordInput = value) }
    fun setWindowsPasswordInput(value: String) { state = state.copy(windowsPasswordInput = value) }

    fun toggleApiTokenVisibility() { state = state.copy(isApiTokenVisible = !state.isApiTokenVisible) }
    fun toggleTelegramTokenVisibility() { state = state.copy(isTelegramTokenVisible = !state.isTelegramTokenVisible) }
    fun toggleSshPasswordVisibility() { state = state.copy(isSshPasswordVisible = !state.isSshPasswordVisible) }
    fun toggleWindowsPasswordVisibility() { state = state.copy(isWindowsPasswordVisible = !state.isWindowsPasswordVisible) }

    private fun formatNetworkError(error: Throwable): String = when (error) {
        is SocketTimeoutException -> "Таймаут запроса. Проверь интернет на устройстве и доступность api.202020.ru:8443"
        is UnknownHostException -> "DNS не резолвит хост api.202020.ru. Проверь сеть/мобильный интернет"
        is ConnectException -> "Нет соединения с api.202020.ru:8443. Проверь доступ к серверу и фаервол"
        is SSLException -> "Ошибка TLS/сертификата. Проверь дату/время устройства и SSL-конфиг сервера"
        else -> error.message ?: "Ошибка сети"
    }

    private fun isMethodNotAllowed(error: Throwable?): Boolean {
        val httpError = error as? HttpException ?: return false
        return httpError.code() == 405
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
        if (value.isBlank()) return null
        return value.toIntOrNull() ?: throw IllegalArgumentException("Поле $fieldName должно быть числом")
    }

    fun refreshSettingsFromServer() {
        if (state.token.isBlank()) {
            state = state.copy(message = "Сначала сохрани Bearer токен")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")

            val snapshot = withContext(Dispatchers.IO) {
                val monitoring = async { runCatching { withTimeout(10_000) { api.getMonitoringSettings() } } }
                val bot = async { runCatching { withTimeout(10_000) { api.getBotSettings() } } }
                val time = async { runCatching { withTimeout(10_000) { api.getTimeSettings() } } }
                val auth = async { runCatching { withTimeout(10_000) { api.getAuthSettings() } } }
                SyncResults(monitoring.await(), bot.await(), time.await(), auth.await())
            }

            val monitoringResult = snapshot.monitoring
            val botResult = snapshot.bot
            val timeResult = snapshot.time
            val authResult = snapshot.auth

            val monitoringFailure = monitoringResult.exceptionOrNull()
            val botFailure = botResult.exceptionOrNull()
            val timeFailure = timeResult.exceptionOrNull()
            val authFailure = authResult.exceptionOrNull()

            if (monitoringFailure != null && botFailure != null && timeFailure != null && authFailure != null) {
                val failMessage = if (
                    monitoringFailure is TimeoutCancellationException &&
                    botFailure is TimeoutCancellationException &&
                    timeFailure is TimeoutCancellationException &&
                    authFailure is TimeoutCancellationException
                ) {
                    "Автосинхронизация настроек недоступна: backend долго не отвечает на /v1/settings/*"
                } else if (
                    isMethodNotAllowed(monitoringFailure) &&
                    isMethodNotAllowed(botFailure) &&
                    isMethodNotAllowed(timeFailure) &&
                    isMethodNotAllowed(authFailure)
                ) {
                    "Сервер не поддерживает GET настроек (HTTP 405). Нужна поддержка endpoint на backend."
                } else {
                    "Не удалось подтянуть настройки: ${formatNetworkError(monitoringFailure)}"
                }
                state = state.copy(isLoading = false, message = failMessage)
                return@launch
            }

            val monitoring = monitoringResult.getOrNull()
            val monitoringData = monitoring?.settings
            val botData = botResult.getOrNull()?.settings
            val time = timeResult.getOrNull()
            val timeData = time?.settings
            val auth = authResult.getOrNull()
            val authData = auth?.settings

            state = state.copy(
                isLoading = false,
                checkIntervalInput = (monitoringData?.checkIntervalSec ?: monitoring?.checkIntervalSec)?.toString() ?: state.checkIntervalInput,
                timeoutInput = (monitoringData?.timeoutSec ?: monitoring?.timeoutSec)?.toString() ?: state.timeoutInput,
                maxDowntimeInput = (monitoringData?.maxDowntimeSec ?: monitoring?.maxDowntimeSec)?.toString() ?: state.maxDowntimeInput,
                telegramTokenInput = botData?.maskedToken ?: botData?.telegramBotToken ?: state.telegramTokenInput,
                telegramChatIdInput = botData?.telegramChatId ?: state.telegramChatIdInput,
                quietStartInput = timeData?.quietStart ?: time?.quietStart ?: state.quietStartInput,
                quietEndInput = timeData?.quietEnd ?: time?.quietEnd ?: state.quietEndInput,
                metricsTimeInput = timeData?.metricsCollectionTime ?: time?.metricsCollectionTime ?: state.metricsTimeInput,
                authModeInput = authData?.authMode ?: auth?.authMode ?: state.authModeInput,
                sshUsernameInput = authData?.sshUsername ?: auth?.sshUsername ?: state.sshUsernameInput,
                sshPortInput = (authData?.sshPort ?: auth?.sshPort)?.toString() ?: state.sshPortInput,
                windowsUsernameInput = authData?.windowsUsername ?: auth?.windowsUsername ?: state.windowsUsernameInput,
                sshPasswordInput = authData?.maskedSshPassword ?: auth?.sshPassword ?: state.sshPasswordInput,
                windowsPasswordInput = authData?.maskedWindowsPassword ?: auth?.windowsPassword ?: state.windowsPasswordInput,
                message = "Настройки синхронизированы автоматически"
            )
        }
    }

    fun refreshAvailability() {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching { api.getAvailability() }
                .onSuccess { response ->
                    val servers = if (response.servers.isNotEmpty()) response.servers else mapItemsToServers(response.items)
                    if (servers.isEmpty()) {
                        state = state.copy(isLoading = false, message = "API ответил, но список серверов пуст")
                        return@onSuccess
                    }
                    state = state.copy(
                        isLoading = false,
                        servers = servers,
                        summaryText = buildSummaryText(servers),
                        message = "Данные обновлены"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun sendAction(action: String) {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching { api.runControlAction(ControlActionRequest(action)) }
                .onSuccess { response ->
                    state = state.copy(isLoading = false, message = response.message ?: response.result ?: "Команда отправлена")
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
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
        }.getOrElse {
            state = state.copy(message = it.message ?: "Ошибка в полях monitoring")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching { api.updateMonitoringSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Настройки мониторинга обновлены")
                    refreshSettingsFromServer()
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
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
            runCatching { api.updateBotSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Настройки бота обновлены")
                    refreshSettingsFromServer()
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
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
            runCatching { api.updateTimeSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Временные настройки обновлены")
                    refreshSettingsFromServer()
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun updateAuthSettings() {
        val authMode = state.authModeInput
        val sshUsername = state.sshUsernameInput
        val sshPort = state.sshPortInput
        val windowsUsername = state.windowsUsernameInput
        val sshPassword = state.sshPasswordInput
        val windowsPassword = state.windowsPasswordInput

        if (!hasAnyValue(authMode, sshUsername, sshPort, windowsUsername, sshPassword, windowsPassword)) {
            state = state.copy(message = "Заполни хотя бы одно поле auth")
            return
        }

        val request = runCatching {
            SettingsAuthRequest(
                authMode = authMode.ifBlank { null },
                sshUsername = sshUsername.ifBlank { null },
                sshPort = parseOptionalInt(sshPort, "ssh_port"),
                windowsUsername = windowsUsername.ifBlank { null },
                sshPassword = sshPassword.ifBlank { null },
                windowsPassword = windowsPassword.ifBlank { null }
            )
        }.getOrElse {
            state = state.copy(message = it.message ?: "Ошибка в полях auth")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            runCatching { api.updateAuthSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Auth-настройки обновлены")
                    refreshSettingsFromServer()
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
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

private data class SyncResults(
    val monitoring: Result<ru.monitoring.mobile.api.SettingsMonitoringResponse>,
    val bot: Result<ru.monitoring.mobile.api.SettingsBotResponse>,
    val time: Result<ru.monitoring.mobile.api.SettingsTimeResponse>,
    val auth: Result<ru.monitoring.mobile.api.SettingsAuthResponse>
)

data class MainUiState(
    val token: String = "",
    val isApiTokenVisible: Boolean = false,
    val isTelegramTokenVisible: Boolean = false,
    val isSshPasswordVisible: Boolean = false,
    val isWindowsPasswordVisible: Boolean = false,
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
    val windowsUsernameInput: String = "",
    val sshPasswordInput: String = "",
    val windowsPasswordInput: String = ""
)
