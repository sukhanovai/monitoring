"""
/app/modules/debug.py
Server Monitoring System v8.62.72
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Debugging and diagnostics module
Система мониторинга серверов
Версия: 8.62.72
Автор: Александр Суханов (c)
Лицензия: MIT
Модуль отладки и диагностики
"""

import logging
import socket
import subprocess
from datetime import datetime
from pathlib import Path

from config.db_settings import (
    BOT_DEBUG_LOG_FILE,
    DATA_DIR,
    DEBUG_LOG_FILE,
    MAIL_MONITOR_LOG_FILE,
)
from lib.logging import debug_log


class DebugManager:
    """Класс управления отладкой и диагностикой"""

    def __init__(self):
        self.debug_config = None
        self.load_debug_config()

    def load_debug_config(self):
        """Загрузка конфигурации отладки"""
        try:
            from config.debug_app import debug_config

            self.debug_config = debug_config
        except ImportError:
            debug_log("⚠️ Конфигурация отладки недоступна", force=True)
            self.debug_config = None

    def get_system_status(self):
        """Получение статуса системы"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "resources": {},
            "processes": {},
            "logs": {},
        }

        # Проверка сервисов
        services = [
            ("SSH", "localhost", 22),
            ("Веб-интерфейс", "192.168.20.2", 5000),
            ("База данных", "localhost", None),
        ]

        for name, host, port in services:
            try:
                if port:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    status["services"][name] = "🟢" if result == 0 else "🔴"
                else:
                    # Проверка файла базы
                    db_path = DATA_DIR / "backups.db"
                    status["services"][name] = "🟢" if db_path.exists() else "🔴"
            except Exception as e:
                status["services"][name] = f"🔴 ({str(e)[:30]})"

        # Проверка процессов
        processes = ["python3", "main.py", "improved_mail_monitor.py"]
        for process in processes:
            try:
                result = subprocess.run(["pgrep", "-f", process], capture_output=True, text=True)
                running = len(result.stdout.strip().split("\n")) > 0 and result.stdout.strip() != ""
                status["processes"][process] = "🟢" if running else "🔴"
            except Exception as e:
                status["processes"][process] = "🔴"

        # Проверка логов
        log_files = {
            "debug.log": DEBUG_LOG_FILE,
            "bot_debug.log": BOT_DEBUG_LOG_FILE,
        }

        for name, path in log_files.items():
            try:
                log_path = Path(path)
                if log_path.exists():
                    size = log_path.stat().st_size / 1024 / 1024
                    status["logs"][name] = f"{size:.2f} MB"
                else:
                    status["logs"][name] = "файл не существует"
            except Exception as e:
                status["logs"][name] = "ошибка проверки"

        return status

    def diagnose_server_connection(self, server_ip):
        """Диагностика подключения к серверу"""
        try:
            from extensions.server_checks import get_server_by_ip

            server = get_server_by_ip(server_ip)

            if not server:
                return f"❌ Сервер {server_ip} не найден в списке"

            result = {
                "server": f"{server['name']} ({server_ip})",
                "type": server["type"],
                "checks": {},
            }

            # Проверка ping
            from extensions.server_checks import check_ping

            result["checks"]["ping"] = "🟢 OK" if check_ping(server_ip) else "🔴 FAIL"

            # Проверка портов в зависимости от типа
            if server["type"] == "ssh":
                from extensions.server_checks import check_port

                result["checks"]["ssh_port"] = "🟢 OK" if check_port(server_ip, 22) else "🔴 FAIL"

            elif server["type"] == "rdp":
                from extensions.server_checks import check_port

                result["checks"]["rdp_port"] = "🟢 OK" if check_port(server_ip, 3389) else "🔴 FAIL"
                result["checks"]["winrm_port"] = (
                    "🟢 OK" if check_port(server_ip, 5985) else "🔴 FAIL"
                )

            # Форматирование результата
            message = "🔧 *Диагностика подключения*\n\n"
            message += f"**Сервер:** {result['server']}\n"
            message += f"**Тип:** {result['type']}\n\n"
            message += "**Проверки:**\n"

            for check_name, check_result in result["checks"].items():
                message += f"• {check_name}: {check_result}\n"

            return message

        except Exception as e:
            return f"❌ Ошибка диагностики: {str(e)[:100]}"

    def clear_logs(self):
        """Очистка логов"""
        log_files = [
            DEBUG_LOG_FILE,
            BOT_DEBUG_LOG_FILE,
            MAIL_MONITOR_LOG_FILE,
        ]

        cleared = 0
        errors = []

        for log_file in log_files:
            try:
                log_file = Path(log_file)
                if log_file.exists():
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
                else:
                    # Создаем пустой файл если не существует
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    log_file.write_text("", encoding="utf-8")
                    cleared += 1
            except Exception as e:
                errors.append(f"{Path(log_file).name}: {str(e)[:50]}")

        return cleared, errors

    def toggle_debug_mode(self, enable=True):
        """Переключение режима отладки"""
        if not self.debug_config:
            return False, "Конфигурация отладки недоступна"

        try:
            if enable:
                self.debug_config.enable_debug()
                logging.getLogger().setLevel(logging.DEBUG)
                return True, "🟢 Отладка включена"
            else:
                self.debug_config.disable_debug()
                logging.getLogger().setLevel(logging.INFO)
                return True, "🔴 Отладка выключена"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def get_debug_info(self):
        """Получение информации об отладке"""
        if not self.debug_config:
            return {"error": "Конфигурация отладки недоступна"}

        return self.debug_config.get_debug_info()


# Глобальный экземпляр менеджера отладки
debug_manager = DebugManager()
