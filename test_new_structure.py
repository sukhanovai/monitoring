"""
Server Monitoring System v4.0.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Тестирование новой структуры без влияния на рабочую систему
Версия: 4.0.0
"""

import sys
import os

def test_new_structure():
    """Тестирует новую структуру"""
    print("🧪 Тестирование новой структуры...")
    
    # Тест 1: Импорт новой структуры
    try:
        sys.path.insert(0, '/opt/monitoring/app')
        from core.checker import ServerChecker
        from utils.common import progress_bar, format_duration
        
        print("✅ 1. Импорт новой структуры: УСПЕХ")
        
        # Тест 2: Создание экземпляра
        checker = ServerChecker()
        print(f"✅ 2. Создание ServerChecker: {checker}")
        
        # Тест 3: Работа функций
        bar = progress_bar(75)
        duration = format_duration(3665)
        print(f"✅ 3. Функции: bar={bar}, duration={duration}")
        
        # Тест 4: Совместимость с app/__init__.py
        from app import server_checker as app_checker
        print(f"✅ 4. Импорт из app/: {app_checker}")
        
        return True
        
    except Exception as e:
        print(f"❌ Тест провален: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_old_structure():
    """Тестирует старую структуру"""
    print("\n🧪 Тестирование старой структуры...")
    
    try:
        from core_utils import server_checker, progress_bar
        
        print("✅ Старая структура работает")
        return True
        
    except Exception as e:
        print(f"❌ Старая структура не работает: {e}")
        return False

def test_both_structures():
    """Тестирует обе структуры одновременно"""
    print("\n🧪 Тестирование совместимости...")
    
    # Добавляем пути
    sys.path.insert(0, '/opt/monitoring/app')
    
    try:
        # Импортируем из обоих источников
        from core_utils import server_checker as old_checker
        from app import server_checker as new_checker
        
        print(f"✅ Обе структуры работают:")
        print(f"   Старый: {old_checker}")
        print(f"   Новый: {new_checker}")
        
        # Проверяем, что это разные объекты
        if old_checker is not new_checker:
            print("⚠️  Внимание: разные экземпляры checker")
        
        return True
        
    except Exception as e:
        print(f"❌ Совместимость не работает: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТ НОВОЙ СТРУКТУРЫ")
    print("=" * 50)
    
    test1 = test_new_structure()
    test2 = test_old_structure()
    test3 = test_both_structures()
    
    print("\n" + "=" * 50)
    print("ИТОГ ТЕСТИРОВАНИЯ:")
    print(f"Новая структура: {'✅' if test1 else '❌'}")
    print(f"Старая структура: {'✅' if test2 else '❌'}")
    print(f"Совместимость: {'✅' if test3 else '❌'}")
    print("=" * 50)
    
    if test1 and test2:
        print("\n🎉 ГОТОВО К МИГРАЦИИ!")
    else:
        print("\n⚠️  ТРЕБУЕТСЯ ДОРАБОТКА")
