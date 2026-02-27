package ru.monitoring.mobile

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
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
import ru.monitoring.mobile.api.ManagedServer
import ru.monitoring.mobile.notifications.MorningReportWorker
import ru.monitoring.mobile.storage.AppPreferences
import ru.monitoring.mobile.ui.MainUiState
import ru.monitoring.mobile.ui.MonitoringTheme
import ru.monitoring.mobile.ui.MainViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ensureNotificationPermission()
        val preferences = AppPreferences(applicationContext)

        enableEdgeToEdge()
        setContent {
            val vm: MainViewModel = viewModel(factory = MainViewModel.Factory(applicationContext, preferences))
            val openMorningReport = intent?.getBooleanExtra(MorningReportWorker.EXTRA_OPEN_MORNING_REPORT, false) == true
            MonitoringTheme(darkTheme = vm.state.themeMode != "light") {
                LaunchedEffect(Unit) {
                    vm.loadInitialState()
                    if (openMorningReport) {
                        vm.markMorningReportRead()
                    }
                }

                MonitoringApp(
                    state = vm.state,
                    onTokenChanged = vm::setTokenInput,
                    onBaseUrlChanged = vm::setBaseUrlInput,
                    onSaveToken = vm::saveToken,
                    onSaveBaseUrl = vm::saveBaseUrl,
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
                    onNewTelegramChatIdChanged = vm::setNewTelegramChatIdInput,
                    onAddTelegramChatId = vm::addTelegramChatId,
                    onRemoveTelegramChatId = vm::removeTelegramChatId,
                    onQuietStartChanged = vm::setQuietStartInput,
                    onQuietEndChanged = vm::setQuietEndInput,
                    onMetricsTimeChanged = vm::setMetricsTimeInput,
                    onSaveTime = vm::updateTimeSettings,
                    onAuthModeChanged = vm::setAuthModeInput,
                    onSshUsernameChanged = vm::setSshUsernameInput,
                    onSshKeyPathChanged = vm::setSshKeyPathInput,
                    onSshPortChanged = vm::setSshPortInput,
                    onWindowsUsernameChanged = vm::setWindowsUsernameInput,
                    onSshPasswordChanged = vm::setSshPasswordInput,
                    onWindowsPasswordChanged = vm::setWindowsPasswordInput,
                    onToggleSshPasswordVisibility = vm::toggleSshPasswordVisibility,
                    onToggleWindowsPasswordVisibility = vm::toggleWindowsPasswordVisibility,
                    onSaveAuth = vm::updateAuthSettings,
                    onWindowsCredUsernameChanged = vm::setWindowsCredUsernameInput,
                    onWindowsCredPasswordChanged = vm::setWindowsCredPasswordInput,
                    onWindowsCredServerTypeChanged = vm::setWindowsCredServerTypeInput,
                    onWindowsCredPriorityChanged = vm::setWindowsCredPriorityInput,
                    onAddWindowsCredential = vm::addWindowsCredential,
                    onRemoveWindowsCredential = vm::removeWindowsCredential,
                    onCreateWindowsTypeInputChanged = vm::setCreateWindowsTypeInput,
                    onRenameOldTypeInputChanged = vm::setRenameOldTypeInput,
                    onRenameNewTypeInputChanged = vm::setRenameNewTypeInput,
                    onMergeSourceTypeInputChanged = vm::setMergeSourceTypeInput,
                    onMergeTargetTypeInputChanged = vm::setMergeTargetTypeInput,
                    onDeleteTypeInputChanged = vm::setDeleteTypeInput,
                    onDeleteTargetTypeInputChanged = vm::setDeleteTargetTypeInput,
                    onCreateWindowsType = vm::createWindowsType,
                    onRenameWindowsType = vm::renameWindowsType,
                    onMergeWindowsTypes = vm::mergeWindowsTypes,
                    onDeleteWindowsType = vm::deleteWindowsType,
                    onServerIpChanged = vm::setServerIpInput,
                    onServerNameChanged = vm::setServerNameInput,
                    onServerTypeChanged = vm::setServerTypeInput,
                    onServerTimeoutChanged = vm::setServerTimeoutInput,
                    onSaveServer = vm::saveServer,
                    onCheckServerAvailability = vm::refreshServerAvailability,
                    onEditServer = vm::startServerEdit,
                    onCancelServerEdit = vm::cancelServerEdit,
                    onDeleteServer = vm::deleteServer,
                    onToggleServerMonitoring = vm::toggleServerMonitoring,
                    onThemeModeChanged = vm::setThemeMode,
                    onMorningNotificationsEnabledChanged = vm::setMorningReportNotificationsEnabled,
                    onMarkMorningReportRead = vm::markMorningReportRead,
                    onClearMorningReport = vm::clearMorningReport
                )
            }
        }
    }

    private fun ensureNotificationPermission() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        val granted = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MonitoringApp(
    state: MainUiState,
    onTokenChanged: (String) -> Unit,
    onBaseUrlChanged: (String) -> Unit,
    onSaveToken: (String) -> Unit,
    onSaveBaseUrl: () -> Unit,
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
    onNewTelegramChatIdChanged: (String) -> Unit,
    onAddTelegramChatId: () -> Unit,
    onRemoveTelegramChatId: (String) -> Unit,
    onQuietStartChanged: (String) -> Unit,
    onQuietEndChanged: (String) -> Unit,
    onMetricsTimeChanged: (String) -> Unit,
    onSaveTime: () -> Unit,
    onAuthModeChanged: (String) -> Unit,
    onSshUsernameChanged: (String) -> Unit,
    onSshKeyPathChanged: (String) -> Unit,
    onSshPortChanged: (String) -> Unit,
    onWindowsUsernameChanged: (String) -> Unit,
    onSshPasswordChanged: (String) -> Unit,
    onWindowsPasswordChanged: (String) -> Unit,
    onToggleSshPasswordVisibility: () -> Unit,
    onToggleWindowsPasswordVisibility: () -> Unit,
    onSaveAuth: () -> Unit,
    onWindowsCredUsernameChanged: (String) -> Unit,
    onWindowsCredPasswordChanged: (String) -> Unit,
    onWindowsCredServerTypeChanged: (String) -> Unit,
    onWindowsCredPriorityChanged: (String) -> Unit,
    onAddWindowsCredential: () -> Unit,
    onRemoveWindowsCredential: (Int?) -> Unit,
    onCreateWindowsTypeInputChanged: (String) -> Unit,
    onRenameOldTypeInputChanged: (String) -> Unit,
    onRenameNewTypeInputChanged: (String) -> Unit,
    onMergeSourceTypeInputChanged: (String) -> Unit,
    onMergeTargetTypeInputChanged: (String) -> Unit,
    onDeleteTypeInputChanged: (String) -> Unit,
    onDeleteTargetTypeInputChanged: (String) -> Unit,
    onCreateWindowsType: () -> Unit,
    onRenameWindowsType: () -> Unit,
    onMergeWindowsTypes: () -> Unit,
    onDeleteWindowsType: () -> Unit,
    onServerIpChanged: (String) -> Unit,
    onServerNameChanged: (String) -> Unit,
    onServerTypeChanged: (String) -> Unit,
    onServerTimeoutChanged: (String) -> Unit,
    onSaveServer: () -> Unit,
    onCheckServerAvailability: (ManagedServer) -> Unit,
    onEditServer: (ManagedServer) -> Unit,
    onCancelServerEdit: () -> Unit,
    onDeleteServer: (String) -> Unit,
    onToggleServerMonitoring: (String, Boolean) -> Unit,
    onThemeModeChanged: (String) -> Unit,
    onMorningNotificationsEnabledChanged: (Boolean) -> Unit,
    onMarkMorningReportRead: () -> Unit,
    onClearMorningReport: () -> Unit
) {
    var isManagementExpanded by rememberSaveable { mutableStateOf(false) }
    var isSettingsExpanded by rememberSaveable { mutableStateOf(false) }
    var isSshAuthExpanded by rememberSaveable { mutableStateOf(false) }
    var isWindowsAuthExpanded by rememberSaveable { mutableStateOf(false) }
    var showWindowsAll by rememberSaveable { mutableStateOf(false) }
    var showWindowsByType by rememberSaveable { mutableStateOf(false) }
    var showWindowsTypeStats by rememberSaveable { mutableStateOf(false) }
    var showServerAvailabilityMenu by rememberSaveable { mutableStateOf(false) }
    var settingsSection by rememberSaveable { mutableStateOf("bff") }

    val canSaveMonitoring = state.checkIntervalInput.isNotBlank() ||
        state.timeoutInput.isNotBlank() ||
        state.maxDowntimeInput.isNotBlank()
    val canSaveBot = state.telegramTokenInput.isNotBlank() ||
        state.telegramChatIdInput.isNotBlank() ||
        state.telegramChatIds.isNotEmpty()
    val canSaveTime = state.quietStartInput.isNotBlank() ||
        state.quietEndInput.isNotBlank() ||
        state.metricsTimeInput.isNotBlank()
    val canSaveAuth = state.authModeInput.isNotBlank() ||
        state.sshUsernameInput.isNotBlank() ||
        state.sshKeyPathInput.isNotBlank() ||
        state.sshPortInput.isNotBlank() ||
        state.windowsUsernameInput.isNotBlank() ||
        state.sshPasswordInput.isNotBlank() ||
        state.windowsPasswordInput.isNotBlank()

    val hiddenTransformation = PasswordVisualTransformation()
    val windowsByType = state.windowsCredentials.groupBy { it.serverType ?: "default" }
    val windowsTotal = state.windowsCredentials.size
    val windowsTypes = windowsByType.keys.size

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
                        Text("РЎС‚Р°С‚СѓСЃ", fontWeight = FontWeight.Bold)
                        Text(state.summaryText)
                        Text("Р’РµСЂСЃРёСЏ Р±РѕС‚Р°: ${state.botVersion}")
                        Text("Р’РµСЂСЃРёСЏ Android: ${state.androidAppVersion}")
                        if (state.message.isNotBlank()) {
                            Text(state.message)
                        }
                    }
                }
            }

            item {
                if (state.morningReportText.isNotBlank()) {
                    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚", fontWeight = FontWeight.Bold)
                            Text(state.morningReportText)
                            if (state.morningReportReceivedAt.isNotBlank()) {
                                Text("РџРѕР»СѓС‡РµРЅ: ${state.morningReportReceivedAt}")
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                if (state.morningReportUnread) {
                                    Button(onClick = onMarkMorningReportRead) { Text("РџСЂРѕС‡РёС‚Р°РЅРѕ") }
                                }
                                Button(onClick = onClearMorningReport) { Text("Р—Р°РєСЂС‹С‚СЊ") }
                            }
                        }
                    }
                }
            }

            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { onAction("send_morning_report") }, modifier = Modifier.fillMaxWidth()) {
                        Text("рџЊ… РћС‚С‡С‘С‚")
                    }
                    Button(onClick = onRefresh, modifier = Modifier.fillMaxWidth()) {
                        Text("рџ–Ґ Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ")
                    }
                    Button(onClick = { showServerAvailabilityMenu = !showServerAvailabilityMenu }, modifier = Modifier.fillMaxWidth()) {
                        Text("🔍 Доступность сервера")
                    }
                    if (showServerAvailabilityMenu) {
                        state.managedServers.forEach { server ->
                            Button(
                                onClick = { onCheckServerAvailability(server) },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("${server.name} (${server.ip})")
                            }
                        }
                    }
                    Button(onClick = { onShowMenuStub("Р РµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР°") }, modifier = Modifier.fillMaxWidth()) {
                        Text("рџ“Љ Р РµСЃСѓСЂСЃС‹ СЃРµСЂРІРµСЂР°")
                    }
                    Button(onClick = { onShowMenuStub("Р Р°СЃС€РёСЂРµРЅРёСЏ") }, modifier = Modifier.fillMaxWidth()) {
                        Text("рџ› пёЏ Р Р°СЃС€РёСЂРµРЅРёСЏ")
                    }
                    Button(onClick = { isManagementExpanded = !isManagementExpanded }, modifier = Modifier.fillMaxWidth()) {
                        Text("рџЋ›пёЏ РЈРїСЂР°РІР»РµРЅРёРµ")
                    }
                    if (isManagementExpanded) {
                        Text("РЈРїСЂР°РІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј", fontWeight = FontWeight.Bold)
                        Text("РЎС‚Р°С‚СѓСЃ: ${state.monitoringStatusText}")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAction("pause_monitoring") }) { Text("РџР°СѓР·Р°") }
                            Button(onClick = { onAction("resume_monitoring") }) { Text("РЎС‚Р°СЂС‚") }
                        }
                        Text("РЈРїСЂР°РІР»РµРЅРёРµ С‚РёС…РёРј СЂРµР¶РёРјРѕРј", fontWeight = FontWeight.Bold)
                        Text("РЎС‚Р°С‚СѓСЃ: ${state.silentStatusText}")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAction("force_quiet") }) { Text("РўРёС…РёР№") }
                            Button(onClick = { onAction("force_loud") }) { Text("Р“СЂРѕРјРєРёР№") }
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAction("auto_mode") }) { Text("РђРІС‚Рѕ") }
                        }
                    }
                    Button(onClick = { isSettingsExpanded = !isSettingsExpanded }, modifier = Modifier.fillMaxWidth()) {
                        Text("вљ™пёЏ РќР°СЃС‚СЂРѕР№РєРё")
                    }
                    if (isSettingsExpanded) {
                        Text("Р Р°Р·РґРµР»С‹ РЅР°СЃС‚СЂРѕРµРє", fontWeight = FontWeight.Bold)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { settingsSection = "bff" }) { Text("BFF") }
                            Button(onClick = { settingsSection = "monitoring" }) { Text("РњРѕРЅРёС‚РѕСЂРёРЅРі") }
                            Button(onClick = { settingsSection = "bot" }) { Text("Р‘РѕС‚") }
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { settingsSection = "time" }) { Text("Р’СЂРµРјСЏ") }
                            Button(onClick = { settingsSection = "auth" }) { Text("РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ") }
                            Button(onClick = { settingsSection = "servers" }) { Text("РЎРµСЂРІРµСЂС‹") }
                            Button(onClick = { settingsSection = "appearance" }) { Text("РўРµРјР°") }
                        }

                        if (settingsSection == "bff") {
                            Text("РџРѕРґРєР»СЋС‡РµРЅРёРµ Рє BFF", fontWeight = FontWeight.Bold)
                        OutlinedTextField(
                            value = state.baseUrlInput,
                            onValueChange = onBaseUrlChanged,
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Base URL API") }
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = onSaveBaseUrl) { Text("РЎРѕС…СЂР°РЅРёС‚СЊ URL") }
                        }
                        OutlinedTextField(
                            value = state.token,
                            onValueChange = onTokenChanged,
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Bearer С‚РѕРєРµРЅ") },
                            visualTransformation = if (state.isApiTokenVisible) VisualTransformation.None else hiddenTransformation,
                            trailingIcon = {
                                TextButton(onClick = onToggleApiTokenVisibility) {
                                    Text(if (state.isApiTokenVisible) "РЎРєСЂС‹С‚СЊ" else "РџРѕРєР°Р·Р°С‚СЊ")
                                }
                            }
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onSaveToken(state.token) }) { Text("РЎРѕС…СЂР°РЅРёС‚СЊ С‚РѕРєРµРЅ") }
                        }
                        }

                        if (settingsSection == "monitoring") {
                        Text("РќР°СЃС‚СЂРѕР№РєРё РјРѕРЅРёС‚РѕСЂРёРЅРіР°", fontWeight = FontWeight.Bold)
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
                            Text("РЎРѕС…СЂР°РЅРёС‚СЊ monitoring")
                        }
                        }

                        if (settingsSection == "bot") {
                        Text("РќР°СЃС‚СЂРѕР№РєРё Р±РѕС‚Р°", fontWeight = FontWeight.Bold)
                        OutlinedTextField(
                            value = state.telegramTokenInput,
                            onValueChange = onTelegramTokenChanged,
                            label = { Text("telegram_bot_token") },
                            modifier = Modifier.fillMaxWidth(),
                            visualTransformation = if (state.isTelegramTokenVisible) VisualTransformation.None else hiddenTransformation,
                            trailingIcon = {
                                TextButton(onClick = onToggleTelegramTokenVisibility) {
                                    Text(if (state.isTelegramTokenVisible) "РЎРєСЂС‹С‚СЊ" else "РџРѕРєР°Р·Р°С‚СЊ")
                                }
                            }
                        )
                        OutlinedTextField(
                            value = state.telegramChatIdInput,
                            onValueChange = onTelegramChatIdChanged,
                            label = { Text("telegram_chat_id (legacy)") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (state.telegramChatIds.isNotEmpty()) {
                            Text("Р§Р°С‚С‹ Telegram (${state.telegramChatIds.size})", fontWeight = FontWeight.Bold)
                            state.telegramChatIds.forEach { chatId ->
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Text(chatId, modifier = Modifier.weight(1f))
                                    Button(onClick = { onRemoveTelegramChatId(chatId) }) { Text("РЈРґР°Р»РёС‚СЊ") }
                                }
                            }
                        }
                        OutlinedTextField(
                            value = state.newTelegramChatIdInput,
                            onValueChange = onNewTelegramChatIdChanged,
                            label = { Text("РќРѕРІС‹Р№ chat_id") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = onAddTelegramChatId) { Text("Р”РѕР±Р°РІРёС‚СЊ chat_id") }
                        }
                        Button(onClick = onSaveBot, enabled = canSaveBot) {
                            Text("РЎРѕС…СЂР°РЅРёС‚СЊ bot")
                        }
                        }

                        if (settingsSection == "time") {
                        Text("Р’СЂРµРјРµРЅРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё", fontWeight = FontWeight.Bold)
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
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onMorningNotificationsEnabledChanged(true) }) { Text("РЈРІРµРґРѕРјР»РµРЅРёСЏ Р’РљР›") }
                            Button(onClick = { onMorningNotificationsEnabledChanged(false) }) { Text("РЈРІРµРґРѕРјР»РµРЅРёСЏ Р’Р«РљР›") }
                        }
                        Text("РЎС‚Р°С‚СѓСЃ СѓРІРµРґРѕРјР»РµРЅРёР№: ${if (state.morningReportNotificationsEnabled) "РІРєР»СЋС‡РµРЅС‹" else "РІС‹РєР»СЋС‡РµРЅС‹"}")
                        Button(onClick = onSaveTime, enabled = canSaveTime) {
                            Text("РЎРѕС…СЂР°РЅРёС‚СЊ time")
                        }
                        }

                        if (settingsSection == "appearance") {
                            Text("Оформление", fontWeight = FontWeight.Bold)
                            Text("Текущая тема: ${if (state.themeMode == "light") "светлая" else "темная"}")
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = { onThemeModeChanged("dark") }) { Text("Темная") }
                                Button(onClick = { onThemeModeChanged("light") }) { Text("Светлая") }
                            }
                        }

                        if (settingsSection == "auth") {
                        Text("рџ”ђ РќР°СЃС‚СЂРѕР№РєРё Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё", fontWeight = FontWeight.Bold)
                            Text("SSH Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ:", fontWeight = FontWeight.Bold)
                            Text("вЂў РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ: ${state.sshUsernameInput.ifBlank { "root" }}")
                            Text("вЂў РџСѓС‚СЊ Рє РєР»СЋС‡Сѓ: ${state.sshKeyPathInput.ifBlank { "/root/.ssh/id_rsa" }}")
                            Spacer(modifier = Modifier.height(4.dp))
                            Text("Windows Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ:", fontWeight = FontWeight.Bold)
                            Text("вЂў РЈС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№: $windowsTotal")
                            Text("вЂў РўРёРїРѕРІ СЃРµСЂРІРµСЂРѕРІ: $windowsTypes")

                            Button(onClick = { isSshAuthExpanded = !isSshAuthExpanded }, modifier = Modifier.fillMaxWidth()) {
                                Text("рџ‘¤ SSH Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ")
                            }
                            if (isSshAuthExpanded) {
                                OutlinedTextField(
                                    value = state.sshUsernameInput,
                                    onValueChange = onSshUsernameChanged,
                                    label = { Text("SSH РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                OutlinedTextField(
                                    value = state.sshKeyPathInput,
                                    onValueChange = onSshKeyPathChanged,
                                    label = { Text("РџСѓС‚СЊ Рє SSH РєР»СЋС‡Сѓ") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Button(onClick = onSaveAuth, enabled = canSaveAuth) { Text("РЎРѕС…СЂР°РЅРёС‚СЊ SSH") }
                            }

                            Button(onClick = { isWindowsAuthExpanded = !isWindowsAuthExpanded }, modifier = Modifier.fillMaxWidth()) {
                                Text("рџ–Ґ Windows Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ")
                            }
                            if (isWindowsAuthExpanded) {
                                Button(onClick = { showWindowsAll = !showWindowsAll }, modifier = Modifier.fillMaxWidth()) {
                                    Text("рџ‘Ґ РџСЂРѕСЃРјРѕС‚СЂ РІСЃРµС… СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№")
                                }
                                if (showWindowsAll) {
                                    state.windowsCredentials.forEach { cred ->
                                        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                            Column(modifier = Modifier.padding(10.dp)) {
                                                Text("рџџў ${cred.serverType ?: "default"} (РїСЂРёРѕСЂРёС‚РµС‚: ${cred.priority ?: 0})")
                                                Text("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ: ${cred.username ?: "-"}")
                                                Text("ID: ${cred.id ?: "-"}")
                                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                    Button(onClick = { onRemoveWindowsCredential(cred.id) }) { Text("РЈРґР°Р»РёС‚СЊ") }
                                                }
                                            }
                                        }
                                    }
                                }

                                Text("вћ• Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ", fontWeight = FontWeight.Bold)
                                OutlinedTextField(
                                    value = state.windowsCredUsernameInput,
                                    onValueChange = onWindowsCredUsernameChanged,
                                    label = { Text("РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                OutlinedTextField(
                                    value = state.windowsCredPasswordInput,
                                    onValueChange = onWindowsCredPasswordChanged,
                                    label = { Text("РџР°СЂРѕР»СЊ") },
                                    modifier = Modifier.fillMaxWidth(),
                                    visualTransformation = if (state.isWindowsPasswordVisible) VisualTransformation.None else hiddenTransformation,
                                    trailingIcon = {
                                        TextButton(onClick = onToggleWindowsPasswordVisibility) {
                                            Text(if (state.isWindowsPasswordVisible) "РЎРєСЂС‹С‚СЊ" else "РџРѕРєР°Р·Р°С‚СЊ")
                                        }
                                    }
                                )
                                OutlinedTextField(
                                    value = state.windowsCredServerTypeInput,
                                    onValueChange = onWindowsCredServerTypeChanged,
                                    label = { Text("РўРёРї СЃРµСЂРІРµСЂРѕРІ") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                OutlinedTextField(
                                    value = state.windowsCredPriorityInput,
                                    onValueChange = onWindowsCredPriorityChanged,
                                    label = { Text("РџСЂРёРѕСЂРёС‚РµС‚") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Button(onClick = onAddWindowsCredential) { Text("Р”РѕР±Р°РІРёС‚СЊ СѓС‡РµС‚РЅСѓСЋ Р·Р°РїРёСЃСЊ") }

                                Button(onClick = { showWindowsByType = !showWindowsByType }, modifier = Modifier.fillMaxWidth()) {
                                    Text("рџ“Љ РЈС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ РїРѕ С‚РёРїР°Рј")
                                }
                                if (showWindowsByType) {
                                    windowsByType.forEach { (serverType, creds) ->
                                        Text("$serverType (${creds.size} СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№):", fontWeight = FontWeight.Bold)
                                        creds.take(3).forEach { cred ->
                                            Text("вЂў ${cred.username ?: "-"} (РїСЂРёРѕСЂРёС‚РµС‚: ${cred.priority ?: 0})")
                                        }
                                        if (creds.size > 3) {
                                            Text("... Рё РµС‰Рµ ${creds.size - 3}")
                                        }
                                    }
                                }

                                Button(onClick = { showWindowsTypeStats = !showWindowsTypeStats }, modifier = Modifier.fillMaxWidth()) {
                                    Text("вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ С‚РёРїР°РјРё СЃРµСЂРІРµСЂРѕРІ")
                                }
                                if (showWindowsTypeStats) {
                                    Text("РЎСѓС‰РµСЃС‚РІСѓСЋС‰РёРµ С‚РёРїС‹:", fontWeight = FontWeight.Bold)
                                    if (state.windowsTypes.isNotEmpty()) {
                                        state.windowsTypes.forEach { type ->
                                            Text("вЂў ${type.name}: ${type.active}/${type.total} Р°РєС‚РёРІРЅС‹С… СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№")
                                        }
                                    } else {
                                        windowsByType.keys.sorted().forEach { type ->
                                            val total = windowsByType[type]?.size ?: 0
                                            Text("вЂў $type: $total/$total Р°РєС‚РёРІРЅС‹С… СѓС‡РµС‚РЅС‹С… Р·Р°РїРёСЃРµР№")
                                        }
                                    }

                                    Text("РЎРѕР·РґР°С‚СЊ РЅРѕРІС‹Р№ С‚РёРї", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.createWindowsTypeInput,
                                        onValueChange = onCreateWindowsTypeInputChanged,
                                        label = { Text("РРјСЏ РЅРѕРІРѕРіРѕ С‚РёРїР°") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onCreateWindowsType) { Text("РЎРѕР·РґР°С‚СЊ С‚РёРї") }

                                    Text("РџРµСЂРµРёРјРµРЅРѕРІР°С‚СЊ С‚РёРї", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.renameOldTypeInput,
                                        onValueChange = onRenameOldTypeInputChanged,
                                        label = { Text("РЎС‚Р°СЂРѕРµ РёРјСЏ С‚РёРїР°") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    OutlinedTextField(
                                        value = state.renameNewTypeInput,
                                        onValueChange = onRenameNewTypeInputChanged,
                                        label = { Text("РќРѕРІРѕРµ РёРјСЏ С‚РёРїР°") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onRenameWindowsType) { Text("РџРµСЂРµРёРјРµРЅРѕРІР°С‚СЊ") }

                                    Text("РћР±СЉРµРґРёРЅРёС‚СЊ С‚РёРїС‹", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.mergeSourceTypeInput,
                                        onValueChange = onMergeSourceTypeInputChanged,
                                        label = { Text("Source type") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    OutlinedTextField(
                                        value = state.mergeTargetTypeInput,
                                        onValueChange = onMergeTargetTypeInputChanged,
                                        label = { Text("Target type") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onMergeWindowsTypes) { Text("РћР±СЉРµРґРёРЅРёС‚СЊ") }

                                    Text("РЈРґР°Р»РёС‚СЊ С‚РёРї", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.deleteTypeInput,
                                        onValueChange = onDeleteTypeInputChanged,
                                        label = { Text("РЈРґР°Р»СЏРµРјС‹Р№ С‚РёРї") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    OutlinedTextField(
                                        value = state.deleteTargetTypeInput,
                                        onValueChange = onDeleteTargetTypeInputChanged,
                                        label = { Text("РџРµСЂРµРЅРµСЃС‚Рё РІ С‚РёРї (target)") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onDeleteWindowsType) { Text("РЈРґР°Р»РёС‚СЊ С‚РёРї") }
                                }
                            }
                        }

                        if (settingsSection == "servers") {
                            Text("рџ–ҐпёЏ РЎРµСЂРІРµСЂС‹", fontWeight = FontWeight.Bold)
                            Text("Р’СЃРµРіРѕ: ${state.managedServers.size}")
                            Text("РђРєС‚РёРІРЅС‹С…: ${state.managedServers.count { it.enabled == true }}")

                            Text(
                                if (state.serverEditIp.isBlank()) "Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ" else "Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ СЃРµСЂРІРµСЂР° ${state.serverEditIp}",
                                fontWeight = FontWeight.Bold
                            )
                            OutlinedTextField(
                                value = state.serverIpInput,
                                onValueChange = onServerIpChanged,
                                label = { Text("IP СЃРµСЂРІРµСЂР°") },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = state.serverEditIp.isBlank()
                            )
                            OutlinedTextField(
                                value = state.serverNameInput,
                                onValueChange = onServerNameChanged,
                                label = { Text("РРјСЏ СЃРµСЂРІРµСЂР°") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            OutlinedTextField(
                                value = state.serverTypeInput,
                                onValueChange = onServerTypeChanged,
                                label = { Text("РўРёРї (rdp/ssh/ping)") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            OutlinedTextField(
                                value = state.serverTimeoutInput,
                                onValueChange = onServerTimeoutChanged,
                                label = { Text("Timeout (СЃРµРє)") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = onSaveServer) {
                                    Text(if (state.serverEditIp.isBlank()) "Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ" else "РЎРѕС…СЂР°РЅРёС‚СЊ РёР·РјРµРЅРµРЅРёСЏ")
                                }
                                if (state.serverEditIp.isNotBlank()) {
                                    Button(onClick = onCancelServerEdit) { Text("РћС‚РјРµРЅР°") }
                                }
                            }

                            state.managedServers.forEach { server ->
                                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                    Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Text("${server.name} (${server.ip})", fontWeight = FontWeight.Bold)
                                        Text("РўРёРї: ${server.type}, timeout: ${server.timeout ?: 30} СЃРµРє")
                                        Text("РњРѕРЅРёС‚РѕСЂРёРЅРі: ${if (server.enabled == true) "РІРєР»СЋС‡РµРЅ" else "РІС‹РєР»СЋС‡РµРЅ"}")
                                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Button(onClick = { onToggleServerMonitoring(server.ip, server.enabled != true) }) {
                                                Text(if (server.enabled == true) "Р’С‹РєР»СЋС‡РёС‚СЊ" else "Р’РєР»СЋС‡РёС‚СЊ")
                                            }
                                            Button(onClick = { onEditServer(server) }) { Text("Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ") }
                                            Button(onClick = { onDeleteServer(server.ip) }) { Text("РЈРґР°Р»РёС‚СЊ") }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

        }
    }
}
