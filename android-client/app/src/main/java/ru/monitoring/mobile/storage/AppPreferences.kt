package ru.monitoring.mobile.storage

import android.content.Context

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

    companion object {
        private const val KEY_API_TOKEN = "api_token"
        private const val KEY_API_BASE_URL = "api_base_url"
        private const val DEFAULT_API_BASE_URL = "https://api.202020.ru:8443/"
    }
}
