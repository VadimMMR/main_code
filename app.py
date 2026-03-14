import os
import json
import threading
import time
from flask import Flask, jsonify
from flask_cors import CORS
from hardware_collector_lib.main import get_device_info
from system_info_library.main import get_system_info

app = Flask(__name__)
CORS(app)

def test_functions_directly():
    """Тестирует функции напрямую без HTTP запросов"""
    print("\n" + "="*50)
    print("Тестирование функций сбора данных:")
    print("="*50)
    
    # Тестируем get_device_info
    try:
        device_data = get_device_info()
        print(f"✓ get_device_info(): Успешно")
        print(f"  Получено данных: {len(str(device_data))} символов")
    except Exception as e:
        print(f"✗ get_device_info(): Ошибка - {str(e)}")
    
    # Тестируем get_system_info(mode="standard")
    try:
        system_info_std = get_system_info(mode="standard")
        print(f"✓ get_system_info(standard): Успешно")
        if hasattr(system_info_std, 'to_dict'):
            data = system_info_std.to_dict()
        else:
            data = system_info_std
        print(f"  Получено данных: {len(str(data))} символов")
    except Exception as e:
        print(f"✗ get_system_info(standard): Ошибка - {str(e)}")
    
    # Тестируем get_system_info(mode="advanced")
    try:
        system_info_adv = get_system_info(mode="advanced")
        print(f"✓ get_system_info(advanced): Успешно")
        if hasattr(system_info_adv, 'to_flat_dict'):
            data = system_info_adv.to_flat_dict()
        else:
            data = system_info_adv
        print(f"  Получено данных: {len(str(data))} символов")
    except Exception as e:
        print(f"✗ get_system_info(advanced): Ошибка - {str(e)}")
    
    print("="*50 + "\n")

# Запускаем тест функций ДО запуска сервера
test_functions_directly()

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
    app.run(host='0.0.0.0', port=port, debug=False)