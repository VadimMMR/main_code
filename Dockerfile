# Multi-stage: копируем библиотеки из Docker Hub
FROM dayg0555/hardware_collector_lib:latest as hw_lib
FROM dayg0555/system-info-library:latest as os_lib
FROM python:3.11-slim

WORKDIR /app

# Копируем КОД библиотек из Docker Hub образов
COPY --from=hw_lib /app /app/hardware_collector_lib
COPY --from=os_lib /app /app/system_info_library

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ваш main.py
COPY main.py .

# IMPORTANT: PYTHONPATH должен видеть библиотеки
ENV PYTHONPATH=/app

# Проверяем импорты
RUN python -c "from hardware_collector_lib.main import get_device_info; print('HW OK')" && \
    python -c "from system_info_library.main import get_system_info; print('OS OK')"

EXPOSE 8000
CMD ["python", "main.py"]
