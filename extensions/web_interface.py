from flask import Flask, jsonify
from config import WEB_PORT, WEB_HOST
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return "🌐 Мониторинг серверов - help<br>Веб-интерфейс в разработке"

@app.route('/api/status')
def api_status():
    return jsonify({"status": "ok", "message": "Система мониторинга работает"})

def start_web_server():
    """Запускает веб-сервер"""
    print(f"🌐 Запуск веб-интерфейса на порту {WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)
