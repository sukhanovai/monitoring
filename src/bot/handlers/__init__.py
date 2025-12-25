"""
Shim-пакет для обратной совместимости.
Перенаправляет импорты в bot.handlers.
"""

from bot.handlers import *  # noqa: F401,F403
from bot.handlers import __all__  # noqa: F401
