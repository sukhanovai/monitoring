package ru.monitoring.mobile.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val AppDarkColorScheme = darkColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF8CCBFF),
    onPrimary = androidx.compose.ui.graphics.Color(0xFF00344F),
    primaryContainer = androidx.compose.ui.graphics.Color(0xFF0F3A57),
    onPrimaryContainer = androidx.compose.ui.graphics.Color(0xFFCBE7FF),
    secondary = androidx.compose.ui.graphics.Color(0xFF7DE9C8),
    secondaryContainer = androidx.compose.ui.graphics.Color(0xFF18463A),
    onSecondaryContainer = androidx.compose.ui.graphics.Color(0xFFBAF7E5),
    tertiary = androidx.compose.ui.graphics.Color(0xFFE0B9FF),
    background = androidx.compose.ui.graphics.Color(0xFF0A1118),
    surface = androidx.compose.ui.graphics.Color(0xFF121C25),
    surfaceContainerHigh = androidx.compose.ui.graphics.Color(0xFF182635)
)

private val AppLightColorScheme = lightColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF005B8A),
    onPrimary = androidx.compose.ui.graphics.Color(0xFFFFFFFF),
    primaryContainer = androidx.compose.ui.graphics.Color(0xFFD0E9FF),
    onPrimaryContainer = androidx.compose.ui.graphics.Color(0xFF001C2E),
    secondary = androidx.compose.ui.graphics.Color(0xFF006C54),
    secondaryContainer = androidx.compose.ui.graphics.Color(0xFF95F8D9),
    onSecondaryContainer = androidx.compose.ui.graphics.Color(0xFF002117),
    tertiary = androidx.compose.ui.graphics.Color(0xFF7F4FA2),
    background = androidx.compose.ui.graphics.Color(0xFFF1F6FB),
    surface = androidx.compose.ui.graphics.Color(0xFFFFFFFF),
    surfaceContainerHigh = androidx.compose.ui.graphics.Color(0xFFE1ECF6)
)

@Composable
fun MonitoringTheme(
    darkTheme: Boolean,
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = if (darkTheme) AppDarkColorScheme else AppLightColorScheme,
        content = content
    )
}
