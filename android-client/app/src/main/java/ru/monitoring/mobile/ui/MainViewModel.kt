package ru.monitoring.mobile.ui

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import java.net.ConnectException
import java.net.URI
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import javax.net.ssl.SSLException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.AddWindowsCredentialRequest
import ru.monitoring.mobile.api.AddServerRequest
import ru.monitoring.mobile.api.AuthTokenExchangeRequest
import ru.monitoring.mobile.api.AvailabilityItem
import ru.monitoring.mobile.api.BotChatRequest
import ru.monitoring.mobile.api.CreateWindowsTypeRequest
import ru.monitoring.mobile.api.ControlActionRequest
import ru.monitoring.mobile.api.ExtensionItem
import ru.monitoring.mobile.api.ExtensionUpdateRequest
import ru.monitoring.mobile.api.ExtensionsActionRequest
import ru.monitoring.mobile.api.MergeWindowsTypesRequest
import ru.monitoring.mobile.api.MenuOption
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
import ru.monitoring.mobile.notifications.ServerDownAlertWorker
import ru.monitoring.mobile.storage.AppPreferences

class MainViewModel(
    private val appContext: Context,
    private val preferences: AppPreferences
) : ViewModel() {
    private val projectVersion = "8.33.77"
    private val problemBackupMarkers = listOf("❌", "⚠️", "🚨", "🆘", "⛔", "🔴", "🟠", "⚪")
    private val problemBackupKeywords = listOf("failed", "error", "problem", "down", "ошиб", "проблем", "недоступ", "не найден", "no backup")
    private val fallbackUpdateUrl = "https://github.com/sukhanovai/monitoring/releases/latest"
    private val mailBackupHistoryRegex = Regex(
        pattern = """^([✅✔❌⚠️🚨])\s*(.+?)\s*[—-]\s*(.+?)\s*\(([^()]+)\)\s*$"""
    )
    private val extensionMainMenuActions = setOf(
        "backup_hosts",
        "backup_databases",
        "backup_mail",
        "backup_stock_loads",
        "supplier_stock_reports",
        "zfs_menu"
    )
    private val extensionControlActions = setOf(
        "backup_proxmox",
        "backup_stock_loads",
        "supplier_stock_reports",
        "zfs_menu",
        "zfs"
    )
    private val extensionSettingsControlActions = extensionControlActions + setOf("open_extensions_settings")
    private val extensionActionToIdMatchers = listOf<Pair<(String) -> Boolean, String>>(
        Pair({ action -> action == "check_resources" }, "resource_monitor"),
        Pair({ action -> action == "backup_proxmox" || action.startsWith("backup_host_") }, "backup_monitor"),
        Pair({ action -> action == "backup_databases" }, "database_backup_monitor"),
        Pair({ action -> action.startsWith("backup_mail") }, "mail_backup_monitor"),
        Pair({ action -> action == "backup_stock_loads" }, "stock_load_monitor"),
        Pair({ action -> action == "supplier_stock_reports" || action.startsWith("supplier_stock_reports_") || action.startsWith("supplier_stock_report_source_day|") }, "supplier_stock_files"),
        Pair({ action -> action == "zfs_menu" || action == "zfs" }, "zfs_monitor")
    )
    private val extensionSettingsFallbackActions = listOf(
        Triple("backup_monitor", "💾 Бэкапы Proxmox", "settings_ext_backup_proxmox"),
        Triple("database_backup_monitor", "🗃️ Бэкапы БД", "settings_ext_backup_db"),
        Triple("mail_backup_monitor", "📬 Бэкапы почты", "settings_ext_backup_mail"),
        Triple("stock_load_monitor", "📦 Загрузка остатков 1С", "settings_ext_stock_load"),
        Triple("supplier_stock_files", "📦 Остатки поставщиков", "settings_ext_supplier_stock"),
        Triple("zfs_monitor", "🧊 ZFS", "settings_zfs"),
        Triple("resource_monitor", "💻 Ресурсы", "settings_resources")
    )
    private val localExtensionsSettingsBackAction = "settings_extensions_back_local"
    private val localExtensionsSettingsCloseAction = "settings_extensions_close_local"
    private val morningReportActions = listOf("send_morning_report", "morning_report")

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

    private fun isProblemBackupLabel(label: String): Boolean {
        val normalized = label.lowercase()
        return problemBackupMarkers.any { marker -> label.contains(marker) } ||
            problemBackupKeywords.any { keyword -> normalized.contains(keyword) }
    }

    private fun isProblemBackupOption(option: MenuOption): Boolean {
        val label = option.label?.trim().orEmpty()
        val action = option.action?.trim().orEmpty()
        val callbackAction = option.callbackData?.trim().orEmpty()
        val callbackActionCamel = option.callbackDataCamel?.trim().orEmpty()
        val normalizedAction = listOf(action, callbackAction, callbackActionCamel)
            .joinToString(" ")
            .lowercase()
        return isProblemBackupLabel(label) ||
            problemBackupKeywords.any { keyword -> normalizedAction.contains(keyword) }
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
            projectVersion = projectVersion
        )

        if (token.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
            checkMobileVersion()
        }
        rescheduleBackgroundWorkers()
    }

    fun checkMobileVersion() {
        val token = normalizeToken(state.token.ifBlank { preferences.apiToken })
        if (token.isBlank()) return

        viewModelScope.launch {
            runCatching {
                currentApi().getMobileVersionInfo(projectVersion)
            }.onSuccess { response ->
                val minVersion = response.minSupportedVersion.orEmpty()
                val latestVersion = response.latestVersion.orEmpty()
                val installedVersion = response.currentVersion?.takeIf { it.isNotBlank() } ?: projectVersion
                val updateUrl = resolveUpdateUrl(response.apkDownloadUrl.orEmpty())
                val updateRequiredByApi = response.updateRequired == true
                val updateRequiredBySemver = isVersionOlder(projectVersion, minVersion)
                val needUpdate = updateRequiredByApi || updateRequiredBySemver

                state = state.copy(
                    installedVersion = installedVersion,
                    minSupportedVersion = minVersion,
                    latestVersion = latestVersion,
                    apkDownloadUrl = updateUrl,
                    isUpdateRequired = needUpdate,
                    updateMessage = if (needUpdate) {
                        "Требуется обновление приложения до версии ${latestVersion.ifBlank { minVersion }}"
                    } else {
                        ""
                    }
                )
            }
        }
    }

    private fun resolveUpdateUrl(rawUrl: String): String {
        val candidate = rawUrl.trim()
        if (candidate.isBlank()) return fallbackUpdateUrl

        return runCatching {
            val uri = URI(candidate)
            val scheme = uri.scheme?.lowercase().orEmpty()
            val host = uri.host?.lowercase().orEmpty()
            val path = uri.path.orEmpty()
            val hasValidScheme = scheme == "http" || scheme == "https"
            val pointsToLegacyMissingAsset = host.contains("github.com") &&
                path.endsWith("/releases/latest/download/monitoring-android.apk")
            val pointsToGithubPage = host.contains("github.com") &&
                (path.contains("/tree/") || path.contains("/blob/") || path.contains("/issues/"))

            if (!hasValidScheme || pointsToGithubPage || pointsToLegacyMissingAsset) fallbackUpdateUrl else candidate
        }.getOrElse { fallbackUpdateUrl }
    }

    private fun isVersionOlder(current: String, required: String): Boolean {
        fun parse(value: String): List<Int>? {
            val parts = value.trim().split('.')
            if (parts.size != 3) return null
            return parts.map { it.toIntOrNull() ?: return null }
        }

        val c = parse(current) ?: return false
        val r = parse(required) ?: return false
        return c[0] < r[0] || (c[0] == r[0] && (c[1] < r[1] || (c[1] == r[1] && c[2] < r[2])))
    }

    fun saveToken(token: String) {
        val normalizedToken = normalizeToken(token)
        if (normalizedToken.isBlank()) {
            preferences.apiToken = ""
            state = state.copy(token = "", message = "Токен очищен")
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
                message = if (exchangedToken.isNotBlank()) "Токен выдан сервером и сохранен" else "Токен сохранен"
            )

            if (finalToken.isNotBlank()) {
                refreshSettingsFromServer(showErrors = false)
                checkMobileVersion()
            }
            rescheduleBackgroundWorkers()
        }
    }

    fun saveBaseUrl() {
        val normalized = normalizeBaseUrlInput(state.baseUrlInput)
        preferences.apiBaseUrl = normalized
        state = state.copy(baseUrlInput = normalized, message = "URL API сохранён")

        if (state.token.isNotBlank()) {
            refreshSettingsFromServer(showErrors = false)
        }
        rescheduleBackgroundWorkers()
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
        state = state.copy(themeMode = normalized, message = "Тема: ${if (normalized == "dark") "темная" else "светлая"}")
    }
    fun setMorningReportNotificationsEnabled(value: Boolean) {
        preferences.morningReportNotificationsEnabled = value
        state = state.copy(morningReportNotificationsEnabled = value)
        rescheduleBackgroundWorkers()
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

    private fun mapItemsToServers(items: List<AvailabilityItem>): List<ServerAvailability> {
        val managedByIp = state.managedServers.associateBy { it.ip.trim().lowercase() }
        val managedByName = state.managedServers.associateBy { it.name.trim().lowercase() }

        return items.mapIndexed { index, item ->
            val normalizedId = item.serverId?.trim().orEmpty()
            val normalizedIp = item.ip?.trim().orEmpty()
            val normalizedServerName = item.serverName?.trim().orEmpty()
            val normalizedName = item.name?.trim().orEmpty()

            val resolvedManaged = listOf(normalizedIp, normalizedId, normalizedServerName, normalizedName)
                .firstNotNullOfOrNull { token ->
                    val lookup = token.lowercase()
                    managedByIp[lookup] ?: managedByName[lookup]
                }

            val fallbackId = listOf(normalizedId, normalizedIp, normalizedServerName, normalizedName)
                .firstOrNull { it.isNotBlank() }
                ?: "server-${index + 1}"
            val fallbackName = listOf(
                resolvedManaged?.name.orEmpty(),
                normalizedServerName,
                normalizedName,
                normalizedId,
                normalizedIp
            ).firstOrNull { it.isNotBlank() } ?: fallbackId

            ServerAvailability(
                id = fallbackId,
                name = fallbackName,
                status = item.status ?: "UNKNOWN",
                lastCheckedAt = item.checkedAt
            )
        }
    }

    private fun isDownStatus(statusRaw: String): Boolean {
        val normalized = statusRaw.trim().lowercase()
        return normalized in setOf("down", "unreachable", "offline", "error", "critical")
    }

    private fun buildSummaryText(servers: List<ServerAvailability>): String {
        val up = servers.count { it.status.equals("UP", ignoreCase = true) }
        val down = servers.count { isDownStatus(it.status) }
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
        return value.toIntOrNull() ?: throw IllegalArgumentException("Поле $fieldName должно быть числом")
    }

    // Совместимость со старыми ссылками после частичных merge/cherry-pick.
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
                val extensions = runCatching { currentApi().getExtensionsSettings() }.getOrNull()
                listOf(monitoring, bot, time, auth, control, winTypes, winCreds, servers, extensions)
            }

            val monitoring = result[0] as? ru.monitoring.mobile.api.SettingsMonitoringResponse
            val bot = result[1] as? ru.monitoring.mobile.api.SettingsBotResponse
            val time = result[2] as? ru.monitoring.mobile.api.SettingsTimeResponse
            val auth = result[3] as? ru.monitoring.mobile.api.SettingsAuthResponse
            val control = result[4] as? ru.monitoring.mobile.api.ControlStatusResponse
            val winTypes = result[5] as? ru.monitoring.mobile.api.WindowsTypesResponse
            val winCreds = result[6] as? ru.monitoring.mobile.api.WindowsCredentialsResponse
            val servers = result[7] as? ru.monitoring.mobile.api.ServersSettingsResponse
            val extensions = result[8] as? ru.monitoring.mobile.api.ExtensionsSettingsResponse

            val monitoringData = monitoring?.settings
            val botData = bot?.settings
            val timeData = time?.settings
            val authData = auth?.settings
            val botChatIds = when {
                botData?.telegramChatIds != null -> botData.telegramChatIds
                !botData?.telegramChatId.isNullOrBlank() -> listOf(botData?.telegramChatId.orEmpty())
                else -> state.telegramChatIds
            }

            val hasAny = monitoring != null || bot != null || time != null || auth != null || control != null || winTypes != null || winCreds != null || servers != null || extensions != null
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
                extensions = extensions?.items ?: state.extensions,
                monitoringStatusText = when {
                    control?.monitoringActive == true -> "🟢 Активен"
                    control?.monitoringActive == false -> "🔴 Приостановлен"
                    else -> state.monitoringStatusText
                },
                silentStatusText = when (control?.silentMode) {
                    "force_quiet" -> "🔇 Принудительно тихий"
                    "force_loud" -> "🔊 Принудительно громкий"
                    "auto" -> if (control.silentActive == true) "🔇 Авто (сейчас тихий)" else "🔊 Авто (сейчас громкий)"
                    else -> state.silentStatusText
                }
            )
            rescheduleBackgroundWorkers()
        }
    }


    fun refreshData() {
        refreshSettingsFromServer(showErrors = true)
        refreshAvailability()
    }

    fun applyServerDownNotification(downServers: List<String>) {
        val normalized = downServers.map { it.trim() }.filter { it.isNotBlank() }.distinct()
        if (normalized.isEmpty()) return

        val text = normalized.joinToString(", ")
        state = state.copy(
            summaryText = "Недоступен: $text",
            message = "Из уведомления: $text",
            messageSource = "global"
        )
    }

    fun refreshAvailability() {
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().getAvailability() }
                .onSuccess { response ->
                    val servers = if (response.servers.isNotEmpty()) response.servers else mapItemsToServers(response.items)
                    if (servers.isEmpty()) {
                        state = state.copy(
                            isLoading = false,
                            message = "API ответил, но список серверов пуст",
                            messageSource = "all_servers"
                        )
                        return@onSuccess
                    }
                    state = state.copy(
                        isLoading = false,
                        servers = servers,
                        summaryText = buildSummaryText(servers),
                        message = "Данные обновлены",
                        messageSource = "all_servers"
                    )
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к статусу серверов. Проверь Base URL и токен в Настройках"
                        403 -> "HTTP 403: нет прав на получение статуса серверов"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(isLoading = false, message = userMessage, messageSource = "all_servers")
                }
        }
    }

    private fun buildLookupTokens(server: ManagedServer): Set<String> {
        fun normalize(value: String): String = value.trim().lowercase()

        val tokens = mutableSetOf<String>()
        listOf(server.ip, server.name).forEach { raw ->
            val value = normalize(raw)
            if (value.isNotBlank()) tokens += value

            val ipFromBrackets = Regex("\\(([^)]+)\\)").find(value)?.groupValues?.getOrNull(1)?.trim()
            if (!ipFromBrackets.isNullOrBlank()) tokens += ipFromBrackets

            val cleaned = value
                .replace("\"", "")
                .replace("'", "")
                .replace("`", "")
                .replace("(", " ")
                .replace(")", " ")
                .trim()
            if (cleaned.isNotBlank()) {
                tokens += cleaned
                cleaned.split(" ")
                    .map { it.trim() }
                    .filter { it.isNotBlank() }
                    .forEach { tokens += it }
            }
        }
        return tokens
    }

    fun refreshServerAvailability(server: ManagedServer) {
        val query = listOf(server.ip, server.name)
            .map { it.trim() }
            .firstOrNull { it.isNotBlank() }
            .orEmpty()
        if (query.isBlank()) return

        val serverTarget = server.ip.ifBlank { server.name }

        viewModelScope.launch {
            state = state.copy(isLoading = true, availabilityServerMessageTarget = serverTarget)
            runCatching { currentApi().getAvailabilitySingle(serverTarget) }
                .onSuccess { response ->
                    val allServers = if (response.servers.isNotEmpty()) response.servers else mapItemsToServers(response.items)
                    val selected = allServers.firstOrNull()

                    if (selected == null) {
                        state = state.copy(
                            isLoading = false,
                            servers = emptyList(),
                            summaryText = "UP: 0, DOWN: 0, UNKNOWN: 0",
                            message = "Сервер \"$query\" не найден в ответе API",
                            messageSource = "server_availability",
                            availabilityServerMessageTarget = serverTarget
                        )
                        return@onSuccess
                    }

                    val statusLabel = selected.status.ifBlank { "UNKNOWN" }
                    val statusEmoji = when (statusLabel.lowercase()) {
                        "up" -> "✅"
                        "down" -> "❌"
                        else -> "❔"
                    }
                    state = state.copy(
                        isLoading = false,
                        servers = listOf(selected),
                        summaryText = "${server.name} (${server.ip}): $statusLabel",
                        message = "$statusEmoji ${server.name} (${server.ip}): $statusLabel",
                        messageSource = "server_availability",
                        availabilityServerMessageTarget = serverTarget
                    )
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к статусу серверов. Проверь Base URL и токен в Настройках"
                        403 -> "HTTP 403: нет прав на получение статуса серверов"
                        404 -> "Сервер \"$query\" не найден"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(
                        isLoading = false,
                        message = userMessage,
                        messageSource = "server_availability",
                        availabilityServerMessageTarget = serverTarget
                    )
                }
        }
    }

    fun refreshServerResources(server: ManagedServer) {
        val serverTarget = server.ip.ifBlank { server.name }.trim()
        if (serverTarget.isBlank()) return

        viewModelScope.launch {
            state = state.copy(isLoading = true, availabilityServerMessageTarget = serverTarget)
            runCatching { currentApi().getServerResources(serverTarget) }
                .onSuccess { response ->
                    val resources = response.resources
                    val cpuText = resources?.cpu?.let { "$it%" } ?: "N/A"
                    val ramText = resources?.ram?.let { "$it%" } ?: "N/A"
                    val diskText = resources?.disk?.let { "$it%" } ?: "N/A"
                    val methodText = resources?.accessMethod ?: "неизвестно"
                    val checkedAtText = resources?.timestamp ?: "N/A"
                    val targetName = response.serverName ?: server.name
                    val targetIp = response.serverIp ?: server.ip

                    val messageText = buildString {
                        append("📊 Ресурсы ")
                        append(targetName)
                        if (targetIp.isNotBlank()) append(" (").append(targetIp).append(")")
                        append("\n")
                        append("CPU: ").append(cpuText).append("\n")
                        append("RAM: ").append(ramText).append("\n")
                        append("Disk: ").append(diskText).append("\n")
                        append("Метод: ").append(methodText).append("\n")
                        append("Проверка: ").append(checkedAtText)
                    }

                    state = state.copy(
                        isLoading = false,
                        message = response.message?.takeIf { it.isNotBlank() } ?: messageText,
                        messageSource = "server_resources",
                        availabilityServerMessageTarget = serverTarget
                    )
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к ресурсам серверов. Проверь Base URL и токен в Настройках"
                        403 -> "HTTP 403: нет прав на просмотр ресурсов серверов"
                        404 -> "Сервер \"$serverTarget\" не найден"
                        409 -> "Мониторинг ресурсов отключён на сервере"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(
                        isLoading = false,
                        message = userMessage,
                        messageSource = "server_resources",
                        availabilityServerMessageTarget = serverTarget
                    )
                }
        }
    }


    fun toggleProxmoxBackupMenu() {
        if (state.extensionMenuAction == "backup_proxmox" && state.extensionMenuOptions.isNotEmpty()) {
            state = state.copy(
                extensionMenuOptions = emptyList(),
                extensionMenuAction = "",
                message = "Список серверов Proxmox скрыт",
                messageSource = "global"
            )
            return
        }
        sendAction("backup_proxmox")
    }

    fun toggleDatabaseBackupMenu() {
        if (state.extensionMenuAction == "backup_databases" && state.extensionMenuOptions.isNotEmpty()) {
            state = state.copy(
                extensionMenuOptions = emptyList(),
                extensionMenuAction = "",
                message = "Меню бэкапов БД скрыто",
                messageSource = "global"
            )
            return
        }
        sendAction("backup_databases")
    }

    fun toggleMailBackupMenu() {
        if (state.extensionMenuAction == "backup_mail" && state.extensionMenuOptions.isNotEmpty()) {
            state = state.copy(
                extensionMenuOptions = emptyList(),
                extensionMenuAction = "",
                mailBackupHistoryTitle = "",
                mailBackupHistoryItems = emptyList(),
                message = "Меню бэкапов почты скрыто",
                messageSource = "global"
            )
            return
        }
        sendAction("backup_mail")
    }

    fun openExtensionsSettingsMenu() {
        viewModelScope.launch {
            state = state.copy(
                isLoading = true,
                extensionSettingsMenuOptions = emptyList(),
                extensionSettingsMenuAction = ""
            )

            val extensionsResponse = runCatching { currentApi().getExtensionsSettings() }.getOrNull()
            val menuResponse = runCatching {
                currentApi().runControlAction(ControlActionRequest("open_extensions_settings"))
            }.getOrNull()

            if (extensionsResponse == null && menuResponse == null) {
                state = state.copy(
                    isLoading = false,
                    message = "Не удалось загрузить настройки расширений",
                    messageSource = "extensions_settings"
                )
                return@launch
            }

            val extensions = extensionsResponse?.items ?: state.extensions
            val fallbackOptions = buildExtensionsSettingsFallbackOptions(extensions)
            state = state.copy(
                isLoading = false,
                extensions = extensions,
                message = menuResponse?.message ?: "Список расширений обновлён",
                messageSource = "extensions_settings",
                extensionSettingsMenuOptions = fallbackOptions,
                extensionSettingsMenuAction = "open_extensions_settings"
            )
        }
    }

    fun runExtensionsSettingsAction(action: String) {
        val normalizedAction = normalizeExtensionsSettingsAction(action.trim())
        if (normalizedAction.isBlank()) return

        viewModelScope.launch {
            val localMenuOptions = buildLocalExtensionsSettingsMenuOptions(normalizedAction)
            if (localMenuOptions != null) {
                val message = localExtensionsSettingsMessage(normalizedAction)
                state = state.copy(
                    isLoading = false,
                    message = message,
                    messageSource = "extensions_settings",
                    extensionSettingsMenuOptions = localMenuOptions,
                    extensionSettingsMenuAction = normalizedAction
                )
                return@launch
            }

            state = state.copy(isLoading = true)
            val actionCall = if (shouldRunExtensionsSettingsViaControlApi(normalizedAction)) {
                runCatching {
                    currentApi().runControlAction(ControlActionRequest(normalizedAction))
                }.map { response ->
                    val filteredOptions = filterMenuOptionsByEnabledExtensions(
                        response.menuOptions.orEmpty(),
                        state.extensions
                    )
                    val nextOptions = if (filteredOptions.isNotEmpty()) {
                        filteredOptions
                    } else {
                        state.extensionSettingsMenuOptions
                    }
                    Triple(
                        response.message ?: response.result ?: "Команда отправлена",
                        nextOptions,
                        normalizedAction
                    )
                }
            } else {
                runCatching {
                    currentApi().runExtensionsAction(ExtensionsActionRequest(normalizedAction))
                }.map { response ->
                    val filteredOptions = filterMenuOptionsByEnabledExtensions(
                        response.menuOptions.orEmpty(),
                        state.extensions
                    )
                    val nextOptions = if (filteredOptions.isNotEmpty()) {
                        filteredOptions
                    } else {
                        state.extensionSettingsMenuOptions
                    }
                    Triple(
                        response.message ?: "Команда отправлена",
                        nextOptions,
                        if (filteredOptions.isNotEmpty()) normalizedAction else state.extensionSettingsMenuAction
                    )
                }
            }
            actionCall
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        message = response.first,
                        messageSource = "extensions_settings",
                        extensionSettingsMenuOptions = response.second,
                        extensionSettingsMenuAction = response.third
                    )
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к настройкам расширений. Проверь Base URL и токен"
                        403 -> "HTTP 403: нет прав на настройки расширений"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(
                        isLoading = false,
                        message = userMessage,
                        messageSource = "extensions_settings"
                    )
                }
        }
    }

    private fun shouldRunExtensionsSettingsViaControlApi(action: String): Boolean =
        action in extensionSettingsControlActions ||
            action.startsWith("backup_host_") ||
            action.startsWith("backup_mail") ||
            action.startsWith("supplier_stock_reports_") ||
            action.startsWith("supplier_stock_report_source_day|")

    private fun normalizeExtensionsSettingsAction(action: String): String = when (action) {
        "settings_backup_hosts" -> "settings_backup_proxmox"
        "settings_backup_patterns" -> "settings_patterns_proxmox"
        "settings_backup_databases" -> "settings_db_main"
        "settings_backup_db_patterns" -> "settings_patterns_db"
        "settings_backup_mail" -> "settings_ext_backup_mail"
        "settings_stock_load" -> "settings_ext_stock_load"
        "settings_supplier_stock" -> "settings_ext_supplier_stock"
        else -> action
    }

    private fun localExtensionsSettingsMessage(action: String): String = when (action) {
        "settings_ext_backup_proxmox" -> "🖥️ Настройки Proxmox открыты."
        "settings_ext_backup_db" -> "🗃️ Настройки бэкапов БД открыты."
        "settings_ext_backup_mail" -> "📬 Настройки бэкапов почты открыты."
        "settings_ext_stock_load" -> "📦 Настройки загрузки остатков 1С открыты."
        "settings_ext_supplier_stock" -> "📦 Настройки остатков поставщиков открыты."
        "settings_zfs" -> "🧊 Настройки ZFS открыты."
        "settings_backup_hosts" -> "🖥️ Раздел «Хосты» открыт."
        "settings_backup_patterns" -> "🔍 Раздел «Паттерны» открыт."
        "settings_backup_databases" -> "🗃️ Раздел «Базы данных» открыт."
        "settings_backup_db_patterns" -> "🔍 Раздел «Паттерны БД» открыт."
        "settings_backup_mail" -> "📬 Раздел «Почтовые бэкапы» открыт."
        "settings_stock_load" -> "📦 Раздел «Загрузка остатков 1С» открыт."
        "settings_supplier_stock" -> "📦 Раздел «Остатки поставщиков» открыт."
        localExtensionsSettingsBackAction -> "Список настроек расширений обновлён."
        else -> "Настройки расширений открыты."
    }

    private fun buildLocalExtensionsSettingsMenuOptions(action: String): List<MenuOption>? {
        return when (action) {
            localExtensionsSettingsBackAction -> buildExtensionsSettingsFallbackOptions(state.extensions) +
                MenuOption(label = "✖️ Закрыть", action = localExtensionsSettingsCloseAction)
            localExtensionsSettingsCloseAction -> emptyList()
            else -> null
        }
    }

    private fun resolveMenuOptionAction(option: MenuOption, preferCallbackData: Boolean = false): String {
        val optionAction = option.action?.trim().orEmpty()
        val callbackAction = option.callbackData?.trim().orEmpty()
        val callbackActionCamel = option.callbackDataCamel?.trim().orEmpty()

        return if (preferCallbackData) {
            when {
                callbackAction.isNotBlank() -> callbackAction
                callbackActionCamel.isNotBlank() -> callbackActionCamel
                optionAction.isNotBlank() -> optionAction
                else -> ""
            }
        } else {
            when {
                optionAction.isNotBlank() -> optionAction
                callbackAction.isNotBlank() -> callbackAction
                callbackActionCamel.isNotBlank() -> callbackActionCamel
                else -> ""
            }
        }
    }

    private fun filterMenuOptionsByEnabledExtensions(
        options: List<MenuOption>,
        extensions: List<ExtensionItem>
    ): List<MenuOption> {
        val enabledExtensionIds = extensions.asSequence()
            .filter { it.enabled }
            .map { normalizeExtensionId(it.id) }
            .filter { it.isNotBlank() }
            .toSet()
        if (enabledExtensionIds.isEmpty()) return emptyList()

        return options.filter { option ->
            val optionExtensionId = normalizeExtensionId(option.extensionId.orEmpty())
            val targetAction = resolveMenuOptionAction(option)
            if (optionExtensionId.isNotBlank()) {
                return@filter optionExtensionId in enabledExtensionIds
            }
            if (targetAction.isBlank()) return@filter false
            val mappedExtensionId = mapActionToExtensionId(targetAction)?.let(::normalizeExtensionId)
            mappedExtensionId == null || mappedExtensionId in enabledExtensionIds
        }
    }

    private fun normalizeExtensionId(id: String): String = id
        .trim()
        .lowercase()
        .replace('-', '_')

    private fun mapActionToExtensionId(action: String): String? =
        extensionActionToIdMatchers.firstOrNull { (matcher, _) -> matcher(action) }?.second

    private fun buildExtensionsSettingsFallbackOptions(extensions: List<ExtensionItem>): List<MenuOption> {
        val enabledExtensionIds = extensions.asSequence()
            .filter { it.enabled }
            .map { normalizeExtensionId(it.id) }
            .filter { it.isNotBlank() }
            .toSet()
        if (enabledExtensionIds.isEmpty()) return emptyList()

        return extensionSettingsFallbackActions.asSequence()
            .filter { (extensionId, _, _) -> normalizeExtensionId(extensionId) in enabledExtensionIds }
            .map { (extensionId, label, action) ->
                MenuOption(
                    label = label,
                    action = action,
                    extensionId = extensionId
                )
            }
            .toList()
    }

    fun toggleExtension(id: String, enabled: Boolean) {
        val extensionId = id.trim()
        if (extensionId.isBlank()) return

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().updateExtensionSettings(extensionId, ExtensionUpdateRequest(enabled)) }
                .onSuccess { response ->
                    refreshExtensionsSettings(response.message ?: if (enabled) "Расширение включено" else "Расширение отключено")
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun enableAllExtensions() {
        runExtensionsAction("enable_all", "Все расширения включены")
    }

    fun disableAllExtensions() {
        runExtensionsAction("disable_all", "Все расширения отключены")
    }

    private fun runExtensionsAction(action: String, fallbackMessage: String) {
        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching {
                    if (
                    action in extensionControlActions ||
                    action == "backup_databases" ||
                    action.startsWith("backup_host_") ||
                    action.startsWith("backup_mail") ||
                    action.startsWith("supplier_stock_reports_") ||
                    action.startsWith("supplier_stock_report_source_day|")
                ) {
                        currentApi().runControlAction(ControlActionRequest(action)).message
                    } else {
                        currentApi().runExtensionsAction(ExtensionsActionRequest(action)).message
                    }
                }
                .onSuccess { message ->
                    refreshExtensionsSettings(message ?: fallbackMessage)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    private fun refreshExtensionsSettings(successMessage: String? = null, messageSource: String = "global") {
        viewModelScope.launch {
            runCatching { currentApi().getExtensionsSettings() }
                .onSuccess { response ->
                    state = state.copy(
                        isLoading = false,
                        extensions = response.items,
                        message = successMessage ?: "Список расширений обновлён",
                        messageSource = messageSource
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun sendAction(action: String) {
        if (hasUnsavedConnectionSettings()) {
            state = state.copy(message = "Сначала сохрани Base URL и токен в Настройках")
            return
        }

        if (
            action in extensionMainMenuActions ||
            action == "backup_proxmox" ||
            action == "backup_databases" ||
            action.startsWith("backup_host_") ||
            action.startsWith("backup_mail") ||
            action.startsWith("supplier_stock_reports_") ||
            action.startsWith("supplier_stock_report_source_day|")
        ) {
            viewModelScope.launch {
                state = state.copy(isLoading = true)
                if (
                    action in extensionControlActions ||
                    action == "backup_databases" ||
                    action.startsWith("backup_host_") ||
                    action.startsWith("backup_mail") ||
                    action.startsWith("supplier_stock_reports_") ||
                    action.startsWith("supplier_stock_report_source_day|")
                ) {
                    runCatching { currentApi().runControlAction(ControlActionRequest(action)) }
                        .onSuccess { response ->
                            val mailHistory = if (action.startsWith("backup_mail")) {
                                parseMailBackupHistory(response.message.orEmpty())
                            } else {
                                null
                            }
                            val hasProblemBackups = response.menuOptions
                                .orEmpty()
                                .any { option -> isProblemBackupOption(option) }
                            state = state.copy(
                                isLoading = false,
                                message = response.message ?: "Команда отправлена",
                                messageSource = "global",
                                extensionMenuOptions = response.menuOptions.orEmpty(),
                                extensionMenuAction = if (response.menuOptions.isNullOrEmpty()) "" else action,
                                backupProxmoxHasProblemItems = if (action == "backup_proxmox") hasProblemBackups else state.backupProxmoxHasProblemItems,
                                backupDatabasesHasProblemItems = if (action == "backup_databases") hasProblemBackups else state.backupDatabasesHasProblemItems,
                                mailBackupHistoryTitle = mailHistory?.title.orEmpty(),
                                mailBackupHistoryItems = mailHistory?.items.orEmpty()
                            )
                        }
                        .onFailure { error ->
                            val userMessage = when ((error as? HttpException)?.code()) {
                                401 -> "HTTP 401: нет доступа к расширениям. Проверь Base URL и токен в Настройках"
                                403 -> "HTTP 403: нет прав на команды расширений"
                                else -> formatNetworkError(error)
                            }
                            state = state.copy(
                                isLoading = false,
                                message = userMessage,
                                messageSource = "global",
                                extensionMenuOptions = emptyList(),
                                extensionMenuAction = "",
                                mailBackupHistoryTitle = "",
                                mailBackupHistoryItems = emptyList()
                            )
                        }
                } else {
                    runCatching { currentApi().runExtensionsAction(ExtensionsActionRequest(action)) }
                        .onSuccess { response ->
                            state = state.copy(
                                isLoading = false,
                                message = response.message ?: "Команда отправлена",
                                messageSource = "global",
                                extensionMenuOptions = emptyList(),
                                extensionMenuAction = "",
                                mailBackupHistoryTitle = "",
                                mailBackupHistoryItems = emptyList()
                            )
                            refreshSettingsFromServer(showErrors = false)
                        }
                        .onFailure { error ->
                            val userMessage = when ((error as? HttpException)?.code()) {
                                401 -> "HTTP 401: нет доступа к расширениям. Проверь Base URL и токен в Настройках"
                                403 -> "HTTP 403: нет прав на команды расширений"
                                else -> formatNetworkError(error)
                            }
                            state = state.copy(
                                isLoading = false,
                                message = userMessage,
                                messageSource = "global",
                                extensionMenuOptions = emptyList(),
                                extensionMenuAction = "",
                                mailBackupHistoryTitle = "",
                                mailBackupHistoryItems = emptyList()
                            )
                        }
                }
            }
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching {
                if (action == "send_morning_report") {
                    runMorningReportControlAction()
                } else {
                    currentApi().runControlAction(ControlActionRequest(action))
                }
            }
                .onSuccess { response ->
                    val actionMessage = response.message ?: response.result ?: "Команда отправлена"
                    if (action == "send_morning_report") {
                        saveMorningReport(actionMessage)
                    }
                    state = state.copy(
                        isLoading = false,
                        message = actionMessage,
                        messageSource = if (action == "send_morning_report") "morning_report" else "global",
                        extensionMenuOptions = emptyList(),
                        extensionMenuAction = "",
                        mailBackupHistoryTitle = "",
                        mailBackupHistoryItems = emptyList()
                    )
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error ->
                    val userMessage = when ((error as? HttpException)?.code()) {
                        401 -> "HTTP 401: нет доступа к командам управления. Проверь Base URL и токен в Настройках"
                        403 -> "HTTP 403: нет прав на команды управления"
                        else -> formatNetworkError(error)
                    }
                    state = state.copy(
                        isLoading = false,
                        message = userMessage,
                        messageSource = if (action == "send_morning_report") "morning_report" else "global",
                        extensionMenuOptions = emptyList(),
                        extensionMenuAction = "",
                        mailBackupHistoryTitle = "",
                        mailBackupHistoryItems = emptyList()
                    )
                }
        }
    }

    private fun parseMailBackupHistory(message: String): MailBackupHistory? {
        if (message.isBlank()) return null
        val lines = message.lines().map { it.trim() }.filter { it.isNotBlank() }
        if (lines.isEmpty()) return null

        val normalizedLines = lines.map { line ->
            line
                .replace("*", "")
                .replace("\\_", "_")
                .replace("\\-", "-")
                .replace("\\(", "(")
                .replace("\\)", ")")
        }
        val title = normalizedLines.firstOrNull {
            it.contains("бэкап", ignoreCase = true) && it.contains("почт", ignoreCase = true)
        } ?: normalizedLines.first()
        val items = normalizedLines.drop(1).mapNotNull { line ->
            val match = mailBackupHistoryRegex.matchEntire(line) ?: return@mapNotNull null
            MailBackupHistoryItem(
                statusIcon = match.groupValues[1].trim(),
                size = match.groupValues[2].trim(),
                path = match.groupValues[3].trim(),
                relativeTime = match.groupValues[4].trim()
            )
        }

        return if (items.isNotEmpty()) MailBackupHistory(title = title, items = items) else null
    }

    private suspend fun runMorningReportControlAction() =
        runCatching {
            currentApi().runControlAction(ControlActionRequest(morningReportActions.first()))
        }.recoverCatching {
            currentApi().runControlAction(ControlActionRequest(morningReportActions.last()))
        }.getOrThrow()

    fun addTelegramChatId() {
        val chatId = state.newTelegramChatIdInput.trim()
        if (chatId.isBlank()) {
            state = state.copy(message = "Введи chat_id для добавления")
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
                        message = "Chat ID добавлен"
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
                        message = "Chat ID удален"
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
            state = state.copy(message = "Для Windows-учетки нужны username и password")
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
                        message = "Windows-учетка добавлена"
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
                        message = "Windows-учетка удалена"
                    )
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    fun createWindowsType() {
        val typeName = state.createWindowsTypeInput.trim()
        if (typeName.isBlank()) {
            state = state.copy(message = "Введите имя нового типа")
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
                        message = "Тип создан"
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
            state = state.copy(message = "Заполни старое и новое имя типа")
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
                        message = "Тип переименован"
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
            state = state.copy(message = "Укажи source/target типы (и они должны отличаться)")
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
                        message = "Типы объединены"
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
            state = state.copy(message = "Укажи тип для удаления")
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
                        message = "Тип удален"
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
            message = "Режим редактирования: ${server.ip}"
        )
    }

    fun cancelServerEdit() {
        state = state.copy(
            serverEditIp = "",
            serverIpInput = "",
            serverNameInput = "",
            serverTypeInput = "",
            serverTimeoutInput = "30",
            message = "Редактирование сервера отменено"
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
            state = state.copy(message = "Введите IP сервера")
            return
        }
        if (name.isBlank()) {
            state = state.copy(message = "Введите имя сервера")
            return
        }
        if (type == null) {
            state = state.copy(message = "Тип сервера: rdp / ssh / ping")
            return
        }
        if (timeout < 1) {
            state = state.copy(message = "timeout должен быть >= 1")
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
                        message = if (isEdit) "Сервер обновлен" else "Сервер добавлен"
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
                        message = "Сервер удален"
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
                        message = if (enabled) "Мониторинг включен" else "Мониторинг приостановлен"
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
            runCatching { currentApi().updateMonitoringSettings(request) }
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
        if (!hasAnyValue(telegramToken, telegramChatId) && state.telegramChatIds.isEmpty()) {
            state = state.copy(message = "Заполни хотя бы одно поле bot")
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
            runCatching { currentApi().updateTimeSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Временные настройки обновлены")
                    refreshSettingsFromServer(showErrors = false)
                    rescheduleBackgroundWorkers()
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
            state = state.copy(message = "Заполни хотя бы одно поле auth")
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
            state = state.copy(message = it.message ?: "Ошибка в полях auth")
            return
        }

        viewModelScope.launch {
            state = state.copy(isLoading = true)
            runCatching { currentApi().updateAuthSettings(request) }
                .onSuccess {
                    state = state.copy(isLoading = false, message = "Auth-настройки обновлены")
                    refreshSettingsFromServer(showErrors = false)
                }
                .onFailure { error -> state = state.copy(isLoading = false, message = formatNetworkError(error)) }
        }
    }

    private fun rescheduleBackgroundWorkers() {
        val notificationsEnabled = state.morningReportNotificationsEnabled && state.token.isNotBlank()
        val scheduleTime = state.metricsTimeInput.ifBlank { "08:30" }

        MorningReportWorker.schedule(
            context = appContext,
            timeRaw = scheduleTime,
            enabled = notificationsEnabled
        )
        ServerDownAlertWorker.schedule(
            context = appContext,
            enabled = notificationsEnabled
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
    val extensionMenuOptions: List<MenuOption> = emptyList(),
    val extensionMenuAction: String = "",
    val extensionSettingsMenuOptions: List<MenuOption> = emptyList(),
    val extensionSettingsMenuAction: String = "",
    val backupProxmoxHasProblemItems: Boolean = false,
    val backupDatabasesHasProblemItems: Boolean = false,
    val mailBackupHistoryTitle: String = "",
    val mailBackupHistoryItems: List<MailBackupHistoryItem> = emptyList(),
    val servers: List<ServerAvailability> = emptyList(),
    val message: String = "",
    val messageSource: String = "global",
    val availabilityServerMessageTarget: String = "",
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
    val extensions: List<ExtensionItem> = emptyList(),
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
    val projectVersion: String = "",
    val installedVersion: String = "",
    val isUpdateRequired: Boolean = false,
    val minSupportedVersion: String = "",
    val latestVersion: String = "",
    val apkDownloadUrl: String = "",
    val updateMessage: String = "",
    val monitoringStatusText: String = "Неизвестно",
    val silentStatusText: String = "Неизвестно"
)

data class MailBackupHistoryItem(
    val statusIcon: String,
    val size: String,
    val path: String,
    val relativeTime: String
)

private data class MailBackupHistory(
    val title: String,
    val items: List<MailBackupHistoryItem>
)
