package ru.monitoring.mobile.api

class MonitoringRepository(
    private val api: MonitoringApi
) {
    suspend fun getAvailability(): Result<AvailabilityResponse> = runCatchingEnvelope {
        api.getAvailability()
    }

    suspend fun runAction(action: String): Result<ControlActionResult> = runCatchingEnvelope {
        api.runControlAction(ControlActionRequest(action))
    }

    suspend fun updateMonitoringSettings(request: SettingsMonitoringRequest): Result<SettingsMonitoringResponse> = runCatchingEnvelope {
        api.updateMonitoringSettings(request)
    }

    suspend fun getProxmoxBackups(from: String, to: String): Result<ProxmoxBackupsResponse> = runCatchingEnvelope {
        api.getProxmoxBackups(from = from, to = to)
    }

    private inline fun <T> runCatchingEnvelope(call: () -> ApiEnvelope<T>): Result<T> {
        return runCatching { call() }.fold(
            onSuccess = { envelope ->
                envelope.data?.let { Result.success(it) }
                    ?: Result.failure(IllegalStateException(envelope.error?.message ?: "Пустой ответ API"))
            },
            onFailure = { Result.failure(it) }
        )
    }
}
