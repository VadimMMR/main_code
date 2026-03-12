# ==============================
# Main Code with System Information Library
# ==============================

# Этап 1: Получаем hardware_collector_lib из образа
FROM dayg0555/hardware_collector_lib:latest AS hw_lib

# Этап 2: Получаем system-info-library из образа
FROM dayg0555/system-info-library:latest AS os_lib

# Этап 3: Финальный образ с приложением
FROM python:3.11-slim

LABEL maintainer="dayg0555@gmail.com"
LABEL description="Main application using System Information Library"
LABEL version="1.0.0"

# ------------------------------
# Установка системных зависимостей
# ------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    pciutils \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------
# Рабочая директория
# ------------------------------
WORKDIR /app

# ------------------------------
# Копирование hardware_collector_lib (ПРАВИЛЬНЫЙ ПУТЬ)
# ------------------------------
COPY --from=hw_lib /app/hardware_collector_lib /app/hardware_collector_lib/

# ------------------------------
# Копирование system_info_library (ПРОВЕРЬТЕ ЭТОТ ПУТЬ!)
# ------------------------------
# Предполагаем, что в образе system-info-library структура такая же
COPY --from=os_lib /app /app/system_info_library/
# Если структура другая, замените на:
# COPY --from=os_lib /app/system_info_library /app/system_info_library/

# ------------------------------
# Устанавливаем Python путь
# ------------------------------
ENV PYTHONPATH="/app:${PYTHONPATH}"

# ------------------------------
# Копируем зависимости
# ------------------------------
COPY requirements.txt .

# ------------------------------
# Установка Python-зависимостей
# ------------------------------
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ------------------------------
# Копируем основной код приложения
# ------------------------------
COPY main.py .

# ------------------------------
# ПРОВЕРКА СТРУКТУРЫ (для отладки)
# ------------------------------
RUN echo "=== Содержимое /app ===" && \
    ls -la /app/ && \
    echo "=== Содержимое /app/hardware_collector_lib ===" && \
    ls -la /app/hardware_collector_lib/ && \
    echo "=== Содержимое /app/system_info_library ===" && \
    ls -la /app/system_info_library/ || echo "system_info_library не найден"

# ------------------------------
# ПРОВЕРКА ИМПОРТОВ
# ------------------------------
RUN echo "=== Проверка импорта hardware_collector_lib ===" && \
    python -c "import sys; print('Python path:', sys.path); from hardware_collector_lib.main import get_device_info; print('✅ hardware_collector_lib импортирован успешно')" || \
    echo "❌ hardware_collector_lib не импортируется"

RUN echo "=== Проверка импорта system_info_library ===" && \
    python -c "import sys; from system_info_library.main import get_system_info; print('✅ system_info_library импортирован успешно')" || \
    echo "❌ system_info_library не импортируется"

# ------------------------------
# Создание непривилегированного пользователя
# ------------------------------
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# ------------------------------
# Запуск приложения
# ------------------------------
CMD ["python", "main.py"]