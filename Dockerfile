FROM dayg0555/hardware_collector_lib:latest AS hardware_lib
FROM dayg0555/os-info-collector:latest AS os_lib

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеку hardware (ВСЮ, со всеми файлами)
COPY --from=hardware_lib /app/hardware_collector_lib/ /app/hardware_collector_lib/

# Копируем библиотеку OS (не в подпапку, а прямо в корень)
COPY --from=os_lib /app/ /app/os_system_lib/

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем основной код
COPY main.py .

# Устанавливаем PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD ["python", "main.py"]