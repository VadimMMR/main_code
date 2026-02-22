# Первый этап: берём образ с библиотеками
FROM dayg0555/device_lib:latest AS libs

FROM python:3.11-slim

WORKDIR /app

# Копируем библиотеки из первого образа — ПРАВИЛЬНЫЙ ПУТЬ!
COPY --from=libs /app/device_lib/ /app/device_lib/

# Копируем requirements и main.py
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]