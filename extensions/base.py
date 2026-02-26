"""
/extensions/base.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Extensions interface
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РРЅС‚РµСЂС„РµР№СЃ СЂР°СЃС€РёСЂРµРЅРёР№
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
