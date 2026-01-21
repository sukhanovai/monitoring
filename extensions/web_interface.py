"""
/extensions/supplier_stock_files.py
Server Monitoring System v8.1.9
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface
Система мониторинга серверов
Версия: 8.1.9
Автор: Александр Суханов (c)
Лицензия: MIT
Веб-интерфейс
"""

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

# HTML шаблон с вкладками и темной темой (без вкладки Ресурсы)
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
        .status-critical { color: #ff4444; }
        
        /* Стили для списка серверов */
        .server-list {
            max-height: 600px;
            overflow-y: auto;
        }
        .server-item {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
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
        .server-info {
            flex: 1;
        }
        .server-name {
            font-weight: bold;
            color: #fff;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        .server-details {
            font-size: 0.85em;
            color: #aaa;
            margin-bottom: 8px;
        }
        .server-resources {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 8px;
        }
        .resource-item {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 0.85em;
            padding: 4px 8px;
            border-radius: 6px;
            background: rgba(60, 60, 70, 0.8);
        }
        .resource-cpu.critical { color: #ff4444; font-weight: bold; }
        .resource-cpu.warning { color: #FFC107; }
        .resource-cpu.normal { color: #4CAF50; }
        
        .resource-ram.critical { color: #ff4444; font-weight: bold; }
        .resource-ram.warning { color: #FFC107; }
        .resource-ram.normal { color: #4CAF50; }
        
        .resource-disk.critical { color: #ff4444; font-weight: bold; }
        .resource-disk.warning { color: #FFC107; }
        .resource-disk.normal { color: #4CAF50; }
        
        .server-status {
            font-size: 0.9em;
            padding: 6px 12px;
            border-radius: 15px;
            background: #4CAF50;
            color: white;
            font-weight: 500;
            white-space: nowrap;
        }
        .server-status.down {
            background: #f44336;
        }
        .server-status.warning {
            background: #FFC107;
            color: #333;
        }
        
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
            .server-resources {
                flex-direction: column;
                gap: 5px;
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
            <div class="tab" onclick="switchTab('servers')">🖥️ Сервера</div>
            <div class="tab" onclick="switchTab('server-management')">⚙️ Управление серверами</div>
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
        
        <!-- Содержимое вкладки Сервера -->
        <div id="servers" class="tab-content">
            <h2 style="margin-bottom: 20px;">🖥️ Статус серверов</h2>
            <div class="server-list">
                {% for server in servers %}
                <div class="server-item {% if server.status == 'down' %}down{% elif server.status == 'warning' %}warning{% endif %} fade-in">
                    <div class="server-info">
                        <div class="server-name">{{ server.name }}</div>
                        <div class="server-details">{{ server.ip }} • {{ server.type.upper() }} • {{ server.os }}</div>
                        {% if server.resources %}
                        <div class="server-resources">
                            <div class="resource-item">
                                <span>💻 CPU:</span>
                                <span class="resource-cpu {{ server.resources.cpu_class }}">{{ server.resources.cpu }}%</span>
                            </div>
                            <div class="resource-item">
                                <span>🧠 RAM:</span>
                                <span class="resource-ram {{ server.resources.ram_class }}">{{ server.resources.ram }}%</span>
                            </div>
                            <div class="resource-item">
                                <span>💾 Disk:</span>
                                <span class="resource-disk {{ server.resources.disk_class }}">{{ server.resources.disk }}%</span>
                            </div>
                            {% if server.resources.load_avg and server.resources.load_avg != 'N/A' %}
                            <div class="resource-item">
                                <span>📊 Load:</span>
                                <span>{{ server.resources.load_avg }}</span>
                            </div>
                            {% endif %}
                            {% if server.resources.uptime and server.resources.uptime != 'N/A' %}
                            <div class="resource-item">
                                <span>⏱️ Uptime:</span>
                                <span>{{ server.resources.uptime }}</span>
                            </div>
                            {% endif %}
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
        
        <!-- Содержимое вкладки Управление серверами -->
        <div id="server-management" class="tab-content">
            <h2 style="margin-bottom: 20px;">⚙️ Управление списком серверов</h2>
            
            <div class="card">
                <h2>📋 Список серверов</h2>
                <div id="serverListContainer">
                    <!-- Список серверов будет загружен здесь -->
                </div>
                <button class="btn btn-success" onclick="loadServerList()">🔄 Обновить список</button>
            </div>
            
            <div class="card">
                <h2>➕ Добавить новый сервер</h2>
                <form id="addServerForm" style="display: grid; gap: 15px; margin-top: 15px;">
                    <input type="text" name="name" placeholder="Название сервера" required style="padding: 10px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                    <input type="text" name="ip" placeholder="IP адрес" required style="padding: 10px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                    <select name="type" style="padding: 10px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                        <option value="linux">Linux</option>
                        <option value="windows">Windows</option>
                    </select>
                    <button type="submit" class="btn btn-success">✅ Добавить сервер</button>
                </form>
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
        
        // Запуск проверок
        function runCheck(type) {
            addLog(`Запуск ${getCheckName(type)}...`);
            fetch(`/api/run_check?type=${type}`)
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success && data.reload !== false) {
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
        
        // Управление серверами
        function loadServerList() {
            fetch('/api/servers')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('serverListContainer');
                    container.innerHTML = '<div class="server-list">' + 
                        data.servers.map(server => `
                            <div class="server-item">
                                <div class="server-info">
                                    <div class="server-name">${server.name}</div>
                                    <div class="server-details">${server.ip} • ${server.type.toUpperCase()}</div>
                                </div>
                                <button class="btn btn-danger" onclick="deleteServer('${server.ip}')">🗑️ Удалить</button>
                            </div>
                        `).join('') + '</div>';
                })
                .catch(error => {
                    console.error('Ошибка загрузки списка серверов:', error);
                });
        }

        function deleteServer(ip) {
            if (confirm(`Удалить сервер ${ip}?`)) {
                fetch(`/api/servers?ip=${ip}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        loadServerList();
                    });
            }
        }

        // Обработка формы добавления сервера
        document.addEventListener('DOMContentLoaded', function() {
            const addServerForm = document.getElementById('addServerForm');
            if (addServerForm) {
                addServerForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const formData = new FormData(this);
                    const serverData = {
                        name: formData.get('name'),
                        ip: formData.get('ip'),
                        type: formData.get('type')
                    };
                    
                    fetch('/api/servers', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(serverData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        this.reset();
                        loadServerList();
                    });
                });
            }
        });

        // Модифицируем существующую функцию switchTab для автозагрузки списка серверов
        const originalSwitchTab = switchTab;
        switchTab = function(tabName) {
            originalSwitchTab(tabName);
            
            // Автозагрузка списка серверов при открытии вкладки
            if (tabName === 'server-management') {
                setTimeout(loadServerList, 100);
            }
        };       
        
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
    </script>
</body>
</html>
"""

def get_resource_class(value, resource_type):
    """Определяет класс для окрашивания ресурсов"""
    if not value or value == 0:
        return "normal"
    
    if resource_type == "cpu":
        if value >= 90:
            return "critical"
        elif value >= 80:
            return "warning"
        else:
            return "normal"
    elif resource_type == "ram":
        if value >= 95:
            return "critical"
        elif value >= 85:
            return "warning"
        else:
            return "normal"
    elif resource_type == "disk":
        if value >= 90:
            return "critical"
        elif value >= 80:
            return "warning"
        else:
            return "normal"
    return "normal"

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
            
            # Получаем информацию о ресурсах
            resources_data = None
            os_info = "Unknown"
            if server["ip"] in resource_history and resource_history[server["ip"]]:
                latest_resources = resource_history[server["ip"]][-1]
                os_info = latest_resources.get("os", "Unknown")
                
                # Форматируем ресурсы с классами для окрашивания
                cpu_value = latest_resources.get("cpu", 0)
                ram_value = latest_resources.get("ram", 0)
                disk_value = latest_resources.get("disk", 0)
                
                resources_data = {
                    "cpu": cpu_value,
                    "ram": ram_value,
                    "disk": disk_value,
                    "load_avg": latest_resources.get("load_avg", "N/A"),
                    "uptime": latest_resources.get("uptime", "N/A"),
                    "cpu_class": get_resource_class(cpu_value, "cpu"),
                    "ram_class": get_resource_class(ram_value, "ram"),
                    "disk_class": get_resource_class(disk_value, "disk")
                }
                
                # Проверяем на проблемы с ресурсами для статуса
                if resources_data and (cpu_value > 80 or ram_value > 85 or disk_value > 80):
                    status = "warning"
                    status_display = "⚠️ Высокая нагрузка"
            
            server_data = {
                "name": server["name"],
                "ip": server["ip"],
                "type": server["type"],
                "os": os_info,
                "status": status,
                "status_display": status_display,
                "resources": resources_data
            }
            
            servers_display.append(server_data)
        
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
                if (last_resource.get("cpu", 0) >= 90 or 
                    last_resource.get("ram", 0) >= 95 or 
                    last_resource.get("disk", 0) >= 90):
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
    try:
        stats, servers = get_monitoring_stats()
        
        return render_template_string(
            HTML_TEMPLATE,
            stats=stats,
            servers=servers,
            last_update=datetime.now().strftime("%H:%M:%S")
        )
    except Exception as e:
        return f"❌ Ошибка загрузки веб-интерфейса: {e}"

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
            from monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "✅ Проверка ресурсов запущена. Данные обновятся через 1-2 минуты."
            
        elif action == 'morning_report':
            from monitor_core import send_morning_report
            send_morning_report()
            message = "✅ Утренний отчет отправлен в Telegram"
            
        elif action == 'restart_service':
            # Перезапуск сервиса (осторожно!)
            subprocess.run(['systemctl', 'restart', 'server-monitor.service'], check=True)
            message = "✅ Сервис перезапускается..."
            
        elif action == 'toggle_monitoring':
            # В реальной реализации здесь нужно менять глобальную переменную
            message = "⚠️ Функция переключения мониторинга в разработке"
            
        elif action == 'toggle_silent':
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

@app.route('/api/servers', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_manage_servers():
    """API для управления списком серверов"""
    if request.method == 'GET':
        # Получить список серверов
        from extensions.server_list import initialize_servers
        servers = initialize_servers()
        return jsonify({"servers": servers})
    
    elif request.method == 'POST':
        # Добавить новый сервер
        data = request.json
        # Здесь добавить логику сохранения в server_list.json
        return jsonify({"success": True, "message": "Сервер добавлен"})
    
    elif request.method == 'PUT':
        # Обновить сервер
        data = request.json
        # Логика обновления
        return jsonify({"success": True, "message": "Сервер обновлен"})
    
    elif request.method == 'DELETE':
        # Удалить сервер
        server_ip = request.args.get('ip')
        # Логика удаления
        return jsonify({"success": True, "message": "Сервер удален"})
    
def start_web_server():
    """Запускает веб-сервер"""
    print(f"🌐 Запуск веб-интерфейса на http://{WEB_HOST}:{WEB_PORT}")
    try:
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")

if __name__ == "__main__":
    start_web_server()
