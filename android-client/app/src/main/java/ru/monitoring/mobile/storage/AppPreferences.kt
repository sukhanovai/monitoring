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

    var themeMode: String
        get() = prefs.getString(KEY_THEME_MODE, DEFAULT_THEME_MODE) ?: DEFAULT_THEME_MODE
        set(value) {
            prefs.edit().putString(KEY_THEME_MODE, value).apply()
        }

    var morningReportNotificationsEnabled: Boolean
        get() = prefs.getBoolean(KEY_MORNING_REPORT_NOTIFICATIONS_ENABLED, true)
        set(value) {
            prefs.edit().putBoolean(KEY_MORNING_REPORT_NOTIFICATIONS_ENABLED, value).apply()
        }

    var morningReportText: String
        get() = prefs.getString(KEY_MORNING_REPORT_TEXT, "") ?: ""
        set(value) {
            prefs.edit().putString(KEY_MORNING_REPORT_TEXT, value).apply()
        }

    var morningReportReceivedAt: String
        get() = prefs.getString(KEY_MORNING_REPORT_RECEIVED_AT, "") ?: ""
        set(value) {
            prefs.edit().putString(KEY_MORNING_REPORT_RECEIVED_AT, value).apply()
        }

    var morningReportUnread: Boolean
        get() = prefs.getBoolean(KEY_MORNING_REPORT_UNREAD, false)
        set(value) {
            prefs.edit().putBoolean(KEY_MORNING_REPORT_UNREAD, value).apply()
        }

    var lastDownServersFingerprint: String
        get() = prefs.getString(KEY_LAST_DOWN_SERVERS_FINGERPRINT, "") ?: ""
        set(value) {
            prefs.edit().putString(KEY_LAST_DOWN_SERVERS_FINGERPRINT, value).apply()
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
        private const val KEY_THEME_MODE = "theme_mode"
        private const val KEY_MORNING_REPORT_NOTIFICATIONS_ENABLED = "morning_report_notifications_enabled"
        private const val KEY_MORNING_REPORT_TEXT = "morning_report_text"
        private const val KEY_MORNING_REPORT_RECEIVED_AT = "morning_report_received_at"
        private const val KEY_MORNING_REPORT_UNREAD = "morning_report_unread"
        private const val KEY_LAST_DOWN_SERVERS_FINGERPRINT = "last_down_servers_fingerprint"
        private const val DEFAULT_API_BASE_URL = "https://api.202020.ru:8443/"
        private const val DEFAULT_THEME_MODE = "dark"
    }
}
