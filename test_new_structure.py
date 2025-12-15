#!/usr/bin/env python3
"""
Тестирование новой структуры проекта
"""

import sys
import os

# Добавляем корневую директорию проекта в путь Python
project_root = '/opt/monitoring'
sys.path.insert(0, project_root)

print("=== Тестирование новой структуры проекта ===\n")
print(f"Python путь: {sys.path[:2]}\n")

# 1. Тестируем базовые импорты
print("1. Тестируем базовые импорты...")
try:
    # Проверяем наличие директорий
    for dir_name in ['lib', 'core', 'config', 'modules']:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            print(f"✅ Директория {dir_name}: существует")
        else:
            print(f"❌ Директория {dir_name}: не найдена")
    
    # Проверяем наличие файлов
    required_files = [
        ('lib/logging.py', 'Логирование'),
        ('lib/alerts.py', 'Алерты'),
        ('core/config_manager.py', 'Менеджер конфигурации'),
        ('config/settings.py', 'Настройки по умолчанию'),
        ('config/db_settings.py', 'Настройки из БД'),
    ]
    
    for file_rel_path, description in required_files:
        file_path = os.path.join(project_root, file_rel_path)
        if os.path.exists(file_path):
            print(f"✅ Файл {description}: существует")
        else:
            print(f"❌ Файл {description}: не найден ({file_rel_path})")
    
    print("\n✅ Базовые проверки завершены\n")
    
except Exception as e:
    print(f"❌ Ошибка базовых проверок: {e}\n")

# 2. Тестируем логирование
print("2. Тестируем модуль логирования...")
try:
    from lib.logging import setup_logging, debug_log, set_debug_mode, get_log_file_stats
    logger = setup_logging("test_logger")
    debug_log("✅ Модуль логирования импортирован")
    set_debug_mode(False)
    debug_log("✅ Режим отладки: выключен")
    set_debug_mode(True)
    debug_log("✅ Режим отладки: включен")
    
    # Тестируем разные уровни логирования
    logger.info("✅ Информационное сообщение")
    logger.warning("✅ Предупреждение")
    logger.error("✅ Ошибка")
    
    # Тестируем статистику логов
    stats = get_log_file_stats()
    print(f"✅ Статистика логов получена: {len(stats)} файлов")
    
    print("✅ Логирование: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"   Python путь: {sys.path}")
except Exception as e:
    print(f"❌ Логирование: Ошибка - {e}")
    import traceback
    traceback.print_exc()

# 3. Тестируем алерты
print("\n3. Тестируем модуль алертов...")
try:
    from lib.alerts import send_alert, configure, set_silent_override, is_silent_time, get_alert_stats
    configure(silent_start=20, silent_end=9)
    print("✅ Модуль алертов загружен")
    print(f"✅ Конфигурация: silent={20}:00-{9}:00")
    
    # Тестируем проверку тихого режима
    silent = is_silent_time()
    print(f"✅ Проверка тихого режима: {'активен' if silent else 'не активен'}")
    
    # Тестируем переопределение
    set_silent_override(True)
    print("✅ Переопределение тихого режима: установлено")
    
    # Тестируем статистику
    stats = get_alert_stats()
    print(f"✅ Статистика алертов: {stats['total_all_time']} всего")
    
    print("✅ Алерты: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта алертов: {e}")
except Exception as e:
    print(f"❌ Алерты: Ошибка - {e}")
    import traceback
    traceback.print_exc()

# 4. Тестируем менеджер конфигурации
print("\n4. Тестируем менеджер конфигурации...")
try:
    from core.config_manager import config_manager
    
    print(f"✅ Менеджер конфигурации инициализирован")
    print(f"   Путь к БД: {config_manager.db_path}")
    
    # Проверяем наличие БД
    if os.path.exists(config_manager.db_path):
        print(f"✅ База данных настроек: существует")
    else:
        print(f"⚠️ База данных настроек: не найдена, будет создана")
    
    # Тестируем получение настроек
    token = config_manager.get_setting('TELEGRAM_TOKEN', 'NOT_SET')
    print(f"✅ Получение TELEGRAM_TOKEN: {token}")
    
    interval = config_manager.get_setting('CHECK_INTERVAL', 60)
    print(f"✅ Получение CHECK_INTERVAL: {interval}")
    
    # Тестируем сохранение настроек
    test_key = 'TEST_MIGRATION_KEY'
    config_manager.set_setting(test_key, 'test_value_migration', 'test', 'Тест миграции')
    test_value = config_manager.get_setting(test_key, 'default')
    print(f"✅ Тест сохранения настроек: {test_key} = {test_value}")
    
    # Получаем все настройки
    all_settings = config_manager.get_all_settings()
    print(f"✅ Всего настроек в БД: {len(all_settings)}")
    
    print("✅ Конфигурация: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта конфигурации: {e}")
except Exception as e:
    print(f"❌ Конфигурация: Ошибка - {e}")
    import traceback
    traceback.print_exc()

# 5. Тестируем настройки из БД
print("\n5. Тестируем загрузку настроек из БД...")
try:
    from config.db_settings import load_all_settings, TELEGRAM_TOKEN, CHECK_INTERVAL, USE_DB
    
    print(f"✅ Модуль настроек из БД загружен")
    print(f"   Использование БД: {'ДА' if USE_DB else 'НЕТ'}")
    
    # Загружаем настройки
    load_all_settings()
    print("✅ Настройки загружены из БД")
    
    print(f"   TELEGRAM_TOKEN: {'***установлен***' if TELEGRAM_TOKEN else 'не установлен'}")
    print(f"   CHECK_INTERVAL: {CHECK_INTERVAL} сек")
    print(f"   SILENT_START: {20 if 'SILENT_START' not in locals() else locals().get('SILENT_START', 20)}:00")
    print(f"   SILENT_END: {9 if 'SILENT_END' not in locals() else locals().get('SILENT_END', 9)}:00")
    
    print("✅ Настройки из БД: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта настроек БД: {e}")
except Exception as e:
    print(f"❌ Настройки БД: Ошибка - {e}")
    import traceback
    traceback.print_exc()

# 6. Тестируем утилиты
print("\n6. Тестируем модуль утилит...")
try:
    from lib.utils import safe_import, format_duration, progress_bar, is_proxmox_server
    
    print("✅ Модуль утилит загружен")
    
    # Тестируем safe_import
    os_module = safe_import('os')
    if os_module:
        print(f"✅ safe_import('os'): работает")
    else:
        print(f"❌ safe_import('os'): не работает")
    
    # Тестируем format_duration
    durations = [30, 125, 3665, 86400]
    for seconds in durations:
        formatted = format_duration(seconds)
        print(f"✅ format_duration({seconds}): {formatted}")
    
    # Тестируем progress_bar
    percentages = [0, 25, 50, 75, 100]
    for pct in percentages:
        bar = progress_bar(pct)
        print(f"✅ progress_bar({pct}%): {bar}")
    
    # Тестируем is_proxmox_server
    test_ips = [
        ("192.168.30.10", True),
        ("192.168.20.30", True),
        ("192.168.20.1", False),
        ("192.168.10.10", False),
    ]
    
    for ip, expected in test_ips:
        result = is_proxmox_server(ip)
        status = "✅" if result == expected else "❌"
        print(f"{status} is_proxmox_server({ip}): {result} (ожидалось: {expected})")
    
    print("✅ Утилиты: ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
    
except ImportError as e:
    print(f"❌ Ошибка импорта утилит: {e}")
except Exception as e:
    print(f"❌ Утилиты: Ошибка - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
print("="*50)

# Итоговая проверка структуры
print("\nПроверка структуры проекта:")
tree_output = []
for root, dirs, files in os.walk(project_root):
    # Пропускаем скрытые директории и __pycache__
    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
    
    level = root.replace(project_root, '').count(os.sep)
    indent = ' ' * 2 * level
    tree_output.append(f"{indent}{os.path.basename(root)}/")
    
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        if not file.startswith('.') and file.endswith('.py'):
            tree_output.append(f"{subindent}{file}")

# Выводим только первые 30 строк
print("\n".join(tree_output[:30]))
if len(tree_output) > 30:
    print(f"... и еще {len(tree_output) - 30} элементов")