"""
Server Monitoring System v3.5.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Утилиты ядра мониторинга
"""

import os
import time
import logging
import subprocess
import socket
import paramiko
from datetime import datetime

# Глобальные настройки отладки
DEBUG_MODE = False
DEBUG_LOG_FILE = '/opt/monitoring/logs/debug.log'

def setup_logging():
    """Настройка централизованного логирования"""
    logging.basicConfig(
        level=logging.DEBUG if DEBUG_MODE else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(DEBUG_LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class ServerChecker:
    """Единый класс для проверки серверов - устранение дублирования"""
    
    def __init__(self):
        self.ssh_timeout = 15
        self.ping_timeout = 10
        self.port_timeout = 5

    def check_ping(self, ip):
        """Универсальная проверка ping"""
        try:
            result = subprocess.run(
                ['ping', '-c', '2', '-W', '2', ip],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=self.ping_timeout
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Ping error for {ip}: {e}")
            return False

    def check_port(self, ip, port=3389):
        """Универсальная проверка порта"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.port_timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"Port check error for {ip}:{port}: {e}")
            return False

    def check_ssh_universal(self, ip, username=None, key_path=None):
        """Универсальная проверка SSH с обработкой ошибок"""
        try:
            # Ленивая загрузка конфига
            if username is None or key_path is None:
                from config import SSH_USERNAME, SSH_KEY_PATH
                username = SSH_USERNAME
                key_path = SSH_KEY_PATH

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            client.connect(
                hostname=ip,
                username=username,
                key_filename=key_path,
                timeout=self.ssh_timeout,
                banner_timeout=self.ssh_timeout,
                auth_timeout=self.ssh_timeout,
                look_for_keys=False,
                allow_agent=False,
            )

            # Простая проверка
            stdin, stdout, stderr = client.exec_command('echo "test"', timeout=5)
            exit_code = stdout.channel.recv_exit_status()
            client.close()

            return exit_code == 0

        except paramiko.ssh_exception.AuthenticationException as e:
            logger.warning(f"SSH auth failed for {ip}: {e}")
            return False
        except paramiko.ssh_exception.SSHException as e:
            logger.warning(f"SSH error for {ip}: {e}")
            return False
        except socket.timeout:
            logger.warning(f"SSH timeout for {ip}")
            return False
        except Exception as e:
            logger.debug(f"SSH general error for {ip}: {e}")
            return False

    def check_server(self, server):
        """Универсальная проверка сервера по типу"""
        server_type = server.get("type", "ssh")
        ip = server["ip"]

        if server_type == "rdp":
            return self.check_port(ip, 3389)
        elif server_type == "ping":
            return self.check_ping(ip)
        else:  # ssh и другие
            return self.check_ssh_universal(ip)

# Глобальный экземпляр для использования во всем проекте
server_checker = ServerChecker()

def debug_log(message, force=False):
    """Централизованное логирование отладки"""
    if DEBUG_MODE or force:
        logger.debug(message)

def safe_import(module_name, class_name=None):
    """Безопасный импорт с обработкой ошибок"""
    try:
        module = __import__(module_name, fromlist=[class_name] if class_name else [])
        return getattr(module, class_name) if class_name else module
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return None
    except AttributeError as e:
        logger.error(f"Attribute error: {e}")
        return None

def format_duration(seconds):
    """Форматирование длительности в читаемый вид"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:02d}s"
    else:
        return f"{seconds}s"

def progress_bar(percentage, width=20):
    """Универсальный прогресс-бар"""
    filled = int(round(width * percentage / 100))
    return f"[{'█' * filled}{'░' * (width - filled)}] {percentage:.1f}%"