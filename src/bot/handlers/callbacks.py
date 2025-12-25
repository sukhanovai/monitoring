"""
Shim-модуль для обратной совместимости.
Перенаправляет импорты в bot.handlers.callbacks.
"""

from bot.handlers.callbacks import *  # noqa: F401,F403
