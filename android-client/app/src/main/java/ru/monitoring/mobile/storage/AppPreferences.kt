package ru.monitoring.mobile.storage

import android.content.Context
import java.util.UUID

class AppPreferences(context: Context) {
    private val prefs = context.getSharedPreferences("monitoring_mobile", Context.MODE_PRIVATE)

    var apiToken: String
        get() = prefs.getString(KEY_API_TOKEN, "") ?: ""
        set(value) {
            prefs.edit().putString(KEY_API_TOKEN, value).apply()
        }

    var apiBaseUrl: String
        get() = prefs.getString(KEY_API_BASE_URL, DEFAULT_API_BASE_URL) ?: DEFAULT_API_BASE_URL
        set(value) {
            prefs.edit().putString(KEY_API_BASE_URL, value).apply()
        }

    val deviceId: String
        get() {
            val existing = prefs.getString(KEY_DEVICE_ID, null)?.trim().orEmpty()
            if (existing.isNotBlank()) return existing
            val generated = UUID.randomUUID().toString()
            prefs.edit().putString(KEY_DEVICE_ID, generated).apply()
            return generated
        }

    companion object {
        private const val KEY_API_TOKEN = "api_token"
        private const val KEY_API_BASE_URL = "api_base_url"
        private const val KEY_DEVICE_ID = "device_id"
        private const val DEFAULT_API_BASE_URL = "https://api.202020.ru:8443/"
    }
}
