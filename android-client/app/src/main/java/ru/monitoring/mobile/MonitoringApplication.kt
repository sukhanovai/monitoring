package ru.monitoring.mobile

import android.app.Application
import ru.monitoring.mobile.crash.CrashReporter
import ru.monitoring.mobile.notifications.MorningReportWorker

class MonitoringApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        CrashReporter.install(this)
        // Переустанавливаем точное время ежедневного запроса утреннего отчёта
        // при каждом старте приложения: унаследованное от старых версий
        // расписание WorkManager могло «уплыть» (например, на 6:0x вместо
        // 9:0x), а rescheduleBackgroundWorkers вызывается только по событиям
        // во ViewModel. runCatching — планирование не должно ронять запуск.
        runCatching { MorningReportWorker.rescheduleNextRun(this) }
    }
}
