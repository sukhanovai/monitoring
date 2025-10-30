#!/usr/bin/env python3
"""
Глубокая диагностика callback обработчиков
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def debug_callback_handlers():
    """Диагностика callback обработчиков"""
    
    print("🔍 Глубокая диагностика callback обработчиков...")
    
    try:
        from bot_menu import get_callback_handlers
        
        handlers = get_callback_handlers()
        print(f"✅ Всего callback обработчиков: {len(handlers)}")
        
        # Детальный анализ всех обработчиков
        db_patterns = []
        other_patterns = []
        
        for handler in handlers:
            if hasattr(handler, 'pattern'):
                pattern_str = str(handler.pattern.pattern)
                if 'db_backups' in pattern_str:
                    db_patterns.append(pattern_str)
                else:
                    other_patterns.append(pattern_str)
        
        print(f"\n📋 Обработчики db_backups ({len(db_patterns)}):")
        for pattern in db_patterns:
            print(f"   ✅ {pattern}")
            
        print(f"\n📋 Другие обработчики ({len(other_patterns)}):")
        for pattern in other_patterns[:10]:  # Покажем первые 10
            print(f"   - {pattern}")
            
        if len(db_patterns) == 0:
            print("\n❌ НЕТ обработчиков для db_backups!")
            
        return len(db_patterns) > 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_callback_directly():
    """Прямой тест callback обработки"""
    
    print("\n🧪 Прямой тест callback обработки...")
    
    try:
        from extensions.backup_monitor.bot_handler import backup_callback
        
        # Создаем mock callback update
        class MockUpdate:
            def __init__(self, data):
                self.callback_query = MockCallbackQuery(data)
                
        class MockCallbackQuery:
            def __init__(self, data):
                self.data = data
            def answer(self, text=None):
                print(f"   📨 Callback answer: {text}")
            def edit_message_text(self, text, parse_mode=None, reply_markup=None):
                print(f"   ✅ Сообщение обновлено: {text[:100]}...")
                return True
                
        class MockContext:
            pass
            
        # Тестируем разные callback'ы
        test_callbacks = [
            'db_backups_24h',
            'db_backups_48h', 
            'backup_today'
        ]
        
        for callback_data in test_callbacks:
            print(f"\n🔹 Тест callback: {callback_data}")
            update = MockUpdate(callback_data)
            context = MockContext()
            
            try:
                backup_callback(update, context)
                print("   ✅ Обработчик выполнен успешно")
            except Exception as e:
                print(f"   ❌ Ошибка обработки: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_callback_handlers()
    test_callback_directly()
    