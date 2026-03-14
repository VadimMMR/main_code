import os
import json
import threading
import time
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from hardware_collector_lib.main import get_device_info
from system_info_library.main import get_system_info

app = Flask(__name__)
CORS(app)

# Функция для вызова endpoint'ов после запуска
def call_endpoints_after_start():
    """Вызывает endpoints после запуска сервера"""
    # Даем время серверу полностью запуститься
    time.sleep(2)
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/device",
        "/api/os/standard", 
        "/api/os/advanced"
    ]
    
    print("\n" + "="*50)
    print("Автоматический вызов endpoints после запуска:")
    print("="*50)
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"Вызов {url}...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {endpoint}: Успешно")
                print(f"  Статус: {response.status_code}")
                print(f"  Размер данных: {len(str(data))} символов")
            else:
                print(f"✗ {endpoint}: Ошибка {response.status_code}")
                
        except Exception as e:
            print(f"✗ {endpoint}: Ошибка - {str(e)}")
    
    print("="*50 + "\n")

@app.route('/')
def index():
    return jsonify({
        "name": "System Information API",
        "endpoints": {
            "/api/device": "Get hardware information",
            "/api/os/standard": "Get OS information (standard mode)",
            "/api/os/advanced": "Get OS information (advanced mode)",
            "/api/health": "Health check"
        }
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/device')
def api_device():
    try:
        data = get_device_info()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/os/standard')
def api_os_std():
    try:
        system_info = get_system_info(mode="standard")
        if hasattr(system_info, 'to_dict'):
            return jsonify(system_info.to_dict())
        elif hasattr(system_info, 'to_flat_dict'):
            return jsonify(system_info.to_flat_dict())
        else:
            return jsonify(system_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/os/advanced')
def api_os_adv():
    try:
        system_info = get_system_info(mode="advanced")
        if hasattr(system_info, 'to_flat_dict'):
            return jsonify(system_info.to_flat_dict())
        elif hasattr(system_info, 'to_dict'):
            return jsonify(system_info.to_dict())
        else:
            return jsonify(system_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем поток для вызова endpoints после старта сервера
    threading.Thread(target=call_endpoints_after_start, daemon=True).start()
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=port, debug=False)