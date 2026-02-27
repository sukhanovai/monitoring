package ru.monitoring.mobile.ui

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.net.ssl.SSLException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import ru.monitoring.mobile.BuildConfig
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.AddWindowsCredentialRequest
import ru.monitoring.mobile.api.AddServerRequest
import ru.monitoring.mobile.api.AuthTokenExchangeRequest
import ru.monitoring.mobile.api.AvailabilityItem
import ru.monitoring.mobile.api.BotChatRequest
import ru.monitoring.mobile.api.CreateWindowsTypeRequest
import ru.monitoring.mobile.api.ControlActionRequest
import ru.monitoring.mobile.api.MergeWindowsTypesRequest
import ru.monitoring.mobile.api.ManagedServer
import ru.monitoring.mobile.api.RenameWindowsTypeRequest
import ru.monitoring.mobile.api.ServerAvailability
import ru.monitoring.mobile.api.SettingsAuthRequest
import ru.monitoring.mobile.api.SettingsBotRequest
import ru.monitoring.mobile.api.SettingsMonitoringRequest
import ru.monitoring.mobile.api.SettingsTimeRequest
import ru.monitoring.mobile.api.ToggleServerEnabledRequest
import ru.monitoring.mobile.api.UpdateServerRequest
import ru.monitoring.mobile.api.WindowsCredential
import ru.monitoring.mobile.api.WindowsTypeItem
import ru.monitoring.mobile.notifications.MorningReportWorker
import ru.monitoring.mobile.storage.AppPreferences

class MainViewModel(
    private val appContext: Context,
    private val preferences: AppPreferences
) : ViewModel() {
    private val botVersion = "8.11.0"
    private val androidAppVersion = BuildConfig.VERSION_NAME

    private fun currentApi() = ApiFactory.createApi(
        tokenProvider = { normalizeToken(state.token.ifBlank { preferences.apiToken }) },
        baseUrlProvider = { normalizeBaseUrlInput(state.baseUrlInput.ifBlank { preferences.apiBaseUrl }) }
    )

    private fun apiForToken(rawToken: String) = ApiFactory.createApi(
        tokenProvider = { normalizeToken(rawToken) },
        baseUrlProvider = { normalizeBaseUrlInput(state.baseUrlInput.ifBlank { preferences.apiBaseUrl }) }
    )

    var state by mutableStateOf(MainUiState())
        private set

    private fun normalizeToken(rawToken: String): String = rawToken
        .trim()
        .removePrefix("Bearer ")
        .removePrefix("bearer ")
        .replace("\\s+".toRegex(), "")
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
            baseUrlInput = preferences.apiBaseUrl,
            themeMode = preferences.themeMode,
            morningReportNotificationsEnabled = preferences.morningReportNotificationsEnabled,
            morningReportText = preferences.morningReportText,
            morningReportReceivedAt = preferences.morningReportReceivedAt,
            morningReportUnread = preferences.morningReportUnread,
            botVersion = botVersion,
            androidAppVersion = androidAppVersion
        )

        if (token.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
        }
        rescheduleMorningReportWorker()
    }

    fun saveToken(token: String) {
        val normalizedToken = normalizeToken(token)
        if (normalizedToken.isBlank()) {
            preferences.apiToken = ""
            state = state.copy(token = "", message = "РўРѕРєРµРЅ РѕС‡РёС‰РµРЅ")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)

            val exchangedToken = runCatching {
                val subject = "android-${preferences.deviceId.take(8)}"
                apiForToken(normalizedToken).exchangeAuthToken(
                    AuthTokenExchangeRequest(
                        deviceId = preferences.deviceId,
                        subject = subject,
                        reissue = true
                    )
                ).accessToken
            }.getOrNull().orEmpty()

            val finalToken = normalizeToken(if (exchangedToken.isNotBlank()) exchangedToken else normalizedToken)
            preferences.apiToken = finalToken

            state = state.copy(
                isLoading = false,
                token = finalToken,
                message = if (exchangedToken.isNotBlank()) "РўРѕРєРµРЅ РІС‹РґР°РЅ СЃРµСЂРІРµСЂРѕРј Рё СЃРѕС…СЂР°РЅРµРЅ" else "РўРѕРєРµРЅ СЃРѕС…СЂР°РЅРµРЅ"
            )

            if (finalToken.isNotBlank()) {
                refreshSettingsFromServer(showErrors = false)
            }
            rescheduleMorningReportWorker()
        }
    }

    fun saveBaseUrl() {
        val normalized = normalizeBaseUrlInput(state.baseUrlInput)
        preferences.apiBaseUrl = normalized
        state = state.copy(baseUrlInput = normalized, message = "URL API СЃРѕС…СЂР°РЅС‘РЅ")

        if (state.token.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
        }
        rescheduleMorningReportWorker()
    }

    fun setTokenInput(value: String) { state = state.copy(token = value) }
    fun setBaseUrlInput(value: String) { state = state.copy(baseUrlInput = value) }
    fun setCheckIntervalInput(value: String) { state = state.copy(checkIntervalInput = value) }
    fun setTimeoutInput(value: String) { state = state.copy(timeoutInput = value) }
    fun setMaxDowntimeInput(value: String) { state = state.copy(maxDowntimeInput = value) }
    fun setTelegramTokenInput(value: String) { state = state.copy(telegramTokenInput = value) }
    fun setTelegramChatIdInput(value: String) { state = state.copy(telegramChatIdInput = value) }
    fun setNewTelegramChatIdInput(value: String) { state = state.copy(newTelegramChatIdInput = value) }
    fun setQuietStartInput(value: String) { state = state.copy(quietStartInput = value) }
    fun setQuietEndInput(value: String) { state = state.copy(quietEndInput = value) }
    fun setMetricsTimeInput(value: String) { state = state.copy(metricsTimeInput = value) }
    fun setAuthModeInput(value: String) { state = state.copy(authModeInput = value) }
    fun setSshUsernameInput(value: String) { state = state.copy(sshUsernameInput = value) }
    fun setSshKeyPathInput(value: String) { state = state.copy(sshKeyPathInput = value) }
    fun setSshPortInput(value: String) { state = state.copy(sshPortInput = value) }
    fun setWindowsUsernameInput(value: String) { state = state.copy(windowsUsernameInput = value) }
    fun setSshPasswordInput(value: String) { state = state.copy(sshPasswordInput = value) }
    fun setWindowsPasswordInput(value: String) { state = state.copy(windowsPasswordInput = value) }
    fun setWindowsCredUsernameInput(value: String) { state = state.copy(windowsCredUsernameInput = value) }
    fun setWindowsCredPasswordInput(value: String) { state = state.copy(windowsCredPasswordInput = value) }
    fun setWindowsCredServerTypeInput(value: String) { state = state.copy(windowsCredServerTypeInput = value) }
    fun setWindowsCredPriorityInput(value: String) { state = state.copy(windowsCredPriorityInput = value) }
    fun setCreateWindowsTypeInput(value: String) { state = state.copy(createWindowsTypeInput = value) }
    fun setRenameOldTypeInput(value: String) { state = state.copy(renameOldTypeInput = value) }
    fun setRenameNewTypeInput(value: String) { state = state.copy(renameNewTypeInput = value) }
    fun setMergeSourceTypeInput(value: String) { state = state.copy(mergeSourceTypeInput = value) }
    fun setMergeTargetTypeInput(value: String) { state = state.copy(mergeTargetTypeInput = value) }
    fun setDeleteTypeInput(value: String) { state = state.copy(deleteTypeInput = value) }
    fun setDeleteTargetTypeInput(value: String) { state = state.copy(deleteTargetTypeInput = value) }
    fun setServerIpInput(value: String) { state = state.copy(serverIpInput = value) }
    fun setServerNameInput(value: String) { state = state.copy(serverNameInput = value) }
    fun setServerTypeInput(value: String) { state = state.copy(serverTypeInput = value) }
    fun setServerTimeoutInput(value: String) { state = state.copy(serverTimeoutInput = value) }
    fun setThemeMode(value: String) {
        val normalized = if (value.lowercase() == "light") "light" else "dark"
        preferences.themeMode = normalized
        state = state.copy(themeMode = normalized, message = "РўРµРјР°: ${if (normalized == "dark") "С‚РµРјРЅР°СЏ" else "СЃРІРµС‚Р»Р°СЏ"}")
    }
    fun setMorningReportNotificationsEnabled(value: Boolean) {
        preferences.morningReportNotificationsEnabled = value
        state = state.copy(morningReportNotificationsEnabled = value)
        rescheduleMorningReportWorker()
    }

    fun markMorningReportRead() {
        if (state.morningReportText.isBlank()) return
        preferences.morningReportUnread = false
        state = state.copy(morningReportUnread = false)
    }

    fun clearMorningReport() {
        preferences.morningReportText = ""
        preferences.morningReportReceivedAt = ""
        preferences.morningReportUnread = false
        state = state.copy(
            morningReportText = "",
            morningReportReceivedAt = "",
            morningReportUnread = false
        )
    }

    fun toggleApiTokenVisibility() { state = state.copy(isApiTokenVisible = !state.isApiTokenVisible) }
    fun toggleTelegramTokenVisibility() { state = state.copy(isTelegramTokenVisible = !state.isTelegramTokenVisible) }
    fun toggleSshPasswordVisibility() { state = state.copy(isSshPasswordVisible = !state.isSshPasswordVisible) }
    fun toggleWindowsPasswordVisibility() { state = state.copy(isWindowsPasswordVisible = !state.isWindowsPasswordVisible) }

    private fun formatNetworkError(error: Throwable): String = when (error) {
        is SocketTimeoutException -> "РўР°Р№РјР°СѓС‚ Р·Р°РїСЂРѕСЃР°. РџСЂРѕРІРµСЂСЊ РёРЅС‚РµСЂРЅРµС‚ РЅР° СѓСЃС‚СЂРѕР№СЃС‚РІРµ Рё РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРµСЂР°"
        is UnknownHostException -> "DNS РЅРµ СЂРµР·РѕР»РІРёС‚ С…РѕСЃС‚. РџСЂРѕРІРµСЂСЊ Base URL Рё СЃРµС‚СЊ"
        is ConnectException -> "РќРµС‚ СЃРѕРµРґРёРЅРµРЅРёСЏ СЃ API. РџСЂРѕРІРµСЂСЊ Base URL, РїРѕСЂС‚ Рё С„Р°РµСЂРІРѕР»"
        is SSLException -> "РћС€РёР±РєР° TLS/СЃРµСЂС‚РёС„РёРєР°С‚Р°. РџСЂРѕРІРµСЂСЊ СЃРµСЂС‚РёС„РёРєР°С‚ Рё РґР°С‚Сѓ/РІСЂРµРјСЏ СѓСЃС‚СЂРѕР№СЃС‚РІР°"
        is HttpException -> when (error.code()) {
            401 -> "HTTP 401: С‚РѕРєРµРЅ РЅРµРґРµР№СЃС‚РІРёС‚РµР»РµРЅ РёР»Рё РЅРµС‚ РґРѕСЃС‚СѓРїР°"
            403 -> "HTTP 403: Сѓ С‚РѕРєРµРЅР° РЅРµС‚ РїСЂР°РІ"
            else -> "HTTP ${error.code()}: ${error.message()}"
        }
        else -> error.message ?: "РћС€РёР±РєР° СЃРµС‚Рё"
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

    private fun saveMorningReport(reportText: String) {
        val normalized = reportText.trim()
        if (normalized.isBlank()) return
        val receivedAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        preferences.morningReportText = normalized
        preferences.morningReportReceivedAt = receivedAt
        preferences.morningReportUnread = true
        state = state.copy(
            morningReportText = normalized,
            morningReportReceivedAt = receivedAt,
            morningReportUnread = true
        )
    }

    private fun filterServersByQuery(servers: List<ServerAvailability>, query: String): List<ServerAvailability> {
        val normalizedQuery = query.trim().lowercase()
        if (normalizedQuery.isBlank()) return servers
        return servers.filter { server ->
            server.id.lowercase().contains(normalizedQuery) || server.name.lowercase().contains(normalizedQuery)
        }
    }

    private fun hasAnyValue(vararg values: String): Boolean = values.any { it.isNotBlank() }

    private fun parseOptionalInt(value: String, fieldName: String): Int? {
        if (value.isBlank()) return null
        return value.toIntOrNull() ?: throw IllegalArgumentException("РџРѕР»Рµ $fieldName РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ С‡РёСЃР»РѕРј")
    }

    // РЎРѕРІРјРµСЃС‚РёРјРѕСЃС‚СЊ СЃРѕ СЃС‚Р°СЂС‹РјРё СЃСЃС‹Р»РєР°РјРё РїРѕСЃР»Рµ С‡Р°СЃС‚РёС‡РЅС‹С… merge/cherry-pick.
    private fun hasUnsavedConnectionSettings(): Boolean = false

    fun refreshSettingsFromServer(showErrors: Boolean = false) {
        if (state.token.isBlank()) return

        viewModelScope.launch {
            state = state.copy(isLoading = true)

            val result = withContext(Dispatchers.IO) {
                val monitoring = runCatching { currentApi().getMonitoringSettings() }.getOrNull()
                val bot = runCatching { currentApi().getBotSettings() }.getOrNull()
                val time = runCatching { currentApi().getTimeSettings() }.getOrNull()
                val auth = runCatching { currentApi().getAuthSettings() }.getOrNull()
                val control = runCatching { currentApi().getControlStatus() }.getOrNull()
                val winTypes = runCatching { currentApi().getWindowsTypes() }.getOrNull()
                val winCreds = runCatching { currentApi().getWindowsCredentials() }.getOrNull()
                val servers = runCatching { currentApi().getServersSettings() }.getOrNull()
                listOf(monitoring, bot, time, auth, control, winTypes, winCreds, servers)
            }

            val monitoring = result[0] as? ru.monitoring.mobile.api.SettingsMonitoringResponse
            val bot = result[1] as? ru.monitoring.mobile.api.SettingsBotResponse
            val time = result[2] as? ru.monitoring.mobile.api.SettingsTimeResponse
            val auth = result[3] as? ru.monitoring.mobile.api.SettingsAuthResponse
            val control = result[4] as? ru.monitoring.mobile.api.ControlStatusResponse
            val winTypes = result[5] as? ru.monitoring.mobile.api.WindowsTypesResponse
            val winCreds = result[6] as? ru.monitoring.mobile.api.WindowsCredentialsResponse
            val servers = result[7] as? ru.monitoring.mobile.api.ServersSettingsResponse

            val monitoringData = monitoring?.settings
            val botData = bot?.settings
            val timeData = time?.settings
            val authData = auth?.settings
            val botChatIds = when {
                botData?.telegramChatIds != null -> botData.telegramChatIds
                !botData?.telegramChatId.isNullOrBlank() -> listOf(botData?.telegramChatId.orEmpty())
                else -> state.telegramChatIds
            }

            val hasAny = monitoring != null || bot != null || time != null || auth != null || control != null || winTypes != null || winCreds != null || servers != null
            if (!hasAny) {
                state = if (showErrors) {
                    state.copy(isLoading = false, message = "РќРµ СѓРґР°Р»РѕСЃСЊ РїРѕРґС‚СЏРЅСѓС‚СЊ РЅР°СЃС‚СЂРѕР№РєРё")
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
                telegramChatIds = botChatIds,
                quietStartInput = timeData?.quietStart ?: time?.quietStart ?: state.quietStartInput,
                quietEndInput = timeData?.quietEnd ?: time?.quietEnd ?: state.quietEndInput,
                metricsTimeInput = timeData?.metricsCollectionTime ?: time?.metricsCollectionTime ?: state.metricsTimeInput,
                authModeInput = authData?.authMode ?: auth?.authMode ?: state.authModeInput,
                sshUsernameInput = authData?.sshUsername ?: auth?.sshUsername ?: state.sshUsernameInput,
                sshKeyPathInput = authData?.sshKeyPath ?: auth?.sshKeyPath ?: state.sshKeyPathInput,
                sshPortInput = (authData?.sshPort ?: auth?.sshPort)?.toString() ?: state.sshPortInput,
                windowsUsernameInput = authData?.windowsUsername ?: auth?.windowsUsername ?: state.windowsUsernameInput,
                sshPasswordInput = authData?.maskedSshPassword ?: auth?.sshPassword ?: state.sshPasswordInput,
                windowsPasswordInput = authData?.maskedWindowsPassword ?: auth?.windowsPassword ?: state.windowsPasswordInput,
                windowsCredentials = when {
                    winCreds != null -> winCreds.items
                    authData != null -> authData.windowsCredentials
                    else -> state.windowsCredentials
                },
                windowsServerTypes = when {
                    winCreds != null -> winCreds.serverTypes
                    winTypes != null -> winTypes.types.map { it.name }
                    authData != null -> authData.windowsServerTypes
                    else -> state.windowsServerTypes
                },
                windowsTypes = winTypes?.types ?: state.windowsTypes,
                managedServers = servers?.items ?: state.managedServers,
                monitoringStatusText = when {
                    control?.monitoringActive == true -> "рџџў РђРєС‚РёРІРµРЅ"
                    control?.monitoringActive == false -> "рџ”ґ РџСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"
                    else -> state.monitoringStatusText
                },
                silentStatusText = when (control?.silentMode) {
                    "force_quiet" -> "рџ”‡ РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ С‚РёС…РёР№"
                    "force_loud" -> "рџ”Љ РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РіСЂРѕРјРєРёР№"
                    "auto" -> if (control.silentActive == true) "рџ”‡ РђРІС‚Рѕ (СЃРµР№С‡Р°СЃ С‚РёС…РёР№)" else "рџ”Љ РђРІС‚Рѕ (СЃРµР№С‡Р°СЃ РіСЂРѕРјРєРёР№)"
                    else -> state.silentStatusText
                }
            )
            rescheduleMorningReportWorker()
        }
    }

    fun refreshAvailability() {
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().getAvailability() }
                .onSuccess { response ->
                    val servers = if (response.servers.isNotEmpty()) response.servers else mapItemsToServers(response.items)
                    if (servers.isEmpty()) {
                        state = state.copy(isLoading = false, message = "API РѕС‚РІРµС‚РёР», РЅРѕ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ РїСѓСЃС‚")
                        return@onSuccess
                    }
                    state = state.copy(
                        isLoading = false,
                        servers = servers,
                        summaryText = buildSummaryText(servers),
                        message = "Р”Р°РЅРЅС‹Рµ РѕР±РЅРѕРІР»РµРЅС‹"
                    )
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: РЅРµС‚ РґРѕСЃС‚СѓРїР° Рє СЃС‚Р°С‚СѓСЃСѓ СЃРµСЂРІРµСЂРѕРІ. РџСЂРѕРІРµСЂСЊ Base URL Рё С‚РѕРєРµРЅ РІ РќР°СЃС‚СЂРѕР№РєР°С…"
                        403 -> "HTTP 403: РЅРµС‚ РїСЂР°РІ РЅР° РїРѕР»СѓС‡РµРЅРёРµ СЃС‚Р°С‚СѓСЃР° СЃРµСЂРІРµСЂРѕРІ"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(isLoading = false, message = userMessage)
                }
        }
    }

    fun refreshServerAvailability(server: ManagedServer) {
        val query = listOf(server.ip, server.name)
            .map { it.trim() }
            .firstOrNull { it.isNotBlank() }
            .orEmpty()
        if (query.isBlank()) return

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().getAvailability() }
                .onSuccess { response ->
                    val allServers = if (response.servers.isNotEmpty()) response.servers else mapItemsToServers(response.items)
                    val selected = allServers.firstOrNull { item ->
                        item.id.equals(server.ip, ignoreCase = true) ||
                            item.name.equals(server.ip, ignoreCase = true) ||
                            item.id.equals(server.name, ignoreCase = true) ||
                            item.name.equals(server.name, ignoreCase = true)
                    } ?: filterServersByQuery(allServers, query).firstOrNull()

                    if (selected == null) {
                        state = state.copy(
                            isLoading = false,
                            servers = emptyList(),
                            summaryText = "UP: 0, DOWN: 0, UNKNOWN: 0",
                            message = "Сервер \"$query\" не найден в ответе API"
                        )
                        return@onSuccess
                    }
                    val statusLabel = selected.status.ifBlank { "UNKNOWN" }
                    state = state.copy(
                        isLoading = false,
                        servers = listOf(selected),
                        summaryText = "${server.name} (${server.ip}): $statusLabel",
                        message = "Показан статус для: ${server.name}"
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
        state = state.copy(message = "Р Р°Р·РґРµР» '$section' РµС‰С‘ РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ РґР»СЏ Android-РјРµРЅСЋ")
    }

    fun sendAction(action: String) {
        if (hasUnsavedConnectionSettings()) {
            state = state.copy(message = "РЎРЅР°С‡Р°Р»Р° СЃРѕС…СЂР°РЅРё Base URL Рё С‚РѕРєРµРЅ РІ РќР°СЃС‚СЂРѕР№РєР°С…")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().runControlAction(ControlActionRequest(action)) }
                .onSuccess { response ->
                    val actionMessage = response.message ?: response.result ?: "РљРѕРјР°РЅРґР° РѕС‚РїСЂР°РІР»РµРЅР°"
                    if (action == "send_morning_report") {
                        saveMorningReport(actionMessage)
                    }
                    state = state.copy(isLoading = false, message = actionMessage)
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: РЅРµС‚ РґРѕСЃС‚СѓРїР° Рє РєРѕРјР°РЅРґР°Рј СѓРїСЂР°РІР»РµРЅРёСЏ. РџСЂРѕРІРµСЂСЊ Base URL Рё С‚РѕРєРµРЅ РІ РќР°СЃС‚СЂРѕР№РєР°С…"
                        403 -> "HTTP 403: РЅРµС‚ РїСЂР°РІ РЅР° РєРѕРјР°РЅРґС‹ СѓРїСЂР°РІР»РµРЅРёСЏ"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(isLoading = false, message = userMessage)
                }
        }
    }

    fun addTelegramChatId() {
        val chatId = state.newTelegramChatIdInput.trim()
        if (chatId.isBlank()) {
            state = state.copy(message = "Р’РІРµРґРё chat_id РґР»СЏ РґРѕР±Р°РІР»РµРЅРёСЏ")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().addBotChat(BotChatRequest(chatId)) }
                .onSuccess { response ->
                    val ids = response.settings?.telegramChatIds ?: state.telegramChatIds
                    state = state.copy(
                        isLoading = false,
                        telegramChatIds = ids,
                        telegramChatIdInput = response.settings?.telegramChatId ?: state.telegramChatIdInput,
                        newTelegramChatIdInput = "",
                        message = "Chat ID РґРѕР±Р°РІР»РµРЅ"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun removeTelegramChatId(chatId: String) {
        val normalized = chatId.trim()
        if (normalized.isBlank()) return

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().removeBotChat(normalized) }
                .onSuccess { response ->
                    val ids = response.settings?.telegramChatIds ?: state.telegramChatIds.filterNot { it == normalized }
                    state = state.copy(
                        isLoading = false,
                        telegramChatIds = ids,
                        telegramChatIdInput = response.settings?.telegramChatId ?: state.telegramChatIdInput,
                        message = "Chat ID СѓРґР°Р»РµРЅ"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun addWindowsCredential() {
        val username = state.windowsCredUsernameInput.trim()
        val password = state.windowsCredPasswordInput.trim()
        val serverType = state.windowsCredServerTypeInput.trim().ifBlank { "default" }
        val priority = state.windowsCredPriorityInput.toIntOrNull() ?: 0

        if (username.isBlank() || password.isBlank()) {
            state = state.copy(message = "Р”Р»СЏ Windows-СѓС‡РµС‚РєРё РЅСѓР¶РЅС‹ username Рё password")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching {
                currentApi().addWindowsCredential(
                    AddWindowsCredentialRequest(
                        username = username,
                        password = password,
                        serverType = serverType,
                        priority = priority
                    )
                )
            }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        windowsCredentials = response.items,
                        windowsServerTypes = response.serverTypes,
                        windowsCredUsernameInput = "",
                        windowsCredPasswordInput = "",
                        windowsCredServerTypeInput = "",
                        windowsCredPriorityInput = "0",
                        message = "Windows-СѓС‡РµС‚РєР° РґРѕР±Р°РІР»РµРЅР°"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun removeWindowsCredential(credId: Int?) {
        if (credId == null) return
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().deleteWindowsCredential(credId) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        windowsCredentials = response.items,
                        windowsServerTypes = response.serverTypes,
                        message = "Windows-СѓС‡РµС‚РєР° СѓРґР°Р»РµРЅР°"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun createWindowsType() {
        val typeName = state.createWindowsTypeInput.trim()
        if (typeName.isBlank()) {
            state = state.copy(message = "Р’РІРµРґРёС‚Рµ РёРјСЏ РЅРѕРІРѕРіРѕ С‚РёРїР°")
            return
        }
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().createWindowsType(CreateWindowsTypeRequest(typeName)) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        windowsTypes = response.types,
                        windowsServerTypes = response.types.map { it.name },
                        createWindowsTypeInput = "",
                        message = "РўРёРї СЃРѕР·РґР°РЅ"
                    )
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun renameWindowsType() {
        val oldType = state.renameOldTypeInput.trim()
        val newType = state.renameNewTypeInput.trim()
        if (oldType.isBlank() || newType.isBlank()) {
            state = state.copy(message = "Р—Р°РїРѕР»РЅРё СЃС‚Р°СЂРѕРµ Рё РЅРѕРІРѕРµ РёРјСЏ С‚РёРїР°")
            return
        }
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().renameWindowsType(oldType, RenameWindowsTypeRequest(newType)) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        windowsTypes = response.types,
                        windowsServerTypes = response.types.map { it.name },
                        renameOldTypeInput = "",
                        renameNewTypeInput = "",
                        message = "РўРёРї РїРµСЂРµРёРјРµРЅРѕРІР°РЅ"
                    )
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun mergeWindowsTypes() {
        val source = state.mergeSourceTypeInput.trim()
        val target = state.mergeTargetTypeInput.trim()
        if (source.isBlank() || target.isBlank() || source == target) {
            state = state.copy(message = "РЈРєР°Р¶Рё source/target С‚РёРїС‹ (Рё РѕРЅРё РґРѕР»Р¶РЅС‹ РѕС‚Р»РёС‡Р°С‚СЊСЃСЏ)")
            return
        }
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().mergeWindowsTypes(MergeWindowsTypesRequest(source, target)) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        windowsTypes = response.types,
                        windowsServerTypes = response.types.map { it.name },
                        mergeSourceTypeInput = "",
                        mergeTargetTypeInput = "",
                        message = "РўРёРїС‹ РѕР±СЉРµРґРёРЅРµРЅС‹"
                    )
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun deleteWindowsType() {
        val typeName = state.deleteTypeInput.trim()
        val target = state.deleteTargetTypeInput.trim().ifBlank { "default" }
        if (typeName.isBlank()) {
            state = state.copy(message = "РЈРєР°Р¶Рё С‚РёРї РґР»СЏ СѓРґР°Р»РµРЅРёСЏ")
            return
        }
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().deleteWindowsType(typeName, target) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        windowsTypes = response.types,
                        windowsServerTypes = response.types.map { it.name },
                        deleteTypeInput = "",
                        message = "РўРёРї СѓРґР°Р»РµРЅ"
                    )
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun startServerEdit(server: ManagedServer) {
        state = state.copy(
            serverEditIp = server.ip,
            serverIpInput = server.ip,
            serverNameInput = server.name,
            serverTypeInput = server.type,
            serverTimeoutInput = (server.timeout ?: 30).toString(),
            message = "Р РµР¶РёРј СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ: ${server.ip}"
        )
    }

    fun cancelServerEdit() {
        state = state.copy(
            serverEditIp = "",
            serverIpInput = "",
            serverNameInput = "",
            serverTypeInput = "",
            serverTimeoutInput = "30",
            message = "Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ СЃРµСЂРІРµСЂР° РѕС‚РјРµРЅРµРЅРѕ"
        )
    }

    private fun normalizeServerType(raw: String): String? = when (raw.trim().lowercase()) {
        "rdp", "windows" -> "rdp"
        "ssh", "linux" -> "ssh"
        "ping" -> "ping"
        else -> null
    }

    fun saveServer() {
        val ip = state.serverIpInput.trim()
        val name = state.serverNameInput.trim()
        val type = normalizeServerType(state.serverTypeInput)
        val timeout = state.serverTimeoutInput.trim().toIntOrNull() ?: 30
        val isEdit = state.serverEditIp.isNotBlank()

        if (!isEdit && ip.isBlank()) {
            state = state.copy(message = "Р’РІРµРґРёС‚Рµ IP СЃРµСЂРІРµСЂР°")
            return
        }
        if (name.isBlank()) {
            state = state.copy(message = "Р’РІРµРґРёС‚Рµ РёРјСЏ СЃРµСЂРІРµСЂР°")
            return
        }
        if (type == null) {
            state = state.copy(message = "РўРёРї СЃРµСЂРІРµСЂР°: rdp / ssh / ping")
            return
        }
        if (timeout < 1) {
            state = state.copy(message = "timeout РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ >= 1")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            val result = if (isEdit) {
                runCatching {
                    currentApi().updateServer(
                        state.serverEditIp,
                        UpdateServerRequest(
                            name = name,
                            type = type,
                            timeout = timeout
                        )
                    )
                }
            } else {
                runCatching {
                    currentApi().addServer(
                        AddServerRequest(
                            ip = ip,
                            name = name,
                            type = type,
                            timeout = timeout,
                            enabled = true
                        )
                    )
                }
            }

            result
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        managedServers = response.items,
                        serverEditIp = "",
                        serverIpInput = "",
                        serverNameInput = "",
                        serverTypeInput = "",
                        serverTimeoutInput = "30",
                        message = if (isEdit) "РЎРµСЂРІРµСЂ РѕР±РЅРѕРІР»РµРЅ" else "РЎРµСЂРІРµСЂ РґРѕР±Р°РІР»РµРЅ"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun deleteServer(ip: String) {
        val normalizedIp = ip.trim()
        if (normalizedIp.isBlank()) return
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().deleteServer(normalizedIp) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        managedServers = response.items,
                        message = "РЎРµСЂРІРµСЂ СѓРґР°Р»РµРЅ"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun toggleServerMonitoring(ip: String, enabled: Boolean) {
        val normalizedIp = ip.trim()
        if (normalizedIp.isBlank()) return
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().setServerEnabled(normalizedIp, ToggleServerEnabledRequest(enabled)) }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        managedServers = response.items,
                        message = if (enabled) "РњРѕРЅРёС‚РѕСЂРёРЅРі РІРєР»СЋС‡РµРЅ" else "РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun updateMonitoringSettings() {
        val checkInterval = state.checkIntervalInput
        val timeout = state.timeoutInput
        val maxDowntime = state.maxDowntimeInput
        if (!hasAnyValue(checkInterval, timeout, maxDowntime)) {
            state = state.copy(message = "Р—Р°РїРѕР»РЅРё С…РѕС‚СЏ Р±С‹ РѕРґРЅРѕ РїРѕР»Рµ monitoring")
            return
        }

        val request = runCatching {
            SettingsMonitoringRequest(
                checkIntervalSec = parseOptionalInt(checkInterval, "check_interval_sec"),
                timeoutSec = parseOptionalInt(timeout, "timeout_sec"),
                maxDowntimeSec = parseOptionalInt(maxDowntime, "max_downtime_sec")
            )
        }.getOrElse {
            state = state.copy(message = it.message ?: "РћС€РёР±РєР° РІ РїРѕР»СЏС… monitoring")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().updateMonitoringSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "РќР°СЃС‚СЂРѕР№РєРё РјРѕРЅРёС‚РѕСЂРёРЅРіР° РѕР±РЅРѕРІР»РµРЅС‹")
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun updateBotSettings() {
        val telegramToken = state.telegramTokenInput
        val telegramChatId = state.telegramChatIdInput
        if (!hasAnyValue(telegramToken, telegramChatId) && state.telegramChatIds.isEmpty()) {
            state = state.copy(message = "Р—Р°РїРѕР»РЅРё С…РѕС‚СЏ Р±С‹ РѕРґРЅРѕ РїРѕР»Рµ bot")
            return
        }

        val request = SettingsBotRequest(
            telegramBotToken = telegramToken.ifBlank { null },
            telegramChatId = telegramChatId.ifBlank { null },
            telegramChatIds = state.telegramChatIds
        )

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().updateBotSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "РќР°СЃС‚СЂРѕР№РєРё Р±РѕС‚Р° РѕР±РЅРѕРІР»РµРЅС‹")
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
            state = state.copy(message = "Р—Р°РїРѕР»РЅРё С…РѕС‚СЏ Р±С‹ РѕРґРЅРѕ РїРѕР»Рµ time")
            return
        }

        val request = SettingsTimeRequest(
            quietStart = quietStart.ifBlank { null },
            quietEnd = quietEnd.ifBlank { null },
            metricsCollectionTime = metricsCollectionTime.ifBlank { null }
        )

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().updateTimeSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Р’СЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё РѕР±РЅРѕРІР»РµРЅС‹")
                    refreshSettingsFromServer(showErrors = false)
                    rescheduleMorningReportWorker()
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun updateAuthSettings() {
        val authMode = state.authModeInput
        val sshUsername = state.sshUsernameInput
        val sshKeyPath = state.sshKeyPathInput
        val sshPort = state.sshPortInput
        val windowsUsername = state.windowsUsernameInput
        val sshPassword = state.sshPasswordInput
        val windowsPassword = state.windowsPasswordInput

        if (!hasAnyValue(authMode, sshUsername, sshKeyPath, sshPort, windowsUsername, sshPassword, windowsPassword)) {
            state = state.copy(message = "Р—Р°РїРѕР»РЅРё С…РѕС‚СЏ Р±С‹ РѕРґРЅРѕ РїРѕР»Рµ auth")
            return
        }

        val request = runCatching {
            SettingsAuthRequest(
                authMode = authMode.ifBlank { null },
                sshUsername = sshUsername.ifBlank { null },
                sshPort = parseOptionalInt(sshPort, "ssh_port"),
                sshKeyPath = state.sshKeyPathInput.ifBlank { null },
                windowsUsername = windowsUsername.ifBlank { null },
                sshPassword = sshPassword.ifBlank { null },
                windowsPassword = windowsPassword.ifBlank { null }
            )
        }.getOrElse {
            state = state.copy(message = it.message ?: "РћС€РёР±РєР° РІ РїРѕР»СЏС… auth")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().updateAuthSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Auth-РЅР°СЃС‚СЂРѕР№РєРё РѕР±РЅРѕРІР»РµРЅС‹")
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    private fun rescheduleMorningReportWorker() {
        val scheduleTime = state.metricsTimeInput.ifBlank { "08:30" }
        MorningReportWorker.schedule(
            context = appContext,
            timeRaw = scheduleTime,
            enabled = state.morningReportNotificationsEnabled && state.token.isNotBlank()
        )
    }

    @Suppress("UNCHECKED_CAST")
    class Factory(
        private val context: Context,
        private val preferences: AppPreferences
    ) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return MainViewModel(context.applicationContext, preferences) as T
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
    val baseUrlInput: String = "https://api.202020.ru:8443/",
    val isApiTokenVisible: Boolean = false,
    val isTelegramTokenVisible: Boolean = false,
    val isSshPasswordVisible: Boolean = false,
    val isWindowsPasswordVisible: Boolean = false,
    val isLoading: Boolean = false,
    val summaryText: String = "Статус не запрошен",
    val servers: List<ServerAvailability> = emptyList(),
    val message: String = "",
    val checkIntervalInput: String = "",
    val timeoutInput: String = "",
    val maxDowntimeInput: String = "",
    val telegramTokenInput: String = "",
    val telegramChatIdInput: String = "",
    val telegramChatIds: List<String> = emptyList(),
    val newTelegramChatIdInput: String = "",
    val quietStartInput: String = "",
    val quietEndInput: String = "",
    val metricsTimeInput: String = "",
    val authModeInput: String = "",
    val sshUsernameInput: String = "",
    val sshKeyPathInput: String = "",
    val sshPortInput: String = "",
    val windowsUsernameInput: String = "",
    val sshPasswordInput: String = "",
    val windowsPasswordInput: String = "",
    val windowsCredentials: List<WindowsCredential> = emptyList(),
    val windowsServerTypes: List<String> = emptyList(),
    val windowsTypes: List<WindowsTypeItem> = emptyList(),
    val windowsCredUsernameInput: String = "",
    val windowsCredPasswordInput: String = "",
    val windowsCredServerTypeInput: String = "",
    val windowsCredPriorityInput: String = "0",
    val createWindowsTypeInput: String = "",
    val renameOldTypeInput: String = "",
    val renameNewTypeInput: String = "",
    val mergeSourceTypeInput: String = "",
    val mergeTargetTypeInput: String = "",
    val deleteTypeInput: String = "",
    val deleteTargetTypeInput: String = "default",
    val managedServers: List<ManagedServer> = emptyList(),
    val serverEditIp: String = "",
    val serverIpInput: String = "",
    val serverNameInput: String = "",
    val serverTypeInput: String = "",
    val serverTimeoutInput: String = "30",
    val themeMode: String = "dark",
    val morningReportNotificationsEnabled: Boolean = true,
    val morningReportText: String = "",
    val morningReportReceivedAt: String = "",
    val morningReportUnread: Boolean = false,
    val botVersion: String = "",
    val androidAppVersion: String = "",
    val monitoringStatusText: String = "РќРµРёР·РІРµСЃС‚РЅРѕ",
    val silentStatusText: String = "РќРµРёР·РІРµСЃС‚РЅРѕ"
)
