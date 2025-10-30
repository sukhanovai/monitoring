#!/usr/bin/env python3
"""
Проверка статуса расширения backup_monitor
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def check_extension_status():
    """Проверяет статус расширения backup_monitor"""
    
    print("🔍 Проверяем статус расширения backup_monitor...")
    
    try:
        from extensions.extension_manager import extension_manager
        
        # Проверяем статус всех расширений
        extensions_status = extension_manager.get_extensions_status()
        
        print("📊 Статус всех расширений:")
        for ext_id, status in extensions_status.items():
            enabled = status['enabled']
            info = status['info']
            print(f"   {ext_id}: {'🟢 ВКЛЮЧЕНО' if enabled else '🔴 ОТКЛЮЧЕНО'} - {info['name']}")
        
        # Проверяем конкретно backup_monitor
        backup_enabled = extension_manager.is_extension_enabled('backup_monitor')
        print(f"\n🔍 Расширение 'backup_monitor': {'🟢 ВКЛЮЧЕНО' if backup_enabled else '🔴 ОТКЛЮЧЕНО'}")
        
        # Проверяем доступность команд
        commands_available = extension_manager.is_command_available('backup')
        print(f"🔍 Команда 'backup' доступна: {'✅ ДА' if commands_available else '❌ НЕТ'}")
        
        # Проверяем доступность обработчиков
        handlers_available = extension_manager.is_handler_available('backup_')
        print(f"🔍 Обработчики 'backup_' доступны: {'✅ ДА' if handlers_available else '❌ НЕТ'}")
        
        return backup_enabled
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        import traceback
        traceback.print_exc()
        return False

def enable_backup_extension():
    """Включает расширение backup_monitor"""
    
    print("\n🔧 Включаем расширение backup_monitor...")
    
    try:
        from extensions.extension_manager import extension_manager
        
        success, message = extension_manager.enable_extension('backup_monitor')
        print(f"Результат: {message}")
        
        if success:
            print("✅ Расширение включено, перезапустите бота")
        else:
            print("❌ Не удалось включить расширение")
            
        return success
        
    except Exception as e:
        print(f"❌ Ошибка включения: {e}")
        return False

if __name__ == "__main__":
    is_enabled = check_extension_status()
    
    if not is_enabled:
        enable_backup_extension()
    else:
        print("\n✅ Расширение backup_monitor уже включено")
        