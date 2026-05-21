package ru.monitoring.mobile

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ru.monitoring.mobile.api.ExtensionItem

private enum class ExtensionsFilter { All, Enabled, Disabled }

@Composable
fun ExtensionsSection(
    items: List<ExtensionItem>,
    onToggleExtension: (String, Boolean) -> Unit,
    onEnableAll: (() -> Unit)? = null,
    onDisableAll: (() -> Unit)? = null
) {
    val total = items.size
    val enabledCount = items.count { it.enabled }
    val disabledCount = total - enabledCount

    var searchQuery by rememberSaveable { mutableStateOf("") }
    var filter by rememberSaveable { mutableStateOf(ExtensionsFilter.All) }

    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        ExtensionsSummaryCard(
            total = total,
            enabled = enabledCount,
            disabled = disabledCount,
            filter = filter,
            onFilterChange = { filter = it },
            onEnableAll = onEnableAll,
            onDisableAll = onDisableAll
        )

        if (total == 0) {
            Text(
                "Список расширений пуст",
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            return@Column
        }

        OutlinedTextField(
            value = searchQuery,
            onValueChange = { searchQuery = it },
            label = { Text("Поиск расширений") },
            placeholder = { Text("Название или описание") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
            leadingIcon = {
                Icon(Icons.Filled.Search, contentDescription = "Поиск")
            },
            trailingIcon = {
                if (searchQuery.isNotBlank()) {
                    IconButton(onClick = { searchQuery = "" }) {
                        Icon(Icons.Filled.Close, contentDescription = "Очистить")
                    }
                }
            }
        )

        val visible = items.filter { item ->
            val matchFilter = when (filter) {
                ExtensionsFilter.All -> true
                ExtensionsFilter.Enabled -> item.enabled
                ExtensionsFilter.Disabled -> !item.enabled
            }
            val q = searchQuery.trim()
            val matchSearch = q.isEmpty() ||
                item.name.contains(q, ignoreCase = true) ||
                item.description.contains(q, ignoreCase = true)
            matchFilter && matchSearch
        }

        if (visible.isEmpty()) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp)),
                color = MaterialTheme.colorScheme.surfaceVariant,
                contentColor = MaterialTheme.colorScheme.onSurfaceVariant
            ) {
                Text(
                    "Ничего не найдено по текущему фильтру",
                    modifier = Modifier.padding(12.dp),
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                visible.forEach { item ->
                    ExtensionRow(item = item, onToggleExtension = onToggleExtension)
                }
            }
        }
    }
}

@Composable
private fun ExtensionsSummaryCard(
    total: Int,
    enabled: Int,
    disabled: Int,
    filter: ExtensionsFilter,
    onFilterChange: (ExtensionsFilter) -> Unit,
    onEnableAll: (() -> Unit)?,
    onDisableAll: (() -> Unit)?
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp)),
        color = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
        tonalElevation = 2.dp
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                FilterButton(
                    label = "Все",
                    value = total,
                    selected = filter == ExtensionsFilter.All,
                    selectedContainer = MaterialTheme.colorScheme.secondaryContainer,
                    selectedContent = MaterialTheme.colorScheme.onSecondaryContainer,
                    onClick = { onFilterChange(ExtensionsFilter.All) },
                    modifier = Modifier.weight(1f)
                )
                FilterButton(
                    label = "Включено",
                    value = enabled,
                    selected = filter == ExtensionsFilter.Enabled,
                    selectedContainer = MaterialTheme.colorScheme.tertiaryContainer,
                    selectedContent = MaterialTheme.colorScheme.onTertiaryContainer,
                    onClick = { onFilterChange(ExtensionsFilter.Enabled) },
                    modifier = Modifier.weight(1f)
                )
                FilterButton(
                    label = "Выключено",
                    value = disabled,
                    selected = filter == ExtensionsFilter.Disabled,
                    selectedContainer = MaterialTheme.colorScheme.errorContainer,
                    selectedContent = MaterialTheme.colorScheme.onErrorContainer,
                    onClick = { onFilterChange(ExtensionsFilter.Disabled) },
                    modifier = Modifier.weight(1f)
                )
            }
            if (onEnableAll != null || onDisableAll != null) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (onEnableAll != null) {
                        Button(
                            onClick = onEnableAll,
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(12.dp),
                            enabled = disabled > 0,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                                contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                            )
                        ) {
                            Text("Включить все", fontWeight = FontWeight.SemiBold)
                        }
                    }
                    if (onDisableAll != null) {
                        Button(
                            onClick = onDisableAll,
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(12.dp),
                            enabled = enabled > 0,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.errorContainer,
                                contentColor = MaterialTheme.colorScheme.onErrorContainer
                            )
                        ) {
                            Text("Отключить все", fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilterButton(
    label: String,
    value: Int,
    selected: Boolean,
    selectedContainer: Color,
    selectedContent: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val container = if (selected) selectedContainer else MaterialTheme.colorScheme.surface
    val content = if (selected) selectedContent else MaterialTheme.colorScheme.onSurface
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .clickable(onClick = onClick),
        color = container,
        contentColor = content,
        tonalElevation = if (selected) 3.dp else 1.dp
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 10.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                value.toString(),
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp
            )
            Text(
                label,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Normal
            )
        }
    }
}

@Composable
private fun ExtensionRow(
    item: ExtensionItem,
    onToggleExtension: (String, Boolean) -> Unit
) {
    val container = if (item.enabled) {
        MaterialTheme.colorScheme.tertiaryContainer
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }
    val content = if (item.enabled) {
        MaterialTheme.colorScheme.onTertiaryContainer
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    ElevatedCard(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(
            containerColor = container,
            contentColor = content
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Text(
                    item.name,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 15.sp
                )
                if (item.description.isNotBlank()) {
                    Text(
                        item.description,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                Text(
                    if (item.enabled) "включено" else "выключено",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.SemiBold
                )
            }
            Switch(
                checked = item.enabled,
                onCheckedChange = { newValue -> onToggleExtension(item.id, newValue) },
                colors = SwitchDefaults.colors(
                    checkedThumbColor = MaterialTheme.colorScheme.onTertiaryContainer,
                    checkedTrackColor = MaterialTheme.colorScheme.tertiary,
                    uncheckedThumbColor = MaterialTheme.colorScheme.onSurfaceVariant,
                    uncheckedTrackColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    }
}
