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

    @GET("v1/settings/monitoring")
    suspend fun getMonitoringSettings(): SettingsMonitoringResponse

    @PATCH("v1/settings/monitoring")
    suspend fun updateMonitoringSettings(
        @Body request: SettingsMonitoringRequest
    ): SettingsMonitoringResponse

    @GET("v1/settings/bot")
    suspend fun getBotSettings(): SettingsBotResponse

    @PATCH("v1/settings/bot")
    suspend fun updateBotSettings(
        @Body request: SettingsBotRequest
    ): SettingsBotResponse

    @GET("v1/settings/time")
    suspend fun getTimeSettings(): SettingsTimeResponse

    @PATCH("v1/settings/time")
    suspend fun updateTimeSettings(
        @Body request: SettingsTimeRequest
    ): SettingsTimeResponse

    @GET("v1/settings/auth")
    suspend fun getAuthSettings(): SettingsAuthResponse

    @PATCH("v1/settings/auth")
    suspend fun updateAuthSettings(
        @Body request: SettingsAuthRequest
    ): SettingsAuthResponse
}
