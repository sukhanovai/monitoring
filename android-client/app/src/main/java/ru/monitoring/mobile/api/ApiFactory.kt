package ru.monitoring.mobile.api

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import java.util.UUID
import java.util.concurrent.TimeUnit

object ApiFactory {
    private const val BASE_URL = "https://api.202020.ru:8443/"

    fun createApi(tokenProvider: () -> String): MonitoringApi {
        val authInterceptor = Interceptor { chain ->
            val token = tokenProvider().trim()
            val requestBuilder = chain.request().newBuilder()
                .addHeader("X-Request-ID", UUID.randomUUID().toString())

            if (token.isNotBlank()) {
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }

            chain.proceed(requestBuilder.build())
        }

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
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
}
