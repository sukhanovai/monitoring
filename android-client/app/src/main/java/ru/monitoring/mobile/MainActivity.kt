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
import androidx.compose.animation.animateContentSize
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
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CardDefaults
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
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.material.icons.filled.Add
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

private val PROBLEM_BACKUP_MARKERS = listOf("❌", "⚠️", "🚨", "🆘", "⛔", "🔴", "🟠", "⚪")
private val PROBLEM_BACKUP_KEYWORDS = listOf("failed", "error", "problem", "down", "ошиб", "проблем", "недоступ", "не найден", "no backup")
private val backupStatusPrefixRegex = Regex("""^[✅❌⚠️🚨🆘⛔🔴🟠🟡🟢⚪✔]+\s*""")

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

private val zfsStatusLineRegex = Regex("""^•\s*(.+?):\s*([A-Za-z_]+)\s*\((.+)\)$""")
private val zfsDateTimeRegex = Regex("""(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})(?::\d{2})?""")
private val zfsHostHeaderRegex = Regex("""^[A-Za-z0-9._:-]+$""")
private val zfsServerSummaryLineRegex = Regex("""^[⚪🟢🔴]️?\s*\*?`?([^*`·]+?)`?\*?\s*·\s*\d+/\d+\s*·\s*(.+)$""")
private val zfsTotalHostsLineRegex = Regex("""(?i)^\s*всего\s+хостов\s*:\s*(\d+)\s*$""")
private val resourcePercentRegex = Regex("""(\d{1,3})\s*%""")
private val resourceThresholdPatterns = mapOf(
    "set_cpu_warning" to Regex("""(?i)cpu\s+предупреждение\s*:\s*(\d{1,3})\s*%"""),
    "set_cpu_critical" to Regex("""(?i)cpu\s+критическ(?:ий|ое)\s*:\s*(\d{1,3})\s*%"""),
    "set_ram_warning" to Regex("""(?i)ram\s+предупреждение\s*:\s*(\d{1,3})\s*%"""),
    "set_ram_critical" to Regex("""(?i)ram\s+критическ(?:ий|ое)\s*:\s*(\d{1,3})\s*%"""),
    "set_disk_warning" to Regex("""(?i)disk\s+предупреждение\s*:\s*(\d{1,3})\s*%"""),
    "set_disk_critical" to Regex("""(?i)disk\s+критическ(?:ий|ое)\s*:\s*(\d{1,3})\s*%""")
)
private data class ParsedZfsStatusLine(
    val name: String,
    val state: String,
    val timestamp: String
)

private fun extractResourceThresholdValue(
    settingsOptions: List<ru.monitoring.mobile.api.MenuOption>,
    targetAction: String
): Int? {
    val option = settingsOptions.firstOrNull { resolveMenuOptionAction(it) == targetAction } ?: return null
    val label = option.label?.trim().orEmpty()
    val parsed = resourcePercentRegex.find(label)?.groupValues?.getOrNull(1)?.toIntOrNull()
    return parsed?.takeIf { it in 0..100 }
}

private fun extractResourceThresholdValueFromMessage(message: String, targetAction: String): Int? {
    val regex = resourceThresholdPatterns[targetAction] ?: return null
    val parsed = regex.find(message)?.groupValues?.getOrNull(1)?.toIntOrNull()
    return parsed?.takeIf { it in 0..100 }
}

private fun parseZfsStatusLine(label: String): ParsedZfsStatusLine? {
    val trimmed = label.trim()
    val match = zfsStatusLineRegex.matchEntire(trimmed) ?: return null
    val name = match.groupValues.getOrNull(1)?.trim().orEmpty()
    val state = match.groupValues.getOrNull(2)?.trim().orEmpty()
    val timestamp = match.groupValues.getOrNull(3)?.trim().orEmpty()
    if (name.isBlank() || state.isBlank()) return null
    return ParsedZfsStatusLine(name = name, state = state, timestamp = timestamp)
}

private fun zfsStateLabel(state: String): String {
    return when (state.uppercase()) {
        "ONLINE" -> "OK"
        "DEGRADED" -> "DEG"
        "FAULTED" -> "ERR"
        "OFFLINE" -> "OFF"
        "REMOVED" -> "RM"
        "UNAVAIL" -> "NA"
        "SUSPENDED" -> "SUS"
        else -> state.uppercase()
    }
}

private fun compactZfsTimestamp(timestamp: String): String {
    val raw = timestamp.trim()
    if (raw.isBlank()) return ""
    val dateTimeMatch = zfsDateTimeRegex.find(raw)
    if (dateTimeMatch != null) {
        val day = dateTimeMatch.groupValues.getOrNull(1)?.takeLast(5).orEmpty()
        val time = dateTimeMatch.groupValues.getOrNull(2).orEmpty()
        return "$day $time".trim()
    }
    val token = raw.substringBefore(' ')
    return token.takeIf { it.isNotBlank() } ?: raw
}

private fun compactZfsHost(host: String, maxLength: Int = 18): String {
    val normalized = host.trim()
    if (normalized.length <= maxLength) return normalized
    val keepStart = 10
    val keepEnd = 5
    return "${normalized.take(keepStart)}…${normalized.takeLast(keepEnd)}"
}

private fun formatZfsOptionLabel(label: String): String {
    val trimmed = label.trim()
    val match = zfsStatusLineRegex.matchEntire(trimmed) ?: return trimmed
    val host = match.groupValues.getOrNull(1)?.trim().orEmpty()
    val state = match.groupValues.getOrNull(2)?.trim().orEmpty()
    val timestamp = match.groupValues.getOrNull(3)?.trim().orEmpty()
    if (host.isBlank() || state.isBlank()) return trimmed
    val compactHost = compactZfsHost(host)
    val isOk = state.equals("ONLINE", ignoreCase = true)
    val icon = if (isOk) "✅" else "⚠️"
    val readableState = zfsStateLabel(state)
    val compactTimestamp = compactZfsTimestamp(timestamp)
    val tail = buildString {
        append(readableState)
        if (compactTimestamp.isNotBlank()) {
            append(' ')
            append(compactTimestamp)
        }
    }
    return "$icon $compactHost $tail".trim()
}

private fun extractHostFromZfsStatusLabel(label: String): String {
    val trimmed = label.trim()
    val match = zfsStatusLineRegex.matchEntire(trimmed) ?: return ""
    return match.groupValues.getOrNull(1)?.trim().orEmpty()
}

private fun formatZfsMessageForDialog(message: String): String {
    if (message.isBlank()) return message
    return message
        .lineSequence()
        .map { line ->
            val trimmed = line.trim()
            when {
                trimmed.isBlank() -> ""
                zfsStatusLineRegex.matches(trimmed) -> formatZfsOptionLabel(trimmed)
                trimmed == "📊 ZFS статусы (последние)" -> ""
                trimmed.startsWith("📊") || trimmed.startsWith("🧊") -> ""
                trimmed.startsWith("❌") -> "⚠️ ${trimmed.removePrefix("❌").trim()}"
                trimmed.startsWith("•") -> trimmed.removePrefix("•").trim()
                else -> trimmed
            }
        }
        .filter { it.isNotBlank() }
        .joinToString("\n")
}

private fun resolveZfsHostsCount(
    statusMessage: String,
    renderedHostsCount: Int,
    settingsOptions: List<ru.monitoring.mobile.api.MenuOption>
): Int {
    val totalFromMessage = statusMessage
        .lineSequence()
        .map { it.trim() }
        .mapNotNull { line ->
            zfsTotalHostsLineRegex.matchEntire(line)?.groupValues?.getOrNull(1)?.toIntOrNull()
        }
        .firstOrNull()

    val totalFromSettings = settingsOptions
        .asSequence()
        .mapNotNull { option -> resolveMenuOptionAction(option).takeIf { it.isNotBlank() } }
        .mapNotNull { action ->
            when {
                action.startsWith("settings_zfs_toggle_") -> hostNameFromZfsAction(action, "settings_zfs_toggle_")
                action.startsWith("settings_zfs_edit_name_") -> hostNameFromZfsAction(action, "settings_zfs_edit_name_")
                action.startsWith("settings_zfs_delete_") -> hostNameFromZfsAction(action, "settings_zfs_delete_")
                else -> ""
            }.takeIf { it.isNotBlank() }
        }
        .map { it.lowercase() }
        .toSet()
        .size

    return maxOf(renderedHostsCount, totalFromMessage ?: 0, totalFromSettings)
}

private data class ZfsStatusCardItem(
    val hostName: String,
    val pools: List<ZfsPoolStatusItem>,
    val action: String?,
    val rawLabel: String,
    val hasProblem: Boolean,
    val monitoringEnabled: Boolean? = null,
    val monitoringLabel: String = ""
)

private data class ZfsPoolStatusItem(
    val poolName: String,
    val statusLabel: String,
    val rawState: String,
    val rawTimestamp: String,
    val compactTimestamp: String,
    val hasProblem: Boolean
)

private fun toZfsStatusCardItem(option: ru.monitoring.mobile.api.MenuOption): ZfsStatusCardItem? {
    val rawLabel = option.label?.trim().orEmpty()
    val action = resolveMenuOptionAction(option).ifBlank { null }
    if (rawLabel.isBlank()) return null
    val parsed = parseZfsStatusLine(rawLabel) ?: return null
    val status = zfsStateLabel(parsed.state)
    val hasProblem = !parsed.state.equals("ONLINE", ignoreCase = true)
    return ZfsStatusCardItem(
        hostName = parsed.name,
        pools = listOf(
            ZfsPoolStatusItem(
                poolName = "pool",
                statusLabel = status,
                rawState = parsed.state.uppercase(),
                rawTimestamp = parsed.timestamp,
                compactTimestamp = compactZfsTimestamp(parsed.timestamp),
                hasProblem = hasProblem
            )
        ),
        action = action,
        rawLabel = rawLabel,
        hasProblem = hasProblem
    )
}

private fun toZfsStatusCardItem(rawLabel: String, action: String? = null): ZfsStatusCardItem? {
    val normalizedLabel = rawLabel.trim()
    if (normalizedLabel.isBlank()) return null
    val parsed = parseZfsStatusLine(normalizedLabel) ?: return null
    val status = zfsStateLabel(parsed.state)
    val hasProblem = !parsed.state.equals("ONLINE", ignoreCase = true)
    return ZfsStatusCardItem(
        hostName = parsed.name,
        pools = listOf(
            ZfsPoolStatusItem(
                poolName = "pool",
                statusLabel = status,
                rawState = parsed.state.uppercase(),
                rawTimestamp = parsed.timestamp,
                compactTimestamp = compactZfsTimestamp(parsed.timestamp),
                hasProblem = hasProblem
            )
        ),
        action = action?.takeIf { it.isNotBlank() },
        rawLabel = normalizedLabel,
        hasProblem = hasProblem
    )
}

private fun parseZfsStatusCardsFromMessage(message: String): List<ZfsStatusCardItem> {
    if (message.isBlank()) return emptyList()
    val cards = linkedMapOf<String, ZfsStatusCardItem>()
    val poolsByHost = linkedMapOf<String, MutableList<ZfsPoolStatusItem>>()
    var currentHost = ""
    message.lineSequence().forEach { rawLine ->
        val line = rawLine.trim()
        if (line.isBlank()) return@forEach
        if (line.startsWith("📊") || line.startsWith("🧊") || line.startsWith("❌")) return@forEach

        val serverSummaryMatch = zfsServerSummaryLineRegex.matchEntire(line)
        if (serverSummaryMatch != null) {
            val hostName = serverSummaryMatch.groupValues.getOrNull(1)?.trim().orEmpty()
            val receivedAtRaw = serverSummaryMatch.groupValues.getOrNull(2)?.trim().orEmpty()
            if (hostName.isNotBlank()) {
                val isProblem = line.startsWith("🔴")
                val enabled = !line.startsWith("⚪")
                cards[hostName.lowercase()] = ZfsStatusCardItem(
                    hostName = hostName,
                    pools = emptyList(),
                    action = null,
                    rawLabel = line,
                    hasProblem = isProblem,
                    monitoringEnabled = enabled
                )
                currentHost = hostName
                if (receivedAtRaw.isNotBlank()) {
                    val syntheticPool = ZfsPoolStatusItem(
                        poolName = "pool",
                        statusLabel = if (isProblem) "С проблемами" else "ONLINE",
                        rawState = if (isProblem) "DEGRADED" else "ONLINE",
                        rawTimestamp = receivedAtRaw,
                        compactTimestamp = compactZfsTimestamp(receivedAtRaw),
                        hasProblem = isProblem
                    )
                    poolsByHost.getOrPut(hostName) { mutableListOf() }.add(syntheticPool)
                }
            }
            return@forEach
        }

        if (line.startsWith("•")) {
            val parsed = parseZfsStatusLine(line) ?: return@forEach
            val hostName = currentHost.ifBlank { parsed.name }
            if (hostName.isBlank()) return@forEach
            val poolItem = ZfsPoolStatusItem(
                poolName = parsed.name,
                statusLabel = zfsStateLabel(parsed.state),
                rawState = parsed.state.uppercase(),
                rawTimestamp = parsed.timestamp,
                compactTimestamp = compactZfsTimestamp(parsed.timestamp),
                hasProblem = !parsed.state.equals("ONLINE", ignoreCase = true)
            )
            poolsByHost.getOrPut(hostName) { mutableListOf() }.add(poolItem)
            return@forEach
        }
        if (zfsHostHeaderRegex.matches(line)) {
            currentHost = line
        }
    }

    poolsByHost.forEach { (hostName, pools) ->
        val cardKey = hostName.lowercase()
        val existing = cards[cardKey]
        cards[cardKey] = (existing ?: ZfsStatusCardItem(
            hostName = hostName,
            pools = emptyList(),
            action = null,
            rawLabel = "",
            hasProblem = false
        )).copy(
            pools = pools,
            hasProblem = pools.any { it.hasProblem },
            rawLabel = if (pools.isEmpty()) existing?.rawLabel.orEmpty() else pools.joinToString("\n") { pool ->
                "• ${pool.poolName}: ${pool.statusLabel} (${pool.compactTimestamp})"
            }
        )
    }

    return cards.values.toList()
}

private fun zfsCardReceivedAt(card: ZfsStatusCardItem): String {
    val latestTimestamp = card.pools
        .map { it.rawTimestamp.trim() }
        .filter { it.isNotBlank() }
        .maxOrNull()
        .orEmpty()
    return compactZfsTimestamp(latestTimestamp)
}

private fun formatZfsHostDetails(card: ZfsStatusCardItem): String {
    val monitoringEnabledResolved = card.monitoringEnabled ?: if (card.pools.isNotEmpty()) true else null
    val monitoringStatus = when (monitoringEnabledResolved) {
        true -> "включен"
        false -> "выключен"
        null -> "неизвестно"
    }
    val poolsCount = card.pools.size
    val receivedAt = zfsCardReceivedAt(card).ifBlank { "—" }
    val poolsLines = if (card.pools.isEmpty()) {
        "• Пулы: данные отсутствуют"
    } else {
        card.pools.joinToString("\n") { pool ->
            buildString {
                append("• ")
                append(pool.poolName)
                append(": ")
                append(pool.rawState)
                if (pool.rawTimestamp.isNotBlank()) {
                    append(" (")
                    append(pool.rawTimestamp)
                    append(")")
                }
            }
        }
    }
    return buildString {
        appendLine("Хост: ${card.hostName}")
        appendLine("Мониторинг: $monitoringStatus")
        appendLine("Пулов: $poolsCount")
        appendLine("Время данных: $receivedAt")
        appendLine()
        append(poolsLines)
    }.trim()
}

private fun isZfsMonitoringDisabled(toggleLabel: String): Boolean {
    val normalized = toggleLabel.trim().lowercase()
    if (normalized.isBlank()) return false

    return when {
        normalized.contains("включить") ||
            normalized.contains("enable") ||
            normalized.contains("turn on") -> true

        normalized.contains("выключить") ||
            normalized.contains("отключить") ||
            normalized.contains("disable") ||
            normalized.contains("turn off") -> false

        normalized.contains("выключ") || normalized.contains("отключ") -> true
        else -> false
    }
}

private data class ZfsHostOptionGroup(
    val hostName: String,
    val editAction: String,
    val deleteAction: String,
    val toggleAction: String,
    val toggleLabel: String
)

private fun hostNameFromZfsAction(action: String, prefix: String): String {
    if (!action.startsWith(prefix)) return ""
    return Uri.decode(action.removePrefix(prefix)).trim()
}

private fun extractZfsHostOptionGroups(options: List<Pair<String, String>>): List<ZfsHostOptionGroup> {
    data class MutableZfsHostOptionGroup(
        var hostName: String = "",
        var editAction: String = "",
        var deleteAction: String = "",
        var toggleAction: String = "",
        var toggleLabel: String = ""
    )

    val groups = linkedMapOf<String, MutableZfsHostOptionGroup>()

    options.forEach { (label, action) ->
        val editHost = hostNameFromZfsAction(action, "settings_zfs_edit_name_")
        if (editHost.isNotBlank()) {
            val group = groups.getOrPut(editHost.lowercase()) { MutableZfsHostOptionGroup() }
            group.hostName = editHost
            group.editAction = action
            if (group.hostName.isBlank()) {
                group.hostName = label.removePrefix("✏️ ").trim()
            }
            return@forEach
        }

        val deleteHost = hostNameFromZfsAction(action, "settings_zfs_delete_")
        if (deleteHost.isNotBlank()) {
            val group = groups.getOrPut(deleteHost.lowercase()) { MutableZfsHostOptionGroup() }
            if (group.hostName.isBlank()) group.hostName = deleteHost
            group.deleteAction = action
            return@forEach
        }

        val toggleHost = hostNameFromZfsAction(action, "settings_zfs_toggle_")
        if (toggleHost.isNotBlank()) {
            val group = groups.getOrPut(toggleHost.lowercase()) { MutableZfsHostOptionGroup() }
            if (group.hostName.isBlank()) group.hostName = toggleHost
            group.toggleAction = action
            group.toggleLabel = label
        }
    }

    return groups.values
        .mapNotNull { group ->
            val host = group.hostName.trim()
            if (host.isBlank() || group.toggleAction.isBlank()) {
                null
            } else {
                ZfsHostOptionGroup(
                    hostName = host,
                    editAction = group.editAction,
                    deleteAction = group.deleteAction,
                    toggleAction = group.toggleAction,
                    toggleLabel = group.toggleLabel
                )
            }
        }
}

private fun isBackupMonitorDisabled(label: String, action: String): Boolean {
    if (!action.startsWith("db_detail_") && !action.startsWith("backup_host_")) return false
    val normalizedLabel = label.lowercase()
    return label.startsWith("⚪") ||
        normalizedLabel.contains("мониторинг отключ") ||
        normalizedLabel.contains("мониторинг выкл")
}

private data class DatabaseBackupActionPayload(
    val category: String,
    val databaseKey: String
)

private fun decodeDatabaseBackupActionPayload(action: String): DatabaseBackupActionPayload? {
    if (!action.startsWith("db_detail_")) return null
    val encodedPayload = action.removePrefix("db_detail_")
    val payload = Uri.decode(encodedPayload)
    val parts = payload.split("__", limit = 2)
    val category = parts.firstOrNull()?.trim().orEmpty()
    val databaseKey = parts.getOrNull(1)?.trim().orEmpty()
    if (category.isBlank() && databaseKey.isBlank()) return null
    return DatabaseBackupActionPayload(
        category = category,
        databaseKey = databaseKey
    )
}

private data class ProxmoxPatternOptionGroup(
    val label: String,
    val editAction: String,
    val deleteAction: String
)

private data class PatternActionGroupDraft(
    var label: String = "",
    var editAction: String = "",
    var deleteAction: String = ""
)

private fun extractPatternGroupKey(action: String, fallbackLabel: String): String {
    val rawKey = when {
        action.startsWith("settings_proxmox_pattern_edit_") -> action.removePrefix("settings_proxmox_pattern_edit_")
        action.startsWith("settings_proxmox_pattern_delete_") -> action.removePrefix("settings_proxmox_pattern_delete_")
        else -> ""
    }.substringBefore("|").trim()
    return if (rawKey.isNotBlank()) {
        "id:$rawKey"
    } else {
        "label:${normalizeProxmoxPatternLabel(fallbackLabel)}"
    }
}

private fun buildPatternOptionGroups(options: List<MenuOption>): List<ProxmoxPatternOptionGroup> {
    val grouped = linkedMapOf<String, PatternActionGroupDraft>()
    options.forEach { option ->
        val action = resolveMenuOptionAction(option)
        val normalizedLabel = normalizeProxmoxPatternLabel(option.label?.trim().orEmpty())
        when {
            action.startsWith("settings_proxmox_pattern_edit_") -> {
                val key = extractPatternGroupKey(action, normalizedLabel)
                val group = grouped.getOrPut(key) { PatternActionGroupDraft() }
                group.editAction = action
                if (normalizedLabel.isNotBlank()) {
                    group.label = normalizedLabel
                }
            }

            action.startsWith("settings_proxmox_pattern_delete_") -> {
                val key = extractPatternGroupKey(action, normalizedLabel)
                val group = grouped.getOrPut(key) { PatternActionGroupDraft() }
                group.deleteAction = action
                if (group.label.isBlank() && normalizedLabel.isNotBlank()) {
                    group.label = normalizedLabel
                }
            }
        }
    }

    return grouped.values.mapNotNull { group ->
        if (group.editAction.isBlank() && group.deleteAction.isBlank()) {
            null
        } else {
            ProxmoxPatternOptionGroup(
                label = group.label.ifBlank { "без названия" },
                editAction = group.editAction,
                deleteAction = group.deleteAction
            )
        }
    }
}

private data class DatabasePatternOptionGroup(
    val label: String,
    val editAction: String,
    val deleteAction: String
)

private data class MailPatternOptionGroup(
    val label: String,
    val editAction: String,
    val deleteAction: String
)

private val mailPatternMessageLineRegex = Regex("""^(\d+)\.\s*(?:🟢|🔴)\s*\[([^\]]+)]\s*(.+)$""")
private val mailPatternActionLabelRegex = Regex("""^(?:[✏️🗑️✅⛔️]+\s*)?(\d+)\.\s*mail:([^\s]+).*$""")

private fun extractMailPatternDisplayByIndex(message: String): Map<Int, String> {
    if (message.isBlank()) return emptyMap()
    return message
        .lineSequence()
        .map { line ->
            line
                .trim()
                .replace("\\_", "_")
                .replace("\\-", "-")
                .replace("*", "")
        }
        .mapNotNull { line ->
            val match = mailPatternMessageLineRegex.matchEntire(line) ?: return@mapNotNull null
            val index = match.groupValues[1].toIntOrNull() ?: return@mapNotNull null
            val patternType = match.groupValues[2].trim()
            val patternValue = match.groupValues[3].trim()
            index to "${index}. ${patternType}: ${patternValue}"
        }
        .toMap()
}

private fun extractMailPatternIndexFromLabel(rawLabel: String): Int? {
    return mailPatternActionLabelRegex.matchEntire(rawLabel.trim())
        ?.groupValues
        ?.getOrNull(1)
        ?.toIntOrNull()
}

private fun parseMailPatternEditValue(rawLabel: String): String {
    val normalizedLabel = normalizeProxmoxPatternLabel(rawLabel)
        .replaceFirst(Regex("""^\d+\.\s*"""), "")
        .trim()
    return when {
        normalizedLabel.startsWith("mail:", ignoreCase = true) ->
            normalizedLabel.substringAfter("mail:", "").trim()
        ':' in normalizedLabel ->
            normalizedLabel.substringAfter(':', "").trim()
        else -> normalizedLabel
    }
}

private fun normalizeProxmoxPatternLabel(rawLabel: String): String {
    return rawLabel
        .replaceFirst(Regex("""^[✏️🗑️]+\s*"""), "")
        .trim()
}

private data class ProxmoxPatternEditPrefill(
    val patternType: String,
    val patternValue: String
)

private fun parseProxmoxPatternEditPrefill(rawLabel: String): ProxmoxPatternEditPrefill {
    val normalizedLabel = normalizeProxmoxPatternLabel(rawLabel)
        .replaceFirst(Regex("""^\d+\.\s*"""), "")
        .trim()
    val details = normalizedLabel.substringAfter(". ", normalizedLabel).trim()
    val separator = " — "
    val typePart = details.substringBefore(separator, details).trim()
    val valuePart = details.substringAfter(separator, "").trim()
    val parsedType = typePart.substringAfter(':', typePart).trim().ifBlank { "subject" }
    return ProxmoxPatternEditPrefill(
        patternType = parsedType,
        patternValue = valuePart
    )
}

private fun deriveDatabaseBackupLabelFromAction(action: String): String {
    val payload = decodeDatabaseBackupActionPayload(action) ?: return ""
    val fallback = if (payload.databaseKey.isNotBlank()) {
        payload.databaseKey
    } else {
        payload.category
    }
    return fallback.replace('_', ' ')
}

private fun normalizeDatabaseBackupCategory(category: String): String {
    val normalized = category.trim()
    return if (normalized.equals("company database", ignoreCase = true)) {
        "company"
    } else {
        normalized
    }
}

private fun formatBackupLabelWithMonitorStatus(label: String, action: String): String {
    if (!action.startsWith("db_detail_") && !action.startsWith("backup_host_")) return label
    val monitorMarker = if (isBackupMonitorDisabled(label, action)) "⚪" else "🟢"
    val decodedPayload = decodeDatabaseBackupActionPayload(action)
    val fallbackName = if (action.startsWith("db_detail_")) {
        deriveDatabaseBackupLabelFromAction(action)
    } else {
        action.removePrefix("backup_host_").replace('_', ' ').trim()
    }
    val categoryName = normalizeDatabaseBackupCategory(
        decodedPayload?.category
            ?.replace('_', ' ')
            ?.trim()
            .orEmpty()
    )
    val sanitizedLines = label.lineSequence()
        .map { it.trim() }
        .map { line ->
            val lineWithoutStatusPrefix = line.replace(backupStatusPrefixRegex, "").trim()
            val normalizedLine = if (lineWithoutStatusPrefix.startsWith("Категория:", ignoreCase = true)) {
                lineWithoutStatusPrefix.substringAfter(':').trim()
            } else {
                lineWithoutStatusPrefix
            }
            normalizeDatabaseBackupCategory(normalizedLine)
        }
        .filter { line ->
            line.isNotBlank() &&
                !line.contains("мониторинг вкл", ignoreCase = true) &&
                !line.contains("мониторинг выкл", ignoreCase = true) &&
                !line.equals("🟢", ignoreCase = true) &&
                !line.equals("⚪", ignoreCase = true)
        }
        .toMutableList()

    if (sanitizedLines.isEmpty() && fallbackName.isNotBlank()) {
        sanitizedLines += fallbackName
    }

    if (action.startsWith("db_detail_")) {
        val normalizedCategory = categoryName.lowercase()
        val hasCategoryLine = normalizedCategory.isNotBlank() &&
            sanitizedLines.any { line ->
                val normalizedLine = line.lowercase()
                normalizedLine.contains(normalizedCategory) || normalizedLine.contains("категор")
            }
        if (categoryName.isNotBlank() && !hasCategoryLine) {
            sanitizedLines.add(0, categoryName)
        }
    }

    if (sanitizedLines.isEmpty()) return monitorMarker
    sanitizedLines += monitorMarker
    return sanitizedLines.joinToString("\n")
}

private fun extractDatabaseBackupLines(message: String): List<String> {
    if (message.isBlank()) return emptyList()
    return message.lineSequence()
        .map { it.trim() }
        .filter { line ->
            line.isNotBlank() && (
                line.startsWith("✅") ||
                    line.startsWith("❌") ||
                    line.startsWith("⚠️") ||
                    line.startsWith("🚨") ||
                    line.startsWith("⚪") ||
                    line.startsWith("🟡") ||
                    line.startsWith("🟢") ||
                    line.startsWith("•")
                )
        }
        .toList()
}

private data class OpsMetricTile(
    val id: String,
    val label: String,
    val value: String,
    val hasProblem: Boolean = false,
    val onClick: () -> Unit = {},
    val onLongClick: (() -> Unit)? = null,
    val onSettingsClick: (() -> Unit)? = null
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

private fun normalizeServerLookupToken(raw: String): String = raw.trim().lowercase()

private fun resolveAvailabilityMarker(statusRaw: String?): String {
    val normalizedStatus = statusRaw?.trim().orEmpty().lowercase()
    return when {
        normalizedStatus == "up" -> "🟢"
        normalizedStatus in setOf("down", "unreachable", "offline", "error", "critical") -> "🔴"
        else -> "⚪"
    }
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
    modifier: Modifier = Modifier,
    onClick: () -> Unit = {},
    onLongClick: (() -> Unit)? = null,
    onSettingsClick: (() -> Unit)? = null
) {
    val valueColor = if (hasProblem) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface
    Surface(
        modifier = modifier
            .widthIn(min = 72.dp)
            .wrapContentWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.7f))
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            ),
        shape = RoundedCornerShape(14.dp),
        tonalElevation = 1.dp
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(value, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = valueColor)
                Text(label, style = MaterialTheme.typography.labelSmall)
            }
            if (onSettingsClick != null) {
                IconButton(
                    onClick = onSettingsClick,
                    modifier = Modifier.height(28.dp)
                ) {
                    Icon(
                        imageVector = Icons.Filled.Settings,
                        contentDescription = "Настройки $label"
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ZfsStatusTile(
    card: ZfsStatusCardItem,
    onClick: () -> Unit,
    onLongClick: () -> Unit
) {
    val containerColor = if (card.hasProblem) {
        MaterialTheme.colorScheme.errorContainer
    } else {
        MaterialTheme.colorScheme.tertiaryContainer
    }
    val contentColor = if (card.hasProblem) {
        MaterialTheme.colorScheme.onErrorContainer
    } else {
        MaterialTheme.colorScheme.onTertiaryContainer
    }
    val monitoringDotColor = when (card.monitoringEnabled) {
        true -> Color(0xFF2E7D32)
        false -> Color(0xFF9E9E9E)
        null -> Color(0xFFFFB300)
    }
    val receivedAt = zfsCardReceivedAt(card).ifBlank { "—" }
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            ),
        tonalElevation = 2.dp,
        shape = RoundedCornerShape(10.dp),
        color = containerColor
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Spacer(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(monitoringDotColor)
                )
                Text(
                    text = card.hostName,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    color = contentColor
                )
            }
            Text(
                text = receivedAt,
                style = MaterialTheme.typography.labelSmall,
                color = contentColor.copy(alpha = 0.8f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
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
    var serverDeleteConfirmTargetKey by rememberSaveable { mutableStateOf("") }
    var serverCardsSortMode by rememberSaveable { mutableStateOf(ServerCardsSortMode.BY_NAME.name) }
    var showServerResourcesMenu by rememberSaveable { mutableStateOf(false) }
    var showServerResourcesDetailsDialog by rememberSaveable { mutableStateOf(false) }
    var serverResourceDetailsTargetKey by rememberSaveable { mutableStateOf("") }
    var serverResourceDetailsTitle by rememberSaveable { mutableStateOf("") }
    var areOpsTilesExpanded by rememberSaveable { mutableStateOf(false) }
    var showTileSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var settingsSection by rememberSaveable { mutableStateOf("bff") }
    var showProxmoxPatternAddDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxPatternEditDialog by rememberSaveable { mutableStateOf(false) }
    var proxmoxPatternCategoryInput by rememberSaveable { mutableStateOf("proxmox") }
    var proxmoxPatternTypeInput by rememberSaveable { mutableStateOf("subject") }
    var proxmoxPatternValueInput by rememberSaveable { mutableStateOf("") }
    var proxmoxPatternEditAction by rememberSaveable { mutableStateOf("") }
    var patternDialogReturnAction by rememberSaveable { mutableStateOf("settings_patterns_proxmox") }
    var proxmoxPatternEditTypeInput by rememberSaveable { mutableStateOf("subject") }
    var proxmoxPatternEditValueInput by rememberSaveable { mutableStateOf("") }
    var showMailPatternAddDialog by rememberSaveable { mutableStateOf(false) }
    var showMailPatternEditDialog by rememberSaveable { mutableStateOf(false) }
    var mailPatternInputMode by rememberSaveable { mutableStateOf("subject") }
    var mailPatternInputValue by rememberSaveable { mutableStateOf("") }
    var mailPatternEditAction by rememberSaveable { mutableStateOf("") }
    var mailPatternEditValueInput by rememberSaveable { mutableStateOf("") }
    var showMailPatternsDialog by rememberSaveable { mutableStateOf(false) }
    var showMailPatternActionsDialog by rememberSaveable { mutableStateOf(false) }
    var selectedMailPatternLabel by rememberSaveable { mutableStateOf("") }
    var selectedMailPatternEditAction by rememberSaveable { mutableStateOf("") }
    var selectedMailPatternDeleteAction by rememberSaveable { mutableStateOf("") }
    var returnToMailPatternsDialog by rememberSaveable { mutableStateOf(false) }
    var showDbCategoryAddDialog by rememberSaveable { mutableStateOf(false) }
    var dbCategoryInput by rememberSaveable { mutableStateOf("") }
    var showDbEntryAddDialog by rememberSaveable { mutableStateOf(false) }
    var showDbOpsEntryAddDialog by rememberSaveable { mutableStateOf(false) }
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
    var showZfsStatusesDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsHostsSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsHostActionsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsHostDetailsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsPatternsDialog by rememberSaveable { mutableStateOf(false) }
    var zfsHostInput by rememberSaveable { mutableStateOf("") }
    var zfsHostEditAction by rememberSaveable { mutableStateOf("") }
    var zfsHostEditCurrentName by rememberSaveable { mutableStateOf("") }
    var zfsHostEditNewNameInput by rememberSaveable { mutableStateOf("") }
    var zfsSelectedHostName by rememberSaveable { mutableStateOf("") }
    var zfsSelectedHostEditAction by rememberSaveable { mutableStateOf("") }
    var zfsSelectedHostDeleteAction by rememberSaveable { mutableStateOf("") }
    var showZfsHostDeleteConfirmDialog by rememberSaveable { mutableStateOf(false) }
    var zfsHostDeleteConfirmName by rememberSaveable { mutableStateOf("") }
    var zfsHostDeleteConfirmAction by rememberSaveable { mutableStateOf("") }
    var zfsSelectedHostToggleAction by rememberSaveable { mutableStateOf("") }
    var zfsDetailsHostName by rememberSaveable { mutableStateOf("") }
    var zfsStatusDetailsFallbackText by rememberSaveable { mutableStateOf("") }
    var pendingZfsHostSettingsName by rememberSaveable { mutableStateOf("") }
    var showResourceThresholdDialog by rememberSaveable { mutableStateOf(false) }
    var showResourceSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var resourceThresholdAction by rememberSaveable { mutableStateOf("") }
    var resourceThresholdLabel by rememberSaveable { mutableStateOf("") }
    var resourceThresholdValueInput by rememberSaveable { mutableStateOf("") }
    var resourceThresholdCurrentValue by rememberSaveable { mutableStateOf<Int?>(null) }
    var resourceThresholdOverrides by rememberSaveable { mutableStateOf<Map<String, Int>>(emptyMap()) }
    var selectedProxmoxBackupLabel by rememberSaveable { mutableStateOf("") }
    var selectedDatabaseBackupLabel by rememberSaveable { mutableStateOf("") }
    var showProxmoxBackupStatsDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxBackupsDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxPatternsDialog by rememberSaveable { mutableStateOf(false) }
    var showProxmoxPatternActionsDialog by rememberSaveable { mutableStateOf(false) }
    var selectedProxmoxPatternLabel by rememberSaveable { mutableStateOf("") }
    var selectedProxmoxPatternEditAction by rememberSaveable { mutableStateOf("") }
    var selectedProxmoxPatternDeleteAction by rememberSaveable { mutableStateOf("") }
    var proxmoxPatternDeleteConfirmLabel by rememberSaveable { mutableStateOf("") }
    var proxmoxPatternDeleteConfirmAction by rememberSaveable { mutableStateOf("") }
    var showDatabaseBackupsDialog by rememberSaveable { mutableStateOf(false) }
    var showMailBackupsDialog by rememberSaveable { mutableStateOf(false) }
    var showDatabasePatternsDialog by rememberSaveable { mutableStateOf(false) }
    var showDatabasePatternActionsDialog by rememberSaveable { mutableStateOf(false) }
    var selectedDatabasePatternLabel by rememberSaveable { mutableStateOf("") }
    var selectedDatabasePatternEditAction by rememberSaveable { mutableStateOf("") }
    var selectedDatabasePatternDeleteAction by rememberSaveable { mutableStateOf("") }
    var showProxmoxServerAddDialog by rememberSaveable { mutableStateOf(false) }
    var proxmoxServerNameInput by rememberSaveable { mutableStateOf("") }
    var proxmoxHostActionsTargetKey by rememberSaveable { mutableStateOf("") }
    var proxmoxHostDeleteConfirmTargetKey by rememberSaveable { mutableStateOf("") }
    var databaseActionsTargetAction by rememberSaveable { mutableStateOf("") }
    var showMorningReportDialog by rememberSaveable { mutableStateOf(false) }

    LaunchedEffect(
        pendingZfsHostSettingsName,
        state.extensionSettingsMenuAction,
        state.extensionSettingsMenuOptions
    ) {
        val pendingHost = pendingZfsHostSettingsName.trim()
        if (pendingHost.isBlank()) return@LaunchedEffect
        if (state.extensionSettingsMenuAction != "settings_zfs_list") return@LaunchedEffect
        if (state.extensionSettingsMenuOptions.isEmpty()) return@LaunchedEffect
        val zfsMenuPairs = state.extensionSettingsMenuOptions
            .mapNotNull { option ->
                val action = resolveMenuOptionAction(option)
                val label = option.label?.trim().orEmpty()
                if (label.isBlank() || action.isBlank()) null else label to action
            }
        val hostGroup = extractZfsHostOptionGroups(zfsMenuPairs)
            .firstOrNull { it.hostName.equals(pendingHost, ignoreCase = true) }
        if (hostGroup != null) {
            zfsSelectedHostName = hostGroup.hostName
            zfsSelectedHostEditAction = hostGroup.editAction
            zfsSelectedHostDeleteAction = hostGroup.deleteAction
            zfsSelectedHostToggleAction = hostGroup.toggleAction
            showZfsHostActionsDialog = true
            showZfsHostsSettingsDialog = false
            pendingZfsHostSettingsName = ""
        }
    }

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
    val enabledManagedServers = state.managedServers.filter { it.enabled != false }
    val proxmoxPatternMenuAction = state.extensionSettingsMenuAction
        .takeIf { it == "settings_patterns_proxmox" || it == "settings_backup_patterns" }
        ?: state.extensionMenuAction.takeIf { it == "settings_patterns_proxmox" || it == "settings_backup_patterns" }
    val zfsPatternMenuAction = state.extensionSettingsMenuAction
        .takeIf { it == "settings_patterns_zfs" }
        ?: state.extensionMenuAction.takeIf { it == "settings_patterns_zfs" }
    val databasePatternMenuAction = state.extensionSettingsMenuAction
        .takeIf { it == "settings_patterns_db" || it == "settings_backup_db_patterns" }
        ?: state.extensionMenuAction.takeIf { it == "settings_patterns_db" || it == "settings_backup_db_patterns" }
    val mailPatternMenuAction = state.extensionSettingsMenuAction
        .takeIf { it == "settings_patterns_mail" }
        ?: state.extensionMenuAction.takeIf { it == "settings_patterns_mail" }
    val proxmoxPatternMenuOptions = when {
        proxmoxPatternMenuAction == state.extensionSettingsMenuAction && state.extensionSettingsMenuOptions.isNotEmpty() ->
            state.extensionSettingsMenuOptions
        proxmoxPatternMenuAction == state.extensionMenuAction && state.extensionMenuOptions.isNotEmpty() ->
            state.extensionMenuOptions
        state.extensionSettingsMenuOptions.isNotEmpty() -> state.extensionSettingsMenuOptions
        else -> state.extensionMenuOptions
    }
    val proxmoxPatternOptionGroups = if (proxmoxPatternMenuAction != null) {
        buildPatternOptionGroups(proxmoxPatternMenuOptions)
    } else {
        emptyList()
    }
    val zfsPatternMenuOptions = when {
        zfsPatternMenuAction == state.extensionSettingsMenuAction && state.extensionSettingsMenuOptions.isNotEmpty() ->
            state.extensionSettingsMenuOptions
        zfsPatternMenuAction == state.extensionMenuAction && state.extensionMenuOptions.isNotEmpty() ->
            state.extensionMenuOptions
        state.extensionSettingsMenuOptions.isNotEmpty() -> state.extensionSettingsMenuOptions
        else -> state.extensionMenuOptions
    }
    val zfsPatternOptionGroups = if (zfsPatternMenuAction != null) {
        buildPatternOptionGroups(zfsPatternMenuOptions)
    } else {
        emptyList()
    }
    val databasePatternMenuOptions = when {
        databasePatternMenuAction == state.extensionSettingsMenuAction && state.extensionSettingsMenuOptions.isNotEmpty() ->
            state.extensionSettingsMenuOptions
        databasePatternMenuAction == state.extensionMenuAction && state.extensionMenuOptions.isNotEmpty() ->
            state.extensionMenuOptions
        state.extensionSettingsMenuOptions.isNotEmpty() -> state.extensionSettingsMenuOptions
        else -> state.extensionMenuOptions
    }
    val databasePatternOptionGroups = if (databasePatternMenuAction != null) {
        buildPatternOptionGroups(databasePatternMenuOptions).map { pattern ->
            DatabasePatternOptionGroup(
                label = pattern.label,
                editAction = pattern.editAction,
                deleteAction = pattern.deleteAction
            )
        }
    } else {
        emptyList()
    }
    val mailPatternMenuOptions = when {
        mailPatternMenuAction == state.extensionSettingsMenuAction && state.extensionSettingsMenuOptions.isNotEmpty() ->
            state.extensionSettingsMenuOptions
        mailPatternMenuAction == state.extensionMenuAction && state.extensionMenuOptions.isNotEmpty() ->
            state.extensionMenuOptions
        state.extensionSettingsMenuOptions.isNotEmpty() -> state.extensionSettingsMenuOptions
        else -> state.extensionMenuOptions
    }
    val mailPatternDisplayByIndex = if (mailPatternMenuAction == "settings_patterns_mail" &&
        state.messageSource == "extensions_settings"
    ) {
        extractMailPatternDisplayByIndex(state.message)
    } else {
        emptyMap()
    }
    val mailPatternOptionGroups = if (mailPatternMenuAction != null) {
        val grouped = linkedMapOf<String, Triple<String, String, String>>()
        mailPatternMenuOptions.forEach { option ->
            val action = resolveMenuOptionAction(option)
            val label = option.label?.trim().orEmpty()
            when {
                action.startsWith("settings_mail_pattern_edit_") -> {
                    val rawPatternLabel = normalizeProxmoxPatternLabel(label.ifBlank {
                        Uri.decode(action.removePrefix("settings_mail_pattern_edit_"))
                    })
                    val patternIndex = extractMailPatternIndexFromLabel(rawPatternLabel)
                    val patternLabel = patternIndex?.let { mailPatternDisplayByIndex[it] } ?: rawPatternLabel
                    val key = patternIndex?.toString() ?: patternLabel
                    if (patternLabel.isNotBlank()) {
                        val current = grouped[key] ?: Triple(patternLabel, "", "")
                        grouped[key] = Triple(patternLabel, action, current.third)
                    }
                }
                action.startsWith("settings_mail_pattern_delete_") -> {
                    val rawPatternLabel = normalizeProxmoxPatternLabel(label.ifBlank {
                        Uri.decode(action.removePrefix("settings_mail_pattern_delete_"))
                    })
                    val patternIndex = extractMailPatternIndexFromLabel(rawPatternLabel)
                    val patternLabel = patternIndex?.let { mailPatternDisplayByIndex[it] } ?: rawPatternLabel
                    val key = patternIndex?.toString() ?: patternLabel
                    if (patternLabel.isNotBlank()) {
                        val current = grouped[key] ?: Triple(patternLabel, "", "")
                        grouped[key] = Triple(patternLabel, current.second, action)
                    }
                }
            }
        }
        grouped.mapNotNull { (_, item) ->
            val label = item.first
            val editAction = item.second
            val deleteAction = item.third
            if (editAction.isBlank() && deleteAction.isBlank()) {
                null
            } else {
                MailPatternOptionGroup(
                    label = label,
                    editAction = editAction,
                    deleteAction = deleteAction
                )
            }
        }
    } else {
        emptyList()
    }
    val enabledManagedTokens = enabledManagedServers
        .flatMap { server -> listOf(server.ip, server.name) }
        .map { it.trim().lowercase() }
        .filter { it.isNotBlank() }
        .toSet()
    val serversForOpsCenter = if (enabledManagedTokens.isEmpty()) {
        state.servers
    } else {
        state.servers.filter { server ->
            val idToken = server.id.trim().lowercase()
            val nameToken = server.name.trim().lowercase()
            idToken in enabledManagedTokens || nameToken in enabledManagedTokens
        }
    }
    val upServersCount = serversForOpsCenter.count { it.status.equals("UP", ignoreCase = true) }
    val downServersCount = serversForOpsCenter.count { it.status.equals("DOWN", ignoreCase = true) }
    val unknownServersCount = serversForOpsCenter.count { it.status.equals("UNKNOWN", ignoreCase = true) }
    val totalServersCount = enabledManagedServers.size.takeIf { it > 0 } ?: serversForOpsCenter.size
    val activeServersCount = upServersCount.coerceAtMost(totalServersCount)
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
    val appTitle = "ComDone"
    val contentPadding = if (isCompactOpsHub) 10.dp else 16.dp
    val sectionSpacing = if (isCompactOpsHub) 8.dp else 12.dp
    val openServersDetails = {
        onRefresh()
        showServerAvailabilityDialog = false
    }
    val openServerSingleCheckDetails = {
        onLoadServersForSingleCheck()
        showServerResourcesMenu = false
        showServerAvailabilityDialog = true
    }
    val openServerResourcesSingleCheckDetails = {
        onLoadServersForSingleCheck()
        showServerResourcesMenu = true
        showServerAvailabilityDialog = true
    }
    val openProxmoxBackupDetails = {
        onAction("backup_proxmox")
        showProxmoxBackupsDialog = true
    }
    val openDatabaseBackupDetails = {
        onAction("backup_databases")
        selectedDatabaseBackupLabel = ""
        selectedProxmoxBackupLabel = ""
        showProxmoxBackupStatsDialog = false
        showDatabaseBackupsDialog = true
    }
    val selectedProxmoxHostForActions = state.extensionMenuOptions.firstOrNull { option ->
        val targetAction = resolveMenuOptionAction(option)
        targetAction == "backup_host_$proxmoxHostActionsTargetKey"
    }
    val selectedDatabaseForActions = state.extensionMenuOptions.firstOrNull { option ->
        val targetAction = resolveMenuOptionAction(option)
        targetAction == databaseActionsTargetAction
    }
    val selectedDatabaseActionPayload = selectedDatabaseForActions
        ?.let { resolveMenuOptionAction(it) }
        ?.removePrefix("db_detail_")
        ?.takeIf { "__" in it }
    val selectedDatabaseActionCategory = selectedDatabaseActionPayload
        ?.substringBefore("__")
        ?.trim()
        .orEmpty()
    val selectedDatabaseActionKey = selectedDatabaseActionPayload
        ?.substringAfter("__", "")
        ?.trim()
        .orEmpty()
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
            id = "modes",
            label = "Режим",
            value = state.silentStatusText,
            onClick = openModesDetails
        ),
        OpsMetricTile(
            id = "servers",
            label = "Серверы",
            value = "$activeServersCount/$totalServersCount",
            hasProblem = hasServerProblems,
            onClick = {
                openServerSingleCheckDetails()
            },
            onLongClick = openServerSingleCheckDetails
        )
    )
    val extensionsById = state.extensions.associateBy { it.id }
    val extensionInfoTiles = buildList {
        extensionsById["resource_monitor"]?.takeIf { it.enabled }?.let { extension ->
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
        extensionsById["backup_monitor"]?.takeIf { it.enabled }?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "proxmox"),
                    summaryOverride = state.backupProxmoxSummary,
                    hasProblemOverride = state.backupProxmoxHasProblemItems
                )
            )
        }
        extensionsById["database_backup_monitor"]?.takeIf { it.enabled }?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "БД"),
                    summaryOverride = state.backupDatabasesSummary,
                    hasProblemOverride = state.backupDatabasesHasProblemItems
                )
            )
        }
        extensionsById["mail_backup_monitor"]?.takeIf { it.enabled }?.let { extension ->
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
        extensionsById["zfs_monitor"]?.takeIf { it.enabled }?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "zfs"),
                    summaryOverride = state.zfsSummary,
                    hasProblemOverride = state.zfsHasProblemItems
                )
            )
        }
        extensionsById["stock_load_monitor"]?.takeIf { it.enabled }?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "остатки"),
                    summaryOverride = state.backupStockLoadsSummary,
                    hasProblemOverride = state.backupStockLoadsHasProblemItems
                )
            )
        }
        extensionsById["supplier_stock_files"]?.takeIf { it.enabled }?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(name = "поставщики"),
                    summaryOverride = state.supplierStockSummary,
                    hasProblemOverride = state.supplierStockHasProblemItems
                )
            )
        }
        extensionsById["web_interface"]?.takeIf { it.enabled }?.let { extension ->
            add(buildToggleDataTile(label = "web", enabled = extension.enabled))
        }
        extensionsById["email_processor"]?.takeIf { it.enabled }?.let { extension ->
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
                    selectedDatabaseBackupLabel = ""
                    showProxmoxBackupStatsDialog = false
                    openProxmoxBackupDetails()
                }
            } else if (extension.id == "database_backup_monitor") {
                {
                    selectedDatabaseBackupLabel = ""
                    selectedProxmoxBackupLabel = ""
                    showProxmoxBackupStatsDialog = false
                    openDatabaseBackupDetails()
                }
            } else if (extension.id == "mail_backup_monitor") {
                {
                    showMailBackupsDialog = true
                    onToggleMailBackupMenu()
                }
            } else if (extension.id == "zfs_monitor") {
                {
                    showZfsStatusesDialog = true
                    onAction("zfs_menu")
                    onExtensionsSettingsAction("settings_zfs_list")
                }
            } else if (extension.id == "resource_monitor") {
                {
                    openServerResourcesSingleCheckDetails()
                }
            } else {
                { isSettingsExpanded = true; settingsSection = "extensions"; isExtensionsSettingsOpened = true }
            },
            onLongClick = null,
            onSettingsClick = null
        )
    }
    val allOpsTiles = opsTiles + extensionOpsTiles
    val defaultPinnedTileIds = setOf("servers", "modes")
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
    val availabilityStatusByToken = state.servers
        .flatMap { availability ->
            listOf(
                normalizeServerLookupToken(availability.id) to availability.status,
                normalizeServerLookupToken(availability.name) to availability.status
            )
        }
        .filter { (token, _) -> token.isNotBlank() }
        .toMap()
    val selectedServerForActions = state.managedServers.firstOrNull { managedServer ->
        val key = managedServer.ip.ifBlank { managedServer.name }.trim()
        key == serverActionsTargetKey
    }


    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text(appTitle, fontWeight = FontWeight.SemiBold)
                },
                actions = {
                    IconButton(onClick = onCloseApp) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Свернуть приложение"
                        )
                    }
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
                                    showServerResourcesDetailsDialog = false
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
                            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                IconButton(onClick = { showTileSettingsDialog = true }) {
                                    Icon(
                                        imageVector = Icons.Filled.Settings,
                                        contentDescription = "Настроить плашки"
                                    )
                                }
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
                                    modifier = Modifier.animateContentSize(),
                                    onClick = tile.onClick,
                                    onLongClick = tile.onLongClick,
                                    onSettingsClick = tile.onSettingsClick
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
                                onClick = {
                                    showMorningReportDialog = true
                                    onAction("send_morning_report")
                                }
                            )
                            DashboardActionButton(
                                label = "⚙️ Общие настройки",
                                onClick = { isSettingsExpanded = !isSettingsExpanded }
                            )
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
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (state.message.isNotBlank() && state.messageSource == "morning_report") {
                        Text(state.message)
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
                                                    patternDialogReturnAction =
                                                        if (proxmoxPatternCategoryInput.equals("database", ignoreCase = true)) {
                                                            "settings_patterns_db"
                                                        } else {
                                                            "settings_patterns_proxmox"
                                                        }
                                                    showProxmoxPatternAddDialog = true
                                                }
                                                action.startsWith("settings_proxmox_pattern_edit_") -> {
                                                    proxmoxPatternEditAction = action
                                                    proxmoxPatternEditTypeInput = "subject"
                                                    proxmoxPatternEditValueInput = ""
                                                    patternDialogReturnAction = "settings_patterns_proxmox"
                                                    showProxmoxPatternEditDialog = true
                                                }
                                                action.startsWith("settings_mail_pattern_add") -> {
                                                    val parts = action.split("|")
                                                    mailPatternInputMode = parts.getOrNull(1)
                                                        ?.takeIf { it == "subject" || it == "fragments" }
                                                        ?: "subject"
                                                    mailPatternInputValue = parts.getOrNull(2).orEmpty()
                                                    returnToMailPatternsDialog = false
                                                    showMailPatternAddDialog = true
                                                }
                                                action.startsWith("settings_mail_pattern_edit_") -> {
                                                    mailPatternEditAction = action
                                                    mailPatternEditValueInput = ""
                                                    returnToMailPatternsDialog = false
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
                                            val isDatabasePattern = proxmoxPatternCategoryInput.equals("database", ignoreCase = true)
                                            val hintText = if (isDatabasePattern) {
                                                "Подсказка: для БД укажи category=database, type=subject, а в «Паттерн» — часть темы письма с бэкапом (например: my_db_prod)."
                                            } else {
                                                "Подсказка: для Proxmox укажи category=proxmox, type=subject, а в «Паттерн» — часть темы письма (например: vzdump backup status)."
                                            }
                                            Text(
                                                text = hintText,
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant
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

                            if (showProxmoxPatternEditDialog) {
                                AlertDialog(
                                    onDismissRequest = { showProxmoxPatternEditDialog = false },
                                    title = { Text("✏️ Редактировать паттерн") },
                                    text = {
                                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            OutlinedTextField(
                                                value = proxmoxPatternEditTypeInput,
                                                onValueChange = { proxmoxPatternEditTypeInput = it },
                                                label = { Text("Новый тип") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                            OutlinedTextField(
                                                value = proxmoxPatternEditValueInput,
                                                onValueChange = { proxmoxPatternEditValueInput = it },
                                                label = { Text("Новый паттерн") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
                                        }
                                    },
                                    confirmButton = {
                                        TextButton(
                                            onClick = {
                                                val actionPayload = proxmoxPatternEditAction + "|" +
                                                    Uri.encode(proxmoxPatternEditTypeInput.trim()) + "|" +
                                                    Uri.encode(proxmoxPatternEditValueInput.trim())
                                                onExtensionsSettingsAction(actionPayload)
                                                showProxmoxPatternEditDialog = false
                                            },
                                            enabled = proxmoxPatternEditAction.isNotBlank() &&
                                                proxmoxPatternEditTypeInput.isNotBlank() &&
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
                                            Text(
                                                text = if (mailPatternInputMode == "subject") {
                                                    "Подсказка: вставь тему реального письма с успешным бэкапом — приложение само соберёт regex (например: Backup completed for mail.example.com 120GB)."
                                                } else {
                                                    "Подсказка: укажи 2–4 устойчивых фрагмента через ; или , (например: backup completed;mail.example.com;120GB)."
                                                },
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant
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
                                                    if (returnToMailPatternsDialog) {
                                                        onExtensionsSettingsAction("settings_patterns_mail")
                                                        showMailPatternsDialog = true
                                                        returnToMailPatternsDialog = false
                                                    }
                                                    showMailPatternAddDialog = false
                                                },
                                                enabled = mailPatternInputValue.isNotBlank()
                                            ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = {
                                            showMailPatternAddDialog = false
                                            if (returnToMailPatternsDialog) {
                                                showMailPatternsDialog = true
                                                returnToMailPatternsDialog = false
                                            }
                                        }) {
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
                                                    if (returnToMailPatternsDialog) {
                                                        onExtensionsSettingsAction("settings_patterns_mail")
                                                        showMailPatternsDialog = true
                                                        returnToMailPatternsDialog = false
                                                    }
                                                    showMailPatternEditDialog = false
                                                },
                                                enabled = mailPatternEditAction.isNotBlank() &&
                                                    mailPatternEditValueInput.isNotBlank()
                                        ) {
                                            Text("Сохранить")
                                        }
                                    },
                                    dismissButton = {
                                        TextButton(onClick = {
                                            showMailPatternEditDialog = false
                                            if (returnToMailPatternsDialog) {
                                                showMailPatternsDialog = true
                                                returnToMailPatternsDialog = false
                                            }
                                        }) {
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
                                    title = {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text("➕ Добавить категорию БД", modifier = Modifier.weight(1f))
                                            IconButton(onClick = { showDbCategoryAddDialog = false }) {
                                                Icon(
                                                    imageVector = Icons.Filled.Close,
                                                    contentDescription = "Закрыть окно добавления категории БД"
                                                )
                                            }
                                        }
                                    },
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
                                    title = {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text(
                                                if (dbEntryAddCategory.isNotBlank()) {
                                                    "➕ Добавить БД в ${dbEntryAddCategory.uppercase()}"
                                                } else {
                                                    "➕ Добавить БД"
                                                },
                                                modifier = Modifier.weight(1f)
                                            )
                                            IconButton(onClick = { showDbEntryAddDialog = false }) {
                                                Icon(
                                                    imageVector = Icons.Filled.Close,
                                                    contentDescription = "Закрыть окно добавления БД"
                                                )
                                            }
                                        }
                                    },
                                    text = {
                                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            OutlinedTextField(
                                                value = dbEntryAddCategory,
                                                onValueChange = { dbEntryAddCategory = it },
                                                label = { Text("Категория БД") },
                                                modifier = Modifier.fillMaxWidth()
                                            )
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
                                    title = {
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween,
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Text("✏️ Редактировать БД", modifier = Modifier.weight(1f))
                                            IconButton(onClick = { showDbEntryEditDialog = false }) {
                                                Icon(
                                                    imageVector = Icons.Filled.Close,
                                                    contentDescription = "Закрыть окно редактирования БД"
                                                )
                                            }
                                        }
                                    },
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
                                    Column(modifier = Modifier.padding(8.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
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
                                                onClick = { serverDeleteConfirmTargetKey = server.ip },
                                                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                                            ) { Text("Удал.") }
                                        }
                                    }
                                }
                            }
                        }
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
        val isResourceCheckMode = showServerResourcesMenu
        AlertDialog(
            onDismissRequest = {
                showServerAvailabilityDialog = false
                showServerResourcesMenu = false
                showServerResourcesDetailsDialog = false
            },
            title = {
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.Top
                    ) {
                        Text(
                            text = if (isResourceCheckMode) {
                                "Точечная проверка ресурсов"
                            } else {
                                "Точечная проверка серверов"
                            },
                            modifier = Modifier.weight(1f)
                        )
                        Column(horizontalAlignment = Alignment.End) {
                            IconButton(
                                onClick = {
                                    showServerAvailabilityDialog = false
                                    showServerResourcesMenu = false
                                    showServerResourcesDetailsDialog = false
                                },
                                modifier = Modifier
                                    .padding(bottom = 2.dp)
                                    .height(30.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Close,
                                    contentDescription = "Закрыть окно точечной проверки"
                                )
                            }
                            if (isResourceCheckMode) {
                                IconButton(
                                    onClick = {
                                        onExtensionsSettingsAction("settings_resources")
                                        showResourceSettingsDialog = true
                                    },
                                    modifier = Modifier
                                        .padding(bottom = 2.dp)
                                        .height(30.dp)
                                ) {
                                    Icon(
                                        imageVector = Icons.Filled.Settings,
                                        contentDescription = "Открыть настройки ресурсов"
                                    )
                                }
                            }
                            IconButton(
                                onClick = {
                                    onCancelServerEdit()
                                    showServerAddDialog = true
                                },
                                modifier = Modifier.height(30.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Add,
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
                        .heightIn(max = 520.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    if (serverButtonsForDialog.isEmpty()) {
                        Text("Серверы для выбранного фильтра не найдены.")
                    } else {
                        val longTapHint = if (isResourceCheckMode) {
                            "Долгий тап по плашке хоста — настройки (редактировать / вкл-выкл / удалить)"
                        } else {
                            "Долгий тап по плашке хоста - настройки\n(редактировать / вкл-выкл / удалить)"
                        }
                        Text(
                            text = longTapHint,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalArrangement = Arrangement.spacedBy(6.dp),
                            maxItemsInEachRow = 2
                        ) {
                            serverButtonsForDialog.forEach { server ->
                                val serverTarget = if (server.ip.isNotBlank()) server.ip else server.name
                                val isServerEnabled = server.enabled == true
                                val availabilityStatus = listOf(server.ip, server.name)
                                    .asSequence()
                                    .map(::normalizeServerLookupToken)
                                    .firstNotNullOfOrNull { token -> availabilityStatusByToken[token] }
                                val availabilityMarker = resolveAvailabilityMarker(availabilityStatus)
                                val monitoringMarkerColor = if (isServerEnabled) {
                                    Color(0xFF2E7D32)
                                } else {
                                    Color(0xFF9E9E9E)
                                }
                                val isHostUnavailable = availabilityMarker == "🔴"
                                val serverMessage = if (
                                    state.message.isNotBlank() &&
                                    state.messageSource == (if (isResourceCheckMode) "server_resources" else "server_availability") &&
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
                                            onClick = {
                                                if (isResourceCheckMode) {
                                                    val targetTitle = server.name.ifBlank { server.ip }.ifBlank { "Сервер" }
                                                    serverResourceDetailsTargetKey = serverTarget.trim()
                                                    serverResourceDetailsTitle = targetTitle
                                                    showServerResourcesDetailsDialog = true
                                                    onCheckServerResources(server)
                                                } else {
                                                    onCheckServerAvailability(server)
                                                }
                                            },
                                            onLongClick = {
                                                serverActionsTargetKey = serverTarget.trim()
                                            }
                                        ),
                                    tonalElevation = 2.dp,
                                    shape = RoundedCornerShape(10.dp),
                                    color = if (isHostUnavailable) {
                                        MaterialTheme.colorScheme.errorContainer
                                    } else {
                                        MaterialTheme.colorScheme.tertiaryContainer
                                    }
                                ) {
                                    Column(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(horizontal = 8.dp, vertical = 6.dp),
                                        verticalArrangement = Arrangement.spacedBy(2.dp)
                                    ) {
                                        Row(
                                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                                            verticalAlignment = Alignment.CenterVertically
                                        ) {
                                            Spacer(
                                                modifier = Modifier
                                                    .size(10.dp)
                                                    .clip(CircleShape)
                                                    .background(monitoringMarkerColor)
                                            )
                                            Text(
                                                text = "${server.name.ifBlank { server.ip }}",
                                                fontSize = 12.sp,
                                                maxLines = 1,
                                                overflow = TextOverflow.Ellipsis,
                                                fontWeight = FontWeight.SemiBold
                                            )
                                        }
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


    if (showResourceThresholdDialog) {
        AlertDialog(
            onDismissRequest = { showResourceThresholdDialog = false },
            title = { Text(resourceThresholdLabel.ifBlank { "Изменить порог ресурса" }) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = "Текущее значение: ${resourceThresholdCurrentValue?.let { "$it%" } ?: "не задано"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    OutlinedTextField(
                        value = resourceThresholdValueInput,
                        onValueChange = { input ->
                            resourceThresholdValueInput = input.filter { it.isDigit() }.take(3)
                        },
                        label = { Text("Порог в % (0-100)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                val thresholdValue = resourceThresholdValueInput.toIntOrNull()
                TextButton(
                    onClick = {
                        val actionPayload = "${resourceThresholdAction}|$thresholdValue"
                        if (thresholdValue != null && resourceThresholdAction.isNotBlank()) {
                            resourceThresholdOverrides =
                                resourceThresholdOverrides + (resourceThresholdAction to thresholdValue)
                        }
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

    if (showResourceSettingsDialog) {
        val resourceThresholdGroups = listOf(
            Triple("CPU", "set_cpu_warning", "set_cpu_critical"),
            Triple("RAM", "set_ram_warning", "set_ram_critical"),
            Triple("Disk", "set_disk_warning", "set_disk_critical")
        )
        fun currentThresholdValue(action: String, defaultValue: Int): Int {
            return resourceThresholdOverrides[action]
                ?: extractResourceThresholdValue(state.extensionSettingsMenuOptions, action)
                ?: extractResourceThresholdValueFromMessage(state.message, action)
                ?: defaultValue
        }
        val cpuWarningValue = currentThresholdValue("set_cpu_warning", 80)
        val cpuCriticalValue = currentThresholdValue("set_cpu_critical", 90)
        val ramWarningValue = currentThresholdValue("set_ram_warning", 85)
        val ramCriticalValue = currentThresholdValue("set_ram_critical", 95)
        val diskWarningValue = currentThresholdValue("set_disk_warning", 80)
        val diskCriticalValue = currentThresholdValue("set_disk_critical", 90)
        AlertDialog(
            onDismissRequest = { showResourceSettingsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Параметры проверки ресурсов", modifier = Modifier.weight(1f))
                    IconButton(
                        onClick = { showResourceSettingsDialog = false },
                        modifier = Modifier.height(30.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть параметры проверки ресурсов"
                        )
                    }
                }
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        "Текущие параметры:",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = buildString {
                            append("• CPU предупреждение: ").append(cpuWarningValue).append("%\n")
                            append("• CPU критический: ").append(cpuCriticalValue).append("%\n")
                            append("• RAM предупреждение: ").append(ramWarningValue).append("%\n")
                            append("• RAM критический: ").append(ramCriticalValue).append("%\n")
                            append("• Disk предупреждение: ").append(diskWarningValue).append("%\n")
                            append("• Disk критический: ").append(diskCriticalValue).append("%")
                        },
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        "Выберите параметр и задайте новое значение в процентах.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    resourceThresholdGroups.forEach { (resourceName, warningAction, criticalAction) ->
                        ElevatedCard(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.elevatedCardColors(
                                containerColor = MaterialTheme.colorScheme.surfaceContainerHighest
                            )
                        ) {
                            Column(
                                modifier = Modifier.padding(10.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Text(
                                    text = resourceName,
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.SemiBold
                                )
                                val currentWarningValue = currentThresholdValue(
                                    warningAction,
                                    when (warningAction) {
                                        "set_cpu_warning" -> 80
                                        "set_ram_warning" -> 85
                                        else -> 80
                                    }
                                )
                                val currentCriticalValue = currentThresholdValue(
                                    criticalAction,
                                    when (criticalAction) {
                                        "set_cpu_critical" -> 90
                                        "set_ram_critical" -> 95
                                        else -> 90
                                    }
                                )
                                Text(
                                    text = "Текущие: предупреждение ${currentWarningValue}%, " +
                                        "критический ${currentCriticalValue}%",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                                ) {
                                    OutlinedButton(
                                        onClick = {
                                            resourceThresholdAction = warningAction
                                            resourceThresholdLabel = "$resourceName: предупреждение"
                                            resourceThresholdValueInput = ""
                                            resourceThresholdCurrentValue = currentWarningValue
                                            showResourceThresholdDialog = true
                                            showResourceSettingsDialog = false
                                        },
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("Предупреждение")
                                    }
                                    OutlinedButton(
                                        onClick = {
                                            resourceThresholdAction = criticalAction
                                            resourceThresholdLabel = "$resourceName: критический"
                                            resourceThresholdValueInput = ""
                                            resourceThresholdCurrentValue = currentCriticalValue
                                            showResourceThresholdDialog = true
                                            showResourceSettingsDialog = false
                                        },
                                        modifier = Modifier.weight(1f)
                                    ) {
                                        Text("Критический")
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

    if (showServerResourcesDetailsDialog) {
        val isCurrentServerLoading =
            state.isLoading &&
                state.availabilityServerMessageTarget == serverResourceDetailsTargetKey
        val resourceMessage = if (
            state.messageSource == "server_resources" &&
            state.availabilityServerMessageTarget == serverResourceDetailsTargetKey
        ) {
            state.message
        } else {
            ""
        }
        AlertDialog(
            onDismissRequest = { showServerResourcesDetailsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Ресурсы: $serverResourceDetailsTitle",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = { showServerResourcesDetailsDialog = false }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть окно ресурсов"
                        )
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 360.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    if (isCurrentServerLoading) {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                        Text("Запрашиваю данные по ресурсам…")
                    }

                    if (resourceMessage.isNotBlank()) {
                        Text(resourceMessage)
                    } else if (!isCurrentServerLoading) {
                        Text(
                            "Тапни по карточке сервера ещё раз, если нужно обновить данные.",
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            },
            confirmButton = {}
        )
    }




    if (showMorningReportDialog) {
        AlertDialog(
            onDismissRequest = { showMorningReportDialog = false },
            title = {
                Text("🌅 Утренний отчет", fontWeight = FontWeight.Bold)
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 520.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    if (state.morningReportText.isNotBlank()) {
                        Text(state.morningReportText)
                        if (state.morningReportReceivedAt.isNotBlank()) {
                            Text("Получен: ${state.morningReportReceivedAt}")
                        }
                    } else {
                        Text("Формируем утренний отчет…")
                    }
                    if (state.messageSource == "morning_report" && state.message.isNotBlank()) {
                        Text(state.message)
                    }
                }
            },
            confirmButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (state.morningReportUnread) {
                        TextButton(onClick = {
                            onMarkMorningReportRead()
                            showMorningReportDialog = false
                        }) {
                            Text("Прочитано")
                        }
                    }
                    TextButton(onClick = { showMorningReportDialog = false }) {
                        Text("Закрыть")
                    }
                }
            }
        )
    }

    if (showMailBackupsDialog) {
        AlertDialog(
            onDismissRequest = { showMailBackupsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "📬 Бэкапы почтового сервера",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row {
                        IconButton(
                            onClick = {
                                showMailBackupsDialog = false
                                onExtensionsSettingsAction("settings_patterns_mail")
                                showMailPatternsDialog = true
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = "Открыть настройки паттернов почты"
                            )
                        }
                        IconButton(onClick = { showMailBackupsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть окно бэкапов почты"
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
                    if (state.isLoading && state.mailBackupHistoryItems.isEmpty()) {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                        Text("Загружаем бэкапы почтового сервера…")
                    } else if (state.mailBackupHistoryItems.isNotEmpty()) {
                        val title = state.mailBackupHistoryTitle.trim()
                        if (title.isNotBlank()) {
                            Text(
                                text = title,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        state.mailBackupHistoryItems.forEach { item ->
                            ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                Column(
                                    modifier = Modifier.padding(10.dp),
                                    verticalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    Text(
                                        text = "${item.statusIcon} ${item.size}",
                                        fontWeight = FontWeight.SemiBold
                                    )
                                    Text(
                                        text = item.path,
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                    Text(
                                        text = item.relativeTime,
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                        }
                    } else {
                        Text("Список бэкапов пока пуст.")
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

    if (showProxmoxBackupStatsDialog && selectedDatabaseBackupLabel.isNotBlank()) {
        AlertDialog(
            onDismissRequest = { showProxmoxBackupStatsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "📈 Статистика: $selectedDatabaseBackupLabel",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row {
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

    if (showProxmoxServerAddDialog) {
        AlertDialog(
            onDismissRequest = { showProxmoxServerAddDialog = false },
            title = { Text("➕ Добавить сервер бэкапа Proxmox") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = proxmoxServerNameInput,
                        onValueChange = { proxmoxServerNameInput = it },
                        label = { Text("Имя сервера") },
                        placeholder = { Text("например pve-01") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Text(
                        "После подтверждения откроется backend-действие добавления хоста.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            },
            confirmButton = {
                    TextButton(
                    onClick = {
                        val hostName = proxmoxServerNameInput.trim()
                        val actionPayload = "settings_proxmox_add|" + Uri.encode(hostName)
                        onExtensionsSettingsAction(actionPayload)
                        showProxmoxServerAddDialog = false
                        proxmoxServerNameInput = ""
                    },
                    enabled = proxmoxServerNameInput.trim().isNotBlank()
                ) {
                    Text("Добавить")
                }
            },
            dismissButton = {
                TextButton(onClick = { showProxmoxServerAddDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showDbOpsEntryAddDialog) {
        AlertDialog(
            onDismissRequest = { showDbOpsEntryAddDialog = false },
            title = { Text("➕ Добавить БД") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = dbEntryAddCategory,
                        onValueChange = { dbEntryAddCategory = it },
                        label = { Text("Категория БД") },
                        modifier = Modifier.fillMaxWidth()
                    )
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
                TextButton(
                    onClick = {
                        val category = dbEntryAddCategory.trim()
                        val key = dbEntryAddKeyInput.trim()
                        val name = dbEntryAddNameInput.trim()
                        if (category.isNotBlank() && key.isNotBlank()) {
                            onExtensionsSettingsAction(
                                "settings_db_add_db_submit|${Uri.encode(category)}|${Uri.encode(key)}|${Uri.encode(name)}"
                            )
                            onAction("backup_databases")
                        }
                        showDbOpsEntryAddDialog = false
                    },
                    enabled = dbEntryAddCategory.trim().isNotBlank() && dbEntryAddKeyInput.trim().isNotBlank()
                ) {
                    Text("Добавить")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDbOpsEntryAddDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showZfsStatusesDialog) {
        AlertDialog(
            onDismissRequest = { showZfsStatusesDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🧊 Статусы ZFS",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            zfsHostInput = ""
                            showZfsHostAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить новый ZFS-хост"
                            )
                        }
                        IconButton(onClick = {
                            showZfsPatternsDialog = true
                            onExtensionsSettingsAction("settings_patterns_zfs")
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = "Открыть настройки паттернов ZFS"
                            )
                        }
                        IconButton(onClick = { showZfsStatusesDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть окно статусов ZFS"
                            )
                        }
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 520.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(2.dp)
                ) {
                    val zfsMenuOptions = if (state.extensionMenuAction == "zfs_menu") {
                        state.extensionMenuOptions
                    } else {
                        emptyList()
                    }
                    val zfsSettingsOptions = state.zfsHostMenuOptions
                    val statusCardsFromOptions = zfsMenuOptions.mapNotNull { option -> toZfsStatusCardItem(option) }
                    val statusCardsFromMessage = parseZfsStatusCardsFromMessage(state.zfsStatusMessage)
                    val rawMessage = state.zfsStatusMessage.trim()

                    val zfsActions = zfsMenuOptions
                        .mapNotNull { option ->
                            val action = resolveMenuOptionAction(option)
                            val label = option.label?.trim().orEmpty()
                            if (label.isBlank() || action.isBlank()) return@mapNotNull null
                            if (action.startsWith("settings_zfs")) return@mapNotNull null
                            if (toZfsStatusCardItem(option) != null) return@mapNotNull null
                            label to action
                        }
                        .distinctBy { (_, action) -> action }

                    val groupedCards = linkedMapOf<String, MutableList<ZfsPoolStatusItem>>()
                    val actionByHost = linkedMapOf<String, String?>()
                    val hasProblemByHost = linkedMapOf<String, Boolean>()
                    val monitoringEnabledByHost = linkedMapOf<String, Boolean>()
                    (statusCardsFromMessage + statusCardsFromOptions).forEach { card ->
                        val host = card.hostName.trim()
                        if (host.isBlank()) return@forEach
                        groupedCards.getOrPut(host) { mutableListOf() }.addAll(card.pools)
                        if (actionByHost[host].isNullOrBlank() && !card.action.isNullOrBlank()) {
                            actionByHost[host] = card.action
                        }
                        hasProblemByHost[host] = hasProblemByHost[host] == true || card.hasProblem || card.pools.any { it.hasProblem }
                        if (card.monitoringEnabled != null && !monitoringEnabledByHost.containsKey(host)) {
                            monitoringEnabledByHost[host] = card.monitoringEnabled
                        }
                    }

                    val zfsSettingsPairs = zfsSettingsOptions
                        .mapNotNull { option ->
                            val action = resolveMenuOptionAction(option)
                            val label = option.label?.trim().orEmpty()
                            if (label.isBlank() || action.isBlank()) null else label to action
                        }
                    val zfsHostGroups = extractZfsHostOptionGroups(zfsSettingsPairs)
                    val monitoringByHost = zfsHostGroups.associateBy { it.hostName.trim().lowercase() }

                    val allHostsOrdered = linkedSetOf<String>()
                    groupedCards.keys.forEach { host ->
                        val normalized = host.trim()
                        if (normalized.isNotBlank()) allHostsOrdered.add(normalized)
                    }
                    zfsHostGroups.forEach { group ->
                        val normalized = group.hostName.trim()
                        if (normalized.isNotBlank()) allHostsOrdered.add(normalized)
                    }

                    val allStatusCards = allHostsOrdered.map { host ->
                        val pools = groupedCards[host].orEmpty()
                        val hostGroup = monitoringByHost[host.trim().lowercase()]
                        val poolsWithUniqueState = pools.distinctBy { pool ->
                            "${pool.poolName}|${pool.rawState}|${pool.rawTimestamp}"
                        }
                        val monitoringEnabled = hostGroup?.let { !isZfsMonitoringDisabled(it.toggleLabel) }
                            ?: monitoringEnabledByHost[host]
                        ZfsStatusCardItem(
                            hostName = host,
                            pools = poolsWithUniqueState,
                            action = actionByHost[host],
                            rawLabel = hostGroup?.toggleLabel.orEmpty(),
                            hasProblem = hasProblemByHost[host] == true,
                            monitoringEnabled = monitoringEnabled,
                            monitoringLabel = hostGroup?.toggleLabel.orEmpty()
                        )
                    }

                    val hasAnyData = allStatusCards.isNotEmpty() || rawMessage.isNotBlank() || zfsActions.isNotEmpty()

                    if (state.isLoading && !hasAnyData) {
                        Text("Загружаем ZFS-центр…")
                    } else if (!hasAnyData) {
                        Text("Пока нет данных от ZFS. Нажми «Обновить», чтобы запросить статусы.")
                        Button(onClick = { onAction("zfs_menu") }) { Text("Обновить") }
                    } else {
                        if (allStatusCards.isNotEmpty()) {
                            Text(
                                text = "Хосты ZFS: ${resolveZfsHostsCount(state.zfsStatusMessage, allStatusCards.size, zfsSettingsOptions)}",
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                text = "Долгий тап по плашке хоста — настройки (редактировать / вкл-выкл / удалить)",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            FlowRow(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                                maxItemsInEachRow = 2
                            ) {
                                allStatusCards.forEach { card ->
                                    Box(modifier = Modifier.fillMaxWidth(0.48f)) {
                                        ZfsStatusTile(
                                            card = card,
                                            onClick = {
                                                val hostGroup = monitoringByHost[card.hostName.trim().lowercase()]
                                                if (hostGroup != null) {
                                                    zfsSelectedHostName = hostGroup.hostName
                                                    zfsSelectedHostEditAction = hostGroup.editAction
                                                    zfsSelectedHostDeleteAction = hostGroup.deleteAction
                                                    zfsSelectedHostToggleAction = hostGroup.toggleAction
                                                    showZfsHostActionsDialog = true
                                                } else {
                                                    pendingZfsHostSettingsName = card.hostName
                                                    onExtensionsSettingsAction("settings_zfs_list")
                                                }
                                            },
                                            onLongClick = {
                                                val hostGroup = monitoringByHost[card.hostName.trim().lowercase()]
                                                if (hostGroup != null) {
                                                    zfsSelectedHostName = hostGroup.hostName
                                                    zfsSelectedHostEditAction = hostGroup.editAction
                                                    zfsSelectedHostDeleteAction = hostGroup.deleteAction
                                                    zfsSelectedHostToggleAction = hostGroup.toggleAction
                                                    showZfsHostActionsDialog = true
                                                } else {
                                                    pendingZfsHostSettingsName = card.hostName
                                                    onExtensionsSettingsAction("settings_zfs_list")
                                                }
                                            }
                                        )
                                    }
                                }
                            }
                        }

                        if (zfsActions.isNotEmpty()) {
                            Text(
                                text = "Быстрые действия",
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.SemiBold
                            )
                            zfsActions.forEach { (label, action) ->
                                OutlinedButton(
                                    onClick = { onAction(action) },
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(label)
                                }
                            }
                        }

                        if (rawMessage.isNotBlank() && allStatusCards.isEmpty()) {
                            Text(formatZfsMessageForDialog(rawMessage))
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showZfsSettingsDialog) {
        AlertDialog(
            onDismissRequest = { showZfsSettingsDialog = false },
            title = { Text("⚙️ Настройки ZFS") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        text = "Выбери раздел настроек.",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Button(
                        onClick = {
                            showZfsSettingsDialog = false
                            showZfsHostsSettingsDialog = true
                            onExtensionsSettingsAction("settings_zfs_list")
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Хосты")
                    }
                    Button(
                        onClick = {
                            showZfsSettingsDialog = false
                            showZfsPatternsDialog = true
                            onExtensionsSettingsAction("settings_patterns_zfs")
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Паттерны")
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { showZfsSettingsDialog = false }) {
                    Text("Закрыть")
                }
            }
        )
    }

    if (showZfsHostDetailsDialog) {
        AlertDialog(
            onDismissRequest = { showZfsHostDetailsDialog = false },
            title = { Text("ℹ️ ${zfsDetailsHostName.ifBlank { "Данные ZFS" }}") },
            text = {
                Text(
                    text = when {
                        state.isLoading && zfsStatusDetailsFallbackText.isBlank() -> "Запрашиваем сведения по хосту…"
                        zfsStatusDetailsFallbackText.isNotBlank() -> zfsStatusDetailsFallbackText
                        state.zfsStatusMessage.isNotBlank() -> formatZfsMessageForDialog(state.zfsStatusMessage.trim())
                        else -> "Данные по хосту пока не получены."
                    },
                    lineHeight = 16.sp
                )
            },
            confirmButton = {
                TextButton(onClick = { showZfsHostDetailsDialog = false }) {
                    Text("Ок")
                }
            }
        )
    }

    if (showZfsHostsSettingsDialog) {
        AlertDialog(
            onDismissRequest = { showZfsHostsSettingsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "⚙️ Настройки хостов ZFS",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = { showZfsHostsSettingsDialog = false }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть окно настроек хостов ZFS"
                        )
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 460.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    val zfsSettingsOptions = if (state.extensionSettingsMenuAction == "settings_zfs_list") {
                        state.extensionSettingsMenuOptions
                    } else {
                        emptyList()
                    }

                    if (state.isLoading && zfsSettingsOptions.isEmpty()) {
                        Text("Загружаем настройки хостов ZFS…")
                    } else if (zfsSettingsOptions.isEmpty()) {
                        Text("Настройки хостов ZFS пока недоступны.")
                    } else {
                        val zfsMenuPairs = zfsSettingsOptions
                            .mapNotNull { option ->
                                val action = resolveMenuOptionAction(option)
                                val label = option.label?.trim().orEmpty()
                                if (label.isBlank() || action.isBlank()) null else label to action
                            }
                        val zfsHostGroups = extractZfsHostOptionGroups(zfsMenuPairs)
                        val hostActions = zfsHostGroups.flatMap { group ->
                            listOf(group.editAction, group.deleteAction, group.toggleAction)
                        }.toSet()
                        val commonActions = zfsMenuPairs.filterNot { (_, action) ->
                            hostActions.contains(action)
                        }

                        if (zfsHostGroups.isEmpty()) {
                            Text("Список хостов пуст.")
                        } else {
                            Text(
                                text = "Хосты",
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                text = "Долгий тап по карточке хоста открывает управление.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            zfsHostGroups.forEach { hostGroup ->
                                ElevatedCard(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clip(RoundedCornerShape(12.dp))
                                        .combinedClickable(
                                            onClick = { },
                                            onLongClick = {
                                                zfsSelectedHostName = hostGroup.hostName
                                                zfsSelectedHostEditAction = hostGroup.editAction
                                                zfsSelectedHostDeleteAction = hostGroup.deleteAction
                                                zfsSelectedHostToggleAction = hostGroup.toggleAction
                                                showZfsHostActionsDialog = true
                                            }
                                        )
                                ) {
                                    Column(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(horizontal = 12.dp, vertical = 10.dp),
                                        verticalArrangement = Arrangement.spacedBy(2.dp)
                                    ) {
                                        Text(
                                            text = hostGroup.hostName,
                                            fontWeight = FontWeight.SemiBold
                                        )
                                        Text(
                                            text = hostGroup.toggleLabel,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = if (hostGroup.toggleLabel.startsWith("✅")) {
                                                MaterialTheme.colorScheme.primary
                                            } else {
                                                MaterialTheme.colorScheme.onSurfaceVariant
                                            }
                                        )
                                    }
                                }
                            }
                        }

                        commonActions.forEach { (label, action) ->
                            Button(
                                onClick = {
                                    if (action == "settings_zfs_add") {
                                        zfsHostInput = ""
                                        showZfsHostAddDialog = true
                                    } else {
                                        onExtensionsSettingsAction(action)
                                    }
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(label)
                            }
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showZfsHostActionsDialog) {
        AlertDialog(
            onDismissRequest = { showZfsHostActionsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("⚙️ ${zfsSelectedHostName.ifBlank { "Хост ZFS" }}")
                    IconButton(onClick = { showZfsHostActionsDialog = false }) {
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
                                val action = zfsSelectedHostEditAction
                                if (action.startsWith("settings_zfs_edit_name_")) {
                                    val raw = action.removePrefix("settings_zfs_edit_name_")
                                    zfsHostEditAction = "settings_zfs_edit_name_$raw"
                                    zfsHostEditCurrentName = Uri.decode(raw)
                                    zfsHostEditNewNameInput = zfsHostEditCurrentName
                                    showZfsHostEditDialog = zfsHostEditCurrentName.isNotBlank()
                                }
                                showZfsHostActionsDialog = false
                            },
                            enabled = zfsSelectedHostEditAction.isNotBlank()
                        ) {
                            Icon(Icons.Filled.Edit, contentDescription = "Переименовать")
                        }
                        Text("Изм.", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                onExtensionsSettingsAction(zfsSelectedHostToggleAction)
                                onExtensionsSettingsAction("settings_zfs_list")
                                showZfsHostActionsDialog = false
                            },
                            enabled = zfsSelectedHostToggleAction.isNotBlank()
                        ) {
                            Icon(Icons.Filled.PowerSettingsNew, contentDescription = "Вкл/выкл")
                        }
                        Text("Вкл/выкл", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                zfsHostDeleteConfirmName = zfsSelectedHostName
                                zfsHostDeleteConfirmAction = zfsSelectedHostDeleteAction
                                showZfsHostDeleteConfirmDialog = zfsHostDeleteConfirmAction.isNotBlank()
                            },
                            enabled = zfsSelectedHostDeleteAction.isNotBlank()
                        ) {
                            Icon(Icons.Filled.Delete, contentDescription = "Удалить")
                        }
                        Text("Удал.", style = MaterialTheme.typography.labelSmall)
                    }
                }
            },
            confirmButton = {},
            dismissButton = {}
        )
    }

    if (showZfsHostDeleteConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showZfsHostDeleteConfirmDialog = false },
            title = {
                Text("Удалить хост ZFS")
            },
            text = {
                Text("Подтвердите удаление хоста «${zfsHostDeleteConfirmName.ifBlank { zfsSelectedHostName }}».")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val action = zfsHostDeleteConfirmAction
                        if (action.isNotBlank()) {
                            onExtensionsSettingsAction(action)
                            onExtensionsSettingsAction("settings_zfs_list")
                        }
                        showZfsHostDeleteConfirmDialog = false
                        showZfsHostActionsDialog = false
                    }
                ) {
                    Text("Удалить")
                }
            },
            dismissButton = {
                TextButton(onClick = { showZfsHostDeleteConfirmDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showZfsPatternsDialog) {
        AlertDialog(
            onDismissRequest = { showZfsPatternsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🔍 Паттерны ZFS",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            patternDialogReturnAction = "settings_patterns_zfs"
                            proxmoxPatternCategoryInput = "zfs"
                            proxmoxPatternTypeInput = "subject"
                            proxmoxPatternValueInput = ""
                            showProxmoxPatternAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить паттерн ZFS"
                            )
                        }
                        IconButton(onClick = { showZfsPatternsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть список паттернов ZFS"
                            )
                        }
                    }
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 460.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    if (zfsPatternMenuAction == null) {
                        Text("Загружаем паттерны ZFS…")
                    } else if (zfsPatternOptionGroups.isEmpty()) {
                        Text("Паттерны пока не добавлены.")
                    } else {
                        zfsPatternOptionGroups.forEach { pattern ->
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(10.dp))
                                    .clickable {
                                        patternDialogReturnAction = "settings_patterns_zfs"
                                        selectedProxmoxPatternLabel = pattern.label
                                        selectedProxmoxPatternEditAction = pattern.editAction
                                        selectedProxmoxPatternDeleteAction = pattern.deleteAction
                                        showProxmoxPatternActionsDialog = true
                                    },
                                tonalElevation = 2.dp,
                                shape = RoundedCornerShape(10.dp),
                                color = MaterialTheme.colorScheme.secondaryContainer
                            ) {
                                Text(
                                    text = pattern.label,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                        }
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
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            proxmoxServerNameInput = ""
                            showProxmoxServerAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить новый сервер Proxmox в бэкапы"
                            )
                        }
                        IconButton(onClick = {
                            patternDialogReturnAction = "settings_patterns_proxmox"
                            onExtensionsSettingsAction("settings_patterns_proxmox")
                            showProxmoxPatternsDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = "Открыть паттерны Proxmox"
                            )
                        }
                        IconButton(onClick = { showProxmoxBackupsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть выбор бэкапа Proxmox"
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
                    if (state.extensionMenuAction != "backup_proxmox" || state.extensionMenuOptions.isEmpty()) {
                        Text("Загружаем список бэкапов Proxmox…")
                    } else {
                        Text(
                            text = "Долгий тап по плашке хоста - настройки\n(редактировать / вкл-выкл / удалить)",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            maxItemsInEachRow = 2
                        ) {
                            state.extensionMenuOptions.forEach { option ->
                                val targetAction = resolveMenuOptionAction(option)
                                val label = option.label?.trim().orEmpty().ifBlank {
                                    deriveDatabaseBackupLabelFromAction(targetAction)
                                }
                                if (label.isNotBlank() && targetAction.isNotBlank()) {
                                    val displayLabel = formatBackupLabelWithMonitorStatus(label, targetAction)
                                    val isMonitoringDisabled = isBackupMonitorDisabled(label, targetAction)
                                    val hasProblemForEnabledHost = !isMonitoringDisabled && isProblemBackupOption(label, targetAction)
                                    Surface(
                                        modifier = Modifier
                                            .weight(1f)
                                            .clip(RoundedCornerShape(10.dp))
                                            .combinedClickable(
                                                onClick = {
                                                    showProxmoxBackupsDialog = false
                                                    selectedProxmoxBackupLabel = label
                                                    showProxmoxBackupStatsDialog = true
                                                    onAction(targetAction)
                                                },
                                                onLongClick = {
                                                    val hostName = targetAction
                                                        .removePrefix("backup_host_")
                                                        .trim()
                                                    if (hostName.isNotBlank()) {
                                                        proxmoxHostActionsTargetKey = hostName
                                                    }
                                                }
                                            ),
                                        tonalElevation = 2.dp,
                                        shape = RoundedCornerShape(10.dp),
                                        color = if (hasProblemForEnabledHost) {
                                            MaterialTheme.colorScheme.errorContainer
                                        } else {
                                            MaterialTheme.colorScheme.tertiaryContainer
                                        }
                                    ) {
                                        Text(
                                            text = displayLabel,
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(horizontal = 10.dp, vertical = 8.dp),
                                            maxLines = 3,
                                            overflow = TextOverflow.Ellipsis,
                                            color = if (hasProblemForEnabledHost) {
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

    if (showProxmoxPatternsDialog) {
        AlertDialog(
            onDismissRequest = { showProxmoxPatternsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🔍 Паттерны Proxmox",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            patternDialogReturnAction = "settings_patterns_proxmox"
                            proxmoxPatternCategoryInput = "proxmox"
                            proxmoxPatternTypeInput = "subject"
                            proxmoxPatternValueInput = ""
                            showProxmoxPatternAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить паттерн Proxmox"
                            )
                        }
                        IconButton(onClick = { showProxmoxPatternsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть список паттернов Proxmox"
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
                    if (proxmoxPatternMenuAction == null) {
                        Text("Загружаем список паттернов Proxmox…")
                    } else if (proxmoxPatternOptionGroups.isEmpty()) {
                        Text("Паттерны пока не добавлены.")
                    } else {
                        proxmoxPatternOptionGroups.forEach { pattern ->
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(10.dp))
                                    .clickable {
                                        selectedProxmoxPatternLabel = pattern.label
                                        selectedProxmoxPatternEditAction = pattern.editAction
                                        selectedProxmoxPatternDeleteAction = pattern.deleteAction
                                        showProxmoxPatternActionsDialog = true
                                    },
                                tonalElevation = 2.dp,
                                shape = RoundedCornerShape(10.dp),
                                color = MaterialTheme.colorScheme.secondaryContainer
                            ) {
                                Text(
                                    text = pattern.label,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showProxmoxPatternActionsDialog) {
        AlertDialog(
            onDismissRequest = { showProxmoxPatternActionsDialog = false },
            title = { Text("Паттерн: ${selectedProxmoxPatternLabel.ifBlank { "без названия" }}") },
            text = { Text("Выбери действие для паттерна.") },
            confirmButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(
                        onClick = {
                            proxmoxPatternEditAction = selectedProxmoxPatternEditAction
                            val prefill = parseProxmoxPatternEditPrefill(selectedProxmoxPatternLabel)
                            proxmoxPatternEditTypeInput = prefill.patternType
                            proxmoxPatternEditValueInput = prefill.patternValue
                            showProxmoxPatternEditDialog = true
                            showProxmoxPatternActionsDialog = false
                        },
                        enabled = selectedProxmoxPatternEditAction.isNotBlank()
                    ) {
                        Text("Редактировать")
                    }
                    TextButton(
                        onClick = {
                            proxmoxPatternDeleteConfirmLabel = selectedProxmoxPatternLabel
                            proxmoxPatternDeleteConfirmAction = selectedProxmoxPatternDeleteAction
                            showProxmoxPatternActionsDialog = false
                        },
                        enabled = selectedProxmoxPatternDeleteAction.isNotBlank()
                    ) {
                        Text("Удалить")
                    }
                }
            },
            dismissButton = {
                TextButton(onClick = { showProxmoxPatternActionsDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (proxmoxPatternDeleteConfirmAction.isNotBlank()) {
        AlertDialog(
            onDismissRequest = {
                proxmoxPatternDeleteConfirmAction = ""
                proxmoxPatternDeleteConfirmLabel = ""
            },
            title = { Text("Подтвердить удаление") },
            text = { Text("Удалить паттерн «${proxmoxPatternDeleteConfirmLabel.ifBlank { "без названия" }}»?") },
            confirmButton = {
                TextButton(
                    onClick = {
                        onExtensionsSettingsAction(proxmoxPatternDeleteConfirmAction)
                        onExtensionsSettingsAction(patternDialogReturnAction)
                        proxmoxPatternDeleteConfirmAction = ""
                        proxmoxPatternDeleteConfirmLabel = ""
                    }
                ) {
                    Text("Удалить")
                }
            },
            dismissButton = {
                TextButton(
                    onClick = {
                        proxmoxPatternDeleteConfirmAction = ""
                        proxmoxPatternDeleteConfirmLabel = ""
                    }
                ) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showProxmoxPatternAddDialog && settingsSection != "extensions") {
        AlertDialog(
            onDismissRequest = { showProxmoxPatternAddDialog = false },
            title = {
                Text(
                    if (proxmoxPatternCategoryInput.equals("database", ignoreCase = true)) {
                        "➕ Добавить паттерн БД"
                    } else {
                        "➕ Добавить паттерн Proxmox"
                    }
                )
            },
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
                    val isDatabasePattern = proxmoxPatternCategoryInput.equals("database", ignoreCase = true)
                    val hintText = if (isDatabasePattern) {
                        "Подсказка: для БД укажи category=database, type=subject, а в «Паттерн» — часть темы письма с бэкапом (например: my_db_prod)."
                    } else {
                        "Подсказка: для Proxmox укажи category=proxmox, type=subject, а в «Паттерн» — часть темы письма (например: vzdump backup status)."
                    }
                    Text(
                        text = hintText,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
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
                        onExtensionsSettingsAction(patternDialogReturnAction)
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

    if (showProxmoxPatternEditDialog && settingsSection != "extensions") {
        AlertDialog(
            onDismissRequest = { showProxmoxPatternEditDialog = false },
            title = { Text("✏️ Редактировать паттерн") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = proxmoxPatternEditTypeInput,
                        onValueChange = { proxmoxPatternEditTypeInput = it },
                        label = { Text("Новый тип") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = proxmoxPatternEditValueInput,
                        onValueChange = { proxmoxPatternEditValueInput = it },
                        label = { Text("Новый паттерн") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val actionPayload = proxmoxPatternEditAction + "|" +
                            Uri.encode(proxmoxPatternEditTypeInput.trim()) + "|" +
                            Uri.encode(proxmoxPatternEditValueInput.trim())
                        onExtensionsSettingsAction(actionPayload)
                        onExtensionsSettingsAction(patternDialogReturnAction)
                        showProxmoxPatternEditDialog = false
                    },
                    enabled = proxmoxPatternEditAction.isNotBlank() &&
                        proxmoxPatternEditTypeInput.isNotBlank() &&
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

    if (showMailPatternsDialog) {
        AlertDialog(
            onDismissRequest = { showMailPatternsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🔍 Паттерны бэкапов почты",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            mailPatternInputMode = "subject"
                            mailPatternInputValue = ""
                            returnToMailPatternsDialog = true
                            showMailPatternsDialog = false
                            showMailPatternAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить паттерн почты"
                            )
                        }
                        IconButton(onClick = { showMailPatternsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть список паттернов почты"
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
                    if (mailPatternMenuAction == null) {
                        Text("Загружаем список паттернов почтовых бэкапов…")
                    } else if (mailPatternOptionGroups.isEmpty()) {
                        Text("Паттерны почты пока не добавлены.")
                    } else {
                        Text(
                            text = "mail",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        mailPatternOptionGroups.forEach { pattern ->
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(10.dp))
                                    .clickable {
                                        selectedMailPatternLabel = pattern.label
                                        selectedMailPatternEditAction = pattern.editAction
                                        selectedMailPatternDeleteAction = pattern.deleteAction
                                        showMailPatternActionsDialog = true
                                    },
                                tonalElevation = 2.dp,
                                shape = RoundedCornerShape(10.dp),
                                color = MaterialTheme.colorScheme.secondaryContainer
                            ) {
                                Text(
                                    text = pattern.label,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showMailPatternActionsDialog) {
        AlertDialog(
            onDismissRequest = { showMailPatternActionsDialog = false },
            title = { Text("Паттерн: ${selectedMailPatternLabel.ifBlank { "без названия" }}") },
            text = { Text("Выбери действие для паттерна.") },
            confirmButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(
                        onClick = {
                            mailPatternEditAction = selectedMailPatternEditAction
                            mailPatternEditValueInput = parseMailPatternEditValue(selectedMailPatternLabel)
                            returnToMailPatternsDialog = true
                            showMailPatternsDialog = false
                            showMailPatternEditDialog = true
                            showMailPatternActionsDialog = false
                        },
                        enabled = selectedMailPatternEditAction.isNotBlank()
                    ) {
                        Text("Редактировать")
                    }
                    TextButton(
                        onClick = {
                            onExtensionsSettingsAction(selectedMailPatternDeleteAction)
                            onExtensionsSettingsAction("settings_patterns_mail")
                            showMailPatternActionsDialog = false
                        },
                        enabled = selectedMailPatternDeleteAction.isNotBlank()
                    ) {
                        Text("Удалить")
                    }
                }
            },
            dismissButton = {
                TextButton(onClick = { showMailPatternActionsDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showMailPatternAddDialog && settingsSection != "extensions") {
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
                    Text(
                        text = if (mailPatternInputMode == "subject") {
                            "Подсказка: вставь тему реального письма с успешным бэкапом — приложение само соберёт regex (например: Backup completed for mail.example.com 120GB)."
                        } else {
                            "Подсказка: укажи 2–4 устойчивых фрагмента через ; или , (например: backup completed;mail.example.com;120GB)."
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
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
                        if (returnToMailPatternsDialog) {
                            onExtensionsSettingsAction("settings_patterns_mail")
                            showMailPatternsDialog = true
                            returnToMailPatternsDialog = false
                        }
                        showMailPatternAddDialog = false
                    },
                    enabled = mailPatternInputValue.isNotBlank()
                ) {
                    Text("Сохранить")
                }
            },
            dismissButton = {
                TextButton(onClick = {
                    showMailPatternAddDialog = false
                    if (returnToMailPatternsDialog) {
                        showMailPatternsDialog = true
                        returnToMailPatternsDialog = false
                    }
                }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showMailPatternEditDialog && settingsSection != "extensions") {
        AlertDialog(
            onDismissRequest = { showMailPatternEditDialog = false },
            title = { Text("✏️ Редактировать паттерн почты") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = mailPatternEditValueInput,
                        onValueChange = { mailPatternEditValueInput = it },
                        label = { Text("Новый regex паттерн") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    Text(
                        text = "Подсказка: меняй только текст паттерна, без номера и префикса типа (например, было: 1. subject: backup completed → редактируй только backup completed).",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val actionPayload = mailPatternEditAction + "|" +
                            Uri.encode(mailPatternEditValueInput.trim())
                        onExtensionsSettingsAction(actionPayload)
                        if (returnToMailPatternsDialog) {
                            onExtensionsSettingsAction("settings_patterns_mail")
                            showMailPatternsDialog = true
                            returnToMailPatternsDialog = false
                        }
                        showMailPatternEditDialog = false
                    },
                    enabled = mailPatternEditAction.isNotBlank() &&
                        mailPatternEditValueInput.isNotBlank()
                ) {
                    Text("Сохранить")
                }
            },
            dismissButton = {
                TextButton(onClick = {
                    showMailPatternEditDialog = false
                    if (returnToMailPatternsDialog) {
                        showMailPatternsDialog = true
                        returnToMailPatternsDialog = false
                    }
                }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showDatabaseBackupsDialog) {
        AlertDialog(
            onDismissRequest = { showDatabaseBackupsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🗃️ Бэкапы БД",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            dbEntryAddCategory = ""
                            dbEntryAddKeyInput = ""
                            dbEntryAddNameInput = ""
                            showDbOpsEntryAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить новую БД в список бэкапов"
                            )
                        }
                        IconButton(onClick = {
                            onExtensionsSettingsAction("settings_patterns_db")
                            showDatabasePatternsDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = "Открыть паттерны бэкапов БД"
                            )
                        }
                        IconButton(onClick = { showDatabaseBackupsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть список бэкапов БД"
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
                    if (state.extensionMenuAction != "backup_databases" || state.extensionMenuOptions.isEmpty()) {
                        Text("Загружаем список бэкапов БД…")
                    } else {
                        Text(
                            text = "Долгий тап по плашке БД - настройки\n(редактировать / вкл-выкл / удалить)",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        FlowRow(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                            maxItemsInEachRow = 2
                        ) {
                            state.extensionMenuOptions.forEach { option ->
                                val label = option.label?.trim().orEmpty()
                                val targetAction = resolveMenuOptionAction(option)
                                if (targetAction.isNotBlank()) {
                                    val baseLabel = if (label.isNotBlank()) {
                                        label
                                    } else {
                                        deriveDatabaseBackupLabelFromAction(targetAction)
                                    }
                                    val displayLabel = formatBackupLabelWithMonitorStatus(baseLabel, targetAction)
                                    if (displayLabel.isBlank()) return@forEach
                                    Surface(
                                        modifier = Modifier
                                            .weight(1f)
                                            .clip(RoundedCornerShape(10.dp))
                                            .combinedClickable(
                                                onClick = {
                                                    if (targetAction.startsWith("db_detail_") && "__" in targetAction) {
                                                        databaseActionsTargetAction = targetAction
                                                    } else {
                                                        showDatabaseBackupsDialog = false
                                                        selectedDatabaseBackupLabel = baseLabel
                                                        selectedProxmoxBackupLabel = ""
                                                        showProxmoxBackupStatsDialog = true
                                                        onAction(targetAction)
                                                    }
                                                },
                                                onLongClick = {
                                                    if (targetAction.startsWith("db_detail_") && "__" in targetAction) {
                                                        databaseActionsTargetAction = targetAction
                                                    }
                                                }
                                            ),
                                        tonalElevation = 2.dp,
                                        shape = RoundedCornerShape(10.dp),
                                        color = if (isProblemBackupOption(baseLabel, targetAction)) {
                                            MaterialTheme.colorScheme.errorContainer
                                        } else {
                                            MaterialTheme.colorScheme.tertiaryContainer
                                        }
                                    ) {
                                        Text(
                                            text = displayLabel,
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(horizontal = 10.dp, vertical = 8.dp),
                                            maxLines = 3,
                                            overflow = TextOverflow.Ellipsis,
                                            color = if (isProblemBackupOption(baseLabel, targetAction)) {
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

    if (showDatabasePatternsDialog) {
        AlertDialog(
            onDismissRequest = { showDatabasePatternsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🔍 Паттерны бэкапов БД",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        IconButton(onClick = {
                            patternDialogReturnAction = "settings_patterns_db"
                            proxmoxPatternCategoryInput = "database"
                            proxmoxPatternTypeInput = "subject"
                            proxmoxPatternValueInput = ""
                            showProxmoxPatternAddDialog = true
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = "Добавить паттерн бэкапа БД"
                            )
                        }
                        IconButton(onClick = { showDatabasePatternsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть список паттернов бэкапов БД"
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
                    if (databasePatternMenuAction == null) {
                        Text("Загружаем список паттернов бэкапов БД…")
                    } else if (databasePatternOptionGroups.isEmpty()) {
                        Text("Паттерны бэкапов БД пока не добавлены.")
                    } else {
                        databasePatternOptionGroups.forEach { pattern ->
                            Surface(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(10.dp))
                                    .clickable {
                                        selectedDatabasePatternLabel = pattern.label
                                        selectedDatabasePatternEditAction = pattern.editAction
                                        selectedDatabasePatternDeleteAction = pattern.deleteAction
                                        showDatabasePatternActionsDialog = true
                                    },
                                tonalElevation = 2.dp,
                                shape = RoundedCornerShape(10.dp),
                                color = MaterialTheme.colorScheme.secondaryContainer
                            ) {
                                Text(
                                    text = pattern.label,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    maxLines = 3,
                                    overflow = TextOverflow.Ellipsis,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                        }
                    }
                }
            },
            confirmButton = {}
        )
    }

    if (showDatabasePatternActionsDialog) {
        AlertDialog(
            onDismissRequest = { showDatabasePatternActionsDialog = false },
            title = { Text("Паттерн: ${selectedDatabasePatternLabel.ifBlank { "без названия" }}") },
            text = { Text("Выбери действие для паттерна.") },
            confirmButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(
                        onClick = {
                            proxmoxPatternEditAction = selectedDatabasePatternEditAction
                            val prefill = parseProxmoxPatternEditPrefill(selectedDatabasePatternLabel)
                            proxmoxPatternEditTypeInput = prefill.patternType
                            proxmoxPatternEditValueInput = prefill.patternValue
                            patternDialogReturnAction = "settings_patterns_db"
                            showProxmoxPatternEditDialog = true
                            showDatabasePatternActionsDialog = false
                        },
                        enabled = selectedDatabasePatternEditAction.isNotBlank()
                    ) {
                        Text("Редактировать")
                    }
                    TextButton(
                        onClick = {
                            onExtensionsSettingsAction(selectedDatabasePatternDeleteAction)
                            onExtensionsSettingsAction("settings_patterns_db")
                            showDatabasePatternActionsDialog = false
                        },
                        enabled = selectedDatabasePatternDeleteAction.isNotBlank()
                    ) {
                        Text("Удалить")
                    }
                }
            },
            dismissButton = {
                TextButton(onClick = { showDatabasePatternActionsDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (selectedDatabaseForActions != null) {
        AlertDialog(
            onDismissRequest = { databaseActionsTargetAction = "" },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = selectedDatabaseForActions.label?.trim().orEmpty(),
                        modifier = Modifier.weight(1f),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    IconButton(onClick = { databaseActionsTargetAction = "" }) {
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
                                if (selectedDatabaseActionCategory.isNotBlank() && selectedDatabaseActionKey.isNotBlank()) {
                                    onExtensionsSettingsAction(
                                        "settings_db_edit_db_${Uri.encode(selectedDatabaseActionCategory)}" +
                                            "__${Uri.encode(selectedDatabaseActionKey)}"
                                    )
                                }
                                databaseActionsTargetAction = ""
                            }
                        ) {
                            Icon(Icons.Filled.Edit, contentDescription = "Редактировать")
                        }
                        Text("Изм.", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                if (selectedDatabaseActionCategory.isNotBlank() && selectedDatabaseActionKey.isNotBlank()) {
                                    onExtensionsSettingsAction(
                                        "settings_db_toggle_monitor_${Uri.encode(selectedDatabaseActionCategory)}" +
                                            "__${Uri.encode(selectedDatabaseActionKey)}"
                                    )
                                    onAction("backup_databases")
                                }
                                databaseActionsTargetAction = ""
                            }
                        ) {
                            Icon(Icons.Filled.PowerSettingsNew, contentDescription = "Вкл/выкл")
                        }
                        Text("Вкл/выкл", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                if (selectedDatabaseActionCategory.isNotBlank() && selectedDatabaseActionKey.isNotBlank()) {
                                    onExtensionsSettingsAction(
                                        "settings_db_delete_db_${Uri.encode(selectedDatabaseActionCategory)}" +
                                            "__${Uri.encode(selectedDatabaseActionKey)}"
                                    )
                                    onAction("backup_databases")
                                }
                                databaseActionsTargetAction = ""
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

    if (showServerAddDialog) {
        AlertDialog(
            onDismissRequest = { showServerAddDialog = false },
            title = { Text(if (state.serverEditIp.isBlank()) "Добавить сервер" else "Редактировать сервер") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedTextField(
                        value = state.serverIpInput,
                        onValueChange = onServerIpChanged,
                        label = { Text("IP") },
                        singleLine = true,
                        enabled = state.serverEditIp.isBlank()
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
                    Text(if (state.serverEditIp.isBlank()) "Сохранить" else "Применить")
                }
            },
            dismissButton = {
                TextButton(onClick = { showServerAddDialog = false }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (selectedProxmoxHostForActions != null) {
        AlertDialog(
            onDismissRequest = { proxmoxHostActionsTargetKey = "" },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(proxmoxHostActionsTargetKey)
                    IconButton(onClick = { proxmoxHostActionsTargetKey = "" }) {
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
                                onExtensionsSettingsAction("settings_proxmox_edit_$proxmoxHostActionsTargetKey")
                                proxmoxHostActionsTargetKey = ""
                            }
                        ) {
                            Icon(Icons.Filled.Edit, contentDescription = "Редактировать")
                        }
                        Text("Изм.", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                onExtensionsSettingsAction("settings_proxmox_toggle_$proxmoxHostActionsTargetKey")
                                proxmoxHostActionsTargetKey = ""
                            }
                        ) {
                            Icon(Icons.Filled.PowerSettingsNew, contentDescription = "Вкл/выкл")
                        }
                        Text("Вкл/выкл", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                proxmoxHostDeleteConfirmTargetKey = proxmoxHostActionsTargetKey
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

    if (proxmoxHostDeleteConfirmTargetKey.isNotBlank()) {
        AlertDialog(
            onDismissRequest = { proxmoxHostDeleteConfirmTargetKey = "" },
            title = { Text("Подтвердить удаление") },
            text = {
                Text("Удалить хост «$proxmoxHostDeleteConfirmTargetKey»?")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        onExtensionsSettingsAction("settings_proxmox_delete_$proxmoxHostDeleteConfirmTargetKey")
                        proxmoxHostDeleteConfirmTargetKey = ""
                        proxmoxHostActionsTargetKey = ""
                    }
                ) {
                    Text("Удалить")
                }
            },
            dismissButton = {
                TextButton(onClick = { proxmoxHostDeleteConfirmTargetKey = "" }) {
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
                                showServerAddDialog = true
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
                                serverDeleteConfirmTargetKey = selectedServerForActions.ip
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


    if (serverDeleteConfirmTargetKey.isNotBlank()) {
        val serverToDelete = state.managedServers.firstOrNull {
            normalizeServerLookupToken(it.ip) == normalizeServerLookupToken(serverDeleteConfirmTargetKey)
        }
        val serverDeleteLabel = serverToDelete?.name?.takeIf { it.isNotBlank() } ?: serverDeleteConfirmTargetKey
        AlertDialog(
            onDismissRequest = { serverDeleteConfirmTargetKey = "" },
            title = { Text("Подтвердить удаление") },
            text = {
                Text("Удалить сервер «$serverDeleteLabel»?")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        onDeleteServer(serverDeleteConfirmTargetKey)
                        serverDeleteConfirmTargetKey = ""
                        serverActionsTargetKey = ""
                    }
                ) {
                    Text("Удалить")
                }
            },
            dismissButton = {
                TextButton(onClick = { serverDeleteConfirmTargetKey = "" }) {
                    Text("Отмена")
                }
            }
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
