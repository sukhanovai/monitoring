package ru.monitoring.mobile.api

import android.util.Log
import kotlinx.coroutines.runBlocking
import ru.monitoring.mobile.storage.AppPreferences

// Единая точка авто-восстановления session-токена. На 401 (reason=invalid/expired
// после передеплоя сервера, ротации MOBILE_AUTH_SECRET или отзыва токена) берёт
// сохранённый bootstrap-токен, переобменивает его через /v1/auth/token/reissue на
// свежий session-токен и персистит в preferences.apiToken. Дедуп общий для
// foreground и фоновых воркеров: параллельные 401 не плодят лишние reissue,
// которые отозвали бы только что выданный токен.
object MobileTokenRefresher {
    private const val TAG = "MobileTokenRefresher"
    private const val DEDUP_MS = 10_000L

    private val lock = Any()

    @Volatile
    private var lastRefreshAtMs: Long = 0L

    private fun normalize(raw: String): String = raw
        .trim()
        .removePrefix("Bearer ")
        .removePrefix("bearer ")
        .replace("\\s+".toRegex(), "")
        .trim()

    // Лямбда для ApiFactory.createApi(tokenRefresher = ...). Возвращает свежий
    // session-токен или null, если bootstrap не сохранён / reissue не удался.
    fun forPreferences(preferences: AppPreferences): () -> String? = refresher@{
        val bootstrap = normalize(preferences.bootstrapToken)
        if (bootstrap.isBlank()) {
            Log.w(TAG, "skip refresh: bootstrap token is not saved")
            return@refresher null
        }

        synchronized(lock) {
            if (System.currentTimeMillis() - lastRefreshAtMs < DEDUP_MS) {
                val current = normalize(preferences.apiToken)
                if (current.isNotBlank()) return@refresher current
            }

            val baseUrl = preferences.apiBaseUrl
            val newToken = runCatching {
                runBlocking {
                    // Без tokenRefresher → без Authenticator → 401 на самом reissue
                    // не зациклит вызов на себя.
                    ApiFactory.createApi(
                        tokenProvider = { bootstrap },
                        baseUrlProvider = { baseUrl }
                    ).reissueAuthToken(
                        AuthTokenExchangeRequest(
                            deviceId = preferences.deviceId,
                            subject = "android-${preferences.deviceId.take(8)}",
                            reissue = true
                        )
                    ).accessToken
                }
            }.getOrElse { error ->
                Log.e(TAG, "reissue failed: ${error.message}", error)
                null
            }?.let { normalize(it) }.orEmpty()

            if (newToken.isBlank()) return@refresher null

            preferences.apiToken = newToken
            lastRefreshAtMs = System.currentTimeMillis()
            Log.i(TAG, "session token reissued from bootstrap")
            newToken
        }
    }
}
