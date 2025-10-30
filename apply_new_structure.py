#!/usr/bin/env python3
"""
Скрипт для применения новой структуры меню бэкапов
"""

import sys
sys.path.insert(0, '/opt/monitoring')

def apply_new_backup_structure():
    """Применяет новую структуру меню бэкапов"""
    
    print("🔄 Применяем новую структуру меню бэкапов...")
    
    try:
        # Обновляем команды бота
        from bot_menu import setup_menu
        from telegram import Bot
        from config import TELEGRAM_TOKEN
        
        bot = Bot(token=TELEGRAM_TOKEN)
        setup_menu(bot)
        print("✅ Команды бота обновлены")
        
        # Проверяем расширения
        from extensions.extension_manager import extension_manager
        
        # Добавляем новое расширение если его нет
        extensions_status = extension_manager.get_extensions_status()
        if 'database_backup_monitor' not in extensions_status:
            success, message = extension_manager.enable_extension('database_backup_monitor')
            print(f"✅ Новое расширение добавлено: {message}")
        
        print("🎉 Новая структура меню применена!")
        print("\n📋 Новое меню бэкапов:")
        print("   /backup - Главное меню бэкапов")
        print("   🖥️ Бэкапы Proxmox - бэкапы виртуальных машин")
        print("   🗃️ Бэкапы БД - бэкапы баз данных")
        print("   🛠️ Управление расширениями - включение/выключение мониторинга БД")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    apply_new_backup_structure()
