package ru.monitoring.mobile.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
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
import java.util.concurrent.TimeUnit
import ru.monitoring.mobile.MainActivity
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.storage.AppPreferences

class ServerDownAlertWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val prefs = AppPreferences(applicationContext)
        val token = prefs.apiToken.trim()
        if (token.isBlank()) return Result.success()

        return runCatching {
            val api = ApiFactory.createApi(
                tokenProvider = { prefs.apiToken },
                baseUrlProvider = { prefs.apiBaseUrl }
            )
            val response = api.getAvailability()
            val allServers = if (response.servers.isNotEmpty()) response.servers else response.items.mapIndexed { index, item ->
                ru.monitoring.mobile.api.ServerAvailability(
                    id = item.serverId?.ifBlank { null } ?: "server-${index + 1}",
                    name = item.serverId?.ifBlank { null } ?: "server-${index + 1}",
                    status = item.status ?: "UNKNOWN",
                    lastCheckedAt = item.checkedAt
                )
            }

            val downServerNames = allServers
                .filter { it.status.equals("DOWN", ignoreCase = true) }
                .map { it.name.ifBlank { it.id } }
                .sorted()

            val currentFingerprint = downServerNames.joinToString("|")
            val previousFingerprint = prefs.lastDownServersFingerprint
            prefs.lastDownServersFingerprint = currentFingerprint

            val hasNewDownServers = downServerNames.isNotEmpty() && currentFingerprint != previousFingerprint
            if (hasNewDownServers) {
                ensureNotificationChannel(applicationContext)
                showNotification(applicationContext, downServerNames)
            }

            Result.success()
        }.getOrElse { Result.retry() }
    }

    private fun ensureNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Алерты недоступности",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Пуш-уведомления о недоступных серверах"
            enableVibration(true)
        }
        manager.createNotificationChannel(channel)
    }

    private fun showNotification(context: Context, downServers: List<String>) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) return
        }
        if (!NotificationManagerCompat.from(context).areNotificationsEnabled()) return

        val downCount = downServers.size
        val title = if (downCount == 1) "Сервер недоступен" else "Серверы недоступны"
        val body = downServers.joinToString(", ").ifBlank { "Есть DOWN-серверы" }

        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
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
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(contentIntent)
            .build()

        NotificationManagerCompat.from(context).notify(NOTIFICATION_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "server_down_alerts_channel"
        private const val NOTIFICATION_ID = 202021
        private const val UNIQUE_WORK_NAME = "server_down_alerts_work"

        fun schedule(context: Context, enabled: Boolean) {
            val workManager = WorkManager.getInstance(context)
            if (!enabled) {
                workManager.cancelUniqueWork(UNIQUE_WORK_NAME)
                return
            }

            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = PeriodicWorkRequestBuilder<ServerDownAlertWorker>(15, TimeUnit.MINUTES)
                .setConstraints(constraints)
                .build()

            workManager.enqueueUniquePeriodicWork(
                UNIQUE_WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                request
            )
        }
    }
}
