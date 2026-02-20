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
                    onUpdateMonitoringSettings = vm::updateMonitoringSettings,
                    onUpdateBotSettings = vm::updateBotSettings,
                    onUpdateTimeSettings = vm::updateTimeSettings,
                    onUpdateAuthSettings = vm::updateAuthSettings
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
    onUpdateMonitoringSettings: (String, String, String) -> Unit,
    onUpdateBotSettings: (String, String) -> Unit,
    onUpdateTimeSettings: (String, String, String) -> Unit,
    onUpdateAuthSettings: (String, String, String, String) -> Unit
) {
    var tokenInput by remember(state.token) { mutableStateOf(state.token) }
    var checkInterval by remember { mutableStateOf("") }
    var timeout by remember { mutableStateOf("") }
    var maxDowntime by remember { mutableStateOf("") }

    var telegramToken by remember { mutableStateOf("") }
    var telegramChatId by remember { mutableStateOf("") }

    var quietStart by remember { mutableStateOf("") }
    var quietEnd by remember { mutableStateOf("") }
    var metricsTime by remember { mutableStateOf("") }

    var authMode by remember { mutableStateOf("") }
    var sshUsername by remember { mutableStateOf("") }
    var sshPort by remember { mutableStateOf("") }
    var windowsUsername by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Monitoring Android") })
        }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
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
            }

            item {
                if (state.isLoading) {
                    CircularProgressIndicator()
                }

                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Статус", fontWeight = FontWeight.Bold)
                        Text(state.summaryText)
                        if (state.message.isNotBlank()) {
                            Text(state.message)
                        }
                    }
                }
            }

            item {
                Text("Управление", fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { onAction("pause_monitoring") }) { Text("Пауза") }
                    Button(onClick = { onAction("resume_monitoring") }) { Text("Старт") }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { onAction("send_morning_report") }) { Text("Отчёт") }
                    Button(onClick = { onAction("force_quiet") }) { Text("Quiet") }
                    Button(onClick = { onAction("force_loud") }) { Text("Loud") }
                }
            }

            item {
                Text("Настройки мониторинга", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = checkInterval,
                    onValueChange = { checkInterval = it },
                    label = { Text("check_interval_sec") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = timeout,
                    onValueChange = { timeout = it },
                    label = { Text("timeout_sec") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = maxDowntime,
                    onValueChange = { maxDowntime = it },
                    label = { Text("max_downtime_sec") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = { onUpdateMonitoringSettings(checkInterval, timeout, maxDowntime) }) {
                    Text("Сохранить monitoring")
                }
            }

            item {
                Text("Настройки бота", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = telegramToken,
                    onValueChange = { telegramToken = it },
                    label = { Text("telegram_bot_token") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = telegramChatId,
                    onValueChange = { telegramChatId = it },
                    label = { Text("telegram_chat_id") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = { onUpdateBotSettings(telegramToken, telegramChatId) }) {
                    Text("Сохранить bot")
                }
            }

            item {
                Text("Временные настройки", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = quietStart,
                    onValueChange = { quietStart = it },
                    label = { Text("quiet_start (HH:mm)") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = quietEnd,
                    onValueChange = { quietEnd = it },
                    label = { Text("quiet_end (HH:mm)") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = metricsTime,
                    onValueChange = { metricsTime = it },
                    label = { Text("metrics_collection_time (HH:mm)") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = { onUpdateTimeSettings(quietStart, quietEnd, metricsTime) }) {
                    Text("Сохранить time")
                }
            }

            item {
                Text("Auth-параметры", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = authMode,
                    onValueChange = { authMode = it },
                    label = { Text("auth_mode") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = sshUsername,
                    onValueChange = { sshUsername = it },
                    label = { Text("ssh_username") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = sshPort,
                    onValueChange = { sshPort = it },
                    label = { Text("ssh_port") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = windowsUsername,
                    onValueChange = { windowsUsername = it },
                    label = { Text("windows_username") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = { onUpdateAuthSettings(authMode, sshUsername, sshPort, windowsUsername) }) {
                    Text("Сохранить auth")
                }
            }

            item {
                Spacer(modifier = Modifier.height(8.dp))
                Text("Список серверов", fontWeight = FontWeight.Bold)
            }

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
}
