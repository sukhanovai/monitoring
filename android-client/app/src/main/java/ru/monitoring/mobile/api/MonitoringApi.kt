package ru.monitoring.mobile.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST

interface MonitoringApi {
    @GET("v1/monitoring/availability?scope=all")
    suspend fun getAvailability(): ApiEnvelope<AvailabilityResponse>

    @POST("v1/control/actions")
    suspend fun runControlAction(@Body request: ControlActionRequest): ApiEnvelope<ControlActionResult>

    @PATCH("v1/settings/monitoring")
    suspend fun updateMonitoringSettings(
        @Body request: SettingsMonitoringRequest
    ): ApiEnvelope<SettingsMonitoringResponse>
}
