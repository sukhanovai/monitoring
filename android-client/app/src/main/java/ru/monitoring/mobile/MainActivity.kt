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
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
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
                    onTokenChanged = vm::setTokenInput,
                    onSaveToken = vm::saveToken,
                    onRefresh = vm::refreshAvailability,
                    onRefreshSettings = vm::refreshSettingsFromServer,
                    onToggleApiTokenVisibility = vm::toggleApiTokenVisibility,
                    onToggleTelegramTokenVisibility = vm::toggleTelegramTokenVisibility,
                    onAction = vm::sendAction,
                    onCheckIntervalChanged = vm::setCheckIntervalInput,
                    onTimeoutChanged = vm::setTimeoutInput,
                    onMaxDowntimeChanged = vm::setMaxDowntimeInput,
                    onSaveMonitoring = vm::updateMonitoringSettings,
                    onTelegramTokenChanged = vm::setTelegramTokenInput,
                    onTelegramChatIdChanged = vm::setTelegramChatIdInput,
                    onSaveBot = vm::updateBotSettings,
                    onQuietStartChanged = vm::setQuietStartInput,
                    onQuietEndChanged = vm::setQuietEndInput,
                    onMetricsTimeChanged = vm::setMetricsTimeInput,
                    onSaveTime = vm::updateTimeSettings,
                    onAuthModeChanged = vm::setAuthModeInput,
                    onSshUsernameChanged = vm::setSshUsernameInput,
                    onSshPortChanged = vm::setSshPortInput,
                    onWindowsUsernameChanged = vm::setWindowsUsernameInput,
                    onSaveAuth = vm::updateAuthSettings
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MonitoringApp(
    state: MainUiState,
    onTokenChanged: (String) -> Unit,
    onSaveToken: (String) -> Unit,
    onRefresh: () -> Unit,
    onRefreshSettings: () -> Unit,
    onToggleApiTokenVisibility: () -> Unit,
    onToggleTelegramTokenVisibility: () -> Unit,
    onAction: (String) -> Unit,
    onCheckIntervalChanged: (String) -> Unit,
    onTimeoutChanged: (String) -> Unit,
    onMaxDowntimeChanged: (String) -> Unit,
    onSaveMonitoring: () -> Unit,
    onTelegramTokenChanged: (String) -> Unit,
    onTelegramChatIdChanged: (String) -> Unit,
    onSaveBot: () -> Unit,
    onQuietStartChanged: (String) -> Unit,
    onQuietEndChanged: (String) -> Unit,
    onMetricsTimeChanged: (String) -> Unit,
    onSaveTime: () -> Unit,
    onAuthModeChanged: (String) -> Unit,
    onSshUsernameChanged: (String) -> Unit,
    onSshPortChanged: (String) -> Unit,
    onWindowsUsernameChanged: (String) -> Unit,
    onSaveAuth: () -> Unit
) {
    val canSaveMonitoring = state.checkIntervalInput.isNotBlank() || state.timeoutInput.isNotBlank() || state.maxDowntimeInput.isNotBlank()
    val canSaveBot = state.telegramTokenInput.isNotBlank() || state.telegramChatIdInput.isNotBlank()
    val canSaveTime = state.quietStartInput.isNotBlank() || state.quietEndInput.isNotBlank() || state.metricsTimeInput.isNotBlank()
    val canSaveAuth = state.authModeInput.isNotBlank() || state.sshUsernameInput.isNotBlank() || state.sshPortInput.isNotBlank() || state.windowsUsernameInput.isNotBlank()

    val hiddenTransformation = PasswordVisualTransformation()

    var telegramToken by remember { mutableStateOf("") }
    var telegramChatId by remember { mutableStateOf("") }

    var quietStart by remember { mutableStateOf("") }
    var quietEnd by remember { mutableStateOf("") }
    var metricsTime by remember { mutableStateOf("") }

    var authMode by remember { mutableStateOf("") }
    var sshUsername by remember { mutableStateOf("") }
    var sshPort by remember { mutableStateOf("") }
    var windowsUsername by remember { mutableStateOf("") }

    val canSaveMonitoring = checkInterval.isNotBlank() || timeout.isNotBlank() || maxDowntime.isNotBlank()
    val canSaveBot = telegramToken.isNotBlank() || telegramChatId.isNotBlank()
    val canSaveTime = quietStart.isNotBlank() || quietEnd.isNotBlank() || metricsTime.isNotBlank()
    val canSaveAuth = authMode.isNotBlank() || sshUsername.isNotBlank() || sshPort.isNotBlank() || windowsUsername.isNotBlank()

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
                    value = state.token,
                    onValueChange = onTokenChanged,
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Bearer токен") },
                    visualTransformation = if (state.isApiTokenVisible) VisualTransformation.None else hiddenTransformation,
                    trailingIcon = {
                        TextButton(onClick = onToggleApiTokenVisibility) {
                            Text(if (state.isApiTokenVisible) "Скрыть" else "Показать")
                        }
                    }
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { onSaveToken(state.token) }) { Text("Сохранить токен") }
                    Button(onClick = onRefresh) { Text("Обновить") }
                    Button(onClick = onRefreshSettings) { Text("Подтянуть настройки") }
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
                    value = state.checkIntervalInput,
                    onValueChange = onCheckIntervalChanged,
                    label = { Text("check_interval_sec") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.timeoutInput,
                    onValueChange = onTimeoutChanged,
                    label = { Text("timeout_sec") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.maxDowntimeInput,
                    onValueChange = onMaxDowntimeChanged,
                    label = { Text("max_downtime_sec") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = onSaveMonitoring, enabled = canSaveMonitoring) {
                    Text("Сохранить monitoring")
                }
            }

            item {
                Text("Настройки бота", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = state.telegramTokenInput,
                    onValueChange = onTelegramTokenChanged,
                    label = { Text("telegram_bot_token") },
                    modifier = Modifier.fillMaxWidth(),
                    visualTransformation = if (state.isTelegramTokenVisible) VisualTransformation.None else hiddenTransformation,
                    trailingIcon = {
                        TextButton(onClick = onToggleTelegramTokenVisibility) {
                            Text(if (state.isTelegramTokenVisible) "Скрыть" else "Показать")
                        }
                    }
                )
                OutlinedTextField(
                    value = state.telegramChatIdInput,
                    onValueChange = onTelegramChatIdChanged,
                    label = { Text("telegram_chat_id") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = onSaveBot, enabled = canSaveBot) {
                    Text("Сохранить bot")
                }
            }

            item {
                Text("Временные настройки", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = state.quietStartInput,
                    onValueChange = onQuietStartChanged,
                    label = { Text("quiet_start (HH:mm)") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.quietEndInput,
                    onValueChange = onQuietEndChanged,
                    label = { Text("quiet_end (HH:mm)") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.metricsTimeInput,
                    onValueChange = onMetricsTimeChanged,
                    label = { Text("metrics_collection_time (HH:mm)") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = onSaveTime, enabled = canSaveTime) {
                    Text("Сохранить time")
                }
            }

            item {
                Text("Auth-параметры", fontWeight = FontWeight.Bold)
                OutlinedTextField(
                    value = state.authModeInput,
                    onValueChange = onAuthModeChanged,
                    label = { Text("auth_mode") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.sshUsernameInput,
                    onValueChange = onSshUsernameChanged,
                    label = { Text("ssh_username") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.sshPortInput,
                    onValueChange = onSshPortChanged,
                    label = { Text("ssh_port") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = state.windowsUsernameInput,
                    onValueChange = onWindowsUsernameChanged,
                    label = { Text("windows_username") },
                    modifier = Modifier.fillMaxWidth()
                )
                Button(onClick = onSaveAuth, enabled = canSaveAuth) {
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
