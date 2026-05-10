#!/usr/bin/env python3
"""
/main.py
Server Monitoring System v8.58.24
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
Система мониторинга серверов
Версия: 8.58.24
Автор: Александр Суханов (c)
Лицензия: MIT
Основной модуль запуска
"""

import os
import sys
import argparse
import threading
import time
from pathlib import Path

from lib.logging import setup_logging
PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = Path(os.environ.get("MONITORING_BASE_DIR", PROJECT_ROOT)).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def build_arg_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргументов для CLI."""
    parser = argparse.ArgumentParser(description="Server Monitoring System")
    try:
        from core.task_router import TASK_ROUTES
        parser.add_argument(
            "--check",
            choices=list(TASK_ROUTES.keys()),
            help="Выполнить задачу проверки и завершиться",
        )
    except Exception:
        parser.add_argument(
            "--check",
            help="Выполнить задачу проверки и завершиться",
        )

    parser.add_argument(
        "--server",
        help="IP или имя сервера для точечной проверки",
    )
    parser.add_argument(
        "--mode",
        choices=["availability", "resources"],
        default="availability",
        help="Тип точечной проверки (для targeted_checks)",
    )
    parser.add_argument(
        "--reload-servers",
        action="store_true",
        help="Принудительно перечитать список серверов перед проверкой",
    )
    parser.add_argument(
        "--bot",
        action="store_true",
        help="Запустить Telegram-бота (по умолчанию включено при отсутствии других действий)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Тестовый запуск без сетевых действий и опроса Telegram",
    )
    return parser


def run_cli_checks(args: argparse.Namespace) -> tuple[bool, int]:
    """
    Обрабатывает CLI-команды без запуска Telegram-бота.

    Returns:
        handled: Был ли обработан CLI-режим
        exit_code: Код завершения для sys.exit
    """
    if not args.check:
        return False, 0

    setup_logging("cli", level="INFO")

    from core.task_router import run_task

    success, payload = run_task(
        args.check,
        server_id=args.server,
        mode=args.mode,
        force_reload=args.reload_servers,
    )

    if not success:
        print(payload)
        return True, 1

    if args.check == "availability":
        up = len(payload.get("up", []))
        down = payload.get("down", [])
        print(f"📡 Доступность: {up} доступно, {len(down)} недоступно")
        if down:
            print("⚠️ Недоступные серверы:")
            for server in down:
                name = server.get("name", server.get("ip", ""))
                method = server.get("check_method", "неизвестно")
                print(f" - {name} ({server.get('ip', '')}): {method}")
    elif args.check == "resources":
        results = payload.get("results", [])
        stats = payload.get("stats", {})
        print(
            "📊 Ресурсы: "
            f"{stats.get('success', 0)}/{stats.get('total', 0)} успешно, "
            f"{stats.get('failed', 0)} ошибок"
        )
        for item in results:
            server = item.get("server", {})
            name = server.get("name", server.get("ip", ""))
            resources = item.get("resources") or {}
            if item.get("success"):
                print(
                    f" - {name}: CPU {resources.get('cpu', '?')}%, "
                    f"RAM {resources.get('ram', '?')}%, "
                    f"Disk {resources.get('disk', '?')}%"
                )
            else:
                print(f" - {name}: ресурсы недоступны")
    elif args.check == "targeted_checks":
        message = payload.get("message", "")
        print("🎯 Целевая проверка:")
        print(message)

    return True, 0 if success else 1


def main(args: argparse.Namespace):
    # ------------------------------------------------------------------
    # 1. Загрузка конфигурации
    # ------------------------------------------------------------------
    try:
        from config.db_settings import TELEGRAM_TOKEN, DEBUG_MODE, CHAT_IDS, SILENT_START, SILENT_END
    except ImportError as e:
        print(f"❌ Не удалось загрузить db_settings: {e}")
        sys.exit(1)

    log_level = "DEBUG" if DEBUG_MODE else "INFO"
    logger = setup_logging("main", level=log_level)
    logger.info("🚀 Запуск системы мониторинга")

    bot_token = TELEGRAM_TOKEN
    if not bot_token or len(bot_token) < 10:
        if args.dry_run:
            bot_token = "000000:TESTTOKEN"
            logger.warning("⚠️ Telegram токен отсутствует, используем тестовую заглушку (dry-run)")
        else:
            print("❌ Telegram токен отсутствует или некорректен")
            sys.exit(1)

    # Применяем настройки алертов заранее
    if not args.dry_run:
        try:
            from lib.alerts import configure_alerts

            configure_alerts(
                silent_start=SILENT_START,
                silent_end=SILENT_END,
            )
        except Exception as e:
            logger.warning(f"⚠️ Не удалось применить настройки алертов: {e}")
    else:
        logger.info("🧪 Dry-run: настройка алертов пропущена")

    # ------------------------------------------------------------------
    # 3. Инициализация Telegram-бота
    # ------------------------------------------------------------------
    from telegram.ext import (
        Updater,
    )

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    def telegram_error_handler(update, context):
        """Глобальный обработчик ошибок Telegram для стабильного polling."""
        error = getattr(context, "error", None)
        if error is None:
            logger.error("❌ Неизвестная ошибка Telegram без контекста")
            return

        try:
            from telegram.error import NetworkError, TimedOut
            network_errors = (NetworkError, TimedOut, TimeoutError)
        except Exception:
            network_errors = (TimeoutError,)

        if isinstance(error, network_errors):
            logger.warning(f"⚠️ Сетевая ошибка Telegram API: {error}")
            return

        logger.exception("❌ Необработанная ошибка Telegram", exc_info=error)

    dispatcher.add_error_handler(telegram_error_handler)
    try:
        from lib.alerts import init_telegram_bot

        init_telegram_bot(updater.bot, CHAT_IDS)
    except Exception as e:
        logger.warning(f"⚠️ Не удалось инициализировать алерты: {e}")

    logger.info("✅ Telegram бот инициализирован")


    # ------------------------------------------------------------------
    # 4. Команды бота
    # ------------------------------------------------------------------
    from bot.handlers import (
        get_callback_handlers,
        get_command_handlers,
        get_message_handlers,
    )

    for handler in get_command_handlers():
        dispatcher.add_handler(handler)

    logger.info("✅ Команды зарегистрированы")

    # ------------------------------------------------------------------
    # 5. Callback router (ЕДИНАЯ точка)
    # ------------------------------------------------------------------
    for handler in get_callback_handlers():
        dispatcher.add_handler(handler)
    logger.info("✅ Callback router подключён")

    # ------------------------------------------------------------------
    # 6. Обработчик текстового ввода (настройки)
    # ------------------------------------------------------------------
    message_handlers = get_message_handlers()
    if message_handlers:
        for handler in message_handlers:
            dispatcher.add_handler(handler)
        logger.info("✅ Обработчик ввода настроек подключён")
    else:
        logger.info("ℹ️ Обработчик ввода настроек недоступен")

    # ------------------------------------------------------------------
    # 7. Расширения
    # ------------------------------------------------------------------
    if not args.dry_run:
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

            if extension_manager.is_extension_enabled('supplier_stock_files'):
                from extensions.supplier_stock_files import start_supplier_stock_scheduler
                start_supplier_stock_scheduler()
                logger.info("✅ Планировщик остатков поставщиков запущен")

        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации расширений: {e}")
    else:
        logger.info("🧪 Dry-run: загрузка расширений пропущена")

    # ------------------------------------------------------------------
    # 8. Основной мониторинг
    # ------------------------------------------------------------------
    if not args.dry_run:
        try:
            from core.monitor import monitor
            threading.Thread(
                target=monitor.start,
                daemon=True
            ).start()
            logger.info("✅ Основной мониторинг запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска мониторинга: {e}")
    else:
        logger.info("🧪 Dry-run: запуск основного мониторинга пропущен")

    # ------------------------------------------------------------------
    # 9. Стартовое уведомление
    # ------------------------------------------------------------------
    if not args.dry_run:
        try:
            from lib.alerts import send_alert
            send_alert(
                "🟢 *Мониторинг серверов запущен*\n\n"
                "Система успешно инициализирована",
                force=True
            )
        except Exception as e:
            logger.warning(f"⚠️ Не удалось отправить стартовое сообщение: {e}")
    else:
        logger.info("🧪 Dry-run: стартовое уведомление не отправлялось")

    # ------------------------------------------------------------------
    # 10. Запуск
    # ------------------------------------------------------------------
    if args.dry_run:
        logger.info("🧪 Dry-run завершён: опрос Telegram не запускался")
        return
    
    retry_delay_sec = 5
    max_retry_delay_sec = 60

    while True:
        try:
            updater.start_polling(timeout=20, read_latency=2.0)
            logger.info("✅ Бот запущен и готов к работе")
            updater.idle()
            break
        except Exception as e:
            try:
                from telegram.error import NetworkError, TimedOut
                network_errors = (NetworkError, TimedOut, TimeoutError, ConnectionError, OSError)
            except Exception:
                network_errors = (TimeoutError, ConnectionError, OSError)

            if isinstance(e, network_errors):
                logger.warning(
                    "⚠️ Не удалось подключиться к Telegram API (%s). Повтор через %s сек.",
                    e.__class__.__name__,
                    retry_delay_sec,
                )
                try:
                    updater.stop()
                except Exception:
                    pass
                time.sleep(retry_delay_sec)
                retry_delay_sec = min(retry_delay_sec * 2, max_retry_delay_sec)
                continue

            logger.exception("❌ Критическая ошибка запуска Telegram polling")
            raise


if __name__ == "__main__":
    parser = build_arg_parser()
    cli_args = parser.parse_args()

    handled, exit_code = run_cli_checks(cli_args)
    if handled:
        sys.exit(exit_code)

    main(cli_args)
