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
    @Json(name = "server_id") val serverId: String,
    val status: String,
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

data class Summary(
    val up: Int = 0,
    val down: Int = 0,
    val unknown: Int = 0
)

data class ControlActionRequest(
    val action: String
)

data class ControlActionResult(
    @Json(name = "request_id") val requestId: String? = null,
    val action: String? = null,
    val result: String? = null,
    val accepted: Boolean? = null,
    val message: String? = null,
    @Json(name = "queued_job_id") val queuedJobId: String? = null
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
