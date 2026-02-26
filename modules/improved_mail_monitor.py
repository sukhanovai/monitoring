#!/usr/bin/env python3
"""
/modules/improved_mail_monitor.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mailbox monitoring
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРЅРёС‚РѕСЂРёРЅРі РїРѕС‡С‚РѕРІРѕРіРѕ СЏС‰РёРєР°
"""

import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.mail_monitor import main


if __name__ == "__main__":
    main()
    
