"""
Server Monitoring System v4.4.11 - Обработчики бота
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Диагностика мониторинга

"""

import time
from datetime import datetime
from typing import Dict, List, Any
from app.core.checker import server_checker
from app.utils.common import debug_log

def diagnose_server_check(server: Dict[str, Any]) -> Dict[str, Any]:
    """Расширенная диагностика сервера"""
    result = {
        "server": server,
        "checks": [],
        "overall_status": "unknown"
    }
    
    ip = server["ip"]
    server_type = server.get("type", "ssh").lower()
    name = server.get("name", ip)
    
    debug_log(f"🔍 Диагностика сервера {name} ({ip}) как {server_type}")
    
    # 1. Проверка ping
    try:
        ping_start = time.time()
        ping_result = server_checker.check_ping(ip)
        ping_time = time.time() - ping_start
        
        result["checks"].append({
            "type": "ping",
            "result": ping_result,
            "time": ping_time
        })
        
        debug_log(f"  Ping: {'🟢' if ping_result else '🔴'} ({ping_time:.2f}s)")
    except Exception as e:
        debug_log(f"  Ping error: {e}")
        result["checks"].append({
            "type": "ping",
            "result": False,
            "error": str(e)
        })
    
    # 2. Проверка в зависимости от типа
    if server_type == "rdp":
        try:
            port_start = time.time()
            port_result = server_checker.check_port(ip, 3389)
            port_time = time.time() - port_start
            
            result["checks"].append({
                "type": "rdp_port",
                "port": 3389,
                "result": port_result,
                "time": port_time
            })
            
            debug_log(f"  RDP port 3389: {'🟢' if port_result else '🔴'} ({port_time:.2f}s)")
            
            # Если порт не отвечает, пробуем другие порты Windows
            if not port_result:
                for port in [445, 135, 139]:  # SMB, RPC, NetBIOS
                    try:
                        alt_result = server_checker.check_port(ip, port, timeout=3)
                        result["checks"].append({
                            "type": f"port_{port}",
                            "port": port,
                            "result": alt_result
                        })
                        debug_log(f"  Port {port}: {'🟢' if alt_result else '🔴'}")
                    except:
                        pass
                        
        except Exception as e:
            debug_log(f"  RDP check error: {e}")
            result["checks"].append({
                "type": "rdp_port",
                "result": False,
                "error": str(e)
            })
    
    elif server_type == "ssh":
        try:
            ssh_start = time.time()
            ssh_result = server_checker.check_ssh_universal(ip)
            ssh_time = time.time() - ssh_start
            
            result["checks"].append({
                "type": "ssh",
                "result": ssh_result,
                "time": ssh_time
            })
            
            debug_log(f"  SSH: {'🟢' if ssh_result else '🔴'} ({ssh_time:.2f}s)")
        except Exception as e:
            debug_log(f"  SSH error: {e}")
            result["checks"].append({
                "type": "ssh",
                "result": False,
                "error": str(e)
            })
    
    # Определяем общий статус
    successful_checks = [c for c in result["checks"] if c.get("result", False)]
    if any(c.get("result", False) for c in result["checks"]):
        result["overall_status"] = "online"
    else:
        result["overall_status"] = "offline"
    
    return result
