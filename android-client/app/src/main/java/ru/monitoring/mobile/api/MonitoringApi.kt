package ru.monitoring.mobile.api

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.Path
import retrofit2.http.POST
import retrofit2.http.Query

interface MonitoringApi {
    @POST("v1/auth/token")
    suspend fun exchangeAuthToken(@Body request: AuthTokenExchangeRequest): AuthTokenExchangeResponse

    @POST("v1/auth/token/reissue")
    suspend fun reissueAuthToken(@Body request: AuthTokenExchangeRequest): AuthTokenExchangeResponse

    @GET("v1/monitoring/availability?scope=all")
    suspend fun getAvailability(): AvailabilityResponse

    @POST("v1/control/actions")
    suspend fun runControlAction(@Body request: ControlActionRequest): ControlActionResult

    @GET("v1/control/status")
    suspend fun getControlStatus(): ControlStatusResponse

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

    @POST("v1/settings/bot/chats")
    suspend fun addBotChat(@Body request: BotChatRequest): SettingsBotResponse

    @DELETE("v1/settings/bot/chats/{chatId}")
    suspend fun removeBotChat(@Path("chatId") chatId: String): SettingsBotResponse

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

    @GET("v1/settings/auth/windows-credentials")
    suspend fun getWindowsCredentials(): WindowsCredentialsResponse

    @POST("v1/settings/auth/windows-credentials")
    suspend fun addWindowsCredential(
        @Body request: AddWindowsCredentialRequest
    ): WindowsCredentialsResponse

    @DELETE("v1/settings/auth/windows-credentials/{credId}")
    suspend fun deleteWindowsCredential(@Path("credId") credId: Int): WindowsCredentialsResponse

    @GET("v1/settings/auth/windows-types")
    suspend fun getWindowsTypes(): WindowsTypesResponse

    @POST("v1/settings/auth/windows-types")
    suspend fun createWindowsType(@Body request: CreateWindowsTypeRequest): WindowsTypesResponse

    @PATCH("v1/settings/auth/windows-types/{typeName}")
    suspend fun renameWindowsType(
        @Path("typeName") typeName: String,
        @Body request: RenameWindowsTypeRequest
    ): WindowsTypesResponse

    @POST("v1/settings/auth/windows-types/merge")
    suspend fun mergeWindowsTypes(@Body request: MergeWindowsTypesRequest): WindowsTypesResponse

    @DELETE("v1/settings/auth/windows-types/{typeName}")
    suspend fun deleteWindowsType(
        @Path("typeName") typeName: String,
        @Query("target_type") targetType: String = "default"
    ): WindowsTypesResponse

    @GET("v1/settings/servers")
    suspend fun getServersSettings(): ServersSettingsResponse

    @POST("v1/settings/servers")
    suspend fun addServer(@Body request: AddServerRequest): ServersSettingsResponse

    @PATCH("v1/settings/servers/{ip}")
    suspend fun updateServer(
        @Path("ip") ip: String,
        @Body request: UpdateServerRequest
    ): ServersSettingsResponse

    @PATCH("v1/settings/servers/{ip}/enabled")
    suspend fun setServerEnabled(
        @Path("ip") ip: String,
        @Body request: ToggleServerEnabledRequest
    ): ServersSettingsResponse

    @DELETE("v1/settings/servers/{ip}")
    suspend fun deleteServer(@Path("ip") ip: String): ServersSettingsResponse
}
