package ru.monitoring.mobile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import ru.monitoring.mobile.api.ReportExtensionOption

// Мультивыбор расширений для состава утреннего/ручного отчёта.
// Базовые данные мониторинга доступности входят в отчёт всегда; здесь
// пользователь отмечает, сведения каких расширений добавлять дополнительно.
@Composable
fun ReportExtensionsSection(
    options: List<ReportExtensionOption>,
    onToggle: (String, Boolean) -> Unit
) {
    if (options.isEmpty()) {
        Text(
            "Список расширений недоступен. Потяните, чтобы обновить настройки.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        return
    }

    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        options.forEach { option ->
            ElevatedCard(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.elevatedCardColors()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = option.label.ifBlank { option.name.ifBlank { option.id } },
                            fontWeight = FontWeight.SemiBold
                        )
                        if (option.description.isNotBlank()) {
                            Text(
                                text = option.description,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        if (!option.extensionEnabled) {
                            Text(
                                text = "⚠️ Расширение выключено — данные не попадут в отчёт",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                    Switch(
                        checked = option.included,
                        onCheckedChange = { checked -> onToggle(option.id, checked) }
                    )
                }
            }
        }
    }
}
