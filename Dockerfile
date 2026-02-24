# Первый этап: берём образ с библиотеками
FROM dayg0555/device_lib:latest AS libs

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеку из правильного пути в правильное место
COPY --from=libs /app/hardware_collector_lib/ /app/hardware_collector_lib/

# Копируем requirements и main.py
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]