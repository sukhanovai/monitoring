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
import ru.monitoring.mobile.ui.MainViewModel
import ru.monitoring.mobile.ui.MainUiState

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
                MonitoringApp(vm.state, vm::saveToken, vm::refreshAvailability, vm::sendAction, vm::updateSettings)
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
    onUpdateSettings: (String, String, String) -> Unit
) {
    var tokenInput by remember(state.token) { mutableStateOf(state.token) }
    var checkInterval by remember { mutableStateOf("") }
    var timeout by remember { mutableStateOf("") }
    var maxDowntime by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text("Monitoring Android") })
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

            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Статус", fontWeight = FontWeight.Bold)
                    Text(state.summaryText)
                    if (state.message.isNotBlank()) {
                        Text(state.message)
                    }
                }
            }

            Text("Быстрые действия", fontWeight = FontWeight.Bold)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { onAction("pause_monitoring") }) { Text("Пауза") }
                Button(onClick = { onAction("resume_monitoring") }) { Text("Старт") }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { onAction("send_morning_report") }) { Text("Отчёт") }
                Button(onClick = { onAction("force_quiet") }) { Text("Quiet") }
            }

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
            Button(onClick = { onUpdateSettings(checkInterval, timeout, maxDowntime) }) {
                Text("Сохранить настройки")
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
    }
}
