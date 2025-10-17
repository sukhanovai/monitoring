from flask import Flask, jsonify, render_template_string, request
from config import WEB_PORT, WEB_HOST
import threading
from datetime import datetime
import json
import os
from config import STATS_FILE, DATA_DIR
import subprocess
import sys

app = Flask(__name__)

# HTML шаблон с вкладками и темной темой
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
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: rgba(30, 30, 40, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #444;
        }
        .header h1 {
            color: #fff;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header .status {
            font-size: 1.2em;
            color: #aaa;
        }
        
        /* Вкладки */
        .tabs {
            display: flex;
            background: rgba(30, 30, 40, 0.95);
            border-radius: 15px 15px 0 0;
            border: 1px solid #444;
            border-bottom: none;
            overflow: hidden;
        }
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            background: rgba(40, 40, 50, 0.8);
            border-right: 1px solid #444;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .tab:hover {
            background: rgba(60, 60, 80, 0.8);
        }
        .tab.active {
            background: rgba(80, 80, 120, 0.95);
            color: #fff;
        }
        .tab-content {
            display: none;
            background: rgba(30, 30, 40, 0.95);
            padding: 25px;
            border-radius: 0 0 15px 15px;
            border: 1px solid #444;
            border-top: none;
            min-height: 500px;
        }
        .tab-content.active {
            display: block;
        }
        
        /* Общие стили карточек */
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(40, 40, 50, 0.8);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            border: 1px solid #555;
        }
        .card h2 {
            color: #fff;
            margin-bottom: 15px;
            font-size: 1.4em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #555;
        }
        .stat-item:last-child {
            border-bottom: none;
        }
        .stat-value {
            font-weight: bold;
            font-size: 1.1em;
        }
        .status-up { color: #4CAF50; }
        .status-down { color: #f44336; }
        .status-warning { color: #FFC107; }
        .status-info { color: #2196F3; }
        
        /* Стили для списка серверов */
        .server-list {
            max-height: 500px;
            overflow-y: auto;
        }
        .server-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(50, 50, 60, 0.8);
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
            transition: transform 0.2s ease;
        }
        .server-item:hover {
            transform: translateX(5px);
            background: rgba(60, 60, 70, 0.9);
        }
        .server-item.down {
            border-left-color: #f44336;
            background: rgba(80, 40, 40, 0.8);
        }
        .server-item.warning {
            border-left-color: #FFC107;
            background: rgba(80, 70, 40, 0.8);
        }
        .server-name {
            font-weight: bold;
            color: #fff;
        }
        .server-details {
            font-size: 0.85em;
            color: #aaa;
            margin-top: 5px;
        }
        .server-status {
            font-size: 0.9em;
            padding: 6px 12px;
            border-radius: 15px;
            background: #4CAF50;
            color: white;
            font-weight: 500;
        }
        .server-status.down {
            background: #f44336;
        }
        .server-status.warning {
            background: #FFC107;
            color: #333;
        }
        
        /* Стили для ресурсов */
        .resources-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .resource-item {
            background: rgba(50, 50, 60, 0.8);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #555;
        }
        .resource-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .resource-title {
            font-weight: bold;
            color: #fff;
        }
        .resource-value {
            font-size: 1.3em;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
        }
        .progress-bar {
            height: 8px;
            background: #555;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .progress-cpu { background: linear-gradient(90deg, #4CAF50, #8BC34A); }
        .progress-ram { background: linear-gradient(90deg, #2196F3, #03A9F4); }
        .progress-disk { background: linear-gradient(90deg, #FF9800, #FFC107); }
        
        /* Кнопки */
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95em;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn-success { background: linear-gradient(135deg, #4CAF50, #45a049); }
        .btn-warning { background: linear-gradient(135deg, #FF9800, #F57C00); }
        .btn-danger { background: linear-gradient(135deg, #f44336, #d32f2f); }
        .btn-info { background: linear-gradient(135deg, #2196F3, #1976D2); }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.1em;
            margin: 20px auto;
            display: block;
            transition: all 0.3s ease;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        }
        
        .last-update {
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        /* Подвкладки ресурсов */
        .sub-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .sub-tab {
            padding: 10px 20px;
            background: rgba(50, 50, 60, 0.8);
            border-radius: 8px;
            cursor: pointer;
            border: 1px solid #555;
            transition: all 0.3s ease;
        }
        .sub-tab.active {
            background: #667eea;
            color: white;
        }
        .sub-tab:hover {
            background: rgba(80, 80, 100, 0.8);
        }
        
        /* Анимации */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.5s ease;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 2em;
            }
            .tabs {
                flex-direction: column;
            }
            .tab {
                border-right: none;
                border-bottom: 1px solid #444;
            }
            .controls {
                flex-direction: column;
            }
            .btn {
                width: 100%;
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
        
        <!-- Вкладки -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('overview')">📊 Обзор</div>
            <div class="tab" onclick="switchTab('servers')">🖥️ Серверы</div>
            <div class="tab" onclick="switchTab('resources')">📈 Ресурсы</div>
            <div class="tab" onclick="switchTab('controls')">🎛️ Управление</div>
        </div>
        
        <!-- Содержимое вкладки Обзор -->
        <div id="overview" class="tab-content active">
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
                </div>
                
                <div class="card">
                    <h2>🔄 Мониторинг</h2>
                    <div class="stat-item">
                        <span>Статус:</span>
                        <span class="stat-value status-info">{{ stats.monitoring_mode }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Тихий режим:</span>
                        <span class="stat-value">{{ stats.silent_mode }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Последняя проверка:</span>
                        <span class="stat-value">{{ stats.last_check_time }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Интервал:</span>
                        <span class="stat-value">{{ stats.check_interval }} сек</span>
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
                    <div class="stat-item">
                        <span>Время работы:</span>
                        <span class="stat-value">{{ stats.uptime }}</span>
                    </div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="runCheck('quick')">🔍 Быстрая проверка</button>
                <button class="btn btn-info" onclick="runCheck('resources')">📈 Проверить ресурсы</button>
                <button class="btn btn-warning" onclick="runCheck('report')">📊 Сформировать отчет</button>
            </div>
        </div>
        
        <!-- Содержимое вкладки Серверы -->
        <div id="servers" class="tab-content">
            <h2 style="margin-bottom: 20px;">🖥️ Статус серверов</h2>
            <div class="server-list">
                {% for server in servers %}
                <div class="server-item {% if server.status == 'down' %}down{% elif server.status == 'warning' %}warning{% endif %} fade-in">
                    <div>
                        <div class="server-name">{{ server.name }}</div>
                        <div class="server-details">{{ server.ip }} • {{ server.type.upper() }} • {{ server.os }}</div>
                        {% if server.resources %}
                        <div class="server-details">
                            CPU: {{ server.resources.cpu }}% | RAM: {{ server.resources.ram }}% | Disk: {{ server.resources.disk }}%
                        </div>
                        {% endif %}
                    </div>
                    <div class="server-status {% if server.status == 'down' %}down{% elif server.status == 'warning' %}warning{% endif %}">
                        {{ server.status_display }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Содержимое вкладки Ресурсы -->
        <div id="resources" class="tab-content">
            <h2 style="margin-bottom: 20px;">📈 Мониторинг ресурсов</h2>
            
            <!-- Подвкладки ресурсов -->
            <div class="sub-tabs">
                <div class="sub-tab active" onclick="switchSubTab('cpu')">💻 Процессор</div>
                <div class="sub-tab" onclick="switchSubTab('ram')">🧠 Память</div>
                <div class="sub-tab" onclick="switchSubTab('disk')">💾 Диски</div>
                <div class="sub-tab" onclick="switchSubTab('all')">📊 Все ресурсы</div>
            </div>
            
            <!-- CPU -->
            <div id="cpu-resources" class="sub-tab-content active">
                <div class="resources-grid">
                    {% for server in resource_servers %}
                    {% if server.resources %}
                    <div class="resource-item">
                        <div class="resource-header">
                            <div class="resource-title">{{ server.name }}</div>
                            <div class="server-status {% if server.resources.cpu > 90 %}warning{% endif %}">
                                {{ server.resources.cpu }}%
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-cpu" style="width: {{ server.resources.cpu }}%"></div>
                        </div>
                        <div class="server-details">{{ server.ip }} • {{ server.os }}</div>
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
            </div>
            
            <!-- RAM -->
            <div id="ram-resources" class="sub-tab-content">
                <div class="resources-grid">
                    {% for server in resource_servers %}
                    {% if server.resources %}
                    <div class="resource-item">
                        <div class="resource-header">
                            <div class="resource-title">{{ server.name }}</div>
                            <div class="server-status {% if server.resources.ram > 90 %}warning{% endif %}">
                                {{ server.resources.ram }}%
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-ram" style="width: {{ server.resources.ram }}%"></div>
                        </div>
                        <div class="server-details">{{ server.ip }} • {{ server.os }}</div>
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
            </div>
            
            <!-- Disk -->
            <div id="disk-resources" class="sub-tab-content">
                <div class="resources-grid">
                    {% for server in resource_servers %}
                    {% if server.resources %}
                    <div class="resource-item">
                        <div class="resource-header">
                            <div class="resource-title">{{ server.name }}</div>
                            <div class="server-status {% if server.resources.disk > 80 %}warning{% endif %}">
                                {{ server.resources.disk }}%
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-disk" style="width: {{ server.resources.disk }}%"></div>
                        </div>
                        <div class="server-details">{{ server.ip }} • {{ server.os }}</div>
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
            </div>
            
            <!-- All Resources -->
            <div id="all-resources" class="sub-tab-content">
                <div class="resources-grid">
                    {% for server in resource_servers %}
                    {% if server.resources %}
                    <div class="resource-item">
                        <div class="resource-header">
                            <div class="resource-title">{{ server.name }}</div>
                            <div class="server-status {% if server.resources.cpu > 90 or server.resources.ram > 90 or server.resources.disk > 80 %}warning{% endif %}">
                                📊
                            </div>
                        </div>
                        <div class="stat-item">
                            <span>💻 CPU:</span>
                            <span class="{% if server.resources.cpu > 90 %}status-warning{% else %}status-up{% endif %}">
                                {{ server.resources.cpu }}%
                            </span>
                        </div>
                        <div class="stat-item">
                            <span>🧠 RAM:</span>
                            <span class="{% if server.resources.ram > 90 %}status-warning{% else %}status-up{% endif %}">
                                {{ server.resources.ram }}%
                            </span>
                        </div>
                        <div class="stat-item">
                            <span>💾 Disk:</span>
                            <span class="{% if server.resources.disk > 80 %}status-warning{% else %}status-up{% endif %}">
                                {{ server.resources.disk }}%
                            </span>
                        </div>
                        <div class="server-details">{{ server.ip }} • {{ server.os }}</div>
                    </div>
                    {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- Содержимое вкладки Управление -->
        <div id="controls" class="tab-content">
            <h2 style="margin-bottom: 20px;">🎛️ Управление мониторингом</h2>
            
            <div class="dashboard">
                <div class="card">
                    <h2>🔧 Действия</h2>
                    <div class="controls" style="flex-direction: column; gap: 15px;">
                        <button class="btn btn-success" onclick="runAction('check_all')">🔍 Проверить все серверы</button>
                        <button class="btn btn-info" onclick="runAction('check_resources')">📈 Проверить ресурсы</button>
                        <button class="btn btn-warning" onclick="runAction('morning_report')">📊 Утренний отчет</button>
                        <button class="btn btn-danger" onclick="runAction('restart_service')">🔄 Перезапуск сервиса</button>
                    </div>
                </div>
                
                <div class="card">
                    <h2>⚙️ Настройки</h2>
                    <div class="stat-item">
                        <span>Текущий режим:</span>
                        <span class="stat-value">{{ stats.monitoring_mode }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Тихий режим:</span>
                        <span class="stat-value">{{ stats.silent_mode }}</span>
                    </div>
                    <div class="controls" style="margin-top: 20px;">
                        <button class="btn {% if stats.monitoring_mode == '🟢 Активен' %}btn-warning{% else %}btn-success{% endif %}" 
                                onclick="toggleMonitoring()">
                            {% if stats.monitoring_mode == '🟢 Активен' %}⏸️ Приостановить{% else %}▶️ Возобновить{% endif %}
                        </button>
                        <button class="btn {% if stats.silent_mode == '🔇 Включен' %}btn-info{% else %}btn-warning{% endif %}" 
                                onclick="toggleSilentMode()">
                            {% if stats.silent_mode == '🔇 Включен' %}🔊 Выключить тихий{% else %}🔇 Включить тихий{% endif %}
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h2>📋 Логи действий</h2>
                <div id="actionLogs" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.9em;">
                    <!-- Логи будут добавляться сюда -->
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">🔄 Обновить данные</button>
        
        <div class="last-update">
            Система мониторинга серверов • Версия 2.0 • Темная тема
        </div>
    </div>

    <script>
        // Переключение основных вкладок
        function switchTab(tabName) {
            // Скрыть все вкладки
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Показать выбранную вкладку
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        // Переключение подвкладок ресурсов
        function switchSubTab(resourceType) {
            // Скрыть все подвкладки
            document.querySelectorAll('.sub-tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.sub-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Показать выбранную подвкладку
            document.getElementById(resourceType + '-resources').classList.add('active');
            event.target.classList.add('active');
        }
        
        // Запуск проверок
        function runCheck(type) {
            addLog(`Запуск ${getCheckName(type)}...`);
            fetch(`/api/run_check?type=${type}`)
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success) {
                        setTimeout(() => location.reload(), 2000);
                    }
                })
                .catch(error => {
                    addLog(`Ошибка: ${error}`);
                });
        }
        
        // Запуск действий
        function runAction(action) {
            addLog(`Выполнение: ${getActionName(action)}...`);
            fetch(`/api/run_action?action=${action}`)
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success && data.reload) {
                        setTimeout(() => location.reload(), 2000);
                    }
                })
                .catch(error => {
                    addLog(`Ошибка: ${error}`);
                });
        }
        
        // Переключение мониторинга
        function toggleMonitoring() {
            const action = '{{ "pause" if stats.monitoring_mode == "🟢 Активен" else "resume" }}';
            runAction('toggle_monitoring');
        }
        
        // Переключение тихого режима
        function toggleSilentMode() {
            runAction('toggle_silent');
        }
        
        // Вспомогательные функции
        function getCheckName(type) {
            const names = {
                'quick': 'быстрой проверки',
                'resources': 'проверки ресурсов', 
                'report': 'формирования отчета'
            };
            return names[type] || type;
        }
        
        function getActionName(action) {
            const names = {
                'check_all': 'Проверка всех серверов',
                'check_resources': 'Проверка ресурсов',
                'morning_report': 'Формирование утреннего отчета',
                'restart_service': 'Перезапуск сервиса',
                'toggle_monitoring': 'Переключение мониторинга',
                'toggle_silent': 'Переключение тихого режима'
            };
            return names[action] || action;
        }
        
        function addLog(message) {
            const logDiv = document.getElementById('actionLogs');
            const timestamp = new Date().toLocaleTimeString('ru-RU');
            logDiv.innerHTML = `<div>[${timestamp}] ${message}</div>` + logDiv.innerHTML;
        }
        
        // Авто-обновление каждые 30 секунд
        setTimeout(() => {
            location.reload();
        }, 30000);
        
        // Обновление времени
        function updateLastUpdate() {
            const now = new Date();
            document.getElementById('lastUpdate').textContent = now.toLocaleString('ru-RU');
        }
        
        updateLastUpdate();
        
        // Показываем уведомления
        function showNotification(message, type = 'info') {
            // Простая реализация уведомлений
            addLog(message);
        }
    </script>
</body>
</html>
"""

def get_monitoring_stats():
    """Получает статистику мониторинга"""
    try:
        print("🔍 Обновление данных для веб-интерфейса...")
        
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
        
        print(f"📊 Статус серверов: {len(current_status['ok'])} доступно, {len(current_status['failed'])} недоступно")
        print(f"📈 Данные ресурсов: {len(resource_history)} серверов в истории")
        
        # Формируем список серверов для отображения
        servers_display = []
        resource_servers = []
        
        for server in servers_list:
            is_up = any(s["ip"] == server["ip"] for s in current_status["ok"])
            is_down = any(s["ip"] == server["ip"] for s in current_status["failed"])
            
            status = "up" if is_up else "down"
            status_display = "✅ Доступен" if is_up else "❌ Недоступен"
            
            # Получаем информацию о ресурсах
            resources = None
            os_info = "Unknown"
            if server["ip"] in resource_history and resource_history[server["ip"]]:
                resources = resource_history[server["ip"]][-1]
                os_info = resources.get("os", "Unknown")
                
                # Проверяем на проблемы с ресурсами
                if resources and (resources.get("cpu", 0) > 80 or resources.get("ram", 0) > 85 or resources.get("disk", 0) > 80):
                    status = "warning"
                    status_display = "⚠️ Высокая нагрузка"
            
            server_data = {
                "name": server["name"],
                "ip": server["ip"],
                "type": server["type"],
                "os": os_info,
                "status": status,
                "status_display": status_display,
                "resources": resources
            }
            
            servers_display.append(server_data)
            
            # Для вкладки ресурсов включаем только серверы с данными
            if resources and (resources.get("cpu", 0) > 0 or resources.get("ram", 0) > 0 or resources.get("disk", 0) > 0):
                resource_servers.append(server_data)
        
        # Сортируем серверы: сначала проблемные, потом доступные
        servers_display.sort(key=lambda x: (0 if x["status"] == "down" else 1 if x["status"] == "warning" else 2))
        resource_servers.sort(key=lambda x: x["resources"]["cpu"] if x["resources"] else 0, reverse=True)
        
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
        
        return stats, servers_display, resource_servers
        
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
        }, [], []

@app.route('/')
def index():
    """Главная страница веб-интерфейса"""
    stats, servers, resource_servers = get_monitoring_stats()
    
    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        servers=servers,
        resource_servers=resource_servers,
        last_update=datetime.now().strftime("%H:%M:%S")
    )

@app.route('/api/run_check')
def api_run_check():
    """API для запуска проверок"""
    check_type = request.args.get('type', 'quick')
    
    try:
        if check_type == 'quick':
            # Запуск быстрой проверки доступности
            from monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"✅ Быстрая проверка выполнена: {len(status['ok'])} доступно, {len(status['failed'])} недоступно"
            
        elif check_type == 'resources':
            # Запуск проверки ресурсов
            from monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "✅ Проверка ресурсов выполнена. Данные обновятся через 1-2 минуты."
            
        elif check_type == 'report':
            # Формирование отчета
            from monitor_core import send_morning_report
            send_morning_report()
            message = "✅ Отчет сформирован и отправлен в Telegram"
            
        else:
            message = "❌ Неизвестный тип проверки"
            
        return jsonify({"success": True, "message": message, "reload": check_type != 'resources'})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Ошибка: {str(e)}"})
        
@app.route('/api/run_action')
def api_run_action():
    """API для выполнения действий"""
    action = request.args.get('action', '')
    
    try:
        if action == 'check_all':
            from monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"✅ Проверка всех серверов выполнена: {len(status['ok'])} доступно, {len(status['failed'])} недоступно"
            
        elif action == 'check_resources':
            from monitor_core import force_resource_check
            force_resource_check()
            message = "✅ Принудительная проверка ресурсов запущена. Данные обновятся через 1-2 минуты."
            
        elif action == 'morning_report':
            from monitor_core import send_morning_report
            send_morning_report()
            message = "✅ Утренний отчет отправлен в Telegram"
            
        elif action == 'restart_service':
            # Перезапуск сервиса (осторожно!)
            import subprocess
            subprocess.run(['systemctl', 'restart', 'server-monitor.service'], check=True)
            message = "✅ Сервис перезапускается..."
            
        elif action == 'toggle_monitoring':
            from monitor_core import monitoring_active
            # В реальной реализации здесь нужно менять глобальную переменную
            message = "⚠️ Функция переключения мониторинга в разработке"
            
        elif action == 'toggle_silent':
            from monitor_core import silent_override
            # В реальной реализации здесь нужно менять глобальную переменную
            message = "⚠️ Функция переключения тихого режима в разработке"
            
        else:
            message = "❌ Неизвестное действие"
            
        return jsonify({
            "success": True, 
            "message": message, 
            "reload": action not in ['check_resources', 'toggle_monitoring', 'toggle_silent']
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Ошибка: {str(e)}"})
    
# Существующие API endpoints
@app.route('/api/status')
def api_status():
    """API endpoint для получения статуса"""
    stats, servers, resource_servers = get_monitoring_stats()
    return jsonify({
        "status": "ok", 
        "message": "Система мониторинга работает",
        "data": {
            "stats": stats,
            "servers": servers,
            "resource_servers": resource_servers,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/api/servers')
def api_servers():
    """API endpoint для получения списка серверов"""
    stats, servers, resource_servers = get_monitoring_stats()
    return jsonify({
        "servers": servers,
        "count": len(servers),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint для получения статистики"""
    stats, servers, resource_servers = get_monitoring_stats()
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
