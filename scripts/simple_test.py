"""
Абсолютно простой тест
"""

import sys
import os

print("1. Проверка путей Python:")
print(f"   Текущий каталог: {os.getcwd()}")
print(f"   Python path: {sys.path}")

print("\n2. Пробуем импортировать модули по отдельности:")

# Пробуем импортировать common.py напрямую
common_path = "/opt/monitoring/app/utils/common.py"
if os.path.exists(common_path):
    print(f"✅ common.py существует: {common_path}")
    
    # Создаем отдельный namespace для импорта
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("common", common_path)
    common_module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(common_module)
        print(f"✅ common.py загружен")
        print(f"   Функции: {[x for x in dir(common_module) if not x.startswith('_')]}")
    except Exception as e:
        print(f"❌ Ошибка загрузки common.py: {e}")
else:
    print(f"❌ common.py не найден")

# Пробуем импортировать checker.py напрямую
checker_path = "/opt/monitoring/app/core/checker.py"
if os.path.exists(checker_path):
    print(f"\n✅ checker.py существует: {checker_path}")
    
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("checker", checker_path)
    checker_module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(checker_module)
        print(f"✅ checker.py загружен")
        if hasattr(checker_module, 'ServerChecker'):
            print(f"   ServerChecker класс найден")
            checker = checker_module.ServerChecker()
            print(f"   Экземпляр создан: {checker}")
    except Exception as e:
        print(f"❌ Ошибка загрузки checker.py: {e}")
else:
    print(f"\n❌ checker.py не найден")
