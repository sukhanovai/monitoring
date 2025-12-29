#!/usr/bin/env python3
"""
/modules/improved_mail_monitor.py
Server Monitoring System v6.0.6
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Mailbox monitoring
Система мониторинга серверов
Версия: 6.0.6
Автор: Александр Суханов (c)
Лицензия: MIT
Мониторинг почтового ящика
"""

import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.mail_monitor import main


if __name__ == "__main__":
    main()
    
