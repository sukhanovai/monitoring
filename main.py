#!/usr/bin/env python3
"""
/main.py
Server Monitoring System v4.14.30
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 4.14.30
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import sys
import logging
import threading

# Явно фиксируем корень проекта
sys.path.insert(0, '/opt/monitoring')


def main():
    # ------------------------------------------------------------------
    # 1. Загрузка конфигурации
    # ------------------------------------------------------------------
    try:
        from config.db_settings import TELEGRAM_TOKEN, DEBUG_MODE
    except ImportError as e:
        print(f"❌ Не удалось загрузить db_settings: {e}")
        sys.exit(1)

    if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 10:
        print("❌ Telegram токен отсутствует или некорректен")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Логирование
    # ------------------------------------------------------------------
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    logger = logging.getLogger("main")
    logger.info("🚀 Запуск системы мониторинга")

    # ------------------------------------------------------------------
    # 3. Инициализация Telegram-бота
    # ------------------------------------------------------------------
    from telegram.ext import (
        Updater,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        Filters,
    )

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    logger.info("✅ Telegram бот инициализирован")

    # ------------------------------------------------------------------
    # 4. Команды бота
    # ------------------------------------------------------------------
    from bot.handlers.commands import (
        start_command,
        help_command,
        check_command,
        status_command,
        silent_mode_command,
        control_panel_command,
        report_command,
    )

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("check", check_command))
    dispatcher.add_handler(CommandHandler("status", status_command))
    dispatcher.add_handler(CommandHandler("silent", silent_mode_command))
    dispatcher.add_handler(CommandHandler("control", control_panel_command))
    dispatcher.add_handler(CommandHandler("report", report_command))

    logger.info("✅ Команды зарегистрированы")

    # ------------------------------------------------------------------
    # 5. Callback router (ЕДИНАЯ точка)
    # ------------------------------------------------------------------
    from bot.handlers.callbacks import callback_router

    dispatcher.add_handler(CallbackQueryHandler(callback_router))
    logger.info("✅ Callback router подключён")

    # ------------------------------------------------------------------
    # 6. Обработчик текстового ввода (настройки)
    # ------------------------------------------------------------------
    try:
        from settings_handlers import handle_setting_value
        dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, handle_setting_value)
        )
        logger.info("✅ Обработчик ввода настроек подключён")
    except ImportError:
        logger.warning("⚠️ settings_handlers недоступен")

    # ------------------------------------------------------------------
    # 7. Расширения
    # ------------------------------------------------------------------
    try:
        from extensions.extension_manager import extension_manager

        if extension_manager.is_extension_enabled('backup_monitor'):
            from extensions.backup_monitor.bot_handler import setup_backup_handlers
            setup_backup_handlers(dispatcher)
            logger.info("✅ Расширение backup_monitor подключено")

        if extension_manager.is_extension_enabled('web_interface'):
            from extensions.web_interface import start_web_server
            threading.Thread(
                target=start_web_server,
                daemon=True
            ).start()
            logger.info("✅ Веб-интерфейс запущен")

    except Exception as e:
        logger.warning(f"⚠️ Ошибка инициализации расширений: {e}")

    # ------------------------------------------------------------------
    # 8. Основной мониторинг
    # ------------------------------------------------------------------
    try:
        from core.monitor import monitor
        threading.Thread(
            target=monitor.start,
            daemon=True
        ).start()
        logger.info("✅ Основной мониторинг запущен")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска мониторинга: {e}")

    # ------------------------------------------------------------------
    # 9. Стартовое уведомление
    # ------------------------------------------------------------------
    try:
        from lib.alerts import send_alert
        send_alert(
            "🟢 *Мониторинг серверов запущен*\n\n"
            "Система успешно инициализирована",
            force=True
        )
    except Exception as e:
        logger.warning(f"⚠️ Не удалось отправить стартовое сообщение: {e}")

    # ------------------------------------------------------------------
    # 10. Запуск
    # ------------------------------------------------------------------
    updater.start_polling()
    logger.info("✅ Бот запущен и готов к работе")
    updater.idle()


if __name__ == "__main__":
    main()
