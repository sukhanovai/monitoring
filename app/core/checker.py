"""
Server Monitoring System v4.4.2
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Модуль проверки серверов
Версия: 4.4.2
"""

import os
import time
import subprocess
import socket
import paramiko
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Константы по умолчанию
DEFAULT_SSH_USERNAME = 'root'
DEFAULT_SSH_KEY_PATH = '/root/.ssh/id_rsa'
DEFAULT_TIMEOUTS = {
    'ssh': 15,
    'rdp': 10,
    'ping': 10,
    'http': 5,
    'https': 5,
    'custom': 10
}

# Настройка логирования
logger = logging.getLogger(__name__)


def debug_log(message: str, force: bool = False):
    """Логирование отладочной информации"""
    if force or os.environ.get('DEBUG_MODE', 'False') == 'True':
        logger.debug(message)


def safe_import(module_name: str, class_name: Optional[str] = None):
    """Безопасный импорт модулей"""
    try:
        import importlib
        module = importlib.import_module(module_name)
        if class_name:
            return getattr(module, class_name)
        return module
    except Exception as e:
        debug_log(f"Import error: {e}")
        return None


class ServerChecker:
    """Единый класс для проверки серверов"""
    
    def __init__(self, 
                 ssh_timeout: int = 15, 
                 ping_timeout: int = 10, 
                 port_timeout: int = 5,
                 config: Optional[Dict[str, Any]] = None):
        """
        Инициализация проверяльщика
        
        Args:
            ssh_timeout: Таймаут SSH соединения
            ping_timeout: Таймаут ping проверки
            port_timeout: Таймаут проверки порта
            config: Конфигурация (опционально)
        """
        self.ssh_timeout = ssh_timeout
        self.ping_timeout = ping_timeout
        self.port_timeout = port_timeout
        self.config = config or {}
        
        # Загружаем конфигурацию если передана
        self._load_config()
        
    def _load_config(self):
        """Загрузка конфигурации"""
        try:
            # Пытаемся загрузить из модуля config
            config_module = safe_import('app.config.settings')
            if config_module:
                self.config.update({
                    'ssh_username': getattr(config_module, 'SSH_USERNAME', DEFAULT_SSH_USERNAME),
                    'ssh_key_path': getattr(config_module, 'SSH_KEY_PATH', DEFAULT_SSH_KEY_PATH),
                    'timeouts': getattr(config_module, 'SERVER_TIMEOUTS', DEFAULT_TIMEOUTS)
                })
        except Exception as e:
            debug_log(f"Config load error: {e}")
            # Используем значения по умолчанию
            self.config.setdefault('ssh_username', DEFAULT_SSH_USERNAME)
            self.config.setdefault('ssh_key_path', DEFAULT_SSH_KEY_PATH)
            self.config.setdefault('timeouts', DEFAULT_TIMEOUTS.copy())
    
    def check_ping(self, ip: str) -> bool:
        """Универсальная проверка ping"""
        try:
            # Определяем команду ping в зависимости от ОС
            if os.name == 'nt':  # Windows
                cmd = ['ping', '-n', '2', '-w', '2000', ip]
            else:  # Linux/Mac
                cmd = ['ping', '-c', '2', '-W', '2', ip]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.ping_timeout
            )
            
            success = result.returncode == 0
            if not success:
                debug_log(f"Ping failed for {ip}: returncode={result.returncode}")
            return success
            
        except subprocess.TimeoutExpired:
            debug_log(f"Ping timeout for {ip}")
            return False
        except Exception as e:
            debug_log(f"Ping error for {ip}: {e}")
            return False
    
    def check_port(self, ip: str, port: int = 3389, timeout: Optional[int] = None) -> bool:
        """Универсальная проверка порта"""
        if timeout is None:
            timeout = self.port_timeout
        
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            is_open = result == 0
            
            if not is_open:
                debug_log(f"Port {port} closed on {ip}: error={result}")
            return is_open
            
        except socket.timeout:
            debug_log(f"Port check timeout for {ip}:{port}")
            return False
        except socket.error as e:
            debug_log(f"Socket error for {ip}:{port}: {e}")
            return False
        except Exception as e:
            debug_log(f"Port check error for {ip}:{port}: {e}")
            return False
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def check_ssh(self, 
                  ip: str, 
                  username: Optional[str] = None, 
                  key_path: Optional[str] = None,
                  password: Optional[str] = None) -> bool:
        """Универсальная проверка SSH с обработкой ошибок"""
        try:
            # Получаем учетные данные
            if username is None:
                username = self.config.get('ssh_username', DEFAULT_SSH_USERNAME)
            if key_path is None:
                key_path = self.config.get('ssh_key_path', DEFAULT_SSH_KEY_PATH)
            
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Параметры соединения
            connect_params = {
                'hostname': ip,
                'username': username,
                'timeout': self.ssh_timeout,
                'banner_timeout': self.ssh_timeout,
                'auth_timeout': self.ssh_timeout,
                'look_for_keys': False,
                'allow_agent': False,
            }
            
            # Используем ключ или пароль
            if password:
                connect_params['password'] = password
            else:
                connect_params['key_filename'] = key_path
            
            # Устанавливаем соединение
            client.connect(**connect_params)
            
            # Простая проверка доступности
            stdin, stdout, stderr = client.exec_command('echo "SSH test"', timeout=5)
            exit_code = stdout.channel.recv_exit_status()
            
            client.close()
            
            success = exit_code == 0
            if not success:
                debug_log(f"SSH command failed for {ip}: exit_code={exit_code}")
            return success
            
        except paramiko.AuthenticationException as e:
            debug_log(f"SSH authentication failed for {ip}: {e}")
            return False
        except paramiko.SSHException as e:
            debug_log(f"SSH error for {ip}: {e}")
            return False
        except socket.timeout:
            debug_log(f"SSH timeout for {ip}")
            return False
        except Exception as e:
            debug_log(f"SSH general error for {ip}: {e}")
            return False
    
    def check_http(self, url: str, timeout: int = 10) -> bool:
        """Проверка HTTP/HTTPS доступности"""
        try:
            import requests
            response = requests.get(url, timeout=timeout, verify=False)
            return response.status_code < 400
        except ImportError:
            debug_log("Requests module not installed, using socket check")
            # Fallback to socket check
            from urllib.parse import urlparse
            parsed = urlparse(url)
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            return self.check_port(parsed.hostname, port, timeout)
        except Exception as e:
            debug_log(f"HTTP check error for {url}: {e}")
            return False
    
    def check_custom(self, server: Dict[str, Any]) -> bool:
        """Проверка по пользовательскому скрипту"""
        try:
            script_path = server.get('script_path')
            if not script_path or not os.path.exists(script_path):
                debug_log(f"Custom script not found: {script_path}")
                return False
            
            result = subprocess.run(
                [script_path, server['ip']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=server.get('timeout', 30)
            )
            
            return result.returncode == 0
            
        except Exception as e:
            debug_log(f"Custom check error for {server.get('name', 'unknown')}: {e}")
            return False
    
    def check_server(self, server: Dict[str, Any]) -> bool:
        """Универсальная проверка сервера по типу"""
        server_type = server.get("type", "ssh").lower()
        ip = server["ip"]
        
        debug_log(f"Checking server {server.get('name', ip)} as {server_type}")
        
        # Выбираем метод проверки в зависимости от типа
        if server_type == "rdp":
            port = server.get("port", 3389)
            return self.check_port(ip, port)
            
        elif server_type == "ping":
            return self.check_ping(ip)
            
        elif server_type in ["http", "https"]:
            url = server.get("url", f"{server_type}://{ip}")
            return self.check_http(url)
            
        elif server_type == "ssh":
            username = server.get("username")
            key_path = server.get("key_path")
            password = server.get("password")
            return self.check_ssh(ip, username, key_path, password)
            
        elif server_type == "custom":
            return self.check_custom(server)
            
        elif server_type == "port":
            port = server.get("port", 22)
            return self.check_port(ip, port)
            
        else:
            # По умолчанию пытаемся SSH
            debug_log(f"Unknown server type '{server_type}', trying SSH")
            return self.check_ssh(ip)
    
    def get_timeout_for_type(self, server_type: str) -> int:
        """Получить таймаут для типа сервера"""
        timeouts = self.config.get('timeouts', DEFAULT_TIMEOUTS)
        return timeouts.get(server_type, 15)
    
    def check_with_details(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка сервера с детальной информацией"""
        start_time = time.time()
        
        try:
            status = self.check_server(server)
            response_time = time.time() - start_time
            
            return {
                'server': server.get('name', server['ip']),
                'ip': server['ip'],
                'type': server.get('type', 'ssh'),
                'status': 'online' if status else 'offline',
                'response_time': round(response_time, 3),
                'timestamp': datetime.now().isoformat(),
                'success': status
            }
            
        except Exception as e:
            debug_log(f"Error in detailed check for {server.get('name', 'unknown')}: {e}")
            return {
                'server': server.get('name', server['ip']),
                'ip': server['ip'],
                'type': server.get('type', 'ssh'),
                'status': 'error',
                'response_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    # Совместимость со старым кодом
    def check_ssh_universal(self, ip: str) -> bool:
        """Совместимая функция для старых вызовов"""
        return self.check_ssh(ip)


# Глобальный экземпляр для совместимости
server_checker = ServerChecker()
