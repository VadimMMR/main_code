
FROM dayg0555/hardware_collector_lib:latest AS libs

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеку
COPY --from=libs /app/hardware_collector_lib/ /app/hardware_collector_lib/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
