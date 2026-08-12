package ru.monitoring.mobile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import ru.monitoring.mobile.api.AlertCategoryOption
import ru.monitoring.mobile.api.RegistryUser

// Личные настройки доставки владельца устройства (многопользовательский
// режим, core/users.py). Сбор данных общий для всех, персональна только
// доставка: получать ли отчёт и оповещения, какие уровни и категории,
// личные тихие часы.
//
// Устройство опознаётся сервером по device_id токена. Пока телефон не
// привязан к пользователю, действуют общесистемные настройки — тогда
// показываем блок привязки вместо переключателей.

private val alertLevelLabels = mapOf(
    "critical" to "🚨 Критические",
    "warning" to "⚠️ Предупреждения",
    "info" to "ℹ️ Информационные"
)

@Composable
private fun SettingRow(
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    ElevatedCard(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.elevatedCardColors()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(text = title, fontWeight = FontWeight.SemiBold)
                if (subtitle.isNotBlank()) {
                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Switch(checked = checked, onCheckedChange = onCheckedChange)
        }
    }
}

@Composable
fun DeviceLinkCard(
    deviceId: String,
    users: List<RegistryUser>,
    onLoadUsers: () -> Unit,
    onLinkTo: (Int) -> Unit,
    onCreateUser: (String) -> Unit
) {
    var newUserName by remember { mutableStateOf("") }

    ElevatedCard(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.elevatedCardColors()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("📱 Это устройство", fontWeight = FontWeight.Bold)
            Text(
                "device_id: ${deviceId.take(8)}…",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                "Привяжите устройство к пользователю, чтобы получать отчёт и " +
                    "оповещения по своим настройкам. Настройки сбора данных " +
                    "общие для всех и не меняются.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            OutlinedButton(onClick = onLoadUsers, modifier = Modifier.fillMaxWidth()) {
                Text("🔄 Загрузить список пользователей")
            }

            users.forEach { user ->
                val roleMark = if (user.role == "admin") " 👑" else ""
                OutlinedButton(
                    onClick = { onLinkTo(user.id) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("🔗 ${user.displayName.ifBlank { user.username }}$roleMark")
                }
            }

            OutlinedTextField(
                value = newUserName,
                onValueChange = { newUserName = it },
                label = { Text("Имя нового пользователя") },
                modifier = Modifier.fillMaxWidth()
            )
            Button(
                onClick = { onCreateUser(newUserName) },
                enabled = newUserName.isNotBlank(),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("➕ Создать и привязать это устройство")
            }
        }
    }
}

@Composable
fun MyNotificationsSection(
    user: RegistryUser?,
    levelOptions: List<String>,
    categoryOptions: List<AlertCategoryOption>,
    deviceId: String,
    users: List<RegistryUser>,
    onReportsEnabledChange: (Boolean) -> Unit,
    onAlertsEnabledChange: (Boolean) -> Unit,
    onQuietHoursEnabledChange: (Boolean) -> Unit,
    onToggleLevel: (String) -> Unit,
    onToggleCategory: (String) -> Unit,
    onSelectAllCategories: (Boolean) -> Unit,
    onLoadUsers: () -> Unit,
    onLinkTo: (Int) -> Unit,
    onCreateUser: (String) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        if (user == null) {
            Text(
                "👤 Это устройство не привязано к пользователю системы — " +
                    "действуют общесистемные настройки доставки.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            DeviceLinkCard(
                deviceId = deviceId,
                users = users,
                onLoadUsers = onLoadUsers,
                onLinkTo = onLinkTo,
                onCreateUser = onCreateUser
            )
            return@Column
        }

        val prefs = user.preferences
        val roleMark = if (user.role == "admin") " 👑" else ""
        Text(
            "👤 ${user.displayName.ifBlank { user.username }}$roleMark",
            fontWeight = FontWeight.Bold
        )
        Text(
            "Настройки личные: другие пользователи получают отчёт и " +
                "оповещения по своим. Сбор данных общий для всех.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        SettingRow(
            title = "Утренний/сводный отчёт",
            subtitle = "Приходит по расписанию сервера",
            checked = prefs?.reportsEnabled ?: true,
            onCheckedChange = onReportsEnabledChange
        )
        SettingRow(
            title = "Оповещения мониторинга",
            subtitle = "Недоступность серверов, ресурсы, расширения",
            checked = prefs?.alertsEnabled ?: true,
            onCheckedChange = onAlertsEnabledChange
        )

        Text("📶 Уровни оповещений", fontWeight = FontWeight.SemiBold)
        val selectedLevels = prefs?.alertLevels.orEmpty()
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            levelOptions.forEach { level ->
                FilterChip(
                    selected = level in selectedLevels,
                    onClick = { onToggleLevel(level) },
                    label = { Text(alertLevelLabels[level] ?: level) },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        Text("🧩 Категории оповещений", fontWeight = FontWeight.SemiBold)
        Text(
            "Снятые категории вам не приходят, но продолжают собираться " +
                "системой для остальных.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        val selectedCategories = prefs?.alertCategories.orEmpty()
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = { onSelectAllCategories(true) },
                modifier = Modifier.weight(1f)
            ) {
                Text("Все")
            }
            OutlinedButton(
                onClick = { onSelectAllCategories(false) },
                modifier = Modifier.weight(1f)
            ) {
                Text("Очистить")
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
            categoryOptions.forEach { category ->
                FilterChip(
                    selected = category.id in selectedCategories,
                    onClick = { onToggleCategory(category.id) },
                    label = { Text(category.label.ifBlank { category.id }) },
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }

        val quietStart = prefs?.quietStart ?: 22
        val quietEnd = prefs?.quietEnd ?: 8
        SettingRow(
            title = "Личные тихие часы",
            subtitle = "%02d:00–%02d:00 — критические приходят всегда".format(quietStart, quietEnd),
            checked = prefs?.quietHoursEnabled ?: false,
            onCheckedChange = onQuietHoursEnabledChange
        )

        DeviceLinkCard(
            deviceId = deviceId,
            users = users,
            onLoadUsers = onLoadUsers,
            onLinkTo = onLinkTo,
            onCreateUser = onCreateUser
        )
    }
}
