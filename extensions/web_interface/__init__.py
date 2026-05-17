"""
/extensions/web_interface/__init__.py
Server Monitoring System v8.62.4
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface
Система мониторинга серверов
Версия: 8.62.4
Автор: Александр Суханов (c)
Лицензия: MIT
Веб-интерфейс
"""

from flask import Flask, jsonify, render_template_string, request
from config.db_settings import WEB_PORT, WEB_HOST
from config.settings import STATS_FILE
from extensions.extension_manager import extension_manager
from extensions.server_checks import initialize_servers, check_server_availability
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
import ast
import re
import os
import sqlite3
import hmac
import hashlib
import base64
import secrets
import subprocess
import sys
import time
import uuid
from urllib.parse import quote, unquote

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
    Returns tuple: (ok: bool, message: str, result: str, menu_options: list[dict] | None)
    """
    from core.config_manager import config_manager as settings_manager

    menu_actions = {
        "backup_hosts",
        "backup_proxmox",
        "backup_databases",
        "backup_mail",
        "backup_stock_loads",
        "supplier_stock_reports",
        "zfs",
        "zfs_menu",
        "zfs_free_space",
        "zfs_pool_free_space_menu",
    }
    resource_threshold_settings = {
        "set_cpu_warning": ("CPU_WARNING", "CPU предупреждение"),
        "set_cpu_critical": ("CPU_CRITICAL", "CPU критический"),
        "set_ram_warning": ("RAM_WARNING", "RAM предупреждение"),
        "set_ram_critical": ("RAM_CRITICAL", "RAM критический"),
        "set_disk_warning": ("DISK_WARNING", "Disk предупреждение"),
        "set_disk_critical": ("DISK_CRITICAL", "Disk критический"),
    }

    if action.startswith("set_"):
        action_name, raw_value = (action.split("|", 1) + [""])[:2]
        threshold_meta = resource_threshold_settings.get(action_name)
        if threshold_meta is None:
            return False, f"Неизвестное действие: {action_name}", "failed", None

        setting_key, setting_title = threshold_meta
        value_raw = raw_value.strip()
        if not value_raw:
            return False, (
                f"Для «{setting_title}» передай значение 0-100: "
                f"`{action_name}|<число>`"
            ), "failed", None

        try:
            threshold_value = int(value_raw)
        except ValueError:
            return False, f"Порог «{setting_title}» должен быть целым числом 0-100.", "failed", None

        if threshold_value < 0 or threshold_value > 100:
            return False, f"Порог «{setting_title}» должен быть в диапазоне 0-100.", "failed", None

        settings_manager.set_setting(setting_key, threshold_value, "monitoring")

        cpu_warning = settings_manager.get_setting('CPU_WARNING', 80)
        cpu_critical = settings_manager.get_setting('CPU_CRITICAL', 90)
        ram_warning = settings_manager.get_setting('RAM_WARNING', 85)
        ram_critical = settings_manager.get_setting('RAM_CRITICAL', 95)
        disk_warning = settings_manager.get_setting('DISK_WARNING', 80)
        disk_critical = settings_manager.get_setting('DISK_CRITICAL', 90)

        return True, (
            f"✅ {setting_title}: {threshold_value}%\n\n"
            "Текущие пороги:\n"
            f"• CPU предупреждение: {cpu_warning}%\n"
            f"• CPU критический: {cpu_critical}%\n"
            f"• RAM предупреждение: {ram_warning}%\n"
            f"• RAM критический: {ram_critical}%\n"
            f"• Disk предупреждение: {disk_warning}%\n"
            f"• Disk критический: {disk_critical}%"
        ), "accepted", [
            {"label": "💻 CPU предупреждение", "action": "set_cpu_warning"},
            {"label": "💻 CPU критический", "action": "set_cpu_critical"},
            {"label": "🧠 RAM предупреждение", "action": "set_ram_warning"},
            {"label": "🧠 RAM критический", "action": "set_ram_critical"},
            {"label": "💾 Disk предупреждение", "action": "set_disk_warning"},
            {"label": "💾 Disk критический", "action": "set_disk_critical"},
            {"label": "↩️ Назад", "action": "settings_extensions_back_local"},
            {"label": "✖️ Закрыть", "action": "settings_extensions_close_local"},
        ]

    if (
        action in menu_actions
        or action.startswith("backup_host_")
        or action.startswith("zfsp_")
        or action.startswith("db_detail_")
        or action.startswith("settings_db_toggle_monitor_")
    ):
        from extensions.extension_manager import extension_manager

        extension_requirements = {
            "backup_hosts": ("backup_monitor", "💾 Мониторинг бэкапов Proxmox отключён"),
            "backup_databases": ("database_backup_monitor", "🗃️ Мониторинг бэкапов БД отключён"),
            "backup_mail": ("mail_backup_monitor", "📬 Мониторинг бэкапов почты отключён"),
            "backup_stock_loads": ("stock_load_monitor", "📦 Мониторинг остатков 1С отключён"),
            "supplier_stock_reports": ("supplier_stock_files", "📦 Остатки поставщиков отключены"),
            "zfs": ("zfs_monitor", "🧊 Мониторинг ZFS отключён"),
            "zfs_menu": ("zfs_monitor", "🧊 Мониторинг ZFS отключён"),
            "zfs_pool_free_space_menu": ("zfs_pool_free_space_monitor", "💽 Мониторинг свободного места ZFS-пулов отключён"),
        }

        extension_requirement = extension_requirements.get(action)
        if extension_requirement is None and action.startswith("zfsp_"):
            extension_requirement = ("zfs_pool_free_space_monitor", "💽 Мониторинг свободного места ZFS-пулов отключён")
        if extension_requirement is None and action.startswith("db_detail_"):
            extension_requirement = ("database_backup_monitor", "🗃️ Мониторинг бэкапов БД отключён")
        if extension_requirement is None and action.startswith("settings_db_toggle_monitor_"):
            extension_requirement = ("database_backup_monitor", "🗃️ Мониторинг бэкапов БД отключён")
        if extension_requirement is not None:
            extension_id, disabled_message = extension_requirement
            if not extension_manager.is_extension_enabled(extension_id):
                return False, disabled_message, "failed", None

        try:
            from extensions.backup_monitor.bot_handler import BackupMonitorBot
            backup_bot = BackupMonitorBot()
        except Exception as exc:
            return False, f"Не удалось открыть раздел {action}: {exc}", "failed", None

        if action == "backup_proxmox":
            action = "backup_hosts"

        if action == "zfs":
            action = "zfs_menu"

        if action == "zfs_pool_free_space_menu":
            from extensions.zfs_pool_free_space import build_status_lines, collect_zfs_pool_free_space

            results, errors = collect_zfs_pool_free_space()
            status_message = "\n".join(build_status_lines(results, errors))
            return True, status_message, "accepted", [
                {"label": "🔄 Обновить", "action": "zfs_pool_free_space_menu"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]

        if action == "zfsp_hosts_list" or action.startswith("zfsp_"):
            from extensions.zfs_pool_free_space import get_hosts_config, save_hosts_config

            def _build_zfsp_hosts_response(message_prefix: str | None = None):
                hosts = get_hosts_config()
                lines = ["⚙️ Хосты мониторинга свободного места ZFS", ""]
                if message_prefix:
                    lines.append(message_prefix)
                    lines.append("")

                if not hosts:
                    lines.append("❌ Хосты не настроены.")
                else:
                    for host_name in sorted(hosts.keys()):
                        host_cfg = hosts.get(host_name) or {}
                        status = "🟢" if host_cfg.get("enabled", True) else "🔴"
                        ip = str(host_cfg.get("ip", "")).strip() or "не задан"
                        threshold = int(host_cfg.get("threshold", 15))
                        lines.append(f"{status} {host_name}")
                        lines.append(f"   └ IP: {ip} · Порог: {threshold}%")

                menu_options = []
                for host_name in sorted(hosts.keys()):
                    host_cfg = hosts.get(host_name) or {}
                    enabled = bool(host_cfg.get("enabled", True))
                    toggle_text = "⛔️ Отключить" if enabled else "✅ Включить"
                    menu_options.extend(
                        [
                            {"label": f"✏️ Имя: {host_name}", "action": f"zfsp_edit_name_{host_name}"},
                            {"label": f"🌐 IP: {host_name}", "action": f"zfsp_edit_ip_{host_name}"},
                            {"label": f"🎚 Порог: {host_name}", "action": f"zfsp_edit_threshold_{host_name}"},
                            {"label": f"🗑 Удалить: {host_name}", "action": f"zfsp_delete_{host_name}"},
                            {"label": f"{toggle_text}: {host_name}", "action": f"zfsp_toggle_{host_name}"},
                        ]
                    )

                menu_options.extend(
                    [
                        {"label": "➕ Добавить хост", "action": "zfsp_add"},
                        {"label": "↩️ Назад", "action": "zfs_pool_free_space_menu"},
                    ]
                )
                return True, "\n".join(lines), "accepted", menu_options

            if action == "zfsp_hosts_list":
                return _build_zfsp_hosts_response()

            if action.startswith("zfsp_toggle_"):
                host_name = action.replace("zfsp_toggle_", "", 1).strip()
                hosts = get_hosts_config()
                if host_name in hosts:
                    hosts[host_name]["enabled"] = not bool(hosts[host_name].get("enabled", True))
                    save_hosts_config(hosts)
                    return _build_zfsp_hosts_response(f"✅ Обновлён статус хоста: {host_name}")
                return _build_zfsp_hosts_response(f"⚠️ Хост не найден: {host_name}")

            if action.startswith("zfsp_delete_"):
                host_name = action.replace("zfsp_delete_", "", 1).strip()
                hosts = get_hosts_config()
                if host_name in hosts:
                    hosts.pop(host_name, None)
                    save_hosts_config(hosts)
                    return _build_zfsp_hosts_response(f"✅ Хост удалён: {host_name}")
                return _build_zfsp_hosts_response(f"⚠️ Хост не найден: {host_name}")

            if action == "zfsp_add":
                return _build_zfsp_hosts_response(
                    "ℹ️ Добавление хоста из Android пока в формате действия:\n"
                    "zfsp_add|<name>|<ip>|<threshold 1-95>"
                )

            if action.startswith("zfsp_add|"):
                parts = action.split("|", 3)
                if len(parts) < 4:
                    return _build_zfsp_hosts_response("❌ Неверный формат. Используй zfsp_add|<name>|<ip>|<threshold>")
                _, host_name, host_ip, threshold_raw = parts
                host_name = unquote(host_name).strip()
                host_ip = unquote(host_ip).strip()
                try:
                    threshold = int(threshold_raw.strip())
                except ValueError:
                    return _build_zfsp_hosts_response("❌ Порог должен быть целым числом 1-95.")
                if not host_name or not host_ip or threshold < 1 or threshold > 95:
                    return _build_zfsp_hosts_response("❌ Проверь name/ip/threshold (threshold: 1-95).")
                hosts = get_hosts_config()
                hosts[host_name] = {"ip": host_ip, "threshold": threshold, "enabled": True}
                save_hosts_config(hosts)
                return _build_zfsp_hosts_response(f"✅ Хост добавлен: {host_name}")

            if action.startswith("zfsp_edit_name_"):
                host_and_new = action.replace("zfsp_edit_name_", "", 1)
                if "|" not in host_and_new:
                    return _build_zfsp_hosts_response(
                        "ℹ️ Переименование из Android: zfsp_edit_name_<old>|<new_name>"
                    )
                old_name, new_name = host_and_new.split("|", 1)
                old_name = unquote(old_name).strip()
                new_name = unquote(new_name).strip()
                hosts = get_hosts_config()
                if not old_name or not new_name:
                    return _build_zfsp_hosts_response("❌ Имена не должны быть пустыми.")
                if old_name not in hosts:
                    return _build_zfsp_hosts_response(f"⚠️ Хост не найден: {old_name}")
                if new_name in hosts and new_name != old_name:
                    return _build_zfsp_hosts_response(f"❌ Хост уже существует: {new_name}")
                host_data = dict(hosts.pop(old_name))
                hosts[new_name] = host_data
                save_hosts_config(hosts)
                return _build_zfsp_hosts_response(f"✅ Имя хоста обновлено: {old_name} → {new_name}")

            if action.startswith("zfsp_edit_ip_"):
                host_and_ip = action.replace("zfsp_edit_ip_", "", 1)
                if "|" not in host_and_ip:
                    return _build_zfsp_hosts_response(
                        "ℹ️ Изменение IP из Android: zfsp_edit_ip_<name>|<new_ip>"
                    )
                host_name, new_ip = host_and_ip.split("|", 1)
                host_name = unquote(host_name).strip()
                new_ip = unquote(new_ip).strip()
                hosts = get_hosts_config()
                if host_name not in hosts or not new_ip:
                    return _build_zfsp_hosts_response("❌ Хост не найден или новый IP пустой.")
                hosts[host_name]["ip"] = new_ip
                save_hosts_config(hosts)
                return _build_zfsp_hosts_response(f"✅ IP обновлён: {host_name}")

            if action.startswith("zfsp_edit_threshold_"):
                host_and_threshold = action.replace("zfsp_edit_threshold_", "", 1)
                if "|" not in host_and_threshold:
                    return _build_zfsp_hosts_response(
                        "ℹ️ Изменение порога из Android: zfsp_edit_threshold_<name>|<1-95>"
                    )
                host_name, threshold_raw = host_and_threshold.split("|", 1)
                host_name = host_name.strip()
                try:
                    threshold = int(threshold_raw.strip())
                except ValueError:
                    return _build_zfsp_hosts_response("❌ Порог должен быть числом 1-95.")
                hosts = get_hosts_config()
                if host_name not in hosts:
                    return _build_zfsp_hosts_response(f"⚠️ Хост не найден: {host_name}")
                if threshold < 1 or threshold > 95:
                    return _build_zfsp_hosts_response("❌ Порог должен быть в диапазоне 1-95.")
                hosts[host_name]["threshold"] = threshold
                save_hosts_config(hosts)
                return _build_zfsp_hosts_response(f"✅ Порог обновлён: {host_name}")

            return _build_zfsp_hosts_response("⚠️ Действие пока не поддерживается в Android UI.")

        if action == "backup_hosts":
            hosts = backup_bot.get_all_hosts(include_disabled=True)
            if not hosts:
                return True, "💾 Бэкапы Proxmox\n\nДанные по хостам пока отсутствуют.", "accepted", None
            problem_hosts = 0
            disabled_hosts = 0
            menu_options = []
            for host in hosts:
                host_enabled = backup_bot.is_host_enabled(host)
                if not host_enabled:
                    disabled_hosts += 1
                    problem_hosts += 1
                    host_prefix = "⚪"
                else:
                    host_status = backup_bot.get_host_display_status(host)
                    is_problem = host_status != "success"
                    if is_problem:
                        problem_hosts += 1
                    host_prefix = "🔴" if is_problem else "🟢"
                menu_options.append(
                    {
                        "label": f"{host_prefix} {host}",
                        "action": f"backup_host_{host}",
                    }
                )
            ok_hosts = len(hosts) - problem_hosts
            return True, (
                "💾 Бэкапы Proxmox\n\n"
                f"Всего хостов: {len(hosts)}\n"
                f"✅ Без проблем: {ok_hosts}\n"
                f"🚨 Проблемных: {problem_hosts}\n"
                f"⚪ Отключённых: {disabled_hosts}"
            ), "accepted", menu_options

        if action.startswith("backup_host_"):
            host_name = action.replace("backup_host_", "", 1).strip()
            if not host_name:
                return False, "Не указан хост Proxmox", "failed", None
            host_backups = backup_bot.get_host_status(host_name)
            if not host_backups:
                return True, f"🖥️ {host_name}\n\nДанные по хосту отсутствуют.", "accepted", None

            lines = [f"🖥️ {host_name}", "", "Последние 5 бэкапов:"]
            for row in host_backups:
                status = str(row[0]).lower() if len(row) > 0 else "unknown"
                duration = row[1] if len(row) > 1 else "-"
                total_size = row[2] if len(row) > 2 else "-"
                error_message = row[3] if len(row) > 3 else ""
                received_at = row[4] if len(row) > 4 else "-"
                icon = "✅" if status == "success" else "🚨"
                line = f"{icon} {received_at} • {status} • {duration}с • {total_size}"
                if error_message:
                    line += f"\n   ↳ {error_message}"
                lines.append(line)
            return True, "\n".join(lines), "accepted", None

        if action == "backup_databases":
            from extensions.backup_monitor.backup_handlers import get_database_monitor_snapshot

            snapshot = get_database_monitor_snapshot(backup_bot)
            if not snapshot:
                return True, "🗃️ Бэкапы БД\n\nДанные по базам пока отсутствуют.", "accepted", None

            db_status_rows = [
                (
                    str(item.get("backup_type", "")),
                    str(item.get("db_name", "")),
                    str(item.get("status", "unknown")),
                    bool(item.get("is_disabled", False)),
                    str(item.get("display_name") or item.get("db_name") or ""),
                )
                for item in snapshot
                if item.get("backup_type") and item.get("db_name")
            ]
            enabled_db_rows = [
                (backup_type, db_name, status)
                for backup_type, db_name, status, is_disabled, _display_name in db_status_rows
                if not is_disabled
            ]
            problem_db_rows = [
                (backup_type, db_name, status)
                for backup_type, db_name, status in enabled_db_rows
                if status != "success"
            ]
            problem_dbs = len(problem_db_rows)
            ok_dbs = len(enabled_db_rows) - problem_dbs
            menu_options = []
            for backup_type, db_name, status, is_disabled, display_name in db_status_rows:
                health_prefix = "🚨" if status != "success" else "✅"
                monitor_status = "⚪ мониторинг отключён" if is_disabled else "🟢 мониторинг включён"
                menu_options.append(
                    {
                        "label": f"{health_prefix} {display_name} ({backup_type}) • {monitor_status}",
                        "action": f"db_detail_{backup_type}__{db_name}",
                    }
                )
            problem_db_names = [f"{db_name} ({backup_type})" for backup_type, db_name, _ in problem_db_rows]
            preview_limit = 5
            if problem_db_names:
                preview_names = ", ".join(problem_db_names[:preview_limit])
                if len(problem_db_names) > preview_limit:
                    problem_db_line = f"Проблемные базы: {preview_names} (+{len(problem_db_names) - preview_limit} ещё)"
                else:
                    problem_db_line = f"Проблемные базы: {preview_names}"
            else:
                problem_db_line = "Проблемные базы: нет"
            return True, (
                "🗃️ Бэкапы БД\n\n"
                f"Баз в отчёте: {len(db_status_rows)}\n"
                f"🚫 Отключено: {sum(1 for _, _, _, is_disabled, _ in db_status_rows if is_disabled)}\n"
                f"✅ Без проблем: {ok_dbs}\n"
                f"🚨 Проблемных: {problem_dbs}\n"
                f"🔎 В мониторинге: {len(enabled_db_rows)}\n"
                f"{problem_db_line}"
            ), "accepted", menu_options

        if action.startswith("settings_db_toggle_monitor_"):
            raw = action.replace("settings_db_toggle_monitor_", "", 1)
            if "__" not in raw:
                return False, "Неверный формат toggle-действия для базы данных", "failed", None
            encoded_backup_type, encoded_db_name = raw.split("__", 1)
            backup_type = unquote(encoded_backup_type).strip()
            db_name = unquote(encoded_db_name).strip()
            if not backup_type or not db_name:
                return False, "Не указан тип или имя базы для переключения мониторинга", "failed", None

            from extensions.backup_monitor.backup_handlers import _toggle_database_monitoring

            now_enabled = _toggle_database_monitoring(backup_type, db_name)
            return True, (
                f"🗃️ {db_name} ({backup_type})\n\n"
                f"Мониторинг: {'включён' if now_enabled else 'отключён'}."
            ), "accepted", [
                {"label": "📋 Обновить список БД", "action": "backup_databases"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]

        if action.startswith("db_detail_"):
            payload = action.replace("db_detail_", "", 1)
            if "__" not in payload:
                return False, "Неверный формат действия базы данных", "failed", None
            backup_type, db_name = payload.split("__", 1)
            backup_type = backup_type.strip()
            db_name = db_name.strip()
            if not backup_type or not db_name:
                return False, "Не указан тип или имя базы", "failed", None

            details = backup_bot.get_database_details(backup_type, db_name)
            if not details:
                return True, f"🗃️ {db_name} ({backup_type})\n\nДанные по базе отсутствуют.", "accepted", None

            status = backup_bot.get_database_display_status(backup_type, db_name)
            status_icon = "✅" if status == "success" else "🚨"
            lines = [
                f"🗃️ {db_name} ({backup_type})",
                "",
                f"Текущий статус: {status_icon} {status}",
                "",
                "Последние 10 бэкапов:",
            ]
            for row in details:
                backup_status = str(row[0]).lower() if len(row) > 0 else "unknown"
                task_type = row[1] if len(row) > 1 else "-"
                error_count = row[2] if len(row) > 2 else 0
                received_at = row[4] if len(row) > 4 else "-"
                icon = "✅" if backup_status == "success" else "🚨"
                error_text = f" • errors: {error_count}" if error_count not in (None, "", 0, "0") else ""
                lines.append(f"{icon} {received_at} • {backup_status} • {task_type}{error_text}")

            return True, "\n".join(lines), "accepted", None

        if action == "backup_mail":
            mail_backups = backup_bot.get_mail_backups(hours=72, limit=20)
            if not mail_backups:
                return True, "📬 Бэкапы почты\n\nДанные по почтовым бэкапам пока отсутствуют.", "accepted", None
            problem_backups = sum(1 for row in mail_backups if str(row[0]).lower() != "success")
            ok_backups = len(mail_backups) - problem_backups
            lines = [
                "📬 Бэкапы почтового сервера (за 72ч)",
                "",
            ]
            for status, size, path, received_at in mail_backups:
                status_icon = "✅" if str(status).lower() == "success" else "🚨"
                time_ago = backup_bot.format_time_ago(received_at)
                size_text = str(size).strip() if str(size).strip() else "—"
                path_text = str(path).strip() if str(path).strip() else "—"
                lines.append(f"{status_icon} {size_text} — {path_text} ({time_ago})")

            lines.extend(
                [
                    "",
                    f"Итого записей: {len(mail_backups)}",
                    f"✅ Успешных: {ok_backups}",
                    f"🚨 С ошибками: {problem_backups}",
                ]
            )
            return True, "\n".join(lines), "accepted", None


        if action == "supplier_stock_reports" or action in {"supplier_stock_reports_download", "supplier_stock_reports_mail"}:
            source_kind = "mail" if action.endswith("_mail") else "download"
            reports = get_supplier_stock_reports(limit=None, period_days=1, source_kind=source_kind)
            title = "полученные скачиванием" if source_kind == "download" else "полученные по почте"
            lines = [
                "📦 Остатки поставщиков — результаты",
                "",
                f"Группа: {title}",
                "Период: последние 24 часа",
                "",
            ]
            grouped = summarize_supplier_stock_reports(period_days=1).get(source_kind, [])
            if not grouped:
                lines.append("⚪️ За сутки данных нет.")
                return True, "\n".join(lines), "accepted", [
                    {"label": "⬇️ Скачивание", "action": "supplier_stock_reports_download"},
                    {"label": "📧 Почта", "action": "supplier_stock_reports_mail"},
                ]

            lines.append("Кликни источник, чтобы открыть историю за сутки.")
            menu_options = [
                {"label": "⬇️ Скачивание", "action": "supplier_stock_reports_download"},
                {"label": "📧 Почта", "action": "supplier_stock_reports_mail"},
            ]
            for item in grouped:
                source_name = str(item.get("source_name") or item.get("source_id") or "неизвестный источник")
                recv = item.get("receive", {})
                proc = item.get("processing", {})
                tran = item.get("transfer", {})
                lines.extend([
                    "",
                    f"• {source_name}",
                    f"  📥 Загрузка: {recv.get('icon', '⚪️')} {recv.get('label', 'нет данных')}",
                    f"  🧩 Обработка: {proc.get('icon', '⚪️')} {proc.get('label', 'нет данных')}",
                    f"  📤 Выгрузка: {tran.get('icon', '⚪️')} {tran.get('label', 'нет данных')}",
                ])
                source_id = str(item.get("source_id") or "").strip()
                if source_id:
                    menu_options.append({
                        "label": f"📊 {source_name[:24]}",
                        "action": f"supplier_stock_report_source_day|{source_kind}|{source_id}",
                    })
            return True, "\n".join(lines), "accepted", menu_options

        if action.startswith("supplier_stock_report_source_day|"):
            parts = action.split("|", 2)
            if len(parts) != 3:
                return False, "Неверный формат действия истории источника", "failed", None
            source_kind = parts[1].strip() or "download"
            source_id = parts[2].strip()
            if not source_id:
                return False, "Не указан источник", "failed", None
            stats = build_supplier_stock_source_stats(source_id=source_id, source_kind=source_kind, period_days=1)
            summary = stats.get("summary") or {}
            entries = stats.get("entries") or []
            lines = [
                "📦 Остатки поставщиков — история источника",
                "",
                f"Источник: {source_id}",
                f"Группа: {'полученные скачиванием' if source_kind == 'download' else 'полученные по почте'}",
                "Период: последние 24 часа",
                "",
                f"Всего запусков: {summary.get('total', 0)}",
                f"📥 Успех/ошибка: {summary.get('receive_success', 0)}/{summary.get('receive_error', 0)}",
                f"🧩 Успех/ошибка: {summary.get('processing_success', 0)}/{summary.get('processing_error', 0)}",
                f"📤 Успех/ошибка: {summary.get('transfer_success', 0)}/{summary.get('transfer_error', 0)}",
            ]
            if entries:
                lines.extend(["", "Последние записи:"])
                for entry in entries[:10]:
                    receive = entry.get("receive") or {}
                    processing = entry.get("processing") or {}
                    transfer = entry.get("transfer") or {}
                    timestamp = str(entry.get("timestamp") or "—")
                    error = str(entry.get("error") or "").strip()
                    lines.append(
                        f"• {timestamp} | {receive.get('icon', '⚪️')} {receive.get('label', 'н/д')} | {processing.get('icon', '⚪️')} {processing.get('label', 'н/д')} | {transfer.get('icon', '⚪️')} {transfer.get('label', 'н/д')}"
                    )
                    if error:
                        lines.append(f"  ↳ {error}")
            return True, "\n".join(lines), "accepted", [
                {"label": "↩️ Назад", "action": f"supplier_stock_reports_{source_kind}"},
                {"label": "🔄 Обновить", "action": f"supplier_stock_report_source_day|{source_kind}|{source_id}"},
            ]

        if action == "backup_stock_loads":
            hours = 24
            stock_loads = backup_bot.get_stock_loads(hours=hours)
            if not stock_loads:
                return True, (
                    "📦 Загрузка остатков 1С\n\n"
                    f"❌ Нет данных за последние {hours} часов."
                ), "accepted", None

            grouped = {}
            for source_name, supplier, status, rows_count, error_sample, received_at in stock_loads:
                source_key = str(source_name).strip() or "Основное предприятие"
                grouped.setdefault(source_key, []).append(
                    (supplier, status, rows_count, error_sample, received_at)
                )

            total_suppliers = sum(len(items) for items in grouped.values())
            lines = [
                f"📦 Загрузка остатков 1С (за {hours}ч)",
                f"Всего поставщиков: {total_suppliers}",
                "",
            ]

            for source_name, items in grouped.items():
                lines.append(f"{source_name} ({len(items)})")
                for supplier, status, rows_count, error_sample, received_at in items:
                    normalized_status = str(status).lower()
                    status_icon = "✅" if normalized_status == "success" else "⚠️" if normalized_status == "warning" else "🚨"
                    supplier_text = str(supplier).strip() or "неизвестно"
                    rows_text = f"{rows_count} строк" if rows_count else "строки: —"
                    error_text = f" — {error_sample}" if error_sample else ""
                    time_ago = backup_bot.format_time_ago(received_at)
                    lines.append(f"{status_icon} {supplier_text} ({rows_text}){error_text} ({time_ago})")
                lines.append("")

            return True, "\n".join(lines).strip(), "accepted", None

        def _format_bytes_human(value: int) -> str:
            units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
            size = float(max(value, 0))
            idx = 0
            while size >= 1024 and idx < len(units) - 1:
                size /= 1024.0
                idx += 1
            return f"{size:.1f} {units[idx]}"

        def _resolve_backup_server_targets() -> list[tuple[str, str]]:
            proxmox_hosts = settings_manager.get_setting('PROXMOX_HOSTS', {})
            if not isinstance(proxmox_hosts, dict):
                proxmox_hosts = {}

            enabled_hosts: list[tuple[str, dict]] = []
            for host_name, host_value in proxmox_hosts.items():
                normalized_name = str(host_name).strip()
                if not normalized_name:
                    continue
                payload = host_value if isinstance(host_value, dict) else {}
                if payload.get("enabled", True):
                    enabled_hosts.append((normalized_name, payload))

            managed_servers = settings_manager.get_all_servers(include_disabled=True)
            by_name = {
                str(server.get("name", "")).strip().lower(): str(server.get("ip", "")).strip()
                for server in managed_servers
                if str(server.get("name", "")).strip() and str(server.get("ip", "")).strip()
            }

            targets: list[tuple[str, str]] = []
            for host_name, payload in enabled_hosts:
                address = (
                    str(payload.get("ip") or payload.get("host") or payload.get("address") or "")
                    .strip()
                )
                if not address:
                    address = by_name.get(host_name.lower(), "").strip()
                if not address:
                    address = host_name
                targets.append((host_name, address))
            return targets

        def _build_zfs_free_space_section() -> str:
            targets = _resolve_backup_server_targets()
            if not targets:
                return (
                    "💽 Свободное место ZFS (PBS)\n\n"
                    "⚠️ Нет включённых хостов в `PROXMOX_HOSTS`."
                )

            ssh_username = str(settings_manager.get_setting('SSH_USERNAME', 'root') or 'root').strip() or 'root'
            ssh_key_path = str(settings_manager.get_setting('SSH_KEY_PATH', '/root/.ssh/id_rsa') or '').strip()
            ssh_port = int(settings_manager.get_setting('SSH_PORT', 22) or 22)

            section_lines = ["💽 Свободное место ZFS (PBS)", ""]
            cmd_script = (
                "zpool list -Hp -o name,size,alloc,free,cap,health 2>/dev/null "
                "| awk -F '\\t' '$1==\"rpool\" || $1==\"zfs\" {print $0}'"
            )

            for host_name, address in targets:
                ssh_cmd = [
                    "ssh",
                    "-p",
                    str(ssh_port),
                    "-o",
                    "ConnectTimeout=8",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "StrictHostKeyChecking=no",
                ]
                if ssh_key_path:
                    ssh_cmd.extend(["-i", ssh_key_path])
                ssh_cmd.append(f"{ssh_username}@{address}")
                ssh_cmd.append(cmd_script)

                try:
                    result = subprocess.run(
                        ssh_cmd,
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                except Exception as exc:
                    section_lines.append(f"❌ {host_name} ({address}) — ошибка SSH: {exc}")
                    continue

                if result.returncode != 0:
                    error_text = (result.stderr or result.stdout or "unknown error").strip().splitlines()[0]
                    section_lines.append(f"❌ {host_name} ({address}) — {error_text}")
                    continue

                pool_rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                if not pool_rows:
                    section_lines.append(f"⚠️ {host_name} ({address}) — пулы rpool/zfs не найдены")
                    continue

                section_lines.append(f"🖥 {host_name} ({address})")
                for row in pool_rows:
                    parts = row.split('\t')
                    if len(parts) < 6:
                        continue
                    pool_name, total_raw, alloc_raw, free_raw, cap_raw, health_raw = parts[:6]
                    try:
                        total = int(float(total_raw))
                        free = int(float(free_raw))
                    except Exception:
                        total = 0
                        free = 0
                    section_lines.append(
                        f"• {pool_name}: {_format_bytes_human(free)} из {_format_bytes_human(total)} "
                        f"(занято {cap_raw}, {health_raw.upper()})"
                    )
                section_lines.append("")

            return "\n".join(section_lines).strip()

        if action == "zfs_free_space":
            return True, _build_zfs_free_space_section(), "accepted", None

        if action == "zfs_menu":
            from core.config_manager import config_manager as settings_manager
            from extensions.backup_monitor.db_settings_backup_monitor import BACKUP_DATABASE_CONFIG

            zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
            if not isinstance(zfs_servers, dict):
                zfs_servers = {}

            allowed_servers = {
                name
                for name, server_value in zfs_servers.items()
                if not isinstance(server_value, dict) or server_value.get('enabled', True)
            }

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                status_message = "🧊 ZFS статусы\n\n❌ База бэкапов не настроена."
                return True, f"{status_message}\n\n{_build_zfs_free_space_section()}", "accepted", None

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT s.server_name, s.pool_name, s.pool_state, s.received_at
                    FROM zfs_pool_status s
                    JOIN (
                        SELECT server_name, pool_name, MAX(received_at) AS last_seen
                        FROM zfs_pool_status
                        GROUP BY server_name, pool_name
                    ) latest
                    ON s.server_name = latest.server_name
                    AND s.pool_name = latest.pool_name
                    AND s.received_at = latest.last_seen
                    ORDER BY s.server_name, s.pool_name
                    """
                )
                rows = cursor.fetchall()
            except Exception as exc:
                if "no such table: zfs_pool_status" in str(exc):
                    status_message = (
                        "🧊 ZFS статусы\n\n"
                        "❌ Таблица ZFS ещё не создана.\n"
                        "Дождитесь первого письма или перезапустите мониторинг."
                    )
                    return True, f"{status_message}\n\n{_build_zfs_free_space_section()}", "accepted", None
                return False, f"Не удалось получить статусы ZFS: {exc}", "failed", None
            finally:
                conn.close()

            if allowed_servers:
                rows = [row for row in rows if row[0] in allowed_servers]
            else:
                rows = []

            if not rows:
                status_message = "📊 ZFS статусы\n\n❌ Данных нет."
                return True, f"{status_message}\n\n{_build_zfs_free_space_section()}", "accepted", None

            lines = ["📊 ZFS статусы (последние)", ""]
            current_server = None
            for server_name, pool_name, pool_state, received_at in rows:
                if server_name != current_server:
                    if current_server is not None:
                        lines.append("")
                    lines.append(str(server_name))
                    current_server = server_name
                lines.append(f"• {pool_name}: {pool_state} ({received_at})")

            status_message = "\n".join(lines)
            return True, f"{status_message}\n\n{_build_zfs_free_space_section()}", "accepted", None

        return True, "Команда принята", "accepted", None

    try:
        import core.monitor_core as monitor_core
    except Exception as e:
        return False, f"monitor core unavailable: {e}", "failed", None

    if action == "pause_monitoring":
        monitor_core.monitoring_active = False
        return True, "Мониторинг приостановлен", "applied", None

    if action == "resume_monitoring":
        monitor_core.monitoring_active = True
        return True, "Мониторинг возобновлен", "applied", None

    if action == "send_morning_report":
        from modules.morning_report import morning_report
        report_text = morning_report.force_report()
        return True, report_text, "accepted", None

    if action == "force_quiet":
        monitor_core.set_silent_override(True)
        return True, "Принудительно включен тихий режим", "applied", None

    if action == "force_loud":
        monitor_core.set_silent_override(False)
        return True, "Принудительно включен громкий режим", "applied", None

    if action == "auto_mode":
        monitor_core.set_silent_override(None)
        return True, "Включен автоматический режим quiet/loud", "applied", None

    return False, f"Unsupported action: {action}", "failed", None


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


def _resolve_server_for_targeted_check(server_id):
    """Ищет сервер по ip/имени/id из конфигурации."""
    server_id_normalized = str(server_id or '').strip().lower()
    if not server_id_normalized:
        return None

    servers = initialize_servers()
    for server in servers:
        candidates = {
            str(server.get('ip') or '').strip().lower(),
            str(server.get('name') or '').strip().lower(),
            str(server.get('id') or '').strip().lower(),
        }
        if server_id_normalized in candidates:
            return server
    return None


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


@app.route('/v1/monitoring/availability/<path:server_id>', methods=['GET'])
@app.route('/api/v1/monitoring/availability/<path:server_id>', methods=['GET'])
def mobile_availability_single(server_id):
    """Точечная проверка доступности одного сервера для Android-клиента."""
    started_at = time.time()
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        response = jsonify({
            "error": "unauthorized",
            "message": "Bearer token required",
            "reason": token_data,
            "request_id": request_id,
        })
        response.headers['X-Request-ID'] = request_id
        return response, 401

    server = _resolve_server_for_targeted_check(server_id)
    if not server:
        response = jsonify({
            "error": "server_not_found",
            "message": f'Сервер "{server_id}" не найден',
            "request_id": request_id,
        })
        response.headers['X-Request-ID'] = request_id
        return response, 404

    is_up = check_server_availability(server)
    status = 'up' if is_up else 'down'
    now_iso = datetime.now().isoformat()
    payload = {
        "request_id": request_id,
        "generated_at": now_iso,
        "server": {
            "server_id": server.get('ip') or server.get('name') or server_id,
            "name": server.get('name') or server_id,
            "ip": server.get('ip'),
            "status": status,
            "checked_at": now_iso,
        },
        "servers": [{
            "id": server.get('ip') or server_id,
            "name": server.get('name') or server_id,
            "status": status,
            "last_checked_at": now_iso,
        }],
        "items": [{
            "server_id": server.get('ip') or server_id,
            "status": status,
            "checked_at": now_iso,
        }],
        "summary": {
            "up": 1 if status == 'up' else 0,
            "down": 1 if status == 'down' else 0,
            "unknown": 0,
        },
    }
    duration_ms = int((time.time() - started_at) * 1000)
    app.logger.info(
        "GET /v1/monitoring/availability/<server_id> request_id=%s status=200 duration_ms=%s server=%s server_status=%s",
        request_id,
        duration_ms,
        server.get('ip') or server_id,
        status,
    )
    response = jsonify(payload)
    response.headers['X-Request-ID'] = request_id
    return response


@app.route('/v1/monitoring/resources/<path:server_id>', methods=['GET'])
@app.route('/api/v1/monitoring/resources/<path:server_id>', methods=['GET'])
def mobile_resources_single(server_id):
    """Точечная проверка ресурсов одного сервера для Android-клиента."""
    started_at = time.time()
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        response = jsonify({
            "error": "unauthorized",
            "message": "Bearer token required",
            "reason": token_data,
            "request_id": request_id,
        })
        response.headers['X-Request-ID'] = request_id
        return response, 401

    server = _resolve_server_for_targeted_check(server_id)
    if not server:
        response = jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Server '{server_id}' not found",
                "request_id": request_id,
            }
        })
        response.headers['X-Request-ID'] = request_id
        return response, 404

    if not extension_manager.is_extension_enabled('resource_monitor'):
        response = jsonify({
            "error": {
                "code": "RESOURCE_MONITOR_DISABLED",
                "message": "Resource monitor extension is disabled",
                "request_id": request_id,
            }
        })
        response.headers['X-Request-ID'] = request_id
        return response, 409

    from modules.targeted_checks import targeted_checks
    success, _, message = targeted_checks.check_single_server_resources(server_id)
    if not success:
        response = jsonify({
            "error": {
                "code": "RESOURCE_CHECK_FAILED",
                "message": message,
                "request_id": request_id,
            }
        })
        response.headers['X-Request-ID'] = request_id
        return response, 502

    resources = None
    try:
        from core.monitor_core import server_status
        resources = server_status.get(server['ip'], {}).get('resources')
    except Exception:
        resources = None

    payload = {
        "request_id": request_id,
        "server_id": server_id,
        "server_name": server.get('name'),
        "server_ip": server.get('ip'),
        "resources": resources,
        "message": message,
    }
    response = jsonify(payload)
    response.headers['X-Request-ID'] = request_id
    app.logger.info(
        "GET /v1/monitoring/resources/<server_id> request_id=%s status=200 duration_ms=%s server=%s",
        request_id,
        int((time.time() - started_at) * 1000),
        server.get('ip'),
    )
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




def _parse_semver(raw_value):
    value = str(raw_value or '').strip()
    parts = value.split('.')
    if len(parts) != 3:
        return None
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


@app.route('/v1/mobile/version', methods=['GET'])
@app.route('/api/v1/mobile/version', methods=['GET'])
def v1_mobile_version():
    """Возвращает требования к минимальной версии Android-клиента."""
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

    from config.settings import (
        ANDROID_MIN_SUPPORTED_VERSION,
        ANDROID_LATEST_VERSION,
        ANDROID_APK_DOWNLOAD_URL,
    )

    current_version = (request.args.get('current_version') or '').strip()
    current_semver = _parse_semver(current_version)
    min_semver = _parse_semver(ANDROID_MIN_SUPPORTED_VERSION)

    update_required = False
    if min_semver and current_semver:
        update_required = current_semver < min_semver
    elif current_version:
        update_required = True

    return jsonify({
        "request_id": request_id,
        "platform": "android",
        "min_supported_version": str(ANDROID_MIN_SUPPORTED_VERSION),
        "latest_version": str(ANDROID_LATEST_VERSION),
        "apk_download_url": str(ANDROID_APK_DOWNLOAD_URL),
        "current_version": current_version,
        "update_required": update_required,
    }), 200
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

    ok, message, result, menu_options = _execute_mobile_control_action(action)
    if ok:
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": result,
            "message": message,
            "menu_options": menu_options,
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


@app.route('/v1/settings/extensions', methods=['GET'])
def v1_get_settings_extensions():
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

    status_map = extension_manager.get_extensions_status()
    items = []
    enabled_count = 0

    for ext_id, status_info in status_map.items():
        enabled = bool(status_info.get('enabled'))
        if enabled:
            enabled_count += 1
        info = status_info.get('info') or {}
        items.append({
            "id": ext_id,
            "name": info.get('name', ext_id),
            "description": info.get('description', ''),
            "enabled": enabled,
        })

    return jsonify({
        "request_id": request_id,
        "items": items,
        "summary": {
            "total": len(items),
            "enabled": enabled_count,
            "disabled": len(items) - enabled_count,
        }
    }), 200


@app.route('/v1/settings/extensions/<extension_id>', methods=['PATCH'])
def v1_patch_settings_extension(extension_id):
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
    enabled = payload.get('enabled')
    if enabled is None:
        return jsonify({
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Field 'enabled' is required",
                "request_id": request_id,
            }
        }), 400

    if extension_id not in extension_manager.get_extensions_status():
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Extension '{extension_id}' not found",
                "request_id": request_id,
            }
        }), 404

    success, message = (
        extension_manager.enable_extension(extension_id)
        if bool(enabled)
        else extension_manager.disable_extension(extension_id)
    )

    if not success:
        return jsonify({
            "error": {
                "code": "UPDATE_FAILED",
                "message": message,
                "request_id": request_id,
            }
        }), 500

    return jsonify({
        "request_id": request_id,
        "extension_id": extension_id,
        "enabled": bool(enabled),
        "message": message,
    }), 200


@app.route('/v1/settings/extensions/actions', methods=['POST'])
def v1_extensions_actions():
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
    raw_action = str(payload.get('action') or '').strip()
    action = raw_action.lower()

    from core.config_manager import config_manager as settings_manager

    def _normalize_proxmox_hosts(raw_hosts) -> dict:
        if isinstance(raw_hosts, dict):
            return raw_hosts
        if isinstance(raw_hosts, str):
            try:
                parsed_hosts = json.loads(raw_hosts)
            except Exception:
                try:
                    parsed_hosts = ast.literal_eval(raw_hosts)
                except Exception:
                    parsed_hosts = {}
            return parsed_hosts if isinstance(parsed_hosts, dict) else {}
        return {}

    def _get_proxmox_hosts_for_mobile_settings() -> dict:
        proxmox_hosts = _normalize_proxmox_hosts(settings_manager.get_setting('PROXMOX_HOSTS', {}, use_cache=False))
        if proxmox_hosts:
            return proxmox_hosts

        try:
            from core.config_manager import config_manager
            fallback_db_hosts = _normalize_proxmox_hosts(config_manager.get_setting('PROXMOX_HOSTS', {}))
        except Exception:
            fallback_db_hosts = {}
        if fallback_db_hosts:
            return fallback_db_hosts

        try:
            from config.db_settings import PROXMOX_HOSTS as runtime_proxmox_hosts
        except Exception:
            runtime_proxmox_hosts = {}
        runtime_proxmox_hosts = _normalize_proxmox_hosts(runtime_proxmox_hosts)
        if runtime_proxmox_hosts:
            return runtime_proxmox_hosts

        try:
            from config.settings import PROXMOX_HOSTS as fallback_proxmox_hosts
        except Exception:
            fallback_proxmox_hosts = {}

        return _normalize_proxmox_hosts(fallback_proxmox_hosts)

    settings_menu_action_map = {
        "settings_ext_backup_db": {
            "message": "🗃️ Настройки расширения бэкапов БД открыты.",
            "menu_options": [
                {"label": "📋 Базы", "action": "settings_db_main"},
                {"label": "🔍 Паттерны", "action": "settings_patterns_db"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_ext_backup_mail": {
            "message": "📬 Настройки расширения бэкапов почты открыты.",
            "menu_options": [
                {"label": "🔍 Паттерны", "action": "settings_patterns_mail"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_ext_stock_load": {
            "message": "📦 Настройки расширения загрузки остатков 1С открыты.",
            "menu_options": [
                {"label": "🔍 Паттерны", "action": "settings_patterns_stock"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_ext_supplier_stock": {
            "message": "📦 Настройки расширения остатков поставщиков открыты.",
            "menu_options": [
                {"label": "🌐 Скачивание файлов", "action": "supplier_stock_download"},
                {"label": "📧 Почтовые сообщения", "action": "supplier_stock_mail"},
                {"label": "🗓 Период отчётов", "action": "supplier_stock_report_period"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_db_main": {
            "message": "🗃️ Настройки баз данных для бэкапов открыты.",
            "menu_options": [
                {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                {"label": "➕ Добавить категорию БД", "action": "settings_db_add_category"},
                {"label": "🗑️ Удалить категорию", "action": "settings_db_delete_category"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_db"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_patterns_db": {
            "message": "🔍 Паттерны бэкапов БД открыты.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_db"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_patterns_mail": {
            "message": "🔍 Паттерны бэкапов почты открыты.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_patterns_stock": {
            "message": "🔍 Паттерны загрузки остатков открыты.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_stock_load"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_zfs": {
            "message": "🧊 Настройки расширения ZFS открыты.",
            "menu_options": [
                {"label": "📋 Хосты", "action": "settings_zfs_list"},
                {"label": "🔍 Паттерны", "action": "settings_patterns_zfs"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_zfs_add": {
            "message": "➕ Добавление ZFS-сервера пока доступно в Telegram-боте.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_zfs_list"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_db_add_category": {
            "message": "➕ Добавление категории БД пока доступно в Telegram-боте.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_db_delete_category": {
            "message": "🗑️ Удаление категории БД пока доступно в Telegram-боте.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_db_view_all": {
            "message": "📋 Просмотр полного списка БД пока доступен в Telegram-боте.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
    }

    if action == 'enable_all':
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.enable_extension(ext_id)
            if success:
                changed += 1
        return jsonify({
            "request_id": request_id,
            "action": action,
            "message": f"✅ Включено {changed} расширений",
        }), 200

    if action == 'disable_all':
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.disable_extension(ext_id)
            if success:
                changed += 1
        return jsonify({
            "request_id": request_id,
            "action": action,
            "message": f"✅ Отключено {changed} расширений",
        }), 200

    if action == 'settings_ext_enable_all':
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.enable_extension(ext_id)
            if success:
                changed += 1
        return jsonify({
            "request_id": request_id,
            "action": action,
            "message": f"✅ Включено {changed} расширений",
        }), 200

    if action == 'settings_ext_disable_all':
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.disable_extension(ext_id)
            if success:
                changed += 1
        return jsonify({
            "request_id": request_id,
            "action": action,
            "message": f"✅ Отключено {changed} расширений",
        }), 200

    if action.startswith('settings_ext_toggle_'):
        extension_id = action.replace('settings_ext_toggle_', '', 1).strip()
        if not extension_id:
            return jsonify({
                "error": {
                    "code": "INVALID_ACTION",
                    "message": "Extension id is required for settings_ext_toggle_*",
                    "request_id": request_id,
                }
            }), 400

        status_map = extension_manager.get_extensions_status()
        if extension_id not in status_map:
            return jsonify({
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Extension '{extension_id}' not found",
                    "request_id": request_id,
                }
            }), 404

        enabled_now = bool((status_map.get(extension_id) or {}).get('enabled'))
        success, message = (
            extension_manager.disable_extension(extension_id)
            if enabled_now
            else extension_manager.enable_extension(extension_id)
        )
        if not success:
            return jsonify({
                "error": {
                    "code": "UPDATE_FAILED",
                    "message": message,
                    "request_id": request_id,
                }
            }), 500

        return jsonify({
            "request_id": request_id,
            "action": action,
            "message": message,
        }), 200

    if action == "settings_ext_backup_proxmox":
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
        proxmox_count = len(proxmox_hosts)
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": (
                "🖥️ Бэкапы Proxmox\n\n"
                f"Хостов в списке: {proxmox_count}\n\n"
                "Выберите раздел:"
            ),
            "menu_options": [
                {"label": "📋 Хосты", "action": "settings_backup_proxmox"},
                {"label": "🔍 Паттерны", "action": "settings_patterns_proxmox"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_backup_proxmox":
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": (
                "🖥️ Бэкапы Proxmox\n\n"
                f"Хостов в списке: {len(proxmox_hosts)}\n\n"
                "Выберите действие:"
            ),
            "menu_options": [
                {"label": "📋 Список хостов", "action": "settings_proxmox_list"},
                {"label": "➕ Добавить хост", "action": "settings_proxmox_add"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_proxmox_list":
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
        lines = ["📋 Хосты Proxmox", ""]
        if not proxmox_hosts:
            lines.append("❌ Хосты не настроены.")
        else:
            for host_name in sorted(proxmox_hosts.keys()):
                host_value = proxmox_hosts.get(host_name)
                enabled = True
                if isinstance(host_value, dict):
                    enabled = bool(host_value.get('enabled', True))
                lines.append(f"{'🟢' if enabled else '🔴'} {host_name}")
        menu_options = []
        for host_name in sorted(proxmox_hosts.keys()):
            host_value = proxmox_hosts.get(host_name)
            enabled = True
            if isinstance(host_value, dict):
                enabled = bool(host_value.get('enabled', True))
            toggle_label = "⛔️ Отключить" if enabled else "✅ Включить"
            menu_options.extend([
                {"label": f"✏️ {host_name}", "action": f"settings_proxmox_edit_{host_name}"},
                {"label": f"🗑️ {host_name}", "action": f"settings_proxmox_delete_{host_name}"},
                {"label": f"{toggle_label} {host_name}", "action": f"settings_proxmox_toggle_{host_name}"},
            ])
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_proxmox_toggle_"):
        host_name = raw_action[len("settings_proxmox_toggle_"):]
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()

        host_value = proxmox_hosts.get(host_name)
        if host_value is None:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": f"❌ Хост '{host_name}' не найден.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_proxmox_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        enabled = True
        if isinstance(host_value, dict):
            enabled = bool(host_value.get('enabled', True))
            host_value['enabled'] = not enabled
        else:
            proxmox_hosts[host_name] = {"pattern": str(host_value), "enabled": not enabled}

        settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)
        next_action = "settings_proxmox_list"
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"🔄 Хост '{host_name}': {'включён' if not enabled else 'отключён'}.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": next_action},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_proxmox_delete_"):
        host_name = raw_action[len("settings_proxmox_delete_"):]
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()

        if host_name not in proxmox_hosts:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": f"❌ Хост '{host_name}' не найден.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_proxmox_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        proxmox_hosts.pop(host_name, None)
        settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"✅ Хост '{host_name}' удалён.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_proxmox_list"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_proxmox_edit_"):
        host_name = raw_action[len("settings_proxmox_edit_"):]
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": (
                f"✏️ Редактирование хоста '{host_name}' пока выполняется в Telegram-боте.\n\n"
                "В Android/web сейчас доступны выключение и удаление."
            ),
            "menu_options": [
                {"label": "↩️ Назад", "action": "settings_proxmox_list"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_proxmox_add" or action.startswith("settings_proxmox_add|"):
        host_name = ""
        if "|" in raw_action:
            host_name = unquote(raw_action.split("|", 1)[1]).strip()

        if host_name:
            proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
            if host_name in proxmox_hosts:
                return jsonify({
                    "request_id": request_id,
                    "action": action,
                    "result": "rejected",
                    "message": f"❌ Хост '{host_name}' уже добавлен.",
                    "menu_options": [
                        {"label": "📋 Список хостов", "action": "settings_proxmox_list"},
                        {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }), 200

            proxmox_hosts[host_name] = {"enabled": True}
            settings_manager.set_setting('PROXMOX_HOSTS', proxmox_hosts)
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": f"✅ Хост '{host_name}' добавлен.",
                "menu_options": [
                    {"label": "📋 Список хостов", "action": "settings_proxmox_list"},
                    {"label": "🏠 На главную", "action": "main_menu"},
                    {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": (
                "➕ Добавление Proxmox хоста\n\n"
                "Добавление/редактирование хостов пока выполняется в Telegram-боте."
            ),
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_patterns_proxmox":
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, category, enabled
            FROM backup_patterns
            WHERE category = 'proxmox'
               OR (category = 'database' AND pattern_type LIKE 'proxmox%')
            ORDER BY enabled DESC, category, pattern_type, id
            """
        )
        rows = cursor.fetchall()
        conn.close()

        lines = ["🔍 Паттерны Proxmox", ""]
        if not rows:
            lines.append("❌ Паттерны не настроены.")
        else:
            for index, (pattern_id, pattern_type, pattern_value, category, enabled) in enumerate(rows, start=1):
                display_category = category
                display_type = pattern_type
                if category == "database" and isinstance(pattern_type, str) and pattern_type.startswith("proxmox"):
                    display_category = "proxmox"
                    suffix = pattern_type[len("proxmox"):].strip("_:- ")
                    display_type = suffix or "subject"
                marker = "🟢" if bool(enabled) else "🔴"
                lines.append(f"{index}. {marker} [{display_category}/{display_type}] {pattern_value}")

        menu_options = []
        for index, (pattern_id, pattern_type, pattern_value, category, enabled) in enumerate(rows, start=1):
            display_category = category
            display_type = pattern_type
            if category == "database" and isinstance(pattern_type, str) and pattern_type.startswith("proxmox"):
                display_category = "proxmox"
                suffix = pattern_type[len("proxmox"):].strip("_:- ")
                display_type = suffix or "subject"
            toggle_label = "⛔️ Отключить" if bool(enabled) else "✅ Включить"
            menu_options.extend([
                {"label": f"✏️ {index}. {display_category}:{display_type} — {pattern_value}", "action": f"settings_proxmox_pattern_edit_{pattern_id}"},
                {"label": f"🗑️ {index}. {display_category}:{display_type}", "action": f"settings_proxmox_pattern_delete_{pattern_id}"},
                {"label": f"{toggle_label} {index}. {display_category}:{display_type}", "action": f"settings_proxmox_pattern_toggle_{pattern_id}"},
            ])

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {"label": "➕ Добавить паттерн", "action": "settings_proxmox_pattern_add"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_patterns_mail":
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, enabled
            FROM backup_patterns
            WHERE category = 'mail'
            ORDER BY enabled DESC, id
            """
        )
        rows = cursor.fetchall()
        conn.close()

        lines = ["🔍 Паттерны бэкапов почты", ""]
        if not rows:
            lines.append("❌ Паттерны не настроены.")
        else:
            for index, (_, pattern_type, pattern_value, enabled) in enumerate(rows, start=1):
                marker = "🟢" if bool(enabled) else "🔴"
                lines.append(f"{index}. {marker} [{pattern_type}] {pattern_value}")

        menu_options = []
        for index, (pattern_id, pattern_type, _, enabled) in enumerate(rows, start=1):
            toggle_label = "⛔️ Отключить" if bool(enabled) else "✅ Включить"
            menu_options.extend([
                {"label": f"✏️ {index}. mail:{pattern_type}", "action": f"settings_mail_pattern_edit_{pattern_id}"},
                {"label": f"🗑️ {index}. mail:{pattern_type}", "action": f"settings_mail_pattern_delete_{pattern_id}"},
                {"label": f"{toggle_label} {index}. mail:{pattern_type}", "action": f"settings_mail_pattern_toggle_{pattern_id}"},
            ])

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {"label": "➕ Добавить паттерн", "action": "settings_mail_pattern_add"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_mail_pattern_toggle_"):
        pattern_id_raw = raw_action[len("settings_mail_pattern_toggle_"):].strip()
        if not pattern_id_raw.isdigit():
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Некорректный идентификатор паттерна.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT enabled FROM backup_patterns WHERE id = ? AND category = 'mail'",
            (pattern_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Паттерн не найден.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        next_enabled = 0 if bool(row[0]) else 1
        cursor.execute("UPDATE backup_patterns SET enabled = ? WHERE id = ?", (next_enabled, pattern_id))
        conn.commit()
        conn.close()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"🔄 Паттерн {'включён' if next_enabled else 'отключён'}.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_mail_pattern_delete_"):
        pattern_id_raw = raw_action[len("settings_mail_pattern_delete_"):].strip()
        if not pattern_id_raw.isdigit():
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Некорректный идентификатор паттерна.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE backup_patterns SET enabled = 0 WHERE id = ? AND category = 'mail'",
            (pattern_id,)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted" if deleted else "rejected",
            "message": "✅ Паттерн удалён." if deleted else "❌ Паттерн не найден.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_mail_pattern_add") or action.startswith("settings_mail_pattern_edit_"):
        def _decode_action_part(value: str) -> str:
            return unquote(str(value or "")).strip()

        def _build_mail_pattern_from_subject(subject: str) -> str:
            if not subject:
                return ""
            normalized = subject.strip()
            if not normalized:
                return ""

            size_regex = r"\b\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?\b"
            path_regex = r"/\S+"
            date_iso_regex = r"\b\d{4}[-/.]\d{2}[-/.]\d{2}\b"
            date_ru_regex = r"\b\d{2}[-/.]\d{2}[-/.]\d{4}\b"
            time_regex = r"\b\d{2}:\d{2}(?::\d{2})?\b"

            draft = re.sub(size_regex, "__SIZE__", normalized, flags=re.IGNORECASE)
            draft = re.sub(path_regex, "__PATH__", draft)
            draft = re.sub(date_iso_regex, "__DATE__", draft)
            draft = re.sub(date_ru_regex, "__DATE__", draft)
            draft = re.sub(time_regex, "__TIME__", draft)

            escaped = re.escape(draft)
            escaped = re.sub(r"\\\s+", r"\\s+", escaped)

            replacements = {
                "__SIZE__": r"(?P<size>\d+(?:[.,]\d+)?\s*[TGMK]?(?:i?B)?)",
                "__PATH__": r"(?P<path>/\S+)",
                "__DATE__": r"\d{2,4}[-/.]\d{2}[-/.]\d{2,4}",
                "__TIME__": r"\d{2}:\d{2}(?::\d{2})?",
            }
            for placeholder, pattern in replacements.items():
                escaped = escaped.replace(re.escape(placeholder), pattern)
            return escaped

        def _build_mail_pattern_from_fragments(raw_fragments: str) -> str:
            fragments = [item.strip() for item in re.split(r"[;,]", raw_fragments or "") if item.strip()]
            if not fragments:
                return ""
            escaped_parts = [re.escape(fragment) for fragment in fragments]
            return r".*".join(escaped_parts)

        action_parts = raw_action.split("|")

        if action == "settings_mail_pattern_add":
            if len(action_parts) < 3:
                return jsonify({
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": (
                        "➕ Добавление паттерна почты\n\n"
                        "Android/web: выберите режим (тема или фрагменты), введите значение и сохраните."
                    ),
                    "menu_options": [
                        {"label": "➕ По теме письма", "action": "settings_mail_pattern_add|subject|"},
                        {"label": "➕ По фрагментам", "action": "settings_mail_pattern_add|fragments|"},
                        {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }), 200

            build_mode = _decode_action_part(action_parts[1]).lower() or "subject"
            raw_value = _decode_action_part("|".join(action_parts[2:]))
            pattern_value = (
                _build_mail_pattern_from_fragments(raw_value)
                if build_mode == "fragments"
                else _build_mail_pattern_from_subject(raw_value)
            )
            source_label = "фрагменты" if build_mode == "fragments" else "тема"

            if not pattern_value:
                return jsonify({
                    "request_id": request_id,
                    "action": action,
                    "result": "rejected",
                    "message": "❌ Не удалось собрать паттерн. Проверьте ввод.",
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }), 200

            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                ("subject", pattern_value, "mail")
            )
            conn.commit()
            conn.close()
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": f"✅ Паттерн добавлен (источник: {source_label}).",
                "menu_options": [
                    {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id_raw = raw_action[len("settings_mail_pattern_edit_"):].split("|", 1)[0].strip()
        if not pattern_id_raw.isdigit():
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Некорректный идентификатор паттерна.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        if len(action_parts) < 2:
            pattern_id = int(pattern_id_raw)
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pattern FROM backup_patterns WHERE id = ? AND category = 'mail'",
                (pattern_id,)
            )
            row = cursor.fetchone()
            conn.close()
            current_pattern = row[0] if row and len(row) > 0 else ""
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted" if current_pattern else "rejected",
                "message": (
                    "✏️ Редактирование паттерна почты\n\n"
                    f"Текущий паттерн: `{current_pattern}`\n\n"
                    "Нажмите кнопку ниже, чтобы открыть ввод нового значения."
                ) if current_pattern else "❌ Паттерн не найден.",
                "menu_options": ([
                    {"label": "✏️ Ввести новый паттерн", "action": f"settings_mail_pattern_edit_{pattern_id}"},
                ] if current_pattern else []) + [
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        new_pattern = _decode_action_part("|".join(action_parts[1:]))
        if not new_pattern:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Паттерн не может быть пустым.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE backup_patterns SET pattern = ? WHERE id = ? AND category = 'mail'",
            (new_pattern, pattern_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted" if updated else "rejected",
            "message": "✅ Паттерн обновлён." if updated else "❌ Паттерн не найден.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_proxmox_pattern_toggle_"):
        pattern_id_raw = raw_action[len("settings_proxmox_pattern_toggle_"):].strip()
        if not pattern_id_raw.isdigit():
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Некорректный идентификатор паттерна.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT enabled
            FROM backup_patterns
            WHERE id = ?
              AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
            """,
            (pattern_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Паттерн не найден.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        next_enabled = 0 if bool(row[0]) else 1
        cursor.execute(
            "UPDATE backup_patterns SET enabled = ? WHERE id = ?",
            (next_enabled, pattern_id)
        )
        conn.commit()
        conn.close()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"🔄 Паттерн {'включён' if next_enabled else 'отключён'}.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_patterns_proxmox"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_proxmox_pattern_delete_"):
        pattern_id_raw = raw_action[len("settings_proxmox_pattern_delete_"):].strip()
        if not pattern_id_raw.isdigit():
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Некорректный идентификатор паттерна.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE backup_patterns
            SET enabled = 0
            WHERE id = ?
              AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
            """,
            (pattern_id,)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted" if deleted else "rejected",
            "message": "✅ Паттерн удалён." if deleted else "❌ Паттерн не найден.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_patterns_proxmox"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_proxmox_pattern_add") or action.startswith("settings_proxmox_pattern_edit_"):
        def _decode_action_part(value: str) -> str:
            return unquote(str(value or "")).strip()

        def _proxmox_type_to_db_type(pattern_type_value: str, category_value: str) -> str:
            normalized_type = (pattern_type_value or "subject").strip().lower() or "subject"
            normalized_category = (category_value or "proxmox").strip().lower() or "proxmox"
            if normalized_category == "database":
                if normalized_type.startswith("proxmox"):
                    return normalized_type
                return f"proxmox_{normalized_type}"
            return normalized_type

        action_parts = raw_action.split("|")

        if action.startswith("settings_proxmox_pattern_add"):
            if len(action_parts) < 4:
                return jsonify({
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": (
                        "➕ Добавление паттерна Proxmox\n\n"
                        "Android/web: откройте форму, заполните категорию/тип/паттерн и отправьте."
                    ),
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }), 200

            category = _decode_action_part(action_parts[1]).lower() or "proxmox"
            pattern_type = _decode_action_part(action_parts[2]).lower() or "subject"
            pattern_value = _decode_action_part("|".join(action_parts[3:]))

            if category not in {"proxmox", "database"}:
                return jsonify({
                    "request_id": request_id,
                    "action": action,
                    "result": "rejected",
                    "message": "❌ Категория должна быть proxmox или database.",
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }), 200

            if not pattern_value:
                return jsonify({
                    "request_id": request_id,
                    "action": action,
                    "result": "rejected",
                    "message": "❌ Паттерн не может быть пустым.",
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }), 200

            db_pattern_type = _proxmox_type_to_db_type(pattern_type, category)
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (db_pattern_type, pattern_value, category)
            )
            conn.commit()
            conn.close()
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": "✅ Паттерн Proxmox добавлен.",
                "menu_options": [
                    {"label": "📋 Обновить список", "action": "settings_patterns_proxmox"},
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id_raw = raw_action[len("settings_proxmox_pattern_edit_"):].split("|", 1)[0].strip()
        if not pattern_id_raw.isdigit():
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Некорректный идентификатор паттерна.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        if len(action_parts) < 2:
            pattern_id = int(pattern_id_raw)
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT pattern_type, pattern
                FROM backup_patterns
                WHERE id = ?
                  AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
                """,
                (pattern_id,)
            )
            row = cursor.fetchone()
            conn.close()
            current_pattern_type = row[0] if row and len(row) > 0 else ""
            current_pattern = row[1] if row and len(row) > 1 else ""
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted" if current_pattern else "rejected",
                "message": (
                    "✏️ Редактирование паттерна Proxmox\n\n"
                    f"Текущий тип: `{current_pattern_type}`\n"
                    f"Текущий паттерн: `{current_pattern}`\n\n"
                    "Нажмите кнопку ниже, чтобы открыть ввод нового типа и паттерна.\n"
                    "Если клиент не поддерживает окно ввода, отправьте действие в формате:\n"
                    "`settings_proxmox_pattern_edit_<id>|<новый_тип>|<новый_паттерн>`"
                ) if current_pattern else (
                    "❌ Паттерн не найден."
                ),
                "menu_options": ([
                    {"label": "✏️ Ввести новый паттерн", "action": f"settings_proxmox_pattern_edit_{pattern_id}"},
                ] if current_pattern else []) + [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        if len(action_parts) >= 3:
            new_pattern_type = _decode_action_part(action_parts[1]).lower() or "subject"
            new_pattern = _decode_action_part("|".join(action_parts[2:]))
        else:
            new_pattern_type = ""
            new_pattern = _decode_action_part("|".join(action_parts[1:]))
        if not new_pattern:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Паттерн не может быть пустым.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        if len(action_parts) >= 3 and not new_pattern_type:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Тип паттерна не может быть пустым.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        if len(action_parts) >= 3:
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern_type = ?, pattern = ?
                WHERE id = ?
                  AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
                """,
                (new_pattern_type, new_pattern, pattern_id)
            )
        else:
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern = ?
                WHERE id = ?
                  AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
                """,
                (new_pattern, pattern_id)
            )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted" if updated else "rejected",
            "message": "✅ Паттерн обновлён." if updated else "❌ Паттерн не найден.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_patterns_proxmox"},
                {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_db_view_all":
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}

        lines = ["📋 Все базы данных", ""]
        total_dbs = 0
        if not db_config:
            lines.append("❌ Нет настроенных баз данных.")
        else:
            for category in sorted(db_config.keys()):
                databases = db_config.get(category)
                if not isinstance(databases, dict):
                    databases = {}
                lines.append(f"📁 {str(category).upper()} ({len(databases)} БД):")
                for db_key in sorted(databases.keys()):
                    db_name = str(databases.get(db_key) or db_key)
                    lines.append(f"• {db_name}")
                    total_dbs += 1
                lines.append("")
            lines.append(f"Итого: {total_dbs} баз данных в {len(db_config)} категориях")

        menu_options = []
        for category in sorted(db_config.keys()):
            databases = db_config.get(category)
            if not isinstance(databases, dict):
                databases = {}
            encoded_category = quote(str(category), safe="")
            menu_options.append({
                "label": f"➕ Добавить БД в {str(category).upper()}",
                "action": f"settings_db_add_db_{encoded_category}",
            })
            for db_key in sorted(databases.keys()):
                encoded_db_key = quote(str(db_key), safe="")
                menu_options.extend([
                    {
                        "label": f"✏️ {str(category).upper()}: {str(db_key)}",
                        "action": f"settings_db_edit_db_{encoded_category}__{encoded_db_key}",
                    },
                    {
                        "label": f"🗑️ {str(category).upper()}: {str(db_key)}",
                        "action": f"settings_db_delete_db_{encoded_category}__{encoded_db_key}",
                    },
                ])
            menu_options.append({
                "label": f"🗑️ Удалить категорию {str(category).upper()}",
                "action": f"settings_db_delete_{encoded_category}",
            })

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_db_add_category|"):
        payload = action.split("|", 1)[1].strip()
        category = unquote(payload).strip().lower()
        if not category:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Категория не указана.",
                "menu_options": [{"label": "↩️ Назад", "action": "settings_db_main"}],
            }), 200

        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}
        if category in db_config:
            message = f"ℹ️ Категория «{category}» уже существует."
        else:
            db_config[category] = {}
            settings_manager.set_setting('DATABASE_CONFIG', db_config, 'backup', data_type='auto')
            message = f"✅ Категория «{category}» добавлена."
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": message,
            "menu_options": [
                {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_db_delete_category":
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}
        categories = sorted([str(item) for item in db_config.keys()])
        menu_options = [
            {
                "label": f"🗑️ {category.upper()}",
                "action": f"settings_db_delete_{quote(category, safe='')}",
            }
            for category in categories
        ]
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "Выбери категорию БД для удаления." if categories else "❌ Категории БД не найдены.",
            "menu_options": menu_options + [
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_db_add_db_submit|"):
        parts = action.split("|")
        category = unquote(parts[1]).strip().lower() if len(parts) > 1 else ""
        db_key = unquote(parts[2]).strip() if len(parts) > 2 else ""
        db_name = unquote(parts[3]).strip() if len(parts) > 3 else ""
        if not category or not db_key:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Укажи категорию и ключ БД.",
                "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
            }), 200
        if not db_name:
            db_name = db_key

        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}
        if category not in db_config or not isinstance(db_config.get(category), dict):
            db_config[category] = {}
        db_config[category][db_key] = db_name
        settings_manager.set_setting('DATABASE_CONFIG', db_config, 'backup', data_type='auto')
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"✅ БД «{db_key}» сохранена в категории «{category}».",
            "menu_options": [
                {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_db_edit_db_submit|"):
        parts = action.split("|")
        category = unquote(parts[1]).strip().lower() if len(parts) > 1 else ""
        old_key = unquote(parts[2]).strip() if len(parts) > 2 else ""
        new_key = unquote(parts[3]).strip() if len(parts) > 3 else ""
        new_name = unquote(parts[4]).strip() if len(parts) > 4 else ""
        if not category or not old_key or not new_key:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Недостаточно данных для редактирования БД.",
                "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
            }), 200

        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}
        category_map = db_config.get(category) if isinstance(db_config.get(category), dict) else {}
        if old_key not in category_map:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ База не найдена в указанной категории.",
                "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
            }), 200
        value = new_name or category_map.get(old_key) or new_key
        if old_key != new_key:
            category_map.pop(old_key, None)
        category_map[new_key] = value
        db_config[category] = category_map
        settings_manager.set_setting('DATABASE_CONFIG', db_config, 'backup', data_type='auto')
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"✅ БД «{old_key}» обновлена.",
            "menu_options": [
                {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_db_delete_db_"):
        raw = action.replace("settings_db_delete_db_", "", 1)
        parts = raw.split("__", 1)
        category = unquote(parts[0]).strip().lower() if parts else ""
        db_key = unquote(parts[1]).strip() if len(parts) > 1 else ""
        if not category or not db_key:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Не удалось определить категорию/БД для удаления.",
                "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
            }), 200
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}
        category_map = db_config.get(category) if isinstance(db_config.get(category), dict) else {}
        removed = category_map.pop(db_key, None)
        db_config[category] = category_map
        settings_manager.set_setting('DATABASE_CONFIG', db_config, 'backup', data_type='auto')
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"{'✅' if removed is not None else 'ℹ️'} БД «{db_key}» {'удалена' if removed is not None else 'не найдена'}.",
            "menu_options": [
                {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_db_delete_") and action != "settings_db_delete_category":
        encoded_category = action.replace("settings_db_delete_", "", 1)
        category = unquote(encoded_category).strip().lower()
        if not category:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "rejected",
                "message": "❌ Категория для удаления не указана.",
                "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
            }), 200
        db_config = settings_manager.get_setting('DATABASE_CONFIG', {})
        if not isinstance(db_config, dict):
            db_config = {}
        removed = db_config.pop(category, None)
        settings_manager.set_setting('DATABASE_CONFIG', db_config, 'backup', data_type='auto')
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"{'✅' if removed is not None else 'ℹ️'} Категория «{category}» {'удалена' if removed is not None else 'не найдена'}.",
            "menu_options": [
                {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_patterns_db":
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, enabled
            FROM backup_patterns
            WHERE category = 'database'
              AND pattern_type NOT LIKE 'proxmox%'
            ORDER BY enabled DESC, pattern_type, id
            """
        )
        rows = cursor.fetchall()
        conn.close()

        lines = ["🔍 Паттерны бэкапов БД", ""]
        if not rows:
            lines.append("❌ Паттерны бэкапов БД не настроены.")
        else:
            for index, (_, pattern_type, pattern_value, enabled) in enumerate(rows, start=1):
                marker = "🟢" if bool(enabled) else "🔴"
                lines.append(f"{index}. {marker} [{pattern_type}] {pattern_value}")

        menu_options = []
        for index, (pattern_id, pattern_type, pattern_value, enabled) in enumerate(rows, start=1):
            toggle_label = "⛔️ Отключить" if bool(enabled) else "✅ Включить"
            menu_options.extend([
                {"label": f"✏️ {index}. {pattern_type} — {pattern_value}", "action": f"settings_proxmox_pattern_edit_{pattern_id}"},
                {"label": f"🗑️ {index}. {pattern_type}", "action": f"settings_proxmox_pattern_delete_{pattern_id}"},
                {"label": f"{toggle_label} {index}. {pattern_type}", "action": f"settings_proxmox_pattern_toggle_{pattern_id}"},
            ])

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {
                    "label": "➕ Добавить паттерн БД",
                    "action": "settings_proxmox_pattern_add|database|subject|",
                },
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_ext_backup_db"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_patterns_zfs":
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, pattern_type, pattern, enabled
            FROM backup_patterns
            WHERE category = 'zfs'
            ORDER BY enabled DESC, id
            """
        )
        rows = cursor.fetchall()
        conn.close()

        lines = ["🔍 Паттерны ZFS", ""]
        if not rows:
            lines.append("❌ Паттерны ZFS не настроены.")
        else:
            for index, (_, pattern_type, pattern_value, enabled) in enumerate(rows, start=1):
                marker = "🟢" if bool(enabled) else "🔴"
                lines.append(f"{index}. {marker} [{pattern_type}] {pattern_value}")

        menu_options = []
        for index, (pattern_id, pattern_type, pattern_value, enabled) in enumerate(rows, start=1):
            toggle_label = "⛔️ Отключить" if bool(enabled) else "✅ Включить"
            menu_options.extend([
                {"label": f"✏️ {index}. {pattern_type} — {pattern_value}", "action": f"settings_proxmox_pattern_edit_{pattern_id}"},
                {"label": f"🗑️ {index}. {pattern_type}", "action": f"settings_proxmox_pattern_delete_{pattern_id}"},
                {"label": f"{toggle_label} {index}. {pattern_type}", "action": f"settings_proxmox_pattern_toggle_{pattern_id}"},
            ])

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {
                    "label": "➕ Добавить паттерн ZFS",
                    "action": "settings_proxmox_pattern_add|zfs|subject|",
                },
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_zfs"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_zfs_list":
        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        zfs_servers = zfs_servers if isinstance(zfs_servers, dict) else {}

        lines = ["📋 ZFS серверы", ""]
        if not zfs_servers:
            lines.append("❌ Серверы не настроены.")
        else:
            for server_name in sorted(zfs_servers.keys()):
                server_value = zfs_servers.get(server_name)
                enabled = True
                if isinstance(server_value, dict):
                    enabled = bool(server_value.get('enabled', True))
                lines.append(f"{'🟢' if enabled else '🔴'} {server_name}")

        menu_options = []
        for server_name in sorted(zfs_servers.keys()):
            encoded_server_name = quote(str(server_name), safe="")
            server_value = zfs_servers.get(server_name)
            enabled = True
            if isinstance(server_value, dict):
                enabled = bool(server_value.get('enabled', True))
            toggle_label = "⛔️ Отключить" if enabled else "✅ Включить"
            menu_options.extend([
                {"label": f"✏️ {server_name}", "action": f"settings_zfs_edit_name_{encoded_server_name}"},
                {"label": f"🗑️ {server_name}", "action": f"settings_zfs_delete_{encoded_server_name}"},
                {"label": f"{toggle_label} {server_name}", "action": f"settings_zfs_toggle_{encoded_server_name}"},
            ])

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "\n".join(lines),
            "menu_options": menu_options + [
                {"label": "➕ Добавить сервер", "action": "settings_zfs_add"},
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_zfs"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "settings_zfs_add" or action.startswith("settings_zfs_add|"):
        payload = raw_action.split("|", 1)
        server_name = unquote(payload[1]).strip() if len(payload) > 1 else ""
        if not server_name:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": (
                    "➕ Добавление ZFS-сервера\n\n"
                    "Отправьте действие в формате:\n"
                    "`settings_zfs_add|<имя_сервера>`"
                ),
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_zfs_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        if server_name in zfs_servers:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": f"❌ ZFS-сервер «{server_name}» уже существует.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_zfs_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        zfs_servers[server_name] = {"enabled": True}
        settings_manager.set_setting('ZFS_SERVERS', zfs_servers, 'zfs')
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"✅ ZFS-сервер «{server_name}» добавлен.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_zfs_list"},
                {"label": "↩️ Назад", "action": "settings_zfs"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "supplier_stock_download":
        supplier_config = extension_manager.load_extension_config('supplier_stock_files')
        download_settings = supplier_config.get('download', {}) if isinstance(supplier_config, dict) else {}
        sources = download_settings.get('sources', []) if isinstance(download_settings, dict) else []
        source_count = len(sources) if isinstance(sources, list) else 0
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": (
                "🌐 Скачивание файлов остатков поставщиков\n\n"
                f"Источников: {source_count}\n\n"
                "Выберите раздел:"
            ),
            "menu_options": [
                {"label": "⏱ Расписание", "action": "supplier_stock_schedule"},
                {"label": "🖥 Ресурсы", "action": "supplier_stock_resources"},
                {"label": "🗄 FTP", "action": "supplier_stock_ftp"},
                {"label": "⚙️ Обработка", "action": "supplier_stock_processing"},
                {"label": "↩️ Назад", "action": "settings_ext_supplier_stock"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == "supplier_stock_mail":
        supplier_config = extension_manager.load_extension_config('supplier_stock_files')
        mail_settings = supplier_config.get('mail', {}) if isinstance(supplier_config, dict) else {}
        sources = mail_settings.get('sources', []) if isinstance(mail_settings, dict) else []
        source_count = len(sources) if isinstance(sources, list) else 0
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": (
                "📧 Почтовые сообщения (остатки поставщиков)\n\n"
                f"Источников: {source_count}\n\n"
                "Выберите раздел:"
            ),
            "menu_options": [
                {"label": "📨 Источники почты", "action": "supplier_stock_mail_sources"},
                {"label": "🗓 Отчёты (download)", "action": "supplier_stock_reports_download"},
                {"label": "🗓 Отчёты (mail)", "action": "supplier_stock_reports_mail"},
                {"label": "↩️ Назад", "action": "settings_ext_supplier_stock"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action in {
        "supplier_stock_report_period",
        "supplier_stock_schedule",
        "supplier_stock_resources",
        "supplier_stock_ftp",
        "supplier_stock_processing",
        "supplier_stock_mail_sources",
        "supplier_stock_reports_download",
        "supplier_stock_reports_mail",
    }:
        title_map = {
            "supplier_stock_report_period": "🗓 Период отчётов",
            "supplier_stock_schedule": "⏱ Расписание",
            "supplier_stock_resources": "🖥 Ресурсы",
            "supplier_stock_ftp": "🗄 FTP",
            "supplier_stock_processing": "⚙️ Обработка",
            "supplier_stock_mail_sources": "📨 Источники почты",
            "supplier_stock_reports_download": "🗓 Отчёты (download)",
            "supplier_stock_reports_mail": "🗓 Отчёты (mail)",
        }
        back_action = "supplier_stock_mail" if action.startswith("supplier_stock_mail_") or action.startswith("supplier_stock_reports_") else "supplier_stock_download"
        if action == "supplier_stock_report_period":
            back_action = "settings_ext_supplier_stock"
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"{title_map.get(action, 'Раздел')}\n\nДетальная настройка пока доступна в Telegram-боте.",
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": back_action},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    mapped_action = settings_menu_action_map.get(action)
    if mapped_action:
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": mapped_action.get("message"),
            "menu_options": mapped_action.get("menu_options", []),
        }), 200

    if action.startswith("settings_zfs_toggle_"):
        server_name = unquote(raw_action[len("settings_zfs_toggle_"):]).strip()
        if not server_name:
            return jsonify({
                "error": {
                    "code": "INVALID_ACTION",
                    "message": "Server name is required for settings_zfs_toggle_*",
                    "request_id": request_id,
                }
            }), 400

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        for key, value in zfs_servers.items():
            if key != server_name:
                continue
            if isinstance(value, dict):
                value['enabled'] = not bool(value.get('enabled', True))
            else:
                zfs_servers[key] = {'host': str(value), 'enabled': False}
            settings_manager.set_setting('ZFS_SERVERS', zfs_servers, 'zfs')
            break

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "🔄 Статус ZFS-сервера обновлён.",
            "menu_options": [
                {"label": "↩️ Назад", "action": "settings_zfs_list"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_zfs_edit_name_"):
        payload = raw_action[len("settings_zfs_edit_name_"):]
        parts = payload.split("|", 1)
        current_name = unquote(parts[0]).strip() if parts else ""
        new_name = unquote(parts[1]).strip() if len(parts) > 1 else ""

        if not current_name:
            return jsonify({
                "error": {
                    "code": "INVALID_ACTION",
                    "message": "Server name is required for settings_zfs_edit_name_*",
                    "request_id": request_id,
                }
            }), 400

        if not new_name:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": (
                    "✏️ Переименование ZFS-сервера\n\n"
                    "Отправьте действие в формате:\n"
                    f"`settings_zfs_edit_name_{quote(current_name, safe='')}|<новое_имя>`"
                ),
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_zfs_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}
        if current_name not in zfs_servers:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": f"❌ ZFS-сервер «{current_name}» не найден.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_zfs_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200
        if new_name in zfs_servers and new_name != current_name:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": f"❌ ZFS-сервер «{new_name}» уже существует.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_zfs_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        server_value = zfs_servers.pop(current_name, None)
        if not isinstance(server_value, dict):
            server_value = {"enabled": True}
        zfs_servers[new_name] = server_value
        settings_manager.set_setting('ZFS_SERVERS', zfs_servers, 'zfs')
        try:
            backup_db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if backup_db_path:
                conn = sqlite3.connect(str(backup_db_path))
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE zfs_pool_status SET server_name = ? WHERE server_name = ?",
                    (new_name, current_name),
                )
                conn.commit()
                conn.close()
        except Exception as exc:
            if "no such table: zfs_pool_status" not in str(exc):
                app.logger.warning(
                    "Failed to rename zfs_pool_status from %s to %s: %s",
                    current_name,
                    new_name,
                    exc,
                )

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"✅ ZFS-сервер переименован: «{current_name}» → «{new_name}».",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_zfs_list"},
                {"label": "↩️ Назад", "action": "settings_zfs"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_zfs_delete_"):
        server_name = unquote(raw_action[len("settings_zfs_delete_"):]).strip()
        if not server_name:
            return jsonify({
                "error": {
                    "code": "INVALID_ACTION",
                    "message": "Server name is required for settings_zfs_delete_*",
                    "request_id": request_id,
                }
            }), 400

        zfs_servers = settings_manager.get_setting('ZFS_SERVERS', {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}
        removed = zfs_servers.pop(server_name, None)
        if removed is None:
            return jsonify({
                "request_id": request_id,
                "action": action,
                "result": "accepted",
                "message": f"❌ ZFS-сервер «{server_name}» не найден.",
                "menu_options": [
                    {"label": "↩️ Назад", "action": "settings_zfs_list"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            }), 200

        settings_manager.set_setting('ZFS_SERVERS', zfs_servers, 'zfs')
        try:
            backup_db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if backup_db_path:
                conn = sqlite3.connect(str(backup_db_path))
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM zfs_pool_status WHERE server_name = ?",
                    (server_name,),
                )
                conn.commit()
                conn.close()
        except Exception as exc:
            if "no such table: zfs_pool_status" not in str(exc):
                app.logger.warning(
                    "Failed to delete zfs_pool_status for %s: %s",
                    server_name,
                    exc,
                )

        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": f"✅ ZFS-сервер «{server_name}» удалён.",
            "menu_options": [
                {"label": "📋 Обновить список", "action": "settings_zfs_list"},
                {"label": "↩️ Назад", "action": "settings_zfs"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("settings_db_"):
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "🗃️ Детальное редактирование БД пока доступно в Telegram-боте.",
            "menu_options": [
                {"label": "↩️ Назад", "action": "settings_db_main"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action.startswith("supplier_stock_"):
        return jsonify({
            "request_id": request_id,
            "action": action,
            "result": "accepted",
            "message": "📦 Детальная настройка раздела остатков поставщиков пока доступна в Telegram-боте.",
            "menu_options": [
                {"label": "↩️ Назад", "action": "settings_ext_supplier_stock"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        }), 200

    if action == 'settings_resources':
        return jsonify({
            "request_id": request_id,
            "action": action,
            "message": "Откройте раздел «Доступность и ресурсы» для просмотра ресурсов серверов.",
        }), 200

    return jsonify({
        "error": {
            "code": "INVALID_ACTION",
            "message": (
                "Supported actions: enable_all, disable_all, "
                "settings_ext_enable_all, settings_ext_disable_all, "
                "settings_ext_toggle_{extension_id}, settings_ext_*, settings_zfs, settings_resources"
            ),
            "request_id": request_id,
        }
    }), 400


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
