"""
Server Monitoring System v3.0.0
Обработчики для управления настройками через бота
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from settings_manager import settings_manager

def settings_command(update, context):
    """Команда управления настройками"""
    keyboard = [
        [InlineKeyboardButton("🤖 Настройки бота", callback_data='settings_telegram')],
        [InlineKeyboardButton("⏰ Временные настройки", callback_data='settings_time')],
        [InlineKeyboardButton("🔧 Мониторинг", callback_data='settings_monitoring')],
        [InlineKeyboardButton("💻 Ресурсы", callback_data='settings_resources')],
        [InlineKeyboardButton("🔐 Аутентификация", callback_data='settings_auth')],
        [InlineKeyboardButton("🖥️ Серверы", callback_data='settings_servers')],
        [InlineKeyboardButton("💾 Бэкапы", callback_data='settings_backup')],
        [InlineKeyboardButton("↩️ Назад", callback_data='monitor_status')]
    ]
    
    update.message.reply_text(
        "⚙️ *Управление настройками*\n\nВыберите категорию для настройки:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_telegram_settings(update, context):
    """Показать настройки Telegram"""
    query = update.callback_query
    query.answer()
    
    token = settings_manager.get_setting('TELEGRAM_TOKEN', '')
    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    
    token_display = "🟢 Установлен" if token else "🔴 Не установлен"
    chats_display = f"{len(chat_ids)} чатов" if chat_ids else "🔴 Не настроены"
    
    message = (
        "🤖 *Настройки Telegram*\n\n"
        f"• Токен бота: {token_display}\n"
        f"• ID чатов: {chats_display}\n\n"
        "Выберите параметр для изменения:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 Установить токен", callback_data='set_telegram_token')],
        [InlineKeyboardButton("💬 Управление чатами", callback_data='manage_chats')],
        [InlineKeyboardButton("↩️ Назад", callback_data='settings_main')]
    ]
    
    query.edit_message_text(
        message,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Добавляем аналогичные функции для других категорий настроек...

def settings_callback_handler(update, context):
    """Обработчик callback'ов настроек"""
    query = update.callback_query
    data = query.data
    
    if data == 'settings_main':
        settings_command(update, context)
    elif data == 'settings_telegram':
        show_telegram_settings(update, context)
    # Добавляем обработчики для других категорий...
    
    query.answer()

def get_settings_handlers():
    """Получить обработчики для настроек"""
    return [
        CommandHandler("settings", settings_command),
        CallbackQueryHandler(settings_callback_handler, pattern='^settings_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^set_'),
        CallbackQueryHandler(settings_callback_handler, pattern='^manage_')
    ]
