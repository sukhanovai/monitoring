#!/usr/bin/env python3
"""
/main.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Main launch module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РћСЃРЅРѕРІРЅРѕР№ РјРѕРґСѓР»СЊ Р·Р°РїСѓСЃРєР°
"""

import os
import sys
import argparse
import threading
from pathlib import Path

from lib.logging import setup_logging
PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = Path(os.environ.get("MONITORING_BASE_DIR", PROJECT_ROOT)).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def build_arg_parser() -> argparse.ArgumentParser:
    """РЎРѕР·РґР°С‘С‚ РїР°СЂСЃРµСЂ Р°СЂРіСѓРјРµРЅС‚РѕРІ РґР»СЏ CLI."""
    parser = argparse.ArgumentParser(description="Server Monitoring System")
    try:
        from core.task_router import TASK_ROUTES
        parser.add_argument(
            "--check",
            choices=list(TASK_ROUTES.keys()),
            help="Р’С‹РїРѕР»РЅРёС‚СЊ Р·Р°РґР°С‡Сѓ РїСЂРѕРІРµСЂРєРё Рё Р·Р°РІРµСЂС€РёС‚СЊСЃСЏ",
        )
    except Exception:
        parser.add_argument(
            "--check",
            help="Р’С‹РїРѕР»РЅРёС‚СЊ Р·Р°РґР°С‡Сѓ РїСЂРѕРІРµСЂРєРё Рё Р·Р°РІРµСЂС€РёС‚СЊСЃСЏ",
        )

    parser.add_argument(
        "--server",
        help="IP РёР»Рё РёРјСЏ СЃРµСЂРІРµСЂР° РґР»СЏ С‚РѕС‡РµС‡РЅРѕР№ РїСЂРѕРІРµСЂРєРё",
    )
    parser.add_argument(
        "--mode",
        choices=["availability", "resources"],
        default="availability",
        help="РўРёРї С‚РѕС‡РµС‡РЅРѕР№ РїСЂРѕРІРµСЂРєРё (РґР»СЏ targeted_checks)",
    )
    parser.add_argument(
        "--reload-servers",
        action="store_true",
        help="РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РїРµСЂРµС‡РёС‚Р°С‚СЊ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ РїРµСЂРµРґ РїСЂРѕРІРµСЂРєРѕР№",
    )
    parser.add_argument(
        "--bot",
        action="store_true",
        help="Р—Р°РїСѓСЃС‚РёС‚СЊ Telegram-Р±РѕС‚Р° (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РІРєР»СЋС‡РµРЅРѕ РїСЂРё РѕС‚СЃСѓС‚СЃС‚РІРёРё РґСЂСѓРіРёС… РґРµР№СЃС‚РІРёР№)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="РўРµСЃС‚РѕРІС‹Р№ Р·Р°РїСѓСЃРє Р±РµР· СЃРµС‚РµРІС‹С… РґРµР№СЃС‚РІРёР№ Рё РѕРїСЂРѕСЃР° Telegram",
    )
    return parser


def run_cli_checks(args: argparse.Namespace) -> tuple[bool, int]:
    """
    РћР±СЂР°Р±Р°С‚С‹РІР°РµС‚ CLI-РєРѕРјР°РЅРґС‹ Р±РµР· Р·Р°РїСѓСЃРєР° Telegram-Р±РѕС‚Р°.

    Returns:
        handled: Р‘С‹Р» Р»Рё РѕР±СЂР°Р±РѕС‚Р°РЅ CLI-СЂРµР¶РёРј
        exit_code: РљРѕРґ Р·Р°РІРµСЂС€РµРЅРёСЏ РґР»СЏ sys.exit
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
        print(f"рџ“Ў Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ: {up} РґРѕСЃС‚СѓРїРЅРѕ, {len(down)} РЅРµРґРѕСЃС‚СѓРїРЅРѕ")
        if down:
            print("вљ пёЏ РќРµРґРѕСЃС‚СѓРїРЅС‹Рµ СЃРµСЂРІРµСЂС‹:")
            for server in down:
                name = server.get("name", server.get("ip", ""))
                method = server.get("check_method", "РЅРµРёР·РІРµСЃС‚РЅРѕ")
                print(f" - {name} ({server.get('ip', '')}): {method}")
    elif args.check == "resources":
        results = payload.get("results", [])
        stats = payload.get("stats", {})
        print(
            "рџ“Љ Р РµСЃСѓСЂСЃС‹: "
            f"{stats.get('success', 0)}/{stats.get('total', 0)} СѓСЃРїРµС€РЅРѕ, "
            f"{stats.get('failed', 0)} РѕС€РёР±РѕРє"
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
                print(f" - {name}: СЂРµСЃСѓСЂСЃС‹ РЅРµРґРѕСЃС‚СѓРїРЅС‹")
    elif args.check == "targeted_checks":
        message = payload.get("message", "")
        print("рџЋЇ Р¦РµР»РµРІР°СЏ РїСЂРѕРІРµСЂРєР°:")
        print(message)

    return True, 0 if success else 1


def main(args: argparse.Namespace):
    # ------------------------------------------------------------------
    # 1. Р—Р°РіСЂСѓР·РєР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё
    # ------------------------------------------------------------------
    try:
        from config.db_settings import TELEGRAM_TOKEN, DEBUG_MODE, CHAT_IDS, SILENT_START, SILENT_END, TAMTAM_TOKEN, TAMTAM_CHAT_IDS
    except ImportError as e:
        print(f"вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ db_settings: {e}")
        sys.exit(1)

    log_level = "DEBUG" if DEBUG_MODE else "INFO"
    logger = setup_logging("main", level=log_level)
    logger.info("рџљЂ Р—Р°РїСѓСЃРє СЃРёСЃС‚РµРјС‹ РјРѕРЅРёС‚РѕСЂРёРЅРіР°")

    bot_token = TELEGRAM_TOKEN
    if not bot_token or len(bot_token) < 10:
        if args.dry_run:
            bot_token = "000000:TESTTOKEN"
            logger.warning("вљ пёЏ Telegram С‚РѕРєРµРЅ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚, РёСЃРїРѕР»СЊР·СѓРµРј С‚РµСЃС‚РѕРІСѓСЋ Р·Р°РіР»СѓС€РєСѓ (dry-run)")
        else:
            print("вќЊ Telegram С‚РѕРєРµРЅ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚ РёР»Рё РЅРµРєРѕСЂСЂРµРєС‚РµРЅ")
            sys.exit(1)

    # РџСЂРёРјРµРЅСЏРµРј РЅР°СЃС‚СЂРѕР№РєРё Р°Р»РµСЂС‚РѕРІ Р·Р°СЂР°РЅРµРµ
    if not args.dry_run:
        try:
            from lib.alerts import configure_alerts

            configure_alerts(
                silent_start=SILENT_START,
                silent_end=SILENT_END,
            )
        except Exception as e:
            logger.warning(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРёРјРµРЅРёС‚СЊ РЅР°СЃС‚СЂРѕР№РєРё Р°Р»РµСЂС‚РѕРІ: {e}")
    else:
        logger.info("рџ§Є Dry-run: РЅР°СЃС‚СЂРѕР№РєР° Р°Р»РµСЂС‚РѕРІ РїСЂРѕРїСѓС‰РµРЅР°")

    # ------------------------------------------------------------------
    # 3. РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ Telegram-Р±РѕС‚Р°
    # ------------------------------------------------------------------
    from telegram.ext import (
        Updater,
    )

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    try:
        from lib.alerts import init_telegram_bot

        init_telegram_bot(updater.bot, CHAT_IDS)
    except Exception as e:
        logger.warning(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ Р°Р»РµСЂС‚С‹: {e}")

    logger.info("вњ… Telegram Р±РѕС‚ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ")


    tamtam_service = None
    if TAMTAM_TOKEN:
        try:
            from lib.tamtam_bot import TamTamBotService, TamTamConfig
            from lib.alerts import init_tamtam_sender

            tamtam_service = TamTamBotService(
                TamTamConfig(token=TAMTAM_TOKEN, chat_ids=[str(c) for c in TAMTAM_CHAT_IDS])
            )
            tamtam_service.start()
            init_tamtam_sender(tamtam_service.broadcast)
            logger.info("вњ… TamTam Р±РѕС‚ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅ")
        except Exception as e:
            logger.warning(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ TamTam Р±РѕС‚: {e}")
    else:
        logger.info("в„№пёЏ TamTam С‚РѕРєРµРЅ РЅРµ Р·Р°РґР°РЅ, РёРЅС‚РµРіСЂР°С†РёСЏ РІС‹РєР»СЋС‡РµРЅР°")

    # ------------------------------------------------------------------
    # 4. РљРѕРјР°РЅРґС‹ Р±РѕС‚Р°
    # ------------------------------------------------------------------
    from bot.handlers import (
        get_callback_handlers,
        get_command_handlers,
        get_message_handlers,
    )

    for handler in get_command_handlers():
        dispatcher.add_handler(handler)

    logger.info("вњ… РљРѕРјР°РЅРґС‹ Р·Р°СЂРµРіРёСЃС‚СЂРёСЂРѕРІР°РЅС‹")

    # ------------------------------------------------------------------
    # 5. Callback router (Р•Р”РРќРђРЇ С‚РѕС‡РєР°)
    # ------------------------------------------------------------------
    for handler in get_callback_handlers():
        dispatcher.add_handler(handler)
    logger.info("вњ… Callback router РїРѕРґРєР»СЋС‡С‘РЅ")

    # ------------------------------------------------------------------
    # 6. РћР±СЂР°Р±РѕС‚С‡РёРє С‚РµРєСЃС‚РѕРІРѕРіРѕ РІРІРѕРґР° (РЅР°СЃС‚СЂРѕР№РєРё)
    # ------------------------------------------------------------------
    message_handlers = get_message_handlers()
    if message_handlers:
        for handler in message_handlers:
            dispatcher.add_handler(handler)
        logger.info("вњ… РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РЅР°СЃС‚СЂРѕРµРє РїРѕРґРєР»СЋС‡С‘РЅ")
    else:
        logger.info("в„№пёЏ РћР±СЂР°Р±РѕС‚С‡РёРє РІРІРѕРґР° РЅР°СЃС‚СЂРѕРµРє РЅРµРґРѕСЃС‚СѓРїРµРЅ")

    # ------------------------------------------------------------------
    # 7. Р Р°СЃС€РёСЂРµРЅРёСЏ
    # ------------------------------------------------------------------
    if not args.dry_run:
        try:
            from extensions.extension_manager import extension_manager

            if extension_manager.is_extension_enabled('backup_monitor'):
                from extensions.backup_monitor.bot_handler import setup_backup_handlers
                setup_backup_handlers(dispatcher)
                logger.info("вњ… Р Р°СЃС€РёСЂРµРЅРёРµ backup_monitor РїРѕРґРєР»СЋС‡РµРЅРѕ")

            if extension_manager.is_extension_enabled('web_interface'):
                from extensions.web_interface import start_web_server
                threading.Thread(
                    target=start_web_server,
                    daemon=True
                ).start()
                logger.info("вњ… Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ Р·Р°РїСѓС‰РµРЅ")

            if extension_manager.is_extension_enabled('supplier_stock_files'):
                from extensions.supplier_stock_files import start_supplier_stock_scheduler
                start_supplier_stock_scheduler()
                logger.info("вњ… РџР»Р°РЅРёСЂРѕРІС‰РёРє РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ Р·Р°РїСѓС‰РµРЅ")

        except Exception as e:
            logger.warning(f"вљ пёЏ РћС€РёР±РєР° РёРЅРёС†РёР°Р»РёР·Р°С†РёРё СЂР°СЃС€РёСЂРµРЅРёР№: {e}")
    else:
        logger.info("рџ§Є Dry-run: Р·Р°РіСЂСѓР·РєР° СЂР°СЃС€РёСЂРµРЅРёР№ РїСЂРѕРїСѓС‰РµРЅР°")

    # ------------------------------------------------------------------
    # 8. РћСЃРЅРѕРІРЅРѕР№ РјРѕРЅРёС‚РѕСЂРёРЅРі
    # ------------------------------------------------------------------
    if not args.dry_run:
        try:
            from core.monitor import monitor
            threading.Thread(
                target=monitor.start,
                daemon=True
            ).start()
            logger.info("вњ… РћСЃРЅРѕРІРЅРѕР№ РјРѕРЅРёС‚РѕСЂРёРЅРі Р·Р°РїСѓС‰РµРЅ")
        except Exception as e:
            logger.error(f"вќЊ РћС€РёР±РєР° Р·Р°РїСѓСЃРєР° РјРѕРЅРёС‚РѕСЂРёРЅРіР°: {e}")
    else:
        logger.info("рџ§Є Dry-run: Р·Р°РїСѓСЃРє РѕСЃРЅРѕРІРЅРѕРіРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РїСЂРѕРїСѓС‰РµРЅ")

    # ------------------------------------------------------------------
    # 9. РЎС‚Р°СЂС‚РѕРІРѕРµ СѓРІРµРґРѕРјР»РµРЅРёРµ
    # ------------------------------------------------------------------
    if not args.dry_run:
        try:
            from lib.alerts import send_alert
            send_alert(
                "рџџў *РњРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂРѕРІ Р·Р°РїСѓС‰РµРЅ*\n\n"
                "РЎРёСЃС‚РµРјР° СѓСЃРїРµС€РЅРѕ РёРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°РЅР°",
                force=True
            )
        except Exception as e:
            logger.warning(f"вљ пёЏ РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РїСЂР°РІРёС‚СЊ СЃС‚Р°СЂС‚РѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ: {e}")
    else:
        logger.info("рџ§Є Dry-run: СЃС‚Р°СЂС‚РѕРІРѕРµ СѓРІРµРґРѕРјР»РµРЅРёРµ РЅРµ РѕС‚РїСЂР°РІР»СЏР»РѕСЃСЊ")

    # ------------------------------------------------------------------
    # 10. Р—Р°РїСѓСЃРє
    # ------------------------------------------------------------------
    if args.dry_run:
        logger.info("рџ§Є Dry-run Р·Р°РІРµСЂС€С‘РЅ: РѕРїСЂРѕСЃ Telegram РЅРµ Р·Р°РїСѓСЃРєР°Р»СЃСЏ")
        return
    
    updater.start_polling()
    logger.info("вњ… Р‘РѕС‚ Р·Р°РїСѓС‰РµРЅ Рё РіРѕС‚РѕРІ Рє СЂР°Р±РѕС‚Рµ")
    updater.idle()


if __name__ == "__main__":
    parser = build_arg_parser()
    cli_args = parser.parse_args()

    handled, exit_code = run_cli_checks(cli_args)
    if handled:
        sys.exit(exit_code)

    main(cli_args)
