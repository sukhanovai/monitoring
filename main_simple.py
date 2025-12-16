#!/usr/bin/env python3
"""
Simple main.py for testing new structure
Упрощенный main.py для тестирования новой структуры
"""

import sys
sys.path.insert(0, '/opt/monitoring')

from lib.logging import debug_log, setup_logging
from config.settings import DEBUG_MODE

def main():
    """Упрощенная главная функция"""
    print("🚀 Тестирование новой структуры...")
    
    # Настройка логирования
    setup_logging()
    debug_log("✅ Система логирования работает")
    
    # Проверка модулей
    try:
        from modules.availability import availability_checker
        from modules.resources import resources_checker
        from modules.morning_report import morning_report
        from modules.targeted_checks import targeted_checks
        from core.monitor import monitor
        
        print("✅ Все модули загружены успешно")
        
        # Тест загрузки серверов
        from extensions.server_checks import initialize_servers
        servers = initialize_servers()
        print(f"✅ Загружено {len(servers)} серверов")
        
        # Тест монитора
        print(f"✅ Монитор инициализирован, статус: {monitor.get_status()}")
        
        # Тест targeted_checks
        if servers:
            server = servers[0]
            server_id = server.get('ip')
            success, _, message = targeted_checks.check_single_server_availability(server_id)
            print(f"✅ Точечная проверка: {'успешно' if success else 'ошибка'}")
        
        print("\n🎉 Новая структура готова к использованию!")
        print("Для запуска полной системы выполните:")
        print("1. Обновите monitor_core.py: python3 migrate_monitor_core.py")
        print("2. Запустите основной main.py: python3 main.py")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()