"""
Server Monitoring System v4.11.1
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Bot utilities
Система мониторинга серверов
Версия: 4.11.1
Автор: Александр Суханов (c)
Лицензия: MIT
Утилиты бота
"""

def check_access(chat_id):
    """Проверка доступа к боту"""
    from config.settings import CHAT_IDS
    return str(chat_id) in CHAT_IDS

def get_access_denied_response(update):
    """Возвращает ответ при отсутствии доступа"""
    if update.message:
        update.message.reply_text("⛔ У вас нет прав для использования этого бота")
    elif update.callback_query:
        update.callback_query.answer("⛔ У вас нет прав")
        update.callback_query.edit_message_text("⛔ У вас нет прав для использования этого бота")