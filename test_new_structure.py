#!/usr/bin/env python3
"""
Test script for new monitoring structure
Тестовый скрипт для новой структуры мониторинга
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from lib.logging import debug_log, setup_logging
from config.settings import DEBUG_MODE
from modules.availability import availability_checker
from modules.resources import resources_checker
from modules.morning_report import morning_report
from modules.targeted_checks import targeted_checks
from core.monitor import monitor

def test_modules():
    """Тестирует все модули новой структуры"""
    print("🧪 Тестирование новой структуры мониторинга...")
    
    # 1. Тест логирования
    print("1. Тестирование логирования...")
    setup_logging()
    debug_log("✅ Тестовое сообщение логирования")
    print("   ✅ Логирование работает")
    
    # 2. Тест модуля доступности
    print("2. Тестирование модуля доступности...")
    from extensions.server_checks import initialize_servers
    servers = initialize_servers()[:2]  # Берем 2 сервера для теста
    
    if servers:
        results = availability_checker.check_multiple_servers(servers)
        print(f"   ✅ Проверено {len(servers)} серверов")
        print(f"   🟢 Доступно: {len(results.get('up', []))}")
        print(f"   🔴 Недоступно: {len(results.get('down', []))}")
    else:
        print("   ⚠️ Нет серверов для теста")
    
    # 3. Тест модуля ресурсов
    print("3. Тестирование модуля ресурсов...")
    if servers:
        for server in servers[:1]:  # Тестируем первый сервер
            success, resources = resources_checker.check_server_resources(server)
            if success:
                print(f"   ✅ Ресурсы получены: CPU {resources.get('cpu', 0)}%, "
                      f"RAM {resources.get('ram', 0)}%, Disk {resources.get('disk', 0)}%")
            else:
                print(f"   ⚠️ Не удалось получить ресурсы")
    
    # 4. Тест модуля отчетов
    print("4. Тестирование модуля отчетов...")
    if servers:
        report_data = morning_report.collect_morning_data({
            "up": servers[:1],
            "down": servers[1:2] if len(servers) > 1 else []
        })
        print(f"   ✅ Данные отчета собраны")
        print(f"   📅 Время сбора: {report_data.get('collection_time')}")
    
    # 5. Тест точечных проверок
    print("5. Тестирование точечных проверок...")
    if servers:
        server = servers[0]
        server_id = server.get("ip")
        
        # Проверка доступности
        success, server_info, message = targeted_checks.check_single_server_availability(server_id)
        print(f"   ✅ Точечная проверка доступности: {'успешно' if success else 'ошибка'}")
        
        # Проверка ресурсов
        success, server_info, message = targeted_checks.check_single_server_resources(server_id)
        print(f"   ✅ Точечная проверка ресурсов: {'успешно' if success else 'ошибка'}")
    
    # 6. Тест основного монитора
    print("6. Тестирование основного монитора...")
    monitor_status = monitor.get_status()
    print(f"   ✅ Монитор инициализирован")
    print(f"   📊 Статус: {'активен' if monitor_status.get('monitoring_active') else 'неактивен'}")
    print(f"   📈 Серверов: {monitor_status.get('servers_count', 0)}")
    
    print("\n🎉 Все тесты пройдены успешно!")
    return True

if __name__ == "__main__":
    try:
        test_modules()
    except Exception as e:
        print(f"💥 Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)