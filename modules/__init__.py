"""
/app/modules/__init__.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Monitoring system modules
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»Рё СЃРёСЃС‚РµРјС‹ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
"""

from .targeted_checks import targeted_checks

__all__ = ['targeted_checks']