"""
/core/checker.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Server Checker Module
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
РњРѕРґСѓР»СЊ РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ
"""

import time
import subprocess
import socket
import logging
import paramiko
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple
from lib.logging import debug_log, error_log, setup_logging
from lib.network import check_ping as net_check_ping, check_port as net_check_port

class ServerChecker:
    """Р•РґРёРЅС‹Р№ РєР»Р°СЃСЃ РґР»СЏ РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ - Р±Р°Р·РѕРІР°СЏ РІРµСЂСЃРёСЏ"""
    
    def __init__(self, ssh_timeout: int = 15, ping_timeout: int = 10, port_timeout: int = 5):
        self.ssh_timeout = ssh_timeout
        self.ping_timeout = ping_timeout
        self.port_timeout = port_timeout
        self.logger = setup_logging("checker")
        
    def check_ping(self, ip: str) -> bool:
        """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° ping"""
        return net_check_ping(ip, timeout=self.ping_timeout)
    
    def check_port(self, ip: str, port: int = 3389) -> bool:
        """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° РїРѕСЂС‚Р°"""
        return net_check_port(ip, port, timeout=self.port_timeout)
    
    def check_ssh_universal(self, ip: str, username: Optional[str] = None, key_path: Optional[str] = None) -> bool:
        """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° SSH СЃ РѕР±СЂР°Р±РѕС‚РєРѕР№ РѕС€РёР±РѕРє"""
        try:
            # Р›РµРЅРёРІР°СЏ Р·Р°РіСЂСѓР·РєР° РєРѕРЅС„РёРіР°
            if username is None or key_path is None:
                from config.db_settings import SSH_USERNAME, SSH_KEY_PATH
                username = SSH_USERNAME
                key_path = SSH_KEY_PATH

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            with _suppress_paramiko_logging():
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

            # РџСЂРѕСЃС‚Р°СЏ РїСЂРѕРІРµСЂРєР°
            stdin, stdout, stderr = client.exec_command('echo "test"', timeout=5)
            exit_code = stdout.channel.recv_exit_status()
            client.close()

            return exit_code == 0

        except paramiko.ssh_exception.AuthenticationException as e:
            debug_log(f"SSH auth failed for {ip}: {e}")
            return False
        except paramiko.ssh_exception.SSHException as e:
            debug_log(f"SSH error for {ip}: {e}")
            return False
        except socket.timeout:
            debug_log(f"SSH timeout for {ip}")
            return False
        except Exception as e:
            debug_log(f"SSH general error for {ip}: {e}")
            return False

    def check_server(self, server: Dict) -> bool:
        """РЈРЅРёРІРµСЂСЃР°Р»СЊРЅР°СЏ РїСЂРѕРІРµСЂРєР° СЃРµСЂРІРµСЂР° РїРѕ С‚РёРїСѓ"""
        server_type = server.get("type", "ssh")
        ip = server["ip"]

        if server_type == "rdp":
            return self.check_port(ip, 3389)
        elif server_type == "ping":
            return self.check_ping(ip)
        else:  # ssh Рё РґСЂСѓРіРёРµ
            return self.check_ssh_universal(ip)

    def get_timeout_for_type(self, server_type: str) -> int:
        """РџРѕР»СѓС‡РёС‚СЊ С‚Р°Р№РјР°СѓС‚ РґР»СЏ С‚РёРїР° СЃРµСЂРІРµСЂР°"""
        try:
            from config.db_settings import SERVER_TIMEOUTS
            return SERVER_TIMEOUTS.get(server_type, 15)
        except:
            return 15


@contextmanager
def _suppress_paramiko_logging():
    """Р’СЂРµРјРµРЅРЅРѕ РїРѕРґР°РІР»СЏРµС‚ С€СѓРјРЅС‹Рµ С‚СЂР°СЃСЃРёСЂРѕРІРєРё Paramiko РїСЂРё СЃР±РѕСЏС… SSH."""
    logger = logging.getLogger("paramiko.transport")
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    try:
        yield
    finally:
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
