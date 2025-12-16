"""
Server Monitoring System v4.11.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot utilities
Система мониторинга серверов
Версия: 4.11.2
Автор: Александр Суханов (c)
Лицензия: MIT
Утилиты бота
"""

from lib.logging import debug_log

def check_access(chat_id):
    """Проверка доступа к боту - УПРОЩЕННАЯ ВЕРСИЯ ДЛЯ ТЕСТА"""
    from lib.logging import debug_log
    
    try:
        # Прямой запрос к БД для проверки
        import sqlite3
        import json
        
        conn = sqlite3.connect('/opt/monitoring/data/settings.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'CHAT_IDS'")
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            debug_log("❌ Настройка CHAT_IDS не найдена в БД")
            return False
            
        chat_ids_from_db = json.loads(result[0])
        chat_id_str = str(chat_id)
        
        debug_log(f"🔍 Прямой запрос к БД:")
        debug_log(f"  Chat ID: {chat_id_str}")
        debug_log(f"  CHAT_IDS из БД: {chat_ids_from_db}")
        
        access_granted = chat_id_str in chat_ids_from_db
        debug_log(f"  Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
        
        return access_granted
        
    except Exception as e:
        debug_log(f"💥 Ошибка при прямом запросе к БД: {e}")
        import traceback
        debug_log(f"💥 Traceback: {traceback.format_exc()}")
        
        # ВРЕМЕННО: разрешаем доступ для отладки
        debug_log("⚠️ ВРЕМЕННО: доступ разрешен для отладки")
        return True
    
def get_access_denied_response(update):
    """Возвращает ответ при отсутствии доступа"""
    debug_log(f"🚫 Доступ запрещен для update: {update.update_id}")
    
    if update.message:
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
    elif update.callback_query:
        update.callback_query.answer("⛔ У вас нет прав")
        update.callback_query.edit_message_text("⛔ У вас нет прав для использования этого бота")