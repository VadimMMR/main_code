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

def print_data_sample(data, title, max_items=15, max_str_length=200):
    """Выводит образец данных в читаемом формате"""
    print(f"\n📊 {title}:")
    
    if isinstance(data, dict):
        items_printed = 0
        for key, value in data.items():
            if items_printed >= max_items:
                print(f"  ... и еще {len(data) - max_items} полей")
                break
            
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)[:max_str_length]
                if len(json.dumps(value, ensure_ascii=False)) > max_str_length:
                    value_str += "..."
                print(f"  • {key}: {value_str}")
            else:
                value_str = str(value)[:max_str_length]
                if len(str(value)) > max_str_length:
                    value_str += "..."
                print(f"  • {key}: {value_str}")
            items_printed += 1
    elif isinstance(data, list):
        print(f"  Список из {len(data)} элементов:")
        for i, item in enumerate(data[:5]):
            item_str = json.dumps(item, ensure_ascii=False)[:max_str_length]
            if len(json.dumps(item, ensure_ascii=False)) > max_str_length:
                item_str += "..."
            print(f"    [{i}] {item_str}")
        if len(data) > 5:
            print(f"    ... и еще {len(data) - 5} элементов")
    else:
        print(f"  {data}")

def collect_and_save_data():
    """Собирает данные и сохраняет их в файл и в память"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"system_data_{timestamp}.json"
    
    results = {
        'timestamp': timestamp,
        'datetime': datetime.now().isoformat(),
        'data': {}
    }
    
    print(f"\n{'='*70}")
    print(f"🕒 СБОР ДАННЫХ В {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # Собираем hardware info
    try:
        hw_data = get_device_info()
        results['data']['hardware'] = hw_data
        latest_results['hardware'] = hw_data
        print(f"\n📱 HARDWARE INFO:")
        print_data_sample(hw_data, "Данные оборудования", max_items=10)
        print(f"  📏 Размер: {len(str(hw_data))} символов")
    except Exception as e:
        results['data']['hardware'] = {'error': str(e)}
        print(f"  ❌ Hardware info: {e}")
    
    # Собираем OS standard
    try:
        std_data = get_system_info(mode="standard")
        if hasattr(std_data, 'to_dict'):
            std_dict = std_data.to_dict()
        else:
            std_dict = std_data
        results['data']['os_standard'] = std_dict
        latest_results['os_standard'] = std_dict
        
        print(f"\n💻 OS STANDARD:")
        if isinstance(std_dict, dict):
            print(f"  📋 Структура:")
            for key, value in list(std_dict.items())[:5]:
                if isinstance(value, dict):
                    print(f"    • {key}: {list(value.keys())}")
                else:
                    print(f"    • {key}: {type(value).__name__}")
        print_data_sample(std_dict, "Значения", max_items=10)
        print(f"  📏 Размер: {len(str(std_dict))} символов")
    except Exception as e:
        results['data']['os_standard'] = {'error': str(e)}
        print(f"  ❌ OS standard: {e}")
    
    # Собираем OS advanced
    try:
        adv_data = get_system_info(mode="advanced")
        if hasattr(adv_data, 'to_flat_dict'):
            adv_dict = adv_data.to_flat_dict()
        else:
            adv_dict = adv_data
        results['data']['os_advanced'] = adv_dict
        latest_results['os_advanced'] = adv_dict
        
        print(f"\n⚙️ OS ADVANCED:")
        print_data_sample(adv_dict, "Значения", max_items=15)
        print(f"  📏 Размер: {len(str(adv_dict))} символов")
    except Exception as e:
        results['data']['os_advanced'] = {'error': str(e)}
        print(f"  ❌ OS advanced: {e}")
    
    # Сохраняем в файл
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  💾 Сохранено: {filename}")
    except Exception as e:
        print(f"  ❌ Ошибка сохранения: {e}")
    
    # Обновляем историю
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
        
        if len(history) > 100:
            history = history[-100:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 История: {len(history)} записей")
    except Exception as e:
        print(f"  ❌ Ошибка истории: {e}")
    
    latest_results['last_update'] = results['datetime']
    print(f"{'='*70}\n")
    
    # Возвращаем True для индикации успеха
    return True

def periodic_collection(interval_minutes=20):
    """Запускает сбор данных с заданным интервалом"""
    print(f"⏰ Поток сбора данных запущен с интервалом {interval_minutes} минут")
    
    while True:
        try:
            # Ждем указанное количество минут
            next_time = datetime.now().timestamp() + (interval_minutes * 60)
            next_time_str = datetime.fromtimestamp(next_time).strftime('%H:%M:%S')
            print(f"⏳ Следующий сбор в {next_time_str} (через {interval_minutes} минут)")
            
            # СПИМ указанное время
            time.sleep(interval_minutes * 60)
            
            # После сна выполняем сбор
            print(f"⏰ Пробуждение: начинаю сбор данных...")
            collect_and_save_data()
            
        except Exception as e:
            print(f"❌ Ошибка в periodic_collection: {e}")
            # В случае ошибки все равно ждем и пробуем снова
            time.sleep(60)  # Подождем минуту и попробуем снова

# [Все routes остаются без изменений]
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
    
    # Выполняем первый сбор данных
    print("\n🔄 Первоначальный сбор данных...")
    collect_and_save_data()
    
    # Запускаем фоновый поток для периодического сбора
    collection_thread = threading.Thread(
        target=periodic_collection, 
        args=(20,),
        daemon=True
    )
    collection_thread.start()
    print("⏰ Фоновый сбор данных запущен (интервал: 20 минут)")
    print("📝 Первый сбор выполнен, следующие через 20 минут\n")
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=port, debug=False)