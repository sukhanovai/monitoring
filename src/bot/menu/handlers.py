"""
Shim-модуль для обратной совместимости.
Перенаправляет импорты в bot.menu.handlers.
"""

from bot.menu.handlers import *  # noqa: F401,F403
