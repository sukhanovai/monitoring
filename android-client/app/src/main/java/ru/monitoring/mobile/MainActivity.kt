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
import androidx.compose.material3.IconButtonDefaults
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
import androidx.compose.material.pullrefresh.pullRefresh
import androidx.compose.material.pullrefresh.rememberPullRefreshState
import androidx.compose.material.pullrefresh.PullRefreshIndicator
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.PowerSettingsNew
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DarkMode
import androidx.compose.material.icons.filled.LightMode
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Sync
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
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch
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

private val zfsPoolFreePercentRegex = Regex(
    """(\d{1,3}(?:[.,]\d+)?)\s*%(?=\s*(?:free|свобод(?:но|ного)?))""",
    RegexOption.IGNORE_CASE
)

private fun zfsFreePercentColor(freePercent: Double): Color {
    val normalized = freePercent.coerceIn(0.0, 100.0)
    return when {
        normalized <= 15.0 -> {
            val fraction = (normalized / 15.0).toFloat().coerceIn(0f, 1f)
            lerp(Color(0xFFD50000), Color(0xFFFF6D00), fraction)
        }
        normalized <= 35.0 -> {
            val fraction = ((normalized - 15.0) / 20.0).toFloat().coerceIn(0f, 1f)
            lerp(Color(0xFFFF6D00), Color(0xFFFFC107), fraction)
        }
        else -> {
            val fraction = ((normalized - 35.0) / 65.0).toFloat().coerceIn(0f, 1f)
            lerp(Color(0xFFFFC107), Color(0xFF00C853), fraction)
        }
    }
}

private fun zfsFreePercentBackgroundColor(freePercent: Double): Color {
    val normalized = freePercent.coerceIn(0.0, 100.0)
    return when {
        normalized <= 10.0 -> Color(0xFFFFEBEE)
        normalized <= 20.0 -> Color(0xFFFFF3E0)
        normalized <= 35.0 -> Color(0xFFFFF8E1)
        else -> Color(0xFFE8F5E9)
    }
}

private fun zfsFreePercentBadgeBackgroundColor(freePercent: Double): Color {
    val normalized = freePercent.coerceIn(0.0, 100.0)
    return when {
        normalized <= 15.0 -> Color(0xFFFFCDD2)
        normalized <= 35.0 -> Color(0xFFFFE0B2)
        else -> Color(0xFFC8E6C9)
    }
}

@Composable
private fun zfsPoolCardBackgroundColor(freePercent: Double?): Color {
    if (freePercent == null) return MaterialTheme.colorScheme.tertiaryContainer
    return zfsFreePercentBackgroundColor(freePercent)
}

private fun extractZfsFreePercent(label: String): Double? {
    val match = zfsPoolFreePercentRegex.find(label.trim()) ?: return null
    return match.groupValues.getOrNull(1)?.replace(',', '.')?.toDoubleOrNull()
}

private fun buildReadableZfsPoolLine(line: String) = buildAnnotatedString {
    val match = zfsPoolFreePercentRegex.find(line)
    if (match == null) {
        append(line)
        return@buildAnnotatedString
    }
    val percentText = match.value
    val freePercent = match.groupValues.getOrNull(1)?.replace(',', '.')?.toDoubleOrNull()
    append(line.substring(0, match.range.first))
    if (freePercent == null) {
        append(percentText)
    } else {
        pushStyle(
            SpanStyle(
                color = zfsFreePercentColor(freePercent),
                fontWeight = FontWeight.Bold
            )
        )
        append(percentText)
        pop()
    }
    append(line.substring(match.range.last + 1))
}

private data class ZfsPoolTableRow(
    val host: String,
    val pool: String,
    val freePercentText: String,
    val freePercent: Double?,
    val action: String
)

private fun parseZfsPoolTableRow(label: String, action: String): ZfsPoolTableRow {
    val trimmed = label.trim()
    val freePercent = extractZfsFreePercent(trimmed)
    val freePercentText = freePercent?.let { "${it}%"} ?: "—"
    val withoutStatusEmoji = trimmed.replace(Regex("""^[✅❌⚠️🚨🆘⛔🔴🟠🟡🟢⚪✔]+\s*"""), "")
    val poolName = Regex("""`([^`]+)`""").find(withoutStatusEmoji)?.groupValues?.getOrNull(1).orEmpty()
    val hostRaw = if (poolName.isNotBlank()) {
        withoutStatusEmoji.substringBefore("`").trim()
    } else {
        withoutStatusEmoji.substringBefore("·").trim()
    }
    val host = hostRaw.ifBlank { "—" }
    val pool = poolName.ifBlank { withoutStatusEmoji.ifBlank { "—" } }
    return ZfsPoolTableRow(
        host = host,
        pool = pool,
        freePercentText = freePercentText,
        freePercent = freePercent,
        action = action
    )
}

private fun isAuxiliaryZfsPoolAction(action: String, label: String): Boolean {
    val normalizedAction = action.trim().lowercase()
    val normalizedLabel = label.trim().lowercase()
    return normalizedAction == "zfs_pool_free_space_menu" ||
        normalizedAction == "close" ||
        normalizedLabel.contains("обновить") ||
        normalizedLabel.contains("закрыть")
}

private fun isZfsPoolHostSettingsAction(action: String): Boolean {
    val normalizedAction = action.trim().lowercase()
    return normalizedAction == "zfsp_hosts_list" ||
        normalizedAction == "zfsp_add" ||
        normalizedAction == "zfs_pool_free_space_menu" ||
        normalizedAction.startsWith("zfsp_edit_") ||
        normalizedAction.startsWith("zfsp_delete_") ||
        normalizedAction.startsWith("zfsp_toggle_")
}

private fun extractZfsPoolsTotal(message: String): Int? {
    if (message.isBlank()) return null
    val poolLineRegex = Regex("""(?i)(?:пулов|pools)\s*[:=]\s*(\d+)""")
    return message.lineSequence()
        .map { it.trim() }
        .mapNotNull { line -> poolLineRegex.find(line)?.groupValues?.getOrNull(1)?.toIntOrNull() }
        .firstOrNull()
}

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
private val zfsStatusEmojiPoolLineRegex = Regex("""^[🟢🟡🔴⚪❌⚠️✅✔️]\s*`?([^`]+?)`?\s*:\s*`?([^`()]+?)`?\s*\((.+)\)$""")
private val zfsDateTimeRegex = Regex("""(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})(?::\d{2})?""")
private val zfsHostHeaderRegex = Regex("""^[A-Za-z0-9._:-]+$""")
private val zfsHostHeaderMarkdownRegex = Regex("""^[🖥💻]\s*\*([^*]+)\*\s*$""")
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

        val markdownHostHeaderMatch = zfsHostHeaderMarkdownRegex.matchEntire(line)
        if (markdownHostHeaderMatch != null) {
            currentHost = markdownHostHeaderMatch.groupValues.getOrNull(1)?.trim().orEmpty()
            return@forEach
        }

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

        val emojiPoolMatch = zfsStatusEmojiPoolLineRegex.matchEntire(line)
        if (emojiPoolMatch != null) {
            val poolName = emojiPoolMatch.groupValues.getOrNull(1)?.trim().orEmpty()
            val state = emojiPoolMatch.groupValues.getOrNull(2)?.trim().orEmpty()
            val timestamp = emojiPoolMatch.groupValues.getOrNull(3)?.trim().orEmpty()
            val hostName = currentHost
            if (poolName.isBlank() || state.isBlank() || hostName.isBlank()) return@forEach
            val poolItem = ZfsPoolStatusItem(
                poolName = poolName,
                statusLabel = zfsStateLabel(state),
                rawState = state.uppercase(),
                rawTimestamp = timestamp,
                compactTimestamp = compactZfsTimestamp(timestamp),
                hasProblem = !state.equals("ONLINE", ignoreCase = true)
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

private data class ZfsPoolHostSettingsGroup(
    val hostName: String,
    val editNameAction: String,
    val editIpAction: String,
    val editThresholdAction: String,
    val deleteAction: String,
    val toggleAction: String,
    val toggleLabel: String
)

private fun extractZfsPoolHostSettingsGroups(options: List<Pair<String, String>>): List<ZfsPoolHostSettingsGroup> {
    data class MutableZfsPoolHostSettingsGroup(
        var hostName: String = "",
        var editNameAction: String = "",
        var editIpAction: String = "",
        var editThresholdAction: String = "",
        var deleteAction: String = "",
        var toggleAction: String = "",
        var toggleLabel: String = ""
    )

    fun extractHostForZfsPoolAction(action: String): String {
        return when {
            action.startsWith("zfsp_edit_name_") -> hostNameFromZfsAction(action, "zfsp_edit_name_")
            action.startsWith("zfsp_edit_ip_") -> hostNameFromZfsAction(action, "zfsp_edit_ip_")
            action.startsWith("zfsp_edit_threshold_") -> hostNameFromZfsAction(action, "zfsp_edit_threshold_")
            action.startsWith("zfsp_delete_") -> hostNameFromZfsAction(action, "zfsp_delete_")
            action.startsWith("zfsp_toggle_") -> hostNameFromZfsAction(action, "zfsp_toggle_")
            else -> ""
        }
    }

    val groups = linkedMapOf<String, MutableZfsPoolHostSettingsGroup>()

    options.forEach { (label, action) ->
        val normalizedAction = action.trim()
        val host = extractHostForZfsPoolAction(normalizedAction)
        if (host.isBlank()) return@forEach

        val group = groups.getOrPut(host.lowercase()) { MutableZfsPoolHostSettingsGroup() }
        if (group.hostName.isBlank()) group.hostName = host

        when {
            normalizedAction.startsWith("zfsp_edit_name_") -> group.editNameAction = normalizedAction
            normalizedAction.startsWith("zfsp_edit_ip_") -> group.editIpAction = normalizedAction
            normalizedAction.startsWith("zfsp_edit_threshold_") -> group.editThresholdAction = normalizedAction
            normalizedAction.startsWith("zfsp_delete_") -> group.deleteAction = normalizedAction
            normalizedAction.startsWith("zfsp_toggle_") -> {
                group.toggleAction = normalizedAction
                group.toggleLabel = label
            }
        }
    }

    return groups.values.mapNotNull { group ->
        val host = group.hostName.trim()
        if (host.isBlank()) {
            null
        } else {
            ZfsPoolHostSettingsGroup(
                hostName = host,
                editNameAction = group.editNameAction,
                editIpAction = group.editIpAction,
                editThresholdAction = group.editThresholdAction,
                deleteAction = group.deleteAction,
                toggleAction = group.toggleAction,
                toggleLabel = group.toggleLabel
            )
        }
    }
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

private fun buildPatternOptionGroups(options: List<ru.monitoring.mobile.api.MenuOption>): List<ProxmoxPatternOptionGroup> {
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

private fun findExtensionByIds(
    extensionsById: Map<String, ExtensionItem>,
    vararg ids: String
): ExtensionItem? {
    if (ids.isEmpty()) return null
    val normalizedMap = extensionsById.entries.associateBy { (id, _) ->
        id.trim().lowercase().replace('-', '_')
    }
    return ids.asSequence()
        .map { it.trim().lowercase().replace('-', '_') }
        .mapNotNull { normalizedId -> normalizedMap[normalizedId]?.value }
        .firstOrNull()
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
    isStale: Boolean = false,
    isLoading: Boolean = false,
    onClick: () -> Unit = {},
    onLongClick: (() -> Unit)? = null,
    onSettingsClick: (() -> Unit)? = null
) {
    val displayValue = if (isStale) "?" else value
    val valueColor = when {
        isStale -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
        hasProblem -> MaterialTheme.colorScheme.error
        else -> MaterialTheme.colorScheme.onSurface
    }
    Surface(
        modifier = modifier
            .widthIn(min = 72.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.7f))
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick
            ),
        shape = RoundedCornerShape(14.dp),
        tonalElevation = 1.dp
    ) {
        Box {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(displayValue, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = valueColor)
                    Text(label, style = MaterialTheme.typography.labelSmall)
                }
                if (!isStale && onSettingsClick != null) {
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
            if (isStale) {
                Box(
                    modifier = Modifier
                        .matchParentSize()
                        .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.35f)),
                    contentAlignment = Alignment.Center
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(22.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Filled.Refresh,
                            contentDescription = "Загрузить данные $label",
                            tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.55f),
                            modifier = Modifier.size(26.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun IncidentSummaryChip(
    label: String,
    value: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .clickable(onClick = onClick),
        color = MaterialTheme.colorScheme.errorContainer,
        contentColor = MaterialTheme.colorScheme.onErrorContainer,
        shape = RoundedCornerShape(12.dp),
        tonalElevation = 1.dp
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("⚠", fontSize = 14.sp)
            Text(label, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
            Text(
                value,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun ScreensPagerIndicator(
    pageCount: Int,
    currentPage: Int,
    onPageSelected: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 10.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            repeat(pageCount) { index ->
                val isSelected = index == currentPage
                val dotColor = if (isSelected) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f)
                }
                Box(
                    modifier = Modifier
                        .padding(horizontal = 6.dp)
                        .size(width = if (isSelected) 22.dp else 10.dp, height = 10.dp)
                        .clip(RoundedCornerShape(5.dp))
                        .background(dotColor)
                        .clickable { onPageSelected(index) }
                )
            }
        }
    }
}

@Composable
private fun CertificateStatusTile(
    statusText: String,
    warningText: String,
    isLoading: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val hasWarning = warningText.isNotBlank()
    val containerColor = if (hasWarning) {
        MaterialTheme.colorScheme.errorContainer
    } else {
        MaterialTheme.colorScheme.surfaceContainerHighest
    }
    val titleColor = if (hasWarning) {
        MaterialTheme.colorScheme.onErrorContainer
    } else {
        MaterialTheme.colorScheme.onSurface
    }
    val secondaryColor = if (hasWarning) {
        MaterialTheme.colorScheme.onErrorContainer
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .clickable(enabled = !isLoading, onClick = onClick),
        color = containerColor,
        shape = RoundedCornerShape(12.dp),
        tonalElevation = 1.dp
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("🔐", fontSize = 22.sp)
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Text(
                    "Сертификат BFF",
                    fontWeight = FontWeight.SemiBold,
                    style = MaterialTheme.typography.labelMedium,
                    color = titleColor
                )
                Text(
                    statusText.ifBlank { "—" },
                    style = MaterialTheme.typography.labelSmall,
                    color = secondaryColor
                )
                if (hasWarning) {
                    Text(
                        warningText,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onErrorContainer
                    )
                }
            }
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                    color = titleColor
                )
            } else {
                Icon(
                    imageVector = Icons.Filled.Refresh,
                    contentDescription = "Проверить сертификат",
                    tint = titleColor
                )
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
private fun SettingsActionButton(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
            contentColor = MaterialTheme.colorScheme.onSecondaryContainer
        )
    ) {
        Text(text = label, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun SettingsDangerButton(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.errorContainer,
            contentColor = MaterialTheme.colorScheme.onErrorContainer
        )
    ) {
        Text(text = label, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun SettingsSectionTile(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .heightIn(min = 76.dp)
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.secondaryContainer,
        contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
        tonalElevation = 2.dp
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 16.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = label,
                fontWeight = FontWeight.SemiBold,
                fontSize = 15.sp
            )
        }
    }
}

@Composable
private fun CompactHeaderIconButton(
    onClick: () -> Unit,
    contentDescription: String,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    IconButton(
        onClick = onClick,
        modifier = modifier.size(30.dp),
        colors = IconButtonDefaults.iconButtonColors(
            contentColor = MaterialTheme.colorScheme.onSurfaceVariant
        )
    ) {
        Box(contentAlignment = Alignment.Center) {
            content()
        }
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
                    onCheckCertificateOnly = vm::checkBffCertificateOnly,
                    onLoadServersForSingleCheck = { vm.refreshSettingsFromServer(showErrors = true) },
                    onLoadTileData = vm::loadTileData,
                    onEnsureSettingsLoaded = vm::ensureSettingsLoaded,
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
                    onTestBotServerConnection = vm::testBotServerConnection,
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
                    onFetchProxmoxHostBackups = vm::fetchProxmoxHostBackups,
                    onCloseProxmoxHostBackups = vm::closeProxmoxHostBackups,
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
    onCheckCertificateOnly: () -> Unit,
    onLoadServersForSingleCheck: () -> Unit,
    onLoadTileData: (String) -> Unit,
    onEnsureSettingsLoaded: () -> Unit,
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
    onTestBotServerConnection: () -> Unit,
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
    onFetchProxmoxHostBackups: (String) -> Unit,
    onCloseProxmoxHostBackups: () -> Unit,
    onOpenUpdateUrl: (String) -> Unit
) {
    val isCompactOpsHub = BuildConfig.IS_COMPACT_OPS_HUB

    var isManagementExpanded by rememberSaveable { mutableStateOf(false) }
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
    var showTileHelpDialog by rememberSaveable { mutableStateOf(false) }
    var tileHelpTitle by rememberSaveable { mutableStateOf("") }
    var tileHelpDescription by rememberSaveable { mutableStateOf("") }
    var serverResourceDetailsTargetKey by rememberSaveable { mutableStateOf("") }
    var serverResourceDetailsTitle by rememberSaveable { mutableStateOf("") }
    var areOpsTilesExpanded by rememberSaveable { mutableStateOf(false) }
    var showTileSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var settingsSection by rememberSaveable { mutableStateOf("bff") }
    var showSettingsSectionOverlay by rememberSaveable { mutableStateOf(false) }
    val pullToRefreshState = rememberPullRefreshState(state.isLoading, onRefreshData)
    val reportPullRefreshState = rememberPullRefreshState(
        state.isLoading,
        { onAction("send_morning_report") }
    )
    // 0 — отчёт, 1 — оперативный центр (стартовый экран), 2 — настройки.
    val screensPagerState = rememberPagerState(initialPage = 1) { 3 }
    val screensScope = rememberCoroutineScope()
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
    var showZfsPoolFreeSpaceDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsPoolHostsSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsHostsSettingsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsHostActionsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsPoolHostActionsDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsPoolHostAddDialog by rememberSaveable { mutableStateOf(false) }
    var showZfsPoolHostEditDialog by rememberSaveable { mutableStateOf(false) }
    var zfsPoolHostAddAction by rememberSaveable { mutableStateOf("zfsp_add") }
    var pendingZfsPoolHostAddFromFreeSpaceDialog by rememberSaveable { mutableStateOf(false) }
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
    var zfsPoolSelectedHostName by rememberSaveable { mutableStateOf("") }
    var zfsPoolSelectedHostEditNameAction by rememberSaveable { mutableStateOf("") }
    var zfsPoolSelectedHostEditIpAction by rememberSaveable { mutableStateOf("") }
    var zfsPoolSelectedHostEditThresholdAction by rememberSaveable { mutableStateOf("") }
    var zfsPoolSelectedHostDeleteAction by rememberSaveable { mutableStateOf("") }
    var zfsPoolSelectedHostToggleAction by rememberSaveable { mutableStateOf("") }
    var zfsPoolHostNameInput by rememberSaveable { mutableStateOf("") }
    var zfsPoolHostIpInput by rememberSaveable { mutableStateOf("") }
    var zfsPoolHostThresholdInput by rememberSaveable { mutableStateOf("20") }
    var zfsPoolHostEditNameInput by rememberSaveable { mutableStateOf("") }
    var zfsPoolHostEditIpInput by rememberSaveable { mutableStateOf("") }
    var zfsPoolHostEditThresholdInput by rememberSaveable { mutableStateOf("") }
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
    var showStockLoadsDialog by rememberSaveable { mutableStateOf(false) }
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

    LaunchedEffect(showZfsStatusesDialog) {
        if (showZfsStatusesDialog) {
            onAction("zfs_menu")
        }
    }

    LaunchedEffect(
        pendingZfsPoolHostAddFromFreeSpaceDialog,
        state.extensionMenuAction,
        state.extensionMenuOptions
    ) {
        if (!pendingZfsPoolHostAddFromFreeSpaceDialog) return@LaunchedEffect
        if (!state.extensionMenuAction.startsWith("zfsp_")) return@LaunchedEffect
        if (state.extensionMenuOptions.isEmpty()) return@LaunchedEffect
        val addAction = state.extensionMenuOptions
            .mapNotNull { option ->
                resolveMenuOptionAction(option).trim().takeIf { it.isNotBlank() }
            }
            .firstOrNull { action -> action == "zfsp_add" || action.startsWith("zfsp_add|") }
            ?: return@LaunchedEffect
        zfsPoolHostAddAction = addAction
        zfsPoolHostNameInput = ""
        zfsPoolHostIpInput = ""
        zfsPoolHostThresholdInput = "20"
        showZfsPoolHostAddDialog = true
        pendingZfsPoolHostAddFromFreeSpaceDialog = false
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

    LaunchedEffect(settingsSection) {
        if (settingsSection == "extensions") {
            onOpenExtensionsSettingsMenu()
        }
    }

    LaunchedEffect(showSettingsSectionOverlay) {
        if (showSettingsSectionOverlay) {
            onEnsureSettingsLoaded()
        }
    }

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
    val openTileHelpDialog = { title: String, description: String ->
        tileHelpTitle = title
        tileHelpDescription = description
        showTileHelpDialog = true
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
    val silentModeShortStatus = when {
        state.silentStatusText.contains("Принудительно тих", ignoreCase = true) -> "🔇 тихо"
        state.silentStatusText.contains("Принудительно громк", ignoreCase = true) -> "🔊 громко"
        state.silentStatusText.contains("сейчас тих", ignoreCase = true) -> "🔇 авто"
        state.silentStatusText.contains("сейчас громк", ignoreCase = true) -> "🔊 авто"
        state.silentStatusText.contains("авто", ignoreCase = true) -> "авто"
        else -> "..."
    }
    val opsTiles = listOf(
        OpsMetricTile(
            id = "modes",
            label = "Режим",
            value = silentModeShortStatus,
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
        findExtensionByIds(extensionsById, "zfs_monitor", "zfs")?.takeIf { it.enabled }?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(id = "zfs_monitor", name = "zfs статусы"),
                    summaryOverride = state.zfsSummary,
                    hasProblemOverride = state.zfsHasProblemItems
                )
            )
        }
        val zfsPoolFreeSpaceExtension = findExtensionByIds(
            extensionsById,
            "zfs_pool_free_space_monitor",
            "zfs_pool_free_space",
            "zfs_free_space_monitor"
        )
        zfsPoolFreeSpaceExtension?.takeIf { it.enabled }?.let { extension ->
            val hasProblem = state.zfsPoolFreeSpaceHasProblemItems
            add(
                buildExtensionDataTile(
                    extension = extension.copy(id = "zfs_pool_free_space_monitor", name = "zfs место"),
                    summaryOverride = state.zfsPoolFreeSpaceSummary,
                    hasProblemOverride = hasProblem
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
        findExtensionByIds(extensionsById, "supplier_stock_files", "supplier_stock_reports")
            ?.takeIf { it.enabled }
            ?.let { extension ->
            add(
                buildExtensionDataTile(
                    extension = extension.copy(id = "supplier_stock_files", name = "поставщики"),
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
            } else if (extension.id == "supplier_stock_files") {
                {
                    onAction("supplier_stock_reports")
                }
            } else if (extension.id == "stock_load_monitor") {
                {
                    showStockLoadsDialog = true
                    onAction("backup_stock_loads")
                }
            } else if (extension.id == "zfs_monitor") {
                {
                    showZfsStatusesDialog = true
                    onAction("zfs")
                    onExtensionsSettingsAction("settings_zfs_list")
                }
            } else if (extension.id == "resource_monitor") {
                {
                    openServerResourcesSingleCheckDetails()
                }
            } else if (
                extension.id == "zfs_pool_free_space_monitor" ||
                extension.id == "zfs_pool_free_space" ||
                extension.id.contains("zfs_pool_free_space")
            ) {
                {
                    showZfsPoolFreeSpaceDialog = true
                    onAction("zfs_pool_free_space_menu")
                    zfsPoolHostNameInput = ""
                    zfsPoolHostIpInput = ""
                    zfsPoolHostThresholdInput = "20"
                }
            } else {
                {
                    settingsSection = "extensions"
                    showSettingsSectionOverlay = true
                    screensScope.launch { screensPagerState.animateScrollToPage(2) }
                }
            },
            onLongClick = if (
                extension.id == "zfs_pool_free_space_monitor" ||
                extension.id == "zfs_pool_free_space" ||
                extension.id.contains("zfs_pool_free_space")
            ) {
                {
                    showZfsPoolHostsSettingsDialog = true
                    onAction("zfsp_hosts_list")
                }
            } else {
                null
            },
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
    val autoFillPriorityTileIds = listOf(
        "extension_zfs_pool_free_space_monitor",
        "extension_zfs_monitor",
        "extension_resource_monitor"
    )
    val autoFillTiles = buildList {
        autoFillPriorityTileIds.forEach { tileId ->
            hiddenTiles.firstOrNull { it.id == tileId }?.let { add(it) }
        }
        hiddenTiles.forEach { tile ->
            if (none { it.id == tile.id }) {
                add(tile)
            }
        }
    }
    val minVisibleTilesInCollapsedState = 4
    val autoFillTilesToShow = if (pinnedTiles.size >= minVisibleTilesInCollapsedState) {
        emptyList()
    } else {
        autoFillTiles.take(minVisibleTilesInCollapsedState - pinnedTiles.size)
    }
    val visibleTiles = if (areOpsTilesExpanded) {
        pinnedTiles + hiddenTiles
    } else {
        pinnedTiles + autoFillTilesToShow
    }
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
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        if (state.isLoading || state.isSyncInProgress) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.5.dp
                            )
                        }
                        Text(appTitle, fontWeight = FontWeight.SemiBold)
                    }
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
        },
        bottomBar = {
            ScreensPagerIndicator(
                pageCount = 3,
                currentPage = screensPagerState.currentPage,
                onPageSelected = { target ->
                    screensScope.launch { screensPagerState.animateScrollToPage(target) }
                }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            HorizontalPager(
                state = screensPagerState,
                beyondBoundsPageCount = 1,
                modifier = Modifier.fillMaxSize()
            ) { pagerPage ->
                when (pagerPage) {
                    2 -> {
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(contentPadding)
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("⚙️ Настройки", fontWeight = FontWeight.Bold, fontSize = 20.sp)
                                IconButton(
                                    onClick = {
                                        onThemeModeChanged(
                                            if (state.themeMode == "light") "dark" else "light"
                                        )
                                    }
                                ) {
                                    Icon(
                                        imageVector = if (state.themeMode == "light") {
                                            Icons.Filled.DarkMode
                                        } else {
                                            Icons.Filled.LightMode
                                        },
                                        contentDescription = "Переключить тему"
                                    )
                                }
                            }
                            FlowRow(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalArrangement = Arrangement.spacedBy(8.dp),
                                maxItemsInEachRow = 2
                            ) {
                                listOf(
                                    "bff" to "🔌 BFF",
                                    "monitoring" to "📈 Мониторинг",
                                    "bot" to "🤖 Бот",
                                    "time" to "⏰ Время",
                                    "auth" to "🔐 Аутентификация",
                                    "extensions" to "🧩 Расширения"
                                ).forEach { (sectionId, sectionLabel) ->
                                    SettingsSectionTile(
                                        label = sectionLabel,
                                        modifier = Modifier.weight(1f),
                                        onClick = {
                                            settingsSection = sectionId
                                            showSettingsSectionOverlay = true
                                        }
                                    )
                                }
                            }
                        }
                    }
                    0 -> {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .pullRefresh(reportPullRefreshState)
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .padding(contentPadding)
                                    .verticalScroll(rememberScrollState()),
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Text(
                                    "🌅 Последний отчёт",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 20.sp
                                )
                                if (state.morningReportText.isNotBlank()) {
                                    Text(state.morningReportText)
                                    if (state.morningReportReceivedAt.isNotBlank()) {
                                        Text(
                                            "Получен: ${state.morningReportReceivedAt}",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                } else {
                                    Text("Отчёт ещё не получен. Потяни список вниз, чтобы запросить.")
                                }
                            }
                            PullRefreshIndicator(
                                refreshing = state.isLoading,
                                state = reportPullRefreshState,
                                modifier = Modifier.align(Alignment.TopCenter)
                            )
                        }
                    }
                    else -> {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
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
                                IconButton(onClick = {
                                    onRefreshData()
                                    showServerAvailabilityDialog = false
                                    showServerResourcesMenu = false
                                    showServerResourcesDetailsDialog = false
                                }) {
                                    Icon(
                                        imageVector = Icons.Filled.Sync,
                                        contentDescription = "Синхронизировать данные"
                                    )
                                }
                                IconButton(onClick = { showTileSettingsDialog = true }) {
                                    Icon(
                                        imageVector = Icons.Filled.Settings,
                                        contentDescription = "Настроить плашки"
                                    )
                                }
                            }
                        }
                        val incidentTiles = allOpsTiles.filter { tile ->
                            val tileLoaded = state.allDataLoaded ||
                                tile.id == "modes" ||
                                tile.id in state.loadedTileIds
                            tileLoaded && tile.hasProblem
                        }
                        if (incidentTiles.isNotEmpty()) {
                            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text(
                                    "⚠️ Инциденты (${incidentTiles.size})",
                                    style = MaterialTheme.typography.labelLarge,
                                    fontWeight = FontWeight.SemiBold,
                                    color = MaterialTheme.colorScheme.error
                                )
                                FlowRow(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                                    verticalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    incidentTiles.forEach { tile ->
                                        IncidentSummaryChip(
                                            label = tile.label,
                                            value = tile.value,
                                            onClick = tile.onClick
                                        )
                                    }
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
                                val tileLoaded = state.allDataLoaded ||
                                    tile.id == "modes" ||
                                    tile.id in state.loadedTileIds
                                val isStale = !tileLoaded
                                OpsMetricChip(
                                    label = tile.label,
                                    value = tile.value,
                                    hasProblem = tile.hasProblem,
                                    modifier = Modifier
                                    .weight(1f)
                                    .animateContentSize(),
                                    isStale = isStale,
                                    isLoading = tile.id in state.loadingTileIds,
                                    onClick = if (isStale) {
                                        { onLoadTileData(tile.id) }
                                    } else {
                                        tile.onClick
                                    },
                                    onLongClick = if (isStale) null else tile.onLongClick,
                                    onSettingsClick = if (isStale) null else tile.onSettingsClick
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
                        CertificateStatusTile(
                            statusText = state.bffCertificateStatusText,
                            warningText = state.bffCertificateWarningText,
                            isLoading = state.isLoading,
                            onClick = onCheckCertificateOnly
                        )
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
                            CertificateStatusTile(
                                statusText = state.bffCertificateStatusText,
                                warningText = state.bffCertificateWarningText,
                                isLoading = state.isLoading,
                                onClick = onCheckCertificateOnly
                            )
                            if (state.message.isNotBlank() && state.messageSource == "global") {
                                Text(state.message)
                            }
                        }
                    }
                }
            }


            item {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
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
                                onClick = {
                                    showSettingsSectionOverlay = false
                                    screensScope.launch { screensPagerState.animateScrollToPage(2) }
                                },
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
                    if (showSettingsSectionOverlay) {
                        AlertDialog(
                            onDismissRequest = { showSettingsSectionOverlay = false },
                            confirmButton = {},
                            title = {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        when (settingsSection) {
                                            "bff" -> "🔌 BFF"
                                            "monitoring" -> "📈 Мониторинг"
                                            "bot" -> "🤖 Бот"
                                            "time" -> "⏰ Время"
                                            "auth" -> "🔐 Аутентификация"
                                            "extensions" -> "🧩 Расширения"
                                            else -> "⚙️ Настройки"
                                        }
                                    )
                                    IconButton(onClick = { showSettingsSectionOverlay = false }) {
                                        Icon(
                                            imageVector = Icons.Filled.Close,
                                            contentDescription = "Закрыть настройки раздела"
                                        )
                                    }
                                }
                            },
                            text = {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .heightIn(max = 560.dp)
                                        .verticalScroll(rememberScrollState()),
                                    verticalArrangement = Arrangement.spacedBy(8.dp)
                                ) {

                        if (settingsSection == "bff") {
                            Text("Подключение к BFF", fontWeight = FontWeight.Bold)
                        OutlinedTextField(
                            value = state.baseUrlInput,
                            onValueChange = onBaseUrlChanged,
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("Base URL API") }
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            SettingsActionButton(label = "Сохранить URL", onClick = onSaveBaseUrl)
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
                            SettingsActionButton(
                                label = "Сохранить токен",
                                onClick = { onSaveToken(state.token) }
                            )
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
                        SettingsActionButton(
                            label = "Сохранить monitoring",
                            onClick = onSaveMonitoring,
                            enabled = canSaveMonitoring
                        )
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
                                    SettingsDangerButton(
                                        label = "Удалить",
                                        onClick = { onRemoveTelegramChatId(chatId) }
                                    )
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
                            SettingsActionButton(label = "Добавить chat_id", onClick = onAddTelegramChatId)
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            SettingsActionButton(
                                label = "Проверить связь с сервером бота",
                                onClick = onTestBotServerConnection
                            )
                            SettingsActionButton(
                                label = "Сохранить bot",
                                onClick = onSaveBot,
                                enabled = canSaveBot
                            )
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
                        val notificationsEnabled = state.morningReportNotificationsEnabled
                        if (notificationsEnabled) {
                            SettingsActionButton(
                                label = "Уведомления: включены",
                                onClick = { onMorningNotificationsEnabledChanged(false) }
                            )
                        } else {
                            SettingsDangerButton(
                                label = "Уведомления: выключены",
                                onClick = { onMorningNotificationsEnabledChanged(true) }
                            )
                        }
                        Text("Статус уведомлений: ${if (state.morningReportNotificationsEnabled) "включены" else "выключены"}")
                        SettingsActionButton(
                            label = "Сохранить time",
                            onClick = onSaveTime,
                            enabled = canSaveTime
                        )
                        }

                        if (settingsSection == "extensions") {
                            Text("🧩 Настройки расширений", fontWeight = FontWeight.Bold)
                            Text("Включай/выключай расширения и открывай настройки активных расширений.")

                            if (state.extensionSettingsMenuOptions.isEmpty()) {
                                Text("Нет доступных настроек для активных расширений.")
                            }
                            if (state.message.isNotBlank() && state.messageSource == "extensions_settings") {
                                Text(state.message)
                            }
                            Text(
                                "Кнопки быстрых переходов скрыты в Android. Управляй разделами расширений из Telegram-бота.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )

                            Text("🛠️ Управление расширениями (вкл/выкл)", fontWeight = FontWeight.Bold)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                SettingsActionButton(
                                    label = "Включить все",
                                    onClick = onEnableAllExtensions
                                )
                                SettingsDangerButton(
                                    label = "Отключить все",
                                    onClick = onDisableAllExtensions
                                )
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

                            SettingsActionButton(
                                onClick = { isSshAuthExpanded = !isSshAuthExpanded },
                                modifier = Modifier.fillMaxWidth(),
                                label = "👤 SSH аутентификация"
                            )
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
                                SettingsActionButton(
                                    label = "Сохранить SSH",
                                    onClick = onSaveAuth,
                                    enabled = canSaveAuth
                                )
                            }

                            SettingsActionButton(
                                onClick = { isWindowsAuthExpanded = !isWindowsAuthExpanded },
                                modifier = Modifier.fillMaxWidth(),
                                label = "🖥 Windows аутентификация"
                            )
                            if (isWindowsAuthExpanded) {
                                SettingsActionButton(
                                    onClick = { showWindowsAll = !showWindowsAll },
                                    modifier = Modifier.fillMaxWidth(),
                                    label = "👥 Просмотр всех учетных записей"
                                )
                                if (showWindowsAll) {
                                    state.windowsCredentials.forEach { cred ->
                                        ElevatedCard(modifier = Modifier.fillMaxWidth()) {
                                            Column(modifier = Modifier.padding(10.dp)) {
                                                Text("🟢 ${cred.serverType ?: "default"} (приоритет: ${cred.priority ?: 0})")
                                                Text("Пользователь: ${cred.username ?: "-"}")
                                                Text("ID: ${cred.id ?: "-"}")
                                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                    SettingsDangerButton(
                                                        label = "Удалить",
                                                        onClick = { onRemoveWindowsCredential(cred.id) }
                                                    )
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
                                SettingsActionButton(
                                    label = "Добавить учетную запись",
                                    onClick = onAddWindowsCredential
                                )

                                SettingsActionButton(
                                    onClick = { showWindowsByType = !showWindowsByType },
                                    modifier = Modifier.fillMaxWidth(),
                                    label = "📊 Учетные данные по типам"
                                )
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

                                SettingsActionButton(
                                    onClick = { showWindowsTypeStats = !showWindowsTypeStats },
                                    modifier = Modifier.fillMaxWidth(),
                                    label = "⚙️ Управление типами серверов"
                                )
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
                                    SettingsActionButton(label = "Создать тип", onClick = onCreateWindowsType)

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
                                    SettingsActionButton(label = "Переименовать", onClick = onRenameWindowsType)

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
                                    SettingsActionButton(label = "Объединить", onClick = onMergeWindowsTypes)

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
                                    SettingsDangerButton(label = "Удалить тип", onClick = onDeleteWindowsType)
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

        )
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
                            IconButton(
                                onClick = {
                                    val helpTitle = if (isResourceCheckMode) {
                                        "Справка: плашка «ресурсы»"
                                    } else {
                                        "Справка: плашка «серверы»"
                                    }
                                    val helpDescription = if (isResourceCheckMode) {
                                        "Плашка показывает точечную проверку ресурсов по выбранным серверам. " +
                                            "Внутри можно открыть карточку хоста и увидеть нагрузку CPU/RAM/дисков, " +
                                            "а затем перейти в настройки порогов ресурса. " +
                                            "Настройка делается через кнопку ⚙️ в этом окне и редактирование порогов."
                                    } else {
                                        "Плашка отвечает за точечную проверку доступности серверов. " +
                                            "Внутри выполняется ручной ping/check по каждому хосту и показывается текущий статус. " +
                                            "Настройка списка делается через долгий тап по плашке хоста (редактировать/вкл-выкл/удалить) и кнопку ➕."
                                    }
                                    openTileHelpDialog(helpTitle, helpDescription)
                                },
                                modifier = Modifier
                                    .padding(bottom = 2.dp)
                                    .height(30.dp)
                            ) {
                                Text("?", fontWeight = FontWeight.Bold)
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
                            "Тап по плашке хоста — карточка действий\n(редактировать / вкл-выкл / удалить)"
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

    if (showTileHelpDialog) {
        AlertDialog(
            onDismissRequest = { showTileHelpDialog = false },
            title = {
                Text(
                    text = tileHelpTitle.ifBlank { "Справка по плашке" },
                    fontWeight = FontWeight.Bold
                )
            },
            text = { Text(tileHelpDescription.ifBlank { "Описание для этой плашки пока не задано." }) },
            confirmButton = {
                TextButton(onClick = { showTileHelpDialog = false }) {
                    Text("Понятно")
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
                    Column(
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                        horizontalAlignment = Alignment.End
                    ) {
                        CompactHeaderIconButton(
                            onClick = { showMailBackupsDialog = false },
                            contentDescription = "Закрыть окно бэкапов почты"
                        ) {
                            Icon(Icons.Filled.Close, contentDescription = null)
                        }
                        CompactHeaderIconButton(onClick = {
                            openTileHelpDialog(
                                "Справка: плашка «почта»",
                                "Плашка показывает историю почтовых бэкапов и их статус. " +
                                    "Внутри отображаются размер, путь и свежесть каждого бэкапа. " +
                                    "Настройка делается через кнопку ⚙️: там редактируются паттерны, по которым приложение находит успешные письма о бэкапе."
                            )
                        }, contentDescription = "Справка по плашке почты") {
                            Text("?", fontWeight = FontWeight.Bold)
                        }
                        CompactHeaderIconButton(
                            onClick = {
                                showMailBackupsDialog = false
                                onExtensionsSettingsAction("settings_patterns_mail")
                                showMailPatternsDialog = true
                            },
                            contentDescription = "Открыть паттерны почтовых бэкапов"
                        ) {
                            Icon(Icons.Filled.Settings, contentDescription = null)
                        }
                        CompactHeaderIconButton(onClick = {
                            mailPatternInputMode = "subject"
                            mailPatternInputValue = ""
                            returnToMailPatternsDialog = false
                            showMailBackupsDialog = false
                            onExtensionsSettingsAction("settings_patterns_mail")
                            showMailPatternAddDialog = true
                        }, contentDescription = "Добавить паттерн почты") {
                            Icon(Icons.Filled.Add, contentDescription = null)
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

    if (showStockLoadsDialog) {
        AlertDialog(
            onDismissRequest = { showStockLoadsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "📦 Загрузка остатков 1С",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = { showStockLoadsDialog = false }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть сведения о загрузке остатков"
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
                    if (state.message.isNotBlank() && state.messageSource == "global") {
                        Text(state.message)
                    } else {
                        Text("Загружаем данные о загрузке остатков…")
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
                        onExtensionsSettingsAction("settings_backup_proxmox")
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
                    Column(
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                        horizontalAlignment = Alignment.End
                    ) {
                        CompactHeaderIconButton(
                            onClick = { showZfsStatusesDialog = false },
                            contentDescription = "Закрыть окно статусов ZFS"
                        ) {
                            Icon(Icons.Filled.Close, contentDescription = null)
                        }
                        CompactHeaderIconButton(
                            onClick = { onAction("zfs_menu") },
                            contentDescription = "Обновить статусы ZFS"
                        ) {
                            Icon(Icons.Filled.Refresh, contentDescription = null)
                        }
                        CompactHeaderIconButton(onClick = {
                            openTileHelpDialog(
                                "Справка: плашка «zfs статусы»",
                                "Плашка отвечает за состояние ZFS на хостах: показывает статусы пулов и проблемные места. " +
                                    "Короткий тап по плашке хоста открывает детали, долгий — действия по хосту. " +
                                    "Настройка выполняется через ➕ (добавление хоста) и ⚙️ (паттерны/правила распознавания). " +
                                    "Пример статусов: ONLINE (норма), DEGRADED (внимание), FAULTED/OFFLINE (критично)."
                            )
                        }, contentDescription = "Справка по статусам ZFS") {
                            Text("?", fontWeight = FontWeight.Bold)
                        }
                        CompactHeaderIconButton(onClick = {
                            showZfsPatternsDialog = true
                            onExtensionsSettingsAction("settings_patterns_zfs")
                        }, contentDescription = "Открыть паттерны ZFS") {
                            Icon(Icons.Filled.Settings, contentDescription = null)
                        }
                        CompactHeaderIconButton(onClick = {
                            zfsHostInput = ""
                            showZfsHostAddDialog = true
                        }, contentDescription = "Добавить хост ZFS") {
                            Icon(Icons.Filled.Add, contentDescription = null)
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
                        Button(onClick = { onAction("zfs") }) { Text("Обновить") }
                    } else {
                        if (allStatusCards.isNotEmpty()) {
                            Text(
                                text = "Хосты ZFS: ${resolveZfsHostsCount(state.zfsStatusMessage, allStatusCards.size, zfsSettingsOptions)}",
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                text = "Короткий тап по плашке хоста — сведения. Долгий тап — настройки (редактировать / вкл-выкл / удалить)",
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
                                                zfsDetailsHostName = card.hostName
                                                zfsStatusDetailsFallbackText = ""
                                                showZfsHostDetailsDialog = true
                                                val detailsAction = card.action?.trim().orEmpty()
                                                if (detailsAction.isNotBlank()) {
                                                    onAction(detailsAction)
                                                } else {
                                                    zfsStatusDetailsFallbackText = formatZfsHostDetails(card)
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

    if (showZfsPoolFreeSpaceDialog) {
        val zfsPoolMenuOptions = if (
            state.extensionMenuAction == "zfs_pool_free_space_menu" ||
            state.extensionMenuAction.startsWith("zfsp_")
        ) {
            state.extensionMenuOptions
        } else {
            emptyList()
        }
        AlertDialog(
            onDismissRequest = {
                showZfsPoolFreeSpaceDialog = false
            },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "💽 Свободное место ZFS пулов",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        CompactHeaderIconButton(onClick = {
                            showZfsPoolFreeSpaceDialog = false
                        }, contentDescription = "Закрыть окно ZFS-пулов") {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = null
                            )
                        }
                        CompactHeaderIconButton(onClick = {
                            openTileHelpDialog(
                                "Справка: плашка «zfs место»",
                                "Плашка показывает свободное место по ZFS-пулам на подключённых хостах. " +
                                    "Внутри отображается таблица хост/пул/процент свободного пространства с цветовой индикацией риска. " +
                                    "Настройка выполняется через ⚙️ — список хостов и пороги свободного места для предупреждений."
                            )
                        }, contentDescription = "Справка по ZFS-пулам") {
                            Text("?", fontWeight = FontWeight.Bold)
                        }
                        CompactHeaderIconButton(onClick = {
                            showZfsPoolFreeSpaceDialog = false
                            showZfsPoolHostsSettingsDialog = true
                            onAction("zfsp_hosts_list")
                            pendingZfsPoolHostAddFromFreeSpaceDialog = false
                        }, contentDescription = "Настройки хостов ZFS-пулов") {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = null
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
                    val zfsPoolActions = zfsPoolMenuOptions
                        .mapNotNull { option ->
                            val action = resolveMenuOptionAction(option)
                            val label = option.label?.trim().orEmpty()
                            if (label.isBlank() || action.isBlank()) return@mapNotNull null
                            if (isAuxiliaryZfsPoolAction(action, label)) return@mapNotNull null
                            label to action
                        }
                        .distinctBy { (_, action) -> action }
                    val hasData = zfsPoolActions.isNotEmpty() || state.zfsPoolFreeSpaceSummary.isNotBlank() || extractZfsPoolsTotal(state.message) != null

                    if (state.isLoading && !hasData) {
                        Text("Загружаем данные по ZFS-пулам…")
                    } else if (!hasData) {
                        Text("Пока нет данных по свободному месту ZFS пулов. Потяни список вниз или нажми кнопку синхронизации в оперативном центре.")
                    } else {
                        if (zfsPoolActions.isNotEmpty()) {
                            val zfsPoolRows = zfsPoolActions.map { (label, action) ->
                                parseZfsPoolTableRow(label, action)
                            }
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                tonalElevation = 1.dp,
                                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f)
                            ) {
                                Column(modifier = Modifier.fillMaxWidth()) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(horizontal = 10.dp, vertical = 8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = "Хост",
                                            modifier = Modifier.weight(0.35f),
                                            style = MaterialTheme.typography.labelMedium,
                                            fontWeight = FontWeight.Bold
                                        )
                                        Text(
                                            text = "Пул",
                                            modifier = Modifier.weight(0.4f),
                                            style = MaterialTheme.typography.labelMedium,
                                            fontWeight = FontWeight.Bold
                                        )
                                        Text(
                                            text = "Свободно",
                                            modifier = Modifier.weight(0.25f),
                                            style = MaterialTheme.typography.labelMedium,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                    zfsPoolRows.forEach { row ->
                                        Surface(
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .clickable { onAction(row.action) },
                                            color = zfsPoolCardBackgroundColor(row.freePercent),
                                            tonalElevation = 1.dp
                                        ) {
                                            Row(
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .padding(horizontal = 10.dp, vertical = 8.dp),
                                                verticalAlignment = Alignment.CenterVertically
                                            ) {
                                                Text(
                                                    text = row.host,
                                                    modifier = Modifier.weight(0.35f),
                                                    maxLines = 2,
                                                    overflow = TextOverflow.Ellipsis,
                                                    style = MaterialTheme.typography.bodySmall
                                                )
                                                Text(
                                                    text = row.pool,
                                                    modifier = Modifier.weight(0.4f),
                                                    maxLines = 2,
                                                    overflow = TextOverflow.Ellipsis,
                                                    style = MaterialTheme.typography.bodySmall
                                                )
                                                Text(
                                                    text = row.freePercentText,
                                                    modifier = Modifier
                                                        .weight(0.25f)
                                                        .clip(RoundedCornerShape(8.dp))
                                                        .background(
                                                            row.freePercent?.let(::zfsFreePercentBadgeBackgroundColor)
                                                                ?: MaterialTheme.colorScheme.surface
                                                        )
                                                        .padding(horizontal = 6.dp, vertical = 4.dp),
                                                    color = row.freePercent?.let(::zfsFreePercentColor)
                                                        ?: MaterialTheme.colorScheme.onSurface,
                                                    fontWeight = FontWeight.Bold,
                                                    style = MaterialTheme.typography.bodySmall
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        if (state.messageSource == "global" && state.message.isNotBlank()) {
                            Surface(
                                shape = RoundedCornerShape(10.dp),
                                tonalElevation = 1.dp,
                                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)
                            ) {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 10.dp, vertical = 8.dp),
                                    verticalArrangement = Arrangement.spacedBy(4.dp)
                                ) {
                                    state.message
                                        .lineSequence()
                                        .map { it.trim() }
                                        .filter { it.isNotBlank() }
                                        .forEach { line ->
                                            Text(
                                                text = buildReadableZfsPoolLine(line),
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant
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

    if (showZfsPoolHostsSettingsDialog) {
        val zfsPoolSettingsOptions = if (state.extensionMenuAction.startsWith("zfsp_")) {
            state.extensionMenuOptions
        } else {
            emptyList()
        }
        val zfsPoolAddAction = zfsPoolSettingsOptions
            .mapNotNull { option ->
                resolveMenuOptionAction(option).trim().takeIf { it.isNotBlank() }
            }
            .firstOrNull { action -> action == "zfsp_add" || action.startsWith("zfsp_add|") }
        AlertDialog(
            onDismissRequest = { showZfsPoolHostsSettingsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "⚙️ Хосты свободного места ZFS",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        IconButton(onClick = { showZfsPoolHostsSettingsDialog = false }) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = "Закрыть окно хостов ZFS-пулов"
                            )
                        }
                        if (zfsPoolAddAction != null) {
                            IconButton(
                                onClick = {
                                    zfsPoolHostAddAction = zfsPoolAddAction
                                    zfsPoolHostNameInput = ""
                                    zfsPoolHostIpInput = ""
                                    zfsPoolHostThresholdInput = "20"
                                    showZfsPoolHostAddDialog = true
                                }
                            ) {
                                Icon(
                                    imageVector = Icons.Filled.Add,
                                    contentDescription = "Добавить хост ZFS-пулов"
                                )
                            }
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
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val zfsPoolActions = zfsPoolSettingsOptions
                        .mapNotNull { option ->
                            val action = resolveMenuOptionAction(option)
                            val label = option.label?.trim().orEmpty()
                            if (label.isBlank() || action.isBlank()) null else label to action
                        }
                    val hostSettingsGroups = extractZfsPoolHostSettingsGroups(zfsPoolActions)
                    val commonActions = zfsPoolActions.filterNot { (label, action) ->
                        action.startsWith("zfsp_edit_name_") ||
                            action.startsWith("zfsp_edit_ip_") ||
                            action.startsWith("zfsp_edit_threshold_") ||
                            action.startsWith("zfsp_delete_") ||
                            action.startsWith("zfsp_toggle_") ||
                            action == "zfsp_add" ||
                            action.startsWith("zfsp_add|") ||
                            action == "zfs_pool_free_space_menu" ||
                            action == "back" ||
                            label.trim().lowercase() == "добавить хост" ||
                            label.trim().lowercase() == "назад"
                    }

                    if (state.isLoading && zfsPoolActions.isEmpty()) {
                        Text("Загружаем настройки хостов ZFS-пулов…")
                    } else if (zfsPoolActions.isEmpty()) {
                        Text("Настройки хостов ZFS-пулов пока недоступны.")
                    } else {
                        if (hostSettingsGroups.isNotEmpty()) {
                            Text(
                                text = "Хосты",
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.SemiBold
                            )
                            hostSettingsGroups.forEach { group ->
                                val monitoringEnabled = !isZfsMonitoringDisabled(group.toggleLabel)
                                val markerColor = if (monitoringEnabled) {
                                    Color(0xFF2E7D32)
                                } else {
                                    Color(0xFFC62828)
                                }
                                val markerLabel = if (monitoringEnabled) "Включен" else "Выключен"

                                ElevatedCard(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .combinedClickable(
                                            onClick = {
                                                zfsPoolSelectedHostName = group.hostName
                                                zfsPoolSelectedHostEditNameAction = group.editNameAction
                                                zfsPoolSelectedHostEditIpAction = group.editIpAction
                                                zfsPoolSelectedHostEditThresholdAction = group.editThresholdAction
                                                zfsPoolSelectedHostDeleteAction = group.deleteAction
                                                zfsPoolSelectedHostToggleAction = group.toggleAction
                                                showZfsPoolHostActionsDialog = true
                                            },
                                            onLongClick = {
                                                zfsPoolSelectedHostName = group.hostName
                                                zfsPoolSelectedHostEditNameAction = group.editNameAction
                                                zfsPoolSelectedHostEditIpAction = group.editIpAction
                                                zfsPoolSelectedHostEditThresholdAction = group.editThresholdAction
                                                zfsPoolSelectedHostDeleteAction = group.deleteAction
                                                zfsPoolSelectedHostToggleAction = group.toggleAction
                                                showZfsPoolHostActionsDialog = true
                                            }
                                        )
                                ) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(horizontal = 12.dp, vertical = 10.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                                    ) {
                                        Box(
                                            modifier = Modifier
                                                .size(10.dp)
                                                .clip(CircleShape)
                                                .background(markerColor)
                                        )
                                        Column(
                                            modifier = Modifier.weight(1f),
                                            verticalArrangement = Arrangement.spacedBy(2.dp)
                                        ) {
                                            Text(
                                                text = group.hostName,
                                                style = MaterialTheme.typography.titleSmall,
                                                fontWeight = FontWeight.SemiBold
                                            )
                                            Text(
                                                text = markerLabel,
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant
                                            )
                                        }
                                    }
                                }
                            }
                        }

                        commonActions.forEach { (label, action) ->
                            OutlinedButton(
                                onClick = { onAction(action) },
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
                                            onClick = {
                                                zfsSelectedHostName = hostGroup.hostName
                                                zfsSelectedHostEditAction = hostGroup.editAction
                                                zfsSelectedHostDeleteAction = hostGroup.deleteAction
                                                zfsSelectedHostToggleAction = hostGroup.toggleAction
                                                showZfsHostActionsDialog = true
                                            },
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

    if (showZfsPoolHostActionsDialog) {
        AlertDialog(
            onDismissRequest = { showZfsPoolHostActionsDialog = false },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("⚙️ ${zfsPoolSelectedHostName.ifBlank { "Хост ZFS-пулов" }}")
                    IconButton(onClick = { showZfsPoolHostActionsDialog = false }) {
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
                                zfsPoolHostEditNameInput = zfsPoolSelectedHostName
                                zfsPoolHostEditIpInput = ""
                                zfsPoolHostEditThresholdInput = ""
                                showZfsPoolHostEditDialog = true
                                showZfsPoolHostActionsDialog = false
                            },
                            enabled = zfsPoolSelectedHostEditNameAction.isNotBlank() ||
                                zfsPoolSelectedHostEditIpAction.isNotBlank() ||
                                zfsPoolSelectedHostEditThresholdAction.isNotBlank()
                        ) {
                            Icon(Icons.Filled.Edit, contentDescription = "Редактировать")
                        }
                        Text("Изм.", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                if (zfsPoolSelectedHostToggleAction.isNotBlank()) {
                                    onAction(zfsPoolSelectedHostToggleAction)
                                    onAction("zfsp_hosts_list")
                                }
                                showZfsPoolHostActionsDialog = false
                            },
                            enabled = zfsPoolSelectedHostToggleAction.isNotBlank()
                        ) {
                            Icon(Icons.Filled.PowerSettingsNew, contentDescription = "Вкл/выкл")
                        }
                        Text("Вкл/выкл", style = MaterialTheme.typography.labelSmall)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        FilledIconButton(
                            onClick = {
                                if (zfsPoolSelectedHostDeleteAction.isNotBlank()) {
                                    onAction(zfsPoolSelectedHostDeleteAction)
                                    onAction("zfsp_hosts_list")
                                }
                                showZfsPoolHostActionsDialog = false
                            },
                            enabled = zfsPoolSelectedHostDeleteAction.isNotBlank()
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

    if (showZfsPoolHostAddDialog) {
        AlertDialog(
            onDismissRequest = { showZfsPoolHostAddDialog = false },
            title = { Text("➕ Добавить хост ZFS-пулов") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = zfsPoolHostNameInput,
                        onValueChange = { zfsPoolHostNameInput = it },
                        label = { Text("Имя хоста") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = zfsPoolHostIpInput,
                        onValueChange = { zfsPoolHostIpInput = it },
                        label = { Text("IP адрес") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = zfsPoolHostThresholdInput,
                        onValueChange = { value ->
                            zfsPoolHostThresholdInput = value.filter { it.isDigit() }
                        },
                        label = { Text("Порог, % (1-95)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                val thresholdValue = zfsPoolHostThresholdInput.toIntOrNull()
                TextButton(
                    onClick = {
                        val addAction = zfsPoolHostAddAction.substringBefore("|").ifBlank { "zfsp_add" }
                        val encodedHostName = Uri.encode(zfsPoolHostNameInput.trim())
                        val encodedHostIp = Uri.encode(zfsPoolHostIpInput.trim())
                        val actionPayload = "$addAction|$encodedHostName|$encodedHostIp|$thresholdValue"
                        onAction(actionPayload)
                        onAction("zfsp_hosts_list")
                        showZfsPoolHostAddDialog = false
                        showZfsPoolHostsSettingsDialog = true
                    },
                    enabled = zfsPoolHostNameInput.isNotBlank() &&
                        zfsPoolHostIpInput.isNotBlank() &&
                        thresholdValue != null &&
                        thresholdValue in 1..95
                ) { Text("Добавить") }
            },
            dismissButton = {
                TextButton(onClick = {
                    showZfsPoolHostAddDialog = false
                }) {
                    Text("Отмена")
                }
            }
        )
    }

    if (showZfsPoolHostEditDialog) {
        AlertDialog(
            onDismissRequest = { showZfsPoolHostEditDialog = false },
            title = { Text("✏️ Редактирование хоста ZFS-пулов") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = zfsPoolHostEditNameInput,
                        onValueChange = { zfsPoolHostEditNameInput = it },
                        label = { Text("Имя хоста") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = zfsPoolHostEditIpInput,
                        onValueChange = { zfsPoolHostEditIpInput = it },
                        label = { Text("Новый IP (опционально)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = zfsPoolHostEditThresholdInput,
                        onValueChange = { value ->
                            zfsPoolHostEditThresholdInput = value.filter { it.isDigit() }
                        },
                        label = { Text("Новый порог, % (1-95, опционально)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                val thresholdValue = zfsPoolHostEditThresholdInput.toIntOrNull()
                val hasNameChange = zfsPoolSelectedHostEditNameAction.isNotBlank() &&
                    zfsPoolHostEditNameInput.trim().isNotBlank() &&
                    zfsPoolHostEditNameInput.trim() != zfsPoolSelectedHostName
                val hasIpChange = zfsPoolSelectedHostEditIpAction.isNotBlank() &&
                    zfsPoolHostEditIpInput.trim().isNotBlank()
                val hasThresholdChange = zfsPoolSelectedHostEditThresholdAction.isNotBlank() &&
                    zfsPoolHostEditThresholdInput.trim().isNotBlank() &&
                    thresholdValue != null &&
                    thresholdValue in 1..95
                TextButton(
                    onClick = {
                        if (hasNameChange) {
                            val actionPayload = "${zfsPoolSelectedHostEditNameAction}|${zfsPoolHostEditNameInput.trim()}"
                            onAction(actionPayload)
                        }
                        if (hasIpChange) {
                            val actionPayload = "${zfsPoolSelectedHostEditIpAction}|${zfsPoolHostEditIpInput.trim()}"
                            onAction(actionPayload)
                        }
                        if (hasThresholdChange) {
                            val actionPayload = "${zfsPoolSelectedHostEditThresholdAction}|$thresholdValue"
                            onAction(actionPayload)
                        }
                        onAction("zfsp_hosts_list")
                        showZfsPoolHostEditDialog = false
                    },
                    enabled = hasNameChange || hasIpChange || hasThresholdChange
                ) { Text("Сохранить") }
            },
            dismissButton = {
                TextButton(onClick = { showZfsPoolHostEditDialog = false }) {
                    Text("Отмена")
                }
            }
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
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(2.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CompactHeaderIconButton(
                            onClick = {
                                proxmoxServerNameInput = ""
                                showProxmoxServerAddDialog = true
                            },
                            contentDescription = "Добавить хост Proxmox"
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = null
                            )
                        }
                        CompactHeaderIconButton(
                            onClick = {
                                openTileHelpDialog(
                                    "Справка: плашка «proxmox»",
                                    "Плашка отвечает за мониторинг бэкапов Proxmox по хостам. " +
                                        "Внутри показываются карточки хостов; тап открывает карточку действий по хосту. " +
                                        "Настройка делается через ➕ (добавить хост) и ⚙️ (паттерны, по которым парсятся письма/статусы)."
                                )
                            },
                            contentDescription = "Справка по бэкапам Proxmox"
                        ) {
                            Text("?", fontWeight = FontWeight.Bold)
                        }
                        CompactHeaderIconButton(
                            onClick = {
                                patternDialogReturnAction = "settings_patterns_proxmox"
                                onExtensionsSettingsAction("settings_patterns_proxmox")
                                showProxmoxPatternsDialog = true
                            },
                            contentDescription = "Открыть паттерны Proxmox"
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = null
                            )
                        }
                        CompactHeaderIconButton(
                            onClick = { showProxmoxBackupsDialog = false },
                            contentDescription = "Закрыть бэкапы Proxmox"
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = null
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
                            text = "Тап по плашке хоста — список бэкапов\n" +
                                "Долгий тап — карточка действий (редактировать / вкл-выкл / удалить)",
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
                                                    val hostName = targetAction
                                                        .removePrefix("backup_host_")
                                                        .trim()
                                                    if (hostName.isNotBlank()) {
                                                        onFetchProxmoxHostBackups(hostName)
                                                    }
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
                        if (patternDialogReturnAction != "settings_patterns_proxmox") {
                            onExtensionsSettingsAction(patternDialogReturnAction)
                        }
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
                        if (patternDialogReturnAction != "settings_patterns_proxmox") {
                            onExtensionsSettingsAction(patternDialogReturnAction)
                        }
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
                        if (patternDialogReturnAction != "settings_patterns_proxmox") {
                            onExtensionsSettingsAction(patternDialogReturnAction)
                        }
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
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(2.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CompactHeaderIconButton(
                            onClick = {
                                dbEntryAddCategory = ""
                                dbEntryAddKeyInput = ""
                                dbEntryAddNameInput = ""
                                showDbOpsEntryAddDialog = true
                            },
                            contentDescription = "Добавить запись БД"
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Add,
                                contentDescription = null
                            )
                        }
                        CompactHeaderIconButton(
                            onClick = {
                                openTileHelpDialog(
                                    "Справка: плашка «БД»",
                                    "Плашка отвечает за мониторинг бэкапов баз данных. " +
                                        "Внутри отображаются карточки БД/хостов, откуда можно открыть статистику или карточку действий. " +
                                        "Настройка делается через ➕ (добавить запись БД) и ⚙️ (паттерны распознавания бэкапов БД)."
                                )
                            },
                            contentDescription = "Справка по бэкапам БД"
                        ) {
                            Text("?", fontWeight = FontWeight.Bold)
                        }
                        CompactHeaderIconButton(
                            onClick = {
                                onExtensionsSettingsAction("settings_patterns_db")
                                showDatabasePatternsDialog = true
                            },
                            contentDescription = "Открыть паттерны бэкапов БД"
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Settings,
                                contentDescription = null
                            )
                        }
                        CompactHeaderIconButton(
                            onClick = { showDatabaseBackupsDialog = false },
                            contentDescription = "Закрыть бэкапы БД"
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Close,
                                contentDescription = null
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
                            text = "Тап — список бэкапов БД, долгий тап — карточка действий\n(редактировать / вкл-выкл / удалить)",
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
                                                    showDatabaseBackupsDialog = false
                                                    selectedDatabaseBackupLabel = baseLabel
                                                    selectedProxmoxBackupLabel = ""
                                                    showProxmoxBackupStatsDialog = true
                                                    onAction(targetAction)
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

    if (state.proxmoxHostBackupsHost.isNotBlank()) {
        AlertDialog(
            onDismissRequest = { onCloseProxmoxHostBackups() },
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "🖥️ Бэкапы ${state.proxmoxHostBackupsHost}",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold
                    )
                    IconButton(onClick = { onCloseProxmoxHostBackups() }) {
                        Icon(
                            imageVector = Icons.Filled.Close,
                            contentDescription = "Закрыть"
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
                    if (state.isProxmoxHostBackupsLoading) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                strokeWidth = 2.dp
                            )
                            Text("Загружаем список бэкапов…")
                        }
                    } else if (state.proxmoxHostBackupsText.isNotBlank()) {
                        Text(state.proxmoxHostBackupsText)
                    } else {
                        Text("Нет данных по этому хосту")
                    }
                }
            },
            confirmButton = {}
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
                                onExtensionsSettingsAction("settings_backup_proxmox")
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
                                onExtensionsSettingsAction("settings_backup_proxmox")
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
                        onExtensionsSettingsAction("settings_backup_proxmox")
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
}
}
                        }
                    }
                }
            }
        }
    }
}
