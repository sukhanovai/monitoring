package ru.monitoring.mobile.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST

interface MonitoringApi {
    @GET("v1/monitoring/availability?scope=all")
    suspend fun getAvailability(): AvailabilityResponse

    @POST("v1/control/actions")
    suspend fun runControlAction(@Body request: ControlActionRequest): ControlActionResult

    @PATCH("v1/settings/monitoring")
    suspend fun updateMonitoringSettings(
        @Body request: SettingsMonitoringRequest
    ): SettingsMonitoringResponse

    @PATCH("v1/settings/bot")
    suspend fun updateBotSettings(
        @Body request: SettingsBotRequest
    ): SettingsBotResponse

    @PATCH("v1/settings/time")
    suspend fun updateTimeSettings(
        @Body request: SettingsTimeRequest
    ): SettingsTimeResponse

    @PATCH("v1/settings/auth")
    suspend fun updateAuthSettings(
        @Body request: SettingsAuthRequest
    ): SettingsAuthResponse
}
