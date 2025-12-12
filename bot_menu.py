"""
Server Monitoring System - Совместимость со старым кодом
DEPRECATED: Используйте модули из app.bot.*
"""

import warnings
warnings.warn("bot_menu.py устарел. Используйте app.bot.menus", DeprecationWarning)

# Реэкспорт для обратной совместимости
from app.bot.menus import (
    setup_menu_commands as setup_menu,
    create_main_menu,
    get_start_message,
    get_help_message
)

from app.bot.callbacks import callback_router
from app.bot.handlers import get_handlers as get_handlers_compat

# Для обратной совместимости
get_callback_handlers = callback_router.get_handlers