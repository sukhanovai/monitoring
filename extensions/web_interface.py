"""
/extensions/supplier_stock_files.py
Server Monitoring System v8.6.0
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface
РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ
Р’РµСЂСЃРёСЏ: 8.6.0
РђРІС‚РѕСЂ: РђР»РµРєСЃР°РЅРґСЂ РЎСѓС…Р°РЅРѕРІ (c)
Р›РёС†РµРЅР·РёСЏ: MIT
Р’РµР±-РёРЅС‚РµСЂС„РµР№СЃ
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

# HTML С€Р°Р±Р»РѕРЅ СЃ РІРєР»Р°РґРєР°РјРё Рё С‚РµРјРЅРѕР№ С‚РµРјРѕР№ (Р±РµР· РІРєР»Р°РґРєРё Р РµСЃСѓСЂСЃС‹)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>рџЊђ РњРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂРѕРІ</title>
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
        
        /* Р’РєР»Р°РґРєРё */
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
        
        /* РћР±С‰РёРµ СЃС‚РёР»Рё РєР°СЂС‚РѕС‡РµРє */
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
        
        /* РЎС‚РёР»Рё РґР»СЏ СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ */
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
        
        /* РљРЅРѕРїРєРё */
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
        
        /* РђРЅРёРјР°С†РёРё */
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
            <h1>рџЊђ РњРѕРЅРёС‚РѕСЂРёРЅРі СЃРµСЂРІРµСЂРѕРІ</h1>
            <div class="status">РЎРёСЃС‚РµРјР° СЂР°Р±РѕС‚Р°РµС‚ вЂў РџРѕСЃР»РµРґРЅРµРµ РѕР±РЅРѕРІР»РµРЅРёРµ: <span id="lastUpdate">{{ last_update }}</span></div>
        </div>
        
        <!-- Р’РєР»Р°РґРєРё -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('overview')">рџ“Љ РћР±Р·РѕСЂ</div>
            <div class="tab" onclick="switchTab('servers')">рџ–ҐпёЏ РЎРµСЂРІРµСЂР°</div>
            <div class="tab" onclick="switchTab('server-management')">вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ СЃРµСЂРІРµСЂР°РјРё</div>
            <div class="tab" onclick="switchTab('controls')">рџЋ›пёЏ РЈРїСЂР°РІР»РµРЅРёРµ</div>
        </div>
        
        <!-- РЎРѕРґРµСЂР¶РёРјРѕРµ РІРєР»Р°РґРєРё РћР±Р·РѕСЂ -->
        <div id="overview" class="tab-content active">
            <div class="dashboard">
                <div class="card">
                    <h2>рџ“Љ РћР±С‰Р°СЏ СЃС‚Р°С‚РёСЃС‚РёРєР°</h2>
                    <div class="stat-item">
                        <span>Р’СЃРµРіРѕ СЃРµСЂРІРµСЂРѕРІ:</span>
                        <span class="stat-value">{{ stats.total_servers }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Р”РѕСЃС‚СѓРїРЅРѕ:</span>
                        <span class="stat-value status-up">{{ stats.servers_up }}</span>
                    </div>
                    <div class="stat-item">
                        <span>РќРµРґРѕСЃС‚СѓРїРЅРѕ:</span>
                        <span class="stat-value status-down">{{ stats.servers_down }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ:</span>
                        <span class="stat-value">{{ stats.availability_percentage }}%</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>рџ”„ РњРѕРЅРёС‚РѕСЂРёРЅРі</h2>
                    <div class="stat-item">
                        <span>РЎС‚Р°С‚СѓСЃ:</span>
                        <span class="stat-value status-info">{{ stats.monitoring_mode }}</span>
                    </div>
                    <div class="stat-item">
                        <span>РўРёС…РёР№ СЂРµР¶РёРј:</span>
                        <span class="stat-value">{{ stats.silent_mode }}</span>
                    </div>
                    <div class="stat-item">
                        <span>РџРѕСЃР»РµРґРЅСЏСЏ РїСЂРѕРІРµСЂРєР°:</span>
                        <span class="stat-value">{{ stats.last_check_time }}</span>
                    </div>
                    <div class="stat-item">
                        <span>РРЅС‚РµСЂРІР°Р»:</span>
                        <span class="stat-value">{{ stats.check_interval }} СЃРµРє</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>рџ“€ Р РµСЃСѓСЂСЃС‹</h2>
                    <div class="stat-item">
                        <span>РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ:</span>
                        <span class="stat-value">{{ stats.resource_check_status }}</span>
                    </div>
                    <div class="stat-item">
                        <span>РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё:</span>
                        <span class="stat-value">{{ stats.resource_check_interval }} РјРёРЅ</span>
                    </div>
                    <div class="stat-item">
                        <span>РџСЂРѕР±Р»РµРј СЃ СЂРµСЃСѓСЂСЃР°РјРё:</span>
                        <span class="stat-value status-warning">{{ stats.resource_alerts }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Р’СЂРµРјСЏ СЂР°Р±РѕС‚С‹:</span>
                        <span class="stat-value">{{ stats.uptime }}</span>
                    </div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn btn-success" onclick="runCheck('quick')">рџ”Ќ Р‘С‹СЃС‚СЂР°СЏ РїСЂРѕРІРµСЂРєР°</button>
                <button class="btn btn-info" onclick="runCheck('resources')">рџ“€ РџСЂРѕРІРµСЂРёС‚СЊ СЂРµСЃСѓСЂСЃС‹</button>
                <button class="btn btn-warning" onclick="runCheck('report')">рџ“Љ РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ РѕС‚С‡РµС‚</button>
            </div>
        </div>
        
        <!-- РЎРѕРґРµСЂР¶РёРјРѕРµ РІРєР»Р°РґРєРё РЎРµСЂРІРµСЂР° -->
        <div id="servers" class="tab-content">
            <h2 style="margin-bottom: 20px;">рџ–ҐпёЏ РЎС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂРѕРІ</h2>
            <div class="server-list">
                {% for server in servers %}
                <div class="server-item {% if server.status == 'down' %}down{% elif server.status == 'warning' %}warning{% endif %} fade-in">
                    <div class="server-info">
                        <div class="server-name">{{ server.name }}</div>
                        <div class="server-details">{{ server.ip }} вЂў {{ server.type.upper() }} вЂў {{ server.os }}</div>
                        {% if server.resources %}
                        <div class="server-resources">
                            <div class="resource-item">
                                <span>рџ’» CPU:</span>
                                <span class="resource-cpu {{ server.resources.cpu_class }}">{{ server.resources.cpu }}%</span>
                            </div>
                            <div class="resource-item">
                                <span>рџ§  RAM:</span>
                                <span class="resource-ram {{ server.resources.ram_class }}">{{ server.resources.ram }}%</span>
                            </div>
                            <div class="resource-item">
                                <span>рџ’ѕ Disk:</span>
                                <span class="resource-disk {{ server.resources.disk_class }}">{{ server.resources.disk }}%</span>
                            </div>
                            {% if server.resources.load_avg and server.resources.load_avg != 'N/A' %}
                            <div class="resource-item">
                                <span>рџ“Љ Load:</span>
                                <span>{{ server.resources.load_avg }}</span>
                            </div>
                            {% endif %}
                            {% if server.resources.uptime and server.resources.uptime != 'N/A' %}
                            <div class="resource-item">
                                <span>вЏ±пёЏ Uptime:</span>
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
        
        <!-- РЎРѕРґРµСЂР¶РёРјРѕРµ РІРєР»Р°РґРєРё РЈРїСЂР°РІР»РµРЅРёРµ СЃРµСЂРІРµСЂР°РјРё -->
        <div id="server-management" class="tab-content">
            <h2 style="margin-bottom: 20px;">вљ™пёЏ РЈРїСЂР°РІР»РµРЅРёРµ СЃРїРёСЃРєРѕРј СЃРµСЂРІРµСЂРѕРІ</h2>
            
            <div class="card">
                <h2>рџ“‹ РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ</h2>
                <div id="serverListContainer">
                    <!-- РЎРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ Р±СѓРґРµС‚ Р·Р°РіСЂСѓР¶РµРЅ Р·РґРµСЃСЊ -->
                </div>
                <button class="btn btn-success" onclick="loadServerList()">рџ”„ РћР±РЅРѕРІРёС‚СЊ СЃРїРёСЃРѕРє</button>
            </div>
            
            <div class="card">
                <h2>вћ• Р”РѕР±Р°РІРёС‚СЊ РЅРѕРІС‹Р№ СЃРµСЂРІРµСЂ</h2>
                <form id="addServerForm" style="display: grid; gap: 15px; margin-top: 15px;">
                    <input type="text" name="name" placeholder="РќР°Р·РІР°РЅРёРµ СЃРµСЂРІРµСЂР°" required style="padding: 10px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                    <input type="text" name="ip" placeholder="IP Р°РґСЂРµСЃ" required style="padding: 10px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                    <select name="type" style="padding: 10px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white;">
                        <option value="linux">Linux</option>
                        <option value="windows">Windows</option>
                    </select>
                    <button type="submit" class="btn btn-success">вњ… Р”РѕР±Р°РІРёС‚СЊ СЃРµСЂРІРµСЂ</button>
                </form>
            </div>
        </div>     
                
        <!-- РЎРѕРґРµСЂР¶РёРјРѕРµ РІРєР»Р°РґРєРё РЈРїСЂР°РІР»РµРЅРёРµ -->
        <div id="controls" class="tab-content">
            <h2 style="margin-bottom: 20px;">рџЋ›пёЏ РЈРїСЂР°РІР»РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРј</h2>
            
            <div class="dashboard">
                <div class="card">
                    <h2>рџ”§ Р”РµР№СЃС‚РІРёСЏ</h2>
                    <div class="controls" style="flex-direction: column; gap: 15px;">
                        <button class="btn btn-success" onclick="runAction('check_all')">рџ”Ќ РџСЂРѕРІРµСЂРёС‚СЊ РІСЃРµ СЃРµСЂРІРµСЂС‹</button>
                        <button class="btn btn-info" onclick="runAction('check_resources')">рџ“€ РџСЂРѕРІРµСЂРёС‚СЊ СЂРµСЃСѓСЂСЃС‹</button>
                        <button class="btn btn-warning" onclick="runAction('morning_report')">рџ“Љ РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚</button>
                        <button class="btn btn-danger" onclick="runAction('restart_service')">рџ”„ РџРµСЂРµР·Р°РїСѓСЃРє СЃРµСЂРІРёСЃР°</button>
                    </div>
                </div>
                
                <div class="card">
                    <h2>вљ™пёЏ РќР°СЃС‚СЂРѕР№РєРё</h2>
                    <div class="stat-item">
                        <span>РўРµРєСѓС‰РёР№ СЂРµР¶РёРј:</span>
                        <span class="stat-value">{{ stats.monitoring_mode }}</span>
                    </div>
                    <div class="stat-item">
                        <span>РўРёС…РёР№ СЂРµР¶РёРј:</span>
                        <span class="stat-value">{{ stats.silent_mode }}</span>
                    </div>
                    <div class="controls" style="margin-top: 20px;">
                        <button class="btn {% if stats.monitoring_mode == 'рџџў РђРєС‚РёРІРµРЅ' %}btn-warning{% else %}btn-success{% endif %}" 
                                onclick="toggleMonitoring()">
                            {% if stats.monitoring_mode == 'рџџў РђРєС‚РёРІРµРЅ' %}вЏёпёЏ РџСЂРёРѕСЃС‚Р°РЅРѕРІРёС‚СЊ{% else %}в–¶пёЏ Р’РѕР·РѕР±РЅРѕРІРёС‚СЊ{% endif %}
                        </button>
                        <button class="btn {% if stats.silent_mode == 'рџ”‡ Р’РєР»СЋС‡РµРЅ' %}btn-info{% else %}btn-warning{% endif %}" 
                                onclick="toggleSilentMode()">
                            {% if stats.silent_mode == 'рџ”‡ Р’РєР»СЋС‡РµРЅ' %}рџ”Љ Р’С‹РєР»СЋС‡РёС‚СЊ С‚РёС…РёР№{% else %}рџ”‡ Р’РєР»СЋС‡РёС‚СЊ С‚РёС…РёР№{% endif %}
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h2>рџ“‹ Р›РѕРіРё РґРµР№СЃС‚РІРёР№</h2>
                <div id="actionLogs" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 0.9em;">
                    <!-- Р›РѕРіРё Р±СѓРґСѓС‚ РґРѕР±Р°РІР»СЏС‚СЊСЃСЏ СЃСЋРґР° -->
                </div>
            </div>
        </div>
        
        <button class="refresh-btn" onclick="location.reload()">рџ”„ РћР±РЅРѕРІРёС‚СЊ РґР°РЅРЅС‹Рµ</button>
        
        <div class="last-update">
            РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЃРµСЂРІРµСЂРѕРІ вЂў Р’РµСЂСЃРёСЏ 2.0 вЂў РўРµРјРЅР°СЏ С‚РµРјР°
        </div>
    </div>

    <script>
        // РџРµСЂРµРєР»СЋС‡РµРЅРёРµ РѕСЃРЅРѕРІРЅС‹С… РІРєР»Р°РґРѕРє
        function switchTab(tabName) {
            // РЎРєСЂС‹С‚СЊ РІСЃРµ РІРєР»Р°РґРєРё
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // РџРѕРєР°Р·Р°С‚СЊ РІС‹Р±СЂР°РЅРЅСѓСЋ РІРєР»Р°РґРєСѓ
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        // Р—Р°РїСѓСЃРє РїСЂРѕРІРµСЂРѕРє
        function runCheck(type) {
            addLog(`Р—Р°РїСѓСЃРє ${getCheckName(type)}...`);
            fetch(`/api/run_check?type=${type}`)
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success && data.reload !== false) {
                        setTimeout(() => location.reload(), 2000);
                    }
                })
                .catch(error => {
                    addLog(`РћС€РёР±РєР°: ${error}`);
                });
        }
        
        // Р—Р°РїСѓСЃРє РґРµР№СЃС‚РІРёР№
        function runAction(action) {
            addLog(`Р’С‹РїРѕР»РЅРµРЅРёРµ: ${getActionName(action)}...`);
            fetch(`/api/run_action?action=${action}`)
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success && data.reload) {
                        setTimeout(() => location.reload(), 2000);
                    }
                })
                .catch(error => {
                    addLog(`РћС€РёР±РєР°: ${error}`);
                });
        }
        
        // РџРµСЂРµРєР»СЋС‡РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
        function toggleMonitoring() {
            runAction('toggle_monitoring');
        }
        
        // РџРµСЂРµРєР»СЋС‡РµРЅРёРµ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°
        function toggleSilentMode() {
            runAction('toggle_silent');
        }
        
        // Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Рµ С„СѓРЅРєС†РёРё
        function getCheckName(type) {
            const names = {
                'quick': 'Р±С‹СЃС‚СЂРѕР№ РїСЂРѕРІРµСЂРєРё',
                'resources': 'РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ', 
                'report': 'С„РѕСЂРјРёСЂРѕРІР°РЅРёСЏ РѕС‚С‡РµС‚Р°'
            };
            return names[type] || type;
        }
        
        function getActionName(action) {
            const names = {
                'check_all': 'РџСЂРѕРІРµСЂРєР° РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ',
                'check_resources': 'РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ',
                'morning_report': 'Р¤РѕСЂРјРёСЂРѕРІР°РЅРёРµ СѓС‚СЂРµРЅРЅРµРіРѕ РѕС‚С‡РµС‚Р°',
                'restart_service': 'РџРµСЂРµР·Р°РїСѓСЃРє СЃРµСЂРІРёСЃР°',
                'toggle_monitoring': 'РџРµСЂРµРєР»СЋС‡РµРЅРёРµ РјРѕРЅРёС‚РѕСЂРёРЅРіР°',
                'toggle_silent': 'РџРµСЂРµРєР»СЋС‡РµРЅРёРµ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР°'
            };
            return names[action] || action;
        }
        
        function addLog(message) {
            const logDiv = document.getElementById('actionLogs');
            const timestamp = new Date().toLocaleTimeString('ru-RU');
            logDiv.innerHTML = `<div>[${timestamp}] ${message}</div>` + logDiv.innerHTML;
        }
        
        // РЈРїСЂР°РІР»РµРЅРёРµ СЃРµСЂРІРµСЂР°РјРё
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
                                    <div class="server-details">${server.ip} вЂў ${server.type.toUpperCase()}</div>
                                </div>
                                <button class="btn btn-danger" onclick="deleteServer('${server.ip}')">рџ—‘пёЏ РЈРґР°Р»РёС‚СЊ</button>
                            </div>
                        `).join('') + '</div>';
                })
                .catch(error => {
                    console.error('РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ:', error);
                });
        }

        function deleteServer(ip) {
            if (confirm(`РЈРґР°Р»РёС‚СЊ СЃРµСЂРІРµСЂ ${ip}?`)) {
                fetch(`/api/servers?ip=${ip}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        loadServerList();
                    });
            }
        }

        // РћР±СЂР°Р±РѕС‚РєР° С„РѕСЂРјС‹ РґРѕР±Р°РІР»РµРЅРёСЏ СЃРµСЂРІРµСЂР°
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

        // РњРѕРґРёС„РёС†РёСЂСѓРµРј СЃСѓС‰РµСЃС‚РІСѓСЋС‰СѓСЋ С„СѓРЅРєС†РёСЋ switchTab РґР»СЏ Р°РІС‚РѕР·Р°РіСЂСѓР·РєРё СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ
        const originalSwitchTab = switchTab;
        switchTab = function(tabName) {
            originalSwitchTab(tabName);
            
            // РђРІС‚РѕР·Р°РіСЂСѓР·РєР° СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ РїСЂРё РѕС‚РєСЂС‹С‚РёРё РІРєР»Р°РґРєРё
            if (tabName === 'server-management') {
                setTimeout(loadServerList, 100);
            }
        };       
        
        // РђРІС‚Рѕ-РѕР±РЅРѕРІР»РµРЅРёРµ РєР°Р¶РґС‹Рµ 30 СЃРµРєСѓРЅРґ
        setTimeout(() => {
            location.reload();
        }, 30000);
        
        // РћР±РЅРѕРІР»РµРЅРёРµ РІСЂРµРјРµРЅРё
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
    """РћРїСЂРµРґРµР»СЏРµС‚ РєР»Р°СЃСЃ РґР»СЏ РѕРєСЂР°С€РёРІР°РЅРёСЏ СЂРµСЃСѓСЂСЃРѕРІ"""
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
    """РџРѕР»СѓС‡Р°РµС‚ СЃС‚Р°С‚РёСЃС‚РёРєСѓ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"""
    try:
        # РџСЂРѕР±СѓРµРј РїРѕР»СѓС‡РёС‚СЊ РґР°РЅРЅС‹Рµ РёР· С„Р°Р№Р»Р° СЃС‚Р°С‚РёСЃС‚РёРєРё
        stats_data = {}
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                stats_data = json.load(f)
        
        # РџРѕР»СѓС‡Р°РµРј С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂРѕРІ
        from monitor_core import get_current_server_status, monitoring_active, last_check_time
        from monitor_core import is_silent_time, resource_history
        from extensions.server_list import initialize_servers
        
        current_status = get_current_server_status()
        servers_list = initialize_servers()
        
        # Р¤РѕСЂРјРёСЂСѓРµРј СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ РґР»СЏ РѕС‚РѕР±СЂР°Р¶РµРЅРёСЏ
        servers_display = []
        
        for server in servers_list:
            is_up = any(s["ip"] == server["ip"] for s in current_status["ok"])
            is_down = any(s["ip"] == server["ip"] for s in current_status["failed"])
            
            status = "up" if is_up else "down"
            status_display = "вњ… Р”РѕСЃС‚СѓРїРµРЅ" if is_up else "вќЊ РќРµРґРѕСЃС‚СѓРїРµРЅ"
            
            # РџРѕР»СѓС‡Р°РµРј РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ СЂРµСЃСѓСЂСЃР°С…
            resources_data = None
            os_info = "Unknown"
            if server["ip"] in resource_history and resource_history[server["ip"]]:
                latest_resources = resource_history[server["ip"]][-1]
                os_info = latest_resources.get("os", "Unknown")
                
                # Р¤РѕСЂРјР°С‚РёСЂСѓРµРј СЂРµСЃСѓСЂСЃС‹ СЃ РєР»Р°СЃСЃР°РјРё РґР»СЏ РѕРєСЂР°С€РёРІР°РЅРёСЏ
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
                
                # РџСЂРѕРІРµСЂСЏРµРј РЅР° РїСЂРѕР±Р»РµРјС‹ СЃ СЂРµСЃСѓСЂСЃР°РјРё РґР»СЏ СЃС‚Р°С‚СѓСЃР°
                if resources_data and (cpu_value > 80 or ram_value > 85 or disk_value > 80):
                    status = "warning"
                    status_display = "вљ пёЏ Р’С‹СЃРѕРєР°СЏ РЅР°РіСЂСѓР·РєР°"
            
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
        
        # РЎРѕСЂС‚РёСЂСѓРµРј СЃРµСЂРІРµСЂС‹: СЃРЅР°С‡Р°Р»Р° РїСЂРѕР±Р»РµРјРЅС‹Рµ, РїРѕС‚РѕРј РґРѕСЃС‚СѓРїРЅС‹Рµ
        servers_display.sort(key=lambda x: (0 if x["status"] == "down" else 1 if x["status"] == "warning" else 2))
        
        # Р Р°СЃСЃС‡РёС‚С‹РІР°РµРј СЃС‚Р°С‚РёСЃС‚РёРєСѓ
        total_servers = len(servers_list)
        servers_up = len(current_status["ok"])
        servers_down = len(current_status["failed"])
        availability_percentage = round((servers_up / total_servers) * 100, 1) if total_servers > 0 else 0
        
        # РџРѕР»СѓС‡Р°РµРј РЅР°СЃС‚СЂРѕР№РєРё РёР· РєРѕРЅС„РёРіР°
        from config import CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL
        resource_check_minutes = RESOURCE_CHECK_INTERVAL // 60
        
        # РЎС‡РёС‚Р°РµРј РїСЂРѕР±Р»РµРјС‹ СЃ СЂРµСЃСѓСЂСЃР°РјРё
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
            "monitoring_mode": "рџџў РђРєС‚РёРІРµРЅ" if monitoring_active else "рџ”ґ РџСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ",
            "silent_mode": "рџ”‡ Р’РєР»СЋС‡РµРЅ" if is_silent_time() else "рџ”Љ Р’С‹РєР»СЋС‡РµРЅ",
            "resource_check_status": "рџџў Р Р°Р±РѕС‚Р°РµС‚" if monitoring_active and not is_silent_time() else "вЏёпёЏ РџСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ",
            "resource_check_interval": resource_check_minutes,
            "resource_alerts": resource_alerts_count,
            "uptime": stats_data.get("uptime", "N/A")
        }
        
        return stats, servers_display
        
    except Exception as e:
        print(f"вќЊ РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё: {e}")
        # Р’РѕР·РІСЂР°С‰Р°РµРј РґР°РЅРЅС‹Рµ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РїСЂРё РѕС€РёР±РєРµ
        return {
            "total_servers": 0,
            "servers_up": 0,
            "servers_down": 0,
            "availability_percentage": 0,
            "last_check_time": "N/A",
            "check_interval": 0,
            "monitoring_mode": "вќЊ РћС€РёР±РєР°",
            "silent_mode": "N/A",
            "resource_check_status": "вќЊ РћС€РёР±РєР°",
            "resource_check_interval": 0,
            "resource_alerts": 0,
            "uptime": "N/A"
        }, []

@app.route('/')
def index():
    """Р“Р»Р°РІРЅР°СЏ СЃС‚СЂР°РЅРёС†Р° РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°"""
    try:
        stats, servers = get_monitoring_stats()
        
        return render_template_string(
            HTML_TEMPLATE,
            stats=stats,
            servers=servers,
            last_update=datetime.now().strftime("%H:%M:%S")
        )
    except Exception as e:
        return f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°: {e}"

@app.route('/api/run_check')
def api_run_check():
    """API РґР»СЏ Р·Р°РїСѓСЃРєР° РїСЂРѕРІРµСЂРѕРє"""
    check_type = request.args.get('type', 'quick')
    
    try:
        if check_type == 'quick':
            # Р—Р°РїСѓСЃРє Р±С‹СЃС‚СЂРѕР№ РїСЂРѕРІРµСЂРєРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
            from monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"вњ… Р‘С‹СЃС‚СЂР°СЏ РїСЂРѕРІРµСЂРєР° РІС‹РїРѕР»РЅРµРЅР°: {len(status['ok'])} РґРѕСЃС‚СѓРїРЅРѕ, {len(status['failed'])} РЅРµРґРѕСЃС‚СѓРїРЅРѕ"
            
        elif check_type == 'resources':
            # Р—Р°РїСѓСЃРє РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ
            from monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "вњ… РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РІС‹РїРѕР»РЅРµРЅР°. Р”Р°РЅРЅС‹Рµ РѕР±РЅРѕРІСЏС‚СЃСЏ С‡РµСЂРµР· 1-2 РјРёРЅСѓС‚С‹."
            
        elif check_type == 'report':
            # Р¤РѕСЂРјРёСЂРѕРІР°РЅРёРµ РѕС‚С‡РµС‚Р°
            from monitor_core import send_morning_report
            send_morning_report()
            message = "вњ… РћС‚С‡РµС‚ СЃС„РѕСЂРјРёСЂРѕРІР°РЅ Рё РѕС‚РїСЂР°РІР»РµРЅ РІ Telegram"
            
        else:
            message = "вќЊ РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РёРї РїСЂРѕРІРµСЂРєРё"
            
        return jsonify({"success": True, "message": message, "reload": check_type != 'resources'})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"вќЊ РћС€РёР±РєР°: {str(e)}"})

@app.route('/api/run_action')
def api_run_action():
    """API РґР»СЏ РІС‹РїРѕР»РЅРµРЅРёСЏ РґРµР№СЃС‚РІРёР№"""
    action = request.args.get('action', '')
    
    try:
        if action == 'check_all':
            from monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"вњ… РџСЂРѕРІРµСЂРєР° РІСЃРµС… СЃРµСЂРІРµСЂРѕРІ РІС‹РїРѕР»РЅРµРЅР°: {len(status['ok'])} РґРѕСЃС‚СѓРїРЅРѕ, {len(status['failed'])} РЅРµРґРѕСЃС‚СѓРїРЅРѕ"
            
        elif action == 'check_resources':
            from monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "вњ… РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ Р·Р°РїСѓС‰РµРЅР°. Р”Р°РЅРЅС‹Рµ РѕР±РЅРѕРІСЏС‚СЃСЏ С‡РµСЂРµР· 1-2 РјРёРЅСѓС‚С‹."
            
        elif action == 'morning_report':
            from monitor_core import send_morning_report
            send_morning_report()
            message = "вњ… РЈС‚СЂРµРЅРЅРёР№ РѕС‚С‡РµС‚ РѕС‚РїСЂР°РІР»РµРЅ РІ Telegram"
            
        elif action == 'restart_service':
            # РџРµСЂРµР·Р°РїСѓСЃРє СЃРµСЂРІРёСЃР° (РѕСЃС‚РѕСЂРѕР¶РЅРѕ!)
            subprocess.run(['systemctl', 'restart', 'server-monitor.service'], check=True)
            message = "вњ… РЎРµСЂРІРёСЃ РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚СЃСЏ..."
            
        elif action == 'toggle_monitoring':
            # Р’ СЂРµР°Р»СЊРЅРѕР№ СЂРµР°Р»РёР·Р°С†РёРё Р·РґРµСЃСЊ РЅСѓР¶РЅРѕ РјРµРЅСЏС‚СЊ РіР»РѕР±Р°Р»СЊРЅСѓСЋ РїРµСЂРµРјРµРЅРЅСѓСЋ
            message = "вљ пёЏ Р¤СѓРЅРєС†РёСЏ РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР° РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ"
            
        elif action == 'toggle_silent':
            # Р’ СЂРµР°Р»СЊРЅРѕР№ СЂРµР°Р»РёР·Р°С†РёРё Р·РґРµСЃСЊ РЅСѓР¶РЅРѕ РјРµРЅСЏС‚СЊ РіР»РѕР±Р°Р»СЊРЅСѓСЋ РїРµСЂРµРјРµРЅРЅСѓСЋ
            message = "вљ пёЏ Р¤СѓРЅРєС†РёСЏ РїРµСЂРµРєР»СЋС‡РµРЅРёСЏ С‚РёС…РѕРіРѕ СЂРµР¶РёРјР° РІ СЂР°Р·СЂР°Р±РѕС‚РєРµ"
            
        else:
            message = "вќЊ РќРµРёР·РІРµСЃС‚РЅРѕРµ РґРµР№СЃС‚РІРёРµ"
            
        return jsonify({
            "success": True, 
            "message": message, 
            "reload": action not in ['check_resources', 'toggle_monitoring', 'toggle_silent']
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"вќЊ РћС€РёР±РєР°: {str(e)}"})

@app.route('/api/status')
def api_status():
    """API endpoint РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ СЃС‚Р°С‚СѓСЃР°"""
    stats, servers = get_monitoring_stats()
    return jsonify({
        "status": "ok", 
        "message": "РЎРёСЃС‚РµРјР° РјРѕРЅРёС‚РѕСЂРёРЅРіР° СЂР°Р±РѕС‚Р°РµС‚",
        "data": {
            "stats": stats,
            "servers": servers,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/api/servers')
def api_servers():
    """API endpoint РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ СЃРїРёСЃРєР° СЃРµСЂРІРµСЂРѕРІ"""
    stats, servers = get_monitoring_stats()
    return jsonify({
        "servers": servers,
        "count": len(servers),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ СЃС‚Р°С‚РёСЃС‚РёРєРё"""
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
    """API РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ СЃРїРёСЃРєРѕРј СЃРµСЂРІРµСЂРѕРІ"""
    if request.method == 'GET':
        # РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє СЃРµСЂРІРµСЂРѕРІ
        from extensions.server_list import initialize_servers
        servers = initialize_servers()
        return jsonify({"servers": servers})
    
    elif request.method == 'POST':
        # Р”РѕР±Р°РІРёС‚СЊ РЅРѕРІС‹Р№ СЃРµСЂРІРµСЂ
        data = request.json
        # Р—РґРµСЃСЊ РґРѕР±Р°РІРёС‚СЊ Р»РѕРіРёРєСѓ СЃРѕС…СЂР°РЅРµРЅРёСЏ РІ server_list.json
        return jsonify({"success": True, "message": "РЎРµСЂРІРµСЂ РґРѕР±Р°РІР»РµРЅ"})
    
    elif request.method == 'PUT':
        # РћР±РЅРѕРІРёС‚СЊ СЃРµСЂРІРµСЂ
        data = request.json
        # Р›РѕРіРёРєР° РѕР±РЅРѕРІР»РµРЅРёСЏ
        return jsonify({"success": True, "message": "РЎРµСЂРІРµСЂ РѕР±РЅРѕРІР»РµРЅ"})
    
    elif request.method == 'DELETE':
        # РЈРґР°Р»РёС‚СЊ СЃРµСЂРІРµСЂ
        server_ip = request.args.get('ip')
        # Р›РѕРіРёРєР° СѓРґР°Р»РµРЅРёСЏ
        return jsonify({"success": True, "message": "РЎРµСЂРІРµСЂ СѓРґР°Р»РµРЅ"})
    
def start_web_server():
    """Р—Р°РїСѓСЃРєР°РµС‚ РІРµР±-СЃРµСЂРІРµСЂ"""
    print(f"рџЊђ Р—Р°РїСѓСЃРє РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР° РЅР° http://{WEB_HOST}:{WEB_PORT}")
    try:
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"вќЊ РћС€РёР±РєР° Р·Р°РїСѓСЃРєР° РІРµР±-СЃРµСЂРІРµСЂР°: {e}")

if __name__ == "__main__":
    start_web_server()
