"""
Shim-модуль для обратной совместимости.
Перенаправляет импорты в bot.handlers.base.
"""

from bot.handlers.base import *  # noqa: F401,F403
