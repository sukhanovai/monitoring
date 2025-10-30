#!/usr/bin/env python3
"""
Тестирование утреннего отчета
"""

import sys
import os
sys.path.insert(0, '/opt/monitoring')

from monitor_core import test_morning_report

if __name__ == "__main__":
    print("🧪 Запуск теста утреннего отчета...")
    test_morning_report()
    