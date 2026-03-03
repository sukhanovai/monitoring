package ru.monitoring.mobile.api

import com.squareup.moshi.Json

/**
 * Модели сделаны толерантными к двум форматам API:
 * 1) старый: envelope { data, error }
 * 2) прямой ответ: request_id + payload поля в корне.
 */
data class ApiEnvelope<T>(
    val data: T? = null,
    val error: ApiError? = null
)

data class ApiError(
    val code: String,
    val message: String,
    @Json(name = "request_id") val requestId: String? = null
)

data class ServerAvailability(
    val id: String,
    val name: String,
    val status: String,
    @Json(name = "last_checked_at") val lastCheckedAt: String?
)

data class AvailabilityItem(
    @Json(name = "server_id") val serverId: String? = null,
    @Json(name = "server_name") val serverName: String? = null,
    val name: String? = null,
    val ip: String? = null,
    val status: String? = null,
    @Json(name = "checked_at") val checkedAt: String? = null,
    @Json(name = "error_message") val errorMessage: String? = null
)

data class AvailabilityResponse(
    @Json(name = "request_id") val requestId: String? = null,
    @Json(name = "generated_at") val generatedAt: String? = null,
    val servers: List<ServerAvailability> = emptyList(),
    val items: List<AvailabilityItem> = emptyList(),
    val summary: Summary = Summary()
)

data class ResourceSnapshot(
    val cpu: Int? = null,
    val ram: Int? = null,
    val disk: Int? = null,
    @Json(name = "access_method") val accessMethod: String? = null,
    val timestamp: String? = null
)

data class ServerResourcesResponse(
    @Json(name = "request_id") val requestId: String? = null,
    @Json(name = "server_id") val serverId: String? = null,
    @Json(name = "server_name") val serverName: String? = null,
    @Json(name = "server_ip") val serverIp: String? = null,
    val resources: ResourceSnapshot? = null,
    val message: String? = null
)

data class Summary(
    val up: Int = 0,
    val down: Int = 0,
    val unknown: Int = 0
)

data class ControlActionRequest(
    val action: String
)

data class AuthTokenExchangeRequest(
    @Json(name = "device_id") val deviceId: String? = null,
    @Json(name = "subject") val subject: String? = null,
    @Json(name = "reissue") val reissue: Boolean? = true
)

data class AuthTokenExchangeResponse(
    @Json(name = "access_token") val accessToken: String? = null,
    @Json(name = "token_type") val tokenType: String? = null,
    @Json(name = "expires_in") val expiresIn: Int? = null,
    @Json(name = "expires_at") val expiresAt: String? = null,
    @Json(name = "scope") val scope: String? = null,
    @Json(name = "issued_at") val issuedAt: String? = null,
    @Json(name = "subject") val subject: String? = null,
    @Json(name = "auth_type") val authType: String? = null
)

data class ControlActionResult(
    @Json(name = "request_id") val requestId: String? = null,
    val action: String? = null,
    val result: String? = null,
    val accepted: Boolean? = null,
    val message: String? = null,
    @Json(name = "queued_job_id") val queuedJobId: String? = null
)

data class ControlStatusResponse(
    @Json(name = "request_id") val requestId: String? = null,
    @Json(name = "monitoring_active") val monitoringActive: Boolean? = null,
    @Json(name = "monitoring_status") val monitoringStatus: String? = null,
    @Json(name = "silent_active") val silentActive: Boolean? = null,
    @Json(name = "silent_mode") val silentMode: String? = null,
    @Json(name = "silent_override") val silentOverride: Boolean? = null
)

data class SettingsMonitoringRequest(
    @Json(name = "check_interval_sec") val checkIntervalSec: Int? = null,
    @Json(name = "timeout_sec") val timeoutSec: Int? = null,
    @Json(name = "max_downtime_sec") val maxDowntimeSec: Int? = null
)

data class SettingsMonitoringData(
    @Json(name = "check_interval_sec") val checkIntervalSec: Int,
    @Json(name = "timeout_sec") val timeoutSec: Int,
    @Json(name = "max_downtime_sec") val maxDowntimeSec: Int
)

data class SettingsMonitoringResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val settings: SettingsMonitoringData? = null,
    @Json(name = "check_interval_sec") val checkIntervalSec: Int? = null,
    @Json(name = "timeout_sec") val timeoutSec: Int? = null,
    @Json(name = "max_downtime_sec") val maxDowntimeSec: Int? = null
)

data class SettingsBotRequest(
    @Json(name = "telegram_bot_token") val telegramBotToken: String? = null,
    @Json(name = "telegram_chat_id") val telegramChatId: String? = null,
    @Json(name = "telegram_chat_ids") val telegramChatIds: List<String>? = null
)

data class SettingsBotData(
    @Json(name = "telegram_chat_id") val telegramChatId: String? = null,
    @Json(name = "telegram_chat_ids") val telegramChatIds: List<String>? = null,
    @Json(name = "masked_token") val maskedToken: String? = null,
    @Json(name = "telegram_bot_token") val telegramBotToken: String? = null
)

data class SettingsBotResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val settings: SettingsBotData? = null
)

data class SettingsTimeRequest(
    @Json(name = "quiet_start") val quietStart: String? = null,
    @Json(name = "quiet_end") val quietEnd: String? = null,
    @Json(name = "metrics_collection_time") val metricsCollectionTime: String? = null
)

data class SettingsTimeData(
    @Json(name = "quiet_start") val quietStart: String? = null,
    @Json(name = "quiet_end") val quietEnd: String? = null,
    @Json(name = "metrics_collection_time") val metricsCollectionTime: String? = null
)

data class SettingsTimeResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val settings: SettingsTimeData? = null,
    @Json(name = "quiet_start") val quietStart: String? = null,
    @Json(name = "quiet_end") val quietEnd: String? = null,
    @Json(name = "metrics_collection_time") val metricsCollectionTime: String? = null
)

data class SettingsAuthRequest(
    @Json(name = "auth_mode") val authMode: String? = null,
    @Json(name = "ssh_username") val sshUsername: String? = null,
    @Json(name = "ssh_port") val sshPort: Int? = null,
    @Json(name = "ssh_key_path") val sshKeyPath: String? = null,
    @Json(name = "windows_username") val windowsUsername: String? = null,
    @Json(name = "ssh_password") val sshPassword: String? = null,
    @Json(name = "windows_password") val windowsPassword: String? = null
)

data class SettingsAuthData(
    @Json(name = "auth_mode") val authMode: String? = null,
    @Json(name = "ssh_username") val sshUsername: String? = null,
    @Json(name = "ssh_port") val sshPort: Int? = null,
    @Json(name = "ssh_key_path") val sshKeyPath: String? = null,
    @Json(name = "windows_username") val windowsUsername: String? = null,
    @Json(name = "masked_ssh_password") val maskedSshPassword: String? = null,
    @Json(name = "masked_windows_password") val maskedWindowsPassword: String? = null,
    @Json(name = "windows_credentials") val windowsCredentials: List<WindowsCredential> = emptyList(),
    @Json(name = "windows_server_types") val windowsServerTypes: List<String> = emptyList()
)

data class SettingsAuthResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val settings: SettingsAuthData? = null,
    @Json(name = "auth_mode") val authMode: String? = null,
    @Json(name = "ssh_username") val sshUsername: String? = null,
    @Json(name = "ssh_port") val sshPort: Int? = null,
    @Json(name = "ssh_key_path") val sshKeyPath: String? = null,
    @Json(name = "windows_username") val windowsUsername: String? = null,
    @Json(name = "ssh_password") val sshPassword: String? = null,
    @Json(name = "windows_password") val windowsPassword: String? = null
)

data class BotChatRequest(
    @Json(name = "chat_id") val chatId: String
)

data class WindowsCredential(
    val id: Int? = null,
    val username: String? = null,
    val password: String? = null,
    @Json(name = "server_type") val serverType: String? = null,
    val priority: Int? = null,
    val enabled: Int? = null
)

data class WindowsCredentialsResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val items: List<WindowsCredential> = emptyList(),
    @Json(name = "server_types") val serverTypes: List<String> = emptyList()
)

data class AddWindowsCredentialRequest(
    val username: String,
    val password: String,
    @Json(name = "server_type") val serverType: String,
    val priority: Int = 0
)

data class WindowsTypeItem(
    val name: String,
    val total: Int,
    val active: Int,
    val inactive: Int
)

data class WindowsTypesSummary(
    @Json(name = "types_count") val typesCount: Int = 0,
    @Json(name = "credentials_count") val credentialsCount: Int = 0
)

data class WindowsTypesResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val types: List<WindowsTypeItem> = emptyList(),
    val summary: WindowsTypesSummary = WindowsTypesSummary()
)

data class CreateWindowsTypeRequest(
    val name: String
)

data class RenameWindowsTypeRequest(
    @Json(name = "new_name") val newName: String
)

data class MergeWindowsTypesRequest(
    @Json(name = "source_type") val sourceType: String,
    @Json(name = "target_type") val targetType: String
)

data class ManagedServer(
    val ip: String,
    val name: String,
    @Json(name = "type") val type: String,
    val timeout: Int? = null,
    val enabled: Boolean? = true
)

data class ServersSummary(
    val total: Int = 0,
    val enabled: Int = 0,
    val disabled: Int = 0
)

data class ServersSettingsResponse(
    @Json(name = "request_id") val requestId: String? = null,
    val items: List<ManagedServer> = emptyList(),
    val summary: ServersSummary = ServersSummary()
)

data class AddServerRequest(
    val ip: String,
    val name: String,
    @Json(name = "type") val type: String,
    val timeout: Int = 30,
    val enabled: Boolean = true
)

data class UpdateServerRequest(
    val name: String? = null,
    @Json(name = "type") val type: String? = null,
    val timeout: Int? = null,
    val enabled: Boolean? = null
)

data class ToggleServerEnabledRequest(
    val enabled: Boolean
)
