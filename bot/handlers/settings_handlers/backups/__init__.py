"""
/bot/handlers/settings_handlers/backups/__init__.py
Server Monitoring System v8.62.65
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Backup-семейство UI Telegram-бота (PR7d серии оптимизации).
Система мониторинга серверов
Версия: 8.62.65
Автор: Александр Суханов (c)
Лицензия: MIT
Подпакет настроек разных типов резервных копий, выделенный из
bot/handlers/settings_handlers/_legacy.py. Каждый модуль —
самостоятельная UI-семья: proxmox vzdump, ZFS snapshot transfer,
позже сюда же поедут db / mail.
"""

from __future__ import annotations
