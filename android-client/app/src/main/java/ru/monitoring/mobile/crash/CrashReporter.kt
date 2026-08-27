package ru.monitoring.mobile.crash

import android.content.Context
import android.os.Build
import ru.monitoring.mobile.BuildConfig
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

// Глобальный сборщик отчётов о сбоях. Системный диалог Android «произошёл сбой»
// не несёт никакой технической информации, а logcat без подключённого к ПК
// adb недоступен. Поэтому здесь мы перехватываем любое необработанное
// исключение, сохраняем полный stack trace в SharedPreferences и в файл, после
// чего отдаём управление системному обработчику (он покажет диалог и убьёт
// процесс). На следующем запуске MainActivity покажет сохранённый отчёт.
object CrashReporter {
    private const val PREFS_NAME = "comdone_crash_reporter"
    private const val KEY_LAST_CRASH = "last_crash_report"
    const val CRASH_FILE_NAME = "comdone-last-crash.txt"

    fun install(context: Context) {
        val appContext = context.applicationContext
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            runCatching { saveCrash(appContext, thread, throwable) }
            if (previous != null) {
                previous.uncaughtException(thread, throwable)
            } else {
                android.os.Process.killProcess(android.os.Process.myPid())
                kotlin.system.exitProcess(10)
            }
        }
    }

    fun peekPendingCrash(context: Context): String? =
        prefs(context).getString(KEY_LAST_CRASH, null)?.takeIf { it.isNotBlank() }

    fun clearPendingCrash(context: Context) {
        runCatching { prefs(context).edit().remove(KEY_LAST_CRASH).apply() }
    }

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private fun saveCrash(context: Context, thread: Thread, throwable: Throwable) {
        val report = buildReport(thread, throwable)
        // Процесс вот-вот умрёт — нужен синхронный commit(), а не apply().
        runCatching { prefs(context).edit().putString(KEY_LAST_CRASH, report).commit() }
        runCatching {
            val dir = context.getExternalFilesDir(null)
            if (dir != null) {
                if (!dir.exists()) dir.mkdirs()
                File(dir, CRASH_FILE_NAME).writeText(report)
            }
        }
    }

    private fun buildReport(thread: Thread, throwable: Throwable): String {
        val stack = StringWriter().also { sw ->
            PrintWriter(sw).use { throwable.printStackTrace(it) }
        }.toString()
        val timestamp = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date())
        return buildString {
            appendLine("ComDone — отчёт о сбое")
            appendLine("Время: $timestamp")
            appendLine("Версия: ${BuildConfig.VERSION_NAME} (code ${BuildConfig.VERSION_CODE})")
            appendLine("Сборка: ${BuildConfig.FLAVOR} / ${BuildConfig.BUILD_TYPE}")
            appendLine("Устройство: ${Build.MANUFACTURER} ${Build.MODEL}")
            appendLine("Android: ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
            appendLine("Поток: ${thread.name}")
            appendLine()
            append(stack)
        }
    }
}
