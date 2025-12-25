"""
Shim-модуль для обратной совместимости.
Перенаправляет импорты в bot.handlers.extensions.
"""

from bot.handlers.extensions import *  # noqa: F401,F403
