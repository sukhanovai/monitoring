from flask import Flask, jsonify, render_template_string
from config import WEB_PORT, WEB_HOST
import threading
from datetime import datetime
import json
import os
from config import STATS_FILE, DATA_DIR

app = Flask(__name__)

# HTML шаблон для веб-интерфейса
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌐 Мониторинг серверов</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header .status {
            font-size: 1.2em;
            color: #666;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        .card h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.4em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .stat-item:last-child {
            border-bottom: none;
        }
        .stat-value {
            font-weight: bold;
            font-size: 1.1em;
        }
        .status-up { color: #28a745; }
        .status-down { color: #dc3545; }
        .status-warning { color: #ffc107; }
        
        .server-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .server-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        .server-item.down {
            border-left-color: #dc3545;
            background: #ffe6e6;
        }
        .server-item.warning {
            border-left-color: #ffc107;
            background: #fff3cd;
        }
        .server-name {
            font-weight: bold;
        }
        .server-status {
            font-size: 0.9em;
            padding: 4px 8px;
            border-radius: 12px;
            background: #28a745;
            color: white;
        }
        .server-status.down {
            background: #dc3545;
        }
        .server-status.warning {
            background: #ffc107;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 15px;
            transition: background 0.3s;
        }
        .refresh-btn:hover {
            background: #764ba2;
        }
        
        .last-update {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Мониторинг серверов</h1>
            <div class="status">Система работает • Последнее обновление: <span id="lastUpdate">{{ last_update }}</span></div>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h2>📊 Общая статистика</h2>
                <div class="stat-item">
                    <span>Всего серверов:</span>
                    <span class="stat-value">{{ stats.total_servers }}</span>
                </div>
                <div class="stat-item">
                    <span>Доступно:</span>
                    <span class="stat-value status-up">{{ stats.servers_up }}</span>
                </div>
                <div class="stat-item">
                    <span>Недоступно:</span>
                    <span class="stat-value status-down">{{ stats.servers_down }}</span>
                </div>
                <div class="stat-item">
                    <span>Доступность:</span>
                    <span class="stat-value">{{ stats.availability_percentage }}%</span>
                </div>
                <div class="stat-item">
                    <span>Время работы:</span>
                    <span class="stat-value">{{ stats.uptime }}</span>
                </div>
            </div>
            
            <div class="card">
                <h2>🔄 Последняя проверка</h2>
                <div class="stat-item">
                    <span>Время:</span>
                    <span class="stat-value">{{ stats.last_check_time }}</span>
                </div>
                <div class="stat-item">
                    <span>Интервал:</span>
                    <span class="stat-value">{{ stats.check_interval }} сек</span>
                </div>
                <div class="stat-item">
                    <span>Режим:</span>
                    <span class="stat-value">{{ stats.monitoring_mode }}</span>
                </div>
                <div class="stat-item">
                    <span>Тихий режим:</span>
                    <span class="stat-value">{{ stats.silent_mode }}</span>
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Ресурсы</h2>
                <div class="stat-item">
                    <span>Проверка ресурсов:</span>
                    <span class="stat-value">{{ stats.resource_check_status }}</span>
                </div>
                <div class="stat-item">
                    <span>Интервал проверки:</span>
                    <span class="stat-value">{{ stats.resource_check_interval }} мин</span>
                </div>
                <div class="stat-item">
                    <span>Проблем с ресурсами:</span>
                    <span class="stat-value status-warning">{{ stats.resource_alerts }}</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🖥️ Статус серверов</h2>
            <div class="server-list">
                {% for server in servers %}
                <div class="server-item {% if server.status == 'down' %}down{% elif server.status == 'warning' %}warning{% endif %}">
                    <div>
                        <div class="server-name">{{ server.name }}</div>
                        <div style="font-size: 0.8em; color: #666;">{{ server.ip }} • {{ server.type.upper() }}</div>
                    </div>
                    <div class="server-status {% if server.status == 'down' %}down{% elif server.status == 'warning' %}warning{% endif %}">
                        {{ server.status_display }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="location.reload()">🔄 Обновить</button>
        </div>
        
        <div class="last-update">
            Система мониторинга серверов • Версия 2.0
        </div>
    </div>

    <script>
        // Авто-обновление каждые 30 секунд
        setTimeout(() => {
            location.reload();
        }, 30000);
        
        // Обновление времени последнего обновления
        function updateLastUpdate() {
            const now = new Date();
            document.getElementById('lastUpdate').textContent = now.toLocaleString('ru-RU');
        }
        
        updateLastUpdate();
    </script>
</body>
</html>
"""

def get_monitoring_stats():
    """Получает статистику мониторинга"""
    try:
        # Пробуем получить данные из файла статистики
        stats_data = {}
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                stats_data = json.load(f)
        
        # Получаем текущий статус серверов
        from monitor_core import get_current_server_status, monitoring_active, last_check_time
        from monitor_core import is_silent_time, resource_history
        from extensions.server_list import initialize_servers
        
        current_status = get_current_server_status()
        servers_list = initialize_servers()
        
        # Формируем список серверов для отображения
        servers_display = []
        for server in servers_list:
            is_up = any(s["ip"] == server["ip"] for s in current_status["ok"])
            is_down = any(s["ip"] == server["ip"] for s in current_status["failed"])
            
            status = "up" if is_up else "down"
            status_display = "✅ Доступен" if is_up else "❌ Недоступен"
            
            # Проверяем ресурсы для предупреждений
            resources = None
            if server["ip"] in resource_history and resource_history[server["ip"]]:
                resources = resource_history[server["ip"]][-1]
                if resources and (resources.get("cpu", 0) > 80 or resources.get("ram", 0) > 85 or resources.get("disk", 0) > 80):
                    status = "warning"
                    status_display = "⚠️ Высокая нагрузка"
            
            servers_display.append({
                "name": server["name"],
                "ip": server["ip"],
                "type": server["type"],
                "status": status,
                "status_display": status_display
            })
        
        # Сортируем серверы: сначала проблемные, потом доступные
        servers_display.sort(key=lambda x: (0 if x["status"] == "down" else 1 if x["status"] == "warning" else 2))
        
        # Рассчитываем статистику
        total_servers = len(servers_list)
        servers_up = len(current_status["ok"])
        servers_down = len(current_status["failed"])
        availability_percentage = round((servers_up / total_servers) * 100, 1) if total_servers > 0 else 0
        
        # Получаем настройки из конфига
        from config import CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL
        resource_check_minutes = RESOURCE_CHECK_INTERVAL // 60
        
        # Считаем проблемы с ресурсами
        resource_alerts_count = 0
        for history in resource_history.values():
            if history:
                last_resource = history[-1]
                if (last_resource.get("cpu", 0) >= 99 or 
                    last_resource.get("ram", 0) >= 99 or 
                    last_resource.get("disk", 0) >= 75):
                    resource_alerts_count += 1
        
        stats = {
            "total_servers": total_servers,
            "servers_up": servers_up,
            "servers_down": servers_down,
            "availability_percentage": availability_percentage,
            "last_check_time": last_check_time.strftime("%H:%M:%S") if last_check_time else "N/A",
            "check_interval": CHECK_INTERVAL,
            "monitoring_mode": "🟢 Активен" if monitoring_active else "🔴 Приостановлен",
            "silent_mode": "🔇 Включен" if is_silent_time() else "🔊 Выключен",
            "resource_check_status": "🟢 Работает" if monitoring_active and not is_silent_time() else "⏸️ Приостановлен",
            "resource_check_interval": resource_check_minutes,
            "resource_alerts": resource_alerts_count,
            "uptime": stats_data.get("uptime", "N/A")
        }
        
        return stats, servers_display
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        # Возвращаем данные по умолчанию при ошибке
        return {
            "total_servers": 0,
            "servers_up": 0,
            "servers_down": 0,
            "availability_percentage": 0,
            "last_check_time": "N/A",
            "check_interval": 0,
            "monitoring_mode": "❌ Ошибка",
            "silent_mode": "N/A",
            "resource_check_status": "❌ Ошибка",
            "resource_check_interval": 0,
            "resource_alerts": 0,
            "uptime": "N/A"
        }, []

@app.route('/')
def index():
    """Главная страница веб-интерфейса"""
    stats, servers = get_monitoring_stats()
    
    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        servers=servers,
        last_update=datetime.now().strftime("%H:%M:%S")
    )

@app.route('/api/status')
def api_status():
    """API endpoint для получения статуса"""
    stats, servers = get_monitoring_stats()
    return jsonify({
        "status": "ok", 
        "message": "Система мониторинга работает",
        "data": {
            "stats": stats,
            "servers": servers,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/api/servers')
def api_servers():
    """API endpoint для получения списка серверов"""
    stats, servers = get_monitoring_stats()
    return jsonify({
        "servers": servers,
        "count": len(servers),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint для получения статистики"""
    stats, servers = get_monitoring_stats()
    return jsonify({
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

def start_web_server():
    """Запускает веб-сервер"""
    print(f"🌐 Запуск веб-интерфейса на http://{WEB_HOST}:{WEB_PORT}")
    try:
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")
        