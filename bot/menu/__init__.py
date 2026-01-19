"""
/bot/menu/__init__.py
Server Monitoring System v7.2.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Menu exports
Система мониторинга серверов
Версия: 7.2.3
Автор: Александр Суханов (c)
Лицензия: MIT
Экспорт функций меню
"""

from bot.menu.builder import main_menu
from bot.menu.handlers import show_main_menu

__all__ = ["main_menu", "show_main_menu"]