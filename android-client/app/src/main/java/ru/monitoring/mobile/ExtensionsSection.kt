package ru.monitoring.mobile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import ru.monitoring.mobile.api.ExtensionItem

@Composable
fun ExtensionsSection(
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
                Column(
                    modifier = Modifier.padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text(item.name, fontWeight = FontWeight.Bold)
                    if (item.description.isNotBlank()) {
                        Text(item.description)
                    }
                    Text("Статус: ${if (item.enabled) "Включено" else "Отключено"}")
                    Button(
                        onClick = { onToggleExtension(item.id, !item.enabled) },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (item.enabled) {
                                MaterialTheme.colorScheme.errorContainer
                            } else {
                                MaterialTheme.colorScheme.secondaryContainer
                            },
                            contentColor = if (item.enabled) {
                                MaterialTheme.colorScheme.onErrorContainer
                            } else {
                                MaterialTheme.colorScheme.onSecondaryContainer
                            }
                        )
                    ) {
                        Text(
                            if (item.enabled) "Выключить" else "Включить",
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }
        }
    }
}
