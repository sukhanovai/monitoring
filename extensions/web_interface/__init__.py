"""
/extensions/web_interface/__init__.py
Server Monitoring System v8.4.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface
Система мониторинга серверов
Версия: 8.4.4
Автор: Александр Суханов (c)
Лицензия: MIT
Веб-интерфейс
"""

from flask import Flask, jsonify, render_template_string, request
from config.db_settings import WEB_PORT, WEB_HOST
from config.settings import STATS_FILE
from extensions.extension_manager import extension_manager
from extensions.supplier_stock_files import (
    SUPPLIER_STOCK_EXTENSION_ID,
    build_supplier_stock_source_stats,
    get_supplier_stock_config,
    get_supplier_stock_reports,
    run_supplier_stock_fetch,
    save_supplier_stock_config,
    start_supplier_stock_scheduler,
    summarize_supplier_stock_reports,
    summarize_supplier_stock_sources,
)
import threading
from datetime import datetime
import json
import re
import secrets
import subprocess
import sys
import time
import uuid

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
        .supplier-report-tabs {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        .supplier-report-tabs .btn.active {
            background: #667eea;
            color: #fff;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.4);
        }
        .supplier-report-group {
            display: none;
        }
        .supplier-report-group.active {
            display: block;
        }
        .status-flags {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 8px;
            font-size: 0.9em;
            color: #ccc;
        }
        .status-flag {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(20, 20, 30, 0.4);
            padding: 4px 8px;
            border-radius: 6px;
        }
        .supplier-details {
            font-size: 0.85em;
            color: #9fa6b2;
        }
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-overlay.active {
            display: flex;
        }
        .modal {
            background: rgba(30, 30, 40, 0.95);
            padding: 20px;
            border-radius: 12px;
            width: min(720px, 90vw);
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid #555;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .modal-list {
            margin-top: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .modal-item {
            padding: 10px;
            border-radius: 8px;
            background: rgba(50, 50, 60, 0.7);
            border-left: 3px solid #667eea;
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
            {% if supplier_stock_enabled %}
            <div class="tab" onclick="switchTab('supplier-stock')">📦 Остатки поставщиков</div>
            {% endif %}
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

        {% if supplier_stock_enabled %}
        <!-- Содержимое вкладки Остатки поставщиков -->
        <div id="supplier-stock" class="tab-content">
            <h2 style="margin-bottom: 20px;">📦 Остатки поставщиков</h2>

            <div class="dashboard">
                <div class="card">
                    <h2>⏰ Расписание</h2>
                    <div class="stat-item">
                        <span>Статус:</span>
                        <span class="stat-value">{{ supplier_stock.schedule_status }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Время:</span>
                        <span class="stat-value">{{ supplier_stock.schedule_time }}</span>
                    </div>
                    <div class="controls" style="margin-top: 15px; gap: 10px; flex-wrap: wrap;">
                        <input type="time" id="supplierScheduleTime" value="{{ supplier_stock.schedule_time_value }}"
                               style="padding: 8px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                        <label style="display: flex; align-items: center; gap: 6px;">
                            Период (дней):
                            <input type="number" id="supplierReportPeriod" min="1" value="{{ supplier_stock.report_period_days }}"
                                   style="padding: 8px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white; width: 110px;"
                                   title="Период отчетов (дней)" placeholder="Дней">
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px;">
                            <input type="checkbox" id="supplierScheduleEnabled" {% if supplier_stock.schedule_enabled %}checked{% endif %}>
                            Включено
                        </label>
                        <button class="btn btn-success" onclick="saveSupplierSchedule()">💾 Сохранить</button>
                        <button class="btn btn-info" onclick="runSupplierFetch()">📥 Запустить сейчас</button>
                    </div>
                </div>

                <div class="card">
                    <h2>📦 Источники</h2>
                    {% if supplier_stock.sources %}
                    <div class="server-list">
                        {% for source in supplier_stock.sources %}
                        <div class="server-item">
                            <div class="server-info">
                                <div class="server-name">
                                    {% if source.enabled %}🟢{% else %}🔴{% endif %}
                                    {{ source.name or source.id }}
                                </div>
                                <div class="server-details">{{ source.url or 'URL не задан' }}</div>
                                <div class="server-details">Файл: {{ source.output_name or 'не задан' }}</div>
                                <div class="server-details">Метод: {{ source.method }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="stat-item">Источники не настроены.</div>
                    {% endif %}
                </div>
            </div>

            <div class="card" style="margin-top: 20px;">
                <h2>📋 Результаты остатков поставщиков</h2>
                <div class="supplier-details" style="margin-bottom: 10px;">
                    Период: {{ supplier_stock.report_period_days }} дн.
                </div>
                <div class="supplier-report-tabs">
                    <button class="btn btn-info active" onclick="switchSupplierReports('download')">⬇️ Полученные скачиванием</button>
                    <button class="btn btn-info" onclick="switchSupplierReports('mail')">✉️ Полученные по почте</button>
                </div>
                <div id="supplier-report-download" class="supplier-report-group active">
                    {% if supplier_stock.report_groups.download %}
                    <div class="server-list">
                        {% for report in supplier_stock.report_groups.download %}
                        <div class="server-item">
                            <div class="server-info">
                                <div class="server-name">{{ report.source_name }}</div>
                                <div class="supplier-details">Последнее обновление: {{ report.timestamp or 'нет данных' }}</div>
                                {% if report.method %}
                                <div class="supplier-details">Метод: {{ report.method }}</div>
                                {% endif %}
                                <div class="status-flags">
                                    <div class="status-flag">{{ report.receive.icon }} Получение</div>
                                    <div class="status-flag">{{ report.processing.icon }} Обработка</div>
                                    <div class="status-flag">{{ report.transfer.icon }} Выгрузка</div>
                                </div>
                            </div>
                            <button class="btn btn-info" onclick="showSupplierSourceStats('{{ report.source_id }}', '{{ report.source_kind }}')">📊 Детали</button>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="stat-item">Нет данных за период по скачиванию.</div>
                    {% endif %}
                </div>
                <div id="supplier-report-mail" class="supplier-report-group">
                    {% if supplier_stock.report_groups.mail %}
                    <div class="server-list">
                        {% for report in supplier_stock.report_groups.mail %}
                        <div class="server-item">
                            <div class="server-info">
                                <div class="server-name">{{ report.source_name }}</div>
                                <div class="supplier-details">Последнее обновление: {{ report.timestamp or 'нет данных' }}</div>
                                <div class="status-flags">
                                    <div class="status-flag">{{ report.receive.icon }} Получение</div>
                                    <div class="status-flag">{{ report.processing.icon }} Обработка</div>
                                    <div class="status-flag">{{ report.transfer.icon }} Выгрузка</div>
                                </div>
                            </div>
                            <button class="btn btn-info" onclick="showSupplierSourceStats('{{ report.source_id }}', '{{ report.source_kind }}')">📊 Детали</button>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="stat-item">Нет данных за период по почте.</div>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endif %}
        
        <div id="supplierStatsModal" class="modal-overlay" onclick="closeSupplierSourceStats(event)">
            <div class="modal" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3 id="supplierStatsTitle">Статистика источника</h3>
                    <button class="btn btn-danger" onclick="closeSupplierSourceStats()">✖</button>
                </div>
                <div id="supplierStatsSummary" class="supplier-details"></div>
                <div id="supplierStatsEntries" class="modal-list"></div>
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

        // Запуск загрузки остатков поставщиков
        function runSupplierFetch() {
            addLog('📦 Запуск загрузки остатков поставщиков...');
            fetch('/api/supplier_stock/run', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success) {
                        setTimeout(() => location.reload(), 1500);
                    }
                })
                .catch(error => {
                    addLog(`Ошибка: ${error}`);
                });
        }

        // Сохранение расписания загрузки остатков
        function saveSupplierSchedule() {
            const timeInput = document.getElementById('supplierScheduleTime');
            const enabledInput = document.getElementById('supplierScheduleEnabled');
            const periodInput = document.getElementById('supplierReportPeriod');
            if (!timeInput || !enabledInput) {
                addLog('⚠️ Элементы расписания не найдены');
                return;
            }

            const payload = {
                time: timeInput.value,
                enabled: enabledInput.checked
            };
            if (periodInput) {
                payload.report_period_days = parseInt(periodInput.value, 10);
            }

            fetch('/api/supplier_stock/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success) {
                        setTimeout(() => location.reload(), 1500);
                    }
                })
                .catch(error => {
                    addLog(`Ошибка: ${error}`);
                });
        }

        function switchSupplierReports(kind) {
            document.querySelectorAll('.supplier-report-group').forEach(group => {
                group.classList.remove('active');
            });
            document.querySelectorAll('.supplier-report-tabs .btn').forEach(button => {
                button.classList.remove('active');
            });
            const target = document.getElementById(`supplier-report-${kind}`);
            if (target) {
                target.classList.add('active');
            }
            const button = document.querySelector(`.supplier-report-tabs .btn[onclick*="${kind}"]`);
            if (button) {
                button.classList.add('active');
            }
        }

        function showSupplierSourceStats(sourceId, sourceKind) {
            const modal = document.getElementById('supplierStatsModal');
            const title = document.getElementById('supplierStatsTitle');
            const summary = document.getElementById('supplierStatsSummary');
            const entriesContainer = document.getElementById('supplierStatsEntries');
            if (!modal || !title || !summary || !entriesContainer) {
                addLog('⚠️ Окно статистики недоступно');
                return;
            }
            title.textContent = `Статистика: ${sourceId}`;
            summary.textContent = 'Загрузка...';
            entriesContainer.innerHTML = '';
            modal.classList.add('active');

            const params = new URLSearchParams({
                source_id: sourceId,
                source_kind: sourceKind
            });
            fetch(`/api/supplier_stock/source_stats?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        summary.textContent = data.message || 'Ошибка загрузки статистики';
                        return;
                    }
                    const stats = data.stats || {};
                    summary.innerHTML = `
                        Период: ${data.period_days} дн. • Всего: ${stats.total || 0}
                        • Получено ✅ ${stats.receive_success || 0} / ❌ ${stats.receive_error || 0}
                        • Обработка ✅ ${stats.processing_success || 0} / ❌ ${stats.processing_error || 0}
                        • Выгрузка ✅ ${stats.transfer_success || 0} / ❌ ${stats.transfer_error || 0}
                    `;
                    const entries = data.entries || [];
                    if (!entries.length) {
                        entriesContainer.innerHTML = '<div class="stat-item">Нет записей за период.</div>';
                        return;
                    }
                    entriesContainer.innerHTML = entries.map(entry => `
                        <div class="modal-item">
                            <div class="server-details">${entry.timestamp || '—'}</div>
                            <div class="status-flags">
                                <div class="status-flag">${entry.receive.icon} Получение</div>
                                <div class="status-flag">${entry.processing.icon} Обработка</div>
                                <div class="status-flag">${entry.transfer.icon} Выгрузка</div>
                            </div>
                            ${entry.error ? `<div class="server-details">Ошибка: ${entry.error}</div>` : ''}
                        </div>
                    `).join('');
                })
                .catch(error => {
                    summary.textContent = `Ошибка: ${error}`;
                });
        }

        function closeSupplierSourceStats(event) {
            if (event && event.target !== event.currentTarget) {
                return;
            }
            const modal = document.getElementById('supplierStatsModal');
            if (modal) {
                modal.classList.remove('active');
            }
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
        if STATS_FILE.exists():
            stats_data = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        
        # Получаем текущий статус серверов
        from core.monitor_core import get_current_server_status, monitoring_active, last_check_time
        from core.monitor_core import is_silent_time, resource_history
        from extensions.server_checks import initialize_servers
        
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
        from config.db_settings import CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL
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



# --- Minimal mobile BFF auth/session layer (in-memory) ---
_MOBILE_TOKEN_TTL_SEC = 60 * 60 * 24
_mobile_tokens = {}


def _extract_credentials(payload):
    """Достаёт username/password из JSON или form payload."""
    payload = payload or {}
    username = payload.get("username") or payload.get("login") or payload.get("email")
    password = payload.get("password")
    return username, password


def _issue_mobile_token(subject):
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + _MOBILE_TOKEN_TTL_SEC
    _mobile_tokens[token] = {"sub": subject, "exp": expires_at}
    return token, expires_at


def _validate_mobile_token(auth_header):
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, "missing"

    token = auth_header.split(" ", 1)[1].strip()
    token_data = _mobile_tokens.get(token)
    if not token_data:
        return False, "invalid"

    if token_data["exp"] < int(time.time()):
        _mobile_tokens.pop(token, None)
        return False, "expired"

    return True, token_data


def _map_mobile_action_to_legacy(action: str) -> str | None:
    mapping = {
        "pause_monitoring": "toggle_monitoring",  # временный fallback
        "resume_monitoring": "toggle_monitoring",  # временный fallback
        "send_morning_report": "morning_report",
        "force_quiet": "toggle_silent",           # временный fallback
        "force_loud": "toggle_silent",            # временный fallback
    }
    return mapping.get(action)


@app.route('/v1/auth/token', methods=['POST'])
@app.route('/v1/auth/login', methods=['POST'])
@app.route('/api/v1/auth/token', methods=['POST'])
@app.route('/api/v1/auth/login', methods=['POST'])
@app.route('/auth/token', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
@app.route('/token', methods=['POST'])
def mobile_auth_token():
    """Минимальный auth endpoint для мобильного BFF-потока."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    username, password = _extract_credentials(payload)

    if not username or not password:
        return jsonify({
            "error": "invalid_request",
            "message": "Требуются username/login/email и password"
        }), 400

    token, expires_at = _issue_mobile_token(username)
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": _MOBILE_TOKEN_TTL_SEC,
        "scope": "monitoring:read monitoring:control",
        "issued_at": datetime.now().isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at).isoformat(),
    })


def _build_availability_payload(scope='all'):
    stats, servers = get_monitoring_stats()
    down_ips = {s.get('ip') for s in servers if s.get('status') == 'down'}

    items = []
    for s in servers:
        items.append({
            "ip": s.get("ip"),
            "name": s.get("name"),
            "status": "down" if s.get("ip") in down_ips else "up",
            "status_display": s.get("status_display"),
            "scope": scope,
        })

    return {
        "scope": scope,
        "total": len(items),
        "up": sum(1 for i in items if i["status"] == "up"),
        "down": sum(1 for i in items if i["status"] == "down"),
        "items": items,
        "timestamp": datetime.now().isoformat(),
        "summary": stats,
    }


@app.route('/v1/monitoring/availability', methods=['GET'])
@app.route('/api/v1/monitoring/availability', methods=['GET'])
def mobile_availability():
    """Mobile BFF endpoint совместимый с auth_token_probe.sh"""
    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        return jsonify({
            "error": "unauthorized",
            "message": "Bearer token required",
            "reason": token_data
        }), 401

    scope = request.args.get('scope', 'all')
    return jsonify(_build_availability_payload(scope=scope))


@app.route('/v1/monitoring/status', methods=['GET'])
@app.route('/api/v1/monitoring/status', methods=['GET'])
def mobile_status():
    """Синоним для быстрой проверки статуса с Bearer токеном."""
    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        return jsonify({
            "error": "unauthorized",
            "message": "Bearer token required",
            "reason": token_data
        }), 401

    return jsonify(_build_availability_payload(scope='all'))


@app.route('/v1/control/actions', methods=['POST'])
def v1_control_actions():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    payload = request.get_json(silent=True) or {}
    action = str(payload.get('action') or '').strip()
    if not action:
        return jsonify({
            "error": {
                "code": "INVALID_ACTION",
                "message": "Field 'action' is required",
                "request_id": request_id,
            }
        }), 400

    legacy_action = _map_mobile_action_to_legacy(action)
    if not legacy_action:
        return jsonify({
            "error": {
                "code": "INVALID_ACTION",
                "message": f"Unsupported action: {action}",
                "request_id": request_id,
            }
        }), 400

    try:
        with app.test_request_context(f"/api/run_action?action={legacy_action}"):
            legacy_response = api_run_action()

        if isinstance(legacy_response, tuple):
            response_obj, status_code = legacy_response
        else:
            response_obj, status_code = legacy_response, 200

        data = response_obj.get_json(silent=True) if hasattr(response_obj, 'get_json') else {}
        message = (data or {}).get('message') or 'Action processed'

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted" if status_code < 400 else "rejected",
            "message": message,
        }), (200 if status_code < 400 else status_code)

    except Exception as e:
        return jsonify({
            "error": {
                "code": "CONTROL_ACTION_FAILED",
                "message": str(e),
                "request_id": request_id,
            }
        }), 500


def _mask_secret(value):
    """Возвращает маскированное значение секрета без раскрытия исходной строки."""
    value_str = str(value or '').strip()
    if not value_str:
        return ''
    if ':' in value_str:
        prefix = value_str.split(':', 1)[0]
        return f"{prefix}:***"
    return '********'


def _hour_to_hhmm(value, fallback):
    try:
        hour_value = int(value)
        if 0 <= hour_value <= 23:
            return f"{hour_value:02d}:00"
    except (TypeError, ValueError):
        pass
    return fallback


@app.route('/v1/settings/monitoring', methods=['GET'])
def v1_get_settings_monitoring():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    from config.db_settings_app import settings_manager

    response = {
        "request_id": request_id,
        "settings": {
            "check_interval_sec": settings_manager.get_setting('CHECK_INTERVAL', 60),
            "timeout_sec": settings_manager.get_setting('API_TIMEOUT_SEC', 15),
            "max_downtime_sec": settings_manager.get_setting('MAX_FAIL_TIME', 900),
        }
    }
    app.logger.info("GET /v1/settings/monitoring request_id=%s", request_id)
    return jsonify(response), 200


@app.route('/v1/settings/bot', methods=['GET'])
def v1_get_settings_bot():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    from config.db_settings_app import settings_manager

    chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    if isinstance(chat_ids, list) and chat_ids:
        telegram_chat_id = str(chat_ids[0])
    elif chat_ids:
        telegram_chat_id = str(chat_ids)
    else:
        telegram_chat_id = ''

    token = settings_manager.get_setting('TELEGRAM_TOKEN', '')

    response = {
        "request_id": request_id,
        "settings": {
            "telegram_chat_id": telegram_chat_id,
            "masked_token": _mask_secret(token),
        }
    }
    app.logger.info("GET /v1/settings/bot request_id=%s", request_id)
    return jsonify(response), 200


@app.route('/v1/settings/time', methods=['GET'])
def v1_get_settings_time():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    from config.db_settings_app import settings_manager

    quiet_start = _hour_to_hhmm(settings_manager.get_setting('SILENT_START', 23), '23:00')
    quiet_end = _hour_to_hhmm(settings_manager.get_setting('SILENT_END', 8), '08:00')
    metrics_collection_time = str(settings_manager.get_setting('DATA_COLLECTION_TIME', '07:30'))

    response = {
        "request_id": request_id,
        "settings": {
            "quiet_start": quiet_start,
            "quiet_end": quiet_end,
            "metrics_collection_time": metrics_collection_time,
        }
    }
    app.logger.info("GET /v1/settings/time request_id=%s", request_id)
    return jsonify(response), 200


@app.route('/v1/settings/auth', methods=['GET'])
def v1_get_settings_auth():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    from config.db_settings_app import settings_manager

    ssh_password = settings_manager.get_setting('SSH_PASSWORD', '')
    windows_password = settings_manager.get_setting('WINDOWS_PASSWORD', '')

    response = {
        "request_id": request_id,
        "settings": {
            "auth_mode": str(settings_manager.get_setting('AUTH_MODE', 'mixed')),
            "ssh_username": str(settings_manager.get_setting('SSH_USERNAME', 'root')),
            "ssh_port": int(settings_manager.get_setting('SSH_PORT', 22)),
            "windows_username": str(settings_manager.get_setting('WINDOWS_USERNAME', 'Administrator')),
            "masked_ssh_password": _mask_secret(ssh_password),
            "masked_windows_password": _mask_secret(windows_password),
        }
    }
    app.logger.info("GET /v1/settings/auth request_id=%s", request_id)
    return jsonify(response), 200


@app.route('/v1/settings/monitoring', methods=['PATCH'])
def v1_settings_monitoring():
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get('Authorization'))
    if not is_ok:
        return jsonify({
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Invalid or expired token",
                "request_id": request_id,
            }
        }), 401

    payload = request.get_json(silent=True) or {}

    check_interval = payload.get('check_interval_sec')
    timeout_sec = payload.get('timeout_sec')
    max_downtime = payload.get('max_downtime_sec')

    if check_interval is None and timeout_sec is None and max_downtime is None:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "At least one field is required",
                "request_id": request_id,
            }
        }), 400

    try:
        from config.db_settings_app import settings_manager

        if check_interval is not None:
            check_interval = int(check_interval)
            if check_interval < 5:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "check_interval_sec must be >= 5", "request_id": request_id}}), 400
            settings_manager.set_setting('CHECK_INTERVAL', check_interval, 'monitoring', 'Интервал проверки серверов (секунды)', 'int')
        else:
            check_interval = settings_manager.get_setting('CHECK_INTERVAL', 60)

        if max_downtime is not None:
            max_downtime = int(max_downtime)
            if max_downtime < 30:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "max_downtime_sec must be >= 30", "request_id": request_id}}), 400
            settings_manager.set_setting('MAX_FAIL_TIME', max_downtime, 'monitoring', 'Максимальное время простоя до алерта (секунды)', 'int')
        else:
            max_downtime = settings_manager.get_setting('MAX_FAIL_TIME', 900)

        if timeout_sec is not None:
            timeout_sec = int(timeout_sec)
            if timeout_sec < 1:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "timeout_sec must be >= 1", "request_id": request_id}}), 400
            settings_manager.set_setting('API_TIMEOUT_SEC', timeout_sec, 'monitoring', 'Таймаут API (секунды)', 'int')
        else:
            timeout_sec = settings_manager.get_setting('API_TIMEOUT_SEC', 15)

        return jsonify({
            "request_id": request_id,
            "settings": {
                "check_interval_sec": check_interval,
                "timeout_sec": timeout_sec,
                "max_downtime_sec": max_downtime,
                "updated_at": datetime.now().isoformat(),
            }
        }), 200

    except Exception as e:
        return jsonify({
            "error": {
                "code": "CONFIG_STORE_UNAVAILABLE",
                "message": str(e),
                "request_id": request_id,
            }
        }), 500

@app.route('/')
def index():
    """Главная страница веб-интерфейса"""
    try:
        stats, servers = get_monitoring_stats()
        supplier_stock_enabled = extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID)
        supplier_stock = {}
        if supplier_stock_enabled:
            config = get_supplier_stock_config()
            download = config.get("download", {})
            schedule = download.get("schedule", {})
            schedule_time = schedule.get("time", "")
            period_days = config.get("reporting", {}).get("period_days", 7)
            supplier_stock = {
                "schedule_status": "🟢 Включено" if schedule.get("enabled") else "🔴 Выключено",
                "schedule_time": schedule_time or "не задано",
                "schedule_time_value": schedule_time or "",
                "schedule_enabled": bool(schedule.get("enabled")),
                "report_period_days": period_days,
                "sources": summarize_supplier_stock_sources(download.get("sources", [])),
                "report_groups": summarize_supplier_stock_reports(period_days),
            }

        return render_template_string(
            HTML_TEMPLATE,
            stats=stats,
            servers=servers,
            last_update=datetime.now().strftime("%H:%M:%S"),
            supplier_stock_enabled=supplier_stock_enabled,
            supplier_stock=supplier_stock
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
            from core.monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"✅ Быстрая проверка выполнена: {len(status['ok'])} доступно, {len(status['failed'])} недоступно"
            
        elif check_type == 'resources':
            # Запуск проверки ресурсов
            from core.monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "✅ Проверка ресурсов выполнена. Данные обновятся через 1-2 минуты."
            
        elif check_type == 'report':
            # Формирование отчета
            from core.monitor_core import send_morning_report
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
            from core.monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"✅ Проверка всех серверов выполнена: {len(status['ok'])} доступно, {len(status['failed'])} недоступно"
            
        elif action == 'check_resources':
            from core.monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "✅ Проверка ресурсов запущена. Данные обновятся через 1-2 минуты."
            
        elif action == 'morning_report':
            from core.monitor_core import send_morning_report
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

@app.route('/api/supplier_stock/run', methods=['POST'])
def api_supplier_stock_run():
    """API для запуска загрузки остатков поставщиков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    def _run():
        run_supplier_stock_fetch()

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "message": "✅ Загрузка остатков поставщиков запущена"})

@app.route('/api/supplier_stock/schedule', methods=['GET', 'POST'])
def api_supplier_stock_schedule():
    """API для управления расписанием загрузки остатков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    config = get_supplier_stock_config()
    schedule = config.get("download", {}).get("schedule", {})

    if request.method == 'GET':
        return jsonify({"success": True, "schedule": schedule})

    data = request.json or {}
    time_value = str(data.get("time", "")).strip()
    enabled_value = bool(data.get("enabled", False))
    report_period_days = data.get("report_period_days")

    if time_value and not re.match(r'^\\d{1,2}:\\d{2}$', time_value):
        return jsonify({"success": False, "message": "❌ Неверный формат времени. Используйте HH:MM"})

    schedule["time"] = time_value or schedule.get("time", "")
    schedule["enabled"] = enabled_value
    config["download"]["schedule"] = schedule
    if report_period_days is not None:
        try:
            config.setdefault("reporting", {})["period_days"] = int(str(report_period_days).strip())
        except (TypeError, ValueError):
            pass
    save_supplier_stock_config(config)

    return jsonify({"success": True, "message": "✅ Расписание обновлено", "schedule": schedule})

@app.route('/api/supplier_stock/reports')
def api_supplier_stock_reports():
    """API для получения отчетов по остаткам поставщиков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    limit = request.args.get('limit')
    try:
        limit_value = int(limit) if limit is not None else 20
    except ValueError:
        limit_value = 20
    period_days = request.args.get('period_days')
    try:
        period_value = int(period_days) if period_days else None
    except ValueError:
        period_value = None
    source_id = request.args.get('source_id')
    source_kind = request.args.get('source_kind')
    reports = get_supplier_stock_reports(
        limit_value,
        period_value,
        source_id=source_id,
        source_kind=source_kind,
    )
    return jsonify({"success": True, "reports": reports})

@app.route('/api/supplier_stock/source_stats')
def api_supplier_stock_source_stats():
    """API для получения детальной статистики по источнику остатков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    source_id = request.args.get("source_id")
    source_kind = request.args.get("source_kind")
    if not source_id:
        return jsonify({"success": False, "message": "❌ Не указан источник"})
    config = get_supplier_stock_config()
    period_days = config.get("reporting", {}).get("period_days", 7)
    stats = build_supplier_stock_source_stats(source_id, source_kind, period_days)
    return jsonify({
        "success": True,
        "period_days": period_days,
        "stats": stats.get("summary", {}),
        "entries": stats.get("entries", []),
    })

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
        from extensions.server_checks import initialize_servers
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
        if extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
            start_supplier_stock_scheduler()
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")

if __name__ == "__main__":
    start_web_server()
