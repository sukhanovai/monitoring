"""
Server Monitoring System v2.2.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Сборщик статистики для веб-интерфейса
"""
import json
import time
from datetime import datetime, timedelta
from config import STATS_FILE, DATA_DIR
import os

def save_monitoring_stats():
    """Сохраняет статистику мониторинга"""
    try:
        stats_data = {
            "last_updated": datetime.now().isoformat(),
            "uptime": get_system_uptime(),
            "daily_stats": get_daily_stats()
        }
        
        # Создаем директорию если не существует
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with open(STATS_FILE, 'w') as f:
            json.dump(stats_data, f, indent=2)
            
    except Exception as e:
        print(f"❌ Ошибка сохранения статистики: {e}")

def get_system_uptime():
    """Получает время работы системы"""
    try:
        # Для Linux систем
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    except:
        return "Неизвестно"

def get_daily_stats():
    """Получает дневную статистику"""
    # Здесь можно добавить логику сбора дневной статистики
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "checks_performed": 0,
        "alerts_sent": 0
    }
