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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import ru.monitoring.mobile.storage.AppPreferences
import ru.monitoring.mobile.ui.MainUiState
import ru.monitoring.mobile.ui.MainViewModel

private enum class AppSection {
    MAIN,
    SETTINGS
}

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
                    onToggleApiTokenVisibility = vm::toggleApiTokenVisibility,
                    onToggleTelegramTokenVisibility = vm::toggleTelegramTokenVisibility,
                    onShowMenuStub = vm::showMenuStub,
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
                    onSshPasswordChanged = vm::setSshPasswordInput,
                    onWindowsPasswordChanged = vm::setWindowsPasswordInput,
                    onToggleSshPasswordVisibility = vm::toggleSshPasswordVisibility,
                    onToggleWindowsPasswordVisibility = vm::toggleWindowsPasswordVisibility,
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
    onToggleApiTokenVisibility: () -> Unit,
    onToggleTelegramTokenVisibility: () -> Unit,
    onShowMenuStub: (String) -> Unit,
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
    onSshPasswordChanged: (String) -> Unit,
    onWindowsPasswordChanged: (String) -> Unit,
    onToggleSshPasswordVisibility: () -> Unit,
    onToggleWindowsPasswordVisibility: () -> Unit,
    onSaveAuth: () -> Unit
) {
    var section by rememberSaveable { mutableStateOf(AppSection.MAIN) }

    val canSaveMonitoring = state.checkIntervalInput.isNotBlank() ||
        state.timeoutInput.isNotBlank() ||
        state.maxDowntimeInput.isNotBlank()
    val canSaveBot = state.telegramTokenInput.isNotBlank() || state.telegramChatIdInput.isNotBlank()
    val canSaveTime = state.quietStartInput.isNotBlank() ||
        state.quietEndInput.isNotBlank() ||
        state.metricsTimeInput.isNotBlank()
    val canSaveAuth = state.authModeInput.isNotBlank() ||
        state.sshUsernameInput.isNotBlank() ||
        state.sshPortInput.isNotBlank() ||
        state.windowsUsernameInput.isNotBlank() ||
        state.sshPasswordInput.isNotBlank() ||
        state.windowsPasswordInput.isNotBlank()

    val hiddenTransformation = PasswordVisualTransformation()

    Scaffold(
        topBar = { TopAppBar(title = { Text("Monitoring Android") }) }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
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
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = onRefresh, modifier = Modifier.fillMaxWidth()) {
                        Text("🔄 Доступность всех серверов")
                    }
                    Button(onClick = { onShowMenuStub("Доступность сервера") }, modifier = Modifier.fillMaxWidth()) {
                        Text("🔍 Доступность сервера")
                    }
                    Button(onClick = { onShowMenuStub("Ресурсы сервера") }, modifier = Modifier.fillMaxWidth()) {
                        Text("📊 Ресурсы сервера")
                    }
                    Button(onClick = { onShowMenuStub("Расширения") }, modifier = Modifier.fillMaxWidth()) {
                        Text("🛠️ Расширения")
                    }
                    Button(onClick = { section = AppSection.SETTINGS }, modifier = Modifier.fillMaxWidth()) {
                        Text("⚙️ Настройки")
                    }
                }
            }

            if (section == AppSection.MAIN) {
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
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Список серверов", fontWeight = FontWeight.Bold)
                }

                items(items = state.servers, key = { it.id }) { server ->
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

            if (section == AppSection.SETTINGS) {
                item {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { section = AppSection.MAIN }) { Text("← Назад") }
                    }
                }

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
                    OutlinedTextField(
                        value = state.sshPasswordInput,
                        onValueChange = onSshPasswordChanged,
                        label = { Text("ssh_password") },
                        modifier = Modifier.fillMaxWidth(),
                        visualTransformation = if (state.isSshPasswordVisible) VisualTransformation.None else hiddenTransformation,
                        trailingIcon = {
                            TextButton(onClick = onToggleSshPasswordVisibility) {
                                Text(if (state.isSshPasswordVisible) "Скрыть" else "Показать")
                            }
                        }
                    )
                    OutlinedTextField(
                        value = state.windowsPasswordInput,
                        onValueChange = onWindowsPasswordChanged,
                        label = { Text("windows_password") },
                        modifier = Modifier.fillMaxWidth(),
                        visualTransformation = if (state.isWindowsPasswordVisible) VisualTransformation.None else hiddenTransformation,
                        trailingIcon = {
                            TextButton(onClick = onToggleWindowsPasswordVisibility) {
                                Text(if (state.isWindowsPasswordVisible) "Скрыть" else "Показать")
                            }
                        }
                    )
                    Button(onClick = onSaveAuth, enabled = canSaveAuth) {
                        Text("Сохранить auth")
                    }
                }
            }
        }
    }
}
