package ru.monitoring.mobile.api

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import ru.monitoring.mobile.logging.ConnectionLogger
import java.io.IOException
import java.net.SocketTimeoutException
import java.util.Locale
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.UUID
import java.util.concurrent.TimeUnit

object ApiFactory {
    private const val BASE_URL = "https://api.202020.ru:8443/"
    private const val AVAILABILITY_ENDPOINT = "/v1/monitoring/availability"

    fun createApi(tokenProvider: () -> String): MonitoringApi {
        val authInterceptor = Interceptor { chain ->
            val token = tokenProvider().trim()
            val requestBuilder = chain.request().newBuilder()
            val existingRequestId = chain.request().header("X-Request-ID")
            if (existingRequestId.isNullOrBlank()) {
                requestBuilder.addHeader("X-Request-ID", UUID.randomUUID().toString())
            }

            if (token.isNotBlank()) {
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }

            chain.proceed(requestBuilder.build())
        }

        val availabilityLoggingInterceptor = Interceptor { chain ->
            val request = chain.request()
            val path = request.url.encodedPath
            val requestId = request.header("X-Request-ID").orEmpty()
            val endpoint = if (path.startsWith("/api/")) path.removePrefix("/api") else path
            val isAvailabilityRequest = endpoint == AVAILABILITY_ENDPOINT

            val startedAt = System.nanoTime()
            if (isAvailabilityRequest) {
                ConnectionLogger.info(
                    event = "availability_all_request_sent",
                    fields = mapOf(
                        "request_id" to requestId,
                        "base_url_host" to request.url.host,
                        "endpoint" to endpoint,
                        "http_method" to request.method,
                        "token_present" to !tokenProvider().trim().isBlank(),
                        "network_type" to "unknown"
                    )
                )
            }

            try {
                val response = chain.proceed(request)
                if (isAvailabilityRequest) {
                    ConnectionLogger.info(
                        event = "availability_all_response_received",
                        fields = mapOf(
                            "request_id" to requestId,
                            "base_url_host" to request.url.host,
                            "endpoint" to endpoint,
                            "http_method" to request.method,
                            "http_status" to response.code,
                            "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                            "network_type" to "unknown"
                        )
                    )
                }
                response
            } catch (error: IOException) {
                if (isAvailabilityRequest) {
                    ConnectionLogger.error(
                        event = "availability_all_failed",
                        fields = mapOf(
                            "request_id" to requestId,
                            "base_url_host" to request.url.host,
                            "endpoint" to endpoint,
                            "http_method" to request.method,
                            "duration_ms" to ((System.nanoTime() - startedAt) / 1_000_000),
                            "network_type" to "unknown",
                            "error_type" to mapErrorType(error),
                            "error_message_short" to ConnectionLogger.shortErrorMessage(error.message)
                        )
                    )
                }
                throw error
            }
        }

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(availabilityLoggingInterceptor)
            .addInterceptor(logging)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create())
            .build()
            .create(MonitoringApi::class.java)
    }

    private fun mapErrorType(error: Throwable): String {
        return when (error) {
            is SocketTimeoutException -> "TIMEOUT"
            is javax.net.ssl.SSLException -> "SSL"
            is IOException -> {
                val message = error.message?.lowercase(Locale.US).orEmpty()
                if (message.contains("unreachable") || message.contains("failed to connect")) {
                    "NO_NETWORK"
                } else {
                    "UNKNOWN"
                }
            }

            else -> "UNKNOWN"
        }
    }
}
