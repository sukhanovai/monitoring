"""
Быстрый тест новой структуры
"""

import sys
import os

# Очищаем sys.path
sys.path = [p for p in sys.path if '/opt/monitoring' not in p]

print("=" * 50)
print("БЫСТРЫЙ ТЕСТ СТРУКТУРЫ")
print("=" * 50)

# Тест 1: Старая структура
print("\n1. Тест старой структуры:")
try:
    sys.path.insert(0, '/opt/monitoring')
    from core_utils import server_checker
    print(f"✅ core_utils.server_checker: {server_checker}")
except Exception as e:
    print(f"❌ Ошибка: {e}")

# Тест 2: Новая структура
print("\n2. Тест новой структуры:")
try:
    sys.path.insert(0, '/opt/monitoring/app')
    import app
    print(f"✅ app импортирован: версия {app.__version__}")
    print(f"✅ app.server_checker: {app.server_checker}")
    print(f"✅ app.logger: {app.logger}")
    
    # Тест функций
    from app.utils.common import progress_bar
    print(f"✅ progress_bar(75): {progress_bar(75)}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

# Тест 3: Прямой импорт модулей
print("\n3. Тест прямого импорта:")
try:
    sys.path.insert(0, '/opt/monitoring/app')
    from app.core.checker import ServerChecker
    from app.utils.common import format_duration
    
    checker = ServerChecker()
    print(f"✅ ServerChecker создан: {checker}")
    print(f"✅ format_duration(3665): {format_duration(3665)}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n" + "=" * 50)
print("ТЕСТ ЗАВЕРШЕН")
print("=" * 50)
