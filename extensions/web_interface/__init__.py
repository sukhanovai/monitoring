"""
/extensions/web_interface/__init__.py
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
            {% if supplier_stock_enabled %}
            <div class="tab" onclick="switchTab('supplier-stock')">рџ“¦ РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ</div>
            {% endif %}
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

        {% if supplier_stock_enabled %}
        <!-- РЎРѕРґРµСЂР¶РёРјРѕРµ РІРєР»Р°РґРєРё РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ -->
        <div id="supplier-stock" class="tab-content">
            <h2 style="margin-bottom: 20px;">рџ“¦ РћСЃС‚Р°С‚РєРё РїРѕСЃС‚Р°РІС‰РёРєРѕРІ</h2>

            <div class="dashboard">
                <div class="card">
                    <h2>вЏ° Р Р°СЃРїРёСЃР°РЅРёРµ</h2>
                    <div class="stat-item">
                        <span>РЎС‚Р°С‚СѓСЃ:</span>
                        <span class="stat-value">{{ supplier_stock.schedule_status }}</span>
                    </div>
                    <div class="stat-item">
                        <span>Р’СЂРµРјСЏ:</span>
                        <span class="stat-value">{{ supplier_stock.schedule_time }}</span>
                    </div>
                    <div class="controls" style="margin-top: 15px; gap: 10px; flex-wrap: wrap;">
                        <input type="text" id="supplierScheduleTime" value="{{ supplier_stock.schedule_time_value }}"
                               placeholder="06:00, 12:30"
                               title="HH:MM, РјРѕР¶РЅРѕ РЅРµСЃРєРѕР»СЊРєРѕ С‡РµСЂРµР· РїСЂРѕР±РµР»/Р·Р°РїСЏС‚СѓСЋ/;"
                               style="padding: 8px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white; min-width: 180px;">
                        <label style="display: flex; align-items: center; gap: 6px;">
                            РџРµСЂРёРѕРґ (РґРЅРµР№):
                            <input type="number" id="supplierReportPeriod" min="1" value="{{ supplier_stock.report_period_days }}"
                                   style="padding: 8px; border-radius: 6px; border: 1px solid #555; background: rgba(60,60,70,0.8); color: white; width: 110px;"
                                   title="РџРµСЂРёРѕРґ РѕС‚С‡РµС‚РѕРІ (РґРЅРµР№)" placeholder="Р”РЅРµР№">
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px;">
                            <input type="checkbox" id="supplierScheduleEnabled" {% if supplier_stock.schedule_enabled %}checked{% endif %}>
                            Р’РєР»СЋС‡РµРЅРѕ
                        </label>
                        <button class="btn btn-success" onclick="saveSupplierSchedule()">рџ’ѕ РЎРѕС…СЂР°РЅРёС‚СЊ</button>
                        <button class="btn btn-info" onclick="runSupplierFetch()">рџ“Ґ Р—Р°РїСѓСЃС‚РёС‚СЊ СЃРµР№С‡Р°СЃ</button>
                    </div>
                </div>

                <div class="card">
                    <h2>рџ“¦ РСЃС‚РѕС‡РЅРёРєРё</h2>
                    {% if supplier_stock.sources %}
                    <div class="server-list">
                        {% for source in supplier_stock.sources %}
                        <div class="server-item">
                            <div class="server-info">
                                <div class="server-name">
                                    {% if source.enabled %}рџџў{% else %}рџ”ґ{% endif %}
                                    {{ source.name or source.id }}
                                </div>
                                <div class="server-details">{{ source.url or 'URL РЅРµ Р·Р°РґР°РЅ' }}</div>
                                <div class="server-details">Р¤Р°Р№Р»: {{ source.output_name or 'РЅРµ Р·Р°РґР°РЅ' }}</div>
                                <div class="server-details">РњРµС‚РѕРґ: {{ source.method }}</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="stat-item">РСЃС‚РѕС‡РЅРёРєРё РЅРµ РЅР°СЃС‚СЂРѕРµРЅС‹.</div>
                    {% endif %}
                </div>
            </div>

            <div class="card" style="margin-top: 20px;">
                <h2>рџ“‹ Р РµР·СѓР»СЊС‚Р°С‚С‹ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ</h2>
                <div class="supplier-details" style="margin-bottom: 10px;">
                    РџРµСЂРёРѕРґ: {{ supplier_stock.report_period_days }} РґРЅ.
                </div>
                <div class="supplier-report-tabs">
                    <button class="btn btn-info active" onclick="switchSupplierReports('download')">в¬‡пёЏ РџРѕР»СѓС‡РµРЅРЅС‹Рµ СЃРєР°С‡РёРІР°РЅРёРµРј</button>
                    <button class="btn btn-info" onclick="switchSupplierReports('mail')">вњ‰пёЏ РџРѕР»СѓС‡РµРЅРЅС‹Рµ РїРѕ РїРѕС‡С‚Рµ</button>
                </div>
                <div id="supplier-report-download" class="supplier-report-group active">
                    {% if supplier_stock.report_groups.download %}
                    <div class="server-list">
                        {% for report in supplier_stock.report_groups.download %}
                        <div class="server-item">
                            <div class="server-info">
                                <div class="server-name">{{ report.source_name }}</div>
                                <div class="supplier-details">РџРѕСЃР»РµРґРЅРµРµ РѕР±РЅРѕРІР»РµРЅРёРµ: {{ report.timestamp or 'РЅРµС‚ РґР°РЅРЅС‹С…' }}</div>
                                {% if report.method %}
                                <div class="supplier-details">РњРµС‚РѕРґ: {{ report.method }}</div>
                                {% endif %}
                                <div class="status-flags">
                                    <div class="status-flag">{{ report.receive.icon }} РџРѕР»СѓС‡РµРЅРёРµ</div>
                                    <div class="status-flag">{{ report.processing.icon }} РћР±СЂР°Р±РѕС‚РєР°</div>
                                    <div class="status-flag">{{ report.transfer.icon }} Р’С‹РіСЂСѓР·РєР°</div>
                                </div>
                            </div>
                            <button class="btn btn-info" onclick="showSupplierSourceStats('{{ report.source_id }}', '{{ report.source_kind }}')">рџ“Љ Р”РµС‚Р°Р»Рё</button>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="stat-item">РќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРµСЂРёРѕРґ РїРѕ СЃРєР°С‡РёРІР°РЅРёСЋ.</div>
                    {% endif %}
                </div>
                <div id="supplier-report-mail" class="supplier-report-group">
                    {% if supplier_stock.report_groups.mail %}
                    <div class="server-list">
                        {% for report in supplier_stock.report_groups.mail %}
                        <div class="server-item">
                            <div class="server-info">
                                <div class="server-name">{{ report.source_name }}</div>
                                <div class="supplier-details">РџРѕСЃР»РµРґРЅРµРµ РѕР±РЅРѕРІР»РµРЅРёРµ: {{ report.timestamp or 'РЅРµС‚ РґР°РЅРЅС‹С…' }}</div>
                                <div class="status-flags">
                                    <div class="status-flag">{{ report.receive.icon }} РџРѕР»СѓС‡РµРЅРёРµ</div>
                                    <div class="status-flag">{{ report.processing.icon }} РћР±СЂР°Р±РѕС‚РєР°</div>
                                    <div class="status-flag">{{ report.transfer.icon }} Р’С‹РіСЂСѓР·РєР°</div>
                                </div>
                            </div>
                            <button class="btn btn-info" onclick="showSupplierSourceStats('{{ report.source_id }}', '{{ report.source_kind }}')">рџ“Љ Р”РµС‚Р°Р»Рё</button>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="stat-item">РќРµС‚ РґР°РЅРЅС‹С… Р·Р° РїРµСЂРёРѕРґ РїРѕ РїРѕС‡С‚Рµ.</div>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endif %}
        
        <div id="supplierStatsModal" class="modal-overlay" onclick="closeSupplierSourceStats(event)">
            <div class="modal" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3 id="supplierStatsTitle">РЎС‚Р°С‚РёСЃС‚РёРєР° РёСЃС‚РѕС‡РЅРёРєР°</h3>
                    <button class="btn btn-danger" onclick="closeSupplierSourceStats()">вњ–</button>
                </div>
                <div id="supplierStatsSummary" class="supplier-details"></div>
                <div id="supplierStatsEntries" class="modal-list"></div>
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

        // Р—Р°РїСѓСЃРє Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ
        function runSupplierFetch() {
            addLog('рџ“¦ Р—Р°РїСѓСЃРє Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ...');
            fetch('/api/supplier_stock/run', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    addLog(data.message);
                    if (data.success) {
                        setTimeout(() => location.reload(), 1500);
                    }
                })
                .catch(error => {
                    addLog(`РћС€РёР±РєР°: ${error}`);
                });
        }

        // РЎРѕС…СЂР°РЅРµРЅРёРµ СЂР°СЃРїРёСЃР°РЅРёСЏ Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ
        function saveSupplierSchedule() {
            const timeInput = document.getElementById('supplierScheduleTime');
            const enabledInput = document.getElementById('supplierScheduleEnabled');
            const periodInput = document.getElementById('supplierReportPeriod');
            if (!timeInput || !enabledInput) {
                addLog('вљ пёЏ Р­Р»РµРјРµРЅС‚С‹ СЂР°СЃРїРёСЃР°РЅРёСЏ РЅРµ РЅР°Р№РґРµРЅС‹');
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
                    addLog(`РћС€РёР±РєР°: ${error}`);
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
                addLog('вљ пёЏ РћРєРЅРѕ СЃС‚Р°С‚РёСЃС‚РёРєРё РЅРµРґРѕСЃС‚СѓРїРЅРѕ');
                return;
            }
            title.textContent = `РЎС‚Р°С‚РёСЃС‚РёРєР°: ${sourceId}`;
            summary.textContent = 'Р—Р°РіСЂСѓР·РєР°...';
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
                        summary.textContent = data.message || 'РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё СЃС‚Р°С‚РёСЃС‚РёРєРё';
                        return;
                    }
                    const stats = data.stats || {};
                    summary.innerHTML = `
                        РџРµСЂРёРѕРґ: ${data.period_days} РґРЅ. вЂў Р’СЃРµРіРѕ: ${stats.total || 0}
                        вЂў РџРѕР»СѓС‡РµРЅРѕ вњ… ${stats.receive_success || 0} / вќЊ ${stats.receive_error || 0}
                        вЂў РћР±СЂР°Р±РѕС‚РєР° вњ… ${stats.processing_success || 0} / вќЊ ${stats.processing_error || 0}
                        вЂў Р’С‹РіСЂСѓР·РєР° вњ… ${stats.transfer_success || 0} / вќЊ ${stats.transfer_error || 0}
                    `;
                    const entries = data.entries || [];
                    if (!entries.length) {
                        entriesContainer.innerHTML = '<div class="stat-item">РќРµС‚ Р·Р°РїРёСЃРµР№ Р·Р° РїРµСЂРёРѕРґ.</div>';
                        return;
                    }
                    entriesContainer.innerHTML = entries.map(entry => `
                        <div class="modal-item">
                            <div class="server-details">${entry.timestamp || 'вЂ”'}</div>
                            <div class="status-flags">
                                <div class="status-flag">${entry.receive.icon} РџРѕР»СѓС‡РµРЅРёРµ</div>
                                <div class="status-flag">${entry.processing.icon} РћР±СЂР°Р±РѕС‚РєР°</div>
                                <div class="status-flag">${entry.transfer.icon} Р’С‹РіСЂСѓР·РєР°</div>
                            </div>
                            ${entry.error ? `<div class="server-details">РћС€РёР±РєР°: ${entry.error}</div>` : ''}
                        </div>
                    `).join('');
                })
                .catch(error => {
                    summary.textContent = `РћС€РёР±РєР°: ${error}`;
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
        if STATS_FILE.exists():
            stats_data = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        
        # РџРѕР»СѓС‡Р°РµРј С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ СЃРµСЂРІРµСЂРѕРІ
        from core.monitor_core import get_current_server_status, monitoring_active, last_check_time
        from core.monitor_core import is_silent_time, resource_history
        from extensions.server_checks import initialize_servers
        
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
        from config.db_settings import CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL
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
    """Р”РѕСЃС‚Р°С‘С‚ username/password РёР· JSON РёР»Рё form payload."""
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

    # Bootstrap token СЂР°Р·СЂРµС€РµРЅ С‚РѕР»СЊРєРѕ РґР»СЏ РѕР±РјРµРЅР° РЅР° СЂР°Р±РѕС‡РёР№ session token.
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
        return True, "РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРёРѕСЃС‚Р°РЅРѕРІР»РµРЅ", "applied"

    if action == "resume_monitoring":
        monitor_core.monitoring_active = True
        return True, "РњРѕРЅРёС‚РѕСЂРёРЅРі РІРѕР·РѕР±РЅРѕРІР»РµРЅ", "applied"

    if action == "send_morning_report":
        from modules.morning_report import morning_report
        report_text = morning_report.force_report()
        return True, report_text, "accepted"

    if action == "force_quiet":
        monitor_core.set_silent_override(True)
        return True, "РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РІРєР»СЋС‡РµРЅ С‚РёС…РёР№ СЂРµР¶РёРј", "applied"

    if action == "force_loud":
        monitor_core.set_silent_override(False)
        return True, "РџСЂРёРЅСѓРґРёС‚РµР»СЊРЅРѕ РІРєР»СЋС‡РµРЅ РіСЂРѕРјРєРёР№ СЂРµР¶РёРј", "applied"

    if action == "auto_mode":
        monitor_core.set_silent_override(None)
        return True, "Р’РєР»СЋС‡РµРЅ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ СЂРµР¶РёРј quiet/loud", "applied"

    return False, f"Unsupported action: {action}", "failed"


@app.route('/v1/auth/token', methods=['POST'])
@app.route('/v1/auth/login', methods=['POST'])
@app.route('/api/v1/auth/token', methods=['POST'])
@app.route('/api/v1/auth/login', methods=['POST'])
@app.route('/auth/token', methods=['POST'])
@app.route('/auth/login', methods=['POST'])
@app.route('/token', methods=['POST'])
def mobile_auth_token():
    """Auth endpoint: bootstrap-token -> session token (DB), fallback РЅР° legacy username/password."""
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
            "message": "РўСЂРµР±СѓРµС‚СЃСЏ Authorization: Bearer <MOBILE_DEFAULT_TOKEN> РёР»Рё username/login/email + password"
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
    """РЇРІРЅС‹Р№ РїРµСЂРµРІС‹РїСѓСЃРє С‚РѕРєРµРЅР° РїРѕ bootstrap token (РЅР°РїСЂРёРјРµСЂ, РїРѕСЃР»Рµ РїРµСЂРµСѓСЃС‚Р°РЅРѕРІРєРё РїСЂРёР»РѕР¶РµРЅРёСЏ)."""
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
    """Mobile BFF endpoint СЃРѕРІРјРµСЃС‚РёРјС‹Р№ СЃ auth_token_probe.sh"""
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
    """РЎРёРЅРѕРЅРёРј РґР»СЏ Р±С‹СЃС‚СЂРѕР№ РїСЂРѕРІРµСЂРєРё СЃС‚Р°С‚СѓСЃР° СЃ Bearer С‚РѕРєРµРЅРѕРј."""
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
    """Р’РѕР·РІСЂР°С‰Р°РµС‚ РјР°СЃРєРёСЂРѕРІР°РЅРЅРѕРµ Р·РЅР°С‡РµРЅРёРµ СЃРµРєСЂРµС‚Р° Р±РµР· СЂР°СЃРєСЂС‹С‚РёСЏ РёСЃС…РѕРґРЅРѕР№ СЃС‚СЂРѕРєРё."""
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

    # Р’ Р‘Р” С‚РёРї СЃСѓС‰РµСЃС‚РІСѓРµС‚ С‚РѕР»СЊРєРѕ С‡РµСЂРµР· СѓС‡РµС‚РЅС‹Рµ Р·Р°РїРёСЃРё: СЃРѕР·РґР°РµРј Рё СЃСЂР°Р·Сѓ РѕС‚РєР»СЋС‡Р°РµРј С‚РµС…. Р·Р°РїРёСЃСЊ.
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
            settings_manager.set_setting('CHECK_INTERVAL', check_interval, 'monitoring', 'РРЅС‚РµСЂРІР°Р» РїСЂРѕРІРµСЂРєРё СЃРµСЂРІРµСЂРѕРІ (СЃРµРєСѓРЅРґС‹)', 'int')
        else:
            check_interval = settings_manager.get_setting('CHECK_INTERVAL', 60)

        if max_downtime is not None:
            max_downtime = int(max_downtime)
            if max_downtime < 30:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "max_downtime_sec must be >= 30", "request_id": request_id}}), 400
            settings_manager.set_setting('MAX_FAIL_TIME', max_downtime, 'monitoring', 'РњР°РєСЃРёРјР°Р»СЊРЅРѕРµ РІСЂРµРјСЏ РїСЂРѕСЃС‚РѕСЏ РґРѕ Р°Р»РµСЂС‚Р° (СЃРµРєСѓРЅРґС‹)', 'int')
        else:
            max_downtime = settings_manager.get_setting('MAX_FAIL_TIME', 900)

        if timeout_sec is not None:
            timeout_sec = int(timeout_sec)
            if timeout_sec < 1:
                return jsonify({"error": {"code": "INVALID_THRESHOLD", "message": "timeout_sec must be >= 1", "request_id": request_id}}), 400
            settings_manager.set_setting('API_TIMEOUT_SEC', timeout_sec, 'monitoring', 'РўР°Р№РјР°СѓС‚ API (СЃРµРєСѓРЅРґС‹)', 'int')
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
    """Р“Р»Р°РІРЅР°СЏ СЃС‚СЂР°РЅРёС†Р° РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°"""
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
                "schedule_status": "рџџў Р’РєР»СЋС‡РµРЅРѕ" if schedule.get("enabled") else "рџ”ґ Р’С‹РєР»СЋС‡РµРЅРѕ",
                "schedule_time": schedule_time or "РЅРµ Р·Р°РґР°РЅРѕ",
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
        return f"вќЊ РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё РІРµР±-РёРЅС‚РµСЂС„РµР№СЃР°: {e}"

@app.route('/api/run_check')
def api_run_check():
    """API РґР»СЏ Р·Р°РїСѓСЃРєР° РїСЂРѕРІРµСЂРѕРє"""
    check_type = request.args.get('type', 'quick')
    
    try:
        if check_type == 'quick':
            # Р—Р°РїСѓСЃРє Р±С‹СЃС‚СЂРѕР№ РїСЂРѕРІРµСЂРєРё РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё
            from core.monitor_core import get_current_server_status
            status = get_current_server_status()
            message = f"вњ… Р‘С‹СЃС‚СЂР°СЏ РїСЂРѕРІРµСЂРєР° РІС‹РїРѕР»РЅРµРЅР°: {len(status['ok'])} РґРѕСЃС‚СѓРїРЅРѕ, {len(status['failed'])} РЅРµРґРѕСЃС‚СѓРїРЅРѕ"
            
        elif check_type == 'resources':
            # Р—Р°РїСѓСЃРє РїСЂРѕРІРµСЂРєРё СЂРµСЃСѓСЂСЃРѕРІ
            from core.monitor_core import check_resources_automatically
            check_resources_automatically()
            message = "вњ… РџСЂРѕРІРµСЂРєР° СЂРµСЃСѓСЂСЃРѕРІ РІС‹РїРѕР»РЅРµРЅР°. Р”Р°РЅРЅС‹Рµ РѕР±РЅРѕРІСЏС‚СЃСЏ С‡РµСЂРµР· 1-2 РјРёРЅСѓС‚С‹."
            
        elif check_type == 'report':
            # Р¤РѕСЂРјРёСЂРѕРІР°РЅРёРµ РѕС‚С‡РµС‚Р°
            from core.monitor_core import send_morning_report
            send_morning_report()
            message = "вњ… РћС‚С‡РµС‚ СЃС„РѕСЂРјРёСЂРѕРІР°РЅ Рё РѕС‚РїСЂР°РІР»РµРЅ РІ Telegram"
            
        else:
            message = "вќЊ РќРµРёР·РІРµСЃС‚РЅС‹Р№ С‚РёРї РїСЂРѕРІРµСЂРєРё"
            
        return jsonify({"success": True, "message": message, "reload": check_type != 'resources'})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"вќЊ РћС€РёР±РєР°: {str(e)}"})

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
    """API РґР»СЏ Р·Р°РїСѓСЃРєР° Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "рџ“¦ РњРѕРґСѓР»СЊ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ РѕС‚РєР»СЋС‡РµРЅ"})

    def _run():
        run_supplier_stock_fetch()

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "message": "вњ… Р—Р°РіСЂСѓР·РєР° РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ Р·Р°РїСѓС‰РµРЅР°"})

@app.route('/api/supplier_stock/schedule', methods=['GET', 'POST'])
def api_supplier_stock_schedule():
    """API РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ СЂР°СЃРїРёСЃР°РЅРёРµРј Р·Р°РіСЂСѓР·РєРё РѕСЃС‚Р°С‚РєРѕРІ."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "рџ“¦ РњРѕРґСѓР»СЊ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ РѕС‚РєР»СЋС‡РµРЅ"})

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
                "message": "вќЊ РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ РІСЂРµРјРµРЅРё. РСЃРїРѕР»СЊР·СѓР№С‚Рµ HH:MM, СЂР°Р·РґРµР»РёС‚РµР»Рё: РїСЂРѕР±РµР», Р·Р°РїСЏС‚Р°СЏ РёР»Рё ;",
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

    return jsonify({"success": True, "message": "вњ… Р Р°СЃРїРёСЃР°РЅРёРµ РѕР±РЅРѕРІР»РµРЅРѕ", "schedule": schedule})

@app.route('/api/supplier_stock/reports')
def api_supplier_stock_reports():
    """API РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ РѕС‚С‡РµС‚РѕРІ РїРѕ РѕСЃС‚Р°С‚РєР°Рј РїРѕСЃС‚Р°РІС‰РёРєРѕРІ."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "рџ“¦ РњРѕРґСѓР»СЊ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ РѕС‚РєР»СЋС‡РµРЅ"})

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
    """API РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ РґРµС‚Р°Р»СЊРЅРѕР№ СЃС‚Р°С‚РёСЃС‚РёРєРё РїРѕ РёСЃС‚РѕС‡РЅРёРєСѓ РѕСЃС‚Р°С‚РєРѕРІ."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "рџ“¦ РњРѕРґСѓР»СЊ РѕСЃС‚Р°С‚РєРѕРІ РїРѕСЃС‚Р°РІС‰РёРєРѕРІ РѕС‚РєР»СЋС‡РµРЅ"})

    source_id = request.args.get("source_id")
    source_kind = request.args.get("source_kind")
    if not source_id:
        return jsonify({"success": False, "message": "вќЊ РќРµ СѓРєР°Р·Р°РЅ РёСЃС‚РѕС‡РЅРёРє"})
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
        from extensions.server_checks import initialize_servers
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
        if extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
            start_supplier_stock_scheduler()
        app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"вќЊ РћС€РёР±РєР° Р·Р°РїСѓСЃРєР° РІРµР±-СЃРµСЂРІРµСЂР°: {e}")

if __name__ == "__main__":
    start_web_server()
