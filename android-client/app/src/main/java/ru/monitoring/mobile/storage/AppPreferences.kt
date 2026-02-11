package ru.monitoring.mobile.storage

import android.content.Context

class AppPreferences(context: Context) {
    private val prefs = context.getSharedPreferences("monitoring_mobile", Context.MODE_PRIVATE)

    var apiToken: String
        get() = prefs.getString(KEY_API_TOKEN, "") ?: ""
        set(value) {
            prefs.edit().putString(KEY_API_TOKEN, value).apply()
        }

    companion object {
        private const val KEY_API_TOKEN = "api_token"
    }
}
