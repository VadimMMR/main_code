import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from hardware_collector_lib.main import get_device_info
from system_info_library.main import get_system_info

app = Flask(__name__)
CORS(app)

# Глобальная переменная для хранения последних результатов
latest_results = {
    'hardware': None,
    'os_standard': None,
    'os_advanced': None,
    'last_update': None
}

def collect_and_save_data():
    """Собирает данные и сохраняет их в файл и в память"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"system_data_{timestamp}.json"
    
    results = {
        'timestamp': timestamp,
        'datetime': datetime.now().isoformat(),
        'data': {}
    }
    
    print(f"\n{'='*60}")
    print(f"🕒 СБОР ДАННЫХ В {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Собираем hardware info
    try:
        results['data']['hardware'] = get_device_info()
        latest_results['hardware'] = results['data']['hardware']
        print(f"  ✅ Hardware info: {len(str(results['data']['hardware']))} символов")
    except Exception as e:
        results['data']['hardware'] = {'error': str(e)}
        print(f"  ❌ Hardware info: {e}")
    
    # Собираем OS standard
    try:
        std_data = get_system_info(mode="standard")
        if hasattr(std_data, 'to_dict'):
            results['data']['os_standard'] = std_data.to_dict()
        else:
            results['data']['os_standard'] = std_data
        latest_results['os_standard'] = results['data']['os_standard']
        print(f"  ✅ OS standard: {len(str(results['data']['os_standard']))} символов")
    except Exception as e:
        results['data']['os_standard'] = {'error': str(e)}
        print(f"  ❌ OS standard: {e}")
    
    # Собираем OS advanced
    try:
        adv_data = get_system_info(mode="advanced")
        if hasattr(adv_data, 'to_flat_dict'):
            results['data']['os_advanced'] = adv_data.to_flat_dict()
        else:
            results['data']['os_advanced'] = adv_data
        latest_results['os_advanced'] = results['data']['os_advanced']
        print(f"  ✅ OS advanced: {len(str(results['data']['os_advanced']))} символов")
    except Exception as e:
        results['data']['os_advanced'] = {'error': str(e)}
        print(f"  ❌ OS advanced: {e}")
    
    # Сохраняем в файл с timestamp
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"  💾 Сохранено в файл: {filename}")
    except Exception as e:
        print(f"  ❌ Ошибка сохранения файла: {e}")
    
    # Сохраняем также в общий файл с историей
    history_file = "data_history.json"
    try:
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append({
            'timestamp': timestamp,
            'datetime': results['datetime'],
            'data_size': {
                'hardware': len(str(results['data'].get('hardware', ''))),
                'os_standard': len(str(results['data'].get('os_standard', ''))),
                'os_advanced': len(str(results['data'].get('os_advanced', '')))
            }
        })
        
        # Оставляем только последние 100 записей
        if len(history) > 100:
            history = history[-100:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 История обновлена (всего записей: {len(history)})")
    except Exception as e:
        print(f"  ❌ Ошибка обновления истории: {e}")
    
    latest_results['last_update'] = results['datetime']
    print(f"{'='*60}\n")

def periodic_collection(interval_minutes=20):
    """Запускает сбор данных с заданным интервалом"""
    while True:
        try:
            collect_and_save_data()
        except Exception as e:
            print(f"❌ Критическая ошибка в periodic_collection: {e}")
        
        # Ждем указанное количество минут
        print(f"⏳ Следующий сбор через {interval_minutes} минут...\n")
        time.sleep(interval_minutes * 60)

@app.route('/')
def index():
    return jsonify({
        "name": "System Information API",
        "status": "running",
        "last_update": latest_results.get('last_update'),
        "endpoints": {
            "/api/device": "Get hardware information",
            "/api/os/standard": "Get OS information (standard mode)",
            "/api/os/advanced": "Get OS information (advanced mode)",
            "/api/health": "Health check",
            "/api/latest": "Get latest collected data",
            "/api/history": "Get collection history"
        }
    })

@app.route('/api/health')
def health():
    return jsonify({
        "status": "ok",
        "last_update": latest_results.get('last_update'),
        "data_available": all([
            latest_results['hardware'] is not None,
            latest_results['os_standard'] is not None,
            latest_results['os_advanced'] is not None
        ])
    })

@app.route('/api/latest')
def get_latest():
    """Возвращает последние собранные данные"""
    if latest_results['last_update'] is None:
        return jsonify({"error": "No data collected yet"}), 404
    
    return jsonify({
        "last_update": latest_results['last_update'],
        "data": {
            "hardware": latest_results['hardware'],
            "os_standard": latest_results['os_standard'],
            "os_advanced": latest_results['os_advanced']
        }
    })

@app.route('/api/history')
def get_history():
    """Возвращает историю сборов данных"""
    history_file = "data_history.json"
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return jsonify(history)
    return jsonify([])

@app.route('/api/device')
def api_device():
    if latest_results['hardware'] is not None:
        return jsonify(latest_results['hardware'])
    try:
        data = get_device_info()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/os/standard')
def api_os_std():
    if latest_results['os_standard'] is not None:
        return jsonify(latest_results['os_standard'])
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
    if latest_results['os_advanced'] is not None:
        return jsonify(latest_results['os_advanced'])
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
    
    # Выполняем первый сбор данных перед запуском сервера
    print("\n🔄 Первоначальный сбор данных...")
    collect_and_save_data()
    
    # Запускаем фоновый поток для периодического сбора данных (каждые 20 минут)
    collection_thread = threading.Thread(
        target=periodic_collection, 
        args=(20,),  # 20 минут
        daemon=True
    )
    collection_thread.start()
    print("⏰ Фоновый сбор данных запущен (интервал: 20 минут)\n")
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=port, debug=False)