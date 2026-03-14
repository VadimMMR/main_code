import os
import json
import threading
import time
import requests
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from hardware_collector_lib.main import get_device_info
from system_info_library.main import get_system_info

app = Flask(__name__)
CORS(app)

# Конфигурация Telegram бота
TELEGRAM_BOT_TOKEN = "8667089058:AAGpW3MM9GE3RDDtG6d33FJoQLPqmrAmgVc"
TELEGRAM_CHAT_ID = "7404687267"  # Ваш правильный chat_id

# Глобальная переменная для хранения последних результатов
latest_results = {
    'hardware': None,
    'os_standard': None,
    'os_advanced': None,
    'last_update': None
}

def send_telegram_message(message):
    """Отправляет сообщение в Telegram бот"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"  ✅ Telegram: сообщение отправлено")
            return True
        else:
            print(f"  ⚠️ Telegram: ошибка {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
    except Exception as e:
        print(f"  ⚠️ Telegram: ошибка отправки - {e}")
        return False

def format_hardware_for_telegram(hw_data):
    """Форматирует данные оборудования для Telegram"""
    if not hw_data or (isinstance(hw_data, dict) and 'error' in hw_data):
        return "❌ Данные оборудования недоступны"
    
    message = "🖥 <b>HARDWARE INFO</b>\n"
    message += "═══════════════════\n"
    
    if isinstance(hw_data, dict):
        # CPU информация
        message += f"💻 CPU: {hw_data.get('cpu_model', 'N/A')}\n"
        message += f"   Ядра: {hw_data.get('cpu_cores', 'N/A')} | Потоки: {hw_data.get('cpu_threads', 'N/A')}\n"
        message += f"   L3 кэш: {hw_data.get('cpu_L3_MB', 'N/A')} MB\n"
        message += f"   AVX2: {'✅' if hw_data.get('cpu_avx2') else '❌'}\n"
        message += f"   AVX512: {'✅' if hw_data.get('cpu_avx512') else '❌'}\n"
        
        # GPU информация
        message += f"🎮 GPU: {hw_data.get('gpu_model', 'N/A')}\n"
        if hw_data.get('gpu_vram_GB'):
            message += f"   VRAM: {hw_data.get('gpu_vram_GB')} GB\n"
    
    return message

def format_os_for_telegram(os_data, mode="standard"):
    """Форматирует данные ОС для Telegram"""
    if not os_data or (isinstance(os_data, dict) and 'error' in os_data):
        return f"❌ Данные ОС ({mode}) недоступны"
    
    if mode == "standard" and isinstance(os_data, dict):
        message = f"💿 <b>OS INFO ({mode.upper()})</b>\n"
        message += "═══════════════════\n"
        
        if 'os_info' in os_data and isinstance(os_data['os_info'], dict):
            os_info = os_data['os_info']
            message += f"📀 ОС: {os_info.get('os_name', 'N/A')}\n"
            message += f"   Версия: {os_info.get('os_version', 'N/A')}\n"
            message += f"   Редакция: {os_info.get('os_edition', 'N/A')}\n"
            message += f"   Архитектура: {os_info.get('os_architecture_bits', 'N/A')}bit\n"
            message += f"   Ядро: {os_info.get('os_kernel', 'N/A')[:50]}...\n"
            message += f"   Хост: {os_info.get('os_hostname', 'N/A')}\n"
            message += f"   Uptime: {os_info.get('os_uptime_formatted', 'N/A')}\n"
        
        return message
    
    elif mode == "advanced" and isinstance(os_data, dict):
        message = f"⚙️ <b>OS INFO ({mode.upper()})</b>\n"
        message += "═══════════════════\n"
        
        # Основная информация
        message += f"📀 ОС: {os_data.get('os.os_name', 'N/A')}\n"
        message += f"   Версия: {os_data.get('os.os_version', 'N/A')}\n"
        message += f"   Редакция: {os_data.get('os.os_edition', 'N/A')}\n"
        message += f"   Ядро: {os_data.get('os.os_kernel', 'N/A')[:50]}...\n"
        message += f"   Хост: {os_data.get('os.os_hostname', 'N/A')}\n"
        message += f"   Uptime: {os_data.get('os.os_uptime_formatted', 'N/A')}\n"
        
        # Железо (если есть в advanced)
        if 'hardware.cpu.model' in os_data:
            message += f"💻 CPU: {os_data.get('hardware.cpu.model', 'N/A')}\n"
            message += f"   Ядра: {os_data.get('hardware.cpu.cores', 'N/A')}\n"
        
        if 'hardware.memory.total_gb' in os_data:
            message += f"🧠 RAM: {os_data.get('hardware.memory.total_gb', 'N/A')} GB\n"
        
        return message
    
    return f"❌ Неизвестный формат данных ({mode})"

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
    """Собирает данные, сохраняет их в файл и в память, выводит значения и отправляет в Telegram"""
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
    hw_data = None
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
    std_dict = None
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
    adv_dict = None
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
    history = []
    try:
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
        
        print(f"  💾 История: {len(history)} записей")
    except Exception as e:
        print(f"  ❌ Ошибка истории: {e}")
    
    # ОТПРАВЛЯЕМ В TELEGRAM
    print(f"\n  📱 Отправка в Telegram...")
    
    # Формируем сообщение для Telegram
    tg_message = f"<b>🔔 СБОР ДАННЫХ</b>\n"
    tg_message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Добавляем hardware информацию
    if hw_data and not (isinstance(hw_data, dict) and 'error' in hw_data):
        tg_message += format_hardware_for_telegram(hw_data) + "\n"
    
    # Добавляем OS standard информацию
    if std_dict and not (isinstance(std_dict, dict) and 'error' in std_dict):
        tg_message += format_os_for_telegram(std_dict, "standard") + "\n"
    
    # Добавляем информацию о сохранении
    tg_message += f"📁 Файл: {filename}\n"
    tg_message += f"💾 История: {len(history)} записей"
    
    # Отправляем
    send_telegram_message(tg_message)
    
    latest_results['last_update'] = results['datetime']
    print(f"{'='*70}\n")
    
    return True

def periodic_collection(interval_minutes=20):
    """Запускает сбор данных с заданным интервалом"""
    cycle_count = 0
    print(f"⏰ Поток сбора данных запущен с интервалом {interval_minutes} минут")
    
    while True:
        try:
            cycle_count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n🔄 Цикл #{cycle_count} в {current_time}")
            
            next_time = datetime.now().timestamp() + (interval_minutes * 60)
            next_time_str = datetime.fromtimestamp(next_time).strftime('%H:%M:%S')
            print(f"⏳ Следующий сбор в {next_time_str} (через {interval_minutes} минут)")
            
            # Ждем указанное время
            print(f"😴 Засыпаю на {interval_minutes} минут...")
            time.sleep(interval_minutes * 60)
            
            # После сна выполняем сбор
            print(f"⏰ Проснулся! Начинаю сбор данных...")
            collect_and_save_data()
            
        except Exception as e:
            print(f"❌ Ошибка в periodic_collection: {e}")
            print(f"⏱ Жду 60 секунд и пробую снова...")
            time.sleep(60)

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
    
    # Отправляем тестовое сообщение о запуске
    test_message = "<b>✅ СИСТЕМА МОНИТОРИНГА ЗАПУЩЕНА</b>\n"
    test_message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    test_message += "📊 Бот будет отправлять отчеты каждые 20 минут"
    send_telegram_message(test_message)
    
    # Запускаем фоновый поток для периодического сбора
    collection_thread = threading.Thread(
        target=periodic_collection, 
        args=(10,),  # 20 минут
        daemon=True
    )
    collection_thread.start()
    print("⏰ Фоновый сбор данных запущен (интервал: 20 минут)")
    print("📝 Первый сбор выполнен, следующие через 20 минут\n")
    
    # Запускаем сервер
    app.run(host='0.0.0.0', port=port, debug=False)