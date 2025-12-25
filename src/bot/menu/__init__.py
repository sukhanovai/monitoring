"""
Shim-пакет для обратной совместимости.
Перенаправляет импорты в bot.menu.
"""

from bot.menu import *  # noqa: F401,F403
from bot.menu import __all__  # noqa: F401
