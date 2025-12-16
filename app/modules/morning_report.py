"""
/app/modules/morning_report.py
Server Monitoring System v4.13.3
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Morning Report Module
Система мониторинга серверов
Версия: 4.13.3
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль утреннего отчета
"""

import threading
import time
from datetime import datetime, timedelta
from app.config.settings import DATA_COLLECTION_TIME
from app.utils.logging import debug_log

class MorningReport:
    """Класс управления утренними отчетами"""
    
    def __init__(self):
        self.morning_data = {}
        self.last_report_date = None
        self.last_data_collection = None
        
    def collect_morning_data(self, manual_call=False):
        """Сбор данных для утреннего отчета"""
        try:
            from app.modules.availability import availability_monitor
            current_status = availability_monitor.get_current_status()
            
            self.morning_data = {
                "status": current_status,
                "collection_time": datetime.now(),
                "manual_call": manual_call
            }
            
            debug_log(f"✅ Данные для отчета собраны: {len(current_status['ok'])} доступно, {len(current_status['failed'])} недоступно")
            return True
        except Exception as e:
            debug_log(f"❌ Ошибка сбора данных для отчета: {e}")
            return False
    
    def generate_report_message(self):
        """Генерация сообщения отчета"""
        if not self.morning_data or "status" not in self.morning_data:
            return "❌ Нет данных для отчета"
            
        status = self.morning_data["status"]
        collection_time = self.morning_data.get("collection_time", datetime.now())
        is_manual = self.morning_data.get("manual_call", False)
        
        total_servers = len(status["ok"]) + len(status["failed"])
        up_count = len(status["ok"])
        down_count = len(status["failed"])
        
        # Определяем тип отчета
        if is_manual:
            report_type = "Ручной запрос"
            time_prefix = "⏰ *Время проверки:*"
        else:
            report_type = "Утренний отчет"
            time_prefix = "⏰ *Время сбора данных:*"
        
        message = f"📊 *{report_type} о доступности серверов*\n\n"
        message += f"{time_prefix} {collection_time.strftime('%H:%M')}\n"
        message += f"🔢 *Всего серверов:* {total_servers}\n"
        message += f"🟢 *Доступно:* {up_count}\n"
        message += f"🔴 *Недоступно:* {down_count}\n"
        
        # Добавляем информацию о бэкапах
        try:
            backup_summary = self.get_backup_summary_for_report(24 if is_manual else 16)
            message += f"\n💾 *Статус бэкапов ({'за последние 24ч' if is_manual else 'за последние 16ч'})*\n"
            message += backup_summary
        except Exception as e:
            debug_log(f"⚠️ Ошибка получения данных о бэкапах: {e}")
            message += "\n💾 *Статус бэкапов:* данные недоступны\n"
        
        if down_count > 0:
            message += f"\n⚠️ *Проблемные серверы ({down_count}):*\n"
            # Группируем по типу
            by_type = {}
            for server in status["failed"]:
                if server["type"] not in by_type:
                    by_type[server["type"]] = []
                by_type[server["type"]].append(server)
                
            for server_type, servers_list in by_type.items():
                message += f"\n**{server_type.upper()} ({len(servers_list)}):**\n"
                for s in servers_list:
                    message += f"• {s['name']} ({s['ip']})\n"
        else:
            message += f"\n✅ *Все серверы доступны!*\n"
            
        message += f"\n⏰ *Отчет сформирован:* {datetime.now().strftime('%H:%M:%S')}"
        return message
    
    def get_backup_summary_for_report(self, period_hours=16):
        """Получает сводку по бэкапам"""
        try:
            # Импорт функций бэкапов
            from extensions.backup_monitor.backup_utils import get_backup_summary
            return get_backup_summary(period_hours)
        except Exception as e:
            debug_log(f"❌ Ошибка получения сводки по бэкапам: {e}")
            return "❌ Данные о бэкапах недоступны"
    
    def send_report(self, manual_call=False):
        """Отправка отчета"""
        try:
            # Собираем данные
            self.collect_morning_data(manual_call)
            
            # Генерируем сообщение
            message = self.generate_report_message()
            
            # Отправляем через обработчик
            from app.handlers.commands import send_alert
            send_alert(message, force=True)
            
            debug_log(f"✅ Отчет отправлен ({'ручной' if manual_call else 'автоматический'})")
            return True
        except Exception as e:
            debug_log(f"❌ Ошибка отправки отчета: {e}")
            return False
    
    def start_scheduler(self):
        """Запуск планировщика отчетов"""
        debug_log("⏰ Запуск планировщика утренних отчетов")
        
        while True:
            current_time = datetime.now()
            current_time_time = current_time.time()
            
            # Проверяем время сбора данных
            if (current_time_time.hour == DATA_COLLECTION_TIME.hour and
                current_time_time.minute == DATA_COLLECTION_TIME.minute):
                
                # Проверяем, что сегодня еще не отправляли отчет
                today = current_time.date()
                if self.last_report_date != today:
                    debug_log(f"📊 Автоматический сбор данных для утреннего отчета")
                    self.send_report(manual_call=False)
                    self.last_report_date = today
                    
                    # Задержка чтобы не запускать повторно в ту же минуту
                    time.sleep(65)
                else:
                    debug_log(f"⏭️ Отчет уже отправлен сегодня {self.last_report_date}")
            
            time.sleep(60)  # Проверяем каждую минуту

# Глобальный экземпляр отчета
morning_report = MorningReport()