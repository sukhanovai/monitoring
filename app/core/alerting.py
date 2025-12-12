"""
Server Monitoring System v4.4.7 - Система оповещений
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Модуль управления оповещениями

"""

import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from app.utils.common import debug_log, progress_bar
from app.config import settings


class AlertingSystem:
    """Система управления оповещениями"""
    
    def __init__(self, monitoring_core):
        self.monitoring_core = monitoring_core
    
    def send_manual_check_results(self, context: CallbackContext, chat_id: int, 
                                  progress_message_id: int, results: Dict[str, List]) -> None:
        """Отправляет результаты ручной проверки"""
        if not results["failed"]:
            message = "✅ Все серверы доступны!"
        else:
            message = "⚠️ Проблемные серверы:\n"
            
            # Группируем по типу для удобства чтения
            by_type = {}
            for server in results["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)

            for server_type, servers_list in by_type.items():
                message += f"\n{server_type.upper()} серверы:\n"
                for s in servers_list:
                    message += f"- {s['name']} ({s['ip']})\n"

        context.bot.edit_message_text(
            chat_id=chat_id, 
            message_id=progress_message_id,
            text=f"🔍 Проверка завершена!\n\n{message}\n\n⏰ Время проверки: {self.monitoring_core.last_check_time.strftime('%H:%M:%S')}"
        )
    
    def perform_manual_check(self, context: CallbackContext, chat_id: int, 
                            progress_message_id: int) -> None:
        """Выполняет проверку серверов с обновлением прогресса"""
        total_servers = len(self.monitoring_core.servers)
        results = {"failed": [], "ok": []}

        for i, server in enumerate(self.monitoring_core.servers):
            try:
                progress = (i + 1) / total_servers * 100
                progress_text = f"🔍 Проверяю серверы...\n{progress_bar(progress)}\n\n⏳ Проверяю {server['name']} ({server['ip']})..."

                context.bot.edit_message_text(
                    chat_id=chat_id, 
                    message_id=progress_message_id, 
                    text=progress_text
                )

                # Используем универсальную проверку
                is_up = self.monitoring_core.check_server_availability(server)

                if is_up:
                    results["ok"].append(server)
                    debug_log(f"✅ {server['name']} ({server['ip']}) - доступен")
                else:
                    results["failed"].append(server)
                    debug_log(f"❌ {server['name']} ({server['ip']}) - недоступен")

                time.sleep(1)

            except Exception as e:
                debug_log(f"💥 Критическая ошибка при проверке {server['ip']}: {e}")
                results["failed"].append(server)

        self.monitoring_core.last_check_time = datetime.now()
        self.send_manual_check_results(context, chat_id, progress_message_id, results)


# Глобальный экземпляр
alerting_system = None

def get_alerting_system(monitoring_core):
    """Получает экземпляр системы оповещений"""
    global alerting_system
    if alerting_system is None:
        alerting_system = AlertingSystem(monitoring_core)
    return alerting_system
