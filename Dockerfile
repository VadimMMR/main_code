FROM dayg0555/hardware_collector_lib:latest AS hardware_lib

# Добавляем новый этап для нашей OS библиотеки
FROM dayg0555/os-info-collector:latest AS os_lib

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеку hardware
COPY --from=hardware_lib /app/hardware_collector_lib/ /app/hardware_collector_lib/

# Копируем библиотеку OS
COPY --from=os_lib /app/ /app/os_system_lib/

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код
COPY main.py .

# Устанавливаем PYTHONPATH для доступа к библиотекам
ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD ["python", "main.py"]