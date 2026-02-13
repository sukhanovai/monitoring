package ru.monitoring.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import ru.monitoring.mobile.storage.AppPreferences
import ru.monitoring.mobile.ui.AppTab
import ru.monitoring.mobile.ui.MainUiState
import ru.monitoring.mobile.ui.MainViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val preferences = AppPreferences(applicationContext)

        enableEdgeToEdge()
        setContent {
            MaterialTheme {
                val vm: MainViewModel = viewModel(factory = MainViewModel.Factory(preferences))
                LaunchedEffect(Unit) {
                    vm.loadInitialState()
                }
                MonitoringApp(
                    state = vm.state,
                    onSaveToken = vm::saveToken,
                    onRefresh = vm::refreshAvailability,
                    onAction = vm::sendAction,
                    onUpdateSettings = vm::updateSettings,
                    onTabChange = vm::setTab,
                    onBackupsRangeChange = vm::setBackupsRange,
                    onLoadBackups = vm::loadBackups
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MonitoringApp(
    state: MainUiState,
    onSaveToken: (String) -> Unit,
    onRefresh: () -> Unit,
    onAction: (String) -> Unit,
    onUpdateSettings: (String, String, String) -> Unit,
    onTabChange: (AppTab) -> Unit,
    onBackupsRangeChange: (String, String) -> Unit,
    onLoadBackups: () -> Unit
) {
    var tokenInput by remember(state.token) { mutableStateOf(state.token) }
    var checkInterval by remember { mutableStateOf("") }
    var timeout by remember { mutableStateOf("") }
    var maxDowntime by remember { mutableStateOf("") }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Monitoring Android") }) },
        bottomBar = {
            NavigationBar {
                AppTab.entries.forEach { tab ->
                    NavigationBarItem(
                        selected = state.selectedTab == tab,
                        onClick = { onTabChange(tab) },
                        label = { Text(tab.title()) },
                        icon = { Text(tab.icon()) }
                    )
                }
            }
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("Подключение к BFF", fontWeight = FontWeight.Bold)
            OutlinedTextField(
                value = tokenInput,
                onValueChange = { tokenInput = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Bearer токен") }
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { onSaveToken(tokenInput) }) { Text("Сохранить токен") }
                Button(onClick = onRefresh) { Text("Обновить") }
            }

            if (state.isLoading) {
                CircularProgressIndicator()
            }

            if (state.message.isNotBlank()) {
                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Text(state.message, modifier = Modifier.padding(12.dp))
                }
            }

            when (state.selectedTab) {
                AppTab.DASHBOARD -> DashboardTab(state)
                AppTab.CONTROL -> ControlTab(onAction)
                AppTab.BACKUPS -> BackupsTab(state, onBackupsRangeChange, onLoadBackups)
                AppTab.SETTINGS -> SettingsTab(checkInterval, timeout, maxDowntime, onUpdateSettings,
                    onCheckIntervalChange = { checkInterval = it },
                    onTimeoutChange = { timeout = it },
                    onMaxDowntimeChange = { maxDowntime = it }
                )
            }
        }
    }
}

@Composable
private fun DashboardTab(state: MainUiState) {
    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("Статус", fontWeight = FontWeight.Bold)
            Text(state.summaryText)
        }
    }

    Spacer(modifier = Modifier.height(8.dp))
    Text("Список серверов", fontWeight = FontWeight.Bold)
    LazyColumn(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        items(state.servers) { server ->
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(10.dp)) {
                    Text(server.name, fontWeight = FontWeight.Bold)
                    Text("ID: ${server.id}")
                    Text("Статус: ${server.status}")
                    Text("Проверка: ${server.lastCheckedAt ?: "-"}")
                }
            }
        }
    }
}

@Composable
private fun ControlTab(onAction: (String) -> Unit) {
    Text("Быстрые действия", fontWeight = FontWeight.Bold)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = { onAction("pause_monitoring") }) { Text("Пауза") }
        Button(onClick = { onAction("resume_monitoring") }) { Text("Старт") }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = { onAction("send_morning_report") }) { Text("Отчёт") }
        Button(onClick = { onAction("force_quiet") }) { Text("Quiet") }
    }
}

@Composable
private fun BackupsTab(
    state: MainUiState,
    onBackupsRangeChange: (String, String) -> Unit,
    onLoadBackups: () -> Unit
) {
    Text("Бэкапы Proxmox", fontWeight = FontWeight.Bold)

    OutlinedTextField(
        value = state.backupsFrom,
        onValueChange = { onBackupsRangeChange(it, state.backupsTo) },
        label = { Text("from (YYYY-MM-DD)") },
        modifier = Modifier.fillMaxWidth()
    )
    OutlinedTextField(
        value = state.backupsTo,
        onValueChange = { onBackupsRangeChange(state.backupsFrom, it) },
        label = { Text("to (YYYY-MM-DD)") },
        modifier = Modifier.fillMaxWidth()
    )

    Button(onClick = onLoadBackups) {
        Text("Загрузить бэкапы")
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        items(state.backups) { backup ->
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(10.dp)) {
                    Text(if (backup.id.isBlank()) "Без ID" else backup.id, fontWeight = FontWeight.Bold)
                    Text("Источник: ${backup.source.ifBlank { "-" }}")
                    Text("Статус: ${backup.status}")
                    Text("Дата: ${backup.createdAt ?: "-"}")
                    Text("Размер: ${backup.sizeHuman ?: "-"}")
                    if (!backup.message.isNullOrBlank()) {
                        Text("Комментарий: ${backup.message}")
                    }
                }
            }
        }
    }
}

@Composable
private fun SettingsTab(
    checkInterval: String,
    timeout: String,
    maxDowntime: String,
    onUpdateSettings: (String, String, String) -> Unit,
    onCheckIntervalChange: (String) -> Unit,
    onTimeoutChange: (String) -> Unit,
    onMaxDowntimeChange: (String) -> Unit
) {
    Text("Настройки мониторинга", fontWeight = FontWeight.Bold)
    OutlinedTextField(
        value = checkInterval,
        onValueChange = onCheckIntervalChange,
        label = { Text("check_interval_sec") },
        modifier = Modifier.fillMaxWidth()
    )
    OutlinedTextField(
        value = timeout,
        onValueChange = onTimeoutChange,
        label = { Text("timeout_sec") },
        modifier = Modifier.fillMaxWidth()
    )
    OutlinedTextField(
        value = maxDowntime,
        onValueChange = onMaxDowntimeChange,
        label = { Text("max_downtime_sec") },
        modifier = Modifier.fillMaxWidth()
    )
    Button(onClick = { onUpdateSettings(checkInterval, timeout, maxDowntime) }) {
        Text("Сохранить настройки")
    }
}

private fun AppTab.title(): String = when (this) {
    AppTab.DASHBOARD -> "Статус"
    AppTab.CONTROL -> "Упр."
    AppTab.BACKUPS -> "Бэкапы"
    AppTab.SETTINGS -> "Настройки"
}

private fun AppTab.icon(): String = when (this) {
    AppTab.DASHBOARD -> "📊"
    AppTab.CONTROL -> "🎛️"
    AppTab.BACKUPS -> "💾"
    AppTab.SETTINGS -> "⚙️"
}
