package ru.monitoring.mobile.api

import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.UUID
import java.util.concurrent.TimeUnit

object ApiFactory {
    private const val RETRY_HEADER = "X-Token-Retry"

    private val moshi: com.squareup.moshi.Moshi = com.squareup.moshi.Moshi.Builder()
        .add(com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory())
        .build()

    private fun normalizeToken(raw: String): String = raw
        .trim()
        .removePrefix("Bearer ")
        .removePrefix("bearer ")
        .replace("\\s+".toRegex(), "")
        .trim()

    private fun createHttpClient(
        tokenProvider: () -> String,
        tokenRefresher: (() -> String?)?,
    ): OkHttpClient {
        val authInterceptor = Interceptor { chain ->
            val normalizedToken = normalizeToken(tokenProvider())

            val requestBuilder = chain.request().newBuilder()
                .addHeader("X-Request-ID", UUID.randomUUID().toString())

            if (normalizedToken.isNotBlank()) {
                // .header() (replace), а не .addHeader(): на повторе после
                // Authenticator запрос уже несёт свежий Authorization — дубль
                // заголовка ломает авторизацию на сервере.
                requestBuilder.header("Authorization", "Bearer $normalizedToken")
            }

            chain.proceed(requestBuilder.build())
        }

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val builder = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)

        if (tokenRefresher != null) {
            builder.authenticator(TokenAuthenticator(tokenRefresher))
        }

        return builder.build()
    }

    // Срабатывает автоматически на ответ 401. Переобменивает bootstrap-токен на
    // свежий session-токен (tokenRefresher сам его персистит) и повторяет исходный
    // запрос с новым токеном. Гард от бесконечного цикла: один повтор на запрос.
    private class TokenAuthenticator(
        private val tokenRefresher: () -> String?,
    ) : Authenticator {
        override fun authenticate(route: Route?, response: Response): Request? {
            if (response.request.header(RETRY_HEADER) != null) return null
            if (responseCount(response) >= 2) return null

            val usedToken = response.request.header("Authorization")
                ?.let { normalizeToken(it) }
                .orEmpty()

            val newToken = tokenRefresher()?.let { normalizeToken(it) }.orEmpty()
            if (newToken.isBlank() || newToken == usedToken) return null

            return response.request.newBuilder()
                .header("Authorization", "Bearer $newToken")
                .header(RETRY_HEADER, "1")
                .build()
        }

        private fun responseCount(response: Response): Int {
            var count = 1
            var prior = response.priorResponse
            while (prior != null) {
                count += 1
                prior = prior.priorResponse
            }
            return count
        }
    }

    private fun normalizeBaseUrl(rawUrl: String): String {
        val trimmed = rawUrl.trim()
        if (trimmed.isBlank()) return "https://api.202020.ru:8443/"
        return if (trimmed.endsWith('/')) trimmed else "$trimmed/"
    }

    fun createApi(
        tokenProvider: () -> String,
        baseUrlProvider: () -> String,
        tokenRefresher: (() -> String?)? = null,
    ): MonitoringApi {
        val client = createHttpClient(tokenProvider, tokenRefresher)

        return Retrofit.Builder()
            .baseUrl(normalizeBaseUrl(baseUrlProvider()))
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(MonitoringApi::class.java)
    }
}
