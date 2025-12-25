"""
Shim-модуль для обратной совместимости.
Перенаправляет импорты в bot.handlers.commands.
"""

from bot.handlers.commands import *  # noqa: F401,F403
