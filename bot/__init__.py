"""
/bot/menu/__init__.py
Server Monitoring System v4.13.5
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Telegram bot package
Система мониторинга серверов
Версия: 4.13.5
Автор: Александр Суханов (c)
Лицензия: MIT
Пакет Telegram бота
"""

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from lib.logging import debug_log

def initialize_bot():
    """Инициализирует бота"""
    print("🤖 Инициализация Telegram бота...")
    
    try:
        # Используем импорт из config
        from config import TELEGRAM_TOKEN
        
        if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 10:
            print("❌ Токен не загружен или слишком короткий")
            return None
            
        print(f"✅ Токен загружен ({len(TELEGRAM_TOKEN)} символов)")
        
        # Создаем Updater и Dispatcher
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Регистрируем базовые команды
        from telegram import BotCommand
        
        # Устанавливаем команды меню
        commands = [
            BotCommand("start", "Запуск бота"),
            BotCommand("help", "Помощь"),
            BotCommand("check", "Проверить серверы"),
            BotCommand("status", "Статус мониторинга"),
            BotCommand("servers", "Список серверов"),
            BotCommand("control", "Управление мониторингом"),
        ]
        
        updater.bot.set_my_commands(commands)
        
        # Регистрируем обработчики команд
        # 1. Обработчик /start
        def start_command(update, context):
            """Обработчик команды /start"""
            user = update.effective_user
            welcome_text = (
                f"Привет, {user.first_name}! 👋\n\n"
                "🤖 *Система мониторинга серверов*\n"
                "✅ Бот запущен в тестовом режиме\n\n"
                "📋 *Доступные команды:*\n"
                "/start - Это меню\n"
                "/help - Помощь\n"
                "/check - Проверить серверы\n"
                "/status - Статус мониторинга\n"
                "/servers - Список серверов\n"
                "/control - Управление\n"
            )
            update.message.reply_text(welcome_text, parse_mode='Markdown')
        
        # 2. Обработчик /help
        def help_command(update, context):
            """Обработчик команды /help"""
            help_text = (
                "📚 *Помощь по системе мониторинга*\n\n"
                "*Основные команды:*\n"
                "/start - Запуск бота\n"
                "/check - Быстрая проверка серверов\n"
                "/status - Статус мониторинга\n"
                "/servers - Список всех серверов\n"
                "/control - Управление мониторингом\n\n"
                "*Система находится в тестовом режиме*"
            )
            update.message.reply_text(help_text, parse_mode='Markdown')
        
        # 3. Обработчик /check
        def check_command(update, context):
            """Обработчик команды /check"""
            update.message.reply_text(
                "🔍 *Проверка серверов*\n\n"
                "Функция проверки в разработке...\n"
                "Скоро здесь будет доступна проверка всех серверов.",
                parse_mode='Markdown'
            )
        
        # 4. Обработчик /status
        def status_command(update, context):
            """Обработчик команды /status"""
            try:
                from core.monitor import monitor
                status = monitor.get_status()
                
                status_text = (
                    "📊 *Статус мониторинга*\n\n"
                    f"• Мониторинг: {'🟢 Активен' if status['monitoring_active'] else '🔴 Остановлен'}\n"
                    f"• Режим: {'🔇 Тихий' if status['silent_mode'] else '🔊 Обычный'}\n"
                    f"• Серверов: {status['servers_count']}\n"
                    f"• Последняя проверка: {status['last_check_time'].strftime('%H:%M:%S')}\n\n"
                    "*Система в тестовом режиме*"
                )
            except Exception as e:
                status_text = (
                    "📊 *Статус мониторинга*\n\n"
                    f"• Бот: 🟢 Работает\n"
                    f"• Мониторинг: ⚠️ Не инициализирован\n"
                    f"• Ошибка: {str(e)[:100]}\n\n"
                    "*Система в тестовом режиме*"
                )
            
            update.message.reply_text(status_text, parse_mode='Markdown')
        
        # 5. Обработчик /servers
        def servers_command(update, context):
            """Обработчик команды /servers"""
            try:
                from core.monitor import monitor
                servers = monitor.servers
                
                if not servers:
                    update.message.reply_text("❌ Список серверов пуст")
                    return
                
                message = "📋 *Список серверов*\n\n"
                for i, server in enumerate(servers[:20], 1):  # Показываем первые 20
                    message += f"{i}. {server.get('name', 'Без имени')} ({server.get('ip')})\n"
                
                if len(servers) > 20:
                    message += f"\n... и еще {len(servers) - 20} серверов"
                
                update.message.reply_text(message, parse_mode='Markdown')
            except Exception as e:
                update.message.reply_text(f"❌ Ошибка получения списка серверов: {e}")
        
        # 6. Обработчик /control
        def control_command(update, context):
            """Обработчик команды /control"""
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить все", callback_data='manual_check')],
                [InlineKeyboardButton("📊 Статус", callback_data='monitor_status')],
                [InlineKeyboardButton("🔇 Тихий режим", callback_data='silent_status')],
                [InlineKeyboardButton("✖️ Закрыть", callback_data='close')]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                "🎛️ *Управление мониторингом*\n\n"
                "Выберите действие:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        # Регистрируем обработчики
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("check", check_command))
        dispatcher.add_handler(CommandHandler("status", status_command))
        dispatcher.add_handler(CommandHandler("servers", servers_command))
        dispatcher.add_handler(CommandHandler("control", control_command))
        
        # Регистрируем обработчик callback-запросов (заглушка)
        def callback_handler(update, context):
            query = update.callback_query
            query.answer()
            
            if query.data == 'close':
                try:
                    query.delete_message()
                except:
                    query.edit_message_text("✅ Меню закрыто")
            else:
                query.edit_message_text(f"⚙️ Кнопка '{query.data}' в разработке...")
        
        dispatcher.add_handler(CallbackQueryHandler(callback_handler))
        
        print("✅ Бот инициализирован успешно")
        return updater
        
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        import traceback
        traceback.print_exc()
        return None