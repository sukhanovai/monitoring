"""
Тестирование новой структуры без относительных импортов
"""

import sys
import os

def test_new_structure():
    """Тестирует новую структуру"""
    print("🧪 Тестирование новой структуры...")
    
    # Тест 1: Импорт новой структуры через app
    try:
        # Добавляем путь к app
        sys.path.insert(0, '/opt/monitoring/app')
        
        # Теперь импортируем через app
        import app
        
        print("✅ 1. Импорт app: УСПЕХ")
        print(f"   Версия: {app.__version__}")
        
        # Тест 2: Доступ к компонентам через app
        print(f"✅ 2. Компоненты через app:")
        print(f"   - server_checker: {app.server_checker}")
        print(f"   - logger: {app.logger}")
        
        # Тест 3: Прямой импорт модулей
        from app.core.checker import ServerChecker
        from app.utils.common import progress_bar, format_duration
        
        print(f"✅ 3. Прямой импорт:")
        print(f"   - ServerChecker: {ServerChecker}")
        print(f"   - progress_bar: {progress_bar(75)}")
        print(f"   - format_duration: {format_duration(3665)}")
        
        # Тест 4: Создание экземпляра
        checker = ServerChecker()
        print(f"✅ 4. Создание ServerChecker: {checker}")
        
        # Тест 5: Функции из common
        bar = progress_bar(50)
        duration = format_duration(7200)
        print(f"✅ 5. Работа функций:")
        print(f"   progress_bar(50) = {bar}")
        print(f"   format_duration(7200) = {duration}")
        
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
        # Очищаем sys.path от добавленных путей
        original_path = sys.path.copy()
        sys.path = [p for p in sys.path if '/opt/monitoring/app' not in p]
        
        from core_utils import server_checker, progress_bar
        
        print("✅ Старая структура работает")
        print(f"   server_checker: {server_checker}")
        print(f"   progress_bar(25): {progress_bar(25)}")
        
        # Восстанавливаем путь
        sys.path = original_path
        return True
        
    except Exception as e:
        print(f"❌ Старая структура не работает: {e}")
        sys.path = original_path
        return False

def test_compatibility():
    """Тестирует совместимость"""
    print("\n🧪 Тестирование совместимости...")
    
    try:
        # Импортируем из обеих структур
        from core_utils import server_checker as old_checker
        from core_utils import progress_bar as old_progress
        
        # Добавляем путь для новой структуры
        sys.path.insert(0, '/opt/monitoring/app')
        from app import server_checker as new_checker
        from app.utils.common import progress_bar as new_progress
        
        print(f"✅ Обе структуры работают:")
        print(f"   Старый checker: {type(old_checker).__name__}")
        print(f"   Новый checker: {type(new_checker).__name__}")
        print(f"   Старый progress_bar(33): {old_progress(33)}")
        print(f"   Новый progress_bar(66): {new_progress(66)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Совместимость не работает: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_variants():
    """Тестирует различные варианты импорта"""
    print("\n🧪 Тестирование вариантов импорта...")
    
    variants = [
        ("from core_utils import server_checker", None),
        ("from app import server_checker", None),
        ("from app.core.checker import ServerChecker", None),
        ("from app.utils.common import progress_bar", None),
        ("import app", "app.server_checker"),
    ]
    
    sys.path.insert(0, '/opt/monitoring/app')
    
    for import_str, attr in variants:
        try:
            if "from" in import_str:
                exec(import_str)
                print(f"✅ {import_str}")
            elif "import" in import_str:
                exec(import_str)
                if attr:
                    # Проверяем атрибут
                    check_str = f"{attr}"
                    result = eval(check_str)
                    print(f"✅ {import_str} -> {result}")
                else:
                    print(f"✅ {import_str}")
        except Exception as e:
            print(f"❌ {import_str} - ошибка: {e}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТ НОВОЙ СТРУКТУРЫ v2")
    print("=" * 50)
    
    test1 = test_new_structure()
    test2 = test_old_structure()
    test3 = test_compatibility()
    test4 = test_import_variants()
    
    print("\n" + "=" * 50)
    print("ИТОГ ТЕСТИРОВАНИЯ:")
    print(f"Новая структура: {'✅' if test1 else '❌'}")
    print(f"Старая структура: {'✅' if test2 else '❌'}")
    print(f"Совместимость: {'✅' if test3 else '❌'}")
    print(f"Варианты импорта: {'✅' if test4 else '❌'}")
    print("=" * 50)
    
    if test1 and test2:
        print("\n🎉 ГОТОВО К МИГРАЦИИ!")
        print("\nРекомендуемые импорты для нового кода:")
        print("  from app import server_checker, logger")
        print("  from app.utils.common import progress_bar, format_duration")
        print("  from app.core.checker import ServerChecker")
    else:
        print("\n⚠️  ТРЕБУЕТСЯ ДОРАБОТКА")
