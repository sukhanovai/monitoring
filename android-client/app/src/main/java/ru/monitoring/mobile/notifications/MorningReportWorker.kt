package ru.monitoring.mobile.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.time.Duration
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.util.concurrent.TimeUnit
import ru.monitoring.mobile.MainActivity
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.ControlActionRequest
import ru.monitoring.mobile.api.MobileTokenRefresher
import ru.monitoring.mobile.storage.AppPreferences

class MorningReportWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val prefs = AppPreferences(applicationContext)
        val token = prefs.apiToken.trim()
        val baseUrl = prefs.apiBaseUrl.trim().ifBlank { "https://api.202020.ru:8443/" }.let {
            if (it.endsWith("/")) it else "$it/"
        }
        if (token.isBlank()) {
            Log.w("MorningReportWorker", "doWork skipped: blank token")
            return Result.success()
        }

        return runCatching {
            val api = ApiFactory.createApi(
                // Читаем токен из prefs динамически: после авто-переобмена
                // (Authenticator на 401) повтор должен уйти со свежим токеном.
                tokenProvider = { prefs.apiToken.trim().ifBlank { token } },
                baseUrlProvider = { baseUrl },
                tokenRefresher = MobileTokenRefresher.forPreferences(prefs)
            )
            val response = api.runControlAction(ControlActionRequest("send_morning_report"))
            val reportText = response.message?.trim()
                ?.takeIf { it.isNotBlank() }
                ?: response.result?.trim().orEmpty().ifBlank { "Утренний отчет сформирован." }

            val receivedAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            prefs.morningReportText = reportText
            prefs.morningReportReceivedAt = receivedAt
            prefs.morningReportUnread = true

            ensureNotificationChannel(applicationContext)
            showNotification(applicationContext, reportText)
            Log.i("MorningReportWorker", "doWork success: baseUrl=$baseUrl, report_len=${reportText.length}")
            Result.success()
        }.getOrElse {
            Log.e("MorningReportWorker", "doWork failed: baseUrl=$baseUrl, error=${it.message}", it)
            Result.retry()
        }
    }

    private fun ensureNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Утренний отчет",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Пуш-уведомления с утренним отчетом мониторинга"
            enableVibration(true)
        }
        manager.createNotificationChannel(channel)
    }

    private fun showNotification(context: Context, reportText: String) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) return
        }
        if (!NotificationManagerCompat.from(context).areNotificationsEnabled()) return

        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(EXTRA_OPEN_MORNING_REPORT, true)
        }
        val pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT or
            (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        val contentIntent = PendingIntent.getActivity(
            context,
            NOTIFICATION_ID,
            openIntent,
            pendingFlags
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Утренний отчет")
            .setContentText(reportText)
            .setStyle(NotificationCompat.BigTextStyle().bigText(reportText))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(contentIntent)
            .build()

        NotificationManagerCompat.from(context).notify(NOTIFICATION_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "morning_report_channel"
        private const val NOTIFICATION_ID = 202020
        private const val UNIQUE_WORK_NAME = "morning_report_daily_work"
        const val EXTRA_OPEN_MORNING_REPORT = "open_morning_report"

        fun schedule(context: Context, timeRaw: String, enabled: Boolean) {
            val workManager = WorkManager.getInstance(context)
            if (!enabled) {
                workManager.cancelUniqueWork(UNIQUE_WORK_NAME)
                return
            }

            val targetTime = parseTimeOrDefault(timeRaw)
            val now = LocalDateTime.now()
            var nextRun = now.withHour(targetTime.hour).withMinute(targetTime.minute).withSecond(0).withNano(0)
            if (!nextRun.isAfter(now)) nextRun = nextRun.plusDays(1)

            val initialDelay = Duration.between(now, nextRun).toMinutes().coerceAtLeast(1)
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = PeriodicWorkRequestBuilder<MorningReportWorker>(24, TimeUnit.HOURS)
                .setInitialDelay(initialDelay, TimeUnit.MINUTES)
                .setConstraints(constraints)
                .build()

            workManager.enqueueUniquePeriodicWork(
                UNIQUE_WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                request
            )
        }

        private fun parseTimeOrDefault(raw: String): LocalTime {
            val trimmed = raw.trim()
            return runCatching {
                val parts = trimmed.split(":")
                if (parts.size != 2) throw IllegalArgumentException("Invalid time")
                LocalTime.of(parts[0].toInt(), parts[1].toInt())
            }.getOrElse { LocalTime.of(8, 30) }
        }
    }
}
