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
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedTextField
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material.ExperimentalMaterialApi
import androidx.compose.material.pullrefresh.PullRefreshIndicator
import androidx.compose.material.pullrefresh.pullRefresh
import androidx.compose.material.pullrefresh.rememberPullRefreshState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.PowerSettingsNew
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Settings
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.input.nestedscroll.nestedScroll
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

private val PROBLEM_BACKUP_MARKERS = listOf("❌", "⚠️", "🚨", "🆘", "⛔", "🔴", "🟠", "⚪")
private val PROBLEM_BACKUP_KEYWORDS = listOf("failed", "error", "problem", "down", "ошиб", "проблем", "недоступ", "не найден", "no backup")

private fun isProblemBackupLabel(label: String): Boolean {
    val normalized = label.lowercase()
    return PROBLEM_BACKUP_MARKERS.any { marker -> label.contains(marker) } ||
        PROBLEM_BACKUP_KEYWORDS.any { keyword -> normalized.contains(keyword) }
}

private fun isProblemBackupOption(label: String, action: String): Boolean {
    val normalizedAction = action.lowercase()
    return isProblemBackupLabel(label) || PROBLEM_BACKUP_KEYWORDS.any { keyword ->
        normalizedAction.contains(keyword)
    }
}

private fun resolveMenuOptionAction(option: ru.monitoring.mobile.api.MenuOption): String {
    val optionAction = option.action?.trim().orEmpty()
    val callbackAction = option.callbackData?.trim().orEmpty()
    val callbackActionCamel = option.callbackDataCamel?.trim().orEmpty()
    return when {
        optionAction.isNotBlank() -> optionAction
        callbackAction.isNotBlank() -> callbackAction
        callbackActionCamel.isNotBlank() -> callbackActionCamel
        else -> ""
    }
}

private data class OpsMetricTile(
    val id: String,
    val label: String,
    val value: String,
    val hasProblem: Boolean = false,
    val onClick: () -> Unit = {},
    val onLongClick: (() -> Unit)? = null
)

private data class ExtensionDataTile(
    val id: String,
    val label: String,
    val value: String,
    val hasProblem: Boolean
)

private enum class ServerCardsSortMode {
    BY_NAME,
    BY_IP
}

private val extensionRatioRegex = Regex("""(\d+)\s*/\s*(\d+)""")

private fun buildExtensionDataTile(
    extension: ExtensionItem,
    summaryOverride: String? = null,
    hasProblemOverride: Boolean? = null
): ExtensionDataTile {
    val description = extension.description.trim()
    val ratioMatch = extensionRatioRegex.find(description)
    val ratioValue = ratioMatch?.value?.replace(" ", "")
    val defaultHasProblem = when {
        ratioMatch != null -> {
            val done = ratioMatch.groupValues[1].toIntOrNull() ?: 0
            val total = ratioMatch.groupValues[2].toIntOrNull() ?: 0
            total <= 0 || done < total
        }
        description.isBlank() -> false
        else -> isProblemBackupLabel(description)
    }
    return ExtensionDataTile(
        id = extension.id,
        label = extension.name,
        value = summaryOverride?.takeIf { it.isNotBlank() } ?: ratioValue ?: "—",
        hasProblem = hasProblemOverride ?: defaultHasProblem
    )
}

private fun buildToggleDataTile(label: String, enabled: Boolean): ExtensionDataTile {
    return ExtensionDataTile(
        id = label.lowercase(),
        label = label,
        value = if (enabled) "вкл" else "выкл",
        hasProblem = false
    )
}

private fun extractMailBackupVolumeFromMorningReport(report: String): String? {
    if (report.isBlank()) return null
    val normalizedReport = report
        .replace("\\_", "_")
        .replace("\\-", "-")
        .replace("*", "")
    val lines = normalizedReport.lines().map { it.trim() }.filter { it.isNotBlank() }

    val mailLineIndex = lines.indexOfFirst { current ->
        current.contains("почт", ignoreCase = true) || current.contains("mail", ignoreCase = true)
    }
    val nearMailSection = if (mailLineIndex >= 0) {
        lines.subList(
            fromIndex = mailLineIndex,
            toIndex = (mailLineIndex + 4).coerceAtMost(lines.size)
        ).joinToString("\n")
    } else {
        ""
    }

    val regexes = listOf(
        Regex("""([0-9]+(?:[.,][0-9]+)?\s*(?:B|KB|MB|GB|TB|KiB|MiB|GiB|TiB|байт(?:а|ов)?))""", RegexOption.IGNORE_CASE),
        Regex("""об(?:ъ|ь)ем\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?\s*\S+)""", RegexOption.IGNORE_CASE),
        Regex("""size\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?\s*\S+)""", RegexOption.IGNORE_CASE)
    )

    val extractFrom: (String) -> String? = { text ->
        regexes.firstNotNullOfOrNull { regex ->
            regex.find(text)?.groupValues?.getOrNull(1)?.trim()?.trimEnd('.', ',', ';')
        }
    }
    return extractFrom(nearMailSection) ?: extractFrom(normalizedReport)
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun OpsMetricChip(
    label: String,
    value: String,
    hasProblem: Boolean = false,
    onClick: () -> Unit = {},
    onLongClick: (() -> Unit)? = null
) {
    val valueColor = if (hasProblem) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface
    Surface(
        modifier = Modifier
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.7f))
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            ),
        shape = RoundedCornerShape(14.dp),
        tonalElevation = 1.dp
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp)
        ) {
            Text(value, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = valueColor)
            Text(label, style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
private fun DashboardActionButton(label: String, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer
        )
    ) {
        Text(label, fontWeight = FontWeight.Medium)
    }
}

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
                    preferences = preferences,
                    onTokenChanged = vm::setTokenInput,
                    onBaseUrlChanged = vm::setBaseUrlInput,
                    onSaveToken = vm::saveToken,
                    onSaveBaseUrl = vm::saveBaseUrl,
                    onRefreshData = vm::refreshData,
                    onLoadServersForSingleCheck = { vm.refreshSettingsFromServer(showErrors = true) },
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

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class, ExperimentalMaterialApi::class, ExperimentalFoundationApi::class)
@Composable
private fun MonitoringApp(
    state: MainUiState,
    preferences: AppPreferences,
    onTokenChanged: (String) -> Unit,
    onBaseUrlChanged: (String) -> Unit,
    onSaveToken: (String) -> Unit,
    onSaveBaseUrl: () -> Unit,
    onRefreshData: () -> Unit,
    onLoadServersForSingleCheck: () -> Unit,
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
    val isCompactOpsHub = BuildConfig.IS_COMPACT_OPS_HUB

    var isManagementExpanded by rememberSaveable { mutableStateOf(false) }
    var isSettingsExpanded by rememberSaveable { mutableStateOf(false) }
    var isExtensionsSettingsOpened by rememberSaveable { mutableStateOf(false) }
    var isSshAuthExpanded by rememberSaveable { mutableStateOf(false) }
    var isWindowsAuthExpanded by rememberSaveable { mutableStateOf(false) }
    var showWindowsAll by rememberSaveable { mutableStateOf(false) }
    var showWindowsByType by rememberSaveable { mutableStateOf(false) }
    var showWindowsTypeStats by rememberSaveable { mutableStateOf(false) }
    var showServerAvailabilityDialog by rememberSaveable { mutableStateOf(false) }
    var showServerAddDialog by rememberSaveable { mutableStateOf(false) }
    var serverActionsTargetKey by rememberSaveable { mutableStateOf("") }
    var serverCardsSortMode by rememberSaveable { mutableStateOf(ServerCardsSortMode.BY_NAME.name) }
    var showServerResourcesMenu by rememberSaveable { mutableStateOf(false) }
    var areOpsTilesExpanded by rememberSaveable { mutableStateOf(false) }
    var showTileSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var settingsSection by rememberSaveable { mutableStateOf("bff") }
    var showProxmoxPatternAddDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxPatternEditDialog by rememberSaveable { mutableStateOf(false) }
    var proxmoxPatternCategoryInput by rememberSaveable { mutableStateOf("proxmox") }
    var proxmoxPatternTypeInput by rememberSaveable { mutableStateOf("subject") }
    var proxmoxPatternValueInput by rememberSaveable { mutableStateOf("") }
    var proxmoxPatternEditAction by rememberSaveable { mutableStateOf("") }
    var proxmoxPatternEditValueInput by rememberSaveable { mutableStateOf("") }
    var showMailPatternAddDialog by rememberSaveable { mutableStateOf(false) }
    var showMailPatternEditDialog by rememberSaveable { mutableStateOf(false) }
    var mailPatternInputMode by rememberSaveable { mutableStateOf("subject") }
    var mailPatternInputValue by rememberSaveable { mutableStateOf("") }
    var mailPatternEditAction by rememberSaveable { mutableStateOf("") }
    var mailPatternEditValueInput by rememberSaveable { mutableStateOf("") }
    var showDbCategoryAddDialog by rememberSaveable { mutableStateOf(false) }
    var dbCategoryInput by rememberSaveable { mutableStateOf("") }
    var showDbEntryAddDialog by rememberSaveable { mutableStateOf(false) }
    var dbEntryAddCategory by rememberSaveable { mutableStateOf("") }
    var dbEntryAddKeyInput by rememberSaveable { mutableStateOf("") }
    var dbEntryAddNameInput by rememberSaveable { mutableStateOf("") }
    var showDbEntryEditDialog by rememberSaveable { mutableStateOf(false) }
    var dbEntryEditCategory by rememberSaveable { mutableStateOf("") }
    var dbEntryEditOriginalKey by rememberSaveable { mutableStateOf("") }
    var dbEntryEditNewKeyInput by rememberSaveable { mutableStateOf("") }
    var dbEntryEditNameInput by rememberSaveable { mutableStateOf("") }
    var showZfsHostAddDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsHostEditDialog by rememberSaveable { mutableStateOf(false) }
    var zfsHostInput by rememberSaveable { mutableStateOf("") }
    var zfsHostEditAction by rememberSaveable { mutableStateOf("") }
    var zfsHostEditCurrentName by rememberSaveable { mutableStateOf("") }
    var zfsHostEditNewNameInput by rememberSaveable { mutableStateOf("") }
    var showResourceThresholdDialog by rememberSaveable { mutableStateOf(false) }
    var resourceThresholdAction by rememberSaveable { mutableStateOf("") }
    var resourceThresholdLabel by rememberSaveable { mutableStateOf("") }
    var resourceThresholdValueInput by rememberSaveable { mutableStateOf("") }
    var selectedProxmoxBackupLabel by rememberSaveable { mutableStateOf("") }
    var showProxmoxBackupStatsDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxBackupsDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxBackupAddDialog by rememberSaveable { mutableStateOf(false) }

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
    val windowsTypes = windowsByType.size
    val enabledExtensions = state.extensions.filter { it.enabled }.map { it.id }.toSet()
    val enabledExtensionsCount = state.extensions.count { it.enabled }
    val totalExtensionsCount = state.extensions.size
    val upServersCount = state.servers.count { it.status.equals("UP", ignoreCase = true) }
    val totalServersCount = state.managedServers.size.takeIf { it > 0 } ?: state.servers.size
    val activeServersCount = upServersCount.coerceAtMost(totalServersCount)
    val downServersCount = state.servers.count { it.status.equals("DOWN", ignoreCase = true) }
    val unknownServersCount = state.servers.count { it.status.equals("UNKNOWN", ignoreCase = true) }
    val latestMailBackup = state.mailBackupHistoryItems.firstOrNull()
    val hasMailProblemByLatest = latestMailBackup?.statusIcon?.let { icon ->
        icon.contains("❌") || icon.contains("⚠️") || icon.contains("🚨")
    } ?: state.backupMailHasProblemItems
    val extensionProblemsCount = listOf(
        state.backupProxmoxHasProblemItems,
        state.backupDatabasesHasProblemItems,
        state.backupStockLoadsHasProblemItems,
        state.supplierStockHasProblemItems,
        hasMailProblemByLatest
    ).count { it }
    val hasServerProblems = downServersCount > 0 || unknownServersCount > 0 || activeServersCount < totalServersCount
    val hasExtensionProblems = extensionProblemsCount > 0
    val extensionButtons = MAIN_MENU_EXTENSION_BUTTONS.filter { it.extensionId in enabledExtensions }
    val isResourceMonitorEnabled = "resource_monitor" in enabledExtensions
    val appTitle = "Sysmoraq"
    val contentPadding = if (isCompactOpsHub) 10.dp else 16.dp
    val sectionSpacing = if (isCompactOpsHub) 8.dp else 12.dp

    val openServersDetails = {
        onRefresh()
        showServerAvailabilityDialog = false
    }
    val openServerSingleCheckDetails = {
        onLoadServersForSingleCheck()
        showServerAvailabilityDialog = true
    }
    val openProxmoxBackupDetails = {
        onAction("backup_proxmox")
        showProxmoxBackupsDialog = true
    }
    val openExtensionsDetails = {
        isSettingsExpanded = true
        settingsSection = "extensions"
        isExtensionsSettingsOpened = true
    }
    val openModesDetails = {
        val nextModeAction = when {
            state.silentStatusText.contains("Принудительно тих", ignoreCase = true) -> "force_loud"
            state.silentStatusText.contains("Принудительно громк", ignoreCase = true) -> "auto_mode"
            else -> "force_quiet"
        }
        onAction(nextModeAction)
    }
    val opsTiles = listOf(
        OpsMetricTile(
            id = "servers",
            label = "Серверы",
            value = "$activeServersCount/$totalServersCount",
            hasProblem = hasServerProblems,
            onClick = openServersDetails,
            onLongClick = openServerSingleCheckDetails
        ),
        OpsMetricTile(
            id = "extensions",
            label = "Расширения",
            value = "$enabledExtensionsCount/$totalExtensionsCount",
            hasProblem = hasExtensionProblems,
            onClick = openExtensionsDetails
        ),
        OpsMetricTile(
            id = "modes",
            label = "Режим",
            value = state.silentStatusText,
            onClick = openModesDetails
        )
    )
    val extensionsById = state.extensions.associateBy { it.id }
    val extensionInfoTiles = buildList {
        extensionsById["backup_monitor"]?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "proxmox"),
                    summaryOverride = state.backupProxmoxSummary,
                    hasProblemOverride = state.backupProxmoxHasProblemItems
                )
            )
        }
        extensionsById["database_backup_monitor"]?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "БД"),
                    summaryOverride = state.backupDatabasesSummary,
                    hasProblemOverride = state.backupDatabasesHasProblemItems
                )
            )
        }
        extensionsById["mail_backup_monitor"]?.let { extension ->
            val latestIsOk = latestMailBackup?.statusIcon?.let { icon ->
                icon.contains("✅") || icon.contains("✔")
            }
            val latestSize = latestMailBackup?.size?.takeIf { it.isNotBlank() }
            val serverMailVolume = state.mailBackupLastVolume.takeIf { it.isNotBlank() }
            val morningMailVolume = extractMailBackupVolumeFromMorningReport(state.morningReportText)
            val summary = latestSize ?: serverMailVolume ?: morningMailVolume ?: "нет данных"
            val hasProblem = when {
                latestSize.isNullOrBlank() -> false
                latestIsOk == false -> true
                else -> false
            }
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "почта"),
                    summaryOverride = summary,
                    hasProblemOverride = hasProblem
                )
            )
        }
        extensionsById["stock_load_monitor"]?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "остатки"),
                    summaryOverride = state.backupStockLoadsSummary,
                    hasProblemOverride = state.backupStockLoadsHasProblemItems
                )
            )
        }
        extensionsById["zfs_monitor"]?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "ZFS"),
                    summaryOverride = state.zfsSummary.ifBlank { if (extension.enabled) "ОК" else "выкл" },
                    hasProblemOverride = state.zfsHasProblemItems
                )
            )
        }
        extensionsById["supplier_stock_files"]?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "поставщики"),
                    summaryOverride = state.supplierStockSummary,
                    hasProblemOverride = state.supplierStockHasProblemItems
                )
            )
        }
        extensionsById["resource_monitor"]?.let { extension ->
            val hasProblem = isProblemBackupLabel(extension.description)
            add(
                ExtensionDataTile(
                    id = extension.id,
                    label = "ресурсы",
                    value = if (hasProblem) "!" else "ОК",
                    hasProblem = hasProblem
                )
            )
        }
        extensionsById["web_interface"]?.let { extension ->
            add(buildToggleDataTile(label = "web", enabled = extension.enabled))
        }
        extensionsById["email_processor"]?.let { extension ->
            add(buildToggleDataTile(label = "mail", enabled = extension.enabled))
        }
    }
    val extensionOpsTiles = extensionInfoTiles.map { extension ->
        OpsMetricTile(
            id = "extension_${extension.id}",
            label = extension.label,
            value = extension.value,
            hasProblem = extension.hasProblem,
            onClick = if (extension.id == "backup_monitor") {
                {
                    selectedProxmoxBackupLabel = ""
                    showProxmoxBackupStatsDialog = false
                    openProxmoxBackupDetails()
                }
            } else {
                openExtensionsDetails
            }
        )
    }
    val allOpsTiles = opsTiles + extensionOpsTiles
    val defaultPinnedTileIds = setOf("servers", "extensions", "modes")
    var pinnedOpsTileIds by rememberSaveable {
        mutableStateOf(
            preferences.compactOpsPinnedTileIds.split(",")
                .map { it.trim() }
                .filter { it.isNotBlank() }
                .toSet()
                .ifEmpty { defaultPinnedTileIds }
        )
    }
    val orderedPinnedTileIds = allOpsTiles.map { it.id }.filter { it in pinnedOpsTileIds }.toSet()
    val effectivePinnedTileIds = if (orderedPinnedTileIds.isEmpty()) defaultPinnedTileIds else orderedPinnedTileIds
    val pinnedTiles = allOpsTiles.filter { it.id in effectivePinnedTileIds }
    val hiddenTiles = allOpsTiles.filterNot { it.id in effectivePinnedTileIds }
    val visibleTiles = if (areOpsTilesExpanded) pinnedTiles + hiddenTiles else pinnedTiles
    val isSynchronized = state.isDataSynchronized
    val synchronizationTimeSuffix = state.lastSyncTime
        .takeIf { it.isNotBlank() }
        ?.let { " • $it" }
        .orEmpty()
    val synchronizationText = if (isSynchronized) {
        "синхронизировано$synchronizationTimeSuffix"
    } else {
        "не синхронизировано"
    }
    val synchronizationColor = if (isSynchronized) Color(0xFF2E7D32) else Color(0xFFC62828)
    val pullToRefreshState = rememberPullRefreshState(state.isLoading, onRefreshData)
    val serverButtonsForDialog = state.managedServers
        .asSequence()
        .sortedWith(
            when (ServerCardsSortMode.valueOf(serverCardsSortMode)) {
                ServerCardsSortMode.BY_NAME -> compareBy<ManagedServer> { it.name.lowercase() }
                    .thenBy { it.ip.lowercase() }
                ServerCardsSortMode.BY_IP -> compareBy<ManagedServer> { it.ip.lowercase() }
                    .thenBy { it.name.lowercase() }
            }
        )
        .toList()
    val selectedServerForActions = state.managedServers.firstOrNull { managedServer ->
        val key = managedServer.ip.ifBlank { managedServer.name }.trim()
        key == serverActionsTargetKey
    }


    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text(appTitle, fontWeight = FontWeight.SemiBold)
                }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .pullRefresh(pullToRefreshState)
        ) {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(contentPadding),
                verticalArrangement = Arrangement.spacedBy(sectionSpacing)
            ) {
            if (isCompactOpsHub) {
                item {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(20.dp))
                            .background(
                                brush = Brush.verticalGradient(
                                    listOf(
                                        MaterialTheme.colorScheme.primaryContainer,
                                        MaterialTheme.colorScheme.surfaceContainerHigh
                                    )
                                )
                            )
                            .padding(14.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(
                                modifier = Modifier.clickable {
                                    onRefreshData()
                                    showServerAvailabilityDialog = false
                                    showServerResourcesMenu = false
                                },
                                verticalArrangement = Arrangement.spacedBy(2.dp)
                            ) {
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text("⚡ Оперативный центр", fontWeight = FontWeight.Bold, fontSize = 20.sp)
                                    Text(
                                        state.projectVersion,
                                        style = MaterialTheme.typography.labelMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                Text(
                                    synchronizationText,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = synchronizationColor
                                )
                                if (state.isSyncInProgress) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    LinearProgressIndicator(
                                        progress = { state.syncProgress.coerceIn(0f, 1f) },
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .height(4.dp)
                                            .clip(RoundedCornerShape(10.dp))
                                    )
                                    Text(
                                        "идёт синхронизация… ${(state.syncProgress * 100).toInt()}%",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                if (state.isServerBatchCheckInProgress) {
                                    Spacer(modifier = Modifier.height(6.dp))
                                    LinearProgressIndicator(
                                        progress = { state.serverBatchCheckProgress.coerceIn(0f, 1f) },
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .height(4.dp)
                                            .clip(RoundedCornerShape(10.dp))
                                    )
                                    Text(
                                        "проверяется: ${state.serverBatchCheckCurrentServer.ifBlank { "подготовка" }}",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                            IconButton(onClick = { showTileSettingsDialog = true }) {
                                Icon(
                                    imageVector = Icons.Filled.Settings,
                                    contentDescription = "Настроить плашки"
                                )
                            }
                        }
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            maxItemsInEachRow = 3
                        ) {
                            visibleTiles.forEach { tile ->
                                OpsMetricChip(
                                    label = tile.label,
                                    value = tile.value,
                                    hasProblem = tile.hasProblem,
                                    onClick = tile.onClick,
                                    onLongClick = tile.onLongClick
                                )
                            }
                        }
                        if (hiddenTiles.isNotEmpty()) {
                            Button(
                                onClick = { areOpsTilesExpanded = !areOpsTilesExpanded },
                                modifier = Modifier.fillMaxWidth(),
                                shape = RoundedCornerShape(14.dp),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = MaterialTheme.colorScheme.surfaceContainerHighest,
                                    contentColor = MaterialTheme.colorScheme.onSurface
                                )
                            ) {
                                Text(if (areOpsTilesExpanded) "Свернуть" else "Развернуть")
                            }
                        }
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            maxItemsInEachRow = 2
                        ) {
                            DashboardActionButton(
                                label = "🌅 Утренний отчёт",
                                onClick = { onAction("send_morning_report") }
                            )
                            DashboardActionButton(
                                label = "⚙️ Настройки",
                                onClick = { isSettingsExpanded = true }
                            )
                        }
                        if (state.extensionMenuAction == "backup_proxmox" && state.extensionMenuOptions.isNotEmpty()) {
                            Text("💾 Бэкапы Proxmox", fontWeight = FontWeight.Bold)
                            FlowRow(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                                maxItemsInEachRow = 3
                            ) {
                                state.extensionMenuOptions.forEach { option ->
                                    val label = option.label?.trim().orEmpty()
                                    val targetAction = resolveMenuOptionAction(option)
                                    if (label.isNotBlank() && targetAction.isNotBlank()) {
                                        OpsMetricChip(
                                            label = "бэкап",
                                            value = label,
                                            hasProblem = isProblemBackupOption(label, targetAction),
                                            onClick = {
                                                selectedProxmoxBackupLabel = label
                                                showProxmoxBackupStatsDialog = true
                                                onAction(targetAction)
                                            }
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }

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

            if (!isCompactOpsHub) {
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
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (state.message.isNotBlank() && state.messageSource == "morning_report") {
                        Text(state.message)
                    }
                    Text("Расширения", fontWeight = FontWeight.Bold)
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        maxItemsInEachRow = 2
                    ) {
                        extensionButtons.forEach { extensionButton ->
                            val shouldHighlightBackupButton = when (extensionButton.action) {
                                "backup_proxmox" -> state.backupProxmoxHasProblemItems
                                "backup_databases" -> state.backupDatabasesHasProblemItems
                                else -> false
                            }
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
                                modifier = Modifier.weight(1f),
                                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 8.dp),
                                colors = if (shouldHighlightBackupButton) {
                                    ButtonDefaults.buttonColors(
                                        containerColor = MaterialTheme.colorScheme.errorContainer,
                                        contentColor = MaterialTheme.colorScheme.onErrorContainer
                                    )
                                } else {
                                    ButtonDefaults.buttonColors()
                                }
                            ) {
                                Text(
                                    text = extensionButton.label,
                                    fontSize = 13.sp,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis
                                )
                            }
                        }
                    }
                    extensionButtons.forEach { extensionButton ->
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
                            val shouldHighlightProblemBackups = extensionButton.action == "backup_proxmox" ||
                                extensionButton.action == "backup_databases"
                            val problemOptionsCount = state.extensionMenuOptions.count { item ->
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
                                shouldHighlightProblemBackups &&
                                    isProblemBackupOption(optionLabel, targetAction)
                            }
                            if (extensionButton.action == "backup_databases" && problemOptionsCount > 0) {
                                Text(
                                    text = "⚠️ Проблемных бэкапов: $problemOptionsCount",
                                    color = MaterialTheme.colorScheme.error,
                                    fontWeight = FontWeight.Medium
                                )
                            }
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
                                val isProblemBackupOption = shouldHighlightProblemBackups &&
                                    isProblemBackupOption(optionLabel, targetAction)
                                val containerColor = if (isProblemBackupOption) {
                                    MaterialTheme.colorScheme.errorContainer
                                } else {
                                    MaterialTheme.colorScheme.tertiaryContainer
                                }
                                val contentColor = if (isProblemBackupOption) {
                                    MaterialTheme.colorScheme.onErrorContainer
                                } else {
                                    MaterialTheme.colorScheme.onTertiaryContainer
                                }
                                val displayLabel = if (isProblemBackupOption && !optionLabel.contains("🚨")) {
                                    "🚨 $optionLabel"
                                } else {
                                    optionLabel
                                }
                                if (optionLabel.isNotBlank() && targetAction.isNotBlank()) {
                                    Button(
                                        onClick = { onAction(targetAction) },
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = containerColor,
                                            contentColor = contentColor
                                        )
                                    ) {
                                        Text(displayLabel)
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
                    if (!isCompactOpsHub) {
                        Text("Раздел системы", fontWeight = FontWeight.Bold)
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            maxItemsInEachRow = 2
                        ) {
                            Button(
                                onClick = { isManagementExpanded = !isManagementExpanded },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("🎛️ Управление")
                            }
                            Button(
                                onClick = { isSettingsExpanded = !isSettingsExpanded },
                                modifier = Modifier.weight(1f)
                            ) {
                                Text("⚙️ Настройки")
                            }
                        }
                    }
                    if (!isCompactOpsHub && isManagementExpanded) {
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
                                            when {
                                                action == "settings_extensions_close_local" -> {
                                                    isExtensionsSettingsOpened = false
                                                }
                                                action in setOf(
                                                    "set_cpu_warning",
                                                    "set_cpu_critical",
                                                    "set_ram_warning",
                                                    "set_ram_critical",
                                                    "set_disk_warning",
                                                    "set_disk_critical"
                                                ) -> {
                                                    resourceThresholdAction = action
                                                    resourceThresholdLabel = label
                                                    resourceThresholdValueInput = ""
                                                    showResourceThresholdDialog = true
                                                }
                                                action.startsWith("settings_proxmox_pattern_add") -> {
                                                    val parts = action.split("|")
                                                    proxmoxPatternCategoryInput = parts.getOrNull(1)
                                                        ?.takeIf { it.isNotBlank() }
                                                        ?: "proxmox"
                                                    proxmoxPatternTypeInput = parts.getOrNull(2)
                                                        ?.takeIf { it.isNotBlank() }
                                                        ?: "subject"
                                                    proxmoxPatternValueInput = parts.getOrNull(3).orEmpty()
                                                    showProxmoxPatternAddDialog = true
                                                }
                                                action.startsWith("settings_proxmox_pattern_edit_") -> {
                                                    proxmoxPatternEditAction = action
                                                    proxmoxPatternEditValueInput = ""
                                                    showProxmoxPatternEditDialog = true
                                                }
                                                action.startsWith("settings_mail_pattern_add") -> {
                                                    val parts = action.split("|")
                                                    mailPatternInputMode = parts.getOrNull(1)
                                                        ?.takeIf { it == "subject" || it == "fragments" }
                                                        ?: "subject"
                                                    mailPatternInputValue = parts.getOrNull(2).orEmpty()
                                                    showMailPatternAddDialog = true
                                                }
                                                action.startsWith("settings_mail_pattern_edit_") -> {
                                                    mailPatternEditAction = action
                                                    mailPatternEditValueInput = ""
                                                    showMailPatternEditDialog = true
                                                }
                                                action == "settings_zfs_add" -> {
                                                    zfsHostInput = ""
                                                    showZfsHostAddDialog = true
                                                }
                                                action.startsWith("settings_zfs_edit_name_") -> {
                                                    val raw = action.removePrefix("settings_zfs_edit_name_")
                                                    zfsHostEditAction = "settings_zfs_edit_name_$raw"
                                                    zfsHostEditCurrentName = Uri.decode(raw)
                                                    zfsHostEditNewNameInput = zfsHostEditCurrentName
                                                    showZfsHostEditDialog = zfsHostEditCurrentName.isNotBlank()
                                                }
                                                action == "settings_db_add_category" -> {
                                                    dbCategoryInput = ""
                                                    showDbCategoryAddDialog = true
                                                }
                                                action.startsWith("settings_db_add_db_") -> {
                                                    dbEntryAddCategory = action.removePrefix("settings_db_add_db_")
                                                    dbEntryAddKeyInput = ""
                                                    dbEntryAddNameInput = ""
                                                    showDbEntryAddDialog = true
                                                }
                                                action.startsWith("settings_db_edit_db_") -> {
                                                    val raw = action.removePrefix("settings_db_edit_db_")
                                                    val parts = raw.split("__", limit = 2)
                                                    dbEntryEditCategory = parts.getOrNull(0).orEmpty()
                                                    dbEntryEditOriginalKey = parts.getOrNull(1).orEmpty()
                                                    dbEntryEditNewKeyInput = dbEntryEditOriginalKey
                                                    dbEntryEditNameInput = dbEntryEditOriginalKey
                                                    showDbEntryEditDialog = dbEntryEditCategory.isNotBlank() && dbEntryEditOriginalKey.isNotBlank()
                                                }
                                                else -> {
                                                    onExtensionsSettingsAction(action)
                                                }
                                            }
                                        },
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Text(label)
                                    }
                                    index += 1
                                }
                            }

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

                            Text("🛠️ Управление расширениями (вкл/выкл)", fontWeight = FontWeight.Bold)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = onEnableAllExtensions) { Text("📊 Включить все") }
                                Button(onClick = onDisableAllExtensions) { Text("📋 Отключить все") }
                            }
                            ExtensionsSection(items = state.extensions, onToggleExtension = onToggleExtension)
                            Spacer(modifier = Modifier.height(8.dp))

                            if (showProxmoxPatternAddDialog) {
                                AlertDialog(
                                    onDismissRequest = { showProxmoxPatternAddDialog = false },
                                    title = { Text("➕ Добавить паттерн Proxmox") },
                                    text = {
                                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            OutlinedTextField(
                                                value = proxmoxPatternCategoryInput,
                                                onValueChange = { proxmoxPatternCategoryInput = it },
                                                label = { Text("Категория (proxmox/database)") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                            OutlinedTextField(
                                                value = proxmoxPatternTypeInput,
                                                onValueChange = { proxmoxPatternTypeInput = it },
                                                label = { Text("Тип (например subject)") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                            OutlinedTextField(
                                                value = proxmoxPatternValueInput,
                                                onValueChange = { proxmoxPatternValueInput = it },
                                                label = { Text("Паттерн") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = "settings_proxmox_pattern_add|" +
                                                    Uri.encode(proxmoxPatternCategoryInput.trim()) + "|" +
                                                    Uri.encode(proxmoxPatternTypeInput.trim()) + "|" +
                                                    Uri.encode(proxmoxPatternValueInput.trim())
                                                onExtensionsSettingsAction(actionPayload)
                                                showProxmoxPatternAddDialog = false
                                            },
                                            enabled = proxmoxPatternCategoryInput.isNotBlank() &&
                                                proxmoxPatternTypeInput.isNotBlank() &&
                                                proxmoxPatternValueInput.isNotBlank()
                                        ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showProxmoxPatternAddDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showResourceThresholdDialog) {
                                AlertDialog(
                                    onDismissRequest = { showResourceThresholdDialog = false },
                                    title = { Text(resourceThresholdLabel.ifBlank { "Изменить порог ресурса" }) },
                                    text = {
                                        OutlinedTextField(
                                            value = resourceThresholdValueInput,
                                            onValueChange = { input ->
                                                resourceThresholdValueInput = input.filter { it.isDigit() }.take(3)
                                            },
                                            label = { Text("Порог в % (0-100)") },
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                    },
                                    confirmButton = {
                                        val thresholdValue = resourceThresholdValueInput.toIntOrNull()
                                        TextButton(
                                            onClick = {
                                                val actionPayload = "${resourceThresholdAction}|$thresholdValue"
                                                onExtensionsSettingsAction(actionPayload)
                                                showResourceThresholdDialog = false
                                            },
                                            enabled = resourceThresholdAction.isNotBlank() &&
                                                thresholdValue != null &&
                                                thresholdValue in 0..100
                                        ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showResourceThresholdDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showProxmoxPatternEditDialog) {
                                AlertDialog(
                                    onDismissRequest = { showProxmoxPatternEditDialog = false },
                                    title = { Text("✏️ Редактировать паттерн") },
                                    text = {
                                        OutlinedTextField(
                                            value = proxmoxPatternEditValueInput,
                                            onValueChange = { proxmoxPatternEditValueInput = it },
                                            label = { Text("Новый паттерн") },
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = proxmoxPatternEditAction + "|" +
                                                    Uri.encode(proxmoxPatternEditValueInput.trim())
                                                onExtensionsSettingsAction(actionPayload)
                                                showProxmoxPatternEditDialog = false
                                            },
                                            enabled = proxmoxPatternEditAction.isNotBlank() &&
                                                proxmoxPatternEditValueInput.isNotBlank()
                                        ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showProxmoxPatternEditDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showMailPatternAddDialog) {
                                AlertDialog(
                                    onDismissRequest = { showMailPatternAddDialog = false },
                                    title = { Text("➕ Добавить паттерн почты") },
                                    text = {
                                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Text("Режим генерации:")
                                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                Button(
                                                    onClick = { mailPatternInputMode = "subject" }
                                                ) { Text("Тема письма") }
                                                Button(
                                                    onClick = { mailPatternInputMode = "fragments" }
                                                ) { Text("Фрагменты") }
                                            }
                                            OutlinedTextField(
                                                value = mailPatternInputValue,
                                                onValueChange = { mailPatternInputValue = it },
                                                label = { Text(if (mailPatternInputMode == "subject") "Тема письма" else "Фрагменты через ; или ,") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = "settings_mail_pattern_add|" +
                                                    Uri.encode(mailPatternInputMode) + "|" +
                                                    Uri.encode(mailPatternInputValue.trim())
                                                onExtensionsSettingsAction(actionPayload)
                                                showMailPatternAddDialog = false
                                            },
                                            enabled = mailPatternInputValue.isNotBlank()
                                        ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showMailPatternAddDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showMailPatternEditDialog) {
                                AlertDialog(
                                    onDismissRequest = { showMailPatternEditDialog = false },
                                    title = { Text("✏️ Редактировать паттерн почты") },
                                    text = {
                                        OutlinedTextField(
                                            value = mailPatternEditValueInput,
                                            onValueChange = { mailPatternEditValueInput = it },
                                            label = { Text("Новый regex паттерн") },
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = mailPatternEditAction + "|" +
                                                    Uri.encode(mailPatternEditValueInput.trim())
                                                onExtensionsSettingsAction(actionPayload)
                                                showMailPatternEditDialog = false
                                            },
                                            enabled = mailPatternEditAction.isNotBlank() &&
                                                mailPatternEditValueInput.isNotBlank()
                                        ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showMailPatternEditDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showZfsHostAddDialog) {
                                AlertDialog(
                                    onDismissRequest = { showZfsHostAddDialog = false },
                                    title = { Text("➕ Добавить ZFS-хост") },
                                    text = {
                                        OutlinedTextField(
                                            value = zfsHostInput,
                                            onValueChange = { zfsHostInput = it },
                                            label = { Text("Имя сервера") },
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = "settings_zfs_add|${Uri.encode(zfsHostInput.trim())}"
                                                onExtensionsSettingsAction(actionPayload)
                                                showZfsHostAddDialog = false
                                            },
                                            enabled = zfsHostInput.isNotBlank()
                                        ) { Text("Добавить") }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showZfsHostAddDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showZfsHostEditDialog) {
                                AlertDialog(
                                    onDismissRequest = { showZfsHostEditDialog = false },
                                    title = { Text("✏️ Переименовать ZFS-хост") },
                                    text = {
                                        OutlinedTextField(
                                            value = zfsHostEditNewNameInput,
                                            onValueChange = { zfsHostEditNewNameInput = it },
                                            label = { Text("Новое имя сервера") },
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = "$zfsHostEditAction|${Uri.encode(zfsHostEditNewNameInput.trim())}"
                                                onExtensionsSettingsAction(actionPayload)
                                                showZfsHostEditDialog = false
                                            },
                                            enabled = zfsHostEditAction.isNotBlank() && zfsHostEditNewNameInput.isNotBlank()
                                        ) { Text("Сохранить") }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showZfsHostEditDialog = false }) {
                                            Text("Отмена")
                                        }
                                    }
                                )
                            }

                            if (showDbCategoryAddDialog) {
                                AlertDialog(
                                    onDismissRequest = { showDbCategoryAddDialog = false },
                                    title = { Text("➕ Добавить категорию БД") },
                                    text = {
                                        OutlinedTextField(
                                            value = dbCategoryInput,
                                            onValueChange = { dbCategoryInput = it },
                                            label = { Text("Название категории") },
                                            modifier = Modifier.fillMaxWidth()
                                        )
                                    },
                                    confirmButton = {
                                        TextButton(onClick = {
                                            val category = dbCategoryInput.trim()
                                            if (category.isNotBlank()) {
                                                onExtensionsSettingsAction("settings_db_add_category|${Uri.encode(category)}")
                                            }
                                            showDbCategoryAddDialog = false
                                        }) { Text("Добавить") }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showDbCategoryAddDialog = false }) { Text("Отмена") }
                                    }
                                )
                            }

                            if (showDbEntryAddDialog) {
                                AlertDialog(
                                    onDismissRequest = { showDbEntryAddDialog = false },
                                    title = { Text("➕ Добавить БД в ${dbEntryAddCategory.uppercase()}") },
                                    text = {
                                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            OutlinedTextField(
                                                value = dbEntryAddKeyInput,
                                                onValueChange = { dbEntryAddKeyInput = it },
                                                label = { Text("Ключ БД") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                            OutlinedTextField(
                                                value = dbEntryAddNameInput,
                                                onValueChange = { dbEntryAddNameInput = it },
                                                label = { Text("Отображаемое имя") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    },
                                    confirmButton = {
                                        TextButton(onClick = {
                                            val key = dbEntryAddKeyInput.trim()
                                            val name = dbEntryAddNameInput.trim()
                                            if (dbEntryAddCategory.isNotBlank() && key.isNotBlank()) {
                                                onExtensionsSettingsAction(
                                                    "settings_db_add_db_submit|${Uri.encode(dbEntryAddCategory)}|${Uri.encode(key)}|${Uri.encode(name)}"
                                                )
                                            }
                                            showDbEntryAddDialog = false
                                        }) { Text("Добавить") }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showDbEntryAddDialog = false }) { Text("Отмена") }
                                    }
                                )
                            }

                            if (showDbEntryEditDialog) {
                                AlertDialog(
                                    onDismissRequest = { showDbEntryEditDialog = false },
                                    title = { Text("✏️ Редактировать БД") },
                                    text = {
                                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Text("Категория: ${dbEntryEditCategory.uppercase()}")
                                            OutlinedTextField(
                                                value = dbEntryEditNewKeyInput,
                                                onValueChange = { dbEntryEditNewKeyInput = it },
                                                label = { Text("Новый ключ БД") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                            OutlinedTextField(
                                                value = dbEntryEditNameInput,
                                                onValueChange = { dbEntryEditNameInput = it },
                                                label = { Text("Новое отображаемое имя") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    },
                                    confirmButton = {
                                        TextButton(onClick = {
                                            val newKey = dbEntryEditNewKeyInput.trim()
                                            val newName = dbEntryEditNameInput.trim()
                                            if (dbEntryEditCategory.isNotBlank() && dbEntryEditOriginalKey.isNotBlank() && newKey.isNotBlank()) {
                                                onExtensionsSettingsAction(
                                                    "settings_db_edit_db_submit|${Uri.encode(dbEntryEditCategory)}|${Uri.encode(dbEntryEditOriginalKey)}|${Uri.encode(newKey)}|${Uri.encode(newName)}"
                                                )
                                            }
                                            showDbEntryEditDialog = false
                                        }) { Text("Сохранить") }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = { showDbEntryEditDialog = false }) { Text("Отмена") }
                                    }
                                )
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

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    if (state.serverEditIp.isBlank()) "Добавить сервер" else "Редактирование сервера ${state.serverEditIp}",
                                    fontWeight = FontWeight.Bold
                                )
                                if (state.serverEditIp.isNotBlank()) {
                                    IconButton(onClick = onCancelServerEdit) {
                                        Icon(
                                            imageVector = Icons.Filled.Close,
                                            contentDescription = "Закрыть редактирование"
                                        )
                                    }
                                }
                            }
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
                            }

                            state.managedServers.forEach { server ->
                                ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                    Column(modifier = Modifier.padding(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                        Text("${server.name} (${server.ip})", fontWeight = FontWeight.Bold)
                                        Text("Тип: ${server.type}, timeout: ${server.timeout ?: 30} сек")
                                        Text("Мониторинг: ${if (server.enabled == true) "включен" else "выключен"}")
                                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                            TextButton(
                                                onClick = { onToggleServerMonitoring(server.ip, server.enabled != true) },
                                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                                            ) {
                                                Text(if (server.enabled == true) "Выкл" else "Вкл")
                                            }
                                            TextButton(
                                                onClick = { onEditServer(server) },
                                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                                            ) { Text("Изм.") }
                                            TextButton(
                                                onClick = { onDeleteServer(server.ip) },
                                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                                            ) { Text("Удал.") }
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
            PullRefreshIndicator(
                refreshing = state.isLoading,
                state = pullToRefreshState,
                modifier = Modifier.align(Alignment.TopCenter)
            )
        }
    }

    if (showServerAvailabilityDialog) {
        AlertDialog(
            onDismissRequest = { showServerAvailabilityDialog = false },
            title = {
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.Top
                    ) {
                        Text(
                            text = "Точечная проверка серверов",
                            modifier = Modifier.weight(1f)
                        )
                        Column(horizontalAlignment = Alignment.End) {
                            IconButton(
                                onClick = { showServerAvailabilityDialog = false },
                                modifier = Modifier
                                    .padding(bottom = 2.dp)
                                    .height(30.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Close,
                                    contentDescription = "Закрыть окно точечной проверки"
                                )
                            }
                            IconButton(
                                onClick = {
                                    onCancelServerEdit()
                                    showServerAddDialog = true
                                },
                                modifier = Modifier.height(30.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Settings,
                                    contentDescription = "Открыть добавление сервера"
                                )
                            }
                        }
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        FilterChip(
                            selected = serverCardsSortMode == ServerCardsSortMode.BY_NAME.name,
                            onClick = { serverCardsSortMode = ServerCardsSortMode.BY_NAME.name },
                            label = { Text("Имя") }
                        )
                        FilterChip(
                            selected = serverCardsSortMode == ServerCardsSortMode.BY_IP.name,
                            onClick = { serverCardsSortMode = ServerCardsSortMode.BY_IP.name },
                            label = { Text("IP") }
                        )
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 420.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (serverButtonsForDialog.isEmpty()) {
                        Text("Серверы для выбранного фильтра не найдены.")
                    } else {
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalArrangement = Arrangement.spacedBy(6.dp),
                            maxItemsInEachRow = 2
                        ) {
                            serverButtonsForDialog.forEach { server ->
                                val serverTarget = if (server.ip.isNotBlank()) server.ip else server.name
                                val isServerEnabled = server.enabled == true
                                val serverMessage = if (
                                    state.message.isNotBlank() &&
                                    state.messageSource == "server_availability" &&
                                    state.availabilityServerMessageTarget == serverTarget
                                ) {
                                    state.message
                                } else {
                                    ""
                                }
                                Surface(
                                    modifier = Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(10.dp))
                                        .combinedClickable(
                                            onClick = { onCheckServerAvailability(server) },
                                            onLongClick = {
                                                serverActionsTargetKey = serverTarget.trim()
                                            }
                                        ),
                                    tonalElevation = 2.dp,
                                    shape = RoundedCornerShape(10.dp),
                                    color = if (isServerEnabled) {
                                        MaterialTheme.colorScheme.tertiaryContainer
                                    } else {
                                        MaterialTheme.colorScheme.errorContainer
                                    }
                                ) {
                                    Column(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(horizontal = 8.dp, vertical = 6.dp),
                                        verticalArrangement = Arrangement.spacedBy(2.dp)
                                    ) {
                                        Text(
                                            text = server.name.ifBlank { server.ip },
                                            fontSize = 12.sp,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            fontWeight = FontWeight.SemiBold
                                        )
                                        Text(
                                            text = server.ip,
                                            fontSize = 11.sp,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                        if (serverMessage.isNotBlank()) {
                                            Text(
                                                text = serverMessage,
                                                style = MaterialTheme.typography.labelSmall,
                                                color = MaterialTheme.colorScheme.error,
                                                maxLines = 2,
                                                overflow = TextOverflow.Ellipsis
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showProxmoxBackupStatsDialog && selectedProxmoxBackupLabel.isNotBlank()) {
        AlertDialog(
            onDismissRequest = { showProxmoxBackupStatsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "📈 Статистика: $selectedProxmoxBackupLabel",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row {
                        IconButton(
                            onClick = {
                                showProxmoxBackupAddDialog = true
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = "Добавить новый бэкап"
                            )
                        }
                        IconButton(onClick = { showProxmoxBackupStatsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть статистику бэкапа"
                            )
                        }
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 420.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (state.message.isNotBlank() && state.messageSource == "global") {
                        Text(state.message)
                    } else {
                        Text("Загружаем статистику бэкапа…")
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showProxmoxBackupsDialog) {
        AlertDialog(
            onDismissRequest = { showProxmoxBackupsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "💾 Бэкапы Proxmox",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = { showProxmoxBackupsDialog = false }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть выбор бэкапа Proxmox"
                        )
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 420.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (state.extensionMenuAction != "backup_proxmox" || state.extensionMenuOptions.isEmpty()) {
                        Text("Загружаем список бэкапов Proxmox…")
                    } else {
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            maxItemsInEachRow = 2
                        ) {
                            state.extensionMenuOptions.forEach { option ->
                                val label = option.label?.trim().orEmpty()
                                val targetAction = resolveMenuOptionAction(option)
                                if (label.isNotBlank() && targetAction.isNotBlank()) {
                                    Surface(
                                        modifier = Modifier
                                            .weight(1f)
                                            .clip(RoundedCornerShape(10.dp))
                                            .clickable {
                                                showProxmoxBackupsDialog = false
                                                selectedProxmoxBackupLabel = label
                                                showProxmoxBackupStatsDialog = true
                                                onAction(targetAction)
                                            },
                                        tonalElevation = 2.dp,
                                        shape = RoundedCornerShape(10.dp),
                                        color = if (isProblemBackupOption(label, targetAction)) {
                                            MaterialTheme.colorScheme.errorContainer
                                        } else {
                                            MaterialTheme.colorScheme.tertiaryContainer
                                        }
                                    ) {
                                        Text(
                                            text = label,
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(horizontal = 10.dp, vertical = 8.dp),
                                            maxLines = 2,
                                            overflow = TextOverflow.Ellipsis,
                                            color = if (isProblemBackupOption(label, targetAction)) {
                                                MaterialTheme.colorScheme.onErrorContainer
                                            } else {
                                                MaterialTheme.colorScheme.onTertiaryContainer
                                            }
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showProxmoxBackupAddDialog) {
        AlertDialog(
            onDismissRequest = { showProxmoxBackupAddDialog = false },
            title = { Text("➕ Добавить Proxmox-бэкап") },
            text = {
                Text("Открыть отдельный диалог добавления бэкапа Proxmox?")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        onExtensionsSettingsAction("settings_proxmox_add")
                        showProxmoxBackupAddDialog = false
                    }
                ) {
                    Text("Открыть")
                }
            },
            dismissButton = {
                TextButton(onClick = { showProxmoxBackupAddDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showServerAddDialog) {
        AlertDialog(
            onDismissRequest = { showServerAddDialog = false },
            title = { Text("Добавить сервер") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedTextField(
                        value = state.serverIpInput,
                        onValueChange = onServerIpChanged,
                        label = { Text("IP") },
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = state.serverNameInput,
                        onValueChange = onServerNameChanged,
                        label = { Text("Имя") },
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = state.serverTypeInput,
                        onValueChange = onServerTypeChanged,
                        label = { Text("Тип (rdp / ssh / ping)") },
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = state.serverTimeoutInput,
                        onValueChange = onServerTimeoutChanged,
                        label = { Text("Timeout, сек") },
                        singleLine = true
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        onSaveServer()
                        showServerAddDialog = false
                    }
                ) {
                    Text("Сохранить")
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerAddDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (selectedServerForActions != null) {
        AlertDialog(
            onDismissRequest = { serverActionsTargetKey = "" },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(selectedServerForActions.name)
                    IconButton(onClick = { serverActionsTargetKey = "" }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть"
                        )
                    }
                }
            },
            text = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                onEditServer(selectedServerForActions)
                                isSettingsExpanded = true
                                settingsSection = "servers"
                                showServerAvailabilityDialog = false
                                serverActionsTargetKey = ""
                            }
                        ) {
                            Icon(Icons.Filled.Edit, contentDescription = "Редактировать")
                        }
                        Text("Изм.", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                onToggleServerMonitoring(
                                    selectedServerForActions.ip,
                                    selectedServerForActions.enabled != true
                                )
                                serverActionsTargetKey = ""
                            }
                        ) {
                            Icon(Icons.Filled.PowerSettingsNew, contentDescription = "Вкл/выкл")
                        }
                        Text(
                            if (selectedServerForActions.enabled == true) "Выкл." else "Вкл.",
                            style = MaterialTheme.typography.labelSmall
                        )
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                onDeleteServer(selectedServerForActions.ip)
                                serverActionsTargetKey = ""
                            }
                        ) {
                            Icon(Icons.Filled.Delete, contentDescription = "Удалить")
                        }
                        Text("Удал.", style = MaterialTheme.typography.labelSmall)
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showTileSettingsDialog) {
        AlertDialog(
            onDismissRequest = { showTileSettingsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Настройка плашек")
                    IconButton(onClick = { showTileSettingsDialog = false }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть"
                        )
                    }
                }
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Отметь плашки, которые показывать сразу. Остальные уйдут под «Развернуть».")
                    allOpsTiles.forEach { tile ->
                        FilterChip(
                            selected = tile.id in pinnedOpsTileIds,
                            onClick = {
                                val checked = tile.id !in pinnedOpsTileIds
                                val updated = if (checked) {
                                    pinnedOpsTileIds + tile.id
                                } else {
                                    pinnedOpsTileIds - tile.id
                                }
                                pinnedOpsTileIds = if (updated.isEmpty()) setOf(tile.id) else updated
                                preferences.compactOpsPinnedTileIds = pinnedOpsTileIds.joinToString(",")
                            },
                            label = { Text(tile.label, style = MaterialTheme.typography.labelMedium) },
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            },
            confirmButton = {}
        )
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
