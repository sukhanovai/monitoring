"""
Server Monitoring System v4.11.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot utilities
Система мониторинга серверов
Версия: 4.11.3
Автор: Александр Суханов (c)
Лицензия: MIT
Утилиты бота
"""

from lib.logging import debug_log

def check_access(chat_id):
    """Проверка доступа к боту"""
    try:
        # Импортируем CHAT_IDS из config.settings, который использует приоритет БД
        from config.settings import CHAT_IDS
        
        chat_id_str = str(chat_id)
        
        # Диагностика только в режиме отладки
        from config.settings import DEBUG_MODE
        if DEBUG_MODE:
            debug_log(f"🔍 Проверка доступа для chat_id: {chat_id_str}")
            debug_log(f"📋 CHAT_IDS из настроек: {CHAT_IDS}")
        
        # Проверяем что CHAT_IDS это список
        if not isinstance(CHAT_IDS, list):
            debug_log(f"⚠️ ОШИБКА: CHAT_IDS не является списком: {type(CHAT_IDS)}")
            return False
        
        result = chat_id_str in CHAT_IDS
        
        if DEBUG_MODE:
            debug_log(f"✅ Результат проверки доступа: {'Разрешено' if result else 'Запрещено'}")
        
        return result
        
    except Exception as e:
        debug_log(f"💥 Ошибка в check_access: {e}")
        import traceback
        debug_log(f"💥 Traceback: {traceback.format_exc()}")
        return False

def get_access_denied_response(update):
    """Возвращает ответ при отсутствии доступа"""
    debug_log(f"🚫 Доступ запрещен для update: {update.update_id}")
    
    if update.message:
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
    elif update.callback_query:
        update.callback_query.answer("⛔ У вас нет прав")
        update.callback_query.edit_message_text("⛔ У вас нет прав для использования этого бота")