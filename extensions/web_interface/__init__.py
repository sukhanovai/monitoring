"""
/extensions/web_interface/__init__.py
Server Monitoring System v8.12.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface
Система мониторинга серверов
Версия: 8.12.0
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
    parse_supplier_stock_schedule_times,
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
import os
import hmac
import hashlib
import base64
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
                        <input type="text" id="supplierScheduleTime" value="{{ supplier_stock.schedule_time_value }}"
                               placeholder="06:00, 12:30"
                               title="HH:MM, можно несколько через пробел/запятую/;"
                               style="padding: 8px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white; min-width: 180px;">
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
def _read_mobile_ttl_sec() -> int:
    default_ttl_sec = 60 * 60 * 24
    raw_ttl = str(os.getenv("MOBILE_TOKEN_TTL_SEC", "")).strip()
    if not raw_ttl:
        return default_ttl_sec

    try:
        ttl = int(raw_ttl)
    except ValueError:
        app.logger.warning("Invalid MOBILE_TOKEN_TTL_SEC=%r, fallback=%s", raw_ttl, default_ttl_sec)
        return default_ttl_sec

    if ttl < 0:
        app.logger.warning("Negative MOBILE_TOKEN_TTL_SEC=%s, fallback=%s", ttl, default_ttl_sec)
        return default_ttl_sec

    return ttl


def _read_non_negative_env_int(name: str, default: int) -> int:
    raw_value = str(os.getenv(name, "")).strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        app.logger.warning("Invalid %s=%r, fallback=%s", name, raw_value, default)
        return default
    if value < 0:
        app.logger.warning("Negative %s=%s, fallback=%s", name, value, default)
        return default
    return value


_MOBILE_TOKEN_TTL_SEC = _read_mobile_ttl_sec()
_MOBILE_AUTH_SECRET = os.getenv("MOBILE_AUTH_SECRET", "monitoring-mobile-bff-secret")
_MOBILE_STATIC_TOKEN = str(os.getenv("MOBILE_STATIC_TOKEN", "")).strip()
_MOBILE_DEFAULT_TOKEN = str(os.getenv("MOBILE_DEFAULT_TOKEN", "")).strip()
_MOBILE_SESSION_TOKEN_TTL_SEC = _read_non_negative_env_int("MOBILE_SESSION_TOKEN_TTL_SEC", 0)


def _mask_token(token: str) -> str:
    token = (token or "").strip()
    if len(token) <= 10:
        return "********"
    return f"{token[:6]}***{token[-4:]}"


def _extract_bearer_token(auth_header):
    if not auth_header:
        return None
    match = re.match(r"^Bearer\s+(.+)$", auth_header.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    token = match.group(1).strip()
    return token or None


def _mobile_token_hash(token: str) -> str:
    payload = f"{_MOBILE_AUTH_SECRET}:{token}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _get_mobile_tokens_conn():
    from config.db_settings_app import settings_manager
    conn = settings_manager.get_connection()
    conn.row_factory = None
    return conn


def _ensure_mobile_tokens_table():
    conn = _get_mobile_tokens_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mobile_api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                token_mask TEXT NOT NULL,
                subject TEXT NOT NULL,
                device_id TEXT,
                created_at INTEGER NOT NULL,
                expires_at INTEGER,
                revoked INTEGER DEFAULT 0,
                revoked_at INTEGER,
                last_used_at INTEGER,
                issued_via TEXT DEFAULT 'default_token'
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mobile_api_tokens_subject ON mobile_api_tokens(subject)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mobile_api_tokens_device_id ON mobile_api_tokens(device_id)')
        conn.commit()
    finally:
        conn.close()


def _issue_persistent_mobile_token(subject: str, device_id: str | None = None, reissue: bool = False):
    _ensure_mobile_tokens_table()
    now_ts = int(time.time())
    expires_at = None if _MOBILE_SESSION_TOKEN_TTL_SEC == 0 else now_ts + _MOBILE_SESSION_TOKEN_TTL_SEC
    raw_token = secrets.token_urlsafe(48)
    token_hash = _mobile_token_hash(raw_token)
    token_mask = _mask_token(raw_token)

    conn = _get_mobile_tokens_conn()
    try:
        cursor = conn.cursor()
        if reissue and device_id:
            cursor.execute(
                '''
                UPDATE mobile_api_tokens
                SET revoked = 1, revoked_at = ?
                WHERE device_id = ? AND revoked = 0
                ''',
                (now_ts, device_id),
            )
        cursor.execute(
            '''
            INSERT INTO mobile_api_tokens (
                token_hash, token_mask, subject, device_id, created_at, expires_at, revoked, last_used_at, issued_via
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'default_token')
            ''',
            (token_hash, token_mask, subject, device_id, now_ts, expires_at, now_ts),
        )
        conn.commit()
    finally:
        conn.close()

    return raw_token, expires_at, token_mask


def _validate_persistent_mobile_token(token: str):
    _ensure_mobile_tokens_table()
    now_ts = int(time.time())
    token_hash = _mobile_token_hash(token)

    conn = _get_mobile_tokens_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, subject, device_id, expires_at, revoked
            FROM mobile_api_tokens
            WHERE token_hash = ?
            LIMIT 1
            ''',
            (token_hash,),
        )
        row = cursor.fetchone()
        if not row:
            return False, "invalid"

        token_id, subject, device_id, expires_at, revoked = row
        if int(revoked or 0) == 1:
            return False, "invalid"
        if expires_at is not None and int(expires_at) < now_ts:
            return False, "expired"

        cursor.execute('UPDATE mobile_api_tokens SET last_used_at = ? WHERE id = ?', (now_ts, token_id))
        conn.commit()
        return True, {
            "sub": subject,
            "device_id": device_id,
            "exp": int(expires_at) if expires_at is not None else None,
            "auth_type": "db",
            "token_id": token_id,
        }
    finally:
        conn.close()


def _extract_credentials(payload):
    """Достаёт username/password из JSON или form payload."""
    payload = payload or {}
    username = payload.get("username") or payload.get("login") or payload.get("email")
    password = payload.get("password")
    return username, password


def _issue_mobile_token(subject):
    issued_at = int(time.time())
    expires_at = None if _MOBILE_TOKEN_TTL_SEC == 0 else issued_at + _MOBILE_TOKEN_TTL_SEC
    payload = {
        "sub": subject,
        "iat": issued_at,
    }
    if expires_at is not None:
        payload["exp"] = expires_at

    payload_raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_raw).decode("ascii").rstrip("=")
    signature = hmac.new(
        _MOBILE_AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token = f"{payload_b64}.{signature}"
    return token, expires_at


def _validate_mobile_token(auth_header):
    token = _extract_bearer_token(auth_header)
    if not token:
        return False, "missing"

    if _MOBILE_STATIC_TOKEN and hmac.compare_digest(token, _MOBILE_STATIC_TOKEN):
        return True, {"sub": "static-token", "exp": None, "auth_type": "static"}

    # Bootstrap token разрешен только для обмена на рабочий session token.
    if _MOBILE_DEFAULT_TOKEN and hmac.compare_digest(token, _MOBILE_DEFAULT_TOKEN):
        return False, "bootstrap_only"

    is_db_ok, db_token_data = _validate_persistent_mobile_token(token)
    if is_db_ok:
        return True, db_token_data
    if db_token_data == "expired":
        return False, "expired"

    try:
        payload_b64, provided_sig = token.rsplit(".", 1)
    except ValueError:
        return False, "invalid"

    expected_sig = hmac.new(
        _MOBILE_AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, provided_sig):
        return False, "invalid"

    padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
    try:
        payload_raw = base64.urlsafe_b64decode(padded_payload.encode("ascii"))
        token_data = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return False, "invalid"

    if not isinstance(token_data, dict):
        return False, "invalid"

    if "exp" in token_data and token_data["exp"] is not None:
        try:
            exp_ts = int(token_data["exp"])
        except (TypeError, ValueError):
            return False, "invalid"
        if exp_ts < int(time.time()):
            return False, "expired"
    elif _MOBILE_TOKEN_TTL_SEC != 0:
        return False, "invalid"

    return True, token_data


def _map_mobile_action_to_legacy(action: str) -> str | None:
    mapping = {
        "pause_monitoring": "toggle_monitoring",  # legacy fallback
        "resume_monitoring": "toggle_monitoring",  # legacy fallback
        "send_morning_report": "morning_report",
        "force_quiet": "toggle_silent",           # legacy fallback
        "force_loud": "toggle_silent",            # legacy fallback
    }
    return mapping.get(action)


def _execute_mobile_control_action(action: str):
    """
    Executes explicit control actions for Android API.
    Returns tuple: (ok: bool, message: str, result: str)
    """
    try:
        import core.monitor_core as monitor_core
    except Exception as e:
        return False, f"monitor core unavailable: {e}", "failed"

    if action == "pause_monitoring":
        monitor_core.monitoring_active = False
        return True, "Мониторинг приостановлен", "applied"

    if action == "resume_monitoring":
        monitor_core.monitoring_active = True
        return True, "Мониторинг возобновлен", "applied"

    if action == "send_morning_report":
        from modules.morning_report import morning_report
        report_text = morning_report.force_report()
        return True, report_text, "accepted"

    if action == "force_quiet":
        monitor_core.set_silent_override(True)
        return True, "Принудительно включен тихий режим", "applied"

    if action == "force_loud":
        monitor_core.set_silent_override(False)
        return True, "Принудительно включен громкий режим", "applied"

    if action == "auto_mode":
        monitor_core.set_silent_override(None)
        return True, "Включен автоматический режим quiet/loud", "applied"

    return False, f"Unsupported action: {action}", "failed"


@app.route('/v1/auth/token', methods=['POST'])
@app.route('/v1/auth/login', methods=['POST'])
@app.route('/api/v1/auth/token', methods=['POST'])
@app.route('/api/v1/auth/login', methods=['POST'])
@app.route('/auth/token', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
@app.route('/token', methods=['POST'])
def mobile_auth_token():
    """Auth endpoint: bootstrap-token -> session token (DB), fallback на legacy username/password."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    bearer_token = _extract_bearer_token(request.headers.get("Authorization"))

    if _MOBILE_DEFAULT_TOKEN and bearer_token and hmac.compare_digest(bearer_token, _MOBILE_DEFAULT_TOKEN):
        device_id = str(payload.get("device_id") or request.headers.get("X-Device-ID") or "").strip() or None
        subject_raw = str(payload.get("subject") or payload.get("client_name") or device_id or "android-client").strip()
        subject = subject_raw[:128] if subject_raw else "android-client"
        reissue = bool(payload.get("reissue", True))

        token, expires_at, token_mask = _issue_persistent_mobile_token(
            subject=subject,
            device_id=device_id,
            reissue=reissue,
        )

        return jsonify({
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": _MOBILE_SESSION_TOKEN_TTL_SEC if _MOBILE_SESSION_TOKEN_TTL_SEC > 0 else None,
            "scope": "monitoring:read monitoring:control",
            "issued_at": datetime.now().isoformat(),
            "expires_at": datetime.fromtimestamp(expires_at).isoformat() if expires_at is not None else None,
            "subject": subject,
            "token_mask": token_mask,
            "auth_type": "bootstrap_exchange",
        })

    username, password = _extract_credentials(payload)
    if not username or not password:
        return jsonify({
            "error": "invalid_request",
            "message": "Требуется Authorization: Bearer <MOBILE_DEFAULT_TOKEN> или username/login/email + password"
        }), 400

    token, expires_at = _issue_mobile_token(username)
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": _MOBILE_TOKEN_TTL_SEC if _MOBILE_TOKEN_TTL_SEC > 0 else None,
        "scope": "monitoring:read monitoring:control",
        "issued_at": datetime.now().isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at).isoformat() if expires_at is not None else None,
        "auth_type": "legacy_credentials",
    })


@app.route('/v1/auth/token/reissue', methods=['POST'])
@app.route('/api/v1/auth/token/reissue', methods=['POST'])
def mobile_auth_token_reissue():
    """Явный перевыпуск токена по bootstrap token (например, после переустановки приложения)."""
    if not _MOBILE_DEFAULT_TOKEN:
        return jsonify({
            "error": "bootstrap_token_not_configured",
            "message": "MOBILE_DEFAULT_TOKEN is not configured on server"
        }), 503

    bearer_token = _extract_bearer_token(request.headers.get("Authorization"))
    if not bearer_token or not hmac.compare_digest(bearer_token, _MOBILE_DEFAULT_TOKEN):
        return jsonify({
            "error": "unauthorized",
            "message": "Bearer MOBILE_DEFAULT_TOKEN required"
        }), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    device_id = str(payload.get("device_id") or request.headers.get("X-Device-ID") or "").strip() or None
    subject_raw = str(payload.get("subject") or payload.get("client_name") or device_id or "android-client").strip()
    subject = subject_raw[:128] if subject_raw else "android-client"

    token, expires_at, token_mask = _issue_persistent_mobile_token(
        subject=subject,
        device_id=device_id,
        reissue=True,
    )

    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": _MOBILE_SESSION_TOKEN_TTL_SEC if _MOBILE_SESSION_TOKEN_TTL_SEC > 0 else None,
        "scope": "monitoring:read monitoring:control",
        "issued_at": datetime.now().isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at).isoformat() if expires_at is not None else None,
        "subject": subject,
        "token_mask": token_mask,
        "auth_type": "reissued",
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
    started_at = time.time()
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        app.logger.warning(
            "GET /v1/monitoring/availability unauthorized request_id=%s reason=%s duration_ms=%s",
            request_id,
            token_data,
            int((time.time() - started_at) * 1000),
        )
        response = jsonify({
            "error": "unauthorized",
            "message": "Bearer token required",
            "reason": token_data,
            "request_id": request_id,
        })
        response.headers['X-Request-ID'] = request_id
        return response, 401

    scope = request.args.get('scope', 'all')
    payload = _build_availability_payload(scope=scope)
    payload['request_id'] = request_id
    duration_ms = int((time.time() - started_at) * 1000)
    app.logger.info(
        "GET /v1/monitoring/availability request_id=%s status=200 duration_ms=%s total=%s",
        request_id,
        duration_ms,
        payload.get('total', 0),
    )
    response = jsonify(payload)
    response.headers['X-Request-ID'] = request_id
    return response


@app.route('/v1/monitoring/status', methods=['GET'])
@app.route('/api/v1/monitoring/status', methods=['GET'])
def mobile_status():
    """Синоним для быстрой проверки статуса с Bearer токеном."""
    started_at = time.time()
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        app.logger.warning(
            "GET /v1/monitoring/status unauthorized request_id=%s reason=%s duration_ms=%s",
            request_id,
            token_data,
            int((time.time() - started_at) * 1000),
        )
        response = jsonify({
            "error": "unauthorized",
            "message": "Bearer token required",
            "reason": token_data,
            "request_id": request_id,
        })
        response.headers['X-Request-ID'] = request_id
        return response, 401

    payload = _build_availability_payload(scope='all')
    payload['request_id'] = request_id
    duration_ms = int((time.time() - started_at) * 1000)
    app.logger.info(
        "GET /v1/monitoring/status request_id=%s status=200 duration_ms=%s total=%s",
        request_id,
        duration_ms,
        payload.get('total', 0),
    )
    response = jsonify(payload)
    response.headers['X-Request-ID'] = request_id
    return response


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

    ok, message, result = _execute_mobile_control_action(action)
    if ok:
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": result,
            "message": message,
        }), 200

    # Backward compatibility fallback for legacy action path.
    legacy_action = _map_mobile_action_to_legacy(action)
    if legacy_action:
        try:
            with app.test_request_context(f"/api/run_action?action={legacy_action}"):
                legacy_response = api_run_action()

            if isinstance(legacy_response, tuple):
                response_obj, status_code = legacy_response
            else:
                response_obj, status_code = legacy_response, 200

            data = response_obj.get_json(silent=True) if hasattr(response_obj, 'get_json') else {}
            fallback_message = (data or {}).get('message') or message or 'Action processed'
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted" if status_code < 400 else "rejected",
                "message": fallback_message,
            }), (200 if status_code < 400 else status_code)
        except Exception as e:
            return jsonify({
                "error": {
                    "code": "CONTROL_ACTION_FAILED",
                    "message": str(e),
                    "request_id": request_id,
                }
            }), 500

    return jsonify({
        "error": {
            "code": "INVALID_ACTION",
            "message": message,
            "request_id": request_id,
        }
    }), 400


@app.route('/v1/control/status', methods=['GET'])
@app.route('/api/v1/control/status', methods=['GET'])
def v1_control_status():
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

    import core.monitor_core as monitor_core

    monitoring_active = bool(getattr(monitor_core, 'monitoring_active', True))
    silent_active = bool(monitor_core.is_silent_time())
    silent_override = monitor_core.get_silent_override()

    if silent_override is None:
        silent_mode = "auto"
    elif silent_override:
        silent_mode = "force_quiet"
    else:
        silent_mode = "force_loud"

    return jsonify({
        "request_id": request_id,
        "monitoring_active": monitoring_active,
        "monitoring_status": "active" if monitoring_active else "paused",
        "silent_active": silent_active,
        "silent_mode": silent_mode,
        "silent_override": silent_override,
    }), 200


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

    raw_chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(chat_id).strip() for chat_id in raw_chat_ids if str(chat_id).strip()]
    elif raw_chat_ids:
        chat_ids = [str(raw_chat_ids).strip()]
    else:
        chat_ids = []

    token = settings_manager.get_setting('TELEGRAM_TOKEN', '')

    response = {
        "request_id": request_id,
        "settings": {
            "telegram_chat_id": chat_ids[0] if chat_ids else '',
            "telegram_chat_ids": chat_ids,
            "masked_token": _mask_secret(token),
        }
    }
    app.logger.info("GET /v1/settings/bot request_id=%s", request_id)
    return jsonify(response), 200


@app.route('/v1/settings/bot', methods=['PATCH'])
def v1_settings_bot():
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
    token = payload.get('telegram_bot_token')
    single_chat_id = payload.get('telegram_chat_id')
    chat_ids = payload.get('telegram_chat_ids')

    if token is None and single_chat_id is None and chat_ids is None:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "At least one field is required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager

    if token is not None:
        settings_manager.set_setting('TELEGRAM_TOKEN', str(token), 'telegram')

    if chat_ids is not None:
        if not isinstance(chat_ids, list):
            return jsonify({
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "telegram_chat_ids must be an array",
                    "request_id": request_id,
                }
            }), 400
        normalized_chat_ids = [str(chat_id).strip() for chat_id in chat_ids if str(chat_id).strip()]
        settings_manager.set_setting('CHAT_IDS', normalized_chat_ids, 'telegram')
    elif single_chat_id is not None:
        value = str(single_chat_id).strip()
        settings_manager.set_setting('CHAT_IDS', [value] if value else [], 'telegram')

    raw_chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    if isinstance(raw_chat_ids, list):
        normalized_chat_ids = [str(chat_id).strip() for chat_id in raw_chat_ids if str(chat_id).strip()]
    elif raw_chat_ids:
        normalized_chat_ids = [str(raw_chat_ids).strip()]
    else:
        normalized_chat_ids = []

    saved_token = settings_manager.get_setting('TELEGRAM_TOKEN', '')
    return jsonify({
        "request_id": request_id,
        "settings": {
            "telegram_chat_id": normalized_chat_ids[0] if normalized_chat_ids else '',
            "telegram_chat_ids": normalized_chat_ids,
            "masked_token": _mask_secret(saved_token),
        }
    }), 200


@app.route('/v1/settings/bot/chats', methods=['POST'])
def v1_settings_bot_add_chat():
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
    chat_id = str(payload.get('chat_id') or '').strip()
    if not chat_id:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "chat_id is required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    raw_chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(item).strip() for item in raw_chat_ids if str(item).strip()]
    elif raw_chat_ids:
        chat_ids = [str(raw_chat_ids).strip()]
    else:
        chat_ids = []

    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        settings_manager.set_setting('CHAT_IDS', chat_ids, 'telegram')

    return jsonify({
        "request_id": request_id,
        "settings": {
            "telegram_chat_ids": chat_ids,
            "telegram_chat_id": chat_ids[0] if chat_ids else '',
        }
    }), 200


@app.route('/v1/settings/bot/chats/<chat_id>', methods=['DELETE'])
def v1_settings_bot_remove_chat(chat_id):
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

    target_chat_id = str(chat_id).strip()
    from config.db_settings_app import settings_manager
    raw_chat_ids = settings_manager.get_setting('CHAT_IDS', [])
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(item).strip() for item in raw_chat_ids if str(item).strip()]
    elif raw_chat_ids:
        chat_ids = [str(raw_chat_ids).strip()]
    else:
        chat_ids = []

    chat_ids = [item for item in chat_ids if item != target_chat_id]
    settings_manager.set_setting('CHAT_IDS', chat_ids, 'telegram')

    return jsonify({
        "request_id": request_id,
        "settings": {
            "telegram_chat_ids": chat_ids,
            "telegram_chat_id": chat_ids[0] if chat_ids else '',
        }
    }), 200


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
    windows_credentials = settings_manager.get_windows_credentials()
    safe_windows_credentials = []
    for item in windows_credentials:
        safe_item = dict(item)
        if 'password' in safe_item:
            safe_item['password'] = _mask_secret(safe_item.get('password'))
        safe_windows_credentials.append(safe_item)

    response = {
        "request_id": request_id,
        "settings": {
            "auth_mode": str(settings_manager.get_setting('AUTH_MODE', 'mixed')),
            "ssh_username": str(settings_manager.get_setting('SSH_USERNAME', 'root')),
            "ssh_port": int(settings_manager.get_setting('SSH_PORT', 22)),
            "ssh_key_path": str(settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa')),
            "windows_username": str(settings_manager.get_setting('WINDOWS_USERNAME', 'Administrator')),
            "masked_ssh_password": _mask_secret(ssh_password),
            "masked_windows_password": _mask_secret(windows_password),
            "windows_credentials": safe_windows_credentials,
            "windows_server_types": settings_manager.get_windows_server_types(),
        }
    }
    app.logger.info("GET /v1/settings/auth request_id=%s", request_id)
    return jsonify(response), 200


@app.route('/v1/settings/auth', methods=['PATCH'])
def v1_settings_auth():
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

    auth_mode = payload.get('auth_mode')
    ssh_username = payload.get('ssh_username')
    ssh_port = payload.get('ssh_port')
    ssh_key_path = payload.get('ssh_key_path')
    windows_username = payload.get('windows_username')
    ssh_password = payload.get('ssh_password')
    windows_password = payload.get('windows_password')

    if (
        auth_mode is None and ssh_username is None and ssh_port is None and ssh_key_path is None
        and windows_username is None and ssh_password is None and windows_password is None
    ):
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "At least one field is required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager

    if auth_mode is not None:
        settings_manager.set_setting('AUTH_MODE', str(auth_mode).strip(), 'auth')
    if ssh_username is not None:
        settings_manager.set_setting('SSH_USERNAME', str(ssh_username).strip(), 'auth')
    if ssh_port is not None:
        settings_manager.set_setting('SSH_PORT', int(ssh_port), 'auth', data_type='int')
    if ssh_key_path is not None:
        settings_manager.set_setting('SSH_KEY_PATH', str(ssh_key_path).strip(), 'auth')
    if windows_username is not None:
        settings_manager.set_setting('WINDOWS_USERNAME', str(windows_username).strip(), 'auth')
    if ssh_password is not None:
        settings_manager.set_setting('SSH_PASSWORD', str(ssh_password), 'auth')
    if windows_password is not None:
        settings_manager.set_setting('WINDOWS_PASSWORD', str(windows_password), 'auth')

    return v1_get_settings_auth()


@app.route('/v1/settings/auth/windows-credentials', methods=['GET'])
def v1_get_windows_credentials():
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
    windows_credentials = settings_manager.get_windows_credentials()
    safe_windows_credentials = []
    for item in windows_credentials:
        safe_item = dict(item)
        if 'password' in safe_item:
            safe_item['password'] = _mask_secret(safe_item.get('password'))
        safe_windows_credentials.append(safe_item)
    return jsonify({
        "request_id": request_id,
        "items": safe_windows_credentials,
        "server_types": settings_manager.get_windows_server_types(),
    }), 200


@app.route('/v1/settings/auth/windows-credentials', methods=['POST'])
def v1_add_windows_credential():
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
    username = str(payload.get('username') or '').strip()
    password = str(payload.get('password') or '').strip()
    server_type = str(payload.get('server_type') or 'default').strip() or 'default'
    priority = int(payload.get('priority') or 0)

    if not username or not password:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "username and password are required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    ok = settings_manager.add_windows_credential(username, password, server_type, priority)
    if not ok:
        return jsonify({
            "error": {
                "code": "CONFIG_STORE_UNAVAILABLE",
                "message": "failed to add windows credential",
                "request_id": request_id,
            }
        }), 500

    return v1_get_windows_credentials()


@app.route('/v1/settings/auth/windows-credentials/<int:cred_id>', methods=['DELETE'])
def v1_delete_windows_credential(cred_id):
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
    ok = settings_manager.delete_windows_credential(int(cred_id))
    if not ok:
        return jsonify({
            "error": {
                "code": "CONFIG_STORE_UNAVAILABLE",
                "message": "failed to delete windows credential",
                "request_id": request_id,
            }
        }), 500

    return v1_get_windows_credentials()


def _build_windows_types_stats(settings_manager):
    credentials = settings_manager.get_windows_credentials()
    grouped = {type_name: {"total": 0, "active": 0, "inactive": 0} for type_name in settings_manager.get_windows_server_types()}
    for cred in credentials:
        server_type = str(cred.get('server_type') or 'default')
        bucket = grouped.setdefault(server_type, {"total": 0, "active": 0, "inactive": 0})
        bucket["total"] += 1
        if cred.get('enabled'):
            bucket["active"] += 1
        else:
            bucket["inactive"] += 1
    return grouped


@app.route('/v1/settings/auth/windows-types', methods=['GET'])
def v1_get_windows_types():
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
    stats = _build_windows_types_stats(settings_manager)
    return jsonify({
        "request_id": request_id,
        "types": [
            {
                "name": type_name,
                "total": values["total"],
                "active": values["active"],
                "inactive": values["inactive"],
            }
            for type_name, values in sorted(stats.items())
        ],
        "summary": {
            "types_count": len(stats),
            "credentials_count": sum(item["total"] for item in stats.values()),
        }
    }), 200


@app.route('/v1/settings/auth/windows-types', methods=['POST'])
def v1_create_windows_type():
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
    type_name = str(payload.get('name') or '').strip()
    if not type_name:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "name is required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    existing = set(settings_manager.get_windows_server_types())
    if type_name in existing:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": "type already exists",
                "request_id": request_id,
            }
        }), 409

    # В БД тип существует только через учетные записи: создаем и сразу отключаем тех. запись.
    settings_manager.add_windows_credential(
        username=f"user_{type_name}",
        password="temp_password",
        server_type=type_name,
        priority=0,
    )
    created = settings_manager.get_windows_credentials(type_name)
    if created:
        settings_manager.update_windows_credential(created[0]['id'], enabled=0)

    return v1_get_windows_types()


@app.route('/v1/settings/auth/windows-types/<type_name>', methods=['PATCH'])
def v1_rename_windows_type(type_name):
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
    new_name = str(payload.get('new_name') or '').strip()
    old_name = str(type_name or '').strip()
    if not old_name or not new_name:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "new_name is required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    existing = set(settings_manager.get_windows_server_types())
    if old_name not in existing:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "type not found",
                "request_id": request_id,
            }
        }), 404
    if new_name in existing and new_name != old_name:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": "target type already exists",
                "request_id": request_id,
            }
        }), 409

    for cred in settings_manager.get_windows_credentials(old_name):
        settings_manager.update_windows_credential(cred['id'], server_type=new_name)

    return v1_get_windows_types()


@app.route('/v1/settings/auth/windows-types/merge', methods=['POST'])
def v1_merge_windows_types():
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
    source_type = str(payload.get('source_type') or '').strip()
    target_type = str(payload.get('target_type') or '').strip()
    if not source_type or not target_type or source_type == target_type:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "source_type and target_type are required and must differ",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    existing = set(settings_manager.get_windows_server_types())
    if source_type not in existing or target_type not in existing:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "source or target type not found",
                "request_id": request_id,
            }
        }), 404

    for cred in settings_manager.get_windows_credentials(source_type):
        settings_manager.update_windows_credential(cred['id'], server_type=target_type)

    return v1_get_windows_types()


@app.route('/v1/settings/auth/windows-types/<type_name>', methods=['DELETE'])
def v1_delete_windows_type(type_name):
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

    source_type = str(type_name or '').strip()
    target_type = str(request.args.get('target_type') or 'default').strip() or 'default'
    if source_type == 'default':
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "type 'default' cannot be deleted",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    existing = set(settings_manager.get_windows_server_types())
    if source_type not in existing:
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "type not found",
                "request_id": request_id,
            }
        }), 404

    if target_type not in existing:
        settings_manager.add_windows_credential(
            username=f"user_{target_type}",
            password="temp_password",
            server_type=target_type,
            priority=0,
        )
        created = settings_manager.get_windows_credentials(target_type)
        if created:
            settings_manager.update_windows_credential(created[0]['id'], enabled=0)

    for cred in settings_manager.get_windows_credentials(source_type):
        settings_manager.update_windows_credential(cred['id'], server_type=target_type)

    return v1_get_windows_types()


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


def _normalize_server_type(raw_value):
    normalized = str(raw_value or '').strip().lower()
    aliases = {
        'windows': 'rdp',
        'linux': 'ssh',
        'rdp': 'rdp',
        'ssh': 'ssh',
        'ping': 'ping',
    }
    return aliases.get(normalized)


@app.route('/v1/settings/servers', methods=['GET'])
def v1_get_settings_servers():
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
    servers = settings_manager.get_all_servers(include_disabled=True)
    return jsonify({
        "request_id": request_id,
        "items": servers,
        "summary": {
            "total": len(servers),
            "enabled": sum(1 for item in servers if item.get("enabled")),
            "disabled": sum(1 for item in servers if not item.get("enabled")),
        }
    }), 200


@app.route('/v1/settings/servers', methods=['POST'])
def v1_add_settings_server():
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
    ip = str(payload.get('ip') or '').strip()
    name = str(payload.get('name') or '').strip()
    server_type = _normalize_server_type(payload.get('type'))
    timeout = payload.get('timeout')
    enabled = payload.get('enabled')

    if not ip or not name or not server_type:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "ip, name and type are required",
                "request_id": request_id,
            }
        }), 400

    try:
        timeout_value = int(timeout) if timeout is not None else 30
        if timeout_value < 1:
            raise ValueError("timeout must be >= 1")
    except Exception:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "timeout must be integer >= 1",
                "request_id": request_id,
            }
        }), 400

    enabled_value = True if enabled is None else bool(enabled)
    from config.db_settings_app import settings_manager
    ok = settings_manager.add_server(
        ip=ip,
        name=name,
        server_type=server_type,
        timeout=timeout_value,
        enabled=enabled_value,
    )
    if not ok:
        return jsonify({
            "error": {
                "code": "CONFIG_STORE_UNAVAILABLE",
                "message": "failed to add server",
                "request_id": request_id,
            }
        }), 500

    return v1_get_settings_servers()


@app.route('/v1/settings/servers/<path:ip>', methods=['PATCH'])
def v1_update_settings_server(ip):
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
    name = payload.get('name')
    raw_type = payload.get('type')
    server_type = _normalize_server_type(raw_type) if raw_type is not None else None
    timeout = payload.get('timeout')
    enabled = payload.get('enabled')

    if name is None and raw_type is None and timeout is None and enabled is None:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "At least one field is required",
                "request_id": request_id,
            }
        }), 400

    timeout_value = None
    if timeout is not None:
        try:
            timeout_value = int(timeout)
            if timeout_value < 1:
                raise ValueError("timeout must be >= 1")
        except Exception:
            return jsonify({
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "timeout must be integer >= 1",
                    "request_id": request_id,
                }
            }), 400

    if raw_type is not None and server_type is None:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "type must be one of: rdp, ssh, ping",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    ok = settings_manager.update_server(
        ip=str(ip).strip(),
        name=str(name).strip() if name is not None else None,
        server_type=server_type,
        timeout=timeout_value,
        enabled=bool(enabled) if enabled is not None else None,
    )
    if not ok:
        return jsonify({
            "error": {
                "code": "SERVER_NOT_FOUND",
                "message": "server not found or update skipped",
                "request_id": request_id,
            }
        }), 404

    return v1_get_settings_servers()


@app.route('/v1/settings/servers/<path:ip>/enabled', methods=['PATCH'])
def v1_toggle_settings_server(ip):
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
    if 'enabled' not in payload:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "enabled field is required",
                "request_id": request_id,
            }
        }), 400

    from config.db_settings_app import settings_manager
    ok = settings_manager.set_server_enabled(str(ip).strip(), bool(payload.get('enabled')))
    if not ok:
        return jsonify({
            "error": {
                "code": "SERVER_NOT_FOUND",
                "message": "server not found",
                "request_id": request_id,
            }
        }), 404

    return v1_get_settings_servers()


@app.route('/v1/settings/servers/<path:ip>', methods=['DELETE'])
def v1_delete_settings_server(ip):
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
    ok = settings_manager.delete_server(str(ip).strip())
    if not ok:
        return jsonify({
            "error": {
                "code": "CONFIG_STORE_UNAVAILABLE",
                "message": "failed to delete server",
                "request_id": request_id,
            }
        }), 500

    return v1_get_settings_servers()

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
    """API ??? ?????????? ????????"""
    action = request.args.get('action', '')
    
    try:
        if action == 'check_all':
            from core.monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"? ???????? ???? ???????? ?????????: {len(status['ok'])} ????????, {len(status['failed'])} ??????????"
            
        elif action == 'check_resources':
            from core.monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "? ???????? ???????? ????????. ?????? ????????? ????? 1-2 ??????."
            
        elif action == 'morning_report':
            from core.monitor_core import send_morning_report
            send_morning_report()
            message = "? ???????? ????? ????????? ? Telegram"
            
        elif action == 'restart_service':
            # ?????????? ??????? (?????????!)
            subprocess.run(['systemctl', 'restart', 'server-monitor.service'], check=True)
            message = "? ?????? ???????????????..."
            
        elif action == 'toggle_monitoring':
            # ? ???????? ?????????? ????? ????? ?????? ?????????? ??????????
            message = "?? ??????? ???????????? ??????????? ? ??????????"
            
        elif action == 'toggle_silent':
            # ? ???????? ?????????? ????? ????? ?????? ?????????? ??????????
            message = "?? ??????? ???????????? ?????? ?????? ? ??????????"
            
        else:
            message = "? ??????????? ????????"
            
        return jsonify({
            "success": True, 
            "message": message, 
            "reload": action not in ['check_resources', 'toggle_monitoring', 'toggle_silent']
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"? ??????: {str(e)}"})

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

    if time_value:
        schedule_times = parse_supplier_stock_schedule_times(time_value)
        if not schedule_times:
            return jsonify({
                "success": False,
                "message": "❌ Неверный формат времени. Используйте HH:MM, разделители: пробел, запятая или ;",
            })
        schedule["time"] = ', '.join(schedule_times)
    else:
        schedule["time"] = schedule.get("time", "")
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
