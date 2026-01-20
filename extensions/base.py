"""
/extensions/base.py
Server Monitoring System v7.3.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Extensions interface
Система мониторинга серверов
Версия: 7.3.0
Автор: Александр Суханов (c)
Лицензия: MIT
Интерфейс расширений
"""

from abc import ABC, abstractmethod

class Extension(ABC):
    @abstractmethod
    def enable(self):
        """Enable the extension"""
        pass
    
    @abstractmethod
    def disable(self):
        """Disable the extension"""
        pass
    
    @abstractmethod
    def get_handlers(self):
        """Get bot handlers for this extension"""
        pass
    
    @abstractmethod
    def get_menu_commands(self):
        """Get menu commands for this extension"""
        pass
