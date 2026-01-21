"""
/bot/menu/__init__.py
Server Monitoring System v8.1.10
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu exports
Система мониторинга серверов
Версия: 8.1.10
Автор: Александр Суханов (c)
Лицензия: MIT
Экспорт функций меню
"""

from bot.menu.builder import main_menu
from bot.menu.handlers import show_main_menu

__all__ = ["main_menu", "show_main_menu"]