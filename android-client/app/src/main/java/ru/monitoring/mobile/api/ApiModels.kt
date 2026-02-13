package ru.monitoring.mobile.api

import com.squareup.moshi.Json

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

data class AvailabilityResponse(
    val servers: List<ServerAvailability> = emptyList(),
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
    val accepted: Boolean,
    val message: String,
    @Json(name = "queued_job_id") val queuedJobId: String?
)

data class SettingsMonitoringRequest(
    @Json(name = "check_interval_sec") val checkIntervalSec: Int? = null,
    @Json(name = "timeout_sec") val timeoutSec: Int? = null,
    @Json(name = "max_downtime_sec") val maxDowntimeSec: Int? = null
)

data class SettingsMonitoringResponse(
    @Json(name = "check_interval_sec") val checkIntervalSec: Int,
    @Json(name = "timeout_sec") val timeoutSec: Int,
    @Json(name = "max_downtime_sec") val maxDowntimeSec: Int
)

data class ProxmoxBackupsResponse(
    val backups: List<BackupItem> = emptyList()
)

data class BackupItem(
    val id: String = "",
    val source: String = "",
    val status: String = "unknown",
    @Json(name = "created_at") val createdAt: String? = null,
    @Json(name = "size_human") val sizeHuman: String? = null,
    val message: String? = null
)
