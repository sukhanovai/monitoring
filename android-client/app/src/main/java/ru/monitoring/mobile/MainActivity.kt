package ru.monitoring.mobile

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.background
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import ru.monitoring.mobile.api.ExtensionItem
import ru.monitoring.mobile.api.ManagedServer
import ru.monitoring.mobile.notifications.MorningReportWorker
import ru.monitoring.mobile.notifications.ServerDownAlertWorker
import ru.monitoring.mobile.storage.AppPreferences
import ru.monitoring.mobile.ui.MainUiState
import ru.monitoring.mobile.ui.MonitoringTheme
import ru.monitoring.mobile.ui.MainViewModel

private data class MainMenuExtensionButton(
    val extensionId: String,
    val label: String,
    val action: String
)

private val MAIN_MENU_EXTENSION_BUTTONS = listOf(
    MainMenuExtensionButton("resource_monitor", "📊 Ресурсы сервера", "check_resources"),
    MainMenuExtensionButton("backup_monitor", "💾 Бэкапы Proxmox", "backup_proxmox"),
    MainMenuExtensionButton("database_backup_monitor", "🗃️ Бэкапы БД", "backup_databases"),
    MainMenuExtensionButton("mail_backup_monitor", "📬 Бэкапы почты", "backup_mail"),
    MainMenuExtensionButton("stock_load_monitor", "📦 Остатки 1С", "backup_stock_loads"),
    MainMenuExtensionButton("supplier_stock_files", "📦 Результаты остатков поставщиков", "supplier_stock_reports"),
    MainMenuExtensionButton("zfs_monitor", "🧊 ZFS", "zfs_menu")
)

class MainActivity : ComponentActivity() {
    private var downServersFromNotification by mutableStateOf<List<String>>(emptyList())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ensureNotificationPermission()
        val preferences = AppPreferences(applicationContext)
        downServersFromNotification = extractDownServersFromIntent()

        enableEdgeToEdge()
        setContent {
            val vm: MainViewModel = viewModel(factory = MainViewModel.Factory(applicationContext, preferences))
            val openMorningReport = intent?.getBooleanExtra(MorningReportWorker.EXTRA_OPEN_MORNING_REPORT, false) == true
            MonitoringTheme(darkTheme = vm.state.themeMode != "light") {
                LaunchedEffect(openMorningReport, downServersFromNotification) {
                    vm.loadInitialState()
                    if (openMorningReport) {
                        vm.markMorningReportRead()
                    }
                    if (downServersFromNotification.isNotEmpty()) {
                        vm.applyServerDownNotification(downServersFromNotification)
                    }
                }

                MonitoringApp(
                    state = vm.state,
                    onTokenChanged = vm::setTokenInput,
                    onBaseUrlChanged = vm::setBaseUrlInput,
                    onSaveToken = vm::saveToken,
                    onSaveBaseUrl = vm::saveBaseUrl,
                    onRefreshData = vm::refreshData,
                    onRefresh = vm::refreshAvailability,
                    onCloseApp = { moveTaskToBack(true) },
                    onToggleApiTokenVisibility = vm::toggleApiTokenVisibility,
                    onToggleTelegramTokenVisibility = vm::toggleTelegramTokenVisibility,
                    onToggleExtension = vm::toggleExtension,
                    onEnableAllExtensions = vm::enableAllExtensions,
                    onDisableAllExtensions = vm::disableAllExtensions,
                    onOpenExtensionsSettingsMenu = vm::openExtensionsSettingsMenu,
                    onExtensionsSettingsAction = vm::runExtensionsSettingsAction,
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
                    onCheckServerResources = vm::refreshServerResources,
                    onToggleProxmoxBackupMenu = vm::toggleProxmoxBackupMenu,
                    onToggleDatabaseBackupMenu = vm::toggleDatabaseBackupMenu,
                    onToggleMailBackupMenu = vm::toggleMailBackupMenu,
                    onEditServer = vm::startServerEdit,
                    onCancelServerEdit = vm::cancelServerEdit,
                    onDeleteServer = vm::deleteServer,
                    onToggleServerMonitoring = vm::toggleServerMonitoring,
                    onThemeModeChanged = vm::setThemeMode,
                    onMorningNotificationsEnabledChanged = vm::setMorningReportNotificationsEnabled,
                    onMarkMorningReportRead = vm::markMorningReportRead,
                    onClearMorningReport = vm::clearMorningReport,
                    onOpenUpdateUrl = { url ->
                        if (url.isNotBlank()) {
                            runCatching {
                                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                            }
                        }
                    }
                )
            }
        }
    }

    override fun onNewIntent(intent: android.content.Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        downServersFromNotification = extractDownServersFromIntent()
    }

    private fun extractDownServersFromIntent(): List<String> =
        intent?.getStringArrayExtra(ServerDownAlertWorker.EXTRA_DOWN_SERVER_NAMES)
            ?.toList()
            ?.map { it.trim() }
            ?.filter { it.isNotBlank() }
            ?: emptyList()

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

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
private fun MonitoringApp(
    state: MainUiState,
    onTokenChanged: (String) -> Unit,
    onBaseUrlChanged: (String) -> Unit,
    onSaveToken: (String) -> Unit,
    onSaveBaseUrl: () -> Unit,
    onRefreshData: () -> Unit,
    onRefresh: () -> Unit,
    onCloseApp: () -> Unit,
    onToggleApiTokenVisibility: () -> Unit,
    onToggleTelegramTokenVisibility: () -> Unit,
    onToggleExtension: (String, Boolean) -> Unit,
    onEnableAllExtensions: () -> Unit,
    onDisableAllExtensions: () -> Unit,
    onOpenExtensionsSettingsMenu: () -> Unit,
    onExtensionsSettingsAction: (String) -> Unit,
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
    onCheckServerResources: (ManagedServer) -> Unit,
    onToggleProxmoxBackupMenu: () -> Unit,
    onToggleDatabaseBackupMenu: () -> Unit,
    onToggleMailBackupMenu: () -> Unit,
    onEditServer: (ManagedServer) -> Unit,
    onCancelServerEdit: () -> Unit,
    onDeleteServer: (String) -> Unit,
    onToggleServerMonitoring: (String, Boolean) -> Unit,
    onThemeModeChanged: (String) -> Unit,
    onMorningNotificationsEnabledChanged: (Boolean) -> Unit,
    onMarkMorningReportRead: () -> Unit,
    onClearMorningReport: () -> Unit,
    onOpenUpdateUrl: (String) -> Unit
) {
    var isManagementExpanded by rememberSaveable { mutableStateOf(false) }
    var isSettingsExpanded by rememberSaveable { mutableStateOf(false) }
    var isExtensionsSettingsOpened by rememberSaveable { mutableStateOf(false) }
    var isSshAuthExpanded by rememberSaveable { mutableStateOf(false) }
    var isWindowsAuthExpanded by rememberSaveable { mutableStateOf(false) }
    var showWindowsAll by rememberSaveable { mutableStateOf(false) }
    var showWindowsByType by rememberSaveable { mutableStateOf(false) }
    var showWindowsTypeStats by rememberSaveable { mutableStateOf(false) }
    var showServerAvailabilityMenu by rememberSaveable { mutableStateOf(false) }
    var showServerResourcesMenu by rememberSaveable { mutableStateOf(false) }
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
    val enabledExtensions = state.extensions.filter { it.enabled }.map { it.id }.toSet()
    val extensionButtons = MAIN_MENU_EXTENSION_BUTTONS.filter { it.extensionId in enabledExtensions }
    val isResourceMonitorEnabled = "resource_monitor" in enabledExtensions

    Scaffold(
        topBar = { TopAppBar(title = { Text("Monitoring") }) }
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (state.isUpdateRequired) {
                item {
                    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("⚠ Требуется обновление", fontWeight = FontWeight.Bold)
                            Text(state.updateMessage.ifBlank { "Нужно обновить приложение для продолжения работы" })
                            if (state.minSupportedVersion.isNotBlank()) {
                                Text("Минимальная версия: ${state.minSupportedVersion}")
                            }
                            Text("Установленная версия: ${state.installedVersion.ifBlank { state.projectVersion }}")
                            if (state.latestVersion.isNotBlank()) {
                                Text("Актуальная версия: ${state.latestVersion}")
                            }
                            Button(
                                onClick = { onOpenUpdateUrl(state.apkDownloadUrl) },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = state.apkDownloadUrl.isNotBlank(),
                            ) {
                                Text("Обновить приложение")
                            }
                            Text("Пока не обновишься — функционал заблокирован.")
                        }
                    }
                }
                return@LazyColumn
            }

            item {
                if (state.isLoading) {
                    CircularProgressIndicator()
                }

                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Статус", fontWeight = FontWeight.Bold)
                        Text(state.summaryText)
                        Text("Версия проекта: ${state.projectVersion}")
                        if (state.message.isNotBlank() && state.messageSource == "global") {
                            Text(state.message)
                        }
                    }
                }
            }

            item {
                if (state.morningReportText.isNotBlank()) {
                    ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("Утренний отчет", fontWeight = FontWeight.Bold)
                            Text(state.morningReportText)
                            if (state.morningReportReceivedAt.isNotBlank()) {
                                Text("Получен: ${state.morningReportReceivedAt}")
                            }
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                if (state.morningReportUnread) {
                                    Button(onClick = onMarkMorningReportRead) { Text("Прочитано") }
                                }
                                Button(onClick = onClearMorningReport) { Text("Закрыть") }
                            }
                        }
                    }
                }
            }

            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Быстрые действия", fontWeight = FontWeight.Bold)
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        maxItemsInEachRow = 2
                    ) {
                        Button(
                            onClick = onRefreshData,
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("🔄 Обновить")
                        }
                        Button(
                            onClick = { onAction("send_morning_report") },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("🌅 Отчёт")
                        }
                    }
                    if (state.message.isNotBlank() && state.messageSource == "morning_report") {
                        Text(state.message)
                    }
                    Text("Проверки", fontWeight = FontWeight.Bold)
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        maxItemsInEachRow = 2
                    ) {
                        Button(
                            onClick = onRefresh,
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("🖥 Все серверы")
                        }
                        Button(
                            onClick = { showServerAvailabilityMenu = !showServerAvailabilityMenu },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("🔍 По серверу")
                        }
                    }
                    if (state.message.isNotBlank() && state.messageSource == "all_servers") {
                        Text(state.message)
                    }
                    if (showServerAvailabilityMenu) {
                        state.managedServers.forEach { server ->
                            val serverTarget = if (server.ip.isNotBlank()) server.ip else server.name
                            if (
                                state.message.isNotBlank() &&
                                state.messageSource == "server_availability" &&
                                state.availabilityServerMessageTarget == serverTarget
                            ) {
                                Text(state.message)
                            }
                            Button(
                                onClick = { onCheckServerAvailability(server) },
                                modifier = Modifier.fillMaxWidth(),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                                    contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                                )
                            ) {
                                Text("${server.name} (${server.ip})")
                            }
                        }
                    }
                    Text("Расширения", fontWeight = FontWeight.Bold)
                    extensionButtons.forEach { extensionButton ->
                        Button(
                            onClick = {
                                when (extensionButton.action) {
                                    "check_resources" -> showServerResourcesMenu = !showServerResourcesMenu
                                    "backup_proxmox" -> onToggleProxmoxBackupMenu()
                                    "backup_databases" -> onToggleDatabaseBackupMenu()
                                    "backup_mail" -> onToggleMailBackupMenu()
                                    else -> onAction(extensionButton.action)
                                }
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(extensionButton.label)
                        }
                        if (extensionButton.action == "check_resources" && isResourceMonitorEnabled && showServerResourcesMenu) {
                            state.managedServers.forEach { server ->
                                val serverTarget = if (server.ip.isNotBlank()) server.ip else server.name
                                if (
                                    state.message.isNotBlank() &&
                                    state.messageSource == "server_resources" &&
                                    state.availabilityServerMessageTarget == serverTarget
                                ) {
                                    Text(state.message)
                                }
                                Button(
                                    onClick = { onCheckServerResources(server) },
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                                        contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                                    )
                                ) {
                                    Text("${server.name} (${server.ip})")
                                }
                            }
                        }
                        if (
                            state.extensionMenuOptions.isNotEmpty() &&
                            ((extensionButton.action == "backup_proxmox" && state.extensionMenuAction == "backup_proxmox") ||
                                (extensionButton.action == "backup_databases" && state.extensionMenuAction == "backup_databases") ||
                                (extensionButton.action == "backup_mail" && state.extensionMenuAction == "backup_mail"))
                        ) {
                            val menuTitle = when (extensionButton.action) {
                                "backup_databases" -> "Выбор базы"
                                "backup_mail" -> "Выбор почтового ящика"
                                else -> "Выбор сервера"
                            }
                            Text(menuTitle, fontWeight = FontWeight.Bold)
                            state.extensionMenuOptions.forEach { item ->
                                val optionLabel = item.label?.trim().orEmpty()
                                val optionAction = item.action?.trim().orEmpty()
                                val callbackAction = item.callbackData?.trim().orEmpty()
                                val callbackActionCamel = item.callbackDataCamel?.trim().orEmpty()
                                val targetAction = when {
                                    optionAction.isNotBlank() -> optionAction
                                    callbackAction.isNotBlank() -> callbackAction
                                    callbackActionCamel.isNotBlank() -> callbackActionCamel
                                    else -> ""
                                }
                                if (optionLabel.isNotBlank() && targetAction.isNotBlank()) {
                                    Button(
                                        onClick = { onAction(targetAction) },
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                                            contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                                        )
                                    ) {
                                        Text(optionLabel)
                                    }
                                }
                            }
                        }
                        if (
                            extensionButton.action == "backup_mail" &&
                            state.mailBackupHistoryItems.isNotEmpty()
                        ) {
                            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                Column(
                                    modifier = Modifier.padding(12.dp),
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    Text(
                                        text = if (state.mailBackupHistoryTitle.isNotBlank()) {
                                            state.mailBackupHistoryTitle
                                        } else {
                                            "📬 Бэкапы почтового сервера"
                                        },
                                        fontWeight = FontWeight.Bold
                                    )
                                    Column(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .clip(RoundedCornerShape(10.dp))
                                            .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f))
                                            .padding(horizontal = 8.dp, vertical = 6.dp),
                                        verticalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        state.mailBackupHistoryItems.forEach { backup ->
                                            val statusColor = when (backup.statusIcon) {
                                                "✅", "✔" -> Color(0xFF42D37D)
                                                "⚠️" -> Color(0xFFF5C451)
                                                else -> MaterialTheme.colorScheme.error
                                            }
                                            Row(
                                                modifier = Modifier.fillMaxWidth(),
                                                verticalAlignment = Alignment.CenterVertically,
                                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                                            ) {
                                                Text(
                                                    text = backup.statusIcon,
                                                    color = statusColor,
                                                    fontWeight = FontWeight.SemiBold
                                                )
                                                Text(
                                                    text = "${backup.size} — ${backup.path}",
                                                    color = MaterialTheme.colorScheme.onSurface,
                                                    maxLines = 1,
                                                    overflow = TextOverflow.Ellipsis,
                                                    modifier = Modifier.weight(1f)
                                                )
                                                Text(
                                                    text = "(${backup.relativeTime})",
                                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                                    fontSize = 12.sp
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Button(onClick = { isManagementExpanded = !isManagementExpanded }, modifier = Modifier.fillMaxWidth()) {
                        Text("🎛️ Управление")
                    }
                    if (isManagementExpanded) {
                        Text("Управление мониторингом", fontWeight = FontWeight.Bold)
                        Text("Статус: ${state.monitoringStatusText}")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAction("pause_monitoring") }) { Text("Пауза") }
                            Button(onClick = { onAction("resume_monitoring") }) { Text("Старт") }
                        }
                        Text("Управление тихим режимом", fontWeight = FontWeight.Bold)
                        Text("Статус: ${state.silentStatusText}")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAction("force_quiet") }) { Text("Тихий") }
                            Button(onClick = { onAction("force_loud") }) { Text("Громкий") }
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAction("auto_mode") }) { Text("Авто") }
                        }
                    }
                    Button(onClick = { isSettingsExpanded = !isSettingsExpanded }, modifier = Modifier.fillMaxWidth()) {
                        Text("⚙️ Настройки")
                    }
                    if (isSettingsExpanded) {
                        Text("Разделы настроек", fontWeight = FontWeight.Bold)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { settingsSection = "bff" }) { Text("BFF") }
                            Button(onClick = { settingsSection = "monitoring" }) { Text("Мониторинг") }
                            Button(onClick = { settingsSection = "bot" }) { Text("Бот") }
                        }
                        FlowRow(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(onClick = { settingsSection = "time" }) { Text("Время") }
                            Button(onClick = { settingsSection = "auth" }) { Text("Аутентификация") }
                            Button(onClick = { settingsSection = "servers" }) { Text("Серверы") }
                            Button(onClick = { settingsSection = "appearance" }) { Text("Тема") }
                            Button(onClick = { settingsSection = "extensions" }) { Text("Расширения") }
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onThemeModeChanged("light") }) { Text("☀️ Светлая") }
                            Button(onClick = { onThemeModeChanged("dark") }) { Text("🌙 Тёмная") }
                        }

                        if (settingsSection == "bff") {
                            Text("Подключение к BFF", fontWeight = FontWeight.Bold)
                        OutlinedTextField(
                            value = state.baseUrlInput,
                            onValueChange = onBaseUrlChanged,
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Base URL API") }
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = onSaveBaseUrl) { Text("Сохранить URL") }
                        }
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

                        if (settingsSection == "monitoring") {
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

                        if (settingsSection == "bot") {
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
                            label = { Text("telegram_chat_id (legacy)") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (state.telegramChatIds.isNotEmpty()) {
                            Text("Чаты Telegram (${state.telegramChatIds.size})", fontWeight = FontWeight.Bold)
                            state.telegramChatIds.forEach { chatId ->
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Text(chatId, modifier = Modifier.weight(1f))
                                    Button(onClick = { onRemoveTelegramChatId(chatId) }) { Text("Удалить") }
                                }
                            }
                        }
                        OutlinedTextField(
                            value = state.newTelegramChatIdInput,
                            onValueChange = onNewTelegramChatIdChanged,
                            label = { Text("Новый chat_id") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = onAddTelegramChatId) { Text("Добавить chat_id") }
                        }
                        Button(onClick = onSaveBot, enabled = canSaveBot) {
                            Text("Сохранить bot")
                        }
                        }

                        if (settingsSection == "time") {
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
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onMorningNotificationsEnabledChanged(true) }) { Text("Уведомления ВКЛ") }
                            Button(onClick = { onMorningNotificationsEnabledChanged(false) }) { Text("Уведомления ВЫКЛ") }
                        }
                        Text("Статус уведомлений: ${if (state.morningReportNotificationsEnabled) "включены" else "выключены"}")
                        Button(onClick = onSaveTime, enabled = canSaveTime) {
                            Text("Сохранить time")
                        }
                        }

                        if (settingsSection == "appearance") {
                            Text("Оформление", fontWeight = FontWeight.Bold)
                            Text("Текущая тема: ${if (state.themeMode == "light") "светлая" else "темная"}")
                            Button(
                                onClick = {
                                    onThemeModeChanged(if (state.themeMode == "light") "dark" else "light")
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(if (state.themeMode == "light") "Переключить на темную" else "Переключить на светлую")
                            }
                        }

                        if (settingsSection == "extensions") {
                            Text("🧩 Настройки расширений", fontWeight = FontWeight.Bold)
                            Text("Включай/выключай расширения и открывай настройки активных расширений.")

                            Text("🛠️ Управление расширениями (вкл/выкл)", fontWeight = FontWeight.Bold)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = onEnableAllExtensions) { Text("📊 Включить все") }
                                Button(onClick = onDisableAllExtensions) { Text("📋 Отключить все") }
                            }
                            ExtensionsSection(items = state.extensions, onToggleExtension = onToggleExtension)
                            Spacer(modifier = Modifier.height(8.dp))

                            Button(
                                onClick = {
                                    if (isExtensionsSettingsOpened) {
                                        isExtensionsSettingsOpened = false
                                    } else {
                                        isExtensionsSettingsOpened = true
                                        onOpenExtensionsSettingsMenu()
                                    }
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(if (isExtensionsSettingsOpened) "⚙️ Скрыть настройки расширений" else "⚙️ Открыть настройки расширений")
                            }
                            if (isExtensionsSettingsOpened && state.extensionSettingsMenuOptions.isEmpty()) {
                                Text("Нет доступных настроек для активных расширений.")
                            }
                            if (state.message.isNotBlank() && state.messageSource == "extensions_settings") {
                                Text(state.message)
                            }
                            if (isExtensionsSettingsOpened) {
                                val menuOptions = state.extensionSettingsMenuOptions
                                    .mapNotNull { item ->
                                        val optionLabel = item.label?.trim().orEmpty()
                                        val optionAction = item.action?.trim().orEmpty()
                                        val callbackAction = item.callbackData?.trim().orEmpty()
                                        val callbackActionCamel = item.callbackDataCamel?.trim().orEmpty()
                                        val targetAction = when {
                                            optionAction.isNotBlank() -> optionAction
                                            callbackAction.isNotBlank() -> callbackAction
                                            callbackActionCamel.isNotBlank() -> callbackActionCamel
                                            else -> ""
                                        }
                                        if (optionLabel.isNotBlank() && targetAction.isNotBlank()) {
                                            optionLabel to targetAction
                                        } else {
                                            null
                                        }
                                    }
                                    .distinctBy { (label, action) -> "${label.lowercase()}|$action" }

                                var index = 0
                                while (index < menuOptions.size) {
                                    val (label, action) = menuOptions[index]
                                    val hostNameForEdit = label.removePrefix("✏️ ").trim().takeIf { label.startsWith("✏️ ") && it.isNotBlank() }
                                    val next = menuOptions.getOrNull(index + 1)
                                    val isEditDeletePair = hostNameForEdit != null &&
                                        next != null &&
                                        next.first.startsWith("🗑️ ") &&
                                        next.first.removePrefix("🗑️ ").trim() == hostNameForEdit

                                    if (isEditDeletePair) {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                                        ) {
                                            Button(
                                                onClick = { onExtensionsSettingsAction(action) },
                                                modifier = Modifier.weight(1f)
                                            ) {
                                                Text(label)
                                            }
                                            Button(
                                                onClick = { onExtensionsSettingsAction(next!!.second) },
                                                modifier = Modifier.weight(1f)
                                            ) {
                                                Text(next.first)
                                            }
                                        }
                                        index += 2
                                        continue
                                    }

                                    Button(
                                        onClick = {
                                            if (action == "settings_extensions_close_local") {
                                                isExtensionsSettingsOpened = false
                                            } else {
                                                onExtensionsSettingsAction(action)
                                            }
                                        },
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Text(label)
                                    }
                                    index += 1
                                }
                            }
                        }

                        if (settingsSection == "auth") {
                        Text("🔐 Настройки аутентификации", fontWeight = FontWeight.Bold)
                            Text("SSH аутентификация:", fontWeight = FontWeight.Bold)
                            Text("• Пользователь: ${state.sshUsernameInput.ifBlank { "root" }}")
                            Text("• Путь к ключу: ${state.sshKeyPathInput.ifBlank { "/root/.ssh/id_rsa" }}")
                            Spacer(modifier = Modifier.height(4.dp))
                            Text("Windows аутентификация:", fontWeight = FontWeight.Bold)
                            Text("• Учетных записей: $windowsTotal")
                            Text("• Типов серверов: $windowsTypes")

                            Button(onClick = { isSshAuthExpanded = !isSshAuthExpanded }, modifier = Modifier.fillMaxWidth()) {
                                Text("👤 SSH аутентификация")
                            }
                            if (isSshAuthExpanded) {
                                OutlinedTextField(
                                    value = state.sshUsernameInput,
                                    onValueChange = onSshUsernameChanged,
                                    label = { Text("SSH пользователь") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                OutlinedTextField(
                                    value = state.sshKeyPathInput,
                                    onValueChange = onSshKeyPathChanged,
                                    label = { Text("Путь к SSH ключу") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Button(onClick = onSaveAuth, enabled = canSaveAuth) { Text("Сохранить SSH") }
                            }

                            Button(onClick = { isWindowsAuthExpanded = !isWindowsAuthExpanded }, modifier = Modifier.fillMaxWidth()) {
                                Text("🖥 Windows аутентификация")
                            }
                            if (isWindowsAuthExpanded) {
                                Button(onClick = { showWindowsAll = !showWindowsAll }, modifier = Modifier.fillMaxWidth()) {
                                    Text("👥 Просмотр всех учетных записей")
                                }
                                if (showWindowsAll) {
                                    state.windowsCredentials.forEach { cred ->
                                        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                            Column(modifier = Modifier.padding(10.dp)) {
                                                Text("🟢 ${cred.serverType ?: "default"} (приоритет: ${cred.priority ?: 0})")
                                                Text("Пользователь: ${cred.username ?: "-"}")
                                                Text("ID: ${cred.id ?: "-"}")
                                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                    Button(onClick = { onRemoveWindowsCredential(cred.id) }) { Text("Удалить") }
                                                }
                                            }
                                        }
                                    }
                                }

                                Text("➕ Добавить учетную запись", fontWeight = FontWeight.Bold)
                                OutlinedTextField(
                                    value = state.windowsCredUsernameInput,
                                    onValueChange = onWindowsCredUsernameChanged,
                                    label = { Text("Пользователь") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                OutlinedTextField(
                                    value = state.windowsCredPasswordInput,
                                    onValueChange = onWindowsCredPasswordChanged,
                                    label = { Text("Пароль") },
                                    modifier = Modifier.fillMaxWidth(),
                                    visualTransformation = if (state.isWindowsPasswordVisible) VisualTransformation.None else hiddenTransformation,
                                    trailingIcon = {
                                        TextButton(onClick = onToggleWindowsPasswordVisibility) {
                                            Text(if (state.isWindowsPasswordVisible) "Скрыть" else "Показать")
                                        }
                                    }
                                )
                                OutlinedTextField(
                                    value = state.windowsCredServerTypeInput,
                                    onValueChange = onWindowsCredServerTypeChanged,
                                    label = { Text("Тип серверов") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                OutlinedTextField(
                                    value = state.windowsCredPriorityInput,
                                    onValueChange = onWindowsCredPriorityChanged,
                                    label = { Text("Приоритет") },
                                    modifier = Modifier.fillMaxWidth()
                                )
                                Button(onClick = onAddWindowsCredential) { Text("Добавить учетную запись") }

                                Button(onClick = { showWindowsByType = !showWindowsByType }, modifier = Modifier.fillMaxWidth()) {
                                    Text("📊 Учетные данные по типам")
                                }
                                if (showWindowsByType) {
                                    windowsByType.forEach { (serverType, creds) ->
                                        Text("$serverType (${creds.size} учетных записей):", fontWeight = FontWeight.Bold)
                                        creds.take(3).forEach { cred ->
                                            Text("• ${cred.username ?: "-"} (приоритет: ${cred.priority ?: 0})")
                                        }
                                        if (creds.size > 3) {
                                            Text("... и еще ${creds.size - 3}")
                                        }
                                    }
                                }

                                Button(onClick = { showWindowsTypeStats = !showWindowsTypeStats }, modifier = Modifier.fillMaxWidth()) {
                                    Text("⚙️ Управление типами серверов")
                                }
                                if (showWindowsTypeStats) {
                                    Text("Существующие типы:", fontWeight = FontWeight.Bold)
                                    if (state.windowsTypes.isNotEmpty()) {
                                        state.windowsTypes.forEach { type ->
                                            Text("• ${type.name}: ${type.active}/${type.total} активных учетных записей")
                                        }
                                    } else {
                                        windowsByType.keys.sorted().forEach { type ->
                                            val total = windowsByType[type]?.size ?: 0
                                            Text("• $type: $total/$total активных учетных записей")
                                        }
                                    }

                                    Text("Создать новый тип", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.createWindowsTypeInput,
                                        onValueChange = onCreateWindowsTypeInputChanged,
                                        label = { Text("Имя нового типа") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onCreateWindowsType) { Text("Создать тип") }

                                    Text("Переименовать тип", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.renameOldTypeInput,
                                        onValueChange = onRenameOldTypeInputChanged,
                                        label = { Text("Старое имя типа") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    OutlinedTextField(
                                        value = state.renameNewTypeInput,
                                        onValueChange = onRenameNewTypeInputChanged,
                                        label = { Text("Новое имя типа") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onRenameWindowsType) { Text("Переименовать") }

                                    Text("Объединить типы", fontWeight = FontWeight.Bold)
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
                                    Button(onClick = onMergeWindowsTypes) { Text("Объединить") }

                                    Text("Удалить тип", fontWeight = FontWeight.Bold)
                                    OutlinedTextField(
                                        value = state.deleteTypeInput,
                                        onValueChange = onDeleteTypeInputChanged,
                                        label = { Text("Удаляемый тип") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    OutlinedTextField(
                                        value = state.deleteTargetTypeInput,
                                        onValueChange = onDeleteTargetTypeInputChanged,
                                        label = { Text("Перенести в тип (target)") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Button(onClick = onDeleteWindowsType) { Text("Удалить тип") }
                                }
                            }
                        }

                        if (settingsSection == "servers") {
                            Text("🖥️ Серверы", fontWeight = FontWeight.Bold)
                            Text("Всего: ${state.managedServers.size}")
                            Text("Активных: ${state.managedServers.count { it.enabled == true }}")

                            Text(
                                if (state.serverEditIp.isBlank()) "Добавить сервер" else "Редактирование сервера ${state.serverEditIp}",
                                fontWeight = FontWeight.Bold
                            )
                            OutlinedTextField(
                                value = state.serverIpInput,
                                onValueChange = onServerIpChanged,
                                label = { Text("IP сервера") },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = state.serverEditIp.isBlank()
                            )
                            OutlinedTextField(
                                value = state.serverNameInput,
                                onValueChange = onServerNameChanged,
                                label = { Text("Имя сервера") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            OutlinedTextField(
                                value = state.serverTypeInput,
                                onValueChange = onServerTypeChanged,
                                label = { Text("Тип (rdp/ssh/ping)") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            OutlinedTextField(
                                value = state.serverTimeoutInput,
                                onValueChange = onServerTimeoutChanged,
                                label = { Text("Timeout (сек)") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = onSaveServer) {
                                    Text(if (state.serverEditIp.isBlank()) "Добавить сервер" else "Сохранить изменения")
                                }
                                if (state.serverEditIp.isNotBlank()) {
                                    Button(onClick = onCancelServerEdit) { Text("Отмена") }
                                }
                            }

                            state.managedServers.forEach { server ->
                                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                    Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Text("${server.name} (${server.ip})", fontWeight = FontWeight.Bold)
                                        Text("Тип: ${server.type}, timeout: ${server.timeout ?: 30} сек")
                                        Text("Мониторинг: ${if (server.enabled == true) "включен" else "выключен"}")
                                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Button(onClick = { onToggleServerMonitoring(server.ip, server.enabled != true) }) {
                                                Text(if (server.enabled == true) "Выключить" else "Включить")
                                            }
                                            Button(onClick = { onEditServer(server) }) { Text("Редактировать") }
                                            Button(onClick = { onDeleteServer(server.ip) }) { Text("Удалить") }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Button(onClick = onCloseApp, modifier = Modifier.fillMaxWidth()) {
                        Text("❎ Закрыть")
                    }
                }
            }

        }
    }
}


@Composable
private fun ExtensionsSection(
    items: List<ExtensionItem>,
    onToggleExtension: (String, Boolean) -> Unit
) {
    if (items.isEmpty()) {
        Text("Список расширений пуст")
        return
    }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items.forEach { item ->
            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(item.name, fontWeight = FontWeight.Bold)
                    if (item.description.isNotBlank()) {
                        Text(item.description)
                    }
                    Text("Статус: ${if (item.enabled) "Включено" else "Отключено"}")
                    Button(onClick = { onToggleExtension(item.id, !item.enabled) }) {
                        Text(if (item.enabled) "🔴 Выключить" else "🟢 Включить")
                    }
                }
            }
        }
    }
}
