#!/usr/bin/env python3
"""
Тестирование утреннего отчета
"""

import sys
import os
sys.path.insert(0, '/opt/monitoring')

from monitor_core import test_morning_report, get_current_server_status, servers

def debug_servers():
    """Отладочная информация о серверах"""
    print(f"🧪 Отладочная информация:")
    print(f"• Всего серверов в глобальной переменной: {len(servers) if servers else 0}")
    
    # Проверим текущий статус
    status = get_current_server_status()
    print(f"• Результат проверки: {len(status['ok'])} доступно, {len(status['failed'])} недоступно")
    
    # Выведем несколько серверов для примера
    if status['ok']:
        print("• Примеры доступных серверов:")
        for server in status['ok'][:3]:
            print(f"  - {server['name']} ({server['ip']})")
    
    if status['failed']:
        print("• Примеры недоступных серверов:")
        for server in status['failed'][:3]:
            print(f"  - {server['name']} ({server['ip']})")

if __name__ == "__main__":
    print("🧪 Запуск теста утреннего отчета...")
    debug_servers()
    print("---")
    test_morning_report()
    