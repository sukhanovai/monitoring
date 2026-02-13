package ru.monitoring.mobile.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import ru.monitoring.mobile.api.ApiFactory
import ru.monitoring.mobile.api.BackupItem
import ru.monitoring.mobile.api.MonitoringRepository
import ru.monitoring.mobile.api.SettingsMonitoringRequest
import ru.monitoring.mobile.storage.AppPreferences
import java.time.LocalDate

class MainViewModel(
    private val preferences: AppPreferences
) : ViewModel() {
    private val repository = MonitoringRepository(ApiFactory.createApi { preferences.apiToken })

    var state by mutableStateOf(MainUiState())
        private set

    fun loadInitialState() {
        val now = LocalDate.now()
        state = state.copy(
            token = preferences.apiToken,
            backupsFrom = now.minusDays(7).toString(),
            backupsTo = now.toString()
        )
    }

    fun saveToken(token: String) {
        val normalized = token.trim()
        preferences.apiToken = normalized
        state = state.copy(
            token = normalized,
            message = if (normalized.isBlank()) "Токен очищен" else "Токен сохранён"
        )
    }

    fun refreshAvailability() {
        requestWithLoading {
            repository.getAvailability().onSuccess { payload ->
                state = state.copy(
                    servers = payload.servers,
                    summaryText = "UP: ${payload.summary.up}, DOWN: ${payload.summary.down}, UNKNOWN: ${payload.summary.unknown}",
                    message = "Данные обновлены"
                )
            }.onFailure {
                state = state.copy(message = it.message ?: "Ошибка запроса")
            }
        }
    }

    fun sendAction(action: String) {
        requestWithLoading {
            repository.runAction(action).onSuccess { data ->
                state = state.copy(message = data.message)
            }.onFailure {
                state = state.copy(message = it.message ?: "Ошибка команды")
            }
        }
    }

    fun updateSettings(checkInterval: String, timeout: String, maxDowntime: String) {
        val request = SettingsMonitoringRequest(
            checkIntervalSec = checkInterval.toIntOrNull(),
            timeoutSec = timeout.toIntOrNull(),
            maxDowntimeSec = maxDowntime.toIntOrNull()
        )

        requestWithLoading {
            repository.updateMonitoringSettings(request).onSuccess { data ->
                state = state.copy(
                    message = "Сохранено: interval=${data.checkIntervalSec}, timeout=${data.timeoutSec}, maxDown=${data.maxDowntimeSec}"
                )
            }.onFailure {
                state = state.copy(message = it.message ?: "Ошибка сохранения")
            }
        }
    }

    fun setBackupsRange(from: String, to: String) {
        state = state.copy(backupsFrom = from, backupsTo = to)
    }

    fun loadBackups() {
        if (state.backupsFrom.isBlank() || state.backupsTo.isBlank()) {
            state = state.copy(message = "Укажи обе даты (from/to)")
            return
        }

        requestWithLoading {
            repository.getProxmoxBackups(state.backupsFrom, state.backupsTo).onSuccess { data ->
                state = state.copy(
                    backups = data.backups,
                    message = "Бэкапы загружены: ${data.backups.size}"
                )
            }.onFailure {
                state = state.copy(message = it.message ?: "Ошибка получения бэкапов")
            }
        }
    }

    fun setTab(tab: AppTab) {
        state = state.copy(selectedTab = tab)
    }

    private fun requestWithLoading(block: suspend () -> Unit) {
        viewModelScope.launch {
            state = state.copy(isLoading = true, message = "")
            block()
            state = state.copy(isLoading = false)
        }
    }

    @Suppress("UNCHECKED_CAST")
    class Factory(
        private val preferences: AppPreferences
    ) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            return MainViewModel(preferences) as T
        }
    }
}

enum class AppTab {
    DASHBOARD,
    CONTROL,
    BACKUPS,
    SETTINGS
}

data class MainUiState(
    val token: String = "",
    val isLoading: Boolean = false,
    val selectedTab: AppTab = AppTab.DASHBOARD,
    val summaryText: String = "Нажми \"Обновить\", чтобы получить статус",
    val servers: List<ru.monitoring.mobile.api.ServerAvailability> = emptyList(),
    val backups: List<BackupItem> = emptyList(),
    val backupsFrom: String = "",
    val backupsTo: String = "",
    val message: String = ""
)
