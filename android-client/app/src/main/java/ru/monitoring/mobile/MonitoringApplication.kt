package ru.monitoring.mobile

import android.app.Application
import ru.monitoring.mobile.crash.CrashReporter

class MonitoringApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        CrashReporter.install(this)
    }
}
