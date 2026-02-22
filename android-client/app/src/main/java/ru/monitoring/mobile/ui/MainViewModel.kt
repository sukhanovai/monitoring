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
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
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

    private val api
        get() = ApiFactory.createApi(
            tokenProvider = { preferences.apiToken },
            baseUrlProvider = { preferences.apiBaseUrl }
        )

    var state by mutableStateOf(MainUiState())
        private set

    private fun normalizeToken(rawToken: String): String = rawToken
        .trim()
        .removePrefix("Bearer ")
        .removePrefix("bearer ")
        .trim()

    private fun normalizeBaseUrlInput(rawUrl: String): String {
        val trimmed = rawUrl.trim()
        if (trimmed.isBlank()) return "https://api.202020.ru:8443/"
        return if (trimmed.endsWith('/')) trimmed else "$trimmed/"
    }

    fun loadInitialState() {
        val token = normalizeToken(preferences.apiToken)
        if (token != preferences.apiToken) preferences.apiToken = token

        state = state.copy(
            token = token,
            baseUrlInput = preferences.apiBaseUrl
        )

        if (token.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
        }
    }

    fun saveToken(token: String) {
        val normalizedToken = normalizeToken(token)
        preferences.apiToken = normalizedToken
        state = state.copy(token = normalizedToken, message = "Токен сохранён")

        if (normalizedToken.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
        }
    }

    fun saveBaseUrl() {
        val normalized = normalizeBaseUrlInput(state.baseUrlInput)
        preferences.apiBaseUrl = normalized
        state = state.copy(baseUrlInput = normalized, message = "URL API сохранён")

        if (state.token.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
        }
    }

    fun setTokenInput(value: String) { state = state.copy(token = value) }
    fun setBaseUrlInput(value: String) { state = state.copy(baseUrlInput = value) }
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
        is SocketTimeoutException -> "Таймаут запроса. Проверь интернет на устройстве и доступность сервера"
        is UnknownHostException -> "DNS не резолвит хост. Проверь Base URL и сеть"
        is ConnectException -> "Нет соединения с API. Проверь Base URL, порт и фаервол"
        is SSLException -> "Ошибка TLS/сертификата. Проверь сертификат и дату/время устройства"
        is HttpException -> when (error.code()) {
            401 -> "HTTP 401: токен недействителен или нет доступа"
            403 -> "HTTP 403: у токена нет прав"
            else -> "HTTP ${error.code()}: ${error.message()}"
        }
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
        if (value.isBlank()) return null
        return value.toIntOrNull() ?: throw IllegalArgumentException("Поле $fieldName должно быть числом")
    }


    private fun hasUnsavedConnectionSettings(): Boolean {
        val normalizedStateToken = normalizeToken(state.token)
        val normalizedSavedToken = normalizeToken(preferences.apiToken)
        val normalizedStateBaseUrl = normalizeBaseUrlInput(state.baseUrlInput)
        val normalizedSavedBaseUrl = normalizeBaseUrlInput(preferences.apiBaseUrl)
        return normalizedStateToken != normalizedSavedToken || normalizedStateBaseUrl != normalizedSavedBaseUrl
    }

    fun refreshSettingsFromServer(showErrors: Boolean = false) {
        if (state.token.isBlank()) return

        viewModelScope.launch {
            state = state.copy(isLoading = true)

            val result = withContext(Dispatchers.IO) {
                val monitoring = runCatching { api.getMonitoringSettings() }.getOrNull()
                val bot = runCatching { api.getBotSettings() }.getOrNull()
                val time = runCatching { api.getTimeSettings() }.getOrNull()
                val auth = runCatching { api.getAuthSettings() }.getOrNull()
                listOf(monitoring, bot, time, auth)
            }

            val monitoring = result[0] as? ru.monitoring.mobile.api.SettingsMonitoringResponse
            val bot = result[1] as? ru.monitoring.mobile.api.SettingsBotResponse
            val time = result[2] as? ru.monitoring.mobile.api.SettingsTimeResponse
            val auth = result[3] as? ru.monitoring.mobile.api.SettingsAuthResponse

            val monitoringData = monitoring?.settings
            val botData = bot?.settings
            val timeData = time?.settings
            val authData = auth?.settings

            val hasAny = monitoring != null || bot != null || time != null || auth != null
            if (!hasAny) {
                state = if (showErrors) {
                    state.copy(isLoading = false, message = "Не удалось подтянуть настройки")
                } else {
                    state.copy(isLoading = false)
                }
                return@launch
            }

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
                windowsPasswordInput = authData?.maskedWindowsPassword ?: auth?.windowsPassword ?: state.windowsPasswordInput
            )
        }
    }

    fun refreshAvailability() {
        if (hasUnsavedConnectionSettings()) {
            state = state.copy(message = "Сначала сохрани Base URL и токен в Настройках")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
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
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к статусу серверов. Проверь Base URL и токен в Настройках"
                        403 -> "HTTP 403: нет прав на получение статуса серверов"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(isLoading = false, message = userMessage)
                }
        }
    }

    fun showMenuStub(section: String) {
        state = state.copy(message = "Раздел '$section' ещё в разработке для Android-меню")
    }

    fun sendAction(action: String) {
        if (hasUnsavedConnectionSettings()) {
            state = state.copy(message = "Сначала сохрани Base URL и токен в Настройках")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { api.runControlAction(ControlActionRequest(action)) }
                .onSuccess { response ->
                    state = state.copy(isLoading = false, message = response.message ?: response.result ?: "Команда отправлена")
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к командам управления. Проверь Base URL и токен в Настройках"
                        403 -> "HTTP 403: нет прав на команды управления"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(isLoading = false, message = userMessage)
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
        }.getOrElse {
            state = state.copy(message = it.message ?: "Ошибка в полях monitoring")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { api.updateMonitoringSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Настройки мониторинга обновлены")
                    refreshSettingsFromServer(showErrors = false)
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
            state = state.copy(isLoading = true)
            runCatching { api.updateBotSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Настройки бота обновлены")
                    refreshSettingsFromServer(showErrors = false)
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
            state = state.copy(isLoading = true)
            runCatching { api.updateTimeSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Временные настройки обновлены")
                    refreshSettingsFromServer(showErrors = false)
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
            state = state.copy(isLoading = true)
            runCatching { api.updateAuthSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Auth-настройки обновлены")
                    refreshSettingsFromServer(showErrors = false)
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

data class MainUiState(
    val token: String = "",
    val baseUrlInput: String = "https://api.202020.ru:8443/",
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
