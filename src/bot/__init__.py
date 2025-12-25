"""
Shim-пакет для обратной совместимости.
Перенаправляет импорты в bot.
"""

from bot import *  # noqa: F401,F403
from bot import __all__  # noqa: F401
