FROM dayg0555/hardware_collector_lib:v3.0-final AS hardware_lib
FROM dayg0555/system_info_lib:latest AS os_lib

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеку hardware
COPY --from=hardware_lib /app/hardware_collector_lib/ /app/hardware_collector_lib/

# Копируем библиотеку system_info_lib
COPY --from=os_lib /app/ /app/system_info_lib/

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код
COPY main.py .

# Устанавливаем PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD ["python", "main.py"]