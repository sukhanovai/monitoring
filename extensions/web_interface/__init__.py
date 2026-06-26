"""
/extensions/web_interface/__init__.py
Server Monitoring System v8.63.25
Copyright (c) 2025 Aleksandr Sukhanov
License: MIT
Web interface
Система мониторинга серверов
Версия: 8.63.25
Автор: Александр Суханов (c)
Лицензия: MIT
Веб-интерфейс
"""

import ast
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from urllib.parse import quote, unquote

from flask import Flask, jsonify, request

from config.db_settings import WEB_HOST, WEB_PORT
from config.settings import STATS_FILE
from extensions.extension_manager import extension_manager
from extensions.server_checks import check_server_availability, initialize_servers
from extensions.supplier_stock_files import (
    SUPPLIER_STOCK_EXTENSION_ID,
    build_supplier_stock_dashboard,
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

app = Flask(__name__)

# Современный SPA веб-интерфейс (использует тот же v1 BFF API, что и Android-клиент)
WEB_APP_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🌐 Мониторинг серверов</title>
<style>
:root{
  --bg:#0e1525; --bg2:#131c30; --panel:#172139; --panel2:#1d2a47;
  --border:#26334f; --border2:#33456a;
  --text:#e7edf7; --muted:#93a2bd; --faint:#64748b;
  --accent:#4f8cff; --accent2:#3b6fe0;
  --ok:#34d399; --warn:#fbbf24; --crit:#f87171; --info:#60a5fa;
  --radius:14px; --shadow:0 10px 30px rgba(0,0,0,.35);
  --font:'Segoe UI',Roboto,Tahoma,system-ui,sans-serif;
}
[data-theme="light"]{
  --bg:#eef2f8; --bg2:#e6ecf5; --panel:#ffffff; --panel2:#f3f6fb;
  --border:#d8e0ee; --border2:#c3cfe4;
  --text:#11203a; --muted:#5a6b88; --faint:#8493ad;
  --shadow:0 10px 28px rgba(20,40,80,.12);
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{font-family:var(--font);background:
  radial-gradient(1200px 600px at 80% -10%,rgba(79,140,255,.10),transparent 60%),
  radial-gradient(1000px 500px at -10% 110%,rgba(52,211,153,.08),transparent 55%),
  var(--bg);color:var(--text);min-height:100vh;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
button{font-family:inherit}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:8px}
::-webkit-scrollbar-track{background:transparent}

/* App shell */
.app{display:flex;min-height:100vh}
.sidebar{width:248px;flex:0 0 248px;background:linear-gradient(180deg,var(--bg2),var(--bg));
  border-right:1px solid var(--border);padding:18px 14px;position:sticky;top:0;height:100vh;
  display:flex;flex-direction:column;gap:6px;z-index:30}
.brand{display:flex;align-items:center;gap:10px;padding:8px 10px 16px;font-weight:700;font-size:1.12em}
.brand .logo{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,var(--accent),#7b5cff);
  display:grid;place-items:center;font-size:18px;box-shadow:0 6px 16px rgba(79,140,255,.4)}
.brand small{display:block;font-weight:500;color:var(--muted);font-size:.62em;letter-spacing:.5px}
.nav{display:flex;flex-direction:column;gap:4px;margin-top:4px}
.nav button{display:flex;align-items:center;gap:12px;width:100%;text-align:left;
  background:transparent;border:1px solid transparent;color:var(--muted);
  padding:11px 13px;border-radius:11px;font-size:.96em;cursor:pointer;transition:.15s}
.nav button .ico{font-size:1.15em;width:22px;text-align:center}
.nav button:hover{background:var(--panel);color:var(--text)}
.nav button.active{background:linear-gradient(135deg,rgba(79,140,255,.18),rgba(79,140,255,.05));
  color:var(--text);border-color:var(--border2);font-weight:600}
.nav button.active .ico{filter:drop-shadow(0 0 6px rgba(79,140,255,.6))}
.side-foot{margin-top:auto;display:flex;flex-direction:column;gap:8px;padding-top:12px;border-top:1px solid var(--border)}
.side-foot .row{display:flex;gap:8px}
.icobtn{flex:1;background:var(--panel);border:1px solid var(--border);color:var(--muted);
  padding:9px;border-radius:10px;cursor:pointer;font-size:.85em;transition:.15s}
.icobtn:hover{color:var(--text);border-color:var(--border2)}
.ver{font-size:.72em;color:var(--faint);text-align:center}

.main{flex:1;min-width:0;display:flex;flex-direction:column}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;
  padding:14px 26px;background:color-mix(in srgb,var(--bg) 82%,transparent);
  backdrop-filter:blur(12px);border-bottom:1px solid var(--border)}
.topbar h1{font-size:1.28em;font-weight:700;margin-right:auto}
.topbar .sub{color:var(--muted);font-weight:400;font-size:.62em;display:block}
.pill{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border-radius:999px;
  font-size:.82em;font-weight:600;border:1px solid var(--border);background:var(--panel)}
.pill .dot{width:9px;height:9px;border-radius:50%;background:var(--muted)}
.pill.ok .dot{background:var(--ok);box-shadow:0 0 8px var(--ok)}
.pill.crit .dot{background:var(--crit);box-shadow:0 0 8px var(--crit)}
.pill.warn .dot{background:var(--warn);box-shadow:0 0 8px var(--warn)}
.pill.clk{cursor:pointer;transition:.15s}.pill.clk:hover{border-color:var(--border2)}

.content{padding:24px 26px 80px;max-width:1320px;width:100%;margin:0 auto}
.view{display:none;animation:fade .25s ease}
.view.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

/* Cards & grid */
.grid{display:grid;gap:16px}
.cards{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
.card{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--border);
  border-radius:var(--radius);padding:18px;box-shadow:var(--shadow)}
.card.section{padding:0;overflow:hidden}
.card .head{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid var(--border);
  font-weight:700;font-size:1.02em}
.card .head .ico{font-size:1.2em}
.card .head .sp{margin-left:auto;display:flex;gap:8px}
.card .body{padding:18px}
.stat{display:flex;flex-direction:column;gap:6px}
.stat .lbl{color:var(--muted);font-size:.82em;display:flex;align-items:center;gap:7px}
.stat .val{font-size:2.1em;font-weight:800;line-height:1}
.stat .val.sm{font-size:1.3em}
.tone-ok{color:var(--ok)}.tone-crit{color:var(--crit)}.tone-warn{color:var(--warn)}.tone-info{color:var(--info)}
.section-title{display:flex;align-items:center;gap:10px;margin:26px 0 14px;font-size:1.05em;font-weight:700;color:var(--text)}
.section-title:first-child{margin-top:4px}
.section-title .ln{flex:1;height:1px;background:var(--border)}

/* Server list */
.srv{display:flex;align-items:center;gap:14px;padding:13px 16px;border:1px solid var(--border);
  border-radius:12px;background:var(--panel);margin-bottom:10px;transition:.15s;flex-wrap:wrap}
.srv:hover{border-color:var(--border2)}
.srv .st{width:11px;height:11px;border-radius:50%;flex:0 0 auto}
.st.up{background:var(--ok);box-shadow:0 0 10px var(--ok)}
.st.down{background:var(--crit);box-shadow:0 0 10px var(--crit)}
.st.unknown{background:var(--muted)}
.srv .nm{font-weight:600}
.srv .ip{color:var(--muted);font-size:.86em}
.srv .meta{margin-left:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.tag{font-size:.74em;padding:3px 9px;border-radius:999px;background:var(--panel2);
  border:1px solid var(--border);color:var(--muted)}
.tag.t-up{color:var(--ok);border-color:rgba(52,211,153,.4)}
.tag.t-down{color:var(--crit);border-color:rgba(248,113,113,.4)}
.tag.t-off{color:var(--faint)}
.res{display:flex;gap:14px;flex-wrap:wrap;width:100%;margin-top:6px}
.res .m{flex:1;min-width:120px}
.res .m .top{display:flex;justify-content:space-between;font-size:.78em;color:var(--muted);margin-bottom:4px}
.bar{height:7px;border-radius:6px;background:var(--bg2);overflow:hidden}
.bar > i{display:block;height:100%;border-radius:6px;background:var(--ok);transition:width .4s}
.bar > i.warn{background:var(--warn)}.bar > i.crit{background:var(--crit)}

/* Forms */
.field{margin-bottom:15px}
.field label{display:block;font-size:.85em;color:var(--muted);margin-bottom:6px;font-weight:500}
.field .hint{font-size:.76em;color:var(--faint);margin-top:5px}
input,select,textarea{width:100%;background:var(--bg2);border:1px solid var(--border);color:var(--text);
  padding:11px 13px;border-radius:10px;font-size:.94em;font-family:inherit;transition:.15s}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(79,140,255,.18)}
input::placeholder{color:var(--faint)}
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0 18px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border:none;
  padding:11px 18px;border-radius:10px;font-size:.92em;font-weight:600;cursor:pointer;transition:.15s}
.btn:hover{filter:brightness(1.08);transform:translateY(-1px)}
.btn:active{transform:none}
.btn.ghost{background:var(--panel);color:var(--text);border:1px solid var(--border)}
.btn.ghost:hover{border-color:var(--border2);filter:none}
.btn.ok{background:linear-gradient(135deg,#34d399,#10b981)}
.btn.warn{background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#3a2a00}
.btn.crit{background:linear-gradient(135deg,#fb7185,#ef4444)}
.btn.sm{padding:7px 12px;font-size:.82em}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none;filter:none}
.btnrow{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}

/* Toggle */
.switch{position:relative;display:inline-block;width:46px;height:26px;flex:0 0 auto}
.switch input{opacity:0;width:0;height:0}
.switch .sl{position:absolute;inset:0;background:var(--border2);border-radius:999px;cursor:pointer;transition:.2s}
.switch .sl:before{content:"";position:absolute;width:20px;height:20px;left:3px;top:3px;background:#fff;
  border-radius:50%;transition:.2s}
.switch input:checked + .sl{background:linear-gradient(135deg,var(--accent),var(--accent2))}
.switch input:checked + .sl:before{transform:translateX(20px)}
.toggle-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.toggle-row:last-child{border-bottom:none}
.toggle-row .tx{flex:1}.toggle-row .tx b{font-weight:600}
.toggle-row .tx small{display:block;color:var(--muted);font-size:.82em;margin-top:2px}

/* Action grid */
.ops{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:13px}
.op{display:flex;align-items:center;gap:13px;padding:16px;border:1px solid var(--border);border-radius:13px;
  background:linear-gradient(180deg,var(--panel),var(--panel2));cursor:pointer;transition:.15s;text-align:left}
.op:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:var(--shadow)}
.op .e{font-size:1.7em}.op .t b{display:block;font-weight:600}.op .t small{color:var(--muted);font-size:.8em}

/* Chips */
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border-radius:999px;
  background:var(--panel2);border:1px solid var(--border);font-size:.86em;cursor:pointer;transition:.15s}
.chip:hover{border-color:var(--border2)}
.chip.on{background:linear-gradient(135deg,rgba(79,140,255,.22),rgba(79,140,255,.08));
  border-color:var(--accent);color:var(--text);font-weight:600}
.chip .x{color:var(--crit);font-weight:700}

/* Modal */
.modal-bg{position:fixed;inset:0;background:rgba(5,10,20,.66);backdrop-filter:blur(4px);
  display:none;align-items:center;justify-content:center;z-index:100;padding:20px}
.modal-bg.show{display:flex}
.modal{background:linear-gradient(180deg,var(--panel),var(--panel2));border:1px solid var(--border2);
  border-radius:16px;width:100%;max-width:560px;max-height:88vh;overflow:auto;box-shadow:var(--shadow)}
.modal h3{padding:18px 20px;border-bottom:1px solid var(--border);font-size:1.1em;display:flex;align-items:center;gap:10px}
.modal h3 .cl{margin-left:auto;cursor:pointer;color:var(--muted);font-size:1.2em;background:none;border:none}
.modal .mb{padding:20px}
.modal pre{white-space:pre-wrap;word-break:break-word;font-family:'SF Mono',Consolas,monospace;
  font-size:.86em;line-height:1.5;color:var(--text);background:var(--bg2);padding:14px;border-radius:10px;
  border:1px solid var(--border);max-height:50vh;overflow:auto}

/* Toast */
.toasts{position:fixed;right:20px;bottom:20px;z-index:200;display:flex;flex-direction:column;gap:10px;max-width:380px}
.toast{background:var(--panel);border:1px solid var(--border2);border-left:4px solid var(--accent);
  padding:13px 16px;border-radius:11px;box-shadow:var(--shadow);font-size:.9em;animation:slidein .25s}
.toast.ok{border-left-color:var(--ok)}.toast.err{border-left-color:var(--crit)}.toast.warn{border-left-color:var(--warn)}
@keyframes slidein{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:none}}

/* Login */
.login{position:fixed;inset:0;display:grid;place-items:center;padding:20px;z-index:300;
  background:radial-gradient(900px 500px at 50% -10%,rgba(79,140,255,.16),transparent 60%),var(--bg)}
.login .box{width:100%;max-width:400px;background:linear-gradient(180deg,var(--panel),var(--panel2));
  border:1px solid var(--border2);border-radius:18px;padding:32px;box-shadow:var(--shadow)}
.login .logo-lg{width:60px;height:60px;border-radius:16px;background:linear-gradient(135deg,var(--accent),#7b5cff);
  display:grid;place-items:center;font-size:30px;margin:0 auto 18px;box-shadow:0 10px 28px rgba(79,140,255,.45)}
.login h2{text-align:center;margin-bottom:4px}
.login p.s{text-align:center;color:var(--muted);font-size:.88em;margin-bottom:24px}

.empty{text-align:center;padding:40px 20px;color:var(--muted)}
.empty .e{font-size:2.6em;display:block;margin-bottom:10px;opacity:.6}
.spinner{width:34px;height:34px;border:3px solid var(--border);border-top-color:var(--accent);
  border-radius:50%;animation:spin 1s linear infinite;margin:24px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.skel{background:linear-gradient(90deg,var(--panel) 25%,var(--panel2) 50%,var(--panel) 75%);
  background-size:200% 100%;animation:sk 1.3s infinite;border-radius:10px;height:64px;margin-bottom:10px}
@keyframes sk{to{background-position:-200% 0}}

.hamb{display:none;background:var(--panel);border:1px solid var(--border);color:var(--text);
  width:40px;height:40px;border-radius:10px;font-size:1.2em;cursor:pointer}
.mask{display:none}

@media(max-width:860px){
  .sidebar{position:fixed;left:0;top:0;transform:translateX(-100%);transition:transform .25s;box-shadow:var(--shadow)}
  .sidebar.open{transform:none}
  .mask{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:25}
  .mask.show{display:block}
  .hamb{display:grid;place-items:center}
  .content{padding:18px 16px 80px}
  .topbar{padding:12px 16px}
  .topbar h1{font-size:1.1em}
  .pill.hide-sm{display:none}
}
</style>
</head>
<body>

<!-- LOGIN -->
<div class="login" id="login">
  <div class="box">
    <div class="logo-lg">🛡️</div>
    <h2>Мониторинг серверов</h2>
    <p class="s">Войдите для доступа к панели управления</p>
    <form id="loginForm">
      <div class="field"><label>Логин</label><input id="lgUser" autocomplete="username" placeholder="admin" required></div>
      <div class="field"><label>Пароль</label><input id="lgPass" type="password" autocomplete="current-password" placeholder="••••••••" required></div>
      <div id="lgErr" style="color:var(--crit);font-size:.85em;margin-bottom:12px;display:none"></div>
      <button class="btn" style="width:100%" type="submit" id="lgBtn">Войти</button>
    </form>
  </div>
</div>

<!-- APP -->
<div class="app" id="app" style="display:none">
  <div class="mask" id="mask" onclick="toggleSidebar(false)"></div>
  <aside class="sidebar" id="sidebar">
    <div class="brand"><span class="logo">🛡️</span><div>Мониторинг<small>SERVER CONTROL</small></div></div>
    <nav class="nav" id="nav"></nav>
    <div class="side-foot">
      <div class="row">
        <button class="icobtn" onclick="toggleTheme()" id="themeBtn">🌙 Тема</button>
        <button class="icobtn" onclick="logout()">🚪 Выход</button>
      </div>
      <div class="ver" id="verLabel">v—</div>
    </div>
  </aside>

  <div class="main">
    <header class="topbar">
      <button class="hamb" onclick="toggleSidebar()">☰</button>
      <h1 id="viewTitle">Дашборд<span class="sub" id="viewSub">Состояние инфраструктуры</span></h1>
      <span class="pill clk hide-sm" id="pillMon" onclick="go('dashboard')"><span class="dot"></span><span>—</span></span>
      <span class="pill clk hide-sm" id="pillSilent" onclick="go('dashboard')"><span class="dot"></span><span>—</span></span>
    </header>
    <div class="content">
      <section class="view active" id="view-dashboard"></section>
      <section class="view" id="view-servers"></section>
      <section class="view" id="view-settings"></section>
      <section class="view" id="view-operations"></section>
      <section class="view" id="view-about"></section>
    </div>
  </div>
</div>

<div class="modal-bg" id="modalBg"><div class="modal" id="modal"></div></div>
<div class="toasts" id="toasts"></div>

<script>
//==================== Core helpers ====================
var TOKEN = localStorage.getItem('mon_token') || '';
var APP_VERSION = '__APP_VERSION__';
var state = { availability:null, control:null, resources:{}, view:'dashboard' };

function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}

function toast(msg,kind){
  var t=document.createElement('div');t.className='toast '+(kind||'');
  t.innerHTML=esc(msg);$('toasts').appendChild(t);
  setTimeout(function(){t.style.opacity='0';t.style.transform='translateX(30px)';
    setTimeout(function(){t.remove();},250);},kind==='err'?5200:3200);
}

async function api(path,opts){
  opts=opts||{};
  var headers=Object.assign({'Content-Type':'application/json'},opts.headers||{});
  if(TOKEN) headers['Authorization']='Bearer '+TOKEN;
  var res;
  try{
    res=await fetch(path,{method:opts.method||'GET',headers:headers,
      body:opts.body?JSON.stringify(opts.body):undefined});
  }catch(e){ throw new Error('Сеть недоступна: '+e.message); }
  var data=null; try{ data=await res.json(); }catch(e){}
  if(res.status===401){ doLogout(true); throw new Error('Сессия истекла'); }
  if(!res.ok){
    var m=(data&&(data.message||(data.error&&(data.error.message||data.error))))||('HTTP '+res.status);
    throw new Error(typeof m==='string'?m:JSON.stringify(m));
  }
  return data||{};
}

//==================== Auth ====================
async function login(u,p){
  var res=await fetch('/v1/auth/token',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:u,password:p})});
  var data=await res.json().catch(function(){return {};});
  if(!res.ok||!data.access_token) throw new Error(data.message||'Неверные учётные данные');
  TOKEN=data.access_token; localStorage.setItem('mon_token',TOKEN);
}
function doLogout(silent){
  TOKEN='';localStorage.removeItem('mon_token');
  $('app').style.display='none';$('login').style.display='grid';
  if(!silent) toast('Вы вышли из системы');
}
function logout(){ doLogout(false); }

$('loginForm').addEventListener('submit',async function(e){
  e.preventDefault();
  var btn=$('lgBtn');btn.disabled=true;btn.textContent='Вход…';$('lgErr').style.display='none';
  try{
    await login($('lgUser').value.trim(),$('lgPass').value);
    await boot();
  }catch(err){
    $('lgErr').textContent=err.message;$('lgErr').style.display='block';
  }finally{ btn.disabled=false;btn.textContent='Войти'; }
});

//==================== Navigation ====================
var NAV=[
  {id:'dashboard',ico:'📊',label:'Дашборд',sub:'Состояние инфраструктуры'},
  {id:'servers',ico:'🖥️',label:'Серверы',sub:'Управление серверами'},
  {id:'settings',ico:'⚙️',label:'Настройки',sub:'Параметры системы'},
  {id:'operations',ico:'🧰',label:'Операции',sub:'Бэкапы, ZFS, TLS, отчёты'},
  {id:'about',ico:'ℹ️',label:'О программе',sub:'Информация и версия'},
];
function buildNav(){
  $('nav').innerHTML=NAV.map(function(n){
    return '<button data-id="'+n.id+'" onclick="go(\''+n.id+'\')"><span class="ico">'+n.ico+'</span>'+n.label+'</button>';
  }).join('');
}
function go(id){
  state.view=id;
  document.querySelectorAll('.nav button').forEach(function(b){b.classList.toggle('active',b.dataset.id===id);});
  document.querySelectorAll('.view').forEach(function(v){v.classList.remove('active');});
  $('view-'+id).classList.add('active');
  var meta=NAV.find(function(n){return n.id===id;});
  $('viewTitle').firstChild.textContent=meta.label;$('viewSub').textContent=meta.sub;
  toggleSidebar(false);
  if(id==='dashboard') renderDashboard();
  if(id==='servers') renderServers();
  if(id==='settings') renderSettings();
  if(id==='operations') renderOperations();
  if(id==='about') renderAbout();
}
function toggleSidebar(force){
  var sb=$('sidebar'),mk=$('mask');
  var open=force===undefined?!sb.classList.contains('open'):force;
  sb.classList.toggle('open',open);mk.classList.toggle('show',open);
}

//==================== Theme ====================
function applyTheme(t){
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('mon_theme',t);
  $('themeBtn').textContent=(t==='light'?'🌙 Тёмная':'☀️ Светлая');
}
function toggleTheme(){
  applyTheme(document.documentElement.getAttribute('data-theme')==='light'?'dark':'light');
}

//==================== Modal ====================
function modal(title,html){
  $('modal').innerHTML='<h3>'+title+'<button class="cl" onclick="closeModal()">✕</button></h3><div class="mb">'+html+'</div>';
  $('modalBg').classList.add('show');
}
function closeModal(){ $('modalBg').classList.remove('show'); }
$('modalBg').addEventListener('click',function(e){ if(e.target===$('modalBg')) closeModal(); });

//==================== Dashboard ====================
function toneForPct(v){ if(v>=90)return'crit'; if(v>=75)return'warn'; return'ok'; }
async function renderDashboard(){
  var el=$('view-dashboard');
  if(!state.availability) el.innerHTML='<div class="grid cards"><div class="skel"></div><div class="skel"></div><div class="skel"></div><div class="skel"></div></div>';
  try{
    var av=await api('/v1/monitoring/availability?scope=all');
    var ctrl=await api('/v1/control/status');
    state.availability=av;state.control=ctrl;updatePills();
    var items=av.items||[];
    var up=av.up!=null?av.up:(av.summary&&av.summary.up)||0;
    var down=av.down!=null?av.down:(av.summary&&av.summary.down)||0;
    var total=av.total!=null?av.total:items.length;
    var mon=ctrl.monitoring_active;
    var silent=ctrl.silent_mode||(ctrl.silent_active?'force_quiet':'auto');
    var silentLabel={auto:'Авто',force_quiet:'Тихий режим',force_loud:'Громкий режим'}[silent]||silent;

    var cards=
      statCard('🖥️','Всего серверов',total,'info')+
      statCard('🟢','Доступно',up,'ok')+
      statCard('🔴','Недоступно',down,down>0?'crit':'ok')+
      statCard(mon?'▶️':'⏸️','Мониторинг',mon?'Активен':'Пауза',mon?'ok':'warn',true);

    var ctrlCard=
      '<div class="card section"><div class="head"><span class="ico">🎛️</span>Управление мониторингом</div><div class="body">'+
      '<div class="btnrow">'+
        (mon
          ?'<button class="btn warn" onclick="ctrlAction(\'pause_monitoring\',\'Мониторинг приостановлен\')">⏸️ Приостановить</button>'
          :'<button class="btn ok" onclick="ctrlAction(\'resume_monitoring\',\'Мониторинг возобновлён\')">▶️ Возобновить</button>')+
        '<button class="btn" onclick="ctrlAction(\'send_morning_report\',null)">📋 Утренний отчёт</button>'+
      '</div>'+
      '<div class="section-title" style="margin:18px 0 12px;font-size:.92em"><span>Режим уведомлений</span><span class="ln"></span></div>'+
      '<div class="chips">'+
        silentChip('auto','🔄 Авто',silent)+
        silentChip('force_loud','🔔 Громкий',silent)+
        silentChip('force_quiet','🔕 Тихий',silent)+
      '</div>'+
      '<div class="field hint" style="margin-top:10px">Текущий режим: <b>'+esc(silentLabel)+'</b>'+(ctrl.silent_active?' · сейчас активна тишина':'')+'</div>'+
      '</div></div>';

    var listHtml=items.length?items.map(serverRow).join(''):
      '<div class="empty"><span class="e">🗂️</span>Серверы не настроены</div>';

    el.innerHTML=
      '<div class="grid cards">'+cards+'</div>'+
      '<div class="section-title"><span>🎛️ Управление</span><span class="ln"></span></div>'+
      ctrlCard+
      '<div class="section-title"><span>🖥️ Серверы ('+items.length+')</span><span class="ln"></span>'+
        '<button class="btn ghost sm" onclick="renderDashboard()">🔄 Обновить</button></div>'+
      '<div id="srvList">'+listHtml+'</div>';
  }catch(e){
    el.innerHTML='<div class="card"><div class="body empty"><span class="e">⚠️</span>'+esc(e.message)+
      '<div style="margin-top:14px"><button class="btn" onclick="renderDashboard()">Повторить</button></div></div></div>';
  }
}
function statCard(ico,lbl,val,tone,sm){
  return '<div class="card"><div class="stat"><span class="lbl">'+ico+' '+esc(lbl)+'</span>'+
    '<span class="val '+(sm?'sm ':'')+'tone-'+tone+'">'+esc(val)+'</span></div></div>';
}
function silentChip(mode,label,cur){
  var act={auto:'auto_mode',force_loud:'force_loud',force_quiet:'force_quiet'}[mode];
  var msg={auto:'Автоматический режим',force_loud:'Включён громкий режим',force_quiet:'Включён тихий режим'}[mode];
  return '<span class="chip'+(cur===mode?' on':'')+'" onclick="ctrlAction(\''+act+'\',\''+msg+'\')">'+label+'</span>';
}
function serverRow(s){
  var st=s.status||'unknown';
  var ip=s.ip||s.server_id||'';
  var nm=s.name||s.server_name||ip;
  return '<div class="srv" id="srv-'+esc(cssId(ip))+'">'+
    '<span class="st '+st+'"></span>'+
    '<div><div class="nm">'+esc(nm)+'</div><div class="ip">'+esc(ip)+'</div></div>'+
    '<div class="meta">'+
      '<span class="tag t-'+st+'">'+(st==='up'?'🟢 Доступен':st==='down'?'🔴 Недоступен':'⚪ —')+'</span>'+
      '<button class="btn ghost sm" onclick="checkResources(\''+esc(ip)+'\')">📈 Ресурсы</button>'+
      '<button class="btn ghost sm" onclick="recheck(\''+esc(ip)+'\')">🔄</button>'+
    '</div></div>';
}
function cssId(s){return String(s).replace(/[^a-zA-Z0-9_-]/g,'_');}

async function recheck(ip){
  toast('Проверка '+ip+'…');
  try{ var r=await api('/v1/monitoring/availability/'+encodeURIComponent(ip));
    var st=(r.server&&r.server.status)||(r.items&&r.items[0]&&r.items[0].status)||'unknown';
    toast(ip+': '+(st==='up'?'🟢 доступен':'🔴 недоступен'),st==='up'?'ok':'err');
    renderDashboard();
  }catch(e){ toast(e.message,'err'); }
}
async function checkResources(ip){
  modal('📈 Ресурсы: '+esc(ip),'<div class="spinner"></div>');
  try{
    var r=await api('/v1/monitoring/resources/'+encodeURIComponent(ip));
    var res=r.resources||{};
    var rows=['cpu','ram','disk'].map(function(k){
      var v=res[k];
      if(v==null) return '';
      var tone=toneForPct(v);
      return '<div class="m" style="min-width:100%"><div class="top"><span>'+
        ({cpu:'⚡ CPU',ram:'🧠 RAM',disk:'💾 Диск'}[k])+'</span><span class="tone-'+tone+'">'+v+'%</span></div>'+
        '<div class="bar"><i class="'+tone+'" style="width:'+Math.min(100,v)+'%"></i></div></div>';
    }).join('');
    var meta='';
    if(res.access_method) meta+='<div class="field hint">Метод доступа: <b>'+esc(res.access_method)+'</b></div>';
    if(res.timestamp) meta+='<div class="field hint">Обновлено: '+esc(res.timestamp)+'</div>';
    $('modal').querySelector('.mb').innerHTML=
      '<div class="res">'+(rows||'<div class="empty">Нет данных о ресурсах</div>')+'</div>'+meta+
      (r.message?'<div class="field hint" style="margin-top:10px">'+esc(r.message)+'</div>':'');
  }catch(e){
    $('modal').querySelector('.mb').innerHTML='<div class="empty"><span class="e">⚠️</span>'+esc(e.message)+'</div>';
  }
}
async function ctrlAction(action,okMsg){
  try{
    var r=await api('/v1/control/actions',{method:'POST',body:{action:action}});
    if(action==='send_morning_report'){
      modal('📋 Утренний отчёт','<pre>'+esc(r.message||r.text||'Отчёт сформирован')+'</pre>');
    }else{
      toast(okMsg||r.message||'Готово','ok');
    }
    state.availability=null;renderDashboard();
  }catch(e){ toast(e.message,'err'); }
}
function updatePills(){
  var c=state.control;if(!c)return;
  var mon=c.monitoring_active;
  var pm=$('pillMon');pm.className='pill clk hide-sm '+(mon?'ok':'warn');
  pm.querySelector('span:last-child').textContent=mon?'Мониторинг активен':'Мониторинг на паузе';
  var silent=c.silent_active;
  var ps=$('pillSilent');ps.className='pill clk hide-sm '+(silent?'warn':'ok');
  ps.querySelector('span:last-child').textContent=silent?'🔕 Тихий режим':'🔔 Уведомления вкл.';
}

//==================== Servers ====================
var SRV_TYPES=[
  {v:'linux',l:'🐧 Linux'},{v:'windows',l:'🪟 Windows'},
  {v:'windows_domain',l:'🪟 Windows (домен)'},{v:'windows_admin',l:'🪟 Windows (админ)'},
  {v:'windows_2025',l:'🪟 Windows 2025'},{v:'ping',l:'📡 Ping'}
];
async function renderServers(){
  var el=$('view-servers');
  el.innerHTML='<div class="spinner"></div>';
  try{
    var r=await api('/v1/settings/servers');
    var items=r.items||[];var sum=r.summary||{};
    var cards='<div class="grid cards">'+
      statCard('🖥️','Всего',sum.total!=null?sum.total:items.length,'info')+
      statCard('✅','Включено',sum.enabled||0,'ok')+
      statCard('⛔','Выключено',sum.disabled||0,'warn')+'</div>';
    var list=items.length?items.map(function(s){
      var en=s.enabled!==false;
      return '<div class="srv">'+
        '<span class="st '+(en?'up':'unknown')+'"></span>'+
        '<div><div class="nm">'+esc(s.name||s.ip)+'</div><div class="ip">'+esc(s.ip)+'</div></div>'+
        '<div class="meta">'+
          '<span class="tag">'+esc(typeLabel(s.type))+'</span>'+
          '<span class="tag">⏱ '+esc(s.timeout||'—')+'s</span>'+
          '<span class="tag '+(en?'t-up':'t-off')+'">'+(en?'включён':'выключен')+'</span>'+
          '<label class="switch"><input type="checkbox" '+(en?'checked':'')+
            ' onchange="toggleServer(\''+esc(s.ip)+'\',this.checked)"><span class="sl"></span></label>'+
          '<button class="btn ghost sm" onclick=\'editServer('+JSON.stringify(s).replace(/'/g,"&#39;")+')\'>✏️</button>'+
          '<button class="btn ghost sm" onclick="delServer(\''+esc(s.ip)+'\',\''+esc(s.name||s.ip)+'\')">🗑️</button>'+
        '</div></div>';
    }).join(''):'<div class="empty"><span class="e">🗂️</span>Серверы не добавлены</div>';
    el.innerHTML=cards+
      '<div class="section-title"><span>🖥️ Список серверов</span><span class="ln"></span>'+
        '<button class="btn sm" onclick="editServer(null)">➕ Добавить сервер</button></div>'+list;
  }catch(e){
    el.innerHTML='<div class="card"><div class="body empty"><span class="e">⚠️</span>'+esc(e.message)+'</div></div>';
  }
}
function typeLabel(t){var f=SRV_TYPES.find(function(x){return x.v===t;});return f?f.l:(t||'—');}
function editServer(s){
  var isNew=!s;
  var opts=SRV_TYPES.map(function(t){return '<option value="'+t.v+'" '+(s&&s.type===t.v?'selected':'')+'>'+t.l+'</option>';}).join('');
  modal((isNew?'➕ Новый сервер':'✏️ '+esc(s.name||s.ip)),
    '<div class="field"><label>IP / адрес</label><input id="svIp" value="'+esc(s?s.ip:'')+'" '+(isNew?'':'disabled')+' placeholder="192.168.1.10"></div>'+
    '<div class="field"><label>Имя</label><input id="svName" value="'+esc(s?s.name:'')+'" placeholder="Сервер БД"></div>'+
    '<div class="form-grid">'+
      '<div class="field"><label>Тип</label><select id="svType">'+opts+'</select></div>'+
      '<div class="field"><label>Таймаут (сек)</label><input id="svTimeout" type="number" value="'+esc(s&&s.timeout!=null?s.timeout:30)+'"></div>'+
    '</div>'+
    '<div class="toggle-row"><div class="tx"><b>Включён</b><small>Участвует в мониторинге</small></div>'+
      '<label class="switch"><input type="checkbox" id="svEnabled" '+(!s||s.enabled!==false?'checked':'')+'><span class="sl"></span></label></div>'+
    '<div class="btnrow"><button class="btn" onclick="saveServer('+(isNew?'true':'false')+')">💾 Сохранить</button>'+
      '<button class="btn ghost" onclick="closeModal()">Отмена</button></div>');
}
async function saveServer(isNew){
  var ip=$('svIp').value.trim();
  var body={name:$('svName').value.trim(),type:$('svType').value,
    timeout:parseInt($('svTimeout').value)||30,enabled:$('svEnabled').checked};
  if(!ip){ toast('Укажите IP/адрес','err');return; }
  try{
    if(isNew){ body.ip=ip; await api('/v1/settings/servers',{method:'POST',body:body}); toast('Сервер добавлен','ok'); }
    else{ await api('/v1/settings/servers/'+encodeURIComponent(ip),{method:'PATCH',body:body}); toast('Сервер обновлён','ok'); }
    closeModal();renderServers();
  }catch(e){ toast(e.message,'err'); }
}
async function toggleServer(ip,enabled){
  try{ await api('/v1/settings/servers/'+encodeURIComponent(ip)+'/enabled',{method:'PATCH',body:{enabled:enabled}});
    toast('Сервер '+(enabled?'включён':'выключен'),'ok'); }
  catch(e){ toast(e.message,'err');renderServers(); }
}
async function delServer(ip,name){
  if(!confirm('Удалить сервер "'+name+'" ('+ip+')?'))return;
  try{ await api('/v1/settings/servers/'+encodeURIComponent(ip),{method:'DELETE'});
    toast('Сервер удалён','ok');renderServers(); }
  catch(e){ toast(e.message,'err'); }
}

//==================== Settings ====================
var SETTINGS_TABS=[
  {id:'monitoring',ico:'📡',label:'Мониторинг'},
  {id:'bot',ico:'🤖',label:'Telegram'},
  {id:'matrix',ico:'💬',label:'Matrix'},
  {id:'time',ico:'🕒',label:'Время'},
  {id:'auth',ico:'🔐',label:'Доступы'},
  {id:'report',ico:'📋',label:'Отчёт'},
  {id:'extensions',ico:'🧩',label:'Расширения'},
];
var settingsTab='monitoring';
function renderSettings(){
  var el=$('view-settings');
  el.innerHTML='<div class="chips" style="margin-bottom:18px" id="setTabs">'+
    SETTINGS_TABS.map(function(t){return '<span class="chip'+(t.id===settingsTab?' on':'')+
      '" onclick="setSettingsTab(\''+t.id+'\')">'+t.ico+' '+t.label+'</span>';}).join('')+
    '</div><div id="setBody"><div class="spinner"></div></div>';
  loadSettingsTab();
}
function setSettingsTab(id){ settingsTab=id; renderSettings(); }
function fieldNum(id,label,val,hint){
  return '<div class="field"><label>'+label+'</label><input id="'+id+'" type="number" value="'+esc(val!=null?val:'')+'">'+
    (hint?'<div class="hint">'+hint+'</div>':'')+'</div>';
}
function fieldTxt(id,label,val,ph,type){
  return '<div class="field"><label>'+label+'</label><input id="'+id+'" type="'+(type||'text')+'" value="'+esc(val!=null?val:'')+'" placeholder="'+esc(ph||'')+'"></div>';
}
async function loadSettingsTab(){
  var b=$('setBody');
  try{
    if(settingsTab==='monitoring') return settingsMonitoring(b);
    if(settingsTab==='bot') return settingsBot(b);
    if(settingsTab==='matrix') return settingsMatrix(b);
    if(settingsTab==='time') return settingsTime(b);
    if(settingsTab==='auth') return settingsAuth(b);
    if(settingsTab==='report') return settingsReport(b);
    if(settingsTab==='extensions') return settingsExtensions(b);
  }catch(e){ b.innerHTML='<div class="card"><div class="body empty"><span class="e">⚠️</span>'+esc(e.message)+'</div></div>'; }
}
function pickSettings(r){ return r.settings||r; }

async function settingsMonitoring(b){
  var r=await api('/v1/settings/monitoring');var s=pickSettings(r);
  b.innerHTML=card('📡','Параметры мониторинга',
    '<div class="form-grid">'+
      fieldNum('mCheck','Интервал проверки (сек)',s.check_interval_sec)+
      fieldNum('mTimeout','Базовый таймаут (сек)',s.timeout_sec)+
      fieldNum('mDown','Макс. простой до алерта (сек)',s.max_downtime_sec)+
      fieldNum('mPing','Таймаут ping (сек)',s.ping_timeout_sec)+
      fieldNum('mLinux','Таймаут Linux (сек)',s.linux_timeout_sec)+
      fieldNum('mWin','Таймаут Windows станд. (сек)',s.standard_windows_timeout_sec)+
      fieldNum('mWinDom','Таймаут Windows домен (сек)',s.domain_servers_timeout_sec)+
      fieldNum('mWinAdm','Таймаут Windows админ (сек)',s.admin_servers_timeout_sec)+
      fieldNum('mWin25','Таймаут Windows 2025 (сек)',s.windows_2025_timeout_sec)+
    '</div>'+
    '<div class="btnrow"><button class="btn" onclick="saveMonitoring()">💾 Сохранить</button></div>');
}
async function saveMonitoring(){
  var body={};
  var map={mCheck:'check_interval_sec',mTimeout:'timeout_sec',mDown:'max_downtime_sec',
    mPing:'ping_timeout_sec',mLinux:'linux_timeout_sec',mWin:'standard_windows_timeout_sec',
    mWinDom:'domain_servers_timeout_sec',mWinAdm:'admin_servers_timeout_sec',mWin25:'windows_2025_timeout_sec'};
  Object.keys(map).forEach(function(k){var v=$(k).value;if(v!=='')body[map[k]]=parseInt(v);});
  try{ await api('/v1/settings/monitoring',{method:'PATCH',body:body});toast('Настройки мониторинга сохранены','ok'); }
  catch(e){ toast(e.message,'err'); }
}

async function settingsBot(b){
  var r=await api('/v1/settings/bot');var s=pickSettings(r);
  var chats=s.telegram_chat_ids||(s.telegram_chat_id?[s.telegram_chat_id]:[]);
  var chipsHtml=chats.length?chats.map(function(c){
    return '<span class="chip">'+esc(c)+' <span class="x" onclick="removeBotChat(\''+esc(c)+'\')">✕</span></span>';
  }).join(''):'<span class="field hint">Чаты не добавлены</span>';
  b.innerHTML=card('🤖','Telegram-бот',
    '<div class="field"><label>Токен бота</label><input id="btToken" placeholder="'+esc(s.masked_token||'123456:ABC…')+'">'+
      '<div class="hint">Оставьте пустым, чтобы не менять. Текущий: '+esc(s.masked_token||'—')+'</div></div>'+
    '<div class="field"><label>Чаты получателей</label><div class="chips" style="margin-bottom:10px">'+chipsHtml+'</div>'+
      '<div style="display:flex;gap:8px"><input id="btNewChat" placeholder="chat_id (напр. -100123…)">'+
      '<button class="btn ghost" onclick="addBotChat()">➕</button></div></div>'+
    '<div class="btnrow"><button class="btn" onclick="saveBot()">💾 Сохранить</button>'+
      '<button class="btn ghost" onclick="testBot()">📶 Проверить связь</button></div>');
}
async function saveBot(){
  var body={};var tok=$('btToken').value.trim();if(tok)body.telegram_bot_token=tok;
  try{ await api('/v1/settings/bot',{method:'PATCH',body:body});toast('Настройки Telegram сохранены','ok');settingsBot($('setBody')); }
  catch(e){ toast(e.message,'err'); }
}
async function addBotChat(){
  var c=$('btNewChat').value.trim();if(!c){toast('Укажите chat_id','err');return;}
  try{ await api('/v1/settings/bot/chats',{method:'POST',body:{chat_id:c}});toast('Чат добавлен','ok');settingsBot($('setBody')); }
  catch(e){ toast(e.message,'err'); }
}
async function removeBotChat(c){
  try{ await api('/v1/settings/bot/chats/'+encodeURIComponent(c),{method:'DELETE'});toast('Чат удалён','ok');settingsBot($('setBody')); }
  catch(e){ toast(e.message,'err'); }
}
async function testBot(){
  toast('Проверка связи…');
  try{ var r=await api('/v1/settings/bot/test',{method:'POST'});toast(r.message||(r.ok?'Связь есть':'Нет связи'),r.ok?'ok':'err'); }
  catch(e){ toast(e.message,'err'); }
}

async function settingsMatrix(b){
  var r=await api('/v1/settings/bot/matrix');var s=pickSettings(r);
  b.innerHTML=card('💬','Matrix-бот',
    fieldTxt('mxHome','Homeserver',s.matrix_homeserver,'https://matrix.org')+
    '<div class="field"><label>Access token</label><input id="mxToken" placeholder="'+esc(s.masked_access_token||'syt_…')+'">'+
      '<div class="hint">Оставьте пустым, чтобы не менять. Текущий: '+esc(s.masked_access_token||'—')+'</div></div>'+
    fieldTxt('mxRoom','Room ID',s.matrix_room_id,'!room:matrix.org')+
    '<div class="btnrow"><button class="btn" onclick="saveMatrix()">💾 Сохранить</button>'+
      '<button class="btn ghost" onclick="testMatrix()">📶 Проверить связь</button></div>');
}
async function saveMatrix(){
  var body={matrix_homeserver:$('mxHome').value.trim(),matrix_room_id:$('mxRoom').value.trim()};
  var tok=$('mxToken').value.trim();if(tok)body.matrix_access_token=tok;
  try{ await api('/v1/settings/bot/matrix',{method:'PATCH',body:body});toast('Настройки Matrix сохранены','ok');settingsMatrix($('setBody')); }
  catch(e){ toast(e.message,'err'); }
}
async function testMatrix(){
  toast('Проверка связи…');
  try{ var r=await api('/v1/settings/bot/matrix/test',{method:'POST'});toast(r.message||(r.ok?'Связь есть':'Нет связи'),r.ok?'ok':'err'); }
  catch(e){ toast(e.message,'err'); }
}

async function settingsTime(b){
  var r=await api('/v1/settings/time');var s=pickSettings(r);
  b.innerHTML=card('🕒','Время и тишина',
    '<div class="form-grid">'+
      fieldTxt('tQs','Начало тихого режима',s.quiet_start,'22:00','time')+
      fieldTxt('tQe','Конец тихого режима',s.quiet_end,'08:00','time')+
      fieldTxt('tMc','Время сбора метрик',s.metrics_collection_time,'09:00','time')+
    '</div>'+
    '<div class="btnrow"><button class="btn" onclick="saveTime()">💾 Сохранить</button></div>');
}
async function saveTime(){
  var body={quiet_start:$('tQs').value,quiet_end:$('tQe').value,metrics_collection_time:$('tMc').value};
  try{ await api('/v1/settings/time',{method:'PATCH',body:body});toast('Настройки времени сохранены','ok'); }
  catch(e){ toast(e.message,'err'); }
}

async function settingsAuth(b){
  var r=await api('/v1/settings/auth');var s=pickSettings(r);
  var modes=['ssh_key','ssh_password','windows','mixed','auto'];
  var modeOpts=modes.map(function(m){return '<option value="'+m+'" '+(s.auth_mode===m?'selected':'')+'>'+m+'</option>';}).join('');
  b.innerHTML=
    card('🔐','Доступ SSH / Windows',
      '<div class="form-grid">'+
        '<div class="field"><label>Режим аутентификации</label><select id="auMode">'+modeOpts+'</select></div>'+
        fieldTxt('auSshUser','SSH пользователь',s.ssh_username,'root')+
        fieldNum('auSshPort','SSH порт',s.ssh_port)+
        fieldTxt('auSshKey','Путь к SSH-ключу',s.ssh_key_path,'/root/.ssh/id_rsa')+
        fieldTxt('auWinUser','Windows пользователь',s.windows_username,'Administrator')+
      '</div>'+
      '<div class="form-grid">'+
        '<div class="field"><label>SSH пароль</label><input id="auSshPass" type="password" placeholder="'+esc(s.masked_ssh_password||'не менять')+'"></div>'+
        '<div class="field"><label>Windows пароль</label><input id="auWinPass" type="password" placeholder="'+esc(s.masked_windows_password||'не менять')+'"></div>'+
      '</div>'+
      '<div class="btnrow"><button class="btn" onclick="saveAuth()">💾 Сохранить</button></div>')+
    '<div id="winCredsBox" style="margin-top:18px"></div>';
  loadWindowsCreds();
}
async function saveAuth(){
  var body={auth_mode:$('auMode').value,ssh_username:$('auSshUser').value.trim(),
    ssh_key_path:$('auSshKey').value.trim(),windows_username:$('auWinUser').value.trim()};
  var p=$('auSshPort').value;if(p!=='')body.ssh_port=parseInt(p);
  var sp=$('auSshPass').value;if(sp)body.ssh_password=sp;
  var wp=$('auWinPass').value;if(wp)body.windows_password=wp;
  try{ await api('/v1/settings/auth',{method:'PATCH',body:body});toast('Доступы сохранены','ok'); }
  catch(e){ toast(e.message,'err'); }
}
async function loadWindowsCreds(){
  var box=$('winCredsBox');if(!box)return;
  try{
    var r=await api('/v1/settings/auth/windows-credentials');
    var tr=await api('/v1/settings/auth/windows-types');
    var items=r.items||[];var types=tr.types||[];
    var typeOpts=(r.server_types||types.map(function(t){return t.name;})||['default']);
    var credRows=items.length?items.map(function(c){
      return '<div class="srv"><span class="st '+(c.enabled?'up':'unknown')+'"></span>'+
        '<div><div class="nm">'+esc(c.username)+'</div><div class="ip">'+esc(c.server_type||'default')+' · приоритет '+esc(c.priority||0)+'</div></div>'+
        '<div class="meta"><button class="btn ghost sm" onclick="delWinCred('+c.id+')">🗑️</button></div></div>';
    }).join(''):'<div class="empty">Учётные записи Windows не добавлены</div>';
    var typeRows=types.length?types.map(function(t){
      return '<div class="srv"><span class="st up"></span><div><div class="nm">'+esc(t.name)+'</div>'+
        '<div class="ip">всего '+t.total+' · активных '+t.active+'</div></div>'+
        '<div class="meta"><button class="btn ghost sm" onclick="renameWinType(\''+esc(t.name)+'\')">✏️</button>'+
        '<button class="btn ghost sm" onclick="delWinType(\''+esc(t.name)+'\')">🗑️</button></div></div>';
    }).join(''):'<div class="empty">Типы не созданы</div>';
    var typeSel=typeOpts.map(function(t){return '<option value="'+esc(t)+'">'+esc(t)+'</option>';}).join('');
    box.innerHTML=
      card('👥','Учётные записи Windows',
        credRows+
        '<div class="section-title" style="font-size:.92em;margin:18px 0 10px"><span>Добавить запись</span><span class="ln"></span></div>'+
        '<div class="form-grid">'+
          fieldTxt('wcUser','Пользователь','','DOMAIN\\user')+
          '<div class="field"><label>Пароль</label><input id="wcPass" type="password"></div>'+
          '<div class="field"><label>Тип сервера</label><select id="wcType">'+typeSel+'</select></div>'+
          fieldNum('wcPrio','Приоритет',0)+
        '</div>'+
        '<div class="btnrow"><button class="btn" onclick="addWinCred()">➕ Добавить запись</button></div>')+
      '<div style="margin-top:18px">'+card('📂','Типы Windows-серверов',
        typeRows+
        '<div class="section-title" style="font-size:.92em;margin:18px 0 10px"><span>Новый тип</span><span class="ln"></span></div>'+
        '<div style="display:flex;gap:8px"><input id="wtName" placeholder="название типа">'+
        '<button class="btn ghost" onclick="addWinType()">➕ Создать</button></div>')+'</div>';
  }catch(e){ box.innerHTML='<div class="card"><div class="body empty">'+esc(e.message)+'</div></div>'; }
}
async function addWinCred(){
  var body={username:$('wcUser').value.trim(),password:$('wcPass').value,
    server_type:$('wcType').value,priority:parseInt($('wcPrio').value)||0};
  if(!body.username||!body.password){toast('Заполните пользователя и пароль','err');return;}
  try{ await api('/v1/settings/auth/windows-credentials',{method:'POST',body:body});toast('Запись добавлена','ok');loadWindowsCreds(); }
  catch(e){ toast(e.message,'err'); }
}
async function delWinCred(id){
  if(!confirm('Удалить учётную запись?'))return;
  try{ await api('/v1/settings/auth/windows-credentials/'+id,{method:'DELETE'});toast('Удалено','ok');loadWindowsCreds(); }
  catch(e){ toast(e.message,'err'); }
}
async function addWinType(){
  var n=$('wtName').value.trim();if(!n){toast('Укажите название','err');return;}
  try{ await api('/v1/settings/auth/windows-types',{method:'POST',body:{name:n}});toast('Тип создан','ok');loadWindowsCreds(); }
  catch(e){ toast(e.message,'err'); }
}
async function renameWinType(name){
  var nn=prompt('Новое имя типа "'+name+'":',name);if(!nn||nn===name)return;
  try{ await api('/v1/settings/auth/windows-types/'+encodeURIComponent(name),{method:'PATCH',body:{new_name:nn}});toast('Переименовано','ok');loadWindowsCreds(); }
  catch(e){ toast(e.message,'err'); }
}
async function delWinType(name){
  if(!confirm('Удалить тип "'+name+'"? Записи перейдут в default.'))return;
  try{ await api('/v1/settings/auth/windows-types/'+encodeURIComponent(name),{method:'DELETE'});toast('Тип удалён','ok');loadWindowsCreds(); }
  catch(e){ toast(e.message,'err'); }
}

async function settingsReport(b){
  var r=await api('/v1/settings/report');var s=pickSettings(r);
  var avail=s.available||[];var sel=s.report_extensions||[];
  var chips=avail.length?avail.map(function(o){
    var on=sel.indexOf(o.id)>=0;
    var dis=o.extension_enabled===false;
    return '<span class="chip'+(on?' on':'')+(dis?'" style="opacity:.45;cursor:not-allowed':'')+
      '" '+(dis?'':'onclick="toggleReportExt(this,\''+esc(o.id)+'\')"')+'>'+
      (o.heavy?'🐘 ':'')+esc(o.label||o.name||o.id)+'</span>';
  }).join(''):'<div class="empty">Нет доступных блоков отчёта</div>';
  b.innerHTML=card('📋','Состав утреннего отчёта',
    '<div class="field hint" style="margin-bottom:12px">Выберите блоки, которые включаются в утренний отчёт. 🐘 — тяжёлые блоки.</div>'+
    '<div class="chips" id="reportChips">'+chips+'</div>'+
    '<div class="btnrow"><button class="btn" onclick="saveReport()">💾 Сохранить</button></div>');
}
function toggleReportExt(elm,id){ elm.classList.toggle('on'); }
async function saveReport(){
  var sel=[];document.querySelectorAll('#reportChips .chip.on').forEach(function(c){
    var m=c.getAttribute('onclick');if(m){var mm=m.match(/'([^']+)'\)$/);if(mm)sel.push(mm[1]);}
  });
  try{ await api('/v1/settings/report',{method:'PATCH',body:{report_extensions:sel}});toast('Состав отчёта сохранён','ok'); }
  catch(e){ toast(e.message,'err'); }
}

async function settingsExtensions(b){
  var r=await api('/v1/settings/extensions');var items=r.items||[];var sum=r.summary||{};
  var rows=items.map(function(x){
    var setAction=EXT_SETTINGS[x.id];
    var setBtn=setAction
      ?'<button class="btn ghost sm" style="margin-right:10px" onclick="openExtSettings(\''+esc(setAction)+'\',\''+esc(x.name)+'\')">⚙️ Настройки</button>'
      :'';
    return '<div class="toggle-row"><div class="tx"><b>'+esc(extIcon(x.id)+x.name)+'</b><small>'+esc(x.description||'')+'</small></div>'+
      setBtn+
      '<label class="switch"><input type="checkbox" '+(x.enabled?'checked':'')+
      ' onchange="toggleExt(\''+esc(x.id)+'\',this.checked)"><span class="sl"></span></label></div>';
  }).join('');
  b.innerHTML=
    '<div class="grid cards" style="margin-bottom:16px">'+
      statCard('🧩','Всего',sum.total!=null?sum.total:items.length,'info')+
      statCard('✅','Включено',sum.enabled||0,'ok')+
      statCard('⛔','Выключено',sum.disabled||0,'warn')+'</div>'+
    '<div class="btnrow" style="margin-bottom:14px">'+
      '<button class="btn ok sm" onclick="extAction(\'enable_all\')">✅ Включить все</button>'+
      '<button class="btn warn sm" onclick="extAction(\'disable_all\')">⛔ Выключить все</button>'+
      '<button class="btn ghost sm" onclick="renderSettings()">🔄 Обновить</button>'+
    '</div>'+
    card('🧩','Модули расширений',
      '<div class="field hint" style="margin-bottom:12px">Кнопка «⚙️ Настройки» открывает параметры расширения '+
      '(паттерны, хосты, периоды и т.п.) напрямую из системы мониторинга.</div>'+
      (rows||'<div class="empty">Нет расширений</div>'));
}
// Соответствие id расширения → корневое действие его настроек (то же, что в боте/Android).
var EXT_SETTINGS={
  zfs_monitor:'settings_zfs',
  backup_monitor:'settings_ext_backup_proxmox',
  database_backup_monitor:'settings_ext_backup_db',
  mail_backup_monitor:'settings_ext_backup_mail',
  zfs_pool_free_space_monitor:'zfs_pool_free_space_menu',
  stock_load_monitor:'settings_ext_stock_load',
  nas_transfer_monitor:'settings_ext_nas',
  config_console_backup_monitor:'settings_ext_config_console',
  supplier_stock_files:'settings_ext_supplier_stock',
  resource_monitor:'settings_resources',
  tls_cert_monitor:'settings_ext_tls'
};
var EXT_ICONS={
  resource_monitor:'💻 ',backup_monitor:'💾 ',database_backup_monitor:'🗃️ ',
  mail_backup_monitor:'📬 ',zfs_monitor:'🧊 ',zfs_pool_free_space_monitor:'💽 ',
  snapshot_transfer_monitor:'📸 ',stock_load_monitor:'📦 ',nas_transfer_monitor:'📤 ',
  config_console_backup_monitor:'🗂️ ',supplier_stock_files:'📦 ',tls_cert_monitor:'🔐 ',
  web_interface:'🌐 ',email_processor:'📧 '
};
function extIcon(id){ return EXT_ICONS[id]||'🧩 '; }
async function extAction(action){
  try{ var r=await api('/v1/settings/extensions/actions',{method:'POST',body:{action:action}});
    toast(r.message||'Готово','ok');renderSettings();
  }catch(e){ toast(e.message,'err'); }
}
function openExtSettings(action,title){
  modal('⚙️ '+esc(title),'<div class="spinner"></div>');
  runExtSettings(action,title);
}
async function runExtSettings(action,title){
  if(action==='close'||action==='main_menu'){ closeModal(); return; }
  if(action==='settings_extensions'){ closeModal(); renderSettings(); return; }
  var mb=$('modal').querySelector('.mb');
  if(mb) mb.innerHTML='<div class="spinner"></div>';
  try{
    var r=await api('/v1/settings/extensions/actions',{method:'POST',body:{action:action}});
    var text=r.message||'Готово';
    var opts=(r.menu_options||r.menuOptions||[]).filter(function(o){return o.action;});
    var btns=opts.map(function(o){
      return '<button class="btn ghost sm" onclick="runExtSettings(\''+esc(o.action)+'\',\''+esc(title)+'\')">'+esc(o.label||o.action)+'</button>';
    }).join('');
    if(!btns) btns='<button class="btn ghost sm" onclick="closeModal()">Закрыть</button>';
    if(mb) mb.innerHTML='<pre>'+esc(text)+'</pre><div class="btnrow" style="margin-top:14px">'+btns+'</div>';
  }catch(e){
    if(mb) mb.innerHTML='<div class="empty"><span class="e">⚠️</span>'+esc(e.message)+'</div>'+
      '<div class="btnrow"><button class="btn ghost sm" onclick="closeModal()">Закрыть</button></div>';
  }
}
async function toggleExt(id,enabled){
  try{ await api('/v1/settings/extensions/'+encodeURIComponent(id),{method:'PATCH',body:{enabled:enabled}});
    toast('Расширение '+(enabled?'включено':'выключено'),'ok'); }
  catch(e){ toast(e.message,'err');renderSettings(); }
}

function card(ico,title,body){
  return '<div class="card section"><div class="head"><span class="ico">'+ico+'</span>'+esc(title)+'</div><div class="body">'+body+'</div></div>';
}

//==================== Operations ====================
var OPS=[
  {a:'backup_hosts',e:'💾',t:'Бэкапы Proxmox',d:'Состояние бэкапов хостов'},
  {a:'backup_databases',e:'🗃️',t:'Бэкапы БД',d:'Резервные копии баз данных'},
  {a:'backup_mail',e:'📬',t:'Бэкапы почты',d:'Почтовый сервер'},
  {a:'backup_stock_loads',e:'📦',t:'Остатки 1С',d:'Загрузки остатков'},
  {a:'backup_nas_transfer',e:'📤',t:'Передача на NAS',d:'Трансфер бэкапов'},
  {a:'backup_config_console',e:'🗂️',t:'Конфиги и истории',d:'Бэкап конфигураций'},
  {a:'zfs_menu',e:'🧊',t:'ZFS',d:'Состояние ZFS'},
  {a:'zfs_pool_free_space_menu',e:'💽',t:'Свободное место ZFS',d:'Пулы ZFS'},
  {a:'snapshot_transfer_menu',e:'📸',t:'ZFS снэпшоты',d:'Передачи снэпшотов'},
  {a:'tls_cert_monitor_status',e:'🔐',t:'TLS-сертификаты',d:'Сроки сертификатов'},
  {a:'supplier_stock_reports',e:'📦',t:'Остатки поставщиков',d:'Отчёты по остаткам'},
];
function renderOperations(){
  $('view-operations').innerHTML=
    '<div class="card" style="margin-bottom:18px"><div class="body"><div class="field hint">'+
      'Разделы открывают актуальные статусы напрямую из системы мониторинга. Недоступные модули можно включить в «Настройки → Расширения».'+
    '</div></div>'+
    '<div class="ops">'+OPS.map(function(o){
      return '<button class="op" onclick="openOp(\''+o.a+'\',\''+esc(o.t)+'\',\''+o.e+'\')">'+
        '<span class="e">'+o.e+'</span><div class="t"><b>'+esc(o.t)+'</b><small>'+esc(o.d)+'</small></div></button>';
    }).join('')+'</div>';
}
async function openOp(action,title,emoji){
  modal(emoji+' '+esc(title),'<div class="spinner"></div>');
  try{
    var r=await api('/v1/control/actions',{method:'POST',body:{action:action}});
    var text=r.message||r.text||'Нет данных';
    var opts=r.menu_options||r.menuOptions||[];
    var btns=opts.filter(function(o){return o.action&&o.action!=='close';}).map(function(o){
      return '<button class="btn ghost sm" onclick="openOp(\''+esc(o.action)+'\',\''+esc(title)+'\',\''+emoji+'\')">'+esc(o.label||o.action)+'</button>';
    }).join('');
    $('modal').querySelector('.mb').innerHTML='<pre>'+esc(text)+'</pre>'+
      (btns?'<div class="btnrow" style="margin-top:14px">'+btns+'</div>':'');
  }catch(e){
    $('modal').querySelector('.mb').innerHTML='<div class="empty"><span class="e">⚠️</span>'+esc(e.message)+'</div>';
  }
}

//==================== About ====================
async function renderAbout(){
  var el=$('view-about');
  el.innerHTML=card('ℹ️','О системе',
    '<p style="line-height:1.7">Система мониторинга серверов — единая панель управления инфраструктурой: '+
    'доступность серверов, ресурсы (CPU/RAM/диск), бэкапы, ZFS, TLS-сертификаты, Telegram/Matrix-оповещения '+
    'и утренние отчёты.</p>'+
    '<div class="grid cards" style="margin-top:18px">'+
      statCard('🏷️','Версия сервера',APP_VERSION,'info','sm')+
      '<div class="card"><div class="stat"><span class="lbl">📱 Мобильный клиент</span>'+
        '<span class="val sm tone-info" id="aboutMobile">…</span></div></div>'+
    '</div>'+
    '<div class="btnrow" style="margin-top:16px">'+
      '<a class="btn ghost" href="/health" target="_blank">❤️ Health-check</a>'+
      '<button class="btn ghost" onclick="go(\'dashboard\')">📊 К дашборду</button>'+
    '</div>');
  try{
    var r=await api('/v1/mobile/version?current_version='+encodeURIComponent(APP_VERSION));
    var m=$('aboutMobile');if(m)m.textContent=(r.latest_version||'—')+' (min '+(r.min_supported_version||'—')+')';
  }catch(e){}
}

//==================== Boot ====================
async function boot(){
  $('login').style.display='none';$('app').style.display='flex';
  $('verLabel').textContent='v'+APP_VERSION;
  buildNav();
  // verify token via control status; refresh pills
  try{ state.control=await api('/v1/control/status');updatePills(); }
  catch(e){ if(/Сессия|401/.test(e.message)){return;} }
  go('dashboard');
}

(function init(){
  applyTheme(localStorage.getItem('mon_theme')||'dark');
  if(TOKEN) boot(); else { $('login').style.display='grid'; }
})();
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
        from core.monitor_core import (
            get_current_server_status,
            is_silent_time,
            last_check_time,
            monitoring_active,
            resource_history,
        )
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
                    "disk_class": get_resource_class(disk_value, "disk"),
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
                "resources": resources_data,
            }

            servers_display.append(server_data)

        # Сортируем серверы: сначала проблемные, потом доступные
        servers_display.sort(
            key=lambda x: (0 if x["status"] == "down" else 1 if x["status"] == "warning" else 2)
        )

        # Рассчитываем статистику
        total_servers = len(servers_list)
        servers_up = len(current_status["ok"])
        servers_down = len(current_status["failed"])
        availability_percentage = (
            round((servers_up / total_servers) * 100, 1) if total_servers > 0 else 0
        )

        # Получаем настройки из конфига
        from config.db_settings import CHECK_INTERVAL, RESOURCE_CHECK_INTERVAL

        resource_check_minutes = RESOURCE_CHECK_INTERVAL // 60

        # Считаем проблемы с ресурсами
        resource_alerts_count = 0
        for history in resource_history.values():
            if history:
                last_resource = history[-1]
                if (
                    last_resource.get("cpu", 0) >= 90
                    or last_resource.get("ram", 0) >= 95
                    or last_resource.get("disk", 0) >= 90
                ):
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
            "resource_check_status": (
                "🟢 Работает" if monitoring_active and not is_silent_time() else "⏸️ Приостановлен"
            ),
            "resource_check_interval": resource_check_minutes,
            "resource_alerts": resource_alerts_count,
            "uptime": stats_data.get("uptime", "N/A"),
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
            "uptime": "N/A",
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
        cursor.execute(
            """
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
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_mobile_api_tokens_subject ON mobile_api_tokens(subject)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_mobile_api_tokens_device_id ON mobile_api_tokens(device_id)"
        )
        conn.commit()
    finally:
        conn.close()


def _issue_persistent_mobile_token(
    subject: str, device_id: str | None = None, reissue: bool = False
):
    _ensure_mobile_tokens_table()
    now_ts = int(time.time())
    expires_at = (
        None if _MOBILE_SESSION_TOKEN_TTL_SEC == 0 else now_ts + _MOBILE_SESSION_TOKEN_TTL_SEC
    )
    raw_token = secrets.token_urlsafe(48)
    token_hash = _mobile_token_hash(raw_token)
    token_mask = _mask_token(raw_token)

    conn = _get_mobile_tokens_conn()
    try:
        cursor = conn.cursor()
        if reissue and device_id:
            cursor.execute(
                """
                UPDATE mobile_api_tokens
                SET revoked = 1, revoked_at = ?
                WHERE device_id = ? AND revoked = 0
                """,
                (now_ts, device_id),
            )
        cursor.execute(
            """
            INSERT INTO mobile_api_tokens (
                token_hash, token_mask, subject, device_id, created_at, expires_at, revoked, last_used_at, issued_via
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'default_token')
            """,
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
            """
            SELECT id, subject, device_id, expires_at, revoked
            FROM mobile_api_tokens
            WHERE token_hash = ?
            LIMIT 1
            """,
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

        cursor.execute(
            "UPDATE mobile_api_tokens SET last_used_at = ? WHERE id = ?", (now_ts, token_id)
        )
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


def _get_web_auth_credentials():
    """Возвращает (login, password) веб-интерфейса из настроек.

    Читается из БД на момент запроса (свежие значения после правки из
    ботов/Android/веб-интерфейса). Пустые строки означают «не задано».
    """
    try:
        from core.config_manager import config_manager

        login = str(config_manager.get_setting("WEB_LOGIN", "", use_cache=False) or "").strip()
        password = str(config_manager.get_setting("WEB_PASSWORD", "", use_cache=False) or "")
    except Exception:
        login, password = "", ""
    return login, password


def _set_web_auth_credentials(login=None, password=None):
    """Сохраняет логин/пароль веб-интерфейса в настройки (категория ``web``)."""
    from core.config_manager import config_manager

    if login is not None:
        config_manager.set_setting(
            "WEB_LOGIN", str(login), category="web", data_type="string"
        )
    if password is not None:
        config_manager.set_setting(
            "WEB_PASSWORD", str(password), category="web", data_type="string"
        )


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
        "force_quiet": "toggle_silent",  # legacy fallback
        "force_loud": "toggle_silent",  # legacy fallback
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
        "backup_nas_transfer",
        "backup_config_console",
        "supplier_stock_reports",
        "zfs",
        "zfs_menu",
        "zfs_free_space",
        "zfs_pool_free_space_menu",
        "snapshot_transfer_menu",
        "tls_cert_monitor_status",
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
            return (
                False,
                (f"Для «{setting_title}» передай значение 0-100: " f"`{action_name}|<число>`"),
                "failed",
                None,
            )

        try:
            threshold_value = int(value_raw)
        except ValueError:
            return False, f"Порог «{setting_title}» должен быть целым числом 0-100.", "failed", None

        if threshold_value < 0 or threshold_value > 100:
            return False, f"Порог «{setting_title}» должен быть в диапазоне 0-100.", "failed", None

        settings_manager.set_setting(setting_key, threshold_value, "monitoring")

        cpu_warning = settings_manager.get_setting("CPU_WARNING", 80)
        cpu_critical = settings_manager.get_setting("CPU_CRITICAL", 90)
        ram_warning = settings_manager.get_setting("RAM_WARNING", 85)
        ram_critical = settings_manager.get_setting("RAM_CRITICAL", 95)
        disk_warning = settings_manager.get_setting("DISK_WARNING", 80)
        disk_critical = settings_manager.get_setting("DISK_CRITICAL", 90)

        return (
            True,
            (
                f"✅ {setting_title}: {threshold_value}%\n\n"
                "Текущие пороги:\n"
                f"• CPU предупреждение: {cpu_warning}%\n"
                f"• CPU критический: {cpu_critical}%\n"
                f"• RAM предупреждение: {ram_warning}%\n"
                f"• RAM критический: {ram_critical}%\n"
                f"• Disk предупреждение: {disk_warning}%\n"
                f"• Disk критический: {disk_critical}%"
            ),
            "accepted",
            [
                {"label": "💻 CPU предупреждение", "action": "set_cpu_warning"},
                {"label": "💻 CPU критический", "action": "set_cpu_critical"},
                {"label": "🧠 RAM предупреждение", "action": "set_ram_warning"},
                {"label": "🧠 RAM критический", "action": "set_ram_critical"},
                {"label": "💾 Disk предупреждение", "action": "set_disk_warning"},
                {"label": "💾 Disk критический", "action": "set_disk_critical"},
                {"label": "↩️ Назад", "action": "settings_extensions_back_local"},
                {"label": "✖️ Закрыть", "action": "settings_extensions_close_local"},
            ],
        )

    if (
        action in menu_actions
        or action.startswith("backup_host_")
        or action.startswith("backup_cc_host|")
        or action == "backup_cc_final"
        or action.startswith("zfsp_")
        or action.startswith("db_detail_")
        or action.startswith("settings_db_toggle_monitor_")
        or action.startswith("snapshot_transfer_host_")
        or action.startswith("supplier_stock_reports_")
        or action.startswith("supplier_stock_report_source_day|")
    ):
        from extensions.extension_manager import extension_manager

        extension_requirements = {
            "backup_hosts": ("backup_monitor", "💾 Мониторинг бэкапов Proxmox отключён"),
            "backup_databases": ("database_backup_monitor", "🗃️ Мониторинг бэкапов БД отключён"),
            "backup_mail": ("mail_backup_monitor", "📬 Мониторинг бэкапов почты отключён"),
            "backup_stock_loads": ("stock_load_monitor", "📦 Мониторинг остатков 1С отключён"),
            "backup_nas_transfer": (
                "nas_transfer_monitor",
                "📤 Мониторинг передачи на NAS отключён",
            ),
            "backup_config_console": (
                "config_console_backup_monitor",
                "🗂️ Мониторинг бэкапа конфигов и историй отключён",
            ),
            "supplier_stock_reports": ("supplier_stock_files", "📦 Остатки поставщиков отключены"),
            "zfs": ("zfs_monitor", "🧊 Мониторинг ZFS отключён"),
            "zfs_menu": ("zfs_monitor", "🧊 Мониторинг ZFS отключён"),
            "zfs_pool_free_space_menu": (
                "zfs_pool_free_space_monitor",
                "💽 Мониторинг свободного места ZFS-пулов отключён",
            ),
            "snapshot_transfer_menu": (
                "snapshot_transfer_monitor",
                "📸 Мониторинг передач ZFS-снэпшотов отключён",
            ),
            "tls_cert_monitor_status": (
                "tls_cert_monitor",
                "🔐 Мониторинг TLS-сертификатов отключён",
            ),
        }

        extension_requirement = extension_requirements.get(action)
        if extension_requirement is None and action.startswith("zfsp_"):
            extension_requirement = (
                "zfs_pool_free_space_monitor",
                "💽 Мониторинг свободного места ZFS-пулов отключён",
            )
        if extension_requirement is None and action.startswith("db_detail_"):
            extension_requirement = ("database_backup_monitor", "🗃️ Мониторинг бэкапов БД отключён")
        if extension_requirement is None and action.startswith("settings_db_toggle_monitor_"):
            extension_requirement = ("database_backup_monitor", "🗃️ Мониторинг бэкапов БД отключён")
        if extension_requirement is None and action.startswith("snapshot_transfer_host_"):
            extension_requirement = (
                "snapshot_transfer_monitor",
                "📸 Мониторинг передач ZFS-снэпшотов отключён",
            )
        if extension_requirement is None and (
            action.startswith("backup_cc_host|") or action == "backup_cc_final"
        ):
            extension_requirement = (
                "config_console_backup_monitor",
                "🗂️ Мониторинг бэкапа конфигов и историй отключён",
            )
        if extension_requirement is None and (
            action.startswith("supplier_stock_reports_")
            or action.startswith("supplier_stock_report_source_day|")
        ):
            extension_requirement = (
                "supplier_stock_files",
                "📦 Остатки поставщиков отключены",
            )
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
            from extensions.zfs_pool_free_space import (
                build_status_lines,
                collect_zfs_pool_free_space,
            )

            results, errors = collect_zfs_pool_free_space()
            status_message = "\n".join(build_status_lines(results, errors))
            return (
                True,
                status_message,
                "accepted",
                [
                    {"label": "🔄 Обновить", "action": "zfs_pool_free_space_menu"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            )

        if action == "tls_cert_monitor_status":
            from extensions.tls_cert_monitor import (
                build_status_lines as tls_build_status_lines,
                collect_certificates,
            )

            results, errors = collect_certificates()
            status_message = "\n".join(tls_build_status_lines(results, errors))
            return (
                True,
                status_message,
                "accepted",
                [
                    {"label": "🔄 Обновить", "action": "tls_cert_monitor_status"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            )

        if action == "snapshot_transfer_menu":
            from config.settings import BACKUP_DB_FILE
            from core.config_manager import config_manager as snap_settings

            hosts_cfg = snap_settings.get_setting("SNAPSHOT_TRANSFER_HOSTS", {}) or {}
            if not isinstance(hosts_cfg, dict):
                hosts_cfg = {}

            transfer_rows: dict[str, dict[str, str]] = {}
            try:
                snap_conn = sqlite3.connect(str(BACKUP_DB_FILE))
                snap_cursor = snap_conn.cursor()
                snap_cursor.execute(
                    """
                    SELECT host_name, status, received_at
                    FROM snapshot_transfers
                    ORDER BY datetime(received_at) DESC, id DESC
                    """
                )
                for host_name, transfer_status, received_at in snap_cursor.fetchall():
                    host = str(host_name or "").strip()
                    status_val = str(transfer_status or "").upper().strip()
                    received = str(received_at or "").strip()
                    if not host:
                        continue
                    if host not in transfer_rows:
                        transfer_rows[host] = {
                            "status": status_val,
                            "received_at": received,
                        }
            except sqlite3.OperationalError:
                pass
            except Exception:
                pass
            finally:
                try:
                    snap_conn.close()  # type: ignore[name-defined]
                except Exception:
                    pass

            def _status_icon(status_val: str) -> str:
                normalized = (status_val or "").upper()
                if normalized in {"SUCCESS", "SKIPPED"}:
                    return "🟢"
                if normalized in {"STARTED", "BUSY"}:
                    return "🟡"
                if normalized == "ERROR":
                    return "🔴"
                return "⚪️"

            lines = ["📸 Передачи ZFS-снэпшотов", ""]
            total_hosts = len(hosts_cfg)
            ok_hosts = 0
            problem_hosts = 0
            menu_options: list[dict] = []

            # Хосты — кнопками. В список включаем и настроенные хосты,
            # и те, по которым есть записи о передачах.
            all_host_names = sorted(
                set(hosts_cfg.keys()) | set(transfer_rows.keys()), key=str.lower
            )
            total_hosts = len(all_host_names)
            if not all_host_names:
                lines.append("ℹ️ Пока нет ни хостов, ни записей о передачах.")
            else:
                for host_name in all_host_names:
                    latest = transfer_rows.get(host_name, {})
                    latest_status = str(latest.get("status") or "—")
                    transfer_state = _status_icon(latest_status)
                    if latest_status in {"SUCCESS", "SKIPPED"}:
                        ok_hosts += 1
                    elif latest_status == "ERROR":
                        problem_hosts += 1
                    host_cfg = hosts_cfg.get(host_name) or {}
                    if not isinstance(host_cfg, dict):
                        host_cfg = {}
                    disabled_mark = "" if bool(host_cfg.get("enabled", True)) else "🔕 "
                    menu_options.append(
                        {
                            "label": f"{transfer_state} {disabled_mark}{host_name}",
                            "action": f"snapshot_transfer_host_{host_name}",
                        }
                    )
                lines.append(
                    f"Хостов: {total_hosts} · 🟢 {ok_hosts} · 🔴 {problem_hosts}"
                )
                lines.append("")
                lines.append("Выберите хост, чтобы открыть последние 15 записей.")

            menu_options.extend(
                [
                    {"label": "🔄 Обновить", "action": "snapshot_transfer_menu"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ]
            )
            return True, "\n".join(lines), "accepted", menu_options

        if action.startswith("snapshot_transfer_host_"):
            from config.settings import BACKUP_DB_FILE

            host_name = action.replace("snapshot_transfer_host_", "", 1).strip()
            if not host_name:
                return False, "Не указан хост передач снэпшотов", "failed", None

            records: list[tuple[str, str, str]] = []
            try:
                snap_conn = sqlite3.connect(str(BACKUP_DB_FILE))
                snap_cursor = snap_conn.cursor()
                snap_cursor.execute(
                    """
                    SELECT status, received_at, email_subject
                    FROM snapshot_transfers
                    WHERE host_name = ?
                    ORDER BY datetime(received_at) DESC, id DESC
                    LIMIT 15
                    """,
                    (host_name,),
                )
                for status_val, received_at, subject in snap_cursor.fetchall():
                    records.append(
                        (
                            str(status_val or "").upper().strip(),
                            str(received_at or "").strip(),
                            str(subject or "").strip(),
                        )
                    )
            except sqlite3.OperationalError:
                pass
            except Exception:
                pass
            finally:
                try:
                    snap_conn.close()  # type: ignore[name-defined]
                except Exception:
                    pass

            lines = [f"📸 Передачи снэпшотов · {host_name}", ""]
            if not records:
                lines.append("ℹ️ Записей по хосту пока нет.")
            else:
                ok_count = sum(1 for s, _, _ in records if s in {"SUCCESS", "SKIPPED"})
                err_count = sum(1 for s, _, _ in records if s == "ERROR")
                lines.append(f"Показано: {len(records)} · 🟢 {ok_count} · 🔴 {err_count}")
                lines.append("")
                for status_val, received_at, subject in records:
                    normalized = (status_val or "").upper()
                    if normalized in {"SUCCESS", "SKIPPED"}:
                        icon = "🟢"
                    elif normalized in {"STARTED", "BUSY"}:
                        icon = "🟡"
                    elif normalized == "ERROR":
                        icon = "🔴"
                    else:
                        icon = "⚪️"
                    line = f"{icon} {received_at or '—'} · {status_val or '—'}"
                    if subject:
                        line += f"\n   ↳ {subject}"
                    lines.append(line)

            return (
                True,
                "\n".join(lines),
                "accepted",
                [
                    {"label": "↩️ Назад", "action": "snapshot_transfer_menu"},
                    {"label": "🔄 Обновить", "action": f"snapshot_transfer_host_{host_name}"},
                ],
            )

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
                            {
                                "label": f"✏️ Имя: {host_name}",
                                "action": f"zfsp_edit_name_{host_name}",
                            },
                            {"label": f"🌐 IP: {host_name}", "action": f"zfsp_edit_ip_{host_name}"},
                            {
                                "label": f"🎚 Порог: {host_name}",
                                "action": f"zfsp_edit_threshold_{host_name}",
                            },
                            {
                                "label": f"🗑 Удалить: {host_name}",
                                "action": f"zfsp_delete_{host_name}",
                            },
                            {
                                "label": f"{toggle_text}: {host_name}",
                                "action": f"zfsp_toggle_{host_name}",
                            },
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
                    return _build_zfsp_hosts_response(
                        "❌ Неверный формат. Используй zfsp_add|<name>|<ip>|<threshold>"
                    )
                _, host_name, host_ip, threshold_raw = parts
                host_name = unquote(host_name).strip()
                host_ip = unquote(host_ip).strip()
                try:
                    threshold = int(threshold_raw.strip())
                except ValueError:
                    return _build_zfsp_hosts_response("❌ Порог должен быть целым числом 1-95.")
                if not host_name or not host_ip or threshold < 1 or threshold > 95:
                    return _build_zfsp_hosts_response(
                        "❌ Проверь name/ip/threshold (threshold: 1-95)."
                    )
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
                return _build_zfsp_hosts_response(
                    f"✅ Имя хоста обновлено: {old_name} → {new_name}"
                )

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
                return (
                    True,
                    "💾 Бэкапы Proxmox\n\nДанные по хостам пока отсутствуют.",
                    "accepted",
                    None,
                )
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
            return (
                True,
                (
                    "💾 Бэкапы Proxmox\n\n"
                    f"Всего хостов: {len(hosts)}\n"
                    f"✅ Без проблем: {ok_hosts}\n"
                    f"🚨 Проблемных: {problem_hosts}\n"
                    f"⚪ Отключённых: {disabled_hosts}"
                ),
                "accepted",
                menu_options,
            )

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
                monitor_status = (
                    "⚪ мониторинг отключён" if is_disabled else "🟢 мониторинг включён"
                )
                menu_options.append(
                    {
                        "label": f"{health_prefix} {display_name} ({backup_type}) • {monitor_status}",
                        "action": f"db_detail_{backup_type}__{db_name}",
                    }
                )
            problem_db_names = [
                f"{db_name} ({backup_type})" for backup_type, db_name, _ in problem_db_rows
            ]
            preview_limit = 5
            if problem_db_names:
                preview_names = ", ".join(problem_db_names[:preview_limit])
                if len(problem_db_names) > preview_limit:
                    problem_db_line = f"Проблемные базы: {preview_names} (+{len(problem_db_names) - preview_limit} ещё)"
                else:
                    problem_db_line = f"Проблемные базы: {preview_names}"
            else:
                problem_db_line = "Проблемные базы: нет"
            return (
                True,
                (
                    "🗃️ Бэкапы БД\n\n"
                    f"Баз в отчёте: {len(db_status_rows)}\n"
                    f"🚫 Отключено: {sum(1 for _, _, _, is_disabled, _ in db_status_rows if is_disabled)}\n"
                    f"✅ Без проблем: {ok_dbs}\n"
                    f"🚨 Проблемных: {problem_dbs}\n"
                    f"🔎 В мониторинге: {len(enabled_db_rows)}\n"
                    f"{problem_db_line}"
                ),
                "accepted",
                menu_options,
            )

        if action.startswith("settings_db_toggle_monitor_"):
            raw = action.replace("settings_db_toggle_monitor_", "", 1)
            if "__" not in raw:
                return False, "Неверный формат toggle-действия для базы данных", "failed", None
            encoded_backup_type, encoded_db_name = raw.split("__", 1)
            backup_type = unquote(encoded_backup_type).strip()
            db_name = unquote(encoded_db_name).strip()
            if not backup_type or not db_name:
                return (
                    False,
                    "Не указан тип или имя базы для переключения мониторинга",
                    "failed",
                    None,
                )

            from extensions.backup_monitor.backup_handlers import _toggle_database_monitoring

            now_enabled = _toggle_database_monitoring(backup_type, db_name)
            return (
                True,
                (
                    f"🗃️ {db_name} ({backup_type})\n\n"
                    f"Мониторинг: {'включён' if now_enabled else 'отключён'}."
                ),
                "accepted",
                [
                    {"label": "📋 Обновить список БД", "action": "backup_databases"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ],
            )

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
                return (
                    True,
                    f"🗃️ {db_name} ({backup_type})\n\nДанные по базе отсутствуют.",
                    "accepted",
                    None,
                )

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
                error_text = (
                    f" • errors: {error_count}" if error_count not in (None, "", 0, "0") else ""
                )
                lines.append(f"{icon} {received_at} • {backup_status} • {task_type}{error_text}")

            return True, "\n".join(lines), "accepted", None

        if action == "backup_mail":
            mail_backups = backup_bot.get_mail_backups(hours=72, limit=20)
            if not mail_backups:
                return (
                    True,
                    "📬 Бэкапы почты\n\nДанные по почтовым бэкапам пока отсутствуют.",
                    "accepted",
                    None,
                )
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

        if action == "backup_nas_transfer":
            try:
                nas_hours = int(
                    settings_manager.get_setting("NAS_TRANSFER_ALERT_HOURS", 48) or 48
                )
            except (TypeError, ValueError):
                nas_hours = 48
            transfers = backup_bot.get_nas_transfers(hours=nas_hours, limit=20)
            if not transfers:
                return (
                    True,
                    "📤 Передача бэкапов на NAS\n\nДанные о передаче на NAS пока отсутствуют.",
                    "accepted",
                    None,
                )
            status_icons = {
                "OK": "✅",
                "ERROR": "🚨",
                "SKIPPED": "⏭️",
                "STARTED": "🟡",
                "BUSY": "🟡",
            }
            ok_count = 0
            problem_count = 0
            lines = [f"📤 Передача бэкапов на NAS (за {nas_hours}ч)", ""]
            for (
                host_name,
                status,
                nas_mounted,
                _started_at,
                completed_at_text,
                bases_processed,
                error_count,
                problem_bases,
                received_at,
            ) in transfers:
                status_norm = str(status or "").upper().strip()
                if status_norm == "OK":
                    ok_count += 1
                else:
                    problem_count += 1
                icon = status_icons.get(status_norm, "⚪")
                time_ago = backup_bot.format_time_ago(received_at)
                mount_text = "NAS ✅" if nas_mounted else "NAS ⛔"
                lines.append(
                    f"{icon} {host_name} · {status_norm or '—'} · {mount_text} · "
                    f"баз {bases_processed or 0} · ошибок {error_count or 0} "
                    f"({completed_at_text or time_ago})"
                )
                if problem_bases:
                    lines.append(f"   ⚠️ Проблемные базы: {problem_bases}")
            lines.extend(
                [
                    "",
                    f"Итого: {ok_count}/{len(transfers)} успешно",
                    f"🚨 С проблемами: {problem_count}",
                ]
            )
            return True, "\n".join(lines), "accepted", None

        if action == "backup_config_console" or action.startswith("backup_cc_host|") or (
            action == "backup_cc_final"
        ):
            try:
                cfg_hours = int(
                    settings_manager.get_setting("CONFIG_CONSOLE_ALERT_HOURS", 168) or 168
                )
            except (TypeError, ValueError):
                cfg_hours = 168
            rows = backup_bot.get_config_console_backups(hours=cfg_hours, limit=200)

            from extensions.backup_monitor.backup_utils import (
                get_config_console_servers,
                group_config_console_rows,
            )

            expected = get_config_console_servers()
            grouped = group_config_console_rows(rows, expected_servers=expected)
            servers = grouped["servers"]
            final_row = grouped["final"]
            status_icons = {"OK": "✅", "PARTIAL": "🟡", "ERROR": "🚨"}

            def _fmt_cc(row):
                (
                    host_name, status, dm, rc, st, completed_at_text,
                    vm, lxc, hist_c, hist_f, err, problem_items, received_at,
                ) = row
                sn = str(status or "").upper().strip()
                icon = status_icons.get(sn, "⚪")
                time_ago = backup_bot.format_time_ago(received_at)
                out = (
                    f"{icon} {host_name} · {sn or '—'} · "
                    f"VM {vm or 0} · LXC {lxc or 0} · контейнеров {hist_c or 0} · "
                    f"файлов {hist_f or 0} · ошибок {err or 0} "
                    f"({completed_at_text or time_ago})"
                )
                if dm:
                    out += f"\nСпособ доставки: {dm}"
                if rc:
                    out += f"\nПриёмник: {rc}"
                if problem_items:
                    out += f"\n⚠️ Проблемные элементы: {problem_items}"
                return out

            # Кнопки по серверам + финальная передача — общие для всех экранов.
            ok_count = 0
            menu_options = []
            for entry in servers:
                host = entry["host"]
                if entry["missing"]:
                    icon = "⛔"
                else:
                    sn = str(entry["latest"][1] or "").upper().strip()
                    if sn == "OK":
                        ok_count += 1
                    icon = status_icons.get(sn, "⚪")
                menu_options.append(
                    {"label": f"{icon} {host}", "action": f"backup_cc_host|{host}"}
                )
            if final_row is not None:
                sn = str(final_row[1] or "").upper().strip()
                icon = status_icons.get(sn, "⚪")
                menu_options.append(
                    {"label": f"📦 {icon} Финальная передача на NAS", "action": "backup_cc_final"}
                )
            menu_options.extend(
                [
                    {"label": "🔄 Обновить", "action": "backup_config_console"},
                    {"label": "🏠 На главную", "action": "main_menu"},
                    {"label": "✖️ Закрыть", "action": "close"},
                ]
            )

            # Детализация одного сервера / финальной передачи.
            if action.startswith("backup_cc_host|") or action == "backup_cc_final":
                if action == "backup_cc_final":
                    if final_row is None:
                        msg = "📦 Финальная передача на NAS\n\nНет данных."
                    else:
                        msg = "📦 Финальная передача всех конфигов на NAS\n\n" + _fmt_cc(final_row)
                else:
                    host = action.split("|", 1)[1]
                    entry = next(
                        (e for e in servers if e["host"].lower() == host.lower()), None
                    )
                    if entry is None or entry["missing"] or entry["latest"] is None:
                        msg = f"🗂️ {host}\n\n⛔ Нет свежего отчёта за период."
                    else:
                        msg = f"🗂️ {entry['host']}\n\n" + _fmt_cc(entry["latest"])
                        msg += f"\nПрогонов за период: {entry['runs']}"
                return True, msg, "accepted", menu_options

            # Сводный экран со списком серверов-кнопок.
            if not servers and final_row is None:
                return (
                    True,
                    "🗂️ Бэкап конфигов и историй\n\nДанные пока отсутствуют.",
                    "accepted",
                    menu_options,
                )
            head = f"🗂️ Бэкап конфигов и историй (за {cfg_hours}ч)\n\n"
            if expected:
                head += (
                    f"Серверов: {len(servers)} · 🟢 {ok_count} · "
                    f"⛔ пропустили {len(grouped['missing'])}\n\nВыберите сервер:"
                )
            else:
                head += f"Серверов: {len(servers)} · 🟢 {ok_count}\n\nВыберите сервер:"
            return True, head, "accepted", menu_options

        if action == "supplier_stock_reports":
            # Сводный дашборд — как в Telegram-боте: счётчики статусов,
            # время обновления и по одной строке на поставщика с иконками
            # этапов (приём/обработка/передача). Тот же формат отображается
            # в веб-интерфейсе («Операции») и в плашке «📦 поставщики» Android.
            try:
                cfg = get_supplier_stock_config()
                reporting_days = int((cfg.get("reporting") or {}).get("period_days", 7) or 7)
            except Exception:
                reporting_days = 7
            dashboard = build_supplier_stock_dashboard(period_days=reporting_days)
            counts = dashboard.get("counts", {}) or {}
            items = dashboard.get("items", []) or []
            updated = dashboard.get("updated")
            updated_label = str(updated) if updated else "нет данных"
            lines = [
                "📦 Остатки поставщиков — сводка",
                "",
                f"Обновлено: {updated_label} · Период: {reporting_days} дн.",
                "",
                (
                    f"✅ {counts.get('success', 0)}   "
                    f"🟡 {counts.get('warning', 0)}   "
                    f"🔴 {counts.get('error', 0)}   "
                    f"всего {dashboard.get('total', 0)}"
                ),
                "",
            ]
            overall_icons = {"success": "🟢", "warning": "🟡", "error": "🔴"}
            menu_options = [
                {"label": "⬇️ Скачивание (сутки)", "action": "supplier_stock_reports_download"},
                {"label": "📧 Почта (сутки)", "action": "supplier_stock_reports_mail"},
            ]
            if not items:
                lines.append("⚪️ За период данных нет.")
            else:
                for item in items:
                    overall_icon = overall_icons.get(item.get("overall"), "⚪️")
                    name = str(item.get("source_name") or item.get("source_id") or "источник")
                    kind = item.get("source_kind") or "download"
                    kind_icon = "🌐" if kind == "download" else "📧"
                    recv = (item.get("receive") or {}).get("icon", "⚪️")
                    proc = (item.get("processing") or {}).get("icon", "⚪️")
                    tran = (item.get("transfer") or {}).get("icon", "⚪️")
                    timestamp = str(item.get("timestamp") or "—")
                    lines.append(f"{overall_icon} {kind_icon} {name} — {timestamp}")
                    lines.append(f"    📥 {recv}  🧩 {proc}  📤 {tran}")
                    source_id = str(item.get("source_id") or "").strip()
                    if source_id:
                        menu_options.append(
                            {
                                "label": f"{overall_icon} {name[:24]}",
                                "action": f"supplier_stock_report_source_day|{kind}|{source_id}",
                            }
                        )
                lines.append("")
                lines.append("Кликни поставщика, чтобы открыть историю.")
            return True, "\n".join(lines), "accepted", menu_options

        if action in {
            "supplier_stock_reports_download",
            "supplier_stock_reports_mail",
        }:
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
                return (
                    True,
                    "\n".join(lines),
                    "accepted",
                    [
                        {"label": "⬇️ Скачивание", "action": "supplier_stock_reports_download"},
                        {"label": "📧 Почта", "action": "supplier_stock_reports_mail"},
                    ],
                )

            lines.append("Кликни источник, чтобы открыть историю за сутки.")
            menu_options = [
                {"label": "⬇️ Скачивание", "action": "supplier_stock_reports_download"},
                {"label": "📧 Почта", "action": "supplier_stock_reports_mail"},
            ]
            for item in grouped:
                source_name = str(
                    item.get("source_name") or item.get("source_id") or "неизвестный источник"
                )
                recv = item.get("receive", {})
                proc = item.get("processing", {})
                tran = item.get("transfer", {})
                lines.extend(
                    [
                        "",
                        f"• {source_name}",
                        f"  📥 Загрузка: {recv.get('icon', '⚪️')} {recv.get('label', 'нет данных')}",
                        f"  🧩 Обработка: {proc.get('icon', '⚪️')} {proc.get('label', 'нет данных')}",
                        f"  📤 Выгрузка: {tran.get('icon', '⚪️')} {tran.get('label', 'нет данных')}",
                    ]
                )
                source_id = str(item.get("source_id") or "").strip()
                if source_id:
                    menu_options.append(
                        {
                            "label": f"📊 {source_name[:24]}",
                            "action": f"supplier_stock_report_source_day|{source_kind}|{source_id}",
                        }
                    )
            return True, "\n".join(lines), "accepted", menu_options

        if action.startswith("supplier_stock_report_source_day|"):
            parts = action.split("|", 2)
            if len(parts) != 3:
                return False, "Неверный формат действия истории источника", "failed", None
            source_kind = parts[1].strip() or "download"
            source_id = parts[2].strip()
            if not source_id:
                return False, "Не указан источник", "failed", None
            stats = build_supplier_stock_source_stats(
                source_id=source_id, source_kind=source_kind, period_days=1
            )
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
            return (
                True,
                "\n".join(lines),
                "accepted",
                [
                    {"label": "↩️ Назад", "action": f"supplier_stock_reports_{source_kind}"},
                    {
                        "label": "🔄 Обновить",
                        "action": f"supplier_stock_report_source_day|{source_kind}|{source_id}",
                    },
                ],
            )

        if action == "backup_stock_loads":
            hours = 24
            stock_loads = backup_bot.get_stock_loads(hours=hours)
            if not stock_loads:
                return (
                    True,
                    ("📦 Загрузка остатков 1С\n\n" f"❌ Нет данных за последние {hours} часов."),
                    "accepted",
                    None,
                )

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
                    status_icon = (
                        "✅"
                        if normalized_status == "success"
                        else "⚠️" if normalized_status == "warning" else "🚨"
                    )
                    supplier_text = str(supplier).strip() or "неизвестно"
                    rows_text = f"{rows_count} строк" if rows_count else "строки: —"
                    error_text = f" — {error_sample}" if error_sample else ""
                    time_ago = backup_bot.format_time_ago(received_at)
                    lines.append(
                        f"{status_icon} {supplier_text} ({rows_text}){error_text} ({time_ago})"
                    )
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
            proxmox_hosts = settings_manager.get_setting("PROXMOX_HOSTS", {})
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
                address = str(
                    payload.get("ip") or payload.get("host") or payload.get("address") or ""
                ).strip()
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
                    "💽 Свободное место ZFS (PBS)\n\n" "⚠️ Нет включённых хостов в `PROXMOX_HOSTS`."
                )

            ssh_username = (
                str(settings_manager.get_setting("SSH_USERNAME", "root") or "root").strip()
                or "root"
            )
            ssh_key_path = str(
                settings_manager.get_setting("SSH_KEY_PATH", "/root/.ssh/id_rsa") or ""
            ).strip()
            ssh_port = int(settings_manager.get_setting("SSH_PORT", 22) or 22)

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
                    error_text = (
                        (result.stderr or result.stdout or "unknown error").strip().splitlines()[0]
                    )
                    section_lines.append(f"❌ {host_name} ({address}) — {error_text}")
                    continue

                pool_rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                if not pool_rows:
                    section_lines.append(f"⚠️ {host_name} ({address}) — пулы rpool/zfs не найдены")
                    continue

                section_lines.append(f"🖥 {host_name} ({address})")
                for row in pool_rows:
                    parts = row.split("\t")
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

            zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
            if not isinstance(zfs_servers, dict):
                zfs_servers = {}

            allowed_servers = {
                name
                for name, server_value in zfs_servers.items()
                if not isinstance(server_value, dict) or server_value.get("enabled", True)
            }

            db_path = BACKUP_DATABASE_CONFIG.get("backups_db")
            if not db_path:
                return True, "🧊 ZFS статусы\n\n❌ База бэкапов не настроена.", "accepted", None

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
                    return (
                        True,
                        (
                            "🧊 ZFS статусы\n\n"
                            "❌ Таблица ZFS ещё не создана.\n"
                            "Дождитесь первого письма или перезапустите мониторинг."
                        ),
                        "accepted",
                        None,
                    )
                return False, f"Не удалось получить статусы ZFS: {exc}", "failed", None
            finally:
                conn.close()

            if allowed_servers:
                rows = [row for row in rows if row[0] in allowed_servers]
            else:
                rows = []

            if not rows:
                return True, "📊 ZFS статусы\n\n❌ Данных нет.", "accepted", None

            lines = ["📊 ZFS статусы (последние)", ""]
            current_server = None
            for server_name, pool_name, pool_state, received_at in rows:
                if server_name != current_server:
                    if current_server is not None:
                        lines.append("")
                    lines.append(str(server_name))
                    current_server = server_name
                lines.append(f"• {pool_name}: {pool_state} ({received_at})")

            return True, "\n".join(lines), "accepted", None

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


@app.route("/v1/auth/token", methods=["POST"])
@app.route("/v1/auth/login", methods=["POST"])
@app.route("/api/v1/auth/token", methods=["POST"])
@app.route("/api/v1/auth/login", methods=["POST"])
@app.route("/auth/token", methods=["POST"])
@app.route("/auth/login", methods=["POST"])
@app.route("/token", methods=["POST"])
def mobile_auth_token():
    """Auth endpoint: bootstrap-token -> session token (DB), fallback на legacy username/password."""
    payload = request.get_json(silent=True) or request.form.to_dict()
    bearer_token = _extract_bearer_token(request.headers.get("Authorization"))

    if (
        _MOBILE_DEFAULT_TOKEN
        and bearer_token
        and hmac.compare_digest(bearer_token, _MOBILE_DEFAULT_TOKEN)
    ):
        device_id = (
            str(payload.get("device_id") or request.headers.get("X-Device-ID") or "").strip()
            or None
        )
        subject_raw = str(
            payload.get("subject") or payload.get("client_name") or device_id or "android-client"
        ).strip()
        subject = subject_raw[:128] if subject_raw else "android-client"
        reissue = bool(payload.get("reissue", True))

        token, expires_at, token_mask = _issue_persistent_mobile_token(
            subject=subject,
            device_id=device_id,
            reissue=reissue,
        )

        return jsonify(
            {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": (
                    _MOBILE_SESSION_TOKEN_TTL_SEC if _MOBILE_SESSION_TOKEN_TTL_SEC > 0 else None
                ),
                "scope": "monitoring:read monitoring:control",
                "issued_at": datetime.now().isoformat(),
                "expires_at": (
                    datetime.fromtimestamp(expires_at).isoformat()
                    if expires_at is not None
                    else None
                ),
                "subject": subject,
                "token_mask": token_mask,
                "auth_type": "bootstrap_exchange",
            }
        )

    username, password = _extract_credentials(payload)
    if not username or not password:
        return (
            jsonify(
                {
                    "error": "invalid_request",
                    "message": "Требуется Authorization: Bearer <MOBILE_DEFAULT_TOKEN> или username/login/email + password",
                }
            ),
            400,
        )

    # Если в настройках задан логин/пароль веб-интерфейса — проверяем их.
    # Если не задан ни логин, ни пароль — сохраняем прежнее поведение (вход
    # без проверки), чтобы не заблокировать доступ при первичной настройке.
    web_login, web_password = _get_web_auth_credentials()
    if web_login or web_password:
        valid = hmac.compare_digest(str(username), web_login) and hmac.compare_digest(
            str(password), web_password
        )
        if not valid:
            return (
                jsonify(
                    {
                        "error": "invalid_credentials",
                        "message": "Неверный логин или пароль веб-интерфейса",
                    }
                ),
                401,
            )

    token, expires_at = _issue_mobile_token(username)
    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": _MOBILE_TOKEN_TTL_SEC if _MOBILE_TOKEN_TTL_SEC > 0 else None,
            "scope": "monitoring:read monitoring:control",
            "issued_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.fromtimestamp(expires_at).isoformat() if expires_at is not None else None
            ),
            "auth_type": "legacy_credentials",
        }
    )


@app.route("/v1/auth/token/reissue", methods=["POST"])
@app.route("/api/v1/auth/token/reissue", methods=["POST"])
def mobile_auth_token_reissue():
    """Явный перевыпуск токена по bootstrap token (например, после переустановки приложения)."""
    if not _MOBILE_DEFAULT_TOKEN:
        return (
            jsonify(
                {
                    "error": "bootstrap_token_not_configured",
                    "message": "MOBILE_DEFAULT_TOKEN is not configured on server",
                }
            ),
            503,
        )

    bearer_token = _extract_bearer_token(request.headers.get("Authorization"))
    if not bearer_token or not hmac.compare_digest(bearer_token, _MOBILE_DEFAULT_TOKEN):
        return (
            jsonify({"error": "unauthorized", "message": "Bearer MOBILE_DEFAULT_TOKEN required"}),
            401,
        )

    payload = request.get_json(silent=True) or request.form.to_dict()
    device_id = (
        str(payload.get("device_id") or request.headers.get("X-Device-ID") or "").strip() or None
    )
    subject_raw = str(
        payload.get("subject") or payload.get("client_name") or device_id or "android-client"
    ).strip()
    subject = subject_raw[:128] if subject_raw else "android-client"

    token, expires_at, token_mask = _issue_persistent_mobile_token(
        subject=subject,
        device_id=device_id,
        reissue=True,
    )

    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": (
                _MOBILE_SESSION_TOKEN_TTL_SEC if _MOBILE_SESSION_TOKEN_TTL_SEC > 0 else None
            ),
            "scope": "monitoring:read monitoring:control",
            "issued_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.fromtimestamp(expires_at).isoformat() if expires_at is not None else None
            ),
            "subject": subject,
            "token_mask": token_mask,
            "auth_type": "reissued",
        }
    )


def _build_availability_payload(scope="all"):
    stats, servers = get_monitoring_stats()
    down_ips = {s.get("ip") for s in servers if s.get("status") == "down"}

    items = []
    for s in servers:
        items.append(
            {
                "ip": s.get("ip"),
                "name": s.get("name"),
                "status": "down" if s.get("ip") in down_ips else "up",
                "status_display": s.get("status_display"),
                "scope": scope,
            }
        )

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
    server_id_normalized = str(server_id or "").strip().lower()
    if not server_id_normalized:
        return None

    servers = initialize_servers()
    for server in servers:
        candidates = {
            str(server.get("ip") or "").strip().lower(),
            str(server.get("name") or "").strip().lower(),
            str(server.get("id") or "").strip().lower(),
        }
        if server_id_normalized in candidates:
            return server
    return None


@app.route("/v1/monitoring/availability", methods=["GET"])
@app.route("/api/v1/monitoring/availability", methods=["GET"])
def mobile_availability():
    """Mobile BFF endpoint совместимый с auth_token_probe.sh"""
    started_at = time.time()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        app.logger.warning(
            "GET /v1/monitoring/availability unauthorized request_id=%s reason=%s duration_ms=%s",
            request_id,
            token_data,
            int((time.time() - started_at) * 1000),
        )
        response = jsonify(
            {
                "error": "unauthorized",
                "message": "Bearer token required",
                "reason": token_data,
                "request_id": request_id,
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 401

    scope = request.args.get("scope", "all")
    payload = _build_availability_payload(scope=scope)
    payload["request_id"] = request_id
    duration_ms = int((time.time() - started_at) * 1000)
    app.logger.info(
        "GET /v1/monitoring/availability request_id=%s status=200 duration_ms=%s total=%s",
        request_id,
        duration_ms,
        payload.get("total", 0),
    )
    response = jsonify(payload)
    response.headers["X-Request-ID"] = request_id
    return response


@app.route("/v1/monitoring/availability/<path:server_id>", methods=["GET"])
@app.route("/api/v1/monitoring/availability/<path:server_id>", methods=["GET"])
def mobile_availability_single(server_id):
    """Точечная проверка доступности одного сервера для Android-клиента."""
    started_at = time.time()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        response = jsonify(
            {
                "error": "unauthorized",
                "message": "Bearer token required",
                "reason": token_data,
                "request_id": request_id,
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 401

    server = _resolve_server_for_targeted_check(server_id)
    if not server:
        response = jsonify(
            {
                "error": "server_not_found",
                "message": f'Сервер "{server_id}" не найден',
                "request_id": request_id,
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 404

    is_up = check_server_availability(server)
    status = "up" if is_up else "down"
    now_iso = datetime.now().isoformat()
    payload = {
        "request_id": request_id,
        "generated_at": now_iso,
        "server": {
            "server_id": server.get("ip") or server.get("name") or server_id,
            "name": server.get("name") or server_id,
            "ip": server.get("ip"),
            "status": status,
            "checked_at": now_iso,
        },
        "servers": [
            {
                "id": server.get("ip") or server_id,
                "name": server.get("name") or server_id,
                "status": status,
                "last_checked_at": now_iso,
            }
        ],
        "items": [
            {
                "server_id": server.get("ip") or server_id,
                "status": status,
                "checked_at": now_iso,
            }
        ],
        "summary": {
            "up": 1 if status == "up" else 0,
            "down": 1 if status == "down" else 0,
            "unknown": 0,
        },
    }
    duration_ms = int((time.time() - started_at) * 1000)
    app.logger.info(
        "GET /v1/monitoring/availability/<server_id> request_id=%s status=200 duration_ms=%s server=%s server_status=%s",
        request_id,
        duration_ms,
        server.get("ip") or server_id,
        status,
    )
    response = jsonify(payload)
    response.headers["X-Request-ID"] = request_id
    return response


@app.route("/v1/monitoring/resources/<path:server_id>", methods=["GET"])
@app.route("/api/v1/monitoring/resources/<path:server_id>", methods=["GET"])
def mobile_resources_single(server_id):
    """Точечная проверка ресурсов одного сервера для Android-клиента."""
    started_at = time.time()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        response = jsonify(
            {
                "error": "unauthorized",
                "message": "Bearer token required",
                "reason": token_data,
                "request_id": request_id,
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 401

    server = _resolve_server_for_targeted_check(server_id)
    if not server:
        response = jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Server '{server_id}' not found",
                    "request_id": request_id,
                }
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 404

    if not extension_manager.is_extension_enabled("resource_monitor"):
        response = jsonify(
            {
                "error": {
                    "code": "RESOURCE_MONITOR_DISABLED",
                    "message": "Resource monitor extension is disabled",
                    "request_id": request_id,
                }
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 409

    from modules.targeted_checks import targeted_checks

    success, _, message = targeted_checks.check_single_server_resources(server_id)
    if not success:
        response = jsonify(
            {
                "error": {
                    "code": "RESOURCE_CHECK_FAILED",
                    "message": message,
                    "request_id": request_id,
                }
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 502

    resources = None
    try:
        from core.monitor_core import server_status

        resources = server_status.get(server["ip"], {}).get("resources")
    except Exception:
        resources = None

    payload = {
        "request_id": request_id,
        "server_id": server_id,
        "server_name": server.get("name"),
        "server_ip": server.get("ip"),
        "resources": resources,
        "message": message,
    }
    response = jsonify(payload)
    response.headers["X-Request-ID"] = request_id
    app.logger.info(
        "GET /v1/monitoring/resources/<server_id> request_id=%s status=200 duration_ms=%s server=%s",
        request_id,
        int((time.time() - started_at) * 1000),
        server.get("ip"),
    )
    return response


@app.route("/v1/monitoring/status", methods=["GET"])
@app.route("/api/v1/monitoring/status", methods=["GET"])
def mobile_status():
    """Синоним для быстрой проверки статуса с Bearer токеном."""
    started_at = time.time()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    ok, token_data = _validate_mobile_token(request.headers.get("Authorization"))
    if not ok:
        app.logger.warning(
            "GET /v1/monitoring/status unauthorized request_id=%s reason=%s duration_ms=%s",
            request_id,
            token_data,
            int((time.time() - started_at) * 1000),
        )
        response = jsonify(
            {
                "error": "unauthorized",
                "message": "Bearer token required",
                "reason": token_data,
                "request_id": request_id,
            }
        )
        response.headers["X-Request-ID"] = request_id
        return response, 401

    payload = _build_availability_payload(scope="all")
    payload["request_id"] = request_id
    duration_ms = int((time.time() - started_at) * 1000)
    app.logger.info(
        "GET /v1/monitoring/status request_id=%s status=200 duration_ms=%s total=%s",
        request_id,
        duration_ms,
        payload.get("total", 0),
    )
    response = jsonify(payload)
    response.headers["X-Request-ID"] = request_id
    return response


def _parse_semver(raw_value):
    value = str(raw_value or "").strip()
    parts = value.split(".")
    if len(parts) != 3:
        return None
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def _resolve_branch_apk_url(branch_cfg, repo, version, fallback_url):
    """Собирает ссылку на APK для ветки из шаблона `apk_url_template`.

    Плейсхолдеры: {repo}, {version}, {branch}. Любой сбой шаблона
    (пустой/битый) → возвращается fallback_url (ANDROID_APK_DOWNLOAD_URL).
    """
    template = str((branch_cfg or {}).get("apk_url_template") or "").strip()
    name = str((branch_cfg or {}).get("name") or "").strip()
    if not template:
        return fallback_url
    try:
        url = template.format(repo=repo, version=version, branch=name)
    except (KeyError, IndexError, ValueError):
        return fallback_url
    return url or fallback_url


def _build_android_update_branches():
    """Список веток обновления Android-клиента с готовыми ссылками на APK.

    Возвращает (branches: list[dict], default_branch: str). Каждый элемент:
    {name, title, latest_version, apk_download_url, is_default}.
    """
    from config.settings import (
        ANDROID_APK_DOWNLOAD_URL,
        ANDROID_DEFAULT_UPDATE_BRANCH,
        ANDROID_LATEST_VERSION,
        ANDROID_RELEASE_REPO,
        ANDROID_UPDATE_BRANCHES,
    )

    version = str(ANDROID_LATEST_VERSION)
    repo = str(ANDROID_RELEASE_REPO)
    default_branch = str(ANDROID_DEFAULT_UPDATE_BRANCH or "").strip()
    configured = list(ANDROID_UPDATE_BRANCHES or [])

    if default_branch and not any(
        str(b.get("name") or "").strip() == default_branch for b in configured
    ):
        default_branch = ""
    if not default_branch and configured:
        default_branch = str(configured[0].get("name") or "").strip()

    branches = []
    for branch_cfg in configured:
        name = str(branch_cfg.get("name") or "").strip()
        if not name:
            continue
        branches.append(
            {
                "name": name,
                "title": str(branch_cfg.get("title") or name),
                "latest_version": version,
                "apk_download_url": _resolve_branch_apk_url(
                    branch_cfg, repo, version, str(ANDROID_APK_DOWNLOAD_URL)
                ),
                "is_default": name == default_branch,
            }
        )
    return branches, default_branch


@app.route("/v1/mobile/branches", methods=["GET"])
@app.route("/api/v1/mobile/branches", methods=["GET"])
def v1_mobile_branches():
    """Список доступных веток обновления Android-клиента с ссылками на APK."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    branches, default_branch = _build_android_update_branches()
    return (
        jsonify(
            {
                "request_id": request_id,
                "platform": "android",
                "default_branch": default_branch,
                "branches": branches,
            }
        ),
        200,
    )


@app.route("/v1/mobile/version", methods=["GET"])
@app.route("/api/v1/mobile/version", methods=["GET"])
def v1_mobile_version():
    """Возвращает требования к минимальной версии Android-клиента."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.settings import (
        ANDROID_APK_DOWNLOAD_URL,
        ANDROID_LATEST_VERSION,
        ANDROID_MIN_SUPPORTED_VERSION,
    )

    current_version = (request.args.get("current_version") or "").strip()
    current_semver = _parse_semver(current_version)
    min_semver = _parse_semver(ANDROID_MIN_SUPPORTED_VERSION)

    update_required = False
    if min_semver and current_semver:
        update_required = current_semver < min_semver
    elif current_version:
        update_required = True

    # Если клиент просит APK конкретной ветки (`?branch=develop`) — отдаём
    # ссылку из настроенного списка веток, иначе общий ANDROID_APK_DOWNLOAD_URL.
    requested_branch = (request.args.get("branch") or "").strip()
    apk_download_url = str(ANDROID_APK_DOWNLOAD_URL)
    resolved_branch = ""
    if requested_branch:
        branches, _default_branch = _build_android_update_branches()
        for branch in branches:
            if branch.get("name") == requested_branch:
                apk_download_url = str(branch.get("apk_download_url") or apk_download_url)
                resolved_branch = requested_branch
                break

    return (
        jsonify(
            {
                "request_id": request_id,
                "platform": "android",
                "min_supported_version": str(ANDROID_MIN_SUPPORTED_VERSION),
                "latest_version": str(ANDROID_LATEST_VERSION),
                "apk_download_url": apk_download_url,
                "current_version": current_version,
                "update_required": update_required,
                "branch": resolved_branch,
            }
        ),
        200,
    )


@app.route("/v1/mobile/diagnostics/tls", methods=["POST"])
@app.route("/api/v1/mobile/diagnostics/tls", methods=["POST"])
def v1_mobile_diagnostics_tls():
    """Принимает от Android-клиента результат проверки TLS-сертификата
    Base URL и подробно логирует его в консоль сервера, чтобы можно было
    диагностировать ошибку «⚪ TLS: ошибка проверки (Ошибка сети)»
    удалённо, без доступа к logcat устройства.

    Временный диагностический эндпоинт (см. CHANGELOG 8.62.29)."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        app.logger.warning(
            "POST /v1/mobile/diagnostics/tls unauthorized request_id=%s",
            request_id,
        )
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}

    outcome = str(payload.get("outcome") or "unknown")
    host = payload.get("host")
    port = payload.get("port")
    base_url = payload.get("base_url")
    protocol = payload.get("protocol")
    cipher = payload.get("cipher_suite")
    status_text = payload.get("status_text")
    cert_subject = payload.get("cert_subject")
    cert_issuer = payload.get("cert_issuer")
    cert_not_before = payload.get("cert_not_before")
    cert_not_after = payload.get("cert_not_after")
    cert_sans = payload.get("cert_sans")
    app_version = payload.get("app_version")
    device = payload.get("device")
    error_chain = payload.get("error_chain")
    stacktrace = payload.get("stacktrace")

    subject = token_info.get("subject") if isinstance(token_info, dict) else None

    header = (
        "[ANDROID TLS DIAG] request_id=%s subject=%s app_version=%s device=%s "
        "outcome=%s base_url=%s host=%s port=%s protocol=%s cipher=%s"
    )
    header_args = (
        request_id,
        subject,
        app_version,
        device,
        outcome,
        base_url,
        host,
        port,
        protocol,
        cipher,
    )
    if outcome == "success":
        app.logger.info(header, *header_args)
        app.logger.info(
            "[ANDROID TLS DIAG] request_id=%s status=%s subject=%s issuer=%s "
            "not_before=%s not_after=%s sans=%s",
            request_id,
            status_text,
            cert_subject,
            cert_issuer,
            cert_not_before,
            cert_not_after,
            cert_sans,
        )
    else:
        app.logger.warning(header, *header_args)
        app.logger.warning(
            "[ANDROID TLS DIAG] request_id=%s status=%s error_chain=%s",
            request_id,
            status_text,
            error_chain,
        )
        if stacktrace:
            app.logger.warning(
                "[ANDROID TLS DIAG] request_id=%s stacktrace:\n%s",
                request_id,
                stacktrace,
            )

    return (
        jsonify(
            {
                "request_id": request_id,
                "received": True,
            }
        ),
        200,
    )


@app.route("/v1/control/actions", methods=["POST"])
def v1_control_actions():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action") or "").strip()
    if not action:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INVALID_ACTION",
                        "message": "Field 'action' is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    ok, message, result, menu_options = _execute_mobile_control_action(action)
    if ok:
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": result,
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

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

            data = response_obj.get_json(silent=True) if hasattr(response_obj, "get_json") else {}
            fallback_message = (data or {}).get("message") or message or "Action processed"
            return jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted" if status_code < 400 else "rejected",
                    "message": fallback_message,
                }
            ), (200 if status_code < 400 else status_code)
        except Exception as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "CONTROL_ACTION_FAILED",
                            "message": str(e),
                            "request_id": request_id,
                        }
                    }
                ),
                500,
            )

    return (
        jsonify(
            {
                "error": {
                    "code": "INVALID_ACTION",
                    "message": message,
                    "request_id": request_id,
                }
            }
        ),
        400,
    )


@app.route("/v1/control/status", methods=["GET"])
@app.route("/api/v1/control/status", methods=["GET"])
def v1_control_status():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    import core.monitor_core as monitor_core

    monitoring_active = bool(getattr(monitor_core, "monitoring_active", True))
    silent_active = bool(monitor_core.is_silent_time())
    silent_override = monitor_core.get_silent_override()

    if silent_override is None:
        silent_mode = "auto"
    elif silent_override:
        silent_mode = "force_quiet"
    else:
        silent_mode = "force_loud"

    return (
        jsonify(
            {
                "request_id": request_id,
                "monitoring_active": monitoring_active,
                "monitoring_status": "active" if monitoring_active else "paused",
                "silent_active": silent_active,
                "silent_mode": silent_mode,
                "silent_override": silent_override,
            }
        ),
        200,
    )


def _mask_secret(value):
    """Возвращает маскированное значение секрета без раскрытия исходной строки."""
    value_str = str(value or "").strip()
    if not value_str:
        return ""
    if ":" in value_str:
        prefix = value_str.split(":", 1)[0]
        return f"{prefix}:***"
    return "********"


def _hour_to_hhmm(value, fallback):
    try:
        hour_value = int(value)
        if 0 <= hour_value <= 23:
            return f"{hour_value:02d}:00"
    except (TypeError, ValueError):
        pass
    return fallback


@app.route("/v1/settings/extensions", methods=["GET"])
def v1_get_settings_extensions():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    status_map = extension_manager.get_extensions_status()
    items = []
    enabled_count = 0

    for ext_id, status_info in status_map.items():
        enabled = bool(status_info.get("enabled"))
        if enabled:
            enabled_count += 1
        info = status_info.get("info") or {}
        items.append(
            {
                "id": ext_id,
                "name": info.get("name", ext_id),
                "description": info.get("description", ""),
                "enabled": enabled,
            }
        )

    return (
        jsonify(
            {
                "request_id": request_id,
                "items": items,
                "summary": {
                    "total": len(items),
                    "enabled": enabled_count,
                    "disabled": len(items) - enabled_count,
                },
            }
        ),
        200,
    )


@app.route("/v1/settings/extensions/<extension_id>", methods=["PATCH"])
def v1_patch_settings_extension(extension_id):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    enabled = payload.get("enabled")
    if enabled is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "Field 'enabled' is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    if extension_id not in extension_manager.get_extensions_status():
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": f"Extension '{extension_id}' not found",
                        "request_id": request_id,
                    }
                }
            ),
            404,
        )

    success, message = (
        extension_manager.enable_extension(extension_id)
        if bool(enabled)
        else extension_manager.disable_extension(extension_id)
    )

    if not success:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UPDATE_FAILED",
                        "message": message,
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "request_id": request_id,
                "extension_id": extension_id,
                "enabled": bool(enabled),
                "message": message,
            }
        ),
        200,
    )


def _build_report_settings_payload(request_id):
    """Готовит тело ответа для настроек состава отчёта."""
    from lib.report_settings import (
        REPORT_CAPABLE_EXTENSIONS,
        get_report_extension_label,
        get_report_extensions,
        is_heavy_report_extension,
    )

    selected = set(get_report_extensions(use_cache=False))
    status_map = extension_manager.get_extensions_status()

    available = []
    for ext_id in REPORT_CAPABLE_EXTENSIONS:
        info = (status_map.get(ext_id) or {}).get("info") or {}
        enabled = bool((status_map.get(ext_id) or {}).get("enabled"))
        available.append(
            {
                "id": ext_id,
                "name": info.get("name", get_report_extension_label(ext_id)),
                "label": get_report_extension_label(ext_id),
                "description": info.get("description", ""),
                "extension_enabled": enabled,
                "included": ext_id in selected,
                "heavy": is_heavy_report_extension(ext_id),
            }
        )

    return {
        "request_id": request_id,
        "settings": {
            "report_extensions": [
                ext_id for ext_id in REPORT_CAPABLE_EXTENSIONS if ext_id in selected
            ],
            "available": available,
        },
    }


@app.route("/v1/settings/report", methods=["GET"])
def v1_get_settings_report():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    app.logger.info("GET /v1/settings/report request_id=%s", request_id)
    return jsonify(_build_report_settings_payload(request_id)), 200


@app.route("/v1/settings/report", methods=["PATCH"])
def v1_patch_settings_report():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from lib.report_settings import REPORT_CAPABLE_EXTENSIONS, set_report_extensions

    payload = request.get_json(silent=True) or {}
    extensions_list = payload.get("report_extensions")
    if extensions_list is None or not isinstance(extensions_list, list):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "Field 'report_extensions' (list) is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    unknown = [
        str(item) for item in extensions_list if str(item) not in REPORT_CAPABLE_EXTENSIONS
    ]
    if unknown:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": f"Unknown report extensions: {', '.join(unknown)}",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    set_report_extensions(extensions_list)
    app.logger.info("PATCH /v1/settings/report request_id=%s", request_id)
    return jsonify(_build_report_settings_payload(request_id)), 200


@app.route("/v1/settings/extensions/actions", methods=["POST"])
def v1_extensions_actions():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    raw_action = str(payload.get("action") or "").strip()
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
        proxmox_hosts = _normalize_proxmox_hosts(
            settings_manager.get_setting("PROXMOX_HOSTS", {}, use_cache=False)
        )
        if proxmox_hosts:
            return proxmox_hosts

        try:
            from core.config_manager import config_manager

            fallback_db_hosts = _normalize_proxmox_hosts(
                config_manager.get_setting("PROXMOX_HOSTS", {})
            )
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

    def _count_setting_entries(setting_key: str) -> int:
        """Возвращает число элементов в настройке-словаре/списке (для статуса)."""
        try:
            raw_value = settings_manager.get_setting(setting_key, {}, use_cache=False)
        except TypeError:
            raw_value = settings_manager.get_setting(setting_key, {})
        except Exception:
            raw_value = {}
        if isinstance(raw_value, str):
            try:
                raw_value = json.loads(raw_value)
            except Exception:
                try:
                    raw_value = ast.literal_eval(raw_value)
                except Exception:
                    raw_value = {}
        if isinstance(raw_value, dict):
            return len(raw_value)
        if isinstance(raw_value, (list, tuple, set)):
            return len(raw_value)
        return 0

    def _get_int_setting(setting_key: str, default: int) -> int:
        """Безопасно читает целочисленную настройку с дефолтом."""
        try:
            raw_value = settings_manager.get_setting(setting_key, default, use_cache=False)
        except TypeError:
            raw_value = settings_manager.get_setting(setting_key, default)
        except Exception:
            return default
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return default

    tls_cert_count = _count_setting_entries("TLS_CERT_DOMAINS")
    nas_alert_hours = _get_int_setting("NAS_TRANSFER_ALERT_HOURS", 24)
    config_console_alert_hours = _get_int_setting("CONFIG_CONSOLE_ALERT_HOURS", 24)
    zfs_pool_hosts_count = _count_setting_entries("ZFS_POOL_FREE_SPACE_HOSTS")

    settings_menu_action_map = {
        "settings_ext_tls": {
            "message": (
                "🔐 Настройки расширения TLS-сертификатов\n\n"
                f"Отслеживаемых сертификатов: {tls_cert_count}\n\n"
                "Список доменов и пороги предупреждений редактируются "
                "в Telegram-боте."
            ),
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_ext_nas": {
            "message": (
                "📤 Настройки расширения переноса на NAS\n\n"
                f"Порог тревоги: {nas_alert_hours} ч без свежей передачи.\n\n"
                "Детальная настройка хостов и порогов доступна в Telegram-боте."
            ),
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "settings_ext_config_console": {
            "message": (
                "🗂️ Настройки расширения бэкапов конфигураций консолей\n\n"
                f"Порог тревоги: {config_console_alert_hours} ч без свежего бэкапа.\n\n"
                "Детальная настройка доступна в Telegram-боте."
            ),
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
        "zfs_pool_free_space_menu": {
            "message": (
                "💽 Настройки расширения свободного места в пулах ZFS\n\n"
                f"Хостов в списке: {zfs_pool_hosts_count}\n\n"
                "Добавление хостов и пороги свободного места настраиваются "
                "в Telegram-боте."
            ),
            "menu_options": [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ],
        },
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

    if action == "enable_all":
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.enable_extension(ext_id)
            if success:
                changed += 1
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "message": f"✅ Включено {changed} расширений",
                }
            ),
            200,
        )

    if action == "disable_all":
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.disable_extension(ext_id)
            if success:
                changed += 1
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "message": f"✅ Отключено {changed} расширений",
                }
            ),
            200,
        )

    if action == "settings_ext_enable_all":
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.enable_extension(ext_id)
            if success:
                changed += 1
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "message": f"✅ Включено {changed} расширений",
                }
            ),
            200,
        )

    if action == "settings_ext_disable_all":
        changed = 0
        for ext_id in extension_manager.get_extensions_status():
            success, _ = extension_manager.disable_extension(ext_id)
            if success:
                changed += 1
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "message": f"✅ Отключено {changed} расширений",
                }
            ),
            200,
        )

    if action.startswith("settings_ext_toggle_"):
        extension_id = action.replace("settings_ext_toggle_", "", 1).strip()
        if not extension_id:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_ACTION",
                            "message": "Extension id is required for settings_ext_toggle_*",
                            "request_id": request_id,
                        }
                    }
                ),
                400,
            )

        status_map = extension_manager.get_extensions_status()
        if extension_id not in status_map:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Extension '{extension_id}' not found",
                            "request_id": request_id,
                        }
                    }
                ),
                404,
            )

        enabled_now = bool((status_map.get(extension_id) or {}).get("enabled"))
        success, message = (
            extension_manager.disable_extension(extension_id)
            if enabled_now
            else extension_manager.enable_extension(extension_id)
        )
        if not success:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "UPDATE_FAILED",
                            "message": message,
                            "request_id": request_id,
                        }
                    }
                ),
                500,
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "message": message,
                }
            ),
            200,
        )

    if action == "settings_ext_backup_proxmox":
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
        proxmox_count = len(proxmox_hosts)
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

    if action == "settings_backup_proxmox":
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

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
                    enabled = bool(host_value.get("enabled", True))
                lines.append(f"{'🟢' if enabled else '🔴'} {host_name}")
        menu_options = []
        for host_name in sorted(proxmox_hosts.keys()):
            host_value = proxmox_hosts.get(host_name)
            enabled = True
            if isinstance(host_value, dict):
                enabled = bool(host_value.get("enabled", True))
            toggle_label = "⛔️ Отключить" if enabled else "✅ Включить"
            menu_options.extend(
                [
                    {"label": f"✏️ {host_name}", "action": f"settings_proxmox_edit_{host_name}"},
                    {"label": f"🗑️ {host_name}", "action": f"settings_proxmox_delete_{host_name}"},
                    {
                        "label": f"{toggle_label} {host_name}",
                        "action": f"settings_proxmox_toggle_{host_name}",
                    },
                ]
            )
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_proxmox_toggle_"):
        host_name = raw_action[len("settings_proxmox_toggle_") :]
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()

        host_value = proxmox_hosts.get(host_name)
        if host_value is None:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": f"❌ Хост '{host_name}' не найден.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_proxmox_list"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        enabled = True
        if isinstance(host_value, dict):
            enabled = bool(host_value.get("enabled", True))
            host_value["enabled"] = not enabled
        else:
            proxmox_hosts[host_name] = {"pattern": str(host_value), "enabled": not enabled}

        settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)
        next_action = "settings_proxmox_list"
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

    if action.startswith("settings_proxmox_delete_"):
        host_name = raw_action[len("settings_proxmox_delete_") :]
        proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()

        if host_name not in proxmox_hosts:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": f"❌ Хост '{host_name}' не найден.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_proxmox_list"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        proxmox_hosts.pop(host_name, None)
        settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

    if action.startswith("settings_proxmox_edit_"):
        host_name = raw_action[len("settings_proxmox_edit_") :]
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

    if action == "settings_proxmox_add" or action.startswith("settings_proxmox_add|"):
        host_name = ""
        if "|" in raw_action:
            host_name = unquote(raw_action.split("|", 1)[1]).strip()

        if host_name:
            proxmox_hosts = _get_proxmox_hosts_for_mobile_settings()
            if host_name in proxmox_hosts:
                return (
                    jsonify(
                        {
                            "request_id": request_id,
                            "action": action,
                            "result": "rejected",
                            "message": f"❌ Хост '{host_name}' уже добавлен.",
                            "menu_options": [
                                {"label": "📋 Список хостов", "action": "settings_proxmox_list"},
                                {"label": "↩️ Назад", "action": "settings_backup_proxmox"},
                                {"label": "✖️ Закрыть", "action": "close"},
                            ],
                        }
                    ),
                    200,
                )

            proxmox_hosts[host_name] = {"enabled": True}
            settings_manager.set_setting("PROXMOX_HOSTS", proxmox_hosts)
            return (
                jsonify(
                    {
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
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

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
            for index, (pattern_id, pattern_type, pattern_value, category, enabled) in enumerate(
                rows, start=1
            ):
                display_category = category
                display_type = pattern_type
                if (
                    category == "database"
                    and isinstance(pattern_type, str)
                    and pattern_type.startswith("proxmox")
                ):
                    display_category = "proxmox"
                    suffix = pattern_type[len("proxmox") :].strip("_:- ")
                    display_type = suffix or "subject"
                marker = "🟢" if bool(enabled) else "🔴"
                lines.append(
                    f"{index}. {marker} [{display_category}/{display_type}] {pattern_value}"
                )

        menu_options = []
        for index, (pattern_id, pattern_type, pattern_value, category, enabled) in enumerate(
            rows, start=1
        ):
            display_category = category
            display_type = pattern_type
            if (
                category == "database"
                and isinstance(pattern_type, str)
                and pattern_type.startswith("proxmox")
            ):
                display_category = "proxmox"
                suffix = pattern_type[len("proxmox") :].strip("_:- ")
                display_type = suffix or "subject"
            toggle_label = "⛔️ Отключить" if bool(enabled) else "✅ Включить"
            menu_options.extend(
                [
                    {
                        "label": f"✏️ {index}. {display_category}:{display_type} — {pattern_value}",
                        "action": f"settings_proxmox_pattern_edit_{pattern_id}",
                    },
                    {
                        "label": f"🗑️ {index}. {display_category}:{display_type}",
                        "action": f"settings_proxmox_pattern_delete_{pattern_id}",
                    },
                    {
                        "label": f"{toggle_label} {index}. {display_category}:{display_type}",
                        "action": f"settings_proxmox_pattern_toggle_{pattern_id}",
                    },
                ]
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {"label": "➕ Добавить паттерн", "action": "settings_proxmox_pattern_add"},
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": "settings_ext_backup_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

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
            menu_options.extend(
                [
                    {
                        "label": f"✏️ {index}. mail:{pattern_type}",
                        "action": f"settings_mail_pattern_edit_{pattern_id}",
                    },
                    {
                        "label": f"🗑️ {index}. mail:{pattern_type}",
                        "action": f"settings_mail_pattern_delete_{pattern_id}",
                    },
                    {
                        "label": f"{toggle_label} {index}. mail:{pattern_type}",
                        "action": f"settings_mail_pattern_toggle_{pattern_id}",
                    },
                ]
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {"label": "➕ Добавить паттерн", "action": "settings_mail_pattern_add"},
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_mail_pattern_toggle_"):
        pattern_id_raw = raw_action[len("settings_mail_pattern_toggle_") :].strip()
        if not pattern_id_raw.isdigit():
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Некорректный идентификатор паттерна.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT enabled FROM backup_patterns WHERE id = ? AND category = 'mail'", (pattern_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Паттерн не найден.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        next_enabled = 0 if bool(row[0]) else 1
        cursor.execute(
            "UPDATE backup_patterns SET enabled = ? WHERE id = ?", (next_enabled, pattern_id)
        )
        conn.commit()
        conn.close()
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"🔄 Паттерн {'включён' if next_enabled else 'отключён'}.",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                        {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_mail_pattern_delete_"):
        pattern_id_raw = raw_action[len("settings_mail_pattern_delete_") :].strip()
        if not pattern_id_raw.isdigit():
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Некорректный идентификатор паттерна.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE backup_patterns SET enabled = 0 WHERE id = ? AND category = 'mail'",
            (pattern_id,),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted" if deleted else "rejected",
                    "message": "✅ Паттерн удалён." if deleted else "❌ Паттерн не найден.",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                        {"label": "↩️ Назад", "action": "settings_ext_backup_mail"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_mail_pattern_add") or action.startswith(
        "settings_mail_pattern_edit_"
    ):

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
            fragments = [
                item.strip() for item in re.split(r"[;,]", raw_fragments or "") if item.strip()
            ]
            if not fragments:
                return ""
            escaped_parts = [re.escape(fragment) for fragment in fragments]
            return r".*".join(escaped_parts)

        action_parts = raw_action.split("|")

        if action == "settings_mail_pattern_add":
            if len(action_parts) < 3:
                return (
                    jsonify(
                        {
                            "request_id": request_id,
                            "action": action,
                            "result": "accepted",
                            "message": (
                                "➕ Добавление паттерна почты\n\n"
                                "Android/web: выберите режим (тема или фрагменты), введите значение и сохраните."
                            ),
                            "menu_options": [
                                {
                                    "label": "➕ По теме письма",
                                    "action": "settings_mail_pattern_add|subject|",
                                },
                                {
                                    "label": "➕ По фрагментам",
                                    "action": "settings_mail_pattern_add|fragments|",
                                },
                                {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                                {"label": "✖️ Закрыть", "action": "close"},
                            ],
                        }
                    ),
                    200,
                )

            build_mode = _decode_action_part(action_parts[1]).lower() or "subject"
            raw_value = _decode_action_part("|".join(action_parts[2:]))
            pattern_value = (
                _build_mail_pattern_from_fragments(raw_value)
                if build_mode == "fragments"
                else _build_mail_pattern_from_subject(raw_value)
            )
            source_label = "фрагменты" if build_mode == "fragments" else "тема"

            if not pattern_value:
                return (
                    jsonify(
                        {
                            "request_id": request_id,
                            "action": action,
                            "result": "rejected",
                            "message": "❌ Не удалось собрать паттерн. Проверьте ввод.",
                            "menu_options": [
                                {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                                {"label": "✖️ Закрыть", "action": "close"},
                            ],
                        }
                    ),
                    200,
                )

            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                ("subject", pattern_value, "mail"),
            )
            conn.commit()
            conn.close()
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted",
                        "message": f"✅ Паттерн добавлен (источник: {source_label}).",
                        "menu_options": [
                            {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        pattern_id_raw = raw_action[len("settings_mail_pattern_edit_") :].split("|", 1)[0].strip()
        if not pattern_id_raw.isdigit():
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Некорректный идентификатор паттерна.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        if len(action_parts) < 2:
            pattern_id = int(pattern_id_raw)
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pattern FROM backup_patterns WHERE id = ? AND category = 'mail'",
                (pattern_id,),
            )
            row = cursor.fetchone()
            conn.close()
            current_pattern = row[0] if row and len(row) > 0 else ""
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted" if current_pattern else "rejected",
                        "message": (
                            (
                                "✏️ Редактирование паттерна почты\n\n"
                                f"Текущий паттерн: `{current_pattern}`\n\n"
                                "Нажмите кнопку ниже, чтобы открыть ввод нового значения."
                            )
                            if current_pattern
                            else "❌ Паттерн не найден."
                        ),
                        "menu_options": (
                            [
                                {
                                    "label": "✏️ Ввести новый паттерн",
                                    "action": f"settings_mail_pattern_edit_{pattern_id}",
                                },
                            ]
                            if current_pattern
                            else []
                        )
                        + [
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        new_pattern = _decode_action_part("|".join(action_parts[1:]))
        if not new_pattern:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Паттерн не может быть пустым.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        pattern_id = int(pattern_id_raw)
        conn = settings_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE backup_patterns SET pattern = ? WHERE id = ? AND category = 'mail'",
            (new_pattern, pattern_id),
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted" if updated else "rejected",
                    "message": "✅ Паттерн обновлён." if updated else "❌ Паттерн не найден.",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_patterns_mail"},
                        {"label": "↩️ Назад", "action": "settings_patterns_mail"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_proxmox_pattern_toggle_"):
        pattern_id_raw = raw_action[len("settings_proxmox_pattern_toggle_") :].strip()
        if not pattern_id_raw.isdigit():
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Некорректный идентификатор паттерна.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

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
            (pattern_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Паттерн не найден.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        next_enabled = 0 if bool(row[0]) else 1
        cursor.execute(
            "UPDATE backup_patterns SET enabled = ? WHERE id = ?", (next_enabled, pattern_id)
        )
        conn.commit()
        conn.close()
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

    if action.startswith("settings_proxmox_pattern_delete_"):
        pattern_id_raw = raw_action[len("settings_proxmox_pattern_delete_") :].strip()
        if not pattern_id_raw.isdigit():
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Некорректный идентификатор паттерна.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

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
            (pattern_id,),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return (
            jsonify(
                {
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
                }
            ),
            200,
        )

    if action.startswith("settings_proxmox_pattern_add") or action.startswith(
        "settings_proxmox_pattern_edit_"
    ):

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
                return (
                    jsonify(
                        {
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
                        }
                    ),
                    200,
                )

            category = _decode_action_part(action_parts[1]).lower() or "proxmox"
            pattern_type = _decode_action_part(action_parts[2]).lower() or "subject"
            pattern_value = _decode_action_part("|".join(action_parts[3:]))

            if category not in {"proxmox", "database"}:
                return (
                    jsonify(
                        {
                            "request_id": request_id,
                            "action": action,
                            "result": "rejected",
                            "message": "❌ Категория должна быть proxmox или database.",
                            "menu_options": [
                                {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                                {"label": "✖️ Закрыть", "action": "close"},
                            ],
                        }
                    ),
                    200,
                )

            if not pattern_value:
                return (
                    jsonify(
                        {
                            "request_id": request_id,
                            "action": action,
                            "result": "rejected",
                            "message": "❌ Паттерн не может быть пустым.",
                            "menu_options": [
                                {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                                {"label": "✖️ Закрыть", "action": "close"},
                            ],
                        }
                    ),
                    200,
                )

            db_pattern_type = _proxmox_type_to_db_type(pattern_type, category)
            conn = settings_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backup_patterns (pattern_type, pattern, category, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (db_pattern_type, pattern_value, category),
            )
            conn.commit()
            conn.close()
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted",
                        "message": "✅ Паттерн Proxmox добавлен.",
                        "menu_options": [
                            {"label": "📋 Обновить список", "action": "settings_patterns_proxmox"},
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        pattern_id_raw = (
            raw_action[len("settings_proxmox_pattern_edit_") :].split("|", 1)[0].strip()
        )
        if not pattern_id_raw.isdigit():
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Некорректный идентификатор паттерна.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

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
                (pattern_id,),
            )
            row = cursor.fetchone()
            conn.close()
            current_pattern_type = row[0] if row and len(row) > 0 else ""
            current_pattern = row[1] if row and len(row) > 1 else ""
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted" if current_pattern else "rejected",
                        "message": (
                            (
                                "✏️ Редактирование паттерна Proxmox\n\n"
                                f"Текущий тип: `{current_pattern_type}`\n"
                                f"Текущий паттерн: `{current_pattern}`\n\n"
                                "Нажмите кнопку ниже, чтобы открыть ввод нового типа и паттерна.\n"
                                "Если клиент не поддерживает окно ввода, отправьте действие в формате:\n"
                                "`settings_proxmox_pattern_edit_<id>|<новый_тип>|<новый_паттерн>`"
                            )
                            if current_pattern
                            else ("❌ Паттерн не найден.")
                        ),
                        "menu_options": (
                            [
                                {
                                    "label": "✏️ Ввести новый паттерн",
                                    "action": f"settings_proxmox_pattern_edit_{pattern_id}",
                                },
                            ]
                            if current_pattern
                            else []
                        )
                        + [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        if len(action_parts) >= 3:
            new_pattern_type = _decode_action_part(action_parts[1]).lower() or "subject"
            new_pattern = _decode_action_part("|".join(action_parts[2:]))
        else:
            new_pattern_type = ""
            new_pattern = _decode_action_part("|".join(action_parts[1:]))
        if not new_pattern:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Паттерн не может быть пустым.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        if len(action_parts) >= 3 and not new_pattern_type:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Тип паттерна не может быть пустым.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

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
                (new_pattern_type, new_pattern, pattern_id),
            )
        else:
            cursor.execute(
                """
                UPDATE backup_patterns
                SET pattern = ?
                WHERE id = ?
                  AND (category = 'proxmox' OR (category = 'database' AND pattern_type LIKE 'proxmox%'))
                """,
                (new_pattern, pattern_id),
            )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted" if updated else "rejected",
                    "message": "✅ Паттерн обновлён." if updated else "❌ Паттерн не найден.",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_patterns_proxmox"},
                        {"label": "↩️ Назад", "action": "settings_patterns_proxmox"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "settings_db_view_all":
        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
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
            menu_options.append(
                {
                    "label": f"➕ Добавить БД в {str(category).upper()}",
                    "action": f"settings_db_add_db_{encoded_category}",
                }
            )
            for db_key in sorted(databases.keys()):
                encoded_db_key = quote(str(db_key), safe="")
                menu_options.extend(
                    [
                        {
                            "label": f"✏️ {str(category).upper()}: {str(db_key)}",
                            "action": f"settings_db_edit_db_{encoded_category}__{encoded_db_key}",
                        },
                        {
                            "label": f"🗑️ {str(category).upper()}: {str(db_key)}",
                            "action": f"settings_db_delete_db_{encoded_category}__{encoded_db_key}",
                        },
                    ]
                )
            menu_options.append(
                {
                    "label": f"🗑️ Удалить категорию {str(category).upper()}",
                    "action": f"settings_db_delete_{encoded_category}",
                }
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_db_add_category|"):
        payload = action.split("|", 1)[1].strip()
        category = unquote(payload).strip().lower()
        if not category:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Категория не указана.",
                        "menu_options": [{"label": "↩️ Назад", "action": "settings_db_main"}],
                    }
                ),
                200,
            )

        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
        if not isinstance(db_config, dict):
            db_config = {}
        if category in db_config:
            message = f"ℹ️ Категория «{category}» уже существует."
        else:
            db_config[category] = {}
            settings_manager.set_setting("DATABASE_CONFIG", db_config, "database", data_type="auto")
            message = f"✅ Категория «{category}» добавлена."
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": [
                        {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "settings_db_delete_category":
        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
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
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": (
                        "Выбери категорию БД для удаления."
                        if categories
                        else "❌ Категории БД не найдены."
                    ),
                    "menu_options": menu_options
                    + [
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_db_add_db_submit|"):
        parts = action.split("|")
        category = unquote(parts[1]).strip().lower() if len(parts) > 1 else ""
        db_key = unquote(parts[2]).strip() if len(parts) > 2 else ""
        db_name = unquote(parts[3]).strip() if len(parts) > 3 else ""
        if not category or not db_key:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Укажи категорию и ключ БД.",
                        "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
                    }
                ),
                200,
            )
        if not db_name:
            db_name = db_key

        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
        if not isinstance(db_config, dict):
            db_config = {}
        if category not in db_config or not isinstance(db_config.get(category), dict):
            db_config[category] = {}
        db_config[category][db_key] = db_name
        settings_manager.set_setting("DATABASE_CONFIG", db_config, "database", data_type="auto")
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"✅ БД «{db_key}» сохранена в категории «{category}».",
                    "menu_options": [
                        {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_db_edit_db_submit|"):
        parts = action.split("|")
        category = unquote(parts[1]).strip().lower() if len(parts) > 1 else ""
        old_key = unquote(parts[2]).strip() if len(parts) > 2 else ""
        new_key = unquote(parts[3]).strip() if len(parts) > 3 else ""
        new_name = unquote(parts[4]).strip() if len(parts) > 4 else ""
        if not category or not old_key or not new_key:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Недостаточно данных для редактирования БД.",
                        "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
                    }
                ),
                200,
            )

        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
        if not isinstance(db_config, dict):
            db_config = {}
        category_map = db_config.get(category) if isinstance(db_config.get(category), dict) else {}
        if old_key not in category_map:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ База не найдена в указанной категории.",
                        "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
                    }
                ),
                200,
            )
        value = new_name or category_map.get(old_key) or new_key
        if old_key != new_key:
            category_map.pop(old_key, None)
        category_map[new_key] = value
        db_config[category] = category_map
        settings_manager.set_setting("DATABASE_CONFIG", db_config, "database", data_type="auto")
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"✅ БД «{old_key}» обновлена.",
                    "menu_options": [
                        {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_db_delete_db_"):
        raw = action.replace("settings_db_delete_db_", "", 1)
        parts = raw.split("__", 1)
        category = unquote(parts[0]).strip().lower() if parts else ""
        db_key = unquote(parts[1]).strip() if len(parts) > 1 else ""
        if not category or not db_key:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Не удалось определить категорию/БД для удаления.",
                        "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
                    }
                ),
                200,
            )
        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
        if not isinstance(db_config, dict):
            db_config = {}
        category_map = db_config.get(category) if isinstance(db_config.get(category), dict) else {}
        removed = category_map.pop(db_key, None)
        db_config[category] = category_map
        settings_manager.set_setting("DATABASE_CONFIG", db_config, "database", data_type="auto")
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"{'✅' if removed is not None else 'ℹ️'} БД «{db_key}» {'удалена' if removed is not None else 'не найдена'}.",
                    "menu_options": [
                        {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_db_delete_") and action != "settings_db_delete_category":
        encoded_category = action.replace("settings_db_delete_", "", 1)
        category = unquote(encoded_category).strip().lower()
        if not category:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "rejected",
                        "message": "❌ Категория для удаления не указана.",
                        "menu_options": [{"label": "↩️ Назад", "action": "settings_db_view_all"}],
                    }
                ),
                200,
            )
        db_config = settings_manager.get_setting("DATABASE_CONFIG", {})
        if not isinstance(db_config, dict):
            db_config = {}
        removed = db_config.pop(category, None)
        settings_manager.set_setting("DATABASE_CONFIG", db_config, "database", data_type="auto")
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"{'✅' if removed is not None else 'ℹ️'} Категория «{category}» {'удалена' if removed is not None else 'не найдена'}.",
                    "menu_options": [
                        {"label": "📋 Просмотр всех БД", "action": "settings_db_view_all"},
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

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
            menu_options.extend(
                [
                    {
                        "label": f"✏️ {index}. {pattern_type} — {pattern_value}",
                        "action": f"settings_proxmox_pattern_edit_{pattern_id}",
                    },
                    {
                        "label": f"🗑️ {index}. {pattern_type}",
                        "action": f"settings_proxmox_pattern_delete_{pattern_id}",
                    },
                    {
                        "label": f"{toggle_label} {index}. {pattern_type}",
                        "action": f"settings_proxmox_pattern_toggle_{pattern_id}",
                    },
                ]
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {
                            "label": "➕ Добавить паттерн БД",
                            "action": "settings_proxmox_pattern_add|database|subject|",
                        },
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": "settings_ext_backup_db"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

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
            menu_options.extend(
                [
                    {
                        "label": f"✏️ {index}. {pattern_type} — {pattern_value}",
                        "action": f"settings_proxmox_pattern_edit_{pattern_id}",
                    },
                    {
                        "label": f"🗑️ {index}. {pattern_type}",
                        "action": f"settings_proxmox_pattern_delete_{pattern_id}",
                    },
                    {
                        "label": f"{toggle_label} {index}. {pattern_type}",
                        "action": f"settings_proxmox_pattern_toggle_{pattern_id}",
                    },
                ]
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {
                            "label": "➕ Добавить паттерн ZFS",
                            "action": "settings_proxmox_pattern_add|zfs|subject|",
                        },
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": "settings_zfs"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "settings_zfs_list":
        zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
        zfs_servers = zfs_servers if isinstance(zfs_servers, dict) else {}

        lines = ["📋 ZFS серверы", ""]
        if not zfs_servers:
            lines.append("❌ Серверы не настроены.")
        else:
            for server_name in sorted(zfs_servers.keys()):
                server_value = zfs_servers.get(server_name)
                enabled = True
                if isinstance(server_value, dict):
                    enabled = bool(server_value.get("enabled", True))
                lines.append(f"{'🟢' if enabled else '🔴'} {server_name}")

        menu_options = []
        for server_name in sorted(zfs_servers.keys()):
            encoded_server_name = quote(str(server_name), safe="")
            server_value = zfs_servers.get(server_name)
            enabled = True
            if isinstance(server_value, dict):
                enabled = bool(server_value.get("enabled", True))
            toggle_label = "⛔️ Отключить" if enabled else "✅ Включить"
            menu_options.extend(
                [
                    {
                        "label": f"✏️ {server_name}",
                        "action": f"settings_zfs_edit_name_{encoded_server_name}",
                    },
                    {
                        "label": f"🗑️ {server_name}",
                        "action": f"settings_zfs_delete_{encoded_server_name}",
                    },
                    {
                        "label": f"{toggle_label} {server_name}",
                        "action": f"settings_zfs_toggle_{encoded_server_name}",
                    },
                ]
            )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "\n".join(lines),
                    "menu_options": menu_options
                    + [
                        {"label": "➕ Добавить сервер", "action": "settings_zfs_add"},
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": "settings_zfs"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "settings_zfs_add" or action.startswith("settings_zfs_add|"):
        payload = raw_action.split("|", 1)
        server_name = unquote(payload[1]).strip() if len(payload) > 1 else ""
        if not server_name:
            return (
                jsonify(
                    {
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
                    }
                ),
                200,
            )

        zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        if server_name in zfs_servers:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted",
                        "message": f"❌ ZFS-сервер «{server_name}» уже существует.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_zfs_list"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        zfs_servers[server_name] = {"enabled": True}
        settings_manager.set_setting("ZFS_SERVERS", zfs_servers, "zfs")
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"✅ ZFS-сервер «{server_name}» добавлен.",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_zfs_list"},
                        {"label": "↩️ Назад", "action": "settings_zfs"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "supplier_stock_download":
        supplier_config = extension_manager.load_extension_config("supplier_stock_files")
        download_settings = (
            supplier_config.get("download", {}) if isinstance(supplier_config, dict) else {}
        )
        sources = (
            download_settings.get("sources", []) if isinstance(download_settings, dict) else []
        )
        source_count = len(sources) if isinstance(sources, list) else 0
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": (
                        "🌐 Скачивание файлов остатков поставщиков\n\n"
                        f"Источников: {source_count}\n\n"
                        "Выберите раздел:"
                    ),
                    "menu_options": [
                        {"label": "📦 Источники файлов", "action": "supplier_stock_sources"},
                        {"label": "⏱ Расписание", "action": "supplier_stock_schedule"},
                        {"label": "🖥 Ресурсы", "action": "supplier_stock_resources"},
                        {"label": "🗄 FTP", "action": "supplier_stock_ftp"},
                        {"label": "⚙️ Обработка", "action": "supplier_stock_processing"},
                        {"label": "↩️ Назад", "action": "settings_ext_supplier_stock"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if (
        action == "supplier_stock_sources"
        or action.startswith("supplier_stock_source_add|")
        or action.startswith("supplier_stock_source_update|")
        or action.startswith("supplier_stock_source_edit|")
        or action.startswith("supplier_stock_source_toggle|")
        or action.startswith("supplier_stock_source_unpack|")
        or action.startswith("supplier_stock_source_delete_confirm|")
        or action.startswith("supplier_stock_source_delete|")
    ):
        config = get_supplier_stock_config()
        sources = (config.get("download", {}) or {}).get("sources", []) or []
        notice = ""
        pending_delete_id = ""
        editing_id = ""
        if action.startswith("supplier_stock_source_add|"):
            fields = {}
            for pair in raw_action.split("|", 1)[1].split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    fields[key.strip().lower()] = unquote(value)
            name = (fields.get("name") or "").strip()
            url = (fields.get("url") or "").strip()
            output_name = (fields.get("output") or "").strip()
            method = (fields.get("method") or "http").strip() or "http"
            unpack = (fields.get("unpack") or "").strip().lower() in ("1", "true", "yes", "on")
            if not name or not url or not output_name:
                notice = "❌ Заполните название, URL и имя файла назначения\n\n"
            else:
                base_id = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_") or "source"
                existing = {str(s.get("id")) for s in sources if s.get("id")}
                new_id = base_id
                suffix = 2
                while new_id in existing:
                    new_id = f"{base_id}_{suffix}"
                    suffix += 1
                sources.append(
                    {
                        "id": new_id,
                        "name": name,
                        "url": url,
                        "output_name": output_name,
                        "method": method,
                        "enabled": True,
                        "unpack_archive": unpack,
                    }
                )
                config.setdefault("download", {})["sources"] = sources
                save_supplier_stock_config(config)
                notice = f"✅ Источник «{name}» добавлен\n\n"
        elif action.startswith("supplier_stock_source_toggle|"):
            target = raw_action.split("|", 1)[1].strip()
            for source in sources:
                if str(source.get("id")) == target:
                    source["enabled"] = not source.get("enabled", True)
                    notice = (
                        f"{'✅ Включён' if source['enabled'] else '⛔️ Выключен'} "
                        f"источник «{source.get('name') or target}»\n\n"
                    )
                    break
            config.setdefault("download", {})["sources"] = sources
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_source_unpack|"):
            target = raw_action.split("|", 1)[1].strip()
            for source in sources:
                if str(source.get("id")) == target:
                    source["unpack_archive"] = not source.get("unpack_archive", False)
                    notice = (
                        f"📦 Распаковка архива для «{source.get('name') or target}»: "
                        f"{'вкл' if source['unpack_archive'] else 'выкл'}\n\n"
                    )
                    break
            config.setdefault("download", {})["sources"] = sources
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_source_update|"):
            parts = raw_action.split("|", 2)
            target = parts[1].strip() if len(parts) > 1 else ""
            fields = {}
            if len(parts) > 2:
                for pair in parts[2].split("&"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        fields[key.strip().lower()] = unquote(value)
            updated = None
            for source in sources:
                if str(source.get("id")) == target:
                    updated = source
                    for field_key, src_key in (
                        ("name", "name"),
                        ("url", "url"),
                        ("output", "output_name"),
                        ("method", "method"),
                    ):
                        value = (fields.get(field_key) or "").strip()
                        if value:
                            source[src_key] = value
                    break
            config.setdefault("download", {})["sources"] = sources
            save_supplier_stock_config(config)
            notice = (
                f"✅ Источник «{updated.get('name') or target}» обновлён\n\n"
                if updated
                else "ℹ️ Источник не найден\n\n"
            )
        elif action.startswith("supplier_stock_source_edit|"):
            candidate = raw_action.split("|", 1)[1].strip()
            if any(str(s.get("id")) == candidate for s in sources):
                editing_id = candidate
            else:
                notice = "ℹ️ Источник не найден\n\n"
        elif action.startswith("supplier_stock_source_delete_confirm|"):
            target = raw_action.split("|", 1)[1].strip()
            before = len(sources)
            sources = [s for s in sources if str(s.get("id")) != target]
            config.setdefault("download", {})["sources"] = sources
            save_supplier_stock_config(config)
            notice = (
                "🗑 Источник удалён\n\n" if len(sources) < before else "ℹ️ Источник не найден\n\n"
            )
        elif action.startswith("supplier_stock_source_delete|"):
            pending_delete_id = raw_action.split("|", 1)[1].strip()

        if pending_delete_id:
            target_source = next(
                (s for s in sources if str(s.get("id")) == pending_delete_id), None
            )
            name = str((target_source or {}).get("name") or pending_delete_id)
            message = (
                f"🗑 Удалить источник «{name}»?\n\n"
                "Действие необратимо — настройки источника будут потеряны."
            )
            menu_options = [
                {
                    "label": f"⚠️ Да, удалить «{name[:24]}»",
                    "action": f"supplier_stock_source_delete_confirm|{pending_delete_id}",
                },
                {"label": "↩️ Отмена", "action": "supplier_stock_sources"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        elif editing_id:
            src = next(s for s in sources if str(s.get("id")) == editing_id)
            message = (
                f"{notice}✏️ Редактирование источника «{src.get('name') or editing_id}»\n\n"
                "Текущие значения:\n"
                f"• Название: {src.get('name') or '—'}\n"
                f"• URL: {src.get('url') or 'не задан'}\n"
                f"• Файл: {src.get('output_name') or 'не задано'}\n"
                f"• Метод: {src.get('method') or 'http'}\n\n"
                "Заполните только те поля, которые нужно изменить "
                "(пустые поля останутся без изменений)."
            )
            menu_options = [
                {"label": "↩️ К списку источников", "action": "supplier_stock_sources"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        else:
            lines = [f"{notice}📦 Источники файлов остатков", ""]
            if not sources:
                lines.append("⚪️ Источники не настроены.")
            else:
                for idx, source in enumerate(sources, start=1):
                    name = source.get("name") or source.get("id") or f"Источник {idx}"
                    url = source.get("url") or "URL не задан"
                    output_name = source.get("output_name") or "не задано"
                    method = source.get("method") or "http"
                    status = "🟢 вкл" if source.get("enabled", True) else "🔴 выкл"
                    unpack = "да" if source.get("unpack_archive", False) else "нет"
                    lines.append(f"{idx}. {status} {name}")
                    lines.append(f"    URL: {url}")
                    lines.append(f"    Файл: {output_name}")
                    lines.append(f"    Метод: {method} · Распаковка: {unpack}")
            lines.append("")
            lines.append(
                "Базовые поля (название, URL, файл, метод) редактируются здесь; "
                "поиск ссылки, переменные, авторизация и обработка — пока в Telegram-боте."
            )
            message = "\n".join(lines)
            menu_options = []
            for source in sources:
                sid = str(source.get("id") or "").strip()
                if not sid:
                    continue
                name = str(source.get("name") or sid)
                enabled = source.get("enabled", True)
                unpack = source.get("unpack_archive", False)
                toggle_label = (
                    f"{'⛔️ Выключить' if enabled else '✅ Включить'} {name[:18]}"
                )
                unpack_label = (
                    f"📦 Распаковка {'выкл' if unpack else 'вкл'}: {name[:14]}"
                )
                menu_options.append(
                    {"label": f"✏️ Изменить {name[:18]}", "action": f"supplier_stock_source_edit|{sid}"}
                )
                menu_options.append(
                    {"label": toggle_label, "action": f"supplier_stock_source_toggle|{sid}"}
                )
                menu_options.append(
                    {"label": unpack_label, "action": f"supplier_stock_source_unpack|{sid}"}
                )
                menu_options.append(
                    {"label": f"🗑 Удалить {name[:18]}", "action": f"supplier_stock_source_delete|{sid}"}
                )
            menu_options.append({"label": "↩️ Назад", "action": "supplier_stock_download"})
            menu_options.append({"label": "✖️ Закрыть", "action": "close"})
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

        supplier_config = extension_manager.load_extension_config("supplier_stock_files")
        mail_settings = supplier_config.get("mail", {}) if isinstance(supplier_config, dict) else {}
        sources = mail_settings.get("sources", []) if isinstance(mail_settings, dict) else []
        source_count = len(sources) if isinstance(sources, list) else 0
        return (
            jsonify(
                {
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
                        {
                            "label": "🗓 Отчёты (download)",
                            "action": "supplier_stock_reports_download",
                        },
                        {"label": "🗓 Отчёты (mail)", "action": "supplier_stock_reports_mail"},
                        {"label": "↩️ Назад", "action": "settings_ext_supplier_stock"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "supplier_stock_report_period" or action.startswith(
        "supplier_stock_set_period|"
    ):
        config = get_supplier_stock_config()
        notice = ""
        if action.startswith("supplier_stock_set_period|"):
            raw_value = raw_action.split("|", 1)[1].strip()
            try:
                days = int(raw_value)
                if not (1 <= days <= 365):
                    raise ValueError
                config.setdefault("reporting", {})["period_days"] = days
                save_supplier_stock_config(config)
                notice = f"✅ Период отчётов: {days} дн.\n\n"
            except (TypeError, ValueError):
                notice = "❌ Введите целое число дней от 1 до 365\n\n"
        try:
            current_days = int((config.get("reporting", {}) or {}).get("period_days", 7) or 7)
        except (TypeError, ValueError):
            current_days = 7
        message = (
            f"{notice}🗓 Период отчётов остатков поставщиков\n\n"
            f"Текущий период: {current_days} дн.\n\n"
            "Период задаёт, за сколько последних дней дашборд берёт последний "
            "запуск по каждому поставщику. Выберите пресет или введите своё "
            "число дней в поле ниже."
        )
        menu_options = []
        for preset in (1, 3, 7, 14, 30):
            mark = "✅ " if preset == current_days else ""
            menu_options.append(
                {"label": f"{mark}{preset} дн.", "action": f"supplier_stock_set_period|{preset}"}
            )
        menu_options.append({"label": "↩️ Назад", "action": "settings_ext_supplier_stock"})
        menu_options.append({"label": "✖️ Закрыть", "action": "close"})
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if (
        action == "supplier_stock_schedule"
        or action == "supplier_stock_sched_toggle"
        or action.startswith("supplier_stock_sched_time|")
    ):
        config = get_supplier_stock_config()
        schedule = (config.get("download", {}) or {}).get("schedule", {}) or {}
        notice = ""
        if action == "supplier_stock_sched_toggle":
            schedule["enabled"] = not bool(schedule.get("enabled", False))
            config.setdefault("download", {})["schedule"] = schedule
            save_supplier_stock_config(config)
            notice = (
                "✅ Плановое скачивание включено\n\n"
                if schedule["enabled"]
                else "⏸ Плановое скачивание выключено\n\n"
            )
        elif action.startswith("supplier_stock_sched_time|"):
            raw_value = unquote(raw_action.split("|", 1)[1]).strip()
            times = parse_supplier_stock_schedule_times(raw_value)
            if not times:
                notice = (
                    "❌ Неверный формат времени. Используйте HH:MM, "
                    "разделители: пробел, запятая или ;\n\n"
                )
            else:
                schedule["time"] = ", ".join(times)
                config.setdefault("download", {})["schedule"] = schedule
                save_supplier_stock_config(config)
                notice = f"✅ Время скачивания: {', '.join(times)}\n\n"
        enabled = bool(schedule.get("enabled", False))
        time_text = str(schedule.get("time") or "—")
        status = "🟢 включено" if enabled else "⚪️ выключено"
        message = (
            f"{notice}⏱ Расписание скачивания остатков\n\n"
            f"Плановое скачивание: {status}\n"
            f"Время запуска: {time_text}\n\n"
            "Можно указать несколько точек через запятую (например 06:00, 18:00). "
            "Введите новое время в поле ниже."
        )
        toggle_label = (
            "⏸ Выключить плановое скачивание"
            if enabled
            else "▶️ Включить плановое скачивание"
        )
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": [
                        {"label": toggle_label, "action": "supplier_stock_sched_toggle"},
                        {"label": "↩️ Назад", "action": "supplier_stock_download"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if (
        action == "supplier_stock_ftp"
        or action == "supplier_stock_ftp_clear_password"
        or action.startswith("supplier_stock_ftp_set_host|")
        or action.startswith("supplier_stock_ftp_set_login|")
        or action.startswith("supplier_stock_ftp_set_password|")
    ):
        config = get_supplier_stock_config()
        ftp_settings = config.get("ftp_ork", {}) or {}
        notice = ""
        if action.startswith("supplier_stock_ftp_set_host|"):
            value = unquote(raw_action.split("|", 1)[1]).strip()
            ftp_settings["host"] = value
            config["ftp_ork"] = ftp_settings
            save_supplier_stock_config(config)
            notice = (
                f"✅ HOST FTP: {value}\n\n" if value else "🗑 HOST FTP очищен\n\n"
            )
        elif action.startswith("supplier_stock_ftp_set_login|"):
            value = unquote(raw_action.split("|", 1)[1]).strip()
            ftp_settings["login"] = value
            config["ftp_ork"] = ftp_settings
            save_supplier_stock_config(config)
            notice = (
                f"✅ Логин FTP: {value}\n\n" if value else "🗑 Логин FTP очищен\n\n"
            )
        elif action.startswith("supplier_stock_ftp_set_password|"):
            # Пароль не нормализуем strip'ом по краям — он может содержать
            # значимые пробелы; но ведущие/замыкающие пробелы из ввода убираем.
            value = unquote(raw_action.split("|", 1)[1])
            ftp_settings["password"] = value
            config["ftp_ork"] = ftp_settings
            save_supplier_stock_config(config)
            notice = "✅ Пароль FTP сохранён\n\n" if value else "🗑 Пароль FTP очищен\n\n"
        elif action == "supplier_stock_ftp_clear_password":
            ftp_settings["password"] = ""
            config["ftp_ork"] = ftp_settings
            save_supplier_stock_config(config)
            notice = "🗑 Пароль FTP очищен\n\n"
        host_text = ftp_settings.get("host") or "не задано"
        login_text = ftp_settings.get("login") or "не задано"
        password_text = "задано" if ftp_settings.get("password") else "не задано"
        message = (
            f"{notice}🗄 FTP ОРК — настройки\n\n"
            f"HOST FTP: {host_text}\n"
            f"Логин FTP: {login_text}\n"
            f"Пароль FTP: {password_text}\n\n"
            "Введите новые значения в полях ниже. Пароль не отображается."
        )
        menu_options = [
            {"label": "🗑 Очистить пароль", "action": "supplier_stock_ftp_clear_password"},
            {"label": "↩️ Назад", "action": "supplier_stock_download"},
            {"label": "✖️ Закрыть", "action": "close"},
        ]
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if action.startswith("supplier_stock_source_hde_settings|") or action.startswith(
        "supplier_stock_source_hde_field|"
    ):
        config = get_supplier_stock_config()
        sources = (config.get("download", {}) or {}).get("sources", []) or []
        notice = ""
        parts = raw_action.split("|")
        source_id = parts[1].strip() if len(parts) > 1 else ""
        source = next((s for s in sources if str(s.get("id")) == source_id), None)
        if source and action.startswith("supplier_stock_source_hde_field|"):
            field = parts[2].strip() if len(parts) > 2 else ""
            if len(parts) > 3:
                value = unquote(parts[3])
                hde = source.setdefault("hde_api", {})
                valid_fields = {"base_url", "basic_user", "basic_pass", "company_inn", "smsh_secret", "output_name"}
                if field in valid_fields:
                    hde[field] = value.strip() if field not in ("basic_pass", "smsh_secret") else value
                    notice = f"✅ Сохранено: {field}\n\n"
                elif field == "fetch_endpoints":
                    valid_ep = {"stock", "price", "transit"}
                    chosen = [ep.strip() for ep in re.split(r"[,\s]+", value) if ep.strip() in valid_ep]
                    if chosen:
                        hde["fetch_endpoints"] = chosen
                        notice = f"✅ Запросы: {', '.join(chosen)}\n\n"
                    else:
                        notice = "❌ Допустимые значения: stock, price, transit\n\n"
                config.setdefault("download", {})["sources"] = sources
                save_supplier_stock_config(config)
        if not source:
            notice = f"❌ Источник {source_id!r} не найден\n\n"
            hde = {}
        else:
            hde = source.get("hde_api") or {}
        base_url = hde.get("base_url") or "не задано"
        basic_user = hde.get("basic_user") or "не задано"
        pass_state = "задано" if hde.get("basic_pass") else "не задано"
        company_inn = hde.get("company_inn") or "не задано"
        secret_state = "задано" if hde.get("smsh_secret") else "не задано"
        endpoints = ", ".join(hde.get("fetch_endpoints") or ["stock", "price", "transit"])
        output_name = hde.get("output_name") or "не задано"
        also_csv = "вкл" if hde.get("also_csv") else "выкл"
        message = (
            f"{notice}⚙️ HD-Electric API\n\n"
            f"• URL: {base_url}\n"
            f"• Логин: {basic_user}\n"
            f"• Пароль: {pass_state}\n"
            f"• ИНН/КПП: {company_inn}\n"
            f"• Секрет: {secret_state}\n"
            f"• Запросы: {endpoints}\n"
            f"• Файл: {output_name}\n"
            f"• CSV: {also_csv}\n\n"
            "Нажмите на поле ниже для редактирования."
        )
        menu_options = [
            {"label": "🔗 URL", "action": f"supplier_stock_source_hde_field|{source_id}|base_url"},
            {"label": "👤 Логин", "action": f"supplier_stock_source_hde_field|{source_id}|basic_user"},
            {"label": "🔐 Пароль", "action": f"supplier_stock_source_hde_field|{source_id}|basic_pass"},
            {"label": "🏢 ИНН/КПП", "action": f"supplier_stock_source_hde_field|{source_id}|company_inn"},
            {"label": "🗝️ Секрет", "action": f"supplier_stock_source_hde_field|{source_id}|smsh_secret"},
            {"label": "📡 Запросы", "action": f"supplier_stock_source_hde_field|{source_id}|fetch_endpoints"},
            {"label": "📄 Файл", "action": f"supplier_stock_source_hde_field|{source_id}|output_name"},
            {"label": "↩️ Назад", "action": "supplier_stock_sources"},
            {"label": "✖️ Закрыть", "action": "close"},
        ]
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if (
        action == "supplier_stock_resources"
        or action.startswith("supplier_stock_resource_add|")
        or action.startswith("supplier_stock_resource_update|")
        or action.startswith("supplier_stock_resource_edit|")
        or action.startswith("supplier_stock_resource_toggle|")
        or action.startswith("supplier_stock_resource_delete_confirm|")
        or action.startswith("supplier_stock_resource_delete|")
    ):
        config = get_supplier_stock_config()
        resources = config.get("resources", []) or []
        notice = ""
        pending_delete_id = ""
        editing_id = ""
        if action.startswith("supplier_stock_resource_add|"):
            fields = {}
            for pair in raw_action.split("|", 1)[1].split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    fields[key.strip().lower()] = unquote(value)
            name = (fields.get("name") or "").strip()
            unc_path = (fields.get("unc") or "").strip()
            login = (fields.get("login") or "").strip()
            password = fields.get("password") or ""
            if not name or not unc_path:
                notice = "❌ Заполните название и UNC-путь\n\n"
            else:
                base_id = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_") or "resource"
                existing = {str(r.get("id")) for r in resources if r.get("id")}
                new_id = base_id
                suffix = 2
                while new_id in existing:
                    new_id = f"{base_id}_{suffix}"
                    suffix += 1
                new_resource = {
                    "id": new_id,
                    "name": name,
                    "unc_path": unc_path,
                    "enabled": True,
                }
                if login:
                    new_resource["login"] = login
                if password:
                    new_resource["password"] = password
                resources.append(new_resource)
                config["resources"] = resources
                save_supplier_stock_config(config)
                notice = f"✅ Ресурс «{name}» добавлен\n\n"
        elif action.startswith("supplier_stock_resource_toggle|"):
            target = raw_action.split("|", 1)[1].strip()
            for resource in resources:
                if str(resource.get("id")) == target:
                    resource["enabled"] = not resource.get("enabled", True)
                    notice = (
                        f"{'✅ Включён' if resource['enabled'] else '⛔️ Выключен'} "
                        f"ресурс «{resource.get('name') or target}»\n\n"
                    )
                    break
            config["resources"] = resources
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_resource_update|"):
            parts = raw_action.split("|", 2)
            target = parts[1].strip() if len(parts) > 1 else ""
            fields = {}
            if len(parts) > 2:
                for pair in parts[2].split("&"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        fields[key.strip().lower()] = unquote(value)
            updated = None
            for resource in resources:
                if str(resource.get("id")) == target:
                    updated = resource
                    if (fields.get("name") or "").strip():
                        resource["name"] = fields["name"].strip()
                    if (fields.get("unc") or "").strip():
                        resource["unc_path"] = fields["unc"].strip()
                    if (fields.get("login") or "").strip():
                        resource["login"] = fields["login"].strip()
                    # Пароль пишем только если задан (пустой = без изменений).
                    if fields.get("password"):
                        resource["password"] = fields["password"]
                    break
            config["resources"] = resources
            save_supplier_stock_config(config)
            notice = (
                f"✅ Ресурс «{updated.get('name') or target}» обновлён\n\n"
                if updated
                else "ℹ️ Ресурс не найден\n\n"
            )
        elif action.startswith("supplier_stock_resource_edit|"):
            candidate = raw_action.split("|", 1)[1].strip()
            if any(str(r.get("id")) == candidate for r in resources):
                editing_id = candidate
            else:
                notice = "ℹ️ Ресурс не найден\n\n"
        elif action.startswith("supplier_stock_resource_delete_confirm|"):
            target = raw_action.split("|", 1)[1].strip()
            before = len(resources)
            resources = [r for r in resources if str(r.get("id")) != target]
            config["resources"] = resources
            save_supplier_stock_config(config)
            notice = (
                "🗑 Ресурс удалён\n\n" if len(resources) < before else "ℹ️ Ресурс не найден\n\n"
            )
        elif action.startswith("supplier_stock_resource_delete|"):
            pending_delete_id = raw_action.split("|", 1)[1].strip()

        if pending_delete_id:
            target_resource = next(
                (r for r in resources if str(r.get("id")) == pending_delete_id), None
            )
            name = str((target_resource or {}).get("name") or pending_delete_id)
            message = (
                f"🗑 Удалить ресурс «{name}»?\n\n"
                "Действие необратимо — настройки ресурса будут потеряны."
            )
            menu_options = [
                {
                    "label": f"⚠️ Да, удалить «{name[:24]}»",
                    "action": f"supplier_stock_resource_delete_confirm|{pending_delete_id}",
                },
                {"label": "↩️ Отмена", "action": "supplier_stock_resources"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        elif editing_id:
            res = next(r for r in resources if str(r.get("id")) == editing_id)
            message = (
                f"{notice}✏️ Редактирование ресурса «{res.get('name') or editing_id}»\n\n"
                "Текущие значения:\n"
                f"• Название: {res.get('name') or '—'}\n"
                f"• UNC: {res.get('unc_path') or 'не задан'}\n"
                f"• Логин: {res.get('login') or 'не задан'}\n"
                f"• Пароль: {'задан' if res.get('password') else 'не задан'}\n\n"
                "Заполните только те поля, которые нужно изменить "
                "(пустые поля останутся без изменений)."
            )
            menu_options = [
                {"label": "↩️ К списку ресурсов", "action": "supplier_stock_resources"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        else:
            lines = [f"{notice}🖥 Ресурсы выгрузки остатков", ""]
            if not resources:
                lines.append("⚪️ Ресурсы не настроены.")
            else:
                for idx, resource in enumerate(resources, start=1):
                    name = resource.get("name") or resource.get("id") or f"Ресурс {idx}"
                    unc = resource.get("unc_path") or "—"
                    login = resource.get("login") or "—"
                    status = "🟢 вкл" if resource.get("enabled", True) else "🔴 выкл"
                    lines.append(f"{idx}. {status} {name}")
                    lines.append(f"    UNC: {unc}")
                    lines.append(f"    Логин: {login}")
            lines.append("")
            lines.append("Базовые поля ресурса (название, UNC, логин, пароль) редактируются здесь.")
            message = "\n".join(lines)
            menu_options = []
            for resource in resources:
                rid = str(resource.get("id") or "").strip()
                if not rid:
                    continue
                name = str(resource.get("name") or rid)
                enabled = resource.get("enabled", True)
                toggle_label = (
                    f"{'⛔️ Выключить' if enabled else '✅ Включить'} {name[:20]}"
                )
                menu_options.append(
                    {"label": f"✏️ Изменить {name[:20]}", "action": f"supplier_stock_resource_edit|{rid}"}
                )
                menu_options.append(
                    {"label": toggle_label, "action": f"supplier_stock_resource_toggle|{rid}"}
                )
                menu_options.append(
                    {"label": f"🗑 Удалить {name[:20]}", "action": f"supplier_stock_resource_delete|{rid}"}
                )
            menu_options.append({"label": "↩️ Назад", "action": "supplier_stock_download"})
            menu_options.append({"label": "✖️ Закрыть", "action": "close"})
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if (
        action == "supplier_stock_mail_sources"
        or action.startswith("supplier_stock_mail_source_add|")
        or action.startswith("supplier_stock_mail_source_update|")
        or action.startswith("supplier_stock_mail_source_edit|")
        or action.startswith("supplier_stock_mail_source_toggle|")
        or action.startswith("supplier_stock_mail_source_unpack|")
        or action.startswith("supplier_stock_mail_source_delete_confirm|")
        or action.startswith("supplier_stock_mail_source_delete|")
    ):
        config = get_supplier_stock_config()
        sources = (config.get("mail", {}) or {}).get("sources", []) or []
        notice = ""
        pending_delete_id = ""
        editing_id = ""
        if action.startswith("supplier_stock_mail_source_add|"):
            fields = {}
            for pair in raw_action.split("|", 1)[1].split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    fields[key.strip().lower()] = unquote(value)
            name = (fields.get("name") or "").strip()
            output_template = (fields.get("output") or "").strip()
            try:
                expected = int((fields.get("expected") or "1").strip())
                if expected <= 0:
                    expected = 1
            except (TypeError, ValueError):
                expected = 1
            unpack = (fields.get("unpack") or "").strip().lower() in ("1", "true", "yes", "on")
            if not name or not output_template:
                notice = "❌ Заполните название и шаблон имени выходного файла\n\n"
            else:
                base_id = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_") or "source"
                existing = {str(s.get("id")) for s in sources if s.get("id")}
                new_id = base_id
                suffix = 2
                while new_id in existing:
                    new_id = f"{base_id}_{suffix}"
                    suffix += 1
                new_rule = {
                    "id": new_id,
                    "name": name,
                    "expected_attachments": expected,
                    "output_template": output_template,
                    "enabled": True,
                    "unpack_archive": unpack,
                }
                # Необязательные паттерны добавляем только если заданы — иначе
                # пустые поля означают «принимать любые».
                for field_key, rule_key in (
                    ("sender", "sender_pattern"),
                    ("subject", "subject_pattern"),
                    ("filename", "filename_pattern"),
                ):
                    value = (fields.get(field_key) or "").strip()
                    if value:
                        new_rule[rule_key] = value
                sources.append(new_rule)
                config.setdefault("mail", {})["sources"] = sources
                save_supplier_stock_config(config)
                notice = f"✅ Правило «{name}» добавлено\n\n"
        elif action.startswith("supplier_stock_mail_source_toggle|"):
            target = raw_action.split("|", 1)[1].strip()
            for source in sources:
                if str(source.get("id")) == target:
                    source["enabled"] = not source.get("enabled", True)
                    notice = (
                        f"{'✅ Включено' if source['enabled'] else '⛔️ Выключено'} "
                        f"правило «{source.get('name') or target}»\n\n"
                    )
                    break
            config.setdefault("mail", {})["sources"] = sources
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_mail_source_unpack|"):
            target = raw_action.split("|", 1)[1].strip()
            for source in sources:
                if str(source.get("id")) == target:
                    source["unpack_archive"] = not source.get("unpack_archive", False)
                    notice = (
                        f"📦 Распаковка архива для «{source.get('name') or target}»: "
                        f"{'вкл' if source['unpack_archive'] else 'выкл'}\n\n"
                    )
                    break
            config.setdefault("mail", {})["sources"] = sources
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_mail_source_update|"):
            parts = raw_action.split("|", 2)
            target = parts[1].strip() if len(parts) > 1 else ""
            fields = {}
            if len(parts) > 2:
                for pair in parts[2].split("&"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        fields[key.strip().lower()] = unquote(value)
            updated = None
            for source in sources:
                if str(source.get("id")) == target:
                    updated = source
                    if (fields.get("name") or "").strip():
                        source["name"] = fields["name"].strip()
                    if (fields.get("output") or "").strip():
                        source["output_template"] = fields["output"].strip()
                    expected_raw = (fields.get("expected") or "").strip()
                    if expected_raw:
                        try:
                            expected_value = int(expected_raw)
                            if expected_value > 0:
                                source["expected_attachments"] = expected_value
                        except (TypeError, ValueError):
                            pass
                    for field_key, rule_key in (
                        ("sender", "sender_pattern"),
                        ("subject", "subject_pattern"),
                        ("filename", "filename_pattern"),
                    ):
                        value = (fields.get(field_key) or "").strip()
                        if value:
                            source[rule_key] = value
                    break
            config.setdefault("mail", {})["sources"] = sources
            save_supplier_stock_config(config)
            notice = (
                f"✅ Правило «{updated.get('name') or target}» обновлено\n\n"
                if updated
                else "ℹ️ Правило не найдено\n\n"
            )
        elif action.startswith("supplier_stock_mail_source_edit|"):
            candidate = raw_action.split("|", 1)[1].strip()
            if any(str(s.get("id")) == candidate for s in sources):
                editing_id = candidate
            else:
                notice = "ℹ️ Правило не найдено\n\n"
        elif action.startswith("supplier_stock_mail_source_delete_confirm|"):
            target = raw_action.split("|", 1)[1].strip()
            before = len(sources)
            sources = [s for s in sources if str(s.get("id")) != target]
            config.setdefault("mail", {})["sources"] = sources
            save_supplier_stock_config(config)
            notice = (
                "🗑 Правило удалено\n\n" if len(sources) < before else "ℹ️ Правило не найдено\n\n"
            )
        elif action.startswith("supplier_stock_mail_source_delete|"):
            pending_delete_id = raw_action.split("|", 1)[1].strip()

        if pending_delete_id:
            target_source = next(
                (s for s in sources if str(s.get("id")) == pending_delete_id), None
            )
            name = str((target_source or {}).get("name") or pending_delete_id)
            message = (
                f"🗑 Удалить правило вложений «{name}»?\n\n"
                "Действие необратимо — настройки правила будут потеряны."
            )
            menu_options = [
                {
                    "label": f"⚠️ Да, удалить «{name[:24]}»",
                    "action": f"supplier_stock_mail_source_delete_confirm|{pending_delete_id}",
                },
                {"label": "↩️ Отмена", "action": "supplier_stock_mail_sources"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        elif editing_id:
            src = next(s for s in sources if str(s.get("id")) == editing_id)
            message = (
                f"{notice}✏️ Редактирование правила «{src.get('name') or editing_id}»\n\n"
                "Текущие значения:\n"
                f"• Название: {src.get('name') or '—'}\n"
                f"• Отправитель: {src.get('sender_pattern') or 'любой'}\n"
                f"• Тема: {src.get('subject_pattern') or 'любая'}\n"
                f"• Имя файла: {src.get('filename_pattern') or 'любой'}\n"
                f"• Вложений: {src.get('expected_attachments', 1)}\n"
                f"• Шаблон файла: {src.get('output_template') or 'не задано'}\n\n"
                "Заполните только те поля, которые нужно изменить "
                "(пустые поля останутся без изменений)."
            )
            menu_options = [
                {"label": "↩️ К списку правил", "action": "supplier_stock_mail_sources"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        else:
            lines = [f"{notice}📨 Источники почты (правила вложений)", ""]
            if not sources:
                lines.append("⚪️ Правила не настроены.")
            else:
                for idx, source in enumerate(sources, start=1):
                    name = source.get("name") or source.get("id") or f"Правило {idx}"
                    sender = source.get("sender_pattern") or "любой"
                    subject = source.get("subject_pattern") or "любой"
                    filename = source.get("filename_pattern") or "любой"
                    expected = source.get("expected_attachments", 1)
                    status = "🟢 вкл" if source.get("enabled", True) else "🔴 выкл"
                    unpack = "да" if source.get("unpack_archive", False) else "нет"
                    lines.append(f"{idx}. {status} {name}")
                    lines.append(f"    Отправитель: {sender}")
                    lines.append(f"    Тема: {subject}")
                    lines.append(f"    Имя файла: {filename} · вложений: {expected}")
                    lines.append(f"    Распаковка: {unpack}")
            lines.append("")
            lines.append(
                "Базовые поля (название, паттерны, вложения, шаблон) редактируются здесь; "
                "MIME-фильтр — пока в Telegram-боте."
            )
            message = "\n".join(lines)
            menu_options = []
            for source in sources:
                sid = str(source.get("id") or "").strip()
                if not sid:
                    continue
                name = str(source.get("name") or sid)
                enabled = source.get("enabled", True)
                unpack = source.get("unpack_archive", False)
                toggle_label = (
                    f"{'⛔️ Выключить' if enabled else '✅ Включить'} {name[:18]}"
                )
                unpack_label = (
                    f"📦 Распаковка {'выкл' if unpack else 'вкл'}: {name[:14]}"
                )
                menu_options.append(
                    {"label": f"✏️ Изменить {name[:18]}", "action": f"supplier_stock_mail_source_edit|{sid}"}
                )
                menu_options.append(
                    {"label": toggle_label, "action": f"supplier_stock_mail_source_toggle|{sid}"}
                )
                menu_options.append(
                    {"label": unpack_label, "action": f"supplier_stock_mail_source_unpack|{sid}"}
                )
                menu_options.append(
                    {
                        "label": f"🗑 Удалить {name[:18]}",
                        "action": f"supplier_stock_mail_source_delete|{sid}",
                    }
                )
            menu_options.append({"label": "↩️ Назад", "action": "supplier_stock_mail"})
            menu_options.append({"label": "✖️ Закрыть", "action": "close"})
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if (
        action == "supplier_stock_processing"
        or action.startswith("supplier_stock_proc_update|")
        or action.startswith("supplier_stock_proc_edit|")
        or action.startswith("supplier_stock_proc_toggle|")
        or action.startswith("supplier_stock_proc_activate|")
        or action.startswith("supplier_stock_proc_delete_confirm|")
        or action.startswith("supplier_stock_proc_delete|")
    ):
        config = get_supplier_stock_config()
        rules = (config.get("processing", {}) or {}).get("rules", []) or []
        notice = ""
        pending_delete_id = ""
        editing_id = ""
        if action.startswith("supplier_stock_proc_toggle|"):
            target = raw_action.split("|", 1)[1].strip()
            for rule in rules:
                if str(rule.get("id")) == target:
                    rule["enabled"] = not rule.get("enabled", True)
                    if not rule["enabled"]:
                        rule["active"] = False
                    notice = (
                        f"{'✅ Включено' if rule['enabled'] else '⛔️ Выключено'} "
                        f"правило «{rule.get('name') or target}»\n\n"
                    )
                    break
            config.setdefault("processing", {})["rules"] = rules
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_proc_activate|"):
            target = raw_action.split("|", 1)[1].strip()
            for rule in rules:
                if str(rule.get("id")) == target:
                    rule["active"] = not rule.get("active", False)
                    if rule["active"]:
                        rule["enabled"] = True
                    notice = (
                        f"{'⭐ Активировано' if rule['active'] else '☆ Деактивировано'} "
                        f"правило «{rule.get('name') or target}»\n\n"
                    )
                    break
            config.setdefault("processing", {})["rules"] = rules
            save_supplier_stock_config(config)
        elif action.startswith("supplier_stock_proc_update|"):
            parts = raw_action.split("|", 2)
            target = parts[1].strip() if len(parts) > 1 else ""
            fields = {}
            if len(parts) > 2:
                for pair in parts[2].split("&"):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        fields[key.strip().lower()] = unquote(value)
            updated = None
            for rule in rules:
                if str(rule.get("id")) == target:
                    updated = rule
                    if (fields.get("name") or "").strip():
                        rule["name"] = fields["name"].strip()
                    if (fields.get("source_file") or "").strip():
                        rule["source_file"] = fields["source_file"].strip()
                    break
            config.setdefault("processing", {})["rules"] = rules
            save_supplier_stock_config(config)
            notice = (
                f"✅ Правило «{updated.get('name') or target}» обновлено\n\n"
                if updated
                else "ℹ️ Правило не найдено\n\n"
            )
        elif action.startswith("supplier_stock_proc_edit|"):
            candidate = raw_action.split("|", 1)[1].strip()
            if any(str(r.get("id")) == candidate for r in rules):
                editing_id = candidate
            else:
                notice = "ℹ️ Правило не найдено\n\n"
        elif action.startswith("supplier_stock_proc_delete_confirm|"):
            target = raw_action.split("|", 1)[1].strip()
            before = len(rules)
            rules = [r for r in rules if str(r.get("id")) != target]
            config.setdefault("processing", {})["rules"] = rules
            save_supplier_stock_config(config)
            notice = (
                "🗑 Правило удалено\n\n" if len(rules) < before else "ℹ️ Правило не найдено\n\n"
            )
        elif action.startswith("supplier_stock_proc_delete|"):
            pending_delete_id = raw_action.split("|", 1)[1].strip()

        if pending_delete_id:
            target_rule = next(
                (r for r in rules if str(r.get("id")) == pending_delete_id), None
            )
            name = str((target_rule or {}).get("name") or pending_delete_id)
            message = (
                f"🗑 Удалить правило обработки «{name}»?\n\n"
                "Действие необратимо — настройки правила будут потеряны."
            )
            menu_options = [
                {
                    "label": f"⚠️ Да, удалить «{name[:24]}»",
                    "action": f"supplier_stock_proc_delete_confirm|{pending_delete_id}",
                },
                {"label": "↩️ Отмена", "action": "supplier_stock_processing"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        elif editing_id:
            rule = next(r for r in rules if str(r.get("id")) == editing_id)
            message = (
                f"{notice}✏️ Редактирование правила «{rule.get('name') or editing_id}»\n\n"
                "Текущие значения:\n"
                f"• Название: {rule.get('name') or '—'}\n"
                f"• Файл источника: {rule.get('source_file') or 'не задано'}\n\n"
                "Заполните только те поля, которые нужно изменить "
                "(пустые поля останутся без изменений). Колонки, шаблоны и "
                "варианты обработки — пока в Telegram-боте."
            )
            menu_options = [
                {"label": "↩️ К списку правил", "action": "supplier_stock_processing"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        else:
            lines = [f"{notice}⚙️ Правила обработки файлов остатков", ""]
            if not rules:
                lines.append("⚪️ Правила обработки не настроены.")
            else:
                for idx, rule in enumerate(rules, start=1):
                    name = rule.get("name") or rule.get("id") or f"Правило {idx}"
                    source_file = rule.get("source_file") or "не задано"
                    enabled = rule.get("enabled", True)
                    active = rule.get("active", False)
                    status = "🟢 вкл" if enabled else "🔴 выкл"
                    mode = (
                        "обработка" if rule.get("requires_processing", True) else "без обработки"
                    )
                    lines.append(f"{idx}. {status}{' ⭐' if active else ''} {name}")
                    lines.append(f"    Файл источника: {source_file}")
                    lines.append(f"    Режим: {mode} · Активно: {'да' if active else 'нет'}")
            lines.append("")
            lines.append(
                "Базовые поля (название, файл источника) редактируются здесь; "
                "колонки, шаблоны и варианты обработки — пока в Telegram-боте."
            )
            message = "\n".join(lines)
            menu_options = []
            for rule in rules:
                rid = str(rule.get("id") or "").strip()
                if not rid:
                    continue
                name = str(rule.get("name") or rid)
                enabled = rule.get("enabled", True)
                active = rule.get("active", False)
                toggle_label = (
                    f"{'⛔️ Выключить' if enabled else '✅ Включить'} {name[:18]}"
                )
                activate_label = (
                    f"{'☆ Деактивировать' if active else '⭐ Активировать'} {name[:14]}"
                )
                menu_options.append(
                    {"label": f"✏️ Изменить {name[:18]}", "action": f"supplier_stock_proc_edit|{rid}"}
                )
                menu_options.append(
                    {"label": toggle_label, "action": f"supplier_stock_proc_toggle|{rid}"}
                )
                menu_options.append(
                    {"label": activate_label, "action": f"supplier_stock_proc_activate|{rid}"}
                )
                menu_options.append(
                    {"label": f"🗑 Удалить {name[:18]}", "action": f"supplier_stock_proc_delete|{rid}"}
                )
            menu_options.append({"label": "↩️ Назад", "action": "supplier_stock_download"})
            menu_options.append({"label": "✖️ Закрыть", "action": "close"})
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if action in {
        "supplier_stock_reports_download",
        "supplier_stock_reports_mail",
    }:
        title_map = {
            "supplier_stock_reports_download": "🗓 Отчёты (download)",
            "supplier_stock_reports_mail": "🗓 Отчёты (mail)",
        }
        back_action = (
            "supplier_stock_mail"
            if action.startswith("supplier_stock_mail_")
            or action.startswith("supplier_stock_reports_")
            else "supplier_stock_download"
        )
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"{title_map.get(action, 'Раздел')}\n\nДетальная настройка пока доступна в Telegram-боте.",
                    "menu_options": [
                        {"label": "🏠 На главную", "action": "main_menu"},
                        {"label": "↩️ Назад", "action": back_action},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "settings_ext_config_console" or action in (
        "cc_server_clear",
    ) or action.startswith(
        ("cc_set_hours|", "cc_server_add|", "cc_unserver|", "cc_pat_add|", "cc_pat_del|")
    ):
        from extensions.backup_monitor.backup_utils import (
            get_config_console_patterns_from_config,
            get_config_console_servers,
            save_config_console_patterns,
            save_config_console_servers,
        )

        notice = ""
        if action.startswith("cc_set_hours|"):
            raw_hours = raw_action.split("|", 1)[1].strip()
            try:
                hours_value = int(raw_hours)
                if hours_value <= 0:
                    raise ValueError
                settings_manager.set_setting(
                    "CONFIG_CONSOLE_ALERT_HOURS", hours_value, "config_console"
                )
                notice = f"✅ Период отчёта: {hours_value}ч\n\n"
            except (TypeError, ValueError):
                notice = "❌ Некорректное значение периода\n\n"
        elif action.startswith("cc_server_add|"):
            raw_value = unquote(raw_action.split("|", 1)[1])
            names = [p.strip() for p in re.split(r"[,\n;]+", raw_value) if p.strip()]
            servers = get_config_console_servers()
            existing = {s.lower() for s in servers}
            added = []
            for name in names:
                if name.lower() not in existing:
                    servers.append(name)
                    existing.add(name.lower())
                    added.append(name)
            save_config_console_servers(servers)
            notice = (
                f"✅ Добавлены серверы: {', '.join(added)}\n\n"
                if added
                else "ℹ️ Ничего не добавлено (пусто или дубли)\n\n"
            )
        elif action.startswith("cc_unserver|"):
            srv = unquote(raw_action.split("|", 1)[1]).strip()
            remaining = [s for s in get_config_console_servers() if s.lower() != srv.lower()]
            save_config_console_servers(remaining)
            notice = f"🗑 Сервер «{srv}» удалён из списка\n\n"
        elif action == "cc_server_clear":
            save_config_console_servers([])
            notice = "🧹 Список серверов очищен\n\n"
        elif action.startswith("cc_pat_add|"):
            raw_value = unquote(raw_action.split("|", 1)[1]).strip()
            if not raw_value:
                notice = "❌ Паттерн не может быть пустым\n\n"
            else:
                try:
                    re.compile(raw_value)
                    patterns = get_config_console_patterns_from_config()
                    if raw_value in patterns:
                        notice = "ℹ️ Такой паттерн уже есть\n\n"
                    else:
                        patterns.append(raw_value)
                        save_config_console_patterns(patterns)
                        notice = "✅ Паттерн добавлен\n\n"
                except re.error as exc:
                    notice = f"❌ Некорректный regex: {exc}\n\n"
        elif action.startswith("cc_pat_del|"):
            raw_idx = raw_action.split("|", 1)[1].strip()
            patterns = get_config_console_patterns_from_config()
            try:
                idx = int(raw_idx)
                if 0 <= idx < len(patterns):
                    removed = patterns.pop(idx)
                    save_config_console_patterns(patterns)
                    notice = f"🗑 Паттерн удалён: {removed[:40]}\n\n"
                else:
                    notice = "❌ Нет такого паттерна\n\n"
            except (TypeError, ValueError):
                notice = "❌ Некорректный индекс\n\n"

        try:
            current_hours = int(
                settings_manager.get_setting("CONFIG_CONSOLE_ALERT_HOURS", 168) or 168
            )
        except (TypeError, ValueError):
            current_hours = 168
        servers = get_config_console_servers()
        patterns = get_config_console_patterns_from_config()

        servers_text = ", ".join(servers) if servers else "— (по факту)"
        patterns_text = "\n".join(f"  • {p}" for p in patterns) if patterns else "— (дефолт)"
        message = (
            f"{notice}⚙️ Бэкап конфигов и историй — настройки\n\n"
            f"• Период отчёта: {current_hours}ч\n"
            f"• Ожидаемые серверы: {servers_text}\n"
            f"• Паттерны темы письма:\n{patterns_text}\n\n"
            "Серверы из списка группируются и подсвечиваются при отсутствии "
            "свежего отчёта. Добавьте сервер или паттерн в поле ниже."
        )

        menu_options = []
        for value in (48, 72, 168, 336):
            prefix = "✅ " if value == current_hours else ""
            menu_options.append({"label": f"{prefix}{value}ч", "action": f"cc_set_hours|{value}"})
        for srv in servers:
            menu_options.append({"label": f"🗑 {srv}", "action": f"cc_unserver|{srv}"})
        if servers:
            menu_options.append({"label": "🧹 Очистить серверы", "action": "cc_server_clear"})
        for idx, pat in enumerate(patterns):
            short = pat if len(pat) <= 28 else pat[:25] + "…"
            menu_options.append({"label": f"🗑 паттерн: {short}", "action": f"cc_pat_del|{idx}"})
        menu_options.extend(
            [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if action == "settings_ext_nas" or action == "nas_ignore_clear" or action.startswith(
        ("nas_set_hours|", "nas_unignore|", "nas_ignore_add|", "nas_pat_add|", "nas_pat_del|")
    ):
        from extensions.backup_monitor.backup_utils import (
            get_nas_ignore_bases,
            save_nas_ignore_bases,
        )

        def _get_nas_patterns() -> list:
            rows: list = []
            try:
                conn = settings_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, pattern FROM backup_patterns "
                    "WHERE category = 'nas_transfer' AND pattern_type = 'subject' "
                    "ORDER BY id"
                )
                rows = [(int(r[0]), str(r[1] or "")) for r in cursor.fetchall()]
            except Exception:
                rows = []
            return rows

        notice = ""
        if action.startswith("nas_set_hours|"):
            raw_hours = action.split("|", 1)[1].strip()
            try:
                hours_value = int(raw_hours)
                if hours_value <= 0:
                    raise ValueError
                settings_manager.set_setting(
                    "NAS_TRANSFER_ALERT_HOURS", hours_value, "nas_transfer"
                )
                notice = f"✅ Период отчёта: {hours_value}ч\n\n"
            except (TypeError, ValueError):
                notice = "❌ Некорректное значение периода\n\n"
        elif action.startswith("nas_ignore_add|"):
            raw_value = unquote(raw_action.split("|", 1)[1])
            names = [
                part.strip()
                for part in re.split(r"[,\n;]+", raw_value)
                if part.strip()
            ]
            bases = get_nas_ignore_bases()
            existing = {b.lower() for b in bases}
            added = []
            for name in names:
                if name.lower() not in existing:
                    bases.append(name)
                    existing.add(name.lower())
                    added.append(name)
            save_nas_ignore_bases(bases)
            notice = (
                f"✅ Добавлено в игнор: {', '.join(added)}\n\n"
                if added
                else "ℹ️ Ничего не добавлено (пусто или дубли)\n\n"
            )
        elif action.startswith("nas_unignore|"):
            base = unquote(raw_action.split("|", 1)[1]).strip()
            remaining = [b for b in get_nas_ignore_bases() if b.lower() != base.lower()]
            save_nas_ignore_bases(remaining)
            notice = f"🗑 База «{base}» убрана из игнор-списка\n\n"
        elif action == "nas_ignore_clear":
            save_nas_ignore_bases([])
            notice = "🧹 Игнор-список очищен\n\n"
        elif action.startswith("nas_pat_add|"):
            raw_value = unquote(raw_action.split("|", 1)[1]).strip()
            if not raw_value:
                notice = "❌ Паттерн не может быть пустым\n\n"
            else:
                try:
                    re.compile(raw_value)
                    if raw_value in [p for _, p in _get_nas_patterns()]:
                        notice = "ℹ️ Такой паттерн уже есть\n\n"
                    else:
                        conn = settings_manager.get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO backup_patterns "
                            "(pattern_type, pattern, category, enabled) VALUES (?, ?, ?, 1)",
                            ("subject", raw_value, "nas_transfer"),
                        )
                        conn.commit()
                        notice = "✅ Паттерн добавлен\n\n"
                except re.error as exc:
                    notice = f"❌ Некорректный regex: {exc}\n\n"
        elif action.startswith("nas_pat_del|"):
            raw_id = raw_action.split("|", 1)[1].strip()
            try:
                pat_id = int(raw_id)
                conn = settings_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM backup_patterns "
                    "WHERE id = ? AND category = 'nas_transfer'",
                    (pat_id,),
                )
                conn.commit()
                notice = "🗑 Паттерн удалён\n\n" if cursor.rowcount else "❌ Нет такого паттерна\n\n"
            except (TypeError, ValueError):
                notice = "❌ Некорректный идентификатор\n\n"

        try:
            current_hours = int(settings_manager.get_setting("NAS_TRANSFER_ALERT_HOURS", 48) or 48)
        except (TypeError, ValueError):
            current_hours = 48
        ignore_bases = get_nas_ignore_bases()
        patterns = _get_nas_patterns()

        ignore_text = ", ".join(ignore_bases) if ignore_bases else "—"
        patterns_text = (
            "\n".join(f"  • {p}" for _, p in patterns) if patterns else "  — (дефолт)"
        )
        message = (
            f"{notice}⚙️ Передача бэкапов на NAS — настройки\n\n"
            f"• Период отчёта: {current_hours}ч\n"
            f"• Игнорируемые базы: {ignore_text}\n\n"
            f"• Паттерны темы письма:\n{patterns_text}\n\n"
            "Игнорируемые базы не считаются ошибкой. Добавьте новую базу или "
            "паттерн темы письма в поля ниже (базы — можно несколько через запятую)."
        )

        menu_options = []
        for value in (24, 48, 72, 168):
            prefix = "✅ " if value == current_hours else ""
            menu_options.append({"label": f"{prefix}{value}ч", "action": f"nas_set_hours|{value}"})
        for base in ignore_bases:
            menu_options.append({"label": f"🗑 {base}", "action": f"nas_unignore|{base}"})
        if ignore_bases:
            menu_options.append({"label": "🧹 Очистить игнор-список", "action": "nas_ignore_clear"})
        for pat_id, pat in patterns:
            short = pat if len(pat) <= 28 else pat[:25] + "…"
            menu_options.append({"label": f"🗑 паттерн: {short}", "action": f"nas_pat_del|{pat_id}"})
        menu_options.extend(
            [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if action == "settings_ext_snapshot" or action.startswith(
        ("snap_host_add|", "snap_host_toggle|", "snap_host_del|", "snap_pat_add|", "snap_pat_del|")
    ):
        def _get_snap_hosts() -> dict:
            stored = settings_manager.get_setting("SNAPSHOT_TRANSFER_HOSTS", {}) or {}
            return stored if isinstance(stored, dict) else {}

        def _save_snap_hosts(hosts_cfg: dict) -> None:
            settings_manager.set_setting(
                "SNAPSHOT_TRANSFER_HOSTS", hosts_cfg, "snapshot_transfer_hosts"
            )

        def _get_snap_patterns() -> list:
            rows: list = []
            try:
                conn = settings_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, pattern FROM backup_patterns "
                    "WHERE category = 'snapshot_transfer' AND pattern_type = 'subject' "
                    "ORDER BY id"
                )
                rows = [(int(r[0]), str(r[1] or "")) for r in cursor.fetchall()]
            except Exception:
                rows = []
            return rows

        notice = ""
        if action.startswith("snap_host_add|"):
            raw_value = unquote(raw_action.split("|", 1)[1])
            names = [p.strip() for p in re.split(r"[,\n;]+", raw_value) if p.strip()]
            hosts_cfg = _get_snap_hosts()
            existing = {k.lower() for k in hosts_cfg}
            added = []
            for name in names:
                if name.lower() not in existing:
                    hosts_cfg[name] = {"enabled": True, "start_time": "03:00"}
                    existing.add(name.lower())
                    added.append(name)
            _save_snap_hosts(hosts_cfg)
            notice = (
                f"✅ Добавлены хосты: {', '.join(added)}\n\n"
                if added
                else "ℹ️ Ничего не добавлено (пусто или дубли)\n\n"
            )
        elif action.startswith("snap_host_toggle|"):
            name = unquote(raw_action.split("|", 1)[1]).strip()
            hosts_cfg = _get_snap_hosts()
            key = next((k for k in hosts_cfg if k.lower() == name.lower()), None)
            if key is not None:
                host_cfg = hosts_cfg[key] if isinstance(hosts_cfg[key], dict) else {}
                host_cfg["enabled"] = not bool(host_cfg.get("enabled", True))
                hosts_cfg[key] = host_cfg
                _save_snap_hosts(hosts_cfg)
                notice = (
                    f"{'🟢 Включён' if host_cfg['enabled'] else '🔴 Выключен'}: {key}\n\n"
                )
            else:
                notice = "❌ Хост не найден\n\n"
        elif action.startswith("snap_host_del|"):
            name = unquote(raw_action.split("|", 1)[1]).strip()
            hosts_cfg = _get_snap_hosts()
            key = next((k for k in hosts_cfg if k.lower() == name.lower()), None)
            if key is not None:
                hosts_cfg.pop(key, None)
                _save_snap_hosts(hosts_cfg)
                notice = f"🗑 Хост «{key}» удалён\n\n"
            else:
                notice = "❌ Хост не найден\n\n"
        elif action.startswith("snap_pat_add|"):
            raw_value = unquote(raw_action.split("|", 1)[1]).strip()
            if not raw_value:
                notice = "❌ Паттерн не может быть пустым\n\n"
            else:
                try:
                    re.compile(raw_value)
                    if raw_value in [p for _, p in _get_snap_patterns()]:
                        notice = "ℹ️ Такой паттерн уже есть\n\n"
                    else:
                        conn = settings_manager.get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO backup_patterns "
                            "(pattern_type, pattern, category, enabled) VALUES (?, ?, ?, 1)",
                            ("subject", raw_value, "snapshot_transfer"),
                        )
                        conn.commit()
                        notice = "✅ Паттерн добавлен\n\n"
                except re.error as exc:
                    notice = f"❌ Некорректный regex: {exc}\n\n"
        elif action.startswith("snap_pat_del|"):
            raw_id = raw_action.split("|", 1)[1].strip()
            try:
                pat_id = int(raw_id)
                conn = settings_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM backup_patterns "
                    "WHERE id = ? AND category = 'snapshot_transfer'",
                    (pat_id,),
                )
                conn.commit()
                notice = "🗑 Паттерн удалён\n\n" if cursor.rowcount else "❌ Нет такого паттерна\n\n"
            except (TypeError, ValueError):
                notice = "❌ Некорректный идентификатор\n\n"

        hosts_cfg = _get_snap_hosts()
        patterns = _get_snap_patterns()

        if hosts_cfg:
            host_lines = []
            for name in sorted(hosts_cfg, key=str.lower):
                host_cfg = hosts_cfg[name] if isinstance(hosts_cfg[name], dict) else {}
                state_icon = "🟢" if bool(host_cfg.get("enabled", True)) else "🔴"
                start_time = str(host_cfg.get("start_time") or "—")
                host_lines.append(f"  {state_icon} {name} · старт {start_time}")
            hosts_text = "\n".join(host_lines)
        else:
            hosts_text = "  — список пуст"
        patterns_text = (
            "\n".join(f"  • {p}" for _, p in patterns) if patterns else "  — (дефолт)"
        )

        message = (
            f"{notice}⚙️ Передачи снэпшотов — настройки\n\n"
            f"• Хосты:\n{hosts_text}\n\n"
            f"• Паттерны темы письма:\n{patterns_text}\n\n"
            "Добавьте хост или паттерн в поля ниже. Кнопки 🟢/🔴 включают и "
            "выключают хост, 🗑 удаляют запись."
        )

        menu_options = []
        for name in sorted(hosts_cfg, key=str.lower):
            host_cfg = hosts_cfg[name] if isinstance(hosts_cfg[name], dict) else {}
            enabled = bool(host_cfg.get("enabled", True))
            toggle_label = f"{'🔴 выключить' if enabled else '🟢 включить'}: {name}"
            menu_options.append({"label": toggle_label, "action": f"snap_host_toggle|{name}"})
            menu_options.append({"label": f"🗑 {name}", "action": f"snap_host_del|{name}"})
        for pat_id, pat in patterns:
            short = pat if len(pat) <= 28 else pat[:25] + "…"
            menu_options.append({"label": f"🗑 паттерн: {short}", "action": f"snap_pat_del|{pat_id}"})
        menu_options.extend(
            [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    if (
        action == "settings_ext_tls"
        or action.startswith("tls_set_alert_days|")
        or action.startswith("tls_reissue|")
        or action.startswith("tls_cert_toggle|")
        or action.startswith("tls_cert_delete|")
        or action.startswith("tls_cert_upsert|")
        or action == "tls_certs_reset"
    ):
        from extensions.tls_cert_monitor import (
            DEFAULT_CERTS,
            get_domains_config,
            get_settings,
            normalize_domains,
            reissue_certificate,
            save_domains_config,
            save_settings,
        )

        notice = ""
        if action.startswith("tls_set_alert_days|"):
            raw_value = raw_action.split("|", 1)[1].strip()
            try:
                days_value = int(raw_value)
                if days_value < 1 or days_value > 180:
                    raise ValueError
                save_settings({"alert_days_default": days_value})
                notice = f"✅ Порог алерта: {days_value} дн.\n\n"
            except (TypeError, ValueError):
                notice = "❌ Некорректное число дней (1-180)\n\n"
        elif action.startswith("tls_reissue|"):
            cert_name = unquote(raw_action.split("|", 1)[1]).strip()
            _ok_reissue, reissue_msg = reissue_certificate(cert_name)
            notice = f"{reissue_msg}\n\n"
        elif action.startswith("tls_cert_toggle|"):
            cert_name = unquote(raw_action.split("|", 1)[1]).strip()
            certs_cfg = get_domains_config()
            if cert_name in certs_cfg:
                certs_cfg[cert_name]["enabled"] = not bool(
                    certs_cfg[cert_name].get("enabled", True)
                )
                save_domains_config(certs_cfg)
                state_txt = "включён" if certs_cfg[cert_name]["enabled"] else "выключен"
                notice = f"✅ {cert_name}: {state_txt}\n\n"
            else:
                notice = "❌ Сертификат не найден\n\n"
        elif action.startswith("tls_cert_delete|"):
            cert_name = unquote(raw_action.split("|", 1)[1]).strip()
            certs_cfg = get_domains_config()
            if certs_cfg.pop(cert_name, None) is not None:
                save_domains_config(certs_cfg)
                notice = f"🗑 Сертификат {cert_name} удалён\n\n"
            else:
                notice = "❌ Сертификат не найден\n\n"
        elif action.startswith("tls_cert_upsert|"):
            # Формат: tls_cert_upsert|<name>|<host>|<port>|<domains через запятую>
            parts = raw_action.split("|")
            name = unquote(parts[1]).strip() if len(parts) > 1 else ""
            host = unquote(parts[2]).strip() if len(parts) > 2 else ""
            port_raw = unquote(parts[3]).strip() if len(parts) > 3 else ""
            domains_raw = unquote(parts[4]).strip() if len(parts) > 4 else ""
            if not name:
                notice = "❌ Не указан cert-name\n\n"
            else:
                try:
                    port_val = int(port_raw) if port_raw else 443
                    if port_val < 1 or port_val > 65535:
                        raise ValueError
                except (TypeError, ValueError):
                    port_val = 443
                domains_list = [
                    p.strip() for p in domains_raw.replace(",", " ").split() if p.strip()
                ] or [name]
                certs_cfg = get_domains_config()
                existed = name in certs_cfg
                default_alert = int(get_settings().get("alert_days_default", 14))
                certs_cfg[name] = {
                    "enabled": certs_cfg.get(name, {}).get("enabled", True),
                    "check_host": host or name,
                    "port": port_val,
                    "alert_days": certs_cfg.get(name, {}).get("alert_days", default_alert),
                    "domains": domains_list,
                }
                save_domains_config(certs_cfg)
                notice = f"{'✏️ Обновлён' if existed else '➕ Добавлен'} сертификат {name}\n\n"
        elif action == "tls_certs_reset":
            save_domains_config(normalize_domains(DEFAULT_CERTS))
            notice = "🔄 Список сертификатов сброшен к значениям по умолчанию\n\n"

        settings = get_settings()
        certs = get_domains_config()
        alert_days = settings.get("alert_days_default", 14)
        cert_lines = []
        for cert_name in sorted(certs.keys()):
            cfg = certs[cert_name]
            status = "🟢" if cfg.get("enabled", True) else "🔴"
            host = cfg.get("check_host", cert_name)
            ndom = len(cfg.get("domains") or [cert_name])
            cert_lines.append(f"{status} {cert_name} → {host}:{cfg.get('port', 443)} ({ndom} дом.)")
        certs_block = "\n".join(cert_lines) if cert_lines else "—"

        message = (
            f"{notice}🔐 TLS-сертификаты — настройки\n\n"
            f"• SSH-хост certbot: {settings.get('ssh_host') or 'не задан'}\n"
            f"• Команда certbot: {settings.get('certbot_cmd')}\n"
            f"• Перезапуск nginx: {settings.get('nginx_reload_cmd')}\n"
            f"• Порог алерта по умолчанию: {alert_days} дн.\n\n"
            f"Сертификаты ({len(certs)}):\n{certs_block}\n\n"
            "Добавить/изменить сертификат — заполните поля ниже и нажмите «Сохранить» "
            "(если cert-name существует — он обновится). Кнопки ниже: перевыпуск, "
            "вкл/выкл и удаление по каждому сертификату. SSH-хост и команды "
            "certbot/nginx меняются в Telegram-боте."
        )

        menu_options = []
        for value in (7, 14, 30, 60):
            prefix = "✅ " if value == int(alert_days) else ""
            menu_options.append(
                {"label": f"{prefix}алерт {value}д", "action": f"tls_set_alert_days|{value}"}
            )
        for cert_name in sorted(certs.keys()):
            enabled = bool(certs[cert_name].get("enabled", True))
            toggle_label = "🔴 Выкл." if enabled else "🟢 Вкл."
            menu_options.append(
                {"label": f"♻️ Перевыпуск {cert_name}", "action": f"tls_reissue|{cert_name}"}
            )
            menu_options.append(
                {"label": f"{toggle_label} {cert_name}", "action": f"tls_cert_toggle|{cert_name}"}
            )
            menu_options.append(
                {"label": f"🗑 Удалить {cert_name}", "action": f"tls_cert_delete|{cert_name}"}
            )
        menu_options.append({"label": "🔄 Сбросить к дефолтам", "action": "tls_certs_reset"})
        menu_options.extend(
            [
                {"label": "🏠 На главную", "action": "main_menu"},
                {"label": "↩️ Назад", "action": "settings_extensions"},
                {"label": "✖️ Закрыть", "action": "close"},
            ]
        )

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": message,
                    "menu_options": menu_options,
                }
            ),
            200,
        )

    mapped_action = settings_menu_action_map.get(action)
    if mapped_action:
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": mapped_action.get("message"),
                    "menu_options": mapped_action.get("menu_options", []),
                }
            ),
            200,
        )

    if action.startswith("settings_zfs_toggle_"):
        server_name = unquote(raw_action[len("settings_zfs_toggle_") :]).strip()
        if not server_name:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_ACTION",
                            "message": "Server name is required for settings_zfs_toggle_*",
                            "request_id": request_id,
                        }
                    }
                ),
                400,
            )

        zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}

        for key, value in zfs_servers.items():
            if key != server_name:
                continue
            if isinstance(value, dict):
                value["enabled"] = not bool(value.get("enabled", True))
            else:
                zfs_servers[key] = {"host": str(value), "enabled": False}
            settings_manager.set_setting("ZFS_SERVERS", zfs_servers, "zfs")
            break

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "🔄 Статус ZFS-сервера обновлён.",
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_zfs_list"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_zfs_edit_name_"):
        payload = raw_action[len("settings_zfs_edit_name_") :]
        parts = payload.split("|", 1)
        current_name = unquote(parts[0]).strip() if parts else ""
        new_name = unquote(parts[1]).strip() if len(parts) > 1 else ""

        if not current_name:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_ACTION",
                            "message": "Server name is required for settings_zfs_edit_name_*",
                            "request_id": request_id,
                        }
                    }
                ),
                400,
            )

        if not new_name:
            return (
                jsonify(
                    {
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
                    }
                ),
                200,
            )

        zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}
        if current_name not in zfs_servers:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted",
                        "message": f"❌ ZFS-сервер «{current_name}» не найден.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_zfs_list"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )
        if new_name in zfs_servers and new_name != current_name:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted",
                        "message": f"❌ ZFS-сервер «{new_name}» уже существует.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_zfs_list"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        server_value = zfs_servers.pop(current_name, None)
        if not isinstance(server_value, dict):
            server_value = {"enabled": True}
        zfs_servers[new_name] = server_value
        settings_manager.set_setting("ZFS_SERVERS", zfs_servers, "zfs")
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

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"✅ ZFS-сервер переименован: «{current_name}» → «{new_name}».",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_zfs_list"},
                        {"label": "↩️ Назад", "action": "settings_zfs"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_zfs_delete_"):
        server_name = unquote(raw_action[len("settings_zfs_delete_") :]).strip()
        if not server_name:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_ACTION",
                            "message": "Server name is required for settings_zfs_delete_*",
                            "request_id": request_id,
                        }
                    }
                ),
                400,
            )

        zfs_servers = settings_manager.get_setting("ZFS_SERVERS", {})
        if not isinstance(zfs_servers, dict):
            zfs_servers = {}
        removed = zfs_servers.pop(server_name, None)
        if removed is None:
            return (
                jsonify(
                    {
                        "request_id": request_id,
                        "action": action,
                        "result": "accepted",
                        "message": f"❌ ZFS-сервер «{server_name}» не найден.",
                        "menu_options": [
                            {"label": "↩️ Назад", "action": "settings_zfs_list"},
                            {"label": "✖️ Закрыть", "action": "close"},
                        ],
                    }
                ),
                200,
            )

        settings_manager.set_setting("ZFS_SERVERS", zfs_servers, "zfs")
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

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": f"✅ ZFS-сервер «{server_name}» удалён.",
                    "menu_options": [
                        {"label": "📋 Обновить список", "action": "settings_zfs_list"},
                        {"label": "↩️ Назад", "action": "settings_zfs"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("settings_db_"):
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "🗃️ Детальное редактирование БД пока доступно в Telegram-боте.",
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_db_main"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action.startswith("supplier_stock_"):
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "result": "accepted",
                    "message": "📦 Детальная настройка раздела остатков поставщиков пока доступна в Telegram-боте.",
                    "menu_options": [
                        {"label": "↩️ Назад", "action": "settings_ext_supplier_stock"},
                        {"label": "✖️ Закрыть", "action": "close"},
                    ],
                }
            ),
            200,
        )

    if action == "settings_resources":
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "action": action,
                    "message": "Откройте раздел «Доступность и ресурсы» для просмотра ресурсов серверов.",
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "error": {
                    "code": "INVALID_ACTION",
                    "message": (
                        "Supported actions: enable_all, disable_all, "
                        "settings_ext_enable_all, settings_ext_disable_all, "
                        "settings_ext_toggle_{extension_id}, settings_ext_*, settings_zfs, settings_resources"
                    ),
                    "request_id": request_id,
                }
            }
        ),
        400,
    )


@app.route("/v1/settings/monitoring", methods=["GET"])
def v1_get_settings_monitoring():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    response = {
        "request_id": request_id,
        "settings": {
            "check_interval_sec": settings_manager.get_setting("CHECK_INTERVAL", 60),
            "timeout_sec": settings_manager.get_setting("API_TIMEOUT_SEC", 15),
            "max_downtime_sec": settings_manager.get_setting("MAX_FAIL_TIME", 900),
            "windows_2025_timeout_sec": settings_manager.get_setting("WINDOWS_2025_TIMEOUT", 35),
            "domain_servers_timeout_sec": settings_manager.get_setting(
                "DOMAIN_SERVERS_TIMEOUT", 20
            ),
            "admin_servers_timeout_sec": settings_manager.get_setting("ADMIN_SERVERS_TIMEOUT", 25),
            "standard_windows_timeout_sec": settings_manager.get_setting(
                "STANDARD_WINDOWS_TIMEOUT", 30
            ),
            "linux_timeout_sec": settings_manager.get_setting("LINUX_TIMEOUT", 15),
            "ping_timeout_sec": settings_manager.get_setting("PING_TIMEOUT", 10),
        },
    }
    app.logger.info("GET /v1/settings/monitoring request_id=%s", request_id)
    return jsonify(response), 200


@app.route("/v1/settings/bot", methods=["GET"])
def v1_get_settings_bot():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    raw_chat_ids = settings_manager.get_setting("CHAT_IDS", [])
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(chat_id).strip() for chat_id in raw_chat_ids if str(chat_id).strip()]
    elif raw_chat_ids:
        chat_ids = [str(raw_chat_ids).strip()]
    else:
        chat_ids = []

    token = settings_manager.get_setting("TELEGRAM_TOKEN", "")

    response = {
        "request_id": request_id,
        "settings": {
            "telegram_chat_id": chat_ids[0] if chat_ids else "",
            "telegram_chat_ids": chat_ids,
            "masked_token": _mask_secret(token),
        },
    }
    app.logger.info("GET /v1/settings/bot request_id=%s", request_id)
    return jsonify(response), 200


@app.route("/v1/settings/bot", methods=["PATCH"])
def v1_settings_bot():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    token = payload.get("telegram_bot_token")
    single_chat_id = payload.get("telegram_chat_id")
    chat_ids = payload.get("telegram_chat_ids")

    if token is None and single_chat_id is None and chat_ids is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "At least one field is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    if token is not None:
        settings_manager.set_setting("TELEGRAM_TOKEN", str(token), "telegram")

    if chat_ids is not None:
        if not isinstance(chat_ids, list):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "VALIDATION_FAILED",
                            "message": "telegram_chat_ids must be an array",
                            "request_id": request_id,
                        }
                    }
                ),
                400,
            )
        normalized_chat_ids = [str(chat_id).strip() for chat_id in chat_ids if str(chat_id).strip()]
        settings_manager.set_setting("CHAT_IDS", normalized_chat_ids, "telegram")
    elif single_chat_id is not None:
        value = str(single_chat_id).strip()
        settings_manager.set_setting("CHAT_IDS", [value] if value else [], "telegram")

    raw_chat_ids = settings_manager.get_setting("CHAT_IDS", [])
    if isinstance(raw_chat_ids, list):
        normalized_chat_ids = [
            str(chat_id).strip() for chat_id in raw_chat_ids if str(chat_id).strip()
        ]
    elif raw_chat_ids:
        normalized_chat_ids = [str(raw_chat_ids).strip()]
    else:
        normalized_chat_ids = []

    saved_token = settings_manager.get_setting("TELEGRAM_TOKEN", "")
    return (
        jsonify(
            {
                "request_id": request_id,
                "settings": {
                    "telegram_chat_id": normalized_chat_ids[0] if normalized_chat_ids else "",
                    "telegram_chat_ids": normalized_chat_ids,
                    "masked_token": _mask_secret(saved_token),
                },
            }
        ),
        200,
    )


@app.route("/v1/settings/bot/chats", methods=["POST"])
def v1_settings_bot_add_chat():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    chat_id = str(payload.get("chat_id") or "").strip()
    if not chat_id:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "chat_id is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    raw_chat_ids = settings_manager.get_setting("CHAT_IDS", [])
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(item).strip() for item in raw_chat_ids if str(item).strip()]
    elif raw_chat_ids:
        chat_ids = [str(raw_chat_ids).strip()]
    else:
        chat_ids = []

    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        settings_manager.set_setting("CHAT_IDS", chat_ids, "telegram")

    return (
        jsonify(
            {
                "request_id": request_id,
                "settings": {
                    "telegram_chat_ids": chat_ids,
                    "telegram_chat_id": chat_ids[0] if chat_ids else "",
                },
            }
        ),
        200,
    )


@app.route("/v1/settings/bot/chats/<chat_id>", methods=["DELETE"])
def v1_settings_bot_remove_chat(chat_id):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    target_chat_id = str(chat_id).strip()
    from config.db_settings_app import settings_manager

    raw_chat_ids = settings_manager.get_setting("CHAT_IDS", [])
    if isinstance(raw_chat_ids, list):
        chat_ids = [str(item).strip() for item in raw_chat_ids if str(item).strip()]
    elif raw_chat_ids:
        chat_ids = [str(raw_chat_ids).strip()]
    else:
        chat_ids = []

    chat_ids = [item for item in chat_ids if item != target_chat_id]
    settings_manager.set_setting("CHAT_IDS", chat_ids, "telegram")

    return (
        jsonify(
            {
                "request_id": request_id,
                "settings": {
                    "telegram_chat_ids": chat_ids,
                    "telegram_chat_id": chat_ids[0] if chat_ids else "",
                },
            }
        ),
        200,
    )


def _normalize_matrix_homeserver(value):
    homeserver = str(value or "").strip().rstrip("/")
    return homeserver


def _default_matrix_homeserver():
    try:
        from config import settings as _settings

        return _normalize_matrix_homeserver(getattr(_settings, "MATRIX_HOMESERVER", ""))
    except Exception:
        return ""


@app.route("/v1/settings/bot/matrix", methods=["GET"])
def v1_get_settings_bot_matrix():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    homeserver = (
        _normalize_matrix_homeserver(settings_manager.get_setting("MATRIX_HOMESERVER", ""))
        or _default_matrix_homeserver()
    )
    room_id = str(settings_manager.get_setting("MATRIX_ROOM_ID", "") or "").strip()
    access_token = settings_manager.get_setting("MATRIX_ACCESS_TOKEN", "")

    response = {
        "request_id": request_id,
        "settings": {
            "matrix_homeserver": homeserver,
            "matrix_room_id": room_id,
            "masked_access_token": _mask_secret(access_token),
        },
    }
    app.logger.info("GET /v1/settings/bot/matrix request_id=%s", request_id)
    return jsonify(response), 200


@app.route("/v1/settings/bot/matrix", methods=["PATCH"])
def v1_settings_bot_matrix():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    homeserver = payload.get("matrix_homeserver")
    access_token = payload.get("matrix_access_token")
    room_id = payload.get("matrix_room_id")

    if homeserver is None and access_token is None and room_id is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "At least one field is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    if homeserver is not None:
        settings_manager.set_setting(
            "MATRIX_HOMESERVER",
            _normalize_matrix_homeserver(homeserver),
            "matrix",
        )
    if access_token is not None:
        settings_manager.set_setting("MATRIX_ACCESS_TOKEN", str(access_token), "matrix")
    if room_id is not None:
        settings_manager.set_setting("MATRIX_ROOM_ID", str(room_id).strip(), "matrix")

    saved_homeserver = (
        _normalize_matrix_homeserver(settings_manager.get_setting("MATRIX_HOMESERVER", ""))
        or _default_matrix_homeserver()
    )
    saved_room_id = str(settings_manager.get_setting("MATRIX_ROOM_ID", "") or "").strip()
    saved_token = settings_manager.get_setting("MATRIX_ACCESS_TOKEN", "")

    return (
        jsonify(
            {
                "request_id": request_id,
                "settings": {
                    "matrix_homeserver": saved_homeserver,
                    "matrix_room_id": saved_room_id,
                    "masked_access_token": _mask_secret(saved_token),
                },
            }
        ),
        200,
    )


def _telegram_bot_test(token):
    import requests as _requests

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        resp = _requests.get(url, timeout=10)
    except _requests.exceptions.Timeout:
        return False, "timeout: Telegram API не ответил за 10 c", None
    except _requests.exceptions.RequestException as exc:
        return False, f"network: {exc}", None

    try:
        data = resp.json()
    except Exception:
        return False, f"HTTP {resp.status_code}: некорректный JSON", None

    if resp.status_code != 200 or not data.get("ok"):
        description = data.get("description") or f"HTTP {resp.status_code}"
        return False, description, data

    result = data.get("result") or {}
    username = result.get("username")
    return True, username or "ok", result


@app.route("/v1/settings/bot/test", methods=["POST"])
def v1_settings_bot_test():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    token = str(settings_manager.get_setting("TELEGRAM_TOKEN", "") or "").strip()
    if not token:
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "ok": False,
                    "message": "telegram_bot_token не задан в настройках",
                }
            ),
            200,
        )

    ok, detail, _ = _telegram_bot_test(token)
    if ok:
        message = f"Связь с Telegram установлена (бот @{detail})"
    else:
        message = f"Связь с Telegram не установлена: {detail}"

    app.logger.info(
        "POST /v1/settings/bot/test request_id=%s ok=%s detail=%s",
        request_id,
        ok,
        detail,
    )
    return (
        jsonify(
            {
                "request_id": request_id,
                "ok": ok,
                "message": message,
            }
        ),
        200,
    )


def _matrix_bot_test(homeserver, access_token):
    import requests as _requests

    base = (homeserver or "").rstrip("/")
    url = f"{base}/_matrix/client/v3/account/whoami"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        resp = _requests.get(url, headers=headers, timeout=10)
    except _requests.exceptions.Timeout:
        return False, "timeout: Matrix homeserver не ответил за 10 c", None
    except _requests.exceptions.RequestException as exc:
        return False, f"network: {exc}", None

    try:
        data = resp.json()
    except Exception:
        data = None

    if resp.status_code != 200:
        if isinstance(data, dict):
            err = data.get("error") or data.get("errcode") or ""
            return False, f"HTTP {resp.status_code}: {err}".rstrip(": "), data
        return False, f"HTTP {resp.status_code}", data

    user_id = (data or {}).get("user_id") if isinstance(data, dict) else None
    return True, user_id or "ok", data


@app.route("/v1/settings/bot/matrix/test", methods=["POST"])
def v1_settings_bot_matrix_test():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    homeserver = (
        _normalize_matrix_homeserver(settings_manager.get_setting("MATRIX_HOMESERVER", ""))
        or _default_matrix_homeserver()
    )
    access_token = str(settings_manager.get_setting("MATRIX_ACCESS_TOKEN", "") or "").strip()

    if not homeserver:
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "ok": False,
                    "message": "matrix_homeserver не задан в настройках",
                }
            ),
            200,
        )
    if not access_token:
        return (
            jsonify(
                {
                    "request_id": request_id,
                    "ok": False,
                    "message": "matrix_access_token не задан в настройках",
                }
            ),
            200,
        )

    ok, detail, _ = _matrix_bot_test(homeserver, access_token)
    if ok:
        message = f"Связь с Matrix установлена (user_id={detail})"
    else:
        message = f"Связь с Matrix не установлена: {detail}"

    app.logger.info(
        "POST /v1/settings/bot/matrix/test request_id=%s ok=%s detail=%s",
        request_id,
        ok,
        detail,
    )
    return (
        jsonify(
            {
                "request_id": request_id,
                "ok": ok,
                "message": message,
            }
        ),
        200,
    )


@app.route("/v1/settings/time", methods=["GET"])
def v1_get_settings_time():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    quiet_start = _hour_to_hhmm(settings_manager.get_setting("SILENT_START", 23), "23:00")
    quiet_end = _hour_to_hhmm(settings_manager.get_setting("SILENT_END", 8), "08:00")
    metrics_collection_time = str(settings_manager.get_setting("DATA_COLLECTION_TIME", "07:30"))

    response = {
        "request_id": request_id,
        "settings": {
            "quiet_start": quiet_start,
            "quiet_end": quiet_end,
            "metrics_collection_time": metrics_collection_time,
        },
    }
    app.logger.info("GET /v1/settings/time request_id=%s", request_id)
    return jsonify(response), 200


@app.route("/v1/settings/web-auth", methods=["GET"])
def v1_get_settings_web_auth():
    """Текущие учётные данные веб-интерфейса (логин + признак заданного пароля)."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, _token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    login, password = _get_web_auth_credentials()
    payload = {
        "request_id": request_id,
        "settings": {
            "login": login,
            "password_set": bool(password),
            "auth_required": bool(login or password),
        },
        "login": login,
        "password_set": bool(password),
        "auth_required": bool(login or password),
    }
    app.logger.info("GET /v1/settings/web-auth request_id=%s", request_id)
    return jsonify(payload), 200


@app.route("/v1/settings/web-auth", methods=["PATCH"])
def v1_settings_web_auth():
    """Изменение логина/пароля веб-интерфейса.

    Пустая строка очищает значение (полная очистка обоих полей отключает
    проверку — вход в веб-интерфейс снова без пароля).
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, _token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    login = payload.get("login")
    password = payload.get("password")
    if login is None and password is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Нужно поле login и/или password",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    try:
        _set_web_auth_credentials(
            login=None if login is None else str(login).strip(),
            password=None if password is None else str(password),
        )
    except Exception as exc:
        return (
            jsonify(
                {
                    "error": {
                        "code": "SAVE_FAILED",
                        "message": str(exc),
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )

    cur_login, cur_password = _get_web_auth_credentials()
    app.logger.info("PATCH /v1/settings/web-auth request_id=%s", request_id)
    return (
        jsonify(
            {
                "request_id": request_id,
                "settings": {
                    "login": cur_login,
                    "password_set": bool(cur_password),
                    "auth_required": bool(cur_login or cur_password),
                },
                "login": cur_login,
                "password_set": bool(cur_password),
                "auth_required": bool(cur_login or cur_password),
                "message": "Учётные данные веб-интерфейса обновлены",
            }
        ),
        200,
    )


@app.route("/v1/settings/auth", methods=["GET"])
def v1_get_settings_auth():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    ssh_password = settings_manager.get_setting("SSH_PASSWORD", "")
    windows_password = settings_manager.get_setting("WINDOWS_PASSWORD", "")
    windows_credentials = settings_manager.get_windows_credentials()
    safe_windows_credentials = []
    for item in windows_credentials:
        safe_item = dict(item)
        if "password" in safe_item:
            safe_item["password"] = _mask_secret(safe_item.get("password"))
        safe_windows_credentials.append(safe_item)

    response = {
        "request_id": request_id,
        "settings": {
            "auth_mode": str(settings_manager.get_setting("AUTH_MODE", "mixed")),
            "ssh_username": str(settings_manager.get_setting("SSH_USERNAME", "root")),
            "ssh_port": int(settings_manager.get_setting("SSH_PORT", 22)),
            "ssh_key_path": str(settings_manager.get_setting("SSH_KEY_PATH", "/root/.ssh/id_rsa")),
            "windows_username": str(
                settings_manager.get_setting("WINDOWS_USERNAME", "Administrator")
            ),
            "masked_ssh_password": _mask_secret(ssh_password),
            "masked_windows_password": _mask_secret(windows_password),
            "windows_credentials": safe_windows_credentials,
            "windows_server_types": settings_manager.get_windows_server_types(),
        },
    }
    app.logger.info("GET /v1/settings/auth request_id=%s", request_id)
    return jsonify(response), 200


@app.route("/v1/settings/auth", methods=["PATCH"])
def v1_settings_auth():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}

    auth_mode = payload.get("auth_mode")
    ssh_username = payload.get("ssh_username")
    ssh_port = payload.get("ssh_port")
    ssh_key_path = payload.get("ssh_key_path")
    windows_username = payload.get("windows_username")
    ssh_password = payload.get("ssh_password")
    windows_password = payload.get("windows_password")

    if (
        auth_mode is None
        and ssh_username is None
        and ssh_port is None
        and ssh_key_path is None
        and windows_username is None
        and ssh_password is None
        and windows_password is None
    ):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "At least one field is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    if auth_mode is not None:
        settings_manager.set_setting("AUTH_MODE", str(auth_mode).strip(), "auth")
    if ssh_username is not None:
        settings_manager.set_setting("SSH_USERNAME", str(ssh_username).strip(), "auth")
    if ssh_port is not None:
        settings_manager.set_setting("SSH_PORT", int(ssh_port), "auth", data_type="int")
    if ssh_key_path is not None:
        settings_manager.set_setting("SSH_KEY_PATH", str(ssh_key_path).strip(), "auth")
    if windows_username is not None:
        settings_manager.set_setting("WINDOWS_USERNAME", str(windows_username).strip(), "auth")
    if ssh_password is not None:
        settings_manager.set_setting("SSH_PASSWORD", str(ssh_password), "auth")
    if windows_password is not None:
        settings_manager.set_setting("WINDOWS_PASSWORD", str(windows_password), "auth")

    return v1_get_settings_auth()


@app.route("/v1/settings/auth/windows-credentials", methods=["GET"])
def v1_get_windows_credentials():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    windows_credentials = settings_manager.get_windows_credentials()
    safe_windows_credentials = []
    for item in windows_credentials:
        safe_item = dict(item)
        if "password" in safe_item:
            safe_item["password"] = _mask_secret(safe_item.get("password"))
        safe_windows_credentials.append(safe_item)
    return (
        jsonify(
            {
                "request_id": request_id,
                "items": safe_windows_credentials,
                "server_types": settings_manager.get_windows_server_types(),
            }
        ),
        200,
    )


@app.route("/v1/settings/auth/windows-credentials", methods=["POST"])
def v1_add_windows_credential():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "").strip()
    server_type = str(payload.get("server_type") or "default").strip() or "default"
    priority = int(payload.get("priority") or 0)

    if not username or not password:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "username and password are required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    ok = settings_manager.add_windows_credential(username, password, server_type, priority)
    if not ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFIG_STORE_UNAVAILABLE",
                        "message": "failed to add windows credential",
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )

    return v1_get_windows_credentials()


@app.route("/v1/settings/auth/windows-credentials/<int:cred_id>", methods=["DELETE"])
def v1_delete_windows_credential(cred_id):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    ok = settings_manager.delete_windows_credential(int(cred_id))
    if not ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFIG_STORE_UNAVAILABLE",
                        "message": "failed to delete windows credential",
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )

    return v1_get_windows_credentials()


def _build_windows_types_stats(settings_manager):
    credentials = settings_manager.get_windows_credentials()
    grouped = {
        type_name: {"total": 0, "active": 0, "inactive": 0}
        for type_name in settings_manager.get_windows_server_types()
    }
    for cred in credentials:
        server_type = str(cred.get("server_type") or "default")
        bucket = grouped.setdefault(server_type, {"total": 0, "active": 0, "inactive": 0})
        bucket["total"] += 1
        if cred.get("enabled"):
            bucket["active"] += 1
        else:
            bucket["inactive"] += 1
    return grouped


@app.route("/v1/settings/auth/windows-types", methods=["GET"])
def v1_get_windows_types():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    stats = _build_windows_types_stats(settings_manager)
    return (
        jsonify(
            {
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
                },
            }
        ),
        200,
    )


@app.route("/v1/settings/auth/windows-types", methods=["POST"])
def v1_create_windows_type():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    type_name = str(payload.get("name") or "").strip()
    if not type_name:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "name is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    existing = set(settings_manager.get_windows_server_types())
    if type_name in existing:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "type already exists",
                        "request_id": request_id,
                    }
                }
            ),
            409,
        )

    # В БД тип существует только через учетные записи: создаем и сразу отключаем тех. запись.
    settings_manager.add_windows_credential(
        username=f"user_{type_name}",
        password="temp_password",
        server_type=type_name,
        priority=0,
    )
    created = settings_manager.get_windows_credentials(type_name)
    if created:
        settings_manager.update_windows_credential(created[0]["id"], enabled=0)

    return v1_get_windows_types()


@app.route("/v1/settings/auth/windows-types/<type_name>", methods=["PATCH"])
def v1_rename_windows_type(type_name):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    new_name = str(payload.get("new_name") or "").strip()
    old_name = str(type_name or "").strip()
    if not old_name or not new_name:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "new_name is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    existing = set(settings_manager.get_windows_server_types())
    if old_name not in existing:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "type not found",
                        "request_id": request_id,
                    }
                }
            ),
            404,
        )
    if new_name in existing and new_name != old_name:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFLICT",
                        "message": "target type already exists",
                        "request_id": request_id,
                    }
                }
            ),
            409,
        )

    for cred in settings_manager.get_windows_credentials(old_name):
        settings_manager.update_windows_credential(cred["id"], server_type=new_name)

    return v1_get_windows_types()


@app.route("/v1/settings/auth/windows-types/merge", methods=["POST"])
def v1_merge_windows_types():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    source_type = str(payload.get("source_type") or "").strip()
    target_type = str(payload.get("target_type") or "").strip()
    if not source_type or not target_type or source_type == target_type:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "source_type and target_type are required and must differ",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    existing = set(settings_manager.get_windows_server_types())
    if source_type not in existing or target_type not in existing:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "source or target type not found",
                        "request_id": request_id,
                    }
                }
            ),
            404,
        )

    for cred in settings_manager.get_windows_credentials(source_type):
        settings_manager.update_windows_credential(cred["id"], server_type=target_type)

    return v1_get_windows_types()


@app.route("/v1/settings/auth/windows-types/<type_name>", methods=["DELETE"])
def v1_delete_windows_type(type_name):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    source_type = str(type_name or "").strip()
    target_type = str(request.args.get("target_type") or "default").strip() or "default"
    if source_type == "default":
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "type 'default' cannot be deleted",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    existing = set(settings_manager.get_windows_server_types())
    if source_type not in existing:
        return (
            jsonify(
                {
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "type not found",
                        "request_id": request_id,
                    }
                }
            ),
            404,
        )

    if target_type not in existing:
        settings_manager.add_windows_credential(
            username=f"user_{target_type}",
            password="temp_password",
            server_type=target_type,
            priority=0,
        )
        created = settings_manager.get_windows_credentials(target_type)
        if created:
            settings_manager.update_windows_credential(created[0]["id"], enabled=0)

    for cred in settings_manager.get_windows_credentials(source_type):
        settings_manager.update_windows_credential(cred["id"], server_type=target_type)

    return v1_get_windows_types()


@app.route("/v1/settings/monitoring", methods=["PATCH"])
def v1_settings_monitoring():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}

    check_interval = payload.get("check_interval_sec")
    timeout_sec = payload.get("timeout_sec")
    max_downtime = payload.get("max_downtime_sec")
    server_timeout_fields = (
        (
            "windows_2025_timeout_sec",
            "WINDOWS_2025_TIMEOUT",
            "Таймаут Windows 2025 серверов (секунды)",
            35,
        ),
        (
            "domain_servers_timeout_sec",
            "DOMAIN_SERVERS_TIMEOUT",
            "Таймаут доменных серверов (секунды)",
            20,
        ),
        (
            "admin_servers_timeout_sec",
            "ADMIN_SERVERS_TIMEOUT",
            "Таймаут Admin серверов (секунды)",
            25,
        ),
        (
            "standard_windows_timeout_sec",
            "STANDARD_WINDOWS_TIMEOUT",
            "Таймаут стандартных Windows серверов (секунды)",
            30,
        ),
        ("linux_timeout_sec", "LINUX_TIMEOUT", "Таймаут Linux серверов (секунды)", 15),
        ("ping_timeout_sec", "PING_TIMEOUT", "Таймаут Ping серверов (секунды)", 10),
    )
    server_timeout_inputs = {field[0]: payload.get(field[0]) for field in server_timeout_fields}
    any_server_timeout = any(value is not None for value in server_timeout_inputs.values())

    if (
        check_interval is None
        and timeout_sec is None
        and max_downtime is None
        and not any_server_timeout
    ):
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "At least one field is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    try:
        from config.db_settings_app import settings_manager

        if check_interval is not None:
            check_interval = int(check_interval)
            if check_interval < 5:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "INVALID_THRESHOLD",
                                "message": "check_interval_sec must be >= 5",
                                "request_id": request_id,
                            }
                        }
                    ),
                    400,
                )
            settings_manager.set_setting(
                "CHECK_INTERVAL",
                check_interval,
                "monitoring",
                "Интервал проверки серверов (секунды)",
                "int",
            )
        else:
            check_interval = settings_manager.get_setting("CHECK_INTERVAL", 60)

        if max_downtime is not None:
            max_downtime = int(max_downtime)
            if max_downtime < 30:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "INVALID_THRESHOLD",
                                "message": "max_downtime_sec must be >= 30",
                                "request_id": request_id,
                            }
                        }
                    ),
                    400,
                )
            settings_manager.set_setting(
                "MAX_FAIL_TIME",
                max_downtime,
                "monitoring",
                "Максимальное время простоя до алерта (секунды)",
                "int",
            )
        else:
            max_downtime = settings_manager.get_setting("MAX_FAIL_TIME", 900)

        if timeout_sec is not None:
            timeout_sec = int(timeout_sec)
            if timeout_sec < 1:
                return (
                    jsonify(
                        {
                            "error": {
                                "code": "INVALID_THRESHOLD",
                                "message": "timeout_sec must be >= 1",
                                "request_id": request_id,
                            }
                        }
                    ),
                    400,
                )
            settings_manager.set_setting(
                "API_TIMEOUT_SEC", timeout_sec, "monitoring", "Таймаут API (секунды)", "int"
            )
        else:
            timeout_sec = settings_manager.get_setting("API_TIMEOUT_SEC", 15)

        server_timeout_values = {}
        for payload_key, db_key, description, default in server_timeout_fields:
            raw_value = server_timeout_inputs.get(payload_key)
            if raw_value is not None:
                try:
                    parsed_value = int(raw_value)
                except (TypeError, ValueError):
                    return (
                        jsonify(
                            {
                                "error": {
                                    "code": "VALIDATION_FAILED",
                                    "message": f"{payload_key} must be an integer",
                                    "request_id": request_id,
                                }
                            }
                        ),
                        400,
                    )
                if parsed_value < 1:
                    return (
                        jsonify(
                            {
                                "error": {
                                    "code": "INVALID_THRESHOLD",
                                    "message": f"{payload_key} must be >= 1",
                                    "request_id": request_id,
                                }
                            }
                        ),
                        400,
                    )
                settings_manager.set_setting(db_key, parsed_value, "monitoring", description, "int")
                server_timeout_values[payload_key] = parsed_value
            else:
                server_timeout_values[payload_key] = settings_manager.get_setting(db_key, default)

        return (
            jsonify(
                {
                    "request_id": request_id,
                    "settings": {
                        "check_interval_sec": check_interval,
                        "timeout_sec": timeout_sec,
                        "max_downtime_sec": max_downtime,
                        **server_timeout_values,
                        "updated_at": datetime.now().isoformat(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFIG_STORE_UNAVAILABLE",
                        "message": str(e),
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )


def _normalize_server_type(raw_value):
    normalized = str(raw_value or "").strip().lower()
    aliases = {
        "windows": "rdp",
        "linux": "ssh",
        "rdp": "rdp",
        "ssh": "ssh",
        "ping": "ping",
    }
    return aliases.get(normalized)


@app.route("/v1/settings/servers", methods=["GET"])
def v1_get_settings_servers():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    servers = settings_manager.get_all_servers(include_disabled=True)
    return (
        jsonify(
            {
                "request_id": request_id,
                "items": servers,
                "summary": {
                    "total": len(servers),
                    "enabled": sum(1 for item in servers if item.get("enabled")),
                    "disabled": sum(1 for item in servers if not item.get("enabled")),
                },
            }
        ),
        200,
    )


@app.route("/v1/settings/servers", methods=["POST"])
def v1_add_settings_server():
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    ip = str(payload.get("ip") or "").strip()
    name = str(payload.get("name") or "").strip()
    server_type = _normalize_server_type(payload.get("type"))
    timeout = payload.get("timeout")
    enabled = payload.get("enabled")

    if not ip or not name or not server_type:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "ip, name and type are required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    try:
        timeout_value = int(timeout) if timeout is not None else 30
        if timeout_value < 1:
            raise ValueError("timeout must be >= 1")
    except Exception:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "timeout must be integer >= 1",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

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
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFIG_STORE_UNAVAILABLE",
                        "message": "failed to add server",
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )

    return v1_get_settings_servers()


@app.route("/v1/settings/servers/<path:ip>", methods=["PATCH"])
def v1_update_settings_server(ip):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    raw_type = payload.get("type")
    server_type = _normalize_server_type(raw_type) if raw_type is not None else None
    timeout = payload.get("timeout")
    enabled = payload.get("enabled")

    if name is None and raw_type is None and timeout is None and enabled is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "At least one field is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    timeout_value = None
    if timeout is not None:
        try:
            timeout_value = int(timeout)
            if timeout_value < 1:
                raise ValueError("timeout must be >= 1")
        except Exception:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "VALIDATION_FAILED",
                            "message": "timeout must be integer >= 1",
                            "request_id": request_id,
                        }
                    }
                ),
                400,
            )

    if raw_type is not None and server_type is None:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "type must be one of: rdp, ssh, ping",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    ok = settings_manager.update_server(
        ip=str(ip).strip(),
        name=str(name).strip() if name is not None else None,
        server_type=server_type,
        timeout=timeout_value,
        enabled=bool(enabled) if enabled is not None else None,
    )
    if not ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "SERVER_NOT_FOUND",
                        "message": "server not found or update skipped",
                        "request_id": request_id,
                    }
                }
            ),
            404,
        )

    return v1_get_settings_servers()


@app.route("/v1/settings/servers/<path:ip>/enabled", methods=["PATCH"])
def v1_toggle_settings_server(ip):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    payload = request.get_json(silent=True) or {}
    if "enabled" not in payload:
        return (
            jsonify(
                {
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "enabled field is required",
                        "request_id": request_id,
                    }
                }
            ),
            400,
        )

    from config.db_settings_app import settings_manager

    ok = settings_manager.set_server_enabled(str(ip).strip(), bool(payload.get("enabled")))
    if not ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "SERVER_NOT_FOUND",
                        "message": "server not found",
                        "request_id": request_id,
                    }
                }
            ),
            404,
        )

    return v1_get_settings_servers()


@app.route("/v1/settings/servers/<path:ip>", methods=["DELETE"])
def v1_delete_settings_server(ip):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    is_ok, token_info = _validate_mobile_token(request.headers.get("Authorization"))
    if not is_ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Invalid or expired token",
                        "request_id": request_id,
                    }
                }
            ),
            401,
        )

    from config.db_settings_app import settings_manager

    ok = settings_manager.delete_server(str(ip).strip())
    if not ok:
        return (
            jsonify(
                {
                    "error": {
                        "code": "CONFIG_STORE_UNAVAILABLE",
                        "message": "failed to delete server",
                        "request_id": request_id,
                    }
                }
            ),
            500,
        )

    return v1_get_settings_servers()


@app.route("/")
def index():
    """Главная страница веб-интерфейса (современный SPA поверх v1 BFF API)."""
    try:
        from config.settings import APP_VERSION

        html = WEB_APP_HTML.replace("__APP_VERSION__", str(APP_VERSION))
        return app.response_class(html, mimetype="text/html")
    except Exception as e:
        return f"❌ Ошибка загрузки веб-интерфейса: {e}"


@app.route("/api/run_check")
def api_run_check():
    """API для запуска проверок"""
    check_type = request.args.get("type", "quick")

    try:
        if check_type == "quick":
            # Запуск быстрой проверки доступности
            from core.monitor_core import get_current_server_status

            status = get_current_server_status()
            message = f"✅ Быстрая проверка выполнена: {len(status['ok'])} доступно, {len(status['failed'])} недоступно"

        elif check_type == "resources":
            # Запуск проверки ресурсов
            from core.monitor_core import check_resources_automatically

            check_resources_automatically()
            message = "✅ Проверка ресурсов выполнена. Данные обновятся через 1-2 минуты."

        elif check_type == "report":
            # Формирование отчета
            from core.monitor_core import send_morning_report

            send_morning_report()
            message = "✅ Отчет сформирован и отправлен в Telegram"

        else:
            message = "❌ Неизвестный тип проверки"

        return jsonify({"success": True, "message": message, "reload": check_type != "resources"})

    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Ошибка: {str(e)}"})


@app.route("/api/run_action")
def api_run_action():
    """API ??? ?????????? ????????"""
    action = request.args.get("action", "")

    try:
        if action == "check_all":
            from core.monitor_core import get_current_server_status

            status = get_current_server_status()
            message = f"? ???????? ???? ???????? ?????????: {len(status['ok'])} ????????, {len(status['failed'])} ??????????"

        elif action == "check_resources":
            from core.monitor_core import check_resources_automatically

            check_resources_automatically()
            message = "? ???????? ???????? ????????. ?????? ????????? ????? 1-2 ??????."

        elif action == "morning_report":
            from core.monitor_core import send_morning_report

            send_morning_report()
            message = "? ???????? ????? ????????? ? Telegram"

        elif action == "restart_service":
            # ?????????? ??????? (?????????!)
            subprocess.run(["systemctl", "restart", "server-monitor.service"], check=True)
            message = "? ?????? ???????????????..."

        elif action == "toggle_monitoring":
            # ? ???????? ?????????? ????? ????? ?????? ?????????? ??????????
            message = "?? ??????? ???????????? ??????????? ? ??????????"

        elif action == "toggle_silent":
            # ? ???????? ?????????? ????? ????? ?????? ?????????? ??????????
            message = "?? ??????? ???????????? ?????? ?????? ? ??????????"

        else:
            message = "? ??????????? ????????"

        return jsonify(
            {
                "success": True,
                "message": message,
                "reload": action not in ["check_resources", "toggle_monitoring", "toggle_silent"],
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"? ??????: {str(e)}"})


@app.route("/api/supplier_stock/run", methods=["POST"])
def api_supplier_stock_run():
    """API для запуска загрузки остатков поставщиков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    def _run():
        run_supplier_stock_fetch()

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "message": "✅ Загрузка остатков поставщиков запущена"})


@app.route("/api/supplier_stock/schedule", methods=["GET", "POST"])
def api_supplier_stock_schedule():
    """API для управления расписанием загрузки остатков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    config = get_supplier_stock_config()
    schedule = config.get("download", {}).get("schedule", {})

    if request.method == "GET":
        return jsonify({"success": True, "schedule": schedule})

    data = request.json or {}
    time_value = str(data.get("time", "")).strip()
    enabled_value = bool(data.get("enabled", False))
    report_period_days = data.get("report_period_days")

    if time_value:
        schedule_times = parse_supplier_stock_schedule_times(time_value)
        if not schedule_times:
            return jsonify(
                {
                    "success": False,
                    "message": "❌ Неверный формат времени. Используйте HH:MM, разделители: пробел, запятая или ;",
                }
            )
        schedule["time"] = ", ".join(schedule_times)
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


@app.route("/api/supplier_stock/reports")
def api_supplier_stock_reports():
    """API для получения отчетов по остаткам поставщиков."""
    if not extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        return jsonify({"success": False, "message": "📦 Модуль остатков поставщиков отключен"})

    limit = request.args.get("limit")
    try:
        limit_value = int(limit) if limit is not None else 20
    except ValueError:
        limit_value = 20
    period_days = request.args.get("period_days")
    try:
        period_value = int(period_days) if period_days else None
    except ValueError:
        period_value = None
    source_id = request.args.get("source_id")
    source_kind = request.args.get("source_kind")
    reports = get_supplier_stock_reports(
        limit_value,
        period_value,
        source_id=source_id,
        source_kind=source_kind,
    )
    return jsonify({"success": True, "reports": reports})


@app.route("/api/supplier_stock/source_stats")
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
    return jsonify(
        {
            "success": True,
            "period_days": period_days,
            "stats": stats.get("summary", {}),
            "entries": stats.get("entries", []),
        }
    )


@app.route("/api/status")
def api_status():
    """API endpoint для получения статуса"""
    stats, servers = get_monitoring_stats()
    return jsonify(
        {
            "status": "ok",
            "message": "Система мониторинга работает",
            "data": {"stats": stats, "servers": servers, "timestamp": datetime.now().isoformat()},
        }
    )


@app.route("/api/servers")
def api_servers():
    """API endpoint для получения списка серверов"""
    stats, servers = get_monitoring_stats()
    return jsonify(
        {"servers": servers, "count": len(servers), "timestamp": datetime.now().isoformat()}
    )


@app.route("/api/stats")
def api_stats():
    """API endpoint для получения статистики"""
    stats, servers = get_monitoring_stats()
    return jsonify({"statistics": stats, "timestamp": datetime.now().isoformat()})


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/api/servers", methods=["GET", "POST", "PUT", "DELETE"])
def api_manage_servers():
    """API для управления списком серверов"""
    if request.method == "GET":
        # Получить список серверов
        from extensions.server_checks import initialize_servers

        servers = initialize_servers()
        return jsonify({"servers": servers})

    elif request.method == "POST":
        # Добавить новый сервер
        data = request.json
        # Здесь добавить логику сохранения в server_list.json
        return jsonify({"success": True, "message": "Сервер добавлен"})

    elif request.method == "PUT":
        # Обновить сервер
        data = request.json
        # Логика обновления
        return jsonify({"success": True, "message": "Сервер обновлен"})

    elif request.method == "DELETE":
        # Удалить сервер
        server_ip = request.args.get("ip")
        # Логика удаления
        return jsonify({"success": True, "message": "Сервер удален"})


def start_web_server():
    """Запускает веб-сервер"""
    # Читаем bind-хост/порт из БД на момент старта, а не из импортированных
    # на уровне модуля констант (они могли устареть после правки настроек).
    try:
        from config.db_settings import WEB_HOST as _web_host, WEB_PORT as _web_port
    except Exception:
        _web_host, _web_port = WEB_HOST, WEB_PORT

    bind_host = _web_host or WEB_HOST
    bind_port = _web_port or WEB_PORT

    if extension_manager.is_extension_enabled(SUPPLIER_STOCK_EXTENSION_ID):
        try:
            start_supplier_stock_scheduler()
        except Exception as e:
            print(f"⚠️ Не удалось запустить планировщик остатков поставщиков: {e}")

    print(f"🌐 Запуск веб-интерфейса на http://{bind_host}:{bind_port}")
    try:
        app.run(host=bind_host, port=bind_port, debug=False, use_reloader=False)
    except OSError as e:
        # Невозможно привязаться к указанному хосту (неверный/недоступный IP в
        # «Хост (bind)») — сервер-поток молча умрёт, BFF станет недоступен и
        # мобильный клиент получит HTTP 502. Падаем на 0.0.0.0, чтобы интерфейс
        # остался доступен в локальной сети.
        print(
            f"❌ Не удалось привязать веб-сервер к {bind_host}:{bind_port} ({e}). "
            "Повтор на 0.0.0.0"
        )
        try:
            app.run(host="0.0.0.0", port=bind_port, debug=False, use_reloader=False)
        except Exception as e2:
            print(f"❌ Ошибка запуска веб-сервера на 0.0.0.0: {e2}")
    except Exception as e:
        print(f"❌ Ошибка запуска веб-сервера: {e}")


if __name__ == "__main__":
    start_web_server()
