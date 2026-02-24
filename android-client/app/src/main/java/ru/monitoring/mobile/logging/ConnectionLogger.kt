package ru.monitoring.mobile.logging

import android.util.Log
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

object ConnectionLogger {
    private const val TAG = "AndroidConnection"
    private const val ERROR_MESSAGE_LIMIT = 300

    fun info(event: String, fields: Map<String, Any?> = emptyMap()) {
        Log.i(TAG, formatEvent(event, fields))
    }

    fun warn(event: String, fields: Map<String, Any?> = emptyMap()) {
        Log.w(TAG, formatEvent(event, fields))
    }

    fun error(event: String, fields: Map<String, Any?> = emptyMap()) {
        Log.e(TAG, formatEvent(event, fields))
    }

    fun shortErrorMessage(value: String?): String {
        val trimmed = value?.trim().orEmpty()
        if (trimmed.length <= ERROR_MESSAGE_LIMIT) return trimmed
        return trimmed.take(ERROR_MESSAGE_LIMIT)
    }

    private fun formatEvent(event: String, fields: Map<String, Any?>): String {
        val payload = JSONObject()
        payload.put("event", event)
        payload.put("timestamp_utc", utcNow())
        fields.forEach { (key, value) ->
            payload.put(key, value)
        }
        return payload.toString()
    }

    private fun utcNow(): String {
        val formatter = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US)
        formatter.timeZone = TimeZone.getTimeZone("UTC")
        return formatter.format(Date())
    }
}
