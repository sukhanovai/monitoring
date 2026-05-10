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
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit
import android.util.Log
import ru.monitoring.mobile.MainActivity
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.ManagedServer
import ru.monitoring.mobile.storage.AppPreferences

class ServerDownAlertWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {
    private companion object {
        private const val TAG = "ServerDownAlertWorker"
    }

    private val prefs = AppPreferences(appContext)

    override suspend fun doWork(): Result {
        val token = prefs.apiToken.trim()
        val baseUrl = prefs.apiBaseUrl.trim().ifBlank { "https://api.202020.ru:8443/" }.let {
            if (it.endsWith("/")) it else "$it/"
        }
        if (token.isBlank()) {
            Log.w(TAG, "doWork skipped: blank token")
            scheduleNext(applicationContext, enabled = false)
            return Result.success()
        }

        val result = runCatching {
            val api = ApiFactory.createApi(
                tokenProvider = { token },
                baseUrlProvider = { baseUrl }
            )
            val managedServers = runCatching { api.getServersSettings().items }.getOrDefault(emptyList())
            val response = api.getAvailability()
            val allServers = if (response.servers.isNotEmpty()) response.servers else response.items.mapIndexed { index, item ->
                val resolvedName = resolveServerName(
                    serverId = item.serverId,
                    serverName = item.serverName,
                    name = item.name,
                    ip = item.ip,
                    managedServers = managedServers,
                    fallback = "server-${index + 1}"
                )
                ru.monitoring.mobile.api.ServerAvailability(
                    id = item.serverId?.ifBlank { null } ?: "server-${index + 1}",
                    name = resolvedName,
                    status = item.status ?: "UNKNOWN",
                    lastCheckedAt = item.checkedAt
                )
            }

            val downServerNames = allServers
                .filter { isDownStatus(it.status) }
                .map { it.name.ifBlank { it.id } }
                .sorted()

            val currentFingerprint = downServerNames.joinToString("|")
            val previousFingerprint = prefs.lastDownServersFingerprint
            val previousDownServers = previousFingerprint
                .split("|")
                .map { it.trim() }
                .filter { it.isNotBlank() }
                .toSet()
            prefs.lastDownServersFingerprint = currentFingerprint

            val hasNewDownServers = downServerNames.isNotEmpty() && currentFingerprint != previousFingerprint
            if (hasNewDownServers) {
                ensureNotificationChannel(applicationContext)
                showDownNotification(applicationContext, downServerNames)
            }

            val recoveredServers = previousDownServers - downServerNames.toSet()
            if (recoveredServers.isNotEmpty()) {
                ensureNotificationChannel(applicationContext)
                showRecoveryNotification(applicationContext, recoveredServers.sorted())
            }

            Log.i(TAG, "doWork success: baseUrl=$baseUrl, down=${downServerNames.size}")
            Result.success()
        }.getOrElse {
            Log.e(TAG, "doWork failed: baseUrl=$baseUrl, error=${it.message}", it)
            Result.retry()
        }

        scheduleNext(applicationContext, enabled = true)
        return result
    }

    private fun resolveServerName(
        serverId: String?,
        serverName: String?,
        name: String?,
        ip: String?,
        managedServers: List<ManagedServer>,
        fallback: String
    ): String {
        val managedByIp = managedServers.associateBy { it.ip.trim().lowercase() }
        val managedByName = managedServers.associateBy { it.name.trim().lowercase() }

        val candidates = listOf(ip, serverId, serverName, name)
            .map { it?.trim().orEmpty() }
            .filter { it.isNotBlank() }

        val fromManaged = candidates.firstNotNullOfOrNull { token ->
            val lookup = token.lowercase()
            managedByIp[lookup]?.name ?: managedByName[lookup]?.name
        }

        return fromManaged
            ?: serverName?.trim().orEmpty().ifBlank { name?.trim().orEmpty() }
                .ifBlank { serverId?.trim().orEmpty() }
                .ifBlank { ip?.trim().orEmpty() }
                .ifBlank { fallback }
    }


    private fun isDownStatus(statusRaw: String): Boolean {
        val normalized = statusRaw.trim().lowercase()
        return normalized in setOf("down", "unreachable", "offline", "error", "critical")
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

    private fun showDownNotification(context: Context, downServers: List<String>) {
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
            putExtra(EXTRA_DOWN_SERVER_NAMES, downServers.toTypedArray())
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

    private fun showRecoveryNotification(context: Context, recoveredServers: List<String>) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) return
        }
        if (!NotificationManagerCompat.from(context).areNotificationsEnabled()) return

        val recoveredCount = recoveredServers.size
        val title = if (recoveredCount == 1) "Сервер восстановлен" else "Серверы восстановлены"
        val body = recoveredServers.joinToString(", ").ifBlank { "Сервер снова доступен" }

        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingFlags = PendingIntent.FLAG_UPDATE_CURRENT or
            (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
        val contentIntent = PendingIntent.getActivity(
            context,
            RECOVERY_NOTIFICATION_ID,
            openIntent,
            pendingFlags
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(contentIntent)
            .build()

        NotificationManagerCompat.from(context).notify(RECOVERY_NOTIFICATION_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "server_down_alerts_channel"
        private const val NOTIFICATION_ID = 202021
        private const val RECOVERY_NOTIFICATION_ID = 202022
        private const val UNIQUE_WORK_NAME = "server_down_alerts_work"
        private const val CHECK_INTERVAL_MINUTES = 1L
        const val EXTRA_DOWN_SERVER_NAMES = "extra_down_server_names"

        fun schedule(context: Context, enabled: Boolean) {
            val workManager = WorkManager.getInstance(context)
            if (!enabled) {
                workManager.cancelUniqueWork(UNIQUE_WORK_NAME)
                return
            }

            scheduleNext(context, enabled = true)
        }

        private fun scheduleNext(context: Context, enabled: Boolean) {
            val workManager = WorkManager.getInstance(context)
            if (!enabled) {
                workManager.cancelUniqueWork(UNIQUE_WORK_NAME)
                return
            }

            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = OneTimeWorkRequestBuilder<ServerDownAlertWorker>()
                .setInitialDelay(CHECK_INTERVAL_MINUTES, TimeUnit.MINUTES)
                .setConstraints(constraints)
                .build()

            workManager.enqueueUniqueWork(
                UNIQUE_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                request
            )
        }
    }
}
